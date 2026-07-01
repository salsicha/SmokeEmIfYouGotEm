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
from .comparison import (
    CROSS_SECTION_FIELD_NAMES,
    DEFAULT_VELOCITY_DEPTH_FLOOR,
    FIELD_NAMES,
    PROBE_FIELD_NAMES,
    SLOPE_FIELD_NAMES,
    VELOCITY_LIKE_FIELD_NAMES,
)
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
MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA = "raftsim.milestone18.constriction_response_timing.v0"
MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA = "raftsim.milestone18.constriction_shape_timing.v0"
MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA = (
    "raftsim.milestone18.constriction_probe_cross_section.v0"
)
MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA = (
    "raftsim.milestone18.constriction_lateral_face_flux.v0"
)
MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA = (
    "raftsim.milestone18.constriction_face_source_audit.v0"
)
MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA = (
    "raftsim.milestone18.constriction_face_state_width_depth.v0"
)
MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA = (
    "raftsim.milestone18.constriction_hydrostatic_source_decision.v0"
)
MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA = (
    "raftsim.milestone18.drop_ledge_hydraulic_control.v0"
)
MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA = (
    "raftsim.milestone18.remaining_geometry_closure.v0"
)

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
class Milestone18ConstrictionZoneSnapshot:
    """One solver/frame summary for a constriction response zone."""

    solver_label: str
    zone_id: str
    frame_index: int
    source_path: str
    time_s: float
    column_indices: tuple[int, ...]
    wet_cell_count: int
    total_mass_m3: float
    mean_wet_depth_m: float
    max_depth_m: float
    mean_downstream_velocity_mps: float
    mean_cross_stream_velocity_mps: float
    kinetic_energy_like_j: float
    max_froude: float
    mean_wet_froude: float

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["column_indices"] = list(self.column_indices)
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionZoneDelta:
    """C++ minus GeoClaw final and peak timing deltas for one constriction zone."""

    zone_id: str
    column_indices: tuple[int, ...]
    final_mass_delta_m3: float
    final_mean_wet_depth_delta_m: float
    final_max_depth_delta_m: float
    final_kinetic_energy_delta_j: float
    final_max_froude_delta: float
    peak_mass_delta_m3: float
    peak_mass_time_delta_s: float
    peak_energy_delta_j: float
    peak_energy_time_delta_s: float

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["column_indices"] = list(self.column_indices)
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionResponseTimingReport:
    """Diagnostic report for constriction depth, mass, energy, and timing response."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    wet_depth_threshold_m: float
    zones: dict[str, tuple[int, ...]]
    geoclaw_snapshots: tuple[Milestone18ConstrictionZoneSnapshot, ...]
    cpp_snapshots: tuple[Milestone18ConstrictionZoneSnapshot, ...]
    zone_deltas: tuple[Milestone18ConstrictionZoneDelta, ...]
    thresholds: dict[str, float]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "thresholds": self.thresholds,
            "summary": {
                "zone_count": len(self.zone_deltas),
                "max_abs_final_mass_delta_m3": max(
                    (abs(delta.final_mass_delta_m3) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "max_abs_final_mean_wet_depth_delta_m": max(
                    (abs(delta.final_mean_wet_depth_delta_m) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "max_abs_final_kinetic_energy_delta_j": max(
                    (abs(delta.final_kinetic_energy_delta_j) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "max_abs_peak_energy_time_delta_s": max(
                    (abs(delta.peak_energy_time_delta_s) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "max_abs_peak_energy_delta_j": max(
                    (abs(delta.peak_energy_delta_j) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "max_abs_final_froude_delta": max(
                    (abs(delta.final_max_froude_delta) for delta in self.zone_deltas),
                    default=0.0,
                ),
                "worst_zones": [delta.to_json_dict() for delta in self._worst_zones()],
            },
            "zone_deltas": [delta.to_json_dict() for delta in self.zone_deltas],
            "snapshots": {
                "geoclaw": [snapshot.to_json_dict() for snapshot in self.geoclaw_snapshots],
                "cpp": [snapshot.to_json_dict() for snapshot in self.cpp_snapshots],
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
            "# Milestone 18 Constriction Response Timing Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_RESPONSE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            "",
            "## Zones",
            "",
            "| Zone | Columns |",
            "| --- | --- |",
        ]
        for zone_id, columns in self.zones.items():
            lines.append(f"| `{zone_id}` | `{_column_span(columns)}` |")
        lines.extend(
            [
                "",
                "## Final And Peak Deltas",
                "",
                "| Zone | Final mass m3 | Final mean depth m | Final max depth m | Final energy | Peak mass m3 | Peak mass time s | Peak energy | Peak energy time s | Final max Froude |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for delta in self.zone_deltas:
            lines.append(
                "| "
                f"`{delta.zone_id}` | "
                f"{delta.final_mass_delta_m3:.6g} | "
                f"{delta.final_mean_wet_depth_delta_m:.6g} | "
                f"{delta.final_max_depth_delta_m:.6g} | "
                f"{delta.final_kinetic_energy_delta_j:.6g} | "
                f"{delta.peak_mass_delta_m3:.6g} | "
                f"{delta.peak_mass_time_delta_s:.6g} | "
                f"{delta.peak_energy_delta_j:.6g} | "
                f"{delta.peak_energy_time_delta_s:.6g} | "
                f"{delta.final_max_froude_delta:.6g} |"
            )
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_zones(self) -> tuple[Milestone18ConstrictionZoneDelta, ...]:
        return tuple(
            sorted(
                self.zone_deltas,
                key=lambda delta: (
                    abs(delta.final_mass_delta_m3),
                    abs(delta.final_kinetic_energy_delta_j),
                    abs(delta.peak_energy_time_delta_s),
                    abs(delta.final_mean_wet_depth_delta_m),
                ),
                reverse=True,
            )[:4]
        )


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionShapeErrorSample:
    """Worst observed shape/timing error for one field, slope, probe, or cross-section metric."""

    category: str
    field: str
    source_id: str
    value: float
    threshold: float
    ratio_to_threshold: float
    frame_label: str | None = None
    frame_index: int | None = None
    time_s: float | None = None
    distance_m: float | None = None
    row_index: int | None = None
    column_index: int | None = None
    x_m: float | None = None
    y_m: float | None = None
    zone_id: str | None = None
    reference_value: float | None = None
    candidate_value: float | None = None
    delta: float | None = None
    reference_path: str | None = None
    cpp_path: str | None = None

    @property
    def passed(self) -> bool:
        return self.value <= self.threshold

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionShapeTimingReport:
    """Diagnostic report locating constriction field, slope, probe, and cross-section blockers."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    wet_depth_threshold_m: float
    velocity_depth_floor_m: float
    zones: dict[str, tuple[int, ...]]
    thresholds: dict[str, float]
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]
    slope_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]
    probe_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]
    cross_section_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    @property
    def samples(self) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
        return self.field_samples + self.slope_samples + self.probe_samples + self.cross_section_samples

    def to_json_dict(self) -> dict[str, object]:
        sample_groups = {
            "field": self.field_samples,
            "slope": self.slope_samples,
            "probe": self.probe_samples,
            "cross_section": self.cross_section_samples,
        }
        return {
            "schema_version": MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "velocity_depth_floor_m": self.velocity_depth_floor_m,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "thresholds": self.thresholds,
            "summary": {
                "sample_count": len(self.samples),
                "max_field_linf": _max_sample_value(self.field_samples),
                "max_slope_linf": _max_sample_value(self.slope_samples),
                "max_probe_linf": _max_sample_value(self.probe_samples),
                "max_cross_section_linf": _max_sample_value(self.cross_section_samples),
                "worst_overall": [sample.to_json_dict() for sample in self._worst_overall()],
            },
            "samples": {
                category: [sample.to_json_dict() for sample in samples]
                for category, samples in sample_groups.items()
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Constriction Shape/Timing Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_SHAPE_TIMING_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            f"Velocity depth floor: `{self.velocity_depth_floor_m:.6g}` m",
            "",
            "## Summary",
            "",
            f"- Max field Linf: `{_format_number(_float_or_none(summary.get('max_field_linf')))}`",
            f"- Max slope Linf: `{_format_number(_float_or_none(summary.get('max_slope_linf')))}`",
            f"- Max probe Linf: `{_format_number(_float_or_none(summary.get('max_probe_linf')))}`",
            f"- Max cross-section Linf: `{_format_number(_float_or_none(summary.get('max_cross_section_linf')))}`",
            "",
            "## Zones",
            "",
            "| Zone | Columns |",
            "| --- | --- |",
        ]
        for zone_id, columns in self.zones.items():
            lines.append(f"| `{zone_id}` | `{_column_span(columns)}` |")
        lines.extend(
            [
                "",
                "## Worst Field And Slope Cells",
                "",
                "| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for sample in self._worst_grid_samples():
            lines.append(_shape_sample_grid_row(sample))
        lines.extend(
            [
                "",
                "## Worst Probe And Cross-Section Series",
                "",
                "| Category | Sample | Field | Time s | Distance m | Abs error | Threshold | Ratio |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for sample in self._worst_series_samples():
            lines.append(_shape_sample_series_row(sample))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_overall(self) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
        return tuple(sorted(self.samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])

    def _worst_grid_samples(self) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
        samples = self.field_samples + self.slope_samples
        return tuple(sorted(samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])

    def _worst_series_samples(self) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
        samples = self.probe_samples + self.cross_section_samples
        return tuple(sorted(samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionProbeCrossSectionSample:
    """Worst raw point-probe or cross-section mismatch for one sampled field."""

    category: str
    sample_id: str
    field: str
    value: float
    threshold: float
    ratio_to_threshold: float
    time_s: float
    reference_value: float
    candidate_value: float
    delta: float
    reference_h: float
    candidate_h: float
    reference_u: float
    candidate_u: float
    reference_v: float
    candidate_v: float
    reference_froude: float
    candidate_froude: float
    distance_m: float | None = None
    x_m: float | None = None
    y_m: float | None = None
    row_index: int | None = None
    column_index: int | None = None
    zone_id: str | None = None
    reference_path: str | None = None
    cpp_path: str | None = None

    @property
    def passed(self) -> bool:
        return self.value <= self.threshold

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionProbeCrossSectionReport:
    """Diagnostic report locating raw constriction probe and cross-section blocker samples."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    velocity_depth_floor_m: float
    zones: dict[str, tuple[int, ...]]
    thresholds: dict[str, float]
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    @property
    def samples(self) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
        return self.probe_samples + self.cross_section_samples

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "velocity_depth_floor_m": self.velocity_depth_floor_m,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "thresholds": self.thresholds,
            "summary": {
                "sample_count": len(self.samples),
                "max_probe_linf": _max_raw_series_sample_value(self.probe_samples),
                "max_cross_section_linf": _max_raw_series_sample_value(self.cross_section_samples),
                "worst_overall": [sample.to_json_dict() for sample in self._worst_overall()],
            },
            "samples": {
                "probe": [sample.to_json_dict() for sample in self.probe_samples],
                "cross_section": [sample.to_json_dict() for sample in self.cross_section_samples],
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Constriction Probe/Cross-Section Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_PROBE_CROSS_SECTION_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Velocity depth floor: `{self.velocity_depth_floor_m:.6g}` m",
            "",
            "## Summary",
            "",
            f"- Max probe Linf: `{_format_number(_float_or_none(summary.get('max_probe_linf')))}`",
            f"- Max cross-section Linf: `{_format_number(_float_or_none(summary.get('max_cross_section_linf')))}`",
            "",
            "## Worst Raw Samples",
            "",
            "| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |",
            "| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
        for sample in self._worst_overall():
            lines.append(_probe_cross_section_sample_row(sample))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_overall(self) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
        return tuple(sorted(self.samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])


@dataclass(frozen=True, slots=True)
class Milestone18DropLedgeZoneSummary:
    """Final-frame water-shape summary for one drop/ledge control zone."""

    zone_id: str
    columns: tuple[int, ...]
    reference_mean_h: float
    candidate_mean_h: float
    mean_h_delta: float
    reference_mean_eta: float
    candidate_mean_eta: float
    mean_eta_delta: float
    reference_mean_u: float
    candidate_mean_u: float
    mean_u_delta: float
    reference_mean_froude: float
    candidate_mean_froude: float
    mean_froude_delta: float
    reference_wet_cell_count: int
    candidate_wet_cell_count: int

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone18DropLedgeHydraulicControlReport:
    """Diagnostic report locating drop/ledge hydraulic-control and tailwater blockers."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    ledge_feature: dict[str, object]
    downstream_feature: dict[str, object] | None
    grid: dict[str, object]
    wet_depth_threshold_m: float
    velocity_depth_floor_m: float
    zones: dict[str, tuple[int, ...]]
    thresholds: dict[str, float]
    zone_summaries: tuple[Milestone18DropLedgeZoneSummary, ...]
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    @property
    def raw_samples(self) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
        return self.probe_samples + self.cross_section_samples

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "ledge_feature": self.ledge_feature,
            "downstream_feature": self.downstream_feature,
            "grid": self.grid,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "velocity_depth_floor_m": self.velocity_depth_floor_m,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "thresholds": self.thresholds,
            "summary": {
                "sample_count": len(self.field_samples) + len(self.raw_samples),
                "max_final_field_linf": _max_sample_value(self.field_samples),
                "max_probe_linf": _max_raw_series_sample_value(self.probe_samples),
                "max_cross_section_linf": _max_raw_series_sample_value(self.cross_section_samples),
                "max_abs_zone_mean_eta_delta_m": max(
                    (abs(summary.mean_eta_delta) for summary in self.zone_summaries),
                    default=0.0,
                ),
                "max_abs_zone_mean_h_delta_m": max(
                    (abs(summary.mean_h_delta) for summary in self.zone_summaries),
                    default=0.0,
                ),
                "worst_final_field_samples": [sample.to_json_dict() for sample in self._worst_field_samples()],
                "worst_raw_samples": [sample.to_json_dict() for sample in self._worst_raw_samples()],
            },
            "zone_summaries": [summary.to_json_dict() for summary in self.zone_summaries],
            "samples": {
                "final_field": [sample.to_json_dict() for sample in self.field_samples],
                "probe": [sample.to_json_dict() for sample in self.probe_samples],
                "cross_section": [sample.to_json_dict() for sample in self.cross_section_samples],
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Drop/Ledge Hydraulic-Control Diagnostic",
            "",
            f"Schema: `{MILESTONE18_DROP_LEDGE_HYDRAULIC_CONTROL_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            f"Velocity depth floor: `{self.velocity_depth_floor_m:.6g}` m",
            "",
            "## Summary",
            "",
            f"- Max final-field Linf: `{_format_number(_float_or_none(summary.get('max_final_field_linf')))}`",
            f"- Max probe Linf: `{_format_number(_float_or_none(summary.get('max_probe_linf')))}`",
            f"- Max cross-section Linf: `{_format_number(_float_or_none(summary.get('max_cross_section_linf')))}`",
            f"- Max zone mean eta delta: `{_format_number(_float_or_none(summary.get('max_abs_zone_mean_eta_delta_m')))}` m",
            "",
            "## Zones",
            "",
            "| Zone | Columns |",
            "| --- | --- |",
        ]
        for zone_id, columns in self.zones.items():
            lines.append(f"| `{zone_id}` | `{_column_span(columns)}` |")
        lines.extend(
            [
                "",
                "## Final Water Shape By Zone",
                "",
                "| Zone | GeoClaw h/eta/u/Fr | C++ h/eta/u/Fr | Delta h/eta/u/Fr | Wet cells |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for zone_summary in self.zone_summaries:
            lines.append(_drop_ledge_zone_summary_row(zone_summary))
        lines.extend(
            [
                "",
                "## Worst Final-Frame Field Cells",
                "",
                "| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for sample in self._worst_field_samples():
            lines.append(_shape_sample_grid_row(sample))
        lines.extend(
            [
                "",
                "## Worst Raw Probe/Cross-Section Samples",
                "",
                "| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |",
                "| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
            ]
        )
        for sample in self._worst_raw_samples():
            lines.append(_probe_cross_section_sample_row(sample))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_field_samples(self) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
        return tuple(sorted(self.field_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])

    def _worst_raw_samples(self) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
        return tuple(sorted(self.raw_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:12])


@dataclass(frozen=True, slots=True)
class Milestone18RemainingGeometryClosureCase:
    """One remaining geometry-validation family and its closure state."""

    case_id: str
    title: str
    passed: bool
    priority: int
    scenarios: tuple[str, ...]
    solver_modes: tuple[str, ...]
    failing_check_counts: dict[str, int]
    failing_scenario_count: int
    focused_evidence: tuple[dict[str, object], ...] = ()
    notes: tuple[str, ...] = ()
    next_levers: tuple[str, ...] = ()

    @property
    def promotion_ready(self) -> bool:
        return self.passed and not self.failing_check_counts

    def to_json_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "passed": self.passed,
            "promotion_ready": self.promotion_ready,
            "priority": self.priority,
            "scenarios": list(self.scenarios),
            "solver_modes": list(self.solver_modes),
            "failing_check_counts": dict(self.failing_check_counts),
            "failing_scenario_count": self.failing_scenario_count,
            "focused_evidence": list(self.focused_evidence),
            "notes": list(self.notes),
            "next_levers": list(self.next_levers),
        }


@dataclass(frozen=True, slots=True)
class Milestone18RemainingGeometryClosureReport:
    """Closure queue for remaining Milestone 18 geometry-specific blockers."""

    geometry_report: str
    focused_report_paths: tuple[str, ...]
    cases: tuple[Milestone18RemainingGeometryClosureCase, ...]

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(case.promotion_ready for case in self.cases)

    @property
    def blockers(self) -> tuple[Milestone18RemainingGeometryClosureCase, ...]:
        return tuple(case for case in self.cases if not case.promotion_ready)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "geometry_report": self.geometry_report,
            "focused_report_paths": list(self.focused_report_paths),
            "summary": {
                "case_count": len(self.cases),
                "blocker_count": len(self.blockers),
                "promotion_ready_count": sum(1 for case in self.cases if case.promotion_ready),
                "active_blockers": [case.case_id for case in self.blockers],
                "next_case": self.blockers[0].case_id if self.blockers else None,
            },
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Remaining Geometry Closure",
            "",
            f"Schema: `{MILESTONE18_REMAINING_GEOMETRY_CLOSURE_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Geometry report: `{self.geometry_report}`",
            f"Focused reports: `{', '.join(self.focused_report_paths) if self.focused_report_paths else 'none'}`",
            "",
            "## Summary",
            "",
            f"- Blocker count: `{summary['blocker_count']}`",
            f"- Promotion-ready count: `{summary['promotion_ready_count']}`",
            f"- Next case: `{summary['next_case'] or 'none'}`",
            "",
            "## Closure Queue",
            "",
            "| Priority | Case | Status | Failing checks | Focused evidence | Next lever |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
        for case in self.cases:
            evidence = ", ".join(_escape_table(str(item.get("source_report", "unknown"))) for item in case.focused_evidence)
            first_lever = case.next_levers[0] if case.next_levers else "Preserve as guardrail."
            lines.append(
                "| "
                f"{case.priority} | "
                f"`{case.case_id}` | "
                f"{'PASS' if case.promotion_ready else 'BLOCKED'} | "
                f"{_escape_table(_counter_markdown(case.failing_check_counts))} | "
                f"{evidence or 'none'} | "
                f"{_escape_table(first_lever)} |"
            )
        if self.blockers:
            lines.extend(["", "## Active Blockers", ""])
            for case in self.blockers:
                lines.append(f"### {case.title}")
                lines.append("")
                lines.append(f"- Case ID: `{case.case_id}`")
                lines.append(f"- Scenarios: `{', '.join(case.scenarios)}`")
                lines.append(f"- Failing checks: `{_counter_markdown(case.failing_check_counts)}`")
                if case.notes:
                    lines.extend(f"- {note}" for note in case.notes)
                if case.next_levers:
                    lines.append("")
                    lines.append("Next levers:")
                    lines.extend(f"- {lever}" for lever in case.next_levers)
                lines.append("")
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionLateralFaceFluxSample:
    """One upstream lateral face flux proxy comparing final GeoClaw and C++ states."""

    face_role: str
    column_index: int
    south_row_index: int
    north_row_index: int
    x_m: float
    y_face_m: float
    reference_mean_h: float
    candidate_mean_h: float
    reference_mean_v: float
    candidate_mean_v: float
    reference_lateral_volume_flux_m3ps: float
    candidate_lateral_volume_flux_m3ps: float
    flux_delta_m3ps: float
    abs_flux_delta_m3ps: float
    flux_delta_threshold_m3ps: float
    ratio_to_threshold: float
    reference_sign: int
    candidate_sign: int
    sign_matches: bool
    reference_south_h: float
    reference_south_v: float
    reference_north_h: float
    reference_north_v: float
    candidate_south_h: float
    candidate_south_v: float
    candidate_north_h: float
    candidate_north_v: float

    @property
    def passed(self) -> bool:
        return self.sign_matches and self.abs_flux_delta_m3ps <= self.flux_delta_threshold_m3ps

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionLateralFaceFluxReport:
    """Diagnostic report for upstream constriction lateral face flux proxy balance."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    wet_depth_threshold_m: float
    velocity_sign_floor_mps: float
    flux_delta_threshold_m3ps: float
    zones: dict[str, tuple[int, ...]]
    samples: tuple[Milestone18ConstrictionLateralFaceFluxSample, ...]
    edge_pair_summary: tuple[dict[str, object], ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "velocity_sign_floor_mps": self.velocity_sign_floor_mps,
            "flux_delta_threshold_m3ps": self.flux_delta_threshold_m3ps,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "summary": {
                "sample_count": len(self.samples),
                "sign_mismatch_count": sum(1 for sample in self.samples if not sample.sign_matches),
                "max_abs_flux_delta_m3ps": max(
                    (sample.abs_flux_delta_m3ps for sample in self.samples),
                    default=0.0,
                ),
                "reference_opposed_edge_column_count": sum(
                    1 for pair in self.edge_pair_summary if pair.get("reference_opposed_edges")
                ),
                "candidate_opposed_edge_column_count": sum(
                    1 for pair in self.edge_pair_summary if pair.get("candidate_opposed_edges")
                ),
                "opposition_mismatch_count": sum(
                    1 for pair in self.edge_pair_summary if not pair.get("matches_reference_opposition", True)
                ),
                "worst_samples": [sample.to_json_dict() for sample in self._worst_samples()],
            },
            "edge_pair_summary": list(self.edge_pair_summary),
            "samples": [sample.to_json_dict() for sample in self.samples],
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Constriction Lateral Face Flux Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_LATERAL_FACE_FLUX_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            f"Velocity sign floor: `{self.velocity_sign_floor_mps:.6g}` m/s",
            f"Flux delta threshold: `{self.flux_delta_threshold_m3ps:.6g}` m3/s",
            "",
            "## Summary",
            "",
            f"- Sign mismatch count: `{summary['sign_mismatch_count']}`",
            f"- Opposition mismatch count: `{summary['opposition_mismatch_count']}`",
            f"- Max abs lateral flux delta: `{_format_number(_float_or_none(summary['max_abs_flux_delta_m3ps']))}` m3/s",
            "",
            "## Worst Lateral Faces",
            "",
            "| Face | Column | Rows | x m | y-face m | GeoClaw h/v/flux | C++ h/v/flux | Delta | Threshold | Ratio | Signs |",
            "| --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
        for sample in self._worst_samples():
            lines.append(_lateral_face_flux_sample_row(sample))
        lines.extend(
            [
                "",
                "## Edge Pair Summary",
                "",
                "| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for pair in self.edge_pair_summary:
            lines.append(_lateral_face_flux_pair_row(pair))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_samples(self) -> tuple[Milestone18ConstrictionLateralFaceFluxSample, ...]:
        return tuple(
            sorted(
                self.samples,
                key=lambda sample: (not sample.sign_matches, sample.ratio_to_threshold),
                reverse=True,
            )[:12]
        )


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionFaceSourceAuditSample:
    """One reconstructed finite-volume y-face flux/source audit sample."""

    face_role: str
    column_index: int
    south_row_index: int
    north_row_index: int
    x_m: float
    y_face_m: float
    bed_step_m: float
    reference_eta_step_m: float
    candidate_eta_step_m: float
    reference_mean_h: float
    candidate_mean_h: float
    reference_mean_u: float
    candidate_mean_u: float
    reference_mean_v: float
    candidate_mean_v: float
    reference_volume_flux_m3ps: float
    candidate_volume_flux_m3ps: float
    volume_flux_delta_m3ps: float
    abs_volume_flux_delta_m3ps: float
    flux_delta_threshold_m3ps: float
    volume_ratio_to_threshold: float
    reference_volume_sign: int
    candidate_volume_sign: int
    volume_sign_matches: bool
    reference_x_momentum_flux_proxy_m3ps2: float
    candidate_x_momentum_flux_proxy_m3ps2: float
    x_momentum_flux_delta_m3ps2: float
    abs_x_momentum_flux_delta_m3ps2: float
    reference_x_momentum_sign: int
    candidate_x_momentum_sign: int
    x_momentum_sign_matches: bool
    reference_normal_momentum_flux_proxy_m3ps2: float
    candidate_normal_momentum_flux_proxy_m3ps2: float
    normal_momentum_flux_delta_m3ps2: float
    abs_normal_momentum_flux_delta_m3ps2: float
    reference_bed_source_proxy_m3ps2: float
    candidate_bed_source_proxy_m3ps2: float
    bed_source_delta_m3ps2: float
    abs_bed_source_delta_m3ps2: float
    reference_flux_source_balance_proxy_m3ps2: float
    candidate_flux_source_balance_proxy_m3ps2: float
    balance_delta_m3ps2: float
    abs_balance_delta_m3ps2: float
    balance_delta_threshold_m3ps2: float
    balance_ratio_to_threshold: float

    @property
    def passed(self) -> bool:
        return (
            self.volume_sign_matches
            and self.x_momentum_sign_matches
            and self.abs_volume_flux_delta_m3ps <= self.flux_delta_threshold_m3ps
            and self.abs_balance_delta_m3ps2 <= self.balance_delta_threshold_m3ps2
        )

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionFaceSourceAuditReport:
    """Diagnostic report for reconstructed constriction y-face flux/source balance."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    diagnostic_scope: str
    wet_depth_threshold_m: float
    velocity_sign_floor_mps: float
    flux_delta_threshold_m3ps: float
    balance_delta_threshold_m3ps2: float
    zones: dict[str, tuple[int, ...]]
    samples: tuple[Milestone18ConstrictionFaceSourceAuditSample, ...]
    edge_pair_summary: tuple[dict[str, object], ...]
    cpp_internal_audit: tuple[dict[str, object], ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "diagnostic_scope": self.diagnostic_scope,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "velocity_sign_floor_mps": self.velocity_sign_floor_mps,
            "flux_delta_threshold_m3ps": self.flux_delta_threshold_m3ps,
            "balance_delta_threshold_m3ps2": self.balance_delta_threshold_m3ps2,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "summary": {
                "sample_count": len(self.samples),
                "volume_sign_mismatch_count": sum(
                    1 for sample in self.samples if not sample.volume_sign_matches
                ),
                "x_momentum_sign_mismatch_count": sum(
                    1 for sample in self.samples if not sample.x_momentum_sign_matches
                ),
                "max_abs_volume_flux_delta_m3ps": max(
                    (sample.abs_volume_flux_delta_m3ps for sample in self.samples),
                    default=0.0,
                ),
                "max_abs_x_momentum_flux_delta_m3ps2": max(
                    (sample.abs_x_momentum_flux_delta_m3ps2 for sample in self.samples),
                    default=0.0,
                ),
                "max_abs_normal_momentum_flux_delta_m3ps2": max(
                    (sample.abs_normal_momentum_flux_delta_m3ps2 for sample in self.samples),
                    default=0.0,
                ),
                "max_abs_bed_source_delta_m3ps2": max(
                    (sample.abs_bed_source_delta_m3ps2 for sample in self.samples),
                    default=0.0,
                ),
                "max_abs_balance_delta_m3ps2": max(
                    (sample.abs_balance_delta_m3ps2 for sample in self.samples),
                    default=0.0,
                ),
                "reference_opposed_edge_column_count": sum(
                    1 for pair in self.edge_pair_summary if pair.get("reference_opposed_edges")
                ),
                "candidate_opposed_edge_column_count": sum(
                    1 for pair in self.edge_pair_summary if pair.get("candidate_opposed_edges")
                ),
                "opposition_mismatch_count": sum(
                    1 for pair in self.edge_pair_summary if not pair.get("matches_reference_opposition", True)
                ),
                "cpp_internal_audit_sample_count": len(self.cpp_internal_audit),
                "cpp_internal_source_applied_count": sum(
                    1 for sample in self.cpp_internal_audit if bool(sample.get("constriction_face_source_applied"))
                ),
                "cpp_internal_face_state_reconstruction_applied_count": sum(
                    1
                    for sample in self.cpp_internal_audit
                    if bool(sample.get("constriction_face_state_reconstruction_applied"))
                ),
                "cpp_internal_hydrostatic_face_source_enabled_count": sum(
                    1 for sample in self.cpp_internal_audit if bool(sample.get("hydrostatic_face_source_enabled"))
                ),
                "cpp_internal_constriction_source_split_applied_count": sum(
                    1
                    for sample in self.cpp_internal_audit
                    if bool(sample.get("constriction_hydrostatic_source_split_applied"))
                ),
                "cpp_internal_post_source_sign_mismatch_count": sum(
                    1 for sample in self.cpp_internal_audit if not bool(sample.get("post_left_sign_matches", True))
                ),
                "cpp_internal_max_abs_post_source_delta_m3ps": max(
                    (
                        abs(float(sample.get("post_left_flux_delta_m3ps", 0.0)))
                        for sample in self.cpp_internal_audit
                    ),
                    default=0.0,
                ),
                "worst_samples": [sample.to_json_dict() for sample in self._worst_samples()],
            },
            "edge_pair_summary": list(self.edge_pair_summary),
            "cpp_internal_audit": list(self.cpp_internal_audit),
            "samples": [sample.to_json_dict() for sample in self.samples],
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Constriction Face/Source Audit",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_FACE_SOURCE_AUDIT_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Diagnostic scope: {self.diagnostic_scope}",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            f"Velocity sign floor: `{self.velocity_sign_floor_mps:.6g}` m/s",
            f"Flux delta threshold: `{self.flux_delta_threshold_m3ps:.6g}` m3/s",
            f"Balance delta threshold: `{self.balance_delta_threshold_m3ps2:.6g}` m3/s2",
            "",
            "## Summary",
            "",
            f"- Volume sign mismatch count: `{summary['volume_sign_mismatch_count']}`",
            f"- X-momentum sign mismatch count: `{summary['x_momentum_sign_mismatch_count']}`",
            f"- Opposition mismatch count: `{summary['opposition_mismatch_count']}`",
            f"- Max abs lateral volume-flux delta: `{_format_number(_float_or_none(summary['max_abs_volume_flux_delta_m3ps']))}` m3/s",
            f"- Max abs flux/source balance delta: `{_format_number(_float_or_none(summary['max_abs_balance_delta_m3ps2']))}` m3/s2",
            f"- C++ internal audit samples: `{summary['cpp_internal_audit_sample_count']}`",
            f"- C++ internal post-source sign mismatches: `{summary['cpp_internal_post_source_sign_mismatch_count']}`",
            f"- C++ internal face-state reconstruction applications: `{summary['cpp_internal_face_state_reconstruction_applied_count']}`",
            f"- C++ internal constriction source-split applications: `{summary['cpp_internal_constriction_source_split_applied_count']}`",
            "",
            "## Worst Face/Source Samples",
            "",
            "| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |",
            "| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |",
        ]
        for sample in self._worst_samples():
            lines.append(_face_source_audit_sample_row(sample))
        if self.cpp_internal_audit:
            lines.extend(
                [
                    "",
                    "## C++ Internal Y-Face Audit",
                    "",
                    "| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |",
                    "| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |",
                ]
            )
            for sample in self.cpp_internal_audit[:12]:
                lines.append(_cpp_internal_face_audit_row(sample))
        lines.extend(
            [
                "",
                "## Edge Pair Summary",
                "",
                "| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for pair in self.edge_pair_summary:
            lines.append(_face_source_audit_pair_row(pair))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_samples(self) -> tuple[Milestone18ConstrictionFaceSourceAuditSample, ...]:
        return tuple(
            sorted(
                self.samples,
                key=lambda sample: (
                    not sample.volume_sign_matches,
                    not sample.x_momentum_sign_matches,
                    sample.volume_ratio_to_threshold,
                    sample.balance_ratio_to_threshold,
                ),
                reverse=True,
            )[:12]
        )


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionFaceStateWidthDepthReport:
    """Diagnostic report deciding between constriction face-state and width/depth fixes."""

    dual_solver_manifest: str
    scenario_package: str
    scenario_id: str
    feature: dict[str, object]
    grid: dict[str, object]
    diagnostic_scope: str
    wet_depth_threshold_m: float
    velocity_sign_floor_mps: float
    flux_delta_threshold_m3ps: float
    depth_delta_threshold_m: float
    wet_width_delta_threshold_cells: int
    bank_row_delta_threshold_cells: int
    zones: dict[str, tuple[int, ...]]
    column_profiles: tuple[dict[str, object], ...]
    face_state_samples: tuple[dict[str, object], ...]
    edge_pair_summary: tuple[dict[str, object], ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.blocked_reasons

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": "PASS" if self.passed else "BLOCKED",
            "dual_solver_manifest": self.dual_solver_manifest,
            "scenario_package": self.scenario_package,
            "scenario_id": self.scenario_id,
            "feature": self.feature,
            "grid": self.grid,
            "diagnostic_scope": self.diagnostic_scope,
            "wet_depth_threshold_m": self.wet_depth_threshold_m,
            "velocity_sign_floor_mps": self.velocity_sign_floor_mps,
            "flux_delta_threshold_m3ps": self.flux_delta_threshold_m3ps,
            "depth_delta_threshold_m": self.depth_delta_threshold_m,
            "wet_width_delta_threshold_cells": self.wet_width_delta_threshold_cells,
            "bank_row_delta_threshold_cells": self.bank_row_delta_threshold_cells,
            "zones": {zone_id: list(columns) for zone_id, columns in self.zones.items()},
            "summary": {
                "column_profile_count": len(self.column_profiles),
                "face_state_sample_count": len(self.face_state_samples),
                "face_state_blocker_count": sum(
                    1 for sample in self.face_state_samples if bool(sample.get("face_state_blocked"))
                ),
                "face_sign_mismatch_count": sum(
                    1 for sample in self.face_state_samples if not bool(sample.get("volume_sign_matches", True))
                ),
                "width_mapping_blocker_count": sum(
                    1 for profile in self.column_profiles if bool(profile.get("width_mapping_blocked"))
                ),
                "bank_alignment_blocker_count": sum(
                    1 for profile in self.column_profiles if bool(profile.get("bank_alignment_blocked"))
                ),
                "depth_mapping_blocker_count": sum(
                    1 for profile in self.column_profiles if bool(profile.get("depth_mapping_blocked"))
                ),
                "edge_opposition_mismatch_count": sum(
                    1 for pair in self.edge_pair_summary if not bool(pair.get("matches_reference_opposition", True))
                ),
                "max_abs_volume_flux_delta_m3ps": max(
                    (
                        abs(float(sample.get("volume_flux_delta_m3ps", 0.0) or 0.0))
                        for sample in self.face_state_samples
                    ),
                    default=0.0,
                ),
                "max_abs_face_mean_depth_delta_m": max(
                    (
                        abs(float(sample.get("mean_depth_delta_m", 0.0) or 0.0))
                        for sample in self.face_state_samples
                    ),
                    default=0.0,
                ),
                "max_abs_wet_width_delta_cells": max(
                    (
                        abs(int(delta))
                        for delta in (
                            _nested_value(profile, "cpp_minus_geoclaw", "wet_width_delta_cells")
                            for profile in self.column_profiles
                        )
                        if delta is not None
                    ),
                    default=0,
                ),
                "max_abs_bank_row_delta_cells": max(
                    (
                        abs(int(delta))
                        for delta in (
                            _nested_value(profile, "cpp_minus_geoclaw", "max_abs_bank_row_delta_cells")
                            for profile in self.column_profiles
                        )
                        if delta is not None
                    ),
                    default=0,
                ),
                "recommended_levers": sorted(
                    {
                        str(sample.get("recommended_solver_lever"))
                        for sample in self.face_state_samples
                        if sample.get("recommended_solver_lever")
                    }
                ),
                "worst_face_state_samples": list(self._worst_face_state_samples()),
            },
            "column_profiles": list(self.column_profiles),
            "edge_pair_summary": list(self.edge_pair_summary),
            "face_state_samples": list(self.face_state_samples),
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
        summary = self.to_json_dict()["summary"]
        lines = [
            "# Milestone 18 Constriction Face-State Width/Depth Diagnostic",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_FACE_STATE_WIDTH_DEPTH_REPORT_SCHEMA}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Dual solver manifest: `{self.dual_solver_manifest}`",
            f"Scenario package: `{self.scenario_package}`",
            f"Diagnostic scope: {self.diagnostic_scope}",
            f"Wet-depth threshold: `{self.wet_depth_threshold_m:.6g}` m",
            f"Velocity sign floor: `{self.velocity_sign_floor_mps:.6g}` m/s",
            f"Flux delta threshold: `{self.flux_delta_threshold_m3ps:.6g}` m3/s",
            f"Depth delta threshold: `{self.depth_delta_threshold_m:.6g}` m",
            f"Wet-width delta threshold: `{self.wet_width_delta_threshold_cells}` cells",
            f"Bank-row delta threshold: `{self.bank_row_delta_threshold_cells}` cells",
            "",
            "## Summary",
            "",
            f"- Face-state blockers: `{summary['face_state_blocker_count']}`",
            f"- Face sign mismatches: `{summary['face_sign_mismatch_count']}`",
            f"- Width mapping blockers: `{summary['width_mapping_blocker_count']}`",
            f"- Bank alignment blockers: `{summary['bank_alignment_blocker_count']}`",
            f"- Depth mapping blockers: `{summary['depth_mapping_blocker_count']}`",
            f"- Edge opposition mismatches: `{summary['edge_opposition_mismatch_count']}`",
            f"- Max abs volume-flux delta: `{_format_number(_float_or_none(summary['max_abs_volume_flux_delta_m3ps']))}` m3/s",
            f"- Max abs face mean-depth delta: `{_format_number(_float_or_none(summary['max_abs_face_mean_depth_delta_m']))}` m",
            f"- Max abs wet-width delta: `{summary['max_abs_wet_width_delta_cells']}` cells",
            f"- Max abs bank-row delta: `{summary['max_abs_bank_row_delta_cells']}` cells",
            f"- Recommended levers: `{summary['recommended_levers']}`",
            "",
            "## Worst Face-State Samples",
            "",
            "| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |",
            "| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
        for sample in self._worst_face_state_samples():
            lines.append(_face_state_width_depth_sample_row(sample))
        lines.extend(
            [
                "",
                "## Column Profiles",
                "",
                "| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |",
                "| ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for profile in self.column_profiles:
            lines.append(_face_state_width_depth_column_row(profile))
        lines.extend(
            [
                "",
                "## Edge Pair Summary",
                "",
                "| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for pair in self.edge_pair_summary:
            lines.append(_face_state_width_depth_pair_row(pair))
        if self.blocked_reasons:
            lines.extend(["", "## Blocked Reasons", ""])
            lines.extend(f"- {reason}" for reason in self.blocked_reasons)
        if self.next_levers:
            lines.extend(["", "## Next Levers", ""])
            lines.extend(f"- {lever}" for lever in self.next_levers)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def _worst_face_state_samples(self) -> tuple[dict[str, object], ...]:
        return tuple(
            sorted(
                self.face_state_samples,
                key=lambda sample: (
                    bool(sample.get("face_state_blocked")),
                    not bool(sample.get("volume_sign_matches", True)),
                    abs(float(sample.get("volume_flux_delta_m3ps", 0.0) or 0.0)),
                    abs(float(sample.get("mean_depth_delta_m", 0.0) or 0.0)),
                ),
                reverse=True,
            )[:12]
        )


@dataclass(frozen=True, slots=True)
class Milestone18ConstrictionHydrostaticSourceDecisionReport:
    """Decision record for the next constriction y-face source-treatment experiment."""

    face_source_audit_report: str
    scenario_id: str
    decision: str
    diagnostic_scope: str
    summary: dict[str, object]
    target_face: dict[str, object]
    rationale: tuple[str, ...]
    acceptance_constraints: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    next_levers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.decision == "PASS"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA,
            "passed": self.passed,
            "decision": self.decision,
            "face_source_audit_report": self.face_source_audit_report,
            "scenario_id": self.scenario_id,
            "diagnostic_scope": self.diagnostic_scope,
            "summary": self.summary,
            "target_face": self.target_face,
            "rationale": list(self.rationale),
            "acceptance_constraints": list(self.acceptance_constraints),
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
            "# Milestone 18 Constriction Hydrostatic Source Decision",
            "",
            f"Schema: `{MILESTONE18_CONSTRICTION_HYDROSTATIC_SOURCE_DECISION_REPORT_SCHEMA}`",
            "",
            f"Decision: **{self.decision}**",
            "",
            f"Scenario: `{self.scenario_id}`",
            f"Face/source audit: `{self.face_source_audit_report}`",
            f"Diagnostic scope: {self.diagnostic_scope}",
            "",
            "## Summary",
            "",
        ]
        for key, value in self.summary.items():
            lines.append(f"- {key}: `{_format_number(_float_or_none(value)) if isinstance(value, (int, float)) else value}`")
        lines.extend(
            [
                "",
                "## Target Face",
                "",
                "| Face | Column | Rows | Reference q | Base q | Post-source q | Post-source delta | Hydrostatic source enabled | Constriction source applied | Cell bed-source S/N |",
                "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
                _hydrostatic_source_decision_target_row(self.target_face),
            ]
        )
        if self.rationale:
            lines.extend(["", "## Rationale", ""])
            lines.extend(f"- {item}" for item in self.rationale)
        if self.acceptance_constraints:
            lines.extend(["", "## Acceptance Constraints", ""])
            lines.extend(f"- {item}" for item in self.acceptance_constraints)
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


def build_milestone18_constriction_response_timing_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
) -> Milestone18ConstrictionResponseTimingReport:
    """Compare constriction depth, mass, energy, and response timing by flow zone."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), manifest_path.parent)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    nx = int(grid["nx"])
    ny = int(grid["ny"])
    duration_s = float(scenario.get("duration", 0.0) or 0.0)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, manifest_path.parent)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, manifest_path.parent)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    geoclaw_snapshots = _constriction_zone_snapshots(
        "geoclaw",
        geoclaw_manifest,
        geoclaw_manifest_path.parent,
        grid,
        zones,
        wet_depth_threshold_m,
        default_duration_s=duration_s,
    )
    cpp_snapshots = _constriction_zone_snapshots(
        "cpp",
        cpp_manifest,
        cpp_manifest_path.parent,
        grid,
        zones,
        wet_depth_threshold_m,
        default_duration_s=duration_s,
    )
    zone_deltas = tuple(
        _constriction_zone_delta(zone_id, columns, geoclaw_snapshots, cpp_snapshots)
        for zone_id, columns in zones.items()
        if columns
    )
    thresholds = {
        "max_abs_final_mass_delta_m3": 1.0,
        "max_abs_final_mean_wet_depth_delta_m": 0.25,
        "max_abs_peak_energy_time_delta_s": 1.0,
        "max_abs_peak_energy_delta_j": 25.0,
        "max_abs_final_froude_delta": 0.5,
    }
    blocked_reasons = _constriction_response_blocked_reasons(zone_deltas, thresholds)
    next_levers = (
        "Retune constriction water volume and depth response now that wet-mask shape is closer to GeoClaw.",
        "Compare peak mass and energy timing before adding gameplay feature forcing.",
        "Add a bounded source/flux response only if it preserves Milestone 17 guardrails and does not hide conservation failures.",
    )
    return Milestone18ConstrictionResponseTimingReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        wet_depth_threshold_m=wet_depth_threshold_m,
        zones=zones,
        geoclaw_snapshots=geoclaw_snapshots,
        cpp_snapshots=cpp_snapshots,
        zone_deltas=zone_deltas,
        thresholds=thresholds,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_shape_timing_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_depth_floor_m: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    top_n: int = 12,
) -> Milestone18ConstrictionShapeTimingReport:
    """Locate the worst constriction field, slope, probe, and cross-section shape/timing errors."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    field_report_path = comparison_dir / "field_comparison.json"
    probe_report_path = comparison_dir / "probe_comparison.json"
    threshold_report_path = comparison_dir / "threshold_evaluation.json"
    field_report = _load_json_report(field_report_path)
    probe_report = _load_json_report(probe_report_path)
    threshold_report = _load_json_report(threshold_report_path)
    thresholds = _shape_timing_thresholds(threshold_report)

    field_samples: list[Milestone18ConstrictionShapeErrorSample] = []
    slope_samples: list[Milestone18ConstrictionShapeErrorSample] = []
    for frame_index, frame_record in enumerate(_records(field_report, "frame_comparisons")):
        field_samples.extend(
            _constriction_frame_worst_samples(
                frame_record,
                frame_index,
                grid,
                zones,
                category="field",
                fields=FIELD_NAMES,
                threshold=thresholds["max_field_linf"],
                velocity_depth_floor_m=velocity_depth_floor_m,
            )
        )
        slope_samples.extend(
            _constriction_frame_worst_samples(
                frame_record,
                frame_index,
                grid,
                zones,
                category="slope",
                fields=SLOPE_FIELD_NAMES,
                threshold=thresholds["max_slope_linf"],
                velocity_depth_floor_m=velocity_depth_floor_m,
            )
        )

    probe_samples = tuple(
        _shape_summary_samples(
            _records(probe_report, "point_probes"),
            category="probe",
            threshold=thresholds["max_probe_linf"],
            fields=PROBE_FIELD_NAMES,
            top_n=top_n,
        )
    )
    cross_section_samples = tuple(
        _shape_summary_samples(
            _records(probe_report, "cross_sections"),
            category="cross_section",
            threshold=thresholds["max_cross_section_linf"],
            fields=CROSS_SECTION_FIELD_NAMES,
            top_n=top_n,
        )
    )

    sorted_field_samples = tuple(
        sorted(field_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:top_n]
    )
    sorted_slope_samples = tuple(
        sorted(slope_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:top_n]
    )
    blocked_reasons = _constriction_shape_timing_blocked_reasons(
        sorted_field_samples,
        sorted_slope_samples,
        probe_samples,
        cross_section_samples,
    )
    next_levers = _constriction_shape_timing_next_levers(
        sorted_field_samples,
        sorted_slope_samples,
        probe_samples,
        cross_section_samples,
    )
    return Milestone18ConstrictionShapeTimingReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_depth_floor_m=velocity_depth_floor_m,
        zones=zones,
        thresholds=thresholds,
        field_samples=sorted_field_samples,
        slope_samples=sorted_slope_samples,
        probe_samples=probe_samples,
        cross_section_samples=cross_section_samples,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_probe_cross_section_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_depth_floor_m: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    top_n: int = 12,
) -> Milestone18ConstrictionProbeCrossSectionReport:
    """Locate the exact raw point-probe and cross-section samples blocking constriction parity."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    threshold_report = _load_json_report(comparison_dir / "threshold_evaluation.json")
    thresholds = _shape_timing_thresholds(threshold_report)

    geoclaw_record = manifest.get("geoclaw", {})
    cpp_record = manifest.get("cpp", {})
    if not isinstance(geoclaw_record, dict) or not isinstance(cpp_record, dict):
        raise ValueError("dual solver manifest must include geoclaw and cpp records.")
    geoclaw_manifest_path = _resolve_path(str(geoclaw_record.get("manifest", "")), comparison_dir)
    cpp_manifest_path = _resolve_path(str(cpp_record.get("manifest", "")), comparison_dir)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)
    geoclaw_root = geoclaw_manifest_path.parent
    cpp_root = cpp_manifest_path.parent

    probe_metadata = _sample_metadata_by_id(geoclaw_manifest, "probe_manifest")
    cross_section_metadata = _sample_metadata_by_id(geoclaw_manifest, "cross_section_manifest")
    probe_samples = _raw_probe_worst_samples(
        geoclaw_root,
        _string_list(geoclaw_manifest.get("probes")),
        cpp_root,
        _string_list(cpp_manifest.get("probes")),
        probe_metadata,
        grid,
        zones,
        threshold=thresholds["max_probe_linf"],
        velocity_depth_floor_m=velocity_depth_floor_m,
        top_n=top_n,
    )
    cross_section_samples = _raw_cross_section_worst_samples(
        geoclaw_root,
        _string_list(geoclaw_manifest.get("cross_sections")),
        cpp_root,
        _string_list(cpp_manifest.get("cross_sections")),
        cross_section_metadata,
        grid,
        zones,
        threshold=thresholds["max_cross_section_linf"],
        velocity_depth_floor_m=velocity_depth_floor_m,
        top_n=top_n,
    )
    blocked_reasons = _probe_cross_section_blocked_reasons(probe_samples, cross_section_samples)
    next_levers = _probe_cross_section_next_levers(probe_samples, cross_section_samples)
    return Milestone18ConstrictionProbeCrossSectionReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        velocity_depth_floor_m=velocity_depth_floor_m,
        zones=zones,
        thresholds=thresholds,
        probe_samples=probe_samples,
        cross_section_samples=cross_section_samples,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_lateral_face_flux_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_sign_floor_mps: float = 0.05,
    flux_delta_threshold_m3ps: float = 0.25,
    top_n: int = 16,
) -> Milestone18ConstrictionLateralFaceFluxReport:
    """Compare final-frame upstream lateral face flux proxies for the constriction blocker."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    ny = int(grid["ny"])
    nx = int(grid["nx"])

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, comparison_dir)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, comparison_dir)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_manifest_path.parent)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_manifest_path.parent)
    geoclaw_state = _load_water_frame_fields(geoclaw_frame_path, ny, nx)
    cpp_state = _load_water_frame_fields(cpp_frame_path, ny, nx)

    samples = _constriction_upstream_lateral_face_samples(
        initial_state,
        geoclaw_state,
        cpp_state,
        grid,
        zones,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
    )
    edge_pair_summary = _constriction_lateral_face_edge_pair_summary(samples)
    sorted_samples = tuple(
        sorted(
            samples,
            key=lambda sample: (not sample.sign_matches, sample.ratio_to_threshold),
            reverse=True,
        )[:top_n]
    )
    blocked_reasons = _lateral_face_flux_blocked_reasons(sorted_samples, edge_pair_summary)
    next_levers = _lateral_face_flux_next_levers(sorted_samples, edge_pair_summary)
    return Milestone18ConstrictionLateralFaceFluxReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        zones=zones,
        samples=sorted_samples,
        edge_pair_summary=edge_pair_summary,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_face_source_audit_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_sign_floor_mps: float = 0.05,
    flux_delta_threshold_m3ps: float = 0.25,
    balance_delta_threshold_m3ps2: float = 0.75,
    top_n: int = 16,
) -> Milestone18ConstrictionFaceSourceAuditReport:
    """Reconstruct upstream y-face flux/source balance for the constriction blocker."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    ny = int(grid["ny"])
    nx = int(grid["nx"])

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    bed = _load_scenario_bed_array(scenario_package, scenario, initial_state["h"])
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, comparison_dir)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, comparison_dir)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_manifest_path.parent)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_manifest_path.parent)
    geoclaw_state = _load_water_frame_fields(geoclaw_frame_path, ny, nx)
    cpp_state = _load_water_frame_fields(cpp_frame_path, ny, nx)
    cpp_internal_audit = _load_cpp_constriction_y_face_audit(
        cpp_manifest,
        cpp_manifest_path.parent,
        geoclaw_state,
        grid,
        velocity_sign_floor_mps,
    )

    samples = _constriction_upstream_face_source_audit_samples(
        initial_state,
        geoclaw_state,
        cpp_state,
        bed,
        grid,
        zones,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        balance_delta_threshold_m3ps2=balance_delta_threshold_m3ps2,
    )
    edge_pair_summary = _constriction_face_source_edge_pair_summary(samples)
    sorted_samples = tuple(
        sorted(
            samples,
            key=lambda sample: (
                not sample.volume_sign_matches,
                not sample.x_momentum_sign_matches,
                sample.volume_ratio_to_threshold,
                sample.balance_ratio_to_threshold,
            ),
            reverse=True,
        )[:top_n]
    )
    blocked_reasons = _face_source_audit_blocked_reasons(sorted_samples, edge_pair_summary, cpp_internal_audit)
    next_levers = _face_source_audit_next_levers(sorted_samples, edge_pair_summary, cpp_internal_audit)
    return Milestone18ConstrictionFaceSourceAuditReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        diagnostic_scope=(
            "Finite-volume y-face flux/source reconstruction from exported final frames; "
            "this is not internal per-timestep Riemann telemetry."
        ),
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        balance_delta_threshold_m3ps2=balance_delta_threshold_m3ps2,
        zones=zones,
        samples=sorted_samples,
        edge_pair_summary=edge_pair_summary,
        cpp_internal_audit=cpp_internal_audit,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_face_state_width_depth_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_sign_floor_mps: float = 0.05,
    flux_delta_threshold_m3ps: float = 0.25,
    depth_delta_threshold_m: float = 0.25,
    wet_width_delta_threshold_cells: int = 1,
    bank_row_delta_threshold_cells: int = 1,
) -> Milestone18ConstrictionFaceStateWidthDepthReport:
    """Decide whether the constriction blocker is face-state reconstruction, width/depth mapping, or both."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    constriction = _constriction_feature(features)
    grid = _scenario_grid(scenario)
    ny = int(grid["ny"])
    nx = int(grid["nx"])

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _constriction_response_zones(initial_state, grid, constriction, wet_depth_threshold_m)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, comparison_dir)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, comparison_dir)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_manifest_path.parent)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_manifest_path.parent)
    geoclaw_state = _load_water_frame_fields(geoclaw_frame_path, ny, nx)
    cpp_state = _load_water_frame_fields(cpp_frame_path, ny, nx)

    column_profiles = _constriction_face_state_width_depth_column_profiles(
        initial_state,
        geoclaw_state,
        cpp_state,
        grid,
        zones,
        wet_depth_threshold_m=wet_depth_threshold_m,
        depth_delta_threshold_m=depth_delta_threshold_m,
        wet_width_delta_threshold_cells=wet_width_delta_threshold_cells,
        bank_row_delta_threshold_cells=bank_row_delta_threshold_cells,
    )
    lateral_samples = _constriction_upstream_lateral_face_samples(
        initial_state,
        geoclaw_state,
        cpp_state,
        grid,
        zones,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
    )
    face_state_samples = _constriction_face_state_width_depth_samples(
        lateral_samples,
        column_profiles,
        depth_delta_threshold_m=depth_delta_threshold_m,
    )
    edge_pair_summary = _constriction_face_state_width_depth_edge_pair_summary(face_state_samples)
    blocked_reasons = _face_state_width_depth_blocked_reasons(
        column_profiles,
        face_state_samples,
        edge_pair_summary,
    )
    next_levers = _face_state_width_depth_next_levers(
        column_profiles,
        face_state_samples,
        edge_pair_summary,
    )
    return Milestone18ConstrictionFaceStateWidthDepthReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        feature=constriction,
        grid=grid,
        diagnostic_scope=(
            "Compares authored, GeoClaw final, and C++ final wet-band columns while checking "
            "GeoClaw/C++ upstream edge face states before the next constriction solver change."
        ),
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_sign_floor_mps=velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        depth_delta_threshold_m=depth_delta_threshold_m,
        wet_width_delta_threshold_cells=wet_width_delta_threshold_cells,
        bank_row_delta_threshold_cells=bank_row_delta_threshold_cells,
        zones=zones,
        column_profiles=column_profiles,
        face_state_samples=face_state_samples,
        edge_pair_summary=edge_pair_summary,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_drop_ledge_hydraulic_control_report(
    dual_solver_manifest: str | Path,
    *,
    wet_depth_threshold_m: float = 0.15,
    velocity_depth_floor_m: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    top_n: int = 12,
) -> Milestone18DropLedgeHydraulicControlReport:
    """Locate drop/ledge hydraulic-control and tailwater water-shape blockers."""

    manifest_path = Path(dual_solver_manifest)
    manifest = _load_json_report(manifest_path)
    comparison_dir = manifest_path.parent
    scenario_package = _resolve_path(str(manifest.get("scenario_package", "")), comparison_dir)
    scenario = _load_json_report(scenario_package / "scenario.json")
    features = _load_json_report(scenario_package / "features.json")
    ledge = _drop_ledge_feature(features)
    downstream = _feature_by_kind(features, "wave_train")
    grid = _scenario_grid(scenario)

    initial_state_path = _scenario_array_path(scenario_package, scenario, "initial_state", "initial_state.npz")
    initial_state = _load_npz_water_state(initial_state_path, h_key="depth")
    zones = _drop_ledge_response_zones(initial_state, grid, ledge, downstream)

    threshold_report = _load_json_report(comparison_dir / "threshold_evaluation.json")
    thresholds = _shape_timing_thresholds(threshold_report)

    geoclaw_manifest_ref = _manifest_nested_string(manifest, "geoclaw", "manifest")
    cpp_manifest_ref = _manifest_nested_string(manifest, "cpp", "manifest")
    geoclaw_manifest_path = _resolve_path(geoclaw_manifest_ref, comparison_dir)
    cpp_manifest_path = _resolve_path(cpp_manifest_ref, comparison_dir)
    geoclaw_manifest = _load_json_report(geoclaw_manifest_path)
    cpp_manifest = _load_json_report(cpp_manifest_path)
    geoclaw_root = geoclaw_manifest_path.parent
    cpp_root = cpp_manifest_path.parent
    geoclaw_frame_path = _final_frame_path(geoclaw_manifest, geoclaw_root)
    cpp_frame_path = _final_frame_path(cpp_manifest, cpp_root)
    ny = int(grid["ny"])
    nx = int(grid["nx"])
    geoclaw_state = _load_water_frame_fields(geoclaw_frame_path, ny, nx)
    cpp_state = _load_water_frame_fields(cpp_frame_path, ny, nx)

    field_samples = tuple(
        sorted(
            _constriction_frame_worst_samples(
                {
                    "label": "final",
                    "reference_frame": str(geoclaw_frame_path),
                    "cpp_frame": str(cpp_frame_path),
                },
                0,
                grid,
                zones,
                category="field",
                fields=FIELD_NAMES,
                threshold=thresholds["max_field_linf"],
                velocity_depth_floor_m=velocity_depth_floor_m,
            ),
            key=lambda sample: sample.ratio_to_threshold,
            reverse=True,
        )[:top_n]
    )
    probe_metadata = _sample_metadata_by_id(geoclaw_manifest, "probe_manifest")
    cross_section_metadata = _sample_metadata_by_id(geoclaw_manifest, "cross_section_manifest")
    probe_samples = _raw_probe_worst_samples(
        geoclaw_root,
        _string_list(geoclaw_manifest.get("probes")),
        cpp_root,
        _string_list(cpp_manifest.get("probes")),
        probe_metadata,
        grid,
        zones,
        threshold=thresholds["max_probe_linf"],
        velocity_depth_floor_m=velocity_depth_floor_m,
        top_n=top_n,
    )
    cross_section_samples = _raw_cross_section_worst_samples(
        geoclaw_root,
        _string_list(geoclaw_manifest.get("cross_sections")),
        cpp_root,
        _string_list(cpp_manifest.get("cross_sections")),
        cross_section_metadata,
        grid,
        zones,
        threshold=thresholds["max_cross_section_linf"],
        velocity_depth_floor_m=velocity_depth_floor_m,
        top_n=top_n,
    )
    zone_summaries = _drop_ledge_zone_summaries(geoclaw_state, cpp_state, zones, wet_depth_threshold_m)
    blocked_reasons = _drop_ledge_hydraulic_control_blocked_reasons(
        field_samples,
        probe_samples,
        cross_section_samples,
    )
    next_levers = _drop_ledge_hydraulic_control_next_levers(
        field_samples,
        probe_samples,
        cross_section_samples,
        threshold_report,
    )
    return Milestone18DropLedgeHydraulicControlReport(
        dual_solver_manifest=str(manifest_path),
        scenario_package=str(scenario_package),
        scenario_id=str(manifest.get("scenario_id") or scenario.get("metadata", {}).get("scenario_id") or "unknown"),
        ledge_feature=ledge,
        downstream_feature=downstream,
        grid=grid,
        wet_depth_threshold_m=wet_depth_threshold_m,
        velocity_depth_floor_m=velocity_depth_floor_m,
        zones=zones,
        thresholds=thresholds,
        zone_summaries=zone_summaries,
        field_samples=field_samples,
        probe_samples=probe_samples,
        cross_section_samples=cross_section_samples,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_constriction_hydrostatic_source_decision_report(
    face_source_audit_report: str | Path,
) -> Milestone18ConstrictionHydrostaticSourceDecisionReport:
    """Record the next constriction y-face source-treatment decision from the native audit."""

    report_path = Path(face_source_audit_report)
    payload = _load_json_report(report_path)
    summary_payload = payload.get("summary", {})
    summary = summary_payload if isinstance(summary_payload, dict) else {}
    internal_samples = _records(payload, "cpp_internal_audit")
    target_face = _hydrostatic_source_decision_target_face(payload)

    internal_count = int(summary.get("cpp_internal_audit_sample_count", len(internal_samples)) or 0)
    post_source_mismatch_count = int(summary.get("cpp_internal_post_source_sign_mismatch_count", 0) or 0)
    hydrostatic_enabled_count = int(summary.get("cpp_internal_hydrostatic_face_source_enabled_count", 0) or 0)
    source_split_count = int(summary.get("cpp_internal_constriction_source_split_applied_count", 0) or 0)
    constriction_source_count = int(summary.get("cpp_internal_source_applied_count", 0) or 0)
    max_delta = _float_or_none(summary.get("cpp_internal_max_abs_post_source_delta_m3ps"))
    target_delta = _float_or_none(target_face.get("post_left_flux_delta_m3ps"))

    decision = "TEST_REQUIRED"
    if internal_count == 0:
        decision = "AUDIT_REQUIRED"
    elif post_source_mismatch_count == 0 and hydrostatic_enabled_count > 0:
        decision = "PASS"
    elif hydrostatic_enabled_count > 0:
        decision = "REVISE_OR_REJECT"

    rationale = (
        (
            f"The C++ internal audit has {post_source_mismatch_count} post-source sign mismatches "
            f"across {internal_count} constriction y-face samples."
        ),
        (
            f"Hydrostatic y-face source terms are enabled on {hydrostatic_enabled_count} of "
            f"{internal_count} audited samples, while constriction face sources are applied on "
            f"{constriction_source_count} samples and constriction source splitting is applied on "
            f"{source_split_count} samples."
        ),
        (
            "The selected target remains wrong after current source handling: "
            f"`{target_face.get('face_role', 'unknown')}` column {target_face.get('column_index', 'unknown')} "
            f"rows {target_face.get('south_row_index', 'unknown')}-{target_face.get('north_row_index', 'unknown')} "
            f"has post-source q delta {_format_number(target_delta)} m3/s."
        ),
    )
    acceptance_constraints = (
        "Keep feature/gameplay forcing disabled for this fixture; this is a finite-volume water-solver treatment test.",
        "Manifest-record the y-face source-split parameters, target face set, conservation deltas, and feature-forcing scale.",
        "Compare against the corrected GeoClaw `user`-boundary constriction reference and rerun the face/source audit.",
        "Preserve or improve visible mass, energy, Froude, wet-mask, field, slope, probe, and cross-section checks.",
        "Run Milestone 17 analytic guardrails before and after the solver attempt; reject the change if guardrails regress.",
    )
    blocked_reasons = tuple(
        reason
        for reason in (
            "No native C++ y-face audit exists yet." if internal_count == 0 else "",
            (
                "Native C++ constriction y-face flux signs still disagree with GeoClaw after current source handling."
                if post_source_mismatch_count > 0
                else ""
            ),
            (
                "Hydrostatic y-face source treatment is absent for the audited constriction faces."
                if internal_count > 0 and hydrostatic_enabled_count == 0
                else ""
            ),
            (
                "A constriction y-face source split is present, but post-source face signs still disagree with GeoClaw."
                if source_split_count > 0 and post_source_mismatch_count > 0
                else ""
            ),
            (
                "The next change must not be promoted until full geometry checks pass or improve without hiding conservation failures."
                if decision != "PASS"
                else ""
            ),
        )
        if reason
    )
    if source_split_count > 0:
        next_levers = (
            (
                "Do not promote the current constriction y-face source split by itself; it is manifest-recorded and "
                f"audited on {source_split_count} faces but still leaves "
                f"{post_source_mismatch_count} post-source sign mismatches."
            ),
            "Move the next constriction attempt to geometry-aware face-state reconstruction or width/depth mapping instead of increasing source-split strength.",
            "Keep the split bounded and feature forcing off unless a future geometry/state reconstruction report proves it helps without regressing conservation, Froude, or sampled fields.",
        )
    else:
        next_levers = (
            (
                "Implement a fixture-scoped constriction y-face hydrostatic/source-splitting experiment at the audited "
                f"`{target_face.get('face_role', 'unknown')}` column {target_face.get('column_index', 'unknown')} "
                f"rows {target_face.get('south_row_index', 'unknown')}-{target_face.get('north_row_index', 'unknown')} target first."
            ),
            "Apply the treatment inside the finite-volume face/source update, not as final velocity/depth transport or gameplay forcing.",
            "Promote only if the face/source report, throat/shape/timing diagnostics, Milestone 17 guardrail, and threshold report all support the change.",
            "If the split worsens field, slope, wet-mask, probe, cross-section, Froude, mass, or energy checks, reject it and move to geometry width/depth mapping.",
        )
    report_summary = {
        "source_audit_decision": str(payload.get("decision", "UNKNOWN")),
        "cpp_internal_audit_sample_count": internal_count,
        "cpp_internal_post_source_sign_mismatch_count": post_source_mismatch_count,
        "cpp_internal_hydrostatic_face_source_enabled_count": hydrostatic_enabled_count,
        "cpp_internal_constriction_source_split_applied_count": source_split_count,
        "cpp_internal_source_applied_count": constriction_source_count,
        "cpp_internal_max_abs_post_source_delta_m3ps": max_delta,
        "target_post_source_delta_m3ps": target_delta,
    }
    return Milestone18ConstrictionHydrostaticSourceDecisionReport(
        face_source_audit_report=str(report_path),
        scenario_id=str(payload.get("scenario_id", "unknown")),
        decision=decision,
        diagnostic_scope=(
            "Decision artifact derived from the exported C++ internal constriction y-face audit; "
            "it does not change solver behavior by itself."
        ),
        summary=report_summary,
        target_face=target_face,
        rationale=rationale,
        acceptance_constraints=acceptance_constraints,
        blocked_reasons=blocked_reasons,
        next_levers=next_levers,
    )


def build_milestone18_remaining_geometry_closure_report(
    geometry_report: str | Path,
    *,
    focused_reports: tuple[str | Path, ...] = (),
) -> Milestone18RemainingGeometryClosureReport:
    """Build the ordered Milestone 18 queue for remaining geometry-specific blockers."""

    geometry_path = Path(geometry_report)
    geometry = _load_json_report(geometry_path)
    focused_by_case = _focused_geometry_evidence_by_case(focused_reports)
    cases: list[Milestone18RemainingGeometryClosureCase] = []
    for case_payload in _records(geometry, "cases"):
        case_id = str(case_payload.get("case_id", "unknown_geometry_case"))
        evidence_records = _records(case_payload, "evidence")
        failing_counts = _geometry_failing_check_counts(evidence_records)
        focused = focused_by_case.get(case_id, ())
        passed = bool(case_payload.get("passed")) and not failing_counts
        notes = tuple(str(note) for note in case_payload.get("notes", []) if isinstance(note, str))
        cases.append(
            Milestone18RemainingGeometryClosureCase(
                case_id=case_id,
                title=str(case_payload.get("title", case_id)),
                passed=passed,
                priority=_remaining_geometry_priority(case_id),
                scenarios=tuple(str(item) for item in case_payload.get("scenarios", []) if isinstance(item, str)),
                solver_modes=tuple(str(item) for item in case_payload.get("solver_modes", []) if isinstance(item, str)),
                failing_check_counts=failing_counts,
                failing_scenario_count=_geometry_failing_scenario_count(evidence_records),
                focused_evidence=focused,
                notes=_remaining_geometry_notes(case_id, notes, evidence_records),
                next_levers=_remaining_geometry_next_levers(case_id, focused, failing_counts, evidence_records),
            )
        )
    sorted_cases = tuple(sorted(cases, key=lambda case: (case.promotion_ready, case.priority, case.case_id)))
    return Milestone18RemainingGeometryClosureReport(
        geometry_report=str(geometry_path),
        focused_report_paths=tuple(str(Path(path)) for path in focused_reports),
        cases=sorted_cases,
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


def _feature_by_kind(features_payload: dict[str, Any], kind: str) -> dict[str, object] | None:
    features = features_payload.get("features", [])
    if not isinstance(features, list):
        raise ValueError("features must be a list.")
    for feature in features:
        if not isinstance(feature, dict) or feature.get("kind") != kind:
            continue
        center = feature.get("center", {})
        if not isinstance(center, dict):
            center = {}
        return {
            "kind": kind,
            "center_x": float(center.get("x", 0.0)),
            "center_y": float(center.get("y", 0.0)),
            "width_m": _float_or_none(feature.get("width")),
            "length_m": _float_or_none(feature.get("length")),
            "radius_m": _float_or_none(feature.get("radius")),
            "strength": _float_or_none(feature.get("strength")),
            "angle_rad": _float_or_none(feature.get("angle")),
            "metadata": feature.get("metadata", {}),
        }
    return None


def _drop_ledge_feature(features_payload: dict[str, Any]) -> dict[str, object]:
    feature = _feature_by_kind(features_payload, "ledge")
    if feature is None:
        raise ValueError("features.json does not contain a ledge feature.")
    return feature


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


def _load_scenario_bed_array(
    scenario_package: Path,
    scenario: dict[str, Any],
    fallback_shape: np.ndarray,
) -> np.ndarray:
    bed_path = _scenario_array_path(scenario_package, scenario, "bed", "bed.npy")
    if bed_path.exists():
        return np.asarray(np.load(bed_path), dtype=float)
    return np.zeros_like(fallback_shape, dtype=float)


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


def _slopes_from_eta(eta: np.ndarray, dx: float, dy: float) -> tuple[np.ndarray, np.ndarray]:
    slope_y, slope_x = np.gradient(np.asarray(eta, dtype=float), dy, dx)
    return slope_x, slope_y


def _frame_paths(manifest: dict[str, Any], manifest_dir: Path) -> tuple[Path, ...]:
    frames = manifest.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ValueError("solver manifest must include at least one frame.")
    paths: list[Path] = []
    for frame in frames:
        if not isinstance(frame, str):
            raise ValueError("solver manifest frame entries must be strings.")
        paths.append(_resolve_path(frame, manifest_dir))
    return tuple(paths)


def _water_frame_time(path: Path, fallback_time_s: float) -> float:
    if path.suffix == ".npz":
        with np.load(path) as data:
            if "time" in data:
                time_value = np.asarray(data["time"], dtype=float)
                if time_value.size:
                    return float(time_value.reshape(-1)[0])
    return float(fallback_time_s)


def _load_water_frame(path: Path, ny: int, nx: int) -> dict[str, np.ndarray]:
    if path.suffix == ".npz":
        return _load_npz_water_state(path, h_key="h")
    return _load_cpp_water_csv(path, ny, nx)


def _load_water_frame_fields(path: Path, ny: int, nx: int) -> dict[str, np.ndarray]:
    if path.suffix == ".npz":
        with np.load(path) as data:
            h_key = "h" if "h" in data else "depth"
            h = np.asarray(data[h_key], dtype=float)
            fields: dict[str, np.ndarray] = {
                "h": h,
                "eta": np.asarray(data["eta"], dtype=float) if "eta" in data else h.copy(),
                "u": np.asarray(data["u"], dtype=float) if "u" in data else np.zeros_like(h),
                "v": np.asarray(data["v"], dtype=float) if "v" in data else np.zeros_like(h),
                "hu": np.asarray(data["hu"], dtype=float) if "hu" in data else np.zeros_like(h),
                "hv": np.asarray(data["hv"], dtype=float) if "hv" in data else np.zeros_like(h),
                "normal_x": np.asarray(data["normal_x"], dtype=float) if "normal_x" in data else np.zeros_like(h),
                "normal_y": np.asarray(data["normal_y"], dtype=float) if "normal_y" in data else np.zeros_like(h),
                "normal_z": np.asarray(data["normal_z"], dtype=float) if "normal_z" in data else np.ones_like(h),
                "froude": np.asarray(data["froude"], dtype=float) if "froude" in data else np.zeros_like(h),
                "wet": np.asarray(data["wet"], dtype=bool) if "wet" in data else h > 0.0,
            }
            return fields

    arrays: dict[str, np.ndarray] = {
        "h": np.zeros((ny, nx), dtype=float),
        "eta": np.zeros((ny, nx), dtype=float),
        "u": np.zeros((ny, nx), dtype=float),
        "v": np.zeros((ny, nx), dtype=float),
        "hu": np.zeros((ny, nx), dtype=float),
        "hv": np.zeros((ny, nx), dtype=float),
        "normal_x": np.zeros((ny, nx), dtype=float),
        "normal_y": np.zeros((ny, nx), dtype=float),
        "normal_z": np.ones((ny, nx), dtype=float),
        "froude": np.zeros((ny, nx), dtype=float),
        "wet": np.zeros((ny, nx), dtype=bool),
    }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_index = int(row["row"])
            column_index = int(row["col"])
            for field in FIELD_NAMES + ("froude",):
                arrays[field][row_index, column_index] = float(row.get(field, 0.0))
            arrays["wet"][row_index, column_index] = row.get("wet", "0") in {"1", "true", "True"}
    return arrays


def _shape_timing_thresholds(threshold_report: dict[str, Any]) -> dict[str, float]:
    thresholds = threshold_report.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}
    return {
        "max_field_linf": float(thresholds.get("max_field_linf", 0.25)),
        "max_slope_linf": float(thresholds.get("max_slope_linf", 0.25)),
        "max_probe_linf": float(thresholds.get("max_probe_linf", 0.25)),
        "max_cross_section_linf": float(thresholds.get("max_cross_section_linf", 0.25)),
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _sample_metadata_by_id(manifest: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    records = manifest.get(key, [])
    if not isinstance(records, list):
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        sample_id = record.get("probe_id")
        if isinstance(sample_id, str):
            by_id[sample_id] = record
    return by_id


def _matched_sample_files(
    reference_root: Path,
    reference_files: list[str],
    candidate_root: Path,
    candidate_files: list[str],
) -> tuple[tuple[str, Path, Path], ...]:
    candidate_by_id = {Path(path).stem: candidate_root / path for path in candidate_files}
    matched: list[tuple[str, Path, Path]] = []
    for path in reference_files:
        sample_id = Path(path).stem
        candidate_path = candidate_by_id.get(sample_id)
        if candidate_path is not None:
            matched.append((sample_id, reference_root / path, candidate_path))
    return tuple(matched)


def _load_milestone18_probe_csv(path: Path) -> dict[str, np.ndarray]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows.extend(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Probe CSV is empty: {path}")
    return {
        column: np.asarray([float(row[column]) for row in rows], dtype=float)
        for column in rows[0].keys()
    }


def _load_milestone18_reference_cross_section(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {
            "times": np.asarray(data["times"], dtype=float),
            "distance": np.asarray(data["distance"], dtype=float),
            "h": np.asarray(data["h"], dtype=float),
            "eta": np.asarray(data["eta"], dtype=float),
            "u": np.asarray(data["u"], dtype=float),
            "v": np.asarray(data["v"], dtype=float),
            "froude": np.asarray(data["froude"], dtype=float),
        }


def _load_milestone18_cpp_cross_section(path: Path) -> dict[str, np.ndarray]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows.extend(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Cross-section CSV is empty: {path}")
    times = np.asarray(sorted({float(row["time"]) for row in rows}), dtype=float)
    distances = np.asarray(sorted({float(row["distance"]) for row in rows}), dtype=float)
    time_index = {value: index for index, value in enumerate(times)}
    distance_index = {value: index for index, value in enumerate(distances)}
    result: dict[str, np.ndarray] = {
        "times": times,
        "distance": distances,
    }
    for field in CROSS_SECTION_FIELD_NAMES:
        result[field] = np.zeros((len(times), len(distances)), dtype=float)
    for row in rows:
        time_slot = time_index[float(row["time"])]
        distance_slot = distance_index[float(row["distance"])]
        for field in CROSS_SECTION_FIELD_NAMES:
            result[field][time_slot, distance_slot] = float(row[field])
    return result


def _nearest_sample_indices(reference: np.ndarray, candidate: np.ndarray) -> tuple[np.ndarray, float]:
    if reference.size == 0 or candidate.size == 0:
        raise ValueError("Cannot align empty sample arrays.")
    indices = np.zeros(reference.shape, dtype=np.int64)
    max_delta = 0.0
    for index, value in np.ndenumerate(reference):
        nearest = int(np.argmin(np.abs(candidate - value)))
        indices[index] = nearest
        max_delta = max(max_delta, abs(float(candidate[nearest]) - float(value)))
    return indices, max_delta


def _series_velocity_mask(
    reference_h: np.ndarray,
    candidate_h: np.ndarray,
    velocity_depth_floor_m: float,
) -> np.ndarray:
    return (np.asarray(reference_h, dtype=float) >= velocity_depth_floor_m) & (
        np.asarray(candidate_h, dtype=float) >= velocity_depth_floor_m
    )


def _metadata_position(metadata_by_id: dict[str, dict[str, Any]], sample_id: str) -> tuple[float | None, float | None]:
    metadata = metadata_by_id.get(sample_id, {}).get("metadata", {})
    if not isinstance(metadata, dict):
        return None, None
    position = metadata.get("position")
    if isinstance(position, list) and len(position) >= 2:
        return float(position[0]), float(position[1])
    return None, None


def _metadata_normal(metadata_by_id: dict[str, dict[str, Any]], sample_id: str) -> tuple[float, float]:
    metadata = metadata_by_id.get(sample_id, {}).get("metadata", {})
    if not isinstance(metadata, dict):
        return 0.0, 1.0
    normal = metadata.get("normal")
    if isinstance(normal, list) and len(normal) >= 2:
        return float(normal[0]), float(normal[1])
    return 0.0, 1.0


def _zone_for_column(zones: dict[str, tuple[int, ...]], column_index: int | None) -> str | None:
    if column_index is None:
        return None
    for zone_id, columns in zones.items():
        if column_index in columns:
            return zone_id
    return None


def _raw_probe_worst_samples(
    reference_root: Path,
    reference_files: list[str],
    candidate_root: Path,
    candidate_files: list[str],
    metadata_by_id: dict[str, dict[str, Any]],
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    threshold: float,
    velocity_depth_floor_m: float,
    top_n: int,
) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
    samples: list[Milestone18ConstrictionProbeCrossSectionSample] = []
    for sample_id, reference_path, cpp_path in _matched_sample_files(
        reference_root,
        reference_files,
        candidate_root,
        candidate_files,
    ):
        reference = _load_milestone18_probe_csv(reference_path)
        candidate = _load_milestone18_probe_csv(cpp_path)
        time_indices, _ = _nearest_sample_indices(reference["time"], candidate["time"])
        aligned_candidate = {
            field: candidate[field][time_indices]
            for field in candidate
            if field != "time" and field in reference
        }
        x_m, y_m = _metadata_position(metadata_by_id, sample_id)
        row_index = _grid_row(y_m, grid) if y_m is not None else None
        column_index = _grid_column(x_m, grid) if x_m is not None else None
        zone_id = _zone_for_column(zones, column_index)
        for field in PROBE_FIELD_NAMES:
            if field not in reference or field not in aligned_candidate:
                continue
            mask = (
                _series_velocity_mask(reference["h"], aligned_candidate["h"], velocity_depth_floor_m)
                if field in VELOCITY_LIKE_FIELD_NAMES
                else np.ones(reference[field].shape, dtype=bool)
            )
            sample = _raw_series_worst_sample(
                "probe",
                sample_id,
                field,
                reference[field],
                aligned_candidate[field],
                mask,
                threshold,
                reference,
                aligned_candidate,
                time_s=reference["time"],
                distance_m=None,
                x_m=x_m,
                y_m=y_m,
                row_index=row_index,
                column_index=column_index,
                zone_id=zone_id,
                reference_path=reference_path,
                cpp_path=cpp_path,
            )
            if sample is not None:
                samples.append(sample)
    return tuple(sorted(samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:top_n])


def _raw_cross_section_worst_samples(
    reference_root: Path,
    reference_files: list[str],
    candidate_root: Path,
    candidate_files: list[str],
    metadata_by_id: dict[str, dict[str, Any]],
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    threshold: float,
    velocity_depth_floor_m: float,
    top_n: int,
) -> tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]:
    samples: list[Milestone18ConstrictionProbeCrossSectionSample] = []
    for sample_id, reference_path, cpp_path in _matched_sample_files(
        reference_root,
        reference_files,
        candidate_root,
        candidate_files,
    ):
        reference = _load_milestone18_reference_cross_section(reference_path)
        candidate = _load_milestone18_cpp_cross_section(cpp_path)
        time_indices, _ = _nearest_sample_indices(reference["times"], candidate["times"])
        distance_indices, _ = _nearest_sample_indices(reference["distance"], candidate["distance"])
        aligned_candidate = {
            field: candidate[field][np.ix_(time_indices, distance_indices)]
            for field in CROSS_SECTION_FIELD_NAMES
        }
        origin_x, origin_y = _metadata_position(metadata_by_id, sample_id)
        normal_x, normal_y = _metadata_normal(metadata_by_id, sample_id)
        for field in CROSS_SECTION_FIELD_NAMES:
            mask = (
                _series_velocity_mask(reference["h"], aligned_candidate["h"], velocity_depth_floor_m)
                if field in VELOCITY_LIKE_FIELD_NAMES
                else np.ones(reference[field].shape, dtype=bool)
            )
            sample = _raw_series_worst_sample(
                "cross_section",
                sample_id,
                field,
                reference[field],
                aligned_candidate[field],
                mask,
                threshold,
                reference,
                aligned_candidate,
                time_s=reference["times"],
                distance_m=reference["distance"],
                x_m=origin_x,
                y_m=origin_y,
                row_index=None,
                column_index=None,
                zone_id=None,
                reference_path=reference_path,
                cpp_path=cpp_path,
                cross_section_normal=(normal_x, normal_y),
                grid=grid,
                zones=zones,
            )
            if sample is not None:
                samples.append(sample)
    return tuple(sorted(samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)[:top_n])


def _raw_series_worst_sample(
    category: str,
    sample_id: str,
    field: str,
    reference_values: np.ndarray,
    candidate_values: np.ndarray,
    mask: np.ndarray,
    threshold: float,
    reference_context: dict[str, np.ndarray],
    candidate_context: dict[str, np.ndarray],
    *,
    time_s: np.ndarray,
    distance_m: np.ndarray | None,
    x_m: float | None,
    y_m: float | None,
    row_index: int | None,
    column_index: int | None,
    zone_id: str | None,
    reference_path: Path,
    cpp_path: Path,
    cross_section_normal: tuple[float, float] | None = None,
    grid: dict[str, object] | None = None,
    zones: dict[str, tuple[int, ...]] | None = None,
) -> Milestone18ConstrictionProbeCrossSectionSample | None:
    valid_indices = np.argwhere(mask)
    if valid_indices.size == 0:
        return None
    deltas = np.abs(reference_values - candidate_values)
    masked_errors = np.asarray([deltas[tuple(index)] for index in valid_indices], dtype=float)
    worst_slot = int(np.argmax(masked_errors))
    index_tuple = tuple(int(value) for value in valid_indices[worst_slot])
    if len(index_tuple) == 1:
        sample_time = float(time_s[index_tuple[0]])
        sample_distance = None
        sample_x = x_m
        sample_y = y_m
    else:
        sample_time = float(time_s[index_tuple[0]])
        sample_distance = float(distance_m[index_tuple[1]]) if distance_m is not None else None
        normal_x, normal_y = cross_section_normal or (0.0, 1.0)
        sample_x = x_m + normal_x * sample_distance if x_m is not None and sample_distance is not None else x_m
        sample_y = y_m + normal_y * sample_distance if y_m is not None and sample_distance is not None else y_m
        if grid is not None and sample_x is not None and sample_y is not None:
            row_index = _grid_row(sample_y, grid)
            column_index = _grid_column(sample_x, grid)
            zone_id = _zone_for_column(zones or {}, column_index)
    reference_value = float(reference_values[index_tuple])
    candidate_value = float(candidate_values[index_tuple])
    value = abs(reference_value - candidate_value)
    return Milestone18ConstrictionProbeCrossSectionSample(
        category=category,
        sample_id=sample_id,
        field=field,
        value=value,
        threshold=threshold,
        ratio_to_threshold=value / threshold if threshold > 0.0 else float("inf"),
        time_s=sample_time,
        reference_value=reference_value,
        candidate_value=candidate_value,
        delta=candidate_value - reference_value,
        reference_h=float(reference_context["h"][index_tuple]),
        candidate_h=float(candidate_context["h"][index_tuple]),
        reference_u=float(reference_context["u"][index_tuple]),
        candidate_u=float(candidate_context["u"][index_tuple]),
        reference_v=float(reference_context["v"][index_tuple]),
        candidate_v=float(candidate_context["v"][index_tuple]),
        reference_froude=float(reference_context["froude"][index_tuple]),
        candidate_froude=float(candidate_context["froude"][index_tuple]),
        distance_m=sample_distance,
        x_m=sample_x,
        y_m=sample_y,
        row_index=row_index,
        column_index=column_index,
        zone_id=zone_id,
        reference_path=str(reference_path),
        cpp_path=str(cpp_path),
    )


def _constriction_frame_worst_samples(
    frame_record: dict[str, Any],
    frame_index: int,
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    category: str,
    fields: tuple[str, ...],
    threshold: float,
    velocity_depth_floor_m: float,
) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
    reference_path = Path(str(frame_record.get("reference_frame") or frame_record.get("pyclaw_frame") or ""))
    cpp_path = Path(str(frame_record.get("cpp_frame") or ""))
    ny = int(grid["ny"])
    nx = int(grid["nx"])
    reference = _load_water_frame_fields(reference_path, ny, nx)
    candidate = _load_water_frame_fields(cpp_path, ny, nx)
    frame_label = _str_or_none(frame_record.get("label")) or f"frame_{frame_index:04d}"
    fallback_time_s = float(frame_index)
    time_s = _water_frame_time(reference_path, fallback_time_s)
    if category == "slope":
        ref_slope_x, ref_slope_y = _slopes_from_eta(reference["eta"], float(grid["dx"]), float(grid["dy"]))
        cand_slope_x, cand_slope_y = _slopes_from_eta(candidate["eta"], float(grid["dx"]), float(grid["dy"]))
        reference_fields = {"slope_x": ref_slope_x, "slope_y": ref_slope_y}
        candidate_fields = {"slope_x": cand_slope_x, "slope_y": cand_slope_y}
    else:
        reference_fields = reference
        candidate_fields = candidate

    samples: list[Milestone18ConstrictionShapeErrorSample] = []
    for field_name in fields:
        if field_name not in reference_fields or field_name not in candidate_fields:
            continue
        mask = None
        if field_name in VELOCITY_LIKE_FIELD_NAMES:
            mask = (reference["h"] >= velocity_depth_floor_m) & (candidate["h"] >= velocity_depth_floor_m)
        sample = _worst_grid_field_sample(
            category=category,
            field=field_name,
            source_id=frame_label,
            reference=np.asarray(reference_fields[field_name], dtype=float),
            candidate=np.asarray(candidate_fields[field_name], dtype=float),
            grid=grid,
            zones=zones,
            threshold=threshold,
            mask=mask,
            frame_label=frame_label,
            frame_index=frame_index,
            time_s=time_s,
            reference_path=reference_path,
            cpp_path=cpp_path,
        )
        if sample is not None:
            samples.append(sample)
    return tuple(samples)


def _worst_grid_field_sample(
    *,
    category: str,
    field: str,
    source_id: str,
    reference: np.ndarray,
    candidate: np.ndarray,
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    threshold: float,
    mask: np.ndarray | None,
    frame_label: str,
    frame_index: int,
    time_s: float,
    reference_path: Path,
    cpp_path: Path,
) -> Milestone18ConstrictionShapeErrorSample | None:
    if reference.shape != candidate.shape:
        raise ValueError(f"{field} shape mismatch: reference={reference.shape} C++={candidate.shape}")
    diff = candidate - reference
    abs_diff = np.abs(diff)
    if mask is not None:
        if mask.shape != abs_diff.shape:
            raise ValueError(f"{field} mask shape mismatch: mask={mask.shape} field={abs_diff.shape}")
        if not np.any(mask):
            return None
        abs_diff = np.where(mask, abs_diff, -1.0)
    row_index, column_index = (int(value) for value in np.unravel_index(int(np.argmax(abs_diff)), abs_diff.shape))
    value = float(abs(diff[row_index, column_index]))
    return Milestone18ConstrictionShapeErrorSample(
        category=category,
        field=field,
        source_id=source_id,
        value=value,
        threshold=threshold,
        ratio_to_threshold=_threshold_ratio(value, threshold),
        frame_label=frame_label,
        frame_index=frame_index,
        time_s=time_s,
        row_index=row_index,
        column_index=column_index,
        x_m=float(grid["origin_x"]) + column_index * float(grid["dx"]),
        y_m=float(grid["origin_y"]) + row_index * float(grid["dy"]),
        zone_id=_constriction_zone_for_column(column_index, zones),
        reference_value=float(reference[row_index, column_index]),
        candidate_value=float(candidate[row_index, column_index]),
        delta=float(diff[row_index, column_index]),
        reference_path=str(reference_path),
        cpp_path=str(cpp_path),
    )


def _shape_summary_samples(
    series_records: list[dict[str, Any]],
    *,
    category: str,
    threshold: float,
    fields: tuple[str, ...],
    top_n: int,
) -> tuple[Milestone18ConstrictionShapeErrorSample, ...]:
    field_order = {field: index for index, field in enumerate(fields)}
    samples: list[Milestone18ConstrictionShapeErrorSample] = []
    for record in series_records:
        source_id = str(record.get("sample_id", "unknown"))
        for error in _records(record, "field_errors"):
            field = str(error.get("field", "unknown"))
            if field_order and field not in field_order:
                continue
            value = _float_or_none(error.get("linf"))
            if value is None:
                continue
            samples.append(
                Milestone18ConstrictionShapeErrorSample(
                    category=category,
                    field=field,
                    source_id=source_id,
                    value=value,
                    threshold=threshold,
                    ratio_to_threshold=_threshold_ratio(value, threshold),
                )
            )
    return tuple(
        sorted(
            samples,
            key=lambda sample: (sample.ratio_to_threshold, -field_order.get(sample.field, 999)),
            reverse=True,
        )[:top_n]
    )


def _constriction_shape_timing_blocked_reasons(
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    slope_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    probe_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if _max_sample_exceeds(field_samples):
        reasons.append("C++ constriction field Linf still exceeds the GeoClaw/C++ threshold.")
    if _max_sample_exceeds(slope_samples):
        reasons.append("C++ constriction free-surface slope Linf still exceeds the GeoClaw/C++ threshold.")
    if _max_sample_exceeds(probe_samples):
        reasons.append("C++ constriction point-probe Linf still exceeds the GeoClaw/C++ threshold.")
    if _max_sample_exceeds(cross_section_samples):
        reasons.append("C++ constriction cross-section Linf still exceeds the GeoClaw/C++ threshold.")
    return tuple(reasons)


def _constriction_shape_timing_next_levers(
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    slope_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    probe_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
) -> tuple[str, ...]:
    samples = tuple(sorted(field_samples + slope_samples + probe_samples + cross_section_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True))
    if not samples:
        return ("No shape/timing samples were available; rerun the corrected-reference comparison before retuning.",)
    worst = samples[0]
    levers = [
        f"Start with `{worst.category}`/`{worst.field}` at `{worst.source_id}` because it is {_format_number(worst.ratio_to_threshold)}x the diagnostic threshold.",
    ]
    if any(sample.field in {"v", "hv", "slope_y"} for sample in samples[:6]):
        levers.append("Retune lateral velocity and cross-stream surface-slope shape before adding more downstream speed.")
    if any(sample.field in {"h", "eta", "slope_x"} for sample in samples[:6]):
        levers.append("Retune depth/free-surface distribution by zone so field and slope errors move together.")
    if any(sample.category == "cross_section" for sample in samples[:6]):
        levers.append("Use the mid-cross-section profile as the acceptance surface before another full parity run.")
    levers.append("Keep feature forcing off and rerun the Milestone 17 analytic guardrail after the next solver change.")
    return tuple(dict.fromkeys(levers))


def _constriction_response_zones(
    initial_state: dict[str, np.ndarray],
    grid: dict[str, object],
    feature: dict[str, object],
    wet_depth_threshold_m: float,
) -> dict[str, tuple[int, ...]]:
    nx = int(grid["nx"])
    h = initial_state["h"]
    wet_counts = [int(np.count_nonzero(h[:, col] > wet_depth_threshold_m)) for col in range(nx)]
    positive_counts = [count for count in wet_counts if count > 0]
    throat_count = min(positive_counts) if positive_counts else 0
    center_x = float(feature["center_x"])
    half_length = max(float(feature.get("length_m") or 0.0) * 0.5, float(grid["dx"]))
    flow_sign = _initial_flow_sign(initial_state)
    zones: dict[str, list[int]] = {
        "upstream_approach": [],
        "constriction_throat": [],
        "downstream_constriction": [],
        "recovery": [],
    }
    for col in range(nx):
        x = float(grid["origin_x"]) + col * float(grid["dx"])
        signed_x = (x - center_x) * flow_sign
        if wet_counts[col] == throat_count and wet_counts[col] > 0:
            zones["constriction_throat"].append(col)
        elif signed_x < 0.0:
            zones["upstream_approach"].append(col)
        elif signed_x <= half_length:
            zones["downstream_constriction"].append(col)
        else:
            zones["recovery"].append(col)
    return {zone_id: tuple(columns) for zone_id, columns in zones.items() if columns}


def _drop_ledge_response_zones(
    initial_state: dict[str, np.ndarray],
    grid: dict[str, object],
    ledge: dict[str, object],
    downstream: dict[str, object] | None,
) -> dict[str, tuple[int, ...]]:
    nx = int(grid["nx"])
    center_x = float(ledge["center_x"])
    dx = float(grid["dx"])
    control_half_width = max(float(ledge.get("width_m") or dx) * 0.5, dx)
    flow_sign = _initial_flow_sign(initial_state)
    downstream_extent = control_half_width + dx
    if downstream is not None:
        downstream_offset = abs((float(downstream["center_x"]) - center_x) * flow_sign)
        downstream_half_length = max(float(downstream.get("length_m") or 0.0) * 0.5, dx)
        downstream_extent = max(downstream_extent, downstream_offset + downstream_half_length)
    zones: dict[str, list[int]] = {
        "upstream_pool": [],
        "hydraulic_control": [],
        "tailwater_recovery": [],
        "downstream_pool": [],
    }
    for col in range(nx):
        x = float(grid["origin_x"]) + col * dx
        signed_x = (x - center_x) * flow_sign
        if signed_x < -control_half_width:
            zones["upstream_pool"].append(col)
        elif signed_x <= control_half_width:
            zones["hydraulic_control"].append(col)
        elif signed_x <= downstream_extent:
            zones["tailwater_recovery"].append(col)
        else:
            zones["downstream_pool"].append(col)
    return {zone_id: tuple(columns) for zone_id, columns in zones.items() if columns}


def _initial_flow_sign(initial_state: dict[str, np.ndarray]) -> float:
    discharge = float(np.sum(initial_state["h"] * initial_state["u"]))
    return 1.0 if discharge >= 0.0 else -1.0


def _constriction_zone_snapshots(
    solver_label: str,
    manifest: dict[str, Any],
    manifest_dir: Path,
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    wet_depth_threshold_m: float,
    *,
    default_duration_s: float,
) -> tuple[Milestone18ConstrictionZoneSnapshot, ...]:
    frame_paths = _frame_paths(manifest, manifest_dir)
    ny = int(grid["ny"])
    nx = int(grid["nx"])
    snapshots: list[Milestone18ConstrictionZoneSnapshot] = []
    denominator = max(1, len(frame_paths) - 1)
    for frame_index, frame_path in enumerate(frame_paths):
        fallback_time_s = default_duration_s if len(frame_paths) == 1 else default_duration_s * frame_index / denominator
        state = _load_water_frame(frame_path, ny, nx)
        time_s = _water_frame_time(frame_path, fallback_time_s)
        for zone_id, columns in zones.items():
            snapshots.append(
                _constriction_zone_snapshot(
                    solver_label,
                    zone_id,
                    frame_index,
                    frame_path,
                    time_s,
                    columns,
                    state,
                    grid,
                    wet_depth_threshold_m,
                )
            )
    return tuple(snapshots)


def _constriction_zone_snapshot(
    solver_label: str,
    zone_id: str,
    frame_index: int,
    source_path: Path,
    time_s: float,
    columns: tuple[int, ...],
    state: dict[str, np.ndarray],
    grid: dict[str, object],
    wet_depth_threshold_m: float,
) -> Milestone18ConstrictionZoneSnapshot:
    h = state["h"][:, list(columns)]
    u = state["u"][:, list(columns)]
    v = state["v"][:, list(columns)]
    froude = state["froude"][:, list(columns)]
    cell_area = float(grid["dx"]) * float(grid["dy"])
    wet_mask = h > wet_depth_threshold_m
    wet_count = int(np.count_nonzero(wet_mask))
    wet_h = h[wet_mask]
    weights = np.where(wet_mask, h, 0.0)
    wet_mass = float(np.sum(weights))
    if wet_count and wet_mass > 0.0:
        mean_depth = float(np.mean(wet_h))
        mean_u = float(np.sum(u * weights) / wet_mass)
        mean_v = float(np.sum(v * weights) / wet_mass)
        max_froude = float(np.max(froude[wet_mask]))
        mean_froude = float(np.mean(froude[wet_mask]))
    else:
        mean_depth = 0.0
        mean_u = 0.0
        mean_v = 0.0
        max_froude = 0.0
        mean_froude = 0.0
    return Milestone18ConstrictionZoneSnapshot(
        solver_label=solver_label,
        zone_id=zone_id,
        frame_index=frame_index,
        source_path=str(source_path),
        time_s=float(time_s),
        column_indices=columns,
        wet_cell_count=wet_count,
        total_mass_m3=float(np.sum(h) * cell_area),
        mean_wet_depth_m=mean_depth,
        max_depth_m=float(np.max(h)) if h.size else 0.0,
        mean_downstream_velocity_mps=mean_u,
        mean_cross_stream_velocity_mps=mean_v,
        kinetic_energy_like_j=float(np.sum(0.5 * h * (u * u + v * v)) * cell_area),
        max_froude=max_froude,
        mean_wet_froude=mean_froude,
    )


def _constriction_zone_delta(
    zone_id: str,
    columns: tuple[int, ...],
    geoclaw_snapshots: tuple[Milestone18ConstrictionZoneSnapshot, ...],
    cpp_snapshots: tuple[Milestone18ConstrictionZoneSnapshot, ...],
) -> Milestone18ConstrictionZoneDelta:
    geoclaw_zone = tuple(snapshot for snapshot in geoclaw_snapshots if snapshot.zone_id == zone_id)
    cpp_zone = tuple(snapshot for snapshot in cpp_snapshots if snapshot.zone_id == zone_id)
    if not geoclaw_zone or not cpp_zone:
        raise ValueError(f"Missing snapshots for constriction zone {zone_id}.")
    geoclaw_final = max(geoclaw_zone, key=lambda snapshot: snapshot.time_s)
    cpp_final = max(cpp_zone, key=lambda snapshot: snapshot.time_s)
    geoclaw_peak_mass = max(geoclaw_zone, key=lambda snapshot: snapshot.total_mass_m3)
    cpp_peak_mass = max(cpp_zone, key=lambda snapshot: snapshot.total_mass_m3)
    geoclaw_peak_energy = max(geoclaw_zone, key=lambda snapshot: snapshot.kinetic_energy_like_j)
    cpp_peak_energy = max(cpp_zone, key=lambda snapshot: snapshot.kinetic_energy_like_j)
    return Milestone18ConstrictionZoneDelta(
        zone_id=zone_id,
        column_indices=columns,
        final_mass_delta_m3=cpp_final.total_mass_m3 - geoclaw_final.total_mass_m3,
        final_mean_wet_depth_delta_m=cpp_final.mean_wet_depth_m - geoclaw_final.mean_wet_depth_m,
        final_max_depth_delta_m=cpp_final.max_depth_m - geoclaw_final.max_depth_m,
        final_kinetic_energy_delta_j=cpp_final.kinetic_energy_like_j - geoclaw_final.kinetic_energy_like_j,
        final_max_froude_delta=cpp_final.max_froude - geoclaw_final.max_froude,
        peak_mass_delta_m3=cpp_peak_mass.total_mass_m3 - geoclaw_peak_mass.total_mass_m3,
        peak_mass_time_delta_s=cpp_peak_mass.time_s - geoclaw_peak_mass.time_s,
        peak_energy_delta_j=cpp_peak_energy.kinetic_energy_like_j - geoclaw_peak_energy.kinetic_energy_like_j,
        peak_energy_time_delta_s=cpp_peak_energy.time_s - geoclaw_peak_energy.time_s,
    )


def _constriction_response_blocked_reasons(
    zone_deltas: tuple[Milestone18ConstrictionZoneDelta, ...],
    thresholds: dict[str, float],
) -> tuple[str, ...]:
    if not zone_deltas:
        return ("No constriction response zones were available for timing diagnostics.",)
    max_mass = max(abs(delta.final_mass_delta_m3) for delta in zone_deltas)
    max_depth = max(abs(delta.final_mean_wet_depth_delta_m) for delta in zone_deltas)
    max_peak_time = max(abs(delta.peak_energy_time_delta_s) for delta in zone_deltas)
    max_peak_energy = max(abs(delta.peak_energy_delta_j) for delta in zone_deltas)
    max_froude = max(abs(delta.final_max_froude_delta) for delta in zone_deltas)
    reasons: list[str] = []
    if max_mass > thresholds["max_abs_final_mass_delta_m3"]:
        reasons.append("C++ final constriction-zone mass differs from GeoClaw beyond the diagnostic budget.")
    if max_depth > thresholds["max_abs_final_mean_wet_depth_delta_m"]:
        reasons.append("C++ final mean wet depth differs from GeoClaw beyond the diagnostic budget.")
    if max_peak_time > thresholds["max_abs_peak_energy_time_delta_s"]:
        reasons.append("C++ peak-energy timing differs from GeoClaw beyond the diagnostic budget.")
    if max_peak_energy > thresholds["max_abs_peak_energy_delta_j"]:
        reasons.append("C++ peak-energy magnitude differs from GeoClaw beyond the diagnostic budget.")
    if max_froude > thresholds["max_abs_final_froude_delta"]:
        reasons.append("C++ final zone Froude envelope differs from GeoClaw beyond the diagnostic budget.")
    return tuple(reasons)


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


def _column_span(columns: tuple[int, ...]) -> str:
    if not columns:
        return "none"
    if len(columns) == 1:
        return str(columns[0])
    return f"{columns[0]}-{columns[-1]}"


def _max_sample_value(samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]) -> float:
    return max((sample.value for sample in samples), default=0.0)


def _max_raw_series_sample_value(samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]) -> float:
    return max((sample.value for sample in samples), default=0.0)


def _max_sample_exceeds(samples: tuple[Milestone18ConstrictionShapeErrorSample, ...]) -> bool:
    return any(not sample.passed for sample in samples)


def _max_raw_sample_exceeds(samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...]) -> bool:
    return any(not sample.passed for sample in samples)


def _probe_cross_section_blocked_reasons(
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if _max_raw_sample_exceeds(probe_samples):
        reasons.append("C++ constriction point-probe raw samples still exceed the GeoClaw/C++ threshold.")
    if _max_raw_sample_exceeds(cross_section_samples):
        reasons.append("C++ constriction cross-section raw samples still exceed the GeoClaw/C++ threshold.")
    if any(sample.field in {"v", "hv"} and not sample.passed for sample in probe_samples + cross_section_samples):
        reasons.append("Cross-stream velocity or momentum has the wrong magnitude/sign at sampled constriction locations.")
    if any(sample.field == "froude" and not sample.passed for sample in probe_samples + cross_section_samples):
        reasons.append("Froude mismatch is still present in the sampled constriction section.")
    return tuple(reasons)


def _probe_cross_section_next_levers(
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
) -> tuple[str, ...]:
    samples = tuple(
        sorted(probe_samples + cross_section_samples, key=lambda sample: sample.ratio_to_threshold, reverse=True)
    )
    if not samples:
        return ()
    levers = [
        (
            f"Retune from `{samples[0].category}` `{samples[0].sample_id}` field `{samples[0].field}` "
            f"at t={samples[0].time_s:.6g}s because it is {samples[0].ratio_to_threshold:.6g}x threshold."
        )
    ]
    if any(sample.field in {"v", "hv"} for sample in samples[:6]):
        levers.append(
            "Correct cross-stream circulation sign and magnitude at the sampled constriction centerline before changing more depth volume."
        )
    if any(sample.field == "froude" for sample in samples[:6]):
        levers.append(
            "Preserve the Froude envelope while changing lateral circulation; the previous shape pass regressed Froude just over threshold."
        )
    if any(sample.category == "cross_section" for sample in samples[:6]):
        levers.append(
            "Use the recorded cross-section distance and cell coordinates to tune section shape, not only whole-field Linf cells."
        )
    return tuple(levers)


def _drop_ledge_zone_summaries(
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    zones: dict[str, tuple[int, ...]],
    wet_depth_threshold_m: float,
) -> tuple[Milestone18DropLedgeZoneSummary, ...]:
    summaries: list[Milestone18DropLedgeZoneSummary] = []
    for zone_id, columns in zones.items():
        if not columns:
            continue
        column_indices = np.asarray(columns, dtype=np.int64)
        reference_h = reference_state["h"][:, column_indices]
        candidate_h = candidate_state["h"][:, column_indices]
        reference_eta = reference_state["eta"][:, column_indices]
        candidate_eta = candidate_state["eta"][:, column_indices]
        reference_u = reference_state["u"][:, column_indices]
        candidate_u = candidate_state["u"][:, column_indices]
        reference_froude = reference_state["froude"][:, column_indices]
        candidate_froude = candidate_state["froude"][:, column_indices]
        reference_wet = reference_h > wet_depth_threshold_m
        candidate_wet = candidate_h > wet_depth_threshold_m
        reference_mean_h = _masked_mean(reference_h, reference_wet)
        candidate_mean_h = _masked_mean(candidate_h, candidate_wet)
        reference_mean_eta = _masked_mean(reference_eta, reference_wet)
        candidate_mean_eta = _masked_mean(candidate_eta, candidate_wet)
        reference_mean_u = _masked_mean(reference_u, reference_wet)
        candidate_mean_u = _masked_mean(candidate_u, candidate_wet)
        reference_mean_froude = _masked_mean(reference_froude, reference_wet)
        candidate_mean_froude = _masked_mean(candidate_froude, candidate_wet)
        summaries.append(
            Milestone18DropLedgeZoneSummary(
                zone_id=zone_id,
                columns=tuple(int(col) for col in columns),
                reference_mean_h=reference_mean_h,
                candidate_mean_h=candidate_mean_h,
                mean_h_delta=candidate_mean_h - reference_mean_h,
                reference_mean_eta=reference_mean_eta,
                candidate_mean_eta=candidate_mean_eta,
                mean_eta_delta=candidate_mean_eta - reference_mean_eta,
                reference_mean_u=reference_mean_u,
                candidate_mean_u=candidate_mean_u,
                mean_u_delta=candidate_mean_u - reference_mean_u,
                reference_mean_froude=reference_mean_froude,
                candidate_mean_froude=candidate_mean_froude,
                mean_froude_delta=candidate_mean_froude - reference_mean_froude,
                reference_wet_cell_count=int(np.count_nonzero(reference_wet)),
                candidate_wet_cell_count=int(np.count_nonzero(candidate_wet)),
            )
        )
    return tuple(summaries)


def _masked_mean(values: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.asarray(values, dtype=float)[mask]))


def _drop_ledge_hydraulic_control_blocked_reasons(
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if _max_sample_exceeds(field_samples):
        reasons.append("C++ drop/ledge final-field Linf still exceeds the GeoClaw/C++ threshold.")
    if _max_raw_sample_exceeds(probe_samples):
        reasons.append("C++ drop/ledge point-probe raw samples still exceed the GeoClaw/C++ threshold.")
    if _max_raw_sample_exceeds(cross_section_samples):
        reasons.append("C++ drop/ledge cross-section raw samples still exceed the GeoClaw/C++ threshold.")
    if _samples_touch_drop_control_or_tailwater(field_samples, probe_samples, cross_section_samples):
        reasons.append("The remaining drop/ledge error is localized to hydraulic-control or tailwater-recovery water shape.")
    return tuple(reasons)


def _drop_ledge_hydraulic_control_next_levers(
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    threshold_report: dict[str, Any],
) -> tuple[str, ...]:
    samples = tuple(
        sorted(
            field_samples + probe_samples + cross_section_samples,
            key=lambda sample: sample.ratio_to_threshold,
            reverse=True,
        )
    )
    if not samples:
        return ("No drop/ledge samples were available; rerun the corrected-reference comparison before retuning.",)
    worst = samples[0]
    source_id = getattr(worst, "source_id", getattr(worst, "sample_id", "unknown"))
    location = f"`{worst.category}`/`{worst.field}` at `{source_id}`"
    if getattr(worst, "row_index", None) is not None and getattr(worst, "column_index", None) is not None:
        location += f" cell {worst.row_index},{worst.column_index}"
    levers = [
        f"Start with {location}; it is {_format_number(worst.ratio_to_threshold)}x the diagnostic threshold.",
        "Retune the ledge hydraulic-control free-surface/depth reconstruction and downstream recovery shape before adding gameplay feature forcing.",
    ]
    if _threshold_checks_pass(threshold_report, ("mass_drift_delta", "energy_change_delta", "froude_delta")):
        levers.append(
            "Preserve the passing conservation, energy, and Froude checks; this is a water-shape blocker, not permission to hide errors with forcing."
        )
    if any(sample.field in {"h", "eta", "hu"} for sample in samples[:6]):
        levers.append("Inspect depth, stage, and streamwise momentum across the ledge lip and first tailwater recovery columns.")
    if any(sample.category in {"probe", "cross_section"} for sample in samples[:6]):
        levers.append("Use the raw probe/cross-section coordinates as the acceptance surface for the next corrected-reference parity run.")
    levers.append("Keep `feature_strength_scale=0` and rerun the Milestone 17 analytic guardrail after the solver change.")
    return tuple(dict.fromkeys(levers))


def _focused_geometry_evidence_by_case(
    focused_reports: tuple[str | Path, ...],
) -> dict[str, tuple[dict[str, object], ...]]:
    by_case: dict[str, list[dict[str, object]]] = {}
    for report_ref in focused_reports:
        path = Path(report_ref)
        if not path.exists():
            continue
        payload = _load_json_report(path)
        case_id = _focused_geometry_case_id(payload, path)
        if case_id is None:
            continue
        summary = payload.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        by_case.setdefault(case_id, []).append(
            {
                "source_report": str(path),
                "schema_version": str(payload.get("schema_version", "unknown")),
                "decision": str(payload.get("decision", "UNKNOWN")),
                "passed": bool(payload.get("passed")),
                "blocked_reasons": tuple(str(reason) for reason in payload.get("blocked_reasons", []) if isinstance(reason, str)),
                "next_levers": tuple(str(lever) for lever in payload.get("next_levers", []) if isinstance(lever, str)),
                "summary": _compact_report_summary(summary),
            }
        )
    return {case_id: tuple(records) for case_id, records in by_case.items()}


def _compact_report_summary(summary: dict[str, object]) -> dict[str, object]:
    compact: dict[str, object] = {}
    for key, value in summary.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            compact[key] = value
        elif isinstance(value, list):
            compact[f"{key}_count"] = len(value)
        elif isinstance(value, dict):
            compact[f"{key}_key_count"] = len(value)
    return compact


def _focused_geometry_case_id(payload: dict[str, Any], path: Path) -> str | None:
    schema = str(payload.get("schema_version", ""))
    haystack = f"{schema} {path}".lower()
    if "constriction" in haystack:
        return "constriction"
    if "drop_ledge" in haystack or "drop/ledge" in haystack:
        return "drops_ledges_tailwater"
    return None


def _geometry_failing_check_counts(evidence_records: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in evidence_records:
        if bool(record.get("diagnostic_only")):
            continue
        if bool(record.get("threshold_passed")) or bool(record.get("passed")):
            continue
        for check in record.get("failing_checks", []):
            if isinstance(check, str):
                counts[check] += 1
    return dict(sorted(counts.items()))


def _geometry_failing_scenario_count(evidence_records: list[dict[str, Any]]) -> int:
    scenarios = {
        str(record.get("gate_scenario_id"))
        for record in evidence_records
        if (
            not bool(record.get("diagnostic_only"))
            and not bool(record.get("threshold_passed"))
            and not bool(record.get("passed"))
        )
        and record.get("gate_scenario_id")
    }
    return len(scenarios)


def _remaining_geometry_priority(case_id: str) -> int:
    return {
        "constriction": 1,
        "drops_ledges_tailwater": 2,
        "stitched_reach_drop_handoffs": 3,
        "wet_dry_shoreline": 10,
        "bed_step": 11,
        "hydrostatic_sloping_balance": 12,
    }.get(case_id, 50)


def _remaining_geometry_notes(
    case_id: str,
    notes: tuple[str, ...],
    evidence_records: list[dict[str, Any]],
) -> tuple[str, ...]:
    result = list(notes)
    if case_id == "drops_ledges_tailwater":
        cascading_failures = sorted(
            {
                str(record.get("gate_scenario_id"))
                for record in evidence_records
                if str(record.get("gate_scenario_id", "")).startswith("south_fork_cascading")
                and not bool(record.get("threshold_passed"))
            }
        )
        if cascading_failures:
            result.append(
                "Cascading reach/drop handoff checks pass separately; these failures are whole-window water-field parity blockers: "
                + ", ".join(cascading_failures)
                + "."
            )
    if case_id == "stitched_reach_drop_handoffs":
        result.append("Keep this passing stitched-window seam evidence as a guardrail while retuning cascading water fields.")
    return tuple(dict.fromkeys(result))


def _remaining_geometry_next_levers(
    case_id: str,
    focused_evidence: tuple[dict[str, object], ...],
    failing_counts: dict[str, int],
    evidence_records: list[dict[str, Any]],
) -> tuple[str, ...]:
    if not failing_counts:
        return ("Preserve this geometry family as a guardrail while retuning active blockers.",)
    levers: list[str] = []
    has_hydrostatic_source_decision = any(
        "constriction_hydrostatic_source_decision" in str(evidence.get("schema_version", ""))
        for evidence in focused_evidence
    )
    for evidence in focused_evidence:
        for lever in evidence.get("next_levers", ()):
            if not isinstance(lever, str):
                continue
            if has_hydrostatic_source_decision and lever.startswith(
                "Decide whether constriction y-faces need hydrostatic"
            ):
                continue
            levers.append(lever)
    if case_id == "constriction":
        levers.append(
            "Close constriction field, slope, probe, cross-section, and wet-mask parity before treating raft coupling as actionable."
        )
    elif case_id == "drops_ledges_tailwater":
        if any(str(record.get("gate_scenario_id", "")).startswith("drop_ledge") for record in evidence_records):
            levers.append("Retune the single drop/ledge hydraulic-control lane before folding the fix into cascading South Fork flows.")
        if any(str(record.get("gate_scenario_id", "")).startswith("south_fork_cascading") for record in evidence_records):
            levers.append(
                "Use stitched whole-window cascading comparisons for acceptance; reach-local seams already pass and cannot hide water-field errors."
            )
    else:
        levers.append("Regenerate focused evidence for this geometry family before attempting promotion.")
    if "mass_drift_delta" in failing_counts or "energy_change_delta" in failing_counts:
        levers.append("Preserve or restore conservation and energy checks before accepting any visual/gameplay forcing.")
    return tuple(dict.fromkeys(levers))


def _counter_markdown(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _samples_touch_drop_control_or_tailwater(
    field_samples: tuple[Milestone18ConstrictionShapeErrorSample, ...],
    probe_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
    cross_section_samples: tuple[Milestone18ConstrictionProbeCrossSectionSample, ...],
) -> bool:
    zones = {"hydraulic_control", "tailwater_recovery"}
    for sample in field_samples + probe_samples + cross_section_samples:
        if not sample.passed and sample.zone_id in zones:
            return True
    return False


def _threshold_checks_pass(threshold_report: dict[str, Any], names: tuple[str, ...]) -> bool:
    remaining = set(names)
    for check in _records(threshold_report, "checks"):
        name = check.get("name")
        if name in remaining and bool(check.get("passed")):
            remaining.remove(str(name))
    return not remaining


def _nested_value(record: dict[str, object], *keys: str) -> object | None:
    current: object = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _constriction_face_state_width_depth_column_profiles(
    initial_state: dict[str, np.ndarray],
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    wet_depth_threshold_m: float,
    depth_delta_threshold_m: float,
    wet_width_delta_threshold_cells: int,
    bank_row_delta_threshold_cells: int,
) -> tuple[dict[str, object], ...]:
    columns = sorted(set(zones.get("upstream_approach", ()) + zones.get("constriction_throat", ())))
    profiles: list[dict[str, object]] = []
    for col in columns:
        authored = _wet_band_column_profile(initial_state, grid, col, wet_depth_threshold_m)
        reference = _wet_band_column_profile(reference_state, grid, col, wet_depth_threshold_m)
        candidate = _wet_band_column_profile(candidate_state, grid, col, wet_depth_threshold_m)
        cpp_minus_geoclaw = _wet_band_profile_delta(candidate, reference)
        authored_minus_geoclaw = _wet_band_profile_delta(authored, reference)
        wet_width_delta = int(cpp_minus_geoclaw.get("wet_width_delta_cells") or 0)
        bank_row_delta = int(cpp_minus_geoclaw.get("max_abs_bank_row_delta_cells") or 0)
        mean_depth_delta = float(cpp_minus_geoclaw.get("mean_wet_depth_delta_m") or 0.0)
        profiles.append(
            {
                "column_index": col,
                "zone_id": _constriction_zone_for_column(col, zones),
                "x_m": float(grid["origin_x"]) + col * float(grid["dx"]),
                "authored_initial": authored,
                "geoclaw_final": reference,
                "cpp_final": candidate,
                "cpp_minus_geoclaw": cpp_minus_geoclaw,
                "authored_initial_minus_geoclaw": authored_minus_geoclaw,
                "width_mapping_blocked": abs(wet_width_delta) > wet_width_delta_threshold_cells,
                "bank_alignment_blocked": bank_row_delta > bank_row_delta_threshold_cells,
                "depth_mapping_blocked": abs(mean_depth_delta) > depth_delta_threshold_m,
            }
        )
    return tuple(profiles)


def _wet_band_column_profile(
    state: dict[str, np.ndarray],
    grid: dict[str, object],
    column_index: int,
    wet_depth_threshold_m: float,
) -> dict[str, object]:
    h = np.asarray(state["h"])[:, column_index]
    eta = np.asarray(state.get("eta", state["h"]))[:, column_index]
    wet_rows = np.flatnonzero(h > wet_depth_threshold_m)
    cell_area_m2 = float(grid["dx"]) * float(grid["dy"])
    if wet_rows.size == 0:
        return {
            "wet_width_cell_count": 0,
            "first_wet_row": None,
            "last_wet_row": None,
            "mean_wet_depth_m": 0.0,
            "max_wet_depth_m": 0.0,
            "mean_wet_eta_m": None,
            "column_water_volume_m3": float(np.sum(h) * cell_area_m2),
        }
    wet_h = h[wet_rows]
    wet_eta = eta[wet_rows]
    return {
        "wet_width_cell_count": int(wet_rows.size),
        "first_wet_row": int(wet_rows[0]),
        "last_wet_row": int(wet_rows[-1]),
        "mean_wet_depth_m": float(np.mean(wet_h)),
        "max_wet_depth_m": float(np.max(wet_h)),
        "mean_wet_eta_m": float(np.mean(wet_eta)),
        "column_water_volume_m3": float(np.sum(h) * cell_area_m2),
    }


def _wet_band_profile_delta(candidate: dict[str, object], reference: dict[str, object]) -> dict[str, object]:
    first_delta = _optional_int_delta(candidate.get("first_wet_row"), reference.get("first_wet_row"))
    last_delta = _optional_int_delta(candidate.get("last_wet_row"), reference.get("last_wet_row"))
    bank_deltas = [abs(delta) for delta in (first_delta, last_delta) if delta is not None]
    return {
        "wet_width_delta_cells": int(candidate.get("wet_width_cell_count") or 0)
        - int(reference.get("wet_width_cell_count") or 0),
        "first_wet_row_delta_cells": first_delta,
        "last_wet_row_delta_cells": last_delta,
        "max_abs_bank_row_delta_cells": max(bank_deltas, default=0),
        "mean_wet_depth_delta_m": float(candidate.get("mean_wet_depth_m") or 0.0)
        - float(reference.get("mean_wet_depth_m") or 0.0),
        "max_wet_depth_delta_m": float(candidate.get("max_wet_depth_m") or 0.0)
        - float(reference.get("max_wet_depth_m") or 0.0),
        "column_water_volume_delta_m3": float(candidate.get("column_water_volume_m3") or 0.0)
        - float(reference.get("column_water_volume_m3") or 0.0),
    }


def _optional_int_delta(candidate: object, reference: object) -> int | None:
    if candidate is None or reference is None:
        return None
    return int(candidate) - int(reference)


def _constriction_face_state_width_depth_samples(
    samples: tuple[Milestone18ConstrictionLateralFaceFluxSample, ...],
    column_profiles: tuple[dict[str, object], ...],
    *,
    depth_delta_threshold_m: float,
) -> tuple[dict[str, object], ...]:
    profile_by_column = {int(profile["column_index"]): profile for profile in column_profiles}
    records: list[dict[str, object]] = []
    for sample in samples:
        profile = profile_by_column.get(sample.column_index, {})
        column_delta = _nested_value(profile, "cpp_minus_geoclaw") or {}
        if not isinstance(column_delta, dict):
            column_delta = {}
        mean_depth_delta = sample.candidate_mean_h - sample.reference_mean_h
        face_state_blocked = (
            not sample.sign_matches
            or sample.abs_flux_delta_m3ps > sample.flux_delta_threshold_m3ps
            or abs(mean_depth_delta) > depth_delta_threshold_m
        )
        width_mapping_blocked = bool(profile.get("width_mapping_blocked"))
        bank_alignment_blocked = bool(profile.get("bank_alignment_blocked"))
        depth_mapping_blocked = bool(profile.get("depth_mapping_blocked"))
        records.append(
            {
                "face_role": sample.face_role,
                "column_index": sample.column_index,
                "south_row_index": sample.south_row_index,
                "north_row_index": sample.north_row_index,
                "zone_id": profile.get("zone_id"),
                "x_m": sample.x_m,
                "y_face_m": sample.y_face_m,
                "reference_mean_h": sample.reference_mean_h,
                "candidate_mean_h": sample.candidate_mean_h,
                "mean_depth_delta_m": mean_depth_delta,
                "reference_mean_v": sample.reference_mean_v,
                "candidate_mean_v": sample.candidate_mean_v,
                "reference_volume_flux_m3ps": sample.reference_lateral_volume_flux_m3ps,
                "candidate_volume_flux_m3ps": sample.candidate_lateral_volume_flux_m3ps,
                "volume_flux_delta_m3ps": sample.flux_delta_m3ps,
                "abs_volume_flux_delta_m3ps": sample.abs_flux_delta_m3ps,
                "flux_delta_threshold_m3ps": sample.flux_delta_threshold_m3ps,
                "reference_volume_sign": sample.reference_sign,
                "candidate_volume_sign": sample.candidate_sign,
                "volume_sign_matches": sample.sign_matches,
                "wet_width_delta_cells": column_delta.get("wet_width_delta_cells"),
                "first_wet_row_delta_cells": column_delta.get("first_wet_row_delta_cells"),
                "last_wet_row_delta_cells": column_delta.get("last_wet_row_delta_cells"),
                "max_abs_bank_row_delta_cells": column_delta.get("max_abs_bank_row_delta_cells"),
                "column_mean_wet_depth_delta_m": column_delta.get("mean_wet_depth_delta_m"),
                "face_state_blocked": face_state_blocked,
                "width_mapping_blocked": width_mapping_blocked,
                "bank_alignment_blocked": bank_alignment_blocked,
                "depth_mapping_blocked": depth_mapping_blocked,
                "recommended_solver_lever": _face_state_width_depth_solver_lever(
                    face_state_blocked,
                    width_mapping_blocked or bank_alignment_blocked or depth_mapping_blocked,
                ),
            }
        )
    return tuple(
        sorted(
            records,
            key=lambda sample: (
                bool(sample.get("face_state_blocked")),
                not bool(sample.get("volume_sign_matches", True)),
                abs(float(sample.get("volume_flux_delta_m3ps", 0.0) or 0.0)),
            ),
            reverse=True,
        )
    )


def _face_state_width_depth_solver_lever(face_state_blocked: bool, geometry_blocked: bool) -> str:
    if face_state_blocked and geometry_blocked:
        return "geometry_aware_face_state_reconstruction_with_width_depth_mapping_check"
    if face_state_blocked:
        return "geometry_aware_face_state_reconstruction"
    if geometry_blocked:
        return "width_depth_mapping"
    return "preserve_as_guardrail"


def _constriction_face_state_width_depth_edge_pair_summary(
    samples: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    by_col: dict[int, dict[str, dict[str, object]]] = {}
    for sample in samples:
        by_col.setdefault(int(sample["column_index"]), {})[str(sample["face_role"])] = sample
    pairs: list[dict[str, object]] = []
    for col, faces in sorted(by_col.items()):
        lower = faces.get("lower_edge_face")
        upper = faces.get("upper_edge_face")
        if lower is None or upper is None:
            continue
        lower_reference_sign = int(lower.get("reference_volume_sign") or 0)
        upper_reference_sign = int(upper.get("reference_volume_sign") or 0)
        lower_candidate_sign = int(lower.get("candidate_volume_sign") or 0)
        upper_candidate_sign = int(upper.get("candidate_volume_sign") or 0)
        reference_opposed = (
            lower_reference_sign != 0
            and upper_reference_sign != 0
            and lower_reference_sign == -upper_reference_sign
        )
        candidate_opposed = (
            lower_candidate_sign != 0
            and upper_candidate_sign != 0
            and lower_candidate_sign == -upper_candidate_sign
        )
        pairs.append(
            {
                "column_index": col,
                "lower_reference_volume_sign": lower_reference_sign,
                "upper_reference_volume_sign": upper_reference_sign,
                "lower_candidate_volume_sign": lower_candidate_sign,
                "upper_candidate_volume_sign": upper_candidate_sign,
                "reference_opposed_edges": reference_opposed,
                "candidate_opposed_edges": candidate_opposed,
                "matches_reference_opposition": (not reference_opposed) or candidate_opposed,
                "lower_abs_volume_flux_delta_m3ps": abs(float(lower.get("volume_flux_delta_m3ps", 0.0) or 0.0)),
                "upper_abs_volume_flux_delta_m3ps": abs(float(upper.get("volume_flux_delta_m3ps", 0.0) or 0.0)),
                "wet_width_delta_cells": _nested_value(lower, "wet_width_delta_cells"),
                "max_abs_bank_row_delta_cells": _nested_value(lower, "max_abs_bank_row_delta_cells"),
            }
        )
    return tuple(pairs)


def _face_state_width_depth_blocked_reasons(
    column_profiles: tuple[dict[str, object], ...],
    face_state_samples: tuple[dict[str, object], ...],
    edge_pair_summary: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not face_state_samples:
        reasons.append("No upstream edge face-state samples were available for the constriction diagnostic.")
    if any(not bool(sample.get("volume_sign_matches", True)) for sample in face_state_samples):
        reasons.append("C++ upstream edge face-state signs still disagree with GeoClaw.")
    if any(
        abs(float(sample.get("volume_flux_delta_m3ps", 0.0) or 0.0))
        > float(sample.get("flux_delta_threshold_m3ps", 0.0) or 0.0)
        for sample in face_state_samples
    ):
        reasons.append("C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.")
    if any(not bool(pair.get("matches_reference_opposition", True)) for pair in edge_pair_summary):
        reasons.append("GeoClaw lower/upper edge opposition is still missing from the C++ face states.")
    if any(bool(profile.get("width_mapping_blocked")) for profile in column_profiles):
        reasons.append("C++ constriction wet-band width still differs from GeoClaw beyond the mapping threshold.")
    if any(bool(profile.get("bank_alignment_blocked")) for profile in column_profiles):
        reasons.append("C++ constriction bank row placement still differs from GeoClaw beyond the mapping threshold.")
    if any(bool(profile.get("depth_mapping_blocked")) for profile in column_profiles):
        reasons.append("C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.")
    return tuple(reasons)


def _face_state_width_depth_next_levers(
    column_profiles: tuple[dict[str, object], ...],
    face_state_samples: tuple[dict[str, object], ...],
    edge_pair_summary: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    if not face_state_samples:
        return ("Regenerate the constriction comparison with upstream wet-band edge samples before changing the solver.",)
    worst = face_state_samples[0]
    wet_width_delta = _format_number(_float_or_none(worst.get("wet_width_delta_cells")))
    bank_delta = _format_number(_float_or_none(worst.get("max_abs_bank_row_delta_cells")))
    levers = [
        (
            f"Start with `{worst.get('face_role')}` column {worst.get('column_index')} rows "
            f"{worst.get('south_row_index')}-{worst.get('north_row_index')}; q delta is "
            f"{_format_number(_float_or_none(worst.get('volume_flux_delta_m3ps')))} m3/s, face mean-depth delta is "
            f"{_format_number(_float_or_none(worst.get('mean_depth_delta_m')))} m, wet-width delta is "
            f"{wet_width_delta} cells, and max bank-row delta is {bank_delta} cells."
        )
    ]
    has_face_state_blocker = any(bool(sample.get("face_state_blocked")) for sample in face_state_samples)
    has_geometry_blocker = any(
        bool(profile.get("width_mapping_blocked"))
        or bool(profile.get("bank_alignment_blocked"))
        or bool(profile.get("depth_mapping_blocked"))
        for profile in column_profiles
    )
    if has_face_state_blocker:
        levers.append(
            "Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs."
        )
    if has_geometry_blocker:
        levers.append(
            "Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change."
        )
    if any(not bool(pair.get("matches_reference_opposition", True)) for pair in edge_pair_summary):
        levers.append(
            "Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker."
        )
    levers.append(
        "Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail."
    )
    return tuple(dict.fromkeys(levers))


def _constriction_upstream_lateral_face_samples(
    initial_state: dict[str, np.ndarray],
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    wet_depth_threshold_m: float,
    velocity_sign_floor_mps: float,
    flux_delta_threshold_m3ps: float,
) -> tuple[Milestone18ConstrictionLateralFaceFluxSample, ...]:
    samples: list[Milestone18ConstrictionLateralFaceFluxSample] = []
    upstream_columns = zones.get("upstream_approach", ())
    for col in upstream_columns:
        wet_rows = np.flatnonzero(initial_state["h"][:, col] > wet_depth_threshold_m)
        if wet_rows.size == 0:
            continue
        first_row = int(wet_rows[0])
        last_row = int(wet_rows[-1])
        if first_row > 0:
            samples.append(
                _lateral_face_flux_sample(
                    "lower_edge_face",
                    col,
                    first_row - 1,
                    first_row,
                    reference_state,
                    candidate_state,
                    grid,
                    velocity_sign_floor_mps,
                    flux_delta_threshold_m3ps,
                )
            )
        if last_row > 0:
            samples.append(
                _lateral_face_flux_sample(
                    "upper_edge_face",
                    col,
                    last_row - 1,
                    last_row,
                    reference_state,
                    candidate_state,
                    grid,
                    velocity_sign_floor_mps,
                    flux_delta_threshold_m3ps,
                )
            )
    return tuple(samples)


def _lateral_face_flux_sample(
    face_role: str,
    col: int,
    south_row: int,
    north_row: int,
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    grid: dict[str, object],
    velocity_sign_floor_mps: float,
    flux_delta_threshold_m3ps: float,
) -> Milestone18ConstrictionLateralFaceFluxSample:
    face_width_m = float(grid["dx"])
    reference_south_h = float(reference_state["h"][south_row, col])
    reference_north_h = float(reference_state["h"][north_row, col])
    reference_south_v = float(reference_state["v"][south_row, col])
    reference_north_v = float(reference_state["v"][north_row, col])
    candidate_south_h = float(candidate_state["h"][south_row, col])
    candidate_north_h = float(candidate_state["h"][north_row, col])
    candidate_south_v = float(candidate_state["v"][south_row, col])
    candidate_north_v = float(candidate_state["v"][north_row, col])
    reference_mean_h = 0.5 * (reference_south_h + reference_north_h)
    candidate_mean_h = 0.5 * (candidate_south_h + candidate_north_h)
    reference_mean_v = 0.5 * (reference_south_v + reference_north_v)
    candidate_mean_v = 0.5 * (candidate_south_v + candidate_north_v)
    reference_flux = reference_mean_h * reference_mean_v * face_width_m
    candidate_flux = candidate_mean_h * candidate_mean_v * face_width_m
    flux_delta = candidate_flux - reference_flux
    reference_sign = _velocity_sign(reference_mean_v, velocity_sign_floor_mps)
    candidate_sign = _velocity_sign(candidate_mean_v, velocity_sign_floor_mps)
    sign_matches = reference_sign == 0 or candidate_sign == reference_sign
    x_m = float(grid["origin_x"]) + col * float(grid["dx"])
    y_face_m = float(grid["origin_y"]) + (0.5 * (south_row + north_row)) * float(grid["dy"])
    abs_flux_delta = abs(flux_delta)
    return Milestone18ConstrictionLateralFaceFluxSample(
        face_role=face_role,
        column_index=col,
        south_row_index=south_row,
        north_row_index=north_row,
        x_m=x_m,
        y_face_m=y_face_m,
        reference_mean_h=reference_mean_h,
        candidate_mean_h=candidate_mean_h,
        reference_mean_v=reference_mean_v,
        candidate_mean_v=candidate_mean_v,
        reference_lateral_volume_flux_m3ps=reference_flux,
        candidate_lateral_volume_flux_m3ps=candidate_flux,
        flux_delta_m3ps=flux_delta,
        abs_flux_delta_m3ps=abs_flux_delta,
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        ratio_to_threshold=_threshold_ratio(abs_flux_delta, flux_delta_threshold_m3ps),
        reference_sign=reference_sign,
        candidate_sign=candidate_sign,
        sign_matches=sign_matches,
        reference_south_h=reference_south_h,
        reference_south_v=reference_south_v,
        reference_north_h=reference_north_h,
        reference_north_v=reference_north_v,
        candidate_south_h=candidate_south_h,
        candidate_south_v=candidate_south_v,
        candidate_north_h=candidate_north_h,
        candidate_north_v=candidate_north_v,
    )


def _velocity_sign(value: float, floor: float) -> int:
    if value > floor:
        return 1
    if value < -floor:
        return -1
    return 0


def _constriction_lateral_face_edge_pair_summary(
    samples: tuple[Milestone18ConstrictionLateralFaceFluxSample, ...],
) -> tuple[dict[str, object], ...]:
    by_col: dict[int, dict[str, Milestone18ConstrictionLateralFaceFluxSample]] = {}
    for sample in samples:
        by_col.setdefault(sample.column_index, {})[sample.face_role] = sample
    pairs: list[dict[str, object]] = []
    for col, faces in sorted(by_col.items()):
        lower = faces.get("lower_edge_face")
        upper = faces.get("upper_edge_face")
        if lower is None or upper is None:
            continue
        reference_opposed = lower.reference_sign != 0 and upper.reference_sign != 0 and lower.reference_sign == -upper.reference_sign
        candidate_opposed = lower.candidate_sign != 0 and upper.candidate_sign != 0 and lower.candidate_sign == -upper.candidate_sign
        pairs.append(
            {
                "column_index": col,
                "lower_reference_sign": lower.reference_sign,
                "upper_reference_sign": upper.reference_sign,
                "lower_candidate_sign": lower.candidate_sign,
                "upper_candidate_sign": upper.candidate_sign,
                "reference_opposed_edges": reference_opposed,
                "candidate_opposed_edges": candidate_opposed,
                "matches_reference_opposition": (not reference_opposed) or candidate_opposed,
                "lower_abs_flux_delta_m3ps": lower.abs_flux_delta_m3ps,
                "upper_abs_flux_delta_m3ps": upper.abs_flux_delta_m3ps,
            }
        )
    return tuple(pairs)


def _lateral_face_flux_blocked_reasons(
    samples: tuple[Milestone18ConstrictionLateralFaceFluxSample, ...],
    edge_pair_summary: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if any(not sample.sign_matches for sample in samples):
        reasons.append("C++ upstream lateral face velocity signs do not match GeoClaw on one or more edge faces.")
    if any(sample.abs_flux_delta_m3ps > sample.flux_delta_threshold_m3ps for sample in samples):
        reasons.append("C++ upstream lateral face volume-flux proxy deltas exceed the diagnostic threshold.")
    if any(not pair.get("matches_reference_opposition", True) for pair in edge_pair_summary):
        reasons.append("GeoClaw shows opposite-signed lower/upper upstream edge faces that C++ does not reproduce.")
    return tuple(reasons)


def _lateral_face_flux_next_levers(
    samples: tuple[Milestone18ConstrictionLateralFaceFluxSample, ...],
    edge_pair_summary: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    if not samples:
        return ()
    worst = sorted(samples, key=lambda sample: (not sample.sign_matches, sample.ratio_to_threshold), reverse=True)[0]
    levers = [
        (
            f"Start with `{worst.face_role}` column {worst.column_index} rows "
            f"{worst.south_row_index}-{worst.north_row_index}; the GeoClaw/C++ lateral flux proxy differs by "
            f"{_format_number(worst.flux_delta_m3ps)} m3/s."
        ),
        "Instrument or reconstruct the actual finite-volume lateral face flux/source balance before adding another post-step velocity or depth transport.",
    ]
    if any(not pair.get("matches_reference_opposition", True) for pair in edge_pair_summary):
        levers.append(
            "Preserve GeoClaw's opposite-signed lower/upper upstream edge behavior; a single-sign lateral transport will keep damaging Froude shape."
        )
    return tuple(levers)


def _constriction_upstream_face_source_audit_samples(
    initial_state: dict[str, np.ndarray],
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    bed: np.ndarray,
    grid: dict[str, object],
    zones: dict[str, tuple[int, ...]],
    *,
    wet_depth_threshold_m: float,
    velocity_sign_floor_mps: float,
    flux_delta_threshold_m3ps: float,
    balance_delta_threshold_m3ps2: float,
) -> tuple[Milestone18ConstrictionFaceSourceAuditSample, ...]:
    samples: list[Milestone18ConstrictionFaceSourceAuditSample] = []
    upstream_columns = zones.get("upstream_approach", ())
    for col in upstream_columns:
        wet_rows = np.flatnonzero(initial_state["h"][:, col] > wet_depth_threshold_m)
        if wet_rows.size == 0:
            continue
        first_row = int(wet_rows[0])
        last_row = int(wet_rows[-1])
        if first_row > 0:
            samples.append(
                _face_source_audit_sample(
                    "lower_edge_face",
                    col,
                    first_row - 1,
                    first_row,
                    reference_state,
                    candidate_state,
                    bed,
                    grid,
                    velocity_sign_floor_mps,
                    flux_delta_threshold_m3ps,
                    balance_delta_threshold_m3ps2,
                )
            )
        if last_row > 0:
            samples.append(
                _face_source_audit_sample(
                    "upper_edge_face",
                    col,
                    last_row - 1,
                    last_row,
                    reference_state,
                    candidate_state,
                    bed,
                    grid,
                    velocity_sign_floor_mps,
                    flux_delta_threshold_m3ps,
                    balance_delta_threshold_m3ps2,
                )
            )
    return tuple(samples)


def _face_source_audit_sample(
    face_role: str,
    col: int,
    south_row: int,
    north_row: int,
    reference_state: dict[str, np.ndarray],
    candidate_state: dict[str, np.ndarray],
    bed: np.ndarray,
    grid: dict[str, object],
    velocity_sign_floor_mps: float,
    flux_delta_threshold_m3ps: float,
    balance_delta_threshold_m3ps2: float,
) -> Milestone18ConstrictionFaceSourceAuditSample:
    face_width_m = float(grid["dx"])
    g = 9.81
    reference = _face_source_terms(reference_state, bed, south_row, north_row, col, face_width_m, g)
    candidate = _face_source_terms(candidate_state, bed, south_row, north_row, col, face_width_m, g)
    volume_flux_delta = candidate["volume_flux"] - reference["volume_flux"]
    x_momentum_delta = candidate["x_momentum_flux"] - reference["x_momentum_flux"]
    normal_momentum_delta = candidate["normal_momentum_flux"] - reference["normal_momentum_flux"]
    bed_source_delta = candidate["bed_source"] - reference["bed_source"]
    balance_delta = candidate["balance"] - reference["balance"]
    reference_volume_sign = _velocity_sign(reference["mean_v"], velocity_sign_floor_mps)
    candidate_volume_sign = _velocity_sign(candidate["mean_v"], velocity_sign_floor_mps)
    reference_x_momentum_sign = _velocity_sign(reference["x_momentum_flux"], velocity_sign_floor_mps * face_width_m)
    candidate_x_momentum_sign = _velocity_sign(candidate["x_momentum_flux"], velocity_sign_floor_mps * face_width_m)
    x_m = float(grid["origin_x"]) + col * float(grid["dx"])
    y_face_m = float(grid["origin_y"]) + (0.5 * (south_row + north_row)) * float(grid["dy"])
    return Milestone18ConstrictionFaceSourceAuditSample(
        face_role=face_role,
        column_index=col,
        south_row_index=south_row,
        north_row_index=north_row,
        x_m=x_m,
        y_face_m=y_face_m,
        bed_step_m=reference["bed_step"],
        reference_eta_step_m=reference["eta_step"],
        candidate_eta_step_m=candidate["eta_step"],
        reference_mean_h=reference["mean_h"],
        candidate_mean_h=candidate["mean_h"],
        reference_mean_u=reference["mean_u"],
        candidate_mean_u=candidate["mean_u"],
        reference_mean_v=reference["mean_v"],
        candidate_mean_v=candidate["mean_v"],
        reference_volume_flux_m3ps=reference["volume_flux"],
        candidate_volume_flux_m3ps=candidate["volume_flux"],
        volume_flux_delta_m3ps=volume_flux_delta,
        abs_volume_flux_delta_m3ps=abs(volume_flux_delta),
        flux_delta_threshold_m3ps=flux_delta_threshold_m3ps,
        volume_ratio_to_threshold=_threshold_ratio(volume_flux_delta, flux_delta_threshold_m3ps),
        reference_volume_sign=reference_volume_sign,
        candidate_volume_sign=candidate_volume_sign,
        volume_sign_matches=reference_volume_sign == 0 or candidate_volume_sign == reference_volume_sign,
        reference_x_momentum_flux_proxy_m3ps2=reference["x_momentum_flux"],
        candidate_x_momentum_flux_proxy_m3ps2=candidate["x_momentum_flux"],
        x_momentum_flux_delta_m3ps2=x_momentum_delta,
        abs_x_momentum_flux_delta_m3ps2=abs(x_momentum_delta),
        reference_x_momentum_sign=reference_x_momentum_sign,
        candidate_x_momentum_sign=candidate_x_momentum_sign,
        x_momentum_sign_matches=reference_x_momentum_sign == 0
        or candidate_x_momentum_sign == reference_x_momentum_sign,
        reference_normal_momentum_flux_proxy_m3ps2=reference["normal_momentum_flux"],
        candidate_normal_momentum_flux_proxy_m3ps2=candidate["normal_momentum_flux"],
        normal_momentum_flux_delta_m3ps2=normal_momentum_delta,
        abs_normal_momentum_flux_delta_m3ps2=abs(normal_momentum_delta),
        reference_bed_source_proxy_m3ps2=reference["bed_source"],
        candidate_bed_source_proxy_m3ps2=candidate["bed_source"],
        bed_source_delta_m3ps2=bed_source_delta,
        abs_bed_source_delta_m3ps2=abs(bed_source_delta),
        reference_flux_source_balance_proxy_m3ps2=reference["balance"],
        candidate_flux_source_balance_proxy_m3ps2=candidate["balance"],
        balance_delta_m3ps2=balance_delta,
        abs_balance_delta_m3ps2=abs(balance_delta),
        balance_delta_threshold_m3ps2=balance_delta_threshold_m3ps2,
        balance_ratio_to_threshold=_threshold_ratio(balance_delta, balance_delta_threshold_m3ps2),
    )


def _face_source_terms(
    state: dict[str, np.ndarray],
    bed: np.ndarray,
    south_row: int,
    north_row: int,
    col: int,
    face_width_m: float,
    gravity_mps2: float,
) -> dict[str, float]:
    south_h = float(state["h"][south_row, col])
    north_h = float(state["h"][north_row, col])
    south_u = float(state["u"][south_row, col])
    north_u = float(state["u"][north_row, col])
    south_v = float(state["v"][south_row, col])
    north_v = float(state["v"][north_row, col])
    south_eta = float(state["eta"][south_row, col])
    north_eta = float(state["eta"][north_row, col])
    bed_step = float(bed[north_row, col] - bed[south_row, col])
    mean_h = 0.5 * (south_h + north_h)
    mean_u = 0.5 * (south_u + north_u)
    mean_v = 0.5 * (south_v + north_v)
    volume_flux = mean_h * mean_v * face_width_m
    x_momentum_flux = mean_h * mean_u * mean_v * face_width_m
    normal_momentum_flux = (mean_h * mean_v * mean_v + 0.5 * gravity_mps2 * mean_h * mean_h) * face_width_m
    bed_source = -gravity_mps2 * mean_h * bed_step * face_width_m
    return {
        "mean_h": mean_h,
        "mean_u": mean_u,
        "mean_v": mean_v,
        "eta_step": north_eta - south_eta,
        "bed_step": bed_step,
        "volume_flux": volume_flux,
        "x_momentum_flux": x_momentum_flux,
        "normal_momentum_flux": normal_momentum_flux,
        "bed_source": bed_source,
        "balance": normal_momentum_flux + bed_source,
    }


def _constriction_face_source_edge_pair_summary(
    samples: tuple[Milestone18ConstrictionFaceSourceAuditSample, ...],
) -> tuple[dict[str, object], ...]:
    by_col: dict[int, dict[str, Milestone18ConstrictionFaceSourceAuditSample]] = {}
    for sample in samples:
        by_col.setdefault(sample.column_index, {})[sample.face_role] = sample
    pairs: list[dict[str, object]] = []
    for col, faces in sorted(by_col.items()):
        lower = faces.get("lower_edge_face")
        upper = faces.get("upper_edge_face")
        if lower is None or upper is None:
            continue
        reference_opposed = (
            lower.reference_volume_sign != 0
            and upper.reference_volume_sign != 0
            and lower.reference_volume_sign == -upper.reference_volume_sign
        )
        candidate_opposed = (
            lower.candidate_volume_sign != 0
            and upper.candidate_volume_sign != 0
            and lower.candidate_volume_sign == -upper.candidate_volume_sign
        )
        pairs.append(
            {
                "column_index": col,
                "lower_reference_volume_sign": lower.reference_volume_sign,
                "upper_reference_volume_sign": upper.reference_volume_sign,
                "lower_candidate_volume_sign": lower.candidate_volume_sign,
                "upper_candidate_volume_sign": upper.candidate_volume_sign,
                "lower_reference_x_momentum_sign": lower.reference_x_momentum_sign,
                "upper_reference_x_momentum_sign": upper.reference_x_momentum_sign,
                "lower_candidate_x_momentum_sign": lower.candidate_x_momentum_sign,
                "upper_candidate_x_momentum_sign": upper.candidate_x_momentum_sign,
                "reference_opposed_edges": reference_opposed,
                "candidate_opposed_edges": candidate_opposed,
                "matches_reference_opposition": (not reference_opposed) or candidate_opposed,
                "lower_abs_volume_flux_delta_m3ps": lower.abs_volume_flux_delta_m3ps,
                "upper_abs_volume_flux_delta_m3ps": upper.abs_volume_flux_delta_m3ps,
                "lower_abs_balance_delta_m3ps2": lower.abs_balance_delta_m3ps2,
                "upper_abs_balance_delta_m3ps2": upper.abs_balance_delta_m3ps2,
            }
        )
    return tuple(pairs)


def _hydrostatic_source_decision_target_face(payload: dict[str, Any]) -> dict[str, object]:
    internal_samples = _records(payload, "cpp_internal_audit")
    if not internal_samples:
        return {}
    known_blockers = [
        sample
        for sample in internal_samples
        if sample.get("face_role") == "upper_edge_face"
        and sample.get("column_index") == 6
        and sample.get("south_row_index") == 8
        and sample.get("north_row_index") == 9
    ]
    candidates = known_blockers or [
        sample for sample in internal_samples if not bool(sample.get("post_left_sign_matches", True))
    ] or internal_samples
    target = sorted(
        candidates,
        key=lambda sample: abs(float(sample.get("post_left_flux_delta_m3ps", 0.0) or 0.0)),
        reverse=True,
    )[0]
    keep_keys = (
        "source_report",
        "face_role",
        "column_index",
        "south_row_index",
        "north_row_index",
        "time_s",
        "reference_volume_flux_m3ps",
        "base_flux_h_m3ps",
        "post_left_flux_h_m3ps",
        "post_left_flux_delta_m3ps",
        "reference_sign",
        "post_left_sign",
        "post_left_sign_matches",
        "hydro_left_source_hv_m3ps2",
        "hydro_right_source_hv_m3ps2",
        "constriction_source_split_left_hv_m3ps2",
        "constriction_source_split_right_hv_m3ps2",
        "constriction_left_source_h_m3ps",
        "constriction_right_source_h_m3ps",
        "south_cell_bed_slope_source_hv_per_s",
        "north_cell_bed_slope_source_hv_per_s",
        "hydrostatic_face_source_enabled",
        "constriction_hydrostatic_source_split_applied",
        "constriction_face_source_applied",
    )
    return {key: target[key] for key in keep_keys if key in target}


def _hydrostatic_source_decision_target_row(target: dict[str, object]) -> str:
    if not target:
        return "| none | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
    rows = f"{target.get('south_row_index', 'n/a')}-{target.get('north_row_index', 'n/a')}"
    cell_sources = (
        f"{_format_number(_float_or_none(target.get('south_cell_bed_slope_source_hv_per_s')))} / "
        f"{_format_number(_float_or_none(target.get('north_cell_bed_slope_source_hv_per_s')))}"
    )
    return (
        f"| `{_escape_table(str(target.get('face_role', 'unknown')))}` | "
        f"{target.get('column_index', 'n/a')} | {rows} | "
        f"{_format_number(_float_or_none(target.get('reference_volume_flux_m3ps')))} | "
        f"{_format_number(_float_or_none(target.get('base_flux_h_m3ps')))} | "
        f"{_format_number(_float_or_none(target.get('post_left_flux_h_m3ps')))} | "
        f"{_format_number(_float_or_none(target.get('post_left_flux_delta_m3ps')))} | "
        f"`{bool(target.get('hydrostatic_face_source_enabled'))}` | "
        f"`{bool(target.get('constriction_face_source_applied'))}` | {cell_sources} |"
    )


def _face_source_audit_blocked_reasons(
    samples: tuple[Milestone18ConstrictionFaceSourceAuditSample, ...],
    edge_pair_summary: tuple[dict[str, object], ...],
    cpp_internal_audit: tuple[dict[str, object], ...] = (),
) -> tuple[str, ...]:
    reasons: list[str] = []
    if any(not sample.volume_sign_matches for sample in samples):
        reasons.append("C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.")
    if any(not sample.x_momentum_sign_matches for sample in samples):
        reasons.append("C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.")
    if any(sample.abs_volume_flux_delta_m3ps > sample.flux_delta_threshold_m3ps for sample in samples):
        reasons.append("C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.")
    if any(sample.abs_balance_delta_m3ps2 > sample.balance_delta_threshold_m3ps2 for sample in samples):
        reasons.append("C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.")
    if any(not pair.get("matches_reference_opposition", True) for pair in edge_pair_summary):
        reasons.append("GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.")
    if any(not bool(sample.get("post_left_sign_matches", True)) for sample in cpp_internal_audit):
        reasons.append("C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.")
    if cpp_internal_audit and not any(bool(sample.get("hydrostatic_face_source_enabled")) for sample in cpp_internal_audit):
        reasons.append("C++ internal audit records hydrostatic y-face source terms as disabled for constriction faces.")
    return tuple(reasons)


def _face_source_audit_next_levers(
    samples: tuple[Milestone18ConstrictionFaceSourceAuditSample, ...],
    edge_pair_summary: tuple[dict[str, object], ...],
    cpp_internal_audit: tuple[dict[str, object], ...] = (),
) -> tuple[str, ...]:
    if not samples:
        return ()
    worst = sorted(
        samples,
        key=lambda sample: (
            not sample.volume_sign_matches,
            not sample.x_momentum_sign_matches,
            sample.volume_ratio_to_threshold,
            sample.balance_ratio_to_threshold,
        ),
        reverse=True,
    )[0]
    levers = [
        (
            f"Start with `{worst.face_role}` column {worst.column_index} rows "
            f"{worst.south_row_index}-{worst.north_row_index}; reconstructed q delta is "
            f"{_format_number(worst.volume_flux_delta_m3ps)} m3/s and balance delta is "
            f"{_format_number(worst.balance_delta_m3ps2)} m3/s2."
        ),
        "Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.",
        "Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.",
    ]
    if cpp_internal_audit:
        matching_internal = [
            sample
            for sample in cpp_internal_audit
            if sample.get("face_role") == worst.face_role
            and sample.get("column_index") == worst.column_index
            and sample.get("south_row_index") == worst.south_row_index
            and sample.get("north_row_index") == worst.north_row_index
        ]
        worst_internal = sorted(
            matching_internal or list(cpp_internal_audit),
            key=lambda sample: (
                not bool(sample.get("post_left_sign_matches", True)),
                abs(float(sample.get("post_left_flux_delta_m3ps", 0.0))),
            ),
            reverse=True,
        )[0]
        levers.append(
            "Use the exported C++ internal audit at "
            f"`{worst_internal.get('face_role')}` column {worst_internal.get('column_index')} rows "
            f"{worst_internal.get('south_row_index')}-{worst_internal.get('north_row_index')}; post-source q delta is "
            f"{_format_number(_float_or_none(worst_internal.get('post_left_flux_delta_m3ps')))} m3/s."
        )
        if not any(bool(sample.get("hydrostatic_face_source_enabled")) for sample in cpp_internal_audit):
            levers.append(
                "Decide whether constriction y-faces need hydrostatic reconstruction/source splitting instead of relying on cell-centered bed-slope source terms."
            )
    if any(not pair.get("matches_reference_opposition", True) for pair in edge_pair_summary):
        levers.append(
            "Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible."
        )
    return tuple(levers)


def _load_cpp_constriction_y_face_audit(
    cpp_manifest: dict[str, Any],
    manifest_dir: Path,
    reference_state: dict[str, np.ndarray],
    grid: dict[str, object],
    velocity_sign_floor_mps: float,
) -> tuple[dict[str, object], ...]:
    audit_path = _cpp_constriction_y_face_audit_path(cpp_manifest, manifest_dir)
    if audit_path is None or not audit_path.exists():
        return ()
    records: list[dict[str, object]] = []
    face_width_m = float(grid["dx"])
    with audit_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            face_role = str(row.get("face_role", ""))
            col = _int_from_csv(row, "column_index")
            south_row = _int_from_csv(row, "south_row_index")
            north_row = _int_from_csv(row, "north_row_index")
            if col is None or south_row is None or north_row is None:
                continue
            if not (0 <= south_row < reference_state["h"].shape[0] and 0 <= north_row < reference_state["h"].shape[0]):
                continue
            if not (0 <= col < reference_state["h"].shape[1]):
                continue
            reference_mean_h = 0.5 * (
                float(reference_state["h"][south_row, col]) + float(reference_state["h"][north_row, col])
            )
            reference_mean_v = 0.5 * (
                float(reference_state["v"][south_row, col]) + float(reference_state["v"][north_row, col])
            )
            reference_flux = reference_mean_h * reference_mean_v * face_width_m
            post_left_flux = _float_from_csv(row, "post_left_flux_h_m3ps")
            base_flux = _float_from_csv(row, "base_flux_h_m3ps")
            reference_sign = _velocity_sign(reference_mean_v, velocity_sign_floor_mps)
            post_sign = _velocity_sign(post_left_flux, velocity_sign_floor_mps * face_width_m)
            records.append(
                {
                    "source_report": str(audit_path),
                    "face_role": face_role,
                    "column_index": col,
                    "south_row_index": south_row,
                    "north_row_index": north_row,
                    "time_s": _float_from_csv(row, "time_s"),
                    "reference_volume_flux_m3ps": reference_flux,
                    "reference_sign": reference_sign,
                    "base_flux_h_m3ps": base_flux,
                    "post_left_flux_h_m3ps": post_left_flux,
                    "post_left_flux_delta_m3ps": post_left_flux - reference_flux,
                    "post_left_sign": post_sign,
                    "post_left_sign_matches": reference_sign == 0 or post_sign == reference_sign,
                    "face_state_south_h": _float_from_csv(row, "face_state_south_h"),
                    "face_state_south_u": _float_from_csv(row, "face_state_south_u"),
                    "face_state_south_v": _float_from_csv(row, "face_state_south_v"),
                    "face_state_north_h": _float_from_csv(row, "face_state_north_h"),
                    "face_state_north_u": _float_from_csv(row, "face_state_north_u"),
                    "face_state_north_v": _float_from_csv(row, "face_state_north_v"),
                    "hydro_left_source_hv_m3ps2": _float_from_csv(row, "hydro_left_source_hv_m3ps2"),
                    "hydro_right_source_hv_m3ps2": _float_from_csv(row, "hydro_right_source_hv_m3ps2"),
                    "constriction_source_split_left_hv_m3ps2": _float_from_csv(
                        row, "constriction_source_split_left_hv_m3ps2"
                    ),
                    "constriction_source_split_right_hv_m3ps2": _float_from_csv(
                        row, "constriction_source_split_right_hv_m3ps2"
                    ),
                    "constriction_left_source_h_m3ps": _float_from_csv(row, "constriction_left_source_h_m3ps"),
                    "constriction_right_source_h_m3ps": _float_from_csv(row, "constriction_right_source_h_m3ps"),
                    "south_cell_bed_slope_source_hv_per_s": _float_from_csv(
                        row, "south_cell_bed_slope_source_hv_per_s"
                    ),
                    "north_cell_bed_slope_source_hv_per_s": _float_from_csv(
                        row, "north_cell_bed_slope_source_hv_per_s"
                    ),
                    "constriction_face_state_reconstruction_applied": _bool_from_csv(
                        row, "constriction_face_state_reconstruction_applied"
                    ),
                    "hydrostatic_face_source_enabled": _bool_from_csv(row, "hydrostatic_face_source_enabled"),
                    "constriction_hydrostatic_source_split_applied": _bool_from_csv(
                        row, "constriction_hydrostatic_source_split_applied"
                    ),
                    "constriction_face_source_applied": _bool_from_csv(row, "constriction_face_source_applied"),
                }
            )
    return tuple(
        sorted(
            records,
            key=lambda sample: (
                not bool(sample.get("post_left_sign_matches", True)),
                abs(float(sample.get("post_left_flux_delta_m3ps", 0.0))),
            ),
            reverse=True,
        )
    )


def _cpp_constriction_y_face_audit_path(cpp_manifest: dict[str, Any], manifest_dir: Path) -> Path | None:
    audit = cpp_manifest.get("constriction_y_face_flux_source_audit")
    if isinstance(audit, dict):
        path = audit.get("path")
        if isinstance(path, str) and path:
            return _resolve_path(path, manifest_dir)
    diagnostics = cpp_manifest.get("diagnostics", [])
    if isinstance(diagnostics, list):
        for item in diagnostics:
            if isinstance(item, str) and "constriction_y_face_flux_source_audit" in item:
                return _resolve_path(item, manifest_dir)
    return None


def _float_from_csv(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0") or 0.0)
    except ValueError:
        return 0.0


def _int_from_csv(row: dict[str, str], key: str) -> int | None:
    try:
        return int(row.get(key, ""))
    except ValueError:
        return None


def _bool_from_csv(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() in {"1", "true", "yes"}


def _threshold_ratio(value: float, threshold: float) -> float:
    if threshold == 0.0:
        return float("inf") if value else 0.0
    return abs(value) / abs(threshold)


def _constriction_zone_for_column(column_index: int, zones: dict[str, tuple[int, ...]]) -> str | None:
    for zone_id, columns in zones.items():
        if column_index in columns:
            return zone_id
    return None


def _shape_sample_grid_row(sample: Milestone18ConstrictionShapeErrorSample) -> str:
    cell = "n/a"
    if sample.row_index is not None and sample.column_index is not None:
        cell = f"{sample.row_index},{sample.column_index}"
    return (
        "| "
        f"`{sample.category}` | "
        f"`{sample.field}` | "
        f"`{sample.frame_label or sample.source_id}` | "
        f"`{sample.zone_id or 'n/a'}` | "
        f"`{cell}` | "
        f"{_format_number(sample.x_m)} | "
        f"{_format_number(sample.y_m)} | "
        f"{_format_number(sample.reference_value)} | "
        f"{_format_number(sample.candidate_value)} | "
        f"{_format_number(sample.delta)} | "
        f"{sample.value:.6g} | "
        f"{sample.threshold:.6g} | "
        f"{sample.ratio_to_threshold:.6g} |"
    )


def _shape_sample_series_row(sample: Milestone18ConstrictionShapeErrorSample) -> str:
    return (
        "| "
        f"`{sample.category}` | "
        f"`{sample.source_id}` | "
        f"`{sample.field}` | "
        f"{_format_number(sample.time_s)} | "
        f"{_format_number(sample.distance_m)} | "
        f"{sample.value:.6g} | "
        f"{sample.threshold:.6g} | "
        f"{sample.ratio_to_threshold:.6g} |"
    )


def _probe_cross_section_sample_row(sample: Milestone18ConstrictionProbeCrossSectionSample) -> str:
    cell = "n/a"
    if sample.row_index is not None and sample.column_index is not None:
        cell = f"{sample.row_index},{sample.column_index}"
    reference_state = (
        f"{_format_number(sample.reference_h)}/"
        f"{_format_number(sample.reference_u)}/"
        f"{_format_number(sample.reference_v)}/"
        f"{_format_number(sample.reference_froude)}"
    )
    candidate_state = (
        f"{_format_number(sample.candidate_h)}/"
        f"{_format_number(sample.candidate_u)}/"
        f"{_format_number(sample.candidate_v)}/"
        f"{_format_number(sample.candidate_froude)}"
    )
    return (
        "| "
        f"`{sample.category}` | "
        f"`{sample.sample_id}` | "
        f"`{sample.field}` | "
        f"{_format_number(sample.time_s)} | "
        f"{_format_number(sample.distance_m)} | "
        f"`{sample.zone_id or 'n/a'}` | "
        f"`{cell}` | "
        f"{_format_number(sample.reference_value)} | "
        f"{_format_number(sample.candidate_value)} | "
        f"{_format_number(sample.delta)} | "
        f"{sample.value:.6g} | "
        f"`{reference_state}` | "
        f"`{candidate_state}` | "
        f"{sample.threshold:.6g} | "
        f"{sample.ratio_to_threshold:.6g} |"
    )


def _drop_ledge_zone_summary_row(summary: Milestone18DropLedgeZoneSummary) -> str:
    reference_state = (
        f"{_format_number(summary.reference_mean_h)}/"
        f"{_format_number(summary.reference_mean_eta)}/"
        f"{_format_number(summary.reference_mean_u)}/"
        f"{_format_number(summary.reference_mean_froude)}"
    )
    candidate_state = (
        f"{_format_number(summary.candidate_mean_h)}/"
        f"{_format_number(summary.candidate_mean_eta)}/"
        f"{_format_number(summary.candidate_mean_u)}/"
        f"{_format_number(summary.candidate_mean_froude)}"
    )
    delta_state = (
        f"{_format_number(summary.mean_h_delta)}/"
        f"{_format_number(summary.mean_eta_delta)}/"
        f"{_format_number(summary.mean_u_delta)}/"
        f"{_format_number(summary.mean_froude_delta)}"
    )
    wet_cells = f"{summary.reference_wet_cell_count}->{summary.candidate_wet_cell_count}"
    return (
        "| "
        f"`{summary.zone_id}` | "
        f"`{reference_state}` | "
        f"`{candidate_state}` | "
        f"`{delta_state}` | "
        f"`{wet_cells}` |"
    )


def _lateral_face_flux_sample_row(sample: Milestone18ConstrictionLateralFaceFluxSample) -> str:
    reference_state = (
        f"{_format_number(sample.reference_mean_h)}/"
        f"{_format_number(sample.reference_mean_v)}/"
        f"{_format_number(sample.reference_lateral_volume_flux_m3ps)}"
    )
    candidate_state = (
        f"{_format_number(sample.candidate_mean_h)}/"
        f"{_format_number(sample.candidate_mean_v)}/"
        f"{_format_number(sample.candidate_lateral_volume_flux_m3ps)}"
    )
    signs = f"{sample.reference_sign}->{sample.candidate_sign}"
    return (
        "| "
        f"`{sample.face_role}` | "
        f"{sample.column_index} | "
        f"`{sample.south_row_index}-{sample.north_row_index}` | "
        f"{_format_number(sample.x_m)} | "
        f"{_format_number(sample.y_face_m)} | "
        f"`{reference_state}` | "
        f"`{candidate_state}` | "
        f"{_format_number(sample.flux_delta_m3ps)} | "
        f"{_format_number(sample.flux_delta_threshold_m3ps)} | "
        f"{sample.ratio_to_threshold:.6g} | "
        f"`{signs}` |"
    )


def _lateral_face_flux_pair_row(pair: dict[str, object]) -> str:
    lower_signs = f"{pair.get('lower_reference_sign')}->{pair.get('lower_candidate_sign')}"
    upper_signs = f"{pair.get('upper_reference_sign')}->{pair.get('upper_candidate_sign')}"
    return (
        "| "
        f"{pair.get('column_index')} | "
        f"`{lower_signs}` | "
        f"`{upper_signs}` | "
        f"`{bool(pair.get('reference_opposed_edges'))}` | "
        f"`{bool(pair.get('candidate_opposed_edges'))}` | "
        f"`{bool(pair.get('matches_reference_opposition'))}` |"
    )


def _face_source_audit_sample_row(sample: Milestone18ConstrictionFaceSourceAuditSample) -> str:
    reference_state = (
        f"{_format_number(sample.reference_mean_h)}/"
        f"{_format_number(sample.reference_mean_u)}/"
        f"{_format_number(sample.reference_mean_v)}/"
        f"{_format_number(sample.reference_volume_flux_m3ps)}"
    )
    candidate_state = (
        f"{_format_number(sample.candidate_mean_h)}/"
        f"{_format_number(sample.candidate_mean_u)}/"
        f"{_format_number(sample.candidate_mean_v)}/"
        f"{_format_number(sample.candidate_volume_flux_m3ps)}"
    )
    x_momentum_signs = f"{sample.reference_x_momentum_sign}->{sample.candidate_x_momentum_sign}"
    balance = (
        f"{_format_number(sample.normal_momentum_flux_delta_m3ps2)}/"
        f"{_format_number(sample.bed_source_delta_m3ps2)}/"
        f"{_format_number(sample.balance_delta_m3ps2)}"
    )
    ratios = f"{sample.volume_ratio_to_threshold:.6g}/{sample.balance_ratio_to_threshold:.6g}"
    return (
        "| "
        f"`{sample.face_role}` | "
        f"{sample.column_index} | "
        f"`{sample.south_row_index}-{sample.north_row_index}` | "
        f"{_format_number(sample.x_m)} | "
        f"{_format_number(sample.y_face_m)} | "
        f"{_format_number(sample.bed_step_m)} | "
        f"`{reference_state}` | "
        f"`{candidate_state}` | "
        f"{_format_number(sample.volume_flux_delta_m3ps)} | "
        f"`{x_momentum_signs}` | "
        f"`{balance}` | "
        f"`{ratios}` |"
    )


def _face_source_audit_pair_row(pair: dict[str, object]) -> str:
    lower_signs = f"{pair.get('lower_reference_volume_sign')}->{pair.get('lower_candidate_volume_sign')}"
    upper_signs = f"{pair.get('upper_reference_volume_sign')}->{pair.get('upper_candidate_volume_sign')}"
    return (
        "| "
        f"{pair.get('column_index')} | "
        f"`{lower_signs}` | "
        f"`{upper_signs}` | "
        f"`{bool(pair.get('reference_opposed_edges'))}` | "
        f"`{bool(pair.get('candidate_opposed_edges'))}` | "
        f"`{bool(pair.get('matches_reference_opposition'))}` |"
    )


def _cpp_internal_face_audit_row(sample: dict[str, object]) -> str:
    rows = f"{sample.get('south_row_index')}-{sample.get('north_row_index')}"
    reference = (
        f"{_format_number(_float_or_none(sample.get('reference_volume_flux_m3ps')))}/"
        f"{sample.get('reference_sign')}"
    )
    post = (
        f"{_format_number(_float_or_none(sample.get('post_left_flux_h_m3ps')))}/"
        f"{sample.get('post_left_sign')}"
    )
    cell_sources = (
        f"{_format_number(_float_or_none(sample.get('south_cell_bed_slope_source_hv_per_s')))}/"
        f"{_format_number(_float_or_none(sample.get('north_cell_bed_slope_source_hv_per_s')))}"
    )
    return (
        "| "
        f"`{sample.get('face_role')}` | "
        f"{sample.get('column_index')} | "
        f"`{rows}` | "
        f"`{reference}` | "
        f"{_format_number(_float_or_none(sample.get('base_flux_h_m3ps')))} | "
        f"`{post}` | "
        f"{_format_number(_float_or_none(sample.get('post_left_flux_delta_m3ps')))} | "
        f"`{bool(sample.get('constriction_face_state_reconstruction_applied'))}` | "
        f"`{bool(sample.get('constriction_face_source_applied'))}` | "
        f"`{bool(sample.get('constriction_hydrostatic_source_split_applied'))}` | "
        f"`{bool(sample.get('hydrostatic_face_source_enabled'))}` | "
        f"`{cell_sources}` |"
    )


def _face_state_width_depth_sample_row(sample: dict[str, object]) -> str:
    rows = f"{sample.get('south_row_index')}-{sample.get('north_row_index')}"
    reference_state = (
        f"{_format_number(_float_or_none(sample.get('reference_mean_h')))}/"
        f"{_format_number(_float_or_none(sample.get('reference_mean_v')))}/"
        f"{_format_number(_float_or_none(sample.get('reference_volume_flux_m3ps')))}/"
        f"{sample.get('reference_volume_sign')}"
    )
    candidate_state = (
        f"{_format_number(_float_or_none(sample.get('candidate_mean_h')))}/"
        f"{_format_number(_float_or_none(sample.get('candidate_mean_v')))}/"
        f"{_format_number(_float_or_none(sample.get('candidate_volume_flux_m3ps')))}/"
        f"{sample.get('candidate_volume_sign')}"
    )
    width_bank = (
        f"{_format_number(_float_or_none(sample.get('wet_width_delta_cells')))}/"
        f"{_format_number(_float_or_none(sample.get('first_wet_row_delta_cells')))}/"
        f"{_format_number(_float_or_none(sample.get('last_wet_row_delta_cells')))}"
    )
    blockers = (
        f"face={bool(sample.get('face_state_blocked'))}, "
        f"width={bool(sample.get('width_mapping_blocked'))}, "
        f"bank={bool(sample.get('bank_alignment_blocked'))}, "
        f"depth={bool(sample.get('depth_mapping_blocked'))}"
    )
    return (
        "| "
        f"`{sample.get('face_role')}` | "
        f"{sample.get('column_index')} | "
        f"`{rows}` | "
        f"`{sample.get('zone_id') or 'n/a'}` | "
        f"`{reference_state}` | "
        f"`{candidate_state}` | "
        f"{_format_number(_float_or_none(sample.get('volume_flux_delta_m3ps')))} | "
        f"{_format_number(_float_or_none(sample.get('mean_depth_delta_m')))} | "
        f"`{width_bank}` | "
        f"`{blockers}` | "
        f"`{sample.get('recommended_solver_lever')}` |"
    )


def _face_state_width_depth_column_row(profile: dict[str, object]) -> str:
    authored = _wet_band_profile_markdown(profile.get("authored_initial"))
    reference = _wet_band_profile_markdown(profile.get("geoclaw_final"))
    candidate = _wet_band_profile_markdown(profile.get("cpp_final"))
    delta = profile.get("cpp_minus_geoclaw")
    delta_state = "n/a"
    if isinstance(delta, dict):
        delta_state = (
            f"{_format_number(_float_or_none(delta.get('wet_width_delta_cells')))}/"
            f"{_format_number(_float_or_none(delta.get('first_wet_row_delta_cells')))}/"
            f"{_format_number(_float_or_none(delta.get('last_wet_row_delta_cells')))}/"
            f"{_format_number(_float_or_none(delta.get('mean_wet_depth_delta_m')))}"
        )
    blockers = (
        f"width={bool(profile.get('width_mapping_blocked'))}, "
        f"bank={bool(profile.get('bank_alignment_blocked'))}, "
        f"depth={bool(profile.get('depth_mapping_blocked'))}"
    )
    return (
        "| "
        f"{profile.get('column_index')} | "
        f"`{profile.get('zone_id') or 'n/a'}` | "
        f"`{authored}` | "
        f"`{reference}` | "
        f"`{candidate}` | "
        f"`{delta_state}` | "
        f"`{blockers}` |"
    )


def _wet_band_profile_markdown(profile: object) -> str:
    if not isinstance(profile, dict):
        return "n/a"
    return (
        f"{profile.get('wet_width_cell_count')}/"
        f"{profile.get('first_wet_row')}-{profile.get('last_wet_row')}/"
        f"{_format_number(_float_or_none(profile.get('mean_wet_depth_m')))}"
    )


def _face_state_width_depth_pair_row(pair: dict[str, object]) -> str:
    lower_signs = f"{pair.get('lower_reference_volume_sign')}->{pair.get('lower_candidate_volume_sign')}"
    upper_signs = f"{pair.get('upper_reference_volume_sign')}->{pair.get('upper_candidate_volume_sign')}"
    return (
        "| "
        f"{pair.get('column_index')} | "
        f"`{lower_signs}` | "
        f"`{upper_signs}` | "
        f"`{bool(pair.get('reference_opposed_edges'))}` | "
        f"`{bool(pair.get('candidate_opposed_edges'))}` | "
        f"`{bool(pair.get('matches_reference_opposition'))}` |"
    )


def _markdown_counter_table(label: str, counts: object) -> str:
    if not isinstance(counts, dict) or not counts:
        return f"No {label.lower()} entries."
    lines = [f"| {label} | Entries |", "| --- | ---: |"]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
