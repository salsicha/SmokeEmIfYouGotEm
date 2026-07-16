"""Build South Fork A1 source-mile/access endpoint option evidence."""

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
)
from .south_fork_a1_route_graph import _build_graph, _nearest_node, _shortest_path


FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_access_option_matrix.json"
)
FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_access_option_points.geojson"
)

_SNAP_WARNING_DISTANCE_M = 250.0
_PUBLISHED_LENGTH_WARNING_M = 1609.344
_PUBLISHED_CONVENTIONS = (
    ("salmon_falls_20_5_mile_basis", 20.5),
    ("full_run_21_0_mile_basis", 21.0),
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


def _published_conventions() -> list[dict[str, Any]]:
    return [
        {
            "convention_id": convention_id,
            "published_miles": miles,
            "published_station_m": round(miles * MILES_TO_METERS, 6),
        }
        for convention_id, miles in _PUBLISHED_CONVENTIONS
    ]


def _access_option(
    *,
    record: dict[str, Any],
    graph: dict,
    edges: list[dict[str, Any]],
    chili_node: tuple[float, float],
) -> dict[str, Any]:
    lon_lat = tuple(float(value) for value in record["lon_lat"])
    nearest_node, snap_distance_m = _nearest_node(graph, lon_lat)
    distances, _previous, path_edges = _shortest_path(graph, chili_node, nearest_node)
    source_station_m = float(distances[nearest_node])
    convention_deltas = []
    for convention in _published_conventions():
        delta_m = source_station_m - float(convention["published_station_m"])
        convention_deltas.append(
            {
                **convention,
                "source_station_minus_published_m": round(delta_m, 6),
                "absolute_delta_m": round(abs(delta_m), 6),
                "within_one_mile": abs(delta_m) <= _PUBLISHED_LENGTH_WARNING_M,
            }
        )
    nearest_convention = min(convention_deltas, key=lambda item: item["absolute_delta_m"])
    snap_warning = snap_distance_m > _SNAP_WARNING_DISTANCE_M
    source_mile_conflict = nearest_convention["absolute_delta_m"] > _PUBLISHED_LENGTH_WARNING_M
    if snap_warning:
        review_status = "official_access_seed_needs_manual_snap_review"
    elif source_mile_conflict:
        review_status = "official_access_seed_snaps_but_source_mile_conflict"
    else:
        review_status = "official_access_seed_matches_source_mile_tolerance"

    return {
        "option_id": f"official_access_{record['fid']}",
        "fid": record["fid"],
        "name": record["name"],
        "gisid": record["gisid"],
        "review_role": record["review_role"],
        "share": record["share"],
        "use_type": record["use_type"],
        "trailhead": record["trailhead"],
        "lon_lat": record["lon_lat"],
        "nearest_graph_node_lon_lat": list(nearest_node),
        "nearest_graph_node_distance_m": round(snap_distance_m, 3),
        "snap_within_warning_threshold": not snap_warning,
        "path_edge_count": len(path_edges),
        "path_source_record_indices": [
            edges[edge_index]["source_record_index"] for edge_index in path_edges
        ],
        "source_station_m": round(source_station_m, 6),
        "source_station_miles": round(source_station_m / MILES_TO_METERS, 3),
        "convention_deltas": convention_deltas,
        "nearest_published_convention": nearest_convention["convention_id"],
        "nearest_published_convention_absolute_delta_m": nearest_convention[
            "absolute_delta_m"
        ],
        "review_status": review_status,
        "can_select_without_guide_geospatial_review": False,
        "can_promote_as_final_anchor": False,
    }


def build_south_fork_a1_source_mile_access_option_matrix(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the source-mile/access option matrix for the downstream endpoint."""

    repo_root = repo_root.resolve()
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    official_access_review = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    )
    reanchor_diagnostic = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
    )
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)

    edges, graph = _build_graph(geojson["features"])
    chili = _access_feature(access_points, "chili_bar_put_in_review_seed")
    chili_lon_lat = (
        float(chili["properties"]["station_lon"]),
        float(chili["properties"]["station_lat"]),
    )
    chili_node, chili_snap_distance_m = _nearest_node(graph, chili_lon_lat)
    options = [
        _access_option(
            record=record,
            graph=graph,
            edges=edges,
            chili_node=chili_node,
        )
        for record in official_access_review["official_access_records"]
    ]
    options_by_station = sorted(options, key=lambda item: item["source_station_m"])
    options_by_snap = sorted(options, key=lambda item: item["nearest_graph_node_distance_m"])
    primary_option = next(
        option
        for option in options
        if option["review_role"] == "primary_official_downstream_access_geometry_lead"
    )

    source_mile_conflict_count = sum(
        option["review_status"] == "official_access_seed_snaps_but_source_mile_conflict"
        for option in options
    )
    manual_snap_review_count = sum(
        option["review_status"] == "official_access_seed_needs_manual_snap_review"
        for option in options
    )

    return {
        "schema": "raftsim.south_fork.a1_source_mile_access_option_matrix.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "status": "source_mile_access_options_ready_for_review_no_route_promoted",
        "production_promoted": False,
        "inputs": {
            "named_flowline_extract": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "official_access_geometry_discrepancy_review": (
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH
            ),
            "official_access_reanchor_diagnostic": (
                FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH
            ),
        },
        "upstream_anchor": {
            "annotation_id": "chili_bar_put_in_review_seed",
            "lon_lat": list(chili_lon_lat),
            "nearest_graph_node_lon_lat": list(chili_node),
            "nearest_graph_node_distance_m": round(chili_snap_distance_m, 3),
        },
        "published_source_mile_conventions": _published_conventions(),
        "catalog_full_run_length": {
            "run_length_m": river["run_length_m"],
            "run_length_miles": round(float(river["run_length_m"]) / MILES_TO_METERS, 3),
        },
        "official_access_options": options,
        "option_rankings": {
            "by_source_station_m": [option["option_id"] for option in options_by_station],
            "by_snap_distance_m": [option["option_id"] for option in options_by_snap],
            "primary_access_option_id": primary_option["option_id"],
            "closest_to_21_mile_convention_option_id": min(
                options,
                key=lambda item: next(
                    delta["absolute_delta_m"]
                    for delta in item["convention_deltas"]
                    if delta["convention_id"] == "full_run_21_0_mile_basis"
                ),
            )["option_id"],
        },
        "summary": {
            "official_access_option_count": len(options),
            "options_within_snap_warning_threshold": sum(
                option["snap_within_warning_threshold"] for option in options
            ),
            "manual_snap_review_count": manual_snap_review_count,
            "source_mile_conflict_count": source_mile_conflict_count,
            "all_access_options_conflict_with_published_source_miles": (
                source_mile_conflict_count + manual_snap_review_count == len(options)
            ),
            "minimum_source_station_m": min(option["source_station_m"] for option in options),
            "maximum_source_station_m": max(option["source_station_m"] for option in options),
            "minimum_source_station_miles": min(
                option["source_station_miles"] for option in options
            ),
            "maximum_source_station_miles": max(
                option["source_station_miles"] for option in options
            ),
            "primary_option_source_station_miles": primary_option["source_station_miles"],
            "primary_option_source_minus_21_mile_convention_m": next(
                delta["source_station_minus_published_m"]
                for delta in primary_option["convention_deltas"]
                if delta["convention_id"] == "full_run_21_0_mile_basis"
            ),
            "reanchor_diagnostic_status": reanchor_diagnostic["status"],
        },
        "decision_required": {
            "question": (
                "Which physical downstream access endpoint and source-mile convention "
                "should define the playable South Fork full reach?"
            ),
            "acceptable_answers": [
                "Use the official Salmon Falls Lower Water Raft Take-out or a nearby guide-approved bank point, while recording that the route-station axis is not the published 21.0-mile convention.",
                "Use a guide-approved Salmon Falls/Skunk Hollow endpoint that better matches real runnable practice, then regenerate route clips and windows from that exact point.",
                "Treat the 20.5/21.0-mile source values as non-geometric guide conventions and define a separate simulation station axis after reviewer approval.",
                "Replace the NHD route basis with a different official hydrography or hand-reviewed centerline if NHD reservoir/source fragments are causing the 30-mile path.",
            ],
            "must_record_before_promotion": [
                "selected exact downstream endpoint lon/lat and geometry authority",
                "source-mile convention and whether it is distinct from simulation stationing",
                "route graph basis and accepted station axis",
                "guide/geospatial reviewer approval",
                "reservoir-stage/access interpretation",
                "publication-sensitivity decision",
            ],
        },
        "promotion_gate": {
            "can_select_endpoint_from_matrix_alone": False,
            "can_promote_current_nhd_route": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Hold source-mile/access review using this option matrix and the official-access reanchor route overlay.",
                "Record whether the published 20.5/21.0 miles are guide/source conventions distinct from the simulation route station axis.",
                "Regenerate the directed route, corridor windows, review derivatives, and rapid stationing only after the endpoint/station-axis decision is approved.",
                "Keep Meat Grinder and Troublemaker solver-window binding blocked until regenerated exact geometry passes corridor regression.",
            ],
        },
    }


def build_south_fork_a1_source_mile_access_option_points_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    matrix = build_south_fork_a1_source_mile_access_option_matrix(repo_root)
    features = []
    for option in matrix["official_access_options"]:
        features.append(
            {
                "type": "Feature",
                "id": option["option_id"],
                "geometry": {
                    "type": "Point",
                    "coordinates": option["lon_lat"],
                },
                "properties": {
                    "river_id": matrix["river_id"],
                    "name": option["name"],
                    "gisid": option["gisid"],
                    "review_role": option["review_role"],
                    "nearest_graph_node_distance_m": option[
                        "nearest_graph_node_distance_m"
                    ],
                    "source_station_m": option["source_station_m"],
                    "source_station_miles": option["source_station_miles"],
                    "nearest_published_convention": option[
                        "nearest_published_convention"
                    ],
                    "nearest_published_convention_absolute_delta_m": option[
                        "nearest_published_convention_absolute_delta_m"
                    ],
                    "review_status": option["review_status"],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_source_mile_access_option_points.geojson.v1",
        "generated_on": matrix["generated_on"],
        "task_id": matrix["task_id"],
        "river_id": matrix["river_id"],
        "status": matrix["status"],
        "source_json": FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH,
        "production_promoted": False,
        "features": features,
        "policy": {
            "allowed_use": [
                "source-mile/access review",
                "editor/GIS overlay with binding disabled",
                "route reanchor planning",
            ],
            "forbidden_use": [
                "final downstream endpoint authority",
                "corridor crop authority",
                "rapid restationing authority",
                "solver-window binding",
            ],
        },
    }


def write_south_fork_a1_source_mile_access_option_matrix(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    matrix = build_south_fork_a1_source_mile_access_option_matrix(repo_root)
    geojson = build_south_fork_a1_source_mile_access_option_points_geojson(repo_root)
    outputs = [
        repo_root / FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH,
        repo_root / FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH,
    ]
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    outputs[1].write_text(
        json.dumps(geojson, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outputs
