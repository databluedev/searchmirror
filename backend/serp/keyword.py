from rest_framework.decorators import api_view
from glassend.request_fields import bad_request, invalid_request, missing_fields
from serp.models import *
from serp.serializers import *
from serp.common import *
from serp import calculation, views as serp_views
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from mailend.models import KeywordHistory
from account import verify as authPermission
from serp.engine_trigger import trigger_engine_manual
from serp.rank_state import apply_rank_state
import numpy
from operator import itemgetter

from django.shortcuts import render, redirect
import requests, json
from serp.models import *
from serp.common import *
import string, random
from urllib.parse import urlparse
from datetime import date, datetime, timedelta, time
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from urllib.parse import quote
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

GSC_CLIENT_ID = getattr(settings, "GSC_CLIENT_ID", "")
GSC_SECRET_ID = getattr(settings, "GSC_SECRET_ID", "")
GSC_REDIRECT_URL = getattr(settings, "GSC_REDIRECT_URL", "")

GA_CLIENT_ID = getattr(settings, "GA_CLIENT_ID")
GA_SECRET_ID = getattr(settings, "GA_SECRET_ID")

# ~~~~~~~~~~~~~~~~~~~~~New flow add keyword---------------------------

req_platform={
    'E-commerce': 'ecommerce',
    'Non E-commerce': 'non_ecommerce'
}
req_rev_platform={
    'ecommerce': 'E-commerce',
    'non_ecommerce': 'Non E-commerce'
}

def find_date_before_two_weeks(target_day):

    # Get today's date
    today = datetime.today()

    # Find the day of the week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    current_day = today.weekday()

    # Calculate the difference between the current day and the target day
    days_until_target_day = current_day - target_day

    # Calculate the number of days to subtract to get to the target day before two weeks
    days_to_subtract = days_until_target_day + 7  # Add 7 to go back to the previous target day

    # Subtract two weeks from today's date and adjust to the target day
    target_date_before_two_weeks = today - timedelta(weeks=1, days=days_to_subtract)

    return target_date_before_two_weeks.isoformat()


# Add keyword engine.
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def addfreshkey(request):

    userid = str(request.data["userid"])
    getLanguage = request.data["language"].strip()
    grpName = request.data["newGrp"].strip()
    gscToken = request.data["gsctoken"].strip() if request.data["gsctoken"] else ""
    ga_token = request.data["ga_token"].strip() if request.data["ga_token"] else ""
    gscProperty = request.data["gsc_property"].strip() if request.data["gsc_property"] else ""
    ga_property = request.data["ga_property"].strip() if request.data["ga_property"] else ""
    trackDay = request.data["trackDay"] if request.data["trackDay"] else ""
    dm_platform = request.data.get('dmPlatform', '')
    # The UI sends the name bracketed, e.g. "(English)". Match either shape, and
    # never dereference the result unguarded -- a missing language used to raise
    # AttributeError and turn /addnewkey into a 500 with no usable message.
    _lang_name = (getLanguage or "").strip()
    languageData = (
        Language.objects.filter(language_name=_lang_name).first()
        or Language.objects.filter(language_name=_lang_name.strip("()")).first()
        or Language.objects.filter(language_name="(%s)" % _lang_name.strip("()")).first()
    )
    weekDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # "Daily" (and anything not a weekday) is not in this list; index() would
    # raise ValueError and 500 the whole add. It maps to 0 -- the schedule day
    # only seeds the weekly cadence, and a daily schedule has no single day.
    dayValue = weekDays.index(trackDay) if trackDay in weekDays else 0
    if userid.isdigit() and grpName and languageData and languageData.language_code:
        dataChecklist = request.data["keyword"]
        if isinstance(dataChecklist, list) == False:
            dataCheckKeywords = request.POST["keyword"].replace("\n", ",").lower().strip()
            keywordArray = dataCheckKeywords.split(",")
            dataChecklist = list(set(filter(None, map(str.strip, keywordArray))))

        if len(dataChecklist) > 0:
            AccountIns = Accountusage.objects.filter(fb_user_id=userid).first()
            # changed
            sts, cnt = totalKeywordsCount(userid)
            keywrdCount = cnt
            # keywrdCount = Keyword.objects.filter(fk_user_id=userid).count()
            groupcountvalue = Groups.objects.filter(fk_user_id=userid).count()

            if AccountIns.plan_project_limit >= groupcountvalue:
                paystatus, payOverRule = userPaymode(userid, AccountIns)
                if paystatus not in ["dead", "cancelled", "expire"]:
                    if AccountIns.plan_keyword_limit >= (len(dataChecklist) + keywrdCount):
                        serializer = GroupSerializer(data=json.loads(request.data["newGrp"]))
                        default_switch = dict.fromkeys(["DS", "URL", "FS", "ADS", "RS", "CNN", "NIMP", "SSA"], False)
                        email_notify_update = dict.fromkeys(["daily_routine", "best_score_routine", "cannibalisation_routine", "url_change_routine", "no_week_improvement_routine", "ratings_change_routine", "new_ads_routine", "new_featured_routine", "score_routine"], None)

                        if serializer.is_valid():
                            UserSttgdata = Usersettings.objects.filter(fb_user_id=userid).first()
                            # Table_non_columns = list(filter(None, UserSttgdata.non_columns)) if len(UserSttgdata.non_columns) > 0 else []
                            serializer.validated_data["automation_email_switch"] = default_switch
                            serializer.validated_data["automation_email_notify_log"] = email_notify_update
                            serializer.validated_data["non_columns"] = UserSttgdata.non_columns
                            groupcreate = serializer.save()
                            grpid = groupcreate.id

                            grpSttgIns = GroupSetting()
                            grpSttgIns.fk_user_id = userid
                            grpSttgIns.fk_group_id = grpid
                            # The three panels the dashboard actually renders and
                            # the Manage Widgets sheet can actually toggle:
                            # Search Visibility Score, Competitors, Cannibalisation.
                            # The other seven were stored here but had no
                            # component behind them and no toggle to turn them
                            # off -- TK and DK never had either -- so a new
                            # project was seeded with settings it could neither
                            # see nor change.
                            grpSttgIns.widget_handle = ["SS", "CW", "CZ"]
                            grpSttgIns.save()

                            refreshmaual = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid)
                            if refreshmaual.exists():
                                refreshIns = refreshmaual.update(refresh_status="start")
                            else:
                                refreshIns = Refreshmanual()
                                refreshIns.fb_user_id = userid
                                refreshIns.fk_group_id = grpid
                                refreshIns.refresh_status = "start"
                                refreshIns.save()

                            newKeyCount, _existsKW = NewKeywordsInsert(userid, grpid, dataChecklist, request, languageData)

                            if newKeyCount == 0:
                                return Response({"status": "false", "message": "warning", "errormsg": "Keywords already exists. Check once."})

                            if newKeyCount > 0:
                                AccountIns.last_used_refresh_count = newKeyCount
                                AccountIns.keyword_research_searches = []
                                if AccountIns.gsc_token:
                                    AccountIns.gsc_track_status = "scheduled"
                                AccountIns.save()

                            brand_keywords = []
                            if "brand_keywords" in request.data:
                                brand_keywords = request.data["brand_keywords"]
                            if isinstance(brand_keywords, list) == False:
                                brand_keywords_str = json.loads(request.data["brand_keywords"])
                                brand_keywords = list(set(map(lambda x: x["text"].lower().strip(), brand_keywords_str)))

                            GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(ga_refresh_token=ga_token, ga_property=ga_property, week_track_day=trackDay, site_platform = req_platform.get(dm_platform, ''))
                            Groups.objects.filter(id=int(grpid)).update(manual_grp_trigger="INIT", strict_refresh_switch=True, last_used_refresh_count=newKeyCount, gsc_refresh_token=gscToken, brand_keywords=brand_keywords, gsc_property=gscProperty)
                            # New project is queued -- rank it now.
                            trigger_engine_manual(userid, grpid)
                            if gscToken and gscProperty:
                                #GSCWeeklyResult.objects.create(fk_user_id=userid, fk_group_id=grpid, track_status="scheduled", track_scheduled_at=find_date_before_two_weeks(dayValue))
                                #GSCMonthlyResult.objects.create(fk_user_id=userid, fk_group_id=grpid, track_status="scheduled", track_scheduled_at=datetime.today() - relativedelta(months=2))
                                GSCDailyResult.objects.get_or_create(fk_user_id=userid, fk_group_id=grpid, track_scheduled_at=datetime.today() - relativedelta(days=2))
                            if ga_token and ga_property:
                                GA_weekly_monitor.objects.create(fk_user_id=userid, fk_group_id=grpid, track_status="done", track_scheduled_start=datetime.now())
                                GA_monthly_monitor.objects.create(fk_user_id=userid, fk_group_id=grpid, track_status="done", track_scheduled_start=datetime.now())
                                GA_daily_monitor.objects.create(fk_user_id=userid, fk_group_id=grpid, track_mode="yearly", track_status='start', track_scheduled_start=datetime.now())
                            DomainTracking.objects.create(fk_user_id=userid, fk_group_id=grpid, domain=request.data["url"], track_status="scheduled", track_scheduled_at=timezone.now())
                            SettingsData = Settings.objects.filter(id=1).first()
                            core_manual_mode = SettingsData.core_manual_mode if SettingsData and SettingsData.core_manual_mode else 0
                            if newKeyCount != len(dataChecklist):
                                newKeyError = str(len(dataChecklist) - newKeyCount) + " of " + str(len(dataChecklist)) + " Keywords already exists."
                                newKeySuccess = str(newKeyCount) + " Keyword added"
                                return Response({"status": "true", "message": "warning", "groupcount": groupcountvalue, "grpid": grpid, "Engmd": core_manual_mode, "errormsg": newKeyError, "successmsg": newKeySuccess})
                            else:
                                return Response({"status": "true", "groupcount": groupcountvalue, "grpid": grpid, "Engmd": core_manual_mode, "message": "Keyword added"})
                        else:
                            return JsonResponse({"status": "false", "message": "Invalid data!"})
                    else:
                        availKeywrdsLimit = AccountIns.plan_keyword_limit - keywrdCount
                        newKeyError = "You can add only " + str(availKeywrdsLimit) + " keywords."
                        return Response({"status": "false", "message": "warning", "errormsg": newKeyError})
                else:
                    return Response({"status": "false", "message": "Oops! Sorry You've no active subscription."})
            else:
                return Response({"status": "false", "message": "Your project limit has been completed"})
        else:
            return JsonResponse({"status": "false", "message": "Invalid data!"})
    else:
        return JsonResponse({"status": "false", "message": "Something went wrong"})


