"""The keyword page must get everything it renders, on the path users take.

`/keyauth` has two branches, chosen by the `type` field:

    type=full / all   a direct URL -- KeywordPageSerializer, the whole record
    type=half         ARRIVING FROM THE KEYWORDS TABLE -- a partial dict, and
                      the page merges it with the table row it navigated from

`half` is the common path: `keywordOverview/index.js` sends it whenever
`location.state.kwdata` exists, which is every time somebody clicks a keyword.

That made the table's payload load-bearing for a page it does not draw. When
the keywords table was trimmed to send only what the table renders -- a glyph's
worth of `ai_overview`, no `blocks`, no `raw` answer text -- the detail panel
lost the AI Overview's answer and all seven feature rows, while still showing
the "NOT CITED" chip and the cited-source list. It looked like a rendering bug
and was a payload one, two changes away.

So: anything the panel reads must come from the `half` branch itself, not from
whatever the table happened to include.
"""

import ast
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
KEYWORD_VIEW = BACKEND / "serp" / "keyword.py"
SERIALIZERS = BACKEND / "serp" / "serializers.py"
PANEL = ROOT / "app" / "src" / "pages" / "keywordOverview" / "components" / "serp_features.js"
PAGE = ROOT / "app" / "src" / "pages" / "keywordOverview" / "index.js"

TIMEOUT = 60


def _half_branch():
    """The body of the `apitype == "half"` branch in keyload."""
    source = KEYWORD_VIEW.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "keyload":
            for sub in ast.walk(node):
                if isinstance(sub, ast.If):
                    segment = ast.get_source_segment(source, sub) or ""
                    if 'apitype == "half"' in segment.split("\n")[0]:
                        return segment
    raise AssertionError("could not find the half branch in keyload")


def test_the_page_really_does_use_the_half_path():
    """If this stops being true the rest of this file is guarding nothing."""
    page = PAGE.read_text(encoding="utf-8")
    assert '"half"' in page and '"full"' in page, (
        "keywordOverview/index.js no longer chooses between half and full"
    )


def test_the_half_branch_publishes_the_serp_feature_record():
    """The regression itself: without this the panel renders a chip and a
    source list with no answer and no feature rows."""
    branch = _half_branch()
    assert 'serializer["sf"]' in branch, (
        'the "half" branch does not publish `sf`. Arriving from the keywords '
        "table, the page has only the trimmed row the table sent -- no blocks "
        "and no raw answer text."
    )
    assert 'serializer["sfm"]' in branch, (
        '`sfm` is what tells "measured and empty" from "never measured"'
    )


def test_the_half_branch_publishes_the_keyword_configuration():
    """Same class of bug, fixed earlier: a config only a direct URL could show."""
    assert 'serializer["cfg"]' in _half_branch()


def test_the_table_payload_stays_trimmed():
    """The fix is to publish from the half branch, NOT to put the whole record
    back in the list -- it was 87% of that response."""
    source = SERIALIZERS.read_text(encoding="utf-8")
    assert "_table_features(" in source, (
        "the keywords table is sending the untrimmed feature record again"
    )
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_table_features":
            body = ast.get_source_segment(source, node) or ""
            assert '"blocks"' not in body.split('"""')[-1], (
                "the table projection carries per-block detail again"
            )
            return
    raise AssertionError("_table_features is gone")


def test_the_panel_reads_the_fields_the_half_branch_must_supply():
    """Keeps the two sides honest: if the panel starts reading something new,
    this fails until the half branch supplies it too."""
    panel = PANEL.read_text(encoding="utf-8")
    for field in ("ai_overview", "raw", "sources", "blocks", "mode", "target"):
        assert field in panel, "the panel no longer reads %s; update this test" % field


# --- and on the live stack, over the path a user actually takes -------------


def _dig(node, key):
    if isinstance(node, dict):
        if key in node and isinstance(node[key], dict):
            return node[key]
        for value in node.values():
            found = _dig(value, key)
            if found is not None:
                return found
    if isinstance(node, list):
        for value in node:
            found = _dig(value, key)
            if found is not None:
                return found
    return None


