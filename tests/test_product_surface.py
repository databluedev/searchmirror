"""The open-source build exposes only features backed by supported providers."""

import ast
import re
import subprocess

from pathlib import Path


ROOT = Path(__file__).parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _read_code(relative_path):
    """Source with comments removed.

    A "this string must not appear" assertion otherwise fails on a comment that
    explains why the thing was removed -- the description of the fix reads
    identically to the defect. Only whole-line // comments are stripped, so a
    URL inside a string literal is left alone.
    """
    source = re.sub(r"/\*.*?\*/", "", _read(relative_path), flags=re.S)
    return re.sub(r"(?m)^[ 	]*//.*$", "", source)


def test_unsupported_backend_modules_are_not_routed():
    urls = _read("backend/tracker/urls.py")
    for route in (
        'include("payment.urls")',
        'include("payment.redeem.urls")',
        'include("kw_research.urls")',
        'include("pageaudit.urls")',
        'include("content_gap.urls")',
    ):
        assert route not in urls


def test_unsupported_engine_modules_are_not_routed():
    urls = _read("engine/project/machine/urls.py")
    assert "automation_research_call" not in urls
    assert "project.machine.contentgap.urls" not in urls


def test_unsupported_pages_are_not_bundled_or_linked():
    routes = _read("app/src/pages/routeComponents/private_route.js")
    sidebar = _read("app/src/pages/commonComponents/sidebar.js")

    for path in (
        "/keywordresearch",
        "/manageclusters",
        "/contentaudit",
        "/pageauditoverview",
        "/pageauditerror",
        "/addauditpage",
        "/keyword/navigator",
        "/keyword/planner",
        "/contentgap",
    ):
        assert path not in routes

    for label in ("Content Audit", "Content Gap", "Keyword Research"):
        assert label not in sidebar
    assert "Competitor AI" not in sidebar
    assert "Competitors" in sidebar


def test_public_landing_only_advertises_the_supported_content_tool():
    content = _read("app/src/pages/landing/components/sections/content-tools.jsx")

    for retired_surface in (
        "DataForSEO",
        "Hugging Face",
        "Content Audit",
        "Content Gap",
    ):
        assert retired_surface not in content

    assert 'title: "Content Planner"' in content
    assert "DataBlue" in content
    assert "your AI provider key" in content


def test_dashboard_activity_and_google_setup_have_one_truthful_source():
    widget_backend = _read("backend/serp/widget.py")
    history_backend = _read("backend/serp/graph.py")
    scoring = _read("shared/scoring.py")
    capabilities = _read("backend/account/capabilities.py")
    connect_panel = _read("app/src/pages/projectSettings/components/connect_panel.js")

    assert "def activitycard" not in widget_backend
    assert "def activitycard" not in history_backend
    assert "classify_activity_level" in widget_backend
    assert "classify_activity_level" in history_backend
    # One source for the wording. `commonComponents/tool_tip.js` carried a
    # second copy of this vocabulary and was imported by nothing; it was
    # removed on 2026-09-05, so assert against the module both Django images
    # actually call.
    assert 'return "stable"' in scoring

    assert '"google_analytics": entry(' in capabilities
    assert "VITE_GSC_CLIENT_ID" in capabilities
    assert "GA_CLIENT_ID" in capabilities
    assert "GA_SECRET_ID" in capabilities
    assert 'useCapability("search_console")' in connect_panel
    assert 'useCapability("google_analytics")' in connect_panel


def test_content_plans_open_as_drafts_without_a_retired_background_worker():
    table = _read("app/src/pages/contentPlanner/components/cedit_datatable.js")
    backend = _read("backend/contentmanager/views.py")

    assert "Scheduled" not in table
    assert "Inprogress" not in table
    assert 'aria-label={`Open ${row.primary_keyword} editor`}' in table
    assert 'row.track_status === "FAIL"' in table
    assert 'user_content_plan.track_status = "DONE"' in backend
    assert "content_dir.mkdir(parents=True, exist_ok=True)" in backend


def test_content_planner_is_scoped_to_the_active_project():
    models = _read("backend/contentmanager/models.py")
    backend = _read("backend/contentmanager/views.py")
    frontend = "\n".join(
        _read(path)
        for path in (
            "app/src/pages/contentPlanner/index.js",
            "app/src/pages/contentPlanner/cedit_onboard_info.js",
            "app/src/pages/contentPlanner/cedit_editor.js",
            "app/src/pages/contentPlanner/components/cedit_search_list.js",
        )
    )

    assert 'fk_group = models.ForeignKey("serp.Groups"' in models
    assert 'required_fields = ["userid", "grpid"' in backend
    assert backend.count("fk_group_id=grpid") >= 7
    assert 'ContentPlanner.objects.filter(primary_keyword=primary_keyword.lower())' not in backend
    assert frontend.count("'grpid': grpid") >= 6


def test_geo_rerun_preserves_results_until_a_provider_succeeds():
    backend = _read("backend/llmtracker/views.py")
    frontend = _read(
        "app/src/pages/llmTracker/components/llm_run_analysis.js"
    )

    assert "def process_llm_prompts_automatically(" in backend
    assert "prompt=None" in backend
    assert "_queue_ = _queue_.filter(fk_group_id=group_id)" in backend
    assert "scheduled_prompts = scheduled_prompts.filter(fk_group_id=group_id)" in backend
    assert 'group_id = request.data.get("groupid")' in backend
    assert 'rerun = request.data.get("rerun", False)' in backend
    assert "previous_analytics = list(" in backend
    assert "pending_analytics = []" in backend
    assert "Latest analysis failed; previous results retained." in backend

    provider_loop = backend.index("for _provider_, _name_, _make_client_")
    success_guard = backend.index("if not succeeded:", provider_loop)
    replace_results = backend.index("current_analytics.delete()", success_guard)
    assert provider_loop < success_guard < replace_results

    bulk_requeue = re.search(
        r'project_prompts\.filter\(track_status="DONE"\)\.update', backend
    )
    assert bulk_requeue is None
    assert ".exclude(pk=probe_prompt.pk)" in backend

    assert 'cookies.get("activegrp")' in frontend
    assert "rerun: firstRequest" in frontend
    assert "while (remaining > 0)" in frontend
    assert "Running ${completed}/${total}" in frontend
    assert "Runs one queued prompt" not in frontend


def test_geo_new_analysis_closes_only_after_a_successful_create():
    modal = _read("app/src/pages/commonComponents/llm/llm_manage_widget.js")
    form = _read("app/src/pages/commonComponents/llm/llm_onboard_info.js")

    assert "onCreated={() => setOpen(false)}" in modal
    assert "props.onCreated?.()" in form
    success_branch = form.index('if (res.status === "true")')
    failure_branch = form.index("} else {", success_branch)
    callback = form.index("props.onCreated?.()", success_branch)
    assert success_branch < callback < failure_branch


def test_geo_delete_confirmation_names_prompts_not_keywords():
    modal = _read("app/src/pages/commonComponents/llm/llm_delete_modal.js")
    list_view = _read("app/src/pages/llmTracker/components/llm_search_list.js")

    assert "Delete selected prompts?" in modal
    assert "associated analysis and citations" in modal
    assert "delete the keywords" not in modal
    assert "Delete the selected prompts" in list_view
    assert "Delete the selected keywords" not in list_view


def test_reports_use_local_download_and_keep_oauth_types_unavailable():
    report_page = _read("app/src/pages/reports/index.js")
    ecommerce_modal = _read("app/src/pages/reports/components/eComModal.js")
    export_control = _read("app/src/pages/reports/components/export_report.js")
    backend = _read("backend/serp/widget.py")
    routes = _read("backend/serp/urls.py")

    assert 'filterMenu: "rank"' in report_page
    assert "filterMenu: 'rank'" in report_page
    assert report_page.count('value="gsc" disabled') == 1
    assert report_page.count('value="ga" disabled') == 1
    assert ecommerce_modal.count('value="gsc" disabled') == 1
    assert ecommerce_modal.count('value="ga" disabled') == 1
    assert "checked={filterMenu === \"rank\"}" in report_page
    assert "onChange={() => handleFilter(\"rank\")}" in report_page

    assert "/local_report_export" in export_control
    assert "responseType: 'blob'" in export_control
    assert "setInterval" not in export_control
    assert "window.URL.revokeObjectURL" in export_control

    assert "def local_report_export(request):" in backend
    assert 'path("local_report_export", widget.local_report_export)' in routes

    for form_path in (
        "app/src/pages/reports/sheets/rank_form.js",
        "app/src/pages/reports/eComSheets/e_com_rank_form.js",
    ):
        rank_form = _read(form_path)
        assert 'selectedMetrics: ["landing_pages", "base_ranking"]' in rank_form
        assert 'value={"average_volume"}' not in rank_form
        assert "props.handleClose()" in rank_form
        assert "var rprtValues = selectedMetrics" not in rank_form


