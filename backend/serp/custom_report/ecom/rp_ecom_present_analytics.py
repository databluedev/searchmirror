import requests, json, os, string, random 

from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.http import HttpResponse, JsonResponse 

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 

from serp.models import *
from serp.common import *
from account.models import Account  
from account import verify as authPermission
from serp.custom_serializer.ganalytics_serializers import *

###################### GENERAL TRACKER FUNCTION - STARTS ######################
def get_month_start_end(date=datetime.now()): 
    first_day = date.replace(day=1)
    next_month = first_day + relativedelta(months=1)
    last_day = next_month - timedelta(days=1)
    return first_day, last_day

def convert_date(date_str):
    # obj['sd'].strftime('%Y%m%d')
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    formatted_date = date_obj.strftime("%Y-%m-%dT00:00:00.000+00:00")
    return formatted_date

def collect_past_month_data(limit): 
    month_list = []
    end_date = datetime.now()
    current_date = end_date - relativedelta(months=limit)

    while current_date < end_date: 
        month_start, month_end = get_month_start_end(current_date)
        month_list.append({'sd':month_start, 'ed': month_end})  
        current_date += relativedelta(months=1)
    return month_list

def next_date(totaldays=0): 
    next_time = datetime.now() + timedelta(days=totaldays)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00") 

def next_month(totalmonth=1): 
    next_month_date = datetime.now() + relativedelta(months=totalmonth) 
    next_time = next_month_date.replace(day=3)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00")

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

def difference_from_date_to_today(past_date):
    specified_date = datetime.strptime(past_date, "%Y-%m-%dT%H:%M:%S.%f%z") 
    current_date = datetime.now(specified_date.tzinfo)
    difference = (current_date - specified_date).days
    return difference

###################### GENERAL TRACKER FUNCTION - CLOSES ######################
#
#
#
###################### STAGE 1: ECOM PAST MONTHS TRACKER - STARTS ###################### 
def ecom_past_months_tracker(user_id, group_id):
    if user_id and group_id: 
        page_filter={'fk_user_id':user_id, 'fk_group_id':group_id}  
        current_day = datetime.now().day

        if current_day > 0 and current_day < 4:
            past_months = collect_past_month_data(2) 
            flag = 0 

            for single_month in past_months:
                start_date = convert_date(single_month['sd'].strftime('%Y%m%d'))
                end_date = convert_date(single_month['ed'].strftime('%Y%m%d')) 

                month_presence = GA_monthly_reports.objects.filter(**page_filter, start_date=start_date, end_date=end_date).count()
                
                if not month_presence:
                    GA_monthly_reports.objects.create(
                        fk_user_id = user_id,
                        fk_group_id = group_id, 
                        start_date = start_date,
                        end_date = end_date,
                        landing_page = [], 
                        overview = [],
                        created_date = datetime.now(),
                        modified_date = datetime.now(),
                        overview_status = "onTrack"
                    )
                else:
                    GA_monthly_reports.objects.filter(**page_filter, start_date=start_date, end_date=end_date).update(overview_status="onTrack")

                flag += 1

            if flag:
                GA_monthly_monitor.objects.filter(**page_filter).update(
                    track_status="scheduled",  
                    track_scheduled_start=next_date(),
                    track_message="Ecom: Monthly Scheduled planned on date" 
                )
        else:
            GA_monthly_monitor.objects.filter(**page_filter).update(
                track_status="scheduled",  
                track_scheduled_start=next_month(1),
                track_message="Ecom: Scheduled to Next Month"
            )         

    return True 

###################### STAGE 1: ECOM PAST MONTHS TRACKER - CLOSES ######################
#
#
#
###################### STAGE 2: ECOM PAST WEEK TRACKER - STARTS ###################### 
def ecom_past_weeks_tracker(user_id, group_id):
    if user_id and group_id: 
        page_filter={'fk_user_id':user_id, 'fk_group_id':group_id}  
        
        groupSetData = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=group_id).values('week_track_day').first() 
        if 'week_track_day' in groupSetData:
            track_day = groupSetData["week_track_day"].lower()
            start_date, end_date = get_week_start_end(track_day) 

            start_date = convert_date(start_date.strftime('%Y%m%d'))
            end_date = convert_date(end_date.strftime('%Y%m%d'))  
            diff_date = difference_from_date_to_today(end_date)

            if diff_date >= 0 and diff_date < 4:  
                week_presence = GA_weekly_reports.objects.filter(**page_filter, start_date=start_date, end_date=end_date).count()
                
                if not week_presence: 
                    GA_weekly_reports.objects.create(
                        fk_user_id = user_id,
                        fk_group_id = group_id, 
                        start_date = start_date,
                        end_date = end_date,
                        landing_page = [], 
                        overview = [],
                        created_date = datetime.now(),
                        modified_date = datetime.now(),
                        overview_status = "onTrack"
                    )
                else:
                    GA_weekly_reports.objects.filter(**page_filter, start_date=start_date, end_date=end_date).update(overview_status="onTrack")

                GA_weekly_monitor.objects.filter(**page_filter).update(
                    track_status="scheduled",  
                    track_scheduled_start=next_date(),
                    track_message="Ecom: Weekly Scheduled planned on date"
                )
        else:
            GA_weekly_monitor.objects.filter(**page_filter).update(
                track_status="scheduled",  
                track_scheduled_start=next_date(1),
                track_message="Ecom: Weekly Day is Unavailable" 
            )

    return True

        
###################### STAGE 2: ECOM PAST WEEK TRACKER - CLOSES ###################### 