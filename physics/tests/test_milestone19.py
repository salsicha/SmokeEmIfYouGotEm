import json
from pathlib import Path

from raftsim.milestone19 import (
    AUTHORITY_SELECTION_DECISION,
    CHAOS_JOLT_COMPARISON_DECISION,
    COMPARISON_DIMENSIONS,
    FALLBACK_RUNTIME_ID,
    CHAOS_EXPORT_DECISION,
    CHAOS_RUNTIME_ID,
    JOLT_EXPORT_DECISION,
    JOLT_RUNTIME_ID,
    build_chaos_automation_export,
    build_chaos_jolt_comparison_report,
    build_jolt_smoke_harness_export,
    build_runtime_authority_selection_report,
    load_runtime_evaluation_contract,
    write_chaos_automation_export,
    write_chaos_jolt_comparison_report,
    write_jolt_smoke_harness_export,
    write_runtime_authority_selection_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json"
CHAOS_MANIFEST_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json"
CHAOS_SUMMARY_PATH = REPO_ROOT / "physics/reports/milestone19/chaos/summary.json"
JOLT_MANIFEST_PATH = REPO_ROOT / "physics/cpp/tests/jolt_smoke_harness_manifest.json"
JOLT_SUMMARY_PATH = REPO_ROOT / "physics/reports/milestone19/jolt/summary.json"
COMPARISON_PATH = REPO_ROOT / "physics/reports/milestone19/chaos_vs_jolt_comparison.json"
AUTHORITY_SELECTION_PATH = REPO_ROOT / "physics/reports/milestone19/runtime_authority_selection.json"
RAFT_RUNTIME_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/raft_dynamics_runtime.json"
PHYSICS_AUTHORITY_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/physics_authority_policy.json"
FIXED_STEP_BRIDGE_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/fixed_step_bridge.json"


def test_chaos_automation_export_covers_shared_contract():
    contract = load_runtime_evaluation_contract(CONTRACT_PATH)
    export = build_chaos_automation_export(contract)
    contract_fixture_ids = {
        fixture["fixture_id"]
        for fixture in contract["fixtures"]
        if CHAOS_RUNTIME_ID in fixture["applies_to"]
    }
    manifest_fixture_ids = {fixture["fixture_id"] for fixture in export.manifest["fixtures"]}
    replay_fixture_ids = {replay["fixture_id"] for replay in export.replays}

    assert export.manifest["target_runtime"] == CHAOS_RUNTIME_ID
    assert export.summary["decision"] == CHAOS_EXPORT_DECISION
    assert export.summary["authority_selection_allowed"] is False
    assert export.summary["runtime_passed_fixture_suite"] is False
    assert manifest_fixture_ids == contract_fixture_ids
    assert replay_fixture_ids == contract_fixture_ids
    assert export.summary["fixture_count"] == 6
    assert export.summary["all_fixture_samples_match_required_telemetry"] is True


def test_chaos_replay_summaries_include_required_telemetry_fields():
    contract = load_runtime_evaluation_contract(CONTRACT_PATH)
    required = set(contract["shared_fixture_contract"]["telemetry_required"])
    export = build_chaos_automation_export(contract)

    for replay in export.replays:
        assert replay["runtime_id"] == CHAOS_RUNTIME_ID
        assert replay["authoritative_evidence"] is False
        assert replay["sample_frames"]
        for frame in replay["sample_frames"]:
            assert required.issubset(frame)
            assert frame["sample_kind"] == "schema_placeholder"


def test_write_chaos_automation_export_creates_manifest_summary_and_replays(tmp_path):
    manifest_path = tmp_path / "chaos_automation_fixtures.json"
    report_dir = tmp_path / "reports" / "milestone19" / "chaos"

    export = write_chaos_automation_export(
        contract_path=CONTRACT_PATH,
        manifest_path=manifest_path,
        report_dir=report_dir,
    )

    assert manifest_path.exists()
    assert (report_dir / "summary.json").exists()
    assert (report_dir / "summary.md").exists()
    for replay in export.replays:
        replay_path = report_dir / "replays" / f"{replay['fixture_id']}.replay_summary.json"
        assert replay_path.exists()


def test_committed_chaos_export_matches_contract():
    contract = load_runtime_evaluation_contract(CONTRACT_PATH)
    contract_fixture_ids = {
        fixture["fixture_id"]
        for fixture in contract["fixtures"]
        if CHAOS_RUNTIME_ID in fixture["applies_to"]
    }
    manifest = json.loads(CHAOS_MANIFEST_PATH.read_text(encoding="utf-8"))
    summary = json.loads(CHAOS_SUMMARY_PATH.read_text(encoding="utf-8"))

    assert manifest["target_runtime"] == CHAOS_RUNTIME_ID
    assert summary["decision"] == CHAOS_EXPORT_DECISION
    assert summary["authority_selection_allowed"] is False
    assert summary["runtime_passed_fixture_suite"] is False
    assert {fixture["fixture_id"] for fixture in manifest["fixtures"]} == contract_fixture_ids
    assert {fixture["fixture_id"] for fixture in summary["fixtures"]} == contract_fixture_ids


def test_jolt_smoke_harness_export_covers_shared_contract():
    contract = load_runtime_evaluation_contract(CONTRACT_PATH)
    export = build_jolt_smoke_harness_export(contract)
    contract_fixture_ids = {
        fixture["fixture_id"]
        for fixture in contract["fixtures"]
        if JOLT_RUNTIME_ID in fixture["applies_to"]
    }
    manifest_fixture_ids = {fixture["fixture_id"] for fixture in export.manifest["fixtures"]}
    replay_fixture_ids = {replay["fixture_id"] for replay in export.replays}

    assert export.manifest["target_runtime"] == JOLT_RUNTIME_ID
    assert export.summary["decision"] == JOLT_EXPORT_DECISION
    assert export.summary["authority_selection_allowed"] is False
    assert export.summary["runtime_passed_fixture_suite"] is False
    assert manifest_fixture_ids == contract_fixture_ids
    assert replay_fixture_ids == contract_fixture_ids
    assert export.summary["fixture_count"] == 6
    assert export.summary["all_fixture_samples_match_required_telemetry"] is True


def test_write_jolt_smoke_harness_export_creates_manifest_summary_and_replays(tmp_path):
    manifest_path = tmp_path / "jolt_smoke_harness_manifest.json"
    report_dir = tmp_path / "reports" / "milestone19" / "jolt"

    export = write_jolt_smoke_harness_export(
        contract_path=CONTRACT_PATH,
        manifest_path=manifest_path,
        report_dir=report_dir,
    )

    assert manifest_path.exists()
    assert (report_dir / "summary.json").exists()
    assert (report_dir / "summary.md").exists()
    for replay in export.replays:
        replay_path = report_dir / "replays" / f"{replay['fixture_id']}.replay_summary.json"
        assert replay_path.exists()


def test_committed_jolt_export_matches_contract():
    contract = load_runtime_evaluation_contract(CONTRACT_PATH)
    contract_fixture_ids = {
        fixture["fixture_id"]
        for fixture in contract["fixtures"]
        if JOLT_RUNTIME_ID in fixture["applies_to"]
    }
    manifest = json.loads(JOLT_MANIFEST_PATH.read_text(encoding="utf-8"))
    summary = json.loads(JOLT_SUMMARY_PATH.read_text(encoding="utf-8"))

    assert manifest["target_runtime"] == JOLT_RUNTIME_ID
    assert summary["decision"] == JOLT_EXPORT_DECISION
    assert summary["authority_selection_allowed"] is False
    assert summary["runtime_passed_fixture_suite"] is False
    assert {fixture["fixture_id"] for fixture in manifest["fixtures"]} == contract_fixture_ids
    assert {fixture["fixture_id"] for fixture in summary["fixtures"]} == contract_fixture_ids


def test_chaos_jolt_comparison_blocks_authority_without_measured_telemetry():
    report = build_chaos_jolt_comparison_report(
        contract=load_runtime_evaluation_contract(CONTRACT_PATH),
        chaos_summary=json.loads(CHAOS_SUMMARY_PATH.read_text(encoding="utf-8")),
        jolt_summary=json.loads(JOLT_SUMMARY_PATH.read_text(encoding="utf-8")),
    ).report

    assert report["decision"] == CHAOS_JOLT_COMPARISON_DECISION
    assert report["fixture_coverage_match"] is True
    assert report["measured_evidence_available"] is False
    assert report["authority_selection_allowed"] is False
    assert report["runtime_passed_fixture_suite"] is False
    assert {item["dimension"] for item in report["dimension_rankings"]} == set(
        COMPARISON_DIMENSIONS
    )
    assert all(
        item["winner"] == "insufficient_measured_evidence"
        for item in report["dimension_rankings"]
    )


def test_write_chaos_jolt_comparison_report_creates_json_and_markdown(tmp_path):
    output_json = tmp_path / "chaos_vs_jolt_comparison.json"
    output_md = tmp_path / "chaos_vs_jolt_comparison.md"

    report = write_chaos_jolt_comparison_report(
        contract_path=CONTRACT_PATH,
        chaos_summary_path=CHAOS_SUMMARY_PATH,
        jolt_summary_path=JOLT_SUMMARY_PATH,
        output_json=output_json,
        output_md=output_md,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert report.report["decision"] == CHAOS_JOLT_COMPARISON_DECISION


def test_committed_chaos_jolt_comparison_matches_runtime_summaries():
    report = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    chaos_summary = json.loads(CHAOS_SUMMARY_PATH.read_text(encoding="utf-8"))
    jolt_summary = json.loads(JOLT_SUMMARY_PATH.read_text(encoding="utf-8"))

    assert report["decision"] == CHAOS_JOLT_COMPARISON_DECISION
    assert report["fixture_count"] == chaos_summary["fixture_count"] == jolt_summary["fixture_count"]
    assert report["authority_selection_allowed"] is False
    assert {
        item["fixture_id"] for item in report["fixtures"]
    } == {item["fixture_id"] for item in chaos_summary["fixtures"]} == {
        item["fixture_id"] for item in jolt_summary["fixtures"]
    }


def test_runtime_authority_selection_uses_custom_fallback_when_comparison_blocks():
    report = build_runtime_authority_selection_report(
        comparison_report=json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    ).report

    assert report["decision"] == AUTHORITY_SELECTION_DECISION
    assert report["selected_runtime"] == FALLBACK_RUNTIME_ID
    assert report["chaos_or_jolt_authority_selection_allowed"] is False
    assert report["milestone19_closed"] is True


def test_write_runtime_authority_selection_report_creates_json_and_markdown(tmp_path):
    output_json = tmp_path / "runtime_authority_selection.json"
    output_md = tmp_path / "runtime_authority_selection.md"

    report = write_runtime_authority_selection_report(
        comparison_report_path=COMPARISON_PATH,
        output_json=output_json,
        output_md=output_md,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert report.report["selected_runtime"] == FALLBACK_RUNTIME_ID


def test_committed_runtime_authority_selection_matches_comparison_report():
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    selection = json.loads(AUTHORITY_SELECTION_PATH.read_text(encoding="utf-8"))

    assert selection["decision"] == AUTHORITY_SELECTION_DECISION
    assert selection["selected_runtime"] == FALLBACK_RUNTIME_ID
    assert selection["comparison_report"] == "physics/reports/milestone19/chaos_vs_jolt_comparison.json"
    assert selection["chaos_or_jolt_authority_selection_allowed"] == (
        comparison["authority_selection_allowed"]
        and comparison["runtime_passed_fixture_suite"]
        and comparison["measured_evidence_available"]
    )


def test_unreal_manifests_use_selected_custom_reduced_fallback():
    raft_runtime = json.loads(RAFT_RUNTIME_PATH.read_text(encoding="utf-8"))
    authority = json.loads(PHYSICS_AUTHORITY_PATH.read_text(encoding="utf-8"))
    bridge = json.loads(FIXED_STEP_BRIDGE_PATH.read_text(encoding="utf-8"))

    assert raft_runtime["selected_runtime"] == FALLBACK_RUNTIME_ID
    assert raft_runtime["authority_selection_report"] == (
        "physics/reports/milestone19/runtime_authority_selection.json"
    )
    assert authority["authoritative"]["raft_kinematics"] == FALLBACK_RUNTIME_ID
    assert authority["authoritative"]["contacts"] == FALLBACK_RUNTIME_ID
    assert authority["custom_reduced"]["role"].startswith("selected_vertical_slice_fallback")
    assert bridge["authority"]["raft_kinematics"] == FALLBACK_RUNTIME_ID
