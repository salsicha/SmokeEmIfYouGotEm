"""Comparison reports for reference and C++ 2.5D solver outputs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .scenario2_5d import read_scenario2_5d_package

FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]

FIELD_NAMES = ("h", "eta", "u", "v", "hu", "hv", "normal_x", "normal_y", "normal_z")
SLOPE_FIELD_NAMES = ("slope_x", "slope_y")
PROBE_FIELD_NAMES = ("h", "eta", "u", "v", "hu", "hv", "wet", "froude")
CROSS_SECTION_FIELD_NAMES = ("h", "eta", "u", "v", "froude")
VELOCITY_LIKE_FIELD_NAMES = frozenset({"u", "v", "froude"})
DEFAULT_VELOCITY_DEPTH_FLOOR = 0.15


@dataclass(frozen=True, slots=True)
class FieldErrorSummary:
    field: str
    l1: float
    l2: float
    linf: float
    reference_min: float
    reference_max: float
    candidate_min: float
    candidate_max: float
    sample_count: int
    compared_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "l1": self.l1,
            "l2": self.l2,
            "linf": self.linf,
            "reference_min": self.reference_min,
            "reference_max": self.reference_max,
            "candidate_min": self.candidate_min,
            "candidate_max": self.candidate_max,
            "sample_count": self.sample_count,
            "compared_count": self.compared_count,
        }


@dataclass(frozen=True, slots=True)
class FrameFieldComparison:
    label: str
    reference_frame: str
    cpp_frame: str
    field_errors: tuple[FieldErrorSummary, ...]
    slope_errors: tuple[FieldErrorSummary, ...]
    wet_mismatch_fraction: float
    reference_solver: str = "pyclaw"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "reference_solver": self.reference_solver,
            "reference_frame": self.reference_frame,
            "pyclaw_frame": self.reference_frame,
            "cpp_frame": self.cpp_frame,
            "field_errors": [summary.to_json_dict() for summary in self.field_errors],
            "slope_errors": [summary.to_json_dict() for summary in self.slope_errors],
            "wet_mismatch_fraction": self.wet_mismatch_fraction,
        }


@dataclass(frozen=True, slots=True)
class FieldComparisonReport:
    scenario_id: str
    frame_comparisons: tuple[FrameFieldComparison, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "frame_comparisons": [comparison.to_json_dict() for comparison in self.frame_comparisons],
            "aggregate_field_errors": [_aggregate.to_json_dict() for _aggregate in _aggregate_errors(self.frame_comparisons, "field")],
            "aggregate_slope_errors": [_aggregate.to_json_dict() for _aggregate in _aggregate_errors(self.frame_comparisons, "slope")],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class SeriesComparison:
    sample_id: str
    kind: str
    field_errors: tuple[FieldErrorSummary, ...]
    reference_sample_count: int
    candidate_sample_count: int
    max_time_delta: float
    max_distance_delta: float | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "kind": self.kind,
            "field_errors": [summary.to_json_dict() for summary in self.field_errors],
            "reference_sample_count": self.reference_sample_count,
            "candidate_sample_count": self.candidate_sample_count,
            "max_time_delta": self.max_time_delta,
            "max_distance_delta": self.max_distance_delta,
        }


@dataclass(frozen=True, slots=True)
class AggregateErrorSummary:
    field: str
    max_l1: float
    max_l2: float
    max_linf: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "max_l1": self.max_l1,
            "max_l2": self.max_l2,
            "max_linf": self.max_linf,
        }


@dataclass(frozen=True, slots=True)
class ProbeComparisonReport:
    scenario_id: str
    point_probes: tuple[SeriesComparison, ...]
    cross_sections: tuple[SeriesComparison, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "point_probes": [comparison.to_json_dict() for comparison in self.point_probes],
            "cross_sections": [comparison.to_json_dict() for comparison in self.cross_sections],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class PointMetric:
    x: float | None
    y: float | None
    value: float

    def to_json_dict(self) -> dict[str, object]:
        return {"x": self.x, "y": self.y, "value": self.value}


@dataclass(frozen=True, slots=True)
class HoleRetentionMetric:
    hole_count: int
    retained_area: float
    centroid_x: float | None
    centroid_y: float | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "hole_count": self.hole_count,
            "retained_area": self.retained_area,
            "centroid_x": self.centroid_x,
            "centroid_y": self.centroid_y,
        }


@dataclass(frozen=True, slots=True)
class SolverDiagnosticSummary:
    solver: str
    frame_count: int
    mass_initial: float
    mass_final: float
    mass_relative_drift: float
    energy_initial: float
    energy_final: float
    energy_relative_change: float
    froude_max: float
    froude_mean_wet: float
    hydraulic_jump: PointMetric
    wave_crest: PointMetric
    wave_trough: PointMetric
    hole_retention: HoleRetentionMetric

    def to_json_dict(self) -> dict[str, object]:
        return {
            "solver": self.solver,
            "frame_count": self.frame_count,
            "mass_initial": self.mass_initial,
            "mass_final": self.mass_final,
            "mass_relative_drift": self.mass_relative_drift,
            "energy_initial": self.energy_initial,
            "energy_final": self.energy_final,
            "energy_relative_change": self.energy_relative_change,
            "froude_max": self.froude_max,
            "froude_mean_wet": self.froude_mean_wet,
            "hydraulic_jump": self.hydraulic_jump.to_json_dict(),
            "wave_crest": self.wave_crest.to_json_dict(),
            "wave_trough": self.wave_trough.to_json_dict(),
            "hole_retention": self.hole_retention.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticDeltaSummary:
    mass_relative_drift_delta: float
    energy_relative_change_delta: float
    froude_max_delta: float
    froude_mean_wet_delta: float
    hydraulic_jump_distance: float | None
    wave_crest_distance: float | None
    wave_trough_distance: float | None
    hole_retained_area_delta: float
    hole_centroid_distance: float | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "mass_relative_drift_delta": self.mass_relative_drift_delta,
            "energy_relative_change_delta": self.energy_relative_change_delta,
            "froude_max_delta": self.froude_max_delta,
            "froude_mean_wet_delta": self.froude_mean_wet_delta,
            "hydraulic_jump_distance": self.hydraulic_jump_distance,
            "wave_crest_distance": self.wave_crest_distance,
            "wave_trough_distance": self.wave_trough_distance,
            "hole_retained_area_delta": self.hole_retained_area_delta,
            "hole_centroid_distance": self.hole_centroid_distance,
        }


@dataclass(frozen=True, slots=True)
class PhysicsDiagnosticComparisonReport:
    scenario_id: str
    pyclaw: SolverDiagnosticSummary
    cpp: SolverDiagnosticSummary
    delta: DiagnosticDeltaSummary
    reference_solver: str = "pyclaw"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "reference_solver": self.reference_solver,
            "reference": self.pyclaw.to_json_dict(),
            "pyclaw": self.pyclaw.to_json_dict(),
            "cpp": self.cpp.to_json_dict(),
            "delta": self.delta.to_json_dict(),
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class ObservedFeatureMetric:
    x: float
    y: float
    strength: float
    distance_to_authored: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "x": self.x,
            "y": self.y,
            "strength": self.strength,
            "distance_to_authored": self.distance_to_authored,
        }


@dataclass(frozen=True, slots=True)
class FeatureComparison:
    feature_index: int
    kind: str
    authored_x: float
    authored_y: float
    authored_strength: float
    pyclaw: ObservedFeatureMetric
    cpp: ObservedFeatureMetric
    location_delta: float
    strength_delta: float
    reference_solver: str = "pyclaw"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "feature_index": self.feature_index,
            "kind": self.kind,
            "authored_x": self.authored_x,
            "authored_y": self.authored_y,
            "authored_strength": self.authored_strength,
            "reference_solver": self.reference_solver,
            "reference": self.pyclaw.to_json_dict(),
            "pyclaw": self.pyclaw.to_json_dict(),
            "cpp": self.cpp.to_json_dict(),
            "location_delta": self.location_delta,
            "strength_delta": self.strength_delta,
        }


@dataclass(frozen=True, slots=True)
class FeatureComparisonReport:
    scenario_id: str
    feature_count: int
    comparisons: tuple[FeatureComparison, ...]
    max_location_delta: float
    max_abs_strength_delta: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "feature_count": self.feature_count,
            "comparisons": [comparison.to_json_dict() for comparison in self.comparisons],
            "max_location_delta": self.max_location_delta,
            "max_abs_strength_delta": self.max_abs_strength_delta,
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class ScenarioThresholds:
    max_field_linf: float = 0.25
    max_slope_linf: float = 0.25
    max_wet_mismatch_fraction: float = 0.02
    max_probe_linf: float = 0.25
    max_cross_section_linf: float = 0.25
    max_mass_drift_delta: float = 0.05
    max_energy_change_delta: float = 0.25
    max_froude_delta: float = 0.5
    max_feature_location_delta: float = 5.0
    max_feature_strength_delta: float = 10.0
    velocity_depth_floor: float = DEFAULT_VELOCITY_DEPTH_FLOOR

    def to_json_dict(self) -> dict[str, object]:
        return {
            "max_field_linf": self.max_field_linf,
            "max_slope_linf": self.max_slope_linf,
            "max_wet_mismatch_fraction": self.max_wet_mismatch_fraction,
            "max_probe_linf": self.max_probe_linf,
            "max_cross_section_linf": self.max_cross_section_linf,
            "max_mass_drift_delta": self.max_mass_drift_delta,
            "max_energy_change_delta": self.max_energy_change_delta,
            "max_froude_delta": self.max_froude_delta,
            "max_feature_location_delta": self.max_feature_location_delta,
            "max_feature_strength_delta": self.max_feature_strength_delta,
            "velocity_depth_floor": self.velocity_depth_floor,
        }


@dataclass(frozen=True, slots=True)
class ThresholdCheck:
    name: str
    passed: bool
    value: float
    threshold: float
    details: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ThresholdEvaluationReport:
    scenario_id: str
    passed: bool
    thresholds: ScenarioThresholds
    checks: tuple[ThresholdCheck, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "thresholds": self.thresholds.to_json_dict(),
            "checks": [check.to_json_dict() for check in self.checks],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


@dataclass(frozen=True, slots=True)
class ReferenceSolverEntry:
    solver: str
    output_dir: Path
    manifest_path: Path


def compare_dual_solver_fields(
    dual_solver_dir_or_manifest: str | Path,
    *,
    velocity_depth_floor: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    output_path: str | Path | None = None,
) -> FieldComparisonReport:
    """Compare matching initial/final field frames from a dual-solver run."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(root / manifest["scenario_package"])
    reference = _reference_solver_entry(manifest, root)
    reference_manifest = _load_manifest(reference.manifest_path)
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])

    reference_frames = [reference.output_dir / frame for frame in reference_manifest["frames"]]
    cpp_frames = [root / manifest["cpp"]["output_dir"] / frame for frame in cpp_manifest["frames"]]
    pairings = _frame_pairings(reference_frames, cpp_frames)

    comparisons = tuple(
        _compare_frame_pair(
            label,
            reference_frame_path,
            cpp_frame_path,
            scenario.grid.dx,
            scenario.grid.dy,
            reference_solver=reference.solver,
            velocity_depth_floor=velocity_depth_floor,
        )
        for label, reference_frame_path, cpp_frame_path in pairings
    )
    report = FieldComparisonReport(scenario_id=manifest["scenario_id"], frame_comparisons=comparisons)
    if output_path is not None:
        report.write_json(output_path)
    return report


