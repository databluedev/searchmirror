from django.shortcuts import render
from django.conf import settings 

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings 
from project.machine.models import CompProject, CompKeyword
from project.machine.competitor import automation_formulate as _at__self_ 

import requests, json, time, csv, math 
from bs4 import BeautifulSoup
from urllib import parse 
import sys, os, random
from datetime import datetime, date, timedelta
from collections import defaultdict   

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse

from urllib.parse import urlparse 

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail

from project.machine import watchdog 
from mongoengine.queryset.visitor import Q  
from shared.scoring import calculate_visibility_score_from_buckets

def extract_protocol_domain(url, remove_http=True): 
	uri = urlparse(url)
	if remove_http:
		if uri.netloc: 
			domain_name = f"{uri.scheme}://{uri.netloc}/"
		else:
			euri = urlparse(f"http://{uri.path}")
			domain_name = f"{euri.scheme}://{euri.netloc}/" if euri.hostname != None else False 
	else:
		domain_name = f"{uri.scheme}://{uri.netloc}/" 
	return domain_name 

def topScoreUpdate(cpid, incomingSystem): 
	projectObj = CompProject.objects.filter(__raw__= {'id': int(cpid)}).first()
	if projectObj:
		scoreValue = max(set(map(float, projectObj.cp_score_meter)))
		scoreValue = float("{:.2f}".format(scoreValue)) 
		if projectObj.cp_top_score is None:
			CompProject.objects.filter(__raw__= {'id': int(cpid)}).update(cp_top_score=str(scoreValue)) 
		elif scoreValue > float(projectObj.cp_top_score): 
			CompProject.objects.filter(__raw__= {'id': int(cpid)}).update(cp_top_score=str(scoreValue)) 
	return True

def activityCalc(improve, declined, allKey): 
	if allKey > 0: 
		activityResult = round(float( ((len(improve) - len(declined)) / allKey) * 100 ), 2) 
		return str(activityResult)+"|"+str(len(improve))+"|"+str(len(declined)) 
	else:
		return "0|0|0"

def scoreMeterCalc(scorePerDay, allKey): 
	return calculate_visibility_score_from_buckets(scorePerDay, allKey)

def rankFormulation(liveRank, pastRank):
	totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100) 
	
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

	return formulateValue 

def sinceStartCalc(userid, cpid, grpid, index):
	topset = ["0-1","1-2","2-3","3-10","10-100","0-0"]
	singleSincePosition = [] 
	rankIndexCount = int(index) - 1 if int(index) > 0 else 0 

	try:
		for tset in topset: 
			topRankVal = tset.split("-") 

			if len(topRankVal) > 1: 
				minVal = int(topRankVal[0])
				maxVal = int(topRankVal[1]) 

				gtRank = 'rank__'+str(rankIndexCount)+'__gt'
				lteRank = 'rank__'+str(rankIndexCount)+'__lte'
				eqRank = 'rank__'+str(rankIndexCount)   

				if minVal == 0 and maxVal == 0: 
					headerKeywordCount = CompKeyword.objects.filter((Q(**{eqRank: 0})) & Q(fk_cp_project_id=cpid) & Q(fk_group_id=grpid)).count() 
				else:
					headerKeywordCount = CompKeyword.objects.filter((Q(**{gtRank: minVal}) & Q(**{lteRank: maxVal})) & Q(fk_cp_project_id=cpid) & Q(fk_group_id=grpid)).count()

				singleSincePosition.append(str(headerKeywordCount))
			else:
				singleSincePosition.append("0")   
	except Exception as e:
		singleSincePosition = "0,0,0,0,0,0" 
		# UPDATE ERROR ON THE KEYWPRD FIELD as "CSSCERR"
		watchdog.coreLog(" > COMP FORMULTE >> SINCE START CALC >> ERROR = " +str(e)+ " >>> G_ID = "+str(grpid)+" CP_ID = "+str(cpid), "COMPALYSE") 

	return ','.join(map(str, singleSincePosition)) 

