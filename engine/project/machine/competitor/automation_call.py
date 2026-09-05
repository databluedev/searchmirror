from django.shortcuts import render
from django.conf import settings
from django.utils import timezone

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_, ManualRefresh as _mr__record_ 
from project.machine.models import CompProject, CompKeyword 
from project.machine.competitor.automation_serializers import *
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

from bs4 import BeautifulSoup 
import sys, os, random, json
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse,JsonResponse 

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine.competitor import  automation_extractor as _at__extract_ 
from project.machine.competitor import automation_cFormulate as _at__calculate_
from project.machine.competitor import automation_formulate as _at__self_ 
import concurrent.futures as _automation__futures_
from urllib.parse import urlparse


# competitor_project_status  - VOID, INIT, SCHD, COMP, FAIL
# competitor_project_array - array 

# CONVERT TO SERIALIZERS IN FUTURE - CHECK FOR LAST RANKED DATE
def __comp_macro_problem__(_cp_id_, _mode_): 
	try:
		_dt__today_ = _dt_.today()
		_gp__all__keywords_ =  CompKeyword.objects.filter(fk_cp_project_id=_cp_id_) 

		if _gp__all__keywords_.count(): 
			for _single__key_ in _gp__all__keywords_.all():
				_key__total__day_ = int((_dt__today_ - _single__key_.created_date.date()).days) + 1
				_key__rank__count_ = len(_single__key_.rank)

				if _key__rank__count_ > 0 and (_key__rank__count_ > _key__total__day_):
					_pop_ = 0 
					
					# RANK ARRAY OVERFLOW REDUCED
					while (_key__rank__count_ > _key__total__day_):
						CompKeyword.objects.filter(__raw__= {'id': _single__key_.id}).update(pop__rank=-1)
						_key__rank__count_-= 1 
						_pop_ += 1
					_wd_.coreLog(" > RANK ARRAY POP >> KEY_ID = "+str(_single__key_.id)+" >>> POP_COUNT = "+str(_pop_), _mode_) 
				else:
					if _key__rank__count_ > 0 and (_key__rank__count_ < _key__total__day_):
						_push_ = 0
					
						# RANK ARRAY INSUFFICIENCY ADDED 
						while (_key__rank__count_ < _key__total__day_):
							CompKeyword.objects.filter(__raw__= {'id': _single__key_.id}).update(push__rank__0=_single__key_.rank[0]) 
							_key__rank__count_+= 1
							_push_ += 1	

						if _push_ > 1: 
							_wd_.coreLog(" > RANK ARRAY PUSH >> KEY_ID = "+str(_single__key_.id)+" >>> PUSH_COUNT = "+str(_push_), _mode_)   
	except Exception as e:
		# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON
		_wd_.coreLog(" > COMPETITOR PROJECT MACRO PROBLEM ERROR - "+str(e)+" >> CP_ID "+ str(_cp_id_), _mode_)  
	
	return True 

# NEURAL MANUAL REFRESH DASHBOARD CALCULATION
def __competitor_project_dash_calculation__(_cp__active__data_, _gid_): 
	if hasattr(_cp__active__data_, 'id'):
		_cp__id_ = _cp__active__data_.id

		if _cp__id_ > 0:
			_keyword__remain__count_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp__id_, fk_group_id=_gid_).exclude(comp_call_mode__in=["done", "fail"]).count()
			
			if _keyword__remain__count_ == 0: 
				compGraph = _at__calculate_.dashboardCompetitorGraph("COMPALYSE", _cp__id_) 
				ownGraph = _at__self_.dashboardGroupGraph("COMPALYSE", _gid_, _cp__id_) 
				
				# if compGraph and ownGraph:
				# 	_at__common_.__change_group_competitor_project_status__(_gid_, "COMP")   
					
				# 	# UPDATE COMP RECORDS TABLE 
				# 	if len(_cp__active__data_.total_Keyword) <= 2:
				# 		_domain__get_.domainInitiate(_cp__active__data_)

	return True

def __pull_keys__(_gid_, _value_, _qflag_):
	_g__keys_ = []
	_gp__record_.objects.filter(__raw__= {'id': _gid_}).update(__raw__= {'$pullAll': {'competitor_project_array': _value_}}) 
	
	if _qflag_ == 1:
		_g__keys_ = _d__group_.objects.filter(id=_gid_).values_list('competitor_project_array', flat=True).first()

		if len(_g__keys_) == 0:
			_at__common_.__change_group_competitor_project_status__(_gid_, "COMP")
	
	return _g__keys_

