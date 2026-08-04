from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageStat


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorChilkoWaterMaterial.cpp"
TEXTURE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealTextureAssets.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
PHOTOREAL_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealMaterials.cpp"
CATALOG_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorEnvironmentCatalog.cpp"
LIGHTING_SOURCE = EDITOR_ROOT / "Environment/RaftSimEditorNearFieldAndLighting.cpp"
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
    "landscape_candidate_manifest_chilko_river_lava_canyon.json"
)
REVIEW = MANIFEST.with_name("chilko_futaleufu_cold_water_v2_review.json")
RAPID_APPROACH_REVIEW = MANIFEST.with_name(
    "chilko_lava_canyon_rapid_approach_launch_v1_review.json"
)
VOLUME_CORE_REVIEW = MANIFEST.with_name("chilko_live_volume_core_v1_review.json")
TRANSMITTING_REVIEW = MANIFEST.with_name(
    "chilko_lava_canyon_transmitting_water_v2_review.json"
)
FLOW_NORMAL_SOURCE = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Water/ChilkoLavaCanyon/"
    "T_RaftSim_ChilkoLavaCanyon_FlowNormalV1.png"
)
FOAM_LACE_SOURCE = FLOW_NORMAL_SOURCE.with_name(
    "T_RaftSim_ChilkoLavaCanyon_FoamLaceV1.png"
)
COOKED_FIELDS = (
    REPO_ROOT
    / "physics/data/real_world/chilko_river_lava_canyon/"
    "scenario_lava_canyon/cooked_flow_fields"
)

RUNTIME_LAUNCH_PROGRESS = 0.38
RUNTIME_REACH_LENGTH_M = 600.0
RUNTIME_LAUNCH_STATION_M = RUNTIME_LAUNCH_PROGRESS * RUNTIME_REACH_LENGTH_M
RUNTIME_SURFACE_LENGTH_M = 240.0
RUNTIME_SURFACE_WIDTH_M = 96.0
RUNTIME_SAMPLE_SPACING_M = 3.0
RUNTIME_FULL_STATION_COVERAGE_M = 36.0
RUNTIME_MINIMUM_BREAKING_CLEARANCE_M = 15.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bilinear_sample_2m_chilko_field(
    field: np.ndarray,
    stations_m: np.ndarray,
    laterals_m: np.ndarray,
) -> np.ndarray:
    """Mirror the runtime's bilinear sample of the 2 m, y=-40 m cooked grid."""

    ny, nx = field.shape
    grid_x = stations_m / 2.0
    grid_y = (laterals_m + 40.0) / 2.0
    col = np.minimum(np.floor(grid_x).astype(np.int64), nx - 2)
    row = np.minimum(np.floor(grid_y).astype(np.int64), ny - 2)
    fx = grid_x - col
    fy = grid_y - row
    return (
        field[row, col] * (1.0 - fx) * (1.0 - fy)
        + field[row, col + 1] * fx * (1.0 - fy)
        + field[row + 1, col] * (1.0 - fx) * fy
        + field[row + 1, col + 1] * fx * fy
    )


