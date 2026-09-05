import os
from rest_framework.decorators import api_view
import requests
from django.conf import settings
from serp.models import *
from django.http import HttpResponse, JsonResponse
from datetime import *
import concurrent.futures
from serp.common import last_of_day
from account.cron_auth import cron_only

MAX_TRACKS = 10
# GSC POOL
def gsc_pool(ga_tracks):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_TRACKS) as taskExecutor:
            taskExecutorResult = taskExecutor.map(ga_console, ga_tracks)
            taskExecutor.shutdown(wait=False)
        return 1
    except Exception as e:
        return 0

def retriev_access_token(refreshToken):
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
    
def get_start_and_end_of_week(iso_date_str):

    weekday = iso_date_str.isoweekday()

    start_date = iso_date_str - timedelta(days=weekday)

    end_date = start_date + timedelta(days=6) 

    st_date = datetime.strftime(start_date, "%Y-%m-%d")
    en_date = datetime.strftime(end_date, "%Y-%m-%d")   

    return st_date, en_date

def get_start_of_week(iso_date_str):

    # Parse ISO date string to datetime object
    date_obj = datetime.strptime(iso_date_str, "%Y-%m-%d %H:%M:%S.%f%z")

    # Calculate the number of days to subtract to get to the start of the week
    days_to_subtract = (date_obj.isoweekday()) % 7

    # Subtract the days to get the start date of the week
    week_start_date = date_obj - timedelta(days=days_to_subtract)

    return week_start_date

def get_end_of_week(iso_date):

    # Parse ISO date string to datetime object
    date_obj = datetime.strptime(iso_date, "%Y-%m-%d %H:%M:%S.%f%z")

    # Calculate the number of days to add to get to the end of the week (Sunday)
    days_to_add = 6 - ((date_obj.isoweekday()) % 7)

    # Add the days to get the end date of the week
    week_end_date = date_obj + timedelta(days=days_to_add)

    return week_end_date
    
def next_date_to_isodate(iso_date_string, days):
    # Convert ISO date string to datetime object
    date_obj = datetime.fromisoformat(iso_date_string)

    # Add days to the date
    new_date = date_obj + timedelta(days=days)

    # Convert the new date back to ISO format and return
    return new_date.isoformat()

# DATE BEFORE
def before_date_to_isodate(iso_date_string, days):

    # Convert ISO date string to datetime object
    date_obj = datetime.fromisoformat(iso_date_string)

    # Add days to the date
    new_date = date_obj - timedelta(days=days)

    # Convert the new date back to ISO format and return
    return new_date
    
def ga_console(trackings):
    try:
        print('ga_console')
        if hasattr(trackings, "id") and hasattr(trackings, "fk_user_id") and hasattr(trackings, "fk_group_id"):
            grp_sttngs = GroupSetting.objects.filter(fk_user_id=trackings.fk_user_id, fk_group_id=trackings.fk_group_id).first()
            ga_refresh_token = grp_sttngs.ga_refresh_token if hasattr(grp_sttngs, "ga_refresh_token") else None
            ga_property_id = grp_sttngs.ga_property if hasattr(grp_sttngs, "ga_property") else None
            
            if not ga_refresh_token or not ga_property_id:
                GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="failed", track_scheduled_start=last_of_day(datetime.now()))

            ga_access_token = retriev_access_token(ga_refresh_token)
            
            if not ga_access_token:
                GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="failed", track_scheduled_start=last_of_day(datetime.now()))

            headers = {"Authorization": "Bearer " + ga_access_token, "Content-Type": "application/json"}
            prop = ga_property_id[11:]
            api_endpoint = api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            # start_of_week = before_date_to_isodate(str(trackings.track_scheduled_start), 7)
            # end_of_week = (trackings.track_scheduled_start)-timedelta(days=1)
            start_date = "yesterday"
            end_date = "yesterday"
            landing_page_analytics_params = {
                "dateRanges":[{"startDate":start_date,"endDate":end_date}],
                "dimensions":[{"name":"landingPage"}],
                "metrics":[{"name":"sessions"}]
            }
            
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            if response.status_code != 200:
                GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="failed", track_scheduled_start=last_of_day(datetime.now()))
            
            search_analytics_result = response.json()
            ln_transformed_data=[]
            if 'rows' in search_analytics_result:
                rows = search_analytics_result['rows']
                for item in rows:
                    source = item['dimensionValues'][0]['value']
                    session = int(item['metricValues'][0]['value'])  
                    ln_transformed_data.append({'value': source, 'session': session})
            
            overview_analytics_params = {
                "dateRanges":[{"startDate":start_date,"endDate":end_date}],
                "dimensions":[{"name":"sessionDefaultChannelGroup"}],
                "metrics":[{"name":"sessions"}]
            }
            ov_response = requests.post(api_endpoint, headers=headers, json=overview_analytics_params)
            if ov_response.status_code!=200:
                GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="failed", track_scheduled_start=last_of_day(datetime.now()))
            
            ov_transformed_data=[]
            if 'rows' in ov_response.json():
                rows = ov_response.json()['rows']
                for item in rows:
                    source = item['dimensionValues'][0]['value']
                    session = int(item['metricValues'][0]['value'])  
                    ov_transformed_data.append({'value': source, 'session': session})
            
            ln_transformed_data_obj={(trackings.track_scheduled_start).strftime('%Y-%m-%d'):ln_transformed_data}
            ov_transformed_data_obj={(trackings.track_scheduled_start).strftime('%Y-%m-%d'):ov_transformed_data}
            ga_daily_reports=GA_daily_reports.objects.filter(fk_user_id=trackings.fk_user_id, fk_group_id=trackings.fk_group_id)
            if ga_daily_reports:
                pr_ln_row=ga_daily_reports.first().landing_page
                pr_ln_row.append(ln_transformed_data_obj)
                pr_ov_row=ga_daily_reports.first().overview
                pr_ov_row.append(ov_transformed_data_obj)
                ga_daily_reports.update(landing_page=pr_ln_row, overview=pr_ov_row)
            else:
                GA_daily_reports.objects.create(
                    fk_user_id=trackings.fk_user_id,
                    fk_group_id=trackings.fk_group_id,
                    landing_page=[(ln_transformed_data_obj)],
                    overview = [ov_transformed_data_obj]
                )
            GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="done", track_scheduled_start=last_of_day(datetime.now()))
        else:
            GA_daily_monitor.objects.filter(id=trackings.id).update(track_status="failed", track_scheduled_start=last_of_day(datetime.now()))
    except Exception as e:
        print(f'error{str(e)}')

