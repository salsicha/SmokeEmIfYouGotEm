import json
from pathlib import Path

from raftsim.editor_source_layout import (
    build_editor_source_inventory,
    read_raftsim_editor_source,
    render_editor_source_inventory_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "physics/reports/editor_source_inventory"
FROZEN_LEGACY_EXCEPTIONS = {
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorPveEvaluation.cpp",
}


def test_editor_source_set_contains_commands_and_all_river_build_paths():
    inventory = build_editor_source_inventory(REPO_ROOT)
    source = read_raftsim_editor_source(REPO_ROOT)

    assert inventory["registered_console_command_count"] >= 30
    assert len({row["command"] for row in inventory["registered_console_commands"]}) == (
        inventory["registered_console_command_count"]
    )
    assert inventory["all_river_build_targets_present"] is True
    assert "RaftSim.CreateLandscapeImportCandidateMaps" in source
    assert "RaftSim.CreatePhotorealEnvironmentPreviewMaps" in source


def test_editor_source_split_keeps_module_and_focused_implementations_bounded():
    inventory = build_editor_source_inventory(REPO_ROOT)
    line_counts = {
        row["path"]: row["line_count"] for row in inventory["implementation_files"]
    }

    module_path = (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/"
        "RaftSimEditorModule.cpp"
    )
    assert line_counts[module_path] <= 1500
    assert not any("EnvironmentLegacy" in path for path in line_counts)
    assert {
        path: line_count
        for path, line_count in line_counts.items()
        if line_count > 3000 and path not in FROZEN_LEGACY_EXCEPTIONS
    } == {}

    internal_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    )
    assert len(internal_header.read_text(encoding="utf-8").splitlines()) <= 3000


def test_editor_source_inventory_matches_generator():
    expected = build_editor_source_inventory(REPO_ROOT)

    assert json.loads((REPORT_ROOT / "inventory.json").read_text(encoding="utf-8")) == expected
    assert (REPORT_ROOT / "inventory.md").read_text(encoding="utf-8") == (
        render_editor_source_inventory_markdown(expected)
    )
