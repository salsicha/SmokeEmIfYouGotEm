#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_upstream_upper_shelf_near_throat_reverse_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        std::size_t shelf_row = band.last_row + 1;
        if (next.h(shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            -kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportCrossStreamFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfNearThroatReversePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(shelf_row, col) + velocity_blend * (target_u - next.u(shelf_row, col));
        double blended_v = next.v(shelf_row, col) + velocity_blend * (target_v - next.v(shelf_row, col));
        next.u(shelf_row, col) =
            move_toward(next.u(shelf_row, col), blended_u, max_speed_step * support_weight);
        next.v(shelf_row, col) =
            move_toward(next.v(shelf_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_interior_cross_stream_sign_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        auto shape_row = [&](std::size_t row, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = cross_stream_fraction * reference_speed;
            if (next.v(row, col) >= target_v) {
                return;
            }
            double velocity_blend =
                clamp(
                    kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportVelocityRate * dt *
                        support_weight,
                    0.0,
                    1.0);
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        shape_row(
            band.first_row,
            kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportLowerEdgeFraction);
        shape_row(
            band.first_row + 1,
            kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportLowerInteriorFraction);
        shape_row(
            band.first_row + 2,
            kConstrictionUpstreamInteriorCrossStreamSignPocketFinalSupportMidInteriorFraction);
    }
}

void apply_constriction_upstream_mid_interior_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        auto shape_row = [&](std::size_t row, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
                next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = cross_stream_fraction * reference_speed;
            if (next.v(row, col) >= target_v) {
                return;
            }
            double velocity_blend =
                clamp(
                    kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                        support_weight,
                    0.0,
                    1.0);
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        shape_row(
            kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportLowerRowIndex,
            kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportLowerFraction);
        shape_row(
            kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportUpperRowIndex,
            kConstrictionUpstreamMidInteriorCrossStreamPocketFinalSupportUpperFraction);
    }
}

void apply_constriction_upstream_lower_edge_mid_velocity_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionUpstreamLowerEdgeMidVelocityPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign > 0.0) {
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }
        if (next.v(row, col) > target_v) {
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_recovery_inner_interior_depth_velocity_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto column_for_post_inlet_cell = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        long rounded = std::lround(post_inlet_cell);
        long col =
            flow_sign >= 0.0 ? rounded : static_cast<long>(scenario.grid.nx) - 1 - rounded;
        if (col < 0 || col >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        return static_cast<std::size_t>(col);
    };

    std::optional<std::size_t> donor_col =
        column_for_post_inlet_cell(
            kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row < donor_band.first_row || donor_row > donor_band.last_row ||
        receiver_row < receiver_band.first_row || receiver_row > receiver_band.last_row ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_initial_h = scenario.initial.h(donor_row, *donor_col);
    double receiver_initial_h = scenario.initial.h(receiver_row, *receiver_col);
    if (donor_initial_h <= config.dry_tolerance || receiver_initial_h <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        config.dry_tolerance,
        donor_initial_h *
            kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDonorFloorScale);
    double receiver_target = std::max(
        config.dry_tolerance,
        receiver_initial_h *
            kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverTargetScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(
            donor_capacity,
            std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    double receiver_target_u =
        flow_sign *
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(receiver_row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu =
        receiver_h * next.u(receiver_row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv =
        receiver_h * next.v(receiver_row, *receiver_col) + transfer_h * receiver_target_v;

    next.h(donor_row, *donor_col) =
        std::max(donor_floor, next.h(donor_row, *donor_col) - transfer_h);
    next.h(receiver_row, *receiver_col) = merged_h;
    next.u(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

    double velocity_blend =
        clamp(
            kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportVelocityRate * dt *
                final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;
    auto shape_cell = [&](std::size_t row,
                          std::size_t col,
                          double speed_fraction,
                          double cross_stream_fraction) {
        if (next.h(row, col) <= config.dry_tolerance) {
            return;
        }
        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = cross_stream_fraction * reference_speed;
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
    };

    shape_cell(
        donor_row,
        *donor_col,
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryInnerInteriorDepthVelocityPocketFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_upstream_boundary_lower_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row + 1 >= band.last_row) {
            continue;
        }

        std::size_t row = band.first_row + 1;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamBoundaryLowerInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_far_interior_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            -kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryFarInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_mid_interior_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryMidInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_speed_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeSpeedPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_interior_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionThroatInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionThroatInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count > throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        std::size_t row = kConstrictionThroatInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double raw_fraction =
            kConstrictionThroatInteriorCrossStreamPocketFinalSupportCenterFraction -
            kConstrictionThroatInteriorCrossStreamPocketFinalSupportFractionSlope *
                (post_inlet_cell -
                 kConstrictionThroatInteriorCrossStreamPocketFinalSupportCenterPostInletCell);
        double target_fraction =
            clamp(
                raw_fraction,
                kConstrictionThroatInteriorCrossStreamPocketFinalSupportMinFraction,
                kConstrictionThroatInteriorCrossStreamPocketFinalSupportMaxFraction);
        double target_v = -target_fraction * reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_middle_interior_cross_stream_balance_pocket_final_support(
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
            (response_progress -
             kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count > throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        std::size_t row =
            kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            -kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatMiddleInteriorCrossStreamBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double far_normalized =
            (post_inlet_cell -
             kConstrictionUpstreamInteriorStreamwisePocketFinalSupportFarCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamInteriorStreamwisePocketFinalSupportFarPeakWidthCells);
        double upper_far_normalized =
            (post_inlet_cell -
             kConstrictionUpstreamInteriorStreamwisePocketFinalSupportUpperFarCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamInteriorStreamwisePocketFinalSupportUpperFarPeakWidthCells);
        double throat_normalized =
            (post_inlet_cell -
             kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatPeakWidthCells);
        double far_weight = final_response * std::exp(-(far_normalized * far_normalized));
        double upper_far_weight = final_response * std::exp(-(upper_far_normalized * upper_far_normalized));
        double throat_weight = final_response * std::exp(-(throat_normalized * throat_normalized));
        if (far_weight <= 1.0e-6 && upper_far_weight <= 1.0e-6 && throat_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        auto shape_streamwise = [&](std::size_t row, double target_fraction, double support_weight) {
            if (row >= scenario.grid.ny || support_weight <= 1.0e-6 ||
                next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * target_fraction * reference_speed;
            bool needs_deceleration =
                flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
            if (!needs_deceleration) {
                return;
            }
            double velocity_blend =
                clamp(
                    kConstrictionUpstreamInteriorStreamwisePocketFinalSupportVelocityRate * dt *
                        support_weight,
                    0.0,
                    1.0);
            if (velocity_blend <= 0.0) {
                return;
            }
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        };

        if (far_weight > 1.0e-6 && band.first_row + 3 < band.last_row) {
            double lower_middle_fraction =
                kConstrictionUpstreamInteriorStreamwisePocketFinalSupportLowerMiddleBaseFraction +
                kConstrictionUpstreamInteriorStreamwisePocketFinalSupportLowerMiddleSlopeFraction *
                    std::min(post_inlet_cell, 5.0);
            double center_ramp = std::max(0.0, post_inlet_cell - 2.0);
            double center_fraction =
                std::min(
                    kConstrictionUpstreamInteriorStreamwisePocketFinalSupportCenterMaxFraction,
                    kConstrictionUpstreamInteriorStreamwisePocketFinalSupportCenterQuadraticFraction *
                        center_ramp * center_ramp);

            shape_streamwise(band.first_row + 2, lower_middle_fraction, far_weight);
            shape_streamwise(band.first_row + 3, center_fraction, far_weight);
        }

        if (upper_far_weight > 1.0e-6 && band.last_row >= band.first_row + 3) {
            shape_streamwise(
                band.last_row - 2,
                kConstrictionUpstreamInteriorStreamwisePocketFinalSupportUpperFarFraction,
                upper_far_weight);
        }

        if (throat_weight > 1.0e-6 && band.last_row > band.first_row + 1) {
            double throat_ramp =
                std::max(
                    0.0,
                    post_inlet_cell -
                        kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatCenterPostInletCell);
            double throat_fraction =
                std::min(
                    kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatUpperMaxFraction,
                    kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatUpperBaseFraction +
                        kConstrictionUpstreamInteriorStreamwisePocketFinalSupportThroatUpperSlopeFraction *
                            throat_ramp);
            shape_streamwise(band.last_row - 1, throat_fraction, throat_weight);
        }
    }
}

void apply_constriction_upstream_upper_interior_far_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 1) {
            continue;
        }

        std::size_t row = band.last_row - 1;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperInteriorFarStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_shelf_outer_depth_final_support(
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
            (response_progress -
             kConstrictionUpstreamLowerShelfOuterDepthFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamLowerShelfOuterDepthFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamLowerShelfOuterDepthFinalSupportMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamLowerShelfOuterDepthFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerShelfOuterDepthFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamLowerShelfOuterDepthFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row < 2 ||
            band.last_row + 2 >= scenario.grid.ny) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionDepthTransferCell> donors;
        double donor_capacity = 0.0;
        auto add_donor = [&](std::size_t row, double floor_scale) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double donor_floor = std::max(kConstrictionLocalFringeTargetDepth, column_mean_depth * floor_scale);
            double capacity = std::max(0.0, next.h(row, col) - donor_floor);
            if (capacity > config.dry_tolerance) {
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
        };

        add_donor(
            band.last_row,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportUpperEdgeDonorFloorScale);
        add_donor(
            band.last_row + 1,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportUpperShelfDonorFloorScale);
        add_donor(
            band.last_row + 2,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportOuterUpperShelfDonorFloorScale);

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](
                                std::size_t row,
                                double target_scale,
                                double speed_fraction,
                                double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_h = std::max(kConstrictionLocalFringeTargetDepth, column_mean_depth * target_scale);
            double capacity = std::max(0.0, target_h - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                return;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * speed_fraction * reference_speed,
                cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        add_receiver(
            band.first_row - 2,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportOuterShelfTargetScale,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportOuterShelfSpeedFraction,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportOuterShelfCrossStreamFraction);
        add_receiver(
            band.first_row - 1,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportInnerShelfTargetScale,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportInnerShelfSpeedFraction,
            kConstrictionUpstreamLowerShelfOuterDepthFinalSupportInnerShelfCrossStreamFraction);

        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionUpstreamLowerShelfOuterDepthFinalSupportDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            if (removed_h <= 0.0) {
                continue;
            }
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerShelfOuterDepthFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
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
            if (merged_h <= config.dry_tolerance) {
                next.u(receiver.row, receiver.col) = 0.0;
                next.v(receiver.row, receiver.col) = 0.0;
                continue;
            }
            double merged_u = merged_hu / safe_depth(merged_h, config.dry_tolerance);
            double merged_v = merged_hv / safe_depth(merged_h, config.dry_tolerance);
            double target_u = merged_u + velocity_blend * (receiver.target_u - merged_u);
            double target_v = merged_v + velocity_blend * (receiver.target_v - merged_v);
            next.u(receiver.row, receiver.col) =
                move_toward(merged_u, target_u, max_speed_step * support_weight);
            next.v(receiver.row, receiver.col) =
                move_toward(merged_v, target_v, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_recovery_upper_shelf_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        std::size_t shelf_row = band.last_row + 1;
        if (next.h(shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(shelf_row, col) > target_u : next.u(shelf_row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperShelfStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(shelf_row, col) + velocity_blend * (target_u - next.u(shelf_row, col));
        next.u(shelf_row, col) =
            move_toward(next.u(shelf_row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_center_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row + 3 >= band.last_row) {
            continue;
        }

        std::size_t row = band.first_row + 3;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryCenterInteriorStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_near_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row + 1 < band.first_row || row > band.last_row + 1) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryNearInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_far_interior_momentum_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row + 1 < band.first_row || row > band.last_row + 1) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryFarInteriorMomentumPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_slowdown_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row < band.first_row || row > band.last_row) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorSlowdownPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_late_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row < band.first_row || row > band.last_row) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLateInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_far_upper_edge_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = band.last_row;
        if (row != kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportTargetRowIndex ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryFarUpperEdgeCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_far_upper_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row < band.first_row || row > band.last_row) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryFarUpperInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_mid_upper_interior_streamwise_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryMidUpperInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_lower_interior_cross_stream_pocket_final_support(
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
            (response_progress -
             kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row < band.first_row || row > band.last_row) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerInteriorCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_edge_pocket_depth_final_relief(
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
            (response_progress - kConstrictionRecoveryUpperEdgePocketDepthFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperEdgePocketDepthFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionRecoveryUpperEdgePocketDepthFinalReliefMaxDepthPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell - kConstrictionRecoveryUpperEdgePocketDepthFinalReliefCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperEdgePocketDepthFinalReliefPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        std::size_t donor_row = band.last_row;
        std::size_t receiver_row = band.last_row - 1;
        if (next.h(donor_row, col) <= config.dry_tolerance ||
            next.h(receiver_row, col) <= config.dry_tolerance) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionRecoveryUpperEdgePocketDepthFinalReliefDonorFloorScale);
        double receiver_target = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionRecoveryUpperEdgePocketDepthFinalReliefReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionRecoveryUpperEdgePocketDepthFinalReliefDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

        double receiver_h = next.h(receiver_row, col);
        double merged_h = receiver_h + transfer_h;
        double target_u =
            flow_sign * kConstrictionRecoveryUpperEdgePocketDepthFinalReliefReceiverSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionRecoveryUpperEdgePocketDepthFinalReliefReceiverCrossStreamFraction * reference_speed;
        double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

}  // namespace raftsim::solver_detail
