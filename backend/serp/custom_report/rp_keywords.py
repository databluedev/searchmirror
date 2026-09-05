from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.common import *
from account.models import Account  
from serp.models import * 
from serp.custom_serializer.report_serializers import * 
from account import verify as authPermission
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string


import string,random 
from datetime import date, datetime, timedelta


def ordinal_convert(n): 
    return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"

def ordinal_day_convert(n): 
    dateObject = datetime.strptime(str(n), '%Y-%m-%d') 
    dayOrdinal = ordinal_convert(dateObject.day)
    return dateObject.strftime(f'{dayOrdinal} %b')

def rp_calculation_score(score_calc, category, index, f_base, f_last_index, s_last_index, t_last_index):
    if category == f_base:
        score_calc[index][category] += 1
    elif category == f_last_index:
        score_calc[index][category] += 1
    elif category == s_last_index:
        score_calc[index][category] += 1
    elif category == t_last_index: 
        score_calc[index][category] += 1

    return score_calc 

def rp_keywords_overview(f_base, f_last_index, s_last_index, t_last_index, group_data): 

    c_past_index = f_last_index + " vs " + s_last_index

    score_calc = [
        {
            'Keyword Ranking': "Top 5",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
            c_past_index: 0,
        }, {
            'Keyword Ranking': "Top 6 - 10",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
            c_past_index: 0,
        }, {
            'Keyword Ranking': "Top 11 - 20",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
            c_past_index: 0,
        }, {
            'Keyword Ranking': "Top 21 - 30",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
            c_past_index: 0,
        }, {
            'Keyword Ranking': "Top 31 - 50",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
            c_past_index: 0,
        }, {
            'Keyword Ranking': "Above 50",
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0, 
            c_past_index: 0, 
        }, {
            'Keyword Ranking': "Total Keywords", 
            f_base: 0,
            f_last_index: 0,
            s_last_index: 0,
            t_last_index: 0,
        }
    ]

    if group_data:
        # TOP TOTAL CALCULATION FOR EACH COLUMN 
        for single_data in group_data:
            for x in single_data:
                if x in [f_base, f_last_index, s_last_index, t_last_index]: 
                    
                    if str(single_data[x]).isdigit():
                        if single_data[x] >=1 and single_data[x] <=5: 
                            cal_index = 0
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index)
                        elif single_data[x] >=6 and single_data[x] <=10: 
                            cal_index = 1
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index) 
                        elif single_data[x] >=11 and single_data[x] <=20: 
                            cal_index = 2
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index)
                        elif single_data[x] >=21 and single_data[x] <=30: 
                            cal_index = 3
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index) 
                        elif single_data[x] >=31 and single_data[x] <=50: 
                            cal_index = 4
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index)
                        elif single_data[x] >= 51: 
                            cal_index = 5 
                            score_calc = rp_calculation_score(score_calc, x, cal_index, f_base, f_last_index, s_last_index, t_last_index)

        # TOTAL KEYWORDS CALCULATION ON EACH DATE (BASE AND 3 WEEKS DATE) 
        for xy in [f_base, f_last_index, s_last_index, t_last_index]: 
            total_value = 0
            for x in range(0, len(score_calc) - 1):  
                total_value += score_calc[x][xy] 

            # TOTAL KEYWORDS CALCULATE
            score_calc[6][xy] = total_value  

        # VALUE COMPARSION CALCULATION FOR PAST TWO WEEKS
        for up_stream in range(0, len(score_calc) - 1): 
            diff_value = score_calc[up_stream][f_last_index] - score_calc[up_stream][s_last_index] 
            score_calc[up_stream][c_past_index] = diff_value  

    return score_calc 

