from django.conf import settings

import requests, json, time, re
from urllib import parse 
import sys, os, random 
from datetime import datetime, date
from urllib.parse import urlparse 

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine.mining import automation_desktop_serp_features as _at__desk__serp_  
from project.machine.research import automation_on_type_search_call as _tS__parser_
from project.machine.bot import clean as _clean_

from project.machine.research import automation_rStorage as _centralised_

def __rank_parse_data__(_engine__mode_, centerdata, _r__data_, targetLink, xpdTotalContent, _mongo__results_): 
    errorValue = 0

    try:
        _r__kid_ = _r__data_['id'] 

        top_organic_result = False
        loopCount = 0
        ratingContent = 0
        reviewsContent = 0
        reviewsText = "" 
        _inner__data__count_ = 0 

        if centerdata:
            if _r__data_['featured_snippet'] == True:
                _inner__data__count_+= 1
                top_organic_result = True

            center_block_data = centerdata.find_all("div", recursive= False) 
            if len(center_block_data):

                if top_organic_result == False:
                    # MAIN ITERATION BEGINS (RANK)
                    for center_block in center_block_data:
                        loopCount += 1

                        if not center_block.attrs.get('id'): # rhs knowledge panel removed in rank
                            gClass = center_block.find_all('h3', class_='LC20lb') 
                            if gClass:
                                                            
                                # SUB ITERATION BEGINS
                                for gSubClass in gClass:
                                    if gSubClass:
                                        descFlag = "block"
                                        anchors = gSubClass.find_parent('a')
                                        if anchors: 
                                            _inner__data__count_ += 1
                                            keywordLink = anchors['href']
                                            
                                            # INNER FEATURED SNIPPETS CHECK
                                            if _r__data_['featured_snippet'] == False:
                                                featured_anchors = anchors.find_parent('div', class_="xpdopen")
                                                
                                                if featured_anchors:
                                                    featured_inner_anchors = anchors.find_parent('div', class_="yuRUbf")
                                                    if featured_inner_anchors:
                                                        _r__data_['featured_snippet'] = True 
                                                        top_organic_result = True
                                                                                                        
                                                        xpdTitle = "snip"
                                                        descFlag = "featured" 
                                                        xpdTotalContent.update({
                                                            xpdTitle : {
                                                                "lk" :  keywordLink,
                                                                "tt" : _at__desk__serp_.__organic_title__(_engine__mode_, gSubClass, _r__kid_),
                                                                "ds": _at__desk__serp_.__organic_desc_(_engine__mode_, center_block, descFlag, _r__kid_),
                                                                "mt": _at__desk__serp_.__organic_cite__(_engine__mode_, center_block, _r__kid_),
                                                                "rt": ratingContent,
                                                                "rv": reviewsContent,  
                                                                "dt": str(datetime.now()), 
                                                                "img": "",
                                                                "typ": "featured"
                                                            }
                                                        })                                   
                                            # INNER FEATURED SNIPPETS CHECK ENDS
                                            if keywordLink and top_organic_result == False: 
                                                ratingContent, reviewsContent, reviewsText = _at__desk__serp_.__organic_rating__(_engine__mode_, center_block, _r__kid_)

                                                xpdTitle = "snip" 
                                                xpdTotalContent.update({
                                                    xpdTitle : {
                                                        "lk": keywordLink,
                                                        "tt": _at__desk__serp_.__organic_title__(_engine__mode_, gSubClass, _r__kid_),
                                                        "ds": _at__desk__serp_.__organic_desc_(_engine__mode_, center_block, descFlag, _r__kid_),
                                                        "mt": _at__desk__serp_.__organic_cite__(_engine__mode_, center_block, _r__kid_),
                                                        "rt": ratingContent, 
                                                        "rv": reviewsText,  
                                                        "dt": str(datetime.now()),
                                                        "img": "",
                                                        "typ": "organic"
                                                    }
                                                })
                                                top_organic_result = True
                                # SUB ITERATION ENDS

                                if top_organic_result == True:
                                    break

                        # CHECKING FOR THE TOP FIRST ORGANIC RESULT WITHIN FIRST THREE ITERATIONS.
                        if loopCount > 3:
                            break                         
                    # MAIN ITERATION ENDS (RANK) 

                # RESULT UPDATE      
                _mongo__results_.update([
                    ("SNIPPET_DETAILS", xpdTotalContent),
                ])

                # APPEND TO MONGO
                _mp__result_ = _centralised_._mongo__push_(_engine__mode_, _mongo__results_, _r__data_) 

                if _mp__result_ and _inner__data__count_ > 0:
                    return 1
                
                if _inner__data__count_ == 0:
                    errorValue = 4003
            else:
                errorValue = 4002
    
    except Exception as e:
        errorValue = 5000
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP - RANK PARSE DATA FUNCTION ERROR >> KEYWORD ID: "+str(_r__kid_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return errorValue

