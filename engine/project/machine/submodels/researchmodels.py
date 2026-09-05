# from django.db import models
from djongo import models
from django.conf import settings
from project.machine.submodels.accountmodels import Account
from project.machine.submodels.serpmodels import DGroups

# Create your models here.
class DKeywordResearch(models.Model):
	fk_user = models.ForeignKey('Account', on_delete=models.CASCADE)
	fk_group = models.ForeignKey('DGroups', on_delete=models.CASCADE)
	search_text = models.TextField(default="")
	region_name = models.CharField(max_length=50)
	region_code = models.CharField(max_length=4, null=True)
	search_type = models.CharField(max_length = 10, default = 'keyword') # (- / 'keyword' or 'domain') 
	planner_status = models.CharField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE") 
	google_status = models.CharField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE")
	ontype_status = models.CharField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE", "START", "STOP", "COMP")
	research_refresh_count = models.IntegerField(default=0) 
	kw_ontype_array = models.JSONField(blank=True, default=[])  
	kw_related_array = models.JSONField(blank=True, default=[])
	search_results = models.CharField(max_length=20,default="-") # Remove 
	page_uuid_url = models.TextField(default="-")
	page_uuid = models.TextField(default="-")
	serp_json = models.JSONField(default={})
	created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
	modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)

	class Meta:
		db_table = "kw_research"