import os as _os_
from django.shortcuts import render
from django.conf import settings as _def_

from project.machine.models import Keyword as _kw__record_, Group as _gp__record_, Mainsettings as _ms__record_, Accountusage as _au__record_
from project.machine.models import KeywordResearch as _kw__research_

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_
from project.machine.submodels.researchmodels import DKeywordResearch as _dK__research_ 
from project.machine import watchdog as _wd_

from project.machine.bot import clean as _clean_, snippet as _snippet_
from project.machine import formulate as _at__calculate_

from datetime import datetime as _date__time_, date as _dt_, timedelta as _time__delta_
from uuid import uuid4

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from urllib.parse import urlparse  

import re as _re_
import hmac as _hmac_ 

# Callers allowed to drive the automation endpoints. This was the ancestor's
# own production box, hardcoded -- which both leaked their infrastructure and
# refused every self-hosted caller, since a sibling container arrives as
# 172.x, not 127.0.0.1. Set ENGINE_ALLOWED_IPS (comma separated) to whatever
# actually calls this instance.
_server__ip_ = [ip.strip() for ip in
                _os_.environ.get("ENGINE_ALLOWED_IPS", "127.0.0.1").split(",")
                if ip.strip()]

# Claim and retry tuning.
#
# A worker that dies mid-run leaves its claim behind; anything claimed longer
# ago than the sweep window is assumed dead and returned to the pool.  A live
# run renews its claim on the heartbeat interval, so the window has to outlast
# a missed heartbeat, not the whole run.
#
# The attempt cap bounds how often one keyword may be retried before it is
# recorded as unmeasured for the day.  Under BYOK every attempt is billed to
# the account holder, so the cap is deliberately small and the backoff doubles.
#
# The WAIT caps are two different guards: the per-tenant one keeps one account
# from taking the whole queue, the instance one protects this box.  Counting
# only the instance-wide figure -- which is what the ancestor did -- means one
# account's backlog stops refresh for every other account.
_stale__claim__minutes_ = int(_os_.environ.get("ENGINE_STALE_CLAIM_MINUTES", "30"))
_claim__heartbeat__seconds_ = int(_os_.environ.get("ENGINE_CLAIM_HEARTBEAT_SECONDS", "60"))
_keyword__attempt__cap_ = int(_os_.environ.get("ENGINE_KEYWORD_ATTEMPT_CAP", "3"))
_keyword__backoff__minutes_ = int(_os_.environ.get("ENGINE_KEYWORD_BACKOFF_MINUTES", "15"))
_tenant__wait__cap_ = int(_os_.environ.get("ENGINE_TENANT_WAIT_CAP", "1"))

def trim(value):
	return value.strip()

def __uuid__(): 
	return str(uuid4())

def extract_domain(url, remove_http=True):
	uri = urlparse(url)
	if remove_http:
		# domain_name = f"{uri.netloc}".replace("www.", "")
		if uri.netloc: 
			domain_name = f"{uri.netloc}".replace("www.", "") 
		else:
			domainDivision = f"{uri.path}".replace("www.", "").split('/')
			domain_name = domainDivision[0] if len(domainDivision) > 0 else domainDivision    
	else:
		domain_name = f"{uri.netloc}".replace("www.", "")

	return domain_name  

def __ip_validation__(request):
	_remote__addr_ = str(request.META.get('REMOTE_ADDR')) 
	return True if _remote__addr_ in _server__ip_ else False   

def __base_validation__(request, _ustr_):
	_setting__data_ = __ms_record__("ENGINE", "_")

	# A caller that presents the shared engine token is trusted. This is how the
	# backend drives the manual queue on demand ("Run now") over the private
	# compose network, without needing to be on the IP allowlist or to know the
	# settings oid. compare_digest is constant-time. With the token unset there
	# is no bypass, so nothing changes for an instance that has not opted in.
	_token_ = _os_.environ.get("ENGINE_TRIGGER_TOKEN", "")
	if _token_:
		_supplied_ = request.META.get("HTTP_X_ENGINE_TOKEN", "")
		if _supplied_ and _hmac_.compare_digest(str(_supplied_), str(_token_)):
			return int('0b1', 2), _setting__data_

	if hasattr(_setting__data_, 'oid') and __ip_validation__(request) and hasattr(_setting__data_, 'proxy_reset_counter'):
		if len(_ustr_) > int('0b1010', 2) and _re_.search(_ustr_, str(_setting__data_.oid)):
			return int('0b1', 2), _setting__data_ 

	return (int('0b0', 2), ) * int('0b10', 2)