# NEW STRUCTURE
def __engine_parse_data__(_engine__mode_, _r__soup_, _r__data_): 
    # GOOGLE CHECKLIST STARTS
    top_container = "rcnt"
    center_container = "rso"
    _r__error__message_ = ""
    # GOOGLE CHECKLIST ENDS

    try: 
        _r__kid_ = _r__data_['id'] 
        _r__uid_ = _r__data_['fk_user_id'] 
        _r__gid_ = _r__data_['fk_group_id'] 
        _ts__array_ = _tS__parser_.__neural_type_search_call__(_engine__mode_, _r__data_)  

        # print("_ts__array_", _ts__array_)
        _r__lang_ = _r__data_['language']
        _mode_ = str(_engine__mode_).upper() 

        # DATA COLLECTIONS UPDATE. 
        _r__data_['featured_snippet'] = False 

        _bot__language_ = _clean_.__page_language_based_snippet__(_engine__mode_, _r__lang_, _r__kid_)

        if _r__soup_ and _engine__mode_ == "RESEARCH":
            _r__soup_ = _clean_.__page_desktop_cleaner__(_engine__mode_, _r__soup_, _r__lang_, _r__kid_)

            # SHOW ALSO RESULTS FOR
            resultAboutExists = _r__soup_.find("div", {"id": "result-stats"}) 
            resultAbout = "-" 

            if resultAboutExists:  
                resultContent = resultAboutExists.contents 
                if len(resultContent) >= 1:
                    resultAbout = re.sub("[^0-9,. ]","",resultContent[0]).strip()
                    resultAbout = resultAbout.replace(".", ",").replace(" ", ",")

            # ALL SNIPPETS
            serpFeaturesDict = []  
            xpdTotalContent = {}

            adPosition = "" 
            gSnipLink = "" 
            adsTopList = [] 
            adsBottomList = [] 
            gSnipPeopleAsk = False

            _mongo__results_ = {}
            panelFlag = 0

            # TARGET DOMAIN EXTRACTED
            targetLink = _at__desk__serp_.__extract_domain__(_engine__mode_, _r__data_['target'], _r__kid_)

            gAdLinks = _r__soup_.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) 

            for gAdLink in gAdLinks:
                headerTagText = gAdLink.text.replace(' ','_').lower()

                if headerTagText == _bot__language_['_complementary_']: 
                    panelFlag = 1

                # KNOWLEDGE PANEL
                if _bot__language_['_description_'] in headerTagText and panelFlag == 1:
                    if "wikipedia" in gAdLink.parent.parent.text.replace(' ','_').lower(): 
                        xpdTitle = "knw"                         
                        serpFeaturesDict.append(xpdTitle) 

                # SITE LINKS 
                if gAdLink.name == "h2" and _bot__language_['_site__links_'] in headerTagText: 
                    tableFlag = gAdLink.parent.find('table')
                    if tableFlag:
                        if len(tableFlag.find_all('h3')) > 1 and str(tableFlag).count(targetLink) > 0: 
                            xpdTitle = "slrs"    
                            serpFeaturesDict.append(xpdTitle) 

                # IMAGES PACK
                if gAdLink.name == "h3" and _bot__language_['_images_'] in headerTagText:
                    xpdTitle = "imrs"
                    serpFeaturesDict.append(xpdTitle) 

                # MAPS PACK
                if gAdLink.name == "h2" and _bot__language_['_map_'] == headerTagText:
                    xpdTitle = "mprs"
                    serpFeaturesDict.append(xpdTitle)

                # LOCAL RESULTS PACK
                if gAdLink.name == "h2" and _bot__language_['_local_'] == headerTagText: 
                    xpdTitle = "lcrs"
                    serpFeaturesDict.append(xpdTitle)

                # TWITTER RESULTS PACK
                if gAdLink.name == "h2" and _bot__language_['_twitter_'] == headerTagText:
                    xpdTitle = "twrs" 
                    serpFeaturesDict.append(xpdTitle)

                # VIDEOS RESULTS PACK
                if gAdLink.name == "h3" and _bot__language_['_videos_'] == headerTagText: 
                    xpdTitle = "vdrs"  
                    serpFeaturesDict.append(xpdTitle)

                # TOP STORIES OR NEWS RESULTS PACK
                if gAdLink.name == "h3" and _bot__language_['_top__stories_'] == headerTagText:
                    xpdTitle = "nwrs"  
                    serpFeaturesDict.append(xpdTitle)
                    
                # PEOPLE ALSO ASK OR RELATED QUESTIONS.
                if gAdLink.name == "h3" and _bot__language_['_people__ask_'] in headerTagText:
                    gSnipPeopleAsk = True
                    xpdTitle = "rqrs"  
                    serpFeaturesDict.append(xpdTitle)

            # NEW PEOPLE ALSO ASK OR RELATED QUESTIONS UPDATE - DECEMBER 2022.
            if gSnipPeopleAsk == False:
                gPeopleAskBlocks = _r__soup_.find_all("div", attrs={"aria-level": "2", "role":"heading"})  
                if gPeopleAskBlocks:
                    for gSingleBlock in gPeopleAskBlocks:
                        headerTagText = gSingleBlock.text.replace(' ','_').lower() 
                        if gSingleBlock.name == "div" and _bot__language_['_people__ask_'] in headerTagText:
                            gSnipPeopleAsk = True
                            xpdTitle = "rqrs"  
                            serpFeaturesDict.append(xpdTitle)
                            break

            # ADS
            adsTopList, adPresence = _at__desk__serp_.__organic_top_ads__(_engine__mode_, _r__soup_, targetLink, _r__kid_)  
            if adPresence:
                adPosition = "top"

            adsBottomList, adPresence = _at__desk__serp_.__organic_bottom_ads__(_engine__mode_, _r__soup_, targetLink, _r__kid_) 
            if adPresence:
                adPosition = "bottom"

            if len(adsTopList) > 0 or len(adsBottomList) > 0:
                xpdTitle = "ads"
                
                serpFeaturesDict.append(xpdTitle)
                xpdTotalContent.update({
                    xpdTitle : {
                        "top_result": adsTopList,
                        "bottom_result": adsBottomList, 
                        "status": "yes" if adPosition in ["top", "bottom"] else "no",
                        "top_count": len(adsTopList),
                        "bottom_count": len(adsBottomList),
                        "present": adPosition
                    }
                })

            # ONLY FOR KEYWORD RESEARCH RESULTS
            xpdTitle = "feat"
            xpdTotalContent.update({ 
                xpdTitle : serpFeaturesDict, 
                "snip": dict(), 
                "srs": resultAbout
            })

            # RESULTS PARSE
            gMainClassBody = _r__soup_.find("body")
            top_container_block = _r__soup_.find("div", {"id": top_container}) 
            if top_container_block:
                top_container_child = top_container_block.findChildren(recursive=False) 

                if top_container_child:
                    flager = 0

                    # START OF RSO SEGMENT
                    for container_child in top_container_child:
                        center_container_block = container_child.find("div", {"id": center_container}) 

                        if center_container_block:
                            _mongo__results_.update([ 
                                ("ID", _r__kid_),
                                ("RELATED_DETAILS", _at__desk__serp_.__organic_related_keywords__(_engine__mode_, _r__soup_, _r__kid_)),
                                ("ONTYPE_DETAILS", _ts__array_)
                            ])
                            flager = __rank_parse_data__(_engine__mode_, center_container_block, _r__data_, targetLink, xpdTotalContent, _mongo__results_)
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

                                        xpdTitle = "snip"
                                        gSubClass = anchors.find('h3', class_='LC20lb')
                                        xpdTotalContent.update({
                                            xpdTitle : {
                                                "lk" :  keywordLink,
                                                "tt" : _at__desk__serp_.__organic_title__(_engine__mode_, gSubClass, _r__kid_), 
                                                "ds": _at__desk__serp_.__organic_desc_(_engine__mode_, center_block, "featured", _r__kid_),
                                                "mt": _at__desk__serp_.__organic_cite__(_engine__mode_, gClass, _r__kid_),
                                                "rt": 0,
                                                "rv": 0, 
                                                "dt": str(datetime.now()), 
                                                "img": "",
                                                "typ": "featured"
                                            }
                                        })
                                        _r__data_['featured_snippet'] = True
                                # OUTER FEATURED SNIPPETS ENDS
                    # END OF RSO SEGMENT
                    
                    # print(" flager ", flager)
                    if flager == 1:
                        return flager
                    else:
                        # CHECK NO DOCUMENTS MATCH
                        gNDF = gMainClassBody.find('div', attrs={"id":"topstuff"})  
                        if gNDF:
                            gNDF0 = gNDF.find('div', class_="card-section")
                            gNDF1 = gNDF.find(attrs={"role": True, "aria-level":"3"})
                            gNDF2 = gNDF.find('ul')

                            _mongo__results_.update([
                                ("ID", _r__kid_), 
                                ("SNIPPET_DETAILS", xpdTotalContent),
                                ("RELATED_DETAILS", list()),
                                ("ONTYPE_DETAILS", _ts__array_)
                            ])

                            _mp__result_ = _centralised_._mongo__push_(_engine__mode_, _mongo__results_, _r__data_)

                            if gNDF and gNDF0 and gNDF1 and gNDF2: 
                                _wd_.coreLog("> "+_mode_+" - DESKTOP - NO DOCUMENTS FOUND >> KEYWORD ID: "+str(_r__kid_), "ERROR")                                 
                                return 1
                        else:
                            _r__error__message_ = " - DESKTOP - NO DOCUMENT MATCHING CONDITION FAILED, GOOGLE PAGE FORMAT ERROR" 

                    if flager == 4002:
                        # NO DATA SET INSIDE RSO
                        _r__error__message_ = " - DESKTOP - NO DATA SET INSIDE RSO, GOOGLE PAGE FORMAT ERROR"
                    elif flager == 4003:
                        # NO DATA SET INSIDE RSO
                        _r__error__message_ = " - DESKTOP - NO H3 TAG WAS EXISTS, GOOGLE PAGE FORMAT ERROR"
                    else:
                        # GOOGLE PAGE ERROR 
                        _r__error__message_ = " - DESKTOP - GOOGLE PAGE FORMAT ERROR"
                else:
                    # GOOGLE PAGE ERROR - RCNT - NO CHILDRENS
                    _r__error__message_ = " - DESKTOP - RCNT - NO CHILDRENS, GOOGLE PAGE FORMAT ERROR"
            else:
                # GOOGLE PAGE ERROR - RCNT
                _r__error__message_ = " - DESKTOP - RCNT - NOT FOUND, GOOGLE PAGE FORMAT ERROR" 

        else:
            # NO SOUP HTML DATA OR INVALID ENGINE MODE ACCESS.
            _r__error__message_ = " - DESKTOP - SOUP OR ENGINE MODE COMPARISON ERROR"  


        if len(_r__error__message_):
            _mode_ = str(_engine__mode_).upper()
            _wd_.coreLog("> "+_mode_+ str(_r__error__message_) + " >> KEYWORD ID: "+str(_r__kid_), "ERROR")
            # return _wd_.coreCondition(_engine__mode_, 1, _r__data_)

    except Exception as e:
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP ENGINE PARSE DATA FUNCTION ERROR >> KEYWORD ID: "+str(_r__kid_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return 0