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
D6_COMPARISON_REPORT_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_comparison_report.json"
)
D6_MEASUREMENT_MANIFEST_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_measurement_manifest.json"
)
D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_measured_results_template.json"
)
D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_fixture_input_package.json"
)
D6_BEHAVIORAL_SUITE_SCHEMA = "raftsim.flexible_raft.d6_behavioral_validation_suite.v1"
D6_COMPARISON_REPORT_SCHEMA = "raftsim.flexible_raft.d6_reference_comparison_report.v1"
D6_MEASUREMENT_MANIFEST_SCHEMA = "raftsim.flexible_raft.d6_measurement_manifest.v1"
D6_MEASURED_RESULTS_TEMPLATE_SCHEMA = "raftsim.flexible_raft.d6_measured_results_template.v1"
D6_FIXTURE_INPUT_PACKAGE_SCHEMA = "raftsim.flexible_raft.d6_fixture_input_package.v1"
D6_METRIC_ABSOLUTE_TOLERANCE = 1.0e-6
D6_METRIC_RELATIVE_TOLERANCE = 0.05

REQUIRED_D6_FIXTURE_IDS = (
    "static_seat_load_sag",
    "traveling_crew_shift",
    "rock_pinch_wrap",
    "upstream_tube_overwash_flip",
    "timed_high_side_save",
    "post_contact_recovery",
    "pressure_flow_sweeps",
)

D6_TARGET_POLICIES = {
    "project_chrono_or_reviewed_compliant_model": {
        "comparison_mode": "bounded_numeric_equivalence",
        "metric_deltas_are_failures": True,
        "description": (
            "Project Chrono or another reviewed compliant model must match the "
            "Python D1-D5 reference metrics within the recorded tolerance band."
        ),
    },
    "unreal_chaos_rigid_baseline": {
        "comparison_mode": "baseline_delta_recording",
        "metric_deltas_are_failures": False,
        "description": (
            "Unreal Chaos rigid-body output is a same-fixture baseline. It must "
            "be measured and provenance-recorded, but local tube-compliance "
            "deltas are expected and are not treated as equivalence failures."
        ),
    },
}

_REQUIRED_MEASUREMENT_PROVENANCE_FIELDS = ("source_report", "telemetry_sha256")


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


