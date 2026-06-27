import json
import shutil
import subprocess
from pathlib import Path

import pytest

from raftsim.comparison import compare_dual_solver_fields, compare_dual_solver_probes
from raftsim.dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_dual_solver_scenario
from raftsim.pyclaw_reference import PyClawRunConfig, check_pyclaw_availability
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


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
            cpp=CppSolverRunConfig(executable=cpp_solver, steps=3, frame_interval=1),
        ),
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    cpp_validation = json.loads(result.cpp.validation_path.read_text(encoding="utf-8"))
    pyclaw_validation = json.loads((result.pyclaw_output_dir / "validation.json").read_text(encoding="utf-8"))

    assert result.scenario_dir.joinpath("scenario.json").exists()
    assert result.cpp.returncode == 0
    assert manifest["scenario_id"] == scenario.metadata.scenario_id
    assert manifest["scenario_json"].endswith("scenario.json")
    assert manifest["pyclaw"]["manifest"] == "pyclaw_reference/flat_pool_seed_12/manifest.json"
    assert manifest["cpp"]["manifest"] == "cpp_solver/flat_pool_seed_12/manifest.json"
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
