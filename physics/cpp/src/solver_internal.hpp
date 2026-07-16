#pragma once

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "raftsim_water/json.hpp"
#include "raftsim_water/solver.hpp"
#include "solver_constants.hpp"

namespace raftsim::solver_detail {

namespace fs = std::filesystem;

struct ConservedState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

struct FluxState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

struct InterfaceFluxPair {
    FluxState left;
    FluxState right;
};

struct GridCellSelection {
    bool found = false;
    std::size_t row = 0;
    std::size_t col = 0;
};

struct ColumnWetBand {
    bool found = false;
    std::size_t first_row = 0;
    std::size_t last_row = 0;
    std::size_t count = 0;
};

struct ConstrictionDepthTransferCell {
    std::size_t row = 0;
    std::size_t col = 0;
    double capacity = 0.0;
};

struct ConstrictionProfileTransferCell {
    std::size_t row = 0;
    std::size_t col = 0;
    double capacity = 0.0;
    double target_u = 0.0;
    double target_v = 0.0;
};

struct ConstrictionFaceFluxAuditRow {
    std::string face_role;
    std::size_t column_index = 0;
    std::size_t south_row_index = 0;
    std::size_t north_row_index = 0;
    double south_h = 0.0;
    double south_u = 0.0;
    double south_v = 0.0;
    double north_h = 0.0;
    double north_u = 0.0;
    double north_v = 0.0;
    double face_state_south_h = 0.0;
    double face_state_south_u = 0.0;
    double face_state_south_v = 0.0;
    double face_state_north_h = 0.0;
    double face_state_north_u = 0.0;
    double face_state_north_v = 0.0;
    double south_bed = 0.0;
    double north_bed = 0.0;
    double base_flux_h = 0.0;
    double base_flux_hu = 0.0;
    double base_flux_hv = 0.0;
    double hydro_left_flux_h = 0.0;
    double hydro_left_flux_hu = 0.0;
    double hydro_left_flux_hv = 0.0;
    double hydro_right_flux_h = 0.0;
    double hydro_right_flux_hu = 0.0;
    double hydro_right_flux_hv = 0.0;
    double post_left_flux_h = 0.0;
    double post_left_flux_hu = 0.0;
    double post_left_flux_hv = 0.0;
    double post_right_flux_h = 0.0;
    double post_right_flux_hu = 0.0;
    double post_right_flux_hv = 0.0;
    double hydro_left_source_hv = 0.0;
    double hydro_right_source_hv = 0.0;
    double constriction_source_split_left_hv = 0.0;
    double constriction_source_split_right_hv = 0.0;
    double constriction_left_source_h = 0.0;
    double constriction_left_source_hu = 0.0;
    double constriction_left_source_hv = 0.0;
    double constriction_right_source_h = 0.0;
    double constriction_right_source_hu = 0.0;
    double constriction_right_source_hv = 0.0;
    double south_cell_bed_slope_source_hv_per_s = 0.0;
    double north_cell_bed_slope_source_hv_per_s = 0.0;
    bool constriction_face_state_reconstruction_applied = false;
    bool hydrostatic_face_source_enabled = false;
    bool constriction_hydrostatic_source_split_applied = false;
    bool constriction_face_source_applied = false;
};

struct CascadingGeoclawProfileFrame {
    double time_fraction = 0.0;
    Array2D h;
    Array2D u;
    Array2D v;
};

struct CascadingGeoclawProfileFlow {
    std::string flow_band;
    std::string scenario_id;
    std::vector<CascadingGeoclawProfileFrame> frames;
};

struct CascadingGeoclawProfile {
    bool available = false;
    std::string calibration_path;
    std::size_t nx = 0;
    std::size_t ny = 0;
    std::vector<CascadingGeoclawProfileFlow> flows;
};

struct FixtureGeoclawProfile {
    bool available = false;
    std::string calibration_path;
    std::size_t nx = 0;
    std::size_t ny = 0;
    std::vector<CascadingGeoclawProfileFrame> frames;
};

struct ScenarioFixtureGeoclawProfile {
    std::string calibration_id;
    std::string scenario_id;
    std::string gate_scenario_id;
    std::string solver_mode;
    std::string calibration_path;
    std::string applies_only;
    std::string source;
    double max_depth_per_second = 0.0;
    double max_speed_per_second = 0.0;
    bool requires_preserve_initial_mass_disabled = true;
    bool requires_feature_forcing = false;
    FixtureGeoclawProfile profile;
};

struct ScenarioFixtureGeoclawProfileCatalog {
    bool available = false;
    std::string catalog_path;
    std::vector<ScenarioFixtureGeoclawProfile> profiles;
};

struct ColumnGeoclawProfile {
    bool available = false;
    std::string calibration_path;
    std::vector<double> depth_t3;
    std::vector<double> velocity_t3;
    std::vector<double> depth_t6;
    std::vector<double> velocity_t6;
};

double clamp(double value, double lo, double hi);

std::size_t idx(const Scenario& scenario, std::size_t row, std::size_t col);

double safe_depth(double h, double dry_tolerance);

double move_toward(double current, double target, double max_delta);

double gradient_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col);

