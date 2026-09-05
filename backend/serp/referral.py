from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from account.models import Account  
from mailend.models import KeywordHistory 
from serp.serializers import *
from serp.common import *
import string,random 
from django.conf import settings
from serp import calculation, views as serp_views
from account import verify as authPermission

from datetime import date,datetime,timedelta
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
import os
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
# from weasyprint import HTML
# from urllib.parse import urlparse


#Referralprogram API
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def referraldatacreate(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):
        userid = request.POST['userid']
        ref_id = request.POST['ref_id']
        if userid.isdigit() and ref_id:  
            refDataCount = Referralprogram.objects.filter(ref_id=ref_id).count()
            if refDataCount == 0: 
                data = {
                    'userid': userid,
                    'ref_id': ref_id,
                    'visitors_count': {
                        'general':0,
                        'facebook':0,
                        'twitter':0,
                        'email':0,
                        'linkedin':0,
                        'pinterest':0,
                        'whatsapp':0,
                        'telegram':0,
                        'instapaper':0,
                        'hatena':0,
                        'line':0,
                        'livejournal':0,
                        'mailru':0,
                        'ok':0,
                        'tumblr':0,
                        'viber':0,
                        'pocket':0,
                        'reddit':0,
                        'vk':0,
                        'workplace':0,
                        'weibo':0,
                        'facebookmessenger':0,
                        'emailinvite':0,
                    }
                }
                serializer = ReferralprogramSerializer(data=data)
                if serializer.is_valid():
                    refcreate =  serializer.save()

            # Referral Data Fetch
            refData = Referralprogram.objects.filter(ref_id=ref_id).first() 
            if refData: 
                visitorsCountIntegers = [x for x in refData.visitors_count.values() if not isinstance(x, str) and  x != 0]
                visitorsCount = int(sum(visitorsCountIntegers)) 

                refDataCollect = {  
                    'tlR': refData.total_registration,
                    'cmR': refData.claim_registration,
                    'ucmR': refData.unclaimed_registration,
                    'tlKc': refData.total_keywordcount,
                    'cmKc': refData.claim_keywordcount,
                    'tlRc': refData.total_refreshcount,
                    'cmRc': refData.claim_refreshcount,
                    'tlPc': refData.total_projectcount,
                    'cmPc': refData.claim_projectcount,
                    'tlVc': visitorsCount,
                }

                return Response({'status':'true', 'data': refDataCollect})
    
    return Response({'status':'false','message':"Something went wrong"})          
        
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def refvisitorscountadd(request):
    if request.method == 'POST':
        refid = request.POST['ref_id']
        medium = request.POST['medium']
        if refid:
            refdata = Referralprogram.objects.filter(ref_id=refid)
            referraldatas = []
            if refdata.exists():
                referraldatas = [{'userid_id': refdata[0].userid_id, 'ref_id': refdata[0].ref_id,'visitors_count': refdata[0].visitors_count}]

            # for ex in refdata :
            #     referraldatas.append({  
            #         'userid_id': ex.userid_id,
            #         'ref_id': ex.ref_id,
            #         'visitors_count': ex.visitors_count,
            # })
            # refdata.update(visitors_count[medium] = referraldatas[0]["visitors_count"][medium] + 1)
            refdatasave = Referralprogram.objects.filter(ref_id=refid).first()
            if refdatasave is None:
                return Response({'status':'false','message':"Something went wrong"})
            refdatasave.visitors_count[medium] = referraldatas[0]["visitors_count"][medium] + 1
            refdatasave.save()
            return Response({'status':'true','message':medium + " Visitors Count Added"})
        
    else:
        return Response({'status':'false','message':"Something went wrong"}) 
        
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def refregadd(request):
    if request.method == 'POST':
        refid = request.POST['ref_id']
        refregid = request.POST['refregid']
        if refid and refregid:
            refdata = Referralprogram.objects.filter(ref_id=refid)
            refregiddata = []
            if refdata.exists():
                refregiddata = [{'reguserid': refdata[0].reguserid, 'total_registration': refdata[0].total_registration, 'unclaimed_registration': refdata[0].unclaimed_registration}]

            # for ex in refdata :
            #     refregiddata.append({  
            #         'reguserid': ex.reguserid,
            #         'total_registration': ex.total_registration,
            #         'unclaimed_registration': ex.unclaimed_registration
            # })
            # newregid=[]
            newregid = refregiddata[0]["reguserid"]
            newregid.append(refregid)
            refdata.update(reguserid=newregid, total_registration=refregiddata[0]["total_registration"]+1, unclaimed_registration=refregiddata[0]["unclaimed_registration"]+1, modified_date=datetime.now())
            # refdatasave = Referralprogram.objects.get(ref_id=refid)
            # refdatasave.reguserid = newregid
            # refdatasave.total_registration = refregiddata[0]["total_registration"] + 1
            # refdatasave.unclaimed_registration = refregiddata[0]["unclaimed_registration"] + 1
            # refdatasave.save(update_fields=['reguserid','total_registration','unclaimed_registration','modified_date'])
            return Response({'status':'true','message':" Referral Register ID Added"})
        
    else:
        return Response({'status':'false','message':"Something went wrong"})
        
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def refreshclaim(request):
    if request.method == 'POST' and authPermission.validate(request, "POST"):
        userid = request.POST['userid']
        refid = request.POST['ref_key']
        refcall = request.POST['ref_validate'] 
        if refid and refcall and userid:
            refData = Referralprogram.objects.filter(ref_id=refid)
            accUsageData = Accountusage.objects.filter(fb_user_id=refid) 

            if refData.exists() and accUsageData.exists():
                planKeywordLimit = accUsageData[0].plan_keyword_limit
                planRefreshLimit = accUsageData[0].plan_refresh_limit
                planProjectLimit = accUsageData[0].plan_project_limit

                claimRegistration = refData[0].claim_registration
                unClaimRegistration = refData[0].unclaimed_registration
                
                claimRefreshCount = refData[0].claim_refreshcount
                totalRefreshCount = 100

                claimKeywordCount = refData[0].claim_keywordcount 
                totalKeywordCount = 100
                
                claimProjectCount = refData[0].claim_projectcount 
                totalProjectCount = 5 

                if claimRefreshCount >= 100 and refcall == "R01R": 
                    return Response({'status':'true','message':"Already reached maximum refresh limit using the referral"})
                elif claimKeywordCount >= 100 and refcall == "R02K": 
                    return Response({'status':'true','message':"Already reached maximum keyword limit using the referral"})
                elif claimProjectCount >= 5 and refcall == "R03P": 
                    return Response({'status':'true','message':"Already reached maximum project limit using the referral"})

                # intarray = list(map(int, refData[0].reguserid))
                listids = refData[0].reguserid
                regUserCount = Account.objects.filter(id__in=listids).count() 
                # regUserCount = 0
                # for singleId in refData[0].reguserid:
                #     accData = Account.objects.filter(id=int(singleId)).count() 
                #     if accData: 
                #         regUserCount += 1 


                # refdatasave = Referralprogram.objects.get(ref_id=refid)
                # AccountIns = Accountusage.objects.get(fb_user_id=refid)

                if int(unClaimRegistration) >= 5: 
                    regUserTotalCount =  int(unClaimRegistration) +  int(claimRegistration)                 
                    reAllocateUnClaim = int(unClaimRegistration) - 5
                    if claimRefreshCount == 0 and refcall == "R01R" and regUserTotalCount >= regUserCount and regUserCount >= 5:
                        refData.update(claim_refreshcount = totalRefreshCount, claim_registration = int(claimRegistration) + 5, unclaimed_registration = reAllocateUnClaim if reAllocateUnClaim > 0 else 0, modified_date=datetime.now())
                        # refdatasave.claim_refreshcount = totalRefreshCount
                        # refdatasave.claim_registration = int(claimRegistration) + 5
                        # refdatasave.unclaimed_registration = reAllocateUnClaim if reAllocateUnClaim > 0 else 0 
                        # refdatasave.save(update_fields=['claim_refreshcount','claim_registration','unclaimed_registration','modified_date'])
                        
                        accUsageData.update(plan_refresh_limit = planRefreshLimit + totalRefreshCount)
                        # AccountIns.plan_refresh_limit = planRefreshLimit + totalRefreshCount 
                        # AccountIns.save(update_fields=['plan_refresh_limit']) 
                        return Response({'status':'true','message':"Referral claimed and updated refresh count successfully"})
                    elif claimKeywordCount == 0 and refcall == "R02K" and regUserTotalCount >= regUserCount and regUserCount >= 10:
                        refData.update(claim_keywordcount=totalKeywordCount, claim_registration=int(claimRegistration)+5, unclaimed_registration=reAllocateUnClaim if reAllocateUnClaim > 0 else 0, modified_date=datetime.now())
                        # refdatasave.claim_keywordcount = totalKeywordCount
                        # refdatasave.claim_registration = int(claimRegistration) + 5
                        # refdatasave.unclaimed_registration = reAllocateUnClaim if reAllocateUnClaim > 0 else 0 
                        # refdatasave.save(update_fields=['claim_keywordcount','claim_registration','unclaimed_registration','modified_date'])

                        accUsageData.update(plan_keyword_limit = planKeywordLimit + totalKeywordCount)
                        # AccountIns.plan_keyword_limit = planKeywordLimit + totalKeywordCount
                        # AccountIns.save(update_fields=['plan_keyword_limit']) 
                        return Response({'status':'true','message':"Referral claimed and updated keyword count successfully"})
                    elif claimProjectCount == 0 and refcall == "R03P" and regUserTotalCount >= regUserCount and regUserCount >= 15:
                        refData.update(claim_projectcount=totalProjectCount, claim_registration=int(claimRegistration)+5, unclaimed_registration=reAllocateUnClaim if reAllocateUnClaim > 0 else 0, modified_date=datetime.now())
                        # refdatasave.claim_projectcount = totalProjectCount
                        # refdatasave.claim_registration = int(claimRegistration) + 5 
                        # refdatasave.unclaimed_registration = reAllocateUnClaim if reAllocateUnClaim > 0 else 0 
                        # refdatasave.save(update_fields=['claim_projectcount','claim_registration','unclaimed_registration','modified_date'])
                        
                        accUsageData.update(plan_project_limit = planProjectLimit + totalProjectCount)
                        # AccountIns.plan_project_limit = planProjectLimit + totalProjectCount 
                        # AccountIns.save(update_fields=['plan_project_limit'])
                        return Response({'status':'true','message':"Referral claimed and updated project count successfully"})
                    elif claimRefreshCount == totalRefreshCount and claimKeywordCount == totalKeywordCount and claimProjectCount == totalProjectCount:
                        return Response({'status':'true','message':"All referrals are claimed"}) 

    return Response({'status':'false','message':"Something went wrong"})      
        
