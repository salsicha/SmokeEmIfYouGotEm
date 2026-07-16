"""D1 flexible-raft reference model for compliant perimeter tubes."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .math3d import Vec3
from .raft_coupling2_5d import RaftState6DoF
from .scenario2_5d import RaftParameters2_5D


D1_COMPLIANT_TUBE_FIXTURE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d1_compliant_tube_fixture.json"
)
D1_COMPLIANT_TUBE_SCHEMA = "raftsim.flexible_raft.d1_compliant_tube_reference.v1"
D1_SCORING_AUTHORITY = "disabled_reference_only"


@dataclass(frozen=True, slots=True)
class TubeSegmentD1:
    """One pressure/volume-compliant perimeter tube segment."""

    segment_id: str
    local_position: Vec3
    outward_normal: Vec3
    tributary_length_m: float
    rest_volume_m3: float
    contact_area_m2: float
    nominal_pressure_pa: float
    compliance_m3_per_pa: float
    floor_coupling_fraction: float = 0.16
    lacing_coupling_fraction: float = 0.12
    frame_coupling_fraction: float = 0.07

    def __post_init__(self) -> None:
        if not self.segment_id:
            raise ValueError("segment_id must be non-empty.")
        if self.tributary_length_m <= 0.0:
            raise ValueError("tributary_length_m must be positive.")
        if self.rest_volume_m3 <= 0.0:
            raise ValueError("rest_volume_m3 must be positive.")
        if self.contact_area_m2 <= 0.0:
            raise ValueError("contact_area_m2 must be positive.")
        if self.nominal_pressure_pa <= 0.0:
            raise ValueError("nominal_pressure_pa must be positive.")
        if self.compliance_m3_per_pa <= 0.0:
            raise ValueError("compliance_m3_per_pa must be positive.")
        coupling = (
            self.floor_coupling_fraction
            + self.lacing_coupling_fraction
            + self.frame_coupling_fraction
        )
        if coupling >= 1.0:
            raise ValueError("coupling fractions must leave a positive direct load share.")
        for name in (
            "floor_coupling_fraction",
            "lacing_coupling_fraction",
            "frame_coupling_fraction",
        ):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be non-negative.")
        object.__setattr__(self, "outward_normal", self.outward_normal.normalized())


@dataclass(frozen=True, slots=True)
class TubeLoadD1:
    """Downward local load used by the D1 reference model."""

    load_id: str
    local_position: Vec3
    force_n: float
    source: str = "reference_fixture"

    def __post_init__(self) -> None:
        if not self.load_id:
            raise ValueError("load_id must be non-empty.")
        if self.force_n < 0.0:
            raise ValueError("force_n must be non-negative.")
        if not self.source:
            raise ValueError("source must be non-empty.")


@dataclass(frozen=True, slots=True)
class TubeSegmentResponseD1:
    """Local tube response after direct, lacing, floor, and frame coupling."""

    segment_id: str
    local_position: Vec3
    direct_load_n: float
    received_lacing_load_n: float
    floor_load_n: float
    frame_load_n: float
    effective_load_n: float
    pressure_pa: float
    pressure_delta_pa: float
    volume_m3: float
    volume_loss_m3: float
    compression_m: float
    freeboard_loss_m: float
    bounded: bool


@dataclass(frozen=True, slots=True)
class CompliantTubeSolveD1:
    """Closed-form deterministic D1 tube solve result."""

    schema: str
    scoring_authority: str
    segment_responses: tuple[TubeSegmentResponseD1, ...]
    total_applied_load_n: float
    total_effective_tube_load_n: float
    total_volume_loss_m3: float
    max_freeboard_loss_m: float
    max_pressure_delta_pa: float
    roll_load_bias_nm: float
    pitch_load_bias_nm: float
    bounded_segment_count: int

    @property
    def scoring_authority_enabled(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RigidRaftCompliantTubeSolveD1:
    """D1 tube solve sampled through the existing rigid raft transform."""

    rigid_state: RaftState6DoF
    tube_solve: CompliantTubeSolveD1
    world_segment_positions: tuple[Vec3, ...]


def build_default_compliant_tube_layout_d1(
    parameters: RaftParameters2_5D | None = None,
    *,
    segment_count_per_side: int = 4,
    segment_count_per_end: int = 2,
    nominal_pressure_pa: float = 18_000.0,
) -> tuple[TubeSegmentD1, ...]:
    """Build a closed perimeter-tube layout around the existing rigid raft size."""

    params = parameters or RaftParameters2_5D()
    if segment_count_per_side <= 0 or segment_count_per_end <= 0:
        raise ValueError("segment counts must be positive.")

    half_length = params.length_m * 0.5
    half_width = params.width_m * 0.5
    tube_radius = params.tube_radius_m
    side_step = params.length_m / segment_count_per_side
    end_step = params.width_m / segment_count_per_end

    specs: list[tuple[str, Vec3, Vec3, float]] = []
    for index in range(segment_count_per_side):
        x = -half_length + side_step * (index + 0.5)
        specs.append((f"port_{index}", Vec3(x, -half_width, 0.0), Vec3(0.0, -1.0, 0.0), side_step))
    for index in range(segment_count_per_end):
        y = -half_width + end_step * (index + 0.5)
        specs.append((f"bow_{index}", Vec3(half_length, y, 0.0), Vec3(1.0, 0.0, 0.0), end_step))
    for index in reversed(range(segment_count_per_side)):
        x = -half_length + side_step * (index + 0.5)
        specs.append((f"starboard_{index}", Vec3(x, half_width, 0.0), Vec3(0.0, 1.0, 0.0), side_step))
    for index in reversed(range(segment_count_per_end)):
        y = -half_width + end_step * (index + 0.5)
        specs.append((f"stern_{index}", Vec3(-half_length, y, 0.0), Vec3(-1.0, 0.0, 0.0), end_step))

    return tuple(
        _build_segment(
            segment_id=segment_id,
            local_position=local_position,
            outward_normal=normal,
            tributary_length_m=length,
            tube_radius_m=tube_radius,
            nominal_pressure_pa=nominal_pressure_pa,
        )
        for segment_id, local_position, normal, length in specs
    )


def solve_compliant_tube_d1(
    layout: tuple[TubeSegmentD1, ...],
    loads: tuple[TubeLoadD1, ...],
    *,
    max_segment_volume_loss_fraction: float = 0.18,
    max_freeboard_loss_m: float = 0.28,
) -> CompliantTubeSolveD1:
    """Solve deterministic tube compression from bounded local downward loads."""

    if not layout:
        raise ValueError("layout must contain at least one tube segment.")
    segment_ids = [segment.segment_id for segment in layout]
    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("layout segment ids must be unique.")
    if max_segment_volume_loss_fraction <= 0.0:
        raise ValueError("max_segment_volume_loss_fraction must be positive.")
    if max_freeboard_loss_m <= 0.0:
        raise ValueError("max_freeboard_loss_m must be positive.")

    direct_loads = [0.0 for _ in layout]
    lacing_loads = [0.0 for _ in layout]
    floor_loads = [0.0 for _ in layout]
    frame_loads = [0.0 for _ in layout]
    total_applied_load = 0.0

    for load in loads:
        target = _nearest_segment_index(layout, load.local_position)
        segment = layout[target]
        direct_fraction = (
            1.0
            - segment.floor_coupling_fraction
            - segment.lacing_coupling_fraction
            - segment.frame_coupling_fraction
        )
        total_applied_load += load.force_n
        direct_loads[target] += load.force_n * direct_fraction
        previous_index = (target - 1) % len(layout)
        next_index = (target + 1) % len(layout)
        lacing_share = load.force_n * segment.lacing_coupling_fraction * 0.5
        lacing_loads[previous_index] += lacing_share
        lacing_loads[next_index] += lacing_share
        floor_share = load.force_n * segment.floor_coupling_fraction / len(layout)
        for index in range(len(layout)):
            floor_loads[index] += floor_share
        opposite_index = (target + len(layout) // 2) % len(layout)
        frame_share = load.force_n * segment.frame_coupling_fraction * 0.5
        frame_loads[target] += frame_share
        frame_loads[opposite_index] += frame_share

    responses: list[TubeSegmentResponseD1] = []
    for index, segment in enumerate(layout):
        effective_load = direct_loads[index] + lacing_loads[index] + floor_loads[index] + frame_loads[index]
        pressure_delta = effective_load / segment.contact_area_m2
        unbounded_volume_loss = segment.compliance_m3_per_pa * pressure_delta
        max_volume_loss = segment.rest_volume_m3 * max_segment_volume_loss_fraction
        volume_loss = min(unbounded_volume_loss, max_volume_loss)
        unbounded_compression = volume_loss / segment.contact_area_m2
        compression = min(unbounded_compression, max_freeboard_loss_m)
        bounded = (
            unbounded_volume_loss > max_volume_loss + 1.0e-12
            or unbounded_compression > max_freeboard_loss_m + 1.0e-12
        )
        responses.append(
            TubeSegmentResponseD1(
                segment_id=segment.segment_id,
                local_position=segment.local_position,
                direct_load_n=direct_loads[index],
                received_lacing_load_n=lacing_loads[index],
                floor_load_n=floor_loads[index],
                frame_load_n=frame_loads[index],
                effective_load_n=effective_load,
                pressure_pa=segment.nominal_pressure_pa + pressure_delta,
                pressure_delta_pa=pressure_delta,
                volume_m3=segment.rest_volume_m3 - volume_loss,
                volume_loss_m3=volume_loss,
                compression_m=compression,
                freeboard_loss_m=compression,
                bounded=bounded,
            )
        )

    return CompliantTubeSolveD1(
        schema=D1_COMPLIANT_TUBE_SCHEMA,
        scoring_authority=D1_SCORING_AUTHORITY,
        segment_responses=tuple(responses),
        total_applied_load_n=total_applied_load,
        total_effective_tube_load_n=sum(response.effective_load_n for response in responses),
        total_volume_loss_m3=sum(response.volume_loss_m3 for response in responses),
        max_freeboard_loss_m=max((response.freeboard_loss_m for response in responses), default=0.0),
        max_pressure_delta_pa=max((response.pressure_delta_pa for response in responses), default=0.0),
        roll_load_bias_nm=sum(response.effective_load_n * response.local_position.y for response in responses),
        pitch_load_bias_nm=sum(response.effective_load_n * response.local_position.x for response in responses),
        bounded_segment_count=sum(1 for response in responses if response.bounded),
    )


def solve_compliant_tube_on_rigid_state_d1(
    rigid_state: RaftState6DoF,
    layout: tuple[TubeSegmentD1, ...],
    loads: tuple[TubeLoadD1, ...],
    *,
    max_segment_volume_loss_fraction: float = 0.18,
    max_freeboard_loss_m: float = 0.28,
) -> RigidRaftCompliantTubeSolveD1:
    """Layer the local D1 tube solve onto the validated rigid 6-DoF state."""

    tube_solve = solve_compliant_tube_d1(
        layout,
        loads,
        max_segment_volume_loss_fraction=max_segment_volume_loss_fraction,
        max_freeboard_loss_m=max_freeboard_loss_m,
    )
    return RigidRaftCompliantTubeSolveD1(
        rigid_state=rigid_state,
        tube_solve=tube_solve,
        world_segment_positions=tuple(
            rigid_state.world_point(response.local_position)
            for response in tube_solve.segment_responses
        ),
    )


def build_compliant_tube_d1_fixture(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the committed D1 reference fixture payload."""

    layout = build_default_compliant_tube_layout_d1(parameters)
    cases = [
        _case_payload(
            "uniform_reference_download",
            layout,
            tuple(
                TubeLoadD1(
                    load_id=f"uniform_{segment.segment_id}",
                    local_position=segment.local_position,
                    force_n=80.0,
                    source="uniform_reference_guardrail",
                )
                for segment in layout
            ),
            "Symmetric perimeter load should keep roll and pitch bias near zero.",
        ),
        _case_payload(
            "starboard_contact_push",
            layout,
            (
                TubeLoadD1(
                    load_id="starboard_mid_contact",
                    local_position=Vec3(0.35, 0.95, 0.0),
                    force_n=1_450.0,
                    source="abstract_side_contact_guardrail",
                ),
            ),
            "Side contact should deform the contacted tube and lacing neighbors.",
        ),
        _case_payload(
            "bow_floor_frame_transfer",
            layout,
            (
                TubeLoadD1(
                    load_id="bow_floor_download",
                    local_position=Vec3(2.05, 0.0, 0.0),
                    force_n=1_050.0,
                    source="abstract_floor_frame_guardrail",
                ),
            ),
            "Bow load should show floor spread and frame transfer across the perimeter.",
        ),
    ]
    return {
        "schema": D1_COMPLIANT_TUBE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "reference_fixture_recorded_not_gameplay_authority",
        "scoring_authority": D1_SCORING_AUTHORITY,
        "scoring_authority_enabled": False,
        "model_contract": {
            "layers_on_rigid_6dof_raft_state": True,
            "deterministic_python_reference_first": True,
            "pressure_volume_compliant_perimeter_tubes": True,
            "floor_lacing_frame_coupling_recorded": True,
            "crew_seat_load_authority": "deferred_to_d2",
            "gameplay_scoring_authority": "disabled_until_d6_fixture_suite_and_design_review",
        },
        "layout": [_segment_payload(segment, index, len(layout)) for index, segment in enumerate(layout)],
        "cases": cases,
        "promotion_gate": {
            "may_drive_runtime_gameplay": False,
            "may_inform_engine_port": True,
            "requires_before_runtime_authority": [
                "D2 crew/seat loads coupled into tube deformation and freeboard",
                "D3-D6 flexible-raft fixture suite",
                "C++/Unreal implementation parity against this reference",
                "human gameplay review for flips, wraps, pins, and releases",
            ],
        },
    }


