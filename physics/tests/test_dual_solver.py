import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim import comparison
from raftsim.comparison import (
    compare_dual_solver_diagnostics,
    compare_dual_solver_features,
    compare_dual_solver_fields,
    compare_dual_solver_probes,
    evaluate_dual_solver_thresholds,
)
from raftsim.chrono_validation import compare_chrono_bridge_telemetry
from raftsim.cascading import (
    CaliforniaPoolDropParameters2_5D,
    generate_california_pool_drop_cascading_scenario2_5d,
)
from raftsim.dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_dual_solver_scenario
from raftsim.pyclaw_reference import PyClawRunConfig, check_pyclaw_availability
from raftsim.regression import promote_passing_dual_solver_run
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d
from raftsim.sweeps import ParameterSweepCandidate
from raftsim.tuning import (
    CppTuningCandidate,
    default_cascading_cpp_tuning_candidates,
    fit_cpp_and_raft_parameters_against_pyclaw,
    tune_cpp_solver_against_cascading_geoclaw,
    tune_cpp_solver_against_geoclaw,
    tune_cpp_solver_against_pyclaw,
)


def _build_cpp_solver(tmp_path: Path) -> Path:
    cmake = shutil.which("cmake")
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    if cmake is None or compiler is None:
        pytest.skip("CMake and a C++ compiler are required for dual-solver tests.")
    physics_dir = Path(__file__).resolve().parents[1]
    build_dir = tmp_path / "cpp_build"
    subprocess.run([cmake, "-S", str(physics_dir / "cpp"), "-B", str(build_dir)], check=True)
    subprocess.run([cmake, "--build", str(build_dir)], check=True)
    return build_dir / "raftsim_water_solver"


def _write_reference_frame(path: Path, depth: np.ndarray, wet: np.ndarray) -> None:
    zeros = np.zeros_like(depth, dtype=float)
    np.savez(
        path,
        time=0.0,
        h=depth,
        eta=depth,
        u=zeros,
        v=zeros,
        hu=zeros,
        hv=zeros,
        wet=wet,
        normal_x=zeros,
        normal_y=zeros,
        normal_z=np.ones_like(depth, dtype=float),
        froude=zeros,
    )


def _write_cpp_frame(path: Path, depth: np.ndarray, wet: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude\n")
        for row in range(depth.shape[0]):
            for col in range(depth.shape[1]):
                handle.write(
                    f"{row},{col},{col},{row},{depth[row, col]},{depth[row, col]},"
                    f"0,0,0,0,{1 if wet[row, col] else 0},0,0,1,0\n"
                )


def test_field_comparison_wet_mismatch_uses_material_depth_floor(tmp_path):
    reference_depth = np.array([[0.10, 0.20], [0.0, 1.0]], dtype=float)
    candidate_depth = np.array([[0.0, 0.21], [0.0, 1.0]], dtype=float)
    reference_path = tmp_path / "reference.npz"
    candidate_path = tmp_path / "candidate.csv"
    _write_reference_frame(reference_path, reference_depth, reference_depth > 0.0)
    _write_cpp_frame(candidate_path, candidate_depth, candidate_depth > 0.0)

    default_floor = comparison._compare_frame_pair(
        "final",
        reference_path,
        candidate_path,
        1.0,
        1.0,
        reference_solver="geoclaw",
        velocity_depth_floor=0.15,
    )
    low_floor = comparison._compare_frame_pair(
        "final",
        reference_path,
        candidate_path,
        1.0,
        1.0,
        reference_solver="geoclaw",
        velocity_depth_floor=0.05,
    )

    assert default_floor.wet_mismatch_fraction == 0.0
    assert low_floor.wet_mismatch_fraction == pytest.approx(0.25)


def test_dual_solver_runs_pyclaw_and_cpp_on_one_shared_package(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=12, nx=12, ny=8, duration=0.05)
    )

    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(
                executable=cpp_solver,
                steps=3,
                frame_interval=1,
                solver_mode="finite_volume",
                boundary_mode="pyclaw",
                flux_scheme="roe",
                feature_strength_scale=0.0,
                roughness_scale=0.0,
                bed_slope_source_scale=0.0,
            ),
        ),
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    cpp_validation = json.loads(result.cpp.validation_path.read_text(encoding="utf-8"))
    pyclaw_validation = json.loads((result.pyclaw_output_dir / "validation.json").read_text(encoding="utf-8"))

    assert result.scenario_dir.joinpath("scenario.json").exists()
    assert result.cpp.returncode == 0
    assert "--solver-mode" in result.cpp.command
    assert "finite_volume" in result.cpp.command
    assert "--boundary-mode" in result.cpp.command
    assert "pyclaw" in result.cpp.command
    assert "--flux-scheme" in result.cpp.command
    assert "roe" in result.cpp.command
    assert manifest["scenario_id"] == scenario.metadata.scenario_id
    assert manifest["scenario_json"].endswith("scenario.json")
    assert manifest["pyclaw"]["manifest"] == "pyclaw_reference/flat_pool_seed_12/manifest.json"
    assert manifest["cpp"]["manifest"] == "cpp_solver/flat_pool_seed_12/manifest.json"
    assert manifest["runtime"]["simulated_duration_seconds"] == scenario.duration
    assert manifest["runtime"]["pyclaw_runtime_seconds"] >= 0.0
    assert manifest["runtime"]["cpp_runtime_seconds"] >= 0.0
    assert manifest["runtime"]["pyclaw_seconds_per_simulated_second"] >= 0.0
    assert manifest["runtime"]["cpp_seconds_per_simulated_second"] >= 0.0
    assert cpp_validation["passed"] is True
    assert pyclaw_validation["passed"] is True


