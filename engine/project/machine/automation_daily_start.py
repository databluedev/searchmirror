from django.shortcuts import render
from django.conf import settings as _def_

from project.machine.serializers import GroupTimeSerializer as _gp__time__collect_, ClientTrackerSerializer as _ct__time__allocate_
from project.machine.models import Keyword as _kw__record_, Mainsettings as _ms__record_, Accountusage as _au__record_
from project.machine.models import ClientTracker as _ct__record_

from project.machine.submodels.serpmodels import DKeyword as _d__keyword_, DGroups as _d__group_, DCompProject as _dC__project_, DCompKeyword as _dC__keyword_
from project.machine.submodels.serpmodels import DAccountUsage as _dA__usage_

from datetime import datetime as _date__time_, date as _dt_

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse 

from project.machine import watchdog as _wd_, automation_common as _at__common_ 

def __daily_order_groups_by_pay_status__(): 
	_wd_.coreLog(" > INTIATED THE PAY STATUS IN PROJECTS", "ENGINE") 

	# FILTER ACCOUNT USAGE TABLE - STRIPE WITH ACTIVE AND UPDATE PAYMENTMODE AS "A".  # "A" MEANS ACTIVE
	_gateway__uid_ = _dA__usage_.objects.filter(status="active", user_type="stripe").values_list("fb_user_id", flat=True)
	if _gateway__uid_:
		_d__group_.objects.filter(fk_user_id__in=list(_gateway__uid_)).update(paymentmode="A")

	# FILTER ACCOUNT USAGE TABLE - UPDATE PAYMENTMODE AS "B" FOR ANY IMPORTANT PROJECTS IN NEED.  # "B" MEANS TEMPORARILY ACTIVE
	_interim__uid_ = _dA__usage_.objects.filter(status="active").exclude(user_type__in=["stripe", "redeem"]).values_list("fb_user_id", flat=True)
	if _interim__uid_:
		_d__group_.objects.filter(fk_user_id__in=list(_interim__uid_)).update(paymentmode="B")

	# FILTER ACCOUNT USAGE TABLE - REDEEM WITH ACTIVE AND UPDATE PAYMENTMODE AS "C".  # "C" MEANS COUPON
	_deal__uid_ = _dA__usage_.objects.filter(status="active", user_type="redeem").values_list("fb_user_id", flat=True)
	if _deal__uid_:
		_d__group_.objects.filter(fk_user_id__in=list(_deal__uid_)).update(paymentmode="C")

	# FILTER ACCOUNT USAGE TABLE - FOR DEFAULT IN  USER STATUS UPDATE THE PAYMENTMODE AS "D".  # "D" MEANS DEFAULT
	_nominal__uid_ = _dA__usage_.objects.filter(status="default").values_list("fb_user_id", flat=True)
	if _nominal__uid_:
		_d__group_.objects.filter(fk_user_id__in=list(_nominal__uid_)).update(paymentmode="D")

	# FILTER ACCOUNT USAGE TABLE - FOR CANCEL, CLOSE AND EXPIRE IN USER STATUS UPDATE THE PAYMENTMODE AS "F".   # "F" MEANS FAILED
	_negate__uid_ = _dA__usage_.objects.filter(status__in=["close", "cancel", "expire"]).values_list("fb_user_id", flat=True)
	if _negate__uid_:
		_d__group_.objects.filter(fk_user_id__in=list(_negate__uid_)).update(paymentmode="F") 

	# FILTER ACCOUNT USAGE TABLE - ACCOUNT IN THE ABOVE CRITERIA IN USER STATUS UPDATE THE PAYMENTMODE AS "E".   # "E" MEANS "EXTRA"
	_xtra__uid_ = _d__group_.objects.exclude(paymentmode__in=["A", "B", "C", "D", "F"]).count()
	if _xtra__uid_:
		_d__group_.objects.exclude(paymentmode__in=["A", "B", "C", "D", "F"]).update(paymentmode="E") 

	# DEMO ACCOUNT
	_d__group_.objects.filter(fk_user_id=1).update(paymentmode="1")  

	_wd_.coreLog(" > COMPLETED THE PAY STATUS IN PROJECTS", "ENGINE")

	return True 

