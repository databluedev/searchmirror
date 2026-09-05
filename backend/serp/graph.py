from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.serializers import *
from django.conf import settings
from datetime import date,datetime,timedelta,time
import calendar
from rest_framework.decorators import api_view
import csv, os
from account import verify as authPermission
from serp.common import *
from django.utils import timezone
from shared.scoring import classify_activity_level
from shared.scoring import calculate_visibility_history


#Graph API
@api_view(['POST','GET'])
def keywordgraph(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = request.data['userid']
        grpid = request.data['grpid']
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                datatype = request.data['type']
                idg = request.data['idg']
                if userid and grpid and idg:
                    keyIns = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid,id=idg).first()

                    kwchartdetails = {}
                    if datatype == 'filter':
                        startpos = int(request.data['s_p'])
                        endpos = int(request.data['e_p'])
                        kwchartdetails['k_r'] = keyIns.rank[startpos:endpos] if len(keyIns.rank) > endpos else keyIns.rank[0:len(keyIns.rank)]

                        # kw graph notes
                        startdate = keyIns.lastranked_date - timedelta(days=startpos)
                        kwNotesCnt = []
                        kwNotesMnthCnt = []
                        # kwNotesDate = []
                        NoteIns = kwNotes.objects.filter(fk_keyword_id=idg, fk_user_id=userid, fk_group_id=grpid).count()

                        if NoteIns > 0:
                            for i in range(0, len(kwchartdetails['k_r'])):
                                selectdate = startdate - timedelta(days=i)
                                start = timezone.make_aware(datetime.combine(selectdate, time.min))
                                end = timezone.make_aware(datetime.combine(selectdate, time.max))
                                NoteIns = kwNotes.objects.filter(fk_keyword_id=idg, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).count()
                                # NoteIns = kwNotes.objects.filter(note_date__range=(start, end)).count()
                                kwNotesCnt.append(NoteIns)

                                if (endpos-startpos) > 92 and int(selectdate.day) == 1 or i+1 == len(kwchartdetails['k_r']):
                                    start = timezone.make_aware(datetime.combine(selectdate.replace(day=1), time.min))
                                    end = timezone.make_aware(datetime.combine(start.replace(day = calendar.monthrange(start.year, start.month)[1]), time.max))
                                    # kwNotesDate.append(start.strftime('%b, %Y'))
                                    
                                    NoteIns = kwNotes.objects.filter(fk_keyword_id=idg, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).count()
                                    # NoteIns = kwNotes.objects.filter(note_date__range=(start, end)).count()
                                    kwNotesMnthCnt.append(NoteIns)
                                else:
                                    kwNotesMnthCnt.append(0)
                                    # kwNotesDate.append('-')


                        kwchartdetails['ntCnt'] = kwNotesCnt
                        kwchartdetails['ntMCnt'] = kwNotesMnthCnt
                        # kwchartdetails['ntdt'] = kwNotesDate
                        start = timezone.make_aware(datetime.combine(keyIns.lastranked_date, time.min))
                        end = timezone.make_aware(datetime.combine(keyIns.lastranked_date, time.max))
                        NoteIns = kwNotes.objects.filter(fk_keyword_id=idg, fk_user_id=userid, fk_group_id=grpid, note_date__range=(start, end)).all().order_by('note_date')
                        # NoteIns = kwNotes.objects.filter(note_date__range=(start, end)).all().order_by('note_date')
                        serializer = kwNotesSerializer(NoteIns, many=True).data

                        return JsonResponse({'status': "true",'kw_gph_dtls': kwchartdetails, 'nts' : serializer })  

                    # kwchartdetails = {}
                    kwchartdetails['k_id'] = idg
                    kwchartdetails['k_r'] = keyIns.rank
                    kwchartdetails['k_n'] = keyIns.keyword
                    kwchartdetails['t_c'] = len(keyIns.rank)
                    kwchartdetails['s_d'] = keyIns.created_date
                    kwchartdetails['e_d'] = keyIns.lastranked_date.date()
                    kwchartdetails['d_n'] = host_domain(keyIns.site_url)

                    return JsonResponse({'status': "true",'kw_gph_dtls': kwchartdetails })  
    
    return JsonResponse({'status':'false','message':'Something went wrong'}) 

