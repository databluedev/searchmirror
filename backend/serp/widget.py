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
from serp.custom_serializer.widget_serializers import *
from serp.custom_serializer.report_serializers import *
import string, random
from django.conf import settings
from urllib.parse import urlparse
from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
import csv, os
from io import StringIO
from weasyprint import HTML
from serp import calculation, tracker, user_timezone as uTZ
from account import verify as authPermission
from operator import itemgetter

from uuid import UUID
import numpy
import validators
import functools, math

from serp.custom_report.rp_keywords import rp_keywords_table
from django.utils import timezone
from shared.scoring import calculate_visibility_history
from shared.scoring import calculate_visibility_breakdown
from shared.scoring import classify_activity_level

from serp.e_com_widget import ecom_generate_widget
from rest_framework.permissions import IsAuthenticated
from account.cron_auth import cron_only

import logging

logger = logging.getLogger(__name__)

req_platform={
    'E-commerce': 'ecommerce',
    'Non E-commerce': 'non_ecommerce'
}
req_rev_platform={
    'ecommerce': 'E-commerce',
    'non_ecommerce': 'Non E-commerce'
}

def retrieve_access_token(refreshToken):
    try:
        data = {"grant_type": "refresh_token", "refresh_token": refreshToken, "client_id": settings.GA_CLIENT_ID, "client_secret": settings.GA_SECRET_ID, "scope": "https://www.googleapis.com/auth/analytics.readonly"}

        xRequest = requests.post("https://accounts.google.com/o/oauth2/token", data=data)
        json_res = xRequest.json()
        access_token = json_res.get('access_token')

        if access_token:
            return access_token
        else:
            return 0
    except Exception as e:
        return 0

def reverse_sign(f):
    return -f


def reverse_percentage(percentage_str):
    # Remove the percentage sign and convert to a float
    number = float(percentage_str.strip("%"))

    if number == 0.0:
        return percentage_str

    # Reverse the sign
    reversed_number = -number

    # Convert back to string and add percentage sign
    reversed_percentage_str = f"{reversed_number}%"

    return reversed_percentage_str


# COMMON FUNCTIONS
def absInt(num):
    return abs(int(float(num)))


def value_status(num, signType="+"):
    outputData = 0
    if num > 0:
        outputData = 1
    elif num == 0:
        outputData = 0
    else:
        outputData = -1

    return f_to_i(outputData) * -1 if signType == "-" else f_to_i(outputData)


def sinceRecentCalculation(barchartDetails, index=0):
    top_ten_counts = 0
    top_ten_counts += absInt(barchartDetails["P1"][index]) if len(barchartDetails["P1"]) > index else 0
    top_ten_counts += absInt(barchartDetails["P2"][index]) if len(barchartDetails["P2"]) > index else 0
    top_ten_counts += absInt(barchartDetails["P3"][index]) if len(barchartDetails["P3"]) > index else 0
    top_ten_counts += absInt(barchartDetails["T4"][index]) if len(barchartDetails["T4"]) > index else 0

    return top_ten_counts


# MANAGE-WIDGET
@api_view(["POST"])
def manage_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])
            update = request.data["update"] if "update" in request.data else ""

            if userId.isdigit() and grpId.isdigit():
                if "type" in request.data and "data" in request.data:
                    callType = str(request.data["type"])
                    widgetData = request.data["data"]

                    if callType == "update":
                        groupSettingExists = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId)
                        if groupSettingExists.exists():
                            group = groupSettingExists.update(widget_handle=widgetData)
                            if group:
                                group = groupSettingExists.first()
                                return JsonResponse({"st": 1, "dt": group.widget_handle})

                if userId and grpId and update:
                    # if False:
                    # groupSettingExists = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId)
                    if grpId != "-1":
                        data = request.data["datas"] if "datas" in request.data else ""
                        # total=list()
                        total = dict()
                        for i in data:
                            # total.append([i['x'],i['y'],i['i']])
                            total[i["i"]] = [i["x"], i["y"]]

                        groupSettingsExists = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId)
                        if groupSettingsExists:
                            group = groupSettingsExists.update(w_order=total)
                            if group:
                                data = groupSettingsExists.values("w_order").first()["w_order"]
                                return JsonResponse({"st": 1, "dt": data})
                elif "datas" in request.data:
                    # if False:
                    groupSettings = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId).values("w_order").first()
                    data = request.data["datas"] if "datas" in request.data else ""
                    if groupSettings["w_order"]:
                        w_order = [i for i in groupSettings["w_order"].values()]
                        for i in range(len(data)):
                            # if data[i]['i'] == coordinates[i][2]:
                            data[i]["x"] = w_order[i][0]
                            data[i]["y"] = w_order[i][1]
                    return JsonResponse({"st": 1, "dt": data})
    except Exception:
        # `dt` is serialised straight into the response body, so putting the
        # exception object here made json.dumps raise inside the handler: every
        # caught error became an unhandled 500 with a full Django debug page.
        logger.exception("manage_widget failed")
        return JsonResponse({"st": 0, "dt": "Something went wrong"})

    # Every branch above is conditional, so a request that matches none of them
    # fell off the end returning None -- which DRF turns into an AssertionError
    # and another 500 debug page, the same failure B-04 describes reached by a
    # different route. Verified live: POST /eldnah_wdt with only userid and
    # grpid. top_widget already ends this way; match it.
    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# TRENDING-WIDGET
@api_view(["POST"])
def trending_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                serializerData = []

                if groupExists:
                    keywordData = keywordVolume.objects.filter(fk_user_id=userId, fk_group_id=grpId, last_month_difference="up").order_by("-id").all()
                    serializerData = TrendingWidgetSerializer(keywordData, many=True).data

                return JsonResponse({"st": 1, "dt": serializerData})
    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# TRENDING-WIDGET
@api_view(["POST"])
def deviating_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                serializerData = []

                if groupExists:
                    keywordData = keywordVolume.objects.filter(fk_user_id=userId, fk_group_id=grpId, last_month_difference="down").order_by("-id").all()
                    serializerData = TrendingWidgetSerializer(keywordData, many=True).data

                return JsonResponse({"st": 1, "dt": serializerData})
    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# TRACKER-SCORE-WIDGET
@api_view(["POST"])
def score_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                callType = str(request.data["type"])
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId)

                if groupExists.exists():
                    groupData = groupExists.first()
                    keyword_rank_histories = list(
                        Keyword.objects.filter(
                            fk_user_id=userId,
                            fk_group_id=grpId,
                        ).values_list("rank", flat=True)
                    )
                    score_history = calculate_visibility_history(keyword_rank_histories)
                    history_keyword_counts = [
                        sum(index < len(ranks) for ranks in keyword_rank_histories)
                        for index in range(len(score_history))
                    ]
                    current_ranks = [
                        ranks[0] if ranks else 0 for ranks in keyword_rank_histories
                    ]
                    score_breakdown = calculate_visibility_breakdown(current_ranks)

                    # FILTER OPTION STARTED
                    if callType == "filter":
                        startPos = f_to_i(request.data["s_p"])
                        endPos = f_to_i(request.data["e_p"])
                        scoreLimit = score_history[startPos:endPos]
                        scorechartDetails = {}
                        scorechartDetails["ss_d"] = list(map(int, [float(i) for i in scoreLimit]))
                        return JsonResponse({"st": 1, "dt": scorechartDetails})
                    # FILTER OPTION FINISHED

                    scoreData = {}
                    scoreData["ps"] = -1  # PREVIOUS TRACKER SCORE
                    scoreData["ms"] = -1  # TOP TRACKER SCORE
                    scoreData["ts"] = -1  # TODAY TRACKER SCORE
                    scoreData["cp"] = 0  # YESTERDAY TRACKER SCORE COMPARISON - UP (1), DOWN (-1) AND NO-CHANGE (0)
                    scoreData.update(score_breakdown)
                    scoreData["baseline_changed"] = (
                        len(history_keyword_counts) > 1
                        and history_keyword_counts[0] != history_keyword_counts[1]
                    )

                    if len(score_history) > 0:
                        liveRatio = score_history[0]
                        scoreData["ts"] = f_to_i(liveRatio)  # TODAY SCORE
                        scoreData["ms"] = f_to_i(max(score_history))  # BEST SCORE

                    if len(score_history) > 1:
                        liveRatio = score_history[0]
                        prevRatio = score_history[1]
                        valRatio = f_to_i(liveRatio) - f_to_i(prevRatio)
                        scoreData["ps"] = f_to_i(prevRatio)  # PREVIOUS SCORE
                        if not scoreData["baseline_changed"]:
                            scoreData["cp"] = value_status(valRatio)

                    scoreGraphDetails = {}
                    scoreGraphDateTime = []
                    scoreLimitData = []

                    proUpdateDate = groupData.updated_date
                    scoreLimit = score_history[0:7]
                    for i in range(0, len(scoreLimit)):
                        dates = proUpdateDate - timedelta(days=i)
                        scoreGraphDateTime.append(dates.strftime("%m-%d-%Y"))
                        scoreLimitData.append(f_to_i(scoreLimit[i]))

                    scoreGraphDetails["ss_d"] = scoreLimitData
                    scoreGraphDetails["ss_dd"] = scoreGraphDateTime
                    scoreGraphDetails["p_n"] = groupData.group_name
                    scoreGraphDetails["t_c"] = len(score_history)
                    scoreGraphDetails["s_d"] = groupData.created_date.strftime("%m-%d-%Y")
                    scoreGraphDetails["e_d"] = proUpdateDate.strftime("%m-%d-%Y")
                    return JsonResponse({"st": 1, "rs": scoreData, "dt": scoreGraphDetails})
    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# TRACKER-TODAY-WIDGET
@api_view(["POST"])
def today_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                callType = str(request.data["type"])
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId)

                if groupExists.exists():
                    callType = str(request.data["type"])
                    groupData = groupExists.first()
                    bargraphdetails = {}

                    startPos = 0
                    endPos = 15

                    if callType == "filter":
                        startPos = int(request.data["s_p"])
                        endPos = int(request.data["e_p"])

                    barGrpLimit = groupData.activity_level[startPos:endPos] if len(groupData.activity_level) > endPos else groupData.activity_level[0 : len(groupData.activity_level)]
                    today = groupData.updated_date

                    barGraphDateTime = []
                    barGraphImproved = []
                    barGraphDeclined = []
                    barGraphLevel = []

                    for i in reversed(range(len(barGrpLimit))):
                        activityGroupData = list(map(str, barGrpLimit[i].split("|")))
                        if len(activityGroupData) == 3:
                            barGraphLevel.insert(0, classify_activity_level(activityGroupData[0].strip()))
                            barGraphImproved.insert(0, str(activityGroupData[1]))
                            barGraphDeclined.insert(0, "-" + str(activityGroupData[2]))
                        else:
                            barGraphLevel.insert(0, "")
                            barGraphImproved.insert(0, str("0"))
                            barGraphDeclined.insert(0, str("0"))

                        if callType != "filter":
                            dates = today - timedelta(days=i)
                            barGraphDateTime.insert(0, dates.strftime("%m-%d-%Y"))

                    bargraphdetails["i_d"] = barGraphImproved
                    bargraphdetails["d_d"] = barGraphDeclined
                    bargraphdetails["i_l"] = barGraphLevel

                    if callType != "filter":
                        bargraphdetails["g_dd"] = barGraphDateTime
                        bargraphdetails["t_c"] = len(groupData.activity_level)
                        bargraphdetails["p_n"] = groupData.group_name
                        bargraphdetails["s_d"] = groupData.created_date.strftime("%m-%d-%Y")
                        bargraphdetails["e_d"] = today.strftime("%m-%d-%Y")

                        pk = absInt(bargraphdetails["i_d"][0]) if len(bargraphdetails["i_d"]) else 0
                        pY = absInt(bargraphdetails["i_d"][1]) if len(bargraphdetails["i_d"]) > 1 else 0
                        prT = bargraphdetails["i_l"][0] if len(bargraphdetails["i_l"]) else ""
                        prY = bargraphdetails["i_l"][1] if len(bargraphdetails["i_l"]) > 1 else ""
                        nk = absInt(bargraphdetails["d_d"][0]) if len(bargraphdetails["d_d"]) else 0
                        nY = absInt(bargraphdetails["d_d"][1]) if len(bargraphdetails["d_d"]) > 1 else 0
                        pD = value_status(pk - pY)
                        nD = value_status(nk - nY, "-")

                        graphnormal = {
                            "pk": pk,
                            "pY": pY,
                            "pD": pD,
                            "prT": prT,
                            "prY": prY,
                            "nk": nk,
                            "nY": nY,
                            "nD": nD,
                        }

                        return JsonResponse({"st": 1, "rs": graphnormal, "dt": bargraphdetails})

                    return JsonResponse({"st": 1, "dt": bargraphdetails})

    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# TRACKER-TOP-WIDGET
