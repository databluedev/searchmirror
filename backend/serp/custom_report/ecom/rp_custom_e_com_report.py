from rest_framework.decorators import api_view
from django.http import HttpResponse,JsonResponse
from account import verify as authPermission
from django.conf import settings
from serp.models import *

def reorder_sheet_metrics(original_list):
    desired_list = ['clicks', 'impressions', 'position', 'ctr']
    reordered_list = [item for item in desired_list if item in original_list]
    return reordered_list

def rank_manager_create(uid=0, gid=0, status="scheduled", update=False):
    print('test')
    platform = GroupSetting.objects.filter(fk_user_id=uid, fk_group_id=gid).values('site_platform').first()
    report_manager_count = 0
    if uid and gid:
        report_manager_count = ReportManager.objects.filter(fk_user_id=uid, fk_group_id=gid).exists() 

        if not report_manager_count:
            rmCreate = ReportManager()
            rmCreate.fk_user_id = uid
            rmCreate.fk_group_id = gid
            rmCreate.track_status = status 
            rmCreate.download_link = "NA"
            rmCreate.delivery_status = False
            rmCreate.site_platform = platform['site_platform']
            rmCreate.save() 

        if update:
            ReportManager.objects.filter(fk_user_id=uid, fk_group_id=gid).update(track_status=status)

    return True

@api_view(['POST','GET'])
def e_add_report_ga_metrics(request): 
    try:
        userid = request.data['userid']
        grpid = request.data['grpid']
        print('CHECK')

        if userid and grpid and authPermission.validate(request, "POST"):   

            if userid.isdigit() and grpid.isdigit():
                if {'userid', 'grpid', 'sheet', 'type', 'schedule', 'duration', 'change', 'orderby'}.issubset(request.data.keys()):
                    print('CHECK')
                    if Groups.objects.filter(fk_user_id=userid, id=grpid).exists():
                        print('CHECK')
                        # CONDITIONAL FACTOR - STARTS
                        sheet_name = str(request.data['sheet']).strip()      # FORMAT: STRING
                        if not len(sheet_name):
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_type = str(request.data['type']).strip()      # FORMAT: STRING
                        if sheet_type not in ['ga_other_sources', 'ga_landing_pages']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_schedule = str(request.data['schedule']).strip()  # FORMAT: STRING
                        if sheet_schedule not in ['weekly', 'monthly']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_interval = str(request.data['duration']).strip()  # FORMAT: INTEGER
                        if sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        
                        # order_by = (request.data['orderby']).strip()
                        if (request.data['orderby']).strip():
                            order_by = 'asc' if request.data['orderby'] == 'Ascending' else 'desc'

                        controlFlag = 0
                        print('CHECK')
                        sheet_unit = [] 
                        if sheet_type == "ga_landing_pages" and (sheet_schedule == "weekly" or sheet_schedule=='monthly') and sheet_interval in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                            sheet_unit = request.data['change']                 # FORMAT: ARRAY
                            print('CHECK')
                            if set(sheet_unit).issubset(['number', 'percentage']): 
                                controlFlag = 1
                                print('CHECK')
                        elif sheet_type == "ga_other_sources" and sheet_schedule == "weekly" and sheet_interval in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                                controlFlag = 1
                                print('CHECK')
                        elif sheet_type == "ga_other_sources" and sheet_schedule == "monthly" and sheet_interval in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                                controlFlag = 1
                                print('CHECK')
                        else:
                            pass
                        # CONDITIONAL FACTOR - ENDS

                        if controlFlag == 1:
                            print('CHECK')
                            if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name).count():
                                
                                print("\n\nuserid: ", userid, "  grpid: ", grpid)
                                print("sheet_type: ", sheet_type)
                                print("sheet_name: ", sheet_name)
                                print("sheet_unit: ", sheet_unit)
                                print("sheet_schedule: ", sheet_schedule, "  sheet_interval: ", sheet_interval, "\n\n")  
                                
                                # SHEET UPDATE
                                # rsCreate = ReportSheets()
                                # rsCreate.fk_user_id = userid
                                # rsCreate.fk_group_id = grpid
                                # rsCreate.sheet_name = sheet_name
                                # rsCreate.type = sheet_type
                                # rsCreate.metrics = [] 
                                # rsCreate.change_units = sheet_unit
                                # rsCreate.duration = sheet_schedule
                                # rsCreate.duration_limit = int(sheet_interval) 
                                # rsCreate.order_by = order_by
                                rsCreate = ReportSheets.objects.create(
                                        fk_user_id=userid,fk_group_id=grpid, sheet_name=sheet_name, 
                                        type=sheet_type, metrics=[],
                                        change_units=sheet_unit, duration=sheet_schedule, duration_limit=int(sheet_interval),
                                        order_by=order_by
                                    )
                                print('CHECK')
                                
                                if rsCreate:
                                    # MANAGER UPDATE 
                                    rank_manager_create(userid, grpid, "scheduled", False)
                                
                                return JsonResponse({'st':1, 'message':"Report sheet has been successfully added"}) 
                            else:
                                return JsonResponse({'st':0, 'message':'Sheet name already exists'}) 
                        else:
                            return JsonResponse({'st':0, 'message':'Restricted Data'}) 
                    
                    return JsonResponse({'st':0, 'message':'No Data Found'})  
    except Exception as e:
        print(str(e))
        return JsonResponse({'st':0, 'message':str(e)})  
        
    return JsonResponse({'st':0, 'message':'Something went wrong'}) 


