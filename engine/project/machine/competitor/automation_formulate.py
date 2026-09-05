from django.shortcuts import render
from django.conf import settings 

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings 
from project.machine.models import CompProject, CompKeyword

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

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
	try:
		projectObj = CompProject.objects.filter(__raw__= {'id': int(cpid)}).first() 
		if projectObj:
			scoreValue = max(set(map(float, projectObj.mn_score_meter)))
			scoreValue = float("{:.2f}".format(scoreValue)) 
			if projectObj.mn_top_score is None:
				CompProject.objects.filter(__raw__= {'id': int(cpid)}).update(mn_top_score=str(scoreValue)) 
			elif scoreValue > float(projectObj.mn_top_score):
				CompProject.objects.filter(__raw__= {'id': int(cpid)}).update(mn_top_score=str(scoreValue)) 
	except Exception as e:
		watchdog.coreLog(" > MAIN FORMULTE >> TOP SCORE UPDATE >> ERROR = " +str(e), "COMPALYSE")  
	
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

def mainSinceStartCalc(compIds, userid, cpid, grpid, index):
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
					headerKeywordCount = Keyword.objects.filter(__raw__={'id': {'$in': compIds}}).filter((Q(**{eqRank: 0})) & Q(fk_group_id=grpid)).count()
				else:
					headerKeywordCount = Keyword.objects.filter(__raw__={'id': {'$in': compIds}}).filter((Q(**{gtRank: minVal}) & Q(**{lteRank: maxVal})) & Q(fk_group_id=grpid)).count()

				singleSincePosition.append(str(headerKeywordCount))
			else:
				singleSincePosition.append("0") 
	except Exception as e:
		singleSincePosition = "0,0,0,0,0,0"
		# UPDATE ERROR ON THE KEYWPRD FIELD as "MSSCERR" 
		watchdog.coreLog(" > MAIN FORMULTE >> SINCE START CALC >> ERROR = " +str(e)+ " >>> G_ID = "+str(grpid)+" CP_ID = "+str(cpid), "COMPALYSE") 

	return ','.join(map(str, singleSincePosition))

def dashboardGroupGraph(incomingSystem, groupId, compProId): 
	try: 
		groupId = int(groupId)
		compProId = int(compProId)

		if groupId and compProId and incomingSystem == "COMPALYSE":
			startTime = datetime.now()
			currdate = date.today() 
			calcSystemUpdate = []   
			calcSystemAll = []
			totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100) 

			cProjectUpdate = CompProject.objects.filter(__raw__= {'id': compProId})
			watchdog.coreLog(" > MAIN DASHBOARD CALCULATION STARTED >> G_ID = " + str(groupId) + " CP_ID = " + str(compProId), incomingSystem)

			if cProjectUpdate: 
				
				singleProject = cProjectUpdate.first()  
				if hasattr(singleProject, 'id'):
					cpId = int(singleProject.id)
					cpGroupId = int(singleProject.fk_group_id)
					cpUserId = int(singleProject.fk_user_id)
					
					groupAge = int((currdate - singleProject.created_date.date()).days) + 1
					rankIndexCount = int(groupAge)

					compIds = list(CompKeyword.objects.filter(fk_cp_project_id=cpId).values_list('fk_keyword_id').order_by('fk_keyword_id').all())

					if compIds:
						totalKeywordLen = len(singleProject.cp_total_keyword)
						if (groupAge == (totalKeywordLen + 1) and totalKeywordLen > 0) or (groupAge == totalKeywordLen and totalKeywordLen > 0):
							# print("MAIN IF PART", "\n") 
							single_date = currdate + timedelta(1)
							allKeywords = Keyword.objects.filter(__raw__={'id': {'$in': compIds}}, fk_group_id=cpGroupId, created_date__lt=single_date).all()
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

								if rankLength >= rankIndexCount and rankLength > 1:
									dayDiff = rankFormulation(keyIns.rank[0], keyIns.rank[1])
									if dayDiff > 0:
										improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id)) 
									elif dayDiff < 0:
										declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id)) 
							
							sinceStartExplode = mainSinceStartCalc(compIds, cpUserId, cpId, cpGroupId, 0)

							existCount = 0
							newCount = 0 

							# UPDATE MAIN SCORE METER
							if groupAge == len(singleProject.mn_score_meter): 
								cProjectUpdate.update(
									mn_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)),  
									updated_date=datetime.now() 
								)
								existCount += 1
							else:
								cProjectUpdate.update(
									push__mn_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)),
									updated_date=datetime.now() 
								)
								newCount += 1

							# UPDATE MAIN ACTIVITY METER
							if groupAge == len(singleProject.mn_activity_level): 
								cProjectUpdate.update(
									mn_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)), 
									updated_date=datetime.now() 
								)
								existCount += 1
							else:
								cProjectUpdate.update(
									push__mn_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)),
									updated_date=datetime.now()
								) 
								newCount += 1

							# UPDATE MAIN POSITION METER
							if groupAge == len(singleProject.mn_since_position): 
								cProjectUpdate.update(
									mn_since_position__0=str(sinceStartExplode),   
									updated_date=datetime.now()
								)
								existCount += 1
							else:
								cProjectUpdate.update( 
									push__mn_since_position__0=str(sinceStartExplode),    
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

							# print("MAIN ELSE PART", "\n")
							cProjectUpdate.update(
								mn_score_meter=[],
								mn_activity_level=[],
								mn_since_position=[],  
								mn_top_score=None, 
								updated_date=datetime.now()
							)  

							#DATE DIFFERENCE FROM DATE - TO DATE  
							for single_date in (singleProject.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):   

								allKeywords = Keyword.objects.filter(__raw__={'id': {'$in': compIds}}, fk_group_id=cpGroupId, created_date__lt=single_date).all()
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
								
								sinceStartExplode = mainSinceStartCalc(compIds, cpUserId, cpId, cpGroupId, rankIndexCount)  

								cProjectUpdate.update(
									push__mn_score_meter__0=str(scoreMeterCalc(scorePerDay, allKeywordsLen)),
									push__mn_activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, allKeywordsLen)), 
									push__mn_since_position__0=str(sinceStartExplode),
									push__cp_total_keyword__0=str(allKeywordsLen),  
									updated_date=datetime.now()   
								)  
								rankIndexCount = rankIndexCount - 1  
							# End FOR
						# END IF

						# Top tracker Score Update	
						topScoreUpdate(cpId, incomingSystem)  
					else: 
						watchdog.coreLog(" > MAIN FORMULTE >> EMPTY COMPETITOR PROJECT >>> CP_ID = "+str(cpId), incomingSystem)
				else:
					watchdog.coreLog(" > MAIN FORMULTE >> COMPETITOR PROJECT HAS NO ATTRIBUTE ID >>> CP_ID = "+str(compProId), incomingSystem)
			else:
				watchdog.coreLog(" > MAIN FORMULTE >> NO COMPETITOR PROJECT FOUND >>> CP_ID = "+str(compProId), incomingSystem) 
		else:
			watchdog.coreLog(" > MAIN FORMULTE >> COMPALYSE SYSTEM NOT FOUND >>> G_ID = "+str(groupId)+" CP_ID = "+str(compProId), incomingSystem) 

	except Exception as e:
		# UPDATE ERROR ON THE KEYWPRD FIELD as "MDCERR" 
		watchdog.coreLog(" > MAIN FORMULTE >> COMPALYSE SYSTEM >> ERROR = " +str(e)+ " >>> G_ID = "+str(groupId)+" CP_ID = "+str(compProId), incomingSystem) 
		
	return True
