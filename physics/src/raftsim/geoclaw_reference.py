"""GeoClaw reference-solver setup checks and transition utilities."""

from __future__ import annotations

import importlib
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .cascading import CascadingScenarioPackage2_5D, read_cascading_scenario_package
from .real_world import (
    default_player_selections,
    generate_real_world_scenario2_5d,
    generate_south_fork_american_cascading_seed_scenarios,
)
from .scenario2_5d import (
    Feature2_5D,
    FixtureScenario2_5DParameters,
    Scenario2_5D,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    ProceduralScenario2_5DParameters,
    read_scenario2_5d_package,
)

FloatGrid = NDArray[np.float64]


class GeoClawUnavailableError(RuntimeError):
    """Raised when GeoClaw is required but not available locally."""


@dataclass(frozen=True, slots=True)
class GeoClawAvailability:
    """Machine-readable status for the optional GeoClaw research runtime."""

    available: bool
    reason: str
    required_modules: tuple[str, ...]
    missing_modules: tuple[str, ...] = ()
    module_paths: dict[str, str] = field(default_factory=dict)
    clawpack_version: str | None = None
    required_executables: tuple[str, ...] = ()
    missing_executables: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GeoClawSetupReport:
    """Install/setup guidance attached to a GeoClaw availability check."""

    availability: GeoClawAvailability
    install_hint: str
    system_dependency_hint: str
    reference_docs: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "availability": self.availability.to_json_dict(),
            "install_hint": self.install_hint,
            "system_dependency_hint": self.system_dependency_hint,
            "reference_docs": list(self.reference_docs),
        }


GEOCLAW_REQUIRED_MODULES = (
    "clawpack",
    "clawpack.geoclaw",
    "clawpack.clawutil",
    "clawpack.pyclaw",
)
GEOCLAW_RECOMMENDED_EXECUTABLES = ("make", "gfortran")
GEOCLAW_REFERENCE_DOCS = (
    "https://www.clawpack.org/geoclaw.html",
    "https://www.clawpack.org/setrun_geoclaw.html",
    "https://www.clawpack.org/topo.html",
    "https://www.clawpack.org/fgout.html",
)
GEOCLAW_INSTALL_HINT = 'Install the optional research extra with: python -m pip install -e ".[research]"'
GEOCLAW_SYSTEM_DEPENDENCY_HINT = (
    "GeoClaw runs normally compile Fortran kernels; install a local compiler toolchain "
    "with make and gfortran before running full reference simulations."
)
GEOCLAW_EXPORT_SCHEMA = "raftsim.geoclaw_export.v1"
GEOCLAW_NORMALIZED_OUTPUT_SCHEMA = "raftsim.geoclaw_normalized_output.v1"
GEOCLAW_CASCADING_NORMALIZED_OUTPUT_SCHEMA = "raftsim.geoclaw_cascading_normalized_output.v1"
GEOCLAW_CANONICAL_SUITE_SCHEMA = "raftsim.geoclaw_canonical_suite.v1"
GEOCLAW_RAFTING_SUITE_SCHEMA = "raftsim.geoclaw_rafting_suite.v1"
GEOCLAW_CASCADING_SUITE_SCHEMA = "raftsim.geoclaw_cascading_suite.v1"
GEOCLAW_CANONICAL_FIXTURES = (
    "flat_pool",
    "uniform_channel",
    "dam_break",
    "bed_step",
    "constriction",
    "wet_dry_shoreline",
    "sloping_manning_channel",
    "drop_ledge",
)
GEOCLAW_RAFTING_CASES = (
    "boulder_garden",
    "cascading_wave_train",
    "hydraulic_hole_downstream_boil",
    "lateral_wave",
    "eddy_line_shear",
    "shallow_shelf",
)


@dataclass(frozen=True, slots=True)
class GeoClawExportConfig:
    """Deterministic export settings for a shared 2.5D scenario package."""

    num_output_times: int = 8
    gravity: float = 9.81
    dry_tolerance: float = 1.0e-6
    amr_min_level: int = 1
    amr_max_level: int = 3
    feature_padding_m: float = 3.0
    topography_topotype: int = 1

    def __post_init__(self) -> None:
        if self.num_output_times < 1:
            raise ValueError("num_output_times must be at least 1.")
        if self.gravity <= 0.0:
            raise ValueError("gravity must be positive.")
        if self.dry_tolerance < 0.0:
            raise ValueError("dry_tolerance must be non-negative.")
        if self.amr_min_level < 1:
            raise ValueError("amr_min_level must be at least 1.")
        if self.amr_max_level < self.amr_min_level:
            raise ValueError("amr_max_level must be greater than or equal to amr_min_level.")
        if self.feature_padding_m < 0.0:
            raise ValueError("feature_padding_m must be non-negative.")

    def output_times(self, duration: float) -> tuple[float, ...]:
        return tuple(float(value) for value in np.linspace(0.0, duration, self.num_output_times + 1))

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GeoClawExportResult:
    """Summary returned after exporting a shared scenario to GeoClaw inputs."""

    scenario_id: str
    output_dir: Path
    manifest_path: Path
    files: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "output_dir": str(self.output_dir),
            "manifest_path": str(self.manifest_path),
            "files": list(self.files),
        }


@dataclass(frozen=True, slots=True)
class GeoClawScenarioSuiteExport:
    """Summary for a deterministic suite of GeoClaw scenario exports."""

    suite_id: str
    output_dir: Path
    manifest_path: Path
    results: tuple[GeoClawExportResult, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "suite_id": self.suite_id,
            "output_dir": str(self.output_dir),
            "manifest_path": str(self.manifest_path),
            "scenario_count": len(self.results),
            "scenarios": [result.to_json_dict() for result in self.results],
        }


@dataclass(frozen=True, slots=True)
class GeoClawNormalizedFrame:
    """Comparison-ready fixed-grid GeoClaw frame."""

    time: float
    h: FloatGrid
    eta: FloatGrid
    u: FloatGrid
    v: FloatGrid
    hu: FloatGrid
    hv: FloatGrid
    wet: NDArray[np.bool_]
    normal_x: FloatGrid
    normal_y: FloatGrid
    normal_z: FloatGrid
    froude: FloatGrid

    def __post_init__(self) -> None:
        expected_shape = np.asarray(self.h).shape
        for name in ("h", "eta", "u", "v", "hu", "hv", "normal_x", "normal_y", "normal_z", "froude"):
            array = np.asarray(getattr(self, name), dtype=np.float64)
            if array.shape != expected_shape:
                raise ValueError(f"{name} shape {array.shape} does not match h shape {expected_shape}.")
            object.__setattr__(self, name, array.copy())
        wet = np.asarray(self.wet, dtype=np.bool_)
        if wet.shape != expected_shape:
            raise ValueError(f"wet shape {wet.shape} does not match h shape {expected_shape}.")
        object.__setattr__(self, "wet", wet.copy())

    def mass(self, scenario: Scenario2_5D) -> float:
        return float(np.sum(self.h) * scenario.grid.dx * scenario.grid.dy)

    @property
    def max_velocity(self) -> float:
        return float(np.max(np.sqrt(self.u**2 + self.v**2)))

    @property
    def min_depth(self) -> float:
        return float(np.min(self.h))

    def write_npz(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_path,
            time=np.asarray(self.time, dtype=np.float64),
            h=self.h,
            eta=self.eta,
            u=self.u,
            v=self.v,
            hu=self.hu,
            hv=self.hv,
            wet=self.wet,
            normal_x=self.normal_x,
            normal_y=self.normal_y,
            normal_z=self.normal_z,
            froude=self.froude,
        )
        return output_path


@dataclass(frozen=True, slots=True)
class GeoClawProbeSeries:
    probe_id: str
    kind: str
    times: tuple[float, ...]
    values: dict[str, tuple[float, ...]]
    metadata: dict[str, object] = field(default_factory=dict)

    def write_csv(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        columns = ["time", *self.values.keys()]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            for index, time in enumerate(self.times):
                writer.writerow([time, *[self.values[column][index] for column in self.values]])
        return output_path

    def to_manifest_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "kind": self.kind,
            "sample_count": len(self.times),
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class GeoClawCrossSectionSeries:
    probe_id: str
    times: tuple[float, ...]
    distance: tuple[float, ...]
    h: FloatGrid
    eta: FloatGrid
    u: FloatGrid
    v: FloatGrid
    froude: FloatGrid
    metadata: dict[str, object] = field(default_factory=dict)

    def write_npz(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_path,
            times=np.asarray(self.times, dtype=np.float64),
            distance=np.asarray(self.distance, dtype=np.float64),
            h=self.h,
            eta=self.eta,
            u=self.u,
            v=self.v,
            froude=self.froude,
        )
        return output_path

    def to_manifest_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "time_count": len(self.times),
            "distance_count": len(self.distance),
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class GeoClawNormalizedOutputResult:
    scenario_id: str
    output_dir: Path
    manifest_path: Path
    frame_count: int
    probe_count: int
    cross_section_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "output_dir": str(self.output_dir),
            "manifest_path": str(self.manifest_path),
            "frame_count": self.frame_count,
            "probe_count": self.probe_count,
            "cross_section_count": self.cross_section_count,
        }


