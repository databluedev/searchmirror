import uuid
from djongo import models
from django.conf import settings
from project.machine.submodels.accountmodels import Account 

# CGA DOMAINS
class CGADomain(models.Model):
    domain_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False) 
    target_domain = models.CharField(max_length=50)  # example.com 
    absolute_domain = models.CharField(max_length=60)  # https://example.com
    file_name = models.CharField(max_length=60)  # CLOUD OR LOCAL - ONLY FILE NAME
    track_status = models.CharField(max_length=6)  # START, COMP, FAIL
    track_message = models.TextField(null=True)
    last_track_date = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_domains"


class CGADomainCategory(models.Model):
    domain_category_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    category_name = models.CharField(max_length=30, null=True)
    category_slug = models.CharField(max_length=40, null=True)
    fk_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="categories")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_domain_categories"


class CGADomainUrl(models.Model):
    domain_url_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="urls")
    source_url = models.CharField(max_length=2048)
    traffic = models.JSONField(blank=True, default=list)
    backlink = models.JSONField(blank=True, default=list)
    keywords = models.JSONField(blank=True, default=list)
    average_rank = models.JSONField(blank=True, default=list)
    url_status = models.CharField(max_length=6, default="INIT")  # INIT, SCHD, DONE, FAIL
    last_track_date = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_domain_urls"


class CGADomainCategoryUrls(models.Model):
    domain_category_url_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False) 
    fk_domain_category = models.ForeignKey("CGADomainCategory", on_delete=models.CASCADE, related_name="categories")
    fk_domain_url = models.ForeignKey("CGADomainUrl", on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_domain_categories_urls" 


# CGA SEARCH
class CGASearch(models.Model):
    search_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_user = models.ForeignKey("Account", on_delete=models.CASCADE)
    fk_self_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="self_searches")
    fk_comp_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="comp_searches")
    search_status = models.CharField(max_length=6)  # INIT, SCHD, DONE, FAIL 
    search_message = models.TextField(null=True)
    last_track_date = models.DateTimeField(auto_now_add=True, null=True) 
    not_covered_links = models.CharField(max_length=12, default=0)
    low_perform_links = models.CharField(max_length=12, default=0)
    winning_links = models.CharField(max_length=12, default=0)
    created_date = models.DateTimeField(auto_now_add=True) 
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_search"


class CGASearchCategory(models.Model):
    search_category_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_user = models.ForeignKey("Account", on_delete=models.CASCADE) 
    fk_search = models.ForeignKey("CGASearch", on_delete=models.CASCADE, related_name="categories")
    category_name = models.CharField(max_length=30, null=True)
    category_slug = models.CharField(max_length=40, null=True)
    fk_self_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="self_categories")
    fk_comp_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE, related_name="comp_categories")
    category_status = models.CharField(max_length=6, null=True)  # INIT, SCHD, DONE, FAIL, RINIT
    metric_status = models.CharField(max_length=6, null=True)  # INIT, SCHD, DONE, FAIL 
    metric_error_message = models.TextField(null=True, blank=True) 
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_search_categories"

class CGASearchCategoryUrls(models.Model): # CATEGORY MATCHES
    search_category_url_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_user = models.ForeignKey("Account", on_delete=models.CASCADE) 
    fk_search = models.ForeignKey("CGASearch", on_delete=models.CASCADE)
    fk_domain = models.ForeignKey("CGADomain", on_delete=models.CASCADE) 
    fk_domain_url = models.ForeignKey("CGADomainUrl", on_delete=models.CASCADE) 
    fk_search_category = models.ForeignKey("CGASearchCategory", on_delete=models.CASCADE, related_name="search_categories")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True) 

    class Meta:
        db_table = "cga_search_categories_url"

class CGASearchMatch(models.Model): # URLS CATEGORY MAP

    GAPSTATUS = [
        ("NA", "NA"),
        ("NC", "NC"),  # Not Covered
        ("LP", "LP"),  # Low Performance
        ("WIN", "WIN"),  # Winnings
    ]

    search_match_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False) 
    fk_user = models.ForeignKey("Account", on_delete=models.CASCADE) 
    fk_search = models.ForeignKey("CGASearch", on_delete=models.CASCADE, related_name="matches")
    fk_search_category = models.ForeignKey("CGASearchCategory", on_delete=models.CASCADE, related_name="matches")
    source_url = models.ForeignKey("CGADomainUrl", on_delete=models.CASCADE, related_name="source_matches", null=True)
    match_url = models.ForeignKey("CGADomainUrl", on_delete=models.CASCADE, related_name="match_matches", null=True) 
    gap_status = models.CharField(max_length=12, choices=GAPSTATUS, default="NA")
    metric_status = models.CharField(max_length=6, null=True)  # INIT, SCHD, DONE, FAIL
    metric_error_message = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cga_search_matches"