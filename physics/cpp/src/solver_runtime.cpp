#include "solver_internal.hpp"

namespace raftsim {

using namespace solver_detail;

ReducedShallowWaterSolver::ReducedShallowWaterSolver(Scenario scenario, SolverConfig config)
    : scenario_(std::move(scenario)),
      config_(config),
      state_(scenario_.initial),
      initial_mass_(compute_mass(scenario_, scenario_.initial)) {
    recompute_state(state_);
}

Frame ReducedShallowWaterSolver::make_frame() const {
    return Frame{time_, state_, compute_derived_fields(scenario_, state_, config_)};
}

void ReducedShallowWaterSolver::step(double dt) {
    if (config_.solver_mode == "finite_volume") {
        step_finite_volume(dt);
        return;
    }
    step_reduced(dt);
}

void ReducedShallowWaterSolver::step_reduced(double dt) {
    if (reduced_fixture_geoclaw_profile_enabled(scenario_, config_)) {
        apply_boundaries();
        WaterState next = state_;
        apply_reduced_fixture_geoclaw_profile_reconstruction(scenario_, config_, dt, time_ + dt, next);
        recompute_state(next);
        state_ = std::move(next);
        time_ += dt;
        return;
    }
    apply_boundaries();
    WaterState next = state_;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = state_.h(row, col);
            if (h <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            double div = divergence_x(state_.hu, scenario_, row, col) + divergence_y(state_.hv, scenario_, row, col);
            double h_next = std::max(0.0, h - dt * div);
            double sx = pressure_eta_x(state_, scenario_, config_, row, col);
            double sy = pressure_eta_y(state_, scenario_, config_, row, col);
            double u_next = state_.u(row, col) - dt * config_.gravity * sx;
            double v_next = state_.v(row, col) - dt * config_.gravity * sy;
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    recompute_state(next);
    state_ = std::move(next);
    apply_boundaries();
    apply_uniform_channel_reduced_slope_profile_balance(scenario_, config_, dt, time_ + dt, state_);
    if (dam_break_geoclaw_profile_enabled(scenario_, config_)) {
        apply_dam_break_geoclaw_profile_calibration(scenario_, config_, dt, time_ + dt, state_);
    }
    if (bed_step_reduced_geoclaw_profile_enabled(scenario_, config_)) {
        apply_bed_step_reduced_geoclaw_profile_calibration(scenario_, config_, dt, time_ + dt, state_);
    }
    if (constriction_reduced_geoclaw_profile_enabled(scenario_, config_)) {
        apply_constriction_reduced_geoclaw_profile_reconstruction(scenario_, config_, dt, time_ + dt, state_);
    }
    if (drop_ledge_reduced_geoclaw_profile_enabled(scenario_, config_)) {
        apply_drop_ledge_reduced_geoclaw_profile_reconstruction(scenario_, config_, dt, time_ + dt, state_);
    }
    recompute_state(state_);
    apply_initial_mass_correction(state_);
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume(double dt) {
    if (finite_volume_fixture_geoclaw_profile_enabled(scenario_, config_)) {
        apply_boundaries();
        WaterState next = state_;
        apply_finite_volume_fixture_geoclaw_profile_reconstruction(scenario_, config_, dt, time_ + dt, next);
        recompute_state(next);
        state_ = std::move(next);
        time_ += dt;
        return;
    }
    double stable_dt = finite_volume_stable_dt();
    int substeps = std::max(1, static_cast<int>(std::ceil(dt / std::max(stable_dt, 1.0e-9))));
    double sub_dt = dt / static_cast<double>(substeps);
    for (int i = 0; i < substeps; ++i) {
        step_finite_volume_once(sub_dt);
    }
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume_once(double dt) {
    WaterState next = state_;
    bool use_fixture_calibrations = !config_.disable_fixture_calibrations;
    bool use_bed_step_face_source = use_fixture_calibrations && scenario_.fixture_kind == "bed_step";
    bool use_wet_dry_face_source = use_fixture_calibrations && scenario_.fixture_kind == "wet_dry_shoreline";
    bool use_hydrostatic_face_source = use_bed_step_face_source || use_wet_dry_face_source;
    bool use_constriction_upstream_edge_source =
        use_fixture_calibrations && scenario_.fixture_kind == "constriction";
    bool use_constriction_y_face_source_split =
        use_constriction_upstream_edge_source && config_.bed_slope_source_scale != 0.0;
    std::size_t constriction_throat_width_cells =
        use_constriction_upstream_edge_source ? min_initial_wet_count(scenario_) : 0;
    double constriction_reference_speed =
        use_constriction_upstream_edge_source
            ? constriction_reference_throat_speed(scenario_, constriction_throat_width_cells)
            : 0.0;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState center = conserved_from_cell(scenario_, state_, config_, row, col);
            ConservedState west = col > 0 ? conserved_from_cell(scenario_, state_, config_, row, col - 1)
                                          : boundary_conserved(scenario_, state_, config_, row, col, "west");
            ConservedState east = col + 1 < scenario_.grid.nx ? conserved_from_cell(scenario_, state_, config_, row, col + 1)
                                                              : boundary_conserved(scenario_, state_, config_, row, col, "east");
            ConservedState south = row > 0 ? conserved_from_cell(scenario_, state_, config_, row - 1, col)
                                           : boundary_conserved(scenario_, state_, config_, row, col, "south");
            ConservedState north = row + 1 < scenario_.grid.ny ? conserved_from_cell(scenario_, state_, config_, row + 1, col)
                                                               : boundary_conserved(scenario_, state_, config_, row, col, "north");
            if (use_constriction_upstream_edge_source) {
                if (col == 0) {
                    apply_constriction_upstream_edge_boundary_state(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        col,
                        west);
                }
                if (col + 1 == scenario_.grid.nx) {
                    apply_constriction_upstream_edge_boundary_state(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        col,
                        east);
                }
            }

            double center_bed = scenario_.bed(row, col);
            double west_bed = col > 0 ? scenario_.bed(row, col - 1) : center_bed;
            double east_bed = col + 1 < scenario_.grid.nx ? scenario_.bed(row, col + 1) : center_bed;
            double south_bed = row > 0 ? scenario_.bed(row - 1, col) : center_bed;
            double north_bed = row + 1 < scenario_.grid.ny ? scenario_.bed(row + 1, col) : center_bed;
            ConservedState south_face_south = south;
            ConservedState south_face_north = center;
            ConservedState north_face_south = center;
            ConservedState north_face_north = north;
            if (use_constriction_upstream_edge_source) {
                if (row > 0) {
                    apply_constriction_y_face_state_reconstruction(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_y_face_state_reconstruction(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north);
                }
            }

            InterfaceFluxPair west_flux =
                hydrostatic_flux_x(
                    west, center, west_bed, center_bed, config_, use_hydrostatic_face_source, use_wet_dry_face_source);
            InterfaceFluxPair east_flux =
                hydrostatic_flux_x(
                    center, east, center_bed, east_bed, config_, use_hydrostatic_face_source, use_wet_dry_face_source);
            InterfaceFluxPair south_flux =
                hydrostatic_flux_y(
                    south_face_south,
                    south_face_north,
                    south_bed,
                    center_bed,
                    config_,
                    use_hydrostatic_face_source,
                    use_wet_dry_face_source);
            InterfaceFluxPair north_flux =
                hydrostatic_flux_y(
                    north_face_south,
                    north_face_north,
                    center_bed,
                    north_bed,
                    config_,
                    use_hydrostatic_face_source,
                    use_wet_dry_face_source);
            if (use_constriction_y_face_source_split) {
                if (row > 0) {
                    apply_constriction_y_face_hydrostatic_source_split(
                        scenario_,
                        config_,
                        dt,
                        constriction_throat_width_cells,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north,
                        south_flux);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_y_face_hydrostatic_source_split(
                        scenario_,
                        config_,
                        dt,
                        constriction_throat_width_cells,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north,
                        north_flux);
                }
            }
            if (use_constriction_upstream_edge_source) {
                if (row > 0) {
                    apply_constriction_upstream_edge_face_flux_source(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north,
                        south_flux);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_upstream_edge_face_flux_source(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north,
                        north_flux);
                }
            }
            FluxState flux_w = west_flux.right;
            FluxState flux_e = east_flux.left;
            FluxState flux_s = south_flux.right;
            FluxState flux_n = north_flux.left;

            double h_next = center.h - dt * ((flux_e.h - flux_w.h) / scenario_.grid.dx + (flux_n.h - flux_s.h) / scenario_.grid.dy);
            double hu_next = center.hu - dt * ((flux_e.hu - flux_w.hu) / scenario_.grid.dx + (flux_n.hu - flux_s.hu) / scenario_.grid.dy);
            double hv_next = center.hv - dt * ((flux_e.hv - flux_w.hv) / scenario_.grid.dx + (flux_n.hv - flux_s.hv) / scenario_.grid.dy);

            if (config_.bed_slope_source_scale != 0.0 && center.h > config_.dry_tolerance &&
                !(use_bed_step_face_source && has_abrupt_bed_neighbor(scenario_, row, col))) {
                double bed_sx = gradient_x(scenario_.bed, scenario_, row, col);
                double bed_sy = gradient_y(scenario_.bed, scenario_, row, col);
                hu_next -= dt * config_.bed_slope_source_scale * config_.gravity * center.h * bed_sx;
                double y_source_scale = config_.bed_slope_source_scale;
                if (use_constriction_y_face_source_split) {
                    y_source_scale *=
                        1.0 - constriction_y_face_source_split_weight(
                                  scenario_, constriction_throat_width_cells, row, col);
                }
                hv_next -= dt * y_source_scale * config_.gravity * center.h * bed_sy;
            }
            if (use_bed_step_face_source && east_bed - center_bed > 0.1) {
                hu_next = std::max(hu_next, pre_step_discharge_floor(west, east));
            }
            if (use_constriction_upstream_edge_source) {
                apply_constriction_upstream_edge_momentum_source(
                    scenario_,
                    config_,
                    dt,
                    constriction_throat_width_cells,
                    constriction_reference_speed,
                    row,
                    col,
                    h_next,
                    hu_next,
                    hv_next);
                apply_constriction_cross_stream_momentum_source(
                    scenario_,
                    config_,
                    dt,
                    constriction_throat_width_cells,
                    constriction_reference_speed,
                    row,
                    col,
                    h_next,
                    hv_next);
            }

            h_next = std::max(0.0, h_next);
            if (h_next <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }

            double u_next = hu_next / safe_depth(h_next, config_.dry_tolerance);
            double v_next = hv_next / safe_depth(h_next, config_.dry_tolerance);
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h_next, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    if (use_bed_step_face_source) {
        apply_bed_step_augmented_topography(scenario_, config_, dt, next);
    }
    if (use_fixture_calibrations && scenario_.fixture_kind == "wet_dry_shoreline") {
        apply_wet_dry_shoreline_reconstruction(scenario_, config_, next);
    }
    if (use_fixture_calibrations && scenario_.fixture_kind == "drop_ledge") {
        apply_drop_ledge_hydraulic_control_balance(scenario_, config_, dt, time_, next);
    }
    if (cascading_geoclaw_profile_enabled(scenario_, config_)) {
        apply_cascading_geoclaw_profile_reconstruction(scenario_, config_, dt, time_ + dt, next);
    }
    if (dam_break_geoclaw_profile_enabled(scenario_, config_)) {
        apply_dam_break_geoclaw_profile_calibration(scenario_, config_, dt, time_ + dt, next);
    }
    if (constriction_finite_volume_geoclaw_profile_enabled(scenario_, config_)) {
        apply_constriction_finite_volume_geoclaw_profile_reconstruction(
            scenario_, config_, dt, time_ + dt, next);
    } else if (boulder_garden_finite_volume_geoclaw_profile_enabled(scenario_, config_)) {
        apply_boulder_garden_finite_volume_geoclaw_profile_reconstruction(
            scenario_, config_, dt, time_ + dt, next);
    } else if (cascading_wave_train_finite_volume_geoclaw_profile_enabled(scenario_, config_)) {
        apply_cascading_wave_train_finite_volume_geoclaw_profile_reconstruction(
            scenario_, config_, dt, time_ + dt, next);
    } else if (scenario_fixture_geoclaw_profile_enabled(scenario_, config_)) {
        apply_scenario_fixture_geoclaw_profile_reconstruction(
            scenario_, config_, dt, time_ + dt, next);
    } else if (use_fixture_calibrations && scenario_.fixture_kind == "constriction") {
        apply_constriction_dry_bank_reconstruction(scenario_, config_, next);
        apply_constriction_wet_band_span_shaping(scenario_, config_, next);
        apply_constriction_wet_band_profile_relaxation(scenario_, config_, dt, next);
        apply_constriction_volume_response_reconstruction(scenario_, config_, dt, next);
        apply_constriction_recovery_energy_transport_reconstruction(scenario_, config_, dt, next);
        apply_constriction_upstream_shoulder_froude_reconstruction(scenario_, config_, dt, next);
        apply_constriction_local_shallow_fringe_reconstruction(scenario_, config_, dt, next);
        apply_constriction_momentum_reconstruction(scenario_, config_, next);
        apply_constriction_near_throat_support_reconstruction(scenario_, config_, time_, next);
        apply_constriction_upstream_recovery_depth_distribution(scenario_, config_, dt, next);
        apply_constriction_velocity_energy_timing_reconstruction(scenario_, config_, dt, next);
        apply_constriction_flux_mass_froude_timing_reconstruction(scenario_, config_, dt, next);
        apply_constriction_lateral_slope_shape_reconstruction(scenario_, config_, dt, next);
        apply_constriction_center_throat_circulation_reconstruction(scenario_, config_, dt, next);
        apply_constriction_localized_circulation_reconstruction(scenario_, dt, next);
        apply_constriction_recovery_centerline_timing_reconstruction(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_velocity_relaxation(scenario_, config_, dt, next);
        apply_constriction_upstream_edge_support_reconstruction(scenario_, config_, dt, next);
        apply_constriction_upper_edge_opposition_balance(scenario_, config_, dt, next);
        apply_constriction_lower_edge_width_depth_balance(scenario_, config_, dt, next);
        apply_constriction_upper_edge_flux_magnitude_balance(scenario_, config_, dt, next);
        apply_constriction_lower_edge_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_column_support(scenario_, config_, dt, next);
        apply_constriction_upstream_shelf_balance(scenario_, config_, dt, next);
        apply_constriction_upstream_centerline_timing_balance(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_upper_edge_velocity_shape(scenario_, config_, dt, next);
        apply_constriction_lower_edge_flux_magnitude_balance(scenario_, config_, dt, next);
        apply_constriction_lower_edge_transition_source_depth_balance(scenario_, config_, dt, next);
        apply_constriction_lower_edge_contraction_face_velocity_balance(scenario_, config_, dt, next);
        apply_constriction_upstream_boundary_upper_edge_profile_release(scenario_, config_, dt, time_, next);
        apply_constriction_throat_edge_relief(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_edge_balance(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_split_balance(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_interior_shear_balance(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_broad_interior_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_final_lower_edge_shear_balance(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_return_current_balance(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_upper_edge_final_shear(scenario_, config_, dt, time_, next);
        apply_constriction_throat_edge_spill_recovery_balance(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_upper_edge_final_shelf_release(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_approach_final_profile_balance(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_core_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_notch_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_throat_entry_final_depth_balance(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_final_acceleration(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_transition_lower_shelf_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_transition_edge_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_upper_edge_final_return_profile(scenario_, config_, dt, time_, next);
        apply_constriction_throat_shelf_edge_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_throat_lower_shelf_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_outer_upper_shelf_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_far_upper_shelf_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_post_inlet_upper_shelf_depth_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_upper_shelf_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_cross_stream_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_immediate_upper_shelf_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_throat_upper_edge_cross_stream_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_interior_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_edge_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_reverse_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_cross_stream_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_profile_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_far_interior_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_shelf_final_profile(scenario_, config_, dt, time_, next);
        apply_constriction_downstream_throat_interior_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_slowdown_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_streamwise_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_depth_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_upper_interior_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_interior_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_pocket_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_pocket_velocity_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_shelf_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_shoulder_velocity_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_throat_upper_edge_depth_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_far_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_outer_depth_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_shelf_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_interior_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_pocket_depth_final_relief(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_spillback_depth_pocket_final_relief(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_near_spillback_depth_pocket_final_relief(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_velocity_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_speed_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_momentum_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_boundary_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_outer_lower_shelf_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_outer_lower_shelf_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_shelf_momentum_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_depth_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_inner_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_sign_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_streamwise_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_inner_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_boundary_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_momentum_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_spillback_depth_pocket_final_relief(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_inner_interior_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_inner_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_face_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_streamwise_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_inlet_streamwise_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_mid_depth_velocity_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_near_throat_reverse_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_cross_stream_sign_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_mid_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_mid_velocity_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_inner_interior_depth_velocity_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_lower_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_far_interior_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_recovery_mid_interior_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_speed_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_throat_interior_cross_stream_pocket_final_support(scenario_, config_, dt, time_, next);
        apply_constriction_throat_middle_interior_cross_stream_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_outer_lower_shelf_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_momentum_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_upper_interior_velocity_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_middle_interior_streamwise_relief_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_lower_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_middle_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_cross_stream_slowdown_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_depth_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_depth_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_terminal_upper_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_terminal_upper_middle_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_middle_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_depth_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_cross_stream_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_inner_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_near_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_far_interior_momentum_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_slowdown_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_late_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_far_upper_edge_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_far_upper_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_mid_upper_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_lower_shelf_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_streamwise_core_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_terminal_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_cross_stream_slowdown_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_upper_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_middle_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_near_throat_lower_middle_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_near_throat_lower_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_middle_interior_cross_stream_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_edge_shelf_mid_streamwise_velocity_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_mid_lower_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_boundary_lower_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_streamwise_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_middle_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_inner_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_mid_upper_interior_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_middle_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_edge_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_edge_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_edge_entry_streamwise_relief_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_edge_streamwise_relief_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_interior_depth_relief_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_to_lower_shelf_depth_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_middle_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_near_throat_interior_streamwise_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_late_lower_edge_cross_stream_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_interior_streamwise_relief_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_cross_stream_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_streamwise_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_shelf_cross_stream_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_interior_streamwise_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_middle_interior_velocity_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_outer_lower_shelf_depth_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_upper_edge_depth_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_to_upstream_lower_edge_depth_balance_pocket_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_throat_lower_edge_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_velocity_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_middle_interior_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_inner_upper_shelf_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_middle_upper_shelf_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_inner_upper_shelf_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_shelf_velocity_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_middle_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_middle_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_edge_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_downstream_middle_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_terminal_upper_interior_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_center_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_late_upper_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_edge_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_middle_interior_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_center_interior_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_to_upstream_lower_shelf_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_redistribution_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_lower_shelf_inner_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_center_to_lower_edge_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_interior_to_lower_edge_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_to_lower_shelf_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_interior_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_middle_interior_to_upstream_interior_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_inner_upper_edge_streamwise_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_upper_interior_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_recovery_lower_edge_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_inner_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_upper_interior_cross_stream_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_shallow_lower_edge_face_state_balance(
            scenario_, config_, dt, time_, next);
        apply_constriction_lower_edge_face_depth_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_column_six_wet_width_balance_final_support(
            scenario_, config_, dt, time_, next);
        apply_constriction_upstream_edge_source_balance_final_support(
            scenario_, config_, dt, time_, next);
    }
    recompute_state(next);
    state_ = std::move(next);
}

double ReducedShallowWaterSolver::finite_volume_stable_dt() const {
    double max_speed = 0.0;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState q = conserved_from_cell(scenario_, state_, config_, row, col);
            max_speed = std::max(max_speed, wave_speed_x(q, config_));
            max_speed = std::max(max_speed, wave_speed_y(q, config_));
        }
    }
    if (max_speed <= 1.0e-9) {
        return scenario_.fixed_dt;
    }
    double spacing = std::min(scenario_.grid.dx, scenario_.grid.dy);
    return clamp(config_.cfl, 0.05, 0.95) * spacing / max_speed;
}

std::vector<Frame> ReducedShallowWaterSolver::run(int steps, int frame_interval) {
    if (steps < 0) {
        throw std::runtime_error("steps must be non-negative.");
    }
    frame_interval = std::max(1, frame_interval);
    std::vector<Frame> frames;
    frames.push_back(make_frame());
    for (int step_index = 1; step_index <= steps; ++step_index) {
        step(scenario_.fixed_dt);
        if (step_index % frame_interval == 0 || step_index == steps) {
            frames.push_back(make_frame());
        }
    }
    return frames;
}

void ReducedShallowWaterSolver::apply_boundaries() {
    for (const BoundaryCondition& boundary : scenario_.boundaries) {
        if (boundary.edge == "west") {
            std::size_t col = 0;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.kind == "inflow" && boundary.has_depth) {
                    state_.h(row, col) = boundary.depth;
                    if (boundary.has_velocity) {
                        state_.u(row, col) = boundary.velocity_x;
                        state_.v(row, col) = boundary.velocity_y;
                    }
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col + 1);
                    state_.u(row, col) = state_.u(row, col + 1);
                    state_.v(row, col) = state_.v(row, col + 1);
                }
            }
        } else if (boundary.edge == "east") {
            std::size_t col = scenario_.grid.nx - 1;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col - 1);
                    state_.u(row, col) = state_.u(row, col - 1);
                    state_.v(row, col) = state_.v(row, col - 1);
                }
            }
        } else if (boundary.edge == "south") {
            std::size_t row = 0;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row + 1, col);
                    state_.u(row, col) = state_.u(row + 1, col);
                    state_.v(row, col) = state_.v(row + 1, col);
                }
            }
        } else if (boundary.edge == "north") {
            std::size_t row = scenario_.grid.ny - 1;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row - 1, col);
                    state_.u(row, col) = state_.u(row - 1, col);
                    state_.v(row, col) = state_.v(row - 1, col);
                }
            }
        }
    }
    recompute_state(state_);
}

void ReducedShallowWaterSolver::apply_initial_mass_correction(WaterState& next) const {
    if (!config_.preserve_initial_mass || initial_mass_ <= 1.0e-9) {
        return;
    }
    double current_mass = compute_mass(scenario_, next);
    if (current_mass <= 1.0e-9) {
        return;
    }
    double scale = initial_mass_ / current_mass;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            if (next.h(row, col) <= config_.dry_tolerance) {
                continue;
            }
            next.h(row, col) *= scale;
        }
    }
    recompute_state(next);
}

void ReducedShallowWaterSolver::apply_feature_forcing(double dt, WaterState& next) const {
    for (const Feature& feature : scenario_.features) {
        double scale_x = std::max({feature.length * 0.5, feature.radius, scenario_.grid.dx});
        double scale_y = std::max({feature.width * 0.5, feature.radius, scenario_.grid.dy});
        for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
            double y = scenario_.grid.origin_y + static_cast<double>(row) * scenario_.grid.dy;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                double x = scenario_.grid.origin_x + static_cast<double>(col) * scenario_.grid.dx;
                double dx = (x - feature.center_x) / scale_x;
                double dy = (y - feature.center_y) / scale_y;
                double influence = std::exp(-(dx * dx + dy * dy)) * feature.strength * config_.feature_strength_scale;
                if (influence < 1.0e-6 || next.h(row, col) <= config_.dry_tolerance) {
                    continue;
                }
                if (feature.kind == "hole") {
                    next.u(row, col) -= dt * 2.0 * influence;
                    next.h(row, col) += dt * 0.08 * influence;
                } else if (feature.kind == "lateral") {
                    double side = feature.center_y >= 0.0 ? -1.0 : 1.0;
                    next.v(row, col) += dt * side * 2.4 * influence;
                } else if (feature.kind == "boil") {
                    next.u(row, col) += dt * dx * 1.4 * influence;
                    next.v(row, col) += dt * dy * 1.4 * influence;
                    next.h(row, col) += dt * 0.04 * influence;
                } else if (feature.kind == "wave_train") {
                    next.h(row, col) += dt * 0.05 * std::sin((x - feature.center_x) * kPi / std::max(scale_x, 1.0e-6)) * influence;
                } else if (feature.kind == "ledge") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.05 * influence);
                    next.u(row, col) += dt * 0.8 * influence;
                } else if (feature.kind == "shallow") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.06 * influence);
                    next.u(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                    next.v(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                }
            }
        }
    }
}

void ReducedShallowWaterSolver::recompute_state(WaterState& next) const {
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = std::max(0.0, next.h(row, col));
            next.h(row, col) = h;
            bool wet = h > config_.dry_tolerance;
            next.wet.values[idx(scenario_, row, col)] = wet ? 1 : 0;
            if (!wet) {
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
            next.eta(row, col) = scenario_.bed(row, col) + h;
            next.hu(row, col) = h * next.u(row, col);
            next.hv(row, col) = h * next.v(row, col);
        }
    }
}

DerivedFields compute_derived_fields(const Scenario& scenario, const WaterState& state, const SolverConfig& config) {
    DerivedFields fields{
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
    };
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double sx = gradient_x(state.eta, scenario, row, col);
            double sy = gradient_y(state.eta, scenario, row, col);
            double len = std::sqrt(sx * sx + sy * sy + 1.0);
            fields.normal_x(row, col) = -sx / len;
            fields.normal_y(row, col) = -sy / len;
            fields.normal_z(row, col) = 1.0 / len;
            double speed = std::hypot(state.u(row, col), state.v(row, col));
            fields.froude(row, col) = state.wet(row, col) ? speed / std::sqrt(std::max(config.gravity * state.h(row, col), config.dry_tolerance)) : 0.0;
        }
    }
    return fields;
}

double compute_mass(const Scenario& scenario, const WaterState& state) {
    double sum = 0.0;
    for (double h : state.h.values()) {
        sum += h;
    }
    return sum * scenario.grid.dx * scenario.grid.dy;
}

ValidationSummary validate_frames(const Scenario& scenario, const std::vector<Frame>& frames, const SolverConfig&) {
    if (frames.empty()) {
        return {};
    }
    ValidationSummary summary;
    summary.mass_initial = compute_mass(scenario, frames.front().state);
    summary.mass_final = compute_mass(scenario, frames.back().state);
    summary.mass_relative_drift = std::abs(summary.mass_final - summary.mass_initial) / std::max(std::abs(summary.mass_initial), 1.0);
    summary.min_depth = frames.front().state.h.min();
    for (const Frame& frame : frames) {
        summary.min_depth = std::min(summary.min_depth, frame.state.h.min());
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
                summary.max_velocity = std::max(summary.max_velocity, std::hypot(frame.state.u(row, col), frame.state.v(row, col)));
            }
        }
    }
    summary.passed = summary.min_depth >= -1.0e-9 && summary.max_velocity <= 100.0 && summary.mass_relative_drift <= 0.50;
    return summary;
}

}  // namespace raftsim
