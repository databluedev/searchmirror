# TESTING PURPOSE AND INITIATIVE
from django.shortcuts import render
from django.conf import settings 

from project.machine.serializers import GroupTimeSerializer as _gp__time__collect_
from rest_framework_mongoengine import viewsets as meviewsets

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings, KeywordHistory, Accountusage, BrandTracker
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_
from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine import parser as _at__parser_, mobileparser as _at__marser_

from datetime import datetime, date
from bs4 import BeautifulSoup
import sys, os, random 
from urllib.parse import urlparse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from django.db.models import Func
from project.machine import automation_daily_start as aDS, automation_engine as aE, parser 
from project.machine.competitor import automation_comp_reload as _aCR_

import base64

def mobile_test():
	try:
		keywords = ["pit bike enduro"] 

		for keyWord in keywords:
			engineParseDataResult = "" 
			scrapRawData = ""
			rankCount = 0
			soupData = ""

			postDataValues = {}
			postDataValues['exactdomain'] = False
			# postDataValues['id'] = 89669
			postDataValues['id'] = 10805
			postDataValues['fk_group_id'] = 3676
			postDataValues['fk_user_id'] = 3716
			postDataValues['language'] = 'es'
			postDataValues['isocode'] = 'es'

			# postDataValues['target'] = "pit-bikes.es"     
			postDataValues['target'] = "https://www.thefamilyvoyage.com"

			postDataValues['se_name'] = "google.es" 
			postDataValues['device'] = "mobile"  
			postDataValues['language_name'] = "Spanish (Spain)" 
			postDataValues['location_name'] = "(Spain)" 
			postDataValues['keyword'] = keyWord  

			searchFile = ""

			if keyWord == "pit bike enduro": 
				searchFile = os.getcwd()+"/project/files/mobile/searchFile__"+str(postDataValues['id'])+".html"
			else:
				print("KEYWORD MISMATCH") 

			if len(searchFile):
				with open(searchFile) as reader:
					soupData = reader.read().strip() 
			else:
				print("FILE FAILED")

			if soupData != "": 
				_kw_id_ = postDataValues['id']
				startTime = datetime.now() 
				soup = BeautifulSoup(soupData, "html.parser")

				if _at__proxy_.__automation_page_validation__("ENGINE", soup, _kw_id_) == True:
					_at__marser_.engineParseData("ENGINE", soup, postDataValues)
					engineParseDataResult = "OKAY" 
					# engineParseDataResult = engineParseData("ENGINE", soup, postDataValues)
				else:
					engineParseDataResult = "NOT OKAY"
				
				endTime = datetime.now()  
				print('RESULT '+str(engineParseDataResult)+' START TIME = '+str(startTime)+' END TIME = '+str(endTime))    
			else:
				print("No Soup Data Exist") 

	except Exception as e:
		print("EXCEPTION - ", str(e))

	return False

def canonical_code(number_value):
	try:
		if number_value:
			number_value = str(number_value)
			canonical_char_code = {"4": "E", "5": "F", "6": "G", "7": "H", "8": "I", "9": "J", "10": "K", "11": "L", "12": "M", "13": "N", "14": "O", "15": "P", "16": "Q", "17": "R", "18": "S", "19": "T", "20": "U", "21": "V", "22": "W", "23": "X", "24": "Y", "25": "Z", "26": "a", "27": "b", "28": "c", "29": "d", "30": "e", "31": "f", "32": "g", "33": "h", "34": "i", "35": "j", "36": "k", "37": "l", "38": "m", "39": "n", "40": "o", "41": "p", "42": "q", "43": "r", "44": "s", "45": "t", "46": "u", "47": "v", "48": "w", "49": "x", "50": "y", "51": "z", "52": "0", "53": "1", "54": "2", "55": "3", "56": "4", "57": "5", "58": "6", "59": "7", "60": "8", "61": "9", "62": "-", "63": ".", "64": "A", "65": "B", "66": "C", "67": "D", "68": "E", "69": "F", "70": "G", "71": "H", "72": "I", "73": "J", "76": "M", "83": "T", "89": "L"}
			return canonical_char_code[number_value] if number_value in  canonical_char_code else None
	except Exception as e:
		pass

	return None

def generate_uule(location: str) -> str:
	uule = None
	try:
		if location:
			canonical_value = canonical_code(len(location))

			if canonical_value:
				prefix = "w+CAIQICI" + str(canonical_value)
				encoded_location = base64.urlsafe_b64encode(location.encode("utf-8")).decode("utf-8")
				uule = str(prefix.strip()) + str(encoded_location.strip())
				uule = uule.rstrip('=')
	except Exception as e:
		pass

	return uule

def find_location(location: str) -> str:
	result = None

	try:
		if location:
			start = location.find('(')  
			end = location.find(')')    
			if start != -1 and end != -1:
				result = location[start+1:end].strip() 
	except Exception as e:
		pass

	return result 

@api_view(['GET'])  
def testing(request):
	startTime = datetime.now()
	params_url = None 
	# location = "google.com"  
	
	# if location:
	# 	get_location = find_location(location)

	# 	print("get_location ", get_location)
	# 	if get_location:
	# 		params_url = generate_uule(get_location)

	# if not params_url:
	# 	params_url = "static url"
	

	# _kw__task_ = Keyword.objects.filter(isocode = "ae").order_by('+auto_refresh_count').all()[0:1] 

	# for _kw__single__task_ in _kw__task_:
	# 	params_url = _at__proxy_.__automation_search_scrap_url__(_kw__single__task_) 

	endTime = datetime.now() 
	
	return JsonResponse({'pflag':params_url, "st": startTime, "et": endTime, "taken": str(date.today())})
