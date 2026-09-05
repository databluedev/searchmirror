# project/machine/models.py 

from django.conf import settings
import mongoengine
from mongoengine import Document, EmbeddedDocument, fields
from project.machine.submodels.accountmodels import Account
from project.machine.submodels.serpmodels import DKeyword, DGroups, DCompProject, DCompKeyword
from project.machine.submodels.researchmodels import DKeywordResearch
from project.machine.submodels.contentgapmodels import * # NEW
from datetime import datetime 

class BrandTracker(Document): 
    oid = fields.ObjectIdField(db_field = '_id')
    fb_user_id = fields.IntField()  
    fb_group_id = fields.IntField()
    brand_name = fields.StringField(max_length = 50, null=True) 
    region = fields.StringField(max_length=20)
    isocode = fields.StringField(max_length=5)
    conquestor_call_status = fields.StringField(max_length=10, default="done") #avail, busy, done, fail, stop 
    conquestor_url_list = fields.ListField(blank=True, default=[])
    conquestor_recent_list = fields.ListField(blank=True, default=[]) 
    conquestor_recent_date = fields.DateTimeField(null=True) 
    conquestor_mail_date = fields.DateTimeField(null=True)
    conquestor_refresh_count = fields.IntField(default=0)  
    status = fields.StringField(max_length=5, default="off")
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True)
    meta = {
        'collection': 'brand_conquestor'
    }

class ClientTracker(Document): 
    oid = fields.ObjectIdField(db_field = '_id')
    fb_user_id = fields.IntField()
    client_ip = fields.StringField(max_length = 60, null=True) 
    client_agent = fields.StringField(null=True)
    time_zone = fields.StringField(max_length = 50, null=True) 
    country_code = fields.StringField(max_length = 5, null=True)
    country = fields.StringField(max_length = 70, null=True)  
    region = fields.StringField(max_length = 100, null=True)
    city = fields.StringField(max_length = 100, null=True)
    mobile = fields.BooleanField(default=0) 
    other_info = fields.DictField(default={})
    status = fields.StringField(max_length = 6, null=True) # START, BUSY, FAIL, DONE
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False) 
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True) 
    user_automation_time = fields.DateTimeField(null=True)

    meta = {
        'collection': 'account_tracker'
    }

class KeywordHistory(Document):
    oid = fields.ObjectIdField(db_field = '_id')
    fk_keyword_id = fields.IntField()  
    fk_user_id = fields.IntField() 
    fk_group_id = fields.IntField()
    new_featured_snippet_date = fields.DateTimeField(blank=True)
    featured_snippet_url_list = fields.ListField(blank=True, default=[])
    featured_snippet_history = fields.DictField(default={}) 
    new_ad_snippet_date = fields.DateTimeField(blank=True)
    ad_snippet_url_list = fields.ListField(blank=True, default=[])
    ad_snippet_history = fields.DictField(default={})  
    url_status = fields.StringField(default="CMN")
    other_history = fields.DictField(default={})  
    comp_today = fields.DictField(default={}) 
    ratings_changed_date = fields.DateTimeField(null=True) 
    top_ratings = fields.StringField(max_length=5, default="-")   
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True)   
    meta = {
        'collection': 'keywordhistory'
    } 