@api_view(['POST','GET'])
def e_add_report_domain_metrics(request): 
    try:
        userid = request.data['userid'] 
        grpid = request.data['grpid']

        if userid and grpid and authPermission.validate(request, "POST"):   

            if userid.isdigit() and grpid.isdigit():
                if {'userid', 'grpid', 'sheet', 'type', 'schedule', 'duration', 'change', 'orderby'}.issubset(request.data.keys()):
                    if Groups.objects.filter(fk_user_id=userid, id=grpid).exists():

                        # CONDITIONAL FACTOR - STARTS
                        sheet_name = str(request.data['sheet']).strip()      # FORMAT: STRING
                        if not len(sheet_name):
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_type = str(request.data['type']).strip()      # FORMAT: STRING
                        if sheet_type not in ['domain_metrics']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_schedule = str(request.data['schedule']).strip()  # FORMAT: STRING
                        if sheet_schedule not in ['monthly']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_interval = str(request.data['duration']).strip()  # FORMAT: STRING
                        if sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        
                        # order_by = (request.data['orderby']).strip()
                        if (request.data['orderby']).strip():
                            order_by = 'asc' if request.data['orderby'] == 'Ascending' else 'desc'

                        controlFlag = 0
                        sheet_unit = request.data['change']                 # FORMAT: ARRAY
                        if set(sheet_unit).issubset(['number', 'percentage']): 
                            controlFlag = 1

                        if controlFlag == 1:
                            if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name).count():
                                
                                print("\n\nuserid: ", userid, "  grpid: ", grpid)
                                print("sheet_type: ", sheet_type)
                                print("sheet_name: ", sheet_name)
                                print("sheet_unit: ", sheet_unit)
                                print("sheet_schedule: ", sheet_schedule, "  sheet_interval: ", sheet_interval, "\n\n")

                                # SHEET UPDATE
                                # rsCreate = ReportSheets()
                                # rsCreate.fk_user_id = userid
                                # rsCreate.fk_group_id = grpid
                                # rsCreate.sheet_name = sheet_name
                                # rsCreate.type = sheet_type
                                # rsCreate.metrics = [] 
                                # rsCreate.change_units = sheet_unit
                                # rsCreate.duration = sheet_schedule
                                # rsCreate.duration_limit = int(sheet_interval) 
                                # rsCreate.order_by = order_by
                                rsCreate = ReportSheets.objects.create(
                                        fk_user_id=userid,fk_group_id=grpid, sheet_name=sheet_name, 
                                        type=sheet_type, metrics=[],
                                        change_units=sheet_unit, duration=sheet_schedule, duration_limit=int(sheet_interval),
                                        order_by=order_by
                                    )
                                
                                if rsCreate:
                                    # MANAGER UPDATE 
                                    rank_manager_create(userid, grpid, "scheduled", False)
                                
                                return JsonResponse({'st':1, 'message':"Report sheet has been successfully added"})
                            else:
                                return JsonResponse({'st':0, 'message':'Sheet name already exists'}) 
                        else:
                            return JsonResponse({'st':0, 'message':'Restricted Data'}) 
                    
                    return JsonResponse({'st':0, 'message':'No Data Found'})
    except Exception as e:
        return JsonResponse({'st':0, 'message':str(e)})

    return JsonResponse({'st':0, 'message':'Something went wrong'}) 

