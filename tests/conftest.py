"""Shared fixtures for the security regression suite.

These run against a RUNNING stack rather than a Django test database on
purpose. The app is djongo on MongoDB, where `manage.py test` cannot create a
test database, and every bug this suite covers was a routing/authentication
bug that only an actual HTTP request can prove. A view that looks guarded and
is not looks identical in unit tests; it does not look identical to curl.

    docker compose up -d
    pytest tests -v
"""

import os
import subprocess

import pytest
import requests

# The explicit IPv4 form. docker-compose publishes every port on 127.0.0.1, so
# this is the address that always exists regardless of how the host resolves
# "localhost".
API = os.environ.get("TRACKER_API", "http://127.0.0.1:8000")
EMAIL = os.environ.get("TRACKER_EMAIL", "admin@local.test")
PASSWORD = os.environ.get("TRACKER_PASSWORD", "LocalDev12345")

TIMEOUT = 60


@pytest.fixture(scope="session")
def api():
    return API


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    return s


@pytest.fixture(scope="session")
def auth(session):
    """(user_id, token) for the seeded account, or skip if it is not there."""
    r = session.post(
        API + "/api/account/login/",
        json={"username": EMAIL, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    if r.status_code != 200 or r.json().get("status") != "true":
        pytest.skip("no seeded account at %s -- run scripts/seed_local.py" % API)

    body = r.json()

    def dig(node, key):
        if isinstance(node, dict):
            if key in node:
                return node[key]
            for v in node.values():
                found = dig(v, key)
                if found is not None:
                    return found
        return None

    token = dig(body, "token")
    user_id = dig(body, "id")
    assert token and user_id, "login answered 200 without a token: %s" % body
    return str(user_id), str(token)


@pytest.fixture(scope="session")
def headers(auth):
    return {"Authorization": "Token %s" % auth[1], "Content-Type": "application/json"}


# --- leftover probe accounts ------------------------------------------------
#
# `tests/test_registration.py` must create a real account: validation gates
# `save()`, so a payload that fails validation never reaches the code under
# test. Its fixture removes the account in teardown, and on a clean run nothing
# is left behind.
#
# Teardown does not run when a run is INTERRUPTED, which is how
# `pytest_d1910dbfb9@local.test` ended up in the development database. A
# per-test teardown cannot fix that, because the process is already gone. So
# the sweep happens at the START of every session instead: whatever the last
# run failed to remove, this run removes before it does anything else.
#
# Scope is deliberately narrow -- only `pytest_*@local.test`, the prefix the
# probe fixture generates. It can never match a real account.

_SWEEP = (
    "import django,os;"
    "os.environ.setdefault('DJANGO_SETTINGS_MODULE','tracker.settings');"
    "django.setup();"
    "from serp.models import Account, Accountusage, Userregistrationtoken;"
    "from rest_framework.authtoken.models import Token;"
    "stale=list(Account.objects.filter(email__startswith='pytest_', email__endswith='@local.test'));"
    "ids=[a.id for a in stale];"
    "emails=[a.email for a in stale];"
    "Token.objects.filter(user_id__in=ids).delete() if ids else None;"
    "Accountusage.objects.filter(fb_user_id__in=ids).delete() if ids else None;"
    "Userregistrationtoken.objects.filter(email__in=emails).delete() if emails else None;"
    "[a.delete() for a in stale];"
    "print('SWEPT %d' % len(stale))"
)


def _backend_python(script, timeout=180):
    """Run a snippet inside the backend container. Returns (ok, output)."""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backend", "python", "-c", script],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return False, str(error)
    return result.returncode == 0, (result.stdout or "") + (result.stderr or "")


@pytest.fixture(scope="session", autouse=True)
def sweep_probe_accounts():
    """Remove probe accounts an interrupted earlier run left behind."""
    ok, output = _backend_python(_SWEEP)
    if not ok:
        # Not a failure of the run -- the stack may be remote, or docker may
        # not be reachable. Say so rather than pretending the sweep happened.
        print("probe-account sweep did not run: %s" % output.strip()[:200])
        return
    swept = [line for line in output.splitlines() if line.startswith("SWEPT ")]
    if swept and swept[-1] != "SWEPT 0":
        print("%s probe account(s) left by an earlier interrupted run were removed"
              % swept[-1].split()[1])
