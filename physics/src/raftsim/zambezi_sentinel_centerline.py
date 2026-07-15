"""Build a review-only Batoka centerline candidate from Sentinel-2 surface water."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


RIVER_ID = "zambezi_batoka_gorge"
SCENE_IDS = (
    "S2C_35KLA_20260610_0_L2A",
    "S2C_35KMA_20260610_0_L2A",
)
TARGET_CRS = "EPSG:32735"
TARGET_RESOLUTION_M = 10.0
ROUTE_SAMPLE_SPACING_M = 20.0
MAXIMUM_LATERAL_SEARCH_M = 200.0
WATER_NDWI_THRESHOLD = -0.05


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _polyline_length(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def _densify(points: np.ndarray, spacing_m: float) -> tuple[np.ndarray, np.ndarray]:
    segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    stations = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    targets = np.arange(0.0, stations[-1], spacing_m, dtype=np.float64)
    if not math.isclose(float(targets[-1]), float(stations[-1])):
        targets = np.append(targets, stations[-1])
    dense = np.column_stack(
        (
            np.interp(targets, stations, points[:, 0]),
            np.interp(targets, stations, points[:, 1]),
        )
    )
    return dense, targets


def _normals(points: np.ndarray) -> np.ndarray:
    tangents = np.empty_like(points)
    tangents[1:-1] = points[2:] - points[:-2]
    tangents[0] = points[1] - points[0]
    tangents[-1] = points[-1] - points[-2]
    lengths = np.linalg.norm(tangents, axis=1)
    tangents /= np.maximum(lengths[:, None], 1e-9)
    return np.column_stack((-tangents[:, 1], tangents[:, 0]))


def select_centerline_offsets(
    observation_scores: np.ndarray,
    offsets_m: np.ndarray,
    *,
    maximum_step_m: float = 60.0,
    transition_penalty_per_m: float = 0.018,
) -> np.ndarray:
    """Select a smooth route through per-station lateral observation scores."""

    scores = np.asarray(observation_scores, dtype=np.float64)
    offsets = np.asarray(offsets_m, dtype=np.float64)
    if scores.ndim != 2 or scores.shape[1] != len(offsets):
        raise ValueError("observation scores must be station by lateral-offset")
    if len(offsets) < 3 or not np.all(np.diff(offsets) > 0.0):
        raise ValueError("offsets must contain at least three increasing values")

    previous = scores[0].copy()
    backtrack = np.zeros(scores.shape, dtype=np.int16)
    transition_distance = np.abs(offsets[:, None] - offsets[None, :])
    transition_cost = transition_distance * transition_penalty_per_m
    transition_cost[transition_distance > maximum_step_m] = 1e6

    for station_index in range(1, scores.shape[0]):
        candidates = previous[:, None] - transition_cost
        parents = np.argmax(candidates, axis=0)
        previous = scores[station_index] + candidates[parents, np.arange(len(offsets))]
        backtrack[station_index] = parents.astype(np.int16)

    selected = np.empty(scores.shape[0], dtype=np.int16)
    selected[-1] = int(np.argmax(previous))
    for station_index in range(scores.shape[0] - 1, 0, -1):
        selected[station_index - 1] = backtrack[station_index, selected[station_index]]
    return offsets[selected]


def _smooth_offsets(offsets_m: np.ndarray, stations_m: np.ndarray) -> np.ndarray:
    kernel = np.asarray([1.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64)
    kernel /= kernel.sum()
    padded = np.pad(offsets_m, (3, 3), mode="edge")
    smoothed = np.convolve(padded, kernel, mode="valid")
    endpoint_weight = np.minimum.reduce(
        (
            np.ones_like(stations_m),
            stations_m / 200.0,
            (stations_m[-1] - stations_m) / 200.0,
        )
    )
    return smoothed * np.clip(endpoint_weight, 0.0, 1.0)


def _rdp(points: np.ndarray, tolerance_m: float) -> np.ndarray:
    if len(points) <= 2:
        return points
    start, end = points[0], points[-1]
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length <= 1e-9:
        distances = np.linalg.norm(points - start, axis=1)
    else:
        relative = points - start
        distances = np.abs(
            (direction[0] * relative[:, 1] - direction[1] * relative[:, 0]) / length
        )
    split = int(np.argmax(distances))
    if distances[split] <= tolerance_m:
        return points[[0, -1]]
    return np.vstack((_rdp(points[: split + 1], tolerance_m)[:-1], _rdp(points[split:], tolerance_m)))


def _read_source_records(stac_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(stac_path.read_text(encoding="utf-8"))
    selected = {feature["id"]: feature for feature in payload["features"] if feature["id"] in SCENE_IDS}
    missing = sorted(set(SCENE_IDS) - set(selected))
    if missing:
        raise ValueError(f"selected Sentinel scenes missing from STAC response: {missing}")
    return [
        {
            "item_id": scene_id,
            "datetime_utc": selected[scene_id]["properties"]["datetime"],
            "cloud_cover_percent": selected[scene_id]["properties"]["eo:cloud_cover"],
            "green_href": selected[scene_id]["assets"]["green"]["href"],
            "nir_href": selected[scene_id]["assets"]["nir"]["href"],
        }
        for scene_id in SCENE_IDS
    ]


def _read_band_mosaic(
    source_records: list[dict[str, Any]],
    asset_key: str,
    bounds_wgs84: tuple[float, float, float, float],
) -> tuple[np.ndarray, Any]:
    try:
        import rasterio
        from rasterio.transform import from_origin
        from rasterio.warp import Resampling, reproject, transform_bounds
    except ImportError as exc:  # pragma: no cover - exercised by the acquisition CLI
        raise RuntimeError("rasterio is required to read the remote Sentinel COGs") from exc

    projected_bounds = transform_bounds("EPSG:4326", TARGET_CRS, *bounds_wgs84, densify_pts=21)
    west = math.floor(projected_bounds[0] / TARGET_RESOLUTION_M) * TARGET_RESOLUTION_M
    south = math.floor(projected_bounds[1] / TARGET_RESOLUTION_M) * TARGET_RESOLUTION_M
    east = math.ceil(projected_bounds[2] / TARGET_RESOLUTION_M) * TARGET_RESOLUTION_M
    north = math.ceil(projected_bounds[3] / TARGET_RESOLUTION_M) * TARGET_RESOLUTION_M
    width = int(round((east - west) / TARGET_RESOLUTION_M))
    height = int(round((north - south) / TARGET_RESOLUTION_M))
    transform = from_origin(west, north, TARGET_RESOLUTION_M, TARGET_RESOLUTION_M)
    accumulated = np.zeros((height, width), dtype=np.float64)
    counts = np.zeros((height, width), dtype=np.uint8)

    environment = {
        "GDAL_HTTP_MULTIRANGE": "YES",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    }
    with rasterio.Env(**environment):
        for record in source_records:
            with rasterio.open(record[asset_key]) as source:
                tile = np.zeros((height, width), dtype=np.float32)
                reproject(
                    source=rasterio.band(source, 1),
                    destination=tile,
                    src_transform=source.transform,
                    src_crs=source.crs,
                    src_nodata=source.nodata or 0,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    dst_nodata=0,
                    resampling=Resampling.bilinear,
                )
                valid = tile > 0.0
                accumulated[valid] += tile[valid]
                counts[valid] += 1
    result = np.zeros_like(accumulated, dtype=np.float32)
    valid = counts > 0
    result[valid] = (accumulated[valid] / counts[valid]).astype(np.float32)
    return result, transform


def _sample_observations(
    ndwi: np.ndarray,
    valid: np.ndarray,
    transform: Any,
    route_xy: np.ndarray,
    normals: np.ndarray,
    offsets_m: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    candidates = route_xy[:, None, :] + normals[:, None, :] * offsets_m[None, :, None]
    inverse = ~transform
    columns_f, rows_f = inverse * (candidates[..., 0], candidates[..., 1])
    rows = np.floor(rows_f).astype(np.int32)
    columns = np.floor(columns_f).astype(np.int32)
    inside = (
        (rows >= 0)
        & (rows < ndwi.shape[0])
        & (columns >= 0)
        & (columns < ndwi.shape[1])
    )
    observations = np.full(rows.shape, -1.0, dtype=np.float32)
    sampled_valid = np.zeros(rows.shape, dtype=bool)
    observations[inside] = ndwi[rows[inside], columns[inside]]
    sampled_valid[inside] = valid[rows[inside], columns[inside]]
    observations[~sampled_valid] = -1.0
    return observations, sampled_valid, candidates


def _topology_valid_candidates(
    candidate_xy: np.ndarray,
    route_xy: np.ndarray,
    stations_m: np.ndarray,
    offsets_m: np.ndarray,
    *,
    nonlocal_station_delta_m: float = 400.0,
    closer_margin_m: float = 10.0,
    batch_size: int = 48,
) -> np.ndarray:
    """Reject lateral candidates that land closer to a nonlocal route branch."""

    valid = np.ones(candidate_xy.shape[:2], dtype=bool)
    route_f32 = route_xy.astype(np.float32)
    for start in range(0, len(route_xy), batch_size):
        end = min(start + batch_size, len(route_xy))
        batch = candidate_xy[start:end].reshape(-1, 2).astype(np.float32)
        delta = batch[:, None, :] - route_f32[None, :, :]
        nearest_indices = np.argmin(np.sum(delta * delta, axis=2), axis=1)
        nearest_points = route_f32[nearest_indices]
        nearest_distance = np.linalg.norm(batch - nearest_points, axis=1)
        station_indices = np.repeat(np.arange(start, end), len(offsets_m))
        station_delta = np.abs(stations_m[nearest_indices] - stations_m[station_indices])
        own_distance = np.tile(np.abs(offsets_m), end - start)
        rejected = (
            (station_delta > nonlocal_station_delta_m)
            & (nearest_distance + closer_margin_m < own_distance)
        )
        valid[start:end] = (~rejected).reshape(end - start, len(offsets_m))
    return valid


def _mean_lateral_window(values: np.ndarray, radius: int = 2) -> np.ndarray:
    padded = np.pad(values, ((0, 0), (radius, radius)), mode="edge")
    cumulative = np.cumsum(padded, axis=1, dtype=np.float64)
    cumulative = np.pad(cumulative, ((0, 0), (1, 0)), mode="constant")
    width = radius * 2 + 1
    return ((cumulative[:, width:] - cumulative[:, :-width]) / width).astype(np.float32)


def _draw_overlay(
    source_visual: Path,
    output: Path,
    bounds_wgs84: tuple[float, float, float, float],
    route_lon_lat: np.ndarray,
    raw_candidate_lon_lat: np.ndarray,
    candidate_lon_lat: np.ndarray,
) -> None:
    image = Image.open(source_visual).convert("RGB")
    west, south, east, north = bounds_wgs84

    def pixels(points: np.ndarray) -> list[tuple[int, int]]:
        return [
            (
                int(round((lon - west) / (east - west) * (image.width - 1))),
                int(round((north - lat) / (north - south) * (image.height - 1))),
            )
            for lon, lat in points
        ]

    draw = ImageDraw.Draw(image)
    draw.line(pixels(route_lon_lat), fill=(255, 196, 48), width=4, joint="curve")
    draw.line(pixels(raw_candidate_lon_lat), fill=(255, 56, 166), width=3, joint="curve")
    draw.line(pixels(candidate_lon_lat), fill=(35, 236, 255), width=3, joint="curve")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def _large_shift_review_features(
    stations_m: np.ndarray,
    selected_offsets_m: np.ndarray,
    candidate_ndwi: np.ndarray,
    candidate_lon_lat: np.ndarray,
    review_flag: str,
    threshold_m: float = 100.0,
) -> tuple[list[dict[str, Any]], list[dict[str, float]]]:
    flagged = np.abs(selected_offsets_m) >= threshold_m
    features: list[dict[str, Any]] = []
    ranges: list[dict[str, float]] = []
    start: int | None = None
    for index in range(len(flagged) + 1):
        active = bool(flagged[index]) if index < len(flagged) else False
        if active and start is None:
            start = index
        if not active and start is not None:
            end = index - 1
            local_peak = start + int(np.argmax(np.abs(selected_offsets_m[start : end + 1])))
            properties = {
                "river_id": RIVER_ID,
                "review_flag": review_flag,
                "start_station_m": round(float(stations_m[start]), 3),
                "end_station_m": round(float(stations_m[end]), 3),
                "peak_station_m": round(float(stations_m[local_peak]), 3),
                "peak_signed_lateral_shift_m": round(
                    float(selected_offsets_m[local_peak]), 3
                ),
                "peak_candidate_ndwi": round(float(candidate_ndwi[local_peak]), 6),
                "production_authority": False,
            }
            features.append(
                {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": {
                        "type": "Point",
                        "coordinates": candidate_lon_lat[local_peak].tolist(),
                    },
                }
            )
            ranges.append(
                {
                    "start_station_m": properties["start_station_m"],
                    "end_station_m": properties["end_station_m"],
                    "peak_station_m": properties["peak_station_m"],
                    "peak_absolute_lateral_shift_m": abs(
                        properties["peak_signed_lateral_shift_m"]
                    ),
                }
            )
            start = None
    return features, ranges


def build_zambezi_sentinel_centerline_candidate(repo_root: Path) -> dict[str, Any]:
    """Read selected remote Sentinel COGs and write bounded review artifacts."""

    try:
        from rasterio.warp import transform
    except ImportError as exc:  # pragma: no cover - exercised by the acquisition CLI
        raise RuntimeError("rasterio is required to build the Sentinel centerline candidate") from exc

    repo_root = repo_root.resolve()
    river_root = repo_root / "physics/data/real_world/zambezi_batoka_gorge"
    corridor_root = river_root / "production_corridor/boiling_pot_to_mukuni_beach"
    corridor_manifest_path = corridor_root / "manifest.json"
    route_path = corridor_root / "hydrography/route_centerline.geojson"
    stac_path = river_root / "imagery/source/earth_search_stac_response.json"
    visual_path = river_root / "imagery/source/sentinel2_20260610_route_visual.png"
    corridor_manifest = json.loads(corridor_manifest_path.read_text(encoding="utf-8"))
    bounds = tuple(float(value) for value in corridor_manifest["bounds_wgs84"])
    route_payload = json.loads(route_path.read_text(encoding="utf-8"))
    route_lon_lat = np.asarray(route_payload["features"][0]["geometry"]["coordinates"], dtype=np.float64)
    source_records = _read_source_records(stac_path)

    green, raster_transform = _read_band_mosaic(source_records, "green_href", bounds)
    nir, nir_transform = _read_band_mosaic(source_records, "nir_href", bounds)
    if raster_transform != nir_transform or green.shape != nir.shape:
        raise ValueError("Sentinel green and NIR mosaics do not share the target grid")
    valid = (green > 0.0) & (nir > 0.0)
    ndwi = np.full(green.shape, -1.0, dtype=np.float32)
    denominator = green + nir
    ndwi[valid] = (green[valid] - nir[valid]) / np.maximum(denominator[valid], 1e-6)

    route_x, route_y = transform(
        "EPSG:4326", TARGET_CRS, route_lon_lat[:, 0].tolist(), route_lon_lat[:, 1].tolist()
    )
    route_xy = np.column_stack((route_x, route_y))
    dense_route, stations_m = _densify(route_xy, ROUTE_SAMPLE_SPACING_M)
    normals = _normals(dense_route)
    offsets = np.arange(
        -MAXIMUM_LATERAL_SEARCH_M,
        MAXIMUM_LATERAL_SEARCH_M + TARGET_RESOLUTION_M,
        TARGET_RESOLUTION_M,
        dtype=np.float64,
    )
    observations, sampled_valid, lateral_candidates = _sample_observations(
        ndwi, valid, raster_transform, dense_route, normals, offsets
    )
    water_likelihood = np.clip(
        (observations - WATER_NDWI_THRESHOLD) / 0.35,
        0.0,
        1.0,
    )
    lateral_support = _mean_lateral_window(water_likelihood)
    normalized_offset = offsets[None, :] / MAXIMUM_LATERAL_SEARCH_M
    scores = 3.0 * water_likelihood + 1.5 * lateral_support - 0.18 * normalized_offset**2
    scores[~sampled_valid] = -50.0
    unguarded_offsets = _smooth_offsets(
        select_centerline_offsets(scores, offsets), stations_m
    )
    topology_valid = _topology_valid_candidates(
        lateral_candidates,
        dense_route,
        stations_m,
        offsets,
    )
    guarded_scores = scores.copy()
    guarded_scores[~topology_valid] = -50.0
    selected_offsets = _smooth_offsets(
        select_centerline_offsets(guarded_scores, offsets), stations_m
    )
    unguarded_candidate_xy = dense_route + normals * unguarded_offsets[:, None]
    candidate_xy = dense_route + normals * selected_offsets[:, None]

    candidate_x = candidate_xy[:, 0].tolist()
    candidate_y = candidate_xy[:, 1].tolist()
    candidate_lon, candidate_lat = transform(TARGET_CRS, "EPSG:4326", candidate_x, candidate_y)
    candidate_lon_lat_dense = np.column_stack((candidate_lon, candidate_lat))
    unguarded_lon, unguarded_lat = transform(
        TARGET_CRS,
        "EPSG:4326",
        unguarded_candidate_xy[:, 0].tolist(),
        unguarded_candidate_xy[:, 1].tolist(),
    )
    unguarded_lon_lat_dense = np.column_stack((unguarded_lon, unguarded_lat))
    simplified_xy = _rdp(candidate_xy, tolerance_m=8.0)
    simplified_lon, simplified_lat = transform(
        TARGET_CRS,
        "EPSG:4326",
        simplified_xy[:, 0].tolist(),
        simplified_xy[:, 1].tolist(),
    )
    simplified_lon_lat = np.column_stack((simplified_lon, simplified_lat))

    selected_indices = np.rint(
        (selected_offsets + MAXIMUM_LATERAL_SEARCH_M) / TARGET_RESOLUTION_M
    ).astype(np.int32)
    selected_indices = np.clip(selected_indices, 0, len(offsets) - 1)
    route_index = int(round(MAXIMUM_LATERAL_SEARCH_M / TARGET_RESOLUTION_M))
    row_indices = np.arange(len(stations_m))
    route_ndwi = observations[:, route_index]
    candidate_ndwi = observations[row_indices, selected_indices]
    unguarded_indices = np.rint(
        (unguarded_offsets + MAXIMUM_LATERAL_SEARCH_M) / TARGET_RESOLUTION_M
    ).astype(np.int32)
    unguarded_indices = np.clip(unguarded_indices, 0, len(offsets) - 1)
    unguarded_ndwi = observations[row_indices, unguarded_indices]
    review_features, large_shift_ranges = _large_shift_review_features(
        stations_m,
        selected_offsets,
        candidate_ndwi,
        candidate_lon_lat_dense,
        "guarded_large_lateral_shift_requires_manual_water_and_bank_review",
    )
    unguarded_review_features, unguarded_large_shift_ranges = _large_shift_review_features(
        stations_m,
        unguarded_offsets,
        unguarded_ndwi,
        unguarded_lon_lat_dense,
        "raw_cross_channel_snap_rejected_by_route_topology_guard",
    )
    review_features = [*unguarded_review_features, *review_features]

    imagery_review_root = river_root / "imagery/review"
    hydrography_review_root = river_root / "hydrography/review"
    imagery_review_root.mkdir(parents=True, exist_ok=True)
    hydrography_review_root.mkdir(parents=True, exist_ok=True)
    ndwi_path = imagery_review_root / "sentinel2_20260610_ndwi_corridor.png"
    ndwi_encoded = np.rint(np.clip((ndwi + 1.0) * 127.5, 0.0, 255.0)).astype(np.uint8)
    ndwi_encoded[~valid] = 0
    Image.fromarray(ndwi_encoded, mode="L").save(ndwi_path)
    overlay_path = imagery_review_root / "sentinel2_20260610_centerline_comparison.png"
    _draw_overlay(
        visual_path,
        overlay_path,
        bounds,
        route_lon_lat,
        unguarded_lon_lat_dense,
        candidate_lon_lat_dense,
    )

    candidate_path = hydrography_review_root / "sentinel2_20260610_centerline_candidate.geojson"
    candidate_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "river_id": RIVER_ID,
                    "reach": "Boiling Pot to Mukuni Beach",
                    "source": "Copernicus Sentinel-2 L2A green/NIR surface-water observation",
                    "status": "review_candidate_not_production_geometry",
                    "geometry_authority": "10m_surface_water_observation_not_surveyed_centerline_or_bathymetry",
                    "source_scene_ids": list(SCENE_IDS),
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": simplified_lon_lat.tolist(),
                },
            },
            *review_features,
        ],
    }
    candidate_path.write_text(json.dumps(candidate_payload, indent=2) + "\n", encoding="utf-8")

    manifest_path = hydrography_review_root / "sentinel2_20260610_centerline_candidate_manifest.json"
    absolute_offsets = np.abs(selected_offsets)
    valid_route = route_ndwi > -0.999
    valid_candidate = candidate_ndwi > -0.999
    shared_valid = valid_route & valid_candidate
    measurements = {
        "source_route_length_m": round(_polyline_length(route_xy), 4),
        "candidate_dense_length_m": round(_polyline_length(candidate_xy), 4),
        "candidate_simplified_length_m": round(_polyline_length(simplified_xy), 4),
        "source_route_point_count": int(len(route_xy)),
        "candidate_dense_point_count": int(len(candidate_xy)),
        "candidate_simplified_point_count": int(len(simplified_xy)),
        "median_absolute_lateral_shift_m": round(float(np.median(absolute_offsets)), 4),
        "p95_absolute_lateral_shift_m": round(float(np.percentile(absolute_offsets, 95)), 4),
        "maximum_absolute_lateral_shift_m": round(float(absolute_offsets.max()), 4),
        "large_shift_review_threshold_m": 100.0,
        "large_shift_sample_count": int(np.count_nonzero(absolute_offsets >= 100.0)),
        "large_shift_station_ranges": large_shift_ranges,
        "topology_rejected_lateral_candidate_count": int(np.count_nonzero(~topology_valid)),
        "unguarded_maximum_absolute_lateral_shift_m": round(
            float(np.abs(unguarded_offsets).max()), 4
        ),
        "unguarded_large_shift_station_ranges": unguarded_large_shift_ranges,
        "source_route_water_support_fraction": round(
            float(np.mean(route_ndwi[valid_route] >= WATER_NDWI_THRESHOLD)), 6
        ),
        "candidate_water_support_fraction": round(
            float(np.mean(candidate_ndwi[valid_candidate] >= WATER_NDWI_THRESHOLD)), 6
        ),
        "candidate_ndwi_improves_fraction": round(
            float(np.mean(candidate_ndwi[shared_valid] > route_ndwi[shared_valid])), 6
        ),
        "source_route_median_ndwi": round(float(np.median(route_ndwi[valid_route])), 6),
        "candidate_median_ndwi": round(float(np.median(candidate_ndwi[valid_candidate])), 6),
    }
    manifest = {
        "schema": "raftsim.zambezi_sentinel_centerline_candidate.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "river_id": RIVER_ID,
        "status": "surface_water_observation_review_candidate_not_production_geometry",
        "production_promoted": False,
        "source": {
            "stac_response": str(stac_path.relative_to(repo_root)),
            "stac_response_sha256": _sha256(stac_path),
            "visual_reference": str(visual_path.relative_to(repo_root)),
            "visual_reference_sha256": _sha256(visual_path),
            "scenes": source_records,
            "license": "Copernicus Sentinel Data Legal Notice",
        },
        "processing": {
            "target_crs": TARGET_CRS,
            "target_resolution_m": TARGET_RESOLUTION_M,
            "bounds_wgs84": list(bounds),
            "raster_width": int(ndwi.shape[1]),
            "raster_height": int(ndwi.shape[0]),
            "ndwi_formula": "(Sentinel-2 B03 green - B08 NIR) / (B03 + B08)",
            "water_ndwi_threshold": WATER_NDWI_THRESHOLD,
            "route_sample_spacing_m": ROUTE_SAMPLE_SPACING_M,
            "maximum_lateral_search_m": MAXIMUM_LATERAL_SEARCH_M,
            "endpoint_taper_m": 200.0,
            "simplification_tolerance_m": 8.0,
            "route_topology_guard": {
                "nonlocal_station_delta_m": 400.0,
                "closer_margin_m": 10.0,
                "policy": "reject a lateral sample when it is materially closer to a route branch more than 400 m away in station space",
            },
        },
        "measurements": measurements,
        "authority": {
            "surveyed_centerline": False,
            "bathymetry": False,
            "bank_geometry": False,
            "rapid_or_hazard_geometry": False,
            "may_replace_production_corridor": False,
            "changes_cpp_solver_or_geoclaw_state": False,
            "allowed_use": "visual alignment review, source comparison, and survey acquisition QA",
        },
        "outputs": {
            "candidate_geojson": {
                "path": str(candidate_path.relative_to(repo_root)),
                "sha256": _sha256(candidate_path),
            },
            "ndwi_preview": {
                "path": str(ndwi_path.relative_to(repo_root)),
                "sha256": _sha256(ndwi_path),
                "encoding": "uint8 where 0..255 maps NDWI -1..1; invalid pixels are 0",
            },
            "comparison_overlay": {
                "path": str(overlay_path.relative_to(repo_root)),
                "sha256": _sha256(overlay_path),
                "legend": {
                    "osm_route": "yellow",
                    "unguarded_rejected_candidate": "magenta",
                    "topology_guarded_candidate": "cyan",
                },
            },
        },
        "promotion_gates": [
            "manual cloud, shadow, whitewater, island, tributary, and bank review",
            "guide confirms put-in, take-out, route order, named-rapid stations, and navigable channel",
            "geospatial reviewer compares against high-resolution survey terrain, orthophoto, banks, and breaklines",
            "rights reviewer confirms derivative and attribution handling",
            "candidate is regenerated against accepted terrain before any Unreal or solver binding",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
