"""Build Futaleufu A4 flow-source review packets and validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .futaleufu_a4_status import (
    FUTALEUFU_A4_STATUS_RELATIVE_PATH,
    FUTALEUFU_RIVER_ID,
    FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH,
    build_futaleufu_a4_stationing_flow_status,
)


FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/review/"
    "a4_flow_source_review_packet.json"
)
FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/review/"
    "a4_flow_source_result_template.json"
)
FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/review/"
    "a4_flow_source_validation_report.json"
)
FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_SCHEMA = (
    "raftsim.futaleufu.a4_flow_source_review_packet.v1"
)
FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.futaleufu.a4_flow_source_result_template.v1"
)
FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA = (
    "raftsim.futaleufu.a4_flow_source_validation_report.v1"
)

_ALLOWED_FLOW_SOURCE_CLASSES = (
    "official_dga_station_time_series",
    "downstream_station_route_translation",
    "snowmelt_rainfall_seasonal_context",
    "guide_reviewed_flow_band",
    "unsafe_high_water_review",
    "hypothesis_pending_guide_review",
)
_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "hydrology_or_flow_reviewer",
    "futaleufu_guide_or_outfitter_reviewer",
    "geospatial_route_translation_reviewer",
    "rights_publication_reviewer",
    "gameplay_safety_reviewer",
)


def build_futaleufu_a4_flow_source_review_packet(repo_root: Path) -> dict[str, Any]:
    """Build the Futaleufu A4 DGA flow-source review packet."""

    status = build_futaleufu_a4_stationing_flow_status(repo_root)
    seasonal_flow = _load_json(repo_root / FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH)
    actions = [_flow_band_action(band, seasonal_flow) for band in seasonal_flow["planning_bands"]]
    flow_evidence = status["flow_evidence"]
    return {
        "schema": FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A4",
        "river_id": FUTALEUFU_RIVER_ID,
        "status": "flow_source_review_packet_ready_dga_ranges_review_only_no_numeric_promotion",
        "production_promoted": False,
        "source_stationing_status": FUTALEUFU_A4_STATUS_RELATIVE_PATH,
        "source_seasonal_flow_context": FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH,
        "flow_band_count": len(actions),
        "current_stationing_status": status["status"],
        "current_flow_status": {
            "provider": flow_evidence["provider"],
            "station": flow_evidence["station"],
            "station_code": flow_evidence["station_code"],
            "units": flow_evidence["units"],
            "relation_to_reach": flow_evidence["relation_to_reach"],
            "numeric_ranges_present": flow_evidence["numeric_ranges_present"],
            "numeric_flow_bands_promoted": flow_evidence["numeric_flow_bands_promoted"],
            "promotion_gate": flow_evidence["promotion_gate"],
        },
        "source_inputs": [
            {
                "source_class": "seasonal_flow_context",
                "path": FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH,
                "provider": seasonal_flow["provider"],
                "station": seasonal_flow["station"],
                "station_code": seasonal_flow["station_code"],
                "units": seasonal_flow["units"],
                "source_urls": seasonal_flow["source_urls"],
                "promotion_gate": seasonal_flow["promotion_gate"],
            }
        ],
        "flow_band_actions": actions,
        "required_workflow": [
            "acquire or record DGA time-series metadata and terms for station 10704002-1",
            "record route translation from the downstream station to the playable reach",
            "record travel-time, snowmelt, rainfall, and upstream operation assumptions",
            "record guide/outfitter hydraulic behavior review for each flow band",
            "keep unsafe high-water scenarios review-only until safety and rescue readability review passes",
            "update flow presets only after the result template validates reviewed source classes",
        ],
        "promotion_gate": {
            "can_record_flow_band_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_promote_a4": False,
        },
    }


def write_futaleufu_a4_flow_source_review_packet(repo_root: Path) -> Path:
    payload = build_futaleufu_a4_flow_source_review_packet(repo_root)
    path = repo_root / FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_futaleufu_a4_flow_source_result_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty Futaleufu A4 flow-source result template."""

    packet = build_futaleufu_a4_flow_source_review_packet(repo_root)
    return {
        "schema": FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A4",
        "river_id": FUTALEUFU_RIVER_ID,
        "status": "empty_flow_source_result_template_no_flow_promotion",
        "production_promoted": False,
        "source_review_packet": FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_seasonal_flow_context": FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH,
        "allowed_flow_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "flow_source_records": [
            _empty_flow_source_record(action) for action in packet["flow_band_actions"]
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
            "every_flow_band_must_have_source_class": True,
            "dga_station_provider_variables_units_time_zone_route_translation_and_travel_time_required": True,
            "guide_review_required_for_each_band": True,
            "unsafe_band_must_remain_review_only_until_safety_review": True,
            "numeric_values_must_not_be_promoted_by_this_template": True,
            "water_visual_and_feature_forcing_tuning_must_remain_disabled": True,
        },
        "promotion_gate": {
            "can_record_flow_band_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_promote_a4": False,
        },
    }


