from serp.models import *
from serp.custom_serializer.report_serializers import CustomReportKeywordSerializer, KeywordRankingMonthlySerializer, KeywordMonthlyOverviewSerializer
from datetime import *
from django.db.models import Q

di = {
	"Jan":'1',
	"Feb":'2',
	"Mar":'3',
	"Apr":'4',
	"May":'5',
	"Jun":'6',
	"Jul":'7',
	"Aug":'8',
	"Sep":'9',
	"Oct":'10',
	"Nov":'11',
	"Dec":'12',
}
def con_int(x):
	import re
	match = re.search(r'\d+', x)
	conv_int = x
	if match:
		conv_int=match.group()
	return int(conv_int)

def week_classify_rank(rank):
    if 1 <= rank <= 5:
        return 'Top 5'
    elif 6 <= rank <= 10:
        return 'Top 6 - 10'
    elif 11 <= rank <= 20:
        return 'Top 11 - 20'
    elif 21 <= rank <= 30:
        return 'Top 21 - 30'
    elif 31 <= rank <= 50:
        return 'Top 31 - 50'
    else:
        return 'Above 50'

def classify_rank(rank):
    if 1 <= rank <= 5:
        return 'top 5'
    elif 6 <= rank <= 10:
        return '6 to 10'
    elif 11 <= rank <= 20:
        return '11 to 20'
    elif 21 <= rank <= 30:
        return '21 to 30'
    elif 31 <= rank <= 50:
        return '31 to 50'
    elif 51 <= rank <= 100:
        return '51 to 100'
    else:
        return 'not in 100'

def base_rank_counter(keywords, result):
    try:
        category_counts = {'top 5':0, '6 to 10':0, '11 to 20':0, '21 to 30':0, '31 to 50':0, '51 to 100':0, 'not in 100':0}
        result = result
        # print(result)
        for rank_obj in keywords:
            rank_category = classify_rank(rank_obj['rank_sincestart'])
            category_counts[rank_category] += 1
        
        for res_obj in result:
            category = res_obj['primary keyword ranking']
            if category in category_counts:
                res_obj['Base Ranking'] = category_counts[category]

    except Exception as e:
        print(str(e))
    return result

def ordinal_convert(n): 
    return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"

def ordinal_day_convert(n): 
	dateObject = datetime.strptime(str(n), '%Y-%m-%d') 
	dayOrdinal = ordinal_convert(dateObject.day)
	return dateObject.strftime(f'{dayOrdinal} %b')

def remove_empty_keys(data):
    for entry in data:
        if "" in entry:
            del entry[""]
    return data

def week_classify_rank(rank):
    if 1 <= rank <= 5:
        return 'Top 5'
    elif 6 <= rank <= 10:
        return 'Top 6 - 10'
    elif 11 <= rank <= 20:
        return 'Top 11 - 20'
    elif 21 <= rank <= 30:
        return 'Top 21 - 30'
    elif 31 <= rank <= 50:
        return 'Top 31 - 50'
    else:
        return 'Above 50'

def base_rank_week_counter(keywords, result):
    try:
        category_counts = {'Top 5':0, 'Top 6 - 10':0, 'Top 11 - 20':0, 'Top 21 - 30':0, 'Top 31 - 50':0, 'Above 50':0}
        result = result
        # print(result)
        for rank_obj in keywords:
            rank_category = week_classify_rank(rank_obj['rank_sincestart'])
            category_counts[rank_category] += 1
        
        for res_obj in result:
            category = res_obj['primary keyword ranking']
            if category in category_counts:
                res_obj['Base Ranking'] = category_counts[category]

    except Exception as e:
        print(str(e))
    return result

desired = ['Keywords', 'Avg. Volume', 'Landing Pages', 'Base Ranking']
def reorder(original_item, desired_list=desired):
	reorder_list = [item for item in desired_list if item in original_item]
	return reorder_list

