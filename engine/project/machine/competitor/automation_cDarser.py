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

def cleanMe(soup, lang):
    # _bot__clean_ = _at__common_.__bot_clean__(lang) # DON'T REMOVE PLEASE REFER GENERAL PARSER FILE. 
    try:
    	for tag in soup.find_all(True): 
    		tExtract = True
    		if len(tag.findChildren(recursive=True)) != 0 or len(tag.text) != 0:
    			if tag.has_attr("id"):
    				tId = tag.get("id")
    				if tId:
    					if tId in ["searchform", "top_nav"]:
    						tExtract = False

    			if tExtract == False: 
    				tag.decompose() 

    		if tag.name in ["head", "style", "script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]:
    			tag.extract()

    	for tag in soup.find_all(True):
    		if tag.name in ["head", "div", "a", "span", "w-debug-content", "g-right-button", "g-left-button", "title-with-lhs-icon", "g-section-with-header", "g-inner-card", "g-scrolling-carousel", "g-image-section", "g-link", "g-img"] and len(tag.findChildren(recursive=True)) == 0 and len(tag.text) == 0: 
    			tag.extract()  
    except Exception as e:
        # DESKTOP BOT CLEAN ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
        _wd_.coreLog(" > COMPALYSE ERROR ON DESKTOP SOUP CLEAN", "COMPALYSE") 

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
        adsList = list()
        adexist = 0
        # DESKTOP PARSE ADS ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
        _wd_.coreLog(" > COMPALYSE DESKTOP PARSE ADS FUNCTION ERROR", engineMode)
        
    return adsList, adexist

def topAds(bsoup, btarget, engineMode):
    try:
        top_ad_container = bsoup.find('div', attrs={"id": "tads", "role":"region"})
        if top_ad_container:
            top_header_container = top_ad_container.find('h1')
            if top_header_container:
                return parseAds(top_header_container, btarget, engineMode)
    except Exception as e:
        # DESKTOP TOP ADS ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP TOP ADS FUNCTION ERROR", engineMode) 

    return list(), 0

def bottomAds(bsoup, btarget, engineMode):
    try:
        bottom_ad_container = bsoup.find('div', attrs={"id": "bottomads"}) 
        if bottom_ad_container:
            bottom_header_container = bottom_ad_container.find('h1')
            if bottom_header_container:
                return parseAds(bottom_header_container, btarget, engineMode)
    except Exception as e:
        # DESKTOP BOTTOM ADS ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP BOTTOM ADS FUNCTION ERROR", engineMode)

    return list(), 0
   
def get_cite(block, engineMode):
    citeLink = []

    try:
        citeBlock = block.find('cite')
        if citeBlock:
            for cLink in citeBlock:
                if cLink.name is None:
                    citeLink.append(cLink)
                else:
                    citeLink.append(cLink.get_text())

    except Exception as e:
        citeLink = []
        # DESKTOP CITE ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP CITE FUNCTION ERROR", engineMode)

    return citeLink 

def get_title(block, engineMode): 
    titleBlock = ""

    try:
        titleBlock = block.get_text()
    except Exception as e:
        titleBlock = ""
        # DESKTOP TITLE ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP TITLE FUNCTION ERROR", engineMode)

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
        # DESKTOP DESCRIPTION ERROR
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP DESCRIPTION FUNCTION ERROR", engineMode)

    return []

def get_rating(block, engineMode):
    ratingArray = []
    ratingContent = 0
    reviewsContent = 0
    reviewsText = ""

    try:
        ratingReviews = block.find('g-review-stars')
        if ratingReviews:
            children = ratingReviews.parent.findChildren(recursive=False)
            for child in children:
                if child.text.strip() != "":
                    ratingArray.append(str(re.sub("[^0-9a-z.]","",child.text.lower().strip())))
            if len(ratingArray) > 0:
                for value in ratingArray:
                    if "rating" in value:
                        ratingContent = re.sub("[^0-9.]","",value)
                        ratingContent = ratingContent if len(_at__common_.trim(ratingContent)) > 0 else 0 
                    elif "review" in value: 
                        reContent = re.sub("[^0-9]","",value).strip() 
                        reviewsContent = reContent if len(_at__common_.trim(reContent)) > 0 else 0 
                        reviewsText = str(reviewsContent)+" reviews"
                    elif "vote" in value: 
                        reContent = re.sub("[^0-9]","",value).strip() 
                        reviewsContent = reContent if len(_at__common_.trim(reContent)) > 0 else 0  
                        reviewsText = str(reviewsContent)+" votes"
    except Exception as e:
        ratingContent = 0
        reviewsContent = 0
        reviewsText = "" 
        # DESKTOP RATINGS ERROR 
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
        _wd_.coreLog(" > COMPALYSE DESKTOP RATINGS FUNCTION ERROR", engineMode) 
    
    return ratingContent, reviewsContent, reviewsText

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
            # START OF OUTER FEATURED SNIPPET CHECK
            if postdata['featured_snippet'] == True:
                if 'featured_box' in xpdTotalContent:
                    if 'link' in xpdTotalContent['featured_box']:
                        keywordLink = xpdTotalContent['featured_box']['link']

                        if keywordLink and mongoFlag == 0:
                            # RANK INCREMENT
                            postdata['rank'] += 1

                            if keywordLink.find(targetLink) > -1:
                                if extract_domain(keywordLink) == extract_domain(keywordTarget):  
                                    mongoLiveRank = postdata['rank']
                                    keywordTarget = keywordLink 
                                    mongoFlag = 2
            # END OF OUTER FEATURED SNIPPET CHECK

            urlList = []
            urlList.append(targetLink)
            gMainClassBodyContents = [ele for ele in urlList if(ele in str(centerdata.contents))]  if centerdata else ""
            
            center_block_data = centerdata.find_all("div", recursive= False) 
            if len(center_block_data):

                # MAIN ITERATION BEGINS (RANK)
                for center_block in center_block_data:
                    loopCount += 1

                    if not center_block.attrs.get('id'): # rhs knowledge panel removed in rank
                        # gClass = center_block.find_all('div', class_='yuRUbf')
                        gClass = center_block.find_all('h3', class_='LC20lb') 
                        if gClass:
                            anchors_flag = 0
                            
                            # SUB ITERATION BEGINS
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
                                                            "title" : get_title(gSubClass, engineMode),
                                                            "desc": get_desc(center_block, descFlag, engineMode),
                                                            "cite": get_cite(center_block, engineMode), 
                                                            "img": ""
                                                        }
                                                    })                                   
                                        # INNER FEATURED SNIPPETS CHECK ENDS

                                        if keywordLink and mongoFlag == 0 and bool(gMainClassBodyContents):
                                            if keywordLink.find(targetLink) > -1:
                                                if extract_domain(keywordLink) == extract_domain(keywordTarget): 
                                                    postdata['rank'] += 1 
                                                    keywordTarget = keywordLink
                                                    mongoFlag = 1
                                                
                                                if mongoFlag == 1:
                                                    mongoLiveRank = postdata['rank']
                                                    anchors_flag += 1

                                                    ratingContent, reviewsContent, reviewsText = get_rating(center_block, engineMode)  

                                        # RANK INCREMENT
                                        if anchors_flag < 1: 
                                            postdata['rank'] += 1

                            # RANK ITERATION ENDS
                            if mongoFlag > 0: 
                                break

                    # CHECKING FOR THE DOMAIN EXIST IN THE SOUP STRING
                    if bool(gMainClassBodyContents) == False and (postdata['featured_snippet'] == True or postdata['rank'] > 3):
                        break 
                # MAIN ITERATION ENDS (RANK)

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
        _wd_.coreLog(" > COMPALYSE DESKTOP RANK PARSE DATA FUNCTION ERROR", engineMode)

    return errorValue

