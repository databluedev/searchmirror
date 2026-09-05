from django.urls import path
from mailend import views as sysMail
from django.conf.urls import url , include

urlpatterns = [
	path('automation-trigger', sysMail.automationTrigger), 
]  
