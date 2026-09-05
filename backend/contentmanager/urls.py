from django.urls import path
from contentmanager import views

urlpatterns = [
    path("create", views.create_content),
    path("list", views.list_content),
    path("details", views.plan_details),
    path("delete", views.delete_content),
    path("update", views.update_content),
    path("generate", views.generate_ai_content),
    path("generate/status", views.generate_ai_status),
]
