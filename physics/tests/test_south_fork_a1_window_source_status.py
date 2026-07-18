import json
from pathlib import Path

from raftsim.south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
    build_south_fork_a1_window_source_pull_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_status() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_source_pull_status_is_reproducible():
    generated = build_south_fork_a1_window_source_pull_status(REPO_ROOT)
    committed = _load_status()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_window_source_pull_status.v1"
    assert committed["status"] == "ready_for_stitched_validation_review"
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_source_pull_status_records_current_downloaded_files():
    status = _load_status()
    summary = status["summary"]

    assert summary["window_count"] == 8
    assert summary["expected_source_file_count"] == 16
    assert summary["present_source_file_count"] == 16
    assert summary["missing_source_file_count"] == 0
    assert summary["expected_window_manifest_count"] == 8
    assert summary["present_window_manifest_count"] == 8
    assert summary["missing_window_manifest_count"] == 0
    assert summary["present_existing_pilot_artifact_count"] == 1
    assert summary["expected_review_derivative_count"] == 32
    assert summary["present_review_derivative_count"] == 32
    assert summary["missing_review_derivative_count"] == 0
    assert summary["unexpected_file_count"] == 0
    assert summary["all_source_files_present"] is True
    assert summary["all_window_manifests_present"] is True


def test_south_fork_a1_window_source_pull_status_keeps_official_urls_and_hashes():
    status = _load_status()

    for window in status["windows"]:
        assert window["status"] == "source_files_and_window_manifest_present_review_pending"
        assert window["can_generate_window_derivatives"] is True
        assert window["can_enter_stitched_validation"] is True
        assert "3DEPElevation/ImageServer/exportImage" in window["terrain_dem"]["official_export_url"]
        assert "NAIP/USDA_CONUS_PRIME/ImageServer/exportImage" in window["aerial_imagery"]["official_export_url"]
        assert window["terrain_dem"]["byte_count"] > 0
        assert len(window["terrain_dem"]["sha256"]) == 64
        assert window["aerial_imagery"]["byte_count"] > 0
        assert len(window["aerial_imagery"]["sha256"]) == 64
        assert window["window_manifest"]["byte_count"] > 0
        assert len(window["window_manifest"]["sha256"]) == 64
        assert window["review_derivative_expected_count"] == 4
        assert window["review_derivative_present_count"] == 4
        for derivative in window["review_derivatives"]:
            assert derivative["byte_count"] > 0
            assert len(derivative["sha256"]) == 64


def test_south_fork_a1_window_source_pull_status_blocks_promotion_until_review():
    status = _load_status()
    gate = status["promotion_gate"]

    assert gate["can_promote_full_reach_corridor"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert gate["can_enter_stitched_validation_review"] is True
    assert len(gate["exit_criteria"]) == 5
