import os
from django.shortcuts import render
from django.conf import settings

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_, ManualRefresh as _mr__record_ 
from project.machine.competitor.automation_serializers import *
from project.machine.competitor.automation_comp_reload import automation_comp_reload_data
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_

from bs4 import BeautifulSoup 
import sys, os, random
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
# from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse 

from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine import formulate as _at__calculate_, domains as _domain__get_

import concurrent.futures as _automation__futures_

from urllib.parse import urlparse 
from collections import Counter
import itertools, json 
import requests

mailToken = settings.MAIL_TOKEN 
siteUrl = settings.SITE_URL 
compDocument = "/compai/document"

# Local override to allow launch API regardless of remote MANUAL mode
CORE_MANUAL_LOCAL_OVERRIDE = True

# Local helper: extract domain from URL (kept consistent with other modules)
def extract_domain(url, remove_http=True):
	uri = urlparse(url)
	if remove_http:
		if uri.netloc:
			domain_name = f"{uri.netloc}".replace("www.", "")
		else:
			domainDivision = f"{uri.path}".replace("www.", "").split('/')
			domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision
	else:
		domain_name = f"{uri.netloc}".replace("www.", "")

	return domain_name

def __neural_competitor_save__(_source_, _gid_):
	try:
		_search__file_ = os.getcwd()+"/project/files/competitor/comProjectFile__"+str(_gid_)+".json"

		with open(_search__file_, 'w') as f:
			f.write(str(_source_))
		f.close
	except Exception as e:
		_wd_.coreLog(" > COMP ERROR ON FILE SAVE", "COMPETITOR")

	return True


def __neural_competitor_upload__(_payload_):
	"""Hand the competitor domain map to the backend so its pages can read it.

	The engine and the backend are separate services with separate disks, so a
	file the engine writes to its own FS is invisible to the backend. The backend
	reads competitor/ai_files/domains via its comppage endpoint, which this fills.
	Authenticated with the shared ENGINE_TRIGGER_TOKEN (the same secret the
	backend uses to drive the engine); with no token there is no trusted target,
	so the upload fails closed.
	"""
	try:
		token = os.environ.get("ENGINE_TRIGGER_TOKEN", "")
		if not token:
			return False
		base = os.environ.get("APP_SERVER_URL", "http://backend:8000").rstrip("/")
		resp = requests.post(
			base + compDocument,
			data={"data": json.dumps(_payload_)},
			headers={"X-Engine-Token": token},
			timeout=30,
		)
		return resp.status_code == 200
	except Exception as e:
		_wd_.coreLog(" > COMP ERROR ON APP UPLOAD "+str(e), "COMPETITOR")
		return False

def __neural_competitor_analyse_json__(json_obj, target_domain, kw_id):
	result = []
	try:
		items = json_obj.get('organic_results', [])
		for it in items:
			url = it.get('link')
			if not url:
				continue
			domain = urlparse(url).netloc.replace('www.', '')
			if domain and domain != target_domain and domain not in result:
				result.append(domain)
			if len(result) >= 100:
				break
	except Exception:
		_wd_.coreLog(" > COMP JSON PARSE ERROR >> MAIN KID "+ str(kw_id), "COMPETITOR")
		result = []
	return result, len(result)

def __neural_competitor_analyse_source__(_kw_, _target_):
	_comp__dict_ = {}
	try:
		if len(_kw_) >= 2:
			_kw__id_ = _kw_['id']
			_kw__pt_ = _kw_['platform'].lower()
			path = ""
			if str(_kw__id_).isdigit():
				if _kw__pt_ == "desktop":
					path = os.getcwd()+"/project/files/desktop/searchFile__"+str(_kw__id_)+".json"
				elif _kw__pt_ == "mobile":
					path = os.getcwd()+"/project/files/mobile/searchFile__"+str(_kw__id_)+".json"

			if path and os.path.exists(path):
				with open(path, 'r', encoding='utf-8') as reader:
					data = json.load(reader)

				comp_list, comp_count = __neural_competitor_analyse_json__(data, _target_, _kw__id_)

				if 0 < comp_count <= 100:
					_comp__dict_['id'] = _kw__id_
					_comp__dict_['val'] = comp_list
					_at__common_.__change_keyword_competitor_call_status__(_kw__id_, "COMP", int(comp_count))
				else:
					print(f"[COMP-FAIL] competitor JSON parse produced invalid count for keyword_id={_kw__id_} count={comp_count}")
					_at__common_.__change_keyword_competitor_call_status__(_kw__id_, "FAIL", 0)
			else:
				_at__common_.__change_keyword_competitor_call_status__(_kw__id_, "FERR", 0)

	except Exception:
		_wd_.coreLog(" > COMP ERROR ANALYSIS FUNCTION", "COMPETITOR")

	return _comp__dict_

