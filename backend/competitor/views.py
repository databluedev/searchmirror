# from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import JsonResponse


import os, json
from .models import *
from .serializers import *
from serp.models import *
from account.models import Account  
from serp.common import *
from serp.engine_trigger import trigger_engine_competitor, trigger_engine_competitor_crawl
from django.conf import settings
from account import verify as authPermission
import validators
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from shared.scoring import calculate_visibility_history, calculate_visibility_score


def _load_unwanted_domains():
    """Domains excluded from competitors (social, community, forum, generic).

    Optional by design: a missing or unreadable filter file yields an empty set
    so the competitor list degrades to "show everything" rather than blanking.
    The file previously being absent, combined with the old code letting that
    absence throw, is what showed "no matches" beside a non-zero count.
    """
    try:
        path = os.getcwd() + "/competitor/ai_files/filter_domain_list.json"
        data = json.loads(open(path).read())
        out = set()
        for bucket in ("General", "Social Media", "Other"):
            out.update(data.get(bucket, []))
        return out
    except Exception:
        return set()


def _read_competitor_list(ai_file, search="", limit=100):
    """Read the persisted competitor domain->score map, filtered.

    The domains file is written by compfiles.comppage after analysis; a missing
    file means there is nothing to show yet, so return {}. This is kept distinct
    from a merely-absent filter file, which must never blank a list that exists.
    When `search` is given the unwanted filter is skipped -- the user is looking
    for a specific site.
    """
    try:
        content = json.loads(open(ai_file).read())
    except Exception:
        return {}
    search = (search or "").strip()
    unwanted = set() if search else _load_unwanted_domains()
    out = {}
    for key, val in content.items():
        if len(out) >= limit:
            break
        if search and search not in key:
            continue
        # Match subdomains too: in.linkedin.com is filtered by linkedin.com,
        # m.facebook.com by facebook.com. Exact match is the key == u case.
        if any(key == u or key.endswith("." + u) for u in unwanted):
            continue
        out[key] = val
    return out


# start analysis
def _comp_limit(userid):
    """Return the compatibility limit used by the legacy response shape.

    SearchMirror does not sell plans, so a missing usage row must not disable
    competitors. Existing rows use the same unmetered default.
    """
    row = Accountusage.objects.filter(fb_user_id=userid).values('plan_competitor_limit').first()
    return row['plan_competitor_limit'] if row else UNMETERED


@api_view(['POST'])    
@permission_classes((IsAuthenticated,))
def start_analysis(request):
    userid = request.data['userid']
    grpid = request.data['grpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            SettingsData = Settings.objects.filter(id=1).first()
            # core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 1
            core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 0
            AnalysisCnt = Groups.objects.filter(fk_user_id=userid,competitor_analyse_status__in=["START","SCHD"]).count()
            if core_manual_mode == 1 and AnalysisCnt == 0:
                cgrpCnt = CompProject.objects.filter(fk_user_id=userid).count()
                compLimit = _comp_limit(userid)

                if compLimit <= cgrpCnt:
                    grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).update(competitor_analyse_status="OVER")
                    return JsonResponse({'st':0,'message':'Sorry! You have reached your limit.'})

                kwIns = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid).update(manual_task_allocation="-",manual_task_count=0)
                grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).update(competitor_analyse_status="START")

                # Analysis is queued (START); ask the engine to run it now,
                # so a self-hosted instance does not wait on a scheduler.
                trigger_engine_competitor()

                return JsonResponse({'st':1, 'Ac':AnalysisCnt, 'Eg':core_manual_mode, 'tlk':kwIns})

            return JsonResponse({'st':1, 'Ac':AnalysisCnt, 'Eg':core_manual_mode})

    return JsonResponse({'st':0,'message':'Something went wrong'})


