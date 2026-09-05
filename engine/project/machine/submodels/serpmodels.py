from djongo import models
from django.conf import settings
from project.machine.submodels.accountmodels import Account
from datetime import datetime 

TRIALDAYS = 14

class DAccountUsage(models.Model):   
    fb_user = models.ForeignKey('Account', on_delete=models.CASCADE)    
    current_plan_id = models.IntegerField() 
    future_plan_id = models.IntegerField() 
    last_used_refresh_count = models.IntegerField(default=0)  
    plan_keyword_limit = models.IntegerField(default=0) 
    plan_refresh_limit = models.IntegerField(default=0)
    plan_project_limit = models.IntegerField(default=1)
    used_refresh_limit = models.IntegerField(default=0)  
    validity_from = models.DateTimeField()
    validity_to = models.DateTimeField()   
    status = models.CharField(max_length = 100) 
    st_purchase_id = models.IntegerField(default = 0)
    # BYOK — same `accountusage` collection the backend writes to. Declared here
    # so the engine can read the account's own key and page depth instead of
    # falling back to the operator's global key and a hardcoded page count.
    serp_provider = models.CharField(max_length=50, default="datablue")
    serp_key = models.TextField(blank=True, default="")
    serp_depth = models.IntegerField(default=1) 
    st_subscription_id = models.CharField(max_length = 50, null=True) 
    st_customer_id = models.CharField(max_length = 100, null=True)
    st_user_mail = models.CharField(max_length = 100, null=True) 
    mail_max_keyword_reach = models.CharField(max_length = 5, default="-") 
    automatic_mail_status = models.CharField(max_length = 15, default="COMP") #VOID, START, SCHD, COMP, FAIL
    startup_base_plan = models.JSONField(default={})
    plan_cancel_request = models.JSONField(default={})
    future_upgrade_plan = models.JSONField(default={})  
    created_date = models.DateTimeField(auto_now_add = True, auto_now = False) 
    modified_date = models.DateTimeField(auto_now_add = False, auto_now = True) 
    freemium_credit_usage = models.JSONField(default={})
    redeem_api_call_count = models.IntegerField(default=0) 
    keyword_research_searches = models.JSONField(blank=True, default=[]) #suggestion keywords
    trial_days = models.IntegerField(default=TRIALDAYS)
    user_type = models.CharField(max_length = 10, default="trial")  #Trial, Free(pre user), Redeem, Stripe
    st_redeem_id = models.CharField(max_length = 100, null=True)
    plan_competitor_limit = models.IntegerField(default=1)  
    project_competitor_limit = models.IntegerField(default=1) 
    plan_kw_research_limit = models.IntegerField(default=30)  
    plan_per_day_kw_research_limit = models.IntegerField(default=3)  
    used_kw_research_limit = models.IntegerField(default=0)
    used_per_day_kw_research_limit = models.IntegerField(default=0)  
    primary_keyword_limit = models.IntegerField(default=2)  
    
    # PAGE AUDIT
    gsc_token = models.TextField(default = 'NA')
    gsc_track_status = models.CharField(max_length=10, default="NA")
    gsc_last_track = models.DateTimeField(null=True,default=datetime.utcnow)
    page_audit_limit = models.IntegerField(default=0)
    used_page_audit_limit = models.IntegerField(default=0)
    
    # BACKLINK MANAGER
    backlink_monit_limit = models.IntegerField(default=0)
    used_backlink_monit_limit = models.IntegerField(default=0)

    # KEYWORD OPPORTUNITIES
    kwopportunities_limit = models.IntegerField(default=0)
    used_kwopportunities_limit = models.IntegerField(default=0)
    kwo_track_status = models.CharField(max_length=10, default="NA")
    kwo_last_track = models.DateTimeField(null=True)

    class Meta:
        db_table = "accountusage" 

