"""Per-account AI provider keys.

The four columns (`chatgpt_api_key`, `claude_api_key`, `perplexity_api_key`,
`gemini_api_key`) were declared on Accountusage, in the migration and on the
engine model -- and read by nothing. Geo Citations billed the operator's
instance key for every account, the same way ranking did before BYOK was
wired. This module is the read path that was missing.

Keys are stored with `shared.keycrypto`, the same envelope as `serp_key`, so
one rotation of SERP_KEY_SECRET governs every stored credential.
"""

import os

from shared.keycrypto import decrypt_key, encrypt_key


# provider slug -> Accountusage field holding that provider's key
PROVIDERS = {
    "chatgpt": "chatgpt_api_key",
    "claude": "claude_api_key",
    "perplexity": "perplexity_api_key",
    "gemini": "gemini_api_key",
}

# provider slug -> Accountusage field holding that provider's model override.
# Blank means "use the instance default" (the provider's *_MODEL env var).
PROVIDER_MODELS = {
    "chatgpt": "chatgpt_model",
    "claude": "claude_model",
    "perplexity": "perplexity_model",
    "gemini": "gemini_model",
}

# Suggested models per provider for the settings dropdown. The first entry is
# the current instance default; the account may also type a custom id. Kept
# short and current on purpose -- an unknown id just errors at call time and is
# recorded on the model's FAIL row, so this is guidance, not a hard allow-list.
MODEL_OPTIONS = {
    "chatgpt": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
    "claude": ["claude-sonnet-5", "claude-haiku-4-5-20251001"],
    "perplexity": ["sonar", "sonar-pro"],
    "gemini": ["gemini-3.6-flash", "gemini-2.5-flash"],
}

# provider slug -> Django settings attribute used when the account has no key
# of its own AND the fallback is allowed.
_INSTANCE_SETTING = {
    "chatgpt": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

_INSTANCE_MODEL_ENV = {
    "chatgpt": "OPENAI_MODEL",
    "claude": "ANTHROPIC_MODEL",
    "perplexity": "PERPLEXITY_MODEL",
    "gemini": "GEMINI_MODEL",
}


def instance_fallback_allowed():
    """Whether a missing per-account key may spend the instance-wide key.

    Same switch the engine reads for SERP. A single-operator self-host runs
    everything on one key; a hosted instance sets it false so an account with
    no key gets no analysis rather than quietly spending the operator's.
    """
    return str(os.environ.get("ALLOW_INSTANCE_FALLBACK", "false")).lower() not in ("0", "false", "no")


def stored_key(usage, provider):
    """Decrypt one provider's key off an Accountusage row. "" when unset.

    Tolerates a plaintext value: these columns predate encryption and were
    never written, but a hand-edited row should not raise.
    """
    field = PROVIDERS.get(provider)
    if not usage or not field:
        return ""
    raw = getattr(usage, field, "") or ""
    if not raw:
        return ""
    if not raw.startswith("v1:"):
        return raw
    try:
        return decrypt_key(raw) or ""
    except Exception:
        # Unreadable token (rotated secret). Treat as absent, never as an error
        # that would abort a scheduled run.
        return ""


def store_key(usage, provider, plain):
    """Encrypt and set one provider's key on the row. Does not save()."""
    field = PROVIDERS.get(provider)
    if not field:
        raise ValueError("unknown provider %r" % provider)
    setattr(usage, field, encrypt_key(plain) if plain else "")
    return field


def stored_model(usage, provider):
    """The account's chosen model for a provider, "" when using the default."""
    field = PROVIDER_MODELS.get(provider)
    if not usage or not field:
        return ""
    return (getattr(usage, field, "") or "").strip()


def store_model(usage, provider, model):
    """Set one provider's model override on the row. Does not save()."""
    field = PROVIDER_MODELS.get(provider)
    if not field:
        raise ValueError("unknown provider %r" % provider)
    setattr(usage, field, (model or "").strip())
    return field


def resolve_key(user_id, provider):
    """The key a call for this account should bill against, or "".

    Account key first; the instance key only if the fallback is allowed.
    """
    from django.conf import settings
    from serp.models import Accountusage

    key = ""
    if user_id:
        try:
            usage = Accountusage.objects.filter(fb_user_id=int(user_id)).first()
        except Exception:
            usage = None
        key = stored_key(usage, provider)
    if key:
        return key
    if not instance_fallback_allowed():
        return ""
    return getattr(settings, _INSTANCE_SETTING.get(provider, ""), "") or ""


def resolve_model(user_id, provider):
    """Resolve an account model override, then the instance/default model."""
    from serp.models import Accountusage

    usage = None
    if user_id:
        try:
            usage = Accountusage.objects.filter(fb_user_id=int(user_id)).first()
        except Exception:
            usage = None
    model = stored_model(usage, provider)
    if model:
        return model
    default = (MODEL_OPTIONS.get(provider) or [""])[0]
    return os.environ.get(_INSTANCE_MODEL_ENV.get(provider, ""), default) or default