def build_flexible_raft_d6_comparison_report(
    measured_results: dict[str, Any] | None = None,
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Compare D6 Python fixture metrics against measured engine outputs.

    The committed default report intentionally contains no measured engine
    payloads. It records the exact shape that Project Chrono/reviewed-compliant
    and Unreal Chaos results must satisfy before D6 can be promoted.
    """

    suite = build_flexible_raft_d6_behavioral_suite(parameters)
    measured_by_target = measured_results or {}
    fixture_reports = []
    missing_target_count = 0
    failed_target_count = 0

    for fixture in suite["fixtures"]:
        target_reports = []
        for target in fixture["comparison_targets"]:
            report = _compare_d6_target_fixture(
                fixture,
                target["target_id"],
                measured_by_target.get(target["target_id"], {}).get(fixture["fixture_id"]),
            )
            if report["status"] == "missing_measured_result":
                missing_target_count += 1
            if not report["passed"]:
                failed_target_count += 1
            target_reports.append(report)

        fixture_reports.append(
            {
                "fixture_id": fixture["fixture_id"],
                "objective": fixture["objective"],
                "target_count": len(target_reports),
                "passed": all(target["passed"] for target in target_reports),
                "targets": target_reports,
            }
        )

    all_measurements_present = missing_target_count == 0
    comparison_passed = all_measurements_present and failed_target_count == 0
    if missing_target_count:
        status = "blocked_pending_measured_engine_results"
    elif comparison_passed:
        status = "measured_comparisons_passed_manual_promotion_required"
    else:
        status = "measured_comparisons_failed"

    return {
        "schema": D6_COMPARISON_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "source_suite_schema": suite["schema"],
        "source_suite_path": D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
        "status": status,
        "d6_complete": False,
        "production_promoted": False,
        "all_measurements_present": all_measurements_present,
        "comparison_passed": comparison_passed,
        "missing_target_count": missing_target_count,
        "failed_target_count": failed_target_count,
        "metric_tolerance": {
            "absolute": D6_METRIC_ABSOLUTE_TOLERANCE,
            "relative": D6_METRIC_RELATIVE_TOLERANCE,
        },
        "measured_result_contract": {
            "shape": {
                "<target_id>": {
                    "<fixture_id>": {
                        "source_report": "path or URI for the reviewed run output",
                        "telemetry_sha256": "sha256 of the replay/telemetry payload",
                        "engine_version": "engine build or package version",
                        "metrics": {"<metric_name>": "numeric metric tree"},
                    }
                }
            },
            "required_targets": list(D6_TARGET_POLICIES),
            "required_provenance_fields": list(_REQUIRED_MEASUREMENT_PROVENANCE_FIELDS),
        },
        "target_policies": D6_TARGET_POLICIES,
        "fixtures": fixture_reports,
        "promotion_gate": {
            "may_mark_d6_complete": comparison_passed,
            "may_drive_runtime_gameplay": False,
            "manual_review_required": True,
            "reason": (
                "D6 remains incomplete in the committed artifact until measured "
                "engine outputs are attached, source-reviewed, and this report is "
                "regenerated with every required fixture passing or recorded."
            ),
        },
    }


def write_flexible_raft_d6_comparison_report(repo_root: Path) -> Path:
    """Write the committed pending D6 measured-result comparison report."""

    payload = build_flexible_raft_d6_comparison_report()
    path = repo_root / D6_COMPARISON_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_flexible_raft_d6_measurement_manifest(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the external-engine measurement manifest for D6 fixtures."""

    suite = build_flexible_raft_d6_behavioral_suite(parameters)
    comparison_report = build_flexible_raft_d6_comparison_report(parameters=parameters)
    tasks = []
    for fixture in suite["fixtures"]:
        metric_paths = sorted(_flatten_numeric_metrics(fixture["python_reference_metrics"]))
        for target in fixture["comparison_targets"]:
            target_id = target["target_id"]
            tasks.append(
                {
                    "task_id": f"{target_id}__{fixture['fixture_id']}",
                    "target_id": target_id,
                    "fixture_id": fixture["fixture_id"],
                    "comparison_mode": D6_TARGET_POLICIES[target_id]["comparison_mode"],
                    "metric_deltas_are_failures": D6_TARGET_POLICIES[target_id][
                        "metric_deltas_are_failures"
                    ],
                    "status": "pending_measured_engine_run",
                    "source_fixture_objective": fixture["objective"],
                    "required_metric_paths": metric_paths,
                    "required_metric_count": len(metric_paths),
                    "required_d5_replay_channels": fixture["d5_replay_channels_required"],
                    "required_provenance_fields": list(
                        _REQUIRED_MEASUREMENT_PROVENANCE_FIELDS
                    ),
                    "expected_result_template_path": (
                        f"physics/data/calibration/d6_measurements/{target_id}/"
                        f"{fixture['fixture_id']}.json"
                    ),
                    "adapter_contract": _d6_target_adapter_contract(target_id),
                    "can_promote_fixture": False,
                }
            )

    return {
        "schema": D6_MEASUREMENT_MANIFEST_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "measurement_manifest_ready_engine_runs_pending",
        "d6_complete": False,
        "production_promoted": False,
        "source_suite_path": D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
        "source_comparison_report_path": D6_COMPARISON_REPORT_RELATIVE_PATH,
        "fixture_input_package_path": D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
        "measured_results_template_path": D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
        "fixture_count": suite["fixture_count"],
        "target_count": len(D6_TARGET_POLICIES),
        "measurement_task_count": len(tasks),
        "required_fixture_ids": list(REQUIRED_D6_FIXTURE_IDS),
        "required_targets": list(D6_TARGET_POLICIES),
        "metric_tolerance": comparison_report["metric_tolerance"],
        "tasks": tasks,
        "summary": {
            "pending_measurement_task_count": len(tasks),
            "required_compliant_reference_task_count": sum(
                task["target_id"] == "project_chrono_or_reviewed_compliant_model"
                for task in tasks
            ),
            "required_chaos_baseline_task_count": sum(
                task["target_id"] == "unreal_chaos_rigid_baseline"
                for task in tasks
            ),
            "can_regenerate_comparison_report_after_template_is_filled": True,
        },
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "next_required_actions": [
                "Run or import every listed target/fixture task from a reviewed compliant model and Unreal Chaos.",
                "Fill the measured-results template with source_report, telemetry_sha256, engine_version, and numeric metrics for every task.",
                "Regenerate the D6 comparison report from the completed measured-results payload.",
                "Require manual review before D6 can enable scoring-critical flexible-raft outcomes.",
            ],
        },
    }