class DKeyword(models.Model):
    keyword = models.TextField()
    site_url = models.TextField()
    target = models.TextField(null=True)
    location = models.TextField(null=True)
    postdata = models.JSONField(default={})
    exactdomain = models.BooleanField(default=0) 
    region = models.CharField(max_length=20)
    language = models.CharField(max_length=15)
    language_code = models.CharField(max_length=8, null=True)     
    platform = models.CharField(max_length=10)
    fk_group = models.ForeignKey('DGroups', on_delete=models.CASCADE,default=1) 
    fk_user = models.ForeignKey('Account', on_delete=models.CASCADE) 
    tags = models.JSONField(blank=True, default=[])
    tagcount = models.IntegerField(default=0)
    rank = models.JSONField(blank=True, default=[])
    ranknow = models.IntegerField(default=0)
    rank_sincestart = models.IntegerField(default=0)  
    # task_id = models.CharField(max_length=25)
    search_results = models.CharField(max_length=50,default="-")  
    search_volume = models.CharField(max_length=50,default="init")  
    featured_snippet = models.BooleanField(default=0) 
    review = models.BooleanField(default=0) 
    knowledge_panel = models.BooleanField(default=0) 
    ads = models.BooleanField(default=0) 
    total_rating = models.CharField(max_length=5,blank=True,default="")
    total_review = models.CharField(max_length=15,blank=True,default="") 
    snippets_details = models.JSONField(default={})
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField()
    lastranked_date = models.DateTimeField()
    dayval = models.IntegerField(default=0)
    weekval = models.IntegerField(default=0) 
    halfmonthval = models.IntegerField(default=0)
    daymark = models.CharField(max_length=5)
    weekmark = models.CharField(max_length=5)
    halfmonthmark = models.CharField(max_length=5, default="-")    
    status_from_start = models.CharField(max_length=5)
    isocode = models.CharField(max_length=5)
    favour = models.IntegerField(default=0)
    auto_refresh_count = models.IntegerField(null=True,blank=True,default=0)
    strict_refresh_count = models.IntegerField(null=True,blank=True,default=0)
    manual_call_status = models.BooleanField(default=0) 
    manual_call_mode = models.CharField(max_length=6,default="done") 
    manual_task_allocation = models.CharField(max_length=15,default="-")  
    updated_date = models.DateTimeField(auto_now_add = False, auto_now = True)
    keyword_alias = models.TextField(default="")  
    page_uuid_url = models.TextField(default="-")    
    page_uuid = models.TextField(default="-")
    top_rank = models.IntegerField(default=0)  
    cannibalisation = models.JSONField(blank=True, default=[])  
    cannibalisation_mail_status = models.CharField(max_length=5, default="-") 
    keyword_snippet = models.JSONField(default={'tdy':{},'best':{}})
    # "avail" -- a keyword that has never been measured is waiting to be, not
    # finished. This is the same `keyword` collection the mongoengine Keyword
    # model and backend/serp/models.py declare; all three now agree. A shared
    # field with three declarations and two defaults is what made every new
    # keyword look already-done.
    auto_call_status = models.CharField(max_length=5,default="avail")
    manual_task_count = models.IntegerField(default=0)
    
    # PAGE AUDIT
    gsc_clicks = models.CharField(max_length=15,blank=True,default="0")
    gsc_impressions = models.CharField(max_length=15,blank=True,default="0")
    gsc_ctr = models.CharField(max_length=15,blank=True,default="0")
    gsc_position = models.CharField(max_length=15,blank=True,default="0")

    # KEYWORD OPPORTUNITIES
    geo_target = models.TextField(default="") 
    geo_target_uule = models.TextField(default="")  

    class Meta:
        db_table = "keyword"

class DGroups(models.Model): 
    fk_user = models.ForeignKey('Account', on_delete=models.CASCADE) #foriegn key
    group_name = models.CharField(max_length = 100)
    strict_refresh_switch = models.BooleanField(default=True) # 'True' Group refresh enabled 
    activity_level = models.JSONField(blank=True, default=[])
    total_Keyword = models.JSONField(blank=True, default=[]) 
    since_start = models.JSONField(blank=True, default=[]) 
    since_position = models.JSONField(blank=True, default=[])  
    score_meter = models.JSONField(blank=True, default=[])
    domain_name = models.CharField(max_length=500, null=True)
    top_score = models.CharField(null=True, max_length=30)
    domain_info = models.JSONField(default={}) 
    domain_status = models.CharField(max_length=10, default="ON")  
    last_used_refresh_count = models.IntegerField(default=0)
    paymentmode = models.CharField(max_length=15,default="")
    manual_grp_trigger = models.CharField(max_length = 5, default = "DONE") 
    automation_email_notify_log = models.JSONField(default={})  
    automation_email_switch = models.JSONField(default={})  
    automation_email_recipients = models.JSONField(blank=True, default=[])
    dashboard_view = models.CharField(max_length=30, default='listview')
    grid_sort = models.CharField(max_length=30, default='tags')
    project_automation_time = models.DateTimeField(null=True) 
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add = False, auto_now = True)
    group_call_status = models.CharField(max_length = 5, default = "COMP")
    competitor_analyse_json = models.JSONField(default={})
    competitor_analyse_status = models.CharField(max_length = 5, default="VOID") #VOID, START, SCHD, COMP, FAIL
    non_columns = models.JSONField(blank=True, default=[])
    competitor_project_array = models.JSONField(blank=True, default=[])
    competitor_project_status = models.CharField(max_length = 5, default="VOID") #VOID, START, SCHD, COMP, FAIL 
    # PAGE AUDIT
    gsc_track_status = models.CharField(max_length=10, default="NA")
    gsc_last_track = models.DateTimeField(null=True,default=datetime.utcnow) 
    gsc_site_status = models.BooleanField(default=False) 

    # GSC ACCESS
    gsc_refresh_token = models.TextField(default="") 

    def __str__(self):
        return self.group_name
    class Meta:
        db_table = "group"

