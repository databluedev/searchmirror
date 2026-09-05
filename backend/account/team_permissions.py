"""Supported team-role modules and the API surfaces they protect.

FAILS CLOSED. A path that appears in none of the maps below resolves to
``DENY_MODULE``, which no role can hold, so a team member is refused. The
previous behaviour was the opposite: an unmapped path returned ``(None, None)``
and the middleware skipped the role check entirely, which meant the map was
also the list of endpoints that were protected -- every endpoint added since,
every one nobody thought of, and every cron or report surface was reachable by
any member of any role. Adding an endpoint should not silently widen what a
restricted role can do.

Consequence for whoever adds an endpoint: route it here as well, or team
members get a 403. That is the intended failure direction.
"""


# Returned for any path that is not classified. No role holds a module by this
# name -- `_valid_modules` in serp/roles.py restricts stored roles to
# TEAM_MODULES -- so the middleware's `modules.get(module)` misses and refuses.
DENY_MODULE = "__unmapped__"


TEAM_MODULES = {
    "Prjcts",
    "Widgets",
    "Keyword",
    "LLMTracker",
    "ContentPlanner",
    "CompAi",
    "Reports",
    "Settings",
}


_PREFIX_MODULES = {
    "/contentmanager/": "ContentPlanner",
    "/llmtracker/": "LLMTracker",
    "/compai/": "CompAi",
}


# The only paths that stay reachable without a module. Each is here because
# gating it would break a member who is entitled to be signed in, and none of
# them read or write another account's data:
#
#  * the registration and referral endpoints are AllowAny and normally arrive
#    with no member session at all -- listing them stops a leftover token from
#    turning sign-up into a 403;
#  * /last_logout ends the member's own session, so refusing it would strand
#    them signed in;
#  * /country_list is a static reference list with no account scope.
#
# Everything an account owns -- including /account_settings -- is gated. Note
# that _OWNER_ONLY_PATHS in account/ownership.py lists "/acc_settings", which
# is not a routed path; the routed one is "/account_settings", and it is left
# unmapped here deliberately so members are refused it.
_OPEN_PATHS = {
    "/new_user_create",
    "/user_reg_token",
    "/user_regtoken_verify",
    "/refregadd",
    "/last_logout",
    "/country_list",
    # Sign-in and the two session-level reads the shell makes on every route.
    # /api/account/capabilities returns booleans and prose only -- whether a
    # feature can run and what it needs -- never key material, so a member
    # seeing it learns nothing they could not infer from the feature failing.
    # It is what the "you have no key" notices render, so gating it would hide
    # the explanation from exactly the people who hit the wall.
    "/api/account/login",
    "/api/account/Glogin",
    "/api/account/register",
    "/api/account/token",
    "/api/account/serviceauthenticate",
    "/api/account/capabilities",
}


