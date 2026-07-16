"""Diagnose the South Fork A1 full-reach NHD route graph."""

from __future__ import annotations

import heapq
import json
import math
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_full_reach_acquisition import ACCESS_POINTS_RELATIVE_PATH
from .south_fork_a1_nhd_extraction import (
    FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
    FULL_REACH_NHD_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_stationing import ALIGNMENT_REVIEW_RELATIVE_PATH


FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_nhd_route_graph_diagnostic.json"
)
EARTH_RADIUS_M = 6_371_008.8


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _node(point: list[float]) -> tuple[float, float]:
    return (round(float(point[0]), 7), round(float(point[1]), 7))


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


def _geometry_lines(geometry: dict[str, Any]) -> list[list[list[float]]]:
    if geometry["type"] == "LineString":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiLineString":
        return geometry["coordinates"]
    raise ValueError(f"Unsupported geometry type: {geometry['type']}")


def _feature_edge(feature_index: int, feature: dict[str, Any]) -> dict[str, Any]:
    lines = _geometry_lines(feature["geometry"])
    first = _node(lines[0][0])
    last = _node(lines[-1][-1])
    source_length_m = float(feature["properties"].get("lengthkm") or 0.0) * 1000.0
    if source_length_m <= 0.0:
        source_length_m = sum(
            _haversine_m(_node(start), _node(stop))
            for line in lines
            for start, stop in zip(line, line[1:], strict=False)
        )
    return {
        "feature_index": feature_index,
        "source_record_index": feature["properties"]["source_record_index"],
        "source_record_number": feature["properties"]["source_record_number"],
        "permanent_identifier": feature["properties"]["permanent_identifier"],
        "start": first,
        "end": last,
        "length_m": source_length_m,
    }


def _build_graph(features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict]:
    edges = [_feature_edge(index, feature) for index, feature in enumerate(features)]
    graph: dict[tuple[float, float], list[tuple[tuple[float, float], float, int]]] = {}
    for edge_index, edge in enumerate(edges):
        start = edge["start"]
        end = edge["end"]
        length_m = edge["length_m"]
        graph.setdefault(start, []).append((end, length_m, edge_index))
        graph.setdefault(end, []).append((start, length_m, edge_index))
    return edges, graph


def _component_sizes(graph: dict) -> list[int]:
    seen: set[tuple[float, float]] = set()
    sizes: list[int] = []
    for node in graph:
        if node in seen:
            continue
        stack = [node]
        seen.add(node)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for neighbor, _length_m, _edge_index in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _nearest_node(
    graph: dict,
    lon_lat: tuple[float, float],
) -> tuple[tuple[float, float], float]:
    distance_m, node = min(
        (_haversine_m(lon_lat, node), node)
        for node in graph
    )
    return node, distance_m


def _shortest_path(
    graph: dict,
    start: tuple[float, float],
    target: tuple[float, float] | None = None,
) -> tuple[dict[tuple[float, float], float], dict[tuple[float, float], tuple], list[int]]:
    distances = {start: 0.0}
    previous: dict[tuple[float, float], tuple[tuple[float, float], int]] = {}
    queue = [(0.0, start)]
    while queue:
        distance, current = heapq.heappop(queue)
        if distance != distances[current]:
            continue
        if target is not None and current == target:
            break
        for neighbor, length_m, edge_index in graph[current]:
            candidate = distance + length_m
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = (current, edge_index)
                heapq.heappush(queue, (candidate, neighbor))
    path_edges: list[int] = []
    if target is not None and target in distances:
        current = target
        while current != start:
            prior, edge_index = previous[current]
            path_edges.append(edge_index)
            current = prior
        path_edges.reverse()
    return distances, previous, path_edges


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