@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def refwebsiteverfication(request):
	if request.method == 'POST':
		userid = request.POST['userid']
		username = request.POST['username']
		refemail = request.POST['refemail']
		refwebsite = request.POST['refwebsite']
		refphone = request.POST['refphone']
		if userid:
			#Email sent to user
			context = {
				'userid': userid,
				'username': username,
				'refemail': refemail,
				'refwebsite': refwebsite,
				'refphone': refphone,
				'siteurl': settings.SITE_URL,
				'serivceurl': settings.SERVICE_URL,
			}
			subject = "Tracker referral website verification"
			toMail = settings.ADMIN_MAIL
			# toMail = [m for m in os.environ.get("ALERT_MAIL", "").split(",") if m]
			mailDatas = sendMail('email/refwebsiteverfication.html', context, subject, toMail)
			return Response({'status':'true','message':"mailsent"})
	else:
		return Response({'status':'false','message':"Something went wrong"}) 


@api_view(['POST','GET'])
@permission_classes((IsAuthenticated,))
def emailinvite(request):
    if request.method == 'POST':
        userid = request.POST['userid']
        invitername = request.POST['name']
        email = request.POST['email']
        emails = json.loads(email)
        reflink = request.POST['reflink']
        if email:
            # mail_record_update(userid, email, "referral")             
            mailIns = Mailrecords.objects.filter(userid=userid,types="referral")
            if mailIns.exists() == False:
                maildata = Mailrecords()
                maildata.userid = userid
                maildata.types = "referral"
                maildata.mail_list = emails
                maildata.save()
            else:
                mails = set(emails + mailIns[0].mail_list)
                mailIns.update(mail_list = list(mails))
            #Email sent to user
            for emailid in emails:
                context = {
                    'reflink': reflink,
                    'invitername':invitername,
                    'siteurl': settings.SITE_URL,
                    'serivceurl': settings.SERVICE_URL,
                }
                subject = "Invitation mail to join TRACKER" 
                toMail = [emailid]
                mailDatas = sendMail('email/emailinvite.html', context, subject, toMail)
            return Response({'status':'true','message':"Invite email sent"})
    else:
        return Response({'status':'false','message':"Something went wrong"})
