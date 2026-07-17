"""Build Chilko A5 flow-window review packets and validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .chilko_a5_digitizing import (
    CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
    build_chilko_a5_digitizing_action_packet,
)


CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_bc/review/"
    "a5_flow_source_review_packet.json"
)
CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_bc/review/"
    "a5_flow_source_result_template.json"
)
CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/chilko_river_bc/review/"
    "a5_flow_source_validation_report.json"
)
CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_SCHEMA = (
    "raftsim.chilko.a5_flow_source_review_packet.v1"
)
CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.chilko.a5_flow_source_result_template.v1"
)
CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA = (
    "raftsim.chilko.a5_flow_source_validation_report.v1"
)

_ALLOWED_FLOW_SOURCE_CLASSES = (
    "eccc_08ma002_daily_time_series",
    "eccc_08ma002_to_put_in_route_translation",
    "eccc_08ma001_downstream_context_check",
    "guide_reviewed_flow_band",
    "unsafe_high_water_or_washout_review",
    "hypothesis_pending_guide_review",
)
_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "hydrology_or_flow_reviewer",
    "chilko_guide_or_outfitter_reviewer",
    "geospatial_route_translation_reviewer",
    "rights_land_publication_reviewer",
    "gameplay_safety_reviewer",
)
_FLOW_WINDOW_SPECS = (
    {
        "flow_window": "low_technical_review",
        "display_name": "Low technical review window",
        "review_priority": "high",
        "reference_months": [10, 11, 12, 1, 2, 3, 4, 5],
        "expected_gameplay_behavior": (
            "shallower shelves, more exposed boulder contact, less sticky holes, and tighter rescue margins"
        ),
    },
    {
        "flow_window": "reference_summer_runnable_review",
        "display_name": "Reference summer runnable review window",
        "review_priority": "critical",
        "reference_months": [6, 7, 8, 9],
        "expected_gameplay_behavior": (
            "continuous cold big-water run with wave trains, laterals, strong eddy lines, and limited recovery"
        ),
    },
    {
        "flow_window": "high_big_water_review",
        "display_name": "High big-water review window",
        "review_priority": "critical",
        "reference_months": [6, 7, 8],
        "expected_gameplay_behavior": (
            "larger standing waves, stronger laterals, stickier holes at selected stages, and faster swimmer drift"
        ),
    },
    {
        "flow_window": "unsafe_or_washout_review_only",
        "display_name": "Unsafe or washout review-only window",
        "review_priority": "critical",
        "reference_months": [6, 7, 8],
        "expected_gameplay_behavior": (
            "some holes may wash out while hydraulics, pins, flips, swimmer separation, and recovery consequences intensify"
        ),
    },
)


def build_chilko_a5_flow_source_review_packet(repo_root: Path) -> dict[str, Any]:
    """Build the Chilko A5 08MA002/08MA001 flow-window review packet."""

    digitizing_packet = build_chilko_a5_digitizing_action_packet(repo_root)
    seasonal_flow_path = digitizing_packet["source_inputs"]["seasonal_flow_context"]
    seasonal_flow = _load_json(repo_root / seasonal_flow_path)
    stations = {station["station_number"]: station for station in seasonal_flow["stations"]}
    primary = stations["08MA002"]
    downstream = stations["08MA001"]
    actions = [
        _flow_window_action(spec, primary, downstream) for spec in _FLOW_WINDOW_SPECS
    ]
    return {
        "schema": CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A5",
        "river_id": digitizing_packet["river_id"],
        "display_name": digitizing_packet["display_name"],
        "status": "flow_source_review_packet_ready_08ma002_08ma001_review_only_no_numeric_promotion",
        "production_promoted": False,
        "source_digitizing_action_packet": CHILKO_A5_DIGITIZING_ACTION_PACKET_RELATIVE_PATH,
        "source_seasonal_flow_context": seasonal_flow_path,
        "flow_window_count": len(actions),
        "current_stationing_status": digitizing_packet["status"],
        "current_flow_status": {
            "provider": "Environment and Climate Change Canada Water Survey of Canada",
            "primary_station": _station_summary(primary),
            "downstream_context_station": _station_summary(downstream),
            "units": seasonal_flow["units"],
            "gameplay_flow_band_status": seasonal_flow["gameplay_flow_bands"]["status"],
            "numeric_thresholds_present": bool(
                seasonal_flow["gameplay_flow_bands"]["numeric_thresholds"]
            ),
            "numeric_flow_bands_promoted": False,
            "required_before_authoring": seasonal_flow["gameplay_flow_bands"][
                "required_before_authoring"
            ],
        },
        "source_inputs": [
            _source_station_input("primary_upstream_station", primary),
            _source_station_input("downstream_context_station", downstream),
        ],
        "flow_window_actions": actions,
        "required_workflow": [
            "attach daily or event-window 08MA002 discharge records for target run dates",
            "estimate lag, tributary change, and route translation from 08MA002 to the Chilko River Lodge put-in",
            "compare against 08MA001 downstream context while separating Taseko confluence influence",
            "record guide/outfitter hydraulic behavior review for each flow window and priority rapid",
            "keep unsafe or washout scenarios review-only until safety, rescue, and hazard-readability review passes",
            "pair reviewed flow windows with exact rapid stationing before authoring water windows or solver scenarios",
        ],
        "promotion_gate": {
            "can_record_flow_window_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a5": False,
        },
    }


def write_chilko_a5_flow_source_review_packet(repo_root: Path) -> Path:
    payload = build_chilko_a5_flow_source_review_packet(repo_root)
    path = repo_root / CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_chilko_a5_flow_source_result_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty Chilko A5 flow-source result template."""

    packet = build_chilko_a5_flow_source_review_packet(repo_root)
    return {
        "schema": CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A5",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": "empty_flow_source_result_template_no_flow_promotion",
        "production_promoted": False,
        "source_review_packet": CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_seasonal_flow_context": packet["source_seasonal_flow_context"],
        "allowed_flow_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "flow_window_records": [
            _empty_flow_window_record(action) for action in packet["flow_window_actions"]
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
            "every_flow_window_must_have_source_class": True,
            "primary_and_downstream_station_numbers_required": True,
            "daily_window_route_translation_lag_tributary_and_downstream_context_required": True,
            "guide_review_required_for_each_window": True,
            "unsafe_or_washout_window_must_remain_review_only_until_safety_review": True,
            "numeric_values_must_not_be_promoted_by_this_template": True,
            "water_visual_and_feature_forcing_tuning_must_remain_disabled": True,
            "solver_windows_must_remain_disabled": True,
        },
        "promotion_gate": {
            "can_record_flow_window_source_classes": False,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a5": False,
        },
    }


