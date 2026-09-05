import os
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.decorators import api_view, permission_classes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from django.template import RequestContext 
from datetime import date,datetime,timedelta
from django.conf import settings

from serp.models import Keyword, Groups, Settings as MainSettings 
from account.cron_auth import cron_only

emergencyMail = [m for m in os.environ.get("EMERGENCY_MAIL", "").split(",") if m] 
coreSubjectAlert = "Tracker Live WatchDog Alert"

def proxyExceedsMailAlert():
	global emergencyMail, coreSubjectAlert
	settingsData = MainSettings.objects.filter(id=1).first()
	if settingsData:
		if settingsData.automation_keyword_exceeds_mail_status == "ready":
			try:
				keywordData = Keyword.objects.filter(auto_refresh_count__gt=5).all() 
				kIds = []
				if keywordData:
					for kdata in keywordData:
						kIds.insert(0, kdata.id)

				context = {
					'alert':coreSubjectAlert, 
					'date':datetime.strftime(datetime.now(), '%B %d, %Y - %H:%M:%S GMT +00.00'),
					'username':"Team", 
					'device':" - ", 
					'condition':"Critical", 
					'mode':"Engine Automation",  
					'key':" - ",  
					'subject':"Proxy Count Exceeds",
					'message':"Proxy count exceeds over the limit of 5 for certain keywords during engine automation", 
					'description':"Proxy exceeds for these keywords and their ids are: " + str(kIds), 
				}
				email_html_message = render_to_string('email/watchdog.html', context)  
				msg = EmailMultiAlternatives(
					coreSubjectAlert, 
					# message:
					"PROXY EXCEEDS LIMIT",
					# from:
		        	settings.HOST_MAIL,  
					# to:
					emergencyMail  
				)
				msg.attach_alternative(email_html_message, "text/html") 
				
				if msg.send():
					MainSettings.objects.filter(id=1).update(automation_keyword_exceeds_mail_status=str(datetime.now())) 

			except Exception as e:
				pass
	return True

@cron_only
def instantMailAlert(request): 
	proxyExceedsMailAlert()
	return JsonResponse({'status':'true','message':"Recorded"}) 

@api_view(['POST'])
def mailpage(request): 
	if request.method == 'POST': 
		coresubject = request.POST['alert']  
		email = request.POST['email']

		context = {
			'alert':coresubject, 
			'date':request.POST['date'],
			'username':request.POST['username'],
			'device':request.POST['device'], 
			'condition':request.POST['condition'], 
			'mode':request.POST['mode'],  
			'key':request.POST['key'], 
			'subject':request.POST['subject'], 
			'message':request.POST['message'], 
			'description':request.POST['description'],   
		}
		email_html_message = render_to_string('email/watchdog.html', context)  
		msg = EmailMultiAlternatives(
			coresubject, 
			# message:
			"Welcome Content",
			# from:
        	settings.HOST_MAIL, 
			# to:
			email.split(",") 
		)
		msg.attach_alternative(email_html_message, "text/html") 
		msg.send()
		return JsonResponse({'status':'true','message':"Welcome mail send to successfully"})
	else: 
		return JsonResponse({'status':'fail','message':"Something went wrong"})
	