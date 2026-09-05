from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("serp", "0007_auto_20260830_1920"),
        ("contentmanager", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentplanner",
            name="fk_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="serp.groups",
            ),
        ),
    ]
