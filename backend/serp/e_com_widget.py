from serp.models import Groups, ReportSheets, ReportManager
from django.conf import settings

from datetime import timedelta
from datetime import datetime
from operator import itemgetter
from django.utils import timezone
from serp.custom_serializer.widget_serializers import *
from account import verify as authPermission
from serp.e_comm_metrics.gsc_metrics import gsc_report
from serp.e_comm_metrics.ga_metrics import landing_page_report_sub, other_sources_overview, ga_ecom_overview
from serp.e_comm_metrics.other_metrics import keyword_ranking_report, keyword_monthly_ranking_report, monthly_keywords_overview
from serp.e_comm_metrics.domain_metrics import seo_metrics_sub

def get_grpd_colmn(sheet_type):
    # print(sheet_type in ['gsc_queries', 'gsc_branded_queries', 'gsc_non_branded_queries'], sheet_type)
    if sheet_type in ['gsc_queries', 'gsc_branded_queries', 'gsc_non_branded_queries']:
        return ['', '', '']
    elif sheet_type in ['gsc_pages']:
        return ['', '']
    else:
        return []
    
def get_last_ot_date(duration):
    today = datetime.today()
    if duration == 'monthly':
        first_this_month = today.replace(day=1)
        last_month_last = first_this_month - timedelta(days=1)
        last_month_first = last_month_last.replace(day=1)
        return last_month_first, last_month_last
    else:
        this_week_first=today-timedelta(days=today.weekday())
        last_week_last=this_week_first-timedelta(days=1)
        last_week_first=last_week_last-timedelta(days=last_week_last.weekday())
        return last_week_first, last_week_last

