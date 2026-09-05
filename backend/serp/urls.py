from django.urls import path
from serp import project, white_label, views, project_management, referral, report, feedback, register_token, keyword, graph, automated_crons, widget, brand_acq, common, notes, ga_weekly_result
from serp import rank_scheduler
from serp import dashboard_overview, site_icon
from serp import ga_weekly_result as GAWklyRslt, ga_monthly_result as GAMnlyRslt, ga_daily_result as GADlyRslt
from django.conf.urls import url, include

# GENERAL AGENCY REPORT URLS
from serp.custom_report import rp_keywords as rpKW
from serp.custom_report import rp_google_analytics as rpGA

# NON-ECOM REPORT URLS
from serp.custom_report.non_ecom import rp_custom_report as rpCR
from serp.custom_report.non_ecom import ga_overview_last_year as gaLastYearOv
from serp.custom_report.non_ecom import ga_overview_last_year_monthly as gaLastYearOvMon 

# ECOM REPORT URLS
from serp.custom_report.ecom import rp_custom_e_com_report as RceR

# CLIENT SETTINGS

# TEAM SETTINGS
from serp.team import team_settings as tms

# ROLES
from serp.roles import *

# TESTING REFERANCE 
# from serp.custom_report.ecom import rp_ecom_analytics as RePA

