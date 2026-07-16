"""D3 overwash and flip-risk reference coupling for flexible rafts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .flexible_raft_d1 import D1_SCORING_AUTHORITY, TubeSegmentD1, build_default_compliant_tube_layout_d1
from .flexible_raft_d2 import SeatLoadCoupledTubeSolveD2, solve_seat_load_coupled_tube_d2
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    RaftState6DoF,
    WaterField2_5D,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
)
from .scenario2_5d import RaftParameters2_5D


D3_OVERWASH_FIXTURE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d3_overwash_fixture.json"
)
D3_OVERWASH_SCHEMA = "raftsim.flexible_raft.d3_overwash_flip_reference.v1"


@dataclass(frozen=True, slots=True)
class SegmentOverwashD3:
    """Per-segment water overtopping and retained-water loading telemetry."""

    segment_id: str
    local_position: Vec3
    water_surface_m: float
    depressed_tube_top_m: float
    overtopping_depth_m: float
    incoming_speed_mps: float
    overtopping_flux_m3_s: float
    drainage_flux_m3_s: float
    retained_water_volume_m3: float
    retained_water_mass_kg: float
    retained_water_roll_moment_nm: float
    retained_water_pitch_moment_nm: float
    upstream_exposed: bool
    wet: bool
    feature_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OverwashFlipSolveD3:
    """Reference-only overwash solve layered on the D2 tube state."""

    schema: str
    scoring_authority: str
    segment_overwash: tuple[SegmentOverwashD3, ...]
    total_overtopping_flux_m3_s: float
    total_drainage_flux_m3_s: float
    total_retained_water_volume_m3: float
    total_retained_water_mass_kg: float
    retained_water_roll_moment_nm: float
    retained_water_pitch_moment_nm: float
    reference_flip_threshold_nm: float
    reference_flip_margin_nm: float
    reference_flip_risk: bool

    @property
    def scoring_authority_enabled(self) -> bool:
        return False


def evaluate_overwash_flip_d3(
    seat_tube_solve: SeatLoadCoupledTubeSolveD2,
    water: WaterField2_5D,
    *,
    parameters: RaftParameters2_5D | None = None,
    layout: tuple[TubeSegmentD1, ...] | None = None,
    previous_retained_volume_by_segment: dict[str, float] | None = None,
    dt: float = 1.0 / 30.0,
    base_tube_top_freeboard_m: float = 0.16,
    flux_coefficient: float = 0.65,
    drainage_rate_per_s: float = 0.55,
    water_density_kg_m3: float = 1000.0,
    gravity_mps2: float = 9.81,
) -> OverwashFlipSolveD3:
    """Sample depressed upstream tube segments and retain/drain overtopped water."""

    if dt <= 0.0:
        raise ValueError("dt must be positive.")
    if base_tube_top_freeboard_m < 0.0:
        raise ValueError("base_tube_top_freeboard_m must be non-negative.")
    if flux_coefficient < 0.0:
        raise ValueError("flux_coefficient must be non-negative.")
    if drainage_rate_per_s < 0.0:
        raise ValueError("drainage_rate_per_s must be non-negative.")
    if water_density_kg_m3 <= 0.0 or gravity_mps2 <= 0.0:
        raise ValueError("water density and gravity must be positive.")

    params = parameters or RaftParameters2_5D()
    tube_layout = layout or build_default_compliant_tube_layout_d1(params)
    retained_previous = previous_retained_volume_by_segment or {}
    rigid_state = seat_tube_solve.tube_solve.rigid_state
    responses_by_id = {
        response.segment_id: response
        for response in seat_tube_solve.tube_solve.tube_solve.segment_responses
    }

    segment_results: list[SegmentOverwashD3] = []
    for segment in tube_layout:
        response = responses_by_id[segment.segment_id]
        world_position = rigid_state.world_point(response.local_position)
        water_sample = water.sample(world_position.x, world_position.y)
        world_normal = rigid_state.orientation.rotate_vector(segment.outward_normal).normalized()
        relative_water_velocity = water_sample.velocity - rigid_state.point_velocity(response.local_position)
        incoming_speed = max(0.0, -relative_water_velocity.dot(world_normal))
        depressed_tube_top = world_position.z + base_tube_top_freeboard_m - response.freeboard_loss_m
        overtopping_depth = max(0.0, water_sample.surface_height - depressed_tube_top)
        upstream_exposed = water_sample.wet and incoming_speed > 1.0e-6 and overtopping_depth > 1.0e-6
        flux = (
            flux_coefficient * overtopping_depth * incoming_speed * segment.tributary_length_m
            if upstream_exposed
            else 0.0
        )
        previous_volume = max(0.0, retained_previous.get(segment.segment_id, 0.0))
        drainage_flux = min(previous_volume / dt, previous_volume * drainage_rate_per_s)
        retained_volume = max(0.0, previous_volume + flux * dt - drainage_flux * dt)
        retained_mass = retained_volume * water_density_kg_m3
        vertical_load = retained_mass * gravity_mps2
        segment_results.append(
            SegmentOverwashD3(
                segment_id=segment.segment_id,
                local_position=response.local_position,
                water_surface_m=water_sample.surface_height,
                depressed_tube_top_m=depressed_tube_top,
                overtopping_depth_m=overtopping_depth,
                incoming_speed_mps=incoming_speed,
                overtopping_flux_m3_s=flux,
                drainage_flux_m3_s=drainage_flux,
                retained_water_volume_m3=retained_volume,
                retained_water_mass_kg=retained_mass,
                retained_water_roll_moment_nm=vertical_load * response.local_position.y,
                retained_water_pitch_moment_nm=vertical_load * response.local_position.x,
                upstream_exposed=upstream_exposed,
                wet=water_sample.wet,
                feature_tags=water_sample.feature_tags,
            )
        )

    retained_roll = sum(segment.retained_water_roll_moment_nm for segment in segment_results)
    threshold = seat_tube_solve.crew_telemetry.recovery_thresholds.flip_threshold_nm
    margin = threshold - abs(retained_roll)
    return OverwashFlipSolveD3(
        schema=D3_OVERWASH_SCHEMA,
        scoring_authority=D1_SCORING_AUTHORITY,
        segment_overwash=tuple(segment_results),
        total_overtopping_flux_m3_s=sum(segment.overtopping_flux_m3_s for segment in segment_results),
        total_drainage_flux_m3_s=sum(segment.drainage_flux_m3_s for segment in segment_results),
        total_retained_water_volume_m3=sum(segment.retained_water_volume_m3 for segment in segment_results),
        total_retained_water_mass_kg=sum(segment.retained_water_mass_kg for segment in segment_results),
        retained_water_roll_moment_nm=retained_roll,
        retained_water_pitch_moment_nm=sum(segment.retained_water_pitch_moment_nm for segment in segment_results),
        reference_flip_threshold_nm=threshold,
        reference_flip_margin_nm=margin,
        reference_flip_risk=margin < 0.0,
    )


def build_overwash_flip_d3_fixture(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the committed D3 overwash/flip reference fixture."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF(position=Vec3(3.0, 2.0, 0.0))
    calm_water = _synthetic_water_field(surface_height_m=0.05, velocity=Vec3(0.0, 0.0, 0.0))
    starboard_water = _synthetic_water_field(surface_height_m=0.20, velocity=Vec3(0.0, -2.4, 0.0))
    neutral = solve_seat_load_coupled_tube_d2(state, properties, seats, parameters=params)
    high_side = solve_seat_load_coupled_tube_d2(
        state,
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )
    initial_overwash = evaluate_overwash_flip_d3(neutral, starboard_water, parameters=params)
    drain_down = evaluate_overwash_flip_d3(
        neutral,
        calm_water,
        parameters=params,
        previous_retained_volume_by_segment={
            segment.segment_id: segment.retained_water_volume_m3
            for segment in initial_overwash.segment_overwash
        },
    )
    cases = [
        _case_payload(
            "calm_no_overtopping",
            evaluate_overwash_flip_d3(neutral, calm_water, parameters=params),
            "Calm water below the depressed tube top should not overtop or retain water.",
        ),
        _case_payload(
            "starboard_incoming_overwash",
            initial_overwash,
            "Incoming starboard water overtops depressed upstream tube segments.",
        ),
        _case_payload(
            "starboard_high_side_counterplay_reference",
            evaluate_overwash_flip_d3(high_side, starboard_water, parameters=params),
            "High-side crew action changes tube depression and the reference flip margin.",
        ),
        _case_payload(
            "retained_water_drains_without_new_flux",
            drain_down,
            "Previously retained water drains deterministically when overtopping stops.",
        ),
    ]
    return {
        "schema": D3_OVERWASH_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "overwash_flip_reference_fixture_recorded_not_gameplay_authority",
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "model_contract": {
            "accepted_water_sampler_coupled": "WaterField2_5D",
            "uses_deformed_d2_tube_freeboard": True,
            "retained_water_mass_and_drainage_recorded": True,
            "roll_moment_reported_reference_only": True,
            "gameplay_scoring_authority": "disabled_until_d6_fixture_suite_and_design_review",
        },
        "cases": cases,
        "promotion_gate": {
            "may_drive_runtime_gameplay": False,
            "may_inform_engine_port": True,
            "requires_before_runtime_authority": [
                "D4 rock wrap/pin/release contact coupling",
                "D5 replay telemetry",
                "D6 Chrono-or-reviewed compliant reference comparison",
                "named-rapid consequence-line review",
            ],
        },
    }


def write_overwash_flip_d3_fixture(repo_root: Path) -> Path:
    """Write the committed D3 overwash/flip reference fixture JSON."""

    payload = build_overwash_flip_d3_fixture()
    path = repo_root / D3_OVERWASH_FIXTURE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _synthetic_water_field(
    *,
    surface_height_m: float,
    velocity: Vec3,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    nx: int = 8,
    ny: int = 8,
    dx: float = 1.0,
    dy: float = 1.0,
) -> WaterField2_5D:
    shape = (ny, nx)
    bed = np.full(shape, -1.0, dtype=np.float64)
    eta = np.full(shape, surface_height_m, dtype=np.float64)
    depth = eta - bed
    return WaterField2_5D(
        origin_x=origin_x,
        origin_y=origin_y,
        dx=dx,
        dy=dy,
        bed=bed,
        depth=depth,
        eta=eta,
        u=np.full(shape, velocity.x, dtype=np.float64),
        v=np.full(shape, velocity.y, dtype=np.float64),
        wet=np.ones(shape, dtype=np.bool_),
        normal_x=np.zeros(shape, dtype=np.float64),
        normal_y=np.zeros(shape, dtype=np.float64),
        normal_z=np.ones(shape, dtype=np.float64),
    )


def _case_payload(case_id: str, solve: OverwashFlipSolveD3, intent: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "intent": intent,
        "scoring_authority_enabled": solve.scoring_authority_enabled,
        "summary": {
            "total_overtopping_flux_m3_s": solve.total_overtopping_flux_m3_s,
            "total_drainage_flux_m3_s": solve.total_drainage_flux_m3_s,
            "total_retained_water_volume_m3": solve.total_retained_water_volume_m3,
            "total_retained_water_mass_kg": solve.total_retained_water_mass_kg,
            "retained_water_roll_moment_nm": solve.retained_water_roll_moment_nm,
            "retained_water_pitch_moment_nm": solve.retained_water_pitch_moment_nm,
            "reference_flip_threshold_nm": solve.reference_flip_threshold_nm,
            "reference_flip_margin_nm": solve.reference_flip_margin_nm,
            "reference_flip_risk": solve.reference_flip_risk,
        },
        "segments": [_segment_payload(segment) for segment in solve.segment_overwash],
    }


def _segment_payload(segment: SegmentOverwashD3) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "local_position_m": _vec3_payload(segment.local_position),
        "water_surface_m": segment.water_surface_m,
        "depressed_tube_top_m": segment.depressed_tube_top_m,
        "overtopping_depth_m": segment.overtopping_depth_m,
        "incoming_speed_mps": segment.incoming_speed_mps,
        "overtopping_flux_m3_s": segment.overtopping_flux_m3_s,
        "drainage_flux_m3_s": segment.drainage_flux_m3_s,
        "retained_water_volume_m3": segment.retained_water_volume_m3,
        "retained_water_mass_kg": segment.retained_water_mass_kg,
        "retained_water_roll_moment_nm": segment.retained_water_roll_moment_nm,
        "retained_water_pitch_moment_nm": segment.retained_water_pitch_moment_nm,
        "upstream_exposed": segment.upstream_exposed,
        "wet": segment.wet,
        "feature_tags": list(segment.feature_tags),
    }


def _vec3_payload(vector: Vec3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
