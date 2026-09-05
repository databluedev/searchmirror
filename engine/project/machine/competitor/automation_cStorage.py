from django.conf import settings

from project.machine.models import Keyword, Group
from project.machine.models import CompProject, CompKeyword 
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_
from project.machine.submodels.serpmodels import DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

import requests, json, time
from urllib import parse 
import sys, os, random 
from datetime import datetime, date

from project.machine import watchdog as _wd_

def checkstatus(num):
	if num > 0:
		return 'up'        
	elif num == 0:
		return '-'
	else:
		return 'down'

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
	
def mongopush(engineMode, rowSet):
	try:
		mongoid = rowSet.get('ID')
		liverank = rowSet.get('RANK')   
		url = rowSet.get('URL')
		target = rowSet.get('TARGET')
		reviews = True if float(rowSet.get('RATINGS')) > 0 and float(rowSet.get('RATINGS')) <= 5 else False
		total_ratings = str(rowSet.get('RATINGS')) if float(rowSet.get('RATINGS')) > 0 and float(rowSet.get('RATINGS')) <= 5 else "-"
		total_reviews = str(rowSet.get('REVIEWS')) if int(rowSet.get('REVIEWS')) > 0 else "-"
	 
		snippet_details = rowSet.get('SNIPPET_DETAILS')
		snippets = True if "featured_box" in rowSet.get('SNIPPETS') else False  
		knowledge_panel = True if "knowledge_box" in rowSet.get('SNIPPETS') else False 
		ad_box = True if "ads" in rowSet.get('SNIPPETS') else False  
			
		Keywords = CompKeyword.objects.filter(__raw__= {'id': mongoid}) 
		if Keywords:
			keyIns=Keywords[0] 
			currdate = date.today()
			
			rankArrayCount = len(keyIns.rank)  
			keywordTotalDayCount = int((currdate - keyIns.created_date.date()).days) + 1

			# BEST RANK CALCULATION
			exist_top_rank = keyIns.top_rank
			cal_top_rank = int(liverank) 
			totalrank = list(filter(lambda num: num != 0, list(set(keyIns.rank))))
			if len(totalrank) > 0:
				min_rank = min(totalrank)
				cal_top_rank = int(liverank) if liverank <= min_rank and liverank > 0 else min_rank 

			if exist_top_rank != None and exist_top_rank > 0:
				if cal_top_rank <= exist_top_rank: 
					top_rank = int(cal_top_rank) 
				else:
					top_rank = int(exist_top_rank)
			else: 
				top_rank = int(liverank)   
			
			if keywordTotalDayCount == 1:
				Keywords.update( 
					rank=[]  
				)  
				Keywords.update(
					# push__rank__0=liverank,   #If MAcro Problem avoided Uncomment it
					rank__0=liverank, 
					cp_site_url=url,  
					ranknow=liverank,
					top_rank=int(top_rank),  
					rank_sincestart=liverank,  
					daymark = '-',
					dayval = 0,
					weekmark = '-',
					weekval = 0,
					halfmonthmark = '-',
					halfmonthval = 0, 
					featured_snippet = snippets,
					knowledge_panel = knowledge_panel,
					ads = ad_box,
					review = reviews,
					total_rating=total_ratings,
					total_review=total_reviews, 
					snippets_details=snippet_details,  
					lastranked_date=datetime.now(),  
					modified_date=datetime.now(),
					status_from_start = "-" 
				)
			else:
				status_from_start=keyIns.status_from_start 
				halfmonthmark=keyIns.halfmonthmark
				halfmonthval=keyIns.halfmonthval 
				weekval=keyIns.weekval
				weekmark=keyIns.weekmark
				dayval=keyIns.dayval
				daymark=keyIns.daymark 
				
				since_first_rank = keyIns.rank[-1] if len(keyIns.rank) else 0

				if rankArrayCount >= keywordTotalDayCount: 
					groupDifference = rankArrayCount - keywordTotalDayCount

					if groupDifference > 0:
						watchdog.coreLog(" > RANK OVERFLOW >> CP_KID "+str(mongoid), engineMode) 
						flag = 0
						while flag < groupDifference:
							Keywords.update(pop__rank=-1) 
							flag += 1

					if len(keyIns.rank)>1: 
						day_dif = rankFormulation(liverank, keyIns.rank[1])
						daymark = checkstatus(day_dif)
						dayval = abs(day_dif)
					if len(keyIns.rank)>7:
						week_dif = rankFormulation(liverank, keyIns.rank[7])
						weekmark = checkstatus(week_dif) 
						weekval = abs(week_dif)
					if len(keyIns.rank)>15:
						half_month_dif = rankFormulation(liverank, keyIns.rank[15])
						halfmonthmark = checkstatus(half_month_dif)
						halfmonthval = abs(half_month_dif)
					if len(keyIns.rank) > 1: 
						diff = rankFormulation(liverank, keyIns.rank[-1])
						status_from_start = checkstatus(diff)
					
					Keywords.update(
						rank__0 = liverank
					) 
				else:
					if len(keyIns.rank)>0:    
						day_dif = rankFormulation(liverank, keyIns.rank[0])
						daymark = checkstatus(day_dif) 
						dayval = abs(day_dif)
					if len(keyIns.rank)>6:
						week_dif = rankFormulation(liverank, keyIns.rank[6])
						weekmark = checkstatus(week_dif)
						weekval = abs(week_dif)
					if len(keyIns.rank)>14:
						half_month_dif = rankFormulation(liverank, keyIns.rank[14])
						halfmonthmark = checkstatus(half_month_dif)
						halfmonthval = abs(half_month_dif)
					if len(keyIns.rank) > 1:
						diff = rankFormulation(liverank, keyIns.rank[-1])
						status_from_start = checkstatus(diff)   
					
					Keywords.update (
						# push__rank__0 = liverank,   #If Macro Problem avoided Uncomment it
						rank__0 = liverank, 
					)  
				 
				Keywords.update(  
					ranknow = liverank, 
					top_rank=int(top_rank),   
					cp_site_url = url, 
					daymark = daymark,
					dayval = dayval,
					rank_sincestart=since_first_rank,
					weekmark = weekmark,
					weekval = weekval,  
					halfmonthmark = halfmonthmark,
					halfmonthval = halfmonthval, 
					featured_snippet = snippets,
					knowledge_panel = knowledge_panel,
					ads = ad_box, 
					review = reviews, 
					total_rating=total_ratings,
					total_review=total_reviews, 
					snippets_details=snippet_details,
					lastranked_date=datetime.now(),   
					modified_date=datetime.now(),    
					status_from_start = status_from_start
				)
	except Exception as e:
		# MONGO UPDATE ERROR
		# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON  
		_wd_.coreLog(" > COMPALYSE ERROR ON DATA PUSH", "COMPALYSE")
	return 1 