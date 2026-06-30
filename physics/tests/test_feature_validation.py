import numpy as np

from raftsim.feature_validation import (
    CASCADING_RAFT_VALIDATION_CASES,
    CascadingRaftValidationCase,
    FeatureValidationCheck,
    FeatureValidationResult,
    build_cascading_raft_validation_cases,
    validate_cascading_raft_cases,
    validate_boil_upwelling_case,
    validate_eddy_line_case,
    validate_hole_case,
    validate_lateral_wave_case,
    validate_shallow_shelf_case,
    validate_standing_wave_case,
    validate_submerged_rock_case,
    summarize_run_outcomes,
)
from raftsim.cascading import (
    CaliforniaPoolDropParameters2_5D,
    generate_california_pool_drop_cascading_scenario2_5d,
)
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties
from raftsim.scenario2_5d import Feature2_5D, FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


def test_standing_wave_validation_classifies_surf_case():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="uniform_channel", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    eta = water.eta + np.exp(-((np.arange(water.shape[1])[None, :] - 6.0) ** 2) / 8.0) * 0.2
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=water.u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=np.ones_like(water.normal_z),
        roughness=water.roughness,
        features=water.features,
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(6.0, 0.0, 0.8), linear_velocity=Vec3(float(water.u[4, 6]), 0.0, 0.0))

    result = validate_standing_wave_case(water, state, properties, crest_lift_threshold=0.01)

    assert result.feature == "standing_wave"
    assert result.outcome == "surf"
    assert result.passed


def test_hole_validation_detects_retention_and_boil_lift():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    eta = water.eta.copy()
    u = water.u.copy()
    normal_z = water.normal_z.copy()
    center = (6, 4)
    eta[center[1], center[0]] -= 0.2
    u[:, :] = 0.0
    normal_z[center[1], center[0]] = 0.82
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=normal_z,
        roughness=0.08,
        features=(Feature2_5D("hole", (6.0, water.origin_y + 4 * water.dy), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(6.0, water.origin_y + 4 * water.dy, 0.8))

    result = validate_hole_case(water, state, properties, boil_lift_threshold=0.1)

    assert result.feature == "hole"
    assert result.outcome == "retentive_hole"
    assert result.passed


def test_lateral_wave_validation_detects_side_impulse_and_roll_torque():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    v = water.v.copy()
    normal_y = water.normal_y.copy()
    normal_z = water.normal_z.copy()
    for row in range(water.shape[0]):
        y = water.origin_y + row * water.dy
        offset = (y - center_y) / max(water.dy, 1.0e-9)
        influence = np.exp(-(offset * offset) / 3.0)
        v[row, :] = 0.9 * influence
        eta[row, :] += 0.08 * offset * influence
        normal_y[row, :] = -0.12 * influence
        normal_z[row, :] = np.sqrt(np.maximum(1.0 - normal_y[row, :] ** 2, 0.01))
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=water.u,
        v=v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        roughness=water.roughness,
        features=(Feature2_5D("lateral", (center_x, center_y), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 0.8))

    result = validate_lateral_wave_case(water, state, properties)

    assert result.feature == "lateral_wave"
    assert result.outcome == "side_surf"
    assert result.passed


def test_eddy_line_validation_detects_yaw_and_roll_coupling():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    u = water.u.copy()
    normal_y = water.normal_y.copy()
    normal_z = water.normal_z.copy()
    for row in range(water.shape[0]):
        y = water.origin_y + row * water.dy
        side = np.tanh((center_y - y) / 0.55)
        u[row, :] = 0.35 + 0.75 * side
        eta[row, :] += 0.05 * side
        normal_y[row, :] = -0.10 * np.exp(-((y - center_y) ** 2) / 2.0)
        normal_z[row, :] = np.sqrt(np.maximum(1.0 - normal_y[row, :] ** 2, 0.01))
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        roughness=water.roughness,
        features=(Feature2_5D("eddy_line", (center_x, center_y), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 0.8))

    result = validate_eddy_line_case(water, state, properties)

    assert result.feature == "eddy_line"
    assert result.outcome == "eddy_coupled"
    assert result.passed


def test_shallow_shelf_validation_detects_grounding_and_pivot():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    depth = water.depth.copy()
    u = water.u.copy()
    shelf = Feature2_5D("shallow", (center_x + 1.2, center_y + 0.8), radius=2.3, strength=1.0)
    x = water.origin_x + np.arange(water.shape[1]) * water.dx
    y = water.origin_y + np.arange(water.shape[0]) * water.dy
    grid_x, grid_y = np.meshgrid(x, y)
    influence = np.exp(-(((grid_x - shelf.center[0]) / 2.0) ** 2 + ((grid_y - shelf.center[1]) / 1.4) ** 2))
    depth = np.where(influence > 0.25, 0.22, depth)
    u[:, :] = 0.4
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=eta - depth,
        depth=depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=water.normal_z,
        roughness=water.roughness,
        features=(shelf,),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 1.0), linear_velocity=Vec3(2.0, 0.0, -0.5))

    result = validate_shallow_shelf_case(water, state, properties)

    assert result.feature == "shallow_shelf"
    assert result.outcome == "pivoted"
    assert result.passed


