"""Search visibility scoring shared by the ranking engine and dashboard API."""

from collections.abc import Iterable, Mapping, Sequence
from math import isfinite
from typing import Any


BUCKET_WEIGHTS = {
    "eq__first": 1.0,
    "eq__second": 0.75,
    "eq__third": 0.5,
    "gte__four__lte__ten": 0.2,
    "gt__ten__lte__limit": 0.1,
    "gt__limit": 0.0,
}


def classify_activity_level(value: Any) -> str:
    """Describe a ranking-change percentage without inventing activity.

    Activity values are percentages and therefore valid only from -100 to
    100. A zero means the rankings were stable, not that performance was
    moderate.
    """
    try:
        activity = float(value)
    except (TypeError, ValueError):
        return ""

    if not isfinite(activity) or activity < -100 or activity > 100:
        return ""
    if activity < -30:
        return "bad"
    if activity < 0:
        return "low"
    if activity == 0:
        return "stable"
    if activity <= 30:
        return "good"
    return "excellent"


def _rank_weight(rank: Any, rank_limit: int = 100) -> float:
    """Return the visibility weight for one observed organic rank."""
    try:
        position = int(rank or 0)
    except (TypeError, ValueError):
        return 0.0

    if position == 1:
        return 1.0
    if position == 2:
        return 0.75
    if position == 3:
        return 0.5
    if 4 <= position <= 10:
        return 0.2
    if 10 < position <= rank_limit:
        return 0.1
    return 0.0


def calculate_visibility_score(
    ranks: Iterable[Any], rank_limit: int = 100
) -> float:
    """Calculate a 0-100 visibility score across all tracked keywords.

    Unranked keywords contribute zero. They remain in the denominator so the
    score represents coverage without erasing visibility already earned by
    ranked keywords.
    """
    positions = list(ranks)
    if not positions:
        return 0.0

    weighted_total = sum(_rank_weight(rank, rank_limit) for rank in positions)
    return round((weighted_total / len(positions)) * 100, 2)


def calculate_visibility_breakdown(
    ranks: Iterable[Any], rank_limit: int = 100
) -> dict[str, int]:
    """Return the plain-language counts shown beside the visibility score."""
    positions = []
    for rank in ranks:
        try:
            positions.append(int(rank or 0))
        except (TypeError, ValueError):
            positions.append(0)

    ranked = [position for position in positions if 0 < position <= rank_limit]
    return {
        "total_keywords": len(positions),
        "ranked_keywords": len(ranked),
        "first_position": sum(position == 1 for position in ranked),
        "top_ten": sum(position <= 10 for position in ranked),
        "unranked_keywords": len(positions) - len(ranked),
    }


def calculate_visibility_score_from_buckets(
    score_per_day: Mapping[str, Any], total_keywords: int
) -> float:
    """Calculate the same score from the engine's rank bucket counts."""
    if total_keywords <= 0:
        return 0.0

    weighted_total = sum(
        float(score_per_day.get(bucket, 0) or 0) * weight
        for bucket, weight in BUCKET_WEIGHTS.items()
    )
    return round((weighted_total / float(total_keywords)) * 100, 2)


def calculate_visibility_history(
    keyword_rank_histories: Iterable[Sequence[Any]],
    rank_limit: int = 100,
) -> list[float]:
    """Recalculate current-first score history from keyword rank snapshots."""
    histories = [list(history or []) for history in keyword_rank_histories]
    if not histories:
        return []

    history_length = max((len(history) for history in histories), default=0)
    return [
        calculate_visibility_score(
            [history[index] for history in histories if index < len(history)],
            rank_limit,
        )
        for index in range(history_length)
    ]