def __update_zerokeys__(_gid_): 
	return _gp__record_.objects.filter(__raw__= {'id': _gid_}).update(competitor_project_array__0=0) 

def __max_task__(_g_flag_):
	_initial__pool__task_, _max__workers_ = 10, 3
	if _g_flag_ == "ENGINE":
		_wait__count_ = _gp__record_.objects.filter(competitor_project_status="BUSY").count()
		_initial__pool__task_, _max__workers_ = 10, 3
		if _wait__count_ <= 3: 
			_initial__pool__task_, _max__workers_ = 20, 3  
	else:
		_wait__count_ = _gp__record_.objects.filter(competitor_project_status="SCHD").count() 
		_initial__pool__task_, _max__workers_ = 10, 3
		if _wait__count_ <= 3: 
			_initial__pool__task_, _max__workers_ = 15, 3
	
	return _initial__pool__task_, _max__workers_

# NEURAL COMPETITOR SHOWCASE STAGE 2
def __domain_from_url__(_url_):
    try:
        u = urlparse(_url_)
        if u.netloc:
            return u.netloc.replace("www.", "")
        return (u.path or "").split('/')[0].replace("www.", "")
    except Exception:
        return ""

def __rank_from_json_file__(_kid_, _platform_, _target_domain_):
    try:
        _path_ = ""
        if str(_kid_).isdigit():
            if (_platform_ or "").lower() == "desktop":
                _path_ = os.getcwd()+"/project/files/desktop/searchFile__"+str(_kid_)+".json"
            else:
                _path_ = os.getcwd()+"/project/files/mobile/searchFile__"+str(_kid_)+".json"

        if _path_ and os.path.exists(_path_):
            with open(_path_, 'r', encoding='utf-8') as r:
                data = json.load(r)
            items = data.get('organic_results', [])
            pos = 0
            url = None
            for idx, it in enumerate(items):
                link = it.get('link')
                if not link:
                    continue
                dom = __domain_from_url__(link)
                if dom and dom == _target_domain_:
                    # Use provided rank only; if absent/non-numeric, keep rank as 0
                    provided = it.get('rank')
                    if provided is not None and str(provided).isdigit():
                        try:
                            pos = int(provided)
                            url = link
                        except Exception:
                            pos = 0
                    break
            return pos, url
    except Exception as e:
        pass
    return 0, None

def __update_keyword_rank_minimal__(_kw_id_, _liverank_, _url_fetched_):
    try:
        print("liverank: ", _liverank_)
        print("url_fetched: ", _url_fetched_)
        print("kw_id: ", _kw_id_)
        kw = _dC__keyword_.objects.filter(id=_kw_id_).first()
        if not kw:
            return False

        target_url = _url_fetched_ or kw.target or kw.cp_site_url or ""

        # Compute top_rank
        exist_top = int(kw.top_rank or 0)
        new_top = int(_liverank_) if int(_liverank_) > 0 and (exist_top == 0 or int(_liverank_) < exist_top) else exist_top

        # Maintain rank list (JSONField) in Python and save
        try:
            currdate = _dt_.today()
            keywordTotalDayCount = int((currdate - kw.created_date.date()).days) + 1
        except Exception:
            keywordTotalDayCount = 1

        rank_list = list(kw.rank or [])

        if keywordTotalDayCount == 1:
            rank_list = [int(_liverank_)]
        else:
            # ensure latest at front
            rank_list.insert(0, int(_liverank_))
            # limit to window (do not exceed day count)
            if len(rank_list) > keywordTotalDayCount:
                rank_list = rank_list[:keywordTotalDayCount]

        kw.rank = rank_list
        kw.ranknow = int(_liverank_)
        kw.top_rank = int(new_top)
        kw.cp_site_url = target_url
        kw.lastranked_date = timezone.now()
        kw.modified_date = timezone.now()
        kw.save(update_fields=[
            'rank', 'ranknow', 'top_rank', 'cp_site_url', 'lastranked_date', 'modified_date'
        ])
        return True
    except Exception:
        pass
    return False

