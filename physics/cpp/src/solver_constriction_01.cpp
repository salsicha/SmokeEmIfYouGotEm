#include "solver_internal.hpp"

namespace raftsim::solver_detail {

double constriction_signed_x(const Scenario& scenario, std::size_t col) {
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    return (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
}

bool is_constriction_recovery_column(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    return constriction_signed_x(scenario, col) > half_length;
}

bool is_center_throat_column(const Scenario& scenario, const ColumnWetBand& band, std::size_t throat_width_cells, std::size_t col) {
    if (!band.found || band.count != throat_width_cells) {
        return false;
    }
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    return std::abs(x - constriction_center_x(scenario)) <= 0.5 * scenario.grid.dx;
}

std::size_t constriction_wet_band_relaxation_cells(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found || is_center_throat_column(scenario, band, throat_width_cells, col)) {
        return 0;
    }
    return band.count == throat_width_cells ? 1 : kConstrictionWetBandRelaxationCells;
}

std::size_t constriction_asymmetric_target_count(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found) {
        return 0;
    }

    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    double signed_x = (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);

    std::size_t target = band.count;
    if (band.count == throat_width_cells) {
        target = throat_width_cells + 1;
    } else if (signed_x < -half_length) {
        target = band.count + 2;
    } else if (signed_x < 0.0) {
        target = band.count + 1;
    } else if (signed_x <= half_length) {
        target = band.count > 1 ? band.count - 1 : 1;
        target = std::max(target, throat_width_cells + 1);
    } else if (signed_x <= half_length + 2.0 * scenario.grid.dx) {
        target = band.count <= throat_width_cells + 2 ? band.count : band.count - 1;
    } else {
        target = band.count + 1;
    }
    return std::min(scenario.grid.ny, std::max<std::size_t>(1, target));
}

double constriction_asymmetric_target_center(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    double initial_center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    double signed_x = (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);

    if (band.count == throat_width_cells) {
        return initial_center - 0.5;
    }
    if (signed_x < -half_length) {
        return initial_center - 0.5;
    }
    if (signed_x < 0.0) {
        return initial_center + 0.5;
    }
    if (signed_x <= half_length + 2.0 * scenario.grid.dx) {
        return initial_center + 0.5;
    }
    return initial_center - 0.5;
}

double constriction_zone_volume_depth_scale(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found) {
        return 0.0;
    }
    if (band.count == throat_width_cells) {
        return kConstrictionThroatVolumeDepthScale;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x < 0.0) {
        return kConstrictionUpstreamVolumeDepthScale;
    }
    if (signed_x <= half_length) {
        return kConstrictionDownstreamVolumeDepthScale;
    }
    return 0.0;
}

double initial_column_mean_depth(const Scenario& scenario, const ColumnWetBand& band, std::size_t col) {
    if (!band.found || band.count == 0) {
        return 0.0;
    }
    double total_depth = 0.0;
    for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
        total_depth += scenario.initial.h(row, col);
    }
    return total_depth / static_cast<double>(band.count);
}

double constriction_response_target_u(double current_u, double initial_u, double flow_sign) {
    double target_sign = std::abs(initial_u) > 1.0e-9 ? (initial_u >= 0.0 ? 1.0 : -1.0) : flow_sign;
    double target_abs_u = std::max(std::abs(current_u), std::abs(initial_u));
    return target_sign * target_abs_u;
}

double constriction_response_target_depth(double authored_h, double column_mean_depth, double depth_scale) {
    return std::max(authored_h, column_mean_depth) * depth_scale;
}

double constriction_reference_throat_speed(const Scenario& scenario, std::size_t throat_width_cells) {
    double speed = 0.0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells) {
            continue;
        }
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            speed = std::max(speed, std::abs(scenario.initial.u(row, col)));
        }
    }
    return speed;
}

double constriction_lateral_sign(const ColumnWetBand& band, std::size_t row) {
    double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    return static_cast<double>(row) < center_row ? -1.0 : 1.0;
}

double constriction_local_fringe_target_u(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
) {
    double flow_sign = constriction_flow_sign(scenario);
    double lateral_sign = constriction_lateral_sign(band, row);
    double speed_fraction = lateral_sign < 0.0 ? kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction
                                               : kConstrictionLocalFringeSpeedFraction;
    return flow_sign * speed_fraction * reference_speed;
}

double constriction_local_fringe_target_v(
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
) {
    double lateral_sign = constriction_lateral_sign(band, row);
    if (lateral_sign < 0.0) {
        return 0.02 * reference_speed;
    }
    return -kConstrictionLocalFringeEdgeVelocityFraction * reference_speed;
}

bool inside_relaxed_wet_band(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
    if (relax_cells == 0) {
        return false;
    }
    std::size_t first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
    std::size_t last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
    return row >= first && row <= last;
}

bool inside_constriction_local_shallow_fringe(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    if (!band.found || band.count <= throat_width_cells || throat_width_cells == 0) {
        return false;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x >= -half_length) {
        return false;
    }

    std::size_t target_first = band.first_row;
    std::size_t target_last = band.last_row;
    if (signed_x < -2.0 * half_length) {
        target_first = 0;
        target_last = scenario.grid.ny - 1;
    } else {
        std::size_t upstream_recess_cells = band.count <= throat_width_cells + 2 ? 2 : 1;
        target_first = band.first_row > upstream_recess_cells ? band.first_row - upstream_recess_cells : 0;
        target_last = std::min(scenario.grid.ny - 1, band.last_row + 3);
    }

    return row == target_first || row == target_last;
}

bool constriction_upstream_edge_cell(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    if (scenario.fixture_kind != "constriction" || !band.found || band.count <= throat_width_cells) {
        return false;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x >= -half_length) {
        return false;
    }

    if (row == band.first_row || row == band.last_row) {
        return true;
    }
    if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
        return true;
    }
    if (band.first_row > 0 && row + 1 == band.first_row) {
        return true;
    }
    if (band.last_row + 1 < scenario.grid.ny && row == band.last_row + 1) {
        return true;
    }
    return false;
}

double constriction_upstream_edge_approach_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x >= -half_length) {
        return 0.0;
    }
    if (signed_x <= -2.0 * half_length) {
        return 1.0;
    }
    return clamp((-signed_x - half_length) / half_length, 0.0, 1.0);
}

double constriction_transition_edge_face_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x < -half_length) {
        return constriction_upstream_edge_approach_weight(scenario, col);
    }
    if (signed_x >= 0.0) {
        return 0.0;
    }
    return kConstrictionTransitionEdgeFaceWeightScale * clamp(-signed_x / half_length, 0.0, 1.0);
}

double constriction_upper_edge_balance_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x >= 0.0) {
        return 0.0;
    }
    double transition_weight = kConstrictionTransitionEdgeFaceWeightScale * clamp(-signed_x / half_length, 0.0, 1.0);
    return std::max(constriction_upstream_edge_approach_weight(scenario, col), transition_weight);
}

