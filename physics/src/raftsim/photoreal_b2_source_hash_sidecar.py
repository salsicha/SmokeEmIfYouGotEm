"""Build and merge B2 local source-hash sidecar evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_hash_report_template,
    build_b2_source_hash_validation_report,
)


B2_SOURCE_HASH_SIDECAR_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_hash_sidecar_template.json"
)
B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_hash_sidecar_merge_report.json"
)
B2_SOURCE_HASH_SIDECAR_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_source_hash_sidecar_template.v1"
)
B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_SCHEMA = (
    "raftsim.photoreal.b2_source_hash_sidecar_merge_report.v1"
)

_TARGET_LIST_BY_KIND = {
    "cc0_poly_haven_source_bundle": "cc0_hash_records",
    "fab_local_only_source_bundle": "fab_local_only_hash_records",
    "first_party_or_project_owned_recipe": "first_party_recipe_hash_records",
}
_FILE_LIST_BY_KIND = {
    "cc0_poly_haven_source_bundle": "source_files",
    "fab_local_only_source_bundle": "source_files",
    "first_party_or_project_owned_recipe": "generated_files",
}


def build_b2_source_hash_sidecar_template() -> dict[str, Any]:
    """Build a fillable local-only source-hash sidecar template."""

    source_template = build_b2_source_hash_report_template()
    records = [
        _sidecar_record(record)
        for record in (
            source_template["cc0_hash_records"]
            + source_template["fab_local_only_hash_records"]
            + source_template["first_party_recipe_hash_records"]
        )
    ]
    return {
        "schema": B2_SOURCE_HASH_SIDECAR_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_source_hash_sidecar_template_no_downloads_or_promotion",
        "source_hash_report_template": B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
        "source_hash_validation_report": B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
        "production_promoted": False,
        "current_operating_mode": source_template["current_operating_mode"],
        "summary": {
            "sidecar_record_count": len(records),
            "filled_sidecar_record_count": 0,
            "source_file_hash_count": 0,
            "source_binaries_committed": False,
            "can_promote_any_b2_asset_set": False,
        },
        "records": records,
        "sidecar_contract": {
            "record_id_must_match_hash_report_template": True,
            "source_files_must_use_hash_entry_contract": source_template[
                "hash_entry_contract"
            ],
            "may_commit_sidecar_without_source_binaries": True,
            "may_commit_third_party_source_binaries_from_sidecar": False,
            "merge_updates_only_hash_report_fields": True,
            "manual_rights_import_capture_and_performance_review_still_required": True,
        },
        "promotion_gate": {
            "can_download_from_sidecar_alone": False,
            "can_commit_source_binaries": False,
            "can_run_corridor_substitution": False,
            "can_mark_any_asset_source_reviewed": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "complete_when": [
                "a sidecar record exists for every source-hash template record",
                "each sidecar record includes local source root or recipe provenance",
                "each source/generated file has byte size, media type, role, and SHA-256",
                "license snapshot URL or recipe/tool/seed provenance is recorded",
                "the merged hash report validates before import/capture review begins",
            ],
        },
    }


def write_b2_source_hash_sidecar_template(repo_root: Path) -> Path:
    payload = build_b2_source_hash_sidecar_template()
    path = repo_root / B2_SOURCE_HASH_SIDECAR_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def merge_b2_source_hash_sidecar(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge a sidecar payload into the canonical B2 source-hash report shape."""

    source_template = build_b2_source_hash_report_template()
    merged = deepcopy(source_template)
    sidecar = sidecar_payload or build_b2_source_hash_sidecar_template()
    target_records = {
        record["record_id"]: record
        for list_name in _TARGET_LIST_BY_KIND.values()
        for record in merged[list_name]
    }
    for record in sidecar["records"]:
        target = target_records.get(record["record_id"])
        if target is None:
            continue
        kind = record["record_kind"]
        if kind == "cc0_poly_haven_source_bundle":
            target["selected_resolution"] = record["selected_resolution"]
            target["selected_file_formats"] = record["selected_file_formats"]
            target["expected_total_byte_size"] = record["expected_total_byte_size"]
            target["actual_local_source_root"] = record["local_source_root"]
            target["license_snapshot_url"] = record["license_snapshot_url"]
            target["source_files"] = record["source_files"]
            target["source_binary_committed"] = record["source_binary_committed"]
            target["source_binary_repo_paths"] = record["source_binary_repo_paths"]
            target["hash_status"] = record["hash_status"]
        elif kind == "fab_local_only_source_bundle":
            target["local_source_root"] = record["local_source_root"]
            target["license_snapshot_url"] = record["license_snapshot_url"]
            target["source_files"] = record["source_files"]
            target["source_binary_committed"] = record["source_binary_committed"]
            target["hash_status"] = record["hash_status"]
        elif kind == "first_party_or_project_owned_recipe":
            target["recipe_source_path"] = record["recipe_source_path"]
            target["tool_version"] = record["tool_version"]
            target["seed"] = record["seed"]
            target["generated_files"] = record["source_files"]
            target["source_binary_committed"] = record["source_binary_committed"]
            target["hash_status"] = record["hash_status"]
    validation = build_b2_source_hash_validation_report(merged)
    merged["summary"]["filled_hash_record_count"] = (
        merged["summary"]["required_hash_record_count"]
        - validation["failing_record_count"]
    )
    merged["summary"]["source_file_hash_count"] = validation["source_file_hash_count"]
    merged["summary"]["can_promote_any_b2_asset_set"] = False
    return merged


