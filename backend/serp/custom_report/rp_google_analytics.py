from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.common import *
from account.models import Account  
from serp.models import * 
from serp.custom_serializer.report_serializers import * 
from account import verify as authPermission
from django.conf import settings
from dateutil.relativedelta import relativedelta

import string, random 
from datetime import date, datetime, timedelta

# NON ECOMMERCE - ANALYTICS FILE 
from serp.custom_report.non_ecom import rp_past_analytics as rpPA
from serp.custom_report.non_ecom import rp_present_analytics as rpPRA 

# ECOMMERCE - ANALYTICS FILE 
from serp.custom_report.ecom import rp_ecom_analytics as rpECPA 
from serp.custom_report.ecom import rp_ecom_present_analytics as rpEPRA 
from account.cron_auth import cron_only

MAX_TRACKS = 5

def next_month(totalmonth=1): 
    next_month_date = datetime.now() + relativedelta(months=totalmonth) 
    next_time = next_month_date.replace(day=3)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00") 


def next_date(totaldays=0):
    next_time = datetime.now() + timedelta(days=totaldays)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00")   

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

# STAGE 3 
@cron_only
def rp_google_monthly_connect(request): 
    try: 
        global MAX_TRACKS
        
        ga_queue_count = GA_monthly_monitor.objects.filter(track_status="inprogress").count() 
        if ga_queue_count > MAX_TRACKS:
            return JsonResponse({'st':0, 'message':"Server Queue was Busy"}) 

        # CHECK FOR NEW GOOGLE ANALYTICS TRACKING 
        monthlyMonitor = GA_monthly_monitor.objects.filter(track_status__in=["scheduled", "failed"], track_scheduled_start__lte=datetime.now()).values('id', 'fk_user_id', 'fk_group_id', 'track_scheduled_start').first()

        if monthlyMonitor:
            user_id = monthlyMonitor["fk_user_id"]
            group_id = monthlyMonitor["fk_group_id"]
            track_id = monthlyMonitor["id"]

            page_filter={'fk_user_id':user_id, 'fk_group_id':group_id}

            # CHECK FOR SETTINGS CONDITIONS 
            group_settings_data = GroupSetting.objects.filter(**page_filter).values("ga_refresh_token", "ga_property", "site_platform").first() 
            ga_platform = str(group_settings_data['site_platform'].lower()) if "site_platform" in group_settings_data else None 

            if ga_platform not in ["non_ecommerce", "ecommerce"]:
                GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update(
                    track_status="failed",
                    track_scheduled_start=next_month(1),
                    track_message="Error in Platform Variant"
                )
                return JsonResponse({'st':0, 'ms':"Error in Platform Variant."})

            # UPDATE THE MONTHLY MONITOR STATUS
            GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update(track_status="inprogress")

            if ga_platform == "non_ecommerce":
                # MONTHLY SCHEDULE - NON ECOMMERCE SECTION - STARTS
                
                ga_flag = rpPRA.monthly_tracker_connect(user_id, group_id, track_id)

                if ga_flag == True: 
                    message = "Last Month Tracker has updated successfully"
                    return JsonResponse({'st':1, 'ms': message}) 
                else:
                    message = "Last Month Tracker contains some issues"
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_status="failed",  
                        track_scheduled_start=next_month(1),
                        track_message=message 
                    )
                    return JsonResponse({'st':0, 'ms': message}) 
                # MONTHLY SCHEDULE - NON ECOMMERCE SECTION - CLOSES 
            
            elif ga_platform == "ecommerce": 
                # MONTHLY SCHEDULE - ECOMMERCE SECTION - STARTS
                ga_refresh_token = group_settings_data['ga_refresh_token'] if "ga_refresh_token" in group_settings_data else None
                ga_property_id = group_settings_data['ga_property'] if "ga_property" in group_settings_data else None
                
                # NO REFRESH TOKEN OR PROPERTY WAS AVAILABLE
                if not ga_refresh_token or not ga_property_id:
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="failed",  
                        track_scheduled_start=next_month(1),
                        track_message="Ecom: Error in Refresh Token or Property Retrieval"
                    ) 
                    return JsonResponse({'st':0, 'ms':"Error in Refresh Token or Property Retrieval."})

                if ga_property_id:
                    ga_property_id = ga_property_id.split('/')[-1]

                # ECOM MONTHLY SCHEDULE FOR SINGLE GROUP
                ga_flag = rpECPA.ecom_monthly_tracker_connect(user_id, group_id, track_id, ga_refresh_token, ga_property_id)   

                if ga_flag == 1:
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="scheduled",  
                        modified_date=datetime.now(),
                        track_message="Ecom: Scheduled for next month set",
                        track_scheduled_start=next_date(0)
                    ) 
                    return JsonResponse({'st':1, 'ms':"Ecom: Scheduled for next month set."})
                elif ga_flag == 2:
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="done",   
                        modified_date=datetime.now(),
                        track_scheduled_start=next_month(1),
                        track_message="Ecom: Monthly Tracker has updated successfully"
                    ) 
                    return JsonResponse({'st':1, 'ms':"Ecom Yearly - Week Tracker has updated successfully."}) 
                elif ga_flag == -1:
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="done",   
                        modified_date=datetime.now(),
                        track_scheduled_start=next_month(1),
                        track_message="Ecom: No Monthly Tracker was exist"
                    ) 
                    return JsonResponse({'st':1, 'ms':"Ecom: No Monthly Tracker was exist."})  
                else:
                    GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="failed",   
                        modified_date=datetime.now(),
                        track_scheduled_start=next_month(1),
                        track_message="Ecom: Month Tracker has failed." 
                    ) 
                    return JsonResponse({'st':0, 'ms':"Ecom Month Tracker has failed."})  
                # MONTHLY SCHEDULE - ECOMMERCE SECTION - CLOSES 
            else:
                pass
        else:
            return JsonResponse({'st':0, 'ms':"No Yearly - Monthly GA Tracker are scheduled in Queue."})     

    except Exception as e:
        return JsonResponse({"st":0, "ms":"Yearly - Monthly GA Tracker - Exceptional Warning, Try again later.", "err": str(e)}) 

    return JsonResponse({'st':0, 'message':'Something went wrong'}) 