@api_view(["POST"])
def top_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                callType = str(request.data["type"])
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId)

                if groupExists.exists():
                    callType = str(request.data["type"])
                    groupData = groupExists.first()

                    proUpdatedate = groupData.updated_date
                    barchartDetails = {}

                    startPos = 0
                    endPos = 7

                    if callType == "filter":
                        startPos = int(request.data["s_p"])
                        endPos = int(request.data["e_p"])

                    # startLimit = groupData.since_start[startPos:endPos] if len(groupData.since_start) > endPos else groupData.since_start[0:len(groupData.since_start)]
                    startPosition = groupData.since_position[startPos:endPos] if len(groupData.since_position) > endPos else groupData.since_position[0 : len(groupData.since_position)]
                    totalKeywords = groupData.total_Keyword[startPos:endPos] if len(groupData.total_Keyword) > endPos else groupData.total_Keyword[0 : len(groupData.total_Keyword)]

                    barFirstPos = []
                    barSecondPos = []
                    barThirdPos = []
                    barFourthPos = []
                    barMoreThan10 = []
                    barMoreThanLimit = []
                    barGraphDates = []

                    for i in range(0, len(startPosition)):
                        if callType != "filter":
                            dates = proUpdatedate - timedelta(days=i)
                            barGraphDates.append(dates.strftime("%m-%d-%Y"))

                        startPos = list(map(int, startPosition[i].split(",")))

                        barFirstPos.append(f_to_i(startPos[0]) if len(startPos) else 0)
                        barSecondPos.append(f_to_i(startPos[1]) if len(startPos) > 1 else 0)
                        barThirdPos.append(f_to_i(startPos[2]) if len(startPos) > 2 else 0)
                        barFourthPos.append(f_to_i(startPos[3]) if len(startPos) > 3 else 0)
                        barMoreThan10.append(f_to_i(startPos[4]) if len(startPos) > 4 else 0)
                        barMoreThanLimit.append(f_to_i(startPos[5]) if len(startPos) > 5 else 0)

                    barchartDetails["P1"] = barFirstPos
                    barchartDetails["P2"] = barSecondPos
                    barchartDetails["P3"] = barThirdPos
                    barchartDetails["T4"] = barFourthPos
                    barchartDetails["MT"] = barMoreThan10
                    barchartDetails["NR"] = barMoreThanLimit
                    barchartDetails["TK"] = totalKeywords

                    if callType != "filter":
                        barchartDetails["s_dd"] = barGraphDates
                        barchartDetails["t_c"] = len(groupData.since_start)
                        barchartDetails["p_n"] = groupData.group_name
                        barchartDetails["s_d"] = groupData.created_date.strftime("%m-%d-%Y")
                        barchartDetails["e_d"] = proUpdatedate.strftime("%m-%d-%Y")

                        fT = barchartDetails["P1"][0] if len(barchartDetails["P1"]) else 0
                        fY = barchartDetails["P1"][1] if len(barchartDetails["P1"]) > 1 else None
                        fD = value_status(fT - fY) if len(barchartDetails["P1"]) > 1 else 0

                        nT = barchartDetails["NR"][0] if len(barchartDetails["NR"]) else 0
                        nY = barchartDetails["NR"][1] if len(barchartDetails["NR"]) > 1 else None
                        nD = value_status(nT - nY) if len(barchartDetails["NR"]) > 1 else 0

                        cT = sinceRecentCalculation(barchartDetails)
                        cY = sinceRecentCalculation(barchartDetails, 1) if len(barchartDetails["P1"]) > 1 else None
                        cD = value_status(cT - cY) if len(barchartDetails["P1"]) > 1 else 0

                        graphdata = {
                            "fT": fT,
                            "fY": fY,
                            "fD": fD,
                            "nT": nT,
                            "nY": nY,
                            "nD": nD,
                            "cT": cT,
                            "cY": cY,
                            "cD": cD,
                        }

                        return JsonResponse({"st": 1, "rs": graphdata, "dt": barchartDetails})

                    return JsonResponse({"st": 1, "dt": barchartDetails})

    except Exception:
        # See manage_widget: an exception object is not JSON-serialisable, so
        # this error path used to raise and return a 500 debug page instead.
        logger.exception("top_widget failed")
        return JsonResponse({"st": 0, "dt": "Something went wrong"})

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# RESET SEARCH VOLUME TO NEW TABLE KEYWORD VOLUME
def resetVolumeTable(request):
    keywordData = Keyword.objects.all()
    data = []
    noData = []

    for singleKeyword in keywordData:
        kvData = {}

        kvData["kv_user_id"] = singleKeyword.fk_user_id
        kvData["kv_group_id"] = singleKeyword.fk_group_id
        flag = 0

        slug = singleKeyword.keyword.lower()
        keyword_slug = f"{slug}".replace(" ", "_")
        svExists = searchvolumes.objects.filter(keyword_slug=keyword_slug, region_code=singleKeyword.isocode)
        if svExists.exists():
            svData = svExists.first()
            if svData != None:
                kvData["kv_keyword_id"] = singleKeyword.id
                kvData["kv_keyword"] = svData.keyword
                kvData["kv_keyword_slug"] = svData.keyword_slug
                kvData["kv_region_name"] = svData.region_name
                kvData["kv_region_code"] = svData.region_code
                kvData["kv_searchvolume_country_id"] = svData.searchvolume_country_id
                kvData["kv_average_volume"] = svData.average_volume
                kvData["kv_comp_level"] = svData.comp_level
                kvData["kv_comp_index"] = svData.comp_index
                kvData["kv_last_update_volume"] = svData.last_update_volume
                kvData["kv_status"] = svData.status
                kvData["kv_month_wise_volume"] = svData.month_wise_volume
                kvData["kv_past_months"] = svData.past_months
                kvData["kv_created_date"] = svData.created_date
                kvData["kv_modified_date"] = svData.modified_date
                kvData["kv_keyword_details"] = {
                    "ky": kvData["kv_keyword"],
                    "rg": kvData["kv_region_name"],
                    "rc": kvData["kv_region_code"],
                }

                flag = 1
                kvData["kv_last_month_difference"] = "-"
                if len(svData.month_wise_volume) > 1:
                    svDiff = int(svData.month_wise_volume[-1]) - int(svData.month_wise_volume[-2])
                    print(svDiff)
                    if svDiff > 0:
                        kv_volume_difference = "up"
                    elif svDiff < 0:
                        kv_volume_difference = "down"
                    elif svDiff == 0:
                        kv_volume_difference = "same"
                    else:
                        kv_volume_difference = "-"
                    kvData["kv_last_month_difference"] = kv_volume_difference
        if flag == 1:
            KvInstance = keywordVolume()
            KvInstance.fk_user_id = kvData["kv_user_id"]
            KvInstance.fk_group_id = kvData["kv_group_id"]
            KvInstance.fk_keyword_id = kvData["kv_keyword_id"]
            KvInstance.keyword = kvData["kv_keyword"]
            KvInstance.keyword_slug = kvData["kv_keyword_slug"]
            KvInstance.region_name = kvData["kv_region_name"]
            KvInstance.region_code = kvData["kv_region_code"]
            KvInstance.searchvolume_country_id = kvData["kv_searchvolume_country_id"]
            KvInstance.average_volume = kvData["kv_average_volume"]
            KvInstance.comp_level = kvData["kv_comp_level"]
            KvInstance.comp_index = kvData["kv_comp_index"]
            KvInstance.last_update_volume = kvData["kv_last_update_volume"]
            KvInstance.last_month_difference = kvData["kv_last_month_difference"]
            KvInstance.status = kvData["kv_status"]
            KvInstance.month_wise_volume = kvData["kv_month_wise_volume"]
            KvInstance.past_months = kvData["kv_past_months"]
            KvInstance.created_date = kvData["kv_created_date"]
            KvInstance.modified_date = kvData["kv_modified_date"]
            KvInstance.keyword_details = kvData["kv_keyword_details"]
            KvInstance.save()

            data.append(singleKeyword.id)
        else:
            noData.append(singleKeyword.id)

    return JsonResponse({"status": "True", "noData": noData, "data": data})


# CANNIBALIZATION-WIDGET
@api_view(["POST"])
def cannib_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                serializerData = list()

                if groupExists:
                    keywordData = Keyword.objects.exclude(cannibalisation=[]).filter(fk_user_id=userId, fk_group_id=grpId).order_by("id").all()
                    # .values('id','rank','ranknow','region','location', 'language','search_results','cannibalisation','keyword','isocode','daymark')
                    serializerData = CannibalizationWidgetSerializer(keywordData, many=True).data

                return JsonResponse({"st": 1, "dt": serializerData})
    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# IMPROVED KEYWORDS-WIDGET
@api_view(["POST"])
def improvedkwds_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                serializerData = []

                if groupExists:
                    keywordData = Keyword.objects.filter(fk_user_id=userId, fk_group_id=grpId, daymark="up").order_by("-id").all()
                    # values('id','rank','ranknow','region','location', 'language','search_results','cannibalisation','keyword','isocode','daymark')
                    serializerData = ImpDecKwdWidgetSerializer(keywordData, many=True).data

                return JsonResponse({"st": 1, "dt": serializerData})
    except Exception as e:
        raise e

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# DECLINED KEYWORDS-WIDGET
@api_view(["POST"])
def declinedkwds_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                serializerData = []

                if groupExists:
                    keywordData = Keyword.objects.filter(fk_user_id=userId, fk_group_id=grpId, daymark="down").order_by("-id").all()
                    # values('id','rank','ranknow','region','location', 'language','search_results','cannibalisation','keyword','isocode','daymark')
                    serializerData = ImpDecKwdWidgetSerializer(keywordData, many=True).data

                return JsonResponse({"st": 1, "dt": serializerData})
    except Exception as e:
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# WEEKLY SEARCH QUERY WIDGET
@api_view(["POST"])
def weekly_search_query_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
                if groupExists:
                    gsc_data = GSCWeeklyQuery.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).order_by("-created_date").first()
                    serialized_gsc_data = GSCWeeklyQuerySerializer(gsc_data).data

                    if not serialized_gsc_data:
                        return JsonResponse({"st": 1, "wq": []})

                    weekly_queries = []
                    if len(serialized_gsc_data["queries"]) > 0:
                        for each_query in serialized_gsc_data["queries"]:
                            weekly_queries.append(
                                {
                                    "qry": each_query["query"],
                                    "cks": each_query["clicks"],
                                    "imps": each_query["impressions"],
                                }
                            )

                return JsonResponse({"st": 1, "wq": weekly_queries, "wqt": serialized_gsc_data["timeline"]})
        else:
            return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        print(e)
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# WEEKLY SEARCH PAGE WIDGET
@api_view(["POST"])
def weekly_search_page_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()

                if groupExists:
                    gsc_data = GSCWeeklyQuery.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).order_by("-created_date").first()
                    serialized_gsc_data = GSCWeeklyPageSerializer(gsc_data).data

                    if not serialized_gsc_data:
                        return JsonResponse({"st": 1, "wp": []})

                    weekly_pages = []
                    if len(serialized_gsc_data["pages"]) > 0:
                        for each_query in serialized_gsc_data["pages"]:
                            weekly_pages.append(
                                {
                                    "qry": each_query["query"],
                                    "cks": each_query["clicks"],
                                    "imps": each_query["impressions"],
                                }
                            )

                return JsonResponse({"st": 1, "wp": weekly_pages, "wpt": serialized_gsc_data["timeline"]})
        else:
            return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        print(e)
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# MONTHLY SEARCH QUERY WIDGET
@api_view(["POST"])
def monthly_search_query_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()

                if groupExists:
                    gsc_data = GSCMonthlyQuery.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).order_by("-created_date").first()
                    serialized_gsc_data = GSCMonthlyQuerySerializer(gsc_data).data

                    if not serialized_gsc_data:
                        return JsonResponse({"st": 1, "mq": []})

                    monthly_queries = []
                    if len(serialized_gsc_data["queries"]) > 0:
                        for each_query in serialized_gsc_data["queries"]:
                            monthly_queries.append(
                                {
                                    "qry": each_query["query"],
                                    "cks": each_query["clicks"],
                                    "imps": each_query["impressions"],
                                }
                            )

                return JsonResponse({"st": 1, "mq": monthly_queries, "mqt": serialized_gsc_data["timeline"]})
        else:
            return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        print(e)
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# MONTHLY SEARCH PAGE WIDGET
@api_view(["POST"])
def monthly_search_page_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()

                if groupExists:
                    gsc_data = GSCMonthlyQuery.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).order_by("-created_date").first()
                    serialized_gsc_data = GSCMonthlyPageSerializer(gsc_data).data

                    if not serialized_gsc_data:
                        return JsonResponse({"st": 1, "mp": []})

                    monthly_pages = []
                    if len(serialized_gsc_data["pages"]) > 0:
                        for each_query in serialized_gsc_data["pages"]:
                            monthly_pages.append(
                                {
                                    "qry": each_query["query"],
                                    "cks": each_query["clicks"],
                                    "imps": each_query["impressions"],
                                }
                            )

                return JsonResponse({"st": 1, "mp": monthly_pages, "mpt": serialized_gsc_data["timeline"]})
        else:
            return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        print(e)
        pass

    return JsonResponse({"st": 0, "dt": "Something went wrong"})


# Format this date
# def gsc_date_formatter(original_date, interval):
#     try: 
#         # Convert to datetime object
#         print(original_date)
#         dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S.%f%z") if interval == "M" else datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z")

#         # Format to the desired format
#         formatted_date = dt_object.strftime("%B %Y") if interval == "M" else dt_object.strftime("%d %b")

#         return formatted_date
#     except Exception as e:
#         print(e)
#         return ""
def gsc_date_formatter(original_date, interval):
    try:
        # print(original_date)

        if interval == "M":

            # Adjust to match the expected format
            # original_date = original_date.replace(" ", "T") + ".000000Z"

            # Parse using the expected format
            dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z")

            # Format to the desired format
            formatted_date = dt_object.strftime("%b %y")
        else:

            # original_date = original_date.replace(" ", "T") + ".000000Z"

            # Convert to datetime object
            dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z")

            # Format to the desired format
            formatted_date = dt_object.strftime("%d %b")

        return formatted_date
    except Exception as e:
        print(e)
        return ""


def get_overview_week_data(data, target_week, attr):
    for item in data:
        if item["week"] == target_week:
            return item[attr]
    return 0


def get_overview_month_data(data, target_week, attr):
    for item in data:
        if item["month"] == target_week:
            return item[attr]
    return 0


def calculate_percentage_difference(old_value, new_value):
    if old_value == 0:
        if new_value == 0:
            return "0%"
        else:
            return "100%"

    # Calculate the percentage difference
    percentage_difference = (new_value - old_value) / old_value * 100

    # Format the percentage difference with the plus or minus symbol and one decimal point
    formatted_percentage_difference = "{:+.1f}%".format(percentage_difference)

    return formatted_percentage_difference


