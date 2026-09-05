from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.decorators import api_view, permission_classes
# from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse,JsonResponse

from rest_framework.response import Response

from datetime import date,datetime,timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from urllib.parse import urlparse

# Data Models
from serp.models import Keyword,Language,Region,Groups,Feedback,Refreshmanual,Subscriptionplans,Accountusage,Settings,Usersettings,Userregistrationtoken,Referralprogram,searchvolumes as searchvolumemodel, brandTracker, clientTracker, kwNotes
from account.models import Account
from rest_framework.authtoken.models import Token 
from account.authorization.models import ResetPasswordToken 
from serp.serializers import *
from serp.common import totalKeywordsCount
from mailend.serializers import *
from django.db.models import Q 

from mailend.models import KeywordHistory

from django.conf import settings

import os, random

#TimeZone
from pytz import timezone
from dateutil.relativedelta import relativedelta

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

emptyAccountMailLimit = 5

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


# check before release
def pre_Update1():
	for user in Usersettings.objects.all():
		refdatasave = Usersettings.objects.get(id=user.id) 
		refdatasave.email_daily_routine = True
		refdatasave.save(update_fields=['email_daily_routine'])
	return True 

def pre_Update2():
	# Keyword Existing Data Creation Module for Its History. 
	totalKeywords = Keyword.objects.all() 

	for tKey in totalKeywords: 
		KHobjects = KeywordHistory.objects.filter(fk_keyword=tKey.id).count()

		if KHobjects == 0:
			keyIns = {}
			keyIns['fk_keyword'] = tKey.id
			keyIns['fk_user'] = tKey.fk_user_id
			keyIns['fk_group'] = tKey.fk_group_id
			serializer = AccountHistorySerializer(data = keyIns) 
			if serializer.is_valid():
				serializer.save()
	return True

def pre_Update3(): 
	email_notify_update = {
		'daily_routine' : None, 
		'best_score_routine' : None,
		'cannibalisation_routine': None,
		'url_change_routine': None, 
		'no_week_improvement_routine': None,   
		'ratings_change_routine': None,
		'new_ads_routine': None, 
		'new_featured_routine' : None,  
		'score_routine' : None,     
	}

	Groups.objects.filter(id__gt=0).update(automation_email_notify_log=email_notify_update)   
	Accountusage.objects.filter(id__gt=0).update(mail_max_keyword_reach="-") 
	# Account.objects.filter(id__gt=0).update(mail_count_status_no_keyword=0, mail_no_keyword_routine=None)   
	Account.objects.filter(id__gt=0).update(mail_count_status_no_keyword=0)   
	Usersettings.objects.filter(id__gt=0).update(email_daily_routine=True)   
	Keyword.objects.filter(id__gt=0).update(cannibalisation_mail_status="-")   

	return True

def pre_Update4():
	keywords = Keyword.objects.exclude(tags=[]).all()
	sd = []
	if keywords:
		tagKeywords = DashKeywordSerializer(keywords, many=True).data  
		for singleTag in tagKeywords:
			tagsList = list(set(map(lambda x:x.lower(), singleTag['tags'])))
			Keyword.objects.filter(id=singleTag['id']).update(tags=tagsList) 
			sd.append({
				'id': singleTag['id'] 
			}) 
		return sd 
	return False

def pre_Update5():
	for user in Account.objects.all():
		Account.objects.filter(id=user.id).update(mail_count_status_no_keyword=0, mail_no_keyword_routine=user.date_joined) 

def deleteUpdate(uid):  
	Account.objects.filter(id=uid).delete()     
	Accountusage.objects.filter(fb_user_id=uid).delete()      
	Keyword.objects.filter(fk_user_id=uid).delete()  
	kwNotes.objects.filter(fk_user_id=uid).delete()  
	brandTracker.objects.filter(fb_user_id=uid).delete()  
	clientTracker.objects.filter(fb_user_id=uid).delete()  
	Groups.objects.filter(fk_user_id=uid).delete()
	Refreshmanual.objects.filter(fb_user_id=uid).delete()
	Usersettings.objects.filter(fb_user_id=uid).delete()
	Feedback.objects.filter(fb_user_id=uid).delete()
	Referralprogram.objects.filter(userid_id=uid).delete() 
	KeywordHistory.objects.filter(fk_user_id=uid).delete()  
	Report.objects.filter(fb_user_id=uid).delete()
	Token.objects.filter(user_id=int(uid)).delete() 
	ResetPasswordToken.objects.filter(user_id=int(uid)).delete() 

	return "OKKK"  
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# mail footer project setting url create
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def letter_gen():
    letter = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    return letter

def projectSettingURL_gen(userid,grpid,grpname):
	grpname = f"{grpname}".replace(" ", "_")
	# projectSettingURL = ""+ settings.SITE_URL + settings.SITE_SUB_URL + str(userid) + letter_gen() + str(grpid) + '/' + grpname + '/settings'
	projectSettingURL = ""+ settings.SITE_URL + '/settings/' + grpname + '/' + str(grpid)
	return projectSettingURL

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Log file
def coreGetDateTime():
    return " "+str(datetime.strftime(datetime.now(), 'GMT %b|%d|%Y-%H:%M:%S'))+" => "

