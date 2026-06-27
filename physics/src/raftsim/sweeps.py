"""Parameter sweep helpers for water-solver and raft-force coefficients."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .math3d import Vec3
from .raft_coupling2_5d import (
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    sample_buoyancy_forces,
    sample_grounding_forces,
    sample_hydrodynamic_forces,
    sum_force_contributions,
)
from .scenario2_5d import Feature2_5D, Scenario2_5D


@dataclass(frozen=True, slots=True)
class ParameterSweepCandidate:
    label: str
    roughness_scale: float = 1.0
    feature_strength_scale: float = 1.0
    raft_drag_scale: float = 1.0
    buoyancy_density_scale: float = 1.0
    grounding_friction_scale: float = 1.0
    contact_stiffness_scale: float = 1.0
    contact_damping_scale: float = 1.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name != "label" and value <= 0.0:
                raise ValueError(f"{name} must be positive.")

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ParameterSweepResult:
    candidate: ParameterSweepCandidate
    total_force: tuple[float, float, float]
    total_torque: tuple[float, float, float]
    contribution_count: int
    max_contribution_force: float

    def to_json_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.to_json_dict(),
            "total_force": list(self.total_force),
            "total_torque": list(self.total_torque),
            "contribution_count": self.contribution_count,
            "max_contribution_force": self.max_contribution_force,
        }


@dataclass(frozen=True, slots=True)
class ParameterSweepReport:
    scenario_id: str
    results: tuple[ParameterSweepResult, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "candidate_count": len(self.results),
            "results": [result.to_json_dict() for result in self.results],
        }

    def write_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path


def default_parameter_sweep_candidates(scale_values: tuple[float, ...] = (0.75, 1.0, 1.25)) -> tuple[ParameterSweepCandidate, ...]:
    """Return one-at-a-time coefficient sweeps around the baseline candidate."""

    if not scale_values:
        raise ValueError("scale_values must not be empty.")
    for value in scale_values:
        if value <= 0.0:
            raise ValueError("all scale values must be positive.")
    candidates = [ParameterSweepCandidate("baseline")]
    axes = (
        "roughness_scale",
        "feature_strength_scale",
        "raft_drag_scale",
        "buoyancy_density_scale",
        "grounding_friction_scale",
        "contact_stiffness_scale",
        "contact_damping_scale",
    )
    for axis in axes:
        for value in scale_values:
            if value == 1.0:
                continue
            label = f"{axis}_{value:g}".replace(".", "p")
            candidates.append(replace(ParameterSweepCandidate(label), **{axis: value}))
    return tuple(candidates)


def run_raft_force_parameter_sweep(
    scenario: Scenario2_5D,
    *,
    candidates: tuple[ParameterSweepCandidate, ...] | None = None,
    state: RaftState6DoF | None = None,
) -> ParameterSweepReport:
    """Evaluate raft-force response for a set of parameter sweep candidates."""

    selected = candidates if candidates is not None else default_parameter_sweep_candidates()
    if not selected:
        raise ValueError("At least one parameter sweep candidate is required.")
    baseline_water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    sweep_state = state or _default_sweep_state(scenario, baseline_water)
    results: list[ParameterSweepResult] = []
    for candidate in selected:
        water = _scaled_water_field(baseline_water, candidate)
        contributions = (
            *sample_buoyancy_forces(
                sweep_state,
                properties,
                water,
                water_density_kg_m3=1000.0 * candidate.buoyancy_density_scale,
            ),
            *sample_hydrodynamic_forces(
                sweep_state,
                properties,
                water,
                horizontal_drag_coefficient=1.25 * candidate.raft_drag_scale,
            ),
            *sample_grounding_forces(
                sweep_state,
                properties,
                water,
                contact_stiffness=12000.0 * candidate.contact_stiffness_scale,
                contact_damping=1200.0 * candidate.contact_damping_scale,
                grounding_friction=0.65 * candidate.grounding_friction_scale,
            ),
        )
        total_force, total_torque = sum_force_contributions(contributions)
        results.append(
            ParameterSweepResult(
                candidate=candidate,
                total_force=total_force.as_tuple(),
                total_torque=total_torque.as_tuple(),
                contribution_count=len(contributions),
                max_contribution_force=max((contribution.force.magnitude for contribution in contributions), default=0.0),
            )
        )
    return ParameterSweepReport(scenario.metadata.scenario_id, tuple(results))


def _scaled_water_field(water: WaterField2_5D, candidate: ParameterSweepCandidate) -> WaterField2_5D:
    return WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=water.eta,
        u=water.u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=water.normal_z,
        roughness=water.roughness * candidate.roughness_scale,
        features=tuple(_scale_feature(feature, candidate.feature_strength_scale) for feature in water.features),
    )


def _scale_feature(feature: Feature2_5D, scale: float) -> Feature2_5D:
    return Feature2_5D(
        kind=feature.kind,
        center=feature.center,
        radius=feature.radius,
        strength=feature.strength * scale,
        length=feature.length,
        width=feature.width,
        angle=feature.angle,
        metadata=feature.metadata,
    )


def _default_sweep_state(scenario: Scenario2_5D, water: WaterField2_5D) -> RaftState6DoF:
    center_x, center_y = scenario.grid.center
    surface = water.sample(center_x, center_y).surface_height
    return RaftState6DoF(
        position=Vec3(center_x, center_y, surface - 0.35),
        linear_velocity=Vec3(1.0, 0.0, -0.4),
    )
