import binascii
import os

# Tracker meters nothing. Under BYOK the user pays DataBlue for every SERP call
# and their AI provider for every completion, so a "plan limit" would be
# Tracker capping spend it does not receive. The ~100 limit checks scattered
# through the backend are left in place and compare against this instead --
# rewriting each of them would have been a hundred chances to miss one and
# leave a feature silently capped, which is how page audit and backlink
# manager shipped switched off at 0.
UNMETERED = 1_000_000_000


from djongo import models
from account.models import Account
from django.conf import settings
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password

# from django.dispatch import receiver
# from django.db.models.signals import post_delete, post_save


# DELETE THE SITE KEYWORDS RECORDS FOR EVERY MONTH BASED ON DATE.
class SiteKeywords(models.Model):
    domain = models.CharField(max_length=100, null=True)
    keyword_list = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "site_keywords"


class GroupSetting(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)  # foriegn key
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    overview_switch = models.BooleanField(default=True)  # 'True' project overview enabled
    columns_order = models.JSONField(default={"brk": 1, "1d": 1, "7d": 1, "15d": 1, "clks": 0, "imps": 0, "fts": 1, "sv": 1, "tg": 1, "dt": 1})
    widget_handle = models.JSONField(blank=True, default=[])
    dashboard_view = models.CharField(max_length=30, default="listview")
    grid_sort = models.CharField(max_length=30, default="tags")
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when the data is altered
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    w_order = models.JSONField(default={"ss": [0, 0], "to": [1, 0], "tp": [0, 1], "cw": [1, 1], "tk": [0, 2], "dk": [1, 2], "fk": [0, 3], "cz": [1, 3], "imk": [0, 4], "dck": [1, 4]}, blank=True)
    wl_report_image = models.JSONField(blank=True, default={})
    wl_rprt_sttngs = models.JSONField(blank=True, default=[])

    # GA start
    ga_refresh_token = models.TextField(default="")
    ga_property = models.TextField(default="")
    week_track_day = models.TextField(default="Monday")

    # site platform
    site_platform = models.TextField(default="")

    class Meta:
        db_table = "groupsettings"


# class GrpKwSuggestions(models.Model):
#     fk_group = models.ForeignKey('Groups', on_delete=models.CASCADE)
#     region_name = models.CharField(max_length=20)
#     region_code = models.CharField(max_length=8, null=True)
#     searchvolume_country_id = models.CharField(max_length=8, null=True)
#     status = models.CharField(max_length = 5, default = "START") # START & MONTH, WAIT, COMP
#     created_date = models.DateTimeField(auto_now_add = True, auto_now = False)
#     modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)

#     class Meta:
#         db_table = "gp_keyword_suggestions"

# class GrpKwSuggestionsList(models.Model):
#     fk_gks = models.ForeignKey('GrpKwSuggestions', on_delete=models.CASCADE)
#     fk_group = models.ForeignKey('Groups', on_delete=models.CASCADE)
#     keyword = models.TextField()
#     keyword_slug = models.TextField()
#     average_volume = models.CharField(max_length = 40, default = 'init') # (- / 'value' or 'busy')
#     last_volume = models.CharField(max_length = 40, default = 'init') # (- / 'value' or 'busy')
#     comp_level = models.CharField(max_length = 10, default = '-') # (- / low or high)
#     comp_index = models.CharField(max_length = 10, default = '-') # (- / 1 - 10)
#     month_wise_volume = models.JSONField(blank=True, default=[])
#     past_months = models.JSONField(blank=True, default=[])
#     created_date = models.DateTimeField(auto_now_add = True, auto_now = False)

#     class Meta:
#         db_table = "gp_keyword_suggestions_list"


