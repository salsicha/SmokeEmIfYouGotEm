import json
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_REPORT_TEMPLATE_SCHEMA,
    build_b2_source_hash_report_template,
)
from raftsim.photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
    build_b2_source_storage_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_source_hash_report_template_is_reproducible_and_empty():
    generated = build_b2_source_hash_report_template()
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_HASH_REPORT_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_source_hash_report_template_no_downloads_or_promotion"
    assert committed["production_promoted"] is False
    assert committed["source_preflight"] == B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH
    assert committed["source_storage_decision"] == B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH


def test_b2_source_hash_report_template_matches_preflight_counts():
    template = build_b2_source_hash_report_template()
    preflight = build_b2_source_acquisition_preflight()
    summary = template["summary"]

    assert summary["river_count"] == preflight["river_count"] == 5
    assert summary["cc0_hash_record_count"] == preflight["cc0_download_task_count"] == 22
    assert summary["fab_local_only_hash_record_count"] == preflight["fab_local_only_slot_count"] == 16
    assert summary["first_party_recipe_hash_record_count"] == preflight["first_party_entry_count"] == 6
    assert summary["required_hash_record_count"] == 44
    assert summary["filled_hash_record_count"] == 0
    assert summary["source_file_hash_count"] == 0
    assert summary["can_promote_any_b2_asset_set"] is False


def test_b2_source_hash_report_template_tracks_current_storage_policy():
    template = build_b2_source_hash_report_template()
    storage = build_b2_source_storage_decision()
    mode = template["current_operating_mode"]

    assert mode["mode"] == storage["current_operating_mode"]["mode"]
    assert mode["downloads_allowed_now"] is False
    assert mode["source_binaries_allowed_in_repo_now"] is False
    assert mode["hash_manifests_allowed_in_repo_now"] is True
    assert mode["source_binary_policy_decision_required"] is True


def test_b2_source_hash_report_template_covers_every_preflight_record():
    template = build_b2_source_hash_report_template()
    preflight = build_b2_source_acquisition_preflight()

    assert {
        record["task_id"] for record in template["cc0_hash_records"]
    } == {task["task_id"] for task in preflight["cc0_download_tasks"]}
    assert {
        record["slot_id"] for record in template["fab_local_only_hash_records"]
    } == {slot["slot_id"] for slot in preflight["fab_local_only_slots"]}
    assert {
        record["entry_id"] for record in template["first_party_recipe_hash_records"]
    } == {entry["entry_id"] for entry in preflight["first_party_entries"]}


def test_b2_source_hash_report_template_records_are_not_promotional():
    template = build_b2_source_hash_report_template()

    for record in template["cc0_hash_records"]:
        assert record["source_files"] == []
        assert record["source_binary_committed"] is False
        assert record["hash_status"] == "not_recorded"
        assert record["can_import_from_record_now"] is False
        assert record["can_promote_candidate_now"] is False
        assert "record SHA-256 hash for every source file" in record[
            "required_before_review"
        ]

    for record in template["fab_local_only_hash_records"]:
        assert record["source_files"] == []
        assert record["source_binary_committed"] is False
        assert record["can_commit_source_binaries"] is False
        assert record["can_import_from_record_now"] is False
        assert record["can_promote_candidate_now"] is False

    for record in template["first_party_recipe_hash_records"]:
        assert record["generated_files"] == []
        assert record["source_binary_committed"] is False
        assert record["can_promote_candidate_now"] is False


def test_b2_source_hash_report_template_gate_blocks_promotion():
    template = build_b2_source_hash_report_template()
    contract = template["hash_entry_contract"]
    gate = template["promotion_gate"]

    assert contract["hash_report_may_be_committed_without_source_binary"] is True
    assert contract["source_binary_may_be_committed_from_empty_template"] is False
    assert set(contract["required_source_file_fields"]) == {
        "relative_path",
        "byte_size",
        "sha256",
        "media_type_or_extension",
        "source_bundle_role",
    }
    assert gate["can_download_from_template_alone"] is False
    assert gate["can_commit_source_binaries"] is False
    assert gate["can_run_corridor_substitution"] is False
    assert gate["can_mark_any_asset_source_reviewed"] is False
    assert gate["can_mark_any_b2_asset_set_promotion_ready"] is False
