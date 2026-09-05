"""Launch-critical report downloads against the running local stack."""

import csv
import io

import pytest
import requests


TIMEOUT = 60


def _project_with_keywords(api, session, headers, user_id):
    response = session.post(
        api + "/homeauth",
        json={"userid": user_id},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, response.text
    projects = response.json().get("data", [])
    project = next((item for item in projects if item.get("kw_ln", 0) > 0), None)
    assert project, "The seeded account needs one project with ranking keywords"
    return str(project["GY"])


def test_keyword_report_download_is_scoped_and_immediately_usable(
    api, session, auth, headers
):
    user_id, _ = auth
    group_id = _project_with_keywords(api, session, headers, user_id)

    response = session.post(
        api + "/local_report_export",
        json={"userid": user_id, "grpid": group_id},
        headers=headers,
        timeout=TIMEOUT,
    )

    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/csv")
    assert "attachment;" in response.headers["Content-Disposition"]

    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows
    assert {"keyword", "Rank", "Best rank", "Volume", "URL"}.issubset(rows[0])
    assert all(row["Volume"] != "init" for row in rows)

    anonymous = requests.post(
        api + "/local_report_export",
        json={"userid": user_id, "grpid": group_id},
        timeout=TIMEOUT,
    )
    assert anonymous.status_code in (401, 403)

    missing_project = session.post(
        api + "/local_report_export",
        json={"userid": user_id, "grpid": "999999999"},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert missing_project.status_code == 404


def test_saved_keyword_report_never_exposes_internal_volume_sentinels(
    api, session, auth, headers
):
    user_id, _ = auth
    projects_response = session.post(
        api + "/homeauth",
        json={"userid": user_id},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert projects_response.status_code == 200, projects_response.text

    report_rows = []
    for project in sorted(
        projects_response.json().get("data", []),
        key=lambda item: item.get("kw_ln", 0),
        reverse=True,
    ):
        response = session.post(
            api + "/dynamic_widget",
            json={"userid": user_id, "grpid": project["GY"], "page": 1},
            headers=headers,
            timeout=TIMEOUT,
        )
        if response.status_code == 200 and response.json().get("st") == 1:
            report_rows = response.json().get("dt", [])
            break

    # This asserts a property OF a saved report -- that the internal
    # "init" search-volume sentinel never reaches the response. With no saved
    # report the assertion is vacuous, and a fresh seed has none: reports
    # appear only after a rank run, which CI must never perform because it
    # spends provider credits. Skip rather than fail on an empty database.
    if not report_rows:
        pytest.skip("no saved keyword report on this instance; nothing to check")

    assert "init" not in str(report_rows).lower()
