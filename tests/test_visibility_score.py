"""Visibility score rules shared by the API and ranking engine."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCORING_MODULE = ROOT / "shared" / "scoring.py"


def _load_scoring():
    assert SCORING_MODULE.exists(), "shared/scoring.py must be the single score source"
    spec = importlib.util.spec_from_file_location("shared_scoring", SCORING_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unranked_keywords_do_not_erase_real_search_visibility():
    scoring = _load_scoring()

    # One #1 ranking and one #5 ranking among 30 tracked keywords.
    assert scoring.calculate_visibility_score([1, 5] + [0] * 28) == 4.0
    assert scoring.calculate_visibility_score([0, None, 101]) == 0.0
    assert scoring.calculate_visibility_breakdown([1, 5] + [0] * 28) == {
        "total_keywords": 30,
        "ranked_keywords": 2,
        "first_position": 1,
        "top_ten": 2,
        "unranked_keywords": 28,
    }


def test_visibility_history_is_recalculated_from_keyword_rank_snapshots():
    scoring = _load_scoring()

    # Keyword rank histories are stored current day first.
    histories = [[1, 2], [5, 0], [0, 0]]
    assert scoring.calculate_visibility_history(histories) == [40.0, 25.0]

    # A keyword added later must not dilute snapshots from before it existed.
    assert scoring.calculate_visibility_history([[1, 2], [5]]) == [60.0, 75.0]


def test_activity_level_describes_zero_change_as_stable():
    scoring = _load_scoring()

    assert scoring.classify_activity_level(-31) == "bad"
    assert scoring.classify_activity_level(-1) == "low"
    assert scoring.classify_activity_level(0) == "stable"
    assert scoring.classify_activity_level(1) == "good"
    assert scoring.classify_activity_level(31) == "excellent"
