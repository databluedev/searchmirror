import uuid
from djongo import models


class ContentPlanner(models.Model):

    # Tracking Status
    TRACK_STATUS_CHOICES = [
        ("INIT", "Initialized"),
        ("SCHD", "Scheduled"),
        ("DONE", "Completed"),
        ("FAIL", "Failed"),
    ]

    content_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("serp.Groups", on_delete=models.CASCADE, null=True, blank=True)
    primary_keyword = models.CharField(max_length=2048)
    secondary_keywords = models.JSONField(blank=True, default=list)
    country_name = models.CharField(max_length=50, null=False, blank=False)
    region_name = models.CharField(max_length=50, null=False, blank=False)
    region_code = models.CharField(max_length=4, null=False, blank=False)
    score = models.TextField(null=True, blank=True, default="0")
    file_name = models.TextField(null=True, blank=True)
    nlp_stats = models.JSONField(blank=True, default=list)
    track_status = models.TextField(max_length=4, choices=TRACK_STATUS_CHOICES, default="INIT")  # INIT, SCHD, DONE, FAIL
    track_message = models.TextField(null=True, blank=True)

    # AI GENERATION, kept separate from track_status.
    # track_status is about the DRAFT ("has the user saved this plan"); these
    # are about one provider call. Overloading the first would make "the
    # article failed to generate" and "the draft was never saved" the same
    # value.
    #
    # gen_claim_date is stamped when a worker takes the plan. It is both the
    # claim -- a second request finding a live claim does not spend again --
    # and the staleness cutoff: a RUNNING plan whose claim is older than the
    # window belonged to a process that no longer exists, and is reported
    # interrupted rather than left spinning forever. Same idiom as the
    # engine's Keyword.call_claim_date.
    gen_status = models.CharField(max_length=12, default="", blank=True)  # "", QUEUED, RUNNING, DONE, FAIL
    gen_message = models.TextField(null=True, blank=True)
    gen_claim_date = models.DateTimeField(null=True, blank=True)
    gen_content = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "content_planner"
