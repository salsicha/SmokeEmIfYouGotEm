"""D4 rock contact, wrap, pin, and release reference coupling."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .flexible_raft_d1 import D1_SCORING_AUTHORITY, TubeSegmentD1, build_default_compliant_tube_layout_d1
from .flexible_raft_d2 import SeatLoadCoupledTubeSolveD2, solve_seat_load_coupled_tube_d2
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    RaftState6DoF,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
)
from .scenario2_5d import RaftParameters2_5D


D4_ROCK_CONTACT_FIXTURE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d4_rock_contact_fixture.json"
)
D4_ROCK_CONTACT_SCHEMA = "raftsim.flexible_raft.d4_rock_contact_wrap_pin_reference.v1"


@dataclass(frozen=True, slots=True)
class RockObstacleD4:
    """Local obstacle used by the D4 reference contact model."""

    obstacle_id: str
    local_position: Vec3
    radius_m: float
    friction_coefficient: float = 0.72

    def __post_init__(self) -> None:
        if not self.obstacle_id:
            raise ValueError("obstacle_id must be non-empty.")
        if self.radius_m <= 0.0:
            raise ValueError("radius_m must be positive.")
        if self.friction_coefficient < 0.0:
            raise ValueError("friction_coefficient must be non-negative.")


@dataclass(frozen=True, slots=True)
class RockContactD4:
    """Per-segment D4 rock contact, wrap, release, and recovery telemetry."""

    obstacle_id: str
    segment_id: str
    local_position: Vec3
    obstacle_local_position: Vec3
    clearance_m: float
    penetration_m: float
    recovered_previous_indentation_m: float
    indentation_m: float
    pressure_pa: float
    pressure_release_support_n: float
    normal_force_n: float
    damping_force_n: float
    friction_force_n: float
    wrap_support_n: float
    holding_force_n: float
    release_resistance_n: float
    release_authority_n: float
    release_margin_n: float
    wrapping: bool
    pinned: bool
    recovering: bool


@dataclass(frozen=True, slots=True)
class RockContactSolveD4:
    """Reference-only D4 contact solve layered on D2 tube state."""

    schema: str
    scoring_authority: str
    contacts: tuple[RockContactD4, ...]
    total_holding_force_n: float
    max_indentation_m: float
    min_release_margin_n: float
    pinned_obstacle_count: int
    wrapping_contact_count: int
    recovering_contact_count: int
    water_field_modified: bool = False

    @property
    def scoring_authority_enabled(self) -> bool:
        return False


def evaluate_rock_contact_wrap_pin_d4(
    seat_tube_solve: SeatLoadCoupledTubeSolveD2,
    obstacles: tuple[RockObstacleD4, ...],
    *,
    parameters: RaftParameters2_5D | None = None,
    layout: tuple[TubeSegmentD1, ...] | None = None,
    previous_indentation_by_segment: dict[str, float] | None = None,
    dt: float = 1.0 / 30.0,
    tube_radius_m: float | None = None,
    max_indentation_m: float = 0.22,
    tube_contact_stiffness_n_m: float = 30_000.0,
    contact_damping_n_s_m: float = 850.0,
    pressure_release_area_m2: float = 0.018,
    recovery_rate_per_s: float = 2.4,
    wrap_support_scale: float = 0.32,
) -> RockContactSolveD4:
    """Evaluate bounded rock indentation, wrap holding force, and recovery."""

    if dt <= 0.0:
        raise ValueError("dt must be positive.")
    if max_indentation_m <= 0.0:
        raise ValueError("max_indentation_m must be positive.")
    if tube_contact_stiffness_n_m <= 0.0 or contact_damping_n_s_m < 0.0:
        raise ValueError("contact stiffness must be positive and damping non-negative.")
    if pressure_release_area_m2 < 0.0:
        raise ValueError("pressure_release_area_m2 must be non-negative.")
    if recovery_rate_per_s < 0.0:
        raise ValueError("recovery_rate_per_s must be non-negative.")
    if wrap_support_scale < 0.0:
        raise ValueError("wrap_support_scale must be non-negative.")

    params = parameters or RaftParameters2_5D()
    tube_radius = params.tube_radius_m if tube_radius_m is None else tube_radius_m
    if tube_radius <= 0.0:
        raise ValueError("tube_radius_m must be positive.")
    tube_layout = layout or build_default_compliant_tube_layout_d1(params)
    responses_by_id = {
        response.segment_id: response
        for response in seat_tube_solve.tube_solve.tube_solve.segment_responses
    }
    previous_indent = previous_indentation_by_segment or {}
    rigid_state = seat_tube_solve.tube_solve.rigid_state
    contact_candidates: list[tuple[RockObstacleD4, TubeSegmentD1, float, float]] = []
    touched_segment_ids: set[str] = set()

    for obstacle in obstacles:
        for segment in tube_layout:
            distance = _xy_distance(segment.local_position, obstacle.local_position)
            clearance = distance - (tube_radius + obstacle.radius_m)
            penetration = max(0.0, -clearance)
            if penetration <= 0.0:
                continue
            contact_candidates.append((obstacle, segment, clearance, penetration))
            touched_segment_ids.add(segment.segment_id)

    obstacle_contact_counts: dict[str, int] = {}
    for obstacle, _, _, _ in contact_candidates:
        obstacle_contact_counts[obstacle.obstacle_id] = obstacle_contact_counts.get(obstacle.obstacle_id, 0) + 1

    contacts = [
        _contact_payload(
            seat_tube_solve,
            obstacle,
            segment,
            responses_by_id[segment.segment_id],
            clearance,
            penetration,
            previous_indent.get(segment.segment_id, 0.0),
            dt=dt,
            rigid_state=rigid_state,
            max_indentation_m=max_indentation_m,
            tube_contact_stiffness_n_m=tube_contact_stiffness_n_m,
            contact_damping_n_s_m=contact_damping_n_s_m,
            pressure_release_area_m2=pressure_release_area_m2,
            recovery_rate_per_s=recovery_rate_per_s,
            wrap_support_scale=wrap_support_scale,
            obstacle_contact_count=obstacle_contact_counts[obstacle.obstacle_id],
            recovering=False,
        )
        for obstacle, segment, clearance, penetration in contact_candidates
    ]

    for segment in tube_layout:
        if segment.segment_id in touched_segment_ids:
            continue
        previous = previous_indent.get(segment.segment_id, 0.0)
        if previous <= 0.0:
            continue
        recovery_obstacle = RockObstacleD4(
            obstacle_id="shape_recovery",
            local_position=segment.local_position,
            radius_m=0.01,
            friction_coefficient=0.0,
        )
        contacts.append(
            _contact_payload(
                seat_tube_solve,
                recovery_obstacle,
                segment,
                responses_by_id[segment.segment_id],
                clearance_m=0.0,
                penetration_m=0.0,
                previous_indentation_m=previous,
                dt=dt,
                rigid_state=rigid_state,
                max_indentation_m=max_indentation_m,
                tube_contact_stiffness_n_m=tube_contact_stiffness_n_m,
                contact_damping_n_s_m=0.0,
                pressure_release_area_m2=pressure_release_area_m2,
                recovery_rate_per_s=recovery_rate_per_s,
                wrap_support_scale=0.0,
                obstacle_contact_count=1,
                recovering=True,
            )
        )

    pinned_obstacles = {
        contact.obstacle_id
        for contact in contacts
        if contact.pinned and not contact.recovering
    }
    return RockContactSolveD4(
        schema=D4_ROCK_CONTACT_SCHEMA,
        scoring_authority=D1_SCORING_AUTHORITY,
        contacts=tuple(contacts),
        total_holding_force_n=sum(contact.holding_force_n for contact in contacts),
        max_indentation_m=max((contact.indentation_m for contact in contacts), default=0.0),
        min_release_margin_n=min((contact.release_margin_n for contact in contacts), default=0.0),
        pinned_obstacle_count=len(pinned_obstacles),
        wrapping_contact_count=sum(1 for contact in contacts if contact.wrapping),
        recovering_contact_count=sum(1 for contact in contacts if contact.recovering),
        water_field_modified=False,
    )


def build_rock_contact_wrap_pin_d4_fixture(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the committed D4 rock contact/wrap/pin reference fixture."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF(position=Vec3(3.0, 2.0, 0.0), linear_velocity=Vec3(0.0, 0.7, 0.0))
    neutral = solve_seat_load_coupled_tube_d2(state, properties, seats, parameters=params)
    high_side = solve_seat_load_coupled_tube_d2(
        state,
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )
    single_rock = (RockObstacleD4("single_starboard_boulder", Vec3(0.54, 1.22, 0.0), 0.18),)
    wrap_rock = (RockObstacleD4("wrap_starboard_pillow", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),)
    recovery = evaluate_rock_contact_wrap_pin_d4(
        neutral,
        (),
        parameters=params,
        previous_indentation_by_segment={"starboard_2": 0.12, "starboard_1": 0.08},
    )
    cases = [
        _case_payload(
            "clear_no_contact",
            evaluate_rock_contact_wrap_pin_d4(
                neutral,
                (RockObstacleD4("far_clear_boulder", Vec3(0.0, 4.5, 0.0), 0.25),),
                parameters=params,
            ),
            "Distant rock should produce no contact or water-field mutation.",
        ),
        _case_payload(
            "single_starboard_indentation",
            evaluate_rock_contact_wrap_pin_d4(neutral, single_rock, parameters=params),
            "Single boulder should indent a bounded local tube segment with friction.",
        ),
        _case_payload(
            "starboard_wrap_pin",
            evaluate_rock_contact_wrap_pin_d4(neutral, wrap_rock, parameters=params),
            "Wide boulder contact should wrap multiple tube segments and create pin risk.",
        ),
        _case_payload(
            "high_side_changes_release_margin",
            evaluate_rock_contact_wrap_pin_d4(high_side, wrap_rock, parameters=params),
            "High-side load changes tube pressure and the pressure-dependent release margin.",
        ),
        _case_payload(
            "post_contact_shape_recovery",
            recovery,
            "Previously indented segments recover deterministically after contact clears.",
        ),
    ]
    return {
        "schema": D4_ROCK_CONTACT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "rock_contact_wrap_pin_reference_fixture_recorded_not_gameplay_authority",
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "model_contract": {
            "uses_deformed_d2_tube_state": True,
            "bounded_indentation_recorded": True,
            "friction_wrap_pin_release_recorded": True,
            "pressure_dependent_release_recorded": True,
            "stable_post_contact_shape_recovery_recorded": True,
            "accepted_water_fields_modified": False,
            "gameplay_scoring_authority": "disabled_until_d6_fixture_suite_and_design_review",
        },
        "cases": cases,
        "promotion_gate": {
            "may_drive_runtime_gameplay": False,
            "may_inform_engine_port": True,
            "requires_before_runtime_authority": [
                "D5 replay telemetry",
                "D6 Chrono-or-reviewed compliant reference comparison",
                "contact-stability sweeps",
                "named-rapid pin/release consequence-line review",
            ],
        },
    }


def write_rock_contact_wrap_pin_d4_fixture(repo_root: Path) -> Path:
    """Write the committed D4 rock contact/wrap/pin reference fixture JSON."""

    payload = build_rock_contact_wrap_pin_d4_fixture()
    path = repo_root / D4_ROCK_CONTACT_FIXTURE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _contact_payload(
    seat_tube_solve: SeatLoadCoupledTubeSolveD2,
    obstacle: RockObstacleD4,
    segment: TubeSegmentD1,
    response: Any,
    clearance_m: float,
    penetration_m: float,
    previous_indentation_m: float,
    *,
    dt: float,
    rigid_state: RaftState6DoF,
    max_indentation_m: float,
    tube_contact_stiffness_n_m: float,
    contact_damping_n_s_m: float,
    pressure_release_area_m2: float,
    recovery_rate_per_s: float,
    wrap_support_scale: float,
    obstacle_contact_count: int,
    recovering: bool,
) -> RockContactD4:
    recovery_factor = max(0.0, 1.0 - recovery_rate_per_s * dt)
    recovered_previous = min(max_indentation_m, max(0.0, previous_indentation_m) * recovery_factor)
    indentation = min(max_indentation_m, max(penetration_m, recovered_previous))
    normal = _xy_normal(segment.local_position - obstacle.local_position)
    world_normal = rigid_state.orientation.rotate_vector(normal)
    approach_speed = max(0.0, -rigid_state.point_velocity(segment.local_position).dot(world_normal))
    damping_force = contact_damping_n_s_m * approach_speed if not recovering else 0.0
    normal_force = indentation * tube_contact_stiffness_n_m + damping_force
    friction_force = normal_force * obstacle.friction_coefficient
    wrapping = obstacle_contact_count >= 3 and not recovering
    wrap_support = normal_force * wrap_support_scale * max(0, obstacle_contact_count - 1) if wrapping else 0.0
    holding_force = 0.0 if recovering else friction_force + wrap_support
    pressure_support = response.pressure_pa * pressure_release_area_m2
    release_resistance = max(0.0, holding_force - pressure_support)
    release_authority = seat_tube_solve.crew_telemetry.recovery_thresholds.release_threshold_n
    release_margin = release_authority - release_resistance
    return RockContactD4(
        obstacle_id=obstacle.obstacle_id,
        segment_id=segment.segment_id,
        local_position=segment.local_position,
        obstacle_local_position=obstacle.local_position,
        clearance_m=clearance_m,
        penetration_m=penetration_m,
        recovered_previous_indentation_m=recovered_previous,
        indentation_m=indentation,
        pressure_pa=response.pressure_pa,
        pressure_release_support_n=pressure_support,
        normal_force_n=normal_force,
        damping_force_n=damping_force,
        friction_force_n=friction_force,
        wrap_support_n=wrap_support,
        holding_force_n=holding_force,
        release_resistance_n=release_resistance,
        release_authority_n=release_authority,
        release_margin_n=release_margin,
        wrapping=wrapping,
        pinned=release_margin < 0.0 and not recovering,
        recovering=recovering,
    )


def _xy_distance(first: Vec3, second: Vec3) -> float:
    return math.hypot(first.x - second.x, first.y - second.y)


def _xy_normal(vector: Vec3) -> Vec3:
    length = math.hypot(vector.x, vector.y)
    if length <= 1.0e-9:
        return Vec3(1.0, 0.0, 0.0)
    return Vec3(vector.x / length, vector.y / length, 0.0)


def _case_payload(case_id: str, solve: RockContactSolveD4, intent: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "intent": intent,
        "scoring_authority_enabled": solve.scoring_authority_enabled,
        "summary": {
            "contact_count": len(solve.contacts),
            "total_holding_force_n": solve.total_holding_force_n,
            "max_indentation_m": solve.max_indentation_m,
            "min_release_margin_n": solve.min_release_margin_n,
            "pinned_obstacle_count": solve.pinned_obstacle_count,
            "wrapping_contact_count": solve.wrapping_contact_count,
            "recovering_contact_count": solve.recovering_contact_count,
            "water_field_modified": solve.water_field_modified,
        },
        "contacts": [_contact_json(contact) for contact in solve.contacts],
    }


def _contact_json(contact: RockContactD4) -> dict[str, Any]:
    return {
        "obstacle_id": contact.obstacle_id,
        "segment_id": contact.segment_id,
        "local_position_m": _vec3_payload(contact.local_position),
        "obstacle_local_position_m": _vec3_payload(contact.obstacle_local_position),
        "clearance_m": contact.clearance_m,
        "penetration_m": contact.penetration_m,
        "recovered_previous_indentation_m": contact.recovered_previous_indentation_m,
        "indentation_m": contact.indentation_m,
        "pressure_pa": contact.pressure_pa,
        "pressure_release_support_n": contact.pressure_release_support_n,
        "normal_force_n": contact.normal_force_n,
        "damping_force_n": contact.damping_force_n,
        "friction_force_n": contact.friction_force_n,
        "wrap_support_n": contact.wrap_support_n,
        "holding_force_n": contact.holding_force_n,
        "release_resistance_n": contact.release_resistance_n,
        "release_authority_n": contact.release_authority_n,
        "release_margin_n": contact.release_margin_n,
        "wrapping": contact.wrapping,
        "pinned": contact.pinned,
        "recovering": contact.recovering,
    }


def _vec3_payload(vector: Vec3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
