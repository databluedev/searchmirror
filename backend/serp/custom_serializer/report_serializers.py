from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS 
from serp.models import *
from serp.common import *
from mailend.models import KeywordHistory 
from account.models import Account  
from bisect import bisect_right 
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 
from urllib.parse import urlparse
import string,random 
from serp import calculation
from collections import defaultdict

import collections
import numpy

current_day = date.today()
this_week_first_date = current_day - timedelta(days=current_day.isoweekday())
this_week_days = (this_week_first_date - current_day).days
this_week_day = abs(this_week_days)+1

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def timeDifference(later_time, formattype="full"): 
	current_time = datetime.now() 
	start = current_time.strptime(current_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
	ends = datetime.strptime(later_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

	diff = relativedelta(start, ends)

	multiples = 0
	portion = ""

	if diff.years > 0:
		multiples = diff.years
		portion = str(diff.years)+" "+"year"
	elif diff.months > 0:
		multiples = diff.months
		portion = str(diff.months)+" "+"month"
	elif diff.days > 0:
		multiples = diff.days
		portion = str(diff.days)+" "+"day"
	elif diff.hours > 0:
		multiples = diff.hours
		portion = str(diff.hours)+" "+"hour"
	elif diff.minutes > 0:
		multiples = diff.minutes
		portion = str(diff.minutes)+" "+"minute"
	elif diff.seconds > 0:
		multiples = diff.seconds
		portion = str(diff.seconds)+" "+"second"

	returnContent = ""
	if portion == "": 
		returnContent = " Just now "
	elif portion != "" and multiples > 1: 
		returnContent = portion + "s ago"
	else:
		returnContent = portion+" ago" 

	if formattype == "off":
		return returnContent 
	else:
		return returnContent + " ("+custom_strftime('%b {S}, %Y', later_time)+")" 
	# return portion+multiples+" "+"ago" + " ("+custom_strftime('%B {S}, %Y', later_time)+")"  

def reportRankFormulation(liveRank, pastRank):
	totalRankLength = 100 

	if str(liveRank).isdigit() and str(pastRank).isdigit():

		if int(liveRank) == 0 and int(pastRank) == 0:
			formulateValue = 0
		elif int(liveRank) == 0 and int(pastRank) > 0:
			formulateValue = int(pastRank) - int(totalRankLength)
		elif int(liveRank) > 0 and int(pastRank) == 0:
			formulateValue = int(totalRankLength) - int(liveRank) 
		elif int(liveRank) > int(pastRank):
			formulateValue = int(pastRank) - int(liveRank)
		elif int(pastRank) > int(liveRank):
			formulateValue = int(pastRank) - int(liveRank)
		else:  
			formulateValue = int(liveRank) - int(pastRank)
	else:
		formulateValue = "NA"

	return formulateValue 

def ordinal_convert(n): 
    return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"

def ordinal_day_convert(n): 
	dateObject = datetime.strptime(str(n), '%Y-%m-%d') 
	dayOrdinal = ordinal_convert(dateObject.day)
	return dateObject.strftime(f'{dayOrdinal} %b')

# CUSTOM REPORT SERIALIZER FOR THE KEYWORDS DATA.
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

desired = ['Keywords', 'Avg. Volume', 'Landing Pages', 'Base Ranking']
def reorder(original_item, desired_list=desired):
	reorder_list = [item for item in desired_list if item in original_item]
	return reorder_list


def normalize_search_volume(value):
	"""Keep internal/provider sentinels out of customer-facing reports."""
	if value is None:
		return "-"
	normalized = str(value).strip().lower()
	if normalized in {"", "-", "-1", "init", "none", "null", "na", "n/a"}:
		return "-"
	return value


class CustomReportKeywordSerializer(serializers.Serializer):

	def to_representation(self, obj):
		superData = super().to_representation(obj) 
		try:		

			# superData['ID'] = obj['id'] 
			superData['Keywords'] = obj['keyword']

			# SEARCH VOLUME
			if 'average_volume' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Avg. Volume'] = normalize_search_volume(obj['search_volume'])
				svolData = None
				if 'voldata' in self.context:
					svolData = self.context['voldata'][obj['id']] if obj['id'] in self.context['voldata'] else None
				
				if svolData:
					superData['Avg. Volume'] = normalize_search_volume(svolData['month_wise_volume'][-1]) if len(svolData['month_wise_volume']) > 1 else '-'

			# URL
			if 'landing_pages' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Landing Pages'] = ""
				if obj['site_url'] and obj['ranknow'] > 0: 
					superData['Landing Pages'] = obj['site_url'] 
				else:
					superData['Landing Pages'] = self.context['dn']
			
			# BASE RANKING
			if 'base_ranking' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Base Ranking'] = obj['rank_sincestart'] if obj['rank_sincestart'] != 0 else 100 

			# RANKNOW
			# superData['Today'] = obj['ranknow'] if obj['ranknow'] != 0 else 101  

			last_day = ""
			day_name = "monday" 
			week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
			total_days = 7

			target_day = today_weekday = 0 

			if obj['lastranked_date']:
				last_day = obj['lastranked_date'].date()
				today_weekday = last_day.weekday() 

			if 'dy' in self.context: 
				day_name = self.context['dy'].lower()

			if day_name in week_list:
				target_day = week_list.index(day_name) % total_days 

			remain_count = (today_weekday - target_day + total_days) % total_days  
			
			superData[self.context["f_last_index"]] = superData[self.context["s_last_index"]] = superData[self.context["t_last_index"]] = "NA"  

			rank_list_count = len(obj['rank'])

			if rank_list_count >= remain_count: 
				superData[self.context["f_last_index"]] = obj['rank'][remain_count] if obj['rank'][remain_count] else 100
				
			if rank_list_count >= (remain_count + 7):
				superData[self.context["s_last_index"]] = obj['rank'][remain_count + 7] if obj['rank'][remain_count + 7] else 100

			if rank_list_count >= (remain_count + 14):
				superData[self.context["t_last_index"]] = obj['rank'][remain_count + 14] if obj['rank'][remain_count + 14] else 100

			if rank_list_count >= (remain_count + 21):
				superData[self.context["fr_last_index"]] = obj['rank'][remain_count + 21] if obj['rank'][remain_count + 21] else 100

			if rank_list_count >= (remain_count + 28):
				superData[self.context["last_index_5"]] = obj['rank'][remain_count + 28] if obj['rank'][remain_count + 28] else 100

			if rank_list_count >= (remain_count + 28):
				superData[self.context["fv_last_index"]] = obj['rank'][remain_count + 35] if obj['rank'][remain_count + 35] else 100

			if rank_list_count >= (remain_count + 35):
				superData[self.context["sx_last_index"]] = obj['rank'][remain_count + 42] if obj['rank'][remain_count + 42] else 100

			if rank_list_count >= (remain_count + 42):
				superData[self.context['last_index_7']] = obj['rank'][remain_count + 42] if obj['rank'][remain_count + 42] else 100

			if rank_list_count >= (remain_count + 42):
				superData[self.context['se_last_index']] = obj['rank'][remain_count + 42] if obj['rank'][remain_count + 42] else 100
			
			if rank_list_count >= (remain_count + 49):
				superData[self.context['egt_last_index']] = obj['rank'][remain_count + 49] if obj['rank'][remain_count + 49] else 100
			
			if rank_list_count >= (remain_count + 56):
				superData[self.context['last_index_9']] = obj['rank'][remain_count + 56] if obj['rank'][remain_count + 56] else 100

			if rank_list_count >= (remain_count + 63):
				superData[self.context['last_index_10']] = obj['rank'][remain_count + 63] if obj['rank'][remain_count + 63] else 100

			if rank_list_count >= (remain_count + 70):
				superData[self.context['last_index_11']] = obj['rank'][remain_count + 70] if obj['rank'][remain_count + 70] else 100

			if rank_list_count >= (remain_count + 77):
				superData[self.context['last_index_12']] = obj['rank'][remain_count + 77] if obj['rank'][remain_count + 77] else 100
				
			isAsc = False if self.context['filter_options']['order_by'] == 'asc' else True
			diff = str(self.context['f_last_index']) + " vs " + str(self.context['s_last_index'])
			diff_index = "Change ("+diff+")"
			superData[diff_index] = reportRankFormulation(superData[self.context["f_last_index"]], superData[self.context["s_last_index"]])
			date_keys = sorted([key for key in superData.keys() if key not in ['Keywords', 'Avg. Volume', 'Landing Pages', 'Base Ranking', diff_index]], key=lambda x: (di[x.split(' ')[1]] if x!='' else x, con_int(x.split(' ')[0]) if x!='' else x), reverse=isAsc)
			superData = {key: superData[key] for key in reorder(list({'Keywords', 'Avg. Volume', 'Landing Pages', 'Base Ranking'}.intersection(set(superData.keys())))) + date_keys + [diff_index]}
		except Exception as e: 
			pass

		return superData
	
class KeywordRankingMonthlySerializer(serializers.Serializer):
	def to_representation(self, obj):
		try:
			superData = super().to_representation(obj)
			ranks = obj['rank']
			last_ranked_date = obj['lastranked_date']
			start_date = last_ranked_date - timedelta(len(ranks)+1)
			
			if start_date.day > 4:
				if start_date.month == 12:
					current_date = start_date.replace(year=start_date.year + 1, month=1, day=4)
				else:
					current_date = start_date.replace(month=start_date.month + 1, day=4)
			else:
				current_date = start_date.replace(day=4)
				
			ranked_dates = []
			while current_date <= last_ranked_date:
				if start_date <= current_date <= last_ranked_date:
					index = (start_date-current_date).days
					if len(ranks) > abs(index):
					    ranked_dates.append((current_date, ranks[abs(index)-1], index-1))
				if current_date.month == 12:
					current_date = current_date.replace(year=current_date.year + 1, month=1, day=4)
				else:
					current_date = current_date.replace(month=current_date.month + 1, day=4)
			
			superData['Keyword'] = obj['keyword']
			if 'average_volume' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Avg. Volume'] = normalize_search_volume(obj['search_volume'])
				svolData = None
				if 'voldata' in self.context:
					svolData = self.context['voldata'][obj['id']] if obj['id'] in self.context['voldata'] else None
				
				if svolData:
					superData['Avg. Volume'] = normalize_search_volume(svolData['month_wise_volume'][-1]) if len(svolData['month_wise_volume']) > 1 else '-'
			
			if 'landing_pages' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Landing Pages'] = ""
				if obj['site_url'] and obj['ranknow'] > 0: 
					superData['Landing Pages'] = obj['site_url'] 
				else:
					superData['Landing Pages'] = self.context['dn']

			if 'base_ranking' in self.context['filter_options']['metrics'] or len(self.context['filter_options']['metrics']) ==0:
				superData['Base Ranking'] = obj['rank_sincestart'] if obj['rank_sincestart'] !=0 else 100
			
			monthly_ranking = [(date.strftime('%b/%Y'), rank) for date, rank, index in ranked_dates[::-1][0:self.context['filter_options']['duration_limit']]]
			for date, rank in monthly_ranking[::-1]:
				superData[date] = rank
			
			superData['MOM Change'] = monthly_ranking[1][1] - monthly_ranking[0][1]
		
		except Exception as e:
			print(str(e))
		
		return superData

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

class KeywordMonthlyOverviewSerializer(serializers.Serializer):
	def to_representation(self, obj):
		try:
			superData = super().to_representation(obj)
			ranks = obj['rank']
			last_ranked_date = obj['lastranked_date']
			start_date = last_ranked_date - timedelta(len(ranks)+1)
			# start_date = start_date.replace(day=start_date.day+1)

			if start_date.day > 4:
				if start_date.month == 12:
					current_date = start_date.replace(year=start_date.year + 1, month=1, day=4)
				else:
					current_date = start_date.replace(month=start_date.month + 1, day=4)
			else:
				current_date = start_date.replace(day=4)
			ranked_dates = []   
			while current_date <= last_ranked_date:
				# Calculate the actual index for the rank
				if start_date <= current_date <= last_ranked_date:
					index = (start_date-current_date).days
					rank = ranks[index+1]
					rank_classification = classify_rank(rank)
					ranked_dates.append((current_date, rank, rank_classification))
				
				# Move to the next month
				if current_date.month == 12:
					current_date = current_date.replace(year=current_date.year + 1, month=1, day=4)
				else:
					current_date = current_date.replace(month=current_date.month + 1, day=4)

			# print(ranked_dates)
			monthly_overview=[(date, rank, index) for date, rank, index in ranked_dates[::-1][0:self.context['filter_options']['duration_limit']]]
			for date, rank, classification in monthly_overview:
				superData[date.strftime("%b/%Y")]=classification

		except Exception as e:
			print(str(e))
		return superData

# CUSTOM REPORT SERIALIZER FOR THE KEYWORDS DATA. 
class CustomWidgetReportKeywordSerializer(serializers.Serializer):

	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		superData['kd'] = obj['id']
		superData['cc'] = obj['isocode']
		superData['ky'] = obj['keyword']
		superData['pt'] = "M" if obj['platform'].lower() == "mobile" else "D" 

		superData['V'] = normalize_search_volume(obj['search_volume'])

		# SEARCH VOLUME
		svolData = None
		if 'voldata' in self.context:
			svolData = self.context['voldata'][obj['id']] if obj['id'] in self.context['voldata'] else None
		
		if svolData:
			superData['V'] = normalize_search_volume(svolData['month_wise_volume'][-1]) if len(svolData['month_wise_volume']) > 1 else '-'

		last_day = ""
		day_name = "monday"
		week_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
		total_days = 7

		target_day = today_weekday = 0

		if obj['lastranked_date']:
			last_day = obj['lastranked_date'].date()
			today_weekday = last_day.weekday() 

		if 'dy' in self.context: 
			day_name = self.context['dy'].lower()

		if day_name in week_list:
			target_day = week_list.index(day_name) % total_days  

		remain_count = (today_weekday - target_day + total_days) % total_days 

		# A report row for a day the keyword did not appear carries no
		# position at all, rather than an out-of-range sentinel that reads
		# as a measured place. RnS says which: "ranked" or "out_of_range",
		# and "no_entry" when the history does not reach back that far.
		superData['Rn'] = None
		superData['RnS'] = 'no_entry'

		rank_list_count = len(obj['rank'])

		if rank_list_count >= remain_count:
			_day_rank = obj['rank'][remain_count]
			superData['Rn'] = _day_rank if _day_rank else None
			superData['RnS'] = 'ranked' if _day_rank else 'out_of_range'
		
		return superData 


class ReportExportSerializer(serializers.ModelSerializer): 
	xcount = 0
	class Meta:
		model = Keyword
		fields = ("id", "favour") 

	def to_representation(self, obj): 

		if 'format' in self.context:
			superData = super().to_representation(obj)
			self.xcount = int(self.xcount) + 1

			superData["#"] = int(self.xcount)
			superData["Volume"]= "-"
			superData["Comp"] = "-"
			superData["Region"] = obj["region"]
			superData["URL"] = obj["site_url"]  # FULL URL
			superData["Keyword"] = obj["keyword"]
			superData["Rank"] = obj["ranknow"] if obj["ranknow"] != 0 else '>100'
			superData["CLKS"] = obj["gsc_clicks"]
			superData["IMPS"] = obj["gsc_impressions"]

			svolData = None
			if 'voldata' in self.context:
				svolData = next((x for x in self.context["voldata"] if x["fk_keyword_id"] == obj["id"]), None)
			
			if svolData:
				superData["Volume"] = normalize_search_volume(svolData["month_wise_volume"][-1]) if len(svolData["month_wise_volume"]) > 1 else "-"
				superData["Comp"] = svolData["comp_level"].capitalize() if svolData["comp_level"] != "UNSPECIFIED" else "-"

			report_format = str(self.context["format"]).lower()
			if "csv" in report_format:
				# print("XCOUNT ", self.xcount)

				superData["1D"] = "-"
				superData["7D"] = "-"
				superData["15D"] = "-"

				if(obj["dayval"] != 0):
				    superData["1D"] = str(obj["dayval"]) + " ("+ obj["daymark"] +")"

				if(obj["weekval"] != 0):
				    superData["7D"] = str(obj["weekval"]) + " ("+ obj["weekmark"] +")"
				    
				if(obj["halfmonthval"] != 0):
				    superData["15D"] = str(obj["halfmonthval"]) + " ("+ obj["halfmonthmark"] +")" 

				superData["Best Rank"] = int(obj["top_rank"]) if int(obj["top_rank"]) > 0 else '-'
				superData["Updated On"] = custom_strftime('%b {S}, %Y', obj["lastranked_date"]) 

			if "pdf" in report_format:
				domain_name = ""

				domain = urlparse(obj["site_url"])
				if domain.path == "":
				    domain_name = f"{domain.netloc}".replace("www.", "") 
				elif f"{domain.path}" == "/":
				    domain_name = f"{domain.netloc}".replace("www.", "") 
				else:
				    domain_name = domain.path

				superData["Best"] = int(obj["top_rank"]) if int(obj["top_rank"]) > 0 else '-'
				superData["Updated"] = custom_strftime('%b {S}, %Y', obj["lastranked_date"])
				superData["Slug"]= domain_name if domain_name != "" else obj.site_url    # URL		
				superData["Dvalue"] = obj["dayval"]
				superData["Wvalue"] = obj["weekval"]
				superData["Hvalue"] = obj["halfmonthval"]
				superData["Dmark"]= obj['daymark']
				superData["Wmark"]= obj['weekmark']
				superData["Hmark"]= obj['halfmonthmark']

			return superData
		else:
			return None

class NewExportCSVKeywordSerializer(serializers.ModelSerializer):
	xcount = 0
	class Meta:
		model = Keyword
		fields = ("id", "favour")

	def to_representation(self, obj): 
		superData = super().to_representation(obj) 
		self.xcount = int(self.xcount) + 1

		# print("XCOUNT ", self.xcount) 
		
		superData["#"] = int(self.xcount)
		superData["Comp"] = '-'
		superData["Volume"] = '-'
		superData["1D"] = "-"
		superData["7D"] = "-"
		superData["15D"] = "-"

		svolData = None

		if 'voldata' in self.context:
			svolData = next((x for x in self.context["voldata"] if x["fk_keyword_id"] == obj["id"]), None)
		
		if svolData:
			superData["Comp"] = svolData["comp_level"].capitalize() if svolData["comp_level"] != "UNSPECIFIED" else "-"
			superData["Volume"] = normalize_search_volume(svolData["month_wise_volume"][-1]) if len(svolData["month_wise_volume"]) > 1 else '-'
		
		if(obj["dayval"] != 0):
		    superData["1D"] = str(obj["dayval"]) + " ("+ obj["daymark"] +")"

		if(obj["weekval"] != 0):
		    superData["7D"] = str(obj["weekval"]) + " ("+ obj["weekmark"] +")"
		    
		if(obj["halfmonthval"] != 0):
		    superData["15D"] = str(obj["halfmonthval"]) + " ("+ obj["halfmonthmark"] +")"
	
		superData["Keyword"] = obj["keyword"]
		superData["Rank"] = obj["ranknow"] if obj["ranknow"] != 0 else '>100'
		superData["Best Rank"] = int(obj["top_rank"]) if int(obj["top_rank"]) > 0 else '-'
		superData["URL"] = obj["site_url"] 
		superData["Region"] = obj["region"]
		superData["Created On"] = custom_strftime('%b {S}, %Y', obj["created_date"]) 

		return superData

class NewExportPDFKeywordSerializer(serializers.ModelSerializer):
	class Meta:
		model = Keyword
		fields = ("id", "favour") 

	def to_representation(self, obj):
		superData = super().to_representation(obj)

		superData["Volume"]= "-"
		superData["Comp"] = "-"

		domain_name = ""

		domain = urlparse(obj["site_url"])
		if domain.path == "":
		    domain_name = f"{domain.netloc}".replace("www.", "") 
		elif f"{domain.path}" == "/":
		    domain_name = f"{domain.netloc}".replace("www.", "") 
		else:
		    domain_name = domain.path

		svolData = None

		if 'voldata' in self.context:
			svolData = next((x for x in self.context["voldata"] if x["fk_keyword_id"] == obj["id"]), None)
		
		if svolData:
			superData["Volume"] = normalize_search_volume(svolData["month_wise_volume"][-1]) if len(svolData["month_wise_volume"]) > 1 else "-"
			superData["Comp"] = svolData["comp_level"].capitalize() if svolData["comp_level"] != "UNSPECIFIED" else "-"

		superData["Keyword"] = obj["keyword"]
		superData["Rank"] = obj["ranknow"] if obj["ranknow"] != 0 else '>100'
		superData["Best"] = int(obj["top_rank"]) if int(obj["top_rank"]) > 0 else '-'
		superData["URL"] = obj["site_url"]  # Furl
		superData["Region"] = obj["region"]
		superData["Created"] = custom_strftime('%b {S}, %Y', obj["created_date"]) 

		superData["Slug"]= domain_name if domain_name != "" else obj.site_url    # URL		
		
		superData["Dvalue"] = obj["dayval"]
		superData["Wvalue"] = obj["weekval"]
		superData["Hvalue"] = obj["halfmonthval"]
		superData["Dmark"]= obj['daymark']
		superData["Wmark"]= obj['weekmark']
		superData["Hmark"]= obj['halfmonthmark']

		return superData
