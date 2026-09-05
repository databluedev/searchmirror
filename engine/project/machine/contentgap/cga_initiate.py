import base64
import sys, os, random, socket, re
from datetime import datetime, date
from urllib.parse import urlparse

from django.shortcuts import render
from django.conf import settings

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchMatch
from project.machine import automation_common as _at__common_

from project.machine.contentgap import cga_scraper as cga_scrap
from project.machine.contentgap import cga_category_match as cga_cm

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse


def extract_domain(url):
    # Ensure the URL has a valid protocol for parsing
    if not re.match(r"http[s]?://", url):
        url = "http://" + url  # Add HTTP if missing

    # Parse the URL
    parsed_url = urlparse(url)

    # Extract subdomain and domain
    domain = parsed_url.netloc

    return domain


def remove_www(url):
    return re.sub(r"^(https?:\/\/)?(www\.)?", r"\1", url)


def validate_and_format_url(url):
    # Check if the URL starts with a protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url  # Default to HTTPS

    # Validate the domain format
    pattern = r"^(https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/.*)?$"
    domain = remove_www(url)

    match = re.match(pattern, domain)

    if match:
        return url  # Valid domain format
    else:
        return 0


def is_domain_real(domain):
    try:
        socket.gethostbyname(domain)  # Resolves domain to an IP
        return True
    except socket.gaierror:
        return False


def process_domain(domain):
    try:
        domain = validate_and_format_url(domain)
        if domain:
            domain_flag = extract_domain(domain)
            return domain, domain_flag, is_domain_real(domain_flag)

    except Exception as e:
        pass

    return False, False, None


def format_connection_status(domain_name):
    if len(domain_name) == 1:
        return f"{domain_name[0]} is not reacheable or invalid."
    elif len(domain_name) == 2:
        return f"{' and '.join(domain_name)} are not reacheable or invalid."
    else:
        return ""


@api_view(["GET"])
def automation_cga_call(request, _ustr_, _kstr_):
    try:
        _base__result_, _setting__data_ = _at__common_.__base_validation__(request, _ustr_)
        if _base__result_ and _kstr_.isdigit():
            if int(_kstr_) % 2 == 1:
                _cg__active__data_ = CGASearch.objects.filter(search_status="INIT").values("search_id", "fk_self_domain_id", "fk_comp_domain_id", "fk_user_id").order_by("modified_date").first()  # ASC ORDER
            else:
                _cg__active__data_ = CGASearch.objects.filter(search_status="INIT").values("search_id", "fk_self_domain_id", "fk_comp_domain_id", "fk_user_id").order_by("-modified_date").first()  # DESC ORDER

            if _cg__active__data_ and "search_id" in _cg__active__data_:
                CGASearch.objects.filter(search_id=_cg__active__data_["search_id"]).update(search_status="SCHD", modified_date=datetime.now())

                _cg__domains_ = CGADomain.objects.filter(track_status__in=["START", "FAIL"], domain_id__in=[_cg__active__data_["fk_self_domain_id"], _cg__active__data_["fk_comp_domain_id"]]).values("domain_id", "target_domain", "absolute_domain", "track_status").all()

                if _cg__domains_:
                    _cg__flag__list_ = []
                    _cg__domain__list_ = []

                    for _cg__each__domain_ in _cg__domains_:
                        domain, domain_host, domain_flag = process_domain(_cg__each__domain_["absolute_domain"])

                        if domain_flag == True:
                            _cg__domain_ = {}
                            _cg__domain_["id"] = _cg__each__domain_["domain_id"]
                            _cg__domain_["fd"] = domain
                            _cg__domain_["pd"] = domain_host
                            _cg__domain__list_.append(_cg__domain_)
                        else:
                            error_message = str(domain_host) + " - The domain seems not reacheable or invalid"
                            CGADomain.objects.filter(domain_id=_cg__each__domain_["domain_id"]).update(track_status="FAIL", track_message=error_message, last_track_date=datetime.now())
                            _cg__flag__list_.append(domain_host)

                    if not _cg__flag__list_ and _cg__domain__list_:
                        _cg_return_ = cga_scrap.automation_cga_scraper(_cg__domain__list_, _cg__active__data_["search_id"])
                    else:
                        # IF ANY ONE DOMAIN WERE FAILED TO REACH OR INVALID.
                        error_message = format_connection_status(_cg__flag__list_)
                        CGASearch.objects.filter(search_id=_cg__active__data_["search_id"]).update(search_status="FAIL", search_message=error_message, modified_date=datetime.now())
                        return JsonResponse({"st": 0, "status": "Domain are not reacheable or invalid. Try again Later"})

                # CHECK FOR DOMAIN CATEGORY MATCH FROM GIVEN SCHEDULED DOMAINS
                _cg__domains_ = CGADomain.objects.filter(track_status="COMP", domain_id__in=[_cg__active__data_["fk_self_domain_id"], _cg__active__data_["fk_comp_domain_id"]]).values("domain_id", "target_domain", "absolute_domain", "track_status").all()
                if len(_cg__domains_) == 2:
                    cga_cm_status = cga_cm.automation_cga_category_mapper(_cg__active__data_["fk_self_domain_id"], _cg__active__data_["fk_comp_domain_id"], _cg__active__data_)
                    if cga_cm_status:
                        CGASearch.objects.filter(search_id=_cg__active__data_["search_id"]).update(search_status="DONE", search_message="Completed the CGA Category Search Mapping", modified_date=datetime.now())
                    else:
                        CGASearch.objects.filter(search_id=_cg__active__data_["search_id"]).update(search_status="FAIL", search_message="Error occurs in CGA Category Search Mapping", modified_date=datetime.now())

                    return JsonResponse({"st": 1, "status": cga_cm_status})

                else:
                    error_message = "Domains are failed in their tracking"
                    CGASearch.objects.filter(search_id=_cg__active__data_["search_id"]).update(search_status="FAIL", search_message=error_message, modified_date=datetime.now())
                    return JsonResponse({"st": 0, "status": "Domain are not reacheable or invalid. Try again Later"})

            elif not _cg__active__data_:
                return JsonResponse({"st": 0, "status": "No Records are present for the CGA Search"})

    except Exception as e:
        return JsonResponse({"st": 0, "status": str(e)})

    return JsonResponse({"st": 0, "status": "OOPS! visit tracker.example"})