class Keyword(Document):  
    oid = fields.ObjectIdField(db_field = '_id')  
    keyword = fields.StringField()
    site_url = fields.StringField()
    target = fields.StringField(null=True)
    location = fields.StringField(null=True) 
    postdata = fields.DictField() 
    exactdomain = fields.BooleanField(default=0) 
    region = fields.StringField(max_length=20) 
    language = fields.StringField(max_length=15)
    language_code = fields.StringField(max_length=8) 
    platform = fields.StringField(max_length=10)
    fk_group_id = fields.IntField()  
    fk_user_id = fields.IntField() 
    tags = fields.ListField(blank=True)
    tagcount = fields.IntField(default=0)
    rank = fields.ListField(blank=True) 
    ranknow = fields.IntField(default=0)
    rank_sincestart = fields.IntField(default=0) 
    search_results = fields.StringField(max_length=50)   
    search_volume = fields.StringField(max_length=50)    
    featured_snippet = fields.BooleanField(default=0) 
    review = fields.BooleanField(default=0) 
    knowledge_panel = fields.BooleanField(default=0)
    ads = fields.BooleanField(default=0)
    total_rating = fields.StringField(max_length=5,blank=True,default="")
    total_review = fields.StringField(max_length=15,blank=True,default="")  
    snippets_details = fields.DictField()
    # Tri-state SERP feature record written by parser_json.extract_serp_features.
    # {} means never measured -- distinct from a block measured as absent. The
    # booleans above cannot carry that difference; do not infer one from them.
    serp_features = fields.DictField(default={})
    created_date = fields.DateTimeField(auto_now_add=True)
    modified_date = fields.DateTimeField()
    lastranked_date = fields.DateTimeField() 
    dayval = fields.IntField(default=0)
    weekval = fields.IntField(default=0)
    monthval = fields.IntField(default=0)
    halfmonthval = fields.IntField(default=0) 
    daymark = fields.StringField(max_length=5)
    weekmark = fields.StringField(max_length=5)
    monthmark = fields.StringField(max_length=5) 
    halfmonthmark = fields.StringField(max_length=5)
    status_from_start = fields.StringField(max_length=5)
    isocode = fields.StringField(max_length=5)
    favour = fields.IntField(default=0) 
    auto_refresh_count = fields.IntField(null=True,blank=True,default=0)
    strict_refresh_count = fields.IntField(null=True,blank=True,default=0)  
    manual_call_status = fields.BooleanField(default=0)
    manual_call_mode = fields.StringField(max_length=5,blank=False,default='done')   
    manual_task_allocation = fields.StringField(max_length=15, null=True, default="-")     
    updated_date = fields.DateTimeField(auto_now_add=False, auto_now=True) 
    keyword_alias = fields.StringField(default="")  
    page_uuid_url = fields.StringField(default='-')  
    page_uuid = fields.StringField(max_length=50,default='-') 
    top_rank = fields.IntField(null=True) 
    cannibalisation = fields.ListField(blank=True, default=[]) 
    cannibalisation_mail_status = fields.StringField(max_length=5, default="-")      
    keyword_snippet = fields.DictField(default={'tdy':{}, 'best':{}})  
    auto_call_status = fields.StringField(max_length=5,blank=False,default='avail')
    manual_task_count = fields.IntField(default=0)

    # PER-KEYWORD SERP OVERRIDES (backend serp/models.py, migration 0011).
    # Null means "inherit" -- the account's depth and the project's Lite/Advanced
    # flag. Declared here because mongoengine refuses to load a document
    # carrying a field the class does not know, so an undeclared column in the
    # collection takes down every keyword read in this process, not just the
    # code that wanted the new value.
    serp_pages = fields.IntField(null=True, default=None)
    serp_advanced = fields.BooleanField(null=True, default=None)

    # CLAIM AND FAILURE ACCOUNTING (ENGINE + MANUAL)
    # call_claim_date is stamped every time a worker takes this keyword, so a
    # claim left behind by a worker that died can be recognised and taken over
    # instead of stranding the row forever.  The failure fields keep a failed
    # keyword retryable and, once its attempt budget is spent, record why it
    # was never measured -- writing 'done' on failure loses both facts and is
    # what stopped 1,437 keywords retrying (docs/ORCHESTRATION.md 2).
    call_claim_date = fields.DateTimeField(null=True)
    call_fail_count = fields.IntField(default=0)
    call_fail_reason = fields.StringField(default="")
    call_fail_date = fields.DateTimeField(null=True)
    call_retry_date = fields.DateTimeField(null=True)

    # ONLY FOR ENGINE FIELDS
    crawlurl = fields.StringField()    

    # PAGE AUDIT
    gsc_clicks = fields.StringField(max_length=15,blank=True,default="0")
    gsc_impressions = fields.StringField(max_length=15,blank=True,default="0")
    gsc_clicks_last_week = fields.StringField(max_length=15,blank=True,default="0")
    gsc_impressions_last_week = fields.StringField(max_length=15,blank=True,default="0") 
    gsc_ctr = fields.StringField(max_length=15,blank=True,default="0")
    gsc_position = fields.StringField(max_length=15,blank=True,default="0")

     # Location Search
    geo_target = fields.StringField(default="") 
    geo_target_uule = fields.StringField(default="")
    
    meta = {
        'collection': 'keyword',
        # The scheduler draws its work from these three predicates on every
        # pass; unindexed they are collection scans over every tenant's rows.
        'indexes': [
            ('fk_group_id', 'auto_call_status'),
            ('fk_group_id', 'manual_call_status'),
            ('auto_call_status', 'call_retry_date'),
        ],
    }