double constriction_lower_edge_transition_momentum_weight(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t row,
    std::size_t col
) {
    if (!band.found || row != band.first_row) {
        return 0.0;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x >= -half_length) {
        return 0.0;
    }

    double transition_distance = -half_length - signed_x;
    double transition_window =
        std::max(scenario.grid.dx, kConstrictionLowerEdgeTransitionMomentumWindowCells * scenario.grid.dx);
    if (transition_distance < 0.0 || transition_distance > transition_window) {
        return 0.0;
    }

    double transition_weight = 1.0 - transition_distance / transition_window;
    return kConstrictionLowerEdgeTransitionMomentumWeightFloor * clamp(transition_weight, 0.0, 1.0);
}

double bed_slope_source_y_per_s(
    const Scenario& scenario,
    const SolverConfig& config,
    double h,
    std::size_t row,
    std::size_t col
) {
    if (config.bed_slope_source_scale == 0.0 || h <= config.dry_tolerance) {
        return 0.0;
    }
    double bed_sy = gradient_y(scenario.bed, scenario, row, col);
    return -config.bed_slope_source_scale * config.gravity * h * bed_sy;
}

double constriction_y_face_source_split_weight(
    const Scenario& scenario,
    std::size_t throat_width_cells,
    std::size_t row,
    std::size_t col
) {
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return 0.0;
    }
    return kConstrictionYFaceSourceSplitFraction * constriction_upstream_edge_approach_weight(scenario, col);
}

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
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0 || reference_speed <= 0.0) {
        return false;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells || south_row + 1 != north_row) {
        return false;
    }

    bool lower_edge_face = north_row == band.first_row;
    bool upper_edge_face = north_row == band.last_row;
    if (!lower_edge_face && !upper_edge_face) {
        return false;
    }

    double face_weight = constriction_transition_edge_face_weight(scenario, col);
    if (face_weight <= 0.0) {
        return false;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    if (column_mean_depth <= config.dry_tolerance) {
        return false;
    }

    double raw_face_depth = 0.5 * (south.h + north.h);
    bool shallow_lower_edge_face =
        lower_edge_face &&
        raw_face_depth <= kConstrictionYFaceStateShallowLowerEdgeDepthThreshold;
    double cross_stream_fraction =
        shallow_lower_edge_face
            ? kConstrictionYFaceStateShallowLowerEdgeCrossStreamFraction
            : kConstrictionYFaceStateCrossStreamFraction;
    double edge_lateral_sign = lower_edge_face ? -1.0 : 1.0;
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionYFaceStateDownstreamSpeedFraction * reference_speed;
    double target_v = -edge_lateral_sign * cross_stream_fraction * reference_speed;
    double edge_target_h = std::max(kConstrictionYFaceStateMinDepth, column_mean_depth * kConstrictionYFaceStateDepthScale);
    double blend = clamp(kConstrictionYFaceStateBlend * face_weight, 0.0, 1.0);
    double velocity_weight = std::max(face_weight, kConstrictionYFaceStateTransitionVelocityWeightFloor);
    double max_speed_delta = kConstrictionYFaceStateMaxSpeedDelta * velocity_weight;
    bool changed = false;

    auto reconstruct_state = [&](ConservedState& q, double depth_fraction, double velocity_fraction, bool reset_velocity) {
        double target_h = edge_target_h * depth_fraction;
        double new_h = q.h + blend * (target_h - q.h);
        new_h = std::max(new_h, config.dry_tolerance);
        double current_u = velocity_x(q, config);
        double current_v = velocity_y(q, config);
        double limited_u =
            reset_velocity ? target_u : move_toward(current_u, target_u, max_speed_delta * velocity_fraction);
        double limited_v =
            reset_velocity ? target_v : move_toward(current_v, target_v, max_speed_delta * velocity_fraction);
        changed = changed || std::abs(new_h - q.h) > 1.0e-12 || std::abs(limited_u - current_u) > 1.0e-12 ||
                  std::abs(limited_v - current_v) > 1.0e-12;
        q.h = new_h;
        q.hu = new_h * limited_u;
        q.hv = new_h * limited_v;
    };

    reconstruct_state(north, 1.0, 1.0, false);
    bool lower_outside_companion = lower_edge_face && south_row + 1 == band.first_row;
    double companion_depth_fraction = lower_outside_companion ? kConstrictionYFaceStateOutsideCompanionDepthFraction
                                                              : kConstrictionYFaceStateCompanionDepthFraction;
    reconstruct_state(south, companion_depth_fraction, 0.5, lower_outside_companion);
    return changed;
}

double constriction_y_face_source_split_hv_delta(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    const ConservedState& q,
    std::size_t row,
    std::size_t col
) {
    double split_weight = constriction_y_face_source_split_weight(scenario, throat_width_cells, row, col);
    if (split_weight <= 0.0 || q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double source_hv_per_s = bed_slope_source_y_per_s(scenario, config, q.h, row, col);
    double max_hv_delta = q.h * kConstrictionYFaceSourceSplitMaxSpeedPerSecond * dt * split_weight;
    return clamp(source_hv_per_s * dt * split_weight, -max_hv_delta, max_hv_delta);
}

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
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0 || dt <= 0.0) {
        return false;
    }
    double south_delta_hv = constriction_y_face_source_split_hv_delta(
        scenario, config, dt, throat_width_cells, south, south_row, col);
    double north_delta_hv = constriction_y_face_source_split_hv_delta(
        scenario, config, dt, throat_width_cells, north, north_row, col);
    if (std::abs(south_delta_hv) <= 1.0e-12 && std::abs(north_delta_hv) <= 1.0e-12) {
        return false;
    }

    ConservedState south_predictor = south;
    ConservedState north_predictor = north;
    south_predictor.hv += south_delta_hv;
    north_predictor.hv += north_delta_hv;
    FluxState split_flux = finite_volume_flux_y(south_predictor, north_predictor, config);
    flux.left = split_flux;
    flux.right = split_flux;
    return true;
}