def write_flexible_raft_d6_measurement_manifest(repo_root: Path) -> Path:
    payload = build_flexible_raft_d6_measurement_manifest()
    path = repo_root / D6_MEASUREMENT_MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_flexible_raft_d6_measured_results_template(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build a fillable measured-results payload template for D6."""

    suite = build_flexible_raft_d6_behavioral_suite(parameters)
    manifest = build_flexible_raft_d6_measurement_manifest(parameters)
    measured_results: dict[str, dict[str, Any]] = {
        target_id: {} for target_id in D6_TARGET_POLICIES
    }
    fixture_lookup = {fixture["fixture_id"]: fixture for fixture in suite["fixtures"]}
    for task in manifest["tasks"]:
        fixture = fixture_lookup[task["fixture_id"]]
        metric_paths = task["required_metric_paths"]
        measured_results[task["target_id"]][task["fixture_id"]] = {
            "status": "not_measured",
            "source_report": "",
            "telemetry_sha256": "",
            "engine_version": "",
            "fixture_id": task["fixture_id"],
            "target_id": task["target_id"],
            "metric_paths_required": metric_paths,
            "metrics": _null_metric_tree_from_reference(
                fixture["python_reference_metrics"]
            ),
        }

    return {
        "schema": D6_MEASURED_RESULTS_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "measured_results_template_empty",
        "d6_complete": False,
        "production_promoted": False,
        "source_suite_path": D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
        "source_measurement_manifest_path": D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
        "source_fixture_input_package_path": D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
        "target_count": len(measured_results),
        "fixture_count": suite["fixture_count"],
        "required_result_count": manifest["measurement_task_count"],
        "filled_result_count": 0,
        "measured_results": measured_results,
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "reason": (
                "This committed artifact is intentionally empty. It becomes input "
                "to build_flexible_raft_d6_comparison_report only after every "
                "source report, telemetry hash, engine version, and metric tree is filled."
            ),
        },
    }


def write_flexible_raft_d6_measured_results_template(repo_root: Path) -> Path:
    payload = build_flexible_raft_d6_measured_results_template()
    path = repo_root / D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_flexible_raft_d6_fixture_input_package(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build deterministic fixture inputs for external D6 engine adapters."""

    params = parameters or RaftParameters2_5D(passenger_count=4)
    context = _build_context(params)
    suite = build_flexible_raft_d6_behavioral_suite(params)
    manifest = build_flexible_raft_d6_measurement_manifest(params)
    fixtures = [
        _d6_fixture_input_payload(context, fixture, index)
        for index, fixture in enumerate(suite["fixtures"])
    ]
    return {
        "schema": D6_FIXTURE_INPUT_PACKAGE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "fixture_inputs_ready_engine_adapter_runs_pending",
        "d6_complete": False,
        "production_promoted": False,
        "source_suite_path": D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
        "source_measurement_manifest_path": D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
        "source_measured_results_template_path": D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
        "fixture_count": len(fixtures),
        "measurement_task_count": manifest["measurement_task_count"],
        "required_fixture_ids": list(REQUIRED_D6_FIXTURE_IDS),
        "required_targets": list(D6_TARGET_POLICIES),
        "common_setup": _d6_common_setup_payload(context),
        "fixtures": fixtures,
        "adapter_contract": {
            "input_package_path": D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
            "result_template_path": D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
            "comparison_report_path": D6_COMPARISON_REPORT_RELATIVE_PATH,
            "adapter_must_not_substitute_python_reference": True,
            "required_output_fields": [
                "source_report",
                "telemetry_sha256",
                "engine_version",
                "metrics",
            ],
            "required_metric_tolerance": {
                "absolute": D6_METRIC_ABSOLUTE_TOLERANCE,
                "relative": D6_METRIC_RELATIVE_TOLERANCE,
            },
        },
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "reason": (
                "This package only records deterministic fixture inputs. D6 remains "
                "incomplete until measured compliant-reference and Unreal Chaos "
                "outputs populate the measured-results template and pass review."
            ),
        },
    }


