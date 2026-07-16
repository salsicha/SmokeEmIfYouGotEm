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
    assert committed["schema"] == "raftsim.south_fork.a1_window_source_pull_preflight_review.v1"
    assert (
        committed["status"]
        == "nonpromotional_overcover_source_pull_preflight_passed_exact_anchor_pending"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_source_preflight_matches_downstream_ambiguity_window():
    preflight = _load_preflight()
    downstream = preflight["downstream_anchor_review"]

    assert downstream["current_seed_status"] == "missing_exact_anchor"
    assert downstream["exact_anchor_available"] is False
    assert downstream["source_mile_window"]["minimum_mile"] == 20.5
    assert downstream["source_mile_window"]["maximum_mile"] == 21.0
    assert downstream["final_window_id"] == "salmon_falls_folsom_review_32991_33796m"
    assert downstream["final_window_start_m"] == downstream["source_window_min_station_m"]
    assert downstream["final_window_end_m"] == downstream["source_window_max_station_m"]
    assert downstream["final_window_matches_source_mile_ambiguity"] is True


def test_south_fork_a1_window_source_preflight_allows_only_nonpromotional_source_pull():
    preflight = _load_preflight()
    readiness = preflight["execution_readiness"]
    gate = preflight["promotion_gate"]

    assert preflight["window_continuity"]["contiguous"] is True
    assert preflight["window_continuity"]["gap_count"] == 0
    assert readiness["can_execute_overcover_source_pull"] is True
    assert readiness["source_pull_task_count"] == 12
    assert readiness["expected_source_file_count"] == 12
    assert readiness["destination_missing_count"] == 12
    assert gate["can_download_source_files"] is True
    assert gate["can_promote_full_reach_corridor"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert "Unreal full-reach landscape import" in readiness["forbidden_use"]
