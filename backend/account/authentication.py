"""Authenticate owner and team credentials without sharing owner tokens."""

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from team_management.models import TeamAccount


class OwnerOrTeamTokenAuthentication(BaseAuthentication):
    """Resolve ``Authorization: Token`` to an owner or one of their members.

    Team credentials deliberately authenticate as the owning Account because
    the legacy API keys every row by that owner's ``userid``. ``request.auth``
    remains the TeamAccount instance, allowing authorization code to tell a
    restricted member from the owner without ever issuing the owner's token.
    """

    keyword = "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise AuthenticationFailed(_("Invalid token header."))

        try:
            auth[1].decode()
        except UnicodeError:
            raise AuthenticationFailed(_("Invalid token header."))

        # Shared with the ownership middleware, which has already run by now,
        # and with verify.validate inside the view. One read instead of three;
        # account/identity.py explains why that is safe. The refusals below are
        # unchanged -- an unresolvable credential is never cached, so it is
        # re-resolved and refused exactly as before.
        from account.identity import resolve_request

        _owner, member, credential = resolve_request(request)

        if credential is None:
            raise AuthenticationFailed(_("Invalid token."))

        if member is None:
            # An owner token: `credential` is the Token row.
            if not credential.user.is_active:
                raise AuthenticationFailed(_("User inactive or deleted."))
            return credential.user, credential

        if not member.fk_user.is_active:
            raise AuthenticationFailed(_("User inactive or deleted."))
        return member.fk_user, member
