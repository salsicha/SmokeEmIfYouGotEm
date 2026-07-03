import json

from raftsim.milestone16 import (
    MILESTONE16_FULL_CPP_VALIDATION_GATE_REPORT_SCHEMA,
    Milestone16ComparisonRecord,
    Milestone16ComparisonReport,
    Milestone16CppRunRecord,
    Milestone16CppRunReport,
    Milestone16GeometryCaseResult,
    Milestone16GeometryValidationReport,
    Milestone16GeoClawReferenceReport,
    Milestone16GeoClawRunRecord,
    Milestone16RaftCouplingRecord,
    Milestone16RaftCouplingReport,
    Milestone16RuntimeProfileRecord,
    Milestone16RuntimeProfileReport,
    _cpp_config_for_mode,
    build_milestone16_full_cpp_validation_gate_report,
    run_milestone16_geometry_validation,
    run_milestone16_regression_promotion,
)
from raftsim.examples.generate_milestone16_full_cpp_validation_gate import main as generate_full_gate_main


def test_milestone16_geoclaw_reference_report_requires_full_solution():
    passed_record = Milestone16GeoClawRunRecord(
        gate_scenario_id="flat_pool",
        actual_scenario_id="flat_pool_seed_16",
        suite="canonical",
        flow_band=None,
        export_dir="outputs/flat_pool",
        run_manifest="outputs/flat_pool/geoclaw_run_manifest.json",
        normalized_manifest="outputs/flat_pool/normalized/manifest.json",
        normalized_mode="fgout_npz",
        returncode=0,
        runtime_seconds=1.0,
        frame_count=3,
        full_solution=True,
    )
    fallback_record = Milestone16GeoClawRunRecord(
        gate_scenario_id="uniform_channel",
        actual_scenario_id="uniform_channel_seed_16",
        suite="canonical",
        flow_band=None,
        export_dir="outputs/uniform_channel",
        run_manifest="outputs/uniform_channel/geoclaw_run_manifest.json",
        normalized_manifest="outputs/uniform_channel/normalized/manifest.json",
        normalized_mode="export_initial_state_only",
        returncode=0,
        runtime_seconds=0.0,
        frame_count=0,
        full_solution=False,
    )
    report = Milestone16GeoClawReferenceReport(
        output_root="outputs/milestone16/geoclaw_reference_runs",
        seed=16,
        config={"num_output_times": 2},
        availability={"available": True},
        records=(passed_record, fallback_record),
    )

    payload = report.to_json_dict()
    assert report.passed is False
    assert payload["passed_count"] == 1
    assert payload["failed_count"] == 1
    assert payload["records"][0]["passed"] is True
    assert payload["records"][1]["passed"] is False


def test_milestone16_cpp_run_report_requires_manifest_settings():
    run = Milestone16CppRunRecord(
        gate_scenario_id="flat_pool",
        actual_scenario_id="flat_pool_seed_16",
        suite="canonical",
        solver_mode="finite_volume",
        scenario_package="outputs/m16g/c_flat/shared_scenario",
        output_dir="outputs/m16cpp/c_flat/finite_volume/cpp_solver/flat_pool_seed_16",
        manifest="outputs/m16cpp/c_flat/finite_volume/cpp_solver/flat_pool_seed_16/manifest.json",
        validation="outputs/m16cpp/c_flat/finite_volume/cpp_solver/flat_pool_seed_16/validation.json",
        returncode=0,
        runtime_seconds=0.1,
        frame_count=3,
        validation_passed=True,
        manifest_settings={
            "solver": "raftsim_water_cpp_v1",
            "solver_mode": "finite_volume",
            "boundary_mode": "scenario",
            "flux_scheme": "hll",
            "cfl": 0.45,
            "dry_tolerance": 1.0e-6,
            "feature_strength_scale": 0.0,
            "roughness_scale": 0.5,
            "bed_slope_source_scale": 0.75,
            "preserve_initial_mass": False,
        },
        cascading={"present": False, "reach_count": 0, "drop_transition_count": 0},
        required_manifest_fields_present=True,
    )
    report = Milestone16CppRunReport(
        geoclaw_reference_report="reports/milestone16/geoclaw_reference_runs.json",
        output_root="outputs/m16cpp",
        cpp_solver="/tmp/raftsim-water-m16-build/raftsim_water_solver",
        records=(run,),
    )

    payload = report.to_json_dict()
    assert report.passed is True
    assert payload["run_count"] == 1
    assert payload["records"][0]["passed"] is True


