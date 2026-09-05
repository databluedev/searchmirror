from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from account.api.serializers import RegistrationSerializer, ChangePasswordSerializer
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
#password update
from rest_framework.generics import UpdateAPIView
from rest_framework.views import APIView
from serp.tracker import userTrackerRequest
from serp.models import Mailrecords, Accountusage, Roles, Userregistrationtoken
from shared.keycrypto import encrypt_key, decrypt_key, mask_key
from account.aikeys import (PROVIDERS, stored_key, store_key,
                            stored_model, store_model, MODEL_OPTIONS,
                            instance_fallback_allowed)
from account.capabilities import capabilities
from account.authentication import OwnerOrTeamTokenAuthentication
from account.models import Account
from team_management.models import TeamAccount, TeamProject
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import date,datetime,timedelta
from django.utils import timezone
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

@csrf_exempt
@api_view(['POST', ])
@permission_classes((AllowAny,))
def registration_view(request):

    if request.method == 'POST':
        email = (request.data.get("email") or "").strip().lower()
        registration_token = (request.data.get("userregtoken") or "").strip()
        valid_after = timezone.now() - timedelta(minutes=60)

        with transaction.atomic():
            registration = Userregistrationtoken.objects.select_for_update().filter(
                email__iexact=email,
                reg_key=registration_token,
                created_date__gte=valid_after,
            ).first()
            if registration is None:
                return Response(
                    {
                        "status": "false",
                        "message": "Verify your email with a current signup link before registering.",
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            serializer = RegistrationSerializer(data=request.data)
            data = {}
            if serializer.is_valid():
                account = serializer.save()
                registration.delete()

                data['status'] = 'true'
                data['message'] = 'Registered successfully'
                data['email'] = account.email
                data['username'] = account.username
                data['id'] = account.id
                token = Token.objects.get_or_create(user=account)[0].key
                data['token'] = token
            else:
                data['status'] = 'false'
                data['message'] = serializer.errors
            return Response(data)
        
        
        
@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'status':'false','message': 'Please provide both username and password'}, 
                        status=HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if not user:
        member = TeamAccount.objects.select_related("fk_user").filter(
            email__iexact=username
        ).first()
        if member and member.check_password(password):
            role = Roles.objects.filter(
                id=member.role_id, fk_user_id=member.fk_user_id
            ).first()
            projects = list(
                TeamProject.objects.filter(
                    client_id=member.id, fk_user_id=member.fk_user_id
                ).values_list("group", flat=True)
            )
            return Response(
                {
                    "status": "true",
                    "message": "Logged in successfully",
                    "id": member.fk_user_id,
                    "token": str(member.token),
                    "username": member.name,
                    "email": member.email,
                    "account_type": "team",
                    "role": member.role,
                    "role_id": member.role_id,
                    "modules": role.modules if role else {},
                    "projects": projects,
                },
                status=HTTP_200_OK,
            )

        account_exists = Account.objects.filter(email__iexact=username).exists()
        message = "Invalid Credentials" if account_exists or member else "No SearchMirror account exists for this email."
        return Response(
            {"status": "false", "email": username, "message": message},
            status=HTTP_404_NOT_FOUND,
        )

    lastloginupdate = Account.objects.filter(email=username).first()
    if lastloginupdate is None:
        return Response({'status':'false','message': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    lastloginupdate.last_login = timezone.now()
    lastloginupdate.account_status="normal"
    lastloginupdate.normal_mode="enable"
    lastloginupdate.save()
    userTrackerRequest(request, lastloginupdate.id)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'status':'true','message':'Loggedin Successfully','id': token.user_id, 'token': token.key,'username':user.username,'email':user.email},
                    status=HTTP_200_OK)
                    

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def Glogin(request):
    username = request.data.get("email")
    name = request.data.get("name")
    googleId = request.data.get("googleId")
    #new fields
    campaign = request.data.get("campaign")
    medium = request.data.get("medium")
    source = request.data.get("source")
    referral = request.data.get("referral")
    #new fields
    if username is None or googleId is None:
        return Response({'status':'false','message': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    accdata = Account.objects.filter(email=username).count()
    user = Account.objects.filter(email=username).first()
    if accdata == 0:
        account = Account()
        account.email=username
        account.username=name
        account.google_id=str(googleId)
        account.account_status="social"
        account.normal_mode="disable"
        account.social_mode="google"
        account.last_login = datetime.now()
        account.last_logout = datetime.now()
        #new fields
        account.campaign=campaign
        account.medium=medium
        account.source=source
        account.referral=referral
        #new fields
        account.save()
        mailIns = Mailrecords.objects.filter(userid=0,types="google_login").first()
        if mailIns == None:
            maildata = Mailrecords()
            maildata.userid = 0
            maildata.types = "google_login"
            maildata.mail_list = [username]
            maildata.save()
        elif username not in mailIns.mail_list:
            mailIns.mail_list = mailIns.mail_list + [username]
            mailIns.save(update_fields=['mail_list'])
        data = {}
        data['status'] = 'true'
        data['type'] = 'newaccount'
        data['message'] = 'Registered successfully'
        data['email'] = account.email
        data['username'] = account.username
        data['id'] = account.id
        userTrackerRequest(request, account.id)
        token = Token.objects.get_or_create(user=account)[0].key
        data['token'] = token
        
        return Response(data)        
    else:                   
        if not user:
            return Response({'status':'false','message': 'Invalid Credentials'},
                            status=HTTP_404_NOT_FOUND)
        lastloginupdate = Account.objects.filter(email=username).first()
        if lastloginupdate is None:
            return Response({'status':'false','message': 'Invalid Credentials'},
                            status=HTTP_404_NOT_FOUND)
        lastloginupdate.google_id = googleId
        lastloginupdate.account_status="social"
        lastloginupdate.social_mode="google"
        lastloginupdate.last_login = datetime.now()
        lastloginupdate.save()
        userTrackerRequest(request, lastloginupdate.id)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'status':'true','type':'login','message':'Loggedin Successfully','id': token.user_id, 'token': token.key,'username':user.username,'email':user.email},
                        status=HTTP_200_OK)

                   
class ChangePasswordView(UpdateAPIView):

    serializer_class = ChangePasswordSerializer
    model = Account
    # get_object() returns request.user, which is the OWNER Account even when a
    # client is calling -- so a client must be refused here, not merely 401'd
    # for presenting a key TokenAuthentication cannot read. Accepting the
    # client key and then denying it is what turns that into an honest 403.
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            account_type = serializer.data.get("old_password")
            print(account_type)
            if account_type != "-":
                if not self.object.check_password(serializer.data.get("old_password")):  
                    return Response({"status":"false","message": "Old password is wrong"}, status=status.HTTP_200_OK)

            # confirm the new passwords match
            new_password = serializer.data.get("new_password")
            old_password = serializer.data.get("old_password")
            confirm_new_password = serializer.data.get("confirm_new_password")
            
            if new_password == old_password:
                return Response({"status":"false","message": "New password same as old. Try for different one"}, status=status.HTTP_200_OK)
            elif new_password != confirm_new_password:
                return Response({"status":"false","message": "New password must match with confirm password"}, status=status.HTTP_200_OK)

            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.normal_mode="enable"
            self.object.save()
            return Response({"status":"true","message":"Successfully changed password"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def serviceauthenticate(request):
    return Response({'status':'true','message':'Response Successfully'},status=HTTP_200_OK)


# ---------------------------------------------------------------------------
# BYOK - per-account SERP provider key
# ---------------------------------------------------------------------------
# Validation and the balance readout both come from here. The provider
# documents this endpoint as "not charged": it consumes no credits and writes
# no billing record. Validation used to run a real google/serp query instead,
# which proved the key worked by spending the user's money every single time
# they saved it.
SERP_USAGE_URL = "https://api.datablue.dev/v1/usage/summary"


def _serp_usage(api_key):
    """Ask the provider who this key belongs to and what it has left.

    Returns (ok, message, summary). `summary` is the parsed usage body on
    success and None otherwise. Never logs or echoes the key itself.
    """
    import requests

    try:
        response = requests.get(
            SERP_USAGE_URL,
            headers={"Authorization": "Bearer %s" % api_key},
            timeout=30,
        )
    except Exception as exc:
        return False, "Could not reach the SERP provider: %s" % type(exc).__name__, None

    if response.status_code in (401, 403):
        return False, "The SERP provider rejected this key", None
    if response.status_code != HTTP_200_OK:
        return False, "SERP provider returned HTTP %s" % response.status_code, None

    try:
        return True, "Key validated", response.json()
    except ValueError:
        return False, "SERP provider returned a response we could not read", None


def _balance(summary):
    """The few numbers worth putting on screen, or None if we have no summary.

    Unlimited plans report null for the finite figures, so `unlimited` is
    carried through rather than rendering a blank where a number belongs.
    """
    if not isinstance(summary, dict):
        return None

    credits = summary.get("credits") or {}
    plan = summary.get("plan") or {}

    return {
        "plan": plan.get("name") or "",
        "unlimited": bool(credits.get("unlimited")),
        "remaining": credits.get("remaining"),
        "included": credits.get("included"),
        "used": credits.get("used"),
        "topup_balance": credits.get("payg_balance"),
        "total_available": credits.get("total_available"),
        "as_of": summary.get("as_of") or "",
    }


class SerpKeyView(APIView):
    """GET    -> the caller's stored key, MASKED.
    POST   -> validate a raw key against the provider, then store it encrypted.
    PATCH  -> change serp_depth alone, without re-sending the key.
    DELETE -> revoke the stored key.
    """

    # Owner-only, like everything else: the account holder is the only
    # principal that exists.
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get(self, request):
        usage = Accountusage.objects.filter(fb_user_id=request.user.id).first()
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)

        try:
            plain = decrypt_key(usage.serp_key)
        except Exception:
            # Stored token is unreadable (wrong/rotated SERP_KEY_SECRET).
            return Response({"status": "false", "message": "Stored key could not be read. Please save it again."},
                            status=HTTP_200_OK)

        # The balance is a live read, and a provider outage must not take the
        # settings page down with it -- a missing balance renders as "unknown",
        # a broken page renders as nothing.
        balance = None
        if plain:
            ok, _msg, summary = _serp_usage(plain)
            if ok:
                balance = _balance(summary)

        return Response({
            "status": "true",
            "message": "Response Successfully",
            "serp_provider": usage.serp_provider,
            "serp_depth": usage.serp_depth,
            "serp_key": mask_key(plain),
            "has_key": "true" if plain else "false",
            "balance": balance,
        }, status=HTTP_200_OK)

    def post(self, request):
        usage = Accountusage.objects.filter(fb_user_id=request.user.id).first()
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)

        api_key = (request.data.get("serp_key") or "").strip()
        if not api_key:
            return Response({"status": "false", "message": "Please provide serp_key"},
                            status=HTTP_400_BAD_REQUEST)

        provider = (request.data.get("serp_provider") or usage.serp_provider or "datablue").strip()
        if provider != "datablue":
            return Response({"status": "false", "message": "Unsupported serp_provider: %s" % provider},
                            status=HTTP_400_BAD_REQUEST)

        try:
            depth = int(request.data.get("serp_depth", usage.serp_depth))
        except (TypeError, ValueError):
            return Response({"status": "false", "message": "serp_depth must be a whole number"},
                            status=HTTP_400_BAD_REQUEST)
        if depth < 1 or depth > 10:
            return Response({"status": "false", "message": "serp_depth must be between 1 and 10"},
                            status=HTTP_400_BAD_REQUEST)

        valid, message, summary = _serp_usage(api_key)
        if not valid:
            return Response({"status": "false", "message": message}, status=HTTP_200_OK)

        usage.serp_provider = provider
        usage.serp_depth = depth
        usage.serp_key = encrypt_key(api_key)
        usage.save()

        return Response({
            "status": "true",
            "message": message,
            "serp_provider": usage.serp_provider,
            "serp_depth": usage.serp_depth,
            "serp_key": mask_key(api_key),
            "has_key": "true",
            "balance": _balance(summary),
        }, status=HTTP_200_OK)

    def patch(self, request):
        """Change how many result pages a rank check pulls, and nothing else.

        POST requires a raw serp_key, so before this existed the only way to
        change depth was to delete the key and re-enter it -- which spends a
        live validation request and forces the user to hold their key again to
        edit an unrelated preference. The settings page consequently rendered
        depth as read-only text once a key was stored, so the setting that
        decides whether a rank beyond page 1 is visible at all could be set
        exactly once, at key-entry time.

        Deliberately does NOT call the provider: depth is a local preference,
        and validating a key the user did not touch would spend a credit to
        answer a question nobody asked.
        """
        usage = Accountusage.objects.filter(fb_user_id=request.user.id).first()
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)

        if "serp_depth" not in request.data:
            return Response({"status": "false", "message": "Please provide serp_depth"},
                            status=HTTP_400_BAD_REQUEST)

        try:
            depth = int(request.data.get("serp_depth"))
        except (TypeError, ValueError):
            return Response({"status": "false", "message": "serp_depth must be a whole number"},
                            status=HTTP_400_BAD_REQUEST)
        if depth < 1 or depth > 10:
            return Response({"status": "false", "message": "serp_depth must be between 1 and 10"},
                            status=HTTP_400_BAD_REQUEST)

        usage.serp_depth = depth
        usage.save()

        # Echo the stored key's mask so the caller can re-render without a
        # second GET. An unreadable token is not this endpoint's problem --
        # depth was still saved -- so it degrades to "no key" rather than
        # failing the update.
        try:
            plain = decrypt_key(usage.serp_key)
        except Exception:
            plain = ""

        return Response({
            "status": "true",
            "message": "Pages per keyword updated",
            "serp_provider": usage.serp_provider,
            "serp_depth": usage.serp_depth,
            "serp_key": mask_key(plain),
            "has_key": "true" if plain else "false",
        }, status=HTTP_200_OK)

    def delete(self, request):
        """Revoke the stored key.

        Blanks serp_key only -- serp_provider and serp_depth are left intact
        so a user who re-enters a key keeps their depth preference.

        Idempotent: deleting when nothing is stored still reports success,
        because the caller's desired end state (no key) is what they get.
        """
        usage = Accountusage.objects.filter(fb_user_id=request.user.id).first()
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)

        usage.serp_key = ""
        usage.save()

        return Response({
            "status": "true",
            "message": "Key removed",
            "serp_provider": usage.serp_provider,
            "serp_depth": usage.serp_depth,
            "serp_key": "",
            "has_key": "false",
        }, status=HTTP_200_OK)