void apply_constriction_shallow_lower_edge_face_state_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionShallowLowerEdgeFaceStateBalanceResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionShallowLowerEdgeFaceStateBalanceResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double target_v = kConstrictionYFaceStateShallowLowerEdgeCrossStreamFraction * reference_speed;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double face_weight = constriction_transition_edge_face_weight(scenario, col);
        if (face_weight <= 0.0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        std::size_t first_wet_row = band.first_row;
        double face_mean_h = 0.5 * (next.h(lower_shelf_row, col) + next.h(first_wet_row, col));
        if (face_mean_h <= config.dry_tolerance ||
            face_mean_h > kConstrictionYFaceStateShallowLowerEdgeDepthThreshold) {
            continue;
        }

        double support_weight = final_response * face_weight;
        double velocity_blend =
            clamp(
                kConstrictionShallowLowerEdgeFaceStateBalanceVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double max_speed_step =
            kConstrictionShallowLowerEdgeFaceStateBalanceMaxSpeedPerSecond * dt * support_weight;
        auto reduce_cross_stream = [&](std::size_t row) {
            if (next.h(row, col) <= config.dry_tolerance || next.v(row, col) <= target_v) {
                return;
            }
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
        };

        reduce_cross_stream(lower_shelf_row);
        reduce_cross_stream(first_wet_row);
    }
}

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
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0) {
        return;
    }
    (void)south;

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells) {
        return;
    }

    if (south_row + 1 != north_row) {
        return;
    }
    bool lower_edge_face = north_row == band.first_row;
    bool upper_edge_face = north_row == band.last_row;
    if (!lower_edge_face && !upper_edge_face) {
        return;
    }

    double face_weight = constriction_transition_edge_face_weight(scenario, col);
    if (face_weight <= 0.0) {
        return;
    }

    const ConservedState& edge = north;
    if (edge.h <= config.dry_tolerance) {
        return;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    double target_h = std::max(kConstrictionUpstreamEdgeFluxMinTargetDepth,
                               column_mean_depth * kConstrictionUpstreamEdgeFluxTargetDepthScale);
    if (edge.h <= target_h) {
        return;
    }

    double depth_rate = std::min(
        (edge.h - target_h) * kConstrictionUpstreamEdgeFluxRate,
        kConstrictionUpstreamEdgeFluxMaxDepthPerSecond * face_weight);
    if (depth_rate <= 0.0) {
        return;
    }

    double direction = lower_edge_face ? 1.0 : -1.0;
    double mass_flux = direction * depth_rate * scenario.grid.dy;
    double edge_u = edge.hu / safe_depth(edge.h, config.dry_tolerance);
    double edge_v = edge.hv / safe_depth(edge.h, config.dry_tolerance);
    flux.left.h += mass_flux;
    flux.right.h += mass_flux;
    flux.left.hu += mass_flux * edge_u;
    flux.right.hu += mass_flux * edge_u;
    flux.left.hv += mass_flux * edge_v;
    flux.right.hv += mass_flux * edge_v;

    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }
    double opposition_target_h = std::max(
        kConstrictionYFaceStateMinDepth,
        column_mean_depth * kConstrictionYFaceOppositionFluxTargetDepthScale);
    double target_flux_h =
        direction * opposition_target_h * kConstrictionYFaceOppositionFluxCrossStreamFraction * reference_speed;
    double correction_weight = std::max(face_weight, kConstrictionYFaceOppositionFluxTransitionWeightFloor);
    double max_flux_correction =
        kConstrictionYFaceOppositionFluxMaxReferenceScale * reference_speed * correction_weight;
    double correction_h = clamp(target_flux_h - flux.left.h, -max_flux_correction, max_flux_correction);
    if (std::abs(correction_h) <= 1.0e-12) {
        return;
    }
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionYFaceStateDownstreamSpeedFraction * reference_speed;
    double target_v = direction * kConstrictionYFaceOppositionFluxCrossStreamFraction * reference_speed;
    flux.left.h += correction_h;
    flux.right.h += correction_h;
    flux.left.hu += correction_h * target_u;
    flux.right.hu += correction_h * target_u;
    flux.left.hv += correction_h * target_v;
    flux.right.hv += correction_h * target_v;
}

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
) {
    if (scenario.fixture_kind != "constriction" || h_next <= config.dry_tolerance ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return;
    }

    double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
    double transition_weight = constriction_lower_edge_transition_momentum_weight(scenario, band, row, col);
    approach_weight = std::max(approach_weight, transition_weight);
    if (approach_weight <= 0.0) {
        return;
    }

    double lateral_sign = constriction_lateral_sign(band, row);
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionUpstreamEdgeSpeedFraction * reference_speed;
    double target_v = -lateral_sign * kConstrictionUpstreamEdgeCrossStreamFraction * reference_speed;
    double blend = clamp(kConstrictionUpstreamEdgeMomentumRate * dt * approach_weight, 0.0, 1.0);
    double max_step_speed = kConstrictionUpstreamEdgeMomentumMaxSpeedPerSecond * dt * approach_weight;

    double u_next = hu_next / safe_depth(h_next, config.dry_tolerance);
    double v_next = hv_next / safe_depth(h_next, config.dry_tolerance);
    double blended_u = u_next + blend * (target_u - u_next);
    double blended_v = v_next + blend * (target_v - v_next);
    double limited_u = move_toward(u_next, blended_u, max_step_speed);
    double limited_v = move_toward(v_next, blended_v, max_step_speed);
    hu_next = h_next * limited_u;
    hv_next = h_next * limited_v;
}

void apply_constriction_upstream_edge_boundary_state(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    ConservedState& boundary
) {
    if (scenario.fixture_kind != "constriction" || boundary.h <= config.dry_tolerance ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    bool upstream_edge_column = flow_sign >= 0.0 ? col == 0 : col + 1 == scenario.grid.nx;
    if (!upstream_edge_column) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    double target_h = std::max(kConstrictionUpstreamEdgeFluxMinTargetDepth,
                               column_mean_depth * kConstrictionUpstreamEdgeFluxTargetDepthScale);
    double lateral_sign = constriction_lateral_sign(band, row);
    double target_u = flow_sign * kConstrictionUpstreamEdgeSpeedFraction * reference_speed;
    double target_v = -lateral_sign * kConstrictionUpstreamEdgeCrossStreamFraction * reference_speed;
    boundary.h = target_h;
    boundary.hu = target_h * target_u;
    boundary.hv = target_h * target_v;
}

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
) {
    if (scenario.fixture_kind != "constriction" || h_next <= kConstrictionCrossStreamMomentumMinDepth ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells) {
        return;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x <= half_length) {
        return;
    }

    double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
    double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
    double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
    double zone_weight = kConstrictionCrossStreamMomentumInteriorWeightFloor +
                         (1.0 - kConstrictionCrossStreamMomentumInteriorWeightFloor) * edge_norm;
    double target_v = lateral_sign * kConstrictionCrossStreamMomentumRecoveryFraction * reference_speed;

    double current_v = hv_next / safe_depth(h_next, config.dry_tolerance);
    double blend = clamp(kConstrictionCrossStreamMomentumRate * dt * zone_weight, 0.0, 1.0);
    double max_step_speed = kConstrictionCrossStreamMomentumMaxSpeedPerSecond * dt * zone_weight;
    double blended_v = current_v + blend * (target_v - current_v);
    double limited_v = move_toward(current_v, blended_v, max_step_speed);
    hv_next = h_next * limited_v;
}

void apply_wet_dry_shoreline_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "wet_dry_shoreline") {
        return;
    }

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (scenario.initial.wet(row, col)) {
                continue;
            }

            double leaked_h = next.h(row, col);
            if (leaked_h > config.dry_tolerance) {
                GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
                if (receiver.found) {
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + leaked_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + leaked_h * next.u(row, col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                }
            }

            next.h(row, col) = 0.0;
            next.u(row, col) = 0.0;
            next.v(row, col) = 0.0;
        }
    }

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (!scenario.initial.wet(row, col)) {
                continue;
            }
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            } else {
                next.v(row, col) = 0.0;
            }
        }
    }
}

