"""What a group's captured model answers say about the brand, counted once.

Extracted from ``views.geo_share_of_voice`` so the Geo Citations page and the
rank dashboard read the same numbers from the same pass over the same rows.
Two implementations of "how many answers mentioned us" is how the old
share-of-voice percentage came to disagree with the trend chart beside it.

No provider calls: every value here is derived from ``LLMPromptAnalytics`` rows
already stored by a completed tracking run, and from the daily
``LLMMetricSnapshot`` aggregates written from those same rows.

A RATE IS NOT EVIDENCE; A RATE AND ITS COUNTS ARE
-------------------------------------------------
2 of 8 answers and 200 of 800 answers are both 25%, and they are not the same
finding. ``mentioning_answers`` and ``answers_total`` are the primary pair and
``answer_coverage`` is derived from them, never the other way round. Anything
rendering the percentage is expected to render the counts with it.

WHY THERE IS A SIGNIFICANCE VERDICT IN HERE
-------------------------------------------
This project's stored Geo history moves 0.50 -> 0.25 across four days, which a
chart draws as a decline. It is two answers, out of four and then out of eight,
and the 95% intervals around those two proportions overlap across most of their
range. Calling it a decline is a claim the data cannot carry, and it is worse
than merely wrong here: the prompts are written by the user, and a published
study measured a 6.6x swing in mention rate from prompt wording alone, so a
user can move this number without anything changing in the world.

``coverage_change.*.significant`` is decided here rather than in the frontend on
purpose. What is statistically sayable is a property of the measurement, not a
rendering choice, and a UI that decides it will decide it differently on the
next screen. The frontend's contract is one line: draw the delta only when
``significant`` is ``True``.

The interval is the **Wilson score interval**, and Newcombe's Wilson-based
interval for the difference of two proportions, not the normal approximation.
At n = 4 and n = 8 the normal approximation produces intervals that run past 0%
and 100% and understates them badly; Wilson is bounded, behaves at small n, and
is defined at x = 0 and x = n -- all of which this data hits.
"""

import math

# Two-sided 95%. One level, named once: an interval and the verdict drawn from
# it must not be able to disagree about how confident they are.
CONFIDENCE = 0.95
_Z = 1.959963984540054


def _pct(fraction):
    """A 0..1 fraction as a 0..100 percentage, one decimal."""
    return round(100.0 * fraction, 1)


def _wilson_bounds(successes, total):
    """95% Wilson score interval for one proportion, as 0..1 fractions.

    ``None`` when there is nothing to measure. Not ``(0.0, 1.0)``: "we have no
    answers" and "we have answers and the rate could be anything" are different
    statements, and only one of them is a measurement.
    """
    if not total or total <= 0:
        return None
    n = float(total)
    x = float(max(0, min(int(successes), int(total))))
    z2 = _Z * _Z
    denominator = n + z2
    centre = (x + z2 / 2.0) / denominator
    half = (_Z / denominator) * math.sqrt(x * (n - x) / n + z2 / 4.0)
    return max(0.0, centre - half), min(1.0, centre + half)


def _difference_bounds(x_from, n_from, x_to, n_to):
    """95% interval for (to - from) as a difference of two proportions.

    Newcombe's method 10 (1998): take each proportion's Wilson interval, then
    combine the distances from each estimate to the bound that pushes the
    difference outward. It inherits Wilson's small-sample behaviour rather than
    the normal approximation's, which is the whole reason for using it -- the
    counts on this data are single digits.

    ``None`` when either side measured no answers, which is not "no difference".
    """
    bounds_from = _wilson_bounds(x_from, n_from)
    bounds_to = _wilson_bounds(x_to, n_to)
    if bounds_from is None or bounds_to is None:
        return None

    p_from = float(x_from) / float(n_from)
    p_to = float(x_to) / float(n_to)
    low_from, high_from = bounds_from
    low_to, high_to = bounds_to
    delta = p_to - p_from

    low = delta - math.sqrt((p_to - low_to) ** 2 + (high_from - p_from) ** 2)
    high = delta + math.sqrt((high_to - p_to) ** 2 + (p_from - low_from) ** 2)
    return max(-1.0, low), min(1.0, high)