def test_competitors_expose_real_limits_scores_and_content_opportunities():
    add_modal = _read("app/src/pages/competitor/components/competitor_list.js")
    shared_parts = _read("app/src/pages/commonComponents/parts.js")
    comparison = _read("app/src/pages/competitor/tables/competitor_tables.js")
    backend = _read("backend/competitor/views.py")
    content_form = _read("app/src/pages/contentPlanner/cedit_onboard_info.js")

    assert "projectCompetitorLimit = Math.min" in add_modal
    assert "isAtCompetitorLimit" in add_modal
    assert "disabled={isAtCompetitorLimit}" in add_modal
    assert "disabled={props.loading || props.disabled}" in shared_parts
    # The number shown beside the count must be the per-project limit, not the
    # account-wide one -- that mix-up disabled Add for every project at once.
    # Asserted on the value, not on how it is formatted.
    assert "{projectCompetitorLimit}" in add_modal
    assert '"/"+lm' not in add_modal
    assert "{lm}" not in add_modal

    assert "calculate_visibility_score" in backend
    assert "calculate_visibility_history" in backend
    assert "shared_main_ranks" in backend
    assert "shared_competitor_ranks" in backend

    assert "Ranking opportunities" in comparison
    assert "competitorOutranks" in comparison
    assert "Create content brief" in comparison
    assert "contentPlannerSeed" in comparison
    assert "contentPlannerSeed" in content_form


def test_content_editor_loads_drafts_without_legacy_nlp_stats():
    editor = _read("app/src/pages/contentPlanner/cedit_editor.js")

    assert "const nlpStats = res.data.nlp_stats || {};" in editor
    assert "const competitors = Array.isArray(nlpStats.competitors)" in editor
    assert "activeSecondaryKeywords.length / secondaryKeywords.length" in editor
    assert "usedSecondaryKeywords.length / secondaryKeywords.length" not in editor

    # The score must normalise over the components that HAVE data. Two of the
    # four read nlp_stats, which has had no writer since the background worker
    # was retired, so a fixed 4x25 total capped a perfect document at 50/100
    # and labelled it "Okay !". Summing into one running total is the shape
    # that regresses to that, so the running total is what is pinned out.
    assert "possibleScore" in editor
    assert "earnedScore / possibleScore" in editor
    assert "newContentScore" not in editor


def test_content_region_waits_for_async_options_and_tracks_parent_reset():
    region = _read("app/src/pages/contentPlanner/components/cedit_region_list.js")

    assert "const optionAvailable" in region
    assert 'value={optionAvailable ? regionValue : ""}' in region
    assert "setRegion(props.lastKwdRegion.region)" in region
    assert "console.log(props.lastKwdRegion)" not in region


def test_content_planner_uses_supported_editor_formats_and_stable_row_ids():
    editor = _read("app/src/pages/contentPlanner/cedit_editor.js")
    table = _read("app/src/pages/contentPlanner/components/cedit_datatable.js")
    geo_table = _read("app/src/pages/llmTracker/components/llm_datatable.js")
    keyword_table = _read("app/src/pages/serpRank/data_table.js")
    keyword_container = _read("app/src/pages/serpRank/serp_rank_table.js")
    keyword_grid = _read("app/src/pages/serpRank/grid_single_table.js")
    keyword_grid_table = _read(
        "app/src/pages/serpRank/gridTableComponents/trending_table.js"
    )

    assert '      "bullet",' not in editor
    assert 'keyField="content_id"' in table
    assert 'keyField="prompt_id"' in geo_table
    assert 'keyField="key"' in keyword_table
    assert 'keyField="key"' in keyword_grid_table
    assert "Array(5).fill(lstresltdata)" not in keyword_container
    assert "Array(5).fill(lstresltdata)" not in keyword_grid
    assert "createLoadingRows" in keyword_container
    assert "createLoadingRows" in keyword_grid
    assert "selectableRowDisabled={(row) => !row.KW}" in keyword_table
    assert "selectableRowDisabled={(row) => !row.KW}" in keyword_grid_table


def test_supported_runtime_has_no_retired_vendor_configuration():
    checked = {
        "backend/requirements-prod.txt": (
            "boto3", "botocore", "stripe==", "google-ads=="
        ),
        "backend/requirements.txt": (
            "boto3", "botocore", "stripe==", "google-ads=="
        ),
        "engine/requirements-prod.txt": (
            "boto3", "botocore", "huggingface", "sentence-transformers",
            "torch==", "transformers==", "nvidia-", "triton==", "selenium==",
            "cloudscraper==",
        ),
        ".env.example": (
            "DATAFORSEO_", "SCRAPINGDOG_", "STRIPE_", "HUGGING_FACE_",
            "DO_SPACES_",
        ),
    }
    for relative_path, retired_names in checked.items():
        source = _read(relative_path).lower()
        for name in retired_names:
            assert name.lower() not in source, "%s still contains %s" % (
                relative_path, name
            )


def test_active_code_has_no_retired_provider_calls():
    active_files = (
        "backend/serp/project.py",
        "backend/serp/brand_acq.py",
        "backend/serp/views.py",
        "backend/serp/urls.py",
        "backend/tracker/settings.py",
        "backend/contentmanager/views.py",
        "engine/project/machine/competitor/automation_analyse.py",
    )
    retired_names = (
        "dataforseo", "huggingface", "boto3", "digitaloceanspaces",
        "import stripe", "stripe.api_key", "googleadsclient",
    )
    for relative_path in active_files:
        source = _read(relative_path).lower()
        for name in retired_names:
            assert name not in source, "%s still calls %s" % (relative_path, name)


def test_actively_routed_modules_do_not_import_retired_sdks():
    active_files = (
        "backend/serp/brand_acq.py",
        "backend/serp/project.py",
        "backend/serp/views.py",
        "backend/contentmanager/views.py",
        "engine/project/machine/competitor/automation_analyse.py",
    )
    retired_modules = {"boto3", "stripe", "transformers", "selenium"}

    for relative_path in active_files:
        tree = ast.parse(_read(relative_path), filename=relative_path)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert not imports.intersection(retired_modules), (
            "%s imports retired SDKs: %s"
            % (relative_path, sorted(imports.intersection(retired_modules)))
        )


def test_local_seed_does_not_invent_keyword_volume():
    source = _read("backend/scripts/seed_local.py")

    assert "200 + 137 * (len(text) % 7)" not in source
    assert 'search_volume="-"' in source


def test_keyword_rank_tables_hide_volume_until_a_provider_exists():
    for relative_path in (
        "app/src/pages/serpRank/data_table.js",
        "app/src/pages/serpRank/gridTableComponents/trending_table.js",
    ):
        source = _read(relative_path)
        assert 'name: "VOLUME"' not in source, relative_path

    list_table = _read("app/src/pages/serpRank/data_table.js")
    assert ".filter(Boolean)" in list_table
    assert "columns[13]" not in list_table


def test_mobile_shell_keeps_account_actions_in_the_header():
    sidebar = _read("app/src/pages/commonComponents/sidebar.js")

    assert 'aria-label={`${displayName(props.uname)} account menu`}' in sidebar
    assert 'className="mobileProfileButton"' in sidebar
    assert 'View profile' in sidebar
    assert 'history.push("/settings/profile")' in sidebar


def test_active_account_visit_timestamps_are_timezone_aware():
    views = _read("backend/serp/views.py")

    assert views.count("update(last_home_visit=timezone.now())") == 2
    assert "modified_date=datetime.now()" not in views


def test_serp_links_use_live_google_instead_of_retired_preview_service():
    backend = _read("backend/serp/views.py")
    routes = _read("backend/tracker/urls.py")
    frontend = _read("app/src/pages/common_fun.js")

    assert '"https://www.google.com/search?"' in backend
    assert '"mode": "live"' in backend
    assert "search/results/<str:ustr>" not in routes
    assert "research/results/<str:ustr>" not in routes
    assert "export const openLiveGoogleSerp" in frontend
    assert "global.spyurl" not in _read("app/src/index.js")


