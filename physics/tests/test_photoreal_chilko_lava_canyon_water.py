from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorChilkoWaterMaterial.cpp"
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
    "landscape_candidate_manifest_chilko_river_lava_canyon.json"
)
REVIEW = MANIFEST.with_name("chilko_futaleufu_cold_water_v2_review.json")
RAPID_APPROACH_REVIEW = MANIFEST.with_name(
    "chilko_lava_canyon_rapid_approach_launch_v1_review.json"
)
VOLUME_CORE_REVIEW = MANIFEST.with_name("chilko_live_volume_core_v1_review.json")
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
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_chilko_water_is_native_moving_and_non_displacing() -> None:
    water = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Chilko_LavaCanyonDefaultLitWater" in water
    assert "MSM_DefaultLit" in water
    assert "BLEND_Opaque" in water
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
    assert 'TEXT("T_RaftSim_%s_NormalAtlas")' in base
    assert "Hance, Terminator, and Chilko each sample their packed field once" in base


def test_chilko_capture_and_live_profiles_are_river_local() -> None:
    catalog = CATALOG_SOURCE.read_text(encoding="utf-8")
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    runtime = RUNTIME_SOURCE.read_text(encoding="utf-8")
    config = CONFIG_HEADER.read_text(encoding="utf-8")

    for token in (
        "Settings.BaseColorScale = 1.10f",
        "Settings.EmissiveFillScale = 0.16f",
        "Settings.NormalIntensity = 0.34f",
        "Settings.SurfaceVariationStrength = 0.46f",
        "Settings.VertexTintWeight = 0.78f",
    ):
        assert token in catalog
    for token in (
        "bEnableLiveSolverVolumeCore = true",
        "LiveSurfaceCalmCoverage = 0.035f",
        "LiveSurfaceActiveCoverage = 0.14f",
        "LiveSkyReflectionStrength = 0.38f",
        "LiveRippleStrength = 0.32f",
        "LiveFoamIntensity = 0.72f",
        "RaftSimChilkoDefaultLitWater",
        "RaftSimCpuAuthoredCookedFieldColor",
        "RaftSimColdWaterCpuChopV2",
        "RaftSimColdWaterEmbeddedAerationV2",
    ):
        assert token in geometry
    for parameter in (
        "bEnableLiveSolverVolumeCore",
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
    ):
        assert parameter in config
    for parameter in (
        "LiveSkyReflectionStrength",
        "LiveRippleStrength",
        "LiveFoamIntensity",
    ):
        assert f'TEXT("{parameter}")' in runtime
    assert 'TEXT("LiveVolumeCoreMesh")' in runtime
    assert "kLiveVolumeCoreMinimumStationCoverage = 0.60f" in runtime
    assert "MinimumCellStationCoverage" in runtime
    assert "kLiveVolumeCoreCalmDetailCoverage = 0.035f" in runtime
    assert "kLiveVolumeCoreActiveDetailCoverage = 0.14f" in runtime
    assert "WetVertexMask[I0] != 0" in runtime
    assert "LiveVolumeCoreTriangles != NewVolumeCoreTriangles" in runtime
    assert "M_RaftSim_SouthForkRaftTransmissionWater" in runtime
    assert 'TEXT("chilko_river_lava_canyon")' in runtime
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
        "chilko_lava_canyon_default_lit_native_moving_normal_candidate_"
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
    assert candidate["water_base_color_scale"] == 1.10
    assert candidate["water_vertex_tint_weight"] == 0.78
    assert candidate["water_emissive_fill_scale"] == 0.16
    assert candidate["water_reflection_fill_intensity"] == 0.12
    assert candidate["water_roughness"] == 0.22
    assert candidate["water_specular"] == 0.48
    assert candidate["water_normal_intensity"] == 0.34
    assert candidate["water_surface_variation_strength"] == 0.46
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
