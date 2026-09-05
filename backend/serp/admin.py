from django.contrib import admin
from .models import SiteKeywords, Keyword, Groups as project, Accountusage, keywordVolume, Report, Settings, Userregistrationtoken 
#from .models import brandTracker, Feedback 
from django.contrib.auth.models import Group
from datetime import datetime, date 
from account.models import Account
from competitor.models import CompProject, CompKeyword
from django.utils.html import format_html

# Register your models here.

# class FeedbackAdmin(admin.ModelAdmin):
#     list_display = ('id', 'fb_user_id', 'user_name','message','created_date')
#     readonly_fields=('id', 'fb_user_id', 'user_name','message','created_date')
#     list_filter = ("user_name","created_date")
#     list_per_page = 10
#     actions = None
#     list_display_links = None    
#     def has_add_permission(self, request):
#         return False
#     def has_change_permission(self, request):
#         return False
    
#     # search_fields = ['title', 'content']
#     # prepopulated_fields = {'slug': ('title',)}
  
# admin.site.register(Feedback, FeedbackAdmin)


class SiteKeywordSuggestionAdmin(admin.ModelAdmin):
    list_display=('id','domain','created_date','get_keyword_list') 
    readonly_fields=('domain', 'created_date')
    list_filter=('domain','created_date')
    list_per_page=100
    actions=None
    list_display_links=None

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request): 
        return False
    
    def get_keyword_list(self, obj):
        # return obj.keyword_list
        return format_html("<div style='width:750px; word-break: break-all;'>"+str(obj.keyword_list).strip()+"</div>") 
    get_keyword_list.short_description='Keyword Suggestion' 

admin.site.register(SiteKeywords, SiteKeywordSuggestionAdmin) 

# user Registration token admin datas
class UserregistrationtokenAdmin(admin.ModelAdmin):
    list_display=('id','get_email','created_date','get_ipAddress','get_user_agent')
    readonly_fields=('get_email','get_ipAddress')
    list_filter=('id','ip_address')
    list_per_page=100
    actions=None
    list_display_links=None

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request): 
        return False
    
    def get_email(self, obj):
        return obj.email
    get_email.short_description='Email'

    def get_ipAddress(self, obj):
        return obj.ip_address
    get_ipAddress.short_description='ip address'

    def get_user_agent(self, obj):
        data=''
        if obj.user_agent:
            dD = "-" if obj.user_agent is None else obj.user_agent
            data +=  dD
        if len(data.strip()):
            return format_html("<div style='width:200px; word-break: break-all;'>"+data.strip()+"</div>")
        else:
            return " - "
    get_user_agent.short_description='user agent'

    def created_date(self, obj):
        return obj.created_date.strftime("%b %d,%Y - %H:%M:%S")
    created_date.short_description='created date'

admin.site.register(Userregistrationtoken, UserregistrationtokenAdmin)


