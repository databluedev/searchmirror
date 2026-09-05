"""Run one rank-scheduling pass from inside the container.

The HTTP endpoint (/rank/schedule) exists for an external cron and is guarded
by CRON_TOKEN, because it is a public URL that spends provider credits. This
command is the same pass invoked as a local process, so it needs no token: an
attacker who can run manage.py already has the container.

The bundled `scheduler` service calls this; an operator who prefers their own
cron can call either.
"""

import json

from django.core.management.base import BaseCommand

from serp.rank_scheduler import run_rank_schedule


class Command(BaseCommand):
    help = "Queue projects whose daily rank run is due, and poke the engine."

    def handle(self, *args, **options):
        result = run_rank_schedule()
        # One line of JSON: the scheduler container's log is the only place an
        # operator can see whether ranking is actually happening.
        self.stdout.write(json.dumps(result))
