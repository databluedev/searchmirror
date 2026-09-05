"""What a keyword's rank actually is, kept apart from what it is not.

`ranknow == 0` in the database means three different things and the API used to
render all three as the number **101**:

* the keyword was checked and the domain was not in the pages fetched
* the keyword was checked and the provider returned nothing usable
* the keyword has never been checked at all

Only the first is a measurement. The other two are absences of one, and 101 --
"worse than 100" -- states them as a position the product never observed. It is
not even 100: the default depth is three pages of ten, so a keyword that did not
appear was not seen in the first **30**, and the export already rendered the same
sentinel as ">30" while the history graph plotted it as 101.

This module is the one place that decides which of the four states a keyword is
in. Every serializer asks it rather than writing `or 101` again.

WHAT THE API SENDS, and why each field exists:

    RW   the position, as a number, ONLY when the keyword ranks. `None`
         otherwise -- deliberately not 0 and not 101, so a renderer that was
         never migrated shows nothing rather than confidently showing a
         position that was never measured.
    RS   which of the four states: "ranked", "out_of_range", "not_measured",
         "never_checked".
    RC   the ceiling that was actually searched, e.g. 30 for three pages of
         ten. Only meaningful with "out_of_range", where it is what turns
         "not ranked" into "not in the first 30".
    RSK  a numeric SORT KEY. Sorting and filtering need a total order and
         `None` does not give one. Never display it: it is a large number for
         everything that does not rank, which is exactly the lie RW used to
         tell, confined to a field nothing renders.
"""

RANKED = "ranked"
OUT_OF_RANGE = "out_of_range"
NOT_MEASURED = "not_measured"
NEVER_CHECKED = "never_checked"

# Sorts unranked keywords to the end without pretending to be a position.
SORT_FLOOR = 100000

# Precedence for pages, one direction only, matching serp/keyword.py:
#     keyword.serp_pages  ->  Accountusage.serp_depth  ->  this fallback
#
# The account default matters: Accountusage.serp_depth is 1 on a fresh row, so
# an account that has never chosen a depth searches ONE page. Reporting "not in
# the first 30" for it would be the same class of invention this module exists
# to remove -- a ceiling nothing measured against. Callers must pass
# `account_pages`; the constant below is only for a row that carries neither.
_DEFAULT_PAGES = 1
_RESULTS_PER_PAGE = 10


def _get(obj, name, default=None):
    """Serializers here are handed dicts from .values() AND model instances."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def depth_ceiling(obj, account_pages=None):
    """How many results were actually looked at for this keyword.

    Per-keyword `serp_pages` wins, then the account default, then the engine's
    own fallback. A keyword tracked at one page and one tracked at five have
    different ceilings, and reporting a shared one would be a guess.
    """
    for candidate in (_get(obj, "serp_pages"), account_pages, _DEFAULT_PAGES):
        try:
            pages = int(candidate)
        except (TypeError, ValueError):
            continue
        if pages >= 1:
            return pages * _RESULTS_PER_PAGE
    return _DEFAULT_PAGES * _RESULTS_PER_PAGE


def rank_state(obj, account_pages=None):
    """``(RW, RS, RC, RSK)`` for one keyword.

    Order matters. A failed check is asked about before an empty history,
    because a keyword can fail on its very first run and is then both -- and
    "we could not measure it" is the more useful of the two answers.
    """
    ranknow = _get(obj, "ranknow") or 0
    try:
        ranknow = int(ranknow)
    except (TypeError, ValueError):
        ranknow = 0

    ceiling = depth_ceiling(obj, account_pages)

    if ranknow > 0:
        return ranknow, RANKED, ceiling, ranknow

    mode = str(_get(obj, "manual_call_mode") or "").strip().lower()
    if mode == "fail":
        return None, NOT_MEASURED, ceiling, SORT_FLOOR + 2

    # An empty rank history means no run has ever written a position for this
    # keyword. KeywordCreateSerializer stores `rank=[]`, so this is what a
    # just-added keyword looks like before its first check.
    history = _get(obj, "rank") or []
    if not history:
        return None, NEVER_CHECKED, ceiling, SORT_FLOOR + 3

    return None, OUT_OF_RANGE, ceiling, SORT_FLOOR + 1


def apply_rank_state(superData, obj, account_pages=None, prefix="R"):
    """Write the four fields onto a serializer's output dict.

    `prefix` exists because the widget serializers key the same idea as `Rn`
    and `rnw` rather than `RW`; the state fields ride alongside whatever the
    position is called there.
    """
    value, state, ceiling, sort_key = rank_state(obj, account_pages)
    superData[prefix + "S"] = state
    superData[prefix + "C"] = ceiling
    superData[prefix + "SK"] = sort_key
    return value, state, ceiling, sort_key