# Aanalysis status (useEffect)
@api_view(['POST'])    
def analysis_status(request):
    userid = request.data['userid']
    grpid = request.data['grpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).first()
            if grpIns:
                analysis_status = grpIns.competitor_analyse_status

                if analysis_status in ["COMP","OVER"]:
                    # totalkwdCnt = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid).count()
                    totalCompetitorCnt = grpIns.competitor_analyse_json["unique_domains"] if grpIns.competitor_analyse_json and "unique_domains" in grpIns.competitor_analyse_json else 0
                    totalkeywordCnt = grpIns.competitor_analyse_json["total_keywords"] if grpIns.competitor_analyse_json and "total_keywords" in grpIns.competitor_analyse_json else 0
                    compLimit = _comp_limit(userid)
                    usedCompCnt = CompProject.objects.filter(fk_user_id=userid).count()
                    complist = CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
                    serializers = CompProjectSerializer(complist, many=True, context=grpIns.competitor_project_array).data
                    
                    if analysis_status == "OVER":
                        # compProject = CompProjectKeywordCreateSerializer(["klusster.com","appdupe.com","appscrip.com"], many=True, context={'userid':userid, 'grpid':grpid, 'data':{"appdupe.com":"appdupe","klusster.com":"klusster","appscrip.com":"appscrip"}}).data
                        return JsonResponse({ 'st':1, 'As':analysis_status, 'Cp':serializers, 'tlk':totalkeywordCnt, 'tcc':totalCompetitorCnt, 'lm':compLimit, 'uCc':usedCompCnt })

                    aiFile = os.getcwd()+"/competitor/ai_files/domains/aiGroup__"+str(grpid)+".json"
                    competitor_list = _read_competitor_list(aiFile)

                    return JsonResponse({ 'st':1, 'As':analysis_status, 'Ad':grpIns.competitor_analyse_json, 'Cp':serializers, 'Cl':competitor_list, 'tlk':totalkeywordCnt, 'tcc':totalCompetitorCnt, 'lm':compLimit, 'uCc':usedCompCnt })
                    # return JsonResponse({ 'st':1, 'As':analysis_status, 'Ad':grpIns.competitor_analyse_json, 'Cp':serializers, 'Cl':competitor_list, 'tlk':totalkeywordCnt, 'lm':compLimit, 'cf':comp_list })

                if analysis_status in ["START","SCHD"]:
                    SettingsData = Settings.objects.filter(id=1).first()
                    # core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 1
                    core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 0

                    analysis_data =  {}
                    kwIns = Keyword.objects.exclude(manual_task_allocation="-").filter(fk_user_id=userid,fk_group_id=grpid)
                    analysis_data["total_keywords"] = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid).count()
                    analysis_data["total_domains"] = sum(list(kwIns.values_list('manual_task_count', flat=True)))
                    analysis_data["track_keywords"] = kwIns.count()

                    return JsonResponse({'st':1, 'As':analysis_status, 'Ad': analysis_data, 'Eg':core_manual_mode })

                return JsonResponse({ 'st':1, 'As':analysis_status })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})

# Competitor widget status (useEffect)
@api_view(['POST'])    
def competitor_widget(request):
    userid = request.data['userid']
    grpid = request.data['grpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid and grpid:
            grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).first()
            if grpIns:
                analysis_status = grpIns.competitor_analyse_status
                totalCompetitorCnt = grpIns.competitor_analyse_json["unique_domains"] if "unique_domains" in grpIns.competitor_analyse_json else 0
                compLimit = _comp_limit(userid)
                usedCompCnt = CompProject.objects.filter(fk_user_id=userid).count()
                
                complist = CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
                serializers = CompProjectSerializer(complist, many=True, context=grpIns.competitor_project_array).data
                
                return JsonResponse({'st':1, 'As':analysis_status, 'Cp':serializers, 'lm':compLimit, 'uCc':usedCompCnt, 'tcc':totalCompetitorCnt })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})

