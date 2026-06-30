"""Milestone 18 validation-closure triage artifacts."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .analytic_validation import AnalyticCandidateKind, AnalyticValidationReport, compare_analytic_fixture_manifest

MILESTONE18_FAILURE_TRIAGE_REPORT_SCHEMA = "raftsim.milestone18.failure_triage_matrix.v0"
MILESTONE18_ANALYTIC_GUARDRAIL_REPORT_SCHEMA = "raftsim.milestone18.analytic_retune_guardrail.v0"
MILESTONE18_PARITY_RETUNE_REPORT_SCHEMA = "raftsim.milestone18.parity_family_retune.v0"

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


def _markdown_counter_table(label: str, counts: object) -> str:
    if not isinstance(counts, dict) or not counts:
        return f"No {label.lower()} entries."
    lines = [f"| {label} | Entries |", "| --- | ---: |"]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
