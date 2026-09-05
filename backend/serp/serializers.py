from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS
from django.utils import timezone
from .models import *
from serp.rank_state import apply_rank_state
from serp.common import *
from mailend.models import KeywordHistory
from account.models import Account
from bisect import bisect_right
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse
import string, random
from serp import calculation
from shared.scoring import calculate_visibility_history
from collections import defaultdict

import collections
import numpy

comp_levels = ["LOW", "MEDIUM", "HIGH"]
current_day = date.today()
this_week_first_date = current_day - timedelta(days=current_day.isoweekday())
this_week_days = (this_week_first_date - current_day).days
this_week_day = abs(this_week_days) + 1

# class DashHomeSerializer(serializers.ModelSerializer):
# 	G_N = serializers.SerializerMethodField('get_G_N')
# 	D_N = serializers.SerializerMethodField('get_D_N')
# 	class Meta:
# 		model = Groups
# 		fields = ('G_N', 'D_N')

# 	def get_G_N(self, obj):
# 		return obj.group_name

# 	def get_D_N(self, obj):
# 		return obj.domain_name

# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj)

# 		superData['sb_s'] = ""
# 		superData['dn_d'] = obj.domain_info
# 		superData['dn_s'] = obj.domain_status

# 		# Group Based Keywords
# 		grpKeyData = Keyword.objects.filter(fk_group_id=obj.id,fk_user_id=obj.fk_user_id)

# 		grpData = Groups.objects.filter(fk_user_id=obj.fk_user_id,id=obj.id).first()
# 		superData['g_age'] = len(grpData.score_meter)

# 		refreshData = Refreshmanual.objects.filter(fb_user_id=obj.fk_user_id,fk_group_id=obj.id).values('refresh_time').first()

# 		logid = self.context["logid"] if "logid" in self.context else obj.fk_user_id
# 		accountData = Accountusage.objects.filter(fb_user_id=logid).first()
# 		# accountData = Accountusage.objects.filter(fb_user_id=obj.fk_user_id).values('last_used_refresh_count', 'st_subscription_id', 'st_customer_id', 'st_purchase_id', 'plan_keyword_limit', 'plan_refresh_limit', 'used_refresh_limit').first()

# 		if accountData:
# 			superData['sb_s'], pOverRule = userPaymode(logid, accountData)
# 			# payData = UserSubscriptions.objects.filter(fk_user_id=obj.fk_user_id, st_subscription_id=accountData['st_subscription_id'], st_customer_id=accountData['st_customer_id'], fk_reference_type="MAIN").last()
# 			# if payData:
# 			# 	if payData.st_subscription_status == "SUBSCRIBED" and payData.st_pay_status == "PAID":
# 			# 		superData['sb_s'] = "active"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "PAID":
# 			# 		superData['sb_s'] = "active"
# 			# 	elif payData.st_subscription_status == "CANCEL" and payData.st_pay_status == "DROP":
# 			# 		superData['sb_s'] = "cancelled"
# 			# 	elif payData.st_subscription_status == "EXPIRE" and payData.st_pay_status == "FAIL":
# 			# 		superData['sb_s'] = "expire"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "UPDATING":
# 			# 		superData['sb_s'] = "renewal-update"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "FAIL":
# 			# 		superData['sb_s'] = "renewal-fail"

# 		superData['rf_t'] = timeDifference(refreshData['refresh_time']) if 'refresh_time' in refreshData else timeDifference(obj.updated_date)

# 		# Total Groups
# 		grpAll = Groups.objects.filter(fk_user_id=logid)
# 		superData['g_ln'] = grpAll.count()

# 		# User Total Keywords
# 		usrKeyData = Keyword.objects.filter(fk_user_id=logid)
# 		superData['u_kw'] = usrKeyData.count()
# 		superData['luRc'] = accountData.last_used_refresh_count if accountData.last_used_refresh_count else 0
# 		superData['tYP'] = accountData.st_purchase_id if accountData.st_purchase_id else 0
# 		superData['pKL'] = accountData.plan_keyword_limit if accountData.plan_keyword_limit else 0
# 		superData['pRL'] = accountData.plan_refresh_limit if accountData.plan_refresh_limit else 0
# 		superData['pPL'] = accountData.plan_project_limit if accountData.plan_project_limit else 1
# 		superData['uRL'] = accountData.used_refresh_limit if accountData.used_refresh_limit else 0

# 		superData['kw_ln'] = grpKeyData.count()

# 		return  superData


def append_duration_text(track_date):
    try:
        if track_date:
            last_week = track_date - timedelta(days=7)
            track_starts_before = last_week - timedelta(days=9)
            track_ends_before = last_week - timedelta(days=3)
            duration_text = " from " + track_starts_before.strftime("%d %b") + " to " + track_ends_before.strftime("%d %b") + ", " + track_ends_before.strftime("%Y")
            return duration_text
        else:
            return ""
    except Exception as e:
        return ""



# The keywords table draws two things out of a keyword's SERP feature record:
# the AI Overview glyph with its tooltip, and nothing else. The record itself
# carries up to ten extracted entries per block -- title, link, domain,
# description, position -- which only the keyword detail view reads.
#
# Sent whole, those entries were 87% of the keywords-table response: 123KB of
# 142KB for one 30-keyword project, and the share grows with the project. This
# keeps exactly what data_table.js reads and drops the rest, so the detail view
# is free to render the full record from its own endpoint.
_TABLE_AI_SOURCES = 4  # data_table.js tooltip shows sources.slice(0, 4)


def _table_features(features):
    """`serp_features` reduced to what the keywords TABLE renders."""
    if not isinstance(features, dict) or not features:
        return {}

    # `blocks` is deliberately NOT carried. app/src/pages/serpRank/data_table.js
    # reads exactly `sf.ai_overview` and `sf.mode` and nothing else; the block
    # states were seven objects per keyword that no column rendered. The
    # per-keyword badge list the table DOES draw is `sp`, computed above.
    #
    # If a feature column is ever added to this table, add its block back here
    # -- it will otherwise read undefined and render nothing, silently.
    trimmed = {
        # `mode` decides between "not measured at this depth" and "the provider
        # did not say", which are different sentences in the tooltip.
        "mode": features.get("mode", ""),
    }

    ai = features.get("ai_overview")
    if isinstance(ai, dict):
        sources = ai.get("sources") if isinstance(ai.get("sources"), list) else []
        trimmed["ai_overview"] = {
            "state": ai.get("state", ""),
            "owned": ai.get("owned", False),
            # Only the fields the tooltip prints, and only as many as it shows.
            "sources": [
                {"domain": src.get("domain", ""), "title": src.get("title", "")}
                for src in sources[:_TABLE_AI_SOURCES]
                if isinstance(src, dict)
            ],
        }

    return trimmed


def _last_refresh_at(obj):
    """When this project was last refreshed by hand, or its updated_date.

    `.values(...).first()` is None for a project with no manualrefresh row --
    which is every project that has never been refreshed by hand, including
    every newly created one. The old `"refresh_time" in refreshData` raised
    TypeError on that None, and these serializers render the whole project
    list, so ONE such project 500s /baseauth for the entire account and the app
    loses its project picker and keyword table.
    """
    row = Refreshmanual.objects.filter(
        fb_user_id=int(obj.fk_user_id), fk_group_id=int(obj.id)
    ).values("refresh_time").first()
    return (row.get("refresh_time") if row else None) or obj.updated_date


