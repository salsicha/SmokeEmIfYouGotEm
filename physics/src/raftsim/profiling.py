"""Runtime profiling helpers for solver and raft-coupling research loops."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from .dual_solver import CppSolverRunConfig, CppSolverRunResult, run_cpp_solver_scenario
from .math3d import Vec3
from .pyclaw_reference import (
    PyClawAvailability,
    PyClawReferenceResult,
    PyClawRunConfig,
    build_initial_pyclaw_reference_result,
    run_pyclaw_reference,
)
from .raft_coupling2_5d import (
    RaftMassProperties,
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    sample_total_raft_forces,
    sum_force_contributions,
)
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
CouplingStateFactory = Callable[[Scenario2_5D, WaterField2_5D, RaftMassProperties], RaftState6DoF]
ProbeExportBuilder = Callable[..., PyClawReferenceResult]
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


def profile_raft_coupling_runs(
    scenarios: Iterable[Scenario2_5D],
    *,
    repetitions: int = 1,
    samples_per_run: int = 1,
    state_factory: CouplingStateFactory | None = None,
    clock: Clock = perf_counter,
) -> SolverProfileReport:
    """Profile raft force sampling cost over solver-neutral water fields."""

    if repetitions < 1:
        raise ValueError("repetitions must be at least 1.")
    if samples_per_run < 1:
        raise ValueError("samples_per_run must be at least 1.")
    runs: list[ProfiledSolverRun] = []
    for scenario in scenarios:
        water = WaterField2_5D.from_scenario_initial_state(scenario)
        properties = build_default_raft_mass_properties(scenario.raft)
        state = state_factory(scenario, water, properties) if state_factory is not None else _default_coupling_state(scenario, water)
        for repetition in range(repetitions):
            last_contribution_count = 0
            last_force_magnitude = 0.0
            started = clock()
            for _ in range(samples_per_run):
                contributions = sample_total_raft_forces(state, properties, water)
                total_force, _ = sum_force_contributions(contributions)
                last_contribution_count = len(contributions)
                last_force_magnitude = total_force.magnitude
            finished = clock()
            runtime_seconds = max(0.0, finished - started)
            simulated_seconds = max(float(scenario.fixed_dt * samples_per_run), 1.0e-9)
            grid_cells = scenario.grid.nx * scenario.grid.ny
            runs.append(
                ProfiledSolverRun(
                    solver="raft_coupling",
                    scenario_id=scenario.metadata.scenario_id,
                    repetition=repetition,
                    grid_cells=grid_cells,
                    simulated_seconds=simulated_seconds,
                    output_frames=samples_per_run,
                    runtime_seconds=runtime_seconds,
                    seconds_per_simulated_second=runtime_seconds / simulated_seconds,
                    cell_seconds_per_simulated_second=runtime_seconds / (simulated_seconds * max(grid_cells, 1)),
                    validation_passed=True,
                    run_status={
                        "samples_per_run": samples_per_run,
                        "last_contribution_count": last_contribution_count,
                        "last_force_magnitude": last_force_magnitude,
                    },
                )
            )
    return SolverProfileReport("raft_coupling", tuple(runs))


def profile_probe_export_runs(
    scenarios: Iterable[Scenario2_5D],
    *,
    config: PyClawRunConfig | None = None,
    repetitions: int = 1,
    output_dir: str | Path | None = None,
    builder: ProbeExportBuilder = build_initial_pyclaw_reference_result,
    clock: Clock = perf_counter,
) -> SolverProfileReport:
    """Profile probe sampling and reference artifact export cost."""

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
            result = builder(
                scenario,
                config=cfg,
                availability=PyClawAvailability(False, "probe/export profile"),
            )
            if run_output_dir is not None:
                result.write_output(run_output_dir)
            finished = clock()
            runtime_seconds = max(0.0, finished - started)
            simulated_seconds = max(float(scenario.duration), 1.0e-9)
            grid_cells = scenario.grid.nx * scenario.grid.ny
            runs.append(
                ProfiledSolverRun(
                    solver="probe_export",
                    scenario_id=scenario.metadata.scenario_id,
                    repetition=repetition,
                    grid_cells=grid_cells,
                    simulated_seconds=float(scenario.duration),
                    output_frames=len(result.frames),
                    runtime_seconds=runtime_seconds,
                    seconds_per_simulated_second=runtime_seconds / simulated_seconds,
                    cell_seconds_per_simulated_second=runtime_seconds / (simulated_seconds * max(grid_cells, 1)),
                    validation_passed=result.validation.passed,
                    run_status={
                        "probe_count": len(result.probes),
                        "cross_section_count": len(result.cross_sections),
                        "output_dir": str(run_output_dir) if run_output_dir is not None else "",
                    },
                )
            )
    return SolverProfileReport("probe_export", tuple(runs))


def _default_coupling_state(scenario: Scenario2_5D, water: WaterField2_5D) -> RaftState6DoF:
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    return RaftState6DoF(position=Vec3(center_x, center_y, surface - 0.35))
