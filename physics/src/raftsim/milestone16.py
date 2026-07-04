"""Milestone 16 validation runners and report artifacts."""

from __future__ import annotations

import json
import shutil
from hashlib import sha256
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .comparison import (
    ScenarioThresholds,
    compare_dual_solver_diagnostics,
    compare_dual_solver_features,
    compare_dual_solver_fields,
    compare_dual_solver_probes,
    evaluate_dual_solver_thresholds,
)
from .cascading import (
    evaluate_cascading_handoff_conservation,
    read_cascading_scenario_package,
)
from .dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
from .feature_validation import (
    FeatureValidationResult,
    build_cascading_raft_validation_cases,
    summarize_run_outcomes,
    validate_boil_upwelling_case,
    validate_cascading_raft_cases,
    validate_eddy_line_case,
    validate_hole_case,
    validate_lateral_wave_case,
    validate_shallow_shelf_case,
    validate_standing_wave_case,
    validate_submerged_rock_case,
)
from .geoclaw_reference import (
    GEOCLAW_CANONICAL_FIXTURES,
    GEOCLAW_RAFTING_CASES,
    GeoClawExportConfig,
    GeoClawRunConfig,
    cascading_geoclaw_scenarios,
    check_geoclaw_availability,
    export_geoclaw_cascading_package,
    export_geoclaw_scenario,
    normalize_geoclaw_cascading_fixed_grid_output,
    normalize_geoclaw_fixed_grid_output,
    rafting_geoclaw_scenarios,
    run_geoclaw_export,
)
from .math3d import Vec3
from .raft_coupling2_5d import (
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    compare_raft_force_samples,
)
from .real_world import default_player_selections, generate_real_world_scenario2_5d
from .scenario2_5d import Scenario2_5D
from .scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d, read_scenario2_5d_package
from .validation_gate import CUSTOM_CPP_VALIDATION_SCENARIOS, CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS

MILESTONE16_GEOCLAW_REFERENCE_REPORT_SCHEMA = "raftsim.milestone16.geoclaw_reference_runs.v0"
MILESTONE16_CPP_RUN_REPORT_SCHEMA = "raftsim.milestone16.cpp_solver_runs.v0"
MILESTONE16_COMPARISON_REPORT_SCHEMA = "raftsim.milestone16.geoclaw_cpp_comparisons.v0"
MILESTONE16_GEOMETRY_VALIDATION_REPORT_SCHEMA = "raftsim.milestone16.geometry_validation.v0"
MILESTONE16_RAFT_COUPLING_REPORT_SCHEMA = "raftsim.milestone16.raft_coupling_validation.v0"
MILESTONE16_REGRESSION_PROMOTION_REPORT_SCHEMA = "raftsim.milestone16.regression_promotion.v0"
MILESTONE16_REGRESSION_REGISTRY_SCHEMA = "raftsim.milestone16.regression_registry.v0"
MILESTONE16_RUNTIME_PROFILE_REPORT_SCHEMA = "raftsim.milestone16.runtime_profile.v0"
MILESTONE16_FULL_CPP_VALIDATION_GATE_REPORT_SCHEMA = "raftsim.milestone16.full_cpp_validation_gate.v0"
MILESTONE16_RAFT_FORCE_DELTA_WEIGHT_RATIO_THRESHOLD = 1.0
MILESTONE16_RAFT_TORQUE_DELTA_INERTIA_RATIO_THRESHOLD = 2.5
MILESTONE16_RAFT_TRAJECTORY_POSITION_DELTA_M_THRESHOLD = 0.25
MILESTONE16_RAFT_TRAJECTORY_VELOCITY_DELTA_MPS_THRESHOLD = 0.5
MILESTONE16_CASE_DIRS = {
    "flat_pool": "c_flat",
    "uniform_channel": "c_uniform",
    "dam_break": "c_dam",
    "bed_step": "c_step",
    "constriction": "c_constrict",
    "wet_dry_shoreline": "c_wetdry",
    "sloping_manning_channel": "c_slope",
    "drop_ledge": "c_drop",
    "boulder_garden": "r_boulder",
    "cascading_wave_train": "r_waves",
    "hydraulic_hole_downstream_boil": "r_hole",
    "lateral_wave": "r_lateral",
    "eddy_line_shear": "r_eddy",
    "shallow_shelf": "r_shelf",
    "south_fork_low_runnable": "rw_low",
    "south_fork_median_runnable": "rw_med",
    "south_fork_high_runnable": "rw_high",
    "south_fork_cascading_low_runnable": "cg_low",
    "south_fork_cascading_median_runnable": "cg_med",
    "south_fork_cascading_high_runnable": "cg_high",
}
MILESTONE16_FULL_GATE_REPORT_FILES = {
    "geoclaw_reference": "geoclaw_reference_runs.json",
    "cpp_solver": "cpp_solver_runs.json",
    "geoclaw_cpp_comparisons": "geoclaw_cpp_comparisons.json",
    "geometry": "geometry_validation.json",
    "raft_coupling": "raft_coupling_validation.json",
    "runtime_profile": "runtime_profile.json",
    "regression_promotion": "regression_promotion_manifest.json",
}
MILESTONE18_GEOMETRY_CLOSURE_REPORTS = {
    "wet_dry_shoreline": {
        "report": "wet_dry_finite_volume_reconstruction_retune.json",
        "accepted_solver_modes": ("finite_volume", "reduced"),
        "diagnostic_solver_modes": (),
    },
    "bed_step": {
        "report": "bed_step_parity_retune.json",
        "accepted_solver_modes": ("finite_volume",),
        "diagnostic_solver_modes": ("reduced",),
    },
}
MILESTONE18_REMAINING_GEOMETRY_CLOSURE_CASES = frozenset({"constriction", "drops_ledges_tailwater"})


