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

from serp.custom_report.ecom import rp_ecom_present_analytics as rpEPRA

###################### REQUESTS FUNCTION - STARTS ###################### 
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
###################### REQUESTS FUNCTION - CLOSES ###################### 

###################### GENERAL TRACKER FUNCTION - STARTS ###################### 
def next_date(totaldays=0): 
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

# MONTHS MANAGING CONDITIONS AND FACTORS
def next_month(totalmonth=1): 
    next_month_date = datetime.now() + relativedelta(months=totalmonth) 
    next_time = next_month_date.replace(day=3)
    return next_time.strftime("%Y-%m-%dT00:00:00.000+00:00")

def get_month_start(date=datetime.now()): 
    first_day = date.replace(day=1)
    return first_day

def get_month_start_end(date=datetime.now()): 
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

###################### GENERAL TRACKER FUNCTION - CLOSES ###################### 
#
#
#
###################### STAGE 1: ECOM WEEKLY BLANK TRACKER - STARTS ######################
def ecom_weekly_blank_tracker(user_id, grp_id, daily_id): 
    try:
        message = ""
        if user_id and grp_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}

            # UNLOCK LATER 
            weekly_count = GA_weekly_reports.objects.filter(**page_filter).count() 
            if weekly_count:
                GA_weekly_reports.objects.filter(**page_filter).delete()

            weeks_list = []
            groupSetData = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=grp_id).values('week_track_day').first() 
            if 'week_track_day' in groupSetData:
                track_day = groupSetData["week_track_day"].lower()
                track_date = day_check(track_day)
                weeks_list = collect_each_week_data(track_date)

            if weeks_list:
                serializer = EcomYearlyToWeeklyBlankSerializer(weeks_list, many=True, context={"userid": user_id, "grpid": grp_id}) 
                blank_serial_data = list(filter(None, serializer.data)) 

                if len(blank_serial_data):
                    GA_weekly_reports.objects.bulk_create(blank_serial_data)

                    GA_weekly_monitor.objects.filter(**page_filter).update( 
                        track_status="scheduled",
                        track_scheduled_start=next_date() 
                    ) 

                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_mode="monthly",
                        track_status="start", 
                        track_scheduled_start=next_date(), 
                        track_message="Ecom: Completed the Yearly - Weekly Tracker"
                    )

                    return True 
                
    except Exception as e:
        message = "Ecom: Yearly - Blank Weekly Exceptional Error: " + str(e) 

    if len(message): 
        GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
            track_status="fail",
            track_scheduled_start=next_date(1),
            track_message=message
        )

    return False 
###################### STAGE 1: ECOM WEEKLY BLANK TRACKER - CLOSES ######################
#
#
#
###################### STAGE 2: ECOM MONTHLY BLANK TRACKER - STARTS ######################
def ecom_monthly_blank_tracker(user_id, grp_id, daily_id):  
    try:
        message = ""
        if user_id and grp_id: 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id}

            # UNLOCK LATER - MONTHLY REMOVAL
            monthly_count = GA_monthly_reports.objects.filter(**page_filter).count() 
            if monthly_count:
                GA_monthly_reports.objects.filter(**page_filter).delete() 

            months_list = collect_each_month_data() 

            if months_list:
                serializer = EcomYearlyToMonthlyBlankSerializer(months_list, many=True, context={"userid": user_id, "grpid": grp_id}) 
                blank_serial_data = list(filter(None, serializer.data))

                if len(blank_serial_data):
                    GA_monthly_reports.objects.bulk_create(blank_serial_data)

                    GA_monthly_monitor.objects.filter(**page_filter).update(
                        track_status="scheduled",  
                        track_scheduled_start=get_month_start()
                    ) 

                    GA_daily_monitor.objects.filter(**page_filter, id=daily_id).update(
                        track_mode="daily",
                        track_status="start", 
                        track_scheduled_start=next_date(1),
                        track_message="Ecom: Completed the Yearly - Monthly Tracker" 
                    )
                    return True
                
    except Exception as e:
        message = "Ecom: Yearly - Blank Monthly Exceptional Error: " + str(e) 

    if len(message): 
        GA_daily_monitor.objects.filter(id=daily_id).update(
            track_status="fail",  
            track_scheduled_start=next_date(1),
            track_message=message
        )

    return False