# mainsettings admin datas
class SettingsAdmin(admin.ModelAdmin):
    list_display=('id','get_core_coreman_corere_coremanmail', 'get_proxy_usage', 'get_core_refresh','get_daily_automation','get_daily_demand','get_rate')
    readonly_fields=('get_core_mode','get_core_manual_mail')
    list_per_page=100
    actions=None
    list_display_links=None
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request): 
        return False
    
    def get_core_coreman_corere_coremanmail(self, obj):
        data=""
        if obj.core_mode:
            dD = "-- Not Found --" if obj.core_mode is None else obj.core_mode
            data += "<b>Core Mode</b>: %s <br /><br />" % (dD)
        if obj.core_manual_mode:
            dD="--Not Found --" if obj.core_manual_mode is None else obj.core_manual_mode
            data += "<b>Core Manual Mode</b>: %s <br/><br/>" % (dD)
        if obj.core_kw_research_mode:
            dD="--Not Found --" if obj.core_kw_research_mode is None else obj.core_kw_research_mode
            data += "<b>Core Research Mode</b>: %s <br/><br/>" % (dD)
        if obj.core_manual_mail:
            dD="--Not Found --" if obj.core_manual_mail is None else obj.core_manual_mail
            data += "<b>Core Manual Mail</b>: %s <br/><br/>" % (dD)
        if len(data.strip()):
            return format_html("<div style='width:200px; word-break: break-all;'>"+data.strip()+"</div>")
        else:
            return " - "
    get_core_coreman_corere_coremanmail.short_description="core modes"
    
    def get_proxy_usage(self, obj):
        data = ""
        data += "<b>Max Load</b>: %s <br />" % str(obj.proxy_maximum_load_limit)
        data += "<b>Reset Limit</b>: %s <br /><br /><br />" % str(obj.proxy_reset_counter)
        data += "<b>Success Limit</b>: %s <br />" % str(obj.proxy_success_count)
        data += "<b>Failure Limit</b>: %s <br />" % str(obj.proxy_invalid_count)
        data += "<b>Exceeds Limit</b>: %s <br />" % str(obj.proxy_exceeds_count)
        if len(data.strip()):
            return format_html("<div style='width:200px; word-break: break-all;'>"+data.strip()+"</div>")
        else:
            return " - "
    get_proxy_usage.short_description="proxy status"

    def get_core_mode(self, obj):
        return obj.core_mode
    get_core_mode.short_description='core mode'

    def get_core_manual_mail(self, obj):
        return obj.core_manual_mail
    get_core_manual_mail.short_description='core manual mail'

    def get_core_refresh(self, obj):
        return obj.core_refresh_time.strftime("%b %d,%Y - %H:%M:%S")
    get_core_refresh.short_description='core refresh'

    def get_daily_automation(self, obj):
        if len(obj.daily_automation_count):
            return obj.daily_automation_count[0]
        else:
            return '-'
    get_daily_automation.short_description='daily automation'  

    def get_daily_demand(self, obj):
        if len(obj.daily_demand_count):
            return obj.daily_demand_count[0]
        else:
            return '-'
    get_daily_demand.short_description='daily demand'

    def get_core_man_mode(self, obj):
        return obj.core_manual_mode
    get_core_man_mode.short_description='core manual mode'

    def get_core_kw_re_mode(self, obj):
        return obj.core_kw_research_mode
    get_core_kw_re_mode.short_description='core keyword research mode'

    def get_rate(self, obj):
        return obj.rate_usd_inr
    get_rate.short_description='rate'

admin.site.register(Settings, SettingsAdmin)


# Report Admin datas
class ReportAdmin(admin.ModelAdmin):
    list_display=('id',"get_user_group",'get_delivery','get_group_name','get_recipient','get_frequency','get_report_format','get_dates')
    readonly_fields=('get_recipient','get_frequency')
    list_filter=("frequency",'recipient')
    list_per_page=100
    actions=None
    list_display_links=None

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request): 
        return False

    def get_user_group(self, obj):
        if obj.fb_user_id and obj.fk_group_id !=None:
            return str(obj.fb_user_id)+"/"+str(obj.fk_group_id)
        else:
            return '-'
    get_user_group.short_description="Uid/Gid"

    def get_group_name(self, obj):
        return obj.group_name
    get_group_name.short_description='Group'

    def get_recipient(self, obj):
        return obj.recipient
    get_recipient.short_description='Email'

    def get_frequency(self, obj):
        if obj.frequency==1:
            return "Day"
        elif obj.frequency==7:
            return "Week"
        else:
            return "Month"
    get_frequency.short_description='Schedule'
        
    def get_delivery(self, obj):
        data = ""
        if obj.last_delivery:
            dD = "-- Not Found --" if obj.last_delivery is None else obj.last_delivery.strftime("%b %d,%Y - %H:%M:%S")
            data += "<b>Last Delivery</b>:<br /> %s <br /><br />" % (dD) 
        if obj.next_delivery:
            dD = "-- Not Found --" if obj.next_delivery is None else obj.next_delivery.strftime("%b %d,%Y - %H:%M:%S")            
            data += "<b>Next Delivery</b>:<br /> %s <br /><br />" % (dD)
        if len(data.strip()):
            return format_html("<div style='width:150px; word-break: break-all;'>"+data.strip()+"</div>")
        else:
            return " - "
    get_delivery.short_description='Delivery'

    def get_report_format(self, obj):
        if len(obj.report_format):
            return obj.report_format
        else:
            return '-'
    get_report_format.short_description="Format"

    def get_dates(self, obj):
        data=''
        if obj.created_date:
            dD = "-- Not Found --" if obj.created_date is None else obj.created_date.strftime("%b %d,%Y - %H:%M:%S")            
            data += "<b>Created Date</b>:<br /> %s <br /><br />" % (dD)
        if obj.updated_date:
            dD = "-- Not Found --" if obj.updated_date is None else obj.updated_date.strftime("%b %d,%Y - %H:%M:%S")            
            data += "<b>Updated Date</b>:<br /> %s <br /><br />" % (dD)
        if len(data.strip()):
            return format_html("<div style='width:150px; word-break: break-all;'>"+data.strip()+"</div>")
        else:
            return " - "
    get_dates.short_description='Date'

