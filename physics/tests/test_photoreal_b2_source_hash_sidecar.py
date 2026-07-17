import json
from pathlib import Path

from raftsim.photoreal_b2_source_hash_report import (
    build_b2_source_hash_validation_report,
)
from raftsim.photoreal_b2_source_hash_sidecar import (
    B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_RELATIVE_PATH,
    B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_SCHEMA,
    B2_SOURCE_HASH_SIDECAR_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_SIDECAR_TEMPLATE_SCHEMA,
    build_b2_source_hash_sidecar_merge_report,
    build_b2_source_hash_sidecar_template,
    merge_b2_source_hash_sidecar,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_HASH_SIDECAR_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_merge_report() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_source_hash_sidecar_template_is_reproducible_and_empty():
    generated = build_b2_source_hash_sidecar_template()
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_HASH_SIDECAR_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_source_hash_sidecar_template_no_downloads_or_promotion"
    assert committed["production_promoted"] is False
    assert committed["summary"]["sidecar_record_count"] == 44
    assert committed["summary"]["filled_sidecar_record_count"] == 0
    assert committed["summary"]["source_file_hash_count"] == 0
    assert committed["summary"]["source_binaries_committed"] is False


def test_b2_source_hash_sidecar_template_covers_all_record_kinds():
    template = _load_template()
    counts = {}
    for record in template["records"]:
        counts[record["record_kind"]] = counts.get(record["record_kind"], 0) + 1
        assert record["source_files"] == []
        assert record["source_binary_committed"] is False
        assert record["source_binary_repo_paths"] == []
        assert record["hash_status"] == "not_recorded"

    assert counts == {
        "cc0_poly_haven_source_bundle": 22,
        "fab_local_only_source_bundle": 16,
        "first_party_or_project_owned_recipe": 6,
    }
    contract = template["sidecar_contract"]
    assert contract["may_commit_sidecar_without_source_binaries"] is True
    assert contract["may_commit_third_party_source_binaries_from_sidecar"] is False


def test_b2_source_hash_sidecar_merge_report_is_reproducible_and_blocked():
    generated = build_b2_source_hash_sidecar_merge_report()
    committed = _load_merge_report()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_SCHEMA
    assert committed["status"] == "source_hash_sidecar_incomplete_promotion_blocked"
    assert committed["production_promoted"] is False
    assert committed["sidecar_record_count"] == 44
    assert committed["sidecar_error_count"] == 0
    assert committed["merged_validation"]["source_hashes_valid"] is False
    assert committed["merged_validation"]["failing_record_count"] == 44
    permissions = committed["promotion_permissions"]
    assert permissions["can_commit_source_binaries"] is False
    assert permissions["can_run_imports"] is False
    assert permissions["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_source_hash_sidecar_merge_accepts_complete_local_hash_evidence():
    payload = _complete_sidecar_payload()
    merged = merge_b2_source_hash_sidecar(payload)
    validation = build_b2_source_hash_validation_report(merged)
    report = build_b2_source_hash_sidecar_merge_report(payload)

    assert validation["source_hashes_valid"] is True
    assert validation["source_file_hash_count"] == 44
    assert merged["summary"]["filled_hash_record_count"] == 44
    assert merged["summary"]["source_file_hash_count"] == 44
    assert report["status"] == "source_hash_sidecar_valid_manual_review_required"
    assert report["sidecar_error_count"] == 0
    assert report["promotion_permissions"]["can_run_imports"] is True
    assert report["promotion_permissions"]["can_mark_any_asset_source_reviewed"] is True
    assert report["promotion_permissions"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_source_hash_sidecar_merge_rejects_source_binary_commit_paths():
    payload = _complete_sidecar_payload()
    first = payload["records"][0]
    first["source_binary_committed"] = True
    first["source_binary_repo_paths"] = ["Content/Forbidden/source.zip"]
    report = build_b2_source_hash_sidecar_merge_report(payload)

    assert report["status"] == "source_hash_sidecar_incomplete_promotion_blocked"
    assert report["promotion_permissions"]["can_run_imports"] is False
    assert {
        "record_id": first["record_id"],
        "field": "source_binary_committed",
        "reason": "source_binary_commit_blocked_by_current_storage_policy",
    } in report["sidecar_errors"]
    assert {
        "record_id": first["record_id"],
        "field": "source_binary_repo_paths",
        "reason": "source_binary_repo_paths_blocked_by_current_storage_policy",
    } in report["sidecar_errors"]


def _complete_sidecar_payload() -> dict:
    payload = build_b2_source_hash_sidecar_template()
    for index, record in enumerate(payload["records"]):
        kind = record["record_kind"]
        record["local_source_root"] = f"/reviewed/local/source/{index}"
        record["license_snapshot_url"] = "https://example.com/reviewed-license"
        record["source_files"] = [_source_file(index)]
        record["hash_status"] = "recorded"
        if kind == "cc0_poly_haven_source_bundle":
            record["selected_resolution"] = "1k"
            record["selected_file_formats"] = ["fbx"]
            record["expected_total_byte_size"] = 2048 + index
        elif kind == "first_party_or_project_owned_recipe":
            record["recipe_source_path"] = f"tools/first_party_asset_{index}.py"
            record["tool_version"] = "test-tool-1"
            record["seed"] = str(index)
    payload["summary"]["filled_sidecar_record_count"] = payload["summary"][
        "sidecar_record_count"
    ]
    payload["summary"]["source_file_hash_count"] = payload["summary"][
        "sidecar_record_count"
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
