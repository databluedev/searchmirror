"""One request for the whole rank dashboard, ordered by what needs doing.

The dashboard used to be assembled from eight independent widget calls
(/erocs_wdt, /Y25iX3dkdA, /JkcaW1RrZXl3b3wcm92ZW193aWRnZXQ, /compai/omptr_wdt,
/refreshstatus and friends). Each one re-queried the same keyword rows, each
answered with a different envelope (`st`/`dt` here, `status`/`data` there), and
none of them could say which of the numbers on screen the user should act on
first. This endpoint answers that question.

WHICH BLOCK LEADS DEPENDS ON THE PROJECT
----------------------------------------
`attention` names individual keywords that moved, and on a project with rank
history it is the point of the screen. On a project that has never ranked there
is nothing to name -- eight rows all reading "never ranked" is one fact printed
eight times -- so the counts move to `attention_groups` and `gap` leads instead:
the keywords the site does not rank for, and which competitors hold them. The
two are mutually exclusive by construction, so exactly one of them has something
to say, and the frontend renders whichever is non-empty.

WHAT IT REUSES RATHER THAN REIMPLEMENTS
---------------------------------------
* the visibility score: ``shared.scoring`` -- the same functions /erocs_wdt,
  /homeauth and /projectoverview call, so a fifth surface cannot disagree with
  the other four about what the score is;
* the failed-run reason: ``serp.refresh_error.refresh_error_state`` -- byte for
  byte the ``errc``/``err``/``fkw`` that /refreshstatus returns, from the one
  module that decides it;
* the Geo Citations numbers: ``llmtracker.geo_summary.geo_answer_summary`` --
  the same single pass over ``LLMPromptAnalytics`` that /llmtracker/
  share-of-voice returns, extracted so both read one implementation;
* cannibalisation: the same ``cannibalisation`` list the CZ widget renders;
* competitor positions: ``competitor.models`` joined on ``fk_keyword_id``, the
  same join /compai/ uses to pair a competitor's row with the user's own
  (competitor/views.py). ``competitors`` and ``gap`` are two questions asked of
  one load of those rows -- see ``_competitor_rows`` -- so the gap chart cannot
  name a competitor the list beside it does not.

The only thing computed here that exists nowhere else is the ranking of
`attention`, the gap between the site and its competitors, and the
movement/spread buckets they share their window with.

ZERO IS NOT "NOTHING HAPPENED"
------------------------------
Several numbers here can be zero for two entirely different reasons, and a
frontend given only the zero renders the wrong sentence. Each one carries a
companion field saying which it is: ``movement.comparable`` (there is a second
observation to compare against), ``competitors[].keywords`` and
``[].trend_comparable`` (the average and the trend are over something), and
``gap.covered`` (how many unranked keywords a competitor actually holds).
``ai.sentiment`` already did this, with "na". Anywhere a count is added here it
must be possible to tell an absence from a measured zero.

``ai`` extends the same rule from "is this zero real" to "is this MOVEMENT
real": ``ai.change.*.significant`` is null when there is nothing to compare
against, false when the change is inside the 95% interval, and true only when
the data actually supports drawing it. See ``_ai_block``.

RANK HISTORY, AND WHY THE WINDOW IS AN INDEX
--------------------------------------------
``Keyword.rank`` is current-first: the engine pushes each day's position at
index 0 (``push__rank__0``, automation_common.py). Index *n* is therefore *n*
observations ago, not *n* days ago -- a project that has not been checked for a
week has one observation for that week. Comparing by index compares "now"
against "the last time we had this many observations ago", which is the only
comparison the stored data actually supports; there is no per-observation
timestamp to compare against. A project with fewer observations than the window
is compared against its oldest one.

EMPTY PROJECTS ARE NOT AN ERROR
-------------------------------
A project created a minute ago has no keywords, no rank arrays, no competitors
and no answers. Every block below is built from a list that is allowed to be
empty, and every key is always present, because the first-run 500 (a view
indexing ``[0]`` into a history that does not exist yet) is the single most
common failure this codebase has.
"""

import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view

from account import verify as authPermission
from competitor.models import CompKeyword, CompProject
from serp.common import f_to_i, host_domain
from serp.models import Groups, Keyword
from serp.refresh_error import mark_run_outcome_reported, refresh_error_state
from shared.scoring import calculate_visibility_history

logger = logging.getLogger(__name__)


# Positions worse than this are "not ranked" as far as every other surface is
# concerned -- it is shared.scoring's rank_limit, and using a different number
# here would make the spread buckets disagree with the score above them.
RANK_LIMIT = 100

# Comparison window, in observations. Reported as `movement.window_days` for the
# frontend to label; see the module docstring on why it is an index.
WINDOW = 7

# Enough rows to act on, few enough to read without scrolling. The list is
# ranked, so the cap drops the least urgent items, never an arbitrary slice.
ATTENTION_LIMIT = 8

# Every reason `attention` can carry, most urgent first, with the phrase that
# completes "<count> <label>". The order is both the group order and the row
# order; there is one list so the two cannot drift apart.
ATTENTION_REASONS = (
    ("dropped_top10", "dropped out of the top 10"),
    ("declined", "lost positions"),
    ("cannibal", "have more than one page competing"),
    ("never_ranked", "have never ranked"),
)

# Reasons that earn an individual `attention` row. A row is worth naming when it
# says something about THAT keyword: `dropped_top10` and `declined` carry the
# two positions and the size of the fall, `cannibal` carries how many of the
# site's pages collide. `never_ranked` carries none of that -- every one of its
# rows is `from: 0, to: 0, delta: 0`, identical but for the keyword name, so
# twenty-eight of them state one fact twenty-eight times. It is reported as a
# count in `attention_groups`, and the keywords behind it are actionable through
# `gap`, which can say who holds the positions instead.
NAMED_REASONS = ("dropped_top10", "declined", "cannibal")