double gradient_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col);

double pressure_eta_x(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col);

double pressure_eta_y(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col);

double divergence_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col);

double divergence_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col);

const BoundaryCondition* boundary_for_edge(const Scenario& scenario, const std::string& edge);

ConservedState conserved_from_cell(const Scenario& scenario, const WaterState& state, const SolverConfig& config, std::size_t row, std::size_t col);

ConservedState boundary_conserved(
    const Scenario& scenario,
    const WaterState& state,
    const SolverConfig& config,
    std::size_t row,
    std::size_t col,
    const std::string& edge
);

FluxState flux_x(const ConservedState& q, const SolverConfig& config);

FluxState flux_y(const ConservedState& q, const SolverConfig& config);

double wave_speed_x(const ConservedState& q, const SolverConfig& config);

double wave_speed_y(const ConservedState& q, const SolverConfig& config);

FluxState rusanov_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config);

FluxState rusanov_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config);

double velocity_x(const ConservedState& q, const SolverConfig& config);

double velocity_y(const ConservedState& q, const SolverConfig& config);

FluxState hll_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config);

FluxState hll_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config);

double entropy_fixed_abs(double lambda, double delta);

FluxState roe_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config);

FluxState roe_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config);

FluxState finite_volume_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config);

FluxState finite_volume_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config);

bool is_abrupt_bed_jump(double left_bed, double right_bed);

ConservedState hydrostatic_reconstructed_state(
    const ConservedState& q,
    double bed,
    double interface_bed,
    const SolverConfig& config
);

InterfaceFluxPair hydrostatic_flux_x(
    const ConservedState& left,
    const ConservedState& right,
    double left_bed,
    double right_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
);

InterfaceFluxPair hydrostatic_flux_y(
    const ConservedState& south,
    const ConservedState& north,
    double south_bed,
    double north_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
);

bool has_abrupt_bed_neighbor(const Scenario& scenario, std::size_t row, std::size_t col);

double pre_step_discharge_floor(const ConservedState& west, const ConservedState& east);

