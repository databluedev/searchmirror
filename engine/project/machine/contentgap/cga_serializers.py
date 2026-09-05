from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainCategoryUrls, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchCategoryUrls, CGASearchMatch
from project.machine.submodels.accountmodels import Account 

from bisect import bisect_right 
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse
import string, random 
from collections import defaultdict
import collections


class UrlCreateSerializer(serializers.Serializer):

    def to_representation(self, obj): 
        domain_urls = CGADomainUrl( 
            fk_domain_id = self.context["domain"],
            source_url = obj,
            traffic = [],
            backlink = [],
            keywords = [],
            average_rank = [],
            url_status = "INIT"
        )

        return domain_urls

class CategoryCreateSerializer(serializers.Serializer):

    def to_representation(self, obj): 
        domain_categories = CGADomainCategory( 
            category_name = obj,
            category_slug = obj.replace(" ", "_"),  
            fk_domain_id = self.context["domain"]
        )

        return domain_categories


class CategoryUrlCreateSerializer(serializers.Serializer): 

    def to_representation(self, obj): 
        if obj:
            cat_name = self.context["cat"]
            url_id = self.context["durls"][obj] if obj in self.context["durls"] else None
            cat_id = self.context["dcats"][cat_name] if cat_name in self.context["dcats"] else None

            if url_id and cat_id:
                domain_urls_category = CGADomainCategoryUrls(
                    fk_domain_category_id = cat_id, 
                    fk_domain_url_id = url_id 
                )
                return domain_urls_category         
        return None

class SearchCategoryCreateSerializer(serializers.Serializer): 
    def to_representation(self, obj): 
        if obj:
            active_data = self.context["active_data"]

            if "search_id" in active_data:
                domain_urls_category = CGASearchCategory(
                    fk_user_id = active_data["fk_user_id"], 
                    fk_search_id = active_data["search_id"],
                    category_name = obj.lower(),
                    category_slug = obj.lower().replace(" ", "_"),
                    fk_self_domain_id = active_data["fk_self_domain_id"],
                    fk_comp_domain_id = active_data["fk_comp_domain_id"],
                    category_status = None,
                    metric_status = None,  
                    metric_error_message = "" 
                )

                return domain_urls_category

        return None

class SearchCategoryUrlsCreateSerializer(serializers.Serializer): 
    def to_representation(self, obj): 
        if obj:
            active_data = self.context["active_data"]
            domain_id = self.context["domain_id"]
            search_category_id = self.context["search_category_id"] 

            if "search_id" in active_data and domain_id and search_category_id:
                domain_search_category_urls = CGASearchCategoryUrls(
                    fk_user_id = active_data["fk_user_id"], 
                    fk_search_id = active_data["search_id"],
                    fk_domain_id = domain_id,
                    fk_domain_url_id = obj,
                    fk_search_category_id = search_category_id
                )

                return domain_search_category_urls 

        return None

class SearchMatchUrlsCreateSerializer(serializers.Serializer): 
    def to_representation(self, obj): 
        if obj:
            active_data = self.context["active_data"]
            url_data = self.context["url_data"]

            if "fk_search_id" in active_data and "fk_user_id" in active_data and "search_category_id" in active_data:
                if obj[0] in url_data and obj[1] in url_data:
                    search_match_urls = CGASearchMatch(
                        fk_user_id = active_data["fk_user_id"],
                        fk_search_id = active_data["fk_search_id"],
                        fk_search_category_id = active_data["search_category_id"],
                        source_url_id = url_data[obj[0]],
                        match_url_id = url_data[obj[1]],
                        metric_status = "INIT" 
                    ) 
                    return search_match_urls 
            return None

class SearchUnMatchUrlsCreateSerializer(serializers.Serializer): 
    def to_representation(self, obj): 
        if obj:
            active_data = self.context["active_data"]
            url_data = self.context["url_data"]
            check_key = self.context["check_key"]

            if "fk_search_id" in active_data and "fk_user_id" in active_data and "search_category_id" in active_data:
                if obj in url_data:
                    search_match_urls = CGASearchMatch(
                        fk_user_id = active_data["fk_user_id"],
                        fk_search_id = active_data["fk_search_id"],
                        fk_search_category_id = active_data["search_category_id"],
                        source_url_id = url_data[obj] if check_key == "unmatched_a" else None,
                        match_url_id = url_data[obj] if check_key == "unmatched_b" else None, 
                        metric_status = "INIT" 
                    ) 
                    return search_match_urls
            return None
        