from rest_framework_mongoengine import serializers
from project.machine.models import Group as _gp__record_, ClientTracker as _ct__record_
from datetime import datetime, date as _dt_

class GroupTimeSerializer(serializers.DocumentSerializer):

	class Meta:
		model = _gp__record_
		fields = ('id', 'project_automation_time', 'group_call_status', 'paymentmode')

	def to_representation(_ox_, _o_):
		# Recalculates today's run time. It does NOT queue the project: writing
		# group_call_status="INIT" here queued every project it touched, and
		# deciding what runs belongs to the scheduler alone.
		_dt__today_ = _dt_.today()
		if _o_.project_automation_time != None and isinstance(_o_.project_automation_time, datetime):
			_dt__join_ = datetime.combine(_dt__today_, _o_.project_automation_time.time())
			_gp__record_.objects.filter(__raw__= {'id': _o_.id}).update(project_automation_time=_dt__join_)

		return True


class ClientTrackerSerializer(serializers.DocumentSerializer):
	class Meta:
		model = _ct__record_
		fields = ('id', 'fb_user_id', 'user_automation_time')

	def to_representation(_ox_, _o_):
		# One behaviour for both callers: recalculate today's run time for this
		# tenant's projects. The two context types used to differ only in that
		# "ALL" ALSO queued every one of those projects by writing
		# group_call_status="INIT" -- which is how the daily reset queued the
		# whole instance at midnight. Queueing is the scheduler's job, and with
		# it gone the two branches were the same code twice.
		if _ox_.context.get("type") in ("ALL", "PAT"):
			if _o_.user_automation_time != None and isinstance(_o_.user_automation_time, datetime):
				_dt__today_ = _dt_.today()
				_dt__join_ = datetime.combine(_dt__today_, _o_.user_automation_time.time())
				_gp__record_.objects.filter(fk_user_id=_o_.fb_user_id).update(project_automation_time=_dt__join_)

		return True