def build_b2_source_hash_sidecar_merge_report(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a sidecar merge without promoting source assets."""

    sidecar = sidecar_payload or build_b2_source_hash_sidecar_template()
    sidecar_errors = _sidecar_errors(sidecar)
    merged = merge_b2_source_hash_sidecar(sidecar)
    validation = build_b2_source_hash_validation_report(merged)
    valid = not sidecar_errors and validation["source_hashes_valid"]
    status = (
        "source_hash_sidecar_valid_manual_review_required"
        if valid
        else "source_hash_sidecar_incomplete_promotion_blocked"
    )
    return {
        "schema": B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": status,
        "production_promoted": False,
        "source_hash_sidecar_template": B2_SOURCE_HASH_SIDECAR_TEMPLATE_RELATIVE_PATH,
        "source_hash_report_template": B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
        "source_hash_validation_report": B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
        "sidecar_record_count": len(sidecar["records"]),
        "sidecar_error_count": len(sidecar_errors),
        "sidecar_errors": sidecar_errors,
        "merged_validation": {
            "source_hashes_valid": validation["source_hashes_valid"],
            "validation_error_count": validation["validation_error_count"],
            "failing_record_count": validation["failing_record_count"],
            "source_file_hash_count": validation["source_file_hash_count"],
        },
        "promotion_permissions": {
            "can_commit_source_binaries": False,
            "can_run_imports": valid,
            "can_mark_any_asset_source_reviewed": valid,
            "can_run_corridor_substitution": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
        },
        "promotion_gate": {
            "can_download_from_merge_report_alone": False,
            "can_commit_source_binaries": False,
            "can_replace_import_capture_review": False,
            "can_replace_rights_or_ecology_review": False,
            "manual_rights_import_capture_and_performance_review_required": True,
        },
    }


def write_b2_source_hash_sidecar_merge_report(repo_root: Path) -> Path:
    payload = build_b2_source_hash_sidecar_merge_report()
    path = repo_root / B2_SOURCE_HASH_SIDECAR_MERGE_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sidecar_record(record: dict[str, Any]) -> dict[str, Any]:
    kind = record["record_kind"]
    payload = {
        "record_id": record["record_id"],
        "record_kind": kind,
        "river_id": record["river_id"],
        "candidate_id": record["candidate_id"],
        "asset_need_id": record["asset_need_id"],
        "local_source_root": "",
        "license_snapshot_url": "",
        "selected_resolution": "",
        "selected_file_formats": [],
        "expected_total_byte_size": None,
        "recipe_source_path": "",
        "tool_version": "",
        "seed": "",
        "source_files": [],
        "source_binary_committed": False,
        "source_binary_repo_paths": [],
        "hash_status": "not_recorded",
        "notes": "",
    }
    if kind == "cc0_poly_haven_source_bundle":
        payload["task_id"] = record["task_id"]
        payload["asset_url"] = record["asset_url"]
    elif kind == "fab_local_only_source_bundle":
        payload["slot_id"] = record["slot_id"]
        payload["asset_url"] = record["asset_url"]
    elif kind == "first_party_or_project_owned_recipe":
        payload["entry_id"] = record["entry_id"]
        payload["source_family"] = record["source_family"]
    return payload


def _sidecar_errors(sidecar: dict[str, Any]) -> list[dict[str, str]]:
    source_template = build_b2_source_hash_report_template()
    expected_by_id = {
        record["record_id"]: record
        for list_name in _TARGET_LIST_BY_KIND.values()
        for record in source_template[list_name]
    }
    errors: list[dict[str, str]] = []
    ids = [record["record_id"] for record in sidecar["records"]]
    for record_id in sorted(set(expected_by_id) - set(ids)):
        errors.append(_error(record_id, "records", "sidecar_record_missing"))
    for record_id in sorted(set(ids) - set(expected_by_id)):
        errors.append(_error(record_id, "records", "unknown_sidecar_record"))
    if len(ids) != len(set(ids)):
        errors.append(_error("", "records", "duplicate_sidecar_record"))
    for record in sidecar["records"]:
        expected = expected_by_id.get(record["record_id"])
        if expected is None:
            continue
        if record["record_kind"] != expected["record_kind"]:
            errors.append(_error(record["record_id"], "record_kind", "record_kind_mismatch"))
        if record["record_kind"] not in _TARGET_LIST_BY_KIND:
            errors.append(_error(record["record_id"], "record_kind", "record_kind_unknown"))
        if record["source_binary_committed"]:
            errors.append(
                _error(
                    record["record_id"],
                    "source_binary_committed",
                    "source_binary_commit_blocked_by_current_storage_policy",
                )
            )
        if record["source_binary_repo_paths"]:
            errors.append(
                _error(
                    record["record_id"],
                    "source_binary_repo_paths",
                    "source_binary_repo_paths_blocked_by_current_storage_policy",
                )
            )
    return errors


def _error(record_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "field": field,
        "reason": reason,
    }
