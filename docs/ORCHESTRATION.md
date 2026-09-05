# Orchestration spec — multi-project rank scheduling

**Status:** the design `engine/project/machine/` is built to. Read this before
changing that package.

SearchMirror inherited its ranking engine from a single-tenant commercial
product. This is the part of that inheritance worth the most and the hardest to
reinvent: how you rank tens of thousands of keywords across hundreds of
projects, every day, unattended, without stampeding a provider or losing work
when something dies.

What follows is that design corrected for the two things SearchMirror changes:
**multi-tenancy** and **bring-your-own-key**. Where this document and the code
disagree, the code won and this document is stale — say so in the pull request.
Throughout, "the inherited engine" means the original single-tenant
implementation, and "the correction" is what this project does instead.

---

## 1. The problem

At a realistic volume — tens of thousands of keywords across hundreds of
projects — a naive "loop over every keyword at midnight" fails in four ways:

1. Everything hits the provider at once; you get rate-limited.
2. One slow project blocks every project behind it.
3. A crash mid-run loses track of what was already done.
4. Two workers pick the same keyword and you pay twice.

The layer below solves all four. Each mechanism exists because one of these bit
somebody.

---

## 2. Keyword state machine

Every keyword carries a status. This is what lets multiple workers draw from one
pool without coordinating.

```
        ┌──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
     ┌───────┐   claimed    ┌────────┐   success   ┌────────┐
     │ avail │─────────────►│ busy   │────────────►│ done   │
     └───────┘              └────────┘             └────────┘
        ▲                        │
        │                        │ provider error / timeout
        │                        ▼
        │                   ┌────────┐
        └───────────────────│ failed │   retry, with backoff and a cap
          reset on retry    └────────┘
                                 │  attempts exhausted
                                 ▼
                            ┌────────┐
                            │ done   │  (recorded as not-ranked, with a reason)
                            └────────┘
```

The inherited engine uses `avail / busy / load / done / fail`. `load` and `busy` do the same
job — **collapse them to one**.

### Rules

- **Claiming must be atomic.** `UPDATE ... SET status='busy' WHERE id = ANY(...)
  AND status='avail' RETURNING id` — the worker processes only the rows it got
  back. It claims with a plain `.update()`, which races if two workers
  overlap.
- **Reset stale claims.** A keyword `busy` for longer than a run could plausibly
  take belongs to a dead worker. Sweep it back to `avail`. The inherited engine has no such
  sweep — that is exactly how 362 rows sat stuck in `busy` and became invisible
  to the batch loader.
- **`failed` is a real state, not a synonym for done.** The inherited engine forces
  `auto_call_status='done'` on failure, with the comment *"so cron doesn't
  re-pick failed kw"*. That is why over a thousand keywords silently stopped
  retrying. Keep failures visible and retry them properly.

---

## 3. Scheduling: spreading the day

**Every project gets its own run time**, derived from the tenant's timezone.
Runs are then spread across the day rather than all firing at 00:00.

The inherited engine recalculates `project_automation_time` per project on the daily pass.
Keep that. Drop what decides the ordering.

### Ordering

The inherited engine orders projects by **payment tier** — `paymentmode` A/B/C/D/E/F, where
A is an active Stripe subscriber and F is expired. 13 references across the
codebase.

**Under BYOK this concept disappears.** Nobody is paying us, so nobody has
priority for having paid. Replace with:

| Rule | Why |
|---|---|
| Round-robin across tenants | one tenant with 10,000 keywords cannot starve one with 50 |
| Oldest-ranked keyword first, within a project | staleness is the fair tiebreak — the inherited engine already does this via `order_by('+auto_refresh_count')` |
| Per-tenant concurrent-run cap | bounds any single tenant's slice of the queue |

Round-robin across tenants is the single most important change. The inherited engine never
needed it — every project belonged to one company. A hosted BYOK service does.

---

## 4. Concurrency

One sliding window, not fixed batches.

```python
sem = asyncio.Semaphore(concurrency)

async def fetch(item):
    async with sem:
        return await provider.search(item)

tasks = [asyncio.create_task(fetch(i)) for i in items]
for coro in asyncio.as_completed(tasks):
    await handle(await coro)
```

The inherited engine's own comment explains why: *"the sliding window is enforced by
`asyncio.Semaphore(100)` … so 100 requests stay in-flight continuously with zero
idle time at batch boundaries."* That is correct and worth keeping verbatim as a
principle.

