"""Build the adopted South Fork A1 full-reach route stationing.

Executes the decided §6 gate disposition from ``docs/release-1.0-plan.md``:
the official California State Parks "Salmon Falls Lower Water Raft Take-out"
access geometry is ground truth for the downstream anchor, the mainstem route
is the directed NHD flowline chain re-validated against official access
points, and published mile figures become alias metadata with a recorded
divergence note. This module produces stationing data only; it does not
author exact per-rapid geometry (P3/P4 work) and it does not promote
photoreal or gameplay claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
    _access_feature,
    _build_directed_graph,
    _clip_chain_coordinates,
    _follow_unique_chain,
    _haversine_m,
    _node,
    _project_station,
    _south_fork_catalog_record,
)
from .south_fork_a1_full_reach_acquisition import ACCESS_POINTS_RELATIVE_PATH
from .south_fork_a1_nhd_extraction import FULL_REACH_NHD_GEOJSON_RELATIVE_PATH
from .south_fork_a1_official_access_geometry_review import (
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
)
from .south_fork_a1_official_access_reanchor_diagnostic import (
    FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
)
from .south_fork_a1_source_mile_divergence_audit import (
    FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
)
from .south_fork_a1_stationing import (
    A1_ADOPTED_STATION_AXIS_ID,
    A1_ADOPTION_DECISION_AUTHORITY,
    A1_ADOPTION_DECISION_SOURCE,
    FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
    P7_REVIEW_BATCH_ID,
)

_PUBLISHED_MILE_ALIASES = (
    (
        "salmon_falls_bridge_published_20_5_miles",
        "south_fork_american_rivers_mile_guide",
        20.5,
    ),
    (
        "full_run_published_21_0_miles",
        "south_fork_americanwhitewater_map",
        21.0,
    ),
)

_PENDING_HUMAN_REVIEW_ITEMS = (
    {
        "review_id": "salmon_falls_takeout_bank_landing_confirmation",
        "description": (
            "Confirm the exact riverbank landing at the Salmon Falls Lower Water "
            "Raft Take-out relative to the State Parks parking-centroid anchor "
            "(117.7 m snap) and its reservoir-stage usability."
        ),
        "formerly": "local guide review blocker",
    },
    {
        "review_id": "rapid_station_realism_guide_confirmation",
        "description": (
            "Guide/oarsman confirmation that the 20 named-rapid stations "
            "projected from published guide miles onto the adopted NHD axis "
            "land at the real rapids."
        ),
        "formerly": "local guide review blocker",
    },
    {
        "review_id": "published_mile_alias_divergence_note_review",
        "description": (
            "Owner review of the recorded divergence between published guide "
            "miles (21.0-mile full run) and the adopted NHD source-length axis "
            "(30.495 miles to the official take-out)."
        ),
        "formerly": "source-mile convention review blocker",
    },
    {
        "review_id": "flow_band_guide_outfitter_validation",
        "description": (
            "Guide/outfitter validation of the CBR/A25 flow bands, seasonal "
            "windows, and station-to-rapid flow routing."
        ),
        "formerly": "local guide review blocker",
    },
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _chain_context(repo_root: Path) -> dict[str, Any]:
    geojson = _load_json(repo_root, FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    official_review = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    )
    features = geojson["features"]
    chili = _access_feature(access_points, "chili_bar_put_in_review_seed")
    chili_lon_lat = (
        float(chili["properties"]["station_lon"]),
        float(chili["properties"]["station_lat"]),
    )
    edges, outgoing, _in_degree, _out_degree = _build_directed_graph(features)
    chain = _follow_unique_chain(edges, outgoing, _node(chili_lon_lat))
    official_seed = official_review["primary_official_access_geometry_lead"]
    official_lon_lat = tuple(float(value) for value in official_seed["lon_lat"])
    anchor_node, anchor_snap_distance_m, anchor_station_m = _nearest_chain_node(
        chain,
        official_lon_lat,
    )
    return {
        "features": features,
        "chain": chain,
        "chili_lon_lat": chili_lon_lat,
        "official_review": official_review,
        "official_seed": official_seed,
        "official_lon_lat": official_lon_lat,
        "anchor_node": anchor_node,
        "anchor_snap_distance_m": anchor_snap_distance_m,
        "anchor_station_m": anchor_station_m,
    }


def _nearest_chain_node(
    chain: list[dict[str, Any]],
    lon_lat: tuple[float, float],
) -> tuple[tuple[float, float], float, float]:
    best: tuple[float, tuple[float, float], float] | None = None
    for edge in chain:
        for node, station_m in (
            (edge["start"], edge["station_start_m"]),
            (edge["end"], edge["station_end_m"]),
        ):
            distance_m = _haversine_m(lon_lat, node)
            if best is None or distance_m < best[0]:
                best = (distance_m, node, station_m)
    if best is None:
        raise ValueError("Directed chain has no nodes to snap against")
    return best[1], best[0], best[2]


def _published_mile_alias_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for alias_id, source_id, published_miles in _PUBLISHED_MILE_ALIASES:
        projected = _project_station(
            context["features"],
            context["chain"],
            published_miles * MILES_TO_METERS,
        )
        records.append(
            {
                "alias_id": alias_id,
                "source_id": source_id,
                "published_miles": published_miles,
                "station_m_on_adopted_axis": projected["station_m"],
                "lon_lat_on_adopted_axis": projected["lon_lat"],
                "geodesic_distance_to_adopted_anchor_m": round(
                    _haversine_m(
                        tuple(projected["lon_lat"]),
                        context["official_lon_lat"],
                    ),
                    3,
                ),
                "remaining_axis_distance_to_adopted_anchor_m": round(
                    context["anchor_station_m"] - projected["station_m"],
                    6,
                ),
                "role": "alias_metadata_with_recorded_divergence",
                "rejected_as_anchor": True,
            }
        )
    return records


def _rejected_anchor_candidate_records(
    official_review: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in official_review["candidate_comparisons"]:
        records.append(
            {
                "station_id": candidate["station_id"],
                "option_id": candidate["option_id"],
                "published_river_mile": candidate["published_river_mile"],
                "candidate_lon_lat": candidate["candidate_lon_lat"],
                "distance_to_official_raft_takeout_m": candidate[
                    "primary_raft_takeout_distance_m"
                ],
                "disposition": "rejected_as_anchor_retained_as_alias_metadata",
                "reason": (
                    "NHD-derived published-mile point lies more than 9 km from "
                    "the official Salmon Falls access geometry; official access "
                    "geometry is ground truth per the release-1.0 plan."
                ),
            }
        )
    return records


def _rapid_station_records(
    river: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rapid in river["rapids"]:
        published_mile = float(rapid["river_mile"])
        projected = _project_station(
            context["features"],
            context["chain"],
            published_mile * MILES_TO_METERS,
        )
        records.append(
            {
                "name": rapid["name"],
                "order": rapid["order"],
                "class": rapid["class"],
                "review_priority": rapid["review_priority"],
                "feature_tags": rapid["feature_tags"],
                "published_river_mile_alias": published_mile,
                "station_m": projected["station_m"],
                "lon_lat": projected["lon_lat"],
                "source_record_index": projected["source_record_index"],
                "source_record_number": projected["source_record_number"],
                "permanent_identifier": projected["permanent_identifier"],
                "reachcode": projected["reachcode"],
                "station_source": projected["station_source"],
                "coordinate_interpolation": projected["coordinate_interpolation"],
                "stationing_basis": (
                    "published_mile_alias_projected_along_adopted_axis"
                ),
                "exact_geometry_status": (
                    "stationing_only_exact_geometry_authoring_pending_p3_p4"
                ),
                "pending_human_review": True,
                "review_batch": P7_REVIEW_BATCH_ID,
            }
        )
    return records


def build_south_fork_a1_adopted_route_stationing(repo_root: Path) -> dict[str, Any]:
    """Build the adopted full-reach route stationing artifact."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
    divergence_audit = _load_json(
        repo_root,
        FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
    )
    context = _chain_context(repo_root)
    chain = context["chain"]
    anchor_station_m = float(context["anchor_station_m"])
    official_seed = context["official_seed"]
    aliases = _published_mile_alias_records(context)
    rapid_stations = _rapid_station_records(river, context)
    full_run_alias = next(
        alias for alias in aliases if alias["published_miles"] == 21.0
    )
    audit_anchor_station_m = float(
        divergence_audit["official_access_endpoint"]["source_station_m"]
    )
    route_edge_count = sum(
        1 for edge in chain if edge["station_start_m"] < anchor_station_m
    )
    stations = [rapid["station_m"] for rapid in rapid_stations]
    published_run_length_m = float(river["run_length_m"])

    return {
        "schema": "raftsim.south_fork.a1_adopted_route_stationing.v1",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "adopted_official_access_anchor_route_stationing_active",
        "production_promoted": False,
        "decision": {
            "decision_id": "south_fork_a1_source_mile_access_authority",
            "decision_source": A1_ADOPTION_DECISION_SOURCE,
            "decision_authority": A1_ADOPTION_DECISION_AUTHORITY,
            "decision_date": "2026-07-17",
            "adopted": [
                "The official California State Parks Salmon Falls Lower Water "
                "Raft Take-out access geometry is ground truth for the "
                "downstream anchor.",
                "The mainstem route is the directed NHD flowline chain from the "
                "Chili Bar seed, re-validated against official access points.",
                "Published mile figures are alias metadata with a recorded "
                "divergence note; they are not anchors.",
                "Items formerly gated on local guide review become "
                "pending_human_review entries batched to the P7 owner packet "
                "and do not block stationing or corridor binding.",
            ],
            "rejected_anchor_candidates": _rejected_anchor_candidate_records(
                context["official_review"]
            ),
            "supersedes_promotion_gates_in": [
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
                FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
                FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
                FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
            ],
            "evidence_policy": (
                "The superseded artifacts remain committed as discrepancy "
                "evidence; their anchor-selection promotion gates are resolved "
                "by this adoption, and no evidence is deleted."
            ),
        },
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
            "source_mile_divergence_audit": (
                FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH
            ),
        },
        "station_axis": {
            "axis_id": A1_ADOPTED_STATION_AXIS_ID,
            "axis_source": "nhd_source_lengthkm_along_directed_chain",
            "directed_chain_edge_count": len(chain),
            "directed_chain_length_m": chain[-1]["station_end_m"],
            "adopted_route_edge_count": route_edge_count,
            "adopted_route_length_m": round(anchor_station_m, 6),
            "adopted_route_length_miles": round(
                anchor_station_m / MILES_TO_METERS,
                3,
            ),
            "cross_check": {
                "divergence_audit_official_access_station_m": audit_anchor_station_m,
                "delta_m": round(anchor_station_m - audit_anchor_station_m, 6),
                "matches_divergence_audit": (
                    abs(anchor_station_m - audit_anchor_station_m) < 0.001
                ),
            },
        },
        "upstream_anchor": {
            "name": "Chili Bar put-in review seed",
            "annotation_id": "chili_bar_put_in_review_seed",
            "lon_lat": list(context["chili_lon_lat"]),
            "station_m": 0.0,
            "anchor_status": "adopted_route_origin",
        },
        "downstream_anchor": {
            "name": official_seed["name"],
            "fid": official_seed["fid"],
            "gisid": official_seed["gisid"],
            "lon_lat": official_seed["lon_lat"],
            "authority": "california_state_parks_parking_points",
            "anchor_status": "adopted_ground_truth_official_access_geometry",
            "station_m": round(anchor_station_m, 6),
            "station_miles": round(anchor_station_m / MILES_TO_METERS, 3),
            "nearest_chain_node_lon_lat": list(context["anchor_node"]),
            "snap_distance_m": round(context["anchor_snap_distance_m"], 3),
            "pending_human_review": {
                "review_id": "salmon_falls_takeout_bank_landing_confirmation",
                "review_batch": P7_REVIEW_BATCH_ID,
                "blocking": False,
                "note": (
                    "The parking-centroid anchor is adopted for stationing; the "
                    "exact riverbank landing refinement rides the P7 owner "
                    "packet and does not block stationing or corridor binding."
                ),
            },
        },
        "published_mile_aliases": {
            "alias_policy": "published_river_miles_are_alias_metadata_not_anchors",
            "aliases": aliases,
            "published_full_run_length_m": published_run_length_m,
            "published_full_run_length_miles": round(
                published_run_length_m / MILES_TO_METERS,
                3,
            ),
            "adopted_axis_length_to_official_anchor_m": round(anchor_station_m, 6),
            "excess_axis_length_after_published_full_run_m": full_run_alias[
                "remaining_axis_distance_to_adopted_anchor_m"
            ],
            "divergence_note": (
                "Published guide miles reach 21.0 miles well upstream of the "
                "official Salmon Falls Lower Water Raft Take-out; the adopted "
                "NHD source-length axis measures 30.495 miles from Chili Bar "
                "to that anchor. Published miles are recorded as aliases with "
                "this divergence and are not used as anchors."
            ),
        },
        "rapid_stations": rapid_stations,
        "rapid_station_summary": {
            "rapid_count": len(rapid_stations),
            "stations_monotonic_increasing": all(
                earlier < later for earlier, later in zip(stations, stations[1:])
            ),
            "max_station_m": max(stations),
            "all_stations_within_adopted_route": max(stations) <= anchor_station_m,
            "order_interpolation_used": False,
            "stationing_basis": "published_mile_alias_projected_along_adopted_axis",
        },
        "pending_human_review": [
            {
                **item,
                "review_batch": P7_REVIEW_BATCH_ID,
                "blocking": False,
            }
            for item in _PENDING_HUMAN_REVIEW_ITEMS
        ],
        "promotion_gate": {
            "can_use_adopted_axis_for_stationing": True,
            "can_restation_named_rapids": True,
            "can_crop_to_final_downstream_anchor": True,
            "can_plan_corridor_windows_against_adopted_axis": True,
            "can_bind_solver_windows": True,
            "can_bind_named_rapid_geometry": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_claim_photoreal_or_gameplay_realism": False,
            "gate_reasons": {
                "can_bind_solver_windows": (
                    "Unblocked by the adoption; window regeneration and binding "
                    "execute inside P3-P4 against this axis."
                ),
                "can_bind_named_rapid_geometry": (
                    "Exact per-rapid geometry authoring is P3/P4 work; this "
                    "artifact provides stationing only and fabricates no rapid "
                    "geometry."
                ),
                "can_import_unreal_full_reach_landscape": (
                    "Committed window source pulls cover the planned 0-33796 m "
                    "spans; extending coverage to the 49078 m adopted axis is "
                    "P3/P4 source-pull work."
                ),
                "can_claim_photoreal_or_gameplay_realism": (
                    "This adoption unblocks stationing and corridor binding "
                    "only; it makes no photoreal or gameplay realism claims."
                ),
            },
        },
    }