urlpatterns = [

    # ROLES
    # path('redis_demo', views.redis_demo),
    path('my_view/', MyView.as_view(), name='my_view'),
    path('rl_delete', role_delete),

    # CLIENT MANAGEMENT
    # ------- *** no needed *** --------
    # ------- *** no needed *** --------

    # TEAM MANAGEMENT
    # path('retre_team', TeamView.as_view()),
    path('get_team', tms.get_team),
    path('del_team', tms.delete_team),
    path('mng_tm_prjcts', tms.manage_projects),
    path('teams', tms.TeamView.as_view(), name='teams'),
    path('team_mng', tms.TeamEdit.as_view(), name="team_manage"),

    # GOOGLE ANALYTICS
    path("ga_crawler", rpGA.rp_google_analytics_connect),
    path("ga_week_crawler", rpGA.rp_google_weekly_connect),
    path("ga_month_crawler", rpGA.rp_google_monthly_connect),
    path("ga_weekly_last_year_crawler", gaLastYearOv.last_year_overview_data_weekly),
    path("ga_monthly_last_year_crawler", gaLastYearOvMon.last_year_overview_data_monthly),
    
    # CUSTOM REPORT - MANAGE
    path("kX3JlYWF9nYV9tZRcXRyaWG9ydNz", rpCR.add_report_ga_metrics),  # ADD EXPORT REPORT - GA METRICS
    path("dF9kb21YG9yhaW5cWV0cmljfbWRkX3Jlcw", rpCR.add_report_domain_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("dF9rZYWRkXb21ldH3JlcG9y3JkXXl3JY3Mp", rpCR.add_report_keyword_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("G9ydFcWRkV0cml9n2YjX3JlcNfbWcw", rpCR.add_report_gsc_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("overview_sheet", rpCR.add_summary),
    # CUSTOM REPORT
    
    # E-COM REPORT
    path("e-ga_sheet", RceR.e_add_report_ga_metrics),  # ADD EXPORT REPORT - GA METRICS
    path("e-domain_sheet", RceR.e_add_report_domain_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("e-keyword_sheet", RceR.e_add_report_keyword_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("e-gsc_sheet", RceR.e_add_report_gsc_metrics),  # ADD EXPORT REPORT - DOMAIN METRICS
    path("e-overview_sheet", RceR.e_add_summary),
    # E-COM REPORT
    
    path("cmVmluZwb3J0RfcX2tl3aWRneXdvcFua2m19ZXQ", rpKW.rp_keywords_widget),  # Report Keyword Ranking Widget
    
    # SPACE API
    path("_spaceApi_", views._spaceApi_),
    path("updtWl", views._updtWl_),
    path("RP_wlSui0dGlZWxfcd2hpd2GVfbGFVZ3M", white_label._whtLblCheck_),
    path("whiteLabelSettings", white_label._whtLblSttgs_),
    # ADD PROJECT PAGE
    path("AP_d2V20ic2ZJnV5d2V90YX9ylZXRfaZHM", project._website_target_keywords_),
    # Testing
    # cron Trial Expire Update
    path("trial-expire", automated_crons.user_trial_expiry),
    # cron currency Update
    path("currency-update", automated_crons.currency_convert),
    # Widget
    path("dnert_wdt", widget.trending_widget),
    path("aived_wdt", widget.deviating_widget),
    path("erocs_wdt", widget.score_widget),
    path("airav_wdt", widget.today_widget),
    path("ecnis_wdt", widget.top_widget),
    path("eldnah_wdt", widget.manage_widget),
    path("Y25iX3dkdA", widget.cannib_widget),  # cannibalisation widget
    path("JkcaW1RrZXl3b3wcm92ZW193aWRnZXQ", widget.improvedkwds_widget),  # improvedkeywords_widget
    path("jbGluZWZG3Jkc19VRrZXl3b3aWRnZXQ", widget.declinedkwds_widget),  # declinedkeywords_widget
    path("is_enable", widget.check_ga_gsc),
    # GSC
    path("d2Vla2x5X3NlYXJjaF9xdWVyeV93aWRnZXQ", widget.weekly_search_query_widget),
    path("d2Vla2x5X3NlYXJjaF9wYWdlc193aWRnZXQ", widget.weekly_search_page_widget),
    path("bW9udGhseV9zZWFyY2hfcXVlcnlfd2lkZ2V0", widget.monthly_search_query_widget),
    path("bW9udGhseV9zZWFyY2hfcGFnZV93aWRnZXQ", widget.monthly_search_page_widget),
    path("Z3NjX2V4cG9ydA", widget.gsc_export),
    path("csv_monitor", widget.CSV_monitor),
    path("csv_report_mailer", widget.csv_report_mailer),
    # GA
    path("ga_lndg_pg_wdgt", widget.ga_landing_page_widget),
    path("check_report", widget.checkReport),
    path("gen_report", widget.gen_report),
    path("local_report_export", widget.local_report_export),
    # project settings
    path("project_overview_change", project_management.prjtoverview_change),
    path("projectoverview", project_management.prjtoverview),
    path("projectsetting", project_management.projectdetails),
    path("prjctserpmode", project_management.project_serp_mode),
    path("rpntmailupdate", project_management.recipientmailupdate),
    path("mailoptswupdate", project_management.mailoptionswupdate),
    path("brndadupdate", project_management.brandadcreate),
    path("brndadswupdate", project_management.brandadswupdate),
    path("brndaddelete", project_management.brandaddelete),
    # Referral programs
    path("referraldatacreate", referral.referraldatacreate),
    path("refvisitorscountadd", referral.refvisitorscountadd),
    path("refregadd", referral.refregadd),
    path("refreshclaim", referral.refreshclaim),
    path("refwebsiteverfication", referral.refwebsiteverfication),
    path("emailinvite", referral.emailinvite),
    # Report
    path("smrdata", report.smrdata),
    path("report_schedule_add", report.report_schedule_add),
    path("reportsentnow", report.report_email_sent_now),
    path("report_schedule_emails", report.report_schedule_emails),
    path("report_schedule_delete", report.report_schedule_delete),
    # Feedback
    path("feed_back", feedback.feedback),
    # Token
    path("user_reg_token", register_token.user_reg_token),
    path("user_regtoken_verify", register_token.user_regtoken_verify),
    # Keyword
    path("addkeyv3", keyword.addkeyv3),
    path("addnewkey", keyword.addfreshkey),
    path("connectgsc", keyword.connect_gsc),
    path("gsctoken", keyword.gsc_token),
    path("project_branded_keywords", keyword.project_branded_keywords),
    # graph
    path("kw_gph", graph.keywordgraph),
    path("analysismeter", graph.scoremeter),
    path("activitymeter", graph.activitylevel),
    path("sincemeter", graph.sincestartlevel),
    # Keyword page
    path("keyauth", keyword.keyload),
    path("kwads", keyword.kwads),
    path("kwcomps", keyword.kwcmptrs),
    path("kwsvolume", keyword.kwsvolume),
    path("kwnotes", keyword.kwnts),
    path("kwnotecreate", keyword.kwnt_create),
    path("kwnoteupdate", keyword.kwnt_update),
    path("kwnotedelete", keyword.kwnt_delete),
    # Per-keyword tracking configuration. The read rides on /keyauth; these two
    # are the writes -- one keyword, and the project-wide clear of overrides.
    path("kwconfigsave", keyword.kwconfig_save),
    path("kwconfigreset", keyword.kwconfig_reset),
    # Pages per check, so the add form can price a multi-country add up front.
    path("kwaddcost", keyword.kwaddcost),
    # App Home
    path("baseauth", views.apphomeload),
    path("usageauth", views.usageload),
    path("homeauth", views.homeload),
    path("gridauth", views.gridload),
    path("projectrefreshstatus", views.project_refresh_status),
    # ManageTag
    path("getlabels", views.getlabels),
    path("update_tags", views.update_tags),
    path("updatetag", views.updatetag_singlekw),
    path("remove_tag", views.remove_tag),
    path("updategroupservice", views.updategrpservice),
    path("deletegroupservice", views.deletegrpservice),
    path("dashservice", views.getdashboard),
    path("tablecolumsupdate", views.tblHeaderUpdate),
    # path('mail_notifications', views.mailntfictn),
    path("gresultpage", views.gresultpage),
    path("getsetting", views.getsetting),
    path("redirectcheck", views.validatecheck),
    path("usercrawl", views.usercrawl),
    path("menu_details", views.menu_details),
    path("multidelete", views.multidelete),
    path("export", views.export),
    path("refreshstatus", views.refreshstatus),
    path("keyaddfetchstatus", views.keyaddfetchstatus),
    path("typoerrorfix", views.typoerrorfix),
    path("pdfexport", views.pdfexport),
    path("new_user_create", views.new_user_create),
    path("account_settings", views.acc_settings),
    path("profile_settings", views.user_settings),
    path("country_list", views.countries),
    path("skip_create", views.skip_create),
    path("skip_off", views.skip_off),
    path("username_update", views.username_update),
    path("dashboard_view_change", views.dashboard_view_change),
    path("domain_valid_check", views.domain_valid_check),
    path("last_logout", views.last_logout),
    # Brand Acquisition
    path("cmQkX2JyeXdYW5kX2tlvcmQYWR", brand_acq.add__brand__key),  # add_brand_keyword
    path("ZHNbmRfa2V5d29yfbGlzdYnJhA", brand_acq.brand__list__key),  # brand_keywords_list
    path("xpc3QcmVnaW9uX2xhWdlX2bmd1Y", brand_acq.rl__list__key),  # region_language_list
    path("kX2tleXdZGVslX2JyYW5vZXRcmQ", brand_acq.delete__brand__key),  # delete_brand_keyword
    path("fa2V5d2Y291hbmR9yZAbnRfYnJ", brand_acq.comp__key__count),  # count_brand_keyword
    # NOTES
    path("dm90ZlldhbGx19fbmXM", notes.view_all_notes),  # view all keyword notes
    path("ub3RlZGVsNplX39bmdsZVZXRub3Rl", notes.delete_note),  # delete single keyword note
    # path('search_console', google_search_console.extract_data),
    # Live Report
    path("connectga", keyword.connect_ga),
    path("ga_connect", keyword.ga_connection),
    path("ga_weekly_monitor", GAWklyRslt.ga_weekly_monitor),
    path("ga_weekly_rescheduler", GAWklyRslt.ga_weekly_rescheduler),
    path("ga_monthly_monitor", GAMnlyRslt.ga_monthly_monitor),
    path("ga_monthly_rescheduler", GAMnlyRslt.ga_monthly_rescheduler),
    path("ga_daily_monitor", GADlyRslt.ga_daily_monitor),
    path("ga_daily_scheduler", GADlyRslt.ga_daily_scheduler),
    path("dynamic_widget", widget.generate_report),
    path("rpt_dlte", widget.reportDelete),
    path('sheet_update', widget.rnme_sht),
    path('reset_track_day', keyword.Reset_track_day),
    # path('streaming_view', widget.streaming_view),
    # path('stream', widget.stream),
    path('change_platform', widget.change_platform),
    path('reset_platform', keyword.reset_platform),

    # Dashboard: the whole action-first screen in one call, replacing the eight
    # widget requests that each re-queried the same keyword rows.
    path('dashboard_overview', dashboard_overview.dashboard_overview),

    # Favicon proxy. The server fetches and caches, so the browser never talks
    # to a competitor's domain -- see serp/site_icon.py for the SSRF guards.
    path('site-icon', site_icon.site_icon),

    # Daily rank scheduling. Token-gated (CRON_TOKEN), not a browser route:
    # nothing in the app links here and an anonymous caller would spend
    # every account's provider credits. Call it every 15 minutes from cron.
    path('rank/schedule', rank_scheduler.rank_schedule),
]
