"""Record downstream access/source leads for the South Fork A1 anchor decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_downstream_anchor_decision import (
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH,
)


FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_downstream_access_publication_review.json"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def build_south_fork_a1_downstream_access_publication_review(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the link-only downstream access/source review for A1."""

    repo_root = repo_root.resolve()
    decision_packet = _load_json(
        repo_root,
        FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH,
    )
    return {
        "schema": "raftsim.south_fork.a1_downstream_access_publication_review.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": decision_packet["river_id"],
        "status": "official_downstream_access_source_leads_attached_exact_geometry_pending",
        "production_promoted": False,
        "scope": (
            "Downstream Salmon Falls/Folsom access, publication-sensitivity, "
            "and source-authority review for choosing the South Fork full-run endpoint."
        ),
        "inputs": {
            "downstream_anchor_decision_packet": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH
            ),
            "downstream_anchor_candidates_geojson": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
            ),
        },
        "sources_checked": [
            {
                "source_id": "ca_state_parks_dbw_salmon_falls_btaf",
                "provider": "California Department of Parks and Recreation / Division of Boating and Waterways",
                "url": "https://www.parks.ca.gov/BoatingFacilities/f/1200",
                "retrieved_on": "2026-07-16",
                "http_status": 200,
                "rights_status": "link_only_factual_index",
                "review_status": "official_facility_page_reviewed_geometry_pending",
                "used_for": [
                    "Official public boating-access lead for Folsom Lake SRA Salmon Falls BTAF.",
                    "Confirms body-of-water context as American River-South Fork.",
                    "Confirms California State Parks jurisdiction/authority and El Dorado County context.",
                ],
                "evidence": [
                    "Facility name is Folsom Lake SRA Salmon Falls BTAF.",
                    "Facility address is Salmon Falls Road, Folsom, California.",
                    "Body of water is American River-South Fork.",
                    "Facility type is boating access and access is public.",
                    "Jurisdiction/authority is California Department of Parks and Recreation.",
                ],
                "blocked_from": [
                    "exact take-out coordinate",
                    "bank-side landing point",
                    "parking polygon",
                    "public/private parcel boundary",
                    "reservoir-stage-dependent access rule",
                ],
            },
            {
                "source_id": "ca_state_parks_dbw_american_south_fork_facilities",
                "provider": "California Department of Parks and Recreation / Division of Boating and Waterways",
                "url": "https://dbw.parks.ca.gov/BoatingFacilities/Body-of-Water/American%20River-South%20Fork",
                "retrieved_on": "2026-07-16",
                "http_status": 200,
                "rights_status": "link_only_factual_index",
                "review_status": "official_facility_index_reviewed_geometry_pending",
                "used_for": [
                    "Cross-check that Folsom Lake SRA Salmon Falls BTAF is in the official American River-South Fork boating-facility index.",
                    "Cross-check that the facility class is boating access and public access.",
                    "Compare downstream access with Gorge Run, Greenwood Creek, Henningsen-Lotus, Skunk Hollow, and Slab Creek entries during station review.",
                ],
                "evidence": [
                    "The American River-South Fork facility index lists Folsom Lake SRA Salmon Falls BTAF.",
                    "The same index lists its facility type as boating access.",
                    "The same index lists access as public.",
                ],
                "blocked_from": [
                    "final take-out identity",
                    "exact ramp or shore coordinate",
                    "current operating restriction",
                    "publication-sensitive route geometry",
                ],
            },
            {
                "source_id": "blm_south_fork_american_river",
                "provider": "Bureau of Land Management",
                "url": "https://www.blm.gov/visit/south-fork-american-river",
                "retrieved_on": "2026-07-16",
                "http_status": 200,
                "rights_status": "u_s_government_link_only_factual_index",
                "review_status": "official_route_context_reviewed_exact_anchor_pending",
                "used_for": [
                    "Official federal route-context lead for South Fork American public-land recreation.",
                    "Confirms BLM route context for a 21-mile South Fork run.",
                    "Confirms Salmon Falls Bridge appears as an official take-out option.",
                ],
                "evidence": [
                    "BLM identifies the South Fork American as a whitewater rafting and kayaking destination.",
                    "BLM describes a twenty-one-mile river run.",
                    "BLM lists Salmon Falls Bridge among take-out options.",
                    "BLM lists multiple upstream put-in/access options, including Chili Bar.",
                ],
                "blocked_from": [
                    "exact Salmon Falls Bridge landing coordinate",
                    "final source-mile convention",
                    "parking or route-publication authority",
                    "commercial permit interpretation",
                    "guide-reviewed line or rescue access",
                ],
            },
            {
                "source_id": "ca_state_parks_folsom_lake_boat_launch_status",
                "provider": "California Department of Parks and Recreation",
                "url": "https://www.parks.ca.gov/?page_id=31951",
                "retrieved_on": "2026-07-16",
                "http_status": 200,
                "rights_status": "link_only_factual_index",
                "review_status": "current_park_operations_lead_not_anchor_authority",
                "used_for": [
                    "Current Folsom Lake SRA operations and launch-status lead for reservoir-stage/access review.",
                    "Reminder that launch/access status can change and must be checked at review time.",
                ],
                "evidence": [
                    "California State Parks publishes current Folsom Lake SRA boat-launch status.",
                    "The status page records open/closed launch areas and current operation notes.",
                ],
                "blocked_from": [
                    "Salmon Falls exact access claim",
                    "future operating status",
                    "river take-out coordinate",
                    "gameplay or public screenshot authority",
                ],
            },
        ],
        "candidate_support": [
            {
                "option_id": "select_20_5_mile_salmon_falls_basis",
                "supporting_sources": [
                    "ca_state_parks_dbw_salmon_falls_btaf",
                    "ca_state_parks_dbw_american_south_fork_facilities",
                    "blm_south_fork_american_river",
                ],
                "support_status": "official_access_and_takeout_leads_attached_exact_geometry_pending",
                "still_required": [
                    "confirm exact riverbank take-out point relative to bridge",
                    "confirm whether the candidate should be named Salmon Falls Bridge, Salmon Falls BTAF, Skunk Hollow, or another reviewed access label",
                    "confirm reservoir-stage effects on landing/access",
                    "attach guide/geospatial review",
                ],
            },
            {
                "option_id": "select_21_0_mile_full_run_folsom_basis",
                "supporting_sources": [
                    "blm_south_fork_american_river",
                    "ca_state_parks_dbw_salmon_falls_btaf",
                    "ca_state_parks_folsom_lake_boat_launch_status",
                ],
                "support_status": "official_21_mile_route_context_attached_exact_full_run_endpoint_pending",
                "still_required": [
                    "confirm whether the extra 804.672 m over-cover represents a real playable take-out extension or only guide/source-mile wording",
                    "confirm Folsom Reservoir stage/access implications",
                    "attach exact access geometry and public/private land status",
                    "attach guide/geospatial review",
                ],
            },
        ],
        "required_editor_annotations": [
            FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
            "review/full_reach_downstream_access_publication_review.json",
            "future: reviewed downstream access polygon/point GeoJSON",
            "future: reservoir-stage/access note",
            "future: guide/geospatial reviewer decision",
        ],
        "allowed_use": [
            "source-lead triage",
            "anchor decision review",
            "editor/GIS overlay planning",
            "publication-sensitivity checklist preparation",
        ],
        "forbidden_use": [
            "final access geometry",
            "public/private land authority",
            "reservoir-stage access authority",
            "Unreal corridor crop",
            "named-rapid stationing authority",
            "solver-window binding",
            "public route-detail screenshots without review",
        ],
        "promotion_gate": {
            "can_select_downstream_anchor": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_restation_named_rapids": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Review official California State Parks facility/map context and BLM route context in the editor/GIS tool.",
                "Attach exact take-out/access geometry from an accepted official layer, survey, or guide-reviewed field point.",
                "Record reservoir-stage/access implications for the selected endpoint.",
                "Record guide/geospatial/publication-sensitivity approval before route crop or rapid restationing.",
            ],
        },
    }


def write_south_fork_a1_downstream_access_publication_review(repo_root: Path) -> Path:
    payload = build_south_fork_a1_downstream_access_publication_review(repo_root)
    path = repo_root.resolve() / FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
