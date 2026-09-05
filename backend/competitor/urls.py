from django.urls import path
from competitor import views
# from django.conf.urls import url , include
from competitor import compfiles as cF

urlpatterns = [

    # App Home
    path('startanalysis', views.start_analysis), 
    path('analysisstatus', views.analysis_status), 
    path('omptr_wdt', views.competitor_widget), 
    path('skipanalysis', views.skip_analysis), 
    path('competitorslist', views.competitors_list), 
    path('keywordgraph', views.competitor_keyword_graph), 
    path('addcompetitors', views.add_competitors), 
    path('deletecompetitor', views.delete_competitor), 
    path('competitoroverview', views.competitor_overview), 
    path('ranks', views.competitor_keyword_ranks),
    path('document', cF.comppage),
    path('projectstatus', views.competitor_project_status),
    path('keywordstatus', views.competitor_keyword_status),
    path('updategrpname', views.competitor_group_update),
    
]  