# Keyword names carried on a group, so the UI can write "28 have never ranked,
# including x, y and z" without a second request. The head of the ranked bucket,
# not a random slice.
GROUP_SAMPLE = 3

# Competitors on the gap chart. More than this and the bars stop being readable;
# the list is ranked by keywords held, so the cap drops the weakest holders.
GAP_HOLDER_LIMIT = 6

# Individual keywords on the gap list. Small on purpose -- these are meant to be
# the next things the user works on, not an inventory.
GAP_WORST_LIMIT = 5

# Points in the visibility sparkline, oldest first.
SPARK_POINTS = 14

# Sort key for an unranked keyword. Not RANK_LIMIT + 1: "outside the top 100"
# and "position 101" must not compare equal, or a keyword that genuinely sits at
# 101 outranks nothing.
_UNRANKED_SORT = 10 ** 6


def _position(row):
    """This keyword's current position, 0 when it is not ranked.

    ``rank[0]`` rather than ``ranknow`` for the same reason /erocs_wdt reads it:
    the visibility score is computed from the rank arrays, so a header that read
    ``ranknow`` could show "3 keywords in the top 10" beside a score computed
    from different numbers. They agree today; reading one of them everywhere is
    what keeps them agreeing.
    """
    history = row.get("rank") or []
    if history:
        return _as_position(history[0])
    return _as_position(row.get("ranknow"))


def _window_position(row):
    """This keyword's position at the start of the comparison window.

    Falls back to the oldest observation the keyword has, so a project with
    three days of history is compared against day one rather than against
    nothing.
    """
    history = row.get("rank") or []
    if not history:
        return 0
    return _as_position(history[min(WINDOW, len(history) - 1)])


def _as_position(value):
    """A stored rank as a position, or 0 for anything that is not one."""
    try:
        position = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return position if 0 < position <= RANK_LIMIT else 0


def _sortable(position):
    """Position ordered so that "better" is always smaller, unranked last."""
    return position if position else _UNRANKED_SORT


def _ever_ranked(row):
    """True when this keyword has held a position at some point, ever.

    Distinct from "is not ranked right now": a keyword that reached position 8
    last week and has since fallen out is a decline to act on, while one that
    has never appeared at all is a different problem with a different fix.
    """
    if _as_position(row.get("ranknow")):
        return True
    return any(_as_position(value) for value in (row.get("rank") or []))


