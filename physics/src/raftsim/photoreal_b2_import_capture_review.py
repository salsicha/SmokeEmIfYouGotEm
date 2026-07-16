"""Build B2 isolated import, capture, and review ledgers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_source_hash_report import (
    B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_hash_report_template,
    build_b2_source_hash_validation_report,
)


B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_import_capture_review_ledger.json"
)
B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_import_capture_review_validation_report.json"
)
B2_IMPORT_CAPTURE_REVIEW_LEDGER_SCHEMA = (
    "raftsim.photoreal.b2_import_capture_review_ledger.v1"
)
B2_IMPORT_CAPTURE_REVIEW_VALIDATION_SCHEMA = (
    "raftsim.photoreal.b2_import_capture_review_validation.v1"
)

_CAPTURE_VIEWS = (
    ("isolated_turntable", "isolated turntable capture"),
    ("river_distance_60m", "60 m river-distance capture"),
    ("river_distance_150m", "150 m river-distance capture"),
)
_REVIEW_DOMAINS = (
    "rights_and_license",
    "ecology_or_guide_fit",
    "art_direction_lifelike",
    "technical_art_import_quality",
    "hazard_readability",
    "desktop_vr_performance",
)


def build_b2_import_capture_review_ledger() -> dict[str, Any]:
    """Build the empty per-candidate B2 import/capture/review ledger."""

    source_template = build_b2_source_hash_report_template()
    source_validation = build_b2_source_hash_validation_report(source_template)
    records = []
    for source_record in source_template["cc0_hash_records"]:
        records.append(_import_record(source_record, "cc0_poly_haven"))
    for source_record in source_template["fab_local_only_hash_records"]:
        records.append(_import_record(source_record, "fab_local_only"))
    for source_record in source_template["first_party_recipe_hash_records"]:
        records.append(_import_record(source_record, "first_party_or_project_owned"))
    return {
        "schema": B2_IMPORT_CAPTURE_REVIEW_LEDGER_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_import_capture_review_ledger_source_hashes_missing",
        "production_promoted": False,
        "source_hash_report_template": B2_SOURCE_HASH_REPORT_TEMPLATE_RELATIVE_PATH,
        "source_hash_validation_report": B2_SOURCE_HASH_VALIDATION_REPORT_RELATIVE_PATH,
        "source_hash_validation_summary": {
            "source_hashes_valid": source_validation["source_hashes_valid"],
            "validation_error_count": source_validation["validation_error_count"],
            "failing_record_count": source_validation["failing_record_count"],
            "source_file_hash_count": source_validation["source_file_hash_count"],
        },
        "summary": {
            "import_review_record_count": len(records),
            "blocked_record_count": len(records),
            "candidate_import_report_count": 0,
            "candidate_capture_count": 0,
            "approved_review_record_count": 0,
            "can_run_any_import_now": False,
            "can_promote_any_b2_asset_set": False,
        },
        "records": records,
        "record_contract": {
            "required_capture_views": [view_id for view_id, _ in _CAPTURE_VIEWS],
            "required_review_domains": list(_REVIEW_DOMAINS),
            "source_hash_record_must_be_valid": True,
            "map_check_zero_errors_required": True,
            "desktop_and_vr_performance_required": True,
            "corridor_substitution_allowed_from_ledger_alone": False,
        },
        "promotion_gate": {
            "can_run_imports_from_empty_ledger": False,
            "can_mark_any_source_reviewed": False,
            "can_mark_any_candidate_visual_approved": False,
            "can_run_corridor_substitution": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "complete_when": [
                "source hash validation passes for the candidate",
                "Unreal import report path and SHA-256 are recorded",
                "turntable, 60 m, and 150 m isolated captures exist and are hash-locked",
                "rights, ecology/guide, art, technical-art, hazard, and performance reviews pass",
                "desktop and VR performance evidence is attached",
            ],
        },
    }


def write_b2_import_capture_review_ledger(repo_root: Path) -> Path:
    payload = build_b2_import_capture_review_ledger()
    path = repo_root / B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_b2_import_capture_review_validation_report(
    ledger_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate B2 import/capture/review records without promotion."""

    ledger = ledger_payload or build_b2_import_capture_review_ledger()
    record_errors = []
    candidate_capture_count = 0
    approved_record_count = 0
    for record in ledger["records"]:
        record_errors.extend(_validate_import_record(record))
        candidate_capture_count += sum(
            1 for capture in record["captures"] if capture["capture_path"]
        )
        if _record_fully_approved(record):
            approved_record_count += 1
    failing_record_ids = sorted({error["record_id"] for error in record_errors})
    import_reviews_valid = not record_errors
    status = (
        "import_capture_review_records_valid_manual_promotion_required"
        if import_reviews_valid
        else "import_capture_review_records_incomplete_promotion_blocked"
    )
    return {
        "schema": B2_IMPORT_CAPTURE_REVIEW_VALIDATION_SCHEMA,
        "generated_on": "2026-07-16",
        "status": status,
        "production_promoted": False,
        "source_ledger": B2_IMPORT_CAPTURE_REVIEW_LEDGER_RELATIVE_PATH,
        "import_reviews_valid": import_reviews_valid,
        "validation_error_count": len(record_errors),
        "failing_record_count": len(failing_record_ids),
        "failing_record_ids": failing_record_ids,
        "record_errors": record_errors,
        "summary": {
            "import_review_record_count": len(ledger["records"]),
            "candidate_import_report_count": sum(
                1 for record in ledger["records"] if record["import_report"]["path"]
            ),
            "candidate_capture_count": candidate_capture_count,
            "approved_review_record_count": approved_record_count,
        },
        "promotion_gate": {
            "can_run_imports_from_validation_report_alone": False,
            "can_mark_any_source_reviewed": import_reviews_valid,
            "can_run_corridor_substitution": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "manual_per_river_asset_set_review_required": True,
        },
    }