# ---------------------------------------------------------------------------
# MULTI-COUNTRY ADD
# ---------------------------------------------------------------------------
# One keyword tracked in several countries is stored as ONE KEYWORD ROW PER
# (keyword, country). Every per-country fact the product needs already lives on
# the row -- region (the Google domain the engine searches), isocode, location,
# rank history -- and duplicate detection already keys on region, so nothing
# below the API changes and no column is added to `keyword` or `group`.
#
# The alternative, a list of countries on a single row, would have to be read
# by engine/project/machine/models.py as well, and would give one rank series
# for several different SERPs.


class _RegionScopedRequest(object):
    """One country's view of an add-keyword request.

    KeywordCreateSerializer reads region/isocode/countryname straight off
    ``request.data``, so adding a keyword to several countries means handing it
    one request-shaped object per country. These five keys are the whole of
    what that serializer reads; a field added there fails loudly here rather
    than silently writing the wrong country.
    """

    def __init__(self, request, regionIns):
        self.data = {
            "language": request.data.get("language"),
            "platform": request.data.get("platform"),
            "region": regionIns.region_name,
            "isocode": regionIns.region_code,
            "countryname": regionIns.region_country,
        }


def _add_regions(request):
    """The countries an add applies to, resolved against the Region table.

    The client sends region NAMES (Google domains, e.g. "google.co.in"); the
    isocode and country name are read from the matching row and never trusted
    from the body, so the three can never disagree -- the same rule
    kwconfig_save follows. "regions" carries the multi-country list; a body
    with only the legacy single "region" resolves to a one-item list. Order is
    the user's; repeats collapse.

    Returns (regions, error message) -- exactly one of the two is truthy.
    """
    raw = request.data.get("regions")
    if raw in (None, ""):
        raw = [request.data.get("region")]
    if not isinstance(raw, list):
        return [], "regions must be a list of countries."

    names = []
    for value in raw:
        name = str(value or "").strip()
        if name and name not in names:
            names.append(name)
    if not names:
        return [], "Select at least one country."

    rows = {}
    for regionIns in Region.objects.filter(region_name__in=names):
        rows[regionIns.region_name] = regionIns
    unknown = [name for name in names if name not in rows]
    if unknown:
        return [], "Unknown country: %s" % ", ".join(unknown)

    return [rows[name] for name in names], ""


