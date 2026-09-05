from django.shortcuts import render
from django.conf import settings 

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings 

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

def topScoreUpdate(gid, incomingSystem): 
	groupObj = Group.objects.filter(__raw__= {'id': int(gid)}).first()
	if groupObj:
		scoreValue = max(set(map(float, groupObj.score_meter)))
		scoreValue = float("{:.2f}".format(scoreValue)) 
		if groupObj.top_score is None:
			Group.objects.filter(__raw__= {'id': int(gid)}).update(top_score=str(scoreValue)) 
		elif scoreValue > float(groupObj.top_score): 
			Group.objects.filter(__raw__= {'id': int(gid)}).update(top_score=str(scoreValue)) 
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

def timeDifference(startTime, endTime, timeIn):
	diff = endTime - startTime
	if timeIn == "days":
		return diff.days
	elif timeIn == "hours":
		return diff.seconds/3600;
	elif timeIn == "minutes":
		return diff.seconds/60; 
	elif timeIn == "seconds":
		return diff.seconds
	elif timeIn == "microseconds":
		return diff.microseconds
	else:
		return 0  

def sinceStartCalc(userid, grpid, index):
	topset = ["0-1","1-2","2-3","3-10","10-100","0-0"]
	singleSinceStart = [] 
	singleSincePosition = [] 
	rankIndexCount = int(index) - 1 if int(index) > 0 else 0  

	for tset in topset: 
		positiveCount = 0
		negativeCount = 0

		topRankVal = tset.split("-") 

		if len(topRankVal) > 1:
			minVal = int(topRankVal[0])
			maxVal = int(topRankVal[1]) 

			gtRank = 'rank__'+str(rankIndexCount)+'__gt'
			lteRank = 'rank__'+str(rankIndexCount)+'__lte'
			eqRank = 'rank__'+str(rankIndexCount)   

			if minVal == 0 and maxVal == 0: 
				headerKeywordCount = Keyword.objects.filter((Q(**{eqRank: 0})) & Q(fk_user_id=userid) & Q(fk_group_id=grpid)).count() 
				positiveCount = 0
				negativeCount = 0
			else:
				positiveFilter = Keyword.objects.filter(
					Q(fk_user_id=userid) & Q(fk_group_id=grpid)	
					& (Q(rank_sincestart=0) | Q(rank_sincestart__gt=maxVal)) 
					& (Q(**{gtRank: minVal}) & Q(**{lteRank: maxVal}))
				)  

				negativeFilter = Keyword.objects.filter( 
					Q(fk_user_id=userid) & Q(fk_group_id=grpid)	
					& (Q(rank_sincestart__gt=minVal) & Q(rank_sincestart__lte=maxVal)) 
					& (Q(**{eqRank: 0}) | Q(**{gtRank: maxVal}))     
				)  

				headerKeywordCount = Keyword.objects.filter((Q(**{gtRank: minVal}) & Q(**{lteRank: maxVal})) & Q(fk_user_id=userid) & Q(fk_group_id=grpid)).count() 

				positiveCount = positiveFilter.count() 
				negativeCount = negativeFilter.count() 

			markValue = positiveCount - negativeCount 
			# CHANGE | POSITIVE | NEGATIVE 
			singleSinceStart.append(str(markValue)+"|"+str(positiveCount)+"|"+str(negativeCount))    
			singleSincePosition.append(str(headerKeywordCount)) 
		else:
			# CHANGE | POSITIVE | NEGATIVE 
			singleSinceStart.append("0|0|0")     
			singleSincePosition.append("0")  

	return ','.join(map(str, singleSinceStart))+"~~"+','.join(map(str, singleSincePosition)) 

def resetDashboard():
	Group.objects.update(   
		score_meter=[],
		activity_level=[],
		since_start=[],
		since_position=[], 
		total_Keyword=[], 
		updated_date=datetime.now()   
	);
	return "OK" 