@dataclass(frozen=True, slots=True)
class GeoClawCascadingNormalizedOutputResult:
    scenario_id: str
    output_dir: Path
    manifest_path: Path
    stitched_manifest_path: Path
    reach_window_count: int
    drop_transition_window_count: int
    frame_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "output_dir": str(self.output_dir),
            "manifest_path": str(self.manifest_path),
            "stitched_manifest_path": str(self.stitched_manifest_path),
            "reach_window_count": self.reach_window_count,
            "drop_transition_window_count": self.drop_transition_window_count,
            "frame_count": self.frame_count,
        }


@dataclass(frozen=True, slots=True)
class GeoClawRunConfig:
    """Execution settings for a generated GeoClaw app directory."""

    claw_root: Path | None = None
    timeout_seconds: float = 300.0
    clean_output: bool = True
    make_target: str = ".output"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "claw_root": str(self.claw_root) if self.claw_root is not None else None,
            "timeout_seconds": self.timeout_seconds,
            "clean_output": self.clean_output,
            "make_target": self.make_target,
        }


@dataclass(frozen=True, slots=True)
class GeoClawRunResult:
    """Summary returned after executing GeoClaw and extracting fgout frames."""

    scenario_id: str
    export_dir: Path
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    runtime_seconds: float
    output_dir: Path
    frame_dir: Path
    frame_count: int

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and self.frame_count > 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "export_dir": str(self.export_dir),
            "command": list(self.command),
            "returncode": self.returncode,
            "runtime_seconds": self.runtime_seconds,
            "output_dir": str(self.output_dir),
            "frame_dir": str(self.frame_dir),
            "frame_count": self.frame_count,
            "passed": self.passed,
            "stdout_tail": self.stdout[-4000:],
            "stderr_tail": self.stderr[-4000:],
        }


def check_geoclaw_availability() -> GeoClawAvailability:
    """Return whether the optional Clawpack/GeoClaw runtime can be imported."""

    missing_modules: list[str] = []
    module_paths: dict[str, str] = {}
    imported_modules: dict[str, object] = {}
    for module_name in GEOCLAW_REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception:  # pragma: no cover - exact import failure varies by install.
            missing_modules.append(module_name)
            continue
        imported_modules[module_name] = module
        module_file = getattr(module, "__file__", None)
        if module_file:
            module_paths[module_name] = str(module_file)

    missing_executables = tuple(
        executable for executable in GEOCLAW_RECOMMENDED_EXECUTABLES if shutil.which(executable) is None
    )
    clawpack = imported_modules.get("clawpack")
    version = str(getattr(clawpack, "__version__", "")) or None if clawpack is not None else None

    if missing_modules:
        return GeoClawAvailability(
            False,
            "Missing required Python modules: " + ", ".join(missing_modules),
            required_modules=GEOCLAW_REQUIRED_MODULES,
            missing_modules=tuple(missing_modules),
            module_paths=module_paths,
            clawpack_version=version,
            required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
            missing_executables=missing_executables,
        )
    if missing_executables:
        return GeoClawAvailability(
            False,
            "Missing recommended GeoClaw build executables: " + ", ".join(missing_executables),
            required_modules=GEOCLAW_REQUIRED_MODULES,
            module_paths=module_paths,
            clawpack_version=version,
            required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
            missing_executables=missing_executables,
        )
    return GeoClawAvailability(
        True,
        "GeoClaw modules and recommended build executables are available.",
        required_modules=GEOCLAW_REQUIRED_MODULES,
        module_paths=module_paths,
        clawpack_version=version,
        required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
    )


def build_geoclaw_setup_report(availability: GeoClawAvailability | None = None) -> GeoClawSetupReport:
    """Build a setup report for CLI checks and readiness artifacts."""

    return GeoClawSetupReport(
        availability=availability or check_geoclaw_availability(),
        install_hint=GEOCLAW_INSTALL_HINT,
        system_dependency_hint=GEOCLAW_SYSTEM_DEPENDENCY_HINT,
        reference_docs=GEOCLAW_REFERENCE_DOCS,
    )