def gsc_weekly_report(type, userId, grpId, branded_queries):
    try:
        gsc_data = (
            GSCWeeklyQuery.objects.filter(
                fk_group_id=int(grpId),
                fk_user_id=userId,
            )
            .values("id", "queries", "pages", "week_start_date", "week_end_date", "created_date")
            .order_by("-created_date")[:2]
        )
        serialized_gsc_data = GSCWeeklyQDataSerializer(gsc_data, many=True).data
        if not serialized_gsc_data:
            return [], []

        weekly_gsc_query_data = []
        for each_gsc_data in serialized_gsc_data:
            each_week = {}
            each_week["week"] = gsc_date_formatter(str(each_gsc_data["week_start_date"]), "W") + "-" + gsc_date_formatter(str(each_gsc_data["week_end_date"]), "W")
            each_week["queries"] = each_gsc_data["queries"] if type == "queries" else each_gsc_data["pages"]
            weekly_gsc_query_data.append(each_week)

        combined_data = {}
        overview_data = []

        # Get the week ranges
        week_ranges = [week_data["week"] for week_data in weekly_gsc_query_data]

        # Iterate through response data
        for week_data in weekly_gsc_query_data:
            kw_clicks = 0
            kw_impressions = 0
            brand_clicks = 0
            brand_impresions = 0
            non_brand_clicks = 0
            non_brand_impressions = 0
            for query_data in week_data.get("queries", []):

                query = query_data["query"]
                clicks = query_data.get("clicks", "NA")
                impressions = query_data.get("impressions", "NA")
                ctr = query_data.get("ctr", "NA")
                pos = query_data.get("position", "NA")

                if query not in combined_data:
                    combined_data[query] = {}

                branded_query = 0
                if query in branded_queries:
                    branded_query = 1

                kw_clicks += clicks
                kw_impressions += impressions

                if query in branded_queries:
                    brand_clicks += clicks
                    brand_impresions += impressions
                else:
                    non_brand_clicks += clicks
                    non_brand_impressions += impressions

                combined_data[query][week_data["week"]] = {"clicks": clicks, "impressions": impressions, "ctr": ctr, "position": pos, "branded": branded_query}

            overview_data.append({"week": week_data["week"], "clicks": kw_clicks, "impressions": kw_impressions, "brand_clicks": brand_clicks, "brand_impressions": brand_impresions, "non_brand_clicks": non_brand_clicks, "non_brand_impressions": non_brand_impressions}),

        # Format data for output
        output_data = []
        for query, week_data in combined_data.items():
            query_entry = {}
            for week in week_ranges:
                week_info = week_data.get(week, {"clicks": "NA", "impressions": "NA", "ctr": "NA", "position": "NA", "branded": 0})
                if type == "queries":
                    query_entry["Queries"] = "Brand" if query in branded_queries else "Non Brand"
                query_entry["Top queries"] = query
                query_entry[week + " Clicks"] = week_info["clicks"]
                query_entry[week + " Impressions"] = week_info["impressions"]
                query_entry[week + " CTR"] = week_info["ctr"]
                query_entry[week + " Position"] = week_info["position"]

            output_data.append(query_entry)

        overview_results = ["brand_clicks", "brand_impressions", "non_brand_clicks", "non_brand_impressions", "clicks", "impressions"]
        overview_names = ["Branded Clicks", "Branded Impressions", "Non Branded Clicks", "Non Branded Impressions", "Total Clicks", "Total Impressions"]
        search_over_view_result = []
        if len(weekly_gsc_query_data) > 0:
            for index, each_overiew in enumerate(overview_results):
                each_overiew_result = {}
                each_overiew_points = []
                each_overiew_result["Weekly Search Queries"] = overview_names[index]

                for index, week in enumerate(week_ranges):
                    each_overiew_result[week] = get_overview_week_data(overview_data, week, each_overiew)
                    each_overiew_points.append(get_overview_week_data(overview_data, week, each_overiew))

                each_overiew_result["Difference in %"] = calculate_percentage_difference(each_overiew_points[-2], each_overiew_points[-1]) if len(each_overiew_points) >= 2 else "0%"
                search_over_view_result.append(each_overiew_result)

        return output_data, search_over_view_result

    except Exception as e:
        return [], []
        
def is_branded_keyword(keyword, branded_keywords):
    for each_branded_keyword in branded_keywords:
        if each_branded_keyword in keyword:
            return True
    return False

