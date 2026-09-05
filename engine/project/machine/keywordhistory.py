from django.shortcuts import render
from django.conf import settings

from project.machine.models import Keyword, Group, KeywordHistory 

from urllib.parse import urlparse 
from datetime import datetime, date
from project.machine import parser 

# Url check starts
def checkUrlAlteration(newUrl, prevUrl, kid, liveRank, lastRating, newRating):
	domain_identity = None
	protocol_status = None
	ssl_options = None 

	# ssl_options, protocol_status, domain_identity = check_domain_protocol(newUrl, prevUrl)
	
	singleKeywordHistory = KeywordHistory.objects.filter(fk_keyword_id=kid)
	if singleKeywordHistory: 
		keyValues = singleKeywordHistory[0] 
		topRating = keyValues.top_ratings
		ratingChangeStaus = False
		
		if lastRating != "-" and newRating != "-" and lastRating != "": 
			ratingChangeStaus =  True if float(newRating) != float(lastRating) else False
		elif lastRating == "-" and newRating != "-" and lastRating != "":  
			ratingChangeStaus =  True
		elif lastRating != "-" and newRating == "-" and lastRating != "": 
			ratingChangeStaus =  True
		elif lastRating == "" and newRating != "-":  
			ratingChangeStaus =  True 
		else: 
			ratingChangeStaus =  False

		if topRating != "-" and newRating !="-": 
			topRating = str(newRating) if float(newRating) > float(topRating) else str(keyValues.top_ratings)
		elif topRating == "-" and newRating !="-": 
			topRating = str(newRating) 

		url_update = { 
			# 'ssl' : ssl_options, 
			# 'protocol_status' : protocol_status,
			# 'domain_identity': domain_identity,
			'ssl': None,
			'last_url': prevUrl, 
			'new_url': newUrl,   
			'last_rating': str(lastRating),
			'new_rating': str(newRating), 
			'date' : date.today().strftime("%b %d, %Y"),  
		}

		if ratingChangeStaus == True: 
			singleKeywordHistory.update( 
				other_history=url_update,
				top_ratings=topRating, 
				url_status=domain_identity,
				ratings_changed_date=datetime.now()
			)
		else:
		  	singleKeywordHistory.update( 
				other_history=url_update,
				top_ratings=topRating, 
				url_status=domain_identity,
				ratings_changed_date=None 
			)
	return True 

def extract_domain_protocol(uri, www=True):
	domain_name = f"{uri.netloc}"
	domain_slug = f"{uri.path}"
	if www == False:
		domain_name = f"{uri.netloc}".replace("www.", "")

	if not uri.netloc: 
		domainDivision = f"{uri.path}".split('/')
		domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision    
		domain_slug = domainDivision[1] if len(domainDivision) > 1 else None    
	
	scheme = "%s://" % uri.scheme
	url_wo_scheme = uri.geturl().replace(scheme, '', 1).rstrip("/")
	
	return domain_name, domain_slug, url_wo_scheme

def check_domain_protocol(newUrl, prevUrl):  
	# Previous Url
	prevUri = urlparse(prevUrl)
	prevScheme = ("%s" % prevUri.scheme).strip() 

	# New Url
	newUri = urlparse(newUrl)
	newScheme = ("%s" % newUri.scheme).strip() 

	# SSL Checking (HTTPS or HTTP)
	protocol_status, ssl_options, domain_identity = None, None, None

	if prevScheme == "http" and newScheme == "https":
		protocol_status, ssl_options = "upgrade", "https"
	elif prevScheme == "https" and newScheme == "http":
		protocol_status, ssl_options = "downgrade", "http"
	elif prevScheme ==  "" and (newScheme == "https" or newScheme == "http"):  
		protocol_status, ssl_options = "normal", newScheme 
	elif prevScheme == newScheme:
		protocol_status, ssl_options = "normal", newScheme

	# domain_name, domain_slug, url_wo_scheme = extract_domain_protocol(prevUri)

	
	if str(newUrl.rstrip("/")) != str(prevUrl.rstrip("/")): 
		domain_identity = "UNQ"
	elif str(newUrl.rstrip("/")) == str(prevUrl.rstrip("/")): 
		domain_identity = "CMN" 

	return ssl_options, protocol_status, domain_identity 


# Url check ends

