"""Drive the ranking engine's manual queue on demand.

Refreshing a project, and adding one, both queue work by setting the group to
manual_grp_trigger="INIT". A scheduler is meant to notice that and drive the
engine; a self-hosted instance has no scheduler, so the queue would sit there
and the UI would spin forever. This asks the engine to process it now.

Fire-and-forget in a daemon thread: the engine ranks synchronously and would
otherwise block the request that queued the work for the whole crawl, while the
frontend is already polling /refreshstatus for progress. It spends the
account's own provider credits -- which is what a rank check costs.

Disabled when ENGINE_TRIGGER_TOKEN is unset: no token, no trusted caller, so the
call is skipped and the queue waits for whatever else drives the engine. The
engine accepts this token (constant-time compared) in place of its IP + oid
handshake -- see engine automation_common.__base_validation__.
"""

import os
import threading

import requests


def _fire(kstr, userid=None, grpid=None):
    """Ask the engine to drain queue branch `kstr`.

    `userid`/`grpid` name the project whose run this is. They are optional --
    the competitor triggers have no single project -- but when given, a failure
    to reach the engine is recorded against that project so /refreshstatus can
    report it instead of the UI polling a queue nothing will ever drain.
    """
    token = os.environ.get("ENGINE_TRIGGER_TOKEN", "")
    if not token:
        if userid and grpid:
            from serp.refresh_error import CODE_ENGINE_DISABLED, record_refresh_error

            record_refresh_error(userid, grpid, CODE_ENGINE_DISABLED)
        return
    base = os.environ.get("ENGINE_URL", "http://engine:8001")

    def _run():
        try:
            # The ustr path segment is ignored once the token is accepted, so
            # any 11+ char placeholder does. kstr selects the engine's branch.
            response = requests.get(
                base + "/automation/manual/call/rn-trigger01/%s" % kstr,
                headers={"X-Engine-Token": token},
                timeout=600,
            )
            if response.status_code != 200 and userid and grpid:
                from serp.refresh_error import CODE_ENGINE_UNREACHABLE, record_refresh_error

                record_refresh_error(
                    userid,
                    grpid,
                    CODE_ENGINE_UNREACHABLE,
                    "The ranking engine refused the request (HTTP %s), so the queued keywords were never processed."
                    % response.status_code,
                )
        except requests.exceptions.ReadTimeout:
            # Connected, then no response within the window. The engine HAS the
            # work and ranks synchronously, so it is probably still running --
            # recording a failure here would show a permanent error for a run
            # that goes on to succeed, and the frontend poller gives up long
            # before this 600s timeout anyway. Say nothing rather than
            # something wrong. A connect timeout is a different case and falls
            # to the branch below, because that one never reached the engine.
            pass
        except Exception:
            # Work that cannot reach the engine is not worth crashing the
            # request that queued it, but it must not look like success
            # either: record it where /refreshstatus will find it.
            if userid and grpid:
                from serp.refresh_error import CODE_ENGINE_UNREACHABLE, record_refresh_error

                record_refresh_error(userid, grpid, CODE_ENGINE_UNREACHABLE)

    threading.Thread(target=_run, daemon=True).start()


def trigger_engine_manual(userid=None, grpid=None):
    """Rank the next queued (INIT) project now. kstr=1 -> the INIT-group branch."""
    _fire("1", userid, grpid)


def _fire_scheduled(path):
    """Call one of the engine's SCHEDULED endpoints, fire-and-forget.

    Separate from `_fire` because the scheduled entry points live under
    /automation/engine/, not /automation/manual/, and because there is no
    single project to attribute a failure to: the scheduler queues many groups
    at once, so there is no `/refreshstatus` poller waiting on a specific one.
    Failures go to the engine's own log rather than a project's error row.

    Same token contract as `_fire`: no ENGINE_TRIGGER_TOKEN, no call at all.
    """
    token = os.environ.get("ENGINE_TRIGGER_TOKEN", "")
    if not token:
        return
    base = os.environ.get("ENGINE_URL", "http://engine:8001")

    def _run():
        try:
            requests.get(
                base + path,
                headers={"X-Engine-Token": token},
                timeout=600,
            )
        except Exception:
            # A scheduled run that cannot reach the engine must not crash the
            # cron request -- the next tick tries again, and the queued groups
            # stay INIT until something drains them.
            pass

    threading.Thread(target=_run, daemon=True).start()


