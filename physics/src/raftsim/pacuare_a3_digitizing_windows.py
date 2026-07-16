"""Generate review-only Pacuare A3 rapid digitizing work windows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pacuare_a3_digitizing import PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH
from .pacuare_a3_stationing import (
    PACUARE_RIVER_ID,
    PREVIEW_STATIONING_RELATIVE_PATH,
    build_pacuare_a3_stationing_repair_status,
)


PACUARE_A3_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_digitizing_work_windows.geojson"
)
PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_digitizing_work_window_manifest.json"
)
PACUARE_A3_DIGITIZING_WORK_WINDOWS_SCHEMA = (
    "raftsim.pacuare.a3_stationing_digitizing_work_windows.geojson.v1"
)
PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA = (
    "raftsim.pacuare.a3_stationing_digitizing_work_window_manifest.v1"
)

_WINDOW_BY_PRIORITY = {
    "critical": {"half_length_m": 900.0, "lateral_review_buffer_m": 180.0},
    "high": {"half_length_m": 650.0, "lateral_review_buffer_m": 130.0},
    "medium": {"half_length_m": 450.0, "lateral_review_buffer_m": 90.0},
}


def build_pacuare_a3_digitizing_work_windows_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    """Build review-only rapid work windows on the current preview scaffold."""

    status = build_pacuare_a3_stationing_repair_status(repo_root)
    preview_stationing = _load_json(repo_root / PREVIEW_STATIONING_RELATIVE_PATH)
    samples = preview_stationing["station_samples"]
    preview_length_m = float(samples[-1]["station_m"])
    rapid_records = status["catalog_stationing_scaffold"]["rapid_stations"]
    features = [
        _work_window_feature(record, samples, preview_length_m, len(rapid_records))
        for record in rapid_records
    ]
    return {
        "type": "FeatureCollection",
        "schema": PACUARE_A3_DIGITIZING_WORK_WINDOWS_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": PACUARE_RIVER_ID,
        "status": "review_only_digitizing_windows_on_preview_scaffold_not_authoritative",
        "source_action_packet": PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_stationing": PREVIEW_STATIONING_RELATIVE_PATH,
        "review_limits": [
            "Window center stations are distributed by catalog rapid order over the preview scaffold length.",
            "The preview scaffold length still conflicts with the catalog run length.",
            "These features only focus human digitizing review and cannot replace GPS/aerial/guide-reviewed stations.",
            "Do not bind editor geometry, solver windows, public route screenshots, or gameplay hazards from these windows.",
        ],
        "features": features,
    }


def write_pacuare_a3_digitizing_work_windows_geojson(repo_root: Path) -> Path:
    payload = build_pacuare_a3_digitizing_work_windows_geojson(repo_root)
    path = repo_root / PACUARE_A3_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_pacuare_a3_digitizing_work_window_manifest(repo_root: Path) -> dict[str, Any]:
    """Summarize the Pacuare A3 digitizing work windows and promotion gates."""

    status = build_pacuare_a3_stationing_repair_status(repo_root)
    geojson = build_pacuare_a3_digitizing_work_windows_geojson(repo_root)
    preview_length_m = status["current_geometry_evidence"]["preview_length_m"]
    catalog_length_m = status["current_geometry_evidence"]["catalog_run_length_m"]
    windows = [
        {
            "rapid_name": feature["properties"]["rapid_name"],
            "order": feature["properties"]["order"],
            "review_priority": feature["properties"]["review_priority"],
            "preview_order_station_m": feature["properties"]["preview_order_station_m"],
            "catalog_order_station_m": feature["properties"]["catalog_order_station_m"],
            "window_start_m": feature["properties"]["window_start_m"],
            "window_end_m": feature["properties"]["window_end_m"],
            "half_length_m": feature["properties"]["half_length_m"],
            "lateral_review_buffer_m": feature["properties"]["lateral_review_buffer_m"],
            "coordinate_count": len(feature["geometry"]["coordinates"]),
        }
        for feature in geojson["features"]
    ]
    return {
        "schema": PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": PACUARE_RIVER_ID,
        "status": "work_windows_ready_for_manual_digitizing_review_no_stationing_promotion",
        "production_promoted": False,
        "work_windows_geojson": PACUARE_A3_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH,
        "source_action_packet": PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_stationing": PREVIEW_STATIONING_RELATIVE_PATH,
        "rapid_count": len(windows),
        "critical_window_count": sum(
            1 for window in windows if window["review_priority"] == "critical"
        ),
        "preview_length_m": preview_length_m,
        "catalog_run_length_m": catalog_length_m,
        "preview_to_catalog_length_ratio": status["current_geometry_evidence"][
            "preview_to_catalog_length_ratio"
        ],
        "window_policy": {
            "stationing_method": "order_distributed_on_preview_scaffold_for_review_focus_only",
            "priority_window_sizes_m": _WINDOW_BY_PRIORITY,
            "not_authoritative_reason": (
                "The preview scaffold is a generated route with a material length mismatch, "
                "and rapid stations remain order-only until reviewed source geometry exists."
            ),
        },
        "windows": windows,
        "promotion_gate": {
            "can_replace_order_interpolation": False,
            "can_regenerate_named_rapid_catalog": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a3": False,
            "complete_when": [
                "reviewed route centerline replaces the preview scaffold",
                "accepted aerial or orthomosaic source is selected",
                "each rapid is digitized as exact point or span geometry",
                "guide/outfitter, geospatial, rights/protected-area, and flow-source reviews approve",
                "the A3 digitizing result validator passes on reviewed records",
            ],
        },
    }


def write_pacuare_a3_digitizing_work_window_manifest(repo_root: Path) -> Path:
    payload = build_pacuare_a3_digitizing_work_window_manifest(repo_root)
    path = repo_root / PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _work_window_feature(
    record: dict[str, Any],
    samples: list[dict[str, Any]],
    preview_length_m: float,
    rapid_count: int,
) -> dict[str, Any]:
    priority = str(record["review_priority"])
    policy = _WINDOW_BY_PRIORITY[priority]
    preview_station_m = round(preview_length_m * int(record["order"]) / (rapid_count + 1), 3)
    half_length_m = policy["half_length_m"]
    start_m = round(max(0.0, preview_station_m - half_length_m), 3)
    end_m = round(min(preview_length_m, preview_station_m + half_length_m), 3)
    coordinates = _line_coordinates_for_station_range(samples, start_m, end_m)
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
        "properties": {
            "window_id": f"pacuare_a3_window_{int(record['order']):02d}_{_slug(record['name'])}",
            "river_id": PACUARE_RIVER_ID,
            "rapid_name": record["name"],
            "aliases": record["aliases"],
            "order": record["order"],
            "class": record["class"],
            "feature_tags": record["feature_tags"],
            "review_priority": priority,
            "catalog_order_station_m": record["station_m_from_order_interpolation"],
            "preview_order_station_m": preview_station_m,
            "window_start_m": start_m,
            "window_end_m": end_m,
            "half_length_m": half_length_m,
            "lateral_review_buffer_m": policy["lateral_review_buffer_m"],
            "stationing_status": "order_distributed_preview_work_window_not_authoritative",
            "geometry_status": "review_focus_window_not_exact_rapid_geometry",
            "source_stationing": PREVIEW_STATIONING_RELATIVE_PATH,
            "source_action_packet": PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
            "promotion_gate": (
                "Use only to focus manual digitizing review. Replace with accepted route, "
                "aerial/orthomosaic rapid point/span geometry, guide confirmation, rights "
                "review, and flow-source review before catalog, editor, water-window, or solver binding."
            ),
        },
    }


def _line_coordinates_for_station_range(
    samples: list[dict[str, Any]],
    start_m: float,
    end_m: float,
) -> list[list[float]]:
    coordinates = [_interpolate_lon_lat(samples, start_m)]
    for sample in samples:
        station_m = float(sample["station_m"])
        if start_m < station_m < end_m:
            coordinates.append([sample["lon"], sample["lat"]])
    coordinates.append(_interpolate_lon_lat(samples, end_m))
    return coordinates


def _interpolate_lon_lat(
    samples: list[dict[str, Any]],
    station_m: float,
) -> list[float]:
    if station_m <= float(samples[0]["station_m"]):
        return [samples[0]["lon"], samples[0]["lat"]]
    for left, right in zip(samples, samples[1:]):
        left_station = float(left["station_m"])
        right_station = float(right["station_m"])
        if left_station <= station_m <= right_station:
            span = right_station - left_station
            t = 0.0 if span == 0.0 else (station_m - left_station) / span
            lon = float(left["lon"]) + (float(right["lon"]) - float(left["lon"])) * t
            lat = float(left["lat"]) + (float(right["lat"]) - float(left["lat"])) * t
            return [round(lon, 7), round(lat, 7)]
    return [samples[-1]["lon"], samples[-1]["lat"]]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
