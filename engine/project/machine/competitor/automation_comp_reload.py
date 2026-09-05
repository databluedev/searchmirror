from django.shortcuts import render
from django.conf import settings

from project.machine.models import Group, CompProject, CompKeyword
from project.machine.competitor.automation_serializers import * 
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

import sys, os, random
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse,JsonResponse 

from project.machine import watchdog as _wd_, automation_common as _at__common_


# competitor_project_status  - VOID, INIT, SCHD, COMP, FAIL
# competitor_project_array - array 

def automation_comp_reload_data(_comp__dict_, _gid_, _uid_, _kw_remain_list_, _mode_): 
	try:
		# print("_kw_remain_list_ ", _kw_remain_list_)
		# print("_kw_remain_list_ ", len(_kw_remain_list_))
		# print("\n")
		# print("_comp__dict_ ", _comp__dict_) 

		if _gid_ and _comp__dict_:

			for _single__comp_ in _comp__dict_: 
				_reload__cpid_ = False
				_comp__id_ = int(_comp__dict_[_single__comp_]['#']) 
				_comp__list_ = _comp__dict_[_single__comp_]['L'] 
				_match_list_ = list() 
				# print("\n")
				# print("_comp__id_ ", _comp__id_) 
				# print("_comp__list_ ", _comp__list_) 

				if _comp__id_: 
					_cp_keyword_list_ = list(_dC__keyword_.objects.filter(fk_cp_project_id=_comp__id_, fk_group_id=_gid_).values_list('fk_keyword_id', flat=True)) 
					_compare_list_ = [*set(_comp__list_).difference(_cp_keyword_list_)]

					# print("_cp_keyword_list_ ", _cp_keyword_list_)
					# print("len _cp_keyword_list_ ", len(_cp_keyword_list_))
					# print("_compare_list_ ", _compare_list_)

					if len(_compare_list_):
						_comp__project_ = DCompProject.objects.filter(fk_user_id=_uid_, fk_group_id=_gid_, id=_comp__id_).values('cp_domain_name').first() 
						if _comp__project_:
							_cp__domain_ = _comp__project_['cp_domain_name'] 
							_new__comp__keywords_ = CompCreateKeywordSerializer(_compare_list_, many=True, context={'cpdomain': _cp__domain_, 'cpid':_comp__id_, 'uid':_uid_, 'gid':_gid_}).data 
							_new__comp__keywords_ = list(filter(None, _new__comp__keywords_)) 

							if _new__comp__keywords_:
								_flag_ = _dC__keyword_.objects.bulk_create(_new__comp__keywords_)
								if _flag_:
									_reload__cpid_=True

					if _mode_ == "ENGINE":
						_dC__keyword_.objects.filter(fk_cp_project_id=_comp__id_, fk_group_id=_gid_).update(comp_call_mode="avail") 
						_reload__cpid_=True
					elif _mode_ == "MANUAL":
						_match_list_ = [*set(_kw_remain_list_).intersection(_cp_keyword_list_)]
						# print("\n")
						# print("_match_list_ ", _match_list_)
						# print("len _match_list_ ", len(_match_list_)) 

						if _match_list_: 
							_dC__keyword_.objects.filter(fk_keyword_id__in=_match_list_, fk_cp_project_id=_comp__id_, fk_group_id=_gid_).update(comp_call_mode="avail") 
							_reload__cpid_=True
						
					if _match_list_ or _reload__cpid_:
						# print("OK")
						Group.objects.filter(__raw__= {'id': int(_gid_)}).update(push__competitor_project_array=int(_comp__id_)) 
						if _mode_ == "MANUAL": 
							Group.objects.filter(__raw__= {'id': int(_gid_)}, competitor_project_status__nin=["SCHD", "BUSY"]).update(competitor_project_status="INIT") 
						else:
							Group.objects.filter(__raw__= {'id': int(_gid_)}, competitor_project_status__nin=["SCHD", "BUSY"]).update(competitor_project_status="START")

	except Exception as e:
		# print(str(e)) 
		pass 		

	# print("DONE") 
	return True 