def _launch_window_breaking_sites(band_id: str) -> list[dict[str, float]]:
    """Evaluate the live 3 m breaking-water/edge contract at the Chilko launch."""

    band = COOKED_FIELDS / band_id
    h = np.load(band / "h.npy").astype(np.float64)
    u = np.load(band / "u.npy").astype(np.float64)
    v = np.load(band / "v.npy").astype(np.float64)
    station_count = int(round(RUNTIME_SURFACE_LENGTH_M / RUNTIME_SAMPLE_SPACING_M)) + 1
    lateral_count = int(round(RUNTIME_SURFACE_WIDTH_M / RUNTIME_SAMPLE_SPACING_M)) + 1
    stations = (
        RUNTIME_LAUNCH_STATION_M
        - RUNTIME_SURFACE_LENGTH_M * 0.5
        + np.arange(station_count) * RUNTIME_SAMPLE_SPACING_M
    )
    laterals = (
        -RUNTIME_SURFACE_WIDTH_M * 0.5
        + np.arange(lateral_count) * RUNTIME_SAMPLE_SPACING_M
    )
    station_grid, lateral_grid = np.meshgrid(stations, laterals)
    depth = _bilinear_sample_2m_chilko_field(h, station_grid, lateral_grid)
    velocity_u = _bilinear_sample_2m_chilko_field(u, station_grid, lateral_grid)
    velocity_v = _bilinear_sample_2m_chilko_field(v, station_grid, lateral_grid)
    wet = depth > 1.0e-4
    froude = np.hypot(velocity_u, velocity_v) / np.sqrt(
        9.80665 * np.maximum(depth, 1.0e-9)
    )
    minimum_wet = np.asarray(
        [np.flatnonzero(wet[:, x])[0] if wet[:, x].any() else -1 for x in range(station_count)]
    )
    maximum_wet = np.asarray(
        [np.flatnonzero(wet[:, x])[-1] if wet[:, x].any() else -1 for x in range(station_count)]
    )

    accepted: list[dict[str, float]] = []
    for y in range(lateral_count):
        for x in range(1, station_count):
            if not wet[y, x] or not wet[y, x - 1] or froude[y, x] > 0.94:
                continue
            upstream_x = x - 1
            upstream_froude = float(froude[y, upstream_x])
            if (
                upstream_froude < 1.12
                and x >= 2
                and wet[y, x - 2]
                and froude[y, x - 2] > upstream_froude
            ):
                upstream_x = x - 2
                upstream_froude = float(froude[y, upstream_x])
            if upstream_froude < 1.12:
                continue
            intensity = np.clip((upstream_froude - 1.0) / 1.4, 0.0, 1.0) * np.clip(
                depth[y, x] / 0.6, 0.3, 1.0
            )
            if intensity < 0.08:
                continue
            station_clearance = min(
                (x - 1) * RUNTIME_SAMPLE_SPACING_M,
                (station_count - x) * RUNTIME_SAMPLE_SPACING_M,
                x * RUNTIME_SAMPLE_SPACING_M,
                (station_count - 1 - x) * RUNTIME_SAMPLE_SPACING_M,
            )
            lateral_clearance = min(
                (y - minimum_wet[x - 1]) * RUNTIME_SAMPLE_SPACING_M,
                (maximum_wet[x - 1] - y) * RUNTIME_SAMPLE_SPACING_M,
                (y - minimum_wet[x]) * RUNTIME_SAMPLE_SPACING_M,
                (maximum_wet[x] - y) * RUNTIME_SAMPLE_SPACING_M,
            )
            edge_clearance = min(station_clearance, lateral_clearance)
            if (
                station_clearance < RUNTIME_FULL_STATION_COVERAGE_M
                or lateral_clearance < 9.0
                or edge_clearance < RUNTIME_MINIMUM_BREAKING_CLEARANCE_M
            ):
                continue
            accepted.append(
                {
                    "station_m": float(stations[upstream_x]),
                    "lateral_m": float(laterals[y]),
                    "upstream_froude": upstream_froude,
                    "downstream_froude": float(froude[y, x]),
                    "intensity": float(intensity),
                    "edge_clearance_m": float(edge_clearance),
                }
            )
    return accepted


@pytest.mark.parametrize("band_id", ("low_runnable", "median_runnable", "high_runnable"))
def test_chilko_rapid_approach_launch_frames_an_interior_solver_jump(
    band_id: str,
) -> None:
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")

    assert "bChilkoLavaCanyon" in geometry
    assert "? 0.38f" in geometry
    assert "RaftSimChilkoRapidApproachLaunchV1" in geometry
    sites = _launch_window_breaking_sites(band_id)
    assert sites, band_id
    strongest = max(sites, key=lambda site: site["intensity"])
    assert 285.0 <= strongest["station_m"] <= 365.0
    assert strongest["upstream_froude"] >= 1.12
    assert strongest["downstream_froude"] <= 0.94
    assert strongest["edge_clearance_m"] >= RUNTIME_MINIMUM_BREAKING_CLEARANCE_M


