"""Whitewater feature validation heuristics for 2.5D raft coupling."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .cascading import CascadingScenarioPackage2_5D, DropTransitionMetadata2_5D, ReachMetadata2_5D
from .math3d import Vec3
from .raft_coupling2_5d import (
    RaftMassProperties,
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    sample_grounding_forces,
    sample_total_raft_forces,
    sum_force_contributions,
)

CANONICAL_RUN_OUTCOMES = ("clear", "stalled", "surfed", "flushed", "grounded", "pinned", "flipped")
CASCADING_RAFT_VALIDATION_CASES = (
    "pool_entry",
    "drop_entry",
    "hydraulic_hole_surf_flush",
    "eddy_recovery",
    "boulder_garden_impacts",
    "transition_boundary_crossing",
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


@dataclass(frozen=True, slots=True)
class CascadingRaftValidationCase:
    case_id: str
    reach_id: str
    station: float
    lateral_offset: float
    state: RaftState6DoF
    expected_outcomes: tuple[str, ...]
    transition_id: str | None = None


@dataclass(frozen=True, slots=True)
class RunOutcomeSummary:
    counts: tuple[tuple[str, int], ...]
    total_runs: int
    passed_runs: int
    failed_runs: int

    @property
    def counts_by_outcome(self) -> dict[str, int]:
        return dict(self.counts)

    @property
    def dominant_outcome(self) -> str:
        if self.total_runs == 0:
            return "clear"
        return max(self.counts, key=lambda item: item[1])[0]

    def summary_lines(self) -> list[str]:
        counts = " ".join(f"{label}={count}" for label, count in self.counts)
        return [
            f"total={self.total_runs} passed={self.passed_runs} failed={self.failed_runs}",
            counts,
            f"dominant={self.dominant_outcome}",
        ]


def summarize_run_outcomes(results: Iterable[FeatureValidationResult | str]) -> RunOutcomeSummary:
    """Summarize feature or run outcomes into canonical raft outcome buckets."""

    counts = {label: 0 for label in CANONICAL_RUN_OUTCOMES}
    total_runs = 0
    passed_runs = 0
    failed_runs = 0
    for result in results:
        total_runs += 1
        if isinstance(result, FeatureValidationResult):
            outcome = result.outcome
            if result.passed:
                passed_runs += 1
            else:
                failed_runs += 1
        else:
            outcome = result
            passed_runs += 1
        counts[_canonical_run_outcome(outcome)] += 1
    return RunOutcomeSummary(
        counts=tuple((label, counts[label]) for label in CANONICAL_RUN_OUTCOMES),
        total_runs=total_runs,
        passed_runs=passed_runs,
        failed_runs=failed_runs,
    )


def build_cascading_raft_validation_cases(
    package: CascadingScenarioPackage2_5D,
    *,
    water: WaterField2_5D | None = None,
) -> tuple[CascadingRaftValidationCase, ...]:
    """Build deterministic raft validation states for a cascading pool/drop package."""

    water_field = water or WaterField2_5D.from_scenario_initial_state(package.scenario)
    pool = _first_reach_of_kind(package, "pool")
    drop = _first_reach_of_kind(package, "drop")
    eddy = _first_reach_of_kind(package, "eddy_recovery")
    transition = _first_drop_transition(package)
    hole = _first_feature_of_kind(package, "hole")
    eddy_line = _first_feature_of_kind(package, "eddy_line")
    rock = _middle_feature_of_kind(package, "rock")
    return (
        _case_at(
            "pool_entry",
            pool.reach_id,
            pool.station_start + pool.length * 0.22,
            0.0,
            water_field,
            expected_outcomes=("clear",),
            velocity_scale=0.65,
            z_offset=0.35,
        ),
        _case_at(
            "drop_entry",
            transition.downstream_reach_id or drop.reach_id,
            transition.crest_station,
            0.0,
            water_field,
            expected_outcomes=("flushed",),
            transition_id=transition.transition_id,
            velocity_scale=0.92,
            z_offset=0.32,
            vertical_velocity=-0.25,
        ),
        _case_at(
            "hydraulic_hole_surf_flush",
            _feature_reach_id(hole, drop.reach_id),
            hole.center[0],
            hole.center[1],
            water_field,
            expected_outcomes=("surfed", "flushed"),
            transition_id=transition.transition_id,
            velocity_scale=0.35,
            z_offset=0.34,
        ),
        _case_at(
            "eddy_recovery",
            _feature_reach_id(eddy_line, eddy.reach_id),
            eddy_line.center[0],
            eddy_line.center[1],
            water_field,
            expected_outcomes=("clear",),
            velocity_scale=0.85,
            z_offset=0.35,
        ),
        _case_at(
            "boulder_garden_impacts",
            _feature_reach_id(rock, "boulder_garden_001"),
            rock.center[0],
            rock.center[1],
            water_field,
            expected_outcomes=("grounded",),
            velocity_scale=1.2,
            z_offset=1.0,
            vertical_velocity=-0.7,
        ),
        _case_at(
            "transition_boundary_crossing",
            transition.downstream_reach_id,
            transition.crest_station + water_field.dx,
            0.0,
            water_field,
            expected_outcomes=("flushed",),
            transition_id=transition.transition_id,
            velocity_scale=0.95,
            z_offset=0.33,
            vertical_velocity=-0.2,
        ),
    )


def validate_cascading_raft_cases(
    package: CascadingScenarioPackage2_5D,
    *,
    water: WaterField2_5D | None = None,
    properties: RaftMassProperties | None = None,
) -> tuple[FeatureValidationResult, ...]:
    """Validate raft behavior across the canonical cascading pool/drop cases."""

    water_field = water or WaterField2_5D.from_scenario_initial_state(package.scenario)
    raft_properties = properties or build_default_raft_mass_properties(package.scenario.raft)
    cases = {case.case_id: case for case in build_cascading_raft_validation_cases(package, water=water_field)}
    return (
        _validate_pool_entry_case(package, water_field, raft_properties, cases["pool_entry"]),
        _validate_drop_entry_case(package, water_field, raft_properties, cases["drop_entry"]),
        _validate_hydraulic_hole_surf_flush_case(package, water_field, raft_properties, cases["hydraulic_hole_surf_flush"]),
        _validate_eddy_recovery_case(package, water_field, cases["eddy_recovery"]),
        _validate_boulder_garden_impacts_case(package, water_field, raft_properties, cases["boulder_garden_impacts"]),
        _validate_transition_boundary_crossing_case(package, water_field, cases["transition_boundary_crossing"]),
    )


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


def _validate_pool_entry_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    properties: RaftMassProperties,
    case: CascadingRaftValidationCase,
    *,
    min_depth: float = 0.8,
    max_lift_ratio: float = 5.0,
) -> FeatureValidationResult:
    pool = _reach_by_id(package, case.reach_id)
    tongue = _first_reach_of_kind(package, "tongue")
    sample = water.sample(case.state.position.x, case.state.position.y)
    tongue_sample = water.sample(tongue.station_start + tongue.length * 0.5, 0.0)
    total_force, _ = sum_force_contributions(sample_total_raft_forces(case.state, properties, water))
    lift_ratio = total_force.z / max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    speed = sample.velocity.magnitude
    tongue_speed = tongue_sample.velocity.magnitude
    checks = (
        _validation_check("pool_reach", pool.kind == "pool", 1.0 if pool.kind == "pool" else 0.0, 1.0),
        _validation_check("entry_depth", sample.depth >= min_depth, sample.depth, min_depth),
        _validation_check("pool_slower_than_tongue", speed < tongue_speed, speed, tongue_speed),
        _validation_check("bounded_lift", 0.0 <= lift_ratio <= max_lift_ratio, lift_ratio, max_lift_ratio),
    )
    return FeatureValidationResult(case.case_id, "clear" if all(check.passed for check in checks) else "stalled", checks)


def _validate_drop_entry_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    properties: RaftMassProperties,
    case: CascadingRaftValidationCase,
    *,
    min_drop_speed: float = 2.0,
    min_surface_fall: float = 0.15,
    min_tailwater_depth: float = 0.45,
) -> FeatureValidationResult:
    transition = _drop_transition_by_id(package, case.transition_id)
    sample = water.sample(case.state.position.x, case.state.position.y)
    upstream = water.sample(transition.crest_station - 2.0 * water.dx, case.state.position.y)
    downstream = water.sample(transition.crest_station + 5.0 * water.dx, case.state.position.y)
    total_force, _ = sum_force_contributions(sample_total_raft_forces(case.state, properties, water))
    lift_ratio = total_force.z / max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    surface_fall = upstream.surface_height - downstream.surface_height
    speed = sample.velocity.magnitude
    checks = (
        _validation_check(
            "drop_transition",
            transition.downstream_reach_id == case.reach_id,
            1.0 if transition.downstream_reach_id == case.reach_id else 0.0,
            1.0,
        ),
        _validation_check("ledge_tag", "ledge" in sample.feature_tags, 1.0 if "ledge" in sample.feature_tags else 0.0, 1.0),
        _validation_check("entry_speed", speed >= min_drop_speed, speed, min_drop_speed),
        _validation_check("surface_fall", surface_fall >= min_surface_fall, surface_fall, min_surface_fall),
        _validation_check("tailwater_depth", downstream.depth >= min_tailwater_depth, downstream.depth, min_tailwater_depth),
        _validation_check("bounded_entry_lift", 0.0 <= lift_ratio <= 8.0, lift_ratio, 8.0),
    )
    return FeatureValidationResult(case.case_id, "flushed" if all(check.passed for check in checks) else "stalled", checks)


def _validate_hydraulic_hole_surf_flush_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    properties: RaftMassProperties,
    case: CascadingRaftValidationCase,
    *,
    min_recirculation_risk: float = 0.45,
    flush_speed_threshold: float = 2.0,
    min_boil_lift_ratio: float = 0.5,
) -> FeatureValidationResult:
    transition = _drop_transition_by_id(package, case.transition_id)
    sample = water.sample(case.state.position.x, case.state.position.y)
    downstream_state = RaftState6DoF(
        position=case.state.position + Vec3(water.dx, 0.0, 0.0),
        orientation=case.state.orientation,
        linear_velocity=case.state.linear_velocity,
        angular_velocity=case.state.angular_velocity,
    )
    downstream_force, _ = sum_force_contributions(sample_total_raft_forces(downstream_state, properties, water))
    lift_ratio = downstream_force.z / max(properties.total_mass_kg * abs(properties.gravity.z), 1.0)
    speed = sample.velocity.magnitude
    damping_proxy = water.roughness + max(0.0, 1.0 - sample.normal.z) + 1.0 / (1.0 + speed)
    surf_or_flush_signal = max(speed / max(flush_speed_threshold, 1.0e-9), transition.recirculation_risk)
    outcome = "flushed" if speed >= flush_speed_threshold else "surfed"
    checks = (
        _validation_check("hole_tag", "hole" in sample.feature_tags, 1.0 if "hole" in sample.feature_tags else 0.0, 1.0),
        _validation_check(
            "recirculation_risk",
            transition.recirculation_risk >= min_recirculation_risk,
            transition.recirculation_risk,
            min_recirculation_risk,
        ),
        _validation_check("surf_or_flush_signal", surf_or_flush_signal >= 1.0, surf_or_flush_signal, 1.0),
        _validation_check("downstream_boil_lift", lift_ratio >= min_boil_lift_ratio, lift_ratio, min_boil_lift_ratio),
        _validation_check("aerated_damping", damping_proxy >= 0.25, damping_proxy, 0.25),
    )
    return FeatureValidationResult(case.case_id, outcome if all(check.passed for check in checks) else "stalled", checks)


def _validate_eddy_recovery_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    case: CascadingRaftValidationCase,
    *,
    min_speed_drop: float = 0.25,
    min_lateral_shear: float = 0.15,
) -> FeatureValidationResult:
    eddy = _reach_by_id(package, case.reach_id)
    wave = _first_reach_of_kind(package, "wave_train")
    eddy_sample = water.sample(case.state.position.x, case.state.position.y)
    centerline_sample = water.sample(case.state.position.x, 0.0)
    wave_sample = water.sample(wave.station_start + wave.length * 0.5, 0.0)
    speed_drop = wave_sample.velocity.magnitude - centerline_sample.velocity.magnitude
    lateral_shear = (eddy_sample.velocity - centerline_sample.velocity).magnitude
    checks = (
        _validation_check("eddy_recovery_reach", eddy.kind == "eddy_recovery", 1.0 if eddy.kind == "eddy_recovery" else 0.0, 1.0),
        _validation_check(
            "eddy_line_tag",
            "eddy_line" in eddy_sample.feature_tags,
            1.0 if "eddy_line" in eddy_sample.feature_tags else 0.0,
            1.0,
        ),
        _validation_check("speed_recovery", speed_drop >= min_speed_drop, speed_drop, min_speed_drop),
        _validation_check("lateral_shear", lateral_shear >= min_lateral_shear, lateral_shear, min_lateral_shear),
    )
    return FeatureValidationResult(case.case_id, "clear" if all(check.passed for check in checks) else "stalled", checks)


def _validate_boulder_garden_impacts_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    properties: RaftMassProperties,
    case: CascadingRaftValidationCase,
    *,
    min_rock_count: int = 3,
    min_scrape_acceleration: float = 0.2,
    min_launch_acceleration: float = 0.2,
) -> FeatureValidationResult:
    rock_features = tuple(feature for feature in package.scenario.features if feature.kind == "rock")
    sample = water.sample(case.state.position.x, case.state.position.y)
    grounding = sample_grounding_forces(case.state, properties, water)
    rock_contacts = tuple(
        contribution
        for contribution in grounding
        if "rock" in str((contribution.metadata or {}).get("feature_tags", ""))
    )
    grounding_force, grounding_torque = sum_force_contributions(grounding)
    travel = Vec3(case.state.linear_velocity.x, case.state.linear_velocity.y, 0.0)
    if travel.magnitude <= 1.0e-9:
        travel = Vec3(1.0, 0.0, 0.0)
    scrape_acceleration = max(0.0, -grounding_force.dot(travel.normalized()) / max(properties.total_mass_kg, 1.0e-9))
    launch_acceleration = max(0.0, grounding_force.z / max(properties.total_mass_kg, 1.0e-9) + properties.gravity.z)
    pitch_acceleration = abs(grounding_torque.y) / max(properties.inertia_diagonal_kg_m2.y, 1.0e-9)
    checks = (
        _validation_check("rock_feature_count", len(rock_features) >= min_rock_count, float(len(rock_features)), float(min_rock_count)),
        _validation_check("rock_tag", "rock" in sample.feature_tags, 1.0 if "rock" in sample.feature_tags else 0.0, 1.0),
        _validation_check("rock_contacts", bool(rock_contacts), float(len(rock_contacts)), 1.0),
        _validation_check("scrape_acceleration", scrape_acceleration >= min_scrape_acceleration, scrape_acceleration, min_scrape_acceleration),
        _validation_check("launch_acceleration", launch_acceleration >= min_launch_acceleration, launch_acceleration, min_launch_acceleration),
        _validation_check("pitch_impulse", pitch_acceleration >= 0.05, pitch_acceleration, 0.05),
    )
    return FeatureValidationResult(case.case_id, "grounded" if all(check.passed for check in checks) else "clear", checks)


def _validate_transition_boundary_crossing_case(
    package: CascadingScenarioPackage2_5D,
    water: WaterField2_5D,
    case: CascadingRaftValidationCase,
    *,
    min_crossing_speed: float = 2.0,
    min_surface_fall: float = 0.10,
) -> FeatureValidationResult:
    transition = _drop_transition_by_id(package, case.transition_id)
    upstream_reach = _reach_at_station(package, transition.crest_station - 2.0 * water.dx)
    downstream_reach = _reach_at_station(package, transition.crest_station + 2.0 * water.dx)
    upstream = water.sample(transition.crest_station - water.dx, case.state.position.y)
    downstream = water.sample(transition.crest_station + 2.0 * water.dx, case.state.position.y)
    sample = water.sample(case.state.position.x, case.state.position.y)
    transition_index = _drop_transition_index_at(package, transition.crest_station, case.state.position.y)
    surface_fall = upstream.surface_height - downstream.surface_height
    speed = sample.velocity.magnitude
    checks = (
        _validation_check(
            "upstream_reach_match",
            upstream_reach.reach_id == transition.upstream_reach_id,
            1.0 if upstream_reach.reach_id == transition.upstream_reach_id else 0.0,
            1.0,
        ),
        _validation_check(
            "downstream_reach_match",
            downstream_reach.reach_id == transition.downstream_reach_id,
            1.0 if downstream_reach.reach_id == transition.downstream_reach_id else 0.0,
            1.0,
        ),
        _validation_check("transition_grid_coverage", transition_index >= 0, float(transition_index), 0.0),
        _validation_check("crossing_speed", speed >= min_crossing_speed, speed, min_crossing_speed),
        _validation_check("crossing_surface_fall", surface_fall >= min_surface_fall, surface_fall, min_surface_fall),
    )
    return FeatureValidationResult(case.case_id, "flushed" if all(check.passed for check in checks) else "stalled", checks)


def _validation_check(
    name: str,
    passed: bool,
    value: float,
    threshold: float,
    details: str = "",
) -> FeatureValidationCheck:
    return FeatureValidationCheck(name, passed, value, threshold, details)


def _case_at(
    case_id: str,
    reach_id: str,
    station: float,
    lateral_offset: float,
    water: WaterField2_5D,
    *,
    expected_outcomes: tuple[str, ...],
    transition_id: str | None = None,
    velocity_scale: float = 1.0,
    z_offset: float = 0.35,
    vertical_velocity: float = 0.0,
) -> CascadingRaftValidationCase:
    sample = water.sample(station, lateral_offset)
    return CascadingRaftValidationCase(
        case_id=case_id,
        reach_id=reach_id,
        station=station,
        lateral_offset=lateral_offset,
        state=RaftState6DoF(
            position=Vec3(station, lateral_offset, sample.surface_height - z_offset),
            linear_velocity=Vec3(sample.velocity.x * velocity_scale, sample.velocity.y * velocity_scale, vertical_velocity),
        ),
        expected_outcomes=expected_outcomes,
        transition_id=transition_id,
    )


def _first_reach_of_kind(package: CascadingScenarioPackage2_5D, kind: str) -> ReachMetadata2_5D:
    for reach in package.reaches:
        if reach.kind == kind:
            return reach
    raise ValueError(f"Cascading package does not include a {kind!r} reach.")


def _reach_by_id(package: CascadingScenarioPackage2_5D, reach_id: str) -> ReachMetadata2_5D:
    for reach in package.reaches:
        if reach.reach_id == reach_id:
            return reach
    raise ValueError(f"Cascading package does not include reach {reach_id!r}.")


def _reach_at_station(package: CascadingScenarioPackage2_5D, station: float) -> ReachMetadata2_5D:
    for reach in package.reaches:
        if reach.station_start <= station < reach.station_end:
            return reach
    if package.reaches and abs(station - package.reaches[-1].station_end) <= 1.0e-9:
        return package.reaches[-1]
    raise ValueError(f"No cascading reach covers station {station:g}.")


def _first_drop_transition(package: CascadingScenarioPackage2_5D) -> DropTransitionMetadata2_5D:
    if not package.drop_transitions:
        raise ValueError("Cascading package does not include a drop transition.")
    return package.drop_transitions[0]


def _drop_transition_by_id(
    package: CascadingScenarioPackage2_5D,
    transition_id: str | None,
) -> DropTransitionMetadata2_5D:
    if transition_id is None:
        return _first_drop_transition(package)
    for transition in package.drop_transitions:
        if transition.transition_id == transition_id:
            return transition
    raise ValueError(f"Cascading package does not include drop transition {transition_id!r}.")


def _first_feature_of_kind(package: CascadingScenarioPackage2_5D, kind: str):
    for feature in package.scenario.features:
        if feature.kind == kind:
            return feature
    raise ValueError(f"Cascading package does not include a {kind!r} feature.")


def _middle_feature_of_kind(package: CascadingScenarioPackage2_5D, kind: str):
    features = tuple(feature for feature in package.scenario.features if feature.kind == kind)
    if not features:
        raise ValueError(f"Cascading package does not include a {kind!r} feature.")
    return features[len(features) // 2]


def _feature_reach_id(feature, fallback: str) -> str:
    metadata = getattr(feature, "metadata", {})
    if isinstance(metadata, dict):
        reach_id = metadata.get("reach_id")
        if isinstance(reach_id, str) and reach_id:
            return reach_id
    return fallback


def _drop_transition_index_at(package: CascadingScenarioPackage2_5D, station: float, lateral_offset: float) -> int:
    grid = package.drop_transition_id_grid
    if grid is None:
        return -1
    scenario = package.scenario
    col = int(round((station - scenario.grid.origin_x) / scenario.grid.dx))
    row = int(round((lateral_offset - scenario.grid.origin_y) / scenario.grid.dy))
    col = max(0, min(scenario.grid.nx - 1, col))
    row = max(0, min(scenario.grid.ny - 1, row))
    return int(grid[row, col])


def _canonical_run_outcome(outcome: str) -> str:
    normalized = outcome.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in CANONICAL_RUN_OUTCOMES:
        return normalized
    aliases = {
        "stall": "stalled",
        "surf": "surfed",
        "side_surf": "surfed",
        "flush": "flushed",
        "crossed": "flushed",
        "retentive_hole": "pinned",
        "pin": "pinned",
        "ground": "grounded",
        "pivoted": "grounded",
        "scraped": "grounded",
        "launched": "grounded",
        "flip": "flipped",
        "floating": "clear",
        "forced": "clear",
        "freefall": "clear",
        "eddy_coupled": "clear",
        "upwelling": "clear",
        "flat": "clear",
    }
    return aliases.get(normalized, "clear")


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