def _modal(values):
    """The most common non-empty value, "" when there is none.

    A project's keywords may not share a region, language or device -- nothing
    stops a user adding one mobile keyword to a desktop project. The header
    reports what most of them use rather than pretending the mixture is a single
    setting; the keyword table is where the exceptions are visible.
    """
    counts = {}
    for value in values:
        value = str(value or "").strip().strip("()").strip()
        if value:
            counts[value] = counts.get(value, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def _isoformat(value):
    return value.isoformat() if value else ""


def _project_block(group, rows):
    last_checked = max(
        (row["lastranked_date"] for row in rows if row.get("lastranked_date")),
        default=None,
    )
    return {
        "name": group.group_name or "",
        "domain": group.domain_name or "",
        "region": _modal(row.get("region") for row in rows),
        "language": _modal(row.get("language") for row in rows),
        "device": _modal(row.get("platform") for row in rows),
        "last_checked": _isoformat(last_checked),
        # Null is legitimate -- the scheduler assigns a run time on its next
        # pass, and an instance with no cron never will. "" says "not
        # scheduled", which is a true statement about the project.
        "next_run": _isoformat(group.project_automation_time),
    }


def _visibility_block(rows):
    histories = [row.get("rank") or [] for row in rows]
    score_history = calculate_visibility_history(histories)

    positions = [_position(row) for row in rows]
    ranked = [position for position in positions if position]
    spark = [f_to_i(score) for score in reversed(score_history[:SPARK_POINTS])]

    score = f_to_i(score_history[0]) if score_history else 0
    previous = f_to_i(score_history[1]) if len(score_history) > 1 else score

    return {
        "score": score,
        "best": f_to_i(max(score_history)) if score_history else 0,
        "delta": score - previous,
        # Oldest first: a sparkline is drawn left to right, and score_history is
        # current-first like the rank arrays it is built from.
        "spark": spark,
        "first": sum(1 for position in positions if position == 1),
        "top3": sum(1 for position in positions if 1 <= position <= 3),
        "top10": sum(1 for position in positions if 1 <= position <= 10),
        # Keywords holding a position RIGHT NOW, anywhere in 1..RANK_LIMIT.
        #
        # It is a THIRD number, and neither of its two near-synonyms:
        #   * `unranked` below counts keywords that have never ranked in their
        #     whole history, so `len(rows) - unranked` counts a keyword that
        #     ranked last week and has since dropped out as still ranking;
        #   * `spread.p1 + p2_3 + p4_10 + p11_30` stops at position 30, so it
        #     omits a keyword sitting at 45 -- which `spread` files under
        #     `beyond` alongside the ones that do not rank at all.
        # The three coincide only while every ranked keyword sits inside the top
        # 30 and none has ever dropped out, which is true of the seeded data and
        # is not a property of the model. `ranked` is the only one of the three
        # that means "ranks today", so it is the only honest denominator for
        # `avg_position` and for a "5 of 7 ranked" tile.
        "ranked": len(ranked),
        # Mean position over `ranked` only. 0.0 means nothing ranks, which is
        # why `ranked` is published beside it: on a project where 28 of 30
        # keywords have never ranked, an average over the surviving 2 is a real
        # number but a thin one, and the frontend needs the denominator to say
        # so rather than printing it as if it described the project.
        "avg_position": _mean_position(positions),
        # Keywords that have NEVER held a position, not keywords unranked right
        # now -- those are `spread.beyond`. The two answer different questions:
        # this one is "how much of what I track has never worked", that one is
        # "where do I stand today".
        "unranked": sum(1 for row in rows if not _ever_ranked(row)),
    }


def _window_spans(rows):
    """Every keyword's individual comparison span, in days.

    ``_window_position`` falls back per keyword -- ``min(WINDOW, len - 1)`` --
    so a project does not have one comparison window, it has one per keyword.
    This is that set, and `window_actual`/`window_min` are its two ends.

    A keyword with a single observation contributes 0: it is compared against
    itself, which is a real span of zero days and always lands in `unchanged`.
    A keyword with NO observations contributes nothing at all -- it is not
    compared over zero days, it is not compared, and letting it push the minimum
    to 0 would report a project as spanning "0-7 days" because one keyword was
    added an hour ago and has never been checked.
    """
    return [
        min(WINDOW, len(row.get("rank") or []) - 1)
        for row in rows
        if row.get("rank")
    ]


def _observations(rows):
    """The most rank observations any one keyword in the project has.

    Per keyword rather than per project because that is how the data is stored:
    a keyword added yesterday holds one observation inside a project that has
    been running for months. The largest is what decides whether ANY comparison
    is possible at all.
    """
    return max((len(row.get("rank") or []) for row in rows), default=0)


def _keyword_count_delta(group, comparable):
    """Signed change in the number of tracked keywords over the window.

    WHY THIS NUMBER EXISTS
    ----------------------
    The visibility score divides by every tracked keyword, so adding ten
    keywords that do not rank drops the score without a single position having
    moved. Nothing else on the payload can tell that apart from a real loss --
    the sparkline just falls. This is the number that separates them.

    WHERE IT COMES FROM, AND WHY NOT FROM THE RANK ARRAYS
    ----------------------------------------------------
    ``Groups.total_Keyword`` -- the existing current-first, day-indexed count
    history that ``calculation.py`` writes (it inserts ``len(allKeywords)`` at
    index 0 and normalises the array against the group's age exactly as the
    engine normalises ``Keyword.rank``). Reading it means one stored series has
    one meaning, and this number shares its index with `movement`'s counters by
    construction rather than by coincidence.

    The obvious alternative -- counting keywords whose ``rank`` array is longer
    than the window -- was rejected because it is **structurally incapable of
    going negative**. A deleted keyword leaves no row behind, so a project that
    removed four keywords would report 0, and 0 would then mean both "the list
    did not change" and "the list shrank and I cannot see it". ``total_Keyword``
    is a snapshot of the count on each day, so a removal shows up as a fall.
    That is the whole reason the delta can be signed and honest.

    NULL, NEVER 0, WHEN THERE IS NO ANSWER
    --------------------------------------
    0 is a real, meaningful value here -- the keyword list did not change over
    the window -- so it cannot double as the unknown sentinel. ``None`` (null in
    the payload) is returned when there is no window to measure across, when the
    count history is too short to have a start point, or when what is stored
    cannot be read as a number. A guess would be worse than nothing: this number
    exists specifically to stop the user misreading a score movement, and a
    wrong one would cause the mistake it is meant to prevent.
    """
    if not comparable:
        return None

    history = group.total_Keyword or []
    if len(history) < 2:
        # A project whose count history has not been written yet. Real: the
        # array starts empty and `calculation.py` fills it on its first pass.
        return None

    try:
        # Same index and the same short-history fallback as `_window_position`,
        # so "the window" means one thing across the whole block.
        now = int(history[0])
        then = int(history[min(WINDOW, len(history) - 1)])
    except (TypeError, ValueError):
        return None

    return now - then


def _movement_block(rows, group):
    """How the project moved over the window -- or that it cannot yet say.

    NOTHING TO COMPARE IS NOT "NOTHING CHANGED"
    -------------------------------------------
    With a single rank observation every keyword's "now" and "then" are the same
    number, so the old counters answered ``unchanged: 30`` for a project that
    had been checked exactly once. That is a claim about stability the data does
    not support, and the frontend had no way to tell it apart from a genuinely
    static month. `comparable` is the flag: false means the three counters are
    zero because there is no second observation, and `first_comparison_at` says
    when there will be (the project's next scheduled run, "" when nothing is
    scheduled -- see `_project_block`).

    ABSENT IS NOT UNCHANGED EITHER
    ------------------------------
    A keyword that held no position at either end of the window has not "stayed
    where it was"; it was never anywhere. Counting it as `unchanged` is how a
    project with 28 keywords that have never ranked reported 30 unchanged and
    looked stable. Those keywords are `absent`, and `gap` is where they are
    actually answered. The four counters sum to the keyword count.
    """
    snapshots = _observations(rows)
    comparable = snapshots > 1
    spans = _window_spans(rows)

    movement = {
        "improved": 0,
        "declined": 0,
        # Held a position at both ends of the window, and the same one.
        "unchanged": 0,
        # No position at EITHER end. Distinct from `visibility.unranked`, which
        # counts keywords that have never ranked in their whole history; this
        # one is only about the two ends of this window.
        "absent": 0,
        # What the label WANTS to say. Kept unchanged and unconditional: it is
        # the configured window, not a measurement.
        "window_days": WINDOW,
        # What the comparison actually spans, which on a project younger than
        # the window is less. `window_days: 7` on a project with five days of
        # history describes a measurement nobody took -- the same fault as the
        # three zeros, one level up: the number is real and the period it is
        # attributed to is not. Never greater than `window_days`; null when
        # there is no comparison at all.
        #
        # It is the OUTER BOUND, not a single shared window. `_window_position`
        # falls back per keyword, so a keyword with a shorter history is
        # compared over a shorter span than this: on a project whose oldest
        # keywords hold five observations and whose newest hold three, this
        # reads 4 while most of the keywords span 2. It is the longest span any
        # keyword contributes, which is the honest ceiling for one label over a
        # mixed set.
        "window_actual": min(WINDOW, snapshots - 1) if comparable else None,
        # The other end of the same set: the SHORTEST span any keyword
        # contributes. Equal to `window_actual` only when every keyword shares
        # one window, which is rarer than it looks -- a project is non-uniform
        # the moment one keyword is added later than the rest.
        #
        # 0 is a real value, not a sentinel: a keyword with a single observation
        # is compared against itself over zero days. null means the span could
        # not be determined at all -- no comparison, or no keyword with any
        # history to measure. Keywords with no observations are excluded rather
        # than counted as 0; see `_window_spans`.
        "window_min": min(spans) if (comparable and spans) else None,
        "comparable": comparable,
        "snapshots": snapshots,
        "first_comparison_at": "",
        # Signed, and null rather than 0 when unmeasurable -- see
        # `_keyword_count_delta`. Positive means keywords were added, which is
        # NOT a ranking improvement: it is the explanation for a score that fell
        # without any position moving.
        "keywords_delta": _keyword_count_delta(group, comparable),
        # True when a keyword that MOVED was measured over a shorter span than
        # `window_actual` -- i.e. when the single window label is decorating a
        # real finding with a period that keyword never had.
        #
        # It is deliberately narrower than "the spans are mixed", which is true
        # of almost every project and would therefore be ignored. A keyword with
        # a short span that lands in `absent` or `unchanged` is not misreported:
        # it cannot have moved during days it did not exist, so a longer label
        # still describes it truthfully. Only a mover makes the label overstate
        # something that actually happened.
        #
        # null, not false, when there is no comparison -- false would assert
        # "checked, and no mover was mixed", which is not what an unmeasured
        # project knows.
        "window_mixed": None,
    }

    if not comparable:
        movement["first_comparison_at"] = _isoformat(group.project_automation_time)
        return movement

    ceiling = movement["window_actual"]
    mixed = False

    for row in rows:
        now = _position(row)
        then = _window_position(row)
        if not now and not then:
            movement["absent"] += 1
            continue
        current, previous = _sortable(now), _sortable(then)
        if current == previous:
            movement["unchanged"] += 1
            continue
        if current < previous:
            movement["improved"] += 1
        else:
            movement["declined"] += 1

        history = row.get("rank") or []
        span = min(WINDOW, len(history) - 1) if history else None
        if span is not None and span < ceiling:
            mixed = True

    movement["window_mixed"] = mixed
    return movement


def _spread_block(rows):
    spread = {"p1": 0, "p2_3": 0, "p4_10": 0, "p11_30": 0, "beyond": 0}
    for row in rows:
        position = _position(row)
        if position == 1:
            spread["p1"] += 1
        elif 2 <= position <= 3:
            spread["p2_3"] += 1
        elif 4 <= position <= 10:
            spread["p4_10"] += 1
        elif 11 <= position <= 30:
            spread["p11_30"] += 1
        else:
            # Position 0 -- no rank -- lands here too. A keyword the user cannot
            # find is beyond position 30 by every definition that matters, and
            # splitting it out would leave the five buckets not summing to the
            # keyword count.
            spread["beyond"] += 1
    return spread


def _competing_pages(row):
    """How many of the site's own pages rank for this keyword.

    `cannibalisation` is a plain list of the site's URLs seen in the results.
    A conflict needs TWO of them -- a list of one is simply the page that ranks,
    which is the normal, healthy case. `serializers.py` has always drawn the
    line at `> 1` for its `cnn` flag; drawing it anywhere else here would put a
    keyword on the action list for having a page.
    """
    return len(row.get("cannibalisation") or [])


def _attention_row(row, reason, frm, to):
    return {
        "kwid": str(row.get("id") or ""),
        "kw": row.get("keyword") or "",
        "from": frm,
        "to": to,
        # Signed movement in the reader's direction: NEGATIVE IS WORSE, because
        # a rank of 6 is worse than a rank of 5 and every consumer of a rank
        # tracker reads "-1" as a decline. It is `from - to`, so it can never
        # contradict the two positions printed beside it.
        #
        # 0 when either end is unranked, and that is the whole reason to read
        # this field rather than subtract the positions yourself: `from - to`
        # applied blindly turns "was 4, now nowhere" into +4 and paints a total
        # loss as an improvement. There is no honest number for that case, so
        # this returns none and lets `from`/`to` and `reason` carry it.
        "delta": (frm - to) if (frm and to) else 0,
        # The site's own pages competing for this keyword. 2 or more is the
        # cannibalisation conflict; 0 or 1 is normal. Present on every row, not
        # just `cannibal` ones -- a keyword can be declining AND cannibalised,
        # and only the more urgent reason is reported.
        "pages": _competing_pages(row),
        "reason": reason,
    }


def _numeric_kwid(item):
    """Sort key for "oldest first". Ids are strings in the payload, and sorting
    those lexicographically puts keyword 10 before keyword 8."""
    kwid = item.get("kwid") or ""
    return (0, int(kwid)) if kwid.isdigit() else (1, 0)


def _attention_buckets(rows):
    """Every keyword worth acting on, bucketed by reason and fully ranked.

    Four reasons, in descending order of what they cost the user:

    1. ``dropped_top10`` -- ranked in the top ten at the start of the window and
       does not now. This is the only bucket where traffic has already been
       lost, so it leads regardless of how large the numeric fall was.
    2. ``declined`` -- still ranked, but further down than it was. Ordered by
       positions lost, largest first.
    3. ``cannibal`` -- more than one page of the site competes for the keyword.
       A standing structural problem rather than a change, so it ranks below
       anything that moved today; ordered best-position first, because the
       conflict costs most where the keyword already ranks well.
    4. ``never_ranked`` -- tracked but has never held a position. Last: it is
       the least urgent because nothing has been lost, and oldest first, because
       a keyword that has never ranked in six months is a stronger signal than
       one added yesterday.

    A keyword appears once, under its most urgent reason. Every row carries
    `delta` (negative is worse, 0 when a position is missing at either end) and
    `pages` (the site's own pages competing for the keyword).

    NOTHING IS CAPPED HERE. The buckets are the complete, ranked truth;
    `_attention_block` takes the rows worth naming and `_attention_groups_block`
    counts all of them, so the count on a group is the real total and not the
    length of a list that was already trimmed to eight.
    """
    seen = set()
    dropped, declined, cannibal, never = [], [], [], []

    for row in rows:
        key = row.get("id")
        now = _position(row)
        then = _window_position(row)

        if 1 <= then <= 10 and not 1 <= now <= 10:
            dropped.append(_attention_row(row, "dropped_top10", then, now))
            seen.add(key)
        elif then and now and now > then:
            declined.append(_attention_row(row, "declined", then, now))
            seen.add(key)
        elif then and not now:
            # Fell out of the results from outside the top ten. Still a loss,
            # still a decline -- it just did not cross the threshold that makes
            # the first bucket urgent.
            declined.append(_attention_row(row, "declined", then, now))
            seen.add(key)

    for row in rows:
        key = row.get("id")
        if key in seen:
            continue
        if _competing_pages(row) > 1:
            cannibal.append(
                _attention_row(row, "cannibal", _window_position(row), _position(row))
            )
            seen.add(key)
        elif not _ever_ranked(row):
            never.append(_attention_row(row, "never_ranked", 0, 0))
            seen.add(key)

    dropped.sort(key=lambda item: (-_sortable(item["to"]), item["from"]))
    # `delta` is 0 exactly when the keyword fell out of the results altogether,
    # which is a total loss and therefore leads the bucket -- it is not a
    # keyword that did not move. Everything else here slipped, so delta <= -1
    # and ascending order puts the largest fall first.
    declined.sort(key=lambda item: (0 if item["delta"] == 0 else 1, item["delta"]))
    cannibal.sort(key=lambda item: _sortable(item["to"]))
    never.sort(key=_numeric_kwid)

    return {
        "dropped_top10": dropped,
        "declined": declined,
        "cannibal": cannibal,
        "never_ranked": never,
    }


def _attention_block(buckets):
    """The keywords worth NAMING, most urgent first.

    Only `NAMED_REASONS` reach this list. The bulk states -- currently just
    `never_ranked` -- are counted in `attention_groups` instead, because a list
    of eight rows that all read "never ranked" is one fact printed eight times
    in the most prominent block on the screen, and it crowded out the three
    reasons that do point at a specific keyword.

    This list is therefore allowed to be empty, and on a young project it will
    be: nothing has moved yet because there is nothing to move from.
    """
    named = []
    for reason in NAMED_REASONS:
        named.extend(buckets.get(reason) or [])
    return named[:ATTENTION_LIMIT]


def _attention_groups_block(buckets):
    """One row per reason, with the count of every keyword in it.

    Present for all four reasons whether or not any keyword is in them, so the
    frontend reads a fixed set of keys rather than discovering which reasons
    exist from the data. A group with `count: 0` is a true statement -- nothing
    dropped out of the top ten -- and it is the frontend's call whether saying
    so is worth the space.
    """
    groups = []
    for reason, label in ATTENTION_REASONS:
        bucket = buckets.get(reason) or []
        groups.append(
            {
                "reason": reason,
                "count": len(bucket),
                "label": label,
                # The head of an already-ranked bucket: the most urgent few, and
                # for `never_ranked` the oldest few. Names only -- a sample is
                # for writing a sentence, not for rendering a table.
                "sample": [item["kw"] for item in bucket[:GROUP_SAMPLE] if item["kw"]],
            }
        )
    return groups


def _mean_position(positions):
    """Mean position across the ranked entries only, 0.0 when there are none.

    Unranked keywords are left out rather than counted as zero: a site tracked
    on ten keywords and ranking for two has an average position of whatever
    those two are, and averaging in eight zeroes would report it as the
    strongest domain on the page. Counting them as 101 is no better -- it
    reports a site that ranks second for two keywords as sitting near the bottom
    of page ten.

    Used for the site's own average and for every competitor's, because "average
    position" has to mean the same thing on both sides of the screen or the
    stat row and the competitor table cannot be compared by eye. The caller is
    responsible for publishing the denominator beside it (`visibility.ranked`,
    `competitors[].keywords`, `gap.holders[].keywords`), since 0.0 here means
    "nothing ranked" and would otherwise read as the best score on the page.

    THIS DIVERGES FROM THE INDUSTRY CONVENTION, DELIBERATELY. Semrush counts an
    unranked keyword as position 100, and Nozzle as 101, both explicitly to stop
    averages being skewed by exclusions. Researched 2026-09-02; on this data the
    conventional formula would report project 4 at 94.5 rather than 3.0.

    We do not adopt it because our headline score already tells that story.
    `calculate_visibility_score` divides by ALL keywords, so unranked entries
    drag it down -- project 4 scores 4/100, which is the "you are nowhere"
    reading. Making this number 94.5 as well would say the same thing twice and
    cost the complementary one: how well the site does *where it appears at all*.
    The two are only contradictory when the denominator is hidden, which is the
    caller's obligation above, not a reason to change the measure.

    If you are here because a tile read 3.0 for a project ranking on 2 of 30
    keywords, the bug is the missing denominator on that tile.
    """
    ranked = [position for position in positions if position]
    if not ranked:
        return 0.0
    return round(sum(ranked) / float(len(ranked)), 1)


def _competitor_rows(userid, grpid):
    """This project's competitors and their tracked keywords, loaded once.

    Two blocks read this: `competitors` (how strong is each rival overall) and
    `gap` (which of MY unranked keywords does each of them hold). They are the
    same rows answering two questions, so they are fetched once and passed in --
    two independent pairs of queries could return different competitor sets
    inside one response, and the gap chart would then disagree with the
    competitor list printed beside it.

    Rows are keyed by ``fk_cp_project_id`` and carry ``fk_keyword_id``, which is
    the join back to ``serp.Keyword`` that /compai/ uses (competitor/views.py
    reads the same field to pair a competitor's row with the user's own).

    Returns ``([], {})`` for a project with no competitors -- the ordinary state
    of a project nobody has added one to, not an error.
    """
    projects = list(
        CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).values(
            "id", "cp_domain_name"
        )
    )
    if not projects:
        return [], {}

    by_project = {project["id"]: [] for project in projects}
    keyword_rows = CompKeyword.objects.filter(
        fk_user_id=userid, fk_group_id=grpid
    ).values("fk_cp_project_id", "fk_keyword_id", "rank", "ranknow")
    for row in keyword_rows:
        bucket = by_project.get(row.get("fk_cp_project_id"))
        if bucket is not None:
            bucket.append(row)

    return projects, by_project


