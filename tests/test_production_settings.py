"""Production configuration must fail closed instead of using local defaults."""

from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_backend_rejects_documented_local_secret_outside_debug():
    settings = (ROOT / "backend" / "tracker" / "settings.py").read_text(
        encoding="utf-8"
    )

    assert "local-dev-only-not-a-real-secret" in settings
    assert "UNSAFE_SECRET_KEYS" in settings
    assert "raise ImproperlyConfigured" in settings
    assert 'open(searchFile, "r+")' not in settings


def test_engine_debug_and_secret_are_environment_controlled():
    settings = (ROOT / "engine" / "project" / "settings.py").read_text(
        encoding="utf-8"
    )

    assert "DEBUG = True" not in settings
    assert "ENGINE_DEBUG" in settings
    assert "raise ImproperlyConfigured" in settings


def test_instance_key_fallback_is_opt_in():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "ALLOW_INSTANCE_FALLBACK=false" in example
