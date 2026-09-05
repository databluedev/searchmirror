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
from project.machine.research import automation_on_type_search_call as _tS__parser_
import concurrent.futures as _automation__futures_


# google_status  - "VOID", "INIT", "SCHD", "FAIL", "DONE"
#		INIT ON PROXY
#		SCHD ON PARSER
# ontype_status  - "VOID", "INIT", "SCHD", "FAIL", "DONE", "START", "STOP", "COMP" 

# RESEARCH STAGE 4
def __neural_research_page_request__(_engine__mode_, _kw_id_): 
	try:
		_automation__soup_ = ""
		_search__file_ = ""
		_engine__parse__result_ = 0
		_mode_ = str(_engine__mode_).upper() 

		_kw__data_ = _kw__research_.objects.filter(__raw__= {'id': int(_kw_id_)}).first() 

		if str(_kw_id_).isdigit():
			_search__file_ = os.getcwd()+"/project/files/research/researchFile__"+str(_kw_id_)+".html"

		if len(_search__file_) and _kw__data_: 
			_soup_ = ""
			if os.path.exists(_search__file_):
				with open(_search__file_) as reader:
					_soup_ = reader.read().strip()

			_task__group__data_ = _gp__record_.objects.filter(__raw__= {'id': _kw__data_.fk_group_id}).values_list('domain_name') 

			if len(_soup_) and _task__group__data_: 
				_automation__soup_ = BeautifulSoup(_soup_, "html.parser") 
				
				_task__data_= {}	
				_task__data_['id'] = _kw__data_.id  
				_task__data_['fk_user_id'] = _kw__data_.fk_user_id 
				_task__data_['fk_group_id'] = _kw__data_.fk_group_id      		
				_task__data_['target'] = _task__group__data_[0] 
				_task__data_['language'] = "en"
				_task__data_['region'] = _kw__data_.region_name
				_task__data_['iso'] = _kw__data_.region_code
				_task__data_['text'] = _kw__data_.search_text

				# print("_task__data_", _task__data_, "\n \n") 

				_engine__parse__result_ = _rD__parser_.__engine_parse_data__("RESEARCH", _automation__soup_, _task__data_)

				if _engine__parse__result_ == 1:
					sd = _at__common_.__change_research_call_status__(int(_kw_id_), "DONE", "both") 
					# AFTER SUCCESS REDUCE COUNT
				else:
					_at__common_.__change_research_call_status__(int(_kw_id_), "FAIL", "google")
					_wd_.coreLog(" > "+_mode_+" - NEURAL RESEARCH ENGINE PARSE DATA CALL BACK RESPONSE ERROR >> KEYWORD ID: "+str(_kw_id_), "ERROR")
					# MAIL ON IT

	except Exception as _exp_: 
		_wd_.coreLog(" > "+_mode_+" - NEURAL RESEARCH PAGE REQUEST FUNCTION ERROR >> KEYWORD ID: "+str(_kw_id_)+" >>> ERROR MESSAGE: "+ str(_exp_), "ERROR") 

	return _engine__parse__result_

def __neural_research_task__(_engine__mode_, _r_record_): 
	_kw_research_url_list_ = list()
	_kw_research_key_list_ = list()
	_kw_research_output_ = list()

	try: 
		if _r_record_:
			for _single_record_ in _r_record_:
				_search_type_ = _at__common_.trim(_single_record_.search_type.lower()) 

				if _search_type_ == "keyword": 
					_scrap__data__length_ = str(10)
					_kw__query_ = format(_at__common_.trim(_single_record_.search_text))
					_kw__query_ = urllib.parse.quote_plus(_kw__query_)

					_kw__id_ = _single_record_.id
					_kw__region_ = _at__common_.trim(_single_record_.region_name)
					_kw__isocode_ = _at__common_.trim(_single_record_.region_code)
					_kw__lang_ = "en-us"
					_kw__delimiter_ = _def_.URL_DELIMITER 
	
					_kw__url_ = "https://www."+_kw__region_+"/search?gl="+_kw__isocode_+"&q="+_kw__query_+"&oq="+_kw__query_+"&hl="+_kw__lang_+"&num="+_scrap__data__length_+"&pws=0"+str(_kw__delimiter_)+str(_kw__id_)

					_kw_research_url_list_.append(_kw__url_)
					_kw_research_key_list_.append(_kw__id_)
					
		_kw_research_parse_key_list_ = _kw_research_key_list_
		_max__key__length_ = len(_kw_research_key_list_) 

		# print("_max__key__length_ ", _max__key__length_)
		# print("_kw_research_key_list_ ", _kw_research_key_list_, "\n\n")  

		if _kw_research_url_list_ and _max__key__length_: 
			# MAX WORKERS PER POOL
			_max__task__workers_ = 5 if _max__key__length_ > 5 else _max__key__length_
			_at__common_.__change_research_call_status_in_list__(_kw_research_key_list_, "INIT")

			with _automation__futures_.ThreadPoolExecutor(max_workers=_max__task__workers_) as _task__executor_:
				with requests.Session() as session:
					_task__executor__result_ = _task__executor_.map(_at__proxy_.__automation_research_request__, [session]*int(_max__key__length_), _kw_research_url_list_) 

					for _r_status_, _r_key_  in _task__executor__result_: 						
						if _r_status_ and _r_key_.isdigit(): 
							_at__common_.__change_research_call_status__(int(_r_key_), "SCHD", "google")
						else:
							_kw_research_parse_key_list_.remove(int(_r_key_)) 
							_at__common_.__change_research_call_status__(int(_r_key_), "VOID", "google")

				del(_kw_research_url_list_) 
				del(_task__executor__result_)
				_task__executor_.shutdown(wait=False)
			del(_task__executor_)

		# print(_kw_research_parse_key_list_) 
		
		_max__key__length_ = len(_kw_research_parse_key_list_) 
		if _max__key__length_:
			with _automation__futures_.ThreadPoolExecutor(max_workers=_max__key__length_) as _task__executor_:
				future_to_url = {_task__executor_.submit(__neural_research_page_request__, _engine__mode_=_engine__mode_, _kw_id_=_kw__key_): _kw__key_ for _kw__key_ in _kw_research_parse_key_list_} 
				# if no needed remove the following line
				for future in _automation__futures_.as_completed(future_to_url): 
					# print("F RESULT ", str(future.result()))
					if str(future.result()) == "1":
						_kw_research_output_.append(future.result()) 
				
				del(future_to_url)
				_task__executor_.shutdown(wait=False)

			del(_kw_research_parse_key_list_) 
			del(_task__executor_)

		# print("_kw_research_output_", _kw_research_output_)
	except Exception as _exp_:
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog(" > "+_mode_+" - NEURAL RESEARCH TASK FUNCTION ERROR >> ERROR MESSAGE: "+ str(_exp_), "ERROR") 
	
	return _kw_research_output_ 

