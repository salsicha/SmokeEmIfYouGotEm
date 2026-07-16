"""Build and validate the Colorado A2 centerline/CRS decision template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .colorado_a2_centerline_acquisition_plan import (
    COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH,
    build_colorado_a2_centerline_acquisition_plan,
)
from .colorado_a2_metadata_probe import (
    COLORADO_A2_METADATA_PROBE_RELATIVE_PATH,
    build_colorado_a2_metadata_probe,
)


COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/review/"
    "full_reach_centerline_decision_template.json"
)
COLORADO_A2_CENTERLINE_DECISION_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/review/"
    "full_reach_centerline_decision_validation_report.json"
)
COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_SCHEMA = (
    "raftsim.colorado.a2_centerline_decision_template.v1"
)
COLORADO_A2_CENTERLINE_DECISION_VALIDATION_SCHEMA = (
    "raftsim.colorado.a2_centerline_decision_validation_report.v1"
)

_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "grand_canyon_oarsman_or_guide_reviewer",
    "geospatial_reviewer",
    "rights_publication_reviewer",
    "technical_world_partition_reviewer",
)

_ALLOWED_OPTION_IDS = (
    "official_hydrography_with_nps_gcmrc_river_mile_calibration",
    "reviewed_local_river_mile_axis_with_source_raster_transforms",
    "defer_until_pearce_ferry_anchor_or_source_family_is_reviewed",
)

_REQUIRED_FIELDS = (
    "chosen_option_id",
    "decision_owner",
    "decision_date",
    "full_length_centerline_source",
    "lees_ferry_anchor_geometry",
    "pearce_ferry_anchor_geometry",
    "working_crs_or_station_axis_policy",
    "river_mile_calibration_policy",
    "major_rapid_crosscheck_policy",
    "source_window_bbox_generation_scope",
    "route_regeneration_scope",
    "rights_publication_policy",
)


def build_colorado_a2_centerline_decision_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty fail-closed decision template for Colorado A2."""

    acquisition = build_colorado_a2_centerline_acquisition_plan(repo_root)
    metadata_probe = build_colorado_a2_metadata_probe()
    return {
        "schema": COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A2",
        "river_id": acquisition["river_id"],
        "display_name": acquisition["display_name"],
        "status": "empty_centerline_decision_template_no_source_download_no_promotion",
        "production_promoted": False,
        "source_contracts": {
            "centerline_acquisition_plan": COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH,
            "metadata_probe": COLORADO_A2_METADATA_PROBE_RELATIVE_PATH,
        },
        "evidence_summary": {
            "existing_editor_binding_max_station_m": acquisition["current_scope_gap"][
                "existing_editor_binding_max_station_m"
            ],
            "planned_run_length_m": acquisition["current_scope_gap"]["planned_run_length_m"],
            "a2_window_count_waiting_for_bboxes": acquisition["current_scope_gap"][
                "a2_window_count_waiting_for_bboxes"
            ],
            "hydrography_tnm_total": _probe_result(
                metadata_probe, "hydrography"
            )["total"],
            "terrain_tnm_total": _probe_result(
                metadata_probe, "terrain_dem_or_lidar"
            )["total"],
            "naip_tnm_total": _probe_result(metadata_probe, "aerial_imagery")[
                "total"
            ],
            "pearce_ferry_anchor_status": "missing_exact_anchor",
        },
        "allowed_option_ids": list(_ALLOWED_OPTION_IDS),
        "required_filled_fields": list(_REQUIRED_FIELDS),
        "required_reviewer_roles": list(_REVIEW_ROLES),
        "decision_result": {
            "decision_id": "colorado_a2_full_reach_centerline_crs_and_endpoint_policy",
            "chosen_option_id": "",
            "decision_owner": "",
            "decision_date": "",
            "decision_status": "not_recorded",
            "full_length_centerline_source": {
                "source_family": "",
                "source_product_or_dataset": "",
                "source_report": "",
                "source_feature_id_policy": "",
                "notes": "",
            },
            "lees_ferry_anchor_geometry": _empty_geometry("upstream_start"),
            "pearce_ferry_anchor_geometry": _empty_geometry("downstream_end"),
            "working_crs_or_station_axis_policy": {
                "policy_id": "",
                "crs_or_axis": "",
                "distortion_review_report": "",
                "unreal_world_partition_notes": "",
            },
            "river_mile_calibration_policy": {
                "source_authority": "",
                "station_zero_policy": "",
                "river_mile_tick_policy": "",
                "source_report": "",
            },
            "major_rapid_crosscheck_policy": {
                "required_sources": [],
                "crosscheck_report": "",
                "acceptable_tolerance_m": None,
                "unresolved_disagreement_policy": "",
            },
            "source_window_bbox_generation_scope": {
                "windows_to_generate": [],
                "buffer_policy_m": None,
                "terrain_export_policy": "",
                "imagery_export_policy": "",
            },
            "route_regeneration_scope": [],
            "rights_publication_policy": "",
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
        "validation_contract": {
            "template_is_empty": True,
            "chosen_option_must_be_allowed": True,
            "all_required_fields_must_be_populated": True,
            "all_reviewer_roles_must_approve": True,
            "endpoint_geometries_must_include_crs_source_authority_and_source_report": True,
            "source_window_scope_must_name_windows_and_bounded_export_policies": True,
            "route_regeneration_scope_must_be_non_empty": True,
            "may_download_sources_from_empty_template": False,
            "may_generate_window_bboxes_from_empty_template": False,
            "may_promote_rapid_stationing_from_empty_template": False,
            "may_bind_solver_windows_from_empty_template": False,
        },
        "promotion_gate": {
            "can_download_full_reach_sources": False,
            "can_generate_source_window_bboxes": False,
            "can_promote_full_reach_centerline": False,
            "can_restation_major_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_solver_windows": False,
            "complete_when": [
                "chosen_option_id is one allowed option id",
                "Lees Ferry and Pearce Ferry anchors include reviewed geometry, CRS, source authority, and source report",
                "full-length centerline source and source-feature ID policy are recorded",
                "working CRS or station-axis policy includes distortion and Unreal streaming review evidence",
                "major-rapid cross-check policy names NPS/USGS/oarsman evidence and tolerance",
                "source-window bbox generation scope lists windows, buffers, terrain exports, and imagery exports",
                "all required reviewer roles approve with dated evidence",
            ],
        },
    }


def write_colorado_a2_centerline_decision_template(repo_root: Path) -> Path:
    payload = build_colorado_a2_centerline_decision_template(repo_root)
    path = repo_root / COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_colorado_a2_centerline_decision_validation_report(
    repo_root: Path,
    decision_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a Colorado A2 centerline decision payload without promotion."""

    template = (
        decision_payload
        if decision_payload is not None
        else build_colorado_a2_centerline_decision_template(repo_root)
    )
    result = template["decision_result"]
    missing_fields = _missing_decision_fields(template)
    invalid_fields = _invalid_decision_fields(result, template["allowed_option_ids"])
    reviewer_failures = _reviewer_failures(template["reviewer_signoff"])
    validation_errors = [
        {"field": field, "reason": "required_field_empty"}
        for field in missing_fields
    ]
    validation_errors.extend(
        {"field": field, "reason": reason} for field, reason in invalid_fields
    )
    validation_errors.extend(
        {"field": role, "reason": reason} for role, reason in reviewer_failures
    )
    decision_valid = not validation_errors
    return {
        "schema": COLORADO_A2_CENTERLINE_DECISION_VALIDATION_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A2",
        "river_id": template["river_id"],
        "display_name": template["display_name"],
        "status": (
            "centerline_decision_valid_manual_regeneration_allowed"
            if decision_valid
            else "centerline_decision_incomplete_a2_promotion_blocked"
        ),
        "production_promoted": False,
        "source_result_template": COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH,
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
            "source_window_count": len(
                result["source_window_bbox_generation_scope"]["windows_to_generate"]
            ),
        },
        "allowed_option_ids": template["allowed_option_ids"],
        "regeneration_permissions": {
            "can_download_full_reach_sources": decision_valid,
            "can_generate_source_window_bboxes": decision_valid,
            "can_generate_full_reach_centerline_candidate": decision_valid,
            "can_generate_rapid_mile_crosscheck": decision_valid,
            "can_restation_major_rapids": decision_valid,
            "can_bind_solver_windows": decision_valid,
            "can_promote_from_validation_report_alone": False,
            "manual_review_still_required_after_valid_result": True,
        },
        "promotion_gate": {
            "can_promote_current_lees_ferry_pilot_to_full_run": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_solver_windows_from_empty_or_invalid_result": False,
            "next_after_valid_result": [
                "generate_full_reach_centerline_candidate",
                "generate_source_window_bboxes",
                "generate_rapid_mile_crosscheck",
                "generate_full_reach_source_pull_plan",
            ],
        },
    }


def write_colorado_a2_centerline_decision_validation_report(repo_root: Path) -> Path:
    payload = build_colorado_a2_centerline_decision_validation_report(repo_root)
    path = repo_root / COLORADO_A2_CENTERLINE_DECISION_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _empty_geometry(role: str) -> dict[str, Any]:
    return {
        "role": role,
        "geometry_type": "",
        "coordinates": [],
        "crs": "",
        "source_authority": "",
        "source_report": "",
        "publication_sensitivity": "",
    }


def _probe_result(metadata_probe: dict[str, Any], source_class: str) -> dict[str, Any]:
    for result in metadata_probe["results"]:
        if result["source_class"] == source_class:
            return result
    raise RuntimeError(f"Missing metadata probe result: {source_class}")


def _missing_decision_fields(template: dict[str, Any]) -> list[str]:
    result = template["decision_result"]
    values = {
        "chosen_option_id": result["chosen_option_id"],
        "decision_owner": result["decision_owner"],
        "decision_date": result["decision_date"],
        "full_length_centerline_source": _centerline_source_complete(
            result["full_length_centerline_source"]
        ),
        "lees_ferry_anchor_geometry": _geometry_complete(
            result["lees_ferry_anchor_geometry"]
        ),
        "pearce_ferry_anchor_geometry": _geometry_complete(
            result["pearce_ferry_anchor_geometry"]
        ),
        "working_crs_or_station_axis_policy": _working_crs_complete(
            result["working_crs_or_station_axis_policy"]
        ),
        "river_mile_calibration_policy": _river_mile_policy_complete(
            result["river_mile_calibration_policy"]
        ),
        "major_rapid_crosscheck_policy": _rapid_crosscheck_policy_complete(
            result["major_rapid_crosscheck_policy"]
        ),
        "source_window_bbox_generation_scope": _source_window_scope_complete(
            result["source_window_bbox_generation_scope"]
        ),
        "route_regeneration_scope": result["route_regeneration_scope"],
        "rights_publication_policy": result["rights_publication_policy"],
    }
    return [
        field
        for field in template["required_filled_fields"]
        if values[field] is False or values[field] == "" or values[field] == []
    ]


def _invalid_decision_fields(
    result: dict[str, Any], allowed_option_ids: list[str]
) -> list[tuple[str, str]]:
    invalid = []
    option_id = result["chosen_option_id"]
    if option_id and option_id not in allowed_option_ids:
        invalid.append(("chosen_option_id", "option_id_not_allowed"))
    if result["decision_status"] not in {"not_recorded", "approved", "rejected"}:
        invalid.append(("decision_status", "unsupported_decision_status"))
    if result["source_window_bbox_generation_scope"]["buffer_policy_m"] is not None:
        if result["source_window_bbox_generation_scope"]["buffer_policy_m"] <= 0:
            invalid.append(("source_window_bbox_generation_scope", "buffer_policy_m_must_be_positive"))
    return invalid


def _reviewer_failures(reviewers: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    failures = []
    for role, payload in reviewers.items():
        if not payload["approved"]:
            failures.append((role, "review_not_approved"))
        if not payload["name_or_role"] or not payload["review_date"]:
            failures.append((role, "reviewer_identity_or_date_missing"))
        if not payload["evidence"]:
            failures.append((role, "review_evidence_missing"))
    return failures


def _centerline_source_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["source_family"]
        and payload["source_product_or_dataset"]
        and payload["source_report"]
        and payload["source_feature_id_policy"]
    )


def _geometry_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["geometry_type"]
        and payload["coordinates"]
        and payload["crs"]
        and payload["source_authority"]
        and payload["source_report"]
        and payload["publication_sensitivity"]
    )


def _working_crs_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["policy_id"]
        and payload["crs_or_axis"]
        and payload["distortion_review_report"]
        and payload["unreal_world_partition_notes"]
    )


def _river_mile_policy_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["source_authority"]
        and payload["station_zero_policy"]
        and payload["river_mile_tick_policy"]
        and payload["source_report"]
    )


def _rapid_crosscheck_policy_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["required_sources"]
        and payload["crosscheck_report"]
        and payload["acceptable_tolerance_m"] is not None
        and payload["unresolved_disagreement_policy"]
    )


def _source_window_scope_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload["windows_to_generate"]
        and payload["buffer_policy_m"] is not None
        and payload["terrain_export_policy"]
        and payload["imagery_export_policy"]
    )