admin.site.register(Report,ReportAdmin)



#Search Volume datas
class keywordVolumeAdmin(admin.ModelAdmin): 
    list_display = ('id', 'keyword','get_region', 'get_country', 'get_code','get_average', 'get_comp_level', 'get_comp_index', 'get_last_update_volume', 'status', 'get_modified', 'get_created')
    search_fields = ('status','keyword')
    readonly_fields=('id', 'keyword','get_region', 'get_country', 'get_code','get_average', 'get_comp_level', 'get_comp_index', 'get_last_update_volume', 'status', 'get_modified', 'get_created')
    list_filter = ("created_date", "region_name", "searchvolume_country_id")
    actions = None
    list_display_links = None
    list_per_page = 100
    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
    # This will help you to disbale view functionality
    def has_change_permission(self, request):
        return False

    def get_region(self, obj):
        return obj.region_name
    get_region.short_description = 'region'
    
    def get_country(self, obj):
        return obj.searchvolume_country_id
    get_country.short_description = 'sv code'

    def get_code(self, obj):
        return obj.region_code
    get_code.short_description = 'code'

    def get_average(self, obj):
        return obj.average_volume
    get_average.short_description = 'avg'

    def get_comp_level(self, obj):
        return obj.comp_level
    get_comp_level.short_description = 'c.level'

    def get_comp_index(self, obj):
        return obj.comp_index
    get_comp_index.short_description = 'c.index'

    def get_last_update_volume(self, obj):
        return obj.last_update_volume
    get_last_update_volume.short_description = 'record'

    def get_modified(self, obj):
        return "-- Not Found --" if obj.modified_date is None else obj.modified_date.strftime("%b %d,%Y - %H:%M:%S")
    get_modified.short_description = 'last'

    def get_created(self, obj):
        return "-- Not Found --" if obj.created_date is None else obj.created_date.strftime("%b %d,%Y - %H:%M:%S")
    get_created.short_description = 'since' 

admin.site.register(keywordVolume, keywordVolumeAdmin)