# Add keyword engine.
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def addkeyv3(request):
    userid = request.data["userid"]
    grpid = request.data["grpid"]
    getLanguage = request.data["language"].strip()
    languageData = Language.objects.filter(language_name=getLanguage).first()
    # The language name comes straight from the request. An unrecognised one is
    # a bad request; this used to be a 500 on Add Keyword.
    if languageData is None:
        return JsonResponse({"status": "false", "message": "Unknown language: %s" % getLanguage})

    if userid and grpid and languageData.language_code:

        # Resolved before the keyword list so the plan check counts what will
        # actually be written: one row per keyword PER COUNTRY.
        regionList, regionError = _add_regions(request)
        if regionError:
            return _bad_request(regionError)

        dataChecklist = request.data["keyword"]
        if isinstance(dataChecklist, list) == False:
            dataCheckKeywords = request.POST["keyword"].replace("\n", ",").lower().strip()
            keywordArray = dataCheckKeywords.split(",")
            dataChecklist = list(set(filter(None, map(str.strip, keywordArray))))

        if len(dataChecklist) > 0:
            AccountIns = Accountusage.objects.filter(fb_user_id=userid).first()
            # changed
            sts, cnt = totalKeywordsCount(userid)
            keywrdCount = cnt
            # keywrdCount = Keyword.objects.filter(fk_user_id=userid).count()
            plannedCount = len(dataChecklist) * len(regionList)

            paystatus, payOverRule = userPaymode(userid, AccountIns)
            if paystatus not in ["dead", "cancelled", "expire"]:
                if AccountIns.plan_keyword_limit >= (plannedCount + keywrdCount):
                    # A new run must not inherit the previous run's reason.
                    refreshIns = Refreshmanual.objects.filter(fb_user_id=userid, fk_group_id=grpid).update(refresh_type="new", refresh_status="wait", refresh_error="", refresh_error_code="")
                    # One pass per country. Each pass writes and then clears its
                    # own "key" sentinel rows, so the next country's history
                    # back-fill cannot pick up the previous country's rows.
                    newKeyCount = 0
                    alreadyTracked = []
                    for regionIns in regionList:
                        created, existing = NewKeywordsInsert(userid, grpid, dataChecklist, request, languageData, regionIns)
                        newKeyCount += created
                        if existing:
                            alreadyTracked.append("%d in %s" % (len(existing), regionIns.region_country))

                    if newKeyCount == 0:
                        return Response({"status": "false", "message": "warning", "errormsg": "Already tracked, so nothing was added: " + ", ".join(alreadyTracked) + "."})

                    if newKeyCount > 0:
                        AccountIns.last_used_refresh_count = newKeyCount
                        AccountIns.save()
                    Groups.objects.filter(id=int(grpid)).update(manual_grp_trigger="INIT", strict_refresh_switch=True, last_used_refresh_count=newKeyCount)
                    trigger_engine_manual(userid, grpid)
                    SettingsData = Settings.objects.filter(id=1).first()
                    core_manual_mode = SettingsData.core_manual_mode if SettingsData and SettingsData.core_manual_mode else 0

                    if newKeyCount != plannedCount:
                        # Named per country: with several countries selected,
                        # "3 of 9 already exist" does not say which to fix.
                        newKeyError = "Already tracked, so not added again: " + ", ".join(alreadyTracked) + "."
                        newKeySuccess = str(newKeyCount) + " of " + str(plannedCount) + " keywords added"
                        return Response({"status": "true", "Engmd": core_manual_mode, "message": "warning", "errormsg": newKeyError, "successmsg": newKeySuccess, "kwcnt": int(newKeyCount)})
                    else:
                        return Response({"status": "true", "Engmd": core_manual_mode, "message": "Keyword added", "kwcnt": int(newKeyCount)})
                else:
                    availKeywrdsLimit = AccountIns.plan_keyword_limit - keywrdCount
                    # Says what was asked for as well as what fits: with N
                    # countries selected the request is N times the list.
                    newKeyError = "You can add only " + str(availKeywrdsLimit) + " keywords, and this adds " + str(plannedCount) + " (" + str(len(dataChecklist)) + " keywords in " + str(len(regionList)) + " countries)."
                    return Response({"status": "false", "message": "warning", "errormsg": newKeyError})
            else:
                return JsonResponse({"status": "false", "message": "Oops! Sorry You've no active subscription."})
        else:
            return JsonResponse({"status": "false", "message": "Invalid data!"})
    else:
        return JsonResponse({"status": "false", "message": "Something went wrong"})


def NewKeywordsInsert(userid, grpid, dataChecklist, request, languageData, regionIns=None):
    """Write one country's worth of keywords. Returns (created, already there).

    ``regionIns`` is the country this pass writes; without it the country is
    whatever the body's single "region" says, which is how the new-project
    wizard still calls it. The returned list is the keyword texts that were
    skipped, so the caller can name the country they already exist in.
    """

    # exactdomain = True if request.data['exactdomain']=='true' else False
    # if exactdomain == True:
    exactdomain = request.data["exactdomain"]
    if exactdomain:
        url = request.data["url"].strip()
    else:
        url = request.data["url"].lower().strip()

    # mydict = {}
    # mydict['target'] = url
    # mydict['se_name'] = request.data['region'].strip()
    # mydict['device'] = request.data['platform']
    # mydict['language_name'] = request.data['language']
    # mydict['language_code'] = languageData.language_code.strip()
    # mydict['location_name'] = settings.DEF_LOCATION

    manual_call_status = 0
    SettingsData = Settings.objects.filter(id=1).first()
    if SettingsData:
        if SettingsData.core_manual_mode == True:
            manual_call_status = 1

    domain = url if exactdomain == True else host_domain(url)
    # The country being written, and the request view the serializer gets. Both
    # come from the Region row when there is one, so the duplicate check and
    # the rows it guards are always asking about the same country.
    keywordRequest = _RegionScopedRequest(request, regionIns) if regionIns is not None else request
    region = regionIns.region_name if regionIns is not None else request.data["region"].strip()
    existsKW = list(Keyword.objects.filter(keyword__in=dataChecklist, site_url__contains=domain, exactdomain__in=[exactdomain], fk_group_id=grpid, region=region, platform=request.data["platform"]).values_list("keyword", flat=True))
    # print("existsKW", existsKW)
    # print("dataChecklist", dataChecklist)
    tags = []
    if "tags" in request.data:
        tags = request.data["tags"]
        if isinstance(tags, list) == False:
            tagstr = json.loads(request.data["tags"])
            # tags = list(set(map(itemgetter('text'), tagstr)))
            tags = list(set(map(lambda x: x["text"].lower().strip(), tagstr)))

    keywords = []
    newkeywords = set(dataChecklist) - set(existsKW)
    serializer = KeywordCreateSerializer(list(newkeywords), many=True, context={"userid": userid, "grpid": grpid, "existsKW": existsKW, "exactdomain": exactdomain, "tags": tags, "manual_call_status": manual_call_status, "request": keywordRequest, "languageData": languageData, "url": url})
    keywords = serializer.data

    if len(keywords) > 0:
        Keyword.objects.bulk_create(keywords)
        # djongo's bulk_create does not populate primary keys, so the rows just
        # written have to be read back. "key" is the sentinel the serializer
        # stamps on a row it has just built; it is cleared to "done" below.
        #
        # This read MUST be scoped to the requesting account, project and the
        # exact keyword texts of THIS call. Unscoped, two accounts adding
        # keywords in the same moment swept up each other's rows: A wrote
        # keywordhistory stamped with A's user/group ids against B's keyword
        # ids, then flipped B's rows to "done" -- so B's own call found nothing
        # left to back-fill and B got no history at all.
        #
        # The sentinel is still required after scoping: a group can hold the
        # same keyword text more than once (existsKW excludes by region and
        # platform too), so keyword__in alone would also match rows added
        # earlier and duplicate their history.
        new_ids = list(
            Keyword.objects.filter(
                fk_user_id=userid,
                fk_group_id=grpid,
                manual_call_mode="key",
                keyword__in=[keywordIns.keyword for keywordIns in keywords],
            ).values_list("id", flat=True)
        )
        kwHistryserializer = kwHistoryCreateSerializer(new_ids, many=True, context={"fk_user_id": userid, "fk_group_id": grpid})
        KeywordHistory.objects.bulk_create(kwHistryserializer.data)
        Keyword.objects.filter(id__in=new_ids).update(manual_call_mode="done")

    return len(keywords), existsKW