@api_view(['POST'])    
def scoremeter(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = request.POST['userid']
        grpid = request.POST['grpid']
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                datatype = request.POST['type']
                grpIns = Groups.objects.filter(id=grpid, fk_user_id=userid) 

                if grpIns.exists(): 
                    grpData = grpIns.first()
                    # Recomputed from the keyword rank arrays, NOT read from
                    # the stored Groups.score_meter / top_score. Those only
                    # move when a ranking run writes them, so between runs
                    # they drift from every other surface: on the seeded
                    # Local Demo Project the snapshot said 34 / 42 while
                    # /erocs_wdt, /homeauth, /projectoverview and
                    # /dashboard_overview all said 37 / 44 from these same
                    # rank arrays. This was the last surface still reading
                    # the snapshot; it now makes the same shared.scoring
                    # call as the other four, so a fifth number cannot
                    # appear.
                    keyword_rank_histories = list(
                        Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid).values_list("rank", flat=True)
                    )
                    score_history = calculate_visibility_history(keyword_rank_histories)

                    if datatype == "filter":
                        startpos = int(request.POST['s_p'])
                        endpos = int(request.POST['e_p'])
                        scoreLimit = score_history[startpos:endpos] if len(score_history) > endpos else score_history[0:len(score_history)] 
                        scorechartDetails = {}
                        scorechartDetails['ss_d'] = list(map(int,[float(i) for i in scoreLimit]))
                        return JsonResponse({'status':'true','data':scorechartDetails})   

                    scoreData = {}
                    if(len(score_history) > 0):
                        liveRatio = score_history[0]
                        scoreData['ps'] = f_to_i(liveRatio)  
                        scoreData['ms'] = f_to_i(max(score_history))
                    else:
                        scoreData['ps'] = 0
                        scoreData['ms'] = 0
                        # scoreData['present'] = 0
                        # scoreData['maxScore'] = 0

                    if(len(score_history) > 1):
                        liveRatio = score_history[0]
                        prevRatio = score_history[1]
                        valRatio = f_to_i(liveRatio) - f_to_i(prevRatio)  
                        scoreData['cp'] = abs(valRatio) 
                        scoreData['st'] = checkstatus(valRatio)
                    else:
                        scoreData['cp'] = 0
                        scoreData['st'] = "-"
                        # scoreData['compare'] = 0
                        # scoreData['status'] = "-"

                    scoreGraphDetails = {}
                    scoreGraphDateTime = []
                    scoreLimitData = []
                    # scoreGraphfullDate = []

                    P_update_date = grpData.updated_date
                    # P_create_date = grpData.created_date
                    # projectname = grpData.group_name
                    # scoreTotalCount = len(grpData.score_meter)

                    scoreLimit = score_history[0:7] if len(score_history) > 7 else score_history[0:len(score_history)] 
                    dates = P_update_date
                    for i in range(0,len(scoreLimit)):
                        dates = P_update_date - timedelta(days=i)
                        scoreGraphDateTime.append(dates.strftime("%m-%d-%Y"))   
                        scoreLimitData.append(f_to_i(scoreLimit[i]))

                    scoreGraphDetails['ss_d'] = scoreLimitData
                    scoreGraphDetails['ss_dd'] = scoreGraphDateTime
                    scoreGraphDetails['p_n'] = grpData.group_name
                    scoreGraphDetails['t_c'] = len(score_history)
                    scoreGraphDetails['s_d'] = grpData.created_date.strftime("%m-%d-%Y")
                    scoreGraphDetails['e_d'] = P_update_date.strftime("%m-%d-%Y")
                    return JsonResponse({'status':'true','result':scoreData, 'data':scoreGraphDetails})   

    return JsonResponse({'status':'false','message':"Something went wrong"})   

def activitygroup(actValue):
    activityGroupVal = list(map(str, actValue.split('|')))
    if len(activityGroupVal) == 3:
        return activityGroupVal[0]
    else:
        return 0