# NEW STRUCTURE
def engineParseData(engineMode, soupdata, postdata):
    # GOOGLE CHECKLIST STARTS
    top_container = "rcnt"
    center_container = "rso"
    # GOOGLE CHECKLIST ENDS

    try: 
        postdata['featured_snippet'] = False
        lang = postdata['language'] 
        __cp_kid__ = postdata['id']
        _bot__language_ = _at__common_.__bot_language__(lang)

        if soupdata and engineMode == "COMPALYSE": 
            bsoup = cleanMe(soupdata, lang) 

            # ALL SNIPPETS
            xpdTotalContent = {}
            adPosition = "" 
            gSnipLink = "" 
            adsTopList = [] 
            adsBottomList = [] 

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
                ("TARGET",targetLink),
            ]) 

            # RESULTS PARSE
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
                                                "title" : get_title(anchors, engineMode),
                                                "desc": get_desc(center_block, "featured", engineMode), 
                                                "cite": get_cite(gClass, engineMode),
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
                                _wd_.coreLog(" > DESKTOP - NO DOCUMENTS FOUND ERROR >> CP_KID "+str(__cp_kid__), engineMode) 
                                return 1
                            else:
                                pass 

                    if flager == 4001: 
                        # UNEXPECTED DESKTOP RANK ERROR OCCURED 
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > DESKTOP - UNEXPECTED ERROR ON RANK >> CP_KID "+str(__cp_kid__), engineMode)
                    elif flager == 4002:
                        # NO DATA SET INSIDE RSO
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > DESKTOP - NO DATA SET INSIDE RSO >> CP_KID "+str(__cp_kid__), engineMode)
                    else:
                        # GOOGLE PAGE ERROR 
                        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                        _wd_.coreLog(" > DESKTOP - RSO - GOOGLE PAGE FORMAT ERROR >> CP_KID "+str(__cp_kid__), engineMode)

                    return True
                    # return _wd_.coreCondition(engineMode, 1, postdata)

                else:
                    # GOOGLE PAGE ERROR - RCNT
                    # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
                    _wd_.coreLog(" > DESKTOP - RCNT - NO CHILDRENS ERROR >> CP_KID "+str(__cp_kid__), engineMode) 
                    return True
                    # return _wd_.coreCondition(engineMode, 1, postdata)
            else:
                _wd_.coreLog(" > DESKTOP - RCNT - ERROR >> CP_KID "+str(__cp_kid__), engineMode) 
                # return _wd_.coreCondition(engineMode, 1, postdata) 
                return True

    except Exception as e: 
        # GOOGLE DESKTOP PARSER ERROR 
        # UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
        _wd_.coreLog(" > COMPALYSE DESKTOP ENGINE PARSE DATA FUNCTION ERROR >> ERROR = "+str(e)+" >>> CP_KID "+str(__cp_kid__), engineMode)  

    return 0