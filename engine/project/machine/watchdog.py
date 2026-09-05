from django.shortcuts import render
from django.conf import settings 

from rest_framework_mongoengine import viewsets as meviewsets 
from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings, Accountusage 

import requests, json, time, csv
from bs4 import BeautifulSoup
from urllib import parse 
import sys, os, random
from datetime import datetime, date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse

from urllib.parse import urlparse 
from threading import Timer

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail

from project.machine import formulate
 
emergencyMail = settings.EMERGENCY_MAIL
coreSubjectAlert = settings.CORE_SUBJECT_ALERT
mailToken = settings.MAIL_TOKEN
siteUrl = settings.SITE_URL
apiGoogleLink = settings.API_GOOGLE_LINK
# apiDailyMail = "/mailsystem/automation-trigger"


def checkDog(params): 
	return "tracker V4.4.4.0 LIVE ENGINE "+str(params)

def sendCoreMessage(params):     
	settingData = Mainsettings.objects.filter(__raw__= {'id': 1}) 
	if settingData[0].core_mode == True:   
		settingData.update( 
			core_mode=False,
			core_manual_mode=False,
			modified_date=datetime.now()
		)
		return "Deactivated"
	else:  
		settingData.update( 
			core_mode=True,
			core_manual_mode=True,
			modified_date=datetime.now()
		)
		return "Activated"
	# return formulate.resetDashboard()
	# return formulate.dashboardNewGraph('ENGINE', 0)      
	# return formulate.sampleCheck('MANUAL', 33)

def coreLog(line, systemMode):
	if line == "LINE":
		repeats = "~~" * 100
		line = str(repeats) 
	else:
		line = coreGetDateTime() + str(systemMode) + str(line) 

	if systemMode == "ENGINE":
		searchFile = os.getcwd()+"/logs/engine/engine-"+str(date.today())+".log"  
	elif systemMode == "MANUAL":
		searchFile = os.getcwd()+"/logs/manual/manual-"+str(date.today())+".log"
	elif systemMode == "BRAND":
		searchFile = os.getcwd()+"/logs/brand/brand-"+str(date.today())+".log"
	elif systemMode == "COMPETITOR":
		searchFile = os.getcwd()+"/logs/competitor/competitor-"+str(date.today())+".log" 
	elif systemMode == "COMPALYSE":
		searchFile = os.getcwd()+"/logs/competitor/compalyse-"+str(date.today())+".log"
	elif systemMode == "RESEARCH":
		searchFile = os.getcwd()+"/logs/research/research-"+str(date.today())+".log"
	elif systemMode == "ERROR":
		searchFile = os.getcwd()+"/logs/error/error-"+str(date.today())+".log" 
	elif systemMode == "PROXY":
		searchFile = os.getcwd()+"/logs/proxy/proxy-"+str(date.today())+".log" 
	else:
		searchFile = os.getcwd()+"/logs/other/other-"+str(date.today())+".log" 

	# The per-mode log directories are not in the image, and the container
	# command only creates their parent -- so every coreLog call used to raise
	# FileNotFoundError and take the whole engine request down with it.
	os.makedirs(os.path.dirname(searchFile), exist_ok=True)

	if not os.path.exists(searchFile):
		with open(searchFile, 'w'): pass 
	with open(searchFile, 'r+') as f:
		content = f.read()
		f.seek(0, 0)
		f.write(line.rstrip('\r\n') + '\n' + content) 
	return True    

def coreGetDateTime():
	return " "+str(datetime.strftime(datetime.now(), 'GMT %b|%d|%Y-%H:%M:%S'))+" => "

def firstCallOfTheDay(systemMode): 
	Keyword.objects.update( 
		auto_refresh_count=0,
		strict_refresh_count=0
	)  
	settingData = Mainsettings.objects.filter(__raw__= {'id': 1}).update(
		push__daily_automation_count__0=0,
		push__daily_demand_count__0=0, 
	)

	# OnDemand Refresh Reset Count
	currdate = date.today() 
	settingData = Mainsettings.objects.filter(__raw__= {'id': 1}).first()
	if (settingData.core_refresh_time.date() < currdate): 
		Accountusage.objects.update(used_refresh_limit=0, modified_date=datetime.now())     
		coreLog(" > ACCOUNT USAGE LIMIT RESET DONE ", systemMode) 

	return True 