# FIRST INITIATOR CALL ON EVERY 12.01 A.M
@api_view(['GET'])
def daily_automation_first_call(request, _ustr_): 

	_base__result_, _setting__data_  = _at__common_.__base_validation__(request, _ustr_)  

	if _base__result_ and len(_setting__data_) >= int('0b1010', 2):
		_curr__date_ = _dt_.today()
				
		if _setting__data_.core_refresh_time.date() < _curr__date_: 
			_wd_.coreLog("LINE", "ENGINE")

			# UPDATE PAYMENT STATUS FOR ALL PROJECTS - USED TO SORT EVERY PROJECTS IN EACH TIMEZONE BASED ON PRIORITY OF PAYMENT.
			__daily_order_groups_by_pay_status__()

			_kw__record_.objects.update(
				auto_refresh_count=0,
				strict_refresh_count=0
			)
			_wd_.coreLog(" > KEYWORD USAGE LIMIT RESET COMPLETED", "ENGINE")

			_ms__record_.objects.update( 
				push__daily_automation_count__0=0,
				push__daily_demand_count__0=0, 
				core_manual_mail=True,
				core_mode=True,
				core_kw_research_mode=True,
				core_manual_mode=True, 
				proxy_success_count=0,
				proxy_exceeds_count=0,
				proxy_invalid_count=0,
				proxy_reset_counter=0,
				modified_date=_date__time_.now(), 
				core_refresh_time=_date__time_.now(),
				automation_keyword_exceeds_mail_status="-", 
				manual_keyword_exceeds_mail_status="-"
			) 
			_wd_.coreLog(" > SETTINGS USAGE RESET UPDATED", "ENGINE")
			
			if _curr__date_.day == 1:
				_au__record_.objects.update(
					automatic_mail_status="VOID", 
					used_refresh_limit=0,
					redeem_api_call_count=0,
					used_kw_research_limit=0,
					used_per_day_kw_research_limit=0,
					modified_date=_date__time_.now()
				)
			else:
				_au__record_.objects.update(
					automatic_mail_status="VOID",
					redeem_api_call_count=0,
					used_per_day_kw_research_limit=0,
					modified_date=_date__time_.now()
				) 

			_wd_.coreLog(" > ACCOUNT USAGE RESET COMPLETED", "ENGINE") 

			# Daystart resets; it does not queue.
			#
			# This used to set group_call_status="INIT" on every project of
			# every tenant, which queued the whole instance at midnight -- one
			# engine call afterwards drains every INIT project in a single
			# loop, so the reset was itself the stampede the scheduler exists
			# to prevent, and it spent money as a side effect of housekeeping.
			# Deciding what runs and when belongs to exactly one component,
			# and that component is the scheduler.
			#
			# Recovery is not queueing and is unaffected: a project whose run
			# died is returned to INIT by __sweep_stale_group_claims__, which
			# hands back work that was already queued.

			# A new day is a fresh attempt budget as well as a fresh status.
			# Leaving call_fail_count behind would carry yesterday's failures
			# forward, so a keyword that failed its cap yesterday would go
			# terminal on its first failure today and never be retried again.
			_kw__record_.objects.update (
				auto_call_status="avail",
				call_claim_date=None,
				call_fail_count=0,
				call_fail_reason="",
				call_retry_date=None
			)

			# PROJECT TIMEZONE AUTOMATION TIME RE-CALCUATION.
			_ct__time__allocate_(_ct__record_.objects.all(), many=True, context={'type': 'ALL'}).data
			
			_wd_.coreLog(" > GROUP USAGE RESET UPDATED", "ENGINE")
			
			return JsonResponse({'status': "Neural engine daily process has updated for today schedule"}) 
		else:
			return JsonResponse({'status': "Neural engine error on daily request call"}) 
	else:
		# Needed Watch Dog Message 
		return JsonResponse({'status': 'Neural engine autorization error'})
