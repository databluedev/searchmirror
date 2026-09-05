from serp.rank_state import depth_ceiling, rank_state
from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS
from serp.models import *
from serp.common import *
from mailend.models import KeywordHistory
from account.models import Account
from bisect import bisect_right
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse
import string, random
from serp import calculation
from collections import defaultdict

import collections
import numpy


class TrendingWidgetSerializer(serializers.ModelSerializer):
    ky = serializers.SerializerMethodField("get_keyword")
    cc = serializers.SerializerMethodField("get_country_code")
    Vd = serializers.SerializerMethodField("get_last_month_difference")

    class Meta:
        model = keywordVolume
        fields = ("ky", "cc", "Vd")

    def get_keyword(self, obj):
        return obj.keyword

    def get_country_code(self, obj):
        return obj.region_code

    def get_last_month_difference(self, obj):
        if obj.last_month_difference.lower() == "up":
            return 1
        elif obj.last_month_difference.lower() == "down":
            return -1
        elif obj.last_month_difference.lower() == "same":
            return 0
        else:
            return 0

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        superData["V"] = obj.month_wise_volume[-1] if len(obj.month_wise_volume) > 1 else -1
        superData["pV"] = obj.month_wise_volume[-2] if len(obj.month_wise_volume) > 1 else -1
        SVMY = obj.past_months[-1].split("-", 1) if len(obj.past_months) > 1 else []
        superData["Vm"] = SVMY[0].capitalize().strip() if len(SVMY) > 1 else ""
        PSVMY = obj.past_months[-2].split("-", 1) if len(obj.past_months) > 1 else []
        superData["Vpm"] = PSVMY[0].capitalize().strip() if len(PSVMY) > 1 else ""

        superData["od"] = 0
        superData["Ry"] = ""
        superData["Rn"] = ""
        superData["rg"] = ""
        superData["cy"] = ""
        superData["ln"] = ""
        superData["pt"] = "D"
        superData["sr"] = ""
        superData["kd"] = 0

        kvQuery = Keyword.objects.filter(id=obj.fk_keyword_id)
        if kvQuery.exists():
            kvData = kvQuery.first()
            superData["kd"] = kvData.id
            superData["od"] = kvData.dayval if kvData.daymark != "down" else -abs(int(kvData.dayval))
            if len(kvData.rank) > 1:
                superData["Ry"] = kvData.rank[1] if kvData.rank[1] > 0 else None
            else:
                superData["Ry"] = "-"

            _rn, _rs, _rc, _rsk = rank_state(kvData, self.context.get('account_pages'))
            superData["Rn"] = _rn
            superData["RnS"] = _rs
            superData["RnC"] = _rc
            superData["rg"] = kvData.region
            superData["cy"] = kvData.location.split("(")[1].replace(")", "").strip() if "(" in kvData.location else "-"
            superData["ln"] = kvData.language
            superData["pt"] = "M" if kvData.platform.lower() == "mobile" else "D"
            superData["sr"] = kvData.search_results

        return superData


class CannibalizationWidgetSerializer(serializers.ModelSerializer):
    ky = serializers.SerializerMethodField("get_keyword")
    cc = serializers.SerializerMethodField("get_country_code")
    dd = serializers.SerializerMethodField("get_last_day_difference")
    Ry = serializers.SerializerMethodField("get_rank_yesterday")

    class Meta:
        model = Keyword
        fields = ("ky", "cc", "dd", "Ry")

    def get_keyword(self, obj):
        return obj.keyword

    def get_country_code(self, obj):
        return obj.isocode

    def get_last_day_difference(self, obj):
        if obj.daymark.lower() == "up":
            return 1
        elif obj.daymark.lower() == "down":
            return -1
        elif obj.daymark.lower() == "same":
            return 0
        else:
            return 0

    def get_rank_yesterday(self, obj):
        # A history entry carries no failure marker, so 0 there can only
        # mean "did not appear in the depth searched that day". None rather
        # than the old out-of-range sentinel, so nothing renders a position
        # that was never observed.
        if len(obj.rank) > 1:
            return obj.rank[1] if obj.rank[1] > 0 else None
        else:
            return "-"

    def to_representation(self, obj):
        superData = super().to_representation(obj)
        superData["keyid"] = obj.id
        superData["rnk"] = obj.rank[0:2]
        _rnw, _rs, _rc, _rsk = rank_state(obj, self.context.get('account_pages'))
        superData["rnw"] = _rnw
        superData["rnwS"] = _rs
        superData["rnwC"] = _rc
        superData["rg"] = obj.region
        superData["cy"] = obj.location.split("(")[1].replace(")", "").strip() if "(" in obj.location else "-"
        superData["ln"] = obj.language
        superData["sr"] = obj.search_results
        superData["cnb"] = obj.cannibalisation

        return superData