# analysis competitor list
@api_view(['POST'])    
def competitors_list(request):
    # .get(): a no-project screen omits grpid entirely and the literal
    # subscript made that an unhandled 500 instead of the status:false below.
    userid = request.data.get('userid')
    grpid = request.data.get('grpid')

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).first()
            # complist = CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
            # serializers = CompProjectSerializer(complist, many=True, context=grpIns.competitor_project_array).data
            compProjects = list(CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).values_list('cp_domain_name', flat=True))
            totalCompetitorCnt = grpIns.competitor_analyse_json["unique_domains"] if "unique_domains" in grpIns.competitor_analyse_json else 0
            totalkeywordCnt = grpIns.competitor_analyse_json["total_keywords"] if "total_keywords" in grpIns.competitor_analyse_json else 0
            compLimit = _comp_limit(userid)
            usedCompCnt = CompProject.objects.filter(fk_user_id=userid).count()

            # testid = 7
            aiFile = os.getcwd()+"/competitor/ai_files/domains/aiGroup__"+str(grpid)+".json"
            competitor_list = _read_competitor_list(aiFile, search=request.data.get("search", ""))

            return JsonResponse({'st':1, 'Cpd': compProjects, 'Cl':competitor_list, 'tlk':totalkeywordCnt, 'tcc':totalCompetitorCnt, 'lm':compLimit, 'uCc':usedCompCnt})
                
    return JsonResponse({'st':0,'message':'Something went wrong'})

# skip analysis competitor list
@api_view(['POST'])    
@permission_classes((IsAuthenticated,))
def skip_analysis(request):
    userid = request.data['userid']
    grpid = request.data['grpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            compProjectCnt = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid).count()

            if compProjectCnt > 0:
                # kwIns = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid).update(manual_task_allocation="-",manual_task_count=0)
                grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid).update(competitor_analyse_status="OVER")
            
            return JsonResponse({'st':1, 'message':"Analysis skip successful"})
                
    return JsonResponse({'st':0,'message':'Something went wrong'})


# Add competitors
@api_view(['POST'])    
@permission_classes((IsAuthenticated,))
def add_competitors(request):
    userid = request.data['userid']
    grpid = request.data['grpid']
    competitors = request.data['comp']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            usedCompCnt = CompProject.objects.filter(fk_user_id=userid).count()
            compLimit = _comp_limit(userid)

            if (usedCompCnt + len(competitors)) > compLimit:
                remainCount = int(compLimit) - int(usedCompCnt)
                if remainCount <= 0:
                    msg = "You have reached your competitors limit"
                else:
                    msg = "Sorry! only "+str(remainCount)+" competitors are remaining for your account"
                return JsonResponse({'st':0,'message': msg})
            
            usedProjectCompCnt = CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).count()
            if (usedProjectCompCnt + len(competitors)) > 6:
                remainCount = 6 - int(usedProjectCompCnt)
                if remainCount <= 0: 
                    msg = "You have reached your maximum limit for this project"
                elif remainCount == 6: 
                    msg = "Sorry! only "+str(remainCount)+" competitors are allowed per project"
                else:
                    msg = "Sorry! You can add another "+str(remainCount)+" more competitors only"
                return JsonResponse({'st':0,'message': msg})

            serializer = CompProjectCreateSerializer(list(competitors.keys()), many=True, context={'userid':userid, 'grpid':grpid, 'data':competitors})
            # serializer = CompProjectCreateSerializer(["klusster.com","appdupe.com","appscrip.com"], many=True, context={'userid':userid, 'grpid':grpid, 'data':{"appdupe.com":"appdupe","klusster.com":"klusster","appscrip.com":"appscrip"}})
            # projects = list(filter(None, serializer.data))
            projects = serializer.data
        	
            if len(projects) > 0:
                bulk_keywords = CompProject.objects.bulk_create(projects)

            # compProject = CompProjectKeywordCreateSerializer(list(competitors.keys()), many=True, context={'userid':userid, 'grpid':grpid, 'data':competitors}).data

            compPrtIns = list(CompProject.objects.exclude(keyword_ids=[]).filter(fk_user_id=userid,fk_group_id=grpid).values_list('id', flat=True))
            serializers = CompProjectKeywordCreateSerializer(compPrtIns, many=True, context={'userid':userid, 'grpid':grpid}).data

            grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid)
            grpData = grpIns.first()
            competitor_ids = list(grpData.competitor_project_array)
            competitor_ids.extend(compPrtIns)
            grpUpdate = grpIns.update(competitor_analyse_status="OVER",competitor_project_array=competitor_ids,competitor_project_status="INIT")

            # Drive the stage-2 SERP crawl for the just-selected competitors.
            # add_competitors queued INIT above; a self-hosted instance has no
            # scheduler to notice it, so fire the crawl now (fire-and-forget).
            trigger_engine_competitor_crawl()

            compIns = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid).all()
            serializers = CompProjectSerializer(compIns, many=True, context=competitor_ids).data
            
            return JsonResponse({'st':1, 'message':'Competitors add successfully', 'Cp':serializers, 'uCc':usedCompCnt })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})