def __bot_language__(_lang_):
	if _lang_ != "" and _lang_ != None:
		_lang_ = trim(_lang_)
		if _lang_ in _snippet_._snippet__futures_:
			return _snippet_._snippet__futures_[_lang_]
	
	return _snippet_._snippet__futures_['default']

def __bot_clean__(_lang_):
	_lang_ = trim(_lang_)
	if _lang_ != "" and _lang_ != None:
		if _lang_ in _clean_._clean__futures_:
			return _clean_._clean__futures_[_lang_]
	
	return _clean_._clean__futures_['default']
	
# CHANGE RESEARCH GOOGLE AND ONTYPE CALL STATUS
def __change_research_call_status__(_id_, _status_, _type_="google"):
	# google_status  - "VOID", "INIT", "SCHD", "FAIL", "DONE"
	#		VOID ON INITIALISATION, INIT ON PROXY, SCHD ON PARSER, FAIL
	# ontype_status  - "VOID", "INIT", "SCHD", "FAIL", "DONE", "START", "STOP", "COMP"	
	if _id_ > 0 and _type_ in ["google", "ontype", "both"]: 
		_research_ = _kw__research_.objects.filter(__raw__= {'id': _id_})

		if _type_ == "both":
			_research_.update(google_status=_status_, ontype_status=_status_)
			return True
		elif _type_ == "ontype":
			_research_.update(ontype_status=_status_)   
			return True
		elif _type_ == "google": 
			_research_.update(google_status=_status_)   
			return True
		else:
			pass

	return False

def __change_research_call_status_in_list__(_id_array_, _status_):
	if len(_id_array_): 
		_dK__research_.objects.filter(id__in=_id_array_).update(google_status=_status_) 
		return True

	return False

# CHANGE GROUP CALL STATUS
def __change_group_call_status__(_id_, _status_, _expect_=None):    # INIT, PROC, COMP, STOP, DROP
	# Passing _expect_ turns this into a compare-and-set: the write only lands
	# while the group still holds the status the caller read, and only the
	# caller whose write matched is told "success".  Read-then-update told
	# every concurrent caller "success" because the group merely existed, so
	# two workers ran one project and the account was billed twice.
	if _id_ == "all":
		if _expect_:
			return "failed"
		_groups_ = _gp__record_.objects.all()
	elif _id_ > 0:
		_query_ = {'id': _id_}
		if _expect_:
			_query_['group_call_status'] = _expect_
		_groups_ = _gp__record_.objects.filter(__raw__= _query_)
	else:
		return "failed"

	if _groups_.update(group_call_status=_status_, call_claim_date=_date__time_.now()):
		return "success"
	else:
		return "failed"

# CHANGE MANUAL CALL STATUS FOR GROUP
def __change_group_manual_call_status__(_id_, _status_, _expect_=None):    # INIT, WAIT, DONE, NOPE
	# Same compare-and-set as the engine side: a double-clicked "Refresh"
	# reaches here twice and only the transition that actually happened may
	# report success, or both callers fetch the project and the account pays
	# for every keyword twice.
	_query_ = {'id': _id_}
	if _expect_:
		_query_['manual_grp_trigger'] = _expect_

	_groups_ = _gp__record_.objects.filter(__raw__= _query_)

	if _groups_.update(manual_grp_trigger=_status_, call_claim_date=_date__time_.now()):
		return "success"
	else:
		return "failed"

# NEXT MANUAL GROUP TO CLAIM — chosen per tenant, not first-come across all
def __next_manual_group__():
	"""Return the next requested project whose account is not already busy.

	Which project runs next is decided per tenant: an account that already
	holds its share of in-flight refreshes is skipped and the next account's
	project is taken instead, so one account's queue -- or one account's
	stranded run -- cannot stop refresh for everybody else.  Oldest project
	first is the tiebreak inside that.

	Returns a Group document, or None when nothing is claimable right now.
	"""
	_busy__tenants_ = dict()
	for _uid_ in _gp__record_.objects.filter(manual_grp_trigger="WAIT").values_list('fk_user_id'):
		_busy__tenants_[_uid_] = _busy__tenants_.get(_uid_, 0) + 1

	for _group_ in _gp__record_.objects.filter(manual_grp_trigger="INIT").order_by('+created_date'):
		if int(getattr(_group_, 'id', 0) or 0) <= 0:
			continue
		if _busy__tenants_.get(_group_.fk_user_id, 0) < _tenant__wait__cap_:
			return _group_

	return None

