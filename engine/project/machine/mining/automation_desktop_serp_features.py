from django.conf import settings

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_
from project.machine.models import KeywordResearch as _kw__research_

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_
from project.machine.submodels.serpmodels import DCompProject as _dC__project_, DCompKeyword as _dC__keyword_
from project.machine.submodels.researchmodels import DKeywordResearch as _dK__research_

import requests, json, time, re 
from bs4 import BeautifulSoup
from urllib import parse 
import sys, os, random 
from datetime import datetime, date
from urllib.parse import urlparse 

from project.machine import watchdog as _wd_, automation_common as _at__common_ 

def __find_url_from_string__(_engine__mode_, _string__url_, _data__id_):
    try:
        validateUrlRegex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(validateUrlRegex,_string__url_)      
        return [x[0] for x in url]
    except Exception as e:
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - KEYWORD - FIND URL FROM STRING FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return list()

def __extract_domain__(_engine__mode_, url, _data__id_, _remove__http_=True): 
    try:
        domain_name = "" 
        uri = urlparse(url)
        if _remove__http_:
            if uri.netloc: 
                domain_name = f"{uri.netloc}".replace("www.", "") 
            else:
                domainDivision = f"{uri.path}".replace("www.", "").split('/')
                domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision    
        else:
            domain_name = f"{uri.netloc}".replace("www.", "")
    except Exception as e:
        _mode_ = str(_engine__mode_).upper() 
        _wd_.coreLog("> "+_mode_+" - KEYWORD - EXTRACT DOMAIN FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return domain_name

def __organic_related_keywords__(_engine__mode_, _source_, _data__id_): 
    _related__array_ = list()
    try:
        _related_stuff_container_ = _source_.find('div', attrs={"id": "botstuff"})

        if _related_stuff_container_:
            _related_anchor_container_ = _related_stuff_container_.find_all("a", class_="R0xfCb")
            if len(_related_anchor_container_):
                for _related_anchor_block_ in _related_anchor_container_: 
                    _related__array_.append(_related_anchor_block_.text.lower())

    except Exception as e:
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - KEYWORD - GOOGLE SERP RELATED KEYWORDS ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return _related__array_

# NEW STRUCTURE 
def __parse_ads__(_engine__mode_, _source_, _target_, _data__id_): 
    adsList = list()
    adexist = 0
    adSingleLink = None

    try:
        children = _source_.parent.findChildren("div", class_="uEierd", recursive=False)
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
                            e_domain = __extract_domain__(_engine__mode_, adSingleLink, _data__id_).strip()
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
                        parseExtract = __find_url_from_string__(_engine__mode_, gSnipAnchors.text, _data__id_)
                        adSingleLink = parseExtract[0] if len(parseExtract) else None
                    else:
                        adSingleLink = ''.join(parseExtract).strip()

                if adexist == 0 and adSingleLink:
                    if adSingleLink.find(_target_) > -1:  
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
        
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP PARSE ADS FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return adsList, adexist

def __organic_top_ads__(_engine__mode_, _source_, _target_, _data__id_):
    try:
        top_ad_container = _source_.find('div', attrs={"id": "tads", "role":"region"})
        if top_ad_container:
            top_header_container = top_ad_container.find('h1')
            if top_header_container:
                return __parse_ads__(_engine__mode_, top_header_container, _target_, _data__id_)

    except Exception as e:        
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP TOP ADS FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return list(), 0

def __organic_bottom_ads__(_engine__mode_, _source_, _target_, _data__id_):
    try:
        bottom_ad_container = _source_.find('div', attrs={"id": "bottomads"}) 
        if bottom_ad_container:
            bottom_header_container = bottom_ad_container.find('h1')
            if bottom_header_container:
                return __parse_ads__(_engine__mode_, bottom_header_container, _target_, _data__id_)

    except Exception as e:
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP BOTTOM ADS FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

    return list(), 0

def __organic_cite__(_engine__mode_, _source_, _data__id_):
    citeLink = list()

    try:
        citeBlock = _source_.find('cite')
        if citeBlock:
            for cLink in citeBlock:
                if cLink.name is None:
                    citeLink.append(cLink)
                else:
                    citeLink.append(cLink.get_text())

    except Exception as e:
        citeLink = list()

        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP ORGANIC CITE FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR") 

    return citeLink 

def __organic_title__(_engine__mode_, _source_, _data__id_):  
    titleBlock = ""

    try:
        titleBlock = _source_.get_text()

    except Exception as e:
        titleBlock = ""
        
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP ORGANIC TITLE FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR") 

    return titleBlock if len(titleBlock) else "" 

def __organic_desc_(_engine__mode_, _source_, _flag_, _data__id_):
    try:
        if _flag_ == "block":
            descBlock = _source_.find('div', class_= "VwiC3b")
            if descBlock:
                descContent = descBlock.get_text()
                if descContent:
                    return [descContent.strip()]

            descBlock = _source_.find('div', attrs={'data-snf': 'nke7rc'})
            if descBlock:
                descContent = descBlock.get_text()
                if descContent:
                    return [descContent.strip()]

            descBlock = _source_.find('div', class_= "IsZvec")
            if descBlock: 
                descBlock = descBlock.find('div')
                if descBlock: 
                    return [descBlock.get_text()]

            descBlock = _source_.find('div', class_= "Uroaid")
            if descBlock:
                descBlock = descBlock.parent.findChildren(recursive=False)
                if descBlock:
                    videoDesc = []
                    for dsc in descBlock:
                        videoDesc.append(dsc.get_text()) 
                    return videoDesc
                    
        elif _flag_ == "featured":
            descBlock = _source_.find("div", attrs={'role': True, 'aria-level': "3"})
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
        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP ORGANIC DESCRIPTION FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR") 

    return list() 

def __organic_rating__(_engine__mode_, _source_, _data__id_): 
    ratingArray = list()
    ratingContent = 0
    reviewsContent = 0
    reviewsText = ""

    try:
        ratingReviews = _source_.find('g-review-stars')
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

        _mode_ = str(_engine__mode_).upper()
        _wd_.coreLog("> "+_mode_+" - DESKTOP ORGANIC RATINGS FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR") 
    
    return ratingContent, reviewsContent, reviewsText

