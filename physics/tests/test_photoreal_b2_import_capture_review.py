import json
from pathlib import Path

from raftsim.photoreal_b2_import_capture_review import (
    B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_LEDGER_SCHEMA,
    B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_VALIDATION_SCHEMA,
    build_b2_import_capture_review_ledger,
    build_b2_import_capture_review_validation_report,
)
from raftsim.photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_hash_report_template,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_ledger() -> dict:
    return json.loads(
        (REPO_ROOT / B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation() -> dict:
    return json.loads(
        (REPO_ROOT / B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_import_capture_review_ledger_is_reproducible_and_blocked():
    generated = build_b2_import_capture_review_ledger()
    committed = _load_ledger()

    assert generated == committed
    assert committed["schema"] == B2_IMPORT_CAPTURE_REVIEW_LEDGER_SCHEMA
    assert committed["status"] == "empty_import_capture_review_ledger_source_hashes_missing"
    assert committed["production_promoted"] is False
    assert committed["source_hash_report_template"] == B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH
    assert committed["source_hash_validation_report"] == B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH


def test_b2_import_capture_review_ledger_covers_every_hash_record():
    ledger = build_b2_import_capture_review_ledger()
    source_template = build_b2_source_hash_report_template()
    source_ids = {
        record["record_id"]
        for group in (
            source_template["cc0_hash_records"],
            source_template["fab_local_only_hash_records"],
            source_template["first_party_recipe_hash_records"],
        )
        for record in group
    }

    assert ledger["summary"]["import_review_record_count"] == 44
    assert ledger["summary"]["blocked_record_count"] == 44
    assert {record["source_hash_record_id"] for record in ledger["records"]} == source_ids
    assert len({record["record_id"] for record in ledger["records"]}) == 44


def test_b2_import_capture_review_ledger_records_capture_and_review_contracts():
    ledger = build_b2_import_capture_review_ledger()
    contract = ledger["record_contract"]

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
    assert contract["source_hash_record_must_be_valid"] is True
    assert contract["corridor_substitution_allowed_from_ledger_alone"] is False

    for record in ledger["records"]:
        assert record["source_hash_record_valid"] is False
        assert record["can_import_now"] is False
        assert record["can_promote_candidate_now"] is False
        assert len(record["captures"]) == 3
        assert len(record["reviews"]) == 6
        assert record["import_report"]["unreal_destination_root"].startswith(
            "/Game/RaftSim/Environment/ExternalReview/B2/"
        )


def test_b2_import_capture_review_validation_is_reproducible_and_blocked():
    generated = build_b2_import_capture_review_validation_report()
    committed = _load_validation()

    assert generated == committed
    assert committed["schema"] == B2_IMPORT_CAPTURE_REVIEW_VALIDATION_SCHEMA
    assert committed["status"] == "import_capture_review_records_incomplete_promotion_blocked"
    assert committed["production_promoted"] is False
    assert committed["import_reviews_valid"] is False
    assert committed["summary"]["import_review_record_count"] == 44
    assert committed["failing_record_count"] == 44


def test_b2_import_capture_review_validation_blocks_empty_ledger():
    report = _load_validation()

    assert report["validation_error_count"] > 44
    assert report["summary"]["candidate_import_report_count"] == 0
    assert report["summary"]["candidate_capture_count"] == 0
    assert report["summary"]["approved_review_record_count"] == 0
    assert report["promotion_gate"]["can_mark_any_source_reviewed"] is False
    assert report["promotion_gate"]["can_run_corridor_substitution"] is False
    assert report["promotion_gate"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_import_capture_review_validation_accepts_complete_ledger():
    ledger = _complete_ledger()
    report = build_b2_import_capture_review_validation_report(ledger)

    assert report["status"] == "import_capture_review_records_valid_manual_promotion_required"
    assert report["import_reviews_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["failing_record_count"] == 0
    assert report["summary"]["candidate_import_report_count"] == 44
    assert report["summary"]["candidate_capture_count"] == 132
    assert report["summary"]["approved_review_record_count"] == 44
    assert report["promotion_gate"]["can_mark_any_source_reviewed"] is True
    assert report["promotion_gate"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_import_capture_review_validation_rejects_bad_hash():
    ledger = _complete_ledger()
    ledger["records"][0]["captures"][0]["sha256"] = "bad"
    report = build_b2_import_capture_review_validation_report(ledger)

    assert report["import_reviews_valid"] is False
    assert {
        "record_id": ledger["records"][0]["record_id"],
        "field": "captures.isolated_turntable.sha256",
        "reason": "invalid_sha256",
    } in report["record_errors"]


def _complete_ledger() -> dict:
    ledger = build_b2_import_capture_review_ledger()
    for index, record in enumerate(ledger["records"]):
        record["source_hash_record_valid"] = True
        record["status"] = "reviewed_import_capture_record_complete"
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
                    "notes": "synthetic complete test record",
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
    return ledger
