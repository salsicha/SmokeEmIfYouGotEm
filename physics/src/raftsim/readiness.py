"""Python-to-Unreal readiness gate artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal

import numpy as np

from .math3d import Quaternion, Vec3
from .performance import BaselinePerformanceReport
from .profiling import SolverProfileReport
from .raft_coupling2_5d import (
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    sample_total_raft_forces,
    sum_force_contributions,
)
from .real_world import (
    adaptive_solver_parameters,
    default_player_selections,
    generate_real_world_scenario2_5d,
    south_fork_american_section,
)
from .scenario2_5d import (
    FixtureScenario2_5DParameters,
    InitialWaterState2_5D,
    ProceduralScenario2_5DParameters,
    SCENARIO_SCHEMA_VERSION,
    Scenario2_5D,
    ScenarioMetadata2_5D,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)
from .schema_versions import REPLAY_SCHEMA_VERSION
from .telemetry import TelemetryRecorder

READINESS_REPORT_VERSION = "raftsim.python_to_unreal_readiness.v0"
GEOCLAW_READINESS_REPORT_VERSION = "raftsim.geoclaw_to_unreal_readiness.v1"
UNREAL_VISUALIZATION_EXPORT_VERSION = "raftsim.unreal_visualization_export.v0"
PYCLAW_REFERENCE_MIN_DEPTH_M = 0.01

GateStatus = Literal["approved", "blocked"]
CheckStatus = Literal["passed", "failed", "warning"]


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    check_id: str
    title: str
    passed: bool
    status: CheckStatus
    details: str
    artifacts: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReadinessGateDecision:
    status: GateStatus
    approved_for_unreal_production_start: bool
    reason: str
    required_next_actions: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PythonToUnrealReadinessReport:
    gate_version: str
    decision: ReadinessGateDecision
    checks: tuple[ReadinessCheck, ...]
    runtime_choices: dict[str, object]
    accepted_model_limitations: tuple[str, ...]
    risks: tuple[str, ...]
    artifact_manifest: dict[str, object]

    @property
    def passed(self) -> bool:
        return self.decision.approved_for_unreal_production_start and all(check.passed for check in self.checks)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "gate_version": self.gate_version,
            "passed": self.passed,
            "decision": self.decision.to_json_dict(),
            "checks": [check.to_json_dict() for check in self.checks],
            "runtime_choices": self.runtime_choices,
            "accepted_model_limitations": list(self.accepted_model_limitations),
            "risks": list(self.risks),
            "artifact_manifest": self.artifact_manifest,
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path

    def write_markdown(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Python-To-Unreal Readiness Report",
            "",
            f"Gate version: `{self.gate_version}`",
            "",
            f"Decision: **{self.decision.status.upper()}**",
            "",
            self.decision.reason,
            "",
            "## Checks",
            "",
            "| Check | Status | Details |",
            "| --- | --- | --- |",
        ]
        for check in self.checks:
            status = "PASS" if check.passed else check.status.upper()
            lines.append(f"| {check.title} | {status} | {check.details} |")
        lines.extend(["", "## Runtime Choices", ""])
        for key, value in self.runtime_choices.items():
            lines.append(f"- `{key}`: {value}")
        lines.extend(["", "## Required Next Actions", ""])
        for action in self.decision.required_next_actions:
            lines.append(f"- {action}")
        lines.extend(["", "## Accepted Model Limitations", ""])
        for limitation in self.accepted_model_limitations:
            lines.append(f"- {limitation}")
        lines.extend(["", "## Risks", ""])
        for risk in self.risks:
            lines.append(f"- {risk}")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def build_milestone10_scenario_suite() -> tuple[Scenario2_5D, ...]:
    """Return the scenario suite audited at the Python-to-Unreal readiness gate."""

    real_world_scenarios = tuple(
        generate_real_world_scenario2_5d(selection, nx=32, ny=16, duration=0.05)
        for selection in default_player_selections()
    )
    return (
        generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture="flat_pool", seed=100, nx=24, ny=12, duration=0.05)
        ),
        generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture="uniform_channel", seed=101, nx=24, ny=12, duration=0.05)
        ),
        generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture="bed_step", seed=102, nx=24, ny=12, duration=0.05)
        ),
        make_pyclaw_reference_compatible(
            generate_procedural_scenario2_5d(
                ProceduralScenario2_5DParameters(seed=103, nx=32, ny=18, feature_count=9, duration=0.05)
            )
        ),
        *real_world_scenarios,
    )


def make_pyclaw_reference_compatible(
    scenario: Scenario2_5D,
    *,
    minimum_depth_m: float = PYCLAW_REFERENCE_MIN_DEPTH_M,
) -> Scenario2_5D:
    """Return a reference copy with a shallow shelf instead of exact dry cells."""

    if minimum_depth_m < 0.0:
        raise ValueError("minimum_depth_m must be non-negative.")
    if minimum_depth_m == 0.0:
        return scenario
    depth = np.maximum(scenario.initial_state.depth, minimum_depth_m)
    shallow_mask = scenario.initial_state.depth <= minimum_depth_m
    u = np.where(shallow_mask, 0.0, scenario.initial_state.u)
    v = np.where(shallow_mask, 0.0, scenario.initial_state.v)
    state = InitialWaterState2_5D.from_depth_velocity(scenario.bed, depth, u, v)
    metadata = _metadata_with_provenance(
        scenario.metadata,
        {
            "pyclaw_reference_min_depth_m": minimum_depth_m,
            "pyclaw_reference_transform": "exact dry cells converted to shallow reference shelf",
        },
    )
    return replace(scenario, metadata=metadata, initial_state=state)


def build_adaptive_flow_validation() -> dict[str, object]:
    """Validate low/median/high flow-to-parameter mapping for the first real-world section."""

    rows = []
    for selection in default_player_selections():
        preset = adaptive_solver_parameters(selection)
        rows.append(
            {
                "flow_band": selection.flow_band,
                "season": selection.season,
                "difficulty": selection.difficulty,
                "boundary_inflow_m3s": preset.boundary_inflow_m3s,
                "initial_depth_m": preset.initial_depth_m,
                "downstream_velocity_mps": preset.downstream_velocity_mps,
                "roughness_manning_n": preset.roughness_manning_n,
                "wave_train_strength": preset.wave_train_strength,
                "eddy_line_shear": preset.eddy_line_shear,
                "hole_retention_strength": preset.hole_retention_strength,
                "confidence_score": preset.confidence_score,
            }
        )
    inflows = [float(row["boundary_inflow_m3s"]) for row in rows]
    wave_strengths = [float(row["wave_train_strength"]) for row in rows]
    shear = [float(row["eddy_line_shear"]) for row in rows]
    passed = inflows == sorted(inflows) and wave_strengths == sorted(wave_strengths) and shear == sorted(shear)
    return {
        "validation_version": "raftsim.adaptive_flow_validation.v0",
        "river_id": south_fork_american_section().river_id,
        "section_id": south_fork_american_section().section_id,
        "passed": passed,
        "checks": {
            "inflow_monotonic": inflows == sorted(inflows),
            "wave_train_strength_monotonic": wave_strengths == sorted(wave_strengths),
            "eddy_line_shear_monotonic": shear == sorted(shear),
        },
        "flow_presets": rows,
    }


def write_unreal_visualization_exports(
    output_dir: str | Path,
    *,
    scenario: Scenario2_5D | None = None,
    frame_count: int = 5,
) -> dict[str, object]:
    """Write representative replay and force telemetry for Unreal visualization."""

    if frame_count < 1:
        raise ValueError("frame_count must be at least 1.")
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    scenario = scenario or generate_real_world_scenario2_5d()
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    state = RaftState6DoF(
        position=Vec3(center_x, center_y, surface - 0.35),
        orientation=Quaternion.identity(),
        linear_velocity=Vec3(0.8, 0.0, 0.0),
    )
    recorder = TelemetryRecorder()
    replay_frames: list[dict[str, object]] = []
    for step_index in range(frame_count):
        time = step_index * scenario.fixed_dt
        frame = recorder.begin_frame(step_index=step_index, time=time, dt=scenario.fixed_dt)
        contributions = sample_total_raft_forces(state, properties, water)
        total_force, total_torque = sum_force_contributions(contributions)
        for contribution in contributions:
            frame.record_force(
                contribution.name,
                contribution.force,
                torque=contribution.torque,
                application_point=contribution.application_point,
                metadata=contribution.metadata,
            )
        recorder.end_frame()
        replay_frames.append(
            {
                "step_index": step_index,
                "time": time,
                "raft_state": {
                    "position": _vec_json(state.position),
                    "orientation": _quat_json(state.orientation),
                    "linear_velocity": _vec_json(state.linear_velocity),
                    "angular_velocity": _vec_json(state.angular_velocity),
                },
                "outcome": "floating",
                "force_telemetry_file": "telemetry_forces.csv",
            }
        )
        state = state.advance(
            scenario.fixed_dt,
            linear_acceleration=total_force / max(properties.total_mass_kg, 1.0),
            angular_acceleration=Vec3(
                total_torque.x / max(properties.inertia_diagonal_kg_m2.x, 1.0),
                total_torque.y / max(properties.inertia_diagonal_kg_m2.y, 1.0),
                total_torque.z / max(properties.inertia_diagonal_kg_m2.z, 1.0),
            ),
        )
    telemetry_path = recorder.write_force_csv(output_root / "telemetry_forces.csv")
    replay = {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_schema_version": SCENARIO_SCHEMA_VERSION,
        "fixed_dt": scenario.fixed_dt,
        "parameter_profile": {
            "river_id": scenario.metadata.river_id,
            "section_id": scenario.metadata.section_id,
            "season_preset": scenario.metadata.season_preset,
            "flow_band": scenario.metadata.flow_band,
            "difficulty_preset": scenario.metadata.difficulty_preset,
        },
        "frames": replay_frames,
    }
    replay_path = output_root / "replay.json"
    replay_path.write_text(json.dumps(replay, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "export_version": UNREAL_VISUALIZATION_EXPORT_VERSION,
        "scenario_id": scenario.metadata.scenario_id,
        "replay": replay_path.name,
        "force_telemetry": telemetry_path.name,
        "frame_count": frame_count,
        "force_row_count": len(recorder.force_rows()),
    }
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def build_readiness_report(
    checks: tuple[ReadinessCheck, ...],
    *,
    artifact_manifest: dict[str, object],
    accepted_model_limitations: tuple[str, ...] | None = None,
    risks: tuple[str, ...] | None = None,
) -> PythonToUnrealReadinessReport:
    """Build the final gate decision from completed readiness checks."""

    blocking_failures = tuple(check for check in checks if not check.passed and check.status == "failed")
    approved = not blocking_failures
    if approved:
        decision = ReadinessGateDecision(
            status="approved",
            approved_for_unreal_production_start=True,
            reason="Python modeling, profiling, telemetry/replay export, and real-world preproduction package checks passed.",
            required_next_actions=(
                "Create the production Unreal project and keep telemetry playback as the first integration target.",
                "Re-check latest UE5 rendering, VR, platform, and geospatial plugin support before locking project settings.",
            ),
        )
    else:
        decision = ReadinessGateDecision(
            status="blocked",
            approved_for_unreal_production_start=False,
            reason="The readiness audit completed, but one or more blocking checks failed; do not start the production Unreal project yet.",
            required_next_actions=tuple(
                f"Resolve {check.check_id}: {check.details}" for check in blocking_failures
            ),
        )
    return PythonToUnrealReadinessReport(
        gate_version=READINESS_REPORT_VERSION,
        decision=decision,
        checks=checks,
        runtime_choices={
            "authoritative_water_candidate": "custom C++ reduced shallow-water / height-field solver",
            "reference_solver": "PyClaw, with shallow reference shelf for exact dry-cell scenarios until wet/dry reference handling is improved",
            "raft_and_contact_candidate": "Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail",
            "unreal_integration_order": "replay/telemetry playback first, then live custom water, then Chrono/custom raft coupling",
            "chrono_fsi": "optional research path only, not a baseline runtime dependency",
        },
        accepted_model_limitations=accepted_model_limitations
        or (
            "2.5D shallow-water/height-field flow is the accepted runtime model for the first Unreal bridge; full 3D CFD is out of scope.",
            "PyClaw reference exports use a shallow shelf for exact dry cells to avoid Roe-solver singularities.",
            "The first real-world corridor remains a preproduction seed package; heavy lidar, imagery, guide references, and field media are not vendored.",
            "Real-world C++ matching must pass threshold reports before final river-content production.",
        ),
        risks=risks
        or (
            "Real-world hydraulic matching may need additional C++ solver terms or calibrated thresholds.",
            "Runtime budgets are measured on local smoke scenarios and need target hardware confirmation.",
            "Geospatial source licensing and attribution must be re-checked when pulling production data.",
            "Chrono integration is not yet verified inside Unreal or VR frame scheduling.",
        ),
        artifact_manifest=artifact_manifest,
    )


def build_geoclaw_readiness_report(
    *,
    geoclaw_reference_summary: dict[str, object],
    cpp_summary: dict[str, object],
    comparison_summary: dict[str, object],
    tuning_summary: dict[str, object],
    raft_coupling_summary: dict[str, object],
    artifact_manifest: dict[str, object],
) -> PythonToUnrealReadinessReport:
    """Build the GeoClaw replacement readiness gate for live Unreal water."""

    normalized_mode = str(geoclaw_reference_summary.get("normalized_mode", "unknown"))
    checks = (
        check_from_summary(
            "geoclaw_reference_exports",
            "GeoClaw Reference Exports",
            bool(geoclaw_reference_summary.get("exports_passed")),
            f"{geoclaw_reference_summary.get('export_count', 0)} GeoClaw export packages generated.",
            ("geoclaw_reference_summary.json",),
        ),
        check_from_summary(
            "geoclaw_fixed_grid_outputs",
            "GeoClaw Fixed-Grid Outputs",
            bool(geoclaw_reference_summary.get("has_full_geoclaw_frames")),
            f"Normalized output mode is {normalized_mode}; full GeoClaw fgout frames are required for approval.",
            ("geoclaw_reference_summary.json",),
        ),
        check_from_summary(
            "custom_cpp_solver_scenarios",
            "Custom C++ Solver Scenarios",
            bool(cpp_summary.get("passed")),
            f"{cpp_summary.get('run_count', 0)} C++ scenario runs completed.",
            ("cpp_solver_summary.json",),
        ),
        check_from_summary(
            "geoclaw_cpp_comparison",
            "GeoClaw/C++ Comparison",
            bool(comparison_summary.get("passed")),
            f"{comparison_summary.get('comparison_count', 0)} GeoClaw/C++ threshold comparisons completed.",
            ("geoclaw_cpp_comparison_summary.json",),
        ),
        check_from_summary(
            "geoclaw_cpp_tuning",
            "GeoClaw C++ Tuning",
            bool(tuning_summary.get("passed")),
            f"{tuning_summary.get('candidate_count', 0)} C++ tuning candidates scored against GeoClaw.",
            ("geoclaw_cpp_tuning_summary.json",),
        ),
        check_from_summary(
            "geoclaw_raft_coupling",
            "GeoClaw Raft Coupling",
            bool(raft_coupling_summary.get("passed")),
            f"{raft_coupling_summary.get('comparison_count', 0)} raft coupling comparisons completed.",
            ("geoclaw_raft_coupling_validation.json",),
        ),
    )
    blocking_failures = tuple(check for check in checks if not check.passed and check.status == "failed")
    approved = not blocking_failures
    decision = ReadinessGateDecision(
        status="approved" if approved else "blocked",
        approved_for_unreal_production_start=approved,
        reason=(
            "GeoClaw/C++ validation passed; live Unreal custom water can proceed after target-hardware confirmation."
            if approved
            else "GeoClaw transition artifacts were generated, but live Unreal water remains blocked until the failed GeoClaw validation checks pass."
        ),
        required_next_actions=(
            (
                "Replace export-only normalized frames with real GeoClaw fixed-grid output for canonical, rafting, and real-world flow suites.",
                "Run the custom C++ solver against the same packages and pass GeoClaw/C++ thresholds.",
                "Re-run raft coupling against GeoClaw and C++ fields with outcome agreement.",
            )
            if not approved
            else (
                "Lock the accepted GeoClaw/C++ telemetry schema before Unreal live-water integration.",
                "Keep GeoClaw as the offline regression reference for future river content.",
            )
        ),
    )
    return PythonToUnrealReadinessReport(
        gate_version=GEOCLAW_READINESS_REPORT_VERSION,
        decision=decision,
        checks=checks,
        runtime_choices={
            "authoritative_water_candidate": "custom C++ reduced shallow-water / height-field solver",
            "reference_solver": "GeoClaw offline fixed-grid output normalized into the shared telemetry schema",
            "raft_and_contact_candidate": "Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail",
            "unreal_integration_order": "telemetry/replay playback first, then live custom water after GeoClaw revalidation, then Chrono/custom raft coupling",
            "chrono_fsi": "optional research path only, not a baseline runtime dependency",
        },
        accepted_model_limitations=(
            "2.5D shallow-water/height-field flow remains the accepted runtime model for the first Unreal bridge; full 3D CFD is out of scope.",
            "GeoClaw is an offline validation/reference dependency, not a shipping Unreal runtime dependency.",
            "Export-only normalized GeoClaw frames are setup smoke artifacts and cannot approve live water.",
            "Real-world C++ matching must pass GeoClaw threshold reports before final river-content production.",
        ),
        risks=(
            "GeoClaw setup depends on local Clawpack and Fortran build tooling.",
            "C++ solver parameters may need retuning after full GeoClaw fgout frames are available.",
            "Runtime budgets are still measured on local smoke scenarios and need target hardware confirmation.",
            "Geospatial source licensing and attribution must be re-checked when pulling production data.",
        ),
        artifact_manifest=artifact_manifest,
    )


def build_milestone16_geoclaw_readiness_report(
    *,
    geoclaw_reference_summary: dict[str, object],
    cpp_summary: dict[str, object],
    comparison_summary: dict[str, object],
    geometry_summary: dict[str, object],
    raft_coupling_summary: dict[str, object],
    runtime_profile_summary: dict[str, object],
    regression_promotion_summary: dict[str, object],
    artifact_manifest: dict[str, object],
) -> PythonToUnrealReadinessReport:
    """Build the full Milestone 16 GeoClaw-to-Unreal live-water gate."""

    checks = (
        check_from_summary(
            "milestone16_geoclaw_reference_runs",
            "Milestone 16 GeoClaw Reference Runs",
            bool(geoclaw_reference_summary.get("passed")),
            (
                f"{geoclaw_reference_summary.get('passed_count', 0)} of "
                f"{geoclaw_reference_summary.get('scenario_count', 0)} scenarios have full GeoClaw frames."
            ),
            ("geoclaw_reference_summary.json",),
        ),
        check_from_summary(
            "milestone16_cpp_solver_runs",
            "Milestone 16 C++ Solver Runs",
            bool(cpp_summary.get("passed")),
            f"{cpp_summary.get('passed_count', 0)} of {cpp_summary.get('run_count', 0)} C++ runs completed with manifests.",
            ("cpp_solver_summary.json",),
        ),
        check_from_summary(
            "milestone16_geoclaw_cpp_thresholds",
            "Milestone 16 GeoClaw/C++ Thresholds",
            bool(comparison_summary.get("passed")),
            (
                f"{comparison_summary.get('threshold_passed_count', 0)} of "
                f"{comparison_summary.get('comparison_count', 0)} threshold comparisons pass."
            ),
            ("geoclaw_cpp_comparison_summary.json",),
        ),
        check_from_summary(
            "milestone16_geometry_validation",
            "Milestone 16 Geometry Validation",
            bool(geometry_summary.get("passed")),
            f"{geometry_summary.get('passed_count', 0)} of {geometry_summary.get('case_count', 0)} geometry families pass.",
            ("geometry_validation_summary.json",),
        ),
        check_from_summary(
            "milestone16_raft_coupling",
            "Milestone 16 Raft Coupling",
            bool(raft_coupling_summary.get("passed")),
            (
                f"{raft_coupling_summary.get('passed_count', 0)} of "
                f"{raft_coupling_summary.get('comparison_count', 0)} raft comparisons pass."
            ),
            ("raft_coupling_validation_summary.json",),
        ),
        check_from_summary(
            "milestone16_runtime_profile",
            "Milestone 16 Runtime Profile",
            bool(runtime_profile_summary.get("passed")),
            (
                f"{runtime_profile_summary.get('budget_passed_count', 0)} of "
                f"{runtime_profile_summary.get('run_count', 0)} promoted C++ profile repetitions pass runtime budgets."
            ),
            ("runtime_profile_summary.json",),
        ),
        check_from_summary(
            "milestone16_regression_promotion",
            "Milestone 16 Regression Promotion",
            bool(regression_promotion_summary.get("passed")),
            f"{regression_promotion_summary.get('entry_count', 0)} passing artifacts promoted.",
            ("regression_promotion_summary.json",),
        ),
    )
    blocking_failures = tuple(check for check in checks if not check.passed and check.status == "failed")
    approved = not blocking_failures
    failed_check_ids = {check.check_id for check in blocking_failures}
    blocked_titles = ", ".join(check.title for check in blocking_failures)
    blocked_actions: list[str] = []
    if "milestone16_geoclaw_cpp_thresholds" in failed_check_ids:
        blocked_actions.append("Fix remaining GeoClaw/C++ threshold failures outside accepted guardrail rows.")
    if "milestone16_geometry_validation" in failed_check_ids:
        blocked_actions.append(
            "Retune wet/dry, bed-step, constriction, drop/ledge, and cascading reach/drop dynamics until geometry families pass."
        )
    if "milestone16_raft_coupling" in failed_check_ids:
        blocked_actions.append(
            "Retune raft coupling against GeoClaw and C++ fields until force envelopes, outcomes, and transition cases pass."
        )
    if "milestone16_runtime_profile" in failed_check_ids:
        blocked_actions.append("Bring promoted C++ water configurations back under the runtime and deterministic replay budgets.")
    if "milestone16_regression_promotion" in failed_check_ids:
        blocked_actions.append("Promote every passing comparison, geometry, and raft artifact required by the full gate.")
    if blocking_failures:
        blocked_actions.append(
            "Keep the distinct Milestone 18 pin/release fixture separate from the raft-coupling water-field agreement gate."
        )
    decision = ReadinessGateDecision(
        status="approved" if approved else "blocked",
        approved_for_unreal_production_start=approved,
        reason=(
            "The full Milestone 16 GeoClaw/C++/raft/runtime gate passed; live Unreal custom water can proceed after target-hardware confirmation."
            if approved
            else f"The full Milestone 16 gate was regenerated, but live Unreal custom water remains blocked by: {blocked_titles}."
        ),
        required_next_actions=(
            tuple(blocked_actions)
            if blocking_failures
            else (
                "Lock the accepted Milestone 16 report set and regression fixtures before live-water Unreal integration.",
                "Repeat runtime profiling on target desktop, VR, and handheld hardware.",
            )
        ),
    )
    return PythonToUnrealReadinessReport(
        gate_version=GEOCLAW_READINESS_REPORT_VERSION,
        decision=decision,
        checks=checks,
        runtime_choices={
            "authoritative_water_candidate": "custom C++ reduced or finite-volume shallow-water / height-field solver after full Milestone 16 approval",
            "reference_solver": "GeoClaw offline fixed-grid output normalized into the shared telemetry schema",
            "raft_and_contact_candidate": "Project Chrono bridge or custom reduced raft fallback over validated custom water fields",
            "unreal_integration_order": "telemetry/replay playback and promoted regression fixtures first; live custom water only after all Milestone 16 checks pass",
            "chrono_fsi": "optional research path only, not a baseline runtime dependency",
        },
        accepted_model_limitations=(
            "2.5D shallow-water/height-field flow remains the intended runtime model; full 3D CFD is out of scope.",
            "GeoClaw remains offline reference infrastructure and does not ship inside Unreal.",
            "Promoted fixtures are passing subsets, not proof that the full live-water gate has passed.",
            "Dedicated pin/release evidence remains a separate Milestone 18 fixture until the full readiness gate is rerun.",
        ),
        risks=(
            "Most GeoClaw/C++ threshold comparisons still fail outside hydrostatic/sloping cases.",
            "Raft force and outcome agreement is not yet stable across hydraulics, drops, and boulder gardens.",
            "Runtime profile passes only the promoted configurations and still needs target hardware confirmation.",
            "Real-world river source licensing, guide review, and field-media validation remain production gates.",
        ),
        artifact_manifest=artifact_manifest,
    )


def check_from_summary(
    check_id: str,
    title: str,
    passed: bool,
    details: str,
    artifacts: tuple[str, ...] = (),
    *,
    warning: bool = False,
) -> ReadinessCheck:
    status: CheckStatus = "passed" if passed else ("warning" if warning else "failed")
    return ReadinessCheck(
        check_id=check_id,
        title=title,
        passed=passed,
        status=status,
        details=details,
        artifacts=artifacts,
    )


def write_json_artifact(path: str | Path, data: dict[str, object]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def summarize_profile_report(report: SolverProfileReport) -> dict[str, object]:
    return report.to_json_dict()["summary"]  # type: ignore[index]


def summarize_performance_report(report: BaselinePerformanceReport) -> dict[str, object]:
    return report.to_json_dict()


def count_csv_rows(path: str | Path) -> int:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for _ in csv.DictReader(handle)))


def _metadata_with_provenance(metadata: ScenarioMetadata2_5D, provenance_update: dict[str, object]) -> ScenarioMetadata2_5D:
    return replace(metadata, provenance={**metadata.provenance, **provenance_update})  # type: ignore[arg-type]


def _vec_json(value: Vec3) -> dict[str, float]:
    return {"x": value.x, "y": value.y, "z": value.z}


def _quat_json(value: Quaternion) -> dict[str, float]:
    return {"w": value.w, "x": value.x, "y": value.y, "z": value.z}
