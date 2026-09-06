"""No routed endpoint answers a missing required field with a server error.

`api-request-validation` already requires that an endpoint missing a required
field "SHALL respond with a 4xx status and a message naming what was missing or
unusable ... It SHALL NOT raise an unhandled exception". That requirement was
written per-endpoint. Probing the whole routing table on 2026-09-06, against a
live instance with one account and no project, found **69 endpoints returning a
500** — a `KeyError` on a field the caller never sent.

The endpoints checked are DERIVED FROM THE ROUTING TABLE rather than listed
here. A list would have the same failure mode as the frontend guard this change
also fixes: 21 of 54 callers were simply forgotten. A new route cannot be
omitted from this check by forgetting to add it — only by adding it to
`EXCLUDED` below, with a reason.

**On status codes.** This API answers a handled failure with `200` and
`{"status": "false"}`. That is not what a fresh design would do, but it is
consistent across roughly seventy endpoints and the frontend reads the body
field rather than the status line at 99 call sites — so converting them to 4xx
would turn a visible failure into a silent one across most of the product. That
convention is a recorded deviation, not this test's business. What this test
forbids is the *unhandled* case: a 5xx, where a client mistake consumed a
worker to render a server error.
"""

import re
from pathlib import Path

import pytest
import requests

from conftest import API, TIMEOUT

ROOT = Path(__file__).parents[1]
URLS_ROOT = ROOT / "backend" / "tracker" / "urls.py"

# Endpoints this test must not send a request to, each with the reason.
# Keep this small. An entry here is a decision, not a convenience.
EXCLUDED = {
    "/rank/schedule": "queues rank runs; every one spends a DataBlue request",
    "/llmtracker/manage": (
        "scheduler entry point behind @cron_only. Without CRON_TOKEN it answers "
        "503 by design -- failing closed is the point, and reaching it would "
        "spend the account's AI credits."
    ),
}


def _routes():
    """Every routed path, resolved from the URL configuration itself."""
    root = URLS_ROOT.read_text(encoding="utf-8")

    prefixes = re.findall(r'path\(\s*"([^"]*)"\s*,\s*include\(\s*"([^"]+)"', root)
    found = []

    for prefix, module in prefixes:
        path = ROOT / "backend" / (module.replace(".", "/") + ".py")
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("#"):
                continue  # a commented-out route routes nothing
            match = re.search(
                r"(?:path|re_path|url)\(\s*[r]?['\"]([^'\"]*)['\"]\s*,\s*(?!include)"
                r"([A-Za-z_][\w.]*)",
                line,
            )
            if not match:
                continue
            route, view = match.group(1), match.group(2)
            if "<" in route or "(?P" in route or "\\" in route:
                continue  # takes path arguments; not a bare-body endpoint
            if route.startswith("^") or route.endswith("$"):
                # A regex route via url()/re_path(). Joining it to a prefix
                # yields a literal that matches nothing, so probing it would
                # test a 404 rather than the endpoint. Those are the account
                # apps -- authentication, not the project-scoped surface here.
                continue
            found.append(("/" + prefix + route, view))
    return found


def test_the_routing_table_is_readable():
    """If this stops finding routes, the rest of this file proves nothing."""
    routes = _routes()
    assert len(routes) > 50, (
        "only %d routes resolved from the URL configuration; the parser has "
        "drifted from how routes are declared and this suite would silently "
        "stop checking them" % len(routes)
    )
    paths = {p for p, _ in routes}
    for expected in ("/compai/analysisstatus", "/contentmanager/list", "/dashservice"):
        assert expected in paths, "%s not found by the route parser" % expected


def test_no_endpoint_answers_a_missing_field_with_a_server_error(api, headers, auth):
    """The requirement, applied to every route rather than to the ones somebody
    remembered to check."""
    user_id = auth[0]
    offenders = []

    for path, view in sorted(set(_routes())):
        if path in EXCLUDED:
            continue
        try:
            # `userid` only: whatever else the endpoint requires is absent,
            # which is exactly the shape a brand-new account with no project
            # sends.
            response = requests.post(
                api + path,
                json={"userid": user_id},
                headers=headers,
                timeout=TIMEOUT,
            )
        except requests.RequestException as error:
            offenders.append("%s (%s): request failed: %s" % (path, view, error))
            continue

        if response.status_code >= 500:
            offenders.append(
                "%s (%s): %d" % (path, view, response.status_code)
            )

    assert not offenders, (
        "%d routed endpoint(s) raise an unhandled exception when a required "
        "field is absent:\n\n    %s\n\n"
        "api-request-validation forbids this: a client mistake must not consume "
        "a worker to render a server error. The fix is central -- see "
        "glassend.views.custom_exception_handler -- not per view."
        % (len(offenders), "\n    ".join(offenders))
    )


def test_excluded_routes_still_exist():
    """A stale exclusion silently stops checking an endpoint that is still live."""
    paths = {p for p, _ in _routes()}
    missing = [p for p in EXCLUDED if p not in paths]
    assert not missing, (
        "EXCLUDED names route(s) that no longer exist: %s. Remove the entry, or "
        "it starts excusing something that is not there." % missing
    )
