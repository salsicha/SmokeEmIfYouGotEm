"""Build Pacuare A3 flow-source review packets and validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pacuare_a3_stationing import (
    FLOW_PRESETS_RELATIVE_PATH,
    HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH,
    PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
    PACUARE_RIVER_ID,
    build_pacuare_a3_stationing_repair_status,
)


PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_flow_source_review_packet.json"
)
PACUARE_A3_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_flow_source_result_template.json"
)
PACUARE_A3_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_flow_source_validation_report.json"
)
PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_SCHEMA = (
    "raftsim.pacuare.a3_flow_source_review_packet.v1"
)
PACUARE_A3_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.pacuare.a3_flow_source_result_template.v1"
)
PACUARE_A3_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA = (
    "raftsim.pacuare.a3_flow_source_validation_report.v1"
)

DISCHARGE_STAGE_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrology/"
    "production_import_pilot/discharge_or_stage_station_review.json"
)
RAINFALL_STATION_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrology/"
    "production_import_pilot/rainfall_station_review.json"
)
FLASH_RESPONSE_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrology/"
    "production_import_pilot/flash_response_review.json"
)
RAINFALL_CONTEXT_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrology/rainfall_context.json"
)

_ALLOWED_FLOW_SOURCE_CLASSES = (
    "official_gauge_or_stage",
    "rainfall_station_with_basin_relation",
    "operator_runnable_range",
    "seasonal_precipitation_regime",
    "flash_response_review_model",
    "hypothesis_pending_guide_review",
)
_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "hydrology_or_flow_reviewer",
    "pacuare_guide_or_outfitter_reviewer",
    "rights_publication_reviewer",
    "gameplay_safety_reviewer",
)


def build_pacuare_a3_flow_source_review_packet(repo_root: Path) -> dict[str, Any]:
    """Build the Pacuare A3 flow-source review packet."""

    flow_presets = _load_json(repo_root / FLOW_PRESETS_RELATIVE_PATH)
    gauge_search = _load_json(repo_root / HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH)
    discharge_review = _load_json(repo_root / DISCHARGE_STAGE_REVIEW_RELATIVE_PATH)
    rainfall_review = _load_json(repo_root / RAINFALL_STATION_REVIEW_RELATIVE_PATH)
    flash_review = _load_json(repo_root / FLASH_RESPONSE_REVIEW_RELATIVE_PATH)
    rainfall_context = _load_json(repo_root / RAINFALL_CONTEXT_RELATIVE_PATH)
    stationing_status = build_pacuare_a3_stationing_repair_status(repo_root)
    actions = [_flow_band_action(band) for band in flow_presets["flow_bands"]]
    return {
        "schema": PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": PACUARE_RIVER_ID,
        "status": "flow_source_review_packet_ready_no_numeric_flow_promotion",
        "production_promoted": False,
        "source_stationing_status": PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
        "source_flow_presets": FLOW_PRESETS_RELATIVE_PATH,
        "flow_band_count": len(actions),
        "current_flow_policy": flow_presets["flow_band_policy"],
        "current_flow_status": flow_presets["status"],
        "current_stationing_status": stationing_status["status"],
        "source_inputs": [
            _source_input("hydrology_gauge_search", HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH, gauge_search),
            _source_input("discharge_or_stage_station_review", DISCHARGE_STAGE_REVIEW_RELATIVE_PATH, discharge_review),
            _source_input("rainfall_station_review", RAINFALL_STATION_REVIEW_RELATIVE_PATH, rainfall_review),
            _source_input("flash_response_review", FLASH_RESPONSE_REVIEW_RELATIVE_PATH, flash_review),
            _source_input("rainfall_context", RAINFALL_CONTEXT_RELATIVE_PATH, rainfall_context),
        ],
        "flow_band_actions": actions,
        "required_workflow": [
            "select exact station/layer/source IDs and terms for each flow band",
            "record variables, units, time zone, temporal resolution, and basin relation",
            "record guide/outfitter runnable range and hydraulic behavior review per band",
            "keep flash-response scenarios review-only until safety and rescue readability review passes",
            "update flow presets only after the result template validates reviewed source classes",
        ],
        "promotion_gate": {
            "can_record_flow_band_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_promote_a3": False,
        },
    }


def write_pacuare_a3_flow_source_review_packet(repo_root: Path) -> Path:
    payload = build_pacuare_a3_flow_source_review_packet(repo_root)
    path = repo_root / PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_pacuare_a3_flow_source_result_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty Pacuare A3 flow-source result template."""

    packet = build_pacuare_a3_flow_source_review_packet(repo_root)
    return {
        "schema": PACUARE_A3_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": PACUARE_RIVER_ID,
        "status": "empty_flow_source_result_template_no_flow_promotion",
        "production_promoted": False,
        "source_review_packet": PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_flow_presets": FLOW_PRESETS_RELATIVE_PATH,
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
            "source_id_provider_variables_units_time_zone_and_basin_relation_required": True,
            "guide_review_required_for_each_band": True,
            "flash_band_must_remain_review_only_until_lag_and_safety_review": True,
            "numeric_values_must_not_be_promoted_by_this_template": True,
            "water_visual_and_feature_forcing_tuning_must_remain_disabled": True,
        },
        "promotion_gate": {
            "can_record_flow_band_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_promote_a3": False,
        },
    }


