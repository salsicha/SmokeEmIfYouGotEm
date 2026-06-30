import json

from raftsim.readiness import (
    GEOCLAW_READINESS_REPORT_VERSION,
    READINESS_REPORT_VERSION,
    build_adaptive_flow_validation,
    build_geoclaw_readiness_report,
    build_milestone10_scenario_suite,
    build_milestone16_geoclaw_readiness_report,
    build_readiness_report,
    check_from_summary,
    count_csv_rows,
    make_pyclaw_reference_compatible,
    write_unreal_visualization_exports,
)
from raftsim.examples.generate_geoclaw_to_unreal_readiness import main as generate_geoclaw_readiness_main
from raftsim.examples.generate_milestone16_geoclaw_to_unreal_readiness import main as generate_milestone16_readiness_main
from raftsim.scenario2_5d import ProceduralScenario2_5DParameters, generate_procedural_scenario2_5d
from raftsim.schema_versions import REPLAY_SCHEMA_VERSION


def test_pyclaw_reference_compatible_copy_adds_shallow_shelf_and_provenance():
    scenario = generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=2, nx=32, ny=18, feature_count=9)
    )
    reference = make_pyclaw_reference_compatible(scenario, minimum_depth_m=0.02)

    assert scenario.initial_state.depth.min() == 0.0
    assert reference.initial_state.depth.min() >= 0.02
    assert reference.metadata.provenance["pyclaw_reference_min_depth_m"] == 0.02
    assert reference.validate().passed


def test_milestone10_scenario_suite_includes_real_world_flow_bands():
    scenarios = build_milestone10_scenario_suite()
    flow_bands = {scenario.metadata.flow_band for scenario in scenarios if scenario.metadata.scenario_type == "real_world"}

    assert len(scenarios) == 7
    assert {"low_runnable", "median_runnable", "high_runnable"}.issubset(flow_bands)
    assert all(scenario.validate().passed for scenario in scenarios)


def test_adaptive_flow_validation_maps_low_median_high_monotonically():
    validation = build_adaptive_flow_validation()
    presets = validation["flow_presets"]

    assert validation["passed"] is True
    assert [preset["flow_band"] for preset in presets] == ["low_runnable", "median_runnable", "high_runnable"]
    assert presets[0]["boundary_inflow_m3s"] < presets[1]["boundary_inflow_m3s"] < presets[2]["boundary_inflow_m3s"]
    assert presets[0]["wave_train_strength"] < presets[1]["wave_train_strength"] < presets[2]["wave_train_strength"]


def test_unreal_visualization_exports_replay_and_force_telemetry(tmp_path):
    manifest = write_unreal_visualization_exports(tmp_path, frame_count=3)
    replay = json.loads((tmp_path / "replay.json").read_text(encoding="utf-8"))

    assert manifest["frame_count"] == 3
    assert manifest["force_row_count"] > 0
    assert replay["schema_version"] == REPLAY_SCHEMA_VERSION
    assert len(replay["frames"]) == 3
    assert count_csv_rows(tmp_path / "telemetry_forces.csv") == manifest["force_row_count"]


def test_readiness_report_blocks_unreal_when_a_blocking_check_fails(tmp_path):
    checks = (
        check_from_summary("pyclaw", "PyClaw", True, "reference passed"),
        check_from_summary("dual", "Dual Solver", False, "real-world threshold failed"),
    )
    report = build_readiness_report(checks, artifact_manifest={"dual": "dual.json"})
    json_path = report.write_json(tmp_path / "report.json")
    md_path = report.write_markdown(tmp_path / "report.md")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert report.gate_version == READINESS_REPORT_VERSION
    assert report.passed is False
    assert report.decision.status == "blocked"
    assert data["decision"]["approved_for_unreal_production_start"] is False
    assert "BLOCKED" in md_path.read_text(encoding="utf-8")


def test_readiness_report_approves_when_all_checks_pass():
    checks = (
        check_from_summary("pyclaw", "PyClaw", True, "reference passed"),
        check_from_summary("dual", "Dual Solver", True, "thresholds passed"),
    )
    report = build_readiness_report(checks, artifact_manifest={})

    assert report.passed is True
    assert report.decision.status == "approved"
    assert report.decision.approved_for_unreal_production_start is True