class DCompProject(models.Model):
    # FOREIGN KEYS
    fk_user = models.ForeignKey('Account', on_delete=models.CASCADE)
    fk_group = models.ForeignKey('DGroups', on_delete=models.CASCADE)
    # OTHER FIELDS
    cp_group_name = models.CharField(max_length = 100)
    cp_domain_name = models.CharField(max_length=500, null=True)
    cp_grp_trigger = models.CharField(max_length = 5, default = "DONE") 
    cp_total_keyword = models.JSONField(blank=True, default=[]) 

    cp_top_score = models.CharField(null=True, max_length=10)
    mn_top_score = models.CharField(null=True, max_length=10)
    cp_activity_level = models.JSONField(blank=True, default=[])
    mn_activity_level = models.JSONField(blank=True, default=[])
    cp_since_position = models.JSONField(blank=True, default=[])  
    mn_since_position = models.JSONField(blank=True, default=[])  
    cp_score_meter = models.JSONField(blank=True, default=[])
    mn_score_meter = models.JSONField(blank=True, default=[])
    group_call_status = models.CharField(max_length=5, default = "COMP")
    keyword_ids = models.JSONField(blank=True, default=[])
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add = False, auto_now = True)

    def __str__(self):
        return self.cp_group_name 
    class Meta:
        db_table = "competitor_project"

class DCompKeyword(models.Model): 
    # FOREIGN KEYS
    fk_user = models.ForeignKey('Account', on_delete=models.CASCADE)
    fk_group = models.ForeignKey('DGroups', on_delete=models.CASCADE)
    fk_keyword = models.ForeignKey('DKeyword', on_delete=models.CASCADE)
    fk_cp_project = models.ForeignKey('DCompProject', on_delete=models.CASCADE)  

    # OTHER FIELDS
    cp_site_url = models.TextField()
    target = models.TextField(null=True)
    rank = models.JSONField(blank=True, default=[])
    ranknow = models.IntegerField(default=0)
    rank_sincestart = models.IntegerField(default=0)  
    language_code = models.CharField(max_length=8, null=True)
    featured_snippet = models.BooleanField(default=0) 
    review = models.BooleanField(default=0) 
    knowledge_panel = models.BooleanField(default=0) 
    ads = models.BooleanField(default=0) 
    total_rating = models.CharField(max_length=5, blank=True, default=None)
    total_review = models.CharField(max_length=15, blank=True, default=None) 
    snippets_details = models.JSONField(default={})
    dayval = models.IntegerField(default=0)
    weekval = models.IntegerField(default=0)
    halfmonthval = models.IntegerField(default=0)
    daymark = models.CharField(max_length=5, default="-") 
    weekmark = models.CharField(max_length=5, default="-")
    halfmonthmark = models.CharField(max_length=5, default="-")    
    status_from_start = models.CharField(max_length=5, default="-")
    comp_call_mode = models.CharField(max_length=5, default="done")
    auto_call_status = models.CharField(max_length=5,default="done")
    top_rank = models.IntegerField(default=0)
    lastranked_date = models.DateTimeField()

    comp_call_status = models.BooleanField(default=0)
    platform = models.CharField(max_length=10, default="desktop")
    isocode = models.CharField(max_length=5, default="us")
    keyword = models.TextField(default="")
    # keyword_alias = models.TextField(default="")

    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
    # Auto updated when the data is altered
    modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)

    class Meta:
        db_table = "competitor_keyword"  