"""Build the first physical-scale South Fork American production corridor slice."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


CORRIDOR_RELATIVE_ROOT = Path(
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "chili_bar_reach_0_2500m"
)
CENTERLINE_RELATIVE_PATH = Path(
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "production_import_pilot/centerline.geojson"
)
DEM_RELATIVE_PATH = Path("source/usgs_1m_ca_sierranevada_b22_object_131308.tif")
NAIP_RELATIVE_PATH = Path("source/usda_naip_20220720_object_1828092.png")
DEM_SHA256 = "d360aff16cfa1e404a69dc45f9a47248be36aa9351a7ed39449625a891e933d2"
NAIP_SHA256 = "7c1d03f3bcf300a87f4077821f8d4fbf984fbd2c36b847af7419252aafe82cb2"
BBOX_EPSG3857 = (
    -13440966.690560449,
    4688433.364095909,
    -13437882.594484959,
    4690610.71422138,
)
LANDSCAPE_SIZE = 2017
EARTH_RADIUS_M = 6_378_137.0
CHANNEL_HALF_WIDTH_M = 14.0
CHANNEL_FEATHER_WIDTH_M = 12.0
CHANNEL_DEPTH_M = 1.4
MAX_CHANNEL_LOWERING_M = 4.0
MAX_SOURCE_HEIGHT_ABOVE_SURFACE_M = 3.0
WATER_HALF_WIDTH_M = 11.0
CHANNEL_SMOOTHING_ITERATIONS = 24


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


def _inverse_web_mercator(x: float, y: float) -> tuple[float, float]:
    return (
        math.degrees(x / EARTH_RADIUS_M),
        math.degrees(2.0 * math.atan(math.exp(y / EARTH_RADIUS_M)) - math.pi * 0.5),
    )


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon_a, lat_a = map(math.radians, a)
    lon_b, lat_b = map(math.radians, b)
    dlon = lon_b - lon_a
    dlat = lat_b - lat_a
    value = (
        math.sin(dlat * 0.5) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(dlon * 0.5) ** 2
    )
    return 2.0 * 6_371_008.8 * math.asin(math.sqrt(value))


def _load_reach_centerline(repo_root: Path) -> list[tuple[float, float, float]]:
    source = json.loads((repo_root / CENTERLINE_RELATIVE_PATH).read_text(encoding="utf-8"))
    coordinates = source["features"][0]["geometry"]["coordinates"]
    points: list[tuple[float, float, float]] = []
    station_m = 0.0
    previous: tuple[float, float] | None = None
    for raw in coordinates:
        point = (float(raw[0]), float(raw[1]))
        if previous is not None:
            station_m += _haversine_m(previous, point)
        if station_m <= 2_550.0:
            points.append((point[0], point[1], station_m))
        else:
            break
        previous = point
    if not points or points[-1][2] < 2_450.0:
        raise RuntimeError("The reviewed NHD centerline does not cover the 0-2,500 m reach")
    return points


def _smooth_and_resample_centerline(
    points: list[tuple[float, float, float]],
    spacing_m: float = 4.0,
) -> list[tuple[float, float, float]]:
    """Create a dense, corner-cut centerline while retaining the reviewed endpoints."""

    smoothed = list(points)
    for _ in range(3):
        refined = [smoothed[0]]
        for first, second in zip(smoothed, smoothed[1:]):
            refined.append(
                tuple(0.75 * a + 0.25 * b for a, b in zip(first, second, strict=True))
            )
            refined.append(
                tuple(0.25 * a + 0.75 * b for a, b in zip(first, second, strict=True))
            )
        refined.append(smoothed[-1])
        smoothed = refined

    dense = []
    for first, second in zip(smoothed, smoothed[1:]):
        station_span_m = max(0.001, second[2] - first[2])
        steps = max(1, int(math.ceil(station_span_m / spacing_m)))
        for step in range(steps):
            fraction = step / steps
            dense.append(
                tuple(
                    a + (b - a) * fraction
                    for a, b in zip(first, second, strict=True)
                )
            )
    dense.append(smoothed[-1])
    return dense


def _write_heightfield(dem: np.ndarray, path: Path) -> tuple[float, float]:
    minimum = float(np.min(dem))
    maximum = float(np.max(dem))
    if not math.isfinite(minimum) or not math.isfinite(maximum) or maximum <= minimum:
        raise RuntimeError("DEM has invalid elevation bounds")
    resized = np.asarray(
        Image.fromarray(dem.astype(np.float32), mode="F").resize(
            (LANDSCAPE_SIZE, LANDSCAPE_SIZE),
            Image.Resampling.BILINEAR,
        ),
        dtype=np.float32,
    )
    normalized = np.clip((resized - minimum) / (maximum - minimum), 0.0, 1.0)
    Image.fromarray(np.rint(normalized * 65535.0).astype(np.uint16)).save(path)
    return minimum, maximum


def _condition_channel(
    dem: np.ndarray,
    normalized_centerline: list[tuple[float, float, float]],
    ground_width_m: float,
    ground_height_m: float,
) -> tuple[np.ndarray, dict[str, object], list[tuple[float, float, float]]]:
    """Lower a bounded channel around the reviewed centerline without altering uplands."""

    height, width = dem.shape
    pixel_x_m = ground_width_m / (width - 1)
    pixel_y_m = ground_height_m / (height - 1)
    sample_radius_x = max(2, int(round(10.0 / pixel_x_m)))
    sample_radius_y = max(2, int(round(10.0 / pixel_y_m)))
    sampled_surfaces: list[float] = []
    for normalized_x, normalized_y, _station_m in normalized_centerline:
        column = int(round(normalized_x * (width - 1)))
        row = int(round((1.0 - normalized_y) * (height - 1)))
        window = dem[
            max(0, row - sample_radius_y) : min(height, row + sample_radius_y + 1),
            max(0, column - sample_radius_x) : min(width, column + sample_radius_x + 1),
        ]
        sampled_surfaces.append(float(np.percentile(window, 5.0)))

    monotone_surfaces = np.minimum.accumulate(np.asarray(sampled_surfaces, dtype=np.float64))
    if len(monotone_surfaces) >= 3:
        smoothed = monotone_surfaces.copy()
        for _ in range(3):
            smoothed[1:-1] = (
                monotone_surfaces[:-2]
                + 2.0 * monotone_surfaces[1:-1]
                + monotone_surfaces[2:]
            ) * 0.25
            monotone_surfaces = np.minimum.accumulate(smoothed)

    conditioned = dem.copy()
    touched = np.zeros(dem.shape, dtype=bool)
    corridor_weight = np.zeros(dem.shape, dtype=np.float32)
    half_width_with_feather = CHANNEL_HALF_WIDTH_M + CHANNEL_FEATHER_WIDTH_M
    dense_profile: list[tuple[float, float, float]] = []
    for index in range(len(normalized_centerline) - 1):
        x0, y0, station0 = normalized_centerline[index]
        x1, y1, station1 = normalized_centerline[index + 1]
        segment_length_m = max(0.001, station1 - station0)
        steps = max(1, int(math.ceil(segment_length_m / 2.0)))
        for step in range(steps):
            fraction = step / steps
            dense_profile.append(
                (
                    x0 + (x1 - x0) * fraction,
                    y0 + (y1 - y0) * fraction,
                    float(
                        monotone_surfaces[index]
                        + (monotone_surfaces[index + 1] - monotone_surfaces[index])
                        * fraction
                    ),
                )
            )
    dense_profile.append(
        (
            normalized_centerline[-1][0],
            normalized_centerline[-1][1],
            float(monotone_surfaces[-1]),
        )
    )

    radius_x = int(math.ceil(half_width_with_feather / pixel_x_m))
    radius_y = int(math.ceil(half_width_with_feather / pixel_y_m))
    for normalized_x, normalized_y, surface_elevation_m in dense_profile:
        center_column = int(round(normalized_x * (width - 1)))
        center_row = int(round((1.0 - normalized_y) * (height - 1)))
        x_start = max(0, center_column - radius_x)
        x_stop = min(width, center_column + radius_x + 1)
        y_start = max(0, center_row - radius_y)
        y_stop = min(height, center_row + radius_y + 1)
        x_offsets_m = (np.arange(x_start, x_stop) - center_column) * pixel_x_m
        y_offsets_m = (np.arange(y_start, y_stop) - center_row) * pixel_y_m
        distance_m = np.sqrt(y_offsets_m[:, None] ** 2 + x_offsets_m[None, :] ** 2)
        blend = np.clip(
            (distance_m - CHANNEL_HALF_WIDTH_M) / CHANNEL_FEATHER_WIDTH_M,
            0.0,
            1.0,
        )
        blend = blend * blend * (3.0 - 2.0 * blend)
        corridor_weight[y_start:y_stop, x_start:x_stop] = np.maximum(
            corridor_weight[y_start:y_stop, x_start:x_stop],
            1.0 - blend,
        )
        source_window = conditioned[y_start:y_stop, x_start:x_stop]
        original_window = dem[y_start:y_stop, x_start:x_stop]
        target_bed_m = surface_elevation_m - CHANNEL_DEPTH_M
        lowered = target_bed_m * (1.0 - blend) + source_window * blend
        candidate = np.maximum(
            original_window - MAX_CHANNEL_LOWERING_M,
            np.minimum(source_window, lowered),
        )
        candidate = np.where(
            original_window <= surface_elevation_m + MAX_SOURCE_HEIGHT_ABOVE_SURFACE_M,
            candidate,
            source_window,
        )
        modified = candidate < source_window - 1.0e-4
        source_window[modified] = candidate[modified]
        touched[y_start:y_stop, x_start:x_stop] |= modified

    smoothed = conditioned.copy()
    for _ in range(CHANNEL_SMOOTHING_ITERATIONS):
        padded = np.pad(smoothed, 1, mode="edge")
        smoothed = (
            padded[1:-1, 1:-1] * 4.0
            + padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
        ) * 0.125
    smoothing_weight = np.clip(corridor_weight * 0.82, 0.0, 0.82)
    conditioned = np.minimum(
        dem,
        conditioned * (1.0 - smoothing_weight) + smoothed * smoothing_weight,
    )
    conditioned = np.maximum(conditioned, dem - MAX_CHANNEL_LOWERING_M)

    delta = dem - conditioned
    profile = [
        (point[2], float(surface), float(surface - CHANNEL_DEPTH_M))
        for point, surface in zip(normalized_centerline, monotone_surfaces, strict=True)
    ]
    report: dict[str, object] = {
        "policy": "bounded_reviewed_centerline_low_percentile_monotone_bed_conditioning",
        "authority": "derived_render_and_landscape_geometry_not_solver_or_surveyed_bathymetry",
        "centerline_source": str(CENTERLINE_RELATIVE_PATH),
        "surface_sample_percentile": 5.0,
        "surface_sample_radius_m": 10.0,
        "channel_half_width_m": CHANNEL_HALF_WIDTH_M,
        "bank_feather_width_m": CHANNEL_FEATHER_WIDTH_M,
        "nominal_depth_m": CHANNEL_DEPTH_M,
        "maximum_allowed_lowering_m": MAX_CHANNEL_LOWERING_M,
        "maximum_source_height_above_surface_m": MAX_SOURCE_HEIGHT_ABOVE_SURFACE_M,
        "corridor_smoothing_iterations": CHANNEL_SMOOTHING_ITERATIONS,
        "corridor_smoothing_weight": 0.82,
        "profile_start_surface_m_navd88": float(monotone_surfaces[0]),
        "profile_end_surface_m_navd88": float(monotone_surfaces[-1]),
        "profile_drop_m": float(monotone_surfaces[0] - monotone_surfaces[-1]),
        "monotone_downstream": bool(np.all(np.diff(monotone_surfaces) <= 1.0e-6)),
        "modified_source_sample_count": int(np.count_nonzero(touched)),
        "maximum_lowering_m": float(np.max(delta)),
        "mean_lowering_over_modified_samples_m": float(np.mean(delta[touched])),
    }
    return conditioned, report, profile


def _write_hillshade(dem: np.ndarray, path: Path, ground_pixel_size_m: float) -> None:
    row_gradient, column_gradient = np.gradient(dem, ground_pixel_size_m, ground_pixel_size_m)
    dz_east = column_gradient
    dz_north = -row_gradient
    normal_x = -dz_east
    normal_y = -dz_north
    normal_z = np.ones_like(dem)
    length = np.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z)
    normal_x /= length
    normal_y /= length
    normal_z /= length

    azimuth = math.radians(315.0)
    altitude = math.radians(45.0)
    light_x = math.sin(azimuth) * math.cos(altitude)
    light_y = math.cos(azimuth) * math.cos(altitude)
    light_z = math.sin(altitude)
    shade = np.clip(normal_x * light_x + normal_y * light_y + normal_z * light_z, 0.0, 1.0)
    shade = np.clip((shade - 0.12) / 0.88, 0.0, 1.0) ** 0.72
    Image.fromarray(np.rint(shade * 255.0).astype(np.uint8), mode="L").save(path)


def _write_source_material_maps(
    dem: np.ndarray,
    naip: Image.Image,
    normalized_centerline: list[tuple[float, float]],
    ground_width_m: float,
    ground_height_m: float,
    derived_root: Path,
) -> dict[str, Path]:
    size = 2048
    albedo = np.asarray(
        naip.resize((size, size), Image.Resampling.LANCZOS),
        dtype=np.float32,
    )
    shadow_lift = np.clip((albedo.mean(axis=2, keepdims=True) - 28.0) / 92.0, 0.0, 1.0)
    albedo = np.clip(albedo * (1.05 + 0.08 * (1.0 - shadow_lift)), 0.0, 255.0)
    albedo_path = derived_root / "south_fork_chili_bar_reach_source_albedo_2048.png"
    Image.fromarray(np.rint(albedo).astype(np.uint8), mode="RGB").save(albedo_path)

    water_image = Image.new("L", (size, size), 0)
    water_draw = ImageDraw.Draw(water_image)
    centerline_pixels = [
        (int(round(x * (size - 1))), int(round((1.0 - y) * (size - 1))))
        for x, y in normalized_centerline
    ]
    river_width_m = WATER_HALF_WIDTH_M * 2.0
    river_width_pixels = max(3, int(round(river_width_m / ground_width_m * size)))
    water_draw.line(centerline_pixels, fill=255, width=river_width_pixels, joint="curve")
    water = np.asarray(water_image, dtype=np.float32) / 255.0

    red = albedo[..., 0]
    green = albedo[..., 1]
    blue = albedo[..., 2]
    excess_green = green - 0.5 * (red + blue)
    vegetation = np.clip((excess_green + 8.0) / 38.0, 0.0, 1.0) * (1.0 - water)
    dry = 1.0 - water
    zones = np.stack([dry, vegetation, water], axis=2)
    zones_path = derived_root / "south_fork_chili_bar_reach_material_zones_2048.png"
    Image.fromarray(np.rint(zones * 255.0).astype(np.uint8), mode="RGB").save(zones_path)

    dem_resized = np.asarray(
        Image.fromarray(dem.astype(np.float32), mode="F").resize(
            (size, size),
            Image.Resampling.BILINEAR,
        ),
        dtype=np.float32,
    )
    pixel_x_m = ground_width_m / (size - 1)
    pixel_y_m = ground_height_m / (size - 1)
    row_gradient, column_gradient = np.gradient(dem_resized, pixel_y_m, pixel_x_m)
    normal_strength = 0.42
    normal_x = -column_gradient * normal_strength
    normal_y = row_gradient * normal_strength
    normal_z = np.ones_like(dem_resized)
    normal_length = np.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z)
    normal = np.stack(
        [
            normal_x / normal_length * 0.5 + 0.5,
            normal_y / normal_length * 0.5 + 0.5,
            normal_z / normal_length * 0.5 + 0.5,
        ],
        axis=2,
    )
    normal_path = derived_root / "south_fork_chili_bar_reach_normal_2048.png"
    Image.fromarray(np.rint(np.clip(normal, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB").save(
        normal_path
    )

    height = np.clip(
        (dem_resized - float(np.min(dem))) / (float(np.max(dem)) - float(np.min(dem))),
        0.0,
        1.0,
    )
    slope = np.sqrt(column_gradient * column_gradient + row_gradient * row_gradient)
    ambient_occlusion = np.clip(0.96 - np.minimum(slope, 2.5) * 0.13, 0.48, 1.0)
    roughness = np.clip(0.62 + vegetation * 0.22 + water * -0.26, 0.32, 0.90)
    packed = np.stack([ambient_occlusion, roughness, height], axis=2)
    packed_path = derived_root / "south_fork_chili_bar_reach_ao_roughness_height_2048.png"
    Image.fromarray(np.rint(packed * 255.0).astype(np.uint8), mode="RGB").save(packed_path)
    return {
        "source_albedo": albedo_path,
        "material_zones": zones_path,
        "normal": normal_path,
        "ao_roughness_height": packed_path,
    }


def build_south_fork_chili_bar_production_corridor(repo_root: Path) -> dict[str, object]:
    """Validate source exports and generate physical-scale Unreal corridor inputs."""

    repo_root = repo_root.resolve()
    corridor_root = repo_root / CORRIDOR_RELATIVE_ROOT
    derived_root = corridor_root / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)
    dem_path = corridor_root / DEM_RELATIVE_PATH
    naip_path = corridor_root / NAIP_RELATIVE_PATH
    if _sha256(dem_path) != DEM_SHA256 or _sha256(naip_path) != NAIP_SHA256:
        raise RuntimeError("South Fork production corridor source hash mismatch")

    dem = np.asarray(Image.open(dem_path), dtype=np.float32)
    naip = Image.open(naip_path).convert("RGB")
    if dem.shape != (1445, 2048) or naip.size != (4096, 2890):
        raise RuntimeError(f"Unexpected source dimensions: DEM {dem.shape}, NAIP {naip.size}")

    xmin, ymin, xmax, ymax = BBOX_EPSG3857
    center_latitude = 38.7780
    mercator_ground_scale = math.cos(math.radians(center_latitude))
    ground_width_m = (xmax - xmin) * mercator_ground_scale
    ground_height_m = (ymax - ymin) * mercator_ground_scale
    ground_pixel_size_m = 0.5 * (
        ground_width_m / dem.shape[1] + ground_height_m / dem.shape[0]
    )

    heightfield_path = derived_root / "south_fork_chili_bar_reach_heightfield_2017.png"
    hillshade_path = derived_root / "south_fork_chili_bar_reach_hillshade_2048.png"
    alignment_path = derived_root / "south_fork_chili_bar_reach_naip_centerline_2048.png"
    centerline_path = corridor_root / "centerline_local.json"

    source_centerline = _load_reach_centerline(repo_root)
    source_centerline_mercator = [
        (*_web_mercator(lon, lat), station_m)
        for lon, lat, station_m in source_centerline
    ]
    centerline = _smooth_and_resample_centerline(source_centerline_mercator)
    local_points = []
    overlay = naip.resize((2048, 1445), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(overlay)
    overlay_points = []
    for mercator_x, mercator_y, station_m in centerline:
        lon, lat = _inverse_web_mercator(mercator_x, mercator_y)
        normalized_x = (mercator_x - xmin) / (xmax - xmin)
        normalized_y = (mercator_y - ymin) / (ymax - ymin)
        if not (0.0 <= normalized_x <= 1.0 and 0.0 <= normalized_y <= 1.0):
            raise RuntimeError(f"Centerline station {station_m:.1f} m falls outside the source bbox")
        local_points.append(
            {
                "station_m": round(station_m, 3),
                "wgs84": [lon, lat],
                "epsg3857": [mercator_x, mercator_y],
                "normalized_xy": [normalized_x, normalized_y],
                "unreal_local_cm": [
                    normalized_x * ground_width_m * 100.0,
                    (1.0 - normalized_y) * ground_height_m * 100.0,
                ],
            }
        )
        overlay_points.append(
            (
                int(round(normalized_x * (overlay.width - 1))),
                int(round((1.0 - normalized_y) * (overlay.height - 1))),
            )
        )
    normalized_centerline = [
        (
            float(point["normalized_xy"][0]),
            float(point["normalized_xy"][1]),
            float(point["station_m"]),
        )
        for point in local_points
    ]
    conditioned_dem, channel_conditioning, channel_profile = _condition_channel(
        dem,
        normalized_centerline,
        ground_width_m,
        ground_height_m,
    )
    for point, (_station_m, surface_elevation_m, bed_elevation_m) in zip(
        local_points,
        channel_profile,
        strict=True,
    ):
        point["conditioned_surface_elevation_m_navd88"] = surface_elevation_m
        point["conditioned_bed_elevation_m_navd88"] = bed_elevation_m

    elevation_min_m, elevation_max_m = _write_heightfield(conditioned_dem, heightfield_path)
    _write_hillshade(conditioned_dem, hillshade_path, ground_pixel_size_m)
    draw.line(overlay_points, fill=(255, 54, 40), width=4, joint="curve")
    draw.ellipse(
        (
            overlay_points[0][0] - 7,
            overlay_points[0][1] - 7,
            overlay_points[0][0] + 7,
            overlay_points[0][1] + 7,
        ),
        fill=(80, 220, 255),
    )
    overlay.save(alignment_path)

    material_map_paths = _write_source_material_maps(
        conditioned_dem,
        naip,
        [(point["normalized_xy"][0], point["normalized_xy"][1]) for point in local_points],
        ground_width_m,
        ground_height_m,
        derived_root,
    )

    centerline_record = {
        "schema": "raftsim.production_corridor_centerline_local.v1",
        "status": "source_aligned_review_gated_not_gameplay_authority",
        "source": str(CENTERLINE_RELATIVE_PATH),
        "source_crs": "EPSG:4326",
        "service_crs": "EPSG:3857",
        "local_metric_policy": "EPSG:3857 offsets multiplied by cos(38.778 degrees); Unreal local X increases east and local Y follows source image rows southward from the northwest heightfield corner",
        "source_point_count": len(source_centerline),
        "derived_centerline_policy": "three_pass_chaikin_corner_cut_then_4m_station_resample_preserving_source_endpoints",
        "station_range_m": [local_points[0]["station_m"], local_points[-1]["station_m"]],
        "points": local_points,
    }
    centerline_path.write_text(json.dumps(centerline_record, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema": "raftsim.south_fork_production_corridor.v1",
        "river_id": "american_south_fork",
        "reach_id": "chili_bar_0_2500m",
        "status": "official_source_attached_physical_landscape_inputs_generated_review_gated",
        "production_promoted": False,
        "bounds_epsg3857": [xmin, ymin, xmax, ymax],
        "ground_span_m_approx": [ground_width_m, ground_height_m],
        "unreal_landscape": {
            "heightfield": str(heightfield_path.relative_to(repo_root)),
            "heightfield_size_px": [LANDSCAPE_SIZE, LANDSCAPE_SIZE],
            "horizontal_span_cm": [ground_width_m * 100.0, ground_height_m * 100.0],
            "xy_scale_cm_per_quad": [
                ground_width_m * 100.0 / (LANDSCAPE_SIZE - 1),
                ground_height_m * 100.0 / (LANDSCAPE_SIZE - 1),
            ],
            "elevation_min_m_navd88": elevation_min_m,
            "elevation_max_m_navd88": elevation_max_m,
            "relief_m": elevation_max_m - elevation_min_m,
            "z_scale_cm": (elevation_max_m - elevation_min_m) * 100.0 / 512.0,
            "channel_conditioning": channel_conditioning,
        },
        "source_artifacts": {
            "dem": {
                "path": str(dem_path.relative_to(repo_root)),
                "sha256": DEM_SHA256,
                "dimensions": [2048, 1445],
                "catalog_object_id": 131308,
                "title": "USGS 1 Meter 10 x69y430 CA_SierraNevada_B22",
                "acquisition_range": ["2021-11-03", "2022-09-23"],
                "vertical_datum": "NAVD 88",
                "rights": "U.S. Public Domain; credit U.S. Geological Survey",
                "rights_url": "https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map",
                "service_url": "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer",
                "export_request": {
                    "bbox": list(BBOX_EPSG3857),
                    "bbox_sr": 3857,
                    "image_sr": 3857,
                    "size": [2048, 1445],
                    "format": "tiff",
                    "pixel_type": "F32",
                    "interpolation": "RSP_BilinearInterpolation",
                    "mosaic_method": "esriMosaicLockRaster",
                    "lock_raster_ids": [131308],
                },
            },
            "aerial": {
                "path": str(naip_path.relative_to(repo_root)),
                "sha256": NAIP_SHA256,
                "dimensions": [4096, 2890],
                "catalog_object_id": 1828092,
                "name": "m_3812011_sw_10_060_20220720",
                "acquisition_date": "2022-07-20",
                "rights": "U.S. Public Domain; credit USDA/FSA/APFO NAIP",
                "rights_url": "https://agdatacommons.nal.usda.gov/articles/dataset/NAIP_Digital_Ortho_Photo_Image_Geospatial_Data_Presentation_Form_remote-sensing_image/24664908",
                "service_url": "https://gis.apfo.usda.gov/arcgis/rest/services/NAIP/USDA_CONUS_PRIME/ImageServer",
                "export_request": {
                    "bbox": list(BBOX_EPSG3857),
                    "bbox_sr": 3857,
                    "image_sr": 3857,
                    "size": [4096, 2890],
                    "format": "png",
                    "interpolation": "RSP_BilinearInterpolation",
                    "mosaic_method": "esriMosaicLockRaster",
                    "lock_raster_ids": [1828092],
                },
            },
        },
        "derived_artifacts": {
            "heightfield": {
                "path": str(heightfield_path.relative_to(repo_root)),
                "sha256": _sha256(heightfield_path),
                "dimensions": [LANDSCAPE_SIZE, LANDSCAPE_SIZE],
                "pixel_format": "16_bit_grayscale_png",
            },
            "hillshade": {
                "path": str(hillshade_path.relative_to(repo_root)),
                "sha256": _sha256(hillshade_path),
                "dimensions": [2048, 1445],
            },
            "centerline_alignment_preview": {
                "path": str(alignment_path.relative_to(repo_root)),
                "sha256": _sha256(alignment_path),
                "dimensions": [2048, 1445],
            },
            "local_centerline": {
                "path": str(centerline_path.relative_to(repo_root)),
                "sha256": _sha256(centerline_path),
                "point_count": len(local_points),
            },
            "source_material_maps": {
                key: {
                    "path": str(path.relative_to(repo_root)),
                    "sha256": _sha256(path),
                    "dimensions": [2048, 2048],
                }
                for key, path in material_map_paths.items()
            },
        },
        "review_gates": [
            "Visually review NHD centerline alignment against the locked 2022 NAIP image.",
            "Confirm horizontal transform, NAVD88 conversion, channel conditioning, banks, and stationing with a geospatial reviewer.",
            "Build a physical-scale Unreal Landscape and source-aligned river spline before replacing the validation diorama.",
            "Attach guide-reviewed rapid, eddy, access, swimmer, rescue, and sensitive-location annotations.",
            "Pass art, hazard readability, seasonal flow, desktop, and VR review before production promotion.",
        ],
    }
    manifest_path = corridor_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