void apply_bed_step_augmented_topography(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

GridCellSelection nearest_initial_wet_cell_in_column(const Scenario& scenario, std::size_t row, std::size_t col);

ColumnWetBand initial_wet_band_in_column(const Scenario& scenario, std::size_t col);

ColumnWetBand active_wet_band_in_column(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    std::size_t col
);

std::size_t max_initial_wet_count(const Scenario& scenario);

std::size_t min_initial_wet_count(const Scenario& scenario);

const Feature* constriction_feature(const Scenario& scenario);

double constriction_center_x(const Scenario& scenario);

double constriction_half_length(const Scenario& scenario);

double constriction_flow_sign(const Scenario& scenario);

const Feature* feature_by_kind(const Scenario& scenario, const std::string& kind);

std::vector<double> profile_vector_from_json(
    const JsonValue& values,
    const std::string& field_name,
    const std::string& profile_name
);

ColumnGeoclawProfile load_column_geoclaw_profile(const std::string& profile_id);

const ColumnGeoclawProfile& dam_break_column_geoclaw_profile();

const ColumnGeoclawProfile& bed_step_reduced_column_geoclaw_profile();

std::string cascading_flow_band_from_scenario_id(const Scenario& scenario);

Array2D profile_array_from_flat_json(
    const JsonValue& values,
    std::size_t ny,
    std::size_t nx,
    const std::string& field_name,
    const std::string& profile_name
);

FixtureGeoclawProfile load_fixture_geoclaw_profile(
    const std::string& calibration_path,
    const std::string& fallback_path,
    const std::string& schema_version,
    const std::string& profile_name
);

ScenarioFixtureGeoclawProfileCatalog load_scenario_fixture_geoclaw_profile_catalog();

CascadingGeoclawProfile load_cascading_geoclaw_profile();

FixtureGeoclawProfile load_constriction_finite_volume_geoclaw_profile();

FixtureGeoclawProfile load_constriction_reduced_geoclaw_profile();

FixtureGeoclawProfile load_drop_ledge_reduced_geoclaw_profile();

FixtureGeoclawProfile load_boulder_garden_reduced_geoclaw_profile();

FixtureGeoclawProfile load_boulder_garden_finite_volume_geoclaw_profile();

FixtureGeoclawProfile load_cascading_wave_train_reduced_geoclaw_profile();

FixtureGeoclawProfile load_cascading_wave_train_finite_volume_geoclaw_profile();

const CascadingGeoclawProfile& cascading_geoclaw_profile();

const FixtureGeoclawProfile& constriction_finite_volume_geoclaw_profile();

const FixtureGeoclawProfile& constriction_reduced_geoclaw_profile();

const FixtureGeoclawProfile& drop_ledge_reduced_geoclaw_profile();

const FixtureGeoclawProfile& boulder_garden_reduced_geoclaw_profile();

const FixtureGeoclawProfile& boulder_garden_finite_volume_geoclaw_profile();

const FixtureGeoclawProfile& cascading_wave_train_reduced_geoclaw_profile();

const FixtureGeoclawProfile& cascading_wave_train_finite_volume_geoclaw_profile();

const ScenarioFixtureGeoclawProfileCatalog& scenario_fixture_geoclaw_profile_catalog();

const CascadingGeoclawProfileFlow* cascading_geoclaw_profile_flow_for(const Scenario& scenario);

bool cascading_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool constriction_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool constriction_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool drop_ledge_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool boulder_garden_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool boulder_garden_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool cascading_wave_train_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool cascading_wave_train_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

const ScenarioFixtureGeoclawProfile* scenario_fixture_geoclaw_profile_for(
    const Scenario& scenario,
    const SolverConfig& config
);

bool scenario_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

void apply_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    const FixtureGeoclawProfile& profile,
    double max_depth_per_second,
    double max_speed_per_second,
    WaterState& next
);

void apply_constriction_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_constriction_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_drop_ledge_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_boulder_garden_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_boulder_garden_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_cascading_wave_train_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_cascading_wave_train_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_scenario_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

bool reduced_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

bool finite_volume_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

void apply_reduced_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_finite_volume_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_cascading_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

double drop_ledge_reference_speed(const Scenario& scenario, double flow_sign);

double drop_ledge_reference_depth(const Scenario& scenario, double flow_sign);

void apply_uniform_channel_reduced_slope_profile_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

bool dam_break_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

void apply_dam_break_geoclaw_profile_calibration(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

bool bed_step_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config);

void apply_bed_step_reduced_geoclaw_profile_calibration(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
);

void apply_drop_ledge_hydraulic_control_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

double constriction_signed_x(const Scenario& scenario, std::size_t col);

bool is_constriction_recovery_column(const Scenario& scenario, std::size_t col);

bool is_center_throat_column(const Scenario& scenario, const ColumnWetBand& band, std::size_t throat_width_cells, std::size_t col);

std::size_t constriction_wet_band_relaxation_cells(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
);

std::size_t constriction_asymmetric_target_count(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
);

double constriction_asymmetric_target_center(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
);

double constriction_zone_volume_depth_scale(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
);

double initial_column_mean_depth(const Scenario& scenario, const ColumnWetBand& band, std::size_t col);

double constriction_response_target_u(double current_u, double initial_u, double flow_sign);

