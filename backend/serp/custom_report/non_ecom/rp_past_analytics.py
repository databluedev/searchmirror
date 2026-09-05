from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from account.models import Account  
from serp.models import *
from serp.common import *
from account import verify as authPermission
from serp.custom_serializer.ganalytics_serializers import *

import requests, json, os, string, random 
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 

###################### GENERAL TRACKER FUNCTION - STARTS ###################### 
def next_date(totaldays): 
    next_time = datetime.now() + timedelta(days=totaldays)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00") 


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # If the day is past the specified weekday, jump to the next week
        days_ahead += 7
    return d + timedelta(days=days_ahead)


def day_check(track_day):
    target_weekday = 0
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] 

    if track_day in weekdays:
        target_weekday = weekdays.index(track_day)

    on_date = datetime.now() - timedelta(days=365)    
    week_day_analyse = next_weekday(on_date, target_weekday)
    return week_day_analyse


def collect_each_week_data(start_day_of_week):
    weeks_list = []
    if start_day_of_week:
        while start_day_of_week < datetime.now(): 
            end_day_of_week = start_day_of_week + timedelta(days=6)
            if end_day_of_week < datetime.now(): 
                weeks_list.append({'sd':start_day_of_week, 'ed': end_day_of_week}) 
            start_day_of_week += timedelta(weeks=1) 
            
    return weeks_list  


def get_month_start_end(date):
    first_day = date.replace(day=1)
    next_month = first_day + relativedelta(months=1)
    last_day = next_month - timedelta(days=1)
    return first_day, last_day


def collect_each_month_data():
    month_list = []
    end_date = datetime.now()
    current_date = end_date - relativedelta(years=1)

    while current_date < end_date: 
        month_start, month_end = get_month_start_end(current_date)
        month_list.append({'sd':month_start, 'ed': month_end})  
        current_date += relativedelta(months=1)
    return month_list

###################### GENERAL TRACKER FUNCTION - ENDS ######################
#
#
#
###################### STAGE 1: SESSIONS TRACKER & MANAGER - STARTS ######################
def collect_sessions(token, sdate, edate, prop, user_id, grp_id):
    try:
        message = ""
        data_dict = {} 
        page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 

        if token: 
            landing_page_analytics_params = {
                "dateRanges":[{"startDate":sdate,"endDate":edate}],
                "dimensions":[{"name":"landingPage"}, {"name":"date"}],  
                "metrics":[{"name":"sessions"}],
                'orderBys': [{'dimension': {'dimensionName': 'date'}, "desc": False}], 
                'limit': 250000
            } 

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 
            
            if 'error' in resp:
                message = "Stage 1 - Collect Sessions - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    organic_date = row['dimensionValues'][1]['value']
                    landing_page = row['dimensionValues'][0]['value']
                    sessions = int(row['metricValues'][0]['value'])
                    
                    if organic_date not in data_dict:
                        data_dict[organic_date] = []
                    
                    data_dict[organic_date].append({"value": landing_page, "session": sessions}) 
            
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_sessions/ga_yearly_sessions_'+str(grp_id)+'.json'
                with open(filePath, 'w') as f: 
                    json.dump(data_dict, f, indent=4) 
        else:
           message = "Stage 1 - Collect Sessions Token not available"

    except Exception as e: 
        message = "Stage 1 - Collect Sessions Exceptional Error: " + str(e)
    
    if len(message):
        GA_daily_monitor.objects.filter(**page_filter).update(
            track_status="fail", 
            track_scheduled_start=next_date(1),
            track_message=message
        )

    return data_dict
