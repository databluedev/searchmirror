from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.conf import settings
from serp.models import *
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import quote
import concurrent.futures
from django.db.models import Q
import requests
import calendar
from account.cron_auth import cron_only
MAX_TRACKS = 10

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
    
def format_date_string(date_str):

    # Convert the input string to a datetime object
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")

    # Format the datetime object as "14 Mar 24"
    formatted_date = date.strftime("%Y-%m-%d")

    return str(formatted_date)

def next_month_to_isodate(iso_date_string, months):
    # Convert ISO date string to datetime object
    date_obj = datetime.fromisoformat(iso_date_string)

    # Add days to the date
    new_date = date_obj + relativedelta(months=months)

    # Convert the new date back to ISO format and return
    return new_date.isoformat()

def get_start_of_month(iso_date_str):
    # Parse ISO date string to datetime object
    date_obj = datetime.fromisoformat(iso_date_str)

    # Get start of the day (00:00:00)
    start_of_month = date_obj.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Format start and end of the day in the desired format
    start_of_month_str = start_of_month.strftime("%Y-%m-%d %H:%M:%S.%f")

    return start_of_month_str

def get_end_of_month(iso_date_str):

    # Parse ISO date string to datetime object
    date_obj = datetime.fromisoformat(iso_date_str)

    # Get the number of days in the month
    _, num_days = calendar.monthrange(date_obj.year, date_obj.month)

    # Get end of the month
    end_of_month = date_obj.replace(day=num_days, hour=23, minute=59, second=59, microsecond=999999)

    # Format end of the month as desired
    end_of_month_str = end_of_month.strftime("%Y-%m-%d %H:%M:%S.%f")

    return end_of_month_str

def ga_console(track_data):
    try:
        if hasattr(track_data, "id") and hasattr(track_data, "fk_user_id") and hasattr(track_data, "fk_group_id"):
            project_data = GroupSetting.objects.filter(Q(fk_group_id=track_data.fk_group_id, fk_user_id=track_data.fk_user_id)).first()
            ga_refresh_token = project_data.ga_refresh_token if hasattr(project_data, "ga_refresh_token") else None
            ga_property_id = project_data.ga_property if hasattr(project_data, "ga_property") else None
            print('1')
            if not ga_refresh_token or not ga_property_id:
                GA_monthly_monitor.objects.filter(Q(id=track_data.id)).update(track_status="failed", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))
                return
            
            ga_access_token = retriev_access_token(ga_refresh_token)
            print('1')
            if not ga_access_token:
                GA_monthly_monitor.objects.filter(Q(id=track_data.id)).update(track_status="failed", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))
                return
            
            headers = {"Authorization": "Bearer " + ga_access_token, "Content-Type": "application/json"}
            prop = ga_property_id[11:]
            api_endpoint = api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            print('1')
            start_of_day = get_start_of_month(str(track_data.track_scheduled_start))
            end_of_day = get_end_of_month(str(track_data.track_scheduled_start))
            print('1')
            week_ago = format_date_string(str(start_of_day))
            day_ago = format_date_string(str(end_of_day))
            print('1')
            monthly_overview_params = {
                "dateRanges":[{"startDate":week_ago,"endDate":day_ago}],
                "dimensions":[{"name":"sessionDefaultChannelGroup"}],
                "metrics":[{"name":"sessions"}]
            }
            ov_response = requests.post(api_endpoint, headers=headers, json=monthly_overview_params)
            if ov_response.status_code!=200:
                GA_weekly_monitor.objects.filter(id=track_data.id).update(track_status="failed", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))

            ov_transformed_data=[]
            if 'rows' in ov_response.json():
                rows = ov_response.json()['rows']
                for item in rows:
                    source = item['dimensionValues'][0]['value']
                    session = int(item['metricValues'][0]['value'])  
                    ov_transformed_data.append({'value': source, 'session': session})

            GA_monthly_reports.objects.create(
                fk_user_id=track_data.fk_user_id,
                fk_group_id=track_data.fk_group_id,
                start_date=get_start_of_month(str(track_data.track_scheduled_start)),
                end_date=get_end_of_month(str(track_data.track_scheduled_start)),
                overview = ov_transformed_data
            )
            GA_monthly_monitor.objects.filter(id=track_data.id).update(track_status="done", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))
            
        else:
            GA_monthly_monitor.objects.filter(id=track_data.id).update(track_status="failed", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))

    except Exception as e:
        print(e)
        GA_monthly_monitor.objects.filter(Q(id=track_data.id)).update(track_status="failed", track_scheduled_start=next_month_to_isodate(str(track_data.track_scheduled_start), 1))

def gsc_pool(ga_tracks):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_TRACKS) as taskExecutor:
            taskExecutorResult = taskExecutor.map(ga_console, ga_tracks)
            taskExecutor.shutdown(wait=False)
        return 1
    except Exception as e:
        return 0
    
# @api_view(['POST'])
@cron_only
def ga_monthly_monitor(request):
    try:
        inprogress_ga_tracking_count = GA_monthly_monitor.objects.filter(track_status="inprogress").count()
        
        if inprogress_ga_tracking_count >= MAX_TRACKS:
            return JsonResponse({"status": "true", "message": "Track Queue Filled!"})
        
        scheduled_ga_trackings = GA_monthly_monitor.objects.filter(track_status="scheduled").all().order_by("-id")[0 : MAX_TRACKS - inprogress_ga_tracking_count]

        if not scheduled_ga_trackings:
            return JsonResponse({"status": "true", "message": "No Tracks are scheduled yet"})
        
        scheduled_tracks = []

        for each_track in scheduled_ga_trackings:
            scheduled_tracks.append(each_track.id)

        GA_monthly_monitor.objects.filter(id__in=scheduled_tracks).update(track_status="inprogress")

        gsc_pool(scheduled_ga_trackings)

        return JsonResponse({"status": "true", "message": "Tracking has been completed"})
    
    except Exception as e:
        return JsonResponse({"message": "Something went wrong"})
    
def get_start_of_current_date():

    # Get the current date
    current_date = datetime.now().date()

    # Get the first day of the month
    start_of_month = current_date.replace(day=1)

    return start_of_month.isoformat()

# @api_view(['POST'])
@cron_only
def ga_monthly_rescheduler(request):
    try:
        rescheduled_tracks = list()

        tracks_scheduled_before_one_week = GA_monthly_monitor.objects.filter(track_scheduled_start__lt=get_start_of_current_date(), track_status__in=["failed", "done"]).all()[0:20]

        if tracks_scheduled_before_one_week:
            for each_track_scheduled in tracks_scheduled_before_one_week:
                rescheduled_tracks.append(each_track_scheduled.id)

            GA_monthly_monitor.objects.filter(id__in=rescheduled_tracks, track_status__in=["failed", "done"]).update(track_status="scheduled")

            return JsonResponse({"message": "All Trackings has been rescheduled"})
        else:
            return JsonResponse({"message": "No tracks to scheduled"})
    except Exception as e:
        return JsonResponse({"message": "Something went wrong"})
