from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from raftsim.colorado_hance_visual_water import (
    MANIFEST_RELATIVE,
    NORMALIZATION_CAPS,
    PACKED_TEXTURE_RELATIVE,
    SCHEMA,
    build_colorado_hance_visual_water,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_RELATIVE = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "colorado_hance_reach_local_runnable_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_hance_visual_water_is_hydraulic_hash_locked_and_non_authoritative():
    manifest = json.loads((REPO_ROOT / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    assert manifest["schema"] == SCHEMA
    assert manifest["river_id"] == "colorado_river"
    assert manifest["flow_band"] == "moderate_release_planning"
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
    assert evidence["foam_eligible_cell_count"] > 0
    assert 430.0 <= evidence["strongest_column_station_m"] <= 500.0
    assert evidence["strongest_column_mean_froude"] > 0.9
    assert manifest["surface_relief_derivation"]["render_height_cap_cm"] == 9.0

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
    capture_filter = manifest["render_binding"]["capture_surface_filter"]
    assert capture_filter["schema"] == (
        "raftsim.presentation.plane_preserving_cardinal_5tap.v1"
    )
    assert capture_filter["center_weight"] == 0.44
    assert capture_filter["cardinal_neighbor_weight_each"] == 0.14
    assert capture_filter["neighbor_offset_m"] == 4.0
    assert capture_filter["wet_interior_only"] is True
    assert capture_filter["render_height_scale"] == 0.06
    capture_water = manifest["render_binding"]["capture_water_material"]
    assert capture_water["version"] == "V2"
    assert capture_water["blend_mode"] == "Translucent"
    assert capture_water["opacity_parameter"] == 0.9
    assert capture_water["refraction_ior"] == 1.333
    assert capture_water["collision_enabled"] is False
    assert capture_water["hidden_in_game"] is True
    assert manifest["render_binding"]["capture_foam_breakup"] == {
        "base_coverage": 0.22,
        "noise_smoothstep": [0.42, 0.74],
        "coverage_gain": 0.96,
        "maximum_opacity": 0.82,
    }
    assert manifest["render_binding"]["live_runtime_presentation"] == {
        "wet_cell_clipped_volume_core": True,
        "volume_core_material": (
            "/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
            "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2"
        ),
        "flow_normal": (
            "/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
            "T_RaftSim_ColoradoHanceWaterV1_FlowNormal"
        ),
        "foam_lace": (
            "/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
            "T_RaftSim_ColoradoHanceWaterV1_FoamLace"
        ),
        "calm_detail_skin_coverage": 0.035,
        "active_detail_skin_coverage": 0.14,
        "surface_smoothing_strength": 0.72,
        "standing_wave_scale": 0.55,
        "hydraulic_relief_scale": 0.55,
        "carrier_foam_intensity": 0.55,
        "rapid_foam_focus": [0.30, 0.82],
        "rapid_foam_coverage_gain": 0.82,
    }


def test_committed_hance_visual_water_matches_generator():
    committed_texture = (REPO_ROOT / PACKED_TEXTURE_RELATIVE).read_bytes()
    committed_manifest = (REPO_ROOT / MANIFEST_RELATIVE).read_bytes()
    build_colorado_hance_visual_water(REPO_ROOT)
    assert (REPO_ROOT / PACKED_TEXTURE_RELATIVE).read_bytes() == committed_texture
    assert (REPO_ROOT / MANIFEST_RELATIVE).read_bytes() == committed_manifest


def test_hance_runnable_review_retains_immutable_evidence_and_is_honest():
    review = json.loads((REPO_ROOT / REVIEW_RELATIVE).read_text(encoding="utf-8"))
    assert review["status"] == (
        "accepted_reference_runnable_photoreal_promotion_rejected"
    )
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["production_promoted"] is False
    assert review["decision"]["live_solver_owns_gameplay_rendering_and_forces"]
    assert review["decision"]["authored_capture_water_hidden_in_game"]
    assert review["coordinate_contract"][
        "maximum_static_to_runtime_centerline_surface_error_m"
    ] == 0.0
    assert review["terrain_authority"]["surveyed_hance_terrain"] is False
    assert len(review["required_external_acceptance_gates"]) == 6
    assert len(review["remaining_photoreal_defects"]) >= 6

    # The Hance presentation milestone supersedes the mutable saved map,
    # manifest, and current captures. Its review locks their current hashes;
    # this reach-local review continues to lock immutable terrain, coordinate,
    # solver-field, and source-package evidence.
    superseded_paths = {
        "unreal/Content/RaftSim/Maps/L_Hance.umap",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_guide_seat_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_solver_rapid_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_colorado_river.json",
        "unreal/Content/RaftSim/Rendering/SolverVisualizationFields/colorado_hance_moderate_visualization_manifest.json",
        "physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/hance_visual/hance_conditioned_heightfield_1009.png",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_paths:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
