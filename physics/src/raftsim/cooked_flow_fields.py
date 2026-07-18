"""Cook per-flow-band steady-state river flow fields with the genuine C++ FV solver.

This module produces the precomputed flow fields that release-1.0-plan.md section 5
A-1 requires for the P2 live river-water windows: for each South Fork flow band
(low / median / high runnable) the genuine finite-volume solver (HLL, spatial order
2, fixture calibrations disabled) is run on the Chili Bar seed scenario until the
field change rate between saved frames falls below explicit thresholds, and the
resulting steady-state grids (h, u, v, bed, wet mask) are exported as ``.npy``
arrays plus a JSON manifest.

The manifest is the contract the UE river-window loader reads. Its schema id is
``raftsim.cooked_flow_fields.v1`` and it records, per band: array files with
dtype/shape/units/sha256, the grid transform (origin/spacing/CRS note), the exact
solver configuration the fields were cooked with (the loader must configure the
embedded live solver identically or the seeded window will transient away), and
honest convergence evidence (full residual history plus a converged flag; a band
that fails to converge is recorded as ``converged: false``, never hidden).
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from .dual_solver import CppSolverRunConfig, CppSolverRunResult, run_cpp_solver_scenario
from .real_world import (
    PlayerSelection,
    default_player_selections,
    generate_real_world_scenario2_5d,
    south_fork_american_flow_bands,
)
from .scenario2_5d import Scenario2_5D, read_scenario2_5d_package

COOKED_FLOW_FIELDS_SCHEMA = "raftsim.cooked_flow_fields.v1"
COOKED_FLOW_FIELDS_GENERATOR = "raftsim.cooked_flow_fields"

#: Array names every band directory must provide, with dtype and units.
COOKED_ARRAY_CONTRACT: dict[str, dict[str, str]] = {
    "h": {"dtype": "float32", "units": "m", "description": "Water depth above bed."},
    "u": {"dtype": "float32", "units": "m_per_s", "description": "Depth-averaged x (downstream) velocity."},
    "v": {"dtype": "float32", "units": "m_per_s", "description": "Depth-averaged y (cross-stream) velocity."},
    "bed": {"dtype": "float32", "units": "m", "description": "Bed elevation in scenario-local meters."},
    "wet_mask": {"dtype": "uint8", "units": "boolean", "description": "1 where the solver reports the cell wet."},
}

SOUTH_FORK_COOKED_BAND_IDS = ("low_runnable", "median_runnable", "high_runnable")


@dataclass(frozen=True, slots=True)
class ConvergenceThresholds:
    """Steady-state acceptance thresholds on inter-frame field change.

    A "window" is the interval between two consecutive saved frames
    (``frame_interval`` solver steps). A band counts as converged when the final
    ``consecutive_windows_required`` windows all satisfy every threshold.
    """

    max_abs_dh_m: float = 0.002
    max_abs_du_m_per_s: float = 0.01
    max_abs_dv_m_per_s: float = 0.01
    consecutive_windows_required: int = 3

    def window_passes(self, window: "ConvergenceWindow") -> bool:
        return (
            window.max_abs_dh_m <= self.max_abs_dh_m
            and window.max_abs_du_m_per_s <= self.max_abs_du_m_per_s
            and window.max_abs_dv_m_per_s <= self.max_abs_dv_m_per_s
        )

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConvergenceWindow:
    """Field change between two consecutive saved frames."""

    end_time_s: float
    max_abs_dh_m: float
    max_abs_du_m_per_s: float
    max_abs_dv_m_per_s: float

    def to_json_dict(self) -> dict[str, float]:
        return {
            "end_time_s": self.end_time_s,
            "max_abs_dh_m": self.max_abs_dh_m,
            "max_abs_du_m_per_s": self.max_abs_du_m_per_s,
            "max_abs_dv_m_per_s": self.max_abs_dv_m_per_s,
        }


@dataclass(frozen=True, slots=True)
class CookedFlowFieldsRunConfig:
    """Solver settings used to cook the steady fields.

    These deliberately mirror the finite-volume gate configuration used by the
    solver-truth baseline (``reports/solver_truth_baseline``) for the
    ``south_fork_*_runnable`` rows: genuine dynamics only. The UE river-window
    loader must configure the embedded live solver with the same
    ``flux_scheme`` / ``spatial_order`` / ``roughness_scale`` /
    ``bed_slope_source_scale`` or the seeded field will immediately drift.
    """

    steps: int = 36000
    frame_interval: int = 600
    solver_mode: str = "finite_volume"
    boundary_mode: str = "scenario"
    flux_scheme: str = "hll"
    spatial_order: int = 2
    cfl: float = 0.45
    dry_tolerance: float = 1.0e-6
    feature_strength_scale: float = 0.0
    roughness_scale: float = 0.5
    bed_slope_source_scale: float = 0.75
    preserve_initial_mass: bool = False
    disable_fixture_calibrations: bool = True
    thresholds: ConvergenceThresholds = field(default_factory=ConvergenceThresholds)

    def __post_init__(self) -> None:
        if self.steps < 2 * self.frame_interval:
            raise ValueError("steps must cover at least two frame intervals to measure convergence.")
        if self.spatial_order != 2:
            raise ValueError("Cooked flow fields are contracted to the order-2 MUSCL path.")
        if not self.disable_fixture_calibrations:
            raise ValueError("Cooked flow fields must come from the genuine solver: calibrations stay disabled.")

    def cpp_config(self, executable: Path) -> CppSolverRunConfig:
        return CppSolverRunConfig(
            executable=executable,
            steps=self.steps,
            frame_interval=self.frame_interval,
            solver_mode=self.solver_mode,
            boundary_mode=self.boundary_mode,
            flux_scheme=self.flux_scheme,
            cfl=self.cfl,
            dry_tolerance=self.dry_tolerance,
            feature_strength_scale=self.feature_strength_scale,
            roughness_scale=self.roughness_scale,
            bed_slope_source_scale=self.bed_slope_source_scale,
            preserve_initial_mass=self.preserve_initial_mass,
            disable_fixture_calibrations=self.disable_fixture_calibrations,
            allow_validation_failure=True,
        )


@dataclass(frozen=True, slots=True)
class AuthoredWindowBand:
    """One authored scenario-window flow band cooked from an on-disk package.

    Unlike the Chili Bar pilot bands (synthesized deterministically from a
    ``PlayerSelection``), an authored window's per-band scenario package already
    lives on disk (``scenario.json`` + ``bed.npy`` + ``initial_state.npz`` + ...).
    The solver runs directly against that committed package so the cooked field
    is the genuine steady state of exactly the geometry that was authored and
    behaviorally validated.
    """

    band_id: str
    scenario_dir: Path
    discharge_target_m3s: float
    discharge_target_cfs: float | None = None


@dataclass(frozen=True, slots=True)
class CookedBandResult:
    band_id: str
    scenario: Scenario2_5D
    run: CppSolverRunResult
    arrays: dict[str, np.ndarray]
    windows: tuple[ConvergenceWindow, ...]
    converged: bool
    scenario_input_hashes: dict[str, str]
    discharge_target_m3s: float
    discharge_target_cfs: float | None = None


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_frame_fields(frame_path: Path, ny: int, nx: int) -> dict[str, np.ndarray]:
    h = np.zeros((ny, nx), dtype=np.float64)
    u = np.zeros((ny, nx), dtype=np.float64)
    v = np.zeros((ny, nx), dtype=np.float64)
    wet = np.zeros((ny, nx), dtype=np.uint8)
    with frame_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            i = int(row["row"])
            j = int(row["col"])
            h[i, j] = float(row["h"])
            u[i, j] = float(row["u"])
            v[i, j] = float(row["v"])
            wet[i, j] = int(row["wet"])
    return {"h": h, "u": u, "v": v, "wet": wet}


def _convergence_windows(
    frame_fields: list[dict[str, np.ndarray]],
    *,
    window_seconds: float,
) -> tuple[ConvergenceWindow, ...]:
    windows = []
    for index in range(1, len(frame_fields)):
        prev = frame_fields[index - 1]
        cur = frame_fields[index]
        windows.append(
            ConvergenceWindow(
                end_time_s=index * window_seconds,
                max_abs_dh_m=float(np.abs(cur["h"] - prev["h"]).max()),
                max_abs_du_m_per_s=float(np.abs(cur["u"] - prev["u"]).max()),
                max_abs_dv_m_per_s=float(np.abs(cur["v"] - prev["v"]).max()),
            )
        )
    return tuple(windows)


def _is_converged(windows: tuple[ConvergenceWindow, ...], thresholds: ConvergenceThresholds) -> bool:
    required = thresholds.consecutive_windows_required
    if len(windows) < required:
        return False
    return all(thresholds.window_passes(window) for window in windows[-required:])


def _selection_for_band(band_id: str) -> PlayerSelection:
    for selection in default_player_selections():
        if selection.flow_band == band_id:
            return selection
    raise ValueError(f"No default player selection maps to flow band '{band_id}'.")


def _band_result_from_run(
    *,
    band_id: str,
    scenario: Scenario2_5D,
    run: CppSolverRunResult,
    scenario_input_dir: Path,
    config: CookedFlowFieldsRunConfig,
    discharge_target_m3s: float,
    discharge_target_cfs: float | None,
) -> CookedBandResult:
    """Extract steady-state grids and convergence evidence from a finished run.

    Shared by the Chili Bar pilot path and the authored-window path so both
    produce byte-identical band records from the same solver frames.
    """

    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8"))
    ny = scenario.grid.ny
    nx = scenario.grid.nx
    frame_fields = [_load_frame_fields(run.output_dir / frame, ny, nx) for frame in manifest["frames"]]
    if len(frame_fields) < 2:
        raise RuntimeError(f"Band '{band_id}' produced fewer than two frames; cannot assess convergence.")
    window_seconds = config.frame_interval * scenario.fixed_dt
    windows = _convergence_windows(frame_fields, window_seconds=window_seconds)
    converged = _is_converged(windows, config.thresholds)

    final = frame_fields[-1]
    arrays = {
        "h": np.ascontiguousarray(final["h"], dtype=np.float32),
        "u": np.ascontiguousarray(final["u"], dtype=np.float32),
        "v": np.ascontiguousarray(final["v"], dtype=np.float32),
        "bed": np.ascontiguousarray(scenario.bed, dtype=np.float32),
        "wet_mask": np.ascontiguousarray(final["wet"], dtype=np.uint8),
    }
    scenario_input_hashes = {
        name: sha256_of_file(scenario_input_dir / name)
        for name in ("scenario.json", "bed.npy", "initial_state.npz")
    }
    return CookedBandResult(
        band_id=band_id,
        scenario=scenario,
        run=run,
        arrays=arrays,
        windows=windows,
        converged=converged,
        scenario_input_hashes=scenario_input_hashes,
        discharge_target_m3s=discharge_target_m3s,
        discharge_target_cfs=discharge_target_cfs,
    )


def cook_flow_field_band(
    band_id: str,
    *,
    executable: Path,
    work_dir: Path,
    config: CookedFlowFieldsRunConfig,
) -> CookedBandResult:
    """Run the genuine solver for one Chili Bar pilot flow band (synthesized scenario)."""

    selection = _selection_for_band(band_id)
    scenario = generate_real_world_scenario2_5d(selection)
    band_work_dir = Path(work_dir) / band_id
    run = run_cpp_solver_scenario(scenario, output_dir=band_work_dir, config=config.cpp_config(Path(executable)))
    flow_band = next(band for band in south_fork_american_flow_bands() if band.flow_band == band_id)
    scenario_input_dir = band_work_dir / "scenario" / scenario.metadata.scenario_id
    return _band_result_from_run(
        band_id=band_id,
        scenario=scenario,
        run=run,
        scenario_input_dir=scenario_input_dir,
        config=config,
        discharge_target_m3s=flow_band.discharge_m3s,
        discharge_target_cfs=flow_band.discharge_cfs,
    )


def cook_flow_field_band_from_package(
    band: AuthoredWindowBand,
    *,
    executable: Path,
    work_dir: Path,
    config: CookedFlowFieldsRunConfig,
) -> CookedBandResult:
    """Run the genuine solver on one authored scenario-window package on disk.

    The solver is pointed at the committed band package directly (no copy), so
    the cooked steady state is the genuine finite-volume evolution of exactly
    the authored, behaviorally-validated geometry and boundaries.
    """

    scenario_dir = Path(band.scenario_dir)
    scenario = read_scenario2_5d_package(scenario_dir)
    band_work_dir = Path(work_dir) / band.band_id
    run = run_cpp_solver_scenario(scenario_dir, output_dir=band_work_dir, config=config.cpp_config(Path(executable)))
    return _band_result_from_run(
        band_id=band.band_id,
        scenario=scenario,
        run=run,
        scenario_input_dir=scenario_dir,
        config=config,
        discharge_target_m3s=band.discharge_target_m3s,
        discharge_target_cfs=band.discharge_target_cfs,
    )


def _discharge_profile_m3s(arrays: dict[str, np.ndarray], dy: float) -> dict[str, float]:
    h = arrays["h"].astype(np.float64)
    u = arrays["u"].astype(np.float64)
    nx = h.shape[1]
    return {
        "west": float((h[:, 0] * u[:, 0]).sum() * dy),
        "mid": float((h[:, nx // 2] * u[:, nx // 2]).sum() * dy),
        "east": float((h[:, nx - 1] * u[:, nx - 1]).sum() * dy),
    }


def _field_stats(arrays: dict[str, np.ndarray]) -> dict[str, float]:
    h = arrays["h"].astype(np.float64)
    speed = np.hypot(arrays["u"].astype(np.float64), arrays["v"].astype(np.float64))
    return {
        "h_min_m": float(h.min()),
        "h_max_m": float(h.max()),
        "h_mean_m": float(h.mean()),
        "speed_max_m_per_s": float(speed.max()),
        "wet_fraction": float(arrays["wet_mask"].astype(bool).mean()),
    }


def _band_manifest_entry(
    result: CookedBandResult,
    *,
    output_dir: Path,
    config: CookedFlowFieldsRunConfig,
) -> dict[str, object]:
    scenario = result.scenario
    band_dir = output_dir / result.band_id
    band_dir.mkdir(parents=True, exist_ok=True)

    array_entries: dict[str, object] = {}
    for name, contract in COOKED_ARRAY_CONTRACT.items():
        array = result.arrays[name]
        if str(array.dtype) != contract["dtype"]:
            raise RuntimeError(f"Array '{name}' dtype {array.dtype} violates contract dtype {contract['dtype']}.")
        array_path = band_dir / f"{name}.npy"
        np.save(array_path, array)
        array_entries[name] = {
            "file": f"{result.band_id}/{name}.npy",
            "dtype": contract["dtype"],
            "shape": list(array.shape),
            "units": contract["units"],
            "description": contract["description"],
            "sha256": sha256_of_file(array_path),
        }

    entry: dict[str, object] = {
        "band_id": result.band_id,
        "scenario_id": scenario.metadata.scenario_id,
        "difficulty": scenario.metadata.difficulty_preset,
        "season": scenario.metadata.season_preset,
        "discharge_target_m3s": result.discharge_target_m3s,
        "discharge_steady_m3s": _discharge_profile_m3s(result.arrays, scenario.grid.dy),
        "directory": result.band_id,
        # Roughness the window was solved with. The earlier Chili Bar manifest
        # omitted this, forcing the UE loader to pass Manning n as a parameter;
        # record it per band so the loader can configure friction from the file.
        # The solver applies ``manning_n`` scaled by the run's ``roughness_scale``.
        "manning_n": scenario.roughness,
        "effective_manning_n": scenario.roughness * config.roughness_scale,
        "arrays": array_entries,
        "field_stats": _field_stats(result.arrays),
        "scenario_input_sha256": result.scenario_input_hashes,
        "convergence": {
            "converged": result.converged,
            "window_seconds": config.frame_interval * scenario.fixed_dt,
            "thresholds": config.thresholds.to_json_dict(),
            "windows": [window.to_json_dict() for window in result.windows],
            "final_window": result.windows[-1].to_json_dict(),
        },
    }
    if result.discharge_target_cfs is not None:
        entry["discharge_target_cfs"] = result.discharge_target_cfs
    return entry


def generate_south_fork_cooked_flow_fields(
    *,
    executable: str | Path,
    output_dir: str | Path,
    work_dir: str | Path,
    config: CookedFlowFieldsRunConfig | None = None,
    band_ids: tuple[str, ...] = SOUTH_FORK_COOKED_BAND_IDS,
    source_commit: str | None = None,
) -> Path:
    """Cook all South Fork flow bands and write the v1 package. Returns the manifest path."""

    config = config or CookedFlowFieldsRunConfig()
    executable = Path(executable)
    if not executable.exists():
        raise FileNotFoundError(
            f"C++ solver binary not found at {executable}. Build it with: "
            "cmake -S physics/cpp -B physics/cpp/build && cmake --build physics/cpp/build"
        )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if source_commit is None:
        probe = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent,
        )
        source_commit = probe.stdout.strip() if probe.returncode == 0 else "unknown"

    results = [
        cook_flow_field_band(band_id, executable=executable, work_dir=Path(work_dir), config=config)
        for band_id in band_ids
    ]
    reference = results[0].scenario

    manifest = {
        "schema": COOKED_FLOW_FIELDS_SCHEMA,
        "generator": COOKED_FLOW_FIELDS_GENERATOR,
        "generated_on": date.today().isoformat(),
        "source_commit": source_commit,
        "river_id": reference.metadata.river_id,
        "section_id": reference.metadata.section_id,
        "source_package": "physics/data/real_world/south_fork_american_chili_bar",
        "solver": {
            "solver": "raftsim_water_cpp_v1",
            "binary_sha256": sha256_of_file(executable),
            "solver_mode": config.solver_mode,
            "flux_scheme": config.flux_scheme,
            "spatial_order": config.spatial_order,
            "boundary_mode": config.boundary_mode,
            "cfl": config.cfl,
            "dry_tolerance": config.dry_tolerance,
            "feature_strength_scale": config.feature_strength_scale,
            "roughness_scale": config.roughness_scale,
            "bed_slope_source_scale": config.bed_slope_source_scale,
            "preserve_initial_mass": config.preserve_initial_mass,
            "disable_fixture_calibrations": config.disable_fixture_calibrations,
            "fixed_dt_s": reference.fixed_dt,
            "steps": config.steps,
            "frame_interval_steps": config.frame_interval,
            "simulated_seconds": config.steps * reference.fixed_dt,
        },
        "grid": {
            "nx": reference.grid.nx,
            "ny": reference.grid.ny,
            "dx_m": reference.grid.dx,
            "dy_m": reference.grid.dy,
            "origin_x_m": reference.grid.origin_x,
            "origin_y_m": reference.grid.origin_y,
            "crs": reference.metadata.coordinate_reference_system,
            "layout": "row_major_c_order",
            "index_to_world": "world_x = origin_x_m + col * dx_m; world_y = origin_y_m + row * dy_m (cell-centered samples)",
            "downstream_axis": "+x",
        },
        "bands": [
            _band_manifest_entry(result, output_dir=output_dir, config=config)
            for result in results
        ],
        "notes": [
            "Fields are the genuine finite-volume solver's approximate steady state; no fixture "
            "calibrations, playback, or feature forcing contributed.",
            "The UE river-window loader must run the embedded live solver with this manifest's "
            "solver settings (notably roughness_scale and bed_slope_source_scale); with the "
            "SolverConfig defaults (roughness_scale=1.0, bed_slope_source_scale=0.0) the seed "
            "scenario relaxes to an unphysical upstream circulation instead of downstream flow.",
            "feature_strength_scale is 0: authored rapid forcing is a live layer, not baked "
            "into the base flow field.",
            "The seed window floods its low banks at steady state (wet_fraction ~1.0): the "
            "scenario applies a 0.01 m PyClaw-compatible depth floor bank-wide and the reach "
            "fills until inflow balances outflow. Honest solver output, recorded as-is.",
            "discharge_steady_m3s exceeds discharge_target_m3s per band: the seed scenario's "
            "boundary preset (fixed inflow depth/velocity, fixed outflow stage) over-drives the "
            "gauge-derived target. Recorded honestly; scenario authoring owns any recalibration.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def read_cooked_flow_fields_manifest(package_dir: str | Path) -> dict[str, object]:
    manifest_path = Path(package_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != COOKED_FLOW_FIELDS_SCHEMA:
        raise ValueError(
            f"Unsupported cooked flow fields schema: {manifest.get('schema')!r} "
            f"(expected {COOKED_FLOW_FIELDS_SCHEMA!r})."
        )
    return manifest


def load_cooked_flow_field_band(package_dir: str | Path, band_id: str) -> dict[str, np.ndarray]:
    """Load one band's arrays exactly as the manifest describes them."""

    package_dir = Path(package_dir)
    manifest = read_cooked_flow_fields_manifest(package_dir)
    entry = next((band for band in manifest["bands"] if band["band_id"] == band_id), None)
    if entry is None:
        raise KeyError(f"Band '{band_id}' not present in cooked flow fields manifest.")
    arrays: dict[str, np.ndarray] = {}
    for name, spec in entry["arrays"].items():
        arrays[name] = np.load(package_dir / spec["file"])
    return arrays


