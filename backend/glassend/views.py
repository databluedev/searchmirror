"""Small error-page handlers used by the Django project.

The former module also proxied cached Google HTML from a retired external
server. DataBlue supplies structured SERP data, not raw HTML archives, so that
public proxy surface has been removed.
"""

from django.shortcuts import render
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
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
