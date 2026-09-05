import os
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from glassend.request_fields import bad_request, missing_fields, require_ids
from serp.engine_trigger import trigger_engine_manual
from serp.refresh_error import refresh_error_state
from django.http import HttpResponse, JsonResponse
from serp.models import *
from competitor.models import *
from account.models import Account
from mailend.models import KeywordHistory
from serp.serializers import *
from serp.common import *
import string, random
from django.conf import settings
from urllib.parse import urlencode, urlparse
from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.utils import timezone

# from django_cron import CronJobBase, Schedule
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
import csv, os
from io import StringIO

# from PIL import Image
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter, A4
# from easy_pdf.rendering import render_to_pdf
from weasyprint import HTML
from serp import calculation, tracker, user_timezone as uTZ
from account import verify as authPermission
from operator import itemgetter

from uuid import UUID

# import whois
import numpy
import validators

# NEW
from django.core.files.images import get_image_dimensions
import time
import magic
from django.core.files.storage import default_storage
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from team_management.models import TeamAccount, TeamProject

import logging

logger = logging.getLogger(__name__)

useragentlibery_gob = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
]
useragentrandomselect_gob = random.choice(useragentlibery_gob)

# Create your views here.

# ---------------------dashboard------------------------------

# @api_view(['POST'])
# def apphomeload(request):
#     if request.method == 'POST' and authPermission.validate(request, "POST"):
#         userid = request.POST['userid']
#         if userid.isdigit():
#             accdata = Account.objects.filter(id=userid).all()
#             if accdata:
#                 Account.objects.filter(id=userid).update(last_home_visit=datetime.now())
#                 serializer = AppHomeSerializer(accdata, many=True).data[0]
#                 # serializer = AppGroupSerializer(grps, many=True)
#                 return JsonResponse({'status':'true','data': serializer})

#     return JsonResponse({'status':'false','message':"Something went wrong"})


@api_view(["POST"])
def usageload(request):
    # BEFORE the entitlement check, not inside it. validate() returns
    # False for a missing or non-numeric userid, so a guard placed
    # inside never runs and the view falls through to the trailing
    # "Something went wrong" -- which answers HTTP 200. A malformed
    # request has to be told it was malformed.
    ids, error = require_ids(request, "userid")
    if error:
        return error
    userid = ids[0]
    if request.method == "POST" and authPermission.validate(request, "POST"):
        if userid.isdigit():
            serializer = {}
            accountData = Accountusage.objects.filter(fb_user_id=userid).first()
            serializer["luRc"] = accountData.last_used_refresh_count if accountData.last_used_refresh_count else 0
            serializer["pKL"] = accountData.plan_keyword_limit if accountData.plan_keyword_limit else 0
            serializer["pRL"] = accountData.plan_refresh_limit if accountData.plan_refresh_limit else 0
            # serializer['pPL'] = accountData.plan_project_limit if accountData.plan_project_limit else 0
            serializer["uRL"] = accountData.used_refresh_limit if accountData.used_refresh_limit else 0
            serializer["pCL"] = accountData.plan_competitor_limit if accountData.plan_competitor_limit else 1
            serializer["uCL"] = CompProject.objects.filter(fk_user_id=userid).count()
            # changed

            sts, cnt = totalKeywordsCount(userid)
            serializer["u_kw"] = cnt
            # serializer['u_kw'] = Keyword.objects.filter(fk_user_id=userid).count()

            return JsonResponse({"status": "true", "data": serializer})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def apphomeload(request):
    # BEFORE the entitlement check, not inside it. validate() returns
    # False for a missing or non-numeric userid, so a guard placed
    # inside never runs and the view falls through to the trailing
    # "Something went wrong" -- which answers HTTP 200. A malformed
    # request has to be told it was malformed.
    ids, error = require_ids(request, "userid")
    if error:
        return error
    userid = ids[0]
    if request.method == "POST" and authPermission.validate(request, "POST"):
        if userid.isdigit():
            accIns = Account.objects.filter(id=userid)
            accFst = accIns.first()
            if accFst:
                accdata = accIns.update(last_home_visit=timezone.now())
                logout = 1 if accFst and accFst.last_logout == None else 0
                # serializer = {}
                serializer = AppHomeSerializer([accFst], many=True).data[0]
                if isinstance(request.auth, TeamAccount):
                    allowed_projects = set(
                        TeamProject.objects.filter(
                            fk_user_id=userid,
                            client_id=request.auth.id,
                        ).values_list("group", flat=True)
                    )
                    serializer["slt"] = [
                        project
                        for project in serializer.get("slt", [])
                        if project.get("GY") in allowed_projects
                    ]
                    serializer["uPL"] = len(serializer["slt"])
                    serializer["ac_typ"] = "team"
                    role = Roles.objects.filter(
                        id=request.auth.role_id,
                        fk_user_id=userid,
                    ).first()
                    serializer["team_modules"] = role.modules if role else {}
                # UserSttgdata = Usersettings.objects.filter(fb_user_id=userid).first()
                #     serializer['dmdata'] = AppGroupSerializer(demogrpData, many=True).data
                return JsonResponse({"status": "true", "data": serializer, "lg": logout})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def homeload(request):
    ids, error = require_ids(request, "userid")
    if error:
        return error
    userid = ids[0]
    if request.method == "POST" and authPermission.validate(request, "POST"):
        if userid:

            if userid.isdigit():

                # REQUEST TRACKER UPDATE - STARTS
                # reqFlag = 0
                # if int(userid) == 1 and "logid" in request.POST:
                #     if request.POST['logid'].isdigit():
                #         tracker.userTrackerRequest(request, request.POST['logid'])
                #         reqFlag = 1

                # if reqFlag == 0:
                # tracker.userTrackerRequest(request, userid)

                tracker.userTrackerRequest(request, userid)
                # REQUEST TRACKER UPDATE - ENDS
                UserSttgdata = Usersettings.objects.filter(fb_user_id=userid).first()
                # Table_non_columns = list(filter(None, UserSttgdata.non_columns))+["alpjt"] if len(UserSttgdata.non_columns) > 0 else list(filter(None, grpData.non_columns))+["alpjt"]

                serializer = []

                grpData = Groups.objects.filter(fk_user_id=userid)
                if isinstance(request.auth, TeamAccount):
                    allowed_projects = TeamProject.objects.filter(
                        fk_user_id=userid,
                        client_id=request.auth.id,
                    ).values_list("group", flat=True)
                    grpData = grpData.filter(id__in=allowed_projects)
                grpData = grpData.all()
                if grpData:
                    Account.objects.filter(id=userid).update(last_home_visit=timezone.now())
                    serializer.extend(DashHomeSerializer(grpData, many=True).data)
                exitlast(userid, "dashboard")

                SettingsData = Settings.objects.filter(id=1).first()
                Engmd = 1 if SettingsData and SettingsData.core_manual_mode else 0

                return JsonResponse({"status": "true", "data": serializer, "Eng": Engmd})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# @api_view(['POST'])
# def homeload(request):
#     if request.method == 'POST' and authPermission.validate(request, "POST"):
#         userid = request.POST['userid']
#         grpid = request.POST['grpid']
#         if userid and grpid:

#             if userid.isdigit() and grpid.isdigit():

#                 # REQUEST TRACKER UPDATE - STARTS
#                 reqFlag = 0
#                 if int(userid) == 1 and "logid" in request.POST:
#                     if request.POST['logid'].isdigit():
#                         tracker.userTrackerRequest(request, request.POST['logid'])
#                         reqFlag = 1

#                 if reqFlag == 0:
#                     tracker.userTrackerRequest(request, userid)
#                 # REQUEST TRACKER UPDATE - ENDS

