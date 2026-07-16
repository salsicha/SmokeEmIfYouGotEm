#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_recovery_upper_edge_spillback_depth_pocket_final_relief(
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
             kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefMaxDepthPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        if (!donor_band.found || donor_band.count <= throat_width_cells ||
            donor_band.last_row <= donor_band.first_row) {
            continue;
        }

        std::size_t donor_row = donor_band.last_row;
        if (next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, donor_band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            column_mean_depth *
                kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](int offset_cells, double speed_fraction, double cross_stream_fraction) {
            int receiver_col_signed =
                static_cast<int>(col) - (flow_sign >= 0.0 ? offset_cells : -offset_cells);
            if (receiver_col_signed < 0 ||
                receiver_col_signed >= static_cast<int>(scenario.grid.nx)) {
                return;
            }
            std::size_t receiver_col = static_cast<std::size_t>(receiver_col_signed);
            ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
            if (!receiver_band.found || receiver_band.count <= throat_width_cells ||
                receiver_band.last_row <= receiver_band.first_row) {
                return;
            }
            std::size_t receiver_row = receiver_band.last_row - 1;
            if (receiver_row >= scenario.grid.ny ||
                next.h(receiver_row, receiver_col) <= config.dry_tolerance) {
                return;
            }

            double receiver_target_h = std::max(
                config.dry_tolerance,
                scenario.initial.h(receiver_row, receiver_col) *
                    kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefReceiverTargetScale);
            double capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, receiver_col));
            if (capacity <= config.dry_tolerance) {
                return;
            }

            receivers.push_back(ConstrictionProfileTransferCell{
                receiver_row,
                receiver_col,
                capacity,
                flow_sign * speed_fraction * reference_speed,
                cross_stream_fraction * reference_speed});
            receiver_capacity += capacity;
        };

        add_receiver(
            1,
            kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefNearReceiverSpeedFraction,
            kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefNearReceiverCrossStreamFraction);
        add_receiver(
            2,
            kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefFarReceiverSpeedFraction,
            kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefFarReceiverCrossStreamFraction);
        if (receivers.empty() || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionRecoveryUpperEdgeSpillbackDepthPocketFinalReliefDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            double added_h = transfer_h * receiver.capacity / receiver_capacity;
            double receiver_h = next.h(receiver.row, receiver.col);
            double merged_h = receiver_h + added_h;
            double merged_hu = receiver_h * next.u(receiver.row, receiver.col) +
                               added_h * receiver.target_u;
            double merged_hv = receiver_h * next.v(receiver.row, receiver.col) +
                               added_h * receiver.target_v;
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                : 0.0;
        }
    }
}

void apply_constriction_recovery_upper_edge_near_spillback_depth_pocket_final_relief(
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
             kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefMaxDepthPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefPeakWidthCells);
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
            config.dry_tolerance,
            column_mean_depth *
                kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefDonorFloorScale);
        double receiver_target = std::max(
            config.dry_tolerance,
            scenario.initial.h(receiver_row, col) *
                kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefDepthRate *
            dt * support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

        double receiver_h = next.h(receiver_row, col);
        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefReceiverSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionRecoveryUpperEdgeNearSpillbackDepthPocketFinalReliefReceiverCrossStreamFraction *
            reference_speed;
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                            : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                            : 0.0;
    }
}

