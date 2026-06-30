"""Analytic fixture comparison reports for Milestone 17."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from .scenario2_5d import GridSpec2_5D, Scenario2_5D, read_scenario2_5d_package

ANALYTIC_VALIDATION_REPORT_SCHEMA_VERSION = "raftsim.milestone17.analytic_validation_report.v0"
AnalyticCandidateKind = Literal["scenario", "cpp", "geoclaw", "reference"]


@dataclass(frozen=True, slots=True)
class AnalyticCandidateFields:
    """Candidate field arrays loaded from a scenario, C++ frame, GeoClaw frame, or reference."""

    kind: str
    source: str
    fields: dict[str, np.ndarray]


@dataclass(frozen=True, slots=True)
class AnalyticMetricResult:
    fixture_id: str
    metric_id: str
    field: str
    norm: str
    value: float
    threshold: float
    units: str
    passed: bool
    details: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "metric_id": self.metric_id,
            "field": self.field,
            "norm": self.norm,
            "value": self.value,
            "threshold": self.threshold,
            "units": self.units,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class AnalyticFixtureComparison:
    fixture_id: str
    title: str
    tolerance_tier: str
    scenario_package: str
    reference_path: str
    candidate_kind: str
    candidate_source: str
    metrics: tuple[AnalyticMetricResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.metrics) and all(metric.passed for metric in self.metrics)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "title": self.title,
            "tolerance_tier": self.tolerance_tier,
            "scenario_package": self.scenario_package,
            "reference_path": self.reference_path,
            "candidate_kind": self.candidate_kind,
            "candidate_source": self.candidate_source,
            "passed": self.passed,
            "metrics": [metric.to_json_dict() for metric in self.metrics],
        }


@dataclass(frozen=True, slots=True)
class AnalyticValidationReport:
    manifest_path: str
    candidate_kind: str
    candidate_label: str
    candidate_root: str | None
    frame_index: int
    comparisons: tuple[AnalyticFixtureComparison, ...]

    @property
    def passed(self) -> bool:
        return bool(self.comparisons) and all(comparison.passed for comparison in self.comparisons)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": ANALYTIC_VALIDATION_REPORT_SCHEMA_VERSION,
            "passed": self.passed,
            "manifest_path": self.manifest_path,
            "candidate_kind": self.candidate_kind,
            "candidate_label": self.candidate_label,
            "candidate_root": self.candidate_root,
            "frame_index": self.frame_index,
            "fixture_count": len(self.comparisons),
            "passed_count": sum(1 for comparison in self.comparisons if comparison.passed),
            "failed_count": sum(1 for comparison in self.comparisons if not comparison.passed),
            "comparisons": [comparison.to_json_dict() for comparison in self.comparisons],
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
            "# Milestone 17 Analytic Fixture Validation",
            "",
            f"Schema: `{ANALYTIC_VALIDATION_REPORT_SCHEMA_VERSION}`",
            "",
            f"Decision: **{'PASS' if self.passed else 'BLOCKED'}**",
            "",
            f"Candidate: `{self.candidate_label}` (`{self.candidate_kind}`)",
            "",
            f"Fixture count: {len(self.comparisons)}",
            "",
            "| Fixture | Tier | Result | Max metric value | Failing metrics |",
            "| --- | --- | --- | ---: | --- |",
        ]
        for comparison in self.comparisons:
            max_value = max((metric.value for metric in comparison.metrics), default=0.0)
            failing = ", ".join(metric.metric_id for metric in comparison.metrics if not metric.passed) or "-"
            lines.append(
                "| "
                f"{comparison.fixture_id} | "
                f"{comparison.tolerance_tier} | "
                f"{'PASS' if comparison.passed else 'FAIL'} | "
                f"{max_value:.6g} | "
                f"{failing} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def compare_analytic_fixture_manifest(
    manifest_path: str | Path,
    *,
    candidate_kind: AnalyticCandidateKind = "scenario",
    candidate_root: str | Path | None = None,
    candidate_label: str | None = None,
    frame_index: int = 0,
) -> AnalyticValidationReport:
    """Compare analytic fixture references against one candidate field source."""

    manifest_file = Path(manifest_path)
    manifest_root = manifest_file.parent
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    comparisons: list[AnalyticFixtureComparison] = []
    root_path = None if candidate_root is None else Path(candidate_root)

    for entry in manifest["fixtures"]:
        fixture_id = str(entry["fixture_id"])
        outputs = entry["outputs"]
        scenario_package = manifest_root / str(outputs["scenario_package"])
        reference_path = manifest_root / str(outputs["analytic_reference"])
        reference_fields_path = manifest_root / str(outputs.get("analytic_fields", Path(outputs["analytic_reference"]).with_name("reference_fields.npz")))
        scenario = read_scenario2_5d_package(scenario_package)
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        reference_fields = _load_npz_fields(reference_fields_path)
        candidate = _load_candidate_fields(
            kind=candidate_kind,
            scenario=scenario,
            reference_fields=reference_fields,
            fixture_id=fixture_id,
            candidate_root=root_path,
            frame_index=frame_index,
        )
        metrics = tuple(
            _evaluate_metric(
                fixture_id=fixture_id,
                metric=metric,
                scenario=scenario,
                reference=reference,
                reference_fields=reference_fields,
                candidate_fields=candidate.fields,
            )
            for metric in entry["metrics"]
        )
        comparisons.append(
            AnalyticFixtureComparison(
                fixture_id=fixture_id,
                title=str(entry["title"]),
                tolerance_tier=str(entry["tolerance_tier"]),
                scenario_package=str(scenario_package),
                reference_path=str(reference_path),
                candidate_kind=candidate.kind,
                candidate_source=candidate.source,
                metrics=metrics,
            )
        )

    label = candidate_label or _default_candidate_label(candidate_kind)
    return AnalyticValidationReport(
        manifest_path=str(manifest_file),
        candidate_kind=candidate_kind,
        candidate_label=label,
        candidate_root=None if root_path is None else str(root_path),
        frame_index=frame_index,
        comparisons=tuple(comparisons),
    )


def _load_candidate_fields(
    *,
    kind: AnalyticCandidateKind,
    scenario: Scenario2_5D,
    reference_fields: dict[str, np.ndarray],
    fixture_id: str,
    candidate_root: Path | None,
    frame_index: int,
) -> AnalyticCandidateFields:
    if kind == "scenario":
        return AnalyticCandidateFields(
            kind=kind,
            source=scenario.metadata.scenario_id,
            fields=_scenario_fields(scenario),
        )
    if kind == "reference":
        return AnalyticCandidateFields(kind=kind, source=f"{fixture_id}/reference_fields.npz", fields=reference_fields)
    if candidate_root is None:
        raise ValueError(f"--candidate-root is required for {kind!r} analytic validation.")
    candidate_dir = _fixture_candidate_dir(candidate_root, fixture_id)
    manifest_path = candidate_dir / "manifest.json"
    if kind == "geoclaw":
        return AnalyticCandidateFields(
            kind=kind,
            source=str(manifest_path),
            fields=_load_geoclaw_frame_fields(manifest_path, frame_index=frame_index),
        )
    if kind == "cpp":
        return AnalyticCandidateFields(
            kind=kind,
            source=str(manifest_path),
            fields=_load_cpp_frame_fields(manifest_path, shape=scenario.grid.shape, frame_index=frame_index),
        )
    raise ValueError(f"Unsupported analytic candidate kind: {kind}")


def _fixture_candidate_dir(candidate_root: Path, fixture_id: str) -> Path:
    fixture_dir = candidate_root / fixture_id
    if (fixture_dir / "manifest.json").exists():
        return fixture_dir
    return candidate_root


def _scenario_fields(scenario: Scenario2_5D) -> dict[str, np.ndarray]:
    state = scenario.initial_state
    return _normalize_fields(
        {
            "bed": scenario.bed,
            "depth": state.depth,
            "h": state.depth,
            "eta": state.eta,
            "u": state.u,
            "v": state.v,
            "hu": state.hu,
            "hv": state.hv,
            "wet": state.wet,
        }
    )


def _load_npz_fields(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return _normalize_fields({key: np.asarray(data[key]) for key in data.files})


def _load_geoclaw_frame_fields(manifest_path: Path, *, frame_index: int) -> dict[str, np.ndarray]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame_path = _selected_frame_path(manifest_path.parent, manifest["frames"], frame_index)
    return _load_npz_fields(frame_path)


def _load_cpp_frame_fields(manifest_path: Path, *, shape: tuple[int, int], frame_index: int) -> dict[str, np.ndarray]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame_path = _selected_frame_path(manifest_path.parent, manifest["frames"], frame_index)
    arrays = {
        "h": np.zeros(shape, dtype=np.float64),
        "eta": np.zeros(shape, dtype=np.float64),
        "u": np.zeros(shape, dtype=np.float64),
        "v": np.zeros(shape, dtype=np.float64),
        "hu": np.zeros(shape, dtype=np.float64),
        "hv": np.zeros(shape, dtype=np.float64),
        "wet": np.zeros(shape, dtype=np.bool_),
        "froude": np.zeros(shape, dtype=np.float64),
    }
    with frame_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            r = int(row["row"])
            c = int(row["col"])
            for field in ("h", "eta", "u", "v", "hu", "hv", "froude"):
                arrays[field][r, c] = float(row[field])
            arrays["wet"][r, c] = row["wet"] in {"1", "true", "True"}
    return _normalize_fields(arrays)


def _selected_frame_path(root: Path, frames: list[str], frame_index: int) -> Path:
    if not frames:
        raise ValueError(f"No frames recorded in {root / 'manifest.json'}.")
    index = frame_index if frame_index >= 0 else len(frames) + frame_index
    if index < 0 or index >= len(frames):
        raise IndexError(f"Frame index {frame_index} is out of range for {len(frames)} frames.")
    return root / frames[index]


def _normalize_fields(fields: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    normalized = {key: np.asarray(value) for key, value in fields.items()}
    if "h" not in normalized and "depth" in normalized:
        normalized["h"] = normalized["depth"]
    if "depth" not in normalized and "h" in normalized:
        normalized["depth"] = normalized["h"]
    if "wet" in normalized:
        normalized["wet"] = np.asarray(normalized["wet"], dtype=np.bool_)
    if "hu" not in normalized and {"h", "u"}.issubset(normalized):
        normalized["hu"] = normalized["h"] * normalized["u"]
    if "hv" not in normalized and {"h", "v"}.issubset(normalized):
        normalized["hv"] = normalized["h"] * normalized["v"]
    if "froude" not in normalized and {"h", "u", "v"}.issubset(normalized):
        speed = np.sqrt(normalized["u"] ** 2 + normalized["v"] ** 2)
        froude = np.zeros_like(speed, dtype=np.float64)
        np.divide(speed, np.sqrt(9.81 * normalized["h"]), out=froude, where=normalized["h"] > 1.0e-9)
        normalized["froude"] = froude
    return normalized


def _evaluate_metric(
    *,
    fixture_id: str,
    metric: dict[str, object],
    scenario: Scenario2_5D,
    reference: dict[str, object],
    reference_fields: dict[str, np.ndarray],
    candidate_fields: dict[str, np.ndarray],
) -> AnalyticMetricResult:
    metric_id = str(metric["metric_id"])
    field = str(metric["field"])
    norm = str(metric["norm"])
    threshold = float(metric["threshold"])
    units = str(metric["units"])

    if metric_id == "wet_mask_mismatch_count":
        value = float(np.count_nonzero(_field(candidate_fields, "wet") != _field(reference_fields, "wet")))
        details = "wet mask mismatched cells"
    elif metric_id == "shoreline_position_abs":
        value = abs(_shoreline_y(scenario.grid, candidate_fields) - _shoreline_y(scenario.grid, reference_fields))
        details = "mean shoreline y-position difference"
    elif metric_id == "specific_energy_abs":
        value = _specific_energy_abs(candidate_fields, reference_fields, reference)
        details = "maximum specific-energy difference"
    elif metric_id == "mass_relative_drift":
        value = _mass_relative_difference(candidate_fields, reference_fields)
        details = "candidate mass relative to analytic reference mass"
    elif metric_id == "conjugate_depth_ratio_abs":
        value = abs(_depth_ratio(scenario.grid, candidate_fields) - _depth_ratio(scenario.grid, reference_fields))
        details = "downstream/upstream depth-ratio difference"
    elif metric_id == "froude_class_agreement":
        value = float(np.count_nonzero(_froude_class(candidate_fields) != _froude_class(reference_fields)))
        details = "wet-cell Froude class mismatch count"
    elif metric_id == "crest_froude_abs":
        target = float(reference["diagnostics"]["crest_froude"]) if "diagnostics" in reference else 1.0
        value = abs(_crest_froude(scenario.grid, candidate_fields) - target)
        details = "mean crest Froude difference"
    else:
        value = _array_metric_value(field, norm, candidate_fields, reference_fields)
        details = f"{norm} difference for {field}"

    return AnalyticMetricResult(
        fixture_id=fixture_id,
        metric_id=metric_id,
        field=field,
        norm=norm,
        value=value,
        threshold=threshold,
        units=units,
        passed=value <= threshold,
        details=details,
    )


def _array_metric_value(field: str, norm: str, candidate_fields: dict[str, np.ndarray], reference_fields: dict[str, np.ndarray]) -> float:
    candidate = _field(candidate_fields, field)
    reference = _field(reference_fields, field)
    if candidate.shape != reference.shape:
        raise ValueError(f"Field shape mismatch for {field}: {candidate.shape} != {reference.shape}")
    diff = np.asarray(candidate, dtype=np.float64) - np.asarray(reference, dtype=np.float64)
    if norm in {"linf", "abs", "class"}:
        return float(np.max(np.abs(diff)))
    if norm == "l1":
        return float(np.mean(np.abs(diff)))
    if norm == "l2":
        return float(math.sqrt(np.mean(diff**2)))
    if norm == "relative":
        denom = max(float(np.sum(np.abs(reference))), 1.0e-12)
        return float(np.sum(np.abs(diff)) / denom)
    if norm == "count":
        return float(np.count_nonzero(diff))
    raise ValueError(f"Unsupported analytic metric norm: {norm}")


def _field(fields: dict[str, np.ndarray], name: str) -> np.ndarray:
    if name == "speed":
        return np.sqrt(fields["u"] ** 2 + fields["v"] ** 2)
    if name == "froude":
        return fields["froude"]
    if name == "shoreline_y":
        raise ValueError("shoreline_y is a derived metric and cannot be loaded as a field.")
    if name in fields:
        return fields[name]
    if name == "h" and "depth" in fields:
        return fields["depth"]
    raise KeyError(f"Field {name!r} is not available in analytic comparison data.")


def _shoreline_y(grid: GridSpec2_5D, fields: dict[str, np.ndarray]) -> float:
    wet = _field(fields, "wet")
    ys = grid.y_coordinates()
    shoreline_samples: list[float] = []
    for col in range(wet.shape[1]):
        wet_rows = np.flatnonzero(wet[:, col])
        if len(wet_rows) > 0:
            shoreline_samples.append(float(ys[int(wet_rows[-1])]))
    if not shoreline_samples:
        return float("nan")
    return float(np.mean(shoreline_samples))


def _specific_energy_abs(candidate_fields: dict[str, np.ndarray], reference_fields: dict[str, np.ndarray], reference: dict[str, object]) -> float:
    unit_discharge = float(reference["parameters"]["unit_discharge"])
    candidate = _specific_energy(candidate_fields, unit_discharge)
    analytic = _specific_energy(reference_fields, unit_discharge)
    return float(np.nanmax(np.abs(candidate - analytic)))


def _specific_energy(fields: dict[str, np.ndarray], unit_discharge: float) -> np.ndarray:
    h = np.maximum(_field(fields, "h"), 1.0e-9)
    bed = fields.get("bed", np.zeros_like(h, dtype=np.float64))
    return bed + h + unit_discharge**2 / (2.0 * 9.81 * h**2)


def _mass_relative_difference(candidate_fields: dict[str, np.ndarray], reference_fields: dict[str, np.ndarray]) -> float:
    candidate_mass = float(np.sum(np.maximum(_field(candidate_fields, "h"), 0.0)))
    reference_mass = float(np.sum(np.maximum(_field(reference_fields, "h"), 0.0)))
    return abs(candidate_mass - reference_mass) / max(reference_mass, 1.0e-12)


def _depth_ratio(grid: GridSpec2_5D, fields: dict[str, np.ndarray]) -> float:
    h = _field(fields, "h")
    xs = grid.x_coordinates()
    upstream = h[:, xs < grid.center[0]]
    downstream = h[:, xs >= grid.center[0]]
    return float(np.mean(downstream) / max(float(np.mean(upstream)), 1.0e-12))


def _froude_class(fields: dict[str, np.ndarray]) -> np.ndarray:
    wet = _field(fields, "wet")
    return np.where(wet, _field(fields, "froude") >= 1.0, False)


def _crest_froude(grid: GridSpec2_5D, fields: dict[str, np.ndarray]) -> float:
    crest_col = grid.nx // 2
    return float(np.mean(_field(fields, "froude")[:, crest_col]))


def _default_candidate_label(kind: AnalyticCandidateKind) -> str:
    return {
        "scenario": "scenario_initial_state",
        "reference": "analytic_reference_fields",
        "cpp": "cpp_solver_frame",
        "geoclaw": "geoclaw_normalized_frame",
    }[kind]