def _competitors_block(projects, by_project):
    competitors = []
    for project in projects:
        rows = by_project.get(project["id"]) or []
        now = [_position(row) for row in rows]
        # Only keywords ranked at BOTH ends of the window, so the trend reports
        # movement rather than a change in which keywords happen to be ranked.
        paired = [
            (_position(row), _window_position(row))
            for row in rows
            if _position(row) and _window_position(row)
        ]
        trend = "flat"
        if paired:
            drift = (
                sum(then for _, then in paired) - sum(current for current, _ in paired)
            ) / float(len(paired))
            # "up" means better visibility -- a smaller position number. Half a
            # position of drift is noise from one keyword moving; below that the
            # honest answer is that nothing happened.
            if drift > 0.5:
                trend = "up"
            elif drift < -0.5:
                trend = "down"

        competitors.append(
            {
                "domain": host_domain(project.get("cp_domain_name") or ""),
                "avg_position": _mean_position(now),
                # How many keywords that average is over. `avg_position` is 0.0
                # both for a competitor tracked on nothing and for one tracked
                # on twenty keywords and ranking for none; without this the
                # frontend cannot tell "no data" from "ranks for nothing", and
                # 0.0 printed in a position column reads as the best score on
                # the page.
                "keywords": sum(1 for position in now if position),
                "trend": trend,
                # False when no keyword was ranked at BOTH ends of the window,
                # which is when `trend` falls back to "flat". "Flat" then means
                # "nothing to measure", not "did not move" -- the same two
                # statements `movement.comparable` separates.
                "trend_comparable": bool(paired),
            }
        )

    # Strongest first; a competitor ranking for nothing sorts last rather than
    # first, which a raw ascending sort on 0.0 would do.
    competitors.sort(key=lambda item: item["avg_position"] or _UNRANKED_SORT)
    return competitors


