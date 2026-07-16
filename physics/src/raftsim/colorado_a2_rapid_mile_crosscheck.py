"""Build and validate the Colorado A2 major-rapid mile cross-check template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .colorado_a2_centerline_decision import (
    COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH,
)
from .colorado_a2_full_reach_window_plan import (
    COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
    METER_PER_RIVER_MILE,
    build_colorado_a2_full_reach_window_plan,
)


COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/review/"
    "full_reach_rapid_mile_crosscheck_template.json"
)
COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/review/"
    "full_reach_rapid_mile_crosscheck_validation_report.json"
)
COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_SCHEMA = (
    "raftsim.colorado.a2_rapid_mile_crosscheck_template.v1"
)
COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_SCHEMA = (
    "raftsim.colorado.a2_rapid_mile_crosscheck_validation_report.v1"
)

_REQUIRED_SOURCE_CHECKS = (
    "nps_or_gcmrc_river_mile_reference",
    "usgs_hydraulic_map_or_geospatial_reference",
    "grand_canyon_oarsman_or_guide_review",
    "published_guide_or_secondary_index_crosscheck",
)


def build_colorado_a2_rapid_mile_crosscheck_template(repo_root: Path) -> dict[str, Any]:
    """Build an empty fail-closed rapid-mile cross-check template."""

    window_plan = build_colorado_a2_full_reach_window_plan(repo_root)
    rapid_records = [
        _rapid_record(assignment)
        for assignment in window_plan["rapid_assignments"]
    ]
    return {
        "schema": COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A2",
        "river_id": window_plan["river_id"],
        "display_name": window_plan["display_name"],
        "status": "empty_rapid_mile_crosscheck_template_no_stationing_promotion",
        "production_promoted": False,
        "source_contracts": {
            "window_plan": COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
            "centerline_decision_template": COLORADO_A2_CENTERLINE_DECISION_TEMPLATE_RELATIVE_PATH,
        },
        "rapid_count": len(rapid_records),
        "required_source_checks": list(_REQUIRED_SOURCE_CHECKS),
        "acceptable_default_tolerance_m": 150.0,
        "rapid_records": rapid_records,
        "validation_contract": {
            "template_is_empty": True,
            "every_catalog_rapid_must_have_record": True,
            "every_record_must_include_all_required_source_checks": True,
            "all_required_source_checks_must_approve": True,
            "reviewed_river_mile_and_station_must_be_recorded": True,
            "station_delta_m_must_be_within_record_tolerance": True,
            "unresolved_source_disagreement_blocks_stationing": True,
            "may_restation_from_empty_template": False,
            "may_bind_editor_geometry_from_empty_template": False,
            "may_bind_solver_windows_from_empty_template": False,
        },
        "promotion_gate": {
            "can_restation_major_rapids": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "complete_when": [
                "each rapid has NPS/GCMRC, USGS/geospatial, oarsman/guide, and guide/index checks",
                "each check records source, date, reviewed mile or geometry, evidence, and approval",
                "reviewed station deltas are within per-record tolerance or disagreement is explicitly resolved",
                "no record has unresolved source disagreement",
            ],
        },
    }


def write_colorado_a2_rapid_mile_crosscheck_template(repo_root: Path) -> Path:
    payload = build_colorado_a2_rapid_mile_crosscheck_template(repo_root)
    path = repo_root / COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_colorado_a2_rapid_mile_crosscheck_validation_report(
    repo_root: Path,
    crosscheck_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a rapid-mile cross-check payload without promoting A2."""

    template = (
        crosscheck_payload
        if crosscheck_payload is not None
        else build_colorado_a2_rapid_mile_crosscheck_template(repo_root)
    )
    errors = []
    for record in template["rapid_records"]:
        errors.extend(_record_errors(record))
    crosscheck_valid = not errors
    return {
        "schema": COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A2",
        "river_id": template["river_id"],
        "display_name": template["display_name"],
        "status": (
            "rapid_mile_crosscheck_valid_manual_restation_allowed"
            if crosscheck_valid
            else "rapid_mile_crosscheck_incomplete_stationing_promotion_blocked"
        ),
        "production_promoted": False,
        "source_template": COLORADO_A2_RAPID_MILE_CROSSCHECK_TEMPLATE_RELATIVE_PATH,
        "crosscheck_valid": crosscheck_valid,
        "validation_error_count": len(errors),
        "rapid_count": len(template["rapid_records"]),
        "passing_rapid_count": sum(
            1 for record in template["rapid_records"] if not _record_errors(record)
        ),
        "errors": errors,
        "promotion_permissions": {
            "can_restation_major_rapids": crosscheck_valid,
            "can_bind_editor_geometry": crosscheck_valid,
            "can_generate_rapid_water_windows": crosscheck_valid,
            "can_bind_solver_windows": crosscheck_valid,
            "can_promote_from_validation_report_alone": False,
            "manual_review_still_required_after_valid_result": True,
        },
        "promotion_gate": {
            "can_promote_current_published_mile_stations": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_solver_windows_from_empty_or_invalid_crosscheck": False,
            "next_after_valid_result": [
                "regenerate_named_rapid_stationing",
                "regenerate_editor_markers",
                "generate_rapid_water_windows",
                "run_oarsman_or_guide_visual_review",
            ],
        },
    }


