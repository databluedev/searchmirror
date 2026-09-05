from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.common import *
from account.models import Account  
from mailend.models import KeywordHistory 
from serp.serializers import *
from serp.custom_serializer.report_serializers import *     # V3.3.1.0
import string,random 
from django.conf import settings
from serp import calculation, views as serp_views
from django.core.mail import EmailMultiAlternatives
from account import verify as authPermission
from io import StringIO 

from datetime import date,datetime,timedelta
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from weasyprint import HTML
import csv, os
from rest_framework.permissions import IsAuthenticated
from account.cron_auth import cron_only


#log file
def coreGetDateTime():
    return " "+str(datetime.strftime(datetime.now(), 'GMT %b|%d|%Y-%H:%M:%S'))+" => "

def coreLog(line, record):
    record = str(record)
    line = coreGetDateTime() + str(line) 

    searchFile = str(settings.BASE_DIR)+"/logs/reports.log"
    if record.isdigit() and record != "0":
        searchFile = str(settings.BASE_DIR)+"/logs/reports/reports__"+record+".log" 

    if not os.path.exists(searchFile):
        with open(searchFile, 'w'): pass 
    with open(searchFile, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content) 
    return True

def report_mode_update(record, mode, status): 
    if str(record).isdigit() and status:
        if mode == "INSTANT":
            Report.objects.filter(id=record).update(instant_mode=status)
        elif mode == "SCHEDULE":
            Report.objects.filter(id=record).update(schedule_mode=status)

    return True

#Schedule Email Reports data
@api_view(['POST','GET'])
def smrdata(request):
    userid = request.data['userid']
    grpid = request.data['grpid']

    if userid and grpid and authPermission.validate(request, "POST"):   

        if userid.isdigit() and grpid.isdigit():
            # reportdata = Report.objects.filter(fb_user_id = userid)
            reportdata = Report.objects.filter(fb_user_id = userid, fk_group_id=grpid)
            reportdataCount = Report.objects.filter(fb_user_id = userid, fk_group_id=grpid,instant_mode__in=["INIT","SCHD","BUSY"] ).count()
            reportdatas = []
            groupsetting = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).exists()
            wl_status = bool()

            if groupsetting:
                # subject = ""
                # mail = ""
                # src = ""
                # dm = ""
                groupsetting = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=grpid).values('wl_report_image').first()
                if groupsetting['wl_report_image']==None or len(groupsetting['wl_report_image']) == 0: 
                    wl_status = False 
                else:
                    wl_status = True    

            for ex in reportdata :
                if(ex.last_delivery == None):
                    last_delivery = ex.last_delivery
                else:
                    last_delivery = ex.last_delivery.strftime("%b %d, %Y-%I:%M %p GMT +00:00")
                if(ex.next_delivery == None):
                    next_delivery = ex.next_delivery
                else:
                    next_delivery = ex.next_delivery.strftime("%b %d, %Y-%I:%M %p GMT +00:00")
                reportdatas.append({  
                    'id': ex.id,
                    'userid': ex.fb_user_id,
                    'groupid': ex.fk_group_id,
                    'groupname': ex.group_name,
                    'recipient': ex.recipient,
                    'frequency': ex.frequency,
                    'lastdelivery': last_delivery,
                    'nextdelivery': next_delivery,
                    # 'lastdelivery': last_delivery.split('-')[0],
                    # 'ldt': last_delivery.split('-')[1],
                    # 'nextdelivery': next_delivery.split('-')[0],
                    # 'ndt': next_delivery.split('-')[1],
                    'reportformat': ex.report_format,
                    'instantmode': ex.instant_mode,
                    'WLExists':ex.white_label 

                })
            return Response({'status':'true','message':"Showing reports", 'data': reportdatas, 'progCount':reportdataCount, 'wl_status':wl_status }) 
    
    return Response({'status':'false', 'message':'Something went wrong'})  

