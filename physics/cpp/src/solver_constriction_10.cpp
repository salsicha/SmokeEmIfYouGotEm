#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_recovery_middle_interior_to_upstream_interior_depth_balance_final_support(
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
             kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportResponseStart),
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
            kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row <= donor_band.first_row || donor_row >= donor_band.last_row ||
        receiver_row <= receiver_band.first_row || receiver_row >= receiver_band.last_row) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDepthRate *
        dt * final_response;
    double transfer_h =
        std::min(
            donor_capacity,
            std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    double receiver_target_u =
        flow_sign *
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(receiver_row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu =
        receiver_h * next.u(receiver_row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv =
        receiver_h * next.v(receiver_row, *receiver_col) + transfer_h * receiver_target_v;

    next.h(donor_row, *donor_col) =
        std::max(donor_target, next.h(donor_row, *donor_col) - transfer_h);
    next.h(receiver_row, *receiver_col) = merged_h;
    next.u(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

    double velocity_blend =
        clamp(
            kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportMaxSpeedPerSecond *
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
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryMiddleInteriorToUpstreamInteriorDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_upstream_inner_upper_edge_streamwise_balance_final_support(
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
             kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInnerUpperEdgeStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_depth_balance_final_support(
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
             kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportResponseStart),
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
            kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row <= donor_band.first_row || donor_row >= donor_band.last_row ||
        receiver_row < receiver_band.first_row || receiver_row > receiver_band.last_row) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportDepthRate * dt *
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
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryUpperInteriorDepthBalanceFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(receiver_row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu =
        receiver_h * next.u(receiver_row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv =
        receiver_h * next.v(receiver_row, *receiver_col) + transfer_h * receiver_target_v;

    next.h(donor_row, *donor_col) =
        std::max(donor_target, next.h(donor_row, *donor_col) - transfer_h);
    next.h(receiver_row, *receiver_col) = merged_h;
    next.u(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
}

void apply_constriction_lower_edge_face_depth_balance_final_support(
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
             kConstrictionLowerEdgeFaceDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportResponseStart),
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

    std::optional<std::size_t> primary_donor_col =
        column_for_post_inlet_cell(
            kConstrictionLowerEdgeFaceDepthBalanceFinalSupportPrimaryDonorPostInletCell);
    std::optional<std::size_t> secondary_donor_col =
        column_for_post_inlet_cell(
            kConstrictionLowerEdgeFaceDepthBalanceFinalSupportSecondaryDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionLowerEdgeFaceDepthBalanceFinalSupportReceiverPostInletCell);
    if (!primary_donor_col || !secondary_donor_col || !receiver_col) {
        return;
    }

    struct DepthDonor {
        std::size_t row;
        std::size_t col;
        double floor_h;
        double capacity;
    };
    struct DepthReceiver {
        std::size_t row;
        std::size_t col;
        double target_h;
        double speed_fraction;
        double cross_stream_fraction;
        double capacity;
    };

    std::vector<DepthDonor> donors;
    double donor_capacity = 0.0;
    auto add_donor = [&](std::optional<std::size_t> col, double floor_h) {
        if (!col) {
            return;
        }
        std::size_t row = kConstrictionLowerEdgeFaceDepthBalanceFinalSupportDonorRowIndex;
        if (row >= scenario.grid.ny || next.h(row, *col) <= config.dry_tolerance) {
            return;
        }
        ColumnWetBand band = initial_wet_band_in_column(scenario, *col);
        if (!band.found || band.count <= throat_width_cells ||
            row <= band.first_row || row >= band.last_row) {
            return;
        }
        double floor_depth = std::max(config.dry_tolerance, floor_h);
        double capacity = std::max(0.0, next.h(row, *col) - floor_depth);
        if (capacity <= config.dry_tolerance) {
            return;
        }
        donors.push_back(DepthDonor{row, *col, floor_depth, capacity});
        donor_capacity += capacity;
    };
    add_donor(
        primary_donor_col,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportPrimaryDonorTargetDepth);
    add_donor(
        secondary_donor_col,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportSecondaryDonorTargetDepth);

    std::vector<DepthReceiver> receivers;
    double receiver_capacity = 0.0;
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    std::size_t lower_shelf_row =
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerShelfRowIndex;
    std::size_t lower_edge_row =
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerEdgeRowIndex;
    if (!receiver_band.found || receiver_band.count <= throat_width_cells ||
        receiver_band.first_row != lower_edge_row ||
        lower_shelf_row + 1 != lower_edge_row) {
        return;
    }
    auto add_receiver = [&](std::size_t row,
                            double target_h,
                            double speed_fraction,
                            double cross_stream_fraction) {
        if (row >= scenario.grid.ny || next.h(row, *receiver_col) <= config.dry_tolerance) {
            return;
        }
        double bounded_target = std::max(config.dry_tolerance, target_h);
        double capacity = std::max(0.0, bounded_target - next.h(row, *receiver_col));
        if (capacity <= config.dry_tolerance) {
            return;
        }
        receivers.push_back(DepthReceiver{
            row,
            *receiver_col,
            bounded_target,
            speed_fraction,
            cross_stream_fraction,
            capacity});
        receiver_capacity += capacity;
    };
    add_receiver(
        lower_shelf_row,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerShelfTargetDepth,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerShelfSpeedFraction,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerShelfCrossStreamFraction);
    add_receiver(
        lower_edge_row,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerEdgeTargetDepth,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerEdgeSpeedFraction,
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportLowerEdgeCrossStreamFraction);
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionLowerEdgeFaceDepthBalanceFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(
            donor_capacity,
            std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    for (const DepthDonor& donor : donors) {
        double removed_h = transfer_h * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) =
            std::max(donor.floor_h, next.h(donor.row, donor.col) - removed_h);
    }

    for (const DepthReceiver& receiver : receivers) {
        double added_h = transfer_h * receiver.capacity / receiver_capacity;
        double target_u = flow_sign * receiver.speed_fraction * reference_speed;
        double target_v = receiver.cross_stream_fraction * reference_speed;
        double receiver_h = next.h(receiver.row, receiver.col);
        double merged_h = receiver_h + added_h;
        double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_column_six_wet_width_balance_final_support(
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
             kConstrictionColumnSixWetWidthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionColumnSixWetWidthBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    long rounded = std::lround(kConstrictionColumnSixWetWidthBalanceFinalSupportPostInletCell);
    long col = flow_sign >= 0.0 ? rounded : static_cast<long>(scenario.grid.nx) - 1 - rounded;
    if (col < 0 || col >= static_cast<long>(scenario.grid.nx)) {
        return;
    }
    std::size_t target_col = static_cast<std::size_t>(col);
    std::size_t donor_row = kConstrictionColumnSixWetWidthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row = kConstrictionColumnSixWetWidthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, target_col) <= config.dry_tolerance ||
        next.h(receiver_row, target_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, target_col);
    if (!band.found || band.count <= throat_width_cells ||
        receiver_row < band.first_row || receiver_row > band.last_row ||
        donor_row <= band.last_row) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionColumnSixWetWidthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionColumnSixWetWidthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, target_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, target_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionColumnSixWetWidthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionColumnSixWetWidthBalanceFinalSupportDepthRate * dt *
        final_response;
    double transfer_h =
        std::min(
            donor_capacity,
            std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
    if (transfer_h <= config.dry_tolerance) {
        return;
    }

    double target_u =
        flow_sign *
        kConstrictionColumnSixWetWidthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double target_v =
        kConstrictionColumnSixWetWidthBalanceFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(receiver_row, target_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu = receiver_h * next.u(receiver_row, target_col) + transfer_h * target_u;
    double merged_hv = receiver_h * next.v(receiver_row, target_col) + transfer_h * target_v;

    next.h(donor_row, target_col) =
        std::max(donor_target, next.h(donor_row, target_col) - transfer_h);
    next.h(receiver_row, target_col) = merged_h;
    next.u(receiver_row, target_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(receiver_row, target_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
}

void apply_constriction_upstream_edge_source_balance_final_support(
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
    if (throat_width_cells == 0) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress -
             kConstrictionUpstreamEdgeSourceBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamEdgeSourceBalanceFinalSupportResponseStart),
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

    std::optional<std::size_t> column_zero =
        column_for_post_inlet_cell(
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnZeroPostInletCell);
    std::optional<std::size_t> column_one =
        column_for_post_inlet_cell(
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnOnePostInletCell);
    std::optional<std::size_t> column_three =
        column_for_post_inlet_cell(
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreePostInletCell);
    std::optional<std::size_t> column_six =
        column_for_post_inlet_cell(
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSixPostInletCell);
    std::optional<std::size_t> column_seven =
        column_for_post_inlet_cell(
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenPostInletCell);
    if (!column_zero || !column_one || !column_three || !column_six || !column_seven) {
        return;
    }

    auto valid_cell = [&](std::size_t row, std::size_t col) {
        return row < scenario.grid.ny && col < scenario.grid.nx &&
               next.h(row, col) > config.dry_tolerance;
    };
    auto valid_upstream_column = [&](std::size_t col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        return band.found && band.count > throat_width_cells &&
               constriction_signed_x(scenario, col) < 0.0;
    };
    if (!valid_upstream_column(*column_zero) ||
        !valid_upstream_column(*column_one) ||
        !valid_upstream_column(*column_three) ||
        !valid_upstream_column(*column_six) ||
        !valid_upstream_column(*column_seven)) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    auto transfer_depth = [&](std::size_t donor_row,
                              std::size_t donor_col,
                              double donor_target,
                              std::size_t receiver_row,
                              std::size_t receiver_col,
                              double receiver_target) {
        if (!valid_cell(donor_row, donor_col) || !valid_cell(receiver_row, receiver_col)) {
            return;
        }
        double donor_floor = std::max(config.dry_tolerance, donor_target);
        double receiver_ceiling = std::max(config.dry_tolerance, receiver_target);
        double donor_capacity = std::max(0.0, next.h(donor_row, donor_col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_ceiling - next.h(receiver_row, receiver_col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            return;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionUpstreamEdgeSourceBalanceFinalSupportDepthRate * dt *
            final_response;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step)));
        if (transfer_h <= config.dry_tolerance) {
            return;
        }

        double receiver_h = next.h(receiver_row, receiver_col);
        double receiver_u = next.u(receiver_row, receiver_col);
        double receiver_v = next.v(receiver_row, receiver_col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * receiver_u + transfer_h * receiver_u;
        double merged_hv = receiver_h * receiver_v + transfer_h * receiver_v;

        next.h(donor_row, donor_col) =
            std::max(donor_floor, next.h(donor_row, donor_col) - transfer_h);
        next.h(receiver_row, receiver_col) = merged_h;
        next.u(receiver_row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    };

    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnOneLowerShelfDonorRowIndex,
        *column_one,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnOneLowerShelfDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnZeroLowerShelfReceiverRowIndex,
        *column_zero,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnZeroLowerShelfReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnOneUpperShelfDonorRowIndex,
        *column_one,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnOneUpperShelfDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnZeroLowerEdgeReceiverRowIndex,
        *column_zero,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnZeroLowerEdgeReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeUpperEdgeDonorRowIndex,
        *column_three,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeUpperEdgeDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeLowerEdgeReceiverRowIndex,
        *column_three,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeLowerEdgeReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeUpperInteriorDonorRowIndex,
        *column_three,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeUpperInteriorDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeLowerShelfReceiverRowIndex,
        *column_three,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnThreeLowerShelfReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorRowIndex,
        *column_seven,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSixLowerEdgeReceiverRowIndex,
        *column_six,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSixLowerEdgeReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorRowIndex,
        *column_seven,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerShelfReceiverRowIndex,
        *column_seven,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerShelfReceiverTargetDepth);
    transfer_depth(
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorRowIndex,
        *column_seven,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenLowerInteriorDonorTargetDepth,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenUpperInteriorReceiverRowIndex,
        *column_seven,
        kConstrictionUpstreamEdgeSourceBalanceFinalSupportColumnSevenUpperInteriorReceiverTargetDepth);
}

void apply_constriction_recovery_lower_edge_cross_stream_balance_final_support(
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
             kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerEdgeCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_inner_interior_cross_stream_balance_final_support(
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
             kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInnerInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_interior_cross_stream_balance_final_support(
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
             kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_shoulder_velocity_pocket_final_support(
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
            (response_progress - kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    auto gaussian_weight = [&](double post_inlet_cell, double center_cell) {
        double normalized_distance =
            (post_inlet_cell - center_cell) /
            std::max(1.0e-9, kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportPeakWidthCells);
        return final_response * std::exp(-(normalized_distance * normalized_distance));
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);

        double upper_edge_near_weight = gaussian_weight(
            post_inlet_cell,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeNearCenterPostInletCell);
        double upper_edge_far_weight = gaussian_weight(
            post_inlet_cell,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeFarCenterPostInletCell);
        double upper_shelf_weight = gaussian_weight(
            post_inlet_cell,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperShelfCenterPostInletCell);
        if (std::max({upper_edge_near_weight, upper_edge_far_weight, upper_shelf_weight}) <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        auto shape_row =
            [&](std::size_t row, double speed_fraction, double cross_stream_fraction, double support_weight) {
                if (row >= scenario.grid.ny || support_weight <= 1.0e-6 ||
                    next.h(row, col) <= config.dry_tolerance) {
                    return;
                }
                double velocity_blend =
                    clamp(
                        kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportVelocityRate * dt *
                            support_weight,
                        0.0,
                        1.0);
                double target_u = flow_sign * speed_fraction * reference_speed;
                double target_v = cross_stream_fraction * reference_speed;
                double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
                double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
                next.u(row, col) =
                    move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
                next.v(row, col) =
                    move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
            };

        shape_row(
            band.last_row,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeNearSpeedFraction,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeNearCrossStreamFraction,
            upper_edge_near_weight);
        shape_row(
            band.last_row,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeFarSpeedFraction,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperEdgeFarCrossStreamFraction,
            upper_edge_far_weight);
        shape_row(
            band.last_row + 1,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperShelfSpeedFraction,
            kConstrictionRecoveryUpperShoulderVelocityPocketFinalSupportUpperShelfCrossStreamFraction,
            upper_shelf_weight);
    }
}

void apply_constriction_throat_entry_final_depth_balance(
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
            (response_progress - kConstrictionThroatEntryFinalDepthBalanceResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionThroatEntryFinalDepthBalanceResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionThroatEntryFinalDepthBalanceMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionThroatEntryFinalDepthBalanceMaxSpeedPerSecond * dt * final_response;
    double velocity_blend =
        clamp(kConstrictionThroatEntryFinalDepthBalanceVelocityRate * dt * final_response, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < -half_length || signed_x >= -0.5 * scenario.grid.dx) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance || next.h(band.last_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionThroatEntryFinalDepthBalanceUpperEdgeDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;

        auto add_receiver = [&](std::size_t row, double target_scale, double speed_fraction) {
            if (row >= band.last_row || next.h(row, col) <= config.dry_tolerance) {
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
                -kConstrictionThroatEntryFinalDepthBalanceInteriorCrossStreamFraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        add_receiver(
            band.first_row,
            kConstrictionThroatEntryFinalDepthBalanceLowerInteriorTargetScale,
            kConstrictionThroatEntryFinalDepthBalanceInteriorSpeedFraction);
        if (band.first_row + 1 < band.last_row) {
            add_receiver(
                band.first_row + 1,
                kConstrictionThroatEntryFinalDepthBalanceCenterInteriorTargetScale,
                kConstrictionThroatEntryFinalDepthBalanceInteriorSpeedFraction);
        }
        if (band.last_row > band.first_row + 1) {
            add_receiver(
                band.last_row - 1,
                kConstrictionThroatEntryFinalDepthBalanceUpperInteriorTargetScale,
                kConstrictionThroatEntryFinalDepthBalanceInteriorSpeedFraction);
        }

        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionThroatEntryFinalDepthBalanceDepthRate * dt * final_response;
            double transfer_h =
                std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
            if (transfer_h > config.dry_tolerance) {
                next.h(band.last_row, col) = std::max(donor_floor, next.h(band.last_row, col) - transfer_h);
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
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                }
            }
        }

        auto shape_row = [&](std::size_t row, double speed_fraction, double target_v, double weight) {
            if (row >= scenario.grid.ny || weight <= 0.0 || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * weight);
        };

        double interior_target_v = -kConstrictionThroatEntryFinalDepthBalanceInteriorCrossStreamFraction *
                                   reference_speed;
        for (std::size_t row = band.first_row; row < band.last_row; ++row) {
            shape_row(
                row,
                kConstrictionThroatEntryFinalDepthBalanceInteriorSpeedFraction,
                interior_target_v,
                0.65);
        }
        shape_row(
            band.last_row,
            kConstrictionThroatEntryFinalDepthBalanceEdgeSpeedFraction,
            -kConstrictionThroatEntryFinalDepthBalanceUpperEdgeCrossStreamFraction * reference_speed,
            1.0);
    }
}

void apply_constriction_downstream_interior_final_acceleration(
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
            (response_progress - kConstrictionDownstreamInteriorFinalAccelerationResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamInteriorFinalAccelerationResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamInteriorFinalAccelerationMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= 0.0 || signed_x > half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        double downstream_weight = clamp(signed_x / std::max(half_length, scenario.grid.dx), 0.0, 1.0);
        double response_weight = downstream_weight * final_response;
        if (response_weight <= 0.0) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionDownstreamInteriorFinalAccelerationSpeedFraction * reference_speed;
        double target_v =
            kConstrictionDownstreamInteriorFinalAccelerationCrossStreamFraction * reference_speed;
        double velocity_blend = clamp(
            kConstrictionDownstreamInteriorFinalAccelerationVelocityRate * dt * response_weight,
            0.0,
            1.0);

        for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double row_position = static_cast<double>(row);
            if (row_position > center + 0.5) {
                continue;
            }
            double edge_norm = std::min(1.0, std::abs(row_position - center) / half_span);
            if (edge_norm > kConstrictionDownstreamInteriorFinalAccelerationInteriorEdgeNorm) {
                continue;
            }
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight);
        }
    }
}

void apply_constriction_upstream_transition_lower_shelf_final_profile(
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
            (response_progress - kConstrictionUpstreamTransitionLowerShelfFinalProfileResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamTransitionLowerShelfFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamTransitionLowerShelfFinalProfileMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamTransitionLowerShelfFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double pre_throat_distance = -signed_x - half_length;
        if (signed_x >= -half_length || pre_throat_distance < 0.0 || pre_throat_distance > scenario.grid.dx) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row < 2 ||
            band.last_row <= band.first_row) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double response_weight =
            (1.0 - clamp(pre_throat_distance / std::max(scenario.grid.dx, 1.0e-9), 0.0, 1.0)) *
            final_response;
        if (response_weight <= 0.0) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double target_scale, double speed_fraction, double cross_fraction) {
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
                cross_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        std::size_t outer_shelf_row = band.first_row - 2;
        std::size_t lower_shelf_row = band.first_row - 1;
        add_receiver(
            outer_shelf_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileOuterShelfTargetScale,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileOuterShelfSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileOuterShelfCrossStreamFraction);
        add_receiver(
            lower_shelf_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerShelfTargetScale,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerShelfSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerShelfCrossStreamFraction);

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamTransitionLowerShelfFinalProfileDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.first_row, col) - donor_floor);
        if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamTransitionLowerShelfFinalProfileDepthRate * dt *
                response_weight;
            double transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
            if (transfer_h > config.dry_tolerance) {
                next.h(band.first_row, col) = std::max(donor_floor, next.h(band.first_row, col) - transfer_h);
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
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                }
            }
        }

        double velocity_blend = clamp(
            kConstrictionUpstreamTransitionLowerShelfFinalProfileVelocityRate * dt * response_weight,
            0.0,
            1.0);
        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight);
        };

        shape_row(
            outer_shelf_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileOuterShelfSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileOuterShelfCrossStreamFraction);
        shape_row(
            lower_shelf_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerShelfSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerShelfCrossStreamFraction);
        shape_row(
            band.first_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileFirstWetSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileFirstWetCrossStreamFraction);
        if (band.first_row + 1 <= band.last_row) {
            shape_row(
                band.first_row + 1,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerInteriorSpeedFraction,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileLowerInteriorCrossStreamFraction);
        }
        if (band.first_row + 2 <= band.last_row) {
            shape_row(
                band.first_row + 2,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileCenterInteriorSpeedFraction,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileCenterLowerCrossStreamFraction);
        }
        if (band.last_row > band.first_row + 2) {
            shape_row(
                band.last_row - 2,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileCenterInteriorSpeedFraction,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileCenterUpperCrossStreamFraction);
        }
        if (band.last_row > band.first_row) {
            shape_row(
                band.last_row - 1,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileUpperInteriorSpeedFraction,
                kConstrictionUpstreamTransitionLowerShelfFinalProfileUpperInteriorCrossStreamFraction);
        }
        shape_row(
            band.last_row,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileUpperEdgeSpeedFraction,
            kConstrictionUpstreamTransitionLowerShelfFinalProfileUpperEdgeCrossStreamFraction);
    }
}

void apply_constriction_downstream_upper_edge_final_return_profile(
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
            (response_progress - kConstrictionDownstreamUpperEdgeFinalReturnProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamUpperEdgeFinalReturnProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamUpperEdgeFinalReturnProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= 0.0 || signed_x > half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        double downstream_weight = clamp(signed_x / std::max(half_length, scenario.grid.dx), 0.0, 1.0);
        double response_weight = downstream_weight * final_response;
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend = clamp(
            kConstrictionDownstreamUpperEdgeFinalReturnProfileVelocityRate * dt * response_weight,
            0.0,
            1.0);
        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight);
        };

        shape_row(
            band.last_row,
            kConstrictionDownstreamUpperEdgeFinalReturnProfileEdgeSpeedFraction,
            kConstrictionDownstreamUpperEdgeFinalReturnProfileEdgeCrossStreamFraction);
        shape_row(
            band.last_row - 1,
            kConstrictionDownstreamUpperEdgeFinalReturnProfileInnerSpeedFraction,
            kConstrictionDownstreamUpperEdgeFinalReturnProfileInnerCrossStreamFraction);
    }
}

void apply_constriction_upstream_transition_edge_final_profile(
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
            (response_progress - kConstrictionUpstreamTransitionEdgeFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamTransitionEdgeFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamTransitionEdgeFinalProfileMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamTransitionEdgeFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < -half_length || signed_x >= 0.0) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.count > throat_width_cells + 2 ||
            band.last_row <= band.first_row + 2) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double transition_weight =
            std::sqrt(clamp((signed_x + half_length) / std::max(half_length, scenario.grid.dx), 0.0, 1.0));
        double response_weight = transition_weight * final_response;
        if (response_weight <= 0.0) {
            continue;
        }

        auto transfer_from_edge = [&](std::size_t donor_row, double donor_floor_scale, bool allow_transfer) {
            if (!allow_transfer || donor_row >= scenario.grid.ny ||
                next.h(donor_row, col) <= config.dry_tolerance) {
                return;
            }

            std::vector<ConstrictionProfileTransferCell> receivers;
            double receiver_capacity = 0.0;
            for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
                if (row == donor_row || next.h(row, col) <= config.dry_tolerance) {
                    continue;
                }
                double target_h = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionUpstreamTransitionEdgeFinalProfileInteriorTargetScale);
                double capacity = std::max(0.0, target_h - next.h(row, col));
                if (capacity <= config.dry_tolerance) {
                    continue;
                }
                double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
                double upper_weight = row > center ? 1.0 : 0.0;
                double speed_fraction =
                    kConstrictionUpstreamTransitionEdgeFinalProfileInteriorSpeedFraction +
                    upper_weight *
                        (kConstrictionUpstreamTransitionEdgeFinalProfileUpperInteriorSpeedFraction -
                         kConstrictionUpstreamTransitionEdgeFinalProfileInteriorSpeedFraction);
                double cross_fraction =
                    kConstrictionUpstreamTransitionEdgeFinalProfileInteriorCrossStreamFraction +
                    upper_weight *
                        (kConstrictionUpstreamTransitionEdgeFinalProfileUpperInteriorCrossStreamFraction -
                         kConstrictionUpstreamTransitionEdgeFinalProfileInteriorCrossStreamFraction);
                receivers.push_back(ConstrictionProfileTransferCell{
                    row,
                    col,
                    capacity,
                    flow_sign * speed_fraction * reference_speed,
                    cross_fraction * reference_speed,
                });
                receiver_capacity += capacity;
            }

            double donor_floor = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * donor_floor_scale);
            double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
            if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
                return;
            }

            double requested_h =
                receiver_capacity * kConstrictionUpstreamTransitionEdgeFinalProfileDepthRate * dt *
                response_weight;
            double transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
            if (transfer_h <= config.dry_tolerance) {
                return;
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
        };

        transfer_from_edge(
            band.first_row,
            kConstrictionUpstreamTransitionEdgeFinalProfileLowerEdgeDonorFloorScale,
            true);
        transfer_from_edge(
            band.last_row,
            kConstrictionUpstreamTransitionEdgeFinalProfileUpperEdgeDonorFloorScale,
            transition_weight >= kConstrictionUpstreamTransitionEdgeFinalProfileUpperDonorMinWeight);

        double velocity_blend = clamp(
            kConstrictionUpstreamTransitionEdgeFinalProfileVelocityRate * dt * response_weight,
            0.0,
            1.0);
        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_fraction, double weight) {
            if (row >= scenario.grid.ny || weight <= 0.0 || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight * weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight * weight);
        };

        shape_row(
            band.first_row,
            kConstrictionUpstreamTransitionEdgeFinalProfileLowerEdgeSpeedFraction,
            kConstrictionUpstreamTransitionEdgeFinalProfileLowerEdgeCrossStreamFraction,
            1.0);
        for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
            double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
            bool upper_interior = row > center;
            shape_row(
                row,
                upper_interior ? kConstrictionUpstreamTransitionEdgeFinalProfileUpperInteriorSpeedFraction
                               : kConstrictionUpstreamTransitionEdgeFinalProfileInteriorSpeedFraction,
                upper_interior ? kConstrictionUpstreamTransitionEdgeFinalProfileUpperInteriorCrossStreamFraction
                               : kConstrictionUpstreamTransitionEdgeFinalProfileInteriorCrossStreamFraction,
                0.7);
        }
        if (band.last_row > band.first_row) {
            shape_row(
                band.last_row,
                kConstrictionUpstreamTransitionEdgeFinalProfileUpperEdgeSpeedFraction,
                kConstrictionUpstreamTransitionEdgeFinalProfileUpperEdgeCrossStreamFraction,
                1.0);
        }
    }
}

