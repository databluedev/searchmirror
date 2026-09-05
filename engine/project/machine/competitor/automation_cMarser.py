from django.conf import settings

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_
from project.machine.submodels.serpmodels import DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

from rest_framework.decorators import api_view

import requests, json, time, re 
from bs4 import BeautifulSoup
from urllib import parse 
import sys, os, random 
from datetime import datetime, date
from urllib.parse import urlparse 

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine.competitor import automation_cStorage as centralised 

def cleanMe(soup):
    try:
    	idElement = soup.find("div", id="before-appbar") 
    	if idElement: 
    		idElement.decompose()

    	idElement = soup.find("div", id="lfootercc")  
    	if idElement:
    		idElement.decompose() 

    	elements = soup.findAll(["hr", "script", "noscript", "style", "button", "head", "dialog", "noscript", "form", "header", "g-dropdown-menu",  "svg", "textarea", "g-more-button", "g-fab", "g-tabs", "wholepage-tab-history-helper"])    
    	for element in elements:
    		element.decompose() 
    except Exception as e:
        # MOBILE BOT CLEAN ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE ERROR ON MOBILE SOUP CLEAN", "COMPALYSE")

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

# NEW STRUCTURE 
def parseAds(centerdata, target, engineMode):
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
        adsList = list()
        adexist = 0
        # DESKTOP PARSE ADS ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
        _wd_.coreLog(" > COMPALYSE MOBILE PARSE ADS FUNCTION ERROR", engineMode)  

    return adsList, adexist

def topAds(bsoup, btarget, engineMode):
    try:
        top_ad_container = bsoup.find('div', attrs={"id": "tads", "role":"region"})
        if top_ad_container:
            top_header_container = top_ad_container.find('h1')
            if top_header_container:
                return parseAds(top_header_container, btarget, engineMode) 
    except Exception as e:
        # MOBILE TOP ADS ERROR 
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE TOP ADS FUNCTION ERROR", engineMode)  

    return list(), 0

def bottomAds(bsoup, btarget, engineMode):
    try:
        bottom_ad_container = bsoup.find('div', attrs={"id": "bottomads"})
        if bottom_ad_container:
            bottom_header_container = bottom_ad_container.find('h1')
            if bottom_header_container:
                return parseAds(bottom_header_container, btarget, engineMode)
    except Exception as e:
        # MOBILE BOTTOM ADS ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE BOTTOM ADS FUNCTION ERROR", engineMode)

    return list(), 0

def get_cite(block, flag, engineMode): 
    citeLink = []

    try:
        if flag == "block":
            citeBlock = block.find('div', attrs={"aria-label": True, "role": "link"})
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
    except Exception as e:
        citeLink = []
        # MOBILE CITE ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE CITE FUNCTION ERROR", engineMode)

    return citeLink

def get_title(block, engineMode): 
    titleBlock = ""

    try:
        titleBlock = block.get_text()
    except Exception as e:
        titleBlock = "" 
        # DESKTOP TITLE ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE TITLE FUNCTION ERROR", engineMode)

    return titleBlock if len(titleBlock) else "" 


def get_desc(block, flag, engineMode):
    try:
        if flag == "block":
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
        # MOBILE DESCRIPTION ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE DESCRIPTION FUNCTION ERROR", engineMode) 

    return []

def get_rating(block, engineMode):
    ratingArray = []
    ratingContent = 0
    reviewsContent = 0
    reviewsText = ""

    try:
        gSingleGroupInner = block.find(attrs={'aria-label':True, "role":"img"})
        if gSingleGroupInner:
            if gSingleGroupInner.find_previous_sibling():
                ratingContent = re.sub("[^0-9.]","",gSingleGroupInner.find_previous_sibling().text)
                ratingContent = ratingContent if len(_at__common_.trim(ratingContent)) > 0 else 0
            if gSingleGroupInner.find_next_sibling():
                reContent = re.sub("[^0-9]","",gSingleGroupInner.find_next_sibling().text).strip() 
                reviewsContent = reContent if len(_at__common_.trim(reContent)) > 0 else 0  
                reviewsText = str(reviewsContent)+" reviews"
    except Exception as e:
        ratingContent = 0
        reviewsContent = 0
        reviewsText = "" 
        # MOBILE RATINGS ERROR 
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE RATINGS FUNCTION ERROR", engineMode) 

    return ratingContent, reviewsContent, reviewsText

