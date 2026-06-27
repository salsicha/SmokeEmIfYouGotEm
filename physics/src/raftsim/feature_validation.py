"""Whitewater feature validation heuristics for 2.5D raft coupling."""

from __future__ import annotations

from dataclasses import dataclass

from .math3d import Vec3
from .raft_coupling2_5d import (
    RaftMassProperties,
    RaftState6DoF,
    WaterField2_5D,
    sample_grounding_forces,
    sample_total_raft_forces,
    sum_force_contributions,
)


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


def validate_hole_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    depression_threshold: float = 0.08,
    retention_velocity_threshold: float = 0.15,
    damping_threshold: float = 0.25,
    boil_lift_threshold: float = 0.5,
) -> FeatureValidationResult:
    """Validate hole depression, retention, aerated damping, and boil/upwelling."""

    sample = water.sample(state.position.x, state.position.y)
    local_eta = sample.surface_height
    upstream = water.sample(state.position.x - water.dx, state.position.y)
    downstream_state = RaftState6DoF(
        position=state.position + Vec3(water.dx, 0.0, 0.0),
        orientation=state.orientation,
        linear_velocity=state.linear_velocity,
        angular_velocity=state.angular_velocity,
    )
    downstream_force, _ = sum_force_contributions(sample_total_raft_forces(downstream_state, properties, water))
    lift_ratio = downstream_force.z / max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    neighborhood = [
        water.sample(state.position.x + ox * water.dx, state.position.y + oy * water.dy).surface_height
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1))
    ]
    depression = max(neighborhood) - local_eta
    speed = sample.velocity.magnitude
    damping_proxy = water.roughness + max(0.0, 1.0 - sample.normal.z) + 1.0 / (1.0 + speed)
    retained = upstream.velocity.x <= retention_velocity_threshold
    checks = (
        FeatureValidationCheck("hole_tag", "hole" in sample.feature_tags, 1.0 if "hole" in sample.feature_tags else 0.0, 1.0),
        FeatureValidationCheck("depression", depression >= depression_threshold, depression, depression_threshold),
        FeatureValidationCheck(
            "upstream_retention",
            retained,
            upstream.velocity.x,
            retention_velocity_threshold,
            "Upstream hole velocity should be slow or reversing.",
        ),
        FeatureValidationCheck("aerated_damping", damping_proxy >= damping_threshold, damping_proxy, damping_threshold),
        FeatureValidationCheck("downstream_boil_lift", lift_ratio >= boil_lift_threshold, lift_ratio, boil_lift_threshold),
    )
    outcome = "retentive_hole" if all(check.passed for check in checks[1:]) else "flush"
    return FeatureValidationResult("hole", outcome, checks)


def validate_lateral_wave_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    cross_current_threshold: float = 0.25,
    side_acceleration_threshold: float = 0.12,
    roll_acceleration_threshold: float = 1.0,
) -> FeatureValidationResult:
    """Validate lateral-wave side impulse and roll-torque response."""

    sample = water.sample(state.position.x, state.position.y)
    left = water.sample(state.position.x, state.position.y - water.dy)
    right = water.sample(state.position.x, state.position.y + water.dy)
    total_force, total_torque = sum_force_contributions(sample_total_raft_forces(state, properties, water))
    cross_current = max(abs(sample.velocity.y), abs(left.velocity.y), abs(right.velocity.y))
    side_acceleration = abs(total_force.y) / max(properties.total_mass_kg, 1.0e-9)
    roll_acceleration = abs(total_torque.x) / max(properties.inertia_diagonal_kg_m2.x, 1.0e-9)
    checks = (
        FeatureValidationCheck(
            "lateral_tag",
            "lateral" in sample.feature_tags,
            1.0 if "lateral" in sample.feature_tags else 0.0,
            1.0,
        ),
        FeatureValidationCheck(
            "cross_current",
            cross_current >= cross_current_threshold,
            cross_current,
            cross_current_threshold,
            "Lateral wave should expose a meaningful cross-current.",
        ),
        FeatureValidationCheck(
            "side_impulse",
            side_acceleration >= side_acceleration_threshold,
            side_acceleration,
            side_acceleration_threshold,
            "Integrated raft forces should push the raft sideways.",
        ),
        FeatureValidationCheck(
            "roll_torque",
            roll_acceleration >= roll_acceleration_threshold,
            roll_acceleration,
            roll_acceleration_threshold,
            "Asymmetric water loading should create roll acceleration.",
        ),
    )
    outcome = "side_surf" if all(check.passed for check in checks[1:]) else "clear"
    return FeatureValidationResult("lateral_wave", outcome, checks)


