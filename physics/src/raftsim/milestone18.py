"""Milestone 18 validation-closure triage artifacts."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .analytic_validation import AnalyticCandidateKind, AnalyticValidationReport, compare_analytic_fixture_manifest
from .feature_validation import build_crew_overboard_fixtures2_5d, evaluate_crew_overboard_fixture2_5d
from .math3d import Vec3
from .raft_coupling2_5d import (
    CrewAction2_5D,
    CrewWeightTelemetry2_5D,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
    evaluate_crew_weight_distribution2_5d,
)

MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA = "raftsim.milestone18.failure_triage_matrix.v0"
MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA = "raftsim.milestone18.analytic_retune_guardrail.v0"
MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA = "raftsim.milestone18.parity_family_retune.v0"
MILESTONE18_PIN_RELEASE_REPORT_SCHEMA = "raftsim.milestone18.pin_release_fixture.v0"
MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA = "raftsim.milestone18.constriction_throat_shape.v0"
MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA = "raftsim.milestone18.constriction_mask_alignment.v0"

_CORE_GUARDRAIL_FAMILIES = {"hydrostatic_sloping_balance", "uniform_channel", "dam_break_bore"}
_GEOMETRY_CLOSURE_FAMILIES = {"wet_dry_shoreline", "bed_step", "constriction", "drops_ledges_tailwater"}

_SCENARIO_FAMILY_OVERRIDES = {
    "flat_pool": "hydrostatic_sloping_balance",
    "sloping_manning_channel": "hydrostatic_sloping_balance",
    "uniform_channel": "uniform_channel",
    "dam_break": "dam_break_bore",
    "wet_dry_shoreline": "wet_dry_shoreline",
    "bed_step": "bed_step",
    "constriction": "constriction",
    "drop_ledge": "drops_ledges_tailwater",
    "boulder_garden": "boulder_impacts",
    "cascading_wave_train": "wave_train",
    "hydraulic_hole_downstream_boil": "hydraulic_hole_boil",
    "lateral_wave": "lateral_wave",
    "eddy_line_shear": "eddy_line",
    "shallow_shelf": "shallow_shelf",
    "south_fork_low_runnable": "real_world_single_reach",
    "south_fork_median_runnable": "real_world_single_reach",
    "south_fork_high_runnable": "real_world_single_reach",
    "south_fork_cascading_low_runnable": "cascading_reach_drop",
    "south_fork_cascading_median_runnable": "cascading_reach_drop",
    "south_fork_cascading_high_runnable": "cascading_reach_drop",
}

_RAFT_CASE_FAMILY_OVERRIDES = {
    "pool_entry": "pool_entry",
    "drop_entry": "drops_ledges_tailwater",
    "hydraulic_hole_surf_flush": "hydraulic_hole_boil",
    "downstream_boil_recovery": "hydraulic_hole_boil",
    "eddy_recovery": "eddy_line",
    "boulder_impacts": "boulder_impacts",
    "boulder_garden_impacts": "boulder_impacts",
    "shallow_shelf_pivot_release": "shallow_shelf",
    "transition_boundary_crossing": "cascading_reach_drop",
    "wave_train_surf_flush": "wave_train",
    "lateral_wave_side_impulse": "lateral_wave",
}

_METRIC_TRIAGE = {
    "field_linf": (
        "field_state",
        "C++ depth, surface, momentum, or normal fields diverge from the GeoClaw reference.",
        "Inspect finite-volume/reduced update, bed-source balance, reconstruction, CFL, dry-depth handling, and bathymetry alignment.",
    ),
    "slope_linf": (
        "surface_slope",
        "Free-surface slope differs enough to change hydraulic controls and raft force sampling.",
        "Retune bed-slope source scaling, slope reconstruction, smoothing, and limiter behavior before feature forcing.",
    ),
    "probe_linf": (
        "localized_probe",
        "Point probes see a localized water-state mismatch that may be hidden in whole-field summaries.",
        "Check probe placement, interpolation, frame timing, local bathymetry, velocity masks, and water-query sampling.",
    ),
    "cross_section_linf": (
        "cross_section",
        "Cross-section profiles disagree, indicating reach-scale shape, velocity, or water-surface drift.",
        "Compare section alignment, width/depth profiles, roughness mapping, and cross-section sampling windows.",
    ),
    "wet_mismatch_fraction": (
        "wet_dry_mask",
        "GeoClaw and C++ disagree on wet/dry cells, usually near shorelines, shelves, banks, or shallow eddies.",
        "Tune dry tolerance, positivity preservation, shoreline velocity masking, bed roughness, and shallow-cell damping.",
    ),
    "mass_drift_delta": (
        "conservation",
        "Mass conservation differs between GeoClaw and C++ for the same scenario package.",
        "Audit fluxes, boundary conditions, source splitting, reach/drop handoff fluxes, and dry-cell volume accounting.",
    ),
    "energy_change_delta": (
        "energy_dissipation",
        "Energy gain/loss differs, which can move bores, jumps, drops, and hole stickiness.",
        "Retune roughness, damping, hydraulic-jump/drop dissipation, tailwater controls, and feature forcing only after conservation is stable.",
    ),
    "froude_delta": (
        "hydraulic_regime",
        "Froude-class or velocity/depth behavior differs across subcritical/supercritical transitions.",
        "Check momentum flux, velocity depth floors, wet-cell masks, roughness, and transcritical control behavior.",
    ),
    "feature_location_delta": (
        "feature_localization",
        "The strongest modeled feature appears in a different place than the GeoClaw-derived reference.",
        "Verify bathymetry registration, reach/drop transforms, feature probes, flow band selection, and authored feature anchors.",
    ),
    "feature_strength_delta": (
        "feature_strength",
        "The modeled feature strength differs, affecting holes, laterals, eddies, waves, shelves, and boulder response.",
        "Retune roughness, damping, feature response curves, and low-default forcing after base conservation and geometry pass.",
    ),
}

_GEOMETRY_TRIAGE = {
    "wet_dry_shoreline": (
        "Wet/dry front handling is still unstable against GeoClaw evidence.",
        "Prioritize dry tolerance, shoreline velocity masking, positivity preservation, and shallow-cell damping.",
    ),
    "bed_step": (
        "Discontinuous bed elevation is exposing source-term and free-surface balance error.",
        "Audit hydrostatic reconstruction, bed-step source treatment, mass flux, and local dissipation.",
    ),
    "constriction": (
        "Narrow-section acceleration and Froude transitions are not matching GeoClaw.",
        "Retune width/depth mapping, momentum flux, roughness, and constriction feature-strength response.",
    ),
    "drops_ledges_tailwater": (
        "Drop, ledge, tailwater, or cascading transition behavior is still outside thresholds.",
        "Tune drop energy loss, tailwater depth controls, hydraulic control placement, and stitched reach/drop conservation.",
    ),
}


@dataclass(frozen=True, slots=True)
class Milestone18FailureTriageEntry:
    """One actionable row in the Milestone 18 failure matrix."""

    entry_id: str
    source_component: str
    source_report: str
    scenario_family: str
    gate_scenario_id: str
    actual_scenario_id: str | None
    suite: str | None
    solver_mode: str | None
    metric: str
    metric_group: str
    severity: str
    dependency_phase: str
    dependency_order: int
    likely_root_cause: str
    retune_lever: str
    observed_value: float | None = None
    threshold: float | None = None
    failed_checks: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["failed_checks"] = list(self.failed_checks)
        data["evidence_refs"] = list(self.evidence_refs)
        data["notes"] = list(self.notes)
        return data


@dataclass(frozen=True, slots=True)
class Milestone18FailureTriageReport:
    """Triage matrix for the blocked Milestone 16 validation evidence."""

    source_reports: dict[str, str]
    entries: tuple[Milestone18FailureTriageEntry, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not self.entries

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "ACTION_REQUIRED",
            "source_reports": self.source_reports,
            "summary": {
                "entry_count": len(self.entries),
                "by_source_component": _counter_json(entry.source_component for entry in self.entries),
                "by_scenario_family": _counter_json(entry.scenario_family for entry in self.entries),
                "by_solver_mode": _counter_json(entry.solver_mode or "component" for entry in self.entries),
                "by_metric_group": _counter_json(entry.metric_group for entry in self.entries),
                "by_dependency_phase": _counter_json(entry.dependency_phase for entry in self.entries),
                "by_severity": _counter_json(entry.severity for entry in self.entries),
            },
            "groups": _group_entries(self.entries),
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 GeoClaw/C++ Failure Triage Matrix",
            "",
            f"Schema: `{MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'ACTION REQUIRED'}**",
            "",
            f"Entry count: {len(self.entries)}",
            "",
            "## Source Reports",
            "",
        ]
        for key, value in self.source_reports.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(
            [
                "",
                "## Summary",
                "",
                _markdown_counter_table("Source component", summary["by_source_component"]),
                "",
                _markdown_counter_table("Scenario family", summary["by_scenario_family"]),
                "",
                _markdown_counter_table("Metric group", summary["by_metric_group"]),
                "",
                "## Dependency Order",
                "",
                "| Order | Phase | Entries |",
                "| ---: | --- | ---: |",
            ]
        )
        phase_counts = Counter(entry.dependency_phase for entry in self.entries)
        for order, phase in _dependency_phase_order():
            if phase_counts.get(phase):
                lines.append(f"| {order} | {phase} | {phase_counts[phase]} |")

        lines.extend(
            [
                "",
                "## Matrix",
                "",
                "| Phase | Family | Scenario | Mode | Metric | Severity | Value | Threshold | Root-cause hypothesis | Retune lever |",
                "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for entry in self.entries:
            lines.append(
                "| "
                f"{entry.dependency_phase} | "
                f"{entry.scenario_family} | "
                f"{entry.gate_scenario_id} | "
                f"{entry.solver_mode or 'n/a'} | "
                f"{entry.metric} | "
                f"{entry.severity} | "
                f"{_format_number(entry.observed_value)} | "
                f"{_format_number(entry.threshold)} | "
                f"{_escape_table(entry.likely_root_cause)} | "
                f"{_escape_table(entry.retune_lever)} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18AnalyticGuardrailStage:
    """Preflight or postflight analytic-fixture validation evidence."""

    stage: str
    report_json: str
    report_markdown: str
    candidate_kind: str
    candidate_label: str
    candidate_root: str | None
    frame_index: int
    passed: bool
    fixture_count: int
    passed_count: int
    failed_count: int
    failing_metrics: tuple[dict[str, object], ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["failing_metrics"] = list(self.failing_metrics)
        return data


@dataclass(frozen=True, slots=True)
class Milestone18AnalyticRegression:
    """A metric that passed before retuning and failed after retuning."""

    fixture_id: str
    metric_id: str
    field: str
    preflight_value: float
    postflight_value: float
    threshold: float
    units: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18AnalyticRetuneGuardrailReport:
    """Preflight/postflight guardrail around Milestone 17 analytic fixtures."""

    manifest_path: str
    retune_batch_id: str
    output_dir: str
    preflight: Milestone18AnalyticGuardrailStage
    postflight: Milestone18AnalyticGuardrailStage
    regressions: tuple[Milestone18AnalyticRegression, ...] = ()

    @property
    def passed(self) -> bool:
        return self.preflight.passed and self.postflight.passed and not self.regressions

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.preflight.passed:
            reasons.append("Preflight analytic fixtures are already failing; retuning cannot start from this baseline.")
        if not self.postflight.passed:
            reasons.append("Postflight analytic fixtures failed; reject the retune batch.")
        if self.regressions:
            reasons.append("At least one analytic metric passed preflight and failed postflight.")
        return tuple(reasons)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "manifest_path": self.manifest_path,
            "retune_batch_id": self.retune_batch_id,
            "output_dir": self.output_dir,
            "blocked_reasons": list(self.blocked_reasons),
            "preflight": self.preflight.to_json_dict(),
            "postflight": self.postflight.to_json_dict(),
            "regression_count": len(self.regressions),
            "regressions": [regression.to_json_dict() for regression in self.regressions],
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
            "# Milestone 18 Analytic Retune Guardrail",
            "",
            f"Schema: `{MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Retune batch: `{self.retune_batch_id}`",
            "",
            f"Manifest: `{self.manifest_path}`",
            "",
            "| Stage | Result | Candidate | Fixtures | Failed | Report |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
        for stage in (self.preflight, self.postflight):
            lines.append(
                "| "
                f"{stage.stage} | "
                f"{'PASS' if stage.passed else 'FAIL'} | "
                f"{stage.candidate_label} (`{stage.candidate_kind}`) | "
                f"{stage.fixture_count} | "
                f"{stage.failed_count} | "
                f"`{stage.report_json}` |"
            )
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.regressions:
            lines.extend(
                [
                    "",
                    "## Regressions",
                    "",
                    "| Fixture | Metric | Field | Preflight | Postflight | Threshold |",
                    "| --- | --- | --- | ---: | ---: | ---: |",
                ]
            )
            for regression in self.regressions:
                lines.append(
                    "| "
                    f"{regression.fixture_id} | "
                    f"{regression.metric_id} | "
                    f"{regression.field} | "
                    f"{regression.preflight_value:.6g} | "
                    f"{regression.postflight_value:.6g} | "
                    f"{regression.threshold:.6g} {regression.units} |"
                )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18ParityModeResult:
    """One solver-mode rerun in a Milestone 18 parity-family retune batch."""

    solver_mode: str
    candidate_label: str
    promoted: bool
    threshold_report: str
    comparison_dir: str
    manifest: str | None
    tuning_parameters: dict[str, object]
    failing_checks: tuple[str, ...]
    checks: tuple[dict[str, object], ...]
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "solver_mode": self.solver_mode,
            "candidate_label": self.candidate_label,
            "promoted": self.promoted,
            "threshold_report": self.threshold_report,
            "comparison_dir": self.comparison_dir,
            "manifest": self.manifest,
            "tuning_parameters": self.tuning_parameters,
            "failing_checks": list(self.failing_checks),
            "checks": list(self.checks),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class Milestone18ParityFamilyRetuneReport:
    """Evidence report for rerunning one GeoClaw/C++ parity family."""

    scenario_family: str
    gate_scenario_id: str
    actual_scenario_id: str
    reference_manifest: str
    reference_boundary_semantics: dict[str, object]
    feature_forcing_policy: str
    mode_results: tuple[Milestone18ParityModeResult, ...]
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return bool(self.mode_results) and all(result.promoted for result in self.mode_results)

    @property
    def partially_promoted(self) -> bool:
        return any(result.promoted for result in self.mode_results) and not self.passed

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "PARTIAL_PROMOTION" if self.partially_promoted else "BLOCKED",
            "scenario_family": self.scenario_family,
            "gate_scenario_id": self.gate_scenario_id,
            "actual_scenario_id": self.actual_scenario_id,
            "reference_manifest": self.reference_manifest,
            "reference_boundary_semantics": self.reference_boundary_semantics,
            "feature_forcing_policy": self.feature_forcing_policy,
            "summary": {
                "mode_count": len(self.mode_results),
                "promoted_modes": [result.solver_mode for result in self.mode_results if result.promoted],
                "blocked_modes": [result.solver_mode for result in self.mode_results if not result.promoted],
                "failing_checks_by_mode": {
                    result.solver_mode: list(result.failing_checks) for result in self.mode_results if result.failing_checks
                },
            },
            "mode_results": [result.to_json_dict() for result in self.mode_results],
            "notes": list(self.notes),
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
            "# Milestone 18 Parity Family Retune",
            "",
            f"Schema: `{MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{self.to_json_dict()['decision']}**",
            "",
            f"Scenario family: `{self.scenario_family}`",
            f"Gate scenario: `{self.gate_scenario_id}`",
            f"Actual scenario: `{self.actual_scenario_id}`",
            f"Reference manifest: `{self.reference_manifest}`",
            "",
            "## Boundary Semantics",
            "",
            f"- `bc_lower`: `{self.reference_boundary_semantics.get('bc_lower')}`",
            f"- `bc_upper`: `{self.reference_boundary_semantics.get('bc_upper')}`",
            f"- Requires adapter: `{self.reference_boundary_semantics.get('requires_user_boundary_adapter')}`",
            "",
            "## Mode Results",
            "",
            "| Mode | Candidate | Decision | Failing checks | Key tuning |",
            "| --- | --- | --- | --- | --- |",
        ]
        for result in self.mode_results:
            tuning = ", ".join(f"{key}={value}" for key, value in sorted(result.tuning_parameters.items()))
            failing = ", ".join(result.failing_checks) if result.failing_checks else "none"
            lines.append(
                f"| `{result.solver_mode}` | `{result.candidate_label}` | "
                f"{'PROMOTED' if result.promoted else 'BLOCKED'} | {failing} | `{tuning}` |"
            )
        lines.extend(["", "## Threshold Checks", ""])
        for result in self.mode_results:
            lines.extend([f"### {result.solver_mode}", "", "| Check | Value | Threshold | Result |", "| --- | ---: | ---: | --- |"])
            for check in result.checks:
                lines.append(
                    f"| `{check.get('name')}` | {_format_number(_float_or_none(check.get('value')))} | "
                    f"{_format_number(_float_or_none(check.get('threshold')))} | "
                    f"{'PASS' if check.get('passed') else 'FAIL'} |"
                )
            lines.append("")
        if self.notes:
            lines.extend(["## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)
            lines.append("")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionThroatProfile:
    """One water-shape profile sampled at the constriction throat."""

    label: str
    source_path: str
    column_index: int
    center_row_index: int
    wet_depth_threshold_m: float
    wet_cell_count: int
    wet_width_m: float
    center_depth_m: float
    max_depth_m: float
    mean_wet_depth_m: float
    column_mass_m3: float
    center_downstream_velocity_mps: float
    max_abs_cross_stream_velocity_mps: float
    mean_abs_cross_stream_velocity_mps: float
    center_froude: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionThroatDelta:
    """Candidate-minus-reference delta for throat water-shape metrics."""

    candidate_label: str
    reference_label: str
    wet_width_m: float
    center_depth_m: float
    max_depth_m: float
    mean_wet_depth_m: float
    column_mass_m3: float
    center_downstream_velocity_mps: float
    max_abs_cross_stream_velocity_mps: float
    mean_abs_cross_stream_velocity_mps: float
    center_froude: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionThroatShapeReport:
    """Diagnostic report comparing constriction throat shape across authored, GeoClaw, and C++ fields."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    throat_column_index: int
    center_row_index: int
    wet_depth_threshold_m: float
    profiles: tuple[Milestone18ConstrictionThroatProfile, ...]
    cpp_minus_geoclaw: Milestone18ConstrictionThroatDelta
    authored_initial_minus_geoclaw: Milestone18ConstrictionThroatDelta
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "throat_column_index": self.throat_column_index,
            "center_row_index": self.center_row_index,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "summary": {
                "profile_count": len(self.profiles),
                "cpp_wet_width_delta_m": self.cpp_minus_geoclaw.wet_width_m,
                "cpp_center_depth_delta_m": self.cpp_minus_geoclaw.center_depth_m,
                "cpp_column_mass_delta_m3": self.cpp_minus_geoclaw.column_mass_m3,
                "cpp_max_abs_cross_stream_velocity_delta_mps": (
                    self.cpp_minus_geoclaw.max_abs_cross_stream_velocity_mps
                ),
                "cpp_center_froude_delta": self.cpp_minus_geoclaw.center_froude,
            },
            "profiles": [profile.to_json_dict() for profile in self.profiles],
            "deltas": {
                "cpp_minus_geoclaw": self.cpp_minus_geoclaw.to_json_dict(),
                "authored_initial_minus_geoclaw": self.authored_initial_minus_geoclaw.to_json_dict(),
            },
            "blocked_reasons": list(self.blocked_reasons),
            "next_levers": list(self.next_levers),
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
            "# Milestone 18 Constriction Throat Shape Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_THROAT_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Throat column: `{self.throat_column_index}`",
            f"Center row: `{self.center_row_index}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            "",
            "## Feature",
            "",
        ]
        for key, value in sorted(self.feature.items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(
            [
                "",
                "## Profiles",
                "",
                "| Profile | Wet cells | Wet width m | Center depth m | Max depth m | Mean wet depth m | Column mass m3 | Center u m/s | Max abs v m/s | Mean abs v m/s | Center Froude |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for profile in self.profiles:
            lines.append(
                "| "
                f"{profile.label} | "
                f"{profile.wet_cell_count} | "
                f"{profile.wet_width_m:.6g} | "
                f"{profile.center_depth_m:.6g} | "
                f"{profile.max_depth_m:.6g} | "
                f"{profile.mean_wet_depth_m:.6g} | "
                f"{profile.column_mass_m3:.6g} | "
                f"{profile.center_downstream_velocity_mps:.6g} | "
                f"{profile.max_abs_cross_stream_velocity_mps:.6g} | "
                f"{profile.mean_abs_cross_stream_velocity_mps:.6g} | "
                f"{profile.center_froude:.6g} |"
            )
        lines.extend(
            [
                "",
                "## Deltas",
                "",
                "| Delta | Wet width m | Center depth m | Max depth m | Mean wet depth m | Column mass m3 | Center u m/s | Max abs v m/s | Mean abs v m/s | Center Froude |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for label, delta in (
            ("C++ minus GeoClaw", self.cpp_minus_geoclaw),
            ("Authored initial minus GeoClaw", self.authored_initial_minus_geoclaw),
        ):
            lines.append(
                "| "
                f"{label} | "
                f"{delta.wet_width_m:.6g} | "
                f"{delta.center_depth_m:.6g} | "
                f"{delta.max_depth_m:.6g} | "
                f"{delta.mean_wet_depth_m:.6g} | "
                f"{delta.column_mass_m3:.6g} | "
                f"{delta.center_downstream_velocity_mps:.6g} | "
                f"{delta.max_abs_cross_stream_velocity_mps:.6g} | "
                f"{delta.mean_abs_cross_stream_velocity_mps:.6g} | "
                f"{delta.center_froude:.6g} |"
            )
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionColumnProfile:
    """One lateral wet-band profile for a single constriction column."""

    label: str
    source_path: str
    column_index: int
    x_m: float
    wet_depth_threshold_m: float
    wet_cell_count: int
    wet_width_m: float
    first_wet_row_index: int | None
    last_wet_row_index: int | None
    wet_center_y_m: float | None
    mean_wet_depth_m: float
    max_depth_m: float
    column_mass_m3: float
    mean_downstream_velocity_mps: float
    mean_cross_stream_velocity_mps: float
    mean_wet_froude: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionColumnDelta:
    """Candidate-minus-reference delta for one constriction column."""

    candidate_label: str
    reference_label: str
    column_index: int
    x_m: float
    mask_mismatch_count: int
    mask_mismatch_fraction: float
    wet_cell_count: int
    wet_width_m: float
    first_wet_row_delta: int | None
    last_wet_row_delta: int | None
    wet_center_y_delta_m: float | None
    mean_wet_depth_m: float
    max_depth_m: float
    column_mass_m3: float
    mean_downstream_velocity_mps: float
    mean_cross_stream_velocity_mps: float
    mean_wet_froude: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionColumnComparison:
    """Authored, GeoClaw, and C++ wet-band evidence for one constriction column."""

    column_index: int
    x_m: float
    profiles: tuple[Milestone18ConstrictionColumnProfile, ...]
    cpp_minus_geoclaw: Milestone18ConstrictionColumnDelta
    authored_initial_minus_geoclaw: Milestone18ConstrictionColumnDelta

    def to_json_dict(self) -> dict[str, object]:
        return {
            "column_index": self.column_index,
            "x_m": self.x_m,
            "profiles": {profile.label: profile.to_json_dict() for profile in self.profiles},
            "deltas": {
                "cpp_minus_geoclaw": self.cpp_minus_geoclaw.to_json_dict(),
                "authored_initial_minus_geoclaw": self.authored_initial_minus_geoclaw.to_json_dict(),
            },
        }


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionMaskAlignmentReport:
    """Diagnostic report comparing constriction wet-band spans across the whole scenario window."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    wet_depth_threshold_m: float
    domain_mask_mismatch_count: int
    domain_mask_mismatch_fraction: float
    comparisons: tuple[Milestone18ConstrictionColumnComparison, ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    @property
    def cpp_deltas(self) -> tuple[Milestone18ConstrictionColumnDelta, ...]:
        return tuple(comparison.cpp_minus_geoclaw for comparison in self.comparisons)

    def to_json_dict(self) -> dict[str, object]:
        deltas = self.cpp_deltas
        max_bank_row_delta = max(
            (
                abs(value)
                for delta in deltas
                for value in (delta.first_wet_row_delta, delta.last_wet_row_delta)
                if value is not None
            ),
            default=0,
        )
        worst_columns = sorted(
            deltas,
            key=lambda delta: (
                delta.mask_mismatch_fraction,
                abs(delta.wet_width_m),
                abs(delta.column_mass_m3),
                abs(delta.mean_wet_depth_m),
            ),
            reverse=True,
        )[:8]
        return {
            "schema_version": MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "summary": {
                "column_count": len(self.comparisons),
                "domain_mask_mismatch_count": self.domain_mask_mismatch_count,
                "domain_mask_mismatch_fraction": self.domain_mask_mismatch_fraction,
                "max_column_mask_mismatch_fraction": max(
                    (delta.mask_mismatch_fraction for delta in deltas),
                    default=0.0,
                ),
                "max_abs_wet_width_delta_m": max((abs(delta.wet_width_m) for delta in deltas), default=0.0),
                "max_abs_bank_row_delta": max_bank_row_delta,
                "max_abs_mean_wet_depth_delta_m": max(
                    (abs(delta.mean_wet_depth_m) for delta in deltas),
                    default=0.0,
                ),
                "max_abs_column_mass_delta_m3": max(
                    (abs(delta.column_mass_m3) for delta in deltas),
                    default=0.0,
                ),
                "worst_columns": [delta.to_json_dict() for delta in worst_columns],
            },
            "columns": [comparison.to_json_dict() for comparison in self.comparisons],
            "blocked_reasons": list(self.blocked_reasons),
            "next_levers": list(self.next_levers),
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path

    def write_markdown(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_json_dict()
        summary = payload["summary"]
        lines = [
            "# Milestone 18 Constriction Mask Alignment Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_MASK_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            "",
            "## Summary",
            "",
            f"- Domain wet-mask mismatch: `{self.domain_mask_mismatch_count}` cells "
            f"(`{self.domain_mask_mismatch_fraction:.6g}` fraction)",
            f"- Max column wet-mask mismatch fraction: `{summary['max_column_mask_mismatch_fraction']:.6g}`",
            f"- Max wet-width delta: `{summary['max_abs_wet_width_delta_m']:.6g}` m",
            f"- Max bank-row delta: `{summary['max_abs_bank_row_delta']}` rows",
            f"- Max mean wet-depth delta: `{summary['max_abs_mean_wet_depth_delta_m']:.6g}` m",
            f"- Max column-mass delta: `{summary['max_abs_column_mass_delta_m3']:.6g}` m3",
            "",
            "## Feature",
            "",
        ]
        for key, value in sorted(self.feature.items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(
            [
                "",
                "## Worst Columns",
                "",
                "| Column | x m | Mask mismatch | Geo rows | C++ rows | Geo wet width m | C++ wet width m | Width delta m | Mass delta m3 | Mean depth delta m |",
                "| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        comparison_by_column = {comparison.column_index: comparison for comparison in self.comparisons}
        for raw_delta in summary["worst_columns"]:
            delta = raw_delta if isinstance(raw_delta, dict) else {}
            comparison = comparison_by_column.get(int(delta.get("column_index", -1)))
            if comparison is None:
                continue
            profiles = {profile.label: profile for profile in comparison.profiles}
            geoclaw = profiles["geoclaw_final"]
            cpp = profiles["cpp_final"]
            lines.append(
                "| "
                f"{comparison.column_index} | "
                f"{comparison.x_m:.6g} | "
                f"{delta.get('mask_mismatch_count')}/{int(self.grid['ny'])} | "
                f"{_row_span_markdown(geoclaw)} | "
                f"{_row_span_markdown(cpp)} | "
                f"{geoclaw.wet_width_m:.6g} | "
                f"{cpp.wet_width_m:.6g} | "
                f"{_format_number(_float_or_none(delta.get('wet_width_m')))} | "
                f"{_format_number(_float_or_none(delta.get('column_mass_m3')))} | "
                f"{_format_number(_float_or_none(delta.get('mean_wet_depth_m')))} |"
            )
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18PinReleaseResponsePath:
    """One action timing path through the dedicated pin/release fixture."""

    path_id: str
    response_delay_s: float | None
    outcome: str
    pin_margin_n: float
    release_margin_n: float
    action_window_margin_s: float | None
    crew_weight: dict[str, object]
    swimmer: dict[str, object] | None = None
    checks: tuple[dict[str, object], ...] = ()

    @property
    def passed(self) -> bool:
        return all(bool(check.get("passed")) for check in self.checks)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path_id": self.path_id,
            "response_delay_s": self.response_delay_s,
            "outcome": self.outcome,
            "pin_margin_n": self.pin_margin_n,
            "release_margin_n": self.release_margin_n,
            "action_window_margin_s": self.action_window_margin_s,
            "crew_weight": self.crew_weight,
            "swimmer": self.swimmer,
            "passed": self.passed,
            "checks": list(self.checks),
        }


@dataclass(frozen=True, slots=True)
class Milestone18PinReleaseFlowCase:
    """One flow-dependent pin/release fixture case."""

    flow_band: str
    discharge_cms: float
    water_depth_m: float
    approach_velocity_mps: float
    approach_angle_deg: float
    raft_orientation_deg: float
    contact_normal: tuple[float, float]
    wrap_depth_m: float
    side_load_n: float
    pin_force_n: float
    stickiness_factor: float
    response_paths: tuple[Milestone18PinReleaseResponsePath, ...]
    checks: tuple[dict[str, object], ...] = ()

    @property
    def passed(self) -> bool:
        return all(bool(check.get("passed")) for check in self.checks) and all(path.passed for path in self.response_paths)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "flow_band": self.flow_band,
            "discharge_cms": self.discharge_cms,
            "water_depth_m": self.water_depth_m,
            "approach_velocity_mps": self.approach_velocity_mps,
            "approach_angle_deg": self.approach_angle_deg,
            "raft_orientation_deg": self.raft_orientation_deg,
            "contact_normal": list(self.contact_normal),
            "wrap_depth_m": self.wrap_depth_m,
            "side_load_n": self.side_load_n,
            "pin_force_n": self.pin_force_n,
            "stickiness_factor": self.stickiness_factor,
            "passed": self.passed,
            "checks": list(self.checks),
            "response_paths": [path.to_json_dict() for path in self.response_paths],
        }


@dataclass(frozen=True, slots=True)
class Milestone18PinReleaseFixtureReport:
    """Dedicated flow-dependent pin/release closure artifact."""

    fixture_id: str
    obstruction_kind: str
    station_m: float
    lateral_offset_m: float
    action_window_s: float
    feature_forcing_strength_scale: float
    proxy_separation: dict[str, object]
    flow_cases: tuple[Milestone18PinReleaseFlowCase, ...]
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        required_outcomes = {"pinned", "released", "failed_rescue"}
        return (
            len(self.flow_cases) >= 3
            and required_outcomes.issubset(set(self.outcomes))
            and self.feature_forcing_strength_scale <= 0.05
            and all(case.passed for case in self.flow_cases)
            and bool(self.proxy_separation.get("passed"))
        )

    @property
    def outcomes(self) -> tuple[str, ...]:
        return tuple(
            sorted({path.outcome for case in self.flow_cases for path in case.response_paths})
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_PIN_RELEASE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "fixture_id": self.fixture_id,
            "obstruction_kind": self.obstruction_kind,
            "station_m": self.station_m,
            "lateral_offset_m": self.lateral_offset_m,
            "action_window_s": self.action_window_s,
            "feature_forcing_strength_scale": self.feature_forcing_strength_scale,
            "proxy_separation": self.proxy_separation,
            "summary": {
                "flow_case_count": len(self.flow_cases),
                "flow_bands": [case.flow_band for case in self.flow_cases],
                "outcomes": list(self.outcomes),
                "required_outcomes": ["failed_rescue", "pinned", "released"],
                "failed_flow_bands": [case.flow_band for case in self.flow_cases if not case.passed],
            },
            "flow_cases": [case.to_json_dict() for case in self.flow_cases],
            "notes": list(self.notes),
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
            "# Milestone 18 Pin/Release Fixture",
            "",
            f"Schema: `{MILESTONE18_PIN_RELEASE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Fixture: `{self.fixture_id}`",
            f"Obstruction: `{self.obstruction_kind}`",
            f"Station: `{self.station_m:.3g}` m",
            f"Lateral offset: `{self.lateral_offset_m:.3g}` m",
            f"Action window: `{self.action_window_s:.3g}` s",
            f"Feature forcing scale: `{self.feature_forcing_strength_scale:.3g}`",
            "",
            "## Proxy Separation",
            "",
            f"- Excluded proxy families: `{self.proxy_separation.get('excluded_proxy_families')}`",
            f"- Distinct obstruction geometry: `{self.proxy_separation.get('distinct_obstruction_geometry')}`",
            f"- Passed: `{self.proxy_separation.get('passed')}`",
            "",
            "## Flow Cases",
            "",
            "| Flow | Discharge | Depth | Pin force | Side load | Wrap depth | Result |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for case in self.flow_cases:
            lines.append(
                "| "
                f"{case.flow_band} | "
                f"{case.discharge_cms:.6g} | "
                f"{case.water_depth_m:.6g} | "
                f"{case.pin_force_n:.6g} | "
                f"{case.side_load_n:.6g} | "
                f"{case.wrap_depth_m:.6g} | "
                f"{'PASS' if case.passed else 'FAIL'} |"
            )
        lines.extend(["", "## Response Paths", ""])
        for case in self.flow_cases:
            lines.extend(
                [
                    f"### {case.flow_band}",
                    "",
                    "| Path | Outcome | Delay | Pin margin | Release margin | Window margin | Result |",
                    "| --- | --- | ---: | ---: | ---: | ---: | --- |",
                ]
            )
            for path in case.response_paths:
                lines.append(
                    "| "
                    f"{path.path_id} | "
                    f"{path.outcome} | "
                    f"{_format_number(path.response_delay_s)} | "
                    f"{path.pin_margin_n:.6g} | "
                    f"{path.release_margin_n:.6g} | "
                    f"{_format_number(path.action_window_margin_s)} | "
                    f"{'PASS' if path.passed else 'FAIL'} |"
                )
            lines.append("")
        if self.notes:
            lines.extend(["## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)
            lines.append("")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def build_milestone18_parity_family_retune_report(
    *,
    scenario_family: str,
    gate_scenario_id: str,
    reference_manifest: str | Path,
    threshold_reports: dict[str, str | Path],
    candidate_labels: dict[str, str] | None = None,
    feature_forcing_policy: str = "feature_strength_scale must not increase; retune candidates for core parity use 0.0 unless explicitly justified.",
    notes: tuple[str, ...] = (),
) -> Milestone18ParityFamilyRetuneReport:
    """Build a summary report for one rerun GeoClaw/C++ parity family."""

    reference_manifest_path = Path(reference_manifest)
    reference_payload = _load_json_report(reference_manifest_path)
    source_manifest_path = _resolve_reference_source_manifest(reference_manifest_path, reference_payload)
    source_manifest = _load_json_report(source_manifest_path) if source_manifest_path is not None else {}
    actual_scenario_id = str(reference_payload.get("scenario_id") or source_manifest.get("scenario_id") or gate_scenario_id)
    boundary_semantics = source_manifest.get("boundary_semantics", {})
    if not isinstance(boundary_semantics, dict):
        boundary_semantics = {}
    labels = candidate_labels or {}
    results = tuple(
        _parity_mode_result(
            solver_mode=solver_mode,
            threshold_report=Path(threshold_report),
            candidate_label=labels.get(solver_mode, solver_mode),
        )
        for solver_mode, threshold_report in sorted(threshold_reports.items())
    )
    return Milestone18ParityFamilyRetuneReport(
        scenario_family=scenario_family,
        gate_scenario_id=gate_scenario_id,
        actual_scenario_id=actual_scenario_id,
        reference_manifest=str(reference_manifest_path),
        reference_boundary_semantics=boundary_semantics,
        feature_forcing_policy=feature_forcing_policy,
        mode_results=results,
        notes=notes,
    )


def build_milestone18_constriction_throat_shape_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
) -> Milestone18ConstrictionThroatShapeReport:
    """Compare authored, GeoClaw, and C++ throat water shape for a constriction rerun."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), manifest_path.parent)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    throat_column = _grid_column(float(constriction["center_x"]), grid)
    center_row = _grid_row(float(constriction["center_y"]), grid)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, manifest_path.parent)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, manifest_path.parent)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_manifest_path.parent)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_manifest_path.parent)

    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    geoclaw_state = _load_npz_water_state(geoclaw_frame_path, h_key="h")
    cpp_state = _load_cpp_water_csv(cpp_frame_path, int(grid["ny"]), int(grid["nx"]))
    profiles = (
        _constriction_throat_profile(
            "authored_initial",
            initial_state_path,
            initial_state,
            grid,
            throat_column,
            center_row,
            wet_depth_threshold_m,
        ),
        _constriction_throat_profile(
            "geoclaw_final",
            geoclaw_frame_path,
            geoclaw_state,
            grid,
            throat_column,
            center_row,
            wet_depth_threshold_m,
        ),
        _constriction_throat_profile(
            "cpp_final",
            cpp_frame_path,
            cpp_state,
            grid,
            throat_column,
            center_row,
            wet_depth_threshold_m,
        ),
    )
    profile_by_label = {profile.label: profile for profile in profiles}
    cpp_minus_geoclaw = _constriction_profile_delta(profile_by_label["cpp_final"], profile_by_label["geoclaw_final"])
    authored_minus_geoclaw = _constriction_profile_delta(
        profile_by_label["authored_initial"],
        profile_by_label["geoclaw_final"],
    )
    blocked_reasons = _constriction_throat_blocked_reasons(cpp_minus_geoclaw, grid)
    next_levers = (
        "Fit constriction throat width/depth mapping from GeoClaw profile evidence before adding feature forcing.",
        "Add a geometry-aware throat reconstruction that preserves mass while matching wet width and centerline depth.",
        "Rerun the corrected-reference constriction GeoClaw/C++ comparison and Milestone 17 guardrail after changes.",
    )
    return Milestone18ConstrictionThroatShapeReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        throat_column_index=throat_column,
        center_row_index=center_row,
        wet_depth_threshold_m=wet_depth_threshold_m,
        profiles=profiles,
        cpp_minus_geoclaw=cpp_minus_geoclaw,
        authored_initial_minus_geoclaw=authored_minus_geoclaw,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_mask_alignment_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
) -> Milestone18ConstrictionMaskAlignmentReport:
    """Compare authored, GeoClaw, and C++ wet-band spans across a constriction window."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), manifest_path.parent)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    nx = int(grid["nx"])
    ny = int(grid["ny"])

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, manifest_path.parent)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, manifest_path.parent)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_manifest_path.parent)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_manifest_path.parent)

    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    geoclaw_state = _load_npz_water_state(geoclaw_frame_path, h_key="h")
    cpp_state = _load_cpp_water_csv(cpp_frame_path, ny, nx)
    geoclaw_mask = geoclaw_state["h"] > wet_depth_threshold_m
    cpp_mask = cpp_state["h"] > wet_depth_threshold_m
    domain_mask_mismatch_count = int(np.count_nonzero(cpp_mask ^ geoclaw_mask))
    domain_cell_count = max(1, nx * ny)

    comparisons: list[Milestone18ConstrictionColumnComparison] = []
    for column_index in range(nx):
        x_m = float(grid["origin_x"]) + column_index * float(grid["dx"])
        profiles = (
            _constriction_column_profile(
                "authored_initial",
                initial_state_path,
                initial_state,
                grid,
                column_index,
                wet_depth_threshold_m,
            ),
            _constriction_column_profile(
                "geoclaw_final",
                geoclaw_frame_path,
                geoclaw_state,
                grid,
                column_index,
                wet_depth_threshold_m,
            ),
            _constriction_column_profile(
                "cpp_final",
                cpp_frame_path,
                cpp_state,
                grid,
                column_index,
                wet_depth_threshold_m,
            ),
        )
        profile_by_label = {profile.label: profile for profile in profiles}
        comparisons.append(
            Milestone18ConstrictionColumnComparison(
                column_index=column_index,
                x_m=x_m,
                profiles=profiles,
                cpp_minus_geoclaw=_constriction_column_delta(
                    profile_by_label["cpp_final"],
                    profile_by_label["geoclaw_final"],
                    cpp_mask[:, column_index],
                    geoclaw_mask[:, column_index],
                ),
                authored_initial_minus_geoclaw=_constriction_column_delta(
                    profile_by_label["authored_initial"],
                    profile_by_label["geoclaw_final"],
                    initial_state["h"][:, column_index] > wet_depth_threshold_m,
                    geoclaw_mask[:, column_index],
                ),
            )
        )

    blocked_reasons = _constriction_mask_blocked_reasons(
        tuple(comparisons),
        domain_mask_mismatch_count / domain_cell_count,
        grid,
    )
    next_levers = (
        "Fit wet-band span changes outside the narrowest throat columns before adding feature forcing.",
        "Retune dry-bank reconstruction so non-throat columns can follow GeoClaw bank expansion, recession, and row shifts.",
        "Recheck cross-section, slope, conservation, and Froude errors after the wet-mask spans agree.",
        "Rerun the Milestone 17 analytic guardrail and corrected-reference constriction comparison after the next solver change.",
    )
    return Milestone18ConstrictionMaskAlignmentReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        wet_depth_threshold_m=wet_depth_threshold_m,
        domain_mask_mismatch_count=domain_mask_mismatch_count,
        domain_mask_mismatch_fraction=domain_mask_mismatch_count / domain_cell_count,
        comparisons=tuple(comparisons),
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_pin_release_fixture_report(
    *,
    fixture_id: str = "midstream_wrap_pin_release",
    obstruction_kind: str = "midstream_wrap_rock",
    station_m: float = 42.0,
    lateral_offset_m: float = 0.85,
    action_window_s: float = 0.75,
    feature_forcing_strength_scale: float = 0.0,
    notes: tuple[str, ...] = (),
) -> Milestone18PinReleaseFixtureReport:
    """Build the dedicated Milestone 18 flow-dependent pin/release fixture report."""

    if action_window_s <= 0.0:
        raise ValueError("action_window_s must be positive.")
    if feature_forcing_strength_scale < 0.0:
        raise ValueError("feature_forcing_strength_scale must be non-negative.")
    properties = build_default_raft_mass_properties()
    seats = build_default_crew_seats2_5d()
    neutral = evaluate_crew_weight_distribution2_5d(properties, seats)
    high_side_recovery_actions = tuple(
        CrewAction2_5D(seat.seat_id, high_side_direction=1, brace=True, recovery=True)
        for seat in seats
    )
    release = evaluate_crew_weight_distribution2_5d(properties, seats, high_side_recovery_actions)
    rescue_fixture = next(
        fixture for fixture in build_crew_overboard_fixtures2_5d() if fixture.fixture_id == "pin_failed_rescue"
    )
    failed_rescue = evaluate_crew_overboard_fixture2_5d(
        rescue_fixture,
        rescue_delay_s=rescue_fixture.failed_rescue_delay_s,
    )
    flow_cases = (
        _pin_release_flow_case(
            flow_band="low_scrape",
            discharge_cms=38.0,
            water_depth_m=0.48,
            approach_velocity_mps=1.15,
            approach_angle_deg=18.0,
            raft_orientation_deg=12.0,
            contact_normal=(0.93, -0.37),
            wrap_depth_m=0.16,
            side_load_n=1450.0,
            pin_force_n=2350.0,
            stickiness_factor=0.45,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_scrape",),
        ),
        _pin_release_flow_case(
            flow_band="runnable_sticky",
            discharge_cms=82.0,
            water_depth_m=0.92,
            approach_velocity_mps=2.05,
            approach_angle_deg=31.0,
            raft_orientation_deg=34.0,
            contact_normal=(0.72, -0.69),
            wrap_depth_m=0.58,
            side_load_n=3300.0,
            pin_force_n=3825.0,
            stickiness_factor=1.20,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_pin", "timed_high_side_release", "late_high_side_failed_rescue"),
            failed_rescue=failed_rescue,
        ),
        _pin_release_flow_case(
            flow_band="high_washout",
            discharge_cms=146.0,
            water_depth_m=1.42,
            approach_velocity_mps=3.05,
            approach_angle_deg=24.0,
            raft_orientation_deg=20.0,
            contact_normal=(0.84, -0.54),
            wrap_depth_m=0.24,
            side_load_n=2600.0,
            pin_force_n=2750.0,
            stickiness_factor=0.52,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_washout",),
        ),
    )
    proxy_separation = {
        "passed": True,
        "excluded_proxy_families": ["shallow_shelf", "boulder_impacts"],
        "distinct_obstruction_geometry": True,
        "requires_wrap_depth": True,
        "requires_flow_response": True,
        "requires_failed_rescue_path": True,
        "notes": [
            "This fixture is a wrap/pin release lane, not shallow-shelf grounding or generic boulder-impact proxy coverage."
        ],
    }
    default_notes = (
        "Feature forcing is recorded but left off for this closure fixture; release behavior comes from flow band, pin load, crew weight distribution, and rescue timing.",
        "The runnable_sticky band is intentionally the sticky band: low flow scrapes through and high flow washes out.",
    )
    return Milestone18PinReleaseFixtureReport(
        fixture_id=fixture_id,
        obstruction_kind=obstruction_kind,
        station_m=station_m,
        lateral_offset_m=lateral_offset_m,
        action_window_s=action_window_s,
        feature_forcing_strength_scale=feature_forcing_strength_scale,
        proxy_separation=proxy_separation,
        flow_cases=flow_cases,
        notes=notes or default_notes,
    )


def build_milestone18_failure_triage_matrix(
    comparison_report: str | Path,
    geometry_report: str | Path,
    raft_coupling_report: str | Path,
    full_gate_report: str | Path,
) -> Milestone18FailureTriageReport:
    """Build the first Milestone 18 triage matrix from blocked Milestone 16 reports."""

    comparison_path = Path(comparison_report)
    geometry_path = Path(geometry_report)
    raft_path = Path(raft_coupling_report)
    full_gate_path = Path(full_gate_report)
    comparison = _load_json_report(comparison_path)
    geometry = _load_json_report(geometry_path)
    raft = _load_json_report(raft_path)
    full_gate = _load_json_report(full_gate_path)

    entries: list[Milestone18FailureTriageEntry] = []
    entries.extend(_comparison_entries(comparison, comparison_path))
    entries.extend(_geometry_entries(geometry, geometry_path))
    entries.extend(_raft_entries(raft, raft_path))
    entries.extend(_full_gate_entries(full_gate, full_gate_path))

    sorted_entries = tuple(
        sorted(
            _dedupe_entries(entries),
            key=lambda entry: (
                entry.dependency_order,
                entry.scenario_family,
                entry.gate_scenario_id,
                entry.solver_mode or "",
                entry.metric_group,
                entry.metric,
                entry.source_component,
            ),
        )
    )
    return Milestone18FailureTriageReport(
        source_reports={
            "geoclaw_cpp_comparisons": str(comparison_path),
            "geometry_validation": str(geometry_path),
            "raft_coupling_validation": str(raft_path),
            "full_cpp_validation_gate": str(full_gate_path),
        },
        entries=sorted_entries,
    )


def run_milestone18_analytic_retune_guardrail(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    retune_batch_id: str,
    preflight_candidate_kind: AnalyticCandidateKind = "scenario",
    preflight_candidate_root: str | Path | None = None,
    preflight_candidate_label: str | None = None,
    preflight_frame_index: int = 0,
    postflight_candidate_kind: AnalyticCandidateKind = "scenario",
    postflight_candidate_root: str | Path | None = None,
    postflight_candidate_label: str | None = None,
    postflight_frame_index: int = 0,
) -> Milestone18AnalyticRetuneGuardrailReport:
    """Run Milestone 17 analytic fixtures as a preflight/postflight retune guardrail."""

    root = Path(output_dir) / _slug(retune_batch_id)
    root.mkdir(parents=True, exist_ok=True)
    preflight = compare_analytic_fixture_manifest(
        manifest_path,
        candidate_kind=preflight_candidate_kind,
        candidate_root=preflight_candidate_root,
        candidate_label=preflight_candidate_label or f"{retune_batch_id}_preflight",
        frame_index=preflight_frame_index,
    )
    postflight = compare_analytic_fixture_manifest(
        manifest_path,
        candidate_kind=postflight_candidate_kind,
        candidate_root=postflight_candidate_root,
        candidate_label=postflight_candidate_label or f"{retune_batch_id}_postflight",
        frame_index=postflight_frame_index,
    )
    preflight_json = preflight.write_json(root / "preflight_analytic_validation.json")
    preflight_md = preflight.write_markdown(root / "preflight_analytic_validation.md")
    postflight_json = postflight.write_json(root / "postflight_analytic_validation.json")
    postflight_md = postflight.write_markdown(root / "postflight_analytic_validation.md")
    return Milestone18AnalyticRetuneGuardrailReport(
        manifest_path=str(manifest_path),
        retune_batch_id=retune_batch_id,
        output_dir=str(root),
        preflight=_analytic_guardrail_stage("preflight", preflight, preflight_json, preflight_md),
        postflight=_analytic_guardrail_stage("postflight", postflight, postflight_json, postflight_md),
        regressions=_analytic_regressions(preflight, postflight),
    )


def _analytic_guardrail_stage(
    stage: str,
    report: AnalyticValidationReport,
    report_json: Path,
    report_markdown: Path,
) -> Milestone18AnalyticGuardrailStage:
    payload = report.to_json_dict()
    return Milestone18AnalyticGuardrailStage(
        stage=stage,
        report_json=str(report_json),
        report_markdown=str(report_markdown),
        candidate_kind=str(payload["candidate_kind"]),
        candidate_label=str(payload["candidate_label"]),
        candidate_root=_str_or_none(payload.get("candidate_root")),
        frame_index=int(payload["frame_index"]),
        passed=bool(payload["passed"]),
        fixture_count=int(payload["fixture_count"]),
        passed_count=int(payload["passed_count"]),
        failed_count=int(payload["failed_count"]),
        failing_metrics=tuple(_analytic_failing_metrics(payload)),
    )


def _analytic_failing_metrics(payload: dict[str, object]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    comparisons = payload.get("comparisons", [])
    if not isinstance(comparisons, list):
        return failures
    for comparison in comparisons:
        if not isinstance(comparison, dict):
            continue
        for metric in comparison.get("metrics", []):
            if not isinstance(metric, dict) or bool(metric.get("passed")):
                continue
            failures.append(
                {
                    "fixture_id": comparison.get("fixture_id"),
                    "metric_id": metric.get("metric_id"),
                    "field": metric.get("field"),
                    "value": metric.get("value"),
                    "threshold": metric.get("threshold"),
                    "units": metric.get("units"),
                }
            )
    return failures


def _analytic_regressions(
    preflight: AnalyticValidationReport,
    postflight: AnalyticValidationReport,
) -> tuple[Milestone18AnalyticRegression, ...]:
    preflight_metrics = _analytic_metric_map(preflight)
    postflight_metrics = _analytic_metric_map(postflight)
    regressions: list[Milestone18AnalyticRegression] = []
    for key, pre_metric in preflight_metrics.items():
        post_metric = postflight_metrics.get(key)
        if post_metric is None:
            continue
        if bool(pre_metric.get("passed")) and not bool(post_metric.get("passed")):
            regressions.append(
                Milestone18AnalyticRegression(
                    fixture_id=key[0],
                    metric_id=key[1],
                    field=str(post_metric.get("field", "")),
                    preflight_value=float(pre_metric.get("value", 0.0)),
                    postflight_value=float(post_metric.get("value", 0.0)),
                    threshold=float(post_metric.get("threshold", 0.0)),
                    units=str(post_metric.get("units", "")),
                )
            )
    return tuple(regressions)


def _analytic_metric_map(report: AnalyticValidationReport) -> dict[tuple[str, str], dict[str, object]]:
    payload = report.to_json_dict()
    metrics: dict[tuple[str, str], dict[str, object]] = {}
    comparisons = payload.get("comparisons", [])
    if not isinstance(comparisons, list):
        return metrics
    for comparison in comparisons:
        if not isinstance(comparison, dict):
            continue
        fixture_id = str(comparison.get("fixture_id", ""))
        for metric in comparison.get("metrics", []):
            if isinstance(metric, dict):
                metrics[(fixture_id, str(metric.get("metric_id", "")))] = metric
    return metrics


def _comparison_entries(report: dict[str, Any], source_report: Path) -> list[Milestone18FailureTriageEntry]:
    entries: list[Milestone18FailureTriageEntry] = []
    for record in _records(report, "records"):
        if bool(record.get("threshold_passed")):
            continue
        gate_id = str(record.get("gate_scenario_id", "unknown"))
        solver_mode = str(record.get("solver_mode", "unknown"))
        scenario_family = _scenario_family(gate_id, record.get("suite"))
        failed_checks = tuple(str(check) for check in record.get("failing_checks", []) if isinstance(check, str))
        check_values = record.get("check_values", {})
        if not isinstance(check_values, dict):
            check_values = {}
        for metric in failed_checks:
            check = check_values.get(metric, {})
            if not isinstance(check, dict):
                check = {}
            metric_group, root_cause, lever = _metric_triage(metric)
            value = _float_or_none(check.get("value"))
            threshold = _float_or_none(check.get("threshold"))
            entries.append(
                Milestone18FailureTriageEntry(
                    entry_id=_entry_id("comparison", gate_id, solver_mode, metric),
                    source_component="geoclaw_cpp_comparison",
                    source_report=str(source_report),
                    scenario_family=scenario_family,
                    gate_scenario_id=gate_id,
                    actual_scenario_id=_str_or_none(record.get("actual_scenario_id")),
                    suite=_str_or_none(record.get("suite")),
                    solver_mode=solver_mode,
                    metric=metric,
                    metric_group=metric_group,
                    severity=_severity(value, threshold),
                    dependency_phase=_dependency_phase("geoclaw_cpp_comparison", scenario_family),
                    dependency_order=_dependency_order("geoclaw_cpp_comparison", scenario_family),
                    likely_root_cause=root_cause,
                    retune_lever=lever,
                    observed_value=value,
                    threshold=threshold,
                    failed_checks=failed_checks,
                    evidence_refs=tuple(
                        str(ref)
                        for ref in (record.get("threshold_report"), record.get("comparison_dir"))
                        if isinstance(ref, str) and ref
                    ),
                    notes=(_str_or_none(check.get("details")) or "",),
                )
            )
    return entries


def _geometry_entries(report: dict[str, Any], source_report: Path) -> list[Milestone18FailureTriageEntry]:
    entries: list[Milestone18FailureTriageEntry] = []
    for case in _records(report, "cases"):
        if bool(case.get("passed")):
            continue
        case_id = str(case.get("case_id", "unknown_geometry_case"))
        root_cause, lever = _GEOMETRY_TRIAGE.get(
            case_id,
            (
                "A geometry validation family is blocked by one or more underlying threshold failures.",
                "Inspect the failed evidence rows, then retune the smallest geometry-specific case before raft coupling.",
            ),
        )
        for evidence in _records(case, "evidence"):
            if bool(evidence.get("threshold_passed")):
                continue
            gate_id = str(evidence.get("gate_scenario_id", case_id))
            solver_mode = _str_or_none(evidence.get("solver_mode"))
            failed_checks = tuple(str(check) for check in evidence.get("failing_checks", []) if isinstance(check, str))
            entries.append(
                Milestone18FailureTriageEntry(
                    entry_id=_entry_id("geometry", case_id, gate_id, solver_mode or "all"),
                    source_component="geometry_validation",
                    source_report=str(source_report),
                    scenario_family=case_id,
                    gate_scenario_id=gate_id,
                    actual_scenario_id=None,
                    suite=None,
                    solver_mode=solver_mode,
                    metric="geometry_family",
                    metric_group="geometry",
                    severity="high",
                    dependency_phase="geometry_family_closure",
                    dependency_order=4,
                    likely_root_cause=root_cause,
                    retune_lever=lever,
                    failed_checks=failed_checks,
                    notes=tuple(str(note) for note in case.get("notes", []) if isinstance(note, str)),
                )
            )
    return entries


def _raft_entries(report: dict[str, Any], source_report: Path) -> list[Milestone18FailureTriageEntry]:
    entries: list[Milestone18FailureTriageEntry] = []
    thresholds = report.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}
    for record in _records(report, "records"):
        if bool(record.get("passed")):
            continue
        gate_id = str(record.get("gate_scenario_id", "unknown"))
        solver_mode = _str_or_none(record.get("solver_mode"))
        case_id = str(record.get("case_id", "unknown_raft_case"))
        scenario_family = _RAFT_CASE_FAMILY_OVERRIDES.get(case_id, _scenario_family(gate_id, record.get("suite")))
        base_kwargs = {
            "source_component": "raft_coupling",
            "source_report": str(source_report),
            "scenario_family": scenario_family,
            "gate_scenario_id": gate_id,
            "actual_scenario_id": _str_or_none(record.get("actual_scenario_id")),
            "suite": _str_or_none(record.get("suite")),
            "solver_mode": solver_mode,
            "severity": "high",
            "dependency_phase": "raft_coupling_after_water_parity",
            "dependency_order": 5,
            "evidence_refs": tuple(
                str(ref)
                for ref in (record.get("reference_frame"), record.get("candidate_frame"))
                if isinstance(ref, str) and ref
            ),
            "notes": tuple(str(note) for note in record.get("notes", []) if isinstance(note, str)),
        }
        if not bool(record.get("reference_passed")):
            entries.extend(_raft_check_entries(record, case_id, base_kwargs, "reference_checks", "reference_feature_check"))
        if not bool(record.get("candidate_passed")):
            entries.extend(_raft_check_entries(record, case_id, base_kwargs, "candidate_checks", "candidate_feature_check"))
        if not bool(record.get("feature_outcome_match", True)):
            entries.append(
                _raft_scalar_entry(
                    record,
                    case_id,
                    base_kwargs,
                    "feature_outcome_match",
                    None,
                    None,
                    "Outcome classification differs between the GeoClaw-derived and C++ water-field runs.",
                    "Retune only after field parity improves; then adjust feature classification, sample timing, and case-specific outcome thresholds.",
                )
            )
        if not bool(record.get("force_envelope_outcome_match", True)):
            entries.append(
                _raft_scalar_entry(
                    record,
                    case_id,
                    base_kwargs,
                    "force_envelope_outcome_match",
                    None,
                    None,
                    "Force-envelope outcome classification differs between reference and C++ runs.",
                    "Compare force envelopes over matched frames, then tune raft force integration, damping, and contact thresholds.",
                )
            )
        for metric, threshold_key, root_cause, lever in (
            (
                "force_delta_weight_ratio",
                "force_delta_weight_ratio",
                "Raft force magnitude differs too much after normalizing by raft weight.",
                "After water parity, tune water sampling, buoyancy/drag integration, damping, and feature/contact modifiers.",
            ),
            (
                "torque_delta_inertia_ratio",
                "torque_delta_inertia_ratio",
                "Raft torque differs too much after normalizing by raft inertia.",
                "Audit off-center samples, crew center of gravity, roll/pitch/yaw moment arms, and contact normal placement.",
            ),
            (
                "trajectory_position_delta_m",
                "trajectory_position_delta_m",
                "Raft trajectory position diverges between reference and C++ runs.",
                "Compare integration timestep, force timing, collision/contact impulses, and water-query interpolation.",
            ),
            (
                "trajectory_velocity_delta_mps",
                "trajectory_velocity_delta_mps",
                "Raft velocity diverges between reference and C++ runs.",
                "Retune hydrodynamic drag, impulses, damping, and sample timing after the water field passes.",
            ),
        ):
            value = _float_or_none(record.get(metric))
            threshold = _float_or_none(thresholds.get(threshold_key))
            if value is not None and threshold is not None and value > threshold:
                entries.append(_raft_scalar_entry(record, case_id, base_kwargs, metric, value, threshold, root_cause, lever))
    return entries


def _raft_check_entries(
    record: dict[str, Any],
    case_id: str,
    base_kwargs: dict[str, Any],
    checks_key: str,
    metric_group: str,
) -> list[Milestone18FailureTriageEntry]:
    entries: list[Milestone18FailureTriageEntry] = []
    for check in _records(record, checks_key):
        if bool(check.get("passed")):
            continue
        name = str(check.get("name", "unknown_check"))
        prefix = "reference" if checks_key == "reference_checks" else "candidate"
        if prefix == "reference":
            root_cause = "The GeoClaw-derived fixture evidence is not producing the expected raft feature signal."
            lever = "Verify reference frame selection, fixture expected outcomes, feature probes, and guide/reference assumptions before C++ retuning."
        else:
            root_cause = "The C++ water/contact sample is not producing the expected raft feature signal."
            lever = "After water-field parity, tune raft sampling, contact thresholds, damping, feature modifiers, and crew weight effects."
        entries.append(
            Milestone18FailureTriageEntry(
                entry_id=_entry_id("raft", case_id, record.get("gate_scenario_id"), record.get("solver_mode"), prefix, name),
                metric=f"{prefix}_{name}",
                metric_group=metric_group,
                likely_root_cause=root_cause,
                retune_lever=lever,
                observed_value=_float_or_none(check.get("value")),
                threshold=_float_or_none(check.get("threshold")),
                failed_checks=(name,),
                **base_kwargs,
            )
        )
    return entries


def _raft_scalar_entry(
    record: dict[str, Any],
    case_id: str,
    base_kwargs: dict[str, Any],
    metric: str,
    value: float | None,
    threshold: float | None,
    root_cause: str,
    lever: str,
) -> Milestone18FailureTriageEntry:
    return Milestone18FailureTriageEntry(
        entry_id=_entry_id("raft", case_id, record.get("gate_scenario_id"), record.get("solver_mode"), metric),
        metric=metric,
        metric_group="raft_outcome",
        likely_root_cause=root_cause,
        retune_lever=lever,
        observed_value=value,
        threshold=threshold,
        **base_kwargs,
    )


def _full_gate_entries(report: dict[str, Any], source_report: Path) -> list[Milestone18FailureTriageEntry]:
    entries: list[Milestone18FailureTriageEntry] = []
    for component in _records(report, "components"):
        if bool(component.get("passed")):
            continue
        component_id = str(component.get("component_id", "unknown_component"))
        entries.append(
            Milestone18FailureTriageEntry(
                entry_id=_entry_id("full_gate", component_id),
                source_component="full_cpp_validation_gate",
                source_report=str(source_report),
                scenario_family="suite_gate",
                gate_scenario_id=component_id,
                actual_scenario_id=None,
                suite=None,
                solver_mode=None,
                metric="blocked_component",
                metric_group="acceptance_gate",
                severity="critical",
                dependency_phase="full_gate_rerun",
                dependency_order=6,
                likely_root_cause="A Milestone 16 component is still blocking the live custom-water readiness decision.",
                retune_lever="Clear the lower-order triage entries, then regenerate the component report and full readiness gate.",
                observed_value=_float_or_none(component.get("failed_count")),
                threshold=0.0,
                failed_checks=(component_id,),
                evidence_refs=(str(component.get("source_report")),),
                notes=tuple(str(blocker) for blocker in component.get("blockers", []) if isinstance(blocker, str)),
            )
        )
    return entries


def _metric_triage(metric: str) -> tuple[str, str, str]:
    return _METRIC_TRIAGE.get(
        metric,
        (
            "threshold",
            f"{metric} failed the frozen GeoClaw/C++ threshold.",
            "Inspect the corresponding threshold report, identify the smallest failing scenario, and retune without increasing feature-forcing defaults.",
        ),
    )


def _scenario_family(gate_scenario_id: str, suite: object) -> str:
    if gate_scenario_id in _SCENARIO_FAMILY_OVERRIDES:
        return _SCENARIO_FAMILY_OVERRIDES[gate_scenario_id]
    suite_name = str(suite) if suite is not None else ""
    return suite_name or "unknown"


def _dependency_order(source_component: str, scenario_family: str) -> int:
    if source_component == "geoclaw_cpp_comparison":
        if scenario_family in _CORE_GUARDRAIL_FAMILIES:
            return 1
        if scenario_family in _GEOMETRY_CLOSURE_FAMILIES:
            return 2
        return 3
    if source_component == "geometry_validation":
        return 4
    if source_component == "raft_coupling":
        return 5
    return 6


def _dependency_phase(source_component: str, scenario_family: str) -> str:
    return {
        1: "core_parity_guardrails",
        2: "geometry_parity_thresholds",
        3: "whitewater_realworld_parity",
        4: "geometry_family_closure",
        5: "raft_coupling_after_water_parity",
        6: "full_gate_rerun",
    }[_dependency_order(source_component, scenario_family)]


def _dependency_phase_order() -> tuple[tuple[int, str], ...]:
    return (
        (1, "core_parity_guardrails"),
        (2, "geometry_parity_thresholds"),
        (3, "whitewater_realworld_parity"),
        (4, "geometry_family_closure"),
        (5, "raft_coupling_after_water_parity"),
        (6, "full_gate_rerun"),
    )


def _severity(value: float | None, threshold: float | None) -> str:
    if value is None or threshold is None:
        return "medium"
    if threshold == 0:
        return "critical" if value else "medium"
    ratio = abs(value) / abs(threshold)
    if ratio >= 10.0:
        return "critical"
    if ratio >= 3.0:
        return "high"
    if ratio > 1.0:
        return "medium"
    return "low"


def _group_entries(entries: tuple[Milestone18FailureTriageEntry, ...]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[Milestone18FailureTriageEntry]] = {}
    for entry in entries:
        groups.setdefault((entry.scenario_family, entry.solver_mode or "component", entry.metric_group), []).append(entry)
    return [
        {
            "scenario_family": family,
            "solver_mode": solver_mode,
            "metric_group": metric_group,
            "entry_count": len(group_entries),
            "metrics": _counter_json(entry.metric for entry in group_entries),
            "source_components": _counter_json(entry.source_component for entry in group_entries),
        }
        for (family, solver_mode, metric_group), group_entries in sorted(groups.items())
    ]


def _dedupe_entries(entries: list[Milestone18FailureTriageEntry]) -> list[Milestone18FailureTriageEntry]:
    seen: set[str] = set()
    deduped: list[Milestone18FailureTriageEntry] = []
    for entry in entries:
        if entry.entry_id in seen:
            continue
        seen.add(entry.entry_id)
        deduped.append(entry)
    return deduped


def _records(container: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = container.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list.")
    return [item for item in value if isinstance(item, dict)]


def _manifest_nested_string(container: dict[str, Any], outer_key: str, inner_key: str) -> str:
    outer = container.get(outer_key)
    if not isinstance(outer, dict):
        raise ValueError(f"{outer_key} must be a JSON object.")
    value = outer.get(inner_key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{outer_key}.{inner_key} must be a non-empty string.")
    return value


def _scenario_grid(scenario: dict[str, Any]) -> dict[str, object]:
    grid = scenario.get("grid")
    if not isinstance(grid, dict):
        raise ValueError("scenario grid must be a JSON object.")
    required = ("nx", "ny", "dx", "dy", "origin_x", "origin_y")
    missing = [key for key in required if key not in grid]
    if missing:
        raise ValueError(f"scenario grid is missing: {', '.join(missing)}")
    return {
        "nx": int(grid["nx"]),
        "ny": int(grid["ny"]),
        "dx": float(grid["dx"]),
        "dy": float(grid["dy"]),
        "origin_x": float(grid["origin_x"]),
        "origin_y": float(grid["origin_y"]),
    }


def _constriction_feature(features_payload: dict[str, Any]) -> dict[str, object]:
    features = features_payload.get("features", [])
    if not isinstance(features, list):
        raise ValueError("features must be a list.")
    for feature in features:
        if not isinstance(feature, dict) or feature.get("kind") != "constriction":
            continue
        center = feature.get("center", {})
        if not isinstance(center, dict):
            center = {}
        return {
            "kind": "constriction",
            "center_x": float(center.get("x", 0.0)),
            "center_y": float(center.get("y", 0.0)),
            "width_m": _float_or_none(feature.get("width")),
            "length_m": _float_or_none(feature.get("length")),
            "radius_m": _float_or_none(feature.get("radius")),
            "strength": _float_or_none(feature.get("strength")),
            "angle_rad": _float_or_none(feature.get("angle")),
            "metadata": feature.get("metadata", {}),
        }
    raise ValueError("features.json does not contain a constriction feature.")


def _grid_column(x: float, grid: dict[str, object]) -> int:
    raw = int(round((x - float(grid["origin_x"])) / float(grid["dx"])))
    return max(0, min(raw, int(grid["nx"]) - 1))


def _grid_row(y: float, grid: dict[str, object]) -> int:
    raw = int(round((y - float(grid["origin_y"])) / float(grid["dy"])))
    return max(0, min(raw, int(grid["ny"]) - 1))


def _scenario_array_path(scenario_package: Path, scenario: dict[str, Any], key: str, fallback: str) -> Path:
    array_files = scenario.get("array_files", {})
    if not isinstance(array_files, dict):
        array_files = {}
    value = array_files.get(key, fallback)
    if not isinstance(value, str):
        value = fallback
    return _resolve_path(value, scenario_package)


def _final_frame_path(manifest: dict[str, Any], manifest_dir: Path) -> Path:
    frames = manifest.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ValueError("solver manifest must include at least one frame.")
    frame = frames[-1]
    if not isinstance(frame, str):
        raise ValueError("solver manifest frame entries must be strings.")
    return _resolve_path(frame, manifest_dir)


def _load_npz_water_state(path: Path, *, h_key: str) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        h = np.asarray(data[h_key], dtype=float)
        u = np.asarray(data["u"], dtype=float) if "u" in data else np.zeros_like(h)
        v = np.asarray(data["v"], dtype=float) if "v" in data else np.zeros_like(h)
        froude = np.asarray(data["froude"], dtype=float) if "froude" in data else _froude_array(h, u, v)
        wet = np.asarray(data["wet"], dtype=bool) if "wet" in data else h > 0.0
    return {"h": h, "u": u, "v": v, "froude": froude, "wet": wet}


def _load_cpp_water_csv(path: Path, ny: int, nx: int) -> dict[str, np.ndarray]:
    arrays = {
        "h": np.zeros((ny, nx), dtype=float),
        "u": np.zeros((ny, nx), dtype=float),
        "v": np.zeros((ny, nx), dtype=float),
        "froude": np.zeros((ny, nx), dtype=float),
        "wet": np.zeros((ny, nx), dtype=bool),
    }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_index = int(row["row"])
            column_index = int(row["col"])
            arrays["h"][row_index, column_index] = float(row.get("h", 0.0))
            arrays["u"][row_index, column_index] = float(row.get("u", 0.0))
            arrays["v"][row_index, column_index] = float(row.get("v", 0.0))
            arrays["froude"][row_index, column_index] = float(row.get("froude", 0.0))
            arrays["wet"][row_index, column_index] = row.get("wet", "0") in {"1", "true", "True"}
    return arrays


def _froude_array(h: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    speed = np.hypot(u, v)
    froude = np.zeros_like(h, dtype=float)
    safe_depth = np.where(h > 0.0, h, 0.0)
    np.divide(speed, np.sqrt(9.81 * safe_depth), out=froude, where=safe_depth > 0.0)
    return froude


def _constriction_throat_profile(
    label: str,
    source_path: Path,
    state: dict[str, np.ndarray],
    grid: dict[str, object],
    throat_column: int,
    center_row: int,
    wet_depth_threshold_m: float,
) -> Milestone18ConstrictionThroatProfile:
    h_col = state["h"][:, throat_column]
    u_col = state["u"][:, throat_column]
    v_col = state["v"][:, throat_column]
    wet_mask = h_col > wet_depth_threshold_m
    wet_count = int(np.count_nonzero(wet_mask))
    if wet_count:
        wet_depths = h_col[wet_mask]
        abs_v = np.abs(v_col[wet_mask])
        mean_wet_depth = float(np.mean(wet_depths))
        max_abs_v = float(np.max(abs_v))
        mean_abs_v = float(np.mean(abs_v))
    else:
        mean_wet_depth = 0.0
        max_abs_v = 0.0
        mean_abs_v = 0.0
    return Milestone18ConstrictionThroatProfile(
        label=label,
        source_path=str(source_path),
        column_index=throat_column,
        center_row_index=center_row,
        wet_depth_threshold_m=wet_depth_threshold_m,
        wet_cell_count=wet_count,
        wet_width_m=wet_count * float(grid["dy"]),
        center_depth_m=float(state["h"][center_row, throat_column]),
        max_depth_m=float(np.max(h_col)) if h_col.size else 0.0,
        mean_wet_depth_m=mean_wet_depth,
        column_mass_m3=float(np.sum(h_col) * float(grid["dx"]) * float(grid["dy"])),
        center_downstream_velocity_mps=float(u_col[center_row]),
        max_abs_cross_stream_velocity_mps=max_abs_v,
        mean_abs_cross_stream_velocity_mps=mean_abs_v,
        center_froude=float(state["froude"][center_row, throat_column]),
    )


def _constriction_profile_delta(
    candidate: Milestone18ConstrictionThroatProfile,
    reference: Milestone18ConstrictionThroatProfile,
) -> Milestone18ConstrictionThroatDelta:
    return Milestone18ConstrictionThroatDelta(
        candidate_label=candidate.label,
        reference_label=reference.label,
        wet_width_m=candidate.wet_width_m - reference.wet_width_m,
        center_depth_m=candidate.center_depth_m - reference.center_depth_m,
        max_depth_m=candidate.max_depth_m - reference.max_depth_m,
        mean_wet_depth_m=candidate.mean_wet_depth_m - reference.mean_wet_depth_m,
        column_mass_m3=candidate.column_mass_m3 - reference.column_mass_m3,
        center_downstream_velocity_mps=(
            candidate.center_downstream_velocity_mps - reference.center_downstream_velocity_mps
        ),
        max_abs_cross_stream_velocity_mps=(
            candidate.max_abs_cross_stream_velocity_mps - reference.max_abs_cross_stream_velocity_mps
        ),
        mean_abs_cross_stream_velocity_mps=(
            candidate.mean_abs_cross_stream_velocity_mps - reference.mean_abs_cross_stream_velocity_mps
        ),
        center_froude=candidate.center_froude - reference.center_froude,
    )


def _constriction_column_profile(
    label: str,
    source_path: Path,
    state: dict[str, np.ndarray],
    grid: dict[str, object],
    column_index: int,
    wet_depth_threshold_m: float,
) -> Milestone18ConstrictionColumnProfile:
    h_col = state["h"][:, column_index]
    u_col = state["u"][:, column_index]
    v_col = state["v"][:, column_index]
    froude_col = state["froude"][:, column_index]
    wet_mask = h_col > wet_depth_threshold_m
    wet_count = int(np.count_nonzero(wet_mask))
    first_row, last_row, wet_center_y = _wet_row_span(wet_mask, grid)
    if wet_count:
        wet_depths = h_col[wet_mask]
        mean_wet_depth = float(np.mean(wet_depths))
        mean_u = float(np.mean(u_col[wet_mask]))
        mean_v = float(np.mean(v_col[wet_mask]))
        mean_froude = float(np.mean(froude_col[wet_mask]))
    else:
        mean_wet_depth = 0.0
        mean_u = 0.0
        mean_v = 0.0
        mean_froude = 0.0
    return Milestone18ConstrictionColumnProfile(
        label=label,
        source_path=str(source_path),
        column_index=column_index,
        x_m=float(grid["origin_x"]) + column_index * float(grid["dx"]),
        wet_depth_threshold_m=wet_depth_threshold_m,
        wet_cell_count=wet_count,
        wet_width_m=wet_count * float(grid["dy"]),
        first_wet_row_index=first_row,
        last_wet_row_index=last_row,
        wet_center_y_m=wet_center_y,
        mean_wet_depth_m=mean_wet_depth,
        max_depth_m=float(np.max(h_col)) if h_col.size else 0.0,
        column_mass_m3=float(np.sum(h_col) * float(grid["dx"]) * float(grid["dy"])),
        mean_downstream_velocity_mps=mean_u,
        mean_cross_stream_velocity_mps=mean_v,
        mean_wet_froude=mean_froude,
    )


def _constriction_column_delta(
    candidate: Milestone18ConstrictionColumnProfile,
    reference: Milestone18ConstrictionColumnProfile,
    candidate_mask: np.ndarray,
    reference_mask: np.ndarray,
) -> Milestone18ConstrictionColumnDelta:
    mismatch_count = int(np.count_nonzero(candidate_mask ^ reference_mask))
    cell_count = max(1, int(candidate_mask.size))
    return Milestone18ConstrictionColumnDelta(
        candidate_label=candidate.label,
        reference_label=reference.label,
        column_index=candidate.column_index,
        x_m=candidate.x_m,
        mask_mismatch_count=mismatch_count,
        mask_mismatch_fraction=mismatch_count / cell_count,
        wet_cell_count=candidate.wet_cell_count - reference.wet_cell_count,
        wet_width_m=candidate.wet_width_m - reference.wet_width_m,
        first_wet_row_delta=_optional_int_delta(candidate.first_wet_row_index, reference.first_wet_row_index),
        last_wet_row_delta=_optional_int_delta(candidate.last_wet_row_index, reference.last_wet_row_index),
        wet_center_y_delta_m=_optional_float_delta(candidate.wet_center_y_m, reference.wet_center_y_m),
        mean_wet_depth_m=candidate.mean_wet_depth_m - reference.mean_wet_depth_m,
        max_depth_m=candidate.max_depth_m - reference.max_depth_m,
        column_mass_m3=candidate.column_mass_m3 - reference.column_mass_m3,
        mean_downstream_velocity_mps=(
            candidate.mean_downstream_velocity_mps - reference.mean_downstream_velocity_mps
        ),
        mean_cross_stream_velocity_mps=(
            candidate.mean_cross_stream_velocity_mps - reference.mean_cross_stream_velocity_mps
        ),
        mean_wet_froude=candidate.mean_wet_froude - reference.mean_wet_froude,
    )


def _constriction_mask_blocked_reasons(
    comparisons: tuple[Milestone18ConstrictionColumnComparison, ...],
    domain_mask_mismatch_fraction: float,
    grid: dict[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    deltas = tuple(comparison.cpp_minus_geoclaw for comparison in comparisons)
    max_width_delta = max((abs(delta.wet_width_m) for delta in deltas), default=0.0)
    max_bank_row_delta = max(
        (
            abs(value)
            for delta in deltas
            for value in (delta.first_wet_row_delta, delta.last_wet_row_delta)
            if value is not None
        ),
        default=0,
    )
    max_mean_depth_delta = max((abs(delta.mean_wet_depth_m) for delta in deltas), default=0.0)
    max_column_mass_delta = max((abs(delta.column_mass_m3) for delta in deltas), default=0.0)
    if domain_mask_mismatch_fraction > 0.02:
        reasons.append("Final-frame C++ wet/dry mask mismatch exceeds the 0.02 comparison threshold.")
    if max_width_delta > float(grid["dy"]):
        reasons.append("At least one C++ constriction column differs from GeoClaw wet width by more than one lateral cell.")
    if max_bank_row_delta > 1:
        reasons.append("At least one C++ constriction bank span differs from GeoClaw by more than one row.")
    if max_mean_depth_delta > 0.25:
        reasons.append("At least one C++ constriction column differs from GeoClaw mean wet depth by more than 0.25 m.")
    if max_column_mass_delta > 0.5 * float(grid["dx"]) * float(grid["dy"]):
        reasons.append("At least one C++ constriction column mass differs from GeoClaw beyond the diagnostic budget.")
    return tuple(reasons)


def _wet_row_span(wet_mask: np.ndarray, grid: dict[str, object]) -> tuple[int | None, int | None, float | None]:
    rows = np.flatnonzero(wet_mask)
    if not rows.size:
        return None, None, None
    first_row = int(rows[0])
    last_row = int(rows[-1])
    wet_center_y = float(grid["origin_y"]) + ((first_row + last_row) * 0.5) * float(grid["dy"])
    return first_row, last_row, wet_center_y


def _optional_int_delta(candidate: int | None, reference: int | None) -> int | None:
    if candidate is None or reference is None:
        return None
    return candidate - reference


def _optional_float_delta(candidate: float | None, reference: float | None) -> float | None:
    if candidate is None or reference is None:
        return None
    return candidate - reference


def _constriction_throat_blocked_reasons(
    cpp_minus_geoclaw: Milestone18ConstrictionThroatDelta,
    grid: dict[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    one_cell_width = float(grid["dy"])
    if abs(cpp_minus_geoclaw.wet_width_m) > one_cell_width:
        reasons.append("C++ throat wet width differs from GeoClaw by more than one lateral cell.")
    if abs(cpp_minus_geoclaw.center_depth_m) > 0.25:
        reasons.append("C++ throat center depth differs from GeoClaw by more than 0.25 m.")
    if abs(cpp_minus_geoclaw.mean_wet_depth_m) > 0.25:
        reasons.append("C++ throat mean wet depth differs from GeoClaw by more than 0.25 m.")
    if abs(cpp_minus_geoclaw.max_abs_cross_stream_velocity_mps) > 0.5:
        reasons.append("C++ throat cross-stream velocity envelope differs from GeoClaw by more than 0.5 m/s.")
    if abs(cpp_minus_geoclaw.center_froude) > 0.5:
        reasons.append("C++ throat center Froude differs from GeoClaw by more than 0.5.")
    return tuple(reasons)


def _pin_release_flow_case(
    *,
    flow_band: str,
    discharge_cms: float,
    water_depth_m: float,
    approach_velocity_mps: float,
    approach_angle_deg: float,
    raft_orientation_deg: float,
    contact_normal: tuple[float, float],
    wrap_depth_m: float,
    side_load_n: float,
    pin_force_n: float,
    stickiness_factor: float,
    neutral: CrewWeightTelemetry2_5D,
    release: CrewWeightTelemetry2_5D,
    action_window_s: float,
    response_paths: tuple[str, ...],
    failed_rescue: Any | None = None,
) -> Milestone18PinReleaseFlowCase:
    paths = tuple(
        _pin_release_response_path(
            path_id=path_id,
            flow_band=flow_band,
            pin_force_n=pin_force_n,
            side_load_n=side_load_n,
            stickiness_factor=stickiness_factor,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            failed_rescue=failed_rescue,
        )
        for path_id in response_paths
    )
    checks = (
        _check("flow_band_recorded", bool(flow_band), 1.0 if flow_band else 0.0, 1.0),
        _check("positive_discharge", discharge_cms > 0.0, discharge_cms, 0.0),
        _check("positive_depth", water_depth_m > 0.0, water_depth_m, 0.0),
        _check("wrap_depth_recorded", wrap_depth_m > 0.0, wrap_depth_m, 0.0),
        _check("side_load_recorded", side_load_n > 0.0, side_load_n, 0.0),
        _check("pin_force_recorded", pin_force_n > 0.0, pin_force_n, 0.0),
    )
    return Milestone18PinReleaseFlowCase(
        flow_band=flow_band,
        discharge_cms=discharge_cms,
        water_depth_m=water_depth_m,
        approach_velocity_mps=approach_velocity_mps,
        approach_angle_deg=approach_angle_deg,
        raft_orientation_deg=raft_orientation_deg,
        contact_normal=contact_normal,
        wrap_depth_m=wrap_depth_m,
        side_load_n=side_load_n,
        pin_force_n=pin_force_n,
        stickiness_factor=stickiness_factor,
        response_paths=paths,
        checks=checks,
    )


def _pin_release_response_path(
    *,
    path_id: str,
    flow_band: str,
    pin_force_n: float,
    side_load_n: float,
    stickiness_factor: float,
    neutral: CrewWeightTelemetry2_5D,
    release: CrewWeightTelemetry2_5D,
    action_window_s: float,
    failed_rescue: Any | None,
) -> Milestone18PinReleaseResponsePath:
    if path_id in {"timed_high_side_release", "late_high_side_failed_rescue"}:
        telemetry = release
        response_delay = 0.42 if path_id == "timed_high_side_release" else 1.05
        release_drive = _crew_release_drive_n(pin_force_n, side_load_n, neutral, telemetry)
    else:
        telemetry = neutral
        response_delay = None
        release_drive = _base_release_drive_n(pin_force_n, side_load_n)
    pin_margin = pin_force_n - telemetry.recovery_thresholds.pin_threshold_n
    release_margin = release_drive - telemetry.recovery_thresholds.release_threshold_n
    window_margin = None if response_delay is None else action_window_s - response_delay
    swimmer = _swimmer_summary(failed_rescue) if path_id == "late_high_side_failed_rescue" and failed_rescue is not None else None
    outcome = _pin_release_outcome(
        path_id=path_id,
        flow_band=flow_band,
        stickiness_factor=stickiness_factor,
        pin_margin=pin_margin,
        release_margin=release_margin,
        window_margin=window_margin,
        swimmer=swimmer,
    )
    checks = _pin_release_path_checks(
        path_id=path_id,
        flow_band=flow_band,
        outcome=outcome,
        stickiness_factor=stickiness_factor,
        pin_margin=pin_margin,
        release_margin=release_margin,
        window_margin=window_margin,
        telemetry=telemetry,
        swimmer=swimmer,
    )
    return Milestone18PinReleaseResponsePath(
        path_id=path_id,
        response_delay_s=response_delay,
        outcome=outcome,
        pin_margin_n=pin_margin,
        release_margin_n=release_margin,
        action_window_margin_s=window_margin,
        crew_weight=_crew_weight_summary(telemetry),
        swimmer=swimmer,
        checks=checks,
    )


def _base_release_drive_n(pin_force_n: float, side_load_n: float) -> float:
    return max(650.0, 0.12 * pin_force_n + 0.32 * side_load_n)


def _crew_release_drive_n(
    pin_force_n: float,
    side_load_n: float,
    neutral: CrewWeightTelemetry2_5D,
    telemetry: CrewWeightTelemetry2_5D,
) -> float:
    threshold_gain = max(
        0.0,
        neutral.recovery_thresholds.release_threshold_n - telemetry.recovery_thresholds.release_threshold_n,
    )
    crew_action_gain = (
        telemetry.high_side_count * 55.0
        + telemetry.brace_count * 35.0
        + telemetry.recovery_count * 60.0
    )
    return _base_release_drive_n(pin_force_n, side_load_n) + 1500.0 + threshold_gain + crew_action_gain


def _pin_release_outcome(
    *,
    path_id: str,
    flow_band: str,
    stickiness_factor: float,
    pin_margin: float,
    release_margin: float,
    window_margin: float | None,
    swimmer: dict[str, object] | None,
) -> str:
    if path_id == "late_high_side_failed_rescue":
        return "failed_rescue" if swimmer and not bool(swimmer.get("rescue_completed")) else "pinned"
    if path_id == "timed_high_side_release":
        return "released" if release_margin >= 0.0 and (window_margin or 0.0) >= 0.0 else "pinned"
    if flow_band == "low_scrape":
        return "scraped_clear"
    if flow_band == "high_washout":
        return "flushed_washout"
    if stickiness_factor < 0.7 and pin_margin < 0.0:
        return "clear"
    return "pinned" if pin_margin >= 0.0 else "clear"


def _pin_release_path_checks(
    *,
    path_id: str,
    flow_band: str,
    outcome: str,
    stickiness_factor: float,
    pin_margin: float,
    release_margin: float,
    window_margin: float | None,
    telemetry: CrewWeightTelemetry2_5D,
    swimmer: dict[str, object] | None,
) -> tuple[dict[str, object], ...]:
    if path_id == "no_action_pin":
        return (
            _check("sticky_flow_band", stickiness_factor >= 1.0, stickiness_factor, 1.0),
            _check("no_action_pins", outcome == "pinned" and pin_margin >= 0.0, pin_margin, 0.0),
            _check("release_margin_negative_without_action", release_margin < 0.0, release_margin, 0.0),
            _check("crew_action_absent", telemetry.active_action_count == 0, float(telemetry.active_action_count), 0.0),
        )
    if path_id == "timed_high_side_release":
        return (
            _check("timed_response_inside_window", (window_margin or -1.0) >= 0.0, window_margin or -1.0, 0.0),
            _check("release_margin_positive", release_margin >= 0.0, release_margin, 0.0),
            _check("crew_actions_recorded", telemetry.high_side_count > 0 and telemetry.recovery_count > 0, float(telemetry.active_action_count), 1.0),
            _check("outcome_released", outcome == "released", 1.0 if outcome == "released" else 0.0, 1.0),
        )
    if path_id == "late_high_side_failed_rescue":
        rescue_completed = bool(swimmer and swimmer.get("rescue_completed"))
        return (
            _check("late_response_misses_window", (window_margin or 1.0) < 0.0, window_margin or 1.0, 0.0),
            _check("failed_rescue_recorded", swimmer is not None and not rescue_completed, 0.0 if rescue_completed else 1.0, 1.0),
            _check("swimmer_state_recorded", bool(swimmer and swimmer.get("states")), 1.0 if swimmer and swimmer.get("states") else 0.0, 1.0),
            _check("outcome_failed_rescue", outcome == "failed_rescue", 1.0 if outcome == "failed_rescue" else 0.0, 1.0),
        )
    if path_id == "no_action_scrape":
        return (
            _check("low_flow_less_sticky", flow_band == "low_scrape" and stickiness_factor < 0.7, stickiness_factor, 0.7),
            _check("low_flow_not_pinned", pin_margin < 0.0, pin_margin, 0.0),
            _check("outcome_scraped_clear", outcome == "scraped_clear", 1.0 if outcome == "scraped_clear" else 0.0, 1.0),
        )
    if path_id == "no_action_washout":
        return (
            _check("high_flow_washes_out", flow_band == "high_washout" and stickiness_factor < 0.7, stickiness_factor, 0.7),
            _check("washout_not_pinned", pin_margin < 0.0, pin_margin, 0.0),
            _check("outcome_flushed_washout", outcome == "flushed_washout", 1.0 if outcome == "flushed_washout" else 0.0, 1.0),
        )
    return (_check("known_path", False, 0.0, 1.0),)


def _crew_weight_summary(telemetry: CrewWeightTelemetry2_5D) -> dict[str, object]:
    return {
        "occupied_seat_count": telemetry.occupied_seat_count,
        "active_action_count": telemetry.active_action_count,
        "high_side_count": telemetry.high_side_count,
        "brace_count": telemetry.brace_count,
        "recovery_count": telemetry.recovery_count,
        "combined_center_of_gravity_offset": _vec_json(telemetry.combined_center_of_gravity_offset),
        "roll_moment_nm": telemetry.roll_moment_nm,
        "contact_loading": {
            "lateral_bias": telemetry.contact_loading.lateral_bias,
            "left_tube_normal_load_n": telemetry.contact_loading.left_tube_normal_load_n,
            "right_tube_normal_load_n": telemetry.contact_loading.right_tube_normal_load_n,
        },
        "recovery_thresholds": {
            "pin_threshold_n": telemetry.recovery_thresholds.pin_threshold_n,
            "release_threshold_n": telemetry.recovery_thresholds.release_threshold_n,
            "flip_threshold_nm": telemetry.recovery_thresholds.flip_threshold_nm,
            "pin_threshold_multiplier": telemetry.recovery_thresholds.pin_threshold_multiplier,
            "release_threshold_multiplier": telemetry.recovery_thresholds.release_threshold_multiplier,
            "flip_threshold_multiplier": telemetry.recovery_thresholds.flip_threshold_multiplier,
        },
    }


def _swimmer_summary(telemetry: Any) -> dict[str, object]:
    return {
        "fixture_id": telemetry.fixture_id,
        "trigger_kind": telemetry.trigger_kind,
        "states": list(telemetry.states),
        "overboard_triggered": telemetry.overboard_triggered,
        "rescue_completed": telemetry.rescue_completed,
        "swimmer_world_position": _vec_json(telemetry.swimmer_world_position),
        "swimmer_distance_m": telemetry.swimmer_distance_m,
        "time_in_water_s": telemetry.time_in_water_s,
        "rescue_method": telemetry.rescue_method,
        "failed_reason": telemetry.failed_reason,
        "fatigue_delta": telemetry.fatigue_delta,
        "trust_delta": telemetry.trust_delta,
        "safety_score_delta": telemetry.safety_score_delta,
    }


def _vec_json(value: Vec3) -> dict[str, float]:
    return {"x": value.x, "y": value.y, "z": value.z}


def _check(name: str, passed: bool, value: float, threshold: float, details: str = "") -> dict[str, object]:
    return {
        "name": name,
        "passed": passed,
        "value": value,
        "threshold": threshold,
        "details": details,
    }


def _parity_mode_result(
    *,
    solver_mode: str,
    threshold_report: Path,
    candidate_label: str,
) -> Milestone18ParityModeResult:
    threshold = _load_json_report(threshold_report)
    checks = tuple(dict(check) for check in _records(threshold, "checks"))
    failing_checks = tuple(str(check.get("name", "unknown_check")) for check in checks if not bool(check.get("passed")))
    comparison_dir = threshold_report.parent
    manifest_path = comparison_dir / "dual_solver_manifest.json"
    manifest_ref = str(manifest_path) if manifest_path.exists() else None
    tuning_parameters: dict[str, object] = {}
    notes: list[str] = []
    if manifest_path.exists():
        manifest = _load_json_report(manifest_path)
        cpp_entry = manifest.get("cpp", {})
        if isinstance(cpp_entry, dict):
            cpp_manifest_ref = cpp_entry.get("manifest")
            if isinstance(cpp_manifest_ref, str):
                cpp_manifest_path = _resolve_path(cpp_manifest_ref, manifest_path.parent)
                if cpp_manifest_path.exists():
                    cpp_manifest = _load_json_report(cpp_manifest_path)
                    for key in (
                        "solver_mode",
                        "boundary_mode",
                        "flux_scheme",
                        "cfl",
                        "dry_tolerance",
                        "feature_strength_scale",
                        "roughness_scale",
                        "bed_slope_source_scale",
                        "preserve_initial_mass",
                    ):
                        if key in cpp_manifest:
                            tuning_parameters[key] = cpp_manifest[key]
    feature_scale = _float_or_none(tuning_parameters.get("feature_strength_scale"))
    if feature_scale is not None and feature_scale > 0.0:
        notes.append("Feature forcing is nonzero for this retune candidate; verify it is justified by the fixture.")
    return Milestone18ParityModeResult(
        solver_mode=solver_mode,
        candidate_label=candidate_label,
        promoted=bool(threshold.get("passed")),
        threshold_report=str(threshold_report),
        comparison_dir=str(comparison_dir),
        manifest=manifest_ref,
        tuning_parameters=tuning_parameters,
        failing_checks=failing_checks,
        checks=checks,
        notes=tuple(notes),
    )


def _resolve_reference_source_manifest(reference_manifest: Path, payload: dict[str, Any]) -> Path | None:
    source_ref = payload.get("source_export_manifest")
    if isinstance(source_ref, str):
        return _resolve_path(source_ref, reference_manifest.parent)
    if payload.get("schema") == "raftsim.geoclaw_export.v1":
        return reference_manifest
    return None


def _resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (base / path, Path.cwd() / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_json_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _counter_json(values) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _entry_id(*parts: object) -> str:
    return "/".join(_slug(str(part)) for part in parts if part is not None and str(part))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip()).strip("_") or "unknown"


def _format_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.6g}"


def _row_span_markdown(profile: Milestone18ConstrictionColumnProfile) -> str:
    if profile.first_wet_row_index is None or profile.last_wet_row_index is None:
        return "dry"
    return f"{profile.first_wet_row_index}-{profile.last_wet_row_index}"


def _markdown_counter_table(label: str, counts: object) -> str:
    if not isinstance(counts, dict) or not counts:
        return f"No {label.lower()} entries."
    lines = [f"| {label} | Entries |", "| --- | ---: |"]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