def write_geoclaw_setup_report(directory: str | Path, availability: GeoClawAvailability | None = None) -> Path:
    """Write a machine-readable GeoClaw setup report."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_geoclaw_setup_report(availability)
    path = output_dir / "geoclaw_setup_report.json"
    path.write_text(json.dumps(report.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def export_geoclaw_scenario(
    scenario_or_path: Scenario2_5D | str | Path,
    output_dir: str | Path,
    *,
    config: GeoClawExportConfig | None = None,
) -> GeoClawExportResult:
    """Export a solver-neutral 2.5D scenario package into GeoClaw input files."""

    scenario = read_scenario2_5d_package(scenario_or_path) if not isinstance(scenario_or_path, Scenario2_5D) else scenario_or_path
    validation = scenario.validate()
    if not validation.passed:
        details = "; ".join(validation.summary_lines())
        raise ValueError(f"Cannot export invalid scenario to GeoClaw: {details}")

    cfg = config or GeoClawExportConfig()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    files: list[str] = []
    files.extend(_write_shared_scenario_package(scenario, root))
    files.append(_relative_path(_write_makefile(root), root))
    files.append(_relative_path(_write_setrun_py(scenario, cfg, root), root))
    files.append(_relative_path(_write_qinit_f90(scenario, root), root))
    files.append(_relative_path(_write_topography(scenario, root), root))
    files.append(_relative_path(_write_initial_state_npz(scenario, root), root))
    files.append(_relative_path(_write_qinit_xyz(scenario, root), root))
    files.append(_relative_path(_write_roughness_grid(scenario, root), root))
    files.extend(_write_boundaries(scenario, root))
    files.append(_relative_path(_write_amr_regions(scenario, cfg, root), root))
    files.append(_relative_path(_write_fixed_grid_output(scenario, cfg, root), root))

    manifest = {
        "schema": GEOCLAW_EXPORT_SCHEMA,
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_metadata": scenario.metadata.to_json_dict(),
        "config": cfg.to_json_dict(),
        "files": {
            "makefile": "Makefile",
            "setrun": "setrun.py",
            "qinit_fortran": "qinit.f90",
            "topography": "b.tt1",
            "initial_state": "initial_state/initial_water_state.npz",
            "qinit": "initial_state/qinit.xyz",
            "roughness": "roughness/manning_n.npy",
            "boundaries": "boundaries/boundaries.json",
            "amr_regions": "amr/amr_regions.json",
            "fixed_grid_output": "fgout/fgout_grids.json",
            "shared_scenario": "shared_scenario/scenario.json",
        },
        "exported_files": sorted(files),
        "notes": [
            "GeoClaw is the active offline reference target.",
            "This package is generated from the shared solver-neutral scenario; do not edit exported inputs by hand.",
            "The custom C++ solver must be validated against normalized GeoClaw fixed-grid outputs from this scenario.",
        ],
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    files.append("manifest.json")
    return GeoClawExportResult(
        scenario_id=scenario.metadata.scenario_id,
        output_dir=root,
        manifest_path=manifest_path,
        files=tuple(sorted(files)),
    )


def export_geoclaw_cascading_package(
    package: CascadingScenarioPackage2_5D,
    output_dir: str | Path,
    *,
    config: GeoClawExportConfig | None = None,
) -> GeoClawExportResult:
    """Export a cascading package to GeoClaw inputs while preserving reach/drop annotations."""

    result = export_geoclaw_scenario(package.scenario, output_dir, config=config)
    root = result.output_dir
    cascading_dir = package.write_package(root / "shared_cascading_package")
    cascading_files = sorted(_relative_path(path, root) for path in cascading_dir.iterdir() if path.is_file())
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["shared_cascading_package"] = "shared_cascading_package/cascading_metadata.json"
    manifest["cascading_package"] = {
        "schema": "raftsim.geoclaw_cascading_export.v1",
        "metadata": "shared_cascading_package/cascading_metadata.json",
        "annotations": "shared_cascading_package/cascading_annotations.npz",
        "reach_count": len(package.reaches),
        "drop_transition_count": len(package.drop_transitions),
        "reach_ids": [reach.reach_id for reach in package.reaches],
        "drop_transition_ids": [transition.transition_id for transition in package.drop_transitions],
    }
    manifest["exported_files"] = sorted(set((*manifest["exported_files"], *cascading_files)))
    _write_json(result.manifest_path, manifest)
    return GeoClawExportResult(
        scenario_id=result.scenario_id,
        output_dir=root,
        manifest_path=result.manifest_path,
        files=tuple(manifest["exported_files"]),
    )


def cascading_geoclaw_scenarios(
    *,
    nx: int = 112,
    ny: int = 40,
    dx: float = 4.0,
    dy: float = 2.0,
    duration: float = 8.0,
) -> tuple[CascadingScenarioPackage2_5D, ...]:
    """Return South Fork American cascading packages for GeoClaw reference export."""

    return generate_south_fork_american_cascading_seed_scenarios(
        nx=nx,
        ny=ny,
        dx=dx,
        dy=dy,
        duration=duration,
    )


def export_cascading_geoclaw_scenarios(
    output_dir: str | Path,
    *,
    config: GeoClawExportConfig | None = None,
    nx: int = 112,
    ny: int = 40,
    dx: float = 4.0,
    dy: float = 2.0,
    duration: float = 8.0,
) -> GeoClawScenarioSuiteExport:
    """Export South Fork cascading flow packages for GeoClaw reference runs."""

    cfg = config or GeoClawExportConfig()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    packages = cascading_geoclaw_scenarios(nx=nx, ny=ny, dx=dx, dy=dy, duration=duration)
    results = tuple(
        export_geoclaw_cascading_package(package, root / package.scenario.metadata.scenario_id, config=cfg)
        for package in packages
    )
    manifest = {
        "schema": GEOCLAW_CASCADING_SUITE_SCHEMA,
        "suite_id": "south_fork_cascading_geoclaw",
        "scenario_count": len(results),
        "flow_bands": [package.scenario.metadata.flow_band for package in packages],
        "config": cfg.to_json_dict(),
        "exports": [
            {
                "scenario_id": result.scenario_id,
                "flow_band": packages[index].scenario.metadata.flow_band,
                "difficulty": packages[index].scenario.metadata.difficulty_preset,
                "manifest": _relative_path(result.manifest_path, root),
                "reach_count": len(packages[index].reaches),
                "drop_transition_count": len(packages[index].drop_transitions),
                "file_count": len(result.files),
            }
            for index, result in enumerate(results)
        ],
    }
    manifest_path = root / "cascading_suite_manifest.json"
    _write_json(manifest_path, manifest)
    return GeoClawScenarioSuiteExport(
        suite_id="south_fork_cascading_geoclaw",
        output_dir=root,
        manifest_path=manifest_path,
        results=results,
    )


def run_geoclaw_export(
    geoclaw_export_dir: str | Path,
    *,
    config: GeoClawRunConfig | None = None,
    export_config: GeoClawExportConfig | None = None,
) -> GeoClawRunResult:
    """Execute a generated GeoClaw app directory and extract fgout frames."""

    cfg = config or GeoClawRunConfig()
    export_root = Path(geoclaw_export_dir)
    manifest_path = export_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"GeoClaw export manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(export_root / "shared_scenario")

    if cfg.clean_output:
        for path in (export_root / "_output", export_root / "fgout_frames"):
            if path.exists():
                shutil.rmtree(path)
        for marker in (".output", ".data"):
            marker_path = export_root / marker
            if marker_path.exists():
                marker_path.unlink()

    env = _geoclaw_subprocess_env(cfg.claw_root)
    command = ("make", cfg.make_target)
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=export_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=cfg.timeout_seconds,
    )
    runtime_seconds = time.perf_counter() - start
    frame_count = 0
    if completed.returncode == 0:
        frame_count = _extract_geoclaw_fgout_frames(
            export_root,
            scenario,
            config=export_config,
        )
    run_manifest = {
        "schema": "raftsim.geoclaw_run.v1",
        "source_export_schema": manifest.get("schema"),
        "config": cfg.to_json_dict(),
        "result": {
            "command": list(command),
            "returncode": completed.returncode,
            "runtime_seconds": runtime_seconds,
            "frame_count": frame_count,
        },
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    _write_json(export_root / "geoclaw_run_manifest.json", run_manifest)
    return GeoClawRunResult(
        scenario_id=scenario.metadata.scenario_id,
        export_dir=export_root,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        runtime_seconds=runtime_seconds,
        output_dir=export_root / "_output",
        frame_dir=export_root / "fgout_frames",
        frame_count=frame_count,
    )


def canonical_geoclaw_scenarios(seed: int = 1) -> tuple[Scenario2_5D, ...]:
    """Return the canonical GeoClaw fixture set for C++ validation."""

    return tuple(
        generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture=fixture, seed=seed))
        for fixture in GEOCLAW_CANONICAL_FIXTURES
    )


def export_canonical_geoclaw_scenarios(
    output_dir: str | Path,
    *,
    seed: int = 1,
    config: GeoClawExportConfig | None = None,
) -> GeoClawScenarioSuiteExport:
    """Export every canonical GeoClaw fixture to deterministic run packages."""

    cfg = config or GeoClawExportConfig()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    results = tuple(
        export_geoclaw_scenario(scenario, root / scenario.metadata.scenario_id, config=cfg)
        for scenario in canonical_geoclaw_scenarios(seed=seed)
    )
    manifest = {
        "schema": GEOCLAW_CANONICAL_SUITE_SCHEMA,
        "suite_id": f"canonical_geoclaw_seed_{seed}",
        "seed": seed,
        "fixtures": list(GEOCLAW_CANONICAL_FIXTURES),
        "scenario_count": len(results),
        "config": cfg.to_json_dict(),
        "exports": [
            {
                "scenario_id": result.scenario_id,
                "manifest": _relative_path(result.manifest_path, root),
                "file_count": len(result.files),
            }
            for result in results
        ],
    }
    manifest_path = root / "canonical_suite_manifest.json"
    _write_json(manifest_path, manifest)
    return GeoClawScenarioSuiteExport(
        suite_id=f"canonical_geoclaw_seed_{seed}",
        output_dir=root,
        manifest_path=manifest_path,
        results=results,
    )


def rafting_geoclaw_scenarios(seed: int = 1) -> tuple[Scenario2_5D, ...]:
    """Return feature-heavy rafting and real-world flow scenarios for GeoClaw."""

    synthetic = tuple(_rafting_case_scenario(case_id, seed + index) for index, case_id in enumerate(GEOCLAW_RAFTING_CASES))
    real_world = tuple(
        generate_real_world_scenario2_5d(
            selection,
            nx=48,
            ny=24,
            duration=6.0,
            pyclaw_reference_min_depth_m=0.0,
        )
        for selection in default_player_selections()
    )
    return (*synthetic, *real_world)


def export_rafting_geoclaw_scenarios(
    output_dir: str | Path,
    *,
    seed: int = 1,
    config: GeoClawExportConfig | None = None,
) -> GeoClawScenarioSuiteExport:
    """Export synthetic rafting cases and real-world flow bands for GeoClaw."""

    cfg = config or GeoClawExportConfig()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    scenarios = rafting_geoclaw_scenarios(seed=seed)
    results = tuple(export_geoclaw_scenario(scenario, root / scenario.metadata.scenario_id, config=cfg) for scenario in scenarios)
    manifest = {
        "schema": GEOCLAW_RAFTING_SUITE_SCHEMA,
        "suite_id": f"rafting_geoclaw_seed_{seed}",
        "seed": seed,
        "synthetic_cases": list(GEOCLAW_RAFTING_CASES),
        "real_world_flow_bands": [
            scenario.metadata.flow_band
            for scenario in scenarios
            if scenario.metadata.scenario_type == "real_world"
        ],
        "scenario_count": len(results),
        "config": cfg.to_json_dict(),
        "exports": [
            {
                "scenario_id": result.scenario_id,
                "scenario_type": scenarios[index].metadata.scenario_type,
                "flow_band": scenarios[index].metadata.flow_band,
                "manifest": _relative_path(result.manifest_path, root),
                "file_count": len(result.files),
            }
            for index, result in enumerate(results)
        ],
    }
    manifest_path = root / "rafting_suite_manifest.json"
    _write_json(manifest_path, manifest)
    return GeoClawScenarioSuiteExport(
        suite_id=f"rafting_geoclaw_seed_{seed}",
        output_dir=root,
        manifest_path=manifest_path,
        results=results,
    )


def normalize_geoclaw_fixed_grid_output(
    geoclaw_export_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    config: GeoClawExportConfig | None = None,
) -> GeoClawNormalizedOutputResult:
    """Normalize GeoClaw fixed-grid frames into the frozen telemetry schema."""

    export_root = Path(geoclaw_export_dir)
    export_manifest_path = export_root / "manifest.json"
    if not export_manifest_path.exists():
        raise FileNotFoundError(f"GeoClaw export manifest not found: {export_manifest_path}")
    export_manifest = json.loads(export_manifest_path.read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(export_root / "shared_scenario")
    cfg = config or GeoClawExportConfig()
    if not (export_root / "fgout_frames").exists() and (export_root / "_output").exists():
        _extract_geoclaw_fgout_frames(export_root, scenario, config=cfg)
    frames = _load_geoclaw_fgout_frames(export_root, scenario, cfg)
    if not frames:
        frames = (frame_from_geoclaw_initial_state(scenario, config=cfg),)

    probes, cross_sections = _sample_normalized_outputs(scenario, frames)
    root = Path(output_dir) if output_dir is not None else export_root / "normalized"
    root.mkdir(parents=True, exist_ok=True)

    frame_files: list[str] = []
    for index, frame in enumerate(frames):
        relative = Path("frames") / f"frame_{index:04d}.npz"
        frame.write_npz(root / relative)
        frame_files.append(relative.as_posix())

    probe_files: list[str] = []
    for probe in probes:
        relative = Path("probes") / f"{probe.probe_id}.csv"
        probe.write_csv(root / relative)
        probe_files.append(relative.as_posix())

    cross_section_files: list[str] = []
    for cross_section in cross_sections:
        relative = Path("cross_sections") / f"{cross_section.probe_id}.npz"
        cross_section.write_npz(root / relative)
        cross_section_files.append(relative.as_posix())

    validation = _normalized_validation(scenario, frames)
    _write_json(root / "validation.json", validation)
    manifest = {
        "schema": GEOCLAW_NORMALIZED_OUTPUT_SCHEMA,
        "scenario_id": scenario.metadata.scenario_id,
        "source_export_manifest": str(export_manifest_path),
        "source_export_schema": export_manifest.get("schema"),
        "run_status": {
            "mode": "fgout_npz" if (export_root / "fgout_frames").exists() else "export_initial_state_only",
            "frame_count": len(frames),
        },
        "config": cfg.to_json_dict(),
        "validation": "validation.json",
        "frames": frame_files,
        "probes": probe_files,
        "cross_sections": cross_section_files,
        "probe_manifest": [probe.to_manifest_dict() for probe in probes],
        "cross_section_manifest": [cross_section.to_manifest_dict() for cross_section in cross_sections],
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    return GeoClawNormalizedOutputResult(
        scenario_id=scenario.metadata.scenario_id,
        output_dir=root,
        manifest_path=manifest_path,
        frame_count=len(frames),
        probe_count=len(probes),
        cross_section_count=len(cross_sections),
    )


def normalize_geoclaw_cascading_fixed_grid_output(
    geoclaw_export_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    config: GeoClawExportConfig | None = None,
) -> GeoClawCascadingNormalizedOutputResult:
    """Normalize a cascading GeoClaw export into stitched and reach-local windows."""

    export_root = Path(geoclaw_export_dir)
    export_manifest_path = export_root / "manifest.json"
    cascading_dir = export_root / "shared_cascading_package"
    if not export_manifest_path.exists():
        raise FileNotFoundError(f"GeoClaw export manifest not found: {export_manifest_path}")
    if not cascading_dir.exists():
        raise FileNotFoundError(f"Cascading package not found in GeoClaw export: {cascading_dir}")

    cfg = config or GeoClawExportConfig()
    package = read_cascading_scenario_package(cascading_dir)
    root = Path(output_dir) if output_dir is not None else export_root / "cascading_normalized"
    root.mkdir(parents=True, exist_ok=True)
    stitched = normalize_geoclaw_fixed_grid_output(export_root, root / "stitched", config=cfg)
    frames = _load_geoclaw_fgout_frames(export_root, package.scenario, cfg)
    if not frames:
        frames = (frame_from_geoclaw_initial_state(package.scenario, config=cfg),)

    reach_windows = _write_cascading_frame_windows(
        root,
        "reach_windows",
        package.scenario,
        frames,
        package.reach_id_grid,
        tuple(range(len(package.reaches))),
        lambda index: package.reaches[index].reach_id,
        lambda index: {
            "reach_id": package.reaches[index].reach_id,
            "kind": package.reaches[index].kind,
            "station_start": package.reaches[index].station_start,
            "station_end": package.reaches[index].station_end,
            "metadata": package.reaches[index].metadata,
        },
    )
    drop_windows = _write_cascading_frame_windows(
        root,
        "drop_transition_windows",
        package.scenario,
        frames,
        package.drop_transition_id_grid,
        tuple(range(len(package.drop_transitions))),
        lambda index: package.drop_transitions[index].transition_id,
        lambda index: {
            "transition_id": package.drop_transitions[index].transition_id,
            "upstream_reach_id": package.drop_transitions[index].upstream_reach_id,
            "downstream_reach_id": package.drop_transitions[index].downstream_reach_id,
            "crest_station": package.drop_transitions[index].crest_station,
            "bed_elevation_fall": package.drop_transitions[index].bed_elevation_fall,
            "hazard_tags": list(package.drop_transitions[index].hazard_tags),
            "metadata": package.drop_transitions[index].metadata,
        },
    )
    export_manifest = json.loads(export_manifest_path.read_text(encoding="utf-8"))
    manifest = {
        "schema": GEOCLAW_CASCADING_NORMALIZED_OUTPUT_SCHEMA,
        "scenario_id": package.scenario.metadata.scenario_id,
        "source_export_manifest": str(export_manifest_path),
        "source_export_schema": export_manifest.get("schema"),
        "stitched_manifest": _relative_path(stitched.manifest_path, root),
        "run_status": {
            "mode": "fgout_npz" if (export_root / "fgout_frames").exists() else "export_initial_state_only",
            "frame_count": len(frames),
        },
        "config": cfg.to_json_dict(),
        "reach_windows": reach_windows,
        "drop_transition_windows": drop_windows,
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    return GeoClawCascadingNormalizedOutputResult(
        scenario_id=package.scenario.metadata.scenario_id,
        output_dir=root,
        manifest_path=manifest_path,
        stitched_manifest_path=stitched.manifest_path,
        reach_window_count=len(reach_windows),
        drop_transition_window_count=len(drop_windows),
        frame_count=len(frames),
    )


def frame_from_geoclaw_initial_state(
    scenario: Scenario2_5D,
    *,
    time: float = 0.0,
    config: GeoClawExportConfig | None = None,
) -> GeoClawNormalizedFrame:
    """Build a normalized GeoClaw frame from a shared scenario initial state."""

    cfg = config or GeoClawExportConfig()
    return _normalized_frame_from_h_momentum(
        scenario,
        h=scenario.initial_state.depth,
        hu=scenario.initial_state.hu,
        hv=scenario.initial_state.hv,
        time=time,
        config=cfg,
    )


def _rafting_case_scenario(case_id: str, seed: int) -> Scenario2_5D:
    base = generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(
            seed=seed,
            nx=72,
            ny=36,
            difficulty=0.72,
            feature_count=9,
            duration=8.0,
        )
    )
    metadata = replace(
        base.metadata,
        scenario_id=f"{case_id}_seed_{seed}",
        description=f"GeoClaw rafting fixture focused on {case_id.replace('_', ' ')}.",
        provenance={
            **base.metadata.provenance,
            "geoclaw_rafting_case": case_id,
            "source": "geoclaw_rafting_fixture_generator",
        },
    )
    return replace(base, metadata=metadata, features=(*base.features, *_focus_features(base, case_id)))


def _focus_features(scenario: Scenario2_5D, case_id: str) -> tuple[Feature2_5D, ...]:
    x0, y0 = scenario.grid.center
    x_span = max((scenario.grid.nx - 1) * scenario.grid.dx, scenario.grid.dx)
    y_span = max((scenario.grid.ny - 1) * scenario.grid.dy, scenario.grid.dy)
    radius = max(1.5 * scenario.grid.dx, 0.07 * y_span)
    if case_id == "boulder_garden":
        offsets = (-0.18, -0.08, 0.02, 0.12, 0.22)
        return tuple(
            Feature2_5D(
                kind="rock",
                center=(x0 + x_span * offset, y0 + ((index % 2) - 0.5) * y_span * 0.18),
                radius=radius,
                strength=1.25,
                metadata={"geoclaw_case_role": "boulder_garden"},
            )
            for index, offset in enumerate(offsets)
        )
    if case_id == "cascading_wave_train":
        return (
            Feature2_5D(
                kind="wave_train",
                center=(x0, y0),
                radius=radius * 1.4,
                strength=1.45,
                length=x_span * 0.42,
                width=y_span * 0.48,
                metadata={"geoclaw_case_role": "cascading_wave_train"},
            ),
        )
    if case_id == "hydraulic_hole_downstream_boil":
        return (
            Feature2_5D(
                kind="hole",
                center=(x0 - x_span * 0.06, y0),
                radius=radius * 1.25,
                strength=1.35,
                length=x_span * 0.14,
                width=y_span * 0.32,
                metadata={"geoclaw_case_role": "hydraulic_hole"},
            ),
            Feature2_5D(
                kind="boil",
                center=(x0 + x_span * 0.08, y0),
                radius=radius * 1.35,
                strength=1.15,
                length=x_span * 0.16,
                width=y_span * 0.34,
                metadata={"geoclaw_case_role": "downstream_boil"},
            ),
        )
    if case_id == "lateral_wave":
        return (
            Feature2_5D(
                kind="lateral",
                center=(x0, y0 + y_span * 0.17),
                radius=radius * 1.2,
                strength=1.35,
                length=x_span * 0.20,
                width=y_span * 0.38,
                angle=-0.55,
                metadata={"geoclaw_case_role": "lateral_wave"},
            ),
        )
    if case_id == "eddy_line_shear":
        return (
            Feature2_5D(
                kind="eddy_line",
                center=(x0, y0 - y_span * 0.18),
                radius=radius * 1.4,
                strength=1.30,
                length=x_span * 0.28,
                width=y_span * 0.22,
                metadata={"geoclaw_case_role": "eddy_line_shear"},
            ),
        )
    if case_id == "shallow_shelf":
        return (
            Feature2_5D(
                kind="shallow",
                center=(x0 + x_span * 0.05, y0 + y_span * 0.20),
                radius=radius * 1.6,
                strength=1.30,
                length=x_span * 0.30,
                width=y_span * 0.30,
                metadata={"geoclaw_case_role": "shallow_shelf"},
            ),
        )
    raise ValueError(f"Unknown GeoClaw rafting case: {case_id}")


def _write_cascading_frame_windows(
    root: Path,
    prefix: str,
    scenario: Scenario2_5D,
    frames: tuple[GeoClawNormalizedFrame, ...],
    id_grid: NDArray[np.int32],
    indices: tuple[int, ...],
    id_for_index,
    metadata_for_index,
) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    for index in indices:
        mask = id_grid == index
        if not bool(np.any(mask)):
            continue
        rows = np.flatnonzero(np.any(mask, axis=1))
        columns = np.flatnonzero(np.any(mask, axis=0))
        row_slice = slice(int(rows[0]), int(rows[-1]) + 1)
        column_slice = slice(int(columns[0]), int(columns[-1]) + 1)
        window_id = str(id_for_index(index))
        frame_files: list[str] = []
        for frame_index, frame in enumerate(frames):
            relative = Path(prefix) / window_id / "frames" / f"frame_{frame_index:04d}.npz"
            _slice_normalized_frame(frame, row_slice, column_slice).write_npz(root / relative)
            frame_files.append(relative.as_posix())
        windows.append(
            {
                **metadata_for_index(index),
                "index": index,
                "bounds": _cascading_window_bounds(scenario, row_slice, column_slice),
                "frames": frame_files,
            }
        )
    return windows


def _slice_normalized_frame(
    frame: GeoClawNormalizedFrame,
    row_slice: slice,
    column_slice: slice,
) -> GeoClawNormalizedFrame:
    return GeoClawNormalizedFrame(
        time=frame.time,
        h=frame.h[row_slice, column_slice],
        eta=frame.eta[row_slice, column_slice],
        u=frame.u[row_slice, column_slice],
        v=frame.v[row_slice, column_slice],
        hu=frame.hu[row_slice, column_slice],
        hv=frame.hv[row_slice, column_slice],
        wet=frame.wet[row_slice, column_slice],
        normal_x=frame.normal_x[row_slice, column_slice],
        normal_y=frame.normal_y[row_slice, column_slice],
        normal_z=frame.normal_z[row_slice, column_slice],
        froude=frame.froude[row_slice, column_slice],
    )


def _cascading_window_bounds(
    scenario: Scenario2_5D,
    row_slice: slice,
    column_slice: slice,
) -> dict[str, object]:
    rows = (int(row_slice.start), int(row_slice.stop) - 1)
    columns = (int(column_slice.start), int(column_slice.stop) - 1)
    xs = scenario.grid.x_coordinates()
    ys = scenario.grid.y_coordinates()
    return {
        "row_min": rows[0],
        "row_max": rows[1],
        "column_min": columns[0],
        "column_max": columns[1],
        "x_min": float(xs[columns[0]]),
        "x_max": float(xs[columns[1]]),
        "y_min": float(ys[rows[0]]),
        "y_max": float(ys[rows[1]]),
    }


def _load_geoclaw_fgout_frames(
    export_root: Path,
    scenario: Scenario2_5D,
    config: GeoClawExportConfig,
) -> tuple[GeoClawNormalizedFrame, ...]:
    frame_dir = export_root / "fgout_frames"
    if not frame_dir.exists():
        return ()
    frames: list[GeoClawNormalizedFrame] = []
    for frame_path in sorted(frame_dir.glob("*.npz")):
        with np.load(frame_path) as data:
            time = float(np.asarray(data["time"])) if "time" in data else float(len(frames))
            h = np.asarray(data["h"], dtype=np.float64)
            hu = np.asarray(data["hu"], dtype=np.float64) if "hu" in data else h * np.asarray(data["u"], dtype=np.float64)
            hv = np.asarray(data["hv"], dtype=np.float64) if "hv" in data else h * np.asarray(data["v"], dtype=np.float64)
        frames.append(_normalized_frame_from_h_momentum(scenario, h=h, hu=hu, hv=hv, time=time, config=config))
    return tuple(frames)


def _normalized_frame_from_h_momentum(
    scenario: Scenario2_5D,
    *,
    h: FloatGrid,
    hu: FloatGrid,
    hv: FloatGrid,
    time: float,
    config: GeoClawExportConfig,
) -> GeoClawNormalizedFrame:
    h_grid = np.maximum(np.asarray(h, dtype=np.float64), 0.0)
    hu_grid = np.asarray(hu, dtype=np.float64)
    hv_grid = np.asarray(hv, dtype=np.float64)
    wet = h_grid > config.dry_tolerance
    u = np.where(wet, hu_grid / np.maximum(h_grid, config.dry_tolerance), 0.0)
    v = np.where(wet, hv_grid / np.maximum(h_grid, config.dry_tolerance), 0.0)
    eta = scenario.bed + h_grid
    normal_x, normal_y, normal_z = _surface_normals(eta, scenario.grid.dx, scenario.grid.dy)
    speed = np.sqrt(u**2 + v**2)
    froude = np.where(wet, speed / np.sqrt(np.maximum(config.gravity * h_grid, config.dry_tolerance)), 0.0)
    return GeoClawNormalizedFrame(
        time=time,
        h=h_grid,
        eta=eta,
        u=u,
        v=v,
        hu=hu_grid,
        hv=hv_grid,
        wet=wet,
        normal_x=normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        froude=froude,
    )


def _sample_normalized_outputs(
    scenario: Scenario2_5D,
    frames: tuple[GeoClawNormalizedFrame, ...],
) -> tuple[tuple[GeoClawProbeSeries, ...], tuple[GeoClawCrossSectionSeries, ...]]:
    point_probes: list[GeoClawProbeSeries] = []
    cross_sections: list[GeoClawCrossSectionSeries] = []
    for probe in scenario.probes:
        if probe.kind == "cross_section":
            cross_sections.append(_sample_normalized_cross_section(scenario, frames, probe))
        else:
            point_probes.append(_sample_normalized_point_probe(scenario, frames, probe))
    return tuple(point_probes), tuple(cross_sections)


def _sample_normalized_point_probe(
    scenario: Scenario2_5D,
    frames: tuple[GeoClawNormalizedFrame, ...],
    probe,
) -> GeoClawProbeSeries:
    row, column = _grid_index_for_position(scenario, probe.position)
    field_names = ("h", "eta", "u", "v", "hu", "hv", "wet", "froude")
    values: dict[str, tuple[float, ...]] = {}
    for name in field_names:
        values[name] = tuple(float(getattr(frame, name)[row, column]) for frame in frames)
    return GeoClawProbeSeries(
        probe_id=probe.probe_id,
        kind=probe.kind,
        times=tuple(frame.time for frame in frames),
        values=values,
        metadata={"row": row, "column": column, "position": probe.position},
    )


def _sample_normalized_cross_section(
    scenario: Scenario2_5D,
    frames: tuple[GeoClawNormalizedFrame, ...],
    probe,
) -> GeoClawCrossSectionSeries:
    normal = probe.normal or (0.0, 1.0)
    length = probe.length or (scenario.grid.ny - 1) * scenario.grid.dy
    normal_length = math.hypot(normal[0], normal[1]) or 1.0
    unit_normal = (normal[0] / normal_length, normal[1] / normal_length)
    sample_count = max(2, int(length / min(scenario.grid.dx, scenario.grid.dy)) + 1)
    distance = np.linspace(-length * 0.5, length * 0.5, sample_count, dtype=np.float64)
    positions = [
        (
            probe.position[0] + unit_normal[0] * float(offset),
            probe.position[1] + unit_normal[1] * float(offset),
        )
        for offset in distance
    ]
    indices = [_grid_index_for_position(scenario, position) for position in positions]

    def sample_field(field_name: str) -> FloatGrid:
        data = np.zeros((len(frames), sample_count), dtype=np.float64)
        for frame_index, frame in enumerate(frames):
            field = getattr(frame, field_name)
            for sample_index, (row, column) in enumerate(indices):
                data[frame_index, sample_index] = float(field[row, column])
        return data

    return GeoClawCrossSectionSeries(
        probe_id=probe.probe_id,
        times=tuple(frame.time for frame in frames),
        distance=tuple(float(value) for value in distance),
        h=sample_field("h"),
        eta=sample_field("eta"),
        u=sample_field("u"),
        v=sample_field("v"),
        froude=sample_field("froude"),
        metadata={"position": probe.position, "normal": unit_normal, "length": length},
    )


def _geoclaw_subprocess_env(claw_root: Path | None) -> dict[str, str]:
    env = os.environ.copy()
    root = Path(claw_root or env.get("CLAW", "") or "/Users/alexmoran/repos/clawpack").expanduser()
    if root.exists():
        env["CLAW"] = str(root)
        build_path = root / "build" / f"cp{sys.version_info.major}{sys.version_info.minor}"
        if build_path.exists():
            env["MESONPY_EDITABLE_SKIP"] = os.pathsep.join(
                value
                for value in (env.get("MESONPY_EDITABLE_SKIP", ""), str(build_path))
                if value
            )
        python_paths = [
            str(root),
            str(Path(__file__).resolve().parents[1]),
            env.get("PYTHONPATH", ""),
        ]
        env["PYTHONPATH"] = os.pathsep.join(path for path in python_paths if path)
    env["CLAW_PYTHON"] = sys.executable
    return env


def _extract_geoclaw_fgout_frames(
    export_root: Path,
    scenario: Scenario2_5D,
    *,
    config: GeoClawExportConfig | None = None,
) -> int:
    output_dir = export_root / "_output"
    if not output_dir.exists():
        return 0

    from clawpack.geoclaw import fgout_tools

    cfg = config or GeoClawExportConfig()
    frame_dir = export_root / "fgout_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for stale in frame_dir.glob("*.npz"):
        stale.unlink()

    fgout_grid = fgout_tools.FGoutGrid(1, str(output_dir), "binary32")
    fgout_grid.read_fgout_grids_data()
    frame_count = 0
    for frame_number in range(1, int(fgout_grid.nout) + 1):
        fgout = fgout_grid.read_frame(frame_number)
        h = _fgout_array_for_scenario(fgout.h, scenario)
        hu = _fgout_array_for_scenario(fgout.hu, scenario)
        hv = _fgout_array_for_scenario(fgout.hv, scenario)
        frame = _normalized_frame_from_h_momentum(
            scenario,
            h=h,
            hu=hu,
            hv=hv,
            time=float(fgout.t),
            config=cfg,
        )
        frame.write_npz(frame_dir / f"frame_{frame_count:04d}.npz")
        frame_count += 1
    return frame_count


def _fgout_array_for_scenario(array: object, scenario: Scenario2_5D) -> FloatGrid:
    values = np.asarray(array, dtype=np.float64)
    if values.shape == scenario.grid.shape:
        return values.copy()
    transposed_shape = (scenario.grid.nx, scenario.grid.ny)
    if values.shape == transposed_shape:
        return values.T.copy()
    raise ValueError(f"fgout array shape {values.shape} does not match scenario grid {scenario.grid.shape}.")


def _normalized_validation(scenario: Scenario2_5D, frames: tuple[GeoClawNormalizedFrame, ...]) -> dict[str, object]:
    mass_initial = frames[0].mass(scenario)
    mass_final = frames[-1].mass(scenario)
    relative_drift = abs(mass_final - mass_initial) / max(abs(mass_initial), 1.0e-9)
    max_velocity = max(frame.max_velocity for frame in frames)
    min_depth = min(frame.min_depth for frame in frames)
    checks = [
        {
            "name": "finite_fields",
            "passed": all(
                bool(np.isfinite(getattr(frame, name)).all())
                for frame in frames
                for name in ("h", "eta", "u", "v", "hu", "hv", "froude")
            ),
        },
        {"name": "nonnegative_depth", "passed": min_depth >= -1.0e-10, "min_depth": min_depth},
        {"name": "bounded_velocity", "passed": max_velocity <= 120.0, "max_velocity": max_velocity},
        {"name": "mass_drift_recorded", "passed": math.isfinite(relative_drift), "relative_drift": relative_drift},
    ]
    return {
        "passed": all(bool(check["passed"]) for check in checks),
        "mass_initial": mass_initial,
        "mass_final": mass_final,
        "mass_relative_drift": relative_drift,
        "max_velocity": max_velocity,
        "min_depth": min_depth,
        "checks": checks,
    }


def _surface_normals(eta: FloatGrid, dx: float, dy: float) -> tuple[FloatGrid, FloatGrid, FloatGrid]:
    d_eta_dy, d_eta_dx = np.gradient(eta, dy, dx)
    normal_x = -d_eta_dx
    normal_y = -d_eta_dy
    normal_z = np.ones_like(eta)
    length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    return normal_x / length, normal_y / length, normal_z / length


def _grid_index_for_position(scenario: Scenario2_5D, position: tuple[float, float]) -> tuple[int, int]:
    x, y = position
    column = int(round((x - scenario.grid.origin_x) / scenario.grid.dx))
    row = int(round((y - scenario.grid.origin_y) / scenario.grid.dy))
    column = max(0, min(scenario.grid.nx - 1, column))
    row = max(0, min(scenario.grid.ny - 1, row))
    return row, column


def _write_shared_scenario_package(scenario: Scenario2_5D, root: Path) -> list[str]:
    package_dir = scenario.write_package(root / "shared_scenario")
    return sorted(_relative_path(path, root) for path in package_dir.iterdir() if path.is_file())


def _write_makefile(root: Path) -> Path:
    content = """# Generated GeoClaw app Makefile for raftsim reference runs.