def write_pacuare_a3_flow_source_result_template(repo_root: Path) -> Path:
    payload = build_pacuare_a3_flow_source_result_template(repo_root)
    path = repo_root / PACUARE_A3_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_pacuare_a3_flow_source_validation_report(
    repo_root: Path,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate Pacuare flow-source results without promoting numeric flow."""

    packet = build_pacuare_a3_flow_source_review_packet(repo_root)
    payload = (
        result_payload
        if result_payload is not None
        else build_pacuare_a3_flow_source_result_template(repo_root)
    )
    records = payload["flow_source_records"]
    expected_bands = [action["flow_band"] for action in packet["flow_band_actions"]]
    errors = _flow_band_set_errors(records, expected_bands)
    for record in records:
        errors.extend(_flow_source_record_errors(record))
    reviewer_failures = _reviewer_failures(payload["reviewer_signoff"])
    valid = not errors and not reviewer_failures
    return {
        "schema": PACUARE_A3_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A3",
        "river_id": PACUARE_RIVER_ID,
        "status": (
            "flow_source_result_valid_source_class_update_allowed"
            if valid
            else "flow_source_result_incomplete_flow_promotion_blocked"
        ),
        "production_promoted": False,
        "source_review_packet": PACUARE_A3_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_result_template": PACUARE_A3_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH,
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
            "can_promote_a3_from_validation_report_alone": False,
        },
        "promotion_gate": {
            "can_replace_current_relative_flow_presets": False,
            "can_make_flash_response_playable": False,
            "can_bind_solver_windows_from_flow_sources": False,
            "next_after_valid_result": [
                "regenerate_pacuare_flow_presets_with_source_class_labels",
                "pair reviewed flow classes with exact rapid stationing",
                "author flow-specific rapid water-window inputs",
                "run guide and safety review before numeric tuning or visuals",
            ],
        },
    }


def write_pacuare_a3_flow_source_validation_report(repo_root: Path) -> Path:
    payload = build_pacuare_a3_flow_source_validation_report(repo_root)
    path = repo_root / PACUARE_A3_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _flow_band_action(band: dict[str, Any]) -> dict[str, Any]:
    flow_band = band["flow_band"]
    required = [
        "source_class",
        "station_or_source_id",
        "provider",
        "variables",
        "units",
        "time_zone",
        "temporal_resolution",
        "basin_relation",
        "guide_reviewed_behavior",
        "rights_terms_status",
    ]
    if flow_band == "flash_response_review_only":
        required.append("flash_safety_status")
    return {
        "flow_band": flow_band,
        "display_name": band["display_name"],
        "relative_flow": band["relative_flow"],
        "runnable": band["runnable"],
        "review_priority": band["review_priority"],
        "expected_gameplay_behavior": band["expected_gameplay_behavior"],
        "allowed_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "required_result_fields": required,
        "numeric_values_allowed_now": False,
        "water_visual_tuning_allowed_now": False,
        "feature_forcing_tuning_allowed_now": False,
    }


def _source_input(source_class: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_class": source_class,
        "path": path,
        "schema": payload["schema"],
        "status": payload["status"],
        "policy": payload.get("policy", {}),
        "promotion_blockers": payload.get("promotion_blockers", []),
    }


def _empty_flow_source_record(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "flow_band": action["flow_band"],
        "display_name": action["display_name"],
        "source_class": "",
        "station_or_source_id": "",
        "provider": "",
        "source_url_or_report": "",
        "reviewed_on": "",
        "variables": [],
        "units": "",
        "time_zone": "",
        "temporal_resolution": "",
        "record_start_end": "",
        "basin_relation": "",
        "date_or_season_window": "",
        "band_threshold_description": "",
        "guide_reviewed_behavior": "",
        "guide_reviewer": "",
        "guide_reviewed_on": "",
        "rights_terms_status": "",
        "flash_safety_status": "not_applicable",
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
        "station_or_source_id",
        "provider",
        "source_url_or_report",
        "reviewed_on",
        "units",
        "time_zone",
        "temporal_resolution",
        "record_start_end",
        "basin_relation",
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
    if band == "flash_response_review_only" and record["flash_safety_status"] != (
        "review_only_not_playable"
    ):
        errors.append(_error(band, "flash_safety_status", "flash_safety_status_not_review_only"))
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
