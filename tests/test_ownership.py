"""A caller may only act for its own account.

Almost every view here identifies the account from a `userid` in the request
body rather than from `request.user`. 56 of them never validated it, and a
second account's token reading user 1's content plans was demonstrated before
UserIdOwnershipMiddleware existed.
"""

import requests

from conftest import API, TIMEOUT


def test_foreign_userid_is_refused(headers, auth):
    """Naming someone else's account id must be refused, not served."""
    user_id, _ = auth
    other = str(int(user_id) + 9999)

    r = requests.post(
        API + "/contentmanager/list",
        json={"userid": other},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert r.status_code == 403, (
        "acting for account %s with account %s's token returned %s"
        % (other, user_id, r.status_code)
    )
    assert "Not authorised" in r.text


def test_own_userid_is_served(headers, auth):
    user_id, _ = auth
    r = requests.post(API + "/contentmanager/list", json={"userid": user_id, "grpid": "1"},
                      headers=headers, timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("status") == "true", r.text[:500]


def test_numeric_identifiers_are_normalized_before_legacy_views(headers, auth):
    """Modern JSON clients may send database ids as numbers, not strings."""
    user_id, _ = auth
    r = requests.post(
        API + "/contentmanager/list",
        json={"userid": int(user_id), "grpid": 1},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("status") == "true", r.text[:500]


def test_foreign_userid_refused_on_query_string(headers, auth):
    """The middleware reads the query string too, not only a JSON body."""
    user_id, _ = auth
    other = str(int(user_id) + 9999)
    r = requests.get(API + "/my_view/", params={"userid": other},
                     headers=headers, timeout=TIMEOUT)
    assert r.status_code == 403


# The guard used to read a JSON body and nothing else. DRF's default parsers
# also accept form-urlencoded and multipart, so `request.data["userid"]` was
# populated for those while the middleware saw nothing to check -- the same
# cross-account request was refused as JSON and served as a form. These assert
# the refusal under every content type DRF will parse.

def _auth_only(headers):
    """The Authorization header without the JSON Content-Type."""
    return {k: v for k, v in headers.items() if k.lower() != "content-type"}


def test_foreign_userid_refused_when_form_encoded(headers, auth):
    user_id, _ = auth
    other = str(int(user_id) + 9999)

    r = requests.post(
        API + "/contentmanager/list",
        data={"userid": other, "grpid": "1"},          # form-urlencoded
        headers=_auth_only(headers),
        timeout=TIMEOUT,
    )
    assert r.status_code == 403, (
        "form-encoded body naming account %s was answered %s, not 403"
        % (other, r.status_code)
    )
    assert "Not authorised" in r.text


def test_foreign_userid_refused_when_multipart(headers, auth):
    user_id, _ = auth
    other = str(int(user_id) + 9999)

    r = requests.post(
        API + "/contentmanager/list",
        files={"userid": (None, other), "grpid": (None, "1")},   # multipart
        headers=_auth_only(headers),
        timeout=TIMEOUT,
    )
    assert r.status_code == 403, (
        "multipart body naming account %s was answered %s, not 403"
        % (other, r.status_code)
    )
    assert "Not authorised" in r.text


def test_own_userid_still_served_when_form_encoded(headers, auth):
    """The control: the view genuinely reads a form body, so the refusals above
    are the guard working -- not the view failing to see the field."""
    user_id, _ = auth
    r = requests.post(
        API + "/contentmanager/list",
        data={"userid": user_id, "grpid": "1"},
        headers=_auth_only(headers),
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("status") == "true", r.text[:500]
