from django.conf import settings


def validate(request, method):
	"""Confirm the caller is entitled to act for the 'userid' in the payload.

	The credential is resolved once per request and shared with the ownership
	middleware and DRF's authenticator -- see account/identity.py. What this
	function decides is unchanged: the caller may act for an account only if
	the credential it presented belongs to that account.
	"""
	returnToken = False
	if request and request.method == method:
		if request.method == "GET":
			uId = str(request.GET.get('userid')).strip()
		elif request.method == "POST":
			# .get(), not ['userid'] -- the GET branch above was already
			# defended and this one was not. A POST body with no userid raised
			# KeyError here, inside the guard every view calls FIRST, so the
			# request became an unhandled 500 with a Django debug page instead
			# of the "not authorised" this function exists to return. A request
			# that names no account cannot be entitled to one: fall through to
			# isdigit() and refuse it.
			uId = str(request.data.get('userid')).strip()
		else:
			return returnToken 
		
		if uId.isdigit():
			# The question here is unchanged: does the credential this request
			# presents belong to the account it names? It used to be answered
			# with a third `authtoken_token` read -- after the ownership
			# middleware's and DRF's -- at ~6ms each under djongo.
			#
			# The shared resolution answers it directly: whoever the credential
			# resolves to IS the account it belongs to. A missing header, an
			# unresolvable credential, or a mismatch all still return False, so
			# every caller refuses exactly what it refused before.
			from account.identity import caller_identity

			owner, _member = caller_identity(request)
			returnToken = owner is not None and int(owner) == int(uId)

	return returnToken
