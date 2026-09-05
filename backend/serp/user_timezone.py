from django.shortcuts import render
from django.conf import settings
from serp.models import *

from datetime import date,datetime,timedelta,time 
from pytz import timezone, all_timezones
from dateutil.relativedelta import relativedelta

mainTimeZone = "Asia/Kolkata"
userAutomationExecuteTime = 7

def systemTimeZone():
	global mainTimeZone	
	timeZone = mainTimeZone

	try:
		if hasattr(settings, 'TIME_ZONE'):
			timeZone = checkTimeZone(settings.TIME_ZONE)
	except:
		pass

	return timeZone if timeZone != None else mainTimeZone 

def checkTimeZone(default_timezone):
	defaultTimeZone = None

	if default_timezone in all_timezones:
		defaultTimeZone = default_timezone
	else:
		for tz in all_timezones:
			if tz.lower() == default_timezone.lower():
				defaultTimeZone = tz
				break

	return defaultTimeZone

def timeZoneTracker(user_TZ):
	global userAutomationExecuteTime

	dateToday = date.today() 
	executeTime = time(hour=userAutomationExecuteTime, minute=0)
	serverAutomationGroupTime = datetime.combine(dateToday, executeTime)

	server_TZ = systemTimeZone()
	# server_TZ = 'Asia/Kolkata'
	hrs, mins = None, None

	if user_TZ:
		utcNow = timezone('utc').localize(datetime.utcnow())
		here = utcNow.astimezone(timezone(server_TZ)).replace(tzinfo=None)
		there = utcNow.astimezone(timezone(user_TZ)).replace(tzinfo=None)

		offset = relativedelta(there, here)

		if hasattr(offset, 'hours'):
			hrs = int(offset.hours)
		if hasattr(offset, 'minutes'):
			mins = int(offset.minutes)

	scheduleTime = None 
    
	if (hrs != None or mins != None) and isinstance(hrs, int) and isinstance(mins, int): 
		if hrs > 0 and mins >= 0:
			hrs = 6 if hrs >=6 else hrs
			scheduleTime = serverAutomationGroupTime - timedelta(hours=abs(hrs), minutes=abs(mins))
		elif hrs < 0 and mins <= 0:
			hrs = -13 if hrs <-13 else hrs
			scheduleTime = serverAutomationGroupTime + timedelta(hours=abs(hrs), minutes=abs(mins))
		elif hrs == 0:
			scheduleTime = serverAutomationGroupTime

	return scheduleTime

def TimeZoneUpdate(userId, timezone): 
	timeZoneData = timeZoneTracker(timezone)
	if timeZoneData:
		clientTracker.objects.filter(fb_user_id=userId).update(user_automation_time = timeZoneData)
		Groups.objects.filter(fk_user_id=userId).update(project_automation_time = timeZoneData)

def existingUserTracker():
	trackerStartData = clientTracker.objects.all()

	for trackerData in trackerStartData:
		if hasattr(trackerData, 'time_zone'): 
			TimeZoneUpdate(trackerData.fb_user_id, trackerData.time_zone) 

	return True