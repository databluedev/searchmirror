from django.shortcuts import render
from django.conf import settings as _def_

from project.machine.serializers import ClientTrackerSerializer as _ct__time__allocate_
from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_, ManualRefresh as _mr__record_
from project.machine.models import ClientTracker as _ct__record_
from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_

from datetime import datetime as _date__time_, date as _dt_, time as _tm_

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from project.machine import watchdog as _wd_, automation_common as _at__common_, automation_proxy as _at__proxy_
from project.machine import formulate as _at__calculate_, domains as _domain__get_
from project.machine.competitor import automation_analyse as _aAS_
from project.machine.competitor import automation_call as _aCL_
from project.machine.competitor import automation_comp_reload as _aCR_

import concurrent.futures as _automation__futures_


# Consecutive lost claim races after which this request stops looking. A loss
# means another worker took that project, so the right move is to take the next
# one; the cap only stops a request spinning against selection when every
# project left is already held.
_LOST_CLAIM_CAP_ = 3


def __automation_slot_allocation__(_kstr_):
	_dt__today_ = _dt_.today()
	_slot__start_, _slot__end_ = (None, ) * int('0b10', 2)

	if int(_kstr_) == 1:
		_execute__time_ = _tm_(hour=0, minute=0, second=0)
		_slot__start_ = _date__time_.combine(_dt__today_, _execute__time_)
		_execute__time_ = _tm_(hour=6, minute=0, second=0)
		_slot__end_ = _date__time_.combine(_dt__today_, _execute__time_)
	elif int(_kstr_) == 2:
		_execute__time_ = _tm_(hour=6, minute=0, second=0)
		_slot__start_ = _date__time_.combine(_dt__today_, _execute__time_)
		_execute__time_ = _tm_(hour=12, minute=0, second=0)
		_slot__end_ = _date__time_.combine(_dt__today_, _execute__time_)
	elif int(_kstr_) == 3:
		_execute__time_ = _tm_(hour=12, minute=0, second=0)
		_slot__start_ = _date__time_.combine(_dt__today_, _execute__time_)
		_execute__time_ = _tm_(hour=18, minute=0, second=0)
		_slot__end_ = _date__time_.combine(_dt__today_, _execute__time_)
	elif int(_kstr_) == 4:
		_execute__time_ = _tm_(hour=18, minute=0, second=0)
		_slot__start_ = _date__time_.combine(_dt__today_, _execute__time_)
		_execute__time_ = _tm_(hour=23, minute=59, second=59)
		_slot__end_ = _date__time_.combine(_dt__today_, _execute__time_)

	return _slot__start_, _slot__end_


