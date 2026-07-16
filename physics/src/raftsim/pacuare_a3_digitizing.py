"""Build Pacuare A3 rapid-stationing digitizing packets and validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pacuare_a3_stationing import (
    PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
    build_pacuare_a3_stationing_repair_status,
)


PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_digitizing_action_packet.json"
)
PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_digitizing_result_template.json"
)
PACUARE_A3_DIGITIZING_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_digitizing_validation_report.json"
)
PACUARE_A3_DIGITIZING_ACTION_PACKET_SCHEMA = (
    "raftsim.pacuare.a3_stationing_digitizing_action_packet.v1"
)
PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.pacuare.a3_stationing_digitizing_result_template.v1"
)
PACUARE_A3_DIGITIZING_VALIDATION_REPORT_SCHEMA = (
    "raftsim.pacuare.a3_stationing_digitizing_validation_report.v1"
)

_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "pacuare_guide_or_outfitter_reviewer",
    "geospatial_reviewer",
    "rights_publication_reviewer",
    "hydrology_or_flow_reviewer",
)
_ALLOWED_GEOMETRY_TYPES = ("Point", "LineString")
_ALLOWED_STATIONING_KINDS = (
    "exact_gps_point",
    "aerial_interpreted_point",
    "aerial_interpreted_span",
    "guide_reviewed_point",
    "guide_reviewed_span",
)
_ALLOWED_FLOW_SOURCE_CLASSES = (
    "official_gauge",
    "stage_or_rainfall_station",
    "operator_runnable_range",
    "seasonal_precipitation_regime",
    "hypothesis_pending_guide_review",
)


def build_pacuare_a3_digitizing_action_packet(repo_root: Path) -> dict[str, Any]:
    """Build the fail-closed Pacuare A3 digitizing action packet."""

    status = build_pacuare_a3_stationing_repair_status(repo_root)
    rapid_records = status["catalog_stationing_scaffold"]["rapid_stations"]
    geometry = status["current_geometry_evidence"]
    flow = status["flow_evidence"]
    return {
        "schema": PACUARE_A3_DIGITIZING_ACTION_PACKET_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": status["river_id"],
        "display_name": status["display_name"],
        "status": "digitizing_actions_ready_no_stationing_promotion",
        "production_promoted": False,
        "source_status_artifact": PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
        "rapid_count": len(rapid_records),
        "critical_rapid_count": status["catalog_stationing_scaffold"][
            "critical_rapid_count"
        ],
        "current_blockers": {
            "all_rapids_are_order_only": status["catalog_stationing_scaffold"][
                "all_rapids_are_order_only"
            ],
            "preview_length_m": geometry["preview_length_m"],
            "catalog_run_length_m": geometry["catalog_run_length_m"],
            "preview_length_matches_catalog_run": geometry[
                "preview_length_matches_catalog_run"
            ],
            "flow_status": flow["flow_status"],
            "numeric_discharge_values_allowed": flow[
                "numeric_discharge_values_allowed"
            ],
        },
        "source_inputs": status["source_review_inputs"],
        "flow_evidence": flow,
        "digitizing_actions": [
            _digitizing_action(record) for record in rapid_records
        ],
        "required_workflow": [
            {
                "step_id": "select_reviewed_route_centerline",
                "required_before": "stationing_digitizing",
                "complete_when": (
                    "official hydrography, aerial-interpreted route, or guide-reviewed "
                    "route authority replaces the preview scaffold"
                ),
            },
            {
                "step_id": "select_accepted_aerial_or_orthomosaic_scene",
                "required_before": "stationing_digitizing",
                "complete_when": (
                    "cloud, shadow, resolution, protected-area, and rights review approve "
                    "the scene or orthomosaic for stationing"
                ),
            },
            {
                "step_id": "digitize_every_rapid_point_or_span",
                "required_before": "catalog_regeneration",
                "complete_when": (
                    "all 15 rapids have Point or LineString WGS84 geometry plus route "
                    "station, source evidence, confidence, and notes"
                ),
            },
            {
                "step_id": "record_guide_geospatial_rights_and_flow_review",
                "required_before": "catalog_regeneration",
                "complete_when": (
                    "guide/outfitter, geospatial, rights/publication, and hydrology "
                    "reviewers approve every record"
                ),
            },
            {
                "step_id": "regenerate_catalog_editor_and_water_window_inputs",
                "required_before": "a3_promotion",
                "complete_when": (
                    "named rapid catalog, editor geometry, flow bands, and water-window "
                    "inputs are regenerated from the reviewed result"
                ),
            },
        ],
        "promotion_gate": {
            "can_replace_order_interpolation": False,
            "can_regenerate_named_rapid_catalog": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a3": False,
        },
    }


def write_pacuare_a3_digitizing_action_packet(repo_root: Path) -> Path:
    payload = build_pacuare_a3_digitizing_action_packet(repo_root)
    path = repo_root / PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_pacuare_a3_digitizing_result_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty result template for reviewed Pacuare A3 stationing."""

    packet = build_pacuare_a3_digitizing_action_packet(repo_root)
    return {
        "schema": PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": "empty_digitizing_result_template_no_stationing_promotion",
        "production_promoted": False,
        "source_action_packet": PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_status_artifact": PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
        "rapid_count": packet["rapid_count"],
        "allowed_geometry_types": list(_ALLOWED_GEOMETRY_TYPES),
        "allowed_stationing_kinds": list(_ALLOWED_STATIONING_KINDS),
        "allowed_flow_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "stationing_result_records": [
            _empty_result_record(action) for action in packet["digitizing_actions"]
        ],
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
            "every_catalog_rapid_must_have_result": True,
            "geometry_must_be_point_or_span": True,
            "station_m_must_be_on_reviewed_route": True,
            "stationing_kind_must_not_be_provisional_order_interpolation": True,
            "source_evidence_and_guide_evidence_required": True,
            "rights_protected_area_and_flow_source_class_required": True,
            "all_reviewer_roles_must_approve": True,
            "may_promote_from_empty_template": False,
            "may_bind_solver_windows_from_template": False,
        },
        "promotion_gate": {
            "can_replace_order_interpolation": False,
            "can_regenerate_named_rapid_catalog": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a3": False,
        },
    }