def write_compliant_tube_d1_fixture(repo_root: Path) -> Path:
    """Write the committed D1 reference fixture JSON."""

    payload = build_compliant_tube_d1_fixture()
    path = repo_root / D1_COMPLIANT_TUBE_FIXTURE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _build_segment(
    *,
    segment_id: str,
    local_position: Vec3,
    outward_normal: Vec3,
    tributary_length_m: float,
    tube_radius_m: float,
    nominal_pressure_pa: float,
) -> TubeSegmentD1:
    rest_volume = math.pi * tube_radius_m * tube_radius_m * tributary_length_m
    contact_area = max(0.08, tube_radius_m * tributary_length_m * 0.55)
    return TubeSegmentD1(
        segment_id=segment_id,
        local_position=local_position,
        outward_normal=outward_normal,
        tributary_length_m=tributary_length_m,
        rest_volume_m3=rest_volume,
        contact_area_m2=contact_area,
        nominal_pressure_pa=nominal_pressure_pa,
        compliance_m3_per_pa=max(3.0e-8, rest_volume * 2.5e-6),
    )


def _nearest_segment_index(layout: tuple[TubeSegmentD1, ...], position: Vec3) -> int:
    return min(
        range(len(layout)),
        key=lambda index: (layout[index].local_position - position).magnitude_squared,
    )


