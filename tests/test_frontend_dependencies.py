"""Regression contracts for production frontend dependency hygiene."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _major(version_spec):
    return int(version_spec.lstrip("^~>=< ").split(".", 1)[0])


def test_frontend_uses_supported_dependency_lines():
    package = json.loads(_read("app/package.json"))
    dependencies = package["dependencies"]

    assert _major(dependencies["axios"]) >= 1
    assert _major(dependencies["universal-cookie"]) >= 8
    assert _major(dependencies["swiper"]) >= 14
    assert _major(dependencies["react-quill-new"]) >= 3
    # Asserted only if declared. lodash was removed on 2026-09-05 -- nothing in
    # app/src imported it, and it is not a peer requirement of anything kept
    # (docs/SHIPPED-SURFACE.md). A package that is not declared has no version
    # line to support; if one is re-added it still has to be a current one.
    if "lodash" in dependencies:
        assert _major(dependencies["lodash"]) >= 4
    assert dependencies["quill"] == "2.0.2"
    assert package["overrides"]["quill"] == "2.0.2"
    assert _major(dependencies["@hello-pangea/dnd"]) >= 18

    for retired_package in ("exceljs", "react-beautiful-dnd", "react-quill", "xlsx"):
        assert retired_package not in dependencies


def test_active_editor_and_carousel_use_current_package_entrypoints():
    editor = _read("app/src/pages/contentPlanner/cedit_editor.js")
    assert 'from "react-quill-new"' in editor
    assert '"react-quill-new/dist/quill.snow.css"' in editor

    for relative_path in (
        "app/src/pages/dashboard/index.js",
        "app/src/pages/serpRank/index.js",
        "app/src/pages/serpRank/serp_rank_table.js",
        "app/src/pages/serpRank/grid_single_table.js",
    ):
        source = _read(relative_path)
        assert '"swiper/swiper.min.css"' not in source


def test_column_reordering_uses_the_maintained_drag_and_drop_package():
    source = _read("app/src/pages/serpRank/components/table_custom_columns.js")

    assert 'from "@hello-pangea/dnd"' in source
    assert 'from "react-beautiful-dnd"' not in source


def test_react_tag_input_uses_string_separators():
    prompt_source = _read("app/src/pages/commonComponents/llm/llm_prompts.js")
    tag_source = _read("app/src/pages/commonComponents/manage_tag.js")

    assert 'const separators = [",", "Enter"];' in prompt_source
    assert "separators={separators}" in prompt_source
    assert "separators={delimiters}" not in prompt_source

    assert 'const separators = [",", "Enter"];' in tag_source
    assert tag_source.count("separators={separators}") == 4
    assert "separators={delimiters}" not in tag_source