def rp_keywords_table(user_id, group_id):
    try:    
        if user_id and group_id:
            
            page_filter={'fk_user_id':user_id, 'fk_group_id':group_id} 
            GrpIns = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('domain_name', 'score_meter', 'gsc_last_track', 'week_track_day').first() 
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by('id') 
            
            if keywords and GrpIns:

                day_name = GrpIns['week_track_day'].lower() 
                week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                total_days = 7
                target_day = today_weekday = 0 
                                
                f_base = "Base Ranking" 
                last_day = f_last_index = s_last_index = t_last_index = ""  

                if 'lastranked_date' in keywords[0]:
                    last_day = keywords[0]['lastranked_date'].date() 
                    today_weekday = last_day.weekday()

                if day_name in week_list:
                    target_day = week_list.index(day_name) % total_days 

                remain_count = (today_weekday - target_day + total_days) % total_days 

                if f_last_index == "" and last_day: 
                    week_date = last_day - timedelta(days=remain_count)
                    f_last_index = ordinal_day_convert(week_date)

                if s_last_index == "" and last_day: 
                    week_date = last_day - timedelta(days=remain_count + 7)
                    s_last_index = ordinal_day_convert(week_date)

                if t_last_index == "" and last_day: 
                    week_date = last_day - timedelta(days=remain_count + 14)  
                    t_last_index = ordinal_day_convert(week_date) 

            if f_last_index or s_last_index or t_last_index:

                page_volume_query = list(keywordVolume.objects.filter(**page_filter).values('month_wise_volume', 'past_months', 'fk_keyword_id').all())

                volume_data = {} 
                if page_volume_query:
                    volume_data = {item['fk_keyword_id']:{'month_wise_volume':item['month_wise_volume'], 'past_months':item['past_months']} for item in page_volume_query}

                serializer = CustomReportKeywordSerializer(keywords, many=True, context={'voldata':volume_data, 'dy': day_name, 'dn': GrpIns['domain_name'], 'f_last_index': f_last_index, 's_last_index': s_last_index, 't_last_index': t_last_index}).data

                score = []
                if serializer:
                    score = rp_keywords_overview(f_base, f_last_index, s_last_index, t_last_index, serializer) 

                return score, serializer 

    except Exception as e:
        return [], []

    return [], []  

@api_view(['POST','GET']) 
def rp_keywords_widget(request):
    try:
        if request.method == 'POST':
            user_id = request.data['userid']
            group_id = request.data['grpid'] 

            if user_id and group_id and authPermission.validate(request, "POST"):           
                
                page_filter={'fk_user_id':user_id, 'fk_group_id':group_id} 
                GrpIns = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('domain_name', 'week_track_day').first()
                keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank", "isocode", "search_volume", "platform", "lastranked_date").order_by('id') 

                if keywords and GrpIns:
                    day_name = GrpIns['week_track_day'].lower()
                    week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    total_days = 7
                    target_day = today_weekday = 0
                    
                    last_day = f_last_index = ""  

                    if 'lastranked_date' in keywords[0]:
                        last_day = keywords[0]['lastranked_date'].date()
                        today_weekday = last_day.weekday() 

                    if day_name in week_list:
                        target_day = week_list.index(day_name) % total_days 
                    
                    remain_count = (today_weekday - target_day + total_days) % total_days 

                    if f_last_index == "" and last_day: 
                        week_date = last_day - timedelta(days=remain_count)
                        f_last_index = week_date.strftime("%B %d, %Y")
                        
                    if f_last_index: 
                        page_volume_query = list(keywordVolume.objects.filter(**page_filter).values('month_wise_volume', 'past_months', 'fk_keyword_id').all())

                        volume_data = {}  
                        if page_volume_query: 
                            volume_data = {item['fk_keyword_id']:{'month_wise_volume':item['month_wise_volume'], 'past_months':item['past_months']} for item in page_volume_query}

                        serializer = CustomWidgetReportKeywordSerializer(keywords, many=True, context={'voldata':volume_data, 'dy': day_name, 'dn': GrpIns['domain_name'], 'f_last_index': f_last_index}).data

                        return JsonResponse({'st':1, 'dy': f_last_index, 'dt': serializer})   

    except Exception as e:
        # print("Error Message ", str(e)) 
        return JsonResponse({'st':0, 'message':"Exceptional Warning, Try again later."})

    return JsonResponse({'st':0, 'message':'Something went wrong'}) 