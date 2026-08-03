from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeGeometry.cpp"
)
CAPTURE_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Captures/"
    "RaftSimEditorEnvironmentCaptures.cpp"
)
COOKED_FIELDS = REPO_ROOT / (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/"
    "scenario_hance/cooked_flow_fields"
)
REVIEW = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "colorado_hance_rapid_approach_launch_v1_review.json"
)

RUNTIME_LAUNCH_PROGRESS = 0.56
RUNTIME_REACH_LENGTH_M = 600.0
RUNTIME_LAUNCH_STATION_M = RUNTIME_LAUNCH_PROGRESS * RUNTIME_REACH_LENGTH_M
RUNTIME_SURFACE_LENGTH_M = 240.0
RUNTIME_SURFACE_WIDTH_M = 96.0
RUNTIME_SAMPLE_SPACING_M = 3.0
RUNTIME_FULL_STATION_COVERAGE_M = 36.0
RUNTIME_MINIMUM_BREAKING_CLEARANCE_M = 15.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads((COOKED_FIELDS / "manifest.json").read_text(encoding="utf-8"))


def _bilinear_sample(
    field: np.ndarray,
    stations_m: np.ndarray,
    laterals_m: np.ndarray,
    grid: dict,
) -> np.ndarray:
    ny, nx = field.shape
    grid_x = (stations_m - grid["origin_x_m"]) / grid["dx_m"]
    grid_y = (laterals_m - grid["origin_y_m"]) / grid["dy_m"]
    col = np.clip(np.floor(grid_x).astype(np.int64), 0, nx - 2)
    row = np.clip(np.floor(grid_y).astype(np.int64), 0, ny - 2)
    fx = grid_x - col
    fy = grid_y - row
    return (
        field[row, col] * (1.0 - fx) * (1.0 - fy)
        + field[row, col + 1] * fx * (1.0 - fy)
        + field[row + 1, col] * (1.0 - fx) * fy
        + field[row + 1, col + 1] * fx * fy
    )


def _launch_window_breaking_sites(band_id: str) -> list[dict[str, float]]:
    manifest = _manifest()
    grid = manifest["grid"]
    band = COOKED_FIELDS / band_id
    h = np.load(band / "h.npy").astype(np.float64)
    u = np.load(band / "u.npy").astype(np.float64)
    v = np.load(band / "v.npy").astype(np.float64)
    station_count = int(
        round(RUNTIME_SURFACE_LENGTH_M / RUNTIME_SAMPLE_SPACING_M)
    ) + 1
    lateral_count = int(
        round(RUNTIME_SURFACE_WIDTH_M / RUNTIME_SAMPLE_SPACING_M)
    ) + 1
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
    depth = _bilinear_sample(h, station_grid, lateral_grid, grid)
    velocity_u = _bilinear_sample(u, station_grid, lateral_grid, grid)
    velocity_v = _bilinear_sample(v, station_grid, lateral_grid, grid)
    wet = depth > 1.0e-4
    froude = np.hypot(velocity_u, velocity_v) / np.sqrt(
        9.80665 * np.maximum(depth, 1.0e-9)
    )
    minimum_wet = np.asarray(
        [
            np.flatnonzero(wet[:, x])[0] if wet[:, x].any() else -1
            for x in range(station_count)
        ]
    )
    maximum_wet = np.asarray(
        [
            np.flatnonzero(wet[:, x])[-1] if wet[:, x].any() else -1
            for x in range(station_count)
        ]
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
            intensity = np.clip(
                (upstream_froude - 1.0) / 1.4, 0.0, 1.0
            ) * np.clip(depth[y, x] / 0.6, 0.3, 1.0)
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


def _launch_centerline_hydraulics(band_id: str) -> tuple[float, float, float]:
    manifest = _manifest()
    grid = manifest["grid"]
    station = np.asarray([[RUNTIME_LAUNCH_STATION_M]])
    lateral = np.asarray([[0.0]])
    band = COOKED_FIELDS / band_id
    depth = float(
        _bilinear_sample(np.load(band / "h.npy"), station, lateral, grid)[0, 0]
    )
    velocity_u = float(
        _bilinear_sample(np.load(band / "u.npy"), station, lateral, grid)[0, 0]
    )
    velocity_v = float(
        _bilinear_sample(np.load(band / "v.npy"), station, lateral, grid)[0, 0]
    )
    speed = float(np.hypot(velocity_u, velocity_v))
    froude = speed / np.sqrt(9.80665 * depth)
    return depth, speed, froude


@pytest.mark.parametrize(
    "band_id",
    (
        "low_release_planning",
        "moderate_release_planning",
        "high_release_planning",
    ),
)
def test_hance_launch_is_subcritical_and_frames_an_interior_solver_jump(
    band_id: str,
) -> None:
    depth, _, launch_froude = _launch_centerline_hydraulics(band_id)
    assert depth >= 1.5
    assert launch_froude <= 0.75

    sites = [
        site
        for site in _launch_window_breaking_sites(band_id)
        if 30.0 <= site["station_m"] - RUNTIME_LAUNCH_STATION_M <= 110.0
    ]
    assert sites, band_id
    strongest = max(sites, key=lambda site: site["intensity"])
    assert 390.0 <= strongest["station_m"] <= 450.0
    assert strongest["upstream_froude"] >= 1.12
    assert strongest["downstream_froude"] <= 0.94
    assert strongest["edge_clearance_m"] >= RUNTIME_MINIMUM_BREAKING_CLEARANCE_M


def test_hance_generator_authors_rapid_approach_and_distinct_camera() -> None:
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")
    assert "const float StartProgress = bColoradoHance" in geometry
    assert "? 0.56f" in geometry
    assert geometry.count("RaftSimColoradoHanceRapidApproachLaunchV1") >= 2
    assert "bSouthForkSolverRapidCamera" in capture
    assert "RaftSim_SolverRapid_RiverEyeCaptureCamera" in capture


def test_hance_rapid_approach_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    assert review["schema"] == (
        "raftsim.environment.colorado_hance_rapid_approach_launch_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["rapid_approach_framing_retained"] is True
    assert review["decision"]["interior_solver_breaking_site_passed"] is True
    assert review["decision"]["production_promoted"] is False
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["cooked_fields_changed"] is False
    assert review["launch_contract"]["retained_launch_station_m"] == pytest.approx(
        336.0
    )
    assert review["launch_contract"]["approach_distance_m"] == pytest.approx(69.0)
    assert review["live_pie_evidence"]["initial_active_breaking_sites"] >= 1
    assert review["live_pie_evidence"]["initial_strongest_interior_coverage"] == 1.0
    assert (
        review["live_pie_evidence"]["initial_strongest_interior_clearance_m"]
        >= 15.0
    )
    assert review["live_pie_evidence"]["initial_visible_rapid_foam_vertices"] > 0
    assert review["capture_evidence"]["solver_rapid_distinct_from_guide"] is True
    assert review["capture_evidence"]["solver_rapid_distinct_from_river_eye"] is True
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
