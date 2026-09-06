from django.shortcuts import render
from django.conf import settings

from rest_framework_mongoengine import viewsets as meviewsets
from project.machine.models import Keyword, Group, ManualRefresh, Mainsettings 

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

import re 


def __distinct_pages__(links):
	"""The pages that cannibalise a keyword, each counted once.

	Cannibalisation is more than one page of YOUR OWN site ranking for one
	keyword, so they compete with each other. The collector above appends every
	matching result, and the same URL can arrive more than once -- as an organic
	result and again as a sitelink or a variant. Counting the raw list therefore
	flagged a single page as cannibalising itself: seen in production on
	2026-09-06, where one keyword carried the identical URL twice and the
	keywords table told the owner to "fix cannibalization issues" for a page that
	has no competitor.

	Order is preserved -- it is the order the pages ranked in, which is the order
	someone reading the list expects.
	"""
	seen = list(dict.fromkeys(link for link in (links or []) if link))
	return seen if len(seen) > 1 else []

def trim(value):
    return value.strip()

def cleanMe(soup):
	idElement = soup.find("div", id="before-appbar") 
	if idElement: 
		idElement.decompose()

	idElement = soup.find("div", id="lfootercc")  
	if idElement:
		idElement.decompose() 

	elements = soup.findAll(["hr", "script", "noscript", "style", "button", "head", "dialog", "noscript", "form", "header", "g-dropdown-menu",  "svg", "textarea", "g-more-button", "g-fab", "g-tabs", "wholepage-tab-history-helper"])    
	for element in elements:
		element.decompose() 

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

# def mobileCannibalisation(soup, targetLink):
# 	canniValue = []
# 	for c_data in soup:
# 		c_data = c_data.find_parent('a')
# 		if c_data:
# 			c_filter_data = c_data.get('href','')
# 			if c_filter_data.find(targetLink) > -1: 
# 				if extract_domain(c_filter_data) == targetLink: 
# 					canniValue.append(c_filter_data)  
# 	return canniValue if len(canniValue) > 1 else [] 

# NEW STRUCTURE 
def parseAds(centerdata, target):
    adsList = []
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
                    parseExtract = []
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

def get_cite(block, flag): 
    citeLink = []

    if flag == "block":
        citeBlock = block.find(attrs={"role": "text"}) 
        if citeBlock:
            citeLink.append(citeBlock.get_text()) 
    elif flag == "featured":
        citeBlock = block.find('cite')
        if citeBlock:
            for cLink in citeBlock:
                if cLink.name is None:
                    citeLink.append(cLink)
                else:
                    citeLink.append(cLink.get_text())

    return citeLink

def get_title(block):
    titleBlock = block.get_text()
    return titleBlock if len(titleBlock) else "" 

def get_desc(block, flag):
    if flag == "block":
        descBlock = block.find('div', attrs={'class': 'VwiC3b'})
        if descBlock:
            descContent = descBlock.get_text()
            if descContent:
                return [descContent.strip()]
        descBlock = block.find('div', attrs={'data-snf': 'nke7rc'}) 
        if descBlock:
            descContent = descBlock.get_text()
            if descContent:
                return [descContent.strip()]
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

    return []

def get_rating(block):
    try:
        ratingArray = []
        ratingContent = 0
        reviewsContent = 0
        reviewsText = ""

        gSingleGroupInner = block.find(attrs={'aria-label':True, "role":"img"})
        if gSingleGroupInner:
            if gSingleGroupInner.find_previous_sibling():
                ratingContent = re.sub("[^0-9.]","",gSingleGroupInner.find_previous_sibling().text)
                ratingContent = ratingContent if len(trim(ratingContent)) > 0 else 0
            if gSingleGroupInner.find_next_sibling():
                reContent = re.sub("[^0-9]","",gSingleGroupInner.find_next_sibling().text).strip() 
                reviewsContent = reContent if len(trim(reContent)) > 0 else 0
                reviewsText = str(reviewsContent)+" reviews" 
    except Exception as e:
        ratingContent = 0
        reviewsContent = 0
        reviewsText = ""

    return ratingContent, reviewsContent, reviewsText

