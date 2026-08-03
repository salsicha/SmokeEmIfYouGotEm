from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
)
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorFutaleufuWaterMaterial.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
CATALOG_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorEnvironmentCatalog.cpp"
GEOMETRY_SOURCE = EDITOR_ROOT / "Landscape/RaftSimEditorLandscapeGeometry.cpp"
RUNTIME_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimWaterSurfaceActor.cpp"
)
CONFIG_HEADER = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimWater/Public/"
    "RaftSimRiverWaterConfig.h"
)
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_futaleufu_terminator.json"
)
REVIEW = MANIFEST.with_name(
    "chilko_futaleufu_cold_water_v2_review.json"
)
RAPID_LACE_REVIEW = MANIFEST.with_name(
    "futaleufu_live_rapid_lace_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_futaleufu_water_is_native_moving_and_non_displacing() -> None:
    water = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Futaleufu_TerminatorDefaultLitWater" in water
    assert "MSM_DefaultLit" in water
    assert "BLEND_Opaque" in water
    assert "UMaterialExpressionSingleLayerWaterMaterialOutput" not in water
    assert water.count("AddNormalSample(") == 3
    assert "0.00031f" in water
    assert "0.00163f" in water
    assert "0.00673f" in water
    assert "EditorOnlyData->WorldPositionOffset" not in water
    assert "Landscape->Import" not in water
    assert "SetCollision" not in water
    assert 'Spec.RiverId == TEXT("futaleufu_terminator")' in base
    assert "LoadOrCreateFutaleufuTerminatorWaterParent" in base
    assert 'WaterNormalAssetName = TEXT("Pacuare")' not in base
    assert 'TEXT("T_RaftSim_%s_NormalAtlas")' in base
    assert "Hance, Terminator, and Chilko each sample their packed field once" in base


def test_futaleufu_capture_and_live_profiles_are_river_local() -> None:
    catalog = CATALOG_SOURCE.read_text(encoding="utf-8")
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    runtime = RUNTIME_SOURCE.read_text(encoding="utf-8")
    config = CONFIG_HEADER.read_text(encoding="utf-8")

    for token in (
        "Settings.BaseColorScale = 1.08f",
        "Settings.EmissiveFillScale = 0.140f",
        "Settings.NormalIntensity = 0.30f",
        "Settings.SurfaceVariationStrength = 0.44f",
        "Settings.VertexTintWeight = 0.76f",
    ):
        assert token in catalog
    for token in (
        "LiveSkyReflectionStrength = 0.34f",
        "LiveRippleStrength = 0.30f",
        "LiveFoamIntensity = 0.68f",
        "LiveRapidFoamFocusStart = 0.08f",
        "LiveRapidFoamFocusEnd = 0.58f",
        "RaftSimFutaleufuDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
        "RaftSimColdWaterCpuChopV2",
        "RaftSimColdWaterEmbeddedAerationV2",
    ):
        assert token in geometry
    for parameter in (
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
        "LiveRapidFoamFocusStart",
        "LiveRapidFoamFocusEnd",
    ):
        assert parameter in config
    for parameter in (
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
    ):
        assert f'TEXT("{parameter}")' in runtime


def test_futaleufu_manifest_records_native_capture_water() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "futaleufu_terminator"
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
        "M_RaftSim_Futaleufu_TerminatorDefaultLitWater"
    )
    assert candidate["water_material_status"] == (
        "futaleufu_terminator_default_lit_native_moving_normal_candidate_"
        "bound_cpu_cooked_field_color"
    )
    assert candidate["water_shading_model"] == "DefaultLit"
    assert candidate["water_blend_mode"] == "Opaque"
    assert candidate["water_solver_visualization_field_enable"] == 0.0
    assert candidate["water_solver_macro_normal_weight"] == 0.0
    assert candidate["water_solver_depth_color_weight"] == 0.0
    assert candidate["water_solver_field_roughness_weight"] == 0.0
    assert candidate["water_solver_froude_aeration_weight"] == 0.0
    assert candidate["water_solver_visualization_field_texture_count"] == 1
    assert candidate["water_solver_foam_status"] == (
        "capture_only_cooked_speed_froude_masked_noncolliding_surface_bound_"
        "hidden_in_game"
    )
    assert candidate["water_base_color_scale"] == 1.08
    assert candidate["water_vertex_tint_weight"] == 0.76
    assert candidate["water_emissive_fill_scale"] == 0.14
    assert candidate["water_reflection_fill_intensity"] == 0.10
    assert candidate["water_roughness"] == 0.24
    assert candidate["water_specular"] == 0.46
    assert candidate["water_normal_intensity"] == 0.30
    assert candidate["water_surface_variation_strength"] == 0.44
    assert candidate["water_solver_render_geometry_collision_enabled"] is False


def test_futaleufu_native_water_review_is_hash_locked_and_honest() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_futaleufu_cold_water_review.v2"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert review["decision"]["capture_ribbon_geometry_changed"] is True
    assert review["decision"]["gameplay_water_geometry_changed"] is False
    river = review["rivers"]["futaleufu_terminator"]
    assert river["moving_normal_layer_count"] == 3
    assert river["world_optical_scales_per_cm"] == [
        0.00031,
        0.00163,
        0.00673,
    ]
    assert river["ribbon_cross_section_steps"] == 48
    assert river["analytic_chop_scale"] == 0.78
    assert river["cross_current_chop_amplitude_cm"] == 8.0
    assert river["embedded_aeration_weight"] == 0.22
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    superseded_paths = {
        "unreal/Content/RaftSim/Maps/L_Terminator.umap",
        "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Materials/M_RaftSim_Futaleufu_TerminatorDefaultLitWater.uasset",
        "unreal/Content/RaftSim/Environment/ChilkoRun/Water/Materials/M_RaftSim_Chilko_LavaCanyonDefaultLitWater.uasset",
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_Futaleufu_PhysicalCorridorWaterCandidate.uasset",
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_Chilko_PhysicalCorridorWaterCandidate.uasset",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_futaleufu_terminator.json",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_chilko_river_lava_canyon.json",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/futaleufu_terminator_guide_seat_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/futaleufu_terminator_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/futaleufu_terminator_solver_rapid_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_guide_seat_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_solver_rapid_river_eye_downstream.png",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_paths:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_futaleufu_live_rapid_lace_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(RAPID_LACE_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.futaleufu_live_rapid_lace_review.v1"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["futaleufu_technical_candidate_retained"] is True
    assert decision["chilko_technical_candidate_retained"] is False
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["shared_calm_surface_material_changed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["raft_forces_changed"] is False
    assert review["futaleufu_terminator"]["focus_before"] == [0.12, 0.72]
    assert review["futaleufu_terminator"]["focus_retained"] == [0.08, 0.58]
    assert review["chilko_lava_canyon_rejected_bracket"]["restored_focus"] == [
        0.12,
        0.72,
    ]
    assert review["chilko_lava_canyon_rejected_bracket"][
        "visible_rapid_foam_vertices"
    ] == 0
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
