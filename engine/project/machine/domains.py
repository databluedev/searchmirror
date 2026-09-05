from project.machine import automation_proxy as _at__proxy_
from project.machine.models import Group

from datetime import datetime, date

import os, requests, random, threading, whois

# Both lookups below run INSIDE a ranking run
# (automation_engine.__automation_concurrency_task__), and neither is bounded by
# anything it can be told.  whois.whois() has no timeout in its call path at all
# -- measured in this image, still blocking after 120 seconds because nothing
# here reaches port 43 -- and requests' (connect, read) timeouts do not cover
# name resolution, so a blackholed DNS blocks it past any figure it was given.
# An unanswered lookup therefore stops the engine draining every project queued
# behind this one, which is the failure the scheduler exists to prevent.  Both
# are best-effort enrichment, so both get a wall-clock bound and a skip.
_domain__lookup__timeout__seconds_ = int(os.environ.get("ENGINE_DOMAIN_LOOKUP_TIMEOUT_SECONDS", "10"))

def _bounded_lookup_(_label_, _domain_, _call_):
	"""Run one blocking lookup, or give up on it. Returns (answered, value).

	The call runs on a daemon thread that is abandoned rather than joined: a
	socket read blocked in C cannot be interrupted from outside, and a daemon
	thread does not hold up interpreter shutdown.  One abandoned thread per
	project per day is the price of not stalling the queue behind it.

	'answered' is returned separately so a caller can tell "we asked and the
	answer was no" from "we never got an answer" -- writing the second down as
	if it were the first is how a project ends up recorded as unreachable
	without a request ever leaving the box.
	"""
	_result_ = {}

	def _run_():
		try:
			_result_['value'] = _call_()
		except Exception:
			_result_['value'] = None

	_worker_ = threading.Thread(target=_run_, daemon=True)
	_worker_.start()
	_worker_.join(_domain__lookup__timeout__seconds_)

	if _worker_.is_alive():
		print("[DOMAIN] %s for %s did not answer within %ds -- skipped"
		      % (_label_, _domain_, _domain__lookup__timeout__seconds_))
		return False, None

	return True, _result_.get('value')

def _whois_lookup_(domainName):
	"""whois.whois(domainName), or None when it does not answer in time."""
	_answered_, _info_ = _bounded_lookup_("whois", domainName, lambda: whois.whois(domainName))
	return _info_ if _answered_ else None

def domainDetails(domainName):
	domainDetails = {}
	if domainName:
		try:
			whoInfo = _whois_lookup_(domainName)
			if whoInfo:

				#domain name get
				domainDetails['DN'] = None
				if 'domain_name' in whoInfo: 
					domainDetails['DN'] = whoInfo.domain_name[1] if type(whoInfo.domain_name) is list else whoInfo.domain_name
                
				#registrar name get
				domainDetails['RG'] = None
				if 'registrar' in whoInfo:
					domainDetails['RG'] = whoInfo.registrar
				elif 'tech_name' in whoInfo:
					domainDetails['RG'] = whoInfo.tech_name 

				#org name get
				domainDetails['OG'] = None
				if 'org' in whoInfo:
					domainDetails['OG'] = whoInfo.org
				elif 'organization' in whoInfo:
					domainDetails['OG'] = whoInfo.organization 
				elif 'registrant_name' in whoInfo:
					domainDetails['OG'] = whoInfo.registrant_name

				#state name get
				domainDetails['ST'] = None
				if 'state' in  whoInfo: 
					domainDetails['ST'] = whoInfo.state 
				elif 'registrant_state_province' in  whoInfo:
					domainDetails['ST'] = whoInfo.registrant_state_province 

				#city name get 
				domainDetails['CY'] = None
				if 'city' in  whoInfo: 
					domainDetails['CY'] = whoInfo.city[1] if type(whoInfo.city) is list else whoInfo.city 
				elif 'registrar_city' in  whoInfo:
					domainDetails['CY'] = whoInfo.registrar_city  

				#country name get
				domainDetails['CO'] = None
				if 'country' in  whoInfo: 
					domainDetails['CO'] = whoInfo.country
				elif 'registrar_country' in  whoInfo:
					domainDetails['CO'] = whoInfo.registrar_country
				elif 'registrant_country' in  whoInfo:
					domainDetails['CO'] = whoInfo.registrant_country

				#creation_date
				domainDetails['CD'] = None
				if 'creation_date' in  whoInfo:  
					cd = whoInfo.creation_date[1] if type(whoInfo.creation_date) is list else whoInfo.creation_date
					cdd = datetime.strptime(str(cd).replace("T", " ").split(".")[0].split("+")[0], '%Y-%m-%d %H:%M:%S')
					domainDetails['CD'] = cdd.strftime('%d-%m-%Y %I:%M %p')
    
				#updated_date
				domainDetails['UD'] = None
				if 'updated_date' in  whoInfo: 
					ud = whoInfo.updated_date[0] if type(whoInfo.updated_date) is list else whoInfo.updated_date
					udd = datetime.strptime(str(ud).replace("T", " ").split(".")[0].split("+")[0], '%Y-%m-%d %H:%M:%S')  
					domainDetails['UD'] = udd.strftime('%d-%m-%Y %I:%M %p')

				#expiration_date
				domainDetails['ED'] = None
				if 'expiration_date' in  whoInfo:  
					ed = whoInfo.expiration_date[1] if type(whoInfo.expiration_date) is list else whoInfo.expiration_date
					edd = datetime.strptime(str(ed).replace("T", " ").split(".")[0].split("+")[0], '%Y-%m-%d %H:%M:%S')
					domainDetails['ED'] = edd.strftime('%d-%m-%Y %I:%M %p')

		except Exception as e: 
			pass 	

	return domainDetails