def coreCondition(systemMode, problemStatus, postData):
	# UPDATE HAPPENED AT EVERY FIRST CALL OF ENGINE 
	settingData = Mainsettings.objects.filter(__raw__= {'id': 1}).first()
	currdate = date.today() 
	if systemMode == "ENGINE": 
		if settingData.core_refresh_time.date() < currdate:     
			firstCallOfTheDay(systemMode)
			Mainsettings.objects.filter(__raw__= {'id': 1}).update(core_manual_mail=True, modified_date=datetime.now(), core_refresh_time=datetime.now())
			coreLog(" > SETTINGS RESET DONE ", systemMode)    
		else: 
			coreLog(" > NOT THE FIRST CALL OF THE DAY ", systemMode) 

	if settingData.core_mode == True:
		if problemStatus == 1 and systemMode == "ENGINE":   				# GOOGLE PAGE ERROR
			# The engine is NOT switched off here. core_mode / core_manual_mode
			# live on a single settings row with no tenant on it, so one
			# account's bad response used to disable ranking for every account
			# on the instance -- permanently, because nothing switches them
			# back on. A bad response is recorded against the keyword that
			# produced it (attempt counted, retry scheduled, terminal only once
			# the budget is spent); the operator still gets the alert below.
			# Copy records
			coreCopyRecords(systemMode, 'error')
			# RE-FORMAULATE GROUP ACTIVITY, SCORE METER AND SINCE START CALCULATION.
			formulate.dashboardNewGraph("ENGINE", 0)
			# Watch Dog mail
			coreDogReport(problemStatus, systemMode, postData)       
			# Maintain Log 
			coreLog(" > GOOGLE PAGE ERROR >> KEY_ID "+str(postData['id'])+" >>> GROUP_ID "+str(postData['fk_group_id']), systemMode) 
			return "page failed" 

		elif problemStatus == 1 and systemMode == "MANUAL":    				# GOOGLE PAGE ERROR
			# Same reason as the ENGINE branch above: core_manual_mode is one
			# global row, so latching it off here took instant refresh away
			# from every account on the instance and nothing ever restored it.
			coreManualMail(False)

			coreChangeManualCallStatusGroup(False, "done", postData)
			# RE-FORMAULATE GROUP ACTIVITY, SCORE METER AND SINCE START CALCULATION.
			formulate.dashboardNewGraph("MANUAL", postData['fk_group_id'])  

			coreChangeManualCallStatus(False, "done", postData)     

			if settingData.core_manual_mail == True:
				# Watch Dog mail	true
				coreDogReport(problemStatus, systemMode, postData)  
				# Maintain Log 
				coreLog(" > GOOGLE PAGE ERROR >> KEY_ID "+str(postData['id'])+" >>> GROUP_ID "+str(postData['fk_group_id']), systemMode) 
				return "page failed"  
			else: 
				return "page failed"  
		else:
			return True      

	elif settingData.core_mode == False:
		if systemMode == "ENGINE":   				# AUTOMATION CALL 
			# Copy records
			coreCopyRecords(systemMode, 'error')
			# RE-FORMAULATE GROUP ACTIVITY, SCORE METER AND SINCE START CALCULATION.
			formulate.dashboardNewGraph("ENGINE", 0) 
			# Watch Dog mail
			coreDogReport(problemStatus, systemMode, postData)

			# Maintain Log 
			coreLog(" > SETTINGS TURNED OFF ", systemMode) 
			return False
		elif systemMode == "MANUAL":              	# MANUAL CALL
			if settingData.core_manual_mail == True:
				coreManualMail(False)   
				# Watch Dog mail
				coreDogReport(problemStatus, systemMode, postData)      
				# Maintain Log 
				coreLog(" > SETTINGS TURNED OFF ", systemMode)   
				return False
			else: 
				return False 
		else: 
			# Watch Dog mail
			coreDogReport(0, 'MALICIOUS', "NOPOSTDATA")
			# Maintain Log 
			coreLog(" > SETTINGS TURNED OFF ", "MALICIOUS")   
			return False
	else:
		# Watch Dog mail
		coreDogReport(0, 'VIRAL', "NOPOSTDATA")
		# Maintain Log 
		coreLog(" > SETTINGS TURNED OFF ", "VIRAL") 
		return False 