def test_submerged_rock_validation_detects_scrape_and_launch():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    depth = water.depth.copy()
    u = water.u.copy()
    rock = Feature2_5D("rock", (center_x + 1.0, center_y), radius=1.8, strength=1.0)
    x = water.origin_x + np.arange(water.shape[1]) * water.dx
    y = water.origin_y + np.arange(water.shape[0]) * water.dy
    grid_x, grid_y = np.meshgrid(x, y)
    influence = np.exp(-(((grid_x - rock.center[0]) / 1.2) ** 2 + ((grid_y - rock.center[1]) / 1.0) ** 2))
    depth = np.where(influence > 0.25, 0.42, depth)
    u[:, :] = 0.5
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=eta - depth,
        depth=depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=water.normal_z,
        roughness=water.roughness,
        features=(rock,),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 0.75), linear_velocity=Vec3(3.0, 0.0, -0.7))

    result = validate_submerged_rock_case(water, state, properties)

    assert result.feature == "submerged_rock"
    assert result.outcome == "launched"
    assert result.passed


def test_boil_validation_detects_deterministic_upwelling_impulse():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    depth = water.depth.copy()
    u = water.u.copy()
    v = water.v.copy()
    normal_x = water.normal_x.copy()
    normal_y = water.normal_y.copy()
    boil = Feature2_5D("boil", (center_x, center_y), radius=2.2, strength=1.0)
    x = water.origin_x + np.arange(water.shape[1]) * water.dx
    y = water.origin_y + np.arange(water.shape[0]) * water.dy
    grid_x, grid_y = np.meshgrid(x, y)
    radius_squared = ((grid_x - center_x) / 1.5) ** 2 + ((grid_y - center_y) / 1.5) ** 2
    influence = np.exp(-radius_squared)
    eta += 0.24 * influence
    depth += 0.12 * influence
    u += 0.25 * ((grid_x - center_x) / 1.5) * influence
    v += 0.25 * ((grid_y - center_y) / 1.5) * influence
    normal_x = -0.16 * ((grid_x - center_x) / 1.5) * influence
    normal_y = -0.16 * ((grid_y - center_y) / 1.5) * influence
    normal_z = np.sqrt(np.maximum(1.0 - normal_x**2 - normal_y**2, 0.01))
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=eta - depth,
        depth=depth,
        eta=eta,
        u=u,
        v=v,
        wet=water.wet,
        normal_x=normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        roughness=water.roughness,
        features=(boil,),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 1.0), linear_velocity=Vec3(0.0, 0.0, -0.6))

    result = validate_boil_upwelling_case(water, state, properties)

    assert result.feature == "boil"
    assert result.outcome == "upwelling"
    assert result.passed


def test_run_outcome_summary_canonicalizes_validation_results():
    failed_grounding = FeatureValidationResult(
        "shallow_shelf",
        "pivoted",
        (FeatureValidationCheck("grounding_support", False, 0.1, 0.5),),
    )

    summary = summarize_run_outcomes(
        (
            FeatureValidationResult("standing_wave", "surf", ()),
            FeatureValidationResult("hole", "retentive_hole", ()),
            failed_grounding,
            "flush",
            "flipped",
            "clear",
        )
    )

    counts = summary.counts_by_outcome
    assert summary.total_runs == 6
    assert summary.passed_runs == 5
    assert summary.failed_runs == 1
    assert counts["clear"] == 1
    assert counts["surfed"] == 1
    assert counts["flushed"] == 1
    assert counts["grounded"] == 1
    assert counts["pinned"] == 1
    assert counts["flipped"] == 1
    assert summary.summary_lines()[0] == "total=6 passed=5 failed=1"


def test_cascading_raft_validation_cases_cover_pool_drop_eddy_boulder_and_boundaries():
    package = generate_california_pool_drop_cascading_scenario2_5d(
        CaliforniaPoolDropParameters2_5D(seed=7, nx=96, ny=34, difficulty=0.62, duration=3.0)
    )

    cases = build_cascading_raft_validation_cases(package)
    results = validate_cascading_raft_cases(package)
    by_case = {result.feature: result for result in results}

    assert all(isinstance(case, CascadingRaftValidationCase) for case in cases)
    assert tuple(case.case_id for case in cases) == CASCADING_RAFT_VALIDATION_CASES
    assert cases[0].reach_id == "pool_001"
    assert cases[1].transition_id == "ledge_drop_001"
    assert cases[-1].expected_outcomes == ("flushed",)
    assert tuple(by_case) == CASCADING_RAFT_VALIDATION_CASES
    assert all(result.passed for result in results)
    assert by_case["pool_entry"].outcome == "clear"
    assert by_case["drop_entry"].outcome == "flushed"
    assert by_case["hydraulic_hole_surf_flush"].outcome in {"surfed", "flushed"}
    assert by_case["eddy_recovery"].outcome == "clear"
    assert by_case["boulder_garden_impacts"].outcome == "grounded"
    assert by_case["transition_boundary_crossing"].outcome == "flushed"
    assert {check.name for check in by_case["hydraulic_hole_surf_flush"].checks} >= {
        "hole_tag",
        "surf_or_flush_signal",
        "downstream_boil_lift",
    }
    assert {check.name for check in by_case["boulder_garden_impacts"].checks} >= {
        "rock_feature_count",
        "rock_contacts",
        "scrape_acceleration",
    }
