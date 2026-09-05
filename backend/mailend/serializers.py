from rest_framework import serializers
from serp.models import *
from serp.common import *
from .models import *
from account.models import Account 
from bisect import bisect_right 
from datetime import date,datetime,timedelta 
from collections import Counter
import collections
import numpy
from django.conf import settings
from mailend import views as aView
from django.db.models import Q
from shared.scoring import calculate_visibility_history


def _live_score_history(group):
	"""Recompute a project's visibility history instead of reading its cache.

	`Groups.score_meter` and `Groups.top_score` are a snapshot written only when
	the engine runs. Every on-screen surface now recomputes from the keyword
	rank arrays (serp/project_management.py:84 via calculate_visibility_history),
	so reading the stored copy here mails the account a number that contradicts
	the dashboard it is looking at. Measured on this instance:

	    group   stored score / top      recomputed score / top
	    1       34.99 / 42.5            37.86 / 44.17
	    2       None  / None            100.0 / 100.0
	    4       4.0   / 18.0            4.0   / 25.0

	Group 4 is the case that matters most: the "new best score" mail below
	compares the stored value against the stored maximum, so it is internally
	consistent and externally wrong -- it would announce a record of 18 for a
	project whose real best is 25, and stay silent when the real score sets an
	actual record. Silence on a true record is the half nobody notices.

	Returns newest-first, matching score_meter's own ordering, or [] when the
	project has no measurable history.
	"""
	ranks = list(
		Keyword.objects.filter(
			fk_user_id=group.fk_user_id, fk_group_id=group.id
		).values_list("rank", flat=True)
	)
	return calculate_visibility_history(ranks) or []

# Global Values
defaultTrackerScoreLimit = 20
defaultWeekImprovementLimit = 10  
defaultDataCount = 5

def diffChecker(v1, v2): 
	global defaultTrackerScoreLimit 
	diff = abs(float("%.2f" % round((float(v1)-float(v2)), 2))) 
	return "yes" if diff > defaultTrackerScoreLimit else "no" 

def weekImpChecker(rankarray):
	global defaultWeekImprovementLimit  
	imp_status = "improve"
	if len(rankarray) == 7 and len(set(rankarray)) == 1:
		if int(rankarray[0]) > defaultWeekImprovementLimit or int(rankarray[0]) == 0:
			imp_status = "worsen"
	return imp_status 

class BrandConquestorSerializer(serializers.ModelSerializer): # brandTracker
	acc_id = serializers.SerializerMethodField()
	acc_name = serializers.SerializerMethodField()
	acc_email = serializers.SerializerMethodField()
	acc_brand = serializers.SerializerMethodField()
	ps_url = serializers.SerializerMethodField()
	
	class Meta: 
		model = brandTracker
		fields = ('acc_id', 'acc_name', 'acc_email', 'acc_brand','ps_url') 

	def to_representation(self, obj):
		brandUser = Account.objects.filter(id=obj.fb_user_id).values('id', 'email', 'username').first() 
		grpIns = Groups.objects.filter(id=obj.fb_group_id,fk_user_id=obj.fb_user_id).values('id', 'group_name').first() 
		brandResult = []
		projectSettingURL = str(settings.SITE_URL)
		if brandUser:
			if len(obj.conquestor_recent_list) > 0:
				brandResult.append({ 
					'ky': obj.id,
					'uid': obj.fb_user_id,
					'gid': obj.fb_group_id,
					'bn': obj.brand_name,
					'c_st': obj.conquestor_call_status,
					'r_lt': obj.conquestor_recent_list,
					'm_de': obj.conquestor_mail_date, 
				})
				projectSettingURL = aView.projectSettingURL_gen(obj.fb_user_id, obj.fb_group_id, grpIns['group_name'])

			if len(brandResult):
				return {
					'acc_brand': brandResult,  
					'acc_email' : brandUser['email'],
					'acc_username' : brandUser['username'],  
					'acc_id': brandUser['id'],
					'ps_url' : projectSettingURL,
				} 
		return None