@api_view(['POST','GET'])
def e_add_report_keyword_metrics(request): 
    try:
        userid = request.data['userid'] 
        grpid = request.data['grpid']

        if userid and grpid and authPermission.validate(request, "POST"):   

            if userid.isdigit() and grpid.isdigit():
                if {'userid', 'grpid', 'sheet', 'type', 'metrics', 'schedule', 'duration', 'change', 'orderby'}.issubset(request.data.keys()):
                    if Groups.objects.filter(fk_user_id=userid, id=grpid).exists():

                        # CONDITIONAL FACTOR - STARTS
                        sheet_name = str(request.data['sheet']).strip()      # FORMAT: STRING
                        if not len(sheet_name):
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_type = str(request.data['type']).strip()      # FORMAT: STRING
                        if sheet_type not in ['keyword_ranking']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_metrics = request.data['metrics']             # FORMAT: ARRAY
                        if not set(sheet_metrics).issubset(["target_url", "base_ranking", "landing_pages", "average_volume"]): 
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_schedule = str(request.data['schedule']).strip()  # FORMAT: STRING
                        if sheet_schedule not in ['weekly', 'monthly']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_interval = str(request.data['duration']).strip()  # FORMAT: STRING
                        if sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        
                        if (request.data['orderby']).strip():
                            order_by = 'asc' if request.data['orderby'] == 'Ascending' else 'desc'

                        controlFlag = 0
                        sheet_unit = request.data['change']                     # FORMAT: ARRAY
                        if set(sheet_unit).issubset(['number']):
                            controlFlag = 1

                        if controlFlag == 1:
                            if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name).count():
                                
                                print("\n\nuserid: ", userid, "  grpid: ", grpid)
                                print("sheet_type: ", sheet_type)
                                print("sheet_name: ", sheet_name)
                                print("sheet_metrics: ", sheet_metrics) 
                                print("sheet_unit: ", sheet_unit)
                                print("sheet_schedule: ", sheet_schedule, "  sheet_interval: ", sheet_interval, "\n\n")

                                # SHEET UPDATE
                                # rsCreate = ReportSheets()
                                # rsCreate.fk_user_id = userid
                                # rsCreate.fk_group_id = grpid
                                # rsCreate.sheet_name = sheet_name
                                # rsCreate.type = sheet_type
                                # rsCreate.metrics = sheet_metrics 
                                # rsCreate.change_units = sheet_unit 
                                # rsCreate.duration = sheet_schedule
                                # rsCreate.duration_limit = int(sheet_interval)
                                # rsCreate.order_by = order_by
                                rsCreate = ReportSheets.objects.create(
                                        fk_user_id=userid,fk_group_id=grpid, sheet_name=sheet_name, 
                                        type=sheet_type, metrics=sheet_metrics,
                                        change_units=sheet_unit, duration=sheet_schedule, duration_limit=int(sheet_interval),
                                        order_by=order_by
                                    )
                                
                                if rsCreate:
                                    # MANAGER UPDATE 
                                    rank_manager_create(userid, grpid, "scheduled", False)
                                
                                return JsonResponse({'st':1, 'message':"Report sheet has been successfully added"}) 
                            else:
                                return JsonResponse({'st':0, 'message':'Sheet name already exists'}) 
                        else:
                            return JsonResponse({'st':0, 'message':'Restricted Data'}) 
                    
                    return JsonResponse({'st':0, 'message':'No Data Found'})  
    except Exception as e:
        return JsonResponse({'st':0, 'message':str(e)})

    return JsonResponse({'st':0, 'message':'Something went wrong'})

