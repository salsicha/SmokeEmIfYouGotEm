from raftsim.milestone16 import (
    Milestone16CppRunRecord,
    Milestone16CppRunReport,
    Milestone16GeoClawReferenceReport,
    Milestone16GeoClawRunRecord,
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