#Report add  
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def report_schedule_add(request): 
    data = {} 
    if request.method == 'POST':
        if authPermission.validate(request, "POST"):
            # group_name = request.data['group_name']
            recipient = request.data['recipient']
            frequency = request.data['frequency']
            report_format = request.data['report_format']
            fb_user = request.data['fb_user']
            fk_group = request.data['fk_group']
            white_label = request.data['white_label']
            groupIns = Groups.objects.filter(fk_user_id=fb_user,id=fk_group).first()
            reportsCount = Report.objects.filter(fb_user=fb_user,fk_group=fk_group).count()
            #check for paymode
            accUseIns = Accountusage.objects.filter(fb_user=fb_user).first()
            paystatus, payOverRule = userPaymode(fb_user, accUseIns)
            if paystatus in ["dead","cancelled","expire"]:
                return JsonResponse({'status':'fail', 'message':"Oops! Sorry You've no active subscription."})   
            else:
                if reportsCount >= settings.MAX_REPORTS_PER_PROJECT:
                    return Response({'status':'fail','key':'exists','message':"You have reached your maximum reports limit for this project."})
                else:
                    repdata = Report.objects.filter(fb_user=fb_user,fk_group=fk_group,recipient=recipient,frequency=frequency,report_format=report_format).count()
                    if repdata == 0 and groupIns:
                        request.data['group_name'] = groupIns.group_name
                        serializer = ReportSerializer(data=request.data)
                        if serializer.is_valid():
                            now = datetime.now()
                            frequency = int(serializer.validated_data['frequency'])
                            add_for_createddate = now + timedelta(days=frequency)        
                            # serializer.validated_data['last_delivery'] = now
                            serializer.validated_data['next_delivery'] = add_for_createddate
                            serializer.validated_data['instant_mode'] = "DONE" 
                            fbcreate =  serializer.save()
                            data['status'] =  "true" 
                            data['message'] =  "Scheduled email report is added successfully"
                            mail_record_update(fb_user, recipient, "report")
                        else:
                            data = serializer.errors
                        return Response(data)
                    else:
                        return Response({'status':'fail','key':'exists','message':"Already exists with the past reports"})