#                 grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
#                 if grpData:
#                     userlogid = request.POST['logid'] if "logid" in request.POST else userid
#                     Account.objects.filter(id=userid).update(last_home_visit=datetime.now())
#                     serializer = DashHomeSerializer([grpData], many=True, context={'logid': userlogid}).data[0]
#                     UserSttgdata = Usersettings.objects.filter(fb_user_id=userid).first()
#                     Table_non_columns = list(filter(None, UserSttgdata.non_columns))+["alpjt"] if len(UserSttgdata.non_columns) > 0 else list(filter(None, grpData.non_columns))+["alpjt"]
#                     # All_project_columns = 1 if len(UserSttgdata.non_columns) > 0 else 0

#                     #demo page add keyword
#                     # if "logid" in request.POST:
#                         # userlogid = request.POST['logid']
#                     if userlogid != userid:
#                         UserSttgdata = Usersettings.objects.filter(fb_user_id=userlogid).first()
#                         # grpAll = Groups.objects.filter(fk_user_id=userlogid).count()
#                         # accountData = Accountusage.objects.filter(fb_user_id=userlogid).values('plan_project_limit').first()
#                         # planProjectLimit = accountData['plan_project_limit'] if 'plan_project_limit' in accountData else 1
#                         exitlast(userlogid,'demo')
#                         # return JsonResponse({'status':'true','data': serializer, 'Ug_ln': grpAll, 'pPL': planProjectLimit, 'tnc': Table_non_columns })
#                         return JsonResponse({'status':'true','data': serializer, 'tnc': Table_non_columns, 's_s': UserSttgdata.skip_status})
#                     else:
#                         exitlast(userid,'dashboard')
#                         return JsonResponse({'status':'true','data': serializer, 'tnc': Table_non_columns, 's_s': UserSttgdata.skip_status})

#     return JsonResponse({'status':'false','message':"Something went wrong"})


# Dashboard Table
def _account_pages_for(userid):
    """The account's pages-per-keyword, for the out-of-range ceiling.

    Accountusage.serp_depth defaults to 1, so an account that never chose a
    depth searches ONE page. Without this the ceiling fell back to a constant
    and every keyword on such an account would have claimed "not in the first
    30" against a search that only ever looked at ten.
    """
    from serp.keyword import _account_pages

    return _account_pages(Accountusage.objects.filter(fb_user_id=userid).first())


def _gsc_connected(group):
    """Is this project actually joined to a Search Console property?

    Both signals are needed. `gsc_last_track` defaults to utcnow on the model,
    so it is truthy on a project that has never connected anything, and
    `gsc_track_status` defaults to the string "NA".
    """
    def field(name):
        if isinstance(group, dict):
            return group.get(name)
        return getattr(group, name, None)

    status = str(field("gsc_track_status") or "").strip().upper()
    prop = str(field("gsc_property") or "").strip()
    return bool(prop) and status not in ("", "NA")


@api_view(["POST"])
def getdashboard(request):
    # Read before use. These four were indexed straight off the body,
    # so a client omitting one got a 500 -- and with DEBUG on, a 94 KB
    # traceback carrying the settings and a source excerpt.
    absent = missing_fields(request, "userid", "grpid", "field", "sort")
    if absent:
        return bad_request(absent)
    userid = logid = str(request.data["userid"])
    grpid = str(request.data["grpid"])
    field = request.data["field"]
    sort = request.data["sort"]
    if userid and grpid and authPermission.validate(request, "POST"):

        if userid.isdigit() and grpid.isdigit():
            limit = request.data["limit"] if "limit" in request.data else 20

            page_filter = {"fk_user_id": userid, "fk_group_id": grpid}
            keywords = (
                Keyword.objects.filter(**page_filter)
                .values(
                    "id",
                    "keyword",
                    "ranknow",
                    # rank_state() needs both: manual_call_mode tells a failed
                    # check from one that found nothing, serp_pages gives the
                    # depth the "not in the first N" ceiling is derived from.
                    "manual_call_mode",
                    "serp_pages",
                    "isocode",
                    "platform",
                    "rank",
                    "lastranked_date",
                    "created_date",
                    "lastranked_date",
                    "top_rank",
                    "dayval",
                    "daymark",
                    "weekval",
                    "weekmark",
                    "halfmonthval",
                    "halfmonthmark",
                    "snippets_details",
                    "serp_features",
                    "knowledge_panel",
                    "featured_snippet",
                    "ads",
                    "review",
                    "total_rating",
                    "search_volume",
                    "exactdomain",
                    "site_url",
                    "tags",
                    "region",
                    "location",
                    "language",
                    "search_results",
                    "isocode",
                    "platform",
                    "keyword_alias",
                    "cannibalisation",
                    "gsc_clicks",
                    "gsc_impressions",
                    "gsc_clicks_last_week",
                    "gsc_impressions_last_week",
                    "fk_group",
                )
                .order_by(field)
                .all()
            )

            if keywords:
                GrpIns = Groups.objects.filter(fk_user_id=userid, id=grpid).values("domain_name", "score_meter", "gsc_last_track", "gsc_track_status", "gsc_property").first()
                page_volume_query = list(keywordVolume.objects.filter(**page_filter).values("month_wise_volume", "past_months", "fk_keyword_id").all())

                volume_data = {}
                if page_volume_query:
                    volume_data = {item["fk_keyword_id"]: {"month_wise_volume": item["month_wise_volume"], "past_months": item["past_months"]} for item in page_volume_query}

                # gsc_connected, not just gsc_last_track: that column defaults to
                # utcnow, so it is truthy on a project that has never been
                # connected to Search Console at all.
                serializer = DashKeywordSerializer(keywords, many=True, context={"voldata": volume_data, "dn": GrpIns["domain_name"], "gsc_lt": GrpIns["gsc_last_track"], "gsc_connected": _gsc_connected(GrpIns), "account_pages": _account_pages_for(userid)}).data

                SettingsData = Settings.objects.filter(id=1).values("core_manual_mode").first()
                Engmd = SettingsData["core_manual_mode"] if SettingsData else False

                Count = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, manual_call_status__in=[True]).count()
                mrKey = "off"
                if Count > 0:
                    mrKey = "onk"
                else:
                    svCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, search_volume="init").count()
                    mrKey = "onv" if svCount > 0 else "off"

                if int(userid) == 1 and "logid" in request.data:
                    if request.data["logid"].isdigit():
                        logid = request.data["logid"]

                GrpSttgdata = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("columns_order").first()
                UserSttgdata = Usersettings.objects.filter(fb_user_id=userid).values("columns_order").first()
                Table_non_columns = UserSttgdata["columns_order"] if len(UserSttgdata["columns_order"]) > 0 else GrpSttgdata["columns_order"]

                return JsonResponse({"st": 1, "mr": mrKey, "results": serializer, "Eng": Engmd, "gA": len(GrpIns["score_meter"]), "tnc": Table_non_columns})

    return JsonResponse({"st": 0, "message": "Something went wrong"})