def _gap_block(rows, projects, by_project):
    """For the keywords the site does not rank for, who does.

    This is the one block that joins the two halves of the payload. Everything
    else reports on the site OR on its competitors; a project like the one this
    was built against -- twenty-eight keywords that have never ranked, six
    competitors that rank for several of them -- has no interesting number
    anywhere until the two are put side by side. "28 keywords never ranked" is a
    complaint; "and docs.apify.com holds two of them at position 2.5" is a task.

    WHICH KEYWORDS COUNT AS UNRANKED
    --------------------------------
    ``_ever_ranked`` -- never held a position in its whole history -- and not
    "has no position today". It is the same set `visibility.unranked` and the
    `never_ranked` attention group count, so the three numbers on the screen
    cannot disagree about how many keywords are in trouble. A keyword that
    ranked last week and slipped out today is a decline, and `attention` already
    names it; putting it here too would report one problem in two places.

    `covered` is the honest denominator for `holders`: the unranked keywords a
    competitor actually holds. The rest -- unranked, and nobody tracked ranks
    for them either -- are not an opportunity anyone can see from this data, so
    they are counted out of the total rather than silently folded into it.
    """
    unranked = {
        row.get("id"): row for row in rows if not _ever_ranked(row)
    }
    gap = {
        "unranked_total": len(unranked),
        "covered": 0,
        "holders": [],
        "worst": [],
    }
    if not unranked or not projects:
        return gap

    # keyword id -> (position, domain) of the strongest competitor on it.
    best = {}
    holders = []
    for project in projects:
        domain = host_domain(project.get("cp_domain_name") or "")
        held = []
        for competitor_row in by_project.get(project["id"]) or []:
            kwid = competitor_row.get("fk_keyword_id")
            if kwid not in unranked:
                continue
            position = _position(competitor_row)
            if not position:
                # Tracked against this keyword but not ranking for it either.
                # Neither side is winning it, so it is not a gap.
                continue
            held.append(position)
            # Position first, domain second, so a tie between two competitors
            # resolves the same way on every request rather than following
            # whatever order the queryset happened to return.
            if kwid not in best or (position, domain) < best[kwid]:
                best[kwid] = (position, domain)
        if held:
            holders.append(
                {
                    "domain": domain,
                    "keywords": len(held),
                    "avg_position": _mean_position(held),
                }
            )

    # Breadth first: a competitor holding nine of these keywords is a bigger
    # problem than one holding two of them very well. Position breaks the tie.
    holders.sort(key=lambda item: (-item["keywords"], item["avg_position"]))

    worst = [
        {
            "kwid": str(kwid),
            "kw": unranked[kwid].get("keyword") or "",
            "best_competitor": domain,
            "their_position": position,
        }
        for kwid, (position, domain) in best.items()
    ]
    # Strongest competitor first: position 1 held by a rival on a keyword the
    # site has never ranked for is the widest gap on the project.
    worst.sort(key=lambda item: (item["their_position"], _numeric_kwid(item)))

    gap["covered"] = len(best)
    gap["holders"] = holders[:GAP_HOLDER_LIMIT]
    gap["worst"] = worst[:GAP_WORST_LIMIT]
    return gap