def test_chilko_rapid_approach_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(RAPID_APPROACH_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_lava_canyon_rapid_approach_launch_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["rapid_approach_framing_retained"] is True
    assert review["decision"]["interior_solver_breaking_site_passed"] is True
    assert review["decision"]["production_promoted"] is False
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["cooked_fields_changed"] is False
    assert review["launch_contract"]["retained_launch_station_m"] == pytest.approx(228.0)
    assert review["launch_contract"]["approach_distance_m"] == pytest.approx(72.0)
    assert review["live_pie_evidence"]["initial_active_breaking_sites"] >= 1
    assert review["live_pie_evidence"]["initial_strongest_interior_coverage"] == 1.0
    assert review["live_pie_evidence"]["initial_strongest_interior_clearance_m"] >= 15.0
    assert review["live_pie_evidence"]["initial_visible_rapid_foam_vertices"] > 0
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        if artifact["path"] == "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap":
            # The V2 transmitting-water milestone deliberately regenerates
            # the runnable package; keep this V1 review immutable while its
            # retained capture remains hash-locked below.
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_chilko_water_is_native_moving_and_non_displacing() -> None:
    water = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Chilko_LavaCanyonDefaultLitWater" in water
    assert "MSM_DefaultLit" in water
    assert "BLEND_Translucent" in water
    assert "TLM_SurfacePerPixelLighting" in water
    assert "EditorOnlyData->Opacity" in water
    assert "EditorOnlyData->Refraction" in water
    assert "UMaterialExpressionSingleLayerWaterMaterialOutput" not in water
    assert water.count("AddNormalSample(") == 3
    assert "0.00027f" in water
    assert "0.00147f" in water
    assert "0.00611f" in water
    assert "EditorOnlyData->WorldPositionOffset" not in water
    assert "Landscape->Import" not in water
    assert "SetCollision" not in water
    assert 'Spec.RiverId == TEXT("chilko_river_lava_canyon")' in base
    assert "LoadOrCreateChilkoLavaCanyonWaterParent" in base
    assert "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal" in base
    assert "Hance, Terminator, and Chilko each sample their packed field once" in base


def test_chilko_capture_and_live_profiles_are_river_local() -> None:
    catalog = CATALOG_SOURCE.read_text(encoding="utf-8")
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    live_material = WATER_SOURCE.read_text(encoding="utf-8")
    photoreal = PHOTOREAL_SOURCE.read_text(encoding="utf-8")
    lighting = LIGHTING_SOURCE.read_text(encoding="utf-8")
    runtime = RUNTIME_SOURCE.read_text(encoding="utf-8")
    config = CONFIG_HEADER.read_text(encoding="utf-8")

    for token in (
        "Settings.BaseColorScale = 0.94f",
        "Settings.EmissiveFillScale = 0.060f",
        "Settings.NormalIntensity = 0.26f",
        "Settings.SurfaceVariationStrength = 0.30f",
        "Settings.VertexTintWeight = 0.78f",
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
        "LiveFoamIntensity = 0.56f",
        "LiveShallowWaterOpacity = 0.36f",
        "LiveOpticalDepthResponseExponent = 0.25f",
        "LiveDeepWaterOpacity = 0.84f",
        "LiveFoamWaterOpacity = 0.86f",
        "FLinearColor(0.00004f, 0.00009f, 0.00014f, 0.0f)",
        "FLinearColor(0.0110f, 0.0065f, 0.0045f, 0.0f)",
        "FLinearColor(0.060f, 0.080f, 0.095f, 0.0f)",
        "FLinearColor(0.025f, 0.050f, 0.075f, 1.0f)",
        "LoadOrCreateChilkoLavaCanyonLiveWaterInstance",
        "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal",
        "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace",
        "RaftSimChilkoTransmittingWaterV2",
        "RaftSimChilkoLocalizedReflectionWaterV3",
        "RaftSimColdWaterHighlightNaturalismV1",
        "RaftSimColdWaterDepthAttenuationV2",
        "RaftSimColdWaterNonlinearOpticalDepthV1",
        "RaftSimNoSolverStateMutation",
        "RaftSimChilkoDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
        "RaftSimColdWaterCpuChopV2",
        "RaftSimColdWaterEmbeddedAerationV2",
    ):
        assert token in geometry
    for token in (
        'SetScalar(TEXT("SpeedAerationFraction"), 0.020f)',
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
        assert token in live_material
    for token in (
        "Settings.SunIntensity = 2.90f",
        "Settings.SkyLightIntensity = 1.30f",
        "Settings.ExposureBias = -0.30f",
    ):
        assert token in catalog
    assert "RaftSimChilkoRestrainedReflectionRigV3" in lighting
    assert "? 0.65f" in lighting
    assert "? FRotator(-50.0f, 55.0f, 0.0f)" in lighting
    for token in (
        'Scalar(TEXT("LiveWetCoverageDepthGain"), 32.0f)',
        'Scalar(TEXT("LiveWetCoverageEnable"), 0.0f)',
        'TEXT("LiveWetCoverageEnable")',
        "bUsesMigratedChilkoVolumeCore ? 1.0f : 0.0f",
        "bUsesMigratedChilkoVolumeCore ? 0.85f : 0.50f",
        "bUsesMigratedChilkoVolumeCore\n            ? 0.0f",
        "bUsesLegacyChilkoPresentationDefaults",
        "!RiverWaterConfig->bEnableLiveSolverVolumeCore",
    ):
        assert token in photoreal or token in runtime
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
    ):
        assert parameter in config
    for parameter in (
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
        "OpticalDepthResponseExponent",
    ):
        assert f'TEXT("{parameter}")' in runtime
    assert 'TEXT("LiveVolumeCoreMesh")' in runtime
    water_config_runtime = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimWater/Private"
        / "RaftSimRiverWaterConfig.cpp"
    ).read_text(encoding="utf-8")
    assert "bMigratedChilkoHighlightResponse" in water_config_runtime
    assert "2.90f" in water_config_runtime
    assert "SetIntensity(RuntimeDirectionalLightIntensity)" in water_config_runtime
    assert "kLiveVolumeCoreMinimumStationCoverage = 0.60f" in runtime
    assert "MinimumCellStationCoverage" in runtime
    assert "kLiveVolumeCoreCalmDetailCoverage = 0.035f" in runtime
    assert "kLiveVolumeCoreActiveDetailCoverage = 0.14f" in runtime
    assert "WetVertexMask[I0] != 0" in runtime
    assert "LiveVolumeCoreTriangles != NewVolumeCoreTriangles" in runtime
    assert "M_RaftSim_SouthForkRaftTransmissionWater" in runtime
    assert 'TEXT("chilko_river_lava_canyon")' in runtime
    assert "MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2" in runtime
    assert "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal" in runtime
    assert "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace" in runtime
    assert "FLinearColor(0.00004f, 0.00009f, 0.00014f, 0.0f)" in runtime
    assert "FLinearColor(0.0110f, 0.0065f, 0.0045f, 0.0f)" in runtime
    assert "FLinearColor(0.060f, 0.080f, 0.095f, 0.0f)" in runtime
    assert "? 0.020f" in runtime
    assert 'TEXT("SpeedAerationFraction")' in runtime
    assert "float LiveRapidFoamFocusStart = 0.12f" in config
    assert "float LiveRapidFoamFocusEnd = 0.72f" in config


