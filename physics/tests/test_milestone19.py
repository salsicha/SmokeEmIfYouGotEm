import json
from pathlib import Path

from raftsim.milestone19 import (
    CHAOS_EXPORT_DECISION,
    CHAOS_RUNTIME_ID,
    JOLT_EXPORT_DECISION,
    JOLT_RUNTIME_ID,
    build_chaos_automation_export,
    build_jolt_smoke_harness_export,
    load_runtime_evaluation_contract,
    write_chaos_automation_export,
    write_jolt_smoke_harness_export,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json"
CHAOS_MANIFEST_PATH = REPO_ROOT / "unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json"
CHAOS_SUMMARY_PATH = REPO_ROOT / "physics/reports/milestone19/chaos/summary.json"
JOLT_MANIFEST_PATH = REPO_ROOT / "physics/cpp/tests/jolt_smoke_harness_manifest.json"
JOLT_SUMMARY_PATH = REPO_ROOT / "physics/reports/milestone19/jolt/summary.json"


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
