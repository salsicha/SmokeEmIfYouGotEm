"""Generate directed NHD station candidates for South Fork A1 review."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_full_reach_acquisition import ACCESS_POINTS_RELATIVE_PATH
from .south_fork_a1_nhd_extraction import (
    FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
    FULL_REACH_NHD_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_route_graph import FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH


FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_directed_station_candidates.json"
)
FULL_REACH_DIRECTED_STATION_CANDIDATES_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_directed_station_candidates.geojson"
)
EARTH_RADIUS_M = 6_371_008.8


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _access_feature(access_points: dict[str, Any], annotation_id: str) -> dict[str, Any]:
    for feature in access_points["features"]:
        if feature["properties"]["annotation_id"] == annotation_id:
            return feature
    raise ValueError(f"Missing access feature {annotation_id}")


def _node(point: list[float] | tuple[float, float]) -> tuple[float, float]:
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


def _feature_coordinates(feature: dict[str, Any]) -> list[tuple[float, float]]:
    coordinates: list[tuple[float, float]] = []
    for line in _geometry_lines(feature["geometry"]):
        coordinates.extend((float(point[0]), float(point[1])) for point in line)
    return coordinates


def _feature_length_m(feature: dict[str, Any]) -> float:
    source_length_m = float(feature["properties"].get("lengthkm") or 0.0) * 1000.0
    if source_length_m > 0.0:
        return source_length_m
    coordinates = _feature_coordinates(feature)
    return sum(
        _haversine_m(start, stop)
        for start, stop in zip(coordinates, coordinates[1:], strict=False)
    )


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


def _directed_edge(feature_index: int, feature: dict[str, Any]) -> dict[str, Any]:
    coordinates = _feature_coordinates(feature)
    return {
        "feature_index": feature_index,
        "source_record_index": feature["properties"]["source_record_index"],
        "source_record_number": feature["properties"]["source_record_number"],
        "permanent_identifier": feature["properties"]["permanent_identifier"],
        "reachcode": feature["properties"]["reachcode"],
        "fcode": feature["properties"]["fcode"],
        "flowdir": feature["properties"]["flowdir"],
        "start": _node(coordinates[0]),
        "end": _node(coordinates[-1]),
        "length_m": _feature_length_m(feature),
    }


def _build_directed_graph(
    features: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict, Counter, Counter]:
    edges = [_directed_edge(index, feature) for index, feature in enumerate(features)]
    outgoing: dict[tuple[float, float], list[int]] = defaultdict(list)
    in_degree: Counter[tuple[float, float]] = Counter()
    out_degree: Counter[tuple[float, float]] = Counter()
    for edge_index, edge in enumerate(edges):
        start = edge["start"]
        end = edge["end"]
        outgoing[start].append(edge_index)
        out_degree[start] += 1
        in_degree[end] += 1
        in_degree[start] += 0
        out_degree[end] += 0
    return edges, outgoing, in_degree, out_degree


def _follow_unique_chain(
    edges: list[dict[str, Any]],
    outgoing: dict[tuple[float, float], list[int]],
    start: tuple[float, float],
) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    current = start
    station_m = 0.0
    visited: set[int] = set()
    while outgoing.get(current):
        outgoing_edges = outgoing[current]
        if len(outgoing_edges) != 1:
            raise ValueError(f"Directed chain branches at {current}: {outgoing_edges}")
        edge_index = outgoing_edges[0]
        if edge_index in visited:
            raise ValueError(f"Directed chain loops at edge {edge_index}")
        visited.add(edge_index)
        edge = dict(edges[edge_index])
        edge["station_start_m"] = round(station_m, 6)
        station_m += float(edge["length_m"])
        edge["station_end_m"] = round(station_m, 6)
        chain.append(edge)
        current = edge["end"]
    return chain


def _project_station(
    features: list[dict[str, Any]],
    chain: list[dict[str, Any]],
    station_m: float,
) -> dict[str, Any]:
    if station_m < 0.0 or station_m > chain[-1]["station_end_m"]:
        raise ValueError(f"Station {station_m} m is outside the directed chain")
    for edge in chain:
        if station_m <= edge["station_end_m"]:
            span_m = max(edge["station_end_m"] - edge["station_start_m"], 1e-9)
            alpha = (station_m - edge["station_start_m"]) / span_m
            lon, lat = _interpolate_feature_lon_lat(
                features[edge["feature_index"]],
                alpha,
            )
            return {
                "station_m": round(station_m, 6),
                "lon_lat": [lon, lat],
                "feature_index": edge["feature_index"],
                "source_record_index": edge["source_record_index"],
                "source_record_number": edge["source_record_number"],
                "permanent_identifier": edge["permanent_identifier"],
                "reachcode": edge["reachcode"],
                "station_source": "nhd_source_lengthkm_along_directed_chain",
                "coordinate_interpolation": "polyline_fraction_within_source_record",
                "geometry_status": (
                    "review_candidate_from_directed_nhd_chain_not_authoritative"
                ),
            }
    raise ValueError(f"Station {station_m} m did not project onto the chain")


def _station_candidate(
    features: list[dict[str, Any]],
    chain: list[dict[str, Any]],
    station_id: str,
    source_id: str,
    published_river_mile: float,
) -> dict[str, Any]:
    station_m = published_river_mile * MILES_TO_METERS
    projected = _project_station(features, chain, station_m)
    return {
        "station_id": station_id,
        "source_id": source_id,
        "published_river_mile": published_river_mile,
        **projected,
    }


def _geojson_feature(
    feature_id: str,
    lon_lat: list[float],
    properties: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "Point",
            "coordinates": lon_lat,
        },
        "properties": properties,
    }


def _rapid_station_candidates(
    river: dict[str, Any],
    features: list[dict[str, Any]],
    chain: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for rapid in river["rapids"]:
        published_mile = float(rapid["river_mile"])
        projected = _project_station(features, chain, published_mile * MILES_TO_METERS)
        candidates.append(
            {
                "name": rapid["name"],
                "order": rapid["order"],
                "published_river_mile": published_mile,
                "class": rapid["class"],
                "review_priority": rapid["review_priority"],
                "feature_tags": rapid["feature_tags"],
                "can_bind_editor_geometry": False,
                "can_bind_solver_window": False,
                **projected,
            }
        )
    return candidates


def build_south_fork_a1_directed_station_candidates(
    repo_root: Path,
) -> dict[str, Any]:
    """Build review-only station candidates along the directed NHD chain."""

    repo_root = repo_root.resolve()
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    manifest = _load_json(repo_root, FULL_REACH_NHD_MANIFEST_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
    features = geojson["features"]
    chili_seed = _access_feature(access_points, "chili_bar_put_in_review_seed")
    chili_lon_lat = (
        float(chili_seed["properties"]["station_lon"]),
        float(chili_seed["properties"]["station_lat"]),
    )

    edges, outgoing, in_degree, out_degree = _build_directed_graph(features)
    chili_node = _node(chili_lon_lat)
    chain = _follow_unique_chain(edges, outgoing, chili_node)
    route_axis_length_m = chain[-1]["station_end_m"]
    source_feature_indices_on_chain = {
        edge["feature_index"]
        for edge in chain
    }
    coloma = _station_candidate(
        features,
        chain,
        "coloma_bridge_checkpoint_published_5_6_miles",
        "south_fork_american_rivers_mile_guide",
        5.6,
    )
    salmon_falls = _station_candidate(
        features,
        chain,
        "salmon_falls_bridge_takeout_published_20_5_miles",
        "south_fork_american_rivers_mile_guide",
        20.5,
    )
    folsom_window = _station_candidate(
        features,
        chain,
        "full_run_downstream_window_published_21_0_miles",
        "south_fork_americanwhitewater_map",
        21.0,
    )
    chili_bar = _station_candidate(
        features,
        chain,
        "chili_bar_put_in_published_0_0_miles",
        "south_fork_american_rivers_mile_guide",
        0.0,
    )
    coloma_current_seed_station_m = 5250.41934
    coloma_seed_lon_lat = (
        -120.7632701,
        38.7784667,
    )

    return {
        "schema": "raftsim.south_fork.a1_directed_station_candidates.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "review_only_directed_nhd_station_candidates_not_promoted",
        "production_promoted": False,
        "inputs": {
            "named_flowline_extract": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
            "named_flowline_extract_manifest": FULL_REACH_NHD_MANIFEST_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "route_graph_diagnostic": FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH,
        },
        "direction_evidence": {
            "flowdir_values": sorted(
                {edge["flowdir"] for edge in edges}
            ),
            "source_record_count": len(edges),
            "directed_edge_count_from_chili_bar": len(chain),
            "upstream_of_chili_bar_edge_count": len(edges) - len(chain),
            "branch_node_count": sum(1 for value in out_degree.values() if value > 1),
            "merge_node_count": sum(1 for value in in_degree.values() if value > 1),
            "route_axis_length_m": route_axis_length_m,
            "source_pool_length_m": round(
                float(manifest["selection"]["selected_length_km_source_sum"])
                * 1000.0,
                6,
            ),
            "catalog_full_run_length_m": river["run_length_m"],
            "route_axis_minus_catalog_full_run_m": round(
                route_axis_length_m - float(river["run_length_m"]),
                6,
            ),
            "route_axis_exceeds_catalog_full_run": (
                route_axis_length_m > float(river["run_length_m"])
            ),
            "terminal_node_lon_lat": list(chain[-1]["end"]),
            "interpretation": (
                "The selected NHD records form a unique directed chain from the "
                "Chili Bar seed, but that chain is far longer than the published "
                "21-mile game reach. Review-only station candidates can be used to "
                "choose anchors, not to promote final geometry."
            ),
        },
        "source_record_coverage": {
            "source_record_indices_on_chili_bar_downstream_chain": [
                edge["source_record_index"]
                for edge in chain
            ],
            "source_record_indices_upstream_or_not_on_chain": [
                edge["source_record_index"]
                for edge in edges
                if edge["feature_index"] not in source_feature_indices_on_chain
            ],
        },
        "source_anchor_station_candidates": {
            "chili_bar_put_in": {
                **chili_bar,
                "current_seed_station_m": 0.0,
                "current_seed_minus_candidate_station_m": 0.0,
                "current_seed_to_candidate_geodesic_distance_m": 0.0,
                "validation_status": (
                    "candidate_matches_current_review_seed_but_exact_access_still_unreviewed"
                ),
            },
            "coloma_bridge_checkpoint": {
                **coloma,
                "current_seed_station_m": coloma_current_seed_station_m,
                "current_seed_minus_candidate_station_m": round(
                    coloma_current_seed_station_m - coloma["station_m"],
                    6,
                ),
                "current_seed_to_candidate_geodesic_distance_m": round(
                    _haversine_m(coloma_seed_lon_lat, tuple(coloma["lon_lat"])),
                    3,
                ),
                "validation_status": (
                    "candidate_review_point_generated_current_seed_still_unresolved"
                ),
            },
            "downstream_source_window": {
                "minimum_source_mile_candidate": salmon_falls,
                "maximum_source_mile_candidate": folsom_window,
                "window_length_m": round(
                    folsom_window["station_m"] - salmon_falls["station_m"],
                    6,
                ),
                "validation_status": (
                    "candidate_review_window_generated_exact_takeout_still_missing"
                ),
            },
        },
        "named_rapid_station_candidates": _rapid_station_candidates(
            river,
            features,
            chain,
        ),
        "promotion_gate": {
            "can_enable_south_fork_editor_geometry": False,
            "can_bind_meat_grinder_troublemaker_solver_windows": False,
            "can_restation_catalog_from_candidates": False,
            "why_blocked": [
                "candidate points are projected from NHD source lengths, not guide-approved rapid GPS",
                "downstream take-out source-mile basis is unresolved",
                "Coloma checkpoint seed identity is still unresolved",
                "corridor terrain/imagery windows are not regenerated from reviewed anchors",
            ],
        },
    }


def build_south_fork_a1_directed_station_candidates_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    """Build a visual review GeoJSON layer from the directed candidates."""

    payload = build_south_fork_a1_directed_station_candidates(repo_root)
    anchors = payload["source_anchor_station_candidates"]
    downstream = anchors["downstream_source_window"]
    anchor_candidates = [
        (
            "anchor_chili_bar_put_in",
            anchors["chili_bar_put_in"],
            "anchor_candidate",
            "Chili Bar put-in",
        ),
        (
            "anchor_coloma_bridge_checkpoint",
            anchors["coloma_bridge_checkpoint"],
            "anchor_checkpoint_candidate",
            "Coloma Bridge checkpoint",
        ),
        (
            "anchor_salmon_falls_20_5",
            downstream["minimum_source_mile_candidate"],
            "downstream_window_candidate",
            "Salmon Falls/Folsom source window 20.5 mi",
        ),
        (
            "anchor_full_run_21_0",
            downstream["maximum_source_mile_candidate"],
            "downstream_window_candidate",
            "Salmon Falls/Folsom source window 21.0 mi",
        ),
    ]
    features: list[dict[str, Any]] = []
    for feature_id, anchor, marker_kind, label in anchor_candidates:
        features.append(
            _geojson_feature(
                feature_id,
                anchor["lon_lat"],
                {
                    "river_id": payload["river_id"],
                    "marker_kind": marker_kind,
                    "label": label,
                    "station_id": anchor["station_id"],
                    "station_m": anchor["station_m"],
                    "published_river_mile": anchor["published_river_mile"],
                    "source_id": anchor["source_id"],
                    "geometry_status": anchor["geometry_status"],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_window": False,
                },
            )
        )
    for rapid in payload["named_rapid_station_candidates"]:
        rapid_id = rapid["name"].lower().replace(" ", "_").replace("'", "")
        features.append(
            _geojson_feature(
                f"rapid_{rapid['order']:02d}_{rapid_id}",
                rapid["lon_lat"],
                {
                    "river_id": payload["river_id"],
                    "marker_kind": "named_rapid_candidate",
                    "label": rapid["name"],
                    "order": rapid["order"],
                    "station_m": rapid["station_m"],
                    "published_river_mile": rapid["published_river_mile"],
                    "class": rapid["class"],
                    "review_priority": rapid["review_priority"],
                    "feature_tags": rapid["feature_tags"],
                    "geometry_status": rapid["geometry_status"],
                    "production_promoted": False,
                    "can_bind_editor_geometry": rapid["can_bind_editor_geometry"],
                    "can_bind_solver_window": rapid["can_bind_solver_window"],
                },
            )
        )

    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_directed_station_candidates.geojson.v1",
        "generated_on": payload["generated_on"],
        "status": "review_only_visual_layer_not_production_geometry",
        "production_promoted": False,
        "source_json": FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
        "river_id": payload["river_id"],
        "feature_count": len(features),
        "policy": {
            "allowed_use": [
                "visual review",
                "anchor and guide review queue",
                "editor overlay with binding disabled",
            ],
            "forbidden_use": [
                "shipping gameplay geometry",
                "solver-window binding",
                "public access or rescue geometry",
            ],
        },
        "features": features,
    }


def write_south_fork_a1_directed_station_candidates(repo_root: Path) -> Path:
    payload = build_south_fork_a1_directed_station_candidates(repo_root)
    path = repo_root / FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_south_fork_a1_directed_station_candidates_geojson(repo_root: Path) -> Path:
    payload = build_south_fork_a1_directed_station_candidates_geojson(repo_root)
    path = repo_root / FULL_REACH_DIRECTED_STATION_CANDIDATES_GEOJSON_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
