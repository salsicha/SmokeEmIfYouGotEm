"""2.5D raft coupling primitives shared by PyClaw and C++ water outputs."""

from __future__ import annotations

from dataclasses import dataclass

from .math3d import Quaternion, Vec3
from .scenario2_5d import RaftParameters2_5D


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


@dataclass(frozen=True, slots=True)
class RaftSamplePatch:
    """A local raft patch used for buoyancy, drag, and contact sampling."""

    kind: str
    local_position: Vec3
    area_m2: float
    local_normal: Vec3 = Vec3(0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        if self.area_m2 <= 0.0:
            raise ValueError("sample patch area must be positive.")
        object.__setattr__(self, "local_normal", self.local_normal.normalized())


@dataclass(frozen=True, slots=True)
class RaftMassProperties:
    """Mass, inertia, crew offsets, and sampling layout for a raft."""

    total_mass_kg: float
    inertia_diagonal_kg_m2: Vec3
    gravity: Vec3
    guide_offset: Vec3
    passenger_offsets: tuple[Vec3, ...]
    sample_patches: tuple[RaftSamplePatch, ...]

    @property
    def inverse_mass(self) -> float:
        return 1.0 / self.total_mass_kg


def build_default_raft_mass_properties(
    parameters: RaftParameters2_5D | None = None,
    *,
    gravity: Vec3 = Vec3(0.0, 0.0, -9.81),
) -> RaftMassProperties:
    """Build deterministic first-pass raft mass and sampling properties."""

    params = parameters or RaftParameters2_5D()
    total_mass = params.mass_kg + params.guide_mass_kg + params.passenger_mass_kg * params.passenger_count
    height = params.tube_radius_m * 2.0
    inertia = Vec3(
        total_mass * (params.width_m**2 + height**2) / 12.0,
        total_mass * (params.length_m**2 + height**2) / 12.0,
        total_mass * (params.length_m**2 + params.width_m**2) / 12.0,
    )
    return RaftMassProperties(
        total_mass_kg=total_mass,
        inertia_diagonal_kg_m2=inertia,
        gravity=gravity,
        guide_offset=Vec3(-params.length_m * 0.42, 0.0, 0.15),
        passenger_offsets=_passenger_offsets(params),
        sample_patches=_sample_patches(params),
    )


def _passenger_offsets(params: RaftParameters2_5D) -> tuple[Vec3, ...]:
    if params.passenger_count <= 0:
        return ()
    rows = max(1, (params.passenger_count + 1) // 2)
    usable_length = params.length_m * 0.58
    start_x = -usable_length * 0.35
    step = usable_length / max(rows - 1, 1)
    side_y = params.width_m * 0.32
    offsets: list[Vec3] = []
    for index in range(params.passenger_count):
        row = index // 2
        side = -1.0 if index % 2 == 0 else 1.0
        x = start_x + row * step
        offsets.append(Vec3(x, side * side_y, 0.12))
    return tuple(offsets)


def _sample_patches(params: RaftParameters2_5D) -> tuple[RaftSamplePatch, ...]:
    patches: list[RaftSamplePatch] = []
    tube_area = params.tube_radius_m * params.length_m / 4.0
    floor_area = (params.length_m * 0.62) * (params.width_m * 0.42) / 6.0
    for x_fraction in (-0.38, -0.12, 0.14, 0.40):
        x = params.length_m * x_fraction
        patches.append(RaftSamplePatch("left_tube", Vec3(x, -params.width_m * 0.5, 0.0), tube_area))
        patches.append(RaftSamplePatch("right_tube", Vec3(x, params.width_m * 0.5, 0.0), tube_area))
    for x_fraction in (-0.25, 0.0, 0.25):
        for y_fraction in (-0.18, 0.18):
            patches.append(
                RaftSamplePatch(
                    "floor",
                    Vec3(params.length_m * x_fraction, params.width_m * y_fraction, -params.tube_radius_m * 0.55),
                    floor_area,
                )
            )
    return tuple(patches)
