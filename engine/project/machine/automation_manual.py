from django.shortcuts import render
from django.conf import settings as _def_

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_, ManualRefresh as _mr__record_
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

import sys, os, random
from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine import formulate as _at__calculate_, domains as _domain__get_
from project.machine.competitor import automation_analyse as _aAS_
from project.machine.competitor import automation_call as _aCL_

import concurrent.futures as _automation__futures_

# Error codes recorded against a failed refresh. Owned by the backend --
# backend/serp/refresh_error.py defines the vocabulary and the API prefers a
# recorded code over the ones it derives for itself. Rate limiting is a
# separate code because the user's next move differs: it is transient and the
# answer is to wait, where the generic code means the request or the provider
# was wrong.
_REFRESH_ERROR_CODE_ = "serp_failed"
_REFRESH_LIMIT_CODE_ = "serp_rate_limited"


# NEURAL MANUAL REFRESH DASHBOARD CALCULATION
def __group_dash_calculation__(_gp__active__data_):
	if hasattr(_gp__active__data_, 'id'):
		_gid_ = _gp__active__data_.id

		if _gid_ > 0:
			_keyword__remain__count_ = _kw__record_.objects.filter(manual_call_status=True, fk_group_id=_gid_).count()
			if _keyword__remain__count_ == 0:
				if _at__calculate_.dashboardNewGraph("MANUAL", _gid_) == True:
					_gp__record_.objects.filter(__raw__={'id': _gid_}).update(strict_refresh_switch=False, manual_grp_trigger="DONE")
					_mr__record_.objects.filter(fk_group_id=_gid_).update(refresh_status="done")
					_mr__record_.objects.filter(fk_group_id=_gid_, refresh_type__ne="new").update(refresh_time=_date__time_.now())
					if len(_gp__active__data_.total_Keyword) <= 2:
						_domain__get_.domainInitiate(_gp__active__data_)

	return True


# NEURAL MANUAL REFRESH FAILED AND RESET ALL ESSENTIALS
def __group_failed_dash_calculation__(_gp__active__data_):
	if hasattr(_gp__active__data_, 'id'):
		_gid_ = _gp__active__data_.id

		if _gid_ > 0:
			# fk_group_id is an IntField; it was being filtered with a dict,
			# which mongoengine cannot coerce -- so this raised and took the
			# whole manual endpoint down for any project with no keywords.
			_kw__record_.objects.filter(fk_group_id=_gid_).update(manual_call_status=False, manual_call_mode="done")
			_gp__record_.objects.filter(__raw__={'id': _gid_}).update(strict_refresh_switch=False, manual_grp_trigger="DONE")
			_mr__record_.objects.filter(fk_group_id=_gid_).update(refresh_status="done")
			_mr__record_.objects.filter(fk_group_id=_gid_, refresh_type__ne="new").update(refresh_time=_date__time_.now())

	return True


# RECORD WHY ONE REFRESH FAILED — written once per run, read by the API
def __record_group_refresh_error__(_gid_, _outcomes_):
	"""Write the provider outcome of one refresh onto the project's refresh row.

	The API surfaces this verbatim (errc / err on /refreshstatus) and the
	frontend switches on the code, so the message is a plain sentence: never a
	key, a status line or a traceback.  The codes belong to the backend
	(backend/serp/refresh_error.py) -- the engine only records what nothing
	else can observe, which is what the provider actually did.

	A clean run clears both fields.  A stale error left behind would go on
	telling the user about a refresh that has since succeeded.
	"""
	_refresh_ = _mr__record_.objects.filter(fk_group_id=_gid_)
	_failed_ = [_o_ for _o_ in _outcomes_ if _o_ != "ok"]

	if not _failed_:
		_refresh_.update(refresh_error_code="", refresh_error="")
		return True

	_limited_ = len([_o_ for _o_ in _failed_ if _o_ == "429"])
	_total_ = len(_outcomes_)

	if _limited_ and _limited_ == len(_failed_):
		# Every failure was a 429, so the account was throttled and nothing
		# else went wrong -- the honest instruction is "wait", not "retry".
		# A run with mixed causes gets the generic code: rate limiting was
		# only part of what happened, and telling the user to wait would be
		# wrong for the rest of it.
		_code_ = _REFRESH_LIMIT_CODE_
		_message_ = (
			"Your SERP provider rate limited this account, so "
			+ str(_limited_) + " of " + str(_total_)
			+ " keywords could not be checked. Wait a few minutes and refresh again."
		)
	else:
		_code_ = _REFRESH_ERROR_CODE_
		_message_ = (
			str(len(_failed_)) + " of " + str(_total_)
			+ " keywords could not be checked - the SERP provider returned no usable"
			  " result for them. Their last known rank is unchanged."
		)

	_refresh_.update(refresh_error_code=_code_, refresh_error=_message_)
	return True


