from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
RUNTIME_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source"
TERRAIN_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoMaterial.cpp"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoWaterMaterial.cpp"
TEXTURE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealTextureAssets.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
CATALOG_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorEnvironmentCatalog.cpp"
GEOMETRY_SOURCE = EDITOR_ROOT / "Landscape/RaftSimEditorLandscapeGeometry.cpp"
WATER_CONFIG_HEADER = (
    RUNTIME_ROOT / "RaftSimWater/Public/RaftSimRiverWaterConfig.h"
)
LIVE_SURFACE_SOURCE = (
    RUNTIME_ROOT / "RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp"
)
MANIFEST = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_colorado_river.json"
)
REVIEW = MANIFEST.with_name(
    "colorado_hance_subcell_smoothed_water_lace_foam_v1_review.json"
)
V2_REVIEW = MANIFEST.with_name(
    "colorado_hance_transmitting_water_v2_review.json"
)
FLOW_NORMAL_SOURCE = REPO_ROOT / (
    "unreal/SourceArt/RaftSim/Water/ColoradoHance/"
    "T_RaftSim_ColoradoHance_FlowNormalV1.png"
)
FOAM_LACE_SOURCE = FLOW_NORMAL_SOURCE.with_name(
    "T_RaftSim_ColoradoHance_FoamLaceV1.png"
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
    assert "BLEND_Translucent" in water
    assert "TLM_SurfacePerPixelLighting" in water
    assert "EditorOnlyData->Opacity" in water
    assert "EditorOnlyData->Refraction" in water
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
        "bEnableLiveSolverVolumeCore = true",
        "LiveSurfaceCalmCoverage = 0.035f",
        "LiveSurfaceActiveCoverage = 0.14f",
        "LiveSkyReflectionStrength = 0.26f",
        "LiveRippleStrength = 0.24f",
        "LiveFoamIntensity = 0.55f",
        "LivePresentationSurfaceSmoothingStrength = 0.72f",
        "LivePresentationStandingWaveScale = 0.55f",
        "LivePresentationHydraulicReliefScale = 0.55f",
        "LiveRapidFoamFocusStart = 0.30f",
        "LiveRapidFoamFocusEnd = 0.82f",
        "LiveRapidFoamCoverageGain = 0.82f",
        "RaftSimColoradoHanceDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
        "RaftSimColoradoHanceSubcellSmoothedWaterV1",
        "RaftSimColoradoHanceLaceFoamV1",
        "LiveVolumeCoreMaterialOverride",
        "LiveWaterFlowNormalTexture",
        "LiveWaterFoamLaceTexture",
    ):
        assert token in geometry

    assert "Settings.SolverSurfaceReliefScale = 0.06f" in catalog
    assert "FoamBaseCoverage =" in geometry
    assert "bColoradoHancePresentation ? 0.22f : 0.28f" in geometry
    assert "bColoradoHancePresentation ? 0.42f : 0.34f" in geometry
    assert "bColoradoHancePresentation ? 0.74f : 0.70f" in geometry


def test_hance_live_smoothing_is_render_only_and_plane_preserving() -> None:
    config = WATER_CONFIG_HEADER.read_text(encoding="utf-8")
    runtime = LIVE_SURFACE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "bEnableLivePresentationSurfaceSmoothing",
        "LivePresentationSurfaceSmoothingStrength",
        "LivePresentationStandingWaveScale",
        "LivePresentationHydraulicReliefScale",
        "LiveRapidFoamFocusStart",
        "LiveRapidFoamFocusEnd",
        "LiveRapidFoamCoverageGain",
    ):
        assert token in config
    assert "ComputePresentationSmoothedSurfaceHeightMeters" in runtime
    assert "CenterSurfaceHeightMeters * 0.44f" in runtime
    assert "* 0.14f" in runtime
    assert "RawPresentationSurfaceHeightMeters" in runtime
    assert "WaterSamples remains the authority for gameplay" in runtime
    assert "PresentationSurfaceHeightMeters[Index]" in runtime


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
        "colorado_hance_transmitting_default_lit_river_local_normal_"
        "candidate_bound_cpu_depth_bank_opacity_and_cooked_field_color"
    )
    assert candidate["water_shading_model"] == "DefaultLit"
    assert candidate["water_blend_mode"] == "Translucent"
    assert candidate["water_surface_opacity"] == 0.90
    assert candidate["water_transmission_refraction_ior"] == 1.333
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
        "raftsim.environment.colorado_hance_subcell_smoothed_water_lace_foam_review.v1"
    )
    assert review["status"] == (
        "retained_technical_water_improvement_photoreal_promotion_fail"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["visual_improvement_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["solver_state_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert review["capture_contract"]["render_relief_cap_cm"] == 9.0
    assert review["capture_contract"]["normal_up_blend"] == 0.80
    assert review["runtime_contract"]["raw_water_samples_unchanged"] is True
    assert review["runtime_contract"]["presentation_array_only"] is True
    assert review["runtime_launch_diagnostics"]["surface_smoothing_enabled"] is True
    assert review["runtime_launch_diagnostics"]["launch_rapid_foam_vertices"] == 0
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    superseded_paths = {
        "unreal/Content/RaftSim/Maps/L_Hance.umap",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_colorado_river.json",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_guide_seat_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_river_solver_rapid_river_eye_downstream.png",
        "unreal/Content/RaftSim/Rendering/SolverVisualizationFields/colorado_hance_moderate_visualization_manifest.json",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorEnvironmentCatalog.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/RaftSimEditorLandscapeGeometry.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSurfaceActor.h",
        "unreal/Plugins/RaftSim/Source/RaftSimWater/Public/RaftSimRiverWaterConfig.h",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_paths:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_hance_v2_visual_textures_are_first_party_and_fail_closed() -> None:
    texture_source = TEXTURE_SOURCE.read_text(encoding="utf-8")
    for texture, asset_id in (
        (FLOW_NORMAL_SOURCE, "colorado_hance_flow_normal_v1"),
        (FOAM_LACE_SOURCE, "colorado_hance_foam_lace_v1"),
    ):
        provenance = json.loads(
            texture.with_suffix(".provenance.json").read_text(encoding="utf-8")
        )
        assert provenance["schema"] == (
            "raftsim.first_party.generated_texture_provenance.v1"
        )
        assert provenance["asset_id"] == asset_id
        assert provenance["project_ownership"] == (
            "first-party generated project asset"
        )
        assert provenance["texture"]["sha256"] == _sha256(texture)
        assert provenance["texture"]["width"] == 1254
        assert provenance["texture"]["height"] == 1254
        assert provenance["texture"]["addressing"] == "mirror_x_mirror_y"
        assert len(provenance["limitations"]) >= 4
    assert "BuildColoradoHanceWaterTextureAssets" in texture_source
    assert "TA_Mirror" in texture_source


def test_hance_transmitting_water_v2_review_is_hash_locked_and_honest() -> None:
    review = json.loads(V2_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.colorado_hance_transmitting_water_review.v2"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["colorado_hance_reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["transmitting_water_v2_retained"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["retained_runnable_map_package_changed"] is False
    assert decision["gameplay_water_geometry_changed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["collision_or_raft_forces_changed"] is False
    assert review["architecture"]["river_local_optics"][
        "calm_detail_skin_coverage"
    ] == 0.035
    assert review["live_pie_evidence"]["volume_core_enabled"] is True
    assert review["live_pie_evidence"]["volume_core_triangles"] > 0
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