# STAGE 2
@cron_only
def rp_google_weekly_connect(request): 
    try:
        global MAX_TRACKS
        
        ga_queue_count = GA_weekly_monitor.objects.filter(track_status="inprogress").count() 
        if ga_queue_count > MAX_TRACKS:
            return JsonResponse({'st':0, 'message':"Server Queue was Busy"}) 

        # CHECK FOR NEW GOOGLE ANALYTICS TRACKING
        weeklyMonitor = GA_weekly_monitor.objects.filter(track_status__in=["scheduled", "failed"], track_scheduled_start__lte=datetime.now()).values('id', 'fk_user_id', 'fk_group_id', 'track_scheduled_start').first()

        if weeklyMonitor:
            user_id = weeklyMonitor["fk_user_id"]
            group_id = weeklyMonitor["fk_group_id"]
            track_id = weeklyMonitor["id"]

            page_filter={'fk_user_id':user_id, 'fk_group_id':group_id}   

            # CHECK FOR SETTINGS CONDITIONS 
            group_settings_data = GroupSetting.objects.filter(**page_filter).values("ga_refresh_token", "ga_property", "site_platform", "week_track_day").first()
            ga_platform = str(group_settings_data['site_platform'].lower()) if "site_platform" in group_settings_data else None 

            if ga_platform not in ["non_ecommerce", "ecommerce"]:
                GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(
                    track_status="failed",
                    track_scheduled_start=next_date(1),
                    track_message="Error in Platform Variant"
                )
                return JsonResponse({'st':0, 'ms':"Error in Platform Variant."}) 

            # UPDATE THE WEEKLY MONITOR STATUS
            GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(track_status="inprogress") 

            if ga_platform == "non_ecommerce":
                # WEEKLY SCHEDULE - NON ECOMMERCE SECTION - STARTS

                ga_flag = rpPRA.weekly_tracker_connect(user_id, group_id, track_id)

                if ga_flag == True:
                    message = "Last Week Tracker has updated successfully"
                    return JsonResponse({'st':1, 'ms': message}) 
                else:
                    message = "Last Week Tracker contains some issues"
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_status="failed",  
                        track_scheduled_start=next_date(1),
                        track_message=message 
                    )
                    return JsonResponse({'st':0, 'ms': message}) 
                # WEEKLY SCHEDULE - NON ECOMMERCE SECTION - CLOSES 
            
            elif ga_platform == "ecommerce":
                # WEEKLY SCHEDULE - ECOMMERCE SECTION - STARTS
                ga_refresh_token = group_settings_data['ga_refresh_token'] if "ga_refresh_token" in group_settings_data else None
                ga_property_id = group_settings_data['ga_property'] if "ga_property" in group_settings_data else None
                ga_track_day = str(group_settings_data['week_track_day'].lower()) if "week_track_day" in group_settings_data else None
                
                # NO REFRESH TOKEN OR PROPERTY WAS AVAILABLE
                if not ga_refresh_token or not ga_property_id:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="failed",  
                        track_scheduled_start=next_date(1),
                        track_message="Ecom: Error in Refresh Token or Property Retrieval"
                    ) 
                    return JsonResponse({'st':0, 'ms':"Error in Refresh Token or Property Retrieval."})

                # NO WEEK DAY WAS AVAILABLE
                if ga_track_day not in ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="failed",  
                        track_scheduled_start=next_date(1),
                        track_message="Ecom: Error in Track Day or Week Day Retrieval"
                    ) 
                    return JsonResponse({'st':0, 'ms':"Error in Track Day or Week Day Retrieval."}) 

                if ga_property_id:
                    ga_property_id = ga_property_id.split('/')[-1]  

                # ECOM WEEKLY SCHEDULE FOR SINGLE GROUP
                ga_flag = rpECPA.ecom_weekly_tracker_connect(user_id, group_id, track_id, ga_refresh_token, ga_property_id, ga_track_day)  

                if ga_flag == 1:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_status="scheduled", 
                        modified_date=datetime.now(),
                        track_message="Ecom: Scheduled for next week set",
                        track_scheduled_start=next_date(0)
                    )
                    return JsonResponse({'st':1, 'ms':"Ecom: Scheduled for next week set."}) 
                elif ga_flag == 2:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="done",   
                        track_scheduled_start=next_date(1),
                        track_message="Ecom: Weekly Tracker has updated successfully"
                    ) 
                    return JsonResponse({'st':1, 'ms':"Ecom Yearly - Week Tracker has updated successfully."}) 
                elif ga_flag == -1:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update( 
                        track_status="done",   
                        track_scheduled_start=next_date(1),
                        track_message="Ecom: No Weekly Tracker was exist"
                    ) 
                    return JsonResponse({'st':1, 'ms':"Ecom: No Weekly Tracker was exist."}) 
                else:
                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_status="failed", 
                        modified_date=datetime.now(),
                        track_message="Ecom Weekly Tracker has failed", 
                        track_scheduled_start=next_date(1)
                    )
                    return JsonResponse({'st':0, 'ms':"Ecom Yearly - Week Tracker has failed."})  
                # WEEKLY SCHEDULE - ECOMMERCE SECTION - CLOSES 
            else:
                pass 
        else:
            return JsonResponse({'st':0, 'ms':"No Yearly - Weekly GA Tracker are scheduled in Queue."}) 

    except Exception as e:
        return JsonResponse({"st":0, "ms":"Yearly - Weekly GA Tracker - Exceptional Warning, Try again later.", "err": str(e)}) 

    return JsonResponse({'st':0, 'message':'Something went wrong'})

