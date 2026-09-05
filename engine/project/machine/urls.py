
from django.conf.urls import url
from project.machine import views, automation_daily_start as aDS, automation_engine as aE, automation_manual as aM, rawsource as rV
from project.machine import automation_brand as aBN
from project.machine.competitor import automation_analyse as aAS
from project.machine.competitor import automation_call as aAC


from django.urls import path

urlpatterns = [

	path('engine/test', views.testing), # Testing Call

	path('engine/daystart/<str:_ustr_>', aDS.daily_automation_first_call), # Daily Start (Reset)

	path('engine/call/<str:_ustr_>/<str:_kstr_>', aE.automation_engine_call),
	
	path('manual/call/<str:_ustr_>/<str:_kstr_>', aM.automation_manual_call),
	
	path('brand/call/<str:_ustr_>/<str:_kstr_>', aBN.automation_brand_call), 
	
	path('competitor/call/<str:_ustr_>/<str:_kstr_>', aAC.automation_comp_call),  
	
	path('competitor/launch/<str:_ustr_>/<str:_kstr_>', aAS.automation_ai_call), 

	path('results/<str:ustr>/<str:kstr>', rV.__organic_page__),
	
	
] 
