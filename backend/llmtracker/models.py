import uuid
from djongo import models


class LLMPrompt(models.Model):
    
    # Tracking Status
    TRACK_STATUS_CHOICES = [
        ("INIT", "Initialized"),
        ("SCHD", "Scheduled"),
        ("DONE", "Completed"),
        ("FAIL", "Failed"),
    ]

    prompt_id= models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    prompt = models.TextField()
    fk_user = models.ForeignKey("account.Account", on_delete=models.CASCADE)
    fk_group = models.ForeignKey("serp.Groups", on_delete=models.CASCADE)
    track_status = models.CharField(max_length=4, choices=TRACK_STATUS_CHOICES, default="INIT")
    track_message = models.TextField(null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_prompts"


class LLMPromptAnalytics(models.Model):
    # Model choices
    MODEL_CHOICES = [
        ("ChatGPT", "ChatGPT"),
        ("Gemini", "Gemini"),
        ("Claude", "Claude"),
        ("Perplexity", "Perplexity"),
        ("DeepSeek", "DeepSeek"),
    ]
    
    # Tracking Status
    TRACK_STATUS_CHOICES = [
        ("INIT", "Initialized"),
        ("SCHD", "Scheduled"),
        ("DONE", "Completed"),
        ("FAIL", "Failed"),
    ]

    # Sentiment choices
    SENTIMENT_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("neutral", "Neutral"),
        ("mixed", "Mixed"),
    ]
    
    analytics_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_prompt = models.ForeignKey(LLMPrompt, on_delete=models.CASCADE, related_name='analytics')
    model = models.CharField(max_length=20, choices=MODEL_CHOICES)
   
    track_status = models.CharField(max_length=4, choices=TRACK_STATUS_CHOICES, default="INIT")
    track_message = models.TextField(null=True, blank=True)
    
    # Fields for mention tracking and analysis
    position = models.IntegerField(default=0)
    is_mention = models.BooleanField(default=False, help_text="Whether this prompt is a mention")
    mention_count = models.IntegerField(default=0, help_text="Number of mentions")
    citations = models.JSONField(default=list, blank=True, help_text="List of citation URLs")
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default="neutral", help_text="Sentiment classification")
    sentiment_score = models.FloatField(default=0.0, help_text="Sentiment score (-1.0 to 1.0)")
    context_summary = models.TextField(blank=True, null=True, help_text="Summary of the context")
    response_text = models.TextField(blank=True, null=True, help_text="Full model response text")
    position_score = models.FloatField(default=0.0, help_text="How prominently the brand appears in the answer, 0..1 (earlier = higher)")

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_prompt_analytics"


class LLMCompetitor(models.Model):
    """One rival brand tracked against a project's captured model answers.

    The set exists because the models name their recommendations in prose and
    link nothing: reading rivals out of citation URLs found one brand for a
    project whose answers name roughly fifteen. See ``llmtracker.brands``.

    ``source`` is the whole curation contract. ``detected`` rows were proposed
    by the extractor from stored answers and are a suggestion; ``user`` rows
    were confirmed or typed by a person and are never overwritten by a re-scan.
    ``is_tracked`` retires a name without deleting it, so a rejected suggestion
    is not proposed again on the next run.

    Uniqueness of (group, name) is enforced in code, not a DB constraint, for
    the same reason ``LLMMetricSnapshot`` gives: djongo's unique_together
    support against MongoDB is unreliable.
    """

    SOURCE_CHOICES = [
        ("detected", "Detected from answers"),
        ("user", "Added by user"),
    ]

    competitor_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_group = models.ForeignKey("serp.Groups", on_delete=models.CASCADE, related_name="llm_competitors")
    name = models.CharField(max_length=120, help_text="Brand name as it appears in answers")
    url = models.CharField(max_length=255, blank=True, default="", help_text="Optional site, so the domain counts as a mention too")
    source = models.CharField(max_length=8, choices=SOURCE_CHOICES, default="detected")
    is_tracked = models.BooleanField(default=True, help_text="Scored against answers; false retires it without deleting")
    detected_answers = models.IntegerField(default=0, help_text="Answers this name was detected in when it was proposed")
    detected_mentions = models.IntegerField(default=0, help_text="Occurrences across those answers when it was proposed")

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_competitors"


class LLMCompetitorAnalytics(models.Model):
    """One competitor measured against one stored model answer.

    Written by re-reading ``LLMPromptAnalytics.response_text``, so adding a
    competitor scores the whole of history for it retroactively and **spends
    nothing**. Counting uses the same span-merging counter as the account's own
    brand (``views.count_merged_matches``); two definitions of "a mention"
    would make the two sides incomparable.
    """

    record_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_competitor = models.ForeignKey(LLMCompetitor, on_delete=models.CASCADE, related_name="analytics")
    fk_analytics = models.ForeignKey(LLMPromptAnalytics, on_delete=models.CASCADE, related_name="competitor_analytics")

    is_mentioned = models.BooleanField(default=False)
    mention_count = models.IntegerField(default=0, help_text="Occurrences in this answer, overlapping matches merged")
    first_index = models.IntegerField(default=-1, help_text="Character offset of the first occurrence; -1 when absent")
    position_score = models.FloatField(default=0.0, help_text="How prominently the rival appears, 0..1 (earlier = higher)")

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_competitor_analytics"


class LLMMetricSnapshot(models.Model):
    """One dated aggregate of a group's Geo Citations metrics, for trend charts.

    Upserted (one row per group per day) after each prompt run, so the page can
    show mention rate, sentiment and prominence rising or falling over time --
    the difference between a one-shot check and an actual monitor. Uniqueness of
    (group, date) is enforced in code, not a DB constraint, because djongo's
    unique_together support against MongoDB is unreliable.
    """
    snapshot_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    fk_group = models.ForeignKey("serp.Groups", on_delete=models.CASCADE, related_name="llm_snapshots")
    snapshot_date = models.DateField()
    prompts_measured = models.IntegerField(default=0)
    mention_rate = models.FloatField(default=0.0, help_text="Fraction of measured model answers that mention the brand, 0..1")
    avg_sentiment = models.FloatField(default=0.0, help_text="Mean sentiment score across mentioning answers, -1..1")
    avg_position = models.FloatField(default=0.0, help_text="Mean prominence (position_score) across mentioning answers, 0..1")
    total_citations = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_metric_snapshot"
