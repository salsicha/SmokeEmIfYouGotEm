"""Build full-reach South Fork presentation products for Unreal Milestone 4.

The generator preserves the M2 collision/terrain grid and M3 water stationing.
USDA NAIP imagery conditions macro colour and vegetation placement.  Where the
source products do not describe bathymetry, small-scale surface response,
species distribution, access furniture, or water presentation, deterministic
procedural infill is emitted with explicit provenance.  These products are game
content and are never suitable for navigation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .south_fork_procedural_geography import (
    FEATURE_EDDY,
    FEATURE_HOLE_CONTROL,
    FEATURE_LEDGE,
    FEATURE_WAVE_TRAIN,
    MATERIAL_CHANNEL_BED,
    MATERIAL_SOIL,
    MATERIAL_VEGETATION,
    MATERIAL_WET_BANK,
    PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
    _bilinear_sample,
    _effective_raster_bounds,
    _load_dem,
)

PHOTOREAL_ENVIRONMENT_DIRECTORY_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "photoreal_environment"
)
PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH = (
    f"{PHOTOREAL_ENVIRONMENT_DIRECTORY_RELATIVE_PATH}/manifest.json"
)
RIVER_COORDINATE_MAP_RELATIVE_PATH = (
    f"{PHOTOREAL_ENVIRONMENT_DIRECTORY_RELATIVE_PATH}/river_coordinate_map.json"
)
INFRASTRUCTURE_CATALOG_RELATIVE_PATH = (
    f"{PHOTOREAL_ENVIRONMENT_DIRECTORY_RELATIVE_PATH}/infrastructure_catalog.json"
)
FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/"
    "full_reach_transit_seed/manifest.json"
)

SCHEMA = "raftsim.south_fork.photoreal_environment.v1"
ALGORITHM_VERSION = "south_fork_photoreal_environment_v12_fold_safe_registered_corridor"
DEFAULT_SEED = 0x5FA4E004
FLOW_BANDS = ("low_runnable", "median_runnable", "high_runnable")
FAR_FIELD_GRID_SIZE = 257
FAR_FIELD_CORRIDOR_EXCLUSION_M = 52.0
FAR_FIELD_UNDERLAY_FALLOFF_M = 80.0
FAR_FIELD_UNDERLAY_MAX_DEPTH_M = 6.4


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _artifact(repo_root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(repo_root)),
        "sha256": _sha256(path),
        "byte_count": path.stat().st_size,
    }


def _bilinear_rgb(
    raster: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
    bounds: list[float],
) -> np.ndarray:
    height, width = raster.shape[:2]
    min_x, min_y, max_x, max_y = map(float, bounds)
    center_x = 0.5 * (min_x + max_x)
    center_y = 0.5 * (min_y + max_y)
    world_units_per_pixel = max(
        (max_x - min_x) / max(width, 1),
        (max_y - min_y) / max(height, 1),
    )
    half_width = 0.5 * world_units_per_pixel * width
    half_height = 0.5 * world_units_per_pixel * height
    min_x, max_x = center_x - half_width, center_x + half_width
    min_y, max_y = center_y - half_height, center_y + half_height
    px = np.clip((world_x - min_x) / (max_x - min_x) * (width - 1), 0.0, width - 1)
    py = np.clip((max_y - world_y) / (max_y - min_y) * (height - 1), 0.0, height - 1)
    x0 = np.floor(px).astype(np.int32)
    y0 = np.floor(py).astype(np.int32)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    tx = (px - x0)[..., None]
    ty = (py - y0)[..., None]
    return (
        raster[y0, x0, :3] * (1.0 - tx) * (1.0 - ty)
        + raster[y0, x1, :3] * tx * (1.0 - ty)
        + raster[y1, x0, :3] * (1.0 - tx) * ty
        + raster[y1, x1, :3] * tx * ty
    ).astype(np.float32)


def _sample_naip_rgb(
    repo_root: Path,
    geography_manifest: dict[str, Any],
    stations_m: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
) -> tuple[np.ndarray, int]:
    output = np.empty((*world_x.shape, 3), dtype=np.float32)
    source_manifests = [
        _load_json(repo_root / entry["manifest_path"])
        for entry in geography_manifest["inputs"]["source_windows"]
    ]
    source_manifests.sort(key=lambda item: float(item["station_range_m"]["start"]))

    def sample(manifest: dict[str, Any], selected: np.ndarray) -> np.ndarray:
        aerial = manifest["source_artifacts"]["aerial"]
        with Image.open(repo_root / aerial["path"]) as source_image:
            rgb = np.asarray(source_image.convert("RGB"), dtype=np.float32)
        return _bilinear_rgb(
            rgb,
            world_x[selected],
            world_y[selected],
            aerial["source_bounds_epsg3857"],
        )

    for index, manifest in enumerate(source_manifests):
        start = float(manifest["station_range_m"]["start"])
        end = float(manifest["station_range_m"]["end"])
        selected = (stations_m >= start) & (
            stations_m <= end
            if index == len(source_manifests) - 1
            else stations_m < end
        )
        output[selected] = sample(manifest, selected)

    seam_blend_m = float(geography_manifest["continuity"]["seam_blend_distance_m"])
    for upstream, downstream in zip(
        source_manifests, source_manifests[1:], strict=False
    ):
        seam = float(upstream["station_range_m"]["end"])
        selected = np.abs(stations_m - seam) <= seam_blend_m
        if not selected.any():
            continue
        alpha = np.clip(
            (stations_m[selected] - seam + seam_blend_m) / (2.0 * seam_blend_m),
            0.0,
            1.0,
        )[:, None, None]
        output[selected] = (
            sample(upstream, selected) * (1.0 - alpha)
            + sample(downstream, selected) * alpha
        )
    return np.clip(output, 0.0, 255.0), len(source_manifests) - 1


def _condition_macro_albedo(
    aerial_rgb: np.ndarray,
    material: np.ndarray,
    bed: np.ndarray,
    stations_m: np.ndarray,
    lateral_m: np.ndarray,
    seed: int,
) -> np.ndarray:
    palettes = np.asarray(
        [
            [82.0, 73.0, 58.0],
            [68.0, 66.0, 55.0],
            [135.0, 130.0, 119.0],
            [132.0, 119.0, 96.0],
            [125.0, 103.0, 72.0],
            [67.0, 96.0, 49.0],
        ],
        dtype=np.float32,
    )
    source_weight = np.asarray([0.12, 0.30, 0.34, 0.38, 0.45, 0.68], dtype=np.float32)
    palette = palettes[material]
    weight = source_weight[material][..., None]
    macro = palette * (1.0 - weight) + aerial_rgb * weight

    dz_ds = np.gradient(bed, stations_m, axis=0)
    dz_dl = np.gradient(bed, lateral_m, axis=1)
    slope = np.clip(np.hypot(dz_ds, dz_dl), 0.0, 2.0)
    macro *= (1.0 - 0.09 * np.clip(slope, 0.0, 1.0))[..., None]

    # Deterministic sub-DEM colour breakup.  It is deliberately bounded: the
    # macro product conditions material response without inventing land cover.
    phase = float(seed & 0xFFFF) / 65535.0 * np.pi * 2.0
    detail = np.sin(stations_m[:, None] * 0.071 + phase) * np.cos(
        lateral_m[None, :] * 0.119 - phase * 0.7
    ) + 0.45 * np.sin(stations_m[:, None] * 0.191 + lateral_m[None, :] * 0.163)
    macro *= (1.0 + 0.045 * detail)[..., None]
    # Match the narrow source-conditioned corridor exposure to the larger NAIP
    # far-field windows.  This is a uniform radiometric correction; it retains
    # measured hue/variation and does not synthesize land-cover classes.
    macro *= 0.78
    return np.clip(np.rint(macro), 0.0, 255.0).astype(np.uint8)


def _surface_products(
    bed: np.ndarray,
    material: np.ndarray,
    vegetation_score: np.ndarray,
    features: np.ndarray,
    stations_m: np.ndarray,
    lateral_m: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dz_ds = np.gradient(bed, stations_m, axis=0)
    dz_dl = np.gradient(bed, lateral_m, axis=1)
    normal = np.stack((-dz_ds, -dz_dl, np.ones_like(bed)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
    normal_rgb = np.clip(np.rint((normal * 0.5 + 0.5) * 255.0), 0, 255).astype(np.uint8)

    d2s = np.gradient(dz_ds, stations_m, axis=0)
    d2l = np.gradient(dz_dl, lateral_m, axis=1)
    concavity = np.clip(-(d2s + d2l) * 2.0, -1.0, 1.0)
    ao = np.clip(np.rint((0.88 - 0.16 * np.maximum(concavity, 0.0)) * 255.0), 0, 255)
    material_roughness = np.asarray([0.83, 0.72, 0.68, 0.81, 0.86, 0.90])
    phase = float((seed >> 8) & 0xFFFF) / 65535.0 * np.pi * 2.0
    noise = np.sin(stations_m[:, None] * 0.137 + phase) * np.cos(
        lateral_m[None, :] * 0.173 - phase
    )
    roughness = np.clip(
        np.rint((material_roughness[material] + 0.045 * noise) * 255.0), 0, 255
    )
    relief = np.clip(np.hypot(dz_ds, dz_dl) / 1.5, 0.0, 1.0)
    packed = np.stack((ao, roughness, np.rint(relief * 255.0)), axis=-1).astype(
        np.uint8
    )

    vegetation = np.clip(vegetation_score.astype(np.float32) / 255.0, 0.0, 1.0)
    vegetated_material = (material == MATERIAL_VEGETATION) | (material == MATERIAL_SOIL)
    slope = np.hypot(dz_ds, dz_dl)
    vegetation *= vegetated_material
    vegetation *= np.clip(1.25 - slope * 0.55, 0.0, 1.0)
    riparian = np.exp(-(((np.abs(lateral_m)[None, :] - 45.0) / 34.0) ** 2))
    elevation_t = np.clip((bed - np.min(bed)) / max(float(np.ptp(bed)), 1.0), 0.0, 1.0)
    conifer = vegetation * np.clip(0.36 + elevation_t * 0.72, 0.0, 1.0)
    broadleaf = vegetation * np.clip(
        0.84 - elevation_t * 0.48 + riparian * 0.35, 0.0, 1.0
    )
    riparian_species = vegetation * riparian * 1.15
    groundcover = vegetation * np.clip(1.15 - slope * 0.5, 0.0, 1.0)
    vegetation_rgba = np.clip(
        np.rint(
            np.stack((conifer, broadleaf, riparian_species, groundcover), axis=-1)
            * 255.0
        ),
        0,
        255,
    ).astype(np.uint8)

    wet_bank = (material == MATERIAL_WET_BANK).astype(np.float32)
    spray_feature = (
        ((features & FEATURE_HOLE_CONTROL) != 0)
        | ((features & FEATURE_WAVE_TRAIN) != 0)
        | ((features & FEATURE_LEDGE) != 0)
    ).astype(np.float32)
    mist = np.clip(
        spray_feature * 0.75 + ((features & FEATURE_EDDY) != 0) * 0.3, 0.0, 1.0
    )
    contact = (
        (material == MATERIAL_CHANNEL_BED) | (material == MATERIAL_WET_BANK)
    ).astype(np.float32)
    vfx_rgba = np.rint(
        np.stack((wet_bank, spray_feature, mist, contact), axis=-1) * 255.0
    ).astype(np.uint8)
    return normal_rgb, packed, vegetation_rgba, vfx_rgba


def _water_products(
    repo_root: Path,
    transit_manifest: dict[str, Any],
) -> dict[str, dict[str, np.ndarray]]:
    transit_dir = repo_root / FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH
    transit_dir = transit_dir.parent
    result: dict[str, dict[str, np.ndarray]] = {}
    for band_id in FLOW_BANDS:
        bed = np.load(transit_dir / band_id / "bed.npy").T.astype(np.float32)
        depth = np.load(transit_dir / band_id / "h.npy").T.astype(np.float32)
        u = np.load(transit_dir / band_id / "u.npy").T.astype(np.float32)
        v = np.load(transit_dir / band_id / "v.npy").T.astype(np.float32)
        wet = np.load(transit_dir / band_id / "wet_mask.npy").T.astype(bool)
        speed = np.hypot(u, v)
        froude = speed / np.sqrt(9.80665 * np.maximum(depth, 0.05))
        foam = np.clip((froude - 0.72) / 1.18, 0.0, 1.0) * wet
        presentation = np.stack(
            (
                np.rint(foam * 255.0),
                np.rint(np.clip(depth / 4.0, 0.0, 1.0) * 255.0),
                np.rint(np.clip(speed / 8.0, 0.0, 1.0) * 255.0),
                wet.astype(np.uint8) * 255,
            ),
            axis=-1,
        ).astype(np.uint8)
        result[band_id] = {
            "surface_m": bed + depth,
            "presentation": presentation,
        }
    if not transit_manifest["all_bands_passed"]:
        raise ValueError("Full-reach transit source has not passed all flow bands")
    return result


def _write_coordinate_map(
    repo_root: Path,
    arrays: dict[str, np.ndarray],
    vertical_datum_m: float,
) -> Path:
    x = arrays["centerline_epsg3857_x_m"].astype(np.float64)
    y = arrays["centerline_epsg3857_y_m"].astype(np.float64)
    ground_scale = float(arrays["epsg3857_to_ground_scale"])
    origin = np.asarray([x[0], y[0]], dtype=np.float64)
    points = [
        [
            round(float(station), 3),
            round(float((px - origin[0]) * ground_scale), 3),
            round(float((py - origin[1]) * ground_scale), 3),
            round(float(nx), 7),
            round(float(ny), 7),
        ]
        for station, px, py, nx, ny in zip(
            arrays["stations_m"],
            x,
            y,
            arrays["centerline_normal_x"],
            arrays["centerline_normal_y"],
            strict=True,
        )
    ]
    path = repo_root / RIVER_COORDINATE_MAP_RELATIVE_PATH
    _write_json(
        path,
        {
            "schema": "raftsim.curved_river_coordinate_map.v1",
            "river_id": "south_fork_american_chili_bar",
            "coordinate_system": "ground-scaled Unreal local meters relative to first EPSG:3857 route point",
            "station_lateral_system": "station meters; lateral positive river-left",
            "epsg3857_origin_m": [
                round(float(origin[0]), 3),
                round(float(origin[1]), 3),
            ],
            "vertical_datum_m": round(vertical_datum_m, 6),
            "epsg3857_to_ground_scale": round(ground_scale, 9),
            "point_encoding": [
                "station_m",
                "local_x_m",
                "local_y_m",
                "normal_x",
                "normal_y",
            ],
            "point_count": len(points),
            "points": points,
            "not_for_navigation": True,
        },
    )
    return path


def _write_infrastructure_catalog(repo_root: Path, seed: int) -> Path:
    path = repo_root / INFRASTRUCTURE_CATALOG_RELATIVE_PATH
    _write_json(
        path,
        {
            "schema": "raftsim.south_fork.infrastructure_catalog.v1",
            "river_id": "south_fork_american_chili_bar",
            "seed": seed,
            "not_for_navigation": True,
            "policy": {
                "official_access_geometry_is_authoritative_where_available": True,
                "unconfirmed_roads_bridges_and_bank_landings_are_procedural_game_infill": True,
                "procedural_infill_must_not_be_presented_as_real_access_advice": True,
            },
            "sites": [
                {
                    "site_id": "chili_bar_put_in",
                    "name": "Chili Bar Put-in",
                    "kind": "put_in",
                    "station_m": 0.0,
                    "lateral_m": 58.0,
                    "authority": "review_seed_conditioned_procedural_bank_furniture",
                },
                {
                    "site_id": "coloma_access",
                    "name": "Coloma Access",
                    "kind": "takeout_and_bridge_context",
                    "station_m": 5200.0,
                    "lateral_m": -62.0,
                    "authority": "review_seed_conditioned_procedural_bank_furniture",
                },
                {
                    "site_id": "salmon_falls_lower_water_takeout",
                    "name": "Salmon Falls Lower Water Raft Take-out",
                    "kind": "takeout",
                    "station_m": 49077.732,
                    "lateral_m": 54.0,
                    "authority": "california_state_parks_anchor_with_procedural_bank_landing",
                },
            ],
            "procedural_structures": [
                {
                    "structure_id": "coloma_context_bridge",
                    "kind": "bridge",
                    "station_m": 5200.0,
                    "span_m": 74.0,
                    "authority": "procedural_context_not_surveyed",
                }
            ],
        },
    )
    return path


def _nearest_route_distance_m(
    world_xy_m: np.ndarray,
    route_xy_m: np.ndarray,
) -> np.ndarray:
    """Return deterministic point-to-sampled-route distance without SciPy."""

    flat = world_xy_m.reshape(-1, 2)
    result = np.empty(flat.shape[0], dtype=np.float64)
    for start in range(0, flat.shape[0], 512):
        stop = min(start + 512, flat.shape[0])
        delta = flat[start:stop, None, :] - route_xy_m[None, :, :]
        result[start:stop] = np.sqrt(np.min(np.sum(delta * delta, axis=2), axis=1))
    return result.reshape(world_xy_m.shape[:-1])


def _nearest_route_station_m(
    world_xy_m: np.ndarray,
    route_xy_m: np.ndarray,
    route_station_m: np.ndarray,
) -> np.ndarray:
    """Return the station of the nearest sampled route point deterministically."""

    flat = world_xy_m.reshape(-1, 2)
    result = np.empty(flat.shape[0], dtype=np.float64)
    for start in range(0, flat.shape[0], 256):
        stop = min(start + 256, flat.shape[0])
        delta = flat[start:stop, None, :] - route_xy_m[None, :, :]
        nearest = np.argmin(np.sum(delta * delta, axis=2), axis=1)
        result[start:stop] = route_station_m[nearest]
    return result.reshape(world_xy_m.shape[:-1])


def _write_far_field_patches(
    repo_root: Path,
    output_dir: Path,
    geography_manifest: dict[str, Any],
    arrays: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    """Build source-backed coarse valley terrain outside the play corridor."""

    patch_dir = output_dir / "far_field"
    patch_dir.mkdir(parents=True, exist_ok=True)
    ground_scale = float(arrays["epsg3857_to_ground_scale"])
    origin_epsg = np.asarray(
        [
            arrays["centerline_epsg3857_x_m"][0],
            arrays["centerline_epsg3857_y_m"][0],
        ],
        dtype=np.float64,
    )
    stations_m = arrays["stations_m"].astype(np.float64)
    route_local_m = np.column_stack(
        (
            arrays["centerline_epsg3857_x_m"],
            arrays["centerline_epsg3857_y_m"],
        )
    )
    route_local_m = (route_local_m - origin_epsg) * ground_scale
    records: list[dict[str, Any]] = []
    source_windows = geography_manifest["inputs"]["source_windows"]
    global_route_xy_m = route_local_m[::4]
    global_route_station_m = stations_m[::4]
    for ordinal, source_entry in enumerate(source_windows):
        source_manifest = _load_json(repo_root / source_entry["manifest_path"])
        source_artifacts = source_manifest["source_artifacts"]
        dem_record = source_artifacts["dem"]
        dem, dem_bounds = _load_dem(
            repo_root / dem_record["path"], dem_record["source_bounds_epsg3857"]
        )
        x_epsg = np.linspace(dem_bounds[0], dem_bounds[2], FAR_FIELD_GRID_SIZE)
        y_epsg = np.linspace(dem_bounds[3], dem_bounds[1], FAR_FIELD_GRID_SIZE)
        world_x_epsg, world_y_epsg = np.meshgrid(x_epsg, y_epsg)
        height_m = _bilinear_sample(dem, world_x_epsg, world_y_epsg, dem_bounds).astype(
            np.float32
        )

        aerial_record = source_artifacts["aerial"]
        with Image.open(repo_root / aerial_record["path"]) as aerial_image:
            aerial_bounds = _effective_raster_bounds(
                aerial_image, aerial_record["source_bounds_epsg3857"]
            )
            aerial_rgb = np.asarray(aerial_image.convert("RGB"), dtype=np.float32)
        macro = _bilinear_rgb(aerial_rgb, world_x_epsg, world_y_epsg, aerial_bounds)
        green = np.clip(
            macro[..., 1] - 0.5 * (macro[..., 0] + macro[..., 2]) + 128.0,
            0.0,
            255.0,
        )
        terrain_palette = np.stack(
            (
                88.0 - green * 0.08,
                72.0 + green * 0.10,
                52.0 + green * 0.035,
            ),
            axis=-1,
        )
        macro = np.clip(macro * 0.62 + terrain_palette * 0.38, 0.0, 255.0).astype(
            np.uint8
        )

        local_x_m = (world_x_epsg - origin_epsg[0]) * ground_scale
        local_y_m = (world_y_epsg - origin_epsg[1]) * ground_scale
        station_start = float(source_manifest["station_range_m"]["start"])
        station_end = float(source_manifest["station_range_m"]["end"])
        route_selection = (stations_m >= station_start - 1400.0) & (
            stations_m <= station_end + 1400.0
        )
        sampled_route = route_local_m[route_selection][::4]
        distance_m = _nearest_route_distance_m(
            np.stack((local_x_m, local_y_m), axis=-1), sampled_route
        )
        nearest_global_station_m = _nearest_route_station_m(
            np.stack((local_x_m, local_y_m), axis=-1),
            global_route_xy_m,
            global_route_station_m,
        )
        # Keep the source-backed valley mesh continuous beneath the detailed
        # curvilinear channel.  A small deterministic depression prevents the
        # coarse DEM surface from covering live water or z-fighting the
        # detailed bank mesh, then fades to the unmodified 3DEP surface beyond
        # the overlap.  This is explicitly game-only procedural infill.
        underlay_weight = np.clip(
            1.0 - distance_m / FAR_FIELD_UNDERLAY_FALLOFF_M, 0.0, 1.0
        )
        height_m = (
            height_m - FAR_FIELD_UNDERLAY_MAX_DEPTH_M * underlay_weight**2
        ).astype(np.float32)
        # The fold-safe Unreal detailed ribbon covers +/-64 m. Remove the
        # coarse far-field render surface inside 52 m, preserving a 12 m
        # registered overlap without offsetting the curvilinear grid far enough
        # to self-intersect in tight bends. The source-backed height remains a
        # lowered underlay product for provenance and non-render consumers.
        terrain_mask = np.where(
            distance_m >= FAR_FIELD_CORRIDOR_EXCLUSION_M, 255, 0
        ).astype(np.uint8)
        owns_station = (nearest_global_station_m >= station_start) & (
            nearest_global_station_m
            < (station_end if ordinal < len(source_windows) - 1 else station_end + 1.0)
        )
        ownership_mask = np.where(owns_station, 255, 0).astype(np.uint8)

        height_min = float(np.min(height_m))
        height_max = float(np.max(height_m))
        height_span = max(height_max - height_min, 1.0)
        encoded_height = np.rint(
            np.clip((height_m - height_min) / height_span, 0.0, 1.0) * 65535.0
        ).astype(np.uint16)
        patch_id = f"far_field_{ordinal:02d}"
        height_path = patch_dir / f"{patch_id}_height.png"
        macro_path = patch_dir / f"{patch_id}_macro_albedo.png"
        mask_path = patch_dir / f"{patch_id}_corridor_exclusion.png"
        ownership_path = patch_dir / f"{patch_id}_source_window_ownership.png"
        Image.fromarray(encoded_height, mode="I;16").save(height_path)
        Image.fromarray(macro, mode="RGB").save(macro_path)
        Image.fromarray(terrain_mask, mode="L").save(mask_path)
        Image.fromarray(ownership_mask, mode="L").save(ownership_path)
        records.append(
            {
                "patch_id": patch_id,
                "source_window_id": source_entry["window_id"],
                "authority": "USGS_3DEP_and_USDA_NAIP_with_procedural_continuous_channel_underlay",
                "dimensions": [FAR_FIELD_GRID_SIZE, FAR_FIELD_GRID_SIZE],
                "bounds_local_m": [
                    round(float(local_x_m[0, 0]), 3),
                    round(float(local_y_m[-1, 0]), 3),
                    round(float(local_x_m[0, -1]), 3),
                    round(float(local_y_m[0, 0]), 3),
                ],
                "height": _artifact(repo_root, height_path),
                "height_encoding": {
                    "minimum_elevation_m": round(height_min, 6),
                    "maximum_elevation_m": round(height_max, 6),
                    "uint16_min": 0,
                    "uint16_max": 65535,
                },
                "macro_albedo": _artifact(repo_root, macro_path),
                "corridor_exclusion_mask": _artifact(repo_root, mask_path),
                "source_window_ownership_mask": _artifact(repo_root, ownership_path),
                "visible_vertex_fraction": round(
                    float(np.count_nonzero(terrain_mask)) / terrain_mask.size, 6
                ),
                "owned_vertex_fraction": round(
                    float(np.count_nonzero(ownership_mask)) / ownership_mask.size, 6
                ),
            }
        )
    return records


def _write_tiles(
    repo_root: Path,
    output_dir: Path,
    geography_manifest: dict[str, Any],
    macro_albedo: np.ndarray,
    normal_rgb: np.ndarray,
    packed: np.ndarray,
    vegetation: np.ndarray,
    vfx: np.ndarray,
    water: dict[str, dict[str, np.ndarray]],
) -> list[dict[str, Any]]:
    tile_dir = output_dir / "unreal_tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    water_min = min(float(np.min(item["surface_m"])) for item in water.values())
    water_max = max(float(np.max(item["surface_m"])) for item in water.values())
    water_span = max(water_max - water_min, 1.0)
    records: list[dict[str, Any]] = []
    for source_tile in geography_manifest["unreal_import"]["tiles"]:
        tile_id = str(source_tile["tile_id"])
        start, inclusive_stop = map(int, source_tile["row_range"])
        stop = inclusive_stop + 1

        products: dict[str, Path] = {}
        arrays = {
            "macro_albedo": macro_albedo[start:stop],
            "normal": normal_rgb[start:stop],
            "ao_roughness_height": packed[start:stop],
            "vegetation_species_density": vegetation[start:stop],
            "water_vfx_zones": vfx[start:stop],
        }
        for label, values in arrays.items():
            product_path = tile_dir / f"{tile_id}_{label}.png"
            Image.fromarray(values).save(product_path)
            products[label] = product_path

        water_records: dict[str, Any] = {}
        for band_id in FLOW_BANDS:
            surface = water[band_id]["surface_m"][start:stop]
            encoded = np.rint(
                np.clip((surface - water_min) / water_span, 0.0, 1.0) * 65535.0
            ).astype(np.uint16)
            height_path = tile_dir / f"{tile_id}_water_{band_id}_height.png"
            presentation_path = tile_dir / f"{tile_id}_water_{band_id}_presentation.png"
            Image.fromarray(encoded, mode="I;16").save(height_path)
            Image.fromarray(
                water[band_id]["presentation"][start:stop], mode="RGBA"
            ).save(presentation_path)
            water_records[band_id] = {
                "surface_height": _artifact(repo_root, height_path),
                "presentation": _artifact(repo_root, presentation_path),
            }

        records.append(
            {
                "tile_id": tile_id,
                "row_range": [start, inclusive_stop],
                "dimensions": source_tile["dimensions"],
                "station_range_m": source_tile["station_range_m"],
                "terrain_height": source_tile["render_heightfield"],
                "terrain_height_encoding": source_tile["height_encoding"],
                "source_authority_features": source_tile["packed_authority_features"],
                "material_mask": source_tile["material_mask"],
                "macro_albedo": _artifact(repo_root, products["macro_albedo"]),
                "normal": _artifact(repo_root, products["normal"]),
                "ao_roughness_height": _artifact(
                    repo_root, products["ao_roughness_height"]
                ),
                "vegetation_species_density": _artifact(
                    repo_root, products["vegetation_species_density"]
                ),
                "water_vfx_zones": _artifact(repo_root, products["water_vfx_zones"]),
                "water_bands": water_records,
            }
        )
    for record in records:
        record["water_height_encoding"] = {
            "minimum_elevation_m": round(water_min, 6),
            "maximum_elevation_m": round(water_max, 6),
            "uint16_min": 0,
            "uint16_max": 65535,
        }
    return records


def write_south_fork_photoreal_environment(
    repo_root: Path, seed: int = DEFAULT_SEED
) -> Path:
    """Generate deterministic full-reach environment and Unreal import products."""

    repo_root = repo_root.resolve()
    output_dir = repo_root / PHOTOREAL_ENVIRONMENT_DIRECTORY_RELATIVE_PATH
    output_dir.mkdir(parents=True, exist_ok=True)
    geography_manifest = _load_json(
        repo_root / PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH
    )
    transit_manifest = _load_json(repo_root / FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH)
    with np.load(repo_root / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH) as source:
        arrays = {key: source[key] for key in source.files}

    stations_m = arrays["stations_m"].astype(np.float64)
    lateral_m = arrays["lateral_offsets_m"].astype(np.float64)
    center_x = arrays["centerline_epsg3857_x_m"].astype(np.float64)
    center_y = arrays["centerline_epsg3857_y_m"].astype(np.float64)
    ground_scale = float(arrays["epsg3857_to_ground_scale"])
    epsg_lateral_m = lateral_m / ground_scale
    world_x = (
        center_x[:, None]
        + arrays["centerline_normal_x"][:, None] * epsg_lateral_m[None, :]
    )
    world_y = (
        center_y[:, None]
        + arrays["centerline_normal_y"][:, None] * epsg_lateral_m[None, :]
    )
    aerial_rgb, seam_count = _sample_naip_rgb(
        repo_root, geography_manifest, stations_m, world_x, world_y
    )
    vegetation_score = np.clip(
        np.rint(
            aerial_rgb[..., 1] - 0.5 * (aerial_rgb[..., 0] + aerial_rgb[..., 2]) + 128.0
        ),
        0.0,
        255.0,
    ).astype(np.uint8)
    bed = arrays["bed_elevation_m"].astype(np.float32)
    material = arrays["material"].astype(np.uint8)
    macro_albedo = _condition_macro_albedo(
        aerial_rgb, material, bed, stations_m, lateral_m, seed
    )
    normal_rgb, packed, vegetation, vfx = _surface_products(
        bed,
        material,
        vegetation_score,
        arrays["features"],
        stations_m,
        lateral_m,
        seed,
    )
    water = _water_products(repo_root, transit_manifest)
    vertical_datum_m = float(np.floor(np.min(bed) / 10.0) * 10.0)
    coordinate_path = _write_coordinate_map(repo_root, arrays, vertical_datum_m)
    infrastructure_path = _write_infrastructure_catalog(repo_root, seed)
    tiles = _write_tiles(
        repo_root,
        output_dir,
        geography_manifest,
        macro_albedo,
        normal_rgb,
        packed,
        vegetation,
        vfx,
        water,
    )
    far_field_patches = _write_far_field_patches(
        repo_root, output_dir, geography_manifest, arrays
    )

    boulder_path = repo_root / PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH
    digest = hashlib.sha256()
    digest.update(ALGORITHM_VERSION.encode())
    digest.update(str(seed).encode())
    for tile in tiles:
        for key in (
            "macro_albedo",
            "normal",
            "ao_roughness_height",
            "vegetation_species_density",
            "water_vfx_zones",
        ):
            digest.update(tile[key]["sha256"].encode())
        for band_id in FLOW_BANDS:
            digest.update(
                tile["water_bands"][band_id]["surface_height"]["sha256"].encode()
            )
            digest.update(
                tile["water_bands"][band_id]["presentation"]["sha256"].encode()
            )
    for patch in far_field_patches:
        digest.update(patch["height"]["sha256"].encode())
        digest.update(patch["macro_albedo"]["sha256"].encode())
        digest.update(patch["corridor_exclusion_mask"]["sha256"].encode())
        digest.update(patch["source_window_ownership_mask"]["sha256"].encode())

    manifest = {
        "schema": SCHEMA,
        "generated_on": "2026-07-19",
        "river_id": "south_fork_american_chili_bar",
        "status": "full_reach_environment_products_ready_for_unreal_build",
        "algorithm": ALGORITHM_VERSION,
        "seed": seed,
        "not_for_navigation": True,
        "inputs": {
            "procedural_geography": PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
            "full_reach_transit_water": FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH,
            "boulder_catalog": PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH,
            "naip_source_window_count": len(
                geography_manifest["inputs"]["source_windows"]
            ),
        },
        "coordinate_map": _artifact(repo_root, coordinate_path),
        "infrastructure_catalog": _artifact(repo_root, infrastructure_path),
        "boulder_catalog": _artifact(repo_root, boulder_path),
        "far_field": {
            "authority": (
                "USGS 3DEP and USDA NAIP where available; deterministic corridor "
                "underlay conditioning and uncovered geography are procedural game infill"
            ),
            "procedural_infill_explicit": True,
            "not_for_navigation": True,
            "grid_size": FAR_FIELD_GRID_SIZE,
            "corridor_exclusion_radius_m": FAR_FIELD_CORRIDOR_EXCLUSION_M,
            "corridor_underlay_falloff_m": FAR_FIELD_UNDERLAY_FALLOFF_M,
            "corridor_underlay_max_depth_m": FAR_FIELD_UNDERLAY_MAX_DEPTH_M,
            "continuous_underlay": True,
            "patch_count": len(far_field_patches),
            "patches": far_field_patches,
        },
        "grid": {
            "station_count": int(stations_m.size),
            "lateral_count": int(lateral_m.size),
            "station_range_m": [float(stations_m[0]), float(stations_m[-1])],
            "lateral_range_m": [float(lateral_m[0]), float(lateral_m[-1])],
            "vertical_datum_m": vertical_datum_m,
            "tile_count": len(tiles),
            "tile_overlap_rows": int(
                geography_manifest["unreal_import"]["tile_overlap_rows"]
            ),
        },
        "presentation": {
            "flow_bands": list(FLOW_BANDS),
            "terrain": "NAIP-conditioned macro colour plus deterministic PBR surface response",
            "vegetation_channels": [
                "conifer",
                "broadleaf_oak_proxy",
                "riparian_willow_alder_proxy",
                "understory_groundcover",
            ],
            "water_channels": ["foam", "depth", "speed", "wet_mask"],
            "vfx_channels": ["wet_bank", "spray", "mist", "water_contact"],
            "naip_seam_count": seam_count,
        },
        "asset_policy": {
            "near_field_species": "South-Fork-curated project-owned or CC0 meshes only",
            "terrain_detail": "project-owned procedural textures and CC0 physical materials",
            "procedural_infill_explicit": True,
            "unconfirmed_infrastructure_is_game_context_not_real_access_guidance": True,
        },
        "unreal_import": {
            "schema": "raftsim.unreal.south_fork_full_reach_environment.v1",
            "world_partition_map": "/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach",
            "terrain_representation": "curved Nanite static-mesh tiles sharing M2 collision height",
            "far_field_representation": (
                "source-backed regular-grid static-mesh patches forming a deterministic lowered underlay beneath the detailed channel"
            ),
            "hlod_and_streaming_required": True,
            "tiles": tiles,
        },
        "determinism_signature_sha256": digest.hexdigest(),
        "acceptance": {
            "full_reach_visual_products_continuous": True,
            "all_flow_bands_present": True,
            "source_conditioned_materials_present": True,
            "vegetation_and_vfx_masks_present": True,
            "coordinate_map_complete": True,
            "procedural_infill_labelled": True,
            "far_field_geography_complete": len(far_field_patches) == 8,
            "unreal_world_partition_build_complete": False,
            "representative_captures_complete": False,
            "owner_art_and_readability_review_passed": False,
        },
    }
    manifest_path = repo_root / PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH
    _write_json(manifest_path, manifest)
    return manifest_path


def build_south_fork_photoreal_environment_manifest(repo_root: Path) -> dict[str, Any]:
    """Load the environment manifest and verify every referenced artifact."""

    repo_root = repo_root.resolve()
    manifest = _load_json(repo_root / PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    artifacts = [
        manifest["coordinate_map"],
        manifest["infrastructure_catalog"],
        manifest["boulder_catalog"],
    ]
    for patch in manifest["far_field"]["patches"]:
        artifacts.extend(
            (
                patch["height"],
                patch["macro_albedo"],
                patch["corridor_exclusion_mask"],
                patch["source_window_ownership_mask"],
            )
        )
    for tile in manifest["unreal_import"]["tiles"]:
        artifacts.extend(
            tile[key]
            for key in (
                "terrain_height",
                "source_authority_features",
                "material_mask",
                "macro_albedo",
                "normal",
                "ao_roughness_height",
                "vegetation_species_density",
                "water_vfx_zones",
            )
        )
        for band_id in FLOW_BANDS:
            artifacts.extend(tile["water_bands"][band_id].values())
    for artifact in artifacts:
        path = repo_root / artifact["path"]
        if not path.is_file() or _sha256(path) != artifact["sha256"]:
            raise ValueError(f"Photoreal environment artifact hash mismatch: {path}")
    return manifest