CLAWMAKE = $(CLAW)/clawutil/src/Makefile.common

CLAW_PKG = geoclaw
EXE = xgeoclaw
SETRUN_FILE = setrun.py
OUTDIR = _output
SETPLOT_FILE = setplot.py
PLOTDIR = _plots

FFLAGS ?=

GEOLIB = $(CLAW)/geoclaw/src/2d/shallow
include $(GEOLIB)/Makefile.geoclaw

EXCLUDE_MODULES =
EXCLUDE_SOURCES =
MODULES =

SOURCES = \\
  ./qinit.f90 \\
  $(CLAW)/riemann/src/rpn2_geoclaw.f \\
  $(CLAW)/riemann/src/rpt2_geoclaw.f \\
  $(CLAW)/riemann/src/geoclaw_riemann_utils.f \\

include $(CLAWMAKE)

.PHONY: app-data reference-run
app-data: .data

reference-run: .output
"""
    path = root / "Makefile"
    path.write_text(content, encoding="utf-8")
    return path


def _write_setrun_py(scenario: Scenario2_5D, config: GeoClawExportConfig, root: Path) -> Path:
    x_min, x_max, y_min, y_max = scenario.grid.extent
    boundary_lower, boundary_upper = _geoclaw_boundary_codes(scenario)
    ratios = _geoclaw_refinement_ratios(config)
    amr_regions = _geoclaw_region_entries(scenario, config)
    output_times = config.output_times(scenario.duration)
    content = f'''"""Generated GeoClaw run configuration for {scenario.metadata.scenario_id}.