# NEXT SCHEDULED GROUP TO CLAIM — round-robin across accounts
def __next_engine_group__(_candidates_, _served_, _order_):
	"""Return the next queued project to rank, or None.

	Accounts take turns.  Ordering the queue by one key alone drains an
	account's entire backlog before the next account's first project: with
	eight projects on one account and six spread over two others, the measured
	drain order was AAAAAAAABBBBCC.  Under BYOK that is the starvation
	docs/ORCHESTRATION.md 3 rules out -- an account with 10,000 keywords must
	not hold up one with 50 -- and the manual queue already refuses to do it
	(__next_manual_group__ above).  _served_ counts what THIS request has
	already run per account, so the least-served account goes next and _order_
	is only the tiebreak inside it.

	Both reads cost the same whatever the queue length: one distinct() and one
	indexed first-row fetch.  Choosing by materialising the candidate set --
	which is what len() on the queryset did on every turn of the drain loop --
	makes draining P projects O(P^2): 2.4ms of selection at 14 queued projects,
	41.8ms at 200, paid once per project drained.
	"""
	try:
		_tenants_ = list(_candidates_.distinct('fk_user_id'))
	except Exception:
		_tenants_ = []

	if not _tenants_:
		return _candidates_.order_by(_order_).first()

	_tenants_.sort(key=lambda _u_: (_served_.get(_u_, 0), _u_))

	for _uid_ in _tenants_:
		_group_ = _candidates_.filter(fk_user_id=_uid_).order_by(_order_).first()
		if _group_ is not None:
			return _group_

	return None

# RETURN GROUP CLAIMS HELD BY A DEAD WORKER TO THE POOL
def __sweep_stale_group_claims__(_mode_):
	"""Reset groups whose claim outlived any run that could still be alive.

	A run that dies mid-flight -- container restart, an error escaping the
	pool -- leaves its project claimed.  Nothing ever cleared those, so the
	project was stranded for good; and because the concurrency cap counted
	claims across every account, a handful of strandings disabled refresh
	instance-wide.  Rows claimed before this field existed carry no claim date
	and are swept too: only a stranded row can be in a claimed state without
	one.
	"""
	_cutoff_ = _date__time_.now() - _time__delta_(minutes=_stale__claim__minutes_)
	_stale_ = [{'call_claim_date': {'$lt': _cutoff_}}, {'call_claim_date': None}]

	if _mode_ == "MANUAL":
		_swept_ = _gp__record_.objects.filter(__raw__= {
			'manual_grp_trigger': "WAIT", '$or': _stale_,
		}).update(manual_grp_trigger="INIT")
	else:
		_swept_ = _gp__record_.objects.filter(__raw__= {
			'group_call_status': "PROC", '$or': _stale_,
		}).update(group_call_status="INIT")

	if _swept_:
		_wd_.coreLog(" > STALE CLAIM SWEEP >> GROUPS RELEASED = "+str(_swept_), _mode_)

	return _swept_

# KEEP A LIVE RUN'S CLAIM FRESH SO THE SWEEP ABOVE CANNOT TAKE IT
def __touch_group_claim__(_gid_, _mode_, _state_):
	"""Renew the claim of a run that is still working.

	call_claim_date was stamped once, when the project was taken, and never
	again -- so the sweep could not tell a run 31 minutes into its work from a
	worker that died 31 minutes ago.  It released the live one, the very next
	selection pass in the same request took it, and both workers fetched every
	keyword in the project: the account paid twice for a project whose only
	fault was being large enough to need more than the window.

	_state_ is a per-run dict; the throttle makes this one small write a minute
	instead of one per keyword.  Two callback threads can pass the check at
	once and both write, which costs a duplicate update and nothing else, so
	the check is deliberately unlocked.  The claimed status is part of the
	match, so a heartbeat arriving after the run has finished cannot revive a
	claim on a project that has already moved on.
	"""
	if not _gid_ or _gid_ <= 0:
		return False

	_now_ = _date__time_.now()
	_last_ = _state_.get('at')
	if _last_ and (_now_ - _last_).total_seconds() < _claim__heartbeat__seconds_:
		return False
	_state_['at'] = _now_

	if _mode_ == "MANUAL":
		_query_ = {'id': _gid_, 'manual_grp_trigger': "WAIT"}
	else:
		_query_ = {'id': _gid_, 'group_call_status': "PROC"}

	return bool(_gp__record_.objects.filter(__raw__= _query_).update(call_claim_date=_now_))

