from django.contrib import admin
from .models import CompProject, CompKeyword
from datetime import datetime, date
from account.models import Account

class CompProjectAdmin(admin.ModelAdmin):
	list_display = ('id', 'get_user', 'get_group', 'cp_domain_name', 'get_created', 'get_updated')
	search_fields = ('cp_domain_name', 'updated_date') 
	readonly_fields=('id', 'get_user', 'get_group', 'cp_domain_name', 'get_created', 'get_updated')
	list_filter = ("cp_domain_name", "updated_date")   
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
		return obj.fk_user_id
	get_user.short_description = 'uid'
	
	def get_group(self, obj):
		return obj.fk_group_id
	get_group.short_description = 'project' 
	
	def get_updated(self, obj):
		return "-- Not Found --" if obj.updated_date is None else obj.updated_date.strftime("%b %d,%Y - %H:%M:%S")
	get_updated.short_description = 'last'

	def get_created(self, obj):
		return "-- Not Found --" if obj.created_date is None else obj.created_date.strftime("%b %d,%Y - %H:%M:%S")
	get_created.short_description = 'since' 

admin.site.register(CompProject, CompProjectAdmin) 

class CompKeywordAdmin(admin.ModelAdmin):
	list_display = ('id', 'get_user', 'get_group', 'get_cgroup', 'comp_call_mode', 'keyword', 'ranknow', 'get_lastranked_date', 'cp_site_url', 'get_created')
	search_fields = ('keyword', 'cp_site_url') 
	readonly_fields=('id', 'get_user', 'get_group', 'get_cgroup', 'comp_call_mode', 'keyword', 'ranknow', 'get_lastranked_date', 'cp_site_url', 'get_created')
	list_filter = ('comp_call_mode', 'lastranked_date')
	actions = None
	list_display_links = None
	list_per_page = 500
	
	# This will help you to disbale add functionality
	def has_add_permission(self, request):
		return False
	# This will help you to disbale view functionality
	def has_change_permission(self, request):
		return False

	def get_user(self, obj):
		return obj.fk_user_id
	get_user.short_description = 'user' 
	
	def get_group(self, obj):
		return obj.fk_group_id
	get_group.short_description = 'project'

	def get_cgroup(self, obj):
		return obj.fk_cp_project_id
	get_cgroup.short_description = 'comp-project'
	
	def get_lastranked_date(self, obj):
		return "-- Not Found --" if obj.lastranked_date is None else obj.lastranked_date.strftime("%b %d,%Y - %H:%M:%S")
	get_lastranked_date.short_description = 'last ranked' 

	def get_created(self, obj):
		return "-- Not Found --" if obj.created_date is None else obj.created_date.strftime("%b %d,%Y - %H:%M:%S")
	get_created.short_description = 'since' 

admin.site.register(CompKeyword, CompKeywordAdmin)