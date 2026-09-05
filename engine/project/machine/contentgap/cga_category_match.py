import base64
import sys, os, random, socket, re, cloudscraper, json
from datetime import datetime, date
from urllib.parse import urlparse

from django.shortcuts import render
from django.conf import settings

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainCategoryUrls, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchCategoryUrls, CGASearchMatch
from project.machine import automation_common as _at__common_
from project.machine.contentgap.cga_serializers import *

from project.machine.contentgap import cga_category
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def compare_lists(A, B):
    A_set, B_set = set(A), set(B)

    matches = list(A_set & B_set)
    unmatched_A = list(A_set - B_set)
    unmatched_B = list(B_set - A_set)

    return {"matches": matches, "unmatched_A": unmatched_A, "unmatched_B": unmatched_B}


def automation_cga_category_mapper(cg_self_domain_id, cg_comp_domain_id, cg_search_data):  # ORIGINAL
    try:
        if cg_self_domain_id and cg_comp_domain_id and cg_search_data:

            cg_self_dc_data = {}
            cg_self_dc_list = []
            cg_self_domain_category = CGADomainCategory.objects.filter(fk_domain_id=cg_self_domain_id).values("domain_category_id", "category_name").all()
            for each_dc in cg_self_domain_category:
                cg_self_dc_data[each_dc["category_name"]] = each_dc["domain_category_id"]

            cg_comp_dc_data = {}
            cg_comp_dc_list = []
            cg_comp_domain_category = CGADomainCategory.objects.filter(fk_domain_id=cg_comp_domain_id).values("domain_category_id", "category_name").all()
            for each_dc in cg_comp_domain_category:
                cg_comp_dc_data[each_dc["category_name"]] = each_dc["domain_category_id"]

            if cg_self_dc_data:
                cg_self_dc_list = list(cg_self_dc_data.keys())

            if cg_comp_dc_data:
                cg_comp_dc_list = list(cg_comp_dc_data.keys())

            if cg_self_dc_list and cg_comp_dc_list:
                compared_list = compare_lists(cg_self_dc_list, cg_comp_dc_list)
                print("compared_list ", compared_list)

                if "matches" in compared_list and len(compared_list["matches"]):
                    # GET ALL DOMAIN CATEGORY IDS FROM MATCHED CATEGORY NAMES OF TWO DOMAINS
                    domain_cat_a, domain_cat_b = list(), list()

                    for each_item in compared_list["matches"]:
                        each_item = each_item.lower()

                        if each_item in cg_self_dc_data:
                            domain_cat_a.append(cg_self_dc_data[each_item])

                        if each_item in cg_comp_dc_data:
                            domain_cat_b.append(cg_comp_dc_data[each_item])

                    # RETRIEVE ALL DOMAIN URLS IDS IN list FOR EACH CATEGORY IDS
                    domain_cat_a_urls_id, domain_cat_b_urls_id = dict(), dict()

                    domain_cat_a_urls_values = CGADomainCategoryUrls.objects.filter(fk_domain_category_id__in=domain_cat_a).values("fk_domain_category_id", "fk_domain_url_id").all()
                    if domain_cat_a_urls_values:
                        for single_item in domain_cat_a_urls_values:
                            if str(single_item["fk_domain_category_id"]) not in domain_cat_a_urls_id:
                                domain_cat_a_urls_id[str(single_item["fk_domain_category_id"])] = []

                            domain_cat_a_urls_id[str(single_item["fk_domain_category_id"])].append(str(single_item["fk_domain_url_id"]))

                    domain_cat_b_urls_values = CGADomainCategoryUrls.objects.filter(fk_domain_category_id__in=domain_cat_b).values("fk_domain_category_id", "fk_domain_url_id").all()
                    if domain_cat_b_urls_values:
                        for single_item in domain_cat_b_urls_values:

                            if str(single_item["fk_domain_category_id"]) not in domain_cat_b_urls_id:
                                domain_cat_b_urls_id[str(single_item["fk_domain_category_id"])] = []

                            domain_cat_b_urls_id[str(single_item["fk_domain_category_id"])].append(str(single_item["fk_domain_url_id"]))

                    # CREATE SEARCH CATEGORY
                    serializer = SearchCategoryCreateSerializer(compared_list["matches"], many=True, context={"active_data": cg_search_data})
                    bulk_search_categories_records = list(filter(None, serializer.data))
                    bulk_search_categories = CGASearchCategory.objects.bulk_create(bulk_search_categories_records)

                    # MAP BULK URLS WITH PRIMARY KEYS
                    search_category_keys = {}
                    search_category_urls_serial_data = []

                    for obj in bulk_search_categories:
                        if obj.category_name in cg_self_dc_data and obj.category_name in cg_comp_dc_data:
                            obj_self_domain_cat_id = str(cg_self_dc_data[obj.category_name])
                            obj_comp_domain_cat_id = str(cg_comp_dc_data[obj.category_name])

                            if obj_self_domain_cat_id in domain_cat_a_urls_id and obj_comp_domain_cat_id in domain_cat_b_urls_id:
                                # SELF DOMAIN - SEARCH CATEGORY URLS CREATION
                                serializer = SearchCategoryUrlsCreateSerializer(domain_cat_a_urls_id[obj_self_domain_cat_id], many=True, context={"search_category_id": obj.search_category_id, "domain_id": cg_self_domain_id, "active_data": cg_search_data})
                                search_category_urls_serial_data = search_category_urls_serial_data + serializer.data

                                # COMP DOMAIN - SEARCH CATEGORY URLS CREATION
                                serializer = SearchCategoryUrlsCreateSerializer(domain_cat_b_urls_id[obj_comp_domain_cat_id], many=True, context={"search_category_id": obj.search_category_id, "domain_id": cg_comp_domain_id, "active_data": cg_search_data})
                                search_category_urls_serial_data = search_category_urls_serial_data + serializer.data

                    if search_category_urls_serial_data:
                        bulk_records = list(filter(None, search_category_urls_serial_data))
                        CGASearchCategoryUrls.objects.bulk_create(bulk_records)

                uncategorised_cat_data = CGASearchCategory.objects.filter(fk_user_id=cg_search_data["fk_user_id"], fk_search_id=cg_search_data["search_id"], category_name="uncategorised").first()
                if not uncategorised_cat_data:
                    serializer = SearchCategoryCreateSerializer(["uncategorised"], many=True, context={"active_data": cg_search_data})
                    bulk_search_categories = CGASearchCategory.objects.bulk_create(serializer.data)
                    uncategorised_cat_id = bulk_search_categories[0].search_category_id
                else:
                    uncategorised_cat_id = uncategorised_cat_data.search_category_id

                print("\n\n uncategorised_cat_id: ", uncategorised_cat_id)

                if "unmatched_A" in compared_list and len(compared_list["unmatched_A"]):
                    print("unmatched_A ", compared_list["unmatched_A"])
                    unmatched_cat_a = list()

                    for each_item in compared_list["unmatched_A"]:
                        each_item = each_item.lower()
                        if each_item in cg_self_dc_data:
                            unmatched_cat_a.append(cg_self_dc_data[each_item])

                    unmatched_cat_a_urls_values = CGADomainCategoryUrls.objects.filter(fk_domain_category_id__in=unmatched_cat_a).values_list("fk_domain_url_id", flat=True).all()
                    print("\n\n", "unmatched_cat_a_urls_values ", unmatched_cat_a_urls_values)
                    print(len(unmatched_cat_a_urls_values))
                    if unmatched_cat_a_urls_values:
                        serializer = SearchCategoryUrlsCreateSerializer(unmatched_cat_a_urls_values, many=True, context={"search_category_id": uncategorised_cat_id, "domain_id": cg_self_domain_id, "active_data": cg_search_data})
                        bulk_records = list(filter(None, serializer.data))
                        CGASearchCategoryUrls.objects.bulk_create(bulk_records)

                if "unmatched_B" in compared_list and len(compared_list["unmatched_B"]):
                    print("unmatched_B ", compared_list["unmatched_B"])
                    unmatched_cat_b = list()

                    for each_item in compared_list["unmatched_B"]:
                        each_item = each_item.lower()
                        if each_item in cg_comp_dc_data:
                            unmatched_cat_b.append(cg_comp_dc_data[each_item])

                    unmatched_cat_b_urls_values = CGADomainCategoryUrls.objects.filter(fk_domain_category_id__in=unmatched_cat_b).values_list("fk_domain_url_id", flat=True).all()

                    print("\n\n", "unmatched_cat_b_urls_values ", unmatched_cat_b_urls_values)
                    print(len(unmatched_cat_b_urls_values))

                    if unmatched_cat_b_urls_values:
                        serializer = SearchCategoryUrlsCreateSerializer(unmatched_cat_b_urls_values, many=True, context={"search_category_id": uncategorised_cat_id, "domain_id": cg_comp_domain_id, "active_data": cg_search_data})
                        bulk_records = list(filter(None, serializer.data))
                        CGASearchCategoryUrls.objects.bulk_create(bulk_records)

            # CHECK
            # cg_domain_url_count = CGADomainUrl.objects.filter(fk_domain_id__in=[cg_self_domain_id, cg_comp_domain_id]).count()
            cg_search_url_count = CGASearchCategoryUrls.objects.filter(fk_domain_id__in=[cg_self_domain_id, cg_comp_domain_id]).count()

            if cg_search_url_count > 0:
                return True

    except Exception as e:
        print("ERROR MAPPER " + str(e))
        raise e

    return False
