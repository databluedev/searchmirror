"""A brand-new account must not meet a 500 on its first day.

Every case here is a row that simply does not exist yet on a fresh install.
The code dereferenced the result of .first() without checking, so "nothing
here yet" arrived as a server error rather than as an empty answer.
"""

import requests

from conftest import API, TIMEOUT


def test_keyword_ads_without_history(headers, auth):
    """KeywordHistory appears the first time a keyword is ranked.

    Open a keyword's detail panel before any ranking run and this used to
    raise AttributeError on None -- so on a fresh install every newly added
    keyword broke its own panel.
    """
    user_id, _ = auth
    r = requests.post(
        API + "/kwads",
        json={"userid": user_id, "grpid": "1", "kwid": "999999", "type": "tp"},
        headers=headers, timeout=TIMEOUT,
    )
    assert r.status_code == 200, "kwads answered HTTP %s" % r.status_code
    assert r.json().get("status") == "true"
    assert r.json().get("lst") == []


def test_keyword_competitors_without_history(headers, auth):
    user_id, _ = auth
    r = requests.post(
        API + "/kwcomps",
        json={"userid": user_id, "grpid": "1", "kwid": "999999", "type": "tp"},
        headers=headers, timeout=TIMEOUT,
    )
    assert r.status_code == 200, "kwcmptrs answered HTTP %s" % r.status_code
    assert r.json().get("status") == "true"


def test_add_keyword_rejects_unknown_language(headers, auth):
    """The language name comes straight from the request. An unrecognised one
    is a bad request; it used to be a 500 on Add Keyword."""
    user_id, _ = auth
    r = requests.post(
        API + "/addkeyv3",
        json={"userid": user_id, "grpid": "1",
              "language": "NotARealLanguage", "keyword": ["x"]},
        headers=headers, timeout=TIMEOUT,
    )
    assert r.status_code == 200, "addkeyv3 answered HTTP %s" % r.status_code
    body = r.json()
    assert body.get("status") == "false"
    assert "language" in (body.get("message") or "").lower(), body


def test_usage_summary_survives(headers, auth):
    """redirectcheck dereferenced the Accountusage row without checking."""
    user_id, _ = auth
    r = requests.post(
        API + "/redirectcheck",
        data={"userid": user_id, "grpid": "1"},
        headers={"Authorization": headers["Authorization"]}, timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]


def test_recipient_and_mail_switch_reads(headers, auth):
    """Both dereferenced the project row; a deleted project made them 500."""
    user_id, _ = auth
    auth_only = {"Authorization": headers["Authorization"]}
    for path in ("rpntmailupdate", "mailoptswupdate", "projectsetting"):
        r = requests.post(API + "/" + path,
                          data={"userid": user_id, "grpid": "1"},
                          headers=auth_only, timeout=TIMEOUT)
        assert r.status_code == 200, "%s answered HTTP %s" % (path, r.status_code)


def test_missing_serp_link_is_a_clean_not_found(headers, auth):
    """An old/missing preview token must never call a retired host or raise."""
    user_id, _ = auth
    r = requests.post(
        API + "/gresultpage",
        json={"userid": user_id, "grpid": "1", "kwid": 999999,
              "pageType": ""},
        headers=headers, timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("status") == "false", body
    assert "not found" in (body.get("message") or "").lower(), body


def test_missing_keyword_detail_is_a_clean_not_found(headers, auth):
    user_id, _ = auth
    r = requests.post(
        API + "/keyauth",
        json={
            "userid": user_id,
            "grpid": "1",
            "kwid": 999999,
            "type": "full",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("status") == "false", body
    assert "not found" in (body.get("message") or "").lower(), body


def test_report_widget_serializes_its_page_result(headers, auth):
    user_id, _ = auth
    response = requests.post(
        API + "/dynamic_widget",
        json={"userid": user_id, "grpid": "1", "page": 1},
        headers=headers,
        timeout=TIMEOUT,
    )

    assert response.status_code == 200, response.text[:200]
    body = response.json()
    assert body != {"st": 0, "dt": "Something went wrong"}, body