# ── NEURAL MANUAL STAGE 2 — async DataBlue fetch ────────────────────────────
def __neural_manual_concurrency_pool__(_gid_, _kw__task_, _kw__task__count_, _comp__dict_, _comp__list_):
	_max__concurrency_ = 100

	if not _kw__task_:
		return _comp__dict_

	_kw__complete__url_ = dict()
	# Per-run heartbeat state — see __touch_group_claim__.  A refresh of a big
	# project spends minutes in this loop before its first request.
	_claim__state_ = dict()
	for _kw__single__task_ in _kw__task_:
		_at__common_.__touch_group_claim__(_gid_, "MANUAL", _claim__state_)
		# START - PLEASE BE CAUTIOUS ON THIS STATEMENT ELSE COMPLETE PROJECT WILL BE DELETED
		_kw__flag_ = 0
		if _kw__single__task_.keyword is None:
			_kw__flag_ = 1
		elif len(_kw__single__task_.keyword.strip()) == 0:
			_kw__flag_ = 1

		if _kw__flag_ == 1:
			_d__keyword_.objects.filter(id=_kw__single__task_.id).delete()
		elif _at__common_.__claim_keyword__(_kw__single__task_.id, "MANUAL"):
			# Only a keyword this run actually claimed is fetched, so a
			# double-clicked refresh that reaches the queue twice cannot bill
			# the account twice for the same keyword.
			_kw__complete__url_.update({
				str(_kw__single__task_.id): _at__proxy_.__automation_search_scrap_url__(_kw__single__task_)
			})
		# END - PLEASE BE CAUTIOUS ON THIS STATEMENT ELSE COMPLETE PROJECT WILL BE DELETED

	if not _kw__complete__url_:
		return _comp__dict_

	_comp__updates_ = []  # list of (kw_id_int, clist)
	_outcomes_      = []  # one entry per keyword fetched; list.append is atomic under the GIL

	def _db_and_parse_(_result_):
		"""Runs in thread pool the instant a DataBlue response arrives."""
		_kw__id_ = _result_["item_id"]
		if _kw__id_ not in _kw__complete__url_ or not _kw__id_.isdigit():
			return None

		_kw_id_int_ = int(_kw__id_)

		# This run is alive; say so before the sweep decides otherwise.
		_at__common_.__touch_group_claim__(_gid_, "MANUAL", _claim__state_)

		# Per-keyword counter increments — MUST use __raw__={'id': ...}
		_kw__record_.objects.filter(__raw__={'id': _kw_id_int_}).update(inc__strict_refresh_count=1)
		_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__daily_demand_count__0=1)

		_val_, _clist_, _outcome_ = _at__proxy_.__automation_process_result__(
			"MANUAL", _kw__id_, _kw__complete__url_, _comp__list_, _result_
		)

		# Per-outcome proxy counters, then the failure goes to the recorder.
		# It ends the keyword's run -- a refresh the user asked for is never
		# retried behind their back, because every attempt is billed to their
		# key -- but it ends it as 'fail', not as 'done'.  Writing 'done' on a
		# failure is what made a refresh in which every keyword failed report
		# itself as a success.
		if _outcome_ == "ok":
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_success_count=1, proxy_reset_counter=0)
		elif _outcome_ == "429":
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_exceeds_count=1, inc__proxy_reset_counter=1)
			_at__common_.__record_keyword_failure__(_kw_id_int_, "MANUAL", "rate limited (429)")
			_outcomes_.append("429")
			return None
		else:
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_invalid_count=1, inc__proxy_reset_counter=1)
			_at__common_.__record_keyword_failure__(
				_kw_id_int_, "MANUAL", "provider " + str(_result_.get("status"))
			)
			_outcomes_.append("fail")
			return None

		# A response that arrives and then will not parse is still a keyword
		# the user did not get a rank for, so it counts as a failure here too.
		_parsed_ = _at__proxy_.__automation_collective_parser__(
			_mode_="MANUAL",
			_index_=str(_val_['id']),
			_kw__data_={str(_val_['id']): _val_},
		)
		_outcomes_.append("ok" if _parsed_ else "parse")

		if _clist_:
			_comp__updates_.append((_kw_id_int_, _clist_))

		return True

	# Bill the account's own DataBlue key, not the operator's, and use the
	# page depth that account actually chose. Without this the fetch falls
	# through to the instance key at a hardcoded depth.
	_acct__key_ = _at__proxy_._apply_account_prefs_(_kw__complete__url_)
	_at__proxy_.__automation_fetch_and_process__(
		_kw__complete__url_, _max__concurrency_, _db_and_parse_,
		_acct__key_,
	)

	# One error per run, not one per keyword: the user asked for a refresh and
	# wants to know whether it worked, not to read a list.
	__record_group_refresh_error__(_gid_, _outcomes_)

	# Apply competitor updates after pipeline drains
	for _item__id_, _clist_ in _comp__updates_:
		for _d_ in _clist_:
			if _d_ in _comp__dict_:
				_comp__dict_ = _at__common_.__get_competitor_list_update__(str(_d_), _item__id_, _comp__dict_)

	return _comp__dict_


