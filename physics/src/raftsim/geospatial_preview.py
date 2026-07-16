"""Small deterministic geospatial preview helpers for source-derived Unreal drapes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class BoundsWgs84:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


@dataclass(frozen=True)
class CopernicusTile:
    path: Path
    south_lat: int
    west_lon: int

    @property
    def north_lat(self) -> int:
        return self.south_lat + 1

    @property
    def east_lon(self) -> int:
        return self.west_lon + 1


def _load_float_tiff(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image, dtype=np.float32)


def _sample_tile_nearest(tile: CopernicusTile, data: np.ndarray, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    height, width = data.shape
    col = np.clip(((lon - tile.west_lon) / (tile.east_lon - tile.west_lon) * (width - 1)).round(), 0, width - 1)
    row = np.clip(((tile.north_lat - lat) / (tile.north_lat - tile.south_lat) * (height - 1)).round(), 0, height - 1)
    return data[row.astype(np.int32), col.astype(np.int32)]


def sample_copernicus_dem(
    southern_tile: CopernicusTile,
    northern_tile: CopernicusTile,
    bounds: BoundsWgs84,
    size: int,
) -> np.ndarray:
    """Sample the two Pacuare GLO-30 tiles into a small north-up preview grid."""

    south_data = _load_float_tiff(southern_tile.path)
    north_data = _load_float_tiff(northern_tile.path)

    xs = np.linspace(bounds.min_lon, bounds.max_lon, size, dtype=np.float32)
    ys = np.linspace(bounds.max_lat, bounds.min_lat, size, dtype=np.float32)
    lon, lat = np.meshgrid(xs, ys)

    sampled = np.empty((size, size), dtype=np.float32)
    north_mask = lat >= float(northern_tile.south_lat)
    sampled[north_mask] = _sample_tile_nearest(northern_tile, north_data, lon[north_mask], lat[north_mask])
    sampled[~north_mask] = _sample_tile_nearest(southern_tile, south_data, lon[~north_mask], lat[~north_mask])
    return sampled


def _normalized_relief(dem: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    finite = np.isfinite(dem)
    low, high = np.percentile(dem[finite], [2.0, 98.0])
    height = np.clip((dem - low) / max(1.0, high - low), 0.0, 1.0)

    grad_y, grad_x = np.gradient(dem)
    slope = np.sqrt(grad_x * grad_x + grad_y * grad_y)
    slope_high = np.percentile(slope[np.isfinite(slope)], 97.0)
    slope_norm = np.clip(slope / max(1.0, slope_high), 0.0, 1.0)

    light = np.clip(0.62 + (-grad_x * 0.0025) + (-grad_y * 0.0035), 0.32, 0.94)
    relief = np.clip(light * (0.82 + height * 0.24) - slope_norm * 0.10, 0.0, 1.0)
    return height, relief


def _manifest_path(path: Path, repo_root: Path | None) -> str:
    if repo_root is None:
        return str(path)
    return str(path.resolve().relative_to(repo_root.resolve()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _geojson_bbox(features: list[dict[str, object]]) -> list[float]:
    coordinates: list[tuple[float, float]] = []

    def collect(value: object) -> None:
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            coordinates.append((float(value[0]), float(value[1])))
            return
        if isinstance(value, list):
            for item in value:
                collect(item)

    for feature in features:
        geometry = feature.get("geometry", {})
        if isinstance(geometry, dict):
            collect(geometry.get("coordinates"))
    if not coordinates:
        return [0.0, 0.0, 0.0, 0.0]
    lons = [lon for lon, _lat in coordinates]
    lats = [lat for _lon, lat in coordinates]
    return [round(min(lons), 7), round(min(lats), 7), round(max(lons), 7), round(max(lats), 7)]


def _smoothstep(edge0: np.ndarray | float, edge1: np.ndarray | float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / np.maximum(1.0e-6, np.asarray(edge1) - np.asarray(edge0)), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _preview_channel_prior(
    output_size_px: int,
    river_half_width_cm: float,
    bend_amplitude_cm: float,
    corridor_half_width_cm: float,
) -> np.ndarray:
    min_x = -5600.0
    max_x = 26000.0
    xs = np.linspace(min_x, max_x, output_size_px, dtype=np.float32)
    ys = np.linspace(-corridor_half_width_cm, corridor_half_width_cm, output_size_px, dtype=np.float32)
    x, y = np.meshgrid(xs, ys)

    primary = np.sin((x + 3800.0) * 0.00043) * bend_amplitude_cm
    secondary = np.sin((x - 600.0) * 0.00019) * bend_amplitude_cm * 0.35
    center_y = primary + secondary
    offset = np.abs(y - center_y)
    return 1.0 - _smoothstep(river_half_width_cm * 0.82, river_half_width_cm + 260.0, offset)


def _preview_river_center_y_cm(x_cm: np.ndarray, bend_amplitude_cm: float) -> np.ndarray:
    primary = np.sin((x_cm + 3800.0) * 0.00043) * bend_amplitude_cm
    secondary = np.sin((x_cm - 600.0) * 0.00019) * bend_amplitude_cm * 0.35
    return primary + secondary


def _preview_world_to_wgs84(
    x_cm: float,
    y_cm: float,
    bounds: BoundsWgs84,
    min_x_cm: float,
    max_x_cm: float,
    corridor_half_width_cm: float,
) -> tuple[float, float]:
    u = (x_cm - min_x_cm) / (max_x_cm - min_x_cm)
    v = (y_cm + corridor_half_width_cm) / (2.0 * corridor_half_width_cm)
    lon = bounds.min_lon + u * (bounds.max_lon - bounds.min_lon)
    lat = bounds.max_lat - v * (bounds.max_lat - bounds.min_lat)
    return round(float(lon), 7), round(float(lat), 7)


def _preview_lon_lat_to_local_meters(lon: float, lat: float, origin_lon: float, origin_lat: float) -> tuple[float, float]:
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = meters_per_degree_lat * math.cos(math.radians(origin_lat))
    return (lon - origin_lon) * meters_per_degree_lon, (lat - origin_lat) * meters_per_degree_lat


def _preview_interpolate_scalar(stations: np.ndarray, values: np.ndarray, station_m: float) -> float:
    return float(np.interp(station_m, stations, values))


def build_pacuare_preview_centerline_scaffold(
    pacuare_root: Path,
    repo_root: Path | None = None,
    vertex_count: int = 129,
    station_interval_m: float = 250.0,
) -> dict[str, object]:
    """Write a review-gated Pacuare centerline scaffold from the Unreal preview curve."""

    bounds = BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12)
    min_x_cm = -5800.0
    max_x_cm = 26500.0
    corridor_half_width_cm = 2750.0
    bend_amplitude_cm = 340.0
    river_half_width_cm = 305.0 * 1.05

    hydro_root = pacuare_root / "hydrography/production_import_pilot"
    centerline_path = hydro_root / "preview_centerline_scaffold.geojson"
    stationing_path = hydro_root / "preview_stationing_scaffold.json"
    manifest_path = hydro_root / "preview_centerline_scaffold_manifest.json"
    hydro_root.mkdir(parents=True, exist_ok=True)

    xs_cm = np.linspace(min_x_cm, max_x_cm, vertex_count, dtype=np.float64)
    ys_cm = _preview_river_center_y_cm(xs_cm, bend_amplitude_cm)
    coordinates = [
        _preview_world_to_wgs84(
            float(x_cm),
            float(y_cm),
            bounds,
            min_x_cm,
            max_x_cm,
            corridor_half_width_cm,
        )
        for x_cm, y_cm in zip(xs_cm, ys_cm)
    ]
    origin_lon, origin_lat = coordinates[0]
    local_xy = np.asarray(
        [_preview_lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat) for lon, lat in coordinates],
        dtype=np.float64,
    )
    segment_lengths = np.linalg.norm(np.diff(local_xy, axis=0), axis=1)
    vertex_stations = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    total_length_m = float(vertex_stations[-1])
    sample_stations = list(np.arange(0.0, total_length_m, station_interval_m, dtype=np.float64))
    if not sample_stations or not math.isclose(float(sample_stations[-1]), total_length_m):
        sample_stations.append(total_length_m)

    lons = np.asarray([coordinate[0] for coordinate in coordinates], dtype=np.float64)
    lats = np.asarray([coordinate[1] for coordinate in coordinates], dtype=np.float64)
    station_samples = []
    for index, station_m in enumerate(sample_stations):
        lon = _preview_interpolate_scalar(vertex_stations, lons, float(station_m))
        lat = _preview_interpolate_scalar(vertex_stations, lats, float(station_m))
        preview_x_cm = _preview_interpolate_scalar(vertex_stations, xs_cm, float(station_m))
        preview_y_cm = _preview_interpolate_scalar(vertex_stations, ys_cm, float(station_m))
        lookahead_m = min(total_length_m, float(station_m) + 20.0)
        lookbehind_m = max(0.0, float(station_m) - 20.0)
        lon_a = _preview_interpolate_scalar(vertex_stations, lons, lookbehind_m)
        lat_a = _preview_interpolate_scalar(vertex_stations, lats, lookbehind_m)
        lon_b = _preview_interpolate_scalar(vertex_stations, lons, lookahead_m)
        lat_b = _preview_interpolate_scalar(vertex_stations, lats, lookahead_m)
        ax_m, ay_m = _preview_lon_lat_to_local_meters(lon_a, lat_a, origin_lon, origin_lat)
        bx_m, by_m = _preview_lon_lat_to_local_meters(lon_b, lat_b, origin_lon, origin_lat)
        tangent = np.asarray([bx_m - ax_m, by_m - ay_m], dtype=np.float64)
        norm = float(np.linalg.norm(tangent))
        if norm > 1.0e-9:
            tangent = tangent / norm
        normal_left = np.asarray([-tangent[1], tangent[0]], dtype=np.float64)
        station_samples.append(
            {
                "sample_index": index,
                "station_m": round(float(station_m), 3),
                "lon": round(float(lon), 7),
                "lat": round(float(lat), 7),
                "preview_world_x_cm": round(float(preview_x_cm), 3),
                "preview_world_y_cm": round(float(preview_y_cm), 3),
                "downstream_tangent_local_m": [round(float(tangent[0]), 6), round(float(tangent[1]), 6)],
                "river_left_normal_local_m": [round(float(normal_left[0]), 6), round(float(normal_left[1]), 6)],
            }
        )

    centerline = {
        "type": "FeatureCollection",
        "name": "pacuare_preview_centerline_scaffold",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "river_id": "pacuare",
                    "section_id": "lower_pacuare_planning_corridor",
                    "status": "preview_scaffold_from_unreal_curve_not_official_hydrography",
                    "source_curve": "RaftSimEditor GetPreviewRiverCenterY Pacuare preview parameters",
                    "stationing": "preview_stationing_scaffold.json",
                    "promotion_gate": "Replace with official Costa Rica hydrography, reviewed working CRS, imagery/DEM alignment, banks, rapid/access stationing, and guide/outfitter validation before production use.",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lon, lat in coordinates],
                },
            }
        ],
    }
    centerline_path.write_text(json.dumps(centerline, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    stationing = {
        "schema": "raftsim.pacuare_preview_stationing_scaffold.v1",
        "review_status": "preview_metric_stationing_review_required_not_final_crs_or_official_route",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "source_centerline": _manifest_path(centerline_path, repo_root),
        "local_transform": {
            "type": "linearized_wgs84_planning_bounds_plus_local_equirectangular_preview_meters",
            "origin_lon": origin_lon,
            "origin_lat": origin_lat,
            "bounds_wgs84": {
                "min_lon": bounds.min_lon,
                "min_lat": bounds.min_lat,
                "max_lon": bounds.max_lon,
                "max_lat": bounds.max_lat,
            },
            "limits": "This transform maps the Unreal preview curve into draft Pacuare planning bounds for editor scaffolding only; it is not a surveyed route or final Costa Rica CRS.",
        },
        "summary": {
            "vertex_count": vertex_count,
            "station_sample_count": len(station_samples),
            "station_sample_interval_m": station_interval_m,
            "preview_world_x_min_cm": min_x_cm,
            "preview_world_x_max_cm": max_x_cm,
            "preview_corridor_half_width_cm": corridor_half_width_cm,
            "preview_bend_amplitude_cm": bend_amplitude_cm,
            "preview_river_half_width_cm": round(river_half_width_cm, 3),
            "length_m_preview_wgs84_linearized": round(total_length_m, 3),
        },
        "station_samples": station_samples,
        "promotion_gate": [
            "replace route with official SNIT/IDECORI/MINAE/HydroSHEDS-reviewed hydrography",
            "select Costa Rica working CRS and record round-trip transform error",
            "align against cloud-screened imagery, conditioned DEM, banks, waterfalls, tributaries, and access points",
            "attach guide/outfitter stationing and rights-reviewed reference annotations",
        ],
    }
    stationing_path.write_text(json.dumps(stationing, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "raftsim.pacuare_preview_centerline_scaffold_manifest.v1",
        "status": "generated_review_gated_preview_route_not_official_hydrography",
        "river_id": "pacuare",
        "section_id": "lower_pacuare_planning_corridor",
        "generated_from": {
            "unreal_preview_curve": "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSurfaceSampling.cpp:GetPreviewRiverCenterY",
            "source_masks": "physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/water_mask_2048.png",
            "production_import_recipe": "physics/data/real_world/pacuare_river_costa_rica/production_import_pilot.json",
        },
        "outputs": {
            "centerline_geojson": _manifest_path(centerline_path, repo_root),
            "stationing_json": _manifest_path(stationing_path, repo_root),
        },
        "parameters": {
            "vertex_count": vertex_count,
            "station_interval_m": station_interval_m,
            "preview_world_x_min_cm": min_x_cm,
            "preview_world_x_max_cm": max_x_cm,
            "preview_corridor_half_width_cm": corridor_half_width_cm,
            "preview_bend_amplitude_cm": bend_amplitude_cm,
            "preview_river_half_width_cm": round(river_half_width_cm, 3),
            "bounds_wgs84": {
                "min_lon": bounds.min_lon,
                "min_lat": bounds.min_lat,
                "max_lon": bounds.max_lon,
                "max_lat": bounds.max_lat,
            },
        },
        "summary": {
            "centerline_vertex_count": vertex_count,
            "station_sample_count": len(station_samples),
            "length_m_preview_wgs84_linearized": round(total_length_m, 3),
            "first_station": station_samples[0],
            "last_station": station_samples[-1],
        },
        "output_checksums": {
            "centerline_geojson": {"sha256": _sha256(centerline_path)},
            "stationing_json": {"sha256": _sha256(stationing_path)},
        },
        "review_limits": [
            "The scaffold is useful for rapid/access annotation placement, procedural dressing, and current Unreal preview capture framing.",
            "It must not be promoted as authoritative Pacuare hydrography, bank geometry, wetted width, access stationing, or solver input.",
            "Future official hydrography, cloud-screened imagery, conditioned DEM, protected-area review, and guide/outfitter annotations must replace or validate it.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_source_imagery_masks(
    source_image_path: Path,
    output_water_mask_path: Path,
    output_vegetation_mask_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    source_description: str,
    repo_root: Path | None = None,
    output_size_px: int = 1024,
    preview_river_half_width_cm: float = 340.0,
    preview_bend_amplitude_cm: float = 300.0,
    preview_corridor_half_width_cm: float = 2750.0,
) -> None:
    """Build review-gated source-assisted water and vegetation masks for Unreal preview dressing."""

    with Image.open(source_image_path) as image:
        source = image.convert("RGBA").resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    rgba = np.asarray(source, dtype=np.float32) / 255.0
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    brightness = rgb.mean(axis=2)
    channel_range = rgb.max(axis=2) - rgb.min(axis=2)

    cloud_or_snow = (brightness > 0.78) & (channel_range < 0.12)
    excess_green = np.clip(2.0 * green - red - blue, 0.0, 1.0)
    green_dominance = np.clip(green - np.maximum(red, blue), 0.0, 1.0)
    vegetation = np.clip(excess_green * 1.85 + green_dominance * 2.20 + (green - brightness) * 1.10, 0.0, 1.0)

    blue_green = np.clip((blue + green) * 0.5 - red, 0.0, 1.0)
    muted_smooth = np.clip(0.42 - channel_range, 0.0, 1.0) * np.clip(0.70 - brightness, 0.0, 1.0)
    color_water = np.clip(blue_green * 2.00 + muted_smooth * 1.35, 0.0, 1.0)
    channel_prior = _preview_channel_prior(
        output_size_px,
        preview_river_half_width_cm,
        preview_bend_amplitude_cm,
        preview_corridor_half_width_cm,
    )

    water = np.clip(np.maximum(color_water, channel_prior * 0.78) * alpha, 0.0, 1.0)
    vegetation = np.clip(vegetation * (1.0 - channel_prior * 0.82) * alpha, 0.0, 1.0)
    water = np.where(cloud_or_snow, channel_prior * 0.50, water)
    vegetation = np.where(cloud_or_snow, vegetation * 0.35, vegetation)

    output_water_mask_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(water * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_water_mask_path)
    Image.fromarray(np.clip(vegetation * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_vegetation_mask_path)

    manifest = {
        "schema": "raftsim.source_imagery_masks.v1",
        "status": "generated_review_gated_preview_masks_not_final_segmentation",
        "source_id": source_id,
        "provider": provider,
        "source_description": source_description,
        "input_image": _manifest_path(source_image_path, repo_root),
        "outputs": {
            "water_mask": _manifest_path(output_water_mask_path, repo_root),
            "vegetation_mask": _manifest_path(output_vegetation_mask_path, repo_root),
        },
        "processing": {
            "output_size_px": output_size_px,
            "water_features": [
                "visible_color_blue_green_or_muted_smooth_water_likelihood",
                "bounded_preview_channel_prior_matching_generated_unreal_preview_geometry",
            ],
            "vegetation_features": [
                "visible_green_excess",
                "green_channel_dominance",
                "channel_prior_suppression",
            ],
            "cloud_or_snow_filter": "brightness > 0.78 and channel range < 0.12 reduces mask confidence",
            "coverage": {
                "water_mean": float(np.mean(water)),
                "vegetation_mean": float(np.mean(vegetation)),
                "cloud_or_snow_fraction": float(np.mean(cloud_or_snow)),
            },
        },
        "caveats": [
            "Masks are deterministic source-assisted preview inputs, not production water or vegetation segmentation.",
            "The water mask uses a bounded preview channel prior so the generated Unreal review map can consume the mask before final hydrography and hand-reviewed bank polygons are available.",
            "Production masks still require reviewed orthomosaics or satellite scenes, hydrography/bank alignment, cloud/shadow review, and guide/geospatial approval.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_dem_relief_preview(
    dem_path: Path,
    output_relief_png_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    repo_root: Path | None = None,
    output_size_px: int = 512,
) -> None:
    dem = _load_float_tiff(dem_path)
    _, relief = _normalized_relief(dem)
    relief_image = Image.fromarray(np.clip(relief * 255.0, 0, 255).astype(np.uint8), mode="L")
    relief_image = relief_image.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)

    output_relief_png_path.parent.mkdir(parents=True, exist_ok=True)
    relief_image.save(output_relief_png_path)

    manifest = {
        "schema": "raftsim.dem_relief_preview.v1",
        "status": "generated_preview_only_not_production_heightfield",
        "source_id": source_id,
        "provider": provider,
        "input_dem": _manifest_path(dem_path, repo_root),
        "output_relief": _manifest_path(output_relief_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "height_percentiles": "2_to_98",
            "relief": "slope_aware_normalized_grayscale_preview",
        },
        "caveats": [
            "Preview relief is sampled into procedural geometry only.",
            "Full terrain import still requires clipping, reprojection, conditioning, and Unreal heightfield or landscape import.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_single_dem_heightfield_candidate(
    dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    source_description: str,
    repo_root: Path | None = None,
    output_size_px: int = 1009,
) -> None:
    """Export a review-gated 16-bit DEM sample for Unreal Landscape import tests."""

    dem = _load_float_tiff(dem_path)
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError(f"DEM sample contains no finite elevations: {dem_path}")

    fill_value = float(np.median(dem[finite]))
    dem = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(dem))
    elevation_max_m = float(np.max(dem))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((dem - elevation_min_m) / elevation_span_m, 0.0, 1.0)

    source_image = Image.fromarray(np.round(normalized * 65535.0).astype(np.uint16))
    heightfield_image = source_image.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    heightfield_image.save(output_png_path)

    manifest = {
        "schema": "raftsim.heightfield_candidate.v1",
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "source_id": source_id,
        "provider": provider,
        "source_description": source_description,
        "input_dem": _manifest_path(dem_path, repo_root),
        "output_heightfield_png": _manifest_path(output_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
            "normalization": "input DEM min/max mapped linearly to 0..65535 before resizing",
            "resize": "bilinear_to_unreal_landscape_test_size",
            "unreal_import_note": "Use the recorded elevation min/max and chosen vertical scale when testing Landscape import.",
        },
        "caveats": [
            "This is an import candidate for tool testing, not a production Unreal heightfield.",
            "The source DEM sample is not a complete reviewed corridor DEM, and still needs clipping, reprojection, void/artifact review, hydrologic conditioning, and alignment to reviewed river geometry.",
            "River channel burning, bank breaklines, boulder/bed features, access constraints, and guide review are still required before photoreal terrain promotion.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _pilot_tile_id(tile_prefix: str, row: int, column: int) -> str:
    return f"{tile_prefix}_tile_r{row}_c{column}"


def _stitch_image_tiles(
    tile_dir: Path,
    tile_prefix: str,
    extension: str,
    rows: int,
    columns: int,
    convert_mode: str,
    output_size_px: int,
) -> tuple[Image.Image, list[Path]]:
    inputs: list[Path] = []
    opened: dict[tuple[int, int], Image.Image] = {}
    for row in range(rows):
        for column in range(columns):
            path = tile_dir / f"{_pilot_tile_id(tile_prefix, row, column)}.{extension}"
            inputs.append(path)
            opened[(row, column)] = Image.open(path).convert(convert_mode)

    tile_width, tile_height = opened[(0, 0)].size
    mosaic = Image.new(convert_mode, (columns * tile_width, rows * tile_height))
    for row in range(rows):
        for column in range(columns):
            # Row zero is the southern tile band; north-up image mosaics place it at the bottom.
            mosaic.paste(opened[(row, column)], (column * tile_width, (rows - 1 - row) * tile_height))

    if mosaic.size != (output_size_px, output_size_px):
        mosaic = mosaic.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    return mosaic, inputs


def _stitch_float_dem_tiles(tile_dir: Path, tile_prefix: str, rows: int, columns: int) -> tuple[np.ndarray, list[Path]]:
    inputs: list[Path] = []
    arrays: dict[tuple[int, int], np.ndarray] = {}
    for row in range(rows):
        for column in range(columns):
            path = tile_dir / f"{_pilot_tile_id(tile_prefix, row, column)}.tif"
            inputs.append(path)
            arrays[(row, column)] = _load_float_tiff(path)

    tile_height, tile_width = arrays[(0, 0)].shape
    mosaic = np.empty((rows * tile_height, columns * tile_width), dtype=np.float32)
    for row in range(rows):
        for column in range(columns):
            y0 = (rows - 1 - row) * tile_height
            x0 = column * tile_width
            mosaic[y0 : y0 + tile_height, x0 : x0 + tile_width] = arrays[(row, column)]
    return mosaic, inputs


def _write_heightfield_from_dem(
    dem: np.ndarray,
    output_png_path: Path,
    output_size_px: int,
) -> tuple[float, float]:
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError("DEM mosaic contains no finite elevations")
    fill_value = float(np.median(dem[finite]))
    filled = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(filled))
    elevation_max_m = float(np.max(filled))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((filled - elevation_min_m) / elevation_span_m, 0.0, 1.0)
    heightfield = Image.fromarray(np.round(normalized * 65535.0).astype(np.uint16))
    heightfield = heightfield.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    heightfield.save(output_png_path)
    return elevation_min_m, elevation_max_m


def _build_import_pilot_derivatives(
    river_root: Path,
    *,
    tile_prefix: str,
    schema: str,
    source_id: str,
    source_description: str,
    preview_river_half_width_cm: float,
    preview_bend_amplitude_cm: float,
    preview_corridor_half_width_cm: float,
    review_role: str,
    repo_root: Path | None = None,
    source_drape_size_px: int = 4096,
    relief_size_px: int = 2048,
    heightfield_size_px: int = 2017,
    mask_size_px: int = 2048,
) -> None:
    """Stitch downloaded pilot tiles into review-gated preview derivatives."""

    rows = 2
    columns = 2
    imagery_root = river_root / "imagery/production_import_pilot"
    terrain_root = river_root / "terrain/production_import_pilot"
    source_drape_path = imagery_root / f"source_drape_{source_drape_size_px}.png"
    relief_path = terrain_root / f"dem_relief_{relief_size_px}.png"
    heightfield_path = terrain_root / f"heightfield_candidate_{heightfield_size_px}.png"
    water_mask_path = imagery_root / f"water_mask_{mask_size_px}.png"
    vegetation_mask_path = imagery_root / f"vegetation_mask_{mask_size_px}.png"
    mask_manifest_path = imagery_root / "source_masks_manifest.json"
    derivative_manifest_path = river_root / "production_import_pilot_derivatives_manifest.json"

    source_drape, imagery_inputs = _stitch_image_tiles(
        imagery_root / "naip_tiles",
        tile_prefix,
        "png",
        rows,
        columns,
        "RGB",
        source_drape_size_px,
    )
    source_drape_path.parent.mkdir(parents=True, exist_ok=True)
    source_drape.save(source_drape_path)

    dem_mosaic, dem_inputs = _stitch_float_dem_tiles(terrain_root / "3dep_tiles", tile_prefix, rows, columns)
    _, relief = _normalized_relief(dem_mosaic)
    relief_image = Image.fromarray(np.clip(relief * 255.0, 0, 255).astype(np.uint8), mode="L")
    if relief_image.size != (relief_size_px, relief_size_px):
        relief_image = relief_image.resize((relief_size_px, relief_size_px), Image.Resampling.BILINEAR)
    relief_path.parent.mkdir(parents=True, exist_ok=True)
    relief_image.save(relief_path)
    elevation_min_m, elevation_max_m = _write_heightfield_from_dem(dem_mosaic, heightfield_path, heightfield_size_px)

    build_source_imagery_masks(
        source_image_path=source_drape_path,
        output_water_mask_path=water_mask_path,
        output_vegetation_mask_path=vegetation_mask_path,
        output_manifest_path=mask_manifest_path,
        source_id=source_id,
        provider="USDA/APFO NAIP ImageServer",
        source_description=source_description,
        repo_root=repo_root,
        output_size_px=mask_size_px,
        preview_river_half_width_cm=preview_river_half_width_cm,
        preview_bend_amplitude_cm=preview_bend_amplitude_cm,
        preview_corridor_half_width_cm=preview_corridor_half_width_cm,
    )

    manifest = {
        "schema": schema,
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "source_recipe": _manifest_path(river_root / "production_import_pilot.json", repo_root),
        "source_pull_manifest": _manifest_path(river_root / "production_import_pilot_pull_manifest.json", repo_root),
        "inputs": {
            "naip_tiles": [_manifest_path(path, repo_root) for path in imagery_inputs],
            "dem_tiles": [_manifest_path(path, repo_root) for path in dem_inputs],
        },
        "outputs": {
            "source_drape": _manifest_path(source_drape_path, repo_root),
            "dem_relief": _manifest_path(relief_path, repo_root),
            "heightfield_candidate": _manifest_path(heightfield_path, repo_root),
            "water_mask": _manifest_path(water_mask_path, repo_root),
            "vegetation_mask": _manifest_path(vegetation_mask_path, repo_root),
            "mask_manifest": _manifest_path(mask_manifest_path, repo_root),
        },
        "processing": {
            "tile_grid": {"rows": rows, "columns": columns},
            "north_up_mosaic": "pilot tile row 1 is placed above row 0",
            "source_drape_size_px": source_drape_size_px,
            "relief_size_px": relief_size_px,
            "heightfield_size_px": heightfield_size_px,
            "mask_size_px": mask_size_px,
            "heightfield_pixel_format": "16_bit_grayscale_png",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
        },
        "caveats": [
            "This is a stitched derivative of the official-service pilot tiles, not final photoreal terrain.",
            f"The DEM mosaic is not yet reprojected to a selected working CRS, hydrologically conditioned, channel-burned, or {review_role} reviewed.",
            f"The source masks are preview segmentation aids and must be reviewed against hydrography, bank polygons, seasonal imagery, and {review_role} feedback before production use.",
        ],
    }
    derivative_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_south_fork_import_pilot_derivatives(
    south_fork_root: Path,
    repo_root: Path | None = None,
    source_drape_size_px: int = 4096,
    relief_size_px: int = 2048,
    heightfield_size_px: int = 2017,
    mask_size_px: int = 2048,
) -> None:
    """Stitch downloaded South Fork pilot tiles into review-gated preview derivatives."""

    _build_import_pilot_derivatives(
        south_fork_root,
        tile_prefix="sfa_chili_bar",
        schema="raftsim.south_fork_import_pilot_derivatives.v1",
        source_id=f"south_fork_production_import_pilot_source_drape_{source_drape_size_px}",
        source_description="South Fork American stitched 2x2 pilot NAIP source drape generated from official service export tiles.",
        preview_river_half_width_cm=335.0,
        preview_bend_amplitude_cm=290.0,
        preview_corridor_half_width_cm=2750.0,
        review_role="guide",
        repo_root=repo_root,
        source_drape_size_px=source_drape_size_px,
        relief_size_px=relief_size_px,
        heightfield_size_px=heightfield_size_px,
        mask_size_px=mask_size_px,
    )


def build_south_fork_production_hydrography_drafts(south_fork_root: Path, repo_root: Path | None = None) -> None:
    """Promote South Fork NHD review seeds into draft production-import hydrography artifacts."""

    hydro_root = south_fork_root / "hydrography"
    output_root = hydro_root / "production_import_pilot"
    output_root.mkdir(parents=True, exist_ok=True)

    stationing_path = hydro_root / "nhd_hu8_18020129_mainstem_stationing_candidate.json"
    cross_section_seed_path = hydro_root / "nhd_hu8_18020129_cross_section_seed_candidates.geojson"
    mainstem_manifest_path = hydro_root / "nhd_hu8_18020129_mainstem_candidate_manifest.json"
    alignment_diagnostic_path = hydro_root / "nhd_hu8_18020129_naip_dem_alignment_diagnostic.json"
    water_prior_manifest_path = south_fork_root / "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json"

    stationing = json.loads(stationing_path.read_text(encoding="utf-8"))
    cross_section_seeds = json.loads(cross_section_seed_path.read_text(encoding="utf-8"))
    mainstem_manifest = json.loads(mainstem_manifest_path.read_text(encoding="utf-8"))
    vertices = stationing["vertices"]
    station_samples = stationing["station_samples"]
    seed_features = cross_section_seeds["features"]

    centerline_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[vertex["lon"], vertex["lat"]] for vertex in vertices],
        },
        "properties": {
            "river_id": "american_south_fork",
            "section_id": "chili_bar_to_coloma",
            "source": "nhd_hu8_18020129_mainstem_stationing_candidate",
            "status": "draft_from_nhd_mainstem_candidate_review_gated_not_final_centerline",
            "station_axis": stationing["local_transform"]["station_axis"],
            "length_m_preview": stationing["summary"]["length_m_geodesic_vertices"],
            "source_length_km_nhd_sum": stationing["summary"]["source_length_km_nhd_sum"],
            "vertex_count": stationing["summary"]["vertex_count"],
            "station_sample_count": stationing["summary"]["station_sample_count"],
            "promotion_gate": (
                "Confirm flow direction, working CRS, NAIP/DEM alignment, bank offsets, rapid/access stationing, "
                "and guide review before solver, Unreal, or gameplay authority."
            ),
        },
    }
    centerline = {
        "type": "FeatureCollection",
        "name": "south_fork_american_production_import_centerline_draft",
        "bbox": _geojson_bbox([centerline_feature]),
        "properties": {
            "schema": "raftsim.south_fork_production_hydrography_drafts.centerline.v1",
            "generated_on": "2026-07-06",
            "review_status": "draft_review_required_not_final_centerline",
            "source_stationing": _manifest_path(stationing_path, repo_root),
        },
        "features": [centerline_feature],
    }

    left_bank_coordinates = [feature["geometry"]["coordinates"][0] for feature in seed_features]
    right_bank_coordinates = [feature["geometry"]["coordinates"][-1] for feature in seed_features]
    bank_features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": left_bank_coordinates},
            "properties": {
                "bank_id": "draft_left_bank_offset_from_cross_section_seeds",
                "side": "river_left",
                "status": "draft_offset_line_not_reviewed_bank",
                "source": "nhd_cross_section_seed_endpoints",
                "offset_m_from_centerline": seed_features[0]["properties"]["half_width_m"],
                "station_start_m": station_samples[0]["station_m"],
                "station_end_m": station_samples[-1]["station_m"],
                "promotion_gate": "Replace with NAIP/DEM/field-reviewed banks, shelves, side channels, and seasonal wetted widths.",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": right_bank_coordinates},
            "properties": {
                "bank_id": "draft_right_bank_offset_from_cross_section_seeds",
                "side": "river_right",
                "status": "draft_offset_line_not_reviewed_bank",
                "source": "nhd_cross_section_seed_endpoints",
                "offset_m_from_centerline": seed_features[0]["properties"]["half_width_m"],
                "station_start_m": station_samples[0]["station_m"],
                "station_end_m": station_samples[-1]["station_m"],
                "promotion_gate": "Replace with NAIP/DEM/field-reviewed banks, shelves, side channels, and seasonal wetted widths.",
            },
        },
    ]
    banks = {
        "type": "FeatureCollection",
        "name": "south_fork_american_production_import_bank_offset_drafts",
        "bbox": _geojson_bbox(bank_features),
        "properties": {
            "schema": "raftsim.south_fork_production_hydrography_drafts.banks.v1",
            "generated_on": "2026-07-06",
            "review_status": "offset_lines_review_required_not_banks_or_wetted_width",
            "source_cross_sections": _manifest_path(cross_section_seed_path, repo_root),
            "feature_count": len(bank_features),
        },
        "features": bank_features,
    }

    cross_section_features = []
    for feature in seed_features:
        properties = {
            **feature["properties"],
            "status": "draft_production_import_cross_section_review_line_not_solver_section",
            "source": "nhd_hu8_18020129_cross_section_seed_candidates",
            "promotion_gate": (
                "Review against NAIP, DEM relief, water prior, guide notes, shelves, side channels, and seasonal flow "
                "before accepting as a production cross section."
            ),
        }
        cross_section_features.append({**feature, "properties": properties})
    cross_sections = {
        "type": "FeatureCollection",
        "name": "south_fork_american_production_import_cross_section_drafts",
        "bbox": _geojson_bbox(cross_section_features),
        "properties": {
            "schema": "raftsim.south_fork_production_hydrography_drafts.cross_sections.v1",
            "generated_on": "2026-07-06",
            "review_status": "draft_review_lines_not_solver_cross_sections",
            "source_cross_sections": _manifest_path(cross_section_seed_path, repo_root),
            "feature_count": len(cross_section_features),
        },
        "features": cross_section_features,
    }

    centerline_path = output_root / "centerline.geojson"
    banks_path = output_root / "banks.geojson"
    cross_sections_path = output_root / "cross_sections.geojson"
    manifest_path = output_root / "hydrography_draft_manifest.json"

    centerline_path.write_text(json.dumps(centerline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    banks_path.write_text(json.dumps(banks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cross_sections_path.write_text(json.dumps(cross_sections, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "raftsim.south_fork_production_hydrography_drafts.manifest.v1",
        "generated_on": "2026-07-06",
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
        "status": "draft_hydrography_artifacts_generated_review_required_not_production_authority",
        "inputs": {
            "stationing": _manifest_path(stationing_path, repo_root),
            "cross_section_seeds": _manifest_path(cross_section_seed_path, repo_root),
            "mainstem_manifest": _manifest_path(mainstem_manifest_path, repo_root),
            "alignment_diagnostic": _manifest_path(alignment_diagnostic_path, repo_root),
            "water_prior_manifest": _manifest_path(water_prior_manifest_path, repo_root),
        },
        "outputs": {
            "centerline": _manifest_path(centerline_path, repo_root),
            "banks": _manifest_path(banks_path, repo_root),
            "cross_sections": _manifest_path(cross_sections_path, repo_root),
        },
        "summary": {
            "centerline_vertex_count": len(vertices),
            "centerline_station_sample_count": len(station_samples),
            "cross_section_count": len(cross_section_features),
            "bank_offset_line_count": len(bank_features),
            "length_m_preview": stationing["summary"]["length_m_geodesic_vertices"],
            "mainstem_orientation": mainstem_manifest["derivation"]["orientation"],
        },
        "review_gates": [
            "Confirm the NHD-derived centerline direction, station zero, and working CRS.",
            "Edit banks against NAIP, DEM relief, water prior masks, field observations, side channels, shelves, and guide notes.",
            "Reject or repair out-of-bounds/low-water cross-section centers before solver grid generation.",
            "Attach guide-reviewed rapid, eddy, access, and rescue annotations before gameplay or Unreal production authority.",
        ],
        "output_checksums": {
            "centerline": {"sha256": _sha256(centerline_path)},
            "banks": {"sha256": _sha256(banks_path)},
            "cross_sections": {"sha256": _sha256(cross_sections_path)},
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_colorado_production_hydrography_drafts(colorado_root: Path, repo_root: Path | None = None) -> None:
    """Promote Colorado/Lees Ferry NHD review seeds into draft production-import hydrography artifacts."""

    hydro_root = colorado_root / "hydrography"
    output_root = hydro_root / "production_import_pilot"
    output_root.mkdir(parents=True, exist_ok=True)

    stationing_path = hydro_root / "nhd_hu8_lees_ferry_mainstem_stationing_candidate.json"
    cross_section_seed_path = hydro_root / "nhd_hu8_lees_ferry_cross_section_seed_candidates.geojson"
    mainstem_manifest_path = hydro_root / "nhd_hu8_lees_ferry_mainstem_candidate_manifest.json"
    alignment_diagnostic_path = hydro_root / "nhd_hu8_lees_ferry_naip_dem_alignment_diagnostic.json"
    water_prior_manifest_path = colorado_root / "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json"

    stationing = json.loads(stationing_path.read_text(encoding="utf-8"))
    cross_section_seeds = json.loads(cross_section_seed_path.read_text(encoding="utf-8"))
    mainstem_manifest = json.loads(mainstem_manifest_path.read_text(encoding="utf-8"))
    vertices = stationing["vertices"]
    station_samples = stationing["station_samples"]
    seed_features = cross_section_seeds["features"]

    centerline_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[vertex["lon"], vertex["lat"]] for vertex in vertices],
        },
        "properties": {
            "river_id": "colorado_river",
            "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
            "source": "nhd_hu8_lees_ferry_mainstem_stationing_candidate",
            "status": "draft_from_nhd_mainstem_candidate_review_gated_not_final_centerline",
            "station_axis": stationing["local_transform"]["station_axis"],
            "length_m_preview": stationing["summary"]["length_m_geodesic_vertices"],
            "source_length_km_nhd_sum": stationing["summary"]["source_length_km_nhd_sum"],
            "vertex_count": stationing["summary"]["vertex_count"],
            "station_sample_count": stationing["summary"]["station_sample_count"],
            "promotion_gate": (
                "Confirm river-mile relation, canyon working CRS, visible water-edge alignment, accepted banks, "
                "release-aware sandbars, eddies, camps/access sensitivity, and oarsman review before solver, "
                "Unreal, or gameplay authority."
            ),
        },
    }
    centerline = {
        "type": "FeatureCollection",
        "name": "colorado_lees_ferry_production_import_centerline_draft",
        "bbox": _geojson_bbox([centerline_feature]),
        "properties": {
            "schema": "raftsim.colorado_production_hydrography_drafts.centerline.v1",
            "generated_on": "2026-07-06",
            "review_status": "draft_review_required_not_final_centerline_or_river_miles",
            "source_stationing": _manifest_path(stationing_path, repo_root),
        },
        "features": [centerline_feature],
    }

    left_bank_coordinates = [feature["geometry"]["coordinates"][0] for feature in seed_features]
    right_bank_coordinates = [feature["geometry"]["coordinates"][-1] for feature in seed_features]
    bank_features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": left_bank_coordinates},
            "properties": {
                "bank_id": "draft_left_bank_offset_from_cross_section_seeds",
                "side": "river_left",
                "status": "draft_offset_line_not_reviewed_bank",
                "source": "nhd_cross_section_seed_endpoints",
                "offset_m_from_centerline": seed_features[0]["properties"]["half_width_m"],
                "station_start_m": station_samples[0]["station_m"],
                "station_end_m": station_samples[-1]["station_m"],
                "promotion_gate": (
                    "Replace with NAIP/DEM/release/oarsman-reviewed banks, shelves, sandbars, side channels, "
                    "and release-dependent wetted widths."
                ),
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": right_bank_coordinates},
            "properties": {
                "bank_id": "draft_right_bank_offset_from_cross_section_seeds",
                "side": "river_right",
                "status": "draft_offset_line_not_reviewed_bank",
                "source": "nhd_cross_section_seed_endpoints",
                "offset_m_from_centerline": seed_features[0]["properties"]["half_width_m"],
                "station_start_m": station_samples[0]["station_m"],
                "station_end_m": station_samples[-1]["station_m"],
                "promotion_gate": (
                    "Replace with NAIP/DEM/release/oarsman-reviewed banks, shelves, sandbars, side channels, "
                    "and release-dependent wetted widths."
                ),
            },
        },
    ]
    banks = {
        "type": "FeatureCollection",
        "name": "colorado_lees_ferry_production_import_bank_offset_drafts",
        "bbox": _geojson_bbox(bank_features),
        "properties": {
            "schema": "raftsim.colorado_production_hydrography_drafts.banks.v1",
            "generated_on": "2026-07-06",
            "review_status": "offset_lines_review_required_not_banks_sandbars_or_wetted_width",
            "source_cross_sections": _manifest_path(cross_section_seed_path, repo_root),
            "feature_count": len(bank_features),
        },
        "features": bank_features,
    }

    cross_section_features = []
    for feature in seed_features:
        properties = {
            **feature["properties"],
            "status": "draft_production_import_cross_section_review_line_not_solver_section",
            "source": "nhd_hu8_lees_ferry_cross_section_seed_candidates",
            "promotion_gate": (
                "Review against NAIP, DEM relief, water prior, release context, oarsman notes, sandbars, side channels, "
                "and seasonal/release flow before accepting as a production cross section."
            ),
        }
        cross_section_features.append({**feature, "properties": properties})
    cross_sections = {
        "type": "FeatureCollection",
        "name": "colorado_lees_ferry_production_import_cross_section_drafts",
        "bbox": _geojson_bbox(cross_section_features),
        "properties": {
            "schema": "raftsim.colorado_production_hydrography_drafts.cross_sections.v1",
            "generated_on": "2026-07-06",
            "review_status": "draft_review_lines_not_solver_cross_sections_or_sandbar_boundaries",
            "source_cross_sections": _manifest_path(cross_section_seed_path, repo_root),
            "feature_count": len(cross_section_features),
        },
        "features": cross_section_features,
    }

    centerline_path = output_root / "centerline.geojson"
    banks_path = output_root / "banks.geojson"
    cross_sections_path = output_root / "cross_sections.geojson"
    manifest_path = output_root / "hydrography_draft_manifest.json"

    centerline_path.write_text(json.dumps(centerline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    banks_path.write_text(json.dumps(banks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cross_sections_path.write_text(json.dumps(cross_sections, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = mainstem_manifest["summary"]
    manifest = {
        "schema": "raftsim.colorado_production_hydrography_drafts.manifest.v1",
        "generated_on": "2026-07-06",
        "river_id": "colorado_river",
        "section_id": "grand_canyon_lees_ferry_to_diamond_creek",
        "status": "draft_hydrography_artifacts_generated_review_required_not_production_authority",
        "inputs": {
            "stationing": _manifest_path(stationing_path, repo_root),
            "cross_section_seeds": _manifest_path(cross_section_seed_path, repo_root),
            "mainstem_manifest": _manifest_path(mainstem_manifest_path, repo_root),
            "alignment_diagnostic": _manifest_path(alignment_diagnostic_path, repo_root),
            "water_prior_manifest": _manifest_path(water_prior_manifest_path, repo_root),
        },
        "outputs": {
            "centerline": _manifest_path(centerline_path, repo_root),
            "banks": _manifest_path(banks_path, repo_root),
            "cross_sections": _manifest_path(cross_sections_path, repo_root),
        },
        "summary": {
            "centerline_vertex_count": len(vertices),
            "centerline_station_sample_count": len(station_samples),
            "cross_section_count": len(cross_section_features),
            "bank_offset_line_count": len(bank_features),
            "length_m_preview": stationing["summary"]["length_m_geodesic_vertices"],
            "source_length_km_nhd_sum": summary["source_length_km_sum"],
            "mainstem_orientation": "upstream_endpoint_to_downstream_endpoint_from_exact_graph_review",
            "upstream_endpoint_wgs84": summary["upstream_endpoint_lonlat"],
            "downstream_endpoint_wgs84": summary["downstream_endpoint_lonlat"],
        },
        "review_gates": [
            "Confirm the NHD-derived centerline direction, station zero, canyon working CRS, and river-mile relation.",
            "Edit banks against NAIP, DEM relief, water prior masks, release-band exposure, sandbars, eddies, camps/access sensitivity, and oarsman notes.",
            "Reject or repair out-of-bounds/low-water cross-section centers before solver grid generation.",
            "Attach river-mile, sandbar, eddy, access, rescue, and oar-line annotations before gameplay or Unreal production authority.",
        ],
        "output_checksums": {
            "centerline": {"sha256": _sha256(centerline_path)},
            "banks": {"sha256": _sha256(banks_path)},
            "cross_sections": {"sha256": _sha256(cross_sections_path)},
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_colorado_import_pilot_derivatives(
    colorado_root: Path,
    repo_root: Path | None = None,
    source_drape_size_px: int = 4096,
    relief_size_px: int = 2048,
    heightfield_size_px: int = 2017,
    mask_size_px: int = 2048,
) -> None:
    """Stitch downloaded Colorado/Lees Ferry pilot tiles into review-gated preview derivatives."""

    _build_import_pilot_derivatives(
        colorado_root,
        tile_prefix="colorado_lees_ferry",
        schema="raftsim.colorado_import_pilot_derivatives.v1",
        source_id=f"colorado_production_import_pilot_source_drape_{source_drape_size_px}",
        source_description="Colorado River Lees Ferry stitched 2x2 pilot NAIP source drape generated from official service export tiles.",
        preview_river_half_width_cm=520.0 * 1.08,
        preview_bend_amplitude_cm=360.0,
        preview_corridor_half_width_cm=4300.0,
        review_role="guide/oarsman",
        repo_root=repo_root,
        source_drape_size_px=source_drape_size_px,
        relief_size_px=relief_size_px,
        heightfield_size_px=heightfield_size_px,
        mask_size_px=mask_size_px,
    )


def build_pacuare_demshade_drape(
    nasa_truecolor_path: Path,
    southern_dem_path: Path,
    northern_dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    output_relief_png_path: Path,
    bounds: BoundsWgs84,
    selected_date: str,
    repo_root: Path | None = None,
    output_size_px: int = 512,
    relief_size_px: int | None = None,
) -> None:
    """Blend NASA true color with DEM-derived rainforest relief for preview-only draping."""

    with Image.open(nasa_truecolor_path) as image:
        source = image.convert("RGBA").resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    source_rgb = np.asarray(source, dtype=np.float32)[..., :3] / 255.0
    source_alpha = np.asarray(source, dtype=np.float32)[..., 3:4] / 255.0

    dem = sample_copernicus_dem(
        CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
        CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
        bounds,
        output_size_px,
    )
    height, relief = _normalized_relief(dem)

    brightness = source_rgb.mean(axis=2)
    color_range = source_rgb.max(axis=2) - source_rgb.min(axis=2)
    cloud_mask = (brightness > 0.70) & (color_range < 0.16)

    forest_low = np.array([0.05, 0.20, 0.08], dtype=np.float32)
    forest_high = np.array([0.20, 0.36, 0.13], dtype=np.float32)
    forest = forest_low + (forest_high - forest_low) * relief[..., None]
    ridge_warmth = np.array([0.09, 0.06, 0.02], dtype=np.float32) * height[..., None]
    dem_rgb = np.clip(forest + ridge_warmth, 0.0, 1.0)

    non_cloud = np.clip(source_rgb * 0.45 + dem_rgb * 0.55, 0.0, 1.0)
    blended = np.where(cloud_mask[..., None], dem_rgb, non_cloud)
    rgba = np.dstack((blended, source_alpha))

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(rgba * 255.0, 0, 255).astype(np.uint8), mode="RGBA").save(output_png_path)
    relief_output_size_px = relief_size_px or output_size_px
    if relief_output_size_px == output_size_px:
        relief_output = relief
    else:
        relief_dem = sample_copernicus_dem(
            CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
            CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
            bounds,
            relief_output_size_px,
        )
        _, relief_output = _normalized_relief(relief_dem)
    output_relief_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(relief_output * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_relief_png_path)

    manifest = {
        "schema": "raftsim.pacuare_source_drape_composite.v1",
        "status": "generated_preview_only_not_production_photoreal",
        "bounds_wgs84": {
            "min_lon": bounds.min_lon,
            "min_lat": bounds.min_lat,
            "max_lon": bounds.max_lon,
            "max_lat": bounds.max_lat,
        },
        "inputs": {
            "nasa_gibs_truecolor": _manifest_path(nasa_truecolor_path, repo_root),
            "nasa_gibs_selected_date": selected_date,
            "copernicus_dem_glo30_southern_tile": _manifest_path(southern_dem_path, repo_root),
            "copernicus_dem_glo30_northern_tile": _manifest_path(northern_dem_path, repo_root),
        },
        "output": _manifest_path(output_png_path, repo_root),
        "terrain_relief_output": _manifest_path(output_relief_png_path, repo_root),
        "processing": {
            "size_px": output_size_px,
            "relief_size_px": relief_output_size_px,
            "dem_sampling": "nearest_neighbor_from_copernicus_glo30_tiles",
            "cloud_mask": "truecolor brightness > 0.70 and channel range < 0.16",
            "blend": "non_cloud = 45% NASA truecolor + 55% DEM rainforest relief; cloud = DEM rainforest relief",
        },
        "caveats": [
            "Preview composite is a deterministic source-derived drape, not a production orthomosaic.",
            "Cloud-filled areas are DEM-derived rainforest relief placeholders and must be replaced by higher-resolution cloud-screened imagery before photoreal approval.",
            "DEM tiles are not yet clipped, reprojected, hydrologically conditioned, or imported as Unreal heightfields.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_pacuare_heightfield_candidate(
    southern_dem_path: Path,
    northern_dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    bounds: BoundsWgs84,
    repo_root: Path | None = None,
    output_size_px: int = 1009,
) -> None:
    """Export a review-gated 16-bit Pacuare DEM sample for Unreal Landscape import tests."""

    dem = sample_copernicus_dem(
        CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
        CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
        bounds,
        output_size_px,
    )
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError("Pacuare DEM sample contains no finite elevations")

    fill_value = float(np.median(dem[finite]))
    dem = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(dem))
    elevation_max_m = float(np.max(dem))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((dem - elevation_min_m) / elevation_span_m, 0.0, 1.0)
    heightfield_u16 = np.round(normalized * 65535.0).astype(np.uint16)

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(heightfield_u16).save(output_png_path)

    manifest = {
        "schema": "raftsim.pacuare_heightfield_candidate.v1",
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "bounds_wgs84": {
            "min_lon": bounds.min_lon,
            "min_lat": bounds.min_lat,
            "max_lon": bounds.max_lon,
            "max_lat": bounds.max_lat,
        },
        "inputs": {
            "copernicus_dem_glo30_southern_tile": _manifest_path(southern_dem_path, repo_root),
            "copernicus_dem_glo30_northern_tile": _manifest_path(northern_dem_path, repo_root),
        },
        "output_heightfield_png": _manifest_path(output_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "dem_sampling": "nearest_neighbor_from_copernicus_glo30_tiles",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
            "unreal_import_note": "Height samples are normalized to 0..65535; use the recorded elevation min/max and chosen vertical exaggeration when testing Landscape import.",
        },
        "caveats": [
            "This is an import candidate for tool testing, not a production Unreal heightfield.",
            "DEM tiles are not yet clipped to a surveyed corridor, reprojected to the chosen Costa Rica working CRS, void/artifact reviewed, hydrologically conditioned, or aligned to a reviewed river centerline.",
            "River channel burning, bank breaklines, boulder/bed features, access constraints, and guide review are still required before photoreal terrain promotion.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_pacuare_import_pilot_derivatives(
    pacuare_root: Path,
    repo_root: Path | None = None,
    source_drape_size_px: int = 4096,
    relief_size_px: int = 2048,
    heightfield_size_px: int = 2017,
    mask_size_px: int = 2048,
) -> None:
    """Generate review-gated Pacuare pilot derivatives from attached public/global seeds."""

    bounds = BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12)
    imagery_root = pacuare_root / "imagery/production_import_pilot"
    terrain_root = pacuare_root / "terrain/production_import_pilot"
    source_drape_path = imagery_root / f"source_drape_{source_drape_size_px}.png"
    source_drape_manifest_path = imagery_root / "source_drape_composite_manifest.json"
    relief_path = terrain_root / f"dem_relief_{relief_size_px}.png"
    heightfield_path = terrain_root / f"heightfield_candidate_{heightfield_size_px}.png"
    heightfield_manifest_path = terrain_root / "heightfield_candidate_manifest.json"
    water_mask_path = imagery_root / f"water_mask_{mask_size_px}.png"
    vegetation_mask_path = imagery_root / f"vegetation_mask_{mask_size_px}.png"
    mask_manifest_path = imagery_root / "source_masks_manifest.json"
    derivative_manifest_path = pacuare_root / "production_import_pilot_derivatives_manifest.json"
    southern_dem_path = pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif"
    northern_dem_path = pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif"
    nasa_truecolor_path = pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_1024.png"

    build_pacuare_demshade_drape(
        nasa_truecolor_path=nasa_truecolor_path,
        southern_dem_path=southern_dem_path,
        northern_dem_path=northern_dem_path,
        output_png_path=source_drape_path,
        output_manifest_path=source_drape_manifest_path,
        output_relief_png_path=relief_path,
        bounds=bounds,
        selected_date="2025-04-02",
        repo_root=repo_root,
        output_size_px=source_drape_size_px,
        relief_size_px=relief_size_px,
    )
    build_pacuare_heightfield_candidate(
        southern_dem_path=southern_dem_path,
        northern_dem_path=northern_dem_path,
        output_png_path=heightfield_path,
        output_manifest_path=heightfield_manifest_path,
        bounds=bounds,
        repo_root=repo_root,
        output_size_px=heightfield_size_px,
    )
    build_source_imagery_masks(
        source_image_path=source_drape_path,
        output_water_mask_path=water_mask_path,
        output_vegetation_mask_path=vegetation_mask_path,
        output_manifest_path=mask_manifest_path,
        source_id=f"pacuare_production_import_pilot_source_drape_{source_drape_size_px}",
        provider="NASA GIBS MODIS/Terra true-color plus Copernicus DEM-derived source drape",
        source_description=(
            "Pacuare stitched-size production-import pilot source drape generated from the selected NASA GIBS "
            "true-color preview seed and Copernicus DEM relief; coarse/cloudy and not production orthophoto."
        ),
        repo_root=repo_root,
        output_size_px=mask_size_px,
        preview_river_half_width_cm=305.0 * 1.05,
        preview_bend_amplitude_cm=340.0,
        preview_corridor_half_width_cm=2750.0,
    )

    manifest = {
        "schema": "raftsim.pacuare_import_pilot_derivatives.v1",
        "status": "generated_review_gated_from_coarse_preview_seeds_not_production_import",
        "source_recipe": _manifest_path(pacuare_root / "production_import_pilot.json", repo_root),
        "inputs": {
            "nasa_gibs_truecolor": _manifest_path(nasa_truecolor_path, repo_root),
            "copernicus_dem_glo30_southern_tile": _manifest_path(southern_dem_path, repo_root),
            "copernicus_dem_glo30_northern_tile": _manifest_path(northern_dem_path, repo_root),
        },
        "outputs": {
            "source_drape": _manifest_path(source_drape_path, repo_root),
            "source_drape_manifest": _manifest_path(source_drape_manifest_path, repo_root),
            "dem_relief": _manifest_path(relief_path, repo_root),
            "heightfield_candidate": _manifest_path(heightfield_path, repo_root),
            "heightfield_manifest": _manifest_path(heightfield_manifest_path, repo_root),
            "water_mask": _manifest_path(water_mask_path, repo_root),
            "vegetation_mask": _manifest_path(vegetation_mask_path, repo_root),
            "mask_manifest": _manifest_path(mask_manifest_path, repo_root),
        },
        "processing": {
            "source_drape_size_px": source_drape_size_px,
            "relief_size_px": relief_size_px,
            "heightfield_size_px": heightfield_size_px,
            "mask_size_px": mask_size_px,
            "heightfield_pixel_format": "16_bit_grayscale_png",
            "bounds_wgs84": {
                "min_lon": bounds.min_lon,
                "min_lat": bounds.min_lat,
                "max_lon": bounds.max_lon,
                "max_lat": bounds.max_lat,
            },
        },
        "caveats": [
            "These derivatives normalize the active Pacuare preview seeds into the production-import folder shape; they are not production photoreal terrain or imagery.",
            "NASA GIBS/MODIS is coarse and partly cloudy, and cloud-filled areas remain DEM-derived rainforest placeholders.",
            "Copernicus DEM tiles are not clipped to a surveyed corridor, reprojected to the final Costa Rica CRS, void-reviewed, hydrologically conditioned, or channel-burned.",
            "Masks are preview segmentation aids and must be replaced or approved through higher-resolution imagery, hydrography, rainfall/flow context, and guide/outfitter review.",
        ],
    }
    derivative_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source-derived DEM relief and preview drapes for river environments.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    south_fork_root = repo_root / "physics/data/real_world/south_fork_american_chili_bar"
    colorado_root = repo_root / "physics/data/real_world/colorado_river_grand_canyon_rowing"
    pacuare_root = repo_root / "physics/data/real_world/pacuare_river_costa_rica"
    build_dem_relief_preview(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_sample_256.tif",
        output_relief_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_relief_preview_512.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_relief_preview_manifest.json",
        source_id="usgs_3dep_chili_bar_sample_256",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
    )
    build_dem_relief_preview(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
        output_relief_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_relief_preview_1024.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_relief_preview_manifest.json",
        source_id="usgs_3dep_chili_bar_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_single_dem_heightfield_candidate(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
        output_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_heightfield_manifest.json",
        source_id="usgs_3dep_chili_bar_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        source_description="South Fork American Chili Bar corridor ImageServer export sample; not a complete conditioned corridor DEM.",
        repo_root=repo_root,
    )
    build_source_imagery_masks(
        source_image_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_sample_1024.png",
        output_water_mask_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_water_mask_1024.png",
        output_vegetation_mask_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_vegetation_mask_1024.png",
        output_manifest_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_masks_manifest.json",
        source_id="usda_naip_chili_bar_corridor_sample_1024",
        provider="USDA/APFO NAIP ImageServer",
        source_description="South Fork American active 1024px NAIP preview drape sample with generated preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=335.0,
        preview_bend_amplitude_cm=290.0,
        preview_corridor_half_width_cm=2750.0,
    )
    build_south_fork_import_pilot_derivatives(south_fork_root, repo_root=repo_root)
    build_south_fork_production_hydrography_drafts(south_fork_root, repo_root=repo_root)
    build_dem_relief_preview(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_sample_256.tif",
        output_relief_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_relief_preview_512.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_relief_preview_manifest.json",
        source_id="usgs_3dep_lees_ferry_sample_256",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
    )
    build_dem_relief_preview(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_sample_512.tif",
        output_relief_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_relief_preview_1024.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_relief_preview_manifest.json",
        source_id="usgs_3dep_lees_ferry_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_single_dem_heightfield_candidate(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_sample_512.tif",
        output_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_heightfield_manifest.json",
        source_id="usgs_3dep_lees_ferry_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        source_description="Colorado River Lees Ferry corridor ImageServer export sample; not a complete conditioned Grand Canyon corridor DEM.",
        repo_root=repo_root,
    )
    build_source_imagery_masks(
        source_image_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_sample_1024.png",
        output_water_mask_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_water_mask_1024.png",
        output_vegetation_mask_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_vegetation_mask_1024.png",
        output_manifest_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_masks_manifest.json",
        source_id="usda_naip_lees_ferry_corridor_sample_1024",
        provider="USDA/APFO NAIP ImageServer",
        source_description="Colorado River Lees Ferry active 1024px NAIP preview drape sample with generated big-water preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=520.0 * 1.08,
        preview_bend_amplitude_cm=360.0,
        preview_corridor_half_width_cm=4300.0,
    )
    build_colorado_import_pilot_derivatives(colorado_root, repo_root=repo_root)
    build_colorado_production_hydrography_drafts(colorado_root, repo_root=repo_root)
    build_pacuare_demshade_drape(
        nasa_truecolor_path=pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_512.png",
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_512.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_source_drape_composite_manifest.json",
        output_relief_png_path=pacuare_root / "terrain/pacuare_dem_relief_preview_512.png",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        selected_date="2025-04-02",
        repo_root=repo_root,
    )
    build_pacuare_demshade_drape(
        nasa_truecolor_path=pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_1024.png",
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_source_drape_composite_manifest_1024.json",
        output_relief_png_path=pacuare_root / "terrain/pacuare_dem_relief_preview_1024.png",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        selected_date="2025-04-02",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_pacuare_heightfield_candidate(
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png",
        output_manifest_path=pacuare_root / "terrain/pacuare_copernicus_dem_corridor_heightfield_manifest.json",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        repo_root=repo_root,
        output_size_px=1009,
    )
    build_source_imagery_masks(
        source_image_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png",
        output_water_mask_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_water_mask_1024.png",
        output_vegetation_mask_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_vegetation_mask_1024.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_masks_manifest.json",
        source_id="pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024",
        provider="NASA GIBS MODIS/Terra true-color plus Copernicus DEM-derived source drape",
        source_description="Pacuare active 1024px NASA GIBS/Copernicus preview drape with generated rainfed-runnable preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=305.0 * 1.05,
        preview_bend_amplitude_cm=340.0,
        preview_corridor_half_width_cm=2750.0,
    )
    build_pacuare_import_pilot_derivatives(pacuare_root, repo_root=repo_root)
    build_pacuare_preview_centerline_scaffold(pacuare_root, repo_root=repo_root)


if __name__ == "__main__":
    main()
