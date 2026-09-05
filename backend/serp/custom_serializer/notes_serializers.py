from rest_framework import serializers
from django.conf import settings as DEF_SETTINGS 
from django.utils import timezone
from serp.models import * 

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day)) 

class ViewNoteSerializer(serializers.ModelSerializer):
	ky = serializers.SerializerMethodField('get_ky')
	tl = serializers.SerializerMethodField('get_tl')
	nt = serializers.SerializerMethodField('get_nt')
	nd = serializers.SerializerMethodField('get_nd')
	kk = serializers.SerializerMethodField('get_kk')
	class Meta: 
		model = kwNotes
		fields = ('ky', 'kk', 'tl', 'nt', 'nd')

	def get_ky(self, obj):
		return obj["id"]

	def get_tl(self, obj):
		return obj["title"]

	def get_nt(self, obj):
		return obj["notes"]

	def get_kk(self, obj):
		return obj["fk_keyword_id"]

	def get_nd(self, obj):
		# return custom_strftime('%b {S}, %Y', obj["note_date"]) 
		return custom_strftime('%Y-%m-%d', timezone.localtime(obj["note_date"]))
