"""Cascading 2.5D reach metadata for pool-and-drop river packages."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .scenario2_5d import (
    BoundaryCondition2_5D,
    Feature2_5D,
    GridSpec2_5D,
    InitialWaterState2_5D,
    Probe2_5D,
    RaftParameters2_5D,
    Scenario2_5D,
    ScenarioMetadata2_5D,
    read_scenario2_5d_package,
)

MetadataValue = str | int | float | bool | None
IntGrid = NDArray[np.int32]
FloatGrid = NDArray[np.float64]

CASCADING_SCHEMA_VERSION = "raftsim.cascading2_5d.v0"
CASCADING_METADATA_FILE = "cascading_metadata.json"
CASCADING_ANNOTATIONS_FILE = "cascading_annotations.npz"
UNREAL_CASCADING_CORRIDOR_METADATA_VERSION = "raftsim.unreal_cascading_corridor_metadata.v0"
UNREAL_CASCADING_CORRIDOR_METADATA_FILE = "unreal_cascading_corridor_metadata.json"
UNREAL_CASCADING_CORRIDOR_GRID_FILE = "unreal_cascading_reach_drop_grid.json"
UNREAL_FIDELITY_REVIEW_OVERLAY_SCHEMA_VERSION = "raftsim.unreal_fidelity_review_overlays.v0"
STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION = "raftsim.stitched_whole_window_validation.v0"
STITCHED_WHOLE_WINDOW_VALIDATION_DIR = "stitched_validation"
STITCHED_WHOLE_WINDOW_VALIDATION_MANIFEST_FILE = "manifest.json"
STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE = "fields.npz"
STITCHED_WHOLE_WINDOW_VALIDATION_PROBES_FILE = "probes.json"
STITCHED_WHOLE_WINDOW_VALIDATION_CROSS_SECTIONS_FILE = "cross_sections.json"
STITCHED_WHOLE_WINDOW_VALIDATION_CONSERVATION_FILE = "conservation_summary.json"
STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE = "raft_transition_checkpoints.json"
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
class _CaliforniaPoolDropReachSpec:
    reach_id: str
    kind: ReachKind2_5D
    station_start: float
    station_end: float
    width_start: float
    width_end: float
    depth_start: float
    depth_end: float
    slope_start: float
    slope_end: float
    bed_roughness: float
    boulder_density: float
    bank_shape: BankShapeKind2_5D
    vegetation_flags: tuple[str, ...] = ()
    debris_flags: tuple[str, ...] = ()

    @property
    def station_midpoint(self) -> float:
        return (self.station_start + self.station_end) * 0.5

    @property
    def length(self) -> float:
        return self.station_end - self.station_start


@dataclass(frozen=True, slots=True)
class CaliforniaPoolDropParameters2_5D:
    seed: int = 1
    nx: int = 112
    ny: int = 40
    dx: float = 1.0
    dy: float = 1.0
    base_width: float = 18.0
    base_depth: float = 1.35
    inflow_speed: float = 1.55
    difficulty: float = 0.55
    fixed_dt: float = 1.0 / 60.0
    duration: float = 10.0

    def __post_init__(self) -> None:
        if self.nx < 56:
            raise ValueError("nx must be at least 56 for a pool-drop cascade.")
        if self.ny < 20:
            raise ValueError("ny must be at least 20 for a pool-drop cascade.")
        if self.dx <= 0.0 or self.dy <= 0.0:
            raise ValueError("dx and dy must be positive.")
        if self.base_width <= 0.0 or self.base_depth <= 0.0:
            raise ValueError("base width and depth must be positive.")
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError("difficulty must be between 0 and 1.")


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
class StitchedValidationFieldSummary2_5D:
    field_name: str
    npz_key: str
    units: str
    shape: tuple[int, int]
    dtype: str
    min_value: float | None
    max_value: float | None
    mean_value: float | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "npz_key": self.npz_key,
            "units": self.units,
            "shape": list(self.shape),
            "dtype": self.dtype,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": self.mean_value,
        }


@dataclass(frozen=True, slots=True)
class StitchedValidationProbeSample2_5D:
    probe_id: str
    kind: str
    position: tuple[float, float]
    grid_index: tuple[int, int]
    reach_id: str | None
    drop_transition_id: str | None
    bed_elevation_m: float
    depth_m: float
    surface_elevation_m: float
    velocity_m_s: tuple[float, float]
    speed_m_s: float
    froude_number: float
    wet: bool
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "kind": self.kind,
            "position": {"x": self.position[0], "y": self.position[1]},
            "grid_index": {"row": self.grid_index[0], "column": self.grid_index[1]},
            "reach_id": self.reach_id,
            "drop_transition_id": self.drop_transition_id,
            "bed_elevation_m": self.bed_elevation_m,
            "depth_m": self.depth_m,
            "surface_elevation_m": self.surface_elevation_m,
            "velocity_m_s": {"u": self.velocity_m_s[0], "v": self.velocity_m_s[1]},
            "speed_m_s": self.speed_m_s,
            "froude_number": self.froude_number,
            "wet": self.wet,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class StitchedValidationCrossSection2_5D:
    section_id: str
    station_m: float
    center: tuple[float, float]
    sample_direction: tuple[float, float]
    length_m: float
    column: int
    reach_id: str | None
    drop_transition_id: str | None
    sample_count: int
    wet_sample_count: int
    wetted_width_m: float
    mean_depth_m: float
    max_depth_m: float
    mean_surface_elevation_m: float
    min_bed_elevation_m: float
    max_speed_m_s: float
    mass_flux_proxy_m3_s: float
    momentum_flux_proxy_m4_s2: float
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "station_m": self.station_m,
            "center": {"x": self.center[0], "y": self.center[1]},
            "sample_direction": {"x": self.sample_direction[0], "y": self.sample_direction[1]},
            "length_m": self.length_m,
            "column": self.column,
            "reach_id": self.reach_id,
            "drop_transition_id": self.drop_transition_id,
            "sample_count": self.sample_count,
            "wet_sample_count": self.wet_sample_count,
            "wetted_width_m": self.wetted_width_m,
            "mean_depth_m": self.mean_depth_m,
            "max_depth_m": self.max_depth_m,
            "mean_surface_elevation_m": self.mean_surface_elevation_m,
            "min_bed_elevation_m": self.min_bed_elevation_m,
            "max_speed_m_s": self.max_speed_m_s,
            "mass_flux_proxy_m3_s": self.mass_flux_proxy_m3_s,
            "momentum_flux_proxy_m4_s2": self.momentum_flux_proxy_m4_s2,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class StitchedValidationConservationSummary2_5D:
    scenario_id: str
    wet_cell_count: int
    total_cell_count: int
    wet_fraction: float
    total_water_volume_m3: float
    mass_proxy_kg: float
    x_momentum_proxy_kg_m_s: float
    y_momentum_proxy_kg_m_s: float
    min_depth_m: float
    max_depth_m: float
    min_surface_elevation_m: float
    max_surface_elevation_m: float
    min_bed_elevation_m: float
    max_bed_elevation_m: float
    max_speed_m_s: float
    handoff_report: HandoffConservationReport2_5D

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "wet_cell_count": self.wet_cell_count,
            "total_cell_count": self.total_cell_count,
            "wet_fraction": self.wet_fraction,
            "total_water_volume_m3": self.total_water_volume_m3,
            "mass_proxy_kg": self.mass_proxy_kg,
            "x_momentum_proxy_kg_m_s": self.x_momentum_proxy_kg_m_s,
            "y_momentum_proxy_kg_m_s": self.y_momentum_proxy_kg_m_s,
            "min_depth_m": self.min_depth_m,
            "max_depth_m": self.max_depth_m,
            "min_surface_elevation_m": self.min_surface_elevation_m,
            "max_surface_elevation_m": self.max_surface_elevation_m,
            "min_bed_elevation_m": self.min_bed_elevation_m,
            "max_bed_elevation_m": self.max_bed_elevation_m,
            "max_speed_m_s": self.max_speed_m_s,
            "handoff_report": self.handoff_report.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class StitchedValidationRaftTransitionCheckpoint2_5D:
    checkpoint_id: str
    transition_id: str
    drop_transition_id: str | None
    phase: str
    upstream_reach_id: str
    downstream_reach_id: str
    station_m: float
    position: tuple[float, float]
    grid_index: tuple[int, int]
    sampled_reach_id: str | None
    sampled_drop_transition_id: str | None
    expected_hydraulic_control: str
    hazard_tags: tuple[str, ...]
    bed_elevation_fall_m: float
    depth_m: float
    surface_elevation_m: float
    velocity_m_s: tuple[float, float]
    speed_m_s: float
    froude_number: float
    wet: bool
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "transition_id": self.transition_id,
            "drop_transition_id": self.drop_transition_id,
            "phase": self.phase,
            "upstream_reach_id": self.upstream_reach_id,
            "downstream_reach_id": self.downstream_reach_id,
            "station_m": self.station_m,
            "position": {"x": self.position[0], "y": self.position[1]},
            "grid_index": {"row": self.grid_index[0], "column": self.grid_index[1]},
            "sampled_reach_id": self.sampled_reach_id,
            "sampled_drop_transition_id": self.sampled_drop_transition_id,
            "expected_hydraulic_control": self.expected_hydraulic_control,
            "hazard_tags": list(self.hazard_tags),
            "bed_elevation_fall_m": self.bed_elevation_fall_m,
            "depth_m": self.depth_m,
            "surface_elevation_m": self.surface_elevation_m,
            "velocity_m_s": {"u": self.velocity_m_s[0], "v": self.velocity_m_s[1]},
            "speed_m_s": self.speed_m_s,
            "froude_number": self.froude_number,
            "wet": self.wet,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class StitchedWholeWindowValidationExport2_5D:
    scenario_id: str
    river_id: str | None
    section_id: str | None
    grid: GridSpec2_5D
    fields_file: str
    field_summaries: tuple[StitchedValidationFieldSummary2_5D, ...]
    probes_file: str
    probes: tuple[StitchedValidationProbeSample2_5D, ...]
    cross_sections_file: str
    cross_sections: tuple[StitchedValidationCrossSection2_5D, ...]
    conservation_file: str
    conservation_summary: StitchedValidationConservationSummary2_5D
    raft_transition_checkpoints_file: str
    raft_transition_checkpoints: tuple[StitchedValidationRaftTransitionCheckpoint2_5D, ...]
    reach_index: dict[str, str]
    drop_transition_index: dict[str, str]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "river_id": self.river_id,
            "section_id": self.section_id,
            "grid": self.grid.to_json_dict(),
            "files": {
                "fields": self.fields_file,
                "probes": self.probes_file,
                "cross_sections": self.cross_sections_file,
                "conservation_summary": self.conservation_file,
                "raft_transition_checkpoints": self.raft_transition_checkpoints_file,
            },
            "field_summaries": [summary.to_json_dict() for summary in self.field_summaries],
            "counts": {
                "fields": len(self.field_summaries),
                "probes": len(self.probes),
                "cross_sections": len(self.cross_sections),
                "raft_transition_checkpoints": len(self.raft_transition_checkpoints),
            },
            "reach_index": self.reach_index,
            "drop_transition_index": self.drop_transition_index,
            "validation_scope": {
                "storage": "stitched_whole_window",
                "covers_reach_local_grids": True,
                "seams_visible_to_validators": True,
                "consumer_contract": "GeoClaw/C++/Unreal must compare this stitched export, not isolated reach chunks.",
            },
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
            "validation_outputs": {
                "stitched_whole_window": {
                    "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
                    "directory": STITCHED_WHOLE_WINDOW_VALIDATION_DIR,
                    "manifest": f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/{STITCHED_WHOLE_WINDOW_VALIDATION_MANIFEST_FILE}",
                    "fields": f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/{STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE}",
                    "probes": f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/{STITCHED_WHOLE_WINDOW_VALIDATION_PROBES_FILE}",
                    "cross_sections": (
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_CROSS_SECTIONS_FILE}"
                    ),
                    "conservation_summary": (
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_CONSERVATION_FILE}"
                    ),
                    "raft_transition_checkpoints": (
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                        f"{STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE}"
                    ),
                }
            },
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
        write_stitched_whole_window_validation_export(self, output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_DIR)
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


def build_stitched_whole_window_validation_export(
    package: CascadingScenarioPackage2_5D,
) -> StitchedWholeWindowValidationExport2_5D:
    """Build stitched, seam-visible validation diagnostics for a cascading package."""

    field_arrays = _stitched_validation_field_arrays(package)
    return StitchedWholeWindowValidationExport2_5D(
        scenario_id=package.scenario.metadata.scenario_id,
        river_id=package.scenario.metadata.river_id,
        section_id=package.scenario.metadata.section_id,
        grid=package.scenario.grid,
        fields_file=STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE,
        field_summaries=tuple(_stitched_validation_field_summary(name, array) for name, array in field_arrays.items()),
        probes_file=STITCHED_WHOLE_WINDOW_VALIDATION_PROBES_FILE,
        probes=_stitched_validation_probe_samples(package),
        cross_sections_file=STITCHED_WHOLE_WINDOW_VALIDATION_CROSS_SECTIONS_FILE,
        cross_sections=_stitched_validation_cross_sections(package),
        conservation_file=STITCHED_WHOLE_WINDOW_VALIDATION_CONSERVATION_FILE,
        conservation_summary=_stitched_validation_conservation_summary(package),
        raft_transition_checkpoints_file=STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE,
        raft_transition_checkpoints=_stitched_validation_raft_transition_checkpoints(package),
        reach_index={str(index): reach.reach_id for index, reach in enumerate(package.reaches)},
        drop_transition_index={
            str(index): transition.transition_id for index, transition in enumerate(package.drop_transitions)
        },
    )


def write_stitched_whole_window_validation_export(
    package: CascadingScenarioPackage2_5D,
    directory: str | Path,
) -> Path:
    """Write stitched validation fields and diagnostic sidecars for a cascading package."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    export = build_stitched_whole_window_validation_export(package)
    np.savez_compressed(output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE, **_stitched_validation_field_arrays(package))
    _write_json(
        output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_PROBES_FILE,
        {
            "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
            "scenario_id": export.scenario_id,
            "probes": [probe.to_json_dict() for probe in export.probes],
        },
    )
    _write_json(
        output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_CROSS_SECTIONS_FILE,
        {
            "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
            "scenario_id": export.scenario_id,
            "cross_sections": [section.to_json_dict() for section in export.cross_sections],
        },
    )
    _write_json(
        output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_CONSERVATION_FILE,
        {
            "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
            "scenario_id": export.scenario_id,
            "conservation_summary": export.conservation_summary.to_json_dict(),
        },
    )
    _write_json(
        output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE,
        {
            "schema_version": STITCHED_WHOLE_WINDOW_VALIDATION_SCHEMA_VERSION,
            "scenario_id": export.scenario_id,
            "raft_transition_checkpoints": [
                checkpoint.to_json_dict() for checkpoint in export.raft_transition_checkpoints
            ],
        },
    )
    manifest_path = output_dir / STITCHED_WHOLE_WINDOW_VALIDATION_MANIFEST_FILE
    _write_json(manifest_path, export.to_json_dict())
    return manifest_path