# ── AUTOMATION STAGE 2 — async fetch via DataBlue, sync DB updates ───────────
def __automation_concurrency_pool__(_gid_, _kw__task_, _kw__task__count_, _comp__dict_, _comp__list_):
	_max__concurrency_ = min(100, _kw__task__count_)

	if not _kw__task_:
		return _comp__dict_

	# Build keyword task collection
	_kw__complete__url_ = dict()
	# Per-run heartbeat state.  This loop is two DB round trips per keyword and
	# runs before the first request, so on a large project it alone can outlast
	# the stale-claim window and get the project taken off this worker.
	_claim__state_ = dict()
	for _kw__single__task_ in _kw__task_:
		_at__common_.__touch_group_claim__(_gid_, "ENGINE", _claim__state_)
		_kw__flag_ = 0
		if _kw__single__task_.keyword is None:
			_kw__flag_ = 1
		elif len(_kw__single__task_.keyword.strip()) == 0:
			_kw__flag_ = 1

		if _kw__flag_ == 1:
			_d__keyword_.objects.filter(id=_kw__single__task_.id).delete()
		elif _at__common_.__claim_keyword__(_kw__single__task_.id, "ENGINE"):
			# Only a keyword this worker actually claimed is fetched.  Without
			# the claim two overlapping passes both selected the same "not
			# done" rows and the account was billed twice for every one of
			# them.
			_kw__complete__url_.update({
				str(_kw__single__task_.id): _at__proxy_.__automation_search_scrap_url__(_kw__single__task_)
			})

	if not _kw__complete__url_:
		return _comp__dict_

	# ── Async fetch + inline per-keyword DB writes via DataBlue ─────────────
	# __automation_fetch_and_process__ dispatches the callback to a thread pool
	# the instant each HTTP response arrives — no waiting for the whole batch.
	# All per-keyword DB writes happen inline in the callback; only competitor
	# dict updates are deferred to after the pipeline drains (main-thread only).
	_comp__updates_ = []  # list of (kw_id_int, clist) tuples

	def _db_and_parse_(_result_):
		"""Runs in thread pool the instant a DataBlue response arrives."""
		_kw__id_ = _result_["item_id"]
		if _kw__id_ not in _kw__complete__url_ or not _kw__id_.isdigit():
			return None

		_kw_id_int_ = int(_kw__id_)

		# This run is alive; say so before the sweep decides otherwise.
		_at__common_.__touch_group_claim__(_gid_, "ENGINE", _claim__state_)

		# Per-keyword counter increments — MUST use __raw__={'id': ...} syntax
		_kw__record_.objects.filter(__raw__={'id': _kw_id_int_}).update(inc__auto_refresh_count=1)
		_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__daily_automation_count__0=1)

		_val_, _clist_, _outcome_ = _at__proxy_.__automation_process_result__(
			"ENGINE", _kw__id_, _kw__complete__url_, _comp__list_, _result_
		)

		# Per-outcome proxy counters, then the failure goes to the recorder:
		# the attempt is counted, the keyword is left retryable with a backoff,
		# and only an exhausted budget writes the terminal status.  Forcing
		# auto_call_status='done' here is the ancestor bug that stopped 1,437
		# keywords retrying (docs/ORCHESTRATION.md 2) -- it reports a failure
		# as a finished measurement and no later pass ever looks at it again.
		if _outcome_ == "ok":
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_success_count=1, proxy_reset_counter=0)
		elif _outcome_ == "429":
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_exceeds_count=1, inc__proxy_reset_counter=1)
			_at__common_.__record_keyword_failure__(_kw_id_int_, "ENGINE", "rate limited (429)")
			return None
		else:
			_ms__record_.objects.filter(__raw__={'id': 1}).update(inc__proxy_invalid_count=1, inc__proxy_reset_counter=1)
			_at__common_.__record_keyword_failure__(
				_kw_id_int_, "ENGINE", "provider " + str(_result_.get("status"))
			)
			return None

		_at__proxy_.__automation_collective_parser__(
			_mode_="ENGINE",
			_index_=str(_val_['id']),
			_kw__data_={str(_val_['id']): _val_},
		)

		if _clist_ and _kw__id_.isdigit():
			# Append to a shared list; lock not needed because list.append is atomic under GIL
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

	# Apply competitor updates after pipeline drains
	for _item__id_, _clist_ in _comp__updates_:
		for _d_ in _clist_:
			if _d_ in _comp__dict_:
				_comp__dict_ = _at__common_.__get_competitor_list_update__(str(_d_), _item__id_, _comp__dict_)

	return _comp__dict_