def test_milestone16_cpp_config_applies_uniform_channel_finite_volume_override():
    uniform = _cpp_config_for_mode(
        "/tmp/raftsim-water-m16-build/raftsim_water_solver",
        "finite_volume",
        gate_scenario_id="uniform_channel",
    )
    generic = _cpp_config_for_mode(
        "/tmp/raftsim-water-m16-build/raftsim_water_solver",
        "finite_volume",
        gate_scenario_id="drop_ledge",
    )
    bed_step = _cpp_config_for_mode(
        "/tmp/raftsim-water-m16-build/raftsim_water_solver",
        "finite_volume",
        gate_scenario_id="bed_step",
    )
    reduced = _cpp_config_for_mode(
        "/tmp/raftsim-water-m16-build/raftsim_water_solver",
        "reduced",
        gate_scenario_id="uniform_channel",
    )

    assert uniform.flux_scheme == "hll"
    assert uniform.feature_strength_scale == 0.0
    assert uniform.roughness_scale == 0.35
    assert uniform.bed_slope_source_scale == 0.65
    assert generic.roughness_scale == 0.5
    assert generic.bed_slope_source_scale == 0.75
    assert bed_step.flux_scheme == "roe"
    assert bed_step.roughness_scale == 0.5
    assert bed_step.bed_slope_source_scale == 0.75
    assert reduced.roughness_scale == 1.0
    assert reduced.bed_slope_source_scale == 0.0
    assert reduced.preserve_initial_mass is False


def test_milestone16_comparison_report_tracks_threshold_failures():
    record = Milestone16ComparisonRecord(
        gate_scenario_id="flat_pool",
        actual_scenario_id="flat_pool_seed_16",
        suite="canonical",
        solver_mode="reduced",
        threshold_tier="production_candidate",
        comparison_dir="outputs/m16cmp/c_flat/reduced",
        threshold_report="outputs/m16cmp/c_flat/reduced/threshold_evaluation.json",
        threshold_passed=False,
        failing_checks=("field_linf", "probe_linf"),
        check_values={"field_linf": {"passed": False, "value": 1.0, "threshold": 0.15}},
        frame_comparisons=2,
        point_probes=3,
        cross_sections=1,
        feature_count=0,
        reach_drop_check={"required": False, "passed": True},
    )
    report = Milestone16ComparisonReport(
        geoclaw_reference_report="reports/milestone16/geoclaw_reference_runs.json",
        cpp_run_report="reports/milestone16/cpp_solver_runs.json",
        output_root="outputs/m16cmp",
        records=(record,),
    )

    payload = report.to_json_dict()
    assert report.passed is False
    assert payload["threshold_failed_count"] == 1
    assert payload["records"][0]["compared"] is True


def test_milestone16_geometry_report_blocks_on_failed_case():
    case = Milestone16GeometryCaseResult(
        case_id="wet_dry_shoreline",
        title="Wet/Dry Shorelines",
        scenarios=("wet_dry_shoreline",),
        solver_modes=("finite_volume", "reduced"),
        passed=False,
        evidence=({"gate_scenario_id": "wet_dry_shoreline", "threshold_passed": False},),
        notes=("Threshold failures remain in: wet_dry_shoreline.",),
    )
    report = Milestone16GeometryValidationReport(
        comparison_report="reports/milestone16/geoclaw_cpp_comparisons.json",
        geoclaw_reference_report="reports/milestone16/geoclaw_reference_runs.json",
        cases=(case,),
    )

    payload = report.to_json_dict()
    assert report.passed is False
    assert payload["failed_count"] == 1
    assert payload["cases"][0]["case_id"] == "wet_dry_shoreline"


