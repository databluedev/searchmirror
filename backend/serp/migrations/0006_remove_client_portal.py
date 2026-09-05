from django.db import migrations


class Migration(migrations.Migration):
    """Drop ClientAccount, ClientToken and ClientProjects from the model state.

    State-only, deliberately. djongo cannot execute DDL -- it raises on
    AlterField and would on a table drop -- and Mongo has no schema to change
    anyway. The three collections stay in the database untouched.

    Leaving the data behind is the point rather than an oversight: the portal
    is preserved on the client-portal-archive branch, so an instance that had
    clients keeps its rows and could be restored by checking that branch out.
    Nothing reads these collections any more.
    """

    dependencies = [("serp", "0005_accountusage_unmetered")]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="ClientProjects"),
                migrations.DeleteModel(name="ClientToken"),
                migrations.DeleteModel(name="ClientAccount"),
            ],
            database_operations=[],
        ),
    ]