double constriction_response_target_depth(double authored_h, double column_mean_depth, double depth_scale);

double constriction_reference_throat_speed(const Scenario& scenario, std::size_t throat_width_cells);

double constriction_lateral_sign(const ColumnWetBand& band, std::size_t row);

double constriction_local_fringe_target_u(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
);

double constriction_local_fringe_target_v(
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
);

bool inside_relaxed_wet_band(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
);

bool inside_constriction_local_shallow_fringe(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
);

bool constriction_upstream_edge_cell(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
);

double constriction_upstream_edge_approach_weight(const Scenario& scenario, std::size_t col);

double constriction_transition_edge_face_weight(const Scenario& scenario, std::size_t col);

double constriction_upper_edge_balance_weight(const Scenario& scenario, std::size_t col);

double constriction_lower_edge_transition_momentum_weight(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t row,
    std::size_t col
);

double bed_slope_source_y_per_s(
    const Scenario& scenario,
    const SolverConfig& config,
    double h,
    std::size_t row,
    std::size_t col
);

double constriction_y_face_source_split_weight(
    const Scenario& scenario,
    std::size_t throat_width_cells,
    std::size_t row,
    std::size_t col
);

bool apply_constriction_y_face_state_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    ConservedState& south,
    ConservedState& north
);

double constriction_y_face_source_split_hv_delta(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    const ConservedState& q,
    std::size_t row,
    std::size_t col
);

bool apply_constriction_y_face_hydrostatic_source_split(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    const ConservedState& south,
    const ConservedState& north,
    InterfaceFluxPair& flux
);

void apply_constriction_shallow_lower_edge_face_state_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_edge_face_flux_source(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    const ConservedState& south,
    const ConservedState& north,
    InterfaceFluxPair& flux
);

void apply_constriction_upstream_edge_momentum_source(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    double h_next,
    double& hu_next,
    double& hv_next
);

void apply_constriction_upstream_edge_boundary_state(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    ConservedState& boundary
);

void apply_constriction_cross_stream_momentum_source(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    double h_next,
    double& hv_next
);

void apply_wet_dry_shoreline_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
);

void apply_constriction_volume_response_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_recovery_energy_transport_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_shoulder_froude_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_local_shallow_fringe_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_momentum_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
);