def gsc_weekly_report_sub(type, userId, grpId, branded_queries, filter_options):
    try:
        isDesc = True if filter_options["order_by"] == "desc" else False
        three_days_ago = timezone.now() - timedelta(days=4)
        gsc_data = list(
            GSCWeeklyQuery.objects.filter(
                fk_group_id=int(grpId),
                fk_user_id=userId,
                week_end_date__lte=three_days_ago
            )
            .values("id", "queries", "pages", "week_start_date", "week_end_date", "overview", "created_date")
            .order_by("-week_start_date")[: filter_options["duration_limit"]]
        )
        gsc_data = sorted(gsc_data, key=itemgetter("week_start_date"), reverse=isDesc)
        serialized_gsc_data = GSCWeeklyQDataSerializer(gsc_data, many=True).data

        if not serialized_gsc_data:
            return [], [], []

        weekly_gsc_query_data = []
        for each_gsc_data in serialized_gsc_data:
            each_week = {}
            each_week["week"] = gsc_date_formatter(str(each_gsc_data["week_start_date"]), "W") + "-" + gsc_date_formatter(str(each_gsc_data["week_end_date"]), "W")
            each_week["queries"] = each_gsc_data["queries"] if type == "queries" else each_gsc_data["pages"]
            weekly_gsc_query_data.append(each_week)

        overview_data = []

        gsc_query_clicks = {}
        gsc_query_impressions = {}
        gsc_query_position = {}
        gsc_query_ctr = {}

        # Get the week ranges
        week_ranges = [week_data["week"] for week_data in weekly_gsc_query_data]

        # Iterate through response data
        for week_data in weekly_gsc_query_data:

            # Overview
            kw_clicks = 0
            kw_impressions = 0
            kw_ctr = 0

            brand_clicks = 0
            brand_impresions = 0
            brand_ctr = 0

            non_brand_clicks = 0
            non_brand_impressions = 0
            non_brand_ctr = 0

            for query_data in week_data.get("queries", []):
                query = query_data["query"]
                clicks = query_data.get("clicks", "NA")
                impressions = query_data.get("impressions", "NA")
                ctr = query_data.get("ctr", "NA")
                pos = query_data.get("position", "NA")

                if query not in gsc_query_clicks:
                    gsc_query_clicks[query] = {}
                    gsc_query_impressions[query] = {}
                    gsc_query_position[query] = {}
                    gsc_query_ctr[query] = {}

                kw_clicks += clicks
                kw_impressions += impressions
                kw_ctr += ctr

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    brand_clicks += clicks
                    brand_impresions += impressions
                    brand_ctr += ctr
                else:
                    non_brand_clicks += clicks
                    non_brand_impressions += impressions
                    non_brand_ctr += ctr

                gsc_query_clicks[query][week_data["week"]] = {"clicks": clicks}
                gsc_query_impressions[query][week_data["week"]] = {"impressions": impressions}
                gsc_query_position[query][week_data["week"]] = {"position": pos}
                gsc_query_ctr[query][week_data["week"]] = {"ctr": ctr}

            overview_data.append(
                {
                    "week": week_data["week"],
                    "clicks": kw_clicks,
                    "impressions": kw_impressions,
                    "ctr": kw_ctr,
                    "brand_clicks": brand_clicks,
                    "brand_impressions": brand_impresions,
                    "brand_ctr": brand_ctr,
                    "non_brand_clicks": non_brand_clicks,
                    "non_brand_impressions": non_brand_impressions,
                    "non_brand_ctr": non_brand_ctr,
                }
            )

        overall_branded_data = {}
        overall_non_branded_data = {}
        branded_id = 1
        non_branded_id = 1
        for query, week_data in gsc_query_clicks.items():
            query_entry = {}
            query_clicks = 0
            clicks_change = 0
            limit_click_sort = 0
            
            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                query_entry["Sr No"] = branded_id
                branded_id += 1
            else:
                query_entry["Sr No"] = non_branded_id
                non_branded_id += 1
                
            for week in week_ranges:
                week_info = week_data.get(week, {"clicks": "NA"})
                if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_click_sort < 2:
                    if week_info["clicks"] not in ["NA"]:
                        clicks_per_change = calculate_percentage_difference(query_clicks, week_info["clicks"])
                        clicks_change = week_info["clicks"] - query_clicks
                        query_clicks = week_info["clicks"]
                    else:
                        clicks_per_change = "0%"
                        clicks_change = 0

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    query_entry["Type"] = "Brand"
                    query_entry["Branded Queries"] = query
                elif type not in ["pages"] and not is_branded_keyword(query, branded_queries):
                    query_entry["Type"] = "Non-Brand"
                    query_entry["Non Branded Queries"] = query
                else:
                    query_entry["Pages"] = query

                if "clicks" in filter_options["metrics"]:
                    query_entry[week + " Clicks"] = week_info["clicks"]

                limit_click_sort = limit_click_sort + 1

            if "clicks" in filter_options["metrics"]:
                if "number" in filter_options["change_units"]:
                    query_entry["Click Change"] = reverse_sign(clicks_change) if filter_options["order_by"] == "desc" else clicks_change
                if "percentage" in filter_options["change_units"]:
                    query_entry["Click Change (%)"] = reverse_percentage(str(clicks_per_change)) if filter_options["order_by"] == "desc" else clicks_per_change

            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                overall_branded_data[query] = query_entry
            else:
                overall_non_branded_data[query] = query_entry

        if "impressions" in filter_options["metrics"]:
            for query, week_data in gsc_query_impressions.items():
                impressions_change = 0
                impressions_per_change = 0
                query_impressions = 0
                limit_imp_sort = 0
                for week in week_ranges:

                    week_info = week_data.get(week, {"impressions": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_imp_sort < 2:

                        if week_info["impressions"] not in ["NA"]:
                            impressions_per_change = calculate_percentage_difference(query_impressions, week_info["impressions"])
                            impressions_change = week_info["impressions"] - query_impressions
                            query_impressions = week_info["impressions"]
                        else:
                            impressions_per_change = "0%"
                            impressions_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][week + " Impressions"] = week_info["impressions"]
                    else:
                        overall_non_branded_data[query][week + " Impressions"] = week_info["impressions"]

                    limit_imp_sort = limit_imp_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["Impression Change"] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["Impression Change (%)"] = reverse_percentage(str(impressions_per_change)) if filter_options["order_by"] == "desc" else impressions_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Impression Change"] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Impression Change (%)"] = reverse_percentage(str(impressions_per_change)) if filter_options["order_by"] == "desc" else impressions_per_change

        if "position" in filter_options["metrics"]:
            for query, week_data in gsc_query_position.items():
                position_change = 0
                position_per_change = 0
                query_position = 0
                limit_pos_sort = 0
                for week in week_ranges:

                    week_info = week_data.get(week, {"position": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_pos_sort < 2:

                        if week_info["position"] not in ["NA"]:
                            position_per_change = calculate_percentage_difference(query_position, week_info["position"])
                            position_change = week_info["position"] - query_position
                            query_position = round(week_info["position"])
                            # print(query_position)
                        else:
                            position_per_change = "0%"
                            position_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][week + " Position"] = week_info["position"]
                    else:
                        overall_non_branded_data[query][week + " Position"] = week_info["position"]

                    limit_pos_sort = limit_pos_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["Position Change"] = reverse_sign(position_change) if filter_options["order_by"] == "desc" else position_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["Position Change (%)"] = reverse_percentage(str(position_per_change)) if filter_options["order_by"] == "desc" else position_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Position Change"] = reverse_sign(position_change) if filter_options["order_by"] == "desc" else position_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Position Change (%)"] = reverse_percentage(str(position_per_change)) if filter_options["order_by"] == "desc" else position_per_change

        if "ctr" in filter_options["metrics"]:
            for query, week_data in gsc_query_ctr.items():
                ctr_change = 0
                ctr_per_change = 0
                query_ctr = 0
                limit_ctr_sort = 0
                for week in week_ranges:

                    week_info = week_data.get(week, {"ctr": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_ctr_sort < 2:

                        if week_info["ctr"] not in ["NA"]:
                            ctr_per_change = calculate_percentage_difference(query_ctr, week_info["ctr"])
                            ctr_change = week_info["ctr"] - query_ctr
                            query_ctr = week_info["ctr"]
                        else:
                            ctr_per_change = "0%"
                            ctr_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][week + " ctr"] = week_info["ctr"]
                    else:
                        overall_non_branded_data[query][week + " ctr"] = week_info["ctr"]

                    limit_ctr_sort = limit_ctr_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["CTR Change"] = reverse_sign(ctr_change) if filter_options["order_by"] == "desc" else ctr_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["CTR Change (%)"] = reverse_percentage(str(ctr_per_change)) if filter_options["order_by"] == "desc" else ctr_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["CTR Change"] = reverse_sign(ctr_change) if filter_options["order_by"] == "desc" else ctr_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["CTR Change (%)"] = reverse_percentage(str(ctr_per_change)) if filter_options["order_by"] == "desc" else ctr_per_change

        overview_results = ["brand_clicks", "non_brand_clicks", "brand_impressions", "non_brand_impressions", "brand_ctr", "non_brand_ctr", "clicks", "impressions", "ctr"]
        overview_names = ["Branded Clicks", "Non Branded Clicks", "Branded Impressions", "Non Branded Impressions", "Branded CTR", "Non Branded CTR", "Total Clicks", "Total Impressions", "Total CTR"]
        search_over_view_result = []
        if len(weekly_gsc_query_data) > 0:
            for index, each_overiew in enumerate(overview_results):
                each_overiew_result = {}
                each_overiew_points = []
                each_overiew_result["Weekly Queries"] = overview_names[index]

                for index, week in enumerate(week_ranges):
                    each_overiew_result[week] = round(get_overview_week_data(overview_data, week, each_overiew))
                    each_overiew_points.append(get_overview_week_data(overview_data, week, each_overiew))

                each_overiew_result["Change in %"] = calculate_percentage_difference(each_overiew_points[-2], each_overiew_points[-1]) if len(each_overiew_points) >= 2 else "0%"
                search_over_view_result.append(each_overiew_result)

        return list(overall_branded_data.values()), list(overall_non_branded_data.values()), search_over_view_result
    except Exception as e:
        print(e)
        return [], [], []

def gsc_monthly_report(type, userId, grpId, branded_queries=[]):
    try:
        gsc_data = (
            GSCMonthlyQuery.objects.filter(
                fk_group_id=int(grpId),
                fk_user_id=userId,
            )
            .values("id", "queries", "pages", "month_start_date", "month_end_date", "created_date")
            .order_by("-created_date")[:2]
        )
        serialized_gsc_data = GSCMonthlyQDataSerializer(gsc_data, many=True).data
        if not serialized_gsc_data:
            return [], []
        monthly_gsc_query_data = []
        for each_gsc_data in serialized_gsc_data:
            each_month = {}
            each_month["month"] = gsc_date_formatter(str(each_gsc_data["month_start_date"]), "M")
            each_month["queries"] = each_gsc_data["queries"] if type == "queries" else each_gsc_data["pages"]
            monthly_gsc_query_data.append(each_month)

        combined_data = {}
        overview_data = []

        # Get the month ranges
        month_ranges = [month_data["month"] for month_data in monthly_gsc_query_data]

        # Iterate through response data
        for month_data in monthly_gsc_query_data:
            kw_clicks = 0
            kw_impressions = 0
            brand_clicks = 0
            brand_impresions = 0
            non_brand_clicks = 0
            non_brand_impressions = 0
            for query_data in month_data.get("queries", []):
                query = query_data["query"]
                clicks = query_data.get("clicks", "NA")
                impressions = query_data.get("impressions", "NA")
                ctr = query_data.get("ctr", "NA")
                pos = query_data.get("position", "NA")
                if query not in combined_data:
                    combined_data[query] = {}

                branded_query = 0
                if query in branded_queries:
                    branded_query = 1

                kw_clicks += clicks
                kw_impressions += impressions

                if query in branded_queries:
                    brand_clicks += clicks
                    brand_impresions += impressions
                else:
                    non_brand_clicks += clicks
                    non_brand_impressions += impressions

                combined_data[query][month_data["month"]] = {"clicks": clicks, "impressions": impressions, "ctr": ctr, "position": pos, "branded": branded_query}

            overview_data.append({"month": month_data["month"], "clicks": kw_clicks, "impressions": kw_impressions, "brand_clicks": brand_clicks, "brand_impressions": brand_impresions, "non_brand_clicks": non_brand_clicks, "non_brand_impressions": non_brand_impressions}),

        # Format data for output
        output_data = []
        for query, month_data in combined_data.items():
            query_entry = {}
            for month in month_ranges:
                month_info = month_data.get(month, {"clicks": "NA", "impressions": "NA", "ctr": "NA", "position": "NA", "branded": 0})
                if type == "queries":
                    query_entry["Queries"] = "Brand" if query in branded_queries else "Non Brand"
                query_entry["Top queries"] = query
                query_entry[month + " Clicks"] = month_info["clicks"]
                query_entry[month + " Impressions"] = month_info["impressions"]
                query_entry[month + " CTR"] = month_info["ctr"]
                query_entry[month + " Position"] = month_info["position"]

            output_data.append(query_entry)

        overview_results = ["brand_clicks", "brand_impressions", "non_brand_clicks", "non_brand_impressions", "clicks", "impressions"]
        overview_names = ["Branded Clicks", "Branded Impressions", "Non Branded Clicks", "Non Branded Impressions", "Total Clicks", "Total Impressions"]
        search_over_view_result = []
        if len(monthly_gsc_query_data) > 0:
            for index, each_overiew in enumerate(overview_results):
                each_overiew_result = {}
                each_overiew_points = []
                each_overiew_result["Monthly Search Queries"] = overview_names[index]

                for index, month in enumerate(month_ranges):
                    each_overiew_result[month] = get_overview_month_data(overview_data, month, each_overiew)
                    each_overiew_points.append(get_overview_month_data(overview_data, month, each_overiew))

                each_overiew_result["Difference in %"] = calculate_percentage_difference(each_overiew_points[-2], each_overiew_points[-1]) if len(each_overiew_points) >= 2 else "0%"
                search_over_view_result.append(each_overiew_result)

        return output_data, search_over_view_result

    except Exception as e:
        print(e)
        return [], []


def gsc_monthly_report_sub(type, userId, grpId, branded_queries, filter_options):
    try:
        isDesc = True if filter_options["order_by"] == "desc" else False
        three_days_ago = timezone.now() - timedelta(days=4)
        gsc_data = list(
            GSCMonthlyQuery.objects.filter(
                fk_group_id=int(grpId),
                fk_user_id=userId,
            )
            .values("id", "queries", "pages", "month_start_date", "month_end_date", "overview", "created_date")
            .order_by("-month_start_date")[: filter_options["duration_limit"]]
        )
        gsc_data = sorted(gsc_data, key=itemgetter("month_start_date"), reverse=isDesc)
        serialized_gsc_data = GSCMonthlyQDataSerializer(gsc_data, many=True).data
        if not serialized_gsc_data:
            return [], [], []

        monthly_gsc_query_data = []
        for each_gsc_data in serialized_gsc_data:
            each_month = {}
            each_month["month"] = gsc_date_formatter(str(each_gsc_data["month_start_date"]), "M")
            each_month["queries"] = each_gsc_data["queries"] if type == "queries" else each_gsc_data["pages"]
            monthly_gsc_query_data.append(each_month)

        overview_data = []

        gsc_query_clicks = {}
        gsc_query_impressions = {}
        gsc_query_position = {}
        gsc_query_ctr = {}

        # Get the month ranges
        month_ranges = [month_data["month"] for month_data in monthly_gsc_query_data]

        # Iterate through response data
        for month_data in monthly_gsc_query_data:
            # Overview
            kw_clicks = 0
            kw_impressions = 0
            kw_ctr = 0
            brand_clicks = 0
            brand_impresions = 0
            brand_ctr = 0
            non_brand_clicks = 0
            non_brand_impressions = 0
            non_brand_ctr = 0
            for query_data in month_data.get("queries", []):
                query = query_data["query"]
                clicks = query_data.get("clicks", "NA")
                impressions = query_data.get("impressions", "NA")
                ctr = query_data.get("ctr", "NA")
                pos = query_data.get("position", "NA")
                if query not in gsc_query_clicks:
                    gsc_query_clicks[query] = {}
                    gsc_query_impressions[query] = {}
                    gsc_query_position[query] = {}
                    gsc_query_ctr[query] = {}

                kw_clicks += clicks
                kw_impressions += impressions
                kw_ctr += ctr

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    brand_clicks += clicks
                    brand_impresions += impressions
                    brand_ctr += ctr
                else:
                    non_brand_clicks += clicks
                    non_brand_impressions += impressions
                    non_brand_ctr += ctr

                gsc_query_clicks[query][month_data["month"]] = {"clicks": clicks}
                gsc_query_impressions[query][month_data["month"]] = {"impressions": impressions}
                gsc_query_position[query][month_data["month"]] = {"position": pos}
                gsc_query_ctr[query][month_data["month"]] = {"ctr": ctr}

            overview_data.append(
                {
                    "month": month_data["month"],
                    "clicks": kw_clicks,
                    "impressions": kw_impressions,
                    "ctr": kw_ctr,
                    "brand_clicks": brand_clicks,
                    "brand_impressions": brand_impresions,
                    "brand_ctr": brand_ctr,
                    "non_brand_clicks": non_brand_clicks,
                    "non_brand_impressions": non_brand_impressions,
                    "non_brand_ctr": non_brand_ctr,
                }
            )

        # Format data for output
        overall_branded_data = {}
        overall_non_branded_data = {}
        branded_id = 1
        non_branded_id = 1
        for query, month_data in gsc_query_clicks.items():
            query_entry = {}
            query_clicks = 0
            clicks_change = 0
            limit_click_sort = 0

            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                query_entry["Sr No"] = branded_id
                branded_id += 1
            else:
                query_entry["Sr No"] = non_branded_id
                non_branded_id += 1

            for month in month_ranges:
                month_info = month_data.get(month, {"clicks": "NA", "impressions": "NA", "ctr": "NA", "position": "NA", "branded": 0})
                if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_click_sort < 2:
                    if month_info["clicks"] not in ["NA"]:
                        clicks_per_change = calculate_percentage_difference(query_clicks, month_info["clicks"])
                        clicks_change = month_info["clicks"] - query_clicks
                        query_clicks = month_info["clicks"]
                    else:
                        clicks_per_change = "0%"
                        clicks_change = 0

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    query_entry["Type"] = "Brand"
                    query_entry["Branded Queries"] = query
                elif type not in ["pages"] and (query, branded_queries):
                    query_entry["Type"] = "Non-Brand"
                    query_entry["Non Branded Queries"] = query
                else:
                    query_entry["Pages"] = query

                if "clicks" in filter_options["metrics"]:
                    query_entry[month + " Clicks"] = month_info["clicks"]

                limit_click_sort = limit_click_sort + 1

            if "clicks" in filter_options["metrics"]:
                if "number" in filter_options["change_units"]:
                    query_entry["Click Change"] = reverse_sign(clicks_change) if filter_options["order_by"] == "desc" else clicks_change
                if "percentage" in filter_options["change_units"]:
                    query_entry["Click Change (%)"] = reverse_percentage(str(clicks_per_change)) if filter_options["order_by"] == "desc" else clicks_per_change

            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                overall_branded_data[query] = query_entry
            else:
                overall_non_branded_data[query] = query_entry

        if "impressions" in filter_options["metrics"]:
            for query, month_data in gsc_query_impressions.items():
                impressions_change = 0
                impressions_per_change = 0
                query_impressions = 0
                limit_imp_sort = 0
                for month in month_ranges:
                    month_info = month_data.get(month, {"impressions": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_imp_sort < 2:
                        if month_info["impressions"] not in ["NA"]:
                            impressions_per_change = calculate_percentage_difference(query_impressions, month_info["impressions"])
                            impressions_change = month_info["impressions"] - query_impressions
                            query_impressions = month_info["impressions"]
                        else:
                            impressions_per_change = "0%"
                            impressions_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][month + " Impressions"] = month_info["impressions"]
                    else:
                        overall_non_branded_data[query][month + " Impressions"] = month_info["impressions"]

                    limit_imp_sort = limit_imp_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["Impression Change"] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["Impression Change (%)"] = reverse_percentage(str(impressions_per_change)) if filter_options["order_by"] == "desc" else impressions_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Impression Change"] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Impression Change (%)"] = reverse_percentage(str(impressions_per_change)) if filter_options["order_by"] == "desc" else impressions_per_change

        if "position" in filter_options["metrics"]:
            for query, month_data in gsc_query_position.items():
                position_change = 0
                position_per_change = 0
                query_position = 0
                limit_pos_sort = 0
                for month in month_ranges:
                    month_info = month_data.get(month, {"position": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_pos_sort < 2:
                        if month_info["position"] not in ["NA"]:
                            position_per_change = calculate_percentage_difference(query_position, month_info["position"])
                            position_change = month_info["position"] - query_position
                            query_position = month_info["position"]
                        else:
                            position_per_change = "0%"
                            position_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][month + " Position"] = month_info["position"]
                    else:
                        overall_non_branded_data[query][month + " Position"] = month_info["position"]

                    limit_pos_sort += 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["Position Change"] = reverse_sign(position_change) if filter_options["order_by"] == "desc" else position_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["Position Change (%)"] = reverse_percentage(str(position_per_change)) if filter_options["order_by"] == "desc" else position_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Position Change"] = reverse_sign(position_change) if filter_options["order_by"] == "desc" else position_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["Position Change (%)"] = reverse_percentage(str(position_per_change)) if filter_options["order_by"] == "desc" else position_per_change

        if "ctr" in filter_options["metrics"]:
            for query, month_data in gsc_query_ctr.items():
                ctr_change = 0
                ctr_per_change = 0
                query_ctr = 0
                limit_ctr_sort = 0
                for month in month_ranges:
                    month_info = month_data.get(month, {"ctr": "NA"})
                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_ctr_sort < 2:
                        if month_info["ctr"] not in ["NA"]:
                            ctr_per_change = calculate_percentage_difference(query_ctr, month_info["ctr"])
                            ctr_change = month_info["ctr"] - query_ctr
                            query_ctr = month_info["ctr"]
                        else:
                            ctr_per_change = "0%"
                            ctr_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][month + " CTR"] = month_info["ctr"]
                    else:
                        overall_non_branded_data[query][month + " CTR"] = month_info["ctr"]

                    limit_ctr_sort += 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query]["CTR Change"] = reverse_sign(ctr_change) if filter_options["order_by"] == "desc" else ctr_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query]["CTR Change (%)"] = reverse_percentage(str(ctr_per_change)) if filter_options["order_by"] == "desc" else ctr_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query]["CTR Change"] = reverse_sign(ctr_change) if filter_options["order_by"] == "desc" else ctr_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query]["CTR Change (%)"] = reverse_percentage(str(ctr_per_change)) if filter_options["order_by"] == "desc" else ctr_per_change

        overview_results = ["brand_clicks", "non_brand_clicks", "brand_impressions", "non_brand_impressions", "brand_ctr", "non_brand_ctr", "clicks", "impressions", "ctr"]
        overview_names = ["Branded Clicks", "Non Branded Clicks", "Branded Impressions", "Non Branded Impressions", "Branded CTR", "Non Branded CTR", "Total Clicks", "Total Impressions", "Total CTR"]
        search_over_view_result = []
        if len(monthly_gsc_query_data) > 0:
            for index, each_overiew in enumerate(overview_results):
                each_overiew_result = {}
                each_overiew_points = []
                each_overiew_result["Monthly Queries"] = overview_names[index]

                for index, month in enumerate(month_ranges):
                    each_overiew_result[month] = math.floor(get_overview_month_data(overview_data, month, each_overiew) * 100) / 100
                    each_overiew_points.append(get_overview_month_data(overview_data, month, each_overiew))

                each_overiew_result["Change in %"] = calculate_percentage_difference(each_overiew_points[-2], each_overiew_points[-1]) if len(each_overiew_points) >= 2 else "0%"
                search_over_view_result.append(each_overiew_result)

        return list(overall_branded_data.values()), list(overall_non_branded_data.values()), search_over_view_result

    except Exception as e:
        print(e)
        return [], [], []


# BASE METRICS
def seo_metrics(userId, grpId):
    try:
        metrics_data = DomainTracking.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).values("da_metrics", "dr_metrics").first()
        serialized_metrics_data = DomainTrackSerializer(metrics_data).data

        if not serialized_metrics_data:
            return []

        monthly_da_metrics = {"Parameters": "Domain Authority(MOZ)"}
        for each_data in serialized_metrics_data["da_metrics"]:
            month, year = each_data["month"].split()
            month_abbr = month[:3].upper()
            year_abbr = year[2:]
            monthly_da_metrics[f"{month_abbr}'{year_abbr}"] = each_data["value"]

        monthly_dr_metrics = {"Parameters": "Domain Rating(AHREFs)"}
        for each_data in serialized_metrics_data["dr_metrics"]:
            month, year = each_data["month"].split()
            month_abbr = month[:3].upper()
            year_abbr = year[2:]
            monthly_dr_metrics[f"{month_abbr}'{year_abbr}"] = each_data["value"]

        return [monthly_da_metrics, monthly_dr_metrics]

    except Exception as e:
        return []

