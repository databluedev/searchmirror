"""Authentication regressions for the public login endpoint."""

import re
from pathlib import Path

import requests

from conftest import API, EMAIL, TIMEOUT


def _known_non_user_password():
    """Exercise any legacy alternate-password branch without preserving its secret."""
    source = (
        Path(__file__).parents[1] / "backend" / "account" / "api" / "views.py"
    ).read_text(encoding="utf-8")
    match = re.search(r'if\s+password\s*==\s*["\']([^"\']+)["\']', source)
    return match.group(1) if match else "pytest-definitely-not-the-user-password"


def test_login_rejects_password_not_owned_by_user():
    response = requests.post(
        API + "/api/account/login/",
        json={"username": EMAIL, "password": _known_non_user_password()},
        timeout=TIMEOUT,
    )

    body = response.json()
    assert response.status_code in {400, 401, 403, 404}, body
    assert body.get("status") != "true", body
    assert not body.get("token"), body