# ~~~~~~~~~~~~~~~~~~~~~New flow add keyword---------------------------


# ---------------------------------------------------------------------------
# PER-KEYWORD TRACKING CONFIGURATION
# ---------------------------------------------------------------------------
# Precedence, one direction only: a keyword's own value if it has one,
# otherwise the inherited default. Nothing is merged and nothing is implicit.
#   pages     keyword.serp_pages    -> Accountusage.serp_depth   (per account)
#   depth     keyword.serp_advanced -> Groups.serp_advanced      (per project)
# Both are cost multipliers on the account's own DataBlue key, so the resolved
# value AND where it came from are reported together -- a number with no tier
# beside it is what let two settings disagree with no way to see which won.
KW_PAGES_MIN = 1
KW_PAGES_MAX = 10
KW_PLATFORMS = ("desktop", "mobile")

# Distinguishes an absent key ("leave this field alone") from an explicit null
# ("clear the override"). None cannot do that job here; it is a real value.
_UNSET = object()


def _account_pages(accountIns):
    """The account's pages-per-keyword, floored at 1. 0/None means never set."""
    return int(getattr(accountIns, "serp_depth", 0) or 0) or KW_PAGES_MIN


def _keyword_config(keyIns, grpData, accountIns):
    """Resolved configuration for one keyword, with the tier each value came from."""
    account_pages = _account_pages(accountIns)
    project_advanced = bool(grpData.serp_advanced) if grpData else False

    kw_pages = keyIns.serp_pages
    kw_advanced = keyIns.serp_advanced

    regionIns = Region.objects.filter(region_name=keyIns.region).first()

    return {
        "pages": {
            "value": int(kw_pages) if kw_pages is not None else account_pages,
            "override": int(kw_pages) if kw_pages is not None else None,
            "inherited": account_pages,
            "source": "keyword" if kw_pages is not None else "account",
        },
        "advanced": {
            "value": bool(kw_advanced) if kw_advanced is not None else project_advanced,
            "override": bool(kw_advanced) if kw_advanced is not None else None,
            "inherited": project_advanced,
            "source": "keyword" if kw_advanced is not None else "project",
        },
        "platform": keyIns.platform,
        "region": keyIns.region,
        "isocode": keyIns.isocode,
        "countryname": regionIns.region_country if regionIns else "",
        "language": keyIns.language,
        "exactdomain": bool(keyIns.exactdomain),
        "url": keyIns.site_url,
        "limits": {"pagesMin": KW_PAGES_MIN, "pagesMax": KW_PAGES_MAX},
    }


def _as_bool(value):
    """Form posts send the string "false", and bool("false") is True."""
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _bad_request(message):
    return JsonResponse({"status": "false", "message": message}, status=400)


