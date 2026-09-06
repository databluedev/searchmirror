"""What a brand-new account meets.

Every check here is about the state an installation is in *before* anyone has
done anything: no project, no measurements, and — until this change — no
country list either.

The reference-data bug is the one worth understanding. `Region` and `Language`
are foreign lookups the add-project and add-keyword forms cannot render without.
They were created only by `scripts/seed_local.py`, which is correctly disabled
in production because it also creates an account whose password is published in
this repository. So the single switch that keeps the demo login out of
production also left every production install with an empty country dropdown
and no way to create a project at all. It was found on a real deployment on
2026-09-06, where the Region dropdown rendered a broken image and the value "0".

Reference data and demo data do not share a switch.
"""

import requests

from conftest import TIMEOUT


def test_the_country_list_is_populated(api, session, headers, auth):
    """Without this the add-project form cannot be completed, so the product is
    unusable on a fresh install however healthy every container looks."""
    user_id = auth[0]
    response = session.post(
        api + "/country_list", json={"userid": user_id}, headers=headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, response.text[:200]

    body = response.json()
    text = str(body)
    assert "india" in text.lower() or "united states" in text.lower(), (
        "the country list came back without recognisable countries. If the "
        "region table is empty, `manage.py load_reference_data` did not run -- "
        "every container entrypoint is supposed to run it on boot. A fresh "
        "install with an empty region table cannot create a project.\n\n%s"
        % text[:300]
    )


def test_every_region_names_a_google_domain():
    """`region_name` holds the GOOGLE DOMAIN, not the country.

    `/country_list` returns display names, which is its job. The invariant that
    matters is in the stored data: the add-keyword form writes `region_name`
    onto the keyword, and the engine only accepts a value beginning "google." --
    anything else silently falls back to google.com. Seeding "India" there
    searched the wrong engine while the interface said India, which is a wrong
    answer rather than an error, and no test would have caught it.
    """
    import sys
    from pathlib import Path

    backend = str(Path(__file__).parents[1] / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from serp.reference_data import SEARCH_REGIONS

    wrong = [(code, engine) for code, engine, _ in SEARCH_REGIONS
             if not engine.startswith("google.")]
    assert not wrong, (
        "%d region(s) do not name a Google domain: %s. The engine falls back to "
        "google.com for these, so the measurement would come from the wrong "
        "search engine while the interface names the right country."
        % (len(wrong), wrong)
    )
    assert len(SEARCH_REGIONS) >= 50, (
        "only %d regions defined; the product supports far more countries than "
        "that and the list has probably been truncated" % len(SEARCH_REGIONS)
    )


def test_reference_data_is_not_gated_on_the_demo_seed():
    """The two must not share a switch. If the region list is only written by
    the seed, disabling the published demo login empties the country dropdown."""
    from pathlib import Path

    root = Path(__file__).parents[1]
    reference = root / "backend" / "serp" / "reference_data.py"
    command = root / "backend" / "serp" / "management" / "commands" / "load_reference_data.py"

    assert reference.exists(), "the shared reference-data module is gone"
    assert command.exists(), "manage.py load_reference_data is gone"

    seed = (root / "backend" / "scripts" / "seed_local.py").read_text(encoding="utf-8")
    assert "from serp.reference_data import" in seed, (
        "the seed defines its own region list again. Two copies drift: the "
        "engine only accepts region_name values starting 'google.', so a "
        "divergent copy searches the wrong engine while the UI names the right "
        "country."
    )

    # Every entrypoint must run it, or a fresh install still starts empty.
    for compose in ("docker-compose.yml", "docker-compose.prod.yml",
                    "docker-compose.dokploy.yml"):
        text = (root / compose).read_text(encoding="utf-8")
        assert "load_reference_data" in text, (
            "%s does not run load_reference_data, so an install started with "
            "that file has no country list" % compose
        )


# --- the frontend side -------------------------------------------------------
#
# `private_route.js` leaves the `activegrp` cookie UNSET when the account has no
# project. That is the honest value -- it previously wrote the literal 'dmo',
# which the backend parsed as an integer and answered with a 500 on every
# screen. The comment justifying that fix states the assumption the whole design
# rests on:
#
#     "Absent is the honest value: the `if (userid && grpid)` guards those
#      callers already carry then skip the request."
#
# The assumption was false. Of 54 files that read the cookie and then call the
# API, 21 carried no such guard, so four pages called endpoints they could not
# satisfy -- two of them answering 500. The bootstrap was made honest on the
# belief that the callers were already safe; two thirds were.

import os
import re
from pathlib import Path

_APP = Path(__file__).parents[1] / "app" / "src"
ROOT_DIR = Path(__file__).parents[1]
_GUARD = re.compile(r"if\s*\(.*grpid|grpid\s*&&|&&\s*grpid|!grpid|!grpId", re.I)


def _files_that_call_with_a_project():
    out = []
    for dirpath, dirnames, filenames in os.walk(_APP):
        dirnames[:] = [d for d in dirnames if d != "node_modules"]
        for name in filenames:
            if not name.endswith(".js"):
                continue
            path = Path(dirpath) / name
            text = path.read_text(encoding="utf-8", errors="replace")
            if "get('activegrp')" not in text:
                continue
            if "axios.post" not in text and "axios.get" not in text:
                continue
            out.append((path, text))
    return out


def test_every_caller_guards_on_having_a_project():
    unguarded = sorted(
        str(path.relative_to(_APP.parents[1])).replace(os.sep, "/")
        for path, text in _files_that_call_with_a_project()
        if not _GUARD.search(text)
    )
    assert not unguarded, (
        "%d file(s) read the active-project cookie and call the API without "
        "checking a project exists:\n\n    %s\n\n"
        "With no project that cookie is unset, so the request goes out with no "
        "grpid. Some endpoints answer 500; the user sees a blank page or the "
        "API's own diagnostic in a red toast."
        % (len(unguarded), "\n    ".join(unguarded))
    )


def test_the_no_project_empty_state_is_shared():
    """One component, so the four pages cannot drift into four wordings."""
    component = _APP / "pages" / "commonComponents" / "not_ready.js"
    assert component.exists(), "the shared not-ready component is gone"

    source = component.read_text(encoding="utf-8")
    assert "emptyState" in source, (
        "the component stopped using the house emptyState block; docs/DESIGN.md "
        "defines it as micro-label, one sentence, one action, no art"
    )
    assert "axios" not in source, (
        "the empty state fetches. It is a presentation component: the caller "
        "already knows why the screen is not ready and passes the reason in."
    )

    for page in ("contentPlanner/index.js", "llmTracker/index.js",
                 "reports/index.js", "competitor/index.js"):
        text = (_APP / "pages" / page).read_text(encoding="utf-8")
        assert "NoProjectYet" in text, "%s does not render the empty state" % page
        assert "hasProject" in text, "%s does not derive whether a project exists" % page


def test_navigation_does_not_mark_every_item():
    """The rail briefly carried a "Set up" chip on every project-scoped item.

    On a new account nothing is usable, so all six rows carried the same chip --
    and a marker that applies to every item carries no information. It read as
    six faults rather than one next step, and collided with the "new" dots.

    "+ New project" is already at the top of the rail, and each page explains
    what it needs when opened. That is where the explanation belongs: at the
    point of intent, not smeared across the navigation.
    """
    # Assert on CODE, not comments: the comment in sidebar.js explains what the
    # chip used to say, and a bare substring check fails against correctly-fixed
    # code the moment somebody documents the old behaviour.
    raw = (_APP / "pages" / "commonComponents" / "sidebar.js").read_text(encoding="utf-8")
    sidebar = re.sub(r"/\*.*?\*/", "", re.sub(r"^\s*//.*$", "", raw, flags=re.M), flags=re.S)
    assert "needsProject" not in sidebar, (
        "the rail marks items again. If some items were usable and others were "
        "not, marking would inform -- but on an empty account none are, so it "
        "marks everything and says nothing."
    )
    assert "Set up" not in sidebar
    assert "useHasProject" not in sidebar, (
        "the rail is fetching the project list again for a signal it no longer "
        "renders"
    )


def test_the_capability_notice_renders_inside_a_layout_section():
    """`.layout` supplies the top padding that clears the fixed app bar. A
    notice rendered outside it sits under the bar and is clipped -- which is how
    Content Planner looked on a real deployment."""
    planner = (_APP / "pages" / "contentPlanner" / "index.js").read_text(encoding="utf-8")
    onboard = (_APP / "pages" / "contentPlanner" / "cedit_onboard.js").read_text(encoding="utf-8")

    assert "notice={" in planner, (
        "the notice is a sibling of CEditOnBoard again, outside any .layout"
    )
    assert "{notice}" in onboard and 'className="layout' in onboard, (
        "CEditOnBoard no longer renders the notice inside its layout section"
    )


def test_the_rank_key_capability_is_actually_shown():
    """`rank_tracking` existed in capabilities() from the start and was rendered
    nowhere, so an account with no DataBlue key was told it had no data rather
    than that it could not rank."""
    for page in ("widget/index.js", "serpRank/index.js"):
        text = (_APP / "pages" / page).read_text(encoding="utf-8")
        assert 'name="rank_tracking"' in text, (
            "%s does not surface the rank_tracking capability" % page
        )


def test_the_engine_settings_row_is_bootstrap_data_not_demo_data():
    """The engine cannot start work without Settings(id=1).

    `automation_common.__ms_record__` does

        Settings.objects.filter(id=1).first().core_manual_mode

    with no None check, so a missing row is an AttributeError inside the engine
    -- an unexplained 500 on EVERY automation endpoint, with nothing in any log.

    Observed in production on 2026-09-06: every scheduled pass had answered 500
    for hours and the Refresh button did the same, because the row was created
    only by `scripts/seed_local.py` and production correctly does not run the
    seed. Reproduced locally by deleting the row (500) and fixed by running the
    command (200).

    Same class as the region lookups: data the product cannot run without,
    gated behind the demo switch.
    """
    command = (ROOT_DIR / "backend" / "serp" / "management" / "commands"
               / "load_reference_data.py").read_text(encoding="utf-8")
    assert "Settings" in command, (
        "load_reference_data no longer ensures the engine's settings row, so a "
        "fresh install cannot rank anything"
    )
    assert "get_or_create(id=1)" in command, (
        "the settings row is not created idempotently on id=1, which is the id "
        "the engine looks up"
    )


def test_the_engine_reads_the_settings_row_this_command_writes():
    """Keeps the two ends honest: if the engine starts reading a different id
    or model, the command above is writing the wrong row and a fresh install
    breaks again in the same silent way."""
    engine = (ROOT_DIR / "engine" / "project" / "machine"
              / "automation_common.py").read_text(encoding="utf-8")
    assert "def __ms_record__" in engine
    body = engine.split("def __ms_record__", 1)[1].split("\ndef ", 1)[0]
    assert "'id': 1" in body or '"id": 1' in body, (
        "the engine no longer looks up id=1; load_reference_data creates that "
        "row and the two have drifted apart"
    )
