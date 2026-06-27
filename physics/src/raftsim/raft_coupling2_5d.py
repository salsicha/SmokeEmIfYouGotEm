"""2.5D raft coupling primitives shared by PyClaw and C++ water outputs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .math3d import Quaternion, Vec3
from .scenario2_5d import Feature2_5D, RaftParameters2_5D, Scenario2_5D

FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]


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


@dataclass(frozen=True, slots=True)
class WaterSample2_5D:
    """Solver-neutral water sample at one world position."""

    x: float
    y: float
    surface_height: float
    bed_height: float
    depth: float
    velocity: Vec3
    normal: Vec3
    wet: bool
    roughness: float
    feature_tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WaterField2_5D:
    """Queryable 2.5D water field shared by PyClaw and C++ outputs."""

    origin_x: float
    origin_y: float
    dx: float
    dy: float
    bed: FloatGrid
    depth: FloatGrid
    eta: FloatGrid
    u: FloatGrid
    v: FloatGrid
    wet: BoolGrid
    normal_x: FloatGrid
    normal_y: FloatGrid
    normal_z: FloatGrid
    roughness: float = 0.035
    features: tuple[Feature2_5D, ...] = ()

    def __post_init__(self) -> None:
        shape = np.asarray(self.depth).shape
        for name in ("bed", "eta", "u", "v", "normal_x", "normal_y", "normal_z"):
            array = np.asarray(getattr(self, name), dtype=np.float64)
            if array.shape != shape:
                raise ValueError(f"{name} shape {array.shape} does not match depth shape {shape}.")
            object.__setattr__(self, name, array.copy())
        wet = np.asarray(self.wet, dtype=np.bool_)
        if wet.shape != shape:
            raise ValueError(f"wet shape {wet.shape} does not match depth shape {shape}.")
        object.__setattr__(self, "depth", np.asarray(self.depth, dtype=np.float64).copy())
        object.__setattr__(self, "wet", wet.copy())
        object.__setattr__(self, "features", tuple(self.features))

    @classmethod
    def from_scenario_initial_state(cls, scenario: Scenario2_5D) -> WaterField2_5D:
        normal_x, normal_y, normal_z = _surface_normals(scenario.initial_state.eta, scenario.grid.dx, scenario.grid.dy)
        return cls(
            origin_x=scenario.grid.origin_x,
            origin_y=scenario.grid.origin_y,
            dx=scenario.grid.dx,
            dy=scenario.grid.dy,
            bed=scenario.bed,
            depth=scenario.initial_state.depth,
            eta=scenario.initial_state.eta,
            u=scenario.initial_state.u,
            v=scenario.initial_state.v,
            wet=scenario.initial_state.wet,
            normal_x=normal_x,
            normal_y=normal_y,
            normal_z=normal_z,
            roughness=scenario.roughness,
            features=scenario.features,
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self.depth.shape

    def sample(self, x: float, y: float) -> WaterSample2_5D:
        row, col = self._nearest_index(x, y)
        normal = Vec3(
            _bilinear(self.normal_x, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
            _bilinear(self.normal_y, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
            _bilinear(self.normal_z, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
        ).normalized()
        return WaterSample2_5D(
            x=x,
            y=y,
            surface_height=_bilinear(self.eta, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
            bed_height=_bilinear(self.bed, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
            depth=max(0.0, _bilinear(self.depth, x, y, self.origin_x, self.origin_y, self.dx, self.dy)),
            velocity=Vec3(
                _bilinear(self.u, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
                _bilinear(self.v, x, y, self.origin_x, self.origin_y, self.dx, self.dy),
                0.0,
            ),
            normal=normal,
            wet=bool(self.wet[row, col]),
            roughness=self.roughness,
            feature_tags=_feature_tags_at(x, y, self.features, self.dx, self.dy),
        )

    def _nearest_index(self, x: float, y: float) -> tuple[int, int]:
        ny, nx = self.shape
        col = int(np.clip(round((x - self.origin_x) / self.dx), 0, nx - 1))
        row = int(np.clip(round((y - self.origin_y) / self.dy), 0, ny - 1))
        return row, col


def _surface_normals(eta: FloatGrid, dx: float, dy: float) -> tuple[FloatGrid, FloatGrid, FloatGrid]:
    slope_y, slope_x = np.gradient(np.asarray(eta, dtype=np.float64), dy, dx)
    normal_x = -slope_x
    normal_y = -slope_y
    normal_z = np.ones_like(normal_x)
    length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    return normal_x / length, normal_y / length, normal_z / length


def _bilinear(array: FloatGrid, x: float, y: float, origin_x: float, origin_y: float, dx: float, dy: float) -> float:
    ny, nx = array.shape
    fx = np.clip((x - origin_x) / dx, 0.0, nx - 1.0)
    fy = np.clip((y - origin_y) / dy, 0.0, ny - 1.0)
    x0 = int(np.floor(fx))
    y0 = int(np.floor(fy))
    x1 = min(x0 + 1, nx - 1)
    y1 = min(y0 + 1, ny - 1)
    tx = fx - x0
    ty = fy - y0
    a = array[y0, x0] * (1.0 - tx) + array[y0, x1] * tx
    b = array[y1, x0] * (1.0 - tx) + array[y1, x1] * tx
    return float(a * (1.0 - ty) + b * ty)


def _feature_tags_at(x: float, y: float, features: tuple[Feature2_5D, ...], dx: float, dy: float) -> tuple[str, ...]:
    tags: list[str] = []
    for feature in features:
        scale_x = max(feature.length * 0.5, feature.radius, dx)
        scale_y = max(feature.width * 0.5, feature.radius, dy)
        distance = ((x - feature.center[0]) / scale_x) ** 2 + ((y - feature.center[1]) / scale_y) ** 2
        if distance <= 1.0:
            tags.append(feature.kind)
    return tuple(tags)


@dataclass(frozen=True, slots=True)
class RaftForceContribution2_5D:
    """One force/torque contribution sampled from a 2.5D water field."""

    name: str
    force: Vec3
    torque: Vec3
    application_point: Vec3
    metadata: dict[str, float | str] | None = None


def sample_buoyancy_forces(
    state: RaftState6DoF,
    properties: RaftMassProperties,
    water: WaterField2_5D,
    *,
    water_density_kg_m3: float = 1000.0,
) -> tuple[RaftForceContribution2_5D, ...]:
    """Sample buoyancy from submerged raft patches using local water normals."""

    contributions: list[RaftForceContribution2_5D] = []
    gravity_magnitude = abs(properties.gravity.z) if abs(properties.gravity.z) > 1.0e-9 else 9.81
    for index, patch in enumerate(properties.sample_patches):
        point = state.world_point(patch.local_position)
        sample = water.sample(point.x, point.y)
        submerged_depth = sample.surface_height - point.z
        if submerged_depth <= 0.0 or not sample.wet:
            continue
        force_magnitude = water_density_kg_m3 * gravity_magnitude * patch.area_m2 * submerged_depth
        force = sample.normal * force_magnitude
        torque = (point - state.position).cross(force)
        contributions.append(
            RaftForceContribution2_5D(
                name=f"buoyancy:{patch.kind}:{index}",
                force=force,
                torque=torque,
                application_point=point,
                metadata={
                    "kind": patch.kind,
                    "submerged_depth": submerged_depth,
                    "area_m2": patch.area_m2,
                },
            )
        )
    return tuple(contributions)


def sum_force_contributions(contributions: tuple[RaftForceContribution2_5D, ...]) -> tuple[Vec3, Vec3]:
    """Return total force and torque for a tuple of contributions."""

    total_force = Vec3()
    total_torque = Vec3()
    for contribution in contributions:
        total_force += contribution.force
        total_torque += contribution.torque
    return total_force, total_torque
