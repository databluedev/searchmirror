"""One fact, one row -- and the rule that decides it lives in one place.

The defect: `dashboard_overview.py` withheld the `failed_keywords` alert
whenever a run had failed, on the grounds that the run row already said it. The
client then appended the standing count back, because it only suppressed its
own row when it saw the alert the API had deliberately not sent. Every failed
run therefore rendered TWO rows about the same keywords. Both halves were
individually reasonable; the pair was wrong.

Reproduced live before the fix: `/dashboard_overview` for project 4 returned
`run.errc="serp_failed"`, `run.fkw=1`, `alerts=[]` -- and AlertBar drew a
failure row and a standing row for the same single keyword.

These tests pin single ownership rather than the wording, because the wording
is expected to change and the ownership is not. The behavioural check at the
bottom runs against the live stack and observes whatever state it finds; the
three-case matrix was verified by driving the project through each state and
restoring it, which is recorded in the change's verification notes.
"""

import ast
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
OVERVIEW = BACKEND / "serp" / "dashboard_overview.py"
ALERT_BAR = ROOT / "app" / "src" / "pages" / "widget" / "components" / "alert_bar.js"

TIMEOUT = 60


def _read(path):
    return path.read_text(encoding="utf-8")


def _code_only(path):
    """JS source with comments removed.

    These tests assert that certain words do NOT appear. Run against the raw
    file they fail on the comment that explains why the word must not appear --
    which is a documented trap in this repository, and cost a green suite once
    already. Assert on code, explain in prose, keep the two apart.
    """
    source = _read(path)
    out, i, n = [], 0, len(source)
    while i < n:
        two = source[i:i + 2]
        if two == "/*":
            end = source.find("*/", i + 2)
            i = n if end == -1 else end + 2
        elif two == "//":
            end = source.find(chr(10), i)
            i = n if end == -1 else end
        elif source[i] in "\"'`":
            quote, i = source[i], i + 1
            while i < n and source[i] != quote:
                i += 2 if source[i] == "\\" else 1
            i += 1
        else:
            out.append(source[i])
            i += 1
    return "".join(out)


def _function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("no function named %s" % name)


# --- the server owns the decision -------------------------------------------


def test_the_run_failure_is_composed_into_the_alert_list():
    """It used to be sent only as `run`, leaving the client to add a row for
    it and then get the de-duplication wrong."""
    source = ast.get_source_segment(_read(OVERVIEW), _function(ast.parse(_read(OVERVIEW)), "_alerts_block"))
    assert 'run.get("errc")' in source
    assert '"severity": "warn"' in source


def test_the_standing_count_is_withheld_only_when_a_run_row_explains_it():
    source = ast.get_source_segment(_read(OVERVIEW), _function(ast.parse(_read(OVERVIEW)), "_alerts_block"))
    assert 'if run["fkw"] and not (run.get("errc") or run.get("err")):' in source, (
        "the standing count is no longer guarded on the presence of a run row"
    )


def test_the_standing_row_is_not_worded_as_this_run_outcome():
    """`fkw` is sticky between runs, so it can outlive the run that caused it."""
    source = ast.get_source_segment(_read(OVERVIEW), _function(ast.parse(_read(OVERVIEW)), "_alerts_block"))
    standing = source.split('"code": "failed_keywords"', 1)[1].split("alerts.append", 1)[0]
    assert "last check failed" not in standing
    assert "could not be checked" not in standing


def test_the_failure_carries_something_the_user_can_do():
    """An alert the user can only read is a dead statement. It must offer the
    thing that CLEARS it."""
    module = _read(OVERVIEW)
    tree = ast.parse(module)
    builder = ast.get_source_segment(module, _function(tree, "_recheck_action"))
    assert '"kind": "recheck"' in builder
    assert '"keyword_ids"' in builder, "an action that names no keywords cannot be priced"
    # and it is actually attached to both rows that can carry it
    block = ast.get_source_segment(module, _function(tree, "_alerts_block"))
    assert block.count("_recheck_action(") == 2, (
        "the action is attached to %d alert rows, expected the run failure and "
        "the standing count" % block.count("_recheck_action(")
    )


def test_the_cost_is_stated_before_it_is_spent():
    """It bills the account holder's own provider key."""
    module = _read(OVERVIEW)
    builder = ast.get_source_segment(module, _function(ast.parse(module), "_recheck_action"))
    assert '"searches"' in builder
    assert "billed to your own API key" in builder
    assert "_pages_for" in module, "the cost is not derived from each keyword's own depth"


def test_the_failed_keyword_ids_are_looked_up_not_just_counted():
    """Deciding whether the standing count is already explained by the run
    needs the set, not the number."""
    source = _read(OVERVIEW)
    assert 'manual_call_mode="fail"' in source
    assert "failed_ids" in source


# --- the client owns nothing -------------------------------------------------


