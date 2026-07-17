import json
from pathlib import Path

from raftsim.chilko_a5_flow_source import (
    CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH,
    CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA,
    CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
    CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_SCHEMA,
    CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH,
    CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA,
    build_chilko_a5_flow_source_result_template,
    build_chilko_a5_flow_source_review_packet,
    build_chilko_a5_flow_source_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_packet() -> dict:
    return json.loads(
        (REPO_ROOT / CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (REPO_ROOT / CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_chilko_a5_flow_source_packet_is_reproducible_and_blocked():
    generated = build_chilko_a5_flow_source_review_packet(REPO_ROOT)
    committed = _load_packet()

    assert generated == committed
    assert committed["schema"] == CHILKO_A5_FLOW_SOURCE_REVIEW_PACKET_SCHEMA
    assert committed["status"] == (
        "flow_source_review_packet_ready_08ma002_08ma001_review_only_no_numeric_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["flow_window_count"] == 4
    current = committed["current_flow_status"]
    assert current["primary_station"]["station_number"] == "08MA002"
    assert current["downstream_context_station"]["station_number"] == "08MA001"
    assert current["numeric_thresholds_present"] is False
    assert current["numeric_flow_bands_promoted"] is False
    gate = committed["promotion_gate"]
    assert gate["can_record_flow_window_source_classes"] is False
    assert gate["can_enable_numeric_discharge_values"] is False
    assert gate["can_tune_water_visuals"] is False
    assert gate["can_tune_feature_forcing"] is False
    assert gate["can_bind_solver_windows"] is False


def test_chilko_a5_flow_source_packet_covers_windows_and_station_inputs():
    packet = _load_packet()
    actions = {action["flow_window"]: action for action in packet["flow_window_actions"]}
    source_inputs = {source["source_class"]: source for source in packet["source_inputs"]}

    assert set(actions) == {
        "low_technical_review",
        "reference_summer_runnable_review",
        "high_big_water_review",
        "unsafe_or_washout_review_only",
    }
    reference = actions["reference_summer_runnable_review"]
    assert reference["primary_station_number"] == "08MA002"
    assert reference["downstream_context_station_number"] == "08MA001"
    assert reference["reference_months"] == [6, 7, 8, 9]
    assert reference["numeric_values_allowed_now"] is False
    assert reference["solver_windows_allowed_now"] is False
    assert "safety_status" in actions["unsafe_or_washout_review_only"]["required_result_fields"]
    assert source_inputs["primary_upstream_station"]["station_number"] == "08MA002"
    assert source_inputs["primary_upstream_station"]["monthly_record_count"] == 1068
    assert source_inputs["downstream_context_station"]["station_number"] == "08MA001"


def test_chilko_a5_flow_source_template_is_reproducible_and_empty():
    generated = build_chilko_a5_flow_source_result_template(REPO_ROOT)
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == CHILKO_A5_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_flow_source_result_template_no_flow_promotion"
    assert committed["production_promoted"] is False
    assert len(committed["flow_window_records"]) == 4
    first = committed["flow_window_records"][0]
    assert first["source_class"] == ""
    assert first["primary_station_number"] == ""
    assert first["downstream_context_station_number"] == ""
    assert first["variables"] == []
    assert first["numeric_values_promoted"] is False
    assert first["water_visual_tuning_allowed"] is False
    assert first["feature_forcing_tuning_allowed"] is False
    assert first["rapid_water_windows_allowed"] is False
    assert first["solver_window_enabled"] is False


def test_chilko_a5_flow_source_validation_blocks_empty_template():
    generated = build_chilko_a5_flow_source_validation_report(REPO_ROOT)
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == CHILKO_A5_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA
    assert committed["status"] == "flow_source_result_incomplete_flow_promotion_blocked"
    assert committed["flow_source_valid"] is False
    assert committed["passing_flow_window_count"] == 0
    assert committed["validation_error_count"] > 95
    reasons = {error["reason"] for error in committed["errors"]}
    assert {
        "source_class_missing_or_not_allowed",
        "required_field_empty",
        "variables_missing",
        "rights_terms_not_approved",
        "source_evidence_missing",
        "guide_evidence_missing",
        "unsafe_or_washout_safety_status_not_review_only",
    }.issubset(reasons)
    permissions = committed["promotion_permissions"]
    assert permissions["can_record_flow_window_source_classes"] is False
    assert permissions["can_enable_numeric_discharge_values"] is False
    assert permissions["can_tune_water_visuals"] is False
    assert permissions["can_tune_feature_forcing"] is False
    assert permissions["can_generate_rapid_water_windows"] is False
    assert permissions["can_bind_solver_windows"] is False


def test_chilko_a5_flow_source_validation_accepts_reviewed_source_classes_only():
    report = build_chilko_a5_flow_source_validation_report(
        REPO_ROOT, _complete_flow_source_payload()
    )

    assert report["status"] == "flow_source_result_valid_08ma002_source_class_update_allowed"
    assert report["flow_source_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["passing_flow_window_count"] == 4
    permissions = report["promotion_permissions"]
    assert permissions["can_record_flow_window_source_classes"] is True
    assert permissions["can_update_flow_window_source_class_labels"] is True
    assert permissions["can_enable_numeric_discharge_values"] is False
    assert permissions["can_tune_water_visuals"] is False
    assert permissions["can_tune_feature_forcing"] is False
    assert permissions["can_generate_rapid_water_windows"] is False
    assert permissions["can_bind_solver_windows"] is False
    assert permissions["can_promote_a5_from_validation_report_alone"] is False
    assert report["promotion_gate"]["can_make_unsafe_or_washout_window_playable"] is False


def test_chilko_a5_flow_source_validation_rejects_numeric_tuning_or_solver_promotion():
    payload = _complete_flow_source_payload()
    first = payload["flow_window_records"][0]
    first["numeric_values_promoted"] = True
    first["water_visual_tuning_allowed"] = True
    first["feature_forcing_tuning_allowed"] = True
    first["rapid_water_windows_allowed"] = True
    first["solver_window_enabled"] = True
    first["primary_station_number"] = "08MA001"
    report = build_chilko_a5_flow_source_validation_report(REPO_ROOT, payload)

    assert report["flow_source_valid"] is False
    assert {
        "flow_window": "low_technical_review",
        "field": "numeric_values_promoted",
        "reason": "numeric_values_require_later_calibration",
    } in report["errors"]
    assert {
        "flow_window": "low_technical_review",
        "field": "water_visual_tuning_allowed",
        "reason": "water_visual_tuning_requires_later_review",
    } in report["errors"]
    assert {
        "flow_window": "low_technical_review",
        "field": "feature_forcing_tuning_allowed",
        "reason": "feature_forcing_requires_later_review",
    } in report["errors"]
    assert {
        "flow_window": "low_technical_review",
        "field": "rapid_water_windows_allowed",
        "reason": "rapid_water_windows_require_exact_stationing",
    } in report["errors"]
    assert {
        "flow_window": "low_technical_review",
        "field": "solver_window_enabled",
        "reason": "solver_binding_requires_later_water_validation",
    } in report["errors"]
    assert {
        "flow_window": "low_technical_review",
        "field": "primary_station_number",
        "reason": "primary_station_must_be_08ma002",
    } in report["errors"]


def _complete_flow_source_payload() -> dict:
    payload = build_chilko_a5_flow_source_result_template(REPO_ROOT)
    source_classes = {
        "low_technical_review": "eccc_08ma002_daily_time_series",
        "reference_summer_runnable_review": "eccc_08ma002_to_put_in_route_translation",
        "high_big_water_review": "guide_reviewed_flow_band",
        "unsafe_or_washout_review_only": "unsafe_high_water_or_washout_review",
    }
    for record in payload["flow_window_records"]:
        flow_window = record["flow_window"]
        record.update(
            {
                "source_class": source_classes[flow_window],
                "primary_station_number": "08MA002",
                "downstream_context_station_number": "08MA001",
                "provider": "Environment and Climate Change Canada Water Survey of Canada",
                "source_url_or_report": "hydrology/reviewed_chilko_flow_source.json",
                "reviewed_on": "2026-07-16",
                "variables": ["daily_discharge_m3_s", "downstream_context_discharge_m3_s"],
                "units": "m3/s",
                "time_zone": "America/Vancouver",
                "temporal_resolution": "reviewed daily or event-window record",
                "record_start_end": "reviewed ECCC record coverage",
                "daily_window_selection": "reviewed target date window selection",
                "route_translation_method": "reviewed 08MA002 to put-in routing method",
                "lag_or_travel_time_assumption": "reviewed outlet-to-put-in lag assumption",
                "tributary_adjustment_assumption": "reviewed tributary and lake-outlet adjustment",
                "downstream_context_check": "reviewed 08MA001 context with Taseko influence separated",
                "reach_relation": "primary upstream station routed to Chilko River Lodge run",
                "date_or_season_window": "reviewed season or event window",
                "band_threshold_description": "reviewed qualitative source-class threshold",
                "guide_reviewed_behavior": "reviewed hydraulic behavior and rescue implications",
                "feature_behavior_notes": "reviewed holes, wave trains, laterals, pins, flips, and washout behavior",
                "guide_reviewer": "chilko guide reviewer",
                "guide_reviewed_on": "2026-07-16",
                "rights_terms_status": "approved_for_project_use",
                "safety_status": (
                    "review_only_not_playable"
                    if flow_window == "unsafe_or_washout_review_only"
                    else "not_applicable"
                ),
                "source_evidence": ["hydrology/reviewed_chilko_flow_source.json"],
                "guide_evidence": ["review/chilko_flow_guide_review.json"],
                "numeric_values_promoted": False,
                "water_visual_tuning_allowed": False,
                "feature_forcing_tuning_allowed": False,
                "rapid_water_windows_allowed": False,
                "solver_window_enabled": False,
                "notes": "synthetic complete test payload",
            }
        )
    for reviewer in payload["reviewer_signoff"].values():
        reviewer.update(
            {
                "name_or_role": "reviewer",
                "review_date": "2026-07-16",
                "approved": True,
                "evidence": ["review/example_chilko_flow_source_evidence.json"],
                "notes": "synthetic complete test payload",
            }
        )
    return payload