# NEW STRUCTURE
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
        urlList = []
        urlList.append(targetLink)
        gMainClassBodyContents = [ele for ele in urlList if(ele in str(centerdata.contents))]  if centerdata else ""
        
        # RSO CHILDRENS
        center_block_data = centerdata.find_all("div", recursive= False)
        if len(center_block_data):
            for center_block in center_block_data:
                loopCount += 1

                if not center_block.attrs.get('id'): # rhs knowledge panel removed in rank

                    # INNER FEATURED SNIPPETS CHECK - STARTS 
                    if postdata['rank'] <= 3 and postdata['featured_snippet'] == False:
                        featured_outer_set = centerdata.find('div', class_="xpdopen")
                        if featured_outer_set:
                            featured_flag = 0
                            featured_inner_set = featured_outer_set.find_all('div', class_="V3FYCf")
                            for featured_anchors in featured_inner_set:
                                featured_title_anchors = featured_anchors.find('h3')
                                featured_link_anchors = featured_anchors.find("a") 
                                if featured_title_anchors and featured_link_anchors:
                                    postdata['featured_snippet'] = True
                                    postdata['rank'] += 1
                                    keywordLink = featured_link_anchors['href']

                                    domains.append({
                                        "rn": str(postdata['rank']),
                                        "dn": extract_domain(keywordLink),
                                        "lk": keywordLink
                                    })

                                    featured_title = get_title(featured_title_anchors)
                                    featured_desc = get_desc(featured_anchors, "featured") 
                                    featured_cite = get_cite(featured_anchors, "featured")

                                    if featured_flag < 1:
                                        xpdTitle = "featured_box"
                                        xpdTotalContent.update({
                                            xpdTitle : {
                                                'status' : "yes" if keywordLink.find(targetLink) > -1 else "no", 
                                                "link" :  keywordLink,
                                                "title" : featured_title,
                                                "desc": featured_desc,
                                                "cite": featured_cite,
                                                "img": ""
                                            }
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
                                            featured_flag += 1
                                            todaySnip = {
                                                "lk": keywordLink,
                                                "tt": featured_title,
                                                "ds": featured_desc,
                                                "mt": featured_cite,
                                                "rt": 0,
                                                "rv": "",
                                                "dt": str(datetime.now()),
                                                "img": "",
                                            }

                    # INNER FEATURED SNIPPETS CHECK - ENDS

                    # gClass = center_block.find_all(class_="v0nnCb", role="heading", attrs={"aria-level":"3"})
                    gClass = center_block.find_all(class_="oewGkc", role="heading", attrs={"aria-level":"3"})
                    if gClass:
                        anchors_flag = 0
                        for gSubClass in gClass:
                            if gSubClass:
                                anchors = gSubClass.find_parent('a')
                                set_block = gSubClass.find_parent(attrs={"data-hveid":True})
                                if anchors and set_block: 
                                    keywordLink = anchors['href']

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

                                                ratingContent, reviewsContent, reviewsText = get_rating(set_block) 

                                                todaySnip = {
                                                    "lk": keywordLink,
                                                    "tt": get_title(gSubClass), 
                                                    "ds": get_desc(set_block, "block"),
                                                    "mt": get_cite(anchors, 'block'),
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
                    ("CANNIBALISATION", __distinct_pages__(cannibalisationResult)), 
                ])
                mongopushResult = centralised.mongopush(engineMode, mongoResults)
                return 1
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
                    ("CANNIBALISATION", __distinct_pages__(cannibalisationResult)), 
                ])
                #APPEND TO MONGO 
                mongopushResult = centralised.mongopush(engineMode, mongoResults)
                return 1
            else:                
                return 4001
        else:            
            return 4002

    return 0    