def snippetsHistory(argParams, argKid, argTarget, argFlag, argComp):
	singleKeywordHistory = KeywordHistory.objects.filter(fk_keyword_id=argKid)

	if singleKeywordHistory: 
		keyValues = singleKeywordHistory[0]  
		# COMPETITOR UPDATE STARTS
		singleKeywordHistory.update(
			comp_today = argComp
		)
		# COMPETITOR UPDATE ENDS

		# Featured History 
		featured_history = keyValues['featured_snippet_history']
		featured_domain = keyValues['featured_snippet_url_list']
		featured_today_domain_list = ""
		featured_flag = False 

		if 'featured_box' in argParams:
			if 'link' in argParams['featured_box']:
				f_domain = parser.extract_domain(argParams['featured_box']['link']).strip()

				if f_domain not in featured_domain:
					featured_domain.insert(0,str(f_domain))
					featured_today_domain_list = f_domain 
				else:
					featured_domain.sort(key=f_domain.__ne__) 

				if 'status' in featured_history:
					featured_history['status'] = argParams['featured_box']['status']
				else:
					featured_history.update({
						'status': argParams['featured_box']['status']
					}) 

				if 'recent' in featured_history:
					featured_history['recent'] = featured_today_domain_list
				else:
					featured_history.update({
						'recent': featured_today_domain_list
					}) 

				if 'list' not in featured_history: 
					featured_history.update({
						'list': {}
					})

				if 'list' in featured_history:
					featured_history['list'].update({
						f_domain : {
							'link': argParams['featured_box']['link'],
							'title': argParams['featured_box']['title'],
							'desc': argParams['featured_box']['desc'],
							'date': str(datetime.now()), 
							# 'date': date.today().strftime("%b %d, %Y"), 
						} 
					})

				featured_flag = True
				if featured_today_domain_list == "":
					singleKeywordHistory.update( 
						featured_snippet_url_list=featured_domain,
						featured_snippet_history=featured_history,
						new_featured_snippet_date=None 
					) 
				else: 
					singleKeywordHistory.update( 
						featured_snippet_url_list=featured_domain,
						featured_snippet_history=featured_history,
						new_featured_snippet_date=datetime.now()
					)

		# Ads History 
		ads_history = keyValues['ad_snippet_history']
		ads_domain = keyValues['ad_snippet_url_list']
		ads_today_domain_list = [] 
		ads_flag = False 

		if 'ads' in argParams: 
			ads_recent = {}

			if 'status' in ads_history:
				ads_history['status'] = argParams['ads']['status']
			else:
				ads_history.update({
					'status': argParams['ads']['status']
				})

			if 'top_result' in argParams['ads']:
				for sub in argParams['ads']['top_result']:
					if "link" in sub:
						a_domain = parser.extract_domain(sub['link']).strip()
						if (a_domain not in ads_domain) and len(a_domain) > 0:  
							ads_domain.insert(0,str(a_domain))
							ads_today_domain_list.insert(0, str(a_domain))
						else:
							ads_domain.sort(key=a_domain.__ne__) 

						ads_recent.update({
							a_domain : {
								'lk': sub['link'] if 'link' in sub else "-", 
								# 'tt': sub['title'] if 'title' in sub else "-",
								'ps': "11" if argTarget == a_domain else "10",
								'dt': str(datetime.now()),
							}
						})
						
			if 'bottom_result' in argParams['ads']:
				for sub in argParams['ads']['bottom_result']:
					if "link" in sub:
						a_domain = parser.extract_domain(sub['link']).strip()
						if (a_domain not in ads_domain) and len(a_domain) > 0:
							ads_domain.insert(0,str(a_domain))
							ads_today_domain_list.insert(0, str(a_domain))
						else:
							ads_domain.sort(key=a_domain.__ne__)

						ads_recent.update({
							a_domain : {
								'lk': sub['link'] if 'link' in sub else "-", 
								# 'tt': sub['title'] if 'title' in sub else "-",
								'ps': "11" if argTarget == a_domain else "01", 
								'dt': str(datetime.now()),
							}
						})

			# Ads whose placement the provider did not report.  The JSON SERP
			# API returns one flat `ads` array with a position but no
			# above/below-the-fold marker, so these are the normal case, not an
			# edge one.  They are still real ads by real domains and belong in
			# the history; what is unknown is only WHERE they sat, and 'ps' says
			# so with "00" rather than borrowing "10" and publishing a guess.
			if 'unknown_result' in argParams['ads']:
				for sub in argParams['ads']['unknown_result']:
					if "link" in sub:
						a_domain = parser.extract_domain(sub['link']).strip()
						if (a_domain not in ads_domain) and len(a_domain) > 0:
							ads_domain.insert(0,str(a_domain))
							ads_today_domain_list.insert(0, str(a_domain))
						else:
							ads_domain.sort(key=a_domain.__ne__)

						ads_recent.update({
							a_domain : {
								'lk': sub['link'] if 'link' in sub else "-", 
								'ps': "11" if argTarget == a_domain else "00", 
								'dt': str(datetime.now()),
							}
						})

			if 'list' not in ads_history or argFlag == True: 
				ads_history.update({
					'list': {}
				})

			if 'list' in ads_history and len(ads_recent):  
				ads_order = {**ads_recent, **{**ads_history['list'], **ads_recent}}
				if argTarget in ads_order:
					active_domain = {
						argTarget: ads_order[argTarget] 
					}
					ads_order = {**active_domain, **ads_order} 
				ads_history['list'] = ads_order

			if 'recent' in ads_history:
				ads_history['recent'] = ads_today_domain_list
			else:
				ads_history.update({
					'recent': ads_today_domain_list 
				})

			ads_flag = True
			if len(ads_today_domain_list) == 0:
				singleKeywordHistory.update( 
					ad_snippet_url_list=ads_domain,
					ad_snippet_history=ads_history, 
					new_ad_snippet_date=None 
				)
			else:
				singleKeywordHistory.update( 
					ad_snippet_url_list=ads_domain,
					ad_snippet_history=ads_history,
					new_ad_snippet_date=datetime.now()
				)

		# elif argFlag == True and 'list' in ads_history: 
		elif argFlag == True: 
			ads_history.update({
				'list': {}
			})
			singleKeywordHistory.update(
				ad_snippet_history=ads_history
			)
				
		if featured_flag == False and ads_flag == False:
			singleKeywordHistory.update(
				new_ad_snippet_date=None,
				new_featured_snippet_date=None
			)
		else: 
			if ads_flag == False:
				singleKeywordHistory.update(
					new_ad_snippet_date=None
				)

			if featured_flag == False:
				singleKeywordHistory.update(
					new_featured_snippet_date=None 
				) 

	return True 