@api_view(['POST','GET']) 
def e_add_report_gsc_metrics(request): 
    try:
        userid = request.data['userid'] 
        grpid = request.data['grpid']

        if userid and grpid and authPermission.validate(request, "POST"):   

            if userid.isdigit() and grpid.isdigit():
                if {'userid', 'grpid', 'sheet', 'type', 'metrics', 'schedule', 'duration', 'change', 'orderby'}.issubset(request.data.keys()):
                    if Groups.objects.filter(fk_user_id=userid, id=grpid).exists():

                        # CONDITIONAL FACTOR - STARTS
                        sheet_name = str(request.data['sheet']).strip()      # FORMAT: STRING
                        if not len(sheet_name):
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_type = request.data['type']                    # FORMAT: ARRAY 
                        if not set(sheet_type).issubset(['gsc_branded_queries', 'gsc_non_branded_queries', 'gsc_pages']): 
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_metrics = request.data['metrics']             # FORMAT: ARRAY
                        if not set(sheet_metrics).issubset(["clicks", "impressions", "ctr", "position"]): 
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_schedule = str(request.data['schedule']).strip()  # FORMAT: STRING
                        if sheet_schedule not in ['weekly', 'monthly']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})

                        sheet_interval = str(request.data['duration']).strip()  # FORMAT: STRING
                        if sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']: 
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        
                        # order_by = (request.data['orderby']).strip()
                        if (request.data['orderby']).strip():
                            order_by = 'asc' if request.data['orderby'] == 'Ascending' else 'desc'

                        if sheet_schedule == "weekly" and sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        elif sheet_schedule == "monthly" and sheet_interval not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']: 
                            return JsonResponse({'st':0, 'message':'Invalid Data'})
                        else:
                            pass

                        controlFlag = 0
                        sheet_unit = request.data['change']                 # FORMAT: ARRAY
                        if set(sheet_unit).issubset(['number', 'percentage']): 
                            controlFlag = 1

                        gsc_sheet_type = []
                        if 'gsc_pages' in  sheet_type:
                            gsc_sheet_type += ['gsc_pages']

                        if 'gsc_branded_queries' in sheet_type and 'gsc_non_branded_queries' in sheet_type:
                            gsc_sheet_type += ['gsc_queries']
                        elif 'gsc_branded_queries' in  sheet_type:
                            gsc_sheet_type += ['gsc_branded_queries']
                        elif 'gsc_non_branded_queries' in  sheet_type:
                            gsc_sheet_type += ['gsc_non_branded_queries']
                        else:
                            pass 

                        if controlFlag == 1:
                            if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name).count():
                                rsLoop = 0
                                for each_sheet_type in gsc_sheet_type:
                                    print("\n\nuserid: ", userid, "  grpid: ", grpid)
                                    print("sheet_type: ", each_sheet_type)
                                    print("sheet_name: ", sheet_name)
                                    print("sheet_metrics: ", reorder_sheet_metrics(sheet_metrics)) 
                                    print("sheet_unit: ", sheet_unit)
                                    print("sheet_schedule: ", sheet_schedule, "  sheet_interval: ", sheet_interval, "\n\n")  
                                    

                                for each_sheet_type in gsc_sheet_type:
                                    # SHEET UPDATE
                                    # rsCreate = ReportSheets()
                                    # rsCreate.fk_user_id = userid
                                    # rsCreate.fk_group_id = grpid
                                    # rsCreate.sheet_name = sheet_name
                                    # rsCreate.type = each_sheet_type
                                    # rsCreate.metrics = reorder_sheet_metrics(sheet_metrics) 
                                    # rsCreate.change_units = sheet_unit
                                    # rsCreate.duration = sheet_schedule
                                    # rsCreate.duration_limit = int(sheet_interval)
                                    # rsCreate.order_by = order_by
                                    rsCreate = ReportSheets.objects.create(
                                        fk_user_id=userid,fk_group_id=grpid, sheet_name=sheet_name, 
                                        type=each_sheet_type, metrics=reorder_sheet_metrics(sheet_metrics),
                                        change_units=sheet_unit, duration=sheet_schedule, duration_limit=int(sheet_interval),
                                        order_by=order_by
                                    )
                                    print(rsCreate)
                                    if rsCreate:
                                        rsLoop += 1 

                                if rsLoop:                                
                                    # MANAGER UPDATE 
                                    rank_manager_create(userid, grpid, "scheduled", False)
                                
                                return JsonResponse({'st':1, 'message':"Report sheet has been successfully added"})
                            else:
                                return JsonResponse({'st':0, 'message':'Sheet name already exists'}) 
                        else:
                            return JsonResponse({'st':0, 'message':'Restricted Data'}) 
                    
                    return JsonResponse({'st':0, 'message':'No Data Found'})  
    
    except Exception as e:
        return JsonResponse({'st':0, 'message':str(e)})

    return JsonResponse({'st':0, 'message':'Something went wrong'})

