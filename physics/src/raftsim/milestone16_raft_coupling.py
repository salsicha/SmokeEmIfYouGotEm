"""Milestone 16 raft-coupling validation: raft force comparison on GeoClaw vs C++ water fields.
Raft code stays in the game; the water validation it compares against lives in milestone16."""
from __future__ import annotations

from pathlib import Path
from raftsim.cascading import read_cascading_scenario_package
from raftsim.feature_validation import FeatureValidationResult, build_cascading_raft_validation_cases, summarize_run_outcomes, validate_boil_upwelling_case, validate_cascading_raft_cases, validate_eddy_line_case, validate_hole_case, validate_lateral_wave_case, validate_shallow_shelf_case, validate_standing_wave_case, validate_submerged_rock_case
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties, compare_raft_force_samples
from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.milestone16 import (MILESTONE16_RAFT_FORCE_DELTA_WEIGHT_RATIO_THRESHOLD, MILESTONE16_RAFT_TORQUE_DELTA_INERTIA_RATIO_THRESHOLD, MILESTONE16_RAFT_TRAJECTORY_POSITION_DELTA_M_THRESHOLD, MILESTONE16_RAFT_TRAJECTORY_VELOCITY_DELTA_MPS_THRESHOLD, Milestone16RaftCouplingRecord, Milestone16RaftCouplingReport, _feature_by_role_or_kind, _last_manifest_frame_path, _raft_feature_check_agreement, _read_json)


def run_milestone16_raft_coupling_validation(
    geoclaw_reference_report: str | Path,
    cpp_run_report: str | Path,
) -> Milestone16RaftCouplingReport:
    """Re-run Milestone 16 raft coupling over GeoClaw-derived and C++ fields."""

    geoclaw_report_path = Path(geoclaw_reference_report)
    cpp_report_path = Path(cpp_run_report)
    geoclaw_report = _read_json(geoclaw_report_path)
    cpp_report = _read_json(cpp_report_path)
    geoclaw_by_gate = {str(record["gate_scenario_id"]): record for record in geoclaw_report["records"]}
    records: list[Milestone16RaftCouplingRecord] = []
    for cpp_record in cpp_report["records"]:
        suite = str(cpp_record["suite"])
        if suite not in {"rafting", "cascading"}:
            continue
        gate_id = str(cpp_record["gate_scenario_id"])
        geoclaw_record = geoclaw_by_gate[gate_id]
        if suite == "cascading":
            records.extend(_cascading_raft_coupling_records(geoclaw_record, cpp_record))
        else:
            records.extend(_standalone_rafting_coupling_records(geoclaw_record, cpp_record))

    return Milestone16RaftCouplingReport(
        geoclaw_reference_report=str(geoclaw_report_path),
        cpp_run_report=str(cpp_report_path),
        records=tuple(records),
        notes=(
            "Distinct pin/release closure evidence is tracked separately in the Milestone 18 "
            "pin_release_fixture report; this report only compares raft coupling over GeoClaw-derived and C++ water fields.",
        ),
    )


def _cascading_raft_coupling_records(
    geoclaw_record: dict[str, object],
    cpp_record: dict[str, object],
) -> tuple[Milestone16RaftCouplingRecord, ...]:
    package = read_cascading_scenario_package(Path(str(geoclaw_record["export_dir"])) / "shared_cascading_package")
    reference_frame = _last_manifest_frame_path(Path(str(geoclaw_record["normalized_manifest"])))
    candidate_frame = _last_manifest_frame_path(Path(str(cpp_record["manifest"])))
    reference_water = WaterField2_5D.from_geoclaw_frame_npz(package.scenario, str(reference_frame))
    candidate_water = WaterField2_5D.from_cpp_frame_csv(package.scenario, str(candidate_frame))
    properties = build_default_raft_mass_properties(package.scenario.raft)
    reference_results = {result.feature: result for result in validate_cascading_raft_cases(package, water=reference_water)}
    candidate_results = {result.feature: result for result in validate_cascading_raft_cases(package, water=candidate_water)}
    cases = build_cascading_raft_validation_cases(package, water=reference_water)
    return tuple(
        _raft_coupling_record_from_results(
            geoclaw_record,
            cpp_record,
            case.case_id,
            case.expected_outcomes,
            reference_frame,
            candidate_frame,
            reference_results[case.case_id],
            candidate_results[case.case_id],
            compare_raft_force_samples(reference_water, candidate_water, case.state, properties),
            properties,
        )
        for case in cases
    )


