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
FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/"
    "streaming_manifest.json"
)

SCHEMA = "raftsim.south_fork.photoreal_environment.v1"
ALGORITHM_VERSION = (
    "south_fork_photoreal_environment_v29_guide_feature_breaking_relief"
)
DEFAULT_SEED = 0x5FA4E004
FLOW_BANDS = ("low_runnable", "median_runnable", "high_runnable")
FAR_FIELD_MACRO_SIZE = 1024
FAR_FIELD_MACRO_TILE_HEIGHT = 1024
FAR_FIELD_TILE_COLUMNS = 4
FAR_FIELD_TILE_ROWS = 2
FAR_FIELD_CELL_SIZE_M = 20.0
FAR_FIELD_SOURCE_EDGE_BLEND_M = 720.0
FAR_FIELD_AERIAL_EXPOSURE_GAIN_MIN = 0.68
FAR_FIELD_AERIAL_EXPOSURE_GAIN_MAX = 1.18
FAR_FIELD_AERIAL_CONTRAST_GAIN_MAX = 1.25
FAR_FIELD_PROCEDURAL_INFILL_MAX_RELIEF_M = 28.0
FAR_FIELD_DOMAIN_PADDING_M = 1600.0
# Retained only by the uncalled v14 rollback generator below. The production
# v17 path derives non-square streaming tiles from one shared global grid.
FAR_FIELD_GRID_SIZE = 513
FAR_FIELD_CORRIDOR_EXCLUSION_M = 100.0
FAR_FIELD_CORRIDOR_ALIGNMENT_FULL_M = 124.0
FAR_FIELD_CORRIDOR_ALIGNMENT_FADE_M = 520.0
FAR_FIELD_CORRIDOR_ALIGNMENT_BELOW_M = 1.5
FAR_FIELD_VALLEY_PROFILE_SCALE = 0.42
FAR_FIELD_VALLEY_PROFILE_EXPONENT = 0.80
FAR_FIELD_VALLEY_GRADE_BASE_M = 1.5
FAR_FIELD_VALLEY_CONDITIONING_START_M = 80.0
FAR_FIELD_VALLEY_CONDITIONING_FULL_M = 180.0
FAR_FIELD_VALLEY_GRADE_CAP_FULL_M = 900.0
FAR_FIELD_VALLEY_GRADE_CAP_FADE_M = 1800.0
FAR_FIELD_VALLEY_CARVE_START_M = 120.0
FAR_FIELD_VALLEY_CARVE_MAX_DEPTH_M = 14.0
FAR_FIELD_UNDERLAY_FALLOFF_M = 136.0
FAR_FIELD_UNDERLAY_MAX_DEPTH_M = 6.4
FAR_FIELD_ROUTE_EXTENSION_M = 1800.0
FAR_FIELD_ROUTE_EXTENSION_STEP_M = 32.0


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