def test_field_comparison_reports_shared_solver_fields(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=13, nx=12, ny=8, duration=0.05)
    )
    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    report = compare_dual_solver_fields(result.output_dir, output_path=result.output_dir / "field_comparison.json")
    report_data = json.loads((result.output_dir / "field_comparison.json").read_text(encoding="utf-8"))
    initial = report.frame_comparisons[0]
    error_by_name = {summary.field: summary for summary in initial.field_errors}
    slope_error_by_name = {summary.field: summary for summary in initial.slope_errors}

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report_data["scenario_id"] == scenario.metadata.scenario_id
    assert {summary["field"] for summary in report_data["aggregate_field_errors"]} >= {"h", "eta", "u", "v", "hu", "hv"}
    assert {summary["field"] for summary in report_data["aggregate_slope_errors"]} == {"slope_x", "slope_y"}
    assert {"h", "eta", "u", "v", "hu", "hv", "normal_x", "normal_y", "normal_z"}.issubset(error_by_name)
    assert {"slope_x", "slope_y"}.issubset(slope_error_by_name)
    assert initial.wet_mismatch_fraction == 0.0
    assert error_by_name["h"].linf == 0.0


def test_probe_comparison_reports_time_series_and_cross_sections(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=14, nx=12, ny=8, duration=0.05)
    )
    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    report = compare_dual_solver_probes(result.output_dir, output_path=result.output_dir / "probe_comparison.json")
    report_data = json.loads((result.output_dir / "probe_comparison.json").read_text(encoding="utf-8"))
    first_probe = report.point_probes[0]
    error_by_name = {summary.field: summary for summary in first_probe.field_errors}

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report_data["scenario_id"] == scenario.metadata.scenario_id
    assert report.point_probes
    assert report.cross_sections
    assert first_probe.kind == "point"
    assert first_probe.max_time_delta <= scenario.fixed_dt
    assert error_by_name["h"].linf == 0.0
    assert report.cross_sections[0].max_distance_delta == 0.0


def test_diagnostic_comparison_reports_physical_summaries(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=15, nx=12, ny=8, duration=0.05)
    )
    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    report = compare_dual_solver_diagnostics(
        result.output_dir,
        output_path=result.output_dir / "diagnostic_comparison.json",
    )
    report_data = json.loads((result.output_dir / "diagnostic_comparison.json").read_text(encoding="utf-8"))

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report_data["scenario_id"] == scenario.metadata.scenario_id
    assert report.pyclaw.mass_relative_drift == 0.0
    assert report.cpp.mass_relative_drift == 0.0
    assert report.pyclaw.froude_max == 0.0
    assert report.cpp.froude_max == 0.0
    assert report.pyclaw.hole_retention.hole_count == 0
    assert report.delta.hole_retained_area_delta == 0.0


def test_feature_comparison_reports_location_and_strength(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="dam_break", seed=16, nx=16, ny=8, duration=0.05)
    )
    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    report = compare_dual_solver_features(result.output_dir, output_path=result.output_dir / "feature_comparison.json")
    report_data = json.loads((result.output_dir / "feature_comparison.json").read_text(encoding="utf-8"))
    first = report.comparisons[0]

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report.feature_count == len(scenario.features)
    assert report_data["feature_count"] == len(scenario.features)
    assert first.kind == "ledge"
    assert first.location_delta >= 0.0
    assert first.pyclaw.strength >= 0.0
    assert first.cpp.strength >= 0.0


