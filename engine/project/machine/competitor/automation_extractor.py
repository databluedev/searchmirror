from django.shortcuts import render
from django.conf import settings as _def_

import urllib
import sys, os, random 
import requests
from bs4 import BeautifulSoup 

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine.competitor import automation_cDarser as _cD__parser_, automation_cMarser as _cM__parser_

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# AUTOMATION STAGE 3
def __neural_competitor_data_collector__(_kw__data_):
	_task__data_= {}	
	_task__data_['id'] = _kw__data_.id  
	_task__data_['fk_user_id'] = _kw__data_.fk_user_id 
	_task__data_['fk_group_id'] = _kw__data_.fk_group_id  
	_task__data_['fk_keyword_id'] = _kw__data_.fk_keyword_id    
	_task__data_['cp_project_id'] = _kw__data_.fk_cp_project_id
	_task__data_['language'] = _kw__data_.language_code
	_task__data_['platform'] = _kw__data_.platform    		
	_task__data_['target'] = _kw__data_.target

	return _task__data_

# AUTOMATION STAGE 4
def __neural_competitor_page_request__(_mode_, _kw_id_, _kw_collections_):
	# _kw_id_ is STRING
	try:
		if _kw_id_ in _kw_collections_:
			_kwc__id_ = _kw_collections_[_kw_id_]['fk_keyword_id']
			_kwc__platform_ = _kw_collections_[_kw_id_]['platform']

			_automation__soup_ = ""
			_search__file_ = ""
			
			if str(_kwc__id_).isdigit(): 
				if _kwc__platform_ == "desktop":
					_search__file_ = os.getcwd()+"/project/files/desktop/searchFile__"+str(_kwc__id_)+".html"
				elif _kwc__platform_ == "mobile":
					_search__file_ = os.getcwd()+"/project/files/mobile/searchFile__"+str(_kwc__id_)+".html" 

			if len(_search__file_):
				_soup_ = ""
				if os.path.exists(_search__file_):
					with open(_search__file_) as reader:
						_soup_ = reader.read().strip()

				if len(_soup_):
					_automation__soup_ = BeautifulSoup(_soup_, "html.parser") 
					_kw_collections_[_kw_id_]['status'] = str('200')
					_kw_collections_[_kw_id_]['response'] = _automation__soup_   
					return _kw_collections_[_kw_id_]
				else:
					_at__common_.__change_competitor_keyword_call_status__(int(_kw_id_), "fail")
					# FILE WITH ID NOT FOUND 
					# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON

	except Exception as e:
		pass
		# COMP PAGE REQUEST ERROR WITH EXCEPTION AND DETAILS.
		# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON

	return False 

# AUTOMATION STAGE 5
def __neural_competitor_page_parser__(_mode_, _index_, _kw__data_):  
	try:
		if _index_ in _kw__data_:
			_engine__parse__result_ = ""
			
			_at__common_.__change_competitor_keyword_call_status__(int(_index_), "busy")  

			_kw__soup_ = _kw__data_[_index_]['response']
			_kw__data_[_index_]['response'] = ""
			_kw__data_[_index_]['status'] = ""

			if _kw__data_[_index_]['platform'].lower() == "desktop":
				_engine__parse__result_ = _cD__parser_.engineParseData(_mode_, _kw__soup_, _kw__data_[_index_]) 
			elif _kw__data_[_index_]['platform'].lower() == "mobile":
				_engine__parse__result_ = _cM__parser_.engineParseData(_mode_, _kw__soup_, _kw__data_[_index_])  
			else:
				## WATCHDOG UN-NOTED ISSUE ON PLATFORM DEVICE.
				_wd_.coreLog(" !!! PLATFORM NOT AVAILABLE ON COMPETITOR KEYWORD ID "+str(_kw__data_[_index_]['id']), _mode_) 
				pass

			if _engine__parse__result_ == 1:
				_at__common_.__change_competitor_keyword_call_status__(int(_index_), "done") 
				return True
			else:
				_at__common_.__change_competitor_keyword_call_status__(int(_index_), "fail") 
				return True 
	except Exception as e: 
		pass 

	return False
