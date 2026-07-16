"""Record source-mile anchors for the South Fork A1 full-reach repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_full_reach_acquisition import (
    ACCESS_POINTS_RELATIVE_PATH,
    FULL_REACH_ACQUISITION_RELATIVE_PATH,
)
from .south_fork_a1_route_graph import (
    FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH,
    build_south_fork_a1_route_graph_diagnostic,
)
from .south_fork_a1_stationing import ALIGNMENT_REVIEW_RELATIVE_PATH


FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_anchor_review.json"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _source_record(catalog: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in catalog["sources"]:
        if source["source_id"] == source_id:
            return source
    raise ValueError(f"Missing source record {source_id}")


def _access_feature(access_points: dict[str, Any], annotation_id: str) -> dict[str, Any]:
    for feature in access_points["features"]:
        if feature["properties"]["annotation_id"] == annotation_id:
            return feature
    raise ValueError(f"Missing access feature {annotation_id}")


def _station_miles_to_meters(miles: float) -> float:
    return round(miles * MILES_TO_METERS, 6)


def _source_lead(
    catalog: dict[str, Any],
    source_id: str,
    used_for: list[str],
) -> dict[str, Any]:
    source = _source_record(catalog, source_id)
    return {
        "source_id": source["source_id"],
        "title": source["title"],
        "url": source["url"],
        "source_kind": source["source_kind"],
        "rights_status": source["rights_status"],
        "used_for": used_for,
    }


def build_south_fork_a1_full_reach_anchor_review(repo_root: Path) -> dict[str, Any]:
    """Build the source-backed full-reach anchor review for A1.

    This is a factual index of source mile anchors and current review seeds. It
    intentionally does not promote the route, infer exact access geometry, or
    replace guide/geospatial review.
    """

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    alignment = _load_json(repo_root, ALIGNMENT_REVIEW_RELATIVE_PATH)
    route_graph = build_south_fork_a1_route_graph_diagnostic(repo_root)

    chili_seed = _access_feature(access_points, "chili_bar_put_in_review_seed")
    coloma_seed = _access_feature(access_points, "coloma_takeout_review_seed")
    coloma_diagnostic = route_graph["anchor_diagnostics"][
        "current_coloma_access_seed"
    ]
    folsom_diagnostic = route_graph["anchor_diagnostics"]["folsom_reservoir_takeout"]
    american_rivers_id = "south_fork_american_rivers_mile_guide"
    american_whitewater_id = "south_fork_americanwhitewater_map"
    american_rivers_coloma_mile = float(
        alignment["published_reference"]["coloma_bridge_river_mile"]
    )
    american_rivers_folsom_mile = 20.5
    american_whitewater_folsom_mile = 21.0

    return {
        "schema": "raftsim.south_fork.a1_full_reach_anchor_review.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "blocked_source_mile_anchors_recorded_exact_geometry_pending_review",
        "production_promoted": False,
        "rights_policy": catalog["rights_policy"],
        "inputs": {
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
            "alignment_review": ALIGNMENT_REVIEW_RELATIVE_PATH,
            "full_reach_acquisition_plan": FULL_REACH_ACQUISITION_RELATIVE_PATH,
            "route_graph_diagnostic": FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH,
        },
        "source_leads": [
            _source_lead(
                catalog,
                american_rivers_id,
                [
                    "Chili Bar source mile 0.0",
                    "Coloma Bridge checkpoint source mile 5.6",
                    "Salmon Falls Bridge/Folsom-area take-out source mile 20.5",
                ],
            ),
            _source_lead(
                catalog,
                american_whitewater_id,
                [
                    "Chili Bar put-in source mile 0.0",
                    "Full Chili Bar-to-Folsom/Salmon Falls run length 21.0 miles",
                ],
            ),
        ],
        "anchor_reviews": [
            {
                "anchor_id": "chili_bar_put_in",
                "role": "upstream_start",
                "source_mile_evidence": [
                    {
                        "source_id": american_rivers_id,
                        "published_river_mile": 0.0,
                        "station_m": 0.0,
                    },
                    {
                        "source_id": american_whitewater_id,
                        "published_river_mile": 0.0,
                        "station_m": 0.0,
                    },
                ],
                "current_seed_lon_lat": [
                    chili_seed["properties"]["station_lon"],
                    chili_seed["properties"]["station_lat"],
                ],
                "current_seed_status": chili_seed["properties"][
                    "stationing_status"
                ],
                "validation_status": (
                    "source_mile_agrees_but_exact_access_geometry_unreviewed"
                ),
                "promotion_blockers": [
                    "official access/land-status geometry not attached",
                    "guide/local review not attached",
                    "full directed route not clipped to this anchor",
                ],
            },
            {
                "anchor_id": "coloma_bridge_checkpoint",
                "role": "station_checkpoint_not_final_takeout",
                "source_mile_evidence": [
                    {
                        "source_id": american_rivers_id,
                        "published_river_mile": american_rivers_coloma_mile,
                        "station_m": _station_miles_to_meters(
                            american_rivers_coloma_mile
                        ),
                    },
                    {
                        "source_id": american_whitewater_id,
                        "published_river_mile": american_rivers_coloma_mile,
                        "station_m": _station_miles_to_meters(
                            american_rivers_coloma_mile
                        ),
                    },
                ],
                "current_seed_lon_lat": [
                    coloma_seed["properties"]["station_lon"],
                    coloma_seed["properties"]["station_lat"],
                ],
                "current_seed_status": coloma_seed["properties"][
                    "stationing_status"
                ],
                "shortest_path_validation": {
                    "nearest_graph_node_distance_m": coloma_diagnostic[
                        "nearest_graph_node_distance_m"
                    ],
                    "graph_station_from_chili_bar_m": coloma_diagnostic[
                        "graph_station_from_chili_bar_m"
                    ],
                    "published_coloma_checkpoint_m": coloma_diagnostic[
                        "published_coloma_checkpoint_m"
                    ],
                    "graph_minus_published_checkpoint_m": coloma_diagnostic[
                        "graph_minus_published_checkpoint_m"
                    ],
                    "shortest_path_does_not_validate_published_checkpoint": (
                        coloma_diagnostic[
                            "shortest_path_does_not_validate_published_checkpoint"
                        ]
                    ),
                    "anchor_identity_requires_review": coloma_diagnostic[
                        "anchor_identity_requires_review"
                    ],
                },
                "validation_status": (
                    "shortest_path_does_not_validate_source_checkpoint"
                ),
                "interpretation": (
                    "This is a strict promotion blocker, not a final rejection of "
                    "the seed coordinate. The next repair must decide whether the "
                    "mismatch comes from the Coloma seed, directed graph traversal, "
                    "source fragments, or source-mile reference."
                ),
            },
            {
                "anchor_id": "salmon_falls_folsom_reservoir_takeout",
                "role": "downstream_end",
                "source_mile_evidence": [
                    {
                        "source_id": american_rivers_id,
                        "published_river_mile": american_rivers_folsom_mile,
                        "station_m": _station_miles_to_meters(
                            american_rivers_folsom_mile
                        ),
                    },
                    {
                        "source_id": american_whitewater_id,
                        "published_river_mile": american_whitewater_folsom_mile,
                        "station_m": _station_miles_to_meters(
                            american_whitewater_folsom_mile
                        ),
                    },
                ],
                "current_seed_lon_lat": folsom_diagnostic["seed_lon_lat"],
                "current_seed_status": folsom_diagnostic["seed_status"],
                "source_mile_window": {
                    "minimum_mile": american_rivers_folsom_mile,
                    "maximum_mile": american_whitewater_folsom_mile,
                    "delta_miles": round(
                        american_whitewater_folsom_mile
                        - american_rivers_folsom_mile,
                        3,
                    ),
                    "delta_m": _station_miles_to_meters(
                        american_whitewater_folsom_mile
                        - american_rivers_folsom_mile
                    ),
                },
                "validation_status": (
                    "exact_anchor_missing_source_mile_window_only"
                ),
                "promotion_blockers": [
                    "exact take-out/access coordinate missing",
                    "20.5 vs 21.0 mile source basis needs review",
                    "reservoir-stage/access geometry not attached",
                ],
            },
        ],
        "decisions_needed": [
            "Choose the authoritative full-run downstream anchor: Salmon Falls Bridge, Folsom Reservoir access, or another reviewed take-out point.",
            "Resolve the 20.5-mile vs 21.0-mile downstream-end source basis and record the chosen stationing convention.",
            "Resolve whether the Coloma checkpoint mismatch comes from the seed coordinate, directed graph traversal, source fragments, or source-mile reference.",
            "Clip a directed route through the named-flowline pool only after reviewed upstream, checkpoint, and downstream anchors are attached.",
        ],
        "promotion_gate": {
            "can_promote_full_reach_centerline": False,
            "can_enable_south_fork_editor_geometry": False,
            "can_bind_solver_windows": False,
            "can_regenerate_rapid_stationing": False,
            "exit_criteria": [
                "Reviewed Chili Bar, Coloma checkpoint, and Salmon Falls/Folsom anchors attached.",
                "Directed mainstem route validates Coloma within the configured tolerance.",
                "Directed mainstem route full length matches the chosen downstream source-mile basis.",
                "Guide/geospatial review approves any source-mile ambiguity before editor or solver binding.",
            ],
        },
    }


def write_south_fork_a1_full_reach_anchor_review(repo_root: Path) -> Path:
    payload = build_south_fork_a1_full_reach_anchor_review(repo_root)
    path = repo_root / FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
