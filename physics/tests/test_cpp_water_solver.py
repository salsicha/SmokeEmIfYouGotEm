import json
import shutil
import subprocess
from pathlib import Path

import pytest

from raftsim.scenario2_5d import (
    ProceduralScenario2_5DParameters,
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
    assert validation["passed"] is True
    assert "frames/frame_0000.csv" in manifest["frames"]
    assert manifest["probes"]
    assert manifest["cross_sections"]

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


def test_chrono_smoke_target_is_optional_and_outside_unreal():
    physics_dir = Path(__file__).resolve().parents[1]
    cmake_text = (physics_dir / "cpp" / "CMakeLists.txt").read_text(encoding="utf-8")
    smoke_source = (physics_dir / "cpp" / "tools" / "chrono_smoke_test.cpp").read_text(encoding="utf-8")

    assert "find_package(Chrono QUIET)" in cmake_text
    assert "add_executable(raftsim_chrono_smoke" in cmake_text
    assert "Project Chrono not found; skipping raftsim_chrono_smoke target" in cmake_text
    assert "ChSystemSMC" in smoke_source
    assert "chrono_smoke=ok" in smoke_source