class DashKeywordSerializer(serializers.ModelSerializer):
	tags = serializers.ListField()
	rank = serializers.ListField() 
	snippets_details = serializers.DictField(
		child = serializers.DictField() 
	)
	bestrank = serializers.SerializerMethodField()
	startrank = serializers.SerializerMethodField()
	
	class Meta:
		model = Keyword
		fields = ('platform','bestrank','startrank','total_rating','total_review','snippets_details','ranknow','rank','id','keyword','site_url','exactdomain','keyword_alias','favour','region','language','isocode','search_results','search_volume','daymark','dayval','weekmark','weekval','halfmonthmark','halfmonthval','tags','review','featured_snippet','knowledge_panel','ads','created_date','page_uuid_url') 

	def get_startrank(self, obj):
		return obj.rank[-1] 
	
	def get_bestrank(self, obj):
		minimum = 0
		orgrank = list(set(obj.rank))
		totalrank = list(filter(lambda num: num != 0, orgrank))

		return min(totalrank) if len(totalrank) > 0 else 0  

class MailFavKeywordSerializer(serializers.ModelSerializer):
	rank = serializers.SerializerMethodField()
	kuid = serializers.SerializerMethodField('get_key_user_id') 
	class Meta:
		model = Keyword
		fields = ('kuid','platform','ranknow','rank','id','keyword','favour','region','daymark','dayval')  
	def get_rank(self, obj): 
		return obj.rank[0:7] 
	def get_key_user_id(self, obj):
		return obj.fk_user_id 

# Tracker Score 
class MailGroupSerializer(serializers.ModelSerializer):
	acc_group = serializers.SerializerMethodField()
	acc_email = serializers.SerializerMethodField() 
	acc_username = serializers.SerializerMethodField() 
	acc_id = serializers.SerializerMethodField()   

	class Meta: 
		model = Account
		fields = ('acc_group', 'acc_email', 'acc_username', 'acc_id')

	def to_representation(self, obj):
		check = "no"
		allGroup = Groups.objects.filter(fk_user_id=obj.id).all() 
		if allGroup and "system" in self.context:  
			scoreTotalResult = []
			for singleGroup in allGroup:
				if singleGroup:
					userswitch = True
					if 'SSA' in singleGroup.automation_email_switch: 
						userswitch = singleGroup.automation_email_switch['SSA']

					if userswitch == True:
						if len(singleGroup.total_Keyword) > 1 and aView.automationRepeatCheck(self.context['system'], obj.id, singleGroup.id, "s-score"):
							if int(singleGroup.total_Keyword[0]) == int(singleGroup.total_Keyword[1]):
								# Recomputed, not singleGroup.score_meter -- see
								# _live_score_history. Mailing a score the
								# dashboard disagrees with is worse than not
								# mailing one.
								liveScore = _live_score_history(singleGroup)
								if len(liveScore) > 1:
									todayScore, prevScore = liveScore[0], liveScore[1]
									check = diffChecker(todayScore, prevScore)
									if check == "yes":
										reciptmail = singleGroup.automation_email_recipients
										scoreTotalResult.append({
											'gid' : singleGroup.id,
											'group_name' : singleGroup.group_name,
											'domain_name' : singleGroup.domain_name,
											'prevscore' : prevScore,
											'newscore' : todayScore,
											'status': "up" if abs(float(todayScore)) > abs(float(prevScore)) else "down",
											'reciptmail' : reciptmail
										}) 

			if len(scoreTotalResult):
				return {
					'acc_group': scoreTotalResult,  
					'acc_email' : obj.email,
					'acc_username' : obj.username,  
					'acc_id': obj.id, 
				}
		return None

class NoWeeklyImprovementSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField() 
	guid = serializers.SerializerMethodField() 
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid', 'ps_url') 

	def to_representation(self, obj):
		global defaultDataCount
		check = "no"
		projectSettingURL = str(settings.SITE_URL)
		keyResultData = []
		dataCount = 0

		if obj and "system" in self.context:
			userswitch = True
			if 'NIMP' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['NIMP']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-noimprovement"):
					allGrpKeyData = Keyword.objects.filter(fk_group_id=obj.id).values('id','rank','keyword','site_url').all()
					if allGrpKeyData: 
						for keyData in allGrpKeyData:
							if weekImpChecker(keyData['rank'][0:7]) == "worsen":
								check = "yes"
								if dataCount <= (defaultDataCount - 1):
									keyResultData.append({ 
										'keyword' : keyData['keyword'],
										'idlerank' : keyData['rank'][0],
										'id': keyData['id'], 
										'site_url': keyData['site_url'], 
									}) 
								dataCount += 1
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)

		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,  
				'guid': obj.fk_user_id,  
				'gname' : obj.group_name,
				'gkeywords' : keyResultData,
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name, 
				'count': dataCount,  
				'rows': defaultDataCount, 
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None

class cannibalisationSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()  
	guid = serializers.SerializerMethodField()  
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid','ps_url')  

	def to_representation(self, obj):
		global defaultDataCount
		check = "no" 
		keyResultData = []
		projectSettingURL = str(settings.SITE_URL)
		dataCount = 0

		if obj and "system" in self.context:
			userswitch = True
			if 'CNN' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['CNN']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-cannib"): 
					allGrpKeySetData = Keyword.objects.exclude(cannibalisation=[]).filter(fk_group_id=obj.id, cannibalisation_mail_status="-").values('id','ranknow','keyword', 'cannibalisation') 

					allGrpKeyData = allGrpKeySetData[0:defaultDataCount]
					dataCount = allGrpKeySetData.count() 

					if allGrpKeyData: 
						for keyData in allGrpKeyData:
							if len(keyData['cannibalisation']) > 0: 
								check = "yes" 
								
								keyResultData.append({
									'keyword' : keyData['keyword'],
									'rank' : keyData['ranknow'],
									'cannibalisation' : keyData['cannibalisation'],
									'id' : keyData['id'],
								}) 
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)

		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,  
				'guid': obj.fk_user_id, 
				'gname' : obj.group_name,
				'gkeywords' : keyResultData,
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name, 
				'count': dataCount,
				'rows': defaultDataCount,  
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None 

class ratingSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()  
	guid = serializers.SerializerMethodField()  
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid','ps_url')  

	def to_representation(self, obj):
		global defaultDataCount 
		check = False
		historyResultData = []
		projectSettingURL = str(settings.SITE_URL)
		dataCount = 0 

		if obj and "system" in self.context:
			userswitch = True
			if 'RS' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['RS']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-rating"): 
					currdate = str(date.today())
					tomorrow = str(date.today() + timedelta(days = 1)) 

					allGrpHistorySetData = KeywordHistory.objects.filter(fk_group_id=obj.id,ratings_changed_date__range=(currdate, tomorrow)) 
					
					allGrpHistoryData = allGrpHistorySetData[0:defaultDataCount] 
					dataCount = allGrpHistorySetData.count() 

					if allGrpHistoryData:  
						for historyData in allGrpHistoryData:
							if historyData:
								keyData = Keyword.objects.filter(id=historyData.fk_keyword_id).first()
								if keyData:
									check = "yes"
									historyResultData.append({ 
										'keyword' : keyData.keyword,
										'rank' : keyData.ranknow, 
										'last_rating' : historyData.other_history['last_rating'],
										'new_rating' : historyData.other_history['new_rating'],
										'top_rating' : historyData.top_ratings,
										'id' : keyData.id,
									})
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)

			 
		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,
				'guid': obj.fk_user_id,   
				'gname' : obj.group_name,
				'gkeywords' : historyResultData,
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name, 
				'count': dataCount,  
				'rows': defaultDataCount,  
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None 

# Ads serializer.

class adSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()  
	guid = serializers.SerializerMethodField()  
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid', 'ps_url')  

	def to_representation(self, obj):
		global defaultDataCount 
		check = False
		adsResultData = []
		projectSettingURL = str(settings.SITE_URL)
		dataCount = 0 

		if obj and "system" in self.context:
			userswitch = True
			if 'ADS' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['ADS']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-ads"):
					currdate = str(date.today())
					tomorrow = str(date.today() + timedelta(days = 1)) 

					allGrpAdsSetData = KeywordHistory.objects.filter(fk_group_id=obj.id,new_ad_snippet_date__range=(currdate, tomorrow)) 

					allGrpAdsData = allGrpAdsSetData[0:defaultDataCount]
					dataCount = allGrpAdsSetData.count()

					if allGrpAdsData:  
						for adsData in allGrpAdsData:
							if adsData: 
								keyData = Keyword.objects.filter(id=adsData.fk_keyword_id).first()
								if keyData:
									check = "yes"
									adsResultData.append({
										'keyword' : keyData.keyword,
										'rank' : keyData.ranknow,
										'ad_status' : adsData.ad_snippet_history['status'],
										'recent_ads' : adsData.ad_snippet_history['recent'],
										'ad_date' : adsData.new_ad_snippet_date,
										'id' : keyData.id,
									}) 
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)
			 
		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,  
				'guid': obj.fk_user_id, 
				'gname' : obj.group_name,
				'gkeywords' : adsResultData,
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name,
				'count': dataCount,  
				'rows': defaultDataCount,  
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None 

# Featured serializer.

class featuredSerializer(serializers.ModelSerializer): 
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()  
	guid = serializers.SerializerMethodField()  
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid', 'ps_url')  

	def to_representation(self, obj):
		global defaultDataCount 
		check = False
		projectSettingURL = str(settings.SITE_URL)
		featuredResultData = []
		dataCount = 0  

		if obj and "system" in self.context:
			userswitch = True
			if 'FS' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['FS']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-featured"): 
					currdate = str(date.today())
					tomorrow = str(date.today() + timedelta(days = 1))

					allGrpFeaturedSetData = KeywordHistory.objects.filter(fk_group_id=obj.id,new_featured_snippet_date__range=(currdate, tomorrow))

					allGrpFeaturedData = allGrpFeaturedSetData[0:defaultDataCount]
					dataCount = allGrpFeaturedSetData.count()

					if allGrpFeaturedData:  
						for featuredData in allGrpFeaturedData:
							if featuredData: 
								keyData = Keyword.objects.filter(id=featuredData.fk_keyword_id).first()
								if keyData:
									check = "yes"
									featuredResultData.append({
										'keyword' : keyData.keyword,
										'rank' : keyData.ranknow,
										'featured_status' : featuredData.featured_snippet_history['status'],
										'recent_featured' : featuredData.featured_snippet_history['recent'],
										'featured_date' : featuredData.new_featured_snippet_date,
										'id' : keyData.id,
						 			})
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)

		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,
				'guid': obj.fk_user_id,  
				'gname' : obj.group_name,
				'gkeywords' : featuredResultData, 
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name,
				'count': dataCount,  
				'rows': defaultDataCount,   
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None 

# Url serializer.

class urlSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()   
	guid = serializers.SerializerMethodField()   
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid', 'ps_url')   

	def to_representation(self, obj):
		global defaultDataCount 
		check = False
		projectSettingURL = str(settings.SITE_URL)
		urlResultData = []
		dataCount = 0  

		if obj and "system" in self.context:
			userswitch = True
			if 'URL' in obj.automation_email_switch: 
				userswitch = obj.automation_email_switch['URL']

			if userswitch == True:
				if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-url"): 
					allGrpUrlSetData = KeywordHistory.objects.filter(fk_group_id=obj.id, url_status="UNQ")

					allGrpUrlData = allGrpUrlSetData[0:defaultDataCount]
					dataCount = allGrpUrlSetData.count()

					if allGrpUrlData:  
						for urlData in allGrpUrlData:
							if urlData: 
								keyData = Keyword.objects.filter(id=urlData.fk_keyword_id).first()
								if keyData:
									check = "yes"
									urlResultData.append({ 
										'keyword' : keyData.keyword,
										'rank' : keyData.ranknow,
										'previous_rank' : keyData.rank[1] if len(keyData.rank) > 1 else "-",
										'change_rank_value' : keyData.dayval,
										'change_rank_mark' : keyData.daymark,
										'old_url' : urlData.other_history['last_url'] if 'last_url' in urlData.other_history else "-",
										'new_url' : urlData.other_history['new_url'] if 'new_url' in urlData.other_history else "-",
										'id' : keyData.id,
										'url_status' : urlData.url_status, 
										'ssl_status' : urlData.other_history['ssl'] if urlData.other_history['ssl'] != None else "-",
									}) 
						projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)
			 			
		if check == "yes":
			accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
			return {
				'gid': obj.id,
				'guid': obj.fk_user_id,   
				'gname' : obj.group_name,
				'gkeywords' : urlResultData,  
				'gemail': accData['email'] if accData else "",  
				'gusername': accData['username'] if accData else "user",
				'gdomain': obj.domain_name,
				'count': dataCount,  
				'rows': defaultDataCount,  
				'reciptmail': obj.automation_email_recipients,
				'ps_url' : projectSettingURL,
			}
		else:
			return None

# Score Serializer

class scoreSerializer(serializers.ModelSerializer):
	acc_group = serializers.SerializerMethodField()
	acc_email = serializers.SerializerMethodField() 
	acc_username = serializers.SerializerMethodField() 
	acc_id = serializers.SerializerMethodField()     

	class Meta: 
		model = Account
		fields = ('acc_group', 'acc_email', 'acc_username', 'acc_id')   

	def to_representation(self, obj):
		allGroup = Groups.objects.filter(fk_user_id=obj.id).all() 
		
		if allGroup and "system" in self.context: 
			scoreTotalResult = []
			for singleGroup in allGroup:
				if singleGroup:
					# Recomputed, not the stored score_meter/top_score pair -- see
					# _live_score_history. The stored comparison was internally
					# consistent and externally wrong: it announced a record of
					# 18 on a project whose real best is 25, and said nothing
					# when the real score set an actual record.
					liveScore = _live_score_history(singleGroup)
					liveTop = max(liveScore) if liveScore else 0
					if len(liveScore) > 1 and float(liveTop) > 0 and aView.automationRepeatCheck(self.context['system'], obj.id, singleGroup.id, "s-bestscore"):
						xValue = int(float(liveTop))
						scoreMeterValues = list(map(int, map(float, liveScore)))
						scoreMeterToday = int(float(liveScore[0]))

						counterParts = Counter(scoreMeterValues)  
						if counterParts[xValue] == 1 and scoreMeterToday == xValue:
							scoreTotalResult.append({
								'gid' : singleGroup.id, 
								'group_name' : singleGroup.group_name,
								'domain_name' : singleGroup.domain_name,
								'score' : xValue, 
							})
							 
			if len(scoreTotalResult):
				return {
					'acc_group': scoreTotalResult,  
					'acc_email' : obj.email,
					'acc_username' : obj.username,  
					'acc_id': obj.id,
				} 
		return None  


# Maximum Keyword Serializer

class MaxKeywordSerializer(serializers.ModelSerializer):
	acc_email = serializers.SerializerMethodField() 
	acc_username = serializers.SerializerMethodField() 
	acc_id = serializers.SerializerMethodField()   
	acc_uid = serializers.SerializerMethodField()   

	class Meta:
		model = Accountusage
		fields = ('acc_email', 'acc_username', 'acc_id', 'acc_uid')   

	def to_representation(self, obj):
		#changed
		sts,cnt = totalKeywordsCount(obj.fb_user_id)
		allAccountUsageData = cnt
		# allAccountUsageData = Keyword.objects.filter(fk_user_id=obj.fb_user_id).count() 

		if allAccountUsageData == obj.plan_keyword_limit and obj.mail_max_keyword_reach == "-": 
			accData = Account.objects.filter(id=obj.fb_user_id).values('email','username').first() 
			return { 
				'acc_id': obj.id,  
				'acc_uid': obj.fb_user_id,   
				'acc_email': accData['email'] if accData else "",  
				'acc_username': accData['username'] if accData else "user",  
			}
		
		return None 

