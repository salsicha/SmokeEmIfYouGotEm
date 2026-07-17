import json
from pathlib import Path

from raftsim.examples.merge_photoreal_b2_asset_promotion_decision_sidecar import (
    main as merge_b2_asset_promotion_decision_sidecar_main,
)
from raftsim.photoreal_b2_asset_promotion_decision import (
    build_b2_asset_promotion_decision_validation_report,
)
from raftsim.photoreal_b2_asset_promotion_decision_sidecar import (
    B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_RELATIVE_PATH,
    B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_SCHEMA,
    B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_RELATIVE_PATH,
    B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_SCHEMA,
    B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS,
    build_b2_asset_promotion_decision_sidecar_merge_report,
    build_b2_asset_promotion_decision_sidecar_template,
    merge_b2_asset_promotion_decision_sidecar,
)
from raftsim.photoreal_b2_asset_promotion_readiness import (
    build_b2_asset_promotion_readiness_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (
            REPO_ROOT / B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def _load_merge_report() -> dict:
    return json.loads(
        (
            REPO_ROOT / B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_b2_asset_promotion_decision_sidecar_template_is_reproducible_and_empty():
    generated = build_b2_asset_promotion_decision_sidecar_template()
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == B2_ASSET_PROMOTION_DECISION_SIDECAR_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_b2_asset_promotion_decision_sidecar_no_river_promoted"
    assert committed["production_promoted"] is False
    assert committed["river_decision_count"] == 5
    assert committed["promotion_gate"]["can_mark_any_b2_complete_from_empty_sidecar"] is False
    assert committed["promotion_gate"]["can_run_corridor_substitution_from_empty_sidecar"] is False
    for decision in committed["river_decisions"]:
        assert decision["plan_checkbox_marked_complete"] is False
        assert decision["corridor_substitution_executed"] is False


def test_b2_asset_promotion_decision_sidecar_merge_report_is_reproducible_and_blocked():
    generated = build_b2_asset_promotion_decision_sidecar_merge_report()
    committed = _load_merge_report()

    assert generated == committed
    assert committed["schema"] == B2_ASSET_PROMOTION_DECISION_SIDECAR_MERGE_REPORT_SCHEMA
    assert committed["status"] == "b2_asset_promotion_decision_sidecar_incomplete_promotion_blocked"
    assert committed["production_promoted"] is False
    assert committed["sidecar_decision_count"] == 5
    assert committed["sidecar_error_count"] == 0
    assert committed["merged_validation"]["decisions_valid"] is False
    assert committed["merged_validation"]["readiness_blocked_river_count"] == 5
    assert committed["promotion_permissions"]["can_run_corridor_substitution"] is False
    assert committed["promotion_gate"]["can_update_plan_checkboxes_from_sidecar_alone"] is False


def test_b2_asset_promotion_decision_sidecar_accepts_complete_ready_payload():
    readiness = _complete_readiness_payload()
    payload = _complete_sidecar_payload(readiness)
    merged = merge_b2_asset_promotion_decision_sidecar(payload)
    validation = build_b2_asset_promotion_decision_validation_report(merged, readiness)
    report = build_b2_asset_promotion_decision_sidecar_merge_report(payload, readiness)

    assert validation["decisions_valid"] is True
    assert validation["summary"]["valid_decision_count"] == 5
    assert report["status"] == B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS
    assert report["sidecar_error_count"] == 0
    assert report["merged_validation"]["validation_error_count"] == 0
    assert report["promotion_permissions"]["can_run_corridor_substitution"] is True
    assert report["promotion_permissions"]["can_mark_south_fork_b2_complete"] is True
    assert report["promotion_permissions"]["can_mark_colorado_b2_complete"] is True
    assert report["promotion_permissions"]["can_mark_pacuare_b2_complete"] is True
    assert report["promotion_permissions"]["can_mark_futaleufu_b2_complete"] is True
    assert report["promotion_permissions"]["can_mark_chilko_b2_complete"] is True
    assert report["promotion_gate"]["can_update_plan_checkboxes_from_sidecar_alone"] is False


def test_b2_asset_promotion_decision_sidecar_rejects_completion_shortcuts():
    readiness = _complete_readiness_payload()
    payload = _complete_sidecar_payload(readiness)
    first = payload["river_decisions"][0]
    first["plan_checkbox_marked_complete"] = True
    first["corridor_substitution_executed"] = True
    report = build_b2_asset_promotion_decision_sidecar_merge_report(payload, readiness)

    assert report["status"] == "b2_asset_promotion_decision_sidecar_incomplete_promotion_blocked"
    assert report["promotion_permissions"]["can_run_corridor_substitution"] is False
    assert {
        "river_id": first["river_id"],
        "field": "plan_checkbox_marked_complete",
        "reason": "plan_checkbox_update_requires_separate_manual_step",
    } in report["sidecar_errors"]
    assert {
        "river_id": first["river_id"],
        "field": "corridor_substitution_executed",
        "reason": "corridor_substitution_requires_separate_execution_step",
    } in report["sidecar_errors"]


def test_b2_asset_promotion_decision_sidecar_merge_cli_writes_outputs_for_valid_sidecar(
    tmp_path,
):
    readiness = _complete_readiness_payload()
    payload = _complete_sidecar_payload(readiness)
    sidecar_path = tmp_path / "filled_asset_promotion_decision_sidecar.json"
    readiness_path = tmp_path / "ready_asset_promotion_readiness.json"
    output_path = tmp_path / "merged_asset_promotion_decision.json"
    report_path = tmp_path / "asset_promotion_decision_sidecar_merge_report.json"
    validation_path = tmp_path / "asset_promotion_decision_validation_report.json"
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    readiness_path.write_text(json.dumps(readiness), encoding="utf-8")

    exit_code = merge_b2_asset_promotion_decision_sidecar_main(
        [
            "--sidecar",
            str(sidecar_path),
            "--readiness",
            str(readiness_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
            "--validation-report",
            str(validation_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert report_path.exists()
    assert validation_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert report["status"] == B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS
    assert validation["decisions_valid"] is True
    assert validation["summary"]["valid_decision_count"] == 5


def test_b2_asset_promotion_decision_sidecar_merge_cli_blocks_current_readiness(
    tmp_path,
):
    readiness = _complete_readiness_payload()
    payload = _complete_sidecar_payload(readiness)
    sidecar_path = tmp_path / "filled_asset_promotion_decision_sidecar.json"
    output_path = tmp_path / "merged_asset_promotion_decision.json"
    report_path = tmp_path / "asset_promotion_decision_sidecar_merge_report.json"
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = merge_b2_asset_promotion_decision_sidecar_main(
        [
            "--sidecar",
            str(sidecar_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1
    assert report_path.exists()
    assert not output_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "b2_asset_promotion_decision_sidecar_incomplete_promotion_blocked"
    assert report["merged_validation"]["decisions_valid"] is False
    assert report["merged_validation"]["readiness_blocked_river_count"] == 5


def _complete_readiness_payload() -> dict:
    readiness = build_b2_asset_promotion_readiness_report()
    readiness["summary"]["ready_river_count"] = 5
    readiness["summary"]["blocked_river_count"] = 0
    for river in readiness["rivers"]:
        river["promotion_ready"] = True
        river["source_hash_failing_record_count"] = 0
        river["import_review_failing_record_count"] = 0
        river["blocking_reasons"] = []
        for key in river["gate_status"]:
            river["gate_status"][key] = True
    return readiness


def _complete_sidecar_payload(readiness: dict) -> dict:
    payload = build_b2_asset_promotion_decision_sidecar_template()
    for decision in payload["river_decisions"]:
        river = next(
            river
            for river in readiness["rivers"]
            if river["river_id"] == decision["river_id"]
        )
        decision.update(
            {
                "decision_status": "approved",
                "decision_owner": "owner",
                "decision_date": "2026-07-16",
                "approved_for_corridor_substitution": True,
                "selected_candidate_ids": [f"{decision['river_id']}:candidate"],
                "source_hash_record_ids": [
                    f"{decision['river_id']}:source:{index}"
                    for index in range(river["source_hash_record_count"])
                ],
                "import_review_record_ids": [
                    f"{decision['river_id']}:import:{index}"
                    for index in range(river["import_review_record_count"])
                ],
                "promotion_ready": True,
            }
        )
        for signoff in decision["reviewer_signoff"].values():
            signoff.update(
                {
                    "reviewer": "reviewer",
                    "review_date": "2026-07-16",
                    "approved": True,
                    "evidence": ["review/evidence.json"],
                    "notes": "synthetic complete sidecar decision",
                }
            )
    return payload
