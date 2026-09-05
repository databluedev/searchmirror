"""Resolve the caller's credential to an account, once per request.

The same `Authorization: Token ...` was being resolved three separate times on
its way through a single request:

    account/ownership.py       middleware, before the view
    account/authentication.py  DRF, inside dispatch
    account/verify.py          inside many view bodies

Each issued its own `authtoken_token` read. Under djongo a query costs ~6ms of
pure-Python SQL translation whatever it selects, so that was 12-18ms on EVERY
authenticated endpoint in the product, spent re-answering a question that
cannot change within one request.

WHY THIS IS SAFE, and why each property is deliberate. Ownership is enforced
from this identity -- 56 views once had none -- so a shortcut here is a
security decision, not a performance one.

  * It lives on the REQUEST OBJECT. Its lifetime is one request by
    construction; nothing has to remember to expire it, and a revoked token is
    refused by the very next request.

  * It is KEYED BY THE CREDENTIAL the request actually presented. A stored
    answer is only ever returned to the same credential string it was derived
    from, so it cannot be handed to a different caller even if a request object
    were somehow reused.

  * A MISS STORES NOTHING. An unresolvable credential is re-resolved every time
    and refused by each caller exactly as before, so a failure can never be
    cached into a success.

Deliberately NOT a process-level or Redis cache. That would outlive the
request, which means revoking a token would not take effect until it expired --
turning an authorization decision into a cache-invalidation problem. The
measured win does not need it.

The resolution returns BOTH the owning account and the team member: a member
authenticates as the owner (rows are keyed by the owner's userid) while
`request.auth` stays the TeamAccount, and authorization tells them apart.
Collapsing the pair would lose that distinction.
"""

from django.core.exceptions import ValidationError

# Attribute name on the request. Leading underscore: this is ours, not part of
# any framework's contract.
_CACHE_ATTR = "_searchmirror_identity"


def credential_from(request):
    """The token string this request presents, or "" if it presents none."""
    header = request.META.get("HTTP_AUTHORIZATION") or ""
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "token":
        return ""
    return parts[1]


def _resolve(key):
    """``(owner id, team member or None)`` for one credential. No caching."""
    from rest_framework.authtoken.models import Token

    token = Token.objects.select_related("user").filter(key=key).first()
    if token is not None:
        return token.user_id, None, token

    from team_management.models import TeamAccount

    try:
        member = TeamAccount.objects.select_related("fk_user").filter(token=key).first()
    except (ValueError, ValidationError):
        # A non-UUID string is not a team token; that is a miss, not an error.
        member = None
    if member is not None:
        return member.fk_user_id, member, member
    return None, None, None


def caller_identity(request):
    """``(owner id, team member or None)`` for this request's credential.

    Resolved once and shared; see the module docstring for why that is safe.
    """
    owner, member, _auth = resolve_request(request)
    return owner, member


def caller_auth(request):
    """The credential object itself -- the Token row or the TeamAccount.

    DRF needs this for `request.auth`; the ownership middleware does not.
    """
    return resolve_request(request)[2]


def resolve_request(request):
    """``(owner id, team member or None, credential object or None)``.

    Every caller goes through here. The first one to ask pays for the lookup;
    the rest read what it found.
    """
    key = credential_from(request)
    if not key:
        return None, None, None

    cached = getattr(request, _CACHE_ATTR, None)
    # The key check is the whole safety property: a stored answer is only
    # returned to the credential it was derived from.
    if cached is not None and cached[0] == key:
        return cached[1], cached[2], cached[3]

    owner, member, auth = _resolve(key)

    # A miss is not stored. Re-resolving an unresolvable credential costs one
    # query on a request that is about to be refused anyway, and storing it
    # would be storing a failure.
    if owner is not None:
        try:
            setattr(request, _CACHE_ATTR, (key, owner, member, auth))
        except (AttributeError, TypeError):
            # Some request-like objects refuse attributes. Correctness does not
            # depend on the cache, only speed does.
            pass

    return owner, member, auth
