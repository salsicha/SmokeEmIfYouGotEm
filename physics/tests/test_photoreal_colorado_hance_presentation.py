from __future__ import annotations

import hashlib
import json
from pathlib import Path
from raftsim.editor_source_layout import read_base_material_source
from raftsim.editor_source_layout import LandscapeFoliageSourceSet, read_landscape_foliage_source


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
RUNTIME_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source"
TERRAIN_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoMaterial.cpp"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorColoradoWaterMaterial.cpp"
TEXTURE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealTextureAssets.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
CATALOG_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorEnvironmentCatalog.cpp"
GEOMETRY_SOURCE = EDITOR_ROOT / "Landscape/RaftSimEditorLandscapeGeometry.cpp"
FOLIAGE_SOURCE = LandscapeFoliageSourceSet(REPO_ROOT)
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
V3_TERRAIN_ECOLOGY_REVIEW = MANIFEST.with_name(
    "colorado_hance_nonperiodic_canyon_dryland_ecology_v3_review.json"
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


# These reviews hash-locked the interpreted 600 m Hance map. On 2026-09-26 it
# was replaced by the evidence-based geographic reach (2021 corridor DEM and
# orthophoto, 2014 sonar pools, labelled inferred rapid bed). The reviews stay
# as historical records; their locked map and captures are no longer shipped.
SUPERSEDING_REVIEW = REPO_ROOT / (
    "docs/reconstruction-review-2026-09-07/colorado-hance-evidence.md"
)


def _assert_superseded_by_evidence_reconstruction(review: dict) -> None:
    assert SUPERSEDING_REVIEW.is_file()
    locked_maps = [
        artifact for artifact in review["retained_artifacts"]
        if artifact["path"] == "unreal/Content/RaftSim/Maps/L_Hance.umap"
    ]
    assert locked_maps
    for artifact in locked_maps:
        assert _sha256(REPO_ROOT / artifact["path"]) != artifact["sha256"]


def test_hance_organic_terrain_is_multiscale_and_non_displacing() -> None:
    terrain = TERRAIN_SOURCE.read_text(encoding="utf-8")
    base = read_base_material_source(REPO_ROOT)

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
    base = read_base_material_source(REPO_ROOT)

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


def test_hance_live_smoothing_uses_shared_render_and_support_kernel() -> None:
    config = WATER_CONFIG_HEADER.read_text(encoding="utf-8")
    runtime = LIVE_SURFACE_SOURCE.read_text(encoding="utf-8")
    adapter = (RUNTIME_ROOT / "RaftSimWater/Private/RaftSimWaterRuntimeAdapter.cpp").read_text(encoding="utf-8")

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
    # The old render-only contract predates shared raft support. Keep this
    # wiring check separate from native numeric tests and historical captures.
    wrapper = runtime.split("float ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(", 1)[1].split("float ARaftSimWaterSurfaceActor::ComputeRaftHullSurfaceExclusion(", 1)[0]
    assert "return URaftSimWaterRuntimeAdapter::" in wrapper
    assert "ComputeCoupledSmoothedSurfaceHeightMeters(" in wrapper
    assert "WaterAdapter->ConfigureRaftSupportSurface(" in runtime
    assert "CenterSurfaceHeightMeters * 0.44f" in adapter
    assert "* 0.14f" in adapter
    assert "OutHeightM = ComputeCoupledSmoothedSurfaceHeightMeters(" in adapter
    assert "RaftSupportSurfaceSmoothingStrength);" in adapter
    assert "PresentationSurfaceHeightMeters[Index]" in runtime


def test_hance_dryland_ecology_v2_is_organic_and_non_authoritative() -> None:
    foliage = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "M_RaftSim_Hance_OpaqueDrylandVegetationV2",
        "SM_RaftSim_Hance_DesertShrub_A_OpaqueV2",
        "SM_RaftSim_Hance_DesertShrub_B_OpaqueV2",
        "SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2",
        "SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2",
        "HanceDrylandGroundCoverInstanceCount = 3000",
        "HanceDrylandShrubInstanceCount = 480",
        "HanceDrylandMinimumGroundCoverInstanceCount = 2700",
        "HanceDrylandMinimumShrubInstanceCount = 420",
        "FMath::Lerp(\n                32.0f,\n                78.0f",
        "FMath::Lerp(\n                78.0f,\n                195.0f",
        "RaftSimHanceOpaqueDrylandVegetationV2",
        "RaftSimOfficialReferenceConstrainedProceduralGapFill",
        "RaftSimOutsideProtectedSolverStrip",
        "RaftSimNoEcologyAuthority",
        "RaftSimNoGeographyAuthority",
        "RaftSimNoHydraulicAuthority",
    ):
        assert token in foliage
    assert "RaftSimHanceOpaqueDrylandVegetationV1" not in foliage
    assert "SM_RaftSim_Hance_DesertShrub_A_OpaqueV1" not in foliage
    assert "SM_RaftSim_Hance_DryGroundCover_A_OpaqueV1" not in foliage


def test_hance_v3_terrain_ecology_review_is_hash_locked_and_honest() -> None:
    review = json.loads(V3_TERRAIN_ECOLOGY_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.colorado_hance_nonperiodic_canyon_"
        "dryland_ecology_review.v3"
    )
    assert review["status"] == (
        "retained_technical_visual_improvement_photoreal_promotion_fail"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["visual_improvement_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["protected_solver_strip_changed"] is False
    assert review["decision"]["runtime_coordinate_map_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert review["terrain_contract"]["protected_strip_max_absolute_change_m"] == 0.0
    assert review["terrain_contract"]["maximum_outer_cross_bank_grade"] == 1.18
    assert (
        review["terrain_contract"][
            "outer_canyon_dominant_band_energy_ratio_after"
        ]
        < review["terrain_contract"][
            "outer_canyon_dominant_band_energy_ratio_before"
        ]
    )
    assert review["vegetation_contract"]["procedural_ground_cover_instances"] == 3000
    assert review["vegetation_contract"]["procedural_desert_shrub_instances"] == 480
    assert review["vegetation_contract"]["hierarchical_instanced_mesh_components"] == 4
    assert review["vegetation_contract"]["collision_enabled"] is False
    assert review["vegetation_contract"]["ecology_authority"] is False
    assert review["vegetation_contract"]["geography_authority"] is False
    assert review["vegetation_contract"]["hydraulic_authority"] is False
    assert len(review["remaining_photoreal_defects"]) >= 7
    assert len(review["required_external_acceptance_gates"]) == 6

    _assert_superseded_by_evidence_reconstruction(review)


def test_hance_manifest_records_evidence_drape_and_native_water() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "colorado_river"
    assert candidate["map_package"] == "/Game/RaftSim/Maps/L_Hance"
    assert candidate["runnable_gameplay_status"] == (
        "reference_runnable_colorado_hance_live_cooked_water_player_raft_and_game_mode"
    )
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"] == (
        "colorado_hance_evidence_2021_orthophoto_drape_albedo_scaled_no_procedural_palette"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == []
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

    _assert_superseded_by_evidence_reconstruction(review)


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
    assert "TA_Wrap" in texture_source


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

    supersession = review["superseded_mutable_artifacts_by"]
    successor = REPO_ROOT / supersession["review_path"]
    assert successor.is_file()
    superseded_paths = set(supersession["paths"])
    assert len(superseded_paths) == 5
    _assert_superseded_by_evidence_reconstruction(review)
