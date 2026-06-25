"""Optional PyClaw reference harness for 2.5D shallow-water scenarios."""

from __future__ import annotations

import csv
import importlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .scenario2_5d import (
    FixtureScenario2_5DParameters,
    Probe2_5D,
    ProceduralScenario2_5DParameters,
    Scenario2_5D,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    read_scenario2_5d_package,
)

FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]

PyClawSolverType = Literal["classic", "sharpclaw"]


class PyClawUnavailableError(RuntimeError):
    """Raised when PyClaw is required but not importable."""


@dataclass(frozen=True, slots=True)
class PyClawAvailability:
    available: bool
    reason: str
    pyclaw_module: str | None = None
    riemann_module: str | None = None
    pyclaw_version: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PyClawRunConfig:
    """Runtime/export settings for an offline PyClaw reference run."""

    solver_type: PyClawSolverType = "classic"
    riemann_solver: str = "shallow_roe_with_efix_2D"
    num_output_times: int = 8
    gravity: float = 9.81
    dry_tolerance: float = 1.0e-6
    max_allowed_velocity: float = 80.0
    mass_relative_tolerance: float = 0.02
    cfl_desired: float = 0.45
    cfl_max: float = 0.9
    verbosity: int = 0

    def __post_init__(self) -> None:
        if self.num_output_times < 1:
            raise ValueError("num_output_times must be at least 1.")
        if self.gravity <= 0.0:
            raise ValueError("gravity must be positive.")
        if self.dry_tolerance < 0.0:
            raise ValueError("dry_tolerance must be non-negative.")
        if self.mass_relative_tolerance < 0.0:
            raise ValueError("mass_relative_tolerance must be non-negative.")

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PyClawValidationCheck:
    name: str
    passed: bool
    details: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PyClawValidationSummary:
    checks: tuple[PyClawValidationCheck, ...]
    mass_initial: float
    mass_final: float
    mass_relative_drift: float
    max_velocity: float
    min_depth: float

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "mass_initial": self.mass_initial,
            "mass_final": self.mass_final,
            "mass_relative_drift": self.mass_relative_drift,
            "max_velocity": self.max_velocity,
            "min_depth": self.min_depth,
            "checks": [check.to_json_dict() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class PyClawFieldFrame:
    time: float
    h: FloatGrid
    eta: FloatGrid
    u: FloatGrid
    v: FloatGrid
    hu: FloatGrid
    hv: FloatGrid
    wet: BoolGrid
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
class PyClawProbeSeries:
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
class PyClawCrossSectionSeries:
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
class PyClawReferenceResult:
    scenario_id: str
    config: PyClawRunConfig
    availability: PyClawAvailability
    frames: tuple[PyClawFieldFrame, ...]
    probes: tuple[PyClawProbeSeries, ...]
    cross_sections: tuple[PyClawCrossSectionSeries, ...]
    validation: PyClawValidationSummary
    run_status: dict[str, object] = field(default_factory=dict)

    def write_output(self, directory: str | Path) -> Path:
        output_dir = Path(directory)
        frames_dir = output_dir / "frames"
        probes_dir = output_dir / "probes"
        cross_sections_dir = output_dir / "cross_sections"
        output_dir.mkdir(parents=True, exist_ok=True)

        frame_files: list[str] = []
        for index, frame in enumerate(self.frames):
            relative = Path("frames") / f"frame_{index:04d}.npz"
            frame.write_npz(output_dir / relative)
            frame_files.append(str(relative))

        probe_files: list[str] = []
        for probe in self.probes:
            relative = Path("probes") / f"{probe.probe_id}.csv"
            probe.write_csv(output_dir / relative)
            probe_files.append(str(relative))

        cross_section_files: list[str] = []
        for cross_section in self.cross_sections:
            relative = Path("cross_sections") / f"{cross_section.probe_id}.npz"
            cross_section.write_npz(output_dir / relative)
            cross_section_files.append(str(relative))

        validation_path = output_dir / "validation.json"
        validation_path.write_text(json.dumps(self.validation.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")

        manifest = {
            "scenario_id": self.scenario_id,
            "config": self.config.to_json_dict(),
            "availability": self.availability.to_json_dict(),
            "run_status": self.run_status,
            "validation": "validation.json",
            "frames": frame_files,
            "probes": probe_files,
            "cross_sections": cross_section_files,
            "probe_manifest": [probe.to_manifest_dict() for probe in self.probes],
            "cross_section_manifest": [cross_section.to_manifest_dict() for cross_section in self.cross_sections],
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        frames_dir.mkdir(exist_ok=True)
        probes_dir.mkdir(exist_ok=True)
        cross_sections_dir.mkdir(exist_ok=True)
        return output_dir


def check_pyclaw_availability() -> PyClawAvailability:
    """Return whether the optional Clawpack/PyClaw runtime can be imported."""

    try:
        pyclaw = importlib.import_module("clawpack.pyclaw")
        riemann = importlib.import_module("clawpack.riemann")
    except Exception as exc:  # pragma: no cover - exact import failure varies by install.
        return PyClawAvailability(False, f"{type(exc).__name__}: {exc}")

    version = getattr(importlib.import_module("clawpack"), "__version__", None)
    missing_solver = not hasattr(riemann, PyClawRunConfig().riemann_solver)
    if missing_solver:
        return PyClawAvailability(
            False,
            f"clawpack.riemann is missing {PyClawRunConfig().riemann_solver}",
            pyclaw_module=getattr(pyclaw, "__file__", None),
            riemann_module=getattr(riemann, "__file__", None),
            pyclaw_version=version,
        )
    return PyClawAvailability(
        True,
        "PyClaw and Riemann shallow-water solver are importable.",
        pyclaw_module=getattr(pyclaw, "__file__", None),
        riemann_module=getattr(riemann, "__file__", None),
        pyclaw_version=version,
    )


def canonical_pyclaw_scenarios(seed: int = 1) -> tuple[Scenario2_5D, ...]:
    """Return the canonical fixture set plus one procedural rapid package."""

    fixture_names = (
        "flat_pool",
        "uniform_channel",
        "dam_break",
        "bed_step",
        "constriction",
        "wet_dry_shoreline",
    )
    fixtures = tuple(
        generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture=fixture, seed=seed))
        for fixture in fixture_names
    )
    return (*fixtures, generate_procedural_scenario2_5d(ProceduralScenario2_5DParameters(seed=seed)))


def frame_from_scenario_initial_state(
    scenario: Scenario2_5D,
    *,
    time: float = 0.0,
    config: PyClawRunConfig | None = None,
) -> PyClawFieldFrame:
    """Build a reference-frame export from a scenario initial state."""

    cfg = config or PyClawRunConfig()
    return _field_frame_from_h_momentum(
        scenario,
        h=scenario.initial_state.depth,
        hu=scenario.initial_state.hu,
        hv=scenario.initial_state.hv,
        time=time,
        config=cfg,
    )


def build_initial_pyclaw_reference_result(
    scenario: Scenario2_5D,
    *,
    config: PyClawRunConfig | None = None,
    availability: PyClawAvailability | None = None,
) -> PyClawReferenceResult:
    """Build export/validation artifacts from initial fields without running PyClaw."""

    cfg = config or PyClawRunConfig()
    return _build_result(
        scenario,
        cfg,
        availability or check_pyclaw_availability(),
        (frame_from_scenario_initial_state(scenario, config=cfg),),
        run_status={"mode": "initial_state_only"},
    )


def run_pyclaw_reference(
    scenario_or_path: Scenario2_5D | str | Path,
    *,
    config: PyClawRunConfig | None = None,
    output_dir: str | Path | None = None,
) -> PyClawReferenceResult:
    """Run PyClaw on a shared 2.5D scenario package and export diagnostics."""

    cfg = config or PyClawRunConfig()
    scenario = read_scenario2_5d_package(scenario_or_path) if not isinstance(scenario_or_path, Scenario2_5D) else scenario_or_path
    availability = check_pyclaw_availability()
    if not availability.available:
        raise PyClawUnavailableError(availability.reason)

    pyclaw = importlib.import_module("clawpack.pyclaw")
    riemann = importlib.import_module("clawpack.riemann")
    solver = _make_solver(pyclaw, riemann, scenario, cfg)
    domain = _make_domain(pyclaw, scenario)
    state = pyclaw.State(domain, 3)
    state.problem_data["grav"] = cfg.gravity
    state.problem_data["dry_tolerance"] = cfg.dry_tolerance
    state.q[0, :, :] = scenario.initial_state.depth.T
    state.q[1, :, :] = scenario.initial_state.hu.T
    state.q[2, :, :] = scenario.initial_state.hv.T

    claw = pyclaw.Controller()
    claw.solution = pyclaw.Solution(state, domain)
    claw.solver = solver
    claw.tfinal = scenario.duration
    claw.num_output_times = cfg.num_output_times
    claw.keep_copy = True
    claw.output_format = None
    claw.verbosity = cfg.verbosity
    status = claw.run()

    frames: list[PyClawFieldFrame] = [frame_from_scenario_initial_state(scenario, config=cfg)]
    for solution in getattr(claw, "frames", []):
        q = _solution_q(solution)
        time = float(getattr(solution, "t", getattr(getattr(solution, "state", None), "t", 0.0)))
        if time <= cfg.dry_tolerance and frames:
            continue
        frames.append(
            _field_frame_from_h_momentum(
                scenario,
                h=np.asarray(q[0, :, :], dtype=np.float64).T,
                hu=np.asarray(q[1, :, :], dtype=np.float64).T,
                hv=np.asarray(q[2, :, :], dtype=np.float64).T,
                time=time,
                config=cfg,
            )
        )

    result = _build_result(
        scenario,
        cfg,
        availability,
        tuple(frames),
        run_status={str(key): _json_scalar(value) for key, value in dict(status or {}).items()},
    )
    if output_dir is not None:
        result.write_output(output_dir)
    return result


def write_unavailable_report(directory: str | Path, availability: PyClawAvailability) -> Path:
    """Write a small machine-readable report when PyClaw cannot run locally."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "available": availability.available,
        "reason": availability.reason,
        "install_hint": 'Install the optional research extra with: python -m pip install -e ".[research]"',
    }
    path = output_dir / "pyclaw_unavailable.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _build_result(
    scenario: Scenario2_5D,
    config: PyClawRunConfig,
    availability: PyClawAvailability,
    frames: tuple[PyClawFieldFrame, ...],
    *,
    run_status: dict[str, object] | None = None,
) -> PyClawReferenceResult:
    probes, cross_sections = _sample_outputs(scenario, frames)
    return PyClawReferenceResult(
        scenario_id=scenario.metadata.scenario_id,
        config=config,
        availability=availability,
        frames=frames,
        probes=probes,
        cross_sections=cross_sections,
        validation=_validate_frames(scenario, frames, config),
        run_status=run_status or {},
    )


def _make_solver(pyclaw, riemann, scenario: Scenario2_5D, config: PyClawRunConfig):
    riemann_solver = getattr(riemann, config.riemann_solver)
    if config.solver_type == "sharpclaw":
        solver = pyclaw.SharpClawSolver2D(riemann_solver)
    else:
        solver = pyclaw.ClawSolver2D(riemann_solver)

    solver.cfl_desired = config.cfl_desired
    solver.cfl_max = config.cfl_max
    edge_to_bc = {boundary.edge: _map_boundary_condition(pyclaw, boundary.kind) for boundary in scenario.boundaries}
    solver.bc_lower[0] = edge_to_bc["west"]
    solver.bc_upper[0] = edge_to_bc["east"]
    solver.bc_lower[1] = edge_to_bc["south"]
    solver.bc_upper[1] = edge_to_bc["north"]
    return solver


def _make_domain(pyclaw, scenario: Scenario2_5D):
    x_min, x_max, y_min, y_max = scenario.grid.extent
    x_dim = pyclaw.Dimension(x_min, x_max, scenario.grid.nx, name="x")
    y_dim = pyclaw.Dimension(y_min, y_max, scenario.grid.ny, name="y")
    return pyclaw.Domain([x_dim, y_dim])


def _map_boundary_condition(pyclaw, kind: str):
    if kind in {"wall", "bank"}:
        return pyclaw.BC.wall
    return pyclaw.BC.extrap


def _solution_q(solution) -> FloatGrid:
    state = getattr(solution, "state", None)
    if state is None:
        states = getattr(solution, "states", None)
        if not states:
            raise ValueError("PyClaw solution has no state data.")
        state = states[0]
    return state.q


def _field_frame_from_h_momentum(
    scenario: Scenario2_5D,
    *,
    h: FloatGrid,
    hu: FloatGrid,
    hv: FloatGrid,
    time: float,
    config: PyClawRunConfig,
) -> PyClawFieldFrame:
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
    return PyClawFieldFrame(
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


def _surface_normals(eta: FloatGrid, dx: float, dy: float) -> tuple[FloatGrid, FloatGrid, FloatGrid]:
    d_eta_dy, d_eta_dx = np.gradient(eta, dy, dx)
    normal_x = -d_eta_dx
    normal_y = -d_eta_dy
    normal_z = np.ones_like(eta)
    length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    return normal_x / length, normal_y / length, normal_z / length


def _sample_outputs(
    scenario: Scenario2_5D,
    frames: tuple[PyClawFieldFrame, ...],
) -> tuple[tuple[PyClawProbeSeries, ...], tuple[PyClawCrossSectionSeries, ...]]:
    point_probes: list[PyClawProbeSeries] = []
    cross_sections: list[PyClawCrossSectionSeries] = []
    for probe in scenario.probes:
        if probe.kind == "cross_section":
            cross_sections.append(_sample_cross_section(scenario, frames, probe))
        else:
            point_probes.append(_sample_point_probe(scenario, frames, probe))
    return tuple(point_probes), tuple(cross_sections)


def _sample_point_probe(
    scenario: Scenario2_5D,
    frames: tuple[PyClawFieldFrame, ...],
    probe: Probe2_5D,
) -> PyClawProbeSeries:
    row, column = _grid_index_for_position(scenario, probe.position)
    field_names = ("h", "eta", "u", "v", "hu", "hv", "wet", "froude")
    values: dict[str, tuple[float, ...]] = {}
    for name in field_names:
        values[name] = tuple(float(getattr(frame, name)[row, column]) for frame in frames)
    return PyClawProbeSeries(
        probe_id=probe.probe_id,
        kind=probe.kind,
        times=tuple(frame.time for frame in frames),
        values=values,
        metadata={"row": row, "column": column, "position": probe.position},
    )


def _sample_cross_section(
    scenario: Scenario2_5D,
    frames: tuple[PyClawFieldFrame, ...],
    probe: Probe2_5D,
) -> PyClawCrossSectionSeries:
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

    return PyClawCrossSectionSeries(
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


def _grid_index_for_position(scenario: Scenario2_5D, position: tuple[float, float]) -> tuple[int, int]:
    column = int(round((position[0] - scenario.grid.origin_x) / scenario.grid.dx))
    row = int(round((position[1] - scenario.grid.origin_y) / scenario.grid.dy))
    row = max(0, min(scenario.grid.ny - 1, row))
    column = max(0, min(scenario.grid.nx - 1, column))
    return row, column


def _validate_frames(
    scenario: Scenario2_5D,
    frames: tuple[PyClawFieldFrame, ...],
    config: PyClawRunConfig,
) -> PyClawValidationSummary:
    if not frames:
        return PyClawValidationSummary(
            checks=(PyClawValidationCheck("has_frames", False, "frames=0"),),
            mass_initial=0.0,
            mass_final=0.0,
            mass_relative_drift=float("inf"),
            max_velocity=float("inf"),
            min_depth=float("inf"),
        )

    masses = [frame.mass(scenario) for frame in frames]
    mass_initial = masses[0]
    mass_final = masses[-1]
    mass_scale = max(abs(mass_initial), 1.0)
    mass_relative_drift = abs(mass_final - mass_initial) / mass_scale
    max_velocity = max(frame.max_velocity for frame in frames)
    min_depth = min(frame.min_depth for frame in frames)
    all_finite = all(
        np.isfinite(field).all()
        for frame in frames
        for field in (frame.h, frame.eta, frame.u, frame.v, frame.hu, frame.hv, frame.froude)
    )
    checks = [
        PyClawValidationCheck("has_frames", len(frames) > 0, f"frames={len(frames)}"),
        PyClawValidationCheck("finite_fields", bool(all_finite), f"frames={len(frames)}"),
        PyClawValidationCheck("nonnegative_depth", min_depth >= -config.dry_tolerance, f"min_depth={min_depth:.6f}"),
        PyClawValidationCheck(
            "bounded_velocity",
            max_velocity <= config.max_allowed_velocity,
            f"max_velocity={max_velocity:.6f}",
        ),
        PyClawValidationCheck(
            "mass_conservation",
            mass_relative_drift <= config.mass_relative_tolerance,
            f"relative_drift={mass_relative_drift:.6f}",
        ),
    ]
    checks.extend(_analytic_validation_checks(scenario, frames, config))
    return PyClawValidationSummary(
        checks=tuple(checks),
        mass_initial=mass_initial,
        mass_final=mass_final,
        mass_relative_drift=mass_relative_drift,
        max_velocity=max_velocity,
        min_depth=min_depth,
    )


def _analytic_validation_checks(
    scenario: Scenario2_5D,
    frames: tuple[PyClawFieldFrame, ...],
    config: PyClawRunConfig,
) -> list[PyClawValidationCheck]:
    fixture = scenario.metadata.fixture_kind
    if fixture == "flat_pool":
        max_speed = max(frame.max_velocity for frame in frames)
        eta_range = max(float(np.max(frame.eta) - np.min(frame.eta)) for frame in frames)
        return [
            PyClawValidationCheck("still_water_velocity", max_speed <= 1.0e-5, f"max_speed={max_speed:.6e}"),
            PyClawValidationCheck("still_water_surface", eta_range <= 1.0e-5, f"eta_range={eta_range:.6e}"),
        ]
    if fixture == "uniform_channel":
        first = frames[0]
        mean_depth = float(np.mean(first.h[first.wet]))
        depth_error = float(np.max(np.abs(first.h[first.wet] - mean_depth)))
        return [
            PyClawValidationCheck(
                "uniform_channel_initial_depth",
                depth_error <= max(config.dry_tolerance, 1.0e-9),
                f"depth_error={depth_error:.6e}",
            )
        ]
    return []


def _json_scalar(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