def _load_exposure_normalized_aerial_sources(
    repo_root: Path,
    source_manifests: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loaded_sources: list[dict[str, Any]] = []
    for manifest in source_manifests:
        record = manifest["source_artifacts"]["aerial"]
        with Image.open(repo_root / record["path"]) as source_image:
            effective_bounds = _effective_raster_bounds(
                source_image, record["source_bounds_epsg3857"]
            )
            rgb = np.asarray(source_image.convert("RGB"), dtype=np.float32)
        luminance = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
        valid_luminance = luminance[(luminance >= 5.0) & (luminance <= 250.0)]
        median_luminance = float(
            np.median(valid_luminance) if valid_luminance.size else np.median(luminance)
        )
        loaded_sources.append(
            {
                "manifest": manifest,
                "record": record,
                "effective_bounds": tuple(effective_bounds),
                "rgb": rgb,
                "median_luminance": median_luminance,
            }
        )

    target_median_luminance = float(
        np.median([source["median_luminance"] for source in loaded_sources])
    )
    exposure_records: list[dict[str, Any]] = []
    for source in loaded_sources:
        median_luminance = float(source["median_luminance"])
        exposure_gain = float(
            np.clip(
                target_median_luminance / max(median_luminance, 1e-6),
                FAR_FIELD_AERIAL_EXPOSURE_GAIN_MIN,
                FAR_FIELD_AERIAL_EXPOSURE_GAIN_MAX,
            )
        )
        contrast_gain = float(
            np.clip(1.0 / exposure_gain, 1.0, FAR_FIELD_AERIAL_CONTRAST_GAIN_MAX)
        )
        normalized_center = median_luminance * exposure_gain
        exposure_matched = source["rgb"] * exposure_gain
        source["rgb"] = np.clip(
            normalized_center + (exposure_matched - normalized_center) * contrast_gain,
            0.0,
            255.0,
        )
        source["exposure_gain"] = exposure_gain
        source["contrast_gain"] = contrast_gain
        exposure_records.append(
            {
                "window_id": str(source["manifest"]["window_id"]),
                "source_median_luminance": round(median_luminance, 6),
                "applied_gain": round(exposure_gain, 6),
                "applied_contrast_gain": round(contrast_gain, 6),
            }
        )
    return loaded_sources, {
        "algorithm": "bounded_per_window_robust_median_luminance_v1",
        "target_median_luminance": round(target_median_luminance, 6),
        "gain_bounds": [
            FAR_FIELD_AERIAL_EXPOSURE_GAIN_MIN,
            FAR_FIELD_AERIAL_EXPOSURE_GAIN_MAX,
        ],
        "contrast_gain_bounds": [1.0, FAR_FIELD_AERIAL_CONTRAST_GAIN_MAX],
        "sources": exposure_records,
    }


def _sample_naip_rgb(
    repo_root: Path,
    geography_manifest: dict[str, Any],
    stations_m: np.ndarray,
    world_x: np.ndarray,
    world_y: np.ndarray,
) -> tuple[np.ndarray, int, dict[str, Any]]:
    output = np.empty((*world_x.shape, 3), dtype=np.float32)
    source_manifests = [
        _load_json(repo_root / entry["manifest_path"])
        for entry in geography_manifest["inputs"]["source_windows"]
    ]
    source_manifests.sort(key=lambda item: float(item["station_range_m"]["start"]))
    normalized_sources, exposure_normalization = (
        _load_exposure_normalized_aerial_sources(repo_root, source_manifests)
    )

    def sample(source: dict[str, Any], selected: np.ndarray) -> np.ndarray:
        aerial = source["record"]
        return _bilinear_rgb(
            source["rgb"],
            world_x[selected],
            world_y[selected],
            aerial["source_bounds_epsg3857"],
        )

    for index, source in enumerate(normalized_sources):
        manifest = source["manifest"]
        start = float(manifest["station_range_m"]["start"])
        end = float(manifest["station_range_m"]["end"])
        selected = (stations_m >= start) & (
            stations_m <= end
            if index == len(source_manifests) - 1
            else stations_m < end
        )
        output[selected] = sample(source, selected)

    seam_blend_m = float(geography_manifest["continuity"]["seam_blend_distance_m"])
    for upstream, downstream in zip(
        normalized_sources, normalized_sources[1:], strict=False
    ):
        seam = float(upstream["manifest"]["station_range_m"]["end"])
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
    return (
        np.clip(output, 0.0, 255.0),
        len(source_manifests) - 1,
        exposure_normalization,
    )


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
    macro *= (1.0 + 0.075 * detail)[..., None]
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


def _smoothstep(lo: float, hi: float, values: np.ndarray) -> np.ndarray:
    t = np.clip((values - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _solver_derived_hydraulic_aeration(
    depth: np.ndarray,
    surface_m: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    wet: np.ndarray,
    dx_m: float,
    dy_m: float,
    named_rapid_authority: np.ndarray,
) -> np.ndarray:
    """Return a bounded static aeration mask derived from validated solver fields.

    Froude remains the global authority used by the original presentation bake.
    Supplemental breaking-water evidence is admitted only inside the smooth
    handoff envelope of a validated named-rapid window. It requires hydraulic
    surface slope plus acceleration/deformation, and an interior-wet-cell guard
    prevents dry-bank discontinuities from masquerading as whitewater.
    """

    speed = np.hypot(u, v)
    froude = speed / np.sqrt(9.80665 * np.maximum(depth, 0.05))
    legacy_froude_foam = np.clip((froude - 0.72) / 1.18, 0.0, 1.0)

    surface_ds = np.gradient(surface_m, dx_m, axis=0)
    surface_dl = np.gradient(surface_m, dy_m, axis=1)
    surface_slope = np.hypot(surface_ds, surface_dl)
    du_ds = np.gradient(u, dx_m, axis=0)
    du_dl = np.gradient(u, dy_m, axis=1)
    dv_ds = np.gradient(v, dx_m, axis=0)
    dv_dl = np.gradient(v, dy_m, axis=1)
    strain_rate = np.sqrt((du_ds - dv_dl) ** 2 + (du_dl + dv_ds) ** 2)
    convergence = np.maximum(-(du_ds + dv_dl), 0.0)
    acceleration = np.hypot(
        u * du_ds + v * du_dl,
        u * dv_ds + v * dv_dl,
    )

    criticality = 0.72 * _smoothstep(0.47, 1.15, froude)
    surface_break = 0.62 * np.sqrt(
        _smoothstep(0.020, 0.18, surface_slope)
        * _smoothstep(0.035, 0.32, acceleration)
    )
    deformation_break = 0.52 * np.sqrt(
        _smoothstep(0.060, 0.30, strain_rate)
        * _smoothstep(0.035, 0.32, acceleration)
    )
    convergence_break = 0.42 * np.sqrt(
        _smoothstep(0.025, 0.16, convergence)
        * _smoothstep(0.060, 0.30, strain_rate)
    )

    wet_neighbors = np.zeros(wet.shape, dtype=np.float32)
    wet_neighbors[1:] += wet[:-1]
    wet_neighbors[:-1] += wet[1:]
    wet_neighbors[:, 1:] += wet[:, :-1]
    wet_neighbors[:, :-1] += wet[:, 1:]
    interior_wet_weight = np.clip((wet_neighbors - 2.0) / 2.0, 0.0, 1.0)
    supplemental = (
        np.maximum.reduce(
            (criticality, surface_break, deformation_break, convergence_break)
        )
        * interior_wet_weight
        * np.clip(named_rapid_authority, 0.0, 1.0)
    )
    return np.maximum(legacy_froude_foam, supplemental) * wet


def _guide_feature_aeration(
    features: list[dict[str, Any]],
    stations_m: np.ndarray,
    lateral_m: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    wet: np.ndarray,
) -> np.ndarray:
    """Rasterize review-gated guide features into non-authoritative aeration.

    These ellipses are explicitly procedural presentation infill. Their centers,
    kinds, sizes, and flow-band strengths come from the same guide-interpreted
    scenario package as the live solver, but they never alter solver arrays,
    collision, navigation, or the broad water surface elevation.
    """

    kind_weight = {
        "hole": 1.00,
        "ledge": 0.95,
        "wave_train": 0.86,
        "lateral": 0.82,
        "rock": 0.52,
        "eddy_line": 0.48,
        "shallow": 0.34,
        "strainer": 0.22,
    }
    station_grid = stations_m[:, None]
    lateral_grid = lateral_m[None, :]
    aeration = np.zeros(wet.shape, dtype=np.float32)
    for feature in features:
        weight = float(kind_weight.get(str(feature["kind"]), 0.0))
        if weight <= 0.0:
            continue
        center = feature["center"]
        along_radius_m = float(
            np.clip(float(feature.get("length", 20.0)) * 0.45, 6.0, 28.0)
        )
        across_radius_m = float(
            np.clip(float(feature.get("width", 10.0)) * 0.50, 4.0, 14.0)
        )
        distance_squared = (
            (station_grid - float(center["x"])) / along_radius_m
        ) ** 2 + ((lateral_grid - float(center["y"])) / across_radius_m) ** 2
        influence = np.exp(-2.2 * distance_squared) * (distance_squared <= 1.8)
        strength = float(np.clip(float(feature.get("strength", 0.5)), 0.0, 1.0))
        aeration = np.maximum(
            aeration,
            weight * (0.45 + 0.55 * strength) * influence,
        )

    speed = np.hypot(u, v)
    speed_weight = 0.35 + 0.65 * _smoothstep(0.60, 2.50, speed)
    return np.clip(aeration * speed_weight, 0.0, 1.0) * wet


def _water_products(
    repo_root: Path,
    transit_manifest: dict[str, Any],
    streaming_manifest: dict[str, Any],
    stations_m: np.ndarray,
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    """Build static presentation water from the same fields used at runtime.

    The transit seed is continuous over the full route, but it intentionally
    lacks the resolved holes, laterals, wave trains, and bed controls in the
    cooked named-rapid windows. Runtime swaps those windows into D3. The saved
    seasonal water must blend the same validated fields into its visual-only
    surface and vertex channels or it can sit decimetres below the raft and
    present a calm pool while gameplay is sampling a rapid.
    """

    transit_dir = repo_root / FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH
    transit_dir = transit_dir.parent
    transit_grid = transit_manifest["grid"]
    water_lateral_m = float(transit_grid["origin_y_m"]) + float(
        transit_grid["dy_m"]
    ) * np.arange(int(transit_grid["ny"]), dtype=np.float64)
    result: dict[str, dict[str, np.ndarray]] = {}
    named_rapid_sources: list[dict[str, Any]] = []
    for band_id in FLOW_BANDS:
        bed = np.load(transit_dir / band_id / "bed.npy").T.astype(np.float32)
        depth = np.load(transit_dir / band_id / "h.npy").T.astype(np.float32)
        u = np.load(transit_dir / band_id / "u.npy").T.astype(np.float32)
        v = np.load(transit_dir / band_id / "v.npy").T.astype(np.float32)
        wet = np.load(transit_dir / band_id / "wet_mask.npy").T.astype(bool)
        surface_m = bed + depth
        named_rapid_authority = np.zeros(depth.shape, dtype=np.float32)
        guide_feature_aeration = np.zeros(depth.shape, dtype=np.float32)

        for window in streaming_manifest["windows"]:
            cooked_manifest_path = repo_root / window["cooked_fields_manifest"]
            cooked_manifest = _load_json(cooked_manifest_path)
            if not cooked_manifest["all_bands_passed"]:
                raise ValueError(
                    f"Named rapid has not passed every flow band: {cooked_manifest_path}"
                )
            grid = cooked_manifest["grid"]
            if int(grid["ny"]) != water_lateral_m.size:
                raise ValueError(
                    f"Named-rapid lateral grid does not match full reach: {cooked_manifest_path}"
                )
            named_lateral_m = float(grid["origin_y_m"]) + float(
                grid["dy_m"]
            ) * np.arange(int(grid["ny"]), dtype=np.float64)
            if not np.allclose(named_lateral_m, water_lateral_m, atol=1e-4):
                raise ValueError(
                    f"Named-rapid lateral coordinates do not match full reach: {cooked_manifest_path}"
                )

            named_dir = cooked_manifest_path.parent / band_id
            named_bed = np.load(named_dir / "bed.npy").T.astype(np.float32)
            named_depth = np.load(named_dir / "h.npy").T.astype(np.float32)
            named_u = np.load(named_dir / "u.npy").T.astype(np.float32)
            named_v = np.load(named_dir / "v.npy").T.astype(np.float32)
            named_wet = np.load(named_dir / "wet_mask.npy").T.astype(np.float32)
            source_station_m = float(grid["origin_x_m"]) + float(
                grid["dx_m"]
            ) * np.arange(int(grid["nx"]), dtype=np.float64)
            start_m, end_m = map(float, window["station_range_m"])
            target_rows = np.flatnonzero(
                (stations_m >= start_m) & (stations_m <= end_m)
            )
            if target_rows.size == 0:
                raise ValueError(
                    f"Named rapid does not intersect the full-reach grid: {cooked_manifest_path}"
                )
            target_station_m = stations_m[target_rows]

            def resample_named(values: np.ndarray) -> np.ndarray:
                sampled = np.empty(
                    (target_rows.size, water_lateral_m.size), dtype=np.float32
                )
                for column in range(water_lateral_m.size):
                    sampled[:, column] = np.interp(
                        target_station_m,
                        source_station_m,
                        values[:, column],
                    )
                return sampled

            datum_m = float(cooked_manifest["source_elevation_datum_m"])
            sampled_depth = resample_named(named_depth)
            sampled_surface_m = resample_named(named_bed) + sampled_depth + datum_m
            sampled_u = resample_named(named_u)
            sampled_v = resample_named(named_v)
            sampled_wet = resample_named(named_wet) >= 0.5

            scenario_band = next(
                item
                for item in cooked_manifest["bands"]
                if item["band_id"] == band_id
            )
            feature_path = (
                repo_root / scenario_band["scenario_package"] / "features.json"
            )
            features = _load_json(feature_path)["features"]
            sampled_feature_aeration = _guide_feature_aeration(
                features,
                target_station_m,
                water_lateral_m,
                sampled_u,
                sampled_v,
                sampled_wet,
            )

            handoff_m = float(window["handoff_blend_distance_m"])
            edge_distance_m = np.minimum(
                target_station_m - start_m,
                end_m - target_station_m,
            )
            blend_t = np.clip(edge_distance_m / max(handoff_m, 1e-6), 0.0, 1.0)
            blend_t = blend_t * blend_t * (3.0 - 2.0 * blend_t)
            blend = blend_t[:, None].astype(np.float32)
            base_blend = 1.0 - blend

            surface_m[target_rows] = (
                surface_m[target_rows] * base_blend + sampled_surface_m * blend
            )
            depth[target_rows] = depth[target_rows] * base_blend + sampled_depth * blend
            u[target_rows] = u[target_rows] * base_blend + sampled_u * blend
            v[target_rows] = v[target_rows] * base_blend + sampled_v * blend
            wet[target_rows] = np.where(
                blend >= 0.5,
                sampled_wet,
                wet[target_rows],
            )
            named_rapid_authority[target_rows] = np.maximum(
                named_rapid_authority[target_rows], blend
            )
            guide_feature_aeration[target_rows] = np.maximum(
                guide_feature_aeration[target_rows],
                sampled_feature_aeration * blend,
            )

            if band_id == FLOW_BANDS[0]:
                named_rapid_sources.append(
                    {
                        "window_id": window["window_id"],
                        "rapid_name": window["rapid_name"],
                        "cooked_fields_manifest": window["cooked_fields_manifest"],
                        "station_range_m": [start_m, end_m],
                        "handoff_blend_distance_m": handoff_m,
                        "source_elevation_datum_m": datum_m,
                        "all_bands_passed": True,
                    }
                )

        speed = np.hypot(u, v)
        solver_aeration = _solver_derived_hydraulic_aeration(
            depth,
            surface_m,
            u,
            v,
            wet,
            float(transit_grid["dx_m"]),
            float(transit_grid["dy_m"]),
            named_rapid_authority,
        )
        foam = np.maximum(solver_aeration, guide_feature_aeration) * wet
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
            "surface_m": surface_m,
            "presentation": presentation,
        }
    if not transit_manifest["all_bands_passed"]:
        raise ValueError("Full-reach transit source has not passed all flow bands")
    if len(named_rapid_sources) != int(streaming_manifest["rapid_window_count"]):
        raise ValueError("Not every named rapid was composited into presentation water")
    return result, named_rapid_sources


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


def _extended_far_field_route_frame(
    route_xy_m: np.ndarray,
    route_station_m: np.ndarray,
    route_normal_xy: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Extend the conditioning axis beyond gameplay endpoints.

    The fixed take-out camera sits only 138 m before the adopted route endpoint.
    A nearest-point distance field closes radially there, turning the valley
    envelope into a conspicuous terminal terrain wedge across the reservoir.
    Continue the last registered route frame through explicitly procedural,
    non-navigational scenery so the far field ends outside normal sightlines.
    """

    source_indices = np.append(
        np.arange(0, route_station_m.size, 8, dtype=np.int32),
        route_station_m.size - 1,
    )
    source_indices = np.unique(source_indices)
    sampled_xy = route_xy_m[source_indices]
    sampled_station = route_station_m[source_indices]
    upstream_distances = np.arange(
        FAR_FIELD_ROUTE_EXTENSION_M,
        0.0,
        -FAR_FIELD_ROUTE_EXTENSION_STEP_M,
        dtype=np.float64,
    )
    downstream_distances = np.arange(
        FAR_FIELD_ROUTE_EXTENSION_STEP_M,
        FAR_FIELD_ROUTE_EXTENSION_M + FAR_FIELD_ROUTE_EXTENSION_STEP_M * 0.5,
        FAR_FIELD_ROUTE_EXTENSION_STEP_M,
        dtype=np.float64,
    )
    upstream_tangent = np.asarray(
        [route_normal_xy[0, 1], -route_normal_xy[0, 0]], dtype=np.float64
    )
    downstream_tangent = np.asarray(
        [route_normal_xy[-1, 1], -route_normal_xy[-1, 0]], dtype=np.float64
    )
    upstream_xy = route_xy_m[0] - upstream_distances[:, None] * upstream_tangent
    downstream_xy = route_xy_m[-1] + downstream_distances[:, None] * downstream_tangent
    return (
        np.concatenate((upstream_xy, sampled_xy, downstream_xy), axis=0),
        np.concatenate(
            (
                route_station_m[0] - upstream_distances,
                sampled_station,
                route_station_m[-1] + downstream_distances,
            )
        ),
    )


def _sample_curvilinear_height(
    height_m: np.ndarray,
    stations_m: np.ndarray,
    lateral_m: np.ndarray,
    query_station_m: np.ndarray,
    query_lateral_m: np.ndarray,
) -> np.ndarray:
    """Bilinearly sample the station/lateral gameplay terrain grid."""

    row = np.interp(
        query_station_m,
        stations_m,
        np.arange(stations_m.size, dtype=np.float64),
    )
    column = np.interp(
        np.clip(query_lateral_m, lateral_m[0], lateral_m[-1]),
        lateral_m,
        np.arange(lateral_m.size, dtype=np.float64),
    )
    row0 = np.floor(row).astype(np.int32)
    column0 = np.floor(column).astype(np.int32)
    row1 = np.minimum(row0 + 1, height_m.shape[0] - 1)
    column1 = np.minimum(column0 + 1, height_m.shape[1] - 1)
    row_t = row - row0
    column_t = column - column0
    return (
        height_m[row0, column0] * (1.0 - row_t) * (1.0 - column_t)
        + height_m[row0, column1] * (1.0 - row_t) * column_t
        + height_m[row1, column0] * row_t * (1.0 - column_t)
        + height_m[row1, column1] * row_t * column_t
    ).astype(np.float32)


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
        # Terrain topology, exclusion, and ownership stay on the deliberately
        # bounded 257-square grid.  Macro colour has no reason to share that
        # vertex budget: retain a 1024-square source drape so the licensed
        # 4096-square NAIP windows do not collapse into broad colour blocks in
        # Unreal.  This improves presentation without quadrupling live terrain
        # vertices or foliage sampling work.
        macro_x_epsg = np.linspace(dem_bounds[0], dem_bounds[2], FAR_FIELD_MACRO_SIZE)
        macro_y_epsg = np.linspace(dem_bounds[3], dem_bounds[1], FAR_FIELD_MACRO_SIZE)
        macro_world_x_epsg, macro_world_y_epsg = np.meshgrid(macro_x_epsg, macro_y_epsg)
        macro = _bilinear_rgb(
            aerial_rgb,
            macro_world_x_epsg,
            macro_world_y_epsg,
            aerial_bounds,
        )
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
        # Preserve most source land-cover variation while applying a restrained
        # palette condition that prevents blue-green orthophoto cast from
        # dominating the lit PBR result.
        macro = np.clip(macro * 0.84 + terrain_palette * 0.16, 0.0, 255.0).astype(
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
                "macro_dimensions": [FAR_FIELD_MACRO_SIZE, FAR_FIELD_MACRO_SIZE],
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


def _raster_blend_support(
    world_x: np.ndarray,
    world_y: np.ndarray,
    bounds: list[float],
    ground_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return source coverage, edge blend weight, and rectangle distance."""

    minimum_x, minimum_y, maximum_x, maximum_y = map(float, bounds)
    inside = (
        (world_x >= minimum_x)
        & (world_x <= maximum_x)
        & (world_y >= minimum_y)
        & (world_y <= maximum_y)
    )
    edge_distance_m = (
        np.minimum.reduce(
            (
                world_x - minimum_x,
                maximum_x - world_x,
                world_y - minimum_y,
                maximum_y - world_y,
            )
        )
        * ground_scale
    )
    blend_t = np.clip(edge_distance_m / FAR_FIELD_SOURCE_EDGE_BLEND_M, 0.0, 1.0)
    smooth_t = blend_t * blend_t * (3.0 - 2.0 * blend_t)
    # A small nonzero edge weight keeps an authoritative sample defined at the
    # exact shared boundary while allowing a neighboring source interior to
    # dominate inside an overlap.
    source_weight = inside.astype(np.float32) * (0.05 + 0.95 * smooth_t)
    dx = np.maximum.reduce(
        (minimum_x - world_x, np.zeros_like(world_x), world_x - maximum_x)
    )
    dy = np.maximum.reduce(
        (minimum_y - world_y, np.zeros_like(world_y), world_y - maximum_y)
    )
    rectangle_distance_m = np.hypot(dx, dy) * ground_scale
    return (
        inside,
        source_weight.astype(np.float32),
        rectangle_distance_m.astype(np.float32),
    )


def _stitched_global_bounds_local_m(
    repo_root: Path,
    source_manifests: list[dict[str, Any]],
    origin_epsg: np.ndarray,
    ground_scale: float,
) -> tuple[float, float, float, float]:
    local_bounds = []
    for manifest in source_manifests:
        record = manifest["source_artifacts"]["dem"]
        _, effective_bounds = _load_dem(
            repo_root / record["path"], record["source_bounds_epsg3857"]
        )
        bounds = np.asarray(effective_bounds, dtype=np.float64)
        local_bounds.append(
            np.asarray(
                [
                    (bounds[0] - origin_epsg[0]) * ground_scale,
                    (bounds[1] - origin_epsg[1]) * ground_scale,
                    (bounds[2] - origin_epsg[0]) * ground_scale,
                    (bounds[3] - origin_epsg[1]) * ground_scale,
                ]
            )
        )
    stacked = np.asarray(local_bounds)
    # The official rasters stop close to both playable route endpoints. Ending
    # the render mesh at those bounds exposes a suspended rectangular shelf
    # from guide-eye cameras near Chili Bar and Salmon Falls. Extend the common
    # domain with explicitly procedural, non-navigational geography so normal
    # sightlines terminate in terrain and atmosphere instead of a mesh edge.
    minimum_x = (
        np.floor(
            (np.min(stacked[:, 0]) - FAR_FIELD_DOMAIN_PADDING_M) / FAR_FIELD_CELL_SIZE_M
        )
        * FAR_FIELD_CELL_SIZE_M
    )
    minimum_y = (
        np.floor(
            (np.min(stacked[:, 1]) - FAR_FIELD_DOMAIN_PADDING_M) / FAR_FIELD_CELL_SIZE_M
        )
        * FAR_FIELD_CELL_SIZE_M
    )
    source_maximum_x = (
        np.ceil(
            (np.max(stacked[:, 2]) + FAR_FIELD_DOMAIN_PADDING_M) / FAR_FIELD_CELL_SIZE_M
        )
        * FAR_FIELD_CELL_SIZE_M
    )
    source_maximum_y = (
        np.ceil(
            (np.max(stacked[:, 3]) + FAR_FIELD_DOMAIN_PADDING_M) / FAR_FIELD_CELL_SIZE_M
        )
        * FAR_FIELD_CELL_SIZE_M
    )
    interval_count_x = int(
        np.ceil((source_maximum_x - minimum_x) / FAR_FIELD_CELL_SIZE_M)
    )
    interval_count_y = int(
        np.ceil((source_maximum_y - minimum_y) / FAR_FIELD_CELL_SIZE_M)
    )
    interval_count_x = int(
        np.ceil(interval_count_x / FAR_FIELD_TILE_COLUMNS) * FAR_FIELD_TILE_COLUMNS
    )
    interval_count_y = int(
        np.ceil(interval_count_y / FAR_FIELD_TILE_ROWS) * FAR_FIELD_TILE_ROWS
    )
    return (
        float(minimum_x),
        float(minimum_y),
        float(minimum_x + interval_count_x * FAR_FIELD_CELL_SIZE_M),
        float(minimum_y + interval_count_y * FAR_FIELD_CELL_SIZE_M),
    )


def _composite_stitched_height(
    repo_root: Path,
    source_manifests: list[dict[str, Any]],
    world_x_epsg: np.ndarray,
    world_y_epsg: np.ndarray,
    local_x_m: np.ndarray,
    local_y_m: np.ndarray,
    ground_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    shape = world_x_epsg.shape
    source_sum = np.zeros(shape, dtype=np.float64)
    source_weight_sum = np.zeros(shape, dtype=np.float64)
    fallback_sum = np.zeros(shape, dtype=np.float64)
    fallback_weight_sum = np.zeros(shape, dtype=np.float64)
    source_count = np.zeros(shape, dtype=np.uint8)
    nearest_source_distance_m = np.full(shape, np.inf, dtype=np.float32)
    for manifest in source_manifests:
        record = manifest["source_artifacts"]["dem"]
        dem, bounds = _load_dem(
            repo_root / record["path"], record["source_bounds_epsg3857"]
        )
        sampled = _bilinear_sample(dem, world_x_epsg, world_y_epsg, bounds).astype(
            np.float32
        )
        inside, source_weight, rectangle_distance_m = _raster_blend_support(
            world_x_epsg, world_y_epsg, bounds, ground_scale
        )
        source_count += inside.astype(np.uint8)
        source_sum += sampled * source_weight
        source_weight_sum += source_weight
        fallback_weight = 1.0 / np.square(rectangle_distance_m + 128.0)
        fallback_sum += sampled * fallback_weight
        fallback_weight_sum += fallback_weight
        nearest_source_distance_m = np.minimum(
            nearest_source_distance_m, rectangle_distance_m
        )

    has_source = source_weight_sum > 0.0
    height_m = np.divide(
        source_sum,
        source_weight_sum,
        out=np.zeros_like(source_sum),
        where=has_source,
    )
    missing = ~has_source
    height_m[missing] = fallback_sum[missing] / np.maximum(
        fallback_weight_sum[missing], 1e-12
    )
    # Uncovered parts of the common rectangle use a bounded world-space relief
    # continuation. Its amplitude begins at zero on source coverage, so the
    # infill cannot introduce another hard source boundary.
    infill_t = np.clip(nearest_source_distance_m / 900.0, 0.0, 1.0)
    infill_noise = (
        0.52 * np.sin(local_x_m / 337.0 + local_y_m / 619.0)
        + 0.31 * np.sin(local_x_m / 911.0 - local_y_m / 421.0 + 0.73)
        + 0.17 * np.cos(local_x_m / 173.0 + local_y_m / 281.0 - 1.11)
    )
    height_m[missing] += (
        FAR_FIELD_PROCEDURAL_INFILL_MAX_RELIEF_M
        * infill_t[missing]
        * infill_noise[missing]
    )
    return height_m.astype(np.float32), source_count, nearest_source_distance_m


def _lattice_hash_01(
    lattice_x: np.ndarray,
    lattice_y: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Return stable pseudo-random lattice values in [0, 1]."""

    x = np.asarray(lattice_x, dtype=np.int64).astype(np.uint64, copy=False)
    y = np.asarray(lattice_y, dtype=np.int64).astype(np.uint64, copy=False)
    hashed = (
        x * np.uint64(0x9E3779B185EBCA87)
        ^ y * np.uint64(0xC2B2AE3D27D4EB4F)
        ^ np.uint64(seed & 0xFFFFFFFFFFFFFFFF)
    )
    hashed ^= hashed >> np.uint64(30)
    hashed *= np.uint64(0xBF58476D1CE4E5B9)
    hashed ^= hashed >> np.uint64(27)
    hashed *= np.uint64(0x94D049BB133111EB)
    hashed ^= hashed >> np.uint64(31)
    return (hashed >> np.uint64(40)).astype(np.float32) / np.float32(16_777_215.0)


def _world_space_value_noise(
    local_x_m: np.ndarray,
    local_y_m: np.ndarray,
    wavelength_m: float,
    seed: int,
) -> np.ndarray:
    """Evaluate smooth, coordinate-stable value noise over arbitrary world samples."""

    scaled_x = np.asarray(local_x_m, dtype=np.float32) / np.float32(wavelength_m)
    scaled_y = np.asarray(local_y_m, dtype=np.float32) / np.float32(wavelength_m)
    lattice_x = np.floor(scaled_x).astype(np.int64)
    lattice_y = np.floor(scaled_y).astype(np.int64)
    fraction_x = scaled_x - lattice_x.astype(np.float32)
    fraction_y = scaled_y - lattice_y.astype(np.float32)
    # Quintic interpolation reaches zero first and second derivatives at every
    # lattice boundary, avoiding the square-cell shading tell of linear noise.
    smooth_x = fraction_x**3 * (fraction_x * (fraction_x * 6.0 - 15.0) + 10.0)
    smooth_y = fraction_y**3 * (fraction_y * (fraction_y * 6.0 - 15.0) + 10.0)
    value_00 = _lattice_hash_01(lattice_x, lattice_y, seed)
    value_10 = _lattice_hash_01(lattice_x + 1, lattice_y, seed)
    value_01 = _lattice_hash_01(lattice_x, lattice_y + 1, seed)
    value_11 = _lattice_hash_01(lattice_x + 1, lattice_y + 1, seed)
    row_0 = value_00 + (value_10 - value_00) * smooth_x
    row_1 = value_01 + (value_11 - value_01) * smooth_x
    return (row_0 + (row_1 - row_0) * smooth_y).astype(np.float32)


def _smoothstep_array(
    edge_0: float,
    edge_1: float,
    value: np.ndarray,
) -> np.ndarray:
    t = np.clip((value - edge_0) / (edge_1 - edge_0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _procedural_far_field_macro_palette(
    local_x_m: np.ndarray,
    local_y_m: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Generate irregular Sierra land-cover colour where aerial data is absent."""

    world_x = np.asarray(local_x_m, dtype=np.float32)
    world_y = np.asarray(local_y_m, dtype=np.float32)
    warp_x = (
        _world_space_value_noise(world_x, world_y, 2_900.0, seed ^ 0x61C88647) - 0.5
    ) * 760.0
    warp_y = (
        _world_space_value_noise(world_x, world_y, 2_300.0, seed ^ 0x9E3779B9) - 0.5
    ) * 620.0
    warped_x = world_x + warp_x
    warped_y = world_y + warp_y

    broad_moisture = _world_space_value_noise(
        warped_x, warped_y, 2_650.0, seed ^ 0x243F6A88
    )
    medium_moisture = _world_space_value_noise(
        warped_x, warped_y, 820.0, seed ^ 0x85A308D3
    )
    detail_moisture = _world_space_value_noise(
        warped_x, warped_y, 280.0, seed ^ 0x13198A2E
    )
    moisture = np.clip(
        broad_moisture * 0.54 + medium_moisture * 0.31 + detail_moisture * 0.15,
        0.0,
        1.0,
    )
    woodland = _smoothstep_array(0.55, 0.76, moisture)
    scrub = _smoothstep_array(0.32, 0.60, moisture) * (1.0 - woodland)

    rock_patch = _world_space_value_noise(warped_x, warped_y, 930.0, seed ^ 0x03707344)
    ridge_noise = _world_space_value_noise(warped_x, warped_y, 360.0, seed ^ 0xA4093822)
    ridge_signal = 1.0 - np.abs(ridge_noise * 2.0 - 1.0)
    exposed_rock = _smoothstep_array(
        0.67, 0.88, rock_patch * 0.64 + ridge_signal * 0.36
    ) * (1.0 - woodland * 0.78)

    dry_grass = np.asarray([126.0, 108.0, 72.0], dtype=np.float32)
    chaparral = np.asarray([71.0, 77.0, 48.0], dtype=np.float32)
    woodland_color = np.asarray([29.0, 47.0, 31.0], dtype=np.float32)
    rock_color = np.asarray([103.0, 96.0, 82.0], dtype=np.float32)
    palette = dry_grass + (chaparral - dry_grass) * scrub[..., None]
    palette += (woodland_color - palette) * woodland[..., None]
    palette += (rock_color - palette) * exposed_rock[..., None]

    fine_variation = 0.68 * _world_space_value_noise(
        warped_x, warped_y, 145.0, seed ^ 0x299F31D0
    ) + 0.32 * _world_space_value_noise(warped_x, warped_y, 54.0, seed ^ 0x082EFA98)
    palette *= (0.87 + 0.23 * fine_variation)[..., None]
    # Sub-canopy crown gaps and small oak/pine groups keep procedural zones at
    # an aerial-like spatial frequency instead of stopping at broad colour
    # blobs. The signal is colour-only and does not claim new land-cover
    # authority or place gameplay foliage.
    crown_signal = _world_space_value_noise(warped_x, warped_y, 34.0, seed ^ 0x452821E6)
    crown_clusters = _smoothstep_array(0.58, 0.82, crown_signal) * woodland
    palette *= (1.0 - 0.24 * crown_clusters)[..., None]
    temperature = (
        _world_space_value_noise(world_x, world_y, 4_800.0, seed ^ 0xEC4E6C89) - 0.5
    )
    palette += np.stack(
        (temperature * 10.0, temperature * 2.0, temperature * -5.0),
        axis=-1,
    )
    return np.clip(palette, 0.0, 255.0).astype(np.float32)


def _composite_stitched_macro(
    repo_root: Path,
    source_manifests: list[dict[str, Any]],
    world_x_epsg: np.ndarray,
    world_y_epsg: np.ndarray,
    local_x_m: np.ndarray,
    local_y_m: np.ndarray,
    ground_scale: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    shape = world_x_epsg.shape
    source_sum = np.zeros((*shape, 3), dtype=np.float32)
    source_weight_sum = np.zeros(shape, dtype=np.float32)
    nearest_source_distance_m = np.full(shape, np.inf, dtype=np.float32)

    # NAIP source windows span different flights and acquisition dates. The
    # final Salmon Falls image is more than twice as bright as the upper-run
    # imagery, which otherwise survives geometric edge blending as a pale
    # rectangular landform. Normalize only robust median luminance, retain the
    # source chroma and local contrast, and clamp every gain so this renderer-
    # space correction cannot erase real seasonal land-cover differences.
    aerial_sources, exposure_normalization = _load_exposure_normalized_aerial_sources(
        repo_root, source_manifests
    )
    for source in aerial_sources:
        sampled = _bilinear_rgb(
            source["rgb"],
            world_x_epsg,
            world_y_epsg,
            source["effective_bounds"],
        )
        _, source_weight, rectangle_distance_m = _raster_blend_support(
            world_x_epsg,
            world_y_epsg,
            source["effective_bounds"],
            ground_scale,
        )
        source_sum += sampled * source_weight[..., None]
        source_weight_sum += source_weight
        nearest_source_distance_m = np.minimum(
            nearest_source_distance_m, rectangle_distance_m
        )

    has_source = source_weight_sum > 0.0
    macro = np.divide(
        source_sum,
        source_weight_sum[..., None],
        out=np.zeros_like(source_sum),
        where=has_source[..., None],
    )
    missing = ~has_source
    # Missing aerial coverage is explicit procedural game geography. The v1
    # sine field was continuous but exposed long, parallel colour bands from
    # guide-eye cameras. Use seeded lattice value noise with domain warping so
    # the same summer-Sierra classes form irregular, nested patches without a
    # preferred stripe direction. The field is evaluated once on the shared
    # global macro grid, retaining bit-identical streaming-tile edges.
    procedural_palette = _procedural_far_field_macro_palette(local_x_m, local_y_m, seed)
    # Do not stretch the last orthophoto pixel across uncovered geography. The
    # absolute source weight falls through the 256 m edge band, producing a
    # smooth handoff to world-space procedural colour; uncovered cells use the
    # procedural palette completely.
    source_confidence = np.clip(source_weight_sum / 0.5, 0.0, 1.0)
    source_confidence[missing] = 0.0
    macro = macro * source_confidence[..., None] + procedural_palette * (
        1.0 - source_confidence[..., None]
    )
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
    return (
        np.clip(macro * 0.84 + terrain_palette * 0.16, 0.0, 255.0).astype(np.uint8),
        nearest_source_distance_m,
        exposure_normalization,
    )


def _write_stitched_far_field_patches(
    repo_root: Path,
    output_dir: Path,
    geography_manifest: dict[str, Any],
    arrays: dict[str, np.ndarray],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build eight streaming tiles from one watertight global source mosaic."""

    patch_dir = output_dir / "far_field"
    patch_dir.mkdir(parents=True, exist_ok=True)
    source_manifests = [
        _load_json(repo_root / entry["manifest_path"])
        for entry in geography_manifest["inputs"]["source_windows"]
    ]
    ground_scale = float(arrays["epsg3857_to_ground_scale"])
    origin_epsg = np.asarray(
        [
            arrays["centerline_epsg3857_x_m"][0],
            arrays["centerline_epsg3857_y_m"][0],
        ],
        dtype=np.float64,
    )
    minimum_x, minimum_y, maximum_x, maximum_y = _stitched_global_bounds_local_m(
        repo_root, source_manifests, origin_epsg, ground_scale
    )
    interval_count_x = int(round((maximum_x - minimum_x) / FAR_FIELD_CELL_SIZE_M))
    interval_count_y = int(round((maximum_y - minimum_y) / FAR_FIELD_CELL_SIZE_M))
    width = interval_count_x + 1
    height = interval_count_y + 1
    global_x_m = np.linspace(minimum_x, maximum_x, width)
    global_y_m = np.linspace(maximum_y, minimum_y, height)
    local_x_m, local_y_m = np.meshgrid(global_x_m, global_y_m)
    world_x_epsg = local_x_m / ground_scale + origin_epsg[0]
    world_y_epsg = local_y_m / ground_scale + origin_epsg[1]
    height_m, source_count, nearest_source_distance_m = _composite_stitched_height(
        repo_root,
        source_manifests,
        world_x_epsg,
        world_y_epsg,
        local_x_m,
        local_y_m,
        ground_scale,
    )
    route_local_m = np.column_stack(
        (
            arrays["centerline_epsg3857_x_m"],
            arrays["centerline_epsg3857_y_m"],
        )
    )
    route_local_m = (route_local_m - origin_epsg) * ground_scale
    conditioning_route_xy_m, conditioning_route_station_m = (
        _extended_far_field_route_frame(
            route_local_m,
            arrays["stations_m"].astype(np.float64),
            np.column_stack(
                (
                    arrays["centerline_normal_x"],
                    arrays["centerline_normal_y"],
                )
            ),
        )
    )
    distance_m = _nearest_route_distance_m(
        np.stack((local_x_m, local_y_m), axis=-1), conditioning_route_xy_m
    )
    stations_m = arrays["stations_m"].astype(np.float64)
    nearest_station_m = _nearest_route_station_m(
        np.stack((local_x_m, local_y_m), axis=-1),
        conditioning_route_xy_m,
        conditioning_route_station_m,
    )
    nearest_center_x_m = np.interp(nearest_station_m, stations_m, route_local_m[:, 0])
    nearest_center_y_m = np.interp(nearest_station_m, stations_m, route_local_m[:, 1])
    nearest_normal_x = np.interp(
        nearest_station_m, stations_m, arrays["centerline_normal_x"]
    )
    nearest_normal_y = np.interp(
        nearest_station_m, stations_m, arrays["centerline_normal_y"]
    )
    normal_length = np.maximum(np.hypot(nearest_normal_x, nearest_normal_y), 1e-9)
    nearest_normal_x /= normal_length
    nearest_normal_y /= normal_length
    nearest_lateral_m = (local_x_m - nearest_center_x_m) * nearest_normal_x + (
        local_y_m - nearest_center_y_m
    ) * nearest_normal_y
    detailed_height_m = _sample_curvilinear_height(
        arrays["bed_elevation_m"].astype(np.float32),
        stations_m,
        arrays["lateral_offsets_m"].astype(np.float64),
        nearest_station_m,
        nearest_lateral_m,
    )
    center_height_m = _sample_curvilinear_height(
        arrays["bed_elevation_m"].astype(np.float32),
        stations_m,
        arrays["lateral_offsets_m"].astype(np.float64),
        nearest_station_m,
        np.zeros_like(nearest_station_m),
    )
    alignment_t = np.clip(
        (FAR_FIELD_CORRIDOR_ALIGNMENT_FADE_M - distance_m)
        / (FAR_FIELD_CORRIDOR_ALIGNMENT_FADE_M - FAR_FIELD_CORRIDOR_ALIGNMENT_FULL_M),
        0.0,
        1.0,
    )
    alignment_weight = alignment_t * alignment_t * (3.0 - 2.0 * alignment_t)
    registered_height_m = detailed_height_m - FAR_FIELD_CORRIDOR_ALIGNMENT_BELOW_M
    height_m = (
        height_m * (1.0 - alignment_weight) + registered_height_m * alignment_weight
    ).astype(np.float32)
    # A narrow binary cutout beside an unconditioned DEM can expose a very
    # steep terrain surface above a guide camera at tight bends. The former
    # constant 14 percent cap solved that safety problem by creating a new one:
    # long conical sheets on both banks. Continue the close-detail bank profile
    # with a sublinear valley shoulder, then modulate it with world-space ridge
    # and drainage fields. The envelope only lowers the source and fades out by
    # 1,800 m, preserving broad authoritative landforms outside the registered
    # gameplay valley.
    valley_profile_m = FAR_FIELD_VALLEY_PROFILE_SCALE * np.power(
        np.maximum(distance_m, 0.0), FAR_FIELD_VALLEY_PROFILE_EXPONENT
    )
    valley_shoulder_signal = np.clip(
        0.50
        + 0.27 * np.sin(local_x_m / 520.0 + local_y_m / 810.0 + 0.27)
        + 0.16 * np.sin(local_x_m / 233.0 - local_y_m / 347.0 - 0.91)
        + 0.07 * np.cos(local_x_m / 119.0 + local_y_m / 173.0 + 1.43),
        0.0,
        1.0,
    )
    valley_cap_height_m = (
        center_height_m
        + FAR_FIELD_VALLEY_GRADE_BASE_M
        + valley_profile_m * (0.78 + 0.34 * valley_shoulder_signal)
    )
    valley_carve_t = np.clip(
        (distance_m - FAR_FIELD_VALLEY_CARVE_START_M)
        / (FAR_FIELD_VALLEY_GRADE_CAP_FULL_M - FAR_FIELD_VALLEY_CARVE_START_M),
        0.0,
        1.0,
    )
    valley_gully_signal = np.clip(
        0.50
        + 0.31 * np.sin(local_x_m / 430.0 + local_y_m / 670.0 + 0.41)
        + 0.19 * np.sin(local_x_m / 910.0 - local_y_m / 510.0 - 1.17),
        0.0,
        1.0,
    )
    valley_cap_height_m -= (
        FAR_FIELD_VALLEY_CARVE_MAX_DEPTH_M * valley_carve_t * valley_gully_signal**2
    )
    valley_condition_t = np.clip(
        (distance_m - FAR_FIELD_VALLEY_CONDITIONING_START_M)
        / (
            FAR_FIELD_VALLEY_CONDITIONING_FULL_M - FAR_FIELD_VALLEY_CONDITIONING_START_M
        ),
        0.0,
        1.0,
    )
    valley_condition_weight = (
        valley_condition_t * valley_condition_t * (3.0 - 2.0 * valley_condition_t)
    )
    valley_fade_t = np.clip(
        (FAR_FIELD_VALLEY_GRADE_CAP_FADE_M - distance_m)
        / (FAR_FIELD_VALLEY_GRADE_CAP_FADE_M - FAR_FIELD_VALLEY_GRADE_CAP_FULL_M),
        0.0,
        1.0,
    )
    valley_fade_weight = valley_fade_t * valley_fade_t * (3.0 - 2.0 * valley_fade_t)
    valley_cap_weight = valley_condition_weight * valley_fade_weight
    height_m = (
        height_m - np.maximum(height_m - valley_cap_height_m, 0.0) * valley_cap_weight
    ).astype(np.float32)
    underlay_weight = np.clip(1.0 - distance_m / FAR_FIELD_UNDERLAY_FALLOFF_M, 0.0, 1.0)
    height_m = (height_m - FAR_FIELD_UNDERLAY_MAX_DEPTH_M * underlay_weight**2).astype(
        np.float32
    )
    terrain_mask = np.where(
        distance_m >= FAR_FIELD_CORRIDOR_EXCLUSION_M, 255, 0
    ).astype(np.uint8)
    river_distance_decimeters = np.rint(
        np.clip(distance_m * 10.0, 0.0, 65535.0)
    ).astype(np.uint16)
    # Compatibility artifact for the Unreal importer. Every sample is owned;
    # topology is partitioned only by the common rectangular tile grid.
    ownership_mask = np.full((height, width), 255, dtype=np.uint8)

    height_min = float(np.min(height_m))
    height_max = float(np.max(height_m))
    height_span = max(height_max - height_min, 1.0)
    encoded_height = np.rint(
        np.clip((height_m - height_min) / height_span, 0.0, 1.0) * 65535.0
    ).astype(np.uint16)

    macro_width = FAR_FIELD_TILE_COLUMNS * (FAR_FIELD_MACRO_SIZE - 1) + 1
    macro_height = FAR_FIELD_TILE_ROWS * (FAR_FIELD_MACRO_TILE_HEIGHT - 1) + 1
    macro_x_m = np.linspace(minimum_x, maximum_x, macro_width)
    macro_y_m = np.linspace(maximum_y, minimum_y, macro_height)
    macro_local_x_m, macro_local_y_m = np.meshgrid(macro_x_m, macro_y_m)
    macro_world_x_epsg = macro_local_x_m / ground_scale + origin_epsg[0]
    macro_world_y_epsg = macro_local_y_m / ground_scale + origin_epsg[1]
    macro, macro_nearest_source_distance_m, aerial_exposure_normalization = (
        _composite_stitched_macro(
            repo_root,
            source_manifests,
            macro_world_x_epsg,
            macro_world_y_epsg,
            macro_local_x_m,
            macro_local_y_m,
            ground_scale,
            seed,
        )
    )

    tile_intervals_x = interval_count_x // FAR_FIELD_TILE_COLUMNS
    tile_intervals_y = interval_count_y // FAR_FIELD_TILE_ROWS
    macro_intervals_x = FAR_FIELD_MACRO_SIZE - 1
    macro_intervals_y = FAR_FIELD_MACRO_TILE_HEIGHT - 1
    records: list[dict[str, Any]] = []
    for tile_row in range(FAR_FIELD_TILE_ROWS):
        for tile_column in range(FAR_FIELD_TILE_COLUMNS):
            ordinal = tile_row * FAR_FIELD_TILE_COLUMNS + tile_column
            row_start = tile_row * tile_intervals_y
            row_stop = (tile_row + 1) * tile_intervals_y
            column_start = tile_column * tile_intervals_x
            column_stop = (tile_column + 1) * tile_intervals_x
            macro_row_start = tile_row * macro_intervals_y
            macro_row_stop = (tile_row + 1) * macro_intervals_y
            macro_column_start = tile_column * macro_intervals_x
            macro_column_stop = (tile_column + 1) * macro_intervals_x
            tile_slice = np.s_[row_start : row_stop + 1, column_start : column_stop + 1]
            macro_slice = np.s_[
                macro_row_start : macro_row_stop + 1,
                macro_column_start : macro_column_stop + 1,
            ]
            patch_id = f"far_field_{ordinal:02d}"
            height_path = patch_dir / f"{patch_id}_height.png"
            macro_path = patch_dir / f"{patch_id}_macro_albedo.png"
            mask_path = patch_dir / f"{patch_id}_corridor_exclusion.png"
            ownership_path = patch_dir / f"{patch_id}_source_window_ownership.png"
            distance_path = patch_dir / f"{patch_id}_river_distance_dm.png"
            Image.fromarray(encoded_height[tile_slice], mode="I;16").save(height_path)
            Image.fromarray(macro[macro_slice], mode="RGB").save(macro_path)
            Image.fromarray(terrain_mask[tile_slice], mode="L").save(mask_path)
            Image.fromarray(ownership_mask[tile_slice], mode="L").save(ownership_path)
            Image.fromarray(river_distance_decimeters[tile_slice], mode="I;16").save(
                distance_path
            )
            tile_source_count = source_count[tile_slice]
            tile_distance = nearest_source_distance_m[tile_slice]
            tile_macro_distance = macro_nearest_source_distance_m[macro_slice]
            tile_height = encoded_height[tile_slice]
            tile_mask = terrain_mask[tile_slice]
            records.append(
                {
                    "patch_id": patch_id,
                    "source_window_id": f"stitched_global_r{tile_row}_c{tile_column}",
                    "authority": "USGS_3DEP_and_USDA_NAIP_global_mosaic_with_bounded_procedural_gap_infill",
                    "topology": "shared_global_grid_streaming_tile",
                    "dimensions": [
                        int(tile_height.shape[1]),
                        int(tile_height.shape[0]),
                    ],
                    "macro_dimensions": [
                        int(macro[macro_slice].shape[1]),
                        int(macro[macro_slice].shape[0]),
                    ],
                    "bounds_local_m": [
                        round(float(global_x_m[column_start]), 3),
                        round(float(global_y_m[row_stop]), 3),
                        round(float(global_x_m[column_stop]), 3),
                        round(float(global_y_m[row_start]), 3),
                    ],
                    "height": _artifact(repo_root, height_path),
                    "height_encoding": {
                        "minimum_elevation_m": round(height_min, 6),
                        "maximum_elevation_m": round(height_max, 6),
                        "uint16_min": 0,
                        "uint16_max": 65535,
                        "shared_across_all_tiles": True,
                    },
                    "macro_albedo": _artifact(repo_root, macro_path),
                    "corridor_exclusion_mask": _artifact(repo_root, mask_path),
                    "source_window_ownership_mask": _artifact(
                        repo_root, ownership_path
                    ),
                    "river_distance_to_route": _artifact(repo_root, distance_path),
                    "river_distance_encoding": {
                        "unit": "decimeter",
                        "meters_per_uint16": 0.1,
                        "maximum_representable_m": 6553.5,
                    },
                    "visible_vertex_fraction": round(
                        float(np.count_nonzero(tile_mask)) / tile_mask.size, 6
                    ),
                    "owned_vertex_fraction": 1.0,
                    "authoritative_vertex_fraction": round(
                        float(np.count_nonzero(tile_source_count))
                        / tile_source_count.size,
                        6,
                    ),
                    "maximum_procedural_infill_distance_m": round(
                        float(np.max(tile_distance)), 3
                    ),
                    "maximum_macro_infill_distance_m": round(
                        float(np.max(tile_macro_distance)), 3
                    ),
                }
            )

    topology = {
        "algorithm": "edge_weighted_official_source_mosaic_then_shared_grid_tiling",
        "procedural_macro_land_cover": (
            "domain_warped_world_space_dry_grass_chaparral_woodland_rock_v2"
        ),
        "global_grid_dimensions": [width, height],
        "global_bounds_local_m": [minimum_x, minimum_y, maximum_x, maximum_y],
        "cell_size_m": FAR_FIELD_CELL_SIZE_M,
        "tile_layout": [FAR_FIELD_TILE_COLUMNS, FAR_FIELD_TILE_ROWS],
        "shared_edge_vertices": True,
        "shared_height_encoding": True,
        "source_window_ownership_cuts": False,
        "source_edge_blend_distance_m": FAR_FIELD_SOURCE_EDGE_BLEND_M,
        "aerial_exposure_normalization": aerial_exposure_normalization,
        "corridor_alignment_full_distance_m": FAR_FIELD_CORRIDOR_ALIGNMENT_FULL_M,
        "corridor_alignment_fade_distance_m": FAR_FIELD_CORRIDOR_ALIGNMENT_FADE_M,
        "corridor_alignment_below_detailed_m": FAR_FIELD_CORRIDOR_ALIGNMENT_BELOW_M,
        "detailed_terrain_half_width_m": float(
            geography_manifest["continuity"]["unreal_detailed_ribbon_orientation"][
                "half_width_m"
            ]
        ),
        "corridor_render_overlap_m": float(
            geography_manifest["continuity"]["unreal_detailed_ribbon_orientation"][
                "half_width_m"
            ]
            - FAR_FIELD_CORRIDOR_EXCLUSION_M
        ),
        "procedural_route_extension_each_endpoint_m": FAR_FIELD_ROUTE_EXTENSION_M,
        "procedural_route_extension_step_m": FAR_FIELD_ROUTE_EXTENSION_STEP_M,
        "procedural_route_extension_not_for_navigation": True,
        "valley_profile_scale": FAR_FIELD_VALLEY_PROFILE_SCALE,
        "valley_profile_exponent": FAR_FIELD_VALLEY_PROFILE_EXPONENT,
        "valley_grade_base_m": FAR_FIELD_VALLEY_GRADE_BASE_M,
        "valley_conditioning_start_distance_m": (FAR_FIELD_VALLEY_CONDITIONING_START_M),
        "valley_conditioning_full_distance_m": (FAR_FIELD_VALLEY_CONDITIONING_FULL_M),
        "valley_grade_cap_full_distance_m": FAR_FIELD_VALLEY_GRADE_CAP_FULL_M,
        "valley_grade_cap_fade_distance_m": FAR_FIELD_VALLEY_GRADE_CAP_FADE_M,
        "valley_gully_carve_start_distance_m": FAR_FIELD_VALLEY_CARVE_START_M,
        "valley_gully_carve_maximum_depth_m": FAR_FIELD_VALLEY_CARVE_MAX_DEPTH_M,
        "valley_gully_carve_only_lowers_envelope": True,
        "source_relief_unmodified_beyond_distance_m": max(
            FAR_FIELD_CORRIDOR_ALIGNMENT_FADE_M,
            FAR_FIELD_VALLEY_GRADE_CAP_FADE_M,
            FAR_FIELD_UNDERLAY_FALLOFF_M,
        ),
        "procedural_infill_maximum_relief_m": FAR_FIELD_PROCEDURAL_INFILL_MAX_RELIEF_M,
        "procedural_domain_padding_m": FAR_FIELD_DOMAIN_PADDING_M,
        "authoritative_vertex_fraction": round(
            float(np.count_nonzero(source_count)) / source_count.size, 6
        ),
        "procedural_infill_explicit": True,
        "not_for_navigation": True,
    }
    return records, topology


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
    streaming_manifest = _load_json(
        repo_root / FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH
    )
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
    aerial_rgb, seam_count, aerial_exposure_normalization = _sample_naip_rgb(
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
    water, named_rapid_visual_sources = _water_products(
        repo_root,
        transit_manifest,
        streaming_manifest,
        stations_m,
    )
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
    far_field_patches, far_field_topology = _write_stitched_far_field_patches(
        repo_root, output_dir, geography_manifest, arrays, seed
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
        digest.update(patch["river_distance_to_route"]["sha256"].encode())

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
            "named_rapid_streaming_water": (
                FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH
            ),
            "boulder_catalog": PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH,
            "naip_source_window_count": len(
                geography_manifest["inputs"]["source_windows"]
            ),
        },
        "source_conditioning": {
            "aerial_exposure_normalization": aerial_exposure_normalization,
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
            "topology": far_field_topology,
            "grid_size": far_field_topology["global_grid_dimensions"],
            "macro_texture_size": FAR_FIELD_MACRO_SIZE,
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
            "water_field_composition": (
                "continuous transit seed with all validated cooked named-rapid fields "
                "smoothstep-blended over each runtime handoff distance"
            ),
            "water_aeration_authority": {
                "global_base": "legacy solver Froude threshold",
                "named_rapid_supplement": (
                    "solver surface slope plus acceleration, strain, and convergence"
                ),
                "guide_feature_supplement": (
                    "flow-scaled procedural ellipses from guide-interpreted named-rapid "
                    "hole, ledge, wave-train, lateral, rock, eddy, shallow, and "
                    "strainer feature records"
                ),
                "guide_feature_geometry_authority": (
                    "procedural_infill_interpreted_from_guide_inventory_pending_human_review"
                ),
                "supplement_scope": (
                    "validated named-rapid smoothstep handoff envelopes only"
                ),
                "shoreline_guard": "three-to-four adjacent wet solver cells",
                "presentation_only": True,
                "hydraulics_or_collision_changed": False,
            },
            "named_rapid_visual_window_count": len(named_rapid_visual_sources),
            "named_rapid_visual_sources": named_rapid_visual_sources,
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
                "shared-grid source-backed static-mesh tiles with a matched erosion-conditioned handoff around the detailed channel"
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
                patch["river_distance_to_route"],
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