class DashHomeSerializer(serializers.ModelSerializer):
    G_N = serializers.SerializerMethodField("get_G_N")
    D_N = serializers.SerializerMethodField("get_D_N")
    GY = serializers.SerializerMethodField("get_GY")

    class Meta:
        model = Groups
        fields = ("GY", "G_N", "D_N")

    def get_G_N(self, obj):
        return obj.group_name

    def get_D_N(self, obj):
        return obj.domain_name

    def get_GY(self, obj):
        return obj.id

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        superData["dn_d"] = obj.domain_info
        superData["dn_s"] = obj.domain_status

        # Group Based Keywords
        keyword_rank_histories = list(
            Keyword.objects.filter(fk_group_id=obj.id, fk_user_id=obj.fk_user_id).values_list("rank", flat=True)
        )
        superData["kw_ln"] = len(keyword_rank_histories)

        # ss/yss are recomputed from the keyword rank arrays, NOT read from the
        # stored Groups.score_meter snapshot. score_meter is only rewritten by a
        # ranking run, so between runs -- most obviously right after keywords are
        # added -- the projects list showed a stale number while the dashboard
        # showed a live one, for the same project, under two different labels.
        # This is the same call on the same input that /erocs_wdt makes
        # (serp/widget.py score_widget: ts = score_history[0], ps =
        # score_history[1]), so the two cannot disagree by construction.
        score_history = calculate_visibility_history(keyword_rank_histories)

        # How many measurements the score is built from. Same value and same
        # name as /erocs_wdt's dt.t_c, so one number keeps one name.
        #
        # Without it ss/yss/bss are indistinguishable on a project's FIRST
        # measured day: yss falls back to ss (below), bss is max() of a
        # one-element list, so all three are equal and the projects page renders
        # "Yesterday, it was N" and a delta of 0 -- two claims about a
        # comparison that has only one measurement behind it. `ss === yss`
        # cannot tell that apart from a genuinely flat second day, and this is
        # the first thing a new user sees. Gate the "yesterday" half and the
        # delta on t_c > 1; the score itself is valid from t_c == 1.
        superData["t_c"] = len(score_history)
        superData["ss"] = f_to_i(score_history[0]) if len(score_history) > 0 else 0
        superData["yss"] = f_to_i(score_history[1]) if len(score_history) > 1 else superData["ss"]
        # bss follows ss/yss to the same source. It was the last of the three
        # still reading a stored field, and that made it a stale discriminator:
        # the projects page gates "yesterday / best" on bss, so a project with
        # a live ss of 100 and no engine-written top_score rendered its score
        # beside "not available". max(score_history) is what /erocs_wdt already
        # calls "best" (score_widget: ms), so the two now agree.
        # The -1 sentinel is preserved deliberately -- the frontend uses it to
        # tell "never scored" from "scored zero", and an empty history is
        # exactly the former.
        superData["bss"] = f_to_i(max(score_history)) if len(score_history) > 0 else -1
        superData["rf_t"] = timeDifference(_last_refresh_at(obj), "off")

        # superData['fp'] = int(obj.since_position[0].split(',')[0]) if len(obj.since_position) > 0 else 0
        # superData['yfp'] = int(obj.since_position[1].split(',')[0]) if len(obj.since_position) > 1 else 0

        # activityGroupData = list(map(str, obj.activity_level[1].split('|'))) if len(obj.activity_level) > 1 else [0,0,0]
        # if len(activityGroupData) == 3:
        #     superData['yik'] = int(activityGroupData[1])
        #     superData['ydk'] = int(activityGroupData[2])
        # else:
        #     superData['yik'] = 0
        #     superData['ydk'] = 0

        # superData['ik'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="up").count()
        # superData['dk'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="down").count()

        grpLimit = obj.activity_level[0:7] if len(obj.activity_level) > 7 else obj.activity_level[0 : len(obj.activity_level)]
        grpFirstPos = obj.since_position[0:7] if len(obj.since_position) > 7 else obj.since_position[0 : len(obj.since_position)]
        improved = []
        declined = []
        firstPos = []

        for i in reversed(range(len(grpLimit))):
            activityGroupData = list(map(str, grpLimit[i].split("|")))
            if len(activityGroupData) == 3:
                improved.insert(0, str(activityGroupData[1]))
                declined.insert(0, str(activityGroupData[2]))
            else:
                improved.insert(0, str("0"))
                declined.insert(0, str("0"))

            if len(grpFirstPos) > i:
                firstPos.insert(0, str(grpFirstPos[i].split(",")[0]))
            else:
                firstPos.insert(0, str("0"))

        crawlkwCount = Keyword.objects.filter(fk_user_id=obj.fk_user_id, fk_group_id=obj.id, manual_call_status__in=[True]).count()
        # mrKey = "off"
        # if crawlkwCount > 0:
        #     mrKey = "onk"
        # else:
        #     svCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, search_volume="init").count()
        #     mrKey = "onv" if svCount > 0 else "off"

        # superData['mrk'] = mrKey
        superData["mrk"] = 1 if crawlkwCount > 0 else 0
        superData["ikw"] = improved
        superData["dkw"] = declined
        superData["fpk"] = firstPos

        return superData


# # DASHBOARD AREA DUMMY
# class DashGroupSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = Groups
# 		fields = ('id', 'group_name', 'fk_user_id', 'domain_name', 'created_date', 'updated_date')
# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj)
# 		refreshData = Refreshmanual.objects.filter(fb_user_id=obj.fk_user_id,fk_group_id=obj.id).values('refresh_time').first()
# 		accountData = Accountusage.objects.filter(fb_user_id=obj.fk_user_id).values('last_used_refresh_count').first()

# 		superData['refresh_time'] = timeDifference(refreshData['refresh_time']) if 'refresh_time' in refreshData else timeDifference(obj.updated_date)
# 		superData['last_used_refresh_count'] = accountData['last_used_refresh_count'] if 'last_used_refresh_count' in accountData else 0
# 		superData['key_total'] = Keyword.objects.filter(fk_group_id=obj.id,fk_user_id=obj.fk_user_id).count()

# 		return  superData


class DashKeywordSerializer(serializers.Serializer):

    def to_representation(self, obj):
        prefixConst = 0
        global comp_levels
        global this_week_day
        superData = super().to_representation(obj)

        superData["KW"] = obj["keyword"]

        superData["key"] = prefixConst + int(obj["id"])
        superData["RK"] = obj["rank"][0:2] if this_week_day < 2 else obj["rank"][0:this_week_day]
        # RW is a position ONLY when the keyword ranks; RS says which of the
        # four states it is in, RC the depth actually searched, RSK a sort
        # key. `or 101` used to answer all four with "worse than 100" --
        # a claim the product never measured. See serp/rank_state.py.
        superData["RW"], _rs, _rc, _rsk = apply_rank_state(superData, obj, self.context.get("account_pages"))
        superData["lrd"] = obj["lastranked_date"].date()
        superData["t_c"] = len(obj["rank"])

        # Created Date
        superData["cd"] = obj["created_date"].strftime("%Y-%m-%d")
        superData["lrupt"] = timeDifference(obj["lastranked_date"], "off")

        superData["CR"] = ""

        # Best Rank
        superData["brnk"] = int(obj["top_rank"])
        # 1D
        superData["OD"] = obj["dayval"] if obj["daymark"] != "down" else -abs(int(obj["dayval"]))
        # 7D
        superData["SD"] = obj["weekval"] if obj["weekmark"] != "down" else -abs(int(obj["weekval"]))
        # 15D
        superData["XD"] = obj["halfmonthval"] if obj["halfmonthmark"] != "down" else -abs(int(obj["halfmonthval"]))

        # Features
        sniptkys = set(obj["snippets_details"].keys())
        if len(sniptkys):
            rmvSniptkys = {"featured_box", "ads", "knowledge_box", "current"}
            sniptkys = sniptkys - rmvSniptkys

        order = ["slrs", "twrs", "lcrs", "imrs", "vdrs", "nwrs", "rqrs", "mprs"]
        ordervalue = list(sniptkys - set(order))
        snipSetKeys = list(sniptkys)
        if len(ordervalue) == 0:
            snipSetKeys = sorted(snipSetKeys, key=lambda snipSetKeys: order.index(snipSetKeys))

        fsnptCount = 0
        if obj["knowledge_panel"]:
            snipSetKeys.insert(0, "knw")
        if obj["featured_snippet"]:
            fs_status = "fs1" if "featured_box" in obj["snippets_details"] and obj["snippets_details"]["featured_box"]["status"] == "yes" else "fs0"
            snipSetKeys.insert(0, fs_status)
        if obj["ads"] != False:
            if "ads" in obj["snippets_details"]:
                if obj["snippets_details"]["ads"]["status"] == "yes":
                    ad = "Ain"
                elif int(obj["snippets_details"]["ads"]["top_count"]) > 0 and obj["snippets_details"]["ads"]["bottom_count"] > 0:
                    ad = "Atb"
                elif int(obj["snippets_details"]["ads"]["top_count"]) > 0:
                    ad = "At"
                elif int(obj["snippets_details"]["ads"]["bottom_count"]) > 0:
                    ad = "Ab"
                else:
                    # Ads present, fold position not reported by the provider.
                    # This branch used to insert the raw boolean True into a
                    # list of string tokens, which every renderer silently drops
                    # -- so a keyword WITH ads showed no ads badge at all.
                    ad = "Au"
            else:
                ad = "Au"

            snipSetKeys.insert(0, ad)
        if obj["review"]:
            snipSetKeys.insert(0, "rv")

        superData["sp"] = snipSetKeys
        # Tri-state SERP feature record. {} means this keyword has never been
        # measured for features -- the "sp" badge list above cannot say that,
        # because an unmeasured keyword and a keyword whose SERP genuinely had
        # no features both produce an empty list. Read "sfm" before rendering a
        # feature count as a zero.
        #
        # TRIMMED for the table: the full record carries up to ten extracted
        # entries per feature block, which the keyword DETAIL view reads and
        # this table does not touch at all. Sent whole they were 87% of this
        # response -- 123KB of 142KB across 30 keywords, and growing linearly
        # with the project. `sfm` still reports whether anything was measured.
        superData["sf"] = _table_features(obj.get("serp_features"))
        superData["sfm"] = bool(obj.get("serp_features"))
        superData["trg"] = obj["total_rating"]

        superData["SV"] = obj["search_volume"] if obj["search_volume"] != "-" else "-1"
        superData["PSV"] = "0"
        superData["SVM"] = ""
        superData["PSVM"] = ""

        # SEARCH VOLUME
        svolData = None
        if "voldata" in self.context:
            # svolData = next((x for x in self.context["voldata"] if x["fk_keyword_id"] == obj["id"]), None)
            svolData = self.context["voldata"][obj["id"]] if obj["id"] in self.context["voldata"] else None

        if svolData:
            superData["SV"] = svolData["month_wise_volume"][-1] if len(svolData["month_wise_volume"]) > 1 else "-1"
            superData["PSV"] = svolData["month_wise_volume"][-2] if len(svolData["month_wise_volume"]) > 1 else "0"
            SVMY = svolData["past_months"][-1] if len(svolData["past_months"]) > 1 else ""
            SVMY = SVMY.split(" ", 1)
            superData["SVM"] = SVMY[0].capitalize() if len(SVMY) else ""

            PSVMY = svolData["past_months"][-2] if len(svolData["past_months"]) > 1 else ""
            PSVMY = PSVMY.split(" ", 1)
            superData["PSVM"] = PSVMY[0].capitalize() if len(PSVMY) else ""

        # URL
        superData["edm"] = obj["exactdomain"]
        if "dn" in self.context and obj["ranknow"] == 0:
            superData["SR"] = self.context["dn"]
        else:
            superData["SR"] = obj["site_url"]

        # TAG
        superData["tg"] = obj["tags"]

        # KEYWORD
        superData["RG"] = obj["region"]
        superData["CY"] = obj["location"].split("(")[1].replace(")", "").strip() if "(" in obj["location"] else "-"
        superData["lng"] = obj["language"]
        superData["srs"] = obj["search_results"]
        superData["io"] = obj["isocode"]
        superData["PM"] = "D" if obj["platform"] == "desktop" else "M"
        superData["kwas"] = obj["keyword_alias"]
        superData["cnn"] = True if len(obj["cannibalisation"]) > 1 else False

        # GOOGLE SEARCH CONSOLE
        # Only when the project is actually connected to one. These columns
        # default to the string "0" on the model and gsc_last_track defaults to
        # utcnow, so an instance that has never connected GSC -- which is every
        # instance, the integration being parked -- was shipping "0 clicks, 0
        # impressions, from 13 Aug to 19 Aug" per keyword. Zero is a
        # measurement; nothing measured it.
        #
        # Omitted rather than blanked: a value that does not exist should not be
        # in the payload for a later renderer to find and display.
        if not self.context.get("gsc_connected"):
            return superData

        superData["clks"] = obj["gsc_clicks"] if obj["gsc_clicks"] is not None else ""
        superData["imps"] = obj["gsc_impressions"] if obj["gsc_impressions"] is not None else ""

        superData["lw_clks"] = obj["gsc_clicks_last_week"] if obj["gsc_clicks_last_week"] is not None else ""
        superData["lw_imps"] = obj["gsc_impressions_last_week"] if obj["gsc_impressions_last_week"] is not None else ""

        lastTrackDate = 0
        if "gsc_lt" in self.context:
            lastTrackDate = self.context["gsc_lt"]

        superData["gsc_dr"] = append_duration_text(lastTrackDate) if lastTrackDate else ""

        clickVariation = "NC"
        impressionVariation = "NC"

        if obj["gsc_clicks"] is not None and obj["gsc_clicks_last_week"] is not None and obj["gsc_impressions"] is not None and obj["gsc_impressions_last_week"] is not None:
            if int(obj["gsc_clicks_last_week"]) > 0 and int(obj["gsc_impressions_last_week"]) > 0:
                superData["clks_v"] = "H" if int(obj["gsc_clicks"]) > int(obj["gsc_clicks_last_week"]) else ("D" if int(obj["gsc_clicks"]) < int(obj["gsc_clicks_last_week"]) else "NC")
                superData["imps_v"] = "H" if int(obj["gsc_impressions"]) > int(obj["gsc_impressions_last_week"]) else ("D" if int(obj["gsc_impressions"]) < int(obj["gsc_impressions_last_week"]) else "NC")
            else:
                superData["clks_v"] = clickVariation
                superData["imps_v"] = impressionVariation
        else:
            superData["clks_v"] = clickVariation
            superData["imps_v"] = impressionVariation

        return superData


