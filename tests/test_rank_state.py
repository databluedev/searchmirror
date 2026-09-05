"""An unmeasured rank is never presented as a rank.

`ranknow == 0` meant three different things and the API rendered all three as
the number 101: checked-and-not-found, checked-and-failed, and never-checked.
Only the first is a measurement. And 101 was not the ceiling either -- the
default depth is three pages of ten, so a keyword that did not appear was
absent from the first 30, which is why the export rendered the same value as
">30" while the history chart plotted it as a position.

These pin the replacement: four states, a position only when there is one, and
a ceiling derived from the depth actually searched.
"""

import sys
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
for source_root in (ROOT, BACKEND):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from serp import rank_state as rs  # noqa: E402


# --- the four states --------------------------------------------------------


def test_a_ranked_keyword_reports_its_position():
    value, state, ceiling, sort_key = rs.rank_state(
        {"ranknow": 7, "rank": [7, 8], "manual_call_mode": "done"}
    )
    assert (value, state) == (7, rs.RANKED)
    assert sort_key == 7, "a ranked keyword must sort by its actual position"


def test_measured_but_not_found_is_not_a_position():
    value, state, ceiling, sort_key = rs.rank_state(
        {"ranknow": 0, "rank": [0, 0], "manual_call_mode": "done"}, account_pages=3
    )
    assert value is None, "an unfound keyword was given a position"
    assert state == rs.OUT_OF_RANGE
    assert ceiling == 30, "three pages of ten"


def test_a_failed_check_is_told_apart_from_not_being_found():
    """The distinction the whole module exists for."""
    failed = rs.rank_state({"ranknow": 0, "rank": [0], "manual_call_mode": "fail"})
    unfound = rs.rank_state({"ranknow": 0, "rank": [0], "manual_call_mode": "done"})
    assert failed[1] == rs.NOT_MEASURED
    assert unfound[1] == rs.OUT_OF_RANGE
    assert failed[1] != unfound[1]


def test_a_never_checked_keyword_says_so():
    value, state, ceiling, sort_key = rs.rank_state(
        {"ranknow": 0, "rank": [], "manual_call_mode": "key"}
    )
    assert value is None
    assert state == rs.NEVER_CHECKED


def test_a_failed_first_check_reports_the_failure_not_the_emptiness():
    """A keyword can fail on its very first run and is then both. "We could
    not measure it" is the more useful of the two answers."""
    assert rs.rank_state({"ranknow": 0, "rank": [], "manual_call_mode": "fail"})[1] == rs.NOT_MEASURED


# --- no state ever carries a fabricated number ------------------------------


@pytest.mark.parametrize(
    "row",
    [
        {"ranknow": 0, "rank": [0], "manual_call_mode": "done"},
        {"ranknow": 0, "rank": [0], "manual_call_mode": "fail"},
        {"ranknow": 0, "rank": [], "manual_call_mode": "key"},
    ],
)
def test_no_unranked_state_carries_a_position(row):
    value, state, _, _ = rs.rank_state(row)
    assert state != rs.RANKED
    assert value is None, "state %s handed back a position" % state


def test_the_old_sentinel_is_not_produced_anywhere():
    """101 as a rank is the bug. It must not come back from any state."""
    for mode in ("done", "fail", "key", ""):
        for history in ([], [0], [0, 0]):
            value, _, _, _ = rs.rank_state(
                {"ranknow": 0, "rank": history, "manual_call_mode": mode}
            )
            assert value != 101


# --- the ceiling is the depth actually searched -----------------------------


def test_the_ceiling_follows_the_keyword_own_depth():
    one_page = rs.rank_state({"ranknow": 0, "rank": [0], "serp_pages": 1})
    five_pages = rs.rank_state({"ranknow": 0, "rank": [0], "serp_pages": 5})
    assert one_page[2] == 10
    assert five_pages[2] == 50
    assert one_page[2] != five_pages[2], "two depths must not share one ceiling"


def test_the_account_default_applies_when_the_keyword_has_none():
    assert rs.rank_state({"ranknow": 0, "rank": [0]}, account_pages=2)[2] == 20


def test_an_unusable_depth_falls_back_rather_than_crashing():
    for pages in (None, 0, -1, "", "abc"):
        assert rs.rank_state({"ranknow": 0, "rank": [0], "serp_pages": pages})[2] == 10


def test_the_keyword_overrides_the_account_and_the_account_overrides_the_fallback():
    """Accountusage.serp_depth is 1 on a fresh row, so a caller that forgets to
    pass it would report a 30-result ceiling against a one-page search."""
    # keyword wins
    assert rs.rank_state({"ranknow": 0, "rank": [0], "serp_pages": 2}, account_pages=5)[2] == 20
    # then the account
    assert rs.rank_state({"ranknow": 0, "rank": [0]}, account_pages=5)[2] == 50
    assert rs.rank_state({"ranknow": 0, "rank": [0]}, account_pages=1)[2] == 10
    # an unusable account value falls through to the fallback, not to a guess
    assert rs.rank_state({"ranknow": 0, "rank": [0]}, account_pages="nope")[2] == 10


