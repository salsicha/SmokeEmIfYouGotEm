import json
from pathlib import Path

from raftsim.photoreal_b2_import_capture_review import (
    build_b2_import_capture_review_validation_report,
)
from raftsim.photoreal_b2_import_capture_sidecar import (
    B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_SCHEMA,
    B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_SCHEMA,
    build_b2_import_capture_review_sidecar_merge_report,
    build_b2_import_capture_review_sidecar_template,
    merge_b2_import_capture_review_sidecar,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_merge_report() -> dict:
    return json.loads(
        (
            REPO_ROOT / B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_b2_import_capture_review_sidecar_template_is_reproducible_and_empty():
    generated = build_b2_import_capture_review_sidecar_template()
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_import_capture_review_sidecar_template_no_promotion"
    assert committed["production_promoted"] is False
    assert committed["summary"]["sidecar_record_count"] == 44
    assert committed["summary"]["filled_sidecar_record_count"] == 0
    assert committed["summary"]["candidate_capture_count"] == 0
    assert committed["summary"]["can_promote_any_b2_asset_set"] is False


def test_b2_import_capture_review_sidecar_template_covers_contract_fields():
    template = _load_template()
    contract = template["sidecar_contract"]

    assert contract["required_capture_views"] == [
        "isolated_turntable",
        "river_distance_60m",
        "river_distance_150m",
    ]
    assert contract["required_review_domains"] == [
        "rights_and_license",
        "ecology_or_guide_fit",
        "art_direction_lifelike",
        "technical_art_import_quality",
        "hazard_readability",
        "desktop_vr_performance",
    ]
    assert contract["corridor_substitution_allowed_from_sidecar"] is False
    for record in template["records"]:
        assert record["status"] == "sidecar_not_recorded"
        assert record["source_hash_record_valid"] is False
        assert len(record["captures"]) == 3
        assert len(record["reviews"]) == 6
        assert record["can_import_now"] is False
        assert record["can_promote_candidate_now"] is False


def test_b2_import_capture_review_sidecar_merge_report_is_reproducible_and_blocked():
    generated = build_b2_import_capture_review_sidecar_merge_report()
    committed = _load_merge_report()

    assert generated == committed
    assert committed["schema"] == B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_SCHEMA
    assert committed["status"] == "import_capture_review_sidecar_incomplete_promotion_blocked"
    assert committed["production_promoted"] is False
    assert committed["sidecar_record_count"] == 44
    assert committed["sidecar_error_count"] == 0
    assert committed["merged_validation"]["import_reviews_valid"] is False
    assert committed["merged_validation"]["failing_record_count"] == 44
    permissions = committed["promotion_permissions"]
    assert permissions["can_mark_any_source_reviewed"] is False
    assert permissions["can_run_corridor_substitution"] is False
    assert permissions["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_import_capture_review_sidecar_accepts_complete_review_evidence():
    payload = _complete_sidecar_payload()
    merged = merge_b2_import_capture_review_sidecar(payload)
    validation = build_b2_import_capture_review_validation_report(merged)
    report = build_b2_import_capture_review_sidecar_merge_report(payload)

    assert validation["import_reviews_valid"] is True
    assert validation["summary"]["candidate_import_report_count"] == 44
    assert validation["summary"]["candidate_capture_count"] == 132
    assert validation["summary"]["approved_review_record_count"] == 44
    assert merged["summary"]["blocked_record_count"] == 0
    assert report["status"] == "import_capture_review_sidecar_valid_manual_promotion_required"
    assert report["promotion_permissions"]["can_mark_any_source_reviewed"] is True
    assert report["promotion_permissions"]["can_run_corridor_substitution"] is False
    assert report["promotion_permissions"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_import_capture_review_sidecar_rejects_candidate_promotion_flags():
    payload = _complete_sidecar_payload()
    first = payload["records"][0]
    first["can_import_now"] = True
    first["can_promote_candidate_now"] = True
    report = build_b2_import_capture_review_sidecar_merge_report(payload)

    assert report["status"] == "import_capture_review_sidecar_incomplete_promotion_blocked"
    assert report["promotion_permissions"]["can_mark_any_source_reviewed"] is False
    assert {
        "record_id": first["record_id"],
        "field": "can_import_now",
        "reason": "import_execution_is_not_granted_by_sidecar",
    } in report["sidecar_errors"]
    assert {
        "record_id": first["record_id"],
        "field": "can_promote_candidate_now",
        "reason": "candidate_promotion_requires_per_river_decision",
    } in report["sidecar_errors"]


def _complete_sidecar_payload() -> dict:
    payload = build_b2_import_capture_review_sidecar_template()
    for index, record in enumerate(payload["records"]):
        record["status"] = "reviewed_import_capture_record_complete"
        record["source_hash_record_valid"] = True
        record["import_report"].update(
            {
                "path": f"Saved/RaftSim/AssetIntake/B2/import_{index}.json",
                "sha256": "a" * 64,
                "map_check_zero_errors": True,
                "import_settings_recorded": True,
            }
        )
        for capture in record["captures"]:
            capture["capture_path"] = capture["expected_capture_path"]
            capture["sha256"] = "b" * 64
            capture["approved"] = True
        for review in record["reviews"]:
            review.update(
                {
                    "reviewer": "reviewer",
                    "review_date": "2026-07-16",
                    "approved": True,
                    "evidence": ["review/evidence.json"],
                    "notes": "synthetic complete sidecar record",
                }
            )
        record["performance_evidence"].update(
            {
                "desktop_profile": "desktop-high",
                "vr_profile": "vr-target",
                "desktop_passed": True,
                "vr_passed": True,
            }
        )
    payload["summary"]["filled_sidecar_record_count"] = payload["summary"][
        "sidecar_record_count"
    ]
    payload["summary"]["candidate_import_report_count"] = payload["summary"][
        "sidecar_record_count"
    ]
    payload["summary"]["candidate_capture_count"] = payload["summary"][
        "sidecar_record_count"
    ] * 3
    payload["summary"]["approved_review_record_count"] = payload["summary"][
        "sidecar_record_count"
    ]
    return payload