def validate_eddy_line_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    shear_velocity_threshold: float = 0.6,
    yaw_acceleration_threshold: float = 0.4,
    roll_acceleration_threshold: float = 1.0,
) -> FeatureValidationResult:
    """Validate eddy-line shear, yaw torque, and coupled roll response."""

    sample = water.sample(state.position.x, state.position.y)
    left = water.sample(state.position.x, state.position.y - water.dy)
    right = water.sample(state.position.x, state.position.y + water.dy)
    total_force, total_torque = sum_force_contributions(sample_total_raft_forces(state, properties, water))
    shear_velocity = (left.velocity - right.velocity).magnitude
    yaw_acceleration = abs(total_torque.z) / max(properties.inertia_diagonal_kg_m2.z, 1.0e-9)
    roll_acceleration = abs(total_torque.x) / max(properties.inertia_diagonal_kg_m2.x, 1.0e-9)
    checks = (
        FeatureValidationCheck(
            "eddy_line_tag",
            "eddy_line" in sample.feature_tags,
            1.0 if "eddy_line" in sample.feature_tags else 0.0,
            1.0,
        ),
        FeatureValidationCheck(
            "shear_velocity",
            shear_velocity >= shear_velocity_threshold,
            shear_velocity,
            shear_velocity_threshold,
            "Current should change sharply across the raft width.",
        ),
        FeatureValidationCheck(
            "yaw_torque",
            yaw_acceleration >= yaw_acceleration_threshold,
            yaw_acceleration,
            yaw_acceleration_threshold,
            "Differential current should rotate the raft around vertical.",
        ),
        FeatureValidationCheck(
            "roll_coupling",
            roll_acceleration >= roll_acceleration_threshold,
            roll_acceleration,
            roll_acceleration_threshold,
            "Eddy-line crossing should also couple into roll.",
        ),
    )
    outcome = "eddy_coupled" if all(check.passed for check in checks[1:]) else "crossed"
    return FeatureValidationResult("eddy_line", outcome, checks)


def validate_shallow_shelf_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    shallow_depth_threshold: float = 0.35,
    grounding_support_threshold: float = 0.5,
    pivot_acceleration_threshold: float = 0.5,
) -> FeatureValidationResult:
    """Validate shallow-shelf grounding contact and pivot response."""

    contributions = sample_grounding_forces(state, properties, water)
    shallow_contacts = tuple(
        contribution
        for contribution in contributions
        if "shallow" in str((contribution.metadata or {}).get("feature_tags", ""))
    )
    grounding_force, grounding_torque = sum_force_contributions(contributions)
    weight = max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    support_ratio = grounding_force.z / weight
    pivot_acceleration = abs(grounding_torque.z) / max(properties.inertia_diagonal_kg_m2.z, 1.0e-9)
    shallow_depth = min(
        (water.sample(contact.application_point.x, contact.application_point.y).depth for contact in shallow_contacts),
        default=float("inf"),
    )
    checks = (
        FeatureValidationCheck(
            "shallow_contact",
            bool(shallow_contacts),
            float(len(shallow_contacts)),
            1.0,
            "Grounding contacts should include a shallow shelf tag.",
        ),
        FeatureValidationCheck(
            "shallow_depth",
            shallow_depth <= shallow_depth_threshold,
            shallow_depth,
            shallow_depth_threshold,
            "Shelf contact should occur in shallow water.",
        ),
        FeatureValidationCheck(
            "grounding_support",
            support_ratio >= grounding_support_threshold,
            support_ratio,
            grounding_support_threshold,
            "Grounding force should support a meaningful share of raft weight.",
        ),
        FeatureValidationCheck(
            "pivot_yaw",
            pivot_acceleration >= pivot_acceleration_threshold,
            pivot_acceleration,
            pivot_acceleration_threshold,
            "Off-center shelf contact should pivot the raft.",
        ),
    )
    outcome = "pivoted" if all(check.passed for check in checks[1:]) and shallow_contacts else "grounded"
    return FeatureValidationResult("shallow_shelf", outcome, checks)


