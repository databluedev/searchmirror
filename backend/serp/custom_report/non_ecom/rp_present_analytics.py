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


def next_month(totalmonth): 
    next_month_date = datetime.now() + relativedelta(months=totalmonth) 
    next_time = next_month_date.replace(day=3)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00") 


def convert_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    formatted_date = date_obj.strftime("%Y-%m-%dT00:00:00.000+00:00")
    return formatted_date


def get_month_start_end(date):
    first_date = date.replace(day=1)
    first_day = first_date - relativedelta(months=1)
    last_day = first_date - timedelta(days=1)  
    return first_day, last_day


def day_index_check(track_day="monday"):
    target_weekday = 1
    weekdays = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    if track_day in weekdays:
        target_weekday = weekdays.index(track_day)
    return target_weekday


def get_week_start_end(track_day):
    target_day = day_index_check(track_day)

    date_obj = datetime.now()
    date_day = date_obj.isoweekday() 
    if target_day <= date_day: 
        before_day = (date_day - target_day) % 7
        start_date_of_week = date_obj - timedelta(days=before_day + 7) 
        end_date_of_week = start_date_of_week + timedelta(days=6)
    else:
        future_day = 14 - (target_day - date_day)
        start_date_of_week = date_obj - timedelta(days=future_day)
        end_date_of_week = start_date_of_week + timedelta(days=6) 

    return start_date_of_week, end_date_of_week

###################### GENERAL TRACKER FUNCTION - ENDS ######################
#
#
#
###################### STAGE 4: EVERYDAY SESSIONS TRACKER & MANAGER - STARTS ######################
def collect_recent_sessions(token, sdate, edate, prop, user_id, grp_id):
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
                message = "Stage 4 - Collect Recent Sessions - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    organic_date = row['dimensionValues'][1]['value']
                    landing_page = row['dimensionValues'][0]['value']
                    sessions = int(row['metricValues'][0]['value'])
                    
                    if organic_date not in data_dict:
                        data_dict[organic_date] = []
                    
                    data_dict[organic_date].append({"value": landing_page, "session": sessions}) 
                
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_sessions/ga_daily_sessions_'+str(grp_id)+'.json' 
                with open(filePath, 'w') as f: 
                    json.dump(data_dict, f, indent=4) 
        else:
            message = "Stage 4 - Collect Recent Sessions Token not available"

    except Exception as e:
        message = "Stage 4 - Collect Recent Sessions Exceptional Error: " + str(e)

    if len(message):
        GA_daily_monitor.objects.filter(**page_filter).update(
            track_status="fail", 
            track_scheduled_start=next_date(1),
            track_message=message 
        )

    return data_dict

###################### STAGE 4: EVERYDAY SESSIONS TRACKER & MANAGER - ENDS ######################
#
#
#
###################### STAGE 4: EVERYDAY ORGANIC TRACKER & MANAGER - STARTS ######################
def collect_recent_organic_overview(token, sdate, edate, prop, user_id, grp_id):
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
                message = "Stage 4 - Collect Recent Organic - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    organic_date = row['dimensionValues'][1]['value']
                    organic_type = row['dimensionValues'][0]['value']
                    organic_value = int(row['metricValues'][0]['value'])
                    
                    if organic_date not in data_dict:
                        data_dict[organic_date] = []
                    
                    data_dict[organic_date].append({"value": organic_type, "session": organic_value}) 
                
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_organic/ga_daily_overview_'+str(grp_id)+'.json'
                with open(filePath, 'w') as f: 
                    json.dump(data_dict, f, indent=4) 
        else:
            message = "Stage 4 - Collect Recent Organic Token not available"
    
    except Exception as e:
        message = "Stage 4 - Collect Recent Organic Exceptional Error: " + str(e)

    if len(message):
        GA_daily_monitor.objects.filter(**page_filter).update(
            track_status="fail", 
            track_scheduled_start=next_date(1),
            track_message=message 
        )
        
    return data_dict