class BrandSerializer(serializers.ModelSerializer):
    ky = serializers.SerializerMethodField("get_keyword")
    # rc = serializers.SerializerMethodField('get_country_code')
    adp = serializers.SerializerMethodField("get_ad_position")

    class Meta:
        model = brandObtain
        fields = ("ky", "adp")

    def get_keyword(self, obj):
        return obj["bkeyword"]

    # def get_country_code(self, obj):
    # 	return obj.isocode

    def get_ad_position(self, obj):
        if obj["ads"] == 0:
            return "-"
        elif obj["ads"] == 2:
            return "Ain"
        else:
            if int(obj["serp_json"]["ads"]["top_count"]) > 0 and obj["serp_json"]["ads"]["bottom_count"] > 0:
                return "Atb"
            elif int(obj["serp_json"]["ads"]["top_count"]) > 0:
                return "At"
            elif int(obj["serp_json"]["ads"]["bottom_count"]) > 0:
                return "Ab"
            else:
                return "-"

    def to_representation(self, obj):
        superData = super().to_representation(obj)
        superData["keyid"] = obj["id"]
        superData["rg"] = obj["input_json"]["region"]
        superData["cy"] = obj["input_json"]["country"]
        superData["ln"] = obj["input_json"]["language"]
        superData["sr"] = obj["serp_json"]["srs"] or ""
        superData["ads"] = obj["ads"]
        superData["cc"] = obj["isocode"]
        superData["keysts"] = obj["brand_call_status"]

        if self.context["pagetype"] == "settings":
            superData["fmt"] = obj["report_format"]
            superData["adc"] = obj["serp_json"]["ads"]["top_count"] + obj["serp_json"]["ads"]["bottom_count"]

        return superData


class ImpDecKwdWidgetSerializer(serializers.ModelSerializer):
    kd = serializers.SerializerMethodField("get_id")
    ky = serializers.SerializerMethodField("get_keyword")
    od = serializers.SerializerMethodField("get_day_difference")
    cc = serializers.SerializerMethodField("get_country_code")
    Ry = serializers.SerializerMethodField("get_rank_yesterday")
    Rn = serializers.SerializerMethodField("get_rank")
    rg = serializers.SerializerMethodField("get_region")
    cy = serializers.SerializerMethodField("get_country")
    ln = serializers.SerializerMethodField("get_language")
    pt = serializers.SerializerMethodField("get_platform")
    sr = serializers.SerializerMethodField("get_search_results")

    class Meta:
        model = Keyword
        fields = ("kd", "ky", "od", "cc", "Ry", "Rn", "rg", "cy", "ln", "pt", "sr")

    def get_id(self, obj):
        return obj.id

    def get_keyword(self, obj):
        return obj.keyword.strip()

    def get_day_difference(self, obj):
        return obj.dayval if obj.daymark != "down" else -abs(int(obj.dayval))

    def get_platform(self, obj):
        return "M" if obj.platform.lower() == "mobile" else "D"

    def get_rank_yesterday(self, obj):
        # A history entry carries no failure marker, so 0 there can only
        # mean "did not appear in the depth searched that day". None rather
        # than the old out-of-range sentinel, so nothing renders a position
        # that was never observed.
        if len(obj.rank) > 1:
            return obj.rank[1] if obj.rank[1] > 0 else None
        else:
            return "-"

    def get_rank(self, obj):
        # None rather than the old out-of-range sentinel: a keyword that did
        # not rank was not measured at any position, and the companion state
        # field says which of the four cases it is.
        return rank_state(obj, self.context.get('account_pages'))[0]

    def get_search_results(self, obj):
        return obj.search_results

    def get_country_code(self, obj):
        return obj.isocode.strip()

    def get_region(self, obj):
        return obj.region.strip()

    def get_country(self, obj):
        country = obj.location.split("(")[1].replace(")", "").strip() if "(" in obj.location else "-"
        return country

    def get_language(self, obj):
        return obj.language.strip()

    def to_representation(self, obj):
        superData = super().to_representation(obj)

        superData["Vd"] = 0
        superData["V"] = -1
        superData["pV"] = -1
        superData["Vm"] = ""
        superData["Vpm"] = ""

        svExists = keywordVolume.objects.filter(fk_keyword_id=obj.id)

        if svExists.exists():
            svData = svExists.first()

            if svData != None:
                volVariation = svData.last_month_difference.lower()
                if volVariation == "up":
                    superData["Vd"] = 1
                elif volVariation == "down":
                    superData["Vd"] = -1
                elif volVariation == "same":
                    superData["Vd"] = 0

                superData["V"] = svData.month_wise_volume[-1] if len(svData.month_wise_volume) > 1 else -1
                superData["pV"] = svData.month_wise_volume[-2] if len(svData.month_wise_volume) > 1 else -1
                SVMY = svData.past_months[-1].split("-", 1) if len(svData.past_months) > 1 else []
                superData["Vm"] = SVMY[0].capitalize().strip() if len(SVMY) > 1 else ""
                PSVMY = svData.past_months[-2].split("-", 1) if len(svData.past_months) > 1 else []
                superData["Vpm"] = PSVMY[0].capitalize().strip() if len(PSVMY) > 1 else ""

        return superData