def _url_host(value):
    """Host of a URL that may have been stored without a scheme.

    Keyword.site_url holds whatever the add form built, and that is often
    "example.com/page" with no scheme -- urlparse puts the whole thing in
    .path and host_domain then returns "". Comparing that against the
    project's scheme-carrying domain_name rejects the value the row already
    holds, so re-saving a keyword unchanged failed.
    """
    value = str(value or "").strip().lower()
    if value and "//" not in value:
        value = "https://" + value
    return host_domain(value)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwconfig_save(request):
    """Change one keyword's tracking configuration.

    Accepts any subset of the fields; an absent key is left alone, and an
    explicit null on pages/adv clears that override so the keyword goes back
    to inheriting. Every value is validated against the same tables the add
    form draws from, so a keyword can never hold a region the engine cannot
    resolve to a Google domain.

    This deliberately does NOT re-rank. A configuration change describes the
    next check; re-running one here would spend a provider credit per keyword
    on what the user experienced as editing a form.
    """
    if not (request.method == "POST" and authPermission.validate(request, "POST")):
        return JsonResponse({"status": "false", "message": "Something went wrong"})

    userid = str(request.data.get("userid") or "").strip()
    grpid = str(request.data.get("grpid") or "").strip()
    kwid = str(request.data.get("kwid") or "").strip()
    if not (userid.isdigit() and grpid.isdigit() and kwid.isdigit()):
        return _bad_request("Provide userid, grpid and kwid.")

    keyIns = Keyword.objects.filter(id=int(kwid), fk_user_id=userid, fk_group_id=grpid).first()
    if keyIns is None:
        return JsonResponse({"status": "false", "message": "Keyword not found."})

    grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
    if grpData is None:
        return JsonResponse({"status": "false", "message": "Project not found."})
    accountIns = Accountusage.objects.filter(fb_user_id=userid).first()

    changes = {}

    # -- pages: int within range, or null to inherit the account setting
    pages = request.data.get("pages", _UNSET)
    if pages is not _UNSET:
        if pages is None or pages == "":
            changes["serp_pages"] = None
        else:
            try:
                pages = int(pages)
            except (TypeError, ValueError):
                return _bad_request("pages must be a whole number.")
            if not (KW_PAGES_MIN <= pages <= KW_PAGES_MAX):
                return _bad_request("pages must be between %d and %d." % (KW_PAGES_MIN, KW_PAGES_MAX))
            changes["serp_pages"] = pages

    # -- adv: Lite/Advanced, or null to inherit the project setting
    adv = request.data.get("adv", _UNSET)
    if adv is not _UNSET:
        changes["serp_advanced"] = None if adv is None or adv == "" else _as_bool(adv)

    # -- platform
    platform = request.data.get("platform", _UNSET)
    if platform is not _UNSET:
        platform = str(platform or "").strip().lower()
        if platform not in KW_PLATFORMS:
            return _bad_request("platform must be one of: %s." % ", ".join(KW_PLATFORMS))
        changes["platform"] = platform

    # -- region: the Google domain the engine searches. isocode and the
    #    country name are derived from the same row rather than trusted from
    #    the client, so the three can never disagree.
    region = request.data.get("region", _UNSET)
    if region is not _UNSET:
        region = str(region or "").strip()
        regionIns = Region.objects.filter(region_name=region).first()
        if regionIns is None:
            return _bad_request("Unknown region: %s" % region)
        changes["region"] = regionIns.region_name
        changes["isocode"] = regionIns.region_code
        changes["location"] = regionIns.region_name + "(" + regionIns.region_country + ")"

    # -- language: name in, code derived
    language = request.data.get("language", _UNSET)
    if language is not _UNSET:
        language = str(language or "").strip()
        languageData = Language.objects.filter(language_name=language).first()
        if languageData is None:
            return _bad_request("Unknown language: %s" % language)
        changes["language"] = languageData.language_name
        changes["language_code"] = languageData.language_code.strip()

    # -- exactdomain: whole-URL match instead of whole-domain match
    exactdomain = request.data.get("edm", _UNSET)
    if exactdomain is not _UNSET:
        changes["exactdomain"] = _as_bool(exactdomain)

    # -- target URL. Must stay on the project's own domain: site_url is what
    #    the matcher compares against, so pointing it elsewhere would record
    #    another site's ranking as this project's.
    url = request.data.get("url", _UNSET)
    if url is not _UNSET:
        url = str(url or "").strip()
        if not url:
            return _bad_request("Enter the page you expect to rank.")
        if _url_host(url) != _url_host(grpData.domain_name):
            return _bad_request("The tracked page must be on %s." % grpData.domain_name)
        changes["site_url"] = url
        changes["target"] = url

    if not changes:
        return _bad_request("Nothing to change.")

    # A project may hold the same keyword text more than once -- once per
    # region/platform combination -- so an edit that lands on a combination
    # already tracked would leave two rows measuring the same search.
    dup_region = changes.get("region", keyIns.region)
    dup_platform = changes.get("platform", keyIns.platform)
    dup_exact = changes.get("exactdomain", keyIns.exactdomain)
    dup_url = changes.get("site_url", keyIns.site_url)
    if (dup_region, dup_platform, dup_exact, dup_url) != (keyIns.region, keyIns.platform, keyIns.exactdomain, keyIns.site_url):
        clash = Keyword.objects.filter(
            fk_user_id=userid,
            fk_group_id=grpid,
            keyword=keyIns.keyword,
            region=dup_region,
            platform=dup_platform,
            exactdomain__in=[dup_exact],
            site_url=dup_url,
        ).exclude(id=int(kwid)).exists()
        if clash:
            return _bad_request("This project already tracks that keyword on the same page, country and device.")

    changes["modified_date"] = timezone.now()
    Keyword.objects.filter(id=int(kwid), fk_user_id=userid, fk_group_id=grpid).update(**changes)

    keyIns = Keyword.objects.filter(id=int(kwid), fk_user_id=userid, fk_group_id=grpid).first()
    return JsonResponse({
        "status": "true",
        "message": "Keyword configuration saved",
        "cfg": _keyword_config(keyIns, grpData, accountIns),
    })


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwconfig_reset(request):
    """Clear per-keyword overrides across one project, or count them.

    This is what the project-level Lite/Advanced control is FOR, beyond being
    the default a new keyword inherits: it is also the way back. Without it a
    project setting could be contradicted by keywords the user had forgotten
    setting, with no way to see how many or to undo them in one move.

    POST without "scope" reports the counts and changes nothing.
    """
    if not (request.method == "POST" and authPermission.validate(request, "POST")):
        return JsonResponse({"status": "false", "message": "Something went wrong"})

    userid = str(request.data.get("userid") or "").strip()
    grpid = str(request.data.get("grpid") or "").strip()
    if not (userid.isdigit() and grpid.isdigit()):
        return _bad_request("Provide userid and grpid.")

    rows = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid)
    scope = str(request.data.get("scope") or "").strip().lower()

    if scope:
        if scope not in ("pages", "advanced", "all"):
            return _bad_request("scope must be pages, advanced or all.")
        if scope in ("pages", "all"):
            rows.exclude(serp_pages=None).update(serp_pages=None)
        if scope in ("advanced", "all"):
            rows.exclude(serp_advanced=None).update(serp_advanced=None)

    return JsonResponse({
        "status": "true",
        "pages": rows.exclude(serp_pages=None).count(),
        "advanced": rows.exclude(serp_advanced=None).count(),
        "total": rows.count(),
    })


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwaddcost(request):
    """Result pages per check for this account -- the add form's cost multiplier.

    The add-keyword form has to state, before the user submits, how many
    DataBlue requests a day the keywords they are about to create will spend.
    That number is keywords x countries x PAGES, and pages is the one factor
    the form had no way to read: /getsetting does not carry it and the settings
    endpoint that does performs a live provider balance call, which is not
    something a form load should trigger.

    Read-only, and it never guesses: a caller that cannot read this gets no
    number rather than a default that would understate the bill.
    """
    if not (request.method == "POST" and authPermission.validate(request, "POST")):
        return JsonResponse({"status": "false", "message": "Something went wrong"})

    userid = str(request.data.get("userid") or "").strip()
    if not userid.isdigit():
        return _bad_request("Provide userid.")

    accountIns = Accountusage.objects.filter(fb_user_id=userid).first()
    if accountIns is None:
        return JsonResponse({"status": "false", "message": "No account usage record found"})

    return JsonResponse({"status": "true", "pages": _account_pages(accountIns)})