void apply_constriction_recovery_upper_interior_cross_stream_pocket_final_support(
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
             kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        std::size_t row = band.last_row - 1;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_edge_velocity_pocket_final_support(
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
            (response_progress - kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportMaxSpeedPerSecond * dt * final_response;

    auto gaussian_weight = [&](double post_inlet_cell, double center_cell) {
        double normalized_distance =
            (post_inlet_cell - center_cell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportPeakWidthCells);
        return final_response * std::exp(-(normalized_distance * normalized_distance));
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double near_weight =
            gaussian_weight(
                post_inlet_cell,
                kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportNearCenterPostInletCell);
        double far_weight =
            gaussian_weight(
                post_inlet_cell,
                kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportFarCenterPostInletCell);
        if (std::max(near_weight, far_weight) <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = band.last_row;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        auto shape_velocity = [&](double speed_fraction, double cross_stream_fraction, double support_weight) {
            if (support_weight <= 1.0e-6) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double velocity_blend =
                clamp(
                    kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportVelocityRate * dt *
                        support_weight,
                    0.0,
                    1.0);
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        shape_velocity(
            kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportNearSpeedFraction,
            kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportNearCrossStreamFraction,
            near_weight);
        shape_velocity(
            kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportFarSpeedFraction,
            kConstrictionRecoveryUpperEdgeVelocityPocketFinalSupportFarCrossStreamFraction,
            far_weight);
    }
}

void apply_constriction_recovery_upper_edge_speed_pocket_final_support(
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
            (response_progress - kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = band.last_row;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportCrossStreamFraction * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperEdgeSpeedPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_cross_stream_pocket_final_support(
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
            (response_progress - kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell - kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t lower_edge_row = band.first_row;
        if (next.h(lower_edge_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportCrossStreamFraction * reference_speed;
        if (next.v(lower_edge_row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v =
            next.v(lower_edge_row, col) + velocity_blend * (target_v - next.v(lower_edge_row, col));
        next.v(lower_edge_row, col) =
            move_toward(next.v(lower_edge_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_momentum_pocket_final_support(
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
             kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (row + 1 < band.first_row || row > band.last_row + 1) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeMomentumPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_boundary_momentum_pocket_final_support(
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
             kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance ||
            row < band.first_row || row > band.last_row) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportCrossStreamFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeBoundaryMomentumPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_outer_lower_shelf_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row < 2) {
            continue;
        }

        std::size_t outer_lower_shelf_row = band.first_row - 2;
        if (next.h(outer_lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(outer_lower_shelf_row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamOuterLowerShelfCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v =
            next.v(outer_lower_shelf_row, col) +
            velocity_blend * (target_v - next.v(outer_lower_shelf_row, col));
        next.v(outer_lower_shelf_row, col) =
            move_toward(
                next.v(outer_lower_shelf_row, col),
                blended_v,
                max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_boundary_outer_lower_shelf_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row < 2) {
            continue;
        }

        std::size_t outer_lower_shelf_row = band.first_row - 2;
        if (next.h(outer_lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(outer_lower_shelf_row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamBoundaryOuterLowerShelfCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v =
            next.v(outer_lower_shelf_row, col) +
            velocity_blend * (target_v - next.v(outer_lower_shelf_row, col));
        next.v(outer_lower_shelf_row, col) =
            move_toward(
                next.v(outer_lower_shelf_row, col),
                blended_v,
                max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_outer_lower_shelf_streamwise_pocket_final_support(
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
            (response_progress - kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double distance =
            post_inlet_cell - kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportCenterPostInletCell;
        double width =
            distance < 0.0
                ? kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportUpstreamPeakWidthCells
                : kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportDownstreamPeakWidthCells;
        double normalized_distance = distance / std::max(1.0e-9, width);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row < 2) {
            continue;
        }

        std::size_t outer_lower_shelf_row = band.first_row - 2;
        if (next.h(outer_lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(outer_lower_shelf_row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamOuterLowerShelfStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u =
            next.u(outer_lower_shelf_row, col) +
            velocity_blend * (target_u - next.u(outer_lower_shelf_row, col));
        next.u(outer_lower_shelf_row, col) =
            move_toward(
                next.u(outer_lower_shelf_row, col),
                blended_u,
                max_speed_step * support_weight);
    }
}

void apply_constriction_downstream_interior_streamwise_pocket_final_support(
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
            (response_progress - kConstrictionDownstreamInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionDownstreamInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double distance =
            post_inlet_cell - kConstrictionDownstreamInteriorStreamwisePocketFinalSupportCenterPostInletCell;
        double width =
            distance < 0.0 ? kConstrictionDownstreamInteriorStreamwisePocketFinalSupportUpstreamPeakWidthCells
                           : kConstrictionDownstreamInteriorStreamwisePocketFinalSupportDownstreamPeakWidthCells;
        double normalized_distance = distance / std::max(1.0e-9, width);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 3) {
            continue;
        }

        std::size_t first_row = band.first_row + 1;
        std::size_t last_row = std::min<std::size_t>(band.first_row + 3, band.last_row - 1);
        double target_u =
            flow_sign * kConstrictionDownstreamInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionDownstreamInteriorStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);

        for (std::size_t row = first_row; row <= last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance ||
                (target_u - next.u(row, col)) * flow_sign <= 0.0) {
                continue;
            }

            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_downstream_interior_velocity_balance_pocket_final_support(
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
             kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamInteriorVelocityBalancePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_downstream_middle_interior_velocity_balance_pocket_final_support(
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
             kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_streamwise_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (needs_streamwise_acceleration) {
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }

        double target_v =
            kConstrictionDownstreamMiddleInteriorVelocityBalancePocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) < target_v) {
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_downstream_interior_momentum_depth_pocket_final_support(
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
             kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        if (!donor_band.found || donor_band.count <= throat_width_cells ||
            donor_band.last_row <= donor_band.first_row +
                                       kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportDonorRowOffset) {
            continue;
        }

        int receiver_col_signed =
            static_cast<int>(col) + (flow_sign >= 0.0 ? 1 : -1);
        if (receiver_col_signed < 0 ||
            receiver_col_signed >= static_cast<int>(scenario.grid.nx)) {
            continue;
        }
        std::size_t receiver_col = static_cast<std::size_t>(receiver_col_signed);
        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
        if (!receiver_band.found || receiver_band.count <= throat_width_cells ||
            receiver_band.last_row <=
                receiver_band.first_row +
                    kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportLastReceiverRowOffset) {
            continue;
        }

        std::size_t donor_row =
            donor_band.first_row +
            kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportDonorRowOffset;
        if (donor_row >= scenario.grid.ny || next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor =
            std::max(
                config.dry_tolerance,
                scenario.initial.h(donor_row, col) *
                    kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportDonorTargetDepthScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        double target_u =
            flow_sign *
            kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportReceiverSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportReceiverCrossStreamFraction *
            reference_speed;
        for (std::size_t offset =
                 kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportFirstReceiverRowOffset;
             offset <= kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportLastReceiverRowOffset;
             ++offset) {
            std::size_t receiver_row = receiver_band.first_row + offset;
            if (receiver_row >= scenario.grid.ny || receiver_row > receiver_band.last_row ||
                next.h(receiver_row, receiver_col) <= config.dry_tolerance) {
                continue;
            }

            double receiver_target_h =
                std::max(
                    config.dry_tolerance,
                    scenario.initial.h(receiver_row, receiver_col) *
                        kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportReceiverTargetDepthScale);
            double capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, receiver_col));
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                receiver_row, receiver_col, capacity, target_u, target_v});
            receiver_capacity += capacity;
        }

        if (receivers.empty() || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionDownstreamInteriorMomentumDepthPocketFinalSupportDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);
        if (next.h(donor_row, col) <= config.dry_tolerance) {
            next.h(donor_row, col) = 0.0;
            next.u(donor_row, col) = 0.0;
            next.v(donor_row, col) = 0.0;
        }

        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            double added_h = transfer_h * receiver.capacity / receiver_capacity;
            double current_h = next.h(receiver.row, receiver.col);
            double merged_h = current_h + added_h;
            double merged_hu = current_h * next.u(receiver.row, receiver.col) +
                               added_h * receiver.target_u;
            double merged_hv = current_h * next.v(receiver.row, receiver.col) +
                               added_h * receiver.target_v;
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                : 0.0;
        }
    }
}

void apply_constriction_downstream_upper_interior_velocity_pocket_final_support(
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
             kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportCrossStreamFraction *
            reference_speed;
        bool needs_streamwise_slowdown =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        bool needs_cross_stream_slowdown = next.v(row, col) > target_v;
        if (!needs_streamwise_slowdown && !needs_cross_stream_slowdown) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamUpperInteriorVelocityPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        if (needs_streamwise_slowdown) {
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }
        if (needs_cross_stream_slowdown) {
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_downstream_interior_cross_stream_pocket_final_support(
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
             kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamInteriorCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_downstream_middle_interior_streamwise_relief_pocket_final_support(
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
             kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t first_row =
            std::max(kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportFirstRowIndex,
                     band.first_row);
        std::size_t last_row =
            std::min(kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportLastRowIndex,
                     band.last_row);
        if (first_row > last_row) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportSpeedFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionDownstreamMiddleInteriorStreamwiseReliefPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        for (std::size_t row = first_row; row <= last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            bool needs_streamwise_deceleration =
                flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
            if (!needs_streamwise_deceleration) {
                continue;
            }

            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_downstream_lower_interior_streamwise_pocket_final_support(
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
             kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamLowerInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_interior_streamwise_pocket_final_support(
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
             kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_middle_interior_streamwise_pocket_final_support(
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
             kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperMiddleInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_middle_interior_cross_stream_slowdown_pocket_final_support(
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
             kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryMiddleInteriorCrossStreamSlowdownPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_interior_depth_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportResponseStart),
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
            kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row < donor_band.first_row || donor_row > donor_band.last_row ||
        receiver_row + 1 != receiver_band.first_row ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, *donor_col);
    if (donor_mean_depth <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        config.dry_tolerance,
        donor_mean_depth *
            kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDonorFloorScale);
    double receiver_target = std::max(
        config.dry_tolerance,
        donor_mean_depth *
            kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverTargetScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDepthRate * dt *
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
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverCrossStreamFraction *
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
            kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;
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
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDonorSpeedFraction,
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverSpeedFraction,
        kConstrictionUpstreamUpperInteriorDepthCrossStreamPocketFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_upstream_upper_shelf_depth_streamwise_pocket_final_support(
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
             kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportResponseStart),
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
            kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row != donor_band.last_row + 1 ||
        receiver_row != receiver_band.last_row + 2 ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, *donor_col);
    double receiver_mean_depth = initial_column_mean_depth(scenario, receiver_band, *receiver_col);
    if (donor_mean_depth <= config.dry_tolerance || receiver_mean_depth <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        config.dry_tolerance,
        donor_mean_depth *
            kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDonorFloorScale);
    double receiver_target = std::max(
        config.dry_tolerance,
        receiver_mean_depth *
            kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverTargetScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDepthRate * dt *
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
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverCrossStreamFraction *
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
            kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;
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
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDonorSpeedFraction,
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverSpeedFraction,
        kConstrictionUpstreamUpperShelfDepthStreamwisePocketFinalSupportReceiverCrossStreamFraction);
}

}  // namespace raftsim::solver_detail