# Format this date
def gsc_date_formatter(original_date, interval):

    # Convert to datetime object
    dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z") if interval == "M" else datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S.%f%z")

    # Format to the desired format
    formatted_date = dt_object.strftime("%B %Y") if interval == "M" else dt_object.strftime("%b %d, %Y")

    return formatted_date


class GSCWeeklyQuerySerializer(serializers.Serializer):

    class Meta:
        model = GSCWeeklyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["timeline"] = gsc_date_formatter(str(instance.week_start_date), "W") + " - " + gsc_date_formatter(str(instance.week_end_date), "W")
        representation["queries"] = instance.queries

        return representation


class GSCWeeklyPageSerializer(serializers.Serializer):

    class Meta:
        model = GSCWeeklyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["timeline"] = gsc_date_formatter(str(instance.week_start_date), "W") + " - " + gsc_date_formatter(str(instance.week_end_date), "W")
        representation["pages"] = instance.pages

        return representation


class GSCMonthlyQuerySerializer(serializers.Serializer):

    class Meta:
        model = GSCMonthlyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["timeline"] = gsc_date_formatter(str(instance.month_start_date), "M")
        representation["queries"] = instance.queries

        return representation


class GSCMonthlyPageSerializer(serializers.Serializer):

    class Meta:
        model = GSCMonthlyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["timeline"] = gsc_date_formatter(str(instance.month_start_date), "M")
        representation["pages"] = instance.pages

        return representation


class GSCWeeklyQDataSerializer(serializers.Serializer):

    class Meta:
        model = GSCWeeklyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["week_start_date"] = instance["week_start_date"]
        representation["week_end_date"] = instance["week_end_date"]
        representation["queries"] = instance["queries"]
        representation["pages"] = instance["pages"]
        # representation['overview'] = instance['overview']

        return representation


class GSCMonthlyQDataSerializer(serializers.Serializer):

    class Meta:
        model = GSCMonthlyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["month_start_date"] = instance["month_start_date"]
        representation["month_end_date"] = instance["month_end_date"]
        representation["queries"] = instance["queries"]
        representation["pages"] = instance["pages"]
        # representation['overview'] = instance['overview']

        return representation


class DomainTrackSerializer(serializers.Serializer):

    class Meta:
        model = DomainTracking

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["da_metrics"] = instance["da_metrics"][::-1] if self.context.get('order_by') =="asc" else instance["da_metrics"]
        representation["dr_metrics"] = instance["dr_metrics"][::-1] if self.context.get('order_by') =="asc" else instance["dr_metrics"]

        return representation
    
class TestCollectionSerializer(serializers.Serializer):
    def to_representation(self, obj):
        # test_collection=TestCollection(landing_page=)
        return obj
