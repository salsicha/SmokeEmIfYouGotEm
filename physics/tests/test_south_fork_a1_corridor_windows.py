import json
from pathlib import Path

from raftsim.south_fork_a1_corridor_windows import (
    FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
    build_south_fork_a1_full_reach_corridor_window_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_corridor_window_manifest_is_reproducible():
    generated = build_south_fork_a1_full_reach_corridor_window_manifest(REPO_ROOT)
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_full_reach_corridor_window_manifest.v1"
    )
    assert committed["status"] == "planned_full_reach_windows_review_gated_not_source_complete"
    assert committed["production_promoted"] is False


def test_south_fork_a1_corridor_window_manifest_covers_full_review_route():
    manifest = _load_manifest()
    summary = manifest["coverage_summary"]
    windows = manifest["windows"]

    assert summary["window_count"] == 6
    assert summary["planned_station_start_m"] == 0.0
    assert summary["planned_station_end_m"] == 33796.224
    assert summary["planned_length_m"] == 33796.224
    assert summary["existing_source_attached_length_m"] == 2500.0
    assert summary["remaining_source_pull_length_m"] == 31296.224
    assert manifest["windowing_policy"]["requires_stitched_validation_outputs"] is True
    assert windows[0]["window_id"] == "chili_bar_existing_pilot_0_2500m"
    assert windows[-1]["window_id"] == "salmon_falls_folsom_review_32991_33796m"
    assert windows[0]["existing_reach_id"] == "chili_bar_0_2500m"
    assert all(window["production_promoted"] is False for window in windows)


def test_south_fork_a1_corridor_window_manifest_assigns_all_rapids():
    manifest = _load_manifest()
    assignments = manifest["rapid_window_assignments"]
    by_name = {assignment["name"]: assignment for assignment in assignments}

    assert manifest["coverage_summary"]["named_rapid_count"] == 20
    assert manifest["coverage_summary"]["all_named_rapids_assigned"] is True
    assert len(by_name) == 20
    assert by_name["Meat Grinder"]["window_id"] == "chili_bar_existing_pilot_0_2500m"
    assert by_name["Troublemaker"]["window_id"] == (
        "upper_chili_bar_to_coloma_2500_10000m"
    )
    assert by_name["Satan's Cesspool"]["window_id"] == "upper_gorge_24000_28500m"
    assert by_name["Surprise"]["window_id"] == (
        "lower_gorge_to_salmon_falls_28500_32991m"
    )
    assert all(
        assignment["can_bind_editor_geometry"] is False
        and assignment["can_bind_solver_window"] is False
        for assignment in assignments
    )


def test_south_fork_a1_corridor_window_manifest_blocks_promotion():
    manifest = _load_manifest()
    gate = manifest["promotion_gate"]

    assert gate["can_promote_full_reach_corridor"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_south_fork_named_rapid_geometry"] is False
    assert gate["can_bind_meat_grinder_troublemaker_solver_windows"] is False
    assert len(gate["exit_criteria"]) == 5
