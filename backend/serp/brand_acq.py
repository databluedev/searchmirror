from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests, json
from django.http import HttpResponse,JsonResponse
from serp.models import *
from serp.serializers import *
from serp.custom_serializer.widget_serializers import BrandSerializer 
from account import verify as authPermission
import os, json, time
from serp.common import totalKeywordsCount
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

# Log file
def coreGetDateTime():
   return " "+str(datetime.strftime(datetime.now(), 'GMT %b|%d|%Y-%H:%M:%S'))+" => "

def coreLog(line, uid=None,gid=None, type=None): 
   try:
      line = coreGetDateTime() + str(line) + " - userid -" + str(uid)
      searchFile = os.getcwd()+"/logs/brands/brandkwdsgroup__"+str(gid)+".log"   
      if not os.path.exists(searchFile):
         with open(searchFile, 'w'): pass 

      with open(searchFile, 'r+') as f:
         content = f.read()
         f.seek(0, 0)
         f.write(line.rstrip('\r\n') + '\n' + content) 
   except Exception as e:
      pass
   return True 
# Log File

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def add__brand__key(request):
   userId = None
   grpId = None
   try:
      if request.method == 'POST' and authPermission.validate(request, "POST"):        
         userId = str(request.data['userid']) 
         grpId = str(request.data['grpid']) 
         keyword = request.data['bkeyword'].lower().strip()
         if userId.isdigit() and grpId.isdigit():
            sts,cnt = totalKeywordsCount(userId)
            if sts == True:
               groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
               brandExists = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId,bkeyword=keyword,isocode=request.data['rc']).exists()
               if groupExists:
                  if brandExists: 
                     return JsonResponse({'st': 0,'message': "This keyword is already added for current group"}) 
                  else:
                     getLanguage = request.data['ln'].strip()

                     language = Language.objects.filter(language_name=getLanguage).first()
                     brand = brandObtain() 
                     brand.fk_user_id = userId
                     brand.fk_group_id = grpId
                     brand.bkeyword = keyword
                     brand.isocode = request.data['rc']
                     brand.language_code = language.language_code
                     brand.input_json = {
                        "region" : request.data['rg'],
                        "isocode" : request.data['rc'],
                        "country" : request.data['cnt'], 
                        "language" : request.data['ln'],
                        "language_code" : language.language_code,
                        "frequency" : 1
                     }
                     brand.report_format = [request.data['format']]
                     brand.serp_json = {
                        "srs":"",
                        "ads":{
                           "top_result" : [],
                           "bottom_result" : [],
                           "top_count" : 0,
                           "bottom_count" : 0,
                           "present" : ""
                        },
                        "urls":[]
                     }
                     brand.save()
                     dataQuery = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId).order_by('-id')
                     brands = dataQuery.values('id', 'bkeyword', 'input_json','serp_json','ads','report_format','brand_call_status','isocode').all()
                     serializerData = list()
                     if brands:
                        serializerData = BrandSerializer(brands, many=True, context={'pagetype': 'settings'}).data
                     
                     coreLog("Brand keyword created successfully", userId, grpId, "create")  
                     return JsonResponse({'st': 1,'dt':serializerData,'message': "Keyword added successfully"}) 
            return JsonResponse({'st': 0,'message': "Sorry! You have reached your keywords limit."})  
   except Exception as e:
      raise e
      uId = userId if userId else None
      gId = grpId if grpId else None
      coreLog("Brand keyword creation failed > Exception error : "+str(e), uId, grpId, "exp") 

   return JsonResponse({'st': 0,'message': "Something went wrong"}) 
     