# New Release Serializer

class NewReleaseSerializer(serializers.ModelSerializer):
	class Meta:
		model = Account
		fields = ('id', 'username', 'email')   

# Account History Serializer

class AccountHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = KeywordHistory
		fields = '__all__'
		extra_kwargs = {
            'new_featured_snippet_date': {'required': False},
            'featured_snippet_history': {'required': False},
            'featured_snippet_url_list': {'required': False}
        } 

	def create(self, validated_data):
		return KeywordHistory.objects.create(**validated_data) 

# Score Serializer 

#Brand Acquisition Serializer   

class BrandAcquisitionSerializer(serializers.ModelSerializer):
	gkeywords = serializers.SerializerMethodField()
	gname = serializers.SerializerMethodField() 
	gemail = serializers.SerializerMethodField() 
	gusername = serializers.SerializerMethodField() 
	gdomain = serializers.SerializerMethodField() 
	gid = serializers.SerializerMethodField()  
	guid = serializers.SerializerMethodField()  
	ps_url = serializers.SerializerMethodField()  

	class Meta:
		model = Groups
		fields = ('gkeywords', 'gname', 'gemail', 'gusername', 'gdomain', 'gid', 'guid', 'ps_url')  

	def to_representation(self, obj):
		global defaultDataCount 
		check = False
		adsResultData = []
		projectSettingURL = str(settings.SITE_URL)
		dataCount = 0 

		if obj and "system" in self.context:
			userswitch = True
			if 'BA' in obj.automation_email_switch:  
				userswitch = obj.automation_email_switch['BA']
				if userswitch == True:
					if aView.automationRepeatCheck(self.context['system'], obj.fk_user_id, obj.id, "s-brands"): 
						currdate = str(date.today())
						tomorrow = str(date.today() + timedelta(days = 1)) 
						# allGrpAdsSetData = brandObtain.objects.filter(fk_group_id=obj.id,brand_call_status="DONE", brand_recent_date__range=(currdate, tomorrow), brand_mail_date__lte=currdate, ads__gt=0).all()
						# allGrpAdsSetData = brandObtain.objects.filter(fk_group_id=obj.id,brand_call_status="DONE",brand_recent_date__range=(currdate, tomorrow), modified_date__range=(currdate, tomorrow), ads__gt=0).all()
						allGrpAdsSetData = brandObtain.objects.filter(fk_group_id=obj.id,brand_call_status="DONE", brand_recent_date__range=(currdate, tomorrow), brand_mail_date__lte=date.today(), ads__gt=0)
						if allGrpAdsSetData:  
							for keyData in allGrpAdsSetData:
								check = "yes"
								adsResultData.append({
									'keyword' : keyData.bkeyword, 
									'ads_count' : keyData.serp_json['ads']['top_count'] + keyData.serp_json['ads']['bottom_count'],
									'ad_status' : "yes" if keyData.ads == 2 else "no" ,
									'recent_ads' : keyData.serp_json['urls'],
									'id' : keyData.id,
								}) 
							projectSettingURL = aView.projectSettingURL_gen(obj.fk_user_id, obj.id, obj.group_name)
								
						if check == "yes":
							accData = Account.objects.filter(id=obj.fk_user_id).values('email','username').first() 
							return {
								'gid': obj.id,  
								'guid': obj.fk_user_id, 
								'gname' : obj.group_name,
								'gkeywords' : adsResultData,
								'gemail': accData['email'] if accData else "",  
								'gusername': accData['username'] if accData else "user",
								'gdomain': obj.domain_name,
								'count': dataCount,  
								'rows': defaultDataCount,  
								'reciptmail': obj.automation_email_recipients,
								'ps_url' : projectSettingURL,
							}
					else:
						return None 
		else:
			return None 
