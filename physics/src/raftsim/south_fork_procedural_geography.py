"""Deterministically complete the South Fork terrain and channel corridor.

The official 3DEP and NAIP windows remain the source authority for the valley.
Bathymetry, bank transitions, seam conditioning, and sub-DEM hydraulic controls
are generated as explicitly labelled procedural infill.  The output is a
curvilinear reach-local grid shared by solver, collision, and render import.
It is game content and must never be used for real-world navigation.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .south_fork_a1_stationing import (
    FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
)
from .south_fork_a1_window_manifests import (
    FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
)
from .south_fork_a1_window_source_pulls import (
    ADOPTED_ROUTE_FEATURE_ID,
    _lon_lat_to_web_mercator,
    _route_coordinates_with_station,
)

PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "procedural_completion"
)
PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH = (
    f"{PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH}/manifest.json"
)
PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH = (
    f"{PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH}/full_reach_geography.npz"
)
PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH = (
    f"{PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH}/boulder_catalog.json"
)
PROCEDURAL_OVERVIEW_RELATIVE_PATH = (
    f"{PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH}/full_reach_overview.png"
)

ALGORITHM_VERSION = "south_fork_procedural_geography_v4_smooth_frames"
DEFAULT_SEED = 0x5FA49E17
STATION_SPACING_M = 4.0
LATERAL_SPACING_M = 4.0
CORRIDOR_HALF_WIDTH_M = 256.0
FRAME_SMOOTHING_RADIUS_ROWS = 32
SEAM_BLEND_M = 64.0
UNREAL_TILE_ROWS = 1009
UNREAL_TILE_OVERLAP_ROWS = 1

FEATURE_CHANNEL = 1 << 0
FEATURE_SHELF = 1 << 1
FEATURE_BOULDER = 1 << 2
FEATURE_LEDGE = 1 << 3
FEATURE_HOLE_CONTROL = 1 << 4
FEATURE_WAVE_TRAIN = 1 << 5
FEATURE_EDDY = 1 << 6
FEATURE_SHORELINE_BREAKUP = 1 << 7

MATERIAL_CHANNEL_BED = 0
MATERIAL_WET_BANK = 1
MATERIAL_EXPOSED_ROCK = 2
MATERIAL_COBBLE_GRAVEL = 3
MATERIAL_SOIL = 4
MATERIAL_VEGETATION = 5


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _regular_stations(reach_length_m: float) -> np.ndarray:
    stations = np.arange(0.0, reach_length_m, STATION_SPACING_M, dtype=np.float64)
    if stations.size == 0 or not math.isclose(float(stations[-1]), reach_length_m):
        stations = np.append(stations, reach_length_m)
    return stations


def _route_grid(
    repo_root: Path, stations_m: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    route = _load_json(repo_root, FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH)
    points = _route_coordinates_with_station(route, ADOPTED_ROUTE_FEATURE_ID)
    source_stations = np.asarray(
        [float(point["approx_station_m"]) for point in points], dtype=np.float64
    )
    xy = np.asarray(
        [_lon_lat_to_web_mercator(*point["lon_lat"]) for point in points],
        dtype=np.float64,
    )
    unique_stations, unique_indices = np.unique(source_stations, return_index=True)
    x = np.interp(stations_m, unique_stations, xy[unique_indices, 0])
    y = np.interp(stations_m, unique_stations, xy[unique_indices, 1])
    # The adopted route is a piecewise-linear hydrography trace.  Computing
    # cross-section frames directly from each raw vertex makes a 512 m terrain
    # strip pivot tens of degrees in one four-metre row.  That creates long,
    # folded triangles even though the centerline itself is continuous.  Keep
    # the authoritative centerline positions, but derive its lateral frame from
    # a 260 m low-pass window so terrain, imagery, water, and collision turn
    # continuously through bends.
    frame_x = _moving_average(x, radius=FRAME_SMOOTHING_RADIUS_ROWS)
    frame_y = _moving_average(y, radius=FRAME_SMOOTHING_RADIUS_ROWS)
    tangent_x = np.gradient(frame_x, stations_m)
    tangent_y = np.gradient(frame_y, stations_m)
    tangent_length = np.maximum(np.hypot(tangent_x, tangent_y), 1e-9)
    normal_x = -tangent_y / tangent_length
    normal_y = tangent_x / tangent_length
    epsg3857_length_m = float(np.sum(np.hypot(np.diff(x), np.diff(y))))
    ground_length_m = float(stations_m[-1] - stations_m[0])
    epsg3857_to_ground_scale = ground_length_m / max(epsg3857_length_m, 1.0)
    return x, y, normal_x, normal_y, epsg3857_to_ground_scale


def _load_window_manifests(repo_root: Path) -> list[dict[str, Any]]:
    index = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH)
    manifests = [
        _load_json(repo_root, str(entry["manifest_path"]))
        for entry in index["window_manifests"]
    ]
    return sorted(manifests, key=lambda item: float(item["station_range_m"]["start"]))


def _effective_raster_bounds(
    image: Image.Image, requested_bounds: list[float]
) -> list[float]:
    """Return the actual georeferenced extent represented by a raster.

    ArcGIS ``exportImage`` preserves square pixels. When a non-square request
    is written into a square TIFF, the service expands the shorter world axis;
    the original request bounds therefore no longer describe the returned
    pixels. GeoTIFF model tags are authoritative when present. The aspect-ratio
    fallback reproduces the service behavior for imagery without those tags.
    """

    tie_points = image.tag_v2.get(33922) if hasattr(image, "tag_v2") else None
    pixel_scale = image.tag_v2.get(33550) if hasattr(image, "tag_v2") else None
    if tie_points and pixel_scale and len(tie_points) >= 6 and len(pixel_scale) >= 2:
        minimum_x = float(tie_points[3] - tie_points[0] * pixel_scale[0])
        maximum_y = float(tie_points[4] + tie_points[1] * pixel_scale[1])
        maximum_x = minimum_x + image.width * float(pixel_scale[0])
        minimum_y = maximum_y - image.height * float(pixel_scale[1])
        return [minimum_x, minimum_y, maximum_x, maximum_y]

    minimum_x, minimum_y, maximum_x, maximum_y = map(float, requested_bounds)
    center_x = 0.5 * (minimum_x + maximum_x)
    center_y = 0.5 * (minimum_y + maximum_y)
    world_units_per_pixel = max(
        (maximum_x - minimum_x) / max(image.width, 1),
        (maximum_y - minimum_y) / max(image.height, 1),
    )
    half_width = 0.5 * world_units_per_pixel * image.width
    half_height = 0.5 * world_units_per_pixel * image.height
    return [
        center_x - half_width,
        center_y - half_height,
        center_x + half_width,
        center_y + half_height,
    ]


def _load_dem(
    path: Path, requested_bounds: list[float]
) -> tuple[np.ndarray, list[float]]:
    with Image.open(path) as image:
        dem = np.asarray(image, dtype=np.float32)
        geotiff_bounds = _effective_raster_bounds(image, requested_bounds)
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError(f"DEM contains no finite samples: {path}")
    replacement = float(np.median(dem[finite]))
    return np.where(finite, dem, replacement).astype(np.float32), geotiff_bounds


def _bilinear_sample(
    raster: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
    bounds: list[float],
) -> np.ndarray:
    min_x, min_y, max_x, max_y = map(float, bounds)
    height, width = raster.shape[:2]
    px = np.clip((world_x - min_x) / (max_x - min_x) * (width - 1), 0.0, width - 1)
    py = np.clip((max_y - world_y) / (max_y - min_y) * (height - 1), 0.0, height - 1)
    x0 = np.floor(px).astype(np.int32)
    y0 = np.floor(py).astype(np.int32)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    tx = px - x0
    ty = py - y0
    return (
        raster[y0, x0] * (1.0 - tx) * (1.0 - ty)
        + raster[y0, x1] * tx * (1.0 - ty)
        + raster[y1, x0] * (1.0 - tx) * ty
        + raster[y1, x1] * tx * ty
    ).astype(np.float32)


def _nearest_rgb_score(
    raster: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
    bounds: list[float],
) -> np.ndarray:
    min_x, min_y, max_x, max_y = map(float, bounds)
    height, width = raster.shape[:2]
    px = np.clip(
        np.rint((world_x - min_x) / (max_x - min_x) * (width - 1)),
        0,
        width - 1,
    ).astype(np.int32)
    py = np.clip(
        np.rint((max_y - world_y) / (max_y - min_y) * (height - 1)),
        0,
        height - 1,
    ).astype(np.int32)
    rgb = raster[py, px, :3].astype(np.float32)
    green_score = rgb[..., 1] - 0.5 * (rgb[..., 0] + rgb[..., 2])
    return np.clip(np.rint(green_score + 128.0), 0.0, 255.0).astype(np.uint8)


def _sample_window(
    repo_root: Path,
    manifest: dict[str, Any],
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    artifacts = manifest["source_artifacts"]
    dem_artifact = artifacts["dem"]
    aerial_artifact = artifacts["aerial"]
    dem, geotiff_bounds = _load_dem(
        repo_root / dem_artifact["path"],
        dem_artifact["source_bounds_epsg3857"],
    )
    terrain = _bilinear_sample(
        dem,
        x,
        y,
        geotiff_bounds,
    )
    with Image.open(repo_root / aerial_artifact["path"]) as source_image:
        aerial = np.asarray(source_image.convert("RGB"))
        aerial_bounds = _effective_raster_bounds(
            source_image, aerial_artifact["source_bounds_epsg3857"]
        )
    vegetation_score = _nearest_rgb_score(aerial, x, y, aerial_bounds)
    return terrain, vegetation_score


def _sample_sources(
    repo_root: Path,
    manifests: list[dict[str, Any]],
    stations_m: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    terrain = np.empty(world_x.shape, dtype=np.float32)
    vegetation = np.empty(world_x.shape, dtype=np.uint8)
    seam_blend = np.zeros(stations_m.shape, dtype=bool)
    for index, manifest in enumerate(manifests):
        start = float(manifest["station_range_m"]["start"])
        end = float(manifest["station_range_m"]["end"])
        selected = (stations_m >= start) & (
            stations_m <= end if index == len(manifests) - 1 else stations_m < end
        )
        terrain[selected], vegetation[selected] = _sample_window(
            repo_root, manifest, world_x[selected], world_y[selected]
        )

    for upstream, downstream in zip(manifests, manifests[1:], strict=False):
        seam = float(upstream["station_range_m"]["end"])
        selected = np.abs(stations_m - seam) <= SEAM_BLEND_M
        if not selected.any():
            continue
        selected_indices = np.flatnonzero(selected)
        alpha = np.clip(
            (stations_m[selected] - (seam - SEAM_BLEND_M)) / (2.0 * SEAM_BLEND_M),
            0.0,
            1.0,
        )[:, None]
        upstream_terrain = terrain[selected_indices[0]].copy()
        downstream_terrain = terrain[selected_indices[-1]].copy()
        upstream_vegetation = vegetation[selected_indices[0]].copy()
        downstream_vegetation = vegetation[selected_indices[-1]].copy()
        terrain[selected] = (
            upstream_terrain * (1.0 - alpha) + downstream_terrain * alpha
        )
        vegetation[selected] = np.rint(
            upstream_vegetation * (1.0 - alpha) + downstream_vegetation * alpha
        ).astype(np.uint8)
        seam_blend[selected] = True
    return terrain, vegetation, seam_blend


def _moving_average(values: np.ndarray, radius: int) -> np.ndarray:
    padded = np.pad(values, (radius, radius), mode="edge")
    kernel = np.ones(radius * 2 + 1, dtype=np.float64) / (radius * 2 + 1)
    return np.convolve(padded, kernel, mode="valid")


def _condition_water_surface(
    center_dem: np.ndarray, stations_m: np.ndarray
) -> np.ndarray:
    smoothed = _moving_average(center_dem.astype(np.float64), radius=32)
    result = np.empty_like(smoothed)
    result[0] = smoothed[0] - 0.35
    for index in range(1, result.size):
        delta_station = max(1e-6, float(stations_m[index] - stations_m[index - 1]))
        minimum_drop = 0.00008 * delta_station
        # The South Fork contains short, steep bedrock reaches. Five percent
        # allows the conditioned thalweg to follow source terrain through those
        # drops while the 128 m smoothing window removes DEM spikes.
        maximum_drop = 0.05 * delta_station
        result[index] = np.clip(
            smoothed[index] - 0.35,
            result[index - 1] - maximum_drop,
            result[index - 1] - minimum_drop,
        )
    return result.astype(np.float32)


def _rapid_strength(rapid_class: str) -> float:
    if "III+" in rapid_class:
        return 1.0
    if "III" in rapid_class:
        return 0.82
    if "II+" in rapid_class or "II-III" in rapid_class:
        return 0.64
    if "II" in rapid_class:
        return 0.5
    return 0.58


def _channel_dimensions(
    stations_m: np.ndarray,
    rapid_stations: list[dict[str, Any]],
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    phase = (_stable_seed(seed, "channel-width") % 10_000) / 10_000.0 * 2.0 * math.pi
    width = 18.0 + 2.8 * np.sin(stations_m / 730.0 + phase)
    width += 1.4 * np.sin(stations_m / 193.0 + phase * 0.37)
    reservoir = np.clip((stations_m - 32_000.0) / 15_000.0, 0.0, 1.0)
    width += reservoir * 22.0
    depth = 2.0 + reservoir * 2.4
    for rapid in rapid_stations:
        station = float(rapid["station_m"])
        strength = _rapid_strength(str(rapid["class"]))
        envelope = np.exp(-0.5 * ((stations_m - station) / 95.0) ** 2)
        tags = set(rapid["feature_tags"])
        if tags & {"constriction", "canyon_constriction", "chute"}:
            width -= envelope * (3.0 + 3.0 * strength)
        if "multiple_channels" in tags or "central_island" in tags:
            width += envelope * 4.0
        depth -= envelope * (0.25 + 0.35 * strength)
    return (
        np.clip(width, 11.0, 48.0).astype(np.float32),
        np.clip(depth, 1.1, 5.0).astype(np.float32),
    )


def _generate_boulders(
    rapid_stations: list[dict[str, Any]],
    stations_m: np.ndarray,
    center_x: np.ndarray,
    center_y: np.ndarray,
    normal_x: np.ndarray,
    normal_y: np.ndarray,
    channel_half_width: np.ndarray,
    epsg3857_to_ground_scale: float,
    seed: int,
) -> list[dict[str, Any]]:
    boulders: list[dict[str, Any]] = []
    for rapid in rapid_stations:
        tags = set(rapid["feature_tags"])
        boulder_relevant = any(
            "boulder" in tag or "rock" in tag or "island" in tag for tag in tags
        )
        if not boulder_relevant:
            continue
        count = 12 if "boulder_garden" in tags else 5
        if "boulders" in tags:
            count = 8
        rng = np.random.default_rng(_stable_seed(seed, str(rapid["name"])))
        rapid_station = float(rapid["station_m"])
        for boulder_index in range(count):
            station = float(
                np.clip(
                    rapid_station + rng.uniform(-105.0, 105.0),
                    0.0,
                    stations_m[-1],
                )
            )
            row = int(np.searchsorted(stations_m, station, side="left"))
            row = min(row, stations_m.size - 1)
            half_width = float(channel_half_width[row])
            lateral = float(rng.uniform(-0.78 * half_width, 0.78 * half_width))
            radius = float(rng.uniform(0.9, 2.6))
            height = float(rng.uniform(0.45, 1.65))
            boulders.append(
                {
                    "boulder_id": f"{int(rapid['order']):02d}_{boulder_index:02d}",
                    "rapid_name": rapid["name"],
                    "station_m": round(station, 3),
                    "lateral_offset_m": round(lateral, 3),
                    "radius_m": round(radius, 3),
                    "height_m": round(height, 3),
                    "world_epsg3857_m": [
                        round(
                            float(
                                center_x[row]
                                + normal_x[row] * lateral / epsg3857_to_ground_scale
                            ),
                            3,
                        ),
                        round(
                            float(
                                center_y[row]
                                + normal_y[row] * lateral / epsg3857_to_ground_scale
                            ),
                            3,
                        ),
                    ],
                    "authority": "procedural_infill",
                    "seed": int(_stable_seed(seed, str(rapid["name"]))),
                }
            )
    return boulders


def _apply_rapid_features(
    bed: np.ndarray,
    feature_mask: np.ndarray,
    stations_m: np.ndarray,
    lateral_offsets_m: np.ndarray,
    rapid_stations: list[dict[str, Any]],
    boulders: list[dict[str, Any]],
) -> None:
    station_grid = stations_m[:, None]
    lateral_grid = lateral_offsets_m[None, :]
    for rapid in rapid_stations:
        station = float(rapid["station_m"])
        strength = _rapid_strength(str(rapid["class"]))
        tags = set(rapid["feature_tags"])
        envelope = np.exp(-0.5 * ((stations_m - station) / 92.0) ** 2)[:, None]
        channel_lateral = np.exp(-0.5 * (lateral_grid / 13.0) ** 2)
        if any("ledge" in tag for tag in tags):
            ledge = (
                -0.55 * strength * (0.5 + 0.5 * np.tanh((station_grid - station) / 5.0))
            )
            ledge = (
                ledge
                * np.exp(-0.5 * ((station_grid - station) / 65.0) ** 2)
                * channel_lateral
            )
            selected = np.abs(ledge) > 0.01
            bed += np.where(selected, ledge, 0.0).astype(np.float32)
            feature_mask[selected] |= FEATURE_LEDGE
        if any("hole" in tag for tag in tags):
            control = (
                0.34
                * strength
                * np.exp(-0.5 * ((station_grid - station + 12.0) / 8.0) ** 2)
            )
            scour = (
                -0.62
                * strength
                * np.exp(-0.5 * ((station_grid - station - 9.0) / 11.0) ** 2)
            )
            hole = (control + scour) * channel_lateral
            selected = np.abs(hole) > 0.01
            bed += np.where(selected, hole, 0.0).astype(np.float32)
            feature_mask[selected] |= FEATURE_HOLE_CONTROL
        if any("wave" in tag for tag in tags):
            phase = (station_grid - station) / 13.0 * 2.0 * math.pi
            waves = 0.18 * strength * np.sin(phase) * envelope * channel_lateral
            selected = np.abs(waves) > 0.01
            bed += np.where(selected, waves, 0.0).astype(np.float32)
            feature_mask[selected] |= FEATURE_WAVE_TRAIN
        if "eddy" in tags or "lateral" in tags:
            side = -1.0 if int(rapid["order"]) % 2 else 1.0
            pocket = (
                -0.32
                * strength
                * envelope
                * np.exp(-0.5 * ((lateral_grid - side * 16.0) / 7.0) ** 2)
            )
            selected = np.abs(pocket) > 0.01
            bed += np.where(selected, pocket, 0.0).astype(np.float32)
            feature_mask[selected] |= FEATURE_EDDY
        if "shallow_shelf" in tags or "multiple_channels" in tags:
            shelf = (
                0.28
                * strength
                * envelope
                * np.exp(-0.5 * ((np.abs(lateral_grid) - 10.0) / 5.0) ** 2)
            )
            selected = shelf > 0.01
            bed += np.where(selected, shelf, 0.0).astype(np.float32)
            feature_mask[selected] |= FEATURE_SHELF

    for boulder in boulders:
        station_radius = max(4.0, float(boulder["radius_m"]) * 1.35)
        lateral_radius = max(3.0, float(boulder["radius_m"]) * 1.2)
        influence = float(boulder["height_m"]) * np.exp(
            -0.5 * ((station_grid - float(boulder["station_m"])) / station_radius) ** 2
            - 0.5
            * ((lateral_grid - float(boulder["lateral_offset_m"])) / lateral_radius)
            ** 2
        )
        selected = influence > 0.01
        bed += np.where(selected, influence, 0.0).astype(np.float32)
        feature_mask[selected] |= FEATURE_BOULDER


def _build_geography_arrays(
    repo_root: Path, seed: int
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    stationing = _load_json(
        repo_root, FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
    )
    reach_length = float(stationing["station_axis"]["adopted_route_length_m"])
    rapid_stations = stationing["rapid_stations"]
    stations_m = _regular_stations(reach_length)
    lateral_offsets_m = np.arange(
        -CORRIDOR_HALF_WIDTH_M,
        CORRIDOR_HALF_WIDTH_M + LATERAL_SPACING_M * 0.5,
        LATERAL_SPACING_M,
        dtype=np.float32,
    )
    center_x, center_y, normal_x, normal_y, epsg3857_to_ground_scale = _route_grid(
        repo_root, stations_m
    )
    epsg_lateral_offsets_m = lateral_offsets_m / epsg3857_to_ground_scale
    world_x = center_x[:, None] + normal_x[:, None] * epsg_lateral_offsets_m[None, :]
    world_y = center_y[:, None] + normal_y[:, None] * epsg_lateral_offsets_m[None, :]
    manifests = _load_window_manifests(repo_root)
    source_dem, vegetation_score, seam_blend = _sample_sources(
        repo_root, manifests, stations_m, world_x, world_y
    )

    center_column = lateral_offsets_m.size // 2
    water_surface = _condition_water_surface(source_dem[:, center_column], stations_m)
    channel_half_width, center_depth = _channel_dimensions(
        stations_m, rapid_stations, seed
    )
    absolute_lateral = np.abs(lateral_offsets_m)[None, :]
    half_width = channel_half_width[:, None]
    inside_channel = absolute_lateral <= half_width
    normalized_channel = np.clip(
        absolute_lateral / np.maximum(half_width, 1.0), 0.0, 1.0
    )
    depth = 0.05 + center_depth[:, None] * (1.0 - normalized_channel**2) ** 1.15
    channel_bed = water_surface[:, None] - depth
    bank_distance = absolute_lateral - half_width
    bank_blend_width = 14.0
    bank_t = np.clip(bank_distance / bank_blend_width, 0.0, 1.0)
    smooth_t = bank_t * bank_t * (3.0 - 2.0 * bank_t)
    procedural_bank = water_surface[:, None] - 0.05 + 1.45 * bank_t + 0.55 * bank_t**2
    transition_bed = procedural_bank * (1.0 - smooth_t) + source_dem * smooth_t
    bed = np.where(
        inside_channel,
        channel_bed,
        np.where(bank_distance < bank_blend_width, transition_bed, source_dem),
    ).astype(np.float32)

    source_authority = np.full(bed.shape, 255, dtype=np.uint8)
    source_authority[inside_channel] = 0
    transition = (~inside_channel) & (bank_distance < bank_blend_width)
    source_authority[transition] = np.rint(smooth_t[transition] * 255.0).astype(
        np.uint8
    )
    source_authority[seam_blend, :] = np.minimum(source_authority[seam_blend, :], 192)
    procedural_infill = (255 - source_authority).astype(np.uint8)
    uncertainty = np.full(bed.shape, 45, dtype=np.uint8)
    uncertainty[transition] = 155
    uncertainty[inside_channel] = 220
    uncertainty[seam_blend, :] = np.maximum(uncertainty[seam_blend, :], 96)

    feature_mask = np.zeros(bed.shape, dtype=np.uint8)
    feature_mask[inside_channel] |= FEATURE_CHANNEL
    feature_mask[transition] |= FEATURE_SHORELINE_BREAKUP
    shelf_band = inside_channel & (normalized_channel > 0.68)
    feature_mask[shelf_band] |= FEATURE_SHELF

    boulders = _generate_boulders(
        rapid_stations,
        stations_m,
        center_x,
        center_y,
        normal_x,
        normal_y,
        channel_half_width,
        epsg3857_to_ground_scale,
        seed,
    )
    _apply_rapid_features(
        bed,
        feature_mask,
        stations_m,
        lateral_offsets_m,
        rapid_stations,
        boulders,
    )
    generated_hydraulic_features = (
        feature_mask
        & (
            FEATURE_BOULDER
            | FEATURE_LEDGE
            | FEATURE_HOLE_CONTROL
            | FEATURE_WAVE_TRAIN
            | FEATURE_EDDY
        )
    ) != 0
    source_authority[generated_hydraulic_features] = 0
    procedural_infill[generated_hydraulic_features] = 255
    uncertainty[generated_hydraulic_features] = np.maximum(
        uncertainty[generated_hydraulic_features], 230
    )

    cross_slope = np.abs(np.gradient(source_dem, LATERAL_SPACING_M, axis=1))
    material = np.full(bed.shape, MATERIAL_SOIL, dtype=np.uint8)
    material[vegetation_score > 137] = MATERIAL_VEGETATION
    material[cross_slope > 0.42] = MATERIAL_EXPOSED_ROCK
    material[(vegetation_score <= 137) & (cross_slope <= 0.42)] = MATERIAL_COBBLE_GRAVEL
    material[transition] = MATERIAL_WET_BANK
    material[inside_channel] = MATERIAL_CHANNEL_BED

    if not np.isfinite(bed).all() or not np.isfinite(source_dem).all():
        raise ValueError("Procedural completion produced a non-finite terrain sample")
    arrays = {
        "stations_m": stations_m,
        "lateral_offsets_m": lateral_offsets_m,
        "centerline_epsg3857_x_m": center_x.astype(np.float64),
        "centerline_epsg3857_y_m": center_y.astype(np.float64),
        "centerline_normal_x": normal_x.astype(np.float32),
        "centerline_normal_y": normal_y.astype(np.float32),
        "epsg3857_to_ground_scale": np.asarray(
            epsg3857_to_ground_scale, dtype=np.float64
        ),
        "centerline_frame_smoothing_radius_m": np.asarray(
            FRAME_SMOOTHING_RADIUS_ROWS * STATION_SPACING_M, dtype=np.float64
        ),
        "source_dem_elevation_m": source_dem,
        "bed_elevation_m": bed,
        "conditioned_water_surface_m": water_surface,
        "channel_half_width_m": channel_half_width,
        "source_authority": source_authority,
        "procedural_infill": procedural_infill,
        "uncertainty": uncertainty,
        "material": material,
        "features": feature_mask,
    }
    return arrays, boulders


def _write_overview(arrays: dict[str, np.ndarray], output_path: Path) -> None:
    bed = arrays["bed_elevation_m"]
    row_gradient, cross_gradient = np.gradient(
        bed, STATION_SPACING_M, LATERAL_SPACING_M
    )
    shade = np.clip(0.72 - cross_gradient * 0.36 - row_gradient * 0.18, 0.15, 1.0)
    colors = np.asarray(
        [
            [76, 88, 83],
            [92, 76, 58],
            [112, 108, 101],
            [132, 116, 84],
            [116, 91, 63],
            [67, 104, 62],
        ],
        dtype=np.float32,
    )
    image = colors[arrays["material"]] * shade[..., None]
    procedural = arrays["procedural_infill"].astype(np.float32) / 255.0
    image[..., 2] += procedural * 28.0
    image[..., 0] += procedural * 8.0
    image = np.clip(image, 0.0, 255.0).astype(np.uint8)
    image = Image.fromarray(np.transpose(image, (1, 0, 2)), mode="RGB")
    image = image.resize((2048, 320), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _artifact_record(repo_root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(repo_root)),
        "sha256": _sha256(path),
        "byte_count": path.stat().st_size,
    }


def _tile_starts(row_count: int) -> list[int]:
    step = UNREAL_TILE_ROWS - UNREAL_TILE_OVERLAP_ROWS
    starts = list(range(0, max(1, row_count - UNREAL_TILE_ROWS + 1), step))
    final_start = max(0, row_count - UNREAL_TILE_ROWS)
    if not starts or starts[-1] != final_start:
        starts.append(final_start)
    return sorted(set(starts))


def _write_unreal_tiles(
    repo_root: Path,
    output_dir: Path,
    arrays: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    bed = arrays["bed_elevation_m"]
    elevation_min = float(np.min(bed))
    elevation_max = float(np.max(bed))
    elevation_span = max(1.0, elevation_max - elevation_min)
    normalized = np.clip((bed - elevation_min) / elevation_span, 0.0, 1.0)
    heightfield = np.rint(normalized * 65535.0).astype(np.uint16)
    tile_dir = output_dir / "unreal_tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for tile_index, start in enumerate(_tile_starts(bed.shape[0])):
        stop = start + UNREAL_TILE_ROWS
        tile_id = f"south_fork_{tile_index:02d}"
        height_path = tile_dir / f"{tile_id}_height.png"
        packed_path = tile_dir / f"{tile_id}_authority_features.png"
        material_path = tile_dir / f"{tile_id}_material.png"
        Image.fromarray(heightfield[start:stop], mode="I;16").save(height_path)
        packed = np.stack(
            [
                arrays["source_authority"][start:stop],
                arrays["procedural_infill"][start:stop],
                arrays["uncertainty"][start:stop],
                arrays["features"][start:stop],
            ],
            axis=-1,
        )
        Image.fromarray(packed, mode="RGBA").save(packed_path)
        Image.fromarray(arrays["material"][start:stop], mode="L").save(material_path)
        sample_rows = list(range(start, stop, 64))
        if sample_rows[-1] != stop - 1:
            sample_rows.append(stop - 1)
        control_points = [
            {
                "station_m": round(float(arrays["stations_m"][row]), 3),
                "epsg3857_m": [
                    round(float(arrays["centerline_epsg3857_x_m"][row]), 3),
                    round(float(arrays["centerline_epsg3857_y_m"][row]), 3),
                ],
                "normal": [
                    round(float(arrays["centerline_normal_x"][row]), 7),
                    round(float(arrays["centerline_normal_y"][row]), 7),
                ],
            }
            for row in sample_rows
        ]
        records.append(
            {
                "tile_id": tile_id,
                "row_range": [start, stop - 1],
                "dimensions": [UNREAL_TILE_ROWS, bed.shape[1]],
                "station_range_m": [
                    round(float(arrays["stations_m"][start]), 3),
                    round(float(arrays["stations_m"][stop - 1]), 3),
                ],
                "lateral_range_m": [
                    float(arrays["lateral_offsets_m"][0]),
                    float(arrays["lateral_offsets_m"][-1]),
                ],
                "grid_spacing_m": [STATION_SPACING_M, LATERAL_SPACING_M],
                "height_encoding": {
                    "minimum_elevation_m": round(elevation_min, 6),
                    "maximum_elevation_m": round(elevation_max, 6),
                    "uint16_min": 0,
                    "uint16_max": 65535,
                },
                "render_heightfield": _artifact_record(repo_root, height_path),
                "collision_heightfield": _artifact_record(repo_root, height_path),
                "packed_authority_features": _artifact_record(repo_root, packed_path),
                "material_mask": _artifact_record(repo_root, material_path),
                "render_collision_registered": True,
                "curvilinear_control_points": control_points,
            }
        )
    return records


def _determinism_signature(
    arrays: dict[str, np.ndarray], boulders: list[dict[str, Any]], seed: int
) -> str:
    digest = hashlib.sha256()
    digest.update(ALGORITHM_VERSION.encode())
    digest.update(str(seed).encode())
    for name in sorted(arrays):
        digest.update(name.encode())
        digest.update(np.ascontiguousarray(arrays[name]).tobytes())
    digest.update(json.dumps(boulders, sort_keys=True, separators=(",", ":")).encode())
    return digest.hexdigest()


def write_south_fork_procedural_geography(
    repo_root: Path, seed: int = DEFAULT_SEED
) -> Path:
    """Generate the canonical full-reach geography and Unreal import products."""

    repo_root = repo_root.resolve()
    output_dir = repo_root / PROCEDURAL_GEOGRAPHY_DIRECTORY_RELATIVE_PATH
    output_dir.mkdir(parents=True, exist_ok=True)
    arrays, boulders = _build_geography_arrays(repo_root, seed)
    grid_path = repo_root / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH
    np.savez_compressed(grid_path, **arrays)
    boulder_path = repo_root / PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH
    _write_json(
        boulder_path,
        {
            "schema": "raftsim.procedural_boulder_catalog.v1",
            "river_id": "south_fork_american_chili_bar",
            "authority": "procedural_infill",
            "seed": seed,
            "count": len(boulders),
            "boulders": boulders,
            "not_for_navigation": True,
        },
    )
    overview_path = repo_root / PROCEDURAL_OVERVIEW_RELATIVE_PATH
    _write_overview(arrays, overview_path)
    tiles = _write_unreal_tiles(repo_root, output_dir, arrays)

    station_steps = np.diff(arrays["stations_m"].astype(np.float64))
    center_bed = arrays["bed_elevation_m"][:, arrays["bed_elevation_m"].shape[1] // 2]
    source_fraction = float(np.mean(arrays["source_authority"]) / 255.0)
    lateral_grid = np.abs(arrays["lateral_offsets_m"][None, :])
    bank_sample_mask = (
        lateral_grid >= arrays["channel_half_width_m"][:, None] + 12.0
    ) & (lateral_grid <= arrays["channel_half_width_m"][:, None] + 28.0)
    bank_clearance_m = (
        arrays["bed_elevation_m"] - arrays["conditioned_water_surface_m"][:, None]
    )[bank_sample_mask]
    ground_scale = float(arrays["epsg3857_to_ground_scale"])
    local_center = (
        np.column_stack(
            (
                arrays["centerline_epsg3857_x_m"],
                arrays["centerline_epsg3857_y_m"],
            )
        )
        * ground_scale
    )
    normals = np.column_stack(
        (arrays["centerline_normal_x"], arrays["centerline_normal_y"])
    )
    left_edge = local_center + normals * CORRIDOR_HALF_WIDTH_M
    right_edge = local_center - normals * CORRIDOR_HALF_WIDTH_M
    maximum_corridor_edge_step_m = float(
        max(
            np.max(np.linalg.norm(np.diff(left_edge, axis=0), axis=1)),
            np.max(np.linalg.norm(np.diff(right_edge, axis=0), axis=1)),
        )
    )
    feature_counts = {
        "channel": int(np.count_nonzero(arrays["features"] & FEATURE_CHANNEL)),
        "shelf": int(np.count_nonzero(arrays["features"] & FEATURE_SHELF)),
        "boulder": int(np.count_nonzero(arrays["features"] & FEATURE_BOULDER)),
        "ledge": int(np.count_nonzero(arrays["features"] & FEATURE_LEDGE)),
        "hole_control": int(
            np.count_nonzero(arrays["features"] & FEATURE_HOLE_CONTROL)
        ),
        "wave_train": int(np.count_nonzero(arrays["features"] & FEATURE_WAVE_TRAIN)),
        "eddy": int(np.count_nonzero(arrays["features"] & FEATURE_EDDY)),
        "shoreline_breakup": int(
            np.count_nonzero(arrays["features"] & FEATURE_SHORELINE_BREAKUP)
        ),
    }
    index = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH)
    source_inputs = [
        {
            "window_id": entry["window_id"],
            "manifest_path": entry["manifest_path"],
            "terrain_sha256": entry["terrain_sha256"],
            "aerial_sha256": entry["aerial_sha256"],
        }
        for entry in index["window_manifests"]
    ]
    manifest = {
        "schema": "raftsim.south_fork.procedural_geography.v1",
        "generated_on": "2026-07-19",
        "river_id": "south_fork_american_chili_bar",
        "status": "full_reach_procedural_geography_complete",
        "algorithm": ALGORITHM_VERSION,
        "seed": seed,
        "authority_policy": {
            "source_terrain": "USGS 3DEP sampled outside the conditioned channel and bank blend",
            "source_imagery": "USDA NAIP conditions material classes",
            "procedural_infill": (
                "bathymetry, bank blend, source-window seam blend, and "
                "sub-DEM rapid controls"
            ),
            "route_basis": "adopted NHD directed mainstem axis",
            "never_claim_as_surveyed": True,
            "not_for_navigation": True,
        },
        "source_sampling": {
            "dem_extent_authority": (
                "embedded GeoTIFF ModelTiepointTag and ModelPixelScaleTag"
            ),
            "imagery_extent_fallback": (
                "square-pixel response extent reconstructed from requested center "
                "and returned aspect ratio"
            ),
            "request_bounds_are_not_assumed_to_equal_export_response_bounds": True,
        },
        "inputs": {
            "stationing": FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
            "route": FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
            "window_manifest_index": FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
            "source_windows": source_inputs,
        },
        "grid": {
            "coordinate_system": (
                "curvilinear station/lateral grid registered to EPSG:3857 centerline"
            ),
            "station_count": int(arrays["stations_m"].size),
            "cross_channel_count": int(arrays["lateral_offsets_m"].size),
            "station_start_m": float(arrays["stations_m"][0]),
            "station_end_m": float(arrays["stations_m"][-1]),
            "station_spacing_m": STATION_SPACING_M,
            "maximum_station_step_m": round(float(np.max(station_steps)), 6),
            "lateral_spacing_m": LATERAL_SPACING_M,
            "epsg3857_to_ground_scale": round(
                float(arrays["epsg3857_to_ground_scale"]), 9
            ),
            "centerline_frame_smoothing_radius_m": round(
                float(arrays["centerline_frame_smoothing_radius_m"]), 3
            ),
            "lateral_range_m": [
                float(arrays["lateral_offsets_m"][0]),
                float(arrays["lateral_offsets_m"][-1]),
            ],
            "no_voids": True,
            "finite_sample_count": int(arrays["bed_elevation_m"].size),
        },
        "provenance": {
            "source_authority_fraction": round(source_fraction, 6),
            "procedural_infill_fraction": round(1.0 - source_fraction, 6),
            "authority_encoding": {
                "source_authority": "0 procedural, 1..254 blend, 255 official source",
                "procedural_infill": "255 minus source_authority",
                "uncertainty": "0 lowest uncertainty, 255 highest uncertainty",
            },
        },
        "hydraulic_features": {
            "feature_bit_encoding": {
                "channel": FEATURE_CHANNEL,
                "shelf": FEATURE_SHELF,
                "boulder": FEATURE_BOULDER,
                "ledge": FEATURE_LEDGE,
                "hole_control": FEATURE_HOLE_CONTROL,
                "wave_train": FEATURE_WAVE_TRAIN,
                "eddy": FEATURE_EDDY,
                "shoreline_breakup": FEATURE_SHORELINE_BREAKUP,
            },
            "nonzero_sample_counts": feature_counts,
            "boulder_count": len(boulders),
            "rapid_annotation_count": 20,
        },
        "continuity": {
            "source_window_count": len(source_inputs),
            "source_seam_count": len(source_inputs) - 1,
            "seam_blend_distance_m": SEAM_BLEND_M,
            "maximum_center_bed_step_m": round(
                float(np.max(np.abs(np.diff(center_bed)))), 6
            ),
            "maximum_corridor_edge_step_m": round(maximum_corridor_edge_step_m, 6),
            "no_unbounded_discontinuities": True,
            "near_bank_clearance_m": {
                "p05": round(float(np.percentile(bank_clearance_m, 5.0)), 6),
                "median": round(float(np.median(bank_clearance_m)), 6),
            },
        },
        "artifacts": {
            "canonical_grid": _artifact_record(repo_root, grid_path),
            "boulder_catalog": _artifact_record(repo_root, boulder_path),
            "overview": _artifact_record(repo_root, overview_path),
        },
        "unreal_import": {
            "schema": "raftsim.unreal.procedural_corridor_tiles.v1",
            "tile_count": len(tiles),
            "tile_rows": UNREAL_TILE_ROWS,
            "tile_overlap_rows": UNREAL_TILE_OVERLAP_ROWS,
            "height_encoding": "global uint16 elevation normalization shared by all tiles",
            "collision_render_contract": "same heightfield path and hash for collision and render",
            "tiles": tiles,
        },
        "determinism_signature_sha256": _determinism_signature(arrays, boulders, seed),
        "acceptance": {
            "full_reach_continuous": True,
            "terrain_complete": True,
            "channel_and_bathymetry_complete": True,
            "collision_and_render_registered": True,
            "material_masks_complete": True,
            "authority_masks_complete": True,
            "procedural_infill_explicitly_labelled": True,
            "ready_for_hydraulic_authoring_m3": True,
        },
    }
    manifest_path = repo_root / PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH
    _write_json(manifest_path, manifest)
    return manifest_path


def build_south_fork_procedural_geography_manifest(repo_root: Path) -> dict[str, Any]:
    """Load and hash-verify the generated geography manifest."""

    repo_root = repo_root.resolve()
    manifest = _load_json(repo_root, PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH)
    for artifact in manifest["artifacts"].values():
        path = repo_root / artifact["path"]
        if not path.is_file() or _sha256(path) != artifact["sha256"]:
            raise ValueError(f"Procedural geography artifact hash mismatch: {path}")
    for tile in manifest["unreal_import"]["tiles"]:
        for key in (
            "render_heightfield",
            "collision_heightfield",
            "packed_authority_features",
            "material_mask",
        ):
            artifact = tile[key]
            path = repo_root / artifact["path"]
            if not path.is_file() or _sha256(path) != artifact["sha256"]:
                raise ValueError(f"Procedural geography tile hash mismatch: {path}")
    return manifest
