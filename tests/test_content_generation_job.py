"""Content Planner generation as a queued job, not an awaited provider call.

A 30-60s provider call awaited inside the request held a server worker for its
whole duration, so three people generating at once made the product
unavailable to everyone. These tests pin the queue-and-poll contract that
replaced it: what /generate returns, what the status endpoint reports in each
state, that a restart is reported as interrupted rather than as still running,
and that two requests for one plan cannot bill the account twice.

Source-level, like the rest of this suite where the behaviour is a code
contract rather than an HTTP one -- reaching DONE over HTTP requires a real
provider call, which spends the account holder's money.
"""

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
VIEWS = BACKEND / "contentmanager" / "views.py"
MODELS = BACKEND / "contentmanager" / "models.py"
APPS = BACKEND / "contentmanager" / "apps.py"
URLS = BACKEND / "contentmanager" / "urls.py"
EDITOR = ROOT / "app" / "src" / "pages" / "contentPlanner" / "cedit_editor.js"


def _read(path):
    return path.read_text(encoding="utf-8")


def _function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("no function named %s" % name)


# --- the request no longer waits for the provider ---------------------------


def test_generate_view_does_not_call_the_provider_inline():
    """The whole point. generate_text inside the view body is the old bug."""
    tree = ast.parse(_read(VIEWS))
    view = _function(tree, "generate_ai_content")
    called = {
        n.func.id
        for n in ast.walk(view)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "generate_text" not in called, (
        "generate_ai_content calls the AI provider inside the request again -- "
        "that holds a server worker for 30-60s"
    )


def test_generation_runs_on_a_daemon_thread():
    source = _read(VIEWS)
    assert "threading.Thread(target=_run_generation" in source
    assert "daemon=True" in source, "a non-daemon thread blocks shutdown"


def test_worker_thread_is_the_only_caller_of_the_provider():
    tree = ast.parse(_read(VIEWS))
    worker = _function(tree, "_run_generation")
    called = {
        n.func.id
        for n in ast.walk(worker)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "generate_text" in called


def test_status_endpoint_is_routed():
    assert "generate/status" in _read(URLS)


# --- every state has a distinct, honest answer ------------------------------


def test_model_keeps_generation_state_apart_from_draft_state():
    """track_status is about the saved draft. Overloading it would make
    'the article failed to generate' and 'the draft was never saved' one value."""
    source = _read(MODELS)
    for field in ("gen_status", "gen_message", "gen_claim_date", "gen_content"):
        assert field in source, "missing %s" % field
    assert "track_status" in source


def test_failure_is_recorded_as_failure_with_a_reason():
    source = _read(VIEWS)
    assert 'gen_status="FAIL"' in source
    assert "gen_message=str(exc)" in source


def test_a_dead_worker_thread_cannot_leave_a_plan_running_forever():
    """A bare `except Exception` that swallowed the error would leave the plan
    RUNNING with nothing running, and the cutoff would not notice for minutes."""
    tree = ast.parse(_read(VIEWS))
    worker = _function(tree, "_run_generation")
    handlers = [n for n in ast.walk(worker) if isinstance(n, ast.ExceptHandler)]
    assert handlers, "the worker thread has no failure handling at all"
    bodies = [ast.dump(h) for h in handlers]
    assert all("gen_status" in b for b in bodies), (
        "an exception path leaves the plan without a terminal state"
    )


def test_done_without_an_article_is_not_reported_as_success():
    tree = ast.parse(_read(VIEWS))
    view = _function(tree, "generate_ai_status")
    source = ast.get_source_segment(_read(VIEWS), view)
    assert 'payload["gen_status"] = "FAIL"' in source
    assert "without producing an article" in source


# --- a restart is visible, not a spinner that never stops -------------------


def test_a_stale_claim_is_reported_interrupted():
    source = _read(VIEWS)
    assert "_GEN_STALE_AFTER" in source
    assert "interrupted" in source.lower()
    assert "start it again" in source


def test_a_restart_is_reconciled_at_startup_not_only_by_the_cutoff():
    """The cutoff alone leaves a killed job reading RUNNING for the whole
    window. Start-up reconciliation is what makes a restart visible at once."""
    source = _read(APPS)
    assert "def ready" in source
    assert 'gen_status__in=("QUEUED", "RUNNING")' in source
    assert 'gen_status="FAIL"' in source


def test_startup_reconciliation_runs_once_per_container_boot():
    """gunicorn forks several workers and all of them call ready(). Without the
    marker, a worker respawned later would clear a sibling's live job."""
    source = _read(APPS)
    assert "O_EXCL" in source, "the marker check is not atomic between workers"
    assert "/proc/1" in source, "the marker is not keyed on container boot"


# --- one request, one bill --------------------------------------------------


def test_the_plan_is_claimed_before_the_thread_starts():
    source = _read(VIEWS)
    claim = source.index('gen_status="QUEUED"')
    spawn = source.index("threading.Thread(target=_run_generation")
    assert claim < spawn, "the thread starts before the claim, so two requests can both spend"


def test_a_second_request_for_a_live_job_does_not_spend_again():
    tree = ast.parse(_read(VIEWS))
    view = _function(tree, "generate_ai_content")
    source = ast.get_source_segment(_read(VIEWS), view)
    assert "if not claimed:" in source
    after = source.split("if not claimed:", 1)[1].split("threading.Thread")[0]
    assert "already running" in after


# --- the browser polls, and stops -------------------------------------------


def test_editor_polls_instead_of_awaiting():
    source = _read(EDITOR)
    assert "/contentmanager/generate/status" in source
    assert "GEN_MAX_POLLS" in source, "an uncapped poller spins forever"
    assert "genAbortRef" in source, "the in-flight request is never aborted"
    assert "clearInterval(genPollRef.current)" in source


def test_editor_does_not_read_the_article_off_the_generate_response():
    """/generate no longer carries it; reading it there would silently do nothing."""
    source = _read(EDITOR)
    handler = source.split("const handleGenerateAIContent", 1)[1].split("return (", 1)[0]
    assert "pollGeneration()" in handler
    assert "res.data.content" not in handler, (
        "the editor still expects the article on the queue response"
    )


def test_generate_button_cannot_be_retriggered_while_running():
    source = _read(EDITOR)
    assert "disabled={generatingAI" in source