def _case_payload(
    case_id: str,
    layout: tuple[TubeSegmentD1, ...],
    loads: tuple[TubeLoadD1, ...],
    intent: str,
) -> dict[str, Any]:
    rigid_solve = solve_compliant_tube_on_rigid_state_d1(RaftState6DoF(), layout, loads)
    return {
        "case_id": case_id,
        "intent": intent,
        "loads": [_load_payload(load) for load in loads],
        "rigid_state_layer": _rigid_state_layer_payload(rigid_solve),
        "result": _solve_payload(rigid_solve.tube_solve),
    }


def _segment_payload(segment: TubeSegmentD1, index: int, segment_count: int) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "index": index,
        "previous_segment_id": segment.segment_id if segment_count == 1 else None,
        "next_segment_id": segment.segment_id if segment_count == 1 else None,
        "closed_loop_previous_index": (index - 1) % segment_count,
        "closed_loop_next_index": (index + 1) % segment_count,
        "local_position_m": _vec3_payload(segment.local_position),
        "outward_normal": _vec3_payload(segment.outward_normal),
        "tributary_length_m": segment.tributary_length_m,
        "rest_volume_m3": segment.rest_volume_m3,
        "contact_area_m2": segment.contact_area_m2,
        "nominal_pressure_pa": segment.nominal_pressure_pa,
        "compliance_m3_per_pa": segment.compliance_m3_per_pa,
        "floor_coupling_fraction": segment.floor_coupling_fraction,
        "lacing_coupling_fraction": segment.lacing_coupling_fraction,
        "frame_coupling_fraction": segment.frame_coupling_fraction,
    }