@dataclass(frozen=True, slots=True)
class Milestone16GeoClawRunRecord:
    """Tracked evidence for one full GeoClaw fixed-grid reference run."""

    gate_scenario_id: str
    actual_scenario_id: str
    suite: str
    flow_band: str | None
    export_dir: str
    run_manifest: str
    normalized_manifest: str | None
    normalized_mode: str | None
    returncode: int
    runtime_seconds: float
    frame_count: int
    full_solution: bool
    reach_window_count: int = 0
    drop_transition_window_count: int = 0
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and self.full_solution and self.frame_count > 0

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["notes"] = list(self.notes)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone16GeoClawReferenceReport:
    """Compact report for the Milestone 16 GeoClaw reference-run suite."""

    output_root: str
    seed: int
    config: dict[str, object]
    availability: dict[str, object]
    records: tuple[Milestone16GeoClawRunRecord, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(record.passed for record in self.records)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_GEOCLAW_REFERENCE_REPORT_SCHEMA,
            "passed": self.passed,
            "output_root": self.output_root,
            "seed": self.seed,
            "config": self.config,
            "availability": self.availability,
            "scenario_count": len(self.records),
            "passed_count": sum(1 for record in self.records if record.passed),
            "failed_count": sum(1 for record in self.records if not record.passed),
            "records": [record.to_json_dict() for record in self.records],
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
            "# Milestone 16 GeoClaw Reference Runs",
            "",
            f"Schema: `{MILESTONE16_GEOCLAW_REFERENCE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario count: {len(self.records)}",
            "",
            "| Suite | Gate scenario | Actual scenario | Frames | Full solution | Runtime (s) |",
            "| --- | --- | --- | ---: | --- | ---: |",
        ]
        for record in self.records:
            lines.append(
                "| "
                f"{record.suite} | "
                f"{record.gate_scenario_id} | "
                f"{record.actual_scenario_id} | "
                f"{record.frame_count} | "
                f"{'yes' if record.full_solution else 'no'} | "
                f"{record.runtime_seconds:.3f} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16CppRunRecord:
    """Tracked evidence for one C++ solver mode run in the validation matrix."""

    gate_scenario_id: str
    actual_scenario_id: str
    suite: str
    solver_mode: str
    scenario_package: str
    output_dir: str
    manifest: str
    validation: str
    returncode: int
    runtime_seconds: float
    frame_count: int
    validation_passed: bool
    manifest_settings: dict[str, object]
    cascading: dict[str, object]
    required_manifest_fields_present: bool

    @property
    def passed(self) -> bool:
        return (
            self.returncode in {0, 2}
            and self.frame_count > 0
            and self.required_manifest_fields_present
            and self.manifest_settings.get("solver_mode") == self.solver_mode
        )

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone16CppRunReport:
    """Compact report for C++ reduced and finite-volume runs over Milestone 16 scenarios."""

    geoclaw_reference_report: str
    output_root: str
    cpp_solver: str
    records: tuple[Milestone16CppRunRecord, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(record.passed for record in self.records)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_CPP_RUN_REPORT_SCHEMA,
            "passed": self.passed,
            "geoclaw_reference_report": self.geoclaw_reference_report,
            "output_root": self.output_root,
            "cpp_solver": self.cpp_solver,
            "scenario_count": len({record.gate_scenario_id for record in self.records}),
            "run_count": len(self.records),
            "passed_count": sum(1 for record in self.records if record.passed),
            "failed_count": sum(1 for record in self.records if not record.passed),
            "records": [record.to_json_dict() for record in self.records],
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
            "# Milestone 16 C++ Solver Runs",
            "",
            f"Schema: `{MILESTONE16_CPP_RUN_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Run count: {len(self.records)}",
            "",
            "| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |",
            "| --- | --- | --- | ---: | --- | ---: | --- |",
        ]
        for record in self.records:
            cascading = record.cascading
            cascading_label = "no"
            if cascading.get("present") is True:
                cascading_label = f"{cascading.get('reach_count')} reaches / {cascading.get('drop_transition_count')} drops"
            lines.append(
                "| "
                f"{record.suite} | "
                f"{record.gate_scenario_id} | "
                f"{record.solver_mode} | "
                f"{record.frame_count} | "
                f"{'PASS' if record.validation_passed else 'FAIL'} | "
                f"{record.runtime_seconds:.3f} | "
                f"{cascading_label} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16ComparisonRecord:
    """Summary for one GeoClaw-vs-C++ comparison run."""

    gate_scenario_id: str
    actual_scenario_id: str
    suite: str
    solver_mode: str
    threshold_tier: str
    comparison_dir: str
    threshold_report: str
    threshold_passed: bool
    failing_checks: tuple[str, ...]
    check_values: dict[str, dict[str, object]]
    frame_comparisons: int
    point_probes: int
    cross_sections: int
    feature_count: int
    reach_drop_check: dict[str, object]

    @property
    def compared(self) -> bool:
        return self.frame_comparisons > 0 and self.point_probes >= 0 and self.cross_sections >= 0

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["failing_checks"] = list(self.failing_checks)
        data["compared"] = self.compared
        return data


@dataclass(frozen=True, slots=True)
class Milestone16ComparisonReport:
    """Suite-level GeoClaw-vs-C++ comparison report."""

    geoclaw_reference_report: str
    cpp_run_report: str
    output_root: str
    records: tuple[Milestone16ComparisonRecord, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(record.threshold_passed for record in self.records)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_COMPARISON_REPORT_SCHEMA,
            "passed": self.passed,
            "geoclaw_reference_report": self.geoclaw_reference_report,
            "cpp_run_report": self.cpp_run_report,
            "output_root": self.output_root,
            "comparison_count": len(self.records),
            "threshold_passed_count": sum(1 for record in self.records if record.threshold_passed),
            "threshold_failed_count": sum(1 for record in self.records if not record.threshold_passed),
            "records": [record.to_json_dict() for record in self.records],
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
            "# Milestone 16 GeoClaw/C++ Comparisons",
            "",
            f"Schema: `{MILESTONE16_COMPARISON_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Comparison count: {len(self.records)}",
            "",
            "| Suite | Gate scenario | Mode | Tier | Thresholds | Failing checks | Reach/drop |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for record in self.records:
            reach_drop = record.reach_drop_check
            if reach_drop.get("required") is True:
                reach_label = "PASS" if reach_drop.get("passed") is True else "FAIL"
            else:
                reach_label = "n/a"
            lines.append(
                "| "
                f"{record.suite} | "
                f"{record.gate_scenario_id} | "
                f"{record.solver_mode} | "
                f"{record.threshold_tier} | "
                f"{'PASS' if record.threshold_passed else 'FAIL'} | "
                f"{', '.join(record.failing_checks) if record.failing_checks else 'none'} | "
                f"{reach_label} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16GeometryCaseResult:
    """One geometry-specific validation family."""

    case_id: str
    title: str
    scenarios: tuple[str, ...]
    solver_modes: tuple[str, ...]
    passed: bool
    evidence: tuple[dict[str, object], ...]
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["scenarios"] = list(self.scenarios)
        data["solver_modes"] = list(self.solver_modes)
        data["evidence"] = list(self.evidence)
        data["notes"] = list(self.notes)
        return data


@dataclass(frozen=True, slots=True)
class Milestone16GeometryValidationReport:
    """Geometry-specific validation summary for Milestone 16."""

    comparison_report: str
    geoclaw_reference_report: str
    cases: tuple[Milestone16GeometryCaseResult, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(case.passed for case in self.cases)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_GEOMETRY_VALIDATION_REPORT_SCHEMA,
            "passed": self.passed,
            "comparison_report": self.comparison_report,
            "geoclaw_reference_report": self.geoclaw_reference_report,
            "case_count": len(self.cases),
            "passed_count": sum(1 for case in self.cases if case.passed),
            "failed_count": sum(1 for case in self.cases if not case.passed),
            "cases": [case.to_json_dict() for case in self.cases],
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
            "# Milestone 16 Geometry Validation",
            "",
            f"Schema: `{MILESTONE16_GEOMETRY_VALIDATION_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            "| Case | Status | Scenarios | Notes |",
            "| --- | --- | --- | --- |",
        ]
        for case in self.cases:
            lines.append(
                "| "
                f"{case.title} | "
                f"{'PASS' if case.passed else 'FAIL'} | "
                f"{', '.join(case.scenarios)} | "
                f"{'; '.join(case.notes) if case.notes else 'none'} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16RaftCouplingRecord:
    """One GeoClaw-vs-C++ raft-coupling case comparison."""

    gate_scenario_id: str
    actual_scenario_id: str
    suite: str
    flow_band: str | None
    solver_mode: str
    case_id: str
    expected_outcomes: tuple[str, ...]
    reference_frame: str
    candidate_frame: str
    reference_outcome: str
    candidate_outcome: str
    reference_passed: bool
    candidate_passed: bool
    feature_outcome_match: bool
    force_envelope_outcome_match: bool
    force_delta_weight_ratio: float
    torque_delta_inertia_ratio: float
    trajectory_position_delta_m: float
    trajectory_velocity_delta_mps: float
    reference_checks: tuple[dict[str, object], ...]
    candidate_checks: tuple[dict[str, object], ...]
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.reference_passed
            and self.candidate_passed
            and self.feature_outcome_match
            and self.force_envelope_outcome_match
            and self.force_delta_weight_ratio <= MILESTONE16_RAFT_FORCE_DELTA_WEIGHT_RATIO_THRESHOLD
            and self.torque_delta_inertia_ratio <= MILESTONE16_RAFT_TORQUE_DELTA_INERTIA_RATIO_THRESHOLD
            and self.trajectory_position_delta_m <= MILESTONE16_RAFT_TRAJECTORY_POSITION_DELTA_M_THRESHOLD
            and self.trajectory_velocity_delta_mps <= MILESTONE16_RAFT_TRAJECTORY_VELOCITY_DELTA_MPS_THRESHOLD
        )

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["expected_outcomes"] = list(self.expected_outcomes)
        data["reference_checks"] = list(self.reference_checks)
        data["candidate_checks"] = list(self.candidate_checks)
        data["notes"] = list(self.notes)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone16RaftCouplingReport:
    """Milestone 16 raft coupling validation over GeoClaw and C++ fields."""

    geoclaw_reference_report: str
    cpp_run_report: str
    records: tuple[Milestone16RaftCouplingRecord, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(record.passed for record in self.records)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_RAFT_COUPLING_REPORT_SCHEMA,
            "passed": self.passed,
            "geoclaw_reference_report": self.geoclaw_reference_report,
            "cpp_run_report": self.cpp_run_report,
            "thresholds": {
                "force_delta_weight_ratio": MILESTONE16_RAFT_FORCE_DELTA_WEIGHT_RATIO_THRESHOLD,
                "torque_delta_inertia_ratio": MILESTONE16_RAFT_TORQUE_DELTA_INERTIA_RATIO_THRESHOLD,
                "trajectory_position_delta_m": MILESTONE16_RAFT_TRAJECTORY_POSITION_DELTA_M_THRESHOLD,
                "trajectory_velocity_delta_mps": MILESTONE16_RAFT_TRAJECTORY_VELOCITY_DELTA_MPS_THRESHOLD,
            },
            "comparison_count": len(self.records),
            "passed_count": sum(1 for record in self.records if record.passed),
            "failed_count": sum(1 for record in self.records if not record.passed),
            "notes": list(self.notes),
            "records": [record.to_json_dict() for record in self.records],
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
            "# Milestone 16 Raft Coupling Validation",
            "",
            f"Schema: `{MILESTONE16_RAFT_COUPLING_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Comparisons: {len(self.records)}",
            "",
            "| Suite | Gate scenario | Mode | Case | Status | Ref outcome | C++ outcome | Force ratio | Velocity delta |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
        for record in self.records:
            lines.append(
                "| "
                f"{record.suite} | "
                f"{record.gate_scenario_id} | "
                f"{record.solver_mode} | "
                f"{record.case_id} | "
                f"{'PASS' if record.passed else 'FAIL'} | "
                f"{record.reference_outcome} | "
                f"{record.candidate_outcome} | "
                f"{record.force_delta_weight_ratio:.3f} | "
                f"{record.trajectory_velocity_delta_mps:.3f} |"
            )
        if self.notes:
            lines.extend(["", "## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16RegressionPromotionEntry:
    """One promoted Milestone 16 regression fixture or artifact manifest."""

    artifact_id: str
    category: str
    gate_scenario_id: str
    actual_scenario_id: str
    suite: str
    solver_mode: str
    artifact_dir: str
    source_report: str
    passed: bool
    case_id: str | None = None
    scenario_package: str | None = None
    manifest: str | None = None
    reports: dict[str, str] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["notes"] = list(self.notes)
        return data


@dataclass(frozen=True, slots=True)
class Milestone16RegressionPromotionReport:
    """Promotion manifest for passing Milestone 16 comparison artifacts."""

    comparison_report: str
    raft_coupling_report: str
    registry_path: str
    fixture_root: str
    geometry_validation_report: str | None = None
    entries: tuple[Milestone16RegressionPromotionEntry, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return bool(self.entries) and all(entry.passed for entry in self.entries)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_REGRESSION_PROMOTION_REPORT_SCHEMA,
            "passed": self.passed,
            "comparison_report": self.comparison_report,
            "raft_coupling_report": self.raft_coupling_report,
            "geometry_validation_report": self.geometry_validation_report,
            "registry_path": self.registry_path,
            "fixture_root": self.fixture_root,
            "entry_count": len(self.entries),
            "geoclaw_cpp_fixture_count": sum(1 for entry in self.entries if entry.category == "geoclaw_cpp"),
            "raft_artifact_count": sum(1 for entry in self.entries if entry.category == "raft_coupling"),
            "geometry_artifact_count": sum(1 for entry in self.entries if entry.category == "geometry_validation"),
            "notes": list(self.notes),
            "entries": [entry.to_json_dict() for entry in self.entries],
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
            "# Milestone 16 Regression Promotion",
            "",
            f"Schema: `{MILESTONE16_REGRESSION_PROMOTION_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Promoted entries: {len(self.entries)}",
            "",
            "| Category | Gate scenario | Mode | Case | Artifact |",
            "| --- | --- | --- | --- | --- |",
        ]
        for entry in self.entries:
            lines.append(
                "| "
                f"{entry.category} | "
                f"{entry.gate_scenario_id} | "
                f"{entry.solver_mode} | "
                f"{entry.case_id or 'n/a'} | "
                f"{entry.artifact_dir} |"
            )
        if self.notes:
            lines.extend(["", "## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16RuntimeProfileRecord:
    """One profiled C++ runtime repetition for a promoted Milestone 16 config."""

    artifact_id: str
    gate_scenario_id: str
    actual_scenario_id: str
    solver_mode: str
    repetition: int
    scenario_package: str
    output_dir: str
    manifest: str
    validation: str
    runtime_seconds: float
    simulated_seconds: float
    step_count: int
    runtime_ms_per_tick: float
    validation_passed: bool
    frame_hash: str
    budget_results: dict[str, dict[str, object]]

    @property
    def passed(self) -> bool:
        return self.validation_passed and all(bool(result["passed"]) for result in self.budget_results.values())

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone16RuntimeProfileReport:
    """Runtime-budget and deterministic-replay profile for promoted C++ configs."""

    registry_path: str
    cpp_solver: str
    budget_config: str
    output_root: str
    records: tuple[Milestone16RuntimeProfileRecord, ...] = field(default_factory=tuple)
    deterministic_replay: tuple[dict[str, object], ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return (
            bool(self.records)
            and all(record.passed for record in self.records)
            and all(bool(group["passed"]) for group in self.deterministic_replay)
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE16_RUNTIME_PROFILE_REPORT_SCHEMA,
            "passed": self.passed,
            "registry_path": self.registry_path,
            "cpp_solver": self.cpp_solver,
            "budget_config": self.budget_config,
            "output_root": self.output_root,
            "run_count": len(self.records),
            "budget_passed_count": sum(1 for record in self.records if record.passed),
            "budget_failed_count": sum(1 for record in self.records if not record.passed),
            "deterministic_replay": list(self.deterministic_replay),
            "records": [record.to_json_dict() for record in self.records],
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
            "# Milestone 16 Runtime Profile",
            "",
            f"Schema: `{MILESTONE16_RUNTIME_PROFILE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            "| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |",
            "| --- | --- | ---: | ---: | --- | --- | --- | --- |",
        ]
        for record in self.records:
            desktop = "PASS" if record.budget_results["desktop"]["passed"] else "FAIL"
            vr = "PASS" if record.budget_results["vr"]["passed"] else "FAIL"
            handheld = "PASS" if record.budget_results["handheld"]["passed"] else "FAIL"
            lines.append(
                "| "
                f"{record.artifact_id} | "
                f"{record.solver_mode} | "
                f"{record.repetition} | "
                f"{record.runtime_ms_per_tick:.4f} | "
                f"{desktop} | "
                f"{vr} | "
                f"{handheld} | "
                f"`{record.frame_hash[:12]}` |"
            )
        lines.extend(["", "## Deterministic Replay", "", "| Artifact | Status | Hashes |", "| --- | --- | --- |"])
        for group in self.deterministic_replay:
            hashes = ", ".join(str(value)[:12] for value in group["hashes"])
            lines.append(
                "| "
                f"{group['artifact_id']} | "
                f"{'PASS' if group['passed'] else 'FAIL'} | "
                f"`{hashes}` |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone16FullGateComponent:
    component_id: str
    title: str
    source_report: str
    passed: bool
    total_count: int
    passed_count: int
    failed_count: int
    blockers: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "title": self.title,
            "source_report": self.source_report,
            "passed": self.passed,
            "total_count": self.total_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class Milestone16FullCppValidationGateReport:
    report_dir: str
    components: tuple[Milestone16FullGateComponent, ...]

    @property
    def passed(self) -> bool:
        return bool(self.components) and all(component.passed for component in self.components)

    def to_json_dict(self) -> dict[str, object]:
        blocked = tuple(component for component in self.components if not component.passed)
        return {
            "schema_version": MILESTONE16_FULL_CPP_VALIDATION_GATE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "report_dir": self.report_dir,
            "component_count": len(self.components),
            "passed_component_count": sum(1 for component in self.components if component.passed),
            "blocked_component_count": len(blocked),
            "blocked_component_ids": [component.component_id for component in blocked],
            "components": [component.to_json_dict() for component in self.components],
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
            "# Milestone 16 Full C++ Validation Gate",
            "",
            f"Schema: `{MILESTONE16_FULL_CPP_VALIDATION_GATE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            "| Component | Result | Passed | Failed | Total | Source |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
        for component in self.components:
            lines.append(
                "| "
                f"{component.title} | "
                f"{'PASS' if component.passed else 'BLOCKED'} | "
                f"{component.passed_count} | "
                f"{component.failed_count} | "
                f"{component.total_count} | "
                f"`{component.source_report}` |"
            )
        blocked = [component for component in self.components if not component.passed]
        if blocked:
            lines.extend(["", "## Blockers", ""])
            for component in blocked:
                lines.append(f"### {component.title}")
                if component.blockers:
                    for blocker in component.blockers:
                        lines.append(f"- {blocker}")
                else:
                    lines.append("- Component reported blocked without detailed blockers.")
                lines.append("")
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return output_path


def build_milestone16_full_cpp_validation_gate_report(report_dir: str | Path) -> Milestone16FullCppValidationGateReport:
    """Build one suite-level report from the Milestone 16 component reports."""

    root = Path(report_dir)
    reports = {key: _load_json_report(root / filename) for key, filename in MILESTONE16_FULL_GATE_REPORT_FILES.items()}
    components = (
        _full_gate_component(
            "geoclaw_reference",
            "GeoClaw Reference Runs",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["geoclaw_reference"],
            reports["geoclaw_reference"],
            total_key="scenario_count",
            passed_key="passed_count",
            failed_key="failed_count",
            blocker_records_key="records",
            blocker_label_key="gate_scenario_id",
            blocker_detail="GeoClaw reference did not produce a full passing solution",
        ),
        _full_gate_component(
            "cpp_solver",
            "C++ Solver Runs",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["cpp_solver"],
            reports["cpp_solver"],
            total_key="run_count",
            passed_key="passed_count",
            failed_key="failed_count",
            blocker_records_key="records",
            blocker_label_key="gate_scenario_id",
            blocker_detail="C++ run or manifest gate failed",
        ),
        _full_gate_component(
            "geoclaw_cpp_comparisons",
            "GeoClaw/C++ Threshold Comparisons",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["geoclaw_cpp_comparisons"],
            reports["geoclaw_cpp_comparisons"],
            total_key="comparison_count",
            passed_key="threshold_passed_count",
            failed_key="threshold_failed_count",
            blocker_records_key="records",
            blocker_label_key="gate_scenario_id",
            blocker_detail="GeoClaw/C++ threshold comparison failed",
            pass_field="threshold_passed",
            detail_field="failing_checks",
        ),
        _full_gate_component(
            "geometry",
            "Geometry-Specific Validation",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["geometry"],
            reports["geometry"],
            total_key="case_count",
            passed_key="passed_count",
            failed_key="failed_count",
            blocker_records_key="cases",
            blocker_label_key="case_id",
            blocker_detail="geometry family is blocked",
        ),
        _full_gate_component(
            "raft_coupling",
            "Raft Coupling Validation",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["raft_coupling"],
            reports["raft_coupling"],
            total_key="comparison_count",
            passed_key="passed_count",
            failed_key="failed_count",
            blocker_records_key="records",
            blocker_label_key="case_id",
            blocker_detail="raft coupling comparison failed",
            detail_field="notes",
        ),
        _runtime_profile_full_gate_component(root / MILESTONE16_FULL_GATE_REPORT_FILES["runtime_profile"], reports["runtime_profile"]),
        _full_gate_component(
            "regression_promotion",
            "Regression Promotion",
            root / MILESTONE16_FULL_GATE_REPORT_FILES["regression_promotion"],
            reports["regression_promotion"],
            total_key="entry_count",
            passed_key=None,
            failed_key=None,
            blocker_records_key="entries",
            blocker_label_key="artifact_id",
            blocker_detail="regression promotion entry failed",
        ),
    )
    return Milestone16FullCppValidationGateReport(report_dir=str(root), components=components)


def _load_json_report(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _full_gate_component(
    component_id: str,
    title: str,
    source_report: Path,
    report: dict[str, object],
    *,
    total_key: str,
    passed_key: str | None,
    failed_key: str | None,
    blocker_records_key: str,
    blocker_label_key: str,
    blocker_detail: str,
    pass_field: str = "passed",
    detail_field: str | None = None,
) -> Milestone16FullGateComponent:
    records = _report_records(report, blocker_records_key)
    passed = bool(report.get("passed"))
    total_count = _int_or_len(report, total_key, records)
    passed_count = (
        _int_or_len(report, passed_key, [record for record in records if record.get(pass_field)])
        if passed_key is not None
        else sum(1 for record in records if record.get(pass_field, passed))
    )
    failed_count = (
        _int_or_len(report, failed_key, [record for record in records if not record.get(pass_field)])
        if failed_key is not None
        else max(0, total_count - passed_count)
    )
    blockers = _component_blockers(
        records,
        label_key=blocker_label_key,
        detail=blocker_detail,
        pass_field=pass_field,
        detail_field=detail_field,
    )
    return Milestone16FullGateComponent(
        component_id=component_id,
        title=title,
        source_report=str(source_report),
        passed=passed,
        total_count=total_count,
        passed_count=passed_count,
        failed_count=failed_count,
        blockers=blockers,
        notes=tuple(str(note) for note in report.get("notes", []) if isinstance(note, str)),
    )


def _runtime_profile_full_gate_component(source_report: Path, report: dict[str, object]) -> Milestone16FullGateComponent:
    records = _report_records(report, "records")
    replays = _report_records(report, "deterministic_replay")
    budget_passed = _int_or_len(report, "budget_passed_count", [record for record in records if record.get("passed")])
    budget_failed = _int_or_len(report, "budget_failed_count", [record for record in records if not record.get("passed")])
    replay_passed = sum(1 for replay in replays if replay.get("passed"))
    replay_failed = len(replays) - replay_passed
    blockers = list(
        _component_blockers(
            records,
            label_key="artifact_id",
            detail="runtime budget failed",
            pass_field="passed",
        )
    )
    blockers.extend(
        _component_blockers(
            replays,
            label_key="artifact_id",
            detail="deterministic replay hash failed",
            pass_field="passed",
        )
    )
    return Milestone16FullGateComponent(
        component_id="runtime_profile",
        title="Runtime Profile And Determinism",
        source_report=str(source_report),
        passed=bool(report.get("passed")),
        total_count=len(records) + len(replays),
        passed_count=budget_passed + replay_passed,
        failed_count=budget_failed + replay_failed,
        blockers=tuple(blockers[:8]),
    )


def _component_blockers(
    records: list[dict[str, object]],
    *,
    label_key: str,
    detail: str,
    pass_field: str,
    detail_field: str | None = None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    for record in records:
        if bool(record.get(pass_field)):
            continue
        label = str(record.get(label_key, "<unknown>"))
        extra = _format_blocker_detail(record.get(detail_field)) if detail_field is not None else ""
        blockers.append(f"{label}: {detail}{extra}")
        if len(blockers) >= 8:
            break
    return tuple(blockers)


def _format_blocker_detail(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return f" ({value})" if value else ""
    if isinstance(value, (list, tuple)):
        details = ", ".join(str(item) for item in value[:4])
        return f" ({details})" if details else ""
    return f" ({value})"


def _report_records(report: dict[str, object], key: str) -> list[dict[str, object]]:
    value = report.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list.")
    return [record for record in value if isinstance(record, dict)]


def _int_or_len(report: dict[str, object], key: str | None, fallback_records: list[dict[str, object]]) -> int:
    if key is None:
        return len(fallback_records)
    value = report.get(key)
    return int(value) if isinstance(value, int) else len(fallback_records)


def run_milestone16_geoclaw_reference_suite(
    output_root: str | Path,
    *,
    seed: int = 16,
    num_output_times: int = 2,
    amr_min_level: int = 1,
    amr_max_level: int = 1,
    canonical_nx: int = 24,
    canonical_ny: int = 12,
    real_world_nx: int = 32,
    real_world_ny: int = 16,
    cascading_nx: int = 56,
    cascading_ny: int = 20,
    timeout_seconds: float = 300.0,
) -> Milestone16GeoClawReferenceReport:
    """Run the full Milestone 16 GeoClaw fixed-grid reference matrix."""

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    availability = check_geoclaw_availability()
    if not availability.available:
        raise RuntimeError(f"GeoClaw is unavailable: {availability.reason}")

    export_config = GeoClawExportConfig(
        num_output_times=num_output_times,
        amr_min_level=amr_min_level,
        amr_max_level=amr_max_level,
    )
    run_config = GeoClawRunConfig(timeout_seconds=timeout_seconds)
    records: list[Milestone16GeoClawRunRecord] = []

    for fixture in GEOCLAW_CANONICAL_FIXTURES:
        scenario = generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture=fixture, seed=seed, nx=canonical_nx, ny=canonical_ny)
        )
        records.append(_run_standard_geoclaw_case(root, fixture, "canonical", scenario, export_config, run_config))

    rafting_scenarios = {
        str(scenario.metadata.provenance.get("geoclaw_rafting_case")): scenario
        for scenario in rafting_geoclaw_scenarios(seed=seed)
        if scenario.metadata.provenance.get("geoclaw_rafting_case") in GEOCLAW_RAFTING_CASES
    }
    for case_id in GEOCLAW_RAFTING_CASES:
        scenario = rafting_scenarios[case_id]
        records.append(_run_standard_geoclaw_case(root, case_id, "rafting", scenario, export_config, run_config))

    for selection in default_player_selections():
        scenario = generate_real_world_scenario2_5d(
            selection,
            nx=real_world_nx,
            ny=real_world_ny,
            duration=8.0,
            pyclaw_reference_min_depth_m=0.0,
        )
        gate_id = f"south_fork_{selection.flow_band}"
        records.append(
            _run_standard_geoclaw_case(
                root,
                gate_id,
                "real_world",
                scenario,
                export_config,
                run_config,
                flow_band=selection.flow_band,
            )
        )

    for package in cascading_geoclaw_scenarios(nx=cascading_nx, ny=cascading_ny, duration=8.0):
        flow_band = package.scenario.metadata.flow_band
        gate_id = f"south_fork_cascading_{flow_band}"
        records.append(_run_cascading_geoclaw_case(root, gate_id, package, export_config, run_config, flow_band=flow_band))

    return Milestone16GeoClawReferenceReport(
        output_root=str(root),
        seed=seed,
        config={
            "num_output_times": num_output_times,
            "amr_min_level": amr_min_level,
            "amr_max_level": amr_max_level,
            "canonical_grid": {"nx": canonical_nx, "ny": canonical_ny},
            "real_world_grid": {"nx": real_world_nx, "ny": real_world_ny},
            "cascading_grid": {"nx": cascading_nx, "ny": cascading_ny},
            "timeout_seconds": timeout_seconds,
        },
        availability=availability.to_json_dict(),
        records=tuple(records),
    )


def run_milestone16_geometry_validation(
    comparison_report: str | Path,
    geoclaw_reference_report: str | Path,
    *,
    milestone18_report_dir: str | Path | None = None,
) -> Milestone16GeometryValidationReport:
    """Build geometry-specific validation results from Milestone 16 artifacts."""

    comparison_path = Path(comparison_report)
    geoclaw_path = Path(geoclaw_reference_report)
    m18_report_dir = Path(milestone18_report_dir) if milestone18_report_dir is not None else comparison_path.parent.parent / "milestone18"
    comparison = _read_json(comparison_path)
    geoclaw = _read_json(geoclaw_path)
    comparison_records = list(comparison["records"])
    cases = (
        _geometry_case_from_thresholds(
            "hydrostatic_sloping_balance",
            "Hydrostatic And Sloping Balance",
            ("flat_pool", "sloping_manning_channel"),
            comparison_records,
        ),
        _geometry_case_from_thresholds(
            "wet_dry_shoreline",
            "Wet/Dry Shorelines",
            ("wet_dry_shoreline",),
            comparison_records,
            milestone18_report_dir=m18_report_dir,
        ),
        _geometry_case_from_thresholds(
            "bed_step",
            "Bed Steps",
            ("bed_step",),
            comparison_records,
            milestone18_report_dir=m18_report_dir,
        ),
        _geometry_case_from_thresholds(
            "constriction",
            "Constrictions",
            ("constriction",),
            comparison_records,
            milestone18_report_dir=m18_report_dir,
        ),
        _geometry_case_from_thresholds(
            "drops_ledges_tailwater",
            "Drops, Ledges, And Tailwater",
            (
                "drop_ledge",
                "south_fork_cascading_low_runnable",
                "south_fork_cascading_median_runnable",
                "south_fork_cascading_high_runnable",
            ),
            comparison_records,
            milestone18_report_dir=m18_report_dir,
        ),
        _reach_drop_handoff_geometry_case(geoclaw),
    )
    return Milestone16GeometryValidationReport(
        comparison_report=str(comparison_path),
        geoclaw_reference_report=str(geoclaw_path),
        cases=cases,
    )


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


def run_milestone16_regression_promotion(
    comparison_report: str | Path,
    raft_coupling_report: str | Path,
    *,
    geometry_report: str | Path | None = None,
    fixture_root: str | Path = "regression_fixtures/milestone16",
    registry_path: str | Path | None = None,
) -> Milestone16RegressionPromotionReport:
    """Promote passing Milestone 16 GeoClaw/C++, geometry, and raft artifacts."""

    comparison_path = Path(comparison_report)
    raft_path = Path(raft_coupling_report)
    geometry_path = Path(geometry_report) if geometry_report is not None else None
    root = Path(fixture_root)
    registry = Path(registry_path) if registry_path is not None else root / "registry.json"
    comparison = _read_json(comparison_path)
    raft = _read_json(raft_path)
    geometry = _read_json(geometry_path) if geometry_path is not None else None
    entries: list[Milestone16RegressionPromotionEntry] = []

    for record in comparison["records"]:
        if bool(record.get("threshold_passed")):
            entries.append(_promote_geoclaw_cpp_regression(record, comparison_path, root))

    if geometry is not None:
        for case in geometry.get("cases", []):
            if not _should_promote_geometry_case(case):
                continue
            for evidence in case.get("evidence", []):
                if _should_promote_geometry_evidence(evidence):
                    entries.append(_promote_geometry_validation_artifact(case, evidence, geometry_path, root))

    for record in raft["records"]:
        if bool(record.get("passed")):
            entries.append(_promote_raft_coupling_artifact(record, raft_path, root))

    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": MILESTONE16_REGRESSION_REGISTRY_SCHEMA,
                "comparison_report": str(comparison_path),
                "raft_coupling_report": str(raft_path),
                "geometry_validation_report": str(geometry_path) if geometry_path is not None else None,
                "entry_count": len(entries),
                "entries": [entry.to_json_dict() for entry in entries],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return Milestone16RegressionPromotionReport(
        comparison_report=str(comparison_path),
        raft_coupling_report=str(raft_path),
        geometry_validation_report=str(geometry_path) if geometry_path is not None else None,
        registry_path=str(registry),
        fixture_root=str(root),
        entries=tuple(entries),
        notes=(
            "Only passing GeoClaw/C++ threshold runs were copied as regression fixtures.",
            "Passing stitched reach/drop geometry checks were promoted as artifact manifests that preserve seam-visible handoff diagnostics.",
            "Passing raft-coupling cases were promoted as artifact manifests that point back to the generated frame outputs.",
        ),
    )


def run_milestone16_runtime_profile(
    registry_path: str | Path,
    *,
    cpp_solver: str | Path,
    budget_config: str | Path = "config/runtime_budgets.json",
    output_root: str | Path = "outputs/m16profile",
    repetitions: int = 2,
) -> Milestone16RuntimeProfileReport:
    """Profile promoted Milestone 16 C++ configs against runtime budgets."""

    if repetitions < 2:
        raise ValueError("repetitions must be at least 2 to check deterministic replay.")
    registry = _read_json(Path(registry_path))
    budgets = _read_json(Path(budget_config))
    root = Path(output_root)
    executable = Path(cpp_solver)
    records: list[Milestone16RuntimeProfileRecord] = []
    replay_groups: list[dict[str, object]] = []
    for entry in registry["entries"]:
        if entry["category"] != "geoclaw_cpp":
            continue
        artifact_id = str(entry["artifact_id"])
        hashes: list[str] = []
        for repetition in range(repetitions):
            scenario_package = Path(str(entry["scenario_package"]))
            scenario = read_scenario2_5d_package(scenario_package)
            run_output = root / _artifact_path_fragment(artifact_id) / f"rep_{repetition:02d}"
            result = run_cpp_solver_scenario(
                scenario_package,
                output_dir=run_output,
                config=_cpp_config_for_mode(
                    executable,
                    str(entry["solver_mode"]),
                    gate_scenario_id=str(entry["gate_scenario_id"]),
                ),
            )
            frame_hash = _cpp_run_frame_hash(result.manifest_path)
            hashes.append(frame_hash)
            step_count = max(1, int(round(scenario.duration / scenario.fixed_dt)))
            runtime_ms_per_tick = result.runtime_seconds * 1000.0 / step_count
            records.append(
                Milestone16RuntimeProfileRecord(
                    artifact_id=artifact_id,
                    gate_scenario_id=str(entry["gate_scenario_id"]),
                    actual_scenario_id=str(entry["actual_scenario_id"]),
                    solver_mode=str(entry["solver_mode"]),
                    repetition=repetition,
                    scenario_package=str(scenario_package),
                    output_dir=str(result.output_dir),
                    manifest=str(result.manifest_path),
                    validation=str(result.validation_path),
                    runtime_seconds=result.runtime_seconds,
                    simulated_seconds=float(scenario.duration),
                    step_count=step_count,
                    runtime_ms_per_tick=runtime_ms_per_tick,
                    validation_passed=result.returncode in {0, 2},
                    frame_hash=frame_hash,
                    budget_results=_runtime_budget_results(runtime_ms_per_tick, budgets),
                )
            )
        replay_groups.append(
            {
                "artifact_id": artifact_id,
                "passed": len(set(hashes)) == 1,
                "hashes": hashes,
            }
        )

    return Milestone16RuntimeProfileReport(
        registry_path=str(registry_path),
        cpp_solver=str(executable),
        budget_config=str(budget_config),
        output_root=str(root),
        records=tuple(records),
        deterministic_replay=tuple(replay_groups),
    )


def run_milestone16_comparison_matrix(
    geoclaw_reference_report: str | Path,
    cpp_run_report: str | Path,
    *,
    output_root: str | Path = "outputs/m16cmp",
) -> Milestone16ComparisonReport:
    """Compare GeoClaw and C++ outputs over the Milestone 16 matrix."""

    geoclaw_report_path = Path(geoclaw_reference_report)
    cpp_report_path = Path(cpp_run_report)
    geoclaw_report = _read_json(geoclaw_report_path)
    cpp_report = _read_json(cpp_report_path)
    if not bool(geoclaw_report.get("passed")):
        raise RuntimeError(f"GeoClaw reference report is not passing: {geoclaw_report_path}")
    if not bool(cpp_report.get("passed")):
        raise RuntimeError(f"C++ run report is not passing: {cpp_report_path}")

    geoclaw_by_gate = {str(record["gate_scenario_id"]): record for record in geoclaw_report["records"]}
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    records: list[Milestone16ComparisonRecord] = []
    for cpp_record in cpp_report["records"]:
        gate_id = str(cpp_record["gate_scenario_id"])
        geoclaw_record = geoclaw_by_gate[gate_id]
        comparison_dir = root / _case_dir(gate_id) / str(cpp_record["solver_mode"])
        comparison_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = _write_milestone16_comparison_manifest(comparison_dir, geoclaw_record, cpp_record)
        thresholds = _thresholds_for_gate(gate_id)
        field_report = compare_dual_solver_fields(manifest_path, output_path=comparison_dir / "field_comparison.json")
        probe_report = compare_dual_solver_probes(manifest_path, output_path=comparison_dir / "probe_comparison.json")
        diagnostic_report = compare_dual_solver_diagnostics(
            manifest_path,
            output_path=comparison_dir / "diagnostic_comparison.json",
        )
        feature_report = compare_dual_solver_features(manifest_path, output_path=comparison_dir / "feature_comparison.json")
        threshold_report = evaluate_dual_solver_thresholds(
            manifest_path,
            thresholds=thresholds,
            output_path=comparison_dir / "threshold_evaluation.json",
        )
        records.append(
            Milestone16ComparisonRecord(
                gate_scenario_id=gate_id,
                actual_scenario_id=str(cpp_record["actual_scenario_id"]),
                suite=str(cpp_record["suite"]),
                solver_mode=str(cpp_record["solver_mode"]),
                threshold_tier=_threshold_tier_for_gate(gate_id),
                comparison_dir=str(comparison_dir),
                threshold_report=str(comparison_dir / "threshold_evaluation.json"),
                threshold_passed=threshold_report.passed,
                failing_checks=tuple(check.name for check in threshold_report.checks if not check.passed),
                check_values={check.name: check.to_json_dict() for check in threshold_report.checks},
                frame_comparisons=len(field_report.frame_comparisons),
                point_probes=len(probe_report.point_probes),
                cross_sections=len(probe_report.cross_sections),
                feature_count=feature_report.feature_count,
                reach_drop_check=_reach_drop_check(geoclaw_record, cpp_record),
            )
        )
        _ = diagnostic_report

    return Milestone16ComparisonReport(
        geoclaw_reference_report=str(geoclaw_report_path),
        cpp_run_report=str(cpp_report_path),
        output_root=str(root),
        records=tuple(records),
    )


def run_milestone16_cpp_solver_matrix(
    geoclaw_reference_report: str | Path,
    *,
    cpp_solver: str | Path,
    output_root: str | Path = "outputs/m16cpp",
) -> Milestone16CppRunReport:
    """Run C++ reduced and finite-volume modes on the GeoClaw scenario packages."""

    report_path = Path(geoclaw_reference_report)
    geoclaw_report = _read_json(report_path)
    if not bool(geoclaw_report.get("passed")):
        raise RuntimeError(f"GeoClaw reference report is not passing: {report_path}")

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    executable = Path(cpp_solver)
    records: list[Milestone16CppRunRecord] = []
    for geoclaw_record in geoclaw_report["records"]:
        export_dir = Path(str(geoclaw_record["export_dir"]))
        if geoclaw_record["suite"] == "cascading":
            scenario_package = export_dir / "shared_cascading_package"
        else:
            scenario_package = export_dir / "shared_scenario"
        gate_scenario_id = str(geoclaw_record["gate_scenario_id"])
        for solver_mode in ("reduced", "finite_volume"):
            config = _cpp_config_for_mode(executable, solver_mode, gate_scenario_id=gate_scenario_id)
            result = run_cpp_solver_scenario(
                scenario_package,
                output_dir=root / _case_dir(gate_scenario_id) / solver_mode,
                config=config,
            )
            records.append(
                _cpp_record_from_result(
                    geoclaw_record,
                    solver_mode=solver_mode,
                    scenario_package=scenario_package,
                    result=result,
                )
            )

    return Milestone16CppRunReport(
        geoclaw_reference_report=str(report_path),
        output_root=str(root),
        cpp_solver=str(executable),
        records=tuple(records),
    )


def _geometry_case_from_thresholds(
    case_id: str,
    title: str,
    scenario_ids: tuple[str, ...],
    comparison_records: list[dict[str, object]],
    *,
    milestone18_report_dir: Path | None = None,
) -> Milestone16GeometryCaseResult:
    evidence = tuple(
        {
            "gate_scenario_id": record["gate_scenario_id"],
            "solver_mode": record["solver_mode"],
            "threshold_passed": record["threshold_passed"],
            "failing_checks": record["failing_checks"],
        }
        for record in comparison_records
        if record["gate_scenario_id"] in scenario_ids
    )
    remaining_closure_case = _milestone18_remaining_geometry_closure_case(
        case_id,
        title,
        scenario_ids,
        evidence,
        milestone18_report_dir,
    )
    if remaining_closure_case is not None:
        return remaining_closure_case
    closure_case = _milestone18_geometry_closure_case(
        case_id,
        title,
        scenario_ids,
        evidence,
        milestone18_report_dir,
    )
    if closure_case is not None:
        return closure_case
    passed = bool(evidence) and all(bool(item["threshold_passed"]) for item in evidence)
    failing = sorted(
        {
            str(item["gate_scenario_id"])
            for item in evidence
            if not bool(item["threshold_passed"])
        }
    )
    notes = ()
    if failing:
        notes = (f"Threshold failures remain in: {', '.join(failing)}.",)
    return Milestone16GeometryCaseResult(
        case_id=case_id,
        title=title,
        scenarios=scenario_ids,
        solver_modes=tuple(sorted({str(item["solver_mode"]) for item in evidence})),
        passed=passed,
        evidence=evidence,
        notes=notes,
    )


def _milestone18_remaining_geometry_closure_case(
    case_id: str,
    title: str,
    scenario_ids: tuple[str, ...],
    stale_evidence: tuple[dict[str, object], ...],
    milestone18_report_dir: Path | None,
) -> Milestone16GeometryCaseResult | None:
    if case_id not in MILESTONE18_REMAINING_GEOMETRY_CLOSURE_CASES or milestone18_report_dir is None:
        return None
    report_path = milestone18_report_dir / "remaining_geometry_closure.json"
    if not report_path.exists():
        return None
    report = _read_json(report_path)
    case_payload = next(
        (
            item
            for item in report.get("cases", [])
            if isinstance(item, dict) and str(item.get("case_id")) == case_id
        ),
        None,
    )
    if case_payload is None:
        return None
    focused_evidence = [
        item for item in case_payload.get("focused_evidence", []) if isinstance(item, dict)
    ]
    failing_counts = {
        str(key): int(value)
        for key, value in case_payload.get("failing_check_counts", {}).items()
        if isinstance(key, str)
    }
    closure_passed = bool(case_payload.get("promotion_ready")) and not failing_counts
    stale_failing = sorted(
        {
            f"{item.get('gate_scenario_id')}:{item.get('solver_mode')}"
            for item in stale_evidence
            if not bool(item.get("threshold_passed"))
        }
    )
    evidence = (
        {
            "gate_scenario_id": case_id,
            "passed": closure_passed,
            "threshold_passed": closure_passed,
            "accepted_for_geometry": closure_passed,
            "diagnostic_only": False,
            "failing_checks": sorted(failing_counts),
            "milestone18_report": str(report_path),
            "focused_evidence_count": len(focused_evidence),
            "focused_pass_count": sum(1 for item in focused_evidence if bool(item.get("passed"))),
            "superseded_stale_blockers": stale_failing,
        },
    )
    notes = [
        f"Milestone 18 remaining-geometry closure evidence applied from {report_path}.",
        "Uses compact rollup evidence; detailed focused diagnostics remain in the Milestone 18 report.",
    ]
    if stale_failing:
        notes.append(
            "Supersedes stale Milestone 16 threshold blockers for: "
            f"{', '.join(stale_failing)}."
        )
    if not closure_passed:
        notes.append("Remaining-geometry closure report is not promotion-ready for this family.")
    for note in case_payload.get("notes", []):
        if isinstance(note, str) and note.startswith("Focused passing evidence supersedes"):
            notes.append(note)
    solver_modes = tuple(
        str(item)
        for item in case_payload.get("solver_modes", [])
        if isinstance(item, str)
    ) or ("focused_closure",)
    return Milestone16GeometryCaseResult(
        case_id=case_id,
        title=title,
        scenarios=scenario_ids,
        solver_modes=solver_modes,
        passed=closure_passed,
        evidence=evidence,
        notes=tuple(dict.fromkeys(notes)),
    )


def _milestone18_geometry_closure_case(
    case_id: str,
    title: str,
    scenario_ids: tuple[str, ...],
    stale_evidence: tuple[dict[str, object], ...],
    milestone18_report_dir: Path | None,
) -> Milestone16GeometryCaseResult | None:
    spec = MILESTONE18_GEOMETRY_CLOSURE_REPORTS.get(case_id)
    if spec is None or milestone18_report_dir is None:
        return None
    report_path = milestone18_report_dir / str(spec["report"])
    if not report_path.exists():
        return None

    report = _read_json(report_path)
    accepted_modes = set(str(mode) for mode in spec["accepted_solver_modes"])
    diagnostic_modes = set(str(mode) for mode in spec["diagnostic_solver_modes"])
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    promoted_modes = set(str(mode) for mode in summary.get("promoted_modes", []) if isinstance(mode, str))
    blocked_modes = set(str(mode) for mode in summary.get("blocked_modes", []) if isinstance(mode, str))
    closure_passed = bool(accepted_modes) and accepted_modes.issubset(promoted_modes) and blocked_modes.issubset(diagnostic_modes)
    evidence = tuple(
        _milestone18_geometry_evidence_row(
            report,
            mode_result,
            report_path,
            accepted_modes=accepted_modes,
            diagnostic_modes=diagnostic_modes,
        )
        for mode_result in report.get("mode_results", [])
        if isinstance(mode_result, dict)
    )
    solver_modes = tuple(sorted({str(item["solver_mode"]) for item in evidence}))
    stale_failing = sorted(
        {
            f"{item.get('gate_scenario_id')}:{item.get('solver_mode')}"
            for item in stale_evidence
            if not bool(item.get("threshold_passed"))
        }
    )
    notes = [
        f"Milestone 18 closure evidence applied from {report_path}.",
        (
            "Accepted solver modes for this geometry family: "
            f"{', '.join(sorted(accepted_modes))}."
        ),
    ]
    if diagnostic_modes:
        notes.append(
            "Diagnostic-only solver modes are retained as smoke evidence but no longer block this geometry family: "
            f"{', '.join(sorted(diagnostic_modes))}."
        )
    if stale_failing:
        notes.append(
            "Supersedes stale Milestone 16 threshold blockers for: "
            f"{', '.join(stale_failing)}."
        )
    if not closure_passed:
        unresolved = sorted(blocked_modes - diagnostic_modes)
        if unresolved:
            notes.append(f"Unresolved accepted-mode blockers remain in: {', '.join(unresolved)}.")
    return Milestone16GeometryCaseResult(
        case_id=case_id,
        title=title,
        scenarios=scenario_ids,
        solver_modes=solver_modes,
        passed=closure_passed and bool(evidence),
        evidence=evidence,
        notes=tuple(notes),
    )


def _milestone18_geometry_evidence_row(
    report: dict[str, object],
    mode_result: dict[str, object],
    report_path: Path,
    *,
    accepted_modes: set[str],
    diagnostic_modes: set[str],
) -> dict[str, object]:
    solver_mode = str(mode_result.get("solver_mode", "unknown"))
    promoted = bool(mode_result.get("promoted"))
    diagnostic_only = solver_mode in diagnostic_modes
    failing_checks = tuple(str(check) for check in mode_result.get("failing_checks", []) if isinstance(check, str))
    return {
        "gate_scenario_id": report.get("scenario_family", report.get("gate_scenario_id")),
        "actual_scenario_id": report.get("actual_scenario_id"),
        "solver_mode": solver_mode,
        "passed": promoted,
        "threshold_passed": promoted,
        "promoted": promoted,
        "accepted_for_geometry": solver_mode in accepted_modes and promoted,
        "diagnostic_only": diagnostic_only,
        "failing_checks": list(failing_checks),
        "candidate_label": mode_result.get("candidate_label"),
        "comparison_dir": mode_result.get("comparison_dir"),
        "threshold_report": mode_result.get("threshold_report"),
        "milestone18_report": str(report_path),
    }


def _reach_drop_handoff_geometry_case(geoclaw_report: dict[str, object]) -> Milestone16GeometryCaseResult:
    evidence: list[dict[str, object]] = []
    notes: list[str] = []
    for record in geoclaw_report["records"]:
        if record["suite"] != "cascading":
            continue
        package = read_cascading_scenario_package(Path(str(record["export_dir"])) / "shared_cascading_package")
        handoff = evaluate_cascading_handoff_conservation(package)
        evidence.append(
            {
                "gate_scenario_id": record["gate_scenario_id"],
                "passed": handoff.passed,
                "check_count": len(handoff.checks),
                "checks": [check.to_json_dict() for check in handoff.checks],
                "geoclaw_reach_windows": record["reach_window_count"],
                "geoclaw_drop_transition_windows": record["drop_transition_window_count"],
            }
        )
        if not handoff.passed:
            notes.append(f"Handoff conservation failed for {record['gate_scenario_id']}.")
    passed = bool(evidence) and all(bool(item["passed"]) for item in evidence)
    return Milestone16GeometryCaseResult(
        case_id="stitched_reach_drop_handoffs",
        title="Stitched Reach/Drop Boundary Handoffs",
        scenarios=tuple(str(item["gate_scenario_id"]) for item in evidence),
        solver_modes=("geoclaw", "package"),
        passed=passed,
        evidence=tuple(evidence),
        notes=tuple(notes),
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
    notes = _raft_coupling_failure_notes(
        reference_result,
        candidate_result,
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
        feature_outcome_match=reference_canonical == candidate_canonical,
        force_envelope_outcome_match=force_comparison.outcome_match,
        force_delta_weight_ratio=force_comparison.force_delta.magnitude / weight,
        torque_delta_inertia_ratio=force_comparison.torque_delta.magnitude / inertia_scale,
        trajectory_position_delta_m=force_comparison.trajectory_position_delta,
        trajectory_velocity_delta_mps=force_comparison.trajectory_velocity_delta,
        reference_checks=_feature_checks_json(reference_result),
        candidate_checks=_feature_checks_json(candidate_result),
        notes=notes,
    )


def _raft_coupling_failure_notes(
    reference_result: FeatureValidationResult,
    candidate_result: FeatureValidationResult,
    feature_outcome_match: bool,
    force_envelope_outcome_match: bool,
    force_delta_weight_ratio: float,
    torque_delta_inertia_ratio: float,
    trajectory_position_delta: float,
    trajectory_velocity_delta: float,
) -> tuple[str, ...]:
    notes: list[str] = []
    if not reference_result.passed:
        notes.append("GeoClaw-derived raft feature checks are not passing.")
    if not candidate_result.passed:
        notes.append("C++ raft feature checks are not passing.")
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


def _feature_by_role_or_kind(scenario: Scenario2_5D, kind: str, role: str):
    for feature in scenario.features:
        if feature.kind == kind and feature.metadata.get("geoclaw_case_role") == role:
            return feature
    for feature in reversed(scenario.features):
        if feature.kind == kind:
            return feature
    raise ValueError(f"Scenario {scenario.metadata.scenario_id} does not include feature {kind!r}.")


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


def _last_manifest_frame_path(manifest_path: Path) -> Path:
    manifest = _read_json(manifest_path)
    frames = manifest.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ValueError(f"Manifest {manifest_path} does not contain frames.")
    return manifest_path.parent / Path(str(frames[-1]))


def _promote_geoclaw_cpp_regression(
    record: dict[str, object],
    source_report: Path,
    fixture_root: Path,
) -> Milestone16RegressionPromotionEntry:
    gate_id = str(record["gate_scenario_id"])
    solver_mode = str(record["solver_mode"])
    comparison_dir = Path(str(record["comparison_dir"]))
    manifest_path = comparison_dir / "dual_solver_manifest.json"
    threshold_path = comparison_dir / "threshold_evaluation.json"
    manifest = _read_json(manifest_path)
    threshold = _read_json(threshold_path)
    if not bool(threshold.get("passed")):
        raise ValueError(f"Refusing to promote failed comparison artifact: {comparison_dir}")

    artifact_dir = fixture_root / "geoclaw_cpp" / _case_dir(gate_id) / solver_mode
    scenario_target = artifact_dir / "scenario"
    reports_target = artifact_dir / "reports"
    scenario_source = Path(str(manifest["scenario_package"]))
    if scenario_target.exists():
        shutil.rmtree(scenario_target)
    shutil.copytree(scenario_source, scenario_target)
    reports_target.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name in (
        "dual_solver_manifest.json",
        "threshold_evaluation.json",
        "field_comparison.json",
        "probe_comparison.json",
        "diagnostic_comparison.json",
        "feature_comparison.json",
    ):
        source = comparison_dir / name
        if source.exists():
            target = reports_target / name
            shutil.copy2(source, target)
            reports[Path(name).stem] = str(target)

    return Milestone16RegressionPromotionEntry(
        artifact_id=f"geoclaw_cpp/{gate_id}/{solver_mode}",
        category="geoclaw_cpp",
        gate_scenario_id=gate_id,
        actual_scenario_id=str(record["actual_scenario_id"]),
        suite=str(record["suite"]),
        solver_mode=solver_mode,
        artifact_dir=str(artifact_dir),
        source_report=str(source_report),
        passed=True,
        scenario_package=str(scenario_target),
        manifest=str(reports_target / "dual_solver_manifest.json"),
        reports=reports,
    )


def _should_promote_geometry_case(case: dict[str, object]) -> bool:
    if not bool(case.get("passed")):
        return False
    case_id = str(case.get("case_id"))
    return (
        case_id == "stitched_reach_drop_handoffs"
        or case_id in MILESTONE18_GEOMETRY_CLOSURE_REPORTS
        or case_id in MILESTONE18_REMAINING_GEOMETRY_CLOSURE_CASES
    )


def _should_promote_geometry_evidence(evidence: dict[str, object]) -> bool:
    return bool(evidence.get("passed")) and not bool(evidence.get("diagnostic_only"))


def _promote_geometry_validation_artifact(
    case: dict[str, object],
    evidence: dict[str, object],
    source_report: Path,
    fixture_root: Path,
) -> Milestone16RegressionPromotionEntry:
    case_id = str(case["case_id"])
    gate_id = str(evidence.get("gate_scenario_id", case_id))
    mode_specific = evidence.get("milestone18_report") is not None and evidence.get("solver_mode") is not None
    solver_mode = str(evidence.get("solver_mode")) if mode_specific else "geoclaw_package"
    artifact_dir = fixture_root / "geometry_validation" / case_id / _case_dir(gate_id)
    if mode_specific:
        artifact_dir = artifact_dir / solver_mode
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "geometry_case.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": MILESTONE16_REGRESSION_REGISTRY_SCHEMA,
                "source_report": str(source_report),
                "case_id": case_id,
                "title": case.get("title"),
                "gate_scenario_id": gate_id,
                "scenarios": case.get("scenarios", []),
                "solver_modes": case.get("solver_modes", []),
                "evidence": evidence,
                "passed": True,
                **(
                    {"milestone18_closure_report": evidence["milestone18_report"]}
                    if evidence.get("milestone18_report") is not None
                    else {}
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return Milestone16RegressionPromotionEntry(
        artifact_id=(
            f"geometry_validation/{case_id}/{gate_id}/{solver_mode}"
            if mode_specific
            else f"geometry_validation/{case_id}/{gate_id}"
        ),
        category="geometry_validation",
        gate_scenario_id=gate_id,
        actual_scenario_id=str(evidence.get("actual_scenario_id", gate_id)),
        suite="cascading" if gate_id.startswith("south_fork_cascading") else "geometry",
        solver_mode=solver_mode,
        artifact_dir=str(artifact_dir),
        source_report=str(source_report),
        passed=True,
        case_id=case_id,
        manifest=str(manifest_path),
        reports={"geometry_case": str(manifest_path)},
        notes=_geometry_artifact_notes(case_id, evidence),
    )


def _geometry_artifact_notes(case_id: str, evidence: dict[str, object]) -> tuple[str, ...]:
    if case_id == "stitched_reach_drop_handoffs":
        return ("Preserves seam-visible reach/drop handoff diagnostics from the geometry validation report.",)
    note = "Preserves Milestone 18 focused geometry closure evidence in the aggregate Milestone 16 regression manifest."
    if bool(evidence.get("diagnostic_only")):
        return (
            note,
            "This solver mode remains diagnostic-only and does not approve live-water use by itself.",
        )
    return (note,)


def _promote_raft_coupling_artifact(
    record: dict[str, object],
    source_report: Path,
    fixture_root: Path,
) -> Milestone16RegressionPromotionEntry:
    gate_id = str(record["gate_scenario_id"])
    solver_mode = str(record["solver_mode"])
    case_id = str(record["case_id"])
    artifact_dir = fixture_root / "raft_coupling" / _case_dir(gate_id) / solver_mode / case_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "raft_coupling_case.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": MILESTONE16_REGRESSION_REGISTRY_SCHEMA,
                "source_report": str(source_report),
                "record": record,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return Milestone16RegressionPromotionEntry(
        artifact_id=f"raft_coupling/{gate_id}/{solver_mode}/{case_id}",
        category="raft_coupling",
        gate_scenario_id=gate_id,
        actual_scenario_id=str(record["actual_scenario_id"]),
        suite=str(record["suite"]),
        solver_mode=solver_mode,
        artifact_dir=str(artifact_dir),
        source_report=str(source_report),
        passed=True,
        case_id=case_id,
        manifest=str(manifest_path),
        reports={"raft_coupling_case": str(manifest_path)},
        notes=("Frame paths remain in generated Milestone 16 output directories.",),
    )


def _runtime_budget_results(runtime_ms_per_tick: float, budgets: dict[str, object]) -> dict[str, dict[str, object]]:
    profiles = budgets.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("Runtime budget config must include a profiles object.")
    results: dict[str, dict[str, object]] = {}
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        budget_ms = float(profile["water_solver_ms"])
        max_runtime_multiplier = float(profile.get("max_runtime_multiplier", 1.0))
        results[str(profile_name)] = {
            "passed": runtime_ms_per_tick <= budget_ms,
            "runtime_ms_per_tick": runtime_ms_per_tick,
            "water_solver_budget_ms": budget_ms,
            "max_runtime_budget_ms": budget_ms * max_runtime_multiplier,
            "max_runtime_multiplier": max_runtime_multiplier,
        }
    return results


def _cpp_run_frame_hash(manifest_path: Path) -> str:
    manifest = _read_json(manifest_path)
    frames = manifest.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ValueError(f"C++ manifest {manifest_path} does not include frames.")
    digest = sha256()
    for frame in frames:
        frame_path = manifest_path.parent / Path(str(frame))
        digest.update(frame_path.name.encode("utf-8"))
        digest.update(frame_path.read_bytes())
    return digest.hexdigest()


def _artifact_path_fragment(artifact_id: str) -> Path:
    return Path(*[part for part in artifact_id.split("/") if part])


def _write_milestone16_comparison_manifest(
    root: Path,
    geoclaw_record: dict[str, object],
    cpp_record: dict[str, object],
) -> Path:
    export_dir = Path(str(geoclaw_record["export_dir"])).resolve()
    if geoclaw_record["suite"] == "cascading":
        scenario_package = export_dir / "shared_cascading_package"
        geoclaw_output = export_dir / "normalized_cascading" / "stitched"
    else:
        scenario_package = export_dir / "shared_scenario"
        geoclaw_output = export_dir / "normalized"
    run_manifest = _read_json(export_dir / "geoclaw_run_manifest.json")
    geoclaw_runtime = float(run_manifest.get("result", {}).get("runtime_seconds", 0.0))
    cpp_output_dir = Path(str(cpp_record["output_dir"])).resolve()
    cpp_runtime = float(cpp_record["runtime_seconds"])
    scenario = _read_json(scenario_package / "scenario.json")
    duration = float(scenario["duration"])
    manifest = {
        "scenario_id": cpp_record["actual_scenario_id"],
        "scenario_package": str(scenario_package),
        "scenario_json": str(scenario_package / "scenario.json"),
        "geoclaw": {
            "solver": "geoclaw",
            "output_dir": str(geoclaw_output),
            "manifest": str(geoclaw_output / "manifest.json"),
            "validation": str(geoclaw_output / "validation.json"),
            "runtime_seconds": geoclaw_runtime,
            "seconds_per_simulated_second": geoclaw_runtime / max(duration, 1.0e-12),
        },
        "cpp": {
            "command": [],
            "returncode": cpp_record["returncode"],
            "stdout": "",
            "stderr": "",
            "output_dir": str(cpp_output_dir),
            "manifest": str(Path(str(cpp_record["manifest"])).resolve()),
            "validation": str(Path(str(cpp_record["validation"])).resolve()),
            "runtime_seconds": cpp_runtime,
        },
        "runtime": {
            "simulated_duration_seconds": duration,
            "geoclaw_runtime_seconds": geoclaw_runtime,
            "geoclaw_seconds_per_simulated_second": geoclaw_runtime / max(duration, 1.0e-12),
            "cpp_runtime_seconds": cpp_runtime,
            "cpp_seconds_per_simulated_second": cpp_runtime / max(duration, 1.0e-12),
        },
    }
    manifest_path = root / "dual_solver_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def _threshold_tier_for_gate(gate_scenario_id: str) -> str:
    for scenario in CUSTOM_CPP_VALIDATION_SCENARIOS:
        if scenario.scenario_id == gate_scenario_id:
            return scenario.threshold_tier
    raise KeyError(f"Unknown validation gate scenario: {gate_scenario_id}")


def _thresholds_for_gate(gate_scenario_id: str) -> ScenarioThresholds:
    tier_id = _threshold_tier_for_gate(gate_scenario_id)
    tier = next(item for item in CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS if item.tier_id == tier_id)
    return ScenarioThresholds(
        max_field_linf=tier.field_linf_max_m,
        max_slope_linf=tier.slope_linf_max,
        max_wet_mismatch_fraction=tier.wet_mismatch_max_fraction,
        max_probe_linf=tier.probe_linf_max,
        max_cross_section_linf=tier.cross_section_linf_max,
        max_mass_drift_delta=tier.mass_relative_drift_max,
        max_energy_change_delta=tier.energy_relative_change_delta_max,
        max_froude_delta=tier.froude_class_mismatch_max_fraction,
        max_feature_location_delta=tier.feature_location_max_m,
        max_feature_strength_delta=tier.feature_strength_linf_max,
    )


def _reach_drop_check(geoclaw_record: dict[str, object], cpp_record: dict[str, object]) -> dict[str, object]:
    if geoclaw_record["suite"] != "cascading":
        return {"required": False, "passed": True}
    cpp_cascading = cpp_record.get("cascading", {})
    if not isinstance(cpp_cascading, dict):
        cpp_cascading = {}
    expected_reaches = int(geoclaw_record.get("reach_window_count", 0))
    expected_drops = int(geoclaw_record.get("drop_transition_window_count", 0))
    actual_reaches = int(cpp_cascading.get("reach_count", 0))
    actual_drops = int(cpp_cascading.get("drop_transition_count", 0))
    return {
        "required": True,
        "passed": expected_reaches == actual_reaches and expected_drops == actual_drops,
        "geoclaw_reach_windows": expected_reaches,
        "cpp_reach_count": actual_reaches,
        "geoclaw_drop_transition_windows": expected_drops,
        "cpp_drop_transition_count": actual_drops,
    }


def _run_standard_geoclaw_case(
    root: Path,
    gate_scenario_id: str,
    suite: str,
    scenario: Scenario2_5D,
    export_config: GeoClawExportConfig,
    run_config: GeoClawRunConfig,
    *,
    flow_band: str | None = None,
) -> Milestone16GeoClawRunRecord:
    case_root = root / _case_dir(gate_scenario_id)
    export = export_geoclaw_scenario(scenario, case_root, config=export_config)
    run = run_geoclaw_export(export.output_dir, config=run_config, export_config=export_config)
    normalized_manifest: Path | None = None
    normalized_mode: str | None = None
    notes: list[str] = []
    if run.returncode == 0 and run.extraction_error is None and run.frame_count > 0:
        normalized = normalize_geoclaw_fixed_grid_output(export.output_dir, export.output_dir / "normalized", config=export_config)
        normalized_manifest = normalized.manifest_path
        normalized_payload = _read_json(normalized.manifest_path)
        normalized_mode = str(normalized_payload.get("run_status", {}).get("mode"))
    else:
        notes.append("GeoClaw execution failed; normalized frames were not generated.")
    if run.extraction_error is not None:
        notes.append(f"GeoClaw fixed-grid extraction failed: {run.extraction_error}")
    full_solution = run.frame_count > 0 and normalized_mode == "fgout_npz"
    if not full_solution:
        notes.append("Full fixed-grid solution frames are missing.")
    return Milestone16GeoClawRunRecord(
        gate_scenario_id=gate_scenario_id,
        actual_scenario_id=scenario.metadata.scenario_id,
        suite=suite,
        flow_band=flow_band,
        export_dir=str(export.output_dir),
        run_manifest=str(export.output_dir / "geoclaw_run_manifest.json"),
        normalized_manifest=str(normalized_manifest) if normalized_manifest is not None else None,
        normalized_mode=normalized_mode,
        returncode=run.returncode,
        runtime_seconds=run.runtime_seconds,
        frame_count=run.frame_count,
        full_solution=full_solution,
        notes=tuple(notes),
    )


def _run_cascading_geoclaw_case(
    root: Path,
    gate_scenario_id: str,
    package,
    export_config: GeoClawExportConfig,
    run_config: GeoClawRunConfig,
    *,
    flow_band: str | None,
) -> Milestone16GeoClawRunRecord:
    case_root = root / _case_dir(gate_scenario_id)
    export = export_geoclaw_cascading_package(package, case_root, config=export_config)
    run = run_geoclaw_export(export.output_dir, config=run_config, export_config=export_config)
    normalized_manifest: Path | None = None
    normalized_mode: str | None = None
    reach_window_count = 0
    drop_transition_window_count = 0
    notes: list[str] = []
    if run.returncode == 0 and run.extraction_error is None and run.frame_count > 0:
        normalized = normalize_geoclaw_cascading_fixed_grid_output(
            export.output_dir,
            export.output_dir / "normalized_cascading",
            config=export_config,
        )
        normalized_manifest = normalized.stitched_manifest_path
        normalized_payload = _read_json(normalized.stitched_manifest_path)
        normalized_mode = str(normalized_payload.get("run_status", {}).get("mode"))
        reach_window_count = normalized.reach_window_count
        drop_transition_window_count = normalized.drop_transition_window_count
    else:
        notes.append("GeoClaw execution failed; cascading normalized windows were not generated.")
    if run.extraction_error is not None:
        notes.append(f"GeoClaw fixed-grid extraction failed: {run.extraction_error}")
    full_solution = run.frame_count > 0 and normalized_mode == "fgout_npz"
    if not full_solution:
        notes.append("Full fixed-grid solution frames are missing.")
    return Milestone16GeoClawRunRecord(
        gate_scenario_id=gate_scenario_id,
        actual_scenario_id=package.scenario.metadata.scenario_id,
        suite="cascading",
        flow_band=flow_band,
        export_dir=str(export.output_dir),
        run_manifest=str(export.output_dir / "geoclaw_run_manifest.json"),
        normalized_manifest=str(normalized_manifest) if normalized_manifest is not None else None,
        normalized_mode=normalized_mode,
        returncode=run.returncode,
        runtime_seconds=run.runtime_seconds,
        frame_count=run.frame_count,
        full_solution=full_solution,
        reach_window_count=reach_window_count,
        drop_transition_window_count=drop_transition_window_count,
        notes=tuple(notes),
    )


def _cpp_config_for_mode(
    executable: Path,
    solver_mode: str,
    *,
    gate_scenario_id: str | None = None,
) -> CppSolverRunConfig:
    finite_volume = solver_mode == "finite_volume"
    flux_scheme = "hll" if finite_volume else "rusanov"
    roughness_scale = 0.5 if finite_volume else 1.0
    bed_slope_source_scale = 0.75 if finite_volume else 0.0
    preserve_initial_mass = not finite_volume
    if finite_volume and gate_scenario_id == "uniform_channel":
        roughness_scale = 0.35
        bed_slope_source_scale = 0.65
    if not finite_volume and gate_scenario_id == "uniform_channel":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "bed_step":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "constriction":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "drop_ledge":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "boulder_garden":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "cascading_wave_train":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "hydraulic_hole_downstream_boil":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "lateral_wave":
        preserve_initial_mass = False
    if not finite_volume and gate_scenario_id == "eddy_line_shear":
        preserve_initial_mass = False
    if finite_volume and gate_scenario_id == "bed_step":
        flux_scheme = "roe"
    return CppSolverRunConfig(
        executable=executable,
        solver_mode=solver_mode,
        boundary_mode="scenario",
        flux_scheme=flux_scheme,
        cfl=0.45,
        dry_tolerance=1.0e-6,
        feature_strength_scale=0.0,
        roughness_scale=roughness_scale,
        bed_slope_source_scale=bed_slope_source_scale,
        preserve_initial_mass=preserve_initial_mass,
        allow_validation_failure=True,
    )


def _cpp_record_from_result(
    geoclaw_record: dict[str, object],
    *,
    solver_mode: str,
    scenario_package: Path,
    result,
) -> Milestone16CppRunRecord:
    manifest = _read_json(result.manifest_path)
    validation = _read_json(result.validation_path)
    required_settings = (
        "solver",
        "solver_mode",
        "boundary_mode",
        "flux_scheme",
        "cfl",
        "dry_tolerance",
        "feature_strength_scale",
        "roughness_scale",
        "bed_slope_source_scale",
        "cascading",
    )
    return Milestone16CppRunRecord(
        gate_scenario_id=str(geoclaw_record["gate_scenario_id"]),
        actual_scenario_id=str(geoclaw_record["actual_scenario_id"]),
        suite=str(geoclaw_record["suite"]),
        solver_mode=solver_mode,
        scenario_package=str(scenario_package),
        output_dir=str(result.output_dir),
        manifest=str(result.manifest_path),
        validation=str(result.validation_path),
        returncode=result.returncode,
        runtime_seconds=result.runtime_seconds,
        frame_count=len(manifest.get("frames", [])),
        validation_passed=bool(validation.get("passed")),
        manifest_settings={
            "solver": manifest.get("solver"),
            "solver_mode": manifest.get("solver_mode"),
            "boundary_mode": manifest.get("boundary_mode"),
            "flux_scheme": manifest.get("flux_scheme"),
            "cfl": manifest.get("cfl"),
            "dry_tolerance": manifest.get("dry_tolerance"),
            "feature_strength_scale": manifest.get("feature_strength_scale"),
            "roughness_scale": manifest.get("roughness_scale"),
            "bed_slope_source_scale": manifest.get("bed_slope_source_scale"),
            "preserve_initial_mass": manifest.get("preserve_initial_mass"),
        },
        cascading=dict(manifest.get("cascading", {})),
        required_manifest_fields_present=all(name in manifest for name in required_settings),
    )


def _case_dir(gate_scenario_id: str) -> str:
    return MILESTONE16_CASE_DIRS.get(gate_scenario_id, gate_scenario_id[:32])


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
