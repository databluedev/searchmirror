"""Why a rank refresh produced no data, recorded where the user can see it.

The refresh loop had no failure surface at all. The engine used to force-clear
``manual_call_status`` and rewrite ``manual_call_mode`` to "done" on every error
path, so ``/refreshstatus`` watched its running-keyword count fall to zero and
the frontend announced "SERP Data loaded successfully" -- identically for a run
in which every keyword succeeded and one in which every keyword failed. A
missing or undecryptable DataBlue key, an unreachable engine and a SERP provider
returning 429 all looked like success.

This module is the one place that answers "what went wrong with this project's
last run". It combines three sources, in this order:

1. **The account's key**, checked live. It is the cause of the other two, so it
   is reported first: an account with no usable key produces a stalled queue,
   not the other way round.
2. **The per-run record** on the project's ``Refreshmanual`` row. The engine
   writes it once when a manual run drains (A-02), and writes ``("", "")`` on a
   clean run so a stale reason cannot outlive the failure it described. The
   backend writes it too, for the failures only the backend can see -- an engine
   it could not reach, or no trigger token to reach it with.
3. **Whether the backend can drive the engine at all**, checked live.

WHAT IS NOT A SOURCE: the count of keywords sitting in ``manual_call_mode
= "fail"``. That flag is **sticky between runs** -- it persists until the
keyword next succeeds, is re-added, or the group is re-run -- so deriving "this
run failed" from it would report last week's failure as the outcome of the
refresh the user is watching right now. It is still returned, as ``fkw``, but
strictly as a standing count of keywords with no current rank data. Only the
per-run record decides whether a run failed.

Anything that queues a run must call ``clear_refresh_error()`` so the previous
run's reason cannot be read as this run's.
"""

import os


CODE_NO_KEY = "nokey"
CODE_KEY_UNREADABLE = "keyunreadable"
CODE_ENGINE_DISABLED = "engine_disabled"
CODE_ENGINE_UNREACHABLE = "engine_unreachable"
CODE_SERP_FAILED = "serp_failed"
# Distinct from CODE_SERP_FAILED because the user's action differs: rate
# limiting is transient and the answer is "wait", where a generic provider
# failure means the request or the provider was wrong. The engine records this
# when every failure in a run was a 429.
CODE_SERP_RATE_LIMITED = "serp_rate_limited"

MESSAGES = {
    CODE_NO_KEY: "No DataBlue API key on this account, so no rank check can run. Add your key under Account -> API Key.",
    CODE_KEY_UNREADABLE: "The stored DataBlue API key could not be decrypted, so rank checks ran without one. Re-enter it under Account -> API Key.",
    CODE_ENGINE_DISABLED: "The ranking engine cannot be started: ENGINE_TRIGGER_TOKEN is not set on this instance, and nothing else drives the queue.",
    CODE_ENGINE_UNREACHABLE: "The ranking engine did not respond, so the queued keywords were never processed.",
    CODE_SERP_FAILED: "The SERP provider returned no usable result for some keywords, so their positions were not updated.",
    CODE_SERP_RATE_LIMITED: "Your SERP provider rate limited this account, so some keywords could not be checked. Wait a few minutes and refresh again.",
}


def message_for(code, fallback=""):
    return MESSAGES.get(code, fallback)


def clear_refresh_error(userid, grpid):
    """Drop the recorded reason for a project -- call when queueing a new run."""
    from serp.models import Refreshmanual

    try:
        Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).update(
            refresh_error="", refresh_error_code=""
        )
    except Exception:
        # Never let bookkeeping break the request that queued real work.
        pass


def record_refresh_error(userid, grpid, code, message=""):
    """Persist why this project's run failed, for /refreshstatus to return."""
    from serp.models import Refreshmanual

    try:
        Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).update(
            refresh_error=message or MESSAGES.get(code, ""),
            refresh_error_code=code,
        )
    except Exception:
        pass