def write_b2_import_capture_review_validation_report(repo_root: Path) -> Path:
    payload = build_b2_import_capture_review_validation_report()
    path = repo_root / B2_IMPORT_CAPTURE_REVIEW_VALIDATION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _import_record(source_record: dict[str, Any], source_kind: str) -> dict[str, Any]:
    river_id = source_record["river_id"]
    candidate_id = source_record["candidate_id"]
    asset_need_id = source_record["asset_need_id"]
    review_root = (
        "docs/environment-captures/photoreal_river_previews/asset_intake/b2"
    )
    return {
        "record_id": f"{river_id}:{candidate_id}:b2_import_capture_review",
        "source_kind": source_kind,
        "source_hash_record_id": source_record["record_id"],
        "river_id": river_id,
        "candidate_id": candidate_id,
        "asset_need_id": asset_need_id,
        "status": "blocked_pending_valid_source_hash_record",
        "source_hash_record_valid": False,
        "import_report": {
            "path": "",
            "sha256": "",
            "unreal_destination_root": _unreal_destination_root(river_id, candidate_id),
            "map_check_zero_errors": False,
            "import_settings_recorded": False,
        },
        "captures": [
            {
                "view_id": view_id,
                "description": description,
                "expected_capture_path": (
                    f"{review_root}/{river_id}/{candidate_id}_{view_id}.png"
                ),
                "capture_path": "",
                "sha256": "",
                "approved": False,
            }
            for view_id, description in _CAPTURE_VIEWS
        ],
        "reviews": [
            {
                "domain_id": domain_id,
                "reviewer": "",
                "review_date": "",
                "approved": False,
                "evidence": [],
                "notes": "",
            }
            for domain_id in _REVIEW_DOMAINS
        ],
        "performance_evidence": {
            "desktop_profile": "",
            "vr_profile": "",
            "desktop_passed": False,
            "vr_passed": False,
        },
        "can_import_now": False,
        "can_promote_candidate_now": False,
    }


def _validate_import_record(record: dict[str, Any]) -> list[dict[str, str]]:
    errors = []
    record_id = record["record_id"]
    if not record["source_hash_record_valid"]:
        errors.append(_error(record_id, "source_hash_record_valid", "not_valid"))
    import_report = record["import_report"]
    for field in ("path", "sha256"):
        if not import_report[field]:
            errors.append(_error(record_id, f"import_report.{field}", "missing"))
    if import_report["sha256"] and not _valid_sha256(import_report["sha256"]):
        errors.append(_error(record_id, "import_report.sha256", "invalid_sha256"))
    if not import_report["map_check_zero_errors"]:
        errors.append(_error(record_id, "import_report.map_check_zero_errors", "false"))
    if not import_report["import_settings_recorded"]:
        errors.append(_error(record_id, "import_report.import_settings_recorded", "false"))
    for capture in record["captures"]:
        prefix = f"captures.{capture['view_id']}"
        if not capture["capture_path"]:
            errors.append(_error(record_id, f"{prefix}.capture_path", "missing"))
        if not capture["sha256"]:
            errors.append(_error(record_id, f"{prefix}.sha256", "missing"))
        elif not _valid_sha256(capture["sha256"]):
            errors.append(_error(record_id, f"{prefix}.sha256", "invalid_sha256"))
        if not capture["approved"]:
            errors.append(_error(record_id, f"{prefix}.approved", "false"))
    for review in record["reviews"]:
        prefix = f"reviews.{review['domain_id']}"
        if not review["reviewer"] or not review["review_date"]:
            errors.append(_error(record_id, prefix, "reviewer_or_date_missing"))
        if not review["approved"]:
            errors.append(_error(record_id, f"{prefix}.approved", "false"))
        if not review["evidence"]:
            errors.append(_error(record_id, f"{prefix}.evidence", "missing"))
    performance = record["performance_evidence"]
    for field in ("desktop_profile", "vr_profile"):
        if not performance[field]:
            errors.append(_error(record_id, f"performance_evidence.{field}", "missing"))
    if not performance["desktop_passed"]:
        errors.append(_error(record_id, "performance_evidence.desktop_passed", "false"))
    if not performance["vr_passed"]:
        errors.append(_error(record_id, "performance_evidence.vr_passed", "false"))
    return errors


def _record_fully_approved(record: dict[str, Any]) -> bool:
    return not _validate_import_record(record)


def _unreal_destination_root(river_id: str, candidate_id: str) -> str:
    return (
        "/Game/RaftSim/Environment/ExternalReview/B2/"
        f"{_pascal_case(river_id)}/{_pascal_case(candidate_id)}"
    )


def _pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)


def _error(record_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "field": field,
        "reason": reason,
    }


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
