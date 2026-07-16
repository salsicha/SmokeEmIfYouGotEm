"""D2 seat-load coupling for the flexible-raft reference model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .flexible_raft_d1 import (
    D1_SCORING_AUTHORITY,
    RigidRaftCompliantTubeSolveD1,
    TubeLoadD1,
    TubeSegmentD1,
    build_default_compliant_tube_layout_d1,
    solve_compliant_tube_on_rigid_state_d1,
)
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    CrewSeat2_5D,
    CrewWeightTelemetry2_5D,
    RaftMassProperties,
    RaftState6DoF,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
    evaluate_crew_weight_distribution2_5d,
)
from .scenario2_5d import RaftParameters2_5D


D2_SEAT_LOAD_FIXTURE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d2_seat_load_fixture.json"
)
D2_SEAT_LOAD_SCHEMA = "raftsim.flexible_raft.d2_seat_load_coupling.v1"


@dataclass(frozen=True, slots=True)
class SeatTubeLoadD2:
    """Per-seat load mapped onto a local compliant tube segment."""

    seat_id: str
    role: str
    occupied: bool
    mass_kg: float
    force_n: float
    base_local_position: Vec3
    effective_local_position: Vec3
    target_segment_id: str
    target_freeboard_loss_m: float
    high_side_direction: int = 0
    brace: bool = False
    recovery: bool = False
    lean_was_clamped: bool = False


@dataclass(frozen=True, slots=True)
class SeatLoadCoupledTubeSolveD2:
    """D2 result tying crew action telemetry to tube/freeboard response."""

    schema: str
    scoring_authority: str
    crew_telemetry: CrewWeightTelemetry2_5D
    seat_loads: tuple[SeatTubeLoadD2, ...]
    tube_solve: RigidRaftCompliantTubeSolveD1
    port_freeboard_loss_m: float
    starboard_freeboard_loss_m: float
    stern_freeboard_loss_m: float
    bow_freeboard_loss_m: float
    port_total_freeboard_loss_m: float
    starboard_total_freeboard_loss_m: float
    stern_total_freeboard_loss_m: float
    bow_total_freeboard_loss_m: float
    max_seat_freeboard_loss_m: float

    @property
    def scoring_authority_enabled(self) -> bool:
        return False


def solve_seat_load_coupled_tube_d2(
    rigid_state: RaftState6DoF,
    properties: RaftMassProperties,
    seats: tuple[CrewSeat2_5D, ...],
    actions: tuple[CrewAction2_5D, ...] = (),
    *,
    parameters: RaftParameters2_5D | None = None,
    layout: tuple[TubeSegmentD1, ...] | None = None,
    max_lean_offset_m: float = 0.55,
    high_side_offset_m: float = 0.45,
    brace_center_drop_m: float = 0.04,
    brace_downforce_fraction: float = 0.08,
    recovery_downforce_fraction: float = 0.04,
) -> SeatLoadCoupledTubeSolveD2:
    """Convert current crew seats/actions into local compliant-tube loads."""

    if brace_downforce_fraction < 0.0:
        raise ValueError("brace_downforce_fraction must be non-negative.")
    if recovery_downforce_fraction < 0.0:
        raise ValueError("recovery_downforce_fraction must be non-negative.")

    params = parameters or RaftParameters2_5D()
    tube_layout = layout or build_default_compliant_tube_layout_d1(params)
    telemetry = evaluate_crew_weight_distribution2_5d(
        properties,
        seats,
        actions,
        raft_length_m=params.length_m,
        raft_width_m=params.width_m,
        max_lean_offset_m=max_lean_offset_m,
        high_side_offset_m=high_side_offset_m,
        brace_center_drop_m=brace_center_drop_m,
    )
    gravity_magnitude = properties.gravity.magnitude if properties.gravity.magnitude > 1.0e-9 else 9.81
    loads = tuple(
        TubeLoadD1(
            load_id=f"seat:{seat.seat_id}",
            local_position=seat.effective_local_position,
            force_n=_seat_force_n(
                seat.mass_kg,
                gravity_magnitude,
                brace=seat.brace,
                recovery=seat.recovery,
                brace_downforce_fraction=brace_downforce_fraction,
                recovery_downforce_fraction=recovery_downforce_fraction,
            ),
            source=f"d2_seat_load:{seat.role}",
        )
        for seat in telemetry.seat_telemetry
        if seat.occupied
    )
    rigid_tube_solve = solve_compliant_tube_on_rigid_state_d1(rigid_state, tube_layout, loads)
    responses_by_id = {
        response.segment_id: response
        for response in rigid_tube_solve.tube_solve.segment_responses
    }
    seat_loads = tuple(
        _seat_load_payload(
            seat,
            gravity_magnitude,
            tube_layout,
            responses_by_id,
            brace_downforce_fraction=brace_downforce_fraction,
            recovery_downforce_fraction=recovery_downforce_fraction,
        )
        for seat in telemetry.seat_telemetry
        if seat.occupied
    )
    return SeatLoadCoupledTubeSolveD2(
        schema=D2_SEAT_LOAD_SCHEMA,
        scoring_authority=D1_SCORING_AUTHORITY,
        crew_telemetry=telemetry,
        seat_loads=seat_loads,
        tube_solve=rigid_tube_solve,
        port_freeboard_loss_m=_max_freeboard_for_prefix(responses_by_id, "port_"),
        starboard_freeboard_loss_m=_max_freeboard_for_prefix(responses_by_id, "starboard_"),
        stern_freeboard_loss_m=_max_freeboard_for_prefix(responses_by_id, "stern_"),
        bow_freeboard_loss_m=_max_freeboard_for_prefix(responses_by_id, "bow_"),
        port_total_freeboard_loss_m=_sum_freeboard_for_prefix(responses_by_id, "port_"),
        starboard_total_freeboard_loss_m=_sum_freeboard_for_prefix(responses_by_id, "starboard_"),
        stern_total_freeboard_loss_m=_sum_freeboard_for_prefix(responses_by_id, "stern_"),
        bow_total_freeboard_loss_m=_sum_freeboard_for_prefix(responses_by_id, "bow_"),
        max_seat_freeboard_loss_m=max(
            (seat.target_freeboard_loss_m for seat in seat_loads),
            default=0.0,
        ),
    )


def build_seat_load_coupled_tube_d2_fixture(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the committed D2 seat-load/freeboard coupling fixture."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF()
    cases = [
        _case_payload(
            "neutral_crew",
            solve_seat_load_coupled_tube_d2(state, properties, seats, parameters=params),
            "Occupied guide/passenger seats sag local tube segments while preserving lateral balance.",
        ),
        _case_payload(
            "starboard_high_side",
            solve_seat_load_coupled_tube_d2(
                state,
                properties,
                seats,
                tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
                parameters=params,
            ),
            "High-side actions shift local load onto the starboard tube and change freeboard.",
        ),
        _case_payload(
            "port_lean_with_brace",
            solve_seat_load_coupled_tube_d2(
                state,
                properties,
                seats,
                tuple(
                    CrewAction2_5D(
                        seat.seat_id,
                        lean_offset=Vec3(0.0, -1.5, 0.0),
                        brace=seat.role == "passenger",
                    )
                    for seat in seats
                ),
                parameters=params,
            ),
            "Clamped port lean plus passenger brace drives port-side tube depression.",
        ),
    ]
    return {
        "schema": D2_SEAT_LOAD_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "seat_load_reference_fixture_recorded_not_gameplay_authority",
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "model_contract": {
            "uses_existing_crew_seats_and_actions": True,
            "occupancy_drives_local_tube_loads": True,
            "lean_and_high_side_shift_effective_local_position": True,
            "brace_and_recovery_add_bounded_downforce": True,
            "center_of_gravity_telemetry_retained": True,
            "gameplay_scoring_authority": "disabled_until_d6_fixture_suite_and_design_review",
        },
        "cases": cases,
        "promotion_gate": {
            "may_drive_runtime_gameplay": False,
            "may_inform_engine_port": True,
            "requires_before_runtime_authority": [
                "D3 overwash/flip water coupling",
                "D4 rock wrap/pin/release contact coupling",
                "D5 replay telemetry",
                "D6 flexible-raft behavioral fixture suite",
            ],
        },
    }


def write_seat_load_coupled_tube_d2_fixture(repo_root: Path) -> Path:
    """Write the committed D2 seat-load/freeboard fixture JSON."""

    payload = build_seat_load_coupled_tube_d2_fixture()
    path = repo_root / D2_SEAT_LOAD_FIXTURE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _seat_force_n(
    mass_kg: float,
    gravity_magnitude: float,
    *,
    brace: bool,
    recovery: bool,
    brace_downforce_fraction: float,
    recovery_downforce_fraction: float,
) -> float:
    multiplier = 1.0
    if brace:
        multiplier += brace_downforce_fraction
    if recovery:
        multiplier += recovery_downforce_fraction
    return mass_kg * gravity_magnitude * multiplier


def _seat_load_payload(
    seat: Any,
    gravity_magnitude: float,
    layout: tuple[TubeSegmentD1, ...],
    responses_by_id: dict[str, Any],
    *,
    brace_downforce_fraction: float,
    recovery_downforce_fraction: float,
) -> SeatTubeLoadD2:
    target = min(
        layout,
        key=lambda segment: (segment.local_position - seat.effective_local_position).magnitude_squared,
    )
    response = responses_by_id[target.segment_id]
    return SeatTubeLoadD2(
        seat_id=seat.seat_id,
        role=seat.role,
        occupied=seat.occupied,
        mass_kg=seat.mass_kg,
        force_n=_seat_force_n(
            seat.mass_kg,
            gravity_magnitude,
            brace=seat.brace,
            recovery=seat.recovery,
            brace_downforce_fraction=brace_downforce_fraction,
            recovery_downforce_fraction=recovery_downforce_fraction,
        ),
        base_local_position=seat.base_local_position,
        effective_local_position=seat.effective_local_position,
        target_segment_id=target.segment_id,
        target_freeboard_loss_m=response.freeboard_loss_m,
        high_side_direction=seat.high_side_direction,
        brace=seat.brace,
        recovery=seat.recovery,
        lean_was_clamped=seat.lean_was_clamped,
    )


def _case_payload(case_id: str, solve: SeatLoadCoupledTubeSolveD2, intent: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "intent": intent,
        "scoring_authority_enabled": solve.scoring_authority_enabled,
        "crew_telemetry": {
            "occupied_seat_count": solve.crew_telemetry.occupied_seat_count,
            "active_action_count": solve.crew_telemetry.active_action_count,
            "high_side_count": solve.crew_telemetry.high_side_count,
            "brace_count": solve.crew_telemetry.brace_count,
            "recovery_count": solve.crew_telemetry.recovery_count,
            "total_crew_mass_kg": solve.crew_telemetry.total_crew_mass_kg,
            "roll_moment_nm": solve.crew_telemetry.roll_moment_nm,
            "pitch_moment_nm": solve.crew_telemetry.pitch_moment_nm,
        },
        "freeboard_summary": {
            "port_freeboard_loss_m": solve.port_freeboard_loss_m,
            "starboard_freeboard_loss_m": solve.starboard_freeboard_loss_m,
            "stern_freeboard_loss_m": solve.stern_freeboard_loss_m,
            "bow_freeboard_loss_m": solve.bow_freeboard_loss_m,
            "port_total_freeboard_loss_m": solve.port_total_freeboard_loss_m,
            "starboard_total_freeboard_loss_m": solve.starboard_total_freeboard_loss_m,
            "stern_total_freeboard_loss_m": solve.stern_total_freeboard_loss_m,
            "bow_total_freeboard_loss_m": solve.bow_total_freeboard_loss_m,
            "max_seat_freeboard_loss_m": solve.max_seat_freeboard_loss_m,
            "tube_roll_load_bias_nm": solve.tube_solve.tube_solve.roll_load_bias_nm,
            "tube_pitch_load_bias_nm": solve.tube_solve.tube_solve.pitch_load_bias_nm,
        },
        "seat_loads": [_seat_payload(seat) for seat in solve.seat_loads],
    }


def _seat_payload(seat: SeatTubeLoadD2) -> dict[str, Any]:
    return {
        "seat_id": seat.seat_id,
        "role": seat.role,
        "occupied": seat.occupied,
        "mass_kg": seat.mass_kg,
        "force_n": seat.force_n,
        "base_local_position_m": _vec3_payload(seat.base_local_position),
        "effective_local_position_m": _vec3_payload(seat.effective_local_position),
        "target_segment_id": seat.target_segment_id,
        "target_freeboard_loss_m": seat.target_freeboard_loss_m,
        "high_side_direction": seat.high_side_direction,
        "brace": seat.brace,
        "recovery": seat.recovery,
        "lean_was_clamped": seat.lean_was_clamped,
    }


def _max_freeboard_for_prefix(responses_by_id: dict[str, Any], prefix: str) -> float:
    return max(
        (
            response.freeboard_loss_m
            for segment_id, response in responses_by_id.items()
            if segment_id.startswith(prefix)
        ),
        default=0.0,
    )


def _sum_freeboard_for_prefix(responses_by_id: dict[str, Any], prefix: str) -> float:
    return sum(
        response.freeboard_loss_m
        for segment_id, response in responses_by_id.items()
        if segment_id.startswith(prefix)
    )


def _vec3_payload(vector: Vec3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
