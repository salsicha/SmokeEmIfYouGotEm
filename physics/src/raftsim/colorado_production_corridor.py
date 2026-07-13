"""Build a source-scale Lees Ferry production corridor from acquired official tiles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


CORRIDOR_RELATIVE_ROOT = Path(
    "physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/"
    "lees_ferry_reach_2200_4700m"
)
SOURCE_ROOT = Path("physics/data/real_world/colorado_river_grand_canyon_rowing")
STATIONING_RELATIVE_PATH = SOURCE_ROOT / (
    "hydrography/nhd_hu8_lees_ferry_mainstem_stationing_candidate.json"
)
DEM_TILE_ROOT = SOURCE_ROOT / "terrain/production_import_pilot/3dep_tiles"
NAIP_TILE_ROOT = SOURCE_ROOT / "imagery/production_import_pilot/naip_tiles"
LANDSCAPE_SIZE = 2017
EARTH_RADIUS_M = 6_378_137.0
STATION_START_M = 2_200.0
STATION_END_M = 4_700.0
GROUND_BUFFER_M = 700.0
SOURCE_BBOX_EPSG3857 = (
    -12_429_934.3420,
    4_411_265.9103,
    -12_416_576.0031,
    4_425_177.2279,
)
SOURCE_HASHES = {
    "terrain/production_import_pilot/3dep_tiles/colorado_lees_ferry_tile_r0_c0.tif":
        "ea2b70bf25c0f82bb97494008fc410c57cfefcfab9d4d8d1f3287c7e80b6223d",
    "terrain/production_import_pilot/3dep_tiles/colorado_lees_ferry_tile_r0_c1.tif":
        "71fe8f13b1740ae588c0cdd20810a9904828f2b59f614d70440f8ba5c5a889af",
    "terrain/production_import_pilot/3dep_tiles/colorado_lees_ferry_tile_r1_c0.tif":
        "1e73fcc827cf2eea06795e2561748466456f7ebcc22c5d7a954b4bad6ee311d1",
    "terrain/production_import_pilot/3dep_tiles/colorado_lees_ferry_tile_r1_c1.tif":
        "a1ee9f7a40682181332c9a8f070c60bff5fe213a80d4cad1bc1243a22e13efc3",
    "imagery/production_import_pilot/naip_tiles/colorado_lees_ferry_tile_r0_c0.png":
        "60c627be7f447ed90166f4bc25aae3204f4114471edbdeca5c8da9155226b728",
    "imagery/production_import_pilot/naip_tiles/colorado_lees_ferry_tile_r0_c1.png":
        "22fa3b69bfd54fc2f836e8f3d93c7b2fe230fc8359e710b21865a6005f5c8006",
    "imagery/production_import_pilot/naip_tiles/colorado_lees_ferry_tile_r1_c0.png":
        "53424d46e2675818694837c6337bf8af8e52bdae2b4966c6cb3deaddd06f613e",
    "imagery/production_import_pilot/naip_tiles/colorado_lees_ferry_tile_r1_c1.png":
        "27726a165d82d37d3fa6c118a35d5257966f95d48c5fada00731962fdc505f3f",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _web_mercator(lon: float, lat: float) -> tuple[float, float]:
    latitude = max(-85.05112878, min(85.05112878, lat))
    return (
        EARTH_RADIUS_M * math.radians(lon),
        EARTH_RADIUS_M
        * math.log(math.tan(math.pi * 0.25 + math.radians(latitude) * 0.5)),
    )


def _load_mosaic(root: Path, suffix: str) -> np.ndarray:
    rows = []
    for row in (1, 0):
        tiles = []
        for column in (0, 1):
            path = root / f"colorado_lees_ferry_tile_r{row}_c{column}.{suffix}"
            tiles.append(np.asarray(Image.open(path)))
        rows.append(np.concatenate(tiles, axis=1))
    return np.concatenate(rows, axis=0)


def _dense_centerline(stationing: dict[str, object]) -> list[dict[str, float]]:
    source = [
        sample
        for sample in stationing["station_samples"]
        if STATION_START_M <= float(sample["station_m"]) <= STATION_END_M
    ]
    if len(source) < 2:
        raise RuntimeError("Colorado stationing does not cover the requested reach")
    dense: list[dict[str, float]] = []
    for first, second in zip(source, source[1:], strict=False):
        station_span = float(second["station_m"]) - float(first["station_m"])
        steps = max(1, int(math.ceil(station_span / 4.0)))
        for step in range(steps):
            fraction = step / steps
            dense.append(
                {
                    key: float(first[key]) + (float(second[key]) - float(first[key])) * fraction
                    for key in ("station_m", "lon", "lat")
                }
            )
    dense.append({key: float(source[-1][key]) for key in ("station_m", "lon", "lat")})
    station_origin = dense[0]["station_m"]
    for point in dense:
        point["station_m"] -= station_origin
    return dense


def _crop_array(
    source: np.ndarray,
    crop_bbox: tuple[float, float, float, float],
) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    source_xmin, source_ymin, source_xmax, source_ymax = SOURCE_BBOX_EPSG3857
    crop_xmin, crop_ymin, crop_xmax, crop_ymax = crop_bbox
    height, width = source.shape[:2]
    left = max(0, int(math.floor((crop_xmin - source_xmin) / (source_xmax - source_xmin) * width)))
    right = min(width, int(math.ceil((crop_xmax - source_xmin) / (source_xmax - source_xmin) * width)))
    top = max(0, int(math.floor((source_ymax - crop_ymax) / (source_ymax - source_ymin) * height)))
    bottom = min(height, int(math.ceil((source_ymax - crop_ymin) / (source_ymax - source_ymin) * height)))
    if right - left < 2 or bottom - top < 2:
        raise RuntimeError("Colorado corridor crop is empty")
    aligned_bbox = (
        source_xmin + left / width * (source_xmax - source_xmin),
        source_ymax - bottom / height * (source_ymax - source_ymin),
        source_xmin + right / width * (source_xmax - source_xmin),
        source_ymax - top / height * (source_ymax - source_ymin),
    )
    return source[top:bottom, left:right].copy(), aligned_bbox


def _write_material_maps(
    dem: np.ndarray,
    aerial: Image.Image,
    centerline_normalized: list[tuple[float, float]],
    ground_width_m: float,
    ground_height_m: float,
    derived_root: Path,
) -> dict[str, Path]:
    size = 2048
    albedo = np.asarray(aerial.resize((size, size), Image.Resampling.LANCZOS), dtype=np.uint8)
    albedo_path = derived_root / "colorado_lees_ferry_reach_source_albedo_2048.png"
    Image.fromarray(albedo, mode="RGB").save(albedo_path)

    source_rgb = albedo.astype(np.float32) / 255.0
    source_luma = (
        source_rgb[..., 0] * 0.2126
        + source_rgb[..., 1] * 0.7152
        + source_rgb[..., 2] * 0.0722
    )
    local_luma = np.asarray(
        Image.fromarray(np.rint(source_luma * 255.0).astype(np.uint8), mode="L").filter(
            ImageFilter.GaussianBlur(radius=56)
        ),
        dtype=np.float32,
    ) / 255.0
    local_gain = np.clip(0.42 / (local_luma + 0.10), 0.78, 3.10)
    terrain_rgb = np.clip(source_rgb * local_gain[..., None], 0.0, 1.0)
    terrain_luma = (
        terrain_rgb[..., 0] * 0.2126
        + terrain_rgb[..., 1] * 0.7152
        + terrain_rgb[..., 2] * 0.0722
    )
    shadow_weight = np.clip((0.32 - terrain_luma) / 0.26, 0.0, 1.0)
    target_luma = terrain_luma + (0.25 - terrain_luma) * shadow_weight * 0.92
    terrain_rgb *= (target_luma / np.maximum(terrain_luma, 0.001))[..., None]
    mineral_tint = np.asarray([1.16, 0.96, 0.78], dtype=np.float32)
    mineral_tint /= float(np.dot(mineral_tint, np.asarray([0.2126, 0.7152, 0.0722])))
    mineral_rgb = target_luma[..., None] * mineral_tint
    terrain_rgb = np.clip(
        terrain_rgb * (1.0 - shadow_weight[..., None] * 0.82)
        + mineral_rgb * shadow_weight[..., None] * 0.82,
        0.0,
        1.0,
    )
    terrain_albedo_path = derived_root / "colorado_lees_ferry_reach_terrain_albedo_2048.png"
    Image.fromarray(np.rint(terrain_rgb * 255.0).astype(np.uint8), mode="RGB").save(
        terrain_albedo_path
    )

    water_image = Image.new("L", (size, size), 0)
    pixels = [
        (int(round(x * (size - 1))), int(round((1.0 - y) * (size - 1))))
        for x, y in centerline_normalized
    ]
    water_width_px = max(5, int(round(120.0 / ground_width_m * size)))
    ImageDraw.Draw(water_image).line(pixels, fill=255, width=water_width_px, joint="curve")
    water = np.asarray(water_image, dtype=np.float32) / 255.0
    red, green, blue = (albedo[..., index].astype(np.float32) for index in range(3))
    vegetation = np.clip((green - 0.52 * (red + blue) + 10.0) / 34.0, 0.0, 1.0)
    vegetation *= 1.0 - water
    zones = np.stack([1.0 - water, vegetation, water], axis=2)
    zones_path = derived_root / "colorado_lees_ferry_reach_material_zones_2048.png"
    Image.fromarray(np.rint(zones * 255.0).astype(np.uint8), mode="RGB").save(zones_path)

    resized_dem = np.asarray(
        Image.fromarray(dem.astype(np.float32), mode="F").resize((size, size), Image.Resampling.BILINEAR),
        dtype=np.float32,
    )
    row_gradient, column_gradient = np.gradient(
        resized_dem,
        ground_height_m / (size - 1),
        ground_width_m / (size - 1),
    )
    nx, ny, nz = -column_gradient * 0.36, row_gradient * 0.36, np.ones_like(resized_dem)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / length * 0.5 + 0.5, ny / length * 0.5 + 0.5, nz / length * 0.5 + 0.5], axis=2)
    normal_path = derived_root / "colorado_lees_ferry_reach_normal_2048.png"
    Image.fromarray(np.rint(normal * 255.0).astype(np.uint8), mode="RGB").save(normal_path)

    relief = float(np.max(resized_dem) - np.min(resized_dem))
    height = np.clip((resized_dem - float(np.min(resized_dem))) / max(relief, 0.001), 0.0, 1.0)
    slope = np.sqrt(column_gradient * column_gradient + row_gradient * row_gradient)
    ao = np.clip(0.96 - np.minimum(slope, 3.0) * 0.12, 0.42, 1.0)
    roughness = np.clip(0.66 + slope * 0.05 - water * 0.25, 0.34, 0.92)
    packed_path = derived_root / "colorado_lees_ferry_reach_ao_roughness_height_2048.png"
    Image.fromarray(np.rint(np.stack([ao, roughness, height], axis=2) * 255.0).astype(np.uint8), mode="RGB").save(packed_path)
    return {
        "source_albedo": albedo_path,
        "terrain_albedo": terrain_albedo_path,
        "material_zones": zones_path,
        "normal": normal_path,
        "ao_roughness_height": packed_path,
    }


def build_colorado_lees_ferry_production_corridor(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    source_root = repo_root / SOURCE_ROOT
    for relative_path, expected_hash in SOURCE_HASHES.items():
        if _sha256(source_root / relative_path) != expected_hash:
            raise RuntimeError(f"Colorado source hash mismatch: {relative_path}")

    stationing = json.loads((repo_root / STATIONING_RELATIVE_PATH).read_text(encoding="utf-8"))
    centerline = _dense_centerline(stationing)
    mercator_points = [(*_web_mercator(point["lon"], point["lat"]), point) for point in centerline]
    center_latitude = sum(point["lat"] for point in centerline) / len(centerline)
    ground_scale = math.cos(math.radians(center_latitude))
    mercator_buffer = GROUND_BUFFER_M / ground_scale
    requested_bbox = (
        max(SOURCE_BBOX_EPSG3857[0], min(point[0] for point in mercator_points) - mercator_buffer),
        max(SOURCE_BBOX_EPSG3857[1], min(point[1] for point in mercator_points) - mercator_buffer),
        min(SOURCE_BBOX_EPSG3857[2], max(point[0] for point in mercator_points) + mercator_buffer),
        min(SOURCE_BBOX_EPSG3857[3], max(point[1] for point in mercator_points) + mercator_buffer),
    )

    dem_mosaic = _load_mosaic(source_root / "terrain/production_import_pilot/3dep_tiles", "tif").astype(np.float32)
    aerial_mosaic = _load_mosaic(source_root / "imagery/production_import_pilot/naip_tiles", "png")
    dem, aligned_bbox = _crop_array(dem_mosaic, requested_bbox)
    aerial, aerial_bbox = _crop_array(aerial_mosaic, aligned_bbox)
    if any(abs(a - b) > 8.0 for a, b in zip(aligned_bbox, aerial_bbox, strict=True)):
        raise RuntimeError("Colorado DEM and aerial crops are not aligned")

    xmin, ymin, xmax, ymax = aligned_bbox
    ground_width_m = (xmax - xmin) * ground_scale
    ground_height_m = (ymax - ymin) * ground_scale
    corridor_root = repo_root / CORRIDOR_RELATIVE_ROOT
    derived_root = corridor_root / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)

    heightfield_path = derived_root / "colorado_lees_ferry_reach_heightfield_2017.png"
    resized_dem = np.asarray(
        Image.fromarray(dem, mode="F").resize((LANDSCAPE_SIZE, LANDSCAPE_SIZE), Image.Resampling.BILINEAR),
        dtype=np.float32,
    )
    elevation_min_m = float(np.min(resized_dem))
    elevation_max_m = float(np.max(resized_dem))
    normalized = np.clip((resized_dem - elevation_min_m) / (elevation_max_m - elevation_min_m), 0.0, 1.0)
    Image.fromarray(np.rint(normalized * 65535.0).astype(np.uint16)).save(heightfield_path)

    local_points = []
    for mercator_x, mercator_y, point in mercator_points:
        normalized_x = (mercator_x - xmin) / (xmax - xmin)
        normalized_y = (mercator_y - ymin) / (ymax - ymin)
        local_points.append(
            {
                "station_m": round(point["station_m"], 3),
                "wgs84": [point["lon"], point["lat"]],
                "epsg3857": [mercator_x, mercator_y],
                "normalized_xy": [normalized_x, normalized_y],
                "unreal_local_cm": [
                    normalized_x * ground_width_m * 100.0,
                    (1.0 - normalized_y) * ground_height_m * 100.0,
                ],
            }
        )

    aerial_image = Image.fromarray(aerial[..., :3].astype(np.uint8), mode="RGB")
    material_maps = _write_material_maps(
        dem,
        aerial_image,
        [(point["normalized_xy"][0], point["normalized_xy"][1]) for point in local_points],
        ground_width_m,
        ground_height_m,
        derived_root,
    )
    alignment = aerial_image.resize((2048, 2048), Image.Resampling.LANCZOS)
    overlay_points = [
        (int(round(point["normalized_xy"][0] * 2047)), int(round((1.0 - point["normalized_xy"][1]) * 2047)))
        for point in local_points
    ]
    ImageDraw.Draw(alignment).line(overlay_points, fill=(80, 220, 255), width=5, joint="curve")
    alignment_path = derived_root / "colorado_lees_ferry_reach_centerline_alignment_2048.png"
    alignment.save(alignment_path)

    centerline_path = corridor_root / "centerline_local.json"
    centerline_record = {
        "schema": "raftsim.production_corridor_centerline_local.v1",
        "status": "source_aligned_review_gated_not_gameplay_authority",
        "source": str(STATIONING_RELATIVE_PATH),
        "source_crs": "EPSG:4269",
        "service_crs": "EPSG:3857",
        "local_metric_policy": "EPSG:3857 offsets multiplied by local latitude cosine; Unreal local X increases east and local Y follows source image rows southward",
        "source_station_range_m": [STATION_START_M, STATION_END_M],
        "station_range_m": [0.0, STATION_END_M - STATION_START_M],
        "points": local_points,
    }
    centerline_path.write_text(json.dumps(centerline_record, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema": "raftsim.colorado_production_corridor.v1",
        "river_id": "colorado_river",
        "reach_id": "lees_ferry_2200_4700m",
        "status": "official_source_attached_physical_landscape_inputs_generated_review_gated",
        "production_promoted": False,
        "bounds_epsg3857": list(aligned_bbox),
        "ground_span_m_approx": [ground_width_m, ground_height_m],
        "unreal_landscape": {
            "heightfield": str(heightfield_path.relative_to(repo_root)),
            "heightfield_size_px": [LANDSCAPE_SIZE, LANDSCAPE_SIZE],
            "horizontal_span_cm": [ground_width_m * 100.0, ground_height_m * 100.0],
            "elevation_min_m_navd88": elevation_min_m,
            "elevation_max_m_navd88": elevation_max_m,
            "relief_m": elevation_max_m - elevation_min_m,
            "z_scale_cm": (elevation_max_m - elevation_min_m) * 100.0 / 512.0,
            "channel_conditioning": {
                "policy": "none_preserve_official_3dep_surface_for_first_source_scale_visual_slice",
                "authority": "source_dem_visual_review_only_not_bathymetry_or_solver_geometry",
            },
        },
        "source_artifacts": {
            "tile_hashes": SOURCE_HASHES,
            "stationing": str(STATIONING_RELATIVE_PATH),
            "source_bbox_epsg3857": list(SOURCE_BBOX_EPSG3857),
        },
        "derived_artifacts": {
            "heightfield": str(heightfield_path.relative_to(repo_root)),
            "local_centerline": str(centerline_path.relative_to(repo_root)),
            "centerline_alignment_preview": str(alignment_path.relative_to(repo_root)),
            **{name: str(path.relative_to(repo_root)) for name, path in material_maps.items()},
        },
        "terrain_albedo_conditioning": {
            "policy": "retain_raw_naip_and_generate_local_luminance_normalized_warm_shadow_render_derivative",
            "purpose": "remove_baked_aerial_cast_shadows_before_unreal_relights_steep_canyon_walls",
            "local_luminance_blur_radius_px": 56,
            "shadow_target_luminance": 0.25,
            "authority": "visual_render_derivative_only_not_source_measurement_or_geometry",
        },
        "review_boundaries": {
            "allowed_now": ["isolated source-scale Unreal visual candidate", "camera and material calibration"],
            "blocked_now": [
                "solver or collision bathymetry authority",
                "full Grand Canyon route claim",
                "lifelike or production promotion",
                "guide or oarsman approval",
            ],
        },
    }
    manifest_path = corridor_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path.relative_to(repo_root))
    return manifest