###################### STAGE 1: SESSIONS TRACKER & MANAGER - ENDS ######################
#
#
#
###################### STAGE 1: ORGANIC TRACKER & MANAGER - STARTS ######################
def collect_organic_overview(token, sdate, edate, prop, user_id, grp_id):
    try:
        message = ""
        data_dict = {}
        page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}  

        if token: 
            landing_page_analytics_params = {
                "dateRanges":[{"startDate":sdate,"endDate":edate}],
                "dimensions":[{"name":"sessionDefaultChannelGroup"}, {'name':'date'}], 
                "metrics":[{"name":"sessions"}],
                'orderBys': [{'dimension': {'dimensionName': 'date'}, "desc": False}], 
                'limit': 250000
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"} 
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json()

            if 'error' in resp:
                message = "Stage 1 - Collect Organic - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    organic_date = row['dimensionValues'][1]['value']
                    organic_type = row['dimensionValues'][0]['value']
                    organic_value = int(row['metricValues'][0]['value'])
                    
                    if organic_date not in data_dict:
                        data_dict[organic_date] = []
                    
                    data_dict[organic_date].append({"value": organic_type, "session": organic_value}) 
                
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_organic/ga_yearly_overview_'+str(grp_id)+'.json' 
                with open(filePath, 'w') as f: 
                    json.dump(data_dict, f, indent=4)
        else:
            message = "Stage 1 - Collect Overview Token not available"
    
    except Exception as e:
        message = "Stage 1 - Collect Overview Exceptional Error: " + str(e)

    if len(message):
        GA_daily_monitor.objects.filter(**page_filter).update(
            track_status="fail", 
            track_scheduled_start=next_date(1),
            track_message=message
        ) 

    return data_dict

###################### STAGE 1: ORGANIC TRACKER & MANAGER - ENDS ######################
#
#
#
###################### STAGE 1: YEARLY TO DAILY TRACKER - STARTS ######################
def year_to_daily_tracker(access_token, user_id, grp_id, prop, track_id): 
    try:
        message = ""
        if access_token and user_id and grp_id and prop and track_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 
            on_date = datetime.now()-timedelta(days=365)
            to_date = datetime.now()-timedelta(days=1)

            start_date = datetime.strftime(on_date, "%Y-%m-%d")
            end_date = datetime.strftime(to_date, "%Y-%m-%d") 

            ga4_sessions = collect_sessions(access_token, start_date, end_date, prop, user_id, grp_id)
            ga4_overview = collect_organic_overview(access_token, start_date, end_date, prop, user_id, grp_id)  

            if ga4_sessions or ga4_overview: 
                serializer = AnalyticsYearlyMetricsSerializer(ga4_sessions.keys(), many=True, context={"ga_sessions": ga4_sessions, "ga_overview": ga4_overview, "userid": user_id, "grpid": grp_id })
                ga4_serial_data = serializer.data

                if len(ga4_serial_data):
                    GA_daily_reports.objects.bulk_create(ga4_serial_data)

                    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_mode="weekly",
                        track_status="start", 
                        track_scheduled_start=next_date(0),
                        track_message="Completed the Yearly - Weekly Tracker"
                    )
                return True
            else:
                message = "Yearly - Daily Error: No Sessions or Overview"
                return False 
        else:
            message = "Yearly - Daily Error: Data not accessible"

    except Exception as e:
        message = "Yearly - Daily Exceptional Error: " + str(e)
    
    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
        track_status="start", 
        track_scheduled_start=next_date(1),
        track_message=message
    )

    return False
###################### STAGE 1: YEARLY TO DAILY TRACKER - ENDS ######################
#
#
#
###################### STAGE 2 & 3: YEARLY TO WEEKLY COLLECT DAILY DATA AND MANAGE - STARTS ######################
def collect_daily(user_id, grp_id):
    data_pages_dict = {}
    data_organic_dict = {}

    if user_id and grp_id:
        daily_data = GA_daily_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).values('start_date', 'landing_page', 'overview').all()

        if daily_data:
            for single_data in daily_data:
                organic_date = single_data['start_date'].strftime('%Y-%m-%d')
                
                if organic_date not in data_pages_dict:
                    data_pages_dict[organic_date] = []

                if organic_date not in data_organic_dict:
                    data_organic_dict[organic_date] = []

                data_pages_dict[organic_date] = list(single_data['landing_page'])
                data_organic_dict[organic_date] = single_data['overview']

    return data_pages_dict, data_organic_dict