def write_pacuare_a3_digitizing_result_template(repo_root: Path) -> Path:
    payload = build_pacuare_a3_digitizing_result_template(repo_root)
    path = repo_root / PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_pacuare_a3_digitizing_validation_report(
    repo_root: Path,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a Pacuare digitizing result without promoting geometry."""

    packet = build_pacuare_a3_digitizing_action_packet(repo_root)
    payload = (
        result_payload
        if result_payload is not None
        else build_pacuare_a3_digitizing_result_template(repo_root)
    )
    records = payload["stationing_result_records"]
    expected_names = [action["rapid_name"] for action in packet["digitizing_actions"]]
    errors = _rapid_set_errors(records, expected_names)
    for record in records:
        errors.extend(_record_errors(record))
    reviewer_failures = _reviewer_failures(payload["reviewer_signoff"])
    digitizing_valid = not errors and not reviewer_failures
    return {
        "schema": PACUARE_A3_DIGITIZING_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": (
            "digitizing_result_valid_manual_catalog_regeneration_allowed"
            if digitizing_valid
            else "digitizing_result_incomplete_stationing_promotion_blocked"
        ),
        "production_promoted": False,
        "source_action_packet": PACUARE_A3_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_result_template": PACUARE_A3_DIGITIZING_RESULT_TEMPLATE_RELATIVE_PATH,
        "source_status_artifact": PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
        "digitizing_valid": digitizing_valid,
        "validation_error_count": len(errors) + len(reviewer_failures),
        "rapid_count": len(records),
        "passing_rapid_count": sum(1 for record in records if not _record_errors(record)),
        "errors": errors,
        "reviewer_failures": [
            {"role": role, "reason": reason} for role, reason in reviewer_failures
        ],
        "promotion_permissions": {
            "can_replace_order_interpolation": digitizing_valid,
            "can_regenerate_named_rapid_catalog": digitizing_valid,
            "can_regenerate_editor_geometry": digitizing_valid,
            "can_generate_rapid_water_windows": digitizing_valid,
            "can_bind_solver_windows": False,
            "can_promote_a3_from_validation_report_alone": False,
            "manual_review_still_required_after_valid_result": True,
        },
        "promotion_gate": {
            "can_promote_current_preview_route": False,
            "can_import_unreal_route_from_empty_or_invalid_result": False,
            "can_bind_solver_windows_from_digitizing_result_alone": False,
            "next_after_valid_result": [
                "regenerate_named_rapid_source_catalog",
                "regenerate_named_rapid_editor_markers",
                "generate_pacuare_rapid_water_window_inputs",
                "run_guide_geospatial_rights_and_flow_review",
            ],
        },
    }


def write_pacuare_a3_digitizing_validation_report(repo_root: Path) -> Path:
    payload = build_pacuare_a3_digitizing_validation_report(repo_root)
    path = repo_root / PACUARE_A3_DIGITIZING_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _digitizing_action(record: dict[str, Any]) -> dict[str, Any]:
    action_id = f"pacuare_a3_digitize_{int(record['order']):02d}_{_slug(record['name'])}"
    return {
        "action_id": action_id,
        "rapid_name": record["name"],
        "aliases": record["aliases"],
        "order": record["order"],
        "class": record["class"],
        "feature_tags": record["feature_tags"],
        "review_priority": record["review_priority"],
        "current_station_m_from_order_interpolation": record[
            "station_m_from_order_interpolation"
        ],
        "current_stationing_kind": record["stationing_kind"],
        "required_output_geometry": list(_ALLOWED_GEOMETRY_TYPES),
        "required_stationing_kinds": list(_ALLOWED_STATIONING_KINDS),
        "required_source_classes": [
            "reviewed_route_centerline",
            "accepted_aerial_or_orthomosaic",
            "rapid_feature_digitizer",
            "guide_or_outfitter_confirmation",
            "rights_and_protected_area_publication_review",
            "flow_band_source_class",
        ],
        "blocks_until_complete": [
            "named_rapid_catalog_restationing",
            "editor_geometry_binding",
            "rapid_water_window_generation",
            "solver_window_binding",
            "a3_promotion",
        ],
    }


def _empty_result_record(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "rapid_name": action["rapid_name"],
        "aliases": action["aliases"],
        "order": action["order"],
        "geometry_type": "",
        "geometry_coordinates_wgs84": [],
        "station_m_on_reviewed_route": None,
        "stationing_kind": "not_recorded",
        "reviewed_route_source": "",
        "aerial_or_orthomosaic_source": "",
        "digitized_by": "",
        "digitized_on": "",
        "confidence_m": None,
        "guide_reviewer": "",
        "guide_reviewed_on": "",
        "rights_publication_status": "",
        "protected_area_publication_status": "",
        "flow_band_source_class": "",
        "source_evidence": [],
        "guide_evidence": [],
        "stationing_promoted": False,
        "editor_binding_enabled": False,
        "solver_window_enabled": False,
        "notes": "",
    }


def _rapid_set_errors(
    records: list[dict[str, Any]],
    expected_names: list[str],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    names = [record["rapid_name"] for record in records]
    for name in sorted(set(expected_names) - set(names)):
        errors.append(
            {"rapid_name": name, "field": "stationing_result_records", "reason": "rapid_result_missing"}
        )
    for name in sorted(set(names) - set(expected_names)):
        errors.append(
            {"rapid_name": name, "field": "stationing_result_records", "reason": "unknown_rapid_result"}
        )
    if len(names) != len(set(names)):
        errors.append(
            {"rapid_name": "", "field": "stationing_result_records", "reason": "duplicate_rapid_result"}
        )
    return errors


def _record_errors(record: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    rapid_name = record["rapid_name"]
    if record["geometry_type"] not in _ALLOWED_GEOMETRY_TYPES:
        errors.append(_error(rapid_name, "geometry_type", "geometry_type_not_allowed_or_missing"))
    elif not _geometry_coordinates_valid(
        record["geometry_type"], record["geometry_coordinates_wgs84"]
    ):
        errors.append(_error(rapid_name, "geometry_coordinates_wgs84", "geometry_coordinates_invalid_or_missing"))
    if record["station_m_on_reviewed_route"] is None:
        errors.append(_error(rapid_name, "station_m_on_reviewed_route", "station_m_missing"))
    elif float(record["station_m_on_reviewed_route"]) < 0.0:
        errors.append(_error(rapid_name, "station_m_on_reviewed_route", "station_m_negative"))
    if record["stationing_kind"] not in _ALLOWED_STATIONING_KINDS:
        errors.append(_error(rapid_name, "stationing_kind", "stationing_kind_not_exact_or_missing"))
    for field in (
        "reviewed_route_source",
        "aerial_or_orthomosaic_source",
        "digitized_by",
        "digitized_on",
        "guide_reviewer",
        "guide_reviewed_on",
    ):
        if not record[field]:
            errors.append(_error(rapid_name, field, "required_field_empty"))
    if record["confidence_m"] is None:
        errors.append(_error(rapid_name, "confidence_m", "confidence_m_missing"))
    elif float(record["confidence_m"]) <= 0.0 or float(record["confidence_m"]) > 75.0:
        errors.append(_error(rapid_name, "confidence_m", "confidence_m_outside_allowed_range"))
    if record["rights_publication_status"] != "approved":
        errors.append(_error(rapid_name, "rights_publication_status", "rights_publication_not_approved"))
    if record["protected_area_publication_status"] != "approved":
        errors.append(_error(rapid_name, "protected_area_publication_status", "protected_area_publication_not_approved"))
    if record["flow_band_source_class"] not in _ALLOWED_FLOW_SOURCE_CLASSES:
        errors.append(_error(rapid_name, "flow_band_source_class", "flow_source_class_missing_or_not_allowed"))
    if not record["source_evidence"]:
        errors.append(_error(rapid_name, "source_evidence", "source_evidence_missing"))
    if not record["guide_evidence"]:
        errors.append(_error(rapid_name, "guide_evidence", "guide_evidence_missing"))
    if record["stationing_promoted"]:
        errors.append(_error(rapid_name, "stationing_promoted", "promotion_must_wait_for_catalog_regeneration"))
    if record["solver_window_enabled"]:
        errors.append(_error(rapid_name, "solver_window_enabled", "solver_binding_requires_later_water_validation"))
    return errors


def _reviewer_failures(
    reviewers: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for role in _REVIEW_ROLES:
        payload = reviewers.get(role)
        if payload is None:
            failures.append((role, "required_reviewer_missing"))
            continue
        if not payload["approved"]:
            failures.append((role, "review_not_approved"))
        if not payload["name_or_role"] or not payload["review_date"]:
            failures.append((role, "reviewer_identity_or_date_missing"))
        if not payload["evidence"]:
            failures.append((role, "review_evidence_missing"))
    return failures


def _geometry_coordinates_valid(geometry_type: str, coordinates: Any) -> bool:
    if geometry_type == "Point":
        return _lon_lat_pair_valid(coordinates)
    if geometry_type == "LineString":
        return (
            isinstance(coordinates, list)
            and len(coordinates) >= 2
            and all(_lon_lat_pair_valid(pair) for pair in coordinates)
        )
    return False


def _lon_lat_pair_valid(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 2:
        return False
    lon, lat = value
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return False
    return -180.0 <= float(lon) <= 180.0 and -90.0 <= float(lat) <= 90.0


def _error(rapid_name: str, field: str, reason: str) -> dict[str, str]:
    return {"rapid_name": rapid_name, "field": field, "reason": reason}


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