def write_flexible_raft_d6_fixture_input_package(repo_root: Path) -> Path:
    payload = build_flexible_raft_d6_fixture_input_package()
    path = repo_root / D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _d6_target_adapter_contract(target_id: str) -> dict[str, Any]:
    if target_id == "project_chrono_or_reviewed_compliant_model":
        return {
            "adapter_id": "chrono_or_reviewed_compliant_d6_fixture_runner",
            "expected_runner": (
                "Project Chrono or reviewed offline compliant model reproducing "
                "the D1-D5 tube, overwash, contact, and recovery fixture semantics."
            ),
            "required_output": "bounded numeric-equivalence metrics plus telemetry hash",
            "may_substitute_with_synthetic_python_reference": False,
        }
    if target_id == "unreal_chaos_rigid_baseline":
        return {
            "adapter_id": "unreal_chaos_rigid_d6_fixture_runner",
            "expected_runner": (
                "Unreal Chaos rigid-body fixture pass using the same initial "
                "raft state, crew actions, obstacle definitions, and flow probes."
            ),
            "required_output": "baseline delta metrics plus telemetry hash",
            "may_substitute_with_synthetic_python_reference": False,
        }
    raise ValueError(f"Unsupported D6 target id: {target_id}")


def _d6_common_setup_payload(context: dict[str, Any]) -> dict[str, Any]:
    params = context["params"]
    properties = context["properties"]
    default_layout = build_default_compliant_tube_layout_d1(params)
    return {
        "coordinate_frame": {
            "local_x": "raft longitudinal axis, positive toward bow",
            "local_y": "raft lateral axis, positive starboard/river-right in fixture space",
            "local_z": "up",
        },
        "fixed_step_s": 1.0 / 30.0,
        "raft_parameters": params.to_json_dict(),
        "initial_state": _state_payload(context["state"]),
        "mass_properties": {
            "total_mass_kg": properties.total_mass_kg,
            "inverse_mass_kg": properties.inverse_mass,
            "inertia_diagonal_kg_m2": _vec3_payload(
                properties.inertia_diagonal_kg_m2
            ),
            "gravity": _vec3_payload(properties.gravity),
            "guide_offset": _vec3_payload(properties.guide_offset),
            "passenger_offsets": [
                _vec3_payload(offset) for offset in properties.passenger_offsets
            ],
            "sample_patch_count": len(properties.sample_patches),
            "sample_patches": [
                _sample_patch_payload(patch)
                for patch in properties.sample_patches
            ],
        },
        "crew_seat_count": len(context["seats"]),
        "crew_seats": [_seat_payload(seat) for seat in context["seats"]],
        "default_tube_layout": {
            "segment_count": len(default_layout),
            "segments": [
                _tube_segment_payload(segment)
                for segment in default_layout
            ],
        },
        "reference_evaluator_defaults": {
            "d3_water_sampler": {
                "input_kind": "synthetic_uniform_water_field",
                "note": "Adapters may replace the field implementation, but must preserve the recorded surface height and velocity vectors per fixture.",
            },
            "d4_rock_contact": {
                "dt_s": 1.0 / 30.0,
                "max_indentation_m": 0.22,
                "tube_contact_stiffness_n_m": 30_000.0,
                "contact_damping_n_s_m": 850.0,
                "pressure_release_area_m2": 0.018,
                "recovery_rate_per_s": 2.4,
                "wrap_support_scale": 0.32,
            },
        },
    }


