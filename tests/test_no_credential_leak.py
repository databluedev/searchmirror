"""No public endpoint may hand out a credential, and no bad input may 500.

The report share link used to answer an anonymous caller with the ACCOUNT
OWNER'S API token: split in half, padded with random characters, the pieces
separated by uppercase letters. The token is lowercase hex, so the split was
unambiguous, and the public viewer page reassembled it in four lines of
JavaScript and sent it as `Authorization`. The slug guarding it was a scramble
of the group id -- enumerable, not secret -- so the links were guessable.

The whole feature is gone. These assert it stays gone, and that the remaining
public pages refuse malformed input without raising.
"""

import re

import pytest
import requests

from conftest import API, TIMEOUT

# a 40-character lowercase hex run is what a DRF auth token looks like
TOKEN_SHAPE = re.compile(r"\b[0-9a-f]{40}\b")

REPORT_ROUTES = [
    "report/ml0aWFG9ydF9pbsX2xvYWQbGl2ZXJlc/anything",
    "report/zVbyZXBvcnGl29Q",
    "report/aW5ncwbGl2ZXJlcG9ydF9zZXR0aW5ncw",
    "report/cG9ydF9nZFbGl2ZXJl0ZW5lcmV91cmw",
]


@pytest.mark.parametrize("path", REPORT_ROUTES)
def test_live_report_endpoints_are_gone(path):
    r = requests.get(API + "/" + path, timeout=TIMEOUT)
    assert r.status_code == 404, (
        "%s still routes (HTTP %s). It answered anonymous callers with the "
        "account owner's API token." % (path, r.status_code)
    )


@pytest.mark.parametrize("path", REPORT_ROUTES)
def test_no_token_shaped_string_in_any_response(path):
    """Belt and braces: even a 404 body must not carry something token-shaped."""
    r = requests.get(API + "/" + path, timeout=TIMEOUT)
    assert not TOKEN_SHAPE.search(r.text), (
        "%s answered with a 40-char hex string -- the shape of an auth token" % path
    )


@pytest.mark.parametrize("junk", ["xx", "!!!", "a" * 200, "../../etc/passwd"])
def test_public_preview_pages_refuse_junk_without_raising(junk):
    """Retired public preview URLs stay gone and malformed input never raises."""
    for base in ("search/results", "research/results"):
        r = requests.get("%s/%s/%s" % (API, base, junk), timeout=TIMEOUT)
        assert r.status_code < 500, (
            "%s/%s answered HTTP %s -- malformed input must not raise"
            % (base, junk, r.status_code)
        )
        assert "Traceback" not in r.text
