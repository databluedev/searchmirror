from django.shortcuts import render
from django.conf import settings

from rest_framework_mongoengine import viewsets as meviewsets

from project.machine.models import BrandTracker, Keyword, Group, ManualRefresh, Mainsettings 

import requests, json, time, csv
from bs4 import BeautifulSoup
from urllib import parse 
import sys, os, random 
from datetime import datetime, date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse

from urllib.parse import urlparse 
from threading import Timer

from project.machine import watchdog, formulate, centralised, encryption 
from project.machine import automation_common as _at__common_

from unidecode import unidecode as _u__dcode_
import re 

def trim(value):
    return value.strip()

def cleanMe(soup, lang):
	_bot__clean_ = _at__common_.__bot_clean__(lang)

	for tag in soup.find_all(True): 
		tExtract = True
		if len(tag.findChildren(recursive=True)) != 0 or len(tag.text) != 0:
			if tag.has_attr("id"):
				tId = tag.get("id")
				if tId:
					if tId in ["searchform", "top_nav"]:
						tExtract = False

			# if tag.has_attr("role"):
			# 	tRole = tag.get("role") 
			# 	if tRole: 
			# 		if tRole in ["navigation", "contentinfo"]:
			# 			tExtract = False

			if tExtract == False: 
				tag.decompose() 
			# else: 	
			# 	# tag.attrs = {} # REMOVE ALL ATTRIBUTES IN TAG 
			# 	attrs = dict(tag.attrs)
			# 	for attr in attrs:
			# 		if tag.name != "html" and attr not in ["id", "class", "role", "href", "src", "data-src", "alt", "height", "width", "data-rw"]:
			# 			del tag[attr]

		#"head", "style", - Super Page Remove from list
		# if tag.name in ["script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]: 
		if tag.name in ["head", "style", "script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]:
			tag.extract()

		# if tag.text.replace(' ','_').lower() in _bot__clean_:
		# 	tag.extract() 

	for tag in soup.find_all(True):
		if tag.name in ["head", "w-debug-content", "g-right-button", "g-left-button", "title-with-lhs-icon", "g-section-with-header", "g-inner-card", "g-scrolling-carousel", "g-image-section", "g-link", "g-img"] and len(tag.findChildren(recursive=True)) == 0 and len(tag.text) == 0: 
			tag.extract()  

	return soup 

def FindUrlFromString(stringUrl):
	validateUrlRegex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
	url = re.findall(validateUrlRegex,stringUrl)      
	return [x[0] for x in url] 

def extract_domain(url, remove_http=True):
	uri = urlparse(url)
	if remove_http:
		# domain_name = f"{uri.netloc}".replace("www.", "")
		if uri.netloc: 
			domain_name = f"{uri.netloc}".replace("www.", "") 
		else:
			domainDivision = f"{uri.path}".replace("www.", "").split('/')
			domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision    
	else:
		domain_name = f"{uri.netloc}".replace("www.", "")

	return domain_name

def exact_url_scheme(url):  
	parsed = urlparse(url)
	scheme = "%s://" % parsed.scheme
	return parsed.geturl().replace(scheme, '', 1).rstrip("/")   

def engineBrandParseData(engineMode, soupdata, postdata):  
	
	keyWord = postdata['keyword'].lower()
	region = postdata['se_name'].lower() 
	lang = postdata['language']
	brand_id = postdata['id']
	brand_ads_domain = postdata['url_list']
	brand_ads_today_list = [] 

	_bot__language_ = _at__common_.__bot_language__(lang) 

	if soupdata and engineMode == "BRAND":
		soup = cleanMe(soupdata, lang)
		targetLink = extract_domain(postdata['target']) 
		singleBrandTracker = BrandTracker.objects.filter(__raw__= {'id': brand_id}) 

		gAdLinks = soup.find_all(['h1', 'h2']) 

		for gAdLink in gAdLinks:
			headerTagText = gAdLink.text.replace(' ','_').lower()

			# ADS
			if headerTagText == _bot__language_['_ads_']:
				children = gAdLink.parent.findChildren(recursive=False)  
				for child in children:

					gSnipAnchors = child.find('a')
					if gSnipAnchors: 
						a_domain = None
						if gSnipAnchors.has_attr('href'):
							adSingleLink = gSnipAnchors.attrs.get("href")
							e_domain = extract_domain(adSingleLink).strip()
							a_domain = None if e_domain == "" or e_domain == None else e_domain
						
						if a_domain == None and gSnipAnchors.has_attr('data-rw'):
							adSingleLink = gSnipAnchors.attrs.get("data-rw")
							a_domain = extract_domain(adSingleLink).strip()

						if (a_domain not in brand_ads_domain) and len(a_domain) > 0:
							brand_ads_domain.insert(0,str(a_domain))
							if adSingleLink.find(targetLink) == -1:
								brand_ads_today_list.insert(0, str(a_domain))
						elif len(a_domain) > 0: 
							brand_ads_domain.sort(key=a_domain.__ne__)

		if len(brand_ads_today_list):
			singleBrandTracker.update(
				conquestor_recent_list =  brand_ads_today_list,
				conquestor_url_list = brand_ads_domain,
				conquestor_recent_date = datetime.now(),
				modified_date = datetime.now()
			)
		else:
			singleBrandTracker.update( 
				conquestor_recent_list =  [], 
				conquestor_url_list = brand_ads_domain,
				modified_date = datetime.now()
			) 
	return 1

# NEW STRUCTURE 
def parseAds(centerdata, target):
    adsList = list()
    adexist = 0
    adSingleLink = None

    try:
        children = centerdata.parent.findChildren("div", class_="uEierd", recursive=False)
        for child in children:
            adsContent = {}
            gSnipAnchors = child.find('a')
            if gSnipAnchors: 
                a_domain = None
                if gSnipAnchors.has_attr('data-pcu'):
                    gSnipAnchorsCollection = gSnipAnchors.attrs.get("data-pcu")
                    if gSnipAnchorsCollection:
                        gSnipAnchorsLink = gSnipAnchorsCollection.split(",")
                        if len(gSnipAnchorsLink):
                            adSingleLink = gSnipAnchorsLink[0]
                            e_domain = extract_domain(adSingleLink).strip()
                            a_domain = None if e_domain == "" or e_domain == None else e_domain

                if a_domain == None:
                    parseExtract = list()
                    citeBlock = gSnipAnchors.find(attrs={'role': "text"})
                    if citeBlock:
                        for cLink in citeBlock:
                            if cLink.name is None:
                                parseExtract.append(cLink)
                            else:
                                parseExtract.append(cLink.get_text())

                    if len(parseExtract) == 0:
                        parseExtract = FindUrlFromString(gSnipAnchors.text)
                        adSingleLink = parseExtract[0] if len(parseExtract) else None
                    else:
                        adSingleLink = ''.join(parseExtract).strip()

                if adexist == 0 and adSingleLink:
                    if adSingleLink.find(target) > -1:  
                        adexist = 1

                if adSingleLink:
                    adsContent.update({"link": adSingleLink})  
                    AdText = gSnipAnchors.find(attrs={"aria-level": "3", "role":"heading"}) 
                    if AdText:
                        adsContent.update({"title": AdText.text}) 
                    else:
                        adsContent.update({"title": ""})

            if adsContent:
                adsList.append(adsContent)
    except Exception as e:
        # Update to exception log
        pass
        
    return adsList, adexist

def topAds(bsoup, btarget):
    top_ad_container = bsoup.find('div', attrs={"id": "tads", "role":"region"})
    if top_ad_container:
        top_header_container = top_ad_container.find('h1')
        if top_header_container:
            return parseAds(top_header_container, btarget)

    return list(), 0

def bottomAds(bsoup, btarget):
    bottom_ad_container = bsoup.find('div', attrs={"id": "bottomads"})
    if bottom_ad_container:
        bottom_header_container = bottom_ad_container.find('h1')
        if bottom_header_container:
            return parseAds(bottom_header_container, btarget)
    
    return list(), 0

def domain_competitors(domains, rank, per_list):
    top = before = after = list()

    if len(domains): 
        top = domains[:per_list]
        kw_rank = rank
        if rank: 
            rank = rank if rank < 1 else rank - 1
            domain_key_min = 0 if kw_rank < per_list else (rank - per_list) + 1
            if kw_rank >= 1:
                before = domains[domain_key_min:kw_rank]

            after = domains[rank:(rank + per_list)]
    
    compValue = {
        "tp": top,
        "bf": before,
        "ar": after
    }
    return compValue
    
def get_cite(block):
    citeLink = []
    citeBlock = block.find('cite')
    if citeBlock:
        for cLink in citeBlock:
            if cLink.name is None:
                citeLink.append(cLink)
            else:
                citeLink.append(cLink.get_text())

    return citeLink 

def get_title(block):
    try:
        titleBlock = block.get_text()
        return titleBlock if len(titleBlock) else "" 
    except Exception as e: 
        pass

    return "" 

def get_desc(block, flag):
    try:
        if flag == "block":
            descBlock = block.find('div', class_= "VwiC3b")
            if descBlock: 
                return [descBlock.get_text()]

            descBlock = block.find('div', attrs={'data-snf': 'nke7rc'}) 
            if descBlock:
                descContent = descBlock.get_text()
                if descContent:
                    return [descContent.strip()]

            descBlock = block.find('div', attrs={'data-content-feature': '1'})
            if descBlock:
                descContent = descBlock.get_text()
                if descContent:
                    return [descContent.strip()]

            descBlock = block.find('div', attrs={'data-content-feature': '2'})
            if descBlock:
                descContent = descBlock.get_text()
                if descContent:
                    return [descContent.strip()]

            descBlock = block.find('div', class_= "IsZvec")
            if descBlock: 
                descBlock = descBlock.find('div')
                if descBlock: 
                    return [descBlock.get_text()]

            descBlock = block.find('div', class_= "Uroaid")
            if descBlock:
                descBlock = descBlock.parent.findChildren(recursive=False)
                if descBlock:
                    videoDesc = []
                    for dsc in descBlock:
                        videoDesc.append(dsc.get_text()) 
                    return videoDesc
                    
        elif flag == "featured":
            descBlock = block.find("div", attrs={'role': True, 'aria-level': "3"})
            if descBlock:
                tag = descBlock.find('g-bubble') 
                if tag:
                    tags = tag.find('div')
                    if tags: 
                        tags.decompose()

            if descBlock:
                return [descBlock.get_text()]
        else:
            pass
            
    except Exception as e: 
        pass

    return []

def _nTd_(_num_):
    # Transliterate the number into ASCII characters
    return float(_u__dcode_(_num_))

def _is__float_(_str_):
    __pattern_cde__ = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
    return re.match(__pattern_cde__, _str_) is not None 

def get_rating(block): 
    try: 
        ratingContent = 0
        reviewsContent = 0
        reviewsText = "" 

        _top__cluster_ = block.find("div", class_='fG8Fp')
        if _top__cluster_:
            _del__label_ = _top__cluster_.find('g-bubble')
            if _del__label_:
                _del__label_.decompose()

            _child__cluster_ = _top__cluster_.find(class_='z3HNkc')
            if _child__cluster_: 
                if _child__cluster_.has_attr('aria-label'):
                    _star__snippet_ = _top__cluster_.get_text()
                    if _star__snippet_:
                        _star__snippet_ = _star__snippet_.split("·")

                        if len(_star__snippet_):
                            _star__text_ = re.search(r'([\d,.٫]+)', _star__snippet_[0]) 
                            if _star__text_:
                                _star__text_ = _star__text_.group(1)
                                if _star__text_:
                                    _star__text_ = str(_star__text_.replace(",", ".")) 

                                    # RATINGS IN ARABIC AND OTHER SYMBOLS CONVERT TO DECIMAL. 
                                    if not _is__float_(_star__text_): 
                                        # WITHOUT LIBRARY CONVERSION                                    
                                        # _star__list_ = list(map(int, re.findall(r'\d+', _star__text_)))
                                        # _star__list_ = _star__list_ if len(_star__list_) <= 2 else _star__list_[0] 
                                        # ratingContent = float('.'.join(map(str, _star__list_)))  
                                        
                                        # WITH LIBRARY CONVERSION 
                                        ratingContent = _nTd_(_star__text_) 
                                    else:
                                        ratingContent = float(_star__text_)

                        if len(_star__snippet_) > 1 and ratingContent: 
                            if _star__snippet_[1]:                           
                                reviewsText = " · ".join(list(map(str.strip, _star__snippet_[1:len(_star__snippet_)])))

                                _star__snippet_ = _star__snippet_[1].strip().split(" ") 
                                if len(_star__snippet_) == 2:
                                    _star__snippet_[0] = re.sub("[^0-9]","",_star__snippet_[0]) 
                                    _star__snippet_ = re.search(r'([\d]+)', _star__snippet_[0])  
                                    if _star__snippet_:
                                        _star__snippet_ = _star__snippet_.group(1)
                                        if str(_star__snippet_).isdigit(): 
                                            reviewsContent = _star__snippet_ 
            if reviewsText == "":
                reviewsText = _top__cluster_.get_text()

    except Exception as e: 
        ratingContent = 0
        reviewsContent = 0
        reviewsText = ""
        watchdog.coreLog(' > RATINGS ERROR ', engineMode) 
    
    return ratingContent, reviewsContent, reviewsText 

def rankParseData(engineMode, centerdata, postdata, targetLink, xpdTotalContent, mongoResults): 
    exactDomain = postdata['exactdomain']
    keywordTarget = postdata['target']
    domains = list()
    targetMax = 10
    loopCount = 0

    cannibalisationResult = []
    gSnipLink = ""

    mongoFlag = 0
    mongoLiveRank = 0
    ratingContent = 0
    reviewsContent = 0
    reviewsText = ""

    if centerdata:
        # START OF OUTER FEATURED SNIPPET CHECK
        if postdata['featured_snippet'] == True:
            if 'featured_box' in xpdTotalContent:
                if 'link' in xpdTotalContent['featured_box']:
                    keywordLink = xpdTotalContent['featured_box']['link']

                    if keywordLink and mongoFlag == 0:
                        # RANK INCREMENT
                        postdata['rank'] += 1
                        
                        domains.append({
                            "rn": str(postdata['rank']),
                            "dn": extract_domain(keywordLink),
                            "lk": keywordLink
                        })

                        if keywordLink.find(targetLink) > -1:
                            if exactDomain:
                                if exact_url_scheme(keywordLink) == exact_url_scheme(keywordTarget):   
                                    mongoLiveRank = postdata['rank']
                                    keywordTarget = keywordLink
                                    mongoFlag = 2
                            elif extract_domain(keywordLink) == extract_domain(keywordTarget):  
                                mongoLiveRank = postdata['rank']
                                keywordTarget = keywordLink
                                mongoFlag = 2
                            else:
                                pass

                            # TODAY INFORMATION FROM FEATURED SNIPPETS
                            if mongoFlag == 2:
                                todaySnip = {
                                    "lk": xpdTotalContent['featured_box']['link'],
                                    "tt": xpdTotalContent['featured_box']['title'],
                                    "ds": xpdTotalContent['featured_box']['desc'],
                                    "mt": xpdTotalContent['featured_box']['cite'],
                                    "rt": 0,
                                    "rv": "",
                                    "dt": str(datetime.now()),
                                    "img": xpdTotalContent['featured_box']['img'],
                                }
        # END OF OUTER FEATURED SNIPPET CHECK

        urlList = []
        urlList.append(targetLink)
        gMainClassBodyContents = [ele for ele in urlList if(ele in str(centerdata.contents))]  if centerdata else ""
        
        center_block_data = centerdata.find_all("div", recursive= False)
        if len(center_block_data):
            for center_block in center_block_data:
                loopCount += 1

                if not center_block.attrs.get('id'): # rhs knowledge panel removed in rank
                    # gClass = center_block.find_all('div', class_='yuRUbf')
                    gClass = center_block.find_all('h3', class_='LC20lb') 
                    if gClass:
                        anchors_flag = 0
                        for gSubClass in gClass:
                            if gSubClass:
                                descFlag = "block"
                                anchors = gSubClass.find_parent('a')
                                if anchors: 
                                    keywordLink = anchors['href']
                                    
                                    # INNER FEATURED SNIPPETS CHECK
                                    if postdata['rank'] <= 3 and postdata['featured_snippet'] == False:
                                        featured_anchors = anchors.find_parent('div', class_="xpdopen")
                                        if featured_anchors:
                                            # anchors_flag += 1
                                            featured_inner_anchors = anchors.find_parent('div', class_="yuRUbf")
                                            if featured_inner_anchors:
                                                postdata['featured_snippet'] = True
                                                                                                
                                                xpdTitle = "featured_box"
                                                descFlag = "featured" 
                                                xpdTotalContent.update({
                                                    xpdTitle : {
                                                        'status' : "yes" if keywordLink.find(targetLink) > -1 else "no", 
                                                        "link" :  keywordLink,
                                                        "title" : get_title(gSubClass),
                                                        "desc": get_desc(center_block, descFlag),
                                                        "cite": get_cite(center_block),
                                                        "img": ""
                                                    }
                                                })                                   
                                    # INNER FEATURED SNIPPETS CHECK ENDS

                                    if keywordLink and mongoFlag == 0:
                                        if keywordLink.find(targetLink) > -1:
                                            if exactDomain:
                                                if exact_url_scheme(keywordLink) == exact_url_scheme(keywordTarget):   
                                                    postdata['rank'] += 1
                                                    keywordTarget = keywordLink
                                                    mongoFlag = 1
                                            elif extract_domain(keywordLink) == extract_domain(keywordTarget): 
                                                postdata['rank'] += 1 
                                                keywordTarget = keywordLink
                                                mongoFlag = 1
                                            
                                            if mongoFlag == 1:
                                                mongoLiveRank = postdata['rank']
                                                anchors_flag += 1

                                                ratingContent, reviewsContent, reviewsText = get_rating(center_block)

                                                todaySnip = {
                                                    "lk": keywordLink,
                                                    "tt": get_title(gSubClass), 
                                                    "ds": get_desc(center_block, descFlag),
                                                    "mt": get_cite(center_block),
                                                    "rt": ratingContent,
                                                    "rv": reviewsText,  
                                                    "dt": str(datetime.now()),
                                                    "img": "",
                                                }

                                    # RANK INCREMENT
                                    if anchors_flag < 1: 
                                        postdata['rank'] += 1

                                    # CANNIBALISATION
                                    if keywordLink.find(targetLink) > -1: 
                                        if anchors_flag == 1:
                                            anchors_flag = 0
                                        if extract_domain(keywordLink) == targetLink:
                                            cannibalisationResult.append(keywordLink)

                                    # UPDATING DOMAIN TO COMPETITOR LIST
                                    if postdata['rank'] <= (mongoLiveRank + (targetMax - 1)) or mongoLiveRank == 0:
                                        domains.append({
                                            "rn": str(postdata['rank']),
                                            "dn": extract_domain(keywordLink),
                                            "lk": keywordLink
                                        }) 

                        # ONCE LIVE RANK GOTTEN AND ALSO CHECK NEXT 10 COMPETITORS
                        rankFlag = 0
                        if mongoFlag == 1 and (postdata['rank'] > (mongoLiveRank + (targetMax - 1)) or loopCount >= len(center_block_data)):
                            rankFlag = 1
                        elif mongoFlag == 2 and (postdata['rank'] >= (mongoLiveRank + (targetMax - 1)) or loopCount >= len(center_block_data)):
                            rankFlag = 1
                        else:
                            pass

                        # GENERATE RESULTS AND BREAK TO UPDATE DATA 
                        if rankFlag == 1:
                            break 

                # DOMAIN NOT PRESENT THEN BREAK THE LOOP AFTER GOTTEN 10 COMPETITORS
                if bool(gMainClassBodyContents) == False and (postdata['rank']) >= targetMax:
                    break

            if mongoFlag > 0:
            	# KEYWORD RANKED
                if(len(xpdTotalContent)):
                    gSnipLink = list(xpdTotalContent.keys())  
                
                xpdCompContent = domain_competitors(domains, mongoLiveRank, targetMax)

                mongoResults.update([
                    ("URL", keywordTarget),
                    ("RANK", mongoLiveRank),
                    ("RATINGS", ratingContent),
                    ("REVIEWS", reviewsContent), 
                    ("SNIPPETS", gSnipLink if gSnipLink else list()),
                    ("SNIPPET_DETAILS", xpdTotalContent),
                    ("COMPETITORS", xpdCompContent),
                    ("TODAY", todaySnip if "todaySnip" in locals() else {}),
                    ("CANNIBALISATION", cannibalisationResult if len(cannibalisationResult) > 1 else []), 
                ])
                mongopushResult = centralised.mongopush(engineMode, mongoResults) 
                return mongopushResult
            elif mongoFlag == 0:
                # KEYWORD NOT RANKED
                if(len(xpdTotalContent)):
                    gSnipLink = list(xpdTotalContent.keys())

                xpdCompContent = domain_competitors(domains, 0, targetMax)

                mongoResults.update([
                    ("URL", postdata['target']),
                    ("RANK", 0),
                    ("RATINGS", 0),
                    ("REVIEWS", 0),
                    ("SNIPPETS", gSnipLink if gSnipLink else list()),
                    ("SNIPPET_DETAILS", xpdTotalContent),
                    ("COMPETITORS", xpdCompContent),
                    ("TODAY", {}), 
                    ("CANNIBALISATION", cannibalisationResult if len(cannibalisationResult) > 1 else []), 
                ])
                #APPEND TO MONGO 
                mongopushResult = centralised.mongopush(engineMode, mongoResults) 
                return mongopushResult
            else: 
                return 4001
        else:
            return 4002

    return 0

# NEW STRUCTURE
def engineParseData(engineMode, soupdata, postdata):
    _gid_ = postdata["fk_group_id"] 
    # GOOGLE CHECKLIST STARTS
    top_container = "rcnt"
    center_container = "rso"
    # GOOGLE CHECKLIST ENDS

    postdata['featured_snippet'] = False 

    keyWord = postdata['keyword'].lower() 
    exactDomain = postdata['exactdomain']
    region = postdata['se_name'].lower() 
    lang = postdata['language']

    _bot__language_ = _at__common_.__bot_language__(lang)

    if soupdata and (engineMode == "ENGINE" or engineMode == "MANUAL"): 
        pageUuid = str("-")
        pageUuidUrl = str("-")

        cqlRawId = _at__common_.__uuid__()
        if cqlRawId != 0:
            pageUuid = str(cqlRawId) 
            pageUuidUrl = str(encryption.encode_page_url(postdata['fk_user_id'], postdata['id'], cqlRawId)) 

        bsoup = cleanMe(soupdata, lang)

        # SHOW ALSO RESULTS FOR
        resultAboutExists = bsoup.find("div", {"id": "result-stats"}) 
        resultAbout = "-" 
        resultTime = "-" 

        if resultAboutExists:  
            resultContent = resultAboutExists.contents 
            if len(resultContent) >= 1:
                resultAbout = re.sub("[^0-9,. ]","",resultContent[0]).strip()
                resultAbout = resultAbout.replace(".", ",").replace(" ", ",")
            if len(resultContent) >= 2:
                resultTime = re.sub("[^0-9,.]","",resultContent[1].text.strip())
                resultTime = resultTime.replace(",", ".") 
        
        # ALIAS KEYWORD - "ERROR" FOR GERMAN LANGUAGE
        gAliasKey = ""
        gAliasKeyword = bsoup.find("div", {"id": "taw"})  
        if gAliasKeyword: 
            gAliasTag = gAliasKeyword.find("p", {"class": "card-section"})
            if gAliasTag: 
                gAliasTagText = gAliasTag.text.lower() 
                if gAliasTagText.find(keyWord) > -1:
                    gAliasKey = gAliasTag.findNext('a').text

        # ALL SNIPPETS
        xpdTotalContent = {}
        adPosition = "" 
        gSnipLink = "" 
        adsTopList = [] 
        adsBottomList = [] 

        xpdTotalContent = {}
        mongoResults = {}

        panelFlag = 0

        # TARGET DOMAIN EXTRACTED
        targetLink = extract_domain(postdata['target'])

        gAdLinks = bsoup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for gAdLink in gAdLinks:
            headerTagText = gAdLink.text.replace(' ','_').lower()

            if headerTagText == _bot__language_['_complementary_']: 
                panelFlag = 1

            # KNOWLEDGE PANEL
            if _bot__language_['_description_'] in headerTagText and panelFlag == 1:
                if "wikipedia" in gAdLink.parent.parent.text.replace(' ','_').lower(): 
                    xpdTitle = "knowledge_box" 
                    xpdTotalContent.update({ 
                        xpdTitle : {    
                            "present" : "yes"
                        }
                    })

            # SITE LINKS 
            if gAdLink.name == "h2" and _bot__language_['_site__links_'] in headerTagText: 
                tableFlag = gAdLink.parent.find('table')
                if tableFlag:
                    if len(tableFlag.find_all('h3')) > 1 and str(tableFlag).count(targetLink) > 0: 
                        xpdTitle = "slrs"    
                        xpdTotalContent.update({ 
                            xpdTitle : "yes"
                        }) 

            # IMAGES PACK
            if gAdLink.name == "h3" and _bot__language_['_images_'] in headerTagText:
                xpdTitle = "imrs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # MAPS PACK
            if gAdLink.name == "h2" and _bot__language_['_map_'] == headerTagText:
                xpdTitle = "mprs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # LOCAL RESULTS PACK
            if gAdLink.name == "h2" and _bot__language_['_local_'] == headerTagText: 
                xpdTitle = "lcrs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # TWITTER RESULTS PACK
            if gAdLink.name == "h2" and _bot__language_['_twitter_'] == headerTagText:
                xpdTitle = "twrs" 
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # VIDEOS RESULTS PACK
            if gAdLink.name == "h3" and _bot__language_['_videos_'] == headerTagText: 
                xpdTitle = "vdrs"  
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # TOP STORIES OR NEWS RESULTS PACK
            if gAdLink.name == "h3" and _bot__language_['_top__stories_'] == headerTagText:
                xpdTitle = "nwrs"  
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # PEOPLE ALSO ASK OR RELATED QUESTIONS.
            if gAdLink.name == "h3" and _bot__language_['_people__ask_'] in headerTagText:
                xpdTitle = "rqrs"  
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

        # ADS
        adsTopList, adPresence = topAds(bsoup, targetLink) 
        if adPresence:
            adPosition = "top"

        adsBottomList, adPresence = bottomAds(bsoup, targetLink) 
        if adPresence:
            adPosition = "bottom"

        if len(adsTopList) > 0 or len(adsBottomList) > 0:
            xpdTotalContent.update({
                "ads" : {
                    "top_result": adsTopList,
                    "bottom_result": adsBottomList, 
                    "status": "yes" if adPosition in ["top", "bottom"] else "no",
                    "top_count": len(adsTopList),
                    "bottom_count": len(adsBottomList),
                    "present": adPosition
                }
            })

        mongoResults.update([
            ("ID", postdata['id']),
            ("WRONGKEYWORD", 0), 
            ("URL", postdata['target']),
            ("KEYALIAS", gAliasKey),
            ("TOTAL_RESULTS", resultAbout),  
            ("TOTAL_TIME", resultTime),   
            ("PAGE_UUID",pageUuid),
            ("PAGE_UUID_URL",pageUuidUrl),
            ("TARGET",targetLink),
        ])

        # RESULTS PARSE
        cannibalisationResult = []

        gMainClassBody = bsoup.find("body") 
        top_container_block = bsoup.find("div", {"id": top_container})
        if top_container_block:
            top_container_child = top_container_block.findChildren(recursive=False) 

            if top_container_child:
                postdata['rank'] = 0
                flager = 0

                # START OF RSO SEGMENT
                for container_child in top_container_child:
                    center_container_block = container_child.find("div", {"id": center_container}) 
                    if center_container_block:
                        flager = rankParseData(engineMode, center_container_block, postdata, targetLink, xpdTotalContent, mongoResults)
                    else:
                        center_block = container_child.find('div', class_="xpdopen")
                        if center_block:
                            # OUTER FEATURED SNIPPETS STARTS
                            gClass = center_block.find('div', class_='yuRUbf')
                            if gClass:
                                anchors = gClass.find('a')
                                if anchors:
                                    flager += 1
                                    keywordLink = anchors['href']

                                    xpdTitle = "featured_box"
                                    xpdTotalContent.update({
                                        xpdTitle : {
                                            'status' : "yes" if keywordLink.find(targetLink) > -1 else "no", 
                                            "link" :  keywordLink,
                                            "title" : get_title(anchors.find('h3')), 
                                            "desc": get_desc(center_block, "featured"), 
                                            "cite": get_cite(gClass),
                                            "img": ""
                                        }
                                    })
                                    postdata['featured_snippet'] = True
                            # OUTER FEATURED SNIPPETS ENDS
                # END OF RSO SEGMENT

                if flager == 1:
                    return 1
                else:
                    # CHECK NO DOCUMENTS MATCH
                    gNDF = gMainClassBody.find('div', class_="mnr-c")
                    if gNDF:
                        gNDF0 = gNDF.find('div', class_="card-section")
                        gNDF1 = gNDF.find(attrs={"role": True, "aria-level":"3"})
                        gNDF2 = gNDF.find('ul')

                        if gNDF and gNDF0 and gNDF1 and gNDF2:
                            xpdCompContent = {
                                "tp": [],
                                "bf": [],
                                "ar": []
                            }

                            mongoResults.update([ 
                                ("URL", postdata['target']),
                                ("RANK", 0),
                                ("RATINGS", 0),
                                ("REVIEWS", 0),
                                ("SNIPPETS", gSnipLink if gSnipLink else list()),
                                ("SNIPPET_DETAILS", xpdTotalContent),
                                ("COMPETITORS", xpdCompContent),
                                ("TODAY", {}), 
                                ("CANNIBALISATION", cannibalisationResult), 
                            ])
                            mongopushResult = centralised.mongopush(engineMode, mongoResults)
                            watchdog.coreLog(' > NO DOCUMENTS FOUND ERROR >> KEY_ID '+str(postdata['id']), engineMode)
                            return mongopushResult 
                        else:
                            pass

                if flager == 4001:
                    # UNEXPECTED RANK ERROR OCCURED 
                    watchdog.coreLog(' > DESKTOP - UNEXPECTED ERROR ON RANK >> KEY_ID '+str(postdata['id']), engineMode)                   
                elif flager == 4002:
                    # NO DATA SET INSIDE RSO
                    watchdog.coreLog(' > DESKTOP - NO DATA SET INSIDE RSO >> KEY_ID '+str(postdata['id']), engineMode)
                else:
                    watchdog.coreLog(" > DESKTOP - RSO - GOOGLE PAGE FORMAT ERROR >> KEY_ID "+str(postdata['id']), engineMode)
            else:
                watchdog.coreLog(" > DESKTOP - RCNT - NO CHILDRENS ERROR >> KEY_ID "+str(postdata['id']), engineMode) 
        else:
            watchdog.coreLog(" > DESKTOP - RCNT - ERROR >> KEY_ID "+str(postdata['id']), engineMode) 
    
    if engineMode == "ENGINE": 
        _at__common_.__change_group_call_status__(_gid_, "STOP") 
    else:
        return watchdog.coreCondition(engineMode, 1, postdata)
    
    return 0