@api_view(["POST"])
def gridload(request):
    # .get(): a screen with no project selected sends no grpid at all -- axios
    # drops an undefined field from the body -- and a literal subscript turned
    # that into KeyError -> unhandled 500. Absence is a value here; the falsy
    # guard below already answers it with the terminal status:false.
    userid = request.data.get("userid")
    grpid = request.data.get("grpid")

    if userid and grpid and authPermission.validate(request, "POST"):

        if userid.isdigit() and grpid.isdigit():
            grp_filter = {"fk_user_id": userid, "id": grpid}
            GrpIns = Groups.objects.filter(**grp_filter).values("id", "fk_user_id", "grid_sort")

            if GrpIns:
                if "gridtype" in request.data:
                    gridtype = request.data["gridtype"]
                else:
                    gridtype = GrpIns[0]["grid_sort"]

                Groups.objects.filter(**grp_filter).update(grid_sort=gridtype)

                # TAG LIST
                Tagflatss = list()
                ss = list(Keyword.objects.exclude(tags=[]).filter(fk_user_id=userid, fk_group_id=grpid).values_list("tags", flat=True).all())
                if len(ss) > 0:
                    Tagflatss = list(set(numpy.concatenate(ss).flat))

                # VOLUME COLLECTION
                data_filter = {"fk_user_id": userid, "fk_group_id": grpid}
                data_volume_query = list(keywordVolume.objects.filter(**data_filter).values("month_wise_volume", "past_months", "fk_keyword_id").all())

                volume_data = {}
                if data_volume_query:
                    volume_data = {item["fk_keyword_id"]: {"month_wise_volume": item["month_wise_volume"], "past_months": item["past_months"]} for item in data_volume_query}

                # SERIALIZER
                if "grdSValue" in request.data:
                    grdtype = request.data["grdSValue"]
                    serializer = TagSerializer(GrpIns, many=True, context={"voldata": volume_data, "search": grdtype, "gridtype": gridtype, "unqtags": Tagflatss}).data
                else:
                    serializer = TagSerializer(GrpIns, many=True, context={"voldata": volume_data, "filter": False, "gridtype": gridtype, "unqtags": Tagflatss}).data

                # COUNT ANALYSIS
                Count = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, manual_call_status__in=[True]).count()
                mrKey = "off"
                if Count > 0:
                    mrKey = "onk"
                else:
                    svCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, search_volume="init").count()
                    mrKey = "onv" if svCount > 0 else "off"

                return JsonResponse({"status": "true", "count": mrKey, "results": serializer, "unq": Tagflatss})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# Manage Tag
@api_view(["POST"])
def getlabels(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                selectids = request.data["sltids"]
                keywords = Groups.objects.filter(fk_user_id=userid, id=grpid).order_by("id")

                if len(selectids) > 0 and keywords:
                    serializer = ManagetagSerializer(keywords, many=True, context={"selectids": selectids}).data
                    return JsonResponse({"status": "true", "result": serializer})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# update tag
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def update_tags(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = request.data["userid"]
            grpid = request.data["grpid"]
            if userid and grpid:


                if userid.isdigit() and grpid.isdigit():
                    # ids = json.loads(request.data['ids'].strip())
                    # tagstr = json.loads(request.data['tags'].strip())
                    # comtags = json.loads(request.data['commontags'].strip())
                    tagstr = request.data["tags"]
                    ids = request.data["ids"]
                    comtags = request.data.get("commontags", [])

                    if len(ids) == 0:
                        return JsonResponse({"status": "false", "message": "Something went wrong"})

                    # taglist = list(set(map(itemgetter('text'), tagstr)))
                    taglist = list(set(map(lambda x: x.strip().lower(), tagstr)))
                    alltags = list(set(taglist + comtags))[:20]

                    if len(alltags) > 20:
                        return JsonResponse({"status": "false", "message": "Maximum 20 tags only allowed"})

                    if len(ids) == 1:
                        Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, id__in=ids).update(tags=alltags, tagcount=len(alltags))
                        NoneTagKeyCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, tagcount=0).count()
                        return JsonResponse({"status": "true", "message": "Tags updated successfully", "noneTag": NoneTagKeyCount})

                    if len(ids) >= 2:
                        keywords = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, id__in=ids)
                        for keyword in keywords:
                            existing_tags = keyword.tags or []
                            keyword.tags = list(set(existing_tags + alltags))[:20]
                            keyword.tagcount = len(keyword.tags)
                            keyword.save()

                        NoneTagKeyCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, tagcount=0).count()
                        return JsonResponse({"status": "true", "message": "Tags updated successfully", "noneTag": NoneTagKeyCount})
                else:
                    return JsonResponse({"status": "false", "message": "Something went wrong"})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
    except Exception as e:
        print(str(e))
        return JsonResponse({"status": "false", "message": "Something went wrong"})


