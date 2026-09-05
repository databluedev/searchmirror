"""One BYOK text-completion path shared by all AI-assisted features."""

from account.aikeys import resolve_key, resolve_model


PROVIDER_ORDER = ("chatgpt", "claude", "perplexity", "gemini")

PROVIDER_NAMES = {
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "perplexity": "Perplexity",
    "gemini": "Gemini",
}


class NoAIProviderConfigured(RuntimeError):
    pass


class AICompletionFailed(RuntimeError):
    pass


def describe_provider_failure(provider, error):
    """Return an actionable provider error without exposing raw API details."""
    name = PROVIDER_NAMES.get(provider, provider.title())
    detail = str(error).lower()

    if any(marker in detail for marker in ("429", "quota", "rate limit", "resource exhausted")):
        return (
            f"{name} quota or rate limit was reached. "
            "Check the provider plan or try again later."
        )
    if any(
        marker in detail
        for marker in ("401", "403", "invalid_api_key", "authentication", "unauthorized")
    ):
        return f"{name} rejected the API key. Update it under Settings -> AI Keys."
    if any(marker in detail for marker in ("timeout", "timed out", "deadline exceeded")):
        return f"{name} timed out. Try again or choose another configured provider."
    if any(marker in detail for marker in ("model_not_found", "model not found", "unknown model")):
        return f"{name} model is unavailable. Check the model under Settings -> AI Keys."
    return (
        f"{name} failed. Check its key and model under Settings -> AI Keys, "
        "or try again later."
    )


def _openai_completion(key, model, system, user, max_tokens, temperature):
    import openai

    client = openai.OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _claude_completion(key, model, system, user, max_tokens, temperature):
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=model,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(getattr(block, "text", "") for block in response.content)


def _perplexity_completion(key, model, system, user, max_tokens, temperature):
    import openai

    client = openai.OpenAI(api_key=key, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _gemini_completion(key, model, system, user, max_tokens, temperature):
    import google.generativeai as genai

    genai.configure(api_key=key)
    client = genai.GenerativeModel(
        model,
        system_instruction=system,
        generation_config={
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        },
    )
    response = client.generate_content(user)
    return getattr(response, "text", "") or ""


_COMPLETERS = {
    "chatgpt": _openai_completion,
    "claude": _claude_completion,
    "perplexity": _perplexity_completion,
    "gemini": _gemini_completion,
}


def generate_text(user_id, system, user, max_tokens=1024, temperature=0.7):
    """Generate text with the account's first working configured provider.

    Each provider uses the account key and model override resolved by
    ``account.aikeys``. A provider error falls through to the next configured
    provider so one temporary outage does not disable every AI-assisted tool.
    """
    configured = False
    failures = []
    for provider in PROVIDER_ORDER:
        key = resolve_key(user_id, provider)
        if not key:
            continue
        configured = True
        model = resolve_model(user_id, provider)
        try:
            text = _COMPLETERS[provider](
                key, model, system, user, max_tokens, temperature
            ).strip()
            if text:
                return text
            failures.append(
                describe_provider_failure(provider, "provider returned no text")
            )
        except Exception as exc:
            failures.append(describe_provider_failure(provider, exc))

    if not configured:
        raise NoAIProviderConfigured(
            "No AI provider key configured. Add one under Settings -> AI Keys."
        )
    raise AICompletionFailed("; ".join(failures) or "AI generation failed")
