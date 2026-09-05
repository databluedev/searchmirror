"""Refuse a request that acts for a user id other than the caller's.

Almost every view here identifies the account from a `userid` in the request
body rather than from `request.user`. Where a view calls
`account.verify.validate` that is safe -- validate() looks up the Token row FOR
THAT userid and compares it against the Authorization header, so a mismatched
id fails. 56 views did not call it, and in those the body's userid went straight
into the query: any authenticated account could read or mutate another
account's rows by changing one number.

Demonstrated before this existed: a second account's token called
POST /contentmanager/list with {"userid": "1"} and received user 1's content
plans, while POST /getsetting -- which does call validate() -- refused the
identical request.

WHY MIDDLEWARE RATHER THAN A DRF PERMISSION
-------------------------------------------
DEFAULT_PERMISSION_CLASSES only applies to views that do not declare their own
`@permission_classes`, and many of the 56 do -- they would have opted out of the
fix by accident, which is exactly how they got here. Middleware also covers the
plain Django views that are not DRF at all, where `@permission_classes` is inert
because nothing consults it.

The cost is that this runs before DRF authenticates, so it resolves the token
itself instead of reading `request.user`.
"""

import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse


# universal-cookie 8 parses JSON-looking cookie values. A cookie containing
# ``"1"`` therefore becomes the number ``1`` in the browser, while this
# legacy API's identifier contract is string-based (many views call
# ``.strip()`` or ``.isdigit()`` before querying). Keep that compatibility at
# one request boundary instead of making every view defend itself.
_STRING_IDENTIFIER_KEYS = {
    "id",
    "userid",
    "grpid",
    "groupid",
    "cgrpid",
    "kwid",
    "reportid",
    "singleid",
    "logid",
    "noteid",
}


def _normalise_json_identifiers(request):
    """Convert numeric JSON identifiers to the API's canonical string form."""
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    if "application/json" not in (request.META.get("CONTENT_TYPE") or ""):
        return

    try:
        payload = json.loads(request.body or b"{}")
    except Exception:
        return
    if not isinstance(payload, dict):
        return

    changed = False
    for key, value in payload.items():
        normalised_key = str(key).lower()
        is_identifier = (
            normalised_key in _STRING_IDENTIFIER_KEYS
            or normalised_key.endswith("_id")
        )
        if is_identifier and isinstance(value, int) and not isinstance(value, bool):
            payload[key] = str(value)
            changed = True

    if changed:
        # request.body is a cached property. Replacing its cache here means DRF
        # and plain Django views both parse the normalized representation.
        request._body = json.dumps(payload, separators=(",", ":")).encode("utf-8")


_FORM_CONTENT_TYPES = ("application/x-www-form-urlencoded", "multipart/form-data")


def _request_payload(request):
    """The body of a mutating request, read the same way the view will read it.

    Covers exactly DRF's three default parsers -- JSON, form-urlencoded and
    multipart. That set is the whole point: a body shape this guard cannot
    read but a VIEW can is a bypass, and that is not hypothetical. The
    JSON-only version of this function was defeated by changing one header --
    `POST /contentmanager/list` with `{"userid": <someone else>}` was refused
    as `application/json` and answered 200 as `x-www-form-urlencoded`, because
    DRF populated `request.data` from the form body while this module looked
    only at `request.body` and saw nothing to check.

    Returns a mapping, empty when there is nothing to inspect. QueryDict is a
    dict subclass, so callers can treat both cases alike.

    Reading `request.POST` on a multipart request exhausts the upload stream.
    DRF anticipates exactly this: `Request._parse()` falls back to
    `request.POST`/`request.FILES` when the stream is already consumed and the
    view supports form parsing, precisely so that middleware may do this.
    """
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return {}

    content_type = (request.META.get("CONTENT_TYPE") or "").lower()

    if "application/json" in content_type:
        try:
            # Django caches request.body, so DRF still parses it afterwards.
            payload = json.loads(request.body or b"{}")
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    if any(form_type in content_type for form_type in _FORM_CONTENT_TYPES):
        return request.POST

    # Anything else is a body DRF's default parsers will not read either, so
    # the view cannot see a userid in it and there is nothing to guard.
    return {}


