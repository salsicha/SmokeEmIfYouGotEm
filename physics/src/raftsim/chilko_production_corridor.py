"""Build the review-gated Chilko River production corridor package."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from raftsim.international_production_corridor import (
    RiverCorridorDefinition,
    SentinelScene,
    _distance_m,
    _physical_size_m,
    _route_bbox,
    _sha256,
    _stationed,
    _write_imagery_artifacts,
    _write_terrain_artifacts,
    _write_unreal_texture_inputs,
)


RIVER_ROOT = Path("physics/data/real_world/chilko_river_bc")
ROUTE_SOURCE = Path(
    "hydrography/lodge_to_taseko_junction_candidate_segments.geojson"
)
SOURCE_MANIFEST = Path("source_manifest.json")
FLOW_CONTEXT = Path("hydrology/seasonal_flow_context.json")
LAND_REVIEW = Path("review/land_and_publication_source_review.json")
MRDEM_SEARCH = Path("source/terrain/nrcan_mrdem30_stac_search.json")
SENTINEL_SEARCH = Path("source/imagery/sentinel2_summer_2025_stac_search.json")
MRDEM_DTM_CLIP = Path("source/terrain/nrcan_mrdem30_chilko_corridor_dtm.tif")
MRDEM_SOURCE_CLIP = Path("source/terrain/nrcan_mrdem30_chilko_corridor_source.tif")
MRDEM_CLIP_MANIFEST = Path("source/terrain/nrcan_mrdem30_chilko_corridor_manifest.json")
SENTINEL_TCI_CLIP = Path("source/imagery/sentinel2_20250825_chilko_corridor_tci.png")
SENTINEL_SCL_CLIP = Path("source/imagery/sentinel2_20250825_chilko_corridor_scl.png")
SENTINEL_CLIP_MANIFEST = Path(
    "source/imagery/sentinel2_20250825_chilko_corridor_manifest.json"
)
CORRIDOR_ROOT = Path(
    "production_corridor/chilko_river_lodge_to_taseko_junction"
)
UNREAL_IMPORT_CONTRACT = Path(
    "unreal/Content/RaftSim/River/chilko_heightfield_import_test.json"
)
PUT_IN_SEED = (-124.10681, 51.69627)
TAKE_OUT_SEED = (-123.677222, 52.006944)
MRDEM_DTM_URL = (
    "https://canelevation-dem.s3.ca-central-1.amazonaws.com/"
    "mrdem-30/mrdem-30-dtm.tif"
)
MRDEM_SOURCE_URL = (
    "https://canelevation-dem.s3.ca-central-1.amazonaws.com/"
    "mrdem-30/mrdem-30-source.tif"
)
SENTINEL_ITEM_ID = "S2C_10UDC_20250825_0_L2A"
UNREAL_LANDSCAPE_SIZE = 1009
MRDEM_SOURCE_CLASSES = {
    1: "adjusted_copernicus_glo_30",
    5: "blended_glo_30_hrdem_transition",
    10: "hrdem_mosaic",
}


CHILKO = RiverCorridorDefinition(
    river_id="chilko_river_lava_canyon",
    display_name="Chilko River: River Lodge to Chilko-Taseko Junction",
    relative_root=str(RIVER_ROOT),
    output_slug="chilko_river_lodge_to_taseko_junction",
    route_source_file=str(ROUTE_SOURCE),
    route_query=(
        "BC Freshwater Atlas WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP "
        "GNIS_NAME='Chilko River'"
    ),
    way_ids=(),
    route_geometry_authority=(
        "official_bc_freshwater_atlas_areal_stream_skeleton_deterministically_"
        "stitched_between_nearest_review_seed_vertices_not_access_or_rapid_approval"
    ),
    start_seed_lon_lat=PUT_IN_SEED,
    end_seed_lon_lat=TAKE_OUT_SEED,
    end_station_m=None,
    route_buffer_m=2_000.0,
    channel_half_width_m=45.0,
    channel_feather_width_m=75.0,
    channel_profile_smoothing_m=500.0,
    channel_maximum_downstream_slope=0.015,
    channel_bed_depth_m=1.5,
    channel_maximum_cut_m=70.0,
    channel_maximum_fill_m=0.0,
    dem_tiles=(),
    sentinel_search_file=str(SENTINEL_SEARCH),
    sentinel_scenes=(
        SentinelScene(
            item_id=SENTINEL_ITEM_ID,
            datetime_utc="2025-08-25T19:30:32.137000Z",
            cloud_cover_percent=0.000644,
            tile_id="10UDC",
            visual_url=(
                "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                "sentinel-s2-l2a-cogs/10/U/DC/2025/8/"
                "S2C_10UDC_20250825_0_L2A/TCI.tif"
            ),
        ),
    ),
    sentinel_visual_file=str(SENTINEL_TCI_CLIP),
    terrain_acquisition_lead_file=None,
    centerline_review_manifest_file=None,
    endpoint_evidence=(
        {
            "endpoint": "put_in",
            "name": "Chilko River Lodge put-in",
            "policy": "nearest official FWA route vertex to review seed",
            "confidence": "review_gated",
            "exact_access_geometry_approved": False,
        },
        {
            "endpoint": "take_out",
            "name": "Chilko-Taseko Junction take-out",
            "policy": "nearest official FWA route vertex to review seed",
            "confidence": "review_gated",
            "exact_access_geometry_approved": False,
        },
    ),
    flow_context={},
    environment_contract={
        "geology": (
            "Chilcotin plateau transition, glacial valley deposits, canyon bedrock, "
            "talus, gravel bars, and flow-exposed boulder controls"
        ),
        "water": (
            "cold turquoise river with flow-dependent constrictions, wave trains, "
            "holes, laterals, boils, eddy lines, and boulder push"
        ),
        "ecology": (
            "interior Douglas-fir and lodgepole-pine forest, aspen and willow riparian "
            "bands, open benches, and disturbance-dependent regeneration"
        ),
        "atmosphere": (
            "clear high-interior light with flow spray, canyon shadow, smoke and haze "
            "only when source and seasonal evidence support them"
        ),
        "procedural_layers": [
            "bedrock",
            "talus",
            "gravel_bars",
            "wet_boulders",
            "interior_conifer_forest",
            "aspen_willow_riparian",
            "foam",
            "spray",
            "mist",
        ],
    },
)


@dataclass(frozen=True)
class StitchedRoute:
    points: list[tuple[float, float]]
    diagnostics: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _coordinate_key(point: list[float] | tuple[float, ...]) -> tuple[float, float]:
    return (round(float(point[0]), 8), round(float(point[1]), 8))


def stitch_official_route(payload: dict[str, Any]) -> StitchedRoute:
    """Stitch the selected FWA chain and clip it to nearest official seed vertices."""

    features = payload.get("features", [])
    if not features:
        raise ValueError("Chilko route source contains no features")

    edges: dict[str, list[tuple[float, float]]] = {}
    adjacency: dict[tuple[float, float], list[str]] = defaultdict(list)
    for index, feature in enumerate(features):
        geometry = feature.get("geometry", {})
        if geometry.get("type") != "LineString":
            raise ValueError("Chilko route source must contain only LineStrings")
        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            raise ValueError("Chilko route segment has fewer than two coordinates")
        feature_id = str(feature.get("id", index))
        points = [(float(point[0]), float(point[1])) for point in coordinates]
        edges[feature_id] = points
        adjacency[_coordinate_key(points[0])].append(feature_id)
        adjacency[_coordinate_key(points[-1])].append(feature_id)

    degree_counts = Counter(len(edge_ids) for edge_ids in adjacency.values())
    endpoints = [point for point, edge_ids in adjacency.items() if len(edge_ids) == 1]
    if len(endpoints) != 2 or any(degree > 2 for degree in degree_counts):
        raise ValueError(
            "selected FWA route is not one unbranched chain: "
            f"endpoints={len(endpoints)}, degree_counts={dict(degree_counts)}"
        )

    current = min(endpoints, key=lambda point: _distance_m(point, PUT_IN_SEED))
    route: list[tuple[float, float]] = []
    used: set[str] = set()
    while True:
        candidates = [edge_id for edge_id in adjacency[current] if edge_id not in used]
        if not candidates:
            break
        if len(candidates) != 1:
            raise ValueError(f"ambiguous FWA traversal at {current}: {candidates}")
        edge_id = candidates[0]
        edge = edges[edge_id]
        if _coordinate_key(edge[0]) != current:
            edge = list(reversed(edge))
        if route:
            if _coordinate_key(route[-1]) != _coordinate_key(edge[0]):
                raise ValueError("FWA route traversal introduced a join gap")
            route.extend(edge[1:])
        else:
            route.extend(edge)
        used.add(edge_id)
        current = _coordinate_key(edge[-1])

    if used != set(edges):
        raise ValueError(f"FWA route traversal omitted {len(set(edges) - used)} segments")

    start_index = min(
        range(len(route)), key=lambda index: _distance_m(route[index], PUT_IN_SEED)
    )
    end_index = min(
        range(len(route)), key=lambda index: _distance_m(route[index], TAKE_OUT_SEED)
    )
    if start_index >= end_index:
        raise ValueError("review endpoint seeds do not follow the stitched downstream route")
    clipped = route[start_index : end_index + 1]
    stationed = _stationed(clipped)
    return StitchedRoute(
        points=clipped,
        diagnostics={
            "source_feature_count": len(features),
            "stitched_feature_count": len(used),
            "source_endpoint_count": len(endpoints),
            "endpoint_degree_counts": {
                str(degree): count for degree, count in sorted(degree_counts.items())
            },
            "all_source_segments_used": len(used) == len(features),
            "maximum_join_gap_m": 0.0,
            "full_chain_point_count": len(route),
            "clipped_point_count": len(clipped),
            "clipped_length_m": stationed[-1]["station_m"],
            "put_in_seed_lon_lat": list(PUT_IN_SEED),
            "put_in_official_vertex_lon_lat": list(clipped[0]),
            "put_in_seed_offset_m": _distance_m(PUT_IN_SEED, clipped[0]),
            "take_out_seed_lon_lat": list(TAKE_OUT_SEED),
            "take_out_official_vertex_lon_lat": list(clipped[-1]),
            "take_out_seed_offset_m": _distance_m(TAKE_OUT_SEED, clipped[-1]),
            "exact_access_geometry_approved": False,
        },
    )


def _write_route_artifacts(
    corridor_root: Path,
    route: StitchedRoute,
    bbox: tuple[float, float, float, float],
) -> dict[str, Path]:
    hydrography_root = corridor_root / "hydrography"
    hydrography_root.mkdir(parents=True, exist_ok=True)
    stationed = _stationed(route.points)
    centerline_path = hydrography_root / "route_centerline.geojson"
    _write_json(
        centerline_path,
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "river_id": CHILKO.river_id,
                        "route": CHILKO.display_name,
                        "source": "British Columbia Freshwater Atlas",
                        "license": "Open Government Licence - British Columbia",
                        "status": (
                            "official_hydrography_stitched_review_seed_endpoints_not_"
                            "access_or_rapid_approval"
                        ),
                        "geometry_authority": CHILKO.route_geometry_authority,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [list(point) for point in route.points],
                    },
                }
            ],
        },
    )
    stationing_path = hydrography_root / "route_stationing.json"
    _write_json(
        stationing_path,
        {
            "schema": "raftsim.route_stationing.v1",
            "river_id": CHILKO.river_id,
            "length_m": stationed[-1]["station_m"],
            "samples": stationed,
            "stitch_diagnostics": route.diagnostics,
        },
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
    _write_json(
        local_path,
        {
            "schema": "raftsim.local_centerline.v1",
            "river_id": CHILKO.river_id,
            "bounds_wgs84": list(bbox),
            "local_metric_policy": (
                "equirectangular offsets at corridor center latitude; Unreal local X "
                "increases east and local Y follows source image rows southward from "
                "the northwest heightfield corner"
            ),
            "source_crs": "EPSG:4326",
            "points": local,
        },
    )
    return {
        "centerline_geojson": centerline_path,
        "stationing": stationing_path,
        "centerline_local": local_path,
    }


def _target_shape(
    bbox: tuple[float, float, float, float],
    source_resolution_m: float,
    maximum_dimension: int,
) -> tuple[int, int, float]:
    width_m, height_m = _physical_size_m(bbox)
    resolution = max(
        source_resolution_m,
        width_m / maximum_dimension,
        height_m / maximum_dimension,
    )
    width = max(2, int(math.ceil(width_m / resolution)))
    height = max(2, int(math.ceil(height_m / resolution)))
    return width, height, resolution


def _require_rasterio() -> tuple[Any, Any, Any, Any]:
    try:
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.transform import from_bounds
        from rasterio.warp import reproject
    except ImportError as exc:  # pragma: no cover - acquisition environment specific
        raise RuntimeError(
            "Chilko source acquisition requires the raftsim[geospatial] extra"
        ) from exc
    return rasterio, Resampling, from_bounds, reproject


def _reproject_remote_asset(
    source_url: str,
    bbox: tuple[float, float, float, float],
    *,
    band_count: int,
    dtype: np.dtype[Any],
    source_resolution_m: float,
    maximum_dimension: int,
    nearest: bool,
) -> tuple[np.ndarray, Any, dict[str, Any]]:
    rasterio, Resampling, from_bounds, reproject = _require_rasterio()
    width, height, resolution = _target_shape(
        bbox, source_resolution_m, maximum_dimension
    )
    transform = from_bounds(*bbox, width, height)
    output = np.zeros((band_count, height, width), dtype=dtype)
    with rasterio.Env(AWS_NO_SIGN_REQUEST="YES"):
        with rasterio.open(source_url) as source:
            if source.count < band_count:
                raise ValueError(
                    f"source {source_url} has {source.count} bands, need {band_count}"
                )
            for band_index in range(band_count):
                reproject(
                    source=rasterio.band(source, band_index + 1),
                    destination=output[band_index],
                    src_transform=source.transform,
                    src_crs=source.crs,
                    src_nodata=source.nodata,
                    dst_transform=transform,
                    dst_crs="EPSG:4326",
                    dst_nodata=0 if np.issubdtype(dtype, np.integer) else -32767.0,
                    resampling=Resampling.nearest if nearest else Resampling.bilinear,
                )
            source_metadata = {
                "source_crs": str(source.crs),
                "source_shape": [source.height, source.width],
                "source_band_count": source.count,
                "source_dtype": list(source.dtypes),
                "source_nodata": source.nodata,
                "source_block_shapes": [list(shape) for shape in source.block_shapes],
            }
    metadata = {
        **source_metadata,
        "target_crs": "EPSG:4326",
        "target_bounds_wgs84": list(bbox),
        "target_shape": [height, width],
        "effective_resolution_m": resolution,
    }
    return output, transform, metadata


def acquire_chilko_source_clips(repo_root: Path) -> list[Path]:
    """Range-read and hash bounded official terrain and imagery source clips."""

    repo_root = repo_root.resolve()
    river_root = repo_root / RIVER_ROOT
    route = stitch_official_route(_read_json(river_root / ROUTE_SOURCE))
    bbox = _route_bbox(route.points, CHILKO.route_buffer_m)
    rasterio, _, _, _ = _require_rasterio()

    dtm, dtm_transform, dtm_metadata = _reproject_remote_asset(
        MRDEM_DTM_URL,
        bbox,
        band_count=1,
        dtype=np.dtype(np.float32),
        source_resolution_m=30.0,
        maximum_dimension=2048,
        nearest=False,
    )
    source_class, source_transform, source_metadata = _reproject_remote_asset(
        MRDEM_SOURCE_URL,
        bbox,
        band_count=1,
        dtype=np.dtype(np.uint8),
        source_resolution_m=30.0,
        maximum_dimension=2048,
        nearest=True,
    )
    if dtm.shape != source_class.shape or dtm_transform != source_transform:
        raise ValueError("MRDEM terrain and per-pixel source clips do not align")
    dtm_path = river_root / MRDEM_DTM_CLIP
    source_path = river_root / MRDEM_SOURCE_CLIP
    dtm_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        dtm_path,
        "w",
        driver="GTiff",
        height=dtm.shape[1],
        width=dtm.shape[2],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=dtm_transform,
        nodata=-32767.0,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as output:
        output.write(dtm)
    with rasterio.open(
        source_path,
        "w",
        driver="GTiff",
        height=source_class.shape[1],
        width=source_class.shape[2],
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=source_transform,
        nodata=0,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as output:
        output.write(source_class)

    valid_dtm = dtm[0][dtm[0] > -32000.0]
    source_counts = Counter(int(value) for value in source_class[0].ravel() if value)
    terrain_manifest_path = river_root / MRDEM_CLIP_MANIFEST
    _write_json(
        terrain_manifest_path,
        {
            "schema": "raftsim.chilko.mrdem30_corridor_clip.v1",
            "status": "official_30m_dtm_and_source_clip_attached_review_gated",
            "acquired_on": "2026-07-15",
            "provider": "Natural Resources Canada CanElevation",
            "license": "Open Government Licence - Canada",
            "product": "MRDEM-30 DTM and MRDEM-30 SOURCE",
            "source_urls": {
                "dtm": MRDEM_DTM_URL,
                "per_pixel_source": MRDEM_SOURCE_URL,
                "product_specification": (
                    "https://download-telecharger.services.geo.ca/pub/elevation/"
                    "dem_mne/MRDEM_MNEMR/CanElevation-MRDEM-Product-Specifications.pdf"
                ),
            },
            "horizontal_source_crs": "EPSG:3979 NAD83(CSRS) Canada Atlas Lambert",
            "horizontal_clip_crs": "EPSG:4326 WGS 84",
            "vertical_datum": "CGVD2013 orthometric heights (EPSG:6647)",
            "metadata": dtm_metadata,
            "source_metadata": source_metadata,
            "elevation_range_m": [float(valid_dtm.min()), float(valid_dtm.max())],
            "per_pixel_source_classes": [
                {
                    "value": value,
                    "meaning": MRDEM_SOURCE_CLASSES.get(value, "unknown_review_required"),
                    "pixel_count": count,
                }
                for value, count in sorted(source_counts.items())
            ],
            "outputs": {
                "dtm": {
                    "path": str(dtm_path.relative_to(repo_root)),
                    "sha256": _sha256(dtm_path),
                },
                "per_pixel_source": {
                    "path": str(source_path.relative_to(repo_root)),
                    "sha256": _sha256(source_path),
                },
            },
            "authority": (
                "official source-scale terrain fallback; not rapid-scale rock, bank, "
                "bathymetry, access, or hazard geometry"
            ),
            "production_promoted": False,
        },
    )

    search = _read_json(river_root / SENTINEL_SEARCH)
    scene = next(
        feature for feature in search["features"] if feature["id"] == SENTINEL_ITEM_ID
    )
    visual_url = scene["assets"]["visual"]["href"]
    scl_url = scene["assets"]["scl"]["href"]
    tci, _, tci_metadata = _reproject_remote_asset(
        visual_url,
        bbox,
        band_count=3,
        dtype=np.dtype(np.uint8),
        source_resolution_m=10.0,
        maximum_dimension=4096,
        nearest=False,
    )
    scl, _, scl_metadata = _reproject_remote_asset(
        scl_url,
        bbox,
        band_count=1,
        dtype=np.dtype(np.uint8),
        source_resolution_m=20.0,
        maximum_dimension=4096,
        nearest=True,
    )
    tci_path = river_root / SENTINEL_TCI_CLIP
    scl_path = river_root / SENTINEL_SCL_CLIP
    tci_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.moveaxis(tci, 0, 2), mode="RGB").save(tci_path)
    Image.fromarray(scl[0], mode="L").save(scl_path)
    valid_scl = scl[0][scl[0] != 0]
    scl_counts = Counter(int(value) for value in valid_scl)
    obscured_codes = {3, 8, 9, 10, 11}
    obscured_count = sum(scl_counts.get(value, 0) for value in obscured_codes)
    imagery_manifest_path = river_root / SENTINEL_CLIP_MANIFEST
    _write_json(
        imagery_manifest_path,
        {
            "schema": "raftsim.chilko.sentinel2_corridor_clip.v1",
            "status": "route_window_tci_and_scl_attached_visual_review_gated",
            "acquired_on": "2026-07-15",
            "provider": "Copernicus Sentinel-2 via Element 84 Earth Search",
            "license": "Copernicus Sentinel Data Legal Notice",
            "attribution": "Contains modified Copernicus Sentinel data (2025)",
            "scene": {
                "item_id": scene["id"],
                "datetime_utc": scene["properties"]["datetime"],
                "platform": scene["properties"]["platform"],
                "tile": scene["properties"]["grid:code"],
                "catalog_cloud_cover_percent": scene["properties"]["eo:cloud_cover"],
                "visual_url": visual_url,
                "scl_url": scl_url,
            },
            "tci_metadata": tci_metadata,
            "scl_metadata": scl_metadata,
            "scl_class_pixel_counts": {
                str(value): count for value, count in sorted(scl_counts.items())
            },
            "obscured_scl_codes": sorted(obscured_codes),
            "obscured_fraction_of_valid_clip": (
                obscured_count / max(int(valid_scl.size), 1)
            ),
            "outputs": {
                "true_color": {
                    "path": str(tci_path.relative_to(repo_root)),
                    "sha256": _sha256(tci_path),
                },
                "scene_classification": {
                    "path": str(scl_path.relative_to(repo_root)),
                    "sha256": _sha256(scl_path),
                },
            },
            "authority": (
                "seasonal surface-color, vegetation, water-extent, cloud and shadow "
                "review; not bed, bank, access, rapid, or bathymetry geometry"
            ),
            "production_promoted": False,
        },
    )
    return [
        dtm_path,
        source_path,
        terrain_manifest_path,
        tci_path,
        scl_path,
        imagery_manifest_path,
    ]


def _write_unreal_import_contract(
    repo_root: Path,
    manifest: dict[str, Any],
) -> Path:
    path = repo_root / UNREAL_IMPORT_CONTRACT
    _write_json(
        path,
        {
            "schema": "raftsim.unreal.chilko_landscape_import.v1",
            "river_id": CHILKO.river_id,
            "status": "source_scale_landscape_candidate_ready_for_isolated_review",
            "activation": "enabled_for_isolated_editor_candidate_only",
            "heightfield": manifest["artifacts"]["heightfield_source_scale"],
            "heightfield_size": UNREAL_LANDSCAPE_SIZE,
            "bounds_wgs84": manifest["bounds_wgs84"],
            "horizontal_span_cm": {
                "x": manifest["physical_size_m"]["width"] * 100.0,
                "y": manifest["physical_size_m"]["height"] * 100.0,
            },
            "target_relief_cm": manifest["terrain"]["relief_m"] * 100.0,
            "local_centerline": manifest["artifacts"]["centerline_local"],
            "source_manifest": manifest["manifest_path"],
            "map_package": (
                "/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
                "L_ChilkoRiver_PhysicalCorridorCandidate"
            ),
            "landscape_nanite_requested": True,
            "authority": {
                "visual_terrain_only": True,
                "changes_solver_state": False,
                "changes_collision_or_raft_forces": False,
                "surveyed_bathymetry": False,
            },
            "promotion_blockers": [
                "exact put-in and take-out access geometry and permission",
                "rapid-scale terrain, banks, boulders, and bathymetry",
                "Bidwell, Lava Canyon, White Mile, Green Mile, and Miracle Canyon stationing",
                "gauge-window routing and local guide flow review",
                "Tŝilhqot'in land, stewardship, naming, and publication review",
                "guide, geospatial, art, rights, hazard-readability, desktop, console, handheld, and VR approval",
            ],
            "production_promoted": False,
        },
    )
    return path


def build_chilko_production_corridor(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    river_root = repo_root / RIVER_ROOT
    required = [
        river_root / ROUTE_SOURCE,
        river_root / SOURCE_MANIFEST,
        river_root / FLOW_CONTEXT,
        river_root / LAND_REVIEW,
        river_root / MRDEM_SEARCH,
        river_root / SENTINEL_SEARCH,
        river_root / MRDEM_DTM_CLIP,
        river_root / MRDEM_SOURCE_CLIP,
        river_root / MRDEM_CLIP_MANIFEST,
        river_root / SENTINEL_TCI_CLIP,
        river_root / SENTINEL_SCL_CLIP,
        river_root / SENTINEL_CLIP_MANIFEST,
    ]
    missing = [str(path.relative_to(repo_root)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing Chilko corridor inputs: {missing}")

    route = stitch_official_route(_read_json(river_root / ROUTE_SOURCE))
    bbox = _route_bbox(route.points, CHILKO.route_buffer_m)
    physical_size = _physical_size_m(bbox)
    corridor_root = river_root / CORRIDOR_ROOT
    corridor_root.mkdir(parents=True, exist_ok=True)
    route_artifacts = _write_route_artifacts(corridor_root, route, bbox)

    dem = np.asarray(Image.open(river_root / MRDEM_DTM_CLIP), dtype=np.float32)
    if dem.ndim == 3:
        dem = dem[..., 0]
    terrain_artifacts = _write_terrain_artifacts(
        corridor_root,
        dem,
        physical_size,
        route.points,
        bbox,
        CHILKO,
    )
    oversampled_heightfield = Path(terrain_artifacts["heightfield"])
    source_scale_heightfield = (
        corridor_root / "derived" / f"heightfield_{UNREAL_LANDSCAPE_SIZE}.png"
    )
    source_scale_values = np.asarray(
        Image.open(oversampled_heightfield).resize(
            (UNREAL_LANDSCAPE_SIZE, UNREAL_LANDSCAPE_SIZE),
            Image.Resampling.BILINEAR,
        ),
        dtype=np.float64,
    )
    source_scale_minimum = float(source_scale_values.min())
    source_scale_range = float(source_scale_values.max() - source_scale_minimum)
    source_scale_encoded = np.rint(
        (source_scale_values - source_scale_minimum)
        / max(source_scale_range, 1.0)
        * 65535.0
    ).astype(np.uint16)
    Image.fromarray(source_scale_encoded, mode="I;16").save(source_scale_heightfield)
    terrain_artifacts["heightfield_source_scale"] = str(source_scale_heightfield)
    terrain_artifacts["heightfield_source_scale_policy"] = {
        "size": UNREAL_LANDSCAPE_SIZE,
        "source_dtm_resolution_m": 30.0,
        "landscape_spacing_m": {
            "x": physical_size[0] / (UNREAL_LANDSCAPE_SIZE - 1),
            "y": physical_size[1] / (UNREAL_LANDSCAPE_SIZE - 1),
        },
        "resampling": "bilinear_then_full_uint16_range_normalization",
        "reason": (
            "1009 samples preserve the official source scale without embedding a "
            "2017-grid Nanite representation that adds no terrain authority"
        ),
    }
    imagery_artifacts = _write_imagery_artifacts(
        river_root / SENTINEL_TCI_CLIP,
        corridor_root,
        route.points,
        bbox,
        physical_size[0],
    )
    unreal_texture_inputs = _write_unreal_texture_inputs(
        repo_root, CHILKO, corridor_root
    )

    flow_path = corridor_root / "hydrology/seasonal_flow_context.json"
    flow_payload = _read_json(river_root / FLOW_CONTEXT)
    _write_json(flow_path, flow_payload)
    terrain_manifest = _read_json(river_root / MRDEM_CLIP_MANIFEST)
    imagery_manifest = _read_json(river_root / SENTINEL_CLIP_MANIFEST)
    source_manifest = _read_json(river_root / SOURCE_MANIFEST)

    def relative_artifact(value: str | Path) -> str:
        return str(Path(value).relative_to(repo_root))

    manifest_path = corridor_root / "manifest.json"
    manifest: dict[str, Any] = {
        "schema": "raftsim.chilko_production_corridor.v1",
        "generated_on": "2026-07-15",
        "river_id": CHILKO.river_id,
        "display_name": CHILKO.display_name,
        "status": "official_source_scale_corridor_generated_unreal_review_pending",
        "bounds_wgs84": list(bbox),
        "physical_size_m": {
            "width": physical_size[0],
            "height": physical_size[1],
        },
        "route": {
            "length_m": route.diagnostics["clipped_length_m"],
            "point_count": len(route.points),
            "geometry_authority": CHILKO.route_geometry_authority,
            "source_feature_count": route.diagnostics["source_feature_count"],
            "all_source_segments_stitched": route.diagnostics[
                "all_source_segments_used"
            ],
            "start_lon_lat": list(route.points[0]),
            "end_lon_lat": list(route.points[-1]),
            "stitch_diagnostics": route.diagnostics,
            "endpoint_evidence": list(CHILKO.endpoint_evidence),
            "exact_access_geometry_approved": False,
            "guide_approval": None,
        },
        "terrain": {
            "product": "NRCan CanElevation MRDEM-30 DTM",
            "horizontal_source_crs": terrain_manifest["horizontal_source_crs"],
            "horizontal_clip_crs": terrain_manifest["horizontal_clip_crs"],
            "vertical_datum": terrain_manifest["vertical_datum"],
            "source_resolution_m": 30.0,
            "per_pixel_source_classes": terrain_manifest[
                "per_pixel_source_classes"
            ],
            "source_minimum_elevation_m": terrain_artifacts[
                "source_minimum_elevation_m"
            ],
            "source_maximum_elevation_m": terrain_artifacts[
                "source_maximum_elevation_m"
            ],
            "conditioned_minimum_elevation_m": terrain_artifacts[
                "minimum_elevation_m"
            ],
            "conditioned_maximum_elevation_m": terrain_artifacts[
                "maximum_elevation_m"
            ],
            "relief_m": terrain_artifacts["relief_m"],
            "authority": terrain_manifest["authority"],
        },
        "imagery": {
            "scene": imagery_manifest["scene"],
            "obscured_fraction_of_valid_clip": imagery_manifest[
                "obscured_fraction_of_valid_clip"
            ],
            "authority": imagery_manifest["authority"],
        },
        "environment_contract": CHILKO.environment_contract,
        "source_records": [
            {
                "role": "official_hydrography",
                "path": str((river_root / ROUTE_SOURCE).relative_to(repo_root)),
                "sha256": _sha256(river_root / ROUTE_SOURCE),
                "provider": "British Columbia Freshwater Atlas",
                "license": "Open Government Licence - British Columbia",
            },
            {
                "role": "official_source_attachment",
                "path": str((river_root / SOURCE_MANIFEST).relative_to(repo_root)),
                "sha256": _sha256(river_root / SOURCE_MANIFEST),
                "status": source_manifest["status"],
            },
            {
                "role": "official_terrain_clip",
                "path": str((river_root / MRDEM_CLIP_MANIFEST).relative_to(repo_root)),
                "sha256": _sha256(river_root / MRDEM_CLIP_MANIFEST),
                "provider": "Natural Resources Canada CanElevation",
                "license": "Open Government Licence - Canada",
            },
            {
                "role": "route_window_imagery_and_scene_classification",
                "path": str(
                    (river_root / SENTINEL_CLIP_MANIFEST).relative_to(repo_root)
                ),
                "sha256": _sha256(river_root / SENTINEL_CLIP_MANIFEST),
                "provider": "Copernicus Sentinel-2 via Element 84 Earth Search",
                "license": "Copernicus Sentinel Data Legal Notice",
            },
            {
                "role": "official_monthly_flow_context",
                "path": str((river_root / FLOW_CONTEXT).relative_to(repo_root)),
                "sha256": _sha256(river_root / FLOW_CONTEXT),
                "provider": "Environment and Climate Change Canada",
                "authority": "seasonal_context_not_gameplay_band_approval",
            },
            {
                "role": "land_and_publication_review",
                "path": str((river_root / LAND_REVIEW).relative_to(repo_root)),
                "sha256": _sha256(river_root / LAND_REVIEW),
                "authority": "review_policy_not_access_permission",
            },
        ],
        "artifacts": {
            **{key: relative_artifact(value) for key, value in route_artifacts.items()},
            **{
                key: relative_artifact(value) if isinstance(value, str) else value
                for key, value in terrain_artifacts.items()
            },
            **{
                key: relative_artifact(value)
                for key, value in imagery_artifacts.items()
            },
            "unreal_texture_inputs": unreal_texture_inputs,
            "seasonal_flow_context": str(flow_path.relative_to(repo_root)),
            "terrain_source_clip_manifest": str(
                (river_root / MRDEM_CLIP_MANIFEST).relative_to(repo_root)
            ),
            "imagery_source_clip_manifest": str(
                (river_root / SENTINEL_CLIP_MANIFEST).relative_to(repo_root)
            ),
        },
        "promotion_gates": {
            "official_source_chain_stitched": True,
            "source_scale_corridor_generated": True,
            "exact_put_in_take_out_access": False,
            "rapid_scale_terrain_and_bathymetry": False,
            "named_rapid_stationing": False,
            "numeric_flow_bands": False,
            "guide_review": False,
            "land_and_publication_review": False,
            "unreal_landscape_import_review": False,
            "lifelike_capture": False,
            "desktop_console_handheld_vr_performance": False,
        },
        "production_promoted": False,
    }
    manifest["manifest_path"] = str(manifest_path.relative_to(repo_root))
    _write_json(manifest_path, manifest)
    import_contract_path = _write_unreal_import_contract(repo_root, manifest)
    manifest["artifacts"]["unreal_import_contract"] = str(
        import_contract_path.relative_to(repo_root)
    )
    _write_json(manifest_path, manifest)
    return manifest