This file is generated from the raftsim shared 2.5D scenario package.
The accompanying manifest.json is the authoritative export inventory.
"""

from __future__ import annotations


def setrun(claw_pkg: str = "geoclaw"):
    from clawpack.clawutil import data
    from clawpack.geoclaw import fgout_tools

    if claw_pkg.lower() != "geoclaw":
        raise ValueError("This generated app is configured for GeoClaw.")
    rundata = data.ClawRunData(claw_pkg, 2)
    clawdata = rundata.clawdata
    clawdata.lower = [{x_min:.17g}, {y_min:.17g}]
    clawdata.upper = [{x_max:.17g}, {y_max:.17g}]
    clawdata.num_cells = [{scenario.grid.nx}, {scenario.grid.ny}]
    clawdata.num_eqn = 3
    clawdata.num_aux = 1
    clawdata.capa_index = 0
    clawdata.t0 = 0.0
    clawdata.tfinal = {scenario.duration:.17g}
    clawdata.output_style = 1
    clawdata.num_output_times = {config.num_output_times}
    clawdata.output_t0 = True
    clawdata.output_format = "ascii"
    clawdata.output_q_components = "all"
    clawdata.output_aux_components = "none"
    clawdata.output_aux_onlyonce = True
    clawdata.dt_variable = True
    clawdata.dt_initial = {scenario.fixed_dt:.17g}
    clawdata.dt_max = {max(scenario.fixed_dt, scenario.duration / max(config.num_output_times, 1)):.17g}
    clawdata.cfl_desired = 0.45
    clawdata.cfl_max = 0.9
    clawdata.steps_max = 100000
    clawdata.num_waves = 3
    clawdata.limiter = ["mc", "mc", "mc"]
    clawdata.use_fwaves = True
    clawdata.source_split = "godunov"
    clawdata.dimensional_split = "unsplit"
    clawdata.transverse_waves = 2
    clawdata.num_ghost = 2
    clawdata.bc_lower = {boundary_lower!r}
    clawdata.bc_upper = {boundary_upper!r}

    amrdata = rundata.amrdata
    amrdata.amr_levels_max = {config.amr_max_level}
    amrdata.refinement_ratios_x = {ratios!r}
    amrdata.refinement_ratios_y = {ratios!r}
    amrdata.refinement_ratios_t = {ratios!r}
    amrdata.aux_type = ["center"]
    amrdata.flag_richardson = False
    amrdata.flag2refine = True
    amrdata.flag2refine_tol = 0.05
    amrdata.regrid_interval = 2
    amrdata.regrid_buffer_width = 2
    amrdata.clustering_cutoff = 0.7
    amrdata.verbosity_regrid = 0

    rundata.regiondata.regions = {amr_regions!r}

    rundata.geo_data.gravity = {config.gravity:.17g}
    rundata.geo_data.coordinate_system = 1
    rundata.geo_data.coriolis_forcing = False
    rundata.geo_data.sea_level = 0.0
    rundata.geo_data.dry_tolerance = {config.dry_tolerance:.17g}
    rundata.geo_data.speed_limit = 120.0
    rundata.geo_data.friction_forcing = True
    rundata.geo_data.manning_coefficient = {scenario.roughness:.17g}
    rundata.geo_data.friction_depth = 100.0

    rundata.topo_data.topofiles = [
        [{config.topography_topotype}, "b.tt1"],
    ]

    rundata.qinit_data.qinit_type = 0
    rundata.qinit_data.qinitfiles = []
    rundata.qinit_data.variable_eta_init = False

    fgout = fgout_tools.FGoutGrid()
    fgout.fgno = 1
    fgout.point_style = 2
    fgout.output_format = "binary32"
    fgout.output_style = 2
    fgout.output_times = {output_times!r}
    fgout.nx = {scenario.grid.nx}
    fgout.ny = {scenario.grid.ny}
    fgout.x1 = {x_min:.17g}
    fgout.x2 = {x_max:.17g}
    fgout.y1 = {y_min:.17g}
    fgout.y2 = {y_max:.17g}
    fgout.q_out_vars = [1, 2, 3, 4, 5]
    rundata.fgout_data.fgout_grids = [fgout]

    return rundata


if __name__ == "__main__":
    import sys

    package = sys.argv[1] if len(sys.argv) > 1 else "geoclaw"
    setrun(package).write()
'''
    path = root / "setrun.py"
    path.write_text(content, encoding="utf-8")
    return path


def _write_qinit_f90(scenario: Scenario2_5D, root: Path) -> Path:
    content = f"""! Generated qinit routine for raftsim scenario {scenario.metadata.scenario_id}.