def coreLog(line):
    line = coreGetDateTime() + str(line) 
    searchFile = os.getcwd()+"/logs/automation_mail.log" 

    if not os.path.exists(searchFile):
        with open(searchFile, 'w'): pass 
    with open(searchFile, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content) 
    return True

# Called From Engine
@api_view(['POST'])
def automationTrigger(request):
	if request.method == 'POST':
		notifyTime = request.POST['automationNotify'] 		
		funCall = request.POST['funcNotify'] 
		SettingData = Settings.objects.filter(id=1).first() 
		if SettingData:
			if SettingData.core_manual_mode == True and str(SettingData.core_refresh_time) == notifyTime:
				if funCall == "NEW-VERSION-RELEASE":
					# mail_new_release()  
					return HttpResponse("success - mail_new_release")
				elif funCall == "DAILY-AUTOMATION":
					# call Automation Function
					# automationFunction('CORE') 
					return HttpResponse("success - mail_daily_service")
				elif funCall == "MANUAL-AUTOMATION":
					# manual call Automation Function  
					automationFunction('MANUAL', 7) 
					return HttpResponse("success - mail_manual_service")

		return HttpResponse("failed")
	else:
		# return render_to_response('error.html', { "data": "Access Denied"})
		return render(request,'error.html', {"data":"Access Denied"})

def userBasedAutomationMail(request):
	# accusgIns = Accountusage.objects.filter(fb_user_id=1,automatic_mail_status="START").first()
	accusgIns = Accountusage.objects.exclude(fb_user_id=1).filter(automatic_mail_status="START", status__in=["active","default"]).first() 
	if accusgIns:
		# accusgIns.update(automatic_mail_status="SCHD")
		accusgIns.automatic_mail_status = "SCHD"
		accusgIns.save(update_fields=['automatic_mail_status'])
		coreLog(str(accusgIns.fb_user_id) +' AUTOMATION MAIL STATUS - SCHD')

		result = automationFunction('MANUAL', accusgIns.fb_user_id)
		list_value = list(result.values())
		if "try error" in list_value or "failed" in list_value:
			accusgIns.automatic_mail_status = "FAIL"
			coreLog(str(accusgIns.fb_user_id) +' AUTOMATION MAIL STATUS - FAIL')
		else:
			accusgIns.automatic_mail_status = "COMP"
			coreLog(str(accusgIns.fb_user_id) +' AUTOMATION MAIL STATUS - COMP')

		accusgIns.save(update_fields=['automatic_mail_status'])       
		return True

	# currentDay = date.today().day
	# if currentDay == 16 or currentDay == 1:   
	# 	Output = mail_account_without_keywords()
	# 	return True 

	return False 

def testmails(request, file, subjects): 
	currdate = date.today() 
	subject = subjects 
	uMail = os.environ.get("ALERT_MAIL", "")
	context = {
		"acc_id" : 0, 
		"today": currdate.strftime("%b %d, %Y"), 
		"username": "Asath", 
		"email": uMail,
		'siteurl': settings.SITE_URL,
		'serivceurl': settings.SERVICE_URL,
	} 
	# Change to User Email
	toMail = [uMail] 
	
	mailDatas = sendMail(file, context, subject, toMail) 					
	return True 

def automationFunction(system, mid=None):
	# mid - it should be user id 
	returnOutput = {}
	returnOutput['empty'] = "nothing"
	
	returnOutput['daily'] = mail_scheduled_daily(system, mid) 
	returnOutput['best'] = mail_best_tracker_score(system, mid)
	returnOutput['canni'] = mail_cannibalisation(system, mid)
	returnOutput['url'] = mail_changes_url(system, mid)
	returnOutput['week'] = mail_no_improvements_in_week(system, mid)
	returnOutput['rating'] = mail_change_in_ratings(system, mid)
	returnOutput['ads'] = mail_ads_snippet(system, mid)
	returnOutput['featured'] = mail_featured_snippet(system, mid)
	returnOutput['score'] = mail_tracker_score_alert(system, mid)
	returnOutput['brands'] = mail_brand_acquisition(system, mid)

	# version 3.0 in referal option remove so max keyword mail disabled.
	# returnOutput['reach'] = mail_max_keywords_reach(system, mid)
	returnOutput['reach'] = "nothing" 

	coreLog(str(mid) +' AUTOMATION MAIL RESULT - Daily > '+str(returnOutput['daily'])+' - Best > '+str(returnOutput['best'])+' - Canni > '+str(returnOutput['canni'])+' - Url > '+str(returnOutput['url'])+' - Week > '+str(returnOutput['week'])+' - Rating > '+str(returnOutput['rating'])+' - Ads > '+str(returnOutput['ads'])+' - Featured > '+str(returnOutput['featured'])+' - Score > '+str(returnOutput['score'])+' - Reach > '+str(returnOutput['reach'])+' - Empty > '+str(returnOutput['empty'])) 
	return returnOutput 