_PATH_MODULES = {
    # Dashboard
    "/homeauth": "Prjcts",
    # App shell. Every stored role carries "Prjcts" -- serp/roles.py refuses to
    # save one without it -- so gating the shell on it costs no member access
    # while keeping the endpoints inside the check rather than beside it.
    "/baseauth": "Prjcts",
    "/menu_details": "Prjcts",
    "/getsetting": "Prjcts",
    "/projectoverview": "Prjcts",
    "/project_overview_change": "Prjcts",
    "/projectrefreshstatus": "Prjcts",
    "/dashboard_view_change": "Prjcts",
    "/d2Vla2x5X3NlYXJjaF9wYWdlc193aWRnZXQ": "Widgets",
    "/AP_d2V20ic2ZJnV5d2V90YX9ylZXRfaZHM": "Keyword",
    "/tablecolumsupdate": "Keyword",
    # Report builders and exports
    "/export": "Reports",
    "/pdfexport": "Reports",
    "/overview_sheet": "Reports",
    "/e-overview_sheet": "Reports",
    "/e-domain_sheet": "Reports",
    "/e-gsc_sheet": "Reports",
    "/e-keyword_sheet": "Reports",
    "/dF9kb21YG9yhaW5cWV0cmljfbWRkX3Jlcw": "Reports",
    "/dF9rZYWRkXb21ldH3JlcG9y3JkXXl3JY3Mp": "Reports",
    "/G9ydFcWRkV0cml9n2YjX3JlcNfbWcw": "Reports",
    "/kX3JlYWF9nYV9tZRcXRyaWG9ydNz": "Reports",
    "/check_report": "Reports",
    # NOT listed: /report_schedule_emails, /csv_report_mailer and the ga_*
    # crawlers. They are @cron_only scheduler endpoints, not user surfaces, so
    # they belong in no team module -- mapping one to "Reports" would let a
    # member holding that module past this check. Unmapped, they fail closed
    # here as well as in cron_auth.
    "/mailoptswupdate": "Settings",
    "/kcip_wdt": "Widgets",
    "/dnert_wdt": "Widgets",
    "/aived_wdt": "Widgets",
    "/erocs_wdt": "Widgets",
    "/airav_wdt": "Widgets",
    "/ecnis_wdt": "Widgets",
    "/eldnah_wdt": "Widgets",
    "/Y25iX3dkdA": "Widgets",
    "/JkcaW1RrZXl3b3wcm92ZW193aWRnZXQ": "Widgets",
    "/jbGluZWZG3Jkc19VRrZXl3b3aWRnZXQ": "Widgets",
    # Keywords and keyword detail
    "/gridauth": "Keyword",
    "/dashservice": "Keyword",
    "/keyauth": "Keyword",
    "/kwads": "Keyword",
    "/kwcomps": "Keyword",
    "/kwsvolume": "Keyword",
    "/kwnotes": "Keyword",
    "/kwnotecreate": "Keyword",
    "/kwnoteupdate": "Keyword",
    "/kwnotedelete": "Keyword",
    "/dm90ZlldhbGx19fbmXM": "Keyword",
    "/kw_gph": "Keyword",
    "/gresultpage": "Keyword",
    "/getlabels": "Keyword",
    "/update_tags": "Keyword",
    "/updatetag": "Keyword",
    "/remove_tag": "Keyword",
    "/addkeyv3": "Keyword",
    "/multidelete": "Keyword",
    "/usercrawl": "Keyword",
    "/refreshstatus": "Keyword",
    # Reports
    "/dynamic_widget": "Reports",
    "/rpt_dlte": "Reports",
    "/sheet_update": "Reports",
    "/gen_report": "Reports",
    "/local_report_export": "Reports",
    "/report_schedule_add": "Reports",
    "/report_schedule_delete": "Reports",
    "/reportsentnow": "Reports",
    # Project settings (never account/profile/API/team settings)
    "/projectsetting": "Settings",
    "/rpntmailupdate": "Settings",
    "/project_branded_keywords": "Settings",
    "/cmQkX2JyeXdYW5kX2tlvcmQYWR": "Settings",
    "/ZHNbmRfa2V5d29yfbGlzdYnJhA": "Settings",
    "/kX2tleXdZGVslX2JyYW5vZXRcmQ": "Settings",
}