def _interval_payload(bounds):
    """A bounds pair as the payload shape, or ``None``."""
    if bounds is None:
        return None
    return {"low": _pct(bounds[0]), "high": _pct(bounds[1])}


def _date_string(value):
    """A stored snapshot date as ``YYYY-MM-DD``, "" when it is not a date.

    djongo hands a ``DateField`` back as a ``datetime`` often enough that a bare
    ``.isoformat()`` would put a time on some points and not others, and two
    strings for the same day would then compare unequal.
    """
    if not value:
        return ""
    if hasattr(value, "date"):
        value = value.date()
    try:
        return value.isoformat()
    except AttributeError:
        return ""


def _point(date, mentioning, answers):
    return {
        "date": date,
        "mentioning": int(mentioning),
        "answers": int(answers),
        # Derived from the two counts beside it, so a point can never show a
        # rate its own numerator and denominator contradict. null, not 0.0,
        # when nothing was measured -- 0% is a measured result.
        "rate": _pct(float(mentioning) / float(answers)) if answers else None,
    }


def _coverage_history(group, mentioning_now, answers_now):
    """The group's answer coverage over time, oldest first, as counts.

    Points come from ``LLMMetricSnapshot`` -- one row per group per day, written
    from the same analytics rows this module reads. Each stores the rate as a
    fraction plus ``prompts_measured``, so the numerator is recovered by
    multiplying the two and rounding: the rate is stored to three decimals and
    is exactly k/n, so at these counts the product lands on an integer. It is
    clamped to 0..n regardless, because a rounding artefact that let a numerator
    exceed its denominator would produce a rate above 100%.

    (``prompts_measured`` counts ANSWERS, not prompts -- one row per prompt per
    model. The field name is inherited and left alone; the value is the same
    denominator as ``answers_total``.)

    THE LAST POINT IS THE LIVE COUNTS
    ---------------------------------
    Today's snapshot and the live rows are the same answers aggregated twice,
    and they diverge whenever the rows are re-analysed without the snapshot
    being rewritten. Refreshing the newest point from the live counts means the
    headline and the end of the sparkline beside it cannot show two different
    numbers. The point keeps the SNAPSHOT's date -- that is when the run
    happened, and stamping it today would invent a measurement nobody took.

    A group with answers but no snapshot yet gets a single point dated "": the
    measurement is real, the day it belongs to was never recorded.
    """
    from llmtracker.models import LLMMetricSnapshot

    points = []
    snapshots = LLMMetricSnapshot.objects.filter(
        fk_group_id=group.id
    ).order_by("snapshot_date")
    for snapshot in snapshots:
        answers = int(snapshot.prompts_measured or 0)
        rate = float(snapshot.mention_rate or 0.0)
        named = max(0, min(int(round(rate * answers)), answers))
        points.append(_point(_date_string(snapshot.snapshot_date), named, answers))

    if answers_now:
        if points:
            points[-1] = _point(points[-1]["date"], mentioning_now, answers_now)
        else:
            points = [_point("", mentioning_now, answers_now)]
    return points


def _comparison(history, index):
    """The current coverage measured against ``history[index]``.

    ``available`` is false and every number null when there is no such earlier
    point, or when either end measured no answers. That is *unknowable*, and it
    is emphatically not ``significant: false`` -- false asserts "we compared, and
    the change was inside the noise", which a project measured once has not done.
    """
    blank = {
        "available": False,
        "from_date": "",
        "from_mentioning": None,
        "from_answers": None,
        "from_rate": None,
        "delta": None,
        "interval": None,
        "significant": None,
        "answers_delta": None,
    }
    if len(history) < 2:
        return blank

    current = history[-1]
    earlier = history[index]
    if earlier is current or not earlier["answers"] or not current["answers"]:
        return blank

    bounds = _difference_bounds(
        earlier["mentioning"], earlier["answers"],
        current["mentioning"], current["answers"],
    )
    if bounds is None:
        return blank

    return {
        "available": True,
        "from_date": earlier["date"],
        "from_mentioning": earlier["mentioning"],
        "from_answers": earlier["answers"],
        "from_rate": earlier["rate"],
        # Percentage POINTS, current minus earlier; negative is a fall in
        # coverage. Carried whether or not it is significant, because the
        # frontend needs the number to draw once it is told it may.
        "delta": round(current["rate"] - earlier["rate"], 1),
        "interval": _interval_payload(bounds),
        # THE SUPPRESSION FLAG. True only when the whole 95% interval for the
        # difference sits on one side of zero -- when "nothing changed" is not
        # among the values the data supports. Render the delta only for True.
        "significant": bounds[0] > 0.0 or bounds[1] < 0.0,
        # How the DENOMINATOR moved. Coverage can halve because the brand lost
        # ground or because the user added four prompts nothing mentions, and
        # this is the only field that tells those apart -- the same job
        # ``movement.keywords_delta`` does for the visibility score. Signed;
        # positive means more answers were measured than before.
        "answers_delta": current["answers"] - earlier["answers"],
    }