def __max_task__(_g_count_):
	_max__workers_ = 2
	if _g_count_ <= 500:
		_max__workers_ = 4
	elif _g_count_ <= 1000:
		_max__workers_ = 3
	else:
		_max__workers_ = 2

	return _max__workers_


def __neural_competitor_analyse_task__(_g_record_, _g_query_):
	_gid_ = _g_record_.id
	_kw__data_ = list()
	_kw__status_ = ""
	_kw__results_ = dict() 
	_kw__count_ = 0

	try:
		if _gid_ > 0: 
			_kw__list_ = _d__keyword_.objects.filter(fk_user_id=_g_record_.fk_user_id, fk_group_id=_gid_).values('id', 'platform').all()
			_kw__count_ = len(_kw__list_) 

			if _kw__count_: 
				# __MAXIMUM_WORKERS_PER_TASK__
				_max__task__workers_ = __max_task__(_kw__count_) 
				_target_ = extract_domain(_g_record_.domain_name)

				with _automation__futures_.ThreadPoolExecutor(max_workers=_max__task__workers_) as _task__executor_:
					future_to_url = {_task__executor_.submit(__neural_competitor_analyse_source__, _kw_=_kw_, _target_=_target_): _kw_ for _kw_ in _kw__list_} 

					for future in _automation__futures_.as_completed(future_to_url):					
						eachTask = future.result()
						if eachTask:
							_kw__data_ = _kw__data_ + eachTask['val']
							_kw__results_.update({eachTask['id']: eachTask['val']})

					del(future_to_url) 
					_task__executor_.shutdown(wait=False) 
				del(_task__executor_)
				del(_kw__list_)

	except Exception as e:
		_wd_.coreLog(" > COMP ERROR "+str(e)+" >> GID "+ str(_gid_), "COMPETITOR") 

	if _kw__data_ and _kw__results_: 
		_kw__competitor__keys__dict_ = dict()
		_project__competitor__dict_ = dict() 

		_kw__counter_ = Counter(_kw__data_)
		_kw__competitor_ = dict(sorted(_kw__counter_.items(), key=lambda item: item[1], reverse=True))
		_kw__competitor__list_ = list(_kw__competitor_.keys()) 

		_project__competitor__dict_['total_keywords'] = _kw__count_
		_project__competitor__dict_['track_keywords'] = len(_kw__results_.keys()) 
		_project__competitor__dict_['total_domains'] = len(_kw__data_)
		_project__competitor__dict_['unique_domains'] = len(_kw__competitor__list_) 
		_project__competitor__dict_['top_matches'] = _kw__competitor_[next(iter(_kw__competitor_))]

		for _single__key_ in _kw__competitor__list_:
			_single__dict_ = [_single__kw_ for _single__kw_ in _kw__results_ if _single__key_ in _kw__results_[_single__kw_]]
			_kw__competitor__keys__dict_.update({_single__key_: _single__dict_}) 

		# Re-analysis must refresh the competitor cards that are already being
		# tracked, not only rebuild the discovery file. This reload helper was
		# written for that job but had no caller, leaving stage two with an empty
		# project queue. Include every tracked project so a domain that stopped
		# ranking is also measured and can move to >30.
		_tracked__projects_ = _dC__project_.objects.filter(
			fk_user_id=_g_record_.fk_user_id,
			fk_group_id=_gid_,
		).values('id', 'cp_domain_name')
		_reload__projects_ = {}
		for _tracked__project_ in _tracked__projects_:
			_tracked__domain_ = extract_domain(_tracked__project_['cp_domain_name'])
			_matched__keywords_ = [
				_kw__id_ for _kw__id_, _domains_ in _kw__results_.items()
				if _tracked__domain_ in _domains_
			]
			_reload__projects_[_tracked__domain_] = {
				'#': _tracked__project_['id'],
				'L': _matched__keywords_,
			}

		if _reload__projects_:
			_d__group_.objects.filter(id=_gid_).update(competitor_project_array=[])
			automation_comp_reload_data(
				_reload__projects_,
				_gid_,
				_g_record_.fk_user_id,
				list(_kw__results_.keys()),
				"ENGINE",
			)
		
		_kw__competitor__file__dict_ = dict()
		_kw__competitor__file__dict_['gid'] = _gid_
		_kw__competitor__file__dict_['domains'] = _kw__competitor_
		_kw__competitor__file__dict_['keys'] = _kw__competitor__keys__dict_ 
		
		_kw__competitor__result_ = json.dumps(_kw__competitor__file__dict_)

		# UPDATE FILE TO ENGINE SERVER
		__neural_competitor_save__(_kw__competitor__result_, _gid_)
		# UPLOAD FILE TO APP SERVER (backend reads this via comppage)
		__neural_competitor_upload__(_kw__competitor__file__dict_)

		_d__group_.objects.filter(id=_gid_).update(competitor_analyse_json=_project__competitor__dict_, competitor_analyse_status="COMP")
		# enable engine processing after launch
		_d__group_.objects.filter(id=_gid_).update(competitor_project_status="START")
		_kw__status_ = "COMP" 
	else:
		print(f"[COMP-FAIL] group analysis produced no data for gid={_gid_}; marking group FAIL")
		_d__group_.objects.filter(id=_gid_).update(competitor_analyse_json=dict(), competitor_analyse_status="FAIL") 
		_kw__status_ = "FAIL" 
	
	return _kw__status_, _gid_