def coreChangeManualCallStatusGroup(callstatus, status, currentData):   
	Keyword.objects.filter(manual_call_status = True, fk_group_id = currentData['fk_group_id']).update(manual_call_status=callstatus, manual_call_mode=status, manual_task_allocation="-")      
	Group.objects.filter(__raw__= {'id': currentData['fk_group_id']}).update(strict_refresh_switch=False, manual_grp_trigger="DONE")
	return True

def coreChangeManualCallStatus(callstatus, status, currentData):      
	ManualRefresh.objects.filter(fk_group_id = currentData['fk_group_id']).update(refresh_time=datetime.now(), refresh_status = "done") 
	return True

def coreManualMail(status):
	settingData = Mainsettings.objects.filter(__raw__= {'id': 1})
	if settingData and (status == True or status == False):
		settingData.update( 
			core_manual_mail=status,
			modified_date=datetime.now() 
		) 
		return True  
	else:
		return False  

def coreCopyRecords(systemMode, currentData):
	currdate = date.today()
	keywordsCount = Keyword.objects.count()

	if keywordsCount > 0:  
		# Maintain Log 
		coreLog(" > STARTED COPYING RECORDS ", systemMode)

		if currentData == "error":
			allKeywords =  Keyword.objects.all()  
		else: 
			allKeywords =  Keyword.objects.filter(manual_call_status = True, fk_group_id = currentData['fk_group_id']).all()

		for keyIns in allKeywords:  
			if keyIns:    
				singleKeywordData =  Keyword.objects.filter(__raw__= {'id': keyIns.id}) 
				if singleKeywordData:
					singleKeyword = singleKeywordData[0]
					rankArrayCount = len(singleKeyword.rank) 
					keywordTotalDayCount = int((currdate - singleKeyword.created_date.date()).days) + 1
				
					if rankArrayCount < keywordTotalDayCount and len(singleKeyword.rank) > 0: 
						coreLog(" > COPYING >> KEY_ID "+str(keyIns.id), systemMode) 
						prevRank = singleKeyword.rank[0]
						while(rankArrayCount < keywordTotalDayCount): 
							singleKeywordData.update( 
								push__rank__0=prevRank
							) 
							rankArrayCount += 1  

						singleKeywordData.update(  
							ranknow=prevRank, 
							daymark = '-',
							dayval = 0,
							weekmark = '-',
							weekval = 0,
							monthmark = '-',
							monthval = 0, 
							halfmonthmark = '-',
							halfmonthval = 0, 
							lastranked_date=datetime.now(),  
							updated_date=datetime.now() 
						)
		# Maintain Log 
		coreLog(" > COMPLETED COPYING RECORDS ", systemMode)
		return True
	else:
		coreLog(" > ZERO COPYING RECORDS ", systemMode)
		return False   