void apply_constriction_volume_response_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_depth = kConstrictionVolumeResponseMaxDepthPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        double depth_scale = constriction_zone_volume_depth_scale(scenario, band, throat_width_cells, col);
        if (depth_scale <= 0.0) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }

            double authored_h = scenario.initial.h(row, col);
            double target_h = constriction_response_target_depth(authored_h, column_mean_depth, depth_scale);
            if (target_h <= current_h) {
                continue;
            }

            double requested_h = (target_h - current_h) * kConstrictionVolumeResponseRate * dt;
            double added_h = std::min(target_h - current_h, std::min(requested_h, max_step_depth));
            if (added_h <= 0.0) {
                continue;
            }

            double target_u = constriction_response_target_u(next.u(row, col), scenario.initial.u(row, col), flow_sign);
            double merged_h = current_h + added_h;
            double merged_hu = current_h * next.u(row, col) + added_h * target_u;
            double merged_hv = current_h * next.v(row, col) + added_h * next.v(row, col);
            next.h(row, col) = merged_h;
            next.u(row, col) = merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(row, col) = merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }
}

void apply_constriction_recovery_energy_transport_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;
    double max_step_depth = kConstrictionRecoveryTransportMaxDepthPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= config.dry_tolerance) {
                    continue;
                }
                double target_h = constriction_response_target_depth(
                    scenario.initial.h(row, col),
                    column_mean_depth,
                    kConstrictionRecoveryTransportDepthScale);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionRecoveryTransportRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        double depth_scale = constriction_zone_volume_depth_scale(scenario, band, throat_width_cells, col);
        if (depth_scale <= 0.0) {
            continue;
        }
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }
            double target_h = constriction_response_target_depth(scenario.initial.h(row, col), column_mean_depth, depth_scale);
            if (target_h <= current_h) {
                continue;
            }
            double capacity = target_h - current_h;
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    double flow_sign = constriction_flow_sign(scenario);
    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_upstream_shoulder_froude_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double depth_blend = clamp(kConstrictionShoulderDepthTaperRate * dt, 0.0, 1.0);
    double velocity_blend = clamp(kConstrictionShoulderVelocityRate * dt, 0.0, 1.0);
    double max_velocity_step = kConstrictionShoulderMaxVelocityPerSecond * dt;
    double target_u = flow_sign * kConstrictionShoulderSpeedFraction * reference_speed;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand initial_band = initial_wet_band_in_column(scenario, col);
        if (!initial_band.found || initial_band.count <= throat_width_cells ||
            constriction_signed_x(scenario, col) >= -2.0 * half_length) {
            continue;
        }

        ColumnWetBand active_band = active_wet_band_in_column(scenario, config, next, col);
        if (!active_band.found || active_band.count < 3) {
            continue;
        }

        double column_mass = 0.0;
        double weight_sum = 0.0;
        double center_row = 0.5 * (static_cast<double>(active_band.first_row) + static_cast<double>(active_band.last_row));
        double half_span = std::max(0.5, 0.5 * static_cast<double>(active_band.last_row - active_band.first_row));
        for (std::size_t row = active_band.first_row; row <= active_band.last_row; ++row) {
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double interior = std::pow(1.0 - edge_norm, 1.35);
            weight_sum += kConstrictionShoulderEdgeWeight + kConstrictionShoulderInteriorWeight * interior;
            column_mass += next.h(row, col);
        }
        if (column_mass <= config.dry_tolerance || weight_sum <= 0.0) {
            continue;
        }

        for (std::size_t row = active_band.first_row; row <= active_band.last_row; ++row) {
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double interior = std::pow(1.0 - edge_norm, 1.35);
            double weight = kConstrictionShoulderEdgeWeight + kConstrictionShoulderInteriorWeight * interior;
            double tapered_h = column_mass * weight / weight_sum;
            next.h(row, col) = std::max(config.dry_tolerance, next.h(row, col) + depth_blend * (tapered_h - next.h(row, col)));

            bool edge_cell = row == active_band.first_row || row == active_band.first_row + 1 ||
                             row + 1 == active_band.last_row || row == active_band.last_row;
            if (!edge_cell) {
                continue;
            }
            double edge_sign = static_cast<double>(row) < center_row ? 1.0 : -1.0;
            double target_v = edge_sign * kConstrictionShoulderEdgeVelocityFraction * std::abs(target_u);
            double limited_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double limited_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), limited_u, max_velocity_step);
            next.v(row, col) = move_toward(next.v(row, col), limited_v, max_velocity_step);
        }
    }
}

void apply_constriction_local_shallow_fringe_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    double max_step_depth = kConstrictionLocalFringeMaxDepthPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        if (constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= kConstrictionLocalFringeTargetDepth) {
                continue;
            }

            GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
            double excess_h = current_h - kConstrictionLocalFringeTargetDepth;
            if (!receiver.found) {
                continue;
            }
            if (excess_h > config.dry_tolerance) {
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + excess_h;
                double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + excess_h * next.u(row, col);
                double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + excess_h * next.v(row, col);
                next.h(receiver.row, receiver.col) = merged_h;
                next.u(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
            next.h(row, col) = kConstrictionLocalFringeTargetDepth;
            next.u(row, col) = constriction_local_fringe_target_u(scenario, band, row, reference_speed);
            next.v(row, col) = constriction_local_fringe_target_v(band, row, reference_speed);
        }
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= config.dry_tolerance) {
                    continue;
                }
                double target_h = constriction_response_target_depth(
                    scenario.initial.h(row, col),
                    column_mean_depth,
                    kConstrictionLocalFringeRecoveryDepthScale);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionLocalFringeRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        if (constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        double target_depth = kConstrictionLocalFringeTargetDepth;
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h >= target_depth) {
                continue;
            }
            double requested_h = (target_depth - current_h) * kConstrictionLocalFringeRate * dt;
            double capacity = std::min(target_depth - current_h, std::min(requested_h, max_step_depth));
            if (capacity <= 0.0) {
                continue;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        ColumnWetBand band = initial_wet_band_in_column(scenario, receiver.col);
        double target_u = constriction_local_fringe_target_u(scenario, band, receiver.row, reference_speed);
        double target_v = constriction_local_fringe_target_v(band, receiver.row, reference_speed);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_momentum_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t reference_width_cells = max_initial_wet_count(scenario);
    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    if (reference_width_cells == 0) {
        return;
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.count >= reference_width_cells) {
            continue;
        }
        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (!scenario.initial.wet(row, col) || next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double initial_u = scenario.initial.u(row, col);
            if (std::abs(next.u(row, col)) < std::abs(initial_u)) {
                next.u(row, col) = initial_u;
            }

            bool edge_cell = row == band.first_row || row == band.last_row;
            if (!edge_cell || band.count < 2) {
                continue;
            }
            double edge_sign = static_cast<double>(row) < center_row ? 1.0 : -1.0;
            double target_v = edge_sign * kConstrictionEdgeVelocityFraction *
                              std::max(std::abs(next.u(row, col)), std::abs(initial_u));
            if (std::abs(next.v(row, col)) < std::abs(target_v)) {
                next.v(row, col) = target_v;
            }
        }
    }
}