@api_view(['POST'])    
def activitylevel(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = request.POST['userid']
        grpid = request.POST['grpid']

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                datatype = request.POST['type']
                grpInsdata = Groups.objects.filter(id=grpid, fk_user_id=userid)

                if grpInsdata.exists():
                    grpIns = grpInsdata.first()
                    bargraphdetails = {}
                    # barTotalCount = len(grpIns.activity_level)
                    if datatype == "filter":
                        startpos = int(request.POST['s_p'])
                        endpos = int(request.POST['e_p'])
                        # barGrpLimit = grpIns.activity_level[startpos:endpos] if len(grpIns.activity_level) > endpos else grpIns.activity_level[0:len(grpIns.activity_level)] 
                    else:
                        startpos = 0
                        endpos = 15
                        # barGrpLimit = grpIns.activity_level[0:15] if len(grpIns.activity_level) > 15 else grpIns.activity_level[0:len(grpIns.activity_level)] 
                                    
                    barGrpLimit = grpIns.activity_level[startpos:endpos] if len(grpIns.activity_level) > endpos else grpIns.activity_level[0:len(grpIns.activity_level)] 
                    today = grpIns.updated_date
                    # Projt_create_date = grpIns.created_date
                    # projectname = grpIns.group_name

                    barGraphDateTime = []
                    barGraphImproved = []
                    barGraphDeclined = []

                    for i in reversed(range(len(barGrpLimit))):
                        activityGroupData = list(map(str, barGrpLimit[i].split('|')))
                        if len(activityGroupData) == 3:
                            barGraphImproved.insert(0, str(activityGroupData[1]))
                            barGraphDeclined.insert(0, "-"+str(activityGroupData[2])) 
                        else:
                            barGraphImproved.insert(0, str("0"))
                            barGraphDeclined.insert(0, str("0")) 

                        if datatype != "filter":
                            dates = today - timedelta(days=i)
                            barGraphDateTime.insert(0, dates.strftime("%m-%d-%Y")) 

                    bargraphdetails['i_d'] = barGraphImproved
                    bargraphdetails['d_d'] = barGraphDeclined 

                    if datatype != "filter":
                        bargraphdetails['g_dd']= barGraphDateTime
                        bargraphdetails['t_c'] = len(grpIns.activity_level)
                        bargraphdetails['p_n'] = grpIns.group_name
                        bargraphdetails['s_d'] = grpIns.created_date.strftime("%m-%d-%Y")
                        bargraphdetails['e_d'] = today.strftime("%m-%d-%Y")

                        valCard = "-"
                        # graphnormal = []
                        if len(grpIns.activity_level) > 0:   
                            groupToday = activitygroup(grpIns.activity_level[0]) 
                            valCard = classify_activity_level(groupToday)
                            
                        #     graphnormal.append({     
                        #         'posKey':Keyword.objects.filter(fk_group_id=grpid, daymark="up").count(),
                        #         'negKey':Keyword.objects.filter(fk_group_id=grpid, daymark="down").count() 
                        #     }) 
                        # else:

                        graphnormal = {     
                            'pk':Keyword.objects.filter(fk_group_id=grpid, daymark="up").count(),
                            'nk':Keyword.objects.filter(fk_group_id=grpid, daymark="down").count()  
                        }

                        return JsonResponse({'status': "true",'result':graphnormal, 'data':bargraphdetails, 'prg':valCard})  
                    # else:
                        # barchartdetails = {} 
                        # barchartdetails['imp_d'] = barGraphImproved
                        # barchartdetails['dec_d'] = barGraphDeclined
                        # barchartdetails['gph_dd'] = barGraphDateTime
                    return JsonResponse({'status': "true",'data': bargraphdetails})  
    
    return JsonResponse({'status':'false','message':"Something went wrong"})  

def sincestartgroup(startVal, startPos):
    startGroupVal = list(map(int, startVal.split('|')))
    if len(startGroupVal) == 3: 
        return str(abs(f_to_i(startGroupVal[0]))) + "~" + str(checkstatus(f_to_i(startGroupVal[0])))+"~"+ str(abs(f_to_i(startPos)))
    else:
        return str(0) + "~" + str(checkstatus(0)) + "~" + str(0)

def old_sincestartgroup(posValue, startVal, startPos):
    startGroupVal = list(map(int, startVal.split('|')))
    if len(startGroupVal) == 3: 
        return posValue + "~" + str(abs(f_to_i(startGroupVal[0]))) + "~" + str(checkstatus(f_to_i(startGroupVal[0])))+"~"+ str(abs(f_to_i(startPos))) +"~"+ str(abs(f_to_i(startGroupVal[1]))) +"~"+ str(abs(f_to_i(startGroupVal[2])))
    else:
        return posValue + "~" + str(0) + "~" + str(checkstatus(0)) + "~" + str(0) + "~" + str(0) + "~" + str(0)

@api_view(['POST'])    
def sincestartlevel(request):  
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = request.POST['userid']
        grpid = request.POST['grpid'] 

        if userid and grpid:

            if userid.isdigit() and grpid.isdigit():
                datatype = request.POST['type']
                grpInsdata = Groups.objects.filter(id=grpid, fk_user_id=userid) 
                if grpInsdata:
                    grpIns = grpInsdata.first() 
                    P_update_date = grpIns.updated_date 
                    # P_create_date = grpIns.created_date 
                    # projectname = grpIns.group_name
                    # sinceTotalCount = len(grpIns.since_start)

                    if datatype == "filter":
                        startpos = int(request.POST['s_p'])
                        endpos = int(request.POST['e_p'])
                    else:
                        startpos = 0
                        endpos = 7
                        # startLimit = grpIns.since_start[0:7] if len(grpIns.since_start) > 7 else grpIns.since_start[0:len(grpIns.since_start)] 
                        # startPosition = grpIns.since_position[0:7] if len(grpIns.since_position) > 7 else grpIns.since_position[0:len(grpIns.since_position)]             
                        # totalKeywords = grpIns.total_Keyword[0:7] if len(grpIns.total_Keyword) > 7 else grpIns.total_Keyword[0:len(grpIns.total_Keyword)] 
                    
                    startLimit = grpIns.since_start[startpos:endpos] if len(grpIns.since_start) > endpos else grpIns.since_start[0:len(grpIns.since_start)] 
                    startPosition = grpIns.since_position[startpos:endpos] if len(grpIns.since_position) > endpos else grpIns.since_position[0:len(grpIns.since_position)]             
                    totalKeywords = grpIns.total_Keyword[startpos:endpos] if len(grpIns.total_Keyword) > endpos else grpIns.total_Keyword[0:len(grpIns.total_Keyword)] 
                                
                    graphdata = {}
                    barGraphDates = []
                    barchartDetails = {}
                    
                    barFirstPos = []
                    barSecondPos = []
                    barThirdPos= []
                    barFourthPos= []
                    barMoreThan10=[]
                    barMoreThanLimit=[]
                    # barTotalKeyword = totalKeywords

                    for i in range(0,len(startPosition)):
                        if datatype != "filter":
                            dates = P_update_date - timedelta(days=i)
                            barGraphDates.append(dates.strftime("%m-%d-%Y"))  

                        startPos = list(map(int, startPosition[i].split(',')))     
                        
                        barFirstPos.append(f_to_i(startPos[0]))
                        barSecondPos.append(f_to_i(startPos[1]))
                        barThirdPos.append(f_to_i(startPos[2]))
                        barFourthPos.append(f_to_i(startPos[3]))
                        barMoreThan10.append(f_to_i(startPos[4]))
                        barMoreThanLimit.append(f_to_i(startPos[5]) if len(startPos) > 5 else 0)

                        if i == 0: 
                            last_seven_day = P_update_date - timedelta(days=i)
                            
                            startVal = list(map(str, startLimit[i].split(',')))  
                            startPos = list(map(int, startPosition[i].split(',')))     
                            
                            if len(startVal) == 6 and len(startPos) == 6: 
                                graphdata= {   
                                    'PosI': sincestartgroup(startVal[0], startPos[0]),    
                                    'PosII': sincestartgroup(startVal[1], startPos[1]),
                                    'PosIII': sincestartgroup(startVal[2], startPos[2]),
                                    'PosX': sincestartgroup(startVal[3], startPos[3]),
                                    'PosL': sincestartgroup(startVal[4], startPos[4]), 
                                    'PosD': sincestartgroup(startVal[5], startPos[5]),  
                                }
                                # graphdata.append({   
                                #     'PosI': sincestartgroup("First Position", startVal[0], startPos[0]),    
                                #     'PosII': sincestartgroup("Second Position", startVal[1], startPos[1]),
                                #     'PosIII': sincestartgroup("Third Position", startVal[2], startPos[2]),
                                #     'PosX': sincestartgroup("4-10 Position", startVal[3], startPos[3]),
                                #     'PosL': sincestartgroup("More than 10", startVal[4], startPos[4]), 
                                #     'PosD': sincestartgroup("More than Limit", startVal[5], startPos[5]),  
                                # })

                    barchartDetails['Fst_P'] = barFirstPos
                    barchartDetails['S_P'] = barSecondPos
                    barchartDetails['T_P'] = barThirdPos
                    barchartDetails['F_P'] = barFourthPos
                    barchartDetails['M_10'] = barMoreThan10
                    barchartDetails['M_L'] = barMoreThanLimit
                    barchartDetails['s_k'] = totalKeywords
                        
                    if datatype != "filter":
                        barchartDetails['s_dd'] = barGraphDates
                        barchartDetails['t_c'] = len(grpIns.since_start)
                        barchartDetails['p_n'] = grpIns.group_name
                        barchartDetails['s_d'] = grpIns.created_date.strftime("%m-%d-%Y")
                        barchartDetails['e_d'] = P_update_date.strftime("%m-%d-%Y")
                        # return JsonResponse({'status': "true",'groupname': grpIns.group_name, 'sincedata':graphdata, 'sincebargraphdetails': barchartDetails})     
                        return JsonResponse({'status': "true", 's_d': graphdata, 'data': barchartDetails})     

                    # barchartDetails = {}
                    # barchartDetails['Fst_P'] = barFirstPos
                    # barchartDetails['S_P'] = barSecondPos
                    # barchartDetails['T_P'] = barThirdPos
                    # barchartDetails['F_P'] = barFourthPos
                    # barchartDetails['M_10'] = barMoreThan10
                    # barchartDetails['M_L'] = barMoreThanLimit
                    # barchartDetails['s_k'] = barTotalKeyword

                    return JsonResponse({'status': "true", 'data': barchartDetails})     

    return JsonResponse({'status':'false','message':"Something went wrong"})
