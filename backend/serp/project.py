import os
from rest_framework.decorators import api_view
from serp.models import *
from serp.serializers import *
from serp.common import *
from serp import calculation, views as serp_views    
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from mailend.models import KeywordHistory 
from account import verify as authPermission
import numpy
from operator import itemgetter

from django.shortcuts import render, redirect
import requests, json
from serp.models import *
from serp.common import *
import string,random 
from urllib.parse import urlparse
from datetime import date,datetime,timedelta,time
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny

import validators

@api_view(['POST']) 
def _website_target_keywords_(request): 
    try:
        if request.method == 'POST' and authPermission.validate(request, "POST"):
            userid = request.data['userid']
            
            if userid: 
                site_name = request.data['_stN_'] 
            
                if userid.isdigit() and isinstance(site_name, str):
                    if all(variable != "" for variable in (site_name)):
                        site_name = site_name.strip() 

                        uri = urlparse(site_name)
                        if (uri.scheme == "" or uri.scheme is None):
                            # Default to https for any bare domain. The presence
                            # of "www." never had anything to do with the scheme;
                            # it just meant "datablue.dev" was saved as http://
                            # while "www.datablue.dev" was saved as https://.
                            site_name = "https://" + site_name

                        if site_name:
                            # VALIDATING THE URL MUST CONTAINS THE PROTOCOL WITH DOMAIN 
                            domainValidtor = validators.url(site_name) 
                            if domainValidtor == True: 
                                # EXTRACT THE SUBDOMAIN OR DOMAIN FROM URL WITHOUT PROTOCOL
                                host_name = host_domain(site_name)
                                if len(host_name):
                                    target_exist = SiteKeywords.objects.filter(domain=host_name).exists()

                                    if target_exist: 
                                        _target_keywords_ = list(SiteKeywords.objects.filter(domain=host_name).values_list("keyword_list", flat=True).first()) 
                                        if _target_keywords_: 
                                            _target_keywords_ = list(dict.fromkeys(_target_keywords_)) 
                                            return JsonResponse({'status': 1, "ds": _target_keywords_, 'ms': 'Domain is valid', 'st': site_name})
                                        else:
                                            return JsonResponse({'status': 0, 'ms': 'Domain is valid', 'st': site_name }) 
                                    else:
                                        # Domain keyword discovery is intentionally parked until
                                        # the first-party Ads integration is available. Project
                                        # creation still validates and accepts the domain; users
                                        # add the keywords they actually want to track.
                                        return JsonResponse({'status': 0, 'ms': 'Domain is valid', 'st': site_name })
                            else:
                                return Response({'status': -1, 'ms': 'Website URL is invalid. Enter the correct website'}) 
                        else:
                            return Response({'status': -1, 'ms': 'Enter the website'}) 
    except Exception as e:
        return JsonResponse({'status': -2, 'ms': str(e)})

    return JsonResponse({'status': -2, 'ms': "Something went wrong."})