def test_keyword_note_ranges_are_timezone_aware():
    graph = _read("backend/serp/graph.py")

    assert "timezone.make_aware(datetime.combine(selectdate, time.min))" in graph
    assert "timezone.make_aware(datetime.combine(selectdate, time.max))" in graph


def test_profile_has_no_local_billing_surface():
    profile = _read_code("app/src/pages/account/components/profile.js").lower()
    backend = _read("backend/serp/views.py")

    assert "billing" not in profile
    assert 'request.data["bl_adrs"]' not in backend
    assert 'request.data["bl_swt"]' not in backend


def test_active_frontend_has_no_subscription_or_pricing_gate():
    for relative_path in (
        "app/src/pages/routeComponents/private_route.js",
        "app/src/pages/projectSettings/index.js",
    ):
        source = _read(relative_path).lower()
        assert "subscription" not in source, relative_path
        assert "'/pricing'" not in source, relative_path


def test_project_recipient_editor_validates_the_same_way_on_enter_and_save():
    settings = _read("app/src/pages/projectSettings/index.js")

    assert "const EMAIL_PATTERN" in settings
    assert settings.count("!EMAIL_PATTERN.test(tag)") == 2
    assert "typeof (e)" not in settings


def test_team_management_never_renders_placeholder_people_or_roles():
    source = _read("app/src/pages/userManagement/index.js") + _read(
        "app/src/pages/userManagement/teamManagement/teamManagement.js"
    )

    assert "msvijay6661@gmail.com" not in source
    assert "Christopher Nolan" not in source
    assert "dummyRoles" not in source
    assert "useEffect(async" not in source


def test_role_actions_are_named_and_delete_copy_matches_the_target():
    roles = _read("app/src/pages/userManagement/manageRoles/manageRoles.js")
    modal = _read("app/src/pages/userManagement/components/parts.js")

    assert 'aria-label={`Edit ${row.rl} role`}' in roles
    assert 'aria-label={`Delete ${row.rl} role`}' in roles
    assert "props.mnhdr" in modal
    assert "props.subhdr" in modal
    assert "Client and its projects will be lost" not in modal


def test_role_editor_only_lists_supported_product_modules():
    source = _read("app/src/pages/userManagement/manageRoles/rolesPr.js")

    for supported in (
        "All Projects",
        "Dashboard",
        "Keywords",
        "Geo Citations",
        "Content Planner",
        "Competitors",
        "Reports",
        "Project Settings",
    ):
        assert supported in source

    for retired in (
        "Content Audit",
        "Keyword Research",
        "Backlink Manager",
        "Competitor AI",
    ):
        assert retired not in source


def test_team_role_modules_control_routes_and_navigation():
    routes = _read("app/src/pages/routeComponents/private_route.js")
    sidebar = _read("app/src/pages/commonComponents/sidebar.js")
    settings = _read("app/src/pages/projectSettings/index.js")

    assert "team_modules" in routes
    assert "allowsModule" in routes
    assert "teamModules" in sidebar
    assert "item.module" in sidebar
    assert 'const landingRoute = isTeam ? "/projects" : "/dashboard"' in routes
    assert '<Redirect from="*" to={landingRoute} />' in routes
    assert "availableTabs" in settings
    assert 'fullbasedata.ac_typ === "team"' in settings


def test_team_child_permissions_hide_dashboard_and_keyword_actions():
    helper = _read("app/src/utils/team_permissions.js")
    routes = _read("app/src/pages/routeComponents/private_route.js")
    dashboard = _read("app/src/pages/widget/index.js")
    keywords = _read("app/src/pages/serpRank/index.js")
    keyword_table = _read("app/src/pages/serpRank/serp_rank_table.js")
    keyword_detail = _read("app/src/pages/keywordOverview/index.js")
    keyword_overview = _read("app/src/pages/keywordOverview/components/overview_tab.js")
    notes = _read("app/src/pages/keywordOverview/components/kw_notes_table.js")
    roles = _read("app/src/pages/userManagement/manageRoles/rolesPr.js")

    assert "export function allowsTeamModule" in helper
    assert "export function allowsTeamAction" in helper
    assert "allowsTeamModule(fullbasedata, module)" in routes
    assert "allowsTeamAction(fullbasedata, module, action)" in routes

    # The dashboard's gate moved with the rebuild. There is no widget manager
    # and so no "Manage Widgets" action to withhold; what a team child must not
    # see now is the DATA of a module it has no permission for, which is gated
    # at module level instead. The rule is unchanged -- a child never sees what
    # its permissions exclude -- and these are the surfaces it now applies to.
    assert 'allowsTeamModule(fullbasedata, "CompAi")' in dashboard
    assert 'allowsTeamModule(fullbasedata, "LLMTracker")' in dashboard
    # No per-ACTION gate is asserted on the dashboard any more, and its absence
    # is the finding rather than an omission: the rebuilt screen has no write
    # control at all. "Add Competitor", "Re-analysis Competitor" and the drag
    # grid were the three things a child could have done here, and all three are
    # gone -- every action on the page is now a link to the screen that owns it,
    # where that screen's own permission check applies.
    #
    # So the invariant asserted instead is the one that makes per-action gating
    # unnecessary: the dashboard reads exactly one endpoint and writes nothing.
    # If a mutation ever appears here it needs its own permission check, and
    # this is what fails to say so.
    data_layer = _read("app/src/pages/widget/dashboard_data.js")
    assert data_layer.count("global.apiurl") == 1
    assert 'const OVERVIEW_URL = "/dashboard_overview";' in data_layer
    # The Connect-your-data strip left the dashboard for Settings -> Connected
    # apps, so the Settings permission is checked where the panel now lives.
    settings_page = _read("app/src/pages/projectSettings/index.js")
    assert (
        'allowsTeamAction(props.fullbasedata, "Settings", "Manage Connected Apps")'
        in settings_page
    )
    assert "canManage={canManageConnectedApps}" in settings_page
    assert 'allowsTeamAction(props.fullbasedata, "Keyword", "Add Keywords")' in keywords
    for permission in ("Manage Tag", "Manual Refresh", "Delete Keywords"):
        assert (
            'allowsTeamAction(props.fullbasedata, "Keyword", "%s")' % permission
        ) in keyword_table

    for permission in ("Manage Notes",):
        assert permission in roles
        assert (
            'allowsTeamAction(props.fullbasedata, "Keyword", "%s")' % permission
        ) in keyword_table or (
            'allowsTeamAction(props.fullbasedata, "Keyword", "%s")' % permission
        ) in keyword_detail

    assert "canSelectKeywords={canSelectKeywords}" in keyword_table
    assert "selectableRows={canSelectKeywords}" in _read(
        "app/src/pages/serpRank/data_table.js"
    )
    assert "selectableRows={canSelectKeywords}" in _read(
        "app/src/pages/serpRank/gridTableComponents/trending_table.js"
    )
    # Favourites are gone entirely -- see test_favourites_are_not_shipped.
    assert "canManageFavourites" not in keyword_table
    assert "canManageFavourites" not in keyword_detail
    assert "fullbasedata={fullbasedata}" in routes
    assert "canManageTags={canManageTags}" in keyword_detail
    assert "canManageNotes={canManageNotes}" in keyword_detail
    assert "canManageTags" in keyword_overview
    assert "props.canManage" in notes


def test_capability_lookup_failures_are_explicitly_unavailable():
    capability = _read("app/src/pages/commonComponents/capability_notice.js")
    panel = _read("app/src/pages/projectSettings/components/connect_panel.js")

    assert "CAPABILITY_LOOKUP_FAILED" in capability
    assert "all[name] || CAPABILITY_LOOKUP_FAILED" in capability
    assert "treated as available" not in capability
    # A missing capability states what is missing instead of offering an action
    # that cannot work. The panel has no Connect/Manage buttons any more -- it
    # sits directly above the OAuth flow it used to route to -- so the
    # unavailable branch is what has to be asserted.
    assert "const unavailable = !!(cap && cap.available === false)" in panel
    assert "Needs {cap.needs}" in panel
    assert "{cap.fix}" in panel


def test_keyword_notes_use_the_current_date_picker_api():
    for relative_path in (
        "app/src/pages/keywordOverview/components/kw_notes_popup.js",
        "app/src/pages/keywordOverview/components/kw_notes_table.js",
    ):
        assert "renderInput=" not in _read(relative_path)


