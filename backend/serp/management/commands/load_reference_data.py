"""Write the Region and Language lookups every install needs.

Idempotent: safe to run on every boot, which is exactly what the container
entrypoints do. Existing rows are updated in place rather than duplicated.

This exists separately from `scripts/seed_local.py` because that script also
creates the demo account, whose credentials are published in this repository.
Disabling the demo account in production must not also empty the country list.
"""

from django.core.management.base import BaseCommand

from serp.models import Language, Region, Settings
from serp.reference_data import LANGUAGES, SEARCH_REGIONS


class Command(BaseCommand):
    help = "Create or update the Region and Language reference rows."

    def handle(self, *args, **options):
        created = 0
        for code, engine, country in SEARCH_REGIONS:
            _, was_created = Region.objects.update_or_create(
                region_code=code,
                defaults=dict(region_name=engine, region_country=country),
            )
            created += 1 if was_created else 0

        for name, code in LANGUAGES:
            Language.objects.get_or_create(
                language_name=name, defaults=dict(language_code=code)
            )

        # THE ENGINE CANNOT START WORK WITHOUT THIS ROW.
        #
        # automation_common.__ms_record__ does
        #     Settings.objects.filter(id=1).first().core_manual_mode
        # with no None check, so a missing row is an AttributeError inside the
        # engine -- an unexplained 500 on EVERY automation endpoint. Observed in
        # production on 2026-09-06: every refresh and every scheduled pass had
        # been answering 500 for hours, with nothing in any log, because the row
        # was created only by scripts/seed_local.py and production correctly
        # does not run the seed.
        #
        # Same class of bug as the regions this command already fixes: data the
        # product cannot run without, gated behind the demo switch. The model's
        # own defaults are the right values -- they are what a working install
        # has.
        _, settings_made = Settings.objects.get_or_create(id=1)

        self.stdout.write(
            "reference data ok       %d regions (%d new), %d languages, "
            "settings row %s"
            % (Region.objects.count(), created, Language.objects.count(),
               "created" if settings_made else "present")
        )
