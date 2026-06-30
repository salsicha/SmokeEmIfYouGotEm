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


@dataclass(frozen=True, slots=True)
class CrewSeat2_5D:
    """Crew seat anchor and current occupancy for deterministic weight telemetry."""

    seat_id: str
    local_position: Vec3
    occupant_mass_kg: float
    occupied: bool = True
    role: str = "passenger"

    def __post_init__(self) -> None:
        if not self.seat_id:
            raise ValueError("seat_id must be non-empty.")
        if self.occupant_mass_kg < 0.0:
            raise ValueError("occupant_mass_kg must be non-negative.")


@dataclass(frozen=True, slots=True)
class CrewAction2_5D:
    """Bounded crew action inputs that can shift weight during a physics tick."""

    seat_id: str
    lean_offset: Vec3 = Vec3()
    high_side_direction: int = 0
    brace: bool = False
    recovery: bool = False

    def __post_init__(self) -> None:
        if not self.seat_id:
            raise ValueError("seat_id must be non-empty.")
        if self.high_side_direction not in (-1, 0, 1):
            raise ValueError("high_side_direction must be -1, 0, or 1.")


@dataclass(frozen=True, slots=True)
class CrewSeatTelemetry2_5D:
    """Per-seat occupancy and effective mass position after bounded actions."""

    seat_id: str
    role: str
    occupied: bool
    mass_kg: float
    base_local_position: Vec3
    action_offset: Vec3
    effective_local_position: Vec3
    high_side_direction: int = 0
    brace: bool = False
    recovery: bool = False
    lean_was_clamped: bool = False


@dataclass(frozen=True, slots=True)
class CrewContactLoading2_5D:
    """First-pass normal-load proxy for side and longitudinal contact checks."""

    total_normal_load_n: float
    left_tube_normal_load_n: float
    right_tube_normal_load_n: float
    stern_normal_load_n: float
    bow_normal_load_n: float
    lateral_bias: float
    longitudinal_bias: float


@dataclass(frozen=True, slots=True)
class CrewRecoveryThresholds2_5D:
    """Pin, flip, and release thresholds adjusted by coordinated crew actions."""

    pin_threshold_n: float
    flip_threshold_nm: float
    release_threshold_n: float
    pin_threshold_multiplier: float
    flip_threshold_multiplier: float
    release_threshold_multiplier: float


@dataclass(frozen=True, slots=True)
class CrewWeightTelemetry2_5D:
    """Crew weight-distribution telemetry used by raft hazards and validation."""

    seat_telemetry: tuple[CrewSeatTelemetry2_5D, ...]
    occupied_seat_count: int
    active_action_count: int
    high_side_count: int
    brace_count: int
    recovery_count: int
    raft_base_mass_kg: float
    total_crew_mass_kg: float
    total_loaded_mass_kg: float
    crew_center_of_gravity_offset: Vec3
    combined_center_of_gravity_offset: Vec3
    roll_moment_nm: float
    pitch_moment_nm: float
    contact_loading: CrewContactLoading2_5D
    recovery_thresholds: CrewRecoveryThresholds2_5D


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


def build_default_crew_seats2_5d(parameters: RaftParameters2_5D | None = None) -> tuple[CrewSeat2_5D, ...]:
    """Build guide/passenger seats that match the default raft mass layout."""

    params = parameters or RaftParameters2_5D()
    seats = [
        CrewSeat2_5D(
            seat_id="guide",
            local_position=Vec3(-params.length_m * 0.42, 0.0, 0.15),
            occupant_mass_kg=params.guide_mass_kg,
            role="guide",
        )
    ]
    for index, offset in enumerate(_passenger_offsets(params)):
        seats.append(
            CrewSeat2_5D(
                seat_id=f"passenger_{index}",
                local_position=offset,
                occupant_mass_kg=params.passenger_mass_kg,
            )
        )
    return tuple(seats)