def write_colorado_a2_rapid_mile_crosscheck_validation_report(repo_root: Path) -> Path:
    payload = build_colorado_a2_rapid_mile_crosscheck_validation_report(repo_root)
    path = repo_root / COLORADO_A2_RAPID_MILE_CROSSCHECK_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _rapid_record(assignment: dict[str, Any]) -> dict[str, Any]:
    planning_station_m = float(assignment["planning_station_m"])
    return {
        "rapid_name": assignment["name"],
        "aliases": assignment["aliases"],
        "class": assignment["class"],
        "feature_tags": assignment["feature_tags"],
        "review_priority": assignment["review_priority"],
        "assigned_window_id": assignment["assigned_window_id"],
        "published_river_mile": assignment["published_river_mile"],
        "planning_station_m": planning_station_m,
        "reviewed_river_mile": None,
        "reviewed_station_m": None,
        "station_delta_m": None,
        "acceptable_tolerance_m": 150.0,
        "exact_stationing_promoted": False,
        "editor_binding_enabled": False,
        "solver_window_enabled": False,
        "unresolved_source_disagreement": True,
        "source_checks": {
            check_id: _empty_source_check(check_id)
            for check_id in _REQUIRED_SOURCE_CHECKS
        },
        "review_notes": "",
    }


def _empty_source_check(check_id: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "source_title_or_reviewer": "",
        "source_url_or_report": "",
        "checked_on": "",
        "reviewed_river_mile": None,
        "reviewed_station_m": None,
        "evidence": [],
        "approved": False,
        "notes": "",
    }


def _record_errors(record: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    prefix = record["rapid_name"]
    missing_checks = set(_REQUIRED_SOURCE_CHECKS) - set(record["source_checks"])
    for check_id in sorted(missing_checks):
        errors.append(
            {
                "rapid_name": prefix,
                "field": f"source_checks.{check_id}",
                "reason": "required_source_check_missing",
            }
        )
    for check_id in _REQUIRED_SOURCE_CHECKS:
        if check_id in record["source_checks"]:
            errors.extend(_source_check_errors(prefix, record["source_checks"][check_id]))
    if record["reviewed_river_mile"] is None:
        errors.append(
            {
                "rapid_name": prefix,
                "field": "reviewed_river_mile",
                "reason": "reviewed_river_mile_missing",
            }
        )
    if record["reviewed_station_m"] is None:
        errors.append(
            {
                "rapid_name": prefix,
                "field": "reviewed_station_m",
                "reason": "reviewed_station_m_missing",
            }
        )
    if record["station_delta_m"] is None:
        errors.append(
            {
                "rapid_name": prefix,
                "field": "station_delta_m",
                "reason": "station_delta_missing",
            }
        )
    elif abs(float(record["station_delta_m"])) > float(record["acceptable_tolerance_m"]):
        errors.append(
            {
                "rapid_name": prefix,
                "field": "station_delta_m",
                "reason": "station_delta_exceeds_tolerance",
            }
        )
    if record["unresolved_source_disagreement"]:
        errors.append(
            {
                "rapid_name": prefix,
                "field": "unresolved_source_disagreement",
                "reason": "source_disagreement_unresolved",
            }
        )
    return errors


def _source_check_errors(rapid_name: str, check: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for field in ("source_title_or_reviewer", "source_url_or_report", "checked_on"):
        if not check[field]:
            errors.append(
                {
                    "rapid_name": rapid_name,
                    "field": f"source_checks.{check['check_id']}.{field}",
                    "reason": "required_source_check_field_empty",
                }
            )
    if check["reviewed_river_mile"] is None and check["reviewed_station_m"] is None:
        errors.append(
            {
                "rapid_name": rapid_name,
                "field": f"source_checks.{check['check_id']}.reviewed_position",
                "reason": "reviewed_mile_or_station_required",
            }
        )
    if not check["evidence"]:
        errors.append(
            {
                "rapid_name": rapid_name,
                "field": f"source_checks.{check['check_id']}.evidence",
                "reason": "source_check_evidence_missing",
            }
        )
    if not check["approved"]:
        errors.append(
            {
                "rapid_name": rapid_name,
                "field": f"source_checks.{check['check_id']}.approved",
                "reason": "source_check_not_approved",
            }
        )
    return errors


def station_from_river_mile(river_mile: float) -> float:
    """Convert a Grand Canyon river-mile value to planning station meters."""

    return float(river_mile) * METER_PER_RIVER_MILE
