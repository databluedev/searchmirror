# TESTING PURPOSE AND INITIATIVE
from django.shortcuts import render
from django.conf import settings 

from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings, KeywordHistory 
from project.machine.models import KeywordResearch

import sys, os, random

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

@api_view(['GET'])  
def __organic_page__(request, ustr, kstr):  

	content = None
	platform = None
	searchFile = "-"

	try: 
		SingleKeywords = Keyword.objects.filter(__raw__= {'id': int(ustr)}, page_uuid = str(kstr)).first()  
		if SingleKeywords: 
			platform = str(SingleKeywords.platform)
			searchFile = os.getcwd()+"/project/files/"+platform+"/searchFile__"+str(SingleKeywords.id)+".html"
			with open(searchFile, 'r+') as f:
				content = f.read()

			if content != None or content != "":  
			 	return JsonResponse({'status': 'true', 'content':str(content)}) 
	except:
		pass 	

	return JsonResponse({'status': 'false', 'content': content})  

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@api_view(['GET'])  
def __research_page__(request, ustr, kstr): 

	content = None
	searchFile = "-"

	try: 
		SingleKeywords = KeywordResearch.objects.filter(__raw__= {'id': int(ustr)}, page_uuid = str(kstr)).first()  
		if SingleKeywords: 
			searchFile = os.getcwd()+"/project/files/research/researchFile__"+str(SingleKeywords.id)+".html"
			with open(searchFile, 'r+') as f:
				content = f.read()

			if content != None or content != "":  
			 	return JsonResponse({'status': 'true', 'content':str(content)}) 
	except:
		pass 	

	return JsonResponse({'status': 'false', 'content': content})  


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~