def dashboardNewGraph(incomingSystem, incomingId):   
	startTime = datetime.now()
	totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)      
	currdate = date.today() 
	calcSystemUpdate = []   
	calcSystemAll = []  

	if incomingSystem == "MANUAL":
		Groups = Group.objects.filter(__raw__= {'id': int(incomingId)}).all()  
	elif incomingSystem == "ENGINE" and int(incomingId) > 0: 
		Groups = Group.objects.filter(__raw__= {'id': int(incomingId)}).all()  
	else: 
		Groups = Group.objects.all() 

	watchdog.coreLog(" > DASHBOARD CALCULATION STARTED ", incomingSystem) 
	for GroupIns in Groups:
		if GroupIns.id: 
			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			userid = GroupIns.fk_user_id
			rankIndexCount = int(groupAge) 

			if len(singleGroup.score_meter) > groupAge:
				groupDifference = len(singleGroup.score_meter) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__score_meter=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.activity_level) > groupAge:
				groupDifference = len(singleGroup.activity_level) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__activity_level=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.since_start) > groupAge:
				groupDifference = len(singleGroup.since_start) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_start=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.since_position) > groupAge:
				groupDifference = len(singleGroup.since_position) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_position=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.total_Keyword) > groupAge:
				groupDifference = len(singleGroup.total_Keyword) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__total_Keyword=-1, updated_date=datetime.now())
					flag += 1 

			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			rankIndexCount = int(groupAge)

			# UPDATE GROUP NAME
			resetGrpDomain = Keyword.objects.filter(fk_group_id = int(incomingId), ranknow__gt=0).first()  
			if resetGrpDomain:
				domainNameParse = extract_protocol_domain(resetGrpDomain.site_url)
				if domainNameParse: 
					singleGroupUpdate.update(domain_name=domainNameParse)

			if (groupAge == (len(singleGroup.total_Keyword) + 1) and len(singleGroup.total_Keyword) > 0) or (groupAge == len(singleGroup.total_Keyword)  and len(singleGroup.total_Keyword) > 0):
				single_date = currdate + timedelta(1)
				allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all() 
				scorePerDay = defaultdict(int) 
				improvedKeywords = []
				declinedKeywords = []  

				for keyIns in allKeywords:  
					if len(keyIns.rank) > 0:  
						if keyIns.rank[0] == 1:
							scorePerDay['eq__first'] += 1
						elif keyIns.rank[0] == 2:
							scorePerDay['eq__second'] += 1
						elif keyIns.rank[0] == 3:
							scorePerDay['eq__third'] += 1
						elif keyIns.rank[0] <= 10 and keyIns.rank[0] > 3:  
							scorePerDay['gte__four__lte__ten'] += 1
						elif keyIns.rank[0] > 10 and keyIns.rank[0] <= totalRankLength:  
							scorePerDay['gt__ten__lte__limit'] += 1  
						else: 
							scorePerDay['gt__limit'] += 1 
					else: 
						scorePerDay['gt__limit'] += 1  

					if rankIndexCount >= len(keyIns.rank) and len(keyIns.rank) > 1:   
						dayDiff = rankFormulation(keyIns.rank[0], keyIns.rank[1])   
						if dayDiff > 0:
							improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
						elif dayDiff < 0:
							declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  

				sinceStartExplode = sinceStartCalc(userid, GroupIns.id, 0).split("~~")
				
				existCount = 0
				newCount = 0

				if groupAge == len(singleGroup.score_meter): 
					singleGroupUpdate.update(
						score_meter__0=str(scoreMeterCalc(scorePerDay, len(allKeywords))),
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__score_meter__0=str(scoreMeterCalc(scorePerDay, len(allKeywords))),
						updated_date=datetime.now() 
					)
					newCount += 1

				if groupAge == len(singleGroup.activity_level): 
					singleGroupUpdate.update(
						activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))),
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))),
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.since_start): 
					singleGroupUpdate.update(
						since_start__0=str(sinceStartExplode[0]),    
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__since_start__0=str(sinceStartExplode[0]),    
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.since_position): 
					singleGroupUpdate.update(
						since_position__0=str(sinceStartExplode[1]),   
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update( 
						push__since_position__0=str(sinceStartExplode[1]),   
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.total_Keyword): 
					singleGroupUpdate.update(
						total_Keyword__0=str(len(allKeywords)), 
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__total_Keyword__0=str(len(allKeywords)),
						updated_date=datetime.now()
					)
					newCount += 1

				if existCount > 0 and newCount > 0:
					calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("BOTH"))
				else: 
					if existCount > 0:
						calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("EXIST"))

					if newCount > 0:
						calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("NEW")) 
			else:  
				calcSystemAll.insert(0, str(GroupIns.id)) 

				#replace update array
				singleGroupUpdate.update(
					score_meter=[],
					activity_level=[],
					since_start=[],
					since_position=[],  
					total_Keyword=[], 
					updated_date=datetime.now()
				)  

				#DATE DIFFERENCE FROM DATE - TO DATE  
				for single_date in (singleGroup.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):   
					allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all() 

					scorePerDay = defaultdict(int) 
					improvedKeywords = []
					declinedKeywords = [] 

					for keyIns in allKeywords:  
						if len(keyIns.rank) >= rankIndexCount:
							if keyIns.rank[rankIndexCount - 1] == 1:
								scorePerDay['eq__first'] += 1
							elif keyIns.rank[rankIndexCount - 1] == 2:
								scorePerDay['eq__second'] += 1
							elif keyIns.rank[rankIndexCount - 1] == 3:
								scorePerDay['eq__third'] += 1
							elif keyIns.rank[rankIndexCount - 1] <= 10 and keyIns.rank[rankIndexCount - 1] > 3:  
								scorePerDay['gte__four__lte__ten'] += 1
							elif keyIns.rank[rankIndexCount - 1] > 10 and keyIns.rank[rankIndexCount - 1] <= totalRankLength: 
								scorePerDay['gt__ten__lte__limit'] += 1 
							else: 
								scorePerDay['gt__limit'] += 1
						else: 
							scorePerDay['gt__limit'] += 1   

						if len(keyIns.rank) > rankIndexCount:
							dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
							if dayDiff > 0:
								improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
							elif dayDiff < 0:
								declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  
					
					sinceStartExplode = sinceStartCalc(userid, GroupIns.id, rankIndexCount).split("~~")
					singleGroupUpdate.update(
						push__score_meter__0=str(scoreMeterCalc(scorePerDay, len(allKeywords))),
						push__activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))), 
						push__since_start__0=str(sinceStartExplode[0]),    
						push__since_position__0=str(sinceStartExplode[1]),   
						push__total_Keyword__0=str(len(allKeywords)), 
						updated_date=datetime.now()   
					)  

					rankIndexCount = rankIndexCount - 1
				# End FOR
			# END IF

			# Top tracker Score Update	
			topScoreUpdate(int(GroupIns.id), incomingSystem)  

	if len(calcSystemUpdate) > 0 or len(calcSystemAll) > 0:  
		watchdog.coreLog(" > DASHBOARD CALCULATION COMLETED >> UPDATE: "+str(calcSystemUpdate)+" >> ALL: "+str(calcSystemAll), incomingSystem)
	else:
		watchdog.coreLog(" > DASHBOARD CALCULATION FAILED ", incomingSystem) 

	return True