# ATOMIC KEYWORD CLAIM — only the caller that transitions the row may fetch it
def __claim_keyword__(_id_, _mode_):
	"""Take exclusive ownership of one keyword for this run.

	Keywords were never claimed at all: every worker selected the same
	"not done" set and every worker fetched it, so two overlapping passes over
	one project billed the account twice for every keyword.  The claim is the
	update itself -- Mongo matches and sets in a single operation, so exactly
	one caller sees a match.

	A claim older than the sweep window belonged to a worker that died and is
	taken over here.  Without that the row stayed busy forever and became
	invisible to every later pass.
	"""
	if _id_ <= 0:
		return False

	_cutoff_ = _date__time_.now() - _time__delta_(minutes=_stale__claim__minutes_)

	if _mode_ == "MANUAL":
		_query_ = {
			'id': _id_,
			'manual_call_status': True,
			'$or': [
				{'manual_call_mode': {'$ne': "busy"}},
				{'call_claim_date': {'$lt': _cutoff_}},
			],
		}
		_claimed_ = _kw__record_.objects.filter(__raw__= _query_).update(
			manual_call_mode="busy", call_claim_date=_date__time_.now()
		)
	else:
		# Two conditions, both required: the keyword is not already claimed by
		# a live worker, and its backoff has elapsed.  The backoff belongs here
		# rather than in the selection query because this is the single gate
		# every provider call passes through -- checked anywhere else it is
		# advisory, and a failing keyword would be re-billed on the next tick.
		_query_ = {
			'id': _id_,
			'$and': [
				{'$or': [
					{'auto_call_status': {'$nin': ["busy", "done"]}},
					{'call_claim_date': {'$lt': _cutoff_}},
				]},
				{'$or': [
					{'call_retry_date': None},
					{'call_retry_date': {'$lte': _date__time_.now()}},
				]},
			],
		}
		_claimed_ = _kw__record_.objects.filter(__raw__= _query_).update(
			auto_call_status="busy", call_claim_date=_date__time_.now()
		)

	return bool(_claimed_)

# RECORD ONE FAILED KEYWORD ATTEMPT
def __record_keyword_failure__(_id_, _mode_, _reason_):
	"""Count a failed attempt and leave the keyword in a state a scheduler can act on.

	The ancestor wrote the terminal status here -- auto_call_status='done',
	commented "so cron doesn't re-pick failed kw" -- which is exactly how 1,437
	keywords stopped retrying for good (docs/ORCHESTRATION.md 2).  A failure is
	not a result.  The keyword stays 'fail' and carries the earliest time it
	may be tried again; only an exhausted attempt budget writes the terminal
	status, and the reason is written with it so "we could not measure this"
	stays distinguishable from "it does not rank".

	Returns "retry", "exhausted", or "failed" when there is no such keyword.
	"""
	if _id_ <= 0:
		return "failed"

	_keywords_ = _kw__record_.objects.filter(__raw__= {'id': _id_})

	if not _keywords_.update(
		inc__call_fail_count=1,
		call_fail_reason=str(_reason_)[:80],
		call_fail_date=_date__time_.now(),
	):
		return "failed"

	_kw__data_ = _keywords_.first()
	_attempts_ = int(getattr(_kw__data_, 'call_fail_count', 0) or 0) if _kw__data_ else _keyword__attempt__cap_

	if _mode_ == "MANUAL":
		# A manual refresh is one attempt the account holder asked for and is
		# billed for.  It is never retried behind their back -- the run ends
		# here, visibly failed rather than reported done, and they decide
		# whether to spend again.
		_keywords_.update(manual_call_status=False, manual_call_mode="fail")
		_wd_.coreLog(" > KEYWORD FAILED >> KEY_ID = "+str(_id_)+" >>> REASON = "+str(_reason_), _mode_)
		return "retry"

	if _attempts_ >= _keyword__attempt__cap_:
		_keywords_.update(auto_call_status="done", call_retry_date=None)
		_wd_.coreLog(
			" > KEYWORD ATTEMPTS EXHAUSTED >> KEY_ID = "+str(_id_)
			+" >>> ATTEMPTS = "+str(_attempts_)+" >>> REASON = "+str(_reason_),
			_mode_
		)
		return "exhausted"

	_keywords_.update(
		auto_call_status="fail",
		call_retry_date=_date__time_.now() + _time__delta_(
			minutes=_keyword__backoff__minutes_ * (2 ** (_attempts_ - 1))
		),
	)
	_wd_.coreLog(
		" > KEYWORD FAILED >> KEY_ID = "+str(_id_)
		+" >>> ATTEMPT = "+str(_attempts_)+" >>> REASON = "+str(_reason_),
		_mode_
	)
	return "retry"

