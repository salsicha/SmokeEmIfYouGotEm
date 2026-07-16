#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_throat_interior_streamwise_pocket_final_support(
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
             kConstrictionThroatInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionThroatInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionThroatInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_lower_edge_cross_stream_pocket_final_support(
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
             kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatLowerEdgeCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_lower_edge_entry_streamwise_relief_pocket_final_support(
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
             kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatLowerEdgeEntryStreamwiseReliefPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_lower_edge_streamwise_relief_pocket_final_support(
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
             kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatLowerEdgeStreamwiseReliefPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_interior_depth_relief_pocket_final_support(
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
             kConstrictionThroatInteriorDepthReliefPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionThroatInteriorDepthReliefPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto post_inlet_column = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        double raw_col =
            flow_sign >= 0.0 ? post_inlet_cell
                             : static_cast<double>(scenario.grid.nx - 1) - post_inlet_cell;
        long rounded = std::lround(raw_col);
        if (rounded < 0 || rounded >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        return static_cast<std::size_t>(rounded);
    };

    std::optional<std::size_t> donor_col =
        post_inlet_column(kConstrictionThroatInteriorDepthReliefPocketFinalSupportDonorPostInletCell);
    if (!donor_col) {
        return;
    }

    std::size_t donor_row = kConstrictionThroatInteriorDepthReliefPocketFinalSupportDonorRowIndex;
    if (donor_row >= scenario.grid.ny || next.h(donor_row, *donor_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    if (!donor_band.found || donor_band.count < throat_width_cells || donor_row < donor_band.first_row ||
        donor_row > donor_band.last_row) {
        return;
    }

    double donor_column_mean_depth = initial_column_mean_depth(scenario, donor_band, *donor_col);
    if (donor_column_mean_depth <= config.dry_tolerance) {
        return;
    }

    double donor_floor =
        std::max(
            kConstrictionLocalFringeTargetDepth,
            donor_column_mean_depth * kConstrictionThroatInteriorDepthReliefPocketFinalSupportDonorFloorScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    if (donor_capacity <= config.dry_tolerance) {
        return;
    }

    std::vector<ConstrictionProfileTransferCell> receivers;
    double receiver_capacity = 0.0;
    auto add_receiver = [&](double post_inlet_cell,
                            double target_scale,
                            double speed_fraction,
                            double cross_stream_fraction) {
        std::optional<std::size_t> receiver_col = post_inlet_column(post_inlet_cell);
        std::size_t receiver_row = kConstrictionThroatInteriorDepthReliefPocketFinalSupportReceiverRowIndex;
        if (!receiver_col || receiver_row >= scenario.grid.ny ||
            next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
            return;
        }

        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
        if (!receiver_band.found || receiver_band.count < throat_width_cells ||
            receiver_row < receiver_band.first_row || receiver_row > receiver_band.last_row) {
            return;
        }

        double receiver_column_mean_depth =
            initial_column_mean_depth(scenario, receiver_band, *receiver_col);
        if (receiver_column_mean_depth <= config.dry_tolerance) {
            return;
        }

        double target_h =
            std::max(kConstrictionLocalFringeTargetDepth, receiver_column_mean_depth * target_scale);
        double capacity = std::max(0.0, target_h - next.h(receiver_row, *receiver_col));
        if (capacity <= config.dry_tolerance) {
            return;
        }

        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = cross_stream_fraction * reference_speed;
        receivers.push_back(
            ConstrictionProfileTransferCell{receiver_row, *receiver_col, capacity, target_u, target_v});
        receiver_capacity += capacity;
    };

    add_receiver(
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportLowerEdgeReceiverPostInletCell,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportLowerEdgeReceiverTargetScale,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportLowerEdgeReceiverSpeedFraction,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportLowerEdgeReceiverCrossStreamFraction);
    add_receiver(
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportNearEdgeReceiverPostInletCell,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportNearEdgeReceiverTargetScale,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportNearEdgeReceiverSpeedFraction,
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportNearEdgeReceiverCrossStreamFraction);

    if (receiver_capacity <= config.dry_tolerance || receivers.empty()) {
        return;
    }

    double requested_h =
        receiver_capacity * kConstrictionThroatInteriorDepthReliefPocketFinalSupportDepthRate *
        dt * final_response;
    double max_depth_step =
        kConstrictionThroatInteriorDepthReliefPocketFinalSupportMaxDepthPerSecond * dt * final_response;
    double transfer_h =
        std::min(donor_capacity, std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    next.h(donor_row, *donor_col) =
        std::max(donor_floor, next.h(donor_row, *donor_col) - transfer_h);

    for (const ConstrictionProfileTransferCell& receiver : receivers) {
        double added_h = transfer_h * receiver.capacity / receiver_capacity;
        if (added_h <= config.dry_tolerance) {
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

void apply_constriction_recovery_upper_interior_to_lower_shelf_depth_pocket_final_support(
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
             kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto post_inlet_column = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        double raw_col =
            flow_sign >= 0.0 ? post_inlet_cell
                             : static_cast<double>(scenario.grid.nx - 1) - post_inlet_cell;
        long rounded = std::lround(raw_col);
        if (rounded < 0 || rounded >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        return static_cast<std::size_t>(rounded);
    };

    std::optional<std::size_t> donor_col = post_inlet_column(
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col = post_inlet_column(
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportDonorRowIndex;
    if (donor_row >= scenario.grid.ny || next.h(donor_row, *donor_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found || donor_band.count <= throat_width_cells ||
        receiver_band.count <= throat_width_cells || receiver_band.first_row == 0 ||
        donor_row < donor_band.first_row || donor_row > donor_band.last_row) {
        return;
    }

    std::size_t receiver_row = receiver_band.first_row - 1;
    if (next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_column_mean_depth = initial_column_mean_depth(scenario, donor_band, *donor_col);
    double receiver_column_mean_depth =
        initial_column_mean_depth(scenario, receiver_band, *receiver_col);
    if (donor_column_mean_depth <= config.dry_tolerance ||
        receiver_column_mean_depth <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        kConstrictionLocalFringeTargetDepth,
        donor_column_mean_depth *
            kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportDonorFloorScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_target_h = std::max(
        kConstrictionLocalFringeTargetDepth,
        receiver_column_mean_depth *
            kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportReceiverTargetScale);
    double receiver_capacity =
        std::max(0.0, receiver_target_h - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportDepthRate * dt *
        final_response;
    double max_depth_step =
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double transfer_h =
        std::min(donor_capacity, std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    next.h(donor_row, *donor_col) =
        std::max(donor_floor, next.h(donor_row, *donor_col) - transfer_h);

    double receiver_h = next.h(receiver_row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double target_u =
        flow_sign *
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportReceiverSpeedFraction *
        reference_speed;
    double target_v =
        kConstrictionRecoveryUpperInteriorToLowerShelfDepthPocketFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double merged_hu = receiver_h * next.u(receiver_row, *receiver_col) + transfer_h * target_u;
    double merged_hv = receiver_h * next.v(receiver_row, *receiver_col) + transfer_h * target_v;
    next.h(receiver_row, *receiver_col) = merged_h;
    next.u(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
}

void apply_constriction_recovery_lower_interior_streamwise_pocket_final_support(
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
             kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_streamwise_pocket_final_support(
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
             kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_middle_interior_streamwise_pocket_final_support(
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
             kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatMiddleInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_near_throat_interior_streamwise_pocket_final_support(
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
             kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamNearThroatInteriorStreamwisePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_late_lower_edge_cross_stream_pocket_final_support(
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
             kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLateLowerEdgeCrossStreamPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_center_interior_streamwise_relief_pocket_final_support(
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
             kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_streamwise_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_streamwise_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryCenterInteriorStreamwiseReliefPocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_center_interior_velocity_balance_pocket_final_support(
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
             kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_streamwise_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (needs_streamwise_deceleration) {
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        }

        double target_v =
            kConstrictionRecoveryCenterInteriorVelocityBalancePocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) > target_v) {
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        }
    }
}

void apply_constriction_recovery_lower_interior_cross_stream_balance_pocket_final_support(
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
             kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerInteriorCrossStreamBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_streamwise_balance_pocket_final_support(
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
             kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorStreamwiseBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_lower_shelf_cross_stream_balance_pocket_final_support(
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
             kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportTargetRowIndex;
        bool row_in_initial_wet_band = row >= band.first_row && row <= band.last_row;
        bool row_is_lower_shelf = row + 1 == band.first_row;
        if (row >= scenario.grid.ny || (!row_in_initial_wet_band && !row_is_lower_shelf) ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatLowerShelfCrossStreamBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_throat_interior_streamwise_balance_pocket_final_support(
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
             kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatInteriorStreamwiseBalancePocketFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_outer_lower_shelf_depth_balance_pocket_final_support(
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
             kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto column_from_post_inlet = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        long rounded_cell = std::lround(post_inlet_cell);
        if (rounded_cell < 0 || rounded_cell >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        std::size_t post_index = static_cast<std::size_t>(rounded_cell);
        return flow_sign >= 0.0 ? post_index : scenario.grid.nx - 1 - post_index;
    };

    std::optional<std::size_t> donor_col =
        column_from_post_inlet(kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportDonorPostInletCell);
    if (!donor_col.has_value()) {
        return;
    }

    std::size_t row =
        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportTargetRowIndex;
    if (row >= scenario.grid.ny || next.h(row, *donor_col) <= config.dry_tolerance) {
        return;
    }

    double donor_floor = kConstrictionLocalFringeTargetDepth;
    double donor_capacity = std::max(0.0, next.h(row, *donor_col) - donor_floor);
    if (donor_capacity <= config.dry_tolerance) {
        return;
    }

    struct ShelfReceiver {
        double post_inlet_cell;
        double target_depth;
        double speed_fraction;
        double cross_stream_fraction;
    };

    std::array<ShelfReceiver, 2> receiver_specs{{
        ShelfReceiver{
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportPrimaryReceiverPostInletCell,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportPrimaryReceiverTargetDepth,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportPrimaryReceiverSpeedFraction,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportPrimaryReceiverCrossStreamFraction,
        },
        ShelfReceiver{
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportSecondaryReceiverPostInletCell,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportSecondaryReceiverTargetDepth,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportSecondaryReceiverSpeedFraction,
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportSecondaryReceiverCrossStreamFraction,
        },
    }};

    std::vector<ConstrictionProfileTransferCell> receivers;
    double receiver_capacity = 0.0;
    for (const ShelfReceiver& spec : receiver_specs) {
        std::optional<std::size_t> receiver_col = column_from_post_inlet(spec.post_inlet_cell);
        if (!receiver_col.has_value() || *receiver_col == *donor_col ||
            next.h(row, *receiver_col) <= config.dry_tolerance) {
            continue;
        }
        double target_depth = std::max(kConstrictionLocalFringeTargetDepth, spec.target_depth);
        double capacity = std::max(0.0, target_depth - next.h(row, *receiver_col));
        if (capacity <= config.dry_tolerance) {
            continue;
        }
        receivers.push_back(ConstrictionProfileTransferCell{
            row,
            *receiver_col,
            capacity,
            flow_sign * spec.speed_fraction * reference_speed,
            spec.cross_stream_fraction * reference_speed,
        });
        receiver_capacity += capacity;
    }

    if (receivers.empty() || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(donor_capacity, std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    next.h(row, *donor_col) = std::max(donor_floor, next.h(row, *donor_col) - transfer_h);

    for (const ConstrictionProfileTransferCell& receiver : receivers) {
        double added_h = transfer_h * receiver.capacity / receiver_capacity;
        if (added_h <= 0.0) {
            continue;
        }
        double current_h = next.h(receiver.row, receiver.col);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }

    double max_speed_step =
        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;
    double velocity_blend =
        clamp(
            kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportVelocityRate * dt *
                final_response,
            0.0,
            1.0);
    double donor_target_u =
        flow_sign * kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportDonorSpeedFraction *
        reference_speed;
    double donor_target_v =
        kConstrictionUpstreamOuterLowerShelfDepthBalancePocketFinalSupportDonorCrossStreamFraction *
        reference_speed;
    double blended_u = next.u(row, *donor_col) + velocity_blend * (donor_target_u - next.u(row, *donor_col));
    double blended_v = next.v(row, *donor_col) + velocity_blend * (donor_target_v - next.v(row, *donor_col));
    next.u(row, *donor_col) = move_toward(next.u(row, *donor_col), blended_u, max_speed_step);
    next.v(row, *donor_col) = move_toward(next.v(row, *donor_col), blended_v, max_speed_step);
}

void apply_constriction_throat_upper_edge_depth_balance_pocket_final_support(
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
             kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto column_from_post_inlet = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        long rounded_cell = std::lround(post_inlet_cell);
        if (rounded_cell < 0 || rounded_cell >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        std::size_t post_index = static_cast<std::size_t>(rounded_cell);
        return flow_sign >= 0.0 ? post_index : scenario.grid.nx - 1 - post_index;
    };

    std::optional<std::size_t> donor_col =
        column_from_post_inlet(kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportDonorPostInletCell);
    if (!donor_col.has_value()) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    if (!donor_band.found || donor_band.count != throat_width_cells ||
        donor_band.last_row + 1 >= scenario.grid.ny) {
        return;
    }

    std::size_t donor_row = donor_band.last_row;
    if (next.h(donor_row, *donor_col) <= config.dry_tolerance) {
        return;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, donor_band, *donor_col);
    if (column_mean_depth <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        kConstrictionLocalFringeTargetDepth,
        column_mean_depth * kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportDonorFloorScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    if (donor_capacity <= config.dry_tolerance) {
        return;
    }

    std::vector<ConstrictionProfileTransferCell> receivers;
    double receiver_capacity = 0.0;
    for (double post_inlet_cell =
             kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportFirstReceiverPostInletCell;
         post_inlet_cell <=
         kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportLastReceiverPostInletCell +
             1.0e-9;
         post_inlet_cell += 1.0) {
        std::optional<std::size_t> receiver_col = column_from_post_inlet(post_inlet_cell);
        if (!receiver_col.has_value() || *receiver_col == *donor_col) {
            continue;
        }

        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
        if (!receiver_band.found || receiver_band.count != throat_width_cells ||
            receiver_band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        std::size_t receiver_row = receiver_band.last_row + 1;
        double capacity = std::max(
            0.0,
            kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportReceiverTargetDepth -
                next.h(receiver_row, *receiver_col));
        if (capacity <= config.dry_tolerance) {
            continue;
        }

        receivers.push_back(ConstrictionProfileTransferCell{
            receiver_row,
            *receiver_col,
            capacity,
            flow_sign * kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportReceiverSpeedFraction *
                reference_speed,
            -kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportReceiverCrossStreamFraction *
                reference_speed,
        });
        receiver_capacity += capacity;
    }

    if (receivers.empty() || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double requested_h =
        receiver_capacity * kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(donor_capacity, std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    next.h(donor_row, *donor_col) = std::max(donor_floor, next.h(donor_row, *donor_col) - transfer_h);

    for (const ConstrictionProfileTransferCell& receiver : receivers) {
        double added_h = transfer_h * receiver.capacity / receiver_capacity;
        if (added_h <= 0.0) {
            continue;
        }
        double current_h = next.h(receiver.row, receiver.col);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }

    double max_speed_step =
        kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;
    double velocity_blend =
        clamp(
            kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportVelocityRate * dt *
                final_response,
            0.0,
            1.0);
    double donor_target_u =
        flow_sign * kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportDonorSpeedFraction *
        reference_speed;
    double donor_target_v =
        -kConstrictionThroatUpperEdgeDepthBalancePocketFinalSupportDonorCrossStreamFraction *
        reference_speed;
    double blended_u =
        next.u(donor_row, *donor_col) + velocity_blend * (donor_target_u - next.u(donor_row, *donor_col));
    double blended_v =
        next.v(donor_row, *donor_col) + velocity_blend * (donor_target_v - next.v(donor_row, *donor_col));
    next.u(donor_row, *donor_col) =
        move_toward(next.u(donor_row, *donor_col), blended_u, max_speed_step);
    next.v(donor_row, *donor_col) =
        move_toward(next.v(donor_row, *donor_col), blended_v, max_speed_step);
}

void apply_constriction_recovery_middle_interior_to_upstream_lower_edge_depth_balance_pocket_final_support(
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
             kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto column_from_post_inlet = [&](double post_inlet_cell) -> std::optional<std::size_t> {
        long rounded_cell = std::lround(post_inlet_cell);
        if (rounded_cell < 0 || rounded_cell >= static_cast<long>(scenario.grid.nx)) {
            return std::nullopt;
        }
        std::size_t post_index = static_cast<std::size_t>(rounded_cell);
        return flow_sign >= 0.0 ? post_index : scenario.grid.nx - 1 - post_index;
    };

    std::optional<std::size_t> donor_col =
        column_from_post_inlet(
            kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_from_post_inlet(
            kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportReceiverPostInletCell);
    if (!donor_col.has_value() || !receiver_col.has_value()) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found || donor_band.count <= throat_width_cells ||
        receiver_band.count <= throat_width_cells) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        donor_row <= donor_band.first_row || donor_row >= donor_band.last_row ||
        receiver_row < receiver_band.first_row || receiver_row > receiver_band.last_row ||
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
        kConstrictionLocalFringeTargetDepth,
        donor_mean_depth *
            kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDonorFloorScale);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_target_h =
        receiver_mean_depth *
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportReceiverTargetScale;
    double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(donor_capacity, std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    next.h(donor_row, *donor_col) =
        std::max(donor_floor, next.h(donor_row, *donor_col) - transfer_h);

    double receiver_h = next.h(receiver_row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double receiver_target_u =
        flow_sign *
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double merged_hu = receiver_h * next.u(receiver_row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv = receiver_h * next.v(receiver_row, *receiver_col) + transfer_h * receiver_target_v;
    next.h(receiver_row, *receiver_col) = merged_h;
    next.u(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportMaxSpeedPerSecond *
        dt * final_response;
    double velocity_blend =
        clamp(
            kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double donor_target_u =
        flow_sign *
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDonorSpeedFraction *
        reference_speed;
    double donor_target_v =
        kConstrictionRecoveryMiddleInteriorToUpstreamLowerEdgeDepthBalancePocketFinalSupportDonorCrossStreamFraction *
        reference_speed;
    double blended_u =
        next.u(donor_row, *donor_col) + velocity_blend * (donor_target_u - next.u(donor_row, *donor_col));
    double blended_v =
        next.v(donor_row, *donor_col) + velocity_blend * (donor_target_v - next.v(donor_row, *donor_col));
    next.u(donor_row, *donor_col) =
        move_toward(next.u(donor_row, *donor_col), blended_u, max_speed_step);
    next.v(donor_row, *donor_col) =
        move_toward(next.v(donor_row, *donor_col), blended_v, max_speed_step);
}

void apply_constriction_throat_lower_edge_cross_stream_balance_final_support(
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
            (response_progress - kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatLowerEdgeCrossStreamBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_interior_velocity_balance_final_support(
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
             kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionUpstreamUpperInteriorVelocityBalanceFinalSupportCrossStreamFraction *
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

void apply_constriction_recovery_middle_interior_cross_stream_balance_final_support(
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
             kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryMiddleInteriorCrossStreamBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_middle_interior_streamwise_balance_final_support(
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
             kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerMiddleInteriorStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_shelf_cross_stream_balance_final_support(
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
             kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfCrossStreamBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

}  // namespace raftsim::solver_detail