# update single tag
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def updatetag_singlekw(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        kwid = request.POST["id"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid.isdigit():
                tagstr = json.loads(request.POST["tags"].strip())
                # comtags = json.loads(request.POST['commontags'].strip())

                alltags = list(set(map(lambda x: x["text"].strip().lower(), tagstr)))
                # alltags =list(set(taglist+comtags))
                if len(alltags) < 6:
                    Tagskey = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, id=kwid).update(tags=alltags, tagcount=len(alltags))
                    return JsonResponse({"status": "true", "message": "Tags updated successfully", "tg": alltags})

                return JsonResponse({"status": "false", "message": "Maximum 5 tags only allowed"})
    return JsonResponse({"status": "false", "message": "Something went wrong"})


# remove tag
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def remove_tag(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        tagname = request.POST["tag"].lower()
        if userid and grpid and tagname != "":

            if userid.isdigit() and grpid.isdigit():
                # kwslist = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid,tags__contains=[tagname]).values_list('tags', flat=True)
                kwslist = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, tags__contains=[tagname])

                if kwslist:
                    for kw in kwslist:
                        tagss = kw.tags
                        if tagname in tagss:
                            tagss.remove(tagname)
                        kw.tags = tagss
                        kw.save(update_fields=["tags"])
                    return JsonResponse({"status": "true", "message": '"' + tagname.capitalize() + '" Tag removed successfully'})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# typoerror fixing
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def typoerrorfix(request):
    if request.method == "POST":
        userid = request.data["userid"]
        keyid = request.data["keyid"]
        action = request.data["action"]
        if userid and keyid:
            keyIns = Keyword.objects.filter(id=keyid, fk_user_id=userid).first()
            if keyIns and action == "ignore":
                keyIns.keyword_alias = "-"
                keyIns.save()
                return JsonResponse({"status": "true", "message": "Error Ignored"})
            elif keyIns:
                typoerrorvalue = keyIns.keyword_alias
                grpid = keyIns.fk_group_id
                url = keyIns.site_url
                region = keyIns.region
                language_code = keyIns.language_code
                platform = keyIns.platform
                existskeycheck = Keyword.objects.filter(keyword=typoerrorvalue, site_url__contains=url, fk_group_id=grpid, region=region, language_code=language_code, platform=platform).count()
                if existskeycheck == 0:
                    if typoerrorvalue != "":
                        # postDataValues=[x for x in keyIns.postdata.values()]
                        # mydict = {}
                        # mydict['target'] = postDataValues[0]['target']
                        # mydict['se_name'] = postDataValues[0]['se_name']
                        # mydict['device'] = postDataValues[0]['device']
                        # mydict['language_name'] = postDataValues[0]['language_name']
                        # mydict['language_code'] = postDataValues[0]['language_code']
                        # mydict['location_name'] = postDataValues[0]['location_name']
                        # mydict['keyword'] = typoerrorvalue
                        randomstr = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
                        # postdata = {
                        #     randomstr: mydict,
                        # }
                        # keyIns.postdata = postdata
                        keyIns.postdata = {}
                        keyIns.keyword = typoerrorvalue
                        keyIns.keyword_alias = ""
                        keyIns.search_volume = "init"
                        keyIns.save()
                        return JsonResponse({"status": "true", "message": "Error Fixed"})
                    else:
                        return JsonResponse({"status": "false", "message": "No error found"})
                else:
                    return JsonResponse({"status": "false", "message": "Keyword already exists"})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def dashboard_view_change(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        view = request.data["view"]
        if userid.isdigit() and (view == "L" or view == "G"):
            tableview = "gridview" if view == "G" else "listview"
            dashview = Groups.objects.filter(id=grpid).update(dashboard_view=tableview)
            return Response({"status": "true", "message": "Dashboard View changes update on user settings"})

    return Response({"status": "false", "message": "Something went wrong"})


# list table header colums
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def tblHeaderUpdate(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        tablecolumns = request.data["tblvw"]
        allgroup_tableview = request.data["alpjt"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                tableview = tablecolumns
                if allgroup_tableview:
                    dashview = GroupSetting.objects.filter(fk_user_id=userid).update(columns_order=tableview)
                    Usersttg = Usersettings.objects.filter(fb_user=userid).update(columns_order=tableview)
                else:
                    dashview = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(columns_order=tableview)
                    Usersttg = Usersettings.objects.filter(fb_user=userid).update(columns_order={})

                # if "alpjt" not in tableview:
                #     dashview = Groups.objects.filter(id=grpid, fk_user=userid).update(non_columns=tableview)
                #     Usersttg = Usersettings.objects.filter(fb_user=userid).update(non_columns=[])
                # else:
                #     tableview.remove("alpjt")
                #     dashview = Groups.objects.filter(fk_user=userid).update(non_columns=tableview)
                #     Usersttg = Usersettings.objects.filter(fb_user=userid).update(non_columns=tableview)
                return Response({"status": "true", "message": "Table column views have been updated successfully."})

    return Response({"status": "false", "message": "Something went wrong"})


# keyword in result page get api
def _live_google_url(keyword, country="", language=""):
    """Build an honest live Google results URL for a tracked query.

    DataBlue returns structured SERP data; it does not return the raw Google
    document the retired preview server used to archive.  Keep the distinction
    explicit by linking to a fresh Google search with the keyword's locale.
    """
    params = {"q": keyword, "pws": "0"}
    if country:
        params["gl"] = str(country).lower()
    if language:
        params["hl"] = str(language).lower()
    return "https://www.google.com/search?" + urlencode(params)


@api_view(["POST", "GET"])
def gresultpage(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = request.data["kwid"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                # One caller, one shape. The `brand` and `kresearch`
                # branches selected models for surfaces this build does not
                # route, and the only caller has never sent a pageType.
                keyIns = Keyword.objects.filter(
                    fk_group=grpid, fk_user=userid, id=kwid
                ).values("keyword", "isocode", "language_code").first()
                keyword_field = "keyword"
                country_field = "isocode"

                if not keyIns:
                    return Response({"status": "false", "message": "Keyword not found"})

                url = _live_google_url(
                    keyIns.get(keyword_field, ""),
                    keyIns.get(country_field, ""),
                    keyIns.get("language_code", ""),
                )
                return Response({"status": "true", "url": url, "mode": "live"})

    return Response({"status": "false", "message": "Something went wrong"})


# # Join the code for notification update on project managemant.py
# # dashboard mail notification
# @api_view(['POST','GET'])
# def mailntfictn(request):
#     if request.method == 'POST' and authPermission.validate(request, "POST"):
#         userid = request.data['userid']
#         grpid = request.data['grpid']

#         if userid and grpid:

#             if userid.isdigit() and grpid.isdigit():

#                 grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
#                 allswitchs = grpData.automation_email_switch

#                 return Response({'status':'true', 'OptSw':allswitchs})

#     return Response({'status':'false','message':"Something went wrong"})

# ---------------------dashboard------------------------------

# ------------------------------------------------------------


# wizard page redirect api
@api_view(["POST"])
def validatecheck(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                # changed
                sts, cnt = totalKeywordsCount(userid)
                totalKeywords = cnt
                # totalKeywords = Keyword.objects.filter(fk_user_id=userid).count()
                groupKeywords = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).count()
                groupcountvalue = Groups.objects.filter(fk_user_id=userid).count()
                userPlan = Accountusage.objects.filter(fb_user_id=userid).first()
                if userPlan is None:
                    return JsonResponse({"status": "false", "message": "No account usage record found"})

                return JsonResponse({"status": "true", "type": userPlan.st_purchase_id, "grouplength": groupcountvalue, "usedKeywords": totalKeywords, "groupKeywords": groupKeywords})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})


# ------------------------------------------------------------


# add keyword, create keyword, new wizard, project setting
def _region_triplet(kw, fallback="us|google.com|United States"):
    """Build "iso|domain|country" from a keyword's location.

    location is expected as "google.co.in (India)". Older or seeded rows may
    hold just "India" with no bracket, which used to raise IndexError on
    region[1] and turn /getsetting into a 500 for the whole account.
    """
    try:
        parts = (kw.location or "").split("(")
        if len(parts) < 2:
            return fallback
        return "%s|%s|%s" % (
            (kw.isocode or "us").lower(),
            parts[0].strip(),
            parts[1].replace(")", "").strip(),
        )
    except Exception:
        return fallback


@api_view(["POST"])
def getsetting(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data.get("userid")
        # "No project selected" is a state, not an error, and it arrives in
        # several shapes. The web app used to write the literal "dmo" into the
        # `activegrp` cookie until the account had its first project; it now
        # leaves the cookie unset, and axios drops an undefined field from the
        # JSON body entirely -- so this key can be "dmo", "", null, 0, or
        # ABSENT. Geo Citations, Content Planner and the keyword navigator all
        # call this before anything else, so every brand-new account comes
        # through here.
        #
        # Two different 500s lived on that path: `request.data["grpid"]` raised
        # KeyError when the key was missing, and passing a non-numeric id to a
        # fk_group_id filter reached djongo and raised ValueError("Field 'id'
        # expected a number but got 'dmo'"). Use .get() so absence is a value,
        # then answer the account-wide half and leave the project-scoped half
        # empty for every one of those shapes.
        grpid = str(request.data.get("grpid") or "").strip()
        hasGroup = grpid.isdigit()
        if userid:

            if userid:
                regions = Region.objects.all()
                regserializer = RegionFltrSerializer(regions, many=True)

                GrpKeywdIns = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid) if hasGroup else Keyword.objects.none()
                KeywdIns = Keyword.objects.filter(fk_user_id=userid)
                GrplastKeywd = GrpKeywdIns.last()
                lastKeywd = KeywdIns.last()
                if GrplastKeywd:
                    lastKeywdRegion = _region_triplet(GrplastKeywd)
                elif lastKeywd:
                    lastKeywdRegion = _region_triplet(lastKeywd)
                else:
                    lastKeywdRegion = "us|google.com|United States"

                if "type" in request.data:
                    if request.data["type"] == "RGOLY":
                        return JsonResponse({"status": "true", "rg": regserializer.data, "DR": lastKeywdRegion})

                keycountvalue = GrpKeywdIns.count()
                # changed
                sts, cnt = totalKeywordsCount(userid)
                totalKeywords = cnt
                # totalKeywords = KeywdIns.count()

                accountUsageData = Accountusage.objects.filter(fb_user_id=userid).first()

                languages = Language.objects.all()
                langserializer = LanguageNameSerializer(languages, many=True)

                groupcountvalue = Groups.objects.filter(fk_user_id=userid).count()
                groupdata = Groups.objects.filter(fk_user_id=userid, id=grpid).first() if hasGroup else None
                domain_name = None
                if groupdata:
                    domain_name = groupdata.domain_name

                # keyword
                taglist = []
                groupTags = list(Keyword.objects.exclude(tags=[]).filter(fk_user_id=userid, fk_group_id=grpid).values_list("tags", flat=True).all()) if hasGroup else []
                if len(groupTags) > 0:
                    taglist = list(set(numpy.concatenate(groupTags).flat))

                # return JsonResponse({'status':'true','dN':domain_name,'type':accountUsageData.st_purchase_id,'pPL':accountUsageData.plan_project_limit, 'planKeyLimit':accountUsageData.plan_keyword_limit, 'planRefreshLimit':accountUsageData.plan_refresh_limit, 'usedRefreshLimit':accountUsageData.used_refresh_limit, 'grouplength':groupcountvalue,'usedKeywords':totalKeywords,'keywordlength':keycountvalue,'addedtags':taglist,'languages':langserializer.data,'regions':regserializer.data,'DR':lastKeywdRegion})
                # An account with no usage row is a broken registration, not a
                # reason to 500 the page that would let the user notice it.
                planProjectLimit = accountUsageData.plan_project_limit if accountUsageData else 0
                planKeywordLimit = accountUsageData.plan_keyword_limit if accountUsageData else 0
                return JsonResponse({"status": "true", "dN": domain_name, "pPL": planProjectLimit, "pKL": planKeywordLimit, "g_l": groupcountvalue, "u_kw": totalKeywords, "k_l": keycountvalue, "o_tg": taglist, "lnge": langserializer.data, "rg": regserializer.data, "DR": lastKeywdRegion})
    return JsonResponse({"status": "false", "message": "Something went wrong"})


# dashboard page refresh
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def usercrawl(request):
    # This one spends the account holder's provider credits, so a
    # malformed call must be refused before anything is queued.
    absent = missing_fields(request, "userid", "grpid", "ids")
    if absent:
        return bad_request(absent)
    userid = request.data["userid"]
    grpid = request.data["grpid"]
    keyids = request.data["ids"]
    # keyids = json.loads(request.data['ids'])
    usageCount = 0

    groupWaitingCount = Groups.objects.filter(fk_user_id=userid, manual_grp_trigger="WAIT").count()
    userGroupWaitingCount = Groups.objects.filter(manual_grp_trigger="WAIT").count()
    if userGroupWaitingCount > 5:
        return JsonResponse({"status": "false", "message": "Server is busy. Try again later"})
    elif groupWaitingCount > 1:
        return JsonResponse({"status": "false", "message": "Multiple project refresh are not allowed"})
    else:
        SettingsData = Settings.objects.filter(id=1).first()
        if SettingsData:
            if SettingsData.core_manual_mode == True:
                if userid and grpid:
                    accountUsage = Accountusage.objects.filter(fb_user_id=userid)
                    if accountUsage.exists():
                        paystatus, payOverRule = userPaymode(userid)
                        if paystatus not in ["dead", "cancelled", "expire"]:
                            usedRefLimit = accountUsage[0].used_refresh_limit
                            totalRefLimit = accountUsage[0].plan_refresh_limit
                            availRefLimit = totalRefLimit - usedRefLimit

                            GrpkeyIns = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid)
                            if len(keyids) == 0:
                                keyCount = GrpkeyIns.count()
                            else:
                                keyCount = len(keyids)

                            if usedRefLimit < totalRefLimit and keyCount <= availRefLimit:
                                if len(keyids) == 0:
                                    keywords = GrpkeyIns.update(manual_call_status=1)
                                    usageCount = GrpkeyIns.count()

                                else:
                                    keywords = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, id__in=keyids).update(manual_call_status=1)
                                    usageCount = len(keyids)

                                if usageCount > 0:
                                    manualRefreshNewUsage = usedRefLimit + usageCount
                                    accountUsage.update(last_used_refresh_count=usageCount, used_refresh_limit=manualRefreshNewUsage, modified_date=timezone.now())
                                    # accountUsage.last_used_refresh_count = usageCount
                                    # accountUsage.used_refresh_limit = manualRefreshNewUsage
                                    # accountUsage.save(update_fields=['used_refresh_limit', 'last_used_refresh_count'])

                                    groupRefreshUpdate = Groups.objects.filter(id=int(grpid)).update(strict_refresh_switch=True, manual_grp_trigger="INIT", last_used_refresh_count=usageCount)
                                    # groupRefreshUpdate = Groups.objects.filter(id=int(grpid)).first()
                                    # if groupRefreshUpdate:
                                    #     groupRefreshUpdate.strict_refresh_switch = True
                                    #     groupRefreshUpdate.manual_grp_trigger = "INIT"
                                    #     groupRefreshUpdate.last_used_refresh_count = usageCount
                                    #     groupRefreshUpdate.save(update_fields=['strict_refresh_switch', 'manual_grp_trigger', 'last_used_refresh_count'])

                                    refreshIns = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid)
                                    if refreshIns.exists():
                                        # A new run must not inherit the last one's reason.
                                        refreshIns.update(refresh_status="start", refresh_type="manual", refresh_error="", refresh_error_code="")
                                    else:
                                        refreshIns = Refreshmanual()
                                        refreshIns.fb_user_id = userid
                                        refreshIns.fk_group_id = grpid
                                        refreshIns.refresh_status = "start"
                                        refreshIns.refresh_type = "manual"
                                        refreshIns.save()

                                    trigger_engine_manual(userid, grpid)
                                    return JsonResponse({"status": "true", "usageCount": usageCount})
                                else:
                                    return JsonResponse({"status": "false", "message": "Try again later"})
                            else:
                                return JsonResponse({"status": "false", "message": "Your account reached the maximum number of refresh requests."})
                        else:
                            return JsonResponse({"status": "false", "message": "Oops! Sorry You've no active subscription."})
                    else:
                        return JsonResponse({"status": "false", "message": "Something went wrong"})
                else:
                    return JsonResponse({"status": "false", "message": "Unauthorized access"})
            else:
                return JsonResponse({"status": "false", "message": "Right now we are under maintenance. We will be back soon."})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong."})


# keywords' rank page refresh
@api_view(["POST", "GET"])
def refreshstatus(request):
    if request.method == "POST":
        # .get(), not [] -- a missing field is the CLIENT's mistake and deserves
        # a 400, not an uncaught KeyError rendered as a 500. This endpoint is
        # polled every 5 seconds by refresh_bar.js while a run is in flight, so
        # a 500 here is the loudest possible version of the mistake: under
        # DEBUG it answers each poll with a ~90KB traceback page.
        #
        # The same `request.data["..."]` pattern appears ~287 more times across
        # the routed backend and is exactly what tests/test_registration.py was
        # written for -- five optional fields read with [] returned 500 to a
        # client that posted only username/email/password. Those are not fixed
        # here: a blanket rewrite of 287 call sites is a larger, riskier change
        # than this bug justifies, and most of those fields are genuinely
        # required. See the audit report; this one is fixed because it is
        # polled continuously rather than called once.
        userid = request.data.get("userid")
        grpid = request.data.get("grpid")
        check = request.data.get("cntid")

        if not userid or not grpid:
            return JsonResponse(
                {"status": "false", "message": "userid and grpid are required."},
                status=400,
            )

        if check == "onvol":
            svIns = Keyword.objects.filter(fk_group=grpid, fk_user=userid, search_volume="init").count()

            return JsonResponse({"status": "true", "runkeyword": svIns})
        else:
            groupData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
            if groupData:
                refreshIns = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).first()
                keyIns = Keyword.objects.filter(fk_group=grpid, fk_user=userid, manual_call_status__in=[True]).count()
                refresh_status = ""
                if refreshIns:
                    refresh_status = refreshIns.refresh_status

                SettingsData = Settings.objects.filter(id=1).first()
                core_manual_mode = SettingsData.core_manual_mode if SettingsData and SettingsData.core_manual_mode else 0

                # runkeyword reaching 0 means the run STOPPED, not that it
                # worked -- the engine clears the running flag on its error
                # paths too. errc/err/fkw are what separates the two; the
                # frontend must only claim success when all three are clear.
                errcode, errmessage, failedKeywords = refresh_error_state(userid, grpid, refreshIns)

                return JsonResponse({"status": "true", "rst": refresh_status, "runkeyword": keyIns, "LUC": groupData.last_used_refresh_count, "Engmd": core_manual_mode, "errc": errcode, "err": errmessage, "fkw": failedKeywords})
            else:
                return JsonResponse({"status": "nope"})

    return JsonResponse({"status": "false"})