# ── AUTOMATION STAGE 1 ───────────────────────────────────────────────────────
def __automation_concurrency_task__(_g_record_):
	_gid_ = _g_record_.id
	_g__comp__flag_ = False

	if _gid_ > 0:
		_kw__all_ = _kw__record_.objects.filter(fk_group_id=_gid_).count()

		if _kw__all_ > 0:
			_comp__dict_, _comp__list_ = dict(), list()
			_kw__done_ = _kw__record_.objects.filter(fk_group_id=_gid_, auto_call_status="done").count()

			if _kw__done_ == _kw__all_:
				_g__comp__flag_ = True
			else:
				# Fetch ALL pending keywords at once — the sliding window is
				# enforced by asyncio.Semaphore(100) inside
				# __automation_fetch_all__, so 100 requests stay in-flight
				# continuously with zero idle time at batch boundaries.
				_kw__task_ = _kw__record_.objects.filter(
					fk_group_id=_gid_, auto_call_status__ne="done"
				).order_by('+auto_refresh_count').all()
				_kw__task__count_ = len(_kw__task_)

				if _kw__task__count_ > 0:
					_comp__dict_ = __automation_concurrency_pool__(
						_gid_, _kw__task_, _kw__task__count_, _comp__dict_, _comp__list_
					)

				_g__comp__flag_ = True

			if _g__comp__flag_:
				# COMP means completed, and it is read that way everywhere: the
				# selector below will not look at a COMP project again today,
				# and the scheduler has already pushed its next run out by a
				# day.  Writing it over a run that left keywords unmeasured
				# reported a failure as a finished measurement -- the same
				# mistake __record_keyword_failure__ exists to avoid, one level
				# up -- and it is why the retry budget and the backoff below it
				# were unreachable on the scheduled path: keywords were left
				# 'fail' with a retry time minutes away and nothing ever came
				# back for them.  STOP is the honest end-state for an
				# incomplete run and is already used for one at the bottom of
				# this function.  Everything else about the wrap-up is
				# unchanged: the ranks that DID land still need their dashboard.
				_kw__pending_ = _kw__record_.objects.filter(
					fk_group_id=_gid_, auto_call_status__ne="done"
				).count()

				if _kw__pending_:
					_at__common_.__change_group_call_status__(_gid_, "STOP")
					_wd_.coreLog(
						" > RUN INCOMPLETE >> GROUP_ID = "+str(_gid_)
						+" >>> UNMEASURED = "+str(_kw__pending_)+" OF "+str(_kw__all_),
						"ENGINE"
					)
				else:
					_at__common_.__change_group_call_status__(_gid_, "COMP")

				_mr__record_.objects.filter(fk_group_id=_gid_).update(refresh_time=_date__time_.now())
				_at__calculate_.dashboardNewGraph("ENGINE", _gid_)
				_domain__get_.domainInitiate(_g_record_)

				if _comp__dict_:
					pass

				_us__gp__count_ = _gp__record_.objects.filter(fk_user_id=_g_record_.fk_user_id).count()
				_us__gp__comp__count_ = _gp__record_.objects.filter(
					fk_user_id=_g_record_.fk_user_id, group_call_status="COMP"
				).count()

				if int(_us__gp__count_) == int(_us__gp__comp__count_):
					pass
			else:
				_at__common_.__change_group_call_status__(_gid_, "STOP")
		else:
			_at__common_.__change_group_call_status__(_gid_, "DROP")

	return True


# ── SLOT CHECKER ─────────────────────────────────────────────────────────────
def __automation_slot_checker__(_slot__start_, _slot__end_):
	# Projects due in this slot first, then anything else still outstanding.
	#
	# There is no payment-tier filter.  The ancestor selected only
	# paymentmode in {1,A..E} and swept up "F" (expired) in a third pass --
	# subscription tiers from a product that billed for rankings.  Under BYOK
	# the account holder pays the provider directly and nobody has priority
	# for having paid us; worse, the field defaults to "" here, so the filter
	# matched no group at all and nothing was ever selectable.
	_gp__slot__data_ = _gp__record_.objects.filter(
		group_call_status__nin=["COMP", "PROC", "STOP", "DROP"],
		project_automation_time__gte=_slot__start_,
		project_automation_time__lte=_slot__end_,
	)

	if _gp__slot__data_.count():
		return "_slot_", _gp__slot__data_

	_gp__slot__data_ = _gp__record_.objects.filter(
		group_call_status__nin=["COMP", "PROC", "STOP", "DROP"],
	)
	if _gp__slot__data_.count():
		return "_non__slot_", _gp__slot__data_

	return (False, ) * int('0b10', 2)