_ACTION_PATHS = {
    "/addnewkey": ("Prjcts", "Add Project"),
    "/updategroupservice": ("Prjcts", "Rename Project"),
    "/deletegroupservice": ("Prjcts", "Delete Project"),
    "/eldnah_wdt": ("Widgets", "Manage Widgets"),
    "/addkeyv3": ("Keyword", "Add Keywords"),
    "/multidelete": ("Keyword", "Delete Keywords"),
    "/usercrawl": ("Keyword", "Manual Refresh"),
    "/update_tags": ("Keyword", "Manage Tag"),
    "/updatetag": ("Keyword", "Manage Tag"),
    "/remove_tag": ("Keyword", "Manage Tag"),
    "/kwnotecreate": ("Keyword", "Manage Notes"),
    "/kwnoteupdate": ("Keyword", "Manage Notes"),
    "/kwnotedelete": ("Keyword", "Manage Notes"),
    "/ub3RlZGVsNplX39bmdsZVZXRub3Rl": ("Keyword", "Manage Notes"),
    # Accepting a spelling correction can create a second keyword row, so it is
    # gated as an add rather than as a plain Keyword read.
    "/typoerrorfix": ("Keyword", "Add Keywords"),
    "/llmtracker/add": ("LLMTracker", "Manage Geo Citations"),
    "/llmtracker/delete": ("LLMTracker", "Manage Geo Citations"),
    "/llmtracker/trigger-processing": ("LLMTracker", "Manage Geo Citations"),
    "/llmtracker/generate-prompts": ("LLMTracker", "Manage Geo Citations"),
    "/contentmanager/create": ("ContentPlanner", "Manage Content"),
    "/contentmanager/delete": ("ContentPlanner", "Manage Content"),
    "/contentmanager/update": ("ContentPlanner", "Manage Content"),
    "/contentmanager/generate": ("ContentPlanner", "Manage Content"),
    "/compai/addcompetitors": ("CompAi", "Add Competitor"),
    "/compai/skipanalysis": ("CompAi", "Add Competitor"),
    "/compai/startanalysis": ("CompAi", "Re-analysis Competitor"),
    "/compai/deletecompetitor": ("CompAi", "Delete Competitor"),
    "/report_schedule_add": ("Reports", "Add Report"),
    "/rpt_dlte": ("Reports", "Delete Report"),
    "/gen_report": ("Reports", "Enable Export"),
    "/local_report_export": ("Reports", "Enable Export"),
    "/sheet_update": ("Reports", "Rename Report"),
    "/cmQkX2JyeXdYW5kX2tlvcmQYWR": ("Settings", "Manage Branded Keywords"),
    "/kX2tleXdZGVslX2JyYW5vZXRcmQ": ("Settings", "Manage Branded Keywords"),
    "/reset_track_day": ("Settings", "Manage Connected Apps"),
    "/reset_platform": ("Settings", "Manage Connected Apps"),
    "/gsctoken": ("Settings", "Manage Connected Apps"),
    "/ga_connect": ("Settings", "Manage Connected Apps"),
}


_TYPED_ACTION_PATHS = {
    "/project_branded_keywords": {
        "module": "Settings",
        "action": "Manage Branded Keywords",
        "read_operations": {"list"},
    },
    "/connectgsc": {
        "module": "Settings",
        "action": "Manage Connected Apps",
        "read_operations": {"verify"},
    },
    "/connectga": {
        "module": "Settings",
        "action": "Manage Connected Apps",
        "read_operations": {"verify"},
    },
}


_PAYLOAD_FIELD_ACTION_PATHS = {
    "/rpntmailupdate": {
        "module": "Settings",
        "action": "Manage Recipients",
        "mutation_field": "rp_m",
    },
    # Reads without "adv", writes with it. Unmapped, the deny-by-default rule
    # refused a member the read too, so the settings page broke for them.
    "/prjctserpmode": {
        "module": "Settings",
        "action": "Manage Connected Apps",
        "mutation_field": "adv",
    },
}


def required_team_permission(path, payload=None):
    """Return ``(module, action or None)`` required for a team request.

    Never returns ``(None, None)`` for a path that is merely unknown: an
    unclassified path returns ``(DENY_MODULE, None)`` so the caller refuses it.
    Only the paths named in ``_OPEN_PATHS`` skip the check.
    """
    path = path.rstrip("/") or "/"
    if path in _OPEN_PATHS:
        return None, None
    field_permission = _PAYLOAD_FIELD_ACTION_PATHS.get(path)
    if field_permission:
        is_mutation = (
            isinstance(payload, dict)
            and field_permission["mutation_field"] in payload
        )
        return (
            field_permission["module"],
            field_permission["action"] if is_mutation else None,
        )
    typed_permission = _TYPED_ACTION_PATHS.get(path)
    if typed_permission:
        operation = ""
        if isinstance(payload, dict):
            operation = str(payload.get("type") or "").strip().lower()
        if operation in typed_permission["read_operations"]:
            return typed_permission["module"], None
        return typed_permission["module"], typed_permission["action"]
    if path in _ACTION_PATHS:
        return _ACTION_PATHS[path]
    if path in _PATH_MODULES:
        return _PATH_MODULES[path], None
    for prefix, module in _PREFIX_MODULES.items():
        if path.startswith(prefix):
            return module, None
    return DENY_MODULE, None
