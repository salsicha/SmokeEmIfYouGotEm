"""Plan bounded source pulls for South Fork A1 corridor windows."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .south_fork_a1_corridor_windows import (
    FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
)
from .south_fork_a1_full_reach_acquisition import FULL_REACH_ACQUISITION_RELATIVE_PATH
from .south_fork_a1_stationing import FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH


FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_pull_plan.json"
)

DIRECTED_CLIP_ROUTE_FEATURE_ID = "chili_bar_to_full_run_21_0_mile_candidate"
ADOPTED_ROUTE_FEATURE_ID = "adopted_route_chili_bar_to_salmon_falls_takeout"
DIRECTED_CLIP_STATION_END_M = 33796.224
DIRECTED_CLIP_ROUTE_BASIS = "directed_route_clip_21_0_mile_candidate"
ADOPTED_AXIS_ROUTE_BASIS = "adopted_route_axis"
_STATION_TOLERANCE_M = 1e-6

EARTH_RADIUS_M = 6_371_008.8
WEB_MERCATOR_RADIUS_M = 6_378_137.0
SOURCE_PULL_BUFFER_M = 350.0
THREE_DEP_SERVICE_URL = (
    "https://elevation.nationalmap.gov/arcgis/rest/services/"
    "3DEPElevation/ImageServer/exportImage"
)
NAIP_SERVICE_URL = (
    "https://gis.apfo.usda.gov/arcgis/rest/services/"
    "NAIP/USDA_CONUS_PRIME/ImageServer/exportImage"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon_a, lat_a = map(math.radians, a)
    lon_b, lat_b = map(math.radians, b)
    dlon = lon_b - lon_a
    dlat = lat_b - lat_a
    value = (
        math.sin(dlat * 0.5) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(dlon * 0.5) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


def _lon_lat_to_web_mercator(lon: float, lat: float) -> tuple[float, float]:
    clamped_lat = max(min(lat, 85.05112878), -85.05112878)
    x = WEB_MERCATOR_RADIUS_M * math.radians(lon)
    y = WEB_MERCATOR_RADIUS_M * math.log(
        math.tan(math.pi / 4.0 + math.radians(clamped_lat) / 2.0)
    )
    return x, y


def _bbox_wgs84(points: list[tuple[float, float]]) -> dict[str, float]:
    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return {
        "min_lon": round(min(lons), 7),
        "min_lat": round(min(lats), 7),
        "max_lon": round(max(lons), 7),
        "max_lat": round(max(lats), 7),
    }


def _bbox_epsg3857(points: list[tuple[float, float]], buffer_m: float) -> list[float]:
    mercator_points = [
        _lon_lat_to_web_mercator(lon, lat)
        for lon, lat in points
    ]
    xs = [point[0] for point in mercator_points]
    ys = [point[1] for point in mercator_points]
    return [
        round(min(xs) - buffer_m, 3),
        round(min(ys) - buffer_m, 3),
        round(max(xs) + buffer_m, 3),
        round(max(ys) + buffer_m, 3),
    ]


def _export_url(service_url: str, params: dict[str, Any]) -> str:
    encoded = urlencode(params, doseq=False)
    return f"{service_url}?{encoded}"


def _route_coordinates_with_station(
    route_geojson: dict[str, Any],
    feature_id: str = DIRECTED_CLIP_ROUTE_FEATURE_ID,
) -> list[dict[str, Any]]:
    route_feature = next(
        feature
        for feature in route_geojson["features"]
        if feature["id"] == feature_id
    )
    coordinates = [
        (float(point[0]), float(point[1]))
        for point in route_feature["geometry"]["coordinates"]
    ]
    full_station_m = float(route_feature["properties"]["station_end_m"])
    cumulative_m = 0.0
    cumulative_geometry = [0.0]
    for start, stop in zip(coordinates, coordinates[1:], strict=False):
        cumulative_m += _haversine_m(start, stop)
        cumulative_geometry.append(cumulative_m)
    scale = 0.0 if cumulative_m <= 0.0 else full_station_m / cumulative_m
    return [
        {
            "lon_lat": coordinate,
            "approx_station_m": cumulative_geometry[index] * scale,
        }
        for index, coordinate in enumerate(coordinates)
    ]


def _points_for_window(
    route_points: list[dict[str, Any]],
    station_start_m: float,
    station_end_m: float,
) -> list[tuple[float, float]]:
    points = [
        point["lon_lat"]
        for point in route_points
        if station_start_m <= point["approx_station_m"] <= station_end_m
    ]
    if not points:
        raise ValueError(
            f"No route points for window {station_start_m}..{station_end_m}"
        )
    return points


def _terrain_export_request(bbox_epsg3857: list[float]) -> dict[str, Any]:
    params = {
        "bbox": ",".join(str(value) for value in bbox_epsg3857),
        "bboxSR": 3857,
        "imageSR": 3857,
        "size": "2048,2048",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    }
    return {
        "service_url": THREE_DEP_SERVICE_URL,
        "query_url": _export_url(THREE_DEP_SERVICE_URL, params),
        "bbox_epsg3857": bbox_epsg3857,
        "size_px": [2048, 2048],
        "format": "tiff",
        "pixel_type": "F32",
        "downloaded": False,
    }


def _aerial_export_request(bbox_epsg3857: list[float]) -> dict[str, Any]:
    params = {
        "bbox": ",".join(str(value) for value in bbox_epsg3857),
        "bboxSR": 3857,
        "imageSR": 3857,
        "size": "4096,4096",
        "format": "png",
        "f": "image",
    }
    return {
        "service_url": NAIP_SERVICE_URL,
        "query_url": _export_url(NAIP_SERVICE_URL, params),
        "bbox_epsg3857": bbox_epsg3857,
        "size_px": [4096, 4096],
        "format": "png",
        "downloaded": False,
    }


def build_south_fork_a1_window_source_pull_plan(repo_root: Path) -> dict[str, Any]:
    """Build metadata-only source-pull requests for each A1 corridor window."""

    repo_root = repo_root.resolve()
    window_manifest = _load_json(repo_root, FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH)
    route_clips = _load_json(repo_root, FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH)
    adopted_route = _load_json(repo_root, FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH)
    clip_route_points = _route_coordinates_with_station(route_clips)
    adopted_route_points = _route_coordinates_with_station(
        adopted_route, ADOPTED_ROUTE_FEATURE_ID
    )

    windows: list[dict[str, Any]] = []
    for window in window_manifest["windows"]:
        station_start_m = float(window["station_start_m"])
        station_end_m = float(window["station_end_m"])
        if station_end_m <= DIRECTED_CLIP_STATION_END_M + _STATION_TOLERANCE_M:
            route_basis = DIRECTED_CLIP_ROUTE_BASIS
            route_points = clip_route_points
        else:
            route_basis = ADOPTED_AXIS_ROUTE_BASIS
            route_points = adopted_route_points
        points = _points_for_window(route_points, station_start_m, station_end_m)
        bbox3857 = _bbox_epsg3857(points, SOURCE_PULL_BUFFER_M)
        window_id = window["window_id"]
        windows.append(
            {
                "window_id": window_id,
                "display_name": window["display_name"],
                "station_start_m": station_start_m,
                "station_end_m": station_end_m,
                "source_pull_status": "planned_not_downloaded",
                "existing_artifact": window.get("existing_artifact"),
                "route_basis": route_basis,
                "route_point_count": len(points),
                "bounds_wgs84": _bbox_wgs84(points),
                "bounds_epsg3857_buffered": bbox3857,
                "buffer_m": SOURCE_PULL_BUFFER_M,
                "terrain_3dep_export": _terrain_export_request(bbox3857),
                "aerial_naip_export": _aerial_export_request(bbox3857),
                "expected_outputs": {
                    "terrain_dem": (
                        "physics/data/real_world/south_fork_american_chili_bar/"
                        f"production_corridor/full_reach_windows/{window_id}/source/3dep_dem.tif"
                    ),
                    "aerial_imagery": (
                        "physics/data/real_world/south_fork_american_chili_bar/"
                        f"production_corridor/full_reach_windows/{window_id}/source/naip.png"
                    ),
                    "window_manifest": (
                        "physics/data/real_world/south_fork_american_chili_bar/"
                        f"production_corridor/full_reach_windows/{window_id}/manifest.json"
                    ),
                },
                "production_promoted": False,
            }
        )

    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_plan.v1",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": window_manifest["river_id"],
        "status": "bounded_window_source_requests_planned_not_downloaded",
        "production_promoted": False,
        "inputs": {
            "full_reach_acquisition_plan": FULL_REACH_ACQUISITION_RELATIVE_PATH,
            "corridor_window_manifest": (
                FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH
            ),
            "directed_route_clips": FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
            "adopted_route_geojson": FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
        },
        "policy": {
            "downloads_performed": False,
            "authority": "source_request_manifest_only_not_source_data",
            "reason": (
                "A1 needs full-reach terrain and imagery, but each source pull must "
                "be bounded, reproducible, and reviewed before committing source or "
                "derived corridor assets."
            ),
            "do_not_promote_from_urls_alone": True,
        },
        "service_sources": {
            "terrain_3dep": {
                "provider": "USGS 3D Elevation Program",
                "service_url": THREE_DEP_SERVICE_URL,
            },
            "aerial_naip": {
                "provider": "USDA/FSA/APFO NAIP",
                "service_url": NAIP_SERVICE_URL,
            },
        },
        "windows": windows,
        "coverage_summary": {
            "window_count": len(windows),
            "planned_download_count": 0,
            "planned_request_count": len(windows) * 2,
            "all_windows_have_terrain_and_imagery_requests": all(
                window["terrain_3dep_export"]["query_url"]
                and window["aerial_naip_export"]["query_url"]
                for window in windows
            ),
        },
        "promotion_gate": {
            "can_download_without_review": False,
            "can_promote_source_assets": False,
            "can_generate_full_reach_landscapes": False,
            "exit_criteria": [
                "Review every bbox against the exact downstream anchor decision.",
                "Perform bounded downloads with hashes and terms metadata recorded.",
                "Generate per-window manifests and stitched validation previews.",
                "Pass geospatial/art review before Unreal landscape import.",
            ],
        },
    }


def write_south_fork_a1_window_source_pull_plan(repo_root: Path) -> Path:
    payload = build_south_fork_a1_window_source_pull_plan(repo_root)
    path = repo_root / FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
