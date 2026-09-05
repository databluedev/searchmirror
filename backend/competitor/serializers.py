from serp.rank_state import apply_rank_state
from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS 
from .models import *
from serp.common import *
from serp.models import *
from account.models import Account  
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta 
from urllib.parse import urlparse
# from tldextract import extract
import os, json

current_day = date.today()
this_week_first_date =current_day - timedelta(days=current_day.isoweekday())
this_week_days = (this_week_first_date - current_day).days
this_week_day = abs(this_week_days)+1


def timeDifference(later_time, formattype="full"):
	current_time = datetime.now() 
	start = current_time.strptime(current_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
	ends = datetime.strptime(later_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

	diff = relativedelta(start, ends)

	multiples = 0
	portion = ""

	if diff.years > 0:
		multiples = diff.years
		portion = str(diff.years)+" "+"year"
	elif diff.months > 0:
		multiples = diff.months
		portion = str(diff.months)+" "+"month"
	elif diff.days > 0:
		multiples = diff.days
		portion = str(diff.days)+" "+"day"
	elif diff.hours > 0:
		multiples = diff.hours
		portion = str(diff.hours)+" "+"hour"
	elif diff.minutes > 0:
		multiples = diff.minutes
		portion = str(diff.minutes)+" "+"minute"
	elif diff.seconds > 0:
		multiples = diff.seconds
		portion = str(diff.seconds)+" "+"second"

	returnContent = ""
	if portion == "": 
		returnContent = " Just now "
	elif portion != "" and multiples > 1: 
		returnContent = portion + "s ago"
	else:
		returnContent = portion+" ago" 

	if formattype == "off":
		return returnContent 
	else:
		return returnContent + " ("+custom_strftime('%b {S}, %Y', later_time)+")" 
	# return portion+multiples+" "+"ago" + " ("+custom_strftime('%B {S}, %Y', later_time)+")"


def domain_valid(domain):
	dmurl = domain
	if dmurl:
		uri = urlparse(dmurl)
		if (uri.scheme == "" or uri.scheme is None):
			dmurl = "https://"+domain
	return dmurl

# def comp_project_name(domain):
# 	dmurl = domain
#     if dmurl:
#         uri = extract(dmurl)
#         print("domain", uri)
#         # if (uri.scheme == "" or uri.scheme is None):
#         #     dmurl = "http://"+domain
#     return dmurl


# Create keyword, add keyword, new wizard
class CompProjectSerializer(serializers.ModelSerializer):
	key = serializers.SerializerMethodField('get_key')
	pn = serializers.SerializerMethodField('get_projectname')
	dn = serializers.SerializerMethodField('get_domainname')
	class Meta: 
		model = Language
		fields = ('key', 'pn','dn')

	def get_key(self, obj):
		return obj.id

	def get_projectname(self, obj):
		return obj.cp_group_name

	def get_domainname(self, obj):
		return obj.cp_domain_name

	def to_representation(self, obj):
		superData = super().to_representation(obj) 
		
		# Group Based Keywords
		# superData['kw_ln'] = Keyword.objects.filter(fk_group_id=obj.id,fk_user_id=obj.fk_user_id).count()
		superData['Tk'] = Keyword.objects.filter(fk_group_id=obj.fk_group_id,fk_user_id=obj.fk_user_id).count()
		superData['Mtk'] = obj.cp_total_keyword[0]  if obj.cp_total_keyword and len(obj.cp_total_keyword) > 0 else None
		superData['yMtk'] = obj.cp_total_keyword[1]  if obj.cp_total_keyword and len(obj.cp_total_keyword) > 1 else -1
		# superData['Mtk'] = Matching keyword update pending

		superData['rT'] = timeDifference(obj.updated_date, "off")  
		superData['ss'] = f_to_i(obj.cp_score_meter[0]) if len(obj.cp_score_meter) > 0 else 0
		superData['yss'] = f_to_i(obj.cp_score_meter[1]) if len(obj.cp_score_meter) > 1 else -1
		superData['bss'] = f_to_i(obj.cp_top_score) if obj.cp_top_score else -1

		superData['fp'] = int(obj.cp_since_position[0].split(',')[0]) if len(obj.cp_since_position) > 0 else 0
		superData['yfp'] = int(obj.cp_since_position[1].split(',')[0]) if len(obj.cp_since_position) > 1 else -1

		activityGroupData = list(map(str, obj.cp_activity_level[0].split('|'))) if len(obj.cp_activity_level) > 0 else [0,0,0]
		if len(activityGroupData) == 3:
		    superData['ik'] = int(activityGroupData[1])
		    superData['dk'] = int(activityGroupData[2])
		else:
		    superData['ik'] = 0
		    superData['dk'] = 0

		activityGroupData = list(map(str, obj.cp_activity_level[1].split('|'))) if len(obj.cp_activity_level) > 1 else [-1,-1,-1]
		if len(activityGroupData) == 3:
		    superData['yik'] = int(activityGroupData[1])
		    superData['ydk'] = int(activityGroupData[2])
		else:
		    superData['yik'] = -1
		    superData['ydk'] = -1

		# superData['ik'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="up").count()
		# superData['dk'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="down").count()

		# crawlkwCount = CompKeyword.objects.filter(fk_user_id=obj.fk_user_id, fk_group_id=obj.fk_group_id, fk_cp_project_id=obj.id, comp_call_status__in=[True]).count()
		# superData['mrk'] = 1 if crawlkwCount > 0 else 0
		superData['mrk'] = 1 if obj.id in self.context else 0
		superData['gA'] = len(obj.cp_score_meter)

		return superData

# class CompKeywordSerializer(serializers.ModelSerializer):
# 	class Meta: 
# 		model = CompKeyword
# 		fields = '__all__'

# Main group used New competitor group bulk create
class CompProjectCreateSerializer(serializers.Serializer):

	def to_representation(self, obj):
		# testid = 7
		aiFile = os.getcwd()+"/competitor/ai_files/keys/aiKeys__"+str(self.context["grpid"])+".json"
		try:
			data = open(""+aiFile).read()
			content = json.loads(data)
			keyword_list = list(content[obj])
		except Exception as e:
			# raise e
			keyword_list = []

		groups = CompProject(
			fk_user_id = self.context["userid"],
			fk_group_id = self.context["grpid"],
			# cp_group_name = comp_project_name(obj),
			cp_group_name = str(self.context["data"][obj]),
			cp_domain_name = domain_valid(obj),
			keyword_ids= keyword_list,
			cp_grp_trigger = "",
		)
		# if len(keyword_list) > 0:
		# else:
		# 	groups = None

		return groups

# Main keywords id used New competitor keywords bulk create
class CompProjectKeywordCreateSerializer(serializers.Serializer):

	def to_representation(self, obj):
		compPrt = CompProject.objects.filter(fk_user_id=self.context["userid"],fk_group_id=self.context["grpid"],id=obj)
		compPrtIns = compPrt.values('keyword_ids','cp_domain_name').first()
		
		main_kwids = list(Keyword.objects.filter(fk_user_id=self.context["userid"],fk_group_id=self.context["grpid"]).values_list('id', flat=True).all())
		selected_kwids = set(compPrtIns['keyword_ids']).intersection(main_kwids)

		if len(selected_kwids) > 0:
			# serializer = CompKeywordCreateSerializer([32, 34, 35, 56, 57, 58], many=True, 
			serializer = CompKeywordCreateSerializer(list(selected_kwids), many=True, 
			    context={'userid':self.context["userid"], 'grpid':self.context["grpid"], 'cp_projectid': obj, 'url':compPrtIns['cp_domain_name']})
			# keywords = list(filter(None, serializer.data))
			keywords = serializer.data
			
			if len(keywords) > 0:
			    bulk_keywords = CompKeyword.objects.bulk_create(keywords)

			compPrtUpdate = compPrt.update(keyword_ids=[])

		return len(selected_kwids)

# Main keywords id used New competitor keywords bulk create
class CompKeywordCreateSerializer(serializers.Serializer):

	def to_representation(self, obj):
		currdate = date.today()
		keywordIns = Keyword.objects.filter(id=obj).values('id','keyword','platform','isocode','language_code').first()

		keywords = CompKeyword(
			fk_user_id = self.context["userid"],
			fk_group_id = self.context["grpid"],
			fk_keyword_id = keywordIns["id"],
			fk_cp_project_id = self.context["cp_projectid"],
			keyword = keywordIns["keyword"],
			cp_site_url=self.context["url"],
			target=self.context["url"],
			rank=[],
			ranknow=0,
			rank_sincestart=0,
			featured_snippet=0,
			status_from_start = "-",
			lastranked_date=datetime.now(),
			platform= keywordIns["platform"],
			isocode=keywordIns["isocode"],
			language_code=keywordIns["language_code"],
			comp_call_mode="avail"
			# region= request.data['region'].strip(),
			# language= request.data['language'],
			# language_code= self.context["languageData"].language_code.strip(),
		)
		# if keywordIns:
		# else:
		# 	keywords = None

		return keywords


class CompKeywordSerializer(serializers.Serializer):

	def to_representation(self, obj):
		# prefixConst = 98765
		# prefixConst = DEF_SETTINGS.UNIQUE_KEYWORD_ID
		prefixConst = 0 
		global comp_levels
		global this_week_day

		mainkwData = Keyword.objects.filter(id=obj['fk_keyword_id']).values(
			'id','rank','ranknow','manual_call_mode','serp_pages').first()
		if mainkwData:
			#common
			superData = super().to_representation(obj) 

			superData['KW'] = obj['keyword']
			superData['RK'] = obj['rank'][0:2] if this_week_day < 2 else obj['rank'][0:this_week_day]
			# The competitor's own position, and below it the tracked domain's.
			# RS/MRS say which of the four states each is in; the tooltip's rank
			# arithmetic is only valid when the state is "ranked".
			superData['RW'], _rs, _rc, _rsk = apply_rank_state(superData, obj, self.context.get('account_pages'))
			
			superData['key'] = prefixConst + int(mainkwData['id'])
			superData['MRK'] = mainkwData['rank'][0:len(superData['RK'])]
			# superData['MRK'] = mainkwData['rank'][0:2] if this_week_day < 2 else mainkwData['rank'][0:this_week_day]
			superData['MRW'], _mrs, _mrc, _mrsk = apply_rank_state(
				superData, mainkwData, self.context.get('account_pages'), prefix='MR')

			superData['lrd'] = obj['lastranked_date'].date()
			superData['t_c'] = len(obj['rank'])
			#create date
			superData['cd']= obj['created_date'].strftime('%Y-%m-%d')
			superData['lrupt'] = timeDifference(obj['lastranked_date'], "off")

			#Action
			# superData['CR'] = obj.page_uuid_url
			superData['CR'] = ""

			#Best rank
			superData['brnk'] = int(obj['top_rank'])

			#1D
			superData['OD'] = obj['dayval'] if obj['daymark'] != "down" else -abs(int(obj['dayval']))
			#7D
			superData['SD'] = obj['weekval'] if obj['weekmark'] != "down" else -abs(int(obj['weekval']))
			#15D
			superData['XD'] = obj['halfmonthval'] if obj['halfmonthmark'] != "down" else -abs(int(obj['halfmonthval']))

			#Features
			sniptkys = set(obj['snippets_details'].keys())
			if len(sniptkys):
				rmvSniptkys = {'featured_box','ads','knowledge_box','current'}
				sniptkys = sniptkys-rmvSniptkys 

			order = ['slrs','twrs','lcrs','imrs','vdrs','nwrs','rqrs','mprs']
			ordervalue = list(sniptkys - set(order))  
			snipSetKeys = list(sniptkys)
			if len(ordervalue) == 0:
				snipSetKeys = sorted(snipSetKeys, key=lambda snipSetKeys: order.index(snipSetKeys))  


			fsnptCount = 0
			if obj['knowledge_panel']:
				snipSetKeys.insert(0, 'knw')
			if obj['featured_snippet']:
				fs_status = "fs1" if 'featured_box' in obj['snippets_details'] and obj['snippets_details']['featured_box']['status'] == "yes" else "fs0"
				snipSetKeys.insert(0, fs_status)
			if obj['ads'] != False:
				if 'ads' in obj['snippets_details']:
					if obj['snippets_details']['ads']['status'] == "yes":
						ad = "Ain"
					elif int(obj['snippets_details']['ads']['top_count']) > 0 and obj['snippets_details']['ads']['bottom_count'] > 0:
						ad = "Atb"
					elif int(obj['snippets_details']['ads']['top_count']) > 0:
						ad = "At"
					elif int(obj['snippets_details']['ads']['bottom_count']) > 0:
						ad = "Ab"
					else:
						ad = obj['ads']
				else:
					ad = obj['ads']

				snipSetKeys.insert(0, ad)
			if obj['review']:
				snipSetKeys.insert(0, "rv")

			superData['sp'] = snipSetKeys
			superData['trg'] = obj['total_rating']

			if 'dn' in self.context and obj['ranknow'] == 0:
				superData['SR'] = self.context['dn'] 
			else:
				superData['SR'] = obj['cp_site_url']


			# Svolume or Comp
			svolData = keywordVolume.objects.filter(fk_keyword_id=obj['fk_keyword_id']).values('month_wise_volume','past_months').first()
			# svolData = None
			
			if svolData != None:
				superData['SV'] = svolData['month_wise_volume'][-1] if len(svolData['month_wise_volume']) > 1 else '-1' 
				superData['PSV'] = svolData['month_wise_volume'][-2] if len(svolData['month_wise_volume']) > 1 else '0' 
				SVMY = svolData['past_months'][-1] if len(svolData['past_months']) > 1 else '' 
				superData['SVM'] = SVMY.split(" ", 1)[0].capitalize()
				PSVMY = svolData['past_months'][-2] if len(svolData['past_months']) > 1 else ''
				superData['PSVM'] = PSVMY.split(" ", 1)[0].capitalize() 
			else:
				# superData['SV'] = obj['search_volume'] if obj['search_volume'] != '-' else '-1'
				superData['SV'] = '-1'
				superData['PSV'] = '0'
				superData['SVM'] = ''
				superData['PSVM'] = ''

			
			#keyword (Hold)
			# superData['RG'] = obj['region']
			# superData['CY'] = obj['location'].split("(")[1].replace(')', '').strip() if "(" in obj['location'] else "-"
			# superData['lng'] = obj['language']
			# superData['srs'] = obj['search_results']

			superData['io'] = obj['isocode']
			superData['PM'] = "D" if obj['platform'] == "desktop" else "M"

			return superData
		else:
			return None

# competitor Project Overview details
class compProjectOverviewSerializer(serializers.Serializer):
	# xcount = 0

	def to_representation(self, obj):
		superData = self.context["superData"]
		# kwIns = self.context["kwIns"]
		xcount = self.context["xcount"]

		# Rating
		rating = isfloat_isdigit(obj['total_rating'])
		if rating and rating > 0:
			superData[xcount+'rv'] += 1

		# Serp Features
		if obj['featured_snippet'] and 'featured_box' in obj['snippets_details'] and obj['snippets_details']['featured_box']['status'] != "no":
			superData[xcount+'sn'] += 1


		# Google Search Ads
		if obj['ads'] and 'ads' in obj['snippets_details']:
			if obj['snippets_details']['ads']['status'] == "yes":
				superData[xcount+'ad'] += 1
		
		# # Main kw Rating
		# xcount = int(xcount)+1
		# mainrating = isfloat_isdigit(kwIns[xcount]['total_rating'])
		# if mainrating and mainrating > 0:
		# 	superData['mrv'] += 1

		# # Main kw Serp Features
		# if kwIns[xcount]['featured_snippet'] and 'featured_box' in kwIns[xcount]['snippets_details'] and kwIns[xcount]['snippets_details']['featured_box']['status'] != "no":
		# 	superData['msn'] += 1


		# # Main kw Google Search Ads
		# if kwIns[xcount]['ads'] and 'ads' in kwIns[xcount]['snippets_details']:
		# 	if kwIns[xcount]['snippets_details']['ads']['status'] == "yes":
		# 		superData['mad'] += 1

		return superData













# class DashHomeSerializer(serializers.ModelSerializer):
# 	G_N = serializers.SerializerMethodField('get_G_N')
# 	D_N = serializers.SerializerMethodField('get_D_N')
# 	GY = serializers.SerializerMethodField('get_GY')
# 	class Meta: 
# 		model = Groups
# 		fields = ('GY','G_N', 'D_N')

# 	def get_G_N(self, obj):
# 		return obj.group_name

# 	def get_D_N(self, obj):
# 		return obj.domain_name

# 	def get_GY(self, obj):
# 		else:
# 			gid = obj.id
# 		return gid

# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj) 
		
# 		superData['dn_d'] = obj.domain_info
# 		superData['dn_s'] = obj.domain_status

# 		# Group Based Keywords
# 		superData['kw_ln'] = Keyword.objects.filter(fk_group_id=obj.id,fk_user_id=obj.fk_user_id).count()

# 		superData['ss'] = f_to_i(obj.score_meter[0]) if len(obj.score_meter) > 0 else 0
# 		superData['yss'] = f_to_i(obj.score_meter[1]) if len(obj.score_meter) > 1 else superData['ss']
# 		superData['bss'] = f_to_i(obj.top_score) if obj.top_score else -1
		
# 		# superData['fp'] = int(obj.since_position[0].split(',')[0]) if len(obj.since_position) > 0 else 0
# 		# superData['yfp'] = int(obj.since_position[1].split(',')[0]) if len(obj.since_position) > 1 else 0

# 		# activityGroupData = list(map(str, obj.activity_level[1].split('|'))) if len(obj.activity_level) > 1 else [0,0,0]
# 		# if len(activityGroupData) == 3:
# 		#     superData['yik'] = int(activityGroupData[1])
# 		#     superData['ydk'] = int(activityGroupData[2])
# 		# else:
# 		#     superData['yik'] = 0
# 		#     superData['ydk'] = 0
		
# 		# superData['ik'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="up").count()
# 		# superData['dk'] = Keyword.objects.filter(fk_group_id=obj.id, daymark="down").count()


# 		grpLimit = obj.activity_level[0:7] if len(obj.activity_level) > 7 else obj.activity_level[0:len(obj.activity_level)] 
# 		grpFirstPos = obj.since_position[0:7] if len(obj.since_position) > 7 else obj.since_position[0:len(obj.since_position)] 
# 		improved = []
# 		declined = []
# 		firstPos = []

# 		for i in reversed(range(len(grpLimit))):
# 		    activityGroupData = list(map(str, grpLimit[i].split('|')))
# 		    if len(activityGroupData) == 3:
# 		        improved.insert(0, str(activityGroupData[1]))
# 		        declined.insert(0, str(activityGroupData[2])) 
# 		    else:
# 		        improved.insert(0, str("0"))
# 		        declined.insert(0, str("0"))

# 		    if len(grpFirstPos) > i:
# 		    	firstPos.insert(0, str(grpFirstPos[i].split(',')[0]))
# 		    else:
# 		        firstPos.insert(0, str("0"))

# 		crawlkwCount = Keyword.objects.filter(fk_user_id=obj.fk_user_id, fk_group_id=obj.id, manual_call_status__in=[True]).count()
# 		# mrKey = "off"  
# 		# if crawlkwCount > 0:
# 		#     mrKey = "onk"
# 		# else:
# 		#     svCount = Keyword.objects.filter(fk_user_id=userid, fk_group_id=grpid, search_volume="init").count()
# 		#     mrKey = "onv" if svCount > 0 else "off"


# 		# superData['mrk'] = mrKey
# 		superData['mrk'] = 1 if crawlkwCount > 0 else 0
# 		superData['ikw'] = improved
# 		superData['dkw'] = declined
# 		superData['fpk'] = firstPos


# 		return  superData

# class DashKeywordSerializer(serializers.Serializer):
# 	# KW = serializers.SerializerMethodField('get_keyword')
# 	# fv = serializers.SerializerMethodField('get_fav')
# 	# class Meta:
# 	# 	model = Keyword
# 	# 	fields = ('KW', 'fv')

# 	# def get_keyword(self, obj):
# 	# 	return obj.keyword

# 	# def get_fav(self, obj):
# 	# 	return obj.favour

# 	def to_representation(self, obj):
# 		# prefixConst = 98765
# 		# prefixConst = DEF_SETTINGS.UNIQUE_KEYWORD_ID
# 		prefixConst = 0 
# 		global comp_levels
# 		global this_week_day
# 		superData = super().to_representation(obj) 

# 		#common
# 		superData['KW'] = obj['keyword']
# 		superData['fv'] = obj['favour']

# 		superData['key'] = prefixConst + int(obj['id'])
# 		superData['RK'] = obj['rank'][0:2] if this_week_day < 2 else obj['rank'][0:this_week_day]
# 		superData['RW'] = obj['ranknow'] if obj['ranknow'] != 0 else 101
# 		superData['lrd'] = obj['lastranked_date'].date()
# 		superData['t_c'] = len(obj['rank'])
# 		#create date
# 		superData['cd']= obj['created_date'].strftime('%Y-%m-%d')
# 		superData['lrupt'] = timeDifference(obj['lastranked_date'], "off")

# 		#Action
# 		# superData['CR'] = obj.page_uuid_url
# 		superData['CR'] = ""

# 		#Best rank
# 		superData['brnk'] = int(obj['top_rank'])

# 		#1D
# 		superData['OD'] = obj['dayval'] if obj['daymark'] != "down" else -abs(int(obj['dayval']))
# 		#7D
# 		superData['SD'] = obj['weekval'] if obj['weekmark'] != "down" else -abs(int(obj['weekval']))
# 		#15D
# 		superData['XD'] = obj['halfmonthval'] if obj['halfmonthmark'] != "down" else -abs(int(obj['halfmonthval']))

# 		#Features
# 		sniptkys = set(obj['snippets_details'].keys())
# 		if len(sniptkys):
# 			rmvSniptkys = {'featured_box','ads','knowledge_box','current'}
# 			sniptkys = sniptkys-rmvSniptkys 

# 		order = ['slrs','twrs','lcrs','imrs','vdrs','nwrs','rqrs','mprs']
# 		ordervalue = list(sniptkys - set(order))  
# 		snipSetKeys = list(sniptkys)
# 		if len(ordervalue) == 0:
# 			snipSetKeys = sorted(snipSetKeys, key=lambda snipSetKeys: order.index(snipSetKeys))  


# 		fsnptCount = 0
# 		if obj['knowledge_panel']:
# 			snipSetKeys.insert(0, 'knw')
# 		if obj['featured_snippet']:
# 			fs_status = "fs1" if 'featured_box' in obj['snippets_details'] and obj['snippets_details']['featured_box']['status'] == "yes" else "fs0"
# 			snipSetKeys.insert(0, fs_status)
# 		if obj['ads'] != False:
# 			if 'ads' in obj['snippets_details']:
# 				if obj['snippets_details']['ads']['status'] == "yes":
# 					ad = "Ain"
# 				elif int(obj['snippets_details']['ads']['top_count']) > 0 and obj['snippets_details']['ads']['bottom_count'] > 0:
# 					ad = "Atb"
# 				elif int(obj['snippets_details']['ads']['top_count']) > 0:
# 					ad = "At"
# 				elif int(obj['snippets_details']['ads']['bottom_count']) > 0:
# 					ad = "Ab"
# 				else:
# 					ad = obj['ads']
# 			else:
# 				ad = obj['ads']

# 			snipSetKeys.insert(0, ad)
# 		if obj['review']:
# 			snipSetKeys.insert(0, "rv")

# 		superData['sp'] = snipSetKeys
# 		superData['trg'] = obj['total_rating']

		
# 		# Svolume or Comp
# 		svolData = keywordVolume.objects.filter(fk_keyword_id=obj['id']).values('month_wise_volume','past_months').first()
# 		# svolData = None
		
# 		if svolData != None:
# 			superData['SV'] = svolData['month_wise_volume'][-1] if len(svolData['month_wise_volume']) > 1 else '-1' 
# 			superData['PSV'] = svolData['month_wise_volume'][-2] if len(svolData['month_wise_volume']) > 1 else '0' 
# 			SVMY = svolData['past_months'][-1] if len(svolData['past_months']) > 1 else '' 
# 			superData['SVM'] = SVMY.split(" ", 1)[0].capitalize()
# 			PSVMY = svolData['past_months'][-2] if len(svolData['past_months']) > 1 else ''
# 			superData['PSVM'] = PSVMY.split(" ", 1)[0].capitalize() 
# 		else:
# 			superData['SV'] = obj['search_volume'] if obj['search_volume'] != '-' else '-1'
# 			superData['PSV'] = '0'
# 			superData['SVM'] = ''
# 			superData['PSVM'] = ''

		
# 		#URL
# 		superData['edm'] = obj['exactdomain']
# 		if 'dn' in self.context and obj['ranknow'] == 0:
# 			superData['SR'] = self.context['dn'] 
# 		else:
# 			superData['SR'] = obj['site_url']
		

# 		#Tag
# 		superData['tg'] = obj['tags']

# 		#keyword
# 		superData['RG'] = obj['region']
# 		superData['CY'] = obj['location'].split("(")[1].replace(')', '').strip() if "(" in obj['location'] else "-"
# 		superData['lng'] = obj['language']
# 		superData['srs'] = obj['search_results']
# 		superData['io'] = obj['isocode']
# 		superData['PM'] = "D" if obj['platform'] == "desktop" else "M"
# 		superData['kwas'] = obj['keyword_alias']
# 		superData['cnn'] = True if len(obj['cannibalisation']) > 1 else False

# 		return superData

# # APP HOME AREA
# class AppHomeSerializer(serializers.Serializer):

# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj)
		
# 		localUserId = obj

# 		superData['sb_s'] = ""
# 		superData['sb_s'] = ""
# 		superData['sO_R'] = 0
# 		superData['uTY'] = "free"


# 		userGroups = Groups.objects.filter(fk_user=localUserId).all()
# 		groupalldata = AppGroupSerializer(userGroups, many=True).data
# 		superData['uPL'] = len(groupalldata)
# 		UserSttgdata = Usersettings.objects.filter(fb_user_id=localUserId).first()
# 		superData['slt'] = groupalldata
# 		# dashview = {}
# 		# for gdata in groupalldata:
# 		# 	dashview[gdata['GY']] = gdata['d_v']

# 		# superData['gpv'] = dashview
# 		accIns = Accountusage.objects.filter(fb_user_id=localUserId)
# 		accData = accIns.first()
		
# 		if accIns.exists() and accData.user_type == "trial" and accData.trial_days == 0:
# 			GrpkeyIns = Keyword.objects.filter(fk_user_id=localUserId)
# 			usageCount = 0
			
# 			if GrpkeyIns.exists():
# 				usageCount = GrpkeyIns.count()
# 				accupdate = accIns.update(last_used_refresh_count = usageCount, used_refresh_limit = 0, user_type="free", status="default", modified_date = datetime.now())
# 				keywords = GrpkeyIns.update(manual_call_status=1)

# 				if usageCount > 0:
# 					groupRefreshUpdate = Groups.objects.filter(fk_user_id=localUserId).update(strict_refresh_switch=True, manual_grp_trigger="INIT", last_used_refresh_count=usageCount)

# 					refreshIns = Refreshmanual.objects.filter(fb_user_id=localUserId)
# 					if refreshIns.exists():
# 					    refreshIns.update(refresh_status = "start", refresh_type = "manual")

# 		accData = Accountusage.objects.filter(fb_user_id=localUserId).first()
# 		if accData:
# 			superData['pPL'] = accData.plan_project_limit if accData else 1 
# 			superData['sb_s'], superData['sO_R'] = userPaymode(localUserId, accData)
# 			superData['uTY'] = accData.user_type 

# 		return superData

# # menu_details, baseauth for apphome, report, setting.js  
# class AppGroupSerializer(serializers.ModelSerializer):
# 	NM = serializers.SerializerMethodField('get_NM') 
# 	GY = serializers.SerializerMethodField('get_GY') 
# 	class Meta: 
# 		model = Groups
# 		fields = ('GY', 'NM')

# 	def get_NM(self, obj):
# 		return obj.group_name

# 	def get_GY(self, obj):
# 		else:
# 			gid = obj.id
# 		return gid

# 	def to_representation(self, obj):
# 		superData = super().to_representation(obj)
# 		superData['kw_c'] = Keyword.objects.filter(fk_group=int(obj.id),fk_user=int(obj.fk_user_id)).count()
# 		gridview = obj.grid_sort[0].upper()
# 		superData['d_v'] = 'G~'+gridview if obj.dashboard_view == 'gridview' else 'L~'+gridview
# 		# superData['d_v'] = 'G' if obj.dashboard_view == 'gridview' else 'L'
# 		superData['DN'] = obj.domain_name
# 		grpsttgIns = GroupSetting.objects.filter(fk_user=int(obj.fk_user_id), fk_group=int(obj.id)).first()
# 		superData['OV'] = grpsttgIns.overview_switch if grpsttgIns else True
# 		superData['W'] = grpsttgIns.widget_handle if grpsttgIns else []
		

# 		refreshData = Refreshmanual.objects.filter(fb_user_id=int(obj.fk_user_id),fk_group_id=int(obj.id)).values('refresh_time').first()
# 		superData['rf_t'] = timeDifference(refreshData['refresh_time'], "off") if 'refresh_time' in refreshData else timeDifference(obj.updated_date, "off")
# 		# superData['rf_t'] = rf_time.split("(", 1)[0].strip()

# 		return superData 


# class RegionFltrSerializer(serializers.ModelSerializer):
# 	Rcd = serializers.SerializerMethodField('get_Rcd')
# 	RN = serializers.SerializerMethodField('get_RN')
# 	Rcnt = serializers.SerializerMethodField('get_Rcnt')
# 	class Meta: 
# 		model = Region
# 		fields = ('Rcd', 'RN', 'Rcnt')

# 	def get_Rcd(self, obj):
# 		return obj.region_code

# 	def get_RN(self, obj):
# 		return obj.region_name

# 	def get_Rcnt(self, obj):
# 		return obj.region_country