# CHANGE MANUAL CALL STATUS FOR KEYWORD
def __change_keyword_manual_call_status__(_id_, _status_):    # busy, done, fail
	_keywords_ = _kw__record_.objects.filter(__raw__= {'id': _id_})

	if _keywords_:
		if _status_ == "done":
			# A measured keyword clears its failure budget, or a transient 429
			# yesterday would count against the retries it gets tomorrow.
			_keywords_.update(
				manual_call_status=False, manual_call_mode=_status_, manual_task_allocation="-",
				call_fail_count=0, call_fail_reason="", call_retry_date=None,
			)
		else:
			_keywords_.update(manual_call_mode=_status_)
		return "success"
	else:
		return "failed"

# CHANGE KEYWORD CALL STATUS
def __change_keyword_call_status__(_id_, _status_, _grp_):    # avail, busy, done, fail
	if _grp_ == "group":
		_keywords_ = _kw__record_.objects.filter(fk_group_id = _id_)
	elif _id_ == "all":
		_keywords_ = _kw__record_.objects.all()
	elif _id_ > 0:
		_keywords_ = _kw__record_.objects.filter(__raw__= {'id': _id_})
	else:
		return "failed"

	if _keywords_:
		if _status_ == "done":
			# See above: success is what clears the attempt budget.  Failures
			# are never written through here -- __record_keyword_failure__ owns
			# that path, because it also has to decide about a retry.
			_keywords_.update(
				auto_call_status=_status_,
				call_fail_count=0, call_fail_reason="", call_retry_date=None,
			)
		else:
			_keywords_.update(auto_call_status=_status_)
		return "success"
	else:
		return "failed"

