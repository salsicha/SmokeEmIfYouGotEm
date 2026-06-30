import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from raftsim.cascading import (
    CaliforniaPoolDropParameters2_5D,
    generate_california_pool_drop_cascading_scenario2_5d,
)
from raftsim.scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)


def test_cpp_reduced_water_solver_builds_and_exports_shared_scenario(tmp_path):
    cmake = shutil.which("cmake")
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    if cmake is None or compiler is None:
        pytest.skip("CMake and a C++ compiler are required for the native solver smoke test.")

    physics_dir = Path(__file__).resolve().parents[1]
    cpp_dir = physics_dir / "cpp"
    build_dir = tmp_path / "cpp_build"
    scenario_dir = tmp_path / "scenario" / "procedural"
    output_dir = tmp_path / "cpp_output"
    native_test_output = tmp_path / "native_test_output"

    scenario = generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=23, nx=32, ny=18, difficulty=0.55, feature_count=9)
    )
    scenario.write_package(scenario_dir)

    subprocess.run([cmake, "-S", str(cpp_dir), "-B", str(build_dir)], check=True)
    subprocess.run([cmake, "--build", str(build_dir)], check=True)

    subprocess.run(
        [str(build_dir / "raftsim_water_tests"), str(scenario_dir), str(native_test_output)],
        check=True,
    )
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
        ],
        check=True,
    )

    run_dir = output_dir / scenario.metadata.scenario_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))

    assert manifest["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_mode"] == "reduced"
    assert manifest["preserve_initial_mass"] is True
    assert validation["passed"] is True
    assert validation["mass_relative_drift"] < 1.0e-9
    assert "frames/frame_0000.csv" in manifest["frames"]
    assert manifest["probes"]
    assert manifest["cross_sections"]

    uncorrected_output_dir = tmp_path / "cpp_uncorrected_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(uncorrected_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    uncorrected_manifest = json.loads(
        (uncorrected_output_dir / scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert uncorrected_manifest["preserve_initial_mass"] is False

    finite_volume_output_dir = tmp_path / "cpp_finite_volume_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(scenario_dir),
            "--output",
            str(finite_volume_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "pyclaw",
            "--flux-scheme",
            "roe",
            "--feature-strength-scale",
            "0",
            "--roughness-scale",
            "0",
            "--bed-slope-source-scale",
            "0",
        ],
        check=True,
    )
    finite_volume_manifest = json.loads(
        (finite_volume_output_dir / scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )

    assert finite_volume_manifest["solver"] == "raftsim_water_cpp_v1"
    assert finite_volume_manifest["solver_mode"] == "finite_volume"
    assert finite_volume_manifest["boundary_mode"] == "pyclaw"
    assert finite_volume_manifest["flux_scheme"] == "roe"

    uniform_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=24, nx=24, ny=12, duration=0.2)
    )
    uniform_scenario_dir = tmp_path / "scenario" / "uniform_channel"
    uniform_scenario.write_package(uniform_scenario_dir)
    scenario_boundary_output_dir = tmp_path / "cpp_finite_volume_scenario_boundary_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(uniform_scenario_dir),
            "--output",
            str(scenario_boundary_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "scenario",
            "--feature-strength-scale",
            "0",
            "--bed-slope-source-scale",
            "1",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    scenario_boundary_run = scenario_boundary_output_dir / uniform_scenario.metadata.scenario_id
    scenario_boundary_manifest = json.loads((scenario_boundary_run / "manifest.json").read_text(encoding="utf-8"))
    final_frame = scenario_boundary_run / scenario_boundary_manifest["frames"][-1]
    west_column = []
    with final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["col"]) == 0:
                west_column.append((float(row["h"]), float(row["u"])))

    assert scenario_boundary_manifest["boundary_mode"] == "scenario"
    assert west_column
    assert any(abs(h - 1.25) > 1.0e-6 or abs(u - 1.4) > 1.0e-6 for h, u in west_column)

    wet_dry_scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="wet_dry_shoreline", seed=25, nx=24, ny=12, duration=0.2)
    )
    wet_dry_scenario_dir = tmp_path / "scenario" / "wet_dry_shoreline"
    wet_dry_scenario.write_package(wet_dry_scenario_dir)
    wet_dry_output_dir = tmp_path / "cpp_wet_dry_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(wet_dry_scenario_dir),
            "--output",
            str(wet_dry_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--feature-strength-scale",
            "0",
        ],
        check=True,
    )
    wet_dry_run = wet_dry_output_dir / wet_dry_scenario.metadata.scenario_id
    wet_dry_manifest = json.loads((wet_dry_run / "manifest.json").read_text(encoding="utf-8"))
    wet_dry_final_frame = wet_dry_run / wet_dry_manifest["frames"][-1]
    lateral_velocities = []
    wet_counts = 0
    with wet_dry_final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lateral_velocities.append(abs(float(row["v"])))
            wet_counts += int(row["wet"])

    assert wet_counts == int(wet_dry_scenario.initial_state.wet.sum())
    assert max(lateral_velocities) < 1.0e-9

    wet_dry_fv_output_dir = tmp_path / "cpp_wet_dry_fv_output"
    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(wet_dry_scenario_dir),
            "--output",
            str(wet_dry_fv_output_dir),
            "--steps",
            "12",
            "--frame-interval",
            "6",
            "--solver-mode",
            "finite_volume",
            "--boundary-mode",
            "scenario",
            "--flux-scheme",
            "hll",
            "--feature-strength-scale",
            "0",
            "--roughness-scale",
            "0.5",
            "--bed-slope-source-scale",
            "0.75",
            "--no-preserve-initial-mass",
        ],
        check=True,
    )
    wet_dry_fv_run = wet_dry_fv_output_dir / wet_dry_scenario.metadata.scenario_id
    wet_dry_fv_manifest = json.loads((wet_dry_fv_run / "manifest.json").read_text(encoding="utf-8"))
    wet_dry_fv_final_frame = wet_dry_fv_run / wet_dry_fv_manifest["frames"][-1]
    finite_volume_lateral_velocities = []
    finite_volume_wet_counts = 0
    with wet_dry_fv_final_frame.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            finite_volume_lateral_velocities.append(abs(float(row["v"])))
            finite_volume_wet_counts += int(row["wet"])

    assert wet_dry_fv_manifest["solver_mode"] == "finite_volume"
    assert wet_dry_fv_manifest["fixture_scoped_wet_dry_reconstruction"] is True
    assert finite_volume_wet_counts == int(wet_dry_scenario.initial_state.wet.sum())
    assert max(finite_volume_lateral_velocities) < 1.0e-9

    cascading_scenario_dir = tmp_path / "scenario" / "cascading"
    cascading_output_dir = tmp_path / "cpp_cascading_output"
    cascading_package = generate_california_pool_drop_cascading_scenario2_5d(
        CaliforniaPoolDropParameters2_5D(seed=31, nx=64, ny=24, duration=1.0)
    )
    cascading_package.write_package(cascading_scenario_dir)
    native_result = subprocess.run(
        [str(build_dir / "raftsim_water_tests"), str(cascading_scenario_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "cascading_reaches=7" in native_result.stdout

    subprocess.run(
        [
            str(build_dir / "raftsim_water_solver"),
            "--scenario",
            str(cascading_scenario_dir),
            "--output",
            str(cascading_output_dir),
            "--steps",
            "8",
            "--frame-interval",
            "4",
        ],
        check=True,
    )
    cascading_manifest = json.loads(
        (cascading_output_dir / cascading_package.scenario.metadata.scenario_id / "manifest.json").read_text(encoding="utf-8")
    )
    assert cascading_manifest["cascading"]["present"] is True
    assert cascading_manifest["cascading"]["reach_count"] == 7
    assert cascading_manifest["cascading"]["drop_transition_count"] == 1


def test_chrono_smoke_target_is_optional_and_outside_unreal():
    physics_dir = Path(__file__).resolve().parents[1]
    cmake_text = (physics_dir / "cpp" / "CMakeLists.txt").read_text(encoding="utf-8")
    smoke_source = (physics_dir / "cpp" / "tools" / "chrono_smoke_test.cpp").read_text(encoding="utf-8")

    assert "find_package(Chrono QUIET)" in cmake_text
    assert "add_executable(raftsim_chrono_smoke" in cmake_text
    assert "Project Chrono not found; skipping raftsim_chrono_smoke target" in cmake_text
    assert "ChSystemSMC" in smoke_source
    assert "chrono_smoke=ok" in smoke_source
