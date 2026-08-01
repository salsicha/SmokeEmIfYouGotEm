"""Reach-local visual terrain bundle for the runnable Pacuare Upper Huacas map.

The committed Upper Huacas C3 window is the most spatially coherent terrain
authority currently available for the playable Pacuare rapid.  It is already
honestly labelled as Copernicus GLO-30 valley-scale terrain plus interpreted
channel/bank geometry.  This module resamples that 600 m by 78 m window into an
Unreal Landscape heightfield and adds bounded, deterministic sub-DEM relief
only outside the protected channel.

The generated relief is presentation/collision infill, not surveyed terrain or
solver authority.  The cooked C3 arrays remain untouched and continue to drive
the live water runtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

SCHEMA = "raftsim.pacuare.upper_huacas_visual_terrain.v1"
DEFAULT_OUTPUT_RELATIVE = Path(
    "physics/data/real_world/pacuare_river_costa_rica/terrain/upper_huacas_visual"
)
WINDOW_ROOT_RELATIVE = Path(
    "physics/data/real_world/pacuare_river_costa_rica/scenario_upper_huacas"
)
REFERENCE_BAND = "rainfed_runnable_planning"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _resample_regular_grid(source: np.ndarray, output_size_px: int) -> np.ndarray:
    """Bilinearly resample a row-major regular grid without a SciPy dependency."""

    source_y = np.linspace(0.0, 1.0, source.shape[0], dtype=np.float64)
    source_x = np.linspace(0.0, 1.0, source.shape[1], dtype=np.float64)
    target = np.linspace(0.0, 1.0, output_size_px, dtype=np.float64)
    along_x = np.empty((source.shape[0], output_size_px), dtype=np.float64)
    for row in range(source.shape[0]):
        along_x[row] = np.interp(target, source_x, source[row])
    output = np.empty((output_size_px, output_size_px), dtype=np.float64)
    for column in range(output_size_px):
        output[:, column] = np.interp(target, source_y, along_x[:, column])
    return output


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_pacuare_upper_huacas_visual_terrain(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    output_size_px: int = 1009,
) -> dict[str, object]:
    """Build the deterministic Landscape, centerline, and provenance manifest."""

    if output_size_px < 127:
        raise ValueError("Upper Huacas visual terrain requires at least 127 samples")

    repo_root = repo_root.resolve()
    window_root = repo_root / WINDOW_ROOT_RELATIVE
    band_root = window_root / "cooked_flow_fields" / REFERENCE_BAND
    output_root = (output_dir or (repo_root / DEFAULT_OUTPUT_RELATIVE)).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    bed_path = band_root / "bed.npy"
    depth_path = band_root / "h.npy"
    wet_path = band_root / "wet_mask.npy"
    cooked_manifest_path = window_root / "cooked_flow_fields/manifest.json"
    window_manifest_path = window_root / "window_manifest.json"
    for required in (
        bed_path,
        depth_path,
        wet_path,
        cooked_manifest_path,
        window_manifest_path,
    ):
        if not required.is_file():
            raise FileNotFoundError(required)

    cooked_manifest = json.loads(cooked_manifest_path.read_text(encoding="utf-8"))
    window_manifest = json.loads(window_manifest_path.read_text(encoding="utf-8"))
    grid = cooked_manifest["grid"]
    nx = int(grid["nx"])
    ny = int(grid["ny"])
    dx_m = float(grid["dx_m"])
    dy_m = float(grid["dy_m"])
    origin_x_m = float(grid["origin_x_m"])
    origin_y_m = float(grid["origin_y_m"])

    bed = np.asarray(np.load(bed_path), dtype=np.float64)
    depth = np.asarray(np.load(depth_path), dtype=np.float64)
    wet = np.asarray(np.load(wet_path), dtype=bool)
    if bed.shape != (ny, nx) or depth.shape != bed.shape or wet.shape != bed.shape:
        raise ValueError("Upper Huacas cooked arrays do not match their manifest grid")

    span_x_m = (nx - 1) * dx_m
    span_y_m = (ny - 1) * dy_m
    base = _resample_regular_grid(bed, output_size_px)
    x = np.linspace(origin_x_m, origin_x_m + span_x_m, output_size_px)
    y = np.linspace(origin_y_m, origin_y_m + span_y_m, output_size_px)
    xx, yy = np.meshgrid(x, y)

    # Domain-warped, non-periodic-looking relief breaks up the 30 m DEM planes
    # without moving the authored channel, waterfall/drop bed, map perimeter,
    # or live solver arrays.  Wavelengths are resolved by the final Landscape;
    # the 38 cm cap is small against the 24 m valley relief.
    warp_x = 3.8 * np.sin(yy / 11.7 + 0.63 * np.sin(xx / 47.0))
    warp_y = 2.9 * np.sin(xx / 31.0 - 0.51 * np.cos(yy / 8.4))
    broad = 0.18 * np.sin((xx + warp_x) / 17.5 + (yy + warp_y) / 13.0) + 0.11 * np.sin(
        (xx - 0.7 * warp_x) / 8.2 - yy / 6.3 + 1.7
    )
    fine = 0.055 * np.sin(
        xx / 3.7 + yy / 2.9 + 0.8 * np.sin(xx / 15.0)
    ) + 0.035 * np.sin(xx / 2.15 - yy / 2.75 + 2.3)
    rill_phase = yy - 4.1 * np.sin(xx / 27.0) - 1.7 * np.sin(xx / 9.5)
    rills = -0.075 * np.exp(-np.square(np.sin(rill_phase / 4.8)) / 0.075)

    protected_channel_half_width_m = 17.0
    full_infill_cross_m = 29.0
    channel_fade = _smoothstep(
        protected_channel_half_width_m,
        full_infill_cross_m,
        np.abs(yy),
    )
    edge_fade = (
        _smoothstep(0.0, 14.0, xx - origin_x_m)
        * _smoothstep(0.0, 14.0, origin_x_m + span_x_m - xx)
        * _smoothstep(0.0, 4.0, yy - origin_y_m)
        * _smoothstep(0.0, 4.0, origin_y_m + span_y_m - yy)
    )
    relief = np.clip((broad + fine + rills) * channel_fade * edge_fade, -0.38, 0.38)
    conditioned = base + relief

    terrain_min_m = float(conditioned.min())
    terrain_max_m = float(conditioned.max())
    terrain_span_m = terrain_max_m - terrain_min_m
    if terrain_span_m <= 0.0:
        raise ValueError("Upper Huacas conditioned terrain has no elevation range")
    normalized = np.clip((conditioned - terrain_min_m) / terrain_span_m, 0.0, 1.0)
    heightfield_u16 = np.round(normalized * 65535.0).astype(np.uint16)

    heightfield_path = (
        output_root / f"upper_huacas_conditioned_heightfield_{output_size_px}.png"
    )
    centerline_path = output_root / "upper_huacas_local_centerline.json"
    coordinate_map_path = output_root / "upper_huacas_runtime_coordinate_map.json"
    manifest_path = output_root / "upper_huacas_visual_terrain_manifest.json"
    Image.fromarray(heightfield_u16).save(heightfield_path)

    eta = bed + depth
    runtime_vertical_datum_m = float(np.mean(eta[wet]))
    channel_half_width_m = float(
        window_manifest["conditioning"]["channel_half_width_m"]
    )
    source_y = origin_y_m + np.arange(ny, dtype=np.float64) * dy_m
    channel_rows = np.abs(source_y) <= channel_half_width_m
    centerline_surface = np.empty(nx, dtype=np.float64)
    centerline_bed = np.empty(nx, dtype=np.float64)
    for column in range(nx):
        wet_rows = channel_rows & wet[:, column]
        rows = wet_rows if wet_rows.any() else channel_rows
        centerline_surface[column] = float(np.median(eta[rows, column]))
        centerline_bed[column] = float(np.median(bed[rows, column]))

    local_center_y_cm = -origin_y_m * 100.0
    centerline_points: list[dict[str, object]] = []
    for column in range(nx):
        station_m = origin_x_m + column * dx_m
        surface_m = float(centerline_surface[column])
        bed_m = float(centerline_bed[column])
        centerline_points.append(
            {
                "station_m": station_m,
                "unreal_local_cm": [station_m * 100.0, local_center_y_cm],
                "conditioned_visual_surface_elevation_m": surface_m,
                "conditioned_visual_bed_elevation_m": bed_m,
                "conditioned_visual_surface_normalized": (surface_m - terrain_min_m)
                / terrain_span_m,
                "conditioned_visual_bed_normalized": (bed_m - terrain_min_m)
                / terrain_span_m,
            }
        )
    centerline = {
        "schema": "raftsim.local_centerline.v1",
        "river_id": "pacuare",
        "section_id": "upper_huacas_station_17000m_c3_window",
        "local_metric_policy": (
            "channel-following C3 coordinates; Unreal X is downstream station and "
            "Unreal Y is cross-channel distance shifted from [-39,39] m to [0,78] m"
        ),
        "points": centerline_points,
    }
    centerline_path.write_text(
        json.dumps(centerline, indent=2) + "\n", encoding="utf-8"
    )

    # The cooked solver grid already uses station/lateral coordinates.  Emit a
    # straight coordinate map anyway so the runtime can apply the same explicit
    # vertical datum used to place the reach-local Landscape.  Without this,
    # absolute source elevations around 454 m would be interpreted as local
    # Unreal elevations even though the visual reach is intentionally re-zeroed.
    coordinate_map = {
        "schema": "raftsim.curved_river_coordinate_map.v1",
        "river_id": "pacuare",
        "section_id": "upper_huacas_station_17000m_c3_window",
        "vertical_datum_m": runtime_vertical_datum_m,
        "mapping_policy": (
            "identity station/lateral map for the straight C3 runtime grid; "
            "vertical datum aligns absolute cooked elevations to the local Unreal reach"
        ),
        "points": [
            [
                origin_x_m + column * dx_m,
                origin_x_m + column * dx_m,
                0.0,
                0.0,
                1.0,
            ]
            for column in range(nx)
        ],
    }
    coordinate_map_path.write_text(
        json.dumps(coordinate_map, indent=2) + "\n", encoding="utf-8"
    )

    protected_mask = np.abs(yy) <= protected_channel_half_width_m
    edge_mask = (
        (xx - origin_x_m <= 0.01)
        | (origin_x_m + span_x_m - xx <= 0.01)
        | (yy - origin_y_m <= 0.01)
        | (origin_y_m + span_y_m - yy <= 0.01)
    )
    runtime_vertical_offset_cm = -(runtime_vertical_datum_m - terrain_min_m) * 100.0
    static_centerline_world_surface_m = (
        centerline_surface - terrain_min_m + runtime_vertical_offset_cm / 100.0
    )
    runtime_centerline_surface_m = centerline_surface - runtime_vertical_datum_m
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "status": (
            "generated_review_gated_reach_local_visual_and_collision_infill_"
            "not_solver_survey_or_production_terrain_authority"
        ),
        "river_id": "pacuare",
        "section_id": "upper_huacas_station_17000m_c3_window",
        "reference_flow_band": REFERENCE_BAND,
        "inputs": {
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
            "horizontal_span_y_m": span_y_m,
            "sample_spacing_x_m": span_x_m / (output_size_px - 1),
            "sample_spacing_y_m": span_y_m / (output_size_px - 1),
            "terrain_min_m": terrain_min_m,
            "terrain_max_m": terrain_max_m,
            "target_relief_cm": terrain_span_m * 100.0,
            "world_vertical_offset_cm": runtime_vertical_offset_cm,
            "runtime_vertical_datum_m": runtime_vertical_datum_m,
        },
        "procedural_infill": {
            "algorithm": "deterministic_domain_warped_multiscale_bank_relief_v1",
            "maximum_absolute_relief_m": float(np.max(np.abs(relief))),
            "protected_channel_half_width_m": protected_channel_half_width_m,
            "full_infill_cross_channel_m": full_infill_cross_m,
            "longitudinal_edge_fade_m": 14.0,
            "cross_channel_edge_fade_m": 4.0,
            "maximum_protected_channel_change_m": float(
                np.max(np.abs(relief[protected_mask]))
            ),
            "maximum_map_edge_change_m": float(np.max(np.abs(relief[edge_mask]))),
            "authority": (
                "bounded_visual_and_landscape_collision_infill_only; cooked C3 bed, "
                "water state, solver forces, and source macroscale terrain are unchanged"
            ),
        },
        "alignment": {
            "world_x_matches_runtime_station_m": True,
            "world_y_matches_runtime_cross_channel_m": True,
            "maximum_static_to_runtime_centerline_surface_error_m": float(
                np.max(
                    np.abs(
                        static_centerline_world_surface_m - runtime_centerline_surface_m
                    )
                )
            ),
            "static_water_flow_offset_cm": 0.0,
        },
        "honesty": {
            "source_macro_geometry_authority": window_manifest["conditioning"][
                "authority"
            ],
            "procedural_gap_fill_authority": "visual_and_collision_infill_not_survey",
            "solver_authority": _relative(cooked_manifest_path, repo_root),
            "production_promoted": False,
            "pending_human_review": True,
            "missing": [
                "surveyed bathymetry and bank breaklines",
                "reviewed exact Upper Huacas stationing and planform",
                "higher-resolution route-local terrain",
                "guide, geospatial, ecology, art, and performance acceptance",
            ],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
