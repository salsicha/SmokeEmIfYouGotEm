"""Build the South Fork A1 source-mile/access decision result template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_source_mile_access_decision import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH,
    build_south_fork_a1_source_mile_access_decision_packet,
)


FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_access_decision_result_template.json"
)
FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.south_fork.a1_source_mile_access_decision_result_template.v1"
)

_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "river_guide_or_oarsman_domain_reviewer",
    "geospatial_reviewer",
    "rights_publication_reviewer",
)


def build_south_fork_a1_source_mile_access_decision_result_template(
    repo_root: Path,
) -> dict[str, Any]:
    """Build an empty, fail-closed template for the required A1 decision."""

    packet = build_south_fork_a1_source_mile_access_decision_packet(repo_root)
    required_record = packet["required_decision_record"]
    option_ids = list(required_record["must_choose_one_option_id"])
    return {
        "schema": FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": packet["river_id"],
        "status": "empty_decision_result_template_no_route_promotion",
        "production_promoted": False,
        "source_decision_packet": (
            FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH
        ),
        "evidence_summary": packet["evidence_summary"],
        "allowed_option_ids": option_ids,
        "decision_result": {
            "decision_id": required_record["decision_id"],
            "chosen_option_id": "",
            "decision_owner": "",
            "decision_date": "",
            "decision_status": "not_recorded",
            "selected_downstream_endpoint_lon_lat_or_centerline_geometry": {
                "geometry_type": "",
                "coordinates": [],
                "crs": "",
                "source_authority": "",
                "source_report": "",
            },
            "endpoint_source_authority": "",
            "simulation_station_axis_policy": "",
            "published_mile_convention_policy": "",
            "reservoir_stage_or_access_assumptions": "",
            "route_regeneration_scope": [],
            "decision_notes": "",
        },
        "reviewer_signoff": {
            role: {
                "name_or_role": "",
                "review_date": "",
                "approved": False,
                "evidence": [],
                "notes": "",
            }
            for role in _REVIEW_ROLES
        },
        "required_filled_fields": required_record["required_fields"],
        "required_reviewer_roles": list(_REVIEW_ROLES),
        "post_decision_regeneration_plan": packet[
            "post_decision_regeneration_plan"
        ],
        "validation_contract": {
            "template_is_empty": True,
            "chosen_option_must_be_allowed": True,
            "all_required_fields_must_be_populated": True,
            "all_reviewer_roles_must_approve": True,
            "route_regeneration_scope_must_be_non_empty": True,
            "selected_geometry_must_include_crs_and_source_report": True,
            "may_promote_current_route_from_empty_template": False,
            "may_regenerate_corridor_windows_from_empty_template": False,
            "may_restation_named_rapids_from_empty_template": False,
            "may_bind_solver_windows_from_empty_template": False,
        },
        "blocked_actions_until_completed_result": required_record["blocks"],
        "promotion_gate": {
            "can_promote_current_nhd_route": False,
            "can_select_endpoint_from_empty_template": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_regenerate_corridor_windows": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "complete_when": [
                "chosen_option_id is one allowed option id",
                "all required_decision_record fields are populated",
                "selected geometry includes coordinates or centerline reference, CRS, source authority, and source report",
                "all required reviewer roles approve with names, dates, evidence, and notes",
                "route_regeneration_scope lists the exact artifacts to rebuild",
            ],
        },
    }


def write_south_fork_a1_source_mile_access_decision_result_template(
    repo_root: Path,
) -> Path:
    payload = build_south_fork_a1_source_mile_access_decision_result_template(
        repo_root
    )
    path = (
        repo_root
        / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
