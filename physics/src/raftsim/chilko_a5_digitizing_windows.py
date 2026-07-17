"""Generate review-only Chilko A5 rapid digitizing work windows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .chilko_a5_digitizing import (
    CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
    build_chilko_a5_digitizing_action_packet,
)


CHILKO_A5_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_bc/review/"
    "a5_stationing_digitizing_work_windows.geojson"
)
CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_bc/review/"
    "a5_stationing_digitizing_work_window_manifest.json"
)
CHILKO_A5_DIGITIZING_WORK_WINDOWS_SCHEMA = (
    "raftsim.chilko.a5_stationing_digitizing_work_windows.geojson.v1"
)
CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA = (
    "raftsim.chilko.a5_stationing_digitizing_work_window_manifest.v1"
)

_WINDOW_BY_PRIORITY = {
    "critical": {"half_length_m": 900.0, "lateral_review_buffer_m": 180.0},
    "high": {"half_length_m": 650.0, "lateral_review_buffer_m": 140.0},
    "medium": {"half_length_m": 450.0, "lateral_review_buffer_m": 100.0},
}


def build_chilko_a5_digitizing_work_windows_geojson(repo_root: Path) -> dict[str, Any]:
    """Build review-only Chilko rapid work windows on the current route scaffold."""

    packet = build_chilko_a5_digitizing_action_packet(repo_root)
    route_stationing_path = packet["source_route_stationing"]
    route_stationing = _load_json(repo_root / route_stationing_path)
    samples = route_stationing["samples"]
    route_length_m = float(route_stationing["length_m"])
    features = [
        _work_window_feature(action, samples, route_length_m, packet, route_stationing_path)
        for action in packet["digitizing_actions"]
    ]
    return {
        "type": "FeatureCollection",
        "schema": CHILKO_A5_DIGITIZING_WORK_WINDOWS_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A5",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": "review_only_digitizing_windows_on_route_scaffold_not_authoritative",
        "production_promoted": False,
        "source_action_packet": CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_stationing": route_stationing_path,
        "review_limits": [
            "Window center stations are provisional downstream-order stations on the current source-scale route scaffold.",
            "The current FWA route is technical corridor evidence, not guide-approved exact rapid stationing.",
            "These features only focus manual aerial/guide digitizing review and cannot replace exact GPS, aerial, or guide-reviewed stationing.",
            "Do not bind editor geometry, water windows, solver windows, public screenshots, or gameplay hazards from these windows.",
        ],
        "features": features,
    }


def write_chilko_a5_digitizing_work_windows_geojson(repo_root: Path) -> Path:
    payload = build_chilko_a5_digitizing_work_windows_geojson(repo_root)
    path = repo_root / CHILKO_A5_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_chilko_a5_digitizing_work_window_manifest(repo_root: Path) -> dict[str, Any]:
    """Summarize the Chilko A5 digitizing work windows and promotion gates."""

    packet = build_chilko_a5_digitizing_action_packet(repo_root)
    route_stationing_path = packet["source_route_stationing"]
    route_stationing = _load_json(repo_root / route_stationing_path)
    geojson = build_chilko_a5_digitizing_work_windows_geojson(repo_root)
    windows = [
        {
            "rapid_name": feature["properties"]["rapid_name"],
            "order": feature["properties"]["order"],
            "review_priority": feature["properties"]["review_priority"],
            "current_station_m_from_order_interpolation": feature["properties"][
                "current_station_m_from_order_interpolation"
            ],
            "route_order_station_m": feature["properties"]["route_order_station_m"],
            "window_start_m": feature["properties"]["window_start_m"],
            "window_end_m": feature["properties"]["window_end_m"],
            "half_length_m": feature["properties"]["half_length_m"],
            "lateral_review_buffer_m": feature["properties"]["lateral_review_buffer_m"],
            "coordinate_count": len(feature["geometry"]["coordinates"]),
        }
        for feature in geojson["features"]
    ]
    return {
        "schema": CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A5",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": "work_windows_ready_for_manual_digitizing_review_no_stationing_promotion",
        "production_promoted": False,
        "work_windows_geojson": CHILKO_A5_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH,
        "source_action_packet": CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_stationing": route_stationing_path,
        "rapid_count": len(windows),
        "critical_window_count": sum(
            1 for window in windows if window["review_priority"] == "critical"
        ),
        "route_stationing_length_m": route_stationing["length_m"],
        "catalog_run_length_m": packet["current_blockers"]["catalog_run_length_m"],
        "route_to_catalog_length_delta_m": round(
            float(route_stationing["length_m"])
            - float(packet["current_blockers"]["catalog_run_length_m"]),
            3,
        ),
        "window_policy": {
            "stationing_method": "order_distributed_on_current_route_scaffold_for_review_focus_only",
            "priority_window_sizes_m": _WINDOW_BY_PRIORITY,
            "not_authoritative_reason": (
                "The FWA route is suitable as a source-scale corridor axis, but the rapid "
                "stations are still order-only until exact GPS, aerial, and Chilko guide "
                "reviewed point/span geometry replaces these work windows."
            ),
        },
        "windows": windows,
        "promotion_gate": {
            "can_replace_order_interpolation": False,
            "can_regenerate_named_rapid_catalog": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a5": False,
            "complete_when": [
                "put-in, take-out, and current FWA route station axis are approved by guide and geospatial review",
                "accepted aerial or orthomosaic source is selected",
                "each priority rapid is digitized as exact point or span geometry",
                "guide/outfitter, geospatial, rights/land/publication, and 08MA002/08MA001 flow-context reviews approve",
                "the A5 digitizing result validator passes on reviewed records",
                "rapid water-window inputs are regenerated from reviewed stations and routed flow windows",
            ],
        },
    }


def write_chilko_a5_digitizing_work_window_manifest(repo_root: Path) -> Path:
    payload = build_chilko_a5_digitizing_work_window_manifest(repo_root)
    path = repo_root / CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _work_window_feature(
    action: dict[str, Any],
    samples: list[dict[str, Any]],
    route_length_m: float,
    packet: dict[str, Any],
    route_stationing_path: str,
) -> dict[str, Any]:
    priority = str(action["review_priority"])
    policy = _WINDOW_BY_PRIORITY[priority]
    route_station_m = float(action["route_order_station_m_for_review_focus"])
    half_length_m = policy["half_length_m"]
    start_m = round(max(0.0, route_station_m - half_length_m), 3)
    end_m = round(min(route_length_m, route_station_m + half_length_m), 3)
    coordinates = _line_coordinates_for_station_range(samples, start_m, end_m)
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
        "properties": {
            "window_id": f"chilko_a5_window_{int(action['order']):02d}_{_slug(action['rapid_name'])}",
            "river_id": packet["river_id"],
            "rapid_name": action["rapid_name"],
            "aliases": action["aliases"],
            "order": action["order"],
            "class": action["class"],
            "feature_tags": action["feature_tags"],
            "review_priority": priority,
            "current_stationing_kind": action["current_stationing_kind"],
            "current_station_m_from_order_interpolation": action[
                "current_station_m_from_order_interpolation"
            ],
            "route_order_station_m": round(route_station_m, 3),
            "window_start_m": start_m,
            "window_end_m": end_m,
            "half_length_m": half_length_m,
            "lateral_review_buffer_m": policy["lateral_review_buffer_m"],
            "stationing_status": "order_distributed_route_work_window_not_authoritative",
            "geometry_status": "review_focus_window_not_exact_rapid_geometry",
            "source_stationing": route_stationing_path,
            "source_action_packet": CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
            "promotion_gate": (
                "Use only to focus manual digitizing review. Replace with approved put-in, "
                "take-out, route station axis, GPS/aerial rapid point/span geometry, Chilko "
                "guide confirmation, rights/land/publication review, and 08MA002/08MA001 "
                "flow-context review before catalog, editor, water-window, or solver binding."
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
