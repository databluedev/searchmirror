# DataBlue SERP API — two findings from live runs

**2026-09-05.** Found while verifying SearchMirror's SERP-feature handling
against live responses. These are about **DataBlue**, not about the tracker —
the tracker now handles both correctly, but both cap what it can show a user.

Evidence: **41 stored responses**, all `advanced=true`, 3 pages each —
35 historic (project `Datablue`, 29 Aug–5 Sep) plus 4 from a probe run on
2026-09-05 using queries chosen because Google answers them with a People-also-ask
box and a featured snippet.

---

## 1. `people_also_ask` is always sent and never populated

```
key present in the response   : 41 / 41
key NON-EMPTY                 :  0 / 41
queries that returned any PAA : none
```

The probe deliberately used the four query shapes most likely to produce PAA:

| Query | PAA returned |
|---|---|
| `what is web scraping` | `[]` |
| `how does a web scraping api work` | `[]` |
| `what is a serp api` | `[]` |
| `web scraping vs web crawling` | `[]` |

Google shows a People-also-ask box for all four. DataBlue returns the key as an
empty list every time.

**Why it matters to the tracker.** Because the key is *present*, the parser
records the block as `reported: true` — "the provider looked and there was
none" — which is the honest reading of the payload but not the truth of the
SERP. Every keyword's People-also-ask row therefore reads **None**, which a
user will take as "Google shows no PAA for my keyword".

**What would fix it, in order of preference:**

1. DataBlue extracts PAA. Then the tracker needs no change: the block is already
   parsed, stored and rendered, and it will start showing entries.
2. If DataBlue is not going to extract it, **omit the key** rather than sending
   an empty list. The tracker already distinguishes "key absent" from "key
   present and empty" (`reported: false` vs `true`); omitting it would make the
   row read as unmeasured rather than as a measured absence.

Sending an empty list is the one option that produces a wrong answer.

---

## 2. `featured_snippet` only ever carries the AI Overview

```
responses carrying a featured_snippet block : 7
  ... typed "ai_overview"                   : 7
  ... an actual featured snippet            : 0
```

Every response that carries the block carries the AI Overview in it, tagged
`type: "ai_overview"`, with `title: "AI Overview"` and the AI answer as
`content`. The `url` is one of the AI Overview's *source* links.

```
query   : "what is a serp api"
featured_snippet.type    = 'ai_overview'
featured_snippet.title   = 'AI Overview'
featured_snippet.url     = 'https://serpapi.com/'
featured_snippet.content = 'SerpApi is a managed API service that scrapes...'
ai_overview.content      = 'SerpApi is a managed API service that scrapes...'   <- the same text
ai_overview.sources      = 10
```

So the same answer arrives twice, under two names, and one of those names means
something else entirely.

**Why it matters, and why it was a live bug.** A featured snippet is a *won
position* — the tracker counts it and reports `owned` by comparing the snippet's
URL against the tracked domain. Taken at face value, this block would report a
**won featured snippet** for 7 keywords that have none, and would report
`owned: true` for any account whose domain happened to be the AI Overview's
first cited source.

The tracker already filters it (`parser_json.py` drops entries typed
`ai_overview` out of the featured-snippet block), so the stored data is correct:
all 30 keywords on project `Datablue` record `featured_snippet: absent` while
4 of them record `ai_overview: present` with 8–10 sources and ~1,000 characters
of answer text. That filter is now the only thing standing between the payload
and a fabricated win, which makes it worth knowing about on the API side.

**What would fix it:** don't populate `featured_snippet` with the AI Overview.
It already has its own top-level `ai_overview` key carrying the same content and
a richer source list. If some consumer depends on the duplication, keeping the
`type` discriminator is what makes it survivable — losing that field would make
the two indistinguishable.

---

## What was verified working

Same runs, for completeness:

- **`related_searches` carry their query text** — 232 of 232 entries after the
  parser fix, 0 of 232 before it. DataBlue sends `{"query", "url"}`; the
  extractor was reading only title-ish field names and keeping the
  `google.<tld>` redirect.
- **`ai_overview` is correct and rich** — present on 4 of 30 project keywords
  and 3 of 4 probe queries, with 8–10 sources and ~1,000 characters of content.
- **Partial-page responses are handled** — 2 historic responses came back
  `success: true, partial: true, 1 of 3 pages`, with 10 usable organic results.
  Those keywords ranked normally.
- **Throughput** — 30 keywords × 3 pages drained in **30 seconds** with zero
  failures.

## Spend

105 DataBlue searches on 2026-09-05, with the owner's approval:
3 (single keyword re-check) + 12 (4-keyword feature probe, since deleted)
+ 90 (full refresh of project `Datablue`).
