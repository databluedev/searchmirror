from django.db import migrations, models


class Migration(migrations.Migration):
    """Per-keyword overrides of the two DataBlue cost settings.

    Both default to None, which means "inherit". Existing rows therefore keep
    behaving exactly as they did -- pages from Accountusage.serp_depth,
    Lite/Advanced from Groups.serp_advanced -- and nothing changes what any
    account is billed until someone sets an override.
    """

    dependencies = [
        ('serp', '0010_serp_features_and_depth'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyword',
            name='serp_pages',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='keyword',
            name='serp_advanced',
            field=models.BooleanField(default=None, null=True),
        ),
    ]
