import json
from pathlib import Path

from raftsim.photoreal_b2_asset_promotion_decision import (
    B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH,
    B2_ASSET_PROMOTION_DECISION_TEMPLATE_SCHEMA,
    B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH,
    B2_ASSET_PROMOTION_DECISION_VALIDATION_SCHEMA,
    build_b2_asset_promotion_decision_template,
    build_b2_asset_promotion_decision_validation_report,
)
from raftsim.photoreal_b2_asset_promotion_readiness import (
    B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH,
    build_b2_asset_promotion_readiness_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (REPO_ROOT / B2_ASSET_PROMOTION_DECISION_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation() -> dict:
    return json.loads(
        (REPO_ROOT / B2_ASSET_PROMOTION_DECISION_VALIDATION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_asset_promotion_decision_template_is_reproducible_and_empty():
    generated = build_b2_asset_promotion_decision_template()
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == B2_ASSET_PROMOTION_DECISION_TEMPLATE_SCHEMA
    assert committed["status"] == "empty_b2_asset_promotion_decision_template_no_river_promoted"
    assert committed["production_promoted"] is False
    assert committed["source_readiness_report"] == B2_ASSET_PROMOTION_READINESS_RELATIVE_PATH
    assert committed["river_decision_count"] == 5


def test_b2_asset_promotion_decision_template_covers_five_rivers():
    template = build_b2_asset_promotion_decision_template()
    decisions = {decision["river_id"]: decision for decision in template["river_decisions"]}

    assert set(decisions) == {
        "south_fork_american_chili_bar",
        "colorado_river_grand_canyon_rowing",
        "pacuare_river_costa_rica",
        "futaleufu_river_chile",
        "chilko_river_lava_canyon",
    }
    for decision in decisions.values():
        assert decision["decision_status"] == "not_recorded"
        assert decision["approved_for_corridor_substitution"] is False
        assert decision["selected_candidate_ids"] == []
        assert decision["source_hash_record_ids"] == []
        assert decision["import_review_record_ids"] == []
        assert decision["promotion_ready"] is False
        assert set(decision["reviewer_signoff"]) == set(template["required_review_roles"])


def test_b2_asset_promotion_decision_validation_is_reproducible_and_blocked():
    generated = build_b2_asset_promotion_decision_validation_report()
    committed = _load_validation()

    assert generated == committed
    assert committed["schema"] == B2_ASSET_PROMOTION_DECISION_VALIDATION_SCHEMA
    assert committed["status"] == "b2_asset_promotion_decisions_incomplete_promotion_blocked"
    assert committed["decisions_valid"] is False
    assert committed["production_promoted"] is False
    assert committed["failing_river_count"] == 5


def test_b2_asset_promotion_decision_validation_blocks_current_empty_decisions():
    report = _load_validation()

    assert report["summary"]["river_decision_count"] == 5
    assert report["summary"]["valid_decision_count"] == 0
    assert report["summary"]["readiness_ready_river_count"] == 0
    assert report["summary"]["readiness_blocked_river_count"] == 5
    assert report["validation_error_count"] > 5
    assert report["promotion_gate"]["can_run_corridor_substitution"] is False
    assert not any(
        value
        for key, value in report["promotion_gate"].items()
        if key.startswith("can_mark_")
    )


def test_b2_asset_promotion_decision_validation_accepts_complete_ready_payload():
    readiness = _complete_readiness_payload()
    template = _complete_decision_payload(readiness)
    report = build_b2_asset_promotion_decision_validation_report(template, readiness)

    assert report["status"] == "b2_asset_promotion_decisions_valid_manual_plan_update_allowed"
    assert report["decisions_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["failing_river_count"] == 0
    assert report["summary"]["valid_decision_count"] == 5
    assert report["promotion_gate"]["can_run_corridor_substitution"] is True
    assert report["promotion_gate"]["can_mark_south_fork_b2_complete"] is True
    assert report["promotion_gate"]["can_mark_colorado_b2_complete"] is True
    assert report["promotion_gate"]["can_mark_pacuare_b2_complete"] is True
    assert report["promotion_gate"]["can_mark_futaleufu_b2_complete"] is True
    assert report["promotion_gate"]["can_mark_chilko_b2_complete"] is True


def test_b2_asset_promotion_decision_validation_rejects_partial_review_signoff():
    readiness = _complete_readiness_payload()
    template = _complete_decision_payload(readiness)
    template["river_decisions"][0]["reviewer_signoff"][
        "owner_or_producer_acceptance"
    ]["approved"] = False
    report = build_b2_asset_promotion_decision_validation_report(template, readiness)

    assert report["decisions_valid"] is False
    assert {
        "river_id": template["river_decisions"][0]["river_id"],
        "field": "reviewer_signoff.owner_or_producer_acceptance.approved",
        "reason": "false",
    } in report["decision_errors"]


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


def _complete_decision_payload(readiness: dict) -> dict:
    template = build_b2_asset_promotion_decision_template()
    for decision in template["river_decisions"]:
        river = next(
            river for river in readiness["rivers"] if river["river_id"] == decision["river_id"]
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
                    "notes": "synthetic complete test decision",
                }
            )
    return template