def transform_asc(data):
    try:
        asc_data=list()
        diff_item=list(data[0].keys())[len(data[0].keys())-1]
        for each_data in data:
            ov_date_keys = sorted([key for key in each_data.keys() if key not in ['primary keyword ranking', 'Base Ranking', diff_item]], key=lambda x: (di[x.split(' ')[1]] if x!='' else x, con_int(x.split(' ')[0]) if x!='' else x))
            returned_data = {key: each_data[key] if key in each_data.keys() else '' for key in reorder(list({'primary keyword ranking', 'Base Ranking'}.intersection(set(each_data.keys()))), ['primary keyword ranking', 'Base Ranking']) + ov_date_keys + [diff_item]}
            asc_data.append(returned_data)
        return asc_data
    except Exception as e:
        print('TESTING',str(e))
        return []

def calculation_score(score_calc, category, index, f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12):
    if category == f_base:
        score_calc[index][category] += 1
    elif category == f_last_index:
        score_calc[index][category] += 1
    elif category == s_last_index:
        score_calc[index][category] += 1
    elif category == t_last_index:
        score_calc[index][category] += 1
    elif category == fr_last_index:
        score_calc[index][category] += 1
    elif category == fv_last_index:
        score_calc[index][category] += 1
    elif category == sx_last_index:
        score_calc[index][category] += 1
    elif category == se_last_index:
        score_calc[index][category] += 1
    elif category == egt_last_index:
        score_calc[index][category] += 1
    elif category == last_index_5:
        score_calc[index][category] += 1
    elif category == last_index_7:
        score_calc[index][category] += 1
    elif category == last_index_9:
        score_calc[index][category] += 1
    elif category == last_index_10:
        score_calc[index][category] += 1
    elif category == last_index_11:
        score_calc[index][category] += 1
    elif category == last_index_12:
        score_calc[index][category] += 1

    return score_calc

def keywords_overview(f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12, group_data):
    try:

        c_past_index = f_last_index + " vs " + s_last_index

        score_calc = [
            {
                "primary keyword ranking": "Top 5",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 6 - 10",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 11 - 20",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 21 - 30",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Top 31 - 50",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Above 50",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
                c_past_index: 0,
            },
            {
                "primary keyword ranking": "Total Keywords",
                f_base: 0,
                f_last_index: 0,
                s_last_index: 0,
                t_last_index: 0,
                fr_last_index: 0,
                fv_last_index: 0,
                sx_last_index: 0,
                se_last_index: 0,
                egt_last_index: 0,
                last_index_5: 0,
                last_index_7: 0,
                last_index_9: 0,
                last_index_10: 0,
                last_index_11: 0,
                last_index_12: 0,
            },
        ]

        if group_data:
            # TOP TOTAL CALCULATION FOR EACH COLUMN
            for single_data in group_data:
                for x in single_data:
                    if x in [
                        f_base,
                        f_last_index,
                        s_last_index,
                        t_last_index,
                        fr_last_index,
                        fv_last_index,
                        sx_last_index,
                        se_last_index,
                        egt_last_index,
                        last_index_5,
                        last_index_7,
                        last_index_9,
                        last_index_10,
                        last_index_11,
                        last_index_12,
                    ]:

                        if str(single_data[x]).isdigit() and f_base and f_last_index and s_last_index and t_last_index:
                            if single_data[x] >= 1 and single_data[x] <= 5:
                                cal_index = 0
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 6 and single_data[x] <= 10:
                                cal_index = 1
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 11 and single_data[x] <= 20:
                                cal_index = 2
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 21 and single_data[x] <= 30:
                                cal_index = 3
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 31 and single_data[x] <= 50:
                                cal_index = 4
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )
                            elif single_data[x] >= 51:
                                cal_index = 5
                                score_calc = calculation_score(
                                    score_calc,
                                    x,
                                    cal_index,
                                    f_base,
                                    f_last_index,
                                    s_last_index,
                                    t_last_index,
                                    fr_last_index,
                                    fv_last_index,
                                    sx_last_index,
                                    se_last_index,
                                    egt_last_index,
                                    last_index_5,
                                    last_index_7,
                                    last_index_9,
                                    last_index_10,
                                    last_index_11,
                                    last_index_12,
                                )

            # TOTAL KEYWORDS CALCULATION ON EACH DATE (BASE AND 3 WEEKS DATE)
            for xy in [
                f_base,
                f_last_index,
                s_last_index,
                t_last_index,
                fr_last_index,
                fv_last_index,
                sx_last_index,
                se_last_index,
                egt_last_index,
                last_index_5,
                last_index_7,
                last_index_9,
                last_index_10,
                last_index_11,
                last_index_12,
            ]:
                total_value = 0
                for x in range(0, len(score_calc) - 1):
                    total_value += score_calc[x][xy]

                # TOTAL KEYWORDS CALCULATE
                score_calc[6][xy] = total_value

            # VALUE COMPARSION CALCULATION FOR PAST TWO WEEKS
            for up_stream in range(0, len(score_calc) - 1):
                diff_value = score_calc[up_stream][f_last_index] - score_calc[up_stream][s_last_index]
                score_calc[up_stream][c_past_index] = diff_value

        asc_list = transform_asc(score_calc)
        return asc_list if asc_list else score_calc
    except Exception as e:
        return []

