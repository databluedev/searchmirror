"""Read a required field off a request, or answer the client that it is missing.

There are 369 `request.data["..."]` reads across ten modules. Every one of them
raises KeyError when the field is absent, which Django renders as a 500 -- and
with DEBUG on, as a 94 KB page carrying the settings, the environment and a
source excerpt. `POST /dashservice` without `field` did exactly that.

A missing field is the caller's mistake. It should cost a 400 and a sentence,
not a server error and a worker's time.

Usage is a guard clause, so the view reads the same way it did:

    missing = missing_fields(request, "userid", "grpid", "field")
    if missing:
        return bad_request(missing)

`require_ids` is the second half of the same problem: `userid.isdigit()` guards
were written as `if ...:` with no else, so a non-numeric id fell through every
branch and returned a bare "Something went wrong" that named nothing.
"""

from django.http import JsonResponse


def missing_fields(request, *names):
    """Which of `names` the request did not supply usefully, in order.

    A field present but empty counts as missing: `{"userid": ""}` cannot
    identify an account, and reporting it as present only moves the failure
    somewhere less obvious.
    """
    data = getattr(request, "data", None)
    if data is None:
        data = request.POST if request.method == "POST" else request.GET

    absent = []
    for name in names:
        try:
            value = data[name]
        except (KeyError, TypeError):
            absent.append(name)
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            absent.append(name)
    return absent


def bad_request(names):
    """400 naming what was missing. Never a traceback, whatever DEBUG says."""
    if isinstance(names, str):
        names = [names]
    listed = ", ".join(names)
    return JsonResponse(
        {
            "status": "false",
            "message": "Missing required field%s: %s" % ("" if len(names) == 1 else "s", listed),
            "missing": list(names),
        },
        status=400,
    )


def invalid_request(name, reason="is not a valid identifier"):
    """400 naming the value that was rejected and why."""
    return JsonResponse(
        {"status": "false", "message": "%s %s." % (name, reason), "invalid": name},
        status=400,
    )


def require_ids(request, *names):
    """``(values, error)`` for fields that must be positive integers.

    Returns the values as strings -- the callers compare and filter on strings
    throughout -- or an error response naming the first field that was not a
    usable identifier. Exactly one of the two is ever meaningful.
    """
    absent = missing_fields(request, *names)
    if absent:
        return None, bad_request(absent)

    data = getattr(request, "data", None)
    if data is None:
        data = request.POST if request.method == "POST" else request.GET

    values = []
    for name in names:
        raw = str(data[name]).strip()
        if not raw.isdigit():
            return None, invalid_request(name)
        values.append(raw)
    return values, None