def test_team_child_permissions_make_geo_and_content_read_only():
    geo = _read("app/src/pages/llmTracker/index.js")
    geo_header = _read("app/src/pages/llmTracker/components/llm_header.js")
    geo_list = _read("app/src/pages/llmTracker/components/llm_search_list.js")
    geo_table = _read("app/src/pages/llmTracker/components/llm_datatable.js")
    content = _read("app/src/pages/contentPlanner/index.js")
    content_header = _read("app/src/pages/contentPlanner/components/cedit_header.js")
    content_list = _read("app/src/pages/contentPlanner/components/cedit_search_list.js")
    content_table = _read("app/src/pages/contentPlanner/components/cedit_datatable.js")
    editor = _read("app/src/pages/contentPlanner/cedit_editor.js")

    assert 'allowsTeamAction(props.fullbasedata, "LLMTracker", "Manage Geo Citations")' in geo
    assert "props.canManage" in geo_header
    assert "props.canManage" in geo_list
    assert "selectableRows={props.canManage}" in geo_table

    assert 'allowsTeamAction(props.fullbasedata, "ContentPlanner", "Manage Content")' in content
    assert "props.canManage" in content_header
    assert "props.canManage" in content_list
    assert "selectableRows={props.canManage}" in content_table
    assert 'allowsTeamAction(props.fullbasedata, "ContentPlanner", "Manage Content")' in editor
    assert "readOnly={!canManageContent}" in editor


def test_team_competitor_actions_follow_each_child_permission():
    page = _read("app/src/pages/competitor/index.js")
    header = _read("app/src/pages/competitor/components/competitor_header.js")
    candidates = _read("app/src/pages/competitor/components/top_competitors.js")
    comparison = _read("app/src/pages/competitor/competitorsComparison.js")
    add_control = _read("app/src/pages/competitor/components/top_all_competiitors.js")

    assert 'allowsTeamAction(props.fullbasedata, "CompAi", "Add Competitor")' in page
    assert 'allowsTeamAction(props.fullbasedata, "CompAi", "Re-analysis Competitor")' in page
    assert "props.canAdd" in header
    assert "props.canReanalyse" in header
    assert "props.canAdd" in candidates
    assert "props.canAdd === false" in add_control
    # The dashboard's competitor panel is read-only -- it spends no credits and
    # offers no re-analysis trigger -- so there is no action there to gate. Its
    # module-level gate is asserted in
    # test_team_child_permissions_hide_dashboard_and_keyword_actions.
    for permission in ("Add Competitor", "Re-analysis Competitor", "Delete Competitor"):
        assert (
            'allowsTeamAction(props.fullbasedata, "CompAi", "%s")' % permission
        ) in comparison


def test_team_report_actions_follow_each_child_permission():
    page = _read("app/src/pages/reports/index.js")
    report_grid = _read("app/src/pages/reports/report_widget.js")
    report = _read("app/src/pages/reports/components/ecom_widget.js")

    for permission in ("Add Report", "Delete Report", "Enable Export", "Rename Report"):
        assert (
            'allowsTeamAction(props.fullbasedata, "Reports", "%s")' % permission
        ) in page
    assert "canDelete={canDeleteReports}" in page
    assert "canRename={canRenameReports}" in page
    assert "props.canDelete" in report_grid
    assert "props.canRename" in report_grid
    assert "props.canDelete" in report
    assert "props.canRename" in report


def test_team_settings_actions_follow_each_child_permission():
    settings = _read("app/src/pages/projectSettings/index.js")
    branded = _read("app/src/pages/projectSettings/components/brand_keywords.js")
    connected = _read("app/src/pages/commonComponents/connected_apps.js")
    roles = _read("app/src/pages/userManagement/manageRoles/rolesPr.js")

    for permission in (
        "Manage Recipients",
        "Manage Branded Keywords",
        "Manage Connected Apps",
    ):
        assert permission in roles
        assert (
            'allowsTeamAction(props.fullbasedata, "Settings", "%s")' % permission
        ) in settings

    assert "canManage={canManageConnectedApps}" in settings
    assert "canManage={canManageBrandedKeywords}" in settings
    assert "canManageRecipients" in settings
    assert "props.canManage" in branded
    assert "Read-only access" in branded
    assert "disabled={!props.canManage}" in connected
    assert "Read-only access" in connected


def test_shared_inputs_associate_visible_labels_with_controls():
    parts = _read("app/src/pages/commonComponents/parts.js")
    login = _read("app/src/pages/welcome/login.js")

    assert 'htmlFor={fieldId}' in parts
    assert 'aria-label={values.showPassword ? "Hide password" : "Show password"}' in parts
    assert 'id="login-email"' in login
    assert 'id="login-password"' in login


def test_react_tags_uses_current_property_names():
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "app" / "src").rglob("*.js")
    )

    assert "delimiters={" not in sources
    assert "separators={delimiters}" not in sources
    assert "const delimiters = [188, 13]" not in sources
    assert "autofocus={" not in sources


def test_keyword_competitor_filter_uses_react_dom_properties():
    source = _read("app/src/pages/keywordOverview/components/competitors_tab.js")
    assert '<div className="compfilterIcon"' in source
    assert '<div class={"compfilterIcon"}' not in source


def test_confirmation_dialogs_layer_above_workspace_modals_and_unmount():
    modal = _read("app/src/pages/commonComponents/Modals.js")
    styles = _read("app/src/assets/styles/dev_style.scss")
    notes = _read("app/src/pages/keywordOverview/components/kw_notes_view.js")

    assert "keepMounted" not in modal[modal.index("export const ModalBox"):]
    assert "onClose={props.onClose || props.handleClose}" in modal
    assert re.search(r"\.MuiModal-root\.Toggle-Modal\s*\{[^}]*z-index:\s*10000", styles, re.DOTALL)
    assert 'cancelTitle="Cancel"' in notes
    assert 'content="Are you sure you want to delete this note?"' in notes


def test_keyword_detail_icon_actions_are_keyboard_and_screen_reader_accessible():
    overview = _read("app/src/pages/keywordOverview/index.js")
    notes = _read("app/src/pages/keywordOverview/components/kw_notes_popup.js")
    tags = _read("app/src/pages/commonComponents/manage_tag.js")

    assert 'aria-label="Back to keywords"' in overview
    assert 'aria-label="Refresh this keyword"' in overview
    assert 'aria-label="Close notes"' in notes
    assert 'aria-label={`Remove ${tag} tag`}' in tags


def test_projects_page_has_no_billing_gate_and_hides_owner_actions_from_members():
    projects = _read("app/src/pages/dashboard/index.js").lower()
    header = _read("app/src/pages/dashboard/components/dashboard_header.js")

    assert "subscription" not in projects
    assert "ppl" not in projects
    assert "canManageProjects" in header


def test_active_tracking_actions_have_no_searchmirror_subscription_gate():
    active_surfaces = (
        "app/src/index.js",
        "app/src/pages/addProject/index.js",
        "app/src/pages/addProject/add_keyword.js",
        "app/src/pages/serpRank/index.js",
        "app/src/pages/serpRank/serp_rank_table.js",
        "app/src/pages/serpRank/components/project_export.js",
    )

    for relative_path in active_surfaces:
        source = _read(relative_path)
        assert "sb_s" not in source, relative_path

    index = _read("app/src/index.js")
    assert "stripetoken" not in index
    assert "redirectionUrl" not in index


def test_add_keyword_starts_the_local_rank_engine():
    tree = ast.parse(_read("backend/serp/keyword.py"))
    add_keyword = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "addkeyv3"
    )
    calls = {
        node.func.id
        for node in ast.walk(add_keyword)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "trigger_engine_manual" in calls


def test_new_keyword_rank_timestamp_is_timezone_aware():
    source = _read("backend/serp/serializers.py")
    tree = ast.parse(source)
    serializer = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "KeywordCreateSerializer"
    )
    serializer_source = ast.get_source_segment(source, serializer)

    assert "from django.utils import timezone" in source
    assert "lastranked_date=timezone.now()" in serializer_source
    assert "lastranked_date=datetime.now()" not in serializer_source


def test_keyword_notes_keep_the_selected_local_calendar_day():
    keyword = _read("backend/serp/keyword.py")
    serializers = _read("backend/serp/serializers.py")
    note_serializers = _read("backend/serp/custom_serializer/notes_serializers.py")
    notes = _read("backend/serp/notes.py")

    assert "def _note_day_bounds" in keyword
    assert "timezone.make_aware" in keyword
    assert "notesIns.note_date = start" in keyword
    assert "datetime.combine(datetime.strptime(selectdate" not in keyword
    assert "timezone.localtime(obj.note_date)" in serializers
    assert 'timezone.localtime(obj["note_date"])' in note_serializers
    assert "timezone.localtime(dateTime)" in notes