def build_unreal_cascading_corridor_metadata(package: CascadingScenarioPackage2_5D) -> dict[str, object]:
    """Build Unreal-facing reach/drop metadata for streaming, overlays, audio, VFX, and review."""

    scenario = package.scenario
    reach_index = {str(index): reach.reach_id for index, reach in enumerate(package.reaches)}
    drop_transition_index = {
        str(index): transition.transition_id for index, transition in enumerate(package.drop_transitions)
    }
    streaming_tiles = [
        _unreal_reach_streaming_tile(package, index, reach)
        for index, reach in enumerate(package.reaches)
    ]
    drop_transitions = [
        _unreal_drop_transition_zone(package, index, transition)
        for index, transition in enumerate(package.drop_transitions)
    ]
    return {
        "schema_version": UNREAL_CASCADING_CORRIDOR_METADATA_VERSION,
        "scenario_id": scenario.metadata.scenario_id,
        "river_id": scenario.metadata.river_id,
        "section_id": scenario.metadata.section_id,
        "flow_band": scenario.metadata.flow_band,
        "difficulty_preset": scenario.metadata.difficulty_preset,
        "coordinate_system": {
            "solver_units": "meters",
            "unreal_units": "centimeters",
            "unreal_unit_scale_cm_per_meter": 100.0,
            "station_axis": "x",
            "lateral_axis": "y",
            "vertical_axis": "z",
            "origin_m": {
                "x": scenario.grid.origin_x,
                "y": scenario.grid.origin_y,
                "z": 0.0,
            },
        },
        "grid": {
            "nx": scenario.grid.nx,
            "ny": scenario.grid.ny,
            "dx": scenario.grid.dx,
            "dy": scenario.grid.dy,
            "origin_x": scenario.grid.origin_x,
            "origin_y": scenario.grid.origin_y,
        },
        "files": {
            "metadata": UNREAL_CASCADING_CORRIDOR_METADATA_FILE,
            "reach_drop_id_grid": UNREAL_CASCADING_CORRIDOR_GRID_FILE,
            "source_cascading_metadata": CASCADING_METADATA_FILE,
            "source_cascading_annotations": CASCADING_ANNOTATIONS_FILE,
        },
        "id_preservation": {
            "reach_index": reach_index,
            "drop_transition_index": drop_transition_index,
            "reach_ids": [reach.reach_id for reach in package.reaches],
            "drop_transition_ids": [transition.transition_id for transition in package.drop_transitions],
        },
        "streaming_tiles": streaming_tiles,
        "drop_transition_zones": drop_transitions,
        "debug_overlays": _unreal_debug_overlays(package, reach_index, drop_transition_index),
        "audio_zones": _unreal_audio_zones(streaming_tiles, drop_transitions),
        "vfx_zones": _unreal_vfx_zones(streaming_tiles, drop_transitions),
        "fidelity_review_overlays": _unreal_fidelity_review_overlays(
            package,
            streaming_tiles,
            drop_transitions,
        ),
        "designer_review": {
            "scenario_description": scenario.metadata.description,
            "reach_review_count": len(streaming_tiles),
            "drop_transition_review_count": len(drop_transitions),
            "confidence_score": scenario.metadata.confidence_score,
            "review_flags": sorted(
                {
                    flag
                    for reach in package.reaches
                    for flag in (*reach.vegetation_flags, *reach.debris_flags)
                }
                | {tag for transition in package.drop_transitions for tag in transition.hazard_tags}
            ),
        },
    }


