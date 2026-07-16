"""Build B2 per-river asset-promotion decision templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_asset_promotion_readiness import (
    B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
    build_b2_asset_promotion_readiness_report,
)


B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_asset_promotion_decision_template.json"
)
B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_asset_promotion_decision_validation_report.json"
)
B2_ASSET_PROMOTION_DECISION_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_asset_promotion_decision_template.v1"
)
B2_ASSET_PROMOTION_DECISION_VALIDATION_SCHEMA = (
    "raftsim.photoreal.b2_asset_promotion_decision_validation.v1"
)

_REVIEW_ROLES = (
    "owner_or_producer_acceptance",
    "environment_art_direction",
    "river_guide_or_ecology_reviewer",
    "rights_or_license_reviewer",
    "hazard_readability_reviewer",
    "technical_art_import_reviewer",
    "desktop_vr_performance_reviewer",
)


def build_b2_asset_promotion_decision_template() -> dict[str, Any]:
    """Build an empty per-river B2 promotion decision template."""

    readiness = build_b2_asset_promotion_readiness_report()
    decisions = [
        _river_decision_template(river)
        for river in readiness["rivers"]
    ]
    return {
        "schema": B2_ASSET_PROMOTION_DECISION_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_b2_asset_promotion_decision_template_no_river_promoted",
        "production_promoted": False,
        "source_readiness_report": B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
        "readiness_summary": readiness["summary"],
        "required_review_roles": list(_REVIEW_ROLES),
        "river_decision_count": len(decisions),
        "river_decisions": decisions,
        "decision_contract": {
            "must_match_readiness_river_ids": True,
            "readiness_must_be_promotion_ready": True,
            "selected_candidate_ids_must_be_non_empty": True,
            "source_hash_record_ids_must_cover_readiness_records": True,
            "import_review_record_ids_must_cover_readiness_records": True,
            "all_review_roles_must_approve": True,
            "manual_owner_acceptance_required": True,
        },
        "promotion_gate": {
            "can_mark_south_fork_b2_complete": False,
            "can_mark_colorado_b2_complete": False,
            "can_mark_pacuare_b2_complete": False,
            "can_mark_futaleufu_b2_complete": False,
            "can_mark_chilko_b2_complete": False,
            "can_run_corridor_substitution": False,
            "complete_when": [
                "the source readiness report marks the river promotion_ready",
                "the river decision selects reviewed candidate assets",
                "source-hash and import/capture record ids cover the readiness counts",
                "all required review roles approve with evidence",
                "owner explicitly approves corridor substitution for the river",
            ],
        },
    }


def write_b2_asset_promotion_decision_template(repo_root: Path) -> Path:
    payload = build_b2_asset_promotion_decision_template()
    path = repo_root / B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_b2_asset_promotion_decision_validation_report(
    decision_payload: dict[str, Any] | None = None,
    readiness_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate B2 promotion decisions without changing plan checkboxes."""

    template = decision_payload or build_b2_asset_promotion_decision_template()
    readiness = readiness_payload or build_b2_asset_promotion_readiness_report()
    readiness_by_river = {river["river_id"]: river for river in readiness["rivers"]}
    decision_errors = []
    valid_decisions = 0
    for decision in template["river_decisions"]:
        errors = _validate_river_decision(decision, readiness_by_river)
        decision_errors.extend(errors)
        if not errors:
            valid_decisions += 1
    failing_river_ids = sorted({error["river_id"] for error in decision_errors})
    all_valid = not decision_errors and valid_decisions == len(readiness_by_river)
    return {
        "schema": B2_ASSET_PROMOTION_DECISION_VALIDATION_SCHEMA,
        "generated_on": "2026-07-16",
        "status": (
            "b2_asset_promotion_decisions_valid_manual_plan_update_allowed"
            if all_valid
            else "b2_asset_promotion_decisions_incomplete_promotion_blocked"
        ),
        "production_promoted": False,
        "source_decision_template": B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH,
        "source_readiness_report": B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
        "decisions_valid": all_valid,
        "validation_error_count": len(decision_errors),
        "failing_river_count": len(failing_river_ids),
        "failing_river_ids": failing_river_ids,
        "decision_errors": decision_errors,
        "summary": {
            "river_decision_count": len(template["river_decisions"]),
            "valid_decision_count": valid_decisions,
            "readiness_ready_river_count": readiness["summary"]["ready_river_count"],
            "readiness_blocked_river_count": readiness["summary"]["blocked_river_count"],
        },
        "promotion_gate": {
            "can_mark_south_fork_b2_complete": _river_valid(
                "south_fork_american_chili_bar",
                failing_river_ids,
                all_valid,
            ),
            "can_mark_colorado_b2_complete": _river_valid(
                "colorado_river_grand_canyon_rowing",
                failing_river_ids,
                all_valid,
            ),
            "can_mark_pacuare_b2_complete": _river_valid(
                "pacuare_river_costa_rica",
                failing_river_ids,
                all_valid,
            ),
            "can_mark_futaleufu_b2_complete": _river_valid(
                "futaleufu_river_chile",
                failing_river_ids,
                all_valid,
            ),
            "can_mark_chilko_b2_complete": _river_valid(
                "chilko_river_lava_canyon",
                failing_river_ids,
                all_valid,
            ),
            "can_run_corridor_substitution": all_valid,
            "manual_plan_checkbox_update_required_after_valid_decisions": True,
        },
    }


