"""Small error-page handlers used by the Django project.

The former module also proxied cached Google HTML from a retired external
server. DataBlue supplies structured SERP data, not raw HTML archives, so that
public proxy surface has been removed.
"""

import logging

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _missing_field(exc):
    """The field name a KeyError is complaining about, or None."""
    if not isinstance(exc, KeyError) or not exc.args:
        return None
    name = exc.args[0]
    return name if isinstance(name, str) and name else None


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # DRF answers None for anything it does not recognise, and the caller
        # then renders a 500. A KeyError raised reading a request field is a
        # CLIENT mistake, not a server fault: views here read
        # `request.data["grpid"]` directly in 508 places across 21 files, so a
        # request that omits a field -- which is exactly what a brand-new
        # account with no project sends -- consumed a worker to render a 500 on
        # 70 routed endpoints.
        #
        # Handling it here binds every view, including ones not yet written.
        # See openspec api-request-validation: the guarantee must hold for the
        # routing table, not for the views somebody remembered to guard.
        field = _missing_field(exc)
        if field is not None:
            view = getattr(context.get("view"), "__class__", None) if isinstance(context, dict) else None
            view_name = getattr(view, "__name__", None) or str(context.get("view")) if isinstance(context, dict) else "unknown"
            # A KeyError raised deeper in a view by a real bug would also land
            # here and be reported as a client error. That is the accepted
            # trade-off for not editing 508 call sites -- so every one of these
            # is logged with the view, and a misclassification shows up in the
            # log rather than disappearing.
            logger.warning(
                "missing request field %r in %s -- answered 400", field, view_name
            )
            return Response(
                {
                    "status": "false",
                    "message": "Missing required field: %s" % field,
                    "status_code": 400,
                },
                status=400,
            )
        return response

    response.data["status_code"] = response.status_code
    if response.status_code == 401:
        request = context.get("request") if isinstance(context, dict) else None
        if request is not None:
            return render(request, "error.html", {"data": "Access Denied"}, status=401)
    return response


def handler404(request, *args, **kwargs):
    return render(
        request,
        "error.html",
        {"data": "Page not found", "code": "404"},
        status=404,
    )


def handler500(request, *args, **kwargs):
    return render(
        request,
        "error.html",
        {"data": "Bad Request", "code": "500"},
        status=500,
    )
