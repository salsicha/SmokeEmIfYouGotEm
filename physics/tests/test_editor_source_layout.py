import json
from pathlib import Path

from raftsim.editor_source_layout import (
    build_editor_source_inventory,
    read_raftsim_editor_source,
    render_editor_source_inventory_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "physics/reports/editor_source_inventory"


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


def test_editor_source_inventory_matches_generator():
    expected = build_editor_source_inventory(REPO_ROOT)

    assert json.loads((REPORT_ROOT / "inventory.json").read_text(encoding="utf-8")) == expected
    assert (REPORT_ROOT / "inventory.md").read_text(encoding="utf-8") == (
        render_editor_source_inventory_markdown(expected)
    )