void apply_constriction_near_throat_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    double target_u = flow_sign * kConstrictionNearThroatSpeedFraction * reference_speed;
    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double late_response = clamp((response_progress - 0.5) / 0.5, 0.0, 1.0);
    double lower_shelf_depth_weight =
        kConstrictionNearThroatLowerShelfDepthWeight +
        late_response *
            (kConstrictionNearThroatLateLowerShelfDepthWeight -
             kConstrictionNearThroatLowerShelfDepthWeight);
    double lower_shelf_speed_fraction =
        kConstrictionNearThroatLowerShelfSpeedFraction +
        late_response *
            (kConstrictionNearThroatLateLowerShelfSpeedFraction -
             kConstrictionNearThroatLowerShelfSpeedFraction);
    double lower_shelf_cross_stream_fraction =
        kConstrictionNearThroatLowerShelfCrossStreamFraction +
        late_response *
            (kConstrictionNearThroatLateLowerShelfCrossStreamFraction -
             kConstrictionNearThroatLowerShelfCrossStreamFraction);
    double interior_speed_fraction =
        kConstrictionNearThroatSpeedFraction +
        late_response *
            (kConstrictionNearThroatLateInteriorSpeedFraction -
             kConstrictionNearThroatSpeedFraction);
    double interior_cross_stream_fraction =
        kConstrictionNearThroatInteriorCrossStreamFraction +
        late_response *
            (kConstrictionNearThroatLateInteriorCrossStreamFraction -
             kConstrictionNearThroatInteriorCrossStreamFraction);
    double transferable_mass = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        if (!is_center_throat_column(scenario, band, throat_width_cells, col) || band.first_row == 0) {
            continue;
        }

        std::size_t target_first = band.first_row - 1;
        std::size_t target_last = band.last_row;
        if (target_last >= scenario.grid.ny || target_last < target_first) {
            continue;
        }
        std::size_t source_first = std::min(target_first, band.first_row);
        std::size_t source_last = std::max(target_last, band.last_row);

        double current_mass = 0.0;
        for (std::size_t row = source_first; row <= source_last; ++row) {
            current_mass += next.h(row, col);
        }
        if (current_mass <= config.dry_tolerance) {
            continue;
        }

        double target_mass = initial_column_mean_depth(scenario, band, col) *
                             static_cast<double>(band.count) * kConstrictionNearThroatDepthScale;
        double retained_mass = std::min(current_mass, target_mass);
        transferable_mass += current_mass - retained_mass;
        auto profile_weight = [&](std::size_t row) {
            if (row < band.first_row) {
                return lower_shelf_depth_weight;
            }
            if (row >= band.last_row) {
                return kConstrictionNearThroatUpperShelfDepthWeight;
            }
            double relative = static_cast<double>(row - band.first_row);
            double interior_span = std::max(1.0, static_cast<double>(band.count - 2));
            double t = clamp(relative / interior_span, 0.0, 1.0);
            if (t <= 0.5) {
                return kConstrictionNearThroatInteriorLowerDepthWeight +
                       2.0 * t *
                           (kConstrictionNearThroatInteriorCenterDepthWeight -
                            kConstrictionNearThroatInteriorLowerDepthWeight);
            }
            return kConstrictionNearThroatInteriorCenterDepthWeight +
                   2.0 * (t - 0.5) *
                       (kConstrictionNearThroatInteriorUpperDepthWeight -
                        kConstrictionNearThroatInteriorCenterDepthWeight);
        };
        double profile_weight_sum = 0.0;
        for (std::size_t row = target_first; row <= target_last; ++row) {
            profile_weight_sum += profile_weight(row);
        }
        if (profile_weight_sum <= 0.0) {
            continue;
        }
        double target_depth_scale = retained_mass / profile_weight_sum;

        for (std::size_t row = source_first; row <= source_last; ++row) {
            if (row < target_first || row > target_last) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }

            bool lower_shifted_edge = row == target_first;
            double target_depth = target_depth_scale * profile_weight(row);
            next.h(row, col) = target_depth;
            if (lower_shifted_edge) {
                next.u(row, col) =
                    flow_sign * lower_shelf_speed_fraction * reference_speed;
                next.v(row, col) = lower_shelf_cross_stream_fraction * reference_speed;
            } else if (row >= band.last_row) {
                next.u(row, col) = target_u;
                next.v(row, col) = kConstrictionNearThroatUpperShelfCrossStreamFraction * std::abs(target_u);
            } else {
                next.u(row, col) = flow_sign * interior_speed_fraction * reference_speed;
                next.v(row, col) = interior_cross_stream_fraction * reference_speed;
            }
        }
    }

    if (transferable_mass <= config.dry_tolerance) {
        return;
    }

    std::size_t throat_width_cells_for_receivers = throat_width_cells;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double receiver_capacity = 0.0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells_for_receivers || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        double target_h = column_mean_depth * kConstrictionNearThroatReceiverDepthScale;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells_for_receivers, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells_for_receivers, col, row)) {
                continue;
            }
            if (next.h(row, col) >= target_h) {
                continue;
            }
            double capacity = target_h - next.h(row, col);
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_mass = std::min(transferable_mass, receiver_capacity);
    if (transfer_mass <= config.dry_tolerance || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_mass * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_receiver_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_receiver_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_throat_edge_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionThroatEdgeReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionThroatEdgeReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionThroatEdgeReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionThroatEdgeReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row <= band.first_row + 1) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (std::abs(signed_x) > half_length) {
            continue;
        }
        bool allow_depth_transfer = std::abs(signed_x) >= scenario.grid.dx;

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionThroatEdgeReliefDonorFloorScale);
        std::vector<ConstrictionDepthTransferCell> donors;
        double donor_capacity = 0.0;
        if (band.first_row > 0) {
            double capacity = std::max(0.0, next.h(band.first_row - 1, col) - donor_floor);
            if (capacity > config.dry_tolerance) {
                donors.push_back(ConstrictionDepthTransferCell{band.first_row - 1, col, capacity});
                donor_capacity += capacity;
            }
        }
        double upper_edge_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (upper_edge_capacity > config.dry_tolerance) {
            donors.push_back(ConstrictionDepthTransferCell{band.last_row, col, upper_edge_capacity});
            donor_capacity += upper_edge_capacity;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        double lower_edge_target_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionThroatEdgeReliefLowerEdgeReceiverTargetScale);
        double interior_target_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionThroatEdgeReliefInteriorTargetScale);
        double interior_cross_stream_sign = signed_x < 0.0 ? -1.0 : 1.0;
        double lower_edge_target_v =
            (signed_x < 0.0 ? kConstrictionThroatEdgeReliefUpstreamLowerCrossStreamFraction
                             : kConstrictionThroatEdgeReliefDownstreamLowerCrossStreamFraction) *
            reference_speed;
        double lower_edge_capacity = std::max(0.0, lower_edge_target_h - next.h(band.first_row, col));
        if (lower_edge_capacity > config.dry_tolerance) {
            receivers.push_back(ConstrictionProfileTransferCell{
                band.first_row,
                col,
                lower_edge_capacity,
                flow_sign * kConstrictionThroatEdgeReliefInteriorSpeedFraction * reference_speed,
                lower_edge_target_v,
            });
            receiver_capacity += lower_edge_capacity;
        }
        for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
            double capacity = std::max(0.0, interior_target_h - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * kConstrictionThroatEdgeReliefInteriorSpeedFraction * reference_speed,
                interior_cross_stream_sign * kConstrictionThroatEdgeReliefInteriorCrossStreamFraction *
                    reference_speed,
            });
            receiver_capacity += capacity;
        }

        double transfer_h = 0.0;
        if (allow_depth_transfer &&
            donor_capacity > config.dry_tolerance &&
            receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionThroatEdgeReliefRate * dt * final_response;
            transfer_h =
                std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        }

        if (transfer_h > config.dry_tolerance) {
            for (const ConstrictionDepthTransferCell& donor : donors) {
                double removed_h = transfer_h * donor.capacity / donor_capacity;
                next.h(donor.row, donor.col) =
                    std::max(donor_floor, next.h(donor.row, donor.col) - removed_h);
            }
            for (const ConstrictionProfileTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + added_h;
                double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
                double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
                next.h(receiver.row, receiver.col) = merged_h;
                next.u(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        auto shape_row = [&](std::size_t row, double speed_fraction, double target_v) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double blend =
                clamp(kConstrictionThroatEdgeReliefVelocityRate * dt * final_response, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
        };

        double upper_edge_target_v =
            (signed_x < 0.0 ? -kConstrictionThroatEdgeReliefUpstreamUpperCrossStreamFraction
                             : kConstrictionThroatEdgeReliefDownstreamUpperCrossStreamFraction) *
            reference_speed;
        double interior_target_v =
            interior_cross_stream_sign * kConstrictionThroatEdgeReliefInteriorCrossStreamFraction *
            reference_speed;

        shape_row(
            band.first_row,
            kConstrictionThroatEdgeReliefEdgeSpeedFraction,
            lower_edge_target_v);
        for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
            shape_row(
                row,
                kConstrictionThroatEdgeReliefInteriorSpeedFraction,
                interior_target_v);
        }
        shape_row(
            band.last_row,
            kConstrictionThroatEdgeReliefEdgeSpeedFraction,
            upper_edge_target_v);
    }
}

