"""Audit where South Fork A1 published source miles diverge from access geometry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_full_reach_acquisition import ACCESS_POINTS_RELATIVE_PATH
from .south_fork_a1_nhd_extraction import FULL_REACH_NHD_GEOJSON_RELATIVE_PATH
from .south_fork_a1_official_access_geometry_review import (
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
)
from .south_fork_a1_official_access_reanchor_diagnostic import (
    FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
    FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH,
)
from .south_fork_a1_route_graph import (
    _build_graph,
    _geometry_lines,
    _haversine_m,
    _nearest_node,
    _node,
    _shortest_path,
)


FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_divergence_audit.json"
)
FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_divergence_overlay.geojson"
)

_PUBLISHED_BREAKPOINTS = (
    ("salmon_falls_20_5_mile_source_convention", 20.5),
    ("full_run_21_0_mile_source_convention", 21.0),
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _access_feature(access_points: dict[str, Any], annotation_id: str) -> dict[str, Any]:
    for feature in access_points["features"]:
        if feature["properties"]["annotation_id"] == annotation_id:
            return feature
    raise ValueError(f"Missing access feature {annotation_id}")


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _feature_coordinates(feature: dict[str, Any]) -> list[tuple[float, float]]:
    coordinates: list[tuple[float, float]] = []
    for line in _geometry_lines(feature["geometry"]):
        coordinates.extend((float(point[0]), float(point[1])) for point in line)
    return coordinates


def _interpolate_feature_lon_lat(
    feature: dict[str, Any],
    alpha: float,
) -> tuple[float, float]:
    coordinates = _feature_coordinates(feature)
    if len(coordinates) == 1:
        return _node(coordinates[0])

    segment_lengths = [
        _haversine_m(start, stop)
        for start, stop in zip(coordinates, coordinates[1:], strict=False)
    ]
    geometry_length_m = sum(segment_lengths)
    if geometry_length_m <= 0.0:
        return _node(coordinates[-1])

    target_m = max(0.0, min(alpha, 1.0)) * geometry_length_m
    accumulated_m = 0.0
    for start, stop, segment_length_m in zip(
        coordinates,
        coordinates[1:],
        segment_lengths,
        strict=False,
    ):
        if accumulated_m + segment_length_m >= target_m:
            segment_alpha = (
                0.0
                if segment_length_m <= 0.0
                else (target_m - accumulated_m) / segment_length_m
            )
            return (
                round(start[0] + (stop[0] - start[0]) * segment_alpha, 7),
                round(start[1] + (stop[1] - start[1]) * segment_alpha, 7),
            )
        accumulated_m += segment_length_m
    return _node(coordinates[-1])


def _path_context(repo_root: Path) -> dict[str, Any]:
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    official_review = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    )
    features = geojson["features"]
    edges, graph = _build_graph(features)
    chili = _access_feature(access_points, "chili_bar_put_in_review_seed")
    chili_lon_lat = (
        float(chili["properties"]["station_lon"]),
        float(chili["properties"]["station_lat"]),
    )
    official_seed = official_review["primary_official_access_geometry_lead"]
    official_lon_lat = tuple(float(value) for value in official_seed["lon_lat"])
    chili_node, chili_snap_distance_m = _nearest_node(graph, chili_lon_lat)
    official_node, official_snap_distance_m = _nearest_node(graph, official_lon_lat)
    distances, _previous, path_edges = _shortest_path(graph, chili_node, official_node)
    return {
        "features": features,
        "edges": edges,
        "path_edges": path_edges,
        "chili_lon_lat": chili_lon_lat,
        "chili_node": chili_node,
        "chili_snap_distance_m": chili_snap_distance_m,
        "official_seed": official_seed,
        "official_lon_lat": official_lon_lat,
        "official_node": official_node,
        "official_snap_distance_m": official_snap_distance_m,
        "official_source_station_m": float(distances[official_node]),
    }


def _project_source_station(context: dict[str, Any], station_m: float) -> dict[str, Any]:
    accumulated_m = 0.0
    features = context["features"]
    edges = context["edges"]
    for path_edge_index, graph_edge_index in enumerate(context["path_edges"]):
        edge = edges[graph_edge_index]
        edge_length_m = float(edge["length_m"])
        edge_start_m = accumulated_m
        edge_end_m = accumulated_m + edge_length_m
        if station_m <= edge_end_m or path_edge_index == len(context["path_edges"]) - 1:
            alpha = 0.0 if edge_length_m <= 0.0 else (station_m - edge_start_m) / edge_length_m
            alpha = max(0.0, min(alpha, 1.0))
            lon_lat = _interpolate_feature_lon_lat(
                features[edge["feature_index"]],
                alpha,
            )
            remaining_path_m = context["official_source_station_m"] - station_m
            return {
                "source_station_m": round(station_m, 6),
                "source_station_miles": round(station_m / MILES_TO_METERS, 3),
                "lon_lat": [lon_lat[0], lon_lat[1]],
                "path_edge_index": path_edge_index,
                "source_record_index": edge["source_record_index"],
                "source_record_number": edge["source_record_number"],
                "permanent_identifier": edge["permanent_identifier"],
                "edge_station_start_m": round(edge_start_m, 6),
                "edge_station_end_m": round(edge_end_m, 6),
                "edge_alpha": round(alpha, 6),
                "remaining_source_path_to_official_access_m": round(remaining_path_m, 6),
                "remaining_source_path_to_official_access_miles": round(
                    remaining_path_m / MILES_TO_METERS,
                    3,
                ),
                "geodesic_distance_to_official_access_m": round(
                    _haversine_m(lon_lat, context["official_lon_lat"]),
                    3,
                ),
            }
        accumulated_m = edge_end_m
    raise ValueError(f"Station {station_m} m is outside the official access path")


def _path_coordinates_between_stations(
    context: dict[str, Any],
    start_station_m: float,
    end_station_m: float,
) -> list[list[float]]:
    start = _project_source_station(context, start_station_m)
    end = _project_source_station(context, end_station_m)
    features = context["features"]
    edges = context["edges"]
    coordinates = [start["lon_lat"]]
    for path_edge_index, graph_edge_index in enumerate(context["path_edges"]):
        edge = edges[graph_edge_index]
        if path_edge_index < start["path_edge_index"]:
            continue
        if path_edge_index > end["path_edge_index"]:
            break
        edge_coordinates = [
            [round(lon, 7), round(lat, 7)]
            for lon, lat in _feature_coordinates(features[edge["feature_index"]])
        ]
        if path_edge_index == start["path_edge_index"]:
            edge_coordinates = [
                point
                for point in edge_coordinates
                if point != coordinates[-1]
            ]
        if path_edge_index == end["path_edge_index"]:
            edge_coordinates.append(end["lon_lat"])
            coordinates.extend(edge_coordinates)
            break
        coordinates.extend(edge_coordinates)
    if coordinates[-1] != end["lon_lat"]:
        coordinates.append(end["lon_lat"])
    collapsed: list[list[float]] = []
    for point in coordinates:
        if not collapsed or collapsed[-1] != point:
            collapsed.append(point)
    return collapsed


def build_south_fork_a1_source_mile_divergence_audit(repo_root: Path) -> dict[str, Any]:
    """Build the published-mile divergence audit for the official access path."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    reanchor_diagnostic = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
    )
    river = _south_fork_catalog_record(catalog)
    context = _path_context(repo_root)
    official_source_station_m = context["official_source_station_m"]
    breakpoint_records = [
        {
            "breakpoint_id": breakpoint_id,
            "published_miles": miles,
            **_project_source_station(context, miles * MILES_TO_METERS),
        }
        for breakpoint_id, miles in _PUBLISHED_BREAKPOINTS
    ]
    full_run_breakpoint = next(
        item
        for item in breakpoint_records
        if item["breakpoint_id"] == "full_run_21_0_mile_source_convention"
    )

    return {
        "schema": "raftsim.south_fork.a1_source_mile_divergence_audit.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "status": "published_source_mile_points_are_upstream_of_official_access_path",
        "production_promoted": False,
        "inputs": {
            "named_flowline_extract": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "official_access_geometry_discrepancy_review": (
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH
            ),
            "official_access_reanchor_diagnostic": (
                FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH
            ),
            "official_access_reanchor_route_geojson": (
                FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH
            ),
        },
        "upstream_anchor": {
            "name": "Chili Bar put-in review seed",
            "lon_lat": list(context["chili_lon_lat"]),
            "nearest_graph_node_lon_lat": list(context["chili_node"]),
            "nearest_graph_node_distance_m": round(
                context["chili_snap_distance_m"],
                3,
            ),
        },
        "official_access_endpoint": {
            "name": context["official_seed"]["name"],
            "fid": context["official_seed"]["fid"],
            "gisid": context["official_seed"]["gisid"],
            "lon_lat": context["official_seed"]["lon_lat"],
            "nearest_graph_node_lon_lat": list(context["official_node"]),
            "nearest_graph_node_distance_m": round(
                context["official_snap_distance_m"],
                3,
            ),
            "source_station_m": round(official_source_station_m, 6),
            "source_station_miles": round(official_source_station_m / MILES_TO_METERS, 3),
        },
        "published_breakpoints_on_official_access_path": breakpoint_records,
        "divergence_summary": {
            "published_full_run_station_m": full_run_breakpoint["source_station_m"],
            "official_access_source_station_m": round(official_source_station_m, 6),
            "excess_source_path_after_21_miles_m": full_run_breakpoint[
                "remaining_source_path_to_official_access_m"
            ],
            "excess_source_path_after_21_miles_miles": full_run_breakpoint[
                "remaining_source_path_to_official_access_miles"
            ],
            "geodesic_21_mile_point_to_official_access_m": full_run_breakpoint[
                "geodesic_distance_to_official_access_m"
            ],
            "reanchor_diagnostic_status": reanchor_diagnostic["status"],
            "interpretation": (
                "The extracted NHD path reaches the published 21.0-mile convention "
                "well upstream of the official Salmon Falls Lower Water Raft Take-out "
                "access seed, leaving a 15.282 km source-path excess. This suggests "
                "the published miles are not directly compatible with the current "
                "NHD source-length station axis without guide/geospatial review."
            ),
        },
        "promotion_gate": {
            "can_promote_current_nhd_station_axis": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Review the 20.5/21.0-mile breakpoint overlay against aerial imagery and guide/local knowledge.",
                "Decide whether published miles are guide conventions separate from the simulation station axis.",
                "If the NHD axis is retained, record a distinct simulation station axis before restationing rapids.",
                "If the NHD axis is rejected, replace it with a reviewed centerline or hydrography source before regenerating windows.",
            ],
        },
    }