def _ai_block(group):
    """Geo Citations, from the same pass over answers /share-of-voice returns.

    THE COUNTS ARE THE HEADLINE, THE PERCENTAGE IS NOT
    --------------------------------------------------
    `mentioning_answers` / `answers_total` is "2 of 8 answers"; `coverage` is
    the same fact as 25.0. They are published together, and the pair leads,
    because 2-of-8 and 200-of-800 are the same rate and are not the same
    evidence. `coverage_interval` is the 95% Wilson interval around that
    percentage -- on 2 of 8 it spans 7.1 to 59.1, which is most of the range,
    and is the fastest way to show a reader what eight answers can support.

    A TREND IS NOT SHOWN UNLESS IT IS ONE
    -------------------------------------
    `coverage_change.since_previous` and `.since_first` each carry a `delta` in
    percentage points AND a `significant` flag; the delta is renderable only
    when the flag is True. The verdict is computed in
    ``llmtracker.geo_summary`` from the two proportions' counts, not here and
    not in the frontend -- see that module for why, and for why the interval is
    Wilson rather than the normal approximation. `answers_delta` on the same
    object is the `movement.keywords_delta` of this block: coverage falls when
    prompts are added that nothing mentions, and nothing else can tell that
    apart from losing ground.

    Every key is present on a project that has never run Geo: the counts are 0,
    the intervals and the deltas are null (not 0, not false -- unmeasured), and
    `history` is empty.
    """
    from llmtracker.geo_summary import geo_answer_summary

    summary = geo_answer_summary(group)
    return {
        "mentioning_answers": summary["mentioning_answers"],
        "answers_total": summary["answers_total"],
        "sentiment": summary["overall_sentiment"],
        # `cited_instead` IS DELIBERATELY NOT FORWARDED. The array behind it is
        # domain-shaped substrings found in prose, not sources any model cited
        # -- see the comment on `cited_instead` in llmtracker/geo_summary.py for
        # what it actually matches and why the number it produces understates
        # the competitor set by an order of magnitude. It was on this block
        # until 2026-09-02 and nothing in app/ reads it any more. Do not add it
        # back; the honest replacement is competitor-brand extraction from the
        # answer text, which is separate work.
        #
        # Percent, one decimal -- the SECONDARY display. 0.0 with
        # `answers_total: 0` means nothing was measured, which is exactly when
        # `coverage_interval` is null; the two are the pair to read together.
        "coverage": summary["answer_coverage"],
        # {"low", "high"} in percent, or null when no answer has been measured.
        "coverage_interval": summary["coverage_interval"],
        "confidence": summary["confidence"],
        # How many of the models ATTEMPTED named the brand at all. Same
        # counts-over-rate rule: "1 of 1 models", never "100%". A provider whose
        # key failed counts in `models_total` and not in `models_covering`, so
        # the pair reads as the gap it is.
        "models_covering": summary["models_covering"],
        "models_total": summary["models_total"],
        # The shape behind `answers_total`: "8 answers from 8 prompts x 1
        # model". `prompts_total` is also what separates the two empty states --
        # 0 means Geo was never set up, and >0 with `answers_total: 0` means
        # prompts exist but nothing has run. They need different wording.
        "prompts_total": summary["prompts_total"],
        "prompts_answered": summary["prompts_answered"],
        # Oldest first, each point {date, mentioning, answers, rate}.
        "history": summary["coverage_history"],
        "change": summary["coverage_change"],
        # The honest replacement for `cited_instead` above: brands actually
        # NAMED in the answers that did not name this one, extracted from the
        # stored answer text rather than matched as domain-shaped substrings.
        # On the seeded project the old field found 1 rival and this finds 15 --
        # Bright Data appears in 6 of 6 lost answers and could never surface
        # before, because its name contains no dot.
        #
        # NOT a share of voice, and it must not be rendered as a percentage:
        # the competitor set is whatever detection proposed plus whatever the
        # user added, so a share over it would move when detection improved
        # rather than when the brand's standing did. `answers_lost_total` is the
        # denominator to publish beside any count taken from it.
        "answers_lost_to": summary["answers_lost_to"],
        "answers_lost_total": summary["answers_lost_total"],
        "competitors_tracked": summary["competitors_tracked"],
    }


