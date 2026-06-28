"""2.5D raft coupling primitives shared by PyClaw and C++ water outputs."""

from __future__ import annotations

import csv
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

    @classmethod
    def from_reference_frame_npz(cls, scenario: Scenario2_5D, frame_path: str) -> WaterField2_5D:
        with np.load(frame_path) as data:
            h = np.asarray(data["h"], dtype=np.float64)
            eta = np.asarray(data["eta"], dtype=np.float64)
            return cls(
                origin_x=scenario.grid.origin_x,
                origin_y=scenario.grid.origin_y,
                dx=scenario.grid.dx,
                dy=scenario.grid.dy,
                bed=eta - h,
                depth=h,
                eta=eta,
                u=np.asarray(data["u"], dtype=np.float64),
                v=np.asarray(data["v"], dtype=np.float64),
                wet=np.asarray(data["wet"], dtype=np.bool_),
                normal_x=np.asarray(data["normal_x"], dtype=np.float64),
                normal_y=np.asarray(data["normal_y"], dtype=np.float64),
                normal_z=np.asarray(data["normal_z"], dtype=np.float64),
                roughness=scenario.roughness,
                features=scenario.features,
            )

    @classmethod
    def from_geoclaw_frame_npz(cls, scenario: Scenario2_5D, frame_path: str) -> WaterField2_5D:
        return cls.from_reference_frame_npz(scenario, frame_path)

    @classmethod
    def from_pyclaw_frame_npz(cls, scenario: Scenario2_5D, frame_path: str) -> WaterField2_5D:
        return cls.from_reference_frame_npz(scenario, frame_path)

    @classmethod
    def from_cpp_frame_csv(cls, scenario: Scenario2_5D, frame_path: str) -> WaterField2_5D:
        rows: list[dict[str, str]] = []
        with open(frame_path, encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"C++ frame CSV is empty: {frame_path}")
        ny, nx = scenario.grid.shape
        arrays = {
            "h": np.zeros((ny, nx), dtype=np.float64),
            "eta": np.zeros((ny, nx), dtype=np.float64),
            "u": np.zeros((ny, nx), dtype=np.float64),
            "v": np.zeros((ny, nx), dtype=np.float64),
            "wet": np.zeros((ny, nx), dtype=np.bool_),
            "normal_x": np.zeros((ny, nx), dtype=np.float64),
            "normal_y": np.zeros((ny, nx), dtype=np.float64),
            "normal_z": np.zeros((ny, nx), dtype=np.float64),
        }
        for row in rows:
            row_index = int(row["row"])
            col_index = int(row["col"])
            arrays["h"][row_index, col_index] = float(row["h"])
            arrays["eta"][row_index, col_index] = float(row["eta"])
            arrays["u"][row_index, col_index] = float(row["u"])
            arrays["v"][row_index, col_index] = float(row["v"])
            arrays["wet"][row_index, col_index] = bool(int(row["wet"]))
            arrays["normal_x"][row_index, col_index] = float(row["normal_x"])
            arrays["normal_y"][row_index, col_index] = float(row["normal_y"])
            arrays["normal_z"][row_index, col_index] = float(row["normal_z"])
        h = arrays["h"]
        eta = arrays["eta"]
        return cls(
            origin_x=scenario.grid.origin_x,
            origin_y=scenario.grid.origin_y,
            dx=scenario.grid.dx,
            dy=scenario.grid.dy,
            bed=eta - h,
            depth=h,
            eta=eta,
            u=arrays["u"],
            v=arrays["v"],
            wet=arrays["wet"],
            normal_x=arrays["normal_x"],
            normal_y=arrays["normal_y"],
            normal_z=arrays["normal_z"],
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


@dataclass(frozen=True, slots=True)
class PaddleBladePose2_5D:
    """Paddle blade pose and local stroke velocity relative to the raft."""

    local_position: Vec3
    local_velocity: Vec3 = Vec3()
    blade_area_m2: float = 0.075

    def __post_init__(self) -> None:
        if self.blade_area_m2 <= 0.0:
            raise ValueError("blade_area_m2 must be positive.")


@dataclass(frozen=True, slots=True)
class PaddleBladeSample2_5D:
    """Water-relative blade sample for paddle force models."""

    world_position: Vec3
    blade_velocity: Vec3
    water_velocity: Vec3
    relative_velocity: Vec3
    depth: float
    submerged: bool
    feature_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RaftForceEnvelope2_5D:
    total_force: Vec3
    total_torque: Vec3
    max_contribution_force: float
    max_contribution_torque: float
    contribution_count: int
    outcome: str


@dataclass(frozen=True, slots=True)
class RaftSolverForceComparison2_5D:
    reference: RaftForceEnvelope2_5D
    candidate: RaftForceEnvelope2_5D
    reference_next_state: RaftState6DoF
    candidate_next_state: RaftState6DoF
    force_delta: Vec3
    torque_delta: Vec3
    trajectory_position_delta: float
    trajectory_velocity_delta: float
    outcome_match: bool


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


def sample_paddle_blade(
    state: RaftState6DoF,
    blade: PaddleBladePose2_5D,
    water: WaterField2_5D,
) -> PaddleBladeSample2_5D:
    """Sample paddle blade depth and velocity relative to local water."""

    world_position = state.world_point(blade.local_position)
    local_blade_velocity = state.orientation.rotate_vector(blade.local_velocity)
    blade_velocity = state.point_velocity(blade.local_position) + local_blade_velocity
    water_sample = water.sample(world_position.x, world_position.y)
    depth = water_sample.surface_height - world_position.z
    return PaddleBladeSample2_5D(
        world_position=world_position,
        blade_velocity=blade_velocity,
        water_velocity=water_sample.velocity,
        relative_velocity=blade_velocity - water_sample.velocity,
        depth=depth,
        submerged=depth > 0.0 and water_sample.wet,
        feature_tags=water_sample.feature_tags,
    )


def sum_force_contributions(contributions: tuple[RaftForceContribution2_5D, ...]) -> tuple[Vec3, Vec3]:
    """Return total force and torque for a tuple of contributions."""

    total_force = Vec3()
    total_torque = Vec3()
    for contribution in contributions:
        total_force += contribution.force
        total_torque += contribution.torque
    return total_force, total_torque


def sample_hydrodynamic_forces(
    state: RaftState6DoF,
    properties: RaftMassProperties,
    water: WaterField2_5D,
    *,
    water_density_kg_m3: float = 1000.0,
    vertical_damping: float = 450.0,
    horizontal_drag_coefficient: float = 1.25,
    slope_force_scale: float = 1.0,
    added_mass_coefficient: float = 0.35,
) -> tuple[RaftForceContribution2_5D, ...]:
    """Sample damping, drag, surface-slope, and added-mass proxy forces."""

    contributions: list[RaftForceContribution2_5D] = []
    gravity_magnitude = abs(properties.gravity.z) if abs(properties.gravity.z) > 1.0e-9 else 9.81
    patch_mass = properties.total_mass_kg / max(len(properties.sample_patches), 1)
    for index, patch in enumerate(properties.sample_patches):
        point = state.world_point(patch.local_position)
        sample = water.sample(point.x, point.y)
        point_velocity = state.point_velocity(patch.local_position)
        relative = point_velocity - sample.velocity
        horizontal_relative = Vec3(relative.x, relative.y, 0.0)
        horizontal_speed = horizontal_relative.magnitude
        force = Vec3()

        if sample.wet:
            force += Vec3(0.0, 0.0, -vertical_damping * relative.z * patch.area_m2)
            if horizontal_speed > 1.0e-9:
                drag = horizontal_relative * (
                    -0.5 * water_density_kg_m3 * horizontal_drag_coefficient * patch.area_m2 * horizontal_speed
                )
                added_mass = horizontal_relative * (
                    -added_mass_coefficient * water_density_kg_m3 * patch.area_m2 * max(sample.depth, 0.05)
                )
                force += drag + added_mass
            slope_force = Vec3(sample.normal.x, sample.normal.y, 0.0) * (patch_mass * gravity_magnitude * slope_force_scale)
            force += slope_force

        if force.magnitude_squared <= 1.0e-18:
            continue
        torque = (point - state.position).cross(force)
        contributions.append(
            RaftForceContribution2_5D(
                name=f"hydrodynamic:{patch.kind}:{index}",
                force=force,
                torque=torque,
                application_point=point,
                metadata={
                    "kind": patch.kind,
                    "relative_speed": horizontal_speed,
                    "depth": sample.depth,
                },
            )
        )
    return tuple(contributions)


def sample_grounding_forces(
    state: RaftState6DoF,
    properties: RaftMassProperties,
    water: WaterField2_5D,
    *,
    contact_stiffness: float = 12000.0,
    contact_damping: float = 1200.0,
    grounding_friction: float = 0.65,
) -> tuple[RaftForceContribution2_5D, ...]:
    """Sample bed/rock/ledge/shallow grounding contact forces."""

    contributions: list[RaftForceContribution2_5D] = []
    for index, patch in enumerate(properties.sample_patches):
        point = state.world_point(patch.local_position)
        sample = water.sample(point.x, point.y)
        penetration = sample.bed_height - point.z
        if penetration <= 0.0 and not _has_grounding_feature(sample.feature_tags):
            continue
        feature_scale = _grounding_feature_scale(sample.feature_tags)
        effective_penetration = max(penetration, 0.03 if feature_scale > 1.0 and sample.depth < 0.35 else 0.0)
        if effective_penetration <= 0.0:
            continue
        point_velocity = state.point_velocity(patch.local_position)
        normal_speed = min(point_velocity.z, 0.0)
        normal_force = contact_stiffness * feature_scale * effective_penetration - contact_damping * normal_speed
        horizontal_velocity = Vec3(point_velocity.x, point_velocity.y, 0.0)
        friction = Vec3()
        if horizontal_velocity.magnitude > 1.0e-9:
            friction = horizontal_velocity.normalized() * (-grounding_friction * normal_force)
        force = Vec3(0.0, 0.0, normal_force) + friction
        torque = (point - state.position).cross(force)
        contributions.append(
            RaftForceContribution2_5D(
                name=f"grounding:{patch.kind}:{index}",
                force=force,
                torque=torque,
                application_point=point,
                metadata={
                    "kind": patch.kind,
                    "penetration": effective_penetration,
                    "feature_tags": ",".join(sample.feature_tags),
                },
            )
        )
    return tuple(contributions)


def sample_total_raft_forces(
    state: RaftState6DoF,
    properties: RaftMassProperties,
    water: WaterField2_5D,
) -> tuple[RaftForceContribution2_5D, ...]:
    """Sample all current raft force channels against one water field."""

    return (
        *sample_buoyancy_forces(state, properties, water),
        *sample_hydrodynamic_forces(state, properties, water),
        *sample_grounding_forces(state, properties, water),
    )


def compare_raft_force_samples(
    reference_water: WaterField2_5D,
    candidate_water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    dt: float = 1.0 / 60.0,
) -> RaftSolverForceComparison2_5D:
    """Compare force envelope, one-step trajectory, and outcome between solvers."""

    reference_contributions = sample_total_raft_forces(state, properties, reference_water)
    candidate_contributions = sample_total_raft_forces(state, properties, candidate_water)
    reference_envelope = _force_envelope(reference_contributions)
    candidate_envelope = _force_envelope(candidate_contributions)
    reference_next = _advance_from_force_envelope(state, properties, reference_envelope, dt)
    candidate_next = _advance_from_force_envelope(state, properties, candidate_envelope, dt)
    return RaftSolverForceComparison2_5D(
        reference=reference_envelope,
        candidate=candidate_envelope,
        reference_next_state=reference_next,
        candidate_next_state=candidate_next,
        force_delta=candidate_envelope.total_force - reference_envelope.total_force,
        torque_delta=candidate_envelope.total_torque - reference_envelope.total_torque,
        trajectory_position_delta=(candidate_next.position - reference_next.position).magnitude,
        trajectory_velocity_delta=(candidate_next.linear_velocity - reference_next.linear_velocity).magnitude,
        outcome_match=reference_envelope.outcome == candidate_envelope.outcome,
    )


def _force_envelope(contributions: tuple[RaftForceContribution2_5D, ...]) -> RaftForceEnvelope2_5D:
    total_force, total_torque = sum_force_contributions(contributions)
    names = [contribution.name for contribution in contributions]
    if any(name.startswith("grounding") for name in names):
        outcome = "grounded"
    elif any(name.startswith("buoyancy") for name in names):
        outcome = "floating"
    elif contributions:
        outcome = "forced"
    else:
        outcome = "freefall"
    return RaftForceEnvelope2_5D(
        total_force=total_force,
        total_torque=total_torque,
        max_contribution_force=max((contribution.force.magnitude for contribution in contributions), default=0.0),
        max_contribution_torque=max((contribution.torque.magnitude for contribution in contributions), default=0.0),
        contribution_count=len(contributions),
        outcome=outcome,
    )


def _advance_from_force_envelope(
    state: RaftState6DoF,
    properties: RaftMassProperties,
    envelope: RaftForceEnvelope2_5D,
    dt: float,
) -> RaftState6DoF:
    linear_acceleration = envelope.total_force * properties.inverse_mass + properties.gravity
    inertia = properties.inertia_diagonal_kg_m2
    angular_acceleration = Vec3(
        envelope.total_torque.x / max(inertia.x, 1.0e-9),
        envelope.total_torque.y / max(inertia.y, 1.0e-9),
        envelope.total_torque.z / max(inertia.z, 1.0e-9),
    )
    return state.advance(dt, linear_acceleration=linear_acceleration, angular_acceleration=angular_acceleration)


def _has_grounding_feature(tags: tuple[str, ...]) -> bool:
    return bool({"rock", "ledge", "shallow", "strainer"} & set(tags))


def _grounding_feature_scale(tags: tuple[str, ...]) -> float:
    scale = 1.0
    if "rock" in tags or "strainer" in tags:
        scale = max(scale, 2.0)
    if "ledge" in tags:
        scale = max(scale, 1.5)
    if "shallow" in tags:
        scale = max(scale, 1.25)
    return scale