# keyword page details
@api_view(["POST"])
def keyload(request):
    # Ahead of validate(): it refuses a missing userid by returning False,
    # which drops the request into the generic trailing response.
    absent = missing_fields(request, "userid", "grpid", "kwid", "type")
    if absent:
        return bad_request(absent)
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        # int() on a non-numeric kwid raised ValueError, which is a 500
        # for what is plainly a bad request.
        if not str(request.data["kwid"]).strip().isdigit():
            return invalid_request("kwid")
        kwid = int(request.data["kwid"])
        apitype = request.data["type"]
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                keyIns = Keyword.objects.filter(id=kwid, fk_user_id=userid, fk_group_id=grpid).first()
                if keyIns is None:
                    return JsonResponse({"status": "false", "message": "Keyword not found."})

                unqtags = list(Keyword.objects.exclude(tags=[]).filter(fk_user_id=userid, fk_group_id=grpid).values_list("tags", flat=True).all())
                if len(unqtags) > 0:
                    unqtags = list(set(numpy.concatenate(unqtags).flat))
                Count = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, manual_call_status__in=[True]).count()
                mrKey = "onk" if Count > 0 else "off"

                if apitype == "half":
                    serializer = {}
                    serializer["CR"] = keyIns.page_uuid_url
                    serializer["tg"] = keyIns.tags
                    serializer["AV"] = keyIns.search_volume
                    serializer["spt"] = keyIns.keyword_snippet["tdy"]
                    serializer["spb"] = keyIns.keyword_snippet["best"]
                    serializer["lct"] = Region.objects.filter(region_code=keyIns.isocode).first().region_country
                    serializer["lrupt"] = timeDifference(keyIns.lastranked_date)
                    serializer["nt"] = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid).count()
                    # Both branches publish it: arriving from the keywords
                    # table takes the "half" path, and a config the page can
                    # only show on a direct URL is a config half the users
                    # never see.
                    serializer["cfg"] = _keyword_config(
                        keyIns,
                        Groups.objects.filter(fk_user_id=userid, id=grpid).first(),
                        Accountusage.objects.filter(fb_user_id=userid).first(),
                    )
                    # Same reasoning, and it became load-bearing: the keywords
                    # table used to carry the WHOLE serp_features record, so
                    # this branch could leave it out and the page would read it
                    # off the row it navigated from. The table now sends only
                    # what the table draws -- a glyph's worth of ai_overview,
                    # no blocks and no raw answer text -- so anything this
                    # branch omits is simply absent on the "half" path, which
                    # is the path a user takes by CLICKING A KEYWORD. That left
                    # the panel with an AI Overview chip, its cited sources,
                    # and no answer or feature rows at all.
                    serializer["sf"] = keyIns.serp_features or {}
                    serializer["sfm"] = bool(keyIns.serp_features)
                    # Third field on the same list, for the same reason. The
                    # overview stat and the history chart both read RC to word
                    # an out-of-range result ("not in the first 30"), and this
                    # branch only ever had it because the merge kept the table
                    # row's copy. Publish it rather than depend on that.
                    # apply_rank_state writes RS/RC/RSK and RETURNS the
                    # position; RW is the caller's to assign, so that a
                    # serializer keying it differently can.
                    serializer["RW"], _rs, _rc, _rsk = apply_rank_state(
                        serializer, keyIns,
                        _account_pages(Accountusage.objects.filter(fb_user_id=userid).first()),
                    )
                    # keyword_slug = f"{keyIns.keyword}".replace(" ", "_")
                    # svolData = keywordVolume.objects.filter(keyword_slug=keyword_slug,region_code=keyIns.isocode).first()
                    # if svolData != None:
                    #     serializer['ASV'] = svolData.month_wise_volume
                    #     serializer['ASVM'] = svolData.past_months
                    # else:
                    #     serializer['ASV'] = []
                    #     serializer['ASVM'] = []

                    return JsonResponse({"status": "true", "data": serializer, "mrK": mrKey})
                else:
                    # The out-of-range ceiling comes from the depth actually
                    # searched: this keyword's own serp_pages, else the
                    # account's serp_depth, which is 1 when never chosen.
                    serializer = KeywordPageSerializer(
                        [keyIns], many=True,
                        context={"account_pages": _account_pages(
                            Accountusage.objects.filter(fb_user_id=userid).first()
                        )},
                    ).data[0]
                    grpData = Groups.objects.filter(fk_user_id=userid, id=grpid).first()
                    userlogid = request.data["logid"] if "logid" in request.data else userid
                    # Homeserializer = kWPageHomeSerializer([grpData], many=True, context={'logid': userlogid})
                    Homeserializer = AppGroupSerializer([grpData], many=True, context={"logid": userlogid})
                    Homeserializer = Homeserializer.data[0] if Homeserializer.data[0] else Homeserializer.data
                    serializer["cfg"] = _keyword_config(keyIns, grpData, Accountusage.objects.filter(fb_user_id=userid).first())

                    return JsonResponse({"status": "true", "data": serializer, "utg": unqtags, "hdata": Homeserializer, "mrK": mrKey})

    return JsonResponse({"status": "false", "message": "Something went wrong"})


# keyword Ads details
@api_view(["POST"])
def kwads(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                KWHstryIns = KeywordHistory.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid).first()
                # A KeywordHistory row appears the first time a keyword is
                # ranked. Before that there is nothing to show, which is not an
                # error -- it is the answer. This used to dereference None and
                # return 500, so on a fresh install every newly added keyword
                # broke its own detail panel.
                if KWHstryIns is None:
                    return JsonResponse({"status": "true", "lst": []})

                if "list" in KWHstryIns.ad_snippet_history and "recent" in KWHstryIns.ad_snippet_history:
                    adlist = KWHstryIns.ad_snippet_history["list"]
                    adrecent = KWHstryIns.ad_snippet_history["recent"]
                else:
                    adlist = {}
                    adrecent = []

                for key, value in adlist.items():
                    value["dm"] = key
                    value["rc"] = 1 if key in adrecent else 0
                    del value["dt"]

                return JsonResponse({"status": "true", "lst": list(adlist.values())})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


# keyword competitors details
@api_view(["POST"])
def kwcmptrs(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                KWHstryIns = KeywordHistory.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid).first()
                # Same as kwads: no ranking run yet means no competitors yet.
                if KWHstryIns is None:
                    empty = {"tp": []} if "tp" == request.data.get("type") else {}
                    return JsonResponse({"status": "true", "cmp": empty})

                if "tp" == request.data["type"]:
                    comp = KWHstryIns.comp_today["tp"] if "tp" in KWHstryIns.comp_today else []
                    return JsonResponse({"status": "true", "cmp": {"tp": comp}})

                return JsonResponse({"status": "true", "cmp": KWHstryIns.comp_today})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


# keyword Ads details
@api_view(["POST"])
def kwsvolume(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                keyIns = Keyword.objects.filter(id=kwid, fk_user_id=userid, fk_group_id=grpid).first()
                # Not this account's keyword, or deleted since the page loaded.
                if keyIns is None:
                    return JsonResponse({"status": "false", "message": "Something went wrong."})

                keyword_slug = f"{keyIns.keyword}".replace(" ", "_")
                svolData = keywordVolume.objects.filter(keyword_slug=keyword_slug, region_code=keyIns.isocode).first()
                serializer = {}
                serializer["AV"] = keyIns.search_volume
                if svolData != None:
                    serializer["ASV"] = svolData.month_wise_volume
                    serializer["ASVM"] = svolData.past_months
                    serializer["CLV"] = svolData.comp_level.capitalize() if svolData.comp_level != "UNSPECIFIED" else "-"
                    if svolData.comp_index != "-" and svolData.comp_level in comp_levels:
                        serializer["CID"] = svolData.comp_index
                else:
                    serializer["ASV"] = []
                    serializer["ASVM"] = []
                    serializer["CLV"] = "-"
                    serializer["CID"] = "-1"

                return JsonResponse({"status": "true", "sv": serializer})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


def _note_day_bounds(value):
    """Return timezone-aware boundaries for a note's local calendar day."""
    date_format = "%Y-%m-%d" if len(value.split("-", 1)[0]) == 4 else "%y-%m-%d"
    selected_day = datetime.strptime(value, date_format).date()
    current_timezone = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(selected_day, time.min), current_timezone)
    end = timezone.make_aware(datetime.combine(selected_day, time.max), current_timezone)
    return start, end


