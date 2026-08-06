from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from raftsim.pacuare_upper_huacas_visual_water import (
    MANIFEST_RELATIVE,
    NORMALIZATION_CAPS,
    PACKED_TEXTURE_RELATIVE,
    SCHEMA,
    build_pacuare_upper_huacas_visual_water,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pacuare_visual_water_is_hydraulic_hash_locked_and_non_authoritative():
    manifest = json.loads((REPO_ROOT / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    assert manifest["schema"] == SCHEMA
    assert manifest["river_id"] == "pacuare"
    assert manifest["flow_band"] == "rainfed_runnable_planning"
    assert manifest["normalization"]["caps"] == NORMALIZATION_CAPS
    assert manifest["solver_evidence"]["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_evidence"]["feature_strength_scale"] == 0.0
    assert manifest["solver_evidence"]["converged"] is False
    assert manifest["solver_evidence"]["production_promoted"] is False

    for artifact in manifest["source_artifacts"].values():
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert path.stat().st_size == artifact["size_bytes"]
        assert _sha256(path) == artifact["sha256"]

    evidence = manifest["hydraulic_visualization_evidence"]
    assert evidence["supercritical_cell_count"] > 0
    assert evidence["foam_eligible_cell_count"] > evidence["supercritical_cell_count"]
    assert 280.0 <= evidence["strongest_column_station_m"] <= 300.0
    assert evidence["strongest_column_mean_froude"] > 1.0
    assert manifest["surface_relief_derivation"]["render_height_cap_cm"] == 18.0

    texture_path = REPO_ROOT / PACKED_TEXTURE_RELATIVE
    assert manifest["texture"]["path"] == str(PACKED_TEXTURE_RELATIVE)
    assert _sha256(texture_path) == manifest["texture"]["sha256"]
    with Image.open(texture_path) as image:
        assert image.mode == "RGBA"
        assert image.size == (1024, 256)
        assert all(high > low for low, high in image.getextrema())

    authority = manifest["authority_policy"]
    assert authority["physical_authority"] == "live_custom_cxx_shallow_water_solver"
    assert authority["changes_collision_or_raft_forces"] is False
    assert authority["changes_solver_state"] is False
    assert authority["changes_cooked_fields"] is False
    assert authority["may_be_used_as_production_calibration_evidence"] is False
    assert manifest["render_binding"]["capture_only"] is True
    assert manifest["render_binding"]["hidden_in_game"] is True
    assert manifest["render_binding"]["collision_enabled"] is False


@pytest.mark.xfail(
    sys.platform != "darwin",
    reason=(
        "Committed bytes are macOS-generated; ~1-ulp libm differences shift the "
        "quantized pixels/floats on other platforms, so byte-identical regeneration "
        "is only expected on the generating platform."
    ),
    strict=False,
)
def test_committed_pacuare_visual_water_matches_generator(tmp_path: Path):
    # Regenerate into tmp: the committed artifacts are never touched, so a
    # divergent regeneration cannot cascade into later hash-lock tests.
    build_pacuare_upper_huacas_visual_water(REPO_ROOT, output_dir=tmp_path)
    assert (tmp_path / PACKED_TEXTURE_RELATIVE.name).read_bytes() == (
        REPO_ROOT / PACKED_TEXTURE_RELATIVE
    ).read_bytes()
    assert (tmp_path / MANIFEST_RELATIVE.name).read_bytes() == (
        REPO_ROOT / MANIFEST_RELATIVE
    ).read_bytes()


def test_pacuare_solver_whitewater_review_is_hash_locked_and_honest():
    review_path = (
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "pacuare_upper_huacas_solver_whitewater_v2_review.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["status"] == (
        "accepted_capture_readability_photoreal_promotion_rejected"
    )
    assert review["decision"]["capture_reads_as_moving_whitewater"] is True
    assert review["decision"]["production_promoted"] is False
    assert review["decision"]["authored_capture_water_hidden_in_game"] is True
    assert review["authority_boundary"]["capture_derivative_changes_solver_state"] is False
    assert review["cooked_field_evidence"]["converged"] is False
    assert review["technical_acceptance"]["runtime_launch_rapid_foam_vertices"] == 0
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        if artifact.get("hash_locked", True):
            assert _sha256(path) == artifact["sha256"]