def build_south_fork_a1_source_mile_divergence_overlay_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    audit = build_south_fork_a1_source_mile_divergence_audit(repo_root)
    context = _path_context(repo_root.resolve())
    full_run = next(
        item
        for item in audit["published_breakpoints_on_official_access_path"]
        if item["breakpoint_id"] == "full_run_21_0_mile_source_convention"
    )
    excess_coordinates = _path_coordinates_between_stations(
        context,
        full_run["source_station_m"],
        audit["official_access_endpoint"]["source_station_m"],
    )
    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            "id": "chili_bar_put_in_review_seed",
            "geometry": {
                "type": "Point",
                "coordinates": audit["upstream_anchor"]["lon_lat"],
            },
            "properties": {
                "marker_kind": "upstream_anchor_seed",
                "production_promoted": False,
                "can_bind_editor_geometry": False,
                "can_bind_solver_windows": False,
            },
        },
        {
            "type": "Feature",
            "id": "official_salmon_falls_lower_water_raft_takeout_seed",
            "geometry": {
                "type": "Point",
                "coordinates": audit["official_access_endpoint"]["lon_lat"],
            },
            "properties": {
                "marker_kind": "official_access_endpoint_seed",
                "source_station_m": audit["official_access_endpoint"]["source_station_m"],
                "source_station_miles": audit["official_access_endpoint"][
                    "source_station_miles"
                ],
                "production_promoted": False,
                "can_bind_editor_geometry": False,
                "can_bind_solver_windows": False,
            },
        },
    ]
    for breakpoint in audit["published_breakpoints_on_official_access_path"]:
        features.append(
            {
                "type": "Feature",
                "id": breakpoint["breakpoint_id"],
                "geometry": {
                    "type": "Point",
                    "coordinates": breakpoint["lon_lat"],
                },
                "properties": {
                    "marker_kind": "published_source_mile_breakpoint",
                    "published_miles": breakpoint["published_miles"],
                    "source_station_m": breakpoint["source_station_m"],
                    "remaining_source_path_to_official_access_m": breakpoint[
                        "remaining_source_path_to_official_access_m"
                    ],
                    "geodesic_distance_to_official_access_m": breakpoint[
                        "geodesic_distance_to_official_access_m"
                    ],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            }
        )
    features.append(
        {
            "type": "Feature",
            "id": "source_path_excess_after_21_0_miles",
            "geometry": {
                "type": "LineString",
                "coordinates": excess_coordinates,
            },
            "properties": {
                "marker_kind": "review_only_source_path_excess",
                "start_breakpoint_id": full_run["breakpoint_id"],
                "source_path_excess_m": audit["divergence_summary"][
                    "excess_source_path_after_21_miles_m"
                ],
                "source_path_excess_miles": audit["divergence_summary"][
                    "excess_source_path_after_21_miles_miles"
                ],
                "point_count": len(excess_coordinates),
                "production_promoted": False,
                "can_bind_editor_geometry": False,
                "can_bind_solver_windows": False,
            },
        }
    )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_source_mile_divergence_overlay.geojson.v1",
        "generated_on": audit["generated_on"],
        "task_id": audit["task_id"],
        "river_id": audit["river_id"],
        "status": audit["status"],
        "source_json": FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
        "production_promoted": False,
        "features": features,
        "policy": {
            "allowed_use": [
                "source-mile/access divergence review",
                "editor/GIS overlay with binding disabled",
                "route-station-axis decision support",
            ],
            "forbidden_use": [
                "final centerline authority",
                "rapid restationing authority",
                "Unreal landscape import",
                "solver-window binding",
            ],
        },
    }


def write_south_fork_a1_source_mile_divergence_audit(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    audit = build_south_fork_a1_source_mile_divergence_audit(repo_root)
    overlay = build_south_fork_a1_source_mile_divergence_overlay_geojson(repo_root)
    outputs = [
        repo_root / FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
        repo_root / FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH,
    ]
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    outputs[1].write_text(
        json.dumps(overlay, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outputs
