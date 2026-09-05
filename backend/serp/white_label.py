from rest_framework.decorators import api_view
from django.http import HttpResponse,JsonResponse
from serp.models import *
from django.conf import settings
from datetime import date,datetime,timedelta
from account import verify as authPermission
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
def _whtLblCheck_(request):
    start=datetime.now()
    try:
        if request.method=='POST' and authPermission.validate(request, "POST"):
            userid = str(request.data['userid'])
            grpid = str(request.data['grpid'])
            if userid.isdigit() and grpid.isdigit():
                groupsetting = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('wl_report_image', 'wl_rprt_sttngs').first()
                if groupsetting:
                    gsc_site_status=bool()
                    wl_rprt_data={'subject':'', 'mail':'', 'src':'', 'dm':'', 'wl_status':bool(), 'wl_rprt_sttngs':None}
                    if groupsetting['wl_report_image']==None or len(groupsetting['wl_report_image']) == 0: 
                        wl_rprt_data['wl_status'] = False
                    else:
                        wl_rprt_data['subject']=groupsetting['wl_report_image']['subject']
                        wl_rprt_data['mail'] = groupsetting['wl_report_image']['mail'] 
                        wl_rprt_data['src'] = groupsetting['wl_report_image']['url']
                        wl_rprt_data['height'] = groupsetting['wl_report_image']['dm'][0]
                        wl_rprt_data['dm'] = 64 if wl_rprt_data['height']>=64 else wl_rprt_data['height']
                        wl_rprt_data['wl_status'] = True
                    
                    if groupsetting['wl_rprt_sttngs']:  
                        wl_rprt_data['wl_rprt_sttngs']=groupsetting['wl_rprt_sttngs']
                    group = Groups.objects.filter(fk_user_id=userid, id=grpid).values('gsc_site_status').first() 
                    if group:
                        if group['gsc_site_status']!=False:
                            gsc_site_status=group['gsc_site_status']           
                    return JsonResponse({'st':1, 'wl_rprt_data':wl_rprt_data, 'gsc_status':gsc_site_status, 'time':str(datetime.now()-start)})    
        return JsonResponse({'st':0, 'dt':'Error'})            
    except Exception as e:
        return JsonResponse({'st':0, 'dt':str(e)}) 

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def _whtLblSttgs_(request):
    try:
        if request.method == 'POST' and authPermission.validate(request, "POST"):
            start = datetime.now()
            userid = str(request.data['userid'])
            grpid = str(request.data['groupid'])
            fields = request.data['fields']
            if userid.isdigit() and grpid.isdigit():
                if fields:
                    groupSetting = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("wl_rprt_sttngs").first()
                    if groupSetting:
                        try:
                            if "wl_rprt_sttngs" in groupSetting: 
                                grpupdt = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).update(wl_rprt_sttngs=fields) 
                                if grpupdt == 1: 
                                    end = datetime.now() 
                                    return JsonResponse({'st':1, 'dt':fields, 'msg':'White label report settings updated successfully', 'grpupdt':grpupdt, 'time':str(end-start)})
                        except Exception as e:
                            return JsonResponse({'st':0, 'dt':str(e)}) 
        return JsonResponse({'st':0}) 
    except Exception as e:
        return JsonResponse({'st':0, 'dt':str(e)})                    