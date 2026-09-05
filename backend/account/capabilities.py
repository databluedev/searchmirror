"""What this instance can actually do, and what is missing when it cannot.

Every feature here depends on a credential the operator or the account has to
supply. Before this existed, an unconfigured integration surfaced as an empty
table or a silent no-op, which reads exactly like "you have no data" -- the
user could not tell a missing key from a genuine zero.

Each entry answers three things: is it available, what does it need, and what
stops working without it. The frontend renders the reason; it does not guess.
"""

from django.conf import settings

from account.aikeys import instance_fallback_allowed, stored_key
from shared.keycrypto import decrypt_key


def _cfg(name):
    return bool(getattr(settings, name, "") or "")


# serp_key_state() results. "unreadable" is the one nothing used to report:
# `bool(usage.serp_key)` is true for a stored token whose plaintext can no
# longer be recovered (SERP_KEY_SECRET rotated, or the value was truncated in
# transit), so the account looked configured, every rank run failed on a key the
# engine could not decrypt, and no surface anywhere said so.
SERP_KEY_OK = "ok"
SERP_KEY_MISSING = "missing"
SERP_KEY_UNREADABLE = "unreadable"
SERP_KEY_INSTANCE = "instance"


def serp_key_state(usage):
    """How this account's DataBlue key stands: one of the SERP_KEY_* constants.

    The single answer to "can this account rank?" -- `capabilities()` and
    /refreshstatus both read it so the settings page and the rank page cannot
    disagree about whether a key is usable.
    """
    stored = (getattr(usage, "serp_key", "") or "").strip()
    if stored:
        if not stored.startswith("v1:"):
            # Predates encryption / hand-edited row. Usable as-is, same as the
            # tolerance aikeys.stored_key() applies to the AI columns.
            return SERP_KEY_OK
        try:
            if decrypt_key(stored):
                return SERP_KEY_OK
        except Exception:
            pass
        return SERP_KEY_UNREADABLE
    if _cfg("DATABLUE_API_KEY") and instance_fallback_allowed():
        return SERP_KEY_INSTANCE
    return SERP_KEY_MISSING


def capabilities(usage):
    """Build the capability map for one account.

    `usage` is that account's Accountusage row, or None.
    """
    serp_state = serp_key_state(usage)
    serp_usable = serp_state in (SERP_KEY_OK, SERP_KEY_INSTANCE)

    ai = {slug: bool(stored_key(usage, slug))
      for slug in ("chatgpt", "claude", "perplexity", "gemini")}
    ai_instance = instance_fallback_allowed() and any(
    _cfg(n) for n in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                      "PERPLEXITY_API_KEY", "GEMINI_API_KEY"))

    gsc = _cfg("GSC_CLIENT_ID") and _cfg("GSC_SECRET_ID")
    ga = _cfg("GA_CLIENT_ID") and _cfg("GA_SECRET_ID")
    email = _cfg("EMAIL_HOST") and _cfg("EMAIL_HOST_USER")
    ai_available = any(ai.values()) or ai_instance

    def entry(available, needs, blocks, fix):
        return {"available": available, "needs": needs, "blocks": blocks, "fix": fix}

    if serp_state == SERP_KEY_UNREADABLE:
        rank_tracking = entry(
            False,
            "a readable DataBlue API key",
            "Rank checks fail: the stored key cannot be decrypted, so every request is made without one.",
            "Re-enter your key under Account -> API Key. The stored value was encrypted with a different SERP_KEY_SECRET.",
        )
    else:
        rank_tracking = entry(
            serp_usable,
            "a DataBlue API key",
            "Rank checks do not run, so positions never update.",
            "Add your key under Account -> API Key.",
        )

    return {
        "rank_tracking": rank_tracking,
        "geo_citations": entry(
            ai_available,
            "an AI provider key",
            "Geo Citations cannot ask any model what it says about you.",
            "Add a key under Account -> AI Keys.",
        ),
        "search_console": entry(
            gsc,
            "a Google OAuth client",
            "Search Console figures cannot be connected.",
            "Set GSC_CLIENT_ID and GSC_SECRET_ID on the backend, then VITE_GSC_CLIENT_ID in the web app.",
        ),
        "google_analytics": entry(
            ga,
            "a Google OAuth client",
            "Analytics traffic figures cannot be connected.",
            "Set GA_CLIENT_ID and GA_SECRET_ID on the backend, then VITE_GSC_CLIENT_ID in the web app.",
        ),
        "email": entry(
            email,
            "SMTP credentials",
            "Report delivery and password-reset mail are not sent.",
            "Set EMAIL_HOST and EMAIL_HOST_USER.",
        ),
        "content_planner": entry(
            ai_available,
            "an AI provider key",
            "AI content generation cannot run; plans can still be created and edited by hand.",
            "Add a key under Account -> AI Keys.",
        ),
    }
