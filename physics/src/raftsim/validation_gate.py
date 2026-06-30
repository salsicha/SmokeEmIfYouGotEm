"""Frozen validation matrix and thresholds for the custom C++ water engine."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

CUSTOM_CPP_VALIDATION_GATE_SCHEMA = "raftsim.custom_cpp_engine_validation_gate.v0"


@dataclass(frozen=True, slots=True)
class ValidationScenarioDefinition:
    """One required scenario family in the full C++ acceptance gate."""

    scenario_id: str
    suite: str
    source: str
    generator: str
    flow_band: str | None
    threshold_tier: str
    required_outputs: tuple[str, ...]
    geometry_focus: tuple[str, ...]
    raft_focus: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["required_outputs"] = list(self.required_outputs)
        data["geometry_focus"] = list(self.geometry_focus)
        data["raft_focus"] = list(self.raft_focus)
        return data


@dataclass(frozen=True, slots=True)
class ValidationThresholdTier:
    """Numerical pass/fail thresholds for one acceptance tier."""

    tier_id: str
    field_linf_max_m: float
    velocity_linf_max_mps: float
    wet_mismatch_max_fraction: float
    slope_linf_max: float
    probe_linf_max: float
    cross_section_linf_max: float
    mass_relative_drift_max: float
    energy_relative_change_delta_max: float
    froude_class_mismatch_max_fraction: float
    feature_location_max_m: float
    feature_strength_linf_max: float
    reach_flux_relative_delta_max: float
    raft_force_relative_linf_max: float
    raft_trajectory_delta_max_m: float
    runtime_budget_multiplier_max: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


FULL_GEOCLAW_OUTPUTS = (
    "geoclaw_run_manifest",
    "geoclaw_fixed_grid_frames",
    "geoclaw_normalized_manifest",
)
CPP_MODE_OUTPUTS = (
    "cpp_reduced_manifest",
    "cpp_finite_volume_manifest",
)
COMPARISON_OUTPUTS = (
    "field_comparison",
    "probe_comparison",
    "cross_section_comparison",
    "diagnostic_comparison",
    "threshold_evaluation",
)
RAFT_OUTPUTS = (
    "raft_force_comparison",
    "raft_outcome_comparison",
)
RUNTIME_OUTPUTS = (
    "cpp_profile",
    "deterministic_replay",
)

CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS: tuple[ValidationThresholdTier, ...] = (
    ValidationThresholdTier(
        tier_id="smoke",
        field_linf_max_m=1.5,
        velocity_linf_max_mps=2.5,
        wet_mismatch_max_fraction=0.35,
        slope_linf_max=0.25,
        probe_linf_max=1.5,
        cross_section_linf_max=1.5,
        mass_relative_drift_max=0.15,
        energy_relative_change_delta_max=0.5,
        froude_class_mismatch_max_fraction=0.35,
        feature_location_max_m=12.0,
        feature_strength_linf_max=2.0,
        reach_flux_relative_delta_max=0.25,
        raft_force_relative_linf_max=0.75,
        raft_trajectory_delta_max_m=8.0,
        runtime_budget_multiplier_max=2.0,
    ),
    ValidationThresholdTier(
        tier_id="research_accepted",
        field_linf_max_m=0.75,
        velocity_linf_max_mps=1.5,
        wet_mismatch_max_fraction=0.2,
        slope_linf_max=0.15,
        probe_linf_max=0.75,
        cross_section_linf_max=0.75,
        mass_relative_drift_max=0.08,
        energy_relative_change_delta_max=0.3,
        froude_class_mismatch_max_fraction=0.2,
        feature_location_max_m=6.0,
        feature_strength_linf_max=1.0,
        reach_flux_relative_delta_max=0.15,
        raft_force_relative_linf_max=0.45,
        raft_trajectory_delta_max_m=4.0,
        runtime_budget_multiplier_max=1.5,
    ),
    ValidationThresholdTier(
        tier_id="unreal_prototype",
        field_linf_max_m=0.35,
        velocity_linf_max_mps=0.8,
        wet_mismatch_max_fraction=0.1,
        slope_linf_max=0.08,
        probe_linf_max=0.35,
        cross_section_linf_max=0.35,
        mass_relative_drift_max=0.04,
        energy_relative_change_delta_max=0.15,
        froude_class_mismatch_max_fraction=0.1,
        feature_location_max_m=3.0,
        feature_strength_linf_max=0.55,
        reach_flux_relative_delta_max=0.08,
        raft_force_relative_linf_max=0.25,
        raft_trajectory_delta_max_m=2.0,
        runtime_budget_multiplier_max=1.0,
    ),
    ValidationThresholdTier(
        tier_id="production_candidate",
        field_linf_max_m=0.15,
        velocity_linf_max_mps=0.35,
        wet_mismatch_max_fraction=0.04,
        slope_linf_max=0.035,
        probe_linf_max=0.15,
        cross_section_linf_max=0.15,
        mass_relative_drift_max=0.02,
        energy_relative_change_delta_max=0.08,
        froude_class_mismatch_max_fraction=0.04,
        feature_location_max_m=1.25,
        feature_strength_linf_max=0.25,
        reach_flux_relative_delta_max=0.04,
        raft_force_relative_linf_max=0.12,
        raft_trajectory_delta_max_m=0.75,
        runtime_budget_multiplier_max=0.9,
    ),
)

CUSTOM_CPP_VALIDATION_SCENARIOS: tuple[ValidationScenarioDefinition, ...] = (
    ValidationScenarioDefinition(
        scenario_id="flat_pool",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="production_candidate",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("hydrostatic_balance", "mass_conservation", "flat_surface_normal"),
    ),
    ValidationScenarioDefinition(
        scenario_id="uniform_channel",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="production_candidate",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("steady_advection", "boundary_inflow_outflow", "momentum_conservation"),
    ),
    ValidationScenarioDefinition(
        scenario_id="dam_break",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("bore_speed", "wet_front", "hydraulic_jump"),
    ),
    ValidationScenarioDefinition(
        scenario_id="bed_step",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("bed_slope_source", "energy_change", "wet_dry_mask"),
    ),
    ValidationScenarioDefinition(
        scenario_id="constriction",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("lateral_acceleration", "froude_class", "cross_section_velocity"),
    ),
    ValidationScenarioDefinition(
        scenario_id="wet_dry_shoreline",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("shoreline_front", "dry_cell_stability", "bank_shelf_transition"),
    ),
    ValidationScenarioDefinition(
        scenario_id="sloping_manning_channel",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS,
        geometry_focus=("bed_slope_balance", "manning_friction", "steady_surface_gradient"),
    ),
    ValidationScenarioDefinition(
        scenario_id="drop_ledge",
        suite="canonical",
        source="fixture",
        generator="generate_fixture_scenario2_5d",
        flow_band=None,
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("ledge_energy_loss", "tailwater_depth", "hydraulic_control"),
        raft_focus=("drop_entry", "pool_entry"),
    ),
    ValidationScenarioDefinition(
        scenario_id="boulder_garden",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("rock_deflection", "local_wet_dry", "feature_strength"),
        raft_focus=("boulder_impacts", "scrape_launch"),
    ),
    ValidationScenarioDefinition(
        scenario_id="cascading_wave_train",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("wave_phase", "wave_amplitude", "froude_transition"),
        raft_focus=("standing_wave_clear", "stall_surf_flush"),
    ),
    ValidationScenarioDefinition(
        scenario_id="hydraulic_hole_downstream_boil",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("hole_retention", "boil_upwelling_proxy", "recirculation_zone"),
        raft_focus=("hole_surf", "hole_flush", "boil_recovery"),
    ),
    ValidationScenarioDefinition(
        scenario_id="lateral_wave",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("lateral_impulse", "bank_angle_response", "surface_slope"),
        raft_focus=("side_impulse", "roll_torque"),
    ),
    ValidationScenarioDefinition(
        scenario_id="eddy_line_shear",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("shear_location", "eddy_recirculation", "velocity_gradient"),
        raft_focus=("eddy_recovery", "yaw_impulse"),
    ),
    ValidationScenarioDefinition(
        scenario_id="shallow_shelf",
        suite="rafting",
        source="procedural_feature",
        generator="rafting_geoclaw_scenarios",
        flow_band=None,
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("shelf_wet_dry", "bed_contact_depth", "shoreline_stability"),
        raft_focus=("grounding", "pivot_release"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_low_runnable",
        suite="real_world",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_real_world_scenario2_5d",
        flow_band="low_runnable",
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("source_provenance", "flow_band_mapping", "low_water_shallows"),
        raft_focus=("shallow_shelf", "pool_entry"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_median_runnable",
        suite="real_world",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_real_world_scenario2_5d",
        flow_band="median_runnable",
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("source_provenance", "flow_band_mapping", "nominal_feature_strength"),
        raft_focus=("wave_train", "eddy_recovery"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_high_runnable",
        suite="real_world",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_real_world_scenario2_5d",
        flow_band="high_runnable",
        threshold_tier="research_accepted",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS,
        geometry_focus=("source_provenance", "flow_band_mapping", "high_water_boundary_flux"),
        raft_focus=("boulder_impacts", "transition_crossing"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_cascading_low_runnable",
        suite="cascading",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_south_fork_american_cascading_seed_scenarios",
        flow_band="low_runnable",
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS + RUNTIME_OUTPUTS,
        geometry_focus=("reach_handoff", "pool_depth", "drop_tailwater", "stitched_window_consistency"),
        raft_focus=("pool_entry", "transition_boundary_crossing"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_cascading_median_runnable",
        suite="cascading",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_south_fork_american_cascading_seed_scenarios",
        flow_band="median_runnable",
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS + RUNTIME_OUTPUTS,
        geometry_focus=("reach_handoff", "wave_train", "drop_energy_loss", "stitched_window_consistency"),
        raft_focus=("drop_entry", "hydraulic_hole_surf_flush"),
    ),
    ValidationScenarioDefinition(
        scenario_id="south_fork_cascading_high_runnable",
        suite="cascading",
        source="south_fork_american_chili_bar_to_coloma",
        generator="generate_south_fork_american_cascading_seed_scenarios",
        flow_band="high_runnable",
        threshold_tier="unreal_prototype",
        required_outputs=FULL_GEOCLAW_OUTPUTS + CPP_MODE_OUTPUTS + COMPARISON_OUTPUTS + RAFT_OUTPUTS + RUNTIME_OUTPUTS,
        geometry_focus=("reach_handoff", "tailwater_control", "high_flow_wet_front", "stitched_window_consistency"),
        raft_focus=("boulder_impacts", "pin_release", "transition_boundary_crossing"),
    ),
)


def custom_cpp_validation_gate_json() -> dict[str, object]:
    """Return the full frozen validation-gate definition as JSON-ready data."""

    return {
        "schema_version": CUSTOM_CPP_VALIDATION_GATE_SCHEMA,
        "reference_solver": "geoclaw",
        "candidate_solver": "raftsim_water_cpp_v1",
        "acceptance_rule": (
            "Live Unreal water remains blocked until each required scenario has full GeoClaw "
            "fixed-grid solution frames, C++ reduced and finite-volume outputs, comparison "
            "reports, raft-relevant checks where listed, and runtime evidence where listed."
        ),
        "threshold_tiers": [tier.to_json_dict() for tier in CUSTOM_CPP_VALIDATION_THRESHOLD_TIERS],
        "scenario_matrix": [scenario.to_json_dict() for scenario in CUSTOM_CPP_VALIDATION_SCENARIOS],
    }


def write_custom_cpp_validation_gate(path: str | Path) -> Path:
    """Write the frozen custom C++ validation gate definition to JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(custom_cpp_validation_gate_json(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path