def automationRepeatCheck(system, uid, gid, autoTag):
	val = False
 
	if system:
		grpData = Groups.objects.filter(fk_user_id=uid, id=gid).first() 
		# The project can be deleted between scheduling the mail and sending it.
		if grpData is None:
			return val
		if bool(grpData.automation_email_notify_log):
			singleData = grpData.automation_email_notify_log
			singleFlag = "-"
			if 'daily_routine' in singleData and autoTag == "s-daily": 
				singleFlag = singleData['daily_routine']
				if singleData['daily_routine'] != None:
					keyTime = singleData['daily_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'best_score_routine' in singleData and autoTag == "s-bestscore": 
				singleFlag = singleData['best_score_routine']
				if singleData['best_score_routine'] != None:
					keyTime = singleData['best_score_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'cannibalisation_routine' in singleData and autoTag == "s-cannib": 
				singleFlag = singleData['cannibalisation_routine']
				if singleData['cannibalisation_routine'] != None:
					keyTime = singleData['cannibalisation_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True    
			elif 'url_change_routine' in singleData and autoTag == "s-url": 
				singleFlag = singleData['url_change_routine']
				if singleData['url_change_routine'] != None:
					keyTime = singleData['url_change_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'no_week_improvement_routine' in singleData and autoTag == "s-noimprovement": 
				singleFlag = singleData['no_week_improvement_routine']
				if singleData['no_week_improvement_routine'] != None:
					keyTime = singleData['no_week_improvement_routine'].split(" ")
					if len(keyTime) == 2:
						lastDate = datetime.strptime(keyTime[0], "%Y-%m-%d") 
						diffToday = (date.today() - lastDate.date()).days
						val = True if int(diffToday) >= 7 else False   # CHANGE WEEKLY MAIL COUNT 
			elif 'ratings_change_routine' in singleData and autoTag == "s-rating": 
				singleFlag = singleData['ratings_change_routine']
				if singleData['ratings_change_routine'] != None:
					keyTime = singleData['ratings_change_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'new_ads_routine' in singleData and autoTag == "s-ads": 
				singleFlag = singleData['new_ads_routine']
				if singleData['new_ads_routine'] != None:
					keyTime = singleData['new_ads_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'new_featured_routine' in singleData and autoTag == "s-featured": 
				singleFlag = singleData['new_featured_routine']
				if singleData['new_featured_routine'] != None:
					keyTime = singleData['new_featured_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'score_routine' in singleData and autoTag == "s-score": 
				singleFlag = singleData['score_routine']
				if singleData['score_routine'] != None:
					keyTime = singleData['score_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
			elif 'new_brandads_routine' in singleData and autoTag == "s-brands": 
				singleFlag = singleData['new_brandads_routine']
				if singleData['new_brandads_routine'] != None:
					keyTime = singleData['new_brandads_routine'].split(" ")
					if len(keyTime) == 2:
						todayDate = date.today().strftime("%Y-%m-%d") 
						val = False if str(keyTime[0]) == str(todayDate) else True
						
			# Still None
			if singleFlag == None:
				val = True

	return val 

# group Mail Update
def mailLogUpdate(uid, gid, autoTag): 
	grpData = Groups.objects.filter(fk_user_id=uid, id=gid).first()
	if hasattr(grpData, 'automation_email_notify_log'):
		saveData = grpData.automation_email_notify_log 
		if autoTag == "s-daily":
			if 'daily_routine' in saveData:
				saveData['daily_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'daily_routine': str(datetime.now())
				})
		elif autoTag == "s-bestscore":
			if 'best_score_routine' in saveData:
				saveData['best_score_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'best_score_routine': str(datetime.now())
				})
		elif autoTag == "s-cannib":
			if 'cannibalisation_routine' in saveData:
				saveData['cannibalisation_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'cannibalisation_routine': str(datetime.now())
				})
		elif autoTag == "s-url":
			if 'url_change_routine' in saveData:
				saveData['url_change_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'url_change_routine': str(datetime.now())
				})
		elif autoTag == "s-noimprovement":
			if 'no_week_improvement_routine' in saveData:
				saveData['no_week_improvement_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'no_week_improvement_routine': str(datetime.now())
				})
		elif autoTag == "s-rating":
			if 'ratings_change_routine' in saveData:
				saveData['ratings_change_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'ratings_change_routine': str(datetime.now())
				})
		elif autoTag == "s-ads":
			if 'new_ads_routine' in saveData:
				saveData['new_ads_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'new_ads_routine': str(datetime.now())
				})
		elif autoTag == "s-featured":
			if 'new_featured_routine' in saveData:
				saveData['new_featured_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'new_featured_routine': str(datetime.now())
				})
		elif autoTag == "s-score":
			if 'score_routine' in saveData:
				saveData['score_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'score_routine': str(datetime.now())
				})
		elif autoTag == "s-brandads":
			if 'new_brandads_routine' in saveData:
				saveData['new_brandads_routine'] = str(datetime.now())
			else: 
				saveData.update({
					'new_brandads_routine': str(datetime.now())
				})

		Groups.objects.filter(fk_user_id=uid, id=gid).update(automation_email_notify_log=saveData) 

	return True

#Check premium user
def CheckPremiumUser(id):
	add_recipient_mail = False
	accountData = Accountusage.objects.filter(fb_user_id=id).values('st_subscription_id','st_user_mail', 'st_customer_id', 'st_purchase_id').first() 
	if accountData['st_customer_id'] != None and accountData['st_subscription_id'] != None and accountData['st_user_mail'] != None and accountData['st_purchase_id'] > 0:
		add_recipient_mail = True
	return add_recipient_mail

