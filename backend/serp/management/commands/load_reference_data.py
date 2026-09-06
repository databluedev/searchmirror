"""Write the Region and Language lookups every install needs.

Idempotent: safe to run on every boot, which is exactly what the container
entrypoints do. Existing rows are updated in place rather than duplicated.

This exists separately from `scripts/seed_local.py` because that script also
creates the demo account, whose credentials are published in this repository.
Disabling the demo account in production must not also empty the country list.
"""

from django.core.management.base import BaseCommand

from serp.models import Language, Region
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

        self.stdout.write(
            "reference data ok       %d regions (%d new), %d languages"
            % (Region.objects.count(), created, Language.objects.count())
        )
