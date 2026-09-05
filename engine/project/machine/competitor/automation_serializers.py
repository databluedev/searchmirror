
from datetime import datetime, date
from rest_framework import serializers 
from django.conf import settings
from django.utils import timezone

from project.machine.submodels.serpmodels import DKeyword, DGroups, DCompProject, DCompKeyword
from project.machine.submodels.accountmodels import Account

class CompCreateKeywordSerializer(serializers.Serializer): 

	def to_representation(self, obj):
		currdate = date.today()
		keywordIns = DKeyword.objects.filter(id=obj, fk_user_id=self.context["uid"],fk_group_id=self.context["gid"]).values('id','keyword','platform','isocode','language_code').first()

		if keywordIns: 
			keywords = DCompKeyword(
				fk_user_id = self.context["uid"],
				fk_group_id = self.context["gid"],
				fk_keyword_id = keywordIns["id"],
				fk_cp_project_id = self.context["cpid"],
				keyword = keywordIns["keyword"],
				cp_site_url=self.context["cpdomain"],
				target=self.context["cpdomain"],
				rank=[],
				ranknow=0,
				rank_sincestart=0,
				featured_snippet=0,
				status_from_start = "-",
				lastranked_date=timezone.now(),
				platform= keywordIns["platform"],
				isocode=keywordIns["isocode"],
				language_code=keywordIns["language_code"], 
				comp_call_mode="avail"
			)
			return keywords

		return None