# Mail Function
def sendMail(template, context, subject, receiver): # 000 
	email_html_message = render_to_string(template, context)
	msg = EmailMultiAlternatives(
		subject, 
		# message:
		"Welcome Content",
		# from:
        settings.HOST_MAIL,
		# to:
		receiver
	)
	msg.attach_alternative(email_html_message, "text/html") 
	return msg.send()

# Refine domain name from the URL
def extract_domain(url, remove_http=True):
	uri = urlparse(url)
	if remove_http:
		if uri.netloc: 
			domain_name = f"{uri.netloc}".replace("www.", "") 
		else:
			domainDivision = f"{uri.path}".replace("www.", "").split('/')
			domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision    
	else:
		domain_name = f"{uri.netloc}".replace("www.", "") 
	return domain_name

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Tracker score alert - STARTS
def mail_tracker_score_alert(system, mid = None):  # 222
	scoreReturn = "nothing"

	try:
		allAccounts = Account.objects.filter(id=mid).all() 

		if allAccounts:
			scoreAlertData = MailGroupSerializer(allAccounts, many=True, context={'system':system})
			if scoreAlertData:
				filteredScoreData = list(filter(None, scoreAlertData.data)) 
				for singleScore in filteredScoreData:
					SettingsData = Settings.objects.filter(id=1).first()

					grpId = singleScore['acc_group'][0]['gid']
					usrId = singleScore['acc_id']
					reciptmail = singleScore['acc_group'][0]['reciptmail']
					if SettingsData: 
						if SettingsData.core_manual_mode == True:
							currdate = date.today()
							subject = "Your today’s Tracker score status"  
							context = {
								"acc_group" :singleScore['acc_group'], 
								"today": currdate.strftime("%b %d, %Y"),
								"username": singleScore['acc_username'], 
								"acc_email": singleScore['acc_email'],
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL,
							}
							
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleScore['acc_email']) 
								toMail = reciptmail
							else:
								toMail = [singleScore['acc_email']]
													
							mailDatas = sendMail('emails/score_alert.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation. 
								for singleGroup in singleScore['acc_group']:
									mailLogUpdate(usrId, singleGroup['gid'], "s-score") 
								scoreReturn = "success"
							else: 
								scoreReturn = "failed"
	except:
		scoreReturn = "try error" 
		pass

	return scoreReturn 
# Tracker score alert - ENDS

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Daily process - Improved, Declined and Favourite - STARTS
def single_Group_Imp_Dec_Keyword(grpid):
	posKey = Keyword.objects.filter(fk_group_id=grpid, daymark="up").count()
	negKey = Keyword.objects.filter(fk_group_id=grpid, daymark="down").count()
	idleKey = Keyword.objects.filter(fk_group_id=grpid, daymark="-").count()
	totalKey = Keyword.objects.filter(fk_group_id=grpid).count()

	id_data = {} 
	id_data['improved'] = posKey  
	id_data['declined'] = negKey  
	id_data['idle'] = idleKey  
	id_data['total'] = totalKey
		
	return id_data 

def single_Group_Fav_Keyword(grpid): 
	keywords = Keyword.objects.filter(Q(favour=1) & Q(fk_group_id=grpid) & ~Q(daymark="-")).order_by('id')[:5]  
	serializer = []
	if len(keywords) > 0:  
		serializer = MailFavKeywordSerializer(keywords, many=True).data   
	return serializer
	
def mail_scheduled_daily(system, mid = None): # 111
	check = "nothing" 
	try:
		# Daily process - Improved, Declined and Favourite 
		SettingsData = Settings.objects.filter(id=1).first() 
		if SettingsData:
			if SettingsData.core_manual_mode == True:
				allGroups = Groups.objects.filter(fk_user_id=mid).all() 

				for singleGrp in allGroups:
					userswitch = True
					if 'DS' in singleGrp.automation_email_switch: 
						userswitch = singleGrp.automation_email_switch['DS']

					if userswitch == True:

						grpUserSettings = Usersettings.objects.filter(fb_user_id=singleGrp.fk_user_id).first()  
						accountSettings = Account.objects.filter(id=singleGrp.fk_user_id).first()  
						
						usrId = singleGrp.fk_user_id
						grpId = singleGrp.id
						reciptmail = singleGrp.automation_email_recipients

						if grpUserSettings and accountSettings and automationRepeatCheck(system, usrId, grpId,"s-daily"):  
							if grpUserSettings.email_daily_routine == True:
								check = True
								currdate = date.today()
								subject = "Scheduled report for "+ str(extract_domain(singleGrp.domain_name)) 
								context = {
									"projectname" : singleGrp.group_name,
									"domainname" :singleGrp.domain_name,
									"imp_dec_data": single_Group_Imp_Dec_Keyword(grpId),
									"fav_data": single_Group_Fav_Keyword(grpId),
									"today": currdate.strftime("%b %d, %Y"),
									"username": accountSettings.username,  	
									"alert": "Daily scheduled report",
									"email": accountSettings.email,
									"siteurl": settings.SITE_URL,
									"serivceurl": settings.SERVICE_URL,       				
									"projectSttngURL" : projectSettingURL_gen(usrId, grpId, singleGrp.group_name),
								}

								# Change to User Email
								if CheckPremiumUser(mid):
									reciptmail.append(accountSettings.email)
									toMail = reciptmail
								else:
									toMail = [accountSettings.email]
								
								mailDatas = sendMail('emails/imp_dec_fav.html', context, subject, toMail)
								if mailDatas:
									# Update mail logs and DB updation.
									mailLogUpdate(usrId, grpId, "s-daily")
									check = "success"   
								else:
									check = "failed"  							
					else:
						check = "disabled"
	except:
		check = "try error"
		pass

	return check 

# Daily process - Improved, Declined and Favourite - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# No improvement in keywords alert - STARTS

def mail_no_improvements_in_week(system, mid = None): 
	impReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all()

		if allGroups:
			noImpAlertData = NoWeeklyImprovementSerializer(allGroups, many=True, context={'system':system})
			if noImpAlertData:
				filteredImpData = list(filter(None, noImpAlertData.data))
				for singleImp in filteredImpData:
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleImp['guid']
					grpId = singleImp['gid']
					reciptmail = singleImp['reciptmail']
					if SettingsData:
						if SettingsData.core_manual_mode == True:
							currdate = date.today()
							moreviw = int(singleImp['count']) - int(singleImp['rows'])
							subject = "Alert: No improvement in keyword for "+ str(extract_domain(singleImp['gdomain'])) 
							context = {
								"domainname" :singleImp['gdomain'], 
								"projectname" :singleImp['gname'], 
								"today": currdate.strftime("%b %d, %Y"),
								"keywords": singleImp['gkeywords'],
								"username": singleImp['gusername'], 
								"email": singleImp['gemail'],  
								"count": singleImp['count'],  
								"rows": singleImp['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleImp['ps_url'],
							}
							# Change to User Email 
							if CheckPremiumUser(mid):
								reciptmail.append(singleImp['gemail'])
								toMail = reciptmail
							else:
								toMail = [singleImp['gemail']]

							mailDatas = sendMail('emails/no_impro_keywords.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation.
								mailLogUpdate(usrId, grpId, "s-noimprovement")
								impReturn = True 
							else: 
								impReturn = "failed"
	except:
		impReturn = "try error" 
		pass				

	return impReturn

# No improvement in keywords alert - ENDS

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Account without Keywords - STARTS

def mail_account_without_keywords():
	emptyReturn = "nothing" 
	try:
		accIns = Account.objects.filter(mail_count_status_no_keyword__lte=int(emptyAccountMailLimit),mail_no_keyword_routine__lte=date.today()).first()
		#changed
		sts,cnt = totalKeywordsCount(accIns.id)
		userKeyword = cnt
		# userKeyword = Keyword.objects.filter(fk_user_id=accIns.id).count() 
		if userKeyword == 0:
			SettingsData = Settings.objects.filter(id=1).first() 
			if SettingsData: 
				if SettingsData.core_manual_mode == True:
					currdate = date.today() 
					subject = "You have not added any keywords and missing lot of opportunities" 
					context = {
						"acc_id" : accIns.id, 
						"today": currdate.strftime("%b %d, %Y"), 
						"username": accIns.username, 
						"email": accIns.email,
						"siteurl": settings.SITE_URL,
						"serivceurl": settings.SERVICE_URL, 
					} 
					# Change to User Email
					toMail = [accIns.email]
					
					mailDatas = sendMail('emails/empty_account.html', context, subject, toMail)  
					if mailDatas:  
						# Update mail logs and DB updation. 
						emptyReturn = "success" 
						if accIns.id:   
							count = int(accIns.mail_count_status_no_keyword) + 1 
							Account.objects.filter(id=int(accIns.id)).update(mail_count_status_no_keyword=int(count), mail_no_keyword_routine=datetime.now()) 
					else: 
						emptyReturn = "failed"
		else:
			Account.objects.filter(id=int(accIns.id)).update(mail_no_keyword_routine=datetime.now()) 

	except:
		emptyReturn = "try error"
		pass

	return emptyReturn 

# Account without Keywords - ENDS

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Cannibalisation - STARTS
def mail_cannibalisation(system, mid = None):
	cannibReturn = "nothing"
	try:	
		allGroups = Groups.objects.filter(fk_user_id=mid).all()

		if allGroups:
			cannibData = cannibalisationSerializer(allGroups, many=True, context={'system':system})
			if cannibData:  
				filteredCannibData = list(filter(None, cannibData.data)) 

				for singleCannib in filteredCannibData: 
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleCannib['guid']
					grpId = singleCannib['gid'] 
					reciptmail = singleCannib['reciptmail']

					if SettingsData:
						if SettingsData.core_manual_mode == True:
							currdate = date.today()
							moreviw = int(singleCannib['count']) - int(singleCannib['rows'])
							subject = "Alert: Cannibalisation keywords for "+ str(extract_domain(singleCannib['gdomain'])) 
							context = {
								"projectname" : singleCannib['gname'],
								"domainname" :singleCannib['gdomain'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"keywords": singleCannib['gkeywords'],
								"username": singleCannib['gusername'],
								"email": singleCannib['gemail'],   
								"count": singleCannib['count'],  
								"rows": singleCannib['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL,
								"projectSttngURL" : singleCannib['ps_url'],

							}
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleCannib['gemail'])  
								toMail = reciptmail
							else:
								toMail = [singleCannib['gemail']]
							
							mailDatas = sendMail('emails/cannibalisation.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation. 
								cannibReturn = "success"
								for singleKeyword in singleCannib['gkeywords']:
									if singleKeyword['id']: 
										Keyword.objects.filter(id=int(singleKeyword['id'])).update(cannibalisation_mail_status="sent")
										mailLogUpdate(usrId, grpId, "s-cannib") 
							else: 
								cannibReturn = "failed"
	except:
		cannibReturn = "try error" 
		pass 

	return cannibReturn 
# Cannibalisation - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Ratings - STARTS
def mail_change_in_ratings(system, mid = None): 
	ratingReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all()

		if allGroups:
			ratingData = ratingSerializer(allGroups, many=True, context={'system':system})
			if ratingData:  
				filteredRatingData = list(filter(None, ratingData.data))

				for singleRating in filteredRatingData:
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleRating['guid']
					grpId = singleRating['gid']
					reciptmail = singleRating['reciptmail']

					if SettingsData:
						if SettingsData.core_manual_mode == True:
							currdate = date.today()
							subject = "Alert: Ratings changes occurred in "+ str(extract_domain(singleRating['gdomain']))
							moreviw = int(singleRating['count']) - int(singleRating['rows'])
							context = {
								"projectname" : singleRating['gname'],
								"domainname" :singleRating['gdomain'],
								"today": currdate.strftime("%b %d, %Y"),
								"keywords": singleRating['gkeywords'],
								"username": singleRating['gusername'], 
								"email": singleRating['gemail'],
								"count": singleRating['count'],
								"rows": singleRating['rows'],
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL,
								"projectSttngURL" : singleRating['ps_url'],
							}
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleRating['gemail'])
								toMail = reciptmail
							else:
								toMail = [singleRating['gemail']]

							mailDatas = sendMail('emails/change_review.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation. 
								mailLogUpdate(usrId, grpId, "s-rating") 
								ratingReturn = "success"
							else: 
								ratingReturn = "failed"
	except:
		ratingReturn = "try error" 
		pass

	return ratingReturn  
# Ratings - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Ads - STARTS
def mail_ads_snippet(system, mid = None):  
	adsReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all()

		if allGroups:
			adsData = adSerializer(allGroups, many=True, context={'system':system}) 
			if adsData:  
				filteredAdsData = list(filter(None, adsData.data))  
				for singleAds in filteredAdsData: 
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleAds['guid']
					grpId = singleAds['gid']
					reciptmail = singleAds['reciptmail']

					if SettingsData:
						if SettingsData.core_manual_mode == True:
							currdate = date.today() 
							moreviw = int(singleAds['count']) - int(singleAds['rows'])
							subject = "Alert: New Google ads found on your project "+ str(extract_domain(singleAds['gdomain'])) 
							context = {
								"projectname" : singleAds['gname'],
								"domainname" :singleAds['gdomain'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"keywords": singleAds['gkeywords'], 
								"username": singleAds['gusername'], 
								"email": singleAds['gemail'],  
								"count": singleAds['count'],  
								"rows": singleAds['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleAds['ps_url'],
							}
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleAds['gemail']) 
								toMail = reciptmail
							else:
								toMail = [singleAds['gemail']]
							
							mailDatas = sendMail('emails/new_ads_found.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation.
								mailLogUpdate(usrId, grpId, "s-ads")  
								adsReturn = "success"
							else: 
								adsReturn = "failed"
	except:
		adsReturn = "try error" 
		pass

	return adsReturn  

# Ads - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Featured - STARTS
def mail_featured_snippet(system, mid = None):  
	featuredReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all()  

		if allGroups:
			featuredData = featuredSerializer(allGroups, many=True, context={'system':system}) 
			if featuredData:  
				filteredFeaturedData = list(filter(None, featuredData.data))  

				for singleFeatured in filteredFeaturedData: 
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleFeatured['guid']
					grpId = singleFeatured['gid']
					reciptmail = singleFeatured['reciptmail']

					if SettingsData:  
						if SettingsData.core_manual_mode == True: 
							currdate = date.today() 
							moreviw = int(singleFeatured['count']) - int(singleFeatured['rows'])
							subject = " Alert: New Featured Snippet found on your project "+ str(extract_domain(singleFeatured['gdomain'])) 
							context = {
								"projectname" : singleFeatured['gname'],
								"domainname" :singleFeatured['gdomain'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"keywords": singleFeatured['gkeywords'], 
								"username": singleFeatured['gusername'],
								"email": singleFeatured['gemail'],
								"count": singleFeatured['count'],  
								"rows": singleFeatured['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleFeatured['ps_url'],
							}
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleFeatured['gemail'])
								toMail = reciptmail
							else:
								toMail = [singleFeatured['gemail']]
							
							mailDatas = sendMail('emails/new_snippet_found.html', context, subject, toMail) 
							if mailDatas: 
								# Update mail logs and DB updation.
								mailLogUpdate(usrId, grpId, "s-featured") 
								featuredReturn = "success"
							else: 
								featuredReturn = "failed"
	except:
		featuredReturn = "try error"
		pass

	return featuredReturn   

# Featured - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# URL - STARTS
def mail_changes_url(system, mid = None): 
	urlReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all() 

		if allGroups:
			urlData = urlSerializer(allGroups, many=True, context={'system':system}) 
			if urlData:  
				filteredUrlData = list(filter(None, urlData.data))
				
				for singleUrl in filteredUrlData: 
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleUrl['guid']
					grpId = singleUrl['gid']
					reciptmail = singleUrl['reciptmail']

					if SettingsData: 
						if SettingsData.core_manual_mode == True:
							currdate = date.today() 
							moreviw = int(singleUrl['count']) - int(singleUrl['rows'])
							subject = "Alert: New URL change(s) found in your domain "+ str(extract_domain(singleUrl['gdomain'])) 
							context = {
								"projectname" : singleUrl['gname'],
								"domainname" :singleUrl['gdomain'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"keywords": singleUrl['gkeywords'], 
								"username": singleUrl['gusername'],
								"email": singleUrl['gemail'],
								"count": singleUrl['count'],  
								"rows": singleUrl['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleUrl['ps_url'],
							}
							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleUrl['gemail'])
								toMail = reciptmail
							else:
								toMail = [singleUrl['gemail']]
							
							mailDatas = sendMail('emails/slug_change.html', context, subject, toMail) 
							if mailDatas: 
								# Update mail logs and DB updation. 
								mailLogUpdate( usrId, grpId, "s-url") 
								urlReturn = "success"
							else: 
								urlReturn = "failed"
	except: 
		urlReturn = "try error" 
		pass

	return urlReturn  

# URL - ENDS 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Best Tracker Score - STARTS 
def mail_best_tracker_score(system, mid = None):   
	scoreReturn = "nothing"

	try:
		allAccounts = Account.objects.filter(id=mid).all()  

		if allAccounts:
			scoreData = scoreSerializer(allAccounts, many=True, context={'system':system}) 
			if scoreData:   
				filteredScoreData = list(filter(None, scoreData.data))

				for singleScore in filteredScoreData:  
					SettingsData = Settings.objects.filter(id=1).first() 

					usrId = singleScore['acc_id']
					grpId = singleScore['acc_group'][0]['gid'] 

					if SettingsData: 
						if SettingsData.core_manual_mode == True:
							currdate = date.today() 
							subject = "Alert: You got the best Tracker Score today on your projects" 
							context = {
								"email" : singleScore['acc_email'],
								"acc_group" : singleScore['acc_group'],
								"today": currdate.strftime("%b %d, %Y"), 
								"username": singleScore['acc_username'],
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL,
							} 
							
							# Change to User Email
							toMail = [singleScore['acc_email']]
							
							mailDatas = sendMail('emails/best_score.html', context, subject, toMail)  
							if mailDatas: 
								# Update mail logs and DB updation. 
								for singleGroup in singleScore['acc_group']:
									mailLogUpdate(usrId, singleGroup['gid'], "s-bestscore") 
								scoreReturn = "success" 
							else: 
								scoreReturn = "failed"
	except:
		scoreReturn = "try error" 
		pass   

	return scoreReturn 

# Best Tracker Score - ENDS

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Account without Keywords - STARTS

def mail_max_keywords_reach(system, mid = None): 
	maxReturn = "nothing"

	try:
		allAccounts = Accountusage.objects.filter(fb_user_id=mid).all() 

		emptyAccounts = MaxKeywordSerializer(allAccounts, many = True) 
		emptyAccountData = [] 
		if emptyAccounts: 
			emptyAccountData = list(filter(None, emptyAccounts.data)) 
			
			for singleAccount in emptyAccountData: 
				SettingsData = Settings.objects.filter(id=1).first() 
				if SettingsData: 
					if SettingsData.core_manual_mode == True:
						currdate = date.today() 
						reflink =  str(settings.SITE_URL+"/app/referral")
						subject = "Share Tracker with your friends and get awesome benefits!" 
						context = {
							"acc_id" : singleAccount['acc_id'], 
							"today": currdate.strftime("%b %d, %Y"), 
							"username": singleAccount['acc_username'], 
							"email": singleAccount['acc_email'], 
							"reflink" : reflink,
							"siteurl": settings.SITE_URL,
							"serivceurl": settings.SERVICE_URL,
						} 
						# Change to User Email
						toMail = [singleAccount['acc_email']]
						
						mailDatas = sendMail('emails/max_keyword_reach.html', context, subject, toMail) 
						if mailDatas: 
							# Update mail logs and DB updation. 
							maxReturn = "success" 
							if singleAccount['acc_id']: 
								Accountusage.objects.filter(id=int(singleAccount['acc_id'])).update(mail_max_keyword_reach=str(datetime.now())) 
						else: 
							maxReturn = "failed"
	except:
		maxReturn = "try error"
		pass

	return maxReturn

# Account without Keywords - ENDS


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# New Relese Keywords - STARTS 

def mail_new_release(system, mid = None): 
	releaseReturn = "nothing"
	try:
		allAccounts = Account.objects.filter(id=mid).all() 

		officialAccounts = NewReleaseSerializer(allAccounts, many = True) 
		AccountData = []
		if officialAccounts:
			AccountData = list(filter(None, officialAccounts.data)) 

			for singleAccount in AccountData: 
				SettingsData = Settings.objects.filter(id=1).first() 
				if SettingsData:
					if SettingsData.core_manual_mode == True:
						currdate = date.today() 
						subject = "Tracker got a new version with stunning features ! Try now."  
						context = {
							"acc_id" : singleAccount['id'], 
							"today": currdate.strftime("%b %d, %Y"), 
							"username": singleAccount['username'], 
							"email": singleAccount['email'],
							"siteurl": settings.SITE_URL,
							"serivceurl": settings.SERVICE_URL, 
						} 
						# Change to User Email
						toMail = [singleAccount['email']] 
						
						mailDatas = sendMail('emails/new_release.html', context, subject, toMail) 
						if mailDatas:  
							# Update mail logs and DB updation. 
							releaseReturn = "success"
						else: 
							releaseReturn = "failed" 
	except:
		releaseReturn = "try error" 
		pass

	return releaseReturn

# New Relese Keywords - ENDS 

# New Brand Ads - STARTS
def mail_brand_conquestor():  
	brandReturn = "nothing" 
	
	try:
		currdate = str(date.today())
		tomorrow = str(date.today() + timedelta(days = 1))

		brandData = brandTracker.objects.exclude(conquestor_mail_date__range=(currdate, tomorrow)).exclude(conquestor_recent_list=[]).filter(conquestor_call_status="done", conquestor_recent_date__range=(currdate, tomorrow), modified_date__range=(currdate, tomorrow), status="on").all()[0:1] 
		# brandData = brandTracker.objects.filter(fb_user_id=5,fb_group_id=81).all()[0:1]
		if brandData: 
			brandValues = BrandConquestorSerializer(brandData, many = True) 

			if brandValues:
				brandSerializer = list(filter(None, brandValues.data))

				for singleBrand in brandSerializer: 
					SettingsData = Settings.objects.filter(id=1).first() 
					if SettingsData:
						if SettingsData.core_manual_mode == True:
							brand_id = singleBrand['acc_brand'][0]['ky'] 
							brand_mail_date = singleBrand['acc_brand'][0]['m_de'] 

							brandTracker.objects.filter(id=brand_id).update(conquestor_mail_date=datetime.now()) 

							currdate = date.today() 
							subject = "New conquestor ads found for your brand name" 
							
							context = {
								"brands" : singleBrand['acc_brand'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"username": singleBrand['acc_username'], 
								"email": singleBrand['acc_email'], 
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleBrand['ps_url'],
							} 
							# Change to User Email
							toMail = [singleBrand['acc_email']]
							
							mailDatas = sendMail('emails/brand_conquest_ads.html', context, subject, toMail) 
							
							if mailDatas:  
								brandTracker.objects.filter(id=brand_id).update(conquestor_mail_date=datetime.now(), modified_date=datetime.now())  
								brandReturn = "success"
							else: 
								brandTracker.objects.filter(id=brand_id).update(conquestor_mail_date=brand_mail_date, modified_date=datetime.now())  
								brandReturn = "failed"

	except: 
		brandReturn = "try error"
		pass
	
	return brandReturn
# New Brand Ads - ENDS

# New Brand Ads - STARTS
def mail_brand_acquisition( system,mid = None):
	brandadsReturn = "nothing"

	try:
		allGroups = Groups.objects.filter(fk_user_id=mid).all()
		if allGroups:
			adsData = BrandAcquisitionSerializer(allGroups, many=True, context={'system':system}) 
			if adsData:  
				filteredAdsData = list(filter(None, adsData.data))  

				for singleAds in filteredAdsData: 
					SettingsData = Settings.objects.filter(id=1).first() 
					usrId = singleAds['guid']
					grpId = singleAds['gid']
					reciptmail = singleAds['reciptmail']
					if SettingsData: 
						if SettingsData.core_manual_mode == True:
							currdate = date.today() 
							moreviw = int(singleAds['count']) - int(singleAds['rows'])
							subject = "Alert: New conquestor ads found for your project "+ str(extract_domain(singleAds['gdomain'])) 
							context = { 
								"projectname" : singleAds['gname'],
								"domainname" :singleAds['gdomain'], 
								"today": currdate.strftime("%b %d, %Y"), 
								"keywords": singleAds['gkeywords'], 
								"username": singleAds['gusername'], 
								"email": singleAds['gemail'],  
								"count": singleAds['count'],  
								"rows": singleAds['rows'],  
								"mview": moreviw if moreviw > 0 else 0,
								"siteurl": settings.SITE_URL,
								"serivceurl": settings.SERVICE_URL, 
								"projectSttngURL" : singleAds['ps_url'],
							}

							# Change to User Email
							if CheckPremiumUser(mid):
								reciptmail.append(singleAds['gemail']) 
								toMail = reciptmail
							else:
								toMail = [singleAds['gemail']]
							mailDatas = sendMail('emails/brand_aqu_ads.html', context, subject, toMail) 
							if mailDatas:
								# Update mail logs and DB updation.
								mailLogUpdate(usrId, grpId, "s-brandads")  
								brandObtain.objects.filter(fk_user_id=usrId,fk_group_id=grpId).update(brand_mail_date=datetime.now(), modified_date=datetime.now())  
								brandadsReturn = "success"
							else: 
								brandObtain.objects.filter(fk_user_id=usrId,fk_group_id=grpId).update(brand_mail_date=brand_mail_date, modified_date=datetime.now())  
								brandadsReturn = "failed"
	except:
		brandadsReturn = "try error" 
		pass

	return brandadsReturn
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Current Testing
