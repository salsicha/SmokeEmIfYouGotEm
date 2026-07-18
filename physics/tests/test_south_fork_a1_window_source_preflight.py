import json
from pathlib import Path

from raftsim.south_fork_a1_window_source_preflight import (
    FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH,
    build_south_fork_a1_window_source_pull_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_preflight() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_source_preflight_is_reproducible():
    generated = build_south_fork_a1_window_source_pull_preflight(REPO_ROOT)
    committed = _load_preflight()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_window_source_pull_preflight_review.v2"
    assert (
        committed["status"]
        == "adopted_axis_source_manifests_ready_for_stitched_validation"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_source_preflight_covers_adopted_anchor():
    preflight = _load_preflight()
    downstream = preflight["downstream_anchor_review"]

    assert downstream["anchor_status"] == "adopted_ground_truth_official_access_geometry"
    assert downstream["anchor_name"] == "Salmon Falls  Lower Water Raft Take-out"
    assert downstream["adopted_station_m"] == 49077.732
    assert downstream["planned_station_end_m"] == 49077.732
    assert downstream["final_window_id"] == "salmon_falls_takeout_approach_41500_49077m"
    assert downstream["final_window_end_m"] == downstream["adopted_station_m"]
    assert downstream["final_window_ends_at_adopted_anchor"] is True
    assert downstream["pending_human_review"]["blocking"] is False
    superseded = downstream["superseded_source_mile_window"]
    assert superseded["source_mile_window"]["minimum_mile"] == 20.5
    assert superseded["source_mile_window"]["maximum_mile"] == 21.0
    assert superseded["historical_review_window_id"] == (
        "salmon_falls_folsom_review_32991_33796m"
    )


def test_south_fork_a1_window_source_preflight_allows_only_nonpromotional_source_pull():
    preflight = _load_preflight()
    readiness = preflight["execution_readiness"]
    gate = preflight["promotion_gate"]

    assert preflight["window_continuity"]["contiguous"] is True
    assert preflight["window_continuity"]["gap_count"] == 0
    assert preflight["window_continuity"]["window_count"] == 8
    assert readiness["can_execute_full_axis_source_pull"] is True
    assert readiness["source_pull_needed"] is False
    assert readiness["source_files_present"] is True
    assert readiness["window_manifests_present"] is True
    assert readiness["can_enter_stitched_validation_review"] is True
    assert readiness["source_pull_task_count"] == 16
    assert readiness["expected_source_file_count"] == 16
    assert readiness["present_source_file_count"] == 16
    assert readiness["present_window_manifest_count"] == 8
    assert readiness["destination_missing_count"] == 0
    assert gate["can_download_source_files"] is True
    assert gate["can_promote_full_reach_corridor"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert "Unreal full-reach landscape import" in readiness["forbidden_use"]
