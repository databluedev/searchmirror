from serp.models import *
import requests
import concurrent.futures
from django.http import HttpResponse, JsonResponse
from datetime import *
from account.cron_auth import cron_only

MAX_TRACKS = 10


def ga_last_year_pool(ga_tracks):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_TRACKS) as taskExecutor:
            taskExecutorResult = taskExecutor.map(ga_last_overview_weekly, ga_tracks)
            taskExecutor.shutdown(wait=False)
        return 1
    except Exception as e:
        return 0


def retriev_access_token(refreshToken):
    try:
        data = {"grant_type": "refresh_token", "refresh_token": refreshToken, "client_id": settings.GA_CLIENT_ID, "client_secret": settings.GA_SECRET_ID, "scope": "https://www.googleapis.com/auth/analytics.readonly"}

        xRequest = requests.post("https://accounts.google.com/o/oauth2/token", data=data)
        json_res = xRequest.json()
        access_token = json_res.get("access_token")

        if access_token:
            return access_token
        else:
            return 0
    except Exception as e:
        return 0


def ga_last_overview_weekly(ga_trackings):
    try:
        if hasattr(ga_trackings, "id") and hasattr(ga_trackings, "fk_user_id") and hasattr(ga_trackings, "fk_group_id"):
            grp_sttngs = GroupSetting.objects.filter(fk_user_id=ga_trackings.fk_user_id, fk_group_id=ga_trackings.fk_group_id).first()
            ga_refresh_token = grp_sttngs.ga_refresh_token if hasattr(grp_sttngs, "ga_refresh_token") else None
            ga_property_id = grp_sttngs.ga_property if hasattr(grp_sttngs, "ga_property") else None

            if not ga_refresh_token or not ga_property_id:
                GA_weekly_reports.objects.filter(id=ga_trackings.id).update(overview_status="failed")

            ga_access_token = retriev_access_token(ga_refresh_token)

            if not ga_access_token:
                GA_weekly_reports.objects.filter(id=ga_trackings.id).update(overview_status="failed")

            headers = {"Authorization": "Bearer " + ga_access_token, "Content-Type": "application/json"}
            prop = ga_property_id[11:]
            api_endpoint = f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
            # start_date = datetime.strftime(start_of_week, "%Y-%m-%d")
            # end_date = datetime.strftime(end_of_week, "%Y-%m-%d")
            start_date = ga_trackings.start_date.strftime("%Y-%m-%d")
            end_date = ga_trackings.end_date.strftime("%Y-%m-%d")
            ga_overview_params = {
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                # "metrics":[{"name":"sessions"}]
                "metrics": [{"name": "sessions"}, {"name": "engagedSessions"}, {"name": "engagementRate"}],
            }
            response = requests.post(api_endpoint, headers=headers, json=ga_overview_params)

            if response.status_code != 200:
                GA_weekly_reports.objects.filter(id=ga_trackings.id).update(overview_status="failed")
            if "rows" not in response.json():
                GA_weekly_reports.objects.filter(id=ga_trackings.id).update(overview_status="failed")
            overview_transformed_data = list()
            rows = response.json()["rows"]
            for item in rows:
                source = item["dimensionValues"][0]["value"]
                session = item["metricValues"][0]["value"]
                engaged_sessions = item["metricValues"][1]["value"]
                eg_rate = float(item["metricValues"][2]["value"]) * 100
                bnce_rate = 100 - (float(item["metricValues"][2]["value"]) * 100)
                overview_transformed_data.append({"value": source, "session": session, "engaged_sessions": engaged_sessions, "engagement_rate": eg_rate, "bounce_rate": bnce_rate})
            GA_weekly_reports.objects.filter(
                fk_user_id=ga_trackings.fk_user_id,
                fk_group_id=ga_trackings.fk_group_id,
                id=ga_trackings.id,
                # end_date=end_of_week,
                # landing_page=transformed_data,
                # overview = ov_transformed_data
            ).update(overview=overview_transformed_data)
            GA_weekly_reports.objects.filter(id=ga_trackings.id).update(overview_status="done")
        else:
            GA_weekly_reports.objects.filter(id=ga_trackings.id).update(
                overview_status="failed",
            )
    except Exception as e:
        print(f"error{str(e)}")
        GA_weekly_reports.objects.filter(id=ga_trackings.id).update(
            overview_status="failed",
        )


@cron_only
def last_year_overview_data_weekly(request):
    try:
        global MAX_TRACKS
        schdld_tracks = GA_weekly_reports.objects.filter(overview_status="scheduled").count()
        inprogress_ga_tracking_count = GA_weekly_reports.objects.filter(overview_status="inprogress").count()

        if inprogress_ga_tracking_count >= MAX_TRACKS:
            return JsonResponse({"status": "true", "dt": "Track Queue Filled!"})

        ga_trackings = GA_weekly_reports.objects.filter(overview_status__in=["scheduled", "failed"]).all().order_by("-id")[0 : MAX_TRACKS - inprogress_ga_tracking_count]
        if not ga_trackings:
            return JsonResponse({"status": "true", "dt": "No tracks are scheduled"})

        scheduled_tracks = []

        for each_track in ga_trackings:
            scheduled_tracks.append(each_track.id)

        GA_weekly_reports.objects.filter(id__in=scheduled_tracks).update(overview_status="inprogress")

        ga_last_year_pool(ga_trackings)

        return JsonResponse({"status": "true", "message": "Tracking has been completed"})

    except Exception as e:
        print(str(e))
        return {"st": "false", "dt": "Something went wrong", "msg": str(e)}