###################### STAGE 2: ECOM WEEKLY BLANK TRACKER - CLOSES ######################
#
#
#
###################### STAGE 3-A: ECOM WEEKLY ORGANIC PAGES TRACKER - STARTS ######################
def collect_weekly_ecom_organic_pages(token, sdate, edate, prop, user_id, grp_id):
    try:
        message = ""
        data_dict = [] 

        if token:

            landing_page_analytics_params = {
                "dateRanges":[{"startDate":sdate,"endDate":edate}],
                "dimensions":[{"name":"landingPage"}, {"name":"sessionDefaultChannelGroup"}], 
                "metrics":[{"name":"sessions"}],
                'limit': 25000,
                "dimensionFilter": {
                    "filter": {
                        "fieldName": "sessionDefaultChannelGroup", 
                        "stringFilter": {
                            "matchType": "EXACT",
                            "value": "Organic Search"
                        } 
                    }
                }
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 
            
            if 'error' in resp:
                message = "Collect Weekly Ecom Organic Pages - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    landing_page = row['dimensionValues'][0]['value']
                    sessions = int(row['metricValues'][0]['value'])
                    
                    data_dict.append({"value": landing_page, "session": sessions}) 
            
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_sessions/ecom/ga_weekly_sessions_'+str(grp_id)+'.json'
                with open(filePath, 'w') as f: 
                    json.dump(resp, f, indent=4)
        else:
           message = "Collect Weekly Ecom Organic Pages Token not available"

    except Exception as e: 
        message = "Collect Weekly Ecom Organic Pages Exceptional Error: " + str(e)

    return data_dict, message

###################### STAGE 3-A: ECOM WEEKLY ORGANIC PAGES TRACKER - CLOSES ######################
#
#
#
###################### STAGE 3-B: ECOM WEEKLY ORGANIC PAGES SUMMARY TRACKER - STARTS ######################
def collect_weekly_ecom_organic_pages_summary(token, sdate, edate, prop, user_id, grp_id): 
    try:
        message = ""
        pages_count = 0 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}], 
                "dimensionFilter": {
                    "andGroup": {
                        "expressions": [
                            {
                                "notExpression": {
                                    "filter": {
                                        "fieldName": "landingPagePlusQueryString",
                                        "stringFilter": {
                                            "matchType": "CONTAINS",
                                            "value": "/blogs"
                                        }
                                    }
                                }
                            },
                            {
                                "filter": {
                                    "fieldName": "sessionDefaultChannelGroup", 
                                    "stringFilter": {
                                        "matchType": "EXACT",
                                        "value": "Organic Search"
                                    }
                                }
                            }
                        ]
                    }
                }                
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Weekly Ecom Organic Pages Summary - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    flag = 0
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0] and row['dimensionValues'][0]['value'] == "Organic Search":
                            flag += 1

                    if flag and 'metricValues' in row:
                        if len(row['metricValues']) and 'value' in row['metricValues'][0]:
                            pages_count += int(row['metricValues'][0]['value'])
        else:
           message = "Collect Weekly Ecom Organic Pages Summary - Token not available" 

    except Exception as e: 
        message = "Collect Weekly Ecom Organic Pages Summary Exceptional Error: " + str(e)

    return pages_count, message
