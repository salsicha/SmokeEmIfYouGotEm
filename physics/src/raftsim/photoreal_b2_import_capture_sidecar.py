"""Build and merge B2 import/capture review sidecar evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .photoreal_b2_import_capture_review import (
    B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
    B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
    build_b2_import_capture_review_ledger,
    build_b2_import_capture_review_validation_report,
)


B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_import_capture_review_sidecar_template.json"
)
B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_import_capture_review_sidecar_merge_report.json"
)
B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_import_capture_review_sidecar_template.v1"
)
B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_SCHEMA = (
    "raftsim.photoreal.b2_import_capture_review_sidecar_merge_report.v1"
)


def build_b2_import_capture_review_sidecar_template() -> dict[str, Any]:
    """Build a fillable local Unreal import/capture/review evidence sidecar."""

    ledger = build_b2_import_capture_review_ledger()
    records = [_sidecar_record(record) for record in ledger["records"]]
    return {
        "schema": B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_import_capture_review_sidecar_template_no_promotion",
        "source_ledger": B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
        "source_validation_report": B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
        "production_promoted": False,
        "summary": {
            "sidecar_record_count": len(records),
            "filled_sidecar_record_count": 0,
            "candidate_import_report_count": 0,
            "candidate_capture_count": 0,
            "approved_review_record_count": 0,
            "can_promote_any_b2_asset_set": False,
        },
        "records": records,
        "sidecar_contract": {
            "record_id_must_match_import_capture_ledger": True,
            "source_hash_record_must_be_valid_before_import_approval": True,
            "required_capture_views": ledger["record_contract"]["required_capture_views"],
            "required_review_domains": ledger["record_contract"]["required_review_domains"],
            "may_commit_sidecar_without_source_binaries": True,
            "may_commit_screenshots_and_reports_only_when_hash_locked": True,
            "corridor_substitution_allowed_from_sidecar": False,
            "manual_per_river_asset_set_review_still_required": True,
        },
        "promotion_gate": {
            "can_run_imports_from_sidecar_alone": False,
            "can_mark_any_source_reviewed": False,
            "can_run_corridor_substitution": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "complete_when": [
                "source hash validation passes for every sidecar record",
                "Unreal import report path and SHA-256 are recorded",
                "turntable, 60 m, and 150 m captures exist, are hash-locked, and are approved",
                "rights, ecology/guide, art, technical-art, hazard, and performance reviews approve with evidence",
                "desktop and VR performance profiles are recorded and pass",
                "per-river promotion readiness and owner decision gates are run after the merge",
            ],
        },
    }


def write_b2_import_capture_review_sidecar_template(repo_root: Path) -> Path:
    payload = build_b2_import_capture_review_sidecar_template()
    path = repo_root / B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def merge_b2_import_capture_review_sidecar(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge sidecar evidence into the canonical B2 import/capture ledger."""

    ledger = deepcopy(build_b2_import_capture_review_ledger())
    sidecar = sidecar_payload or build_b2_import_capture_review_sidecar_template()
    targets = {record["record_id"]: record for record in ledger["records"]}
    for record in sidecar["records"]:
        target = targets.get(record["record_id"])
        if target is None:
            continue
        target["status"] = record["status"]
        target["source_hash_record_valid"] = record["source_hash_record_valid"]
        target["import_report"].update(record["import_report"])
        _merge_list_by_key(target["captures"], record["captures"], "view_id")
        _merge_list_by_key(target["reviews"], record["reviews"], "domain_id")
        target["performance_evidence"].update(record["performance_evidence"])
        target["can_import_now"] = False
        target["can_promote_candidate_now"] = False
    validation = build_b2_import_capture_review_validation_report(ledger)
    ledger["summary"]["blocked_record_count"] = validation["failing_record_count"]
    ledger["summary"]["candidate_import_report_count"] = validation["summary"][
        "candidate_import_report_count"
    ]
    ledger["summary"]["candidate_capture_count"] = validation["summary"][
        "candidate_capture_count"
    ]
    ledger["summary"]["approved_review_record_count"] = validation["summary"][
        "approved_review_record_count"
    ]
    ledger["summary"]["can_run_any_import_now"] = False
    ledger["summary"]["can_promote_any_b2_asset_set"] = False
    return ledger


