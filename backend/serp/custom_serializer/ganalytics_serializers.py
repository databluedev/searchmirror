from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS 

import json, requests
from datetime import date, datetime, timedelta
from collections import Counter 

from serp.models import *
from serp.common import *
from account.models import Account

############################ GENERAL METHODS - STARTS ############################
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

def retrieve_past_each_week(ref, prop, sd, ed):
	try:
		ov_transformed_data = list()
		access_token = retrieve_access_token(ref)
		if access_token:
			overview_params = {
				"dateRanges":[{"startDate":sd,"endDate":ed}],
				"dimensions":[{"name":"sessionDefaultChannelGroup"}], 
				"metrics":[{"name":"sessions"}, {"name":"engagedSessions"}, {"name":"engagementRate"}],
				'limit': 250000
			}
			api_endpoint=f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
			headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"} 

			response = requests.post(api_endpoint, headers=headers, json=overview_params)
			if response.status_code==200:
				if 'rows' in response.json():
					rows = response.json()['rows']
					for item in rows:
						source = item['dimensionValues'][0]['value']
						session = item['metricValues'][0]['value']  
						engaged_sessions = item['metricValues'][1]['value'] 
						eg_rate = float(item['metricValues'][2]['value']) * 100
						bnce_rate = 100 - (float(item['metricValues'][2]['value'])*100)
						ov_transformed_data.append({'value': source, 'session': session, 'engaged_sessions':engaged_sessions, 'engagement_rate':eg_rate, 'bounce_rate':bnce_rate})
		return ov_transformed_data
	except Exception as e:
		print(str(e))
		return []

def convert_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    formatted_date = date_obj.strftime("%Y-%m-%dT00:00:00.000+00:00")
    return formatted_date

############################ GENERAL METHODS - CLOSES ############################
#
#
#
############################ ECOM SERIALIZER METHODS - STARTS ############################
class EcomYearlyToWeeklyBlankSerializer(serializers.Serializer): 
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			if 'userid' in self.context and 'grpid' in self.context:				
				weekly_report = GA_weekly_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = convert_date(obj['sd'].strftime('%Y%m%d')), 
					end_date = convert_date(obj['ed'].strftime('%Y%m%d')),
					landing_page = {}, 
					overview = [],
					created_date = datetime.now(),
					modified_date = datetime.now(),
					overview_status = "onTrack" 
				)
				return weekly_report 

		except Exception as e:
			# GET THE MONITOR ID AND UPDATE THE ERROR MESSAGE 
			raise e

		return None 

class EcomYearlyToMonthlyBlankSerializer(serializers.Serializer):  
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			if 'userid' in self.context and 'grpid' in self.context:				
				monthly_report = GA_monthly_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = convert_date(obj['sd'].strftime('%Y%m%d')), 
					end_date = convert_date(obj['ed'].strftime('%Y%m%d')),
					landing_page = {},
					overview = [],
					created_date = datetime.now(),
					modified_date = datetime.now(),
					overview_status = "onTrack" 
				)
				return monthly_report

		except Exception as e:
			# GET THE MONITOR ID AND UPDATE THE ERROR MESSAGE 
			raise e

		return None
############################ ECOM SERIALIZER METHODS - CLOSES ############################
#
#
#
############################ NON ECOM SERIALIZER METHODS - STARTS ############################
class AnalyticsYearlyMetricsSerializer(serializers.Serializer):
	
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			ga_session_list = ga_overview_list = list()
			if 'ga_sessions' in self.context and 'ga_overview' in self.context:
				if obj in self.context['ga_sessions']:
					ga_session_list = self.context['ga_sessions'][obj]

				if obj in self.context['ga_overview']:
					ga_overview_list = self.context['ga_overview'][obj]
			
				date_value = convert_date(obj)
				daily_report = GA_daily_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = date_value,
					end_date = date_value,
					landing_page = ga_session_list,
					overview = ga_overview_list,
					created_date = datetime.now(),
					modified_date = datetime.now() 
				)
				return daily_report

		except Exception as e:
			raise e

		return None 