# keyword note details
@api_view(["POST"])
def kwnts(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                selectdate = request.data["sld"] if "sld" in request.data else str(date.today())
                enddate = request.data["ed"] if "ed" in request.data else selectdate
                start, _ = _note_day_bounds(selectdate)
                _, end = _note_day_bounds(enddate)
                NoteIns = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).all().order_by("note_date")
                # NoteIns = kwNotes.objects.filter(note_date__range=(start, end)).all().order_by('note_date')
                serializer = kwNotesSerializer(NoteIns, many=True).data
                return JsonResponse({"status": "true", "nts": serializer})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwnt_create(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid:
                title = request.data["tle"]
                note = request.data["nt"]
                selectdate = request.data["sld"]
                if len(title) > 0 and len(note) > 0:
                    start, end = _note_day_bounds(selectdate)
                    NoteInsCnt = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).count()
                    if NoteInsCnt < 5:
                        notesIns = kwNotes()
                        notesIns.fk_user_id = userid
                        notesIns.fk_group_id = grpid
                        notesIns.fk_keyword_id = kwid
                        notesIns.title = title
                        notesIns.notes = note
                        notesIns.note_date = start
                        notesIns.save()
                        NoteIns = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).all()
                        serializer = kwNotesSerializer(NoteIns, many=True).data
                        return JsonResponse({"status": "true", "nts": serializer, "message": "Notes added successfully"})
                    else:
                        return JsonResponse({"status": "false", "message": "The maximum allowed notes limit is 5"})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwnt_update(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        noteid = int(request.data["ntid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid and noteid:
                title = request.data["tle"]
                note = request.data["nt"]
                if len(title) > 0 and len(note) > 0:
                    noteupdate = kwNotes.objects.filter(id=noteid, fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid).update(title=title, notes=note)
                    selectdate = request.data["sld"] if "sld" in request.data else str(date.today())

                    start, end = _note_day_bounds(selectdate)
                    NoteIns = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).all()
                    serializer = kwNotesSerializer(NoteIns, many=True).data
                    return JsonResponse({"status": "true", "nts": serializer, "message": "Notes updated successfully"})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def kwnt_delete(request):
    if request.method == "POST" and authPermission.validate(request, "POST"):
        userid = request.data["userid"]
        grpid = request.data["grpid"]
        kwid = int(request.data["kwid"])
        noteid = int(request.data["ntid"])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and kwid and noteid > 0:
                noteupdate = kwNotes.objects.filter(id=noteid, fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid).delete()
                selectdate = request.data["sld"] if "sld" in request.data else str(date.today())

                start, end = _note_day_bounds(selectdate)
                NoteIns = kwNotes.objects.filter(fk_keyword_id=kwid, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).all()
                serializer = kwNotesSerializer(NoteIns, many=True).data
                return JsonResponse({"status": "true", "nts": serializer, "message": "Notes deleted successfully"})

    return JsonResponse({"status": "false", "message": "Something went wrong."})


# CONNECT GSC
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def gsc_token(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            gCode = str(request.data["gcode"])

            if userId.isdigit() and gCode:
                header = {"Accept-Encoding": "gzip", "User-Agent": "tracker"}
                url = "https://accounts.google.com/o/oauth2/token"
                datar = {
                    "grant_type": "authorization_code",
                    "code": gCode,
                    "client_id": GSC_CLIENT_ID,
                    "client_secret": GSC_SECRET_ID,
                    "redirect_uri": GSC_REDIRECT_URL,
                    "scope": "https://www.googleapis.com/auth/webmasters.readonly",
                }
                xRequest = requests.post(url, data=datar, headers=header)
                refresh_token = xRequest.json()["refresh_token"]
                access_token = xRequest.json()["access_token"]
                if refresh_token is None or access_token is None:
                    return JsonResponse({"status": "false", "message": "Unable to establish a connection with Google Search Console."})
                else:
                    all_gsc_properties = []
                    headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
                    xrequest = requests.get("https://www.googleapis.com/webmasters/v3/sites/", headers=headers)
                    if xrequest.status_code in [200]:
                        gsc_properties = xrequest.json()
                        if len(gsc_properties["siteEntry"]) > 0:
                            all_gsc_properties = [each_property["siteUrl"] for each_property in gsc_properties["siteEntry"]]

                    return JsonResponse({"status": "true", "gsc_refresh_token": refresh_token, "gsc_access_token": access_token, "gsc_properties": all_gsc_properties})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


# CONNECT GSC
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def connect_gsc(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])
            # gCode = str(request.data["gcode"])
            type = str(request.data["type"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).first()

                if groupExists:

                    if type == "revoke":
                        del_rprts = ['gsc_queries', 'gsc_non_branded_queries', 'gsc_branded_queries', 'gsc_overview', 'gsc_pages']
                        Groups.objects.filter(id=int(grpId)).update(gsc_refresh_token="", gsc_property="")
                        GSCDailyResult.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GSCWeeklyResult.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GSCMonthlyResult.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GSCDailyQuery.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GSCWeeklyQuery.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GSCMonthlyQuery.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        ReportSheets.objects.filter(fk_user_id=userId, fk_group_id=grpId, type__in=del_rprts).delete()
                        # ReportManager.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        # ReportSheets.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        return JsonResponse({"status": "true", "message": "GSC Account Revoked"})

                    if type == "verify":
                        gscStatus = False if not groupExists.gsc_property or groupExists.gsc_property is None else True
                        return JsonResponse({"status": gscStatus, "gsc_refresh_token": groupExists.gsc_refresh_token, "gsc_property": groupExists.gsc_property, "message": "GSC Account Status"})

                    refresh_token = str(request.data["gsc_refresh_token"])
                    gsc_property = str(request.data["gsc_property"])
                    if not DomainTracking.objects.filter(fk_user_id=userId, fk_group_id=grpId).exists():
                        dm_name=Groups.objects.filter(fk_user_id=userId, id=grpId).values('domain_name').first()['domain_name']
                        DomainTracking.objects.create(fk_user_id=userId, fk_group_id=grpId, domain=dm_name, track_status="scheduled", track_scheduled_at=timezone.now())
                    Groups.objects.filter(id=int(grpId)).update(gsc_refresh_token=refresh_token, gsc_property=gsc_property)
                    if GSCDailyResult.objects.filter(fk_user_id=userId, fk_group_id=grpId).exists():
                        GSCDailyResult.objects.filter(fk_user_id=userId, fk_group_id=grpId).update(track_scheduled_at=datetime.today() - relativedelta(days=2))
                    else:
                        GSCDailyResult.objects.create(fk_user_id=userId, fk_group_id=grpId, track_scheduled_at=datetime.today() - relativedelta(days=2))
                    return JsonResponse({"status": "true", "gsc_refresh_token": groupExists.gsc_refresh_token, "gsc_property": groupExists.gsc_property, "message": "GSC Connection has been established"})
                else:
                    return JsonResponse({"status": "false", "message": "Something went wrong"})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


# CONNECT GA
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def connect_ga(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])
            gCode = str(request.data["gcode"])
            type = str(request.data["type"])


            if userId.isdigit() and grpId.isdigit():
                groupExists = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId).first()

                if groupExists:
                    if type == "revoke":
                        del_rprts = ['ga_landing_pages', 'ga_overview']
                        GroupSetting.objects.filter(fk_group_id=grpId).update(ga_refresh_token="", ga_property="")
                        GA_weekly_monitor.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GA_monthly_monitor.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GA_daily_monitor.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GA_weekly_reports.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GA_monthly_reports.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        GA_daily_reports.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        ReportSheets.objects.filter(fk_user_id=userId, fk_group_id=grpId, type__in=del_rprts).delete()
                        # ReportManager.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        # ReportSheets.objects.filter(fk_user_id=userId, fk_group_id=grpId).delete()
                        return JsonResponse({"status": "true", "message": "GA Account Revoked"})

                    if type == "verify":
                        gscStatus = False if not groupExists.ga_refresh_token or groupExists.ga_refresh_token is None else True
                        track_day = groupExists.week_track_day
                        platform = req_rev_platform.get(groupExists.site_platform, '')
                        return JsonResponse({"status": gscStatus, "message": "GA Account Status", 'dt':track_day, 'pltform':platform})

                else:
                    return JsonResponse({"status": "false", "message": "Something went wrong"})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def ga_connection(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = request.data["userid"]
            grpId = request.data["grpid"]
            ga_property = request.data["ga_property"]
            ga_refresh_token = request.data["ga_token"]
            required_field = ["userid", "grpid", "ga_property", "ga_token"]

            if not all(item in request.data for item in required_field):
                return JsonResponse({"st": 0, "dt": "One or more required fields are missing."})


            if userId.isdigit() and grpId.isdigit():
                groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).first()

                if groupExists:
                    grpSettings = GroupSetting.objects.filter(fk_user_id=userId, fk_group_id=grpId)
                    updtd=grpSettings.update(ga_property=ga_property, ga_refresh_token=ga_refresh_token)

                    if updtd:
                        weekDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        dayValue = 0
                        if grpSettings.first().week_track_day:
                            dayValue = weekDays.index(grpSettings.first().week_track_day)
                        gWObj, created = GA_weekly_monitor.objects.get_or_create(fk_user_id=userId, fk_group_id=grpId, track_status="done", track_scheduled_start=datetime.now())
                        gMObj, created = GA_monthly_monitor.objects.get_or_create(fk_user_id=userId, fk_group_id=grpId, track_status="done", track_scheduled_start=datetime.now())
                        gDObj, created = GA_daily_monitor.objects.get_or_create(fk_user_id=userId, fk_group_id=grpId, track_mode="yearly", track_status='start', track_scheduled_start=datetime.now())
                        return JsonResponse({"st": 1, "dt": "Your GA account has been successfully connected."})
        return JsonResponse({"st": 0, "dt": "Something went wrong"})
    except Exception as e:
        print(str(e))
        return JsonResponse({"st": 0, "dt": f"Something went wrong {str(e)}"})


# branded_keywords
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def project_branded_keywords(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            userId = str(request.data["userid"])
            grpId = str(request.data["grpid"])
            type = request.data["type"]
            brand_keywords = []

            required_fields = ["userid", "grpid", "type"]

            if not all(item in request.data for item in required_fields):
                return JsonResponse({"st": 0, "dt": "One or more required fields are missing."})

            group_data = Groups.objects.filter(fk_user_id=userId, id=grpId).first()

            if group_data:

                brand_keywords = group_data.brand_keywords if group_data.brand_keywords else []

                if type == "save":
                    if "brand_keywords" not in request.data:
                        return JsonResponse({"status": "false", "message": "Something went wrong"})

                    if "brand_keywords" in request.data:
                        brand_keywords = request.data["brand_keywords"]

                    if isinstance(brand_keywords, list) == False:
                        brand_keywords_str = json.loads(request.data["brand_keywords"])
                        brand_keywords = list(set(map(lambda x: x["text"].lower().strip(), brand_keywords_str)))

                    keywords_updated = Groups.objects.filter(fk_user_id=userId, id=grpId).update(brand_keywords=brand_keywords)
                    if keywords_updated:
                        return JsonResponse({"status": "true", "message": "Keywords added successfully"})
                    else:
                        return JsonResponse({"status": "false", "message": "Something went wrong"})
                else:
                    return JsonResponse({"status": "true", "brand_keywords": brand_keywords})
            else:
                return JsonResponse({"status": "false", "message": "Something went wrong"})
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
    except Exception as e:
        return JsonResponse({"status": "false", "message": "Something went wrong"})

def reset_weekly_schedule(userid, grpid):
    try:
        if GSCDailyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists() and GSCWeeklyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GSCWeeklyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_status='scheduled')
            GSCDailyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_status='scheduled')
            if GSCWeeklyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
                GSCWeeklyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        if GA_daily_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GA_daily_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_mode='weekly', track_scheduled_start=datetime.now())
            if GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
                GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
    except Exception as e:
        print('reset_weekly_schedule', str(e))

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def Reset_track_day(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            if {'userid', 'grpid', 'trackday'}.issubset(request.data.keys()):
                userid = request.data['userid']
                grpid = request.data['grpid']
                trackDay = request.data['trackday']
                grpsttngupdtd=GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(week_track_day=trackDay)
                if grpsttngupdtd:
                    reset_weekly_schedule(userid, grpid)
                    return JsonResponse({'st':1, 'dt':'Rescheduled'})
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
    except Exception as e:
        print(str(e))
        return JsonResponse({'st':0, 'dt':'Something went wrong'})

def initialize__crawler(userid, grpid):
    try:
        GA_daily_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        GSCWeeklyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        GSCMonthlyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        GSCDailyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
        
        if GSCDailyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GSCDailyResult.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(track_scheduled_at=datetime.today() - relativedelta(days=2), track_status='scheduled')
        if GA_weekly_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GA_weekly_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid,).update(track_status="done", track_scheduled_start=datetime.now())
        if GA_monthly_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GA_monthly_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid,).update(track_status="done", track_scheduled_start=datetime.now())
        if GA_daily_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
            GA_daily_monitor.objects.filter(fk_user_id=userid, fk_group_id=grpid,).update( track_mode="yearly", track_status='start', track_scheduled_start=datetime.now())
    except Exception as e:
        print(str(e))
        return False

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def reset_platform(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            if {'userid', 'grpid', 'pltform'}.issubset(request.data.keys()):
                userid = request.data['userid']
                grpid = request.data['grpid']
                platform = request.data['pltform']
                reset__type = request.data['resetType']
                grpsttngupdtd=GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(site_platform=req_platform.get(platform, ''))
                rptMnger=ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(site_platform=req_platform.get(platform, ''))
                ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
                ReportManager.objects.filter(fk_user_id=userid, fk_group_id=grpid).delete()
                if DomainTracking.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists():
                    DomainTracking.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(da_metrics=[], dr_metrics=[], page_speed_metrics=[], track_status='scheduled', track_scheduled_at=datetime.now())
                if grpsttngupdtd:
                    if reset__type:
                        initialize__crawler(userid, grpid)
                    return JsonResponse({'st':1, 'msg':f'Changed Platform to {platform}', 'dt':platform})
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
    except Exception as e:
        print(str(e))
        return JsonResponse({'st':0, 'dt':'Something went wrong'})
