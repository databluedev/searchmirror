import os
from rest_framework.decorators import api_view
from serp.models import *
from serp.serializers import *
from serp import calculation, views as serp_views
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from django.conf import settings
from serp.common import *

from account import verify as authPermission


#Feedback  
@api_view(['POST','GET'])
def feedback(request):
	data = {} 
	if request.method == 'POST':
		serializer = FeedbackSerializer(data=request.data)
		if serializer.is_valid():
			fbcreate =  serializer.save()
			data['message'] =  "Feedback submitted successfully" 
			data['status'] =  "true"
			context = { 
				'userid': fbcreate.fb_user_id,
				'username': fbcreate.user_name,
				'message': fbcreate.message,
				'siteurl': settings.SITE_URL,
				'serivceurl': settings.SERVICE_URL,
			}
			subject = "Feedback Details For {username} - {userid} ".format(username = fbcreate.user_name.capitalize(), userid = fbcreate.fb_user_id)
			toMail = settings.ADMIN_MAIL
			# toMail = [m for m in os.environ.get("ALERT_MAIL", "").split(",") if m]
			mailDatas = sendMail('email/feedback.html', context, subject, toMail)
		else:
			data = serializer.errors
		return Response(data)
	elif request.method == 'GET':  
		data['message'] =  "Error occurred."
		data['status'] =  "false"
		return Response(data)
