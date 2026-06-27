"""Run PyClaw and the C++ reduced solver against identical 2.5D packages."""

from __future__ import annotations

import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .pyclaw_reference import PyClawRunConfig, run_pyclaw_reference
from .scenario2_5d import Scenario2_5D, read_scenario2_5d_package


@dataclass(frozen=True, slots=True)
class CppSolverRunConfig:
    """Runtime settings for the standalone C++ reduced water solver."""

    executable: Path
    steps: int | None = None
    frame_interval: int | None = None
    feature_strength_scale: float = 1.0
    allow_validation_failure: bool = True

    def __post_init__(self) -> None:
        if self.steps is not None and self.steps < 0:
            raise ValueError("steps must be non-negative when provided.")
        if self.frame_interval is not None and self.frame_interval < 1:
            raise ValueError("frame_interval must be at least 1 when provided.")
        if self.feature_strength_scale <= 0.0:
            raise ValueError("feature_strength_scale must be positive.")

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["executable"] = str(self.executable)
        return data


@dataclass(frozen=True, slots=True)
class DualSolverRunConfig:
    """Configuration for one PyClaw-vs-C++ dual solver run."""

    pyclaw: PyClawRunConfig = field(default_factory=lambda: PyClawRunConfig(num_output_times=4))
    cpp: CppSolverRunConfig | None = None

    def require_cpp(self) -> CppSolverRunConfig:
        if self.cpp is None:
            raise ValueError("A C++ solver executable is required for dual-solver runs.")
        return self.cpp


@dataclass(frozen=True, slots=True)
class CppSolverRunResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    output_dir: Path
    manifest_path: Path
    validation_path: Path
    runtime_seconds: float

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_dir": _relative_or_absolute(self.output_dir, root),
            "manifest": _relative_or_absolute(self.manifest_path, root),
            "validation": _relative_or_absolute(self.validation_path, root),
            "runtime_seconds": self.runtime_seconds,
        }


@dataclass(frozen=True, slots=True)
class DualSolverRunResult:
    scenario_id: str
    output_dir: Path
    scenario_dir: Path
    pyclaw_output_dir: Path
    pyclaw_runtime_seconds: float
    simulated_duration: float
    cpp: CppSolverRunResult
    manifest_path: Path

    def to_json_dict(self) -> dict[str, object]:
        root = self.output_dir
        return {
            "scenario_id": self.scenario_id,
            "scenario_package": _relative_or_absolute(self.scenario_dir, root),
            "scenario_json": _relative_or_absolute(self.scenario_dir / "scenario.json", root),
            "pyclaw": {
                "output_dir": _relative_or_absolute(self.pyclaw_output_dir, root),
                "manifest": _relative_or_absolute(self.pyclaw_output_dir / "manifest.json", root),
                "validation": _relative_or_absolute(self.pyclaw_output_dir / "validation.json", root),
                "runtime_seconds": self.pyclaw_runtime_seconds,
                "seconds_per_simulated_second": _seconds_per_simulated_second(
                    self.pyclaw_runtime_seconds,
                    self.simulated_duration,
                ),
            },
            "cpp": self.cpp.to_json_dict(root),
            "runtime": {
                "simulated_duration_seconds": self.simulated_duration,
                "pyclaw_runtime_seconds": self.pyclaw_runtime_seconds,
                "pyclaw_seconds_per_simulated_second": _seconds_per_simulated_second(
                    self.pyclaw_runtime_seconds,
                    self.simulated_duration,
                ),
                "cpp_runtime_seconds": self.cpp.runtime_seconds,
                "cpp_seconds_per_simulated_second": _seconds_per_simulated_second(
                    self.cpp.runtime_seconds,
                    self.simulated_duration,
                ),
            },
        }


def run_dual_solver_scenario(
    scenario_or_path: Scenario2_5D | str | Path,
    *,
    output_dir: str | Path,
    config: DualSolverRunConfig,
) -> DualSolverRunResult:
    """Run PyClaw and C++ on the same shared 2.5D scenario package."""

    cpp_config = config.require_cpp()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    scenario, scenario_dir = _materialize_scenario_package(scenario_or_path, root)

    pyclaw_output_dir = root / "pyclaw_reference" / scenario.metadata.scenario_id
    pyclaw_start = time.perf_counter()
    run_pyclaw_reference(scenario_dir, config=config.pyclaw, output_dir=pyclaw_output_dir)
    pyclaw_runtime_seconds = time.perf_counter() - pyclaw_start

    cpp_result = _run_cpp_solver(
        scenario,
        scenario_dir=scenario_dir,
        output_root=root / "cpp_solver",
        config=cpp_config,
    )

    result = DualSolverRunResult(
        scenario_id=scenario.metadata.scenario_id,
        output_dir=root,
        scenario_dir=scenario_dir,
        pyclaw_output_dir=pyclaw_output_dir,
        pyclaw_runtime_seconds=pyclaw_runtime_seconds,
        simulated_duration=scenario.duration,
        cpp=cpp_result,
        manifest_path=root / "dual_solver_manifest.json",
    )
    result.manifest_path.write_text(json.dumps(result.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return result


def _materialize_scenario_package(scenario_or_path: Scenario2_5D | str | Path, root: Path) -> tuple[Scenario2_5D, Path]:
    if isinstance(scenario_or_path, Scenario2_5D):
        scenario = scenario_or_path
        scenario_dir = root / "scenario" / scenario.metadata.scenario_id
        scenario.write_package(scenario_dir)
        return scenario, scenario_dir

    path = Path(scenario_or_path)
    scenario_dir = path.parent if path.name == "scenario.json" else path
    scenario = read_scenario2_5d_package(scenario_dir)
    return scenario, scenario_dir


def _run_cpp_solver(
    scenario: Scenario2_5D,
    *,
    scenario_dir: Path,
    output_root: Path,
    config: CppSolverRunConfig,
) -> CppSolverRunResult:
    steps = config.steps
    if steps is None:
        steps = int(math.ceil(scenario.duration / scenario.fixed_dt))
    frame_interval = config.frame_interval
    if frame_interval is None:
        frame_interval = max(1, steps // max(1, PyClawRunConfig().num_output_times))

    command = (
        str(config.executable),
        "--scenario",
        str(scenario_dir),
        "--output",
        str(output_root),
        "--steps",
        str(steps),
        "--frame-interval",
        str(frame_interval),
        "--feature-strength-scale",
        str(config.feature_strength_scale),
    )
    start = time.perf_counter()
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    runtime_seconds = time.perf_counter() - start
    if completed.returncode != 0 and not (config.allow_validation_failure and completed.returncode == 2):
        raise RuntimeError(
            "C++ solver run failed with return code "
            f"{completed.returncode}:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )

    run_output = output_root / scenario.metadata.scenario_id
    return CppSolverRunResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        output_dir=run_output,
        manifest_path=run_output / "manifest.json",
        validation_path=run_output / "validation.json",
        runtime_seconds=runtime_seconds,
    )


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _seconds_per_simulated_second(runtime_seconds: float, simulated_duration: float) -> float:
    return runtime_seconds / max(simulated_duration, 1.0e-12)
