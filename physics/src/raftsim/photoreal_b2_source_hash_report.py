"""Build the B2 local source hash report template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)
from .photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
    build_b2_source_storage_decision,
)


B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_hash_report_template.json"
)
B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_hash_validation_report.json"
)
B2_SOURCE_HASH_REPORT_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_source_hash_report_template.v1"
)
B2_SOURCE_HASH_VALIDATION_REPORT_SCHEMA = (
    "raftsim.photoreal.b2_source_hash_validation_report.v1"
)


def build_b2_source_hash_report_template() -> dict[str, Any]:
    """Build an empty source-hash ledger for the five-river B2 queue."""

    preflight = build_b2_source_acquisition_preflight()
    storage = build_b2_source_storage_decision()
    cc0_records = [
        _cc0_hash_record(task) for task in preflight["cc0_download_tasks"]
    ]
    fab_records = [
        _fab_hash_record(slot) for slot in preflight["fab_local_only_slots"]
    ]
    first_party_records = [
        _first_party_hash_record(entry)
        for entry in preflight["first_party_entries"]
    ]
    record_count = len(cc0_records) + len(fab_records) + len(first_party_records)
    return {
        "schema": B2_SOURCE_HASH_REPORT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_source_hash_report_template_no_downloads_or_promotion",
        "source_preflight": B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
        "source_storage_decision": B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
        "production_promoted": False,
        "current_operating_mode": {
            "mode": storage["current_operating_mode"]["mode"],
            "downloads_allowed_now": storage["current_operating_mode"][
                "downloads_allowed_now"
            ],
            "source_binaries_allowed_in_repo_now": storage[
                "current_operating_mode"
            ]["source_binaries_allowed_in_repo_now"],
            "hash_manifests_allowed_in_repo_now": storage[
                "current_operating_mode"
            ]["hash_manifests_allowed_in_repo_now"],
            "source_binary_policy_decision_required": True,
        },
        "summary": {
            "river_count": preflight["river_count"],
            "cc0_hash_record_count": len(cc0_records),
            "fab_local_only_hash_record_count": len(fab_records),
            "first_party_recipe_hash_record_count": len(first_party_records),
            "required_hash_record_count": record_count,
            "filled_hash_record_count": 0,
            "source_file_hash_count": 0,
            "can_promote_any_b2_asset_set": False,
        },
        "cc0_hash_records": cc0_records,
        "fab_local_only_hash_records": fab_records,
        "first_party_recipe_hash_records": first_party_records,
        "hash_entry_contract": {
            "required_source_file_fields": [
                "relative_path",
                "byte_size",
                "sha256",
                "media_type_or_extension",
                "source_bundle_role",
            ],
            "sha256_format": "64 lowercase hexadecimal characters",
            "file_list_must_be_complete": True,
            "hash_report_may_be_committed_without_source_binary": True,
            "source_binary_may_be_committed_from_empty_template": False,
        },
        "promotion_gate": {
            "can_download_from_template_alone": False,
            "can_commit_source_binaries": False,
            "can_run_corridor_substitution": False,
            "can_mark_any_asset_source_reviewed": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "complete_when": [
                "owner storage policy decision is recorded",
                "each executed source acquisition records exact selected formats and byte sizes",
                "every source file has a 64-hex SHA-256 hash",
                "license snapshot and import settings are recorded",
                "isolated capture, rights, ecology/guide/art, and performance reviews pass",
            ],
        },
    }


def write_b2_source_hash_report_template(repo_root: Path) -> Path:
    payload = build_b2_source_hash_report_template()
    path = repo_root / B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_b2_source_hash_validation_report(
    hash_report_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a B2 source-hash report without promoting any asset."""

    payload = hash_report_payload or build_b2_source_hash_report_template()
    record_errors = []
    source_file_hash_count = 0
    for record in payload["cc0_hash_records"]:
        errors, count = _validate_source_file_record(record, "source_files")
        record_errors.extend(errors)
        source_file_hash_count += count
        if not record["selected_resolution"]:
            record_errors.append(_record_error(record["record_id"], "selected_resolution", "missing"))
        if not record["selected_file_formats"]:
            record_errors.append(_record_error(record["record_id"], "selected_file_formats", "missing"))
        if not record["actual_local_source_root"]:
            record_errors.append(_record_error(record["record_id"], "actual_local_source_root", "missing"))
        if not record["license_snapshot_url"]:
            record_errors.append(_record_error(record["record_id"], "license_snapshot_url", "missing"))
    for record in payload["fab_local_only_hash_records"]:
        errors, count = _validate_source_file_record(record, "source_files")
        record_errors.extend(errors)
        source_file_hash_count += count
        if not record["local_source_root"]:
            record_errors.append(_record_error(record["record_id"], "local_source_root", "missing"))
        if not record["license_snapshot_url"]:
            record_errors.append(_record_error(record["record_id"], "license_snapshot_url", "missing"))
    for record in payload["first_party_recipe_hash_records"]:
        errors, count = _validate_source_file_record(record, "generated_files")
        record_errors.extend(errors)
        source_file_hash_count += count
        if not record["recipe_source_path"]:
            record_errors.append(_record_error(record["record_id"], "recipe_source_path", "missing"))
        if not record["tool_version"]:
            record_errors.append(_record_error(record["record_id"], "tool_version", "missing"))
        if not record["seed"]:
            record_errors.append(_record_error(record["record_id"], "seed", "missing"))

    failing_record_ids = sorted({error["record_id"] for error in record_errors})
    source_hashes_valid = not record_errors
    status = (
        "source_hash_records_valid_manual_review_required"
        if source_hashes_valid
        else "source_hash_records_incomplete_promotion_blocked"
    )
    return {
        "schema": B2_SOURCE_HASH_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": status,
        "source_hash_report_template": B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
        "production_promoted": False,
        "source_hashes_valid": source_hashes_valid,
        "validation_error_count": len(record_errors),
        "failing_record_count": len(failing_record_ids),
        "failing_record_ids": failing_record_ids,
        "source_file_hash_count": source_file_hash_count,
        "record_errors": record_errors,
        "summary": {
            "required_hash_record_count": payload["summary"][
                "required_hash_record_count"
            ],
            "filled_hash_record_count": payload["summary"][
                "filled_hash_record_count"
            ],
            "cc0_hash_record_count": len(payload["cc0_hash_records"]),
            "fab_local_only_hash_record_count": len(
                payload["fab_local_only_hash_records"]
            ),
            "first_party_recipe_hash_record_count": len(
                payload["first_party_recipe_hash_records"]
            ),
        },
        "promotion_gate": {
            "can_download_from_validation_report_alone": False,
            "can_commit_source_binaries": False,
            "can_run_imports": source_hashes_valid,
            "can_run_corridor_substitution": False,
            "can_mark_any_asset_source_reviewed": source_hashes_valid,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "manual_rights_import_capture_and_performance_review_required": True,
        },
    }


