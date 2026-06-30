from raftsim.milestone16 import (
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
)


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
            "flux_scheme": "rusanov",
            "cfl": 0.45,
            "dry_tolerance": 1.0e-6,
            "feature_strength_scale": 1.0,
            "roughness_scale": 1.0,
            "bed_slope_source_scale": 1.0,
            "preserve_initial_mass": True,
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
