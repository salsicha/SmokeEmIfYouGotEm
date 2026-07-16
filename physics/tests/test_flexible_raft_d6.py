import json
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
    D6_BEHAVIORAL_SUITE_SCHEMA,
    D6_COMPARISON_REPORT_RELATIVE_PATH,
    D6_COMPARISON_REPORT_SCHEMA,
    REQUIRED_D6_FIXTURE_IDS,
    build_d6_replay_channel_probe,
    build_flexible_raft_d6_behavioral_suite,
    build_flexible_raft_d6_comparison_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flexible_raft_d6_suite_is_reproducible_and_not_promoted():
    generated = build_flexible_raft_d6_behavioral_suite()
    committed = json.loads(
        (REPO_ROOT / D6_BEHAVIORAL_SUITE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_BEHAVIORAL_SUITE_SCHEMA
    assert committed["d6_complete"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False
    assert committed["production_promoted"] is False


def test_flexible_raft_d6_suite_covers_all_required_behavioral_fixtures():
    suite = build_flexible_raft_d6_behavioral_suite()
    fixture_ids = [fixture["fixture_id"] for fixture in suite["fixtures"]]

    assert fixture_ids == list(REQUIRED_D6_FIXTURE_IDS)
    assert suite["fixture_count"] == 7
    assert set(suite["required_fixture_ids"]) == set(REQUIRED_D6_FIXTURE_IDS)


def test_flexible_raft_d6_requires_compliant_reference_and_chaos_baseline():
    suite = build_flexible_raft_d6_behavioral_suite()

    assert suite["reference_requirements"]["compliant_reference"]["status"] == "missing_measured_reference_results"
    assert suite["reference_requirements"]["chaos_rigid_baseline"]["status"] == "missing_measured_unreal_chaos_results"
    for fixture in suite["fixtures"]:
        targets = {target["target_id"]: target for target in fixture["comparison_targets"]}
        assert targets["project_chrono_or_reviewed_compliant_model"]["required"] is True
        assert targets["project_chrono_or_reviewed_compliant_model"]["status"] == "pending_measured_reference"
        assert targets["unreal_chaos_rigid_baseline"]["required"] is True
        assert targets["unreal_chaos_rigid_baseline"]["status"] == "pending_measured_chaos_baseline"
        assert fixture["can_promote"] is False


def test_flexible_raft_d6_suite_records_current_python_metrics():
    suite = build_flexible_raft_d6_behavioral_suite()
    by_id = {fixture["fixture_id"]: fixture for fixture in suite["fixtures"]}

    assert by_id["static_seat_load_sag"]["python_reference_metrics"]["max_seat_freeboard_loss_m"] > 0.0
    assert by_id["rock_pinch_wrap"]["python_reference_metrics"]["wrapping_contact_count"] >= 3
    assert by_id["upstream_tube_overwash_flip"]["python_reference_metrics"]["total_overtopping_flux_m3_s"] > 0.0
    assert by_id["post_contact_recovery"]["python_reference_metrics"]["recovering_contact_count"] > 0
    assert by_id["pressure_flow_sweeps"]["python_reference_metrics"]["sweep_case_count"] == 9


def test_flexible_raft_d6_replay_probe_exposes_d5_hashes():
    probe = build_d6_replay_channel_probe()

    assert probe["frame_count"] == 2
    assert len(probe["frame_hashes"]) == 2
    assert len(probe["replay_sha256"]) == 64


def test_flexible_raft_d6_comparison_report_is_reproducible_and_pending():
    generated = build_flexible_raft_d6_comparison_report()
    committed = json.loads(
        (REPO_ROOT / D6_COMPARISON_REPORT_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_COMPARISON_REPORT_SCHEMA
    assert committed["status"] == "blocked_pending_measured_engine_results"
    assert committed["d6_complete"] is False
    assert committed["comparison_passed"] is False
    assert committed["missing_target_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2


def test_flexible_raft_d6_comparison_report_requires_every_target_fixture_pair():
    report = build_flexible_raft_d6_comparison_report()

    for fixture in report["fixtures"]:
        assert fixture["passed"] is False
        assert fixture["target_count"] == 2
        assert {target["status"] for target in fixture["targets"]} == {"missing_measured_result"}
        assert {target["target_id"] for target in fixture["targets"]} == {
            "project_chrono_or_reviewed_compliant_model",
            "unreal_chaos_rigid_baseline",
        }


def test_flexible_raft_d6_comparison_harness_accepts_synthetic_measured_results():
    report = build_flexible_raft_d6_comparison_report(_synthetic_measured_results())

    assert report["all_measurements_present"] is True
    assert report["comparison_passed"] is True
    assert report["d6_complete"] is False
    assert report["promotion_gate"]["may_mark_d6_complete"] is True
    assert {fixture["passed"] for fixture in report["fixtures"]} == {True}
    for fixture in report["fixtures"]:
        target_statuses = {target["target_id"]: target["status"] for target in fixture["targets"]}
        assert target_statuses["project_chrono_or_reviewed_compliant_model"] == "passed_numeric_equivalence"
        assert target_statuses["unreal_chaos_rigid_baseline"] == "recorded_baseline_delta"


def test_flexible_raft_d6_comparison_harness_flags_compliant_reference_metric_delta():
    measured = _synthetic_measured_results()
    measured["project_chrono_or_reviewed_compliant_model"]["static_seat_load_sag"]["metrics"][
        "raft_width_m"
    ] *= 2.0

    report = build_flexible_raft_d6_comparison_report(measured)
    by_id = {fixture["fixture_id"]: fixture for fixture in report["fixtures"]}
    static_targets = {
        target["target_id"]: target for target in by_id["static_seat_load_sag"]["targets"]
    }

    assert report["comparison_passed"] is False
    assert by_id["static_seat_load_sag"]["passed"] is False
    assert static_targets["project_chrono_or_reviewed_compliant_model"]["status"] == "failed_numeric_equivalence"
    assert static_targets["project_chrono_or_reviewed_compliant_model"]["metric_summary"]["failed_metric_count"] >= 1
    assert static_targets["unreal_chaos_rigid_baseline"]["status"] == "recorded_baseline_delta"


def _synthetic_measured_results() -> dict[str, dict[str, dict[str, object]]]:
    suite = build_flexible_raft_d6_behavioral_suite()
    measured: dict[str, dict[str, dict[str, object]]] = {
        "project_chrono_or_reviewed_compliant_model": {},
        "unreal_chaos_rigid_baseline": {},
    }
    for fixture in suite["fixtures"]:
        for target_id in measured:
            measured[target_id][fixture["fixture_id"]] = {
                "source_report": f"synthetic/{target_id}/{fixture['fixture_id']}.json",
                "telemetry_sha256": "a" * 64,
                "engine_version": "synthetic-test",
                "metrics": json.loads(json.dumps(fixture["python_reference_metrics"])),
            }
    return measured