def _d6_fixture_input_payload(
    context: dict[str, Any],
    fixture: dict[str, Any],
    source_index: int,
) -> dict[str, Any]:
    metric_paths = sorted(_flatten_numeric_metrics(fixture["python_reference_metrics"]))
    return {
        "fixture_id": fixture["fixture_id"],
        "source_fixture_index": source_index,
        "objective": fixture["objective"],
        "status": "ready_for_external_engine_adapter_run",
        "can_promote": False,
        "input_contract": _d6_fixture_specific_input(context, fixture["fixture_id"]),
        "required_metric_paths": metric_paths,
        "required_metric_count": len(metric_paths),
        "required_d5_replay_channels": fixture["d5_replay_channels_required"],
        "adapter_targets": [
            _d6_target_fixture_input_payload(target["target_id"], fixture["fixture_id"])
            for target in fixture["comparison_targets"]
        ],
    }


def _d6_fixture_specific_input(
    context: dict[str, Any],
    fixture_id: str,
) -> dict[str, Any]:
    if fixture_id == "static_seat_load_sag":
        return {
            "fixture_kind": "static_occupied_seat_load",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
            ],
            "expected_engine_setup": "Solve the occupied-seat tube deformation from common_setup with no extra crew action.",
        }
    if fixture_id == "traveling_crew_shift":
        return {
            "fixture_kind": "multi_phase_crew_weight_transfer",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
                _crew_phase_payload("port_lean_requested", _port_lean_actions(context)),
                _crew_phase_payload(
                    "starboard_high_side",
                    _starboard_high_side_actions(context),
                ),
            ],
            "expected_engine_setup": "Run each phase from the same common initial state and compare side freeboard deltas.",
        }
    if fixture_id == "rock_pinch_wrap":
        return {
            "fixture_kind": "static_rock_pinch_wrap_contact",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
            ],
            "obstacles": [
                _obstacle_payload(_wrap_obstacle("wrap_starboard_pillow")),
            ],
            "expected_engine_setup": "Apply the recorded local boulder against the neutral compliant tube state.",
        }
    if fixture_id == "upstream_tube_overwash_flip":
        return {
            "fixture_kind": "uniform_flow_overwash_flip_probe",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
            ],
            "water": _water_payload(surface_height_m=0.24, velocity=Vec3(0.0, -3.0, 0.0)),
            "expected_engine_setup": "Sample the uniform upstream flow against depressed upstream tube segments.",
        }
    if fixture_id == "timed_high_side_save":
        return {
            "fixture_kind": "two_phase_overwash_high_side_recovery",
            "phases": [
                _crew_phase_payload("neutral_overwash", ()),
                _crew_phase_payload(
                    "starboard_high_side_with_retained_water_memory",
                    _starboard_high_side_actions(context),
                ),
            ],
            "water": _water_payload(surface_height_m=0.24, velocity=Vec3(0.0, -3.0, 0.0)),
            "previous_retained_volume_by_segment": _neutral_retained_volume_by_segment(
                context
            ),
            "expected_engine_setup": "Run the neutral overwash phase first, then replay the high-side phase with the recorded retained-water memory.",
        }
    if fixture_id == "post_contact_recovery":
        return {
            "fixture_kind": "post_contact_indentation_recovery",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
            ],
            "previous_indentation_by_segment": {
                "starboard_1": 0.08,
                "starboard_2": 0.12,
            },
            "obstacles": [],
            "expected_engine_setup": "Start with recorded prior indentation and no current obstacle contact.",
        }
    if fixture_id == "pressure_flow_sweeps":
        pressures = (14_000.0, 18_000.0, 22_000.0)
        velocities = (1.2, 2.4, 3.6)
        return {
            "fixture_kind": "pressure_flow_parameter_sweep",
            "phases": [
                _crew_phase_payload("neutral_occupied_seats", ()),
            ],
            "nominal_pressure_values_pa": list(pressures),
            "incoming_velocity_values_mps": list(velocities),
            "water_surface_height_m": 0.22,
            "obstacles": [
                _obstacle_payload(_wrap_obstacle("pressure_sweep_wrap")),
            ],
            "sweep_case_count": len(pressures) * len(velocities),
            "sweep_cases": [
                {
                    "case_id": (
                        f"pressure_{int(pressure)}_velocity_{str(velocity).replace('.', 'p')}"
                    ),
                    "nominal_pressure_pa": pressure,
                    "water": _water_payload(
                        surface_height_m=0.22,
                        velocity=Vec3(0.0, -velocity, 0.0),
                    ),
                }
                for pressure in pressures
                for velocity in velocities
            ],
            "expected_engine_setup": "Run every pressure/velocity pair with the same neutral seat state and boulder geometry.",
        }
    raise ValueError(f"Unsupported D6 fixture id: {fixture_id}")


