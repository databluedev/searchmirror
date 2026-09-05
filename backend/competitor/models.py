from djongo import models
from account.models import Account
from serp.models import Keyword, Groups 
from django.conf import settings

class CompProject(models.Model):
	# FOREIGN KEYS
	fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
	fk_group = models.ForeignKey('serp.Groups', on_delete=models.CASCADE)
	# OTHER FIELDS
	cp_group_name = models.CharField(max_length = 100)
	cp_domain_name = models.CharField(max_length=500, null=True)
	cp_grp_trigger = models.CharField(max_length = 5, default = "DONE") 
	# cp_dashboard_view = models.CharField(max_length=30, default='listview')
	cp_total_keyword = models.JSONField(blank=True, default=[]) 
	# cp_match_keyword = models.JSONField(blank=True, default=[]) 
	cp_top_score = models.CharField(null=True, max_length=10)
	mn_top_score = models.CharField(null=True, max_length=10)
	cp_activity_level = models.JSONField(blank=True, default=[])
	mn_activity_level = models.JSONField(blank=True, default=[])
	cp_since_position = models.JSONField(blank=True, default=[])  
	mn_since_position = models.JSONField(blank=True, default=[])  
	cp_score_meter = models.JSONField(blank=True, default=[])
	mn_score_meter = models.JSONField(blank=True, default=[])
	group_call_status = models.CharField(max_length=5, default = "COMP")
	keyword_ids = models.JSONField(blank=True, default=[])

	# Auto updated when data is inserted
	created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
	# Auto updated when the data is altered
	updated_date = models.DateTimeField(auto_now_add = False, auto_now = True)

	def __str__(self):
		return self.cp_group_name
	class Meta:
		db_table = "competitor_project"

class CompKeyword(models.Model): 
	# FOREIGN KEYS
	fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
	fk_group = models.ForeignKey('serp.Groups', on_delete=models.CASCADE)
	fk_keyword = models.ForeignKey('serp.Keyword', on_delete=models.CASCADE)
	fk_cp_project = models.ForeignKey('CompProject', on_delete=models.CASCADE)  

	# OTHER FIELDS
	cp_site_url = models.TextField()
	target = models.TextField(null=True)
	rank = models.JSONField(blank=True, default=[])
	ranknow = models.IntegerField(default=0)
	rank_sincestart = models.IntegerField(default=0)  
	featured_snippet = models.BooleanField(default=0) 
	review = models.BooleanField(default=0) 
	knowledge_panel = models.BooleanField(default=0) 
	ads = models.BooleanField(default=0) 
	total_rating = models.CharField(max_length=5, blank=True, default=None)
	total_review = models.CharField(max_length=15, blank=True, default=None) 
	snippets_details = models.JSONField(default={})
	dayval = models.IntegerField(default=0)
	weekval = models.IntegerField(default=0)
	halfmonthval = models.IntegerField(default=0)
	daymark = models.CharField(max_length=5, default="-") 
	weekmark = models.CharField(max_length=5, default="-")
	halfmonthmark = models.CharField(max_length=5, default="-")    
	status_from_start = models.CharField(max_length=5, default="-")
	comp_call_mode = models.CharField(max_length=5, default="done")
	auto_call_status = models.CharField(max_length=5,default="done")
	top_rank = models.IntegerField(default=0)
	lastranked_date = models.DateTimeField()

	comp_call_status = models.BooleanField(default=0)
	platform = models.CharField(max_length=10, default="desktop")
	language_code = models.CharField(max_length=8, null=True)     
	isocode = models.CharField(max_length=5, default="us")
	keyword = models.TextField(default="")
	# keyword_alias = models.TextField(default="")

	# Auto updated when data is inserted
	created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
	# Auto updated when the data is altered
	modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)

	class Meta:
		db_table = "competitor_keyword" 