def refresh_error_state(userid, grpid, refreshIns=None):
    """``(code, message, failed_keywords)`` for one project's most recent run.

    ``code`` is "" only when nothing is known to have gone wrong with THIS run.
    The live key check comes first because it is the cause of the recorded
    symptoms: an account with no usable key produces a stalled queue, not the
    other way round.

    ``failed_keywords`` is a standing count, not a per-run one -- see the module
    docstring. It never sets ``code`` on its own.
    """
    from account.capabilities import (
        SERP_KEY_MISSING,
        SERP_KEY_UNREADABLE,
        serp_key_state,
    )
    from serp.models import Accountusage, Keyword, Refreshmanual

    # Keywords with no current rank data because their last attempt failed.
    # Sticky until that keyword next succeeds, so it describes the project's
    # standing state, NOT the run just observed. Reported, never derived from.
    failed = 0
    try:
        failed = Keyword.objects.filter(
            fk_user_id=userid, fk_group_id=grpid, manual_call_mode="fail"
        ).count()
    except Exception:
        failed = 0

    usage = Accountusage.objects.filter(fb_user_id=userid).first()
    key_state = serp_key_state(usage)
    if key_state == SERP_KEY_MISSING:
        return CODE_NO_KEY, MESSAGES[CODE_NO_KEY], failed
    if key_state == SERP_KEY_UNREADABLE:
        return CODE_KEY_UNREADABLE, MESSAGES[CODE_KEY_UNREADABLE], failed

    if refreshIns is None:
        refreshIns = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).first()

    # The per-run record. The engine writes it once when a manual run drains and
    # writes ("", "") on a clean run, so an empty code here means "this run had
    # nothing to report" -- not "no run has ever reported". Its own message wins
    # over the generic one: the engine's carries the counts ("3 of 5 keywords
    # could not be checked"), which no lookup table can reconstruct.
    recorded = (getattr(refreshIns, "refresh_error_code", "") or "").strip()
    if recorded:
        message = (getattr(refreshIns, "refresh_error", "") or "").strip()
        return recorded, message or MESSAGES.get(recorded, ""), failed

    # No token means _fire() returns without calling anything, and a self-hosted
    # instance has no scheduler behind it -- queued work would wait forever.
    if not os.environ.get("ENGINE_TRIGGER_TOKEN", ""):
        status = (getattr(refreshIns, "refresh_status", "") or "").strip().lower()
        if status in ("start", "wait"):
            return CODE_ENGINE_DISABLED, MESSAGES[CODE_ENGINE_DISABLED], failed

    # Deliberately NOT `if failed > 0: return CODE_SERP_FAILED`. manual_call_mode
    # survives the run that set it, so that test would re-announce an old
    # failure every time the user refreshed a project that has since recovered
    # -- the same class of bug as reporting success on runkeyword == 0, only
    # inverted. The engine's per-run record above is what decides.
    return "", "", failed


def mark_run_outcome_reported(userid, grpid):
    """Clear the recorded run outcome once it has been reported to a client.

    A RUN OUTCOME IS NEWS, AND NEWS IS REPORTED ONCE.

    `refresh_error_code` records what the LAST run did. Reloading the dashboard
    re-runs nothing, so that record -- and the banner drawn from it -- survived
    every page load until another run happened. An event was being rendered as a
    standing condition, and it read as a fault the user could not clear.

    This is not dismissal. The condition the run alert reports is "there is an
    unreported run outcome", and reporting it makes that false, so the alert
    still goes away by ceasing to be true. The durable fact stays: the standing
    `failed_keywords` row takes over, worded as a state rather than as this
    run's outcome, and every affected keyword still reads "Could not be checked"
    in the keywords table.

    Returns True when a record was actually cleared.
    """
    from serp.models import Refreshmanual

    updated = Refreshmanual.objects.filter(
        fb_user_id=userid, fk_group_id=grpid
    ).exclude(refresh_error_code="", refresh_error="").update(
        refresh_error_code="", refresh_error=""
    )
    return bool(updated)