#Keyword datas
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user','get_rank','get_lstrnk', 'site_url', 'keyword', 'get_mancal', 'region', 'lastranked_date', 'platform','created_date','get_gsc_clicks','get_gsc_impressions')
    search_fields = ('site_url','keyword','platform')
    readonly_fields=('id', 'get_user', 'site_url', 'keyword','region', 'lastranked_date', 'platform','created_date')
    list_filter = ("created_date", "manual_call_mode", "lastranked_date", "fk_user_id") 
    actions = None
    list_display_links = None
    list_per_page = 100
    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
    # This will help you to disbale view functionality
    def has_change_permission(self, request):
        return False

    def get_mancal(self, obj):
        return obj.manual_call_status
    get_mancal.short_description = 'MR'

    def get_user(self, obj):
        return obj.fk_user_id
    get_user.short_description = 'uid'

    def get_rank(self, obj):
        if len(obj.rank) > 0:
            return obj.rank[0]
        else:
            return ['Not']
    get_rank.short_description = 'rank'

    def get_gsc_clicks(self, obj):
         return obj.gsc_clicks
    
    get_gsc_clicks.short_description = 'clicks'

    def get_gsc_impressions(self, obj):
        return obj.gsc_impressions
    
    get_gsc_impressions.short_description = 'Impressions'

    def get_lstrnk(self, obj):
        if len(obj.rank) > 1:
            return obj.rank[1]
        else:
            return ['Not']
    get_lstrnk.short_description = 'last rk'
  
admin.site.register(Keyword, KeywordAdmin)

# class brandTrackerAdmin(admin.ModelAdmin):
#     list_display = ('id','get_group', 'brand_name','region','status','get_created_date', 'get_conquestor_call_status', 'get_conquestor_recent_date', 'get_conquestor_mail_date')
#     readonly_fields=('id','get_group', 'brand_name','region','status','get_created_date', 'get_conquestor_call_status', 'get_conquestor_recent_date', 'get_conquestor_mail_date')
#     list_filter = ("brand_name", "created_date")
#     list_per_page = 100
#     actions = None
#     list_display_links = None   

#     def has_add_permission(self, request):
#         return False
#     def has_change_permission(self, request):
#         return False
#     def get_conquestor_call_status(self, obj):
#         return obj.conquestor_call_status
#     get_conquestor_call_status.short_description = 'level' 
#     def get_created_date(self, obj):
#         return obj.created_date.date()
#     get_created_date.short_description = 'since'
#     def get_group(self, obj):
#         return obj.fb_group_id
#     get_group.short_description = 'group'
#     def get_conquestor_recent_date(self, obj):
#         return "-- Not Found --" if obj.conquestor_recent_date is None else obj.conquestor_recent_date.strftime("%b %d,%Y - %H:%M:%S")
#     get_conquestor_recent_date.short_description = 'recent' 
#     def get_conquestor_mail_date(self, obj):
#         return "-- Not Found --" if obj.conquestor_recent_date is None else obj.conquestor_mail_date.strftime("%b %d,%Y - %H:%M:%S") 
#     get_conquestor_mail_date.short_description = 'mailed on'
    
# admin.site.register(brandTracker, brandTrackerAdmin)