def ecom_generate_widget(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            update_fields = {}
            userid = request.data["userid"]
            grpid = request.data["grpid"]
            page = request.data['page']

            offset = (page - 1) * 2


            group_data = Groups.objects.filter(fk_user_id=userid, id=grpid).first()

            report_sheets = ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
            if not report_sheets:
                ReportManager.objects.filter(track_status="scheduled", fk_user_id=userid, fk_group_id=grpid).update(track_status="failed")
                return {"st": 0, "dt": "No report sheets!"}

            branded_queries = group_data.brand_keywords if group_data.brand_keywords else []

            transformed_data = list()

            if len(report_sheets[offset:offset + 2]) == 0:
                return {"st": 0, "dt": "Something went wrong", 'sht_flg':False}

            for each_sheet in report_sheets[offset:offset + 2]:

                filter_options = {"id": each_sheet.id, "sheet_name": each_sheet.sheet_name, "type": each_sheet.type, "metrics": each_sheet.metrics, "change_units": each_sheet.change_units, "duration": [each_sheet.duration], "duration_limit": each_sheet.duration_limit, "order_by": each_sheet.order_by}
                grpd_colmn = get_grpd_colmn(filter_options['type'])
                # print(grpd_colmn)
                grpd_colmn.extend(filter_options["metrics"])
                grpd_colmn = [i.capitalize() for i in grpd_colmn]
                
                filter_options = {"id": each_sheet.id, "sheet_name": each_sheet.sheet_name, "type": each_sheet.type, "metrics": each_sheet.metrics, "change_units": each_sheet.change_units, "duration": [each_sheet.duration], "duration_limit": each_sheet.duration_limit, "order_by": each_sheet.order_by, "group_columns": each_sheet.duration_limit + len(each_sheet.change_units)}
                if filter_options["type"] in ["gsc_queries", "gsc_branded_queries"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_queries, gsc_weekly_non_branded_queries, _, _, _, search_query_weekly_overview, key_observations, _ = gsc_report("queries", userid, grpid, branded_queries, "weekly", filter_options)
                    if gsc_weekly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_branded_queries[0].keys())) - 3})

                    if filter_options["type"] in ["gsc_queries", "gsc_non_branded_queries"] and gsc_weekly_non_branded_queries:
                        if gsc_weekly_non_branded_queries:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_queries[0].keys())) - 3})

                if filter_options["type"] in ["gsc_non_branded_queries"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_queries, gsc_weekly_non_branded_queries, _, _, _, search_query_weekly_overview, key_observations, _ = gsc_report("queries", userid, grpid, branded_queries, "weekly", filter_options)
                    if gsc_weekly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_queries[0].keys())) - 3})

                if filter_options["type"] in ["gsc_overview"] and "weekly" in filter_options["duration"]:
                    _, _, gsc_overview_data, gsc_brand_overview_data, gsc_non_brand_overview_data, search_overview, _, overview_from_gsc = gsc_report("queries", userid, grpid, branded_queries, "weekly", filter_options)

                    if overview_from_gsc:
                        transformed_data.append({f"{filter_options['sheet_name']}": overview_from_gsc, 'sheet_id':filter_options['id'], "sheet_type":"R1"})
                    
                    if gsc_brand_overview_data:

                        if not gsc_non_brand_overview_data:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_brand_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R2"})

                        if gsc_non_brand_overview_data:
                            chngd_gsc_weekly_branded_queries=[{'Brand ' + key: value for key, value in item.items()} for item in gsc_brand_overview_data]
                            chngd_gsc_weekly_non_branded_queries=[{'Non Brand '+ key: value for key, value in item.items()} for item in gsc_non_brand_overview_data]
                            
                            for brand_item, non_brand_item in zip(chngd_gsc_weekly_branded_queries, chngd_gsc_weekly_non_branded_queries):
                                brand_item.update(non_brand_item)
                            
                            transformed_data.append({f"{filter_options['sheet_name']}": chngd_gsc_weekly_branded_queries, 'sheet_id':filter_options['id'], "sheet_type":"R5"})
                    
                    if not gsc_brand_overview_data:
                        if gsc_non_brand_overview_data:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_non_brand_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R3"})

                    if gsc_overview_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R4"})

                if filter_options["type"] in ["gsc_pages"] and "weekly" in filter_options["duration"]:
                    gsc_weekly_branded_pages, gsc_weekly_non_branded_pages, _, _, _, search_page_weekly_overview, key_observations, _ = gsc_report("pages", userid, grpid, branded_queries, "weekly", filter_options)
                    if gsc_weekly_non_branded_pages:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_weekly_non_branded_pages, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_weekly_non_branded_pages[0].keys())) - 2})

                if filter_options["type"] in ["gsc_queries", "gsc_branded_queries"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_queries, gsc_monthly_non_branded_queries, _, _, _, search_query_monthly_overview, key_observations, _ = gsc_report("queries", userid, grpid, branded_queries, "monthly", filter_options)
                    if gsc_monthly_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_branded_queries[0].keys())) - 3})

                    if filter_options["type"] in ["gsc_queries", "gsc_non_branded_queries"] and gsc_monthly_non_branded_queries:
                        if gsc_monthly_non_branded_queries:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_queries[0].keys())) - 3})

                if filter_options["type"] in ["gsc_non_branded_queries"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_queries, gsc_monthly_non_branded_queries, _, _, _, search_query_monthly_overview, key_observations, _ = gsc_report("queries", userid, grpid, branded_queries, "monthly", filter_options)
                    if gsc_monthly_non_branded_queries:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_queries, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_queries[0].keys())) - 3})

                if filter_options["type"] in ["gsc_overview"] and "monthly" in filter_options["duration"]:
                    _, _, gsc_month_overview_data, gsc_month_brand_overview_data, gsc_month_non_brand_overview_data, search_overview, _, overview_from_gsc = gsc_report("queries", userid, grpid, branded_queries, "monthly", filter_options)
                    
                    if overview_from_gsc:
                        transformed_data.append({f"{filter_options['sheet_name']}": overview_from_gsc, 'sheet_id':filter_options['id'], "sheet_type":"R1"})

                    if gsc_month_brand_overview_data:

                        if not gsc_month_non_brand_overview_data:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_month_brand_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R2"})

                        if gsc_month_non_brand_overview_data:
                            chngd_gsc_weekly_branded_queries=[{'Brand ' + key: value for key, value in item.items()} for item in gsc_month_brand_overview_data]
                            chngd_gsc_weekly_non_branded_queries=[{'Non Brand '+ key: value for key, value in item.items()} for item in gsc_month_non_brand_overview_data]
                            
                            for brand_item, non_brand_item in zip(chngd_gsc_weekly_branded_queries, chngd_gsc_weekly_non_branded_queries):
                                brand_item.update(non_brand_item)
                            
                            transformed_data.append({f"{filter_options['sheet_name']}": chngd_gsc_weekly_branded_queries, 'sheet_id':filter_options['id'], "sheet_type":"R5"})
                    
                    if not gsc_month_brand_overview_data:
                        if gsc_month_non_brand_overview_data:
                            transformed_data.append({f"{filter_options['sheet_name']}": gsc_month_non_brand_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R3"})

                    if gsc_month_overview_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_month_overview_data, 'sheet_id':filter_options['id'], "sheet_type":"R4"})

                if filter_options["type"] in ["gsc_pages"] and "monthly" in filter_options["duration"]:
                    gsc_monthly_branded_pages, gsc_monthly_non_branded_pages, _, _, _, search_page_monthly_overview, key_observations, _ = gsc_report("pages", userid, grpid, branded_queries, "monthly", filter_options)
                    if gsc_monthly_non_branded_pages:
                        transformed_data.append({f"{filter_options['sheet_name']}": gsc_monthly_non_branded_pages, 'sheet_id':filter_options['id'], "metrics": grpd_colmn, "change_units": len(list(gsc_monthly_non_branded_pages[0].keys())) - 2})

                if filter_options["type"] in ["ga_overview"] and "weekly" in filter_options["duration"]:
                    ga_weekly_report = ga_ecom_overview(userid, grpid, "week", filter_options)
                    if ga_weekly_report:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_weekly_report, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_overview"] and "monthly" in filter_options["duration"]:
                    ga_monthly_report = ga_ecom_overview(userid, grpid, "month", filter_options)
                    if ga_monthly_report:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_monthly_report, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_landing_pages"]:
                    ga_landing_page_data = landing_page_report_sub(userid, grpid, filter_options)
                    if ga_landing_page_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": ga_landing_page_data, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["ga_other_sources"]:
                    sd=""
                    ed=""
                    if filter_options['duration'][0]=='weekly':
                        betwn_date=GSCWeeklyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by('-week_start_date').values('week_start_date', 'week_end_date').first()
            
                        if betwn_date:
                            sd=betwn_date['week_start_date']
                            ed=betwn_date['week_end_date']

                        if not betwn_date:
                            three_days_ago = timezone.now() - timedelta(days=4)
                            betwn_date = GA_weekly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("start_date", "end_date").order_by("-start_date").first()
                            if betwn_date:
                                sd=betwn_date['start_date']
                                ed=betwn_date['end_date']
                    else:
                        betwn_date=GSCMonthlyQuery.objects.filter(fk_user_id=userid, fk_group_id=grpid).order_by('-month_start_date').values('month_start_date', 'month_end_date').first()
            
                        if betwn_date:
                            sd=betwn_date['month_start_date']
                            ed=betwn_date['month_end_date']

                        if not betwn_date:
                            three_days_ago = timezone.now() - timedelta(days=4)
                            betwn_date = GA_monthly_reports.objects.filter(fk_user_id=userid, fk_group_id=grpid, end_date__lte=three_days_ago).values("start_date", "end_date").order_by("-start_date").first()
                            if betwn_date:
                                sd=betwn_date['start_date']
                                ed=betwn_date['end_date']
                    if not sd and not ed:
                        sd, ed = get_last_ot_date(filter_options['duration'][0])

                    start = sd.strftime("%dth %b")
                    last = ed.strftime("%dth %b")
                    last_date = f"{start} - {last}"
                    ot_sources_overview = other_sources_overview(userid, grpid, filter_options, sd, ed)
                    if ot_sources_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": ot_sources_overview, 'bt_date':last_date, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking"] and "weekly" in filter_options["duration"]:
                    rp_score, rp_keywords = keyword_ranking_report(userid, grpid, filter_options)
                    if rp_keywords:
                        transformed_data.append({f"{filter_options['sheet_name']}": rp_keywords, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking"] and "monthly" in filter_options["duration"]:
                    monthly_keywords = keyword_monthly_ranking_report(userid, grpid, filter_options)
                    if monthly_keywords:
                        transformed_data.append({f"{filter_options['sheet_name']}": monthly_keywords, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking_overview"] and "weekly" in filter_options["duration"]:
                    rp_score, _ = keyword_ranking_report(userid, grpid, filter_options)
                    if rp_score:
                        transformed_data.append({f"{filter_options['sheet_name']}": rp_score, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["keyword_ranking_overview"] and "monthly" in filter_options["duration"]:
                    monthly_overview = monthly_keywords_overview(userid, grpid, filter_options)
                    if monthly_overview:
                        transformed_data.append({f"{filter_options['sheet_name']}": monthly_overview, 'sheet_id':filter_options['id']})

                if filter_options["type"] in ["domain_metrics"]:
                    base_metrics_data = seo_metrics_sub(userid, grpid, filter_options)
                    if base_metrics_data:
                        transformed_data.append({f"{filter_options['sheet_name']}": base_metrics_data, 'sheet_id':filter_options['id']})

                summary_list = set(["google search console" if i.type in ["gsc_non_branded_queries", "gsc_branded_queries", "gsc_queries"] else "keyword ranking" for i in report_sheets.filter(type__in=["gsc_branded_queries", "gsc_non_branded_queries", "gsc_queries", "keyword_ranking"])])
                grpd_colmn=list()
            return {'st':1, "page":page+1, 'dt':transformed_data, 'sm_list':list(summary_list)}
        return {'st':0, 'dt':'Something went wrong'}
    except Exception as e:
        print(str(e))
        return {"st": 0, "dt": "Something went wrong"}
