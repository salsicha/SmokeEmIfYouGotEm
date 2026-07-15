"""Build source-recorded Zambezi and Futaleufu production corridor packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageDraw


EARTH_RADIUS_M = 6_371_000.0
LANDSCAPE_SIZE = 2017
MATERIAL_SIZE = 2048
ROUTE_SCHEMA = "raftsim.international_production_corridor.v1"


@dataclass(frozen=True)
class DemTile:
    path: str
    south: int
    west: int
    url: str


@dataclass(frozen=True)
class SentinelScene:
    item_id: str
    datetime_utc: str
    cloud_cover_percent: float
    tile_id: str
    visual_url: str


@dataclass(frozen=True)
class RiverCorridorDefinition:
    river_id: str
    display_name: str
    relative_root: str
    output_slug: str
    route_source_file: str
    route_query: str
    way_ids: tuple[int, ...]
    route_geometry_authority: str
    start_seed_lon_lat: tuple[float, float]
    end_seed_lon_lat: tuple[float, float] | None
    end_station_m: float | None
    route_buffer_m: float
    channel_half_width_m: float
    channel_feather_width_m: float
    channel_profile_smoothing_m: float
    channel_maximum_downstream_slope: float
    channel_bed_depth_m: float
    channel_maximum_cut_m: float
    channel_maximum_fill_m: float
    dem_tiles: tuple[DemTile, ...]
    sentinel_search_file: str
    sentinel_scenes: tuple[SentinelScene, ...]
    sentinel_visual_file: str
    terrain_acquisition_lead_file: str | None
    centerline_review_manifest_file: str | None
    endpoint_evidence: tuple[dict[str, Any], ...]
    flow_context: dict[str, Any]
    environment_contract: dict[str, Any]


ZAMBEZI = RiverCorridorDefinition(
    river_id="zambezi_batoka_gorge",
    display_name="Zambezi River: Boiling Pot to Mukuni Beach",
    relative_root="physics/data/real_world/zambezi_batoka_gorge",
    output_slug="boiling_pot_to_mukuni_beach",
    route_source_file="hydrography/source/osm_batoka_river_ways.json",
    route_query=(
        "[out:json][timeout:60];way[waterway=river]"
        "(-18.08,25.78,-17.86,26.08);out tags geom;"
    ),
    way_ids=(765343870, 717945896, 31300625, 31300571),
    route_geometry_authority=(
        "low_precision_osm_international_boundary_trace_cross_reference_not_surveyed_centerline"
    ),
    start_seed_lon_lat=(25.858278, -17.926081),
    end_seed_lon_lat=None,
    end_station_m=30_000.0,
    route_buffer_m=2_000.0,
    channel_half_width_m=60.0,
    channel_feather_width_m=90.0,
    channel_profile_smoothing_m=500.0,
    channel_maximum_downstream_slope=0.025,
    channel_bed_depth_m=2.0,
    channel_maximum_cut_m=240.0,
    channel_maximum_fill_m=0.0,
    dem_tiles=(
        DemTile(
            path="terrain/source/copernicus_dem_glo30_S18_E025.tif",
            south=-18,
            west=25,
            url=(
                "https://copernicus-dem-30m.s3.amazonaws.com/"
                "Copernicus_DSM_COG_10_S18_00_E025_00_DEM/"
                "Copernicus_DSM_COG_10_S18_00_E025_00_DEM.tif"
            ),
        ),
        DemTile(
            path="terrain/source/copernicus_dem_glo30_S18_E026.tif",
            south=-18,
            west=26,
            url=(
                "https://copernicus-dem-30m.s3.amazonaws.com/"
                "Copernicus_DSM_COG_10_S18_00_E026_00_DEM/"
                "Copernicus_DSM_COG_10_S18_00_E026_00_DEM.tif"
            ),
        ),
    ),
    sentinel_search_file="imagery/source/earth_search_stac_response.json",
    sentinel_scenes=(
        SentinelScene(
            item_id="S2C_35KLA_20260610_0_L2A",
            datetime_utc="2026-06-10T08:35:11.763000Z",
            cloud_cover_percent=0.000003,
            tile_id="35KLA",
            visual_url=(
                "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                "sentinel-s2-l2a-cogs/35/K/LA/2026/6/"
                "S2C_35KLA_20260610_0_L2A/TCI.tif"
            ),
        ),
        SentinelScene(
            item_id="S2C_35KMA_20260610_0_L2A",
            datetime_utc="2026-06-10T08:35:08.983000Z",
            cloud_cover_percent=0.0,
            tile_id="35KMA",
            visual_url=(
                "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                "sentinel-s2-l2a-cogs/35/K/MA/2026/6/"
                "S2C_35KMA_20260610_0_L2A/TCI.tif"
            ),
        ),
    ),
    sentinel_visual_file="imagery/source/sentinel2_20260610_route_visual.png",
    terrain_acquisition_lead_file=(
        "terrain/source/batoka_high_resolution_terrain_acquisition_leads.json"
    ),
    centerline_review_manifest_file=(
        "hydrography/review/sentinel2_20260610_centerline_candidate_manifest.json"
    ),
    endpoint_evidence=(
        {
            "endpoint": "put_in",
            "name": "Boiling Pot",
            "policy": "nearest_named-mainstem vertex",
            "confidence": "high",
            "source": "OpenStreetMap route geometry plus published rafting access descriptions",
        },
        {
            "endpoint": "take_out",
            "name": "Mukuni Beach",
            "policy": "30 km downstream station from Boiling Pot",
            "confidence": "review_gated",
            "source": "published Rapid 25 / Mukuni Beach stationing; exact beach bank point needs local guide review",
        },
    ),
    flow_context={
        "provider": "Zambezi River Authority",
        "station": "Victoria Falls - Nana's Farm Station",
        "source_url": "https://zambezira.org/hydrology/river-flows",
        "units": "m3/s",
        "relation_to_reach": "upstream control station for the below-falls Batoka Gorge run",
        "published_reference_statistics": {
            "long_term_mean_annual_flow_m3_s": 1100.0,
            "historical_maximum_m3_s": 10000.0,
            "historical_maximum_month": "1958-03",
            "lowest_annual_mean_m3_s": 390.0,
            "lowest_annual_mean_water_year": "1995/96",
        },
        "planning_bands": [
            {"id": "low_water_technical", "range_m3_s": [350.0, 900.0]},
            {"id": "normal_big_water", "range_m3_s": [900.0, 2200.0]},
            {"id": "high_water", "range_m3_s": [2200.0, 4500.0]},
            {"id": "extreme_review_only", "range_m3_s": [4500.0, 10000.0]},
        ],
        "promotion_gate": (
            "Planning bands are visual/gameplay hypotheses until a Zambezi guide validates rapid-specific "
            "lines, closure seasons, hole washout, access, and station-to-reach lag."
        ),
    },
    environment_contract={
        "geology": "steep jointed basalt gorge",
        "water": "warm brown-green high-volume river with flow-dependent wave trains, holes, boils, and laterals",
        "ecology": "southern African gorge woodland and riparian scrub",
        "atmosphere": "warm haze, waterfall moisture, localized spray and mist",
        "procedural_layers": ["basalt_strata", "wet_basalt", "talus", "gorge_woodland", "spray", "mist", "foam"],
    },
)


FUTALEUFU = RiverCorridorDefinition(
    river_id="futaleufu_terminator",
    display_name="Futaleufu: Rio Azul Swinging Bridge to The Pasarela",
    relative_root="physics/data/real_world/futaleufu_river_chile",
    output_slug="rio_azul_swinging_bridge_to_pasarela",
    route_source_file="hydrography/source/osm_futaleufu_river_ways.json",
    route_query=(
        "[out:json][timeout:60];way[waterway=river]"
        "(-43.40,-72.20,-43.00,-71.60);out tags geom;"
    ),
    way_ids=(213541728, 265661722),
    route_geometry_authority=(
        "osm_named_river_cross_reference_with_rapid_tags_not_surveyed_centerline"
    ),
    start_seed_lon_lat=(-72.0141746, -43.3076729),
    end_seed_lon_lat=(-72.0583818, -43.3516642),
    end_station_m=None,
    route_buffer_m=1_500.0,
    channel_half_width_m=48.0,
    channel_feather_width_m=75.0,
    channel_profile_smoothing_m=400.0,
    channel_maximum_downstream_slope=0.020,
    channel_bed_depth_m=1.8,
    channel_maximum_cut_m=25.0,
    channel_maximum_fill_m=0.0,
    dem_tiles=(
        DemTile(
            path="terrain/source/copernicus_dem_glo30_S44_W073.tif",
            south=-44,
            west=-73,
            url=(
                "https://copernicus-dem-30m.s3.amazonaws.com/"
                "Copernicus_DSM_COG_10_S44_00_W073_00_DEM/"
                "Copernicus_DSM_COG_10_S44_00_W073_00_DEM.tif"
            ),
        ),
        DemTile(
            path="terrain/source/copernicus_dem_glo30_S44_W072.tif",
            south=-44,
            west=-72,
            url=(
                "https://copernicus-dem-30m.s3.amazonaws.com/"
                "Copernicus_DSM_COG_10_S44_00_W072_00_DEM/"
                "Copernicus_DSM_COG_10_S44_00_W072_00_DEM.tif"
            ),
        ),
    ),
    sentinel_search_file="imagery/source/earth_search_stac_response.json",
    sentinel_scenes=(
        SentinelScene(
            item_id="S2B_18GYS_20260104_0_L2A",
            datetime_utc="2026-01-04T14:45:04.391000Z",
            cloud_cover_percent=0.00152,
            tile_id="18GYS",
            visual_url=(
                "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                "sentinel-s2-l2a-cogs/18/G/YS/2026/1/"
                "S2B_18GYS_20260104_0_L2A/TCI.tif"
            ),
        ),
        SentinelScene(
            item_id="S2B_18GYT_20260104_0_L2A",
            datetime_utc="2026-01-04T14:44:49.998000Z",
            cloud_cover_percent=0.015259,
            tile_id="18GYT",
            visual_url=(
                "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                "sentinel-s2-l2a-cogs/18/G/YT/2026/1/"
                "S2B_18GYT_20260104_0_L2A/TCI.tif"
            ),
        ),
    ),
    sentinel_visual_file="imagery/source/sentinel2_20260104_route_visual.png",
    terrain_acquisition_lead_file=None,
    centerline_review_manifest_file=None,
    endpoint_evidence=(
        {
            "endpoint": "put_in",
            "name": "Rio Azul Swinging Bridge",
            "policy": "nearest Rio Azul centerline point to OSM track bridge 635437017",
            "confidence": "high_review_gated",
            "source": "OSM bridge geometry plus published Terminator-section access description",
        },
        {
            "endpoint": "take_out",
            "name": "The Pasarela",
            "policy": "nearest Futaleufu centerline point to OSM track bridge 165621980",
            "confidence": "high_review_gated",
            "source": "OSM bridge geometry plus published Terminator-section takeout description",
        },
    ),
    flow_context={
        "provider": "Direccion General de Aguas, Chile",
        "station": "Rio Futaleufu ante junta rio Malito",
        "station_code": "10704002-1",
        "station_lon_lat": [-72.1075, -43.449166],
        "units": "m3/s",
        "relation_to_reach": "downstream mainstem station; route translation and travel-time review required",
        "official_monthly_mean_m3_s_2020_2023": {
            "jan": 275.23,
            "feb": 160.30,
            "mar": 130.61,
            "apr": 168.58,
            "may": 222.89,
            "jun": 410.51,
            "jul": 320.07,
            "aug": 256.56,
            "sep": 223.64,
            "oct": 208.66,
            "nov": 289.29,
            "dec": 290.20,
        },
        "source_urls": [
            "https://climatologia.meteochile.gob.cl/application/informacion/fichaDeEstacion/430011",
            "https://www.camara.cl/verdoc.aspx?prmID=132134&prmTIPO=OFICIO_FISCALIZACION_RESPUESTA",
        ],
        "planning_bands": [
            {"id": "low_technical", "range_m3_s": [60.0, 160.0]},
            {"id": "normal_runnable", "range_m3_s": [160.0, 300.0]},
            {"id": "high_big_water", "range_m3_s": [300.0, 500.0]},
            {"id": "unsafe_review_only", "range_m3_s": [500.0, 900.0]},
        ],
        "promotion_gate": (
            "Planning bands remain review-only until DGA time-series acquisition, upstream release/rain/snowmelt "
            "interpretation, route translation, and Futaleufu guide validation are complete."
        ),
    },
    environment_contract={
        "geology": "glacial Patagonian valley with granite and metamorphic boulder gardens",
        "water": "clear turquoise big water with powerful wave trains, holes, pillows, and boulder push",
        "ecology": "temperate rainforest, coigue-dominant woodland, riparian shrubs, and gravel bars",
        "atmosphere": "cool humid valley light, mountain cloud, localized spray and mist",
        "procedural_layers": ["granite", "wet_boulders", "gravel_bars", "temperate_rainforest", "foam", "spray", "mist"],
    },
)


DEFINITIONS = {definition.river_id: definition for definition in (ZAMBEZI, FUTALEUFU)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, first)
    lon2, lat2 = map(math.radians, second)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat * 0.5) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon * 0.5) ** 2
    return EARTH_RADIUS_M * 2.0 * math.asin(math.sqrt(a))


def _nearest_index(points: list[tuple[float, float]], seed: tuple[float, float]) -> int:
    return min(range(len(points)), key=lambda index: _distance_m(points[index], seed))


def _stationed(points: list[tuple[float, float]]) -> list[dict[str, float]]:
    result: list[dict[str, float]] = []
    station = 0.0
    for index, point in enumerate(points):
        if index:
            station += _distance_m(points[index - 1], point)
        result.append({"station_m": station, "lon": point[0], "lat": point[1]})
    return result


def _clip_at_station(
    points: list[tuple[float, float]],
    station_m: float,
) -> list[tuple[float, float]]:
    if station_m <= 0.0:
        raise ValueError("end station must be positive")
    result = [points[0]]
    accumulated = 0.0
    for first, second in zip(points, points[1:], strict=False):
        segment = _distance_m(first, second)
        if accumulated + segment >= station_m:
            fraction = (station_m - accumulated) / max(segment, 1e-9)
            result.append(
                (
                    first[0] + (second[0] - first[0]) * fraction,
                    first[1] + (second[1] - first[1]) * fraction,
                )
            )
            return result
        result.append(second)
        accumulated += segment
    raise ValueError(f"route is only {accumulated:.1f} m; cannot clip at {station_m:.1f} m")


def extract_route(
    overpass_payload: dict[str, Any],
    definition: RiverCorridorDefinition,
    *,
    maximum_join_gap_m: float = 125.0,
) -> list[tuple[float, float]]:
    ways = {int(element["id"]): element for element in overpass_payload.get("elements", []) if element.get("type") == "way"}
    missing = [way_id for way_id in definition.way_ids if way_id not in ways]
    if missing:
        raise ValueError(f"missing configured OSM ways: {missing}")

    route: list[tuple[float, float]] = []
    for way_index, way_id in enumerate(definition.way_ids):
        geometry = [(float(point["lon"]), float(point["lat"])) for point in ways[way_id]["geometry"]]
        if len(geometry) < 2:
            raise ValueError(f"OSM way {way_id} has fewer than two points")
        if not route:
            if way_index + 1 < len(definition.way_ids):
                next_geometry = ways[definition.way_ids[way_index + 1]]["geometry"]
                next_endpoints = [
                    (float(next_geometry[0]["lon"]), float(next_geometry[0]["lat"])),
                    (float(next_geometry[-1]["lon"]), float(next_geometry[-1]["lat"])),
                ]
                first_connection = min(_distance_m(geometry[0], point) for point in next_endpoints)
                last_connection = min(_distance_m(geometry[-1], point) for point in next_endpoints)
                if first_connection < last_connection:
                    geometry.reverse()
            elif _distance_m(geometry[-1], definition.start_seed_lon_lat) < _distance_m(
                geometry[0], definition.start_seed_lon_lat
            ):
                geometry.reverse()
            route.extend(geometry)
            continue
        if _distance_m(route[-1], geometry[-1]) < _distance_m(route[-1], geometry[0]):
            geometry.reverse()
        gap = _distance_m(route[-1], geometry[0])
        if gap > maximum_join_gap_m:
            raise ValueError(f"OSM route gap before way {way_id} is {gap:.1f} m")
        if gap < 0.25:
            route.extend(geometry[1:])
        else:
            route.extend(geometry)

    start_index = _nearest_index(route, definition.start_seed_lon_lat)
    route = route[start_index:]
    if definition.end_seed_lon_lat is not None:
        end_index = _nearest_index(route, definition.end_seed_lon_lat)
        if end_index < 1:
            raise ValueError("configured end seed is not downstream of the start seed")
        route = route[: end_index + 1]
    elif definition.end_station_m is not None:
        route = _clip_at_station(route, definition.end_station_m)
    else:
        raise ValueError("route definition needs an end seed or end station")
    if len(route) < 2:
        raise ValueError("route extraction produced fewer than two points")
    return route


def _route_bbox(points: list[tuple[float, float]], buffer_m: float) -> tuple[float, float, float, float]:
    center_lat = sum(point[1] for point in points) / len(points)
    lat_buffer = buffer_m / 111_320.0
    lon_buffer = buffer_m / (111_320.0 * math.cos(math.radians(center_lat)))
    return (
        min(point[0] for point in points) - lon_buffer,
        min(point[1] for point in points) - lat_buffer,
        max(point[0] for point in points) + lon_buffer,
        max(point[1] for point in points) + lat_buffer,
    )


def _load_dem_mosaic(root: Path, tiles: Iterable[DemTile]) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    tile_list = list(tiles)
    west_values = sorted({tile.west for tile in tile_list})
    south_values = sorted({tile.south for tile in tile_list}, reverse=True)
    by_origin = {(tile.south, tile.west): tile for tile in tile_list}
    rows: list[np.ndarray] = []
    expected_shape: tuple[int, int] | None = None
    for south in south_values:
        columns: list[np.ndarray] = []
        for west in west_values:
            tile = by_origin.get((south, west))
            if tile is None:
                raise ValueError(f"missing DEM tile at south={south}, west={west}")
            array = np.asarray(Image.open(root / tile.path), dtype=np.float32)
            if array.ndim == 3:
                array = array[..., 0]
            if expected_shape is None:
                expected_shape = array.shape
            elif array.shape != expected_shape:
                raise ValueError("DEM tiles do not share dimensions")
            columns.append(array)
        rows.append(np.concatenate(columns, axis=1))
    mosaic = np.concatenate(rows, axis=0)
    return mosaic, (float(min(west_values)), float(min(south_values)), float(max(west_values) + 1), float(max(south_values) + 1))


def _crop_geographic(
    array: np.ndarray,
    source_bbox: tuple[float, float, float, float],
    target_bbox: tuple[float, float, float, float],
) -> np.ndarray:
    source_west, source_south, source_east, source_north = source_bbox
    west, south, east, north = target_bbox
    height, width = array.shape[:2]
    left = max(0, int(math.floor((west - source_west) / (source_east - source_west) * width)))
    right = min(width, int(math.ceil((east - source_west) / (source_east - source_west) * width)))
    top = max(0, int(math.floor((source_north - north) / (source_north - source_south) * height)))
    bottom = min(height, int(math.ceil((source_north - south) / (source_north - source_south) * height)))
    if right - left < 2 or bottom - top < 2:
        raise ValueError("corridor crop does not intersect the DEM mosaic")
    return array[top:bottom, left:right].copy()


def _physical_size_m(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bbox
    center_lat = (south + north) * 0.5
    width = _distance_m((west, center_lat), (east, center_lat))
    height = _distance_m(((west + east) * 0.5, south), ((west + east) * 0.5, north))
    return width, height


def _write_route_artifacts(
    output_root: Path,
    definition: RiverCorridorDefinition,
    points: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
) -> dict[str, str]:
    hydrography_root = output_root / "hydrography"
    hydrography_root.mkdir(parents=True, exist_ok=True)
    stationed = _stationed(points)
    geojson_path = hydrography_root / "route_centerline.geojson"
    geojson_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "river_id": definition.river_id,
                            "route": definition.display_name,
                            "source": "OpenStreetMap named river geometry",
                            "license": "ODbL-1.0",
                            "status": "route_cross_reference_pending_local_guide_review",
                        },
                        "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lon, lat in points]},
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    stationing_path = hydrography_root / "route_stationing.json"
    stationing_path.write_text(
        json.dumps(
            {
                "schema": "raftsim.route_stationing.v1",
                "river_id": definition.river_id,
                "length_m": stationed[-1]["station_m"],
                "samples": stationed,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    west, south, east, north = bbox
    center_lat = (south + north) * 0.5
    cos_lat = math.cos(math.radians(center_lat))
    local = [
        {
            **sample,
            "x_m": (sample["lon"] - west) * 111_320.0 * cos_lat,
            "y_m": (north - sample["lat"]) * 111_320.0,
            "unreal_local_cm": [
                (sample["lon"] - west) * 111_320.0 * cos_lat * 100.0,
                (north - sample["lat"]) * 111_320.0 * 100.0,
            ],
        }
        for sample in stationed
    ]
    local_path = hydrography_root / "centerline_local.json"
    local_path.write_text(
        json.dumps(
            {
                "schema": "raftsim.local_centerline.v1",
                "river_id": definition.river_id,
                "bounds_wgs84": [west, south, east, north],
                "local_metric_policy": (
                    "equirectangular offsets at corridor center latitude; Unreal local X increases east "
                    "and local Y follows source image rows southward from the northwest heightfield corner"
                ),
                "points": local,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "centerline_geojson": str(geojson_path),
        "stationing": str(stationing_path),
        "centerline_local": str(local_path),
    }


def _sample_bilinear(array: np.ndarray, x: float, y: float) -> float:
    height, width = array.shape
    x = float(np.clip(x, 0.0, width - 1.0))
    y = float(np.clip(y, 0.0, height - 1.0))
    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    tx = x - x0
    ty = y - y0
    top = float(array[y0, x0]) * (1.0 - tx) + float(array[y0, x1]) * tx
    bottom = float(array[y1, x0]) * (1.0 - tx) + float(array[y1, x1]) * tx
    return top * (1.0 - ty) + bottom * ty


def _condition_visual_channel(
    dem: np.ndarray,
    physical_size: tuple[float, float],
    points: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
    definition: RiverCorridorDefinition,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Condition coarse visual terrain without changing solver or bathymetry authority."""

    if dem.ndim != 2 or min(dem.shape) < 2:
        raise ValueError("visual channel conditioning requires a two-dimensional DEM")
    if len(points) < 2:
        raise ValueError("visual channel conditioning requires at least two route points")

    width_m, height_m = physical_size
    west, south, east, north = bbox
    center_lat = (south + north) * 0.5
    cos_lat = math.cos(math.radians(center_lat))
    stationed = _stationed(points)
    stations = np.asarray([sample["station_m"] for sample in stationed], dtype=np.float64)
    route_xy = np.asarray(
        [
            (
                (sample["lon"] - west) * 111_320.0 * cos_lat,
                (north - sample["lat"]) * 111_320.0,
            )
            for sample in stationed
        ],
        dtype=np.float64,
    )
    route_xy[:, 0] = np.clip(route_xy[:, 0], 0.0, width_m)
    route_xy[:, 1] = np.clip(route_xy[:, 1], 0.0, height_m)

    raster_height, raster_width = dem.shape
    raw_profile = np.asarray(
        [
            _sample_bilinear(
                dem,
                xy[0] / width_m * (raster_width - 1),
                xy[1] / height_m * (raster_height - 1),
            )
            for xy in route_xy
        ],
        dtype=np.float64,
    )
    smoothing_radius = max(definition.channel_profile_smoothing_m, 1.0)
    station_distance = np.abs(stations[:, None] - stations[None, :])
    smoothing_weights = np.clip(1.0 - station_distance / smoothing_radius, 0.0, 1.0)
    smoothed_profile = (
        smoothing_weights @ raw_profile / np.maximum(smoothing_weights.sum(axis=1), 1.0)
    )

    lower_envelope = np.minimum.accumulate(np.minimum(raw_profile, smoothed_profile))
    conditioned_surface = lower_envelope.copy()
    for index in range(len(conditioned_surface) - 2, -1, -1):
        station_delta = max(stations[index + 1] - stations[index], 0.001)
        maximum_allowed = (
            conditioned_surface[index + 1]
            + definition.channel_maximum_downstream_slope * station_delta
        )
        conditioned_surface[index] = min(lower_envelope[index], maximum_allowed)
    conditioned_bed = conditioned_surface - definition.channel_bed_depth_m

    best_weight = np.zeros_like(dem, dtype=np.float32)
    target_bed = np.zeros_like(dem, dtype=np.float32)
    outer_width_m = definition.channel_half_width_m + definition.channel_feather_width_m
    for segment_index in range(len(route_xy) - 1):
        start = route_xy[segment_index]
        end = route_xy[segment_index + 1]
        direction = end - start
        length_squared = float(np.dot(direction, direction))
        if length_squared <= 1.0e-9:
            continue

        min_col = max(
            0,
            int(math.floor((min(start[0], end[0]) - outer_width_m) / width_m * (raster_width - 1))),
        )
        max_col = min(
            raster_width - 1,
            int(math.ceil((max(start[0], end[0]) + outer_width_m) / width_m * (raster_width - 1))),
        )
        min_row = max(
            0,
            int(math.floor((min(start[1], end[1]) - outer_width_m) / height_m * (raster_height - 1))),
        )
        max_row = min(
            raster_height - 1,
            int(math.ceil((max(start[1], end[1]) + outer_width_m) / height_m * (raster_height - 1))),
        )
        if min_col > max_col or min_row > max_row:
            continue

        world_x = np.arange(min_col, max_col + 1, dtype=np.float64) / (raster_width - 1) * width_m
        world_y = np.arange(min_row, max_row + 1, dtype=np.float64) / (raster_height - 1) * height_m
        grid_x, grid_y = np.meshgrid(world_x, world_y)
        relative_x = grid_x - start[0]
        relative_y = grid_y - start[1]
        segment_t = np.clip(
            (relative_x * direction[0] + relative_y * direction[1]) / length_squared,
            0.0,
            1.0,
        )
        closest_x = start[0] + segment_t * direction[0]
        closest_y = start[1] + segment_t * direction[1]
        distance = np.hypot(grid_x - closest_x, grid_y - closest_y)
        feather_t = np.clip(
            (distance - definition.channel_half_width_m)
            / max(definition.channel_feather_width_m, 0.001),
            0.0,
            1.0,
        )
        blend = 1.0 - feather_t * feather_t * (3.0 - 2.0 * feather_t)
        segment_bed = (
            conditioned_bed[segment_index] * (1.0 - segment_t)
            + conditioned_bed[segment_index + 1] * segment_t
        )

        weight_view = best_weight[min_row : max_row + 1, min_col : max_col + 1]
        target_view = target_bed[min_row : max_row + 1, min_col : max_col + 1]
        source_view = dem[min_row : max_row + 1, min_col : max_col + 1]
        segment_bed = np.clip(
            segment_bed,
            source_view - definition.channel_maximum_cut_m,
            source_view + definition.channel_maximum_fill_m,
        )
        replace_mask = blend > weight_view
        weight_view[replace_mask] = blend[replace_mask].astype(np.float32)
        target_view[replace_mask] = segment_bed[replace_mask].astype(np.float32)

    conditioned = dem.astype(np.float32, copy=True)
    conditioned = conditioned * (1.0 - best_weight) + target_bed * best_weight
    delta = conditioned - dem
    modified = best_weight > 1.0e-6
    station_delta = np.maximum(np.diff(stations), 0.001)
    downstream_slopes = (conditioned_surface[:-1] - conditioned_surface[1:]) / station_delta
    raw_rises = np.maximum(np.diff(raw_profile), 0.0)
    maximum_cut = max(0.0, -float(np.min(delta[modified]))) if np.any(modified) else 0.0
    maximum_fill = max(0.0, float(np.max(delta[modified]))) if np.any(modified) else 0.0
    if maximum_cut < 0.001:
        maximum_cut = 0.0
    if maximum_fill < 0.001:
        maximum_fill = 0.0
    profile_samples = [
        {
            "station_m": round(float(stations[index]), 3),
            "raw_dem_elevation_m": round(float(raw_profile[index]), 4),
            "smoothed_surface_elevation_m": round(float(smoothed_profile[index]), 4),
            "conditioned_surface_elevation_m": round(float(conditioned_surface[index]), 4),
            "conditioned_bed_elevation_m": round(float(conditioned_bed[index]), 4),
        }
        for index in range(len(stations))
    ]
    metadata: dict[str, Any] = {
        "schema": "raftsim.visual_channel_conditioning.v1",
        "status": "bounded_visual_terrain_conditioning_review_gated",
        "river_id": definition.river_id,
        "authority": {
            "scope": "Unreal visual terrain and render-water alignment only",
            "changes_custom_cpp_solver_state": False,
            "changes_collision_or_raft_forces": False,
            "surveyed_bathymetry": False,
            "may_hide_conservation_or_parity_failures": False,
        },
        "parameters": {
            "channel_half_width_m": definition.channel_half_width_m,
            "channel_feather_width_m": definition.channel_feather_width_m,
            "profile_smoothing_radius_m": definition.channel_profile_smoothing_m,
            "maximum_downstream_slope": definition.channel_maximum_downstream_slope,
            "bed_depth_below_visual_surface_m": definition.channel_bed_depth_m,
            "maximum_terrain_cut_m": definition.channel_maximum_cut_m,
            "maximum_terrain_fill_m": definition.channel_maximum_fill_m,
            "profile_policy": "raw_and_triangular_smoothed_lower_envelope_then_backward_nonrising_slope_bound",
            "raster_policy": "smoothstep_core_and_feather_cut_or_fill_clamped_to_explicit_bounds",
        },
        "measurements": {
            "route_sample_count": len(stations),
            "modified_raster_sample_count": int(np.count_nonzero(np.abs(delta) > 0.01)),
            "maximum_cut_m": round(maximum_cut, 4),
            "maximum_fill_m": round(maximum_fill, 4),
            "raw_profile_total_upstream_rise_m": round(float(raw_rises.sum()), 4),
            "conditioned_profile_maximum_upstream_rise_m": round(
                float(max(0.0, float(np.max(np.diff(conditioned_surface))))), 6
            ),
            "conditioned_profile_maximum_downstream_slope": round(
                float(max(0.0, float(np.max(downstream_slopes)))), 6
            ),
            "conditioned_profile_total_drop_m": round(
                float(conditioned_surface[0] - conditioned_surface[-1]), 4
            ),
        },
        "profile_samples": profile_samples,
        "promotion_gates": [
            "geospatial reviewer approves cut/fill bounds and source alignment",
            "local guide reviews channel placement and river-level corridor silhouettes",
            "higher-resolution terrain or surveyed bathymetry replaces this visual approximation where available",
            "custom C++ and GeoClaw validation remain independently green with no dependence on this visual terrain",
        ],
    }
    return conditioned, metadata


