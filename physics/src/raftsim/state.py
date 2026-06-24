"""Simulation state containers."""

from __future__ import annotations

from dataclasses import dataclass, field

from .math3d import Quaternion, Vec3


@dataclass(slots=True)
class BodyState:
    """Minimal 6-DoF body state for Milestone 1 raft dynamics."""

    position: Vec3 = field(default_factory=Vec3)
    orientation: Quaternion = field(default_factory=Quaternion.identity)
    linear_velocity: Vec3 = field(default_factory=Vec3)
    angular_velocity: Vec3 = field(default_factory=Vec3)

    def copy(self) -> BodyState:
        return BodyState(
            position=self.position,
            orientation=self.orientation,
            linear_velocity=self.linear_velocity,
            angular_velocity=self.angular_velocity,
        )
