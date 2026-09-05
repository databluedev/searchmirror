from django.urls import path
from llmtracker import views

urlpatterns = [
    path("add", views.add_prompt),
    path("list", views.list_prompts),
    path("delete", views.delete_prompts),
    path("manage", views.manage_prompts),
    path("trigger-processing", views.trigger_auto_processing),
    path("processing-status", views.get_processing_status),
    path("citations", views.list_citations),
    path("trend", views.geo_trend),
    path("share-of-voice", views.geo_share_of_voice),
    path("competitors", views.geo_competitors),
    path("competitors/manage", views.geo_competitor_manage),
    path("competitors/detect", views.geo_detect_competitors),
    path("generate-prompts", views.generate_prompts),
]