# USE ONLY FOR THE PURPOSE RESET ALL GRAPH DATA 
def dashboardResetGraph(incomingSystem, incomingId): 
	startTime = datetime.now()
	totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)      
	currdate = date.today() 
	calcSystemUpdate = []   
	calcSystemAll = []  

	Groups = Group.objects.all() 

	watchdog.coreLog(" > DASHBOARD CALCULATION STARTED ", incomingSystem) 

	for GroupIns in Groups:
		if GroupIns.id: 
			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			userid = GroupIns.fk_user_id
			rankIndexCount = int(groupAge) 

			if len(singleGroup.score_meter) > groupAge:
				groupDifference = len(singleGroup.score_meter) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__score_meter=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.activity_level) > groupAge:
				groupDifference = len(singleGroup.activity_level) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__activity_level=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.since_start) > groupAge:
				groupDifference = len(singleGroup.since_start) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_start=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.since_position) > groupAge:
				groupDifference = len(singleGroup.since_position) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_position=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.total_Keyword) > groupAge:
				groupDifference = len(singleGroup.total_Keyword) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__total_Keyword=-1, updated_date=datetime.now())
					flag += 1 

			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			rankIndexCount = int(groupAge)

			# UPDATE GROUP NAME
			resetGrpDomain = Keyword.objects.filter(fk_group_id = int(incomingId), ranknow__gt=0).first()  
			if resetGrpDomain:
				domainNameParse = extract_protocol_domain(resetGrpDomain.site_url)
				if domainNameParse: 
					singleGroupUpdate.update(domain_name=domainNameParse)

			  
			calcSystemAll.insert(0, str(GroupIns.id)) 

			#replace update array
			singleGroupUpdate.update(
				score_meter=[],
				activity_level=[],
				since_start=[],
				since_position=[],  
				total_Keyword=[], 
				updated_date=datetime.now()
			)  

			#DATE DIFFERENCE FROM DATE - TO DATE  
			for single_date in (singleGroup.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):   
				allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all() 

				scorePerDay = defaultdict(int) 
				improvedKeywords = []
				declinedKeywords = [] 

				for keyIns in allKeywords:  
					if len(keyIns.rank) >= rankIndexCount:
						if keyIns.rank[rankIndexCount - 1] == 1:
							scorePerDay['eq__first'] += 1
						elif keyIns.rank[rankIndexCount - 1] == 2:
							scorePerDay['eq__second'] += 1
						elif keyIns.rank[rankIndexCount - 1] == 3:
							scorePerDay['eq__third'] += 1
						elif keyIns.rank[rankIndexCount - 1] <= 10 and keyIns.rank[rankIndexCount - 1] > 3:  
							scorePerDay['gte__four__lte__ten'] += 1
						elif keyIns.rank[rankIndexCount - 1] > 10 and keyIns.rank[rankIndexCount - 1] <= totalRankLength: 
							scorePerDay['gt__ten__lte__limit'] += 1 
						else: 
							scorePerDay['gt__limit'] += 1
					else: 
						scorePerDay['gt__limit'] += 1   

					if len(keyIns.rank) > rankIndexCount:
						dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
						if dayDiff > 0:
							improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
						elif dayDiff < 0:
							declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  
				
				sinceStartExplode = sinceStartCalc(userid, GroupIns.id, rankIndexCount).split("~~")
				singleGroupUpdate.update(
					push__score_meter__0=str(scoreMeterCalc(scorePerDay, len(allKeywords))),
					push__activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))), 
					push__since_start__0=str(sinceStartExplode[0]),    
					push__since_position__0=str(sinceStartExplode[1]),   
					push__total_Keyword__0=str(len(allKeywords)), 
					updated_date=datetime.now()   
				)  

				rankIndexCount = rankIndexCount - 1
			# End FOR

			# Top tracker Score Update	
			topScoreUpdate(int(GroupIns.id), incomingSystem)  

	if len(calcSystemUpdate) > 0 or len(calcSystemAll) > 0:  
		watchdog.coreLog(" > DASHBOARD CALCULATION COMLETED >> UPDATE: "+str(calcSystemUpdate)+" >> ALL: "+str(calcSystemAll), incomingSystem)
	else:
		watchdog.coreLog(" > DASHBOARD CALCULATION FAILED ", incomingSystem) 

	return True