# # APP HOME AREA
# class AppHomeSerializer(serializers.Serializer):
# 	# i_a = serializers.SerializerMethodField('get_i_a')
# 	# UNM = serializers.SerializerMethodField('get_UNM')
# 	# class Meta:
# 	# 	model = Account
# 	# 	fields = ('i_a', 'UNM')

# 	# def get_i_a(self, obj):
# 	# 	return obj.is_active

# 	# def get_UNM(self, obj):
# 	# 	return obj.username

# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj)

# 		localUserId = obj

# 		superData['sb_s'] = ""
# 		superData['pPL'] = 1


# 		userGroups = Groups.objects.filter(fk_user=localUserId).all()
# 		groupalldata = AppGroupSerializer(userGroups, many=True).data
# 		superData['slt'] = groupalldata
# 		dashview = {}
# 		for gdata in groupalldata:
# 			dashview[gdata['GY']] = gdata['d_v']

# 		superData['gpv'] = dashview
# 		accData = Accountusage.objects.filter(fb_user_id=localUserId).first()

# 		if accData:
# 			superData['pPL'] = accData.plan_project_limit if accData else 1
# 			superData['sb_s'], pOverRule = userPaymode(localUserId, accData)
# 			# superData['sb_s'], pOverRule = userPaymode(localUserId, accData.st_subscription_id, accData.st_customer_id, "MAIN")

# 			# currdate = datetime.now()
# 			# trialenddate = accData.created_date + timedelta(accData.trial_days)
# 			# superData['tr_c'] = True if superData['sb_s'] == "" and trialenddate.strftime('%Y-%m-%d') < currdate.strftime('%Y-%m-%d') else False
# 			# payData = UserSubscriptions.objects.filter(fk_user_id=localUserId, st_customer_id=accData.st_customer_id, fk_reference_type="MAIN").last()
# 			# if payData:
# 			# 	if payData.st_subscription_status == "SUBSCRIBED" and payData.st_pay_status == "PAID":
# 			# 		superData['sb_s'] = "active"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "PAID":
# 			# 		superData['sb_s'] = "active"
# 			# 	elif payData.st_subscription_status == "CANCEL" and payData.st_pay_status == "DROP":
# 			# 		superData['sb_s'] = "cancelled"
# 			# 	elif payData.st_subscription_status == "EXPIRE" and payData.st_pay_status == "FAIL":
# 			# 		superData['sb_s'] = "expire"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "UPDATING":
# 			# 		superData['sb_s'] = "renewal-update"
# 			# 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "FAIL":
# 			# 		superData['sb_s'] = "renewal-fail"

# 		uSettingData = Usersettings.objects.filter(fb_user_id=obj).first()
# 		if uSettingData:
# 			superData['s_s'] = uSettingData.skip_status
# 			superData['fur'] = list(set(uSettingData.external_reviews.keys())) if superData['sb_s'] in ["", "cancelled", "expire"] else ["g2"]

# 		return superData


# APP HOME AREA
class AppHomeSerializer(serializers.Serializer):

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        localUserId = obj

        superData["sb_s"] = ""
        superData["sb_s"] = ""
        superData["sO_R"] = 0
        superData["uTY"] = "free"

        userGroups = list(Groups.objects.filter(fk_user=localUserId).all())
        groupalldata = AppGroupSerializer(
            userGroups, many=True, context=project_list_context(localUserId, userGroups)
        ).data
        superData["uPL"] = len(groupalldata)
        superData["slt"] = groupalldata
        # dashview = {}
        # for gdata in groupalldata:
        # 	dashview[gdata['GY']] = gdata['d_v']

        # superData['gpv'] = dashview
        accIns = Accountusage.objects.filter(fb_user_id=localUserId)
        accData = accIns.first()

        if accIns.exists() and accData.user_type == "trial" and accData.trial_days == 0:
            GrpkeyIns = Keyword.objects.filter(fk_user_id=localUserId)
            usageCount = 0

            if GrpkeyIns.exists():
                usageCount = GrpkeyIns.count()
                accupdate = accIns.update(last_used_refresh_count=usageCount, used_refresh_limit=0, user_type="free", status="default", modified_date=datetime.now())
                keywords = GrpkeyIns.update(manual_call_status=1)

                if usageCount > 0:
                    groupRefreshUpdate = Groups.objects.filter(fk_user_id=localUserId).update(strict_refresh_switch=True, manual_grp_trigger="INIT", last_used_refresh_count=usageCount)

                    refreshIns = Refreshmanual.objects.filter(fb_user_id=localUserId)
                    if refreshIns.exists():
                        refreshIns.update(refresh_status="start", refresh_type="manual")

        accData = Accountusage.objects.filter(fb_user_id=localUserId).first()
        if accData:
            superData["pPL"] = accData.plan_project_limit if accData else 1
            superData["sb_s"], superData["sO_R"] = userPaymode(localUserId, accData)
            superData["uTY"] = accData.user_type
            superData["gscT"] = accData.gsc_token if (accData.gsc_token) else ""

        superData["ac_typ"] = obj.acc_type if obj.acc_type else ""

        return superData


# menu_details, baseauth for apphome, report, setting.js
# ---------------------------------------------------------------------------
# THE PROJECT LIST, LOADED IN BULK
# ---------------------------------------------------------------------------
# AppGroupSerializer used to issue FOUR queries per project -- a keyword count,
# a GroupSetting row, the SAME GroupSetting row again for one field, and a
# Refreshmanual row. /baseauth is the application shell, so every screen paid
# it: 22 queries to produce 1KB for three projects, and it grew linearly.
#
# Under djongo a query costs ~6ms of pure-Python SQL translation whatever it
# selects (profiled: ~44% sqlparse against ~8% socket I/O), so the lever is
# query COUNT, not query cost -- and joins are the most expensive thing its
# parser does, which is why this bulk-loads and indexes in Python rather than
# reaching for select_related/prefetch_related.
#
# The context these build is optional on purpose. A serializer used without it
# falls back to querying per object, so no caller breaks by not knowing.


def _as_user_id(userid):
    """The numeric account id, whether an id or an Account instance was passed.

    AppHomeSerializer is handed the Account object itself and relies on Django
    coercing it inside a filter(). These helpers do arithmetic on it, so they
    have to unwrap it first.
    """
    return int(getattr(userid, "pk", userid))


def _group_settings_by_project(userid, group_ids):
    """{project id: GroupSetting} for a whole account, in one query."""
    if not group_ids:
        return {}
    rows = GroupSetting.objects.filter(
        fk_user=_as_user_id(userid), fk_group__in=[int(g) for g in group_ids]
    )
    return {int(row.fk_group_id): row for row in rows}