###################### STAGE 2: YEARLY TO WEEKLY COLLECT DAILY DATA AND MANAGE - ENDS ######################
#
#
#
###################### STAGE 2: YEARLY TO WEEKLY TRACKER - STARTS ######################
def year_to_weekly_tracker(user_id, grp_id, track_id):
    try:
        message = ""
        if user_id and grp_id and track_id:
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}  
            daily_count = GA_weekly_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).count()

            if daily_count:
                GA_weekly_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).delete()

            pages_dict, organic_dict = collect_daily(user_id, grp_id)
            
            if pages_dict or organic_dict:
                weeks_list = []
                groupSetData = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).values('week_track_day', 'ga_property', 'ga_refresh_token').first()

                if 'week_track_day' in groupSetData:
                    track_day = groupSetData["week_track_day"].lower()
                    track_date = day_check(track_day)
                    weeks_list = collect_each_week_data(track_date)

                if weeks_list:
                    serializer = YearlyToWeeklyMetricsSerializer(weeks_list, many=True, context={"pages_dict": pages_dict, "organic_dict": organic_dict, "userid": user_id, "grpid": grp_id, 'prop':groupSetData['ga_property'], 'ref_token':groupSetData['ga_refresh_token'] }) 
                    ga4_serial_data = serializer.data 

                    if len(ga4_serial_data):
                        GA_weekly_reports.objects.bulk_create(ga4_serial_data) 
                        
                        GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
                            track_mode="monthly",
                            track_status="start", 
                            track_scheduled_start=next_date(0),
                            track_message="Completed the Yearly - Weekly Tracker"
                        )
                    return True
            else:
                message = "Yearly - Weekly Error: No Session Pages or Organic Overview"
        else:
            message = "Yearly - Weekly Error: Data not accessible"

    except Exception as e:
        message = "Yearly - Weekly Exceptional Error: " + str(e)
        
    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
        track_status="start", 
        track_scheduled_start=next_date(1),
        track_message=message
    )
    return False
###################### STAGE 2: YEARLY TO WEEKLY TRACKER - ENDS ######################
#
#
#
###################### STAGE 3: YEARLY TO MONTHLY TRACKER - STARTS ###################### 
def year_to_monthly_tracker(user_id, grp_id, track_id):
    try:
        message = ""
        if user_id and grp_id and track_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 

            daily_count = GA_monthly_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).count()
            if daily_count:
                GA_monthly_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).delete()

            pages_dict, organic_dict = collect_daily(user_id, grp_id)
            
            if pages_dict or organic_dict:
                groupSetData = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).values('ga_refresh_token', 'ga_property').first()
                months_list = collect_each_month_data() 
                
                if months_list:
                    serializer = YearlyToMonthlyMetricsSerializer(months_list, many=True, context={"pages_dict": pages_dict, "organic_dict": organic_dict, "userid": user_id, "grpid": grp_id, 'prop':groupSetData['ga_property'], 'ref_token':groupSetData['ga_refresh_token']  })
                    ga4_serial_data = serializer.data  

                    if len(ga4_serial_data):
                        GA_monthly_reports.objects.bulk_create(ga4_serial_data) 

                        GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
                            track_mode="daily",
                            track_status="start", 
                            track_scheduled_start=next_date(1),
                            track_message="Completed the Yearly - Monthly Tracker"
                        )
                    return True
            else:
                message = "Yearly - Monthly Error: No Session Pages or Organic Overview"
        else:
            message = "Yearly - Monthly Error: Data not accessible"     

    except Exception as e:
        message = "Yearly - Monthly Exceptional Error: " + str(e) 

    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
        track_status="start", 
        track_scheduled_start=next_date(1),
        track_message=message
    )

    return False 
###################### STAGE 3: YEARLY TO MONTHLY TRACKER - ENDS ###################### 