class ManualRefresh(Document):   
    oid = fields.ObjectIdField(db_field = '_id') 
    fb_user_id = fields.IntField()  
    fk_group_id = fields.IntField()  
    refresh_type = fields.StringField()
    refresh_time = fields.DateTimeField()
    created_date = fields.DateTimeField()
    refresh_status = fields.StringField()   #start, wait, done.

    # Why the last refresh of this project failed, if it did.  The API reads
    # these back out on /refreshstatus (errc / err) and renders the message
    # verbatim, so only the engine writes them and only in plain language --
    # codes are the backend's, in backend/serp/refresh_error.py.
    refresh_error_code = fields.StringField(max_length=32, default="")
    refresh_error = fields.StringField(default="")
    meta = {
        'collection': 'manualrefresh' 
    }

class Group(Document):  
    oid = fields.ObjectIdField(db_field = '_id')  
    fk_user_id = fields.IntField() #foriegn key 
    group_name = fields.StringField(max_length = 100)
    strict_refresh_switch = fields.BooleanField(default=False) # 'True' Group refresh enabled
    activity_level = fields.ListField(blank=True)  
    total_Keyword = fields.ListField(blank=True) 
    since_start = fields.ListField(blank=True)  
    since_position = fields.ListField(blank=True)   
    score_meter = fields.ListField(blank=True)  
    domain_name = fields.StringField(max_length = 500) 
    top_score = fields.StringField(max_length = 30, null=True)
    domain_info = fields.DictField(default={}) 
    domain_status = fields.StringField(max_length = 10,default="ON")
    last_used_refresh_count = fields.IntField(default=0)
    paymentmode = fields.StringField(max_length = 15, default="")    
    manual_grp_trigger = fields.StringField(max_length=5, default="DONE")  # MANUAL 
    automation_email_notify_log = fields.DictField(default={})
    automation_email_switch = fields.DictField(default={}) 
    automation_email_recipients = fields.ListField(blank=True, default=[])    
    dashboard_view = fields.StringField(max_length=30, default='listview') 
    grid_sort = fields.StringField(max_length=30, default='tags')
    # DataBlue `advanced` parameter for every keyword in this project.
    # False = Lite: organic plus the non-AI rich blocks (ads, featured_snippet,
    # people_also_ask, local_results, knowledge_panel, videos).
    # True  = Advanced: the same blocks plus ai_overview, Google's AI answer.
    # ADVANCED COSTS MORE -- it carries a higher DataBlue credit weight per
    # request, and it is billed per keyword per run against the ACCOUNT'S OWN
    # key. Defaults to Lite so nobody's spend changes without them choosing it.
    serp_advanced = fields.BooleanField(default=False)
    project_automation_time = fields.DateTimeField(null=True)
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)
    updated_date = fields.DateTimeField(auto_now_add = False, auto_now = True)  
    group_call_status = fields.StringField(max_length=5,blank=False,default='COMP')  # ENGINE
    competitor_analyse_json = fields.DictField(default={})
    competitor_analyse_status = fields.StringField(max_length = 5, default='VOID') # VOID, START, SCHD, COMP, FAIL 
    non_columns = fields.ListField(blank=True, default=[])
    competitor_project_array = fields.ListField(blank=True, default=[])
    competitor_project_status = fields.StringField(max_length = 5, default='VOID') # VOID, INIT, SCHD, COMP, FAIL  
    
    # PAGE AUDIT
    gsc_track_status = fields.StringField(max_length=10, default="NA")
    gsc_last_track = fields.DateTimeField(null=True,default=datetime.utcnow) 
    gsc_site_status = fields.BooleanField(default=False) 

    # GSC ACCESS
    gsc_refresh_token = fields.StringField(default="")
    week_track_day = fields.StringField(default="Monday") 
    gsc_property = fields.StringField(default="")
    brand_keywords = fields.ListField(blank=True, default=[])

    # Stamped on every status transition, so a claim (PROC for the engine,
    # WAIT for manual refresh) carries the time it was taken and a run that
    # died mid-flight can be swept back into the pool instead of stranding
    # the project.
    call_claim_date = fields.DateTimeField(null=True)

    meta = {
        'collection': 'group',
        # Both selection predicates the engine and the manual queue run on
        # every tick.
        'indexes': [
            ('group_call_status', 'project_automation_time'),
            ('manual_grp_trigger', 'fk_user_id'),
        ],
    }

