from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serp', '0007_auto_20260830_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='refreshmanual',
            name='refresh_error',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='refreshmanual',
            name='refresh_error_code',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
    ]
