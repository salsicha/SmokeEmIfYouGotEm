"""Build and merge B2 per-river asset-promotion decision sidecars."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .photoreal_b2_asset_promotion_decision import (
    B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH,
    B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH,
    build_b2_asset_promotion_decision_template,
    build_b2_asset_promotion_decision_validation_report,
)
from .photoreal_b2_asset_promotion_readiness import (
    B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
    build_b2_asset_promotion_readiness_report,
)


B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_asset_promotion_decision_sidecar_template.json"
)
B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_asset_promotion_decision_sidecar_merge_report.json"
)
B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_asset_promotion_decision_sidecar_template.v1"
)
B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_SCHEMA = (
    "raftsim.photoreal.b2_asset_promotion_decision_sidecar_merge_report.v1"
)
B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS = (
    "b2_asset_promotion_decision_sidecar_valid_manual_plan_update_allowed"
)
B2_ASSET_PROMOTION_DECISION_SIDECAR_BLOCKED_STATUS = (
    "b2_asset_promotion_decision_sidecar_incomplete_promotion_blocked"
)

_MERGE_FIELDS = (
    "decision_status",
    "decision_owner",
    "decision_date",
    "approved_for_corridor_substitution",
    "selected_candidate_ids",
    "source_hash_record_ids",
    "import_review_record_ids",
    "promotion_ready",
    "notes",
    "reviewer_signoff",
)


def build_b2_asset_promotion_decision_sidecar_template() -> dict[str, Any]:
    """Build a fillable owner-review sidecar for B2 promotion decisions."""

    decision_template = build_b2_asset_promotion_decision_template()
    decisions = [
        _sidecar_river_decision(decision)
        for decision in decision_template["river_decisions"]
    ]
    return {
        "schema": B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_b2_asset_promotion_decision_sidecar_no_river_promoted",
        "production_promoted": False,
        "source_decision_template": B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH,
        "source_decision_validation_report": (
            B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH
        ),
        "source_readiness_report": B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
        "required_review_roles": decision_template["required_review_roles"],
        "river_decision_count": len(decisions),
        "river_decisions": decisions,
        "sidecar_contract": {
            "river_ids_must_match_decision_template": True,
            "readiness_report_must_mark_river_promotion_ready": True,
            "review_roles_must_match_decision_template": True,
            "source_hash_and_import_record_ids_must_cover_readiness_counts": True,
            "sidecar_may_not_mark_plan_checkboxes_complete": True,
            "sidecar_may_not_execute_corridor_substitution": True,
            "manual_plan_checkbox_update_required_after_valid_decisions": True,
        },
        "promotion_gate": {
            "can_mark_any_b2_complete_from_empty_sidecar": False,
            "can_run_corridor_substitution_from_empty_sidecar": False,
            "complete_when": [
                "the readiness report marks each river promotion_ready",
                "the sidecar records a reviewed owner decision for each river",
                "selected candidate, source-hash, and import-review ids cover readiness counts",
                "every required review role approves with evidence",
                "the sidecar merge report and canonical decision validation report are green",
                "the plan checkbox update is performed as a separate manual step",
            ],
        },
    }


def write_b2_asset_promotion_decision_sidecar_template(repo_root: Path) -> Path:
    payload = build_b2_asset_promotion_decision_sidecar_template()
    path = repo_root / B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def merge_b2_asset_promotion_decision_sidecar(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge a decision sidecar into the canonical B2 decision template."""

    merged = deepcopy(build_b2_asset_promotion_decision_template())
    sidecar = sidecar_payload or build_b2_asset_promotion_decision_sidecar_template()
    targets = {decision["river_id"]: decision for decision in merged["river_decisions"]}
    for decision in sidecar["river_decisions"]:
        target = targets.get(decision["river_id"])
        if target is None:
            continue
        for field in _MERGE_FIELDS:
            target[field] = deepcopy(decision[field])
    return merged


