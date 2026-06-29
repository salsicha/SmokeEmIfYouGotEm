"""Cascading 2.5D reach metadata for pool-and-drop river packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MetadataValue = str | int | float | bool | None

CASCADING_SCHEMA_VERSION = "raftsim.cascading2_5d.v0"
ReachKind2_5D = Literal["pool", "tongue", "drop", "wave_train", "eddy_recovery", "boulder_garden", "runout"]
BankShapeKind2_5D = Literal["trapezoid", "bedrock", "alluvial", "vegetated", "constructed", "unknown"]


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