def trigger_engine_daystart():
    """Run the engine's daily reset: keyword statuses, counters, engine flags.

    Idempotent by the engine's own guard -- `daily_automation_first_call` does
    nothing unless `core_refresh_time.date()` is older than today -- so the
    scheduler can call it on every tick and it acts once per day.

    It no longer queues groups. That line used to set group_call_status="INIT"
    across every tenant, which made the reset itself a stampede; queueing is
    the scheduler's job now. See serp/rank_scheduler.py.
    """
    _fire_scheduled("/automation/engine/daystart/rn-trigger01")


def trigger_engine_scheduled():
    """Drain the groups the scheduler has queued.

    kstr=5 is outside the engine's 1-4 slot range on purpose, which routes to
    its non-slot branch: drain whatever is INIT. The engine's own slot windows
    filter on project_automation_time, and having both it and the scheduler
    decide what is due would be two components owning one decision -- which is
    how the midnight stampede was built. The scheduler decides; the engine
    executes.
    """
    _fire_scheduled("/automation/engine/call/rn-trigger01/%s" % "5")


def trigger_engine_competitor_crawl():
    """Crawl each selected competitor's SERP now -- the post-selection crawl.

    Runs ONLY stage 2 (kstr=25, automation_comp_analyse("MANUAL")), which reads
    competitor_project_status="INIT". add_competitors already creates the
    CompProject/CompKeyword rows and sets that status to INIT when the user picks
    competitors, so there is no stage 1 to run and no START->INIT bridge to make
    here; without this call the INIT queue sits untouched on a self-hosted
    instance (no scheduler) and the competitor cards stay blank forever.

    Fire-and-forget in a daemon thread; skipped when ENGINE_TRIGGER_TOKEN is
    unset. Spends the account's own SERP credits.
    """
    _fire("25")


def trigger_engine_competitor():
    """Run a queued competitor analysis to completion, now.

    Competitor analysis is a two-stage engine pipeline and the manual path did
    not join the stages: stage 1 (kstr%3, automation_ai_analyse) turns
    competitor_analyse_status START -> COMP and sets competitor_project_status
    START, but the manual stage 2 (kstr%25, automation_comp_analyse("MANUAL"))
    only picks up project_status INIT -- START is the cron's ENGINE flag. So a
    self-hosted "Start analysis" completed stage 1 and stalled.

    This drives stage 1, bridges the START the manual stage cannot see to the
    INIT it can, then drives stage 2 -- the whole thing on demand, in a daemon
    thread, spending the account's own SERP credits.
    """
    token = os.environ.get("ENGINE_TRIGGER_TOKEN", "")
    if not token:
        return
    base = os.environ.get("ENGINE_URL", "http://engine:8001")
    headers = {"X-Engine-Token": token}

    def _run():
        try:
            # Stage 1: analyse keywords, identify competitors (-> project START).
            requests.get(base + "/automation/manual/call/rn-trigger01/3", headers=headers, timeout=600)
            # Bridge: the manual crawl reads INIT, stage 1 writes START.
            from serp.models import Groups
            for g in Groups.objects.all():
                if getattr(g, "competitor_project_status", None) == "START":
                    Groups.objects.filter(id=g.id).update(competitor_project_status="INIT")
            # Stage 2: crawl each identified competitor's SERP.
            requests.get(base + "/automation/manual/call/rn-trigger01/25", headers=headers, timeout=600)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