def keyword_ranking_report(user_id, group_id, filter_options):
    try:
        if user_id and group_id:

            page_filter = {"fk_user_id": user_id, "fk_group_id": group_id}
            GrpIns = Groups.objects.filter(id=group_id, fk_user_id=user_id).values("domain_name", "score_meter", "gsc_last_track").first()
            GrpSttng = GroupSetting.objects.filter(fk_user_id=user_id, fk_group_id=group_id).values('week_track_day').first()
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")
            grp = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('created_date').first()
            end_of_cr_date = grp['created_date'].replace(hour=23, minute=59, second=59, microsecond=999999)
            base_keywords = list(Keyword.objects.filter(fk_user_id=user_id, fk_group_id=group_id, created_date__lte=end_of_cr_date).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id"))
            if keywords and GrpIns:

                day_name = GrpSttng["week_track_day"].lower()
                week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                total_days = 7
                target_day = today_weekday = 0

                f_base = "Base Ranking"
                last_index_12 = last_index_11 = last_index_10 = last_index_9 = last_index_7 = last_index_5 = last_day = f_last_index = s_last_index = t_last_index = fr_last_index = fv_last_index = sx_last_index = se_last_index = egt_last_index = ""

                if "lastranked_date" in keywords[0]:
                    last_day = keywords[0]["lastranked_date"].date()
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

                if filter_options["duration_limit"] in [3]:
                    if t_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 14)
                        t_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [4, 5, 6, 8, 7, 9, 10, 11, 12]:
                    if t_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 14)
                        t_last_index = ordinal_day_convert(week_date)

                    if fr_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 21)
                        fr_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [5]:
                    if last_index_5 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 28)
                        last_index_5 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [6, 8, 7, 9, 10, 11, 12]:
                    if fv_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 28)
                        fv_last_index = ordinal_day_convert(week_date)

                    if sx_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 35)
                        sx_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [7]:
                    if last_index_7 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 42)
                        last_index_7 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [8, 9, 10, 11, 12]:
                    if se_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 42)
                        se_last_index = ordinal_day_convert(week_date)

                    if egt_last_index == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 49)
                        egt_last_index = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [9, 10, 11, 12]:
                    if last_index_9 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 56)
                        last_index_9 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [10, 11, 12]:
                    if last_index_10 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 63)
                        last_index_10 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [11, 12]:
                    if last_index_11 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 70)
                        last_index_11 = ordinal_day_convert(week_date)

                if filter_options["duration_limit"] in [12]:
                    if last_index_12 == "" and last_day:
                        week_date = last_day - timedelta(days=remain_count + 77)
                        last_index_12 = ordinal_day_convert(week_date)
                # if filter_options['duration_limit'] in [9, 10]:
                #     if last_index_9 == "" and last_day:
                #         week_date = last_day - timedelta(days=remain_count + 56)
                #         last_index_9 = ordinal_day_convert(week_date)

                #     if last_index_10 == "" and last_day:
                #         week_date = last_day - timedelta(days=remain_count + 49)
                #         last_index_10 = ordinal_day_convert(week_date)

                if f_last_index or s_last_index or t_last_index or fr_last_index or fv_last_index or sx_last_index or se_last_index or egt_last_index:
                    # print(group_id, last_index_12 , last_index_11 , last_index_10 , last_index_9 , last_index_7 , last_index_5 , f_last_index , s_last_index , t_last_index , fr_last_index , fv_last_index , sx_last_index , se_last_index , egt_last_index ,)
                    page_volume_query = list(keywordVolume.objects.filter(**page_filter).values("month_wise_volume", "past_months", "fk_keyword_id").all())

                    volume_data = {}

                    if page_volume_query:
                        volume_data = {item["fk_keyword_id"]: {"month_wise_volume": item["month_wise_volume"], "past_months": item["past_months"]} for item in page_volume_query}

                    serializer = CustomReportKeywordSerializer(
                        keywords,
                        many=True,
                        context={
                            "voldata": volume_data,
                            "dy": day_name,
                            "dn": GrpIns["domain_name"],
                            "last_index_7": last_index_7,
                            "f_last_index": f_last_index,
                            "s_last_index": s_last_index,
                            "t_last_index": t_last_index,
                            "fr_last_index": fr_last_index,
                            "fv_last_index": fv_last_index,
                            "sx_last_index": sx_last_index,
                            "se_last_index": se_last_index,
                            "egt_last_index": egt_last_index,
                            "last_index_5": last_index_5,
                            "last_index_9": last_index_9,
                            "last_index_10": last_index_10,
                            "last_index_11": last_index_11,
                            "last_index_12": last_index_12,
                            "filter_options": filter_options,
                        },
                    ).data

                    score = []
                    if serializer:
                        score = keywords_overview(f_base, f_last_index, s_last_index, t_last_index, fr_last_index, fv_last_index, sx_last_index, se_last_index, egt_last_index, last_index_5, last_index_7, last_index_9, last_index_10, last_index_11, last_index_12, serializer)
                    rem_score = [i.pop('Base Ranking') for i in score]
                    base_rank = base_rank_week_counter(base_keywords, score)
                    asc_list=transform_asc(base_rank)
                    asc_list.pop(len(asc_list)-1)
                    total_keywords = {'primary keyword ranking': 'Total keywords'}
                    for entry in asc_list:
                        for key, value in entry.items():
                            if key not in ('primary keyword ranking'):
                                total_keywords[key] = total_keywords.get(key, 0) + value
                    asc_list.append(total_keywords)
                    return remove_empty_keys(asc_list), remove_empty_keys(serializer)
            else:
                return [], []
    except Exception as e:
        print(str(e))
        return [], []
    
