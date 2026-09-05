from django.conf import settings

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_
from project.machine.models import KeywordResearch as _kw__research_

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_
from project.machine.submodels.researchmodels import DKeywordResearch as _dK__research_

import requests, json, time
from urllib import parse 
import sys, os, random 
from datetime import datetime, date

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine import encryption as _at__enc_

# google_status, ontype_status
# kw_ontype_array

# research_refresh_count	# RESEARCH PROXY CALL COUNT

def __create_uuid_attr__(_engine__mode_, _data__id_, _data__uid_):
	_mp__uuid__4_ = str("-")
	_mp__uuid__url_ = str("-")
	
	try:
		_mp__uuid_ = str(_at__common_.__uuid__())
		if (len(_mp__uuid_) > 0):
			_mp__uuid__4_ = _mp__uuid_ 
			_mp__uuid__url_ = str(_at__enc_.encode_page_url(_data__uid_, _data__id_, _mp__uuid__4_)) 

	except Exception as _exp_:
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog("> "+_mode_+" - CREATE UUID FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(_exp_), "ERROR")

	return _mp__uuid__4_, _mp__uuid__url_

def _mongo__push_(_engine__mode_, _center__source_, _data__source_):
	_mp__error__message_ = ""

	try:
		_r__kid_ = _data__source_['id'] 
		_r__uid_ = _data__source_['fk_user_id'] 
		_r__gid_ = _data__source_['fk_group_id']  

		_mp__id_ = _center__source_.get('ID') if "ID" in _center__source_ else ""

		if str(_mp__id_).isdigit() and str(_r__kid_).isdigit():
			if int(_mp__id_) == int(_r__kid_):
				_mp__uuid_, _mp__uuid__url_ = __create_uuid_attr__(_engine__mode_, _r__kid_, _r__uid_)
				_mp__related__details_ = _center__source_.get('RELATED_DETAILS') if "RELATED_DETAILS" in _center__source_ else list()
				_mp__snippet__details_ = _center__source_.get('SNIPPET_DETAILS') if "SNIPPET_DETAILS" in _center__source_ else dict()
				_mp__ontype__details_ = _center__source_.get('ONTYPE_DETAILS') if "ONTYPE_DETAILS" in _center__source_ else list()
				_mp__search__results_ = _mp__snippet__details_['srs'] if "srs" in _mp__snippet__details_ else "-"

				_mp__keywords_ = _kw__research_.objects.filter(__raw__= {'id': _mp__id_}) 
				if _mp__keywords_:
					_mp__keywords_.update(
						kw_related_array=_mp__related__details_, 
						kw_ontype_array=_mp__ontype__details_, 
						search_results=str(_mp__search__results_),
						page_uuid_url=_mp__uuid__url_, 
						page_uuid=_mp__uuid_,
						serp_json=_mp__snippet__details_
					)
					return 1
				else:
					_mp__error__message_ = "KEYWORD ID NOT FOUND ON DATABASE"					
			else:
				_mp__error__message_ = "KEYWORD ID COMPARISON MISMATCH"
		else:
			_mp__error__message_ = "KEYWORD ID IS NOT IN INTEGERS"

		if len(_mp__error__message_):
			_mode_ = str(_engine__mode_).upper()
			_wd_.coreLog("> "+_mode_+" - CENTRALISED MONGO PUSH DATA FLAG ERROR >> KEYWORD ID: "+str(_r__kid_)+" >>> FLAG RROR MESSAGE: "+ str(_mp__error__message_), "ERROR") 

	except Exception as _exp_:
		_mode_ = str(_engine__mode_).upper() 
		_wd_.coreLog("> "+_mode_+" - CENTRALISED MONGO PUSH DATA FUNCTION ERROR >> KEYWORD ID: "+str(_r__kid_)+" >>> ERROR MESSAGE: "+ str(_exp_), "ERROR") 
	
	return 0