#report schedule email sent now
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def report_email_sent_now(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = request.data['userid']
        reportid = request.data['scheduleid']

        if userid.isdigit() and reportid:
            now = datetime.now()
            if "rpttype" not in request.data:
                reportIns_ex = Report.objects.filter(fb_user_id=userid,id=reportid)
                reportIns = reportIns_ex.first()
                reportInsUpdate = reportIns_ex.update(instant_mode = "INIT")
            else:
                reportRcd = Report.objects.filter(fb_user_id=userid,id=reportid,last_delivery=None)
                reportIns = reportRcd.first()
                # reportRcdupdate = reportRcd.update(last_delivery=now)
            accUseIns = Accountusage.objects.filter(fb_user=userid).first()
            if reportIns:
                paystatus, payOverRule = userPaymode(userid, accUseIns)
                if paystatus in ["dead","cancelled","expire"]:
                    return JsonResponse({'status':'false', 'message':"Oops! Sorry You've no active subscription."})   
                else:
                    return JsonResponse({'status':'true', 'message':"Mail sending in progress.Please check your mailbox shortly."})   
                    # nowformat = now.strftime('%d-%m-%Y %I:%M %p')
                    # emgroupid = reportIns.fk_group_id
                    # emailid = reportIns.recipient
                    # emformat = reportIns.report_format
                    # group = Groups.objects.get(fk_user_id=userid,id=reportIns.fk_group_id) 
                    # if group:
                    #     projectname = group.group_name
                    #     domainname = group.domain_name
                    #     keydat = Keyword.objects.filter(fk_user_id=reportIns.fb_user_id,fk_group_id=reportIns.fk_group_id).order_by('ranknow')
                    #     keydata = sorted(keydat, key = lambda x: x.ranknow if x.ranknow > 0 else float('inf')) 
                    #     if("CSV" in emformat):
                    #         #CSV Data
                    #         serializer = ExportCSVKeywordSerializer(keydata, many=True)
                    #         exportcsvdata = serializer.data
                    #         rows = exportcsvdata
                    #         csvfile = StringIO()
                    #         fieldnames = ['sno','keyword','Rank','Best rank','Day','Week','Month','Volume','Comp','URL','region','Created on']
                    #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    #         writer.writeheader()
                    #         writer.writerows(rows)
                    #     if("PDF" in emformat):
                    #         #PDF Data
                    #         serializer = ExportPDFKeywordSerializer(keydata, many=True)
                    #         post_pdf = render_to_string(
                    #             'email/report-pdf-template.html',
                    #             {
                    #                 'paragraphs': serializer.data,
                    #                 'projectname': projectname,
                    #                 'domainname': domainname,
                    #                 'siteurl': settings.SITE_URL,
                    #                 'serivceurl': settings.SERVICE_URL,
                    #             },
                    #         )
                    #         post_pdfs = HTML(string=post_pdf).write_pdf()       

                    #     #Mail
                    #     accountIns = Account.objects.filter(id=userid).first()
                    #     currentDate = date.today().strftime("%d %b %Y")
                    #     context = {
                    #         'userid': userid,
                    #         'username': accountIns.username,
                    #         'groupname': projectname,
                    #         'reportdate': nowformat,
                    #         'date': str(currentDate).lower(),
                    #         'siteurl': settings.SITE_URL,
                    #         'serivceurl': settings.SERVICE_URL,
                    #     }
                                        
                    #     email_html_message = render_to_string('email/report.html', context)
                    #     msg = EmailMultiAlternatives(
                    #         # title:
                    #         "Tracker schedule report for "+projectname,
                    #         # message:
                    #         "report Content",
                    #         # from:
                    #         settings.HOST_MAIL,
                    #         # to:
                    #         [emailid]
                    #     )
                    #     msg.attach_alternative(email_html_message, "text/html")
                    #     if("CSV" in emformat):
                    #         filename = projectname+'-report(Tracker).csv'
                    #         msg.attach(filename, csvfile.getvalue(), 'text/csv')
                    #     if("PDF" in emformat):
                    #         filename = projectname+'-report(Tracker).pdf'
                    #         msg.attach(filename, post_pdfs, 'application/pdf')
                        
                    #     if msg.send():
                    #         return JsonResponse({'status':'true', 'message':"Mail sent successfully"})   
            
    return JsonResponse({'status':'false', 'message': "Check your details"})

# REPORT SCHEDULE EMAIL V3.3.1.0 (BOTH CSV AND PDF)
@cron_only
def report_schedule_emails(request):
    errorMsg = "UNKNOWN OR DATA ERROR"
    mode = "INSTANT"
    userid = 0 
    recordid = 0

    try: 
        keydata = Report.objects.filter(instant_mode="INIT")[0:1]
        
        if keydata == None or len(keydata) == 0:
            keydata = Report.objects.filter(next_delivery__lte=datetime.now(), schedule_mode__in=["DONE", "SENT"])[0:1]
            mode = "SCHEDULE"
        
        if keydata:
            # FOR LOOP STARTS
            for ex in keydata :
                recordid = ex.id
                createddate = ex.created_date
                lastdelivery = ex.last_delivery
                nextdelivery = ex.next_delivery
                userid = ex.fb_user_id
                groupid = ex.fk_group_id
                reportformat = ex.report_format
                receiver = ex.recipient 

                clienturl = None
                subject = None
                mail = None
                height = None

                fieldSort = ["KW", "RK", "15D", "BR", "1D", "7D", "VL", "CP", "URL", "RN", "UO", "CLS", "IMP"] 
                data = Report.objects.filter(fb_user_id=userid, fk_group_id=groupid, recipient=receiver).values('white_label').first()
                groupExists = GroupSetting.objects.filter(fk_user_id=userid, fk_group_id=groupid).values('wl_report_image', 'wl_rprt_sttngs').first()

                if "white_label" in data:
                    if data['white_label']=='Enabled':                        
                        if "wl_report_image" in groupExists:
                            if groupExists['wl_report_image']: 
                                subject = groupExists['wl_report_image']['subject'] 
                                clienturl = groupExists['wl_report_image']['url'] 
                                mail = groupExists['wl_report_image']['mail']
                                height = groupExists['wl_report_image']['dm'][0]

                if "wl_rprt_sttngs" in groupExists:
                    if groupExists['wl_rprt_sttngs']: 
                        if len(groupExists['wl_rprt_sttngs']):  
                            fieldSort = groupExists['wl_rprt_sttngs']

                report_mode_update(ex.id, mode, "SCHD") 
                
                if nextdelivery and userid and groupid and reportformat:
                    if mode == "INSTANT" or lastdelivery == None or nextdelivery >= lastdelivery: 
                        stime = datetime.now()
                        diffday = (stime.date() - ex.created_date.date()).days
                        paystatus, payOverRule = userPaymode(ex.fb_user_id, None)

                        if paystatus in ["dead", "cancelled", "expire"]:
                            keydatas = Report.objects.get(id = ex.id)
                            if mode == "INSTANT":
                                keydatas.instant_mode = "DROP"
                            elif mode == "SCHEDULE":
                                keydatas.schedule_mode = "DROP"
                                                    
                            keydatas.next_delivery = ex.created_date + timedelta(days=(int(diffday) + ex.frequency))
                            keydatas.save()
                            return JsonResponse({'status':'false', 'message':'User not subscribed'})
                        else:                          
                            report_mode_update(ex.id, mode, "BUSY")
                            kw_data = Keyword.objects.filter(fk_user_id=userid, fk_group_id=groupid).values("id", "keyword", "region", "dayval", "daymark", "weekval", "weekmark", "halfmonthval", "halfmonthmark", "ranknow", "top_rank", "search_volume", "site_url", "lastranked_date", "gsc_clicks", "gsc_impressions").order_by('ranknow') 
                            kw_volume = keywordVolume.objects.filter(fk_user_id=userid, fk_group_id=groupid).values("fk_keyword_id", "comp_level", "month_wise_volume")
                            group_data = Groups.objects.filter(fk_user_id=userid, id=groupid).values('group_name', 'domain_name', 'total_Keyword', 'created_date', 'gsc_site_status').first()  
                            account_data = Account.objects.filter(id=userid).values('username').first()

                            if kw_data and group_data and account_data:
                                gsc_status = group_data['gsc_site_status'] 
                                total_keyword_count = len(group_data['total_Keyword']) 

                                if total_keyword_count > 0:
                                    projectname = group_data['group_name'] 
                                    domainname = group_data['domain_name']
                                    username = account_data['username']

                                    reportformatinstring = str(reportformat).lower()
                                                               
                                    currentDate = date.today().strftime("%d %^b %Y")
                                    nowformat = group_data['created_date'] + timedelta(days=(int(total_keyword_count)) - 1)
                                    nowformat = nowformat.strftime('%d, %^b %Y')
                                    
                                    context = {
                                        'userid': userid,
                                        'username': username,
                                        'groupname': projectname,
                                        'reportdate': nowformat,
                                        'date': str(currentDate).lower(),
                                        'siteurl': settings.SITE_URL,
                                        'serivceurl': settings.SERVICE_URL, 
                                        'clientUrl' : clienturl,
                                        'mailContent':mail
                                    }
                                    

                                    email_html_message = render_to_string('email/report.html', context)
                                    msg = EmailMultiAlternatives(
                                        # title:
                                        "Tracker schedule report for "+projectname if subject==None else subject,
                                        # message:
                                        "report Content",
                                        # from:
                                        settings.HOST_MAIL,
                                        # to:
                                        [receiver]
                                    )
                                    # *****
                                    msg.attach_alternative(email_html_message, "text/html")
                                    
                                    if("pdf" in reportformatinstring or "csv" in reportformatinstring):
                                        keydata = sorted(kw_data, key = lambda x: x['ranknow'] if x['ranknow'] > 0 else float('inf'))
                                        serializer_data = ReportExportSerializer(keydata, many=True, context={'voldata': kw_volume, "format": reportformatinstring}).data 
                                        exportdata = list(filter(None, serializer_data))

                                        if("csv" in reportformatinstring):
                                            csvfile = StringIO()
                                            fieldnames = ['#',]
                                            fieldname = {'KW':'Keyword','RK':'Rank','BR':'Best Rank','1D':'1D','7D':'7D','15D':'15D','VL':'Volume','CP':'Comp','URL':'URL','RN':'Region','UO':'Updated On'}
                                            if gsc_status:
                                                fieldname['IMP'] = 'IMPS'
                                                fieldname['CLS'] = 'CLKS' 
                                            
                                            for i in fieldSort:
                                                value=fieldname.get(i)
                                                if value!=None:
                                                    fieldnames.append(value) 

                                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                                            writer.writeheader()
                                            writer.writerows(exportdata)
                                            
                                            filename = projectname+'-report(Tracker).csv'
                                            msg.attach(filename, csvfile.getvalue().encode('utf-16'), 'text/csv') 
                                    
                                        if("pdf" in reportformatinstring):
                                            
                                            post_pdf = render_to_string(
                                                'email/schedule-pdf-report-template.html',
                                                {
                                                    'paragraphs': exportdata,
                                                    'projectname': projectname,
                                                    'domainname': domainname,
                                                    'reportdate': nowformat, 
                                                    'siteurl': settings.SITE_URL,
                                                    'serivceurl': settings.SERVICE_URL,
                                                    'clientUrl':clienturl,
                                                    'height': height,
                                                    'fieldSort':fieldSort,
                                                    'gsc_status':gsc_status,
                                                }, 
                                            )
                                            # *****
                                            post_pdfs = HTML(string=post_pdf).write_pdf()
                                            filename = projectname+'-report(Tracker).pdf' 
                                            msg.attach(filename, post_pdfs, 'application/pdf')
                                                                                
                                        if msg.send():
                                            keydatas = Report.objects.get(id = ex.id) 
                                            eTime = datetime.now()

                                            if mode == "INSTANT":
                                                keydatas.instant_mode = "DONE"
                                            elif mode == "SCHEDULE":
                                                keydatas.schedule_mode = "SENT" 
                                            
                                            keydatas.last_delivery = eTime
                                            keydatas.next_delivery = ex.created_date + timedelta(days=(int(diffday) + ex.frequency))
                                            keydatas.save() 

                                            tTime = eTime - stime
                                            logLine = "Report - "+ str(ex.id) +' Mail Sent - '+receiver+" - User id = "+str(userid)+" Time - "+str(tTime)
                                            coreLog(logLine, userid) 
                                            
                                            return JsonResponse({'status':'true', 'message':'Mail sent', 'image':clienturl})
                                        else:
                                            report_mode_update(ex.id, mode, "FAIL")
                                            logLine = "Report - "+ str(ex.id) +' Mail Fail - '+ receiver+" - User id = "+str(userid)
                                            coreLog(logLine, 0)  

                                            return JsonResponse({'status':'false', 'message':'Mail not sent'})
                                    else:
                                        errorMsg = " Report - "+str(ex.id) + " Wrong format "
                                else:
                                    errorMsg = " Report - "+str(ex.id) + " Total keyword count is insufficient or zero "
                            else:
                                errorMsg = " Report - "+str(ex.id) + " Conditional error data not found in the table " 
            # FOR LOOP ENDS
        else:
            return JsonResponse({'status':'false', 'message':'No reports are in queue'}) 
        
    except Exception as e:
        errorMsg = "ERROR: "+str(e)
    
        logLine = "Report - "+ str(recordid) + errorMsg +" - User id = "+str(userid) 
        coreLog(logLine, 0)

        return JsonResponse({'status':'false', 'message':'Something went wrong', 'e':str(e)})

#Report  Delete
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def report_schedule_delete(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):  
        userid = str(request.data['userid'])
        if userid.isdigit():
            scheduleid = request.data['scheduleid']
            if userid and scheduleid:
                repdata = Report.objects.filter(fb_user_id=userid,id=scheduleid).first()
                if repdata is None:
                    return Response({'status':'false', 'message':'Report not found'})
                repdata.delete()
                return Response({ "status":"true", "message": "Report deleted successfully" })
    
    return Response({'status':'false', 'message':'Something went wrong'})
