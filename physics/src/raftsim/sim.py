"""Deterministic fixed-step simulation loop."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .math3d import Vec3
from .telemetry import TelemetryFrame, TelemetryRecorder


@runtime_checkable
class SimulationSystem(Protocol):
    """Protocol for systems that participate in fixed-step simulation."""

    def step(self, simulation: Simulation, dt: float) -> None:
        """Advance the system by one fixed timestep."""


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration for deterministic fixed-step runs."""

    fixed_dt: float = 1.0 / 60.0
    seed: int = 0

    def __post_init__(self) -> None:
        if self.fixed_dt <= 0.0:
            raise ValueError("fixed_dt must be greater than zero.")


class Simulation:
    """Small deterministic simulation kernel.

    The loop owns time, step index, seeded randomness, pluggable systems, and
    telemetry frame boundaries. It intentionally does not implement raft
    hydrodynamics yet; Milestone 1 systems will plug into this class.
    """

    def __init__(
        self,
        *,
        config: SimulationConfig | None = None,
        systems: list[SimulationSystem] | None = None,
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.systems: list[SimulationSystem] = list(systems or [])
        self.telemetry = telemetry or TelemetryRecorder()
        self.random = random.Random(self.config.seed)
        self.time = 0.0
        self.step_index = 0

    def add_system(self, system: SimulationSystem) -> None:
        self.systems.append(system)

    def record_force(
        self,
        name: str,
        force: Vec3,
        *,
        torque: Vec3 | None = None,
        application_point: Vec3 | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.telemetry.record_force(
            name,
            force,
            torque=torque,
            application_point=application_point,
            metadata=metadata,
        )

    def step(self, count: int = 1) -> tuple[TelemetryFrame, ...]:
        if count < 0:
            raise ValueError("count must be non-negative.")

        completed_frames: list[TelemetryFrame] = []
        for _ in range(count):
            dt = self.config.fixed_dt
            self.telemetry.begin_frame(step_index=self.step_index, time=self.time, dt=dt)
            for system in self.systems:
                system.step(self, dt)
            completed_frames.append(self.telemetry.end_frame())
            self.time += dt
            self.step_index += 1
        return tuple(completed_frames)

    def run_for(self, duration: float) -> tuple[TelemetryFrame, ...]:
        if duration < 0.0:
            raise ValueError("duration must be non-negative.")
        count = duration / self.config.fixed_dt
        rounded_count = round(count)
        if not math.isclose(count, rounded_count, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("duration must be an integer multiple of fixed_dt.")
        return self.step(int(rounded_count))

    def reset(self) -> None:
        self.telemetry = TelemetryRecorder()
        self.random = random.Random(self.config.seed)
        self.time = 0.0
        self.step_index = 0
