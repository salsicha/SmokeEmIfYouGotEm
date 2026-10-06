"""Profile raft-coupling runs over reference water fields."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from time import perf_counter
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import RaftMassProperties, RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties, sample_total_raft_forces, sum_force_contributions
from raftsim.scenario2_5d import Scenario2_5D
from raftsim.profiling import (Clock, ProfiledSolverRun, SolverProfileReport)


CouplingStateFactory = Callable[[Scenario2_5D, WaterField2_5D, RaftMassProperties], RaftState6DoF]


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


def _default_coupling_state(scenario: Scenario2_5D, water: WaterField2_5D) -> RaftState6DoF:
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    return RaftState6DoF(position=Vec3(center_x, center_y, surface - 0.35))
