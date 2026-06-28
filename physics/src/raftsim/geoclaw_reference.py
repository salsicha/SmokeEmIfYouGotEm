"""GeoClaw reference-solver setup checks and transition utilities."""

from __future__ import annotations

import importlib
import json
import shutil
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .real_world import default_player_selections, generate_real_world_scenario2_5d
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
GEOCLAW_CANONICAL_SUITE_SCHEMA = "raftsim.geoclaw_canonical_suite.v1"
GEOCLAW_RAFTING_SUITE_SCHEMA = "raftsim.geoclaw_rafting_suite.v1"
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
    files.append(_relative_path(_write_setrun_py(scenario, cfg, root), root))
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
            "setrun": "setrun.py",
            "topography": "topography/bed_topography.xyz",
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


def _write_shared_scenario_package(scenario: Scenario2_5D, root: Path) -> list[str]:
    package_dir = scenario.write_package(root / "shared_scenario")
    return sorted(_relative_path(path, root) for path in package_dir.iterdir() if path.is_file())


def _write_setrun_py(scenario: Scenario2_5D, config: GeoClawExportConfig, root: Path) -> Path:
    x_min, x_max, y_min, y_max = scenario.grid.extent
    content = f'''"""Generated GeoClaw run configuration for {scenario.metadata.scenario_id}.

This file is generated from the raftsim shared 2.5D scenario package.
The accompanying manifest.json is the authoritative export inventory.
"""

from __future__ import annotations


def setrun(claw_pkg: str = "geoclaw"):
    from clawpack.clawutil import data

    rundata = data.ClawRunData(claw_pkg, 2)
    clawdata = rundata.clawdata
    clawdata.lower = [{x_min:.17g}, {y_min:.17g}]
    clawdata.upper = [{x_max:.17g}, {y_max:.17g}]
    clawdata.num_cells = [{scenario.grid.nx}, {scenario.grid.ny}]
    clawdata.t0 = 0.0
    clawdata.tfinal = {scenario.duration:.17g}
    clawdata.num_output_times = {config.num_output_times}
    clawdata.output_style = 1
    clawdata.dt_variable = True
    clawdata.dt_initial = {scenario.fixed_dt:.17g}
    clawdata.cfl_desired = 0.45
    clawdata.cfl_max = 0.9
    clawdata.num_eqn = 3
    clawdata.num_aux = 1
    clawdata.bc_lower = {_geoclaw_boundary_codes(scenario)[0]!r}
    clawdata.bc_upper = {_geoclaw_boundary_codes(scenario)[1]!r}

    rundata.geo_data.gravity = {config.gravity:.17g}
    rundata.geo_data.dry_tolerance = {config.dry_tolerance:.17g}
    rundata.geo_data.friction_forcing = True
    rundata.geo_data.manning_coefficient = {scenario.roughness:.17g}

    rundata.topo_data.topofiles = [
        [{config.topography_topotype}, {config.amr_min_level}, {config.amr_max_level}, 0.0, 1.0e10, "topography/bed_topography.xyz"],
    ]

    # GeoClaw fixed-grid output and AMR region metadata are exported next to this
    # file as JSON so the Python normalization harness can consume them directly.
    return rundata
'''
    path = root / "setrun.py"
    path.write_text(content, encoding="utf-8")
    return path


def _write_topography(scenario: Scenario2_5D, root: Path) -> Path:
    path = root / "topography" / "bed_topography.xyz"
    path.parent.mkdir(parents=True, exist_ok=True)
    x_grid, y_grid = scenario.grid.meshgrid()
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# raftsim GeoClaw topography export: x y bed_z_m\n")
        handle.write(f"# nx={scenario.grid.nx} ny={scenario.grid.ny} dx={scenario.grid.dx:.17g} dy={scenario.grid.dy:.17g}\n")
        for row in range(scenario.grid.ny):
            for column in range(scenario.grid.nx):
                handle.write(
                    f"{x_grid[row, column]:.17g} {y_grid[row, column]:.17g} {scenario.bed[row, column]:.17g}\n"
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
        handle.write("# raftsim GeoClaw initial state export: x y h hu hv eta wet\n")
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
    if kind == "inflow":
        return "user"
    return "extrap"


def _csv_value(value: object) -> object:
    return "" if value is None else value


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()
