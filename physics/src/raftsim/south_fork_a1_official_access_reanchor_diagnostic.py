"""Diagnose re-anchoring the South Fork A1 route to official access geometry."""

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
from .south_fork_a1_route_graph import (
    _build_graph,
    _geometry_lines,
    _haversine_m,
    _nearest_node,
    _node,
    _shortest_path,
)


FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_official_access_reanchor_diagnostic.json"
)
FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_official_access_reanchor_route.geojson"
)

_SNAP_WARNING_DISTANCE_M = 250.0
_PUBLISHED_LENGTH_WARNING_M = 1609.344


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


def _feature_coordinates(feature: dict[str, Any]) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for line in _geometry_lines(feature["geometry"]):
        coordinates.extend([[float(point[0]), float(point[1])] for point in line])
    return coordinates


def _feature_geometry_length_m(feature: dict[str, Any]) -> float:
    coordinates = [_node(point) for point in _feature_coordinates(feature)]
    return sum(
        _haversine_m(start, stop)
        for start, stop in zip(coordinates, coordinates[1:], strict=False)
    )


def _path_coordinates(features: list[dict[str, Any]], path_edges: list[int]) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for edge_index in path_edges:
        edge_coordinates = [
            [round(point[0], 7), round(point[1], 7)]
            for point in _feature_coordinates(features[edge_index])
        ]
        if coordinates and edge_coordinates and coordinates[-1] == edge_coordinates[0]:
            coordinates.extend(edge_coordinates[1:])
        else:
            coordinates.extend(edge_coordinates)
    return coordinates


