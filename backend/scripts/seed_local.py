"""Seed a minimal, self-contained tenant for local Docker.

Deliberately builds only what the app needs to unlock and render:
an Accountusage row (user_type="custom" -> subscription "free", no Stripe),
one project, and a handful of keywords. No production data is copied.

Run:  docker compose exec backend python scripts/seed_local.py
Idempotent -- safe to re-run.
"""
import os
import sys
import django

# Run from anywhere: put the project root (which holds tracker/) on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker.settings")
django.setup()

from serp.reference_data import SEARCH_REGIONS  # noqa: E402  (after django.setup)

from datetime import date, timedelta          # noqa: E402
from django.apps import apps                  # noqa: E402
from django.conf import settings as django_settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

# ---------------------------------------------------------------------------
# This script creates an account whose credentials are published in
# .env.example, the README and CLAUDE.md. docker-compose runs it on EVERY
# backend start, so without a gate every deployment of the shipped compose
# file -- which is exactly what publishing this repo invites -- boots an
# internet-reachable account whose password is in its own documentation.
#
# Refuse outside development. Exit 0, not non-zero: compose chains this with
# `&&` before runserver, so failing hard here would stop the server from
# starting rather than merely skipping the seed.
# ---------------------------------------------------------------------------
SEED_ALLOWED = (
    django_settings.DEBUG
    or os.environ.get("SEED_LOCAL", "").lower() == "true"
)
if not SEED_ALLOWED:
    print("seed skipped -- DJANGO_DEBUG is off and SEED_LOCAL is not 'true'.")
    print("  This is deliberate: the seeded credentials are public.")
    print("  To seed anyway (development only): SEED_LOCAL=true")
    sys.exit(0)

EMAIL = os.environ.get("SEED_EMAIL", "admin@local.test")
# A domain that genuinely ranks for the seeded terms, so the demo shows real
# positions instead of a column of zeroes. Override with SEED_DOMAIN.
DEMO_DOMAIN = os.environ.get("SEED_DOMAIN", "semrush.com")
PASSWORD = os.environ.get("SEED_PASSWORD", "LocalDev12345")

M = apps.get_model
User = get_user_model()

user = User.objects.filter(email=EMAIL).first()
if user is None:
    # Superuser only under DEBUG, where the Django admin is a development
    # convenience. A SEED_LOCAL=true run with DEBUG off gets an ordinary
    # account: nothing in the demo needs admin, and a known-password
    # superuser is the difference between a leaked demo login and a full
    # multi-tenant compromise.
    create = (
        User.objects.create_superuser
        if django_settings.DEBUG
        else User.objects.create_user
    )
    user = create(email=EMAIL, username="admin", password=PASSWORD)
    print(f"user           created  {EMAIL}"
          f"{'  (superuser, DEBUG)' if django_settings.DEBUG else '  (regular account)'}")
else:
    print(f"user           exists   {EMAIL}")

# Region / Language are foreign lookups the keyword form depends on. They are
# NOT demo data: without them the add-project form has an empty country list and
# no project can be created at all. They therefore live in serp/reference_data.py
# and are written by `manage.py load_reference_data`, which every container
# entrypoint runs -- this seed imports the same list so the two cannot drift.
Region, Language = M("serp", "Region"), M("serp", "Language")
# region_name holds the GOOGLE DOMAIN, not the country. The add-keyword form
# stores whatever is in region_name on the keyword (`setRegion(selected.RN)`),
# and the engine's _google_domain_ only accepts a value starting "google." --
# anything else falls back to google.com. Seeding "India" here therefore
# searched the wrong engine while the UI said India.
for _code, _engine, _country in SEARCH_REGIONS:
    Region.objects.update_or_create(
        region_code=_code,
        defaults=dict(region_name=_engine, region_country=_country),
    )
region = Region.objects.get(region_code="in")
# Keyed on language_name, NOT language_code: the form submits the bracketed
# label "(English)" while other code looks up "English", so both rows exist and
# share code "en". Keying on the code would match two rows and raise
# MultipleObjectsReturned on every boot.
language, _ = Language.objects.get_or_create(
    language_name="English", defaults=dict(language_code="en")
)
Language.objects.get_or_create(
    language_name="(English)", defaults=dict(language_code="en")
)
print(f"region/lang    ok       {region.region_name} / {language.language_name}")

# The gate: userPaymode() returns "free" for user_type="custom", which is what
# lifts the /pricing redirect. Everything else here is quota headroom.
Accountusage = M("serp", "Accountusage")
usage, created = Accountusage.objects.get_or_create(
    fb_user_id=user.id,
    defaults=dict(
        user_type="custom",
        status="active",
        plan_keyword_limit=1000,
        plan_project_limit=50,
        plan_refresh_limit=1000,
        plan_competitor_limit=25,
        project_competitor_limit=10,
        plan_kw_research_limit=100,
        plan_per_day_kw_research_limit=25,
        primary_keyword_limit=100,
        page_audit_limit=50,
        backlink_monit_limit=50,
        validity_from=date.today(),
        validity_to=date.today() + timedelta(days=365),
        trial_days=0,
    ),
)
if not created and usage.user_type != "custom":
    usage.user_type = "custom"
    usage.save(update_fields=["user_type"])
