"""Daily rank scheduling: the component that decides what runs, and when.

Until this existed, nothing did. The engine has had a complete scheduled path
all along -- slot allocation, group selection, claiming, the daily reset -- and
not one line of code ever called it. A self-hoster added a project, saw ranks
appear from the on-demand trigger, and then got a flat line forever with no
error anywhere. Four independent causes, each sufficient on its own:

  1. no scheduler existed (this file);
  2. the slot query required a commercial payment tier that BYOK never sets
     (removed in automation_engine.__automation_slot_checker__);
  3. `project_automation_time` was null on every group, so the slot query
     matched nothing (assigned here, see _assign_missing_run_times);
  4. the backend created every keyword `auto_call_status="done"` while the
     selector looks for != "done" -- and, worse, automation_engine.py:167
     skips the whole fetch when done == all, so a group of brand-new keywords
     was marked COMP without a single provider request (fixed at the writer,
     serp/models.py, migration 0009).

WHAT THIS DOES NOT DO
---------------------
It does not select keywords, claim anything, or talk to a provider. The engine
owns all of that and is better at it than a second implementation would be.
This decides *which groups become eligible* and *when*, which is one job, and
it is the job nothing was doing.

WHY GROUPS ARE QUEUED IN WAVES
------------------------------
`automation_daily_start` used to set group_call_status="INIT" on every group of
every tenant at midnight. One engine call afterwards drains every INIT group in
a single loop, so the daily reset was itself the stampede scheduling exists to
prevent -- and it spent provider credits as a side effect of housekeeping. That
line is now gone, and queueing lives here, where it can be spread across the
day.

WHY IT IS SAFE TO CALL OFTEN
----------------------------
Every step is idempotent. Queueing a group advances its next run time by a day,
so a second call in the same window queues nothing. The engine's daystart
guards itself on `core_refresh_time.date() < today`. Call it every 15 minutes;
call it twice by accident; nothing double-spends.
"""

import os
from datetime import datetime, time, timedelta, timezone as dt_timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from account.cron_auth import cron_only
from serp.models import Groups


# Statuses that mean a run is already in flight. Only these block queueing:
# PROC is running (and is swept back to INIT by the engine if its worker died)
# and INIT is queued but not yet drained.
#
# STOP and DROP were listed here as "operator decisions". They are not -- no
# backend view and no screen sets either, and nothing resets them: the engine
# writes DROP when a group had nothing to fetch or hit a macro problem
# (automation_engine.py:207/304, automation_common.py:587) and STOP when a run
# finished incomplete. Daystart clears keyword status but leaves
# group_call_status alone, so treating them as terminal meant a project
# scheduled once and was then excluded from every future day, silently. They
# are end-states, and tomorrow is a new run.
_NOT_QUEUEABLE = ("PROC", "INIT")

# Spread window. Groups are distributed across the day rather than all firing
# at once -- see docs/ORCHESTRATION.md 3. 24h in minutes.
_DAY_MINUTES = 24 * 60

# The engine's kstr 1-4 select 6-hour slot windows and filter on
# project_automation_time themselves. We deliberately use a value outside that
# range, which routes to the engine's non-slot branch: it drains whatever is
# INIT and lets THIS module own the decision about what is due. Two components
# both deciding is how the stampede got built the first time.
_ENGINE_DRAIN_KSTR = "5"


# Ranking runs overnight, in the quiet hour after midnight, so a morning
# dashboard is already current. Groups are spread across that hour rather than
# all firing at 01:00 exactly: 37 is coprime with 60, so consecutive project
# ids land minutes apart instead of together.
_RANK_HOUR = 1
_RANK_SPREAD_MINUTES = 60


def _slot_minute(group_id):
    """Minutes past midnight at which this group runs, derived from its id.

    Deterministic and needs no stored assignment, so it cannot drift or be
    null.
    """
    offset = (int(group_id) * 37) % _RANK_SPREAD_MINUTES
    return (_RANK_HOUR * 60 + offset) % _DAY_MINUTES