subroutine qinit(meqn,mbc,mx,my,xlower,ylower,dx,dy,q,maux,aux)

    implicit none

    integer, intent(in) :: meqn,mbc,mx,my,maux
    real(kind=8), intent(in) :: xlower,ylower,dx,dy
    real(kind=8), intent(inout) :: q(meqn,1-mbc:mx+mbc,1-mbc:my+mbc)
    real(kind=8), intent(inout) :: aux(maux,1-mbc:mx+mbc,1-mbc:my+mbc)

    integer :: i,j,ii,jj,ios,unit,count,nx_file,ny_file
    real(kind=8) :: x_file,y_file,h_value,hu_value,hv_value,eta_value,wet_value
    real(kind=8) :: first_y,tolerance,dx_file,dy_file
    real(kind=8) :: x_min_file,x_max_file,y_min_file,y_max_file,x_cell,y_cell
    real(kind=8), allocatable :: h_data(:,:),hu_data(:,:),hv_data(:,:),wet_data(:,:)
    logical :: initialized
    character(len=*), parameter :: qinit_path = '../initial_state/qinit.xyz'

    q = 0.d0

    if (meqn < 3) then
        write(*,*) 'raftsim qinit requires at least 3 equations.'
        stop 2
    endif

    open(newunit=unit,file=qinit_path,status='old',action='read',iostat=ios)
    if (ios /= 0) then
        write(*,*) 'Unable to open raftsim qinit file: ', qinit_path
        stop 2
    endif

    count = 0
    nx_file = 0
    initialized = .false.
    do
        read(unit,*,iostat=ios) x_file,y_file,h_value,hu_value,hv_value,eta_value,wet_value
        if (ios /= 0) exit
        count = count + 1
        if (.not. initialized) then
            initialized = .true.
            first_y = y_file
            x_min_file = x_file
            x_max_file = x_file
            y_min_file = y_file
            y_max_file = y_file
        endif
        tolerance = max(1.d-10,abs(first_y)*1.d-12)
        if (abs(y_file - first_y) <= tolerance) nx_file = nx_file + 1
        x_min_file = min(x_min_file,x_file)
        x_max_file = max(x_max_file,x_file)
        y_min_file = min(y_min_file,y_file)
        y_max_file = max(y_max_file,y_file)
    enddo
    if (ios > 0) then
        write(*,*) 'Error scanning raftsim qinit file: ', qinit_path
        stop 2
    endif
    if ((count <= 0) .or. (nx_file <= 0) .or. (mod(count,nx_file) /= 0)) then
        write(*,*) 'Invalid raftsim qinit grid shape in ', qinit_path
        stop 2
    endif

    ny_file = count / nx_file
    allocate(h_data(nx_file,ny_file),hu_data(nx_file,ny_file))
    allocate(hv_data(nx_file,ny_file),wet_data(nx_file,ny_file))
    rewind(unit)

    do jj=1,ny_file
        do ii=1,nx_file
            read(unit,*,iostat=ios) x_file,y_file,h_value,hu_value,hv_value,eta_value,wet_value
            if (ios /= 0) then
                write(*,*) 'Error reading raftsim qinit cell ', ii, jj, ' from ', qinit_path
                stop 2
            endif
            h_data(ii,jj) = max(0.d0,h_value)
            hu_data(ii,jj) = hu_value
            hv_data(ii,jj) = hv_value
            wet_data(ii,jj) = wet_value
        enddo
    enddo

    close(unit)

    if (nx_file > 1) then
        dx_file = (x_max_file - x_min_file) / dble(nx_file - 1)
    else
        dx_file = dx
    endif
    if (ny_file > 1) then
        dy_file = (y_max_file - y_min_file) / dble(ny_file - 1)
    else
        dy_file = dy
    endif

    do j=1,my
        y_cell = ylower + (dble(j) - 0.5d0) * dy
        jj = nint((y_cell - y_min_file) / max(dy_file,1.d-12)) + 1
        jj = max(1,min(ny_file,jj))
        do i=1,mx
            x_cell = xlower + (dble(i) - 0.5d0) * dx
            ii = nint((x_cell - x_min_file) / max(dx_file,1.d-12)) + 1
            ii = max(1,min(nx_file,ii))
            if (wet_data(ii,jj) >= 0.5d0) then
                q(1,i,j) = h_data(ii,jj)
                q(2,i,j) = hu_data(ii,jj)
                q(3,i,j) = hv_data(ii,jj)
            else
                q(1,i,j) = 0.d0
                q(2,i,j) = 0.d0
                q(3,i,j) = 0.d0
            endif
        enddo
    enddo

    deallocate(h_data,hu_data,hv_data,wet_data)