def test_geoclaw_readiness_report_blocks_without_full_fgout_frames():
    report = build_geoclaw_readiness_report(
        geoclaw_reference_summary={
            "exports_passed": True,
            "export_count": 1,
            "normalized_mode": "export_initial_state_only",
            "has_full_geoclaw_frames": False,
        },
        cpp_summary={"passed": True, "run_count": 1},
        comparison_summary={"passed": True, "comparison_count": 1},
        tuning_summary={"passed": True, "candidate_count": 1},
        raft_coupling_summary={"passed": True, "comparison_count": 1},
        artifact_manifest={},
    )

    assert report.gate_version == GEOCLAW_READINESS_REPORT_VERSION
    assert report.passed is False
    assert report.decision.status == "blocked"
    assert any(check.check_id == "geoclaw_fixed_grid_outputs" and not check.passed for check in report.checks)


def test_generate_geoclaw_readiness_example_writes_blocked_report_without_cpp(tmp_path):
    exit_code = generate_geoclaw_readiness_main(
        [
            "--output-dir",
            str(tmp_path / "readiness"),
            "--scratch-dir",
            str(tmp_path / "scratch"),
        ]
    )
    report = json.loads((tmp_path / "readiness" / "geoclaw_to_unreal_readiness_report.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["gate_version"] == GEOCLAW_READINESS_REPORT_VERSION
    assert report["decision"]["status"] == "blocked"
    assert (tmp_path / "readiness" / "geoclaw_reference_summary.json").exists()


def test_milestone16_geoclaw_readiness_report_blocks_live_custom_water():
    report = build_milestone16_geoclaw_readiness_report(
        geoclaw_reference_summary={"passed": True, "passed_count": 20, "scenario_count": 20},
        cpp_summary={"passed": True, "passed_count": 40, "run_count": 40},
        comparison_summary={"passed": False, "threshold_passed_count": 4, "comparison_count": 40},
        geometry_summary={"passed": False, "passed_count": 2, "case_count": 6},
        raft_coupling_summary={"passed": False, "passed_count": 7, "comparison_count": 50},
        runtime_profile_summary={"passed": True, "budget_passed_count": 8, "run_count": 8},
        regression_promotion_summary={"passed": True, "entry_count": 11},
        artifact_manifest={},
    )
    check_ids = {check.check_id for check in report.checks}

    assert report.gate_version == GEOCLAW_READINESS_REPORT_VERSION
    assert report.passed is False
    assert report.decision.status == "blocked"
    assert report.decision.approved_for_unreal_production_start is False
    assert "milestone16_geoclaw_cpp_thresholds" in check_ids
    assert "milestone16_geometry_validation" in check_ids
    assert "milestone16_raft_coupling" in check_ids


def test_generate_milestone16_readiness_writes_blocked_report(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    _write_json(
        report_dir / "geoclaw_reference_runs.json",
        {"passed": True, "passed_count": 1, "failed_count": 0, "records": [{"passed": True, "full_solution": True}]},
    )
    _write_json(
        report_dir / "cpp_solver_runs.json",
        {"passed": True, "passed_count": 1, "failed_count": 0, "records": [{"passed": True, "gate_scenario_id": "flat_pool"}]},
    )
    _write_json(
        report_dir / "geoclaw_cpp_comparisons.json",
        {"passed": False, "comparison_count": 2, "records": [{"threshold_passed": True}, {"threshold_passed": False}]},
    )
    _write_json(
        report_dir / "geometry_validation.json",
        {"passed": False, "case_count": 1, "cases": [{"passed": False}]},
    )
    _write_json(
        report_dir / "raft_coupling_validation.json",
        {"passed": False, "comparison_count": 1, "passed_count": 0, "failed_count": 1, "records": [{"passed": False}]},
    )
    _write_json(
        report_dir / "runtime_profile.json",
        {"passed": True, "budget_passed_count": 1, "budget_failed_count": 0, "records": [{"passed": True}], "deterministic_replay": [{"passed": True}]},
    )
    _write_json(
        report_dir / "regression_promotion_manifest.json",
        {"passed": True, "entries": [{"passed": True, "category": "geoclaw_cpp"}, {"passed": True, "category": "raft_coupling"}]},
    )

    exit_code = generate_milestone16_readiness_main(
        [
            "--output-dir",
            str(tmp_path / "readiness"),
            "--report-dir",
            str(report_dir),
        ]
    )
    report = json.loads((tmp_path / "readiness" / "geoclaw_to_unreal_readiness_report.json").read_text(encoding="utf-8"))
    comparison_summary = json.loads((tmp_path / "readiness" / "geoclaw_cpp_comparison_summary.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["decision"]["status"] == "blocked"
    assert report["decision"]["approved_for_unreal_production_start"] is False
    assert comparison_summary["threshold_failed_count"] == 1


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
