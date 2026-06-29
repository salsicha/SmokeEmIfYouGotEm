"""Cascading 2.5D reach metadata for pool-and-drop river packages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .scenario2_5d import GridSpec2_5D, Scenario2_5D, read_scenario2_5d_package

MetadataValue = str | int | float | bool | None
IntGrid = NDArray[np.int32]

CASCADING_SCHEMA_VERSION = "raftsim.cascading2_5d.v0"
CASCADING_METADATA_FILE = "cascading_metadata.json"
CASCADING_ANNOTATIONS_FILE = "cascading_annotations.npz"
ReachKind2_5D = Literal["pool", "tongue", "drop", "wave_train", "eddy_recovery", "boulder_garden", "runout"]
BankShapeKind2_5D = Literal["trapezoid", "bedrock", "alluvial", "vegetated", "constructed", "unknown"]
DropGeometryKind2_5D = Literal["ramp", "ledge", "mixed"]
HydraulicControlKind2_5D = Literal[
    "subcritical_pool_tailwater",
    "critical_crest",
    "hydraulic_jump",
    "retentive_hole",
    "wave_train",
    "unknown",
]
PoolOutflowControlKind2_5D = Literal["free_outflow", "tailwater_limited", "drop_controlled", "backwater", "unknown"]


@dataclass(frozen=True, slots=True)
class HandoffConservationThresholds2_5D:
    max_mass_flux_delta: float = 0.15
    max_momentum_flux_delta: float = 0.35
    max_surface_elevation_delta: float = 0.08
    max_energy_gain: float = 0.05
    max_wet_fraction_delta: float = 0.35

    def __post_init__(self) -> None:
        for name in (
            "max_mass_flux_delta",
            "max_momentum_flux_delta",
            "max_surface_elevation_delta",
            "max_energy_gain",
            "max_wet_fraction_delta",
        ):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be non-negative.")

    def to_json_dict(self) -> dict[str, float]:
        return {
            "max_mass_flux_delta": self.max_mass_flux_delta,
            "max_momentum_flux_delta": self.max_momentum_flux_delta,
            "max_surface_elevation_delta": self.max_surface_elevation_delta,
            "max_energy_gain": self.max_energy_gain,
            "max_wet_fraction_delta": self.max_wet_fraction_delta,
        }


@dataclass(frozen=True, slots=True)
class HandoffConservationCheck2_5D:
    transition_id: str
    upstream_reach_id: str
    downstream_reach_id: str
    upstream_column: int
    downstream_column: int
    mass_flux_delta: float
    momentum_flux_delta: float
    surface_elevation_delta: float
    energy_delta: float
    wet_fraction_delta: float
    mass_flux_passed: bool
    momentum_flux_passed: bool
    surface_elevation_passed: bool
    energy_passed: bool
    wet_front_passed: bool

    @property
    def passed(self) -> bool:
        return (
            self.mass_flux_passed
            and self.momentum_flux_passed
            and self.surface_elevation_passed
            and self.energy_passed
            and self.wet_front_passed
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "transition_id": self.transition_id,
            "upstream_reach_id": self.upstream_reach_id,
            "downstream_reach_id": self.downstream_reach_id,
            "upstream_column": self.upstream_column,
            "downstream_column": self.downstream_column,
            "mass_flux_delta": self.mass_flux_delta,
            "momentum_flux_delta": self.momentum_flux_delta,
            "surface_elevation_delta": self.surface_elevation_delta,
            "energy_delta": self.energy_delta,
            "wet_fraction_delta": self.wet_fraction_delta,
            "mass_flux_passed": self.mass_flux_passed,
            "momentum_flux_passed": self.momentum_flux_passed,
            "surface_elevation_passed": self.surface_elevation_passed,
            "energy_passed": self.energy_passed,
            "wet_front_passed": self.wet_front_passed,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class HandoffConservationReport2_5D:
    scenario_id: str
    thresholds: HandoffConservationThresholds2_5D
    checks: tuple[HandoffConservationCheck2_5D, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "thresholds": self.thresholds.to_json_dict(),
            "checks": [check.to_json_dict() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class StationProfilePoint2_5D:
    station: float
    value: float

    def __post_init__(self) -> None:
        if self.station < 0.0:
            raise ValueError("profile station must be non-negative.")

    def to_json_dict(self) -> dict[str, float]:
        return {"station": self.station, "value": self.value}

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> StationProfilePoint2_5D:
        return cls(station=float(data["station"]), value=float(data["value"]))


@dataclass(frozen=True, slots=True)
class ReachGridTransform2_5D:
    origin_x: float
    origin_y: float
    station_origin: float
    lateral_origin: float = 0.0
    rotation_degrees: float = 0.0
    dx: float = 1.0
    dy: float = 1.0

    def __post_init__(self) -> None:
        if self.dx <= 0.0 or self.dy <= 0.0:
            raise ValueError("reach grid transform spacing must be positive.")

    def to_json_dict(self) -> dict[str, float]:
        return {
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "station_origin": self.station_origin,
            "lateral_origin": self.lateral_origin,
            "rotation_degrees": self.rotation_degrees,
            "dx": self.dx,
            "dy": self.dy,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> ReachGridTransform2_5D:
        return cls(
            origin_x=float(data["origin_x"]),
            origin_y=float(data["origin_y"]),
            station_origin=float(data["station_origin"]),
            lateral_origin=float(data.get("lateral_origin", 0.0)),
            rotation_degrees=float(data.get("rotation_degrees", 0.0)),
            dx=float(data.get("dx", 1.0)),
            dy=float(data.get("dy", 1.0)),
        )


@dataclass(frozen=True, slots=True)
class BankShape2_5D:
    shape: BankShapeKind2_5D = "unknown"
    left_bank_offset_m: float = 9.0
    right_bank_offset_m: float = -9.0
    left_bank_slope: float = 0.35
    right_bank_slope: float = 0.35

    def __post_init__(self) -> None:
        if self.left_bank_offset_m <= self.right_bank_offset_m:
            raise ValueError("left bank offset must be greater than right bank offset.")
        if self.left_bank_slope < 0.0 or self.right_bank_slope < 0.0:
            raise ValueError("bank slopes must be non-negative.")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "shape": self.shape,
            "left_bank_offset_m": self.left_bank_offset_m,
            "right_bank_offset_m": self.right_bank_offset_m,
            "left_bank_slope": self.left_bank_slope,
            "right_bank_slope": self.right_bank_slope,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> BankShape2_5D:
        return cls(
            shape=str(data.get("shape", "unknown")),  # type: ignore[arg-type]
            left_bank_offset_m=float(data.get("left_bank_offset_m", 9.0)),
            right_bank_offset_m=float(data.get("right_bank_offset_m", -9.0)),
            left_bank_slope=float(data.get("left_bank_slope", 0.35)),
            right_bank_slope=float(data.get("right_bank_slope", 0.35)),
        )


@dataclass(frozen=True, slots=True)
class ReachMetadata2_5D:
    reach_id: str
    kind: ReachKind2_5D
    station_start: float
    station_end: float
    local_grid: ReachGridTransform2_5D
    slope_profile: tuple[StationProfilePoint2_5D, ...]
    width_profile: tuple[StationProfilePoint2_5D, ...]
    bank_shape: BankShape2_5D
    bed_roughness: float = 0.035
    boulder_density: float = 0.0
    vegetation_flags: tuple[str, ...] = ()
    debris_flags: tuple[str, ...] = ()
    confidence_score: float = 0.5
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reach_id:
            raise ValueError("reach_id is required.")
        if self.station_end <= self.station_start:
            raise ValueError("reach station_end must be greater than station_start.")
        if self.bed_roughness < 0.0:
            raise ValueError("reach bed roughness must be non-negative.")
        if not 0.0 <= self.boulder_density <= 1.0:
            raise ValueError("boulder density must be between 0 and 1.")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("reach confidence score must be between 0 and 1.")
        object.__setattr__(self, "slope_profile", tuple(self.slope_profile))
        object.__setattr__(self, "width_profile", tuple(self.width_profile))
        object.__setattr__(self, "vegetation_flags", tuple(self.vegetation_flags))
        object.__setattr__(self, "debris_flags", tuple(self.debris_flags))
        if not self.slope_profile:
            raise ValueError("reach slope profile cannot be empty.")
        if not self.width_profile:
            raise ValueError("reach width profile cannot be empty.")
        for profile_name, points in (("slope", self.slope_profile), ("width", self.width_profile)):
            stations = [point.station for point in points]
            if stations != sorted(stations):
                raise ValueError(f"{profile_name} profile stations must be sorted.")
            if stations[0] < self.station_start or stations[-1] > self.station_end:
                raise ValueError(f"{profile_name} profile stations must lie inside reach station range.")
        if any(point.value <= 0.0 for point in self.width_profile):
            raise ValueError("width profile values must be positive.")

    @property
    def length(self) -> float:
        return self.station_end - self.station_start

    def to_json_dict(self) -> dict[str, object]:
        return {
            "reach_id": self.reach_id,
            "kind": self.kind,
            "station_start": self.station_start,
            "station_end": self.station_end,
            "length": self.length,
            "local_grid": self.local_grid.to_json_dict(),
            "slope_profile": [point.to_json_dict() for point in self.slope_profile],
            "width_profile": [point.to_json_dict() for point in self.width_profile],
            "bank_shape": self.bank_shape.to_json_dict(),
            "bed_roughness": self.bed_roughness,
            "boulder_density": self.boulder_density,
            "vegetation_flags": list(self.vegetation_flags),
            "debris_flags": list(self.debris_flags),
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> ReachMetadata2_5D:
        return cls(
            reach_id=str(data["reach_id"]),
            kind=str(data["kind"]),  # type: ignore[arg-type]
            station_start=float(data["station_start"]),
            station_end=float(data["station_end"]),
            local_grid=ReachGridTransform2_5D.from_json_dict(data["local_grid"]),  # type: ignore[arg-type]
            slope_profile=tuple(
                StationProfilePoint2_5D.from_json_dict(point)
                for point in data.get("slope_profile", [])  # type: ignore[union-attr]
            ),
            width_profile=tuple(
                StationProfilePoint2_5D.from_json_dict(point)
                for point in data.get("width_profile", [])  # type: ignore[union-attr]
            ),
            bank_shape=BankShape2_5D.from_json_dict(data.get("bank_shape", {})),  # type: ignore[arg-type]
            bed_roughness=float(data.get("bed_roughness", 0.035)),
            boulder_density=float(data.get("boulder_density", 0.0)),
            vegetation_flags=tuple(str(value) for value in data.get("vegetation_flags", [])),  # type: ignore[union-attr]
            debris_flags=tuple(str(value) for value in data.get("debris_flags", [])),  # type: ignore[union-attr]
            confidence_score=float(data.get("confidence_score", 0.5)),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )


@dataclass(frozen=True, slots=True)
class DropTransitionMetadata2_5D:
    transition_id: str
    upstream_reach_id: str
    downstream_reach_id: str
    crest_station: float
    bed_elevation_fall: float
    geometry_kind: DropGeometryKind2_5D = "ramp"
    ramp_length: float = 0.0
    ledge_length: float = 0.0
    tailwater_depth: float = 0.0
    expected_hydraulic_control: HydraulicControlKind2_5D = "unknown"
    recirculation_risk: float = 0.0
    aeration_proxy: float = 0.0
    turbulence_proxy: float = 0.0
    hazard_tags: tuple[str, ...] = ()
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.transition_id:
            raise ValueError("transition_id is required.")
        if not self.upstream_reach_id or not self.downstream_reach_id:
            raise ValueError("drop transition reach ids are required.")
        if self.upstream_reach_id == self.downstream_reach_id:
            raise ValueError("drop transition must connect two distinct reaches.")
        if self.crest_station < 0.0:
            raise ValueError("drop transition crest station must be non-negative.")
        if self.bed_elevation_fall < 0.0:
            raise ValueError("drop transition bed-elevation fall must be non-negative.")
        if self.ramp_length < 0.0 or self.ledge_length < 0.0:
            raise ValueError("drop transition ramp/ledge lengths must be non-negative.")
        if self.ramp_length == 0.0 and self.ledge_length == 0.0:
            raise ValueError("drop transition must define a ramp or ledge length.")
        if self.tailwater_depth < 0.0:
            raise ValueError("drop transition tailwater depth must be non-negative.")
        for name, value in (
            ("recirculation risk", self.recirculation_risk),
            ("aeration proxy", self.aeration_proxy),
            ("turbulence proxy", self.turbulence_proxy),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"drop transition {name} must be between 0 and 1.")
        object.__setattr__(self, "hazard_tags", tuple(self.hazard_tags))

    @property
    def control_length(self) -> float:
        return self.ramp_length + self.ledge_length

    def to_json_dict(self) -> dict[str, object]:
        return {
            "transition_id": self.transition_id,
            "upstream_reach_id": self.upstream_reach_id,
            "downstream_reach_id": self.downstream_reach_id,
            "crest_station": self.crest_station,
            "bed_elevation_fall": self.bed_elevation_fall,
            "geometry_kind": self.geometry_kind,
            "ramp_length": self.ramp_length,
            "ledge_length": self.ledge_length,
            "control_length": self.control_length,
            "tailwater_depth": self.tailwater_depth,
            "expected_hydraulic_control": self.expected_hydraulic_control,
            "recirculation_risk": self.recirculation_risk,
            "aeration_proxy": self.aeration_proxy,
            "turbulence_proxy": self.turbulence_proxy,
            "hazard_tags": list(self.hazard_tags),
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> DropTransitionMetadata2_5D:
        return cls(
            transition_id=str(data["transition_id"]),
            upstream_reach_id=str(data["upstream_reach_id"]),
            downstream_reach_id=str(data["downstream_reach_id"]),
            crest_station=float(data["crest_station"]),
            bed_elevation_fall=float(data["bed_elevation_fall"]),
            geometry_kind=str(data.get("geometry_kind", "ramp")),  # type: ignore[arg-type]
            ramp_length=float(data.get("ramp_length", 0.0)),
            ledge_length=float(data.get("ledge_length", 0.0)),
            tailwater_depth=float(data.get("tailwater_depth", 0.0)),
            expected_hydraulic_control=str(data.get("expected_hydraulic_control", "unknown")),  # type: ignore[arg-type]
            recirculation_risk=float(data.get("recirculation_risk", 0.0)),
            aeration_proxy=float(data.get("aeration_proxy", 0.0)),
            turbulence_proxy=float(data.get("turbulence_proxy", 0.0)),
            hazard_tags=tuple(str(value) for value in data.get("hazard_tags", [])),  # type: ignore[union-attr]
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )


@dataclass(frozen=True, slots=True)
class PoolEddyControl2_5D:
    zone_id: str
    center_station: float
    lateral_offset: float
    radius: float
    circulation_strength: float = 0.0
    recirculation_risk: float = 0.0

    def __post_init__(self) -> None:
        if not self.zone_id:
            raise ValueError("pool eddy zone_id is required.")
        if self.center_station < 0.0:
            raise ValueError("pool eddy center station must be non-negative.")
        if self.radius <= 0.0:
            raise ValueError("pool eddy radius must be positive.")
        for name, value in (
            ("circulation strength", self.circulation_strength),
            ("recirculation risk", self.recirculation_risk),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"pool eddy {name} must be between 0 and 1.")

    def to_json_dict(self) -> dict[str, float | str]:
        return {
            "zone_id": self.zone_id,
            "center_station": self.center_station,
            "lateral_offset": self.lateral_offset,
            "radius": self.radius,
            "circulation_strength": self.circulation_strength,
            "recirculation_risk": self.recirculation_risk,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> PoolEddyControl2_5D:
        return cls(
            zone_id=str(data["zone_id"]),
            center_station=float(data["center_station"]),
            lateral_offset=float(data.get("lateral_offset", 0.0)),
            radius=float(data["radius"]),
            circulation_strength=float(data.get("circulation_strength", 0.0)),
            recirculation_risk=float(data.get("recirculation_risk", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class PoolControlMetadata2_5D:
    pool_id: str
    reach_id: str
    depth_profile: tuple[StationProfilePoint2_5D, ...]
    tailwater_depth: float
    storage_coefficient: float = 0.0
    residence_time_seconds: float = 0.0
    outflow_control: PoolOutflowControlKind2_5D = "unknown"
    eddy_controls: tuple[PoolEddyControl2_5D, ...] = ()
    recirculation_zones: tuple[PoolEddyControl2_5D, ...] = ()
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.pool_id or not self.reach_id:
            raise ValueError("pool_id and reach_id are required.")
        object.__setattr__(self, "depth_profile", tuple(self.depth_profile))
        object.__setattr__(self, "eddy_controls", tuple(self.eddy_controls))
        object.__setattr__(self, "recirculation_zones", tuple(self.recirculation_zones))
        if not self.depth_profile:
            raise ValueError("pool depth profile cannot be empty.")
        stations = [point.station for point in self.depth_profile]
        if stations != sorted(stations):
            raise ValueError("pool depth profile stations must be sorted.")
        if any(point.value <= 0.0 for point in self.depth_profile):
            raise ValueError("pool depth profile values must be positive.")
        if self.tailwater_depth <= 0.0:
            raise ValueError("pool tailwater depth must be positive.")
        if self.storage_coefficient < 0.0:
            raise ValueError("pool storage coefficient must be non-negative.")
        if self.residence_time_seconds < 0.0:
            raise ValueError("pool residence time must be non-negative.")

    @property
    def mean_depth(self) -> float:
        return sum(point.value for point in self.depth_profile) / len(self.depth_profile)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "reach_id": self.reach_id,
            "depth_profile": [point.to_json_dict() for point in self.depth_profile],
            "mean_depth": self.mean_depth,
            "tailwater_depth": self.tailwater_depth,
            "storage_coefficient": self.storage_coefficient,
            "residence_time_seconds": self.residence_time_seconds,
            "outflow_control": self.outflow_control,
            "eddy_controls": [eddy.to_json_dict() for eddy in self.eddy_controls],
            "recirculation_zones": [zone.to_json_dict() for zone in self.recirculation_zones],
            "metadata": self.metadata,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> PoolControlMetadata2_5D:
        return cls(
            pool_id=str(data["pool_id"]),
            reach_id=str(data["reach_id"]),
            depth_profile=tuple(
                StationProfilePoint2_5D.from_json_dict(point)
                for point in data.get("depth_profile", [])  # type: ignore[union-attr]
            ),
            tailwater_depth=float(data["tailwater_depth"]),
            storage_coefficient=float(data.get("storage_coefficient", 0.0)),
            residence_time_seconds=float(data.get("residence_time_seconds", 0.0)),
            outflow_control=str(data.get("outflow_control", "unknown")),  # type: ignore[arg-type]
            eddy_controls=tuple(
                PoolEddyControl2_5D.from_json_dict(eddy)
                for eddy in data.get("eddy_controls", [])  # type: ignore[union-attr]
            ),
            recirculation_zones=tuple(
                PoolEddyControl2_5D.from_json_dict(zone)
                for zone in data.get("recirculation_zones", [])  # type: ignore[union-attr]
            ),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )


@dataclass(frozen=True, slots=True)
class ReachLocalGrid2_5D:
    reach_id: str
    grid: GridSpec2_5D
    upstream_ghost_cells: int = 0
    downstream_ghost_cells: int = 0

    def __post_init__(self) -> None:
        if not self.reach_id:
            raise ValueError("reach local grid reach_id is required.")
        if self.upstream_ghost_cells < 0 or self.downstream_ghost_cells < 0:
            raise ValueError("reach local grid ghost cells must be non-negative.")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "reach_id": self.reach_id,
            "grid": self.grid.to_json_dict(),
            "upstream_ghost_cells": self.upstream_ghost_cells,
            "downstream_ghost_cells": self.downstream_ghost_cells,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> ReachLocalGrid2_5D:
        return cls(
            reach_id=str(data["reach_id"]),
            grid=GridSpec2_5D.from_json_dict(data["grid"]),  # type: ignore[arg-type]
            upstream_ghost_cells=int(data.get("upstream_ghost_cells", 0)),
            downstream_ghost_cells=int(data.get("downstream_ghost_cells", 0)),
        )


@dataclass(frozen=True, slots=True)
class CascadingScenarioPackage2_5D:
    scenario: Scenario2_5D
    reaches: tuple[ReachMetadata2_5D, ...]
    drop_transitions: tuple[DropTransitionMetadata2_5D, ...] = ()
    pool_controls: tuple[PoolControlMetadata2_5D, ...] = ()
    reach_local_grids: tuple[ReachLocalGrid2_5D, ...] = ()
    reach_id_grid: IntGrid | None = None
    drop_transition_id_grid: IntGrid | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reaches", tuple(self.reaches))
        object.__setattr__(self, "drop_transitions", tuple(self.drop_transitions))
        object.__setattr__(self, "pool_controls", tuple(self.pool_controls))
        object.__setattr__(self, "reach_local_grids", tuple(self.reach_local_grids))
        if not self.reaches:
            raise ValueError("cascading package must include at least one reach.")
        reach_ids = [reach.reach_id for reach in self.reaches]
        if len(reach_ids) != len(set(reach_ids)):
            raise ValueError("cascading package reach ids must be unique.")
        reach_id_set = set(reach_ids)
        for drop in self.drop_transitions:
            if drop.upstream_reach_id not in reach_id_set or drop.downstream_reach_id not in reach_id_set:
                raise ValueError("drop transition references an unknown reach.")
        for pool in self.pool_controls:
            if pool.reach_id not in reach_id_set:
                raise ValueError("pool control references an unknown reach.")
        for local_grid in self.reach_local_grids:
            if local_grid.reach_id not in reach_id_set:
                raise ValueError("reach local grid references an unknown reach.")

        default_reach_grid = np.full(self.scenario.grid.shape, -1, dtype=np.int32)
        reach_grid = np.asarray(self.reach_id_grid if self.reach_id_grid is not None else default_reach_grid, dtype=np.int32)
        drop_grid = np.asarray(
            self.drop_transition_id_grid if self.drop_transition_id_grid is not None else default_reach_grid,
            dtype=np.int32,
        )
        if reach_grid.shape != self.scenario.grid.shape:
            raise ValueError("reach_id_grid shape must match scenario grid.")
        if drop_grid.shape != self.scenario.grid.shape:
            raise ValueError("drop_transition_id_grid shape must match scenario grid.")
        if reach_grid.size and int(reach_grid.max()) >= len(self.reaches):
            raise ValueError("reach_id_grid contains an unknown reach index.")
        if drop_grid.size and int(drop_grid.max()) >= len(self.drop_transitions):
            raise ValueError("drop_transition_id_grid contains an unknown drop-transition index.")
        object.__setattr__(self, "reach_id_grid", reach_grid.copy())
        object.__setattr__(self, "drop_transition_id_grid", drop_grid.copy())

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": CASCADING_SCHEMA_VERSION,
            "scenario_id": self.scenario.metadata.scenario_id,
            "base_scenario": "scenario.json",
            "annotation_files": {"reach_drop_indices": CASCADING_ANNOTATIONS_FILE},
            "reach_index": {str(index): reach.reach_id for index, reach in enumerate(self.reaches)},
            "drop_transition_index": {
                str(index): transition.transition_id for index, transition in enumerate(self.drop_transitions)
            },
            "reaches": [reach.to_json_dict() for reach in self.reaches],
            "drop_transitions": [transition.to_json_dict() for transition in self.drop_transitions],
            "pool_controls": [pool.to_json_dict() for pool in self.pool_controls],
            "reach_local_grids": [grid.to_json_dict() for grid in self.reach_local_grids],
            "stitching": {
                "mode": "stitched_global_grid",
                "reach_id_grid": "reach_id_grid",
                "drop_transition_id_grid": "drop_transition_id_grid",
            },
        }

    def write_package(self, directory: str | Path) -> Path:
        output_dir = self.scenario.write_package(directory)
        np.savez_compressed(
            output_dir / CASCADING_ANNOTATIONS_FILE,
            reach_id_grid=self.reach_id_grid,
            drop_transition_id_grid=self.drop_transition_id_grid,
        )
        _write_json(output_dir / CASCADING_METADATA_FILE, self.to_json_dict())
        return output_dir


def read_cascading_scenario_package(path: str | Path) -> CascadingScenarioPackage2_5D:
    root = Path(path)
    package_dir = root.parent if root.name == "scenario.json" else root
    scenario = read_scenario2_5d_package(package_dir)
    metadata = json.loads((package_dir / CASCADING_METADATA_FILE).read_text(encoding="utf-8"))
    if metadata.get("schema_version") != CASCADING_SCHEMA_VERSION:
        raise ValueError(f"Unsupported cascading schema version: {metadata.get('schema_version')!r}")
    with np.load(package_dir / CASCADING_ANNOTATIONS_FILE) as annotations:
        reach_id_grid = np.asarray(annotations["reach_id_grid"], dtype=np.int32)
        drop_transition_id_grid = np.asarray(annotations["drop_transition_id_grid"], dtype=np.int32)
    return CascadingScenarioPackage2_5D(
        scenario=scenario,
        reaches=tuple(ReachMetadata2_5D.from_json_dict(item) for item in metadata.get("reaches", [])),
        drop_transitions=tuple(
            DropTransitionMetadata2_5D.from_json_dict(item) for item in metadata.get("drop_transitions", [])
        ),
        pool_controls=tuple(PoolControlMetadata2_5D.from_json_dict(item) for item in metadata.get("pool_controls", [])),
        reach_local_grids=tuple(ReachLocalGrid2_5D.from_json_dict(item) for item in metadata.get("reach_local_grids", [])),
        reach_id_grid=reach_id_grid,
        drop_transition_id_grid=drop_transition_id_grid,
    )


def evaluate_cascading_handoff_conservation(
    package: CascadingScenarioPackage2_5D,
    thresholds: HandoffConservationThresholds2_5D | None = None,
    *,
    gravity: float = 9.80665,
) -> HandoffConservationReport2_5D:
    limits = thresholds or HandoffConservationThresholds2_5D()
    scenario = package.scenario
    checks: list[HandoffConservationCheck2_5D] = []
    for transition in package.drop_transitions:
        crest_col = int(round((transition.crest_station - scenario.grid.origin_x) / scenario.grid.dx))
        downstream_col = max(1, min(scenario.grid.nx - 1, crest_col))
        upstream_col = downstream_col - 1
        upstream = _cross_section_metrics(scenario, upstream_col, gravity)
        downstream = _cross_section_metrics(scenario, downstream_col, gravity)
        mass_delta = _relative_delta(downstream["mass_flux"], upstream["mass_flux"])
        momentum_delta = _relative_delta(downstream["momentum_flux"], upstream["momentum_flux"])
        eta_delta = abs(downstream["mean_eta"] - upstream["mean_eta"])
        energy_delta = downstream["mean_energy"] - upstream["mean_energy"]
        wet_delta = abs(downstream["wet_fraction"] - upstream["wet_fraction"])
        surface_passed = transition.bed_elevation_fall > 1.0e-9 or eta_delta <= limits.max_surface_elevation_delta
        checks.append(
            HandoffConservationCheck2_5D(
                transition_id=transition.transition_id,
                upstream_reach_id=transition.upstream_reach_id,
                downstream_reach_id=transition.downstream_reach_id,
                upstream_column=upstream_col,
                downstream_column=downstream_col,
                mass_flux_delta=mass_delta,
                momentum_flux_delta=momentum_delta,
                surface_elevation_delta=eta_delta,
                energy_delta=energy_delta,
                wet_fraction_delta=wet_delta,
                mass_flux_passed=mass_delta <= limits.max_mass_flux_delta,
                momentum_flux_passed=momentum_delta <= limits.max_momentum_flux_delta,
                surface_elevation_passed=surface_passed,
                energy_passed=energy_delta <= limits.max_energy_gain,
                wet_front_passed=wet_delta <= limits.max_wet_fraction_delta,
            )
        )
    return HandoffConservationReport2_5D(
        scenario_id=package.scenario.metadata.scenario_id,
        thresholds=limits,
        checks=tuple(checks),
    )


def _cross_section_metrics(scenario: Scenario2_5D, col: int, gravity: float) -> dict[str, float]:
    h = scenario.initial_state.depth[:, col]
    u = scenario.initial_state.u[:, col]
    v = scenario.initial_state.v[:, col]
    hu = scenario.initial_state.hu[:, col]
    eta = scenario.initial_state.eta[:, col]
    bed = scenario.bed[:, col]
    wet = scenario.initial_state.wet[:, col]
    wet_count = max(int(np.count_nonzero(wet)), 1)
    wet_values = wet.astype(np.float64)
    speed_squared = u * u + v * v
    mass_flux = float(np.sum(hu) * scenario.grid.dy)
    momentum_flux = float(np.sum((h * u * u + 0.5 * gravity * h * h) * wet_values) * scenario.grid.dy)
    mean_eta = float(np.sum(eta * wet_values) / wet_count)
    mean_energy = float(np.sum((bed + h + speed_squared / (2.0 * gravity)) * wet_values) / wet_count)
    wet_fraction = float(np.mean(wet_values))
    return {
        "mass_flux": mass_flux,
        "momentum_flux": momentum_flux,
        "mean_eta": mean_eta,
        "mean_energy": mean_energy,
        "wet_fraction": wet_fraction,
    }


def _relative_delta(left: float, right: float) -> float:
    return abs(left - right) / max(abs(left), abs(right), 1.0)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