def write_b2_source_hash_validation_report(repo_root: Path) -> Path:
    payload = build_b2_source_hash_validation_report()
    path = repo_root / B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _cc0_hash_record(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"{task['task_id']}:source_hash_report",
        "record_kind": "cc0_poly_haven_source_bundle",
        "task_id": task["task_id"],
        "river_id": task["river_id"],
        "candidate_id": task["candidate_id"],
        "asset_need_id": task["asset_need_id"],
        "asset_url": task["asset_url"],
        "license_class": task["license_class"],
        "planned_source_root_env": task["planned_source_root_env"],
        "selected_resolution": "",
        "selected_file_formats": [],
        "expected_total_byte_size": None,
        "actual_local_source_root": "",
        "license_snapshot_url": "",
        "source_files": [],
        "source_binary_committed": False,
        "source_binary_repo_paths": [],
        "hash_status": "not_recorded",
        "required_before_review": task["required_before_commit"],
        "can_import_from_record_now": False,
        "can_promote_candidate_now": False,
    }


def _fab_hash_record(slot: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"{slot['slot_id']}:local_hash_report",
        "record_kind": "fab_local_only_source_bundle",
        "slot_id": slot["slot_id"],
        "river_id": slot["river_id"],
        "candidate_id": slot["candidate_id"],
        "asset_need_id": slot["asset_need_id"],
        "asset_url": slot["asset_url"],
        "license_class": slot["license_class"],
        "repo_binary_policy": slot["repo_binary_policy"],
        "local_source_root": "",
        "license_snapshot_url": "",
        "source_files": [],
        "source_binary_committed": False,
        "hash_status": "not_recorded",
        "required_before_local_import": slot["required_before_local_import"],
        "can_commit_source_binaries": False,
        "can_import_from_record_now": False,
        "can_promote_candidate_now": False,
    }


def _first_party_hash_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"{entry['entry_id']}:recipe_hash_report",
        "record_kind": "first_party_or_project_owned_recipe",
        "entry_id": entry["entry_id"],
        "river_id": entry["river_id"],
        "candidate_id": entry["candidate_id"],
        "asset_need_id": entry["asset_need_id"],
        "source_family": entry["source_family"],
        "recipe_source_path": "",
        "tool_version": "",
        "seed": "",
        "generated_files": [],
        "source_binary_committed": False,
        "hash_status": "not_recorded",
        "can_cover_external_asset_gap": entry["can_cover_external_asset_gap"],
        "can_replace_human_lifelike_review": entry[
            "can_replace_human_lifelike_review"
        ],
        "can_promote_candidate_now": False,
    }


def _validate_source_file_record(
    record: dict[str, Any],
    file_list_field: str,
) -> tuple[list[dict[str, str]], int]:
    files = record[file_list_field]
    if not files:
        return ([_record_error(record["record_id"], file_list_field, "missing")], 0)
    errors = []
    valid_hash_count = 0
    for index, source_file in enumerate(files):
        prefix = f"{file_list_field}[{index}]"
        for field in (
            "relative_path",
            "byte_size",
            "sha256",
            "media_type_or_extension",
            "source_bundle_role",
        ):
            if source_file.get(field) in ("", None, []):
                errors.append(_record_error(record["record_id"], f"{prefix}.{field}", "missing"))
        sha256 = source_file.get("sha256", "")
        if sha256 and not _valid_sha256(sha256):
            errors.append(_record_error(record["record_id"], f"{prefix}.sha256", "invalid_sha256"))
        elif sha256:
            valid_hash_count += 1
    if record["hash_status"] != "recorded":
        errors.append(_record_error(record["record_id"], "hash_status", "not_recorded"))
    return errors, valid_hash_count


def _record_error(record_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "field": field,
        "reason": reason,
    }


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
