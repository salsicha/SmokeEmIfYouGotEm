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
FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_access_decision_validation_report.json"
)
FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.south_fork.a1_source_mile_access_decision_result_template.v1"
)
FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_SCHEMA = (
    "raftsim.south_fork.a1_source_mile_access_decision_validation_report.v1"
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


def build_south_fork_a1_source_mile_access_decision_validation_report(
    repo_root: Path,
    decision_result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a source-mile/access decision result without promoting A1."""

    packet = build_south_fork_a1_source_mile_access_decision_packet(repo_root)
    template = (
        decision_result_payload
        if decision_result_payload is not None
        else build_south_fork_a1_source_mile_access_decision_result_template(repo_root)
    )
    result = template["decision_result"]
    reviewers = template["reviewer_signoff"]
    missing_fields = _missing_decision_fields(template)
    invalid_fields = _invalid_decision_fields(
        result,
        packet["required_decision_record"]["must_choose_one_option_id"],
    )
    reviewer_failures = _reviewer_failures(reviewers)
    validation_errors = [
        {"field": field, "reason": "required_field_empty"}
        for field in missing_fields
    ]
    validation_errors.extend(
        {"field": field, "reason": reason}
        for field, reason in invalid_fields
    )
    validation_errors.extend(
        {"field": role, "reason": reason}
        for role, reason in reviewer_failures
    )
    decision_valid = not validation_errors
    status = (
        "decision_result_valid_manual_regeneration_allowed"
        if decision_valid
        else "decision_result_incomplete_route_promotion_blocked"
    )
    return {
        "schema": FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": packet["river_id"],
        "status": status,
        "production_promoted": False,
        "source_decision_packet": (
            FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH
        ),
        "source_result_template": (
            FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH
        ),
        "decision_valid": decision_valid,
        "validation_error_count": len(validation_errors),
        "missing_required_fields": missing_fields,
        "invalid_fields": [
            {"field": field, "reason": reason} for field, reason in invalid_fields
        ],
        "reviewer_failures": [
            {"role": role, "reason": reason} for role, reason in reviewer_failures
        ],
        "decision_summary": {
            "chosen_option_id": result["chosen_option_id"],
            "decision_owner": result["decision_owner"],
            "decision_date": result["decision_date"],
            "decision_status": result["decision_status"],
            "route_regeneration_scope_count": len(result["route_regeneration_scope"]),
        },
        "allowed_option_ids": packet["required_decision_record"][
            "must_choose_one_option_id"
        ],
        "regeneration_permissions": {
            "can_promote_current_nhd_route": False,
            "can_regenerate_directed_route": decision_valid,
            "can_regenerate_corridor_windows": decision_valid,
            "can_restation_named_rapids": decision_valid,
            "can_bind_named_rapid_geometry": decision_valid,
            "can_bind_solver_windows": decision_valid,
            "manual_review_still_required_after_valid_result": True,
        },
        "promotion_gate": {
            "can_select_endpoint_from_validation_report_alone": False,
            "can_promote_current_route_without_regenerated_artifacts": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_solver_windows_from_empty_or_invalid_result": False,
            "next_after_valid_result": [
                step["step_id"]
                for step in packet["post_decision_regeneration_plan"]
            ],
        },
    }


def write_south_fork_a1_source_mile_access_decision_validation_report(
    repo_root: Path,
) -> Path:
    payload = build_south_fork_a1_source_mile_access_decision_validation_report(
        repo_root
    )
    path = (
        repo_root
        / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_RELATIVE_PATH
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _missing_decision_fields(template: dict[str, Any]) -> list[str]:
    result = template["decision_result"]
    reviewers = template["reviewer_signoff"]
    missing = []
    field_values = {
        "chosen_option_id": result["chosen_option_id"],
        "decision_owner": result["decision_owner"],
        "decision_date": result["decision_date"],
        "selected_downstream_endpoint_lon_lat_or_centerline_geometry": (
            _geometry_is_complete(
                result["selected_downstream_endpoint_lon_lat_or_centerline_geometry"]
            )
        ),
        "endpoint_source_authority": result["endpoint_source_authority"],
        "simulation_station_axis_policy": result["simulation_station_axis_policy"],
        "published_mile_convention_policy": result[
            "published_mile_convention_policy"
        ],
        "guide_reviewer": _reviewer_complete(
            reviewers["river_guide_or_oarsman_domain_reviewer"]
        ),
        "geospatial_reviewer": _reviewer_complete(
            reviewers["geospatial_reviewer"]
        ),
        "rights_publication_reviewer": _reviewer_complete(
            reviewers["rights_publication_reviewer"]
        ),
        "reservoir_stage_or_access_assumptions": result[
            "reservoir_stage_or_access_assumptions"
        ],
        "route_regeneration_scope": result["route_regeneration_scope"],
    }
    for field in template["required_filled_fields"]:
        value = field_values[field]
        if value is False or value == "" or value == []:
            missing.append(field)
    return missing


def _invalid_decision_fields(
    result: dict[str, Any],
    allowed_option_ids: list[str],
) -> list[tuple[str, str]]:
    invalid = []
    option_id = result["chosen_option_id"]
    if option_id and option_id not in allowed_option_ids:
        invalid.append(("chosen_option_id", "option_id_not_allowed"))
    if result["decision_status"] not in {"not_recorded", "approved", "rejected"}:
        invalid.append(("decision_status", "unsupported_decision_status"))
    geometry = result["selected_downstream_endpoint_lon_lat_or_centerline_geometry"]
    if geometry["coordinates"] and geometry["geometry_type"] == "":
        invalid.append(("selected_downstream_endpoint_lon_lat_or_centerline_geometry", "geometry_type_required"))
    return invalid


def _reviewer_failures(
    reviewers: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    failures = []
    for role, payload in reviewers.items():
        if not payload["approved"]:
            failures.append((role, "review_not_approved"))
        if not payload["name_or_role"] or not payload["review_date"]:
            failures.append((role, "reviewer_identity_or_date_missing"))
    return failures


def _geometry_is_complete(geometry: dict[str, Any]) -> bool:
    has_geometry = bool(geometry["coordinates"] or geometry["source_report"])
    return bool(
        geometry["geometry_type"]
        and has_geometry
        and geometry["crs"]
        and geometry["source_authority"]
        and geometry["source_report"]
    )


def _reviewer_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["name_or_role"]
        and payload["review_date"]
        and payload["approved"]
        and payload["evidence"]
    )
