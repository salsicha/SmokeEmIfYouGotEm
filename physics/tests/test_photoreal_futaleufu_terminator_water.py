from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
)
TEXTURE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealTextureAssets.cpp"
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
COLD_WATER_VOLUME_CORE_REVIEW = MANIFEST.with_name(
    "cold_water_live_volume_core_v2_review.json"
)
V3_REVIEW = MANIFEST.with_name(
    "futaleufu_terminator_transmitting_water_v3_review.json"
)
HIGHLIGHT_REVIEW = MANIFEST.with_name(
    "cold_water_highlight_naturalism_v1_review.json"
)
DEPTH_ATTENUATION_REVIEW = MANIFEST.with_name(
    "cold_water_depth_attenuation_v2_review.json"
)
FLOW_NORMAL_SOURCE = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Water/FutaleufuTerminator/"
    "T_RaftSim_FutaleufuTerminator_FlowNormalV1.png"
)
FOAM_LACE_SOURCE = FLOW_NORMAL_SOURCE.with_name(
    "T_RaftSim_FutaleufuTerminator_FoamLaceV1.png"
)
CURRENT_FUTALEUFU_REGENERATED_ARTIFACTS = {
    "unreal/Content/RaftSim/Maps/L_Terminator.umap",
    "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Textures/T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal.uasset",
    "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Textures/T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace.uasset",
    "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Materials/MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3.uasset",
    "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Materials/M_RaftSim_Futaleufu_TerminatorDefaultLitWater.uasset",
    "unreal/Content/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_Futaleufu_PhysicalCorridorWaterCandidate.uasset",
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_futaleufu_terminator.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_futaleufu_water_is_native_moving_and_non_displacing() -> None:
    water = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Futaleufu_TerminatorDefaultLitWater" in water
    assert "MSM_DefaultLit" in water
    assert "BLEND_Translucent" in water
    assert "TLM_SurfacePerPixelLighting" in water
    assert "EditorOnlyData->Opacity" in water
    assert "EditorOnlyData->Refraction" in water
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
        "bEnableLiveSolverVolumeCore = true",
        "LiveSurfaceCalmCoverage = 0.035f",
        "LiveSurfaceActiveCoverage = 0.14f",
        "LiveSurfaceSpecular = 0.18f",
        "LiveSurfaceRoughness = 0.42f",
        "LiveSkyReflectionStrength = 0.05f",
        "LiveRippleStrength = 0.72f",
        "LiveFoamIntensity = 0.58f",
        "LiveRapidFoamFocusStart = 0.08f",
        "LiveRapidFoamFocusEnd = 0.58f",
        "FLinearColor(0.000035f, 0.000070f, 0.000110f, 0.0f)",
        "FLinearColor(0.0120f, 0.0080f, 0.0060f, 0.0f)",
        "FLinearColor(0.055f, 0.075f, 0.090f, 0.0f)",
        "LiveShallowWaterOpacity = 0.36f",
        "LiveOpticalDepthResponseExponent = 0.25f",
        "LiveDeepWaterOpacity = 0.86f",
        "LiveFoamWaterOpacity = 0.88f",
        "LiveVolumeCoreMaterialOverride",
        "LiveWaterFlowNormalTexture",
        "LiveWaterFoamLaceTexture",
        "RaftSimFutaleufuDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
        "RaftSimColdWaterCpuChopV2",
        "RaftSimColdWaterEmbeddedAerationV2",
        "RaftSimColdWaterHighlightNaturalismV1",
        "RaftSimColdWaterDepthAttenuationV2",
        "RaftSimColdWaterNonlinearOpticalDepthV1",
    ):
        assert token in geometry
    for token in (
        'SetScalar(TEXT("SpeedAerationFraction"), 0.025f)',
        'SetScalar(TEXT("ReachHueVariation"), 0.12f)',
        'SetScalar(TEXT("CalmSurfaceColorVariation"), 0.22f)',
        'SetScalar(TEXT("FallbackSkyReflectionFloor"), 0.08f)',
        'SetScalar(TEXT("FallbackSkyReflectionVariation"), 0.24f)',
        'SetScalar(TEXT("RippleGrazingFloor"), 0.75f)',
        'SetScalar(TEXT("SlickNormalFloor"), 0.85f)',
        'SetScalar(TEXT("SlickRoughnessScale"), 1.0f)',
        'SetScalar(TEXT("FresnelSpecular"), 0.01f)',
        'SetScalar(TEXT("OpticalDepthResponseExponent"), 0.25f)',
    ):
        assert token in WATER_SOURCE.read_text(encoding="utf-8")
    for token in (
        "Settings.SunIntensity = 2.40f",
        "Settings.SkyLightIntensity = 1.35f",
        "Settings.ExposureBias = -0.30f",
    ):
        assert token in catalog
    lighting = (
        EDITOR_ROOT / "Environment/RaftSimEditorNearFieldAndLighting.cpp"
    ).read_text(encoding="utf-8")
    assert "RaftSimColdWaterHighlightNaturalismV1" in lighting
    assert "bColdWaterHighlightNaturalism" in lighting
    for parameter in (
        "bEnableLiveSolverVolumeCore",
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
        "LiveOpticalDepthResponseExponent",
        "bEnforceTaggedDirectionalLightPresentation",
        "RuntimeDirectionalLightActorTag",
        "RuntimeDirectionalLightIntensity",
        "RuntimeDirectionalLightRotation",
        "LiveRapidFoamFocusStart",
        "LiveRapidFoamFocusEnd",
        "LiveVolumeCoreMaterialOverride",
        "LiveWaterFlowNormalTexture",
        "LiveWaterFoamLaceTexture",
    ):
        assert parameter in config
    for parameter in (
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
        "OpticalDepthResponseExponent",
    ):
        assert f'TEXT("{parameter}")' in runtime
    assert "bUsesMigratedColdWaterVolumeCore" in runtime
    water_config_runtime = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimWater/Private"
        / "RaftSimRiverWaterConfig.cpp"
    ).read_text(encoding="utf-8")
    assert "bMigratedFutaleufuHighlightResponse" in water_config_runtime
    assert "2.40f" in water_config_runtime
    assert "FRotator(-50.0f, 30.0f, 0.0f)" in water_config_runtime
    assert "SetIntensity(RuntimeDirectionalLightIntensity)" in water_config_runtime
    assert 'TEXT("futaleufu_river_chile")' in runtime
    assert "? 0.18f" in runtime
    assert "? 0.42f" in runtime
    assert "? 0.05f" in runtime
    assert "? 0.72f" in runtime
    assert "FLinearColor(0.008f, 0.055f, 0.130f, 1.0f)" in geometry
    assert "FLinearColor(0.001f, 0.014f, 0.050f, 1.0f)" in geometry
    assert "FLinearColor(0.018f, 0.080f, 0.160f, 1.0f)" in geometry
    assert "FLinearColor(0.008f, 0.055f, 0.130f, 1.0f)" in runtime
    assert "FLinearColor(0.001f, 0.014f, 0.050f, 1.0f)" in runtime
    assert "FLinearColor(0.018f, 0.080f, 0.160f, 1.0f)" in runtime
    assert "FLinearColor(0.000035f, 0.000070f, 0.000110f, 0.0f)" in runtime
    assert "FLinearColor(0.0120f, 0.0080f, 0.0060f, 0.0f)" in runtime
    assert "FLinearColor(0.055f, 0.075f, 0.090f, 0.0f)" in runtime
    assert "? 0.025f" in runtime
    assert 'TEXT("SpeedAerationFraction")' in runtime
    assert "kLiveVolumeCoreMinimumStationCoverage = 0.60f" in runtime
    assert "MinimumCellStationCoverage" in runtime
    assert 'TEXT("WaterFlowNormalPrimary")' in runtime
    assert 'TEXT("WhitewaterFoamLace")' in runtime
    assert 'TEXT("SolverOverlayFoamLace")' in runtime