def test_active_competitor_flow_has_no_subscription_gate():
    backend = _read("backend/competitor/views.py").lower()
    frontend = _read("app/src/pages/competitor/components/top_competitors.js").lower()
    project_settings = _read("backend/serp/project_management.py").lower()

    assert "userpaymode" not in backend
    assert "active subscription" not in backend
    assert "subscription" not in frontend
    assert "active subscription" not in project_settings
    assert "premium users" not in project_settings


def test_competitor_selection_syncs_existing_competitors_after_analysis():
    source = _read("app/src/pages/competitor/components/top_competitors.js")
    polling = _read("app/src/pages/competitor/components/analysis_status.js")

    assert "const existingCompetitorDomains" in source
    assert "addedComp: existingCompetitorDomains(props.aiRunStatus.fullCp)" in source
    assert re.search(
        r"useEffect\(\(\) => \{.*?setData\(olddata => \(\{.*?"
        r"addedComp: existingCompetitorDomains\(props\.aiRunStatus\.fullCp\).*?"
        r"filterComp: props\.aiRunStatus\.Cl",
        source,
        re.DOTALL,
    )
    assert "'fullCp':res.Cp, 'Cp':res.Cp" in polling


def test_competitor_reanalysis_queues_tracked_cards_for_serp_refresh():
    source = _read(
        "engine/project/machine/competitor/automation_analyse.py"
    )

    assert "from project.machine.competitor.automation_comp_reload import" in source
    assert "DCompProject as _dC__project_" in source
    assert "competitor_project_array=[]" in source
    assert "automation_comp_reload_data(" in source
    assert '"ENGINE"' in source


def test_competitor_rank_timestamps_are_timezone_aware():
    ranker = _read("engine/project/machine/competitor/automation_call.py")
    serializers = _read(
        "engine/project/machine/competitor/automation_serializers.py"
    )

    assert "from django.utils import timezone" in ranker
    assert "kw.lastranked_date = timezone.now()" in ranker
    assert "kw.modified_date = timezone.now()" in ranker
    assert "from django.utils import timezone" in serializers
    assert "lastranked_date=timezone.now()" in serializers


def test_public_policies_describe_byok_without_searchmirror_billing():
    privacy = _read("app/src/pages/welcome/privacy_policy.js")
    terms = _read("app/src/pages/welcome/terms_and_conditions.js")
    combined = privacy + terms

    for stale_claim in (
        "credit card",
        "PayPal",
        "auto-renewal",
        "money-back guarantee",
        "subscription plans",
        "Registration and billing policy",
    ):
        assert stale_claim not in combined

    assert "does not collect payment details" in privacy
    assert "encrypted at rest" in privacy
    assert "DataBlue" in terms
    assert "provider charges" in terms


def test_register_consumes_email_token_and_has_no_referral_runtime_dependency():
    backend = _read("backend/account/api/views.py")
    frontend = _read("app/src/pages/welcome/register.js")

    assert 'request.data.get("userregtoken")' in backend
    assert "Userregistrationtoken.objects.select_for_update" in backend
    assert "registration.delete()" in backend
    assert "'userregtoken': registrationToken" in frontend
    assert 'typeof window.fpr === "function"' in frontend
    assert 'const [designation, setDesignation] = useState(\'\')' in frontend


def test_register_authenticates_before_bootstrapping_the_new_account():
    frontend = _read("app/src/pages/welcome/register.js")

    token_received = frontend.index("var smusertoken = resp.token")
    token_activated = frontend.index("global.token = 'Token '+smusertoken")
    settings_bootstrap = frontend.index(
        "axios.post(global.apiurl + '/new_user_create'"
    )

    assert token_received < token_activated < settings_bootstrap


def test_favicon_uses_black_mark_on_white_background_without_blue_fallback():
    html = _read("app/index.html")
    favicon = _read("app/public/favicon.svg")
    manifest = _read("app/public/manifest.json")

    assert 'href="/favicon.svg?v=3"' in html
    assert 'href="/favicon.ico"' not in html
    assert 'fill="#ffffff"' in favicon

    # These four assert the INTENT -- a black mark on a white ground, no accent
    # blue. They replace two that asserted the old MECHANISM: an embedded
    # base64 PNG of the accent tile pushed through feColorMatrix +
    # feComponentTransfer to map blue->white and white->black. The mark is now
    # drawn as vector, so the filter and the raster are gone while the design
    # they produced is unchanged. A test that pins the mechanism fails on a
    # better implementation of the same decision, which is what happened here.
    #
    # Why black-on-white is the decision, measured rather than argued:
    #   --ink mark on its white tile   19.16:1 on a light strip, 19.16:1 on dark
    #   white mark on an --accent tile  5.11:1 on light,  2.40:1 on dark
    # The accent tile fails the 3:1 non-text floor on a dark tab strip. On a
    # white active tab the black-on-white tile's EDGE disappears but the mark
    # holds 19.16:1 -- the background vanishes, not the icon, as with GitHub's
    # and Linear's. _tokens.scss also reserves --accent for "act on this";
    # a permanent logo ground would turn the one action colour into furniture.
    assert "#1a3cff" not in favicon.lower()      # no accent blue
    assert 'rx="40" fill="#ffffff"' in favicon   # white ground
    assert 'fill="#0f0f10"' in favicon           # mark drawn in --ink
    assert "base64" not in favicon               # vector, not an embedded raster
    assert '"name": "SearchMirror"' in manifest
    assert '"src": "favicon.svg"' in manifest


def test_local_signup_uses_console_mail_when_smtp_is_not_configured():
    settings = _read("backend/tracker/settings.py")
    signup = _read("app/src/pages/welcome/signup.js")
    public_copy = _read("app/src/pages/contentComponents/content.json")

    assert 'EMAIL_DELIVERY_MODE = "smtp" if EMAIL_HOST else "console"' in settings
    assert "django.core.mail.backends.console.EmailBackend" in settings
    assert "setSentMessage(msg)" in signup
    assert "sentMessage" in signup
    assert "free trial" not in public_copy.lower()
    assert "Create your SearchMirror account" in public_copy


def test_account_email_lifecycle_uses_aware_time_and_current_brand():
    serializer = _read("backend/account/api/serializers.py")
    password_reset = _read("backend/account/authorization/models.py")

    assert "from django.utils import timezone" in serializer
    assert "datetime.now()" not in serializer
    assert '"Password reset for SearchMirror"' in password_reset
    assert "Sepple" not in password_reset


def test_password_reset_masks_both_password_fields():
    reset_page = _read("app/src/pages/welcome/resetPassword.js")

    assert reset_page.count("<PasswordInput") == 2
    assert '<Input label={general.confirm_password}' not in reset_page


def test_site_marks_are_drawn_locally_and_never_fetch_a_third_party_icon():
    """The marks next to tracked domains must not call out to those domains.

    /competitors renders one per discovered competitor -- around 47 of them, all
    third-party SEO vendors -- so a remote favicon there leaked every user's IP,
    User-Agent and referrer to each vendor and left third-party cookies in the
    profile. The tile is generated from the domain's initial instead.
    """
    site_mark = _read("app/src/pages/commonComponents/site_mark.js")

    # The exact construct that built the remote URL. This is the invariant, and
    # it is the only one of the original assertions that survives.
    assert '"https://" + host' not in site_mark

    # The mark is now fetched from OUR backend, which resolves and caches the
    # icon server-side, so the browser still contacts nobody but this instance.
    # The rule is "no THIRD-PARTY request", not "no request" -- the earlier
    # version asserted the mechanism (no useState, no setTimeout, tile only) and
    # so failed the moment a better implementation of the same rule arrived.
    #
    # The mechanism assertions were also actively wrong to keep: a fetch needs
    # exactly the state and the deadline they forbade. A proxied request has no
    # deadline of its own, and a host that black-holes it leaves the element
    # pending forever with onError never firing -- the row then reads as
    # permanently loading, which is the bug the original timeout existed to
    # prevent.
    assert "global.apiurl" in site_mark, "the icon must come from our own origin"
    assert "/site-icon" in site_mark

    # The offline fallback is unchanged and still mandatory: it covers a 204, a
    # 404, a network failure, a hang, and a blank domain.
    assert "letterTile" in site_mark
    assert "AbortController" in site_mark, "a proxied fetch still needs a deadline"


def test_report_capability_check_does_not_print_connection_state():
    widget = _read("backend/serp/widget.py")

    assert "print(grpSet)" not in widget