def keyword_monthly_ranking_report(user_id, group_id, filter_options):
    try:
        if user_id and group_id:

            page_filter = {"fk_user_id": user_id, "fk_group_id": group_id}
            GrpIns = Groups.objects.filter(Q(id=group_id), fk_user_id=user_id).values("domain_name", "score_meter", "gsc_last_track").first()
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")

            if keywords and GrpIns:
                serializer=KeywordRankingMonthlySerializer(
                    keywords, 
                    many=True, 
                    context={
                        "dn": GrpIns["domain_name"],
                        "filter_options":filter_options
                        }).data
                unique_dates = set()
                for entry in serializer:
                    unique_dates.update(entry.keys())
                desc_date_list = list(filter(lambda x: x not in ['Base Ranking', 'Keyword', 'Avg. Volume', 'MOM Change', 'Landing Pages'], unique_dates))
                desc_date_list.sort(key=lambda date:datetime.strptime(date, "%b/%Y"), reverse=True)

                normalized_data = []
                for entry in serializer:
                    normalized_entry = {date: entry.get(date, 'NA') for date in unique_dates}
                    normalized_data.append(normalized_entry)
                asc_data=list()
                if filter_options['order_by']=='asc':
                    for each_data in normalized_data:
                        returned_data = {key: each_data[key] if key in each_data.keys() else '' for key in reorder(normalized_data[0].keys(), serializer[0].keys())}
                        # print(returned_data)
                        asc_data.append(returned_data)
                else:
                    # desc_data = list()
                    dic={'average_volume':'Avg. Volume', 'landing_pages':'Landing Pages', 'base_ranking':'Base Ranking',}
                    metrics = [dic[i] for i in filter_options['metrics']]
                    for entry in serializer:
                        entries = {key:entry[key] if key in entry.keys() else '' for key in ['Keyword']+metrics+desc_date_list+['MOM Change']}
                        asc_data.append(entries)
                return asc_data
            else:
                return [], []
    except Exception as e:
        print(str(e))
        return [], []