def dashboardCompetitorGraph(incomingSystem, incomingId):  
	try: 
		# incomingId - COMPETITOR PROJECT ID
		startTime = datetime.now()
		totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)
		currdate = date.today() 
		calcSystemUpdate = []   
		calcSystemAll = []

		if incomingSystem == "COMPALYSE":
			cProjects = CompProject.objects.filter(__raw__= {'id': int(incomingId)}).all()
			watchdog.coreLog(" > COMP DASHBOARD CALCULATION STARTED >>  CP_ID = " + str(incomingId), incomingSystem) 

			for cProject in cProjects:
				if cProject.id:
					cpId = int(cProject.id)
					cpGroupId = int(cProject.fk_group_id)
					cpUserId = int(cProject.fk_user_id)

					cProjectUpdate = CompProject.objects.filter(__raw__= {'id': cpId})
					updateFlag = 0

					groupAge = int((currdate - cProject.created_date.date()).days) + 1
					rankIndexCount = int(groupAge)

					# SCORE METER (POP)
					cProjectScoreLen = len(cProject.cp_score_meter)
					if cProjectScoreLen > groupAge:
						groupDifference = cProjectScoreLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_score_meter=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# MAIN SCORE METER (POP)
					cProjectScoreLen = len(cProject.mn_score_meter)
					if cProjectScoreLen > groupAge:
						groupDifference = cProjectScoreLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_score_meter=-1, updated_date=datetime.now()) 
							flag += 1
							updateFlag += 1

					# ACTIVITY METER (POP)
					cProjectActivityLen = len(cProject.cp_activity_level)
					if cProjectActivityLen > groupAge:
						groupDifference = cProjectActivityLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_activity_level=-1, updated_date=datetime.now())
							flag += 1 
							updateFlag += 1

					# MAIN ACTIVITY METER (POP)
					cProjectActivityLen = len(cProject.mn_activity_level)
					if cProjectActivityLen > groupAge:
						groupDifference = cProjectActivityLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_activity_level=-1, updated_date=datetime.now())
							flag += 1 
							updateFlag += 1

					# POSITION METER (POP)
					cProjectPositionLen = len(cProject.cp_since_position)
					if cProjectPositionLen > groupAge:
						groupDifference = cProjectPositionLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_since_position=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# MAIN POSITION METER (POP)
					cProjectPositionLen = len(cProject.mn_since_position)
					if cProjectPositionLen > groupAge:
						groupDifference = cProjectPositionLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_since_position=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# TOTAL KEYWORDS METER  (POP)
					cProjectTotalKeywordLen = len(cProject.cp_total_keyword) 
					if cProjectTotalKeywordLen > groupAge:
						groupDifference = cProjectTotalKeywordLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_total_keyword=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# RECALL AFTER POP OCCURS 
					if updateFlag > 0:
						cProjectUpdate = CompProject.objects.filter(__raw__= {'id': cpId})
						singleProject = cProjectUpdate.first() # singleGroup

						groupAge = int((currdate - singleProject.created_date.date()).days) + 1
						rankIndexCount = int(groupAge)
					else: 
						singleProject = cProjectUpdate.first() # singleGroup 

					# UPDATE GROUP NAME - MAY OCCUR AT ANY TIME 
					resetGrpDomain = CompKeyword.objects.filter(fk_cp_project_id = cpId, fk_group_id=cpGroupId, ranknow__gt=0).first()
					if resetGrpDomain:
						domainNameParse = extract_protocol_domain(resetGrpDomain.cp_site_url)
						if domainNameParse: 
							cProjectUpdate.update(cp_domain_name=domainNameParse)

					if (groupAge == (len(singleProject.cp_total_keyword) + 1) and len(singleProject.cp_total_keyword) > 0) or (groupAge == len(singleProject.cp_total_keyword)  and len(singleProject.cp_total_keyword) > 0): 
						# print("COMP IF PART", "\n") 
						single_date = currdate + timedelta(1) 
						allKeywords = CompKeyword.objects.filter(fk_cp_project_id=cpId, fk_group_id=cpGroupId, created_date__lt=single_date).only('rank').all() 
						allKeywordsLen = len(allKeywords)

						scorePerDay = defaultdict(int) 
						improvedKeywords = []
						declinedKeywords = []  

						for keyIns in allKeywords:  
							rankLength = len(keyIns.rank)
							if rankLength > 0:  
								firstRankValue = keyIns.rank[0]
								if firstRankValue == 1:
									scorePerDay['eq__first'] += 1
								elif firstRankValue == 2:
									scorePerDay['eq__second'] += 1
								elif firstRankValue == 3:
									scorePerDay['eq__third'] += 1
								elif firstRankValue <= 10 and firstRankValue > 3:  
									scorePerDay['gte__four__lte__ten'] += 1
								elif firstRankValue > 10 and firstRankValue <= totalRankLength:  
									scorePerDay['gt__ten__lte__limit'] += 1  
								else: 
									scorePerDay['gt__limit'] += 1 
							else: 
								scorePerDay['gt__limit'] += 1  

							if rankIndexCount >= rankLength and rankLength > 1:  
								dayDiff = rankFormulation(keyIns.rank[0], keyIns.rank[1])   
								if dayDiff > 0:
									improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id)) 
								elif dayDiff < 0:
									declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))
						
						sinceStartExplode = sinceStartCalc(cpUserId, cpId, cpGroupId, 0)

						existCount = 0
						newCount = 0 

						# UPDATE COMPETITOR SCORE METER
						if groupAge == len(singleProject.cp_score_meter): 
							cProjectUpdate.update(
								cp_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)), 
								updated_date=datetime.now() 
							)
							newCount += 1

						# UPDATE COMPETITOR ACTIVITY METER
						if groupAge == len(singleProject.cp_activity_level): 
							cProjectUpdate.update(
								cp_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)),
								updated_date=datetime.now()
							)
							newCount += 1

						# UPDATE COMPETITOR POSITION METER
						if groupAge == len(singleProject.cp_since_position): 
							cProjectUpdate.update(
								cp_since_position__0=str(sinceStartExplode),   
								updated_date=datetime.now()
							)
							existCount += 1
						else:
							cProjectUpdate.update( 
								push__cp_since_position__0=str(sinceStartExplode),    
								updated_date=datetime.now()
							)
							newCount += 1

						# UPDATE TOTAL KEYWORDS
						if groupAge == len(singleProject.cp_total_keyword): 
							cProjectUpdate.update(
								cp_total_keyword__0=str(allKeywordsLen),
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_total_keyword__0=str(allKeywordsLen),
								updated_date=datetime.now()
							)
							newCount += 1

						if existCount > 0 and newCount > 0:
							calcSystemUpdate.insert(0, str(cpId)+"|"+str("BOTH"))
						else: 
							if existCount > 0:
								calcSystemUpdate.insert(0, str(cpId)+"|"+str("EXIST"))

							if newCount > 0:
								calcSystemUpdate.insert(0, str(cpId)+"|"+str("NEW")) 
					else:
						# print("COMP ELSE PART", "\n")
						calcSystemAll.insert(0, str(cpId))  

						cProjectUpdate.update(
							cp_score_meter=[],
							cp_activity_level=[],
							cp_since_position=[],  
							cp_total_keyword=[], 
							cp_top_score=None, 
							updated_date=datetime.now()
						)  

						#DATE DIFFERENCE FROM DATE - TO DATE  
						for single_date in (singleProject.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):   
							allKeywords = CompKeyword.objects.filter(fk_cp_project_id=cpId, fk_group_id=cpGroupId, created_date__lt=single_date).only('rank').all()
							allKeywordsLen = len(allKeywords)

							scorePerDay = defaultdict(int) 
							improvedKeywords = []
							declinedKeywords = [] 

							for keyIns in allKeywords:  
								rankLength = len(keyIns.rank)
								if rankLength >= rankIndexCount:
									onDateRank = keyIns.rank[rankIndexCount - 1]
									if onDateRank == 1:
										scorePerDay['eq__first'] += 1
									elif onDateRank == 2:
										scorePerDay['eq__second'] += 1
									elif onDateRank == 3:
										scorePerDay['eq__third'] += 1
									elif onDateRank <= 10 and onDateRank > 3:  
										scorePerDay['gte__four__lte__ten'] += 1
									elif onDateRank > 10 and onDateRank <= totalRankLength: 
										scorePerDay['gt__ten__lte__limit'] += 1 
									else: 
										scorePerDay['gt__limit'] += 1
								else: 
									scorePerDay['gt__limit'] += 1   

								if rankLength > rankIndexCount:
									dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
									if dayDiff > 0:
										improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
									elif dayDiff < 0:
										declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  
							
							sinceStartExplode = sinceStartCalc(cpUserId,  cpId, cpGroupId, rankIndexCount)

							cProjectUpdate.update(
								push__cp_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)),
								push__cp_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)), 
								push__cp_since_position__0=str(sinceStartExplode),   
								# push__cp_total_keyword__0=str(len(allKeywords)),  
								updated_date=datetime.now()   
							)  

							rankIndexCount = rankIndexCount - 1  
						# End FOR
					# END IF 

					# Top tracker Score Update	
					topScoreUpdate(cpId, incomingSystem)

		if len(calcSystemUpdate) > 0 or len(calcSystemAll) > 0:  
			watchdog.coreLog(" > COMP DASHBOARD CALCULATION COMLETED >> CP_ID = "+str(incomingId)+ " >>> UPDATE: "+str(calcSystemUpdate)+" ALL: "+str(calcSystemAll), incomingSystem)
		else:
			watchdog.coreLog(" > COMP DASHBOARD CALCULATION FAILED >> CP_ID = "+str(incomingId), incomingSystem) 

	except Exception as e:
		# UPDATE ERROR ON THE KEYWPRD FIELD as "CDCERR"
		watchdog.coreLog(" > COMP FORMULTE >> COMPALYSE SYSTEM >> ERROR = " +str(e)+ " >>> CP_ID = "+str(incomingId), incomingSystem)

	return True 