# dashboard page refresh
@api_view(["POST", "GET"])
def project_refresh_status(request):
    if request.method == "POST":
        userid = request.data["userid"]
        grpids = request.data["grpid"]
        if userid and grpids:
            rungrpids = []
            SettingsData = Settings.objects.filter(id=1).first()
            core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 0

            if core_manual_mode:
                kwrfCnt = Keyword.objects.filter(fk_group__in=grpids, fk_user=userid, manual_call_status__in=[True]).count()

                if kwrfCnt > 0:
                    for grpid in grpids:
                        keyIns = Keyword.objects.filter(fk_group=grpid, fk_user=userid, manual_call_status__in=[True]).count()
                        if keyIns > 0:
                            rungrpids.append(grpid)

            return JsonResponse({"status": "true", "grpids": rungrpids, "Engmd": core_manual_mode})

    return JsonResponse({"status": "false"})


# add keyword data fetch (Wizard page)
@api_view(["POST", "GET"])
def keyaddfetchstatus(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        grpid = request.POST["grpid"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                totalKeyIns = Keyword.objects.filter(fk_group=grpid, fk_user=userid).count()
                keyIns = Keyword.objects.filter(fk_group=grpid, fk_user=userid, manual_call_status__in=[True]).count()
                grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                SettingsData = Settings.objects.filter(id=1).first()
                core_manual_mode = SettingsData.core_manual_mode if SettingsData and SettingsData.core_manual_mode else 0

                if keyIns == 0 and grpData.manual_grp_trigger == "DONE":
                    refData = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).first()
                    if refData.refresh_status == "done":
                        return Response({"status": "true", "totalkey": totalKeyIns, "runkeyword": keyIns, "refstatus": refData.refresh_status, "Engmd": core_manual_mode})
                    else:
                        return Response({"status": "false", "Engmd": core_manual_mode})
                else:
                    return Response({"status": "true", "runkeyword": keyIns, "totalkey": totalKeyIns, "Engmd": core_manual_mode})

    return Response({"status": "fail", "message": "Something went wrong"})


# Domain valid check (create keyword, wizard, referral)
@api_view(["POST", "GET"])
def domain_valid_check(request):
    if request.method == "POST":
        websiteurl = request.data["websiteurl"].strip()
        try:
            if websiteurl:
                uri = urlparse(websiteurl)
                if uri.scheme == "" or uri.scheme is None:
                    websiteurl = "https://" + websiteurl

                if websiteurl:
                    domainValidtor = validators.url(websiteurl)
                    if domainValidtor == True:
                        return Response({"status": "true", "message": "Domain is valid", "returnurl": websiteurl})
                    else:
                        return Response({"status": "false", "message": "Domain is invalid. Enter the correct domain name"})
        except requests.exceptions.RequestException:
            return Response({"status": "false", "message": "Domain is invalid. Enter the correct domain name"})
        else:
            return Response({"status": "false", "message": "Something went wrong"})

    return Response({"status": "false", "message": "Something went wrong"})


# group name (dashboard, project setting)
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def updategrpservice(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        grpid = str(request.data["grpid"])

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                grpname = request.data["grpname"].strip()

                grpData = Groups.objects.filter(fk_user_id=userid, id=grpid)
                if grpData.exists():
                    grpData.update(group_name=grpname)
                    # grpData.group_name = grpname
                    # grpData.updated_date = date.today()
                    # grpData.save()
                    return Response({"status": "true", "message": "Project updated"})

    return Response({"status": "false", "message": "Something went wrong"})


# +++++++++++++++++++++++++++keyword+++++++++++++++++++++++++++++++++++


# deletegrpservice, multidelete
def groupdelete(userid, grpid):
    groupFilter = Groups.objects.filter(fk_user_id=userid, id=grpid).delete()
    groupSttg = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
    manualFilter = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid)
    if manualFilter.exists():
        manualFilter.delete()

    reportFilter = Report.objects.filter(fb_user_id=userid, fk_group_id=grpid)
    if reportFilter.exists():
        reportFilter.delete()

    keywordFilter = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid)
    if keywordFilter.exists():
        keywordFilter.delete()

    historyFilter = KeywordHistory.objects.filter(fk_user_id=userid, fk_group_id=grpid)
    if historyFilter.exists():
        historyFilter.delete()

    kwNoteFilter = kwNotes.objects.filter(fk_user_id=userid, fk_group_id=grpid)
    if kwNoteFilter.exists():
        kwNoteFilter.delete()

    # brndTrckrFilter = brandTracker.objects.filter(fb_user_id=userid,fb_group_id=grpid)
    # if brndTrckrFilter.exists():
    #     brndTrckrFilter.delete()

    return True