# STAGE 1
@cron_only
def rp_google_analytics_connect(request): 
    try:
        
        global MAX_TRACKS 

        ga_queue_count = GA_daily_monitor.objects.filter(track_status="busy").count()
        if ga_queue_count > MAX_TRACKS:
            return JsonResponse({'st':0, 'message':"Server Queue was Busy"}) 

        # CHECK FOR NEW GOOGLE ANALYTICS TRACKING 
        dailyMonitor = GA_daily_monitor.objects.filter(track_status__in=["start", "fail"], track_scheduled_start__lte=datetime.now()).values('id', 'fk_user_id', 'fk_group_id', 'track_mode', 'track_scheduled_start').order_by("-created_date").first()
        
        if dailyMonitor:
            user_id = dailyMonitor["fk_user_id"]
            group_id = dailyMonitor["fk_group_id"]
            daily_id = dailyMonitor["id"]
            ga_track_mode = str(dailyMonitor["track_mode"].lower())

            page_filter={'fk_user_id':user_id, 'fk_group_id':group_id}  

            # CHECK FOR SETTINGS CONDITIONS 
            group_settings_data = GroupSetting.objects.filter(**page_filter).values("ga_refresh_token", "ga_property", "site_platform").first()

            ga_refresh_token = group_settings_data['ga_refresh_token'] if "ga_refresh_token" in group_settings_data else None
            ga_property_id = group_settings_data['ga_property'] if "ga_property" in group_settings_data else None
            ga_platform = str(group_settings_data['site_platform'].lower()) if "site_platform" in group_settings_data else None 
            
            if not ga_refresh_token or not ga_property_id:
                GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update( 
                    track_status="fail",  
                    track_scheduled_start=next_date(1),
                    track_message="Error in Refresh Token or Property Retrieval"
                ) 
                return JsonResponse({'st':0, 'ms':"Error in Refresh Token or Property Retrieval."})

            ga_access_token = retrieve_access_token(ga_refresh_token)
            if not ga_access_token:
                GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                    track_status="fail",
                    track_scheduled_start=next_date(1),
                    track_message="Error in Access Token Retrieval"
                )
                return JsonResponse({'st':0, 'ms':"Error in Access Token Retrieval."})  

            if ga_platform not in ["non_ecommerce", "ecommerce"]:
                GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                    track_status="fail",
                    track_scheduled_start=next_date(1),
                    track_message="Error in Platform Variant"
                )
                return JsonResponse({'st':0, 'ms':"Error in Platform Variant."})  

            if ga_property_id:
                ga_property_id = ga_property_id.split('/')[-1] 

            # CHECK FOR BUSY CONDITIONS
            GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(track_status="busy") 
            ga_flag = ""

            if ga_platform == "non_ecommerce":
                # NON ECOMMERCE SECTION - STARTS
                if ga_track_mode == "yearly":
                    ga_flag = rpPA.year_to_daily_tracker(ga_access_token, user_id, group_id, ga_property_id, daily_id) 

                elif ga_track_mode == "weekly":
                    ga_flag = rpPA.year_to_weekly_tracker(user_id, group_id, daily_id) 

                elif ga_track_mode == "monthly":
                    ga_flag = rpPA.year_to_monthly_tracker(user_id, group_id, daily_id)  

                elif ga_track_mode == "daily":
                    ga_flag = rpPRA.every_day_tracker(ga_access_token, user_id, group_id, ga_property_id, daily_id) 

                else: 
                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_mode="daily",
                        track_status="start", 
                        track_scheduled_start=next_date(1),
                        track_message="Rescheduled the daily update"
                    )
                if ga_flag == True:
                    message = "Non Ecommerce Report " + ga_track_mode + " data has updated successfully"
                    return JsonResponse({'st':1, 'ms': message}) 
                # NON ECOMMERCE SECTION - CLOSES

            elif ga_platform == "ecommerce":
                # ECOMMERCE SECTION - STARTS
                if ga_track_mode == "yearly":
                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_mode="weekly", 
                        track_status="start", 
                        track_scheduled_start=next_date(0),  
                        track_message="Ecom: Scheduled the Yearly - Weekly Tracker" 
                    )
                
                elif ga_track_mode == "weekly":
                    ga_flag = rpECPA.ecom_weekly_blank_tracker(user_id, group_id, daily_id) 
                
                elif ga_track_mode == "monthly":
                    ga_flag = rpECPA.ecom_monthly_blank_tracker(user_id, group_id, daily_id) 
                
                elif ga_track_mode == "daily":
                    ga_flag = rpEPRA.ecom_past_months_tracker(user_id, group_id)
                    ga_flag = rpEPRA.ecom_past_weeks_tracker(user_id, group_id)

                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_status="start", 
                        track_scheduled_start=next_date(1),
                        track_message="Updated to tomorrow schedule"
                    )
                else:
                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_mode="daily",
                        track_status="start", 
                        track_scheduled_start=next_date(1),
                        track_message="Rescheduled the daily update"
                    )

                if ga_flag == True:
                    message = "Ecommerce Report " + ga_track_mode + " data has updated successfully" 
                    return JsonResponse({'st':1, 'ms': message})  
                # ECOMMERCE SECTION - CLOSES   
            else:
                GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                    track_status="fail",
                    track_scheduled_start=next_date(1), 
                    track_message="Unknown Report Platform" 
                )
                return JsonResponse({'st':0, 'ms':"Unknown Report Platform."}) 

        else:
            return JsonResponse({'st':0, 'ms':"No GA Tracker are scheduled in Queue."}) 

    except Exception as e: 
        return JsonResponse({"st":0, "ms":"Google Analytics Exceptional Warning, Try again later.", "err": str(e)}) 

    return JsonResponse({'st':0, 'message':'Something went wrong'})