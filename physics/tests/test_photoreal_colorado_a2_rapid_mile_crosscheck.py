import json
from pathlib import Path

from raftsim.colorado_a2_rapid_mile_crosscheck import (
    COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_RELATIVE_PATH,
    COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_SCHEMA,
    COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_REPORT_RELATIVE_PATH,
    COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_SCHEMA,
    build_colorado_a2_rapid_mile_crosscheck_template,
    build_colorado_a2_rapid_mile_crosscheck_validation_report,
    station_from_river_mile,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (
            REPO_ROOT / COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_colorado_a2_rapid_mile_crosscheck_template_is_reproducible_and_empty():
    generated = build_colorado_a2_rapid_mile_crosscheck_template(REPO_ROOT)
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_SCHEMA
    assert committed["status"] == (
        "empty_rapid_mile_crosscheck_template_no_stationing_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 15
    assert committed["promotion_gate"]["can_restation_major_rapids"] is False
    assert committed["promotion_gate"]["can_bind_solver_windows"] is False


def test_colorado_a2_rapid_mile_crosscheck_template_covers_cataloged_rapids():
    template = _load_template()
    records = {record["rapid_name"]: record for record in template["rapid_records"]}

    assert set(records) == {
        "Badger Creek",
        "Soap Creek",
        "House Rock",
        "Georgie",
        "Unkar",
        "Hance",
        "Sockdolager",
        "Grapevine",
        "Horn Creek",
        "Granite",
        "Hermit",
        "Crystal",
        "Bedrock",
        "Upset",
        "Lava Falls",
    }
    assert records["Lava Falls"]["published_river_mile"] == 179.7
    assert records["Lava Falls"]["assigned_window_id"] == "colorado_a2_window_15"
    assert records["Lava Falls"]["unresolved_source_disagreement"] is True
    assert abs(
        records["Lava Falls"]["planning_station_m"] - station_from_river_mile(179.7)
    ) < 1.0e-3
    for record in records.values():
        assert set(record["source_checks"]) == set(template["required_source_checks"])
        assert record["reviewed_river_mile"] is None
        assert record["reviewed_station_m"] is None
        assert record["exact_stationing_promoted"] is False


def test_colorado_a2_rapid_mile_crosscheck_validation_report_is_reproducible():
    generated = build_colorado_a2_rapid_mile_crosscheck_validation_report(REPO_ROOT)
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_SCHEMA
    assert committed["status"] == (
        "rapid_mile_crosscheck_incomplete_stationing_promotion_blocked"
    )
    assert committed["crosscheck_valid"] is False
    assert committed["passing_rapid_count"] == 0
    assert committed["validation_error_count"] > 0


def test_colorado_a2_rapid_mile_crosscheck_validation_blocks_empty_template():
    report = _load_validation_report()

    reasons = {error["reason"] for error in report["errors"]}
    assert {
        "required_source_check_field_empty",
        "reviewed_mile_or_station_required",
        "source_check_evidence_missing",
        "source_check_not_approved",
        "reviewed_river_mile_missing",
        "reviewed_station_m_missing",
        "station_delta_missing",
        "source_disagreement_unresolved",
    }.issubset(reasons)
    permissions = report["promotion_permissions"]
    assert permissions["can_restation_major_rapids"] is False
    assert permissions["can_bind_editor_geometry"] is False
    assert permissions["can_generate_rapid_water_windows"] is False
    assert permissions["can_bind_solver_windows"] is False


def test_colorado_a2_rapid_mile_crosscheck_validation_accepts_complete_payload():
    report = build_colorado_a2_rapid_mile_crosscheck_validation_report(
        REPO_ROOT, _complete_crosscheck_payload()
    )

    assert report["status"] == "rapid_mile_crosscheck_valid_manual_restation_allowed"
    assert report["crosscheck_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["passing_rapid_count"] == 15
    assert report["promotion_permissions"]["can_restation_major_rapids"] is True
    assert report["promotion_permissions"]["can_generate_rapid_water_windows"] is True
    assert report["promotion_permissions"]["can_promote_from_validation_report_alone"] is False
    assert report["promotion_gate"]["can_import_unreal_full_reach_landscape"] is False


def test_colorado_a2_rapid_mile_crosscheck_validation_rejects_bad_delta():
    payload = _complete_crosscheck_payload()
    payload["rapid_records"][0]["station_delta_m"] = 200.0
    report = build_colorado_a2_rapid_mile_crosscheck_validation_report(REPO_ROOT, payload)

    assert report["crosscheck_valid"] is False
    assert {
        "rapid_name": "Badger Creek",
        "field": "station_delta_m",
        "reason": "station_delta_exceeds_tolerance",
    } in report["errors"]


def _complete_crosscheck_payload() -> dict:
    payload = build_colorado_a2_rapid_mile_crosscheck_template(REPO_ROOT)
    for record in payload["rapid_records"]:
        reviewed_mile = record["published_river_mile"]
        reviewed_station = station_from_river_mile(reviewed_mile)
        record.update(
            {
                "reviewed_river_mile": reviewed_mile,
                "reviewed_station_m": reviewed_station,
                "station_delta_m": 0.0,
                "unresolved_source_disagreement": False,
                "review_notes": "synthetic complete test payload",
            }
        )
        for check in record["source_checks"].values():
            check.update(
                {
                    "source_title_or_reviewer": "reviewed source",
                    "source_url_or_report": "review/example_rapid_mile_source.json",
                    "checked_on": "2026-07-16",
                    "reviewed_river_mile": reviewed_mile,
                    "reviewed_station_m": reviewed_station,
                    "evidence": ["review/example_rapid_mile_source.json"],
                    "approved": True,
                    "notes": "synthetic complete test payload",
                }
            )
    return payload