print(f"accountusage   {'created' if created else 'exists '}  user_type={usage.user_type}")

Groups = M("serp", "Groups")
project, created = Groups.objects.get_or_create(
    fk_user_id=user.id,
    group_name="Local Demo Project",
    defaults=dict(domain_name=DEMO_DOMAIN, domain_status="active", paymentmode="custom"),
)
print(f"project        {'created' if created else 'exists '}  {project.group_name} (id={project.id})")

GroupSetting = M("serp", "GroupSetting")
# widget_handle must be set explicitly. The model defaults it to [] and the
# seed is the only creator here, so without this the demo project boots with
# an EMPTY dashboard -- the first screen a `docker compose up` visitor sees.
# These three are the dashboard the product actually ships (serp/keyword.py:139
# gives real projects the same set): the visibility score, cannibalisation, and
# competitors. The five that used to sit alongside them restated the /projects
# row and were removed.
GroupSetting.objects.get_or_create(
    fk_user_id=user.id,
    fk_group_id=project.id,
    defaults=dict(overview_switch=True, widget_handle=["SS", "CW", "CZ"]),
)

# Several views dereference Usersettings without a None check.
Usersettings = M("serp", "Usersettings")
_, c = Usersettings.objects.get_or_create(fb_user_id=user.id)
print(f"usersettings   {'created' if c else 'exists '}")

# serp/serializers.py:529 does `"refresh_time" in refreshData` without a None
# guard, so a project with no Refreshmanual row makes /baseauth 500. Seed one.
Refreshmanual = M("serp", "Refreshmanual")
from django.utils import timezone  # noqa: E402

_, c = Refreshmanual.objects.get_or_create(
    fb_user_id=user.id,
    fk_group_id=project.id,
    defaults=dict(refresh_type="auto", refresh_status="done", refresh_time=timezone.now()),
)
print(f"refreshmanual  {'created' if c else 'exists '}  (guards /baseauth)")

Keyword = M("serp", "Keyword")
# rank is a JSON list of daily positions, newest last. The dashboard
# serializer slices it and calls .date() on lastranked_date, so a keyword
# with no history makes /dashservice 500 -- seed real values, not blanks.
SEEDS = [
    ("seo rank tracker",            "desktop", [14, 12, 11, 9, 8]),
    ("keyword position checker",    "desktop", [23, 21, 22, 19, 18]),
    ("serp tracking tool",          "mobile",  [7, 6, 6, 5, 4]),
    ("backlink monitoring",         "desktop", [45, 41, 38, 36, 31]),
    ("competitor keyword analysis", "mobile",  [62, 58, 55, 51, 49]),
    ("local rank tracking",         "desktop", [3, 3, 2, 2, 1]),
]
made = 0
now = timezone.now()
for text, platform, history in SEEDS:
    keyword_obj, c = Keyword.objects.get_or_create(
        keyword=text,
        fk_user_id=user.id,
        fk_group_id=project.id,
        defaults=dict(
            site_url=DEMO_DOMAIN,
            target=DEMO_DOMAIN,
            platform=platform,
            region=region.region_name,
            isocode=region.region_code,
            language=language.language_name,
            language_code=language.language_code,
            # "domain (Country)" — /getsetting parses this shape; a bare country name
            # used to make it 500 (now guarded, but seed the real format anyway)
            location="google.co.in (India)",
            auto_call_status="avail",   # CharField
            manual_call_status=False,   # BooleanField, not a status string
            rank=history,
            ranknow=history[-1],
            top_rank=min(history),
            lastranked_date=now,
            # Search volume needs a real provider (Google Ads is planned but is
            # not part of the open-source runtime yet). Never seed a plausible
            # number that users could mistake for measured data.
            search_volume="-",
            dayval=history[-2] - history[-1],
            weekval=history[0] - history[-1],
            monthval=history[0] - history[-1],
            halfmonthval=history[0] - history[-1],
            daymark="up" if history[-1] < history[-2] else "down",
            weekmark="up" if history[-1] < history[0] else "down",
            monthmark="up" if history[-1] < history[0] else "down",
            halfmonthmark="up" if history[-1] < history[0] else "down",
            status_from_start="up" if history[-1] < history[0] else "down",
        ),
    )
    if not c and keyword_obj.search_volume != "-":
        keyword_obj.search_volume = "-"
        keyword_obj.save(update_fields=["search_volume"])
    made += c
print(f"keywords       {made} created, {Keyword.objects.filter(fk_user_id=user.id).count()} total")

print()
print("done -- sign in at http://127.0.0.1:3001")
print(f"  {EMAIL} / {PASSWORD}")

# The Settings table ships empty -- no migration or fixture creates a row. Every
# read does `SettingsData.core_manual_mode if SettingsData else False`, so with no
# row the engine reads as OFF and the UI reports "Manual refresh is currently
# disabled". The field's own default is 1; it just never gets instantiated.
Settings = apps.get_model("serp", "Settings")
settings_row, made = Settings.objects.get_or_create(id=1)
print("  Settings row", "created" if made else "exists", "| core_manual_mode =", settings_row.core_manual_mode)