def _refresh_times_by_project(userid, group_ids):
    """{project id: refresh_time or None} for a whole account, in one query.

    A project with no row is ABSENT from this map, and the caller must treat
    that exactly as the old per-project `.first()` treated None -- falling back
    to the project's own updated_date. One project without that row used to
    500 /baseauth for the entire account; the bulk version must not reintroduce
    that by handing back something a caller dereferences.
    """
    if not group_ids:
        return {}
    rows = Refreshmanual.objects.filter(
        fb_user_id=_as_user_id(userid), fk_group_id__in=[int(g) for g in group_ids]
    ).values("fk_group_id", "refresh_time")
    return {int(r["fk_group_id"]): r.get("refresh_time") for r in rows}


def _keyword_counts_by_project(userid):
    """{project id: keyword count} for a whole account, in ONE round trip.

    This is the one figure that cannot be bulk-loaded cheaply through Django.
    `annotate(Count(...))` emits a GROUP BY for djongo to translate, and
    translation is the cost being removed; pulling every keyword id to count in
    Python would be O(keywords), worse on a real account than the N+1 it
    replaces.

    So it goes to the collection directly, through the SAME MongoClient djongo
    has already memoised and opened -- no second pool, no new configuration.
    It reads two integer fields and returns counts: there is no field mapping
    to get wrong and no model behaviour to bypass, and the collection name
    comes from the model rather than a literal.

    Falls back to the ORM if anything about that is unavailable, because a
    project list that is slow is better than one that does not load.
    """
    try:
        from django.conf import settings as _settings
        from djongo import database as _djdb

        name = _settings.DATABASES["default"]["NAME"]
        client = _djdb.clients.get(name)
        if client is None:
            raise RuntimeError("djongo client not open yet")
        collection = client[name][Keyword._meta.db_table]
        rows = collection.aggregate([
            {"$match": {"fk_user_id": _as_user_id(userid)}},
            {"$group": {"_id": "$fk_group_id", "n": {"$sum": 1}}},
        ])
        return {int(r["_id"]): int(r["n"]) for r in rows if r.get("_id") is not None}
    except Exception:
        return None


def project_list_context(userid, groups):
    """Everything AppGroupSerializer needs for a whole account, bulk-loaded."""
    ids = [int(g.id) for g in groups]
    return {
        "kw_counts": _keyword_counts_by_project(userid),
        "grp_settings": _group_settings_by_project(userid, ids),
        "refresh_times": _refresh_times_by_project(userid, ids),
        "_bulk": True,
    }


class AppGroupSerializer(serializers.ModelSerializer):
    NM = serializers.SerializerMethodField("get_NM")
    GY = serializers.SerializerMethodField("get_GY")

    class Meta:
        model = Groups
        fields = ("GY", "NM")

    def get_NM(self, obj):
        return obj.group_name

    def get_GY(self, obj):
        return obj.id

    def to_representation(self, obj):
        superData = super().to_representation(obj)
        # Bulk-loaded when the caller supplied the context; otherwise queried
        # per project exactly as before, so no caller breaks by not knowing.
        bulk = self.context.get("_bulk") is True
        gid = int(obj.id)

        counts = self.context.get("kw_counts") if bulk else None
        if counts is not None:
            # A project with no keywords is absent from the aggregation, which
            # means zero -- not missing.
            superData["kw_c"] = counts.get(gid, 0)
        else:
            superData["kw_c"] = Keyword.objects.filter(fk_group=gid, fk_user=int(obj.fk_user_id)).count()

        gridview = obj.grid_sort[0].upper() if (len(obj.grid_sort)) else "T"
        superData["d_v"] = "G~" + gridview if obj.dashboard_view == "gridview" else "L~" + gridview
        # superData['d_v'] = 'G' if obj.dashboard_view == 'gridview' else 'L'
        superData["DN"] = obj.domain_name

        # ONE fetch supplies all three fields. It used to be two reads of the
        # identical row -- once whole, once for w_order alone.
        if bulk:
            grpsttgIns = (self.context.get("grp_settings") or {}).get(gid)
        else:
            grpsttgIns = GroupSetting.objects.filter(fk_user=int(obj.fk_user_id), fk_group=gid).first()
        superData["w_order"] = grpsttgIns.w_order if grpsttgIns else {}
        superData["OV"] = grpsttgIns.overview_switch if grpsttgIns else True
        superData["W"] = grpsttgIns.widget_handle if grpsttgIns else []
        w_handle = superData["W"] if superData["W"] else []
        w_order = superData["w_order"] if superData["w_order"] else {}

        def funct(item):
            if item[0] in w_handle:
                return item
            else:
                pass

        superData["w"] = dict(filter(funct, w_order.items())) if len(w_order) > 0 else {}

        # A project absent from the map has no manualrefresh row, which is
        # every project never refreshed by hand -- it falls back to
        # updated_date, exactly as the per-project .first() did. Getting this
        # wrong is how one such project once 500'd the whole account.
        if bulk:
            _refreshed = (self.context.get("refresh_times") or {}).get(gid) or obj.updated_date
        else:
            _refreshed = _last_refresh_at(obj)
        superData["rf_t"] = timeDifference(_refreshed, "off")
        # superData['rf_t'] = rf_time.split("(", 1)[0].strip()

        return superData


# frontend Export CSV
class ExportCSVKeywordSerializer(serializers.ModelSerializer):
    xcount = 0

    class Meta:
        model = Keyword
        fields = ("keyword", "region")

    def to_representation(self, obj):
        self.xcount = int(self.xcount) + 1
        superData = super().to_representation(obj)

        exportdata = {}
        exportdata = []
        exporttxtdata = []

        keyword_slug = f"{obj.keyword}".replace(" ", "_")
        svolData = keywordVolume.objects.filter(keyword_slug=keyword_slug, region_code=obj.isocode).first()
        comp = "-"
        sv = "-"
        if svolData != None:
            comp = svolData.comp_level.capitalize() if svolData.comp_level != "UNSPECIFIED" else "-"
            sv = svolData.month_wise_volume[-1] if len(svolData.month_wise_volume) > 1 else "-"

        if obj.dayval != 0:
            dayval = str(obj.dayval) + " (" + obj.daymark + ")"
            dayvalget = dayval
        else:
            dayvalget = "-"
        if obj.weekval != 0:
            weekval = str(obj.weekval) + " (" + obj.weekmark + ")"
            weekvalget = weekval
        else:
            weekvalget = "-"
        if obj.monthval != 0:
            monthval = str(obj.monthval) + " (" + obj.monthmark + ")"
            monthvalget = monthval
        else:
            monthvalget = "-"

        superData["sno"] = int(self.xcount)
        superData["Rank"] = obj.ranknow if obj.ranknow != 0 else ">100"
        superData["Best rank"] = int(obj.top_rank) if int(obj.top_rank) > 0 else "-"
        superData["Day"] = dayvalget
        superData["Week"] = weekvalget
        superData["Month"] = monthvalget
        # superData['Features'] = str(obj.featured_snippet)
        # superData['Volume'] = obj.search_volume
        superData["Volume"] = sv
        superData["Comp"] = comp
        superData["URL"] = obj.site_url
        superData["Created on"] = custom_strftime("%b {S}, %Y", obj.created_date)
        # superData['Created on'] = obj.created_date.strftime('%d-%m-%Y')

        return superData


# frontend Export PDF
class ExportPDFKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ("keyword", "dayval")

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        # def host_path(url):
        domain_name = ""
        domain = urlparse(obj.site_url)
        if domain.path == "":
            domain_name = f"{domain.netloc}".replace("www.", "")
        elif f"{domain.path}" == "/":
            domain_name = f"{domain.netloc}".replace("www.", "")
        else:
            domain_name = domain.path
        # return domain_name

        keyword_slug = f"{obj.keyword}".replace(" ", "_")
        svolData = keywordVolume.objects.filter(keyword_slug=keyword_slug, region_code=obj.isocode).first()
        comp = "-"
        sv = "-"
        if svolData != None:
            comp = svolData.comp_level.capitalize() if svolData.comp_level != "UNSPECIFIED" else "-"
            sv = svolData.month_wise_volume[-1] if len(svolData.month_wise_volume) > 1 else "-"

        superData["furl"] = obj.site_url
        superData["URL"] = domain_name if domain_name != "" else obj.site_url
        superData["RGN"] = obj.region
        superData["ranknow"] = obj.ranknow
        superData["brnk"] = int(obj.top_rank)
        # superData['SV']= obj.search_volume
        superData["SV"] = sv
        superData["CLV"] = comp
        superData["Wk"] = obj.weekval
        superData["Dmark"] = obj.daymark
        superData["Wkmark"] = obj.weekmark
        superData["c_d"] = custom_strftime("%b {S}, %Y", obj.created_date)
        # superData['c_d']= obj.created_date.strftime('%d-%m-%Y')

        return superData


