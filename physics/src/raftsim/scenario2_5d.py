"""Solver-neutral 2.5D scenario packages and fixture generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]

ScenarioType2_5D = Literal["fixture", "procedural", "real_world"]
FixtureKind2_5D = Literal[
    "flat_pool",
    "uniform_channel",
    "dam_break",
    "bed_step",
    "constriction",
    "wet_dry_shoreline",
]
BoundaryEdge2_5D = Literal["west", "east", "south", "north"]
BoundaryKind2_5D = Literal["wall", "bank", "inflow", "outflow", "open"]
FeatureKind2_5D = Literal[
    "rock",
    "ledge",
    "constriction",
    "hole",
    "lateral",
    "boil",
    "shallow",
    "strainer",
    "wave_train",
]
ProbeKind2_5D = Literal["point", "cross_section"]
MetadataValue = str | int | float | bool | None

SCENARIO_SCHEMA_VERSION = "raftsim.scenario2_5d.v0"
INITIAL_STATE_FILE = "initial_state.npz"
BED_FILE = "bed.npy"
FEATURES_FILE = "features.json"
PROBES_FILE = "probes.json"


@dataclass(frozen=True, slots=True)
class ValidationCheck2_5D:
    name: str
    passed: bool
    details: str = ""


@dataclass(frozen=True, slots=True)
class ScenarioValidation2_5D:
    checks: tuple[ValidationCheck2_5D, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def summary_lines(self) -> list[str]:
        return [
            f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.details}"
            for check in self.checks
        ]


@dataclass(frozen=True, slots=True)
class GridSpec2_5D:
    """Row-major grid definition for solver-neutral 2.5D fields.

    Arrays are stored with shape ``(ny, nx)``. Coordinates represent cell centers.
    """

    nx: int = 64
    ny: int = 32
    dx: float = 1.0
    dy: float = 1.0
    origin_x: float = 0.0
    origin_y: float = -16.0

    def __post_init__(self) -> None:
        if self.nx < 2:
            raise ValueError("nx must be at least 2.")
        if self.ny < 2:
            raise ValueError("ny must be at least 2.")
        if self.dx <= 0.0:
            raise ValueError("dx must be positive.")
        if self.dy <= 0.0:
            raise ValueError("dy must be positive.")

    @property
    def shape(self) -> tuple[int, int]:
        return (self.ny, self.nx)

    @property
    def extent(self) -> tuple[float, float, float, float]:
        half_dx = self.dx * 0.5
        half_dy = self.dy * 0.5
        return (
            self.origin_x - half_dx,
            self.origin_x + (self.nx - 0.5) * self.dx,
            self.origin_y - half_dy,
            self.origin_y + (self.ny - 0.5) * self.dy,
        )

    @property
    def center(self) -> tuple[float, float]:
        xs = self.x_coordinates()
        ys = self.y_coordinates()
        return (float((xs[0] + xs[-1]) * 0.5), float((ys[0] + ys[-1]) * 0.5))

    def x_coordinates(self) -> FloatGrid:
        return self.origin_x + np.arange(self.nx, dtype=np.float64) * self.dx

    def y_coordinates(self) -> FloatGrid:
        return self.origin_y + np.arange(self.ny, dtype=np.float64) * self.dy

    def meshgrid(self) -> tuple[FloatGrid, FloatGrid]:
        return np.meshgrid(self.x_coordinates(), self.y_coordinates())

    def contains(self, position: tuple[float, float]) -> bool:
        x, y = position
        x_min, x_max, y_min, y_max = self.extent
        return x_min <= x <= x_max and y_min <= y <= y_max

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> GridSpec2_5D:
        return cls(
            nx=int(data["nx"]),
            ny=int(data["ny"]),
            dx=float(data["dx"]),
            dy=float(data["dy"]),
            origin_x=float(data.get("origin_x", 0.0)),
            origin_y=float(data.get("origin_y", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class ScenarioMetadata2_5D:
    scenario_id: str
    scenario_type: ScenarioType2_5D
    seed: int = 1
    fixture_kind: FixtureKind2_5D | None = None
    generator: str = "raftsim.scenario2_5d"
    generator_version: str = "0.1"
    description: str = ""
    river_id: str | None = None
    section_id: str | None = None
    coordinate_reference_system: str | None = None
    source_manifest: str | None = None
    gauge_source: str | None = None
    season_preset: str | None = None
    flow_percentile: float | None = None
    flow_band: str | None = None
    difficulty_preset: str | None = None
    confidence_score: float | None = None
    provenance: dict[str, MetadataValue] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "seed": self.seed,
            "fixture_kind": self.fixture_kind,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "description": self.description,
            "river_id": self.river_id,
            "section_id": self.section_id,
            "coordinate_reference_system": self.coordinate_reference_system,
            "source_manifest": self.source_manifest,
            "gauge_source": self.gauge_source,
            "season_preset": self.season_preset,
            "flow_percentile": self.flow_percentile,
            "flow_band": self.flow_band,
            "difficulty_preset": self.difficulty_preset,
            "confidence_score": self.confidence_score,
            "provenance": self.provenance,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> ScenarioMetadata2_5D:
        provenance = data.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}
        return cls(
            scenario_id=str(data["scenario_id"]),
            scenario_type=str(data["scenario_type"]),  # type: ignore[arg-type]
            seed=int(data.get("seed", 1)),
            fixture_kind=data.get("fixture_kind"),  # type: ignore[arg-type]
            generator=str(data.get("generator", "raftsim.scenario2_5d")),
            generator_version=str(data.get("generator_version", "0.1")),
            description=str(data.get("description", "")),
            river_id=_optional_str(data.get("river_id")),
            section_id=_optional_str(data.get("section_id")),
            coordinate_reference_system=_optional_str(data.get("coordinate_reference_system")),
            source_manifest=_optional_str(data.get("source_manifest")),
            gauge_source=_optional_str(data.get("gauge_source")),
            season_preset=_optional_str(data.get("season_preset")),
            flow_percentile=_optional_float(data.get("flow_percentile")),
            flow_band=_optional_str(data.get("flow_band")),
            difficulty_preset=_optional_str(data.get("difficulty_preset")),
            confidence_score=_optional_float(data.get("confidence_score")),
            provenance=provenance,  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class BoundaryHydrographSample2_5D:
    time: float
    stage: float | None = None
    depth: float | None = None
    velocity: tuple[float, float] | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "time": self.time,
            "stage": self.stage,
            "depth": self.depth,
            "velocity": self.velocity,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> BoundaryHydrographSample2_5D:
        velocity = data.get("velocity")
        parsed_velocity = None
        if velocity is not None:
            velocity_values = tuple(float(value) for value in velocity)  # type: ignore[union-attr]
            if len(velocity_values) != 2:
                raise ValueError("hydrograph velocity must contain two components.")
            parsed_velocity = (velocity_values[0], velocity_values[1])
        return cls(
            time=float(data["time"]),
            stage=_optional_float(data.get("stage")),
            depth=_optional_float(data.get("depth")),
            velocity=parsed_velocity,
        )


@dataclass(frozen=True, slots=True)
class BoundaryCondition2_5D:
    edge: BoundaryEdge2_5D
    kind: BoundaryKind2_5D
    stage: float | None = None
    depth: float | None = None
    velocity: tuple[float, float] | None = None
    hydrograph: tuple[BoundaryHydrographSample2_5D, ...] = ()
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "hydrograph", tuple(self.hydrograph))

    def to_json_dict(self) -> dict[str, object]:
        return {
            "edge": self.edge,
            "kind": self.kind,
            "stage": self.stage,
            "depth": self.depth,
            "velocity": self.velocity,
            "hydrograph": [sample.to_json_dict() for sample in self.hydrograph],
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> BoundaryCondition2_5D:
        velocity = data.get("velocity")
        parsed_velocity = None
        if velocity is not None:
            velocity_values = tuple(float(value) for value in velocity)  # type: ignore[union-attr]
            if len(velocity_values) != 2:
                raise ValueError("boundary velocity must contain two components.")
            parsed_velocity = (velocity_values[0], velocity_values[1])
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        hydrograph_data = data.get("hydrograph", [])
        if not isinstance(hydrograph_data, list):
            hydrograph_data = []
        return cls(
            edge=str(data["edge"]),  # type: ignore[arg-type]
            kind=str(data["kind"]),  # type: ignore[arg-type]
            stage=_optional_float(data.get("stage")),
            depth=_optional_float(data.get("depth")),
            velocity=parsed_velocity,
            hydrograph=tuple(BoundaryHydrographSample2_5D.from_json_dict(item) for item in hydrograph_data),
            metadata=metadata,  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Feature2_5D:
    kind: FeatureKind2_5D
    center: tuple[float, float]
    radius: float
    strength: float = 1.0
    length: float = 0.0
    width: float = 0.0
    angle: float = 0.0
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.radius < 0.0:
            raise ValueError("feature radius must be non-negative.")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "center": {"x": self.center[0], "y": self.center[1]},
            "radius": self.radius,
            "strength": self.strength,
            "length": self.length,
            "width": self.width,
            "angle": self.angle,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Feature2_5D:
        center = data["center"]
        if not isinstance(center, dict):
            raise ValueError("feature center must be an object.")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            kind=str(data["kind"]),  # type: ignore[arg-type]
            center=(float(center["x"]), float(center["y"])),
            radius=float(data.get("radius", 0.0)),
            strength=float(data.get("strength", 1.0)),
            length=float(data.get("length", 0.0)),
            width=float(data.get("width", 0.0)),
            angle=float(data.get("angle", 0.0)),
            metadata=metadata,  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Probe2_5D:
    probe_id: str
    position: tuple[float, float]
    kind: ProbeKind2_5D = "point"
    normal: tuple[float, float] | None = None
    length: float = 0.0
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "position": {"x": self.position[0], "y": self.position[1]},
            "kind": self.kind,
            "normal": None if self.normal is None else {"x": self.normal[0], "y": self.normal[1]},
            "length": self.length,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Probe2_5D:
        position = data["position"]
        if not isinstance(position, dict):
            raise ValueError("probe position must be an object.")
        normal = data.get("normal")
        parsed_normal = None
        if isinstance(normal, dict):
            parsed_normal = (float(normal["x"]), float(normal["y"]))
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            probe_id=str(data["probe_id"]),
            position=(float(position["x"]), float(position["y"])),
            kind=str(data.get("kind", "point")),  # type: ignore[arg-type]
            normal=parsed_normal,
            length=float(data.get("length", 0.0)),
            metadata=metadata,  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class RaftParameters2_5D:
    mass_kg: float = 420.0
    length_m: float = 4.3
    width_m: float = 1.9
    tube_radius_m: float = 0.28
    guide_mass_kg: float = 85.0
    passenger_mass_kg: float = 75.0
    passenger_count: int = 6
    drag_coefficient: float = 1.25
    grounding_friction: float = 0.65

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> RaftParameters2_5D:
        return cls(
            mass_kg=float(data.get("mass_kg", 420.0)),
            length_m=float(data.get("length_m", 4.3)),
            width_m=float(data.get("width_m", 1.9)),
            tube_radius_m=float(data.get("tube_radius_m", 0.28)),
            guide_mass_kg=float(data.get("guide_mass_kg", 85.0)),
            passenger_mass_kg=float(data.get("passenger_mass_kg", 75.0)),
            passenger_count=int(data.get("passenger_count", 6)),
            drag_coefficient=float(data.get("drag_coefficient", 1.25)),
            grounding_friction=float(data.get("grounding_friction", 0.65)),
        )


@dataclass(frozen=True, slots=True)
class InitialWaterState2_5D:
    depth: FloatGrid
    eta: FloatGrid
    u: FloatGrid
    v: FloatGrid
    hu: FloatGrid
    hv: FloatGrid
    wet: BoolGrid

    def __post_init__(self) -> None:
        for name in ("depth", "eta", "u", "v", "hu", "hv"):
            value = np.asarray(getattr(self, name), dtype=np.float64)
            if value.ndim != 2:
                raise ValueError(f"{name} must be a 2D grid.")
            object.__setattr__(self, name, value.copy())
        wet = np.asarray(self.wet, dtype=np.bool_)
        if wet.ndim != 2:
            raise ValueError("wet must be a 2D grid.")
        object.__setattr__(self, "wet", wet.copy())

    @classmethod
    def from_depth_velocity(
        cls,
        bed: FloatGrid,
        depth: float | FloatGrid,
        u: float | FloatGrid = 0.0,
        v: float | FloatGrid = 0.0,
        *,
        wet_threshold: float = 1.0e-6,
    ) -> InitialWaterState2_5D:
        bed_grid = np.asarray(bed, dtype=np.float64)
        if bed_grid.ndim != 2:
            raise ValueError("bed must be a 2D grid.")
        depth_grid = np.maximum(_coerce_grid(depth, bed_grid.shape, "depth"), 0.0)
        u_grid = _coerce_grid(u, bed_grid.shape, "u")
        v_grid = _coerce_grid(v, bed_grid.shape, "v")
        wet = depth_grid > wet_threshold
        u_grid = np.where(wet, u_grid, 0.0)
        v_grid = np.where(wet, v_grid, 0.0)
        return cls(
            depth=depth_grid,
            eta=bed_grid + depth_grid,
            u=u_grid,
            v=v_grid,
            hu=depth_grid * u_grid,
            hv=depth_grid * v_grid,
            wet=wet,
        )

    def to_npz(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_path,
            depth=self.depth,
            eta=self.eta,
            u=self.u,
            v=self.v,
            hu=self.hu,
            hv=self.hv,
            wet=self.wet,
        )
        return output_path

    @classmethod
    def from_npz(cls, path: str | Path) -> InitialWaterState2_5D:
        with np.load(Path(path)) as data:
            return cls(
                depth=np.asarray(data["depth"], dtype=np.float64),
                eta=np.asarray(data["eta"], dtype=np.float64),
                u=np.asarray(data["u"], dtype=np.float64),
                v=np.asarray(data["v"], dtype=np.float64),
                hu=np.asarray(data["hu"], dtype=np.float64),
                hv=np.asarray(data["hv"], dtype=np.float64),
                wet=np.asarray(data["wet"], dtype=np.bool_),
            )


@dataclass(frozen=True, slots=True)
class Scenario2_5D:
    metadata: ScenarioMetadata2_5D
    grid: GridSpec2_5D
    fixed_dt: float
    duration: float
    bed: FloatGrid
    initial_state: InitialWaterState2_5D
    boundaries: tuple[BoundaryCondition2_5D, ...]
    features: tuple[Feature2_5D, ...] = ()
    probes: tuple[Probe2_5D, ...] = ()
    raft: RaftParameters2_5D = field(default_factory=RaftParameters2_5D)
    roughness: float = 0.035

    def __post_init__(self) -> None:
        if self.fixed_dt <= 0.0:
            raise ValueError("fixed_dt must be positive.")
        if self.duration <= 0.0:
            raise ValueError("duration must be positive.")
        if self.roughness < 0.0:
            raise ValueError("roughness must be non-negative.")
        bed = np.asarray(self.bed, dtype=np.float64)
        if bed.ndim != 2:
            raise ValueError("bed must be a 2D grid.")
        object.__setattr__(self, "bed", bed.copy())
        object.__setattr__(self, "boundaries", tuple(self.boundaries))
        object.__setattr__(self, "features", tuple(self.features))
        object.__setattr__(self, "probes", tuple(self.probes))

    def validate(self) -> ScenarioValidation2_5D:
        checks: list[ValidationCheck2_5D] = []
        expected_shape = self.grid.shape
        state_arrays = (
            ("depth", self.initial_state.depth),
            ("eta", self.initial_state.eta),
            ("u", self.initial_state.u),
            ("v", self.initial_state.v),
            ("hu", self.initial_state.hu),
            ("hv", self.initial_state.hv),
            ("wet", self.initial_state.wet),
        )

        all_shapes = [self.bed.shape, *[array.shape for _, array in state_arrays]]
        checks.append(
            ValidationCheck2_5D(
                "grid_shapes",
                all(shape == expected_shape for shape in all_shapes),
                f"expected={expected_shape} actual={all_shapes}",
            )
        )

        float_arrays = [self.bed, self.initial_state.depth, self.initial_state.eta, self.initial_state.u, self.initial_state.v]
        finite = all(bool(np.isfinite(array).all()) for array in float_arrays)
        checks.append(ValidationCheck2_5D("finite_fields", finite, f"arrays={len(float_arrays)}"))

        minimum_depth = float(np.min(self.initial_state.depth))
        checks.append(
            ValidationCheck2_5D(
                "nonnegative_depth",
                minimum_depth >= -1.0e-10,
                f"min_depth={minimum_depth:.6f}",
            )
        )

        if self.bed.shape == expected_shape and self.initial_state.depth.shape == expected_shape:
            eta_error = float(np.max(np.abs((self.bed + self.initial_state.depth) - self.initial_state.eta)))
            momentum_error = max(
                float(np.max(np.abs(self.initial_state.depth * self.initial_state.u - self.initial_state.hu))),
                float(np.max(np.abs(self.initial_state.depth * self.initial_state.v - self.initial_state.hv))),
            )
            wet_matches = bool(np.array_equal(self.initial_state.wet, self.initial_state.depth > 1.0e-6))
        else:
            eta_error = float("inf")
            momentum_error = float("inf")
            wet_matches = False
        checks.append(ValidationCheck2_5D("eta_matches_bed_plus_depth", eta_error < 1.0e-9, f"max_error={eta_error:.3e}"))
        checks.append(ValidationCheck2_5D("momentum_matches_velocity", momentum_error < 1.0e-9, f"max_error={momentum_error:.3e}"))
        checks.append(ValidationCheck2_5D("wet_mask_matches_depth", wet_matches, "threshold=1e-6"))

        boundary_edges = {boundary.edge for boundary in self.boundaries}
        required_edges = {"west", "east", "south", "north"}
        checks.append(
            ValidationCheck2_5D(
                "boundary_edges",
                boundary_edges == required_edges,
                f"edges={sorted(boundary_edges)}",
            )
        )

        probes_inside = all(self.grid.contains(probe.position) for probe in self.probes)
        checks.append(ValidationCheck2_5D("probes_inside_grid", probes_inside, f"probes={len(self.probes)}"))

        feature_centers_inside = all(self.grid.contains(feature.center) for feature in self.features)
        checks.append(
            ValidationCheck2_5D(
                "feature_centers_inside_grid",
                feature_centers_inside,
                f"features={len(self.features)}",
            )
        )
        return ScenarioValidation2_5D(tuple(checks))

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCENARIO_SCHEMA_VERSION,
            "metadata": self.metadata.to_json_dict(),
            "grid": self.grid.to_json_dict(),
            "fixed_dt": self.fixed_dt,
            "duration": self.duration,
            "roughness": self.roughness,
            "raft": self.raft.to_json_dict(),
            "boundaries": [boundary.to_json_dict() for boundary in self.boundaries],
            "feature_count": len(self.features),
            "probe_count": len(self.probes),
            "array_files": {
                "bed": BED_FILE,
                "initial_state": INITIAL_STATE_FILE,
                "features": FEATURES_FILE,
                "probes": PROBES_FILE,
            },
        }

    def write_package(self, directory: str | Path) -> Path:
        validation = self.validate()
        if not validation.passed:
            details = "; ".join(validation.summary_lines())
            raise ValueError(f"Cannot write invalid scenario package: {details}")

        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        np.save(output_dir / BED_FILE, self.bed)
        self.initial_state.to_npz(output_dir / INITIAL_STATE_FILE)
        _write_json(output_dir / FEATURES_FILE, {"features": [feature.to_json_dict() for feature in self.features]})
        _write_json(output_dir / PROBES_FILE, {"probes": [probe.to_json_dict() for probe in self.probes]})
        _write_json(output_dir / "scenario.json", self.to_json_dict())
        return output_dir


@dataclass(frozen=True, slots=True)
class FixtureScenario2_5DParameters:
    fixture: FixtureKind2_5D = "flat_pool"
    seed: int = 1
    nx: int = 64
    ny: int = 32
    dx: float = 1.0
    dy: float = 1.0
    base_depth: float = 1.25
    high_depth: float = 2.5
    low_depth: float = 0.35
    inflow_speed: float = 1.4
    downstream_slope: float = 0.012
    step_height: float = 0.45
    fixed_dt: float = 1.0 / 60.0
    duration: float = 6.0

    def __post_init__(self) -> None:
        if self.base_depth <= 0.0:
            raise ValueError("base_depth must be positive.")
        if self.high_depth <= self.low_depth:
            raise ValueError("high_depth must be greater than low_depth.")


def generate_fixture_scenario2_5d(parameters: FixtureScenario2_5DParameters | None = None) -> Scenario2_5D:
    """Generate a deterministic 2.5D fixture scenario package in memory."""

    params = parameters or FixtureScenario2_5DParameters()
    origin_y = -0.5 * (params.ny - 1) * params.dy
    grid = GridSpec2_5D(nx=params.nx, ny=params.ny, dx=params.dx, dy=params.dy, origin_x=0.0, origin_y=origin_y)
    x, y = grid.meshgrid()
    bed = np.zeros(grid.shape, dtype=np.float64)
    depth = np.full(grid.shape, params.base_depth, dtype=np.float64)
    u = np.zeros(grid.shape, dtype=np.float64)
    v = np.zeros(grid.shape, dtype=np.float64)
    features: list[Feature2_5D] = []
    description = ""

    if params.fixture == "flat_pool":
        description = "Flat still-water pool for baseline state and raft float tests."
        boundaries = _wall_boundaries()
    elif params.fixture == "uniform_channel":
        description = "Uniform channel flow with constant downstream velocity."
        bed = -params.downstream_slope * x
        u = np.full(grid.shape, params.inflow_speed, dtype=np.float64)
        boundaries = _channel_boundaries(params.base_depth, params.inflow_speed)
    elif params.fixture == "dam_break":
        description = "Left-high/right-low dam-break initial condition."
        split_x = grid.center[0]
        depth = np.where(x < split_x, params.high_depth, params.low_depth)
        features.append(
            Feature2_5D(
                kind="ledge",
                center=(split_x, grid.center[1]),
                radius=0.0,
                strength=1.0,
                length=(params.ny - 1) * params.dy,
                metadata={"fixture_role": "initial_depth_discontinuity"},
            )
        )
        boundaries = _wall_boundaries()
    elif params.fixture == "bed_step":
        description = "Channel flow over a downstream bed step."
        step_x = grid.center[0]
        bed = np.where(x >= step_x, params.step_height, 0.0)
        eta = params.base_depth
        depth = np.maximum(eta - bed, 0.0)
        u = np.where(depth > 1.0e-6, params.inflow_speed, 0.0)
        features.append(
            Feature2_5D(
                kind="ledge",
                center=(step_x, grid.center[1]),
                radius=0.0,
                strength=params.step_height,
                length=(params.ny - 1) * params.dy,
                metadata={"fixture_role": "bed_step"},
            )
        )
        boundaries = _channel_boundaries(float(depth[:, 0].mean()), params.inflow_speed)
    elif params.fixture == "constriction":
        description = "Channel flow through a deterministic dry-bank constriction."
        center_x, center_y = grid.center
        full_half_width = max(params.dy * 3.0, (params.ny - 1) * params.dy * 0.38)
        throat_half_width = max(params.dy * 2.0, full_half_width * 0.42)
        throat = np.exp(-((x - center_x) ** 2) / max((params.nx * params.dx * 0.18) ** 2, 1.0e-6))
        local_half_width = full_half_width - (full_half_width - throat_half_width) * throat
        wet_channel = np.abs(y - center_y) <= local_half_width
        bed = np.where(wet_channel, 0.0, params.base_depth + 0.75)
        depth = np.where(wet_channel, params.base_depth, 0.0)
        speed_scale = full_half_width / np.maximum(local_half_width, params.dy)
        u = np.where(wet_channel, params.inflow_speed * speed_scale, 0.0)
        features.append(
            Feature2_5D(
                kind="constriction",
                center=(center_x, center_y),
                radius=float(throat_half_width),
                strength=float(speed_scale.max()),
                length=float(params.nx * params.dx * 0.36),
                width=float(throat_half_width * 2.0),
                metadata={"fixture_role": "dry_bank_throat"},
            )
        )
        boundaries = _channel_boundaries(params.base_depth, params.inflow_speed)
    elif params.fixture == "wet_dry_shoreline":
        description = "Sloped shoreline with deterministic wet and dry cells."
        y_min = float(y.min())
        y_span = max(float(y.max() - y_min), 1.0e-6)
        bed = params.high_depth * ((y - y_min) / y_span)
        eta = params.base_depth
        depth = np.maximum(eta - bed, 0.0)
        u = np.where(depth > 1.0e-6, params.inflow_speed * 0.25, 0.0)
        features.append(
            Feature2_5D(
                kind="shallow",
                center=(grid.center[0], y_min + y_span * 0.5),
                radius=float(y_span * 0.2),
                strength=1.0,
                length=float((params.nx - 1) * params.dx),
                width=float(y_span * 0.4),
                metadata={"fixture_role": "wet_dry_transition"},
            )
        )
        boundaries = (
            BoundaryCondition2_5D("west", "open"),
            BoundaryCondition2_5D("east", "open"),
            BoundaryCondition2_5D("south", "wall"),
            BoundaryCondition2_5D("north", "wall"),
        )
    else:
        raise ValueError(f"Unknown 2.5D fixture: {params.fixture}")

    state = InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v)
    metadata = ScenarioMetadata2_5D(
        scenario_id=f"{params.fixture}_seed_{params.seed}",
        scenario_type="fixture",
        seed=params.seed,
        fixture_kind=params.fixture,
        description=description,
        provenance={"source": "deterministic_fixture_generator"},
    )
    return Scenario2_5D(
        metadata=metadata,
        grid=grid,
        fixed_dt=params.fixed_dt,
        duration=params.duration,
        bed=bed,
        initial_state=state,
        boundaries=boundaries,
        features=tuple(features),
        probes=_default_probes(grid),
        raft=RaftParameters2_5D(),
    )


def read_scenario2_5d_package(path: str | Path) -> Scenario2_5D:
    root = Path(path)
    scenario_path = root if root.name == "scenario.json" else root / "scenario.json"
    package_dir = scenario_path.parent
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    schema_version = data.get("schema_version")
    if schema_version != SCENARIO_SCHEMA_VERSION:
        raise ValueError(f"Unsupported scenario schema version: {schema_version!r}")

    array_files = data.get("array_files", {})
    if not isinstance(array_files, dict):
        raise ValueError("scenario.json array_files must be an object.")

    bed = np.asarray(np.load(package_dir / str(array_files.get("bed", BED_FILE))), dtype=np.float64)
    initial_state = InitialWaterState2_5D.from_npz(package_dir / str(array_files.get("initial_state", INITIAL_STATE_FILE)))

    features_data = json.loads((package_dir / str(array_files.get("features", FEATURES_FILE))).read_text(encoding="utf-8"))
    probes_data = json.loads((package_dir / str(array_files.get("probes", PROBES_FILE))).read_text(encoding="utf-8"))

    return Scenario2_5D(
        metadata=ScenarioMetadata2_5D.from_json_dict(data["metadata"]),  # type: ignore[arg-type]
        grid=GridSpec2_5D.from_json_dict(data["grid"]),  # type: ignore[arg-type]
        fixed_dt=float(data["fixed_dt"]),
        duration=float(data["duration"]),
        bed=bed,
        initial_state=initial_state,
        boundaries=tuple(BoundaryCondition2_5D.from_json_dict(item) for item in data["boundaries"]),  # type: ignore[index]
        features=tuple(Feature2_5D.from_json_dict(item) for item in features_data.get("features", [])),
        probes=tuple(Probe2_5D.from_json_dict(item) for item in probes_data.get("probes", [])),
        raft=RaftParameters2_5D.from_json_dict(data.get("raft", {})),  # type: ignore[arg-type]
        roughness=float(data.get("roughness", 0.035)),
    )


def _coerce_grid(value: float | FloatGrid, shape: tuple[int, int], name: str) -> FloatGrid:
    array = np.asarray(value, dtype=np.float64)
    if array.shape == ():
        return np.full(shape, float(array), dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} shape {array.shape} does not match expected shape {shape}.")
    return array.copy()


def _wall_boundaries() -> tuple[BoundaryCondition2_5D, ...]:
    return (
        BoundaryCondition2_5D("west", "wall"),
        BoundaryCondition2_5D("east", "wall"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )


def _channel_boundaries(depth: float, speed: float) -> tuple[BoundaryCondition2_5D, ...]:
    return (
        BoundaryCondition2_5D("west", "inflow", depth=depth, velocity=(speed, 0.0)),
        BoundaryCondition2_5D("east", "outflow"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )


def _default_probes(grid: GridSpec2_5D) -> tuple[Probe2_5D, ...]:
    center_y = grid.center[1]
    xs = grid.x_coordinates()
    return (
        Probe2_5D("upstream_center", (float(xs[max(0, grid.nx // 4)]), center_y)),
        Probe2_5D("midstream_center", grid.center),
        Probe2_5D("downstream_center", (float(xs[min(grid.nx - 1, (grid.nx * 3) // 4)]), center_y)),
        Probe2_5D(
            "mid_cross_section",
            grid.center,
            kind="cross_section",
            normal=(0.0, 1.0),
            length=float((grid.ny - 1) * grid.dy),
        ),
    )


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)