def validate_cooked_flow_fields_package(package_dir: str | Path) -> list[str]:
    """Validate manifest/array integrity. Returns a list of problems (empty = valid)."""

    package_dir = Path(package_dir)
    problems: list[str] = []
    try:
        manifest = read_cooked_flow_fields_manifest(package_dir)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"manifest unreadable: {error}"]

    grid = manifest.get("grid", {})
    expected_shape = [grid.get("ny"), grid.get("nx")]
    for band in manifest.get("bands", []):
        band_id = band.get("band_id", "<missing>")
        arrays = band.get("arrays", {})
        missing = sorted(set(COOKED_ARRAY_CONTRACT) - set(arrays))
        if missing:
            problems.append(f"{band_id}: missing contracted arrays {missing}")
        for name, spec in arrays.items():
            path = package_dir / spec["file"]
            if not path.exists():
                problems.append(f"{band_id}/{name}: file missing ({spec['file']})")
                continue
            if sha256_of_file(path) != spec["sha256"]:
                problems.append(f"{band_id}/{name}: sha256 mismatch")
            array = np.load(path)
            if list(array.shape) != list(spec["shape"]) or list(array.shape) != expected_shape:
                problems.append(
                    f"{band_id}/{name}: shape {list(array.shape)} != manifest {spec['shape']} / grid {expected_shape}"
                )
            if str(array.dtype) != spec["dtype"]:
                problems.append(f"{band_id}/{name}: dtype {array.dtype} != manifest {spec['dtype']}")
    return problems
