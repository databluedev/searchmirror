from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from django.http import HttpResponse, JsonResponse
from serp.models import *
from account.models import Account
from mailend.models import KeywordHistory
from serp.serializers import *
from serp.common import *
from shared.scoring import calculate_visibility_history
import string, random
from django.conf import settings

# from urllib.parse import urlparse
from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.db.models import Q

# from django_cron import CronJobBase, Schedule
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
import csv, os
from io import StringIO

# from easy_pdf.rendering import render_to_pdf
from weasyprint import HTML
from serp import calculation, views as serp_views
from account import verify as authPermission
from rest_framework.permissions import IsAuthenticated


def pre_update_1():
    default_switch = {"DS": True, "URL": True, "FS": True, "ADS": True, "RS": True, "CNN": True, "NIMP": True, "SSA": True}
    Groups.objects.filter(id__gt=0).update(automation_email_switch=default_switch, automation_email_recipients=[])
    return JsonResponse({"status": "true"})


@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def prjtoverview_change(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        grpid = str(request.data["grpid"])
        view = request.data["view"]
        if userid.isdigit() and (view == True or view == False):
            #     return Response({'status':'false','message':""})

            dashview = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(overview_switch=view)
            return Response({"status": "true", "message": "Project overview changes updated"})

    return Response({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def prjtoverview(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        # .get(): see getsetting -- a no-project screen omits grpid entirely,
        # and the literal subscript made that an unhandled 500.
        userid = str(request.data.get("userid") or "")
        grpid = str(request.data.get("grpid") or "")
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():

                superData = {}
                grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                if grpData:
                    superData = {"pD": 0, "pM": 0, "ik": 0, "dk": 0, "nk": 0, "tR": {"1": 0, "3": 0, "10": 0, "50": 0, "100": 0, "nr": 0}, "yR": {"1": 0, "3": 0, "10": 0, "50": 0, "100": 0, "nr": 0}, "bR": {"1": 0, "3": 0, "10": 0, "50": 0, "100": 0, "nr": 0}, "R2": 0, "R4": 0, "R5": 0, "So": 0, "Sp": 0, "Ay": {"Atb": 0, "At": 0, "Ab": 0, "Au": 0}, "Ao": {"Atb": 0, "At": 0, "Ab": 0, "Au": 0}}
                    kwIns = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
                    superData = ProjectOverviewSerializer(kwIns, many=True, context=superData).data[-1:][0]
                    # serializer_data = list(filter(None, serializer))
                    # Fourth surface for the same number. Recomputed from the
                    # keyword rank arrays for the same reason /homeauth and
                    # /erocs_wdt are -- the stored Groups.score_meter snapshot
                    # only moves when a ranking run writes it, so between runs
                    # this panel disagreed with the dashboard beside it.
                    keyword_rank_histories = list(
                        Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).values_list("rank", flat=True)
                    )
                    score_history = calculate_visibility_history(keyword_rank_histories)
                    # Measurement count -- see serializers.py. Same name as
                    # /erocs_wdt's dt.t_c and /homeauth's t_c.
                    #
                    # NOTE: this surface's day-one fallback differs from
                    # /homeauth's. Here yss falls back to 0 ("yesterday was
                    # zero"); there it falls back to ss ("yesterday was the
                    # same"). Both are inherited and both are guesses about a
                    # day that was never measured, so they are left as they
                    # are rather than silently picking a winner -- t_c is what
                    # lets the frontend stop rendering either claim.
                    superData["t_c"] = len(score_history)
                    superData["ss"] = f_to_i(score_history[0]) if len(score_history) > 0 else 0
                    superData["yss"] = f_to_i(score_history[1]) if len(score_history) > 1 else 0
                    # Same source as ss/yss above -- see serializers.py. This
                    # surface's "no history" sentinel is 0, not -1; kept as it
                    # was, only the value's source changes.
                    superData["bss"] = f_to_i(max(score_history)) if len(score_history) > 0 else 0
                    activityGroupData = list(map(str, grpData.activity_level[1].split("|"))) if len(grpData.activity_level) > 1 else [0, 0, 0]
                    if len(activityGroupData) == 3:
                        superData["yik"] = int(activityGroupData[1])
                        superData["ydk"] = int(activityGroupData[2])
                    else:
                        superData["yik"] = 0
                        superData["ydk"] = 0

                    # superData['pD'] = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, platform = "desktop").count()
                    # superData['pM'] = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, platform = "mobile").count()

                    # superData['ik'] = Keyword.objects.filter(fk_group_id=grpData.id, daymark="up").count()
                    # superData['dk'] = Keyword.objects.filter(fk_group_id=grpData.id, daymark="down").count()
                    # superData['nk'] = Keyword.objects.filter(fk_group_id=grpData.id, daymark="-").count()

                    return JsonResponse({"status": "true", "data": superData})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def projectdetails(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).all()
                if grpData:
                    AccIns = Account.objects.filter(id=userid).first()
                    user_mail = AccIns.email if AccIns else ""
                    serializer = ProjectSettingSerializer(grpData, many=True).data[0]
                    if "logid" in request.POST:
                        localuserid = request.POST["logid"]
                        serp_views.exitlast(localuserid, "demo-project-settings")
                    else:
                        serp_views.exitlast(userid, "project-settings")
                    return JsonResponse({"status": "true", "data": serializer, "RgM": user_mail})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def recipientmailupdate(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        grpid = str(request.data["grpid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                if "rp_m" in request.data:
                    recipients = list(request.data["rp_m"])
                    recipients_mail = list(filter(None, recipients))
                    group = Groups.objects.filter(fk_user_id=userid, id=grpid).update(automation_email_recipients=recipients_mail)
                    if group:
                        return JsonResponse({"status": "true", "message": "Mail updated successfully", "rp_m": recipients_mail})
                    else:
                        return JsonResponse({"status": "false", "message": "Something went wrong"})
                else:
                    grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                    if grpData is None:
                        return JsonResponse({"status": "false", "message": "Project not found"})
                    # Never blank this on a permission flag -- returning [] destroys
                    # visible state rather than reporting a refusal.
                    recipient_mails = list(filter(None, grpData.automation_email_recipients))
                    return JsonResponse({"status": "true", "message": "Mail details", "rp_m": recipient_mails})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def mailoptionswupdate(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                if "UpSw" in request.data:
                    # email_switch = json.loads(request.data['UpSw'])
                    email_switch = request.data["UpSw"]
                    group = Groups.objects.filter(fk_user_id=userid, id=grpid).update(automation_email_switch=email_switch)
                    if group:
                        return JsonResponse({"status": "true", "message": "Mail updated successfully"})
                else:
                    grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                    if grpData is None:
                        return Response({"status": "false", "message": "Project not found"})
                    return Response({"status": "true", "OptSw": grpData.automation_email_switch})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def brandadcreate(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                bname = request.POST["bn"]
                region = request.POST["region"]
                isocode = request.POST["isocode"]

                # brandIns = brandTracker()
                # brandIns.fb_user_id = userid
                # brandIns.fb_group_id = grpid
                # brandIns.brand_name = bname
                # brandIns.region = region
                # brandIns.isocode = isocode
                # brandIns.status = "on"
                # brandIns.save()

                data = {"bid": brandIns.id, "bn": bname, "bs": "on"}
                return JsonResponse({"status": "true", "data": data, "message": "Your brand create successfully"})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def brandadswupdate(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                brand_id = request.POST["bid"]
                brandswitch = request.POST["bsw"]
                # brandIns =  brandTracker.objects.filter(fb_user_id=userid, fb_group_id=grpid, id=brand_id).update(status=brandswitch)
                # if brandIns:
                #     return JsonResponse({'status':'true','message': "branding ad update successfully"})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def brandaddelete(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                brand_id = request.POST["bid"]
                # brandIns =  brandTracker.objects.get(id=brand_id)
                # if brandIns:
                #     brandIns.delete()
                #     return JsonResponse({'status':'true','message': "branding ad deleted successfully"})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def project_serp_mode(request):
    """Read or set one project's SERP extraction depth.

    POST without "adv" reads the current value; POST with "adv" sets it.

    Lite (False, the default) asks DataBlue for organic results plus the
    non-AI rich blocks -- ads, featured snippet, People Also Ask, local pack,
    knowledge panel, videos, related searches. Advanced (True) adds
    ai_overview, Google's AI answer, and nothing else.

    Advanced carries a higher DataBlue credit weight per request and is billed
    per keyword per scheduled run against the account's OWN key, so the cost is
    reported back on every read and write and the flag is never set implicitly.
    """
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        grpid = str(request.data["grpid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                if grpData is None:
                    return JsonResponse({"status": "false", "message": "Project not found"})

                if "adv" in request.data:
                    advanced = request.data["adv"]
                    # A checkbox arrives as the string "false" from form-encoded
                    # posts, and bool("false") is True -- which would silently
                    # move a project onto the more expensive depth.
                    if isinstance(advanced, str):
                        advanced = advanced.strip().lower() in ("1", "true", "yes", "on")
                    else:
                        advanced = bool(advanced)

                    Groups.objects.filter(fk_user_id=userid, id=grpid).update(serp_advanced=advanced)
                    return JsonResponse({
                        "status": "true",
                        "message": "Extraction depth updated",
                        "adv": advanced,
                    })

                return JsonResponse({"status": "true", "adv": bool(grpData.serp_advanced)})

    return JsonResponse({"status": "false", "message": "Something went wrong"})