void apply_constriction_throat_edge_spill_recovery_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double response_width = std::max(1.0e-6, 1.0 - kConstrictionThroatEdgeSpillResponseStart);
    double final_response =
        clamp((response_progress - kConstrictionThroatEdgeSpillResponseStart) / response_width, 0.0, 1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double receiver_window =
        static_cast<double>(kConstrictionThroatEdgeSpillReceiverWindowCells) * scenario.grid.dx;
    double max_depth_step = kConstrictionThroatEdgeSpillMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionThroatEdgeSpillMaxSpeedPerSecond * dt * final_response;

    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionProfileTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (band.count == throat_width_cells && signed_x >= scenario.grid.dx && signed_x <= half_length &&
            band.last_row > band.first_row) {
            double donor_floor = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionThroatEdgeSpillDonorFloorScale);
            if (band.first_row > 0) {
                double lower_shelf_capacity = std::max(0.0, next.h(band.first_row - 1, col) - donor_floor);
                if (lower_shelf_capacity > config.dry_tolerance) {
                    donors.push_back(ConstrictionDepthTransferCell{band.first_row - 1, col, lower_shelf_capacity});
                    donor_capacity += lower_shelf_capacity;
                }
            }
            double upper_edge_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
            if (upper_edge_capacity > config.dry_tolerance) {
                donors.push_back(ConstrictionDepthTransferCell{band.last_row, col, upper_edge_capacity});
                donor_capacity += upper_edge_capacity;
            }
            continue;
        }

        bool first_recovery_window =
            signed_x > half_length && signed_x <= half_length + std::max(scenario.grid.dx, receiver_window);
        if (!first_recovery_window || band.count > throat_width_cells + 2 || band.last_row == band.first_row) {
            continue;
        }

        double receiver_target_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionThroatEdgeSpillReceiverTargetDepthScale);
        std::size_t first_receiver_row = band.last_row > band.first_row ? band.last_row - 1 : band.last_row;
        for (std::size_t row = first_receiver_row; row <= band.last_row; ++row) {
            double current_h = next.h(row, col);
            if (current_h >= receiver_target_h) {
                continue;
            }
            double capacity = receiver_target_h - current_h;
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            bool edge_row = row == band.last_row;
            double target_speed_fraction = edge_row
                                               ? kConstrictionThroatEdgeSpillReceiverEdgeSpeedFraction
                                               : kConstrictionThroatEdgeSpillReceiverInnerSpeedFraction;
            double target_cross_stream_fraction = edge_row
                                                      ? kConstrictionThroatEdgeSpillReceiverEdgeCrossStreamFraction
                                                      : kConstrictionThroatEdgeSpillReceiverInnerCrossStreamFraction;
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * target_speed_fraction * reference_speed,
                target_cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        }
    }

    double requested_h = receiver_capacity * kConstrictionThroatEdgeSpillRate * dt * final_response;
    double transfer_h =
        std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
            if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
                next.h(donor.row, donor.col) = 0.0;
                next.u(donor.row, donor.col) = 0.0;
                next.v(donor.row, donor.col) = 0.0;
            }
        }

        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            double added_h = transfer_h * receiver.capacity / receiver_capacity;
            if (added_h <= 0.0) {
                continue;
            }
            double receiver_h = next.h(receiver.row, receiver.col);
            double merged_h = receiver_h + added_h;
            double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
            double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }

    auto shape_row = [&](std::size_t row, std::size_t col, double speed_fraction, double cross_stream_fraction) {
        if (row >= scenario.grid.ny || col >= scenario.grid.nx || next.h(row, col) <= config.dry_tolerance) {
            return;
        }
        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = cross_stream_fraction * reference_speed;
        double blend = clamp(kConstrictionThroatEdgeSpillVelocityRate * dt * final_response, 0.0, 1.0);
        double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < scenario.grid.dx || signed_x > half_length) {
            continue;
        }
        if (band.first_row > 0) {
            shape_row(
                band.first_row - 1,
                col,
                kConstrictionThroatEdgeSpillLowerShelfSpeedFraction,
                kConstrictionThroatEdgeSpillLowerShelfCrossStreamFraction);
        }
        shape_row(
            band.last_row,
            col,
            kConstrictionThroatEdgeSpillUpperEdgeSpeedFraction,
            kConstrictionThroatEdgeSpillUpperEdgeCrossStreamFraction);
    }
}

