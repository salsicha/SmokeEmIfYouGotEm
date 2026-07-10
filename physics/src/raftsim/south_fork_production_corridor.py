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
    elevation_min_m, elevation_max_m = _write_heightfield(dem, heightfield_path)
    _write_hillshade(dem, hillshade_path, ground_pixel_size_m)

    centerline = _load_reach_centerline(repo_root)
    local_points = []
    overlay = naip.resize((2048, 1445), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(overlay)
    overlay_points = []
    for lon, lat, station_m in centerline:
        mercator_x, mercator_y = _web_mercator(lon, lat)
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
                    normalized_y * ground_height_m * 100.0,
                ],
            }
        )
        overlay_points.append(
            (
                int(round(normalized_x * (overlay.width - 1))),
                int(round((1.0 - normalized_y) * (overlay.height - 1))),
            )
        )
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

    centerline_record = {
        "schema": "raftsim.production_corridor_centerline_local.v1",
        "status": "source_aligned_review_gated_not_gameplay_authority",
        "source": str(CENTERLINE_RELATIVE_PATH),
        "source_crs": "EPSG:4326",
        "service_crs": "EPSG:3857",
        "local_metric_policy": "EPSG:3857 offsets multiplied by cos(38.778 degrees) for the bounded preview reach",
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