# ---------------------------------------------------------------------------
# BYOK - per-account AI provider keys (Geo Citations)
# ---------------------------------------------------------------------------
class AiKeysView(APIView):
    """GET    -> which providers this account has a key for, all MASKED.
    POST   -> store one provider's key, encrypted.
    DELETE -> revoke one provider's key.

    Deliberately no live validation call, unlike SerpKeyView: verifying an LLM
    key costs a completion on the user's own account for every save. The first
    real run surfaces a bad key instead.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def _usage(self, request):
        return Accountusage.objects.filter(fb_user_id=request.user.id).first()

    def get(self, request):
        usage = self._usage(request)
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)
        providers = {}
        for slug in PROVIDERS:
            plain = stored_key(usage, slug)
            providers[slug] = {"has_key": "true" if plain else "false",
                               "key": mask_key(plain) if plain else "",
                               "model": stored_model(usage, slug),
                               "model_options": MODEL_OPTIONS.get(slug, [])}
        return Response({
            "status": "true",
            "message": "Response Successfully",
            "providers": providers,
            "instance_fallback": "true" if instance_fallback_allowed() else "false",
        }, status=HTTP_200_OK)

    def post(self, request):
        usage = self._usage(request)
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)

        provider = (request.data.get("provider") or "").strip().lower()
        if provider not in PROVIDERS:
            return Response({"status": "false",
                             "message": "Unknown provider. Expected one of: %s" % ", ".join(sorted(PROVIDERS))},
                            status=HTTP_400_BAD_REQUEST)

        api_key = (request.data.get("api_key") or "").strip()
        # `model` is optional and can be sent alone to change the model without
        # re-entering the key. Empty string clears the override (use default).
        has_model = "model" in request.data
        if not api_key and not has_model:
            return Response({"status": "false", "message": "Please provide api_key or model"},
                            status=HTTP_400_BAD_REQUEST)

        changed = []
        if api_key:
            changed.append(store_key(usage, provider, api_key))
        if has_model:
            changed.append(store_model(usage, provider, request.data.get("model") or ""))
        usage.save(update_fields=changed)
        resp = {"status": "true", "message": "Saved", "provider": provider,
                "model": stored_model(usage, provider)}
        if api_key:
            resp.update({"key": mask_key(api_key), "has_key": "true"})
        return Response(resp, status=HTTP_200_OK)

    def delete(self, request):
        usage = self._usage(request)
        if not usage:
            return Response({"status": "false", "message": "No account usage record found"},
                            status=HTTP_404_NOT_FOUND)
        provider = (request.data.get("provider") or "").strip().lower()
        if provider not in PROVIDERS:
            return Response({"status": "false", "message": "Unknown provider"},
                            status=HTTP_400_BAD_REQUEST)
        field = store_key(usage, provider, "")
        usage.save(update_fields=[field])
        return Response({"status": "true", "message": "Key removed",
                         "provider": provider, "has_key": "false"}, status=HTTP_200_OK)


# ---------------------------------------------------------------------------
# What this instance can actually do
# ---------------------------------------------------------------------------
class CapabilitiesView(APIView):
    """Which features are usable, and what is missing when they are not.

    Readable by a client account as well as an owner: a client sees the same
    locked features and needs the same explanation for why a table is empty.
    It exposes no key material -- only booleans and prose.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (OwnerOrTeamTokenAuthentication,)

    def get(self, request):
        usage = Accountusage.objects.filter(fb_user_id=request.user.id).first()
        return Response({
            "status": "true",
            "message": "Response Successfully",
            "capabilities": capabilities(usage),
        }, status=HTTP_200_OK)