void apply_constriction_throat_shelf_edge_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double response_width = std::max(1.0e-6, 1.0 - kConstrictionThroatShelfEdgeFinalReliefResponseStart);
    double final_response =
        clamp((response_progress - kConstrictionThroatShelfEdgeFinalReliefResponseStart) / response_width, 0.0, 1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double receiver_window =
        static_cast<double>(kConstrictionThroatShelfEdgeFinalReliefReceiverWindowCells) * scenario.grid.dx;
    double max_depth_step = kConstrictionThroatShelfEdgeFinalReliefMaxDepthPerSecond * dt * final_response;

    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionProfileTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.last_row <= band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (band.count == throat_width_cells && signed_x >= scenario.grid.dx && signed_x <= half_length) {
            double donor_floor = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionThroatShelfEdgeFinalReliefDonorFloorScale);
            if (band.first_row > 0) {
                double lower_shelf_capacity = std::max(0.0, next.h(band.first_row - 1, col) - donor_floor);
                if (lower_shelf_capacity > config.dry_tolerance) {
                    donors.push_back(ConstrictionDepthTransferCell{band.first_row - 1, col, lower_shelf_capacity});
                    donor_capacity += lower_shelf_capacity;
                }
            }

            double upper_edge_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
            if (upper_edge_capacity > config.dry_tolerance) {
                donors.push_back(ConstrictionDepthTransferCell{band.last_row, col, upper_edge_capacity});
                donor_capacity += upper_edge_capacity;
            }
            continue;
        }

        bool first_recovery_window =
            signed_x > half_length && signed_x <= half_length + std::max(scenario.grid.dx, receiver_window);
        if (!first_recovery_window || band.count > throat_width_cells + 2) {
            continue;
        }

        double receiver_target_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionThroatShelfEdgeFinalReliefReceiverTargetDepthScale);
        std::size_t first_receiver_row = band.last_row - 1;
        for (std::size_t row = first_receiver_row; row <= band.last_row; ++row) {
            double current_h = next.h(row, col);
            if (current_h >= receiver_target_h) {
                continue;
            }
            double capacity = receiver_target_h - current_h;
            if (capacity <= config.dry_tolerance) {
                continue;
            }

            bool edge_row = row == band.last_row;
            double target_speed_fraction =
                edge_row ? kConstrictionThroatShelfEdgeFinalReliefReceiverEdgeSpeedFraction
                         : kConstrictionThroatShelfEdgeFinalReliefReceiverInnerSpeedFraction;
            double target_cross_stream_fraction =
                edge_row ? kConstrictionThroatShelfEdgeFinalReliefReceiverEdgeCrossStreamFraction
                         : kConstrictionThroatShelfEdgeFinalReliefReceiverInnerCrossStreamFraction;
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * target_speed_fraction * reference_speed,
                target_cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        }
    }

    double requested_h = receiver_capacity * kConstrictionThroatShelfEdgeFinalReliefRate * dt * final_response;
    double transfer_h =
        std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_h * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    for (const ConstrictionProfileTransferCell& receiver : receivers) {
        double added_h = transfer_h * receiver.capacity / receiver_capacity;
        if (added_h <= 0.0) {
            continue;
        }

        double receiver_h = next.h(receiver.row, receiver.col);
        double merged_h = receiver_h + added_h;
        double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
        double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_upstream_throat_lower_shelf_final_relief(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionUpstreamThroatLowerShelfFinalReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamThroatLowerShelfFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamThroatLowerShelfFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamThroatLowerShelfFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.first_row == 0 ||
            band.last_row <= band.first_row + 1) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= -scenario.grid.dx || signed_x < -half_length) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t donor_row = band.first_row - 1;
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamThroatLowerShelfFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, std::size_t receiver_col, double target_scale, double speed_fraction, double cross_fraction) {
            if (receiver_col >= scenario.grid.nx || row >= scenario.grid.ny ||
                next.h(row, receiver_col) <= config.dry_tolerance) {
                return;
            }
            double target_h = std::max(kConstrictionLocalFringeTargetDepth, column_mean_depth * target_scale);
            double capacity = std::max(0.0, target_h - next.h(row, receiver_col));
            if (capacity <= config.dry_tolerance) {
                return;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                receiver_col,
                capacity,
                flow_sign * speed_fraction * reference_speed,
                cross_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        add_receiver(
            band.first_row,
            col,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorTargetScale,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorSpeedFraction,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorCrossStreamFraction);
        add_receiver(
            band.first_row + 1,
            col,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorTargetScale,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorSpeedFraction,
            kConstrictionUpstreamThroatLowerShelfFinalReliefInteriorCrossStreamFraction);
        if (col + 1 < scenario.grid.nx) {
            ColumnWetBand downstream_band = initial_wet_band_in_column(scenario, col + 1);
            if (downstream_band.found && downstream_band.count == throat_width_cells &&
                downstream_band.first_row > 0) {
                add_receiver(
                    downstream_band.first_row - 1,
                    col + 1,
                    kConstrictionUpstreamThroatLowerShelfFinalReliefDownstreamShelfTargetScale,
                    kConstrictionUpstreamThroatLowerShelfFinalReliefDownstreamShelfSpeedFraction,
                    kConstrictionUpstreamThroatLowerShelfFinalReliefDownstreamShelfCrossStreamFraction);
            }
        }

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionUpstreamThroatLowerShelfFinalReliefRate * dt * final_response;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);
        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            double added_h = transfer_h * receiver.capacity / receiver_capacity;
            if (added_h <= 0.0) {
                continue;
            }
            double receiver_h = next.h(receiver.row, receiver.col);
            double merged_h = receiver_h + added_h;
            double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
            double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }

        if (next.h(donor_row, col) <= config.dry_tolerance) {
            next.h(donor_row, col) = 0.0;
            next.u(donor_row, col) = 0.0;
            next.v(donor_row, col) = 0.0;
            continue;
        }

        double velocity_blend = clamp(
            kConstrictionUpstreamThroatLowerShelfFinalReliefVelocityRate * dt * final_response,
            0.0,
            1.0);
        double target_u =
            flow_sign * kConstrictionUpstreamThroatLowerShelfFinalReliefDonorSpeedFraction * reference_speed;
        double target_v =
            kConstrictionUpstreamThroatLowerShelfFinalReliefDonorCrossStreamFraction * reference_speed;
        double blended_u = next.u(donor_row, col) + velocity_blend * (target_u - next.u(donor_row, col));
        double blended_v = next.v(donor_row, col) + velocity_blend * (target_v - next.v(donor_row, col));
        next.u(donor_row, col) = move_toward(next.u(donor_row, col), blended_u, max_speed_step);
        next.v(donor_row, col) = move_toward(next.v(donor_row, col), blended_v, max_speed_step);
    }
}

