import json
from pathlib import Path

from raftsim.geoclaw_reference import GEOCLAW_CANONICAL_FIXTURES, GEOCLAW_RAFTING_CASES
from raftsim.validation_gate import (
    CUSTOM_CPP_VALIDATION_GATE_SCHEMA,
    CUSTOM_CPP_VALIDATION_SCENARIOS,
    CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS,
    custom_cpp_validation_gate_json,
)


def test_custom_cpp_validation_gate_scenario_matrix_is_frozen():
    scenario_ids = {scenario.scenario_id for scenario in CUSTOM_CPP_VALIDATION_SCENARIOS}

    assert len(CUSTOM_CPP_VALIDATION_SCENARIOS) == 20
    assert set(GEOCLAW_CANONICAL_FIXTURES).issubset(scenario_ids)
    assert set(GEOCLAW_RAFTING_CASES).issubset(scenario_ids)
    assert {
        "south_fork_low_runnable",
        "south_fork_median_runnable",
        "south_fork_high_runnable",
        "south_fork_cascading_low_runnable",
        "south_fork_cascading_median_runnable",
        "south_fork_cascading_high_runnable",
    }.issubset(scenario_ids)

    for scenario in CUSTOM_CPP_VALIDATION_SCENARIOS:
        assert "geoclaw_fixed_grid_frames" in scenario.required_outputs
        assert "cpp_reduced_manifest" in scenario.required_outputs
        assert "cpp_finite_volume_manifest" in scenario.required_outputs
        assert "threshold_evaluation" in scenario.required_outputs
        assert scenario.threshold_tier in {tier.tier_id for tier in CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS}


def test_custom_cpp_validation_threshold_tiers_get_stricter():
    expected_order = ("smoke", "research_accepted", "unreal_prototype", "production_candidate")
    assert tuple(tier.tier_id for tier in CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS) == expected_order

    metric_names = [
        "field_linf_max_m",
        "velocity_linf_max_mps",
        "wet_mismatch_max_fraction",
        "slope_linf_max",
        "probe_linf_max",
        "cross_section_linf_max",
        "mass_relative_drift_max",
        "energy_relative_change_delta_max",
        "froude_class_mismatch_max_fraction",
        "feature_location_max_m",
        "feature_strength_linf_max",
        "reach_flux_relative_delta_max",
        "raft_force_relative_linf_max",
        "raft_trajectory_delta_max_m",
        "runtime_budget_multiplier_max",
    ]
    for metric_name in metric_names:
        values = [getattr(tier, metric_name) for tier in CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS]
        assert values == sorted(values, reverse=True), metric_name


def test_custom_cpp_validation_gate_config_matches_module():
    config_path = Path(__file__).resolve().parents[1] / "config" / "custom_cpp_validation_gate.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    assert payload == custom_cpp_validation_gate_json()
    assert payload["schema_version"] == CUSTOM_CPP_VALIDATION_GATE_SCHEMA
    assert payload["reference_solver"] == "geoclaw"
    assert payload["candidate_solver"] == "raftsim_water_cpp_v1"
