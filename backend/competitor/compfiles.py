from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.decorators import api_view, permission_classes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from django.template import RequestContext 
from datetime import date,datetime,timedelta
from django.conf import settings

from rest_framework.permissions import AllowAny
from serp.models import Keyword, Groups, Settings as MainSettings
import hmac
import json, os
import logging

logger = logging.getLogger(__name__)

_server__ip_ = "127.0.0.1"

def __ip_validation__(request):
	_if__remote__addr_ = str(request.META.get('REMOTE_ADDR'))
	return True if _if__remote__addr_ == _server__ip_ else False

@api_view(['POST'])
@permission_classes([AllowAny])
def comppage(request):
	# Engine -> backend: the ranking engine POSTs the competitor domain map here
	# after analysis, so the backend's pages can read it (the two run as separate
	# services with separate disks). AllowAny because the engine holds no user
	# session; the shared ENGINE_TRIGGER_TOKEN -- the same secret the backend uses
	# to drive the engine -- gates it instead, constant-time compared. Fails
	# closed: with the token unset there is no trusted caller.
	expected = os.environ.get("ENGINE_TRIGGER_TOKEN", "")
	supplied = request.META.get("HTTP_X_ENGINE_TOKEN", "")
	if not expected or not supplied or not hmac.compare_digest(str(supplied), str(expected)):
		return JsonResponse({'status': 'error', 'message': 'Not authorised.'}, status=403)
	if True:
		if request.method == 'POST':
			compData = request.POST['data']
			try:
				checkListKeys = ('gid', 'domains', 'keys')
				compJsonData = json.loads(compData)

				if all(keys in compJsonData for keys in checkListKeys):
					group_id = compJsonData['gid']
					comp_domains = json.dumps(compJsonData['domains'])
					comp_keys = json.dumps(compJsonData['keys'])

					search_domains_file = os.getcwd()+"/competitor/ai_files/domains/aiGroup__"+str(group_id)+".json"
					search_keys_file = os.getcwd()+"/competitor/ai_files/keys/aiKeys__"+str(group_id)+".json"

					# open('w') does not create missing parents. These directories
					# ship in no image and no volume, so without this the write raised,
					# the bare except swallowed it, and the competitor list was silently
					# lost -- the analysis counted domains but the page showed "no
					# matches". Create the tree before writing.
					os.makedirs(os.path.dirname(search_domains_file), exist_ok=True)
					os.makedirs(os.path.dirname(search_keys_file), exist_ok=True)

					with open(search_domains_file, 'w') as f:
						f.write(str(comp_domains))

					with open(search_keys_file, 'w') as f:
						f.write(str(comp_keys))

			except Exception as e:
				# A persist failure used to vanish here; at least record it so the
				# next "no matches" is diagnosable.
				logger.error("comppage failed to persist competitor files: %s", e)

			return JsonResponse({'status':'ok'}) 
		
	return JsonResponse({'status':'error'}) 
	