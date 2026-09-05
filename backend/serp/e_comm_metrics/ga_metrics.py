from django.utils import timezone
from serp.models import *
from datetime import date, datetime, timedelta
from operator import itemgetter
import functools, requests

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

def formatted_date(date):
    return date.strftime("%d %b")

def monthly_formatted_date(date):
    return date.strftime("%b %y")

def op_identifier(value):
    if value<0:
        return value
    elif value>0:
        return f"{value} ~~"

def calculate_percentage_difference(old_value, new_value):
    if old_value == 0:
        if new_value == 0:
            return "0%"
        else:
            return "100%"

    # Calculate the percentage difference
    percentage_difference = (new_value - old_value) / old_value * 100

    # Format the percentage difference with the plus or minus symbol and one decimal point
    formatted_percentage_difference = "{:+.1f}%".format(percentage_difference)

    return formatted_percentage_difference

def ga_ecom_overview(userid, grpid, param, filter_options):
    try:
        ga_data = None
        three_days_ago = timezone.now() - timedelta(days=4)
        if param == "week":
            ga_data = list(GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("landing_page", "overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[:filter_options['duration_limit']])
        elif param == "month":
            ga_data = list(GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("landing_page", "overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[: filter_options["duration_limit"]])
        
        if not ga_data:
            print('not exists')
            return []
        else:
            overview = list()
            organic_sessions = 0
            transaction = 0
            revenue = 0
            for index, i in enumerate(ga_data):
                overview_data = {}
                if param=='week':
                    overview_data[param.capitalize()] = f"{formatted_date(i['start_date'])} - {formatted_date(i['end_date'])}" 
                else:
                    overview_data[param.capitalize()] = f"{monthly_formatted_date(i['start_date'])}"
                for zindex, k in enumerate(i.get('overview')):
                    if k['value'] == "Organic Search":
                        session_difference = int(k["session"]) - organic_sessions if index!=0 else 'NA'
                        transaction_variance = float(k.get('transaction', 0)) - float(transaction) if index!=0 else 'NA'
                        revenue_variance = float(k.get('revenue', 0)) - float(revenue) if index!=0 else 'NA'

                        organic_sessions = int(k["session"])
                        transaction = float(k.get('transaction', 0))
                        revenue = float(k.get('revenue', 0))

                        overview_data['Session'] = k.get('session', 'NA')
                        overview_data['Landing Pages'] = k.get('pages_count', 'NA')
                        overview_data['Blog'] = k.get('blog_count', 'NA')
                        overview_data['Engagement rate'] = k.get('engagement_rate', 'NA')
                        overview_data["% Change in Traffic"] = (session_difference) if session_difference!='NA' else session_difference
                        overview_data['Transactions'] = k.get('transaction', 'NA')
                        overview_data['% Change in Transaction'] = (transaction_variance) if transaction_variance!='NA' else transaction_variance
                        overview_data['Revenue'] = k.get('revenue', 'NA')
                        overview_data['% Change in Revenue'] = (revenue_variance) if revenue_variance!='NA' else revenue_variance
                overview.append(overview_data)
            return overview
    except Exception as e:
        print(str(e))
        return []

# def ga_overview_sub(userid, grpid, param, filter_options):
#     try:
#         ga_weekly = None
#         three_days_ago = timezone.now() - timedelta(days=4)
#         if param == "week":
#             ga_weekly = list(GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[: filter_options["duration_limit"]])
#         elif param == "month":
#             ga_weekly = list(GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("overview", "id", "start_date", "end_date", "created_date").order_by("-end_date")[: filter_options["duration_limit"]])

#         isDesc = True if filter_options["order_by"] == "desc" else False

#         overview_data = {}
#         overview_data["sessions"] = {"Organic Metrics": "Sessions"}
#         # overview_data["users"] = {"Organic Metrics": "Users"}
#         overview_data['engaged_sessions'] = {"Organic Metrics": "EngagedSessions"}
#         overview_data["engagement_rate"] = {"Organic Metrics": "Engagement Rate (%)"}
#         overview_data["bounce_rate"] = {"Organic Metrics": "Bounce Rate (%)"}
#         # overview_data["time_spent"] = {"Organic Metrics": "Time Spent (Min)"}
#         overview_data["session_change"] = {"Organic Metrics": "Session Change"}
#         overview_data["organic_share"] = {"Organic Metrics": "Organic Share in (%)"}

#         if not ga_weekly:
#             print('ga error')
#             return {}
#         else:
#             ga_weekly = sorted(ga_weekly, key=itemgetter("start_date"), reverse=isDesc)
#             organic_sessions = 0
#             session_difference = 0
#             for index, data in enumerate(ga_weekly):
#                 if param == "week":
#                     duration = f"{formatted_date(data['start_date'])} - {formatted_date(data['end_date'])}"
#                 else:
#                     duration = f"{formatted_date(data['end_date'])}"

#                 overall_sessions = list(map(lambda x: x["session"], data["overview"]))
#                 # print(overall_sessions)
#                 total_sessions = 0
#                 if len(overall_sessions)>0:
#                     total_sessions = functools.reduce(lambda a, b: int(a) + int(b), overall_sessions)
#                 # print(total_sessions)
#                 for i, category_data in enumerate(data["overview"]):
#                     if category_data["value"] == "Organic Search":
#                         # print(category_data['engaged_sessions'])
#                         session_difference = int(category_data["session"]) - organic_sessions if index!=0 else 'NA'
#                         organic_sessions = int(category_data["session"])
#                         overview_data["sessions"][duration] = int(category_data["session"]) if "session" in category_data else "NA"
#                         # overview_data["users"][duration] = int(category_data["users"]) if "users" in category_data else "NA"
#                         # overview_data['engaged_sessions'] = int(category_data['engaged_sessions']) if 'engaged_sessions' in category_data else 'NA'
#                         overview_data['engaged_sessions'][duration] = category_data['engaged_sessions'] if 'engaged_sessions' in category_data else 'NA'
#                         overview_data["bounce_rate"][duration] = category_data['bounce_rate'] if 'bounce_rate' in category_data else 'NA'#round(int(category_data["purchase_event"]) * 100) if "purchase_event" in category_data else "NA"
#                         overview_data["engagement_rate"][duration] = category_data['engagement_rate'] if 'engagement_rate' in category_data else 'NA' #round(float(category_data["eg_rate"]) * 100) if "eg_rate" in category_data else "NA"
#                         # overview_data["time_spent"][duration] = int(category_data["event_count"]) if "event_count" in category_data else "NA"
#                         overview_data["session_change"][duration] = op_identifier(session_difference) if session_difference!='NA' else session_difference
#                         overview_data["organic_share"][duration] = round(int(category_data["session"]) / int(total_sessions) * 100) if "session" in category_data else "NA"

#             return list(overview_data.values())
#     except Exception as e:
#         print(str(e))
#         return {}
def determine_page_type(path):
    if "blog" in str(path):
        return "Blog"
    else:
        return "Non Blog"


def landing_page_report_sub(userid, grpid, filter_options):
    try:
        isDesc = True if filter_options["order_by"] == "desc" else False

        three_days_ago = timezone.now() - timedelta(days=4)
        
        rec_limit = 2 if filter_options['duration_limit']==1 else filter_options['duration_limit']

        if 'weekly' in filter_options['duration']:
            ga_weekly = list(GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("landing_page", "id", "start_date", "end_date", "created_date").order_by("-start_date")[: rec_limit])
        else:
            ga_weekly = list(GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("landing_page", "id", "start_date", "end_date", "created_date").order_by("-start_date")[: rec_limit])
        ga_weekly = sorted(ga_weekly, key=itemgetter("start_date"), reverse=isDesc)
        result = {}

        if not ga_weekly:
            return result

        weekly_ga_landing_pages = []
        overall_ga_landing_pages = {}
        for index, each_ga_page in enumerate(ga_weekly):
            each_week = {}
            each_week["week"] = f"{formatted_date(each_ga_page['start_date'])} - {formatted_date(each_ga_page['end_date'])}"
            each_week["landing_pages"] = each_ga_page["landing_page"]
            weekly_ga_landing_pages.append(each_week)

        week_ranges = [each_week["week"] for each_week in weekly_ga_landing_pages]
        ga_landing_pages = {}

        for week_data in weekly_ga_landing_pages:
            for query_data in week_data.get("landing_pages", []):
                path = query_data["value"]
                session = query_data.get("session", None)
                if path not in ga_landing_pages:
                    ga_landing_pages[path] = {}
                ga_landing_pages[path][week_data["week"]] = {"sessions": session}

        # print(ga_landing_pages)

        for path, week_data in ga_landing_pages.items():
            path_ga_data = {}
            previous_session = None
            last_session = None
            session_difference = "NA"
            session_difference_ratio = "NA"
            comparison_done=True
            for index, week in enumerate(week_ranges):
                week_info = week_data.get(week, {"sessions": "NA"})
                if filter_options['duration_limit']==1:
                    if isDesc and index==0:
                        path_ga_data["Landing Pages"] = path
                        path_ga_data[week] = week_info["sessions"]
                    elif not isDesc and index==1:
                        path_ga_data["Landing Pages"] = path
                        path_ga_data[week] = week_info["sessions"]
                else:
                    path_ga_data["Landing Pages"] = path
                    path_ga_data[week] = week_info["sessions"]

                if week_info["sessions"] not in ["NA", None]:
                    last_session = int(week_info["sessions"])
                
                if isDesc:
                    if comparison_done:
                        if previous_session is not None and last_session is not None and comparison_done:
                            session_difference = previous_session - last_session
                            session_difference_ratio = calculate_percentage_difference(last_session, previous_session)
                            comparison_done=False
                        else:
                            session_difference = "NA"
                            session_difference_ratio = "NA"
                else:
                    if previous_session is not None and last_session is not None:
                        session_difference = last_session - previous_session
                        session_difference_ratio = calculate_percentage_difference(previous_session, last_session)
                    else:
                        session_difference = "NA"
                        session_difference_ratio = "NA"

                previous_session = last_session if last_session not in ["NA", None] else None

            if 'percentage' in filter_options['change_units'] or 'number' in filter_options['change_units']:

                if "percentage" in filter_options["change_units"]:
                    path_ga_data["Change (%)"] = session_difference_ratio

                if "number" in filter_options["change_units"]:
                    path_ga_data["Change"] = session_difference
            else:
                path_ga_data["Change (%)"] = session_difference_ratio
                path_ga_data["Change"] = session_difference

            overall_ga_landing_pages[path] = path_ga_data

        if not overall_ga_landing_pages:
            return {}

        return list(overall_ga_landing_pages.values())

    except Exception as e:
        print(f"Error: {e}")
        return {}

def other_sources_overview(userid, grpid, filter_options, sd, ed):
    try:
        ov_transformed_data = list()
        grpSet = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('ga_property', 'ga_refresh_token').first()
        access_token = retrieve_access_token(grpSet['ga_refresh_token'])
        # print(access_token)
        if access_token:
            overview_params = {
                "dateRanges":[{"startDate":sd.strftime('%Y-%m-%d'),"endDate":ed.strftime('%Y-%m-%d')}],
                "dimensions":[{"name":"sessionDefaultChannelGroup"}], 
                "metrics":[{"name":"sessions"}, {'name':'sessionKeyEventRate:purchase'}, {'name':'activeUsers'}, {'name':'eventCount'}, {'name':'engagementRate'}, {'name':'totalRevenue'}],
                # "metrics":[{"name":"sessions"}, {"name":"engagedSessions"}, {"name":"engagementRate"}],
                'limit': 250000
            }
            prop = grpSet['ga_property'][11:]
            # print(prop)
            api_endpoint=f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
            headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"} 

            response = requests.post(api_endpoint, headers=headers, json=overview_params)
            # print(response.text)
            # print(2780, response.status_code)
            if response.status_code==200:
                if 'rows' in response.json():
                    rows = response.json()['rows']
                    for item in rows:
                        source = item['dimensionValues'][0]['value']
                        session = float(item['metricValues'][0]['value'] ) 
                        purchase_event = float(item['metricValues'][1]['value']) 
                        act_users = float(item['metricValues'][2]['value'])
                        evnt_cnt = float(item['metricValues'][3]['value'])
                        eg_rate = float(item['metricValues'][4]['value']) * 100
                        ttl_revenue = float(item['metricValues'][5]['value'])
                        ov_transformed_data.append({'Session primary channel group (Default Channel Group)': source, 'Users': act_users, 'Sessions':session, 'Engagement Rate (%)':eg_rate, 'Event Count':evnt_cnt, 'Key Event (Purchase)':purchase_event, 'Total Revenue':ttl_revenue})
        return ov_transformed_data
    except Exception as e:
        print(str(e))
        return []