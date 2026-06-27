"""2.5D raft coupling primitives shared by PyClaw and C++ water outputs."""

from __future__ import annotations

from dataclasses import dataclass

from .math3d import Quaternion, Vec3


@dataclass(frozen=True, slots=True)
class RaftState6DoF:
    """Rigid raft state over a 2.5D water field."""

    position: Vec3 = Vec3()
    orientation: Quaternion = Quaternion()
    linear_velocity: Vec3 = Vec3()
    angular_velocity: Vec3 = Vec3()

    def __post_init__(self) -> None:
        object.__setattr__(self, "orientation", self.orientation.normalized())

    def advance(
        self,
        dt: float,
        *,
        linear_acceleration: Vec3 = Vec3(),
        angular_acceleration: Vec3 = Vec3(),
    ) -> RaftState6DoF:
        """Return a deterministic semi-implicit fixed-step state update."""

        if dt < 0.0:
            raise ValueError("dt must be non-negative.")
        new_linear_velocity = self.linear_velocity + linear_acceleration * dt
        new_angular_velocity = self.angular_velocity + angular_acceleration * dt
        return RaftState6DoF(
            position=self.position + new_linear_velocity * dt,
            orientation=self.orientation.integrate_angular_velocity(new_angular_velocity, dt),
            linear_velocity=new_linear_velocity,
            angular_velocity=new_angular_velocity,
        )

    def world_point(self, local_point: Vec3) -> Vec3:
        """Transform a local raft point into world coordinates."""

        return self.position + self.orientation.rotate_vector(local_point)

    def point_velocity(self, local_point: Vec3) -> Vec3:
        """Return world velocity at a local raft point."""

        world_offset = self.orientation.rotate_vector(local_point)
        return self.linear_velocity + self.angular_velocity.cross(world_offset)
