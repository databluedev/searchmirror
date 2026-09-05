"""The application shell must not get more expensive as an account grows.

`/baseauth` is loaded by every screen. It used to issue FOUR queries per
project -- a keyword count, a GroupSetting row, the SAME GroupSetting row again
for one field, and a Refreshmanual row -- so 22 queries produced 1 KB for three
projects and the cost grew linearly with the account.

Under djongo a query costs ~6 ms of pure-Python SQL translation whatever it
selects (profiled: ~44% in sqlparse against ~8% in socket I/O), so query COUNT
is the thing that has to stay bounded. Measured before and after:

    3 projects   22 queries  ->  10 queries
    30 projects  ~213 est.   ->  10 queries   (delta 0, 115 ms)

These are source assertions rather than a live query count, because the suite
runs against a stack over HTTP and cannot read `connection.queries` from
outside the server process. They pin the shape that produces the property: a
bulk load, indexed by project, with the per-project queries gone from the
serializer body. The live flat-count measurement is recorded in the change's
verification notes.
"""

import ast
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
SERIALIZERS = BACKEND / "serp" / "serializers.py"

TIMEOUT = 60


def _source():
    return SERIALIZERS.read_text(encoding="utf-8")


def _function_source(name):
    src = _source()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef,)) and node.name == name:
            return ast.get_source_segment(src, node)
    raise AssertionError("no function named %s" % name)


def _class_method_source(class_name, method_name):
    src = _source()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name == method_name:
                    return ast.get_source_segment(src, sub)
    raise AssertionError("no %s.%s" % (class_name, method_name))


# --- the per-project queries are gone from the serializer body --------------


def test_the_project_serializer_issues_no_query_per_project():
    """This is the N+1 itself. Any `.objects.` here runs once per project."""
    body = _class_method_source("AppGroupSerializer", "to_representation")
    offenders = [
        line.strip()
        for line in body.split("\n")
        if ".objects." in line and not line.strip().startswith("#")
    ]
    # The serializer keeps a per-object fallback ON PURPOSE: serp/keyword.py
    # renders a SINGLE project through it with no bulk context. So the property
    # is not "no queries here" but "no queries on the bulk path" -- every
    # remaining query must sit under an `else:` reached only when bulk is off.
    on_bulk_path = _queries_outside_the_fallback(body)
    assert not on_bulk_path, (
        "AppGroupSerializer.to_representation queries per project again, outside "
        "the non-bulk fallback:\n  " + "\n  ".join(on_bulk_path)
    )
    assert offenders, (
        "the non-bulk fallback is gone; serp/keyword.py renders one project "
        "through this serializer without a bulk context and would break"
    )


def _queries_outside_the_fallback(body):
    """Query lines that would run even when bulk data was supplied."""
    offenders, in_fallback, fallback_indent = [], False, None
    for raw in body.split("\n"):
        line = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if in_fallback and line and indent <= fallback_indent:
            in_fallback = False
        if line == "else:":
            in_fallback, fallback_indent = True, indent
            continue
        if ".objects." in line and not line.startswith("#") and not in_fallback:
            offenders.append(line)
    return offenders


def test_the_group_setting_row_is_read_once_not_twice():
    """It used to be fetched whole and then AGAIN for `w_order` alone -- two
    reads of the identical row, per project."""
    body = _class_method_source("AppGroupSerializer", "to_representation")
    assert body.count("grp_settings") == 1, "the bulk index is consulted more than once"
    assert body.count("GroupSetting.objects") <= 1, (
        "GroupSetting is read %d times; the duplicate read is back"
        % body.count("GroupSetting.objects")
    )
    for field in ("w_order", "overview_switch", "widget_handle"):
        assert "grpsttgIns.%s" % field in body, "%s no longer comes off the one row" % field


def test_the_shell_builds_a_bulk_context():
    body = _class_method_source("AppHomeSerializer", "to_representation")
    assert "project_list_context(" in body, (
        "the shell no longer bulk-loads; every project will query again"
    )


# --- the bulk loaders do one query each -------------------------------------


@pytest.mark.parametrize(
    "name,table",
    [("_group_settings_by_project", "GroupSetting"), ("_refresh_times_by_project", "Refreshmanual")],
)
def test_each_bulk_loader_makes_one_query_for_the_whole_account(name, table):
    src = _function_source(name)
    assert src.count(".objects.") == 1, "%s issues more than one query" % name
    assert "__in=" in src, "%s is not fetching for the whole account at once" % name


def test_the_keyword_count_avoids_the_sql_layer():
    """A GROUP BY through djongo costs more to translate than to run, and
    counting in Python would be O(keywords)."""
    src = _function_source("_keyword_counts_by_project")
    assert "aggregate(" in src
    assert "$group" in src
    assert "_meta.db_table" in src, "the collection name is hardcoded rather than read from the model"


def test_the_keyword_count_falls_back_rather_than_failing():
    """A slow project list beats one that does not load."""
    src = _function_source("_keyword_counts_by_project")
    assert "except Exception" in src
    assert "return None" in src


# --- a missing row still produces the old defaults --------------------------


def test_a_project_with_no_settings_row_keeps_its_defaults():
    """One project with no manualrefresh row once 500'd a whole account.
    The bulk path must default exactly as the per-project `.first()` did."""
    body = _class_method_source("AppGroupSerializer", "to_representation")
    assert "if grpsttgIns else True" in body
    assert "if grpsttgIns else []" in body
    assert "if grpsttgIns else {}" in body


def test_a_project_with_no_refresh_row_falls_back_to_updated_date():
    body = _class_method_source("AppGroupSerializer", "to_representation")
    assert "obj.updated_date" in body


def test_the_bulk_context_is_optional():
    """A serializer used without the context must still work, or every other
    caller breaks by not knowing about it."""
    body = _class_method_source("AppGroupSerializer", "to_representation")
    assert 'self.context.get("_bulk")' in body
    assert "else:" in body


# --- and the endpoint still answers -----------------------------------------


def test_the_shell_still_serves_every_project(api, headers, auth):
    user_id = auth[0]
    response = requests.post(
        api + "/baseauth", json={"userid": user_id}, headers=headers, timeout=TIMEOUT
    )
    assert response.status_code == 200
    body = response.json()

    def dig(node, key):
        if isinstance(node, dict):
            if key in node:
                return node[key]
            for value in node.values():
                found = dig(value, key)
                if found is not None:
                    return found
        return None

    projects = dig(body, "slt")
    assert isinstance(projects, list) and projects, "the shell returned no projects"
    for project in projects:
        for field in ("GY", "NM", "kw_c", "DN", "OV", "W", "w_order", "rf_t"):
            assert field in project, "project %s lost %s" % (project.get("GY"), field)
        assert isinstance(project["kw_c"], int), "keyword count is not a number"