def write_chilko_a5_flow_source_result_template(repo_root: Path) -> Path:
    payload = build_chilko_a5_flow_source_result_template(repo_root)
    path = repo_root / CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_chilko_a5_flow_source_validation_report(
    repo_root: Path,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate Chilko flow-window results without promoting numeric flow."""

    packet = build_chilko_a5_flow_source_review_packet(repo_root)
    payload = (
        result_payload
        if result_payload is not None
        else build_chilko_a5_flow_source_result_template(repo_root)
    )
    records = payload["flow_window_records"]
    expected_windows = [action["flow_window"] for action in packet["flow_window_actions"]]
    errors = _flow_window_set_errors(records, expected_windows)
    for record in records:
        errors.extend(_flow_window_record_errors(record))
    reviewer_failures = _reviewer_failures(payload["reviewer_signoff"])
    valid = not errors and not reviewer_failures
    return {
        "schema": CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A5",
        "river_id": packet["river_id"],
        "display_name": packet["display_name"],
        "status": (
            "flow_source_result_valid_08ma002_source_class_update_allowed"
            if valid
            else "flow_source_result_incomplete_flow_promotion_blocked"
        ),
        "production_promoted": False,
        "source_review_packet": CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
        "source_result_template": CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH,
        "flow_source_valid": valid,
        "validation_error_count": len(errors) + len(reviewer_failures),
        "flow_window_count": len(records),
        "passing_flow_window_count": sum(
            1 for record in records if not _flow_window_record_errors(record)
        ),
        "errors": errors,
        "reviewer_failures": [
            {"role": role, "reason": reason} for role, reason in reviewer_failures
        ],
        "promotion_permissions": {
            "can_record_flow_window_source_classes": valid,
            "can_update_flow_window_source_class_labels": valid,
            "can_enable_numeric_discharge_values": False,
            "can_tune_water_visuals": False,
            "can_tune_feature_forcing": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_promote_a5_from_validation_report_alone": False,
        },
        "promotion_gate": {
            "can_replace_current_review_only_flow_context": False,
            "can_make_unsafe_or_washout_window_playable": False,
            "can_bind_solver_windows_from_flow_sources": False,
            "next_after_valid_result": [
                "regenerate_chilko_flow_window_labels_with_source_class_evidence",
                "pair reviewed flow windows with exact rapid stationing",
                "author flow-specific rapid water-window inputs",
                "run guide, safety, and hazard-readability review before numeric tuning or visuals",
            ],
        },
    }


def write_chilko_a5_flow_source_validation_report(repo_root: Path) -> Path:
    payload = build_chilko_a5_flow_source_validation_report(repo_root)
    path = repo_root / CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _flow_window_action(
    spec: dict[str, Any],
    primary: dict[str, Any],
    downstream: dict[str, Any],
) -> dict[str, Any]:
    required = [
        "source_class",
        "primary_station_number",
        "downstream_context_station_number",
        "provider",
        "variables",
        "units",
        "time_zone",
        "temporal_resolution",
        "daily_window_selection",
        "route_translation_method",
        "lag_or_travel_time_assumption",
        "tributary_adjustment_assumption",
        "downstream_context_check",
        "reach_relation",
        "guide_reviewed_behavior",
        "feature_behavior_notes",
        "rights_terms_status",
    ]
    if spec["flow_window"] == "unsafe_or_washout_review_only":
        required.append("safety_status")
    return {
        "flow_window": spec["flow_window"],
        "display_name": spec["display_name"],
        "review_priority": spec["review_priority"],
        "reference_months": spec["reference_months"],
        "primary_station_number": primary["station_number"],
        "downstream_context_station_number": downstream["station_number"],
        "primary_station_month_summary": _month_summaries(primary, spec["reference_months"]),
        "downstream_context_month_summary": _month_summaries(
            downstream, spec["reference_months"]
        ),
        "expected_gameplay_behavior": spec["expected_gameplay_behavior"],
        "allowed_source_classes": list(_ALLOWED_FLOW_SOURCE_CLASSES),
        "required_result_fields": required,
        "numeric_values_allowed_now": False,
        "water_visual_tuning_allowed_now": False,
        "feature_forcing_tuning_allowed_now": False,
        "rapid_water_windows_allowed_now": False,
        "solver_windows_allowed_now": False,
    }


def _empty_flow_window_record(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "flow_window": action["flow_window"],
        "display_name": action["display_name"],
        "source_class": "",
        "primary_station_number": "",
        "downstream_context_station_number": "",
        "provider": "",
        "source_url_or_report": "",
        "reviewed_on": "",
        "variables": [],
        "units": "",
        "time_zone": "",
        "temporal_resolution": "",
        "record_start_end": "",
        "daily_window_selection": "",
        "route_translation_method": "",
        "lag_or_travel_time_assumption": "",
        "tributary_adjustment_assumption": "",
        "downstream_context_check": "",
        "reach_relation": "",
        "date_or_season_window": "",
        "band_threshold_description": "",
        "guide_reviewed_behavior": "",
        "feature_behavior_notes": "",
        "guide_reviewer": "",
        "guide_reviewed_on": "",
        "rights_terms_status": "",
        "safety_status": "not_applicable",
        "source_evidence": [],
        "guide_evidence": [],
        "numeric_values_promoted": False,
        "water_visual_tuning_allowed": False,
        "feature_forcing_tuning_allowed": False,
        "rapid_water_windows_allowed": False,
        "solver_window_enabled": False,
        "notes": "",
    }


def _flow_window_set_errors(
    records: list[dict[str, Any]],
    expected_windows: list[str],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    windows = [record["flow_window"] for record in records]
    for window in sorted(set(expected_windows) - set(windows)):
        errors.append(_error(window, "flow_window_records", "flow_window_record_missing"))
    for window in sorted(set(windows) - set(expected_windows)):
        errors.append(_error(window, "flow_window_records", "unknown_flow_window_record"))
    if len(windows) != len(set(windows)):
        errors.append(_error("", "flow_window_records", "duplicate_flow_window_record"))
    return errors


def _flow_window_record_errors(record: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    window = record["flow_window"]
    if record["source_class"] not in _ALLOWED_FLOW_SOURCE_CLASSES:
        errors.append(_error(window, "source_class", "source_class_missing_or_not_allowed"))
    for field in (
        "primary_station_number",
        "downstream_context_station_number",
        "provider",
        "source_url_or_report",
        "reviewed_on",
        "units",
        "time_zone",
        "temporal_resolution",
        "record_start_end",
        "daily_window_selection",
        "route_translation_method",
        "lag_or_travel_time_assumption",
        "tributary_adjustment_assumption",
        "downstream_context_check",
        "reach_relation",
        "date_or_season_window",
        "band_threshold_description",
        "guide_reviewed_behavior",
        "feature_behavior_notes",
        "guide_reviewer",
        "guide_reviewed_on",
    ):
        if not record[field]:
            errors.append(_error(window, field, "required_field_empty"))
    if record["primary_station_number"] and record["primary_station_number"] != "08MA002":
        errors.append(_error(window, "primary_station_number", "primary_station_must_be_08ma002"))
    if (
        record["downstream_context_station_number"]
        and record["downstream_context_station_number"] != "08MA001"
    ):
        errors.append(
            _error(
                window,
                "downstream_context_station_number",
                "downstream_context_station_must_be_08ma001",
            )
        )
    if not record["variables"]:
        errors.append(_error(window, "variables", "variables_missing"))
    if record["rights_terms_status"] != "approved_for_project_use":
        errors.append(_error(window, "rights_terms_status", "rights_terms_not_approved"))
    if not record["source_evidence"]:
        errors.append(_error(window, "source_evidence", "source_evidence_missing"))
    if not record["guide_evidence"]:
        errors.append(_error(window, "guide_evidence", "guide_evidence_missing"))
    if window == "unsafe_or_washout_review_only" and record["safety_status"] != (
        "review_only_not_playable"
    ):
        errors.append(
            _error(
                window,
                "safety_status",
                "unsafe_or_washout_safety_status_not_review_only",
            )
        )
    if record["numeric_values_promoted"]:
        errors.append(
            _error(window, "numeric_values_promoted", "numeric_values_require_later_calibration")
        )
    if record["water_visual_tuning_allowed"]:
        errors.append(
            _error(window, "water_visual_tuning_allowed", "water_visual_tuning_requires_later_review")
        )
    if record["feature_forcing_tuning_allowed"]:
        errors.append(
            _error(window, "feature_forcing_tuning_allowed", "feature_forcing_requires_later_review")
        )
    if record["rapid_water_windows_allowed"]:
        errors.append(
            _error(window, "rapid_water_windows_allowed", "rapid_water_windows_require_exact_stationing")
        )
    if record["solver_window_enabled"]:
        errors.append(
            _error(window, "solver_window_enabled", "solver_binding_requires_later_water_validation")
        )
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


def _source_station_input(source_class: str, station: dict[str, Any]) -> dict[str, Any]:
    history = station["monthly_history"]
    return {
        "source_class": source_class,
        "station_number": station["station_number"],
        "station_name": station["station_name"],
        "role": station["role"],
        "limitation": station["limitation"],
        "status": station["status"],
        "real_time": station["real_time"],
        "drainage_area_gross_km2": station["drainage_area_gross_km2"],
        "monthly_record_count": history["record_count"],
        "first_month": history["first_month"],
        "last_month": history["last_month"],
        "discharge_record_count": history["discharge_record_count"],
    }


def _station_summary(station: dict[str, Any]) -> dict[str, Any]:
    return {
        "station_number": station["station_number"],
        "station_name": station["station_name"],
        "role": station["role"],
        "limitation": station["limitation"],
        "status": station["status"],
        "real_time": station["real_time"],
    }


def _month_summaries(
    station: dict[str, Any],
    months: list[int],
) -> list[dict[str, Any]]:
    by_month = {
        month["month"]: month
        for month in station["monthly_history"]["calendar_month_climatology"]
    }
    return [
        {
            "month": month,
            "sample_count": by_month[month]["sample_count"],
            "median_m3_s": by_month[month]["median_m3_s"],
            "p10_m3_s": by_month[month]["p10_m3_s"],
            "p90_m3_s": by_month[month]["p90_m3_s"],
        }
        for month in months
    ]


def _error(flow_window: str, field: str, reason: str) -> dict[str, str]:
    return {"flow_window": flow_window, "field": field, "reason": reason}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
