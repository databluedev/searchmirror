import os

from django.apps import AppConfig


# A generation runs on a daemon thread, so a restart kills it with no chance to
# record anything. The staleness cutoff in views.py eventually notices, but
# "eventually" is ten minutes, and until then the editor shows a spinner for a
# job nothing is running. Reconciling once at start-up is what makes a restart
# visible immediately.
#
# Gated on a marker file rather than run unconditionally: gunicorn forks
# several workers from one master, and all of them call ready(). The first to
# arrive creates the marker and does the reconciliation; the rest see it and
# skip, so a worker respawned later in the day cannot clear a job a sibling
# worker is still running. /tmp is per container, so a restart starts clean.
_MARKER_DIR = "/tmp"


def _boot_marker():
    """A path that is stable within one container start and different after."""
    try:
        boot = int(os.stat("/proc/1").st_ctime)
    except OSError:
        boot = os.getpid()
    return os.path.join(_MARKER_DIR, ".gen_reconcile_%s" % boot)


class ContentmanagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contentmanager'

    def ready(self):
        try:
            marker = _boot_marker()
            # O_EXCL makes "create it" and "was I first" one atomic step, so
            # two workers racing here cannot both reconcile.
            try:
                os.close(os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            except FileExistsError:
                return

            from contentmanager.models import ContentPlanner

            ContentPlanner.objects.filter(gen_status__in=("QUEUED", "RUNNING")).update(
                gen_status="FAIL",
                gen_message="Generation was interrupted before it finished. You can start it again.",
                gen_claim_date=None,
                gen_content="",
            )
        except Exception:
            # Start-up bookkeeping must never stop the application booting --
            # this also runs during migrate, when the column may not exist yet.
            pass