class Mainsettings(Document):
    oid = fields.ObjectIdField(db_field = '_id') 
    core_mode = fields.BooleanField(default=True) # 'True' Engine Automation refresh enabled    
    core_manual_mode = fields.BooleanField(default=True) # 'True' Engine Manual refresh enabled 
    core_manual_mail = fields.BooleanField(default=True) # 'True' Manual mail trigger once in a day 
    core_kw_research_mode = fields.BooleanField(default=True) # 'True' Keyword research is enabled
    rate_usd_inr = fields.StringField(max_length=10, default = '0.0')

    results_per_page = fields.IntField(default=50) 
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)  
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True)  
    core_refresh_time = fields.DateTimeField() 
    daily_automation_count = fields.ListField(blank=True)
    daily_demand_count = fields.ListField(blank=True) 
    manual_swap_memory = fields.ListField(blank=True)  
    automation_keyword_exceeds_mail_status = fields.StringField(max_length=10, default = '-')
    manual_keyword_exceeds_mail_status = fields.StringField(max_length=10, default = '-')

    # NEW (LIMITATION)
    proxy_maximum_load_limit = fields.IntField(default=1000)
    
    # NEW (PROXY USAGES) 
    proxy_success_count = fields.IntField(default=0) 
    proxy_exceeds_count = fields.IntField(default=0) 
    proxy_invalid_count = fields.IntField(default=0)
    proxy_reset_counter = fields.IntField(default=0)
    
    # API Keys
    
    # LLM Service Enable/Disable Settings
    chatgpt_enabled = fields.BooleanField(default=0) 
    claude_enabled = fields.BooleanField(default=0) 
    perplexity_enabled = fields.BooleanField(default=0) 
    gemini_enabled = fields.BooleanField(default=0) 

    meta = {  
        'collection': 'mainsettings'
    } 