def test_threshold_evaluation_reports_scenario_pass_fail(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=17, nx=12, ny=8, duration=0.05)
    )
    result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    report = evaluate_dual_solver_thresholds(
        result.output_dir,
        output_path=result.output_dir / "threshold_evaluation.json",
    )
    report_data = json.loads((result.output_dir / "threshold_evaluation.json").read_text(encoding="utf-8"))

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report.passed is True
    assert report_data["passed"] is True
    assert report_data["thresholds"]["velocity_depth_floor"] == 0.15
    assert {check.name for check in report.checks} >= {"field_linf", "probe_linf", "mass_drift_delta"}


def test_cpp_tuning_selects_best_candidate(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=18, nx=10, ny=6, duration=1.0 / 60.0)
    )

    report = tune_cpp_solver_against_pyclaw(
        scenario,
        output_dir=tmp_path / "tuning",
        cpp_solver_executable=cpp_solver,
        candidates=(
            CppTuningCandidate("baseline", feature_strength_scale=1.0, roughness_scale=1.0),
            CppTuningCandidate("rougher", feature_strength_scale=1.0, roughness_scale=1.2),
        ),
        pyclaw_config=PyClawRunConfig(num_output_times=1),
        cpp_steps=1,
        cpp_frame_interval=1,
    )
    report_data = json.loads((tmp_path / "tuning" / "tuning_report.json").read_text(encoding="utf-8"))

    assert report.scenario_id == scenario.metadata.scenario_id
    assert len(report.candidates) == 2
    assert report.best_candidate.candidate.label in {"baseline", "rougher"}
    assert report_data["best_candidate"]["candidate"]["label"] == report.best_candidate.candidate.label


def test_cpp_tuning_against_geoclaw_selects_best_candidate(tmp_path):
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=118, nx=10, ny=6, duration=1.0 / 60.0)
    )

    report = tune_cpp_solver_against_geoclaw(
        scenario,
        output_dir=tmp_path / "geoclaw_tuning",
        cpp_solver_executable=cpp_solver,
        candidates=(
            CppTuningCandidate("baseline", feature_strength_scale=1.0, roughness_scale=1.0),
            CppTuningCandidate("rougher", feature_strength_scale=1.0, roughness_scale=1.2),
        ),
        cpp_steps=1,
        cpp_frame_interval=1,
    )
    report_data = json.loads((tmp_path / "geoclaw_tuning" / "geoclaw_tuning_report.json").read_text(encoding="utf-8"))
    first_manifest = json.loads(
        (tmp_path / "geoclaw_tuning" / report.candidates[0].candidate.label / "dual_solver_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert report.scenario_id == scenario.metadata.scenario_id
    assert len(report.candidates) == 2
    assert report.best_candidate.candidate.label in {"baseline", "rougher"}
    assert report_data["best_candidate"]["candidate"]["label"] == report.best_candidate.candidate.label
    assert first_manifest["geoclaw"]["solver"] == "geoclaw"
    assert first_manifest["runtime"]["geoclaw_runtime_seconds"] == 0.0

    coupling_report = compare_chrono_bridge_telemetry(report.candidates[0].dual_solver_dir)
    assert coupling_report.reference_solver == "geoclaw"
    assert coupling_report.trajectory_position_delta >= 0.0


def test_cpp_tuning_against_cascading_geoclaw_records_window_manifests(tmp_path):
    cpp_solver = _build_cpp_solver(tmp_path)
    package = generate_california_pool_drop_cascading_scenario2_5d(
        CaliforniaPoolDropParameters2_5D(seed=44, nx=64, ny=24, duration=1.0 / 60.0)
    )
    defaults = default_cascading_cpp_tuning_candidates()
    candidates = (
        CppTuningCandidate(
            "baseline",
            feature_strength_scale=1.0,
            roughness_scale=1.0,
            tuning_roles=("section_handoff", "roughness", "dissipation", "wet_dry", "feature_forcing"),
        ),
        CppTuningCandidate(
            "wet_dry_guarded",
            dry_tolerance=1.0e-5,
            feature_strength_scale=0.9,
            roughness_scale=1.1,
            tuning_roles=("wet_dry", "roughness", "feature_forcing"),
        ),
    )

    report = tune_cpp_solver_against_cascading_geoclaw(
        package,
        output_dir=tmp_path / "cascading_tuning",
        cpp_solver_executable=cpp_solver,
        candidates=candidates,
        cpp_steps=1,
        cpp_frame_interval=1,
    )
    report_data = json.loads(
        (tmp_path / "cascading_tuning" / "cascading_geoclaw_tuning_report.json").read_text(encoding="utf-8")
    )
    first_manifest = json.loads(
        (
            tmp_path
            / "cascading_tuning"
            / report.candidates[0].candidate.label
            / "dual_solver_manifest.json"
        ).read_text(encoding="utf-8")
    )
    first_cpp_manifest = json.loads(
        (
            tmp_path
            / "cascading_tuning"
            / report.candidates[0].candidate.label
            / first_manifest["cpp"]["manifest"]
        ).read_text(encoding="utf-8")
    )

    assert len(report.candidates) == 2
    assert report.best_candidate.candidate.label in {"baseline", "wet_dry_guarded"}
    assert report_data["best_candidate"]["candidate"]["label"] == report.best_candidate.candidate.label
    assert report_data["candidates"][1]["candidate"]["dry_tolerance"] == 1.0e-5
    assert "wet_dry" in report_data["candidates"][1]["candidate"]["tuning_roles"]
    assert any("section_handoff" in candidate.tuning_roles for candidate in defaults)
    assert any("wet_dry" in candidate.tuning_roles for candidate in defaults)
    assert first_manifest["scenario_package"].endswith(package.scenario.metadata.scenario_id)
    assert first_manifest["cascading_geoclaw"]["reach_window_count"] == 7
    assert first_manifest["cascading_geoclaw"]["drop_transition_window_count"] == 1
    assert first_manifest["cascading_geoclaw"]["stitched_manifest"].endswith("stitched/manifest.json")
    assert first_manifest["cpp"]["manifest"].endswith("manifest.json")
    assert first_cpp_manifest["cascading"]["present"] is True
    assert first_cpp_manifest["dry_tolerance"] == 1.0e-6


def test_promote_passing_run_to_regression_fixture(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=19, nx=10, ny=6, duration=1.0 / 60.0)
    )
    run_result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=1, frame_interval=1),
        ),
    )
    evaluate_dual_solver_thresholds(run_result.output_dir, output_path=run_result.output_dir / "threshold_evaluation.json")

    promotion = promote_passing_dual_solver_run(
        run_result.output_dir,
        regression_root=tmp_path / "regressions",
    )
    registry = json.loads(promotion.registry_path.read_text(encoding="utf-8"))

    assert promotion.scenario_id == scenario.metadata.scenario_id
    assert (promotion.fixture_dir / "scenario" / "scenario.json").exists()
    assert promotion.threshold_report.exists()
    assert registry["fixtures"][0]["scenario_id"] == scenario.metadata.scenario_id


