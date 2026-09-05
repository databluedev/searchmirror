# 6006f5c2372de8a93f6cc8a9

from django.conf.urls import url 
from django.urls import path

from project.machine.contentgap import test
from project.machine.contentgap import cga_scraper as cgSCR
from project.machine.contentgap import cga_initiate as cgINT
from project.machine.contentgap import cga_url_match as cgUM
from project.machine.contentgap import cga_url_rematch as cgURM

try:
	urlpatterns = [
		path('call/<str:_ustr_>/<str:_kstr_>', cgINT.automation_cga_call), # CGA Call 
		path('match/<str:_ustr_>/<str:_kstr_>', cgUM.automation_match_call), # CGA URLS MATCH Call 
		path('rematch/<str:_ustr_>/<str:_kstr_>', cgURM.automation_rematch_call), # CGA URLS REMATCH Call 
		# path('check', cgSCR.automation_cga_scraper), # CGA Call 
		path('test', test.testing), # Testing Call 
		
	] 
except Exception as e:
	print("ERR: "+ str(e)) 
