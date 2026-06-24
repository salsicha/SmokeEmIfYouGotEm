"""Procedural 2D river generation and query fields."""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Literal

from .math2d import Vec2, clamp, lerp, smoothstep

RiverFeatureKind = Literal[
    "rock",
    "eddy",
    "standing_wave",
    "wave_train",
    "hole",
    "lateral_wave",
    "boil",
    "hypoviscous",
    "shallow",
    "strainer",
]


@dataclass(frozen=True, slots=True)
class River2DParameters:
    """Seedable procedural river parameters."""

    seed: int = 1
    length: float = 240.0
    sample_count: int = 121
    average_width: float = 18.0
    width_variance: float = 5.0
    bend_amplitude: float = 18.0
    bend_frequency: float = 2.3
    gradient: float = 0.035
    water_volume: float = 1.0
    rock_density: float = 0.035
    feature_density: float = 0.025
    difficulty: float = 0.45
    safety_margin: float = 18.0

    def __post_init__(self) -> None:
        if self.length <= 0.0:
            raise ValueError("length must be positive.")
        if self.sample_count < 3:
            raise ValueError("sample_count must be at least 3.")
        if self.average_width <= 0.0:
            raise ValueError("average_width must be positive.")
        if self.safety_margin < 0.0:
            raise ValueError("safety_margin must be non-negative.")


@dataclass(frozen=True, slots=True)
class RiverFeature2D:
    kind: RiverFeatureKind
    position: Vec2
    radius: float
    strength: float = 1.0
    length: float = 0.0
    width: float = 0.0
    angle: float = 0.0
    metadata: dict[str, float | int | str] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "position": {"x": self.position.x, "y": self.position.y},
            "radius": self.radius,
            "strength": self.strength,
            "length": self.length,
            "width": self.width,
            "angle": self.angle,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class RiverCrossSection2D:
    s: float
    center: Vec2
    tangent: Vec2
    normal: Vec2
    width: float
    depth: float
    gradient: float
    base_speed: float

    @property
    def left_bank(self) -> Vec2:
        return self.center + self.normal * (self.width * 0.5)

    @property
    def right_bank(self) -> Vec2:
        return self.center - self.normal * (self.width * 0.5)


@dataclass(frozen=True, slots=True)
class RiverSample2D:
    position: Vec2
    center: Vec2
    tangent: Vec2
    normal: Vec2
    s: float
    n: float
    width: float
    depth: float
    inside_water: bool
    bank_distance: float
    current: Vec2
    shear: float
    damping: float
    turbulence: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    name: str
    passed: bool
    details: str = ""


@dataclass(frozen=True, slots=True)
class RiverValidation2D:
    checks: tuple[ValidationCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def summary_lines(self) -> list[str]:
        return [
            f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.details}"
            for check in self.checks
        ]