def dashboardZeroRankGraph(incomingSystem, incomingId):  
	startTime = datetime.now()
	totalRankLength = int(settings.SCRAP_DATA_PER_PAGE) if settings.SCRAP_DATA_PER_PAGE >= 100 else int(100)      
	currdate = date.today() 
	calcSystemUpdate = []   
	calcSystemAll = []  

	if incomingSystem == "MANUAL":
		Groups = Group.objects.filter(__raw__= {'id': int(incomingId)}).all()  
	elif incomingSystem == "ENGINE" and int(incomingId) > 0: 
		Groups = Group.objects.filter(__raw__= {'id': int(incomingId)}).all()  
	else: 
		return False

	watchdog.coreLog(" > ZERO RANK DASHBOARD CALCULATION STARTED ", incomingSystem) 
	for GroupIns in Groups:
		if GroupIns.id: 
			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			userid = GroupIns.fk_user_id
			rankIndexCount = int(groupAge) 

			if len(singleGroup.score_meter) > groupAge:
				groupDifference = len(singleGroup.score_meter) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__score_meter=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.activity_level) > groupAge:
				groupDifference = len(singleGroup.activity_level) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__activity_level=-1, updated_date=datetime.now())
					flag += 1 

			if len(singleGroup.since_start) > groupAge:
				groupDifference = len(singleGroup.since_start) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_start=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.since_position) > groupAge:
				groupDifference = len(singleGroup.since_position) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__since_position=-1, updated_date=datetime.now())
					flag += 1

			if len(singleGroup.total_Keyword) > groupAge:
				groupDifference = len(singleGroup.total_Keyword) - groupAge
				flag = 1
				while flag <= groupDifference:
					singleGroupUpdate.update(pop__total_Keyword=-1, updated_date=datetime.now())
					flag += 1 

			singleGroupUpdate = Group.objects.filter(__raw__= {'id': GroupIns.id})
			singleGroup = singleGroupUpdate.first() 
			groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
			rankIndexCount = int(groupAge)

			if (groupAge == (len(singleGroup.total_Keyword) + 1) and len(singleGroup.total_Keyword) > 0) or (groupAge == len(singleGroup.total_Keyword)  and len(singleGroup.total_Keyword) > 0):
				single_date = currdate + timedelta(1)
				allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all() 
				
				existCount = 0
				newCount = 0

				if groupAge == len(singleGroup.score_meter): 
					singleGroupUpdate.update(
						score_meter__0=str("0.0"),
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__score_meter__0=str("0.0"),
						updated_date=datetime.now() 
					)
					newCount += 1

				if groupAge == len(singleGroup.activity_level): 
					singleGroupUpdate.update(
						activity_level__0=str("0.0|0|0"),
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__activity_level__0=str("0.0|0|0"),
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.since_start): 
					singleGroupUpdate.update(
						since_start__0=str("0|0|0,0|0|0,0|0|0,0|0|0,0|0|0,0|0|0"),    
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__since_start__0=str("0|0|0,0|0|0,0|0|0,0|0|0,0|0|0,0|0|0"),
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.since_position): 
					singleGroupUpdate.update(
						since_position__0=str("0,0,0,0,0,0"),
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update( 
						push__since_position__0=str("0,0,0,0,0,0"),
						updated_date=datetime.now()
					)
					newCount += 1

				if groupAge == len(singleGroup.total_Keyword): 
					singleGroupUpdate.update(
						total_Keyword__0=str(len(allKeywords)), 
						updated_date=datetime.now() 
					)
					existCount += 1
				else:
					singleGroupUpdate.update(
						push__total_Keyword__0=str(len(allKeywords)),
						updated_date=datetime.now()
					)
					newCount += 1

				if existCount > 0 and newCount > 0:
					calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("BOTH"))
				else: 
					if existCount > 0:
						calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("EXIST"))

					if newCount > 0:
						calcSystemUpdate.insert(0, str(GroupIns.id)+"|"+str("NEW")) 
			else:  
				calcSystemAll.insert(0, str(GroupIns.id)) 

				#replace update array
				singleGroupUpdate.update(
					score_meter=[],
					activity_level=[],
					since_start=[],
					since_position=[],  
					total_Keyword=[], 
					updated_date=datetime.now()
				)  

				#DATE DIFFERENCE FROM DATE - TO DATE  
				for single_date in (singleGroup.created_date.date() + timedelta(n + 1) for n in range(0, int(groupAge), 1)):
					allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all() 

					scorePerDay = defaultdict(int) 
					improvedKeywords = []
					declinedKeywords = [] 

					for keyIns in allKeywords:  
						if len(keyIns.rank) >= rankIndexCount:
							if keyIns.rank[rankIndexCount - 1] == 1:
								scorePerDay['eq__first'] += 1
							elif keyIns.rank[rankIndexCount - 1] == 2:
								scorePerDay['eq__second'] += 1
							elif keyIns.rank[rankIndexCount - 1] == 3:
								scorePerDay['eq__third'] += 1
							elif keyIns.rank[rankIndexCount - 1] <= 10 and keyIns.rank[rankIndexCount - 1] > 3:  
								scorePerDay['gte__four__lte__ten'] += 1
							elif keyIns.rank[rankIndexCount - 1] > 10 and keyIns.rank[rankIndexCount - 1] <= totalRankLength: 
								scorePerDay['gt__ten__lte__limit'] += 1 
							else: 
								scorePerDay['gt__limit'] += 1
						else: 
							scorePerDay['gt__limit'] += 1   

						if len(keyIns.rank) > rankIndexCount:
							dayDiff = rankFormulation(keyIns.rank[rankIndexCount - 1], keyIns.rank[rankIndexCount]) 
							if dayDiff > 0:
								improvedKeywords.insert(0, str(dayDiff)+" & "+str(keyIns.id))
							elif dayDiff < 0:
								declinedKeywords.insert(0,  str(dayDiff)+" & "+str(keyIns.id))  
					
					sinceStartExplode = sinceStartCalc(userid, GroupIns.id, rankIndexCount).split("~~")
					singleGroupUpdate.update(
						push__score_meter__0=str(scoreMeterCalc(scorePerDay, len(allKeywords))),
						push__activity_level__0=str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))), 
						push__since_start__0=str(sinceStartExplode[0]),    
						push__since_position__0=str(sinceStartExplode[1]),   
						push__total_Keyword__0=str(len(allKeywords)), 
						updated_date=datetime.now()   
					)  

					rankIndexCount = rankIndexCount - 1
				# End FOR
			# END IF

			# Top tracker Score Update
			topScoreUpdate(int(GroupIns.id), incomingSystem)  

	if len(calcSystemUpdate) > 0 or len(calcSystemAll) > 0:  
		watchdog.coreLog(" > ZERO RANK DASHBOARD CALCULATION COMLETED >> UPDATE: "+str(calcSystemUpdate)+" >> ALL: "+str(calcSystemAll), incomingSystem)
	else:
		watchdog.coreLog(" > ZERO RANK DASHBOARD CALCULATION FAILED ", incomingSystem)

	return True
