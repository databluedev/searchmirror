from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import Account
from serp.models import Usersettings, Keyword, clientTracker
from rest_framework.authtoken.admin import (TokenProxy)
from rest_framework.authtoken.models import Token
from django.utils.html import format_html

class AccountAdmin(UserAdmin):
    list_display = ('id', 'email','username', 'traffic_source', 'date_joined', 'last_home_visit', 'get_exit_last', 'total_keyword_count', 'get_location')
    search_fields = ('email','username',)
    readonly_fields=('date_joined', 'last_home_visit') 
    filter_horizontal = ()
    list_filter = ("date_joined", 'last_home_visit', "email")  
    fieldsets = ()
    list_per_page = 100 
    list_display_links = None
    actions = None
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request):
        return False
    def traffic_source(self, obj):
        data = ""
        if obj.campaign.lower() != "na" and obj.campaign.strip() != "":
            data += "<b>Campaign</b>:<br /> %s <br /><br />" % (obj.campaign)
        if obj.medium.lower() != "na" and obj.medium.strip() != "":
            data += "<b>Medium</b>:<br /> %s <br /><br />" % (obj.medium)
        if obj.source.lower() != "na" and obj.source.strip() != "":
            data += "<b>Source</b>:<br /> %s <br /><br />" % (obj.source)
        if obj.referral.lower() != "na" and obj.referral.strip() != "":
            data += "<b>Referral</b>:<br /> %s <br />" % (obj.referral)

        if len(data.strip()):
            return format_html("<div style='width:250px; word-break: break-all;'>"+data.strip()+"</div>") 
        else:
            return " - "

    traffic_source.allow_tags = True
    traffic_source.short_description = 'traffic source'  

    def total_keyword_count(self, obj):
        if obj.id:
            keyCount = Keyword.objects.filter(fk_user_id=obj.id).count()
            if keyCount > 0:
                return keyCount

        return 0
    
    total_keyword_count.short_description = 'keyword count' 
    
    def get_exit_last(self, obj):
        if obj.id:
            usdata = Usersettings.objects.filter(fb_user_id=obj.id).first()
            if usdata != None and len(usdata.exit_last_landed_on) > 0 :
                return usdata.exit_last_landed_on[0]
            else:
                return '-'
        else:
            return '-'

    get_exit_last.short_description = 'last view'

    def get_location(self, obj):
        if obj.id:
            usdata = clientTracker.objects.filter(fb_user_id=obj.id).first()
            if usdata != None:
                a = [usdata.city,usdata.region,usdata.country]
                location = list(filter(None, a))
                return ", ".join(location)
            else:
                return '-'
        else:
            return '-'

    get_location.short_description = 'location'

admin.site.register(Account, AccountAdmin)

#admin module unregister 
# admin.site.unregister(Token)
admin.site.unregister(TokenProxy)

class TokenAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'key', 'created')
    readonly_fields=('user_id', 'key', 'created')
    list_filter = ("user_id","created")
    list_per_page = 20
    actions = None
    list_display_links = None    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request):
        return False
      
admin.site.register(Token, TokenAdmin)