def generate_monthly_metrics(monthly_data, metric_type, filter_options, metric_key, metric_name):
    monthly_metrics = {}
    metric_difference = 0
    percentage_diff = 0
    metric_difference = 0
    # if metric_type in ["da", "dr"]:
    #     monthly_metrics["Area"] = "Authority"
    # elif metric_type in ["backlinks", "ref_domains"]:
    #     monthly_metrics["Area"] = "Backlinks"
    # else:
    #     monthly_metrics["Area"] = "Website Usability"

    monthly_metrics["Key SEO Metrics"] = metric_name
    prev_value = 0
    for data in monthly_data:

        month, year = data["month"].split()
        month_abbr = month[:3].upper()
        year_abbr = year[2:]
        monthly_metrics[f"{month_abbr}'{year_abbr}"] = data[metric_key]

        if not data[metric_key] == "NA" and not prev_value == "NA" and not isinstance(data[metric_key], str):
            metric_difference = data[metric_key] - prev_value
            percentage_diff = calculate_percentage_difference(prev_value, data[metric_key])

        prev_value = data[metric_key]

    if "number" in filter_options["change_units"]:
        monthly_metrics["MOM Change"] = metric_difference if filter_options["order_by"] == "asc" else reverse_sign(metric_difference)
    if "percentage" in filter_options["change_units"]:
        monthly_metrics["MOM Change (%)"] = percentage_diff if filter_options["order_by"] == "asc" else reverse_percentage(percentage_diff)

    return monthly_metrics

def seo_metrics_sub(userId, grpId, filter_options):
    try:
        seo_metrics = list()
        metrics_data = DomainTracking.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).values("da_metrics", "dr_metrics").first()
        serialized_metrics_data = DomainTrackSerializer(metrics_data, context={"order_by": filter_options["order_by"]}).data

        if len(serialized_metrics_data["da_metrics"]) == 0 and len(serialized_metrics_data["dr_metrics"]) == 0:
            return []

        da_metrics = generate_monthly_metrics(serialized_metrics_data["da_metrics"][: filter_options["duration_limit"]], "da", filter_options, "value", "Domain Authority (MOZ)")
        seo_metrics.append(da_metrics)

        dr_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "dr", filter_options, "value", "Domain Rating (AHREFs)")
        seo_metrics.append(dr_metrics)

        backlinks_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "backlinks", filter_options, "backlinks", "Number of Backlinks (AHREFs)")
        seo_metrics.append(backlinks_metrics)

        ref_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "ref_domains", filter_options, "ref_domains", "Referring Domains (AHREFs)")
        seo_metrics.append(ref_metrics)

        return seo_metrics

    except Exception as e:
        print('domain_metrics' ,str(e))
        print(e.args)
        return []

# def seo_metrics_sub(userId, grpId, filter_options):
#     try:
#         seo_metrics = list()
#         metrics_data = DomainTracking.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).values("da_metrics", "dr_metrics").first()
#         serialized_metrics_data = DomainTrackSerializer(metrics_data, context={"order_by": filter_options["order_by"]}).data

#         if len(serialized_metrics_data["da_metrics"]) == 0 and len(serialized_metrics_data["dr_metrics"]) == 0:
#             return []

#         monthly_da_metrics = {}
#         da_difference = 0
#         da_difference_ratio = 0
#         domain_authority = 0

#         for each_data in serialized_metrics_data["da_metrics"][: filter_options["duration_limit"]]:
#             month, year = each_data["month"].split()
#             month_abbr = month[:3].upper()
#             year_abbr = year[2:]
#             da_difference = each_data["value"] - domain_authority
#             da_difference_ratio = calculate_percentage_difference(domain_authority, each_data["value"])
#             domain_authority = each_data["value"]
#             monthly_da_metrics["Key SEO Metrics"] = "Domain Authority (MOZ)"
#             monthly_da_metrics[f"{month_abbr}'{year_abbr}"] = each_data["value"]

#         if "number" in filter_options["change_units"]:
#             monthly_da_metrics["MOM Change"] = da_difference if filter_options["order_by"] == "asc" else reverse_sign(da_difference)
#         if "percentage" in filter_options["change_units"]:
#             monthly_da_metrics["MOM Change (%)"] = da_difference_ratio if filter_options["order_by"] == "asc" else reverse_percentage(da_difference_ratio)

#         if monthly_da_metrics:
#             seo_metrics.append(monthly_da_metrics)

#         monthly_dr_metrics = {}
#         dr_difference = 0
#         dr_difference_ratio = 0
#         domain_rating = 0
#         for each_data in serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]]:
#             month, year = each_data["month"].split()
#             month_abbr = month[:3].upper()
#             year_abbr = year[2:]
#             dr_difference = each_data["value"] - domain_rating
#             dr_difference_ratio = calculate_percentage_difference(domain_rating, each_data["value"])
#             domain_rating = each_data["value"]
#             monthly_dr_metrics["Key SEO Metrics"] = "Domain Rating (AHREFs)"
#             monthly_dr_metrics[f"{month_abbr}'{year_abbr}"] = each_data["value"]
#         if "number" in filter_options["change_units"]:
#             monthly_dr_metrics["MOM Change"] = dr_difference if filter_options["order_by"] == "asc" else reverse_sign(dr_difference)
#         if "percentage" in filter_options["change_units"]:
#             monthly_dr_metrics["MOM Change (%)"] = dr_difference_ratio if filter_options["order_by"] == "asc" else reverse_percentage(dr_difference_ratio)
        
#         if monthly_dr_metrics:
#             seo_metrics.append(monthly_dr_metrics)

#         monthly_bclnks_metrics = {}
#         bclnks_difference = 0
#         bclnks_difference_ratio = 0
#         domain_bclnks = 0
#         for each_data in serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]]:
#             if 'backlinks' in each_data:
#                 month, year = each_data["month"].split()
#                 month_abbr = month[:3].upper()
#                 year_abbr = year[2:]
#                 bclnks_difference = each_data["backlinks"] - domain_bclnks
#                 bclnks_difference_ratio = calculate_percentage_difference(domain_bclnks, each_data["backlinks"])
#                 domain_bclnks = each_data["backlinks"]
#                 monthly_bclnks_metrics["Key SEO Metrics"] = "Number of Backlinks (AHREFs)"
#                 monthly_bclnks_metrics[f"{month_abbr}'{year_abbr}"] = each_data.get("backlinks", 'NA')
#                 if "number" in filter_options["change_units"]:
#                     monthly_bclnks_metrics["MOM Change"] = bclnks_difference if filter_options["order_by"] == "asc" else reverse_sign(bclnks_difference)
#                 if "percentage" in filter_options["change_units"]:
#                     monthly_bclnks_metrics["MOM Change (%)"] = bclnks_difference_ratio if filter_options["order_by"] == "asc" else reverse_percentage(bclnks_difference_ratio)
        
#         if monthly_bclnks_metrics:
#             seo_metrics.append(monthly_bclnks_metrics)

#         monthly_ref_metrics = {}
#         ref_difference = 0
#         ref_difference_ratio = 0
#         ref_bclnks = 0
#         for each_data in serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]]:
#             if 'ref_domains' in each_data:
#                 month, year = each_data["month"].split()
#                 month_abbr = month[:3].upper()
#                 year_abbr = year[2:]
#                 ref_difference = each_data["ref_domains"] - ref_bclnks
#                 ref_difference_ratio = calculate_percentage_difference(ref_bclnks, each_data["ref_domains"])
#                 ref_bclnks = each_data["ref_domains"]
#                 monthly_ref_metrics["Key SEO Metrics"] = "Referring Domains (AHREFs)"
#                 monthly_ref_metrics[f"{month_abbr}'{year_abbr}"] = each_data["ref_domains"]
#                 if "number" in filter_options["change_units"]:
#                     monthly_ref_metrics["MOM Change"] = ref_difference if filter_options["order_by"] == "asc" else reverse_sign(ref_difference)
#                 if "percentage" in filter_options["change_units"]:
#                     monthly_ref_metrics["MOM Change (%)"] = ref_difference_ratio if filter_options["order_by"] == "asc" else reverse_percentage(ref_difference_ratio)

#         if monthly_ref_metrics:
#             seo_metrics.append(monthly_ref_metrics)

#         return seo_metrics

#     except Exception as e:
#         print('domain_metrics' ,str(e))
#         return []

def formatted_date(date):
    return date.strftime("%d %b")


def ga_overview(userid, grpid, param):
    try:
        ga_weekly = None
        if param == "week":
            ga_weekly = GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("overview", "id", "start_date", "end_date", "created_date").order_by("-created_date")[:3]
        elif param == "month":
            ga_weekly = GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("overview", "id", "start_date", "end_date", "created_date").order_by("-created_date")[:3]

        result = {}
        if ga_weekly:
            for index, data in enumerate(ga_weekly):
                week_date_range = f"{formatted_date(data['start_date'])} - {formatted_date(data['end_date'])}"
                category_sessions = []
                trffics = list(map(lambda x: x["session"], data["overview"]))
                total_trffics = functools.reduce(lambda a, b: a + b, trffics)
                category_sessions.append(total_trffics)
                for i, category_data in enumerate(data["overview"]):
                    if category_data["value"] == "Organic Search":
                        category_sessions.append(category_data["session"])
                        organic_share = category_data["session"] / total_trffics * 100
                        category_sessions.append(f"{round(organic_share)}%")

                        if len(ga_weekly) > index + 1:
                            print("IS")
                            li = list(filter(lambda x: x["value"] == "Organic Search", ga_weekly[index + 1]["overview"]))
                            in_change = (category_data["session"] - li[0]["session"]) / li[0]["session"] * 100
                            category_sessions.append(f"{round(in_change)}%")
                        else:
                            category_sessions.append("-")
                result[week_date_range] = category_sessions

        return result

    except Exception as e:
        print(str(e))
        return {}

def op_identifier(value):
    if value<0:
        return value
    elif value>0:
        return f"{value} ~~"

def ga_overview_sub(userid, grpid, param, filter_options):
    try:
        ga_weekly = None
        three_days_ago = timezone.now() - timedelta(days=4)
        if param == "week":
            ga_weekly = list(GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[: filter_options["duration_limit"]])
        elif param == "month":
            ga_weekly = list(GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[: filter_options["duration_limit"]])

        isDesc = True if filter_options["order_by"] == "desc" else False

        overview_data = {}
        overview_data["sessions"] = {"Organic Metrics": "Sessions"}
        # overview_data["users"] = {"Organic Metrics": "Users"}
        overview_data['engaged_sessions'] = {"Organic Metrics": "EngagedSessions"}
        overview_data["engagement_rate"] = {"Organic Metrics": "Engagement Rate (%)"}
        overview_data["bounce_rate"] = {"Organic Metrics": "Bounce Rate (%)"}
        # overview_data["time_spent"] = {"Organic Metrics": "Time Spent (Min)"}
        overview_data["session_change"] = {"Organic Metrics": "Session Change"}
        overview_data["organic_share"] = {"Organic Metrics": "Organic Share in (%)"}

        if not ga_weekly:
            print('ga error')
            return {}
        else:
            ga_weekly = sorted(ga_weekly, key=itemgetter("start_date"), reverse=isDesc)
            organic_sessions = 0
            session_difference = 0
            for index, data in enumerate(ga_weekly):
                if param == "week":
                    duration = f"{formatted_date(data['start_date'])} - {formatted_date(data['end_date'])}"
                else:
                    duration = f"{formatted_date(data['end_date'])}"

                overall_sessions = list(map(lambda x: x["session"], data["overview"]))
                # print(overall_sessions)
                total_sessions = 0
                if len(overall_sessions)>0:
                    total_sessions = functools.reduce(lambda a, b: int(a) + int(b), overall_sessions)
                # print(total_sessions)
                for i, category_data in enumerate(data["overview"]):
                    if category_data["value"] == "Organic Search":
                        # print(category_data['engaged_sessions'])
                        session_difference = int(category_data["session"]) - organic_sessions if index!=0 else 'NA'
                        organic_sessions = int(category_data["session"])
                        overview_data["sessions"][duration] = int(category_data["session"]) if "session" in category_data else "NA"
                        # overview_data["users"][duration] = int(category_data["users"]) if "users" in category_data else "NA"
                        # overview_data['engaged_sessions'] = int(category_data['engaged_sessions']) if 'engaged_sessions' in category_data else 'NA'
                        overview_data['engaged_sessions'][duration] = category_data['engaged_sessions'] if 'engaged_sessions' in category_data else 'NA'
                        overview_data["bounce_rate"][duration] = category_data['bounce_rate'] if 'bounce_rate' in category_data else 'NA'#round(int(category_data["purchase_event"]) * 100) if "purchase_event" in category_data else "NA"
                        overview_data["engagement_rate"][duration] = category_data['engagement_rate'] if 'engagement_rate' in category_data else 'NA' #round(float(category_data["eg_rate"]) * 100) if "eg_rate" in category_data else "NA"
                        # overview_data["time_spent"][duration] = int(category_data["event_count"]) if "event_count" in category_data else "NA"
                        overview_data["session_change"][duration] = op_identifier(session_difference) if session_difference!='NA' else session_difference
                        overview_data["organic_share"][duration] = round(int(category_data["session"]) / int(total_sessions) * 100) if "session" in category_data else "NA"

            return list(overview_data.values())
    except Exception as e:
        print(str(e))
        return {}


def landing_page_report(userid, grpid):
    try:
        ga_weekly = GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("landing_page", "id", "start_date", "end_date", "created_date").order_by("-created_date")[:3]
        result = {}
        for index, data in enumerate(ga_weekly):
            week_date_range = f"{formatted_date(data['start_date'])} - {formatted_date(data['end_date'])}"
            di = {"Landing Page": [], "Sessions": []}
            for i, category_data in enumerate(data["landing_page"]):
                di["Landing Page"].append(category_data["value"])
                di["Sessions"].append(category_data["session"])
            result[week_date_range] = di
        return result
    except Exception as e:
        print(str(e))
        return {}