def build_south_fork_a1_route_graph_diagnostic(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    manifest = _load_json(repo_root, FULL_REACH_NHD_MANIFEST_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    alignment = _load_json(repo_root, ALIGNMENT_REVIEW_RELATIVE_PATH)
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)

    edges, graph = _build_graph(geojson["features"])
    component_sizes = _component_sizes(graph)
    chili_bar = _access_feature(access_points, "chili_bar_put_in_review_seed")
    coloma_seed = _access_feature(access_points, "coloma_takeout_review_seed")
    chili_lon_lat = (
        float(chili_bar["properties"]["station_lon"]),
        float(chili_bar["properties"]["station_lat"]),
    )
    coloma_seed_lon_lat = (
        float(coloma_seed["properties"]["station_lon"]),
        float(coloma_seed["properties"]["station_lat"]),
    )
    chili_node, chili_distance_m = _nearest_node(graph, chili_lon_lat)
    coloma_node, coloma_distance_m = _nearest_node(graph, coloma_seed_lon_lat)
    distances_to_coloma, _previous, coloma_path_edges = _shortest_path(
        graph,
        chili_node,
        coloma_node,
    )
    all_distances, _all_previous, _path = _shortest_path(graph, chili_node)
    farthest_node, farthest_distance_m = max(
        all_distances.items(),
        key=lambda item: item[1],
    )
    published_coloma_station_m = float(
        alignment["published_reference"]["coloma_bridge_station_m"]
    )
    coloma_graph_station_m = distances_to_coloma[coloma_node]
    published_run_length_m = float(river["run_length_m"])

    return {
        "schema": "raftsim.south_fork.a1_full_reach_nhd_route_graph_diagnostic.v1",
        "generated_on": "2026-07-16",
        "status": (
            "blocked_shortest_path_does_not_validate_coloma_checkpoint_"
            "and_folsom_anchor_missing"
        ),
        "production_promoted": False,
        "inputs": {
            "named_flowline_extract": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
            "named_flowline_extract_manifest": FULL_REACH_NHD_MANIFEST_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
            "alignment_review": ALIGNMENT_REVIEW_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
        },
        "source_pool": {
            "feature_count": len(edges),
            "node_count": len(graph),
            "component_count": len(component_sizes),
            "component_node_counts": component_sizes,
            "selected_length_km_source_sum": manifest["selection"][
                "selected_length_km_source_sum"
            ],
            "candidate_pool_is_single_connected_component": len(component_sizes) == 1,
            "candidate_pool_is_ordered_route": False,
        },
        "anchor_diagnostics": {
            "chili_bar_put_in": {
                "seed_lon_lat": list(chili_lon_lat),
                "nearest_graph_node_lon_lat": list(chili_node),
                "nearest_graph_node_distance_m": round(chili_distance_m, 6),
                "seed_status": chili_bar["properties"]["stationing_status"],
            },
            "current_coloma_access_seed": {
                "seed_lon_lat": list(coloma_seed_lon_lat),
                "nearest_graph_node_lon_lat": list(coloma_node),
                "nearest_graph_node_distance_m": round(coloma_distance_m, 6),
                "graph_station_from_chili_bar_m": round(coloma_graph_station_m, 6),
                "published_coloma_checkpoint_m": published_coloma_station_m,
                "graph_minus_published_checkpoint_m": round(
                    coloma_graph_station_m - published_coloma_station_m,
                    6,
                ),
                "path_edge_count": len(coloma_path_edges),
                "path_source_record_indices": [
                    edges[edge_index]["source_record_index"]
                    for edge_index in coloma_path_edges
                ],
                "shortest_path_does_not_validate_published_checkpoint": True,
                "anchor_identity_requires_review": True,
                "interpretation": (
                    "The current NHD shortest path to this review seed is 3.762 km "
                    "short of the published Chili Bar-to-Coloma checkpoint. This "
                    "blocks route promotion, but it does not by itself prove the "
                    "seed coordinate is wrong; directed graph order, source "
                    "fragments, source-mile basis, and exact anchor identity still "
                    "need review."
                ),
            },
            "folsom_reservoir_takeout": {
                "seed_lon_lat": None,
                "seed_status": "missing_exact_anchor",
                "published_run_length_m": published_run_length_m,
                "published_run_length_miles": round(
                    published_run_length_m / MILES_TO_METERS,
                    3,
                ),
            },
        },
        "graph_extent_diagnostic": {
            "farthest_reachable_node_from_chili_bar_lon_lat": list(farthest_node),
            "farthest_reachable_station_m": round(farthest_distance_m, 6),
            "farthest_minus_published_run_length_m": round(
                farthest_distance_m - published_run_length_m,
                6,
            ),
            "interpretation": (
                "The connected named-flowline pool is longer than the published "
                "run because it includes branches, reservoir/source fragments, and "
                "unclipped alternatives. It must be solved as a directed route graph."
            ),
        },
        "promotion_gate": {
            "can_enable_south_fork_editor_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Resolve whether the Coloma seed, graph traversal, or source-mile reference is causing the checkpoint mismatch.",
                "Attach an exact reviewed Salmon Falls/Folsom Reservoir take-out anchor.",
                "Solve a directed path through the named-flowline pool and clip it to reviewed anchors.",
                "Regenerate rapid stationing only after the Coloma checkpoint and full-run length checks pass.",
            ],
        },
    }


def write_south_fork_a1_route_graph_diagnostic(repo_root: Path) -> Path:
    payload = build_south_fork_a1_route_graph_diagnostic(repo_root)
    path = repo_root / FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
