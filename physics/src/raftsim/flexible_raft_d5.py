"""D5 deterministic telemetry and replay snapshots for flexible rafts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .flexible_raft_d1 import D1_SCORING_AUTHORITY
from .flexible_raft_d2 import SeatLoadCoupledTubeSolveD2, solve_seat_load_coupled_tube_d2
from .flexible_raft_d3 import OverwashFlipSolveD3, _synthetic_water_field, evaluate_overwash_flip_d3
from .flexible_raft_d4 import (
    RockContactSolveD4,
    RockObstacleD4,
    evaluate_rock_contact_wrap_pin_d4,
)
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    RaftState6DoF,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
)
from .scenario2_5d import RaftParameters2_5D


D5_TELEMETRY_REPLAY_FIXTURE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d5_telemetry_replay_fixture.json"
)
D5_TELEMETRY_REPLAY_SCHEMA = "raftsim.flexible_raft.d5_telemetry_replay.v1"


def build_flexible_raft_frame_snapshot_d5(
    *,
    case_id: str,
    frame_index: int,
    time_s: float,
    seat_tube_solve: SeatLoadCoupledTubeSolveD2,
    overwash_solve: OverwashFlipSolveD3,
    rock_contact_solve: RockContactSolveD4,
) -> dict[str, Any]:
    """Build one deterministic replay frame from D2-D4 reference outputs."""

    if frame_index < 0:
        raise ValueError("frame_index must be non-negative.")
    if time_s < 0.0:
        raise ValueError("time_s must be non-negative.")

    tube_responses = seat_tube_solve.tube_solve.tube_solve.segment_responses
    overwash_by_segment = {
        segment.segment_id: segment
        for segment in overwash_solve.segment_overwash
    }
    contacts_by_segment: dict[str, list[Any]] = {}
    for contact in rock_contact_solve.contacts:
        contacts_by_segment.setdefault(contact.segment_id, []).append(contact)

    frame = {
        "schema": D5_TELEMETRY_REPLAY_SCHEMA,
        "case_id": case_id,
        "frame_index": frame_index,
        "time_s": time_s,
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "rigid_state": _rigid_state_payload(seat_tube_solve.tube_solve.rigid_state),
        "crew_summary": {
            "occupied_seat_count": seat_tube_solve.crew_telemetry.occupied_seat_count,
            "active_action_count": seat_tube_solve.crew_telemetry.active_action_count,
            "high_side_count": seat_tube_solve.crew_telemetry.high_side_count,
            "brace_count": seat_tube_solve.crew_telemetry.brace_count,
            "recovery_count": seat_tube_solve.crew_telemetry.recovery_count,
            "roll_moment_nm": seat_tube_solve.crew_telemetry.roll_moment_nm,
            "pitch_moment_nm": seat_tube_solve.crew_telemetry.pitch_moment_nm,
        },
        "totals": {
            "tube_total_applied_load_n": seat_tube_solve.tube_solve.tube_solve.total_applied_load_n,
            "tube_total_volume_loss_m3": seat_tube_solve.tube_solve.tube_solve.total_volume_loss_m3,
            "overwash_total_flux_m3_s": overwash_solve.total_overtopping_flux_m3_s,
            "overwash_retained_water_mass_kg": overwash_solve.total_retained_water_mass_kg,
            "overwash_roll_moment_nm": overwash_solve.retained_water_roll_moment_nm,
            "contact_total_holding_force_n": rock_contact_solve.total_holding_force_n,
            "contact_min_release_margin_n": rock_contact_solve.min_release_margin_n,
            "contact_pinned_obstacle_count": rock_contact_solve.pinned_obstacle_count,
        },
        "segments": [
            _segment_snapshot(response, overwash_by_segment.get(response.segment_id), contacts_by_segment.get(response.segment_id, ()))
            for response in tube_responses
        ],
    }
    frame["frame_sha256"] = stable_json_sha256(frame)
    return frame


def build_flexible_raft_telemetry_replay_d5(
    frames: tuple[dict[str, Any], ...],
    *,
    replay_id: str,
) -> dict[str, Any]:
    """Build a deterministic replay envelope around frame snapshots."""

    if not replay_id:
        raise ValueError("replay_id must be non-empty.")
    if not frames:
        raise ValueError("frames must be non-empty.")
    payload = {
        "schema": D5_TELEMETRY_REPLAY_SCHEMA,
        "generated_on": "2026-07-16",
        "replay_id": replay_id,
        "status": "telemetry_replay_reference_recorded_not_gameplay_authority",
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "frame_count": len(frames),
        "frame_hashes": [frame["frame_sha256"] for frame in frames],
        "frames": list(frames),
        "model_contract": {
            "per_segment_tube_pressure_volume_freeboard_recorded": True,
            "floor_lacing_frame_loads_recorded": True,
            "overwash_flux_side_entrained_water_recorded": True,
            "contact_patch_release_margin_recorded": True,
            "water_and_contact_roll_moments_recorded": True,
            "deterministic_replay_hash_recorded": True,
            "gameplay_scoring_authority": "disabled_until_d6_fixture_suite_and_design_review",
        },
        "promotion_gate": {
            "may_drive_runtime_gameplay": False,
            "may_inform_engine_port": True,
            "requires_before_runtime_authority": [
                "D6 Chrono-or-reviewed compliant reference comparison",
                "engine-port replay byte-equivalence",
                "platform deterministic replay checks",
                "named-rapid consequence-line review",
            ],
        },
    }
    payload["replay_sha256"] = stable_json_sha256(payload)
    return payload


def build_flexible_raft_d5_fixture(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the committed D5 telemetry/replay fixture."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF(position=Vec3(3.0, 2.0, 0.0), linear_velocity=Vec3(0.0, 0.7, 0.0))
    water = _synthetic_water_field(surface_height_m=0.20, velocity=Vec3(0.0, -2.4, 0.0))
    obstacle = (RockObstacleD4("wrap_starboard_pillow", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),)

    neutral = solve_seat_load_coupled_tube_d2(state, properties, seats, parameters=params)
    neutral_overwash = evaluate_overwash_flip_d3(neutral, water, parameters=params)
    neutral_contact = evaluate_rock_contact_wrap_pin_d4(neutral, obstacle, parameters=params)
    frame0 = build_flexible_raft_frame_snapshot_d5(
        case_id="starboard_wrap_overwash_neutral",
        frame_index=0,
        time_s=0.0,
        seat_tube_solve=neutral,
        overwash_solve=neutral_overwash,
        rock_contact_solve=neutral_contact,
    )

    high_side = solve_seat_load_coupled_tube_d2(
        state,
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )
    high_side_overwash = evaluate_overwash_flip_d3(
        high_side,
        water,
        parameters=params,
        previous_retained_volume_by_segment={
            segment.segment_id: segment.retained_water_volume_m3
            for segment in neutral_overwash.segment_overwash
        },
    )
    high_side_contact = evaluate_rock_contact_wrap_pin_d4(
        high_side,
        obstacle,
        parameters=params,
        previous_indentation_by_segment={
            contact.segment_id: contact.indentation_m
            for contact in neutral_contact.contacts
        },
    )
    frame1 = build_flexible_raft_frame_snapshot_d5(
        case_id="starboard_wrap_overwash_high_side",
        frame_index=1,
        time_s=1.0 / 30.0,
        seat_tube_solve=high_side,
        overwash_solve=high_side_overwash,
        rock_contact_solve=high_side_contact,
    )
    return build_flexible_raft_telemetry_replay_d5(
        (frame0, frame1),
        replay_id="flexible_raft_d5_starboard_wrap_overwash_reference",
    )


def write_flexible_raft_d5_fixture(repo_root: Path) -> Path:
    """Write the committed D5 telemetry/replay fixture JSON."""

    payload = build_flexible_raft_d5_fixture()
    path = repo_root / D5_TELEMETRY_REPLAY_FIXTURE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def stable_json_sha256(payload: dict[str, Any]) -> str:
    """Return a stable hash while ignoring any existing hash fields."""

    stripped = _strip_hash_fields(payload)
    return hashlib.sha256(
        json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _strip_hash_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_hash_fields(child)
            for key, child in value.items()
            if key not in {"frame_sha256", "replay_sha256"}
        }
    if isinstance(value, list):
        return [_strip_hash_fields(child) for child in value]
    return value


def _segment_snapshot(response: Any, overwash: Any | None, contacts: Any) -> dict[str, Any]:
    contact_list = list(contacts)
    contact_roll_moment = sum(contact.normal_force_n * contact.local_position.y for contact in contact_list)
    return {
        "segment_id": response.segment_id,
        "local_position_m": _vec3_payload(response.local_position),
        "tube": {
            "pressure_pa": response.pressure_pa,
            "pressure_delta_pa": response.pressure_delta_pa,
            "volume_m3": response.volume_m3,
            "volume_loss_m3": response.volume_loss_m3,
            "compression_m": response.compression_m,
            "freeboard_loss_m": response.freeboard_loss_m,
            "floor_load_n": response.floor_load_n,
            "lacing_load_n": response.received_lacing_load_n,
            "frame_load_n": response.frame_load_n,
            "effective_load_n": response.effective_load_n,
        },
        "overwash": _overwash_snapshot(overwash),
        "contact": {
            "active": bool(contact_list),
            "contact_count": len(contact_list),
            "obstacle_ids": sorted({contact.obstacle_id for contact in contact_list}),
            "max_indentation_m": max((contact.indentation_m for contact in contact_list), default=0.0),
            "holding_force_n": sum(contact.holding_force_n for contact in contact_list),
            "min_release_margin_n": min((contact.release_margin_n for contact in contact_list), default=0.0),
            "pinned": any(contact.pinned for contact in contact_list),
            "wrapping": any(contact.wrapping for contact in contact_list),
            "recovering": any(contact.recovering for contact in contact_list),
            "contact_roll_moment_nm": contact_roll_moment,
        },
        "combined_roll_moment_nm": (overwash.retained_water_roll_moment_nm if overwash else 0.0)
        + contact_roll_moment,
    }


def _overwash_snapshot(overwash: Any | None) -> dict[str, Any]:
    if overwash is None:
        return {
            "upstream_exposed": False,
            "overtopping_flux_m3_s": 0.0,
            "retained_water_mass_kg": 0.0,
            "retained_water_roll_moment_nm": 0.0,
            "retained_water_pitch_moment_nm": 0.0,
            "entrained_water_side": "none",
        }
    return {
        "upstream_exposed": overwash.upstream_exposed,
        "overtopping_flux_m3_s": overwash.overtopping_flux_m3_s,
        "retained_water_mass_kg": overwash.retained_water_mass_kg,
        "retained_water_roll_moment_nm": overwash.retained_water_roll_moment_nm,
        "retained_water_pitch_moment_nm": overwash.retained_water_pitch_moment_nm,
        "entrained_water_side": _side_from_y(overwash.local_position.y, overwash.retained_water_mass_kg),
    }


def _rigid_state_payload(state: RaftState6DoF) -> dict[str, Any]:
    return {
        "position_m": _vec3_payload(state.position),
        "orientation_quaternion": {
            "w": state.orientation.w,
            "x": state.orientation.x,
            "y": state.orientation.y,
            "z": state.orientation.z,
        },
        "linear_velocity_mps": _vec3_payload(state.linear_velocity),
        "angular_velocity_rps": _vec3_payload(state.angular_velocity),
    }


def _side_from_y(y: float, mass_kg: float) -> str:
    if mass_kg <= 0.0:
        return "none"
    if y > 1.0e-9:
        return "starboard"
    if y < -1.0e-9:
        return "port"
    return "center"


def _vec3_payload(vector: Vec3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