def _assign_missing_run_times(now):
    """Give every group a next-run time, so the due query can match it.

    `project_automation_time` is null on every group in a self-hosted install:
    its only writers are ClientTrackerSerializer, which iterates a collection
    that is empty, and serp/tracker.py, which explicitly refuses to create a
    row for user 1 -- the first account on any self-host. A null here is why
    the engine's own slot query matched nothing.
    """
    assigned = 0
    for group in Groups.objects.filter(project_automation_time__isnull=True):
        minute = _slot_minute(group.id)
        run_at = datetime.combine(now.date(), time(hour=minute // 60, minute=minute % 60))
        if timezone.is_aware(now):
            run_at = timezone.make_aware(run_at, timezone.get_current_timezone())
        # Today's slot if it is still ahead, otherwise tomorrow's -- so a group
        # created at 18:00 with a 09:00 slot waits for tomorrow rather than
        # ranking immediately as a side effect of being created.
        if run_at <= now:
            run_at += timedelta(days=1)
        Groups.objects.filter(id=group.id).update(project_automation_time=run_at)
        assigned += 1
    return assigned


def _next_run_after(run_at, now):
    """The next occurrence of this group's daily slot that is still ahead.

    Advancing by exactly one day is only right when the slot was missed by less
    than a day. After downtime it is wrong, and expensively so: a next-run time
    three days behind advances to two days behind, which is still due, so the
    tick after the run queues the project again -- four full billed runs of
    every project inside one hour, one per missed day. Measured: a group three
    days behind was queued on four consecutive passes.

    Missed days cannot be recovered anyway. A crawl run today measures today's
    SERP; there is no request that returns last Tuesday's rank. So the misses
    are counted, reported, and skipped, and the project runs once -- now.

    Awareness is normalised rather than assumed: `now` follows USE_TZ, while a
    stored time may have been written naive by the engine's own serializer
    path, and comparing the two raises.
    """
    if timezone.is_aware(run_at) and not timezone.is_aware(now):
        run_at = timezone.make_naive(run_at, dt_timezone.utc)
    elif timezone.is_aware(now) and not timezone.is_aware(run_at):
        run_at = timezone.make_aware(run_at, dt_timezone.utc)

    if run_at > now:
        return run_at, 0

    # O(1) for the bulk of the gap, then at most one more day for the remainder.
    whole = (now - run_at).days
    run_at += timedelta(days=whole)
    missed = whole
    while run_at <= now:
        run_at += timedelta(days=1)
        missed += 1
    return run_at, missed


def _queue_due_groups(now):
    """Mark due groups INIT and set their next run to the next future slot.

    Advancing the time IS the idempotency: a group queued at 09:00 is not due
    again until 09:00 tomorrow, so calling this every fifteen minutes queues it
    exactly once. No 'last run' column, and no way for a crash between the two
    writes to double-queue -- the status write is what the engine reads, and it
    is a no-op on a group already INIT.

    Returns (queued_ids, skipped_days) -- skipped_days totals the daily slots
    that went by while nothing was running, so downtime shows up in the
    scheduler's own log line instead of only in a provider bill.
    """
    due = Groups.objects.filter(project_automation_time__lte=now).exclude(
        group_call_status__in=_NOT_QUEUEABLE
    )

    queued = []
    skipped = 0
    for group in due:
        run_at, missed = _next_run_after(group.project_automation_time, now)
        Groups.objects.filter(id=group.id).update(
            group_call_status="INIT",
            project_automation_time=run_at,
        )
        queued.append(group.id)
        # One of the advances is this run's own slot, not a missed one.
        skipped += max(0, missed - 1)
    return queued, skipped


@csrf_exempt
@cron_only
@api_view(["GET"])
@permission_classes((AllowAny,))
def rank_schedule(request):
    """Scheduler entry point. Call every 15 minutes from cron.

    AllowAny is deliberate -- a cron carries no session -- but @cron_only above
    it demands the instance's CRON_TOKEN, compared with hmac.compare_digest,
    and fails closed when that is unset. Without the token this would be an
    anonymous URL that spends every account's provider credits, which is the
    same reasoning as llmtracker.manage_prompts.

        curl -H "X-Cron-Token: $CRON_TOKEN" https://your-host/rank/schedule

    Returns what it did rather than a bare OK, so an operator can see whether
    the instance is actually ranking without reading engine logs.
    """
    return JsonResponse(run_rank_schedule())


def run_rank_schedule():
    """Do one scheduling pass and report what happened.

    Shared by the HTTP endpoint above and the `rank_schedule` management
    command, so an instance can be scheduled either by an external cron or by
    the bundled scheduler container without two implementations drifting.
    """
    from serp.engine_trigger import trigger_engine_daystart, trigger_engine_scheduled

    now = timezone.localtime() if timezone.is_aware(timezone.now()) else datetime.now()

    # Daystart resets keyword statuses and per-day counters. It guards itself on
    # core_refresh_time, so calling it every run is a no-op until the date rolls
    # over. It no longer queues anything -- that is this module's job now.
    trigger_engine_daystart()

    assigned = _assign_missing_run_times(now)
    queued, skipped_days = _queue_due_groups(now)

    # Only poke the engine when there is something to drain. A poke with an
    # empty queue is harmless but it makes the engine log a run that did
    # nothing, which is noise an operator has to learn to ignore.
    if queued:
        trigger_engine_scheduled()

    return {
        "status": "true",
        "at": now.isoformat(),
        "run_times_assigned": assigned,
        "groups_queued": queued,
        # Daily slots that passed with nothing running. Non-zero means the
        # instance was down; those runs are skipped, not caught up.
        "slots_skipped": skipped_days,
        "engine_poked": bool(queued),
    }
