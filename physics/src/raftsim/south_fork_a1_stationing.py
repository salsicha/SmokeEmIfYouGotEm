"""Track the South Fork A1 stationing gate.

This module intentionally records what is and is not solved by the current
source package. It is not an alternate geometry generator. As of the
release-1.0 plan §6 gate disposition (July 17 2026) it records the adopted
official-access downstream anchor and the active full-reach stationing on the
validated NHD mainstem chain, with remaining review items batched as
non-blocking ``pending_human_review`` entries for the P7 owner packet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH


A1_STATUS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "a1_stationing_repair_status.json"
)
FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_adopted_route_stationing.json"
)
FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_adopted_route.geojson"
)
A1_ADOPTION_DECISION_SOURCE = "release-1.0-plan-v2 §6, July 17 2026"
A1_ADOPTION_DECISION_AUTHORITY = (
    "docs/release-1.0-plan.md#6-gate-dispositions-mechanical--no-forms-no-waiting"
)
A1_ADOPTED_STATION_AXIS_ID = "adopted_nhd_directed_mainstem_chain_v1"
P7_REVIEW_BATCH_ID = "p7_owner_review_packet"
ALIGNMENT_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "named_rapid_station_alignment_review.json"
)
FLOW_BAND_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "production_import_pilot/flow_band_review.json"
)
FLOW_SOURCE_SELECTION_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "south_fork_modern_flow_source_selection.json"
)
NHD_BBOX_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "nhd_hu8_18020129_bbox_extract_manifest.json"
)
PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "chili_bar_reach_0_2500m/manifest.json"
)
FULL_REACH_WINDOW_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_manifest.json"
)
FULL_REACH_WINDOW_SOURCE_STATUS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_pull_status.json"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _rapid_station_records(
    river: dict[str, Any],
    adopted: dict[str, Any],
) -> list[dict[str, Any]]:
    adopted_by_name = {
        rapid["name"]: rapid for rapid in adopted["rapid_stations"]
    }
    records: list[dict[str, Any]] = []
    for rapid in river["rapids"]:
        river_mile = float(rapid["river_mile"])
        adopted_station = adopted_by_name[rapid["name"]]
        records.append(
            {
                "name": rapid["name"],
                "order": rapid["order"],
                "river_mile": river_mile,
                "station_m_from_published_mile": round(river_mile * MILES_TO_METERS, 3),
                "station_m_on_adopted_axis": adopted_station["station_m"],
                "lon_lat_on_adopted_axis": adopted_station["lon_lat"],
                "review_priority": rapid["review_priority"],
                "feature_tags": rapid["feature_tags"],
                "exact_geometry_status": (
                    "stationed_on_adopted_axis_exact_geometry_pending_p3_p4"
                ),
                "pending_human_review": True,
                "review_batch": P7_REVIEW_BATCH_ID,
            }
        )
    return records


def _load_corridor_local_centerline(
    repo_root: Path,
    corridor_manifest: dict[str, Any],
) -> dict[str, Any]:
    relative_path = corridor_manifest["derived_artifacts"]["local_centerline"]["path"]
    return _load_json(repo_root, relative_path)


def build_south_fork_a1_stationing_repair_status(repo_root: Path) -> dict[str, Any]:
    """Build the machine-readable current state for A1.

    The release-1.0 plan §6 gate disposition adopted the official California
    State Parks Salmon Falls Lower Water Raft Take-out geometry as the
    downstream anchor ground truth and the validated NHD directed mainstem
    chain as the station axis, so stationing is no longer blocked on anchor
    selection. Published mile figures remain alias metadata with a recorded
    divergence, guide-review items ride the P7 owner packet as non-blocking
    ``pending_human_review`` entries, and nothing here promotes exact rapid
    geometry, photoreal, or gameplay claims.
    """

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
    alignment = _load_json(repo_root, ALIGNMENT_REVIEW_RELATIVE_PATH)
    flow_review = _load_json(repo_root, FLOW_BAND_REVIEW_RELATIVE_PATH)
    source_selection = _load_json(repo_root, FLOW_SOURCE_SELECTION_RELATIVE_PATH)
    nhd_manifest = _load_json(repo_root, NHD_BBOX_MANIFEST_RELATIVE_PATH)
    corridor = _load_json(repo_root, PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH)
    corridor_centerline = _load_corridor_local_centerline(repo_root, corridor)
    adopted = _load_json(
        repo_root,
        FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
    )
    window_manifest = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_RELATIVE_PATH)
    window_status = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_STATUS_RELATIVE_PATH)

    rapid_records = _rapid_station_records(river, adopted)
    max_rapid = max(rapid_records, key=lambda rapid: rapid["river_mile"])
    coloma_station_m = float(
        alignment["published_reference"]["coloma_bridge_station_m"]
    )
    candidate_length_m = float(
        alignment["candidate_centerline"]["declared_length_m"]
    )
    full_run_length_m = float(river["run_length_m"])
    adopted_route_length_m = float(
        adopted["station_axis"]["adopted_route_length_m"]
    )
    downstream_anchor = adopted["downstream_anchor"]

    return {
        "schema": "raftsim.south_fork.a1_stationing_repair_status.v1",
        "generated_on": "2026-07-17",
        "plan": A1_ADOPTION_DECISION_AUTHORITY,
        "superseded_plan": (
            "docs/five-river-photoreal-execution-plan.md"
            "#workstream-a--source-data-stationing-and-seasonal-flows-per-river"
        ),
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "adopted_official_access_anchor_full_reach_stationing_active",
        "decision_source": A1_ADOPTION_DECISION_SOURCE,
        "production_promoted": False,
        "do_not_use_for": [
            "exact rapid geometry",
            "public access or rescue geometry",
            "photoreal or gameplay realism claims",
            "production-playable South Fork completion claims",
        ],
        "adopted_route_stationing": {
            "artifact": FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
            "route_geojson": FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
            "artifact_status": adopted["status"],
            "decision_source": adopted["decision"]["decision_source"],
            "station_axis_id": adopted["station_axis"]["axis_id"],
            "adopted_route_length_m": adopted_route_length_m,
            "adopted_route_length_miles": adopted["station_axis"][
                "adopted_route_length_miles"
            ],
            "downstream_anchor_name": downstream_anchor["name"],
            "downstream_anchor_fid": downstream_anchor["fid"],
            "downstream_anchor_authority": downstream_anchor["authority"],
            "downstream_anchor_station_m": downstream_anchor["station_m"],
            "downstream_anchor_snap_distance_m": downstream_anchor[
                "snap_distance_m"
            ],
            "published_mile_alias_policy": adopted["published_mile_aliases"][
                "alias_policy"
            ],
            "published_mile_divergence_note": adopted["published_mile_aliases"][
                "divergence_note"
            ],
            "rapid_station_count": adopted["rapid_station_summary"]["rapid_count"],
            "order_interpolation_used": adopted["rapid_station_summary"][
                "order_interpolation_used"
            ],
        },
        "catalog_stationing_scaffold": {
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "stationing_authority": river["stationing_authority"],
            "station_axis": A1_ADOPTED_STATION_AXIS_ID,
            "published_mile_role": "alias_metadata_with_recorded_divergence",
            "run_length_m": full_run_length_m,
            "run_length_miles": round(full_run_length_m / MILES_TO_METERS, 3),
            "adopted_route_length_m": adopted_route_length_m,
            "rapid_count": len(rapid_records),
            "rapid_mile_min": rapid_records[0]["river_mile"],
            "rapid_mile_max": max_rapid["river_mile"],
            "downstreammost_catalog_rapid": max_rapid["name"],
            "all_rapids_have_published_miles": all(
                "river_mile" in rapid for rapid in river["rapids"]
            ),
            "rapid_stations": rapid_records,
        },
        "current_geometry_evidence": {
            "alignment_review": ALIGNMENT_REVIEW_RELATIVE_PATH,
            "alignment_status": alignment["status"],
            "candidate_centerline_path": alignment["candidate_centerline"]["path"],
            "candidate_declared_section_id": alignment["candidate_centerline"][
                "declared_section_id"
            ],
            "candidate_declared_length_m": candidate_length_m,
            "published_chili_bar_to_coloma_length_m": coloma_station_m,
            "candidate_to_published_coloma_length_ratio": round(
                candidate_length_m / coloma_station_m,
                6,
            ),
            "access_seed_to_published_coloma_delta_m": alignment[
                "access_seed_comparison"
            ]["absolute_station_delta_m"],
            "existing_full_run_catalog_length_m": full_run_length_m,
            "candidate_covers_catalog_full_run_length": candidate_length_m
            >= full_run_length_m,
            "geometry_binding_enabled": False,
            "candidate_disposition": (
                "The chili_bar_to_coloma pilot candidate centerline remains "
                "rejected exactly as reviewed; it is superseded for stationing "
                "by the adopted NHD directed mainstem axis and retained as "
                "evidence."
            ),
            "adopted_axis_artifact": (
                FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
            ),
            "adopted_axis_stationing_enabled": True,
        },
        "current_source_coverage": {
            "nhd_bbox_extract": NHD_BBOX_MANIFEST_RELATIVE_PATH,
            "nhd_bbox_bounds_wgs84": nhd_manifest["bounds_wgs84"],
            "nhd_extract_method": nhd_manifest["extract_method"]["type"],
            "nhd_extract_is_full_reach": False,
            "full_reach_named_flowline_extract": (
                adopted["inputs"]["named_flowline_extract"]
            ),
            "full_reach_extract_supports_adopted_axis": True,
            "production_corridor_manifest": PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH,
            "production_corridor_reach_id": corridor["reach_id"],
            "production_corridor_status": corridor["status"],
            "production_corridor_local_centerline": corridor["derived_artifacts"][
                "local_centerline"
            ]["path"],
            "production_corridor_local_centerline_status": corridor_centerline["status"],
            "production_corridor_point_count": corridor["derived_artifacts"][
                "local_centerline"
            ]["point_count"],
            "production_corridor_station_range_m": corridor_centerline[
                "station_range_m"
            ],
            "full_reach_window_coverage": {
                "corridor_window_manifest": FULL_REACH_WINDOW_MANIFEST_RELATIVE_PATH,
                "source_pull_status": FULL_REACH_WINDOW_SOURCE_STATUS_RELATIVE_PATH,
                "window_count": window_status["summary"]["window_count"],
                "covered_station_end_m": window_manifest["coverage_summary"][
                    "planned_station_end_m"
                ],
                "covers_adopted_axis": window_manifest["coverage_summary"][
                    "covers_adopted_axis"
                ],
                "all_source_files_present": window_status["summary"][
                    "all_source_files_present"
                ],
            },
            "coverage_gap": (
                "Resolved July 17 2026: committed DEM/NAIP window pulls now "
                "cover the full 0-49078 m adopted axis in eight hash-locked "
                "windows. Only the 0-2.5 km physical pilot slice is promoted "
                "corridor terrain; that is derivative/review work inside "
                "P3/P4, not an anchor blocker."
            ),
        },
        "flow_evidence": {
            "source_selection": FLOW_SOURCE_SELECTION_RELATIVE_PATH,
            "source_selection_status": source_selection["status"],
            "primary_candidate": "CDEC CBR American River at Chili Bar",
            "secondary_context": "CDEC A25 Chili Bar Powerhouse",
            "flow_band_review": FLOW_BAND_REVIEW_RELATIVE_PATH,
            "flow_band_review_status": flow_review["status"],
            "reviewed_band_count": len(flow_review["reviewed_bands"]),
            "reviewed_bands": [
                {
                    "flow_band": band["flow_band"],
                    "planning_discharge_cfs": band["planning_discharge_cfs"],
                    "planning_discharge_m3s": band["planning_discharge_m3s"],
                    "promotion_decision": band["promotion_decision"],
                    "evidence_status": band["evidence_status"],
                }
                for band in flow_review["reviewed_bands"]
            ],
            "promotion_blockers": flow_review["promotion_blockers"],
            "review_routing": (
                "Guide/outfitter validation items are batched to the P7 owner "
                "packet as pending_human_review and do not block stationing or "
                "corridor binding; flow-band promotion remains its own gate."
            ),
        },
        "pending_human_review": adopted["pending_human_review"],
        "a1_acceptance": [
            {
                "requirement": (
                    "Fix NHD flowline conflict and re-anchor Chili Bar plus "
                    "Folsom take-out."
                ),
                "status": "adopted",
                "evidence": [
                    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
                    adopted["inputs"][
                        "official_access_geometry_discrepancy_review"
                    ],
                    adopted["inputs"]["official_access_reanchor_diagnostic"],
                    adopted["inputs"]["source_mile_divergence_audit"],
                ],
                "next_action": (
                    "None for stationing. The Salmon Falls bank-landing refinement rides the "
                    "P7 owner packet as a non-blocking pending_human_review item."
                ),
            },
            {
                "requirement": "Extend corridor to the full Chili Bar-to-Folsom reach.",
                "status": "extended_full_axis_window_sources_attached",
                "evidence": [
                    PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH,
                    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
                    FULL_REACH_WINDOW_MANIFEST_RELATIVE_PATH,
                    FULL_REACH_WINDOW_SOURCE_STATUS_RELATIVE_PATH,
                ],
                "next_action": (
                    "None for source coverage: eight hash-locked DEM/NAIP windows cover "
                    "the adopted 49078 m axis. Stitched-derivative review and Unreal "
                    "import readiness continue inside P3/P4 against these sources."
                ),
            },
            {
                "requirement": "Attach official low/reference/high flow bands.",
                "status": "attached_pending_human_review_non_blocking",
                "evidence": [
                    FLOW_SOURCE_SELECTION_RELATIVE_PATH,
                    FLOW_BAND_REVIEW_RELATIVE_PATH,
                ],
                "next_action": (
                    "Expand CBR/A25 seasonal windows and resolve the A25 flag/routing/legal "
                    "questions; guide/outfitter validation is batched to the P7 owner packet "
                    "and no longer blocks stationing."
                ),
            },
            {
                "requirement": "Re-station all 20 catalog markers with no order interpolation.",
                "status": "stationed_on_adopted_axis_no_order_interpolation",
                "evidence": [
                    SOURCE_CATALOG_RELATIVE_PATH,
                    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
                ],
                "next_action": (
                    "Author exact per-rapid geometry in P3/P4 and regenerate editor markers "
                    "through the catalog generator alongside that work; stations along the "
                    "adopted axis are recorded now."
                ),
            },
            {
                "requirement": (
                    "Exit gate: conflict resolved and zero South Fork markers "
                    "use order interpolation."
                ),
                "status": "met_for_stationing",
                "evidence": [FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH],
                "next_action": (
                    "Proceed to P3/P4 corridor window regeneration, exact rapid geometry "
                    "authoring, and solver-window binding against the adopted axis."
                ),
            },
        ],
    }


def write_south_fork_a1_stationing_repair_status(repo_root: Path) -> Path:
    payload = build_south_fork_a1_stationing_repair_status(repo_root)
    path = repo_root / A1_STATUS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