@api_view(['POST'])
def brand__list__key(request):
   userId = None
   grpId = None
   try:
      if request.method == 'POST' and authPermission.validate(request, "POST"):       
         userId = str(request.data['userid']) 
         grpId = str(request.data['grpid']) 
         pagetype = str(request.data['pagetype']) 

         if userId.isdigit() and grpId.isdigit():
            groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
            if groupExists:
               dataQuery = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId).order_by('-id')
               brands = dataQuery.values('id', 'bkeyword', 'input_json','serp_json','ads','report_format','brand_call_status','isocode').all()
               serializerData = list()
               if brands:
                  serializerData = BrandSerializer(brands, many=True, context={'pagetype': pagetype}).data
               
               coreLog("Brand keywords listed successfully", userId, grpId, "list") 
               return JsonResponse({'st': 1, 'dt': serializerData}) 
   except Exception as e:
      raise e
      uId = userId if userId else None
      gId = grpId if grpId else None
      coreLog("Brand keywords listing failed > Exception error : "+str(e), uId, gId, "exp")  

   return JsonResponse({'st': 0,'message': "Something went wrong"}) 

@api_view(['POST'])
def rl__list__key(request):
   try:
      if request.method == 'POST' and authPermission.validate(request, "POST"):   
         userId = str(request.data['userid']) 
         grpId = str(request.data['grpid']) 

         if userId.isdigit() and grpId.isdigit():
            regions = Region.objects.all()
            regserializer = RegionFltrSerializer(regions, many=True)
            languages = Language.objects.all()
            langserializer = LanguageNameSerializer(languages, many=True)

            return JsonResponse({'st': 1, 'lng': langserializer.data,'rg':regserializer.data}) 
   except Exception as e:
      raise e

   return JsonResponse({'st': 0,'message': "Something went wrong"})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete__brand__key(request):
   userId = None
   grpId = None
   try:
      if request.method == 'POST' and authPermission.validate(request, "POST"):        
         userId = str(request.data['userid']) 
         grpId = str(request.data['grpid']) 
         kId = str(request.data['keyid'])
         pagetype = 'settings'
         brand = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId,id=kId)
         if brand.exists():
            brand.delete()
            groupExists = Groups.objects.filter(fk_user_id=userId, id=grpId).exists()
            serializerData = list()
            if groupExists:
               dataQuery = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId).order_by('-id')
               brands = dataQuery.values('id', 'bkeyword', 'input_json','serp_json','ads','report_format','brand_call_status','isocode').all()
               if brands:
                  serializerData = BrandSerializer(brands, many=True, context={'pagetype': pagetype}).data
                  # return JsonResponse({'st': 1, 'dt': serializerData,'message':"Keyword deleted successfully"}) 
               coreLog("Brand keywords deleted successfully", userId, grpId, "delete") 
               return JsonResponse({'st': 1,'dt':serializerData ,'message':"Keyword deleted successfully"}) 
   except Exception as e:
      uId = userId if userId else None
      gId = grpId if grpId else None
      coreLog("Brand keyword deletion failed > Exception error : "+str(e), uId, gId, "exp")

   return JsonResponse({'st': 0,'message': "Something went wrong"})  

@api_view(['POST'])
def comp__key__count(request):
   userId = None
   grpId = None
   try:
      if request.method == 'POST' and authPermission.validate(request, "POST"):        
         userId = str(request.data['userid']) 
         grpId = str(request.data['grpid']) 
         brand = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId)
         if brand.exists():
            brandCount = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId,brand_call_status__in=['INIT','SCHD']).count()
            if brandCount > 0:
               dataQuery = brandObtain.objects.filter(fk_user_id=userId,fk_group_id=grpId).order_by('-id')
               brands = dataQuery.values('id', 'bkeyword', 'input_json','serp_json','ads','report_format','brand_call_status','isocode').all()
               serializerData = list()
               if brands:
                  serializerData = BrandSerializer(brands, many=True, context={'pagetype': 'settings'}).data
               return JsonResponse({'st': 1, 'bc':brandCount, 'dt':serializerData}) 
   except Exception as e:
      uId = userId if userId else None
      gId = grpId if grpId else None
      coreLog("Brand keywords list ajax call failed > Exception error : "+str(e), uId, gId, "exp")

   return JsonResponse({'st': 0,'message': "Something went wrong"})
