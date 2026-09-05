from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.serializers import *
from serp.common import *
from account.models import Account
from datetime import date,datetime,timedelta

from currency_converter import CurrencyConverter
from account.cron_auth import cron_only


# cron to trial expiry update on status  
@cron_only
def user_trial_expiry(request):
    accUseIns = Accountusage.objects.filter(status="default", user_type="trial").all()
    trialexpireids = userTrialExpireSerializer(accUseIns, many=True).data

    trialexpireids = list(filter(None, trialexpireids))
    if len(trialexpireids) > 0: 
        value = Accountusage.objects.filter(id__in=trialexpireids).update(status="close")
        return JsonResponse({'status':'true','message': 'Trial expire accounts: '+ str(trialexpireids)})

    return JsonResponse({'status':'false','message': 'No trial account exists to expire'})


# cron to currency update on MainSettings  
@cron_only
def currency_convert(request):
	c = CurrencyConverter()
	inr_rate = c.convert(1, 'USD', 'INR')
	rate_usd_inr = f'{inr_rate:.2f}' if isfloat_isdigit(f'{inr_rate:.2f}') else "0.0"
	MainSettingsIns = Settings.objects.filter(id=1).update(rate_usd_inr=rate_usd_inr)

	return JsonResponse({'status':'true','message': 'Currency update successfully'})

def report_schedule_reset(request):
    Flag = Report.objects.exclude(schedule_mode__in=['DONE','SENT']).filter(id__gt=0).update(schedule_mode="DONE")
    if Flag:
        return JsonResponse({'status':'true','message': 'Report reset done successfully'})

    return JsonResponse({'status':'false','message': 'No Report are to reset'})