_DEFAULT_PAGES = 3


def _pages_for(row, group):
    """Result pages one re-check of this keyword will fetch, and so cost."""
    for candidate in (row.get("serp_pages"), getattr(group, "serp_pages", None)):
        try:
            pages = int(candidate)
        except (TypeError, ValueError):
            continue
        if pages > 0:
            return pages
    return _DEFAULT_PAGES


def _recheck_action(failed_ids, failed_searches):
    """What the user can do about it, with the bill stated up front."""
    if not failed_ids:
        return None
    count = len(failed_ids)
    return {
        "kind": "recheck",
        "keyword_ids": list(failed_ids),
        "label": "Re-check %d keyword%s" % (count, "" if count == 1 else "s"),
        "searches": failed_searches,
        "cost_note": "This spends %d DataBlue search%s, billed to your own API key."
        % (failed_searches, "" if failed_searches == 1 else "es"),
    }


def _alerts_block(group, rows, run, visibility, failed_ids=None, failed_searches=0):
    """EVERY row the alert surface should render, in order, worst first.

    This is the whole list now, run failure included -- the client renders what
    it is given and decides nothing.

    Distinct from `attention`, which is always about a specific keyword. These
    are about the project: nothing is scheduled, there is nothing to measure
    yet, the last check left keywords without data.

    WHY THE CLIENT NO LONGER JOINS THESE
    ------------------------------------
    The rule used to live on both sides and the halves did not meet. This
    function withheld the `failed_keywords` alert whenever a run had failed, on
    the grounds that `run.err` already said it -- and the client then appended
    the standing count back, because it only suppressed its own row when it saw
    the alert this function had deliberately not sent. Every failed run
    therefore rendered TWO rows about the same keywords.

    A rule that lives in two places is a rule that will disagree with itself.
    It lives here now. `run` is still sent, unchanged, for the refresh bar --
    which watches one run in flight and needs a different thing from a screen
    describing a project's standing state.

    THE JOIN ITSELF. A run failure and the standing count are the same fact
    when the standing count is entirely explained by that run, and only this
    side can tell: it takes comparing the keywords the run failed against the
    keywords currently without data. `failed_ids` carries that comparison.
    """
    alerts = []

    # Worst first, and a failed run explains every other number on the page.
    if run.get("errc") or run.get("err"):
        row = {
            "code": run.get("errc") or "run_failed",
            "severity": "warn",
            "text": run.get("err") or "The last ranking run did not finish.",
        }
        # Only offer to re-check when there is something specific to re-check.
        action = _recheck_action(failed_ids, failed_searches)
        if action:
            row["action"] = action
        alerts.append(row)

    if not rows:
        alerts.append(
            {
                "code": "no_keywords",
                "severity": "info",
                "text": "This project has no keywords yet. Add some to start tracking.",
            }
        )
    elif not group.project_automation_time:
        alerts.append(
            {
                "code": "not_scheduled",
                "severity": "info",
                "text": "No daily run is scheduled for this project yet. It is assigned on the scheduler's next pass.",
            }
        )

    # The standing count, and ONLY when the run row above does not already
    # account for it. `fkw` is sticky between runs (refresh_error.py), so it
    # can be non-zero long after the run that caused it -- and when a run has
    # just failed for exactly these keywords, saying it twice is saying it
    # twice.
    if run["fkw"] and not (run.get("errc") or run.get("err")):
        failed = run["fkw"]
        row = {
            "code": "failed_keywords",
            "severity": "info",
            # Worded as a state, not as the outcome of the run just watched.
            "text": "%d %s no current rank data."
            % (failed, "keyword has" if failed == 1 else "keywords have"),
        }
        action = _recheck_action(failed_ids, failed_searches)
        if action:
            row["action"] = action
        alerts.append(row)

    if rows and visibility["unranked"] == len(rows):
        alerts.append(
            {
                "code": "never_ranked",
                "severity": "info",
                "text": "None of this project's keywords have ranked yet. Check the domain and region are right.",
            }
        )

    return alerts


