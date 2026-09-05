"""Email-verified signup must work with only the required profile fields.

RegistrationSerializer.save() read five OPTIONAL fields out of validated_data
with [] rather than .get() -- designation, campaign, medium, source, referral.
A client that posted without them got KeyError out of the serializer, so the
PUBLIC signup endpoint answered 500 rather than registering the account.

The account this creates is removed again in the fixture teardown. It has to
create one: validation gates save(), so a payload that fails validation never
reaches the code under test.
"""

import subprocess
import uuid

import pytest
import requests

from conftest import API, TIMEOUT


def _purge(email):
    """Remove the probe account and everything registration created with it.

    Runs in the backend container: the app is djongo on MongoDB and there is no
    delete-account endpoint to call.

    This used to ignore the subprocess result entirely, so a purge that failed
    left a real account behind and said nothing. It now verifies the account is
    gone and fails the test if it is not -- a leak the suite cannot see is a
    leak that grows every run. `Accountusage` is included because registration
    creates one and the old purge did not touch it.
    """
    script = (
        "import django,os;"
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE','tracker.settings');"
        "django.setup();"
        "from serp.models import Account, Accountusage, Userregistrationtoken;"
        "from rest_framework.authtoken.models import Token;"
        "a=Account.objects.filter(email=%r).first();"
        "Token.objects.filter(user_id=a.id).delete() if a else None;"
        "Accountusage.objects.filter(fb_user_id=a.id).delete() if a else None;"
        "a.delete() if a else None;"
        "Userregistrationtoken.objects.filter(email=%r).delete();"
        "print('REMAINING %%d' %% Account.objects.filter(email=%r).count())"
        % (email, email, email)
    )
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-c", script],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (
        "could not remove the probe account %s -- it is still in the database: %s"
        % (email, (result.stderr or "")[-400:])
    )
    assert "REMAINING 0" in (result.stdout or ""), (
        "the probe account %s survived teardown: %s" % (email, result.stdout[-200:])
    )


def _registration_token(email):
    key = uuid.uuid4().hex + uuid.uuid4().hex
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-c",
         "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','tracker.settings');"
         "django.setup();"
         "from serp.models import Userregistrationtoken;"
         "Userregistrationtoken.objects.update_or_create(email=%r,defaults={'reg_key':%r,'ip_address':'127.0.0.1','user_agent':'pytest'});"
         "print(%r)" % (email, key, key)],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr
    return key


def _password_reset_token(email):
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-c",
         "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','tracker.settings');"
         "django.setup();"
         "from account.authorization.models import ResetPasswordToken;"
         "token=ResetPasswordToken.objects.get(user__email=%r);"
         "print(token.key)" % email],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


@pytest.fixture
def probe_email():
    email = "pytest_%s@local.test" % uuid.uuid4().hex[:10]
    yield email
    _purge(email)


def test_minimal_signup_succeeds(probe_email):
    password = "PytestProbe12345"
    registration_token = _registration_token(probe_email)
    r = requests.post(
        API + "/api/account/register/",
        json={"username": probe_email.split("@")[0], "email": probe_email,
              "password": password, "password2": password,
              "userregtoken": registration_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        "signup answered HTTP %s for a payload with no designation/campaign/"
        "medium/source/referral" % r.status_code
    )
    body = r.json()
    assert body.get("status") == "true", body
    # The account is useless without one, and Token.objects.get() used to raise
    # here if the post-save signal had not fired -- 500 AFTER creating the row,
    # leaving an account that could never log in.
    assert body.get("token"), "registered without issuing a token: %s" % body


def test_the_new_account_can_log_in(probe_email):
    password = "PytestProbe12345"
    registration_token = _registration_token(probe_email)
    requests.post(
        API + "/api/account/register/",
        json={"username": probe_email.split("@")[0], "email": probe_email,
              "password": password, "password2": password,
              "userregtoken": registration_token},
        timeout=TIMEOUT,
    )
    r = requests.post(
        API + "/api/account/login/",
        json={"username": probe_email, "password": password},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("status") == "true", r.text[:200]


def test_signup_without_email_verification_is_rejected(probe_email):
    password = "PytestProbe12345"
    r = requests.post(
        API + "/api/account/register/",
        json={"username": probe_email.split("@")[0], "email": probe_email,
              "password": password, "password2": password},
        timeout=TIMEOUT,
    )
    assert r.status_code == 400, r.text[:200]
    assert r.json().get("status") == "false", r.text[:200]


def test_signup_link_request_does_not_disclose_the_token(probe_email):
    r = requests.post(
        API + "/user_reg_token",
        json={"email": probe_email},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("status") == "true", body
    assert "user_reg_token" not in body, body


def test_password_reset_is_public_and_changes_the_password(probe_email):
    original_password = "PytestProbe12345"
    new_password = "ResetProbe12345!"
    registration_token = _registration_token(probe_email)
    signup = requests.post(
        API + "/api/account/register/",
        json={
            "username": probe_email.split("@")[0],
            "email": probe_email,
            "password": original_password,
            "password2": original_password,
            "userregtoken": registration_token,
        },
        timeout=TIMEOUT,
    )
    assert signup.status_code == 200, signup.text[:200]

    requested = requests.post(
        API + "/reset/",
        json={"email": probe_email},
        timeout=TIMEOUT,
    )
    assert requested.status_code == 200, requested.text[:200]
    assert requested.json().get("status") == "true", requested.text[:200]

    reset_token = _password_reset_token(probe_email)
    validated = requests.post(
        API + "/reset/validate_token/",
        json={"token": reset_token},
        timeout=TIMEOUT,
    )
    assert validated.status_code == 200, validated.text[:200]
    assert validated.json().get("status") == "true", validated.text[:200]

    confirmed = requests.post(
        API + "/reset/confirm/",
        json={"token": reset_token, "password": new_password},
        timeout=TIMEOUT,
    )
    assert confirmed.status_code == 200, confirmed.text[:200]
    assert confirmed.json().get("status") == "true", confirmed.text[:200]

    login = requests.post(
        API + "/api/account/login/",
        json={"username": probe_email, "password": new_password},
        timeout=TIMEOUT,
    )
    assert login.status_code == 200, login.text[:200]
    assert login.json().get("status") == "true", login.text[:200]