###################### STAGE 4: EVERYDAY ORGANIC TRACKER & MANAGER - ENDS ######################
#
#
#
###################### STAGE 4: EVERYDAY TRACKER - STARTS ######################
def every_day_tracker(access_token, user_id, grp_id, prop, track_id): 
    try:
        message = ""
        if access_token and user_id and grp_id and prop and track_id:
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 
            from_date = datetime.now()-timedelta(days=2)
            to_date = datetime.now()-timedelta(days=1)   

            start_date = datetime.strftime(from_date, "%Y-%m-%d")
            end_date = datetime.strftime(to_date, "%Y-%m-%d") 

            ga4_recent_sessions = collect_recent_sessions(access_token, start_date, end_date, prop, user_id, grp_id) 
            ga4_recent_overview = collect_recent_organic_overview(access_token, start_date, end_date, prop, user_id, grp_id)  

            if ga4_recent_sessions or ga4_recent_overview:
                ga_keys = list(ga4_recent_sessions.keys())
                flag = 0

                for single_key in ga_keys:                    
                    ga_session_list = ga_overview_list = list()
                    date_value = convert_date(single_key) 
                    
                    if single_key in ga4_recent_sessions:
                        ga_session_list = ga4_recent_sessions[single_key]

                    if single_key in ga4_recent_overview:
                        ga_overview_list = ga4_recent_overview[single_key]

                    day_presence = GA_daily_reports.objects.filter(**page_filter, start_date=date_value, end_date=date_value).count()
                    if not day_presence: 
                        ga_creation = GA_daily_reports.objects.create(
                            fk_user_id = user_id,
                            fk_group_id = grp_id, 
                            start_date = date_value,
                            end_date = date_value,
                            landing_page = ga_session_list, 
                            overview = ga_overview_list
                        ) 
                        flag+=1
                    else:
                        GA_daily_reports.objects.filter(**page_filter, start_date=date_value, end_date=date_value).update(
                            landing_page = ga_session_list, overview = ga_overview_list
                        ) 
                        flag+=1
                
                if flag:
                    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_mode="daily",
                        track_status="start", 
                        track_scheduled_start=next_date(1),
                        track_message="Every day tracker scheduled to tomorrow"
                    ) 

                    GA_weekly_monitor.objects.filter(**page_filter).update( 
                        track_status="scheduled",
                        track_scheduled_start=next_date(0)
                    )

                return True 
            else:
                message = "Every Day Tracker Error: No Sessions or Overview"
                return False
        else:
            message = "Every Day Tracker Error: Data not accessible"

    except Exception as e:
        message = "Every Day Tracker Exceptional Error: " + str(e)

    GA_daily_monitor.objects.filter(**page_filter, id=track_id).update(
        track_mode="daily",
        track_status="start", 
        track_scheduled_start=next_date(1),
        track_message=message 
    )

    return False

###################### STAGE 4: EVERYDAY TRACKER - ENDS ######################
#
#
#
###################### STAGE 5: LAST MONTH TRACKER COLLECT DAILY DATA AND MANAGE - STARTS ######################

def collect_last_month_records(user_id, grp_id, start_date, end_date):
    data_pages_dict = {}
    data_organic_dict = {}

    if user_id and grp_id and start_date and end_date:

        daily_data = GA_daily_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id, start_date__gte=start_date, end_date__lte=end_date).values('start_date', 'landing_page', 'overview').all() 

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

###################### STAGE 5: LAST MONTH TRACKER COLLECT DAILY DATA AND MANAGE - ENDS ######################
#
#
#
###################### STAGE 5: LAST MONTH TRACKER - STARTS - ON EVERY 5 ######################
def monthly_tracker_connect(user_id, grp_id, track_id): 
    try:
        message = "" 
        if user_id and grp_id and track_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}
            current_date = datetime.now()
            month_start, month_end = get_month_start_end(current_date)
            
            if month_start and month_end:
                from_date = convert_date(month_start.strftime('%Y%m%d')) 
                to_date = convert_date(month_end.strftime('%Y%m%d'))  
                pages_dict, organic_dict = collect_last_month_records(user_id, grp_id, from_date, to_date) 

                pages_list = [] 
                organic_list = [] 
                pages_json = organic_json = {}  

                while month_start <= month_end:
                    on_date = month_start.strftime('%Y-%m-%d') 

                    if on_date in pages_dict:
                        pages_list += pages_dict[on_date]

                    if on_date in organic_dict:
                        organic_list += organic_dict[on_date] 

                    month_start = month_start + timedelta(days=1)

                # DATA COLLECTOR AND MERGER
                if pages_list:
                    pages_counter = Counter()
                    for item in pages_list:
                        pages_counter[item["value"]] += item["session"]

                    pages_json = [{"value": key, "session": value} for key, value in pages_counter.items()] 

                if organic_list:
                    organic_counter = Counter()
                    for item in organic_list:
                        organic_counter[item["value"]] += item["session"]

                    organic_json = [{"value": key, "session": value} for key, value in organic_counter.items()]

                day_presence = GA_monthly_reports.objects.filter(**page_filter, start_date=from_date, end_date=to_date).count()
                grpSet = GroupSetting.objects.filter(**page_filter).values('ga_refresh_token' 'ga_property').first()
                ms, me = get_month_start_end(current_date)
                ov_transformed_data = retrieve_past_each_week(grpSet['ga_refresh_token'], grpSet['ga_property'], ms, me)
                if not day_presence:
                    ga_monthly_creation = GA_monthly_reports.objects.create(
                        fk_user_id = user_id,
                        fk_group_id = grp_id, 
                        start_date = from_date, 
                        end_date = to_date,
                        landing_page = ov_transformed_data,
                        overview = organic_json
                    )  
                else:
                    GA_monthly_reports.objects.filter(**page_filter, start_date=from_date, end_date=to_date).update(
                        landing_page = pages_json, overview = ov_transformed_data
                    )

                GA_monthly_monitor.objects.filter(**page_filter, id=track_id).update(
                    track_status="scheduled",  
                    track_scheduled_start=next_month(1) 
                ) 

                return True
            else:
                message = "Every Month Tracker Error: No Month Start & End Date"
        else:
            message = "Every Month Tracker Error: Data not accessible"

    except Exception as e:
        message = "Every Month Tracker Error: " + str(e) 

    return message

