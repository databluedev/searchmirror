from django.contrib import admin
from llmtracker.models import LLMPrompt


@admin.register(LLMPrompt)
class LLMPromptAdmin(admin.ModelAdmin):
    list_display = ('prompt_id', 'prompt', 'fk_user', 'fk_group', 'track_status', 'created_date')
    list_filter = ('track_status', 'created_date')
    search_fields = ('prompt', 'fk_user__username', 'fk_group__group_name')
    readonly_fields = ('prompt_id', 'created_date', 'modified_date')