def coreDogReport(mode, systemMode, postData):
	global coreSubjectAlert
	global emergencyMail 

	coreSystemMode = "" 
	engine_mode = "DISABLED" 

	if systemMode == "ENGINE":
		coreSystemMode = "Engine Automation"
	elif systemMode == "MANUAL":
		coreSystemMode = "Manual Refresh"   
	elif systemMode == "MALICIOUS":
		coreSystemMode = "Malicious"
	elif systemMode == "VIRAL":
		coreSystemMode = "Viral" 
	else: 
		coreSystemMode = "No System"  

	dogMailData = "-"
	platformBasis = "-"
	if postData != "NOPOSTDATA":
		dogMailData = str(postData['id']) 
		platformBasis = str(postData['platform'])


	if mode == 0: 	    # Engine Enable/Disable
		context = {
			'email': emergencyMail,
			'alert': coreSubjectAlert,
			'date': datetime.strftime(datetime.now(), '%B %d, %Y - %H:%M:%S GMT +00.00'),
			'username': 'Team',
			'device': platformBasis,
			'condition': 'Critical',
			'mode': coreSystemMode,   
			'key': dogMailData,   
			'subject': 'Engine Turned OFF',   
			'message': 'Today, I have analysed the engine is powered OFF. So, I can’t able to do any process. Since, i have formulated some procedures in actions. Kindly, please ignore any development work under progress.',
			'description': 'I think due to some development process, someone has temporarily disabled Engine System. So, I have set previous day information like rank, snippets and other essentials to the present day records for all unprocessed keywords.',
		}  

		return coreDogMail(context)
	elif mode == 1:		# Google Page Format changed	
		context = { 
			'email': emergencyMail,
			'alert': coreSubjectAlert,
            'date': datetime.strftime(datetime.now(), '%B %d, %Y - %H:%M:%S GMT +00.00'), 		
			'username': 'Team',
			'device': platformBasis,
			'condition': 'Critical',
			'mode': coreSystemMode,  
			'key': dogMailData,
			'subject': 'Google has updated the page structure (format)',
			'message': 'Today, I have analysed the google page results and noticed that the page format has completely changed its hierarchy order. So, I can’t able to process the google results. Since, i have formulated some procedures in actions.',
			'description': 'I have temporarily '+engine_mode+' the Automation and Daily refresh (Manual) request. For all unprocessed keywords, I have set previous day information like rank, snippets and other essentials to the present day records.',
		} 
		return coreDogMail(context) 
	else: 
		context = {
			'email': emergencyMail,
			'alert': coreSubjectAlert, 
			'date': datetime.strftime(datetime.now(), '%B %d, %Y - %H:%M:%S GMT +00.00'),
			'username': 'Team',
			'device': platformBasis,
			'condition': 'Critical',
			'mode': coreSystemMode, 
			'key': dogMailData, 
			'subject': 'Engine Turned OFF',   
			'message': 'Today, I have analysed the engine is powered OFF. So, I can’t able to do any process. Since, i have formulated some procedures in actions. Kindly, please ignore any development work under progress.',
			'description': 'I think due to some development process, someone has temporarily disabled Engine System. So, I have set previous day information like rank, snippets and other essentials to the present day records for all unprocessed keywords.',
		}  

		return coreDogMail(context)
		
def coreDogMail(context):
	global mailToken, apiGoogleLink, siteUrl 
	connectUrl = siteUrl+apiGoogleLink
	if context: 
		headers = {'Authorization': mailToken} 
		x = requests.post(connectUrl, data=context, headers=headers) 

		return str(x.status_code) 

# def dailyMailTrigger(params):
# 	global mailToken, apiDailyMail, siteUrl 
# 	connectUrl = siteUrl+apiDailyMail
# 	context = {}
	
# 	if params == "NEW-VERSION-RELEASE":
# 		context = {
# 			'automationNotify': date.today().strftime("%Y-%m-%d"),
# 			'funcNotify': 'NEW-VERSION-RELEASE'
# 		}
# 	elif params == "DAILY-AUTOMATION":
# 		context = {
# 			'automationNotify': date.today().strftime("%Y-%m-%d"),
# 			'funcNotify': 'DAILY-AUTOMATION'
# 		} 
# 	elif params == "MANUAL-AUTOMATION":
# 			context = {
# 				'automationNotify': date.today().strftime("%Y-%m-%d"),
# 				'funcNotify': 'MANUAL-AUTOMATION'
# 			}  

# 	if bool(context):
# 		x = "ERROR"
# 		try:
# 			headers = {'Authorization': mailToken} 
# 			x = requests.post(connectUrl, data=context, headers=headers)   
# 		except:
# 			pass

# 	return x.text  

 