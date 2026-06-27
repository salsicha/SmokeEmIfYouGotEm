"""Whitewater feature validation heuristics for 2.5D raft coupling."""

from __future__ import annotations

from dataclasses import dataclass

from .raft_coupling2_5d import RaftMassProperties, RaftState6DoF, WaterField2_5D, sample_total_raft_forces, sum_force_contributions


@dataclass(frozen=True, slots=True)
class FeatureValidationCheck:
    name: str
    passed: bool
    value: float
    threshold: float
    details: str = ""


@dataclass(frozen=True, slots=True)
class FeatureValidationResult:
    feature: str
    outcome: str
    checks: tuple[FeatureValidationCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def validate_standing_wave_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    crest_lift_threshold: float = 0.05,
    surf_speed_threshold: float = 0.45,
    flush_speed_threshold: float = 1.25,
) -> FeatureValidationResult:
    """Validate clear/stall/surf/flush behavior over a standing-wave sample."""

    sample = water.sample(state.position.x, state.position.y)
    contributions = sample_total_raft_forces(state, properties, water)
    total_force, _ = sum_force_contributions(contributions)
    relative_downstream = state.linear_velocity.x - sample.velocity.x
    lift_ratio = total_force.z / max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    crest_lift = max(0.0, sample.normal.z - 0.95)
    outcome = _standing_wave_outcome(relative_downstream, lift_ratio, surf_speed_threshold, flush_speed_threshold)
    checks = (
        FeatureValidationCheck(
            "crest_lift",
            crest_lift >= crest_lift_threshold,
            crest_lift,
            crest_lift_threshold,
            "Surface normal should show a measurable crest face.",
        ),
        FeatureValidationCheck(
            "bounded_vertical_force",
            0.0 <= lift_ratio <= 6.0,
            lift_ratio,
            6.0,
            "Standing wave lift should remain finite and non-negative.",
        ),
        FeatureValidationCheck(
            "outcome_classified",
            outcome in {"clear", "stall", "surf", "flush"},
            1.0,
            1.0,
            "Outcome must be one of the standing-wave labels.",
        ),
    )
    return FeatureValidationResult("standing_wave", outcome, checks)


def _standing_wave_outcome(
    relative_downstream: float,
    lift_ratio: float,
    surf_speed_threshold: float,
    flush_speed_threshold: float,
) -> str:
    if relative_downstream > flush_speed_threshold:
        return "flush"
    if abs(relative_downstream) <= surf_speed_threshold and lift_ratio > 0.6:
        return "surf"
    if relative_downstream < -surf_speed_threshold:
        return "stall"
    return "clear"
