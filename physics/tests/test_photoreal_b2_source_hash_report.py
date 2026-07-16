import json
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_REPORT_TEMPLATE_SCHEMA,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_SCHEMA,
    build_b2_source_hash_report_template,
    build_b2_source_hash_validation_report,
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


def _load_validation_report() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH).read_text(
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


def test_b2_source_hash_validation_report_is_reproducible_and_blocked():
    generated = build_b2_source_hash_validation_report()
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_HASH_VALIDATION_REPORT_SCHEMA
    assert committed["status"] == "source_hash_records_incomplete_promotion_blocked"
    assert committed["production_promoted"] is False
    assert committed["source_hashes_valid"] is False
    assert committed["source_hash_report_template"] == B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH


def test_b2_source_hash_validation_report_blocks_empty_template():
    report = _load_validation_report()

    assert report["summary"]["required_hash_record_count"] == 44
    assert report["failing_record_count"] == 44
    assert report["source_file_hash_count"] == 0
    assert report["validation_error_count"] > report["failing_record_count"]
    assert report["promotion_gate"]["can_run_imports"] is False
    assert report["promotion_gate"]["can_mark_any_asset_source_reviewed"] is False
    assert report["promotion_gate"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_source_hash_validation_accepts_complete_local_hash_report():
    payload = _complete_hash_report_payload()
    report = build_b2_source_hash_validation_report(payload)

    assert report["status"] == "source_hash_records_valid_manual_review_required"
    assert report["source_hashes_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["failing_record_count"] == 0
    assert report["source_file_hash_count"] == 44
    assert report["promotion_gate"]["can_run_imports"] is True
    assert report["promotion_gate"]["can_mark_any_asset_source_reviewed"] is True
    assert report["promotion_gate"]["can_mark_any_b2_asset_set_promotion_ready"] is False
    assert report["promotion_gate"][
        "manual_rights_import_capture_and_performance_review_required"
    ] is True


def test_b2_source_hash_validation_rejects_invalid_sha256():
    payload = _complete_hash_report_payload()
    payload["cc0_hash_records"][0]["source_files"][0]["sha256"] = "bad"
    report = build_b2_source_hash_validation_report(payload)

    assert report["source_hashes_valid"] is False
    assert {
        "record_id": payload["cc0_hash_records"][0]["record_id"],
        "field": "source_files[0].sha256",
        "reason": "invalid_sha256",
    } in report["record_errors"]


def _complete_hash_report_payload() -> dict:
    payload = build_b2_source_hash_report_template()
    for index, record in enumerate(payload["cc0_hash_records"]):
        record["selected_resolution"] = "1k"
        record["selected_file_formats"] = ["fbx"]
        record["expected_total_byte_size"] = 1024
        record["actual_local_source_root"] = f"/reviewed/local/cc0/{index}"
        record["license_snapshot_url"] = record["asset_url"]
        record["source_files"] = [_source_file(index)]
        record["hash_status"] = "recorded"
    for index, record in enumerate(payload["fab_local_only_hash_records"], start=100):
        record["local_source_root"] = f"/reviewed/local/fab/{index}"
        record["license_snapshot_url"] = record["asset_url"]
        record["source_files"] = [_source_file(index)]
        record["hash_status"] = "recorded"
    for index, record in enumerate(payload["first_party_recipe_hash_records"], start=200):
        record["recipe_source_path"] = f"tools/generated_asset_{index}.py"
        record["tool_version"] = "test-tool-1"
        record["seed"] = str(index)
        record["generated_files"] = [_source_file(index)]
        record["hash_status"] = "recorded"
    payload["summary"]["filled_hash_record_count"] = payload["summary"][
        "required_hash_record_count"
    ]
    payload["summary"]["source_file_hash_count"] = payload["summary"][
        "required_hash_record_count"
    ]
    return payload


def _source_file(index: int) -> dict:
    return {
        "relative_path": f"source_{index}.bin",
        "byte_size": 1024 + index,
        "sha256": "a" * 64,
        "media_type_or_extension": ".bin",
        "source_bundle_role": "source",
    }