def build_b2_import_capture_review_sidecar_merge_report(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an import/capture sidecar merge without promoting assets."""

    sidecar = sidecar_payload or build_b2_import_capture_review_sidecar_template()
    sidecar_errors = _sidecar_errors(sidecar)
    merged = merge_b2_import_capture_review_sidecar(sidecar)
    validation = build_b2_import_capture_review_validation_report(merged)
    valid = not sidecar_errors and validation["import_reviews_valid"]
    return {
        "schema": B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": (
            "import_capture_review_sidecar_valid_manual_promotion_required"
            if valid
            else "import_capture_review_sidecar_incomplete_promotion_blocked"
        ),
        "production_promoted": False,
        "source_sidecar_template": B2_IMPORT_CAPTURE_REVIEW_SIDECAR_TEMPLATE_RELATIVE_PATH,
        "source_ledger": B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
        "source_validation_report": B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH,
        "sidecar_record_count": len(sidecar["records"]),
        "sidecar_error_count": len(sidecar_errors),
        "sidecar_errors": sidecar_errors,
        "merged_validation": {
            "import_reviews_valid": validation["import_reviews_valid"],
            "validation_error_count": validation["validation_error_count"],
            "failing_record_count": validation["failing_record_count"],
            "candidate_import_report_count": validation["summary"][
                "candidate_import_report_count"
            ],
            "candidate_capture_count": validation["summary"]["candidate_capture_count"],
            "approved_review_record_count": validation["summary"][
                "approved_review_record_count"
            ],
        },
        "promotion_permissions": {
            "can_mark_any_source_reviewed": valid,
            "can_run_corridor_substitution": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
        },
        "promotion_gate": {
            "can_replace_per_river_promotion_readiness": False,
            "can_replace_owner_art_guide_rights_hazard_performance_decision": False,
            "manual_per_river_asset_set_review_required": True,
        },
    }


def write_b2_import_capture_review_sidecar_merge_report(repo_root: Path) -> Path:
    payload = build_b2_import_capture_review_sidecar_merge_report()
    path = repo_root / B2_IMPORT_CAPTURE_REVIEW_SIDECAR_MERGE_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sidecar_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "source_kind": record["source_kind"],
        "source_hash_record_id": record["source_hash_record_id"],
        "river_id": record["river_id"],
        "candidate_id": record["candidate_id"],
        "asset_need_id": record["asset_need_id"],
        "status": "sidecar_not_recorded",
        "source_hash_record_valid": False,
        "import_report": deepcopy(record["import_report"]),
        "captures": deepcopy(record["captures"]),
        "reviews": deepcopy(record["reviews"]),
        "performance_evidence": deepcopy(record["performance_evidence"]),
        "can_import_now": False,
        "can_promote_candidate_now": False,
        "notes": "",
    }


def _sidecar_errors(sidecar: dict[str, Any]) -> list[dict[str, str]]:
    ledger = build_b2_import_capture_review_ledger()
    expected = {record["record_id"]: record for record in ledger["records"]}
    errors: list[dict[str, str]] = []
    ids = [record["record_id"] for record in sidecar["records"]]
    for record_id in sorted(set(expected) - set(ids)):
        errors.append(_error(record_id, "records", "sidecar_record_missing"))
    for record_id in sorted(set(ids) - set(expected)):
        errors.append(_error(record_id, "records", "unknown_sidecar_record"))
    if len(ids) != len(set(ids)):
        errors.append(_error("", "records", "duplicate_sidecar_record"))
    for record in sidecar["records"]:
        expected_record = expected.get(record["record_id"])
        if expected_record is None:
            continue
        for field in ("source_kind", "source_hash_record_id", "river_id", "candidate_id", "asset_need_id"):
            if record[field] != expected_record[field]:
                errors.append(_error(record["record_id"], field, "sidecar_field_mismatch"))
        if record["can_promote_candidate_now"]:
            errors.append(
                _error(
                    record["record_id"],
                    "can_promote_candidate_now",
                    "candidate_promotion_requires_per_river_decision",
                )
            )
        if record["can_import_now"]:
            errors.append(
                _error(
                    record["record_id"],
                    "can_import_now",
                    "import_execution_is_not_granted_by_sidecar",
                )
            )
    return errors


def _merge_list_by_key(
    target_items: list[dict[str, Any]],
    sidecar_items: list[dict[str, Any]],
    key: str,
) -> None:
    sidecar_by_key = {item[key]: item for item in sidecar_items}
    for target in target_items:
        source = sidecar_by_key.get(target[key])
        if source is not None:
            target.update(source)


def _error(record_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "field": field,
        "reason": reason,
    }
