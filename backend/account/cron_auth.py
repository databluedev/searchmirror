"""Shared-secret gate for the scheduler-only endpoints.

The Geo Citations scheduler picks up queued work and can spend configured AI
provider credits. It must never be an anonymous "spend the operator's money"
URL on an internet-facing instance.

@permission_classes alone does not protect them: it only sets an attribute DRF
reads, and DRF consults it only when @api_view wraps the view. A cron view that
carries @permission_classes but no @api_view is a plain public Django view no
matter what the decorator says. A check that lives INSIDE the view body cannot
be defeated that way, which is why this is a decorator over the function rather
than a DRF permission class.

Fails closed: with CRON_TOKEN unset there is no valid caller, so the endpoint
refuses everyone rather than falling back to open.
"""

import hmac
import os
from functools import wraps

from django.http import JsonResponse

_HEADER = "HTTP_X_CRON_TOKEN"


def cron_only(view):
    """Refuse anyone who cannot present the instance's CRON_TOKEN."""

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        expected = os.environ.get("CRON_TOKEN", "")
        if not expected:
            return JsonResponse(
                {"status": "false",
                 "message": "Scheduled processing is disabled: CRON_TOKEN is not set."},
                status=503,
            )
        supplied = request.META.get(_HEADER, "")
        # compare_digest, not ==: a plain comparison leaks the token a byte at a
        # time to anyone who can measure the response.
        if not supplied or not hmac.compare_digest(str(supplied), str(expected)):
            return JsonResponse(
                {"status": "false", "message": "Not authorised."}, status=403
            )
        return view(request, *args, **kwargs)

    return _wrapped