###################### STAGE 3-B: ECOM WEEKLY ORGANIC PAGES SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 3-C: ECOM WEEKLY ORGANIC BLOGS SUMMARY TRACKER - STARTS ######################
def collect_weekly_ecom_organic_blogs_summary(token, sdate, edate, prop, user_id, grp_id): 
    try:
        message = ""
        blogs_count = 0 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}], 
                "dimensionFilter": {
                    "andGroup": {
                        "expressions": [
                            {
                                "filter": {
                                    "fieldName": "landingPagePlusQueryString",
                                    "stringFilter": {
                                        "matchType": "CONTAINS",
                                        "value": "/blogs"
                                    }
                                } 
                            },
                            {
                                "filter": {
                                    "fieldName": "sessionDefaultChannelGroup", 
                                    "stringFilter": {
                                        "matchType": "EXACT",
                                        "value": "Organic Search"
                                    }
                                }
                            }
                        ]
                    }
                }                
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Weekly Ecom Organic Blogs Summary - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    flag = 0
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0] and row['dimensionValues'][0]['value'] == "Organic Search":
                            flag += 1

                    if flag and 'metricValues' in row:
                        if len(row['metricValues']) and 'value' in row['metricValues'][0]:
                            blogs_count += int(row['metricValues'][0]['value'])
        else:
           message = "Collect Weekly Ecom Organic Blogs Summary - Token not available" 

    except Exception as e: 
        message = "Collect Weekly Ecom Organic Blogs Summary Exceptional Error: " + str(e)

    return blogs_count, message
###################### STAGE 3-C: ECOM WEEKLY ORGANIC BLOGS SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 3-D: ECOM WEEKLY SUMMARY TRACKER - STARTS ###################### 
def collect_weekly_ecom_summary(token, sdate, edate, prop, user_id, grp_id, pages_count, blog_count):
    try:
        message = ""
        summary_list = [] 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}, {"name": "engagedSessions"}, {"name": "engagementRate"}, {"name": "bounceRate"}, {"name": "transactions"}, {"name": "totalRevenue"}], 
            } 

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Weekly Ecom Summary - " + str(resp['error']['message'])
            elif response.status_code != 200:
                message = "Collect Weekly Ecom Summary - Response Code: " + str(response.status_code)
            elif "rows" in resp: 
                # START OF FOR LOOP
                for row in resp['rows']:
                    source = ""
                    session = engaged_sessions = engagement_rate = bounce_rate = transactions = revenue_rate = 0 
                    
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0]:
                            source = row["dimensionValues"][0]["value"]

                    if source and 'metricValues' in row and len(row["metricValues"]) > 5:
                        session = row["metricValues"][0]["value"]
                        engaged_sessions = row["metricValues"][1]["value"]
                        engagement_rate = round(float(row["metricValues"][2]["value"]) * 100, 2)
                        bounce_rate = round(float(row["metricValues"][3]["value"]) * 100, 2)
                        transactions = row["metricValues"][4]["value"]
                        revenue_rate = round(float(row["metricValues"][5]["value"]), 2)
                    
                    if source == "Organic Search":
                        summary_list.append({
                            "value": source, 
                            "session": session, 
                            "engaged_sessions": engaged_sessions, 
                            "engagement_rate": engagement_rate, 
                            "bounce_rate": bounce_rate,
                            "transaction": transactions,
                            "revenue": revenue_rate,
                            "pages_count": pages_count if pages_count else 0,
                            "blog_count": blog_count if blog_count else 0 
                        }) 
                    else:
                        summary_list.append({
                            "value": source, 
                            "session": session, 
                            "engaged_sessions": engaged_sessions, 
                            "engagement_rate": engagement_rate, 
                            "bounce_rate": bounce_rate,
                            "transaction": transactions,
                            "revenue": revenue_rate
                        })
                # END OF FOR LOOP
                
                filePath = os.getcwd()+'/files/ga_organic/ecom/ga_weekly_organic_'+str(grp_id)+'.json'
                with open(filePath, 'w') as f: 
                    json.dump(resp, f, indent=4)

            else:
                message = "Collect Weekly Ecom Summary - Unknown response handling"
        else:
           message = "Collect Weekly Ecom Summary - Token not available" 

    except Exception as e: 
        message = "Collect Weekly Ecom Summary Exceptional Error: " + str(e)

    return summary_list, message