# TAG LOAD AREA
class TagKeywordSerializer(serializers.ModelSerializer):
    xcount = 0
    KW = serializers.SerializerMethodField("get_keyword")

    class Meta:
        model = Keyword
        fields = ("KW", "ads")

    def get_keyword(self, obj):
        return obj["keyword"]

    def to_representation(self, obj):
        global this_week_day
        superData = super().to_representation(obj)

        superData["fs_s"] = obj["snippets_details"]["featured_box"]["status"] if "featured_box" in obj["snippets_details"] else "no"
        if self.xcount == 0:
            superData["ExD"] = self.context["keywordsexactdomain_count"]
            self.xcount = 1

        sniptkys = set(obj["snippets_details"].keys())
        if len(sniptkys):
            rmvSniptkys = {"featured_box", "ads", "knowledge_box", "current"}
            sniptkys = sniptkys - rmvSniptkys

        order = ["slrs", "twrs", "lcrs", "imrs", "vdrs", "nwrs", "rqrs", "mprs"]
        ordervalue = list(sniptkys - set(order))
        snipSetKeys = list(sniptkys)
        if len(ordervalue) == 0:
            snipSetKeys = sorted(snipSetKeys, key=lambda snipSetKeys: order.index(snipSetKeys))

        fsnptCount = 0
        if obj["featured_snippet"]:
            fsnptCount += 1
        if obj["knowledge_panel"]:
            fsnptCount += 1
        if obj["review"]:
            fsnptCount += 1
        if obj["ads"]:
            fsnptCount += 1
        # fsc counts only the four booleans, which are False both when a
        # feature was absent and when nothing ever looked. sfm says which of the
        # two a 0 is; render "-" rather than "0" when it is False.
        superData["fsc"] = fsnptCount
        superData["sfm"] = bool(obj.get("serp_features"))

        # prefixConst = DEF_SETTINGS.UNIQUE_KEYWORD_ID
        prefixConst = 0
        key = prefixConst + int(obj["id"])

        if "tag" in self.context:
            tag = self.context["tag"]
        else:
            tag = ""
        if tag != "":
            superData["key"] = str(key) + "~" + str(tag)
        else:
            superData["key"] = int(key)
        # superData['key'] = prefixConst + int(obj['id'])
        superData["kwas"] = obj["keyword_alias"]
        # superData['knw'] = obj['knowledge_panel']
        # superData['fds'] = obj['featured_snippet']
        superData["dm"] = obj["daymark"]
        # superData['rvw'] = obj['review']
        superData["brk"] = int(obj["top_rank"])
        superData["trg"] = obj["total_rating"]
        # superData['CR'] = obj['page_uuid_url']
        superData["CR"] = ""
        superData["PM"] = "D" if obj["platform"] == "desktop" else "M"
        superData["SR"] = obj["site_url"]
        superData["RK"] = obj["rank"][0:2] if this_week_day < 2 else obj["rank"][0:this_week_day]
        # RW is a position ONLY when the keyword ranks; RS says which of the
        # four states it is in, RC the depth actually searched, RSK a sort
        # key. `or 101` used to answer all four with "worse than 100" --
        # a claim the product never measured. See serp/rank_state.py.
        superData["RW"], _rs, _rc, _rsk = apply_rank_state(superData, obj, self.context.get("account_pages"))
        superData["edm"] = obj["exactdomain"]
        superData["io"] = obj["isocode"]
        superData["cnn"] = True if len(obj["cannibalisation"]) > 1 else False
        # superData['srs'] = obj['search_results']
        superData["RG"] = obj["region"]
        superData["CY"] = obj["location"].split("(")[1].replace(")", "").strip() if "(" in obj["location"] else "-"
        superData["lng"] = obj["language"]
        superData["cd"] = obj["created_date"].strftime("%Y-%m-%d")
        superData["lrd"] = obj["lastranked_date"].date()
        superData["t_c"] = len(obj["rank"])

        svolData = None
        if "voldata" in self.context:
            svolData = self.context["voldata"][obj["id"]] if obj["id"] in self.context["voldata"] else None

        if svolData:
            superData["SV"] = svolData["month_wise_volume"][-1] if len(svolData["month_wise_volume"]) > 1 else "-1"
            superData["PSV"] = svolData["month_wise_volume"][-2] if len(svolData["month_wise_volume"]) > 1 else "0"
            SVMY = svolData["past_months"][-1] if len(svolData["past_months"]) > 1 else ""
            SVMY = SVMY.split(" ", 1)
            superData["SVM"] = SVMY[0].capitalize() if len(SVMY) else ""

            PSVMY = svolData["past_months"][-2] if len(svolData["past_months"]) > 1 else ""
            PSVMY = PSVMY.split(" ", 1)
            superData["PSVM"] = PSVMY[0].capitalize() if len(PSVMY) else ""

        return superData


class TagSerializer(serializers.Serializer):

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        if "gridtype" in self.context:
            sd = {}
            tagsdata = 1
            _tg_score_ = {}
            volume_data = {}

            if "voldata" in self.context:
                volume_data = self.context["voldata"]

            page_filter = {"fk_user_id": obj["fk_user_id"], "fk_group_id": obj["id"]}
            # manual_call_mode and serp_pages feed rank_state(): one tells a
            # failed check from one that found nothing, the other gives the
            # depth behind "not in the first N".
            page_values = ("id", "keyword", "ads", "snippets_details", "serp_features", "featured_snippet", "knowledge_panel", "review", "keyword_alias", "daymark", "top_rank", "total_rating", "platform", "site_url", "rank", "ranknow", "manual_call_mode", "serp_pages", "exactdomain", "isocode", "cannibalisation", "region", "location", "language", "created_date", "lastranked_date")

            if self.context["gridtype"] == "region":
                ss = list(Keyword.objects.exclude(region="").filter(**page_filter).values_list("region", flat=True).all())

                if len(ss) > 0:
                    flatss = list(dict.fromkeys(ss))
                    for ff in flatss:
                        tag_filter = {"fk_user_id": obj["fk_user_id"], "fk_group_id": obj["id"], "region": ff}
                        if "search" in self.context:
                            singleTag = Keyword.objects.exclude(region="").filter(**tag_filter, keyword__icontains=self.context["search"]).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(region="").filter(**tag_filter, keyword__icontains=self.context["search"], exactdomain__in=[True]).count()
                        else:
                            singleTag = Keyword.objects.exclude(region="").filter(**tag_filter).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(region="").filter(**tag_filter, exactdomain__in=[True]).count()
                            _tg_score_[ff] = tagBasedScore(singleTag)

                        sd[ff] = TagKeywordSerializer(singleTag, many=True, context={"voldata": volume_data, "tag": ff, "keywordsexactdomain_count": keywordsExactDomain}).data
                        if len(sd[ff]) > 0:
                            tagsdata = 0
                tagCollections = collections.OrderedDict(sd.items())

            elif self.context["gridtype"] == "device":
                ss = list(Keyword.objects.exclude(platform="").filter(**page_filter).values_list("platform", flat=True).all())

                if len(ss) > 0:
                    flatss = list(dict.fromkeys(ss))
                    for ff in flatss:
                        tag_filter = {"fk_user_id": obj["fk_user_id"], "fk_group_id": obj["id"], "platform": ff}
                        if "search" in self.context:
                            singleTag = Keyword.objects.exclude(platform="").filter(**tag_filter, keyword__icontains=self.context["search"]).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(platform="").filter(**tag_filter, keyword__icontains=self.context["search"], exactdomain__in=[True]).count()
                        else:
                            singleTag = Keyword.objects.exclude(platform="").filter(**tag_filter).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(platform="").filter(**tag_filter, exactdomain__in=[True]).count()
                            _tg_score_[ff] = tagBasedScore(singleTag)

                        sd[ff] = TagKeywordSerializer(singleTag, many=True, context={"voldata": volume_data, "tag": ff, "keywordsexactdomain_count": keywordsExactDomain}).data
                        if len(sd[ff]) > 0:
                            tagsdata = 0
                tagCollections = collections.OrderedDict(sd.items())

            else:
                if len(self.context["unqtags"]) > 0:
                    for ff in self.context["unqtags"]:
                        if "search" in self.context:
                            singleTag = Keyword.objects.exclude(tags=[]).filter(**page_filter, tags__contains=ff, keyword__icontains=self.context["search"]).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(tags=[]).filter(**page_filter, tags__contains=ff, keyword__icontains=self.context["search"], exactdomain__in=[True]).count()
                        else:
                            singleTag = Keyword.objects.exclude(tags=[]).filter(**page_filter, tags__iexact=ff).values(*page_values).all()
                            keywordsExactDomain = Keyword.objects.exclude(tags=[]).filter(**page_filter, tags__iexact=ff, exactdomain__in=[True]).count()
                            _tg_score_[ff] = tagBasedScore(singleTag)

                        sd[ff] = TagKeywordSerializer(singleTag, many=True, context={"voldata": volume_data, "tag": ff, "keywordsexactdomain_count": keywordsExactDomain}).data
                        if len(sd[ff]) > 0:
                            tagsdata = 0

                if "search" in self.context:
                    noTags = Keyword.objects.filter(**page_filter, tags=[], keyword__icontains=self.context["search"]).values(*page_values).all()
                    noTag_keywordsExactDomain = Keyword.objects.filter(**page_filter, tags=[], keyword__icontains=self.context["search"], exactdomain__in=[True]).count()
                else:
                    noTags = Keyword.objects.filter(**page_filter, tags=[]).values(*page_values).all()
                    noTag_keywordsExactDomain = Keyword.objects.filter(**page_filter, tags=[], exactdomain__in=[True]).count()
                    _tg_score_["no-tags"] = tagBasedScore(noTags)

                sd["no-tags"] = TagKeywordSerializer(noTags, many=True, context={"voldata": volume_data, "tag": "no-tags", "keywordsexactdomain_count": noTag_keywordsExactDomain}).data if len(noTags) else ""
                if len(sd["no-tags"]) > 0:
                    tagsdata = 0

                tagCollections = collections.OrderedDict(sorted(sd.items(), key=lambda x: len(x[1]) if x[0] != "no-tags" else -1, reverse=True))

            superData["tags"] = tagCollections
            superData["tagkeys"] = list(tagCollections.keys())
            superData["tgin"] = tagsdata
            superData["tscr"] = _tg_score_

        return superData