void apply_constriction_upstream_interior_cross_stream_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionUpstreamInteriorCrossStreamFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamInteriorCrossStreamFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double peak_center =
        -half_length -
        kConstrictionUpstreamInteriorCrossStreamFinalSupportCenterOffsetCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx,
            kConstrictionUpstreamInteriorCrossStreamFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionUpstreamInteriorCrossStreamFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < -half_length -
                           kConstrictionUpstreamInteriorCrossStreamFinalSupportUpstreamWindowCells *
                               scenario.grid.dx ||
            signed_x > -half_length -
                           kConstrictionUpstreamInteriorCrossStreamFinalSupportDownstreamMarginCells *
                               scenario.grid.dx) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        double normalized_distance = (signed_x - peak_center) / peak_width;
        double peak_weight = std::exp(-(normalized_distance * normalized_distance));
        double support_weight = final_response * peak_weight;
        if (support_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInteriorCrossStreamFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);

        auto shape_row = [&](std::size_t row, double base_fraction, double peak_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = (base_fraction + peak_fraction * peak_weight) * reference_speed;
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * peak_weight);
        };

        shape_row(
            band.first_row + 1,
            kConstrictionUpstreamInteriorCrossStreamFinalSupportLowerInteriorBaseFraction,
            kConstrictionUpstreamInteriorCrossStreamFinalSupportLowerInteriorPeakFraction);
        shape_row(
            band.first_row + 2,
            kConstrictionUpstreamInteriorCrossStreamFinalSupportCenterInteriorBaseFraction,
            kConstrictionUpstreamInteriorCrossStreamFinalSupportCenterInteriorPeakFraction);
    }
}

void apply_constriction_downstream_interior_streamwise_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionDownstreamInteriorStreamwiseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamInteriorStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamInteriorStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < kConstrictionDownstreamInteriorStreamwiseFinalSupportMinSignedXCells *
                           scenario.grid.dx ||
            signed_x > half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        double downstream_weight = clamp(signed_x / std::max(half_length, scenario.grid.dx), 0.0, 1.0);
        double response_weight = final_response * std::sqrt(std::max(0.0, downstream_weight));
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamInteriorStreamwiseFinalSupportVelocityRate * dt * response_weight,
                0.0,
                1.0);
        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double row_limit = center + 0.5;
        double base_speed_fraction =
            kConstrictionDownstreamInteriorStreamwiseFinalSupportBaseSpeedFraction -
            kConstrictionDownstreamInteriorStreamwiseFinalSupportDownstreamTaperFraction * downstream_weight;

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (static_cast<double>(row) > row_limit || next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double signed_row_offset = static_cast<double>(row) - center;
            double row_bias = 0.0;
            if (signed_row_offset < -0.5) {
                row_bias = kConstrictionDownstreamInteriorStreamwiseFinalSupportLowerRowBiasFraction;
            } else if (signed_row_offset > 0.0) {
                row_bias = kConstrictionDownstreamInteriorStreamwiseFinalSupportUpperRowBiasFraction;
            }

            double target_u = flow_sign * (base_speed_fraction + row_bias) * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
        }
    }
}

void apply_constriction_upstream_outer_upper_shelf_final_profile(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionUpstreamOuterUpperShelfFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamOuterUpperShelfFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionUpstreamOuterUpperShelfFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (upstream_distance_cells > kConstrictionUpstreamOuterUpperShelfFinalProfileWindowCells) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 2 >= scenario.grid.ny) {
            continue;
        }

        std::size_t shelf_row = band.last_row + 2;
        if (next.h(shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double window_span =
            std::max(1.0, static_cast<double>(kConstrictionUpstreamOuterUpperShelfFinalProfileWindowCells));
        double inlet_weight = 1.0 - clamp(static_cast<double>(upstream_distance_cells) / window_span, 0.0, 1.0);
        double speed_fraction =
            inlet_weight * kConstrictionUpstreamOuterUpperShelfFinalProfileInletSpeedFraction +
            (1.0 - inlet_weight) * kConstrictionUpstreamOuterUpperShelfFinalProfileOuterSpeedFraction;
        double cross_stream_fraction =
            inlet_weight * kConstrictionUpstreamOuterUpperShelfFinalProfileInletCrossStreamFraction +
            (1.0 - inlet_weight) * kConstrictionUpstreamOuterUpperShelfFinalProfileOuterCrossStreamFraction;
        double response_weight = final_response * constriction_upstream_edge_approach_weight(scenario, col);
        if (response_weight <= 0.0) {
            continue;
        }

        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = -cross_stream_fraction * reference_speed;
        double velocity_blend =
            clamp(kConstrictionUpstreamOuterUpperShelfFinalProfileVelocityRate * dt * response_weight, 0.0, 1.0);
        double blended_u = next.u(shelf_row, col) + velocity_blend * (target_u - next.u(shelf_row, col));
        double blended_v = next.v(shelf_row, col) + velocity_blend * (target_v - next.v(shelf_row, col));
        next.u(shelf_row, col) =
            move_toward(next.u(shelf_row, col), blended_u, max_speed_step * response_weight);
        next.v(shelf_row, col) =
            move_toward(next.v(shelf_row, col), blended_v, max_speed_step * response_weight);
    }
}

void apply_constriction_upstream_recovery_depth_distribution(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_depth = kConstrictionDepthDistributionMaxDepthPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            double target_h = column_mean_depth * kConstrictionDepthDistributionRecoveryDepthScale;
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionDepthDistributionRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        if (band.count <= throat_width_cells || signed_x > half_length) {
            continue;
        }

        double receiver_scale = signed_x < 0.0 ? kConstrictionDepthDistributionUpstreamDepthScale
                                               : kConstrictionDepthDistributionDownstreamDepthScale;
        double target_h = column_mean_depth * receiver_scale;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h >= target_h) {
                continue;
            }
            double capacity = target_h - current_h;
            if (capacity <= 0.0) {
                continue;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_velocity_energy_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionVelocityTimingMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionVelocityTimingRate * dt, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool upstream = signed_x < 0.0;
        bool downstream_constriction = signed_x >= 0.0 && signed_x <= half_length;
        bool recovery = signed_x > half_length;
        if (!upstream && !downstream_constriction && !recovery) {
            continue;
        }

        double speed_scale = kConstrictionVelocityTimingUpstreamSpeedScale;
        if (downstream_constriction) {
            speed_scale = kConstrictionVelocityTimingDownstreamSpeedScale;
        } else if (recovery) {
            speed_scale = kConstrictionVelocityTimingRecoverySpeedScale;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double initial_u = scenario.initial.u(row, col);
            double target_sign = std::abs(initial_u) > 1.0e-9 ? (initial_u >= 0.0 ? 1.0 : -1.0) : flow_sign;
            double target_abs_u = std::abs(initial_u) * speed_scale;
            if (upstream) {
                double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
                double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
                double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
                double upstream_shape =
                    kConstrictionVelocityTimingUpstreamInteriorSpeedFloor +
                    kConstrictionVelocityTimingUpstreamEdgeSpeedBoost *
                        std::pow(edge_norm, kConstrictionVelocityTimingUpstreamEdgeExponent);
                target_abs_u = std::abs(initial_u) * upstream_shape;
            }
            double blended_u = next.u(row, col) + blend * (target_sign * target_abs_u - next.u(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);

            if (!upstream) {
                double target_v = next.v(row, col) * kConstrictionVelocityTimingCrossStreamDamping;
                double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
                next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
            }
        }
    }
}

}  // namespace raftsim::solver_detail
