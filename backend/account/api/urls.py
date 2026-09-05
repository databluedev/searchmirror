from django.conf.urls import url
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib import admin
from account.api import views
from account.api.views import(
	registration_view,
	login,
	Glogin,
    ChangePasswordView,
    serviceauthenticate,
    SerpKeyView,
    AiKeysView,
    CapabilitiesView,
)

app_name = 'account'

urlpatterns = [
	url(r'^register/$', registration_view, name='register'),
	url(r'^login/$', login, name='login'),
	url(r'^serviceauthenticate/$', serviceauthenticate, name='serviceauthenticate'),
	url(r'^Glogin/$', Glogin, name='Glogin'),
	url(r'^token/$', obtain_auth_token, name='token'),
    url(r'^changepassword/$', views.ChangePasswordView.as_view(), name='update'),
    url(r'^serp-key/$', SerpKeyView.as_view(), name='serp-key'),
    url(r'^ai-keys/$', AiKeysView.as_view(), name='ai-keys'),
    url(r'^capabilities/$', CapabilitiesView.as_view(), name='capabilities'),
]