# Delete competitors
@api_view(['POST'])    
@permission_classes((IsAuthenticated,))
def delete_competitor(request):
    userid = request.data['userid']
    grpid = request.data['grpid']
    competitor_id = request.data['cgrpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit() and str(competitor_id).isdigit():
            
            compPrjtIns = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid,id=competitor_id)
            if compPrjtIns.exists():
                compPrjtIns.delete()

            compKwIns = CompKeyword.objects.filter(fk_user_id=userid,fk_group_id=grpid,fk_cp_project_id=competitor_id)
            if compKwIns.exists():
                compKwIns.delete()

            compPrjtCnt = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid).count()
            grpIns = Groups.objects.filter(fk_user_id=userid,id=grpid)
            if compPrjtCnt == 0:
                grpUpdate = grpIns.update(competitor_analyse_status="VOID",competitor_project_array=[])
            else:
                _grp_row = grpIns.values('competitor_project_array').first()
                competitor_project_ids = _grp_row['competitor_project_array'] if _grp_row else []
                if int(competitor_id) in competitor_project_ids:
                    # competitor_project_ids.remove(competitor_id)
                    list_ids = [pid for pid in competitor_project_ids if pid != int(competitor_id)]
                    grpUpdate = grpIns.update(competitor_project_array=list_ids)

            return JsonResponse({'st':1, 'message':'Competitor deleted successfully' })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})

# competitors keywords' rank page
@api_view(['POST'])    
def competitor_keyword_ranks(request):
    userid = str(request.data['userid'])
    grpid = str(request.data['grpid'])
    # comp_project_id = request.data['cpgrpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            compkws =None
            if "cpgrpid" in request.data and str(request.data['cpgrpid']).isdigit():
                compkws = CompKeyword.objects.filter(fk_cp_project_id=request.data['cpgrpid'],fk_user_id=userid,fk_group_id=grpid)
            
            if compkws == None:
                _proj_row = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid).values('id').first()
                if _proj_row is None:
                    return JsonResponse({"status": "false", "message": "No competitor project found"})
                project_id = _proj_row['id']
                compkws = CompKeyword.objects.filter(fk_cp_project_id=project_id,fk_user_id=userid,fk_group_id=grpid)
            
            compkwIns = compkws.values('id', 'fk_keyword_id', 'keyword', 'ranknow', 'isocode', 'platform','rank','lastranked_date','created_date','top_rank','dayval','daymark','weekval','weekmark','halfmonthval','halfmonthmark','snippets_details','featured_snippet','ads','review','knowledge_panel','total_rating','cp_site_url','isocode','platform').all()
            # account_pages: the out-of-range ceiling is derived from the depth
            # actually searched, and serp_depth is 1 on an account that never
            # chose one.
            from serp.keyword import _account_pages
            from serp.models import Accountusage as _AccUsage
            _acc_pages = _account_pages(_AccUsage.objects.filter(fb_user_id=userid).first())
            serializer = CompKeywordSerializer(compkwIns, many=True, context={'account_pages': _acc_pages}).data
            serializer = list(filter(None, serializer))

            return JsonResponse({'st':1, 'data':serializer })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})