def _load_payload(load: TubeLoadD1) -> dict[str, Any]:
    return {
        "load_id": load.load_id,
        "local_position_m": _vec3_payload(load.local_position),
        "force_n": load.force_n,
        "source": load.source,
    }


def _solve_payload(solve: CompliantTubeSolveD1) -> dict[str, Any]:
    return {
        "schema": solve.schema,
        "scoring_authority": solve.scoring_authority,
        "scoring_authority_enabled": solve.scoring_authority_enabled,
        "total_applied_load_n": solve.total_applied_load_n,
        "total_effective_tube_load_n": solve.total_effective_tube_load_n,
        "total_volume_loss_m3": solve.total_volume_loss_m3,
        "max_freeboard_loss_m": solve.max_freeboard_loss_m,
        "max_pressure_delta_pa": solve.max_pressure_delta_pa,
        "roll_load_bias_nm": solve.roll_load_bias_nm,
        "pitch_load_bias_nm": solve.pitch_load_bias_nm,
        "bounded_segment_count": solve.bounded_segment_count,
        "segments": [_response_payload(response) for response in solve.segment_responses],
    }


def _rigid_state_layer_payload(solve: RigidRaftCompliantTubeSolveD1) -> dict[str, Any]:
    state = solve.rigid_state
    return {
        "state_position_m": _vec3_payload(state.position),
        "state_orientation_quaternion": {
            "w": state.orientation.w,
            "x": state.orientation.x,
            "y": state.orientation.y,
            "z": state.orientation.z,
        },
        "world_segment_positions_m": [
            _vec3_payload(position)
            for position in solve.world_segment_positions
        ],
    }


def _response_payload(response: TubeSegmentResponseD1) -> dict[str, Any]:
    return {
        "segment_id": response.segment_id,
        "local_position_m": _vec3_payload(response.local_position),
        "direct_load_n": response.direct_load_n,
        "received_lacing_load_n": response.received_lacing_load_n,
        "floor_load_n": response.floor_load_n,
        "frame_load_n": response.frame_load_n,
        "effective_load_n": response.effective_load_n,
        "pressure_pa": response.pressure_pa,
        "pressure_delta_pa": response.pressure_delta_pa,
        "volume_m3": response.volume_m3,
        "volume_loss_m3": response.volume_loss_m3,
        "compression_m": response.compression_m,
        "freeboard_loss_m": response.freeboard_loss_m,
        "bounded": response.bounded,
    }


def _vec3_payload(vector: Vec3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