def write_futaleufu_a4_flow_source_result_template(repo_root: Path) -> Path:
    payload = build_futaleufu_a4_flow_source_result_template(repo_root)
    path = repo_root / FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_futaleufu_a4_flow_source_validation_report(
    repo_root: Path,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate Futaleufu flow-source results without promoting numeric flow."""

    packet = build_futaleufu_a4_flow_source_review_packet(repo_root)
    payload = (
        result_payload
        if result_payload is not None
        else build_futaleufu_a4_flow_source_result_template(repo_root)
    )
    records = payload["flow_source_records"]
    expected_bands = [action["flow_band"] for action in packet["flow_band_actions"]]
    errors = _flow_band_set_errors(records, expected_bands)
    for record in records:
        errors.extend(_flow_source_record_errors(record))
    reviewer_failures = _reviewer_failures(payload["reviewer_signoff"])
    valid = not errors and not reviewer_failures
    return {
        "schema": FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A4",
        "river_id": FUTALEUFU_RIVER_ID,
        "status": (
            "flow_source_result_valid_dga_source_class_update_allowed"
            if valid
            else "flow_source_result_incomplete_flow_promotion_blocked"
        ),
        "production_promoted": False,
        "source_review_packet": FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_result_template": FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH,
        "flow_source_valid": valid,
        "validation_error_count": len(errors) + len(reviewer_failures),
        "flow_band_count": len(records),
        "passing_flow_band_count": sum(
            1 for record in records if not _flow_source_record_errors(record)
        ),
        "errors": errors,
        "reviewer_failures": [
            {"role": role, "reason": reason} for role, reason in reviewer_failures
        ],
        "promotion_permissions": {
            "can_record_flow_band_source_classes": valid,
            "can_update_flow_presets_source_class_labels": valid,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_promote_a4_from_validation_report_alone": False,
        },
        "promotion_gate": {
            "can_replace_current_dga_planning_ranges": False,
            "can_make_unsafe_high_water_playable": False,
            "can_bind_solver_windows_from_flow_sources": False,
            "next_after_valid_result": [
                "regenerate_futaleufu_flow_presets_with_source_class_labels",
                "pair reviewed flow classes with exact rapid stationing",
                "author flow-specific rapid water-window inputs",
                "run guide and safety review before numeric tuning or visuals",
            ],
        },
    }


def write_futaleufu_a4_flow_source_validation_report(repo_root: Path) -> Path:
    payload = build_futaleufu_a4_flow_source_validation_report(repo_root)
    path = repo_root / FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _flow_band_action(band: dict[str, Any], seasonal_flow: dict[str, Any]) -> dict[str, Any]:
    flow_band = band["id"]
    required = [
        "source_class",
        "dga_station_code",
        "provider",
        "variables",
        "units",
        "time_zone",
        "temporal_resolution",
        "route_translation_method",
        "travel_time_assumption",
        "reach_relation",
        "guide_reviewed_behavior",
        "rights_terms_status",
    ]
    if flow_band == "unsafe_review_only":
        required.append("safety_status")
    return {
        "flow_band": flow_band,
        "review_range_m3_s": band["range_m3_s"],
        "provider": seasonal_flow["provider"],
        "station": seasonal_flow["station"],
        "station_code": seasonal_flow["station_code"],
        "relation_to_reach": seasonal_flow["relation_to_reach"],
        "allowed_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "required_result_fields": required,
        "numeric_values_allowed_now": False,
        "water_visual_tuning_allowed_now": False,
        "feature_forcing_tuning_allowed_now": False,
    }


def _empty_flow_source_record(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "flow_band": action["flow_band"],
        "source_class": "",
        "dga_station_code": "",
        "provider": "",
        "source_url_or_report": "",
        "reviewed_on": "",
        "variables": [],
        "units": "",
        "time_zone": "",
        "temporal_resolution": "",
        "record_start_end": "",
        "route_translation_method": "",
        "travel_time_assumption": "",
        "reach_relation": "",
        "date_or_season_window": "",
        "band_threshold_description": "",
        "guide_reviewed_behavior": "",
        "guide_reviewer": "",
        "guide_reviewed_on": "",
        "rights_terms_status": "",
        "safety_status": "not_applicable",
        "source_evidence": [],
        "guide_evidence": [],
        "numeric_values_promoted": False,
        "water_visual_tuning_allowed": False,
        "feature_forcing_tuning_allowed": False,
        "notes": "",
    }


def _flow_band_set_errors(
    records: list[dict[str, Any]],
    expected_bands: list[str],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    bands = [record["flow_band"] for record in records]
    for band in sorted(set(expected_bands) - set(bands)):
        errors.append(_error(band, "flow_source_records", "flow_band_record_missing"))
    for band in sorted(set(bands) - set(expected_bands)):
        errors.append(_error(band, "flow_source_records", "unknown_flow_band_record"))
    if len(bands) != len(set(bands)):
        errors.append(_error("", "flow_source_records", "duplicate_flow_band_record"))
    return errors


def _flow_source_record_errors(record: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    band = record["flow_band"]
    if record["source_class"] not in _ALLOWED_FLOW_SOURCE_CLASSES:
        errors.append(_error(band, "source_class", "source_class_missing_or_not_allowed"))
    for field in (
        "dga_station_code",
        "provider",
        "source_url_or_report",
        "reviewed_on",
        "units",
        "time_zone",
        "temporal_resolution",
        "record_start_end",
        "route_translation_method",
        "travel_time_assumption",
        "reach_relation",
        "date_or_season_window",
        "band_threshold_description",
        "guide_reviewed_behavior",
        "guide_reviewer",
        "guide_reviewed_on",
    ):
        if not record[field]:
            errors.append(_error(band, field, "required_field_empty"))
    if not record["variables"]:
        errors.append(_error(band, "variables", "variables_missing"))
    if record["rights_terms_status"] != "approved_for_project_use":
        errors.append(_error(band, "rights_terms_status", "rights_terms_not_approved"))
    if not record["source_evidence"]:
        errors.append(_error(band, "source_evidence", "source_evidence_missing"))
    if not record["guide_evidence"]:
        errors.append(_error(band, "guide_evidence", "guide_evidence_missing"))
    if band == "unsafe_review_only" and record["safety_status"] != (
        "review_only_not_playable"
    ):
        errors.append(_error(band, "safety_status", "unsafe_safety_status_not_review_only"))
    if record["numeric_values_promoted"]:
        errors.append(_error(band, "numeric_values_promoted", "numeric_values_require_later_calibration"))
    if record["water_visual_tuning_allowed"]:
        errors.append(_error(band, "water_visual_tuning_allowed", "water_visual_tuning_requires_later_review"))
    if record["feature_forcing_tuning_allowed"]:
        errors.append(_error(band, "feature_forcing_tuning_allowed", "feature_forcing_requires_later_review"))
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


def _error(flow_band: str, field: str, reason: str) -> dict[str, str]:
    return {"flow_band": flow_band, "field": field, "reason": reason}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
