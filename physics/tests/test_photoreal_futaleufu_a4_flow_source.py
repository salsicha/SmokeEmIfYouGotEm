import json
from pathlib import Path

from raftsim.examples.validate_futaleufu_a4_flow_source_result import (
    main as validate_futaleufu_a4_flow_source_result_main,
)
from raftsim.futaleufu_a4_flow_source import (
    FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH,
    FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA,
    FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH,
    FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_SCHEMA,
    FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH,
    FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA,
    build_futaleufu_a4_flow_source_result_template,
    build_futaleufu_a4_flow_source_review_packet,
    build_futaleufu_a4_flow_source_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_packet() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_futaleufu_a4_flow_source_packet_is_reproducible_and_blocked():
    generated = build_futaleufu_a4_flow_source_review_packet(REPO_ROOT)
    committed = _load_packet()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_SCHEMA
    assert committed["status"] == (
        "flow_source_review_packet_ready_dga_ranges_review_only_no_numeric_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["flow_band_count"] == 4
    assert committed["current_flow_status"]["station_code"] == "10704002-1"
    assert committed["current_flow_status"]["numeric_ranges_present"] is True
    assert committed["current_flow_status"]["numeric_flow_bands_promoted"] is False
    gate = committed["promotion_gate"]
    assert gate["can_record_flow_band_source_classes"] is False
    assert gate["can_enable_numeric_discharge_values"] is False
    assert gate["can_tune_water_visuals"] is False
    assert gate["can_tune_feature_forcing"] is False


def test_futaleufu_a4_flow_source_packet_covers_dga_bands_and_inputs():
    packet = _load_packet()
    actions = {action["flow_band"]: action for action in packet["flow_band_actions"]}
    source_inputs = {source["source_class"]: source for source in packet["source_inputs"]}

    assert set(actions) == {
        "low_technical",
        "normal_runnable",
        "high_big_water",
        "unsafe_review_only",
    }
    assert actions["low_technical"]["review_range_m3_s"] == [60.0, 160.0]
    assert actions["normal_runnable"]["review_range_m3_s"] == [160.0, 300.0]
    assert actions["high_big_water"]["review_range_m3_s"] == [300.0, 500.0]
    assert actions["unsafe_review_only"]["numeric_values_allowed_now"] is False
    assert "safety_status" in actions["unsafe_review_only"]["required_result_fields"]
    assert source_inputs["seasonal_flow_context"]["provider"] == (
        "Direccion General de Aguas, Chile"
    )
    assert source_inputs["seasonal_flow_context"]["station_code"] == "10704002-1"


def test_futaleufu_a4_flow_source_template_is_reproducible_and_empty():
    generated = build_futaleufu_a4_flow_source_result_template(REPO_ROOT)
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_flow_source_result_template_no_flow_promotion"
    assert committed["production_promoted"] is False
    assert len(committed["flow_source_records"]) == 4
    first = committed["flow_source_records"][0]
    assert first["source_class"] == ""
    assert first["dga_station_code"] == ""
    assert first["variables"] == []
    assert first["numeric_values_promoted"] is False
    assert first["water_visual_tuning_allowed"] is False
    assert first["feature_forcing_tuning_allowed"] is False


def test_futaleufu_a4_flow_source_validation_blocks_empty_template():
    generated = build_futaleufu_a4_flow_source_validation_report(REPO_ROOT)
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_SCHEMA
    assert committed["status"] == "flow_source_result_incomplete_flow_promotion_blocked"
    assert committed["flow_source_valid"] is False
    assert committed["passing_flow_band_count"] == 0
    assert committed["validation_error_count"] > 75
    reasons = {error["reason"] for error in committed["errors"]}
    assert {
        "source_class_missing_or_not_allowed",
        "required_field_empty",
        "variables_missing",
        "rights_terms_not_approved",
        "source_evidence_missing",
        "guide_evidence_missing",
        "unsafe_safety_status_not_review_only",
    }.issubset(reasons)
    permissions = committed["promotion_permissions"]
    assert permissions["can_record_flow_band_source_classes"] is False
    assert permissions["can_enable_numeric_discharge_values"] is False
    assert permissions["can_tune_water_visuals"] is False
    assert permissions["can_tune_feature_forcing"] is False


def test_futaleufu_a4_flow_source_validation_accepts_reviewed_source_classes_only():
    report = build_futaleufu_a4_flow_source_validation_report(
        REPO_ROOT, _complete_flow_source_payload()
    )

    assert report["status"] == "flow_source_result_valid_dga_source_class_update_allowed"
    assert report["flow_source_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["passing_flow_band_count"] == 4
    permissions = report["promotion_permissions"]
    assert permissions["can_record_flow_band_source_classes"] is True
    assert permissions["can_update_flow_presets_source_class_labels"] is True
    assert permissions["can_enable_numeric_discharge_values"] is False
    assert permissions["can_tune_water_visuals"] is False
    assert permissions["can_tune_feature_forcing"] is False
    assert permissions["can_promote_a4_from_validation_report_alone"] is False
    assert report["promotion_gate"]["can_make_unsafe_high_water_playable"] is False


def test_futaleufu_a4_flow_source_validation_rejects_numeric_or_tuning_promotion():
    payload = _complete_flow_source_payload()
    first = payload["flow_source_records"][0]
    first["numeric_values_promoted"] = True
    first["water_visual_tuning_allowed"] = True
    first["feature_forcing_tuning_allowed"] = True
    report = build_futaleufu_a4_flow_source_validation_report(REPO_ROOT, payload)

    assert report["flow_source_valid"] is False
    assert {
        "flow_band": "low_technical",
        "field": "numeric_values_promoted",
        "reason": "numeric_values_require_later_calibration",
    } in report["errors"]
    assert {
        "flow_band": "low_technical",
        "field": "water_visual_tuning_allowed",
        "reason": "water_visual_tuning_requires_later_review",
    } in report["errors"]
    assert {
        "flow_band": "low_technical",
        "field": "feature_forcing_tuning_allowed",
        "reason": "feature_forcing_requires_later_review",
    } in report["errors"]


def test_futaleufu_a4_flow_source_cli_writes_empty_gate():
    exit_code = validate_futaleufu_a4_flow_source_result_main(
        ["--repo-root", str(REPO_ROOT)]
    )

    packet_path = REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_REVIEW_PACKET_RELATIVE_PATH
    template_path = REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_RESULT_TEMPLATE_RELATIVE_PATH
    report_path = REPO_ROOT / FUTALEUFU_A4_FLOW_SOURCE_VALIDATION_REPORT_RELATIVE_PATH
    assert exit_code == 0
    assert packet_path.exists()
    assert template_path.exists()
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["flow_source_valid"] is False
    assert report["status"] == "flow_source_result_incomplete_flow_promotion_blocked"


def test_futaleufu_a4_flow_source_cli_accepts_complete_payload(tmp_path):
    payload = _complete_flow_source_payload()
    result_path = tmp_path / "filled_futaleufu_flow_source_result.json"
    output_path = tmp_path / "accepted_futaleufu_flow_source_result.json"
    report_path = tmp_path / "futaleufu_flow_source_validation_report.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = validate_futaleufu_a4_flow_source_result_main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--result",
            str(result_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert report_path.exists()
    accepted = json.loads(output_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert accepted == payload
    assert report["flow_source_valid"] is True
    assert report["passing_flow_band_count"] == 4
    assert report["promotion_permissions"]["can_update_flow_presets_source_class_labels"] is True
    assert report["promotion_permissions"]["can_enable_numeric_discharge_values"] is False


def test_futaleufu_a4_flow_source_cli_blocks_numeric_or_tuning_promotion(tmp_path):
    payload = _complete_flow_source_payload()
    payload["flow_source_records"][0]["numeric_values_promoted"] = True
    result_path = tmp_path / "invalid_futaleufu_flow_source_result.json"
    output_path = tmp_path / "accepted_futaleufu_flow_source_result.json"
    report_path = tmp_path / "futaleufu_flow_source_validation_report.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = validate_futaleufu_a4_flow_source_result_main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--result",
            str(result_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    assert report_path.exists()
    assert not output_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["flow_source_valid"] is False
    assert {
        "flow_band": "low_technical",
        "field": "numeric_values_promoted",
        "reason": "numeric_values_require_later_calibration",
    } in report["errors"]


def _complete_flow_source_payload() -> dict:
    payload = build_futaleufu_a4_flow_source_result_template(REPO_ROOT)
    source_classes = {
        "low_technical": "official_dga_station_time_series",
        "normal_runnable": "downstream_station_route_translation",
        "high_big_water": "guide_reviewed_flow_band",
        "unsafe_review_only": "unsafe_high_water_review",
    }
    for record in payload["flow_source_records"]:
        flow_band = record["flow_band"]
        record.update(
            {
                "source_class": source_classes[flow_band],
                "dga_station_code": "10704002-1",
                "provider": "Direccion General de Aguas, Chile",
                "source_url_or_report": "hydrology/reviewed_futaleufu_flow_source.json",
                "reviewed_on": "2026-07-16",
                "variables": ["discharge_m3_s", "snowmelt_rainfall_context"],
                "units": "m3/s",
                "time_zone": "America/Santiago",
                "temporal_resolution": "reviewed DGA station time-series resolution",
                "record_start_end": "reviewed DGA record coverage",
                "route_translation_method": "reviewed downstream station to reach translation",
                "travel_time_assumption": "reviewed mainstem travel-time assumption",
                "reach_relation": "downstream mainstem station with reviewed translation",
                "date_or_season_window": "reviewed season or event window",
                "band_threshold_description": "reviewed qualitative DGA source-class threshold",
                "guide_reviewed_behavior": "reviewed hydraulic behavior and rescue implications",
                "guide_reviewer": "futaleufu guide reviewer",
                "guide_reviewed_on": "2026-07-16",
                "rights_terms_status": "approved_for_project_use",
                "safety_status": (
                    "review_only_not_playable"
                    if flow_band == "unsafe_review_only"
                    else "not_applicable"
                ),
                "source_evidence": ["hydrology/reviewed_futaleufu_flow_source.json"],
                "guide_evidence": ["review/futaleufu_flow_guide_review.json"],
                "numeric_values_promoted": False,
                "water_visual_tuning_allowed": False,
                "feature_forcing_tuning_allowed": False,
                "notes": "synthetic complete test payload",
            }
        )
    for reviewer in payload["reviewer_signoff"].values():
        reviewer.update(
            {
                "name_or_role": "reviewer",
                "review_date": "2026-07-16",
                "approved": True,
                "evidence": ["review/example_futaleufu_flow_source_evidence.json"],
                "notes": "synthetic complete test payload",
            }
        )
    return payload
