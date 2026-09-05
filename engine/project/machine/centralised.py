from django.shortcuts import render
from django.conf import settings

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings

import requests, json, time, csv
from bs4 import BeautifulSoup
from urllib import parse
import sys, os, random
from datetime import datetime, date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse

from urllib.parse import urlparse
from threading import Timer

from project.machine import watchdog, formulate, keywordhistory as keyword_history
import re


def checkstatus(num):
    if num > 0:
        return "up"
    elif num == 0:
        return "-"
    else:
        return "down"


def rankFormulation(liveRank, pastRank):
    totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)

    if int(liveRank) == 0 and int(pastRank) == 0:
        formulateValue = 0
    elif int(liveRank) == 0 and int(pastRank) > 0:
        formulateValue = int(pastRank) - int(totalRankLength)
    elif int(liveRank) > 0 and int(pastRank) == 0:
        formulateValue = int(totalRankLength) - int(liveRank)
    elif int(liveRank) > int(pastRank):
        formulateValue = int(pastRank) - int(liveRank)
    elif int(pastRank) > int(liveRank):
        formulateValue = int(pastRank) - int(liveRank)
    else:
        formulateValue = int(liveRank) - int(pastRank)

    return formulateValue


def mongopush(engineMode, rowSet):
    try:
        print(rowSet.get("SNIPPET_RATING"))
        mongoid = rowSet.get("ID")
        liverank = rowSet.get("RANK")
        url = rowSet.get("URL")
        target = rowSet.get("TARGET")
        snippet_rating = str(rowSet.get("SNIPPET_RATING") or "0") if "SNIPPET_RATING" in rowSet else "0"
        reviews = True if float(rowSet.get("RATINGS")) > 0 and float(rowSet.get("RATINGS")) <= 5 else False
        # reviews = True if int(get('REVIEWS')) > 0 else False
        total_ratings = str(rowSet.get("RATINGS")) if float(rowSet.get("RATINGS")) > 0 and float(rowSet.get("RATINGS")) <= 5 else "-"
        total_reviews = str(rowSet.get("REVIEWS")) if int(rowSet.get("REVIEWS")) > 0 else "-"
        key_alias = rowSet.get("KEYALIAS") if rowSet.get("KEYALIAS") != "" else ""
        totalresults = rowSet.get("TOTAL_RESULTS") if rowSet.get("TOTAL_RESULTS") != "" else "-"
        totaltime = rowSet.get("TOTAL_TIME") if rowSet.get("TOTAL_TIME") != "" else "-"
        # snippet_details = rowSet.get('SNIPPET_DETAILS') if len(rowSet.get('SNIPPET_DETAILS')) else ""
        snippet_details = rowSet.get("SNIPPET_DETAILS")
        snippets = True if "featured_box" in rowSet.get("SNIPPETS") else False
        knowledge_panel = True if "knowledge_box" in rowSet.get("SNIPPETS") else False
        ad_box = True if "ads" in rowSet.get("SNIPPETS") else False
        cannibalisation = rowSet.get("CANNIBALISATION")
        competitor = rowSet.get("COMPETITORS")
        today_snippet = rowSet.get("TODAY")
        ce_page_uuid = rowSet.get("PAGE_UUID") if rowSet.get("PAGE_UUID") != None else "-"
        ce_page_uuid_url = rowSet.get("PAGE_UUID_URL") if rowSet.get("PAGE_UUID_URL") != None else "-"

        Keywords = Keyword.objects.filter(__raw__={"id": mongoid})
        if Keywords:
            keyIns = Keywords[0]
            currdate = date.today()
            _kw__history__flag_ = False

            if keyIns.lastranked_date.date() < currdate:
                _kw__history__flag_ = True

            if engineMode == "ENGINE" or engineMode == "MANUAL":
                oldUrl = keyIns.site_url
                keyword_history.checkUrlAlteration(url, oldUrl, mongoid, liverank, keyIns.total_rating, total_ratings)

            rankArrayCount = len(keyIns.rank)
            keywordTotalDayCount = int((currdate - keyIns.created_date.date()).days) + 1

            # BEST RANK CALCULATION
            exist_top_rank = keyIns.top_rank
            cal_top_rank = int(liverank)
            totalrank = list(filter(lambda num: num != 0, list(set(keyIns.rank))))
            if len(totalrank) > 0:
                min_rank = min(totalrank)
                cal_top_rank = int(liverank) if liverank <= min_rank and liverank > 0 else min_rank

            if exist_top_rank != None and exist_top_rank > 0:
                if cal_top_rank <= exist_top_rank:
                    top_rank = int(cal_top_rank)
                else:
                    top_rank = int(exist_top_rank)
            else:
                top_rank = int(liverank)

            # KEYWORD ALIAS UPDATE
            key_alias = key_alias if keyIns.keyword_alias != "-" else "-"

            # TODAY AND BEST SNIPPET
            kw_snip = keyIns.keyword_snippet
            if "tdy" not in kw_snip:
                kw_snip.update({"tdy": {}})
            if "best" not in kw_snip:
                kw_snip.update({"best": {}})

            kw_snip.update({"tdy": today_snippet})

            if int(liverank) <= top_rank and int(liverank) > 0:
                kw_snip.update({"best": today_snippet})

            if keywordTotalDayCount == 1:
                Keywords.update(rank=[])
                Keywords.update(
                    # push__rank__0=liverank,   #If MAcro Problem avoided Uncomment it
                    rank__0=liverank,
                    site_url=url,
                    ranknow=liverank,
                    top_rank=int(top_rank),
                    rank_sincestart=liverank,
                    daymark="-",
                    dayval=0,
                    weekmark="-",
                    weekval=0,
                    monthmark="-",
                    monthval=0,
                    halfmonthmark="-",
                    halfmonthval=0,
                    featured_snippet=snippets,
                    knowledge_panel=knowledge_panel,
                    ads=ad_box,
                    review=reviews,
                    total_rating=snippet_rating,
                    total_review=total_reviews,
                    snippets_details=snippet_details,
                    lastranked_date=datetime.now(),
                    updated_date=datetime.now(),
                    status_from_start="-",
                    search_results=totalresults,
                    keyword_alias=key_alias,
                    cannibalisation=cannibalisation,
                    page_uuid=ce_page_uuid,
                    page_uuid_url=ce_page_uuid_url,
                    keyword_snippet=kw_snip,
                )
            else:
                status_from_start = keyIns.status_from_start
                monthmark = keyIns.monthmark
                monthval = keyIns.monthval
                halfmonthmark = keyIns.halfmonthmark
                halfmonthval = keyIns.halfmonthval
                weekval = keyIns.weekval
                weekmark = keyIns.weekmark
                dayval = keyIns.dayval
                daymark = keyIns.daymark

                if rankArrayCount >= keywordTotalDayCount:
                    groupDifference = rankArrayCount - keywordTotalDayCount

                    if groupDifference > 0:
                        watchdog.coreLog(" > RANK OVERFLOW " + str(mongoid), engineMode)
                        flag = 0
                        while flag < groupDifference:
                            Keywords.update(pop__rank=-1)
                            flag += 1

                    if len(keyIns.rank) > 1:
                        day_dif = rankFormulation(liverank, keyIns.rank[1])
                        daymark = checkstatus(day_dif)
                        dayval = abs(day_dif)
                    if len(keyIns.rank) > 7:
                        week_dif = rankFormulation(liverank, keyIns.rank[7])
                        weekmark = checkstatus(week_dif)
                        weekval = abs(week_dif)
                    if len(keyIns.rank) > 15:
                        half_month_dif = rankFormulation(liverank, keyIns.rank[15])
                        halfmonthmark = checkstatus(half_month_dif)
                        halfmonthval = abs(half_month_dif)
                    if len(keyIns.rank) > 30:
                        month_dif = rankFormulation(liverank, keyIns.rank[30])
                        monthmark = checkstatus(month_dif)
                        monthval = abs(month_dif)
                    if len(keyIns.rank) > 1:
                        diff = rankFormulation(liverank, keyIns.rank[-1])
                        status_from_start = checkstatus(diff)

                    Keywords.update(rank__0=liverank)
                else:
                    if len(keyIns.rank) > 0:
                        day_dif = rankFormulation(liverank, keyIns.rank[0])
                        daymark = checkstatus(day_dif)
                        dayval = abs(day_dif)
                    if len(keyIns.rank) > 6:
                        week_dif = rankFormulation(liverank, keyIns.rank[6])
                        weekmark = checkstatus(week_dif)
                        weekval = abs(week_dif)
                    if len(keyIns.rank) > 14:
                        half_month_dif = rankFormulation(liverank, keyIns.rank[14])
                        halfmonthmark = checkstatus(half_month_dif)
                        halfmonthval = abs(half_month_dif)
                    if len(keyIns.rank) > 29:
                        month_dif = rankFormulation(liverank, keyIns.rank[29])
                        monthmark = checkstatus(month_dif)
                        monthval = abs(month_dif)
                    if len(keyIns.rank) > 1:
                        diff = rankFormulation(liverank, keyIns.rank[-1])
                        status_from_start = checkstatus(diff)

                    Keywords.update(
                        # push__rank__0 = liverank,   #If Macro Problem avoided Uncomment it
                        rank__0=liverank,
                    )

                Keywords.update(
                    ranknow=liverank,
                    top_rank=int(top_rank),
                    site_url=url,
                    daymark=daymark,
                    dayval=dayval,
                    weekmark=weekmark,
                    weekval=weekval,
                    monthmark=monthmark,
                    monthval=monthval,
                    halfmonthmark=halfmonthmark,
                    halfmonthval=halfmonthval,
                    featured_snippet=snippets,
                    knowledge_panel=knowledge_panel,
                    ads=ad_box,
                    review=reviews,
                    total_rating=snippet_rating,
                    total_review=total_reviews,
                    snippets_details=snippet_details,
                    lastranked_date=datetime.now(),
                    updated_date=datetime.now(),
                    status_from_start=status_from_start,
                    search_results=totalresults,
                    keyword_alias=key_alias,
                    cannibalisation=cannibalisation,
                    page_uuid=ce_page_uuid,
                    page_uuid_url=ce_page_uuid_url,
                    keyword_snippet=kw_snip,
                )

            # SERP FEATURE RECORD
            #
            # Written separately and only when the parser produced one. The
            # featured_snippet/knowledge_panel/ads booleans above are two-state
            # and cannot say "not measured" -- a keyword ranked before feature
            # extraction existed reads False on all three, which is the same
            # value as a SERP that genuinely had none. serp_features carries the
            # tri-state, and an empty dict there means unmeasured.
            #
            # The HTML parsers (parser.py, mobileparser.py) do not build this
            # key. Writing {} for them would overwrite a real measurement with a
            # false absence, so a missing key skips the write entirely.
            serp_features = rowSet.get("SERP_FEATURES")
            if isinstance(serp_features, dict) and serp_features:
                Keywords.update(serp_features=serp_features)

            # History Update
            if engineMode == "ENGINE" or engineMode == "MANUAL":
                keyword_history.snippetsHistory(snippet_details, mongoid, target, _kw__history__flag_, competitor)
            return 1
    except Exception as e:
        watchdog.coreLog(" > ERROR IN CENTRALISED mongopush FUNCTION >> " + str(e), "ENGINE")

    return 0