def _standalone_rafting_coupling_records(
    geoclaw_record: dict[str, object],
    cpp_record: dict[str, object],
) -> tuple[Milestone16RaftCouplingRecord, ...]:
    scenario = read_scenario2_5d_package(Path(str(geoclaw_record["export_dir"])) / "shared_scenario")
    reference_frame = _last_manifest_frame_path(Path(str(geoclaw_record["normalized_manifest"])))
    candidate_frame = _last_manifest_frame_path(Path(str(cpp_record["manifest"])))
    reference_water = WaterField2_5D.from_geoclaw_frame_npz(scenario, str(reference_frame))
    candidate_water = WaterField2_5D.from_cpp_frame_csv(scenario, str(candidate_frame))
    properties = build_default_raft_mass_properties(scenario.raft)
    specs = _standalone_raft_case_specs(str(geoclaw_record["gate_scenario_id"]))
    records: list[Milestone16RaftCouplingRecord] = []
    for spec in specs:
        case_id, feature_kind, role, expected_outcomes, validator, z_offset, vertical_velocity = spec
        feature = _feature_by_role_or_kind(scenario, feature_kind, role)
        state = _raft_state_at_feature(reference_water, feature.center[0], feature.center[1], z_offset, vertical_velocity)
        reference_result = validator(reference_water, state, properties)
        candidate_result = validator(candidate_water, state, properties)
        records.append(
            _raft_coupling_record_from_results(
                geoclaw_record,
                cpp_record,
                case_id,
                expected_outcomes,
                reference_frame,
                candidate_frame,
                reference_result,
                candidate_result,
                compare_raft_force_samples(reference_water, candidate_water, state, properties),
                properties,
            )
        )
    return tuple(records)


def _raft_coupling_record_from_results(
    geoclaw_record: dict[str, object],
    cpp_record: dict[str, object],
    case_id: str,
    expected_outcomes: tuple[str, ...],
    reference_frame: Path,
    candidate_frame: Path,
    reference_result: FeatureValidationResult,
    candidate_result: FeatureValidationResult,
    force_comparison,
    properties,
) -> Milestone16RaftCouplingRecord:
    weight = max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    inertia_scale = max(properties.inertia_diagonal_kg_m2.magnitude, 1.0)
    reference_canonical = _canonical_feature_outcome(reference_result)
    candidate_canonical = _canonical_feature_outcome(candidate_result)
    reference_checks = _feature_checks_json(reference_result)
    candidate_checks = _feature_checks_json(candidate_result)
    feature_check_agreement = _raft_feature_check_agreement(reference_checks, candidate_checks)
    notes = _raft_coupling_failure_notes(
        reference_result,
        candidate_result,
        feature_check_agreement,
        reference_canonical == candidate_canonical,
        force_comparison.outcome_match,
        force_comparison.force_delta.magnitude / weight,
        force_comparison.torque_delta.magnitude / inertia_scale,
        force_comparison.trajectory_position_delta,
        force_comparison.trajectory_velocity_delta,
    )
    return Milestone16RaftCouplingRecord(
        gate_scenario_id=str(geoclaw_record["gate_scenario_id"]),
        actual_scenario_id=str(geoclaw_record["actual_scenario_id"]),
        suite=str(geoclaw_record["suite"]),
        flow_band=geoclaw_record.get("flow_band") if isinstance(geoclaw_record.get("flow_band"), str) else None,
        solver_mode=str(cpp_record["solver_mode"]),
        case_id=case_id,
        expected_outcomes=expected_outcomes,
        reference_frame=str(reference_frame),
        candidate_frame=str(candidate_frame),
        reference_outcome=reference_result.outcome,
        candidate_outcome=candidate_result.outcome,
        reference_passed=reference_result.passed,
        candidate_passed=candidate_result.passed,
        feature_check_agreement=feature_check_agreement,
        feature_outcome_match=reference_canonical == candidate_canonical,
        force_envelope_outcome_match=force_comparison.outcome_match,
        force_delta_weight_ratio=force_comparison.force_delta.magnitude / weight,
        torque_delta_inertia_ratio=force_comparison.torque_delta.magnitude / inertia_scale,
        trajectory_position_delta_m=force_comparison.trajectory_position_delta,
        trajectory_velocity_delta_mps=force_comparison.trajectory_velocity_delta,
        reference_checks=reference_checks,
        candidate_checks=candidate_checks,
        notes=notes,
    )