def test_milestone16_geometry_validation_applies_milestone18_focused_closure(tmp_path):
    report_root = tmp_path / "reports"
    milestone16_dir = report_root / "milestone16"
    milestone18_dir = report_root / "milestone18"
    milestone16_dir.mkdir(parents=True)
    milestone18_dir.mkdir(parents=True)
    comparison_report = milestone16_dir / "geoclaw_cpp_comparisons.json"
    comparison_report.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "gate_scenario_id": "wet_dry_shoreline",
                        "solver_mode": "reduced",
                        "threshold_passed": True,
                        "failing_checks": [],
                    },
                    {
                        "gate_scenario_id": "wet_dry_shoreline",
                        "solver_mode": "finite_volume",
                        "threshold_passed": False,
                        "failing_checks": ["field_linf", "wet_mismatch_fraction"],
                    },
                    {
                        "gate_scenario_id": "bed_step",
                        "solver_mode": "reduced",
                        "threshold_passed": False,
                        "failing_checks": ["field_linf", "mass_drift_delta"],
                    },
                    {
                        "gate_scenario_id": "bed_step",
                        "solver_mode": "finite_volume",
                        "threshold_passed": True,
                        "failing_checks": [],
                    },
                    {
                        "gate_scenario_id": "constriction",
                        "solver_mode": "finite_volume",
                        "threshold_passed": False,
                        "failing_checks": ["field_linf", "probe_linf"],
                    },
                    {
                        "gate_scenario_id": "drop_ledge",
                        "solver_mode": "finite_volume",
                        "threshold_passed": False,
                        "failing_checks": ["field_linf"],
                    },
                    {
                        "gate_scenario_id": "south_fork_cascading_low_runnable",
                        "solver_mode": "finite_volume",
                        "threshold_passed": False,
                        "failing_checks": ["mass_drift_delta"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    geoclaw_report = milestone16_dir / "geoclaw_reference_runs.json"
    geoclaw_report.write_text(json.dumps({"records": []}), encoding="utf-8")
    (milestone18_dir / "wet_dry_finite_volume_reconstruction_retune.json").write_text(
        json.dumps(
            {
                "scenario_family": "wet_dry_shoreline",
                "gate_scenario_id": "wet_dry_shoreline_seed_16",
                "actual_scenario_id": "wet_dry_shoreline_seed_16",
                "summary": {"promoted_modes": ["finite_volume", "reduced"], "blocked_modes": []},
                "mode_results": [
                    {"solver_mode": "finite_volume", "promoted": True, "failing_checks": []},
                    {"solver_mode": "reduced", "promoted": True, "failing_checks": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    (milestone18_dir / "bed_step_parity_retune.json").write_text(
        json.dumps(
            {
                "scenario_family": "bed_step",
                "gate_scenario_id": "bed_step",
                "actual_scenario_id": "bed_step_seed_16",
                "summary": {"promoted_modes": ["finite_volume"], "blocked_modes": ["reduced"]},
                "mode_results": [
                    {"solver_mode": "finite_volume", "promoted": True, "failing_checks": []},
                    {"solver_mode": "reduced", "promoted": False, "failing_checks": ["field_linf"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    (milestone18_dir / "remaining_geometry_closure.json").write_text(
        json.dumps(
            {
                "schema_version": "raftsim.milestone18.remaining_geometry_closure.v0",
                "passed": True,
                "summary": {"active_blockers": [], "promotion_ready_count": 2},
                "cases": [
                    {
                        "case_id": "constriction",
                        "passed": True,
                        "promotion_ready": True,
                        "solver_modes": ["finite_volume"],
                        "failing_check_counts": {},
                        "focused_evidence": [
                            {"source_report": "constriction_upstream_edge_balance.json", "passed": True}
                        ],
                        "notes": ["Focused passing evidence supersedes stale aggregate failures for: constriction."],
                    },
                    {
                        "case_id": "drops_ledges_tailwater",
                        "passed": True,
                        "promotion_ready": True,
                        "solver_modes": ["finite_volume"],
                        "failing_check_counts": {},
                        "focused_evidence": [
                            {"source_report": "cascading_boundary_correction_diagnostic.json", "passed": True}
                        ],
                        "notes": [
                            "Focused passing evidence supersedes stale aggregate failures for: drop_ledge, south_fork_cascading_low_runnable."
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = run_milestone16_geometry_validation(
        comparison_report,
        geoclaw_report,
        milestone18_report_dir=milestone18_dir,
    )
    cases = {case.case_id: case.to_json_dict() for case in report.cases}

    assert cases["wet_dry_shoreline"]["passed"] is True
    assert cases["bed_step"]["passed"] is True
    assert cases["constriction"]["passed"] is True
    assert cases["drops_ledges_tailwater"]["passed"] is True
    assert any(row["diagnostic_only"] for row in cases["bed_step"]["evidence"])
    assert any("Supersedes stale Milestone 16 threshold blockers" in note for note in cases["wet_dry_shoreline"]["notes"])
    assert cases["constriction"]["evidence"][0]["focused_evidence_count"] == 1
    assert any(
        "remaining-geometry closure evidence applied" in note
        for note in cases["drops_ledges_tailwater"]["notes"]
    )


def test_milestone16_raft_coupling_report_blocks_on_force_delta():
    record = Milestone16RaftCouplingRecord(
        gate_scenario_id="south_fork_cascading_low_runnable",
        actual_scenario_id="american_south_fork_chili_bar_to_coloma_low_runnable_beginner_cascading",
        suite="cascading",
        flow_band="low_runnable",
        solver_mode="reduced",
        case_id="pool_entry",
        expected_outcomes=("clear",),
        reference_frame="outputs/m16g/cg_low/normalized_cascading/stitched/frames/frame_0002.npz",
        candidate_frame="outputs/m16cpp/cg_low/reduced/cpp_solver/example/frames/frame_0008.csv",
        reference_outcome="clear",
        candidate_outcome="clear",
        reference_passed=True,
        candidate_passed=True,
        feature_outcome_match=True,
        force_envelope_outcome_match=True,
        force_delta_weight_ratio=4.0,
        torque_delta_inertia_ratio=0.1,
        trajectory_position_delta_m=0.01,
        trajectory_velocity_delta_mps=0.02,
        reference_checks=({"name": "entry_depth", "passed": True, "value": 1.0, "threshold": 0.8},),
        candidate_checks=({"name": "entry_depth", "passed": True, "value": 1.0, "threshold": 0.8},),
        notes=("Force delta exceeds the weight-normalized threshold.",),
    )
    report = Milestone16RaftCouplingReport(
        geoclaw_reference_report="reports/milestone16/geoclaw_reference_runs.json",
        cpp_run_report="reports/milestone16/cpp_solver_runs.json",
        records=(record,),
    )

    payload = report.to_json_dict()
    assert report.passed is False
    assert payload["failed_count"] == 1
    assert payload["records"][0]["passed"] is False


def test_milestone16_regression_promotion_writes_fixtures_and_artifacts(tmp_path):
    scenario_package = tmp_path / "scenario_package"
    scenario_package.mkdir()
    (scenario_package / "scenario.json").write_text('{"metadata": {"scenario_id": "flat_pool_seed_16"}}', encoding="utf-8")
    comparison_dir = tmp_path / "comparison"
    comparison_dir.mkdir()
    (comparison_dir / "dual_solver_manifest.json").write_text(
        '{"scenario_id": "flat_pool_seed_16", "scenario_package": "' + str(scenario_package) + '"}',
        encoding="utf-8",
    )
    (comparison_dir / "threshold_evaluation.json").write_text('{"passed": true}', encoding="utf-8")
    for name in ("field_comparison.json", "probe_comparison.json", "diagnostic_comparison.json", "feature_comparison.json"):
        (comparison_dir / name).write_text("{}", encoding="utf-8")
    comparison_report = tmp_path / "comparison_report.json"
    comparison_report.write_text(
        """{
          "records": [{
            "gate_scenario_id": "flat_pool",
            "actual_scenario_id": "flat_pool_seed_16",
            "suite": "canonical",
            "solver_mode": "reduced",
            "comparison_dir": "%s",
            "threshold_passed": true
          }]
        }"""
        % comparison_dir,
        encoding="utf-8",
    )
    raft_report = tmp_path / "raft_report.json"
    raft_report.write_text(
        """{
          "records": [{
            "gate_scenario_id": "shallow_shelf",
            "actual_scenario_id": "shallow_shelf_seed_21",
            "suite": "rafting",
            "solver_mode": "reduced",
            "case_id": "shallow_shelf_pivot_release",
            "passed": true
          }]
        }""",
        encoding="utf-8",
    )
    geometry_report = tmp_path / "geometry_report.json"
    geometry_report.write_text(
        """{
          "cases": [{
            "case_id": "stitched_reach_drop_handoffs",
            "title": "Stitched Reach/Drop Boundary Handoffs",
            "scenarios": ["south_fork_cascading_low_runnable"],
            "solver_modes": ["geoclaw", "package"],
            "passed": true,
            "evidence": [{
              "gate_scenario_id": "south_fork_cascading_low_runnable",
              "passed": true,
              "check_count": 1,
              "checks": [{"transition_id": "ledge_drop_001", "passed": true}]
            }]
          }, {
            "case_id": "constriction",
            "passed": false,
            "evidence": [{"gate_scenario_id": "constriction", "passed": false}]
          }]
        }""",
        encoding="utf-8",
    )

    report = run_milestone16_regression_promotion(
        comparison_report,
        raft_report,
        geometry_report=geometry_report,
        fixture_root=tmp_path / "fixtures",
    )
    registry = report.to_json_dict()

    assert report.passed is True
    assert registry["entry_count"] == 3
    assert registry["geometry_artifact_count"] == 1
    assert (tmp_path / "fixtures" / "geoclaw_cpp" / "c_flat" / "reduced" / "scenario" / "scenario.json").exists()
    assert (
        tmp_path
        / "fixtures"
        / "geometry_validation"
        / "stitched_reach_drop_handoffs"
        / "cg_low"
        / "geometry_case.json"
    ).exists()
    assert (
        tmp_path
        / "fixtures"
        / "raft_coupling"
        / "r_shelf"
        / "reduced"
        / "shallow_shelf_pivot_release"
        / "raft_coupling_case.json"
    ).exists()


def test_milestone16_regression_promotion_keeps_mode_specific_geometry_closure_artifacts(tmp_path):
    comparison_report = tmp_path / "comparison_report.json"
    comparison_report.write_text(json.dumps({"records": []}), encoding="utf-8")
    raft_report = tmp_path / "raft_report.json"
    raft_report.write_text(json.dumps({"records": []}), encoding="utf-8")
    geometry_report = tmp_path / "geometry_report.json"
    geometry_report.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "wet_dry_shoreline",
                        "title": "Wet/Dry Shorelines",
                        "scenarios": ["wet_dry_shoreline"],
                        "solver_modes": ["finite_volume", "reduced"],
                        "passed": True,
                        "evidence": [
                            {
                                "gate_scenario_id": "wet_dry_shoreline",
                                "actual_scenario_id": "wet_dry_shoreline_seed_16",
                                "solver_mode": "finite_volume",
                                "passed": True,
                                "accepted_for_geometry": True,
                                "milestone18_report": "reports/milestone18/wet_dry.json",
                            },
                            {
                                "gate_scenario_id": "wet_dry_shoreline",
                                "actual_scenario_id": "wet_dry_shoreline_seed_16",
                                "solver_mode": "reduced",
                                "passed": True,
                                "accepted_for_geometry": True,
                                "milestone18_report": "reports/milestone18/wet_dry.json",
                            },
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = run_milestone16_regression_promotion(
        comparison_report,
        raft_report,
        geometry_report=geometry_report,
        fixture_root=tmp_path / "fixtures",
    )
    artifact_ids = [entry.artifact_id for entry in report.entries]

    assert artifact_ids == [
        "geometry_validation/wet_dry_shoreline/wet_dry_shoreline/finite_volume",
        "geometry_validation/wet_dry_shoreline/wet_dry_shoreline/reduced",
    ]
    assert (
        tmp_path
        / "fixtures"
        / "geometry_validation"
        / "wet_dry_shoreline"
        / "c_wetdry"
        / "finite_volume"
        / "geometry_case.json"
    ).exists()
    assert (
        tmp_path
        / "fixtures"
        / "geometry_validation"
        / "wet_dry_shoreline"
        / "c_wetdry"
        / "reduced"
        / "geometry_case.json"
    ).exists()


def test_milestone16_runtime_profile_report_blocks_on_budget_or_replay_failure():
    passing_budget = {
        "desktop": {"passed": True, "runtime_ms_per_tick": 0.2, "water_solver_budget_ms": 2.4},
        "vr": {"passed": True, "runtime_ms_per_tick": 0.2, "water_solver_budget_ms": 1.6},
        "handheld": {"passed": True, "runtime_ms_per_tick": 0.2, "water_solver_budget_ms": 2.8},
    }
    failing_budget = {
        "desktop": {"passed": True, "runtime_ms_per_tick": 2.0, "water_solver_budget_ms": 2.4},
        "vr": {"passed": False, "runtime_ms_per_tick": 2.0, "water_solver_budget_ms": 1.6},
        "handheld": {"passed": True, "runtime_ms_per_tick": 2.0, "water_solver_budget_ms": 2.8},
    }
    records = (
        Milestone16RuntimeProfileRecord(
            artifact_id="geoclaw_cpp/flat_pool/reduced",
            gate_scenario_id="flat_pool",
            actual_scenario_id="flat_pool_seed_16",
            solver_mode="reduced",
            repetition=0,
            scenario_package="regression_fixtures/milestone16/geoclaw_cpp/c_flat/reduced/scenario",
            output_dir="outputs/m16profile/geoclaw_cpp/flat_pool/reduced/rep_00",
            manifest="outputs/m16profile/geoclaw_cpp/flat_pool/reduced/rep_00/cpp_solver/flat_pool_seed_16/manifest.json",
            validation="outputs/m16profile/geoclaw_cpp/flat_pool/reduced/rep_00/cpp_solver/flat_pool_seed_16/validation.json",
            runtime_seconds=0.1,
            simulated_seconds=1.0,
            step_count=500,
            runtime_ms_per_tick=0.2,
            validation_passed=True,
            frame_hash="abc",
            budget_results=passing_budget,
        ),
        Milestone16RuntimeProfileRecord(
            artifact_id="geoclaw_cpp/flat_pool/finite_volume",
            gate_scenario_id="flat_pool",
            actual_scenario_id="flat_pool_seed_16",
            solver_mode="finite_volume",
            repetition=0,
            scenario_package="regression_fixtures/milestone16/geoclaw_cpp/c_flat/finite_volume/scenario",
            output_dir="outputs/m16profile/geoclaw_cpp/flat_pool/finite_volume/rep_00",
            manifest="outputs/m16profile/geoclaw_cpp/flat_pool/finite_volume/rep_00/cpp_solver/flat_pool_seed_16/manifest.json",
            validation="outputs/m16profile/geoclaw_cpp/flat_pool/finite_volume/rep_00/cpp_solver/flat_pool_seed_16/validation.json",
            runtime_seconds=1.0,
            simulated_seconds=1.0,
            step_count=500,
            runtime_ms_per_tick=2.0,
            validation_passed=True,
            frame_hash="def",
            budget_results=failing_budget,
        ),
    )
    report = Milestone16RuntimeProfileReport(
        registry_path="regression_fixtures/milestone16/registry.json",
        cpp_solver="/tmp/raftsim-water-m16-build/raftsim_water_solver",
        budget_config="config/runtime_budgets.json",
        output_root="outputs/m16profile",
        records=records,
        deterministic_replay=(
            {"artifact_id": "geoclaw_cpp/flat_pool/reduced", "passed": True, "hashes": ["abc", "abc"]},
            {"artifact_id": "geoclaw_cpp/flat_pool/finite_volume", "passed": False, "hashes": ["def", "fed"]},
        ),
    )

    payload = report.to_json_dict()
    assert report.passed is False
    assert payload["budget_failed_count"] == 1
    assert payload["deterministic_replay"][1]["passed"] is False


def test_milestone16_full_cpp_validation_gate_report_aggregates_component_reports(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    _write_component_reports(report_dir)

    report = build_milestone16_full_cpp_validation_gate_report(report_dir)
    payload = report.to_json_dict()
    json_path = report.write_json(tmp_path / "full_gate.json")
    markdown_path = report.write_markdown(tmp_path / "full_gate.md")

    assert report.passed is False
    assert payload["schema_version"] == MILESTONE16_FULL_CPP_VALIDATION_GATE_REPORT_SCHEMA
    assert payload["component_count"] == 7
    assert payload["blocked_component_ids"] == ["geoclaw_cpp_comparisons", "geometry", "raft_coupling"]
    assert "wet_dry_shoreline" in payload["components"][2]["blockers"][0]
    assert "Decision: **BLOCKED**" in markdown_path.read_text(encoding="utf-8")
    assert json_path.exists()


def test_generate_milestone16_full_cpp_validation_gate_cli_writes_blocked_report(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    _write_component_reports(report_dir)
    output_json = tmp_path / "suite.json"
    output_md = tmp_path / "suite.md"

    exit_code = generate_full_gate_main(
        [
            "--report-dir",
            str(report_dir),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )

    assert exit_code == 1
    assert output_json.exists()
    assert "Decision: **BLOCKED**" in output_md.read_text(encoding="utf-8")


def _write_component_reports(report_dir):
    (report_dir / "geoclaw_reference_runs.json").write_text(
        """{
          "passed": true,
          "scenario_count": 2,
          "passed_count": 2,
          "failed_count": 0,
          "records": [{"gate_scenario_id": "flat_pool", "passed": true}, {"gate_scenario_id": "uniform_channel", "passed": true}]
        }""",
        encoding="utf-8",
    )
    (report_dir / "cpp_solver_runs.json").write_text(
        """{
          "passed": true,
          "run_count": 4,
          "passed_count": 4,
          "failed_count": 0,
          "records": [{"gate_scenario_id": "flat_pool", "passed": true}, {"gate_scenario_id": "uniform_channel", "passed": true}]
        }""",
        encoding="utf-8",
    )
    (report_dir / "geoclaw_cpp_comparisons.json").write_text(
        """{
          "passed": false,
          "comparison_count": 2,
          "threshold_passed_count": 1,
          "threshold_failed_count": 1,
          "records": [
            {"gate_scenario_id": "flat_pool", "threshold_passed": true},
            {"gate_scenario_id": "wet_dry_shoreline", "threshold_passed": false, "failing_checks": ["field_linf"]}
          ]
        }""",
        encoding="utf-8",
    )
    (report_dir / "geometry_validation.json").write_text(
        """{
          "passed": false,
          "case_count": 2,
          "passed_count": 1,
          "failed_count": 1,
          "cases": [{"case_id": "hydrostatic", "passed": true}, {"case_id": "bed_steps", "passed": false}]
        }""",
        encoding="utf-8",
    )
    (report_dir / "raft_coupling_validation.json").write_text(
        """{
          "passed": false,
          "comparison_count": 2,
          "passed_count": 1,
          "failed_count": 1,
          "records": [
            {"case_id": "pool_entry", "passed": true},
            {"case_id": "hydraulic_hole_surf", "passed": false, "notes": ["force delta"]}
          ]
        }""",
        encoding="utf-8",
    )
    (report_dir / "runtime_profile.json").write_text(
        """{
          "passed": true,
          "run_count": 1,
          "budget_passed_count": 1,
          "budget_failed_count": 0,
          "records": [{"artifact_id": "flat_pool/reduced", "passed": true}],
          "deterministic_replay": [{"artifact_id": "flat_pool/reduced", "passed": true, "hashes": ["abc", "abc"]}]
        }""",
        encoding="utf-8",
    )
    (report_dir / "regression_promotion_manifest.json").write_text(
        """{
          "passed": true,
          "entry_count": 1,
          "entries": [{"artifact_id": "flat_pool/reduced", "passed": true}]
        }""",
        encoding="utf-8",
    )