class Accountusage(Document):   
    oid = fields.ObjectIdField(db_field = '_id') 
    fb_user_id = fields.IntField() #foriegn key
    current_plan_id = fields.IntField() 
    future_plan_id = fields.IntField()
    last_used_refresh_count = fields.IntField(default=0)  
    plan_keyword_limit = fields.IntField(default=0) 
    plan_refresh_limit = fields.IntField(default=0) 
    plan_project_limit = fields.IntField(default=1) 
    used_refresh_limit = fields.IntField(default=0)
    active_purchase_id = fields.IntField(default=0)   
    validity_from = fields.DateTimeField()
    validity_to = fields.DateTimeField()   
    status = fields.StringField(max_length = 100)
    st_purchase_id = fields.IntField(default = 0) 
    st_subscription_id = fields.StringField(max_length=50, null=True)  
    st_customer_id = fields.StringField(max_length = 100, null=True) 
    st_user_mail = fields.StringField(max_length = 100, null=True)  
    mail_max_keyword_reach = fields.StringField(max_length = 5, default='-') 
    automatic_mail_status = fields.StringField(max_length = 15, default='COMP') 
    startup_base_plan = fields.DictField(default={})
    plan_cancel_request = fields.DictField(default={})
    future_upgrade_plan = fields.DictField(default={}) 
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False) 
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True) 
    freemium_credit_usage = fields.DictField(default={}) 
    redeem_api_call_count = fields.IntField(default = 0) 
    keyword_research_searches = fields.ListField(blank=True, default=[]) #suggestion keywords 
    trial_days = fields.IntField(default=settings.TRIAL_DAYS)
    user_type = fields.StringField(max_length = 10, default="trial")  #trial, cistom, redeem, stripe, free
    st_redeem_id = fields.StringField(max_length = 100, null=True)
    plan_competitor_limit = fields.IntField(default=1)
    project_competitor_limit = fields.IntField(default=1)    
    
    # NEW
    plan_kw_research_limit = fields.IntField(default=30)  
    plan_per_day_kw_research_limit = fields.IntField(default=3)  
    used_kw_research_limit = fields.IntField(default=0)
    used_per_day_kw_research_limit = fields.IntField(default=0)  
    primary_keyword_limit = fields.IntField(default=2)
    # NEW
    gsc_token = fields.StringField(default = 'NA')
    gsc_track_status = fields.StringField(max_length=10, default="NA")
    gsc_last_track = fields.DateTimeField(null=True,default=datetime.utcnow)
    page_audit_limit = fields.IntField(default=0)
    used_page_audit_limit = fields.IntField(default=0) 

    backlink_monit_limit = fields.IntField(default=0)
    used_backlink_monit_limit = fields.IntField(default=0)

    # KEYWORD OPPORTUNITIES
    kwopportunities_limit = fields.IntField(default=0)
    used_kwopportunities_limit = fields.IntField(default=0)
    kwo_track_status = fields.StringField(max_length=10, default="NA")
    kwo_last_track = fields.DateTimeField(null=True)

    # BYOK — the backend writes these onto the SAME `accountusage` collection
    # (backend/serp/models.py Accountusage). The engine does not read them here
    # — the SERP key is read through the djongo twin, DAccountUsage — but a
    # mongoengine document class refuses to LOAD a document carrying a field it
    # does not declare, so leaving them out did not hide the columns, it made
    # every Accountusage row unloadable.
    #
    # That is not a cosmetic failure. __au_status_callback__ swallows the
    # FieldDoesNotExist and returns False, and automation_engine reads False as
    # "this account is not entitled to rank": it marks the project DROP without
    # fetching a single keyword and sets automatic_mail_status="STOP". So the
    # moment an account saved a DataBlue key — the one action BYOK requires —
    # its scheduled ranking stopped, permanently and silently. Same failure the
    # Keyword.serp_pages comment records; same rule (CLAUDE.md): two models,
    # one collection, migrate both or neither.
    serp_provider = fields.StringField(max_length=50, default="datablue")
    serp_key = fields.StringField(default="")
    serp_depth = fields.IntField(default=1)

    chatgpt_api_key = fields.StringField(default="")
    claude_api_key = fields.StringField(default="")
    perplexity_api_key = fields.StringField(default="")
    gemini_api_key = fields.StringField(default="")

    chatgpt_model = fields.StringField(max_length=60, default="")
    claude_model = fields.StringField(max_length=60, default="")
    perplexity_model = fields.StringField(max_length=60, default="")
    gemini_model = fields.StringField(max_length=60, default="")

    meta = {
        'collection': 'accountusage'
    }

class CompProject(Document): 
    # FOREIGN KEYS
    oid = fields.ObjectIdField(db_field = '_id')
    fk_user_id = fields.IntField()  
    fk_group_id = fields.IntField()

    # OTHER FIELDS
    cp_group_name = fields.StringField(max_length = 100)
    cp_domain_name = fields.StringField(max_length = 500) 
    cp_grp_trigger = fields.StringField(max_length=5, default="DONE") 
    cp_total_keyword = fields.ListField(blank=True)  

    cp_top_score = fields.StringField(max_length = 10, null=True)
    mn_top_score = fields.StringField(max_length = 10, null=True) 
    cp_activity_level = fields.ListField(blank=True)  
    mn_activity_level = fields.ListField(blank=True)  
    cp_since_position = fields.ListField(blank=True)  
    mn_since_position = fields.ListField(blank=True)  
    cp_score_meter = fields.ListField(blank=True)  
    mn_score_meter = fields.ListField(blank=True)  
    group_call_status = fields.StringField(max_length=5, default="COMP") 
    keyword_ids = fields.ListField(blank=True)

    # Auto updated when data is inserted
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)
    # Auto updated when the data is altered
    updated_date = fields.DateTimeField(auto_now_add = False, auto_now = True)

    # TABLE
    meta = {  
        'collection': 'competitor_project' 
    }

