"""Team accounts authenticate separately and stay inside their owner scope."""

from uuid import uuid4

import requests

from conftest import API, TIMEOUT


def test_team_login_and_project_scope(headers, auth):
    owner_id, owner_token = auth
    suffix = uuid4().hex[:10]
    role_name = "qa-%s" % suffix
    member_email = "qa-%s@example.test" % suffix
    member_password = "TeamPass-%s-A1!" % suffix
    role_id = None

    try:
        base = requests.post(
            API + "/baseauth",
            json={"userid": owner_id},
            headers=headers,
            timeout=TIMEOUT,
        ).json()
        projects = base.get("data", {}).get("slt", [])
        assert projects, "seeded owner has no project to assign"
        project_id = projects[0]["GY"]

        created = requests.post(
            API + "/my_view/",
            json={
                "userid": owner_id,
                "rl": role_name,
                "mdles": {"Prjcts": []},
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert created.status_code == 200, created.text
        assert created.json().get("st") == 1, created.text

        listed = requests.get(
            API + "/my_view/",
            params={"userid": owner_id},
            headers=headers,
            timeout=TIMEOUT,
        ).json()
        role_id = next(r["rl_id"] for r in listed["dt"] if r["rl"] == role_name)

        member = requests.post(
            API + "/teams",
            json={
                "userid": owner_id,
                "nm": "QA Member",
                "eml": member_email,
                "pass": member_password,
                "role": role_name,
                "rl_id": role_id,
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert member.status_code == 200, member.text
        assert member.json().get("st") == 1, member.text

        assigned = requests.post(
            API + "/mng_tm_prjcts",
            json={
                "userid": owner_id,
                "em": member_email,
                "prjcts": [project_id],
                "type": "project",
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json().get("st") in {0, 1}, assigned.text

        login = requests.post(
            API + "/api/account/login/",
            json={"username": member_email, "password": member_password},
            timeout=TIMEOUT,
        )
        assert login.status_code == 200, login.text
        login_body = login.json()
        assert login_body.get("status") == "true", login_body
        assert login_body.get("account_type") == "team", login_body
        assert str(login_body.get("id")) == owner_id, login_body
        assert login_body.get("token") != owner_token, login_body

        team_headers = {
            "Authorization": "Token %s" % login_body["token"],
            "Content-Type": "application/json",
        }
        team_capabilities = requests.get(
            API + "/api/account/capabilities/",
            headers=team_headers,
            timeout=TIMEOUT,
        )
        assert team_capabilities.status_code == 200, team_capabilities.text
        assert team_capabilities.json().get("status") == "true"

        team_base = requests.post(
            API + "/baseauth",
            json={"userid": owner_id},
            headers=team_headers,
            timeout=TIMEOUT,
        )
        assert team_base.status_code == 200, team_base.text
        team_projects = team_base.json().get("data", {}).get("slt", [])
        assert [p["GY"] for p in team_projects] == [project_id], team_base.text

        forbidden = requests.get(
            API + "/my_view/",
            params={"userid": owner_id},
            headers=team_headers,
            timeout=TIMEOUT,
        )
        assert forbidden.status_code == 403, forbidden.text

        team_home = requests.post(
            API + "/homeauth",
            json={"userid": owner_id},
            headers=team_headers,
            timeout=TIMEOUT,
        )
        assert team_home.status_code == 200, team_home.text
        assert [p["GY"] for p in team_home.json().get("data", [])] == [project_id]

        for path, payload in (
            ("/kcip_wdt", {"userid": owner_id, "grpid": project_id}),
            ("/contentmanager/list", {"userid": owner_id}),
            ("/compai/competitorslist", {"userid": owner_id, "grpid": project_id}),
        ):
            denied = requests.post(
                API + path,
                json=payload,
                headers=team_headers,
                timeout=TIMEOUT,
            )
            assert denied.status_code == 403, "%s: %s" % (path, denied.text)
    finally:
        requests.post(
            API + "/del_team",
            json={"userid": owner_id, "email": member_email},
            headers=headers,
            timeout=TIMEOUT,
        )
        if role_id is not None:
            requests.post(
                API + "/rl_delete",
                json={"userid": owner_id, "rl_id": role_id},
                headers=headers,
                timeout=TIMEOUT,
            )


def test_team_list_never_exposes_password_hash(headers, auth):
    owner_id, _ = auth
    response = requests.post(
        API + "/get_team",
        json={"userid": owner_id},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, response.text
    for member in response.json().get("dt", []):
        assert "pass" not in member


def test_team_module_access_does_not_grant_mutating_actions(headers, auth):
    owner_id, _ = auth
    suffix = uuid4().hex[:10]
    role_name = "viewer-%s" % suffix
    member_email = "viewer-%s@example.test" % suffix
    member_password = "ViewerPass-%s-A1!" % suffix
    role_id = None
    project_id = None
    original_recipients = None

    try:
        projects = requests.post(
            API + "/baseauth",
            json={"userid": owner_id},
            headers=headers,
            timeout=TIMEOUT,
        ).json().get("data", {}).get("slt", [])
        assert projects, "seeded owner has no project to assign"
        project_id = projects[0]["GY"]

        created = requests.post(
            API + "/my_view/",
            json={
                "userid": owner_id,
                "rl": role_name,
                "mdles": {
                    "Prjcts": [],
                    "Keyword": [],
                    "LLMTracker": [],
                    "ContentPlanner": [],
                    "CompAi": [],
                    "Settings": [],
                },
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert created.status_code == 200, created.text
        assert created.json().get("st") == 1, created.text

        roles = requests.get(
            API + "/my_view/",
            params={"userid": owner_id},
            headers=headers,
            timeout=TIMEOUT,
        ).json()["dt"]
        role_id = next(role["rl_id"] for role in roles if role["rl"] == role_name)

        member = requests.post(
            API + "/teams",
            json={
                "userid": owner_id,
                "nm": "Read Only Member",
                "eml": member_email,
                "pass": member_password,
                "role": role_name,
                "rl_id": role_id,
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert member.status_code == 200, member.text
        assert member.json().get("st") == 1, member.text

        assigned = requests.post(
            API + "/mng_tm_prjcts",
            json={
                "userid": owner_id,
                "em": member_email,
                "prjcts": [project_id],
                "type": "project",
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        assert assigned.status_code == 200, assigned.text

        login = requests.post(
            API + "/api/account/login/",
            json={"username": member_email, "password": member_password},
            timeout=TIMEOUT,
        )
        assert login.status_code == 200, login.text
        team_headers = {
            "Authorization": "Token %s" % login.json()["token"],
            "Content-Type": "application/json",
        }

        for path, payload in (
            ("/llmtracker/list", {"userid": owner_id, "groupid": project_id}),
            ("/contentmanager/list", {"userid": owner_id, "grpid": project_id}),
            (
                "/project_branded_keywords",
                {"userid": owner_id, "grpid": project_id, "type": "list"},
            ),
            (
                "/connectgsc",
                {"userid": owner_id, "grpid": project_id, "type": "verify"},
            ),
            (
                "/connectga",
                {"userid": owner_id, "grpid": project_id, "type": "verify"},
            ),
            ("/rpntmailupdate", {"userid": owner_id, "grpid": project_id}),
        ):
            allowed = requests.post(
                API + path,
                json=payload,
                headers=team_headers,
                timeout=TIMEOUT,
            )
            assert allowed.status_code == 200, "%s: %s" % (path, allowed.text)
            if path == "/rpntmailupdate":
                original_recipients = allowed.json().get("rp_m", [])

        for path, payload in (
            ("/llmtracker/add", {"userid": owner_id, "groupid": project_id}),
            ("/llmtracker/delete", {"userid": owner_id, "groupid": project_id}),
            ("/llmtracker/trigger-processing", {"userid": owner_id, "groupid": project_id}),
            ("/llmtracker/generate-prompts", {"userid": owner_id, "groupid": project_id}),
            ("/contentmanager/create", {"userid": owner_id, "grpid": project_id}),
            ("/contentmanager/delete", {"userid": owner_id, "grpid": project_id}),
            ("/contentmanager/update", {"userid": owner_id, "grpid": project_id}),
            ("/contentmanager/generate", {"userid": owner_id, "grpid": project_id}),
            ("/compai/addcompetitors", {"userid": owner_id, "grpid": project_id}),
            ("/compai/startanalysis", {"userid": owner_id, "grpid": project_id}),
            ("/compai/deletecompetitor", {"userid": owner_id, "grpid": project_id}),
            ("/compai/skipanalysis", {"userid": owner_id, "grpid": project_id}),
            (
                "/favour",
                {
                    "userid": owner_id,
                    "grpid": project_id,
                    "chked": "true",
                    "idcheck": "all",
                },
            ),
            ("/kwnotecreate", {"userid": owner_id, "grpid": project_id}),
            ("/kwnoteupdate", {"userid": owner_id, "grpid": project_id}),
            ("/kwnotedelete", {"userid": owner_id, "grpid": project_id}),
            (
                "/ub3RlZGVsNplX39bmdsZVZXRub3Rl",
                {"userid": owner_id, "grpid": project_id},
            ),
            (
                "/project_branded_keywords",
                {
                    "userid": owner_id,
                    "grpid": project_id,
                    "type": "save",
                    "brand_keywords": ["unauthorised-change"],
                },
            ),
            (
                "/connectgsc",
                {"userid": owner_id, "grpid": project_id, "type": "connect"},
            ),
            (
                "/connectgsc",
                {"userid": owner_id, "grpid": project_id, "type": "revoke"},
            ),
            (
                "/connectga",
                {"userid": owner_id, "grpid": project_id, "type": "revoke"},
            ),
            (
                "/reset_track_day",
                {"userid": owner_id, "grpid": project_id, "trackday": "Monday"},
            ),
            (
                "/reset_platform",
                {
                    "userid": owner_id,
                    "grpid": project_id,
                    "pltform": "Non E-commerce",
                    "resetType": False,
                },
            ),
            (
                "/rpntmailupdate",
                {
                    "userid": owner_id,
                    "grpid": project_id,
                    "rp_m": ["unauthorised@example.test"],
                },
            ),
            (
                "/gsctoken",
                {"userid": owner_id, "grpid": project_id, "type": "connect"},
            ),
            (
                "/ga_connect",
                {"userid": owner_id, "grpid": project_id},
            ),
        ):
            denied = requests.post(
                API + path,
                json=payload,
                headers=team_headers,
                timeout=TIMEOUT,
            )
            assert denied.status_code == 403, "%s: %s" % (path, denied.text)
    finally:
        if project_id is not None and original_recipients is not None:
            requests.post(
                API + "/rpntmailupdate",
                json={
                    "userid": owner_id,
                    "grpid": project_id,
                    "rp_m": original_recipients,
                },
                headers=headers,
                timeout=TIMEOUT,
            )
        requests.post(
            API + "/del_team",
            json={"userid": owner_id, "email": member_email},
            headers=headers,
            timeout=TIMEOUT,
        )
        if role_id is not None:
            requests.post(
                API + "/rl_delete",
                json={"userid": owner_id, "rl_id": role_id},
                headers=headers,
                timeout=TIMEOUT,
            )
