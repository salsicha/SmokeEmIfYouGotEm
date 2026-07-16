import json
from pathlib import Path

from raftsim.photoreal_b2_asset_promotion_readiness import (
    B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
    B2_ASSET_PROMOTION_READINESS_SCHEMA,
    build_b2_asset_promotion_readiness_report,
)
from raftsim.photoreal_b2_import_capture_review import (
    B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
    build_b2_import_capture_review_ledger,
    build_b2_import_capture_review_validation_report,
)
from raftsim.photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_hash_report_template,
    build_b2_source_hash_validation_report,
)
from raftsim.photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_report() -> dict:
    return json.loads(
        (REPO_ROOT / B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_asset_promotion_readiness_report_is_reproducible_and_blocked():
    generated = build_b2_asset_promotion_readiness_report()
    committed = _load_report()

    assert generated == committed
    assert committed["schema"] == B2_ASSET_PROMOTION_READINESS_SCHEMA
    assert committed["status"] == (
        "b2_asset_promotion_readiness_blocked_missing_source_import_capture_review_evidence"
    )
    assert committed["production_promoted"] is False
    assert committed["global_gate_status"]["can_promote_any_b2_asset_set"] is False


def test_b2_asset_promotion_readiness_report_links_source_artifacts():
    report = build_b2_asset_promotion_readiness_report()
    artifacts = report["source_artifacts"]

    assert artifacts["source_acquisition_preflight"] == B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH
    assert artifacts["source_storage_decision"] == B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH
    assert artifacts["source_hash_report_template"] == B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH
    assert artifacts["source_hash_validation_report"] == B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH
    assert artifacts["import_capture_review_ledger"] == B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH
    assert artifacts["import_capture_review_validation_report"] == B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH


def test_b2_asset_promotion_readiness_report_matches_global_counts():
    report = build_b2_asset_promotion_readiness_report()
    preflight = build_b2_source_acquisition_preflight()
    source_validation = build_b2_source_hash_validation_report(
        build_b2_source_hash_report_template()
    )
    import_validation = build_b2_import_capture_review_validation_report(
        build_b2_import_capture_review_ledger()
    )
    summary = report["summary"]

    assert summary["river_count"] == 5
    assert summary["ready_river_count"] == 0
    assert summary["blocked_river_count"] == 5
    assert summary["selection_manifest_count"] == preflight["selection_manifest_count"]
    assert summary["source_hash_record_count"] == source_validation["summary"]["required_hash_record_count"] == 44
    assert summary["source_hash_failing_record_count"] == source_validation["failing_record_count"] == 44
    assert summary["import_review_record_count"] == import_validation["summary"]["import_review_record_count"] == 44
    assert summary["import_review_failing_record_count"] == import_validation["failing_record_count"] == 44


def test_b2_asset_promotion_readiness_report_covers_all_five_rivers():
    report = build_b2_asset_promotion_readiness_report()
    rivers = {river["river_id"]: river for river in report["rivers"]}

    assert set(rivers) == {
        "south_fork_american_chili_bar",
        "colorado_river_grand_canyon_rowing",
        "pacuare_river_costa_rica",
        "futaleufu_river_chile",
        "chilko_river_lava_canyon",
    }
    assert all(river["source_hash_record_count"] > 0 for river in rivers.values())
    assert all(river["import_review_record_count"] > 0 for river in rivers.values())
    assert all(river["promotion_ready"] is False for river in rivers.values())


def test_b2_asset_promotion_readiness_report_records_per_river_blockers():
    report = build_b2_asset_promotion_readiness_report()

    for river in report["rivers"]:
        gates = river["gate_status"]
        assert gates["selection_manifest_not_promoted"] is True
        assert gates["source_assets_downloaded"] is False
        assert gates["source_assets_imported"] is False
        assert gates["source_hash_records_valid"] is False
        assert gates["import_capture_reviews_valid"] is False
        assert gates["corridor_substitution_allowed"] is False
        assert gates["desktop_vr_performance_reviewed"] is False
        assert gates["human_ecology_guide_art_rights_hazard_reviewed"] is False
        assert set(river["blocking_reasons"]) == {
            "source_assets_not_downloaded_or_recorded",
            "source_assets_not_imported",
            "source_hash_records_have_failures",
            "import_capture_review_records_have_failures",
            "corridor_substitution_not_allowed",
            "desktop_vr_performance_review_missing",
            "human_domain_reviews_missing",
        }


def test_b2_asset_promotion_readiness_report_blocks_all_plan_b2_checkboxes():
    report = build_b2_asset_promotion_readiness_report()
    gate = report["promotion_gate"]

    assert gate["can_mark_south_fork_b2_complete"] is False
    assert gate["can_mark_colorado_b2_complete"] is False
    assert gate["can_mark_pacuare_b2_complete"] is False
    assert gate["can_mark_futaleufu_b2_complete"] is False
    assert gate["can_mark_chilko_b2_complete"] is False
    assert gate["can_run_corridor_substitution"] is False
