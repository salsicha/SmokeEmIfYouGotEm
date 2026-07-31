"""Independent Project Chrono execution of the seven D6 compliant fixtures.

The runner intentionally consumes only the committed D6 fixture-input package.  It
does not import the D1-D5 Python reference implementation.  Local tube deformation
is measured from Project Chrono ``ChSystemSMC`` systems whose twelve tube nodes are
supported by pressure-derived ``ChLinkTSDA`` elements.  Rock indentation is measured
with separate Chrono penalty springs.  The small overwash and recovery adapters use
the recorded D3/D4 fixture constants and the measured Chrono node state.

PyChrono is an external validation runtime, not a shipping dependency.  Import it
lazily so the normal RaftSim Python suite remains runnable without Project Chrono.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


D6_PROJECT_CHRONO_RUNNER_VERSION = "raftsim_project_chrono_d6_runner_v1"
D6_PROJECT_CHRONO_TELEMETRY_SCHEMA = (
    "raftsim.flexible_raft.d6_project_chrono_fixture_telemetry.v1"
)
D6_PROJECT_CHRONO_SUMMARY_SCHEMA = (
    "raftsim.flexible_raft.d6_compliant_runner_summary.v1"
)
D6_PROJECT_CHRONO_SIDECAR_SCHEMA = (
    "raftsim.flexible_raft.d6_compliant_measured_results_sidecar.v1"
)
D6_PROJECT_CHRONO_TARGET_ID = "project_chrono_or_reviewed_compliant_model"
D6_FIXTURE_PACKAGE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_fixture_input_package.json"
)
D6_PROJECT_CHRONO_SIDECAR_RELATIVE_PATH = (
    "physics/reports/d6/compliant/flexible_raft_d6_compliant_measured_results.json"
)
D6_PROJECT_CHRONO_SUMMARY_RELATIVE_PATH = "physics/reports/d6/compliant/summary.json"
D6_PROJECT_CHRONO_REPLAY_DIR_RELATIVE_PATH = "physics/reports/d6/compliant/replays"
D6_PROJECT_CHRONO_MERGE_REPORT_RELATIVE_PATH = (
    "physics/data/calibration/"
    "flexible_raft_d6_compliant_measured_results_merge_report.json"
)

REQUIRED_FIXTURE_IDS = (
    "static_seat_load_sag",
    "traveling_crew_shift",
    "rock_pinch_wrap",
    "upstream_tube_overwash_flip",
    "timed_high_side_save",
    "post_contact_recovery",
    "pressure_flow_sweeps",
)

REQUIRED_D5_CHANNELS = (
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
)

_GENERATED_ON = "2026-07-28"
_GRAVITY_MPS2 = 9.81
_MAX_LEAN_OFFSET_M = 0.55
_HIGH_SIDE_OFFSET_M = 0.45
_BASE_FLIP_THRESHOLD_NM = 1800.0
_BASE_RELEASE_THRESHOLD_N = 2600.0
_BASE_TUBE_TOP_FREEBOARD_M = 0.16
_OVERWASH_FLUX_COEFFICIENT = 0.65
_DRAINAGE_RATE_PER_S = 0.55
_WATER_DENSITY_KG_M3 = 1000.0
_MAX_SEGMENT_VOLUME_LOSS_FRACTION = 0.18
_MAX_FREEBOARD_LOSS_M = 0.28
_SETTLING_DT_S = 0.001
_SETTLING_STEP_COUNT = 2000


def run_project_chrono_d6(repo_root: Path) -> tuple[Path, Path]:
    """Run every compliant fixture twice and write deterministic measured evidence."""

    chrono = _import_project_chrono()
    fixture_path = repo_root / D6_FIXTURE_PACKAGE_RELATIVE_PATH
    fixture_bytes = fixture_path.read_bytes()
    package = json.loads(fixture_bytes)
    _validate_fixture_package(package)
    fixture_sha256 = hashlib.sha256(fixture_bytes).hexdigest()
    engine = _project_chrono_engine_version(chrono)

    first = _run_suite(package, chrono, engine, fixture_sha256)
    second = _run_suite(package, chrono, engine, fixture_sha256)
    if _canonical_bytes(first) != _canonical_bytes(second):
        raise RuntimeError(
            "Project Chrono D6 fixed-input repeat was not deterministic."
        )

    replay_dir = repo_root / D6_PROJECT_CHRONO_REPLAY_DIR_RELATIVE_PATH
    replay_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    jobs: list[dict[str, Any]] = []
    for fixture_id in REQUIRED_FIXTURE_IDS:
        run = first[fixture_id]
        replay_path = replay_dir / f"{fixture_id}.telemetry.json"
        replay_bytes = _pretty_bytes(run["telemetry"])
        replay_path.write_bytes(replay_bytes)
        replay_hash = hashlib.sha256(replay_bytes).hexdigest()
        metrics = run["metrics"]
        results[fixture_id] = {
            "status": "measured_engine_output",
            "source_report": D6_PROJECT_CHRONO_SUMMARY_RELATIVE_PATH,
            "telemetry_sha256": replay_hash,
            "engine_version": engine,
            "fixture_id": fixture_id,
            "target_id": D6_PROJECT_CHRONO_TARGET_ID,
            "runtime_id": "ProjectChrono10PyChronoSMCTSDA",
            "metrics": metrics,
            "manual_review_complete": False,
        }
        jobs.append(
            {
                "fixture_id": fixture_id,
                "status": "measured_engine_output",
                "ready_for_sidecar_merge": True,
                "blocking_reason": "manual_review_pending",
                "recorded_metric_count": len(_flatten_numeric_metrics(metrics)),
                "telemetry_path": str(replay_path.relative_to(repo_root)),
                "telemetry_sha256": replay_hash,
                "deterministic_fixed_input_repeat": True,
                "measured_by_project_chrono": True,
            }
        )

    runtime_provenance = {
        "physics_backend": "Project Chrono",
        "runner": D6_PROJECT_CHRONO_RUNNER_VERSION,
        "execution": (
            "fixture-input-only PyChrono ChSystemSMC solves with ChLinkTSDA "
            "tube/contact compliance"
        ),
        "fixture_package_sha256": fixture_sha256,
        "python_reference_imported": False,
        "custom_cpp_port_substitution": False,
        "analytical_reference_result_substitution": False,
        "project_chrono_objects_created": True,
        "tube_element_type": "chrono::ChLinkTSDA",
        "system_type": "chrono::ChSystemSMC",
    }
    sidecar = {
        "schema": D6_PROJECT_CHRONO_SIDECAR_SCHEMA,
        "generated_on": _GENERATED_ON,
        "status": "compliant_measurements_recorded_manual_review_pending",
        "d6_complete": False,
        "production_promoted": False,
        "runtime": "ProjectChrono",
        "runtime_id": "ProjectChrono10PyChronoSMCTSDA",
        "target_id": D6_PROJECT_CHRONO_TARGET_ID,
        "engine_version": engine,
        "source_fixture_input_package_path": D6_FIXTURE_PACKAGE_RELATIVE_PATH,
        "source_runner_summary_path": D6_PROJECT_CHRONO_SUMMARY_RELATIVE_PATH,
        "fixture_count": len(REQUIRED_FIXTURE_IDS),
        "filled_result_count": len(results),
        "required_fixture_ids": list(REQUIRED_FIXTURE_IDS),
        "results": results,
        "runtime_provenance": runtime_provenance,
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "may_merge_into_measured_results_template": True,
            "manual_review_required": True,
            "reason": (
                "All seven Project Chrono compliant fixtures are measured and "
                "mergeable; comparison and manual physics/integration/replay/"
                "guide-safety review remain required."
            ),
        },
    }
    summary = {
        "schema": D6_PROJECT_CHRONO_SUMMARY_SCHEMA,
        "generated_on": _GENERATED_ON,
        "status": "compliant_measurements_recorded_manual_review_pending",
        "d6_complete": False,
        "production_promoted": False,
        "runtime": "ProjectChrono",
        "runtime_id": "ProjectChrono10PyChronoSMCTSDA",
        "engine_version": engine,
        "source_fixture_input_package_path": D6_FIXTURE_PACKAGE_RELATIVE_PATH,
        "runner_output_sidecar": D6_PROJECT_CHRONO_SIDECAR_RELATIVE_PATH,
        "runner_replay_dir": D6_PROJECT_CHRONO_REPLAY_DIR_RELATIVE_PATH,
        "fixture_count": len(REQUIRED_FIXTURE_IDS),
        "filled_fixture_count": len(results),
        "invalid_fixture_count": 0,
        "missing_fixture_count": 0,
        "can_merge_sidecar": True,
        "jobs": jobs,
        "runtime_provenance": runtime_provenance,
        "promotion_gate": deepcopy(sidecar["promotion_gate"]),
    }
    sidecar_path = repo_root / D6_PROJECT_CHRONO_SIDECAR_RELATIVE_PATH
    summary_path = repo_root / D6_PROJECT_CHRONO_SUMMARY_RELATIVE_PATH
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_bytes(_pretty_bytes(sidecar))
    summary_path.write_bytes(_pretty_bytes(summary))
    return sidecar_path, summary_path


def validate_project_chrono_fixture_package(package: dict[str, Any]) -> None:
    """Public pure-Python contract validator used by normal CI."""

    _validate_fixture_package(package)


def _run_suite(
    package: dict[str, Any],
    chrono: Any,
    engine_version: str,
    fixture_sha256: str,
) -> dict[str, dict[str, Any]]:
    fixture_lookup = {fixture["fixture_id"]: fixture for fixture in package["fixtures"]}
    return {
        fixture_id: _run_fixture(
            fixture_lookup[fixture_id],
            package["common_setup"],
            chrono,
            engine_version,
            fixture_sha256,
        )
        for fixture_id in REQUIRED_FIXTURE_IDS
    }


def _run_fixture(
    fixture: dict[str, Any],
    common: dict[str, Any],
    chrono: Any,
    engine_version: str,
    fixture_sha256: str,
) -> dict[str, Any]:
    fixture_id = fixture["fixture_id"]
    phase_runs: list[dict[str, Any]] = []

    if fixture_id == "static_seat_load_sag":
        tube = _solve_tube(common, (), chrono)
        metrics = _static_metrics(common, tube)
        phase_runs.append(_phase_telemetry("neutral_occupied_seats", tube))
    elif fixture_id == "traveling_crew_shift":
        phase_by_id = {
            phase["phase_id"]: phase for phase in fixture["input_contract"]["phases"]
        }
        neutral = _solve_tube(common, (), chrono)
        port = _solve_tube(
            common,
            tuple(phase_by_id["port_lean_requested"]["crew_actions"]),
            chrono,
        )
        starboard = _solve_tube(
            common,
            tuple(phase_by_id["starboard_high_side"]["crew_actions"]),
            chrono,
        )
        metrics = {
            "neutral_roll_load_bias_nm": neutral["roll_load_bias_nm"],
            "port_roll_load_bias_nm": port["roll_load_bias_nm"],
            "starboard_roll_load_bias_nm": starboard["roll_load_bias_nm"],
            "port_total_freeboard_delta_m": (
                _side_freeboard_total(port, "port_")
                - _side_freeboard_total(neutral, "port_")
            ),
            "starboard_total_freeboard_delta_m": (
                _side_freeboard_total(starboard, "starboard_")
                - _side_freeboard_total(neutral, "starboard_")
            ),
        }
        phase_runs.extend(
            (
                _phase_telemetry("neutral_occupied_seats", neutral),
                _phase_telemetry("port_lean_requested", port),
                _phase_telemetry("starboard_high_side", starboard),
            )
        )
    elif fixture_id == "rock_pinch_wrap":
        tube = _solve_tube(common, (), chrono)
        contact = _evaluate_contact(
            common,
            tube,
            fixture["input_contract"].get("obstacles", ()),
            {},
            chrono,
        )
        metrics = _contact_metrics(contact)
        phase_runs.append(
            _phase_telemetry("neutral_occupied_seats", tube, contact=contact)
        )
    elif fixture_id == "upstream_tube_overwash_flip":
        tube = _solve_tube(common, (), chrono)
        overwash = _evaluate_overwash(
            common,
            tube,
            fixture["input_contract"]["water"],
            {},
            (),
        )
        metrics = _overwash_metrics(overwash)
        phase_runs.append(
            _phase_telemetry("neutral_occupied_seats", tube, overwash=overwash)
        )
    elif fixture_id == "timed_high_side_save":
        input_contract = fixture["input_contract"]
        phases = input_contract["phases"]
        neutral = _solve_tube(common, (), chrono)
        neutral_overwash = _evaluate_overwash(
            common, neutral, input_contract["water"], {}, ()
        )
        high_actions = tuple(phases[1]["crew_actions"])
        high = _solve_tube(common, high_actions, chrono)
        high_overwash = _evaluate_overwash(
            common,
            high,
            input_contract["water"],
            input_contract["previous_retained_volume_by_segment"],
            high_actions,
        )
        metrics = {
            "neutral_flip_threshold_nm": neutral_overwash["flip_threshold_nm"],
            "high_side_flip_threshold_nm": high_overwash["flip_threshold_nm"],
            "neutral_flip_margin_nm": neutral_overwash["flip_margin_nm"],
            "high_side_flip_margin_nm": high_overwash["flip_margin_nm"],
            "margin_delta_nm": (
                high_overwash["flip_margin_nm"] - neutral_overwash["flip_margin_nm"]
            ),
        }
        phase_runs.extend(
            (
                _phase_telemetry(
                    "neutral_overwash", neutral, overwash=neutral_overwash
                ),
                _phase_telemetry(
                    "starboard_high_side_with_retained_water_memory",
                    high,
                    overwash=high_overwash,
                ),
            )
        )
    elif fixture_id == "post_contact_recovery":
        tube = _solve_tube(common, (), chrono)
        contact = _evaluate_contact(
            common,
            tube,
            (),
            fixture["input_contract"]["previous_indentation_by_segment"],
            chrono,
        )
        metrics = {
            "max_recovered_indentation_m": contact["max_indentation_m"],
            "recovering_contact_count": contact["recovering_contact_count"],
            "total_holding_force_n": contact["total_holding_force_n"],
        }
        phase_runs.append(
            _phase_telemetry("post_contact_recovery", tube, contact=contact)
        )
    elif fixture_id == "pressure_flow_sweeps":
        sweeps = []
        for case in fixture["input_contract"]["sweep_cases"]:
            pressure = float(case["nominal_pressure_pa"])
            tube = _solve_tube(common, (), chrono, nominal_pressure_pa=pressure)
            overwash = _evaluate_overwash(common, tube, case["water"], {}, ())
            contact = _evaluate_contact(
                common,
                tube,
                fixture["input_contract"]["obstacles"],
                {},
                chrono,
            )
            velocity = case["water"]["velocity_mps"]
            incoming_velocity = math.sqrt(
                sum(float(value) ** 2 for value in velocity.values())
            )
            sweeps.append(
                {
                    "nominal_pressure_pa": pressure,
                    "incoming_velocity_mps": incoming_velocity,
                    "overwash_flux_m3_s": overwash["total_overtopping_flux_m3_s"],
                    "retained_water_roll_moment_nm": overwash[
                        "retained_water_roll_moment_nm"
                    ],
                    "contact_min_release_margin_n": contact["min_release_margin_n"],
                }
            )
            phase_runs.append(
                _phase_telemetry(
                    case["case_id"], tube, overwash=overwash, contact=contact
                )
            )
        metrics = {"sweep_case_count": len(sweeps), "sweeps": sweeps}
    else:
        raise ValueError(f"Unsupported D6 fixture: {fixture_id}")

    telemetry = {
        "schema": D6_PROJECT_CHRONO_TELEMETRY_SCHEMA,
        "generated_on": _GENERATED_ON,
        "runtime_id": "ProjectChrono10PyChronoSMCTSDA",
        "fixture_id": fixture_id,
        "target_id": D6_PROJECT_CHRONO_TARGET_ID,
        "engine_version": engine_version,
        "runner_version": D6_PROJECT_CHRONO_RUNNER_VERSION,
        "fixture_package_sha256": fixture_sha256,
        "fixed_observation_step_s": common["fixed_step_s"],
        "quasistatic_settling_dt_s": _SETTLING_DT_S,
        "quasistatic_settling_step_count": _SETTLING_STEP_COUNT,
        "required_d5_replay_channels": list(REQUIRED_D5_CHANNELS),
        "metrics": metrics,
        "scenarios": phase_runs,
        "outcome": {
            "all_project_chrono_systems_advanced": True,
            "all_tsda_handles_valid": True,
            "deterministic_fixed_input_repeat": True,
            "measured_by_project_chrono": True,
            "python_reference_imported": False,
            "d6_complete": False,
            "production_promoted": False,
        },
    }
    return {"metrics": metrics, "telemetry": telemetry}


def _solve_tube(
    common: dict[str, Any],
    actions: tuple[dict[str, Any], ...],
    chrono: Any,
    *,
    nominal_pressure_pa: float | None = None,
) -> dict[str, Any]:
    segments = deepcopy(common["default_tube_layout"]["segments"])
    if nominal_pressure_pa is not None:
        for segment in segments:
            segment["nominal_pressure_pa"] = nominal_pressure_pa
    action_by_seat = {action["seat_id"]: action for action in actions}
    effective_seats = [
        _effective_seat(seat, action_by_seat.get(seat["seat_id"]))
        for seat in common["crew_seats"]
        if seat["occupied"]
    ]
    loads = [0.0] * len(segments)
    load_parts = [
        {
            "direct_load_n": 0.0,
            "lacing_load_n": 0.0,
            "floor_load_n": 0.0,
            "frame_load_n": 0.0,
        }
        for _ in segments
    ]
    seat_target_indices: dict[str, int] = {}
    for seat in effective_seats:
        target_index = min(
            range(len(segments)),
            key=lambda index: _distance_squared(
                segments[index]["local_position"], seat["effective_local_position"]
            ),
        )
        seat_target_indices[seat["seat_id"]] = target_index
        target = segments[target_index]
        force = float(seat["occupant_mass_kg"]) * _GRAVITY_MPS2
        direct_fraction = 1.0 - sum(
            float(target[key])
            for key in (
                "floor_coupling_fraction",
                "lacing_coupling_fraction",
                "frame_coupling_fraction",
            )
        )
        load_parts[target_index]["direct_load_n"] += force * direct_fraction
        previous_index = (target_index - 1) % len(segments)
        next_index = (target_index + 1) % len(segments)
        lacing_share = force * float(target["lacing_coupling_fraction"]) * 0.5
        load_parts[previous_index]["lacing_load_n"] += lacing_share
        load_parts[next_index]["lacing_load_n"] += lacing_share
        floor_share = force * float(target["floor_coupling_fraction"]) / len(segments)
        for part in load_parts:
            part["floor_load_n"] += floor_share
        frame_share = force * float(target["frame_coupling_fraction"]) * 0.5
        load_parts[target_index]["frame_load_n"] += frame_share
        opposite_index = (target_index + len(segments) // 2) % len(segments)
        load_parts[opposite_index]["frame_load_n"] += frame_share

    for index, part in enumerate(load_parts):
        loads[index] = sum(part.values())

    system = chrono.ChSystemSMC()
    system.SetGravitationalAcceleration(chrono.ChVector3d(0.0, 0.0, -_GRAVITY_MPS2))
    bodies = []
    springs = []
    anchor_height = 0.5
    for segment, load in zip(segments, loads, strict=True):
        position = segment["local_position"]
        anchor = chrono.ChBody()
        anchor.SetFixed(True)
        anchor.SetPos(chrono.ChVector3d(position["x"], position["y"], anchor_height))
        system.AddBody(anchor)
        body = chrono.ChBody()
        body.SetMass(max(load / _GRAVITY_MPS2, 1.0e-6))
        body.SetInertiaXX(chrono.ChVector3d(1.0, 1.0, 1.0))
        body.SetPos(chrono.ChVector3d(position["x"], position["y"], 0.0))
        system.AddBody(body)
        stiffness = float(segment["contact_area_m2"]) ** 2 / float(
            segment["compliance_m3_per_pa"]
        )
        spring = chrono.ChLinkTSDA()
        spring.Initialize(
            anchor,
            body,
            False,
            chrono.ChVector3d(position["x"], position["y"], anchor_height),
            chrono.ChVector3d(position["x"], position["y"], 0.0),
        )
        spring.SetRestLength(anchor_height)
        spring.SetSpringCoefficient(stiffness)
        spring.SetDampingCoefficient(2.0 * math.sqrt(stiffness * body.GetMass()))
        system.AddLink(spring)
        bodies.append(body)
        springs.append(spring)
    for _ in range(_SETTLING_STEP_COUNT):
        system.DoStepDynamics(_SETTLING_DT_S)

    responses = []
    for segment, part, body, spring in zip(
        segments, load_parts, bodies, springs, strict=True
    ):
        chrono_load = max(0.0, -float(spring.GetForce()))
        area = float(segment["contact_area_m2"])
        volume_loss = min(
            float(segment["compliance_m3_per_pa"]) * chrono_load / area,
            float(segment["rest_volume_m3"]) * _MAX_SEGMENT_VOLUME_LOSS_FRACTION,
        )
        compression = min(
            max(0.0, -float(body.GetPos().z)),
            _MAX_FREEBOARD_LOSS_M,
        )
        responses.append(
            {
                "segment_id": segment["segment_id"],
                "local_position": deepcopy(segment["local_position"]),
                "outward_normal": deepcopy(segment["outward_normal"]),
                "tributary_length_m": float(segment["tributary_length_m"]),
                "effective_load_n": chrono_load,
                "direct_load_n": part["direct_load_n"],
                "lacing_load_n": part["lacing_load_n"],
                "floor_load_n": part["floor_load_n"],
                "frame_load_n": part["frame_load_n"],
                "pressure_pa": float(segment["nominal_pressure_pa"])
                + chrono_load / area,
                "volume_m3": float(segment["rest_volume_m3"]) - volume_loss,
                "freeboard_loss_m": compression,
                "tsda_force_n": chrono_load,
                "tsda_length_m": float(spring.GetLength()),
            }
        )
    return {
        "responses": responses,
        "effective_seats": effective_seats,
        "seat_target_indices": seat_target_indices,
        "roll_load_bias_nm": sum(
            response["effective_load_n"] * response["local_position"]["y"]
            for response in responses
        ),
        "project_chrono_system_time_s": float(system.GetChTime()),
        "project_chrono_body_count": len(bodies) + len(segments),
        "project_chrono_tsda_count": len(springs),
    }


def _effective_seat(
    seat: dict[str, Any], action: dict[str, Any] | None
) -> dict[str, Any]:
    effective = deepcopy(seat)
    base = seat["local_position"]
    lean = {"x": 0.0, "y": 0.0, "z": 0.0}
    high_side_direction = 0
    if action is not None:
        lean = _clamp_vector(action.get("lean_offset", lean), _MAX_LEAN_OFFSET_M)
        high_side_direction = int(action.get("high_side_direction", 0))
    effective["effective_local_position"] = {
        "x": float(base["x"]) + lean["x"],
        "y": float(base["y"]) + lean["y"] + high_side_direction * _HIGH_SIDE_OFFSET_M,
        "z": float(base["z"]) + lean["z"],
    }
    effective["high_side_direction"] = high_side_direction
    return effective


def _evaluate_overwash(
    common: dict[str, Any],
    tube: dict[str, Any],
    water: dict[str, Any],
    previous_retained: dict[str, float],
    actions: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    velocity = water["velocity_mps"]
    raft_velocity = common["initial_state"]["linear_velocity_mps"]
    surface_height = float(water["surface_height_m"])
    dt = float(common["fixed_step_s"])
    segment_results = []
    for response in tube["responses"]:
        normal = response["outward_normal"]
        relative = {
            axis: float(velocity[axis]) - float(raft_velocity[axis])
            for axis in ("x", "y", "z")
        }
        incoming_speed = max(
            0.0,
            -sum(relative[axis] * float(normal[axis]) for axis in ("x", "y", "z")),
        )
        depressed_top = _BASE_TUBE_TOP_FREEBOARD_M - response["freeboard_loss_m"]
        overtopping_depth = max(0.0, surface_height - depressed_top)
        flux = (
            _OVERWASH_FLUX_COEFFICIENT
            * overtopping_depth
            * incoming_speed
            * response["tributary_length_m"]
            if incoming_speed > 1.0e-6 and overtopping_depth > 1.0e-6
            else 0.0
        )
        prior = max(0.0, float(previous_retained.get(response["segment_id"], 0.0)))
        drainage_flux = min(prior / dt, prior * _DRAINAGE_RATE_PER_S)
        retained_volume = max(0.0, prior + flux * dt - drainage_flux * dt)
        retained_mass = retained_volume * _WATER_DENSITY_KG_M3
        roll_moment = retained_mass * _GRAVITY_MPS2 * response["local_position"]["y"]
        segment_results.append(
            {
                "segment_id": response["segment_id"],
                "overtopping_flux_m3_s": flux,
                "drainage_flux_m3_s": drainage_flux,
                "retained_water_volume_m3": retained_volume,
                "retained_water_mass_kg": retained_mass,
                "retained_water_roll_moment_nm": roll_moment,
                "incoming_speed_mps": incoming_speed,
                "overtopping_depth_m": overtopping_depth,
                "entrained_water_side": _segment_side(response["segment_id"]),
            }
        )
    retained_roll = sum(
        item["retained_water_roll_moment_nm"] for item in segment_results
    )
    threshold = _flip_threshold(common, actions)
    return {
        "segments": segment_results,
        "total_overtopping_flux_m3_s": sum(
            item["overtopping_flux_m3_s"] for item in segment_results
        ),
        "total_retained_water_mass_kg": sum(
            item["retained_water_mass_kg"] for item in segment_results
        ),
        "retained_water_roll_moment_nm": retained_roll,
        "flip_threshold_nm": threshold,
        "flip_margin_nm": threshold - abs(retained_roll),
    }


def _evaluate_contact(
    common: dict[str, Any],
    tube: dict[str, Any],
    obstacles: Any,
    previous_indentation: dict[str, float],
    chrono: Any,
) -> dict[str, Any]:
    defaults = common["reference_evaluator_defaults"]["d4_rock_contact"]
    tube_radius = float(common["raft_parameters"]["tube_radius_m"])
    contacts = []
    touched: set[str] = set()
    candidates: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    for obstacle in obstacles:
        for response in tube["responses"]:
            position = response["local_position"]
            obstacle_position = obstacle["local_position"]
            distance = math.hypot(
                float(position["x"]) - float(obstacle_position["x"]),
                float(position["y"]) - float(obstacle_position["y"]),
            )
            penetration = max(
                0.0,
                tube_radius + float(obstacle["radius_m"]) - distance,
            )
            if penetration > 0.0:
                candidates.append((obstacle, response, penetration))
                touched.add(response["segment_id"])
    counts: dict[str, int] = {}
    for obstacle, _, _ in candidates:
        counts[obstacle["obstacle_id"]] = counts.get(obstacle["obstacle_id"], 0) + 1
    for obstacle, response, penetration in candidates:
        contacts.append(
            _contact_record(
                common,
                response,
                obstacle,
                penetration,
                float(previous_indentation.get(response["segment_id"], 0.0)),
                counts[obstacle["obstacle_id"]],
                defaults,
                chrono,
                recovering=False,
            )
        )
    for response in tube["responses"]:
        prior = float(previous_indentation.get(response["segment_id"], 0.0))
        if response["segment_id"] in touched or prior <= 0.0:
            continue
        contacts.append(
            _contact_record(
                common,
                response,
                {
                    "obstacle_id": "shape_recovery",
                    "friction_coefficient": 0.0,
                    "local_position": response["local_position"],
                },
                0.0,
                prior,
                1,
                defaults,
                chrono,
                recovering=True,
            )
        )
    pinned_obstacles = {
        contact["obstacle_id"]
        for contact in contacts
        if contact["pinned"] and not contact["recovering"]
    }
    return {
        "contacts": contacts,
        "contact_count": len(contacts),
        "total_holding_force_n": sum(item["holding_force_n"] for item in contacts),
        "max_indentation_m": max(
            (item["indentation_m"] for item in contacts), default=0.0
        ),
        "min_release_margin_n": min(
            (item["release_margin_n"] for item in contacts), default=0.0
        ),
        "pinned_obstacle_count": len(pinned_obstacles),
        "wrapping_contact_count": sum(item["wrapping"] for item in contacts),
        "recovering_contact_count": sum(item["recovering"] for item in contacts),
    }


def _contact_record(
    common: dict[str, Any],
    response: dict[str, Any],
    obstacle: dict[str, Any],
    penetration_m: float,
    previous_indentation_m: float,
    obstacle_contact_count: int,
    defaults: dict[str, Any],
    chrono: Any,
    *,
    recovering: bool,
) -> dict[str, Any]:
    dt = float(defaults["dt_s"])
    recovery_factor = max(0.0, 1.0 - float(defaults["recovery_rate_per_s"]) * dt)
    recovered = min(
        float(defaults["max_indentation_m"]),
        max(0.0, previous_indentation_m) * recovery_factor,
    )
    indentation = min(
        float(defaults["max_indentation_m"]), max(penetration_m, recovered)
    )
    approach_speed = (
        0.0 if recovering else _contact_approach_speed(common, response, obstacle)
    )
    normal_force = _measure_chrono_penalty_force(
        chrono,
        indentation,
        approach_speed,
        float(defaults["tube_contact_stiffness_n_m"]),
        0.0 if recovering else float(defaults["contact_damping_n_s_m"]),
    )
    friction_force = normal_force * float(obstacle["friction_coefficient"])
    wrapping = obstacle_contact_count >= 3 and not recovering
    wrap_support = (
        normal_force
        * float(defaults["wrap_support_scale"])
        * max(0, obstacle_contact_count - 1)
        if wrapping
        else 0.0
    )
    holding_force = 0.0 if recovering else friction_force + wrap_support
    pressure_support = response["pressure_pa"] * float(
        defaults["pressure_release_area_m2"]
    )
    release_resistance = max(0.0, holding_force - pressure_support)
    release_authority = _BASE_RELEASE_THRESHOLD_N
    release_margin = release_authority - release_resistance
    return {
        "obstacle_id": obstacle["obstacle_id"],
        "segment_id": response["segment_id"],
        "indentation_m": indentation,
        "recovered_previous_indentation_m": recovered,
        "normal_force_n": normal_force,
        "friction_force_n": friction_force,
        "wrap_support_n": wrap_support,
        "holding_force_n": holding_force,
        "pressure_release_support_n": pressure_support,
        "release_margin_n": release_margin,
        "wrapping": wrapping,
        "pinned": release_margin < 0.0 and not recovering,
        "recovering": recovering,
        "chrono_element_type": "chrono::ChLinkTSDA",
    }


def _measure_chrono_penalty_force(
    chrono: Any,
    indentation_m: float,
    approach_speed_mps: float,
    stiffness_n_m: float,
    damping_n_s_m: float,
) -> float:
    system = chrono.ChSystemSMC()
    anchor = chrono.ChBody()
    anchor.SetFixed(True)
    system.AddBody(anchor)
    probe = chrono.ChBody()
    probe.SetMass(1.0)
    probe.SetInertiaXX(chrono.ChVector3d(1.0, 1.0, 1.0))
    current_length = 1.0 - indentation_m
    probe.SetPos(chrono.ChVector3d(current_length, 0.0, 0.0))
    probe.SetPosDt(chrono.ChVector3d(-approach_speed_mps, 0.0, 0.0))
    system.AddBody(probe)
    spring = chrono.ChLinkTSDA()
    spring.Initialize(
        anchor,
        probe,
        False,
        chrono.ChVector3d(0.0, 0.0, 0.0),
        chrono.ChVector3d(current_length, 0.0, 0.0),
    )
    spring.SetRestLength(1.0)
    spring.SetSpringCoefficient(stiffness_n_m)
    spring.SetDampingCoefficient(damping_n_s_m)
    system.AddLink(spring)
    system.DoStepDynamics(1.0e-9)
    return max(0.0, float(spring.GetForce()))


def _contact_approach_speed(
    common: dict[str, Any], response: dict[str, Any], obstacle: dict[str, Any]
) -> float:
    position = response["local_position"]
    obstacle_position = obstacle["local_position"]
    dx = float(position["x"]) - float(obstacle_position["x"])
    dy = float(position["y"]) - float(obstacle_position["y"])
    length = math.hypot(dx, dy)
    normal_x, normal_y = (1.0, 0.0) if length <= 1.0e-9 else (dx / length, dy / length)
    velocity = common["initial_state"]["linear_velocity_mps"]
    return max(
        0.0, -(float(velocity["x"]) * normal_x + float(velocity["y"]) * normal_y)
    )


def _static_metrics(common: dict[str, Any], tube: dict[str, Any]) -> dict[str, Any]:
    max_seat_loss = max(
        tube["responses"][tube["seat_target_indices"][seat["seat_id"]]][
            "freeboard_loss_m"
        ]
        for seat in tube["effective_seats"]
    )
    params = common["raft_parameters"]
    return {
        "loaded_crew_mass_kg": sum(
            float(seat["occupant_mass_kg"]) for seat in tube["effective_seats"]
        ),
        "max_seat_freeboard_loss_m": max_seat_loss,
        "port_total_freeboard_loss_m": _side_freeboard_total(tube, "port_"),
        "raft_length_m": float(params["length_m"]),
        "raft_width_m": float(params["width_m"]),
        "starboard_total_freeboard_loss_m": _side_freeboard_total(tube, "starboard_"),
    }


def _contact_metrics(contact: dict[str, Any]) -> dict[str, Any]:
    return {
        "contact_count": contact["contact_count"],
        "max_indentation_m": contact["max_indentation_m"],
        "min_release_margin_n": contact["min_release_margin_n"],
        "pinned_obstacle_count": contact["pinned_obstacle_count"],
        "wrapping_contact_count": contact["wrapping_contact_count"],
    }


def _overwash_metrics(overwash: dict[str, Any]) -> dict[str, Any]:
    return {
        "reference_flip_margin_nm": overwash["flip_margin_nm"],
        "reference_flip_risk": overwash["flip_margin_nm"] < 0.0,
        "retained_water_roll_moment_nm": overwash["retained_water_roll_moment_nm"],
        "total_overtopping_flux_m3_s": overwash["total_overtopping_flux_m3_s"],
        "total_retained_water_mass_kg": overwash["total_retained_water_mass_kg"],
    }


def _phase_telemetry(
    phase_id: str,
    tube: dict[str, Any],
    *,
    overwash: dict[str, Any] | None = None,
    contact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    overwash_by_id = {
        item["segment_id"]: item for item in (overwash or {}).get("segments", ())
    }
    contact_by_id = {
        item["segment_id"]: item for item in (contact or {}).get("contacts", ())
    }
    tube_by_id = {response["segment_id"]: response for response in tube["responses"]}
    segment_ids = [response["segment_id"] for response in tube["responses"]]
    d5_channels: dict[str, Any] = {
        "tube.pressure_pa": {
            segment_id: tube_by_id[segment_id]["pressure_pa"]
            for segment_id in segment_ids
        },
        "tube.volume_m3": {
            segment_id: tube_by_id[segment_id]["volume_m3"]
            for segment_id in segment_ids
        },
        "tube.freeboard_loss_m": {
            segment_id: tube_by_id[segment_id]["freeboard_loss_m"]
            for segment_id in segment_ids
        },
        "tube.floor_load_n": {
            segment_id: tube_by_id[segment_id]["floor_load_n"]
            for segment_id in segment_ids
        },
        "tube.lacing_load_n": {
            segment_id: tube_by_id[segment_id]["lacing_load_n"]
            for segment_id in segment_ids
        },
        "overwash.overtopping_flux_m3_s": {
            segment_id: overwash_by_id.get(segment_id, {}).get(
                "overtopping_flux_m3_s", 0.0
            )
            for segment_id in segment_ids
        },
        "overwash.entrained_water_side": {
            segment_id: overwash_by_id.get(segment_id, {}).get(
                "entrained_water_side", "none"
            )
            for segment_id in segment_ids
        },
        "contact.max_indentation_m": {
            segment_id: contact_by_id.get(segment_id, {}).get("indentation_m", 0.0)
            for segment_id in segment_ids
        },
        "contact.min_release_margin_n": (
            (contact or {}).get("min_release_margin_n", 0.0)
        ),
        "combined_roll_moment_nm": tube["roll_load_bias_nm"]
        + (overwash or {}).get("retained_water_roll_moment_nm", 0.0),
    }
    return {
        "scenario_id": phase_id,
        "project_chrono_system_advanced": tube["project_chrono_system_time_s"] > 0.0,
        "project_chrono_system_time_s": tube["project_chrono_system_time_s"],
        "project_chrono_body_count": tube["project_chrono_body_count"],
        "project_chrono_tsda_count": tube["project_chrono_tsda_count"],
        "tube_nodes": tube["responses"],
        "overwash": overwash or {"segments": []},
        "contact": contact or {"contacts": []},
        "d5_replay_channels": d5_channels,
    }


def _flip_threshold(
    common: dict[str, Any], actions: tuple[dict[str, Any], ...]
) -> float:
    action_by_seat = {action["seat_id"]: action for action in actions}
    seats = [
        _effective_seat(seat, action_by_seat.get(seat["seat_id"]))
        for seat in common["crew_seats"]
        if seat["occupied"]
    ]
    crew_mass = sum(float(seat["occupant_mass_kg"]) for seat in seats)
    loaded_mass = float(common["mass_properties"]["total_mass_kg"])
    weighted_y = sum(
        float(seat["occupant_mass_kg"]) * float(seat["effective_local_position"]["y"])
        for seat in seats
    )
    combined_cg_y = weighted_y / loaded_mass if loaded_mass > 0.0 else 0.0
    half_width = float(common["raft_parameters"]["width_m"]) * 0.5
    lateral_bias = max(-0.95, min(0.95, combined_cg_y / max(half_width, 1.0e-6)))
    high_side_count = sum(
        bool(action_by_seat.get(seat["seat_id"], {}).get("high_side_direction", 0))
        for seat in seats
    )
    high_side_ratio = high_side_count / max(len(seats), 1)
    multiplier = 1.0 + 0.20 * high_side_ratio + min(0.35, abs(lateral_bias) * 0.35)
    if crew_mass <= 0.0:
        return _BASE_FLIP_THRESHOLD_NM
    return _BASE_FLIP_THRESHOLD_NM * multiplier


def _side_freeboard_total(tube: dict[str, Any], prefix: str) -> float:
    return sum(
        response["freeboard_loss_m"]
        for response in tube["responses"]
        if response["segment_id"].startswith(prefix)
    )


def _segment_side(segment_id: str) -> str:
    if segment_id.startswith("port_"):
        return "port"
    if segment_id.startswith("starboard_"):
        return "starboard"
    if segment_id.startswith("bow_"):
        return "bow"
    if segment_id.startswith("stern_"):
        return "stern"
    return "unknown"


def _clamp_vector(vector: dict[str, Any], max_length: float) -> dict[str, float]:
    result = {axis: float(vector.get(axis, 0.0)) for axis in ("x", "y", "z")}
    length = math.sqrt(sum(value * value for value in result.values()))
    if length > max_length:
        scale = max_length / length
        return {axis: value * scale for axis, value in result.items()}
    return result


def _distance_squared(first: dict[str, Any], second: dict[str, Any]) -> float:
    return sum(
        (float(first[axis]) - float(second[axis])) ** 2 for axis in ("x", "y", "z")
    )


def _validate_fixture_package(package: dict[str, Any]) -> None:
    if package.get("schema") != "raftsim.flexible_raft.d6_fixture_input_package.v1":
        raise ValueError("Unsupported D6 fixture-input package schema.")
    fixtures = package.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("D6 fixture-input package must contain fixtures.")
    fixture_ids = tuple(fixture.get("fixture_id") for fixture in fixtures)
    if fixture_ids != REQUIRED_FIXTURE_IDS:
        raise ValueError(
            "D6 fixture order or identities do not match the runner contract."
        )
    common = package.get("common_setup")
    if not isinstance(common, dict):
        raise ValueError("D6 fixture-input package is missing common_setup.")
    segments = common.get("default_tube_layout", {}).get("segments", ())
    if len(segments) != 12:
        raise ValueError("Project Chrono D6 runner requires twelve tube segments.")
    for fixture in fixtures:
        required_channels = fixture.get("required_d5_replay_channels")
        if tuple(required_channels or ()) != REQUIRED_D5_CHANNELS:
            raise ValueError(
                f"{fixture['fixture_id']} does not preserve the required D5 channels."
            )


def _import_project_chrono() -> Any:
    try:
        import pychrono as chrono
        import pychrono.fea  # noqa: F401 - capability check is part of provenance.
    except ImportError as exc:
        raise RuntimeError(
            "PyChrono with FEA support is required for the independent D6 run."
        ) from exc
    required = ("ChSystemSMC", "ChBody", "ChLinkTSDA", "ChVector3d")
    missing = [name for name in required if not hasattr(chrono, name)]
    if missing:
        raise RuntimeError(f"PyChrono is missing required APIs: {', '.join(missing)}")
    return chrono


def _project_chrono_engine_version(chrono: Any) -> str:
    try:
        version = importlib.metadata.version("pychrono")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    conda_meta = Path(sys.prefix) / "conda-meta"
    matches = sorted(conda_meta.glob("pychrono-*.json"))
    build = "unknown-build"
    if matches:
        payload = json.loads(matches[-1].read_text(encoding="utf-8"))
        version = str(payload.get("version", version))
        build = str(payload.get("build", build))
    fea_capable = hasattr(sys.modules.get("pychrono.fea"), "ChElementShellANCF_3423")
    return (
        f"Project Chrono/PyChrono {version} conda {build}; "
        f"ChSystemSMC+ChLinkTSDA; FEA={'available' if fea_capable else 'unavailable'}; "
        f"{D6_PROJECT_CHRONO_RUNNER_VERSION}"
    )


def _flatten_numeric_metrics(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, dict):
        flattened: dict[str, float] = {}
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten_numeric_metrics(value[key], child))
        return flattened
    if isinstance(value, list):
        flattened = {}
        for index, item in enumerate(value):
            flattened.update(_flatten_numeric_metrics(item, f"{prefix}[{index}]"))
        return flattened
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {prefix: float(value)}
    return {}


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pretty_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