def __neural_competitor_concurrency_pool__(_cp_id_, _gid_, _kw__task_, _max__task__workers_):
    # JSON-based rank parsing from stored engine output
    data = list()
    try:
        if _kw__task_:
            for _kw__single__task_ in _kw__task_:
                try:
                    _kid_ = getattr(_kw__single__task_, 'fk_keyword_id', None)
                    _platform_ = getattr(_kw__single__task_, 'platform', 'desktop')
                    _target_url_ = getattr(_kw__single__task_, 'target', '') or getattr(_kw__single__task_, 'cp_site_url', '')
                    _target_domain_ = __domain_from_url__(_target_url_)

                    _rank_, _match_url_ = __rank_from_json_file__(_kid_, _platform_, _target_domain_)

                    # Persist only rank-related fields
                    __update_keyword_rank_minimal__(_kw__single__task_.id, int(_rank_ or 0), _match_url_ or _target_url_)
                    # Mark processed
                    _dC__keyword_.objects.filter(id=_kw__single__task_.id).update(comp_call_mode="done")
                except Exception:
                    # best-effort per-keyword; continue others
                    pass
    except Exception:
        data = list()
    return data
 
# NEURAL COMPETITOR SHOWCASE STAGE 1
def __neural_competitor_concurrency_task__(_cp_record_, _cp_id_, _gid_, _g_flag_):
	# ALLOCATE TASK PER THREAD 
	# _initial__pool__task_ = 5
	_task__count_ = 0

	if int(_cp_id_) > 0: 
		_kw__all_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp_id_, fk_group_id=_gid_).count()

		if _kw__all_ > 0: 
			_kw__remain__count_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp_id_, fk_group_id=_gid_, comp_call_mode__in=["done", "fail"]).count()
			if _kw__remain__count_ < _kw__all_:
				# INITIALISE LOOP FOR SLOT
				while(_kw__remain__count_ < _kw__all_):
					# ALLOCATE TASK PER THREAD AND MAX WORKERS 
					_initial__pool__task_, _max__task__workers_ = __max_task__(_g_flag_)  
					_kw__task_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp_id_, fk_group_id=_gid_).exclude(comp_call_mode__in=["done", "fail"]).all()[0:_initial__pool__task_]
					_kw__task__count_ = len(_kw__task_)  
					
					if _kw__task__count_ > 0:
						# CALLING STAGE TWO
						_task__count_ += _kw__task__count_ 
						__neural_competitor_concurrency_pool__(_cp_id_, _gid_, _kw__task_, _max__task__workers_) 

						_kw__remain__count_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp_id_, fk_group_id=_gid_, comp_call_mode__in=["done", "fail"]).count()
						_kw__all_ = _dC__keyword_.objects.filter(fk_cp_project_id=_cp_id_, fk_group_id=_gid_).count() 
						
						# AFTER ALL KEYWORD IN MANUAL REFRESH COMPLETED 
						if _kw__remain__count_ == _kw__all_:
							__competitor_project_dash_calculation__(_cp_record_, _gid_) 

				# END OF LOOP FOR SLOT
			else:
				# KEYWORD DELETE OCCURED
				compGraph = _at__calculate_.dashboardCompetitorGraph("COMPALYSE", _cp_id_) 
				ownGraph = _at__self_.dashboardGroupGraph("COMPALYSE", _gid_, _cp_id_)  
				_task__count_ = -1 
		else:
			_task__count_ = 0
			# NO KEYWORDS EXISTS IN THE COMPETITOR PROJECT 
			# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON

	return _task__count_  # needed key status 