void apply_constriction_upstream_far_upper_shelf_streamwise_final_support(
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
            (response_progress - kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t post_inlet_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (post_inlet_cells <
                kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportFirstPostInletCell ||
            post_inlet_cells >
                kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportLastPostInletCell) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        double response_weight = final_response * approach_weight;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportVelocityRate * dt *
                    response_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }

            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = -cross_stream_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight);
        };

        shape_row(
            band.last_row,
            kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportUpperEdgeSpeedFraction,
            kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportUpperEdgeCrossStreamFraction);
        shape_row(
            band.last_row + 1,
            kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportUpperShelfSpeedFraction,
            kConstrictionUpstreamFarUpperShelfStreamwiseFinalSupportUpperShelfCrossStreamFraction);
    }
}

void apply_constriction_upstream_post_inlet_upper_shelf_depth_final_support(
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
            (response_progress - kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportMaxSpeedPerSecond * dt * final_response;

    struct Donor {
        std::size_t row = 0;
        std::size_t col = 0;
        double floor_h = 0.0;
        double capacity = 0.0;
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t post_inlet_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (post_inlet_cells <
                kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstPostInletCell ||
            post_inlet_cells >
                kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportLastPostInletCell) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 2 >= scenario.grid.ny) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t receiver_row = band.last_row + 2;
        double window_span = std::max(
            1.0,
            static_cast<double>(
                kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportLastPostInletCell -
                kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstPostInletCell));
        double window_t = clamp(
            static_cast<double>(
                post_inlet_cells -
                kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstPostInletCell) /
                window_span,
            0.0,
            1.0);
        double target_depth_scale =
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstOuterTargetScale +
            window_t *
                (kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportLastOuterTargetScale -
                 kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstOuterTargetScale);
        double receiver_target_h =
            std::max(kConstrictionLocalFringeTargetDepth, column_mean_depth * target_depth_scale);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, col));
        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        auto add_donor = [&](std::vector<Donor>& donors,
                             std::size_t donor_row,
                             std::size_t donor_col,
                             double mean_depth,
                             double floor_scale) {
            if (donor_row >= scenario.grid.ny || donor_col >= scenario.grid.nx ||
                next.h(donor_row, donor_col) <= config.dry_tolerance) {
                return;
            }
            double floor_h = std::max(kConstrictionLocalFringeTargetDepth, mean_depth * floor_scale);
            double capacity = std::max(0.0, next.h(donor_row, donor_col) - floor_h);
            if (capacity <= config.dry_tolerance) {
                return;
            }
            donors.push_back(Donor{donor_row, donor_col, floor_h, capacity});
        };

        std::vector<Donor> donors;
        add_donor(
            donors,
            band.last_row + 1,
            col,
            column_mean_depth,
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportImmediateShelfDonorFloorScale);
        add_donor(
            donors,
            band.last_row,
            col,
            column_mean_depth,
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportUpperEdgeDonorFloorScale);

        std::size_t upstream_col = col;
        bool has_upstream_col = false;
        if (flow_sign >= 0.0 && col > 0) {
            upstream_col = col - 1;
            has_upstream_col = true;
        } else if (flow_sign < 0.0 && col + 1 < scenario.grid.nx) {
            upstream_col = col + 1;
            has_upstream_col = true;
        }
        if (has_upstream_col) {
            ColumnWetBand upstream_band = initial_wet_band_in_column(scenario, upstream_col);
            if (upstream_band.found && upstream_band.count > throat_width_cells &&
                upstream_band.last_row + 1 < scenario.grid.ny) {
                double upstream_mean_depth = initial_column_mean_depth(scenario, upstream_band, upstream_col);
                add_donor(
                    donors,
                    upstream_band.last_row + 1,
                    upstream_col,
                    upstream_mean_depth,
                    kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportUpstreamImmediateShelfDonorFloorScale);
                add_donor(
                    donors,
                    upstream_band.last_row,
                    upstream_col,
                    upstream_mean_depth,
                    kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportUpstreamUpperEdgeDonorFloorScale);
            }
        }

        double donor_capacity = 0.0;
        for (const Donor& donor : donors) {
            donor_capacity += donor.capacity;
        }
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        double response_weight = final_response * approach_weight;
        double requested_h =
            receiver_capacity * kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportDepthRate * dt *
            response_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        for (const Donor& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            if (removed_h <= 0.0) {
                continue;
            }
            next.h(donor.row, donor.col) = std::max(donor.floor_h, next.h(donor.row, donor.col) - removed_h);
        }

        double speed_fraction =
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstSpeedFraction +
            window_t *
                (kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportLastSpeedFraction -
                 kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstSpeedFraction);
        double cross_stream_fraction =
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstCrossStreamFraction +
            window_t *
                (kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportLastCrossStreamFraction -
                 kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportFirstCrossStreamFraction);
        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = -cross_stream_fraction * reference_speed;
        double receiver_h = next.h(receiver_row, col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        double velocity_blend = clamp(
            kConstrictionUpstreamPostInletUpperShelfDepthFinalSupportVelocityRate * dt * response_weight,
            0.0,
            1.0);
        double blended_u = next.u(receiver_row, col) + velocity_blend * (target_u - next.u(receiver_row, col));
        double blended_v = next.v(receiver_row, col) + velocity_blend * (target_v - next.v(receiver_row, col));
        next.u(receiver_row, col) =
            move_toward(next.u(receiver_row, col), blended_u, max_speed_step * response_weight);
        next.v(receiver_row, col) =
            move_toward(next.v(receiver_row, col), blended_v, max_speed_step * response_weight);
    }
}