def build_b2_asset_promotion_decision_sidecar_merge_report(
    sidecar_payload: dict[str, Any] | None = None,
    readiness_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a B2 decision sidecar merge without updating the plan."""

    sidecar = sidecar_payload or build_b2_asset_promotion_decision_sidecar_template()
    readiness = readiness_payload or build_b2_asset_promotion_readiness_report()
    sidecar_errors = _sidecar_errors(sidecar)
    merged = merge_b2_asset_promotion_decision_sidecar(sidecar)
    validation = build_b2_asset_promotion_decision_validation_report(merged, readiness)
    valid = not sidecar_errors and validation["decisions_valid"]
    return {
        "schema": B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": (
            B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS
            if valid
            else B2_ASSET_PROMOTION_DECISION_SIDECAR_BLOCKED_STATUS
        ),
        "production_promoted": False,
        "source_sidecar_template": (
            B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_RELATIVE_PATH
        ),
        "source_decision_template": B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH,
        "source_decision_validation_report": (
            B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH
        ),
        "source_readiness_report": B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
        "sidecar_decision_count": len(sidecar["river_decisions"]),
        "sidecar_error_count": len(sidecar_errors),
        "sidecar_errors": sidecar_errors,
        "merged_validation": {
            "decisions_valid": validation["decisions_valid"],
            "validation_error_count": validation["validation_error_count"],
            "failing_river_count": validation["failing_river_count"],
            "valid_decision_count": validation["summary"]["valid_decision_count"],
            "readiness_ready_river_count": validation["summary"][
                "readiness_ready_river_count"
            ],
            "readiness_blocked_river_count": validation["summary"][
                "readiness_blocked_river_count"
            ],
        },
        "promotion_permissions": {
            "can_run_corridor_substitution": valid,
            "can_mark_south_fork_b2_complete": _gate_value(
                validation,
                valid,
                "can_mark_south_fork_b2_complete",
            ),
            "can_mark_colorado_b2_complete": _gate_value(
                validation,
                valid,
                "can_mark_colorado_b2_complete",
            ),
            "can_mark_pacuare_b2_complete": _gate_value(
                validation,
                valid,
                "can_mark_pacuare_b2_complete",
            ),
            "can_mark_futaleufu_b2_complete": _gate_value(
                validation,
                valid,
                "can_mark_futaleufu_b2_complete",
            ),
            "can_mark_chilko_b2_complete": _gate_value(
                validation,
                valid,
                "can_mark_chilko_b2_complete",
            ),
        },
        "promotion_gate": {
            "can_update_plan_checkboxes_from_sidecar_alone": False,
            "can_replace_manual_owner_review": False,
            "manual_plan_checkbox_update_required_after_valid_decisions": True,
        },
    }


def write_b2_asset_promotion_decision_sidecar_merge_report(repo_root: Path) -> Path:
    payload = build_b2_asset_promotion_decision_sidecar_merge_report()
    path = repo_root / B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _sidecar_river_decision(decision: dict[str, Any]) -> dict[str, Any]:
    sidecar_decision = deepcopy(decision)
    sidecar_decision["plan_checkbox_marked_complete"] = False
    sidecar_decision["corridor_substitution_executed"] = False
    return sidecar_decision


def _sidecar_errors(sidecar: dict[str, Any]) -> list[dict[str, str]]:
    template = build_b2_asset_promotion_decision_template()
    expected = {decision["river_id"]: decision for decision in template["river_decisions"]}
    expected_roles = set(template["required_review_roles"])
    errors: list[dict[str, str]] = []
    ids = [decision["river_id"] for decision in sidecar["river_decisions"]]
    for river_id in sorted(set(expected) - set(ids)):
        errors.append(_error(river_id, "river_decisions", "sidecar_river_missing"))
    for river_id in sorted(set(ids) - set(expected)):
        errors.append(_error(river_id, "river_decisions", "unknown_sidecar_river"))
    if len(ids) != len(set(ids)):
        errors.append(_error("", "river_decisions", "duplicate_sidecar_river"))
    if set(sidecar["required_review_roles"]) != expected_roles:
        errors.append(_error("", "required_review_roles", "review_roles_mismatch"))
    for decision in sidecar["river_decisions"]:
        expected_decision = expected.get(decision["river_id"])
        if expected_decision is None:
            continue
        if decision["decision_id"] != expected_decision["decision_id"]:
            errors.append(_error(decision["river_id"], "decision_id", "sidecar_field_mismatch"))
        if set(decision["reviewer_signoff"]) != expected_roles:
            errors.append(
                _error(
                    decision["river_id"],
                    "reviewer_signoff",
                    "review_roles_mismatch",
                )
            )
        if decision["plan_checkbox_marked_complete"]:
            errors.append(
                _error(
                    decision["river_id"],
                    "plan_checkbox_marked_complete",
                    "plan_checkbox_update_requires_separate_manual_step",
                )
            )
        if decision["corridor_substitution_executed"]:
            errors.append(
                _error(
                    decision["river_id"],
                    "corridor_substitution_executed",
                    "corridor_substitution_requires_separate_execution_step",
                )
            )
    return errors


def _gate_value(validation: dict[str, Any], valid: bool, gate_name: str) -> bool:
    return valid and validation["promotion_gate"][gate_name]


def _error(river_id: str, field: str, reason: str) -> dict[str, str]:
    return {
        "river_id": river_id,
        "field": field,
        "reason": reason,
    }
