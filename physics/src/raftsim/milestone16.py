"""Milestone 16 validation runners and report artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
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
from .real_world import default_player_selections, generate_real_world_scenario2_5d
from .scenario2_5d import Scenario2_5D
from .scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d

MILESTONE16_GEOCLAW_REFERENCE_REPORT_SCHEMA = "raftsim.milestone16.geoclaw_reference_runs.v0"
MILESTONE16_CPP_RUN_REPORT_SCHEMA = "raftsim.milestone16.cpp_solver_runs.v0"
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
            config = _cpp_config_for_mode(executable, solver_mode)
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


def _cpp_config_for_mode(executable: Path, solver_mode: str) -> CppSolverRunConfig:
    return CppSolverRunConfig(
        executable=executable,
        solver_mode=solver_mode,
        boundary_mode="scenario",
        flux_scheme="rusanov",
        cfl=0.45,
        dry_tolerance=1.0e-6,
        feature_strength_scale=1.0,
        roughness_scale=1.0,
        bed_slope_source_scale=1.0 if solver_mode == "finite_volume" else 0.0,
        preserve_initial_mass=True,
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