# CONVERT TO SERIALIZERS IN FUTURE - CHECK FOR LAST RANKED DATE
def __macro_problem__(_gid_, _mode_):
	_dt__today_ = _dt_.today()

	_gp__all__keywords_ =  _kw__record_.objects.filter(fk_group_id=_gid_)

	if _gp__all__keywords_.count(): 
		for _single__key_ in _gp__all__keywords_.all():
			_key__total__day_ = int((_dt__today_ - _single__key_.created_date.date()).days) + 1
			_key__rank__count_ = len(_single__key_.rank)

			if _key__rank__count_ > 0 and (_key__rank__count_ > _key__total__day_):
				_pop_ = 0 
				
				# RANK ARRAY OVERFLOW REDUCED
				while (_key__rank__count_ > _key__total__day_):
					_kw__record_.objects.filter(__raw__= {'id': _single__key_.id}).update(pop__rank=-1)
					_key__rank__count_-= 1 
					_pop_ += 1
				_wd_.coreLog(" > RANK ARRAY POP >> KEY_ID = "+str(_single__key_.id)+" >>> POP_COUNT = "+str(_pop_), _mode_) 
			else:
				if _key__rank__count_ > 0 and (_key__rank__count_ < _key__total__day_):
					_push_ = 0
				
					# RANK ARRAY INSUFFICIENCY ADDED 
					while (_key__rank__count_ < _key__total__day_):  
						_kw__record_.objects.filter(__raw__= {'id': _single__key_.id}).update(push__rank__0=_single__key_.rank[0]) 
						_key__rank__count_+= 1
						_push_ += 1	

					if _push_ > 1: 
						_wd_.coreLog(" > RANK ARRAY PUSH >> KEY_ID = "+str(_single__key_.id)+" >>> PUSH_COUNT = "+str(_push_), _mode_)   

		# START MACRO PROCESS FOR ALL CALCULATIONS HERE - STARTS
		_gp__source_ = _gp__record_.objects.filter(__raw__= {'id': _gid_})
		_gp__data_ = _gp__source_.first()

		if _gp__data_:
			currdate = _dt_.today() 
			groupAge = int((currdate - _gp__data_.created_date.date()).days) + 1

			# tracker SCORE METER 
			if len(_gp__data_.score_meter) < groupAge and len(_gp__data_.score_meter):
				groupDifference = groupAge - len(_gp__data_.score_meter)
				flag = 1
				while flag <= groupDifference:
					_gp__source_.update(
						push__score_meter__0=_gp__data_.score_meter[0], 
						updated_date=_date__time_.now() 
					)
					flag += 1 
				_wd_.coreLog(" > MACRO SCORE METER PUSH >> GROUP_ID = "+str(_gid_)+" >>> PUSH_COUNT = "+str(flag), _mode_)   

			# tracker ACTIVITY LEVEL
			if len(_gp__data_.activity_level) < groupAge and len(_gp__data_.activity_level):
				groupDifference = groupAge - len(_gp__data_.activity_level)
				flag = 1
				while flag <= groupDifference:
					_gp__source_.update(
						push__activity_level__0=_gp__data_.activity_level[0],  
						updated_date=_date__time_.now() 
					)
					flag += 1 
				_wd_.coreLog(" > MACRO ACTIVITY LEVEL PUSH >> GROUP_ID = "+str(_gid_)+" >>> PUSH_COUNT = "+str(flag), _mode_)

			# tracker SINCE START
			if len(_gp__data_.since_start) < groupAge and len(_gp__data_.since_start):
				groupDifference = groupAge - len(_gp__data_.since_start)
				flag = 1
				while flag <= groupDifference:
					_gp__source_.update(
						push__since_start__0=_gp__data_.since_start[0],  
						updated_date=_date__time_.now() 
					)
					flag += 1 
				_wd_.coreLog(" > MACRO SINCE START PUSH >> GROUP_ID = "+str(_gid_)+" >>> PUSH_COUNT = "+str(flag), _mode_)

			# tracker SINCE POSITION
			if len(_gp__data_.since_position) < groupAge and len(_gp__data_.since_position):
				groupDifference = groupAge - len(_gp__data_.since_position)
				flag = 1
				while flag <= groupDifference:
					_gp__source_.update(
						push__since_position__0=_gp__data_.since_position[0],
						updated_date=_date__time_.now() 
					)
					flag += 1 
				_wd_.coreLog(" > MACRO SINCE POSITION PUSH >> GROUP_ID = "+str(_gid_)+" >>> PUSH_COUNT = "+str(flag), _mode_)

			# tracker TOTAL KEYWORDS 
			if len(_gp__data_.total_Keyword) < groupAge and len(_gp__data_.total_Keyword): 
				groupDifference = groupAge - len(_gp__data_.total_Keyword)
				flag = 1
				while flag <= groupDifference:
					_gp__source_.update(
						push__total_Keyword__0=_gp__data_.total_Keyword[0],
						updated_date=_date__time_.now() 
					) 
					flag += 1 
				_wd_.coreLog(" > MACRO TOTAL KEYWORDS PUSH >> GROUP_ID = "+str(_gid_)+" >>> PUSH_COUNT = "+str(flag), _mode_)
		# START MACRO PROCESS FOR ALL CALCULATIONS HERE - ENDS
		
	return True			


# MODELS
def __ms_record__(_mode_, _process_):
	_setting__data_ = _ms__record_.objects.filter(__raw__= {'id': 1}).first() 

	if _mode_ == "ENGINE" and _process_ == "_mode__check_":
		return True if _setting__data_.core_mode == True else False
	elif _mode_ == "MANUAL" and _process_ == "_mode__check_":
		return True if _setting__data_.core_manual_mode == True else False
	elif _mode_ == "BRAND" and _process_ == "_mode__check_":
		return True if _setting__data_.core_mode == True else False
	elif _mode_ == "RESEARCH" and _process_ == "_mode__check_":
		return True if _setting__data_.core_kw_research_mode == True else False 
	else:
		return _setting__data_ 