# competitors keywords' rank page Overview
@api_view(['POST'])    
def competitor_overview(request):
    userid = str(request.data['userid'])
    grpid = str(request.data['grpid'])
    # comp_project_id = request.data['cpgrpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid.isdigit() and grpid.isdigit():
            cgrpIns = None
            if "cpgrpid" in request.data and str(request.data['cpgrpid']).isdigit():
                cgrp = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid,id=request.data['cpgrpid'])
                cgrpIns = cgrp.first()

            # cgrpIns = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid).values('cp_group_name','cp_domain_name','cp_score_meter','mn_score_meter','cp_top_score','mn_top_score','cp_since_position','mn_since_position','cp_activity_level').first()['id']
            cAllgrp = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid)
            cgrpCnt = cAllgrp.count()
            
            if cgrpIns == None:
                cgrpIns = cAllgrp.first()
            
            if cgrpIns:
                compLimit = _comp_limit(userid)
                usedCompCnt = CompProject.objects.filter(fk_user_id=userid).count()

                # superData = {}
                superData = {
                    'rv': 0,
                    'sn': 0,
                    'ad': 0,
                    'mrv': 0,
                    'msn': 0,
                    'mad': 0
                }
                compKw = CompKeyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, fk_cp_project_id=cgrpIns.id)
                compKwIns = compKw.values('total_rating','featured_snippet','snippets_details','ads').all()
                superData = compProjectOverviewSerializer(compKwIns, many=True, context={"superData":superData, "xcount":""}).data[-1:][0]
                compKwIds = list(compKw.values_list('fk_keyword_id', flat=True))
                kwIns = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, id__in=compKwIds).values('total_rating','featured_snippet','snippets_details','ads').all()
                # if len(kwIns) > 0:
                superData = compProjectOverviewSerializer(kwIns, many=True, context={"superData":superData, "xcount":"m"}).data[-1:][0]
                
                # runkwCns = CompKeyword.objects.exclude(comp_call_mode__in=["done","fail"]).filter(fk_cp_project_id=cgrpid,fk_group_id=grpid,fk_user_id=userid).count()
                runkwCnt = compKw.exclude(comp_call_mode__in=["done","fail"]).count()

                superData['gn'] = cgrpIns.cp_group_name
                superData['dn'] = cgrpIns.cp_domain_name
                _main_row = Groups.objects.filter(fk_user_id=userid,id=grpid).values('domain_name').first()
                superData['mdn'] = _main_row['domain_name'] if _main_row else ""

                # Compare both domains with the same documented visibility
                # formula and the same shared-keyword denominator. The legacy
                # persisted score arrays used a different scale than Dashboard.
                competitor_rank_rows = list(compKw.values('ranknow', 'rank'))
                main_rank_rows = list(Keyword.objects.filter(
                    fk_user_id=userid,
                    fk_group_id=grpid,
                    id__in=compKwIds,
                ).values('ranknow', 'rank'))
                shared_competitor_ranks = [row['ranknow'] for row in competitor_rank_rows]
                shared_main_ranks = [row['ranknow'] for row in main_rank_rows]
                competitor_history = calculate_visibility_history(
                    [row['rank'] for row in competitor_rank_rows]
                )
                main_history = calculate_visibility_history(
                    [row['rank'] for row in main_rank_rows]
                )

                superData['ss'] = calculate_visibility_score(shared_competitor_ranks)
                superData['yss'] = competitor_history[1] if len(competitor_history) > 1 else superData['ss']
                superData['bss'] = max([superData['ss']] + competitor_history)

                superData['mss'] = calculate_visibility_score(shared_main_ranks)
                superData['myss'] = main_history[1] if len(main_history) > 1 else superData['mss']
                superData['mbss'] = max([superData['mss']] + main_history)

                superData['fp'] = int(cgrpIns.cp_since_position[0].split(',')[0]) if len(cgrpIns.cp_since_position) > 0 else 0
                superData['yfp'] = int(cgrpIns.cp_since_position[1].split(',')[0]) if len(cgrpIns.cp_since_position) > 1 else -1
                
                superData['mfp'] = int(cgrpIns.mn_since_position[0].split(',')[0]) if len(cgrpIns.mn_since_position) > 0 else 0
                superData['myfp'] = int(cgrpIns.mn_since_position[1].split(',')[0]) if len(cgrpIns.mn_since_position) > 1 else -1

                activityGroupData = list(map(str, cgrpIns.cp_activity_level[0].split('|'))) if len(cgrpIns.cp_activity_level) > 0 else [0,0,0]
                if len(activityGroupData) == 3:
                    superData['ik'] = int(activityGroupData[1])
                    superData['dk'] = int(activityGroupData[2])
                else:
                    superData['ik'] = 0
                    superData['dk'] = 0

                activityGroupData = list(map(str, cgrpIns.cp_activity_level[1].split('|'))) if len(cgrpIns.cp_activity_level) > 1 else [-1,-1,-1]
                if len(activityGroupData) == 3:
                    superData['yik'] = int(activityGroupData[1])
                    superData['ydk'] = int(activityGroupData[2])
                else:
                    superData['yik'] = -1
                    superData['ydk'] = -1

                mainActivityGroupData = list(map(str, cgrpIns.mn_activity_level[0].split('|'))) if len(cgrpIns.mn_activity_level) > 0 else [0,0,0]
                if len(mainActivityGroupData) == 3:
                    superData['mik'] = int(mainActivityGroupData[1])
                    superData['mdk'] = int(mainActivityGroupData[2])
                else:
                    superData['mik'] = 0
                    superData['mdk'] = 0

                mainActivityGroupData = list(map(str, cgrpIns.mn_activity_level[1].split('|'))) if len(cgrpIns.mn_activity_level) > 1 else [-1,-1,-1]
                if len(mainActivityGroupData) == 3:
                    superData['myik'] = int(mainActivityGroupData[1])
                    superData['mydk'] = int(mainActivityGroupData[2])
                else:
                    superData['myik'] = -1
                    superData['mydk'] = -1

                return JsonResponse({'st':1, 'mrk':runkwCnt, 'gid':cgrpIns.id, 'al':compLimit-usedCompCnt, 'gA':len(cgrpIns.cp_score_meter), 'data':superData })
            else:
                return JsonResponse({'st':0, 'Cc':cgrpCnt })
                
    return JsonResponse({'st':0,'message':'Something went wrong'})