def test_half_delivers_the_answer_and_every_feature_row(api, headers, auth):
    """Clicking a keyword must produce the same panel a direct URL does."""
    user_id = auth[0]
    projects = requests.post(api + "/baseauth", json={"userid": user_id},
                             headers=headers, timeout=TIMEOUT)
    if projects.status_code != 200:
        pytest.skip("no project list")
    slt = _dig(projects.json(), "data")
    groups = (slt or {}).get("slt") or []
    if not groups:
        pytest.skip("no projects")

    checked = 0
    for group in groups:
        gid = group.get("GY")
        rows = requests.post(
            api + "/dashservice",
            json={"userid": user_id, "grpid": str(gid), "field": "ranknow",
                  "sort": "asc", "limit": 30},
            headers=headers, timeout=TIMEOUT,
        )
        if rows.status_code != 200:
            continue
        for row in (rows.json().get("results") or [])[:4]:
            half = requests.post(
                api + "/keyauth",
                json={"userid": user_id, "grpid": str(gid),
                      "kwid": str(row["key"]), "type": "half"},
                headers=headers, timeout=TIMEOUT,
            )
            if half.status_code != 200:
                continue
            sf = _dig(half.json(), "sf")
            assert sf is not None, (
                "keyword %s: the half path delivered no feature record, so the "
                "panel would render whatever the table happened to send"
                % row["key"]
            )
            ai = sf.get("ai_overview") or {}
            if ai.get("state") == "present":
                answer = ((ai.get("raw") or {}).get("content")) or ""
                assert answer.strip(), (
                    "keyword %s shows an AI Overview with no answer text -- the "
                    "exact symptom of the trimmed payload" % row["key"]
                )
            checked += 1

    if not checked:
        pytest.skip("no keyword answered the half path")


# --- the same class of bug, third field ------------------------------------
#
# `sf` and `cfg` were fixed above. `RW`/`RS`/`RC` were the third: the overview
# stat and the history chart both word an out-of-range result from `RC` ("not
# in the first 30"), and the half branch never sent it. It worked only because
# `keywordOverview/index.js` does `setKwdata({...olddata, ...res.data})`, so
# the TABLE ROW's copy survived the merge. That is an accident of merge order,
# not a contract, and it breaks the moment the table trims one more field.


def test_the_half_branch_publishes_the_rank_state():
    branch = _half_branch()
    assert "apply_rank_state(" in branch, (
        "the half branch does not publish the rank state. RC is what turns a "
        "missing position into 'not in the first 30'; without it the keyword "
        "page depends on the table row it navigated from."
    )
    assert 'serializer["RW"]' in branch, (
        "apply_rank_state writes RS/RC/RSK and RETURNS the position -- RW is "
        "the caller's to assign. Calling it bare publishes a state with no "
        'position, so a ranked keyword arrives as RS="ranked" with RW=None.'
    )


def test_half_agrees_with_the_table_row_about_rank(api, headers, auth):
    """Two paths, one keyword, one answer."""
    user_id = auth[0]
    projects = requests.post(api + "/baseauth", json={"userid": user_id},
                             headers=headers, timeout=TIMEOUT)
    if projects.status_code != 200:
        pytest.skip("no project list")
    groups = ((_dig(projects.json(), "data") or {}).get("slt")) or []
    if not groups:
        pytest.skip("no projects")

    checked = 0
    for group in groups:
        gid = group.get("GY")
        rows = requests.post(
            api + "/dashservice",
            json={"userid": user_id, "grpid": str(gid), "field": "ranknow",
                  "sort": "asc", "limit": 30},
            headers=headers, timeout=TIMEOUT,
        )
        if rows.status_code != 200:
            continue
        for row in (rows.json().get("results") or [])[:6]:
            half = requests.post(
                api + "/keyauth",
                json={"userid": user_id, "grpid": str(gid),
                      "kwid": str(row["key"]), "type": "half"},
                headers=headers, timeout=TIMEOUT,
            )
            if half.status_code != 200:
                continue
            data = half.json().get("data") or {}
            for field in ("RW", "RS", "RC"):
                assert data.get(field) == row.get(field), (
                    "keyword %s: the table says %s=%r and the half path says "
                    "%r. The keyword page merges the two, so they must agree."
                    % (row["key"], field, row.get(field), data.get(field))
                )
            assert not (data.get("RS") == "ranked" and not data.get("RW")), (
                'keyword %s arrives as RS="ranked" with no position'
                % row["key"]
            )
            checked += 1

    if not checked:
        pytest.skip("no keyword answered the half path")