def test_report_action_menu_layers_above_the_report_table():
    styles = _read("app/src/pages/reports/style.scss")

    assert re.search(
        r"\.projectTableCard\s+\.actionToggleList\s*\{\s*"
        r"z-index:\s*\d+\s*!important",
        styles,
    )


def test_report_widget_lists_give_keys_to_the_elements_returned_by_map():
    report_widget = _read("app/src/pages/reports/report_widget.js")
    table_widget = _read(
        "app/src/pages/reports/ecomTable/ecom_widget_table.js"
    )

    assert "key={`report-widget-${item.sheet_id ?? 'unknown'}-${index}`}" in report_widget
    assert "<React.Fragment" not in report_widget
    assert 'key={`demo-${rwindex}-${clindex}`}' in table_widget


def test_interactive_controls_are_semantic_buttons():
    """A thing you click is a button or a link, never a div with a handler.

    This absorbed test_dashboard_controls_are_not_consumed_by_widget_dragging,
    whose subject -- react-grid-layout's draggableCancel selector -- went with
    the eight-widget grid. There is no drag, so there is nothing for a control
    to be swallowed by, and those four assertions are gone. Its other half was
    never about dragging: it asserted that the controls themselves are real
    elements, which is the rule kept here.

    The history trigger this test used to name went the same way. The rule is
    asserted against the controls that exist now instead: the dashboard's only
    non-link control is the retry on a failed load, and the sweep below is the
    durable half -- it fails the moment anyone reintroduces a div-with-onClick
    anywhere on the screen, including in files that do not exist yet.
    """
    states = _read("app/src/pages/widget/components/dash_states.js")
    assert '<button type="button" className="btn btn-primary" onClick={onRetry}>' in states

    # No div pretending to be a control, anywhere on the dashboard.
    dashboard_sources = [ROOT / "app/src/pages/widget/index.js"]
    dashboard_sources += sorted((ROOT / "app/src/pages/widget/components").glob("*.js"))
    for path in dashboard_sources:
        source = path.read_text(encoding="utf-8")
        assert not re.search(r"<div[^>]*onClick", source), str(path)

    click_away = _read("app/src/pages/commonComponents/click_away.js")
    assert 'component={props.parent ? "span" : "button"}' in click_away
    assert "React.cloneElement(props.parent" in click_away
    assert 'props.label || "Widget actions"' in click_away

    competitor_picker = _read(
        "app/src/pages/competitor/components/top_all_competiitors.js"
    )
    assert '<button type="button" className="viewLink' in competitor_picker
    assert "onClick={handleOpen}" in competitor_picker


def test_authenticated_dashboard_never_renders_demo_metrics():
    """An empty panel says it is empty; it never shows invented numbers.

    Every panel named here is a rebuilt one -- the widgets the original three
    pointed at are gone -- but the rule is the reason the test exists and it
    binds harder now, because a dashboard whose sections are fixed has more
    slots that can be empty on a real account.
    """
    expected_empty_states = {
        "app/src/pages/widget/components/dash_states.js": "No rankings yet",
        "app/src/pages/widget/components/competitor_panel.js": "No competitor is being tracked for this project yet",
        "app/src/pages/widget/components/spread_panel.js": "No keyword has a position to place in a band yet.",
        "app/src/pages/widget/components/ai_panel.js": "No AI answer has been collected for this project yet.",
        "app/src/pages/widget/components/attention_list.js": "Nothing dropped out of the top ten",
    }

    for relative_path, message in expected_empty_states.items():
        source = _read(relative_path)
        assert "demographData" not in source, relative_path
        assert "demodataRows" not in source, relative_path
        assert "demo={true}" not in source, relative_path
        assert message in source, relative_path


def test_visibility_score_uses_shared_current_and_historical_calculation():
    backend = _read("backend/serp/widget.py")

    assert "from shared.scoring import calculate_visibility_history" in backend
    assert "calculate_visibility_history(keyword_rank_histories)" in backend
    assert "calculate_visibility_breakdown(current_ranks)" in backend
    assert 'scoreData.update(score_breakdown)' in backend
    assert 'scoreData["baseline_changed"]' in backend

    # The score's BASIS changing must be stated, not drawn as a ranking
    # movement. score_widget.js said so with "New baseline" off
    # `baseline_changed`; the rebuilt dashboard says it off `keywords_delta`,
    # which is the same event -- the keyword set moved, so the denominator
    # moved, so the line fell with nothing having been lost. Project 4 is the
    # case that proves it: 17.5 -> 4.0 with no position changed.
    #
    # Asserted on the mechanism rather than the sentence. The wording will be
    # edited; that the note is driven by a real delta and gated on a real
    # window is the part that must not regress.
    data_layer = _read("app/src/pages/widget/dashboard_data.js")
    assert "export function keywordShift(data)" in data_layer
    assert "m.comparable !== true" in data_layer
    assert "m.keywordsDelta === null || m.keywordsDelta === 0" in data_layer

    trend = _read("app/src/pages/widget/components/trend_panel.js")
    assert "shift && shift.material" in trend
    assert "The score divides by every tracked keyword" in trend
    for relative_path in (
        "engine/project/machine/formulate.py",
        "engine/project/machine/competitor/automation_formulate.py",
        "engine/project/machine/competitor/automation_cFormulate.py",
    ):
        engine = _read(relative_path)
        assert "from shared.scoring import calculate_visibility_score_from_buckets" in engine
        assert "return calculate_visibility_score_from_buckets(scorePerDay, allKey)" in engine
        assert "meterMark = -0.10" not in engine


# Directories whose contents are source: they ship, or they are the tests that
# guard what ships. Anything git reports as untracked under these is a staging
# gap, not a scratch file -- .gitignore already excludes the genuine noise
# (__pycache__, logs, collected static, local env), and `git status` honours it.
#
# Deliberately excluded: the repository root, which legitimately holds untracked
# agent tooling (CLAUDE.md, AGENTS.md, .claude/) and docs whose .gitignore rules
# are a considered choice rather than an oversight.
SOURCE_TREES = (
    "app/src",
    "backend",
    "brand",
    "docker",
    "engine",
    "landing/src",
    "shared",
    "tests",
)


def test_a_first_day_project_never_claims_a_yesterday():
    """A score is one measurement; "yesterday" and a delta are claims about two.

    On a project's first measured day there is only one. Both surfaces that show
    the triple fall back rather than admit that -- /homeauth copies ss into yss
    (serializers.py), /projectoverview zeroes it -- so the same project's first
    day rendered "no change" on one screen and a full +60 rise on the other,
    from the same single reading. Neither fallback is a measurement, so neither
    is gated on: t_c is the count the score is built from, and below 2 the
    comparison is not drawn at all.
    """
    backend = _read("backend/serp/serializers.py")
    overview_backend = _read("backend/serp/project_management.py")
    projects = _read("app/src/pages/dashboard/index.js")
    overview = _read("app/src/pages/serpRank/components/serp_overview.js")

    # The count has to be sent before either screen can gate on it, under the
    # same name /erocs_wdt already uses.
    assert '"t_c"' in backend
    assert '"t_c"' in overview_backend

    # /projects: no delta and no "yesterday" without a second measurement.
    assert "const hasPrevious = (prjt) => Number(prjt.t_c) > 1" in projects
    assert "const compared = scored && hasPrevious(prjt)" in projects
    assert "{scored && compared ? scoreDelta(prjt) : null}" in projects
    # Three states -- never measured, measured once, comparable -- not two.
    assert "Not measured yet" in projects
    assert "Measured once so far" in projects

    # /keywords overview: same gate, and it also colours a pie by the delta.
    assert "const hasPrevious = Number(prjtstatus.t_c) > 1" in overview
    assert "yserpscore={hasPrevious ? prjtstatus.yss : prjtstatus.ss}" in overview
    assert 'Number(prjtstatus.t_c) === 1 ? "Measured once" : "Not measured yet"' in overview

    # C-21: the direction word is "Rising". "Raising" was on both screens.
    # Only serp_overview still uses that vocabulary -- the rebuilt dashboard
    # says "improved" and "declined" -- so the positive half is asserted where
    # the word lives and the typo guard is swept across the dashboard, which is
    # the half that would catch it coming back.
    assert "Raising" not in overview
    assert "Rising" in overview
    for relative_path in (
        "app/src/pages/widget/components/stat_row.js",
        "app/src/pages/widget/components/trend_panel.js",
    ):
        assert "Raising" not in _read(relative_path), relative_path

    # The same rule on the rebuilt dashboard, where it now has three guards
    # rather than one. A score is one measurement; a delta, a window and a
    # keyword-count change are all claims about two, and each is gated on the
    # API confirming a second reading exists rather than on a value being
    # truthy. `comparable` is three-valued -- null means the API did not say,
    # which is not permission.
    data_layer = _read("app/src/pages/widget/dashboard_data.js")
    assert 'return { state: "unmeasured", moved: 0 };' in data_layer
    assert "m.comparable !== true" in data_layer
    assert "movement.windowActual !== null && movement.windowActual > 0" in data_layer
    assert "return data.visibility.spark.length > 0;" in data_layer

    trend_panel = _read("app/src/pages/widget/components/trend_panel.js")
    assert "is nothing to compare." in trend_panel


