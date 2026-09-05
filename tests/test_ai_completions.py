"""Shared BYOK completion routing used by every AI-assisted feature."""

import ast
import logging
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
for source_root in (ROOT, BACKEND):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))


def test_generate_text_uses_first_configured_account_provider(monkeypatch):
    from account import completions

    calls = []
    monkeypatch.setattr(
        completions,
        "resolve_key",
        lambda user_id, provider: "account-key" if provider == "claude" else "",
    )
    monkeypatch.setattr(
        completions,
        "resolve_model",
        lambda user_id, provider: "account-model",
    )
    monkeypatch.setitem(
        completions._COMPLETERS,
        "claude",
        lambda key, model, system, user, max_tokens, temperature: calls.append(
            (key, model, system, user, max_tokens, temperature)
        ) or "generated article",
    )

    text = completions.generate_text(7, "system", "user", max_tokens=900)

    assert text == "generated article"
    assert calls == [("account-key", "account-model", "system", "user", 900, 0.7)]


def test_generate_text_reports_missing_account_key(monkeypatch):
    from account import completions

    monkeypatch.setattr(completions, "resolve_key", lambda user_id, provider: "")

    with pytest.raises(completions.NoAIProviderConfigured):
        completions.generate_text(7, "system", "user")


def test_geo_prompt_suggestions_preserve_safe_provider_failure(monkeypatch):
    from account import completions

    message = (
        "Gemini quota or rate limit was reached. Check the provider plan or "
        "try again later."
    )

    def fail_completion(*args, **kwargs):
        raise completions.AICompletionFailed(message)

    monkeypatch.setattr(completions, "generate_text", fail_completion)

    source = (BACKEND / "llmtracker" / "views.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    helper = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_one_shot_completion"
    )
    namespace = {
        "generate_text": completions.generate_text,
        "logger": logging.getLogger(__name__),
    }
    exec(compile(ast.Module(body=[helper], type_ignores=[]), "views.py", "exec"), namespace)

    with pytest.raises(completions.AICompletionFailed, match="^Gemini quota"):
        namespace["_one_shot_completion"](7, "system", "user")


@pytest.mark.parametrize(
    ("provider", "provider_error", "expected_message"),
    [
        (
            "gemini",
            "429 Resource exhausted for api key secret-gemini-key",
            "Gemini quota or rate limit was reached. Check the provider plan or try again later.",
        ),
        (
            "chatgpt",
            "401 invalid_api_key secret-openai-key",
            "ChatGPT rejected the API key. Update it under Settings -> AI Keys.",
        ),
        (
            "claude",
            "Request timed out while using secret-claude-key",
            "Claude timed out. Try again or choose another configured provider.",
        ),
        (
            "perplexity",
            "404 model_not_found secret-perplexity-key",
            "Perplexity model is unavailable. Check the model under Settings -> AI Keys.",
        ),
    ],
)
def test_generate_text_returns_safe_actionable_provider_failures(
    monkeypatch, provider, provider_error, expected_message
):
    from account import completions

    monkeypatch.setattr(
        completions,
        "resolve_key",
        lambda user_id, current_provider: "configured-key"
        if current_provider == provider
        else "",
    )
    monkeypatch.setattr(completions, "resolve_model", lambda user_id, provider: "model")

    def fail_completion(*args, **kwargs):
        raise RuntimeError(provider_error)

    monkeypatch.setitem(completions._COMPLETERS, provider, fail_completion)

    with pytest.raises(completions.AICompletionFailed) as raised:
        completions.generate_text(7, "system", "user")

    assert str(raised.value) == expected_message
    assert "secret-" not in str(raised.value)


def test_content_planner_uses_shared_byok_completion_path():
    source = (BACKEND / "contentmanager" / "views.py").read_text(encoding="utf-8")

    assert "account.completions" in source
    assert "generate_text(" in source
    assert "huggingface" not in source.lower()
    assert "HUGGING_FACE_API" not in source


def test_content_generation_surfaces_the_safe_provider_failure():
    """A provider failure reaches the user with its real cause.

    The generation call moved off the request onto a worker thread, so this no
    longer happens in an `except` beside a `return`: the thread records the
    reason on the plan and the status endpoint hands it back. The requirement
    is unchanged -- the user must be told what actually went wrong, never
    "Something went wrong" -- so this asserts that, not the old shape.
    """
    backend_source = (BACKEND / "contentmanager" / "views.py").read_text(
        encoding="utf-8"
    )
    frontend_source = (
        ROOT / "app" / "src" / "pages" / "contentPlanner" / "cedit_editor.js"
    ).read_text(encoding="utf-8")

    assert "AICompletionFailed" in backend_source
    assert "NoAIProviderConfigured" in backend_source
    # The provider's own message is what gets stored, and what is handed back.
    assert "gen_message=str(exc)" in backend_source
    assert 'payload = {"gen_status"' in backend_source
    assert '"message": plan.gen_message or ""' in backend_source

    assert "error.response?.data?.message" in frontend_source
    # The poller renders the stored reason rather than a generic string.
    assert "res.data.message" in frontend_source
    assert 'console.error("AI Generation Error:", error)' not in frontend_source


def test_generated_article_html_drops_executable_markup():
    from contentmanager.sanitizer import sanitize_article_html

    result = sanitize_article_html(
        "```html<h1 onclick='steal()'>Title</h1><script>steal()</script>"
        "<p>Safe <a href='https://example.com'>link</a></p>```"
    )

    assert result == "<h1>Title</h1><p>Safe link</p>"