###################### STAGE 3-D: ECOM WEEKLY SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 3: ECOM WEEKLY TRACKER - STARTS ######################
def ecom_weekly_tracker_connect(user_id, grp_id, track_id, ga_refresh_token, ga_property_id, ga_track_day):
    try:
        loopFlag = 0
        
        if track_id and all([user_id, grp_id, track_id, ga_refresh_token, ga_property_id, ga_track_day]): 
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 
            
            # WHILE LOOP - STARTS
            ga_week_all_data = GA_weekly_reports.objects.filter(**page_filter, overview_status="onTrack").values("id", "start_date", "end_date").all()[0:4] 

            if not ga_week_all_data:
                return -1

            for ga_week_data in ga_week_all_data:
                if ga_week_data:
                    ga_week_id = ga_week_data['id']
                    from_date = ga_week_data['start_date']
                    to_date = ga_week_data['end_date']

                    GA_weekly_reports.objects.filter(**page_filter, id=ga_week_id).update(overview_status="onProgress") 

                    start_date = datetime.strftime(from_date, "%Y-%m-%d")
                    end_date = datetime.strftime(to_date, "%Y-%m-%d")

                    ecom_access_token = retrieve_access_token(ga_refresh_token)  
                    if ecom_access_token: 
                        ecom_organic_pages, pages_message = collect_weekly_ecom_organic_pages(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id)
                        ecom_organic_pages_count, pages_summary_message = collect_weekly_ecom_organic_pages_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id) 
                        ecom_organic_blogs_count, blogs_summary_message = collect_weekly_ecom_organic_blogs_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id)
                        ecom_organic_summary, organic_summary_message = collect_weekly_ecom_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id, ecom_organic_pages_count, ecom_organic_blogs_count) 

                        # HANDLE LOGS
                        track_flow_message = [pages_message, pages_summary_message, blogs_summary_message, organic_summary_message]
                        track_flow_message = str(' | '.join(filter(None, track_flow_message))).strip()

                        # DATABASE UPDATE
                        GA_weekly_reports.objects.filter(**page_filter, id=ga_week_id).update(
                            overview=ecom_organic_summary,
                            landing_page=ecom_organic_pages,    
                            overview_status="done", 
                            modified_date=datetime.now(),
                            track_message=track_flow_message,  
                        )
                        loopFlag += 1 
                    else:
                        GA_weekly_reports.objects.filter(**page_filter, id=ga_week_id).update( 
                            overview_status="onFail", 
                            modified_date=datetime.now(),
                            track_message="Ecom: Error in Access Token Retrieval" 
                        )
            # LOOP - ENDS

            ga_remain_count = GA_weekly_reports.objects.filter(**page_filter, overview_status="onTrack").count()
            if ga_remain_count:  
                return 1

        else:
            message = "Ecom: Weekly Tracker Connect Unknown Params Error"
            GA_weekly_monitor.objects.filter(id=track_id).update(
                track_status="failed", 
                modified_date=datetime.now(),
                track_message=str(message),
                track_scheduled_start=next_date(1)
            )
                
    except Exception as e:
        message = "Ecom: Weekly Tracker Connect Exceptional Error: " + str(e)

        GA_weekly_monitor.objects.filter(id=track_id).update(
            track_status="failed", 
            modified_date=datetime.now(),
            track_message=str(message),
            track_scheduled_start=next_date(1) 
        ) 

    return 2 if loopFlag else 0  