def monthly_keywords_overview(user_id, group_id, filter_options):
    try:
        if user_id and group_id:
            page_filter={"fk_user_id": user_id, "fk_group_id": group_id}
            keywords = Keyword.objects.filter(**page_filter).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id")
            grp = Groups.objects.filter(fk_user_id=user_id, id=group_id).values('created_date').first()
            end_of_cr_date = grp['created_date'].replace(hour=23, minute=59, second=59, microsecond=999999)
            base_keywords = list(Keyword.objects.filter(fk_user_id=user_id, fk_group_id=group_id, created_date__lte=end_of_cr_date).values("id", "keyword", "rank_sincestart", "rank", "ranknow", "search_volume", "site_url", "lastranked_date", "created_date").order_by("id"))
            if keywords:
                serializer=KeywordMonthlyOverviewSerializer(keywords, many=True, context={'filter_options':filter_options}).data
                categories = ['top 5', '6 to 10', '11 to 20', '21 to 30', '31 to 50', '51 to 100', 'not in 100']
                counts=dict()
                all_dates = set()
                for entry in serializer:
                    all_dates.update(entry.keys())
                sortable_date = list(all_dates)
                sortable_date.sort(key=lambda date:datetime.strptime(date,"%b/%Y"))
                for category in categories:
                    counts[category] = {date: 0 for date in sortable_date}
                for entry in serializer:
                    for date, category in entry.items():
                        if category in counts:
                            counts[category][date] += 1
                result = []
                for category, date_counts in counts.items():
                    category_entry = {'primary keyword ranking': category, 'Base Ranking':0}
                    category_entry.update(date_counts)
                    result.append(category_entry)
                    # print(returned_data)

                base_result = base_rank_counter(base_keywords, result)
                for entry in base_result:
                    keys=list(entry.keys())[::-1][0:2]
                    val=0
                    # print(keys)
                    fil_key = list(filter(lambda x: x not in ['primary keyword ranking', 'Base Ranking'], keys))
                    if len(fil_key)>1:
                        for i in fil_key:
                                val=entry.get(i)-val
                    else:
                        val=0
                    entry['MOM Change']=-val
                
                total_keywords = {'primary keyword ranking': 'Total keywords'}
                for entry in base_result:
                    for key, value in entry.items():
                        if key not in ('primary keyword ranking', 'MOM Change'):
                            total_keywords[key] = total_keywords.get(key, 0) + value

                base_result.append(total_keywords)
                return base_result
            else:
                print('err1')
                return []
        else:
            print('err2')
            return []
    except Exception as e:
        print(str(e))