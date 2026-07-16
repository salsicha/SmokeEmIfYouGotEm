"""Compare South Fork A1 downstream candidates with official access geometry."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .south_fork_a1_downstream_anchor_decision import (
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
)


FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_official_access_geometry_discrepancy_review.json"
)
FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_official_access_geometry_leads.geojson"
)

_PARKING_POINTS_DATASET_URL = "https://lab.data.ca.gov/dataset/parking-points"
_PARKING_POINTS_LAYER_URL = (
    "https://services2.arcgis.com/AhxrK3F6WM8ECvDi/arcgis/rest/services/"
    "ParkingPoints/FeatureServer/0"
)
_PARKING_POINTS_QUERY_URL = (
    f"{_PARKING_POINTS_LAYER_URL}/query?"
    "where=UPPER(UNITNAME)%20LIKE%20%27%25FOLSOM%25%27%20OR%20"
    "UPPER(NAME)%20LIKE%20%27%25SALMON%25%27%20OR%20"
    "UPPER(NAME)%20LIKE%20%27%25SKUNK%25%27&outFields=*&f=geojson"
)

_OFFICIAL_ACCESS_RECORDS: tuple[dict[str, Any], ...] = (
    {
        "fid": 50817,
        "name": "Old Salmon Falls Assembly Parking",
        "gisid": "GIS0005206",
        "use_type": "Day Use (No Fee)",
        "share": "Public",
        "trailhead": "Yes",
        "lon_lat": [-121.05840946152, 38.7522231811928],
        "review_role": "upstream_or_alternate_salmon_falls_context",
    },
    {
        "fid": 50924,
        "name": "Skunk Hollow Day Use Parking",
        "gisid": "GIS0005558",
        "use_type": "Day Use (Fee)",
        "share": "Public",
        "trailhead": "Yes",
        "lon_lat": [-121.03444619524, 38.7738621515691],
        "review_role": "nearby_public_access_context",
    },
    {
        "fid": 50927,
        "name": "Salmon Falls  Lower Water Raft Take-out",
        "gisid": "GIS0005556",
        "use_type": "Day Use (Fee)",
        "share": "Public",
        "trailhead": "Yes",
        "lon_lat": [-121.043513366612, 38.7717445614809],
        "review_role": "primary_official_downstream_access_geometry_lead",
    },
    {
        "fid": 50930,
        "name": "Salmon Falls Parking",
        "gisid": "GIS0005555",
        "use_type": "Day Use (Fee)",
        "share": "Public",
        "trailhead": "Yes",
        "lon_lat": [-121.042833677013, 38.7717617394222],
        "review_role": "parking_context_for_primary_takeout",
    },
    {
        "fid": 50933,
        "name": "Salmon Falls Overflow Parking",
        "gisid": "GIS0005554",
        "use_type": "Day Use (Fee)",
        "share": "Public",
        "trailhead": "",
        "lon_lat": [-121.042028800892, 38.7719121462091],
        "review_role": "parking_context_for_primary_takeout",
    },
)

_REJECT_EXACT_ANCHOR_DISTANCE_M = 1000.0
_WARN_ANCHOR_DISTANCE_M = 250.0


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(
        dlon / 2.0
    ) ** 2
    return 6371008.8 * 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))


def _point_features(candidate_geojson: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        feature
        for feature in candidate_geojson["features"]
        if feature["geometry"]["type"] == "Point"
    ]


def _primary_record() -> dict[str, Any]:
    return next(
        record
        for record in _OFFICIAL_ACCESS_RECORDS
        if record["review_role"] == "primary_official_downstream_access_geometry_lead"
    )


def _distance_to_official_records(feature: dict[str, Any]) -> dict[str, Any]:
    candidate_lon_lat = tuple(feature["geometry"]["coordinates"])
    distances = []
    for record in _OFFICIAL_ACCESS_RECORDS:
        official_lon_lat = tuple(record["lon_lat"])
        distances.append(
            {
                "official_fid": record["fid"],
                "official_name": record["name"],
                "official_review_role": record["review_role"],
                "distance_m": round(_haversine_m(candidate_lon_lat, official_lon_lat), 3),
            }
        )
    distances.sort(key=lambda item: item["distance_m"])
    primary = next(
        item
        for item in distances
        if item["official_review_role"] == "primary_official_downstream_access_geometry_lead"
    )
    nearest = distances[0]
    return {
        "option_id": feature["id"],
        "station_id": feature["properties"]["station_id"],
        "published_river_mile": feature["properties"]["published_river_mile"],
        "candidate_lon_lat": feature["geometry"]["coordinates"],
        "nearest_official_access": nearest,
        "primary_raft_takeout_distance_m": primary["distance_m"],
        "all_official_access_distances_m": distances,
        "candidate_geometry_status": (
            "rejected_for_exact_anchor_review"
            if nearest["distance_m"] > _REJECT_EXACT_ANCHOR_DISTANCE_M
            else "warning_official_access_offset_requires_review"
        ),
    }


def build_south_fork_a1_official_access_geometry_discrepancy_review(
    repo_root: Path,
) -> dict[str, Any]:
    """Build an official access-geometry discrepancy report for A1."""

    repo_root = repo_root.resolve()
    candidate_geojson = _load_json(
        repo_root,
        FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    )
    comparisons = [
        _distance_to_official_records(feature) for feature in _point_features(candidate_geojson)
    ]
    rejected_count = sum(
        item["candidate_geometry_status"] == "rejected_for_exact_anchor_review"
        for item in comparisons
    )
    primary = _primary_record()

    return {
        "schema": "raftsim.south_fork.a1_official_access_geometry_discrepancy_review.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": "south_fork_american_chili_bar",
        "status": "official_access_geometry_disagrees_with_current_nhd_downstream_candidates",
        "production_promoted": False,
        "source": {
            "source_id": "ca_state_parks_parking_points_arcgis",
            "dataset_url": _PARKING_POINTS_DATASET_URL,
            "feature_layer_url": _PARKING_POINTS_LAYER_URL,
            "query_url": _PARKING_POINTS_QUERY_URL,
            "provider": "California Department of Parks and Recreation / California Open Data",
            "retrieved_on": "2026-07-16",
            "http_status": 200,
            "license": "Creative Commons Attribution",
            "dataset_note": (
                "Parking Points is a simplified point layer of California State Parks "
                "parking-area centroids. It is a strong access-geometry lead, not a "
                "surveyed riverbank landing or reservoir-stage authority."
            ),
        },
        "inputs": {
            "downstream_anchor_decision_candidates_geojson": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
            ),
        },
        "official_access_records": list(_OFFICIAL_ACCESS_RECORDS),
        "primary_official_access_geometry_lead": primary,
        "thresholds": {
            "warn_anchor_distance_m": _WARN_ANCHOR_DISTANCE_M,
            "reject_exact_anchor_distance_m": _REJECT_EXACT_ANCHOR_DISTANCE_M,
        },
        "candidate_comparisons": comparisons,
        "summary": {
            "candidate_point_count": len(comparisons),
            "official_access_record_count": len(_OFFICIAL_ACCESS_RECORDS),
            "rejected_candidate_count": rejected_count,
            "current_nhd_candidate_points_can_be_selected_as_exact_anchor": False,
            "replacement_or_reanchored_endpoint_required": True,
            "minimum_distance_to_any_official_access_m": min(
                item["nearest_official_access"]["distance_m"] for item in comparisons
            ),
            "minimum_distance_to_primary_raft_takeout_m": min(
                item["primary_raft_takeout_distance_m"] for item in comparisons
            ),
        },
        "review_interpretation": [
            "The current 20.5-mile and 21.0-mile NHD-derived downstream candidate points are more than 9 km from the nearest official Salmon Falls/Skunk Hollow access geometry returned by State Parks.",
            "This rejects the current candidate point geometry for exact downstream-anchor selection.",
            "The published 20.5/21.0 mile disagreement may still be used as a source-mile convention question, but the physical endpoint must be re-anchored to official/guide-reviewed access geometry.",
            "The State Parks ParkingPoints feature is a parking/access lead and does not by itself define the riverbank landing, reservoir-stage usability, or public screenshot policy.",
        ],
        "impacted_artifacts": [
            {
                "path": FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
                "impact": "current downstream candidate points rejected for exact-anchor use",
            },
            {
                "path": "physics/data/real_world/south_fork_american_chili_bar/hydrography/full_reach_directed_route_clips.geojson",
                "impact": "directed downstream route clips must be regenerated after re-anchoring",
            },
            {
                "path": "physics/data/real_world/south_fork_american_chili_bar/production_corridor/full_reach_window_manifest.json",
                "impact": "full-reach window station spans and final source windows remain review-only until regenerated",
            },
            {
                "path": "physics/data/real_world/south_fork_american_chili_bar/production_corridor/full_reach_window_derivative_manifest.json",
                "impact": "review derivatives remain useful discrepancy evidence but cannot promote to Unreal import",
            },
        ],
        "promotion_gate": {
            "can_select_current_nhd_downstream_candidate": False,
            "can_select_official_parking_point_without_bank_review": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_promote_full_reach_centerline": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Use the official Salmon Falls Lower Water Raft Take-out and nearby parking points as new downstream access seeds.",
                "Re-run the NHD/3DHP route selection and clipping against the official access seed instead of the rejected downstream candidate points.",
                "Attach guide/geospatial review to choose the exact riverbank endpoint and source-mile convention.",
                "Regenerate corridor windows, derivatives, rapid stationing, and editor outputs only after the corrected route is accepted.",
            ],
        },
    }


def build_south_fork_a1_official_access_geometry_leads_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    review = build_south_fork_a1_official_access_geometry_discrepancy_review(repo_root)
    candidate_geojson = _load_json(
        repo_root.resolve(),
        FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    )
    primary = review["primary_official_access_geometry_lead"]
    features: list[dict[str, Any]] = []
    for record in review["official_access_records"]:
        features.append(
            {
                "type": "Feature",
                "id": f"official_access_{record['fid']}",
                "geometry": {
                    "type": "Point",
                    "coordinates": record["lon_lat"],
                },
                "properties": {
                    "source_id": review["source"]["source_id"],
                    "fid": record["fid"],
                    "name": record["name"],
                    "gisid": record["gisid"],
                    "review_role": record["review_role"],
                    "share": record["share"],
                    "use_type": record["use_type"],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            }
        )
    for comparison in review["candidate_comparisons"]:
        features.append(
            {
                "type": "Feature",
                "id": f"{comparison['option_id']}__to_primary_official_takeout",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        comparison["candidate_lon_lat"],
                        primary["lon_lat"],
                    ],
                },
                "properties": {
                    "source_id": review["source"]["source_id"],
                    "option_id": comparison["option_id"],
                    "candidate_geometry_status": comparison["candidate_geometry_status"],
                    "primary_raft_takeout_distance_m": comparison[
                        "primary_raft_takeout_distance_m"
                    ],
                    "production_promoted": False,
                    "can_bind_editor_geometry": False,
                    "can_bind_solver_windows": False,
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_official_access_geometry_leads.geojson.v1",
        "generated_on": review["generated_on"],
        "task_id": review["task_id"],
        "river_id": review["river_id"],
        "status": review["status"],
        "source": review["source"],
        "policy": {
            "allowed_use": [
                "editor/GIS discrepancy overlay",
                "official access seed review",
                "route re-anchoring planning",
            ],
            "forbidden_use": [
                "final riverbank landing geometry",
                "reservoir-stage access authority",
                "corridor crop authority",
                "named-rapid stationing authority",
                "solver-window binding",
            ],
        },
        "features": features,
        "candidate_feature_count_from_prior_geojson": len(candidate_geojson["features"]),
    }


def write_south_fork_a1_official_access_geometry_review(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    review = build_south_fork_a1_official_access_geometry_discrepancy_review(repo_root)
    geojson = build_south_fork_a1_official_access_geometry_leads_geojson(repo_root)
    outputs = [
        repo_root / FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
        repo_root / FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH,
    ]
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outputs[1].write_text(json.dumps(geojson, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return outputs