###################### STAGE 5: LAST MONTH TRACKER - ENDS - ON EVERY 5 ######################
#
#
#
###################### STAGE 5: LAST WEEK TRACKER COLLECT DAILY DATA AND MANAGE - STARTS ######################

def collect_last_week_records(user_id, grp_id, start_date, end_date):
    data_pages_dict = {}
    data_organic_dict = {}

    if user_id and grp_id and start_date and end_date:

        daily_data = GA_daily_reports.objects.filter(fk_user_id=user_id, fk_group_id=grp_id, start_date__gte=start_date, end_date__lte=end_date).values('start_date', 'landing_page', 'overview').all() 

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

###################### STAGE 5: LAST WEEK TRACKER COLLECT DAILY DATA AND MANAGE - ENDS ######################
#
#
#
###################### STAGE 6: LAST WEEK TRACKER - STARTS ######################
def weekly_tracker_connect(user_id, grp_id, track_id):
    try:
        message = ""
        if user_id and grp_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}
            groupSetData = GroupSetting.objects.filter(**page_filter).values('week_track_day', 'ga_refresh_token').first() 

            if 'week_track_day' in groupSetData:
                track_day = groupSetData["week_track_day"].lower()
                week_start, week_end = get_week_start_end(track_day)
                

                if week_start and week_end:
                    from_date = convert_date(week_start.strftime('%Y%m%d')) 
                    to_date = convert_date(week_end.strftime('%Y%m%d'))  
                    pages_dict, organic_dict = collect_last_week_records(user_id, grp_id, from_date, to_date) 

                    pages_list = [] 
                    organic_list = [] 
                    pages_json = organic_json = {} 

                    while week_start <= week_end:
                        on_date = week_start.strftime('%Y-%m-%d') 
                        
                        if on_date in pages_dict:
                            pages_list += pages_dict[on_date]

                        if on_date in organic_dict:
                            organic_list += organic_dict[on_date]

                        week_start = week_start + timedelta(days=1) 

                    if pages_list:
                        pages_counter = Counter()
                        for item in pages_list:
                            pages_counter[item["value"]] += item["session"]

                        pages_json = [{"value": key, "session": value} for key, value in pages_counter.items()] 

                    if organic_list:
                        organic_counter = Counter()
                        for item in organic_list:
                            organic_counter[item["value"]] += item["session"]

                        organic_json = [{"value": key, "session": value} for key, value in organic_counter.items()]  
                    day_presence = GA_weekly_reports.objects.filter(**page_filter, start_date=from_date, end_date=to_date).count()
                    ws, we = get_week_start_end(track_day)
                    ov_transformed_data = retrieve_past_each_week(groupSetData['ga_refresh_token'], groupSetData['ga_property'], ws, we)
                    if not day_presence:
                        ga_weekly_creation = GA_weekly_reports.objects.create(
                            fk_user_id = user_id,
                            fk_group_id = grp_id, 
                            start_date = from_date, 
                            end_date = to_date,
                            landing_page = pages_json,
                            overview = ov_transformed_data
                        )  
                    else:
                        GA_weekly_reports.objects.filter(**page_filter, start_date=from_date, end_date=to_date).update(
                            landing_page = pages_json, overview = ov_transformed_data
                        )

                    GA_weekly_monitor.objects.filter(**page_filter, id=track_id).update(
                        track_status="scheduled", 
                        track_scheduled_start=next_date(1)  
                    )

                    month_reschedule = datetime.now() - timedelta(days=5)   
                    GA_monthly_monitor.objects.filter(**page_filter).update(
                        track_status="scheduled",  
                        track_scheduled_start=month_reschedule  
                    ) 

                    return True

            message = "Every Week Tracker Error: No Week Start & End Date"
        else:
            message = "Every Week Tracker Error: Data not accessible"

    except Exception as e:
        message = "Every Week Tracker Error: " + str(e)

    return message 


###################### WEEKLY TRACKER CONNECT - ENDS ######################