def test_chilko_live_volume_core_review_is_hash_locked_and_honest() -> None:
    review = json.loads(VOLUME_CORE_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.chilko_live_volume_core_review.v1"
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["volume_core_retained"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["live_pie_evidence"]["volume_core_triangles"] > 0
    assert review["live_pie_evidence"]["initial_visible_rapid_foam_vertices"] > 0
    assert review["visual_comparison"]["retained_water_band_blue_minus_red"] > 0.0
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_chilko_manifest_records_native_capture_water() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "chilko_river_lava_canyon"
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/ChilkoRun/Water/Materials/"
        "M_RaftSim_Chilko_LavaCanyonDefaultLitWater"
    )
    assert candidate["water_material_status"] == (
        "chilko_lava_canyon_transmitting_default_lit_river_local_normal_"
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
    assert candidate["water_base_color_scale"] == 0.94
    assert candidate["water_vertex_tint_weight"] == 0.78
    assert candidate["water_emissive_fill_scale"] == 0.06
    assert candidate["water_reflection_fill_intensity"] == 0.06
    assert candidate["water_roughness"] == 0.34
    assert candidate["water_specular"] == 0.34
    assert candidate["water_surface_opacity"] == 0.90
    assert candidate["water_normal_intensity"] == 0.26
    assert candidate["water_surface_variation_strength"] == 0.30
    assert candidate["water_solver_render_geometry_collision_enabled"] is False


def test_chilko_native_water_review_is_hash_locked_and_honest() -> None:
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
    river = review["rivers"]["chilko_river_lava_canyon"]
    assert river["moving_normal_layer_count"] == 3
    assert river["world_optical_scales_per_cm"] == [
        0.00027,
        0.00147,
        0.00611,
    ]
    assert river["ribbon_cross_section_steps"] == 48
    assert river["analytic_chop_scale"] == 0.72
    assert river["cross_current_chop_amplitude_cm"] == 7.0
    assert river["embedded_aeration_weight"] == 0.18
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


def test_chilko_v2_visual_textures_are_first_party_and_solver_masked() -> None:
    texture_source = TEXTURE_SOURCE.read_text(encoding="utf-8")
    expected = {
        FLOW_NORMAL_SOURCE: (
            "chilko_lava_canyon_flow_normal_v1",
            "44d04e0095653cecdc39f3166c2445f6920f8b59cc6c7ae6a85b6eaeb0d5e180",
            "project_owned_chilko_multiscale_river_flow_normal",
        ),
        FOAM_LACE_SOURCE: (
            "chilko_lava_canyon_foam_lace_v1",
            "961e52ed6a57cd7b34a7369008e6d5cd0646c579147159fe3f0960006ccbed8e",
            "project_owned_chilko_solver_masked_whitewater_lace",
        ),
    }
    for texture, (asset_id, sha256, map_kind) in expected.items():
        assert texture.is_file()
        assert _sha256(texture) == sha256
        provenance = json.loads(
            texture.with_suffix(".provenance.json").read_text(encoding="utf-8")
        )
        assert provenance["asset_id"] == asset_id
        assert provenance["project_ownership"] == (
            "first-party generated project asset"
        )
        assert provenance["texture"]["sha256"] == sha256
        assert provenance["texture"]["width"] == 1254
        assert provenance["texture"]["height"] == 1254
        assert "no hydraulic" in provenance["asset_role"]
        assert len(provenance["limitations"]) >= 4
        assert map_kind in texture_source
    with Image.open(FLOW_NORMAL_SOURCE) as image:
        assert image.size == (1254, 1254)
        assert image.mode == "RGB"
    with Image.open(FOAM_LACE_SOURCE).convert("L") as image:
        assert image.size == (1254, 1254)
        assert ImageStat.Stat(image).mean[0] < 50.0


def test_chilko_transmitting_water_v2_review_is_honest_and_hash_locked() -> None:
    review = json.loads(TRANSMITTING_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_lava_canyon_transmitting_water_review.v2"
    )
    assert review["status"] == (
        "technical_optical_candidate_retained_photoreal_and_external_"
        "acceptance_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["transmitting_water_v2_retained"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["gameplay_water_geometry_changed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["collision_or_raft_forces_changed"] is False
    assert review["runtime_contract"]["live_volume_core_enabled"] is True
    assert review["runtime_contract"]["shallow_opacity"] == 0.42
    assert review["runtime_contract"]["detail_surface_calm_coverage"] == 0.035
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        # The runnable map, generated UE assets, manifest, and canonical
        # captures are versioned in place by later retained environment
        # milestones. Preserve their V2 hashes as historical evidence while
        # byte-locking only immutable source art/provenance and the dedicated
        # V2 live evidence frame.
        if path.name in {
            "T_RaftSim_ChilkoLavaCanyon_FlowNormalV1.png",
            "T_RaftSim_ChilkoLavaCanyon_FlowNormalV1.provenance.json",
            "T_RaftSim_ChilkoLavaCanyon_FoamLaceV1.png",
            "T_RaftSim_ChilkoLavaCanyon_FoamLaceV1.provenance.json",
            "chilko_lava_canyon_transmitting_water_v2_breaking_water_side.png",
        }:
            assert _sha256(path) == artifact["sha256"]