#Competitor keyword Graph API
@api_view(['POST','GET'])
def competitor_keyword_graph(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = str(request.data['userid'])
        grpid = str(request.data['grpid'])
        cgrpid = str(request.data['cgrpid'])
        if userid and grpid:

            if userid.isdigit() and grpid.isdigit() and cgrpid.isdigit():
                datatype = request.data['type']
                idg = request.data['idg']
                if userid and grpid and idg:
                    keyIns = CompKeyword.objects.filter(fk_user_id=userid,fk_group_id=grpid,fk_cp_project_id=cgrpid,fk_keyword_id=idg).first()
                    mainkeyIns = Keyword.objects.filter(fk_user_id=userid,fk_group_id=grpid,id=idg).first()

                    kwchartdetails = {}
                    if datatype == 'filter':
                        startpos = int(request.data['s_p'])
                        endpos = int(request.data['e_p'])
                        kwchartdetails['k_r'] = keyIns.rank[startpos:endpos] if len(keyIns.rank) > endpos else keyIns.rank[0:len(keyIns.rank)]
                        kwchartdetails['Mk_r'] = mainkeyIns.rank[0:len(kwchartdetails['k_r'])]
                        # kwchartdetails['Mk_r'] = mainkeyIns.rank[startpos:endpos] if len(mainkeyIns.rank) > endpos else mainkeyIns.rank[0:len(kwchartdetails['k_r'])]

                        return JsonResponse({'status': "true",'kw_gph_dtls': kwchartdetails })  

                    # kwchartdetails = {}
                    kwchartdetails['k_id'] = idg
                    kwchartdetails['k_r'] = keyIns.rank
                    kwchartdetails['Mk_r'] = mainkeyIns.rank[0:len(kwchartdetails['k_r'])]
                    kwchartdetails['k_n'] = keyIns.keyword
                    kwchartdetails['t_c'] = len(keyIns.rank)
                    kwchartdetails['s_d'] = keyIns.created_date
                    kwchartdetails['e_d'] = keyIns.lastranked_date.date()
                    kwchartdetails['d_n'] = host_domain(keyIns.site_url)

                    return JsonResponse({'status': "true",'kw_gph_dtls': kwchartdetails })  
    
    return JsonResponse({'status':'false','message':'Something went wrong'}) 



#competitor project page refresh status
@api_view(['POST','GET'])
def competitor_project_status(request):
    if request.method == 'POST':
        userid = request.data['userid'] 
        grpid = request.data['grpid']
        cgrpids = request.data['cgrpids']

        if userid and cgrpids:
            serializers = None
            SettingsData = Settings.objects.filter(id=1).first()
            core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 0

            if core_manual_mode:
                # kwrfCnt = CompKeyword.objects.filter(fk_cp_project_id__in=cgrpids,fk_group=grpid,fk_user=userid,comp_call_status__in=[True]).count()
                # if kwrfCnt > 0:
                #     for cgrpid in cgrpids:
                #         keyIns = CompKeyword.objects.filter(fk_cp_project_id=cgrpid,fk_group=grpid,fk_user=userid,comp_call_status__in=[True]).count()
                #         if keyIns > 0:
                #             rungrpids.append(cgrpid)

                grpIns = Groups.objects.filter(id=grpid,fk_user_id=userid).first()
                if grpIns is None:
                    return JsonResponse({"status": "false", "message": "Project not found"})
                rungrpids = grpIns.competitor_project_array
                if set(cgrpids) != set(rungrpids):
                    complist = CompProject.objects.filter(fk_user_id=userid, fk_group_id=grpid).all()
                    serializers = CompProjectSerializer(complist, many=True, context=grpIns.competitor_project_array).data

            return JsonResponse({'st':1, 'Cp': serializers, 'Engmd':core_manual_mode})  
    
    return JsonResponse({'st':0, 'message':'Something went wrong'})


#competitor keyword page refresh status
@api_view(['POST','GET'])
def competitor_keyword_status(request):
    if request.method == 'POST':
        userid = request.data['userid'] 
        grpid = request.data['grpid']
        cgrpid = request.data['cgrpid']

        if userid and cgrpid:
            runkwCns = 0
            SettingsData = Settings.objects.filter(id=1).first()
            core_manual_mode = 1 if SettingsData and SettingsData.core_manual_mode else 0

            if core_manual_mode:
                # kwrfCnt = CompKeyword.objects.filter(fk_cp_project_id__in=cgrpids,fk_group=grpid,fk_user=userid,comp_call_status__in=[True]).count()
                # if kwrfCnt > 0:
                #     for cgrpid in cgrpids:
                #         keyIns = CompKeyword.objects.filter(fk_cp_project_id=cgrpid,fk_group=grpid,fk_user=userid,comp_call_status__in=[True]).count()
                #         if keyIns > 0:
                #             rungrpids.append(cgrpid)

                runkwCns = CompKeyword.objects.exclude(comp_call_mode__in=["done","fail"]).filter(fk_cp_project_id=cgrpid,fk_group_id=grpid,fk_user_id=userid).count()

            return JsonResponse({'st':1, 'rkw': runkwCns, 'Engmd':core_manual_mode})  
    
    return JsonResponse({'st':0, 'message':'Something went wrong'})

# Update competitors
@api_view(['POST'])    
@permission_classes((IsAuthenticated,))
def competitor_group_update(request):
    userid = request.data['userid']
    grpid = request.data['grpid']
    competitor_id = request.data['cgrpid']

    if userid and grpid and authPermission.validate(request, "POST"): 

        if userid and grpid and competitor_id:
            grpname = request.data['grpname'].strip()
            compPrjtIns = CompProject.objects.filter(fk_user_id=userid,fk_group_id=grpid,id=competitor_id)
            if compPrjtIns.exists():
                compPrjtIns.update(cp_group_name = grpname)
                return JsonResponse({'st':1, 'message':'Competior updated successfully'})  
                
    return JsonResponse({'st':0, 'message':'Something went wrong'})
