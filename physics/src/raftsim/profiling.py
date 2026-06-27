"""Runtime profiling helpers for solver and raft-coupling research loops."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from .dual_solver import CppSolverRunConfig, CppSolverRunResult, run_cpp_solver_scenario
from .pyclaw_reference import PyClawReferenceResult, PyClawRunConfig, run_pyclaw_reference
from .scenario2_5d import Scenario2_5D


@dataclass(frozen=True, slots=True)
class ProfiledSolverRun:
    solver: str
    scenario_id: str
    repetition: int
    grid_cells: int
    simulated_seconds: float
    output_frames: int
    runtime_seconds: float
    seconds_per_simulated_second: float
    cell_seconds_per_simulated_second: float
    validation_passed: bool
    run_status: dict[str, object]

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SolverProfileReport:
    solver: str
    runs: tuple[ProfiledSolverRun, ...]

    @property
    def total_runtime_seconds(self) -> float:
        return sum(run.runtime_seconds for run in self.runs)

    @property
    def mean_runtime_seconds(self) -> float:
        if not self.runs:
            return 0.0
        return self.total_runtime_seconds / len(self.runs)

    @property
    def max_runtime_seconds(self) -> float:
        return max((run.runtime_seconds for run in self.runs), default=0.0)

    @property
    def mean_seconds_per_simulated_second(self) -> float:
        if not self.runs:
            return 0.0
        return sum(run.seconds_per_simulated_second for run in self.runs) / len(self.runs)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "solver": self.solver,
            "summary": {
                "run_count": len(self.runs),
                "total_runtime_seconds": self.total_runtime_seconds,
                "mean_runtime_seconds": self.mean_runtime_seconds,
                "max_runtime_seconds": self.max_runtime_seconds,
                "mean_seconds_per_simulated_second": self.mean_seconds_per_simulated_second,
            },
            "runs": [run.to_json_dict() for run in self.runs],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


PyClawProfileRunner = Callable[..., PyClawReferenceResult]
CppProfileRunner = Callable[..., CppSolverRunResult]
Clock = Callable[[], float]


def profile_pyclaw_reference_runs(
    scenarios: Iterable[Scenario2_5D],
    *,
    config: PyClawRunConfig | None = None,
    repetitions: int = 1,
    output_dir: str | Path | None = None,
    runner: PyClawProfileRunner = run_pyclaw_reference,
    clock: Clock = perf_counter,
) -> SolverProfileReport:
    """Profile PyClaw reference runs for offline research-loop cost."""

    if repetitions < 1:
        raise ValueError("repetitions must be at least 1.")
    cfg = config or PyClawRunConfig()
    output_root = Path(output_dir) if output_dir is not None else None
    runs: list[ProfiledSolverRun] = []
    for scenario in scenarios:
        for repetition in range(repetitions):
            run_output_dir = None
            if output_root is not None:
                run_output_dir = output_root / scenario.metadata.scenario_id / f"rep_{repetition:02d}"
            started = clock()
            result = runner(scenario, config=cfg, output_dir=run_output_dir)
            finished = clock()
            runtime_seconds = max(0.0, finished - started)
            simulated_seconds = max(float(scenario.duration), 1.0e-9)
            grid_cells = scenario.grid.nx * scenario.grid.ny
            runs.append(
                ProfiledSolverRun(
                    solver="pyclaw",
                    scenario_id=scenario.metadata.scenario_id,
                    repetition=repetition,
                    grid_cells=grid_cells,
                    simulated_seconds=float(scenario.duration),
                    output_frames=len(result.frames),
                    runtime_seconds=runtime_seconds,
                    seconds_per_simulated_second=runtime_seconds / simulated_seconds,
                    cell_seconds_per_simulated_second=runtime_seconds / (simulated_seconds * max(grid_cells, 1)),
                    validation_passed=result.validation.passed,
                    run_status=result.run_status,
                )
            )
    return SolverProfileReport("pyclaw", tuple(runs))


def profile_cpp_solver_runs(
    scenarios: Iterable[Scenario2_5D],
    *,
    config: CppSolverRunConfig,
    repetitions: int = 1,
    output_dir: str | Path | None = None,
    runner: CppProfileRunner = run_cpp_solver_scenario,
    clock: Clock = perf_counter,
) -> SolverProfileReport:
    """Profile the standalone C++ reduced solver for target runtime cost."""

    if repetitions < 1:
        raise ValueError("repetitions must be at least 1.")
    output_root = Path(output_dir) if output_dir is not None else None
    runs: list[ProfiledSolverRun] = []
    for scenario in scenarios:
        for repetition in range(repetitions):
            run_output_dir = Path(f"{scenario.metadata.scenario_id}_rep_{repetition:02d}")
            if output_root is not None:
                run_output_dir = output_root / scenario.metadata.scenario_id / f"rep_{repetition:02d}"
            started = clock()
            result = runner(scenario, output_dir=run_output_dir, config=config)
            finished = clock()
            wall_runtime_seconds = max(0.0, finished - started)
            runtime_seconds = max(0.0, result.runtime_seconds)
            simulated_seconds = max(float(scenario.duration), 1.0e-9)
            grid_cells = scenario.grid.nx * scenario.grid.ny
            runs.append(
                ProfiledSolverRun(
                    solver="cpp_reduced",
                    scenario_id=scenario.metadata.scenario_id,
                    repetition=repetition,
                    grid_cells=grid_cells,
                    simulated_seconds=float(scenario.duration),
                    output_frames=_cpp_output_frame_count(result.manifest_path),
                    runtime_seconds=runtime_seconds,
                    seconds_per_simulated_second=runtime_seconds / simulated_seconds,
                    cell_seconds_per_simulated_second=runtime_seconds / (simulated_seconds * max(grid_cells, 1)),
                    validation_passed=result.returncode == 0,
                    run_status={
                        "returncode": result.returncode,
                        "profile_wall_seconds": wall_runtime_seconds,
                        "manifest": str(result.manifest_path),
                        "validation": str(result.validation_path),
                    },
                )
            )
    return SolverProfileReport("cpp_reduced", tuple(runs))


def _cpp_output_frame_count(manifest_path: Path) -> int:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError:
        return 0
    frames = manifest.get("frames", [])
    return len(frames) if isinstance(frames, list) else 0
