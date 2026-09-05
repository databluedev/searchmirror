"""Keys belong to the account, are stored encrypted, and are never echoed back.

Tracker is bring-your-own-key: a rank check is billed to the operator's own
DataBlue key and Geo Citations asks each AI provider on the account's own key.
The columns existed long before anything read them, so these assert the wiring,
not the schema.
"""

import requests

from conftest import API, TIMEOUT

PROVIDERS = ["chatgpt", "claude", "perplexity", "gemini"]


def test_serp_key_is_masked_never_raw(headers):
    r = requests.get(API + "/api/account/serp-key/", headers=headers, timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    if body.get("has_key") != "true":
        return
    key = body["serp_key"]
    assert "…" in key or "..." in key, "serp_key came back unmasked: %r" % key


def test_serp_balance_costs_nothing_and_reports_a_plan(headers):
    """The balance is read from /v1/usage/summary, which the provider
    documents as not charged. Validation used to run a real SERP query and
    billed a credit on every save."""
    r = requests.get(API + "/api/account/serp-key/", headers=headers, timeout=TIMEOUT)
    body = r.json()
    if body.get("has_key") != "true":
        return
    balance = body.get("balance")
    if balance is None:
        return          # provider unreachable; the page renders "Unavailable"
    assert "unlimited" in balance
    assert "plan" in balance


def test_every_ai_provider_is_offered(headers):
    r = requests.get(API + "/api/account/ai-keys/", headers=headers, timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]
    offered = r.json().get("providers", {})
    for slug in PROVIDERS:
        assert slug in offered, "%s is not offered; Geo Citations queries all four" % slug


def test_no_account_is_locked_out(headers, auth):
    """There is nothing to sell, so no account may report a dead subscription.

    userPaymode() used to return "dead" unless a paid subscription row said
    otherwise, and 35 places in the frontend refuse to add a project, add a
    keyword, search or export on that value.
    """
    user_id, _ = auth
    r = requests.post(API + "/baseauth", json={"userid": user_id},
                      headers=headers, timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]

    def dig(node, key):
        if isinstance(node, dict):
            if key in node:
                return node[key]
            for v in node.values():
                found = dig(v, key)
                if found is not None:
                    return found
        return None

    assert dig(r.json(), "sb_s") not in ("dead", "cancelled", "expire")