def landing_page_report_sub(userid, grpid, filter_options):
    try:
        isDesc = True if filter_options["order_by"] == "desc" else False

        three_days_ago = timezone.now() - timedelta(days=4)
        
        rec_limit = 2 if filter_options['duration_limit']==1 else filter_options['duration_limit']

        if 'weekly' in filter_options['duration']:
            ga_weekly = list(GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("landing_page", "id", "start_date", "end_date", "created_date").order_by("-start_date")[: rec_limit])
        else:
            ga_weekly = list(GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("landing_page", "id", "start_date", "end_date", "created_date").order_by("-start_date")[: rec_limit])
        ga_weekly = sorted(ga_weekly, key=itemgetter("start_date"), reverse=isDesc)
        result = {}

        if not ga_weekly:
            return result

        weekly_ga_landing_pages = []
        overall_ga_landing_pages = {}
        for index, each_ga_page in enumerate(ga_weekly):
            each_week = {}
            each_week["week"] = f"{formatted_date(each_ga_page['start_date'])} - {formatted_date(each_ga_page['end_date'])}"
            each_week["landing_pages"] = each_ga_page["landing_page"]
            weekly_ga_landing_pages.append(each_week)

        week_ranges = [each_week["week"] for each_week in weekly_ga_landing_pages]
        ga_landing_pages = {}

        for week_data in weekly_ga_landing_pages:
            for query_data in week_data.get("landing_pages", []):
                path = query_data["value"]
                session = query_data.get("session", None)
                if path not in ga_landing_pages:
                    ga_landing_pages[path] = {}
                ga_landing_pages[path][week_data["week"]] = {"sessions": session}

        # print(ga_landing_pages)

        for path, week_data in ga_landing_pages.items():
            path_ga_data = {}
            previous_session = None
            last_session = None
            session_difference = "NA"
            session_difference_ratio = "NA"
            comparison_done=True
            for index, week in enumerate(week_ranges):
                week_info = week_data.get(week, {"sessions": "NA"})
                if filter_options['duration_limit']==1:
                    if isDesc and index==0:
                        path_ga_data["Landing Pages"] = path
                        path_ga_data[week] = week_info["sessions"]
                    elif not isDesc and index==1:
                        path_ga_data["Landing Pages"] = path
                        path_ga_data[week] = week_info["sessions"]
                else:
                    path_ga_data["Landing Pages"] = path
                    path_ga_data[week] = week_info["sessions"]

                if week_info["sessions"] not in ["NA", None]:
                    last_session = int(week_info["sessions"])
                
                if isDesc:
                    if comparison_done:
                        if previous_session is not None and last_session is not None and comparison_done:
                            session_difference = previous_session - last_session
                            session_difference_ratio = calculate_percentage_difference(last_session, previous_session)
                            comparison_done=False
                        else:
                            session_difference = "NA"
                            session_difference_ratio = "NA"
                else:
                    if previous_session is not None and last_session is not None:
                        session_difference = last_session - previous_session
                        session_difference_ratio = calculate_percentage_difference(previous_session, last_session)
                    else:
                        session_difference = "NA"
                        session_difference_ratio = "NA"

                previous_session = last_session if last_session not in ["NA", None] else None

            if 'percentage' in filter_options['change_units'] or 'number' in filter_options['change_units']:

                if "percentage" in filter_options["change_units"]:
                    path_ga_data["Change (%)"] = session_difference_ratio

                if "number" in filter_options["change_units"]:
                    path_ga_data["Change"] = session_difference
            else:
                path_ga_data["Change (%)"] = session_difference_ratio
                path_ga_data["Change"] = session_difference

            overall_ga_landing_pages[path] = path_ga_data

        if not overall_ga_landing_pages:
            return {}

        return list(overall_ga_landing_pages.values())

    except Exception as e:
        print(f"Error: {e}")
        return {}



# EXPORT
@api_view(["POST"])
def gsc_export(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])
            if userId.isdigit() and grpId.isdigit():
                group_data = Groups.objects.filter(fk_user_id=userId, id=grpId).first()
                if group_data:
                    branded_queries = group_data.brand_keywords if group_data.brand_keywords else []
                    gsc_weekly_queries, search_query_weekly_overview = gsc_weekly_report("queries", userId, grpId, branded_queries)
                    gsc_weekly_pages, search_page_weekly_overview = gsc_weekly_report("pages", userId, grpId, branded_queries)

                    gsc_monthly_queries, search_query_monthly_overview = gsc_monthly_report("queries", userId, grpId, branded_queries)
                    gsc_monthly_pages, search_page_monthly_overview = gsc_monthly_report("pages", userId, grpId, branded_queries)

                    base_metrics = seo_metrics(userId, grpId)

                    ga_weekly_report = ga_overview(userId, grpId, "week")

                    ga_monthly_report = ga_overview(userId, grpId, "month")

                    weekly_lndng_pg_report = landing_page_report(userId, grpId)

                    rp_score, rp_keywords = rp_keywords_table(userId, grpId)

                    return JsonResponse(
                        {
                            "st": 1,
                            "kov": rp_score,
                            "krd": rp_keywords,
                            "weekly_lndng_pg_report": weekly_lndng_pg_report,
                            "ga_monthly_report": ga_monthly_report,
                            "ga_weekly_report": ga_weekly_report,
                            "wsq": gsc_weekly_queries,
                            "sqwo": search_query_weekly_overview,
                            "wsp": gsc_weekly_pages,
                            "msq": gsc_monthly_queries,
                            "sqmo": search_query_monthly_overview,
                            "msp": gsc_monthly_pages,
                            "bmt": base_metrics,
                        }
                    )
                else:
                    return JsonResponse({"st": 0, "message": "Something went wrong"})
            else:
                return JsonResponse({"st": 0, "message": "Something went wrong"})
        else:
            return JsonResponse({"st": 0, "message": "Something went wrong"})
    except Exception as e:
        print(e)
        return JsonResponse({"st": 0, "message": "Something went wrong"})


@api_view(["POST"])
def ga_landing_page_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = request.data["userid"]
            grpid = request.data["grpid"]

            if userid.isdigit() and grpid.isdigit():
                ga_weekly_report = GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by("-created_date").values("landing_page", "start_date", "end_date").first()

                if not ga_weekly_report:
                    return JsonResponse({"st": 0, "dt": []})

                start_date = formatted_date(ga_weekly_report["start_date"])
                end_date = formatted_date(ga_weekly_report["end_date"])

                timeline = f"{start_date} - {end_date}"

                data = list()
                for i in ga_weekly_report["landing_page"]:
                    data.append(i)

                return JsonResponse({"st": 1, "dt": data, "tmln": timeline})
        return JsonResponse({"st": 0, "dt": [], "msg": "Something went wrong"})

    except Exception as e:
        print(str(e))
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


def remove_empty_keys(data):
    for entry in data:
        if "" in entry:
            del entry[""]
    return data


def calculation_score(score_calc, category, index, f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12):
    if category == f_base:
        score_calc[index][category] += 1
    elif category == f_last_index:
        score_calc[index][category] += 1
    elif category == s_last_index:
        score_calc[index][category] += 1
    elif category == t_last_index:
        score_calc[index][category] += 1
    elif category == fr_last_index:
        score_calc[index][category] += 1
    elif category == fv_last_index:
        score_calc[index][category] += 1
    elif category == sx_last_index:
        score_calc[index][category] += 1
    elif category == se_last_index:
        score_calc[index][category] += 1
    elif category == egt_last_index:
        score_calc[index][category] += 1
    elif category == last_index_5:
        score_calc[index][category] += 1
    elif category == last_index_7:
        score_calc[index][category] += 1
    elif category == last_index_9:
        score_calc[index][category] += 1
    elif category == last_index_10:
        score_calc[index][category] += 1
    elif category == last_index_11:
        score_calc[index][category] += 1
    elif category == last_index_12:
        score_calc[index][category] += 1

    return score_calc

def transform_asc(data):
    try:
        asc_data=list()
        diff_item=list(data[0].keys())[len(data[0].keys())-1]
        for each_data in data:
            ov_date_keys = sorted([key for key in each_data.keys() if key not in ['primary keyword ranking', 'Base Ranking', diff_item]], key=lambda x: (di[x.split(' ')[1]] if x!='' else x, con_int(x.split(' ')[0]) if x!='' else x))
            returned_data = {key: each_data[key] if key in each_data.keys() else '' for key in reorder(list({'primary keyword ranking', 'Base Ranking'}.intersection(set(each_data.keys()))), ['primary keyword ranking', 'Base Ranking']) + ov_date_keys + [diff_item]}
            asc_data.append(returned_data)
        return asc_data
    except Exception as e:
        print('TESTING',str(e))
        return []

def keywords_overview(f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12, group_data):
    try:

        c_past_index = f_last_index + " vs " + s_last_index

        score_calc = [
            {
                "primary keyword ranking": "Top 5",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 6 - 10",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 11 - 20",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 21 - 30",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 31 - 50",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Above 50",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Total Keywords",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
            },
        ]

        if group_data:
            # TOP TOTAL CALCULATION FOR EACH COLUMN
            for single_data in group_data:
                for x in single_data:
                    if x in [
                        f_base,
                        f_last_index,
                        s_last_index,
                        t_last_index,
                        fr_last_index,
                        fv_last_index,
                        sx_last_index,
                        se_last_index,
                        egt_last_index,
                        last_index_5,
                        last_index_7,
                        last_index_9,
                        last_index_10,
                        last_index_11,
                        last_index_12,
                    ]:

                        if str(single_data[x]).isdigit() and f_base and f_last_index and s_last_index and t_last_index:
                            if single_data[x] >= 1 and single_data[x] <= 5:
                                cal_index = 0
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 6 and single_data[x] <= 10:
                                cal_index = 1
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 11 and single_data[x] <= 20:
                                cal_index = 2
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 21 and single_data[x] <= 30:
                                cal_index = 3
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 31 and single_data[x] <= 50:
                                cal_index = 4
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 51:
                                cal_index = 5
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )

            # TOTAL KEYWORDS CALCULATION ON EACH DATE (BASE AND 3 WEEKS DATE)
            for xy in [
                f_base,
                f_last_index,
                s_last_index,
                t_last_index,
                fr_last_index,
                fv_last_index,
                sx_last_index,
                se_last_index,
                egt_last_index,
                last_index_5,
                last_index_7,
                last_index_9,
                last_index_10,
                last_index_11,
                last_index_12,
            ]:
                total_value = 0
                for x in range(0, len(score_calc) - 1):
                    total_value += score_calc[x][xy]

                # TOTAL KEYWORDS CALCULATE
                score_calc[6][xy] = total_value

            # VALUE COMPARSION CALCULATION FOR PAST TWO WEEKS
            for up_stream in range(0, len(score_calc) - 1):
                diff_value = score_calc[up_stream][f_last_index] - score_calc[up_stream][s_last_index]
                score_calc[up_stream][c_past_index] = diff_value

        asc_list = transform_asc(score_calc)
        return asc_list if asc_list else score_calc
    except Exception as e:
        return []

def week_classify_rank(rank):
    if 1 <= rank <= 5:
        return 'Top 5'
    elif 6 <= rank <= 10:
        return 'Top 6 - 10'
    elif 11 <= rank <= 20:
        return 'Top 11 - 20'
    elif 21 <= rank <= 30:
        return 'Top 21 - 30'
    elif 31 <= rank <= 50:
        return 'Top 31 - 50'
    else:
        return 'Above 50'

def base_rank_week_counter(keywords, result):
    try:
        category_counts = {'Top 5':0, 'Top 6 - 10':0, 'Top 11 - 20':0, 'Top 21 - 30':0, 'Top 31 - 50':0, 'Above 50':0}
        result = result
        # print(result)
        for rank_obj in keywords:
            rank_category = week_classify_rank(rank_obj['rank_sincestart'])
            category_counts[rank_category] += 1
        
        for res_obj in result:
            category = res_obj['primary keyword ranking']
            if category in category_counts:
                res_obj['Base Ranking'] = category_counts[category]

    except Exception as e:
        print(str(e))
    return result

def base_rank_counter(keywords, result):
    try:
        category_counts = {'top 5':0, '6 to 10':0, '11 to 20':0, '21 to 30':0, '31 to 50':0, '51 to 100':0, 'not in 100':0}
        result = result
        # print(result)
        for rank_obj in keywords:
            rank_category = classify_rank(rank_obj['rank_sincestart'])
            category_counts[rank_category] += 1
        
        for res_obj in result:
            category = res_obj['primary keyword ranking']
            if category in category_counts:
                res_obj['Base Ranking'] = category_counts[category]

    except Exception as e:
        print(str(e))
    return result
    