# id, g_name, domain_name, updated_ date, group_call_status, manual_grp_trigger, project_automation_time
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'get_name','get_domain', 'get_KCOMPcount', 'get_mode', 'get_trigger', 'get_grpcalsts', 'get_grpcalsts_count', 'get_mancal_count', 'get_pat', 'get_last_update', 'get_since','gsc_site_status','get_track_status','gsc_last_track') 
    readonly_fields = ('id', 'get_user', 'get_name','get_domain', 'get_trigger', 'get_pat', 'get_last_update', 'get_since')
    list_filter = ("manual_grp_trigger","group_call_status", "paymentmode", "created_date", "updated_date")
    list_per_page = 100
    actions = None
    list_display_links = None    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request):
        return False
    def get_user(self, obj):
        return obj.fk_user_id
    get_user.short_description = 'user' 
    def get_name(self, obj):
        return obj.group_name
    get_name.short_description = 'group name' 
    def get_domain(self, obj):
        return obj.domain_name
    get_domain.short_description = 'domain' 
    
    def get_mode(self, obj):
        return obj.paymentmode
    get_mode.short_description = 'Paymode'

    def get_trigger(self, obj):
        return obj.manual_grp_trigger
    get_trigger.short_description = 'Manual'
    
    def get_grpcalsts(self, obj):
        return obj.group_call_status
    get_grpcalsts.short_description = 'Auto'
    
    def get_grpcalsts_count(self, obj):
        cnt = 0
        if obj.group_call_status != "COMP":
            cnt = Keyword.objects.filter(fk_group_id=obj.id).exclude(auto_call_status="done").count()
        return cnt
    get_grpcalsts_count.short_description = 'A-count'
    
    def get_mancal_count(self, obj):
        cnt = 0
        if obj.manual_grp_trigger != "DONE":
            cnt = Keyword.objects.filter(fk_group_id=obj.id, manual_call_status__in=[True]).count()
        return cnt
    get_mancal_count.short_description = 'M-count'

    def get_pat(self, obj):
        return "-- Not Found --" if obj.project_automation_time is None else obj.project_automation_time.strftime("%b %d,%Y - %H:%M:%S") 
    get_pat.short_description = 'A-Execution Time' 
    def get_last_update(self, obj):
        return "-- Not Found --" if obj.updated_date is None else obj.updated_date.strftime("%b %d,%Y - %H:%M:%S") 
    get_last_update.short_description = 'updated on'
    def get_since(self, obj):
        return "-- Not Found --" if obj.created_date is None else obj.created_date.date()
    get_since.short_description = 'since'
    def get_KCOMPcount(self, obj):
        kc = Keyword.objects.filter(fk_group_id=obj.id).count()
        cpcount = CompProject.objects.filter(fk_group_id=obj.id).count()
        ckcount = CompKeyword.objects.filter(fk_group_id=obj.id).count()

        return str(kc)+"/"+str(cpcount)+"/"+str(ckcount)
    get_KCOMPcount.short_description = 'K/CP/CK Count'

    def get_track_status(self, obj):
        return obj.gsc_track_status
    get_track_status.short_description = 'GSC Track Status' 

admin.site.register(project, GroupAdmin)

#admin module unregister 
admin.site.unregister(Group)



#Account Usage datas
class AccountusageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user','get_user_email','get_KRPlimit', 'get_KPCOMPcount', 'status','user_type','gsc_token','get_track_status','gsc_last_track')
    search_fields = ('status','user_type')
    readonly_fields=('id', 'get_user', 'status', 'user_type')
    list_filter = ("created_date", "status", "user_type", "fb_user_id") 
    actions = None
    list_display_links = None
    list_per_page = 100
    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
    # This will help you to disbale view functionality
    def has_change_permission(self, request):
        return False

    def get_user(self, obj):
        return obj.fb_user_id
    get_user.short_description = 'uid'

    def get_user_email(self, obj):
        AccIns = Account.objects.filter(id=obj.fb_user_id).first()
        if AccIns:
            return AccIns.email
        return "-"
    get_user_email.short_description = 'email'

    def get_KRPlimit(self, obj):
        return ''+str(obj.plan_keyword_limit)+' - '+str(obj.plan_refresh_limit)+' - '+str(obj.plan_project_limit)
    get_KRPlimit.short_description = 'KRP Limit'

    def get_KPCOMPcount(self, obj):
        kc = Keyword.objects.filter(fk_user_id=obj.fb_user_id).count()
        gc = project.objects.filter(fk_user_id=obj.fb_user_id).count() 
        cpcount = CompProject.objects.filter(fk_user_id=obj.fb_user_id).count()
        ckcount = CompKeyword.objects.filter(fk_user_id=obj.fb_user_id).count()

        return str(kc)+"/"+str(gc)+"/"+str(cpcount)+"/"+str(ckcount) 

    get_KPCOMPcount.short_description = 'K/P/CP/CK Count'

    def get_track_status(self, obj):
        return obj.gsc_track_status
    get_track_status.short_description = 'GSC Track Status'  
    
admin.site.register(Accountusage, AccountusageAdmin) 
