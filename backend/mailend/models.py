# from django.db import models
from djongo import models
from serp.models import Keyword, Groups
from account.models import Account
# Create your models here.

class KeywordHistory(models.Model):
	fk_keyword = models.ForeignKey('serp.Keyword', on_delete=models.CASCADE)
	fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
	fk_group = models.ForeignKey('serp.Groups', on_delete=models.CASCADE)
	new_featured_snippet_date = models.DateTimeField(blank=True)
	featured_snippet_url_list = models.JSONField(blank=True, default=[])
	featured_snippet_history = models.JSONField(default={})
	new_ad_snippet_date = models.DateTimeField(blank=True)
	ad_snippet_url_list = models.JSONField(blank=True, default=[]) 
	ad_snippet_history = models.JSONField(default={}) 
	comp_today = models.JSONField(default={}) 
	url_status = models.CharField(max_length=5, default="CMN") 
	other_history = models.JSONField(default={}) 
	top_ratings = models.CharField(max_length=5,blank=True,default="-") 
	ratings_changed_date = models.DateTimeField(null=True) 
	created_date = models.DateTimeField(auto_now_add = True, auto_now = False) 
	modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)
	class Meta: 
		db_table = "keywordhistory" 