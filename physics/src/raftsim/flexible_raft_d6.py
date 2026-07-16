"""D6 behavioral validation-suite contract for flexible raft mechanics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .flexible_raft_d1 import build_default_compliant_tube_layout_d1
from .flexible_raft_d2 import solve_seat_load_coupled_tube_d2
from .flexible_raft_d3 import _synthetic_water_field, evaluate_overwash_flip_d3
from .flexible_raft_d4 import RockObstacleD4, evaluate_rock_contact_wrap_pin_d4
from .flexible_raft_d5 import build_flexible_raft_d5_fixture
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    RaftState6DoF,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
)
from .scenario2_5d import RaftParameters2_5D


D6_BEHAVIORAL_SUITE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_behavioral_suite.json"
)
D6_BEHAVIORAL_SUITE_SCHEMA = "raftsim.flexible_raft.d6_behavioral_validation_suite.v1"

REQUIRED_D6_FIXTURE_IDS = (
    "static_seat_load_sag",
    "traveling_crew_shift",
    "rock_pinch_wrap",
    "upstream_tube_overwash_flip",
    "timed_high_side_save",
    "post_contact_recovery",
    "pressure_flow_sweeps",
)


def build_flexible_raft_d6_behavioral_suite(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the D6 suite contract and current Python-reference metrics."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    context = _build_context(params)
    fixtures = [
        _static_seat_load_sag(context),
        _traveling_crew_shift(context),
        _rock_pinch_wrap(context),
        _upstream_tube_overwash_flip(context),
        _timed_high_side_save(context),
        _post_contact_recovery(context),
        _pressure_flow_sweeps(context),
    ]
    return {
        "schema": D6_BEHAVIORAL_SUITE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "behavioral_fixture_contract_recorded_reference_comparisons_pending",
        "d6_complete": False,
        "production_promoted": False,
        "fixture_count": len(fixtures),
        "required_fixture_ids": list(REQUIRED_D6_FIXTURE_IDS),
        "fixtures": fixtures,
        "reference_requirements": {
            "compliant_reference": {
                "required": True,
                "accepted_sources": [
                    "ProjectChrono",
                    "reviewed_offline_compliant_model",
                ],
                "status": "missing_measured_reference_results",
            },
            "chaos_rigid_baseline": {
                "required": True,
                "source_contract": "unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json",
                "status": "missing_measured_unreal_chaos_results",
            },
        },
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "next_required_actions": [
                "Run every fixture against Project Chrono or another reviewed compliant reference.",
                "Run every fixture against the measured Unreal Chaos rigid baseline.",
                "Attach telemetry/replay outputs with matching D5 segment channels.",
                "Compare behavior against fixture acceptance bands and record pass/fail evidence.",
            ],
        },
    }


def write_flexible_raft_d6_behavioral_suite(repo_root: Path) -> Path:
    """Write the committed D6 behavioral suite contract JSON."""

    payload = build_flexible_raft_d6_behavioral_suite()
    path = repo_root / D6_BEHAVIORAL_SUITE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _build_context(params: RaftParameters2_5D) -> dict[str, Any]:
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF(position=Vec3(3.0, 2.0, 0.0), linear_velocity=Vec3(0.0, 0.7, 0.0))
    return {
        "params": params,
        "properties": properties,
        "seats": seats,
        "state": state,
    }


def _static_seat_load_sag(context: dict[str, Any]) -> dict[str, Any]:
    params = context["params"]
    neutral = _tube(context)
    return _fixture_payload(
        "static_seat_load_sag",
        "Verify occupied guide/passenger seats create local tube sag without gameplay authority.",
        {
            "max_seat_freeboard_loss_m": neutral.max_seat_freeboard_loss_m,
            "port_total_freeboard_loss_m": neutral.port_total_freeboard_loss_m,
            "starboard_total_freeboard_loss_m": neutral.starboard_total_freeboard_loss_m,
            "loaded_crew_mass_kg": neutral.crew_telemetry.total_crew_mass_kg,
            "raft_length_m": params.length_m,
            "raft_width_m": params.width_m,
        },
        {
            "compliant_reference": "freeboard shape and loaded side balance within reviewed tolerance",
            "chaos_rigid_baseline": "rigid baseline records no local tube sag but matches global mass/CG telemetry",
        },
    )


def _traveling_crew_shift(context: dict[str, Any]) -> dict[str, Any]:
    neutral = _tube(context)
    port = _tube(context, tuple(CrewAction2_5D(seat.seat_id, lean_offset=Vec3(0.0, -1.5, 0.0)) for seat in context["seats"]))
    starboard = _tube(context, tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in context["seats"]))
    return _fixture_payload(
        "traveling_crew_shift",
        "Verify moving crew load travels across local tube segments and changes side freeboard.",
        {
            "neutral_roll_load_bias_nm": neutral.tube_solve.tube_solve.roll_load_bias_nm,
            "port_roll_load_bias_nm": port.tube_solve.tube_solve.roll_load_bias_nm,
            "starboard_roll_load_bias_nm": starboard.tube_solve.tube_solve.roll_load_bias_nm,
            "port_total_freeboard_delta_m": port.port_total_freeboard_loss_m - neutral.port_total_freeboard_loss_m,
            "starboard_total_freeboard_delta_m": starboard.starboard_total_freeboard_loss_m - neutral.starboard_total_freeboard_loss_m,
        },
        {
            "compliant_reference": "tube depression peak follows the crew shift direction over time",
            "chaos_rigid_baseline": "rigid baseline reports CG shift but no compliant local freeboard shape",
        },
    )


def _rock_pinch_wrap(context: dict[str, Any]) -> dict[str, Any]:
    tube = _tube(context)
    obstacle = (RockObstacleD4("wrap_starboard_pillow", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),)
    contact = evaluate_rock_contact_wrap_pin_d4(tube, obstacle, parameters=context["params"])
    return _fixture_payload(
        "rock_pinch_wrap",
        "Verify a wide boulder wraps multiple tube segments and records pin/release margins.",
        {
            "contact_count": len(contact.contacts),
            "wrapping_contact_count": contact.wrapping_contact_count,
            "pinned_obstacle_count": contact.pinned_obstacle_count,
            "max_indentation_m": contact.max_indentation_m,
            "min_release_margin_n": contact.min_release_margin_n,
        },
        {
            "compliant_reference": "wrap support and pressure release margins track compliant indentation",
            "chaos_rigid_baseline": "rigid contact has no pressure-dependent release support and should be recorded as baseline-only",
        },
    )


def _upstream_tube_overwash_flip(context: dict[str, Any]) -> dict[str, Any]:
    tube = _tube(context)
    water = _synthetic_water_field(surface_height_m=0.24, velocity=Vec3(0.0, -3.0, 0.0))
    overwash = evaluate_overwash_flip_d3(tube, water, parameters=context["params"])
    return _fixture_payload(
        "upstream_tube_overwash_flip",
        "Verify depressed upstream tube segments retain water and create roll moment.",
        {
            "total_overtopping_flux_m3_s": overwash.total_overtopping_flux_m3_s,
            "total_retained_water_mass_kg": overwash.total_retained_water_mass_kg,
            "retained_water_roll_moment_nm": overwash.retained_water_roll_moment_nm,
            "reference_flip_margin_nm": overwash.reference_flip_margin_nm,
            "reference_flip_risk": overwash.reference_flip_risk,
        },
        {
            "compliant_reference": "overtopping/retention grows with upstream tube depression and flow speed",
            "chaos_rigid_baseline": "rigid baseline cannot produce local tube-top overtopping without D2 deformation input",
        },
    )


def _timed_high_side_save(context: dict[str, Any]) -> dict[str, Any]:
    water = _synthetic_water_field(surface_height_m=0.24, velocity=Vec3(0.0, -3.0, 0.0))
    neutral = evaluate_overwash_flip_d3(_tube(context), water, parameters=context["params"])
    high_side = evaluate_overwash_flip_d3(
        _tube(context, tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in context["seats"])),
        water,
        parameters=context["params"],
        previous_retained_volume_by_segment={
            segment.segment_id: segment.retained_water_volume_m3
            for segment in neutral.segment_overwash
        },
    )
    return _fixture_payload(
        "timed_high_side_save",
        "Verify a timed high-side input changes retained-water roll margin and recovery thresholds.",
        {
            "neutral_flip_threshold_nm": neutral.reference_flip_threshold_nm,
            "high_side_flip_threshold_nm": high_side.reference_flip_threshold_nm,
            "neutral_flip_margin_nm": neutral.reference_flip_margin_nm,
            "high_side_flip_margin_nm": high_side.reference_flip_margin_nm,
            "margin_delta_nm": high_side.reference_flip_margin_nm - neutral.reference_flip_margin_nm,
        },
        {
            "compliant_reference": "reviewed save case must improve or explain flip margin under same flow",
            "chaos_rigid_baseline": "rigid baseline can only alter CG/recovery thresholds, not tube depression or retained water",
        },
    )


def _post_contact_recovery(context: dict[str, Any]) -> dict[str, Any]:
    tube = _tube(context)
    recovery = evaluate_rock_contact_wrap_pin_d4(
        tube,
        (),
        parameters=context["params"],
        previous_indentation_by_segment={"starboard_2": 0.12, "starboard_1": 0.08},
    )
    return _fixture_payload(
        "post_contact_recovery",
        "Verify prior tube indentation decays after contact clears.",
        {
            "recovering_contact_count": recovery.recovering_contact_count,
            "max_recovered_indentation_m": recovery.max_indentation_m,
            "total_holding_force_n": recovery.total_holding_force_n,
        },
        {
            "compliant_reference": "post-contact shape recovers monotonically without residual pin force",
            "chaos_rigid_baseline": "rigid baseline has no persistent tube indentation state",
        },
    )


def _pressure_flow_sweeps(context: dict[str, Any]) -> dict[str, Any]:
    params = context["params"]
    sweeps = []
    for nominal_pressure in (14_000.0, 18_000.0, 22_000.0):
        layout = build_default_compliant_tube_layout_d1(params, nominal_pressure_pa=nominal_pressure)
        tube = _tube(context, layout=layout)
        for velocity in (1.2, 2.4, 3.6):
            water = _synthetic_water_field(surface_height_m=0.22, velocity=Vec3(0.0, -velocity, 0.0))
            overwash = evaluate_overwash_flip_d3(tube, water, parameters=params, layout=layout)
            contact = evaluate_rock_contact_wrap_pin_d4(
                tube,
                (RockObstacleD4("pressure_sweep_wrap", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),),
                parameters=params,
                layout=layout,
            )
            sweeps.append(
                {
                    "nominal_pressure_pa": nominal_pressure,
                    "incoming_velocity_mps": velocity,
                    "overwash_flux_m3_s": overwash.total_overtopping_flux_m3_s,
                    "retained_water_roll_moment_nm": overwash.retained_water_roll_moment_nm,
                    "contact_min_release_margin_n": contact.min_release_margin_n,
                }
            )
    return _fixture_payload(
        "pressure_flow_sweeps",
        "Verify pressure and flow sweeps expose monotonic risk trends before engine porting.",
        {
            "sweep_case_count": len(sweeps),
            "sweeps": sweeps,
        },
        {
            "compliant_reference": "pressure and flow sweeps stay monotonic or record reviewed nonlinearity",
            "chaos_rigid_baseline": "rigid baseline comparison isolates non-compliant contact response",
        },
    )


def _tube(
    context: dict[str, Any],
    actions: tuple[CrewAction2_5D, ...] = (),
    *,
    layout: Any | None = None,
) -> Any:
    return solve_seat_load_coupled_tube_d2(
        context["state"],
        context["properties"],
        context["seats"],
        actions,
        parameters=context["params"],
        layout=layout,
    )


def _fixture_payload(
    fixture_id: str,
    objective: str,
    python_reference_metrics: dict[str, Any],
    acceptance_notes: dict[str, str],
) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "objective": objective,
        "python_reference_status": "generated_from_d1_d5_reference_stack",
        "python_reference_metrics": python_reference_metrics,
        "d5_replay_channels_required": [
            "tube.pressure_pa",
            "tube.volume_m3",
            "tube.freeboard_loss_m",
            "tube.floor_load_n",
            "tube.lacing_load_n",
            "overwash.overtopping_flux_m3_s",
            "overwash.entrained_water_side",
            "contact.max_indentation_m",
            "contact.min_release_margin_n",
            "combined_roll_moment_nm",
        ],
        "comparison_targets": [
            {
                "target_id": "project_chrono_or_reviewed_compliant_model",
                "required": True,
                "status": "pending_measured_reference",
                "acceptance_note": acceptance_notes["compliant_reference"],
            },
            {
                "target_id": "unreal_chaos_rigid_baseline",
                "required": True,
                "status": "pending_measured_chaos_baseline",
                "acceptance_note": acceptance_notes["chaos_rigid_baseline"],
            },
        ],
        "can_promote": False,
    }


def build_d6_replay_channel_probe() -> dict[str, Any]:
    """Return D5 replay metadata used by D6 tests and future engine adapters."""

    replay = build_flexible_raft_d5_fixture()
    return {
        "replay_id": replay["replay_id"],
        "frame_count": replay["frame_count"],
        "frame_hashes": replay["frame_hashes"],
        "replay_sha256": replay["replay_sha256"],
    }
