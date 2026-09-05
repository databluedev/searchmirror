from django.db import migrations, models


class Migration(migrations.Migration):
    """Move the four AI provider keys onto the per-account row.

    They were declared on `Settings`, which is a singleton read as
    `Settings.objects.filter(id=1)` -- so they were instance-wide config that
    nothing ever read. BYOK needs them per account.
    """

    dependencies = [
        ('serp', '0003_clienttoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountusage',
            name='chatgpt_api_key',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='accountusage',
            name='claude_api_key',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='accountusage',
            name='perplexity_api_key',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='accountusage',
            name='gemini_api_key',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RemoveField(model_name='settings', name='chatgpt_api_key'),
        migrations.RemoveField(model_name='settings', name='claude_api_key'),
        migrations.RemoveField(model_name='settings', name='perplexity_api_key'),
        migrations.RemoveField(model_name='settings', name='gemini_api_key'),
    ]