@dataclass(frozen=True, slots=True)
class GeneratedRiver2D:
    parameters: River2DParameters
    cross_sections: tuple[RiverCrossSection2D, ...]
    features: tuple[RiverFeature2D, ...]

    @property
    def length(self) -> float:
        return self.parameters.length

    @property
    def start_position(self) -> Vec2:
        first = self.cross_sections[0]
        return first.center

    @property
    def finish_position(self) -> Vec2:
        last = self.cross_sections[-1]
        return last.center

    @property
    def left_bank_points(self) -> tuple[Vec2, ...]:
        return tuple(section.left_bank for section in self.cross_sections)

    @property
    def right_bank_points(self) -> tuple[Vec2, ...]:
        return tuple(section.right_bank for section in self.cross_sections)

    def section_at_s(self, s: float) -> RiverCrossSection2D:
        clamped_s = clamp(s, 0.0, self.parameters.length)
        spacing = self.parameters.length / (len(self.cross_sections) - 1)
        lower_index = min(int(clamped_s / spacing), len(self.cross_sections) - 2)
        upper_index = lower_index + 1
        lower = self.cross_sections[lower_index]
        upper = self.cross_sections[upper_index]
        t = 0.0 if upper.s == lower.s else (clamped_s - lower.s) / (upper.s - lower.s)

        center = Vec2(lerp(lower.center.x, upper.center.x, t), lerp(lower.center.y, upper.center.y, t))
        tangent = (lower.tangent * (1.0 - t) + upper.tangent * t).safe_normalized()
        normal = tangent.perpendicular_left()
        return RiverCrossSection2D(
            s=clamped_s,
            center=center,
            tangent=tangent,
            normal=normal,
            width=lerp(lower.width, upper.width, t),
            depth=lerp(lower.depth, upper.depth, t),
            gradient=lerp(lower.gradient, upper.gradient, t),
            base_speed=lerp(lower.base_speed, upper.base_speed, t),
        )

    def sample(self, position: Vec2) -> RiverSample2D:
        section = self.section_at_s(position.x)
        offset = position - section.center
        n = offset.dot(section.normal)
        half_width = section.width * 0.5
        inside_water = abs(n) <= half_width
        bank_distance = max(0.0, abs(n) - half_width)

        lateral_fraction = clamp(abs(n) / max(half_width, 1.0e-6), 0.0, 1.5)
        bank_slowdown = clamp(1.0 - 0.55 * lateral_fraction * lateral_fraction, 0.15, 1.0)
        current = section.tangent * (section.base_speed * bank_slowdown)
        shear = 0.15 * section.base_speed * lateral_fraction
        damping = 1.0
        turbulence = 0.0
        tags: set[str] = set()

        for feature in self.features:
            delta = position - feature.position
            distance = delta.magnitude
            influence_radius = max(feature.radius, feature.width * 0.5, 1.0e-6)
            if distance > influence_radius:
                continue
            falloff = 1.0 - smoothstep(0.0, influence_radius, distance)
            direction = delta.safe_normalized(section.normal)

            if feature.kind == "eddy":
                tags.add("eddy")
                swirl = direction.perpendicular_left() * (feature.strength * falloff)
                reverse = -section.tangent * (0.45 * feature.strength * falloff)
                current += swirl + reverse
                turbulence += 0.25 * falloff
            elif feature.kind == "standing_wave":
                tags.add("standing_wave")
                current += -section.tangent * (0.35 * feature.strength * falloff)
                shear += 0.4 * feature.strength * falloff
                turbulence += 0.25 * falloff
            elif feature.kind == "wave_train":
                tags.add("wave_train")
                wave_phase = math.sin(max(0.0, position.x - feature.position.x) * 0.7)
                current += -section.tangent * (0.18 * feature.strength * falloff * abs(wave_phase))
                turbulence += 0.18 * falloff
            elif feature.kind == "hole":
                tags.add("hole")
                current += -section.tangent * (0.6 * feature.strength * falloff)
                current += -direction * (0.35 * feature.strength * falloff)
                turbulence += 0.5 * falloff
            elif feature.kind == "lateral_wave":
                tags.add("lateral_wave")
                lateral_direction = Vec2(math.cos(feature.angle), math.sin(feature.angle)).safe_normalized(section.normal)
                current += lateral_direction * (0.65 * feature.strength * falloff)
                turbulence += 0.2 * falloff
            elif feature.kind == "boil":
                tags.add("boil")
                current += direction * (0.35 * feature.strength * falloff)
                current += direction.perpendicular_left() * (0.25 * feature.strength * falloff)
                turbulence += 0.55 * falloff
            elif feature.kind == "hypoviscous":
                tags.add("hypoviscous")
                damping *= clamp(1.0 - 0.55 * feature.strength * falloff, 0.25, 1.0)
                turbulence += 0.25 * falloff
            elif feature.kind == "shallow":
                tags.add("shallow")
                damping *= 1.0 + 0.8 * feature.strength * falloff
                turbulence += 0.15 * falloff
            elif feature.kind == "strainer":
                tags.add("strainer")
                current += -direction * (0.2 * feature.strength * falloff)
            elif feature.kind == "rock":
                tags.add("rock_influence")
                upstream = (feature.position - position).dot(section.tangent)
                if upstream > 0.0:
                    current += -direction * (0.4 * feature.strength * falloff)

        if not inside_water:
            tags.add("bank")

        return RiverSample2D(
            position=position,
            center=section.center,
            tangent=section.tangent,
            normal=section.normal,
            s=section.s,
            n=n,
            width=section.width,
            depth=section.depth,
            inside_water=inside_water,
            bank_distance=bank_distance,
            current=current,
            shear=shear,
            damping=damping,
            turbulence=turbulence,
            tags=tuple(sorted(tags)),
        )

    def rocks(self) -> tuple[RiverFeature2D, ...]:
        return tuple(feature for feature in self.features if feature.kind == "rock")

    def validate(self) -> RiverValidation2D:
        checks: list[ValidationCheck] = []
        widths = [section.width for section in self.cross_sections]
        checks.append(
            ValidationCheck(
                "positive_widths",
                all(width > 2.0 for width in widths),
                f"min_width={min(widths):.3f}",
            )
        )

        monotonic = all(
            self.cross_sections[index + 1].s > self.cross_sections[index].s
            for index in range(len(self.cross_sections) - 1)
        )
        checks.append(ValidationCheck("monotonic_centerline", monotonic, f"samples={len(self.cross_sections)}"))

        centerline_clear = True
        minimum_clearance = float("inf")
        for feature in self.rocks():
            section = self.section_at_s(_feature_station(feature))
            clearance = abs((feature.position - section.center).dot(section.normal)) - feature.radius
            minimum_clearance = min(minimum_clearance, clearance)
            if clearance < 1.5:
                centerline_clear = False
        if minimum_clearance == float("inf"):
            minimum_clearance = 999.0
        checks.append(
            ValidationCheck(
                "centerline_route_clear",
                centerline_clear,
                f"minimum_centerline_clearance={minimum_clearance:.3f}",
            )
        )

        speeds = []
        for section in self.cross_sections[:: max(1, len(self.cross_sections) // 20)]:
            for lateral in (-0.3, 0.0, 0.3):
                sample = self.sample(section.center + section.normal * (section.width * lateral))
                speeds.append(sample.current.magnitude)
        max_speed = max(speeds) if speeds else 0.0
        checks.append(ValidationCheck("bounded_current_speed", max_speed < 12.0, f"max_speed={max_speed:.3f}"))

        checks.append(
            ValidationCheck(
                "feature_count",
                len(self.features) > 0,
                f"features={len(self.features)}",
            )
        )
        return RiverValidation2D(tuple(checks))

    def to_json_dict(self) -> dict[str, object]:
        return {
            "parameters": asdict(self.parameters),
            "cross_sections": [
                {
                    "s": section.s,
                    "center": {"x": section.center.x, "y": section.center.y},
                    "width": section.width,
                    "depth": section.depth,
                    "gradient": section.gradient,
                    "base_speed": section.base_speed,
                }
                for section in self.cross_sections
            ],
            "features": [feature.to_json_dict() for feature in self.features],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


def generate_river_2d(parameters: River2DParameters | None = None) -> GeneratedRiver2D:
    params = parameters or River2DParameters()
    rng = random.Random(params.seed)
    phase_a = rng.uniform(0.0, math.tau)
    phase_b = rng.uniform(0.0, math.tau)
    width_phase = rng.uniform(0.0, math.tau)
    cross_sections: list[RiverCrossSection2D] = []

    raw_centers: list[Vec2] = []
    for index in range(params.sample_count):
        t = index / (params.sample_count - 1)
        s = params.length * t
        bend = params.bend_amplitude * math.sin(params.bend_frequency * math.tau * t + phase_a)
        bend += params.bend_amplitude * 0.35 * math.sin(params.bend_frequency * 2.7 * math.tau * t + phase_b)
        raw_centers.append(Vec2(s, bend))

    for index, center in enumerate(raw_centers):
        if index == 0:
            tangent = (raw_centers[1] - center).safe_normalized()
        elif index == len(raw_centers) - 1:
            tangent = (center - raw_centers[index - 1]).safe_normalized()
        else:
            tangent = (raw_centers[index + 1] - raw_centers[index - 1]).safe_normalized()

        t = index / (params.sample_count - 1)
        width_wave = math.sin(2.1 * math.tau * t + width_phase)
        width_wave += 0.45 * math.sin(5.0 * math.tau * t + phase_b)
        width = max(6.0, params.average_width + params.width_variance * width_wave)
        depth = max(0.4, 1.1 + 0.6 * params.water_volume + 0.25 * math.sin(3.4 * math.tau * t + phase_a))
        local_gradient = max(0.002, params.gradient * (1.0 + 0.45 * math.sin(4.0 * math.tau * t + phase_b)))
        constriction = params.average_width / width
        base_speed = clamp(1.2 + 12.0 * local_gradient * params.water_volume * constriction, 0.35, 7.5)
        cross_sections.append(
            RiverCrossSection2D(
                s=center.x,
                center=center,
                tangent=tangent,
                normal=tangent.perpendicular_left(),
                width=width,
                depth=depth,
                gradient=local_gradient,
                base_speed=base_speed,
            )
        )

    features: list[RiverFeature2D] = []
    rock_count = max(1, int(params.length * params.rock_density * (0.65 + params.difficulty)))
    feature_count = max(2, int(params.length * params.feature_density * (0.8 + params.difficulty)))

    def random_section_position() -> tuple[RiverCrossSection2D, float]:
        s = rng.uniform(params.safety_margin, params.length - params.safety_margin)
        section = _section_at_s(cross_sections, s, params.length)
        lateral_limit = section.width * 0.32
        lateral = rng.uniform(-lateral_limit, lateral_limit)
        return section, lateral

    for feature_index in range(rock_count):
        section, lateral = random_section_position()
        radius = min(rng.uniform(0.8, 1.7 + 1.4 * params.difficulty), section.width * 0.25)
        clean_line_margin = radius + 2.0
        if abs(lateral) < clean_line_margin:
            lateral = clean_line_margin if lateral >= 0.0 else -clean_line_margin
        lateral = clamp(lateral, -section.width * 0.42, section.width * 0.42)
        position = section.center + section.normal * lateral
        strength = rng.uniform(0.7, 1.3) * (0.7 + params.difficulty)
        features.append(
            RiverFeature2D(
                kind="rock",
                position=position,
                radius=radius,
                strength=strength,
                metadata={"source_index": feature_index, "s": section.s},
            )
        )
        eddy_position = position + section.tangent * (radius * rng.uniform(2.0, 4.0))
        features.append(
            RiverFeature2D(
                kind="eddy",
                position=eddy_position,
                radius=radius * rng.uniform(2.4, 3.8),
                strength=strength * 0.75,
                metadata={"behind_rock": feature_index, "s": section.s},
            )
        )

    feature_kinds: tuple[RiverFeatureKind, ...] = (
        "standing_wave",
        "wave_train",
        "hole",
        "lateral_wave",
        "boil",
        "hypoviscous",
        "shallow",
        "strainer",
    )
    for feature_index in range(feature_count):
        section, lateral = random_section_position()
        kind = feature_kinds[feature_index % len(feature_kinds)]
        if kind in {"standing_wave", "wave_train", "hole"}:
            lateral *= 0.25
        position = section.center + section.normal * lateral
        radius = rng.uniform(section.width * 0.12, section.width * 0.32)
        strength = rng.uniform(0.45, 1.25) * (0.6 + params.difficulty)
        features.append(
            RiverFeature2D(
                kind=kind,
                position=position,
                radius=radius,
                strength=strength,
                length=radius * rng.uniform(1.0, 2.5),
                width=radius * rng.uniform(1.4, 2.8),
                angle=math.atan2(section.normal.y, section.normal.x) * rng.choice((-1, 1)),
                metadata={"source_index": feature_index, "s": section.s},
            )
        )

    return GeneratedRiver2D(params, tuple(cross_sections), tuple(features))


def _feature_station(feature: RiverFeature2D) -> float:
    value = feature.metadata.get("s", feature.position.x)
    try:
        return float(value)
    except (TypeError, ValueError):
        return feature.position.x


def _section_at_s(
    cross_sections: Iterable[RiverCrossSection2D],
    s: float,
    length: float,
) -> RiverCrossSection2D:
    sections = tuple(cross_sections)
    clamped_s = clamp(s, 0.0, length)
    spacing = length / (len(sections) - 1)
    lower_index = min(int(clamped_s / spacing), len(sections) - 2)
    upper_index = lower_index + 1
    lower = sections[lower_index]
    upper = sections[upper_index]
    t = 0.0 if upper.s == lower.s else (clamped_s - lower.s) / (upper.s - lower.s)
    center = Vec2(lerp(lower.center.x, upper.center.x, t), lerp(lower.center.y, upper.center.y, t))
    tangent = (lower.tangent * (1.0 - t) + upper.tangent * t).safe_normalized()
    return RiverCrossSection2D(
        s=clamped_s,
        center=center,
        tangent=tangent,
        normal=tangent.perpendicular_left(),
        width=lerp(lower.width, upper.width, t),
        depth=lerp(lower.depth, upper.depth, t),
        gradient=lerp(lower.gradient, upper.gradient, t),
        base_speed=lerp(lower.base_speed, upper.base_speed, t),
    )