###################### STAGE 3: ECOM WEEKLY TRACKER - CLOSES ###################### 
#
#
#
###################### STAGE 4-A: ECOM MONTHLY ORGANIC PAGES TRACKER - STARTS ######################
def collect_monthly_ecom_organic_pages(token, sdate, edate, prop, user_id, grp_id):
    try:
        message = ""
        data_dict = [] 

        if token:

            landing_page_analytics_params = {
                "dateRanges":[{"startDate":sdate,"endDate":edate}],
                "dimensions":[{"name":"landingPage"}, {"name":"sessionDefaultChannelGroup"}], 
                "metrics":[{"name":"sessions"}],
                'limit': 25000,
                "dimensionFilter": {
                    "filter": {
                        "fieldName": "sessionDefaultChannelGroup", 
                        "stringFilter": {
                            "matchType": "EXACT",
                            "value": "Organic Search"
                        } 
                    }
                }
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 
            
            if 'error' in resp:
                message = "Collect Monthly Ecom Organic Pages - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    landing_page = row['dimensionValues'][0]['value']
                    sessions = int(row['metricValues'][0]['value'])
                    
                    data_dict.append({"value": landing_page, "session": sessions}) 
            
                # Optionally, save to JSON
                filePath = os.getcwd()+'/files/ga_sessions/ecom/ga_monthly_sessions_'+str(grp_id)+'.json' 
                with open(filePath, 'w') as f: 
                    json.dump(resp, f, indent=4)
        else:
           message = "Collect Monthly Ecom Organic Pages Token not available"

    except Exception as e: 
        message = "Collect Monthly Ecom Organic Pages Exceptional Error: " + str(e)

    return data_dict, message

###################### STAGE 4-A: ECOM MONTHLY ORGANIC PAGES TRACKER - CLOSES ######################
#
#
#
###################### STAGE 4-B: ECOM MONTHLY ORGANIC PAGES SUMMARY TRACKER - STARTS ######################
def collect_monthly_ecom_organic_pages_summary(token, sdate, edate, prop, user_id, grp_id): 
    try:
        message = ""
        pages_count = 0 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}], 
                "dimensionFilter": {
                    "andGroup": {
                        "expressions": [
                            {
                                "notExpression": {
                                    "filter": {
                                        "fieldName": "landingPagePlusQueryString",
                                        "stringFilter": {
                                            "matchType": "CONTAINS",
                                            "value": "/blogs"
                                        }
                                    }
                                }
                            },
                            {
                                "filter": {
                                    "fieldName": "sessionDefaultChannelGroup", 
                                    "stringFilter": {
                                        "matchType": "EXACT",
                                        "value": "Organic Search"
                                    }
                                }
                            }
                        ]
                    }
                }                
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Monthly Ecom Organic Pages Summary - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    flag = 0
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0] and row['dimensionValues'][0]['value'] == "Organic Search":
                            flag += 1

                    if flag and 'metricValues' in row:
                        if len(row['metricValues']) and 'value' in row['metricValues'][0]:
                            pages_count += int(row['metricValues'][0]['value'])
        else:
           message = "Collect Monthly Ecom Organic Pages Summary - Token not available" 

    except Exception as e: 
        message = "Collect Monthly Ecom Organic Pages Summary Exceptional Error: " + str(e)

    return pages_count, message
###################### STAGE 4-B: ECOM MONTHLY ORGANIC PAGES SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 4-C: ECOM MONTHLY ORGANIC BLOGS SUMMARY TRACKER - STARTS ######################
def collect_monthly_ecom_organic_blogs_summary(token, sdate, edate, prop, user_id, grp_id): 
    try:
        message = ""
        blogs_count = 0 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}], 
                "dimensionFilter": {
                    "andGroup": {
                        "expressions": [
                            {
                                "filter": {
                                    "fieldName": "landingPagePlusQueryString",
                                    "stringFilter": {
                                        "matchType": "CONTAINS",
                                        "value": "/blogs"
                                    }
                                } 
                            },
                            {
                                "filter": {
                                    "fieldName": "sessionDefaultChannelGroup", 
                                    "stringFilter": {
                                        "matchType": "EXACT",
                                        "value": "Organic Search"
                                    }
                                }
                            }
                        ]
                    }
                }                
            }

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Monthly Ecom Organic Blogs Summary - " + str(resp['error']['message'])
            else:
                for row in resp['rows']:
                    flag = 0
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0] and row['dimensionValues'][0]['value'] == "Organic Search":
                            flag += 1

                    if flag and 'metricValues' in row:
                        if len(row['metricValues']) and 'value' in row['metricValues'][0]:
                            blogs_count += int(row['metricValues'][0]['value'])
        else:
           message = "Collect Monthly Ecom Organic Blogs Summary - Token not available" 

    except Exception as e: 
        message = "Collect Monthly Ecom Organic Blogs Summary Exceptional Error: " + str(e)

    return blogs_count, message
