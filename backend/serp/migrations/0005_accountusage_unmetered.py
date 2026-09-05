from django.db import migrations, models

# Keep in step with serp.models.UNMETERED.
UNMETERED = 1_000_000_000

_FIELDS = [
    "plan_keyword_limit", "plan_refresh_limit", "plan_project_limit",
    "plan_competitor_limit", "project_competitor_limit", "plan_kw_research_limit",
    "plan_per_day_kw_research_limit", "primary_keyword_limit",
    "page_audit_limit", "backlink_monit_limit",
]


def lift_existing(apps, schema_editor):
    """Raise the limits already stored on existing accounts.

    A changed model default only reaches rows created afterwards. Without this,
    every existing account keeps the numbers it was given -- and for
    page_audit_limit and backlink_monit_limit that number is 0, which is why
    those two features were dead on arrival for anyone but the seeded demo user.
    """
    Accountusage = apps.get_model("serp", "Accountusage")
    # Row by row, not .all().update(). djongo compiles an unfiltered queryset
    # update into `UPDATE accountusage SET ...` with no WHERE, then hands it to
    # pymongo's update_many(), which requires a filter -- so the bulk form
    # raises SQLDecodeError here rather than updating nothing.
    for row in Accountusage.objects.all():
        for f in _FIELDS:
            setattr(row, f, UNMETERED)
        row.save(update_fields=_FIELDS)


def noop(apps, schema_editor):
    # Nothing to undo: the old values were arbitrary plan numbers, and putting
    # them back would re-disable features rather than restore meaning.
    pass


class Migration(migrations.Migration):
    """Default change is state-only.

    The field alterations are wrapped in SeparateDatabaseAndState with no
    database operations: this runs on MongoDB through djongo, which cannot
    ALTER a column and raises rather than ignoring it. Mongo is schemaless, so
    a changed IntegerField default needs no storage change anyway -- only
    Django's migration state has to agree with the model. The data update is
    the part that actually matters.
    """

    dependencies = [("serp", "0004_accountusage_byok_ai_keys")]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="accountusage", name=f,
                    field=models.IntegerField(default=UNMETERED),
                ) for f in _FIELDS
            ],
            database_operations=[],
        ),
        migrations.RunPython(lift_existing, noop),
    ]