def _d6_target_fixture_input_payload(target_id: str, fixture_id: str) -> dict[str, Any]:
    policy = D6_TARGET_POLICIES[target_id]
    return {
        "target_id": target_id,
        "fixture_id": fixture_id,
        "comparison_mode": policy["comparison_mode"],
        "metric_deltas_are_failures": policy["metric_deltas_are_failures"],
        "adapter_contract": _d6_target_adapter_contract(target_id),
        "expected_result_template_path": (
            f"physics/data/calibration/d6_measurements/{target_id}/"
            f"{fixture_id}.json"
        ),
        "required_provenance_fields": list(_REQUIRED_MEASUREMENT_PROVENANCE_FIELDS),
        "can_promote_fixture": False,
    }


def _crew_phase_payload(
    phase_id: str,
    actions: tuple[CrewAction2_5D, ...],
    *,
    duration_s: float = 1.0 / 30.0,
) -> dict[str, Any]:
    return {
        "phase_id": phase_id,
        "duration_s": duration_s,
        "action_count": len(actions),
        "crew_actions": [_action_payload(action) for action in actions],
    }


def _port_lean_actions(context: dict[str, Any]) -> tuple[CrewAction2_5D, ...]:
    return tuple(
        CrewAction2_5D(seat.seat_id, lean_offset=Vec3(0.0, -1.5, 0.0))
        for seat in context["seats"]
    )


def _starboard_high_side_actions(context: dict[str, Any]) -> tuple[CrewAction2_5D, ...]:
    return tuple(
        CrewAction2_5D(seat.seat_id, high_side_direction=1)
        for seat in context["seats"]
    )


def _neutral_retained_volume_by_segment(context: dict[str, Any]) -> dict[str, float]:
    water = _synthetic_water_field(surface_height_m=0.24, velocity=Vec3(0.0, -3.0, 0.0))
    neutral = evaluate_overwash_flip_d3(_tube(context), water, parameters=context["params"])
    return {
        segment.segment_id: segment.retained_water_volume_m3
        for segment in neutral.segment_overwash
    }


def _wrap_obstacle(obstacle_id: str) -> RockObstacleD4:
    return RockObstacleD4(obstacle_id, Vec3(0.0, 1.0, 0.0), 1.45, 0.82)