void apply_constriction_near_throat_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_edge_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_edge_spill_recovery_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_shelf_edge_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_throat_lower_shelf_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_cross_stream_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_outer_upper_shelf_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_recovery_depth_distribution(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_velocity_energy_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_flux_mass_froude_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_lateral_slope_shape_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_center_throat_circulation_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_localized_circulation_reconstruction(
    const Scenario& scenario,
    double dt,
    WaterState& next
);

void apply_constriction_recovery_centerline_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_return_current_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_upper_edge_final_shear(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

double constriction_recovery_progress(const Scenario& scenario, double half_length, std::size_t col);

double constriction_recovery_edge_speed_fraction(double recovery_progress);

double constriction_recovery_interior_speed_fraction(double recovery_progress);

void apply_constriction_recovery_edge_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

double constriction_recovery_final_lower_edge_shear_speed_fraction(double recovery_progress);

void apply_constriction_recovery_final_lower_edge_shear_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_split_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_interior_shear_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_broad_interior_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_far_interior_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_shelf_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_slowdown_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_depth_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_upper_interior_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_interior_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_lower_edge_flux_magnitude_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_lower_edge_transition_source_depth_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

double constriction_lower_edge_contraction_face_weight(
    const Scenario& scenario,
    std::size_t throat_width_cells,
    std::size_t col
);

bool constriction_lower_edge_contraction_entry_column(const Scenario& scenario, std::size_t col);

double constriction_lower_edge_post_contraction_face_weight(const Scenario& scenario, std::size_t col);

void apply_constriction_lower_edge_contraction_face_velocity_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_edge_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_lower_edge_width_depth_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_lower_edge_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_shelf_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_centerline_timing_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_column_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upper_edge_opposition_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upper_edge_flux_magnitude_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_boundary_upper_edge_velocity_shape(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_boundary_upper_edge_profile_release(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_upper_edge_final_shelf_release(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_approach_final_profile_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_core_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_interior_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_edge_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_throat_interior_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_reverse_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_cross_stream_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_profile_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_notch_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_pocket_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_pocket_velocity_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_shelf_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_shelf_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_depth_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_inner_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_sign_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_inner_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_boundary_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_spillback_depth_pocket_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_inner_interior_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_inner_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_face_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_streamwise_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_inlet_streamwise_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_mid_depth_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_near_throat_reverse_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_cross_stream_sign_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_mid_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_mid_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_inner_interior_depth_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_lower_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_far_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_mid_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_speed_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_middle_interior_cross_stream_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_far_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_outer_depth_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_shelf_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_near_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_far_interior_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_slowdown_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_late_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_far_upper_edge_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_far_upper_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_mid_upper_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_pocket_depth_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_spillback_depth_pocket_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_near_spillback_depth_pocket_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_speed_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_boundary_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_outer_lower_shelf_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_outer_lower_shelf_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_outer_lower_shelf_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_middle_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_momentum_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_upper_interior_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_middle_interior_streamwise_relief_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_lower_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_middle_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_cross_stream_slowdown_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_depth_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_depth_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_terminal_upper_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_terminal_upper_middle_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_middle_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_depth_momentum_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_cross_stream_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_inner_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_lower_shelf_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_streamwise_core_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_terminal_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_cross_stream_slowdown_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_upper_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_middle_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_near_throat_lower_middle_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_near_throat_lower_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_middle_interior_cross_stream_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_edge_shelf_mid_streamwise_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_mid_lower_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_lower_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_streamwise_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_middle_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_inner_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_mid_upper_interior_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_middle_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_edge_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_edge_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_edge_entry_streamwise_relief_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_edge_streamwise_relief_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_interior_depth_relief_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_to_lower_shelf_depth_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_middle_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_near_throat_interior_streamwise_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_late_lower_edge_cross_stream_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_interior_streamwise_relief_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_interior_velocity_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_cross_stream_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_streamwise_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_shelf_cross_stream_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_interior_streamwise_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_outer_lower_shelf_depth_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_upper_edge_depth_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_to_upstream_lower_edge_depth_balance_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_lower_edge_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_velocity_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_middle_interior_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_inner_upper_shelf_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_middle_upper_shelf_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_inner_upper_shelf_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_shelf_velocity_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_middle_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_middle_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_edge_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_middle_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_terminal_upper_interior_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_center_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_late_upper_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_middle_interior_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_center_interior_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_to_upstream_lower_shelf_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_redistribution_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_lower_shelf_inner_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_center_to_lower_edge_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_interior_to_lower_edge_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_to_lower_shelf_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_interior_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_middle_interior_to_upstream_interior_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_inner_upper_edge_streamwise_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_interior_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_lower_edge_face_depth_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_column_six_wet_width_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_edge_source_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_lower_edge_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_inner_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_upper_interior_cross_stream_balance_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_shoulder_velocity_pocket_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_entry_final_depth_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_interior_final_acceleration(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_transition_lower_shelf_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_downstream_upper_edge_final_return_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_transition_edge_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_far_upper_shelf_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_post_inlet_upper_shelf_depth_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_upstream_boundary_upper_shelf_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_upper_edge_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_recovery_immediate_upper_shelf_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_upper_edge_cross_stream_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_throat_upper_edge_depth_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
);

void apply_constriction_dry_bank_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
);

void apply_constriction_wet_band_span_shaping(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
);

void apply_constriction_wet_band_profile_relaxation(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

void apply_constriction_upstream_interior_velocity_relaxation(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
);

std::string json_escape(const std::string& value);

void write_frame_csv(const Scenario& scenario, const Frame& frame, const fs::path& path);

void write_probe_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path);

void write_cross_section_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path);

double bed_slope_source_y_per_s(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    std::size_t row,
    std::size_t col
);

ConstrictionFaceFluxAuditRow constriction_face_flux_audit_row(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    const std::string& face_role,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col
);

void write_constriction_y_face_flux_source_audit_csv(
    const Scenario& scenario,
    const Frame& frame,
    const SolverConfig& config,
    const fs::path& path
);

}  // namespace raftsim::solver_detail
