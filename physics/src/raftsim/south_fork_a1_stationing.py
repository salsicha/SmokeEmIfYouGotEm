"""Track the South Fork A1 stationing repair gate.

This module intentionally records what is and is not solved by the current
source package. It is not an alternate geometry generator.
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


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _rapid_station_records(river: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rapid in river["rapids"]:
        river_mile = float(rapid["river_mile"])
        exact_geometry_status = (
            "blocked_pending_full_reach_centerline_and_guide_review"
        )
        records.append(
            {
                "name": rapid["name"],
                "order": rapid["order"],
                "river_mile": river_mile,
                "station_m_from_published_mile": round(river_mile * MILES_TO_METERS, 3),
                "review_priority": rapid["review_priority"],
                "feature_tags": rapid["feature_tags"],
                "exact_geometry_status": exact_geometry_status,
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

    The five-river execution plan requires full Chili Bar-to-Folsom stationing
    and exact rapid geometry. Current committed evidence does not yet prove that,
    so this artifact keeps the blocker explicit while preserving the usable
    published rapid-mile scaffold and official flow-source attachments.
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

    rapid_records = _rapid_station_records(river)
    max_rapid = max(rapid_records, key=lambda rapid: rapid["river_mile"])
    coloma_station_m = float(
        alignment["published_reference"]["coloma_bridge_station_m"]
    )
    candidate_length_m = float(
        alignment["candidate_centerline"]["declared_length_m"]
    )
    full_run_length_m = float(river["run_length_m"])

    return {
        "schema": "raftsim.south_fork.a1_stationing_repair_status.v1",
        "generated_on": "2026-07-16",
        "plan": (
            "docs/five-river-photoreal-execution-plan.md"
            "#workstream-a--source-data-stationing-and-seasonal-flows-per-river"
        ),
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "blocked_pending_full_reach_hydrography_exact_anchors_and_guide_review",
        "production_promoted": False,
        "do_not_use_for": [
            "exact rapid geometry",
            "solver water-window binding",
            "public access or rescue geometry",
            "production-playable South Fork completion",
        ],
        "catalog_stationing_scaffold": {
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "stationing_authority": river["stationing_authority"],
            "run_length_m": full_run_length_m,
            "run_length_miles": round(full_run_length_m / MILES_TO_METERS, 3),
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
            "why_blocked": alignment["decision"],
        },
        "current_source_coverage": {
            "nhd_bbox_extract": NHD_BBOX_MANIFEST_RELATIVE_PATH,
            "nhd_bbox_bounds_wgs84": nhd_manifest["bounds_wgs84"],
            "nhd_extract_method": nhd_manifest["extract_method"]["type"],
            "nhd_extract_is_full_reach": False,
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
            "coverage_blocker": (
                "The committed NHD extract is a pilot bbox and the physical corridor is "
                "a 0-2.5 km Chili Bar slice; neither covers the full Chili Bar-to-Folsom "
                "run or proves exact Coloma/Folsom anchors."
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
        },
        "a1_acceptance": [
            {
                "requirement": (
                    "Fix NHD flowline conflict and re-anchor Chili Bar plus "
                    "Folsom take-out."
                ),
                "status": "blocked",
                "evidence": [
                    ALIGNMENT_REVIEW_RELATIVE_PATH,
                    NHD_BBOX_MANIFEST_RELATIVE_PATH,
                ],
                "next_action": (
                    "Acquire or derive a full-reach official hydrography route, select the correct "
                    "South Fork mainstem path, and record exact reviewed put-in/take-out anchors."
                ),
            },
            {
                "requirement": "Extend corridor to the full Chili Bar-to-Folsom reach.",
                "status": "blocked",
                "evidence": [PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH],
                "next_action": (
                    "Replace the current 0-2.5 km physical corridor slice with windowed full-run "
                    "corridor packages after official route selection."
                ),
            },
            {
                "requirement": "Attach official low/reference/high flow bands.",
                "status": "attached_but_review_gated",
                "evidence": [
                    FLOW_SOURCE_SELECTION_RELATIVE_PATH,
                    FLOW_BAND_REVIEW_RELATIVE_PATH,
                ],
                "next_action": (
                    "Expand CBR/A25 seasonal windows, resolve A25 flag/routing/legal review, and "
                    "obtain guide/outfitter validation before promotion."
                ),
            },
            {
                "requirement": "Re-station all 20 catalog markers with no order interpolation.",
                "status": "published_mile_scaffold_ready_exact_geometry_blocked",
                "evidence": [SOURCE_CATALOG_RELATIVE_PATH],
                "next_action": (
                    "Project the published miles only after the corrected centerline and anchors "
                    "are reviewed; then regenerate editor markers through the catalog generator."
                ),
            },
            {
                "requirement": (
                    "Exit gate: conflict resolved and zero South Fork markers "
                    "use order interpolation."
                ),
                "status": "not_met",
                "evidence": [ALIGNMENT_REVIEW_RELATIVE_PATH],
                "next_action": (
                    "Do not enable South Fork editor-map geometry or Meat Grinder/Troublemaker "
                    "solver windows until the alignment review status changes to resolved."
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