class kwNotes(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    fk_keyword = models.ForeignKey("Keyword", on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    notes = models.TextField()
    note_date = models.DateTimeField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "keyword_notes"


class clientTracker(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    client_ip = models.CharField(max_length=60, null=True)
    client_agent = models.TextField(null=True)
    time_zone = models.CharField(max_length=50, null=True)
    country_code = models.CharField(max_length=5, null=True)
    country = models.CharField(max_length=70, null=True)
    region = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    mobile = models.BooleanField(default=0)
    other_info = models.JSONField(default={})
    status = models.CharField(max_length=6, null=True)  # START, BUSY, FAIL, DONE
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    user_automation_time = models.DateTimeField(null=True)

    class Meta:
        db_table = "account_tracker"


# Brand Competitor con-questing
class brandTracker(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fb_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=50, null=True)
    region = models.CharField(max_length=100, null=True)
    isocode = models.CharField(max_length=5, default="us")
    conquestor_call_status = models.CharField(max_length=10, default="done")  # avil, busy, done, fail
    conquestor_url_list = models.JSONField(blank=True, default=[])
    conquestor_recent_list = models.JSONField(blank=True, default=[])
    conquestor_recent_date = models.DateTimeField()
    conquestor_mail_date = models.DateTimeField()
    conquestor_refresh_count = models.IntegerField(default=0)
    status = models.CharField(max_length=5, default="off")  # on, off
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "brand_conquestor"


class brandObtain(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)  # Foreign Key
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)  # Foreign Key
    bkeyword = models.TextField()
    # brkeyword = models.TextField()
    isocode = models.CharField(max_length=5, default="us")
    language_code = models.CharField(max_length=8, null=True)
    frequency = models.IntegerField(default=1)
    report_format = models.JSONField(blank=True, default=["csv"])
    ads = models.IntegerField(default=0)  # 0->not found, 1-> found, 2->your ad found
    brand_call_status = models.CharField(max_length=10, default="INIT")  # INIT,SCHD,FAIL,DONE
    serp_json = models.JSONField(default={})
    urls = models.JSONField(blank=True, default=[])
    brand_recent_date = models.DateTimeField()
    brand_mail_date = models.DateTimeField()
    brand_ads_list = models.JSONField(blank=True, default=[])
    input_json = models.JSONField(default={})
    page_uuid_url = models.TextField(default="-")
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "brand_acquisition"


# Create your models here.
class Header(models.Model):
    header = models.CharField(max_length=20)
    countlist = models.JSONField(blank=True, default=[])
    diffval = models.IntegerField(default=0)
    markval = models.CharField(max_length=5)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    updated_date = models.DateField()

    class Meta:
        db_table = "header"


class Keyword(models.Model):
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
    # PER-KEYWORD OVERRIDES OF THE TWO COST SETTINGS.
    # None means inherit, and is NOT the same fact as an explicit value that
    # happens to match the default -- clearing an override has to be
    # expressible, so neither field may use a real value as its "unset".
    #   serp_pages    inherits Accountusage.serp_depth (result pages per query)
    #   serp_advanced inherits Groups.serp_advanced    (Lite / Advanced)
    # Both multiply what a check costs on the account's own DataBlue key: pages
    # bills one request per page, advanced bills each request at a higher credit
    # weight. Precedence is keyword-then-default, one direction, never merged.
    serp_pages = models.IntegerField(null=True, default=None)
    serp_advanced = models.BooleanField(null=True, default=None)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE, default=1)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    tags = models.JSONField(blank=True, default=[])
    tagcount = models.IntegerField(default=0)
    rank = models.JSONField(blank=True, default=[])
    ranknow = models.IntegerField(default=0)
    rank_sincestart = models.IntegerField(default=0)
    # task_id = models.CharField(max_length=25)
    search_results = models.CharField(max_length=50, default="-")
    search_volume = models.CharField(max_length=50, default="init")
    featured_snippet = models.BooleanField(default=0)
    review = models.BooleanField(default=0)
    knowledge_panel = models.BooleanField(default=0)
    ads = models.BooleanField(default=0)
    total_rating = models.CharField(max_length=5, blank=True, default="")
    total_review = models.CharField(max_length=15, blank=True, default="")
    snippets_details = models.JSONField(default={})
    # Tri-state SERP feature record written by the engine
    # (engine/project/machine/parser_json.py extract_serp_features).
    # {} means the keyword was never measured for SERP features -- which is NOT
    # the same fact as a block measured and found absent. featured_snippet /
    # knowledge_panel / ads above are two-state and cannot express that
    # difference; read this field when the distinction matters and never infer
    # an absence from a False boolean.
    serp_features = models.JSONField(default={})
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField()
    # lastranked_date = models.DateField()
    lastranked_date = models.DateTimeField()
    dayval = models.IntegerField(default=0)
    weekval = models.IntegerField(default=0)
    monthval = models.IntegerField(default=0)
    halfmonthval = models.IntegerField(default=0)
    daymark = models.CharField(max_length=5)
    weekmark = models.CharField(max_length=5)
    monthmark = models.CharField(max_length=5)
    halfmonthmark = models.CharField(max_length=5, default="-")
    status_from_start = models.CharField(max_length=5)
    isocode = models.CharField(max_length=5)
    favour = models.IntegerField(default=0)
    auto_refresh_count = models.IntegerField(null=True, blank=True, default=0)
    strict_refresh_count = models.IntegerField(null=True, blank=True, default=0)
    manual_call_status = models.BooleanField(default=0)
    manual_call_mode = models.CharField(max_length=6, default="done")
    manual_task_allocation = models.CharField(max_length=15, default="-")
    updated_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    keyword_alias = models.TextField(default="")
    page_uuid_url = models.TextField(default="-")
    page_uuid = models.TextField(default="-")
    top_rank = models.IntegerField(default=0)
    cannibalisation = models.JSONField(blank=True, default=[])
    cannibalisation_mail_status = models.CharField(max_length=5, default="-")
    keyword_snippet = models.JSONField(default={"tdy": {}, "best": {}})
    # "avail", not "done" -- this is the writer's default, and the engine is the
    # reader. The two projects share this collection and disagreed: mongoengine
    # defaults it 'avail' (engine/project/machine/models.py:130) while this,
    # the side that actually creates keywords, defaulted "done". The backend
    # wins, so every keyword ever created was born terminal.
    #
    # That broke scheduled ranking twice over, independently:
    #   1. the scheduled selector reads auto_call_status__ne="done", so a new
    #      keyword was invisible to it; and
    #   2. automation_engine.py:167 skips the whole fetch when done == all, so
    #      a group of brand-new keywords looked already-complete and was closed
    #      as COMP without a single provider request.
    # Neither surfaced as an error -- the rank graph simply stayed flat.
    #
    # backend/scripts/seed_local.py:178 already passed "avail" explicitly,
    # which is what a keyword awaiting its first check actually is.
    auto_call_status = models.CharField(max_length=5, default="avail")
    manual_task_count = models.IntegerField(default=0)

    # PAGE AUDIT
    gsc_clicks = models.CharField(max_length=15, blank=True, default="0")
    gsc_impressions = models.CharField(max_length=15, blank=True, default="0")
    gsc_clicks_last_week = models.CharField(max_length=15, blank=True, default="0")
    gsc_impressions_last_week = models.CharField(max_length=15, blank=True, default="0")
    gsc_ctr = models.CharField(max_length=15, blank=True, default="0")
    gsc_position = models.CharField(max_length=15, blank=True, default="0")

    class Meta:
        db_table = "keyword"

    # def __str__(self):
    #     return str(self._id)
    # @property
    # def getrankstatistics(self):
    #     return self.keyword
    # test_name = computed_property.ComputedCharField(max_length=3 * 64, compute_from='getrankstatistics')


class Groups(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)  # foriegn key
    group_name = models.CharField(max_length=100)
    strict_refresh_switch = models.BooleanField(default=True)  # 'True' Group refresh enabled
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
    paymentmode = models.CharField(max_length=15, default="")
    manual_grp_trigger = models.CharField(max_length=5, default="DONE")
    automation_email_notify_log = models.JSONField(default={})
    automation_email_switch = models.JSONField(default={})
    automation_email_recipients = models.JSONField(blank=True, default=[])
    dashboard_view = models.CharField(max_length=30, default="listview")
    grid_sort = models.CharField(max_length=30, default="tags")
    # DataBlue `advanced` parameter for every keyword in this project.
    # False = Lite: organic results plus the non-AI rich blocks (ads,
    #         featured_snippet, people_also_ask, local_results,
    #         knowledge_panel, videos, related_searches).
    # True  = Advanced: the same blocks plus ai_overview, Google's AI answer.
    # ADVANCED COSTS MORE. It carries a higher DataBlue credit weight per
    # request and is billed per keyword per run against the account's own key,
    # so turning it on raises the cost of every scheduled run for this project.
    # Defaults to Lite; nothing raises a user's spend without them choosing it.
    # Pages-per-keyword is a separate per-account multiplier
    # (Accountusage.serp_depth) and the two compound.
    serp_advanced = models.BooleanField(default=False)
    project_automation_time = models.DateTimeField(null=True)
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    group_call_status = models.CharField(max_length=5, default="COMP")
    competitor_analyse_json = models.JSONField(default={})
    competitor_analyse_status = models.CharField(max_length=5, default="VOID")  # VOID, START, SCHD, COMP, FAIL
    competitor_project_array = models.JSONField(blank=True, default=[])
    competitor_project_status = models.CharField(max_length=5, default="VOID")  # VOID, START, SCHD, COMP, FAIL

    # PAGE AUDIT
    gsc_track_status = models.CharField(max_length=10, default="NA")
    gsc_last_track = models.DateTimeField(null=True, default=datetime.utcnow)
    gsc_site_status = models.BooleanField(default=False)

    # GSC ACCESS
    gsc_refresh_token = models.TextField(default="")
    gsc_property = models.TextField(default="")

    # BRAND KEYWORDS
    brand_keywords = models.JSONField(blank=True, default=[])

    # check and remove
    non_columns = models.JSONField(blank=True, default=[])

    def __str__(self):
        return self.group_name

    class Meta:
        db_table = "group"


class Region(models.Model):
    region_name = models.CharField(max_length=30)
    region_code = models.CharField(max_length=3)
    region_country = models.CharField(max_length=100)
    searchvolume_country_id = models.CharField(max_length=100, default="")
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.region_name

    class Meta:
        db_table = "region"


class Language(models.Model):
    language_name = models.CharField(max_length=100)
    language_code = models.CharField(max_length=10)
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.language_name

    class Meta:
        db_table = "language"


# feedback
class Feedback(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    user_name = models.CharField(max_length=30)
    message = models.TextField()
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.user_name

    class Meta:
        db_table = "feedback"


# Report
class Report(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    group_name = models.CharField(max_length=100)
    recipient = models.CharField(max_length=100)
    frequency = models.IntegerField()
    # last_delivery = models.DateTimeField()
    last_delivery = models.DateTimeField(null=True, blank=True)
    next_delivery = models.DateTimeField()
    report_format = models.JSONField(blank=True, default=["CSV"])
    # new
    white_label = models.CharField(max_length=100, blank=True)

    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when the data is altered
    updated_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    schedule_mode = models.CharField(max_length=4, default="DONE")
    instant_mode = models.CharField(max_length=4, default="INIT")

    # def __str__(self):
    # return self.fb_user
    class Meta:
        db_table = "report"


class Refreshmanual(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    refresh_type = models.CharField(max_length=15)
    refresh_status = models.CharField(max_length=15, null=True)
    refresh_time = models.DateTimeField(auto_now_add=True)
    # Why the most recent run for this project could not produce data. The
    # engine force-clears manual_call_status on every failure path, so
    # refresh_status and the running-keyword count reach the same terminal
    # values for a total success and a total failure -- the UI reported
    # "SERP Data loaded successfully" when every keyword had failed. Written
    # by whichever side detected the failure, cleared when a run is queued,
    # and returned by /refreshstatus as `err` / `errc`.
    refresh_error = models.TextField(blank=True, default="")
    refresh_error_code = models.CharField(max_length=32, blank=True, default="")
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.fk_group

    class Meta:
        db_table = "manualrefresh"


class Subscriptionplans(models.Model):
    plan_name = models.CharField(max_length=100)
    price = models.IntegerField(default=0)
    plan_keyword_limit = models.IntegerField(default=0)
    plan_project_limit = models.IntegerField(default=1)
    plan_refresh_limit = models.IntegerField(default=0)
    plan_competitor_limit = models.IntegerField(default=0)
    plan_research_limit = models.IntegerField(default=0)
    daily_research_limit = models.IntegerField(default=0)
    plan_primary_list_limit = models.IntegerField(default=0)
    plan_duration_label = models.CharField(max_length=10, default="month")
    stripe_price_key = models.CharField(max_length=100, null=True)
    plan_type = models.CharField(max_length=100, default="free")  # (free / subscription)
    plan_validity = models.IntegerField(default=30)  # default = 30
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    currency_mode = models.CharField(max_length=5, default="USD")
    currency_sym = models.CharField(max_length=3, default="$")
    currency_order = models.IntegerField(default=0)
    plan_more = models.CharField(max_length=10, default="INSTANT")  # (INSTANT / REGULAR)
    visible = models.BooleanField(default=0)
    org_price = models.IntegerField(default=0)
    plan_audit_limit = models.IntegerField(default=0)
    plan_backlink_limit = models.IntegerField(default=0)

    class Meta:
        db_table = "subscriptionplans"


class Accountusage(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    current_plan_id = models.IntegerField()
    future_plan_id = models.IntegerField()
    last_used_refresh_count = models.IntegerField(default=0)
    plan_keyword_limit = models.IntegerField(default=UNMETERED)
    plan_refresh_limit = models.IntegerField(default=UNMETERED)
    plan_project_limit = models.IntegerField(default=UNMETERED)
    used_refresh_limit = models.IntegerField(default=0)
    validity_from = models.DateField()
    validity_to = models.DateField()
    status = models.CharField(max_length=100)
    st_purchase_id = models.IntegerField(default=0)
    st_subscription_id = models.CharField(max_length=50, null=True)
    st_customer_id = models.CharField(max_length=100, null=True)
    st_user_mail = models.CharField(max_length=100, null=True)
    mail_max_keyword_reach = models.CharField(max_length=5, default="-")
    automatic_mail_status = models.CharField(max_length=15, default="COMP")  # VOID, START, SCHD, COMP, FAIL
    startup_base_plan = models.JSONField(default={})
    plan_cancel_request = models.JSONField(default={})
    future_upgrade_plan = models.JSONField(default={})
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    freemium_credit_usage = models.JSONField(default={})
    redeem_api_call_count = models.IntegerField(default=0)
    keyword_research_searches = models.JSONField(blank=True, default=[])  # suggestion keywords
    trial_days = models.IntegerField(default=settings.TRIALDAYS)
    user_type = models.CharField(max_length=10, default="trial")  # Trial, Free(pre user), Parcial, Redeem, Stripe
    st_redeem_id = models.CharField(max_length=100, null=True)
    plan_competitor_limit = models.IntegerField(default=UNMETERED)
    project_competitor_limit = models.IntegerField(default=UNMETERED)

    # NEW
    plan_kw_research_limit = models.IntegerField(default=UNMETERED)
    plan_per_day_kw_research_limit = models.IntegerField(default=UNMETERED)
    used_kw_research_limit = models.IntegerField(default=0)
    used_per_day_kw_research_limit = models.IntegerField(default=0)
    primary_keyword_limit = models.IntegerField(default=UNMETERED)

    # PAGE AUDIT
    gsc_token = models.TextField(default="NA")
    gsc_track_status = models.CharField(max_length=10, default="NA")
    gsc_last_track = models.DateTimeField(null=True, default=datetime.utcnow)
    page_audit_limit = models.IntegerField(default=UNMETERED)
    used_page_audit_limit = models.IntegerField(default=0)

    # BACKLINK MANAGER
    backlink_monit_limit = models.IntegerField(default=UNMETERED)
    used_backlink_monit_limit = models.IntegerField(default=0)

    # BYOK - per-account SERP provider credentials.
    # serp_key holds a token from serp.keycrypto.encrypt_key(), never the raw
    # key.  Read it back with shared.keycrypto.decrypt_key().
    serp_provider = models.CharField(max_length=50, default="datablue")
    serp_key = models.TextField(blank=True, default="")
    serp_depth = models.IntegerField(default=1)  # result pages per query; each page costs a credit

    # BYOK - per-account AI provider keys, used by Geo Citations.
    # These four previously sat on the global `Settings` singleton, so they
    # could never be per-account; nothing read them and every account's
    # analysis billed the operator's instance key. Same envelope as serp_key:
    # shared.keycrypto tokens, never raw keys.
    chatgpt_api_key = models.TextField(blank=True, default="")
    claude_api_key = models.TextField(blank=True, default="")
    perplexity_api_key = models.TextField(blank=True, default="")
    gemini_api_key = models.TextField(blank=True, default="")

    # Per-account model choice for each provider (Geo Citations). Blank means
    # use the instance default (the provider's *_MODEL env var). Lets a BYOK
    # account pick, e.g., gpt-4o over gpt-4o-mini, without an operator env change.
    chatgpt_model = models.CharField(max_length=60, blank=True, default="")
    claude_model = models.CharField(max_length=60, blank=True, default="")
    perplexity_model = models.CharField(max_length=60, blank=True, default="")
    gemini_model = models.CharField(max_length=60, blank=True, default="")

    class Meta:
        db_table = "accountusage"


class Settings(models.Model):
    core_mode = models.BooleanField(default=1)
    core_manual_mode = models.BooleanField(default=1)  # Maintenance mode Wizard, add project & keyword page
    core_manual_mail = models.BooleanField(default=1)
    results_per_page = models.IntegerField(default=50)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    core_refresh_time = models.DateField(auto_now_add=True)
    automation_keyword_exceeds_mail_status = models.CharField(max_length=10, default="-")
    manual_keyword_exceeds_mail_status = models.CharField(max_length=10, default="-")
    daily_automation_count = models.JSONField(blank=True, default=[])
    daily_demand_count = models.JSONField(blank=True, default=[])
    rate_usd_inr = models.CharField(max_length=10, default="0.0")
    core_kw_research_mode = models.BooleanField(default=1)  # Maintenance mode for keyword research

    # new felid
    proxy_maximum_load_limit = models.IntegerField(default=1000)
    proxy_success_count = models.IntegerField(default=0)
    proxy_exceeds_count = models.IntegerField(default=0)
    proxy_invalid_count = models.IntegerField(default=0)
    proxy_reset_counter = models.IntegerField(default=0)

    # API Keys
    
    # LLM Service Enable/Disable Settings
    chatgpt_enabled = models.BooleanField(default=True)
    claude_enabled = models.BooleanField(default=True)
    perplexity_enabled = models.BooleanField(default=True)
    gemini_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "mainsettings"


class Usersettings(models.Model):
    fb_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    demo_view = models.CharField(max_length=15, default="visible")
    skip_status = models.CharField(max_length=15, default="off")
    # Auto updated when data is inserted
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    email_daily_routine = models.BooleanField(default=True)
    exit_last_landed_on = models.JSONField(blank=True, default=[])  # wizard, demo, dashboard, pricing-plan, project-settings
    # need to remove
    # dashboard_view = models.CharField(max_length=30, default = 'listview')
    external_reviews = models.JSONField(default={})
    default_pay_currency = models.CharField(max_length=5, null=True)

    columns_order = models.JSONField(default={"brk": 1, "1d": 1, "7d": 1, "15d": 1, "clks": 0, "imps": 0, "fts": 1, "sv": 1, "tg": 1, "dt": 1})
    personal_address = models.JSONField(default={})
    billing_address = models.JSONField(default={})
    billing_switch = models.BooleanField(default=0)

    # check and remove
    non_columns = models.JSONField(blank=True, default=[])

    def __str__(self):
        return self.fb_user

    class Meta:
        db_table = "usersettings"


class Userregistrationtoken(models.Model):
    email = models.EmailField(max_length=150, unique=True)
    reg_key = models.CharField(max_length=64, default="")
    ip_address = models.GenericIPAddressField(default="")
    user_agent = models.CharField(max_length=256, default="")
    reg_status = models.CharField(max_length=30, default="")
    # Auto updated when data is inserted
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    # def __str__(self):
    #     return self.email
    class Meta:
        db_table = "user_registration_token"


class searchvolumes(models.Model):
    keyword = models.TextField()
    keyword_slug = models.TextField()
    region_name = models.CharField(max_length=20)
    region_code = models.CharField(max_length=8, null=True)
    searchvolume_country_id = models.CharField(max_length=8, null=True)
    average_volume = models.CharField(max_length=100, default="init")  # (- / '540' or 'busy')
    comp_level = models.CharField(max_length=10, default="-")  # (- / low or high)
    comp_index = models.CharField(max_length=10, default="-")  # (- / 1 - 10)
    last_update_volume = models.CharField(max_length=20, default="new")  # (- / 'last update month')
    status = models.CharField(max_length=10, default="new")  # (- / 'done','month','not','fail')
    month_wise_volume = models.JSONField(blank=True, default=[])
    past_months = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "search_volumes"


class Referralprogram(models.Model):
    userid = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    ref_id = models.IntegerField(default=0)
    visitors_count = models.JSONField(default={})
    reguserid = models.JSONField(blank=True, default=[])
    total_registration = models.IntegerField(default=0)
    claim_registration = models.IntegerField(default=0)
    unclaimed_registration = models.IntegerField(default=0)
    total_refreshcount = models.IntegerField(default=100)
    claim_refreshcount = models.IntegerField(default=0)
    total_keywordcount = models.IntegerField(default=100)
    claim_keywordcount = models.IntegerField(default=0)
    total_projectcount = models.IntegerField(default=5)
    claim_projectcount = models.IntegerField(default=0)
    # today_visitors_count = models.IntegerField(default = 0)
    # Auto updated when data is inserted
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.ref_id

    class Meta:
        db_table = "referralprogram"


# class Paymentdetails(models.Model):
#     user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
#     customerid = models.CharField(max_length=100,default = "")
#     subid = models.CharField(max_length=100,default = "")
#     useremail = models.CharField(max_length=100,default = "")
#     substartdate = models.CharField(max_length=100,default = "")
#     subenddate = models.CharField(max_length=100,default = "")
#     plantype = models.CharField(max_length=100,default = "")
#     invoice = models.JSONField(default={})
#     substatus = models.CharField(max_length=50,default = "")
#     before_keyword = models.IntegerField(default = 0)
#     before_refresh = models.IntegerField(default = 0)
#     before_project = models.IntegerField(default = 0)
#     payment_starteddate = models.DateTimeField(auto_now_add = True, auto_now = False)
#     payment_stopdate = models.DateTimeField(null=True, blank=True)
#     renewal_date = models.DateTimeField(null=True, blank=True)
#     # Auto updated when data is inserted
#     modified_date = models.DateTimeField(auto_now_add = False, auto_now = True)
#     created_date = models.DateTimeField(auto_now_add = True, auto_now = False)

#     def __str__(self):
#         return self.user
#     class Meta:
#         db_table = "paymentdetails"


class Mailrecords(models.Model):
    userid = models.IntegerField(default=0)
    types = models.CharField(max_length=100, default="")
    mail_list = models.JSONField(blank=True, default=[])
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.user

    class Meta:
        db_table = "mailrecords"


# ALTERNATIVE VOLUME TABLE FOR KEYWORDS
class keywordVolume(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    fk_keyword = models.ForeignKey("Keyword", on_delete=models.CASCADE)

    # REMOVE THE BELOW FIELDS IN FUTURE - STARTS
    # keyword_details = models.JSONField(default={})  # keyword, region_name, region_code # after multi model inheritance
    keyword = models.TextField()
    keyword_slug = models.TextField()
    region_name = models.CharField(max_length=20)
    region_code = models.CharField(max_length=8, null=True)
    # REMOVE THE BELOW FIELDS IN FUTURE - ENDS

    searchvolume_country_id = models.CharField(max_length=8, null=True)
    average_volume = models.CharField(max_length=100, default="init")  # (- / '540' or 'busy')
    comp_level = models.CharField(max_length=10, default="-")  # (- / low or high)
    comp_index = models.CharField(max_length=10, default="-")  # (- / 1 - 10)
    last_update_volume = models.CharField(max_length=20, default="new")  # (- / 'last update month')
    last_month_difference = models.CharField(max_length=10, default="-")  # 'up', 'down', '-'
    status = models.CharField(max_length=10, default="new")  # (- / 'done','month','not','fail')
    month_wise_volume = models.JSONField(blank=True, default=[])
    past_months = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "keyword_volume"


# @receiver(post_save, sender=Groups)
# def update_contact_keycount(sender, instance=None, created=False, **kwargs):
#     if created:
#         user = Account.objects.filter(id=instance.fk_user_id).first()
#         grpCount = Groups.objects.filter(fk_user_id=instance.fk_user_id).count()
#         if grpCount == 1:
#             hubspot.updateContactKey(email=user.email,grpstatus="Add",name=user.username)
#             mailercloud.updateContactKey(email=user.email,grpstatus="Add",name=user.username)


# @receiver(post_delete, sender=Groups)
# def update_delete_keycount(sender, instance=None,*args,**kwargs):
#     user = Account.objects.filter(id=instance.fk_user_id).first()
#     grpCount = Groups.objects.filter(fk_user_id=instance.fk_user_id).count()
#     if grpCount == 0:
#         hubspot.updateContactKey(email=user.email,grpstatus="Delete",name=user.username)
#         mailercloud.updateContactKey(email=user.email,grpstatus="Delete",name=user.username)


class GSCWeeklyQuery(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    week_start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    week_end_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    queries = models.JSONField(blank=True, default=[])
    pages = models.JSONField(blank=True, default=[])
    overview = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_weekly_search_queries"


class GSCWeeklyResult(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_at = models.DateTimeField(auto_now_add=False, auto_now=False)
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_weekly_search_results"


class GSCMonthlyQuery(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    month_start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    month_end_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    queries = models.JSONField(blank=True, default=[])
    pages = models.JSONField(blank=True, default=[])
    overview = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_monthly_search_queries"


class GSCMonthlyResult(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_at = models.DateTimeField(auto_now_add=False, auto_now=False)
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_monthly_search_results"


class DomainTracking(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    domain = models.CharField(max_length=1000, null=True)
    da_metrics = models.JSONField(blank=True, default=[])
    dr_metrics = models.JSONField(blank=True, default=[])
    page_speed_metrics = models.JSONField(blank=True, default=[])
    message = models.TextField(null=True, blank=True)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_at = models.DateTimeField(auto_now_add=False, auto_now=False)
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "domain_trackings"


# GA Analytics data
class GA_monthly_monitor(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_start = models.DateTimeField(auto_now_add=False, auto_now=False)
    track_message = models.TextField(default="") 
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "ga_monthly_monitor"


class GA_monthly_reports(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    end_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    landing_page = models.JSONField(blank=True, default=[])
    overview = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    overview_status = models.CharField(max_length=25, default='')
    track_message = models.TextField(default="")

    class Meta: 
        db_table = "ga_monthly_report"


class GA_weekly_monitor(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_start = models.DateTimeField(auto_now_add=False, auto_now=False)
    track_message = models.TextField(default="")
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "ga_weekly_monitor"


class GA_weekly_reports(models.Model):
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    end_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    landing_page = models.JSONField(blank=True, default=[])
    overview = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    overview_status = models.CharField(max_length=25, default='')
    track_message = models.TextField(default="") 

    class Meta:
        db_table = "ga_weekly_report"
        
class GA_daily_monitor(models.Model):
    id = models.AutoField(primary_key=True)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    track_mode = models.CharField(max_length=6, default="yearly") # YEARLY, WEEKLY, MONTHLY, DAILY
    track_status = models.CharField(max_length=6, default="start") # START, BUSY, DONE, FAIL
    track_scheduled_start = models.DateTimeField(auto_now_add=False, auto_now=False)
    track_message = models.TextField(default="") 
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "ga_daily_monitor"


class GA_daily_reports(models.Model):
    id = models.AutoField(primary_key=True) 
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    end_date = models.DateTimeField(auto_now_add=False, auto_now=False) 
    landing_page = models.JSONField(blank=True, default=[])
    overview = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "ga_daily_report"


class ReportManager(models.Model):

    STATUS = (
        ("scheduled", "scheduled"),
        ("inprogress", "inprogress"),
        ("done", "done"),
        ("failed", "failed"),
    )

    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE, default=1)
    track_status = models.CharField(max_length=12, choices=STATUS, default="scheduled")
    download_link = models.TextField(default="NA")
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    delivery_status = models.BooleanField(default=False)
    site_platform = models.CharField(max_length=20, default="")

    class Meta:
        db_table = "report_manager"


class ReportSheets(models.Model):

    REPORT_TYPE = (
        ("gsc_queries", "gsc_queries"),
        ("gsc_branded_queries", "gsc_branded_queries"),
        ("gsc_non_brand_queries", "gsc_non_brand_queries"),
        ("gsc_pages", "gsc_pages"),
        ("ga_overview", "ga_overview"),
        ("ga_landing_pages", "ga_landing_pages"),
        ("keyword_ranking", "keyword_ranking"),
        ("domain_rating", "domain_rating"),
    )

    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE, default=1)
    sheet_name = models.CharField(max_length=150, blank=False, null=False)
    type = models.CharField(max_length=21, choices=REPORT_TYPE, null=True)
    metrics = models.JSONField(blank=True, default=[])
    change_units = models.JSONField(blank=True, default=[])
    duration = models.CharField(max_length=10, default="weekly")
    duration_limit = models.IntegerField(default=1)
    order_by = models.CharField(max_length=50, blank=False, null=False, default="asc")
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "report_sheets"


class TestCollection(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    record_date = models.DateField(default=None)
    landing_page = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "test_collection"


class GSCDailyResult(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE, default=1)
    track_status = models.CharField(max_length=6, default="scheduled")
    track_scheduled_at = models.DateTimeField(auto_now_add=False, auto_now=False)
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_daily_search_results"


class GSCDailyQuery(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("Groups", on_delete=models.CASCADE, default=1)
    start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    end_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    queries = models.JSONField(blank=True, default=[])
    pages = models.JSONField(blank=True, default=[])
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "gsc_daily_search_queries"

class Roles(models.Model):
    fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    role = models.CharField(max_length=30)
    modules = models.JSONField(default=dict)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "custom_role"