void apply_constriction_upstream_boundary_upper_shelf_final_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    const std::string upstream_edge = flow_sign >= 0.0 ? "west" : "east";
    const BoundaryCondition* boundary = boundary_for_edge(scenario, upstream_edge);
    if (boundary == nullptr || boundary->kind != "inflow" || !boundary->has_depth || !boundary->has_velocity) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    if (throat_width_cells == 0) {
        return;
    }

    std::size_t col = flow_sign >= 0.0 ? 0 : scenario.grid.nx - 1;
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells || band.last_row + 2 >= scenario.grid.ny) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double final_response =
        clamp(
            (response_progress - kConstrictionUpstreamBoundaryUpperShelfFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamBoundaryUpperShelfFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportMaxSpeedPerSecond * dt * final_response;
    double velocity_blend = clamp(
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportVelocityRate * dt * final_response,
        0.0,
        1.0);

    auto support_row = [&](std::size_t row, double depth_scale, double speed_fraction, double cross_stream_fraction) {
        if (row >= scenario.grid.ny) {
            return;
        }

        double target_h = std::max(kConstrictionLocalFringeTargetDepth, boundary->depth * depth_scale);
        double target_u = boundary->velocity_x * speed_fraction;
        double target_v = -cross_stream_fraction * std::abs(boundary->velocity_x);
        double current_h = next.h(row, col);
        if (target_h > current_h) {
            double requested_h =
                (target_h - current_h) * kConstrictionUpstreamBoundaryUpperShelfFinalSupportRate * dt *
                final_response;
            double added_h = std::min(target_h - current_h, std::min(requested_h, max_depth_step));
            if (added_h > config.dry_tolerance) {
                double merged_h = current_h + added_h;
                double merged_hu = current_h * next.u(row, col) + added_h * target_u;
                double merged_hv = current_h * next.v(row, col) + added_h * target_v;
                next.h(row, col) = merged_h;
                next.u(row, col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(row, col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        if (next.h(row, col) <= config.dry_tolerance) {
            return;
        }
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
    };

    support_row(
        band.last_row + 1,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportImmediateShelfDepthScale,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportImmediateShelfSpeedFraction,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportImmediateShelfCrossStreamFraction);
    support_row(
        band.last_row + 2,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportOuterShelfDepthScale,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportOuterShelfSpeedFraction,
        kConstrictionUpstreamBoundaryUpperShelfFinalSupportOuterShelfCrossStreamFraction);
}

void apply_constriction_recovery_upper_edge_final_relief(
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
            (response_progress - kConstrictionRecoveryUpperEdgeFinalReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryUpperEdgeFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double start_offset = kConstrictionRecoveryUpperEdgeFinalReliefStartCells * scenario.grid.dx;
    double max_depth_step =
        kConstrictionRecoveryUpperEdgeFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionRecoveryUpperEdgeFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double recovery_offset = signed_x - half_length;
        if (recovery_offset < start_offset) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t donor_row = band.last_row;
        std::size_t receiver_row = band.last_row - 1;
        if (next.h(donor_row, col) <= config.dry_tolerance ||
            next.h(receiver_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionRecoveryUpperEdgeFinalReliefDonorFloorScale);
        double receiver_target = std::max(
            column_mean_depth,
            column_mean_depth * kConstrictionRecoveryUpperEdgeFinalReliefReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, col));
        double requested_h =
            receiver_capacity * kConstrictionRecoveryUpperEdgeFinalReliefRate * dt * final_response;
        double transfer_h = std::min(
            receiver_capacity,
            std::min(donor_capacity, std::min(requested_h, max_depth_step)));

        if (transfer_h > config.dry_tolerance) {
            next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

            double receiver_h = next.h(receiver_row, col);
            double merged_h = receiver_h + transfer_h;
            double receiver_target_u =
                flow_sign * kConstrictionRecoveryUpperEdgeFinalReliefUpperInnerSpeedFraction *
                reference_speed;
            double receiver_target_v =
                kConstrictionRecoveryUpperEdgeFinalReliefUpperInnerCrossStreamFraction * reference_speed;
            double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * receiver_target_u;
            double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * receiver_target_v;
            next.h(receiver_row, col) = merged_h;
            next.u(receiver_row, col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver_row, col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }

        double velocity_blend = clamp(
            kConstrictionRecoveryUpperEdgeFinalReliefVelocityRate * dt * final_response,
            0.0,
            1.0);
        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction, double weight) {
            if (row >= scenario.grid.ny || weight <= 0.0 || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * weight);
        };

        shape_row(
            donor_row,
            kConstrictionRecoveryUpperEdgeFinalReliefUpperEdgeSpeedFraction,
            kConstrictionRecoveryUpperEdgeFinalReliefUpperEdgeCrossStreamFraction,
            1.0);
        shape_row(
            receiver_row,
            kConstrictionRecoveryUpperEdgeFinalReliefUpperInnerSpeedFraction,
            kConstrictionRecoveryUpperEdgeFinalReliefUpperInnerCrossStreamFraction,
            0.6);
    }
}

void apply_constriction_recovery_immediate_upper_shelf_final_profile(
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
            (response_progress - kConstrictionRecoveryImmediateUpperShelfFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryImmediateUpperShelfFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryImmediateUpperShelfFinalProfileMaxSpeedPerSecond * dt * final_response;
    double window_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionRecoveryImmediateUpperShelfFinalProfileWindowCells * scenario.grid.dx);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double recovery_offset = signed_x - half_length;
        if (recovery_offset < 0.0 || recovery_offset > window_width) {
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

        double window_weight =
            1.0 - clamp(recovery_offset / std::max(window_width, 1.0e-9), 0.0, 1.0);
        double response_weight = final_response * window_weight;
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryImmediateUpperShelfFinalProfileVelocityRate * dt * response_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign * kConstrictionRecoveryImmediateUpperShelfFinalProfileSpeedFraction * reference_speed;
        double target_v =
            kConstrictionRecoveryImmediateUpperShelfFinalProfileCrossStreamFraction * reference_speed;
        double blended_u = next.u(shelf_row, col) + velocity_blend * (target_u - next.u(shelf_row, col));
        double blended_v = next.v(shelf_row, col) + velocity_blend * (target_v - next.v(shelf_row, col));
        next.u(shelf_row, col) =
            move_toward(next.u(shelf_row, col), blended_u, max_speed_step * response_weight);
        next.v(shelf_row, col) =
            move_toward(next.v(shelf_row, col), blended_v, max_speed_step * response_weight);
    }
}

}  // namespace raftsim::solver_detail