# NEW STRUCTURE
def rankParseData(engineMode, centerdata, postdata, targetLink, xpdTotalContent, mongoResults): 
    errorValue = 0

    try:
        keywordTarget = postdata['target']
        loopCount = 0
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
                
                # MAIN ITERATION BEGINS
                for center_block in center_block_data:
                    loopCount += 1

                    if not center_block.attrs.get('id'): # rhs knowledge panel removed in rank

                        # INNER FEATURED SNIPPETS CHECK - STARTS 
                        if postdata['rank'] <= 3 and postdata['featured_snippet'] == False:
                            featured_outer_set = centerdata.find('div', class_="xpdopen")
                            if featured_outer_set:
                                featured_flag = 0
                                featured_inner_set = featured_outer_set.find_all('div', class_="V3FYCf")
                                
                                # FEATURED SNIPPETS ITERATION BEGINS
                                for featured_anchors in featured_inner_set:
                                    featured_title_anchors = featured_anchors.find('h3')
                                    featured_link_anchors = featured_anchors.find("a") 
                                    if featured_title_anchors and featured_link_anchors:
                                        postdata['featured_snippet'] = True
                                        postdata['rank'] += 1
                                        keywordLink = featured_link_anchors['href']

                                        if featured_flag < 1: 
                                            xpdTitle = "featured_box"
                                            xpdTotalContent.update({
                                                xpdTitle : {
                                                    'status' : "yes" if keywordLink.find(targetLink) > -1 else "no", 
                                                    "link" :  keywordLink,
                                                    "title" : get_title(featured_title_anchors, engineMode),
                                                    "desc": get_desc(featured_anchors, "featured", engineMode),
                                                    "cite": get_cite(featured_anchors, "featured", engineMode),
                                                    "img": ""
                                                }
                                            })

                                        if keywordLink.find(targetLink) > -1 and bool(gMainClassBodyContents): 
                                            if extract_domain(keywordLink) == extract_domain(keywordTarget):
                                                mongoLiveRank = postdata['rank']
                                                keywordTarget = keywordLink
                                                mongoFlag = 2
                                            else:
                                                pass

                                            # TODAY INFORMATION FROM FEATURED SNIPPETS
                                            if mongoFlag == 2:
                                                featured_flag += 1

                        # INNER FEATURED SNIPPETS CHECK - ENDS
                        gClass = center_block.find_all(class_="oewGkc", role="heading", attrs={"aria-level":"3"})
                        if gClass:
                            anchors_flag = 0

                            # RANK ITERATION BEGINS
                            for gSubClass in gClass:
                                if gSubClass:
                                    anchors = gSubClass.find_parent('a')
                                    set_block = gSubClass.find_parent(attrs={"data-hveid":True})
                                    if anchors and set_block: 
                                        keywordLink = anchors['href']

                                        if keywordLink and mongoFlag == 0 and bool(gMainClassBodyContents):
                                            if keywordLink.find(targetLink) > -1:
                                                if extract_domain(keywordLink) == extract_domain(keywordTarget): 
                                                    postdata['rank'] += 1 
                                                    keywordTarget = keywordLink
                                                    mongoFlag = 1
                                                
                                                if mongoFlag == 1:
                                                    mongoLiveRank = postdata['rank']
                                                    anchors_flag += 1

                                                    ratingContent, reviewsContent, reviewsText = get_rating(set_block, engineMode)   

                                        # RANK INCREMENT
                                        if anchors_flag < 1:
                                            postdata['rank'] += 1

                            # GENERATE RESULTS AND BREAK TO UPDATE DATA 
                            if mongoFlag > 0: 
                                break   

                    # CHECKING FOR THE DOMAIN EXIST IN THE SOUP STRING 
                    if bool(gMainClassBodyContents) == False and (postdata['featured_snippet'] == True or postdata['rank'] > 3): 
                        break 

                if mongoFlag > 0:
                    # KEYWORD RANKED
                    if(len(xpdTotalContent)):
                        gSnipLink = list(xpdTotalContent.keys())  

                    mongoResults.update([
                        ("URL", keywordTarget),
                        ("RANK", mongoLiveRank),
                        ("RATINGS", ratingContent),
                        ("REVIEWS", reviewsContent), 
                        ("SNIPPETS", gSnipLink if gSnipLink else list()),
                        ("SNIPPET_DETAILS", xpdTotalContent),
                    ])
                    # print("\n", mongoResults)
                    #APPEND TO MONGO 
                    mongopushResult = centralised.mongopush(engineMode, mongoResults) 
                    return 1

                elif mongoFlag == 0:
                    # KEYWORD NOT RANKED
                    if(len(xpdTotalContent)):
                        gSnipLink = list(xpdTotalContent.keys())

                    mongoResults.update([
                        ("URL", postdata['target']),
                        ("RANK", 0),
                        ("RATINGS", 0),
                        ("REVIEWS", 0),
                        ("SNIPPETS", gSnipLink if gSnipLink else list()),
                        ("SNIPPET_DETAILS", xpdTotalContent),
                    ])
                    # print("\n", mongoResults)  
                    #APPEND TO MONGO 
                    mongopushResult = centralised.mongopush(engineMode, mongoResults)
                    return 1
                else:                
                    errorValue = 4001
            else:            
                errorValue = 4002

    except Exception as e:
        errorValue = 5000 
        _wd_.coreLog(" > COMPALYSE MOBILE RANK PARSE DATA FUNCTION ERROR", engineMode) 

    return errorValue     