def automation_research_call(_engine__mode_, flag=None):
	_research__flag_ = 0
	try:
		_start__time_ = str(_date__time_.now())
		_max__wait__count_ = 10   # 50 
		_initial__pool__task_ = 5  # 5
		
		# MAX REPEATATIVE CALL FOR EACH FAILED KEYWORD
		_max__loop__call_ = 10

		_wait__count_ = _kw__research_.objects.filter(google_status__in=["INIT", "SCHD"]).count()  
		
		if _wait__count_ < _max__wait__count_:
			_kw__research__task_ = _kw__research_.objects.filter(google_status="VOID", search_type="keyword", research_refresh_count__lt=_max__loop__call_)[0:_initial__pool__task_]
			# _kw__research__task_ = _kw__research_.objects.filter(fk_group_id=6, google_status="VOID", search_type="keyword", research_refresh_count__lt=_max__loop__call_)[0:_initial__pool__task_] 

			_research__dict_ = 0 
			if len(_kw__research__task_): 
				_research__dict_ = len(__neural_research_task__(_engine__mode_, _kw__research__task_))
			
			if _research__dict_ > 0:
				_research__flag_ = 1
			elif len(_kw__research__task_) == 0:
				_research__flag_ = 0
			else:
				_research__flag_ = -1
			
		_end__time_ = str(_date__time_.now())

	except Exception as _exp_: 
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog(" > "+_mode_+" - AUTOMATION RESEARCH CALL FUNCTION ERROR >> ERROR MESSAGE: "+ str(_exp_), "ERROR") 
	
	if _research__flag_ > 0:
		return "COMP", _start__time_, _end__time_
	elif _research__flag_ == 0:
		return "ZERO", _start__time_, _end__time_ 
	else:
		return "FAIL", _start__time_, _end__time_ 

@api_view(['GET']) 
def automation_research_module(request, _ustr_, _kstr_):
	_engine__mode_ = "RESEARCH" 

	try:
		_base__result_, _setting__data_  = _at__common_.__base_validation__(request, _ustr_)
		_start__time_ = ""
		_end__time_ = ""

		if _base__result_ and _kstr_.isdigit():
			_core__mode_ = _at__common_.__ms_record__(_engine__mode_, "_mode__check_")
			
			if _core__mode_ == True:
				_gp__result_, _start__time_, _end__time_ = automation_research_call(_engine__mode_, "DIRECT")

				if _gp__result_ != "ZERO": 
					if _gp__result_ == "COMP":
						return JsonResponse({'status': 'Neural keyword research refresh completed', 'start': str(_start__time_), 'end': str(_end__time_)}) 
					else:	
						return JsonResponse({'status': 'Neural keyword research failed', 'start': str(_start__time_), 'end': str(_end__time_)}) 
				else:
					return JsonResponse({'status': 'No neural keyword research allocation found'})
			else:
				return JsonResponse({'status': 'Neural keyword research mode turned off'})

	except Exception as _exp_:			
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog(" > "+_mode_+" - AUTOMATION RESEARCH MODULE FUNCTION ERROR >> ERROR MESSAGE: "+ str(_exp_), "ERROR") 

	return JsonResponse({'status': 'Oops, visit: tracker.com'})