def dashboardZeroRankGraph(incomingSystem, incomingId): 
	try: 
		# incomingId - COMPETITOR PROJECT ID
		startTime = datetime.now()
		totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)      
		currdate = date.today() 
		calcSystemUpdate = []   
		calcSystemAll = [] 

		if incomingSystem == "COMPALYSE":
			cProjects = CompProject.objects.filter(__raw__= {'id': int(incomingId)}).all()
			watchdog.coreLog(" > COMP-MAIN ZERO DASHBOARD CALCULATION STARTED >> CP_ID = " + str(incomingId), incomingSystem)

			for cProject in cProjects:
				if cProject.id: 
					cpId = int(cProject.id)
					cpGroupId = int(cProject.fk_group_id)
					cpUserId = int(cProject.fk_user_id)

					cProjectUpdate = CompProject.objects.filter(__raw__= {'id': cpId})
					updateFlag = 0

					groupAge = int((currdate - cProject.created_date.date()).days) + 1
					rankIndexCount = int(groupAge)

					# COMPETITOR SCORE METER
					cProjectScoreLen = len(cProject.cp_score_meter)
					if cProjectScoreLen > groupAge:
						groupDifference = cProjectScoreLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_score_meter=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# MAIN SCORE METER
					cProjectScoreLen = len(cProject.mn_score_meter)
					if cProjectScoreLen > groupAge:
						groupDifference = cProjectScoreLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_score_meter=-1, updated_date=datetime.now()) 
							flag += 1
							updateFlag += 1

					# COMPETITOR ACTIVITY METER
					cProjectActivityLen = len(cProject.cp_activity_level)
					if cProjectActivityLen > groupAge:
						groupDifference = cProjectActivityLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_activity_level=-1, updated_date=datetime.now())
							flag += 1 
							updateFlag += 1

					# MAIN ACTIVITY METER
					cProjectActivityLen = len(cProject.mn_activity_level)
					if cProjectActivityLen > groupAge:
						groupDifference = cProjectActivityLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_activity_level=-1, updated_date=datetime.now())
							flag += 1 
							updateFlag += 1

					# COMPETITOR POSITION METER
					cProjectPositionLen = len(cProject.cp_since_position)
					if cProjectPositionLen > groupAge:
						groupDifference = cProjectPositionLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_since_position=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# MAIN POSITION METER
					cProjectPositionLen = len(cProject.mn_since_position)
					if cProjectPositionLen > groupAge:
						groupDifference = cProjectPositionLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__mn_since_position=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# TOTAL KEYWORDS
					cProjectTotalKeywordLen = len(cProject.cp_total_keyword) 
					if cProjectTotalKeywordLen > groupAge:
						groupDifference = cProjectTotalKeywordLen - groupAge
						flag = 1
						while flag <= groupDifference:
							cProjectUpdate.update(pop__cp_total_keyword=-1, updated_date=datetime.now())
							flag += 1
							updateFlag += 1

					# Recall 
					if updateFlag > 0:
						cProjectUpdate = CompProject.objects.filter(__raw__= {'id': cpId})
						singleProject = cProjectUpdate.first() # singleGroup

						groupAge = int((currdate - singleProject.created_date.date()).days) + 1
						rankIndexCount = int(groupAge)
					else: 
						singleProject = cProjectUpdate.first() # singleGroup

					if (groupAge == (len(singleProject.cp_total_keyword) + 1) and len(singleProject.cp_total_keyword) > 0) or (groupAge == len(singleProject.cp_total_keyword)  and len(singleProject.cp_total_keyword) > 0): 

						single_date = currdate + timedelta(1)
						allKeywordsLen = CompKeyword.objects.filter(fk_cp_project_id=cpId, fk_group_id=cpGroupId, created_date__lt=single_date).count()

						existCount = 0
						newCount = 0

						# UPDATE COMPETITOR SCORE METER
						if groupAge == len(singleProject.cp_score_meter): 
							cProjectUpdate.update(
								cp_score_meter__0=str("0.0"), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_score_meter__0=str("0.0"), 
								updated_date=datetime.now() 
							)
							newCount += 1

						# UPDATE MAIN SCORE METER
						if groupAge == len(singleProject.mn_score_meter): 
							cProjectUpdate.update(
								mn_score_meter__0=str("0.0"), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__mn_score_meter__0=str("0.0"), 
								updated_date=datetime.now() 
							)
							newCount += 1

						# UPDATE COMPETITOR ACTIVITY METER
						if groupAge == len(singleProject.cp_activity_level): 
							cProjectUpdate.update(
								cp_activity_level__0=str("0.0|0|0"), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_activity_level__0=str("0.0|0|0"), 
								updated_date=datetime.now()
							)
							newCount += 1

						# UPDATE MAIN ACTIVITY METER
						if groupAge == len(singleProject.mn_activity_level): 
							cProjectUpdate.update(
								mn_activity_level__0=str("0.0|0|0"), 
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__mn_activity_level__0=str("0.0|0|0"), 
								updated_date=datetime.now()
							)
							newCount += 1

						# UPDATE COMPETITOR POSITION METER
						if groupAge == len(singleProject.cp_since_position): 
							cProjectUpdate.update(
								cp_since_position__0=str("0,0,0,0,0,0"),   
								updated_date=datetime.now()
							)
							existCount += 1
						else:
							cProjectUpdate.update( 
								push__cp_since_position__0=str("0,0,0,0,0,0"),     
								updated_date=datetime.now()
							)
							newCount += 1

						# UPDATE MAIN POSITION METER
						if groupAge == len(singleProject.mn_since_position): 
							cProjectUpdate.update(
								mn_since_position__0=str("0,0,0,0,0,0"),   
								updated_date=datetime.now()
							)
							existCount += 1
						else:
							cProjectUpdate.update( 
								push__mn_since_position__0=str("0,0,0,0,0,0"),     
								updated_date=datetime.now()
							)
							newCount += 1

						# TOTAL KEYWORD METER COMPETITOR AND MAIN PROJECT IN ONE ARRAY.
						if groupAge == len(singleProject.cp_total_keyword): 
							cProjectUpdate.update(
								cp_total_keyword__0=str(allKeywordsLen),
								updated_date=datetime.now() 
							)
							existCount += 1
						else:
							cProjectUpdate.update(
								push__cp_total_keyword__0=str(allKeywordsLen),
								updated_date=datetime.now() 
							)
							newCount += 1

						if existCount > 0 and newCount > 0:
							calcSystemUpdate.insert(0, str(cpId)+"|"+str("BOTH"))
						else: 
							if existCount > 0:
								calcSystemUpdate.insert(0, str(cpId)+"|"+str("EXIST"))

							if newCount > 0:
								calcSystemUpdate.insert(0, str(cpId)+"|"+str("NEW")) 
					else:
						calcSystemAll.insert(0, str(cpId))  

						cProjectUpdate.update(
							cp_score_meter=[], 
							cp_activity_level=[],
							cp_since_position=[],
							cp_top_score=None, 
							mn_score_meter=[],
							mn_activity_level=[],
							mn_since_position=[],  
							mn_top_score=None,
							cp_total_keyword=[], 
							updated_date=datetime.now()
						)  

						compIds = list(CompKeyword.objects.filter(fk_cp_project_id=cpId).values_list('fk_keyword_id').order_by('fk_keyword_id').all())

						# DATE DIFFERENCE FROM DATE - TO DATE
						for single_date in (singleProject.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):   
							allKeywords = CompKeyword.objects.filter(fk_cp_project_id=cpId, fk_group_id=cpGroupId, created_date__lt=single_date).only('rank').all() 
							allKeywordsLen = len(allKeywords)

							scorePerDay = defaultdict(int) 
							improvedKeywords = []
							declinedKeywords = []

							# COMPETTITOR RESET DATA 
							for keyIns in allKeywords:  
								rankLength = len(keyIns.rank)
								if rankLength >= rankIndexCount:
									onDateRank = keyIns.rank[rankIndexCount - 1]
									if onDateRank == 1:
										scorePerDay['eq__first'] += 1
									elif onDateRank == 2:
										scorePerDay['eq__second'] += 1
									elif onDateRank == 3:
										scorePerDay['eq__third'] += 1
									elif onDateRank <= 10 and onDateRank > 3:  
										scorePerDay['gte__four__lte__ten'] += 1
									elif onDateRank > 10 and onDateRank <= totalRankLength: 
										scorePerDay['gt__ten__lte__limit'] += 1 
									else: 
										scorePerDay['gt__limit'] += 1
								else: 
									scorePerDay['gt__limit'] += 1   

								if rankLength > rankIndexCount:
									dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
									if dayDiff > 0:
										improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
									elif dayDiff < 0:
										declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  
							
							sinceStartExplode = sinceStartCalc(cpUserId,  cpId, cpGroupId, rankIndexCount)

							# MAIN GROUP RESET
							allMainKeywords = Keyword.objects.filter(__raw__={'id': {'$in': compIds}}, fk_group_id=cpGroupId, created_date__lt=single_date).all() 
							mainScorePerDay = defaultdict(int) 
							mainImprovedKeywords = []
							mainDeclinedKeywords = []

							for keyIns in allMainKeywords:  
								rankLength = len(keyIns.rank)
								if rankLength >= rankIndexCount:
									onDateRank = keyIns.rank[rankIndexCount - 1]
									if onDateRank == 1:
										mainScorePerDay['eq__first'] += 1
									elif onDateRank == 2:
										mainScorePerDay['eq__second'] += 1
									elif onDateRank == 3:
										mainScorePerDay['eq__third'] += 1
									elif onDateRank <= 10 and onDateRank > 3:  
										mainScorePerDay['gte__four__lte__ten'] += 1
									elif onDateRank > 10 and onDateRank <= totalRankLength: 
										mainScorePerDay['gt__ten__lte__limit'] += 1 
									else: 
										mainScorePerDay['gt__limit'] += 1
								else: 
									mainScorePerDay['gt__limit'] += 1  

								if rankLength > rankIndexCount:
									dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
									if dayDiff > 0:
										mainImprovedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
									elif dayDiff < 0:
										mainDeclinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id)) 
							
							mainSinceStartExplode = _at__self_.mainSinceStartCalc(compIds, cpUserId, cpId, cpGroupId, rankIndexCount) 


							cProjectUpdate.update( 
								push__cp_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)),
								push__cp_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)), 
								push__cp_since_position__0=str(sinceStartExplode), 
								push__cp_total_keyword__0=str(allKeywordsLen), 
								push__mn_score_meter__0=str(scoreMeterCalc(mainScorePerDay, allKeywordsLen)),
								push__mn_activity_level__0=str(activityCalc(mainImprovedKeywords, mainDeclinedKeywords, allKeywordsLen)), 
								push__mn_since_position__0=str(mainSinceStartExplode), 
								updated_date=datetime.now()   
							) 

							rankIndexCount = rankIndexCount - 1 
						# END FOR
					# END IF

					# Top tracker Score Update	
					topScoreUpdate(cpId, incomingSystem) 
					_at__self_.topScoreUpdate(cpId, incomingSystem) 

		if len(calcSystemUpdate) > 0 or len(calcSystemAll) > 0: 
			watchdog.coreLog(" > COMP-MAIN ZERO DASHBOARD CALCULATION COMLETED >> CP_ID = "+str(incomingId)+ " >>> UPDATE: "+str(calcSystemUpdate)+" ALL: "+str(calcSystemAll), incomingSystem)
		else:
			watchdog.coreLog(" > COMP-MAIN ZERO DASHBOARD CALCULATION FAILED >> CP_ID = "+str(incomingId), incomingSystem) 

	except Exception as e:
		# UPDATE ERROR ON THE KEYWPRD FIELD as "CZCERR"
		watchdog.coreLog(" > COMP-MAIN ZERO DASHBOARD CALCULATION >> COMPALYSE SYSTEM >> ERROR = " +str(e)+ " >>> CP_ID = "+str(incomingId), incomingSystem)

	return True