def automation_ai_analyse(flag=None):
	_start__time_ = str(_date__time_.now())
	_gid_ = 0
	_gp__result_ = "" 
	_max__wait__count_ = 5

	_wait__count_ = _gp__record_.objects.filter(competitor_analyse_status="SCHD").count() 
	if _wait__count_ <= _max__wait__count_:
		_gp__current__slot_ = _gp__record_.objects.filter(competitor_analyse_status="START") 

		if len(_gp__current__slot_): 
			_gp__active__data_ = _gp__current__slot_[0]
			if hasattr(_gp__active__data_, 'id'):
				if _gp__active__data_.id > 0:
					if _at__common_.__change_group_competitor_call_status__(_gp__active__data_.id, "SCHD") == "success":
						_gp__result_, _gid_ = __neural_competitor_analyse_task__(_gp__active__data_, _gp__current__slot_) 

	_end__time_ = str(_date__time_.now())
	if _gp__result_ != "": 
		_wd_.coreLog(" > COMP GROUP STATUS "+str(_gp__result_)+" >> GID "+ str(_gid_)+" >> START "+str(_start__time_)+" >>> END "+str(_end__time_), "COMPETITOR")

	if flag == "DIRECT":
		return _gp__result_, _gid_, _start__time_, _end__time_
	else:
		return _gp__result_

@api_view(['GET'])
def automation_ai_call(request, _ustr_, _kstr_):
	_base__result_, _setting__data_  = _at__common_.__base_validation__(request, _ustr_)
	_start__time_ = ""
	_end__time_ = "" 

	if _base__result_ and _kstr_.isdigit():		
		_core__mode_ = _at__common_.__ms_record__("MANUAL", "_mode__check_")
		# Allow local override to run even if remote manual mode is off
		if CORE_MANUAL_LOCAL_OVERRIDE:
			_core__mode_ = True
		
		if _core__mode_ == True:
			print("_core__mode_", _core__mode_)
			_gp__result_, _gid_, _start__time_, _end__time_ = automation_ai_analyse("DIRECT")
			
			print("gp__result_", _gp__result_)
			if _gp__result_ != "": 
				if _gp__result_ == "COMP": 
					return JsonResponse({'status': 'Neural competitor refresh completed', 'group': str(_gid_), 'start': str(_start__time_), 'end': str(_end__time_)}) 
				else:	
					return JsonResponse({'status': 'Neural competitor failed', 'group': str(_gid_), 'start': str(_start__time_), 'end': str(_end__time_)}) 
			else:
				return JsonResponse({'status': 'No neural competitor refresh allocation found'}) 
		else:
			return JsonResponse({'status': 'Neural engine turned off'})
			

	return JsonResponse({'status': 'Oops, visit: tracker.com'})
