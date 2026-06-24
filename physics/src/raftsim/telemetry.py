"""Telemetry capture for deterministic physics runs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .math3d import Vec3


@dataclass(frozen=True, slots=True)
class ForceContribution:
    """One named force/torque contribution recorded during a simulation frame."""

    name: str
    force: Vec3 = field(default_factory=Vec3)
    torque: Vec3 = field(default_factory=Vec3)
    application_point: Vec3 | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(slots=True)
class TelemetryFrame:
    """Telemetry for one fixed simulation step."""

    step_index: int
    time: float
    dt: float
    forces: list[ForceContribution] = field(default_factory=list)

    def record_force(
        self,
        name: str,
        force: Vec3,
        *,
        torque: Vec3 | None = None,
        application_point: Vec3 | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ForceContribution:
        contribution = ForceContribution(
            name=name,
            force=force,
            torque=torque or Vec3(),
            application_point=application_point,
            metadata=metadata or {},
        )
        self.forces.append(contribution)
        return contribution

    @property
    def net_force(self) -> Vec3:
        total = Vec3()
        for contribution in self.forces:
            total += contribution.force
        return total

    @property
    def net_torque(self) -> Vec3:
        total = Vec3()
        for contribution in self.forces:
            total += contribution.torque
        return total

    def force_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for contribution in self.forces:
            point = contribution.application_point
            rows.append(
                {
                    "step_index": self.step_index,
                    "time": self.time,
                    "dt": self.dt,
                    "name": contribution.name,
                    "force_x": contribution.force.x,
                    "force_y": contribution.force.y,
                    "force_z": contribution.force.z,
                    "torque_x": contribution.torque.x,
                    "torque_y": contribution.torque.y,
                    "torque_z": contribution.torque.z,
                    "application_x": "" if point is None else point.x,
                    "application_y": "" if point is None else point.y,
                    "application_z": "" if point is None else point.z,
                    "metadata": json.dumps(dict(contribution.metadata), sort_keys=True),
                }
            )
        return rows


class TelemetryRecorder:
    """Collects per-step telemetry with explicit frame boundaries."""

    FIELDNAMES = [
        "step_index",
        "time",
        "dt",
        "name",
        "force_x",
        "force_y",
        "force_z",
        "torque_x",
        "torque_y",
        "torque_z",
        "application_x",
        "application_y",
        "application_z",
        "metadata",
    ]

    def __init__(self) -> None:
        self._frames: list[TelemetryFrame] = []
        self._current_frame: TelemetryFrame | None = None

    @property
    def frames(self) -> tuple[TelemetryFrame, ...]:
        return tuple(self._frames)

    @property
    def current_frame(self) -> TelemetryFrame:
        if self._current_frame is None:
            raise RuntimeError("No active telemetry frame.")
        return self._current_frame

    def begin_frame(self, *, step_index: int, time: float, dt: float) -> TelemetryFrame:
        if self._current_frame is not None:
            raise RuntimeError("Cannot begin a new telemetry frame before ending the current one.")
        self._current_frame = TelemetryFrame(step_index=step_index, time=time, dt=dt)
        return self._current_frame

    def record_force(
        self,
        name: str,
        force: Vec3,
        *,
        torque: Vec3 | None = None,
        application_point: Vec3 | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ForceContribution:
        return self.current_frame.record_force(
            name,
            force,
            torque=torque,
            application_point=application_point,
            metadata=metadata,
        )

    def end_frame(self) -> TelemetryFrame:
        frame = self.current_frame
        self._frames.append(frame)
        self._current_frame = None
        return frame

    def force_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for frame in self._frames:
            rows.extend(frame.force_rows())
        return rows

    def write_force_csv(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(self.force_rows())
        return output_path