class YearlyToWeeklyMetricsSerializer(serializers.Serializer):
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			if 'pages_dict' in self.context and 'organic_dict' in self.context:				
				week_start = obj['sd']
				week_end = obj['ed'] 
				
				pages_list = [] 
				organic_list = [] 
				pages_json = organic_json = {}

				while week_start <= week_end:
					on_date = week_start.strftime('%Y-%m-%d') 

					if on_date in self.context['pages_dict']:
						pages_list += self.context['pages_dict'][on_date]

					if on_date in self.context['organic_dict']:
						organic_list += self.context['organic_dict'][on_date]

					week_start = week_start + timedelta(days=1)

				# DATA COLLECTOR AND MERGER
				if pages_list:
					pages_counter = Counter()
					for item in pages_list:
						pages_counter[item["value"]] += item["session"]

					pages_json = [{"value": key, "session": value} for key, value in pages_counter.items()] 

				if organic_list:
					organic_counter = Counter()
					for item in organic_list:
						organic_counter[item["value"]] += item["session"]

					organic_json = [{"value": key, "session": value} for key, value in organic_counter.items()]

				daily_report = GA_weekly_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = convert_date(obj['sd'].strftime('%Y%m%d')), 
					end_date = convert_date(obj['ed'].strftime('%Y%m%d')),
					landing_page = pages_json,
					overview = [],
					created_date = datetime.now(),
					modified_date = datetime.now(),
					overview_status = "scheduled" 
				)
				return daily_report

		except Exception as e:
			raise e

		return None 

# MONTHLY CONVERSION API
class YearlyToMonthlyMetricsSerializer(serializers.Serializer): 
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			if 'pages_dict' in self.context and 'organic_dict' in self.context:				
				month_start = obj['sd']
				month_end = obj['ed'] 
				
				pages_list = [] 
				organic_list = [] 
				pages_json = organic_json = {}

				while month_start <= month_end:
					on_date = month_start.strftime('%Y-%m-%d') 

					if on_date in self.context['pages_dict']:
						pages_list += self.context['pages_dict'][on_date]

					if on_date in self.context['organic_dict']:
						organic_list += self.context['organic_dict'][on_date]

					month_start = month_start + timedelta(days=1)

				# DATA COLLECTOR AND MERGER
				if pages_list:
					pages_counter = Counter()
					for item in pages_list:
						pages_counter[item["value"]] += item["session"]

					pages_json = [{"value": key, "session": value} for key, value in pages_counter.items()] 

				if organic_list:
					organic_counter = Counter()
					for item in organic_list:
						organic_counter[item["value"]] += item["session"]

					organic_json = [{"value": key, "session": value} for key, value in organic_counter.items()] 

				daily_report = GA_monthly_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = convert_date(obj['sd'].strftime('%Y%m%d')), 
					end_date = convert_date(obj['ed'].strftime('%Y%m%d')),
					landing_page = pages_json,
					overview = [],
					created_date = datetime.now(),
					modified_date = datetime.now(),
					overview_status = "scheduled" 
				)
				return daily_report

		except Exception as e:
			raise e

		return None 

class SingleMonthlyMetricsSerializer(serializers.Serializer):
	def to_representation(self, obj):
		superData = super().to_representation(obj) 

		try:
			if 'pages_dict' in self.context and 'organic_dict' in self.context:				
				month_start = obj['sd']
				month_end = obj['ed'] 
				
				pages_list = [] 
				organic_list = [] 
				pages_json = organic_json = [] 

				while month_start <= month_end:
					on_date = month_start.strftime('%Y-%m-%d') 

					if on_date in self.context['pages_dict']:
						pages_list += self.context['pages_dict'][on_date]

					if on_date in self.context['organic_dict']:
						organic_list += self.context['organic_dict'][on_date]

					month_start = month_start + timedelta(days=1)

				# DATA COLLECTOR AND MERGER
				if pages_list:
					pages_counter = Counter()
					for item in pages_list:
						pages_counter[item["value"]] += item["session"]

					pages_json = [{"value": key, "session": value} for key, value in pages_counter.items()] 

				if organic_list:
					organic_counter = Counter()
					for item in organic_list:
						organic_counter[item["value"]] += item["session"]

					organic_json = [{"value": key, "session": value} for key, value in organic_counter.items()]  

				daily_report = GA_monthly_reports(
					fk_user_id = self.context["userid"],
					fk_group_id = self.context["grpid"], 
					start_date = convert_date(obj['sd'].strftime('%Y%m%d')), 
					end_date = convert_date(obj['ed'].strftime('%Y%m%d')),
					landing_page = pages_json,
					overview = organic_json 
				)
				return daily_report
				
		except Exception as e:
			raise e

		return None 
############################ NON ECOM SERIALIZER METHODS - CLOSES ############################