def test_the_client_adds_no_row_of_its_own():
    source = _code_only(ALERT_BAR)
    for smell in ("run.fkw", "saidStanding", "failureRow", "failed_keywords"):
        assert smell not in source, (
            "alert_bar.js is deciding again (%s) -- that is how the rule split "
            "in two the first time" % smell
        )


def test_the_client_renders_what_it_is_given():
    source = _code_only(ALERT_BAR)
    assert "alerts" in source
    assert "rows.map" in source


def test_the_client_cannot_dismiss_a_true_alert():
    """An alert goes away by ceasing to be true, not by being closed or timed
    out while the condition still holds."""
    source = _code_only(ALERT_BAR)
    for smell in ("setTimeout", "dismiss", "onClose", "useState"):
        assert smell not in source, "alert_bar.js can now hide an alert that is still true (%s)" % smell


# --- and the live payload agrees ---------------------------------------------


def test_no_two_live_alert_rows_describe_the_same_failed_keywords(api, headers):
    """Whatever state the stack is in, the failure must not be stated twice."""
    projects = requests.post(
        api + "/baseauth", json={"userid": headers.get("__uid__", "1")}, headers=headers, timeout=TIMEOUT
    )
    if projects.status_code != 200:
        pytest.skip("no project list available")

    body = projects.json()

    def dig(node, key):
        if isinstance(node, dict):
            if key in node:
                return node[key]
            for value in node.values():
                found = dig(value, key)
                if found is not None:
                    return found
        if isinstance(node, list):
            for value in node:
                found = dig(value, key)
                if found is not None:
                    return found
        return None

    groups = dig(body, "slt") or []
    checked = 0
    for group in groups:
        gid = group.get("GY")
        if gid is None:
            continue
        response = requests.post(
            api + "/dashboard_overview",
            json={"userid": str(dig(body, "id") or "1"), "grpid": str(gid)},
            headers=headers,
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            continue
        payload = response.json()
        alerts = payload.get("alerts") or []
        about_failed = [
            row for row in alerts
            if "could not be checked" in (row.get("text") or "")
            or "no current rank data" in (row.get("text") or "")
        ]
        assert len(about_failed) <= 1, (
            "project %s renders %d rows about the same failed keywords: %s"
            % (gid, len(about_failed), [r.get("text") for r in about_failed])
        )
        checked += 1

    if not checked:
        pytest.skip("no project answered /dashboard_overview")


# --- a run outcome is news, and news is reported once -------------------------


def test_the_run_outcome_is_cleared_once_it_has_been_reported():
    """`refresh_error_code` records what the LAST run did. Reloading the
    dashboard re-runs nothing, so that record -- and the warn banner drawn from
    it -- survived every page load until another run happened. An event was
    being rendered as a standing condition, and it read as a fault the user
    could not clear.

    This is not dismissal, which `test_the_client_cannot_dismiss_a_true_alert`
    forbids and which stays forbidden. The condition the run row reports is
    "there is an unreported run outcome"; reporting it makes that false. The
    durable fact survives in the standing `failed_keywords` row and in the
    keywords table, where each affected keyword reads "Could not be checked".
    """
    source = _read(OVERVIEW)
    assert "mark_run_outcome_reported" in source, (
        "the dashboard no longer clears the run outcome after reporting it, so "
        "the warn banner will persist across every page load again"
    )
    guard = source.split("mark_run_outcome_reported(userid, grpid)", 1)[0]
    assert 'severity") == "warn"' in guard.rsplit("\n\n", 1)[-1], (
        "the clear is not guarded on an alert actually having been produced. "
        "Unguarded, a response that never reached a browser would swallow the "
        "only report of a failed run."
    )


def test_the_machine_code_is_not_rendered_to_the_user():
    """`serp_failed` printed beside the sentence told the reader nothing the
    sentence had not already said, and read as an error dump."""
    source = _code_only(ALERT_BAR)
    assert "dashAlert__code" not in source, (
        "the raw error code is rendered in the alert again"
    )
    assert "row.code" not in source.split("key=", 1)[-1].split("\n", 1)[-1], (
        "row.code is being displayed rather than only keying the row"
    )


def test_the_alert_row_wraps_so_its_action_stays_reachable():
    """The action is the only way to clear the alert and sits behind
    `margin-left: auto`. Without wrapping, a long sentence pushed it past the
    viewport on a narrow window and the alert read as a dead statement."""
    from pathlib import Path

    style = (Path(__file__).parents[1] / "app" / "src" / "pages" / "widget" / "style.scss").read_text(encoding="utf-8")
    block = style.split(".dashAlert {", 1)[1].split("}", 1)[0]
    assert "flex-wrap: wrap" in block, (
        "the alert row no longer wraps, so its re-check control can be pushed "
        "off-screen at narrow widths"
    )