def _water_payload(surface_height_m: float, velocity: Vec3) -> dict[str, Any]:
    return {
        "surface_height_m": surface_height_m,
        "velocity_mps": _vec3_payload(velocity),
        "field_kind": "synthetic_uniform",
    }


def _tube_segment_payload(segment: Any) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "local_position": _vec3_payload(segment.local_position),
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


def _state_payload(state: RaftState6DoF) -> dict[str, Any]:
    return {
        "position": _vec3_payload(state.position),
        "orientation": _quaternion_payload(state.orientation),
        "linear_velocity_mps": _vec3_payload(state.linear_velocity),
        "angular_velocity_rad_s": _vec3_payload(state.angular_velocity),
    }


def _seat_payload(seat: Any) -> dict[str, Any]:
    return {
        "seat_id": seat.seat_id,
        "role": seat.role,
        "local_position": _vec3_payload(seat.local_position),
        "occupant_mass_kg": seat.occupant_mass_kg,
        "occupied": seat.occupied,
    }


def _action_payload(action: CrewAction2_5D) -> dict[str, Any]:
    return {
        "seat_id": action.seat_id,
        "lean_offset": _vec3_payload(action.lean_offset),
        "high_side_direction": action.high_side_direction,
        "brace": action.brace,
        "recovery": action.recovery,
        "lean_clamp_expected": action.lean_offset.magnitude > 0.55,
    }


def _sample_patch_payload(patch: Any) -> dict[str, Any]:
    return {
        "kind": patch.kind,
        "local_position": _vec3_payload(patch.local_position),
        "area_m2": patch.area_m2,
        "local_normal": _vec3_payload(patch.local_normal),
    }


def _obstacle_payload(obstacle: RockObstacleD4) -> dict[str, Any]:
    return {
        "obstacle_id": obstacle.obstacle_id,
        "local_position": _vec3_payload(obstacle.local_position),
        "radius_m": obstacle.radius_m,
        "friction_coefficient": obstacle.friction_coefficient,
    }


def _vec3_payload(value: Vec3) -> dict[str, float]:
    return {
        "x": value.x,
        "y": value.y,
        "z": value.z,
    }


def _quaternion_payload(value: Any) -> dict[str, float]:
    return {
        "w": value.w,
        "x": value.x,
        "y": value.y,
        "z": value.z,
    }


def _null_metric_tree_from_reference(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _null_metric_tree_from_reference(value[key])
            for key in sorted(value)
        }
    if isinstance(value, list):
        return [_null_metric_tree_from_reference(item) for item in value]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return None
    return value


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


def _compare_d6_target_fixture(
    fixture: dict[str, Any],
    target_id: str,
    measured_result: dict[str, Any] | None,
) -> dict[str, Any]:
    policy = D6_TARGET_POLICIES[target_id]
    if measured_result is None:
        return {
            "target_id": target_id,
            "comparison_mode": policy["comparison_mode"],
            "status": "missing_measured_result",
            "passed": False,
            "required": True,
            "missing_provenance_fields": list(_REQUIRED_MEASUREMENT_PROVENANCE_FIELDS),
            "metric_summary": {
                "compared_metric_count": 0,
                "failed_metric_count": 0,
                "missing_reference_metric_count": None,
                "extra_measured_metric_count": None,
            },
            "metric_comparisons": [],
        }

    missing_provenance = [
        field for field in _REQUIRED_MEASUREMENT_PROVENANCE_FIELDS if not measured_result.get(field)
    ]
    comparison = _compare_metric_trees(
        fixture["python_reference_metrics"],
        measured_result.get("metrics", {}),
        fail_on_missing_reference_metrics=policy["metric_deltas_are_failures"],
        fail_on_metric_delta=policy["metric_deltas_are_failures"],
    )
    if missing_provenance:
        status = "incomplete_measured_result_provenance"
        passed = False
    elif comparison["compared_metric_count"] == 0:
        status = "no_comparable_numeric_metrics"
        passed = False
    elif policy["metric_deltas_are_failures"] and not comparison["passed"]:
        status = "failed_numeric_equivalence"
        passed = False
    elif policy["metric_deltas_are_failures"]:
        status = "passed_numeric_equivalence"
        passed = True
    else:
        status = "recorded_baseline_delta"
        passed = True

    return {
        "target_id": target_id,
        "comparison_mode": policy["comparison_mode"],
        "status": status,
        "passed": passed,
        "required": True,
        "source_report": measured_result.get("source_report"),
        "telemetry_sha256": measured_result.get("telemetry_sha256"),
        "engine_version": measured_result.get("engine_version"),
        "missing_provenance_fields": missing_provenance,
        "metric_summary": {
            "compared_metric_count": comparison["compared_metric_count"],
            "failed_metric_count": comparison["failed_metric_count"],
            "missing_reference_metric_count": comparison["missing_reference_metric_count"],
            "extra_measured_metric_count": comparison["extra_measured_metric_count"],
        },
        "metric_comparisons": comparison["metric_comparisons"],
        "missing_reference_metrics": comparison["missing_reference_metrics"],
        "extra_measured_metrics": comparison["extra_measured_metrics"],
    }