def domainStatusCheck(websiteurl):
	""""ON" / "OFF" / "NOT", or None when the site could not be reached at all.

	None is not "NOT": the caller must not write down a verdict for a check that
	never completed.
	"""
	if not websiteurl:
		return None

	# Group.domain_name is a bare host ("example.com"), and requests rejects
	# that with MissingSchema -- a RequestException, so every project was
	# recorded "NOT" (unreachable) without a request ever leaving the box.
	_url_ = websiteurl if "://" in websiteurl else "https://" + websiteurl

	def _get_():
		try:
			x = requests.get(_url_, headers=_at__proxy_.__automation_desktop_headers__(), timeout=(5, 10))
			return "ON" if x.status_code in (200, 403) else "OFF"
		except requests.exceptions.RequestException:
			return "NOT"

	_answered_, _status_ = _bounded_lookup_("status check", _url_, _get_)
	return _status_ if _answered_ else None

def domainInitiate(grpData): 
	if grpData:
		s_00_Domain = {} 
		flag = "NO"

		gId = grpData.id 
		domainName = grpData.domain_name

		if bool(grpData.domain_info) == False:
			flag = "YES" 
		elif 'ED' not in grpData.domain_info:
			flag = "YES"
		elif 'ED' in grpData.domain_info:
			domainExpiryDate = grpData.domain_info['ED'] 
			if domainExpiryDate is None or domainExpiryDate == "":
				flag = "YES" 
			elif domainExpiryDate != "":
				domainExpiryDate = domainExpiryDate.split(" ")[0].strip() 
				domainExpiryDate = datetime.strptime(domainExpiryDate, "%d-%m-%Y")
				currentDate = datetime.strptime(str(date.today()), "%Y-%m-%d")

				if domainExpiryDate <= currentDate: 
					flag = "YES"

		if flag == "YES": 
			s_00_Domain = domainDetails(domainName)

		s_00_DomainStatus = domainStatusCheck(domainName)

		# A status of None means the check never completed.  Leave whatever was
		# last actually measured in place rather than overwriting it with a
		# verdict this run did not earn.
		s_00_Update = {}
		if bool(s_00_Domain) == True:
			s_00_Update['domain_info'] = s_00_Domain
		if s_00_DomainStatus is not None:
			s_00_Update['domain_status'] = s_00_DomainStatus

		if s_00_Update:
			Group.objects.filter(__raw__= {'id': int(gId)}).update(**s_00_Update)

	return True