def engineParseData(engineMode, soupdata, postdata):
    # GOOGLE CHECKLIST STARTS
    top_container = "center_col"
    center_container = "rso"
    # GOOGLE CHECKLIST ENDS


    try: 
        postdata['featured_snippet'] = False
        lang = postdata['language'] 
        __cp_kid__ = postdata['id'] 
        _bot__language_ = _at__common_.__bot_language__(lang)

        if soupdata and engineMode == "COMPALYSE":
            bsoup = cleanMe(soupdata)

            # ALL SNIPPETS
            xpdTotalContent = {}
            adPosition = "" 
            gSnipLink = ""
            adsTopList = [] 
            adsBottomList = [] 

            mongoResults = {}

            # TARGET DOMAIN EXTRACTED
            targetLink = extract_domain(postdata['target'])

            panelFlag = 0
            newsPack = 0
            mapFlag = 0
            relatedQuestionPack = 0
            videosPack = 0
            imagesPack = 0
            localPack = 0

            gAdLinks = bsoup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            # FIRST SNIPPETS LOOP
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
            # FIRST SNIPPETS ENDS

            # SECOND SNIPPETS LOOP STARTS
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
            # SECOND SNIPPETS LOOP ENDS

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
            adsTopList, adPresence = topAds(bsoup, targetLink, engineMode) 
            if adPresence:
            	adPosition = "top"

            adsBottomList, adPresence = bottomAds(bsoup, targetLink, engineMode) 
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
            	("URL", postdata['target']),
            	("TARGET", targetLink),
            ]) 

            # RESULTS PARSE
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
                    gNDF = gMainClassBody.find('div', attrs={"id":"topstuff"})                
                    if gNDF:
                    	gNDF0 = gNDF.find('div', class_="card-section")
                    	gNDF1 = gNDF.find(attrs={"role": True, "aria-level":"3"})
                    	gNDF2 = gNDF.find('ul')

                    	if gNDF and gNDF0 and gNDF1 and gNDF2:
                    		mongoResults.update([
                    			("RANK", 0),
                    			("RATINGS", 0),
                    			("REVIEWS", 0),
                    			("SNIPPETS", gSnipLink if gSnipLink else list()),
                    			("SNIPPET_DETAILS", xpdTotalContent),
                    		])
                    		mongopushResult = centralised.mongopush(engineMode, mongoResults)  
                    		_wd_.coreLog(" > MOBILE NO DOCUMENTS FOUND ERROR >> CP_KID "+str(__cp_kid__), engineMode) 
                    		return 1 
                    	else:
                    		pass

                    if flager == 4001:
                        # UNEXPECTED MOBILE RANK ERROR OCCURED 
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > MOBILE - UNEXPECTED ERROR ON RANK >> CP_KID "+str(__cp_kid__), engineMode) 
                    elif flager == 4002:
                        # NO DATA SET INSIDE RSO
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > MOBILE - NO DATA SET INSIDE RSO >> CP_KID "+str(__cp_kid__), engineMode)
                    else:
                        # GOOGLE PAGE ERROR 
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > MOBILE RSO - GOOGLE PAGE FORMAT ERROR >> CP_KID "+str(__cp_kid__), engineMode)

            		# return _wd_.coreCondition(engineMode, 1, postdata)
                    return True
            else: 
                _wd_.coreLog(" > MOBILE RCNT ERROR >> CP_KID "+str(__cp_kid__), engineMode) 
                # return _wd_.coreCondition(engineMode, 1, postdata)
                return True

    except Exception as e:
        # GOOGLE MOBILE PARSER ERROR 
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE MOBILE ENGINE PARSE DATA FUNCTION ERROR >> CP_KID "+str(__cp_kid__), engineMode)

    return 0