def _compare_metric_trees(
    reference_metrics: dict[str, Any],
    measured_metrics: dict[str, Any],
    *,
    fail_on_missing_reference_metrics: bool,
    fail_on_metric_delta: bool,
) -> dict[str, Any]:
    reference = _flatten_numeric_metrics(reference_metrics)
    measured = _flatten_numeric_metrics(measured_metrics)
    common_paths = sorted(set(reference) & set(measured))
    missing_reference_metrics = sorted(set(reference) - set(measured))
    extra_measured_metrics = sorted(set(measured) - set(reference))
    metric_comparisons = []
    failed_metric_count = 0

    for path in common_paths:
        reference_value = reference[path]
        measured_value = measured[path]
        abs_delta = abs(measured_value - reference_value)
        tolerance = D6_METRIC_ABSOLUTE_TOLERANCE + (
            D6_METRIC_RELATIVE_TOLERANCE * max(abs(reference_value), abs(measured_value))
        )
        within_tolerance = abs_delta <= tolerance
        if not within_tolerance:
            failed_metric_count += 1
        metric_comparisons.append(
            {
                "path": path,
                "reference_value": reference_value,
                "measured_value": measured_value,
                "abs_delta": abs_delta,
                "tolerance": tolerance,
                "within_tolerance": within_tolerance,
            }
        )

    passed = bool(common_paths)
    if fail_on_metric_delta:
        passed = passed and failed_metric_count == 0
    if fail_on_missing_reference_metrics:
        passed = passed and not missing_reference_metrics

    return {
        "passed": passed,
        "compared_metric_count": len(common_paths),
        "failed_metric_count": failed_metric_count,
        "missing_reference_metric_count": len(missing_reference_metrics),
        "extra_measured_metric_count": len(extra_measured_metrics),
        "missing_reference_metrics": missing_reference_metrics,
        "extra_measured_metrics": extra_measured_metrics,
        "metric_comparisons": metric_comparisons,
    }


def _flatten_numeric_metrics(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, dict):
        flattened: dict[str, float] = {}
        for key in sorted(value):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten_numeric_metrics(value[key], child_prefix))
        return flattened
    if isinstance(value, list):
        flattened = {}
        for index, item in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            flattened.update(_flatten_numeric_metrics(item, child_prefix))
        return flattened
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {prefix: float(value)}
    return {}


def build_d6_replay_channel_probe() -> dict[str, Any]:
    """Return D5 replay metadata used by D6 tests and future engine adapters."""

    replay = build_flexible_raft_d5_fixture()
    return {
        "replay_id": replay["replay_id"],
        "frame_count": replay["frame_count"],
        "frame_hashes": replay["frame_hashes"],
        "replay_sha256": replay["replay_sha256"],
    }