@api_view(['POST', 'GET'])
def e_add_summary(request):
    try:
        userid = request.data['userid']
        grpid = request.data['grpid']

        if userid and grpid and authPermission.validate(request, "POST"):   

            if userid.isdigit() and grpid.isdigit():
                if {'userid', 'grpid', 'sheet', 'type', 'schedule', 'duration', 'orderby'}.issubset(request.data.keys()):
                    sheet_name = request.data['sheet']
                    sheet_type = request.data['type']
                    sheet_schedule = request.data['schedule']
                    sheet_duration = request.data['duration']
                    if (request.data['orderby']).strip():
                            sheet_sort = 'asc' if request.data['orderby'] == 'Ascending' else 'desc'
                    print(userid, grpid)

                    if Groups.objects.filter(fk_user_id=userid, id=grpid).exists():
                        # rpt_sht, crted=ReportSheets.objects.get_or_create(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name, type=sheet_type, duration=sheet_schedule)
                        if not ReportSheets.objects.filter(fk_user_id=userid, fk_group_id=grpid, sheet_name=sheet_name).count():
                            # rsCreate = ReportSheets()
                            # rsCreate.fk_user_id = userid
                            # rsCreate.fk_group_id = grpid
                            # rsCreate.sheet_name = sheet_name
                            # rsCreate.type = sheet_type
                            # rsCreate.metrics = [] 
                            # rsCreate.duration = sheet_schedule
                            # rsCreate.duration_limit = sheet_duration
                            # rsCreate.order_by = sheet_sort
                            # print('CHECK')
                            rsCreate = ReportSheets.objects.create(
                                        fk_user_id=userid,fk_group_id=grpid, sheet_name=sheet_name, 
                                        type=sheet_type, metrics=[], duration=sheet_schedule, duration_limit=int(sheet_duration),
                                        order_by=sheet_sort
                                    )
                            if rsCreate.save():
                                rank_manager_create(userid, grpid, 'scheduled', False)
                            
                            return JsonResponse({'st':1, 'message':"Report sheet has been added succussfully"})
                        else:
                            return JsonResponse({'st':0, 'message': 'Sheet name already exists'})
        return JsonResponse({'st':0, 'dt':'Soemthing went wrong'})            

    except Exception as e:
        print(str(e))
        return JsonResponse({'st':0, 'dt':'Something went wrong'})