def _raft_coupling_failure_notes(
    reference_result: FeatureValidationResult,
    candidate_result: FeatureValidationResult,
    feature_check_agreement: bool,
    feature_outcome_match: bool,
    force_envelope_outcome_match: bool,
    force_delta_weight_ratio: float,
    torque_delta_inertia_ratio: float,
    trajectory_position_delta: float,
    trajectory_velocity_delta: float,
) -> tuple[str, ...]:
    notes: list[str] = []
    if not feature_check_agreement:
        if not reference_result.passed:
            notes.append("GeoClaw-derived raft feature checks are not passing.")
        if not candidate_result.passed:
            notes.append("C++ raft feature checks are not passing.")
        if reference_result.passed == candidate_result.passed:
            notes.append("GeoClaw-derived and C++ raft feature check failure signatures differ.")
    elif not reference_result.passed:
        notes.append(
            "GeoClaw-derived and C++ raft feature checks fail the same authored expectation; "
            "tracked as non-blocking feature-sanity debt for this agreement gate."
        )
    if not feature_outcome_match:
        notes.append("Canonical feature outcomes differ.")
    if not force_envelope_outcome_match:
        notes.append("Force-envelope outcomes differ.")
    if force_delta_weight_ratio > MILESTONE16_RAFT_FORCE_DELTA_WEIGHT_RATIO_THRESHOLD:
        notes.append("Force delta exceeds the weight-normalized threshold.")
    if torque_delta_inertia_ratio > MILESTONE16_RAFT_TORQUE_DELTA_INERTIA_RATIO_THRESHOLD:
        notes.append("Torque delta exceeds the inertia-normalized threshold.")
    if trajectory_position_delta > MILESTONE16_RAFT_TRAJECTORY_POSITION_DELTA_M_THRESHOLD:
        notes.append("One-step position delta exceeds threshold.")
    if trajectory_velocity_delta > MILESTONE16_RAFT_TRAJECTORY_VELOCITY_DELTA_MPS_THRESHOLD:
        notes.append("One-step velocity delta exceeds threshold.")
    return tuple(notes)


def _standalone_raft_case_specs(gate_scenario_id: str):
    specs = {
        "boulder_garden": (
            (
                "boulder_impacts",
                "rock",
                "boulder_garden",
                ("grounded", "pinned"),
                validate_submerged_rock_case,
                0.45,
                -0.7,
            ),
        ),
        "cascading_wave_train": (
            (
                "wave_train_surf_flush",
                "wave_train",
                "cascading_wave_train",
                ("clear", "stalled", "surfed", "flushed"),
                validate_standing_wave_case,
                0.35,
                -0.2,
            ),
        ),
        "hydraulic_hole_downstream_boil": (
            (
                "hydraulic_hole_surf_flush",
                "hole",
                "hydraulic_hole",
                ("surfed", "flushed", "pinned"),
                validate_hole_case,
                0.35,
                -0.3,
            ),
            (
                "downstream_boil_recovery",
                "boil",
                "downstream_boil",
                ("clear",),
                validate_boil_upwelling_case,
                0.30,
                -0.4,
            ),
        ),
        "lateral_wave": (
            (
                "lateral_wave_side_impulse",
                "lateral",
                "lateral_wave",
                ("clear", "surfed"),
                validate_lateral_wave_case,
                0.35,
                -0.2,
            ),
        ),
        "eddy_line_shear": (
            (
                "eddy_recovery",
                "eddy_line",
                "eddy_line_shear",
                ("clear",),
                validate_eddy_line_case,
                0.35,
                -0.2,
            ),
        ),
        "shallow_shelf": (
            (
                "shallow_shelf_pivot_release",
                "shallow",
                "shallow_shelf",
                ("grounded", "pinned"),
                validate_shallow_shelf_case,
                0.35,
                -0.5,
            ),
        ),
    }
    return specs.get(gate_scenario_id, ())


def _raft_state_at_feature(
    water: WaterField2_5D,
    x: float,
    y: float,
    z_offset: float,
    vertical_velocity: float,
) -> RaftState6DoF:
    sample = water.sample(x, y)
    return RaftState6DoF(
        position=Vec3(x, y, sample.surface_height - z_offset),
        linear_velocity=Vec3(sample.velocity.x, sample.velocity.y, vertical_velocity),
    )


def _canonical_feature_outcome(result: FeatureValidationResult) -> str:
    return summarize_run_outcomes((result,)).dominant_outcome


def _feature_checks_json(result: FeatureValidationResult) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "name": check.name,
            "passed": check.passed,
            "value": check.value,
            "threshold": check.threshold,
            "details": check.details,
        }
        for check in result.checks
    )