def validate_submerged_rock_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    submerged_depth_threshold: float = 0.1,
    scrape_acceleration_threshold: float = 1.0,
    launch_acceleration_threshold: float = 1.0,
    pitch_acceleration_threshold: float = 0.3,
) -> FeatureValidationResult:
    """Validate submerged-rock scrape drag, upward launch, and pitch response."""

    contributions = sample_grounding_forces(state, properties, water)
    rock_contacts = tuple(
        contribution
        for contribution in contributions
        if "rock" in str((contribution.metadata or {}).get("feature_tags", ""))
    )
    grounding_force, grounding_torque = sum_force_contributions(contributions)
    travel = Vec3(state.linear_velocity.x, state.linear_velocity.y, 0.0)
    if travel.magnitude <= 1.0e-9:
        travel = Vec3(1.0, 0.0, 0.0)
    travel_direction = travel.normalized()
    scrape_acceleration = max(0.0, -grounding_force.dot(travel_direction) / max(properties.total_mass_kg, 1.0e-9))
    launch_acceleration = max(0.0, grounding_force.z / max(properties.total_mass_kg, 1.0e-9) + properties.gravity.z)
    pitch_acceleration = abs(grounding_torque.y) / max(properties.inertia_diagonal_kg_m2.y, 1.0e-9)
    submerged_depth = min(
        (water.sample(contact.application_point.x, contact.application_point.y).depth for contact in rock_contacts),
        default=0.0,
    )
    checks = (
        FeatureValidationCheck(
            "rock_contact",
            bool(rock_contacts),
            float(len(rock_contacts)),
            1.0,
            "Grounding contacts should include a submerged rock tag.",
        ),
        FeatureValidationCheck(
            "submerged_depth",
            submerged_depth >= submerged_depth_threshold,
            submerged_depth,
            submerged_depth_threshold,
            "Rock contact should happen below the water surface.",
        ),
        FeatureValidationCheck(
            "scrape_drag",
            scrape_acceleration >= scrape_acceleration_threshold,
            scrape_acceleration,
            scrape_acceleration_threshold,
            "Rock contact should scrape opposite raft travel.",
        ),
        FeatureValidationCheck(
            "launch_acceleration",
            launch_acceleration >= launch_acceleration_threshold,
            launch_acceleration,
            launch_acceleration_threshold,
            "Rock contact should kick the raft upward.",
        ),
        FeatureValidationCheck(
            "pitch_launch",
            pitch_acceleration >= pitch_acceleration_threshold,
            pitch_acceleration,
            pitch_acceleration_threshold,
            "Off-center rock contact should pitch the raft during launch.",
        ),
    )
    outcome = "launched" if all(check.passed for check in checks[1:]) and rock_contacts else "scraped"
    return FeatureValidationResult("submerged_rock", outcome, checks)


def validate_boil_upwelling_case(
    water: WaterField2_5D,
    state: RaftState6DoF,
    properties: RaftMassProperties,
    *,
    surface_dome_threshold: float = 0.03,
    vertical_acceleration_threshold: float = 2.0,
    deterministic_tolerance: float = 1.0e-9,
) -> FeatureValidationResult:
    """Validate deterministic boil/upwelling vertical impulse response."""

    sample = water.sample(state.position.x, state.position.y)
    neighbor_heights = [
        water.sample(state.position.x + ox * water.dx, state.position.y + oy * water.dy).surface_height
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1))
    ]
    surface_dome = sample.surface_height - min(neighbor_heights)
    first_force, first_torque = sum_force_contributions(sample_total_raft_forces(state, properties, water))
    second_force, second_torque = sum_force_contributions(sample_total_raft_forces(state, properties, water))
    vertical_acceleration = max(0.0, first_force.z / max(properties.total_mass_kg, 1.0e-9) + properties.gravity.z)
    deterministic_error = max((first_force - second_force).magnitude, (first_torque - second_torque).magnitude)
    checks = (
        FeatureValidationCheck(
            "boil_tag",
            "boil" in sample.feature_tags,
            1.0 if "boil" in sample.feature_tags else 0.0,
            1.0,
        ),
        FeatureValidationCheck(
            "surface_dome",
            surface_dome >= surface_dome_threshold,
            surface_dome,
            surface_dome_threshold,
            "Boil should form a measurable upwelling dome.",
        ),
        FeatureValidationCheck(
            "vertical_impulse",
            vertical_acceleration >= vertical_acceleration_threshold,
            vertical_acceleration,
            vertical_acceleration_threshold,
            "Boil should impart upward raft acceleration.",
        ),
        FeatureValidationCheck(
            "deterministic_repeat",
            deterministic_error <= deterministic_tolerance,
            deterministic_error,
            deterministic_tolerance,
            "Repeated force sampling should return identical boil impulses.",
        ),
    )
    outcome = "upwelling" if all(check.passed for check in checks[1:]) else "flat"
    return FeatureValidationResult("boil", outcome, checks)


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