def engineParseData(engineMode, soupdata, postdata):
    _gid_ = postdata["fk_group_id"] 
    # GOOGLE CHECKLIST STARTS
    top_container = "center_col"
    center_container = "rso"
	# GOOGLE CHECKLIST ENDS

    keyWord = postdata['keyword'].lower() 
    exactDomain = postdata['exactdomain']  
    region = postdata['se_name'].lower() 
    lang = postdata['language'] 
    postdata['featured_snippet'] = False

    _bot__language_ = _at__common_.__bot_language__(lang)

    if soupdata and (engineMode == "ENGINE" or engineMode == "MANUAL"):
        pageUuid = str("-")
        pageUuidUrl = str("-")

        cqlRawId = _at__common_.__uuid__() 
        if cqlRawId != 0:
            pageUuid = str(cqlRawId) 
            pageUuidUrl = str(encryption.encode_page_url(postdata['fk_user_id'], postdata['id'], cqlRawId))

        bsoup = cleanMe(soupdata) 

        # ABOUT AND TIME RESULTS STRICTLY NOT AVAILABLE IN MOBILE PLATFORM
        resultAbout = "-"  
        resultTime = "-"

        #ALIAS KEYWORD 
        gAliasKey = ""
        gAliasKeyword = bsoup.find("div", {"id": "taw"})  
        if gAliasKeyword: 
            gAliasTag = gAliasKeyword.find("p", {"class": "card-section"})  
            if gAliasTag:
                gAliasKey = gAliasTag.findNext('a').text    
				
        # ALL SNIPPETS
        adPosition = "" 
        adsTopList = [] 
        adsBottomList = [] 

        xpdTotalContent = {}
        mongoResults = {}

        # TARGET DOMAIN EXTRACTED
        targetLink = extract_domain(postdata['target'])

        gSnipLink = ""
        newsPack = 0
        panelFlag = 0
        mapFlag = 0
        relatedQuestionPack = 0
        videosPack = 0
        imagesPack = 0
        localPack = 0

        gAdLinks = bsoup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for gAdLink in gAdLinks: 
            headerTagText = gAdLink.text.replace(' ','_').lower()

            # START - WEB RESULTS WITH SITE LINKS.
            if gAdLink.name == "h2" and _bot__language_['_site__links_'] in headerTagText: 
                tableFlag = gAdLink.parent.find_all('a')
                tableContent = gAdLink.parent
                if len(tableFlag) > 1 and str(tableContent).count(targetLink) > 1:
                    xpdTitle = "slrs"
                    xpdTotalContent.update({ 
                        xpdTitle : "yes"
                    })

            # MOBILE - TWITTER PACK
            if gAdLink.name == "h2" and _bot__language_['_twitter_'] == headerTagText: 
                xpdTitle = "twrs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                })

            # NEWS PACK
            if gAdLink.name == "h2" and _bot__language_['_news_'] == headerTagText: 
                newsPack = 1
                xpdTitle = "nwrs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                }) 

            # MAP RESULTS PACK
            if gAdLink.name == "h2" and _bot__language_['_map_'] == headerTagText and mapFlag == 0:
                mapFlag = 1  
                xpdTitle = "mprs"
                xpdTotalContent.update({ 
                    xpdTitle : "yes" 
                }) 

            if gAdLink.name == "h2" and _bot__language_['_description_'] in headerTagText and panelFlag == 0:
                if "wikipedia" in gAdLink.parent.parent.text.replace(' ','_').lower():
                    panelFlag = 1
                    xpdTitle = "knowledge_box" 
                    xpdTotalContent.update({ 
                        xpdTitle : {    
                            "present" : "yes"  
                        } 
                    }) 

        idElement = bsoup.findAll(role="heading", attrs={"aria-level":"2"}) 
        for singleId in idElement: 
            # PEOPLE ALSO ASK OR RELATED QUESTIONS.
            if _bot__language_['_people__ask_'] == singleId.get_text(strip=True).replace(' ','_').lower() and relatedQuestionPack == 0: 
                relatedQuestionPack = 1 
                xpdTitle = "rqrs" 
                xpdTotalContent.update({ 
                    xpdTitle : "yes"  
                }) 
			
            if _bot__language_['_videos_'] == singleId.get_text(strip=True).replace(' ','_').lower() and videosPack == 0: 
                videosPack = 1 
                xpdTitle = "vdrs" 
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                }) 

            if _bot__language_['_top__stories_'] == singleId.get_text(strip=True).replace(' ','_').lower() and newsPack == 0: 
                newsPack = 1 
                xpdTitle = "nwrs" 
                xpdTotalContent.update({ 
                    xpdTitle : "yes"
                }) 

            imgCaption = singleId.get_text(strip=True).replace(' ','_').lower()
            if imgCaption:
                imgCaption = str(re.sub("[^a-z_]","",imgCaption))

            if (_bot__language_['_images_'] == imgCaption or _bot__language_['_images_'] in imgCaption)  and imagesPack == 0:  
                imagesPack = 1 
                xpdTitle = "imrs"  
                xpdTotalContent.update({ 
                    xpdTitle : "yes" 
                }) 

        gLocalLinks = bsoup.find('div', attrs={"class":"IEBeid"})
        if gLocalLinks:
            if gLocalLinks.find("div", attrs={"aria-level":True, "role":"heading"}): 
                localPack = 1

        if localPack == 0: 
            gLocalLinks = bsoup.find('div', attrs={"data-prvwid":"HEADER"})
            if gLocalLinks:
                if gLocalLinks.find(attrs={"aria-level":True, "role":"heading"}):
                    localPack = 1 

        if localPack == 1:
            xpdTitle = "lcrs"  
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
            ("TARGET", targetLink),
        ]) 

        # RESULTS PARSE
        cannibalisationResult = []

        gMainClassBody = bsoup.find("body")
        top_container_block = bsoup.find("div", {"id": top_container})
        if top_container_block:
            postdata['rank'] = 0
            flager = 0

            center_container_block = top_container_block.find("div", {"id": center_container}) 
            if center_container_block:
                flager = rankParseData(engineMode, center_container_block, postdata, targetLink, xpdTotalContent, mongoResults)

            if flager == 1:
                return 1
            else:
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
                        watchdog.coreLog(' > MOBILE NO DOCUMENTS FOUND ERROR >> KEY_ID '+str(postdata['id']), engineMode)
                        return 1
                    else:
                        pass

            if flager == 4001: 
                # UNEXPECTED RANK ERROR OCCURED
                watchdog.coreLog(' > MOBILE - UNEXPECTED ERROR ON RANK >> KEY_ID '+str(postdata['id']), engineMode)
            elif flager == 4002:
                # NO DATA SET INSIDE RSO
                watchdog.coreLog(' > MOBILE - NO DATA SET INSIDE RSO >> KEY_ID '+str(postdata['id']), engineMode)
            else:
                watchdog.coreLog(" > MOBILE RSO - GOOGLE PAGE FORMAT ERROR >> KEY_ID "+str(postdata['id']), engineMode)
        else:
            watchdog.coreLog(" > MOBILE RCNT ERROR >> KEY_ID "+str(postdata['id']), engineMode) 

    if engineMode == "ENGINE": 
        _at__common_.__change_group_call_status__(_gid_, "STOP") 		
    else:
        return watchdog.coreCondition(engineMode, 1, postdata)

    return 0 