def test_deleted_source_files_are_staged_as_deletions():
    """Removing a file from disk does not remove it from the release.

    The companion to the tracking check above, and the harder half to see. That
    one catches a file that exists on disk and in no commit; this one catches a
    file that is still in the commit and no longer on disk. Both are the same
    invariant -- the working tree and what will actually ship disagree about
    which files exist -- but they fail in opposite directions, and only this one
    is silent: everything works locally, every other check in this suite reads
    the working tree where the file is correctly gone, and the deleted content
    ships anyway.

    That is not hypothetical here. The issue register lists the commercial
    Averta typefaces (X-06) and the predecessor's wordmark (X-05) as fixed this
    session, and they are -- deleted from disk. Their deletions were never
    staged, so both would still be published. "Gone from disk" is a proxy for
    "gone from the release", and a licence violation is a bad place to accept a
    proxy.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--"] + list(SOURCE_TREES),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        import pytest

        pytest.skip("git unavailable: %s" % exc)

    if result.returncode != 0:  # pragma: no cover
        import pytest

        pytest.skip("git status failed: %s" % result.stderr.strip())

    # " D" is deleted from the working tree with the deletion UNSTAGED -- still
    # in the index, so still in the next commit. "D " is a staged deletion,
    # which is the correct end state and is not reported here.
    unstaged_deletions = sorted(
        line[3:].strip().strip('"')
        for line in result.stdout.splitlines()
        if line.startswith(" D ")
    )

    if not unstaged_deletions:
        return

    # 200+ paths is unreadable as a flat list, and an unreadable failure gets
    # skimmed. Group by top-level area, show a few from each.
    by_area = {}
    for path in unstaged_deletions:
        parts = path.split("/")
        depth = 3 if parts[0] == "app" else 2
        # A path shallower than the grouping depth is its own directory, which
        # would make the group name the file name. Fall back a level.
        area = "/".join(parts[:depth]) if len(parts) > depth else parts[0]
        by_area.setdefault(area, []).append(path)

    lines = []
    for area in sorted(by_area):
        paths = by_area[area]
        lines.append("  %s  (%d)" % (area, len(paths)))
        for path in paths[:3]:
            lines.append("      %s" % path)
        if len(paths) > 3:
            lines.append("      ... and %d more" % (len(paths) - 3))

    # NOT `git add -A <dir>`: this tree carries unrelated modified files from
    # other work, and a directory-scoped add stages every one of them along
    # with the deletions. A remedy that sweeps in unreviewed changes is worse
    # than no remedy. This pipeline stages the unstaged deletions and nothing
    # else -- it re-runs the same query and passes only those paths to git add.
    remedy = (
        "git status --porcelain -- %s \\\n"
        "      | grep '^ D' | cut -c4- | tr '\\n' '\\0' | xargs -0 git add --"
        % " ".join(SOURCE_TREES)
    )

    raise AssertionError(
        "%d file(s) were deleted from disk but their deletions are not staged, "
        "so every one of them still ships:\n\n%s\n\n"
        "    %s\n\n"
        "Staging a deletion is not the same as deleting the file. Until it is "
        "staged the removal exists only on this machine. Stage the deletions "
        "alone -- a directory-wide `git add -A` would also stage unrelated "
        "modified files this tree is carrying."
        % (len(unstaged_deletions), "\n".join(lines), remedy)
    )


def test_every_source_file_is_tracked_by_git():
    """A file that exists on one machine and in no commit is not a feature.

    This repository has shipped that bug twice. The pre-launch audit found
    fourteen imported modules, two migrations and half the test suite never
    `git add`ed -- the published repository would not have run. They were
    staged; then four parallel lanes each created new source files and did not
    stage those either, and nothing caught it, because every other check in
    this suite reads the working tree, where the file is present and correct.

    A missing import is a build failure on a fresh clone and completely
    invisible locally, which is the worst combination a defect can have. So it
    is asserted here rather than left to review: the check costs one git call
    and fails with the exact command that fixes it.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--"]
            + list(SOURCE_TREES),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        import pytest

        pytest.skip("git unavailable: %s" % exc)

    if result.returncode != 0:  # pragma: no cover
        import pytest

        pytest.skip("git status failed: %s" % result.stderr.strip())

    untracked = sorted(
        line[3:].strip().strip('"')
        for line in result.stdout.splitlines()
        if line.startswith("?? ")
    )

    assert not untracked, (
        "%d source file(s) exist on disk but are in no commit. A fresh clone "
        "will not have them, and anything importing them fails to build:\n\n"
        "    git add %s\n\n"
        "If one of these genuinely should not ship, add it to .gitignore "
        "instead -- an explicit exclusion is reviewable; an unstaged file is "
        "not." % (len(untracked), " ".join(untracked))
    )