def write_b2_asset_promotion_decision_validation_report(repo_root: Path) -> Path:
    payload = build_b2_asset_promotion_decision_validation_report()
    path = repo_root / B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _river_decision_template(river: dict[str, Any]) -> dict[str, Any]:
    return {
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "decision_id": f"{river['river_id']}:b2_asset_promotion_decision",
        "decision_status": "not_recorded",
        "decision_owner": "",
        "decision_date": "",
        "approved_for_corridor_substitution": False,
        "selected_candidate_ids": [],
        "source_hash_record_ids": [],
        "import_review_record_ids": [],
        "readiness_record_counts": {
            "source_hash_record_count": river["source_hash_record_count"],
            "import_review_record_count": river["import_review_record_count"],
        },
        "reviewer_signoff": {
            role: {
                "reviewer": "",
                "review_date": "",
                "approved": False,
                "evidence": [],
                "notes": "",
            }
            for role in _REVIEW_ROLES
        },
        "promotion_ready": False,
        "notes": "",
    }


def _validate_river_decision(
    decision: dict[str, Any],
    readiness_by_river: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    river_id = decision["river_id"]
    readiness = readiness_by_river.get(river_id)
    errors = []
    if readiness is None:
        return [_error(river_id, "river_id", "not_found_in_readiness_report")]
    if not readiness["promotion_ready"]:
        errors.append(_error(river_id, "readiness.promotion_ready", "false"))
    for field in ("decision_owner", "decision_date"):
        if not decision[field]:
            errors.append(_error(river_id, field, "missing"))
    if decision["decision_status"] != "approved":
        errors.append(_error(river_id, "decision_status", "not_approved"))
    if not decision["approved_for_corridor_substitution"]:
        errors.append(_error(river_id, "approved_for_corridor_substitution", "false"))
    if not decision["selected_candidate_ids"]:
        errors.append(_error(river_id, "selected_candidate_ids", "missing"))
    if len(decision["source_hash_record_ids"]) < readiness["source_hash_record_count"]:
        errors.append(_error(river_id, "source_hash_record_ids", "insufficient_coverage"))
    if len(decision["import_review_record_ids"]) < readiness["import_review_record_count"]:
        errors.append(_error(river_id, "import_review_record_ids", "insufficient_coverage"))
    for role, signoff in decision["reviewer_signoff"].items():
        prefix = f"reviewer_signoff.{role}"
        if not signoff["reviewer"] or not signoff["review_date"]:
            errors.append(_error(river_id, prefix, "reviewer_or_date_missing"))
        if not signoff["approved"]:
            errors.append(_error(river_id, f"{prefix}.approved", "false"))
        if not signoff["evidence"]:
            errors.append(_error(river_id, f"{prefix}.evidence", "missing"))
    return errors


def _river_valid(river_id: str, failing_river_ids: list[str], all_valid: bool) -> bool:
    return all_valid and river_id not in failing_river_ids


def _error(river_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "river_id": river_id,
        "field": field,
        "reason": reason,
    }