def build_south_fork_a1_adopted_route_geojson(repo_root: Path) -> dict[str, Any]:
    """Build the adopted route/stationing visual layer."""

    repo_root = repo_root.resolve()
    stationing = build_south_fork_a1_adopted_route_stationing(repo_root)
    context = _chain_context(repo_root)
    route_coordinates = _clip_chain_coordinates(
        context["features"],
        context["chain"],
        stationing["downstream_anchor"]["station_m"],
    )
    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            "id": "adopted_upstream_anchor_chili_bar",
            "geometry": {
                "type": "Point",
                "coordinates": stationing["upstream_anchor"]["lon_lat"],
            },
            "properties": {
                "marker_kind": "adopted_upstream_anchor",
                "station_m": 0.0,
                "production_promoted": False,
            },
        },
        {
            "type": "Feature",
            "id": "adopted_downstream_anchor_salmon_falls_takeout",
            "geometry": {
                "type": "Point",
                "coordinates": stationing["downstream_anchor"]["lon_lat"],
            },
            "properties": {
                "marker_kind": "adopted_downstream_anchor_official_access",
                "fid": stationing["downstream_anchor"]["fid"],
                "gisid": stationing["downstream_anchor"]["gisid"],
                "station_m": stationing["downstream_anchor"]["station_m"],
                "snap_distance_m": stationing["downstream_anchor"]["snap_distance_m"],
                "production_promoted": False,
            },
        },
        {
            "type": "Feature",
            "id": "adopted_route_chili_bar_to_salmon_falls_takeout",
            "geometry": {
                "type": "LineString",
                "coordinates": route_coordinates,
            },
            "properties": {
                "marker_kind": "adopted_route_centerline",
                "axis_id": stationing["station_axis"]["axis_id"],
                "station_start_m": 0.0,
                "station_end_m": stationing["downstream_anchor"]["station_m"],
                "point_count": len(route_coordinates),
                "production_promoted": False,
            },
        },
    ]
    for alias in stationing["published_mile_aliases"]["aliases"]:
        features.append(
            {
                "type": "Feature",
                "id": alias["alias_id"],
                "geometry": {
                    "type": "Point",
                    "coordinates": alias["lon_lat_on_adopted_axis"],
                },
                "properties": {
                    "marker_kind": "published_mile_alias",
                    "published_miles": alias["published_miles"],
                    "station_m": alias["station_m_on_adopted_axis"],
                    "rejected_as_anchor": True,
                    "production_promoted": False,
                },
            }
        )
    for rapid in stationing["rapid_stations"]:
        rapid_id = rapid["name"].lower().replace(" ", "_").replace("'", "")
        features.append(
            {
                "type": "Feature",
                "id": f"rapid_{rapid['order']:02d}_{rapid_id}",
                "geometry": {
                    "type": "Point",
                    "coordinates": rapid["lon_lat"],
                },
                "properties": {
                    "marker_kind": "named_rapid_station_adopted_axis",
                    "label": rapid["name"],
                    "order": rapid["order"],
                    "station_m": rapid["station_m"],
                    "published_river_mile_alias": rapid["published_river_mile_alias"],
                    "exact_geometry_status": rapid["exact_geometry_status"],
                    "pending_human_review": True,
                    "review_batch": rapid["review_batch"],
                    "production_promoted": False,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_adopted_route.geojson.v1",
        "generated_on": stationing["generated_on"],
        "task_id": stationing["task_id"],
        "river_id": stationing["river_id"],
        "status": stationing["status"],
        "decision_source": A1_ADOPTION_DECISION_SOURCE,
        "source_json": FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
        "production_promoted": False,
        "feature_count": len(features),
        "features": features,
        "policy": {
            "allowed_use": [
                "full-reach route stationing",
                "corridor window planning and regeneration basis",
                "editor/GIS overlay",
                "P3/P4 rapid-geometry authoring reference",
            ],
            "forbidden_use": [
                "exact rapid geometry authority",
                "public access or rescue navigation",
                "photoreal or gameplay realism claims",
            ],
        },
    }


def write_south_fork_a1_adopted_route_stationing(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    stationing = build_south_fork_a1_adopted_route_stationing(repo_root)
    route_geojson = build_south_fork_a1_adopted_route_geojson(repo_root)
    outputs = [
        repo_root / FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
        repo_root / FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
    ]
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(
        json.dumps(stationing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    outputs[1].write_text(
        json.dumps(route_geojson, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outputs