###################### STAGE 4-C: ECOM MONTHLY ORGANIC BLOGS SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 4-D: ECOM MONTHLY SUMMARY TRACKER - STARTS ###################### 
def collect_monthly_ecom_summary(token, sdate, edate, prop, user_id, grp_id, pages_count, blog_count):
    try:
        message = ""
        summary_list = [] 

        if token:
            landing_page_analytics_params = { 
                "dateRanges": [{"startDate": sdate, "endDate": edate}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}, {"name": "engagedSessions"}, {"name": "engagementRate"}, {"name": "bounceRate"}, {"name": "transactions"}, {"name": "totalRevenue"}], 
            } 

            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            api_endpoint = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
            response = requests.post(api_endpoint, headers=headers, json=landing_page_analytics_params)
            resp = response.json() 

            if 'error' in resp:
                message = "Collect Monthly Ecom Summary - " + str(resp['error']['message'])
            elif response.status_code != 200:
                message = "Collect Monthly Ecom Summary - Response Code: " + str(response.status_code)
            elif "rows" in resp: 
                # START OF FOR LOOP
                for row in resp['rows']:
                    source = ""
                    session = engaged_sessions = engagement_rate = bounce_rate = transactions = revenue_rate = 0 
                    
                    if 'dimensionValues' in row:
                        if len(row['dimensionValues']) and 'value' in row['dimensionValues'][0]:
                            source = row["dimensionValues"][0]["value"]

                    if source and 'metricValues' in row and len(row["metricValues"]) > 5:
                        session = row["metricValues"][0]["value"]
                        engaged_sessions = row["metricValues"][1]["value"]
                        engagement_rate = round(float(row["metricValues"][2]["value"]) * 100, 2)
                        bounce_rate = round(float(row["metricValues"][3]["value"]) * 100, 2)
                        transactions = row["metricValues"][4]["value"]
                        revenue_rate = round(float(row["metricValues"][5]["value"]), 2)  
                    
                    if source == "Organic Search":
                        summary_list.append({
                            "value": source, 
                            "session": session, 
                            "engaged_sessions": engaged_sessions, 
                            "engagement_rate": engagement_rate, 
                            "bounce_rate": bounce_rate,
                            "transaction": transactions,
                            "revenue": revenue_rate,
                            "pages_count": pages_count if pages_count else 0,
                            "blog_count": blog_count if blog_count else 0 
                        }) 
                    else:
                        summary_list.append({
                            "value": source, 
                            "session": session, 
                            "engaged_sessions": engaged_sessions, 
                            "engagement_rate": engagement_rate, 
                            "bounce_rate": bounce_rate,
                            "transaction": transactions,
                            "revenue": revenue_rate
                        })
                # END OF FOR LOOP
                
                filePath = os.getcwd()+'/files/ga_organic/ecom/ga_monthly_organic_'+str(grp_id)+'.json'
                with open(filePath, 'w') as f: 
                    json.dump(resp, f, indent=4)

            else:
                message = "Collect Monthly Ecom Summary - Unknown response handling"
        else:
           message = "Collect Monthly Ecom Summary - Token not available" 

    except Exception as e: 
        message = "Collect Monthly Ecom Summary Exceptional Error: " + str(e) 

    return summary_list, message
