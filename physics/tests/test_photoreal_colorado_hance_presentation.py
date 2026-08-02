from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
TERRAIN_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoMaterial.cpp"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoWaterMaterial.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
CATALOG_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorEnvironmentCatalog.cpp"
GEOMETRY_SOURCE = EDITOR_ROOT / "Landscape/RaftSimEditorLandscapeGeometry.cpp"
MANIFEST = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_colorado_river.json"
)
REVIEW = MANIFEST.with_name(
    "colorado_hance_organic_terrain_native_water_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_hance_organic_terrain_is_multiscale_and_non_displacing() -> None:
    terrain = TERRAIN_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "BuildColoradoOrganicHanceBaseColor" in terrain
    for scale in ("0.00014f", "0.00053f", "0.00230f", "0.00680f"):
        assert scale in terrain
    for token in (
        "ColoradoSandyBenchTint",
        "ColoradoWeatheredRockTint",
        "ColoradoDarkBasementRockTint",
        "ColoradoIronCliffTint",
        "ColoradoPaleTalusTint",
    ):
        assert token in terrain
    assert "WorldPositionOffset" not in terrain
    assert "Landscape->Import" not in terrain
    assert "SetCollision" not in terrain
    assert "BuildColoradoOrganicHanceBaseColor" in base


def test_hance_water_is_native_moving_and_samples_cooked_color_once() -> None:
    water = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Colorado_HanceDefaultLitWater" in water
    assert "MSM_DefaultLit" in water
    assert "BLEND_Opaque" in water
    assert "UMaterialExpressionSingleLayerWaterMaterialOutput" not in water
    assert water.count("AddNormalSample(") == 2
    assert "0.00029f" in water
    assert "0.00141f" in water
    assert "EditorOnlyData->WorldPositionOffset" not in water
    assert "Landscape->Import" not in water
    assert "SetCollision" not in water
    assert 'Spec.RiverId == TEXT("colorado_river")' in base
    assert "LoadOrCreateColoradoHanceWaterParent" in base
    assert "Hance, Terminator, and Chilko each sample their packed field once" in base


def test_hance_capture_and_live_profiles_are_river_local() -> None:
    catalog = CATALOG_SOURCE.read_text(encoding="utf-8")
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")

    for token in (
        "Settings.BaseColorScale = 1.06f",
        "Settings.EmissiveFillScale = 0.20f",
        "Settings.NormalIntensity = 0.30f",
        "Settings.SurfaceVariationStrength = 0.32f",
        "Settings.VertexTintWeight = 0.74f",
    ):
        assert token in catalog
    for token in (
        "LiveSkyReflectionStrength = 0.34f",
        "LiveRippleStrength = 0.30f",
        "LiveFoamIntensity = 0.76f",
        "RaftSimColoradoHanceDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
    ):
        assert token in geometry


def test_hance_manifest_records_organic_terrain_and_native_water() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "colorado_river"
    assert candidate["map_package"] == "/Game/RaftSim/Maps/L_Hance"
    assert candidate["runnable_gameplay_status"] == (
        "reference_runnable_colorado_hance_live_cooked_water_player_raft_and_game_mode"
    )
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"] == (
        "colorado_hance_v1_four_scale_world_space_sandy_bench_weathered_iron_"
        "cliff_dark_rock_talus_and_fine_grain_response"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == [
        0.00014,
        0.00053,
        0.0023,
        0.0068,
    ]
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
        "M_RaftSim_Colorado_HanceDefaultLitWater"
    )
    assert candidate["water_material_status"] == (
        "colorado_hance_default_lit_native_moving_normal_candidate_"
        "bound_cpu_cooked_field_color"
    )
    assert candidate["water_shading_model"] == "DefaultLit"
    assert candidate["water_blend_mode"] == "Opaque"
    assert candidate["water_solver_visualization_field_enable"] == 0.0
    assert candidate["water_solver_macro_normal_weight"] == 0.0
    assert candidate["water_solver_depth_color_weight"] == 0.0
    assert candidate["water_solver_field_roughness_weight"] == 0.0
    assert candidate["water_solver_froude_aeration_weight"] == 0.0
    assert candidate["water_base_color_scale"] == 1.06
    assert candidate["water_vertex_tint_weight"] == 0.74
    assert candidate["water_emissive_fill_scale"] == 0.20
    assert candidate["water_reflection_fill_intensity"] == 0.14
    assert candidate["water_roughness"] == 0.25
    assert candidate["water_specular"] == 0.46
    assert candidate["water_normal_intensity"] == 0.30
    assert candidate["water_surface_variation_strength"] == 0.32
    assert candidate["water_solver_render_geometry_collision_enabled"] is False


def test_hance_presentation_review_is_hash_locked_and_honest() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.colorado_hance_organic_terrain_native_water_review.v1"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_geometry_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert review["capture_water"]["cross_river_shader_field_reuse"] is False
    assert review["capture_water"]["native_normal_atlas"] is True
    assert review["capture_water"]["moving_normal_layer_count"] == 2
    assert review["capture_water"]["world_optical_scales_per_cm"] == [
        0.00029,
        0.00141,
    ]
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