def test_futaleufu_manifest_records_native_capture_water() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "futaleufu_terminator"
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
        "M_RaftSim_Futaleufu_TerminatorDefaultLitWater"
    )
    assert candidate["water_material_status"] == (
        "futaleufu_terminator_transmitting_default_lit_river_local_normal_"
        "candidate_bound_cpu_depth_bank_opacity_and_cooked_field_color"
    )
    assert candidate["water_shading_model"] == "DefaultLit"
    assert candidate["water_blend_mode"] == "Translucent"
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


def test_cold_water_depth_attenuation_v2_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(DEPTH_ATTENUATION_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.cold_water_depth_attenuation_review.v2"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["cold_water_depth_attenuation_v2_retained"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["production_promoted"] is False
    for unchanged in (
        "terrain_geometry_changed",
        "water_geometry_changed",
        "hydraulics_changed",
        "wet_dry_mask_changed",
        "bathymetry_changed",
        "collision_changed",
        "buoyancy_or_raft_forces_changed",
        "raft_interior_transmission_changed",
        "solver_foam_authority_changed",
    ):
        assert review["decision"][unchanged] is False

    comparison = review["visual_comparison"]
    fut_base = comparison["futaleufu_baseline"]
    fut_retained = comparison["futaleufu_retained"]
    chilko_base = comparison["chilko_baseline"]
    chilko_retained = comparison["chilko_retained"]
    assert fut_retained["mean_luminance"] < fut_base["mean_luminance"] * 0.98
    assert (
        fut_retained["right_body_mean_luminance"]
        < fut_base["right_body_mean_luminance"] * 0.95
    )
    assert (
        fut_retained["luminance_standard_deviation"]
        > fut_base["luminance_standard_deviation"] * 1.15
    )
    assert chilko_retained["mean_luminance"] < chilko_base["mean_luminance"] * 0.80
    assert chilko_retained["p95_luminance"] < chilko_base["p95_luminance"] * 0.96
    assert (
        chilko_retained["far_band_mean_luminance"]
        < chilko_base["far_band_mean_luminance"] * 0.87
    )
    assert chilko_retained["fraction_over_0_95"] < 0.001
    assert len(review["required_external_acceptance_gates"]) == 6
    assert all(reviewer is None for reviewer in review["reviewers"].values())

    for artifact in review["retained_artifacts"]:
        if artifact["path"] in CURRENT_FUTALEUFU_REGENERATED_ARTIFACTS:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        assert _sha256(path) == artifact["sha256"], artifact["path"]


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

    # The later rapid-approach and volume-core reviews supersede only the
    # versioned Lava Canyon map package from this two-river historical review.
    # Continue hash-locking the Terminator map, material, and all captures this
    # review still owns instead of rewriting its original evidence payload.
    superseded_artifacts = {
        "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "unreal/Content/RaftSim/Maps/L_Terminator.umap",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_artifacts:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_futaleufu_v3_visual_textures_are_first_party_and_fail_closed() -> None:
    texture_source = TEXTURE_SOURCE.read_text(encoding="utf-8")
    for texture, asset_id, map_kind in (
        (
            FLOW_NORMAL_SOURCE,
            "futaleufu_terminator_flow_normal_v1",
            "project_owned_patagonian_multiscale_river_flow_normal",
        ),
        (
            FOAM_LACE_SOURCE,
            "futaleufu_terminator_foam_lace_v1",
            "project_owned_patagonian_solver_masked_whitewater_lace",
        ),
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
        assert len(provenance["limitations"]) >= 4
        assert map_kind in texture_source
    assert "TA_Mirror" in texture_source
    assert "solver_masked" in texture_source


def test_cold_water_volume_core_v2_review_is_hash_locked_and_honest() -> None:
    review = json.loads(COLD_WATER_VOLUME_CORE_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.cold_water_live_volume_core_review.v2"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["futaleufu_reference_runnable"] is True
    assert decision["chilko_reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["volume_core_retained"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["collision_or_raft_forces_changed"] is False
    assert review["architecture"]["minimum_core_station_coverage"] == 0.60
    assert review["architecture"]["lateral_core_rule"] == (
        "all four sampled cell vertices must be wet"
    )
    assert review["live_pie_evidence"]["futaleufu_terminator"][
        "volume_core_triangles"
    ] == 2438
    assert review["live_pie_evidence"]["chilko_lava_canyon"][
        "volume_core_triangles"
    ] == 1632
    assert review["visual_comparison"]["futaleufu_terminator"][
        "retained_water_band_blue_minus_red"
    ] > 0.0
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_futaleufu_transmitting_water_v3_review_is_hash_locked_and_honest() -> None:
    review = json.loads(V3_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.futaleufu_terminator_transmitting_water_review.v3"
    )
    assert review["status"] == (
        "technical_optical_candidate_retained_photoreal_and_external_"
        "acceptance_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["futaleufu_reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["transmitting_water_v3_retained"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["retained_runnable_map_package_changed"] is False
    assert decision["gameplay_water_geometry_changed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["collision_or_raft_forces_changed"] is False
    assert review["live_pie_evidence"]["volume_core_triangles"] == 2438
    assert review["live_pie_evidence"]["active_breaking_sites"] == 5
    baseline = review["visual_comparison"]["baseline_v2"]
    retained = review["visual_comparison"]["retained_v3"]
    assert retained["mean_luminance"] < baseline["mean_luminance"]
    assert (
        retained["highlight_fraction_gt_0_90"]
        < baseline["highlight_fraction_gt_0_90"]
    )
    assert retained["mean_blue_minus_red"] > baseline["mean_blue_minus_red"]
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        if artifact["path"] in CURRENT_FUTALEUFU_REGENERATED_ARTIFACTS:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_cold_water_highlight_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(HIGHLIGHT_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.cold_water_highlight_naturalism_review.v1"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["futaleufu_reference_runnable"] is True
    assert decision["chilko_reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["first_futaleufu_chroma_bracket_rejected"] is True
    assert decision["chilko_used_as_no_regression_control"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["terrain_geometry_changed"] is False
    assert decision["water_geometry_changed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["wet_dry_mask_changed"] is False
    assert decision["bathymetry_changed"] is False
    assert decision["collision_changed"] is False
    assert decision["buoyancy_or_raft_forces_changed"] is False

    comparison = review["visual_comparison"]
    baseline = comparison["futaleufu_baseline"]
    retained = comparison["futaleufu_retained"]
    assert retained["mean_luminance"] < baseline["mean_luminance"]
    assert retained["p95_luminance"] < baseline["p95_luminance"]
    assert retained["fraction_over_0_90"] < baseline["fraction_over_0_90"]
    assert retained["fraction_over_0_95"] < (
        baseline["fraction_over_0_95"] * 0.025
    )
    assert retained["mean_blue_minus_red"] > (
        baseline["mean_blue_minus_red"] * 1.25
    )

    control_before = comparison["chilko_baseline_control"]
    control_after = comparison["chilko_retained_control"]
    assert abs(
        control_after["mean_luminance"] - control_before["mean_luminance"]
    ) < 0.0001
    assert abs(
        control_after["p95_luminance"] - control_before["p95_luminance"]
    ) < 0.0001
    assert abs(
        control_after["mean_blue_minus_red"]
        - control_before["mean_blue_minus_red"]
    ) < 0.0001
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6

    superseded_by_depth_v2 = {
        "unreal/Content/RaftSim/Maps/L_Terminator.umap",
        "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "unreal/Content/RaftSim/Environment/FutaleufuRun/Water/Materials/MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3.uasset",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_by_depth_v2:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
