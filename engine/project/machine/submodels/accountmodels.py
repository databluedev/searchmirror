from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import date,datetime,timedelta
from django.conf import settings

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from rest_framework.authtoken.models import Token 


class Account(AbstractBaseUser):
	email 					= models.EmailField(verbose_name="email", max_length=60, unique=True,error_messages={
                            'unique': "User with this email already exists.",
                        })
	username 				= models.CharField(max_length=30, unique=False)
	date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
	last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)
	last_logout				= models.DateTimeField(verbose_name='last logout',null=True)
	last_home_visit			= models.DateTimeField() 
	is_admin				= models.BooleanField(default=False)
	is_active				= models.BooleanField(default=True)
	is_staff				= models.BooleanField(default=False)
	is_superuser			= models.BooleanField(default=False)
	google_id				= models.CharField(max_length = 100, default = '-')
	account_status			= models.CharField(max_length = 100, default = 'normal')
	normal_mode				= models.CharField(max_length = 100, default = 'enable')
	social_mode				= models.CharField(max_length = 100, default = 'disable')
	mail_count_status_no_keyword = models.IntegerField(default=0) 
	mail_no_keyword_routine = models.DateTimeField(auto_now_add = True, auto_now = False)
	designation = models.CharField(max_length = 35, default = '')
	campaign = models.TextField(default = 'NA')
	medium = models.TextField(default = 'NA')
	source = models.TextField(default = 'NA')
	referral = models.TextField(default = 'NA') 
	# personal_info = models.JSONField(default={})
	# personal_info = models.DictField(default={})
	# address = models.JSONField(default={})

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	# objects = MyAccountManager()  

	def __str__(self):
		return self.email

	# For checking permissions. to keep it simple all admin have ALL permissons
	def has_perm(self, perm, obj=None):
		return self.is_admin

	# Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
	def has_module_perms(self, app_label):
		return True
	class Meta:
	    db_table = "account"
	