For contrast, fixed batches with a sleep between them waste the boundary: 500
keywords at a time with a 10-second pause is 114 batches in a day, which is
**19 minutes of pure idle** for no benefit.

### Concurrency is per tenant, not global

The inherited engine uses one global figure (100). Under BYOK, concurrency is bounded by the
**tenant's own key and plan**, so it belongs on the tenant. A global ceiling
still applies on top, to protect our server.

---

## 5. Counters and health

The inherited engine tracks per-outcome provider counters — `proxy_success_count`,
`proxy_exceeds_count` (429), `proxy_invalid_count`, plus a `proxy_reset_counter`
that increments on failure and zeroes on success. That last one is a circuit
breaker in all but name. Keep the idea; make it explicit.

**The problem:** all of it lives in **one settings row, `id: 1`**, written from
12 call sites. One shared mutable row across every tenant — a race under
concurrency and a hard ceiling of one instance.

**Replace with per-tenant counters**, and a real circuit breaker:

| State | Behaviour |
|---|---|
| closed | normal |
| open | after N consecutive failures, stop calling; fail fast for a cooldown |
| half-open | after cooldown, allow one probe; success closes, failure re-opens |

This is not theoretical. During a real provider outage — 502s and 60-second
timeouts — the inherited engine's unbounded retry turned roughly 2,000 requests
into **33,000**, most of them timeouts, and still ended with thousands of
keywords in a failed state. A circuit breaker turns that into a few hundred
failed calls and a status a human can read.

---

## 6. The daily cycle

The inherited engine runs a `daystart` pass that resets counters and recalculates schedule
times. Keep the shape; fix the scope.

```
daily, per tenant:
  reset per-tenant usage counters
  recalculate each project's run time from the tenant timezone
  sweep stale `busy` keywords back to `avail`
  reset circuit breakers
```

**The inherited engine does four table-wide `.update()` calls with no tenant filter** — e.g.
`Keyword.objects.update(auto_refresh_count=0)` resets every keyword for every
user in one statement. Every one of these must become tenant-scoped.

---

## 7. Triggering: queue, not cron-plus-ports

The inherited engine is driven by system cron curling HTTP endpoints across six ports:

```cron
0 2 * * *  curl .../automation/engine/daystart/6006f5c2372
*  * * * *  sleep 0;  curl :8002/automation/manual/call/.../1
*  * * * *  sleep 20; curl :8002/automation/manual/call/.../2
*  * * * *  sleep 40; curl :8003/automation/manual/call/.../25
```

Six `manage.py runserver` processes, fanned out by staggered `sleep`, with a
hardcoded token in the crontab. It works, and it is why the engine has no idea
how much work is outstanding.

**Use a real task queue** — Celery, as DataBlue already does. That gives
retries with backoff, visibility into queue depth, scheduled beats, and workers
that scale without editing a crontab.

---

## 8. Cost control — new, no equivalent in the inherited engine

Under BYOK the user pays per call, so the scheduler owes them honesty.

- **Estimate before running.** `keywords × pages` shown before any run starts.
- **Default `pages=1`.** The inherited engine defaults to 3, billing triple for results most
  users never look at.
- **Hard per-run ceiling**, so a misconfiguration cannot drain someone's balance.
- **Never retry a hard failure.** A 402 or an invalid key must stop immediately,
  not retry.
- **Record credits consumed per run** and show a running total.

---

## 9. What to build, in order

1. **State machine + atomic claim** — everything else depends on it
2. **Sliding-window executor** — concurrency, per tenant
3. **Circuit breaker + per-outcome counters**
4. **Scheduler** — timezone spread, round-robin across tenants
5. **Daily cycle** — tenant-scoped resets and the stale-claim sweep
6. **Cost estimation and ceilings**

Items 1–3 are the vertical slice's engine. 4–6 make it safe to leave running.

---

## Summary — keep vs change

| Keep | Change |
|---|---|
| keyword state machine | collapse `busy`/`load`; make claims atomic; keep `failed` real |
| per-project timezone scheduling | ordering by payment tier → round-robin across tenants |
| sliding-window concurrency | global limit → per-tenant, with a global ceiling |
| per-outcome provider counters | singleton `id:1` row → per-tenant, explicit circuit breaker |
| daily reset cycle | table-wide updates → tenant-scoped; add stale-claim sweep |
| multi-worker fan-out | cron + 6 ports + hardcoded token → task queue |
| — | cost estimation and ceilings (new) |