def monthly_keywords_overview(user_id, group_id, filter_options):
    try:
        if user_id and group_id:
            page_filter={"fk_user_id": user_id, "fk_group_id": group_id}
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")
            grp = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('created_date').first()
            end_of_cr_date = grp['created_date'].replace(hour=23, minute=59, second=59, microsecond=999999)
            base_keywords = list(Keyword.objects.filter(fk_user_id=user_id, fk_group_id=group_id, created_date__lte=end_of_cr_date).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id"))
            if keywords:
                serializer=KeywordMonthlyOverviewSerializer(keywords, many=True, context={'filter_options':filter_options}).data
                categories = ['top 5', '6 to 10', '11 to 20', '21 to 30', '31 to 50', '51 to 100', 'not in 100']
                counts=dict()
                all_dates = set()
                for entry in serializer:
                    all_dates.update(entry.keys())
                sortable_date = list(all_dates)
                sortable_date.sort(key=lambda date:datetime.strptime(date,"%b/%Y"))
                for category in categories:
                    counts[category] = {date: 0 for date in sortable_date}
                for entry in serializer:
                    for date, category in entry.items():
                        if category in counts:
                            counts[category][date] += 1
                result = []
                for category, date_counts in counts.items():
                    category_entry = {'primary keyword ranking': category, 'Base Ranking':0}
                    category_entry.update(date_counts)
                    result.append(category_entry)
                    # print(returned_data)

                base_result = base_rank_counter(base_keywords, result)
                for entry in base_result:
                    keys=list(entry.keys())[::-1][0:2]
                    val=0
                    # print(keys)
                    fil_key = list(filter(lambda x: x not in ['primary keyword ranking', 'Base Ranking'], keys))
                    if len(fil_key)>1:
                        for i in fil_key:
                                val=entry.get(i)-val
                    else:
                        val=0
                    entry['MOM Change']=-val
                
                total_keywords = {'primary keyword ranking': 'Total keywords'}
                for entry in base_result:
                    for key, value in entry.items():
                        if key not in ('primary keyword ranking', 'MOM Change'):
                            total_keywords[key] = total_keywords.get(key, 0) + value

                base_result.append(total_keywords)
                return base_result
            else:
                print('err1')
                return []
        else:
            print('err2')
            return []
    except Exception as e:
        # print(str(e))
        log_exception('monthly_keywords_overview', e)

def keyword_monthly_ranking_report(user_id, group_id, filter_options):
    try:
        if user_id and group_id:

            page_filter = {"fk_user_id": user_id, "fk_group_id": group_id}
            GrpIns = Groups.objects.filter(Q(id=group_id), fk_user_id=user_id).values("domain_name", "score_meter", "gsc_last_track").first()
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")

            if keywords and GrpIns:
                serializer=KeywordRankingMonthlySerializer(
                    keywords, 
                    many=True, 
                    context={
                        "dn": GrpIns["domain_name"],
                        "filter_options":filter_options
                        }).data
                unique_dates = set()
                for entry in serializer:
                    unique_dates.update(entry.keys())
                desc_date_list = list(filter(lambda x: x not in ['Base Ranking', 'Keyword', 'Avg. Volume', 'MOM Change', 'Landing Pages'], unique_dates))
                desc_date_list.sort(key=lambda date:datetime.strptime(date, "%b/%Y"), reverse=True)

                normalized_data = []
                for entry in serializer:
                    normalized_entry = {date: entry.get(date, 'NA') for date in unique_dates}
                    normalized_data.append(normalized_entry)
                asc_data=list()
                if filter_options['order_by']=='asc':
                    for each_data in normalized_data:
                        returned_data = {key: each_data[key] if key in each_data.keys() else '' for key in reorder(normalized_data[0].keys(), serializer[0].keys())}
                        # print(returned_data)
                        asc_data.append(returned_data)
                else:
                    # desc_data = list()
                    dic={'average_volume':'Avg. Volume', 'landing_pages':'Landing Pages', 'base_ranking':'Base Ranking',}
                    metrics = [dic[i] for i in filter_options['metrics']]
                    for entry in serializer:
                        entries = {key:entry[key] if key in entry.keys() else '' for key in ['Keyword']+metrics+desc_date_list+['MOM Change']}
                        asc_data.append(entries)
                return asc_data
            else:
                return [], []
    except Exception as e:
        # print(str(e))
        log_exception('keyword_monthly_ranking_report', e)
        return [], []


def keyword_ranking_report(user_id, group_id, filter_options):
    try:
        if user_id and group_id:

            page_filter = {"fk_user_id": user_id, "fk_group_id": group_id}
            GrpIns = Groups.objects.filter(Q(id=group_id), fk_user_id=user_id).values("domain_name", "score_meter", "gsc_last_track").first()
            GrpSttng = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=group_id).values('week_track_day').first()
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")
            grp = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('created_date').first()
            end_of_cr_date = grp['created_date'].replace(hour=23, minute=59, second=59, microsecond=999999)
            base_keywords = list(Keyword.objects.filter(fk_user_id=user_id, fk_group_id=group_id, created_date__lte=end_of_cr_date).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id"))
            if keywords and GrpIns:

                day_name = GrpSttng["week_track_day"].lower()
                week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                total_days = 7
                target_day = today_weekday = 0

                f_base = "Base Ranking"
                last_index_12 = last_index_11 = last_index_10 = last_index_9 = last_index_7 = last_index_5 = last_day = f_last_index = s_last_index = t_last_index = fr_last_index = fv_last_index = sx_last_index = se_last_index = egt_last_index = ""

                if "lastranked_date" in keywords[0]:
                    last_day = keywords[0]["lastranked_date"].date()
                    today_weekday = last_day.weekday()

                if day_name in week_list:
                    target_day = week_list.index(day_name) % total_days

                remain_count = (today_weekday - target_day + total_days) % total_days

                if f_last_index == "" and last_day:
                    week_date = last_day - timedelta(days=remain_count)
                    f_last_index = ordinal_day_convert(week_date)

                if s_last_index == "" and last_day:
                    week_date = last_day - timedelta(days=remain_count + 7)
                    s_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [3]:
                    if t_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 14)
                        t_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [4, 5, 6, 8, 7, 9, 10, 11, 12]:
                    if t_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 14)
                        t_last_index = ordinal_day_convert(week_date)

                    if fr_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 21)
                        fr_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [5]:
                    if last_index_5 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 28)
                        last_index_5 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [6, 8, 7, 9, 10, 11, 12]:
                    if fv_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 28)
                        fv_last_index = ordinal_day_convert(week_date)

                    if sx_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 35)
                        sx_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [7]:
                    if last_index_7 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 42)
                        last_index_7 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [8, 9, 10, 11, 12]:
                    if se_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 42)
                        se_last_index = ordinal_day_convert(week_date)

                    if egt_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 49)
                        egt_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [9, 10, 11, 12]:
                    if last_index_9 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 56)
                        last_index_9 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [10, 11, 12]:
                    if last_index_10 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 63)
                        last_index_10 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [11, 12]:
                    if last_index_11 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 70)
                        last_index_11 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [12]:
                    if last_index_12 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 77)
                        last_index_12 = ordinal_day_convert(week_date)
                # if filter_options['duration_limit'] in [9, 10]:
                #     if last_index_9 == "" and last_day:
                #         week_date = last_day - timedelta(days=remain_count + 56)
                #         last_index_9 = ordinal_day_convert(week_date)

                #     if last_index_10 == "" and last_day:
                #         week_date = last_day - timedelta(days=remain_count + 49)
                #         last_index_10 = ordinal_day_convert(week_date)

                if f_last_index or s_last_index or t_last_index or fr_last_index or fv_last_index or sx_last_index or se_last_index or egt_last_index:
                    # print(group_id, last_index_12 , last_index_11 , last_index_10 , last_index_9 , last_index_7 , last_index_5 , f_last_index , s_last_index , t_last_index , fr_last_index , fv_last_index , sx_last_index , se_last_index , egt_last_index ,)
                    page_volume_query = list(keywordVolume.objects.filter(**page_filter).values("month_wise_volume", "past_months", "fk_keyword_id").all())

                    volume_data = {}

                    if page_volume_query:
                        volume_data = {item["fk_keyword_id"]: {"month_wise_volume": item["month_wise_volume"], "past_months": item["past_months"]} for item in page_volume_query}

                    serializer = CustomReportKeywordSerializer(
                        keywords,
                        many=True,
                        context={
                            "voldata": volume_data,
                            "dy": day_name,
                            "dn": GrpIns["domain_name"],
                            "last_index_7": last_index_7,
                            "f_last_index": f_last_index,
                            "s_last_index": s_last_index,
                            "t_last_index": t_last_index,
                            "fr_last_index": fr_last_index,
                            "fv_last_index": fv_last_index,
                            "sx_last_index": sx_last_index,
                            "se_last_index": se_last_index,
                            "egt_last_index": egt_last_index,
                            "last_index_5": last_index_5,
                            "last_index_9": last_index_9,
                            "last_index_10": last_index_10,
                            "last_index_11": last_index_11,
                            "last_index_12": last_index_12,
                            "filter_options": filter_options,
                        },
                    ).data

                    score = []
                    if serializer:
                        score = keywords_overview(f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12, serializer)
                    rem_score = [i.pop('Base Ranking') for i in score]
                    base_rank = base_rank_week_counter(base_keywords, score)
                    asc_list=transform_asc(base_rank)
                    if len(asc_list)>0:
                        asc_list.pop(len(asc_list)-1)
                    total_keywords = {'primary keyword ranking': 'Total keywords'}
                    for entry in asc_list:
                        for key, value in entry.items():
                            if key not in ('primary keyword ranking'):
                                total_keywords[key] = total_keywords.get(key, 0) + value
                    asc_list.append(total_keywords)
                    return remove_empty_keys(asc_list), remove_empty_keys(serializer)
            else:
                return [], []
    except Exception as e:
        # print(str(e))
        log_exception('keyword_ranking_report', e)
        return [], []

def get_last_ot_date(duration):
    try:
        today = datetime.today()
        if duration == 'monthly':
            first_this_month = today.replace(day=1)
            last_month_last = first_this_month - timedelta(days=1)
            last_month_first = last_month_last.replace(day=1)
            return last_month_first, last_month_last
        else:
            this_week_first=today-timedelta(days=today.weekday())
            last_week_last=this_week_first-timedelta(days=1)
            last_week_first=last_week_last-timedelta(days=last_week_last.weekday())
            return last_week_first, last_week_last
    except Exception as e:
        log_exception('get_last_ot_date', e)
        return datetime.now() - timedelta(days=7), datetime.now()

def other_sources_overview(userid, grpid, filter_options, sd, ed):
    try:
        ov_transformed_data = list()
        
        if not sd and not ed:
            sd, ed = get_last_ot_date(filter_options['duration'][0])

        grpSet = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('ga_property', 'ga_refresh_token').first()
        access_token = retrieve_access_token(grpSet['ga_refresh_token'])
        # print(access_token)
        if access_token:
            overview_params = {
                "dateRanges":[{"startDate":sd.strftime('%Y-%m-%d'),"endDate":ed.strftime('%Y-%m-%d')}],
                "dimensions":[{"name":"sessionDefaultChannelGroup"}], 
                "metrics":[{"name":"sessions"}, {'name':'sessionKeyEventRate:purchase'}, {'name':'activeUsers'}, {'name':'eventCount'}, {'name':'engagementRate'}, {'name':'totalRevenue'}],
                # "metrics":[{"name":"sessions"}, {"name":"engagedSessions"}, {"name":"engagementRate"}],
                'limit': 250000
            }
            prop = grpSet['ga_property'][11:]
            # print(prop)
            api_endpoint=f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
            headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"} 

            response = requests.post(api_endpoint, headers=headers, json=overview_params)
            # print(response.text)
            # print(2780, response.status_code)
            if response.status_code==200:
                if 'rows' in response.json():
                    rows = response.json()['rows']
                    for item in rows:
                        source = item['dimensionValues'][0]['value']
                        session = float(item['metricValues'][0]['value'] ) 
                        purchase_event = float(item['metricValues'][1]['value']) 
                        act_users = float(item['metricValues'][2]['value'])
                        evnt_cnt = float(item['metricValues'][3]['value'])
                        eg_rate = float(item['metricValues'][4]['value']) * 100
                        ttl_revenue = float(item['metricValues'][5]['value'])
                        ov_transformed_data.append({'Session primary channel group (Default Channel Group)': source, 'Users': act_users, 'Sessions':session, 'Engagement Rate (%)':eg_rate, 'Event Count':evnt_cnt, 'Key Event (Purchase)':purchase_event, 'Total Revenue':ttl_revenue})
        return ov_transformed_data
    except Exception as e:
        print('other_sources_overview', str(e))
        return []

def get_grpd_colmn(sheet_type):
    # print(sheet_type in ['gsc_queries', 'gsc_branded_queries', 'gsc_non_branded_queries'], sheet_type)
    if sheet_type in ['gsc_queries', 'gsc_branded_queries', 'gsc_non_branded_queries']:
        return ['', '', '']
    elif sheet_type in ['gsc_pages']:
        return ['', '']
    else:
        return []
@api_view(['POST'])
def generate_report(request):
    try:
        if request.method=='POST' and authPermission.validate(request, 'POST'):
            userid = request.data['userid']
            grpid = request.data['grpid']
            grpSet=GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('site_platform').first()
            if grpSet and grpSet['site_platform'] == "non_ecommerce":
                main_non_ecom_report = generate_widget(request)
                return JsonResponse(main_non_ecom_report, safe=False)
            else:
                main_ecom_report = ecom_generate_widget(request)
                return JsonResponse(main_ecom_report, safe=False)
    except Exception as e:
        # print(str(e))
        log_exception('generate_report', e)
        return JsonResponse({'st':0, 'dt':'Something went wrong'})