# ManageTag
class ManagetagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ("group_name", "domain_name")

    def to_representation(self, obj):
        superData = super().to_representation(obj)
        selectids = self.context["selectids"]
        alltagslist = list(Keyword.objects.exclude(tags=[]).filter(fk_user_id=obj.fk_user_id, fk_group_id=obj.id).values_list("tags", flat=True).all())

        commontags = []
        othertags = []
        selecttags = {}
        if len(alltagslist) > 0:
            # uniquetags = set(numpy.concatenate(alltagslist).flat)
            uniquetags = set(map(lambda x: x.lower(), list(numpy.concatenate(alltagslist).flat)))

            tagslist = list(Keyword.objects.filter(fk_user_id=obj.fk_user_id, fk_group_id=obj.id, id__in=selectids).values_list("tags", flat=True).all())
            if len(tagslist) > 0:
                selecttags = set(map(lambda x: x.lower(), list(numpy.concatenate(tagslist).flat)))
                othertags = list(uniquetags - selecttags)
                if [] not in tagslist:
                    commontags = set.intersection(*map(set, tagslist))
                    selecttags = selecttags - commontags
                selecttags = list(selecttags)
                # selecttags = list(map(lambda x: {'id':'old', 'text':x}, list(selecttags)))
            else:
                othertags = list(uniquetags)

        superData["c_tg"] = list(commontags)
        superData["o_tg"] = othertags
        superData["s_tg"] = list(selecttags)
        return superData


# New keyword or group add
class KeywordCreateSerializer(serializers.Serializer):
    def to_representation(self, obj):
        currdate = date.today()
        request = self.context["request"]
        randomstr = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))

        keywords = Keyword(
            fk_user_id=self.context["userid"],
            fk_group_id=self.context["grpid"],
            keyword=obj.lower().strip(),
            site_url=self.context["url"],
            target=self.context["url"],
            location=request.data["region"].strip() + "(" + request.data["countryname"] + ")",
            postdata={},
            exactdomain=self.context["exactdomain"],
            region=request.data["region"].strip(),
            language=request.data["language"],
            language_code=self.context["languageData"].language_code.strip(),
            platform=request.data["platform"],
            tags=self.context["tags"][:5],
            tagcount=len(self.context["tags"]),
            rank=[],
            ranknow=0,
            rank_sincestart=0,
            featured_snippet=0,
            review=0,
            knowledge_panel=0,
            # lastranked_date=currdate.strftime("%Y-%m-%d"),
            lastranked_date=timezone.now(),
            status_from_start="-",
            isocode=request.data["isocode"],
            manual_call_status=self.context["manual_call_status"],
            manual_call_mode="key",
            manual_task_count=0,
        )

        return keywords


# New keyword add time create keyword history table record
class kwHistoryCreateSerializer(serializers.Serializer):
    def to_representation(self, obj):
        userid = self.context["fk_user_id"]
        grpid = self.context["fk_group_id"]
        testdata = KeywordHistory(fk_keyword_id=obj, fk_user_id=userid, fk_group_id=grpid, comp_today={"tp": [], "bf": [], "ar": []})

        return testdata


# Unwanted Search Volume delete
class UnwantSVdeleteSerializer(serializers.Serializer):
    sv_id = None
    count = 0

    def to_representation(self, obj):
        kwIns = Keyword.objects.filter(keyword=obj["keyword"], isocode=obj["region_code"])
        if kwIns.exists() == False and self.count < DEF_SETTINGS.UNWANT_SV_DELETE:
            self.count += 1
            self.sv_id = obj["id"]
            return self.sv_id

        return None


# KEYWORD AREA
class KeywordSerializer(serializers.ModelSerializer):
    tags = serializers.ListField()
    rank = serializers.ListField()

    class Meta:
        model = Keyword
        fields = "__all__"


# Create keyword, add keyword, new wizard
class LanguageNameSerializer(serializers.ModelSerializer):
    LC = serializers.SerializerMethodField("get_LC")
    LN = serializers.SerializerMethodField("get_LN")

    class Meta:
        model = Language
        fields = ("LC", "LN")

    def get_LC(self, obj):
        return obj.language_code

    def get_LN(self, obj):
        return obj.language_name


class RegionFltrSerializer(serializers.ModelSerializer):
    Rcd = serializers.SerializerMethodField("get_Rcd")
    RN = serializers.SerializerMethodField("get_RN")
    Rcnt = serializers.SerializerMethodField("get_Rcnt")

    class Meta:
        model = Region
        fields = ("Rcd", "RN", "Rcnt")

    def get_Rcd(self, obj):
        return obj.region_code

    def get_RN(self, obj):
        return obj.region_name

    def get_Rcnt(self, obj):
        return obj.region_country


# OTHER SERIALIZERS
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = "__all__"


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "region_code", "region_name", "region_country")


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = "__all__"


class GroupSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupSetting
        fields = "__all__"


# Old group used New group setting bulk create
class GroupSettingCreateSerializer(serializers.Serializer):

    def to_representation(self, obj):
        groups = GroupSetting(
            fk_user_id=obj.fk_user_id,
            fk_group_id=obj.id,
        )

        return groups


# class RefreshSerializer(serializers.ModelSerializer):
# class Meta:
# model = Refresh
# fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    last_delivery = serializers.DateTimeField(required=False)
    next_delivery = serializers.DateTimeField(required=False)

    class Meta:
        model = Report
        fields = "__all__"


class RefreshmanualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refreshmanual
        fields = "__all__"


class UsersettingsSerializer(serializers.ModelSerializer):
    demo_view = serializers.CharField(required=False)
    skip_status = serializers.CharField(required=False)
    non_columns = serializers.ListField(required=False)
    external_reviews = serializers.DictField(required=False)

    class Meta:
        model = Usersettings
        fields = "__all__"


class UserregistrationtokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userregistrationtoken
        fields = "__all__"


class ReferralprogramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referralprogram
        fields = ("userid", "ref_id", "visitors_count")


# class PaymentdetailsSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = Paymentdetails
# 		fields = '__all__'

# class brandTrackerSerializer(serializers.ModelSerializer):
# 	conquestor_recent_date = serializers.DateTimeField(required=False)
# 	conquestor_mail_date = serializers.DateTimeField(required=False)
# 	class Meta:
# 		model = brandTracker
# 		fields = '__all__'

# Other Functions


def suffix(d):
    return "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")


def custom_strftime(format, t):
    return t.strftime(format).replace("{S}", str(t.day) + suffix(t.day))