def __neural_competitor_group__(_g_record_, _g_flag_):
	_g__status_ = ""
	_gid_ = int(_g_record_.id) 

	if _gid_ > 0:
		try:
			_g__keys_ = __pull_keys__(_gid_, [0], 1) 
			
			if len(_g__keys_):
				while _g__keys_:
					_g__key_ = int(_g__keys_[0])
					_g__key__status_ = 0

					_comp__project_ = _dC__project_.objects.filter(id=_g__key_)

					if _comp__project_.exists():
						_comp__active__project_ = _comp__project_[0] 

						if hasattr(_comp__active__project_, 'id'):
							if _comp__active__project_.id > 0: 
								__comp_macro_problem__(_comp__active__project_.id, "COMPALYSE") 
								_g__key__status_ = __neural_competitor_concurrency_task__(_comp__active__project_, _comp__active__project_.id, _gid_, _g_flag_)

					if _g__key__status_ == -1:
						__update_zerokeys__(_gid_) 
						_g__keys_ = __pull_keys__(_gid_, [0], 1)
						_g__status_= "CALC"
					elif _g__key__status_ >= 1: 
						__update_zerokeys__(_gid_) 
						_g__keys_ = __pull_keys__(_gid_, [0], 1)
						_g__status_= "COMP"  
					else: 
						_g__keys_ = __pull_keys__(_gid_, [0, int(_g__key_)], 1)
			else:
				_at__common_.__change_group_competitor_project_status__(_gid_, "COMP")
			

		except Exception as e:
			# UPDATE ON ERROR TABLES - ID , JSON DETAILS, STATUS - GERR etc, REASON 
			_at__common_.__change_group_competitor_project_status__(_gid_, "FAIL") 
			_wd_.coreLog(" > COMPETITOR PROJECT "+str(e)+">> GID "+ str(_gid_), "COMPALYSE") 
	
	return _g__status_, _gid_

def automation_comp_analyse(flag=None): 
	_start__time_ = str(_date__time_.now())
	_gid_ = 0
	_gp__result_ = "" 
	_max__wait__count_ = 5

	if flag == "ENGINE":
		_max__wait__count_ = 6 
		# VOID, START, BUSY, COMP, FAIL
		_wait__count_ = _gp__record_.objects.filter(competitor_project_status="BUSY").count()
	else:
		# VOID, INIT, SCHD, COMP, FAIL 
		_wait__count_ = _gp__record_.objects.filter(competitor_project_status="SCHD").count()

	if _wait__count_ < _max__wait__count_:
		if flag == "ENGINE":
			_gp__current__slot_ = _gp__record_.objects.filter(competitor_project_status="START").order_by('+paymentmode')
		else:
			_gp__current__slot_ = _gp__record_.objects.filter(competitor_project_status="INIT").order_by('+paymentmode')

		if len(_gp__current__slot_): 
			_gp__active__data_ = _gp__current__slot_[0]
			
			if hasattr(_gp__active__data_, 'id'):
			
				if _gp__active__data_.id > 0:
					_gp__current__status_ = ""
			
					if flag == "ENGINE":
						_gp__current__status_ = _at__common_.__change_group_competitor_project_status__(_gp__active__data_.id, "BUSY") 
					else:
						_gp__current__status_ = _at__common_.__change_group_competitor_project_status__(_gp__active__data_.id, "SCHD")

					if _gp__current__status_ == "success":
						_gp__result_, _gid_ = __neural_competitor_group__(_gp__active__data_, flag)  

	_end__time_ = str(_date__time_.now())
	if _gp__result_ != "": 
		_wd_.coreLog(" > COMPETITOR PROJECT STATUS "+str(_gp__result_)+">> GROUP ID "+ str(_gid_)+" >> START "+str(_start__time_)+" >>> END "+str(_end__time_), "COMPALYSE")

	if flag == "ENGINE":
		_end__time_ = str(_date__time_.now())
		return _gp__result_, _gid_, _start__time_, _end__time_
	else:
		return _gp__result_ 

@api_view(['GET']) 
def automation_comp_call(request, _ustr_, _kstr_): 
	_base__result_, _setting__data_  = _at__common_.__base_validation__(request, _ustr_)
	_start__time_ = ""
	_end__time_ = "" 

	if _base__result_ and _kstr_.isdigit(): 		
			
		_gp__result_, _gid_, _start__time_, _end__time_ = automation_comp_analyse("ENGINE")

		if _gp__result_ != "": 
			if _gp__result_ == "COMP":
				return JsonResponse({'status': 'Neural competitor project for automation refresh completed', 'group': str(_gid_), 'start': str(_start__time_), 'end': str(_end__time_)}) 
			elif _gp__result_ == "CALC":   
				return JsonResponse({'status': 'Neural competitor project calculation updated', 'group': str(_gid_), 'start': str(_start__time_), 'end': str(_end__time_)})
			else:	
				return JsonResponse({'status': 'Neural competitor project failed', 'group': str(_gid_), 'start': str(_start__time_), 'end': str(_end__time_)}) 
		else:
			return JsonResponse({'status': 'No neural competitor project refresh allocation found'}) 
			

	return JsonResponse({'status': 'Oops, visit: tracker.com'})