def build_south_fork_a1_official_access_reanchor_diagnostic(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the route diagnostic from Chili Bar to the official access seed."""

    repo_root = repo_root.resolve()
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    official_review = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    )
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
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
    path_source_length_m = float(distances[official_node])
    path_geometry_length_m = sum(
        _feature_geometry_length_m(features[edges[edge_index]["feature_index"]])
        for edge_index in path_edges
    )
    published_run_length_m = float(river["run_length_m"])
    path_coordinates = _path_coordinates(
        features,
        [edges[edge_index]["feature_index"] for edge_index in path_edges],
    )

    return {
        "schema": "raftsim.south_fork.a1_official_access_reanchor_diagnostic.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "status": (
            "official_access_seed_snaps_to_nhd_pool_but_route_length_disagrees_"
            "with_published_run"
        ),
        "production_promoted": False,
        "inputs": {
            "named_flowline_extract": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "official_access_geometry_discrepancy_review": (
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH
            ),
        },
        "official_access_seed": {
            "name": official_seed["name"],
            "fid": official_seed["fid"],
            "gisid": official_seed["gisid"],
            "lon_lat": official_seed["lon_lat"],
            "review_role": official_seed["review_role"],
            "nearest_graph_node_lon_lat": list(official_node),
            "nearest_graph_node_distance_m": round(official_snap_distance_m, 3),
            "snaps_to_candidate_pool_within_warning_threshold": (
                official_snap_distance_m <= _SNAP_WARNING_DISTANCE_M
            ),
        },
        "upstream_anchor": {
            "name": "Chili Bar put-in review seed",
            "lon_lat": list(chili_lon_lat),
            "nearest_graph_node_lon_lat": list(chili_node),
            "nearest_graph_node_distance_m": round(chili_snap_distance_m, 3),
        },
        "route_path": {
            "path_edge_count": len(path_edges),
            "path_point_count": len(path_coordinates),
            "source_record_indices": [
                edges[edge_index]["source_record_index"] for edge_index in path_edges
            ],
            "source_record_numbers": [
                edges[edge_index]["source_record_number"] for edge_index in path_edges
            ],
            "path_source_length_m": round(path_source_length_m, 6),
            "path_geometry_length_m": round(path_geometry_length_m, 6),
            "path_geometry_length_miles": round(path_geometry_length_m / MILES_TO_METERS, 3),
            "published_run_length_m": published_run_length_m,
            "published_run_length_miles": round(published_run_length_m / MILES_TO_METERS, 3),
            "geometry_minus_published_run_length_m": round(
                path_geometry_length_m - published_run_length_m,
                6,
            ),
            "source_minus_published_run_length_m": round(
                path_source_length_m - published_run_length_m,
                6,
            ),
            "length_disagrees_with_published_run": (
                abs(path_geometry_length_m - published_run_length_m)
                > _PUBLISHED_LENGTH_WARNING_M
            ),
        },
        "interpretation": [
            "The official State Parks Salmon Falls Lower Water Raft Take-out seed is close enough to the extracted NHD pool to use as a re-anchoring seed.",
            "The shortest NHD path from Chili Bar to that seed is about 30.5 miles, not the catalog/source 21.0-mile full-run convention.",
            "That mismatch means A1 is no longer missing only an endpoint point; it needs source-mile convention review and route/window regeneration against the accepted downstream access basis.",
            "The current lower-gorge and anchor-window derivatives remain discrepancy/review evidence only.",
        ],
        "promotion_gate": {
            "can_use_official_seed_for_route_reanchor_planning": True,
            "can_promote_reanchored_route": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Review whether the playable full run should end at Salmon Falls Lower Water Raft Take-out, Skunk Hollow/Salmon Falls Bridge, or another guide-approved bank point.",
                "Resolve the 21.0-mile source convention against the 30.5-mile NHD path to the official lower-water take-out seed.",
                "Regenerate directed route clips and full-reach windows only after that source-mile/access decision is recorded.",
                "Then re-station all South Fork rapid markers and rerun corridor regression tests.",
            ],
        },
    }


def build_south_fork_a1_official_access_reanchor_route_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    diagnostic = build_south_fork_a1_official_access_reanchor_diagnostic(repo_root)
    geojson = _load_json(repo_root.resolve(), FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    features = geojson["features"]
    edges, _graph = _build_graph(features)
    route_edges = [
        next(
            edge
            for edge in edges
            if edge["source_record_index"] == source_record_index
        )
        for source_record_index in diagnostic["route_path"]["source_record_indices"]
    ]
    path_coordinates = _path_coordinates(
        features,
        [edge["feature_index"] for edge in route_edges],
    )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_official_access_reanchor_route.geojson.v1",
        "generated_on": diagnostic["generated_on"],
        "task_id": diagnostic["task_id"],
        "river_id": diagnostic["river_id"],
        "status": diagnostic["status"],
        "source_json": FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
        "production_promoted": False,
        "features": [
            {
                "type": "Feature",
                "id": "chili_bar_put_in_review_seed",
                "geometry": {
                    "type": "Point",
                    "coordinates": diagnostic["upstream_anchor"]["lon_lat"],
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
                    "coordinates": diagnostic["official_access_seed"]["lon_lat"],
                },
                "properties": {
                    "marker_kind": "official_access_reanchor_seed",
                    "fid": diagnostic["official_access_seed"]["fid"],
                    "gisid": diagnostic["official_access_seed"]["gisid"],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            },
            {
                "type": "Feature",
                "id": "chili_bar_to_official_salmon_falls_access_nhd_path",
                "geometry": {
                    "type": "LineString",
                    "coordinates": path_coordinates,
                },
                "properties": {
                    "marker_kind": "review_only_reanchor_route_path",
                    "path_edge_count": diagnostic["route_path"]["path_edge_count"],
                    "path_point_count": diagnostic["route_path"]["path_point_count"],
                    "path_geometry_length_m": diagnostic["route_path"][
                        "path_geometry_length_m"
                    ],
                    "geometry_minus_published_run_length_m": diagnostic["route_path"][
                        "geometry_minus_published_run_length_m"
                    ],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            },
        ],
        "policy": {
            "allowed_use": [
                "route reanchor diagnostics",
                "source-mile/access review",
                "editor/GIS overlay with binding disabled",
            ],
            "forbidden_use": [
                "final centerline authority",
                "rapid restationing authority",
                "Unreal landscape import",
                "solver-window binding",
            ],
        },
    }


def write_south_fork_a1_official_access_reanchor_diagnostic(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    diagnostic = build_south_fork_a1_official_access_reanchor_diagnostic(repo_root)
    route_geojson = build_south_fork_a1_official_access_reanchor_route_geojson(repo_root)
    outputs = [
        repo_root / FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
        repo_root / FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH,
    ]
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(
        json.dumps(diagnostic, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    outputs[1].write_text(
        json.dumps(route_geojson, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outputs