def write_unreal_cascading_corridor_metadata(
    package: CascadingScenarioPackage2_5D,
    directory: str | Path,
) -> Path:
    """Write Unreal-facing cascading corridor metadata and ID grids."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / UNREAL_CASCADING_CORRIDOR_GRID_FILE, _unreal_reach_drop_grid(package))
    metadata_path = output_dir / UNREAL_CASCADING_CORRIDOR_METADATA_FILE
    _write_json(metadata_path, build_unreal_cascading_corridor_metadata(package))
    return metadata_path


def generate_california_pool_drop_cascading_scenario2_5d(
    parameters: CaliforniaPoolDropParameters2_5D | None = None,
) -> CascadingScenarioPackage2_5D:
    """Generate a deterministic California-style pool-and-drop cascading package."""

    params = parameters or CaliforniaPoolDropParameters2_5D()
    rng = random.Random(params.seed)
    origin_y = -0.5 * (params.ny - 1) * params.dy
    grid = GridSpec2_5D(nx=params.nx, ny=params.ny, dx=params.dx, dy=params.dy, origin_x=0.0, origin_y=origin_y)
    xs = grid.x_coordinates()
    x, y = grid.meshgrid()
    total_station = float(xs[-1] - xs[0])
    specs = _california_pool_drop_reach_specs(params, rng, total_station)
    reach_grid = _california_reach_id_grid(grid, xs, specs)

    channel_width = _interpolate_spec_profile(xs, specs, "width_start", "width_end")
    center_depth = _interpolate_spec_profile(xs, specs, "depth_start", "depth_end")
    bed_slope = _interpolate_spec_profile(xs, specs, "slope_start", "slope_end")
    centerline = _california_centerline(params, rng, xs, channel_width)

    drop_spec = _spec_by_id(specs, "drop_001")
    wave_spec = _spec_by_id(specs, "wave_train_001")
    main_drop_fall = 0.42 + 0.72 * params.difficulty + rng.uniform(-0.035, 0.035)
    drop_control_length = max(params.dx * 3.0, drop_spec.length * 0.58)
    drop_transition = DropTransitionMetadata2_5D(
        transition_id="ledge_drop_001",
        upstream_reach_id="tongue_001",
        downstream_reach_id="drop_001",
        crest_station=drop_spec.station_start,
        bed_elevation_fall=main_drop_fall,
        geometry_kind="mixed",
        ramp_length=max(params.dx * 2.0, drop_control_length * 0.7),
        ledge_length=max(params.dx, drop_control_length * 0.3),
        tailwater_depth=wave_spec.depth_start,
        expected_hydraulic_control="retentive_hole" if params.difficulty >= 0.58 else "wave_train",
        recirculation_risk=min(1.0, 0.28 + 0.58 * params.difficulty),
        aeration_proxy=min(1.0, 0.36 + 0.52 * params.difficulty),
        turbulence_proxy=min(1.0, 0.42 + 0.50 * params.difficulty),
        hazard_tags=("ledge", "hole", "wave_train"),
        metadata={"generator": "california_pool_drop", "pattern_role": "main_drop"},
    )
    drop_grid = _california_drop_transition_id_grid(grid, xs, (drop_transition,))

    bed_grade_drop = np.cumsum(np.concatenate(([0.0], bed_slope[:-1]))) * params.dx
    explicit_drop = main_drop_fall * _smoothstep((xs - drop_spec.station_start) / drop_control_length)
    bed_centerline = -(bed_grade_drop + explicit_drop)
    center_depth = _add_wave_train_depth_signal(center_depth, xs, wave_spec, params)
    center_depth = np.maximum(center_depth, params.base_depth * 0.35)

    features = _california_pool_drop_features(params, rng, grid, xs, centerline, channel_width, specs, main_drop_fall)
    lateral = y - centerline[np.newaxis, :]
    half_width = np.maximum(channel_width[np.newaxis, :] * 0.5, params.dy)
    lateral_fraction = np.abs(lateral) / half_width
    wet_channel = lateral_fraction <= 1.0
    depth = np.where(
        wet_channel,
        center_depth[np.newaxis, :] * np.maximum(0.24, 1.0 - 0.44 * lateral_fraction**2),
        0.0,
    )
    depth = _apply_california_feature_depth_modifiers(depth, x, y, features, params)
    depth = np.where(wet_channel, np.maximum(depth, 0.0), 0.0)

    eta_centerline = bed_centerline + center_depth
    bank_lift = params.base_depth + 0.72 + 0.18 * np.maximum(lateral_fraction - 1.0, 0.0)
    bed = np.where(depth > 1.0e-6, eta_centerline[np.newaxis, :] - depth, eta_centerline[np.newaxis, :] + bank_lift)

    u, v = _california_initial_velocity(params, grid, depth, lateral_fraction, wet_channel, centerline)
    u, v = _apply_california_feature_velocity_modifiers(u, v, x, y, features, params, centerline, xs)
    u = np.where(depth > 1.0e-6, u, 0.0)
    v = np.where(depth > 1.0e-6, v, 0.0)

    state = InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v)
    boundaries = (
        BoundaryCondition2_5D(
            "west",
            "inflow",
            depth=float(depth[:, 0][depth[:, 0] > 1.0e-6].mean()),
            velocity=(float(u[:, 0][depth[:, 0] > 1.0e-6].mean()), float(v[:, 0][depth[:, 0] > 1.0e-6].mean())),
            metadata={"source": "california_pool_drop_generator"},
        ),
        BoundaryCondition2_5D("east", "outflow"),
        BoundaryCondition2_5D("south", "wall"),
        BoundaryCondition2_5D("north", "wall"),
    )
    reaches = tuple(_metadata_from_california_spec(spec, grid) for spec in specs)
    scenario = Scenario2_5D(
        metadata=ScenarioMetadata2_5D(
            scenario_id=f"california_pool_drop_seed_{params.seed}",
            scenario_type="procedural",
            seed=params.seed,
            generator="raftsim.cascading",
            generator_version="milestone_15_pool_drop.v0",
            description=(
                "Seeded California-style pool-drop sequence with pool, constricted tongue, ledge/drop, "
                "wave train, recovery eddy, boulder garden, and next pool reaches."
            ),
            flow_band="synthetic_pool_drop",
            difficulty_preset=f"california_pool_drop_{params.difficulty:.2f}",
            confidence_score=0.58,
            provenance={
                "source": "deterministic_california_pool_drop_generator",
                "reach_pattern": "pool,tongue,drop,wave_train,eddy_recovery,boulder_garden,pool",
                "drop_count": len((drop_transition,)),
            },
        ),
        grid=grid,
        fixed_dt=params.fixed_dt,
        duration=params.duration,
        bed=bed,
        initial_state=state,
        boundaries=boundaries,
        features=features,
        probes=_california_pool_drop_probes(grid, xs, centerline, specs, drop_transition),
        raft=RaftParameters2_5D(),
        roughness=float(sum(spec.bed_roughness for spec in specs) / len(specs)),
    )
    return CascadingScenarioPackage2_5D(
        scenario=scenario,
        reaches=reaches,
        drop_transitions=(drop_transition,),
        pool_controls=_california_pool_controls(params, specs, channel_width),
        reach_local_grids=_california_reach_local_grids(params, grid, xs, specs),
        reach_id_grid=reach_grid,
        drop_transition_id_grid=drop_grid,
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


def _california_pool_drop_reach_specs(
    params: CaliforniaPoolDropParameters2_5D,
    rng: random.Random,
    total_station: float,
) -> tuple[_CaliforniaPoolDropReachSpec, ...]:
    base_fractions = np.asarray((0.20, 0.11, 0.08, 0.17, 0.12, 0.17, 0.15), dtype=np.float64)
    jitter = np.asarray([rng.uniform(-0.012, 0.012) for _ in range(len(base_fractions))], dtype=np.float64)
    fractions = np.maximum(base_fractions + jitter, 0.055)
    fractions /= float(np.sum(fractions))
    boundaries = [0.0]
    for fraction in fractions[:-1]:
        boundaries.append(boundaries[-1] + float(fraction) * total_station)
    boundaries.append(total_station)

    d = params.difficulty
    max_width = max(params.dy * 8.0, (params.ny - 3) * params.dy)
    min_width = max(params.dy * 4.0, params.base_width * 0.38)

    def width(value: float) -> float:
        return max(min_width, min(max_width, value * (1.0 + rng.uniform(-0.025, 0.025))))

    specs = (
        _CaliforniaPoolDropReachSpec(
            "pool_001",
            "pool",
            boundaries[0],
            boundaries[1],
            width(params.base_width * 1.22),
            width(params.base_width * 1.12),
            params.base_depth * 1.24,
            params.base_depth * 1.08,
            0.0018 + 0.0005 * d,
            0.0024 + 0.0006 * d,
            0.036,
            0.08 + 0.06 * d,
            "vegetated",
            vegetation_flags=("riparian_willow", "pool_margin_grass"),
        ),
        _CaliforniaPoolDropReachSpec(
            "tongue_001",
            "tongue",
            boundaries[1],
            boundaries[2],
            width(params.base_width * 0.96),
            width(params.base_width * (0.62 - 0.06 * d)),
            params.base_depth * 0.98,
            params.base_depth * 0.82,
            0.010 + 0.006 * d,
            0.017 + 0.008 * d,
            0.040,
            0.16 + 0.08 * d,
            "bedrock",
        ),
        _CaliforniaPoolDropReachSpec(
            "drop_001",
            "drop",
            boundaries[2],
            boundaries[3],
            width(params.base_width * (0.62 - 0.04 * d)),
            width(params.base_width * 0.72),
            params.base_depth * 0.80,
            params.base_depth * 0.95,
            0.042 + 0.020 * d,
            0.052 + 0.024 * d,
            0.047 + 0.010 * d,
            0.22 + 0.12 * d,
            "bedrock",
            debris_flags=("aerated_hydraulic",),
        ),
        _CaliforniaPoolDropReachSpec(
            "wave_train_001",
            "wave_train",
            boundaries[3],
            boundaries[4],
            width(params.base_width * 0.78),
            width(params.base_width * 0.92),
            params.base_depth * 0.92,
            params.base_depth * 0.84,
            0.024 + 0.010 * d,
            0.018 + 0.008 * d,
            0.044 + 0.008 * d,
            0.26 + 0.12 * d,
            "bedrock",
        ),
        _CaliforniaPoolDropReachSpec(
            "eddy_recovery_001",
            "eddy_recovery",
            boundaries[4],
            boundaries[5],
            width(params.base_width * 1.04),
            width(params.base_width * 1.14),
            params.base_depth * 1.02,
            params.base_depth * 1.08,
            0.006 + 0.003 * d,
            0.004 + 0.002 * d,
            0.038,
            0.12 + 0.05 * d,
            "alluvial",
            vegetation_flags=("eddy_margin_willow",),
            debris_flags=("eddy_foam",),
        ),
        _CaliforniaPoolDropReachSpec(
            "boulder_garden_001",
            "boulder_garden",
            boundaries[5],
            boundaries[6],
            width(params.base_width * 0.92),
            width(params.base_width * 0.84),
            params.base_depth * 0.91,
            params.base_depth * 0.82,
            0.017 + 0.007 * d,
            0.022 + 0.010 * d,
            0.055 + 0.012 * d,
            0.42 + 0.32 * d,
            "bedrock",
            debris_flags=("boulder_sieves", "technical_moves"),
        ),
        _CaliforniaPoolDropReachSpec(
            "pool_002",
            "pool",
            boundaries[6],
            boundaries[7],
            width(params.base_width * 1.18),
            width(params.base_width * 1.30),
            params.base_depth * 1.16,
            params.base_depth * 1.30,
            0.0028 + 0.0008 * d,
            0.0018 + 0.0004 * d,
            0.037,
            0.10 + 0.04 * d,
            "vegetated",
            vegetation_flags=("recovery_pool_willow",),
        ),
    )
    return specs


def _metadata_from_california_spec(spec: _CaliforniaPoolDropReachSpec, grid: GridSpec2_5D) -> ReachMetadata2_5D:
    mean_width = (spec.width_start + spec.width_end) * 0.5
    return ReachMetadata2_5D(
        reach_id=spec.reach_id,
        kind=spec.kind,
        station_start=spec.station_start,
        station_end=spec.station_end,
        local_grid=ReachGridTransform2_5D(
            origin_x=spec.station_start,
            origin_y=grid.origin_y,
            station_origin=spec.station_start,
            dx=grid.dx,
            dy=grid.dy,
        ),
        slope_profile=(
            StationProfilePoint2_5D(spec.station_start, spec.slope_start),
            StationProfilePoint2_5D(spec.station_end, spec.slope_end),
        ),
        width_profile=(
            StationProfilePoint2_5D(spec.station_start, spec.width_start),
            StationProfilePoint2_5D(spec.station_end, spec.width_end),
        ),
        bank_shape=BankShape2_5D(
            spec.bank_shape,
            left_bank_offset_m=mean_width * 0.5,
            right_bank_offset_m=-mean_width * 0.5,
            left_bank_slope=0.32 if spec.kind == "pool" else 0.48,
            right_bank_slope=0.34 if spec.kind == "pool" else 0.50,
        ),
        bed_roughness=spec.bed_roughness,
        boulder_density=spec.boulder_density,
        vegetation_flags=spec.vegetation_flags,
        debris_flags=spec.debris_flags,
        confidence_score=0.66,
        metadata={"generator": "california_pool_drop", "pattern_role": spec.kind},
    )


def _california_centerline(
    params: CaliforniaPoolDropParameters2_5D,
    rng: random.Random,
    xs: FloatGrid,
    channel_width: FloatGrid,
) -> FloatGrid:
    y_span = max((params.ny - 1) * params.dy, params.dy)
    margin = float(np.max(channel_width)) * 0.5 + params.dy * 2.0
    bend_amplitude = max(0.0, min(2.4 + 1.6 * params.difficulty, y_span * 0.5 - margin))
    if bend_amplitude == 0.0:
        return np.zeros_like(xs, dtype=np.float64)
    t = xs / max(float(xs[-1] - xs[0]), params.dx)
    phase_a = rng.uniform(0.0, math.tau)
    phase_b = rng.uniform(0.0, math.tau)
    centerline = bend_amplitude * np.sin(1.15 * math.tau * t + phase_a)
    centerline += bend_amplitude * 0.28 * np.sin(2.65 * math.tau * t + phase_b)
    return centerline.astype(np.float64)


def _interpolate_spec_profile(
    xs: FloatGrid,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
    start_attr: str,
    end_attr: str,
) -> FloatGrid:
    values = np.zeros_like(xs, dtype=np.float64)
    for index, spec in enumerate(specs):
        mask = _spec_column_mask(xs, spec, is_last=index == len(specs) - 1)
        if not bool(np.any(mask)):
            continue
        local = (xs[mask] - spec.station_start) / max(spec.length, 1.0e-9)
        start = float(getattr(spec, start_attr))
        end = float(getattr(spec, end_attr))
        values[mask] = start + (end - start) * _smoothstep(local)
    return values


def _add_wave_train_depth_signal(
    center_depth: FloatGrid,
    xs: FloatGrid,
    wave_spec: _CaliforniaPoolDropReachSpec,
    params: CaliforniaPoolDropParameters2_5D,
) -> FloatGrid:
    local = (xs - wave_spec.station_start) / max(wave_spec.length, 1.0e-9)
    window = _smoothstep(local) * (1.0 - _smoothstep(local - 0.72))
    wave = np.sin(local * math.tau * 4.0)
    return center_depth + params.base_depth * (0.035 + 0.035 * params.difficulty) * wave * window


def _california_pool_drop_features(
    params: CaliforniaPoolDropParameters2_5D,
    rng: random.Random,
    grid: GridSpec2_5D,
    xs: FloatGrid,
    centerline: FloatGrid,
    channel_width: FloatGrid,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
    main_drop_fall: float,
) -> tuple[Feature2_5D, ...]:
    features: list[Feature2_5D] = []
    tongue = _spec_by_id(specs, "tongue_001")
    drop = _spec_by_id(specs, "drop_001")
    wave_train = _spec_by_id(specs, "wave_train_001")
    eddy = _spec_by_id(specs, "eddy_recovery_001")
    boulders = _spec_by_id(specs, "boulder_garden_001")

    tongue_center = _feature_center(grid, xs, centerline, channel_width, tongue.station_midpoint)
    tongue_width = _width_at_station(xs, channel_width, tongue.station_midpoint)
    features.append(
        Feature2_5D(
            "constriction",
            tongue_center,
            radius=tongue_width * 0.24,
            strength=0.72 + 0.48 * params.difficulty,
            length=tongue.length * 0.78,
            width=tongue_width * 0.62,
            metadata={"reach_id": tongue.reach_id, "pattern_role": "constricted_tongue"},
        )
    )

    ledge_station = drop.station_start
    drop_width = _width_at_station(xs, channel_width, ledge_station)
    features.append(
        Feature2_5D(
            "ledge",
            _feature_center(grid, xs, centerline, channel_width, ledge_station),
            radius=0.0,
            strength=main_drop_fall,
            length=drop_width,
            width=max(params.dx * 2.0, drop.length * 0.4),
            metadata={"reach_id": drop.reach_id, "pattern_role": "ledge_drop"},
        )
    )
    hole_station = min(drop.station_end, drop.station_start + drop.length * 0.72)
    features.append(
        Feature2_5D(
            "hole",
            _feature_center(grid, xs, centerline, channel_width, hole_station),
            radius=drop_width * 0.18,
            strength=0.62 + 0.42 * params.difficulty,
            length=drop.length * 0.52,
            width=drop_width * 0.58,
            metadata={"reach_id": drop.reach_id, "pattern_role": "hydraulic_hole"},
        )
    )

    wave_width = _width_at_station(xs, channel_width, wave_train.station_midpoint)
    features.append(
        Feature2_5D(
            "wave_train",
            _feature_center(grid, xs, centerline, channel_width, wave_train.station_midpoint),
            radius=wave_width * 0.18,
            strength=0.58 + 0.40 * params.difficulty,
            length=wave_train.length * 0.86,
            width=wave_width * 0.72,
            metadata={"reach_id": wave_train.reach_id, "pattern_role": "standing_wave_sequence"},
        )
    )

    eddy_width = _width_at_station(xs, channel_width, eddy.station_midpoint)
    eddy_side = -1.0 if rng.random() < 0.5 else 1.0
    features.append(
        Feature2_5D(
            "eddy_line",
            _feature_center(grid, xs, centerline, channel_width, eddy.station_midpoint, eddy_side * eddy_width * 0.28),
            radius=eddy_width * 0.16,
            strength=0.46 + 0.32 * params.difficulty,
            length=eddy.length * 0.72,
            width=eddy_width * 0.38,
            metadata={"reach_id": eddy.reach_id, "pattern_role": "recovery_eddy_line", "side": eddy_side},
        )
    )
    features.append(
        Feature2_5D(
            "boil",
            _feature_center(grid, xs, centerline, channel_width, eddy.station_start + eddy.length * 0.70, -eddy_side * eddy_width * 0.14),
            radius=eddy_width * 0.12,
            strength=0.34 + 0.24 * params.difficulty,
            metadata={"reach_id": eddy.reach_id, "pattern_role": "tailwater_boil"},
        )
    )

    rock_count = 4 + int(round(4.0 * params.difficulty))
    for index in range(rock_count):
        station = boulders.station_start + boulders.length * ((index + 1) / (rock_count + 1))
        station += rng.uniform(-0.035, 0.035) * boulders.length
        station = max(boulders.station_start, min(boulders.station_end, station))
        width = _width_at_station(xs, channel_width, station)
        lateral = rng.uniform(-0.32, 0.32) * width
        radius = max(params.dx * 0.75, width * rng.uniform(0.045, 0.085))
        features.append(
            Feature2_5D(
                "rock",
                _feature_center(grid, xs, centerline, channel_width, station, lateral),
                radius=radius,
                strength=0.70 + 0.30 * params.difficulty,
                length=radius * rng.uniform(1.4, 2.3),
                width=radius * rng.uniform(1.2, 1.9),
                metadata={"reach_id": boulders.reach_id, "pattern_role": "boulder_garden", "source_index": index},
            )
        )

    return tuple(features)


def _apply_california_feature_depth_modifiers(
    depth: FloatGrid,
    x: FloatGrid,
    y: FloatGrid,
    features: tuple[Feature2_5D, ...],
    params: CaliforniaPoolDropParameters2_5D,
) -> FloatGrid:
    adjusted = depth.copy()
    for feature in features:
        influence = _feature_influence(x, y, feature, params.dx, params.dy)
        if feature.kind == "hole":
            adjusted += params.base_depth * 0.16 * feature.strength * influence
        elif feature.kind == "wave_train":
            wave = np.sin((x - feature.center[0]) * 2.25)
            adjusted += params.base_depth * 0.045 * feature.strength * wave * influence
        elif feature.kind == "rock":
            adjusted *= np.maximum(0.16, 1.0 - 0.58 * min(feature.strength, 1.3) * influence)
        elif feature.kind == "shallow":
            adjusted *= np.maximum(0.35, 1.0 - 0.42 * feature.strength * influence)
    return np.maximum(adjusted, 0.0)


def _california_initial_velocity(
    params: CaliforniaPoolDropParameters2_5D,
    grid: GridSpec2_5D,
    depth: FloatGrid,
    lateral_fraction: FloatGrid,
    wet_channel: NDArray[np.bool_],
    centerline: FloatGrid,
) -> tuple[FloatGrid, FloatGrid]:
    bank_profile = np.where(wet_channel, np.maximum(0.22, 1.0 - 0.44 * lateral_fraction**1.8), 0.0)
    weighted_depth = np.sum(depth * bank_profile, axis=0) * grid.dy
    discharge = params.base_width * params.base_depth * params.inflow_speed * (0.92 + 0.16 * params.difficulty)
    speed = discharge / np.maximum(weighted_depth, 1.0e-6)
    centerline_slope = np.gradient(centerline, grid.dx)
    tangent_scale = np.sqrt(1.0 + centerline_slope**2)
    tangent_x = 1.0 / tangent_scale
    tangent_y = centerline_slope / tangent_scale
    u = bank_profile * speed[np.newaxis, :] * tangent_x[np.newaxis, :]
    v = bank_profile * speed[np.newaxis, :] * tangent_y[np.newaxis, :]
    return u, v


def _apply_california_feature_velocity_modifiers(
    u: FloatGrid,
    v: FloatGrid,
    x: FloatGrid,
    y: FloatGrid,
    features: tuple[Feature2_5D, ...],
    params: CaliforniaPoolDropParameters2_5D,
    centerline: FloatGrid,
    xs: FloatGrid,
) -> tuple[FloatGrid, FloatGrid]:
    adjusted_u = u.copy()
    adjusted_v = v.copy()
    for feature in features:
        influence = _feature_influence(x, y, feature, params.dx, params.dy)
        if feature.kind == "constriction":
            adjusted_u *= 1.0 + 0.12 * feature.strength * influence
        elif feature.kind == "hole":
            adjusted_u -= params.inflow_speed * 0.16 * feature.strength * influence
        elif feature.kind == "eddy_line":
            center_y = float(np.interp(feature.center[0], xs, centerline))
            side = 1.0 if feature.center[1] >= center_y else -1.0
            adjusted_v += side * params.inflow_speed * 0.34 * feature.strength * influence
        elif feature.kind == "boil":
            adjusted_u += params.inflow_speed * 0.12 * feature.strength * ((x - feature.center[0]) / max(feature.radius, params.dx)) * influence
            adjusted_v += params.inflow_speed * 0.16 * feature.strength * ((y - feature.center[1]) / max(feature.radius, params.dy)) * influence
        elif feature.kind == "wave_train":
            wave = np.abs(np.sin((x - feature.center[0]) * 2.25))
            adjusted_u *= 1.0 + 0.08 * feature.strength * wave * influence
    return adjusted_u, adjusted_v


def _california_pool_controls(
    params: CaliforniaPoolDropParameters2_5D,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
    channel_width: FloatGrid,
) -> tuple[PoolControlMetadata2_5D, ...]:
    controls: list[PoolControlMetadata2_5D] = []
    for pool_index, spec in enumerate((spec for spec in specs if spec.kind == "pool"), start=1):
        mean_width = (spec.width_start + spec.width_end) * 0.5
        lateral = mean_width * (0.26 if pool_index == 1 else -0.24)
        controls.append(
            PoolControlMetadata2_5D(
                pool_id=f"{spec.reach_id}_control",
                reach_id=spec.reach_id,
                depth_profile=(
                    StationProfilePoint2_5D(spec.station_start, spec.depth_start),
                    StationProfilePoint2_5D(spec.station_end, spec.depth_end),
                ),
                tailwater_depth=spec.depth_end,
                storage_coefficient=0.52 + 0.10 * (1.0 - params.difficulty),
                residence_time_seconds=max(6.0, spec.length / max(params.inflow_speed * 0.35, 0.1)),
                outflow_control="drop_controlled" if pool_index == 1 else "tailwater_limited",
                eddy_controls=(
                    PoolEddyControl2_5D(
                        zone_id=f"{spec.reach_id}_river_{'left' if lateral > 0.0 else 'right'}_eddy",
                        center_station=spec.station_start + spec.length * 0.58,
                        lateral_offset=lateral,
                        radius=max(params.dy * 1.5, mean_width * 0.16),
                        circulation_strength=0.32 + 0.18 * params.difficulty,
                        recirculation_risk=0.14 + 0.12 * params.difficulty,
                    ),
                ),
                recirculation_zones=(
                    PoolEddyControl2_5D(
                        zone_id=f"{spec.reach_id}_tailout_recirculation",
                        center_station=spec.station_end - spec.length * 0.18,
                        lateral_offset=-lateral * 0.45,
                        radius=max(params.dy * 1.2, mean_width * 0.12),
                        circulation_strength=0.22 + 0.12 * params.difficulty,
                        recirculation_risk=0.20 + 0.20 * params.difficulty,
                    ),
                ),
                metadata={"generator": "california_pool_drop", "sampled_width": float(np.mean(channel_width))},
            )
        )
    return tuple(controls)


def _california_reach_local_grids(
    params: CaliforniaPoolDropParameters2_5D,
    grid: GridSpec2_5D,
    xs: FloatGrid,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
) -> tuple[ReachLocalGrid2_5D, ...]:
    local_grids: list[ReachLocalGrid2_5D] = []
    for index, spec in enumerate(specs):
        columns = np.flatnonzero(_spec_column_mask(xs, spec, is_last=index == len(specs) - 1))
        upstream_ghost = 0 if index == 0 else 2
        downstream_ghost = 0 if index == len(specs) - 1 else 2
        start_col = max(0, int(columns[0]) - upstream_ghost)
        end_col = min(grid.nx - 1, int(columns[-1]) + downstream_ghost)
        local_grids.append(
            ReachLocalGrid2_5D(
                spec.reach_id,
                GridSpec2_5D(
                    nx=end_col - start_col + 1,
                    ny=params.ny,
                    dx=params.dx,
                    dy=params.dy,
                    origin_x=float(xs[start_col]),
                    origin_y=grid.origin_y,
                ),
                upstream_ghost_cells=upstream_ghost,
                downstream_ghost_cells=downstream_ghost,
            )
        )
    return tuple(local_grids)


def _california_pool_drop_probes(
    grid: GridSpec2_5D,
    xs: FloatGrid,
    centerline: FloatGrid,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
    drop_transition: DropTransitionMetadata2_5D,
) -> tuple[Probe2_5D, ...]:
    probes: list[Probe2_5D] = []
    for spec in specs:
        center = _feature_center(grid, xs, centerline, np.asarray([spec.width_start] * len(xs)), spec.station_midpoint)
        probes.append(Probe2_5D(f"{spec.reach_id}_center", center, metadata={"reach_id": spec.reach_id, "reach_kind": spec.kind}))
    probes.append(
        Probe2_5D(
            "main_drop_cross_section",
            _feature_center(grid, xs, centerline, np.asarray([specs[2].width_start] * len(xs)), drop_transition.crest_station),
            kind="cross_section",
            normal=(0.0, 1.0),
            length=max(specs[2].width_start, specs[2].width_end),
            metadata={"drop_transition_id": drop_transition.transition_id},
        )
    )
    return tuple(probes)


def _california_reach_id_grid(
    grid: GridSpec2_5D,
    xs: FloatGrid,
    specs: tuple[_CaliforniaPoolDropReachSpec, ...],
) -> IntGrid:
    reach_grid = np.full(grid.shape, -1, dtype=np.int32)
    for index, spec in enumerate(specs):
        reach_grid[:, _spec_column_mask(xs, spec, is_last=index == len(specs) - 1)] = index
    return reach_grid


def _california_drop_transition_id_grid(
    grid: GridSpec2_5D,
    xs: FloatGrid,
    transitions: tuple[DropTransitionMetadata2_5D, ...],
) -> IntGrid:
    drop_grid = np.full(grid.shape, -1, dtype=np.int32)
    for index, transition in enumerate(transitions):
        station_start = transition.crest_station - grid.dx * 0.5
        station_end = transition.crest_station + max(transition.control_length, grid.dx)
        drop_grid[:, (xs >= station_start) & (xs <= station_end)] = index
    return drop_grid


def _spec_by_id(specs: tuple[_CaliforniaPoolDropReachSpec, ...], reach_id: str) -> _CaliforniaPoolDropReachSpec:
    for spec in specs:
        if spec.reach_id == reach_id:
            return spec
    raise ValueError(f"Unknown generated reach id: {reach_id}")


def _spec_column_mask(xs: FloatGrid, spec: _CaliforniaPoolDropReachSpec, *, is_last: bool = False) -> NDArray[np.bool_]:
    if is_last:
        return (xs >= spec.station_start) & (xs <= spec.station_end)
    return (xs >= spec.station_start) & (xs < spec.station_end)


def _feature_center(
    grid: GridSpec2_5D,
    xs: FloatGrid,
    centerline: FloatGrid,
    channel_width: FloatGrid,
    station: float,
    lateral_offset: float = 0.0,
) -> tuple[float, float]:
    y_min = float(grid.y_coordinates()[0])
    y_max = float(grid.y_coordinates()[-1])
    width = _width_at_station(xs, channel_width, station)
    center_y = float(np.interp(station, xs, centerline)) + lateral_offset
    margin = max(grid.dy, min(width * 0.08, grid.dy * 2.0))
    return (float(station), max(y_min + margin, min(y_max - margin, center_y)))


def _width_at_station(xs: FloatGrid, channel_width: FloatGrid, station: float) -> float:
    return float(np.interp(station, xs, channel_width))


def _feature_influence(
    x: FloatGrid,
    y: FloatGrid,
    feature: Feature2_5D,
    dx: float,
    dy: float,
) -> FloatGrid:
    scale_x = max(feature.length * 0.5, feature.radius, dx)
    scale_y = max(feature.width * 0.5, feature.radius, dy)
    dx_norm = (x - feature.center[0]) / scale_x
    dy_norm = (y - feature.center[1]) / scale_y
    return np.exp(-(dx_norm**2 + dy_norm**2))


def _unreal_reach_streaming_tile(
    package: CascadingScenarioPackage2_5D,
    index: int,
    reach: ReachMetadata2_5D,
) -> dict[str, object]:
    mask = package.reach_id_grid == index
    bounds = _unreal_reach_bounds(package, reach, mask)
    return {
        "tile_id": f"reach_{index:02d}_{reach.reach_id}",
        "world_partition_layer": "river_reach",
        "streaming_priority": _unreal_reach_streaming_priority(reach),
        "reach_id": reach.reach_id,
        "reach_kind": reach.kind,
        "station_start": reach.station_start,
        "station_end": reach.station_end,
        "length": reach.length,
        "bounds_m": bounds,
        "cell_coverage": int(np.count_nonzero(mask)),
        "local_grid": reach.local_grid.to_json_dict(),
        "debug_overlay": {
            "label": reach.reach_id,
            "color_rgba": _unreal_reach_debug_color(reach.kind),
            "show_station_labels": True,
        },
        "audio": {
            "zone_id": f"audio_{reach.reach_id}",
            "emitter_shape": "spline_segment",
            "attenuation_preset": "large_water_reach",
            "parameters": _unreal_reach_audio_parameters(package, reach, mask),
        },
        "vfx": {
            "zone_id": f"vfx_{reach.reach_id}",
            "effect_family": _unreal_reach_vfx_family(reach.kind),
            "parameters": _unreal_reach_vfx_parameters(reach),
        },
        "designer_review": {
            "display_name": reach.reach_id.replace("_", " ").title(),
            "confidence_score": reach.confidence_score,
            "bank_shape": reach.bank_shape.to_json_dict(),
            "vegetation_flags": list(reach.vegetation_flags),
            "debris_flags": list(reach.debris_flags),
            "metadata": reach.metadata,
            "linked_features": _unreal_feature_links(package, reach_id=reach.reach_id),
        },
    }


def _unreal_drop_transition_zone(
    package: CascadingScenarioPackage2_5D,
    index: int,
    transition: DropTransitionMetadata2_5D,
) -> dict[str, object]:
    mask = package.drop_transition_id_grid == index
    bounds = _unreal_drop_bounds(package, transition, mask)
    return {
        "zone_id": f"drop_{index:02d}_{transition.transition_id}",
        "world_partition_layer": "river_drop_transition",
        "streaming_priority": 100,
        "transition_id": transition.transition_id,
        "upstream_reach_id": transition.upstream_reach_id,
        "downstream_reach_id": transition.downstream_reach_id,
        "crest_station": transition.crest_station,
        "bounds_m": bounds,
        "cell_coverage": int(np.count_nonzero(mask)),
        "geometry_kind": transition.geometry_kind,
        "bed_elevation_fall": transition.bed_elevation_fall,
        "ramp_length": transition.ramp_length,
        "ledge_length": transition.ledge_length,
        "tailwater_depth": transition.tailwater_depth,
        "expected_hydraulic_control": transition.expected_hydraulic_control,
        "recirculation_risk": transition.recirculation_risk,
        "aeration_proxy": transition.aeration_proxy,
        "turbulence_proxy": transition.turbulence_proxy,
        "hazard_tags": list(transition.hazard_tags),
        "debug_overlay": {
            "label": transition.transition_id,
            "color_rgba": [1.0, 0.22, 0.08, 0.88],
            "show_crest_marker": True,
            "show_upstream_downstream_links": True,
        },
        "audio": {
            "zone_id": f"audio_{transition.transition_id}",
            "emitter_shape": "area_drop",
            "attenuation_preset": "rapid_hazard",
            "event_tags": sorted(set(("drop", "hydraulic", *transition.hazard_tags))),
            "parameters": {
                "recirculation_risk": transition.recirculation_risk,
                "aeration": transition.aeration_proxy,
                "turbulence": transition.turbulence_proxy,
                "fall_m": transition.bed_elevation_fall,
            },
        },
        "vfx": {
            "zone_id": f"vfx_{transition.transition_id}",
            "effect_family": "drop_hydraulic",
            "event_tags": sorted(set(("foam", "spray", *transition.hazard_tags))),
            "parameters": {
                "foam_intensity": max(transition.aeration_proxy, transition.turbulence_proxy),
                "spray_intensity": min(1.0, transition.bed_elevation_fall),
                "recirculation": transition.recirculation_risk,
            },
        },
        "designer_review": {
            "display_name": transition.transition_id.replace("_", " ").title(),
            "metadata": transition.metadata,
            "review_focus": sorted(set(("line_choice", "safety", *transition.hazard_tags))),
        },
    }


def _unreal_reach_drop_grid(package: CascadingScenarioPackage2_5D) -> dict[str, object]:
    return {
        "schema_version": "raftsim.unreal_cascading_reach_drop_grid.v0",
        "scenario_id": package.scenario.metadata.scenario_id,
        "grid": {
            "nx": package.scenario.grid.nx,
            "ny": package.scenario.grid.ny,
            "dx": package.scenario.grid.dx,
            "dy": package.scenario.grid.dy,
            "origin_x": package.scenario.grid.origin_x,
            "origin_y": package.scenario.grid.origin_y,
        },
        "reach_index": {str(index): reach.reach_id for index, reach in enumerate(package.reaches)},
        "drop_transition_index": {
            str(index): transition.transition_id for index, transition in enumerate(package.drop_transitions)
        },
        "reach_id_grid": package.reach_id_grid.tolist(),
        "drop_transition_id_grid": package.drop_transition_id_grid.tolist(),
    }


def _unreal_debug_overlays(
    package: CascadingScenarioPackage2_5D,
    reach_index: dict[str, str],
    drop_transition_index: dict[str, str],
) -> list[dict[str, object]]:
    return [
        {
            "overlay_id": "reach_id_grid",
            "source_file": UNREAL_CASCADING_CORRIDOR_GRID_FILE,
            "grid_field": "reach_id_grid",
            "legend": reach_index,
            "purpose": "World Partition reach streaming and designer/debug color overlays.",
        },
        {
            "overlay_id": "drop_transition_id_grid",
            "source_file": UNREAL_CASCADING_CORRIDOR_GRID_FILE,
            "grid_field": "drop_transition_id_grid",
            "legend": drop_transition_index,
            "purpose": "Hydraulic transition debug markers and force/audio/VFX trigger zones.",
        },
        {
            "overlay_id": "feature_reach_links",
            "source_file": UNREAL_CASCADING_CORRIDOR_METADATA_FILE,
            "feature_count": len(package.scenario.features),
            "purpose": "Shows authored feature ownership by reach/drop metadata.",
        },
    ]


def _unreal_fidelity_review_overlays(
    package: CascadingScenarioPackage2_5D,
    streaming_tiles: list[dict[str, object]],
    drop_transitions: list[dict[str, object]],
) -> dict[str, object]:
    checkpoint_ids = [
        checkpoint.checkpoint_id for checkpoint in _stitched_validation_raft_transition_checkpoints(package)
    ]
    return {
        "schema_version": UNREAL_FIDELITY_REVIEW_OVERLAY_SCHEMA_VERSION,
        "review_mode": "river_fidelity_review",
        "default_enabled": False,
        "purpose": (
            "Compare authored validation annotations, GeoClaw/C++ fields, raft motion, rendered water/foam, "
            "audio cues, and expected raft outcomes in the Unreal viewport."
        ),
        "source_files": {
            "rapid_review_workflow": "rapid_review_editor_workflow.json",
            "river_validation_annotations": "review/river_validation_annotations.geojson",
            "stitched_validation_manifest": (
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_MANIFEST_FILE}"
            ),
            "stitched_validation_fields": (
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE}"
            ),
            "raft_transition_checkpoints": (
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_DIR}/"
                f"{STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE}"
            ),
            "corridor_metadata": UNREAL_CASCADING_CORRIDOR_METADATA_FILE,
            "reach_drop_grid": UNREAL_CASCADING_CORRIDOR_GRID_FILE,
        },
        "overlays": [
            _unreal_annotation_fidelity_overlay(),
            _unreal_solver_field_fidelity_overlay(),
            _unreal_raft_trajectory_fidelity_overlay(checkpoint_ids),
            _unreal_rendered_water_fidelity_overlay(streaming_tiles, drop_transitions),
            _unreal_audio_cue_fidelity_overlay(streaming_tiles, drop_transitions),
            _unreal_expected_outcome_fidelity_overlay(drop_transitions),
        ],
        "review_targets": _unreal_fidelity_review_targets(drop_transitions),
        "comparison_panels": [
            {
                "panel_id": "annotation_vs_rendered_water",
                "primary_overlays": ["annotation_geometry", "rendered_water_foam_audio"],
                "purpose": "Check that pins, spans, polygons, and raft lines match visible hydraulics, foam, spray, and sound.",
            },
            {
                "panel_id": "solver_fields_vs_visuals",
                "primary_overlays": ["solver_fields", "rendered_water_foam_audio"],
                "purpose": "Compare depth, surface, velocity, wet mask, turbulence, aeration, and foam cues.",
            },
            {
                "panel_id": "raft_outcomes",
                "primary_overlays": ["raft_trajectories", "expected_outcomes"],
                "purpose": "Review expected surf, flush, pin, release, flip, and clean-line behavior against raft motion.",
            },
        ],
    }


def _unreal_annotation_fidelity_overlay() -> dict[str, object]:
    return {
        "overlay_id": "annotation_geometry",
        "display_name": "Annotation Pins Spans Polygons",
        "category": "annotation",
        "source_file": "review/river_validation_annotations.geojson",
        "geometry_types": ["Point", "LineString", "Polygon"],
        "viewport_draw": {
            "point_style": "validation_pin",
            "span_style": "station_span",
            "polygon_style": "transparent_hazard_region",
            "line_style": "raft_line",
            "label_fields": ["annotation_id", "expected_outcome", "confidence"],
        },
        "required_properties": [
            "annotation_id",
            "anchor_type",
            "station_m",
            "expected_outcome",
            "rights_provenance",
        ],
    }


def _unreal_solver_field_fidelity_overlay() -> dict[str, object]:
    return {
        "overlay_id": "solver_fields",
        "display_name": "GeoClaw Cpp Solver Fields",
        "category": "solver",
        "source_file": STITCHED_WHOLE_WINDOW_VALIDATION_FIELDS_FILE,
        "source_manifest": STITCHED_WHOLE_WINDOW_VALIDATION_MANIFEST_FILE,
        "fields": [
            "bed",
            "depth",
            "eta",
            "u",
            "v",
            "hu",
            "hv",
            "wet",
            "reach_id_grid",
            "drop_transition_id_grid",
        ],
        "viewport_draw": {
            "depth": "blue_alpha_heatmap",
            "surface_elevation": "contour_lines",
            "velocity": "arrow_glyphs",
            "wet_mask": "wet_dry_stipple",
            "reach_drop_ids": "indexed_color_overlay",
        },
        "comparison_sources": ["GeoClaw normalized output", "custom C++ fixed-grid output"],
    }


def _unreal_raft_trajectory_fidelity_overlay(checkpoint_ids: list[str]) -> dict[str, object]:
    return {
        "overlay_id": "raft_trajectories",
        "display_name": "Raft Trajectories And Checkpoints",
        "category": "raft",
        "source_file": STITCHED_WHOLE_WINDOW_VALIDATION_RAFT_CHECKPOINTS_FILE,
        "future_runtime_capture": "replay/raft_trajectory.jsonl",
        "checkpoint_ids": checkpoint_ids,
        "viewport_draw": {
            "trajectory_style": "time_gradient_polyline",
            "checkpoint_style": "numbered_transition_marker",
            "contact_style": "pin_flip_release_event_marker",
            "crew_action_style": "high_side_brace_lean_callout",
        },
        "required_events": ["entry", "crest", "recovery", "surf", "flush", "pin", "release", "flip"],
    }


def _unreal_rendered_water_fidelity_overlay(
    streaming_tiles: list[dict[str, object]],
    drop_transitions: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "overlay_id": "rendered_water_foam_audio",
        "display_name": "Rendered Water Foam Spray",
        "category": "visual",
        "source_collections": ["streaming_tiles.vfx", "drop_transition_zones.vfx"],
        "reach_vfx_zone_ids": [
            str(tile["vfx"]["zone_id"])
            for tile in streaming_tiles
            if isinstance(tile.get("vfx"), dict) and "zone_id" in tile["vfx"]
        ],
        "drop_vfx_zone_ids": [
            str(transition["vfx"]["zone_id"])
            for transition in drop_transitions
            if isinstance(transition.get("vfx"), dict) and "zone_id" in transition["vfx"]
        ],
        "viewport_draw": {
            "foam": "foam_intensity_heatmap",
            "spray": "niagara_spawn_debug",
            "aeration": "whitewater_mask",
            "turbulence": "surface_chop_vectors",
        },
        "comparison_fields": ["depth", "velocity", "wet", "aeration_proxy", "turbulence_proxy"],
    }


def _unreal_audio_cue_fidelity_overlay(
    streaming_tiles: list[dict[str, object]],
    drop_transitions: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "overlay_id": "audio_cues",
        "display_name": "Water Audio Cues",
        "category": "audio",
        "source_collections": ["audio_zones", "streaming_tiles.audio", "drop_transition_zones.audio"],
        "reach_audio_zone_ids": [
            str(tile["audio"]["zone_id"])
            for tile in streaming_tiles
            if isinstance(tile.get("audio"), dict) and "zone_id" in tile["audio"]
        ],
        "drop_audio_zone_ids": [
            str(transition["audio"]["zone_id"])
            for transition in drop_transitions
            if isinstance(transition.get("audio"), dict) and "zone_id" in transition["audio"]
        ],
        "viewport_draw": {
            "emitter_shape": "wire_volume",
            "attenuation": "radius_shell",
            "event_tags": "floating_labels",
            "intensity": "meter_bar",
        },
        "comparison_fields": ["velocity", "aeration_proxy", "turbulence_proxy", "fall_m"],
    }


def _unreal_expected_outcome_fidelity_overlay(
    drop_transitions: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "overlay_id": "expected_outcomes",
        "display_name": "Expected Surf Flush Pin Flip",
        "category": "outcome",
        "source_collection": "drop_transition_zones",
        "transition_outcomes": [
            {
                "transition_id": str(transition["transition_id"]),
                "expected_hydraulic_control": str(transition.get("expected_hydraulic_control", "unknown")),
                "hazard_tags": list(transition.get("hazard_tags", [])),
                "expected_outcomes": _unreal_expected_outcomes_for_transition(transition),
            }
            for transition in drop_transitions
        ],
        "viewport_draw": {
            "surf": "retentive_hole_badge",
            "flush": "downstream_arrow_badge",
            "pin": "contact_warning_badge",
            "release": "counterplay_window_badge",
            "flip": "roll_risk_badge",
        },
    }


def _unreal_fidelity_review_targets(drop_transitions: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "target_id": f"fidelity_{transition['transition_id']}",
            "anchor_type": "drop_transition",
            "transition_id": transition["transition_id"],
            "upstream_reach_id": transition["upstream_reach_id"],
            "downstream_reach_id": transition["downstream_reach_id"],
            "station_m": transition["crest_station"],
            "bounds_m": transition["bounds_m"],
            "expected_outcomes": _unreal_expected_outcomes_for_transition(transition),
            "review_overlays": [
                "annotation_geometry",
                "solver_fields",
                "raft_trajectories",
                "rendered_water_foam_audio",
                "audio_cues",
                "expected_outcomes",
            ],
        }
        for transition in drop_transitions
    ]


def _unreal_expected_outcomes_for_transition(transition: dict[str, object]) -> list[str]:
    tags = {str(tag) for tag in transition.get("hazard_tags", [])}
    control = str(transition.get("expected_hydraulic_control", "unknown"))
    outcomes = {"flush", "clean_line"}
    if "hole" in tags or control == "retentive_hole":
        outcomes.update(("surf", "flush", "pin_risk", "release_window"))
    if {"rock", "boulder_sieves", "boulder_garden"} & tags:
        outcomes.update(("pin", "release", "flip_risk"))
    if "wave_train" in tags or control == "wave_train":
        outcomes.update(("clean_line", "flip_risk"))
    if "lateral" in tags:
        outcomes.update(("flip_risk", "high_side_counterplay"))
    return sorted(outcomes)


def _unreal_audio_zones(
    streaming_tiles: list[dict[str, object]],
    drop_transitions: list[dict[str, object]],
) -> list[dict[str, object]]:
    zones: list[dict[str, object]] = []
    for tile in streaming_tiles:
        audio = tile["audio"]
        if isinstance(audio, dict):
            zones.append({"owner_id": tile["reach_id"], **audio})
    for transition in drop_transitions:
        audio = transition["audio"]
        if isinstance(audio, dict):
            zones.append({"owner_id": transition["transition_id"], **audio})
    return zones


def _unreal_vfx_zones(
    streaming_tiles: list[dict[str, object]],
    drop_transitions: list[dict[str, object]],
) -> list[dict[str, object]]:
    zones: list[dict[str, object]] = []
    for tile in streaming_tiles:
        vfx = tile["vfx"]
        if isinstance(vfx, dict):
            zones.append({"owner_id": tile["reach_id"], **vfx})
    for transition in drop_transitions:
        vfx = transition["vfx"]
        if isinstance(vfx, dict):
            zones.append({"owner_id": transition["transition_id"], **vfx})
    return zones


def _unreal_reach_bounds(
    package: CascadingScenarioPackage2_5D,
    reach: ReachMetadata2_5D,
    mask: NDArray[np.bool_],
) -> dict[str, float]:
    half_width = _reach_max_width(reach) * 0.5
    z_min, z_max = _vertical_bounds(package, mask)
    return {
        "min_x": reach.station_start,
        "max_x": reach.station_end,
        "min_y": -half_width,
        "max_y": half_width,
        "min_z": z_min,
        "max_z": z_max,
    }


def _unreal_drop_bounds(
    package: CascadingScenarioPackage2_5D,
    transition: DropTransitionMetadata2_5D,
    mask: NDArray[np.bool_],
) -> dict[str, float]:
    upstream = _reach_by_id(package.reaches, transition.upstream_reach_id)
    downstream = _reach_by_id(package.reaches, transition.downstream_reach_id)
    half_width = max(_reach_max_width(upstream), _reach_max_width(downstream)) * 0.55
    half_length = max(transition.ramp_length + transition.ledge_length, package.scenario.grid.dx * 4.0) * 0.5
    z_min, z_max = _vertical_bounds(package, mask)
    return {
        "min_x": transition.crest_station - half_length,
        "max_x": transition.crest_station + half_length,
        "min_y": -half_width,
        "max_y": half_width,
        "min_z": z_min,
        "max_z": z_max,
    }


def _vertical_bounds(package: CascadingScenarioPackage2_5D, mask: NDArray[np.bool_]) -> tuple[float, float]:
    if np.any(mask):
        bed = package.scenario.bed[mask]
        eta = package.scenario.initial_state.eta[mask]
        return float(np.min(bed)), float(np.max(eta))
    return float(np.min(package.scenario.bed)), float(np.max(package.scenario.initial_state.eta))


def _reach_by_id(reaches: tuple[ReachMetadata2_5D, ...], reach_id: str) -> ReachMetadata2_5D:
    for reach in reaches:
        if reach.reach_id == reach_id:
            return reach
    raise ValueError(f"Unknown reach id: {reach_id}")


def _reach_max_width(reach: ReachMetadata2_5D) -> float:
    return max(point.value for point in reach.width_profile)


def _reach_mean_slope(reach: ReachMetadata2_5D) -> float:
    return float(sum(point.value for point in reach.slope_profile) / len(reach.slope_profile))


def _unreal_reach_streaming_priority(reach: ReachMetadata2_5D) -> int:
    priority_by_kind = {
        "drop": 90,
        "wave_train": 80,
        "boulder_garden": 76,
        "tongue": 70,
        "eddy_recovery": 62,
        "pool": 50,
        "runout": 45,
    }
    return priority_by_kind.get(reach.kind, 50)


def _unreal_reach_debug_color(kind: str) -> list[float]:
    colors = {
        "pool": [0.12, 0.42, 1.0, 0.62],
        "tongue": [0.0, 0.84, 0.95, 0.68],
        "drop": [1.0, 0.18, 0.08, 0.78],
        "wave_train": [0.68, 0.92, 1.0, 0.72],
        "eddy_recovery": [0.12, 0.72, 0.38, 0.68],
        "boulder_garden": [0.56, 0.56, 0.56, 0.72],
        "runout": [0.18, 0.34, 0.72, 0.58],
    }
    return colors.get(kind, [1.0, 1.0, 1.0, 0.55])


def _unreal_reach_audio_parameters(
    package: CascadingScenarioPackage2_5D,
    reach: ReachMetadata2_5D,
    mask: NDArray[np.bool_],
) -> dict[str, float | str]:
    speed = np.hypot(package.scenario.initial_state.u, package.scenario.initial_state.v)
    if np.any(mask):
        mean_speed = float(np.mean(speed[mask]))
        max_speed = float(np.max(speed[mask]))
    else:
        mean_speed = float(np.mean(speed))
        max_speed = float(np.max(speed))
    return {
        "reach_kind": reach.kind,
        "mean_flow_speed": mean_speed,
        "max_flow_speed": max_speed,
        "roughness": reach.bed_roughness,
        "boulder_density": reach.boulder_density,
        "slope": _reach_mean_slope(reach),
    }


def _unreal_reach_vfx_family(kind: str) -> str:
    families = {
        "pool": "calm_pool",
        "tongue": "fast_tongue",
        "drop": "ledge_drop",
        "wave_train": "standing_waves",
        "eddy_recovery": "eddy_and_boil",
        "boulder_garden": "boulder_spray",
        "runout": "runout_flow",
    }
    return families.get(kind, "river_surface")


def _unreal_reach_vfx_parameters(reach: ReachMetadata2_5D) -> dict[str, float | str]:
    foam_by_kind = {
        "pool": 0.08,
        "tongue": 0.25,
        "drop": 0.85,
        "wave_train": 0.72,
        "eddy_recovery": 0.36,
        "boulder_garden": 0.58,
        "runout": 0.16,
    }
    foam = min(1.0, foam_by_kind.get(reach.kind, 0.2) + reach.boulder_density * 0.25)
    return {
        "reach_kind": reach.kind,
        "foam_intensity": foam,
        "surface_chop": min(1.0, _reach_mean_slope(reach) * 16.0 + reach.boulder_density * 0.35),
        "spray_probability": min(1.0, foam * 0.45 + reach.boulder_density * 0.25),
    }


def _unreal_feature_links(
    package: CascadingScenarioPackage2_5D,
    *,
    reach_id: str,
) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []
    for index, feature in enumerate(package.scenario.features):
        metadata = feature.metadata if isinstance(feature.metadata, dict) else {}
        if metadata.get("reach_id") != reach_id:
            continue
        links.append(
            {
                "feature_index": index,
                "kind": feature.kind,
                "center_m": {"x": feature.center[0], "y": feature.center[1]},
                "radius": feature.radius,
                "length": feature.length,
                "width": feature.width,
                "pattern_role": metadata.get("pattern_role", ""),
            }
        )
    return links


def _smoothstep(value: float | FloatGrid) -> float | FloatGrid:
    t = np.clip(value, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


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


def _stitched_validation_field_arrays(package: CascadingScenarioPackage2_5D) -> dict[str, NDArray[np.generic]]:
    state = package.scenario.initial_state
    return {
        "bed": package.scenario.bed,
        "depth": state.depth,
        "eta": state.eta,
        "u": state.u,
        "v": state.v,
        "hu": state.hu,
        "hv": state.hv,
        "wet": state.wet,
        "reach_id_grid": package.reach_id_grid,
        "drop_transition_id_grid": package.drop_transition_id_grid,
    }


def _stitched_validation_field_summary(
    name: str,
    array: NDArray[np.generic],
) -> StitchedValidationFieldSummary2_5D:
    values = np.asarray(array, dtype=np.float64)
    finite_values = values[np.isfinite(values)]
    if finite_values.size:
        min_value = float(np.min(finite_values))
        max_value = float(np.max(finite_values))
        mean_value = float(np.mean(finite_values))
    else:
        min_value = None
        max_value = None
        mean_value = None
    units_by_name = {
        "bed": "m",
        "depth": "m",
        "eta": "m",
        "u": "m/s",
        "v": "m/s",
        "hu": "m^2/s",
        "hv": "m^2/s",
        "wet": "boolean",
        "reach_id_grid": "index",
        "drop_transition_id_grid": "index",
    }
    field_name_by_key = {
        "bed": "bed_elevation_m",
        "depth": "water_depth_m",
        "eta": "surface_elevation_m",
        "u": "velocity_u_m_s",
        "v": "velocity_v_m_s",
        "hu": "momentum_hu_m2_s",
        "hv": "momentum_hv_m2_s",
        "wet": "wet_mask",
        "reach_id_grid": "reach_id_grid",
        "drop_transition_id_grid": "drop_transition_id_grid",
    }
    return StitchedValidationFieldSummary2_5D(
        field_name=field_name_by_key[name],
        npz_key=name,
        units=units_by_name[name],
        shape=(int(array.shape[0]), int(array.shape[1])),
        dtype=str(array.dtype),
        min_value=min_value,
        max_value=max_value,
        mean_value=mean_value,
    )


def _stitched_validation_probe_samples(
    package: CascadingScenarioPackage2_5D,
) -> tuple[StitchedValidationProbeSample2_5D, ...]:
    probes: list[Probe2_5D] = [probe for probe in package.scenario.probes if probe.kind != "cross_section"]
    covered_reach_ids = {
        str(probe.metadata["reach_id"])
        for probe in probes
        if probe.metadata.get("reach_id") is not None
    }
    for reach in package.reaches:
        if reach.reach_id not in covered_reach_ids:
            probes.append(
                Probe2_5D(
                    probe_id=f"{reach.reach_id}_validation_center",
                    position=(reach.station_start + reach.length * 0.5, 0.0),
                    metadata={"reach_id": reach.reach_id, "source": "stitched_validation_default"},
                )
            )
    return tuple(_stitched_validation_probe_sample(package, probe) for probe in probes)


def _stitched_validation_probe_sample(
    package: CascadingScenarioPackage2_5D,
    probe: Probe2_5D,
) -> StitchedValidationProbeSample2_5D:
    sample = _sample_stitched_validation_cell(package, probe.position)
    return StitchedValidationProbeSample2_5D(
        probe_id=probe.probe_id,
        kind=probe.kind,
        position=(float(probe.position[0]), float(probe.position[1])),
        grid_index=sample["grid_index"],  # type: ignore[arg-type]
        reach_id=sample["reach_id"],  # type: ignore[arg-type]
        drop_transition_id=sample["drop_transition_id"],  # type: ignore[arg-type]
        bed_elevation_m=float(sample["bed_elevation_m"]),
        depth_m=float(sample["depth_m"]),
        surface_elevation_m=float(sample["surface_elevation_m"]),
        velocity_m_s=sample["velocity_m_s"],  # type: ignore[arg-type]
        speed_m_s=float(sample["speed_m_s"]),
        froude_number=float(sample["froude_number"]),
        wet=bool(sample["wet"]),
        metadata=dict(probe.metadata),
    )


def _stitched_validation_cross_sections(
    package: CascadingScenarioPackage2_5D,
) -> tuple[StitchedValidationCrossSection2_5D, ...]:
    probes: list[Probe2_5D] = [probe for probe in package.scenario.probes if probe.kind == "cross_section"]
    seen_ids = {probe.probe_id for probe in probes}
    for reach in package.reaches:
        probe_id = f"{reach.reach_id}_validation_cross_section"
        if probe_id not in seen_ids:
            probes.append(
                Probe2_5D(
                    probe_id=probe_id,
                    position=(reach.station_start + reach.length * 0.5, 0.0),
                    kind="cross_section",
                    normal=(0.0, 1.0),
                    length=_reach_max_width(reach),
                    metadata={"reach_id": reach.reach_id, "source": "stitched_validation_default"},
                )
            )
            seen_ids.add(probe_id)
    for transition in package.drop_transitions:
        probe_id = f"{transition.transition_id}_validation_cross_section"
        if probe_id not in seen_ids:
            upstream = _reach_by_id(package.reaches, transition.upstream_reach_id)
            downstream = _reach_by_id(package.reaches, transition.downstream_reach_id)
            probes.append(
                Probe2_5D(
                    probe_id=probe_id,
                    position=(transition.crest_station, 0.0),
                    kind="cross_section",
                    normal=(0.0, 1.0),
                    length=max(_reach_max_width(upstream), _reach_max_width(downstream)),
                    metadata={
                        "drop_transition_id": transition.transition_id,
                        "source": "stitched_validation_default",
                    },
                )
            )
            seen_ids.add(probe_id)
    return tuple(_stitched_validation_cross_section(package, probe) for probe in probes)


def _stitched_validation_cross_section(
    package: CascadingScenarioPackage2_5D,
    probe: Probe2_5D,
) -> StitchedValidationCrossSection2_5D:
    grid = package.scenario.grid
    direction = probe.normal or (0.0, 1.0)
    direction_length = math.hypot(direction[0], direction[1])
    if direction_length <= 1.0e-9:
        direction = (0.0, 1.0)
        direction_length = 1.0
    direction = (direction[0] / direction_length, direction[1] / direction_length)
    length = probe.length if probe.length > 0.0 else grid.dy * max(grid.ny - 1, 1)
    spacing = max(min(grid.dx, grid.dy), 1.0e-9)
    sample_count = max(3, int(math.ceil(length / spacing)) + 1)
    offsets = np.linspace(-0.5 * length, 0.5 * length, sample_count)
    samples = [
        _sample_stitched_validation_cell(
            package,
            (probe.position[0] + float(offset) * direction[0], probe.position[1] + float(offset) * direction[1]),
        )
        for offset in offsets
    ]
    depths = np.asarray([float(sample["depth_m"]) for sample in samples], dtype=np.float64)
    etas = np.asarray([float(sample["surface_elevation_m"]) for sample in samples], dtype=np.float64)
    beds = np.asarray([float(sample["bed_elevation_m"]) for sample in samples], dtype=np.float64)
    speeds = np.asarray([float(sample["speed_m_s"]) for sample in samples], dtype=np.float64)
    us = np.asarray([float(sample["velocity_m_s"][0]) for sample in samples], dtype=np.float64)  # type: ignore[index]
    wet = np.asarray([bool(sample["wet"]) for sample in samples], dtype=np.bool_)
    center_sample = _sample_stitched_validation_cell(package, probe.position)
    wet_values = wet.astype(np.float64)
    wet_sample_count = int(np.count_nonzero(wet))
    mass_flux_proxy = float(np.sum(depths * us * wet_values) * spacing)
    momentum_flux_proxy = float(np.sum(depths * us * speeds * wet_values) * spacing)
    return StitchedValidationCrossSection2_5D(
        section_id=probe.probe_id,
        station_m=float(probe.position[0]),
        center=(float(probe.position[0]), float(probe.position[1])),
        sample_direction=direction,
        length_m=float(length),
        column=center_sample["grid_index"][1],  # type: ignore[index]
        reach_id=center_sample["reach_id"],  # type: ignore[arg-type]
        drop_transition_id=center_sample["drop_transition_id"],  # type: ignore[arg-type]
        sample_count=sample_count,
        wet_sample_count=wet_sample_count,
        wetted_width_m=float(wet_sample_count * spacing),
        mean_depth_m=float(np.mean(depths)),
        max_depth_m=float(np.max(depths)),
        mean_surface_elevation_m=float(np.mean(etas)),
        min_bed_elevation_m=float(np.min(beds)),
        max_speed_m_s=float(np.max(speeds)),
        mass_flux_proxy_m3_s=mass_flux_proxy,
        momentum_flux_proxy_m4_s2=momentum_flux_proxy,
        metadata=dict(probe.metadata),
    )


def _stitched_validation_conservation_summary(
    package: CascadingScenarioPackage2_5D,
) -> StitchedValidationConservationSummary2_5D:
    scenario = package.scenario
    state = scenario.initial_state
    cell_area = scenario.grid.dx * scenario.grid.dy
    speed = np.hypot(state.u, state.v)
    wet_cell_count = int(np.count_nonzero(state.wet))
    total_cell_count = int(state.wet.size)
    total_water_volume = float(np.sum(state.depth) * cell_area)
    water_density_kg_m3 = 1000.0
    return StitchedValidationConservationSummary2_5D(
        scenario_id=scenario.metadata.scenario_id,
        wet_cell_count=wet_cell_count,
        total_cell_count=total_cell_count,
        wet_fraction=float(wet_cell_count / max(total_cell_count, 1)),
        total_water_volume_m3=total_water_volume,
        mass_proxy_kg=float(total_water_volume * water_density_kg_m3),
        x_momentum_proxy_kg_m_s=float(np.sum(state.hu) * cell_area * water_density_kg_m3),
        y_momentum_proxy_kg_m_s=float(np.sum(state.hv) * cell_area * water_density_kg_m3),
        min_depth_m=float(np.min(state.depth)),
        max_depth_m=float(np.max(state.depth)),
        min_surface_elevation_m=float(np.min(state.eta)),
        max_surface_elevation_m=float(np.max(state.eta)),
        min_bed_elevation_m=float(np.min(scenario.bed)),
        max_bed_elevation_m=float(np.max(scenario.bed)),
        max_speed_m_s=float(np.max(speed)),
        handoff_report=evaluate_cascading_handoff_conservation(package),
    )


def _stitched_validation_raft_transition_checkpoints(
    package: CascadingScenarioPackage2_5D,
) -> tuple[StitchedValidationRaftTransitionCheckpoint2_5D, ...]:
    checkpoints: list[StitchedValidationRaftTransitionCheckpoint2_5D] = []
    covered_pairs: set[tuple[str, str]] = set()
    for transition in package.drop_transitions:
        covered_pairs.add((transition.upstream_reach_id, transition.downstream_reach_id))
        offsets = (
            ("upstream_entry", -package.scenario.grid.dx),
            ("crest", 0.0),
            ("downstream_recovery", max(transition.control_length, package.scenario.grid.dx)),
        )
        for phase, offset in offsets:
            station = _clamped_station(package, transition.crest_station + offset)
            checkpoints.append(
                _stitched_validation_raft_checkpoint(
                    package,
                    checkpoint_id=f"{transition.transition_id}_{phase}",
                    transition_id=transition.transition_id,
                    drop_transition_id=transition.transition_id,
                    phase=phase,
                    upstream_reach_id=transition.upstream_reach_id,
                    downstream_reach_id=transition.downstream_reach_id,
                    station=station,
                    expected_hydraulic_control=transition.expected_hydraulic_control,
                    hazard_tags=transition.hazard_tags,
                    bed_elevation_fall=transition.bed_elevation_fall,
                    metadata={
                        "geometry_kind": transition.geometry_kind,
                        "recirculation_risk": transition.recirculation_risk,
                        "aeration_proxy": transition.aeration_proxy,
                        "turbulence_proxy": transition.turbulence_proxy,
                    },
                )
            )
    ordered_reaches = tuple(sorted(package.reaches, key=lambda reach: reach.station_start))
    for upstream, downstream in zip(ordered_reaches, ordered_reaches[1:]):
        pair = (upstream.reach_id, downstream.reach_id)
        if pair in covered_pairs:
            continue
        transition_id = f"reach_boundary_{upstream.reach_id}_to_{downstream.reach_id}"
        station = _clamped_station(package, upstream.station_end)
        checkpoints.append(
            _stitched_validation_raft_checkpoint(
                package,
                checkpoint_id=f"{transition_id}_continuity",
                transition_id=transition_id,
                drop_transition_id=None,
                phase="reach_boundary_continuity",
                upstream_reach_id=upstream.reach_id,
                downstream_reach_id=downstream.reach_id,
                station=station,
                expected_hydraulic_control="unknown",
                hazard_tags=(),
                bed_elevation_fall=0.0,
                metadata={"source": "stitched_validation_reach_boundary"},
            )
        )
    return tuple(checkpoints)


def _stitched_validation_raft_checkpoint(
    package: CascadingScenarioPackage2_5D,
    *,
    checkpoint_id: str,
    transition_id: str,
    drop_transition_id: str | None,
    phase: str,
    upstream_reach_id: str,
    downstream_reach_id: str,
    station: float,
    expected_hydraulic_control: str,
    hazard_tags: tuple[str, ...],
    bed_elevation_fall: float,
    metadata: dict[str, MetadataValue],
) -> StitchedValidationRaftTransitionCheckpoint2_5D:
    position = (station, 0.0)
    sample = _sample_stitched_validation_cell(package, position)
    return StitchedValidationRaftTransitionCheckpoint2_5D(
        checkpoint_id=checkpoint_id,
        transition_id=transition_id,
        drop_transition_id=drop_transition_id,
        phase=phase,
        upstream_reach_id=upstream_reach_id,
        downstream_reach_id=downstream_reach_id,
        station_m=station,
        position=position,
        grid_index=sample["grid_index"],  # type: ignore[arg-type]
        sampled_reach_id=sample["reach_id"],  # type: ignore[arg-type]
        sampled_drop_transition_id=sample["drop_transition_id"],  # type: ignore[arg-type]
        expected_hydraulic_control=expected_hydraulic_control,
        hazard_tags=hazard_tags,
        bed_elevation_fall_m=bed_elevation_fall,
        depth_m=float(sample["depth_m"]),
        surface_elevation_m=float(sample["surface_elevation_m"]),
        velocity_m_s=sample["velocity_m_s"],  # type: ignore[arg-type]
        speed_m_s=float(sample["speed_m_s"]),
        froude_number=float(sample["froude_number"]),
        wet=bool(sample["wet"]),
        metadata=metadata,
    )


def _sample_stitched_validation_cell(
    package: CascadingScenarioPackage2_5D,
    position: tuple[float, float],
    *,
    gravity: float = 9.80665,
) -> dict[str, object]:
    grid = package.scenario.grid
    row, column = _grid_index_for_position(grid, position)
    state = package.scenario.initial_state
    depth = float(state.depth[row, column])
    u = float(state.u[row, column])
    v = float(state.v[row, column])
    speed = math.hypot(u, v)
    reach_index = int(package.reach_id_grid[row, column])
    drop_transition_index = int(package.drop_transition_id_grid[row, column])
    return {
        "grid_index": (row, column),
        "reach_id": None if reach_index < 0 else package.reaches[reach_index].reach_id,
        "drop_transition_id": (
            None if drop_transition_index < 0 else package.drop_transitions[drop_transition_index].transition_id
        ),
        "bed_elevation_m": float(package.scenario.bed[row, column]),
        "depth_m": depth,
        "surface_elevation_m": float(state.eta[row, column]),
        "velocity_m_s": (u, v),
        "speed_m_s": speed,
        "froude_number": 0.0 if depth <= 1.0e-9 else speed / math.sqrt(gravity * depth),
        "wet": bool(state.wet[row, column]),
    }


def _grid_index_for_position(grid: GridSpec2_5D, position: tuple[float, float]) -> tuple[int, int]:
    column = int(round((position[0] - grid.origin_x) / grid.dx))
    row = int(round((position[1] - grid.origin_y) / grid.dy))
    return max(0, min(grid.ny - 1, row)), max(0, min(grid.nx - 1, column))


def _clamped_station(package: CascadingScenarioPackage2_5D, station: float) -> float:
    grid = package.scenario.grid
    return max(grid.origin_x, min(grid.origin_x + grid.dx * (grid.nx - 1), station))


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
