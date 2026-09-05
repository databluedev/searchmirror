"""Scheduled endpoints must never be reachable without the instance token.

Active jobs fail closed through @cron_only. Vendor, billing, and search-volume
jobs that are outside the supported product are absent entirely.

These assert only that the request is REFUSED. They deliberately never send a
valid token: passing one would run the job and spend the operator's credits,
which is not something a test suite should do.
"""

import pytest
import requests

from conftest import API, TIMEOUT

REFUSED = (401, 403, 503)

SCHEDULED = [
    "csv_report_mailer",
    "currency-update",
    "trial-expire",
    "report_schedule_emails",
    "spyglass/watchmail",
    "ga_daily_monitor",
    "ga_daily_scheduler",
    "ga_monthly_monitor",
    "ga_weekly_monitor",
    "ga_crawler",
    "ga_month_crawler",
    "ga_week_crawler",
]

RETIRED = [
    "release-pre-reset",
    "unwantsvkwremove",
    "failsvkwupdate",
    "newmonthupdate",
    "svmisskwupdate",
    "payment/payment-expire",
    "redeem/check",
]


@pytest.mark.parametrize("path", SCHEDULED)
def test_scheduled_endpoint_refuses_anonymous(path):
    r = requests.get(API + "/" + path, timeout=TIMEOUT)
    assert r.status_code in REFUSED, (
        "%s answered anonymously with HTTP %s; several of these spend the "
        "operator's provider credits." % (path, r.status_code)
    )


@pytest.mark.parametrize("path", RETIRED)
def test_retired_scheduled_endpoints_are_gone(path):
    r = requests.get(API + "/" + path, timeout=TIMEOUT)
    assert r.status_code == 404, "%s still routes (HTTP %s)" % (
        path, r.status_code
    )


@pytest.mark.parametrize("path", ["kcount", "test_project", "mailsystem/testing",
                                  "research/test"])
def test_debug_routes_are_gone(path):
    """Four debug leftovers were deleted rather than gated.

    kcount is the one worth remembering: it routed a HELPER that takes a
    userid, so Django passed it the request object and it answered 500 every
    time.
    """
    r = requests.get(API + "/" + path, timeout=TIMEOUT)
    assert r.status_code == 404, "%s still routes (HTTP %s)" % (path, r.status_code)