def _overview(group):
    """Build the whole payload for one project."""
    userid = group.fk_user_id
    grpid = group.id

    rows = list(
        Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).values(
            "id",
            "keyword",
            "rank",
            "ranknow",
            "cannibalisation",
            "region",
            "language",
            "platform",
            "lastranked_date",
        )
    )

    errcode, errmessage, failed = refresh_error_state(userid, grpid)
    run = {"errc": errcode, "err": errmessage, "fkw": failed}
    # Which keywords, not just how many: the alert offers to re-check exactly
    # these, and a re-check that names its targets can be priced before it
    # spends anything.
    failed_rows = list(
        Keyword.objects.filter(
            fk_user_id=userid, fk_group_id=grpid, manual_call_mode="fail"
        ).values("id", "serp_pages")
    ) if failed else []
    failed_ids = [row["id"] for row in failed_rows]
    # Priced here, not in the browser: only this side knows each keyword's own
    # depth, and a control that spends the account holder's provider credits
    # has to say what it will cost BEFORE they agree to it.
    failed_searches = sum(_pages_for(row, group) for row in failed_rows)
    visibility = _visibility_block(rows)
    buckets = _attention_buckets(rows)
    projects, by_project = _competitor_rows(userid, grpid)

    alerts = _alerts_block(group, rows, run, visibility, failed_ids, failed_searches)

    # Reported once. See refresh_error.mark_run_outcome_reported -- the run row
    # is news, and it was redrawn on every page load until the next run
    # happened. Cleared only when an alert was actually produced from it, so a
    # response that never reached a browser cannot swallow the only report of a
    # failed run.
    if any(row.get("severity") == "warn" for row in alerts):
        mark_run_outcome_reported(userid, grpid)

    return {
        "status": "true",
        "project": _project_block(group, rows),
        "alerts": alerts,
        "attention": _attention_block(buckets),
        "attention_groups": _attention_groups_block(buckets),
        "visibility": visibility,
        "movement": _movement_block(rows, group),
        "spread": _spread_block(rows),
        "gap": _gap_block(rows, projects, by_project),
        "competitors": _competitors_block(projects, by_project),
        "ai": _ai_block(group),
        "run": run,
    }


@api_view(["POST"])
def dashboard_overview(request):
    """POST {"userid", "grpid"} -> the whole dashboard in one response.

    Ownership is enforced twice, as everywhere else here: UserIdOwnershipMiddleware
    refuses a userid that is not the caller's before the view runs, and
    ``verify.validate`` re-checks the token against that userid inside it. The
    group lookup is scoped to the user, so a valid caller naming someone else's
    project gets the same answer as one naming a project that does not exist.
    """
    if not authPermission.validate(request, "POST"):
        return JsonResponse(
            {"status": "false", "message": "Unauthorized access"}, status=403
        )

    # .get(), not [] -- see refresh_error.py and views.refreshstatus. A body
    # missing one field is a 400, not a traceback.
    userid = str(request.data.get("userid") or "").strip()
    grpid = str(request.data.get("grpid") or "").strip()

    if not userid.isdigit() or not grpid.isdigit():
        return JsonResponse(
            {"status": "false", "message": "userid and grpid are required."},
            status=400,
        )

    group = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
    if not group:
        return JsonResponse(
            {"status": "false", "message": "Project not found."}, status=404
        )

    try:
        return JsonResponse(_overview(group))
    except Exception:
        # Logged with the traceback rather than swallowed by `except: pass`,
        # which is how the widgets this replaces made a broken query look like
        # an empty project.
        logger.exception("dashboard_overview failed for user %s group %s", userid, grpid)
        return JsonResponse(
            {"status": "false", "message": "Something went wrong"}, status=500
        )
