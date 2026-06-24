"""Top-down raft simulation over procedural 2D rivers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from .backends.base import BackendUnavailableError
from .backends.chrono import ProjectChronoBackend
from .math2d import Vec2, clamp
from .math3d import Vec3
from .river2d import GeneratedRiver2D, RiverFeature2D, RiverSample2D
from .sim import SimulationConfig
from .telemetry import TelemetryFrame, TelemetryRecorder

Raft2DBackendName = Literal["python", "chrono", "auto"]


@dataclass(frozen=True, slots=True)
class Raft2DConfig:
    mass: float = 420.0
    inertia: float = 1550.0
    length: float = 4.6
    width: float = 2.1
    drag_coefficient: float = 95.0
    linear_damping: float = 12.0
    angular_damping: float = 120.0
    contact_stiffness: float = 5500.0
    contact_damping: float = 550.0
    bank_stiffness: float = 2400.0
    paddle_force: float = 520.0

    def __post_init__(self) -> None:
        if self.mass <= 0.0:
            raise ValueError("mass must be positive.")
        if self.inertia <= 0.0:
            raise ValueError("inertia must be positive.")


@dataclass(slots=True)
class Raft2DState:
    position: Vec2
    yaw: float = 0.0
    velocity: Vec2 = field(default_factory=Vec2)
    angular_velocity: float = 0.0

    def copy(self) -> Raft2DState:
        return Raft2DState(
            position=self.position,
            yaw=self.yaw,
            velocity=self.velocity,
            angular_velocity=self.angular_velocity,
        )


@dataclass(frozen=True, slots=True)
class PaddleCommand2D:
    local_point: Vec2
    direction: Vec2
    strength: float = 1.0
    name: str = "paddle"


@dataclass(frozen=True, slots=True)
class Raft2DStepResult:
    frame: TelemetryFrame
    state: Raft2DState
    outcome: str


@dataclass(frozen=True, slots=True)
class _PlanarForce:
    name: str
    force: Vec2
    point: Vec2
    direct_torque: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


class _PurePythonPlanarIntegrator:
    name = "python"

    def step(self, state: Raft2DState, net_force: Vec2, net_torque: float, config: Raft2DConfig, dt: float) -> Raft2DState:
        acceleration = net_force / config.mass
        angular_acceleration = net_torque / config.inertia
        velocity = state.velocity + acceleration * dt
        angular_velocity = state.angular_velocity + angular_acceleration * dt
        position = state.position + velocity * dt
        yaw = _wrap_angle(state.yaw + angular_velocity * dt)
        return Raft2DState(position=position, yaw=yaw, velocity=velocity, angular_velocity=angular_velocity)


class _ChronoPlanarIntegrator:
    """Planar force integrator backed by a PyChrono ChSystem.

    The 2D river plane maps to Chrono's X/Z plane. Y is treated as the vertical
    axis, so yaw torque maps to Chrono Y torque.
    """

    name = "chrono"

    def __init__(self, config: Raft2DConfig, sim_config: SimulationConfig):
        backend = ProjectChronoBackend()
        self._chrono_sim = backend.create_simulation(config=sim_config)
        self._chrono = self._chrono_sim.chrono_module
        self._body = self._make_body(config)
        self._add_body_to_system()

    def step(self, state: Raft2DState, net_force: Vec2, net_torque: float, config: Raft2DConfig, dt: float) -> Raft2DState:
        self._sync_body_from_state(state)
        self._clear_forces()
        self._accumulate_force(net_force)
        self._accumulate_torque(net_torque)
        self._chrono_sim.step(1)
        return self._read_body_state(fallback=state, dt=dt)

    def _make_body(self, config: Raft2DConfig):
        chrono = self._chrono
        body = None
        if hasattr(chrono, "ChBodyEasyBox"):
            try:
                body = chrono.ChBodyEasyBox(
                    config.length,
                    0.25,
                    config.width,
                    config.mass / (config.length * config.width * 0.25),
                    True,
                    False,
                )
            except TypeError:
                body = None
        if body is None and hasattr(chrono, "ChBody"):
            body = chrono.ChBody()
        if body is None:
            raise BackendUnavailableError("PyChrono is missing ChBody/ChBodyEasyBox.")

        _call_if_present(body, ("SetMass",), config.mass)
        inertia_vector = _chrono_vector(chrono, 0.0, config.inertia, 0.0)
        _call_if_present(body, ("SetInertiaXX",), inertia_vector)
        _call_if_present(body, ("EnableCollision",), True)
        _call_if_present(body, ("SetFixed",), False)
        return body

    def _add_body_to_system(self) -> None:
        system = self._chrono_sim.system
        if _call_if_present(system, ("AddBody", "Add"), self._body):
            return
        raise BackendUnavailableError("PyChrono ChSystem does not expose Add/AddBody.")

    def _sync_body_from_state(self, state: Raft2DState) -> None:
        chrono = self._chrono
        position = _chrono_vector(chrono, state.position.x, 0.0, state.position.y)
        rotation = _chrono_quaternion_yaw(chrono, state.yaw)
        linear_velocity = _chrono_vector(chrono, state.velocity.x, 0.0, state.velocity.y)
        angular_velocity = _chrono_vector(chrono, 0.0, state.angular_velocity, 0.0)
        _call_if_present(self._body, ("SetPos",), position)
        _call_if_present(self._body, ("SetRot",), rotation)
        _call_if_present(self._body, ("SetLinVel", "SetPosDt"), linear_velocity)
        _call_if_present(self._body, ("SetAngVelParent", "SetAngVelLocal", "SetWvel_par"), angular_velocity)

    def _clear_forces(self) -> None:
        _call_if_present(self._body, ("EmptyAccumulators", "Empty_forces_accumulators"))

    def _accumulate_force(self, force: Vec2) -> None:
        chrono = self._chrono
        force_vector = _chrono_vector(chrono, force.x, 0.0, force.y)
        point = _chrono_vector(chrono, 0.0, 0.0, 0.0)
        if _call_if_present(self._body, ("AccumulateForce", "Accumulate_force"), force_vector, point, False):
            return
        if _call_if_present(self._body, ("AddForce",), force_vector):
            return
        raise BackendUnavailableError("PyChrono body does not expose a supported force accumulator.")

    def _accumulate_torque(self, torque: float) -> None:
        chrono = self._chrono
        torque_vector = _chrono_vector(chrono, 0.0, torque, 0.0)
        _call_if_present(self._body, ("AccumulateTorque", "Accumulate_torque"), torque_vector, False)

    def _read_body_state(self, fallback: Raft2DState, dt: float) -> Raft2DState:
        position = _call_first(self._body, ("GetPos",))
        velocity = _call_first(self._body, ("GetLinVel", "GetPosDt"))
        angular_velocity = _call_first(self._body, ("GetAngVelParent", "GetAngVelLocal", "GetWvel_par"))

        if position is None:
            return fallback.copy()

        pos2 = Vec2(_component(position, "x", 0), _component(position, "z", 2))
        vel2 = fallback.velocity if velocity is None else Vec2(_component(velocity, "x", 0), _component(velocity, "z", 2))
        omega = fallback.angular_velocity if angular_velocity is None else _component(angular_velocity, "y", 1)
        return Raft2DState(position=pos2, yaw=fallback.yaw + omega * dt, velocity=vel2, angular_velocity=omega)


class Raft2DSimulation:
    """Top-down raft simulation over a generated river."""

    def __init__(
        self,
        river: GeneratedRiver2D,
        *,
        state: Raft2DState | None = None,
        raft_config: Raft2DConfig | None = None,
        sim_config: SimulationConfig | None = None,
        backend: Raft2DBackendName = "auto",
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self.river = river
        self.raft_config = raft_config or Raft2DConfig()
        self.sim_config = sim_config or SimulationConfig(fixed_dt=1.0 / 60.0)
        self.state = state or Raft2DState(position=river.start_position, yaw=0.0)
        self.telemetry = telemetry or TelemetryRecorder()
        self.time = 0.0
        self.step_index = 0
        self.outcome = "running"
        self.integrator = self._create_integrator(backend)

    @property
    def backend_name(self) -> str:
        return self.integrator.name

    def step(self, paddle_commands: tuple[PaddleCommand2D, ...] = ()) -> Raft2DStepResult:
        dt = self.sim_config.fixed_dt
        frame = self.telemetry.begin_frame(step_index=self.step_index, time=self.time, dt=dt)
        forces = self._compute_forces(paddle_commands)
        net_force = Vec2()
        net_torque = 0.0
        for contribution in forces:
            lever = contribution.point - self.state.position
            torque = lever.cross(contribution.force) + contribution.direct_torque
            net_force += contribution.force
            net_torque += torque
            frame.record_force(
                contribution.name,
                Vec3(contribution.force.x, contribution.force.y, 0.0),
                torque=Vec3(0.0, 0.0, torque),
                application_point=Vec3(contribution.point.x, contribution.point.y, 0.0),
                metadata=contribution.metadata,
            )

        self.state = self.integrator.step(self.state, net_force, net_torque, self.raft_config, dt)
        self.state.yaw = _wrap_angle(self.state.yaw)
        self.time += dt
        self.step_index += 1
        self.outcome = self._classify_outcome()
        ended = self.telemetry.end_frame()
        return Raft2DStepResult(frame=ended, state=self.state.copy(), outcome=self.outcome)

    def run(self, duration: float, paddle_commands: tuple[PaddleCommand2D, ...] = ()) -> tuple[Raft2DStepResult, ...]:
        count = int(round(duration / self.sim_config.fixed_dt))
        results = []
        for _ in range(count):
            results.append(self.step(paddle_commands))
            if self.outcome in {"finished", "pinned", "hazard"}:
                break
        return tuple(results)

    def hull_points_world(self) -> tuple[Vec2, ...]:
        half_length = self.raft_config.length * 0.5
        half_width = self.raft_config.width * 0.5
        local_points = (
            Vec2(half_length, 0.0),
            Vec2(-half_length, 0.0),
            Vec2(0.0, half_width),
            Vec2(0.0, -half_width),
            Vec2(half_length * 0.65, half_width * 0.8),
            Vec2(half_length * 0.65, -half_width * 0.8),
            Vec2(-half_length * 0.65, half_width * 0.8),
            Vec2(-half_length * 0.65, -half_width * 0.8),
        )
        return tuple(self.local_to_world(point) for point in local_points)

    def local_to_world(self, point: Vec2) -> Vec2:
        return self.state.position + point.rotated(self.state.yaw)

    def _create_integrator(self, backend: Raft2DBackendName):
        if backend == "python":
            return _PurePythonPlanarIntegrator()
        if backend == "chrono":
            return _ChronoPlanarIntegrator(self.raft_config, self.sim_config)
        try:
            return _ChronoPlanarIntegrator(self.raft_config, self.sim_config)
        except BackendUnavailableError:
            return _PurePythonPlanarIntegrator()

    def _compute_forces(self, paddle_commands: tuple[PaddleCommand2D, ...]) -> list[_PlanarForce]:
        forces: list[_PlanarForce] = []
        hull_points = self.hull_points_world()
        per_point_drag = self.raft_config.drag_coefficient / len(hull_points)
        for point in hull_points:
            sample = self.river.sample(point)
            lever = point - self.state.position
            point_velocity = self.state.velocity + Vec2(-self.state.angular_velocity * lever.y, self.state.angular_velocity * lever.x)
            relative_velocity = sample.current - point_velocity
            drag_force = relative_velocity * (per_point_drag * sample.damping)
            damping_force = -point_velocity * (self.raft_config.linear_damping / len(hull_points))
            if drag_force.magnitude > 0.0:
                forces.append(
                    _PlanarForce(
                        "water.drag",
                        drag_force,
                        point,
                        metadata={"current_x": sample.current.x, "current_y": sample.current.y, "tags": ",".join(sample.tags)},
                    )
                )
            if damping_force.magnitude > 0.0:
                forces.append(_PlanarForce("raft.linear_damping", damping_force, point, metadata={"damping": sample.damping}))
            if sample.shear > 0.0:
                lateral = sample.normal * (-1.0 if sample.n > 0.0 else 1.0)
                forces.append(_PlanarForce("water.shear", lateral * sample.shear * 20.0, point, metadata={"shear": sample.shear}))
            if not sample.inside_water:
                bank_normal = sample.normal * (-1.0 if sample.n > 0.0 else 1.0)
                forces.append(
                    _PlanarForce(
                        "contact.bank",
                        bank_normal * (self.raft_config.bank_stiffness * sample.bank_distance),
                        point,
                        metadata={"penetration": sample.bank_distance},
                    )
                )
            forces.extend(self._feature_forces(point, point_velocity, sample))

        angular_damping = -self.state.angular_velocity * self.raft_config.angular_damping
        if abs(angular_damping) > 0.0:
            forces.append(
                _PlanarForce(
                    "raft.angular_damping",
                    Vec2(0.0, 0.0),
                    self.state.position,
                    direct_torque=angular_damping,
                    metadata={"direct_yaw_torque": angular_damping},
                )
            )

        for command in paddle_commands:
            point = self.local_to_world(command.local_point)
            direction = command.direction.rotated(self.state.yaw).safe_normalized()
            forces.append(
                _PlanarForce(
                    f"paddle.{command.name}",
                    direction * (self.raft_config.paddle_force * command.strength),
                    point,
                    metadata={"strength": command.strength},
                )
            )
        return forces

    def _feature_forces(self, point: Vec2, point_velocity: Vec2, sample: RiverSample2D) -> list[_PlanarForce]:
        forces: list[_PlanarForce] = []
        for feature in self.river.features:
            delta = point - feature.position
            distance = delta.magnitude
            direction = delta.safe_normalized(sample.normal)
            if feature.kind == "rock":
                penetration = feature.radius + 0.35 - distance
                if penetration > 0.0:
                    normal_velocity = point_velocity.dot(direction)
                    normal_force = direction * (
                        self.raft_config.contact_stiffness * penetration
                        - self.raft_config.contact_damping * min(0.0, normal_velocity)
                    )
                    friction = -point_velocity * 0.18 * self.raft_config.contact_damping
                    forces.append(
                        _PlanarForce(
                            "contact.rock",
                            normal_force + friction,
                            point,
                            metadata={"penetration": penetration, "rock_x": feature.position.x, "rock_y": feature.position.y},
                        )
                    )
                elif distance < feature.radius * 3.0 and (feature.position - point).dot(sample.tangent) > 0.0:
                    falloff = 1.0 - clamp((distance - feature.radius) / max(feature.radius * 2.0, 1.0e-6), 0.0, 1.0)
                    forces.append(
                        _PlanarForce(
                            "water.rock_pillow",
                            -direction * (180.0 * feature.strength * falloff),
                            point,
                            metadata={"falloff": falloff},
                        )
                    )
            elif distance <= max(feature.radius, feature.width * 0.5):
                falloff = 1.0 - clamp(distance / max(feature.radius, feature.width * 0.5, 1.0e-6), 0.0, 1.0)
                if feature.kind == "standing_wave":
                    forces.append(
                        _PlanarForce(
                            "feature.standing_wave",
                            -sample.tangent * (260.0 * feature.strength * falloff),
                            point,
                            metadata={"surf_score": falloff},
                        )
                    )
                elif feature.kind == "hole":
                    retention = -sample.tangent * (360.0 * feature.strength * falloff) - direction * (120.0 * falloff)
                    forces.append(_PlanarForce("feature.hole_retention", retention, point, metadata={"retention": falloff}))
                elif feature.kind == "lateral_wave":
                    lateral = Vec2(math.cos(feature.angle), math.sin(feature.angle)).safe_normalized(sample.normal)
                    forces.append(
                        _PlanarForce(
                            "feature.lateral_wave",
                            lateral * (320.0 * feature.strength * falloff),
                            point,
                            metadata={"hit": falloff},
                        )
                    )
                elif feature.kind == "boil":
                    forces.append(
                        _PlanarForce(
                            "feature.boil",
                            (direction + direction.perpendicular_left() * 0.45) * (130.0 * feature.strength * falloff),
                            point,
                            metadata={"disturbance": falloff},
                        )
                    )
                elif feature.kind == "shallow":
                    forces.append(
                        _PlanarForce(
                            "feature.shallow_grounding",
                            -point_velocity * (85.0 * feature.strength * falloff),
                            point,
                            metadata={"grounding": falloff},
                        )
                    )
                elif feature.kind == "strainer":
                    forces.append(
                        _PlanarForce(
                            "hazard.strainer",
                            -point_velocity * (200.0 * feature.strength * falloff),
                            point,
                            metadata={"entrapment": falloff},
                        )
                    )
        return forces

    def _classify_outcome(self) -> str:
        if self.state.position.x >= self.river.length - 3.0:
            return "finished"
        sample = self.river.sample(self.state.position)
        if "strainer" in sample.tags:
            return "hazard"
        if self.state.velocity.magnitude < 0.03 and self.time > 4.0:
            near_rock = any(self.state.position.distance_to(feature.position) < feature.radius + 1.0 for feature in self.river.rocks())
            if near_rock:
                return "pinned"
        if "hole" in sample.tags and self.state.velocity.magnitude < 0.45:
            return "surfing"
        return "running"


def default_forward_paddle_commands() -> tuple[PaddleCommand2D, ...]:
    return (
        PaddleCommand2D(local_point=Vec2(0.8, 0.85), direction=Vec2(1.0, 0.0), strength=0.35, name="front_left"),
        PaddleCommand2D(local_point=Vec2(0.8, -0.85), direction=Vec2(1.0, 0.0), strength=0.35, name="front_right"),
        PaddleCommand2D(local_point=Vec2(-1.4, 0.75), direction=Vec2(1.0, 0.0), strength=0.25, name="guide_left"),
        PaddleCommand2D(local_point=Vec2(-1.4, -0.75), direction=Vec2(1.0, 0.0), strength=0.25, name="guide_right"),
    )


def _wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (math.tau) - math.pi


def _call_if_present(target, names: tuple[str, ...], *args) -> bool:
    for name in names:
        method = getattr(target, name, None)
        if method is None:
            continue
        try:
            method(*args)
        except TypeError:
            continue
        return True
    return False


def _call_first(target, names: tuple[str, ...]):
    for name in names:
        method = getattr(target, name, None)
        if method is None:
            continue
        try:
            return method()
        except TypeError:
            continue
    return None


def _chrono_vector(chrono, x: float, y: float, z: float):
    if hasattr(chrono, "ChVector3d"):
        return chrono.ChVector3d(x, y, z)
    if hasattr(chrono, "ChVectorD"):
        return chrono.ChVectorD(x, y, z)
    return (x, y, z)


def _chrono_quaternion_yaw(chrono, yaw: float):
    half = yaw * 0.5
    if hasattr(chrono, "ChQuaterniond"):
        return chrono.ChQuaterniond(math.cos(half), 0.0, math.sin(half), 0.0)
    if hasattr(chrono, "ChQuaternionD"):
        return chrono.ChQuaternionD(math.cos(half), 0.0, math.sin(half), 0.0)
    return (math.cos(half), 0.0, math.sin(half), 0.0)


def _component(vector, attr: str, index: int) -> float:
    value = getattr(vector, attr, None)
    if value is not None:
        return float(value() if callable(value) else value)
    if isinstance(vector, (tuple, list)):
        return float(vector[index])
    return 0.0
