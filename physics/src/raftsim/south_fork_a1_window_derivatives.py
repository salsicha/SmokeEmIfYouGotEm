"""Generate South Fork A1 full-reach review derivatives from source windows."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
)
from .south_fork_a1_window_manifests import (
    FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
)
from .south_fork_a1_stationing import FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH
from .south_fork_a1_window_source_pulls import (
    ADOPTED_AXIS_ROUTE_BASIS,
    ADOPTED_ROUTE_FEATURE_ID,
    DIRECTED_CLIP_ROUTE_BASIS,
    DIRECTED_CLIP_STATION_END_M,
    _lon_lat_to_web_mercator,
    _route_coordinates_with_station,
)
from .south_fork_a1_window_stitched_validation import (
    FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH,
)


FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_derivative_manifest.json"
)

HEIGHTFIELD_SIZE_PX = 2017
REVIEW_SIZE_PX = 2048


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_dem(path: Path) -> np.ndarray:
    dem = np.asarray(Image.open(path), dtype=np.float32)
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError(f"DEM contains no finite samples: {path}")
    fill_value = float(np.median(dem[finite]))
    return np.where(finite, dem, fill_value).astype(np.float32)


def _write_heightfield(dem: np.ndarray, path: Path) -> dict[str, Any]:
    elevation_min_m = float(np.min(dem))
    elevation_max_m = float(np.max(dem))
    span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((dem - elevation_min_m) / span_m, 0.0, 1.0)
    image = Image.fromarray(np.round(normalized * 65535.0).astype(np.uint16))
    image = image.resize((HEIGHTFIELD_SIZE_PX, HEIGHTFIELD_SIZE_PX), Image.Resampling.BILINEAR)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return {
        "elevation_min_m": round(elevation_min_m, 6),
        "elevation_max_m": round(elevation_max_m, 6),
        "elevation_span_m": round(elevation_max_m - elevation_min_m, 6),
        "normalization": "source DEM min/max mapped linearly to 0..65535",
    }


def _write_hillshade(
    dem: np.ndarray,
    path: Path,
    pixel_resolution_m: list[float],
) -> None:
    pixel_x = float(pixel_resolution_m[0])
    pixel_y = float(pixel_resolution_m[1])
    row_gradient, column_gradient = np.gradient(dem, pixel_y, pixel_x)
    normal_x = -column_gradient
    normal_y = row_gradient
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
    shade = np.clip((shade - 0.08) / 0.92, 0.0, 1.0) ** 0.72
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.round(shade * 255.0).astype(np.uint8), mode="L").save(path)


def _route_points(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    route_clips = _load_json(repo_root, FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH)
    adopted_route = _load_json(repo_root, FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH)
    return {
        DIRECTED_CLIP_ROUTE_BASIS: _route_coordinates_with_station(route_clips),
        ADOPTED_AXIS_ROUTE_BASIS: _route_coordinates_with_station(
            adopted_route, ADOPTED_ROUTE_FEATURE_ID
        ),
    }


def _route_basis_for_window(station_end_m: float) -> str:
    if station_end_m <= DIRECTED_CLIP_STATION_END_M + 1e-6:
        return DIRECTED_CLIP_ROUTE_BASIS
    return ADOPTED_AXIS_ROUTE_BASIS


def _window_route_points(
    route_points: list[dict[str, Any]],
    station_start_m: float,
    station_end_m: float,
) -> list[dict[str, Any]]:
    points = [
        point
        for point in route_points
        if station_start_m <= float(point["approx_station_m"]) <= station_end_m
    ]
    if len(points) >= 2:
        return points

    nearest = sorted(
        route_points,
        key=lambda point: min(
            abs(float(point["approx_station_m"]) - station_start_m),
            abs(float(point["approx_station_m"]) - station_end_m),
        ),
    )
    return sorted(nearest[:2], key=lambda point: float(point["approx_station_m"]))


def _pixel_points(
    points: list[dict[str, Any]],
    bounds_epsg3857: list[float],
    size_px: int,
) -> list[tuple[int, int]]:
    min_x, min_y, max_x, max_y = bounds_epsg3857
    pixels: list[tuple[int, int]] = []
    for point in points:
        lon, lat = point["lon_lat"]
        x, y = _lon_lat_to_web_mercator(lon, lat)
        normalized_x = (x - min_x) / (max_x - min_x)
        normalized_y = (y - min_y) / (max_y - min_y)
        if -0.05 <= normalized_x <= 1.05 and -0.05 <= normalized_y <= 1.05:
            pixels.append(
                (
                    int(round(np.clip(normalized_x, 0.0, 1.0) * (size_px - 1))),
                    int(round((1.0 - np.clip(normalized_y, 0.0, 1.0)) * (size_px - 1))),
                )
            )
    return pixels


def _write_centerline_preview(
    naip_path: Path,
    output_path: Path,
    pixel_points: list[tuple[int, int]],
) -> None:
    image = Image.open(naip_path).convert("RGB").resize(
        (REVIEW_SIZE_PX, REVIEW_SIZE_PX),
        Image.Resampling.LANCZOS,
    )
    draw = ImageDraw.Draw(image)
    if len(pixel_points) >= 2:
        draw.line(pixel_points, fill=(255, 255, 255), width=10, joint="curve")
        draw.line(pixel_points, fill=(255, 54, 40), width=5, joint="curve")
        for point, color in (
            (pixel_points[0], (80, 220, 255)),
            (pixel_points[-1], (255, 218, 78)),
        ):
            x, y = point
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color, outline=(20, 20, 20))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _matching_seams(stitched_report: dict[str, Any], window_id: str) -> dict[str, Any]:
    upstream = None
    downstream = None
    for seam in stitched_report["seams"]:
        if seam["downstream_window_id"] == window_id:
            upstream = seam
        if seam["upstream_window_id"] == window_id:
            downstream = seam
    return {"upstream": upstream, "downstream": downstream}


def _artifact_record(path: Path, repo_root: Path, dimensions: list[int], pixel_format: str) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(repo_root)),
        "sha256": _sha256(path),
        "dimensions": dimensions,
        "pixel_format": pixel_format,
    }


def _generate_window_derivatives(
    repo_root: Path,
    window_manifest: dict[str, Any],
    stitched_report: dict[str, Any],
    route_points_by_basis: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    targets = window_manifest["derivative_targets"]
    dem_artifact = window_manifest["source_artifacts"]["dem"]
    aerial_artifact = window_manifest["source_artifacts"]["aerial"]
    dem_path = repo_root / dem_artifact["path"]
    aerial_path = repo_root / aerial_artifact["path"]
    heightfield_path = repo_root / targets["heightfield"]
    hillshade_path = repo_root / targets["hillshade"]
    preview_path = repo_root / targets["naip_centerline_preview"]
    edge_report_path = repo_root / targets["window_stitched_edge_report"]

    dem = _load_dem(dem_path)
    heightfield_processing = _write_heightfield(dem, heightfield_path)
    _write_hillshade(dem, hillshade_path, dem_artifact["pixel_resolution_m_approx"])

    station = window_manifest["station_range_m"]
    route_basis = _route_basis_for_window(float(station["end"]))
    window_points = _window_route_points(
        route_points_by_basis[route_basis],
        float(station["start"]),
        float(station["end"]),
    )
    pixels = _pixel_points(
        window_points,
        dem_artifact["source_bounds_epsg3857"],
        REVIEW_SIZE_PX,
    )
    _write_centerline_preview(aerial_path, preview_path, pixels)

    edge_report = {
        "schema": "raftsim.south_fork.a1_window_stitched_edge_report.v1",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": window_manifest["river_id"],
        "window_id": window_manifest["window_id"],
        "display_name": window_manifest["display_name"],
        "status": "review_derivatives_generated_not_promoted",
        "production_promoted": False,
        "inputs": {
            "window_manifest": str(
                Path(targets["window_stitched_edge_report"]).parents[1] / "manifest.json"
            ),
            "stitched_validation_report": FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH,
            "directed_route_clips": FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
            "adopted_route_geojson": FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
        },
        "station_range_m": station,
        "route_overlay": {
            "route_basis": route_basis,
            "route_sample_count": len(window_points),
            "visible_pixel_count": len(pixels),
            "line_drawn": len(pixels) >= 2,
        },
        "edge_seams": _matching_seams(stitched_report, window_manifest["window_id"]),
        "derived_artifacts": {
            "heightfield": _artifact_record(
                heightfield_path,
                repo_root,
                [HEIGHTFIELD_SIZE_PX, HEIGHTFIELD_SIZE_PX],
                "16_bit_grayscale_png",
            )
            | heightfield_processing,
            "hillshade": _artifact_record(
                hillshade_path,
                repo_root,
                [REVIEW_SIZE_PX, REVIEW_SIZE_PX],
                "8_bit_grayscale_png",
            ),
            "naip_centerline_preview": _artifact_record(
                preview_path,
                repo_root,
                [REVIEW_SIZE_PX, REVIEW_SIZE_PX],
                "8_bit_rgb_png",
            ),
        },
        "promotion_gate": {
            "can_enter_visual_derivative_review": True,
            "can_import_unreal_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
        },
        "review_notes": [
            "Heightfield and hillshade are DEM-only review derivatives, not hydrologically conditioned terrain.",
            "NAIP centerline overlay shows the recorded review route basis against the source imagery window.",
            "Seams remain explicit so derivative review cannot hide source-window discontinuities.",
            "Banks, cross sections, and Unreal import remain blocked; the Salmon Falls bank-landing refinement rides the P7 owner packet.",
        ],
    }
    _write_json(edge_report_path, edge_report)
    return edge_report


def _window_records_from_edge_reports(
    repo_root: Path,
    manifest_index: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for entry in manifest_index["window_manifests"]:
        window_manifest = _load_json(repo_root, str(entry["manifest_path"]))
        edge_report_path = repo_root / window_manifest["derivative_targets"]["window_stitched_edge_report"]
        edge_report = json.loads(edge_report_path.read_text(encoding="utf-8"))
        records.append(
            {
                "window_id": window_manifest["window_id"],
                "display_name": window_manifest["display_name"],
                "station_range_m": window_manifest["station_range_m"],
                "edge_report": {
                    "path": str(edge_report_path.relative_to(repo_root)),
                    "sha256": _sha256(edge_report_path),
                },
                "route_overlay": edge_report["route_overlay"],
                "derived_artifacts": edge_report["derived_artifacts"],
                "promotion_gate": edge_report["promotion_gate"],
            }
        )
    return sorted(records, key=lambda record: float(record["station_range_m"]["start"]))


def build_south_fork_a1_window_derivative_manifest(repo_root: Path) -> dict[str, Any]:
    """Build a deterministic manifest for already generated review derivatives."""

    repo_root = repo_root.resolve()
    manifest_index = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH)
    stitched_report = _load_json(repo_root, FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH)
    windows = _window_records_from_edge_reports(repo_root, manifest_index)
    derivative_count = sum(len(window["derived_artifacts"]) for window in windows)
    return {
        "schema": "raftsim.south_fork.a1_full_reach_window_derivatives.v1",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": manifest_index["river_id"],
        "status": "review_derivatives_generated_anchor_and_bank_review_pending",
        "production_promoted": False,
        "inputs": {
            "source_manifest_index": FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
            "stitched_validation_report": FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH,
            "directed_route_clips": FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
            "adopted_route_geojson": FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
        },
        "summary": {
            "window_count": len(windows),
            "seam_count": stitched_report["summary"]["seam_count"],
            "derived_png_count": derivative_count,
            "edge_report_count": len(windows),
            "heightfield_count": sum(
                "heightfield" in window["derived_artifacts"] for window in windows
            ),
            "hillshade_count": sum(
                "hillshade" in window["derived_artifacts"] for window in windows
            ),
            "naip_centerline_preview_count": sum(
                "naip_centerline_preview" in window["derived_artifacts"]
                for window in windows
            ),
            "all_route_overlays_drawn": all(
                window["route_overlay"]["line_drawn"] for window in windows
            ),
            "can_enter_visual_derivative_review": True,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
        },
        "windows": windows,
        "promotion_gate": {
            "can_enter_visual_derivative_review": True,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
            "next_required_actions": [
                "Visually review every heightfield, hillshade, NAIP overlay, and edge report.",
                "Confirm the adopted Salmon Falls take-out bank landing via the P7 owner packet before final crop.",
                "Add bank/cross-section interpretation and named rapid geometry review.",
                "Only after review, generate hydrologically conditioned terrain for Unreal import tests.",
            ],
        },
    }


def write_south_fork_a1_window_derivatives(repo_root: Path) -> Path:
    repo_root = repo_root.resolve()
    manifest_index = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH)
    stitched_report = _load_json(repo_root, FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH)
    route_points = _route_points(repo_root)
    for entry in manifest_index["window_manifests"]:
        window_manifest = _load_json(repo_root, str(entry["manifest_path"]))
        _generate_window_derivatives(
            repo_root,
            window_manifest,
            stitched_report,
            route_points,
        )

    payload = build_south_fork_a1_window_derivative_manifest(repo_root)
    output_path = repo_root / FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH
    _write_json(output_path, payload)
    return output_path