###################### STAGE 4-D: ECOM MONTHLY SUMMARY TRACKER - CLOSES ######################
#
#
#
###################### STAGE 4: ECOM MONTHLY TRACKER - STARTS ######################
def ecom_monthly_tracker_connect(user_id, grp_id, track_id, ga_refresh_token, ga_property_id): 
    try:
        loopFlag = 0
        
        if track_id and all([user_id, grp_id, ga_refresh_token, ga_property_id]):  
            page_filter={'fk_user_id':user_id, 'fk_group_id':grp_id} 
            
            # FOR LOOP - STARTS
            ga_month_all_data = GA_monthly_reports.objects.filter(**page_filter, overview_status="onTrack").values("id", "start_date", "end_date").all()[0:4] 

            if not ga_month_all_data:
                return -1

            # WHILE LOOP - STARTS
            for ga_month_data in ga_month_all_data:

                if ga_month_data:
                    ga_month_id = ga_month_data['id']
                    from_date = ga_month_data['start_date']
                    to_date = ga_month_data['end_date']

                    GA_monthly_reports.objects.filter(**page_filter, id=ga_month_id).update(overview_status="onProgress") 

                    start_date = datetime.strftime(from_date, "%Y-%m-%d")
                    end_date = datetime.strftime(to_date, "%Y-%m-%d")

                    ecom_access_token = retrieve_access_token(ga_refresh_token)  
                    if ecom_access_token: 
                        ecom_organic_pages, pages_message = collect_monthly_ecom_organic_pages(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id)
                        ecom_organic_pages_count, pages_summary_message = collect_monthly_ecom_organic_pages_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id) 
                        ecom_organic_blogs_count, blogs_summary_message = collect_monthly_ecom_organic_blogs_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id)
                        ecom_organic_summary, organic_summary_message = collect_monthly_ecom_summary(ecom_access_token, start_date, end_date, ga_property_id, user_id, grp_id, ecom_organic_pages_count, ecom_organic_blogs_count) 

                        # HANDLE LOGS
                        track_flow_message = [pages_message, pages_summary_message, blogs_summary_message, organic_summary_message]
                        track_flow_message = str(' | '.join(filter(None, track_flow_message))).strip()

                        # DATABASE UPDATE
                        GA_monthly_reports.objects.filter(**page_filter, id=ga_month_id).update(
                            overview=ecom_organic_summary,
                            landing_page=ecom_organic_pages,    
                            overview_status="done", 
                            modified_date=datetime.now(),
                            track_message=track_flow_message,
                        )
                        loopFlag += 1 
                    else:
                        GA_monthly_reports.objects.filter(**page_filter, id=ga_month_id).update(
                            overview_status="onFail", 
                            modified_date=datetime.now(),
                            track_message="Ecom: Error in Access Token Retrieval" 
                        ) 
            # LOOP - ENDS

            ga_remain_count = GA_monthly_reports.objects.filter(**page_filter, overview_status="onTrack").count()
            if ga_remain_count:
                return 1

        else:
            message = "Ecom: Monthly Tracker Connect Unknown Params Error"
            GA_monthly_monitor.objects.filter(id=track_id).update( 
                track_status="failed", 
                modified_date=datetime.now(),
                track_message=str(message),
                track_scheduled_start=next_month(1)
            )
                
    except Exception as e:
        message = "Ecom: Monthly Tracker Connect Exceptional Error: " + str(e)

        GA_monthly_monitor.objects.filter(id=track_id).update(
            track_status="failed", 
            modified_date=datetime.now(),
            track_message=str(message),
            track_scheduled_start=next_month(1)
        )

    return 2 if loopFlag else 0 

###################### STAGE 4: ECOM MONTHLY TRACKER - CLOSES ###################### 

def test(request):
    sd = "" 
    try:
        ga_refresh_token = os.environ.get("GA_TEST_REFRESH_TOKEN", "")   
        ga_property_all = os.environ.get("GA_TEST_PROPERTY", "")
        ga_property = os.environ.get("GA_TEST_PROPERTY_ID", "")
        user_id = 3
        grp_id = 6498
        track_id = 73
        ga_track_day = "Thursday".lower()  

        # access_token = retrieve_access_token(ga_refresh_token)
        
        # sd = ecom_monthly_tracker_connect(user_id, grp_id, track_id, ga_refresh_token, ga_property, ga_track_day) 

        sd = rpEPRA.ecom_past_weeks_tracker(user_id, grp_id) 

    except Exception as e: 
        sd = str(e)
    
    return JsonResponse({'st':1, 'count': sd })   