# CONVERT TO SERIALIZERS IN FUTURE - CHECK FOR LAST RANKED DATE
def __zero_rank__(_gid_, _mode_): 
	_dt__today_ = _dt_.today()

	_gp__all__keywords_ =  _kw__record_.objects.filter(fk_group_id=_gid_)

	if _gp__all__keywords_.count(): 
		_wd_.coreLog(" > ZERO RANK CALCULATION CALL INITIATED >> GROUP_ID = "+str(_gid_), _mode_)
		for _single__key_ in _gp__all__keywords_.all():
			_key__total__day_ = int((_dt__today_ - _single__key_.created_date.date()).days) + 1
			_key__rank__count_ = len(_single__key_.rank)

			if _key__rank__count_ > 0 and (_key__rank__count_ > _key__total__day_):
				_pop_ = 0 
				
				# RANK ARRAY OVERFLOW REDUCED
				while (_key__rank__count_ > _key__total__day_):
					_kw__record_.objects.filter(__raw__= {'id': _single__key_.id}).update(pop__rank=-1)
					_key__rank__count_-= 1 
					_pop_ += 1
				_wd_.coreLog(" > ZERO RANK ARRAY POP >> KEY_ID = "+str(_single__key_.id)+" >>> POP_COUNT = "+str(_pop_), _mode_) 
			else:
				if _key__rank__count_ > 0 and (_key__rank__count_ < _key__total__day_):
					_push_ = 0
				
					# RANK ARRAY INSUFFICIENCY ADDED 
					while (_key__rank__count_ < _key__total__day_):  
						_kw__record_.objects.filter(__raw__= {'id': _single__key_.id}).update(push__rank__0=0)
						_key__rank__count_+= 1
						_push_ += 1	

					if _push_ > 1: 
						_wd_.coreLog(" > ZERO RANK ARRAY PUSH >> KEY_ID = "+str(_single__key_.id)+" >>> PUSH_COUNT = "+str(_push_), _mode_)   
			
			# UPDATE OTHER DETAILS 
			_kw__record_.objects.filter(__raw__= {'id': _single__key_.id}).update(
				ranknow=0,
				search_results="-",
				featured_snippet=False,
				review=False,
				knowledge_panel=False,
				ads=False,
				total_rating="-",
				total_review="-",
				snippets_details={},
				lastranked_date=_date__time_.now(),
				daymark = '-',
				dayval = 0,
				weekmark = '-',
				weekval = 0,
				monthmark = '-',
				monthval = 0, 
				halfmonthmark = '-',
				halfmonthval = 0, 
				status_from_start = "-", 
				keyword_alias="",
				cannibalisation=[], 
				cannibalisation_mail_status="-", 
				page_uuid="-",
				page_uuid_url="-",
				auto_call_status="done",
				manual_call_status=False,
				manual_call_mode="done",
				call_fail_count=0,
				call_fail_reason="",
				call_retry_date=None
			)
		# END OF FOR LOOP

		# GROUP UPDATE
		__change_group_call_status__(_gid_, "DROP")
		# DASHBOARD CALCULATION UPDATE
		_at__calculate_.dashboardZeroRankGraph(_mode_, _gid_)

		_wd_.coreLog(" > ZERO RANK CALCULATION CALL COMPLETED >> GROUP_ID = "+str(_gid_), _mode_)
	
	return True	