def test_parameter_fit_scores_cpp_and_raft_candidates(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=20, nx=10, ny=6, duration=1.0 / 60.0)
    )

    report = fit_cpp_and_raft_parameters_against_pyclaw(
        scenario,
        output_dir=tmp_path / "parameter_fit",
        cpp_solver_executable=cpp_solver,
        candidates=(ParameterSweepCandidate("baseline"),),
        pyclaw_config=PyClawRunConfig(num_output_times=1),
        cpp_steps=1,
        cpp_frame_interval=1,
    )
    report_data = json.loads((tmp_path / "parameter_fit" / "parameter_fit_report.json").read_text(encoding="utf-8"))

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report.best_candidate.candidate.label == "baseline"
    assert report.best_candidate.water_score >= 0.0
    assert report.best_candidate.raft_force_score >= 0.0
    assert report_data["best_candidate"]["candidate"]["label"] == "baseline"


def test_chrono_bridge_telemetry_comparison_reports_force_envelope(tmp_path):
    availability = check_pyclaw_availability()
    if not availability.available:
        pytest.skip(f"PyClaw unavailable: {availability.reason}")
    cpp_solver = _build_cpp_solver(tmp_path)
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=21, nx=10, ny=6, duration=1.0 / 60.0)
    )
    run_result = run_dual_solver_scenario(
        scenario,
        output_dir=tmp_path / "dual",
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=1),
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=1, frame_interval=1),
        ),
    )

    report = compare_chrono_bridge_telemetry(
        run_result.output_dir,
        output_path=run_result.output_dir / "chrono_bridge_telemetry_comparison.json",
    )
    report_data = json.loads((run_result.output_dir / "chrono_bridge_telemetry_comparison.json").read_text(encoding="utf-8"))

    assert report.scenario_id == scenario.metadata.scenario_id
    assert report.reference_solver == "pyclaw"
    assert report.trajectory_position_delta >= 0.0
    assert report.trajectory_velocity_delta >= 0.0
    assert report.reference_outcome in {"floating", "grounded", "forced", "freefall"}
    assert report_data["scenario_id"] == scenario.metadata.scenario_id