def evaluate_crew_weight_distribution2_5d(
    properties: RaftMassProperties,
    seats: tuple[CrewSeat2_5D, ...],
    actions: tuple[CrewAction2_5D, ...] = (),
    *,
    raft_length_m: float | None = None,
    raft_width_m: float | None = None,
    base_mass_kg: float | None = None,
    max_lean_offset_m: float = 0.55,
    high_side_offset_m: float = 0.45,
    brace_center_drop_m: float = 0.04,
    base_pin_threshold_n: float = 3200.0,
    base_flip_threshold_nm: float = 1800.0,
    base_release_threshold_n: float = 2600.0,
) -> CrewWeightTelemetry2_5D:
    """Evaluate crew center-of-gravity, contact-load, and recovery telemetry."""

    if max_lean_offset_m <= 0.0:
        raise ValueError("max_lean_offset_m must be positive.")
    if high_side_offset_m < 0.0:
        raise ValueError("high_side_offset_m must be non-negative.")
    if brace_center_drop_m < 0.0:
        raise ValueError("brace_center_drop_m must be non-negative.")
    if (
        base_pin_threshold_n <= 0.0
        or base_flip_threshold_nm <= 0.0
        or base_release_threshold_n <= 0.0
    ):
        raise ValueError("base thresholds must be positive.")

    actions_by_seat = {action.seat_id: action for action in actions}
    seat_ids = {seat.seat_id for seat in seats}
    unknown_actions = sorted(set(actions_by_seat) - seat_ids)
    if unknown_actions:
        raise ValueError(f"actions reference unknown seats: {', '.join(unknown_actions)}")

    all_crew_mass = sum(seat.occupant_mass_kg for seat in seats)
    raft_base_mass = (
        max(0.0, properties.total_mass_kg - all_crew_mass)
        if base_mass_kg is None
        else base_mass_kg
    )
    if raft_base_mass < 0.0:
        raise ValueError("base_mass_kg must be non-negative.")

    occupied_mass = 0.0
    weighted_crew_position = Vec3()
    seat_telemetry: list[CrewSeatTelemetry2_5D] = []
    active_action_count = 0
    high_side_count = 0
    brace_count = 0
    recovery_count = 0

    for seat in seats:
        action = actions_by_seat.get(seat.seat_id, CrewAction2_5D(seat.seat_id))
        lean_offset, lean_was_clamped = _clamped_offset(action.lean_offset, max_lean_offset_m)
        high_side_offset = Vec3(0.0, action.high_side_direction * high_side_offset_m, 0.0)
        brace_offset = Vec3(0.0, 0.0, -brace_center_drop_m if action.brace else 0.0)
        action_offset = lean_offset + high_side_offset + brace_offset
        effective_position = seat.local_position + action_offset
        action_is_active = (
            lean_offset.magnitude > 1.0e-9
            or action.high_side_direction != 0
            or action.brace
            or action.recovery
        )

        if seat.occupied:
            occupied_mass += seat.occupant_mass_kg
            weighted_crew_position += effective_position * seat.occupant_mass_kg
            if action_is_active:
                active_action_count += 1
            if action.high_side_direction != 0:
                high_side_count += 1
            if action.brace:
                brace_count += 1
            if action.recovery:
                recovery_count += 1

        seat_telemetry.append(
            CrewSeatTelemetry2_5D(
                seat_id=seat.seat_id,
                role=seat.role,
                occupied=seat.occupied,
                mass_kg=seat.occupant_mass_kg if seat.occupied else 0.0,
                base_local_position=seat.local_position,
                action_offset=action_offset if seat.occupied else Vec3(),
                effective_local_position=effective_position if seat.occupied else seat.local_position,
                high_side_direction=action.high_side_direction if seat.occupied else 0,
                brace=action.brace if seat.occupied else False,
                recovery=action.recovery if seat.occupied else False,
                lean_was_clamped=lean_was_clamped if seat.occupied else False,
            )
        )

    crew_cg = weighted_crew_position / occupied_mass if occupied_mass > 0.0 else Vec3()
    loaded_mass = raft_base_mass + occupied_mass
    combined_cg = weighted_crew_position / loaded_mass if loaded_mass > 0.0 else Vec3()
    gravity_magnitude = properties.gravity.magnitude if properties.gravity.magnitude > 1.0e-9 else 9.81
    roll_moment_nm = loaded_mass * gravity_magnitude * combined_cg.y
    pitch_moment_nm = loaded_mass * gravity_magnitude * combined_cg.x
    contact_loading = _crew_contact_loading(
        loaded_mass,
        gravity_magnitude,
        combined_cg,
        seats,
        properties.sample_patches,
        raft_length_m=raft_length_m,
        raft_width_m=raft_width_m,
    )
    recovery_thresholds = _crew_recovery_thresholds(
        occupied_count=sum(1 for seat in seats if seat.occupied),
        high_side_count=high_side_count,
        brace_count=brace_count,
        recovery_count=recovery_count,
        contact_loading=contact_loading,
        base_pin_threshold_n=base_pin_threshold_n,
        base_flip_threshold_nm=base_flip_threshold_nm,
        base_release_threshold_n=base_release_threshold_n,
    )

    return CrewWeightTelemetry2_5D(
        seat_telemetry=tuple(seat_telemetry),
        occupied_seat_count=sum(1 for seat in seats if seat.occupied),
        active_action_count=active_action_count,
        high_side_count=high_side_count,
        brace_count=brace_count,
        recovery_count=recovery_count,
        raft_base_mass_kg=raft_base_mass,
        total_crew_mass_kg=occupied_mass,
        total_loaded_mass_kg=loaded_mass,
        crew_center_of_gravity_offset=crew_cg,
        combined_center_of_gravity_offset=combined_cg,
        roll_moment_nm=roll_moment_nm,
        pitch_moment_nm=pitch_moment_nm,
        contact_loading=contact_loading,
        recovery_thresholds=recovery_thresholds,
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


def _clamped_offset(offset: Vec3, max_magnitude: float) -> tuple[Vec3, bool]:
    if offset.magnitude <= max_magnitude:
        return offset, False
    return offset.normalized() * max_magnitude, True


def _crew_contact_loading(
    loaded_mass_kg: float,
    gravity_magnitude: float,
    combined_cg: Vec3,
    seats: tuple[CrewSeat2_5D, ...],
    sample_patches: tuple[RaftSamplePatch, ...],
    *,
    raft_length_m: float | None,
    raft_width_m: float | None,
) -> CrewContactLoading2_5D:
    half_width = (
        raft_width_m * 0.5
        if raft_width_m is not None
        else _max_abs_position(seats, sample_patches, "y")
    )
    half_length = (
        raft_length_m * 0.5
        if raft_length_m is not None
        else _max_abs_position(seats, sample_patches, "x")
    )
    half_width = max(half_width, 1.0e-6)
    half_length = max(half_length, 1.0e-6)
    lateral_bias = _clamp(combined_cg.y / half_width, -0.95, 0.95)
    longitudinal_bias = _clamp(combined_cg.x / half_length, -0.95, 0.95)
    total_load = loaded_mass_kg * gravity_magnitude
    right_fraction = 0.5 + 0.5 * lateral_bias
    bow_fraction = 0.5 + 0.5 * longitudinal_bias
    return CrewContactLoading2_5D(
        total_normal_load_n=total_load,
        left_tube_normal_load_n=total_load * (1.0 - right_fraction),
        right_tube_normal_load_n=total_load * right_fraction,
        stern_normal_load_n=total_load * (1.0 - bow_fraction),
        bow_normal_load_n=total_load * bow_fraction,
        lateral_bias=lateral_bias,
        longitudinal_bias=longitudinal_bias,
    )


def _crew_recovery_thresholds(
    *,
    occupied_count: int,
    high_side_count: int,
    brace_count: int,
    recovery_count: int,
    contact_loading: CrewContactLoading2_5D,
    base_pin_threshold_n: float,
    base_flip_threshold_nm: float,
    base_release_threshold_n: float,
) -> CrewRecoveryThresholds2_5D:
    denominator = max(occupied_count, 1)
    high_side_ratio = high_side_count / denominator
    brace_ratio = brace_count / denominator
    recovery_ratio = recovery_count / denominator
    lateral_authority = abs(contact_loading.lateral_bias)
    pin_multiplier = (
        1.0
        + 0.10 * brace_ratio
        + 0.10 * high_side_ratio
        + min(0.20, lateral_authority * 0.20)
    )
    flip_multiplier = (
        1.0
        + 0.20 * high_side_ratio
        + 0.04 * brace_ratio
        + min(0.35, lateral_authority * 0.35)
    )
    release_multiplier = max(
        0.65,
        1.0
        - 0.12 * high_side_ratio
        - 0.10 * brace_ratio
        - 0.08 * recovery_ratio
        - min(0.18, lateral_authority * 0.18),
    )
    return CrewRecoveryThresholds2_5D(
        pin_threshold_n=base_pin_threshold_n * pin_multiplier,
        flip_threshold_nm=base_flip_threshold_nm * flip_multiplier,
        release_threshold_n=base_release_threshold_n * release_multiplier,
        pin_threshold_multiplier=pin_multiplier,
        flip_threshold_multiplier=flip_multiplier,
        release_threshold_multiplier=release_multiplier,
    )


def _max_abs_position(
    seats: tuple[CrewSeat2_5D, ...],
    sample_patches: tuple[RaftSamplePatch, ...],
    axis: str,
) -> float:
    values = [abs(getattr(seat.local_position, axis)) for seat in seats]
    values.extend(abs(getattr(patch.local_position, axis)) for patch in sample_patches)
    return max(values, default=1.0)


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


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