def test_the_fallback_is_the_smallest_honest_claim():
    """When nothing says otherwise, claim ONE page searched. Claiming three
    would assert two pages nobody paid for."""
    assert rs.rank_state({"ranknow": 0, "rank": [0]})[2] == 10


# --- sorting needs a total order that is not a position ---------------------


def test_unranked_keywords_sort_past_every_real_rank():
    ranked = rs.rank_state({"ranknow": 99, "rank": [99]})[3]
    out_of_range = rs.rank_state({"ranknow": 0, "rank": [0], "manual_call_mode": "done"})[3]
    failed = rs.rank_state({"ranknow": 0, "rank": [0], "manual_call_mode": "fail"})[3]
    never = rs.rank_state({"ranknow": 0, "rank": []})[3]
    assert ranked < out_of_range < failed < never
    assert out_of_range >= rs.SORT_FLOOR


# --- it reads both shapes the serializers hand it ---------------------------


class _Row(object):
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def test_model_instances_and_dicts_agree():
    """Serializers here are handed dicts from .values() AND model instances."""
    as_dict = rs.rank_state({"ranknow": 0, "rank": [0], "manual_call_mode": "fail"})
    as_obj = rs.rank_state(_Row(ranknow=0, rank=[0], manual_call_mode="fail"))
    assert as_dict == as_obj


def test_a_row_missing_the_columns_degrades_safely():
    """Competitor rows have no manual_call_mode at all."""
    value, state, ceiling, _ = rs.rank_state({"ranknow": 0, "rank": [0]}, account_pages=3)
    assert value is None
    assert state == rs.OUT_OF_RANGE
    assert ceiling == 30


def test_apply_writes_the_companion_fields():
    out = {}
    value, state, ceiling, sort_key = rs.apply_rank_state(
        out, {"ranknow": 3, "rank": [3]}, account_pages=3
    )
    assert out["RS"] == rs.RANKED
    assert out["RC"] == 30
    assert out["RSK"] == 3
    assert value == 3


def test_apply_honours_a_prefix_for_the_competitor_pair():
    out = {}
    rs.apply_rank_state(out, {"ranknow": 0, "rank": [0]}, prefix="MR")
    assert out["MRS"] == rs.OUT_OF_RANGE
    assert "RS" not in out, "the prefixed call must not also write the bare keys"


# --- the history chart ------------------------------------------------------
#
# Replacing the 101 sentinel with `null` made a day with no position a GAP,
# which is right for a keyword that ranks on some days. It is not right for a
# keyword that has NEVER ranked: every point becomes null, and ApexCharts
# counts the points, decides the series has data, and skips its noData
# message -- so the tab draws axes, a watermark, and nothing else. 28 of 30
# keywords in the development database are in exactly that state, and the
# owner reported it as "why not showing?".
#
# A blank chart is not a more honest answer than a wrong one. It is no answer.

CHART = ROOT / "app" / "src" / "pages" / "serpRank" / "components" / "kw_history_graph.js"

_LINE_COMMENT = re.compile(r"^\s*//.*$", re.M)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _code(path):
    """Source with comments stripped.

    A bare "string not in source" check fails against correctly-fixed code the
    moment a comment explains what the old value was -- which is exactly what
    the comments in this file do. Assert on what runs.
    """
    source = path.read_text(encoding="utf-8")
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", source))


def test_a_range_with_no_positions_draws_no_series():
    """An empty series is what lets noData speak; a series of nulls silences it."""
    source = CHART.read_text(encoding="utf-8")
    assert "hasPlotted" in source, (
        "the chart no longer distinguishes 'has a position to plot' from "
        "'every reading is a gap'"
    )
    assert "hasPlotted ?" in source, (
        "the series is built unconditionally again. A series of nulls renders "
        "as an empty grid with no explanation."
    )


def test_the_empty_state_states_the_depth_that_produced_it():
    source = CHART.read_text(encoding="utf-8")
    assert "No readings in this range yet" in source, (
        "the never-measured wording is gone"
    )
    assert "on any day in this range" in source, (
        "measured-and-never-ranked reads the same as never-measured again. "
        "They are different facts: one has no data, the other has six days of "
        "it saying the domain was not in the first 30."
    )


def test_the_chart_does_not_hardcode_a_ceiling():
    """">30" was only ever right at the default depth of three pages."""
    source = _code(CHART)
    assert '">30"' not in source, (
        "the tooltip hardcodes a 30-result ceiling again; read RC instead"
    )
    assert "rankCeiling" in source, "the chart no longer reads the real depth"


def test_the_chart_carries_no_sentinel_arithmetic():
    """`val > 100` and `kwrank[0] > 100` were 101-sentinel leftovers that can
    never be true now, so they silently fell through to a null tooltip."""
    source = _code(CHART)
    for dead in ("val > 100", "kwrank[0] > 100"):
        assert dead not in source, (
            "%r is sentinel arithmetic; the position is null when absent" % dead
        )