# dashboard
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def deletegrpservice(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        grpid = str(request.data["grpid"])

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                groupdelete(userid, grpid)
                groupTotal = Groups.objects.filter(fk_user_id=userid)
                groupTopID = 0
                if groupTotal.exists():
                    groupTopID = groupTotal[0].id

                return Response({"status": "true", "groupid": groupTopID, "groupcount": len(groupTotal), "message": "Project deleted", "grpid": grpid, "userid": userid})

    return Response({"status": "false", "message": "Something went wrong"})


# Multiple keyword delete API
@api_view(
    [
        "POST",
        "GET",
    ]
)
@permission_classes((IsAuthenticated,))
def multidelete(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                idstr = request.data["ids"]
                # ids = json.loads(idstr)
                ids = list(idstr)

                cgrpIds = list(CompKeyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, fk_keyword_id__in=ids).values_list("fk_cp_project_id", flat=True))
                keyIns = Keyword.objects.filter(id__in=ids, fk_group_id=grpid).delete()
                kwHistory = KeywordHistory.objects.filter(fk_user_id=userid, fk_keyword_id__in=ids, fk_group_id=grpid)
                if kwHistory.exists():
                    kwHistory.delete()
                kwNote = kwNotes.objects.filter(fk_user_id=userid, fk_keyword_id__in=ids, fk_group_id=grpid)
                if kwNote.exists():
                    kwNote.delete()

                keywordFilter = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid)
                redirectFlag = "DISABLE"
                if keywordFilter.count() == 0:
                    redirectFlag = "ENABLE"
                    groupdelete(userid, grpid)
                elif len(cgrpIds) > 0:
                    grpData = Groups.objects.filter(fk_user_id=userid, id=grpid)
                    grpFstIns = grpData.values("competitor_project_array", "competitor_project_status").first()
                    cgrpStatus = grpFstIns["competitor_project_status"] if grpFstIns["competitor_project_status"] in ["INIT", "SCHD"] else "INIT"
                    listcgrpids = grpFstIns["competitor_project_array"] + cgrpIds
                    grpUpdate = grpData.update(competitor_project_array=listcgrpids, competitor_project_status=cgrpStatus)

                # ReScheduling Dashboard Graph and Meter
                calculation.OnUpdateToGroup(userid, grpid)

                userGroups = Groups.objects.filter(fk_user_id=userid)
                FstOcc = 0
                if userGroups.exists():
                    FstOcc = userGroups[0].id

                return JsonResponse({"status": "true", "grpCnt": len(userGroups), "FstOcc": FstOcc, "grpCheck": redirectFlag, "message": "Keyword deleted successfully"})

    return JsonResponse({"status": "false", "message": "Keyword deletion failed"})