def compare_dual_solver_probes(
    dual_solver_dir_or_manifest: str | Path,
    *,
    velocity_depth_floor: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    output_path: str | Path | None = None,
) -> ProbeComparisonReport:
    """Compare point probe time series and cross sections from a dual-solver run."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reference = _reference_solver_entry(manifest, root)
    reference_manifest = _load_manifest(reference.manifest_path)
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])
    reference_output = reference.output_dir
    cpp_output = root / manifest["cpp"]["output_dir"]

    point_probes = tuple(
        _compare_probe_pair(probe_id, reference_path, cpp_path, velocity_depth_floor=velocity_depth_floor)
        for probe_id, reference_path, cpp_path in _matched_files(
            reference_output,
            reference_manifest["probes"],
            cpp_output,
            cpp_manifest["probes"],
        )
    )
    cross_sections = tuple(
        _compare_cross_section_pair(probe_id, reference_path, cpp_path, velocity_depth_floor=velocity_depth_floor)
        for probe_id, reference_path, cpp_path in _matched_files(
            reference_output,
            reference_manifest["cross_sections"],
            cpp_output,
            cpp_manifest["cross_sections"],
        )
    )
    report = ProbeComparisonReport(
        scenario_id=manifest["scenario_id"],
        point_probes=point_probes,
        cross_sections=cross_sections,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def compare_dual_solver_diagnostics(
    dual_solver_dir_or_manifest: str | Path,
    *,
    velocity_depth_floor: float = DEFAULT_VELOCITY_DEPTH_FLOOR,
    output_path: str | Path | None = None,
) -> PhysicsDiagnosticComparisonReport:
    """Compare mass, energy, Froude, jump, wave, and hole-retention diagnostics."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(root / manifest["scenario_package"])
    reference = _reference_solver_entry(manifest, root)
    reference_manifest = _load_manifest(reference.manifest_path)
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])
    reference_output = reference.output_dir
    cpp_output = root / manifest["cpp"]["output_dir"]
    reference_frames = [_load_reference_npz_frame(reference_output / frame) for frame in reference_manifest["frames"]]
    cpp_frames = [_load_cpp_csv_frame(cpp_output / frame) for frame in cpp_manifest["frames"]]

    reference_summary = _diagnostic_summary(reference.solver, reference_frames, scenario, velocity_depth_floor=velocity_depth_floor)
    cpp_summary = _diagnostic_summary("cpp", cpp_frames, scenario, velocity_depth_floor=velocity_depth_floor)
    report = PhysicsDiagnosticComparisonReport(
        scenario_id=manifest["scenario_id"],
        pyclaw=reference_summary,
        cpp=cpp_summary,
        delta=_diagnostic_delta(reference_summary, cpp_summary),
        reference_solver=reference.solver,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def compare_dual_solver_features(
    dual_solver_dir_or_manifest: str | Path,
    *,
    output_path: str | Path | None = None,
) -> FeatureComparisonReport:
    """Compare feature-local response locations and strengths."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(root / manifest["scenario_package"])
    reference = _reference_solver_entry(manifest, root)
    reference_manifest = _load_manifest(reference.manifest_path)
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])
    reference_output = reference.output_dir
    cpp_output = root / manifest["cpp"]["output_dir"]
    reference_final = _load_reference_npz_frame(reference_output / reference_manifest["frames"][-1])
    cpp_final = _load_cpp_csv_frame(cpp_output / cpp_manifest["frames"][-1])

    comparisons = tuple(
        _compare_feature(index, feature, reference_final, cpp_final, scenario, reference_solver=reference.solver)
        for index, feature in enumerate(scenario.features)
    )
    report = FeatureComparisonReport(
        scenario_id=manifest["scenario_id"],
        feature_count=len(scenario.features),
        comparisons=comparisons,
        max_location_delta=max((comparison.location_delta for comparison in comparisons), default=0.0),
        max_abs_strength_delta=max((abs(comparison.strength_delta) for comparison in comparisons), default=0.0),
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def evaluate_dual_solver_thresholds(
    dual_solver_dir_or_manifest: str | Path,
    *,
    thresholds: ScenarioThresholds | None = None,
    output_path: str | Path | None = None,
) -> ThresholdEvaluationReport:
    """Evaluate one dual-solver scenario against explicit pass/fail thresholds."""

    limits = thresholds or ScenarioThresholds()
    field_report = compare_dual_solver_fields(
        dual_solver_dir_or_manifest,
        velocity_depth_floor=limits.velocity_depth_floor,
    )
    probe_report = compare_dual_solver_probes(
        dual_solver_dir_or_manifest,
        velocity_depth_floor=limits.velocity_depth_floor,
    )
    diagnostic_report = compare_dual_solver_diagnostics(
        dual_solver_dir_or_manifest,
        velocity_depth_floor=limits.velocity_depth_floor,
    )
    feature_report = compare_dual_solver_features(dual_solver_dir_or_manifest)
    checks = (
        _threshold_check(
            "field_linf",
            _max_linf(field_report.frame_comparisons, "field"),
            limits.max_field_linf,
            f"Max Linf across h/eta/u/v/hu/hv/normals; u/v masked below {limits.velocity_depth_floor:g} m.",
        ),
        _threshold_check(
            "slope_linf",
            _max_linf(field_report.frame_comparisons, "slope"),
            limits.max_slope_linf,
            "Max Linf across eta slope fields.",
        ),
        _threshold_check(
            "wet_mismatch_fraction",
            max((comparison.wet_mismatch_fraction for comparison in field_report.frame_comparisons), default=0.0),
            limits.max_wet_mismatch_fraction,
            f"Max material wet/dry mask mismatch fraction across compared frames using h >= {limits.velocity_depth_floor:g} m.",
        ),
        _threshold_check(
            "probe_linf",
            _max_series_linf(probe_report.point_probes),
            limits.max_probe_linf,
            f"Max Linf across point-probe fields; u/v/Froude masked below {limits.velocity_depth_floor:g} m.",
        ),
        _threshold_check(
            "cross_section_linf",
            _max_series_linf(probe_report.cross_sections),
            limits.max_cross_section_linf,
            f"Max Linf across cross-section fields; u/v/Froude masked below {limits.velocity_depth_floor:g} m.",
        ),
        _threshold_check(
            "mass_drift_delta",
            abs(diagnostic_report.delta.mass_relative_drift_delta),
            limits.max_mass_drift_delta,
            "Absolute C++ minus reference mass-drift delta.",
        ),
        _threshold_check(
            "energy_change_delta",
            abs(diagnostic_report.delta.energy_relative_change_delta),
            limits.max_energy_change_delta,
            "Absolute C++ minus reference energy-change delta.",
        ),
        _threshold_check(
            "froude_delta",
            max(abs(diagnostic_report.delta.froude_max_delta), abs(diagnostic_report.delta.froude_mean_wet_delta)),
            limits.max_froude_delta,
            f"Max absolute Froude summary delta for cells at or above {limits.velocity_depth_floor:g} m.",
        ),
        _threshold_check(
            "feature_location_delta",
            feature_report.max_location_delta,
            limits.max_feature_location_delta,
            "Max observed feature response location delta.",
        ),
        _threshold_check(
            "feature_strength_delta",
            feature_report.max_abs_strength_delta,
            limits.max_feature_strength_delta,
            "Max observed feature response strength delta.",
        ),
    )
    report = ThresholdEvaluationReport(
        scenario_id=field_report.scenario_id,
        passed=all(check.passed for check in checks),
        thresholds=limits,
        checks=checks,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def _manifest_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.name == "dual_solver_manifest.json":
        return candidate
    return candidate / "dual_solver_manifest.json"


def _load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _reference_solver_entry(manifest: dict[str, object], root: Path) -> ReferenceSolverEntry:
    for solver in ("geoclaw", "reference", "pyclaw"):
        if solver not in manifest:
            continue
        entry = manifest[solver]
        if not isinstance(entry, dict):
            raise ValueError(f"{solver} manifest entry must be an object.")
        solver_name = str(entry.get("solver", "geoclaw" if solver == "reference" else solver))
        return ReferenceSolverEntry(
            solver=solver_name,
            output_dir=root / str(entry["output_dir"]),
            manifest_path=root / str(entry["manifest"]),
        )
    raise ValueError("Comparison manifest must include a geoclaw, reference, or pyclaw entry.")


def _matched_files(
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


def _aggregate_errors(
    frame_comparisons: tuple[FrameFieldComparison, ...],
    kind: str,
) -> tuple[AggregateErrorSummary, ...]:
    by_field: dict[str, list[FieldErrorSummary]] = {}
    for comparison in frame_comparisons:
        summaries = comparison.field_errors if kind == "field" else comparison.slope_errors
        for summary in summaries:
            by_field.setdefault(summary.field, []).append(summary)
    return tuple(
        AggregateErrorSummary(
            field=field,
            max_l1=max(summary.l1 for summary in summaries),
            max_l2=max(summary.l2 for summary in summaries),
            max_linf=max(summary.linf for summary in summaries),
        )
        for field, summaries in sorted(by_field.items())
    )


def _frame_pairings(pyclaw_frames: list[Path], cpp_frames: list[Path]) -> tuple[tuple[str, Path, Path], ...]:
    if not pyclaw_frames or not cpp_frames:
        raise ValueError("Both solver outputs must contain at least one frame.")
    if len(pyclaw_frames) == 1 or len(cpp_frames) == 1:
        return (("initial", pyclaw_frames[0], cpp_frames[0]),)
    return (
        ("initial", pyclaw_frames[0], cpp_frames[0]),
        ("final", pyclaw_frames[-1], cpp_frames[-1]),
    )


def _compare_frame_pair(
    label: str,
    reference_frame_path: Path,
    cpp_frame_path: Path,
    dx: float,
    dy: float,
    *,
    reference_solver: str,
    velocity_depth_floor: float,
) -> FrameFieldComparison:
    reference_frame = _load_reference_npz_frame(reference_frame_path)
    cpp_frame = _load_cpp_csv_frame(cpp_frame_path)
    velocity_mask = _velocity_comparison_mask(reference_frame["h"], cpp_frame["h"], velocity_depth_floor)
    field_errors = tuple(
        _field_error(
            name,
            reference_frame[name],
            cpp_frame[name],
            mask=velocity_mask if name in VELOCITY_LIKE_FIELD_NAMES else None,
        )
        for name in FIELD_NAMES
    )
    reference_slopes = _slopes_from_eta(reference_frame["eta"], dx, dy)
    cpp_slopes = _slopes_from_eta(cpp_frame["eta"], dx, dy)
    slope_errors = tuple(
        _field_error(name, reference_slopes[index], cpp_slopes[index])
        for index, name in enumerate(SLOPE_FIELD_NAMES)
    )
    reference_material_wet = _material_wet_mask(reference_frame["h"], velocity_depth_floor)
    cpp_material_wet = _material_wet_mask(cpp_frame["h"], velocity_depth_floor)
    wet_mismatch = float(np.mean(reference_material_wet != cpp_material_wet))
    return FrameFieldComparison(
        label=label,
        reference_frame=str(reference_frame_path),
        cpp_frame=str(cpp_frame_path),
        field_errors=field_errors,
        slope_errors=slope_errors,
        wet_mismatch_fraction=wet_mismatch,
        reference_solver=reference_solver,
    )


def _load_reference_npz_frame(path: Path) -> dict[str, FloatGrid | BoolGrid]:
    with np.load(path) as data:
        return {
            "h": np.asarray(data["h"], dtype=np.float64),
            "eta": np.asarray(data["eta"], dtype=np.float64),
            "u": np.asarray(data["u"], dtype=np.float64),
            "v": np.asarray(data["v"], dtype=np.float64),
            "hu": np.asarray(data["hu"], dtype=np.float64),
            "hv": np.asarray(data["hv"], dtype=np.float64),
            "wet": np.asarray(data["wet"], dtype=np.bool_),
            "normal_x": np.asarray(data["normal_x"], dtype=np.float64),
            "normal_y": np.asarray(data["normal_y"], dtype=np.float64),
            "normal_z": np.asarray(data["normal_z"], dtype=np.float64),
            "froude": np.asarray(data["froude"], dtype=np.float64),
        }


def _material_wet_mask(depth: FloatGrid | BoolGrid, depth_floor: float) -> BoolGrid:
    return np.asarray(depth, dtype=np.float64) >= depth_floor


def _load_pyclaw_npz_frame(path: Path) -> dict[str, FloatGrid | BoolGrid]:
    return _load_reference_npz_frame(path)


def _load_cpp_csv_frame(path: Path) -> dict[str, FloatGrid | BoolGrid]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    if not rows:
        raise ValueError(f"C++ frame is empty: {path}")
    ny = max(int(row["row"]) for row in rows) + 1
    nx = max(int(row["col"]) for row in rows) + 1
    frame: dict[str, FloatGrid | BoolGrid] = {
        "h": np.zeros((ny, nx), dtype=np.float64),
        "eta": np.zeros((ny, nx), dtype=np.float64),
        "u": np.zeros((ny, nx), dtype=np.float64),
        "v": np.zeros((ny, nx), dtype=np.float64),
        "hu": np.zeros((ny, nx), dtype=np.float64),
        "hv": np.zeros((ny, nx), dtype=np.float64),
        "wet": np.zeros((ny, nx), dtype=np.bool_),
        "normal_x": np.zeros((ny, nx), dtype=np.float64),
        "normal_y": np.zeros((ny, nx), dtype=np.float64),
        "normal_z": np.zeros((ny, nx), dtype=np.float64),
        "froude": np.zeros((ny, nx), dtype=np.float64),
    }
    for row in rows:
        row_index = int(row["row"])
        col_index = int(row["col"])
        for name, array in frame.items():
            if name == "wet":
                array[row_index, col_index] = bool(int(row[name]))  # type: ignore[index]
            else:
                array[row_index, col_index] = float(row[name])  # type: ignore[index]
    return frame


def _field_error(
    field_name: str,
    reference: FloatGrid | BoolGrid,
    candidate: FloatGrid | BoolGrid,
    *,
    mask: BoolGrid | None = None,
) -> FieldErrorSummary:
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    if ref.shape != cand.shape:
        raise ValueError(f"Shape mismatch for {field_name}: reference={ref.shape} C++={cand.shape}")
    sample_count = int(ref.size)
    if mask is None:
        ref_compared = ref
        cand_compared = cand
    else:
        mask_grid = np.asarray(mask, dtype=np.bool_)
        if mask_grid.shape != ref.shape:
            raise ValueError(f"Mask shape mismatch for {field_name}: mask={mask_grid.shape} field={ref.shape}")
        ref_compared = ref[mask_grid]
        cand_compared = cand[mask_grid]

    compared_count = int(ref_compared.size)
    if compared_count == 0:
        l1 = 0.0
        l2 = 0.0
        linf = 0.0
        ref_min = float(np.min(ref)) if sample_count else 0.0
        ref_max = float(np.max(ref)) if sample_count else 0.0
        cand_min = float(np.min(cand)) if sample_count else 0.0
        cand_max = float(np.max(cand)) if sample_count else 0.0
    else:
        delta = cand_compared - ref_compared
        l1 = float(np.mean(np.abs(delta)))
        l2 = float(np.sqrt(np.mean(delta**2)))
        linf = float(np.max(np.abs(delta)))
        ref_min = float(np.min(ref_compared))
        ref_max = float(np.max(ref_compared))
        cand_min = float(np.min(cand_compared))
        cand_max = float(np.max(cand_compared))
    return FieldErrorSummary(
        field=field_name,
        l1=l1,
        l2=l2,
        linf=linf,
        reference_min=ref_min,
        reference_max=ref_max,
        candidate_min=cand_min,
        candidate_max=cand_max,
        sample_count=sample_count,
        compared_count=compared_count,
    )


def _slopes_from_eta(eta: FloatGrid, dx: float, dy: float) -> tuple[FloatGrid, FloatGrid]:
    slope_y, slope_x = np.gradient(np.asarray(eta, dtype=np.float64), dy, dx)
    return slope_x, slope_y


def _velocity_comparison_mask(
    reference_h: FloatGrid | BoolGrid,
    candidate_h: FloatGrid | BoolGrid,
    depth_floor: float,
) -> BoolGrid:
    ref_h = np.asarray(reference_h, dtype=np.float64)
    cand_h = np.asarray(candidate_h, dtype=np.float64)
    if ref_h.shape != cand_h.shape:
        raise ValueError(f"Depth mask shape mismatch: reference={ref_h.shape} C++={cand_h.shape}")
    return (ref_h >= depth_floor) & (cand_h >= depth_floor)


def _compare_probe_pair(
    probe_id: str,
    pyclaw_path: Path,
    cpp_path: Path,
    *,
    velocity_depth_floor: float,
) -> SeriesComparison:
    reference = _load_probe_csv(pyclaw_path)
    candidate = _load_probe_csv(cpp_path)
    ref_times = reference["time"]
    cand_times = candidate["time"]
    indices, max_time_delta = _nearest_indices(ref_times, cand_times)
    aligned_candidate = {
        field: candidate[field][indices]
        for field in candidate
        if field != "time"
    }
    velocity_mask = _velocity_comparison_mask(
        reference["h"],
        aligned_candidate["h"],
        velocity_depth_floor,
    )
    field_errors = tuple(
        _field_error(
            field,
            reference[field],
            aligned_candidate[field],
            mask=velocity_mask if field in VELOCITY_LIKE_FIELD_NAMES else None,
        )
        for field in PROBE_FIELD_NAMES
        if field in reference and field in aligned_candidate
    )
    return SeriesComparison(
        sample_id=probe_id,
        kind="point",
        field_errors=field_errors,
        reference_sample_count=len(ref_times),
        candidate_sample_count=len(cand_times),
        max_time_delta=max_time_delta,
    )


def _compare_cross_section_pair(
    probe_id: str,
    pyclaw_path: Path,
    cpp_path: Path,
    *,
    velocity_depth_floor: float,
) -> SeriesComparison:
    reference = _load_pyclaw_cross_section_npz(pyclaw_path)
    candidate = _load_cpp_cross_section_csv(cpp_path)
    time_indices, max_time_delta = _nearest_indices(reference["times"], candidate["times"])
    distance_indices, max_distance_delta = _nearest_indices(reference["distance"], candidate["distance"])
    aligned_candidate = {
        field: candidate[field][np.ix_(time_indices, distance_indices)]
        for field in CROSS_SECTION_FIELD_NAMES
    }
    velocity_mask = _velocity_comparison_mask(
        reference["h"],
        aligned_candidate["h"],
        velocity_depth_floor,
    )
    field_errors = tuple(
        _field_error(
            field,
            reference[field],
            aligned_candidate[field],
            mask=velocity_mask if field in VELOCITY_LIKE_FIELD_NAMES else None,
        )
        for field in CROSS_SECTION_FIELD_NAMES
    )
    return SeriesComparison(
        sample_id=probe_id,
        kind="cross_section",
        field_errors=field_errors,
        reference_sample_count=int(reference["times"].size * reference["distance"].size),
        candidate_sample_count=int(candidate["times"].size * candidate["distance"].size),
        max_time_delta=max_time_delta,
        max_distance_delta=max_distance_delta,
    )


def _load_probe_csv(path: Path) -> dict[str, FloatGrid]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    if not rows:
        raise ValueError(f"Probe CSV is empty: {path}")
    columns = rows[0].keys()
    return {column: np.asarray([float(row[column]) for row in rows], dtype=np.float64) for column in columns}


def _load_pyclaw_cross_section_npz(path: Path) -> dict[str, FloatGrid]:
    with np.load(path) as data:
        return {
            "times": np.asarray(data["times"], dtype=np.float64),
            "distance": np.asarray(data["distance"], dtype=np.float64),
            "h": np.asarray(data["h"], dtype=np.float64),
            "eta": np.asarray(data["eta"], dtype=np.float64),
            "u": np.asarray(data["u"], dtype=np.float64),
            "v": np.asarray(data["v"], dtype=np.float64),
            "froude": np.asarray(data["froude"], dtype=np.float64),
        }


def _load_cpp_cross_section_csv(path: Path) -> dict[str, FloatGrid]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    if not rows:
        raise ValueError(f"Cross-section CSV is empty: {path}")
    times = np.asarray(sorted({float(row["time"]) for row in rows}), dtype=np.float64)
    distances = np.asarray(sorted({float(row["distance"]) for row in rows}), dtype=np.float64)
    time_index = {value: index for index, value in enumerate(times)}
    distance_index = {value: index for index, value in enumerate(distances)}
    result: dict[str, FloatGrid] = {
        "times": times,
        "distance": distances,
    }
    for field in CROSS_SECTION_FIELD_NAMES:
        result[field] = np.zeros((len(times), len(distances)), dtype=np.float64)
    for row in rows:
        t = time_index[float(row["time"])]
        d = distance_index[float(row["distance"])]
        for field in CROSS_SECTION_FIELD_NAMES:
            result[field][t, d] = float(row[field])
    return result


def _nearest_indices(reference: FloatGrid, candidate: FloatGrid) -> tuple[NDArray[np.int64], float]:
    if reference.size == 0 or candidate.size == 0:
        raise ValueError("Cannot align empty sample arrays.")
    indices = np.zeros(reference.shape, dtype=np.int64)
    max_delta = 0.0
    for index, value in np.ndenumerate(reference):
        nearest = int(np.argmin(np.abs(candidate - value)))
        indices[index] = nearest
        max_delta = max(max_delta, float(abs(candidate[nearest] - value)))
    return indices, max_delta


def _diagnostic_summary(
    solver: str,
    frames: list[dict[str, FloatGrid | BoolGrid]],
    scenario,
    *,
    velocity_depth_floor: float,
) -> SolverDiagnosticSummary:
    if not frames:
        raise ValueError("Diagnostic comparison requires at least one frame.")
    initial = frames[0]
    final = frames[-1]
    final_h = np.asarray(final["h"], dtype=np.float64)
    mass_initial = _frame_mass(initial, scenario.grid.dx, scenario.grid.dy)
    mass_final = _frame_mass(final, scenario.grid.dx, scenario.grid.dy)
    energy_initial = _frame_energy(initial, scenario.grid.dx, scenario.grid.dy)
    energy_final = _frame_energy(final, scenario.grid.dx, scenario.grid.dy)
    final_wet = np.asarray(final["wet"], dtype=np.bool_)
    final_froude = np.asarray(final["froude"], dtype=np.float64)
    compared_froude_mask = final_wet & (final_h >= velocity_depth_floor)
    wet_froude = final_froude[compared_froude_mask]
    return SolverDiagnosticSummary(
        solver=solver,
        frame_count=len(frames),
        mass_initial=mass_initial,
        mass_final=mass_final,
        mass_relative_drift=abs(mass_final - mass_initial) / max(abs(mass_initial), 1.0),
        energy_initial=energy_initial,
        energy_final=energy_final,
        energy_relative_change=(energy_final - energy_initial) / max(abs(energy_initial), 1.0),
        froude_max=float(np.max(wet_froude)) if wet_froude.size else 0.0,
        froude_mean_wet=float(np.mean(wet_froude)) if wet_froude.size else 0.0,
        hydraulic_jump=_hydraulic_jump_metric(final, scenario),
        wave_crest=_wave_extreme_metric(final, scenario, mode="crest"),
        wave_trough=_wave_extreme_metric(final, scenario, mode="trough"),
        hole_retention=_hole_retention_metric(final, scenario),
    )


def _frame_mass(frame: dict[str, FloatGrid | BoolGrid], dx: float, dy: float) -> float:
    return float(np.sum(np.asarray(frame["h"], dtype=np.float64)) * dx * dy)


def _frame_energy(frame: dict[str, FloatGrid | BoolGrid], dx: float, dy: float, gravity: float = 9.81) -> float:
    h = np.asarray(frame["h"], dtype=np.float64)
    eta = np.asarray(frame["eta"], dtype=np.float64)
    u = np.asarray(frame["u"], dtype=np.float64)
    v = np.asarray(frame["v"], dtype=np.float64)
    bed = eta - h
    kinetic = 0.5 * h * (u**2 + v**2)
    potential = gravity * h * bed + 0.5 * gravity * h**2
    return float(np.sum(kinetic + potential) * dx * dy)


def _hydraulic_jump_metric(frame: dict[str, FloatGrid | BoolGrid], scenario) -> PointMetric:
    h = np.asarray(frame["h"], dtype=np.float64)
    wet = np.asarray(frame["wet"], dtype=np.bool_)
    masked_h = np.where(wet, h, 0.0)
    grad_y, grad_x = np.gradient(masked_h, scenario.grid.dy, scenario.grid.dx)
    strength = np.hypot(grad_x, grad_y)
    row, col = np.unravel_index(int(np.argmax(strength)), strength.shape)
    return PointMetric(
        x=_x_at_col(scenario, col),
        y=_y_at_row(scenario, row),
        value=float(strength[row, col]),
    )


def _wave_extreme_metric(frame: dict[str, FloatGrid | BoolGrid], scenario, *, mode: str) -> PointMetric:
    eta = np.asarray(frame["eta"], dtype=np.float64)
    wet = np.asarray(frame["wet"], dtype=np.bool_)
    if not np.any(wet):
        return PointMetric(x=None, y=None, value=0.0)
    masked_eta = np.where(wet, eta, -np.inf if mode == "crest" else np.inf)
    row, col = np.unravel_index(
        int(np.argmax(masked_eta) if mode == "crest" else np.argmin(masked_eta)),
        masked_eta.shape,
    )
    return PointMetric(
        x=_x_at_col(scenario, col),
        y=_y_at_row(scenario, row),
        value=float(eta[row, col]),
    )


def _hole_retention_metric(frame: dict[str, FloatGrid | BoolGrid], scenario) -> HoleRetentionMetric:
    holes = [feature for feature in scenario.features if feature.kind == "hole"]
    if not holes:
        return HoleRetentionMetric(hole_count=0, retained_area=0.0, centroid_x=None, centroid_y=None)

    h = np.asarray(frame["h"], dtype=np.float64)
    u = np.asarray(frame["u"], dtype=np.float64)
    froude = np.asarray(frame["froude"], dtype=np.float64)
    wet = np.asarray(frame["wet"], dtype=np.bool_)
    xs = scenario.grid.x_coordinates()
    ys = scenario.grid.y_coordinates()
    x_grid, y_grid = np.meshgrid(xs, ys)
    retained = np.zeros(h.shape, dtype=np.bool_)
    for hole in holes:
        scale_x = max(hole.length * 0.5, hole.radius, scenario.grid.dx)
        scale_y = max(hole.width * 0.5, hole.radius, scenario.grid.dy)
        influence = ((x_grid - hole.center[0]) / scale_x) ** 2 + ((y_grid - hole.center[1]) / scale_y) ** 2
        retained |= wet & (influence <= 1.0) & ((u < 0.0) | (froude < 0.9))
    area = float(np.sum(retained) * scenario.grid.dx * scenario.grid.dy)
    if not np.any(retained):
        return HoleRetentionMetric(hole_count=len(holes), retained_area=0.0, centroid_x=None, centroid_y=None)
    return HoleRetentionMetric(
        hole_count=len(holes),
        retained_area=area,
        centroid_x=float(np.mean(x_grid[retained])),
        centroid_y=float(np.mean(y_grid[retained])),
    )


def _diagnostic_delta(reference: SolverDiagnosticSummary, candidate: SolverDiagnosticSummary) -> DiagnosticDeltaSummary:
    return DiagnosticDeltaSummary(
        mass_relative_drift_delta=candidate.mass_relative_drift - reference.mass_relative_drift,
        energy_relative_change_delta=candidate.energy_relative_change - reference.energy_relative_change,
        froude_max_delta=candidate.froude_max - reference.froude_max,
        froude_mean_wet_delta=candidate.froude_mean_wet - reference.froude_mean_wet,
        hydraulic_jump_distance=_point_distance(reference.hydraulic_jump, candidate.hydraulic_jump),
        wave_crest_distance=_point_distance(reference.wave_crest, candidate.wave_crest),
        wave_trough_distance=_point_distance(reference.wave_trough, candidate.wave_trough),
        hole_retained_area_delta=candidate.hole_retention.retained_area - reference.hole_retention.retained_area,
        hole_centroid_distance=_centroid_distance(reference.hole_retention, candidate.hole_retention),
    )


def _point_distance(reference: PointMetric, candidate: PointMetric) -> float | None:
    if reference.x is None or reference.y is None or candidate.x is None or candidate.y is None:
        return None
    return float(np.hypot(candidate.x - reference.x, candidate.y - reference.y))


def _centroid_distance(reference: HoleRetentionMetric, candidate: HoleRetentionMetric) -> float | None:
    if (
        reference.centroid_x is None
        or reference.centroid_y is None
        or candidate.centroid_x is None
        or candidate.centroid_y is None
    ):
        return None
    return float(np.hypot(candidate.centroid_x - reference.centroid_x, candidate.centroid_y - reference.centroid_y))


def _x_at_col(scenario, col: int) -> float:
    return float(scenario.grid.origin_x + col * scenario.grid.dx)


def _y_at_row(scenario, row: int) -> float:
    return float(scenario.grid.origin_y + row * scenario.grid.dy)


def _compare_feature(index: int, feature, reference_frame, cpp_frame, scenario, *, reference_solver: str) -> FeatureComparison:
    reference_metric = _observed_feature_metric(feature, reference_frame, scenario)
    cpp_metric = _observed_feature_metric(feature, cpp_frame, scenario)
    return FeatureComparison(
        feature_index=index,
        kind=feature.kind,
        authored_x=float(feature.center[0]),
        authored_y=float(feature.center[1]),
        authored_strength=float(feature.strength),
        pyclaw=reference_metric,
        cpp=cpp_metric,
        location_delta=float(np.hypot(cpp_metric.x - reference_metric.x, cpp_metric.y - reference_metric.y)),
        strength_delta=cpp_metric.strength - reference_metric.strength,
        reference_solver=reference_solver,
    )


def _observed_feature_metric(feature, frame: dict[str, FloatGrid | BoolGrid], scenario) -> ObservedFeatureMetric:
    signal = _feature_signal(feature, frame, scenario)
    mask = _feature_mask(feature, signal.shape, scenario)
    if not np.any(mask):
        row, col = _nearest_cell(feature.center[0], feature.center[1], scenario)
    else:
        masked_signal = np.where(mask, signal, -np.inf)
        row, col = np.unravel_index(int(np.argmax(masked_signal)), masked_signal.shape)
    x = _x_at_col(scenario, int(col))
    y = _y_at_row(scenario, int(row))
    return ObservedFeatureMetric(
        x=x,
        y=y,
        strength=float(signal[row, col]),
        distance_to_authored=float(np.hypot(x - feature.center[0], y - feature.center[1])),
    )


def _feature_signal(feature, frame: dict[str, FloatGrid | BoolGrid], scenario) -> FloatGrid:
    h = np.asarray(frame["h"], dtype=np.float64)
    eta = np.asarray(frame["eta"], dtype=np.float64)
    u = np.asarray(frame["u"], dtype=np.float64)
    v = np.asarray(frame["v"], dtype=np.float64)
    wet = np.asarray(frame["wet"], dtype=np.bool_)
    froude = np.asarray(frame["froude"], dtype=np.float64)
    speed = np.hypot(u, v)
    slope_y, slope_x = np.gradient(eta, scenario.grid.dy, scenario.grid.dx)
    slope = np.hypot(slope_x, slope_y)
    local_eta = eta - np.nanmean(np.where(wet, eta, np.nan))
    if feature.kind == "hole":
        return np.where(wet, np.maximum(0.0, -u) + np.maximum(0.0, 0.9 - froude) + 0.25 * h, 0.0)
    if feature.kind == "lateral":
        return np.where(wet, np.abs(v), 0.0)
    if feature.kind == "boil":
        return np.where(wet, speed + 0.2 * h, 0.0)
    if feature.kind == "wave_train":
        return np.where(wet, np.abs(local_eta) + 0.1 * speed, 0.0)
    if feature.kind in {"ledge", "shallow"}:
        return np.where(wet, slope + np.maximum(0.0, np.nanmax(np.where(wet, h, np.nan)) - h), 0.0)
    if feature.kind in {"constriction", "rock", "strainer"}:
        return slope + speed + np.where(wet, 0.0, 1.0)
    return np.where(wet, speed + slope, 0.0)


def _feature_mask(feature, shape: tuple[int, int], scenario) -> BoolGrid:
    xs = scenario.grid.x_coordinates()
    ys = scenario.grid.y_coordinates()
    x_grid, y_grid = np.meshgrid(xs, ys)
    scale_x = max(feature.length * 0.5, feature.radius, scenario.grid.dx)
    scale_y = max(feature.width * 0.5, feature.radius, scenario.grid.dy)
    dx = (x_grid - feature.center[0]) / scale_x
    dy = (y_grid - feature.center[1]) / scale_y
    mask = (dx**2 + dy**2) <= 1.0
    if mask.shape != shape:
        raise ValueError("Feature mask shape does not match frame shape.")
    return mask


def _nearest_cell(x: float, y: float, scenario) -> tuple[int, int]:
    col = int(np.clip(round((x - scenario.grid.origin_x) / scenario.grid.dx), 0, scenario.grid.nx - 1))
    row = int(np.clip(round((y - scenario.grid.origin_y) / scenario.grid.dy), 0, scenario.grid.ny - 1))
    return row, col


def _threshold_check(name: str, value: float, threshold: float, details: str) -> ThresholdCheck:
    return ThresholdCheck(name=name, passed=value <= threshold, value=value, threshold=threshold, details=details)


def _max_linf(frame_comparisons: tuple[FrameFieldComparison, ...], kind: str) -> float:
    values: list[float] = []
    for comparison in frame_comparisons:
        summaries = comparison.field_errors if kind == "field" else comparison.slope_errors
        values.extend(summary.linf for summary in summaries)
    return max(values, default=0.0)


def _max_series_linf(series: tuple[SeriesComparison, ...]) -> float:
    return max((summary.linf for item in series for summary in item.field_errors), default=0.0)
