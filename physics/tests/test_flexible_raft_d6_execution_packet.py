import json
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPARISON_REPORT_RELATIVE_PATH,
    D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
    D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
    D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
    REQUIRED_D6_FIXTURE_IDS,
)
from raftsim.flexible_raft_d6_execution_packet import (
    D6_EXECUTION_PACKET_RELATIVE_PATH,
    D6_EXECUTION_PACKET_SCHEMA,
    build_flexible_raft_d6_execution_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flexible_raft_d6_execution_packet_is_reproducible_and_not_promoted():
    generated = build_flexible_raft_d6_execution_packet()
    committed = json.loads(
        (REPO_ROOT / D6_EXECUTION_PACKET_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_EXECUTION_PACKET_SCHEMA
    assert committed["status"] == "external_engine_execution_packet_ready_measurements_missing"
    assert committed["d6_complete"] is False
    assert committed["production_promoted"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False
    assert committed["promotion_gate"]["may_drive_runtime_gameplay"] is False


def test_flexible_raft_d6_execution_packet_tracks_all_pending_external_jobs():
    packet = build_flexible_raft_d6_execution_packet()
    summary = packet["summary"]

    assert summary["fixture_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert summary["target_count"] == 2
    assert summary["execution_job_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert summary["pending_external_job_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert summary["committed_report_missing_target_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert summary["python_only_can_satisfy_d6"] is False
    assert summary["can_promote_d6_now"] is False


def test_flexible_raft_d6_execution_packet_links_source_artifacts():
    packet = build_flexible_raft_d6_execution_packet()
    artifacts = packet["source_artifacts"]

    assert artifacts["measurement_manifest"] == D6_MEASUREMENT_MANIFEST_RELATIVE_PATH
    assert artifacts["fixture_input_package"] == D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH
    assert artifacts["measured_results_template"] == D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH
    assert artifacts["compliant_measured_results_sidecar_template"] == (
        D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
    )
    assert artifacts["compliant_measured_results_merge_report"] == (
        D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
    )
    assert artifacts["chaos_measured_results_sidecar_template"] == (
        D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
    )
    assert artifacts["chaos_measured_results_merge_report"] == (
        D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
    )
    assert artifacts["comparison_report"] == D6_COMPARISON_REPORT_RELATIVE_PATH
    assert packet["local_preparation_checks"]["can_generate_fixture_inputs"] is True
    assert packet["local_preparation_checks"]["can_generate_empty_target_sidecar_templates"] is True
    assert packet["local_preparation_checks"]["can_validate_target_sidecars_before_merge"] is True
    assert packet["local_preparation_checks"]["can_run_external_measurement_gate_with_python_only"] is False


def test_flexible_raft_d6_execution_jobs_cover_manifest_tasks_with_evidence():
    packet = build_flexible_raft_d6_execution_packet()
    jobs = packet["execution_jobs"]
    pairs = {(job["target_id"], job["fixture_id"]) for job in jobs}

    for fixture_id in REQUIRED_D6_FIXTURE_IDS:
        assert ("project_chrono_or_reviewed_compliant_model", fixture_id) in pairs
        assert ("unreal_chaos_rigid_baseline", fixture_id) in pairs

    for job in jobs:
        assert job["status"] == "pending_external_engine_run"
        assert job["fixture_input_package"] == D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH
        assert job["required_metric_count"] == len(job["required_metric_paths"])
        assert job["required_metric_count"] > 0
        assert job["current_comparison_report_state"]["status"] == "missing_measured_result"
        assert job["current_comparison_report_state"]["passed"] is False
        assert job["required_evidence"]["source_report"]["required"] is True
        assert job["required_evidence"]["telemetry_sha256"]["required"] is True
        assert job["required_evidence"]["engine_version"]["required"] is True
        assert job["required_evidence"]["metrics"]["metric_paths"] == job["required_metric_paths"]
        assert job["guardrails"]["may_substitute_python_reference"] is False
        assert job["guardrails"]["may_promote_fixture"] is False
        assert job["guardrails"]["may_ignore_missing_metric"] is False
        assert job["guardrails"]["may_ignore_missing_provenance"] is False


def test_flexible_raft_d6_execution_packet_separates_compliant_and_chaos_policies():
    packet = build_flexible_raft_d6_execution_packet()
    groups = {group["target_id"]: group for group in packet["adapter_groups"]}

    compliant = groups["project_chrono_or_reviewed_compliant_model"]
    chaos = groups["unreal_chaos_rigid_baseline"]

    assert compliant["runner_family"] == "reviewed_compliant_reference"
    assert compliant["comparison_mode"] == "bounded_numeric_equivalence"
    assert compliant["metric_deltas_are_failures"] is True
    assert compliant["adapter_must_not_substitute_python_reference"] is True
    assert compliant["required_external_runner"] is True
    assert compliant["job_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert compliant["pending_job_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert compliant["measured_results_sidecar_template"] == (
        D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
    )
    assert compliant["measured_results_merge_report"] == (
        D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
    )
    assert "merge_flexible_raft_d6_compliant_measured_results.py" in compliant[
        "sidecar_merge_command"
    ]

    assert chaos["runner_family"] == "unreal_chaos_rigid_baseline"
    assert chaos["comparison_mode"] == "baseline_delta_recording"
    assert chaos["metric_deltas_are_failures"] is False
    assert chaos["adapter_must_not_substitute_python_reference"] is True
    assert chaos["required_external_runner"] is True
    assert chaos["job_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert chaos["pending_job_count"] == len(REQUIRED_D6_FIXTURE_IDS)
    assert chaos["measured_results_sidecar_template"] == (
        D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
    )
    assert chaos["measured_results_merge_report"] == (
        D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
    )
    assert "merge_flexible_raft_d6_chaos_measured_results.py" in chaos[
        "sidecar_merge_command"
    ]


def test_flexible_raft_d6_execution_packet_blocks_runtime_until_reviewed():
    packet = build_flexible_raft_d6_execution_packet()

    blocked_actions = set(packet["blocked_actions_until_jobs_pass"])
    assert "marking D6 complete" in blocked_actions
    assert "using flexible tube deformation for scoring-critical gameplay" in blocked_actions
    assert "declaring Unreal Chaos rigid-baseline agreement" in blocked_actions
    assert packet["post_measurement_workflow"][0]["required_job_count"] == len(REQUIRED_D6_FIXTURE_IDS) * 2
    assert packet["post_measurement_workflow"][0]["allowed_to_skip_jobs"] is False
    workflow_steps = [step["step"] for step in packet["post_measurement_workflow"]]
    assert "populate_target_sidecars" in workflow_steps
    assert "validate_and_merge_target_sidecars" in workflow_steps
    merge_step = next(
        step
        for step in packet["post_measurement_workflow"]
        if step["step"] == "validate_and_merge_target_sidecars"
    )
    assert set(merge_step["merge_reports"]) == {
        "project_chrono_or_reviewed_compliant_model",
        "unreal_chaos_rigid_baseline",
    }
    assert packet["post_measurement_workflow"][-1]["may_mark_d6_complete_before_review"] is False