@api_view(['GET'])
def automation_engine_call(request, _ustr_, _kstr_):
	_base__result_, _setting__data_ = _at__common_.__base_validation__(request, _ustr_)

	if _base__result_ and _kstr_.isdigit():
		if int(_kstr_) < 1:
			_ct__time__allocate_(_ct__record_.objects.all(), many=True, context={'type': 'PAT'}).data

		_gp__slot__flag_ = None
		_slot__start_, _slot__end_ = __automation_slot_allocation__(_kstr_)

		# A run that died left its project claimed as PROC, where the selection
		# below can never see it again.  Release those before selecting.
		_at__common_.__sweep_stale_group_claims__("ENGINE")

		if _slot__start_ is not None and _slot__end_ is not None:
			_gp__slot__flag_, _gp__slot__data_ = __automation_slot_checker__(_slot__start_, _slot__end_)
		else:
			_gp__slot__data_ = _gp__record_.objects.filter(
				group_call_status__nin=["COMP", "PROC", "STOP", "DROP"],
			)
			if _gp__slot__data_.count():
				_gp__slot__flag_ = "_non__slot_"

		# Losing a claim race means another worker took THAT project, not that
		# there is no work left.  This request used to break out of the drain
		# entirely on the first loss and still answer "completed": with six
		# concurrent requests over fourteen queued projects, three of them ran
		# nothing at all and said they had.  Re-selecting is safe -- the winner
		# has already written PROC, which the selector excludes, so the same
		# project cannot come back -- but an unbounded retry needs a floor, so
		# a run that keeps losing gives up and says which it was.
		_lost__claims_ = 0
		# Projects this request has already run, per account.  Selection reads
		# it to take turns between accounts -- see __next_engine_group__.
		_served__by__tenant_ = dict()

		if _gp__slot__flag_:
			while _gp__slot__flag_:
				_core__mode_ = _at__common_.__ms_record__("ENGINE", "_mode__check_")

				if _gp__slot__flag_ == "_non__slot_":
					_gp__order_ = '-created_date'
				elif _gp__slot__flag_ == "_slot_":
					# Due first.  The ancestor ordered by payment tier, which
					# under BYOK ranks nobody above anybody -- staleness is the
					# fair tiebreak (docs/ORCHESTRATION.md 3).
					_gp__order_ = '+project_automation_time'
				else:
					# Reached only with an error flag already set below, and it
					# is how this loop exits: no order, no candidate, break.
					_gp__order_ = None

				_gp__active__data_ = None
				if _gp__order_ and _core__mode_:
					_gp__active__data_ = _at__common_.__next_engine_group__(
						_gp__slot__data_, _served__by__tenant_, _gp__order_
					)

				if _gp__active__data_ is not None:
					if int(getattr(_gp__active__data_, 'id', 0) or 0) > 0:
						_au__status__flag_ = _at__common_.__au_status_callback__(_gp__active__data_)
						if _au__status__flag_:
							# Compare-and-set against the status just read:
							# whoever transitions the project owns it.
							if _at__common_.__change_group_call_status__(
								_gp__active__data_.id, "PROC", _gp__active__data_.group_call_status
							) == "success":
								_lost__claims_ = 0
								_served__by__tenant_[_gp__active__data_.fk_user_id] = (
									_served__by__tenant_.get(_gp__active__data_.fk_user_id, 0) + 1
								)
								_at__common_.__macro_problem__(_gp__active__data_.id, "ENGINE")
								__automation_concurrency_task__(_gp__active__data_)
							else:
								_wd_.coreLog(
									" > GROUP ALREADY CLAIMED BY ANOTHER WORKER >> GROUP_ID = "
									+ str(_gp__active__data_.id), "ENGINE"
								)
								_lost__claims_ += 1
								if _lost__claims_ >= _LOST_CLAIM_CAP_:
									_gp__slot__flag_ = "ERROR-BUSY"
									break
						elif _au__status__flag_ is None:
							# The entitlement question could not be answered, so
							# nothing is concluded from it.  The project is
							# parked in an ordinary end-state -- the scheduler
							# queues it again tomorrow -- and its mail is left
							# alone, because switching a user's notifications
							# off is a decision and this code did not get to
							# make one.  It must not stay INIT: the selector
							# would hand back the same project on the next turn
							# of this loop and spin the request forever.
							_at__common_.__change_group_call_status__(
								_gp__active__data_.id, "STOP", _gp__active__data_.group_call_status
							)
						else:
							# A real answer: no account row, or a status that is
							# not default/active.  Claim it first -- writing
							# PROC unconditionally let two overlapping workers
							# both run the macro pass over the same project.
							if _at__common_.__change_group_call_status__(
								_gp__active__data_.id, "PROC", _gp__active__data_.group_call_status
							) == "success":
								_lost__claims_ = 0
								_served__by__tenant_[_gp__active__data_.fk_user_id] = (
									_served__by__tenant_.get(_gp__active__data_.fk_user_id, 0) + 1
								)
								_at__common_.__macro_problem__(_gp__active__data_.id, "ENGINE")
								_at__common_.__change_group_call_status__(_gp__active__data_.id, "DROP")
								_au__record_.objects.filter(fb_user_id=_gp__active__data_.fk_user_id).update(
									automatic_mail_status="STOP"
								)
							else:
								_wd_.coreLog(
									" > GROUP ALREADY CLAIMED BY ANOTHER WORKER >> GROUP_ID = "
									+ str(_gp__active__data_.id), "ENGINE"
								)
								_lost__claims_ += 1
								if _lost__claims_ >= _LOST_CLAIM_CAP_:
									_gp__slot__flag_ = "ERROR-BUSY"
									break
					else:
						# A selectable project with no usable id.  Nothing can
						# claim it, so leaving it INIT would hand it straight
						# back on the next turn and spin this request forever;
						# stop and say so instead.
						_gp__slot__flag_ = "ERROR-GID"
						_wd_.coreLog(
							" > NO ID EXISTS ON GROUP >> " + str(getattr(_gp__active__data_, 'group_name', '')),
							"ENGINE"
						)

					if _gp__slot__flag_ != "ERROR-GID":
						_gp__slot__flag_, _gp__slot__data_ = __automation_slot_checker__(_slot__start_, _slot__end_)

				elif _core__mode_ == False:
					_gp__slot__flag_ = "ERROR-OFF"
					break
				else:
					break

			if _gp__slot__flag_ == "ERROR-OFF":
				_wd_.coreLog(" > TEMPORARILY SHUTDOWN >> AUTOMATION FOR PROJECT BREAK ", "ENGINE")
				return JsonResponse({'status': "Neural engine turned off #" + str(_kstr_)})
			elif _gp__slot__flag_ == "ERROR-GID":
				return JsonResponse({'status': "Neural engine group identification error #" + str(_kstr_)})
			elif _gp__slot__flag_ == "ERROR-BUSY":
				# Not "completed".  Other workers hold what is left of the
				# queue, and reporting that as a finished drain is how a pass
				# that ran nothing still read as a success in every log line.
				return JsonResponse({'status': "Neural engine queue held by other workers #" + str(_kstr_)})
			else:
				return JsonResponse({'status': "Neural engine automation completed for the slot #" + str(_kstr_)})
		else:
			return JsonResponse({'status': 'Neural engine no allocation found in slot', 'start': str(_slot__start_), 'end': str(_slot__end_)})
	else:
		return JsonResponse({'status': 'Neural engine autorization error'})

	return JsonResponse({'status': 'Oops, visit: tracker.com'})