def _claimed_userid(request):
    """The user id this request says it is acting for, or None.

    Reads the query string first, then the body -- in whatever content type it
    arrived as. See `_request_payload`.
    """
    raw = request.GET.get("userid")

    if raw is None:
        raw = _request_payload(request).get("userid")

    if raw is None:
        return None
    raw = str(raw).strip()
    return int(raw) if raw.isdigit() else None


def _caller_userid(request):
    """The account id behind the Authorization header, or None if unauthenticated."""
    caller, _ = _caller_identity(request)
    return caller


def _caller_identity(request):
    """Return ``(owner id, team member or None)`` for a token credential.

    Resolved once per request and shared with DRF's authenticator and
    verify.validate -- all three used to issue their own token read, at ~6ms
    each under djongo. See account/identity.py for why sharing it is safe.
    Behaviour here is unchanged: same pair, same None for an unresolvable
    credential.
    """
    from account.identity import caller_identity

    return caller_identity(request)


def _claimed_project_ids(request):
    """Return project identifiers explicitly named by the request."""
    project_keys = {"grpid", "groupid", "group_id", "fk_group_id"}
    raw_values = [
        value
        for key, value in request.GET.items()
        if str(key).lower() in project_keys
    ]

    raw_values.extend(
        value
        for key, value in _request_payload(request).items()
        if str(key).lower() in project_keys
    )

    project_ids = set()
    for value in raw_values:
        value = str(value).strip()
        if value.isdigit():
            project_ids.add(int(value))
    return project_ids


_OWNER_ONLY_PATHS = {
    "/my_view/",
    "/rl_delete",
    "/get_team",
    "/del_team",
    "/teams",
    "/team_mng",
    "/mng_tm_prjcts",
    "/profile_settings",
    "/acc_settings",
}


def _owner_only_path(path):
    return path in _OWNER_ONLY_PATHS or path.startswith(
        (
            "/api/account/ai-keys",
            "/api/account/serp-key",
            "/api/account/change_password",
        )
    )


class UserIdOwnershipMiddleware:
    """Block any authenticated request naming a userid that is not the caller's."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _normalise_json_identifiers(request)
        claimed = _claimed_userid(request)
        caller, member = _caller_identity(request)

        if member is not None and _owner_only_path(request.path):
            return JsonResponse(
                {"status": "false", "message": "Owner access is required."},
                status=403,
            )

        if member is not None:
            from account.team_permissions import required_team_permission
            from serp.models import Roles

            payload = _request_payload(request)

            module, action = required_team_permission(request.path, payload)
            if module:
                role = Roles.objects.filter(
                    id=member.role_id,
                    fk_user_id=caller,
                ).first()
                modules = role.modules if role and isinstance(role.modules, dict) else {}
                allowed_actions = modules.get(module)
                module_allowed = isinstance(allowed_actions, list)
                action_allowed = action is None or action in allowed_actions
                if not module_allowed or not action_allowed:
                    return JsonResponse(
                        {
                            "status": "false",
                            "message": "Your role does not allow this action.",
                        },
                        status=403,
                    )

            claimed_projects = _claimed_project_ids(request)
            if claimed_projects:
                from team_management.models import TeamProject

                allowed_projects = set(
                    TeamProject.objects.filter(
                        fk_user_id=caller,
                        client_id=member.id,
                        group__in=claimed_projects,
                    ).values_list("group", flat=True)
                )
                if allowed_projects != claimed_projects:
                    return JsonResponse(
                        {
                            "status": "false",
                            "message": "Not authorised for that project.",
                        },
                        status=403,
                    )

        # No userid in play, or no credentials to compare it against. The
        # AllowAny endpoints (login, registration, the token-gated cron hooks)
        # carry their own checks and have no session to measure this against.
        if claimed is not None:
            if caller is not None and int(caller) != int(claimed):
                return JsonResponse(
                    {"status": "false", "message": "Not authorised for that account."},
                    status=403,
                )

        return self.get_response(request)
