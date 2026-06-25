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

    assert manifest["solver"] == "raftsim_water_reduced_cpp_v0"
    assert validation["passed"] is True
    assert "frames/frame_0000.csv" in manifest["frames"]
    assert manifest["probes"]
    assert manifest["cross_sections"]
