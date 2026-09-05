""" contains basic admin views for MultiToken """
from django.contrib import admin
from account.authorization.models import ResetPasswordToken


@admin.register(ResetPasswordToken)
class ResetPasswordTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at', 'ip_address', 'user_agent')
    actions = None
    list_display_links = None    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request):
        return False
