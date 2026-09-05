from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("team_management", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="teamaccount",
            name="password",
            field=models.CharField(max_length=128),
        ),
    ]
