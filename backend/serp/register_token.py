import logging
import random
import string
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from account.models import Account
from serp.common import mail_record_update, sendMail
from serp.models import Userregistrationtoken
from serp.serializers import UserregistrationtokenSerializer


logger = logging.getLogger(__name__)
TOKEN_LIFETIME = timedelta(minutes=60)


def _new_token():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=64))


def _delivery_message():
    if settings.EMAIL_DELIVERY_MODE == "console":
        return "SMTP is not configured, so we cannot email you. Continue below to set your password."
    return "User registration verification link sent to your email address"


def _console_mode():
    """True when the instance has no SMTP and therefore cannot verify by email.

    With no mail host the verification link only ever reached the container
    logs, so nobody could finish signing up without running `docker logs` --
    the first thing a self-hoster does is create an account, and it was
    impossible. Email verification is not "skipped" here; it is not available,
    and pretending it happened was the dishonest part.
    """
    return settings.EMAIL_DELIVERY_MODE == "console"


@api_view(["POST"])
@permission_classes((AllowAny,))
def user_reg_token(request):
    email = (request.data.get("email") or "").strip().lower()
    if not email:
        return Response({"status": "false", "message": "Please enter a valid email address"})
    if Account.objects.filter(email__iexact=email).exists():
        return Response({"status": "false", "message": "User account already exists"})

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:256]
    registration = Userregistrationtoken.objects.filter(email__iexact=email).first()
    token = _new_token()

    if registration:
        registration.email = email
        registration.reg_key = token
        registration.ip_address = ip_address
        registration.user_agent = user_agent
        registration.created_date = timezone.now()
        registration.save(update_fields=["email", "reg_key", "ip_address", "user_agent", "created_date"])
    else:
        serializer = UserregistrationtokenSerializer(
            data={
                "email": email,
                "reg_key": token,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )
        if not serializer.is_valid():
            return Response({"status": "false", "message": serializer.errors})
        registration = serializer.save()

    mail_record_update(0, email, "pre_register")
    context = {
        "email": email,
        "regurl": settings.SITE_URL + "/register/?userregtoken=" + registration.reg_key,
        "siteurl": settings.SITE_URL,
        "serivceurl": settings.SERVICE_URL,
    }
    try:
        delivered = sendMail(
            "email/newuserreg.html",
            context,
            "Email confirmation to complete the sign up process",
            [email],
        )
    except Exception:
        logger.exception("Registration email delivery failed")
        registration.delete()
        return Response({"status": "false", "message": "Verification email could not be delivered"})

    if not delivered:
        registration.delete()
        return Response({"status": "false", "message": "Verification email could not be delivered"})
    payload = {"status": "true", "message": _delivery_message()}
    if _console_mode():
        # Hand the link back so the browser can continue. Only ever populated
        # when the operator has configured no mail host, which is an explicit
        # instance state, not a per-request choice.
        payload["regurl"] = "/register/?userregtoken=" + registration.reg_key
        payload["verification"] = "unavailable"
    return Response(payload)


def user_reg_token_expiry():
    Userregistrationtoken.objects.filter(
        created_date__lte=timezone.now() - TOKEN_LIFETIME
    ).delete()
    return False


@api_view(["POST"])
@permission_classes((AllowAny,))
def user_regtoken_verify(request):
    token = (request.data.get("userregtoken") or "").strip()
    registration = Userregistrationtoken.objects.filter(
        reg_key=token,
        created_date__gte=timezone.now() - TOKEN_LIFETIME,
    ).first()
    if registration is None:
        return Response({"status": "false", "message": "user registration is invalid"})
    return Response(
        {
            "status": "true",
            "message": "user registration is valid",
            "email": registration.email,
        }
    )