def _write_terrain_artifacts(
    output_root: Path,
    dem_crop: np.ndarray,
    physical_size: tuple[float, float],
    points: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
    definition: RiverCorridorDefinition,
) -> dict[str, str | float | dict[str, Any]]:
    derived_root = output_root / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)
    dem = np.asarray(
        Image.fromarray(dem_crop.astype(np.float32), mode="F").resize(
            (LANDSCAPE_SIZE, LANDSCAPE_SIZE), Image.Resampling.BILINEAR
        ),
        dtype=np.float32,
    )
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError("DEM crop contains no finite elevations")
    fill = float(np.median(dem[finite]))
    dem = np.where(finite, dem, fill)
    source_minimum = float(np.min(dem))
    source_maximum = float(np.max(dem))
    dem, channel_conditioning = _condition_visual_channel(
        dem,
        physical_size,
        points,
        bbox,
        definition,
    )
    minimum = float(np.min(dem))
    maximum = float(np.max(dem))
    relief = maximum - minimum
    for profile_sample in channel_conditioning["profile_samples"]:
        profile_sample["conditioned_surface_normalized"] = round(
            (profile_sample["conditioned_surface_elevation_m"] - minimum) / max(relief, 0.001),
            8,
        )
        profile_sample["conditioned_bed_normalized"] = round(
            (profile_sample["conditioned_bed_elevation_m"] - minimum) / max(relief, 0.001),
            8,
        )

    channel_conditioning_path = output_root / "hydrology" / "visual_channel_conditioning.json"
    channel_conditioning_path.parent.mkdir(parents=True, exist_ok=True)
    channel_conditioning_path.write_text(
        json.dumps(channel_conditioning, indent=2) + "\n",
        encoding="utf-8",
    )
    centerline_path = output_root / "hydrography" / "centerline_local.json"
    centerline_payload = json.loads(centerline_path.read_text(encoding="utf-8"))
    centerline_points = centerline_payload["points"]
    if len(centerline_points) != len(channel_conditioning["profile_samples"]):
        raise ValueError("visual channel profile does not match local centerline point count")
    for centerline_point, profile_sample in zip(
        centerline_points,
        channel_conditioning["profile_samples"],
        strict=True,
    ):
        centerline_point["conditioned_visual_surface_elevation_m"] = profile_sample[
            "conditioned_surface_elevation_m"
        ]
        centerline_point["conditioned_visual_bed_elevation_m"] = profile_sample[
            "conditioned_bed_elevation_m"
        ]
        centerline_point["conditioned_visual_surface_normalized"] = profile_sample[
            "conditioned_surface_normalized"
        ]
        centerline_point["conditioned_visual_bed_normalized"] = profile_sample[
            "conditioned_bed_normalized"
        ]
    centerline_payload["visual_channel_conditioning"] = {
        "path": "hydrology/visual_channel_conditioning.json",
        "status": channel_conditioning["status"],
        "surface_authority": "render_only_not_solver_or_surveyed_bathymetry",
    }
    centerline_path.write_text(json.dumps(centerline_payload, indent=2) + "\n", encoding="utf-8")

    normalized = np.clip((dem - minimum) / max(relief, 0.001), 0.0, 1.0)
    heightfield_path = derived_root / "heightfield_2017.png"
    Image.fromarray(np.rint(normalized * 65535.0).astype(np.uint16), mode="I;16").save(heightfield_path)
    relief_path = derived_root / "dem_relief_2048.png"
    Image.fromarray(np.rint(normalized * 255.0).astype(np.uint8), mode="L").resize(
        (MATERIAL_SIZE, MATERIAL_SIZE), Image.Resampling.BILINEAR
    ).save(relief_path)

    width_m, height_m = physical_size
    material_dem = np.asarray(
        Image.fromarray(dem, mode="F").resize((MATERIAL_SIZE, MATERIAL_SIZE), Image.Resampling.BILINEAR),
        dtype=np.float32,
    )
    gradient_y, gradient_x = np.gradient(
        material_dem,
        height_m / (MATERIAL_SIZE - 1),
        width_m / (MATERIAL_SIZE - 1),
    )
    nx, ny, nz = -gradient_x * 0.35, gradient_y * 0.35, np.ones_like(material_dem)
    normal_length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack(
        [nx / normal_length * 0.5 + 0.5, ny / normal_length * 0.5 + 0.5, nz / normal_length * 0.5 + 0.5],
        axis=2,
    )
    normal_path = derived_root / "terrain_normal_2048.png"
    Image.fromarray(np.rint(normal * 255.0).astype(np.uint8), mode="RGB").save(normal_path)
    slope = np.sqrt(gradient_x * gradient_x + gradient_y * gradient_y)
    ao = np.clip(0.96 - np.minimum(slope, 3.5) * 0.11, 0.40, 1.0)
    roughness = np.clip(0.62 + slope * 0.06, 0.48, 0.94)
    packed = np.stack([ao, roughness, np.asarray(Image.fromarray(normalized, mode="F").resize((MATERIAL_SIZE, MATERIAL_SIZE), Image.Resampling.BILINEAR))], axis=2)
    packed_path = derived_root / "terrain_ao_roughness_height_2048.png"
    Image.fromarray(np.rint(np.clip(packed, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB").save(packed_path)
    return {
        "heightfield": str(heightfield_path),
        "dem_relief": str(relief_path),
        "terrain_normal": str(normal_path),
        "terrain_ao_roughness_height": str(packed_path),
        "visual_channel_conditioning": str(channel_conditioning_path),
        "channel_conditioning_summary": {
            "status": channel_conditioning["status"],
            "parameters": channel_conditioning["parameters"],
            "measurements": channel_conditioning["measurements"],
            "authority": channel_conditioning["authority"],
        },
        "source_minimum_elevation_m": source_minimum,
        "source_maximum_elevation_m": source_maximum,
        "minimum_elevation_m": minimum,
        "maximum_elevation_m": maximum,
        "relief_m": relief,
    }


def _write_imagery_artifacts(
    source_visual_path: Path,
    output_root: Path,
    points: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
    physical_width_m: float,
) -> dict[str, str]:
    image = Image.open(source_visual_path).convert("RGB")
    albedo = image.resize((MATERIAL_SIZE, MATERIAL_SIZE), Image.Resampling.LANCZOS)
    derived_root = output_root / "derived"
    albedo_path = derived_root / "source_albedo_2048.png"
    albedo.save(albedo_path)
    rgb = np.asarray(albedo, dtype=np.float32)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    vegetation = np.clip((green - 0.47 * (red + blue) + 14.0) / 54.0, 0.0, 1.0)
    water_image = Image.new("L", (MATERIAL_SIZE, MATERIAL_SIZE), 0)
    west, south, east, north = bbox
    pixels = [
        (
            int(round((lon - west) / (east - west) * (MATERIAL_SIZE - 1))),
            int(round((north - lat) / (north - south) * (MATERIAL_SIZE - 1))),
        )
        for lon, lat in points
    ]
    river_width_px = max(5, int(round(100.0 / physical_width_m * MATERIAL_SIZE)))
    ImageDraw.Draw(water_image).line(pixels, fill=255, width=river_width_px, joint="curve")
    water = np.asarray(water_image, dtype=np.float32) / 255.0
    vegetation *= 1.0 - water
    zones = np.stack([1.0 - water, vegetation, water], axis=2)
    zones_path = derived_root / "material_zones_2048.png"
    Image.fromarray(np.rint(zones * 255.0).astype(np.uint8), mode="RGB").save(zones_path)
    water_path = derived_root / "water_mask_2048.png"
    Image.fromarray(np.rint(water * 255.0).astype(np.uint8), mode="L").save(water_path)
    vegetation_path = derived_root / "vegetation_mask_2048.png"
    Image.fromarray(np.rint(vegetation * 255.0).astype(np.uint8), mode="L").save(vegetation_path)
    return {
        "source_albedo": str(albedo_path),
        "material_zones": str(zones_path),
        "water_mask": str(water_path),
        "vegetation_mask": str(vegetation_path),
    }


def _write_unreal_texture_inputs(
    repo_root: Path,
    definition: RiverCorridorDefinition,
    corridor_root: Path,
) -> dict[str, str]:
    derived_root = corridor_root / "derived"
    source_albedo = Image.open(derived_root / "source_albedo_2048.png").convert("RGB")
    terrain_normal = Image.open(derived_root / "terrain_normal_2048.png").convert("RGB")
    packed = Image.open(derived_root / "terrain_ao_roughness_height_2048.png").convert("RGB")
    zones = Image.open(derived_root / "material_zones_2048.png").convert("RGB")

    physical_aliases = {
        "physical_source_albedo": (derived_root / f"{definition.river_id}_source_albedo_2048.png", source_albedo),
        "physical_normal": (derived_root / f"{definition.river_id}_normal_2048.png", terrain_normal),
        "physical_packed": (derived_root / f"{definition.river_id}_ao_roughness_height_2048.png", packed),
        "physical_material_zones": (derived_root / f"{definition.river_id}_material_zones_2048.png", zones),
    }
    alias_outputs: dict[str, str] = {}
    for key, (output, image) in physical_aliases.items():
        image.save(output)
        alias_outputs[key] = str(output.relative_to(repo_root))

    texture_sets = {
        "atlas_albedo": (
            Path("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases")
            / f"{definition.river_id}_first_party_material_texture_atlas_albedo.png",
            source_albedo.resize((1536, 1024), Image.Resampling.LANCZOS),
        ),
        "atlas_normal": (
            Path("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases")
            / f"{definition.river_id}_first_party_material_texture_atlas_normal.png",
            terrain_normal.resize((1536, 1024), Image.Resampling.LANCZOS),
        ),
        "atlas_packed": (
            Path("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases")
            / f"{definition.river_id}_first_party_material_texture_atlas_ao_roughness_height.png",
            packed.resize((1536, 1024), Image.Resampling.LANCZOS),
        ),
        "source_macro_albedo": (
            Path("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps")
            / f"{definition.river_id}_source_conditioned_macro_albedo.png",
            source_albedo,
        ),
        "source_normal_detail": (
            Path("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps")
            / f"{definition.river_id}_source_conditioned_normal_detail.png",
            terrain_normal,
        ),
        "source_packed": (
            Path("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps")
            / f"{definition.river_id}_source_conditioned_ao_roughness_height.png",
            packed,
        ),
        "source_material_zones": (
            Path("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps")
            / f"{definition.river_id}_source_conditioned_material_zones.png",
            zones,
        ),
        "detail_albedo": (
            Path("unreal/Content/RaftSim/Rendering/ProductionDetailTextures")
            / f"{definition.river_id}_terrain_bank_detail_v1_albedo.png",
            source_albedo.resize((1024, 1024), Image.Resampling.LANCZOS),
        ),
        "detail_normal": (
            Path("unreal/Content/RaftSim/Rendering/ProductionDetailTextures")
            / f"{definition.river_id}_terrain_bank_detail_v1_normal.png",
            terrain_normal.resize((1024, 1024), Image.Resampling.LANCZOS),
        ),
        "detail_packed": (
            Path("unreal/Content/RaftSim/Rendering/ProductionDetailTextures")
            / f"{definition.river_id}_terrain_bank_detail_v1_ao_roughness_height.png",
            packed.resize((1024, 1024), Image.Resampling.LANCZOS),
        ),
    }
    outputs: dict[str, str] = dict(alias_outputs)
    for key, (relative_path, image) in texture_sets.items():
        output = repo_root / relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        outputs[key] = str(relative_path)
    return outputs


def build_production_corridor(repo_root: Path, river_id: str) -> dict[str, Any]:
    definition = DEFINITIONS[river_id]
    repo_root = repo_root.resolve()
    river_root = repo_root / definition.relative_root
    route_source = river_root / definition.route_source_file
    sentinel_search = river_root / definition.sentinel_search_file
    sentinel_visual = river_root / definition.sentinel_visual_file
    required = [route_source, sentinel_search, sentinel_visual, *(river_root / tile.path for tile in definition.dem_tiles)]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing production inputs for {river_id}: {missing}")

    overpass_payload = json.loads(route_source.read_text(encoding="utf-8"))
    points = extract_route(overpass_payload, definition)
    bbox = _route_bbox(points, definition.route_buffer_m)
    physical_size = _physical_size_m(bbox)
    corridor_root = river_root / "production_corridor" / definition.output_slug
    corridor_root.mkdir(parents=True, exist_ok=True)
    route_artifacts = _write_route_artifacts(corridor_root, definition, points, bbox)
    dem_mosaic, dem_bbox = _load_dem_mosaic(river_root, definition.dem_tiles)
    dem_crop = _crop_geographic(dem_mosaic, dem_bbox, bbox)
    terrain_artifacts = _write_terrain_artifacts(
        corridor_root,
        dem_crop,
        physical_size,
        points,
        bbox,
        definition,
    )
    imagery_artifacts = _write_imagery_artifacts(sentinel_visual, corridor_root, points, bbox, physical_size[0])
    unreal_texture_inputs = _write_unreal_texture_inputs(repo_root, definition, corridor_root)

    hydrology_root = corridor_root / "hydrology"
    hydrology_root.mkdir(parents=True, exist_ok=True)
    flow_path = hydrology_root / "seasonal_flow_context.json"
    flow_path.write_text(json.dumps(definition.flow_context, indent=2) + "\n", encoding="utf-8")
    source_records = [
        {
            "role": "named_route_cross_reference",
            "path": str(route_source.relative_to(repo_root)),
            "sha256": _sha256(route_source),
            "provider": "OpenStreetMap contributors",
            "license": "ODbL-1.0",
            "query": definition.route_query,
            "authority": "cross_reference_not_survey_authority",
        },
        {
            "role": "sentinel_scene_search",
            "path": str(sentinel_search.relative_to(repo_root)),
            "sha256": _sha256(sentinel_search),
            "provider": "Element 84 Earth Search / Copernicus Sentinel-2",
            "license": "Copernicus Sentinel Data Legal Notice",
            "authority": "visual_surface_reference",
        },
        {
            "role": "route_visual",
            "path": str(sentinel_visual.relative_to(repo_root)),
            "sha256": _sha256(sentinel_visual),
            "provider": "Copernicus Sentinel-2",
            "scenes": [scene.__dict__ for scene in definition.sentinel_scenes],
            "license": "Copernicus Sentinel Data Legal Notice",
            "authority": "visual_surface_reference_not_bed_geometry",
        },
    ]
    source_records.extend(
        {
            "role": "terrain",
            "path": str((river_root / tile.path).relative_to(repo_root)),
            "sha256": _sha256(river_root / tile.path),
            "provider": "Copernicus DEM GLO-30",
            "url": tile.url,
            "license": "Copernicus DEM ESA user license; attribution and redistribution review required",
            "authority": "30m_surface_model_terrain_source",
        }
        for tile in definition.dem_tiles
    )
    terrain_acquisition_lead_path: Path | None = None
    if definition.terrain_acquisition_lead_file:
        terrain_acquisition_lead_path = river_root / definition.terrain_acquisition_lead_file
        terrain_acquisition_lead = json.loads(
            terrain_acquisition_lead_path.read_text(encoding="utf-8")
        )
        source_records.append(
            {
                "role": "high_resolution_terrain_acquisition_lead",
                "path": str(terrain_acquisition_lead_path.relative_to(repo_root)),
                "sha256": _sha256(terrain_acquisition_lead_path),
                "provider": "Zambezi River Authority / BGHES feasibility document set",
                "license": "discovery metadata only; survey data access and rights pending",
                "authority": "lead_only_no_geometry_or_media_imported",
                "status": terrain_acquisition_lead["status"],
            }
        )
    centerline_review_manifest_path: Path | None = None
    centerline_review_candidate_path: Path | None = None
    if definition.centerline_review_manifest_file:
        centerline_review_manifest_path = river_root / definition.centerline_review_manifest_file
        centerline_review_manifest = json.loads(
            centerline_review_manifest_path.read_text(encoding="utf-8")
        )
        centerline_review_candidate_path = repo_root / (
            centerline_review_manifest["outputs"]["candidate_geojson"]["path"]
        )
        source_records.append(
            {
                "role": "surface_water_centerline_review_candidate",
                "path": str(centerline_review_manifest_path.relative_to(repo_root)),
                "sha256": _sha256(centerline_review_manifest_path),
                "provider": "Copernicus Sentinel-2",
                "license": "Copernicus Sentinel Data Legal Notice",
                "authority": "10m_surface_water_observation_not_surveyed_centerline_or_bathymetry",
                "status": centerline_review_manifest["status"],
                "production_promoted": centerline_review_manifest["production_promoted"],
            }
        )
    route_length = _stationed(points)[-1]["station_m"]
    manifest = {
        "schema": ROUTE_SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "river_id": definition.river_id,
        "display_name": definition.display_name,
        "status": "source_scale_technical_corridor_not_yet_lifelike",
        "bounds_wgs84": list(bbox),
        "physical_size_m": {"width": physical_size[0], "height": physical_size[1]},
        "route": {
            "length_m": route_length,
            "point_count": len(points),
            "way_ids": list(definition.way_ids),
            "geometry_authority": definition.route_geometry_authority,
            "start_lon_lat": list(points[0]),
            "end_lon_lat": list(points[-1]),
            "endpoint_evidence": list(definition.endpoint_evidence),
            "guide_approval": None,
        },
        "source_records": source_records,
        "environment_contract": definition.environment_contract,
        "artifacts": {
            **{key: str(Path(value).relative_to(repo_root)) for key, value in route_artifacts.items()},
            **{
                key: str(Path(value).relative_to(repo_root)) if isinstance(value, str) else value
                for key, value in terrain_artifacts.items()
            },
            **{key: str(Path(value).relative_to(repo_root)) for key, value in imagery_artifacts.items()},
            "unreal_texture_inputs": unreal_texture_inputs,
            "seasonal_flow_context": str(flow_path.relative_to(repo_root)),
            "high_resolution_terrain_acquisition_lead": (
                str(terrain_acquisition_lead_path.relative_to(repo_root))
                if terrain_acquisition_lead_path
                else None
            ),
            "centerline_review_candidate": (
                str(centerline_review_candidate_path.relative_to(repo_root))
                if centerline_review_candidate_path
                else None
            ),
            "centerline_review_manifest": (
                str(centerline_review_manifest_path.relative_to(repo_root))
                if centerline_review_manifest_path
                else None
            ),
        },
        "promotion_gates": [
            "local guide confirms exact put-in, take-out, line direction, rapid stations, access, and rescue routes",
            "geospatial reviewer confirms DEM datum, route alignment, channel conditioning, and bank geometry",
            "rights reviewer confirms Copernicus DEM redistribution/attribution and all public capture references",
            "seasonal-flow reviewer confirms gauge-to-reach translation and flow-dependent visual/gameplay bands",
            "Unreal map uses source-scale terrain and approved assets, passes desktop/VR budgets, and has human lifelike approval",
        ],
    }
    manifest_path = corridor_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def acquire_sentinel_visual(
    repo_root: Path,
    river_id: str,
    *,
    maximum_dimension: int = 4096,
) -> Path:
    """Range-read selected Sentinel COGs and write a bounded route visual.

    Rasterio is an acquisition-only dependency so normal tests and package imports do
    not require GDAL.
    """

    try:
        import rasterio
        from rasterio.merge import merge
        from rasterio.warp import transform_bounds
    except ImportError as exc:  # pragma: no cover - environment-specific acquisition path
        raise RuntimeError("Sentinel acquisition requires rasterio") from exc

    definition = DEFINITIONS[river_id]
    repo_root = repo_root.resolve()
    river_root = repo_root / definition.relative_root
    route_payload = json.loads((river_root / definition.route_source_file).read_text(encoding="utf-8"))
    points = extract_route(route_payload, definition)
    bbox = _route_bbox(points, definition.route_buffer_m)
    datasets = [rasterio.open(scene.visual_url) for scene in definition.sentinel_scenes]
    try:
        crs = datasets[0].crs
        if any(dataset.crs != crs for dataset in datasets):
            raise ValueError("selected Sentinel scenes do not share a CRS")
        projected_bounds = transform_bounds("EPSG:4326", crs, *bbox, densify_pts=21)
        width_m = projected_bounds[2] - projected_bounds[0]
        height_m = projected_bounds[3] - projected_bounds[1]
        resolution = max(10.0, width_m / maximum_dimension, height_m / maximum_dimension)
        mosaic, _ = merge(datasets, bounds=projected_bounds, res=resolution, nodata=0)
    finally:
        for dataset in datasets:
            dataset.close()
    image = np.transpose(np.clip(mosaic[:3], 0, 255).astype(np.uint8), (1, 2, 0))
    output = river_root / definition.sentinel_visual_file
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image, mode="RGB").save(output)
    return output