class CompKeyword(Document):
    # FOREIGN KEYS
    oid = fields.ObjectIdField(db_field = '_id') 
    fk_user_id = fields.IntField()  
    fk_group_id = fields.IntField()
    fk_keyword_id = fields.IntField()
    fk_cp_project_id = fields.IntField() 

    # OTHER FIELDS
    cp_site_url = fields.StringField()
    target = fields.StringField(null=True)
    rank = fields.ListField(blank=True, default=[]) 
    ranknow = fields.IntField(default=0)
    rank_sincestart = fields.IntField(default=0) 
    language_code = fields.StringField(max_length=8)
    featured_snippet = fields.BooleanField(default=0) 
    review = fields.BooleanField(default=0) 
    knowledge_panel = fields.BooleanField(default=0)
    ads = fields.BooleanField(default=0)
    total_rating = fields.StringField(max_length=5, blank=True,  default=None)
    total_review = fields.StringField(max_length=15, blank=True, default=None)
    snippets_details = fields.DictField(default={})  
    dayval = fields.IntField(default=0)
    weekval = fields.IntField(default=0)
    halfmonthval = fields.IntField(default=0) 
    monthval = fields.IntField(default=0) 
    daymark = fields.StringField(max_length=5, default="-")
    weekmark = fields.StringField(max_length=5, default="-")
    halfmonthmark = fields.StringField(max_length=5, default="-")
    monthmark = fields.StringField(max_length=5) 
    status_from_start = fields.StringField(max_length=5, default="-")
    comp_call_mode = fields.StringField(max_length=5, default="done")  
    auto_call_status = fields.StringField(max_length=5, default="done") 
    top_rank = fields.IntField(default=0) 
    lastranked_date = fields.DateTimeField()
    comp_call_status = fields.BooleanField(default=0)
    platform = fields.StringField(max_length=10, default="desktop")
    isocode = fields.StringField(max_length=5, default="us")
    keyword = fields.StringField()

    # Auto updated when data is inserted 
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False)
    modified_date = fields.DateTimeField() 

    # TABLE
    meta = {  
        'collection': 'competitor_keyword'   
    }

class KeywordResearch(Document): 
    oid = fields.ObjectIdField(db_field = '_id') # FOREIGN KEYS
    fk_user_id = fields.IntField()  
    fk_group_id = fields.IntField()
    search_text = fields.StringField()
    region_name = fields.StringField(max_length=50)
    region_code = fields.StringField(max_length=4, null=True)
    search_type = fields.StringField(max_length = 10, default = 'keyword') # (- / 'keyword' or 'domain') 
    planner_status = fields.StringField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE") 
    google_status = fields.StringField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE")
    ontype_status = fields.StringField(max_length = 5, default = 'VOID') # (- / "VOID", "INIT","SCHD","FAIL","DONE", "START", "STOP", "COMP")
    research_refresh_count = fields.IntField(default=0) 
    kw_ontype_array = fields.ListField(blank=True, default=[])  
    kw_related_array = fields.ListField(blank=True, default=[])
    search_results = fields.StringField(max_length=20,default="-") # Remove
    page_uuid_url = fields.StringField(default="-")
    page_uuid = fields.StringField(default="-")
    serp_json = fields.DictField(default={})
    created_date = fields.DateTimeField(auto_now_add = True, auto_now = False) 
    modified_date = fields.DateTimeField(auto_now_add = False, auto_now = True)
    
    # TABLE
    meta = {  
        'collection': 'kw_research'   
    }