# CHECKING STATUS CALLBACK OF ACCOUNT USAGE
def __au_status_callback__(_g_record_):
	"""Is this project's account entitled to rank?  True / False / None.

	None means the question could not be answered, and it is a third answer on
	purpose.  This used to return False for "no" and for "the read raised", and
	the caller acts on False by dropping the project and switching its mail off
	-- so an account row the engine could not read was written down as an
	account that is not allowed to run.  That is the failure this returns None
	to prevent: it happened, it lasted, and nothing said so.

	The way it happened is worth keeping in view, because it will recur the
	next time the two halves of this codebase disagree about one collection.
	The backend added the BYOK columns to `accountusage`; the engine's
	mongoengine twin did not declare them; mongoengine refuses to load a
	document carrying a field its class does not know.  So `.first()` raised
	FieldDoesNotExist, this swallowed it, and every scheduled run marked every
	project of every key-holding account DROP without one provider request.
	Ranking looked switched off, and no error appeared anywhere.
	"""
	if not hasattr(_g_record_, 'fk_user_id'):
		return False
	if not _g_record_.fk_user_id or _g_record_.fk_user_id <= 0:
		return False

	try:
		_au__data_ = _au__record_.objects.filter(fb_user_id=_g_record_.fk_user_id).first()
	except Exception as e:
		_wd_.coreLog(
			" > ACCOUNT USAGE UNREADABLE >> USER_ID = "+str(_g_record_.fk_user_id)
			+" >>> "+str(type(e).__name__)+": "+str(e)[:200], "ENGINE"
		)
		return None

	if not _au__data_:
		return False
	if getattr(_au__data_, 'status', None) in ["default", "active"]:
		return True

	return False

# CHANGE COMP CALL STATUS FOR GROUP ON ANALYSE
def __change_group_competitor_call_status__(_id_, _status_):    # VOID, START, SCHD, COMP, FAIL, OVER
	_groups_ = _gp__record_.objects.filter(__raw__= {'id': _id_})      

	if _groups_:
		_groups_ = _groups_.update(competitor_analyse_status=_status_) 
		return "success"
	else:
		return "failed"

# CHANGE COMP CALL STATUS FOR KEYWORD ON ANALYSE
def __change_keyword_competitor_call_status__(_id_, _status_, _count_):    # - , COMP, GIER, GERR, FERR, FAIL
	_keywords_ = _kw__record_.objects.filter(__raw__= {'id': _id_})      

	if _keywords_:
		_keywords_.update(manual_task_allocation = _status_, manual_task_count=int(_count_))  
		return "success"
	else:
		return "failed" 

# CHANGE COMP PROJECT CALL STATUS ON MAIN GROUP
def __change_group_competitor_project_status__(_id_, _status_):    # VOID, START, SCHD, COMP, FAIL, OVER 
	_groups_ = _gp__record_.objects.filter(__raw__= {'id': _id_})      

	if _groups_:
		_groups_ = _groups_.update(competitor_project_status=_status_)
		return "success"
	else:
		return "failed"

# CHANGE COMPETITOR CALL STATUS FOR KEYWORD
def __change_competitor_keyword_call_status__(_id_, _status_):    # AVAIL, BUSY, DONE, FAIL 
	_keywords_ = _dC__keyword_.objects.filter(id=_id_) 

	if _keywords_:
		_cKeywords_ = _keywords_.first()
		if _cKeywords_.comp_call_mode == "busy" and _status_ in ["done", "fail"]:      
			_keywords_.update(comp_call_mode=_status_)
		elif _status_ in ["avail", "busy", "fail"]:
			_keywords_.update(comp_call_mode=_status_) 

		return "success"
	else:
		return "failed"

# REPLACE :// AND WWW.
def __c_remove__(x):
	return x.replace("://", "").replace("www.","")

# GET COMPETITOR DATA UNDER A GROUP AND PERFORM AS DICT.
def __get_competitor_list__(_gid_):
	_cProjectOfGroup_ = _dC__project_.objects.filter(fk_group_id=_gid_).values('id', 'cp_domain_name')
	_cProjectOfGroupDict_ = dict() 
	_cProjectDomains_ = list()

	if _cProjectOfGroup_:
		for _cProject_ in _cProjectOfGroup_:
			_extract__domain_ = str(extract_domain(_cProject_['cp_domain_name']))
			
			_cProjectDomains_ = _cProjectDomains_ + ["://"+_extract__domain_, "www."+_extract__domain_]

			_cProjectOfGroupDict_.update({
				_extract__domain_ : {
					'#' : _cProject_['id'], 
					'L' : [] 
				}
			})

	return _cProjectOfGroupDict_, _cProjectDomains_ 

def __get_competitor_list_update__(_key_, _value_, _dict_): 
	try:
		if _key_ in _dict_:
			_dict_.update({_key_: {
				"#": _dict_[_key_]["#"],
				"L": _dict_[_key_]["L"] + [int(_value_)] 
			}})
	except Exception as e:
		# print("list update > ", str(e))
		pass

	return _dict_
