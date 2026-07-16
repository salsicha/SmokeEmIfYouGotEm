"""Build the South Fork A1 downstream-anchor reviewer action packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_downstream_access_review import (
    FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH,
)
from .south_fork_a1_downstream_anchor_decision import (
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH,
)
from .south_fork_a1_official_access_geometry_review import (
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH,
)


FULL_REACH_DOWNSTREAM_ANCHOR_REVIEW_ACTIONS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_downstream_anchor_review_actions.json"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _candidate_feature_counts(geojson: dict[str, Any]) -> dict[str, int]:
    geometry_types: dict[str, int] = {}
    for feature in geojson["features"]:
        geometry_type = feature["geometry"]["type"]
        geometry_types[geometry_type] = geometry_types.get(geometry_type, 0) + 1
    return geometry_types


def _review_window_inputs(packet: dict[str, Any]) -> list[dict[str, Any]]:
    windows = []
    for role, window in packet["visual_review_inputs"].items():
        artifacts = window["derived_artifacts"]
        windows.append(
            {
                "role": role,
                "window_id": window["window_id"],
                "station_range_m": window["station_range_m"],
                "required_artifacts": [
                    {
                        "artifact_id": "naip_centerline_preview",
                        "path": artifacts["naip_centerline_preview"]["path"],
                        "sha256": artifacts["naip_centerline_preview"]["sha256"],
                        "review_use": "primary aerial/route overlay for candidate placement",
                    },
                    {
                        "artifact_id": "hillshade",
                        "path": artifacts["hillshade"]["path"],
                        "sha256": artifacts["hillshade"]["sha256"],
                        "review_use": "terrain context for banks, road cuts, bridge approaches, and reservoir shoreline",
                    },
                    {
                        "artifact_id": "heightfield",
                        "path": artifacts["heightfield"]["path"],
                        "sha256": artifacts["heightfield"]["sha256"],
                        "review_use": "source elevation derivative for later crop/terrain sanity checks",
                    },
                    {
                        "artifact_id": "stitched_edge_report",
                        "path": window["edge_report"]["path"],
                        "sha256": window["edge_report"]["sha256"],
                        "review_use": "seam and source-window continuity check before final crop",
                    },
                ],
            }
        )
    return windows


def _source_document_summary(access_review: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": source["source_id"],
            "provider": source["provider"],
            "url": source["url"],
            "rights_status": source["rights_status"],
            "review_status": source["review_status"],
            "used_for": source["used_for"],
            "blocked_from": source["blocked_from"],
        }
        for source in access_review["sources_checked"]
    ]


def build_south_fork_a1_downstream_anchor_review_actions(
    repo_root: Path,
) -> dict[str, Any]:
    """Build a deterministic reviewer checklist for selecting the A1 endpoint."""

    repo_root = repo_root.resolve()
    packet = _load_json(repo_root, FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH)
    access_review = _load_json(repo_root, FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH)
    official_access_geometry_review = _load_json(
        repo_root,
        FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    )
    geojson = _load_json(
        repo_root,
        FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    )
    geometry_type_counts = _candidate_feature_counts(geojson)
    option_ids = [option["option_id"] for option in packet["options"]]

    return {
        "schema": "raftsim.south_fork.a1_downstream_anchor_review_actions.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": packet["river_id"],
        "status": "editor_geospatial_review_actions_ready_exact_anchor_pending",
        "production_promoted": False,
        "scope": (
            "Reviewer-facing action packet for choosing the exact downstream "
            "South Fork full-reach anchor, source-mile convention, final crop, "
            "and publication-sensitivity rule."
        ),
        "inputs": {
            "downstream_anchor_decision_packet": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH
            ),
            "downstream_access_publication_review": (
                FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH
            ),
            "candidate_geojson": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
            ),
            "official_access_geometry_discrepancy_review": (
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH
            ),
            "official_access_geometry_leads_geojson": (
                FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH
            ),
        },
        "evidence_bundle": {
            "candidate_geojson": {
                "path": FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
                "feature_count": len(geojson["features"]),
                "geometry_type_counts": geometry_type_counts,
                "candidate_option_ids": option_ids,
                "production_promoted": False,
            },
            "station_options": packet["options"],
            "station_delta_m": packet["candidate_window"]["station_delta_m"],
            "review_windows": _review_window_inputs(packet),
            "official_source_leads": _source_document_summary(access_review),
            "official_access_geometry_discrepancy": {
                "path": FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
                "geojson_overlay_path": FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH,
                "status": official_access_geometry_review["status"],
                "primary_official_access_geometry_lead": official_access_geometry_review[
                    "primary_official_access_geometry_lead"
                ],
                "rejected_candidate_count": official_access_geometry_review["summary"][
                    "rejected_candidate_count"
                ],
                "minimum_distance_to_any_official_access_m": official_access_geometry_review[
                    "summary"
                ]["minimum_distance_to_any_official_access_m"],
                "minimum_distance_to_primary_raft_takeout_m": official_access_geometry_review[
                    "summary"
                ]["minimum_distance_to_primary_raft_takeout_m"],
                "replacement_or_reanchored_endpoint_required": official_access_geometry_review[
                    "summary"
                ]["replacement_or_reanchored_endpoint_required"],
            },
        },
        "required_review_roles": [
            {
                "role_id": "geospatial_or_technical_art_reviewer",
                "required_decision": (
                    "Confirm exact riverbank endpoint geometry, source CRS, "
                    "station_m, and final crop relative to the candidate points."
                ),
            },
            {
                "role_id": "river_guide_or_oarsman_domain_reviewer",
                "required_decision": (
                    "Confirm whether the selected endpoint matches runnable "
                    "guide practice and whether reservoir level changes the take-out."
                ),
            },
            {
                "role_id": "rights_or_publication_sensitivity_reviewer",
                "required_decision": (
                    "Approve what access geometry, maps, and screenshots can be "
                    "published, withheld, or blurred."
                ),
            },
            {
                "role_id": "owner_or_producer_acceptance",
                "required_decision": (
                    "Accept the source-mile convention and unblock corridor crop "
                    "only after the other reviewer records are complete."
                ),
            },
        ],
        "action_sequence": [
            {
                "action_id": "load_evidence_bundle",
                "title": "Load candidate GeoJSON and the two downstream review windows.",
                "required_inputs": [
                    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
                    "lower_gorge_window.naip_centerline_preview",
                    "anchor_review_window.naip_centerline_preview",
                    "lower_gorge_window.hillshade",
                    "anchor_review_window.hillshade",
                ],
                "expected_output": (
                    "Reviewer can see both candidate points and the 804.672 m "
                    "decision span against aerial and terrain derivatives."
                ),
            },
            {
                "action_id": "verify_official_access_context",
                "title": "Check official access/source leads and geometry against the candidate points.",
                "required_inputs": [
                    "ca_state_parks_dbw_salmon_falls_btaf",
                    "ca_state_parks_dbw_american_south_fork_facilities",
                    "blm_south_fork_american_river",
                    "ca_state_parks_folsom_lake_boat_launch_status",
                    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
                    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH,
                ],
                "expected_output": (
                    "Current NHD candidate-point mismatch, exact geometry source, "
                    "unresolved source disagreement, and unsupported access claims "
                    "are recorded separately."
                ),
            },
            {
                "action_id": "resolve_source_mile_convention",
                "title": "Choose 20.5-mile, 21.0-mile, or replacement reviewed endpoint basis.",
                "required_inputs": option_ids,
                "expected_output": (
                    "Selected source-mile convention or replacement endpoint basis "
                    "is recorded; current NHD candidate points remain invalid after "
                    "the official access-geometry discrepancy unless a corrected "
                    "route is regenerated and approved."
                ),
            },
            {
                "action_id": "record_exact_anchor_geometry",
                "title": "Attach exact lon/lat, station_m, and geometry authority.",
                "required_inputs": [
                    "official Salmon Falls Lower Water Raft Take-out access seed",
                    "accepted official layer, field point, survey, or guide-reviewed GIS point",
                    "CRS/datum note",
                    "reservoir-stage/access interpretation",
                ],
                "expected_output": (
                    "A replacement or selected endpoint is explicit enough for final "
                    "window crop, rapid restationing, and editor overlay regeneration."
                ),
            },
            {
                "action_id": "record_publication_sensitivity",
                "title": "Decide what downstream access details may appear in public captures.",
                "required_inputs": [
                    "access/land-status note",
                    "publication sensitivity note",
                    "no-publish geometry if needed",
                ],
                "expected_output": (
                    "Public route-detail screenshots are either approved, restricted, "
                    "or blocked with a documented reason."
                ),
            },
            {
                "action_id": "record_reviewer_signoff",
                "title": "Capture reviewer identities, dates, evidence links, and decision comments.",
                "required_inputs": [
                    "geospatial reviewer",
                    "guide/oarsman reviewer",
                    "rights/publication reviewer",
                    "owner/producer acceptance",
                ],
                "expected_output": (
                    "Every required role has a dated result before any promotion flag can change."
                ),
            },
            {
                "action_id": "regenerate_after_approval_only",
                "title": "Regenerate crop/station/editor artifacts only after approval is complete.",
                "required_inputs": [
                    "completed downstream anchor selection record",
                    "completed publication-sensitivity record",
                ],
                "expected_output": (
                    "Final clipped corridor, all 20 rapid stations, editor markers, "
                    "and solver windows are regenerated from the selected anchor."
                ),
            },
        ],
        "review_result_template": {
            "schema": "raftsim.south_fork.a1_downstream_anchor_review_result.v1",
            "selected_option_id": "",
            "replacement_endpoint_used": False,
            "exact_anchor_lon_lat": [],
            "exact_anchor_station_m": None,
            "source_mile_convention": "",
            "geometry_authority": "",
            "access_land_status": "",
            "reservoir_stage_access_note": "",
            "publication_sensitivity_decision": "",
            "reviewers": {
                "geospatial_or_technical_art_reviewer": {
                    "name_or_role": "",
                    "review_date": "",
                    "approved": False,
                    "notes": "",
                },
                "river_guide_or_oarsman_domain_reviewer": {
                    "name_or_role": "",
                    "review_date": "",
                    "approved": False,
                    "notes": "",
                },
                "rights_or_publication_sensitivity_reviewer": {
                    "name_or_role": "",
                    "review_date": "",
                    "approved": False,
                    "notes": "",
                },
                "owner_or_producer_acceptance": {
                    "name_or_role": "",
                    "review_date": "",
                    "approved": False,
                    "notes": "",
                },
            },
            "production_promoted": False,
        },
        "promotion_gate": {
            "can_select_downstream_anchor_from_this_packet_alone": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_promote_full_reach_centerline": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "complete_when": [
                "selected_option_id is one of the packet options or replacement_endpoint_used is true",
                "exact anchor lon/lat, CRS, station_m, source-mile convention, and geometry authority are recorded",
                "geospatial, guide/oarsman, rights/publication, and owner acceptance reviews are approved with dates",
                "reservoir-stage/access and public-screenshot policy are explicitly recorded",
            ],
            "next_after_completion": [
                "Regenerate final downstream crop and station axis.",
                "Re-station all 20 South Fork rapid markers without order interpolation.",
                "Regenerate catalog/editor marker outputs and corridor regression tests.",
                "Only then bind Meat Grinder and Troublemaker solver windows to production geometry.",
            ],
        },
    }


def write_south_fork_a1_downstream_anchor_review_actions(repo_root: Path) -> Path:
    payload = build_south_fork_a1_downstream_anchor_review_actions(repo_root)
    path = repo_root.resolve() / FULL_REACH_DOWNSTREAM_ANCHOR_REVIEW_ACTIONS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