end subroutine qinit
"""
    path = root / "qinit.f90"
    path.write_text(content, encoding="utf-8")
    return path


def _write_topography(scenario: Scenario2_5D, root: Path) -> Path:
    path = root / "b.tt1"
    path.parent.mkdir(parents=True, exist_ok=True)
    x_min, x_max, y_min, y_max = scenario.grid.extent
    x_values = np.linspace(x_min, x_max, scenario.grid.nx + 1, dtype=np.float64)
    y_values = np.linspace(y_min, y_max, scenario.grid.ny + 1, dtype=np.float64)
    with path.open("w", encoding="utf-8") as handle:
        for y in reversed(y_values):
            row = int(np.clip(round((float(y) - scenario.grid.origin_y) / scenario.grid.dy), 0, scenario.grid.ny - 1))
            for x in x_values:
                column = int(
                    np.clip(round((float(x) - scenario.grid.origin_x) / scenario.grid.dx), 0, scenario.grid.nx - 1)
                )
                handle.write(
                    f"{float(x):.17g} {float(y):.17g} {scenario.bed[row, column]:.17g}\n"
                )
    return path


def _write_initial_state_npz(scenario: Scenario2_5D, root: Path) -> Path:
    path = root / "initial_state" / "initial_water_state.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        h=scenario.initial_state.depth,
        eta=scenario.initial_state.eta,
        u=scenario.initial_state.u,
        v=scenario.initial_state.v,
        hu=scenario.initial_state.hu,
        hv=scenario.initial_state.hv,
        wet=scenario.initial_state.wet,
        bed=scenario.bed,
    )
    return path


def _write_qinit_xyz(scenario: Scenario2_5D, root: Path) -> Path:
    path = root / "initial_state" / "qinit.xyz"
    path.parent.mkdir(parents=True, exist_ok=True)
    x_grid, y_grid = scenario.grid.meshgrid()
    with path.open("w", encoding="utf-8") as handle:
        for row in range(scenario.grid.ny):
            for column in range(scenario.grid.nx):
                handle.write(
                    f"{x_grid[row, column]:.17g} {y_grid[row, column]:.17g} "
                    f"{scenario.initial_state.depth[row, column]:.17g} "
                    f"{scenario.initial_state.hu[row, column]:.17g} "
                    f"{scenario.initial_state.hv[row, column]:.17g} "
                    f"{scenario.initial_state.eta[row, column]:.17g} "
                    f"{int(scenario.initial_state.wet[row, column])}\n"
                )
    return path


def _write_roughness_grid(scenario: Scenario2_5D, root: Path) -> Path:
    path = root / "roughness" / "manning_n.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, _roughness_grid(scenario))
    return path


def _write_boundaries(scenario: Scenario2_5D, root: Path) -> list[str]:
    boundary_dir = root / "boundaries"
    hydrograph_dir = boundary_dir / "hydrographs"
    boundary_dir.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    boundary_entries: list[dict[str, object]] = []
    for boundary in scenario.boundaries:
        entry = boundary.to_json_dict()
        if boundary.hydrograph:
            hydrograph_path = hydrograph_dir / f"{boundary.edge}.csv"
            hydrograph_path.parent.mkdir(parents=True, exist_ok=True)
            with hydrograph_path.open("w", encoding="utf-8") as handle:
                handle.write("time,stage,depth,velocity_x,velocity_y\n")
                for sample in boundary.hydrograph:
                    velocity = sample.velocity or ("", "")
                    handle.write(
                        f"{sample.time},{_csv_value(sample.stage)},{_csv_value(sample.depth)},"
                        f"{_csv_value(velocity[0])},{_csv_value(velocity[1])}\n"
                    )
            entry["hydrograph_file"] = _relative_path(hydrograph_path, root)
            exported.append(_relative_path(hydrograph_path, root))
        boundary_entries.append(entry)
    path = boundary_dir / "boundaries.json"
    _write_json(path, {"boundaries": boundary_entries})
    exported.append(_relative_path(path, root))
    return sorted(exported)


def _write_amr_regions(scenario: Scenario2_5D, config: GeoClawExportConfig, root: Path) -> Path:
    path = root / "amr" / "amr_regions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, {"regions": _amr_regions(scenario, config)})
    return path


def _write_fixed_grid_output(scenario: Scenario2_5D, config: GeoClawExportConfig, root: Path) -> Path:
    path = root / "fgout" / "fgout_grids.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    x_min, x_max, y_min, y_max = scenario.grid.extent
    fgout = {
        "grids": [
            {
                "fgno": 1,
                "name": "comparison_domain",
                "x": {"lower": x_min, "upper": x_max, "num_cells": scenario.grid.nx},
                "y": {"lower": y_min, "upper": y_max, "num_cells": scenario.grid.ny},
                "times": config.output_times(scenario.duration),
                "fields": ["h", "eta", "u", "v", "hu", "hv", "wet", "normal_x", "normal_y", "normal_z", "froude"],
            }
        ]
    }
    _write_json(path, fgout)
    return path


def _roughness_grid(scenario: Scenario2_5D) -> FloatGrid:
    roughness = np.full(scenario.grid.shape, scenario.roughness, dtype=np.float64)
    x_grid, y_grid = scenario.grid.meshgrid()
    roughness_scale = {
        "rock": 0.020,
        "strainer": 0.025,
        "shallow": 0.015,
        "ledge": 0.010,
        "constriction": 0.008,
        "eddy_line": 0.006,
    }
    for feature in scenario.features:
        increment = roughness_scale.get(feature.kind, 0.0)
        if increment <= 0.0:
            continue
        influence = _feature_influence(x_grid, y_grid, feature.center, feature.radius, feature.length, feature.width)
        roughness += increment * max(feature.strength, 0.0) * influence
    return np.where(scenario.initial_state.wet, roughness, scenario.roughness)


def _amr_regions(scenario: Scenario2_5D, config: GeoClawExportConfig) -> list[dict[str, object]]:
    regions: list[dict[str, object]] = []
    x_min, x_max, y_min, y_max = scenario.grid.extent
    if bool((~scenario.initial_state.wet).any()):
        regions.append(
            {
                "name": "wet_dry_front_domain",
                "reason": "initial wet/dry cells present",
                "min_level": config.amr_min_level,
                "max_level": config.amr_max_level,
                "x": [x_min, x_max],
                "y": [y_min, y_max],
                "t": [0.0, scenario.duration],
            }
        )

    high_priority = {"ledge", "hole", "wave_train", "constriction", "rock", "shallow"}
    for index, feature in enumerate(scenario.features):
        span_x = max(feature.radius, feature.length * 0.5, scenario.grid.dx) + config.feature_padding_m
        span_y = max(feature.radius, feature.width * 0.5, scenario.grid.dy) + config.feature_padding_m
        max_level = config.amr_max_level if feature.kind in high_priority else max(config.amr_min_level, config.amr_max_level - 1)
        regions.append(
            {
                "name": f"feature_{index:03d}_{feature.kind}",
                "reason": f"refine {feature.kind}",
                "feature": feature.to_json_dict(),
                "min_level": config.amr_min_level,
                "max_level": max_level,
                "x": [max(x_min, feature.center[0] - span_x), min(x_max, feature.center[0] + span_x)],
                "y": [max(y_min, feature.center[1] - span_y), min(y_max, feature.center[1] + span_y)],
                "t": [0.0, scenario.duration],
            }
        )
    return regions


def _feature_influence(
    x_grid: FloatGrid,
    y_grid: FloatGrid,
    center: tuple[float, float],
    radius: float,
    length: float,
    width: float,
) -> FloatGrid:
    scale_x = max(radius, length * 0.5, 1.0)
    scale_y = max(radius, width * 0.5, 1.0)
    dx = (x_grid - center[0]) / scale_x
    dy = (y_grid - center[1]) / scale_y
    return np.exp(-(dx**2 + dy**2))


def _geoclaw_boundary_codes(scenario: Scenario2_5D) -> tuple[list[str], list[str]]:
    code_by_edge = {boundary.edge: _boundary_code(boundary.kind) for boundary in scenario.boundaries}
    return [code_by_edge["west"], code_by_edge["south"]], [code_by_edge["east"], code_by_edge["north"]]


def _boundary_code(kind: str) -> str:
    if kind in {"wall", "bank"}:
        return "wall"
    return "extrap"


def _geoclaw_refinement_ratios(config: GeoClawExportConfig) -> list[int]:
    return [2] * max(config.amr_max_level - 1, 1)


def _geoclaw_region_entries(scenario: Scenario2_5D, config: GeoClawExportConfig) -> list[list[float | int]]:
    return [
        [
            int(region["min_level"]),
            int(region["max_level"]),
            float(region["t"][0]),  # type: ignore[index]
            float(region["t"][1]),  # type: ignore[index]
            float(region["x"][0]),  # type: ignore[index]
            float(region["x"][1]),  # type: ignore[index]
            float(region["y"][0]),  # type: ignore[index]
            float(region["y"][1]),  # type: ignore[index]
        ]
        for region in _amr_regions(scenario, config)
    ]


def _csv_value(value: object) -> object:
    return "" if value is None else value


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()
