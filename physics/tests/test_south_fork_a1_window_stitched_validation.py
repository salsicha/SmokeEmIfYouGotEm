import json
from pathlib import Path

from raftsim.south_fork_a1_window_stitched_validation import (
    FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH,
    build_south_fork_a1_window_stitched_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_report() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_stitched_validation_report_is_reproducible():
    generated = build_south_fork_a1_window_stitched_validation_report(REPO_ROOT)
    committed = _load_report()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_full_reach_window_stitched_validation.v1"
    )
    assert committed["status"] == (
        "stitched_source_window_validation_ready_derivatives_pending"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_stitched_validation_covers_windows_and_seams():
    report = _load_report()
    summary = report["summary"]

    assert summary["window_count"] == 8
    assert summary["seam_count"] == 7
    assert summary["all_window_manifests_present"] is True
    assert summary["all_source_files_present"] is True
    assert summary["all_hashes_recorded"] is True
    assert summary["station_gap_count"] == 0
    assert summary["station_overlap_count"] == 0
    assert summary["can_generate_stitched_validation_derivatives"] is True
    assert summary["can_import_unreal_full_reach_landscape"] is False
    assert len(report["windows"]) == 8
    assert len(report["seams"]) == 7
    assert report["windows"][-1]["window_id"] == "salmon_falls_takeout_approach_41500_49077m"
    assert report["windows"][-1]["station_range_m"]["end"] == 49077.732


def test_south_fork_a1_window_stitched_validation_keeps_every_seam_visible():
    report = _load_report()

    for seam in report["seams"]:
        assert seam["station_contiguous"] is True
        assert seam["station_gap_m"] == 0.0
        assert seam["station_overlap_m"] == 0.0
        assert seam["review_required"] is True
        assert seam["can_hide_physics_errors"] is False
        assert "source_bbox_relationship" in seam
        assert "source_grid_relationship" in seam
        assert seam["source_grid_relationship"]["same_crs"] is True
        assert seam["source_grid_relationship"]["dem_dimension_match"] is True
        assert seam["source_grid_relationship"]["aerial_dimension_match"] is True


def test_south_fork_a1_window_stitched_validation_blocks_production_promotion():
    report = _load_report()
    gate = report["promotion_gate"]

    assert gate["can_generate_stitched_validation_derivatives"] is True
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert gate["can_promote_full_reach_corridor"] is False
    assert "Generate hillshade" in gate["next_required_actions"][0]

    for window in report["windows"]:
        assert window["manifest_present"] is True
        assert window["source_hashes_recorded"] is True
        assert window["can_enter_stitched_validation_review"] is True
        assert window["can_generate_window_derivatives"] is True
        assert window["can_import_unreal_landscape"] is False
        assert window["production_promoted"] is False
