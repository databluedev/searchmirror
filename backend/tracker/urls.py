"""SearchMirror URL configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from glassend import watchmail as coreViews
from django.conf.urls import url, include

urlpatterns = [
    path("", include("serp.urls")),
    path("mailsystem/", include("mailend.urls")),
    path("api/account/", include("account.api.urls", "account_api")),
    path("reset/", include("account.authorization.urls")),
    path("compai/", include("competitor.urls")),
    # Others
    path("spyglass/notify", coreViews.mailpage),
    path("spyglass/watchmail", coreViews.instantMailAlert),
    path("contentmanager/", include("contentmanager.urls")),
    path("llmtracker/", include("llmtracker.urls")),
]

handler401 = "glassend.views.handler404"
handler404 = "glassend.views.handler404"
handler405 = "glassend.views.handler404"
handler500 = "glassend.views.handler500"

# Full cross-tenant model access, so it is not routed unless the operator asks.
# See ENABLE_DJANGO_ADMIN in settings.py -- on under DEBUG, off otherwise.
if settings.ENABLE_DJANGO_ADMIN:
    urlpatterns.insert(0, path("serministrator/", admin.site.urls))

admin.site.site_header = "SearchMirror Admin"
admin.site.site_title = "SearchMirror Admin"
admin.site.index_title = "SearchMirror administration"
admin.site.site_url = settings.SITE_URL

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
