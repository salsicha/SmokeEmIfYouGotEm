import json
from pathlib import Path

from PIL import Image

from raftsim.south_fork_a1_window_derivatives import (
    FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH,
    build_south_fork_a1_window_derivative_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_derivative_manifest_is_reproducible():
    generated = build_south_fork_a1_window_derivative_manifest(REPO_ROOT)
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_full_reach_window_derivatives.v1"
    assert committed["status"] == "review_derivatives_generated_anchor_and_bank_review_pending"
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_derivatives_cover_every_window_and_artifact_class():
    manifest = _load_manifest()
    summary = manifest["summary"]

    assert summary["window_count"] == 8
    assert summary["seam_count"] == 7
    assert summary["derived_png_count"] == 24
    assert summary["edge_report_count"] == 8
    assert summary["heightfield_count"] == 8
    assert summary["hillshade_count"] == 8
    assert summary["naip_centerline_preview_count"] == 8
    assert summary["all_route_overlays_drawn"] is True
    assert len(manifest["windows"]) == 8
    basis_by_id = {
        window["window_id"]: window["route_overlay"]["route_basis"]
        for window in manifest["windows"]
    }
    assert basis_by_id["below_full_run_alias_33796_41500m"] == "adopted_route_axis"
    assert basis_by_id["salmon_falls_takeout_approach_41500_49077m"] == "adopted_route_axis"
    assert basis_by_id["chili_bar_existing_pilot_0_2500m"] == (
        "directed_route_clip_21_0_mile_candidate"
    )


def test_south_fork_a1_window_derivative_images_and_edge_reports_exist():
    manifest = _load_manifest()
    expected_modes = {
        "heightfield": "I;16",
        "hillshade": "L",
        "naip_centerline_preview": "RGB",
    }
    expected_sizes = {
        "heightfield": (2017, 2017),
        "hillshade": (2048, 2048),
        "naip_centerline_preview": (2048, 2048),
    }

    for window in manifest["windows"]:
        edge_report_path = REPO_ROOT / window["edge_report"]["path"]
        edge_report = json.loads(edge_report_path.read_text(encoding="utf-8"))
        assert len(window["edge_report"]["sha256"]) == 64
        assert edge_report["window_id"] == window["window_id"]
        assert edge_report["route_overlay"]["line_drawn"] is True
        assert edge_report["route_overlay"]["visible_pixel_count"] >= 2

        for artifact_kind, artifact in window["derived_artifacts"].items():
            image_path = REPO_ROOT / artifact["path"]
            assert image_path.exists()
            assert len(artifact["sha256"]) == 64
            with Image.open(image_path) as image:
                assert image.size == expected_sizes[artifact_kind]
                assert image.mode == expected_modes[artifact_kind]


def test_south_fork_a1_window_derivatives_keep_production_gates_closed():
    manifest = _load_manifest()
    gate = manifest["promotion_gate"]

    assert gate["can_enter_visual_derivative_review"] is True
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert gate["can_promote_full_reach_corridor"] is False

    for window in manifest["windows"]:
        window_gate = window["promotion_gate"]
        assert window_gate["can_enter_visual_derivative_review"] is True
        assert window_gate["can_import_unreal_landscape"] is False
        assert window_gate["can_bind_named_rapid_geometry"] is False
        assert window_gate["can_bind_solver_windows"] is False
        assert window_gate["can_promote_full_reach_corridor"] is False