# @api_view(['GET'])
@cron_only
def ga_daily_monitor(self):
    try:
        schdld_tracks=GA_daily_monitor.objects.filter(track_status="scheduled").count()
        inprogress_ga_tracking_count = GA_daily_monitor.objects.filter(track_status="inprogress").count()

        if inprogress_ga_tracking_count >= MAX_TRACKS:
            return JsonResponse({"status": "true", "dt": "Track Queue Filled!"})
        

        ga_trackings=GA_daily_monitor.objects.filter(track_status='scheduled').all().order_by("-id")[0:MAX_TRACKS-inprogress_ga_tracking_count]

        if not ga_trackings:
            return JsonResponse({"status": "true", "dt": "No tracks are scheduled"})
        
        scheduled_tracks = []

        for each_track in ga_trackings:
            scheduled_tracks.append(each_track.id)
            
        GA_daily_monitor.objects.filter(id__in=scheduled_tracks).update(track_status="inprogress")

        gsc_pool(ga_trackings)
        
        return JsonResponse({"status": "true", "message": "Tracking has been completed"})

    except Exception as e:
        print(str(e))
        return JsonResponse({'status':'false', 'dt':'Something went wrong'})
    
def get_start_of_this_week():

    # Get the current date
    current_date = datetime.now().date()

    # Calculate the number of days to subtract to get to the start of the current week
    days_to_start_of_week = (current_date.isoweekday()) % 7

    # Subtract the days to get the start date of the current week
    start_of_week = current_date - timedelta(days=days_to_start_of_week)

    return start_of_week.isoformat()

# @api_view(['GET'])
@cron_only
def ga_daily_scheduler(self):
    try:

        rescheduled_tracks = list()

        tracks_scheduled_before_one_week = GA_daily_monitor.objects.filter(track_scheduled_start__lt=datetime.now(), track_status__in=["failed", "done"]).all()[0:20]

        if tracks_scheduled_before_one_week:
            for each_track_scheduled in tracks_scheduled_before_one_week:
                rescheduled_tracks.append(each_track_scheduled.id)

            GA_daily_monitor.objects.filter(id__in=rescheduled_tracks, track_status__in=["failed", "done"]).update(track_status="scheduled")

            return JsonResponse({"message": "All Trackings has been rescheduled"})
        else:
            return JsonResponse({"message": "No tracks to scheduled"})
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Something went wrong"})

def out():
    refreshToken = os.environ.get("GA_REFRESH_TOKEN", "")

    prop = "280106824"

    access_token=retriev_access_token(refreshToken)
    start_date = '365daysAgo'
    end_date = (datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")

    landing_page_analytics_params = {
        "dateRanges":[{"startDate":'365daysAgo',"endDate":end_date}],
        "dimensions":[{"name":"sessionDefaultChannelGroup"}, {'name':'date'}],
        "metrics":[{"name":"sessions"}]
    }
    headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
    
    api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'

    response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
    return response.json()

def strtoiso(date):
    (datetime.strptime(date, "%Y%m%d")).strftime("%Y-%m-%d")

def total(data):
    last_one_year_record=list(map(lambda x:TestCollection(record_date=strtoiso(x), landing_page=data[x]), data))
    TestCollection.objects.bulk_create(last_one_year_record)