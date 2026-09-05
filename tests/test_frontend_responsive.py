"""Source contracts for responsive shell and parked OAuth behavior."""

import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_mobile_and_desktop_shell_breakpoints_do_not_overlap():
    source = _read("app/src/pages/routeComponents/private_route.js")
    assert 'useMediaQuery("(max-width:575.98px)")' in source
    assert 'useMediaQuery("(min-width:576px)")' in source


def test_desktop_navigation_groups_start_open_and_toggle_independently():
    source = _read("app/src/pages/commonComponents/sidebar.js")

    assert 'const GROUP_PREF = "tracker.rail.groups.v2"' in source
    assert "NAV_GROUPS.forEach((g) => { state[g.id] = true; });" in source
    assert "const next = { ...prev, [id]: !prev[id] };" in source


def test_auth_uses_a_compact_centered_shell_that_can_shrink():
    layout = _read("app/src/pages/welcome/components/layout.js")
    styles = _read("app/src/pages/welcome/style.scss")

    assert "authAside" not in layout
    assert "authSample" not in layout
    assert "Powered by DataBlue" in layout
    assert re.search(
        r"\.authFrame\s*\{[^}]*width:\s*100%;[^}]*max-width:\s*28rem;",
        styles,
        re.DOTALL,
    )
    assert re.search(
        r"\.loginRightBox\s*\{[^}]*width:\s*100%;",
        styles,
        re.DOTALL,
    )
    assert "grid-template-columns: minmax(0, 1fr);" in styles


def test_parked_gsc_does_not_request_a_token_without_oauth_config():
    source = _read("app/src/pages/serpRank/index.js")
    assert re.search(
        r"if\s*\(gscClientId\)\s*\{\s*updateAccessToken\(controller\.signal\)",
        source,
        re.DOTALL,
    )


def test_refresh_status_has_one_visual_card():
    component = _read("app/src/pages/commonComponents/refresh_bar.js")
    shell = _read("app/src/assets/styles/modules/_shell.scss")

    assert 'className="refreshProgressContent"' in component
    assert 'className="progressCard"' not in component
    assert "height: auto !important" in shell


def test_add_forms_only_select_values_returned_by_settings():
    shared = _read("app/src/pages/common_fun.js")
    add_project = _read("app/src/pages/addProject/index.js")
    add_keyword = _read("app/src/pages/addProject/add_keyword.js")
    parts = _read("app/src/pages/commonComponents/parts.js")

    assert "export const normalizeSearchDefaults" in shared
    assert "regions.find((item) => item.Rcd === selectedCode)" in shared
    assert "languages.find((item) => item.LN === \"English\")" in shared
    assert "language: selectedLanguage ? selectedLanguage.LN : \"\"" in shared
    for source in (add_project, add_keyword):
        assert 'useState("")' in source
        assert re.search(
            r"normalizeSearchDefaults\(\s*res\.rg,\s*res\.lnge,\s*res\.DR",
            source,
        )
        assert 'useState("google.com")' not in source
        assert 'useState(["(English)"])' not in source
        assert "'language': lang," in source
        assert "setLang(value);" in source

    assert "Array.isArray(selected) ? selected.join(\", \") : selected" in parts
    assert 'typeof (selected) === "string" ? selected.join' not in parts


def test_keyword_chip_delete_is_one_integrated_control():
    styles = _read("app/src/pages/addProject/style.scss")

    assert ".addtag .tags-input ul li > button.close" in styles
    assert "appearance: none" in styles
    assert "border: 0" in styles
    assert "border-left: 1px solid var(--line)" in styles
    assert "border-radius: 999px" in styles


def test_add_project_footer_never_overlays_form_fields():
    styles = _read("app/src/pages/addProject/style.scss")

    assert re.search(
        r"\.addProject\s*\{.*?\.footer\s*\{[^}]*position:\s*static;",
        styles,
        re.DOTALL,
    )
    assert not re.search(
        r"\.addProject\s*\{.*?\.footer\s*\{[^}]*position:\s*sticky;",
        styles,
        re.DOTALL,
    )


def test_mobile_drawer_keeps_the_global_project_switcher():
    sidebar = _read("app/src/pages/commonComponents/sidebar.js")
    mobile_sidebar = sidebar.split("export function MobSidebar", 1)[1]

    assert "<ProjectSwitcher />" in mobile_sidebar


def test_reports_table_overflow_is_contained_by_its_card():
    component = _read("app/src/pages/reports/report_widget.js")
    styles = _read("app/src/pages/reports/style.scss")

    assert 'className="reportsCanvas"' in component

    report_styles = styles.split(".reportsCanvas {", 1)[1]
    assert ".projectSection > .MuiGrid-item" in report_styles
    assert report_styles.count("min-width: 0;") >= 3
    assert ".MuiTableContainer-root" in report_styles
    assert "overflow-x: auto;" in report_styles
    assert "scrollbar-gutter: stable;" in report_styles
    assert "text-overflow: ellipsis;" in report_styles
    assert "outline: none;" in report_styles
    assert "@media (max-width: 900px)" in report_styles
    assert ".MuiTablePagination-toolbar" in report_styles
    assert "flex-wrap: wrap;" in report_styles
    assert ".MuiTablePagination-spacer" in report_styles
    assert "display: none;" in report_styles