def geo_answer_summary(group):
    """Answer coverage, sentiment, cited sources and the coverage trend.

    Returns the full set of numbers ``/llmtracker/share-of-voice`` answers with,
    plus the rival brands named in the answers this brand was not, and the
    trend. Zeroes, empty lists and nulls when the group has never been tracked
    -- that is a valid state, not an error.
    """
    from llmtracker.models import LLMPrompt, LLMPromptAnalytics
    from llmtracker.views import get_domain_from_url

    rows = list(
        LLMPromptAnalytics.objects.filter(
            fk_prompt__fk_group=group, track_status="DONE"
        )
    )

    your_mentions = sum((row.mention_count or 0) for row in rows)
    brand = get_domain_from_url(group.domain_name) or (group.group_name or "You")

    sources = {}
    # Sources cited by answers that did NOT name the brand. Counted separately
    # from `sources` because it answers a different question: not "who gets
    # cited alongside us" but "who got the citation we did not".
    instead = {}
    for row in rows:
        for domain in (row.citations or []):
            sources[domain] = sources.get(domain, 0) + 1
            if not row.is_mention and domain != brand:
                instead[domain] = instead.get(domain, 0) + 1

    competitor_total = sum(sources.values())
    top_sources = sorted(
        ({"domain": domain, "count": count} for domain, count in sources.items()),
        key=lambda item: item["count"], reverse=True)[:15]
    cited_instead = [
        domain for domain, _ in
        sorted(instead.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]

    mentioning = [row for row in rows if row.is_mention]
    models_covering = len({row.model for row in mentioning})

    # THE MODEL DENOMINATOR IS MODELS ATTEMPTED, NOT MODELS THAT ANSWERED.
    # A provider that errors still writes an analytics row, with its model name
    # and `track_status="FAIL"` (views.py, the except branch around the
    # per-provider call). Counting DONE rows only -- as this did -- excluded the
    # failure from its own denominator, so the number read "1 of 1 models"
    # whether one model answered or one of four did, and a dead provider key
    # looked like full coverage.
    #
    # `answers_total` is deliberately NOT widened the same way: a provider that
    # errored produced no answer, so it must not dilute the coverage rate. It is
    # a gap in how many MODELS were heard from, not an answer that said nothing.
    #
    # A run where EVERY provider failed writes no rows at all (the `if not
    # succeeded` early return), so it is invisible here -- that state is carried
    # by the prompt's own track_status, not by this count.
    attempted = set(
        LLMPromptAnalytics.objects.filter(fk_prompt__fk_group=group)
        .values_list("model", flat=True)
    )
    # Unioned with the models that did answer so `models_covering` can never
    # exceed `models_total`, whatever the second query returns.
    models_total = len(attempted | {row.model for row in rows})

    # Prompts, so a reader can see the shape behind the answer count: "8 answers
    # from 8 prompts x 1 model". `prompts_total` is what the project has
    # configured and `prompts_answered` is how many produced an answer; the two
    # differ when a prompt has never been run or every provider failed on it.
    #
    # `prompts_total` is also the only field that separates "Geo was never set
    # up" (0) from "prompts exist but nothing has run yet" (> 0 with
    # `answers_total` 0). Both show zero answers and need different words.
    prompts_total = LLMPrompt.objects.filter(fk_group=group).count()
    prompts_answered = len({row.fk_prompt_id for row in rows})
    spos = sum(1 for row in mentioning if row.sentiment == "positive")
    sneg = sum(1 for row in mentioning if row.sentiment == "negative")
    sneu = len(mentioning) - spos - sneg
    if not mentioning:
        overall = "na"
    elif sneg > 0:
        # Negative wins, for brand safety -- one hostile answer matters more
        # than five neutral ones.
        overall = "negative"
    elif spos >= sneu:
        overall = "positive"
    else:
        overall = "neutral"

    answer_coverage = round(100.0 * len(mentioning) / len(rows), 1) if rows else 0.0

    history = _coverage_history(group, len(mentioning), len(rows))

    # Who was named in the answers this brand was not. Reads stored competitor
    # scores only -- no extraction and no provider call on a page load.
    from llmtracker.brands import group_competitor_summary

    rivals = group_competitor_summary(group)

    return {
        "brand": brand,
        "your_mentions": your_mentions,
        "answer_coverage": answer_coverage,
        "cited_total": competitor_total,
        "top_sources": top_sources,
        # DO NOT BUILD ON THIS, AND DO NOT DISPLAY IT. The `citations` array it
        # is derived from does not hold sources the model cited: the extractor
        # (views.py, get_domain_from_url and its caller) matches domain-shaped
        # SUBSTRINGS IN PROSE, and the stored answers contain no URLs at all.
        # The one value in the whole dataset, "searchapi.io", comes from a
        # markdown heading naming a competitor whose brand ends in ".io".
        # Rivals without a dot in their name -- Bright Data, Apify, Scrapy,
        # Zyte, Octoparse -- can never appear, though the stored text shows
        # Bright Data winning 6 of 6 answers that did not name the brand. So
        # "cited instead" reads as "one rival is taking your answers" when the
        # real figure is around fifteen. DEPRECATED and kept on the payload only
        # because it is pre-existing and still consumed by
        # app/src/pages/widget/dashboard_data.js. Read `answers_lost_to` below.
        "cited_instead": cited_instead,
        # THE HONEST REPLACEMENT. Brands NAMED in the answers that did not name
        # this brand, ranked by how many of those answers each appears in, each
        # entry carrying its own count. `answers_lost_total` is the denominator
        # those counts are measured against and travels with them, for the
        # reason this module's docstring gives about rates.
        #
        # An empty list means "no competitor set yet", not "nobody is winning",
        # which is why `competitors_tracked` sits beside it -- 0 tracked and 0
        # named are different statements and need different words on screen.
        #
        # NOT A SHARE OF VOICE, and it must not be rendered as a percentage of
        # anything. The competitor set is whatever detection proposed plus
        # whatever the user added, so a share computed against it would move
        # when the list improved rather than when the brand's standing did.
        "answers_lost_to": rivals["answers_lost_to"],
        "answers_lost_total": rivals["answers_lost_total"],
        "competitors_tracked": rivals["competitors_tracked"],
        "mentioning_answers": len(mentioning),
        "answers_total": len(rows),
        "models_covering": models_covering,
        "models_total": models_total,
        "prompts_total": prompts_total,
        "prompts_answered": prompts_answered,
        "overall_sentiment": overall,
        "sentiment_counts": {"positive": spos, "neutral": sneu, "negative": sneg},
        # 95% Wilson interval around the CURRENT coverage, in percentage points.
        # null when no answers have been measured. On 2 of 8 it reads 7.1-59.1,
        # which is the honest width of a headline built on eight answers and is
        # worth printing beside it.
        "coverage_interval": _interval_payload(
            _wilson_bounds(len(mentioning), len(rows))
        ),
        "confidence": CONFIDENCE,
        # Oldest first, every point carrying its own numerator and denominator,
        # so a sparkline cannot be drawn from rates whose counts nobody saw.
        "coverage_history": history,
        # Two comparisons, each with its own `significant` verdict.
        # `since_previous` is the change since the last measurement;
        # `since_first` is the change across the whole retained series, which is
        # what a four-point chart looks like it is showing. Neither may be
        # rendered as a movement unless its own flag is True.
        "coverage_change": {
            "since_previous": _comparison(history, -2),
            "since_first": _comparison(history, 0),
        },
    }
