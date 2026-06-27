"""Comparison reports for PyClaw and C++ 2.5D solver outputs."""

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
        }


@dataclass(frozen=True, slots=True)
class FrameFieldComparison:
    label: str
    pyclaw_frame: str
    cpp_frame: str
    field_errors: tuple[FieldErrorSummary, ...]
    slope_errors: tuple[FieldErrorSummary, ...]
    wet_mismatch_fraction: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "pyclaw_frame": self.pyclaw_frame,
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


def compare_dual_solver_fields(
    dual_solver_dir_or_manifest: str | Path,
    *,
    output_path: str | Path | None = None,
) -> FieldComparisonReport:
    """Compare matching initial/final field frames from a dual-solver run."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(root / manifest["scenario_package"])
    pyclaw_manifest = _load_manifest(root / manifest["pyclaw"]["manifest"])
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])

    pyclaw_frames = [root / manifest["pyclaw"]["output_dir"] / frame for frame in pyclaw_manifest["frames"]]
    cpp_frames = [root / manifest["cpp"]["output_dir"] / frame for frame in cpp_manifest["frames"]]
    pairings = _frame_pairings(pyclaw_frames, cpp_frames)

    comparisons = tuple(
        _compare_frame_pair(
            label,
            pyclaw_frame_path,
            cpp_frame_path,
            scenario.grid.dx,
            scenario.grid.dy,
        )
        for label, pyclaw_frame_path, cpp_frame_path in pairings
    )
    report = FieldComparisonReport(scenario_id=manifest["scenario_id"], frame_comparisons=comparisons)
    if output_path is not None:
        report.write_json(output_path)
    return report


def compare_dual_solver_probes(
    dual_solver_dir_or_manifest: str | Path,
    *,
    output_path: str | Path | None = None,
) -> ProbeComparisonReport:
    """Compare point probe time series and cross sections from a dual-solver run."""

    manifest_path = _manifest_path(dual_solver_dir_or_manifest)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pyclaw_manifest = _load_manifest(root / manifest["pyclaw"]["manifest"])
    cpp_manifest = _load_manifest(root / manifest["cpp"]["manifest"])
    pyclaw_output = root / manifest["pyclaw"]["output_dir"]
    cpp_output = root / manifest["cpp"]["output_dir"]

    point_probes = tuple(
        _compare_probe_pair(probe_id, pyclaw_path, cpp_path)
        for probe_id, pyclaw_path, cpp_path in _matched_files(
            pyclaw_output,
            pyclaw_manifest["probes"],
            cpp_output,
            cpp_manifest["probes"],
        )
    )
    cross_sections = tuple(
        _compare_cross_section_pair(probe_id, pyclaw_path, cpp_path)
        for probe_id, pyclaw_path, cpp_path in _matched_files(
            pyclaw_output,
            pyclaw_manifest["cross_sections"],
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


def _manifest_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.name == "dual_solver_manifest.json":
        return candidate
    return candidate / "dual_solver_manifest.json"


def _load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    pyclaw_frame_path: Path,
    cpp_frame_path: Path,
    dx: float,
    dy: float,
) -> FrameFieldComparison:
    pyclaw_frame = _load_pyclaw_npz_frame(pyclaw_frame_path)
    cpp_frame = _load_cpp_csv_frame(cpp_frame_path)
    field_errors = tuple(_field_error(name, pyclaw_frame[name], cpp_frame[name]) for name in FIELD_NAMES)
    pyclaw_slopes = _slopes_from_eta(pyclaw_frame["eta"], dx, dy)
    cpp_slopes = _slopes_from_eta(cpp_frame["eta"], dx, dy)
    slope_errors = tuple(
        _field_error(name, pyclaw_slopes[index], cpp_slopes[index])
        for index, name in enumerate(SLOPE_FIELD_NAMES)
    )
    wet_mismatch = float(np.mean(np.asarray(pyclaw_frame["wet"], dtype=np.bool_) != np.asarray(cpp_frame["wet"], dtype=np.bool_)))
    return FrameFieldComparison(
        label=label,
        pyclaw_frame=str(pyclaw_frame_path),
        cpp_frame=str(cpp_frame_path),
        field_errors=field_errors,
        slope_errors=slope_errors,
        wet_mismatch_fraction=wet_mismatch,
    )


def _load_pyclaw_npz_frame(path: Path) -> dict[str, FloatGrid | BoolGrid]:
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
        }


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


def _field_error(field_name: str, reference: FloatGrid | BoolGrid, candidate: FloatGrid | BoolGrid) -> FieldErrorSummary:
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    if ref.shape != cand.shape:
        raise ValueError(f"Shape mismatch for {field_name}: PyClaw={ref.shape} C++={cand.shape}")
    delta = cand - ref
    return FieldErrorSummary(
        field=field_name,
        l1=float(np.mean(np.abs(delta))),
        l2=float(np.sqrt(np.mean(delta**2))),
        linf=float(np.max(np.abs(delta))),
        reference_min=float(np.min(ref)),
        reference_max=float(np.max(ref)),
        candidate_min=float(np.min(cand)),
        candidate_max=float(np.max(cand)),
    )


def _slopes_from_eta(eta: FloatGrid, dx: float, dy: float) -> tuple[FloatGrid, FloatGrid]:
    slope_y, slope_x = np.gradient(np.asarray(eta, dtype=np.float64), dy, dx)
    return slope_x, slope_y


def _compare_probe_pair(probe_id: str, pyclaw_path: Path, cpp_path: Path) -> SeriesComparison:
    reference = _load_probe_csv(pyclaw_path)
    candidate = _load_probe_csv(cpp_path)
    ref_times = reference["time"]
    cand_times = candidate["time"]
    indices, max_time_delta = _nearest_indices(ref_times, cand_times)
    field_errors = tuple(
        _field_error(field, reference[field], candidate[field][indices])
        for field in PROBE_FIELD_NAMES
        if field in reference and field in candidate
    )
    return SeriesComparison(
        sample_id=probe_id,
        kind="point",
        field_errors=field_errors,
        reference_sample_count=len(ref_times),
        candidate_sample_count=len(cand_times),
        max_time_delta=max_time_delta,
    )


def _compare_cross_section_pair(probe_id: str, pyclaw_path: Path, cpp_path: Path) -> SeriesComparison:
    reference = _load_pyclaw_cross_section_npz(pyclaw_path)
    candidate = _load_cpp_cross_section_csv(cpp_path)
    time_indices, max_time_delta = _nearest_indices(reference["times"], candidate["times"])
    distance_indices, max_distance_delta = _nearest_indices(reference["distance"], candidate["distance"])
    field_errors = tuple(
        _field_error(
            field,
            reference[field],
            candidate[field][np.ix_(time_indices, distance_indices)],
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
