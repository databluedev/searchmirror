from django.shortcuts import render
from django.conf import settings as _def_

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_, ManualRefresh as _mr__record_
from project.machine.models import BrandTracker as _bd__record_

import sys, os, random
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine import formulate as _at__calculate_, domains as _domain__get_

import concurrent.futures as _automation__futures_


# avail, load, read, done, stop (overload), omit (no group)
_max__brand__refresh__count_ = 5


# NEURAL CHANGE BRAND STATUS
def __neural_change_brand_status__(_bid_, _status_):
	if _bid_ == "all" and isinstance(_bid_, str):
		_bd__record_.objects.filter(conquestor_call_status__ne="omit").all().update(
			conquestor_call_status=_status_, conquestor_refresh_count=0, modified_date=_date__time_.now()
		)
		return "success"
	elif _bid_ != "all" and isinstance(_bid_, int):
		_bd__record_.objects.filter(__raw__={'id': _bid_}).update(
			conquestor_call_status=_status_, modified_date=_date__time_.now()
		)
		return "success"
	else:
		return "failed"


# ── NEURAL BRAND STAGE 2 — async DataBlue fetch ──────────────────────────────
def __neural_brand_concurrency_pool__(_bd__task_, _bd__task__count_):
	global _max__brand__refresh__count_
	_max__concurrency_ = 100
	_bd__pool__count_  = 0

	if not _bd__task_:
		return _bd__pool__count_

	_bd__complete__url_ = dict()
	for _bd__single__task_ in _bd__task_:
		if not (hasattr(_bd__single__task_, 'fb_group_id') and hasattr(_bd__single__task_, 'id')):
			continue

		_gp__data_ = _gp__record_.objects.filter(__raw__={'id': _bd__single__task_.fb_group_id}).first()

		if not hasattr(_gp__data_, 'id'):
			__neural_change_brand_status__(int(_bd__single__task_.id), "omit")
			continue

		if _bd__single__task_.conquestor_refresh_count >= _max__brand__refresh__count_:
			__neural_change_brand_status__(int(_bd__single__task_.id), "stop")
			continue

		_bd__complete__url_.update({
			str(_bd__single__task_.id): _at__proxy_.__automation_brand_scrap_url__(_bd__single__task_, _gp__data_)
		})
		_bd__pool__count_ += 1

	if not _bd__complete__url_:
		return _bd__pool__count_

	def _db_and_parse_(_result_):
		"""Runs in thread pool the instant a DataBlue response arrives."""
		_bd__id_ = _result_["item_id"]
		if _bd__id_ not in _bd__complete__url_ or not _bd__id_.isdigit():
			return False

		_bd_id_int_ = int(_bd__id_)

		# Per-brand counter increment — MUST use __raw__={'id': ...}
		_bd__record_.objects.filter(__raw__={'id': _bd_id_int_}).update(inc__conquestor_refresh_count=1)

		_val_ = _at__proxy_.__automation_brand_process_result__(
			_bd__id_, _bd__complete__url_, _result_
		)

		# Proxy counters — new for BRAND
		_status_ = _result_.get("status")
		if _val_:
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_success_count=1, proxy_reset_counter=0)
		elif _status_ == 429:
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_exceeds_count=1, inc__proxy_reset_counter=1)
		else:
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_invalid_count=1, inc__proxy_reset_counter=1)

		if not _val_:
			__neural_change_brand_status__(_bd_id_int_, "fail")
			return False

		__neural_change_brand_status__(int(_val_['id']), "load")
		_parse__result_ = _at__proxy_.__automation_brand_collective_parser__(
			_index_=str(_val_['id']),
			_bd__data_={str(_val_['id']): _val_},
		)

		if _parse__result_:
			__neural_change_brand_status__(int(_val_['id']), "done")
		else:
			__neural_change_brand_status__(int(_val_['id']), "fail")

		return _parse__result_

	# Bill the account's own DataBlue key, not the operator's, and use the
	# page depth that account actually chose. Without this the fetch falls
	# through to the instance key at a hardcoded depth.
	_acct__key_ = _at__proxy_._apply_account_prefs_(_bd__complete__url_)
	_at__proxy_.__automation_fetch_and_process__(
		_bd__complete__url_, _max__concurrency_, _db_and_parse_,
		_acct__key_,
	)

	return _bd__pool__count_


# NEURAL BRAND STAGE 1
def __neural_brand_concurrency_task__():
	_task__count_ = 0

	# ── Fetch ALL pending brand records at once — semaphore is the sliding window ──
	_bd__task_ = list(
		_bd__record_.objects.filter(
			conquestor_call_status__in=["avail", "load", "read"], status="on"
		).all()
	)
	_bd__task__count_ = len(_bd__task_)

	if _bd__task__count_ > 0:
		_task__count_ += __neural_brand_concurrency_pool__(_bd__task_, _bd__task__count_)

	return _task__count_


# BRAND CONQUESTOR CALL
@api_view(['GET'])
def automation_brand_call(request, _ustr_, _kstr_):
	_start__time_ = _date__time_.now()
	_gp__result_  = 0

	_base__result_, _setting__data_ = _at__common_.__base_validation__(request, _ustr_)

	if _base__result_ and _kstr_.isdigit():
		_core__mode_ = _at__common_.__ms_record__("BRAND", "_mode__check_")
		if _core__mode_ == True:

			_wait__count_ = _gp__record_.objects.filter(manual_grp_trigger="WAIT").count()
			if _wait__count_ == 0:
				_gp__result_ = __neural_brand_concurrency_task__()

				if _gp__result_:
					_end__time_ = _date__time_.now()
					_wd_.coreLog(
						" > TOTAL BRAND REQUEST " + str(_gp__result_) + " >> START " + str(_start__time_) + " >>> END " + str(_end__time_),
						"BRAND"
					)
					return JsonResponse({'status': 'Neural brand refresh completed', 'start': str(_start__time_), 'end': str(_end__time_)})
				else:
					return JsonResponse({'status': 'No neural brand refresh allocation found'})

	return JsonResponse({'status': 'Oops, visit: rankyfy.com'})
