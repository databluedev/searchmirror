from django.conf import settings as _def_ 

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_
from project.machine.models import KeywordResearch as _kw__research_

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_
from project.machine.submodels.researchmodels import DKeywordResearch as _dK__research_

from bs4 import BeautifulSoup 
import urllib, requests 
import sys, os, random
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse 

from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine.research import automation_rDarser as _rD__parser_
import concurrent.futures as _automation__futures_

def _trim_(_value_):
	return _value_.strip()

def __append_keyword__(_data_value_):
	_keyword__list_ = list()
	if len(_data_value_):
		_data_value_ = str(_trim_(_data_value_))
		_keyword__list_.append(_data_value_)
		_keyword__list_.append(_data_value_ + " ")

	return _keyword__list_

# AUTOMATION GOOGLE ON TYPE XML VALIDATION
def __neural_xml_bot_validation__(_engine__mode_, _ts_soup_, _ts_id_): 
	_ts__keywords_ = list()
	_ts__error__message_ = ""

	try:
		if _ts_soup_:
			_content__top_ = _ts_soup_.find("toplevel")
			if _content__top_:
				_content__data_ = _content__top_.findChildren("suggestion", attrs={'data': True}, recursive=True)
				_content__data__length_ = len(_content__data_)

				if _content__data__length_:
					for _single__data_ in _content__data_:
						_ts__keywords_.append(_single__data_["data"])
				else:
					_ts__error__message_= "ONTYPE RESEARCH: NO SUGGESTION FOUND"
			else:
				_ts__error__message_ = "ONTYPE RESEARCH: TOP LEVEL XML PAGE VALIDATION ERROR"
		else:
			_ts__error__message_ = "ONTYPE RESEARCH: NO DATA EXISTS IN THE SOUP TEXT"
		if len(_ts__error__message_):
			_mode_ = str(_engine__mode_).upper()
			_wd_.coreLog("> "+_mode_+" - "+str(_ts__error__message_)+" >> KEYWORD ID: "+str(_ts_id_), "ERROR")

	except Exception as _exp_: 
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog("> "+_mode_+" - NEURAL XML PAGE VALIDATION FUNCTION ERROR >> KEYWORD ID: "+str(_ts_id_)+" >>> ERROR MESSAGE: "+ str(_exp_), "ERROR")
	
	return _ts__keywords_

# ON TYPE RESEARCH STAGE 2
def __neural_type_search_request__(_ts_session_, _ts_data_):
	_ts__list_ = list()
	_ts__mode_ = _ts_data_['_ts_mode_']
	_ts__url_ = _ts_data_['_ts_url_']
	_ts__id_ = str(_ts_data_['_ts_id_']) 
	try:
		if _ts__url_ and _ts__mode_ and _ts__id_.isdigit(): 
			with _ts_session_.get(_ts__url_, headers = _at__proxy_.__automation_desktop_headers__(), timeout=(10, 30)) as _ts__resp_:
				if hasattr(_ts__resp_, 'status_code'):
					if _ts__resp_.status_code == 200:
						_ts__soup_ = BeautifulSoup(_ts__resp_.text, "html.parser")
						_ts__list_ = __neural_xml_bot_validation__(_ts__mode_, _ts__soup_, _ts__id_) 

	except Exception as _exp_:
		_mode_ = str(_ts__mode_).upper() 
		_wd_.coreLog("> "+_mode_+" - NEURAL TYPE SEARCH REQUEST FUNCTION ERROR >> KEYWORD ID: "+str(_ts__id_)+" >>> ERROR MESSAGE: "+ str(_exp_), "ERROR")         
 
	return _ts__list_

# ON TYPE RESEARCH STAGE 1
def __neural_type_search_call__(_engine__mode_, _ot__data_): 
	_ts__search__keyword__list_ = list()

	try:
		if len(_ot__data_):
			_ts__keywords_ = __append_keyword__(_ot__data_['text'])
			_ts__keywords__length_ = len(_ts__keywords_)
			_ts__search__url__list_ = list()

			if _ts__keywords__length_: 
				for _each__keyword_ in _ts__keywords_:
					_keyword__query_ = format(_each__keyword_) 
					_keyword__query_ = urllib.parse.quote_plus(_keyword__query_)
					
					_ts__data_ = dict() 
					_ts__data_['_ts_id_'] = _ot__data_['id']  
					_ts__data_['_ts_mode_'] = _engine__mode_ 
					_ts__data_['_ts_url_'] = "https://www."+_trim_(_ot__data_['region'])+"/complete/search?gl="+_trim_(_ot__data_['iso'])+"&q="+_keyword__query_+"&oq="+_keyword__query_+"&hl="+_trim_(_ot__data_['language'])+"&output=toolbar"
					
					_ts__search__url__list_.append(_ts__data_) 
					del(_ts__data_)
			
			if _ts__search__url__list_ and _ts__keywords__length_:
				
				with _automation__futures_.ThreadPoolExecutor(max_workers=_ts__keywords__length_) as _task__executor_:
					with requests.Session() as session:
						_task__executor__result_ = _task__executor_.map(__neural_type_search_request__, [session]*_ts__keywords__length_, _ts__search__url__list_) 

						for _ts__list_  in _task__executor__result_: 
							_ts__search__keyword__list_ += _ts__list_

						del(_task__executor__result_) 
							 
					_task__executor_.shutdown(wait=False)

				if (len(_ts__search__keyword__list_)): 
					_ts__search__keyword__list_ = list(set(_ts__search__keyword__list_))
					_ts__search__keyword__list_.sort()

				del(_task__executor_)

	except Exception as _exp_: 
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog(" > "+_mode_+" - NEURAL TYPE SEARCH CALL FUNCTION ERROR >> ERROR MESSAGE: "+ str(_exp_), "ERROR") 
	
	return _ts__search__keyword__list_