# NEURAL MANUAL STAGE 1
def __neural_manual_concurrency_task__(_g_record_):
	_gid_ = _g_record_.id
	_task__count_ = 0

	if _gid_ > 0:
		_uid_ = _g_record_.fk_user_id

		_comp__dict_, _comp__list_ = dict(), list()

		# ── Fetch ALL pending keywords at once — semaphore is the sliding window ──
		_kw__task_ = list(
			_kw__record_.objects.filter(
				fk_user_id=_g_record_.fk_user_id, fk_group_id=_gid_,
				manual_call_status__ne=False
			).all()
		)
		_kw__task__count_ = len(_kw__task_)

		if _kw__task__count_ > 0:
			_task__count_ = _kw__task__count_
			_comp__dict_ = __neural_manual_concurrency_pool__(
				_gid_, _kw__task_, _kw__task__count_, _comp__dict_, _comp__list_
			)
			__group_dash_calculation__(_g_record_)

			if _comp__dict_:
				pass
		else:
			_kw__all_ = _kw__record_.objects.filter(
				fk_user_id=_g_record_.fk_user_id, fk_group_id=_gid_
			).count()

			if _kw__all_ == 0:
				_at__common_.__change_group_manual_call_status__(_g_record_.id, "NOPE")
				__group_failed_dash_calculation__(_g_record_)
			else:
				# All keywords are already done (manual_call_status=False)
				__group_dash_calculation__(_g_record_)

	return _task__count_


@api_view(['GET'])
def automation_manual_call(request, _ustr_, _kstr_):
	_start__time_ = _date__time_.now()
	# Instance-wide ceiling on concurrent refreshes -- it protects this box.
	# It is NOT the fairness rule: which tenant runs next is decided by
	# __next_manual_group__, so one account's backlog cannot consume it.
	_max__wait__count_ = 5

	_base__result_, _setting__data_ = _at__common_.__base_validation__(request, _ustr_)

	if _base__result_ and _kstr_.isdigit():
		_core__mode_ = _at__common_.__ms_record__("MANUAL", "_mode__check_")
		if _core__mode_ == True:
			if int(_kstr_) % 25 == 0:
				_gp__result_ = _aCL_.automation_comp_analyse("MANUAL")
				if _gp__result_ == "COMP":
					return JsonResponse({'status': 'Neural competitor project for manual refresh completed'})
				elif _gp__result_ == "CALC":
					return JsonResponse({'status': 'Neural competitor project for manual refresh calculation updated'})
				else:
					return JsonResponse({'status': 'No Neural competitor project for manual found'})
			elif int(_kstr_) % 3 == 0:
				_gp__result_ = _aAS_.automation_ai_analyse("INDIRECT")
				if _gp__result_ == "COMP":
					return JsonResponse({'status': 'Neural competitor analyse refresh completed'})
				else:
					return JsonResponse({'status': 'No Neural competitor analyse found'})
			else:
				_gp__result_ = 0

				# A refresh that died mid-run left its project claimed as WAIT
				# and nothing ever released it.  Sweep first: otherwise those
				# strandings accumulate against the ceiling below and, once
				# enough of them exist, instant refresh is off for everybody.
				_at__common_.__sweep_stale_group_claims__("MANUAL")

				_wait__count_ = _gp__record_.objects.filter(manual_grp_trigger="WAIT").count()
				if _wait__count_ <= _max__wait__count_:

					# Which project runs next is decided per tenant; this
					# ceiling is only about how much this box will run at once.
					_gp__active__data_ = _at__common_.__next_manual_group__()
					if _gp__active__data_ is not None:

						# Claim by compare-and-set: only the caller that moved
						# the project out of INIT runs it, so a double-clicked
						# "Refresh" that arrives twice is fetched once.
						if _at__common_.__change_group_manual_call_status__(
							_gp__active__data_.id, "WAIT", "INIT"
						) == "success":
							_at__common_.__macro_problem__(_gp__active__data_.id, "MANUAL")
							_gp__result_ = __neural_manual_concurrency_task__(_gp__active__data_)

				if _gp__result_:
					_end__time_ = _date__time_.now()
					_wd_.coreLog(
						" > TOTAL REQUEST " + str(_gp__result_) + " >> START " + str(_start__time_) + " >>> END " + str(_end__time_),
						"MANUAL"
					)
					return JsonResponse({'status': 'Neural instant refresh completed', 'start': str(_start__time_), 'end': str(_end__time_)})
				else:
					return JsonResponse({'status': 'No neural instant refresh allocation found'})
		else:
			return JsonResponse({'status': 'Neural engine turned off'})

	return JsonResponse({'status': 'Oops, visit: tracker.com'})
