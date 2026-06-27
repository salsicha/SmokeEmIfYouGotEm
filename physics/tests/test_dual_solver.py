import json
import shutil
import subprocess
from pathlib import Path

import pytest

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