# @api_view(["POST"])
def generate_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            update_fields = {}
            userid = request.data["userid"]
            grpid = request.data["grpid"]
            page = int(request.data["page"])

            # Calculate the offset
            offset = (page - 1) * 2


            group_data = Groups.objects.filter(fk_user_id=userid, id=grpid).first()

            # if not group_data:
            #     ReportManager.objects.filter(track_status="scheduled", fk_user_id=[report_data["id"]]).update(track_status="failed")
            #     return JsonResponse({'st':0, 'dt':'Something went wrong'})

            # report_sheets = ReportSheets.objects.filter(fk_user=report_data["fk_user"], fk_group=report_data["fk_group"]).all()
            report_sheets = ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
            if not report_sheets:
                ReportManager.objects.filter(track_status="scheduled", fk_user_id=userid, fk_group_id=grpid).update(track_status="failed")
                return {"st": 0, "dt": "No report sheets!"}

            branded_queries = group_data.brand_keywords if group_data.brand_keywords else []

            transformed_data = list()

            if len(report_sheets[offset:offset + 2]) == 0:
                 return {"st": 0, "dt": "Something went wrong", 'sht_flg':False}

            for each_sheet in report_sheets[offset:offset + 2]:

                filter_options = {"id": each_sheet.id, "sheet_name": each_sheet.sheet_name, "type": each_sheet.type, "metrics": each_sheet.metrics, "change_units": each_sheet.change_units, "duration": [each_sheet.duration], "duration_limit": each_sheet.duration_limit, "order_by": each_sheet.order_by}
                grpd_colmn = get_grpd_colmn(filter_options['type'])
                # print(grpd_colmn)
                grpd_colmn.extend(filter_options["metrics"])
                grpd_colmn = [i.capitalize() for i in grpd_colmn]
                

                if filter_options["type"] in ["gsc_overview"] and "weekly" in filter_options["duration"]:
                    _, _, search_query_weekly_overview = gsc_weekly_report_sub("queries", userid, grpid, branded_queries, filter_options)

                    if search_query_weekly_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": search_query_weekly_overview, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_overview"] and "monthly" in filter_options["duration"]:
                    _, _, search_query_weekly_overview = gsc_monthly_report_sub("queries", userid, grpid, branded_queries, filter_options)

                    if search_query_weekly_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": search_query_weekly_overview, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking_overview"] and 'weekly' in filter_options['duration']:
                    rp_score, _ = keyword_ranking_report(userid, grpid, filter_options)
                    if rp_score:
                        transformed_data.append({f"{filter_options['sheet_name']}": rp_score, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_queries"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_queries, gsc_weekly_non_branded_queries, search_query_weekly_overview = gsc_weekly_report_sub("queries", userid, grpid, branded_queries, filter_options)

                    # if filter_options["type"] in ["gsc_queries", "gsc_non_branded_queries"] and gsc_weekly_non_branded_queries:
                    if gsc_weekly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                    if gsc_weekly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})
                        # else:
                        #     chngd_gsc_weekly_branded_queries=[{'Brand_' + key: value for key, value in item.items()} for item in gsc_weekly_branded_queries]
                        #     chngd_gsc_weekly_non_branded_queries=[{'Non_'+ key: value for key, value in item.items()} for item in gsc_weekly_non_branded_queries]

                        #     for brand_item, non_brand_item in zip(chngd_gsc_weekly_branded_queries, chngd_gsc_weekly_non_branded_queries):
                        #         brand_item.update(non_brand_item)

                        #     transformed_data.append({f"{filter_options['sheet_name']}":chngd_gsc_weekly_branded_queries})

                if filter_options["type"] in ["gsc_non_branded_queries"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_queries, gsc_monthly_non_branded_queries, search_query_monthly_overview = gsc_monthly_report_sub("queries", userid, grpid, branded_queries, filter_options)
                    if gsc_monthly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_queries"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_queries, gsc_monthly_non_branded_queries, search_query_monthly_overview = gsc_monthly_report_sub("queries", userid, grpid, branded_queries, filter_options)
                    if gsc_monthly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                    # if filter_options["type"] in ["gsc_queries", "gsc_non_branded_queries"] and gsc_monthly_non_branded_queries:
                    if gsc_monthly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})
                        # else:
                        # chngd_gsc_monthly_branded_queries=[{'Brand_' + key: value for key, value in item.items()} for item in gsc_monthly_branded_queries]
                        # chngd_gsc_monthly_non_branded_queries=[{'Non_'+ key: value for key, value in item.items()} for item in gsc_monthly_non_branded_queries]

                        # for brand_item, non_brand_item in zip(chngd_gsc_monthly_branded_queries, chngd_gsc_monthly_non_branded_queries):
                        #     brand_item.update(non_brand_item)

                        # transformed_data.append({f"{filter_options['sheet_name']}":gsc_monthly_branded_queries})

                if filter_options["type"] in ["gsc_non_branded_queries"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_queries, gsc_weekly_non_branded_queries, search_query_weekly_overview = gsc_weekly_report_sub("queries", userid, grpid, branded_queries, filter_options)
                    if gsc_weekly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_branded_queries"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_queries, gsc_weekly_non_branded_queries, search_query_weekly_overview = gsc_weekly_report_sub("queries", userid, grpid, branded_queries, filter_options)
                    if gsc_weekly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_branded_queries"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_queries, gsc_monthly_non_branded_queries, _ = gsc_monthly_report_sub("queries", userid, grpid, branded_queries, filter_options)
                    if gsc_monthly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_branded_queries, "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_branded_queries[0].keys())) - 3, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_pages"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_pages, gsc_weekly_non_branded_pages, search_page_weekly_overview = gsc_weekly_report_sub("pages", userid, grpid, branded_queries, filter_options)
                    if gsc_weekly_non_branded_pages:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_pages, "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_pages[0].keys())) - 2, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["gsc_pages"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_pages, gsc_monthly_non_branded_pages, search_page_monthly_overview = gsc_monthly_report_sub("pages", userid, grpid, branded_queries, filter_options)
                    if gsc_monthly_non_branded_pages:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_pages, "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_pages[0].keys())) - 2, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_overview"] and "weekly" in filter_options["duration"]:
                    ga_weekly_report = ga_overview_sub(userid, grpid, "week", filter_options)
                    if ga_weekly_report:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_weekly_report, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_overview"] and "monthly" in filter_options["duration"]:
                    ga_monthly_report = ga_overview_sub(userid, grpid, "month", filter_options)
                    if ga_monthly_report:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_monthly_report, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_landing_pages"]:
                    ga_landing_page_data = landing_page_report_sub(userid, grpid, filter_options)
                    if ga_landing_page_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_landing_page_data, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["domain_metrics"]:
                    base_metrics_data = seo_metrics_sub(userid, grpid, filter_options)
                    if base_metrics_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": base_metrics_data, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking"] and 'weekly' in filter_options['duration']:
                    rp_score, rp_keywords = keyword_ranking_report(userid, grpid, filter_options)
                    # print(rp_keywords)
                    if rp_keywords:
                        transformed_data.append({f"{filter_options['sheet_name']}": rp_keywords, 'sheet_id':filter_options['id']})
                
                if filter_options['type'] in ['ga_other_sources']:
                    sd=""
                    ed=""
                    if filter_options['duration'][0]=='weekly':
                        betwn_date=GSCWeeklyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by('-week_start_date').values('week_start_date', 'week_end_date').first()
            
                        if betwn_date:
                            sd=betwn_date['week_start_date']
                            ed=betwn_date['week_end_date']

                        if not betwn_date:
                            three_days_ago = timezone.now() - timedelta(days=4)
                            betwn_date = GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("start_date", "end_date").order_by("-start_date").first()
                            if betwn_date:
                                sd=betwn_date['start_date']
                                ed=betwn_date['end_date']
                    else:
                        betwn_date=GSCMonthlyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by('-month_start_date').values('month_start_date', 'month_end_date').first()
            
                        if betwn_date:
                            sd=betwn_date['month_start_date']
                            ed=betwn_date['month_end_date']

                        if not betwn_date:
                            three_days_ago = timezone.now() - timedelta(days=4)
                            betwn_date = GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("start_date", "end_date").order_by("-start_date").first()
                            if betwn_date:
                                sd=betwn_date['start_date']
                                ed=betwn_date['end_date']

                    ot_sources_overview = other_sources_overview(userid, grpid,filter_options, sd, ed)
                    start = sd.strftime("%dth %b")
                    last = ed.strftime("%dth %b")
                    last_date = f"{start} - {last}"
                    if ot_sources_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": ot_sources_overview, 'bt_date':last_date, 'sheet_id':filter_options['id']})
                
                if filter_options['type'] in ['keyword_ranking'] and 'monthly' in filter_options['duration']:
                    monthly_keywords=keyword_monthly_ranking_report(userid, grpid, filter_options)
                    if monthly_keywords:
                        transformed_data.append({f"{filter_options['sheet_name']}": monthly_keywords, 'sheet_id':filter_options['id']})
                if filter_options['type'] in ['keyword_ranking_overview'] and 'monthly' in filter_options['duration']:
                    monthly_overview = monthly_keywords_overview(userid, grpid, filter_options)
                    if monthly_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": monthly_overview, 'sheet_id':filter_options['id']})
    
                summary_list = set(["google search console" if i.type in ["gsc_non_branded_queries", "gsc_branded_queries", "gsc_queries"] else "keyword ranking" for i in report_sheets.filter(type__in=["gsc_branded_queries", "gsc_non_branded_queries", "gsc_queries", "keyword_ranking"])])
                grpd_colmn=list()
            return {"st": 1, "page":page + 1,"dt": transformed_data, "sm_list": list(summary_list)}
        return {"st": 0, "dt": "Something went wrong"}
        # update_fields["track_status"] = "scheduled"
        # ReportManager.objects.filter(track_status="inprogress", id__in=[report_data["id"]]).update(**update_fields)
    except Exception as e:
        # print(e)
        log_exception('generate_widget', e)
        # ReportManager.objects.filter(track_status="scheduled", id__in=[report_data["id"]]).update(track_status="failed")
        return {"st": 0, "dt": "Something went wrong"}


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def CSV_monitor(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = request.data["userid"]
            grpid = request.data["grpid"]

            if userid.isdigit() and grpid.isdigit():
                rpt_shts_count = ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid).count()
                if rpt_shts_count:
                    rpt_mnger_updt = ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_status="scheduled", delivery_status=True)
                    return JsonResponse({"st": 1, "dt": "Downloadable link will be sent your mail shortly."})
                else:
                    return JsonResponse({"st": 0, "dt": "Something went wrong"})
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        log_exception('CSV_monitor', e)
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


# @api_view(['POST'])
@cron_only
def csv_report_mailer(userid, grpid):
    try:
        if userid.isdigit() and grpid.isdigit():
            acc = Account.objects.filter(id=userid).values("username", "email").first()
            grp = Groups.objects.filter(fk_user_id=userid, id=grpid).values("group_name").first()
            username = ""
            receiver = []
            projectname = ""
            if acc:
                username = acc["username"]
                receiver = acc["email"]
            if grp:
                projectname = grp["group_name"]

            rpt_mnger = ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("fk_user_id", "fk_group_id", "track_status", "delivery_status", "download_link").first()

            if rpt_mnger and username and receiver and projectname:
                if rpt_mnger["delivery_status"] and rpt_mnger["download_link"] and rpt_mnger["download_link"] != "NA":
                    download_link = rpt_mnger["download_link"]
                    context = {
                        "download_link": download_link,
                        "username": username,
                        "groupname": projectname,
                        "siteurl": settings.SITE_URL,
                        "serivceurl": settings.SERVICE_URL,
                    }
                    email_html_message = render_to_string("email/report_copy.html", context)
                    msg = EmailMultiAlternatives("Tracker schedule report for " + projectname, "report Content", settings.HOST_MAIL, [receiver])
                    msg.attach_alternative(email_html_message, "text/html")
                    if msg.send():
                        ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(delivery_status=False)
                        return JsonResponse({"st": 1, "dt": "Done"})

        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        log_exception('csv_report_mailer', e)
        # print(str(e))
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def reportDelete(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = request.data["userid"]
            grpid = request.data["grpid"]
            report_name = request.data["report_name"]
            report_number = request.data["sheet_number"]
            # print(userid, grpid, report_name, report_number)
            rpt_sht = ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, id=report_number).delete()
            if rpt_sht[0] == 1:
                return JsonResponse({"st": 1, "dt": "Report deleted successfully"})
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        log_exception('reportDelete', e)
        # print(str(e))
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


@api_view(["POST", "GET"])
def checkReport(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            if {"userid", "grpid"}.issubset(request.data.keys()):
                userid = request.data["userid"]
                grpid = request.data["grpid"]
                rpt_mnger = ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("track_status", "download_link")
                if rpt_mnger.exists():
                    if not rpt_mnger.first()["download_link"] == "NA":
                        download_link = rpt_mnger.first()["download_link"]
                        if not validators.url(download_link):
                            return JsonResponse({"st": 0, "dt": "Not validated url"})
                        elif rpt_mnger.first()['track_status'] in ['scheduled', 'inprogress']:
                            return JsonResponse({"st": 1, "dt": True, "link": download_link, 'trkSts':True})
                        else:
                            return JsonResponse({"st": 1, "dt": True, "link": download_link, 'trkSts':False})
                    elif rpt_mnger.first()['track_status'] in ['scheduled', 'inprogress']:
                        return JsonResponse({'st':1, 'dt':False, 'link':'', 'trkSts':True})
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        log_exception('checkReport', e)
        # print(str(e))
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


@api_view(["POST", "GET"])
def gen_report(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            if {"userid", "grpid", "type"}.issubset(request.data.keys()):
                userid = request.data["userid"]
                grpid = request.data["grpid"]
                sh_type = request.data["type"]
                rpt_mnger = ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("track_status", "download_link")
                if sh_type == "update":
                    if rpt_mnger.exists():
                        if not (rpt_mnger.first()["track_status"] in ["scheduled", "inprogress"]):
                            updt_rprt_mnger = ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_status="scheduled")
                            if updt_rprt_mnger:
                                return JsonResponse({"st": 1, "dt": "Generating the report..."})
                else:
                    if rpt_mnger.exists():
                        if rpt_mnger.first()["track_status"] in ["scheduled", "inprogress"]:
                            return JsonResponse({"st": 1, "dt": True})
                        else:
                            download_link = False
                            if not rpt_mnger.first()["download_link"] == "NA":
                                download_link = rpt_mnger.first()["download_link"]
                                if not validators.url(download_link):
                                    download_link = False
                            return JsonResponse({"st": 0, "dt": False, "dl": download_link})
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        log_exception('gen_report', e)
        return JsonResponse({"st": 0, "dt": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def local_report_export(request):
    """Download the active project's ranking report without a background worker."""
    if not authPermission.validate(request, "POST"):
        return JsonResponse(
            {"status": "false", "message": "Not authorised to export this report"},
            status=403,
        )

    userid = str(request.data.get("userid", "")).strip()
    grpid = str(request.data.get("grpid", "")).strip()
    if not userid.isdigit() or not grpid.isdigit():
        return JsonResponse(
            {"status": "false", "message": "userid and grpid are required"},
            status=400,
        )

    group = Groups.objects.filter(id=grpid, fk_user_id=userid).first()
    if group is None:
        return JsonResponse(
            {"status": "false", "message": "Project not found"}, status=404
        )

    keywords = Keyword.objects.filter(
        fk_user_id=userid, fk_group_id=grpid
    ).order_by("ranknow", "keyword")
    rows = ExportCSVKeywordSerializer(keywords, many=True).data
    fieldnames = [
        "sno",
        "keyword",
        "region",
        "Rank",
        "Best rank",
        "Day",
        "Week",
        "Month",
        "Volume",
        "Comp",
        "URL",
        "Created on",
    ]

    project_name = "".join(
        char if char.isalnum() else "-" for char in (group.group_name or "project")
    ).strip("-") or "project"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="{project_name}-keyword-ranking.csv"'
    )
    response.write("\ufeff")
    writer = csv.DictWriter(response, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "-") for field in fieldnames})
    return response

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def rnme_sht(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid = request.data['userid']
            grpid = request.data['grpid']
            sheet_number = request.data['shtNmber']
            sheet_name = request.data['shtNme']
            update_sheet_name = request.data['updtShtNme']
            if ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, id=sheet_number, sheet_name=sheet_name).exists():
                if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=update_sheet_name).exists():
                    if (ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, id=sheet_number).update(sheet_name=update_sheet_name)):
                        return JsonResponse({'st':1, 'dt':'Sheet name updated'})
                    else:
                        return JsonResponse({'st':0, 'dt':'Error in update'})
                else:
                    return JsonResponse({'st':0, 'dt':'Sheet name already exists'})
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
    except Exception as e:
        log_exception('rnme_sht', e)
        # print(str(e))

@api_view(['POST', 'GET'])
def check_ga_gsc(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid=request.data['userid']
            grpid = request.data['grpid']
            enabled_sheet = {'gsc':False, 'ga':False, 'pltfrm':False, 'platform':''}
            grpSet = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('ga_refresh_token', 'site_platform').first()
            grp = Groups.objects.filter(fk_user_id=userid, id=grpid).values('gsc_refresh_token').first()
            rpt_shts = ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid).count()
            if grp:
                if grp['gsc_refresh_token']:
                    enabled_sheet['gsc']=True
            if grpSet:
                if grpSet['ga_refresh_token']:
                    enabled_sheet['ga']=True
                enabled_sheet['pltfrm'] = False if grpSet['site_platform'] else True
                enabled_sheet['platform'] = req_rev_platform.get(grpSet['site_platform'])

            return JsonResponse({'st':1, 'dt':enabled_sheet})
            
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
    except Exception as e:
        log_exception('check_ga_gsc', e)
        # print(str(e))
        return JsonResponse({'st':0, 'dt':'Something went wrong'})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_platform(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userid=request.data['userid']
            grpid = request.data['grpid']
            platform = request.data['pltform']
            # print(platform)
            GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(site_platform=req_platform.get(platform))
            return JsonResponse({'st':1, 'dt':'Done'})
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
    except Exception as e:
        log_exception('change_platform', e)
        # print(str(e))
        return JsonResponse({'st':0, 'dt':'Something went wrong'})

def log_exception(func, Error):
    print(func, Error)
