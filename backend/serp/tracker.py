from django.shortcuts import render
from django.conf import settings
from serp.models import *  
from account.models import Account 
from datetime import date, datetime, timedelta
from serp import user_timezone as uTZ 
import sys, os, random, time
import requests 

def userTrackerExist(user_id):
	if user_id != 1: 
		trackerCount = clientTracker.objects.filter(fb_user_id=user_id).exists() 
		return trackerCount

	return True

def userTrackerRequest(request, user_id):
	try:
		ip = None 
	
		if user_id and request:
			trackerExists = clientTracker.objects.filter(fb_user_id=user_id).exists()
			if trackerExists: 
				trackerData = clientTracker.objects.filter(fb_user_id=user_id).first() 
				if trackerData:
					ip = trackerData.client_ip
			
			if ip == None and int(user_id) != 1: 
				clientIp = None

				x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
				if x_forwarded_for:
					clientIp = x_forwarded_for.split(',')[0]
				else:
					clientIp = request.META.get('REMOTE_ADDR') 

				if clientIp:
					reqAgent = request.META['HTTP_USER_AGENT'] 
					trackerIns = clientTracker()
					trackerIns.fb_user_id = user_id
					trackerIns.client_ip = clientIp
					trackerIns.client_agent = reqAgent
					trackerIns.status = "START" 
					trackerIns.save() 
					
	except Exception as e:
		pass 
	
	return True 

def fetchAgent():
	agentHeadersList = [
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0",
		"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
		"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"
	]

	listIndex = random.randint(0,len(agentHeadersList)-1)
	return agentHeadersList[listIndex]

def automateRequestCall():
	try:
		trackerStartData = clientTracker.objects.filter(status="START").first()

		if trackerStartData:
			if hasattr(trackerStartData, 'client_ip'): 
				clientTracker.objects.filter(id=trackerStartData.id).update(status="BUSY", modified_date=datetime.now())

				headers = { 
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/gif,image/png,image/webp,image/jpeg,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
					"Accept-Encoding": "gzip",
					"Accept-Language": "en-GB;q=0.9,en;q=0.8",
					"Dnt": "1", 
					"Upgrade-Insecure-Requests": "1", 
					'User-Agent': fetchAgent()  
				}
				
				# URL = "http://ip-api.com/json/"+str(trackerStartData.client_ip)
				URL = "http://ip-api.com/json/"+str(trackerStartData.client_ip)+"?fields=66842623&lang=en"
				resp = requests.get(URL, headers = headers)

				if hasattr(resp, 'status_code'): 
					if resp.status_code == 200: 
						ipResults = resp.json()
						if ipResults:
							clientTracker.objects.filter(id=trackerStartData.id).update(
								status = "DONE",
								time_zone = ipResults['timezone'],
								country_code = ipResults['countryCode'],
							    country = ipResults['country'],
							    region = ipResults['region'],
							    city = ipResults['city'],
							    mobile = ipResults['mobile'], 
							    other_info = ipResults, 
							    modified_date = datetime.now()
							) 
							uTZ.TimeZoneUpdate(trackerStartData.fb_user_id, ipResults['timezone'])
							return True
					else:
						clientTracker.objects.filter(id=trackerStartData.id).update(status="FAIL", modified_date=datetime.now())
				else:
					clientTracker.objects.filter(id=trackerStartData.id).update(status="ERROR", modified_date=datetime.now())
			else:
				clientTracker.objects.filter(id=trackerStartData.id).update(status="500", modified_date=datetime.now())

	except Exception as e:
		pass 
 	
	return True



		