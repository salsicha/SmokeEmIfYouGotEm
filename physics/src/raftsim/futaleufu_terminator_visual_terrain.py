"""Build a reach-local Terminator Landscape from committed terrain and C3 data.

The Copernicus GLO-30 corridor remains the broad terrain authority. The complete
interpreted 2 m C3 solver strip replaces it only inside the committed 600 x 84 m
window. Smooth edge alignment and deterministic sub-30 m microrelief are visual
and Landscape-collision infill, never survey, bathymetry, or solver authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


SCHEMA = "raftsim.futaleufu.terminator_visual_terrain.v1"
DEFAULT_OUTPUT_RELATIVE = Path(
    "physics/data/real_world/futaleufu_river_chile/terrain/terminator_visual"
)
PRODUCTION_ROOT_RELATIVE = Path(
    "physics/data/real_world/futaleufu_river_chile/production_corridor/"
    "rio_azul_swinging_bridge_to_pasarela"
)
WINDOW_ROOT_RELATIVE = Path(
    "physics/data/real_world/futaleufu_river_chile/scenario_terminator"
)
REFERENCE_BAND = "median_runnable"
OUTPUT_CROSS_SPAN_M = 600.0
ANCHOR_STATION_M = 5312.259


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _resample_regular_grid(
    source: np.ndarray,
    source_x: np.ndarray,
    source_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
) -> np.ndarray:
    along_x = np.empty((source.shape[0], target_x.size), dtype=np.float64)
    for row in range(source.shape[0]):
        along_x[row] = np.interp(target_x, source_x, source[row])
    output = np.empty((target_y.size, target_x.size), dtype=np.float64)
    for column in range(target_x.size):
        output[:, column] = np.interp(
            target_y,
            source_y,
            along_x[:, column],
            left=along_x[0, column],
            right=along_x[-1, column],
        )
    return output


def _sample_image_bilinear(
    source: np.ndarray, x_px: np.ndarray, y_px: np.ndarray
) -> np.ndarray:
    height, width = source.shape[:2]
    x = np.clip(x_px, 0.0, width - 1.0)
    y = np.clip(y_px, 0.0, height - 1.0)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    fx = x - x0
    fy = y - y0
    return (
        source[y0, x0] * (1.0 - fx) * (1.0 - fy)
        + source[y0, x1] * fx * (1.0 - fy)
        + source[y1, x0] * (1.0 - fx) * fy
        + source[y1, x1] * fx * fy
    )


def build_futaleufu_terminator_visual_terrain(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    output_size_px: int = 1009,
) -> dict[str, object]:
    """Build deterministic Terminator Landscape and runtime alignment inputs."""

    if output_size_px < 127:
        raise ValueError("Terminator visual terrain requires at least 127 samples")

    repo_root = repo_root.resolve()
    production_root = repo_root / PRODUCTION_ROOT_RELATIVE
    window_root = repo_root / WINDOW_ROOT_RELATIVE
    cooked_root = window_root / "cooked_flow_fields"
    band_root = cooked_root / REFERENCE_BAND
    output_root = (output_dir or repo_root / DEFAULT_OUTPUT_RELATIVE).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    source_manifest_path = production_root / "manifest.json"
    source_centerline_path = production_root / "hydrography/centerline_local.json"
    source_heightfield_path = production_root / "derived/heightfield_2017.png"
    cooked_manifest_path = cooked_root / "manifest.json"
    window_manifest_path = window_root / "window_manifest.json"
    bed_path = band_root / "bed.npy"
    depth_path = band_root / "h.npy"
    wet_path = band_root / "wet_mask.npy"
    for path in (
        source_manifest_path,
        source_centerline_path,
        source_heightfield_path,
        cooked_manifest_path,
        window_manifest_path,
        bed_path,
        depth_path,
        wet_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_centerline = json.loads(
        source_centerline_path.read_text(encoding="utf-8")
    )
    cooked_manifest = json.loads(cooked_manifest_path.read_text(encoding="utf-8"))
    window_manifest = json.loads(window_manifest_path.read_text(encoding="utf-8"))

    grid = cooked_manifest["grid"]
    nx = int(grid["nx"])
    ny = int(grid["ny"])
    dx_m = float(grid["dx_m"])
    dy_m = float(grid["dy_m"])
    origin_x_m = float(grid["origin_x_m"])
    origin_y_m = float(grid["origin_y_m"])
    bed = np.asarray(np.load(bed_path, allow_pickle=False), dtype=np.float64)
    depth = np.asarray(np.load(depth_path, allow_pickle=False), dtype=np.float64)
    wet = np.asarray(np.load(wet_path, allow_pickle=False), dtype=bool)
    if bed.shape != (ny, nx) or depth.shape != bed.shape or wet.shape != bed.shape:
        raise ValueError("Terminator cooked arrays do not match their manifest grid")

    span_x_m = (nx - 1) * dx_m
    source_span_y_m = (ny - 1) * dy_m
    source_half_width_m = source_span_y_m * 0.5
    source_x = origin_x_m + np.arange(nx, dtype=np.float64) * dx_m
    source_y = origin_y_m + np.arange(ny, dtype=np.float64) * dy_m
    target_x = np.linspace(origin_x_m, origin_x_m + span_x_m, output_size_px)
    target_y = np.linspace(
        -OUTPUT_CROSS_SPAN_M * 0.5,
        OUTPUT_CROSS_SPAN_M * 0.5,
        output_size_px,
    )
    xx, yy = np.meshgrid(target_x, target_y)

    # The committed OSM route is review-gated, but it is the same adopted axis
    # used to derive the C3 grid. Local X points east and local Y points south,
    # so (tangent_y, -tangent_x) points river-left in raster coordinates.
    route_points = source_centerline["points"]
    route_station = np.asarray(
        [point["station_m"] for point in route_points], dtype=np.float64
    )
    route_x = np.asarray([point["x_m"] for point in route_points], dtype=np.float64)
    route_y = np.asarray([point["y_m"] for point in route_points], dtype=np.float64)
    corridor_station = ANCHOR_STATION_M - span_x_m * 0.5 + target_x
    center_x = np.interp(corridor_station, route_station, route_x)
    center_y = np.interp(corridor_station, route_station, route_y)
    tangent_x = np.gradient(center_x)
    tangent_y = np.gradient(center_y)
    tangent_length = np.hypot(tangent_x, tangent_y)
    if np.any(tangent_length <= 1.0e-9):
        raise ValueError("Terminator route contains a degenerate local tangent")
    tangent_x /= tangent_length
    tangent_y /= tangent_length
    sample_x_m = center_x[None, :] + tangent_y[None, :] * yy
    sample_y_m = center_y[None, :] - tangent_x[None, :] * yy

    source_u16 = np.asarray(Image.open(source_heightfield_path), dtype=np.float64)
    artifacts = source_manifest["artifacts"]
    source_min_m = float(artifacts["minimum_elevation_m"])
    source_relief_m = float(artifacts["relief_m"])
    source_elevation = source_min_m + source_u16 / 65535.0 * source_relief_m
    physical_width_m = float(source_manifest["physical_size_m"]["width"])
    physical_height_m = float(source_manifest["physical_size_m"]["height"])
    source_px_x = sample_x_m / physical_width_m * (source_u16.shape[1] - 1)
    source_px_y = sample_y_m / physical_height_m * (source_u16.shape[0] - 1)
    corridor_dem = _sample_image_bilinear(source_elevation, source_px_x, source_px_y)

    solver_bed = _resample_regular_grid(
        bed, source_x, source_y, target_x, target_y
    )
    left_edge = _resample_regular_grid(
        bed[-1:, :], source_x, np.asarray([source_y[-1]]), target_x, target_y
    )[0]
    right_edge = _resample_regular_grid(
        bed[:1, :], source_x, np.asarray([source_y[0]]), target_x, target_y
    )[0]
    left_row = int(np.argmin(np.abs(target_y - source_half_width_m)))
    right_row = int(np.argmin(np.abs(target_y + source_half_width_m)))
    left_delta = left_edge - corridor_dem[left_row]
    right_delta = right_edge - corridor_dem[right_row]
    edge_delta = np.where(yy >= 0.0, left_delta[None, :], right_delta[None, :])
    bank_distance = np.maximum(np.abs(yy) - source_half_width_m, 0.0)
    alignment_weight = 1.0 - _smoothstep(0.0, 135.0, bank_distance)
    aligned_dem = corridor_dem + edge_delta * alignment_weight

    # Restore bounded sub-grid ground form outside the exact C3 strip. The
    # incommensurate waves avoid square tiling and fade fully at its boundary.
    micro_fade = _smoothstep(0.0, 20.0, bank_distance)
    microrelief = micro_fade * (
        0.62 * np.sin(xx / 15.3 + yy / 9.7 + 0.31 * np.sin(xx / 57.0))
        + 0.34 * np.sin(xx / 6.9 - yy / 12.1 + 0.8)
        + 0.20 * np.sin(xx / 4.1 + yy / 5.9 + 2.3)
    )
    microrelief = np.clip(microrelief, -1.50, 1.50)
    conditioned = aligned_dem + microrelief
    protected_mask = np.abs(yy) <= source_half_width_m
    conditioned[protected_mask] = solver_bed[protected_mask]

    terrain_min_m = float(conditioned.min())
    terrain_max_m = float(conditioned.max())
    terrain_span_m = terrain_max_m - terrain_min_m
    if terrain_span_m <= 0.0:
        raise ValueError("Terminator conditioned terrain has no elevation range")
    heightfield_u16 = np.round(
        np.clip((conditioned - terrain_min_m) / terrain_span_m, 0.0, 1.0)
        * 65535.0
    ).astype(np.uint16)

    heightfield_path = (
        output_root / f"terminator_conditioned_heightfield_{output_size_px}.png"
    )
    centerline_path = output_root / "terminator_local_centerline.json"
    coordinate_map_path = output_root / "terminator_runtime_coordinate_map.json"
    manifest_path = output_root / "terminator_visual_terrain_manifest.json"
    Image.fromarray(heightfield_u16).save(heightfield_path)

    eta = bed + depth
    runtime_vertical_datum_m = float(np.mean(eta[wet]))
    channel_half_width_m = float(
        window_manifest["conditioning"]["channel_half_width_m"]
    )
    channel_rows = np.abs(source_y) <= channel_half_width_m
    centerline_surface = np.empty(nx, dtype=np.float64)
    centerline_bed = np.empty(nx, dtype=np.float64)
    for column in range(nx):
        wet_rows = channel_rows & wet[:, column]
        rows = wet_rows if wet_rows.any() else channel_rows
        centerline_surface[column] = float(np.median(eta[rows, column]))
        centerline_bed[column] = float(np.median(bed[rows, column]))

    local_center_y_cm = OUTPUT_CROSS_SPAN_M * 50.0
    centerline_points = []
    for column, station_m in enumerate(source_x):
        surface_m = float(centerline_surface[column])
        bed_m = float(centerline_bed[column])
        centerline_points.append(
            {
                "station_m": float(station_m),
                "corridor_station_m": float(
                    ANCHOR_STATION_M - span_x_m * 0.5 + station_m
                ),
                "unreal_local_cm": [float(station_m * 100.0), local_center_y_cm],
                "conditioned_visual_surface_elevation_m": surface_m,
                "conditioned_visual_bed_elevation_m": bed_m,
                "conditioned_visual_surface_normalized": (
                    surface_m - terrain_min_m
                )
                / terrain_span_m,
                "conditioned_visual_bed_normalized": (bed_m - terrain_min_m)
                / terrain_span_m,
            }
        )
    centerline = {
        "schema": "raftsim.local_centerline.v1",
        "river_id": "futaleufu_terminator",
        "section_id": "terminator_station_5312m_c3_window",
        "local_metric_policy": (
            "channel-following C3 coordinates; Unreal X is downstream station and "
            "Unreal Y shifts solver lateral 0 to the center of a 600 m visual valley"
        ),
        "points": centerline_points,
    }
    centerline_path.write_text(
        json.dumps(centerline, indent=2) + "\n", encoding="utf-8"
    )

    coordinate_map = {
        "schema": "raftsim.curved_river_coordinate_map.v1",
        "river_id": "futaleufu_river_chile",
        "section_id": "terminator_station_5312m_c3_window",
        "vertical_datum_m": runtime_vertical_datum_m,
        "mapping_policy": (
            "identity station/lateral map for the straight interpreted C3 grid; "
            "vertical datum aligns absolute cooked elevations to the local Unreal reach"
        ),
        "points": [
            [float(station), float(station), 0.0, 0.0, 1.0]
            for station in source_x
        ],
    }
    coordinate_map_path.write_text(
        json.dumps(coordinate_map, indent=2) + "\n", encoding="utf-8"
    )

    runtime_vertical_offset_cm = -(
        runtime_vertical_datum_m - terrain_min_m
    ) * 100.0
    static_centerline_world_surface_m = (
        centerline_surface - terrain_min_m + runtime_vertical_offset_cm / 100.0
    )
    runtime_centerline_surface_m = centerline_surface - runtime_vertical_datum_m
    source_change = conditioned - corridor_dem
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "status": (
            "generated_review_gated_reach_local_copernicus_dem_plus_interpreted_"
            "c3_solver_strip_not_survey_or_production_terrain_authority"
        ),
        "river_id": "futaleufu_terminator",
        "section_id": "terminator_station_5312m_c3_window",
        "reference_flow_band": REFERENCE_BAND,
        "inputs": {
            "source_corridor_manifest": _relative(source_manifest_path, repo_root),
            "source_corridor_manifest_sha256": _sha256(source_manifest_path),
            "source_centerline": _relative(source_centerline_path, repo_root),
            "source_centerline_sha256": _sha256(source_centerline_path),
            "conditioned_corridor_heightfield": _relative(
                source_heightfield_path, repo_root
            ),
            "conditioned_corridor_heightfield_sha256": _sha256(
                source_heightfield_path
            ),
            "window_manifest": _relative(window_manifest_path, repo_root),
            "window_manifest_sha256": _sha256(window_manifest_path),
            "cooked_manifest": _relative(cooked_manifest_path, repo_root),
            "cooked_manifest_sha256": _sha256(cooked_manifest_path),
            "bed": _relative(bed_path, repo_root),
            "bed_sha256": _sha256(bed_path),
            "depth": _relative(depth_path, repo_root),
            "depth_sha256": _sha256(depth_path),
            "wet_mask": _relative(wet_path, repo_root),
            "wet_mask_sha256": _sha256(wet_path),
        },
        "outputs": {
            "heightfield": _relative(heightfield_path, repo_root),
            "heightfield_sha256": _sha256(heightfield_path),
            "local_centerline": _relative(centerline_path, repo_root),
            "local_centerline_sha256": _sha256(centerline_path),
            "runtime_coordinate_map": _relative(coordinate_map_path, repo_root),
            "runtime_coordinate_map_sha256": _sha256(coordinate_map_path),
        },
        "landscape": {
            "size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "horizontal_span_x_m": span_x_m,
            "horizontal_span_y_m": OUTPUT_CROSS_SPAN_M,
            "source_solver_span_y_m": source_span_y_m,
            "sample_spacing_x_m": span_x_m / (output_size_px - 1),
            "sample_spacing_y_m": OUTPUT_CROSS_SPAN_M / (output_size_px - 1),
            "terrain_min_m": terrain_min_m,
            "terrain_max_m": terrain_max_m,
            "target_relief_cm": terrain_span_m * 100.0,
            "world_vertical_offset_cm": runtime_vertical_offset_cm,
            "runtime_vertical_datum_m": runtime_vertical_datum_m,
        },
        "source_registration": {
            "anchor_corridor_station_m": ANCHOR_STATION_M,
            "corridor_station_range_m": [
                ANCHOR_STATION_M - span_x_m * 0.5,
                ANCHOR_STATION_M + span_x_m * 0.5,
            ],
            "adopted_hydrography": (
                "OpenStreetMap named-river route scaffold pending guide and geospatial review"
            ),
            "terrain": "Copernicus DEM GLO-30 surface model, corridor-conditioned",
            "terrain_vertical_datum": "Copernicus DEM EGM2008 orthometric heights",
            "sampling_policy": "bilinear_frenet_cross_section_along_adopted_route",
        },
        "procedural_infill": {
            "algorithm": "corridor_dem_edge_alignment_and_sub_30m_microrelief_v1",
            "source_solver_half_width_m": source_half_width_m,
            "protected_solver_strip_change_m": float(
                np.max(np.abs(conditioned[protected_mask] - solver_bed[protected_mask]))
            ),
            "maximum_corridor_dem_edge_correction_m": float(
                max(np.max(np.abs(left_delta)), np.max(np.abs(right_delta)))
            ),
            "edge_correction_feather_distance_m": 135.0,
            "maximum_procedural_microrelief_m": float(np.max(np.abs(microrelief))),
            "maximum_change_from_corridor_dem_outside_solver_strip_m": float(
                np.max(np.abs(source_change[~protected_mask]))
            ),
            "authority": (
                "visual and Landscape collision infill only; Copernicus broad form, "
                "complete interpreted C3 bed, cooked water state, and raft forces remain unchanged"
            ),
        },
        "alignment": {
            "world_x_matches_runtime_station_m": True,
            "world_y_center_matches_runtime_lateral_zero": True,
            "maximum_static_to_runtime_centerline_surface_error_m": float(
                np.max(
                    np.abs(
                        static_centerline_world_surface_m
                        - runtime_centerline_surface_m
                    )
                )
            ),
            "static_water_flow_offset_cm": 0.0,
        },
        "honesty": {
            "source_bed_geometry_authority": window_manifest["honesty"][
                "bed_geometry_authority"
            ],
            "source_terrain_resolution_m": 30.0,
            "route_station_authority": (
                "order_distributed_route_work_window_not_authoritative"
            ),
            "procedural_gap_fill_authority": "visual_and_collision_infill_not_survey",
            "solver_authority": _relative(cooked_manifest_path, repo_root),
            "production_promoted": False,
            "pending_human_review": True,
            "missing": [
                "surveyed Terminator bathymetry, bank breaklines, and rapid rocks",
                "reviewed rapid station, span, and guide lines",
                "gauge-to-reach discharge calibration and solver convergence",
                "guide, geospatial, ecology, art, rights, and performance acceptance",
            ],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


__all__ = [
    "DEFAULT_OUTPUT_RELATIVE",
    "OUTPUT_CROSS_SPAN_M",
    "REFERENCE_BAND",
    "SCHEMA",
    "build_futaleufu_terminator_visual_terrain",
]