def timeDifference(later_time, formattype="full"):
    current_time = datetime.now()
    start = current_time.strptime(current_time.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    ends = datetime.strptime(later_time.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")

    diff = relativedelta(start, ends)

    multiples = 0
    portion = ""

    if diff.years > 0:
        multiples = diff.years
        portion = str(diff.years) + " " + "year"
    elif diff.months > 0:
        multiples = diff.months
        portion = str(diff.months) + " " + "month"
    elif diff.days > 0:
        multiples = diff.days
        portion = str(diff.days) + " " + "day"
    elif diff.hours > 0:
        multiples = diff.hours
        portion = str(diff.hours) + " " + "hour"
    elif diff.minutes > 0:
        multiples = diff.minutes
        portion = str(diff.minutes) + " " + "minute"
    elif diff.seconds > 0:
        multiples = diff.seconds
        portion = str(diff.seconds) + " " + "second"

    returnContent = ""
    if portion == "":
        returnContent = " Just now "
    elif portion != "" and multiples > 1:
        returnContent = portion + "s ago"
    else:
        returnContent = portion + " ago"

    if formattype == "off":
        return returnContent
    else:
        return returnContent + " (" + custom_strftime("%b {S}, %Y", later_time) + ")"
    # return portion+multiples+" "+"ago" + " ("+custom_strftime('%B {S}, %Y', later_time)+")"


def tagBasedScore(allKeywords):
    scorePerDay = defaultdict(int)

    for keyIns in allKeywords:
        scorePerDay = calculation.scoreAllocationCalc(keyIns, scorePerDay)
    return f_to_i(calculation.scoreMeterCalc(scorePerDay, len(allKeywords)))


# Project Overview details
class ProjectOverviewSerializer(serializers.Serializer):
    sv_id = None
    count = 0
    # superData = {
    # 	'pD': 0,
    # 	'pM': 0,
    # 	'ik': 0,
    # 	'dk': 0,
    # 	'nk': 0,
    # 	'tR': {'1':0, '3':0, '10':0, '50':0, '100':0, 'nr':0},
    # 	'bR': {'1':0, '3':0, '10':0, '50':0, '100':0, 'nr':0},
    # 	'R2': 0,
    # 	'R4': 0,
    # 	'R5': 0,
    # 	'So': 0,
    # 	'Sp': 0,
    # 	'Ay': {'Atb': 0, 'At': 0, 'Ab': 0},
    # 	'Ao': {'Atb': 0, 'At': 0, 'Ab': 0}
    # }
    # superData['pD'] = 0
    # superData['pM'] = 0

    def to_representation(self, obj):

        superData = self.context
        # Device
        if obj.platform == "mobile":
            superData["pM"] += 1
        else:
            superData["pD"] += 1

        # Activity
        if obj.daymark == "up":
            superData["ik"] += 1
        elif obj.daymark == "down":
            superData["dk"] += 1
        else:
            superData["nk"] += 1

        # Comparison
        if obj.ranknow != 0:
            if obj.ranknow == 1:
                superData["tR"]["1"] += 1
            if obj.ranknow <= 3:
                superData["tR"]["3"] += 1
            if obj.ranknow <= 10:
                superData["tR"]["10"] += 1
            if obj.ranknow <= 50:
                superData["tR"]["50"] += 1
            if obj.ranknow <= 100:
                superData["tR"]["100"] += 1
        else:
            superData["tR"]["nr"] += 1

        if obj.top_rank != 0:
            if obj.top_rank == 1:
                superData["bR"]["1"] += 1
            if obj.top_rank <= 3:
                superData["bR"]["3"] += 1
            if obj.top_rank <= 10:
                superData["bR"]["10"] += 1
            if obj.top_rank <= 50:
                superData["bR"]["50"] += 1
            if obj.top_rank <= 100:
                superData["bR"]["100"] += 1
        else:
            superData["bR"]["nr"] += 1

        # Yesterday rank
        if isinstance(obj.rank, list) and len(obj.rank) > 1:
            second_rank = obj.rank[1]
            if second_rank != 0:
                if second_rank == 1:
                    if "1" in superData["yR"]:
                        superData["yR"]["1"] += 1
                if second_rank <= 3:
                    if "3" in superData["yR"]:
                        superData["yR"]["3"] += 1
                if second_rank <= 10:
                    if "10" in superData["yR"]:
                        superData["yR"]["10"] += 1
                if second_rank <= 50:
                    if "50" in superData["yR"]:
                        superData["yR"]["50"] += 1
                if second_rank <= 100:
                    if "100" in superData["yR"]:
                        superData["yR"]["100"] += 1
            else:
                if "nr" in superData["yR"]:
                    superData["yR"]["nr"] += 1
        else:
            if "nr" in superData.get("yR", {}):
                superData["yR"]["nr"] += 1

        # Rating
        rating = isfloat_isdigit(obj.total_rating)
        if rating <= 2:
            superData["R2"] += 1
        elif rating and rating <= 4:
            superData["R4"] += 1
        elif rating and rating <= 5:
            superData["R5"] += 1

        # Serp Features
        if obj.featured_snippet:
            superData["So"] += 1
            if "featured_box" in obj.snippets_details and obj.snippets_details["featured_box"]["status"] != "no":
                superData["Sp"] += 1

        # Google Search Ads
        if obj.ads and "ads" in obj.snippets_details:
            if int(obj.snippets_details["ads"]["top_count"]) > 0 and int(obj.snippets_details["ads"]["bottom_count"]) > 0:
                if obj.snippets_details["ads"]["status"] == "yes":
                    superData["Ay"]["Atb"] += 1
                elif obj.snippets_details["ads"]["status"] == "no":
                    superData["Ao"]["Atb"] += 1
            elif int(obj.snippets_details["ads"]["top_count"]) > 0:
                if obj.snippets_details["ads"]["status"] == "yes":
                    superData["Ay"]["At"] += 1
                elif obj.snippets_details["ads"]["status"] == "no":
                    superData["Ao"]["At"] += 1
            elif int(obj.snippets_details["ads"]["bottom_count"]) > 0:
                if obj.snippets_details["ads"]["status"] == "yes":
                    superData["Ay"]["Ab"] += 1
                elif obj.snippets_details["ads"]["status"] == "no":
                    superData["Ao"]["Ab"] += 1
            else:
                # Ads ran, placement unreported. The JSON SERP API returns one
                # flat `ads` array with no above/below-the-fold marker, so this
                # is the common case and it used to fall out of every bucket --
                # a keyword with ads counted as a keyword with none. "Au" says
                # ads were measured and the fold position was not.
                if obj.snippets_details["ads"]["status"] == "yes":
                    superData["Ay"]["Au"] += 1
                else:
                    superData["Ao"]["Au"] += 1

        # kwIns = Keyword.objects.filter(keyword=obj['keyword'], isocode=obj['region_code'])
        # if kwIns.exists() == False and self.count < DEF_SETTINGS.UNWANT_SV_DELETE :
        # 	self.count += 1
        # 	self.sv_id = obj['id']
        # 	return self.sv_id

        return superData


class ProjectSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ("group_name", "domain_name")

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        superData["sb_s"] = ""
        superData["dn_d"] = obj.domain_info
        superData["dn_s"] = obj.domain_status

        superData["OptSw"] = obj.automation_email_switch
        # SERP extraction depth for this project: False = Lite, True = Advanced
        # (adds ai_overview, higher DataBlue credit weight per request).
        superData["srp_adv"] = bool(obj.serp_advanced)

        # Group Based Keywords
        grpKeyData = Keyword.objects.filter(fk_group_id=obj.id, fk_user_id=obj.fk_user_id)
        superData["kw_ln"] = grpKeyData.count()

        # project details
        superData["gCD"] = custom_strftime("%b {S}, %Y", obj.created_date)

        domain = urlparse(obj.domain_name)
        if domain.path == "":
            domain_name = f"{domain.netloc}".replace("www.", "")
        elif f"{domain.path}" == "/":
            domain_name = f"{domain.netloc}".replace("www.", "")
        else:
            domain_name = domain.path

        superData["dn"] = domain_name

        accountData = Accountusage.objects.filter(fb_user_id=obj.fk_user_id).first()
        # accountData = Accountusage.objects.filter(fb_user_id=obj.fk_user_id).values('last_used_refresh_count', 'st_subscription_id','st_user_mail', 'st_customer_id', 'st_purchase_id', 'plan_keyword_limit', 'plan_refresh_limit', 'used_refresh_limit').first()

        add_recipient_mail = False
        if accountData.st_customer_id != None and accountData.st_subscription_id != None and accountData.st_user_mail != None and accountData.st_purchase_id > 0:
            add_recipient_mail = True
        superData["prmu"] = add_recipient_mail

        superData["rp_m"] = list(filter(None, obj.automation_email_recipients)) if add_recipient_mail == True else []

        if accountData:
            superData["sb_s"], pOverRule = userPaymode(obj.fk_user_id, accountData)
            # superData['sb_s'], pOverRule = userPaymode(obj.fk_user_id, accountData.st_subscription_id, accountData.st_customer_id, "MAIN")
            # payData = UserSubscriptions.objects.filter(fk_user_id=obj.fk_user_id, st_subscription_id=accountData['st_subscription_id'], st_customer_id=accountData['st_customer_id'], fk_reference_type="MAIN").last()
            # if payData:
            # 	if payData.st_subscription_status == "SUBSCRIBED" and payData.st_pay_status == "PAID":
            # 		superData['sb_s'] = "active"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "PAID":
            # 		superData['sb_s'] = "active"
            # 	elif payData.st_subscription_status == "CANCEL" and payData.st_pay_status == "DROP":
            # 		superData['sb_s'] = "cancelled"
            # 	elif payData.st_subscription_status == "EXPIRE" and payData.st_pay_status == "FAIL":
            # 		superData['sb_s'] = "expire"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "UPDATING":
            # 		superData['sb_s'] = "renewal-update"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "FAIL":
            # 		superData['sb_s'] = "renewal-fail"

        rf_time = timeDifference(_last_refresh_at(obj))
        rf_t = rf_time.split("(", 1)[0]
        superData["rf_t"] = rf_t.strip()

        # brandIns = brandTracker.objects.filter(fb_user_id=obj.fk_user_id,fb_group_id=obj.id).values('id','brand_name','status','region','isocode').first()
        # if brandIns != None:
        # 	superData['bid'] = brandIns['id']
        # 	superData['bn'] = brandIns['brand_name']
        # 	superData['bs'] = brandIns['status']
        # 	superData['rg'] = brandIns['region']
        # 	superData['drg'] = brandIns['isocode'].upper()
        # else:
        # 	superData['bid'] = 0
        # 	superData['bn'] = ""
        # 	superData['bs'] = "off"
        # 	superData['rg'] = ""
        # 	superData['drg'] = ""

        return superData


class KeywordPageSerializer(serializers.ModelSerializer):
    KW = serializers.SerializerMethodField("get_keyword")
    AV = serializers.SerializerMethodField("get_avg_volume")

    class Meta:
        model = Keyword
        fields = ("KW", "AV")

    def get_keyword(self, obj):
        return obj.keyword

    def get_avg_volume(self, obj):
        return obj.search_volume

    def to_representation(self, obj):
        # prefixConst = 98765
        # prefixConst = DEF_SETTINGS.UNIQUE_KEYWORD_ID
        prefixConst = 0
        global comp_levels
        global this_week_day
        superData = super().to_representation(obj)

        # keyword_slug = f"{obj.keyword}".replace(" ", "_")
        # svolData = keywordVolume.objects.filter(keyword_slug=keyword_slug,region_code=obj.isocode).first()

        superData["key"] = prefixConst + int(obj.id)

        superData["OD"] = obj.dayval if obj.daymark != "down" else -abs(int(obj.dayval))
        # superData['SD'] = obj.weekval if obj.weekmark != "down" else -abs(int(obj.weekval))
        # superData['XD'] = obj.halfmonthval if obj.halfmonthmark != "down" else -abs(int(obj.halfmonthval))
        superData["CR"] = obj.page_uuid_url
        # superData['SV'] = obj.search_volume if obj.search_volume != '-' else '-1'
        # superData['CID'] = svolData['comp_index'] if 'comp_index' in svolData and svolData['comp_index'] != '-' and svolData['comp_level'] in comp_levels else '-1'
        # superData['CID'] = '-1'
        # superData['CLV'] = '-'
        # # superData['SV'] = obj.search_volume if obj.search_volume != '-' else '-1'
        # # superData['PSV'] = '0'
        # # superData['SVM'] = ''
        # # superData['PSVM'] = ''
        # superData['ASV'] = []
        # superData['ASVM'] = []

        # if svolData != None:
        # 	# superData['SV'] = svolData.month_wise_volume[-1] if len(svolData.month_wise_volume) > 1 else '-1'
        # 	# superData['PSV'] = svolData.month_wise_volume[-2] if len(svolData.month_wise_volume) > 1 else '0'
        # 	# SVMY = svolData.past_months[-1] if len(svolData.past_months) > 1 else ''
        # 	# superData['SVM'] = SVMY.split(" ", 1)[0].capitalize()
        # 	# PSVMY = svolData.past_months[-2] if len(svolData.past_months) > 1 else ''
        # 	# superData['PSVM'] = PSVMY.split(" ", 1)[0].capitalize()
        # 	if svolData.comp_index != '-' and svolData.comp_level in comp_levels:
        # 		superData['CID'] = svolData.comp_index
        # 	superData['CLV'] = svolData.comp_level.capitalize() if svolData.comp_level != "UNSPECIFIED" else "-"
        # 	superData['ASV'] = svolData.month_wise_volume
        # 	superData['ASVM'] = svolData.past_months

        keywordGroup = Groups.objects.filter(id=obj.fk_group_id).first()
        if keywordGroup and obj.ranknow == 0:
            superData["SR"] = keywordGroup.domain_name
        else:
            superData["SR"] = obj.site_url

        superData["RK"] = obj.rank[0:2] if this_week_day < 2 else obj.rank[0:this_week_day]

        # The detail page used to read the position out of RK[0] and print a
        # hardcoded ">30" when it was zero -- a ceiling that is wrong for any
        # keyword not tracked at three pages, and silent about whether the
        # check failed at all. Same four-state answer as the table.
        superData["RW"], _rs, _rc, _rsk = apply_rank_state(superData, obj, self.context.get("account_pages"))

        # unwated
        # superData['cnn'] = True if len(obj.cannibalisation) > 1 else False
        # superData['fds'] = obj.featured_snippet
        # superData['knw'] = obj.knowledge_panel
        # superData['rvw'] = obj.review
        # superData['trg'] = obj.total_rating

        superData["t_c"] = len(obj.rank)
        superData["kwas"] = obj.keyword_alias

        superData["tg"] = obj.tags
        superData["lng"] = obj.language
        superData["PM"] = "D" if obj.platform == "desktop" else "M"
        superData["RG"] = obj.region
        superData["io"] = obj.isocode
        superData["edm"] = obj.exactdomain
        superData["srs"] = obj.search_results
        superData["brnk"] = int(obj.top_rank)
        superData["cd"] = obj.created_date.strftime("%Y-%m-%d")
        superData["lrd"] = obj.lastranked_date.date()

        # superData['AV'] = obj.search_volume
        superData["lct"] = Region.objects.filter(region_code=obj.isocode).first().region_country
        superData["lrupt"] = timeDifference(obj.lastranked_date)
        superData["nt"] = kwNotes.objects.filter(fk_keyword_id=obj.id, fk_user_id=obj.fk_user_id, fk_group_id=obj.fk_group_id).count()
        superData["spt"] = obj.keyword_snippet["tdy"]
        superData["spb"] = obj.keyword_snippet["best"]

        # Same pair DashKeywordSerializer publishes at :326. Without it the
        # keyword detail page only had feature data when the user arrived from
        # the keywords table, which passes the row in route state -- a direct
        # URL or a refresh showed nothing, and "nothing" is indistinguishable
        # from "no features found" unless the field is present to say which.
        #
        # This serializer takes a model instance, not a dict, so it is the
        # attribute rather than .get(). Every existing row reads None until a
        # rank run populates it, which `or {}` normalises; `sfm` is what tells
        # the UI apart "measured, none present" from "never measured".
        superData["sf"] = obj.serp_features or {}
        superData["sfm"] = bool(obj.serp_features)

        return superData


# check and remove
class kWPageHomeSerializer(serializers.ModelSerializer):
    G_N = serializers.SerializerMethodField("get_G_N")
    D_N = serializers.SerializerMethodField("get_D_N")

    class Meta:
        model = Groups
        fields = ("G_N", "D_N")

    def get_G_N(self, obj):
        return obj.group_name

    def get_D_N(self, obj):
        return obj.domain_name

    def to_representation(self, obj):
        logid = self.context["logid"] if "logid" in self.context else obj.fk_user_id
        superData = super().to_representation(obj)

        superData["sb_s"] = ""
        # superData['dn_d'] = obj.domain_info
        # superData['dn_s'] = obj.domain_status

        # Group Based Keywords
        grpKeyData = Keyword.objects.filter(fk_group_id=obj.id, fk_user_id=obj.fk_user_id)
        superData["kw_ln"] = grpKeyData.count()

        # Total Groups
        # grpAll = Groups.objects.filter(fk_user_id=obj.fk_user_id)
        # superData['g_ln'] = grpAll.count()
        # grpData = Groups.objects.filter(fk_user_id=obj.fk_user_id,id=obj.id).first()
        # superData['g_age'] = len(grpData.score_meter)

        # User Total Keywords

        # changed
        sts, cnt = totalKeywordsCount(obj.fk_user_id)
        usrKeyData = cnt
        superData["u_kw"] = usrKeyData

        # usrKeyData = Keyword.objects.filter(fk_user_id=logid)
        # superData['u_kw'] = usrKeyData.count()

        accountData = Accountusage.objects.filter(fb_user_id=logid).first()
        # accountData = Accountusage.objects.filter(fb_user_id=obj.fk_user_id).values('last_used_refresh_count', 'st_subscription_id', 'st_customer_id', 'st_purchase_id', 'plan_keyword_limit', 'plan_refresh_limit', 'used_refresh_limit').first()

        if accountData:
            superData["sb_s"], pOverRule = userPaymode(logid, accountData)
            # payData = UserSubscriptions.objects.filter(fk_user_id=obj.fk_user_id, st_subscription_id=accountData['st_subscription_id'], st_customer_id=accountData['st_customer_id'], fk_reference_type="MAIN").last()
            # if payData:
            # 	if payData.st_subscription_status == "SUBSCRIBED" and payData.st_pay_status == "PAID":
            # 		superData['sb_s'] = "active"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "PAID":
            # 		superData['sb_s'] = "active"
            # 	elif payData.st_subscription_status == "CANCEL" and payData.st_pay_status == "DROP":
            # 		superData['sb_s'] = "cancelled"
            # 	elif payData.st_subscription_status == "EXPIRE" and payData.st_pay_status == "FAIL":
            # 		superData['sb_s'] = "expire"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "UPDATING":
            # 		superData['sb_s'] = "renewal-update"
            # 	elif payData.st_subscription_status == "RENEWAL" and payData.st_pay_status == "FAIL":
            # 		superData['sb_s'] = "renewal-fail"

        # superData['rf_t'] = timeDifference(refreshData['refresh_time']) if 'refresh_time' in refreshData else timeDifference(obj.updated_date)
        superData["luRc"] = accountData.last_used_refresh_count if accountData.last_used_refresh_count else 0
        superData["tYP"] = accountData.st_purchase_id if accountData.st_purchase_id else 0
        superData["pKL"] = accountData.plan_keyword_limit if accountData.plan_keyword_limit else 0
        superData["pRL"] = accountData.plan_refresh_limit if accountData.plan_refresh_limit else 0
        superData["uRL"] = accountData.used_refresh_limit if accountData.used_refresh_limit else 0

        return superData


class kwNotesSerializer(serializers.ModelSerializer):
    tl = serializers.SerializerMethodField("get_tl")
    nt = serializers.SerializerMethodField("get_nt")
    nd = serializers.SerializerMethodField("get_nd")

    class Meta:
        model = kwNotes
        fields = ("id", "tl", "nt", "nd")

    def get_tl(self, obj):
        return obj.title

    def get_nt(self, obj):
        return obj.notes

    def get_nd(self, obj):
        return timezone.localtime(obj.note_date).strftime("%Y-%m-%d")


class userTrialExpireSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        currdate = datetime.now()
        trialenddate = obj.created_date + timedelta(obj.trial_days)
        trialexpireid = obj.id if trialenddate.strftime("%Y-%m-%d, %H:%M:%S") < currdate.strftime("%Y-%m-%d, %H:%M:%S") else None

        return trialexpireid


# New GrpKwSuggestionsList add
# class GrpKwSuggestionsListCreateSerializer(serializers.Serializer):
# 	def to_representation(self, obj):
# 		# print(obj.text)
# 		exitskws = self.context["kwname"]
# 		if obj.text not in exitskws:
# 			keyword_name = obj.text
# 			keyword_slug = f"{obj.text}".replace(" ", "_")
# 			list_months = []
# 			list_searches = []
# 			last_volume = -1
# 			for y in obj.keyword_idea_metrics.monthly_search_volumes:
# 				list_months.append(str(y.month)[12::] + " - " + str(y.year))
# 				list_searches.append(y.monthly_searches)
# 				last_volume = y.monthly_searches

# 			keywords = GrpKwSuggestionsList(
# 				fk_gks_id = 1,
# 				fk_group_id = self.context["grpid"],
# 				keyword = obj.text.lower().strip(),
# 				keyword_slug = f"{obj.text}".replace(" ", "_"),
# 				average_volume = obj.keyword_idea_metrics.avg_monthly_searches,
# 				last_volume = last_volume,
# 				comp_level = f"{str(obj.keyword_idea_metrics.competition)}".replace("KeywordPlanCompetitionLevel.", ""),
# 				comp_index = obj.keyword_idea_metrics.competition_index,
# 				month_wise_volume = list_searches,
# 				past_months = list_months
# 			)

# 			return keywords
# 		else:
# 			return None



class CustomGrpSerializer(serializers.Serializer):
    def to_representation(self, obj):
        superData = super().to_representation(obj)

        userid = obj['fk_user_id']
        grpid = obj['id'] 

        key_count = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).count()

        total_limit = total_price = 0
        if "plans" in self.context:
            total_limit, total_price = calculate_billings(self.context['plans'], key_count)

        superData['pr_nm'] = obj['group_name'] 
        superData['ud_kwrds'] = key_count
        superData['key_lmt'] = total_limit
        superData['prc'] = total_price
        superData['dn'] = obj['domain_name'] 

        return superData