# authenticate, login, report, setting
@api_view(["POST"])
def menu_details(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        if userid.isdigit():
            getGrpCount = request.data["count"]

            if userid:
                grps = Groups.objects.filter(fk_user=userid)
                userPlan = Accountusage.objects.filter(fb_user_id=userid)

                if getGrpCount == "GRPCNTONLY":
                    usdata = Usersettings.objects.filter(fb_user_id=userid).first()
                    if grps.count() == 0:
                        # This is the ONLY path that creates an Accountusage row for a new signup,
                        # and it required a Subscriptionplans row with plan_type="free" that no
                        # migration, fixture or seed ever creates. On a self-hosted install the
                        # table is empty, so no row was created and everything downstream broke:
                        # /getsetting 500s on a null plan_project_limit, and the API-key endpoints
                        # 404 -- a new user could not save their own DataBlue key at all.
                        #
                        # This product has no plans; limits come from the user's own key. The row
                        # is now created unconditionally, consulting Subscriptionplans only if a
                        # row happens to exist.
                        planData = Subscriptionplans.objects.filter(plan_type="free").first()
                        accountCount = userPlan.count()
                        if accountCount == 0:
                            currdate = datetime.now()
                            todate = currdate + timedelta(29)
                            kw_limit = planData.plan_keyword_limit if planData else 100000
                            rf_limit = planData.plan_refresh_limit if planData else 100000
                            pj_limit = planData.plan_project_limit if planData else 1000
                            cp_limit = getattr(planData, 'plan_competitor_limit', None) or 1000
                            base_plan = {"pKL": kw_limit, "pRL": rf_limit, "pPL": pj_limit, "pCL": cp_limit}
                        
                            accUseIns = Accountusage()
                            accUseIns.fb_user_id = int(userid)
                            accUseIns.st_purchase_id = 0
                            accUseIns.current_plan_id = planData.id if planData else 0
                            accUseIns.future_plan_id = planData.id if planData else 0
                            accUseIns.plan_keyword_limit = kw_limit
                            accUseIns.plan_refresh_limit = rf_limit
                            accUseIns.plan_project_limit = pj_limit


                            # Nothing is set here any more. Every limit field defaults to
                            # serp.models.UNMETERED, because Tracker meters nothing under
                            # BYOK. Signup used to hand-pick numbers to work around defaults
                            # of 0, which is a worse version of the same idea.

                            accUseIns.used_refresh_limit = 0
                            accUseIns.validity_from = currdate.strftime("%Y-%m-%d")
                            accUseIns.validity_to = todate.strftime("%Y-%m-%d")
                            accUseIns.status = "default"
                            accUseIns.user_type = "free"
                            accUseIns.startup_base_plan = base_plan
                            accUseIns.freemium_credit_usage = {}
                            accUseIns.save()

                    sb_s, pOverRule = userPaymode(userid)

                    return JsonResponse({"status": "true", "sidelist": grps.count(), "sb_s": sb_s})
                else:
                    sb_s, pOverRule = userPaymode(userid)
                    serializer = AppGroupSerializer(grps, many=True)
                    return JsonResponse({"status": "true", "sidelist": serializer.data, "type": userPlan[0].st_purchase_id, "projectlimit": userPlan[0].plan_project_limit, "sb_s": sb_s})

    return JsonResponse({"status": "false"})


# # wizard, setting
# @api_view(['POST','GET'])
# def user_settings(request):
#     if request.method == 'POST':
#         userid = request.POST['userid']
#         if userid.isdigit():
#             usdata = Usersettings.objects.filter(fb_user_id=userid)
#             usdatas = []
#             if usdata.exists():
#             # for ex in usdata :
#             #     usdatas.append({
#             #         'userid': ex.fb_user_id,
#             #         'skip_status': ex.skip_status,
#             #         'email_daily': ex.email_daily_routine,
#             #     })
#             account = Account.objects.filter(id=userid).first()

#             if "page" in request.POST:
#                 page = request.POST['page']

#                 # UPDATE LAST VIEWED PAGE
#                 exitlast(userid,page)

#                 # REQUEST TRACKER UPDATE - STARTS
#                 if page == "wizard":
#                     tracker.userTrackerRequest(request, userid)
#                 # REQUEST TRACKER UPDATE - ENDS

#             return Response({'status':'true','data':usdatas,'account_type': account.normal_mode})

#     return Response({'status':'false','message':"Something went wrong"})


# account settings
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def acc_settings(request):
    if request.method == "POST":
        userid = str(request.data["userid"])
        if userid.isdigit():
            account = Account.objects.filter(id=userid).first()
            grpCnt = Groups.objects.filter(fk_user_id=userid).count()

            return Response({"status": "true", "At": account.normal_mode, "uPL": grpCnt})

    return Response({"status": "false", "message": "Something went wrong"})


# profile settings
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def user_settings(request):
    if request.method == "POST":
        userid = str(request.data["userid"])
        if userid.isdigit():
            if "uname" in request.data:
                uname = request.data["uname"]
                personal_address = request.data["adrs"]
                designation = personal_address["des"] if "des" in personal_address else ""

                account = Account.objects.filter(id=userid)
                account.update(username=uname, designation=designation)
                Usersettings.objects.filter(fb_user_id=userid).update(
                    personal_address=personal_address
                )

                return Response({"status": "true", "message": "Profile successfully updated"})
            else:
                usIns = Usersettings.objects.filter(fb_user_id=userid).first()
                personal_address = usIns.personal_address if usIns and usIns.personal_address else {}

                accIns = Account.objects.filter(id=userid).first()
                personal_address["des"] = accIns.designation if accIns else ""

                return Response({"status": "true", "adrs": personal_address})

    return Response({"status": "false", "message": "Something went wrong"})


# profile settings
@api_view(["POST", "GET"])
def countries(request):
    if request.method == "POST":
        ids, error = require_ids(request, "userid")
        if error:
            return error
        userid = ids[0]
        if userid.isdigit():
            countries = Region.objects.values_list("region_country", flat=True).all()
            countries_list = list(filter(None, countries))
            countries_list.sort()
            return Response({"status": "true", "country_list": countries_list})

    return Response({"status": "false", "message": "Something went wrong"})


# Authenticate, accountregistration
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def new_user_create(request):
    if request.method == "POST":
        userid = request.data["userid"]
        usersettings = Usersettings.objects.filter(fb_user_id=userid).count()
        if usersettings == 0:
            serializer = UsersettingsSerializer(data={"fb_user": str(userid)})
            if serializer.is_valid():
                serializer.validated_data["columns_order"] = {}
                serializer.validated_data["external_reviews"] = {}
                fbcreate = serializer.save()
                username = request.data["username"]
                email = request.data["email"]
                if username and email:
                    context = {
                        "email": email,
                        "username": username,
                        "siteurl": settings.SITE_URL,
                        "serivceurl": settings.SERVICE_URL,
                    }
                    subject = "Welcome To Tracker "
                    toMail = [email]
                    mailDatas = sendMail("email/welcome.html", context, subject, toMail)
                    userregdetails = Userregistrationtoken.objects.filter(email=email)
                    # if userregdetails.count() > 0:
                    if userregdetails.exists():
                        userregdetails.delete()

                return Response({"status": "true", "message": "User settings created"})
            else:
                return Response({"status": "fail", "message": serializer.errors})
        elif usersettings > 0:
            return Response({"status": "true", "message": "existing user"})
        else:
            return Response({"status": "fail", "message": "details already created"})

    return Response({"status": "fail", "message": "Something went wrong"})


# wizard
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def skip_create(request):
    if request.method == "POST":
        userid = request.POST["userid"]
        if userid.isdigit():
            userset = Usersettings.objects.filter(fb_user_id=userid).update(skip_status="on", modified_date=timezone.now())
            return Response({"status": "true", "message": "Skip view on"})

    return Response({"status": "false", "message": "Something went wrong"})


# setting, createkeyword
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def skip_off(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        if userid.isdigit():
            userset = Usersettings.objects.filter(fb_user_id=userid).update(skip_status="off", modified_date=timezone.now())
            return Response({"status": "true", "message": "Skip view off"})

    return Response({"status": "false", "message": "Something went wrong"})


# setting
@api_view(["POST", "GET"])
@permission_classes((IsAuthenticated,))
def username_update(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.POST["userid"]
        newusername = request.POST["newusername"]
        if userid.isdigit():
            # usersname = Account.objects.filter(id=userid).update(username = newusername)
            usersname = Account.objects.filter(id=userid).first()
            if usersname is None:
                return Response({"status": "false", "message": "Something went wrong"})
            usersname.username = newusername
            usersname.save(update_fields=["username"])
            return Response({"status": "true", "message": "User name successfully changed", "data": usersname.username})

    return Response({"status": "false", "message": "Something went wrong"})


# frontend export txt or csv
@api_view(["POST", "GET"])
def export(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        exporttype = request.data["type"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                keydat = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by("ranknow")
                keydata = sorted(keydat, key=lambda x: x.ranknow if x.ranknow > 0 else float("inf"))

                if keydata:
                    if exporttype == "txt":
                        exporttxtdata = keydat.values_list("keyword", flat=True)
                        return Response({"status": "true", "message": "Successfully get export data", "txtdata": exporttxtdata})

                    serializer = ExportCSVKeywordSerializer(keydata, many=True)
                    exportdata = serializer.data

                    return Response({"status": "true", "message": "Successfully get export data", "data": exportdata})

    return Response({"status": "fail", "message": "Something went wrong"})


# frontend export pdf
@api_view(["POST", "GET"])
def pdfexport(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                keydat = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by("ranknow")
                keydata = sorted(keydat, key=lambda x: x.ranknow if x.ranknow > 0 else float("inf"))
                group = Groups.objects.filter(fk_user_id=userid, id=grpid).first()

                if keydata and group:
                    projectname = group.group_name
                    domainname = group.domain_name
                    serializer = ExportPDFKeywordSerializer(keydata, many=True)

                    post_pdf = render_to_string(
                        "email/report-pdf-template.html",
                        {
                            "paragraphs": serializer.data,
                            "projectname": projectname,
                            "domainname": domainname,
                            "siteurl": settings.SITE_URL,
                            "serivceurl": settings.SERVICE_URL,
                        },
                    )
                    post_pdfs = HTML(string=post_pdf).write_pdf()
                    return HttpResponse(post_pdfs, content_type="application/octet-stream")

    return Response({"status": "false", "message": "Something went wrong"})


# Accounts table last logout
@api_view(["POST", "GET"])
def last_logout(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = str(request.data["userid"])
        if userid.isdigit():
            if isinstance(request.auth, TeamAccount):
                TeamAccount.objects.filter(
                    id=request.auth.id,
                    fk_user_id=userid,
                ).update(last_logout=timezone.now())
            else:
                Account.objects.filter(id=userid).update(last_logout=timezone.now())
            # logout = Account.objects.get(id=userid)
            # logout.last_logout = datetime.now()
            # logout.save(update_fields=['last_logout'])
            return Response({"status": "true", "message": "Logout time successfully updated"})

    return Response({"status": "false", "message": "Something went wrong"})


# Exit last landed on
# @api_view(['POST'])
def exitlast(userid, page):
    if userid.isdigit():
        USettingIns = Usersettings.objects.filter(fb_user_id=userid).first()
        # Written on navigation, before the account has ever saved a setting.
        if USettingIns is None:
            return
        old_exit_last_landed_on = USettingIns.exit_last_landed_on
        if (page not in old_exit_last_landed_on) and len(old_exit_last_landed_on) > 0:
            old_exit_last_landed_on.insert(0, str(page))
        elif len(old_exit_last_landed_on) > 0:
            old_exit_last_landed_on.sort(key=page.__ne__)
        else:
            old_exit_last_landed_on = [page]

        USettingIns = Usersettings.objects.filter(fb_user_id=userid).update(exit_last_landed_on=old_exit_last_landed_on, modified_date=timezone.now())
        return JsonResponse({"status": "true"})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# NEW
@api_view(["POST"])
def _spaceApi_(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = str(request.data["userid"])
            grpid = str(request.data["grpid"])
            subject = request.data["subject"] if "subject" in request.data else ""
            mail = request.data["mail"] if "mail" in request.data else ""
            apply = request.data["apply"] if "apply" in request.data else ""
            image = request.FILES.get("image")
            current_timestamp_ms = str(int(time.time()))

            if len(apply) > 0:
                filename = f"wlr-{userid}-all-{current_timestamp_ms}.png"
            else:
                filename = f"wlr-{userid}-{grpid}-{current_timestamp_ms}.png"

            types = ["image/png"]
            if image:
                mime_type = magic.from_buffer(image.read(), mime=True)
                image.seek(0)

                if mime_type not in types:
                    return JsonResponse({"st": 0, "dt": "Only PNG Image are allowed"})
                else:
                    width, height = get_image_dimensions(image)
                    # height, width = get_height_and_width(magic.from_buffer(image.read()))
                    # image.seek(0)
                    groupData = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("wl_report_image").first()
                    if groupData:
                        if groupData["wl_report_image"] != None and len(groupData["wl_report_image"]):
                            if len(groupData["wl_report_image"]["key"]) != 0:
                                _delkey_ = groupData["wl_report_image"]["key"]
                                if default_storage.exists(_delkey_):
                                    default_storage.delete(_delkey_)

                    if userid.isdigit() and grpid.isdigit:
                        key = "white-label-report-images/sgkey" + userid + "/" + filename
                        if image:
                            key = default_storage.save(key, image)
                            image_url = request.build_absolute_uri(default_storage.url(key))
                            groupsettings = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid)
                            if groupsettings.exists():
                                wl_report_image_data = {"subject": subject, "mail": mail, "url": image_url, "key": key if len(apply) == 0 else "", "all": key if len(apply) > 0 else "", "dm": [height, width]}
                                if len(apply) > 0:
                                    groupsettings1 = GroupSetting.objects.filter(fk_user_id=userid)
                                    if groupsettings1.exists():
                                        grpupdt = groupsettings1.update(wl_report_image=wl_report_image_data)
                                        if grpupdt:
                                            retn_data = groupsettings1.values("wl_report_image").first()["wl_report_image"]["url"]
                                            return JsonResponse({"st": 1, "dt": retn_data})
                                else:
                                    grpupdt = groupsettings.update(wl_report_image=wl_report_image_data)
                                    if grpupdt:
                                        retn_data = groupsettings.values("wl_report_image").first()["wl_report_image"]["url"]
                                        return JsonResponse({"st": 1, "dt": retn_data, "dm": (height, width)})

                            return JsonResponse({"st": 1, "dt": "No data"})
    except Exception as e:
        return JsonResponse({"st": 0, "dt": str(e)})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def _updtWl_(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = str(request.data["userid"])
            grpid = str(request.data["grpid"])
            subject = request.data["subject"]
            mail = request.data["mail"]
            applyAll = request.data["apply"]

            if userid.isdigit() and grpid.isdigit():
                if len(applyAll) == 0:
                    Group = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).first()
                    if Group:
                        Group.wl_report_image["subject"] = subject
                        Group.wl_report_image["mail"] = mail
                        Group.save()
                        return JsonResponse({"st": 1, "dt": "updated"})
                else:
                    Groups = GroupSetting.objects.filter(fk_user_id=userid)
                    if Groups:
                        for group in Groups:
                            group.wl_report_image["subject"] = subject
                            group.wl_report_image["mail"] = mail
                            group.save(update_fields=["wl_report_image"])
                        return JsonResponse({"st": 1, "dt": "updateds"})
    except Exception:
        # `dt` goes straight through json.dumps, so returning the exception
        # object made the handler's own error path raise -- every caught error
        # became an unhandled 500 with a Django debug page.
        logger.exception("_updtWl_ failed")
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


def agency_pricing_retrieve():
    keyword_list = []
    try:
        agency_pricing_file = os.getcwd() + "/files/tracker_billing_plans.json"

        if agency_pricing_file and os.path.exists(agency_pricing_file):
            data = open(agency_pricing_file).read()
            content = json.loads(data)

            if isinstance(keyword_list, list):
                return content

    except Exception as e:
        print(" Error ", str(e))

    return keyword_list