def test_refresh_never_claims_success_on_a_run_that_failed():
    """`runkeyword` reaching 0 means the run STOPPED, not that it worked.

    The engine clears the running flag on its error paths too, so 0-and-"done"
    was reached identically by total success and total failure, and the poller
    fired "SERP Data loaded successfully" over both. `/refreshstatus` now
    carries `errc` (machine code for this run) and `err` (the sentence to
    show); B-03.
    """
    poller = _read("app/src/pages/commonComponents/refresh_bar.js")
    backend = _read("backend/serp/views.py")
    error_state = _read("backend/serp/refresh_error.py")

    # The backend has to be sending it before the frontend can read it.
    assert "refresh_error_state(userid, grpid, refreshIns)" in backend
    assert '"errc": errcode' in backend
    assert '"err": errmessage' in backend
    assert '"fkw": failedKeywords' in backend

    # errc is checked BEFORE the done-and-drained branch, not inside it.
    # nokey, keyunreadable and engine_disabled are all raised while a run is
    # still nominally in flight, so a check gated on runkeyword === 0 would
    # never fire for them -- the poller would exhaust its attempts and report
    # "taking longer than expected" instead of naming the cause.
    errc_at = poller.index("}else if(res.errc) {")
    drained_at = poller.index('}else if(parseInt(res.runkeyword) === 0 && res.rst === "done") {')
    assert errc_at < drained_at

    # err is rendered verbatim: the engine writes it with counts this side
    # cannot reconstruct.
    assert "toast.error(res.err ||" in poller

    # Success is claimed only where errc is empty, and never from fkw, which is
    # a standing count that survives the run that set it.
    success_branch = poller[drained_at:drained_at + 1800]
    assert "toast.success('SERP Data loaded successfully.')" in success_branch
    assert "res.fkw" not in poller

    # The backend must not derive a per-run code from that standing count
    # either -- same bug inverted. Asserted against code rather than prose:
    # the module documents the rejected derivation in a comment, so a plain
    # substring search matches the explanation of the fix, not the fix.
    code_only = "\n".join(
        line for line in error_state.splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "return CODE_SERP_FAILED" not in code_only
    assert 'return "", "", failed' in code_only


def test_visibility_score_is_one_number_under_one_name():
    """The same measurement read 37 / 34 / 34 on three screens under two names.

    The number was two formulas -- shared/scoring.py weights an unranked
    keyword 0.0, the backend copies weighted it -0.10 -- and the differing
    names hid the contradiction from a casual reader.
    """
    # One formula. The engine already delegated; the surviving backend copy
    # now does too -- the second, in the parked `kw_research` app, went with
    # that package on 2026-09-05.
    for relative_path in (
        "backend/serp/calculation.py",
    ):
        source = _read(relative_path)
        assert "calculate_visibility_score_from_buckets" in source, relative_path
        # The assignment, not the digits: both files explain the old weight in
        # a comment, and matching that would fail on the description of the fix.
        assert "meterMark = -0.10" not in source, relative_path
        assert "score_meter = -0.10" not in source, relative_path

    assert 'BUCKET_WEIGHTS = {' in _read("shared/scoring.py")
    assert '"gt__limit": 0.0' in _read("shared/scoring.py")

    # One name, on every surface that shows it.
    #
    # score_widget.js and toggle_widget.js were dropped when the dashboard's
    # eight-widget grid was replaced. The surfaces move; the rule does not.
    #
    # The rule is NOT "the full name appears everywhere" -- a stat tile and a
    # table column legitimately use the short form, which is why /projects was
    # always allowed a short header with the full name in its tooltip. The rule
    # is that the SECOND, CONTRADICTORY name never appears, and that the
    # canonical name is reachable from wherever the number is shown. Two names
    # for one measurement is what let 37 and 34 sit on two screens unnoticed.
    for relative_path in (
        "app/src/pages/serpRank/grid_single_table.js",
        "app/src/pages/serpRank/components/serp_overview.js",
        "app/src/pages/competitor/components/competitor_overview.js",
        "app/src/pages/competitor/components/competitor_projects.js",
    ):
        source = _read(relative_path)
        assert "Search Visibility Score" in source, relative_path
        assert "SearchMirror score" not in source, relative_path

    # /projects names it in the tooltip; its column header is the short form.
    projects = _read("app/src/pages/dashboard/index.js")
    assert "What is the Search Visibility Score?" in projects
    assert '<span className="prjSrOnly">Search Visibility Score</span>' in projects

    # The rejected name appears on no rebuilt dashboard surface. This is the
    # assertion that actually caught the 37-vs-34 bug.
    #
    # dashboard/index.js is deliberately NOT in this list: it names all three
    # rejected spellings in the comment that explains the fix, so asserting on
    # the bare string there would fail on the description of the repair rather
    # than on a repeat of the bug -- the same trap the -0.10 assertion above
    # calls out and sidesteps.
    for relative_path in (
        "app/src/pages/widget/components/stat_row.js",
        "app/src/pages/widget/components/trend_panel.js",
        "app/src/pages/widget/dashboard_data.js",
    ):
        assert "SearchMirror score" not in _read(relative_path), relative_path


def test_keyword_list_has_working_local_pagination_controls():
    source = _read("app/src/pages/serpRank/data_table.js")

    assert "useState(25)" in source
    assert "[10, 25, 50, 100].includes" in source
    assert "setPerPage(newPerPage)" in source
    assert "pagination={totalRows > 10}" in source
    assert "paginationRowsPerPageOptions={[10, 25, 50, 100]}" in source
    assert "paginationServer={false}" in source


def test_keyword_detail_does_not_ship_a_volume_history_tab():
    # Search volume has no provider on this product, so /kwsvolume always
    # answers with an empty series. The keyword detail page rendered a whole
    # Volume History tab from it -- four NA tiles and an empty chart. The route
    # guards elsewhere in this file cover routes and sidebar links; an in-page
    # tab is neither, so it is asserted here.
    tab_file = ROOT / "app/src/pages/keywordOverview/components/volume_history_tab.js"
    assert not tab_file.exists()

    detail = _read("app/src/pages/keywordOverview/index.js")
    assert "volume_history_tab" not in detail
    assert "Volume History" not in detail
    assert "kwsvolume" not in detail

    # The competitors panel is in-page, and it is not labelled "Competitors":
    # the side rail carries a destination by that exact name on the same
    # screen, so two controls answered to one word and only one of them stayed
    # on the keyword.
    assert 'label="SERP Competitors" value="3"' in detail
    assert "<KWCompetitors" in detail


def test_dashboard_empty_charts_are_compact_and_non_negative():
    """Never-measured is said in words, and no axis runs below zero.

    Both halves survived the rebuild; only the files moved. `rowHeight={460}`
    went with react-grid-layout and is not replaced -- there is no fixed row
    height to assert against a layout that has no grid.

    The first assertion is the one worth keeping most. "Has this project ever
    ranked" must be answered by the spark series and nothing else: the score is
    always an int and 0 is a real reading; the five spread buckets sum to the
    KEYWORD count so a never-run project totals 30, not 0; and
    `visibility.unranked` counts all 30 for the same reason. Each of those
    alternatives reports a never-run project as measured and shows it a
    dashboard of zeros, and two of them were tried here first.
    """
    data_layer = _read("app/src/pages/widget/dashboard_data.js")
    assert "return data.visibility.spark.length > 0;" in data_layer

    states = _read("app/src/pages/widget/components/dash_states.js")
    assert "No rankings yet" in states

    # Non-negative, and anchored rather than fitted. A series scaled to its own
    # extremes turns any short run into a cliff whatever the numbers are.
    trend = _read("app/src/pages/widget/components/trend_panel.js")
    assert "min: 0," in trend
    assert "One reading so far, so there is no line yet." in trend


def test_favourites_are_not_shipped():
    """Favourites had two entry points and neither led anywhere.

    The dashboard favourites widget was cut first, then the star in the
    keywords table's actions column, on the grounds that the action had
    nowhere left to lead. What survived was a star beside the
    keyword title and a "Favourite" option in the grid view's filter menu --
    two ways to set a flag that nothing displayed. The owner spotted the star
    and asked why it was still there.

    Removed on 2026-09-05: the control, the grid view, the `/favour` and
    `kcip_wdt` endpoints, `FavWidgetSerializer`, the `Manage Favourites` team
    permission, and the `fv` field the API sent for a flag no screen read.

    `Keyword.favour` is deliberately KEPT. It is a populated column, and
    `engine/project/machine/models.py` declares the same collection through
    mongoengine -- dropping it on one side only is the `FieldDoesNotExist`
    failure CLAUDE.md warns about. A dormant column is not dead code.
    """
    assert not (ROOT / "app/src/pages/serpRank/components/keyword_favourite.js").exists(), (
        "the favourite control is back"
    )

    for relative in (
        "app/src/pages/keywordOverview/index.js",
        "app/src/pages/serpRank/serp_rank_table.js",
        "app/src/pages/serpRank/gridTableComponents/grid_table_filter.js",
        "app/src/pages/serpRank/gridTableComponents/empty_table.js",
        "app/src/pages/serpRank/grid_single_table.js",
        "app/src/pages/userManagement/manageRoles/rolesPr.js",
    ):
        source = _read(relative)
        for token in ("KWFavourite", "canManageFavourites", "Manage Favourites", "'fav'"):
            assert token not in source, "%s still references %s" % (relative, token)

    urls = _read("backend/serp/urls.py")
    for route in ("favour", "kcip_wdt"):
        assert route not in urls, "%s is routed again with nothing to call it" % route

    for relative, gone in (
        ("backend/serp/views.py", "def favour("),
        ("backend/serp/widget.py", "def favourite_widget("),
        ("backend/serp/custom_serializer/widget_serializers.py", "class FavWidgetSerializer"),
        ("backend/account/team_permissions.py", "/favour"),
    ):
        assert gone not in _read(relative), "%s: %s is back" % (relative, gone)

    # The column stays; only the feature went.
    assert "favour = models.IntegerField" in _read("backend/serp/models.py"), (
        "Keyword.favour was dropped. The engine declares the same collection "
        "through mongoengine -- removing a column on one side only makes every "
        "keyword unreadable to the ranking worker."
    )


def test_the_profile_menu_links_use_a_component_that_can_be_a_link():
    """`MenuItem` in sidebar.js is react-pro-sidebar's, which powers the rail
    and accepts `onClick` but has no `component`/`href`.

    The "Source on GitHub" and "Documentation" rows sit inside a MUI <MenuList>
    and were written with MUI's API, so `component="a"` and `href` were dropped
    and both rendered inert. The project's own source and documentation were
    unreachable from inside the app -- which is the exact thing the comment
    above them says that menu exists to fix. Logout worked only because it uses
    onClick, which the other component does support.
    """
    source = _read("app/src/pages/commonComponents/sidebar.js")

    assert 'import MuiMenuItem from "@mui/material/MenuItem"' in source, (
        "the MUI MenuItem alias is gone; a react-pro-sidebar MenuItem cannot "
        "render an href"
    )

    for anchor in ("href={REPO_URL}", "href={DOCS_URL}"):
        assert anchor in source, "%s is no longer linked" % anchor
        # the opening tag for that row must be the MUI one
        before = source.split(anchor, 1)[0]
        opening = before.rsplit("<", 2)[-2].split()[0] if "<" in before else ""
        assert "MuiMenuItem" in before.rsplit("<MuiMenuItem", 1)[-1] or \
               before.rstrip().endswith(('component="a"',)) or \
               "<MuiMenuItem" in before[-400:], (
            "%s hangs off a component that ignores href, so the row is inert" % anchor
        )
