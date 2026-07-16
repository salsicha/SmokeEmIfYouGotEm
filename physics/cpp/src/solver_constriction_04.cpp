#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_upstream_upper_edge_streamwise_final_support(
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
            (response_progress - kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;
    double taper_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportEdgeTaperCells * scenario.grid.dx);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t post_inlet_cell =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        double support_weight = final_response;
        if (post_inlet_cell < kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportFirstPostInletCell) {
            double distance =
                static_cast<double>(kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportFirstPostInletCell -
                                    post_inlet_cell) *
                scenario.grid.dx;
            double normalized = distance / taper_width;
            support_weight *= std::exp(-(normalized * normalized));
        } else if (post_inlet_cell > kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportLastPostInletCell) {
            double distance =
                static_cast<double>(post_inlet_cell -
                                    kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportLastPostInletCell) *
                scenario.grid.dx;
            double normalized = distance / taper_width;
            support_weight *= std::exp(-(normalized * normalized));
        }
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
            flow_sign * kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportSpeedFraction * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeStreamwiseFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_profile_final_relief(
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
            (response_progress - kConstrictionUpstreamLowerEdgeProfileFinalReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamLowerEdgeProfileFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    bool forward_flow = flow_sign >= 0.0;
    double taper_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefEdgeTaperCells * scenario.grid.dx);
    double max_depth_step =
        kConstrictionUpstreamLowerEdgeProfileFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeProfileFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t post_inlet_cell = forward_flow ? col : (scenario.grid.nx - 1 - col);
        double support_weight = final_response;
        if (post_inlet_cell < kConstrictionUpstreamLowerEdgeProfileFinalReliefFirstPostInletCell) {
            double distance =
                static_cast<double>(kConstrictionUpstreamLowerEdgeProfileFinalReliefFirstPostInletCell -
                                    post_inlet_cell) *
                scenario.grid.dx;
            double normalized = distance / taper_width;
            support_weight *= std::exp(-(normalized * normalized));
        } else if (post_inlet_cell > kConstrictionUpstreamLowerEdgeProfileFinalReliefLastPostInletCell) {
            double distance =
                static_cast<double>(post_inlet_cell -
                                    kConstrictionUpstreamLowerEdgeProfileFinalReliefLastPostInletCell) *
                scenario.grid.dx;
            double normalized = distance / taper_width;
            support_weight *= std::exp(-(normalized * normalized));
        }
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells + 2 || band.last_row <= band.first_row + 1) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance || next.h(band.first_row, col) <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver =
            [&](std::size_t receiver_row,
                std::size_t receiver_col,
                double receiver_mean_depth,
                double target_scale,
                double speed_fraction,
                double cross_stream_fraction) {
                if (receiver_row >= scenario.grid.ny || receiver_col >= scenario.grid.nx ||
                    receiver_mean_depth <= config.dry_tolerance) {
                    return;
                }
                double target_h = receiver_mean_depth * target_scale;
                double capacity = std::max(0.0, target_h - next.h(receiver_row, receiver_col));
                if (capacity <= config.dry_tolerance) {
                    return;
                }
                receivers.push_back(ConstrictionProfileTransferCell{
                    receiver_row,
                    receiver_col,
                    capacity,
                    flow_sign * speed_fraction * reference_speed,
                    cross_stream_fraction * reference_speed,
                });
                receiver_capacity += capacity;
            };

        add_receiver(
            band.first_row + 1,
            col,
            column_mean_depth,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorTargetScale,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorSpeedFraction,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorCrossStreamFraction);
        if (band.first_row + 2 < band.last_row) {
            add_receiver(
                band.first_row + 2,
                col,
                column_mean_depth,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorTargetScale,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorSpeedFraction,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefInteriorCrossStreamFraction);
        }

        if (post_inlet_cell <= kConstrictionUpstreamLowerEdgeProfileFinalReliefFirstPostInletCell) {
            add_receiver(
                band.last_row + 1,
                col,
                column_mean_depth,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperImmediateShelfTargetScale,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
                kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);
        }
        add_receiver(
            band.last_row + 2,
            col,
            column_mean_depth,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperOuterShelfTargetScale,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);
        add_receiver(
            band.last_row + 3,
            col,
            column_mean_depth,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperOuterShelfTargetScale,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
            kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);

        std::size_t upstream_col = forward_flow ? (col == 0 ? col : col - 1)
                                                : (col + 1 >= scenario.grid.nx ? col : col + 1);
        if (upstream_col != col) {
            ColumnWetBand upstream_band = initial_wet_band_in_column(scenario, upstream_col);
            if (upstream_band.found && upstream_band.count > throat_width_cells) {
                double upstream_mean_depth = initial_column_mean_depth(scenario, upstream_band, upstream_col);
                add_receiver(
                    upstream_band.last_row + 1,
                    upstream_col,
                    upstream_mean_depth,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperImmediateShelfTargetScale,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);
                add_receiver(
                    upstream_band.last_row + 2,
                    upstream_col,
                    upstream_mean_depth,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperOuterShelfTargetScale,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);
                add_receiver(
                    upstream_band.last_row + 3,
                    upstream_col,
                    upstream_mean_depth,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperOuterShelfTargetScale,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfSpeedFraction,
                    kConstrictionUpstreamLowerEdgeProfileFinalReliefUpperShelfCrossStreamFraction);
            }
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamLowerEdgeProfileFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.first_row, col) - donor_floor);
        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamLowerEdgeProfileFinalReliefDepthRate * dt *
                support_weight;
            double transfer_h =
                std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
            if (transfer_h > config.dry_tolerance) {
                next.h(band.first_row, col) =
                    std::max(donor_floor, next.h(band.first_row, col) - transfer_h);
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

        if (next.h(band.first_row, col) <= config.dry_tolerance) {
            continue;
        }
        double target_u =
            flow_sign * kConstrictionUpstreamLowerEdgeProfileFinalReliefLowerEdgeSpeedFraction * reference_speed;
        double target_v =
            kConstrictionUpstreamLowerEdgeProfileFinalReliefLowerEdgeCrossStreamFraction * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeProfileFinalReliefVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(band.first_row, col) + velocity_blend * (target_u - next.u(band.first_row, col));
        double blended_v = next.v(band.first_row, col) + velocity_blend * (target_v - next.v(band.first_row, col));
        next.u(band.first_row, col) =
            move_toward(next.u(band.first_row, col), blended_u, max_speed_step * support_weight);
        next.v(band.first_row, col) =
            move_toward(next.v(band.first_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_shelf_notch_final_profile(
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
            (response_progress - kConstrictionUpstreamLowerShelfNotchFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamLowerShelfNotchFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double notch_center = -kConstrictionUpstreamLowerShelfNotchFinalProfileCenterHalfLengthScale * half_length;
    double upstream_width =
        std::max(scenario.grid.dx, kConstrictionUpstreamLowerShelfNotchFinalProfileUpstreamWidthHalfLengthScale *
                                       half_length);
    double downstream_width =
        std::max(scenario.grid.dx, kConstrictionUpstreamLowerShelfNotchFinalProfileDownstreamWidthHalfLengthScale *
                                       half_length);
    double max_speed_step =
        kConstrictionUpstreamLowerShelfNotchFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= -half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        std::size_t shelf_row = band.first_row - 1;
        if (next.h(shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double width = signed_x < notch_center ? upstream_width : downstream_width;
        double normalized_distance = (signed_x - notch_center) / std::max(1.0e-9, width);
        double notch_weight = std::exp(-(normalized_distance * normalized_distance));
        double response_weight = final_response * approach_weight * notch_weight;
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(kConstrictionUpstreamLowerShelfNotchFinalProfileVelocityRate * dt * response_weight, 0.0, 1.0);
        double target_u =
            flow_sign * kConstrictionUpstreamLowerShelfNotchFinalProfileSpeedFraction * reference_speed;
        double target_v = kConstrictionUpstreamLowerShelfNotchFinalProfileCrossStreamFraction * reference_speed;
        double blended_u = next.u(shelf_row, col) + velocity_blend * (target_u - next.u(shelf_row, col));
        double blended_v = next.v(shelf_row, col) + velocity_blend * (target_v - next.v(shelf_row, col));
        next.u(shelf_row, col) =
            move_toward(next.u(shelf_row, col), blended_u, max_speed_step * response_weight);
        next.v(shelf_row, col) =
            move_toward(next.v(shelf_row, col), blended_v, max_speed_step * response_weight);
    }
}

void apply_constriction_upstream_lower_shelf_pocket_final_relief(
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
            (response_progress - kConstrictionUpstreamLowerShelfPocketFinalReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamLowerShelfPocketFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamLowerShelfPocketFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionUpstreamLowerShelfPocketFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        double normalized_distance =
            (static_cast<double>(upstream_distance_cells) -
             kConstrictionUpstreamLowerShelfPocketFinalReliefCenterDistanceCells) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerShelfPocketFinalReliefPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0 ||
            band.first_row + 1 > band.last_row) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        if (next.h(lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamLowerShelfPocketFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(lower_shelf_row, col) - donor_floor);

        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double target_scale) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_h = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * target_scale);
            double capacity = std::max(0.0, target_h - next.h(row, col));
            if (capacity > config.dry_tolerance) {
                receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                receiver_capacity += capacity;
            }
        };

        if (lower_shelf_row > 0) {
            add_receiver(
                lower_shelf_row - 1,
                kConstrictionUpstreamLowerShelfPocketFinalReliefOuterShelfTargetScale);
        }
        add_receiver(
            band.first_row,
            kConstrictionUpstreamLowerShelfPocketFinalReliefLowerEdgeTargetScale);
        add_receiver(
            band.first_row + 1,
            kConstrictionUpstreamLowerShelfPocketFinalReliefLowerInteriorTargetScale);

        double transfer_h = 0.0;
        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamLowerShelfPocketFinalReliefDepthRate * dt *
                support_weight;
            transfer_h =
                std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        }

        if (transfer_h > config.dry_tolerance) {
            next.h(lower_shelf_row, col) =
                std::max(donor_floor, next.h(lower_shelf_row, col) - transfer_h);

            for (const ConstrictionDepthTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + added_h;
                next.h(receiver.row, receiver.col) = merged_h;
            }
        }

        if (next.h(lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerShelfPocketFinalReliefVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign * kConstrictionUpstreamLowerShelfPocketFinalReliefLowerShelfSpeedFraction *
            reference_speed;
        double blended_u = next.u(lower_shelf_row, col) + velocity_blend * (target_u - next.u(lower_shelf_row, col));
        next.u(lower_shelf_row, col) =
            move_toward(next.u(lower_shelf_row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_pocket_velocity_final_support(
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
            (response_progress - kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        double normalized_distance =
            (static_cast<double>(upstream_distance_cells) -
             kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportCenterDistanceCells) /
            std::max(1.0e-9, kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportPeakWidthCells);
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

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign * kConstrictionUpstreamLowerEdgePocketVelocityFinalSupportSpeedFraction * reference_speed;
        if ((next.u(lower_edge_row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double blended_u =
            next.u(lower_edge_row, col) + velocity_blend * (target_u - next.u(lower_edge_row, col));
        next.u(lower_edge_row, col) =
            move_toward(next.u(lower_edge_row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_shelf_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        auto shape_cross_stream = [&](std::size_t row, double target_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = -target_fraction * reference_speed;
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        shape_cross_stream(
            band.last_row,
            kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportUpperEdgeFraction);
        shape_cross_stream(
            band.last_row + 1,
            kConstrictionUpstreamUpperEdgeShelfCrossStreamPocketFinalSupportUpperShelfFraction);
    }
}

void apply_constriction_upstream_upper_edge_shelf_momentum_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        auto accelerate_streamwise_toward = [&](double target_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u =
                flow_sign * target_fraction * reference_speed;
            bool needs_acceleration =
                flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
            if (!needs_acceleration) {
                return;
            }

            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        };

        auto accelerate_cross_stream_toward = [&](double target_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = -target_fraction * reference_speed;
            if (next.v(row, col) <= target_v) {
                return;
            }

            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        if (row == band.last_row) {
            accelerate_streamwise_toward(
                kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportUpperEdgeSpeedFraction);
        } else if (row == band.last_row + 1) {
            accelerate_streamwise_toward(
                kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportUpperShelfSpeedFraction);
            accelerate_cross_stream_toward(
                kConstrictionUpstreamUpperEdgeShelfMomentumPocketFinalSupportUpperShelfCrossStreamFraction);
        }
    }
}

void apply_constriction_upstream_upper_edge_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            -kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_shelf_streamwise_pocket_final_support(
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
             kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row + 1 != band.first_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_deceleration =
            flow_sign >= 0.0 ? next.u(row, col) > target_u : next.u(row, col) < target_u;
        if (!needs_deceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerShelfStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_shelf_depth_momentum_pocket_final_support(
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
             kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0 ||
            band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        std::size_t receiver_row =
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportTargetRowIndex;
        if (receiver_row + 1 != band.first_row ||
            next.h(receiver_row, col) <= config.dry_tolerance) {
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
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportUpperEdgeDonorFloorScale);
        add_donor(
            band.last_row + 1,
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportUpperShelfDonorFloorScale);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        double receiver_target_h =
            std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth *
                    kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportReceiverTargetScale);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, col));
        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportReceiverSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionUpstreamLowerShelfDepthMomentumPocketFinalSupportReceiverCrossStreamFraction *
            reference_speed;
        double receiver_h = next.h(receiver_row, col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_upstream_lower_shelf_inner_streamwise_pocket_final_support(
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
             kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row + 1 != band.first_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerShelfInnerStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_sign_pocket_final_support(
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
             kConstrictionUpstreamLowerEdgeSignPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerEdgeSignPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeSignPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerEdgeSignPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamLowerEdgeSignPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerEdgeSignPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.first_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            -kConstrictionUpstreamLowerEdgeSignPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeSignPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_shelf_streamwise_pocket_final_support(
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
             kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row + 1 ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        bool needs_acceleration =
            flow_sign >= 0.0 ? next.u(row, col) < target_u : next.u(row, col) > target_u;
        if (!needs_acceleration) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_shelf_inner_streamwise_pocket_final_support(
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
             kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row >= scenario.grid.ny) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row + 1 ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfInnerStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_shelf_boundary_streamwise_pocket_final_support(
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
             kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row >= scenario.grid.ny) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row + 1 ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfBoundaryStreamwisePocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_interior_momentum_pocket_final_support(
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
            (response_progress - kConstrictionUpstreamInteriorMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamInteriorMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInteriorMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell - kConstrictionUpstreamInteriorMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamInteriorMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamInteriorMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionUpstreamInteriorMomentumPocketFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInteriorMomentumPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_spillback_depth_pocket_final_relief(
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
             kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefMaxDepthPerSecond * dt *
        final_response;
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        if (!donor_band.found || donor_band.count <= throat_width_cells) {
            continue;
        }

        std::size_t donor_row =
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefTargetRowIndex;
        if (donor_row >= scenario.grid.ny || donor_row != donor_band.last_row ||
            next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        int receiver_col_signed =
            flow_sign >= 0.0 ? static_cast<int>(col) - 1 : static_cast<int>(col) + 1;
        if (receiver_col_signed < 0 || receiver_col_signed >= static_cast<int>(scenario.grid.nx)) {
            continue;
        }
        std::size_t receiver_col = static_cast<std::size_t>(receiver_col_signed);
        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
        if (!receiver_band.found || receiver_band.count <= throat_width_cells ||
            donor_row != receiver_band.last_row ||
            next.h(donor_row, receiver_col) <= config.dry_tolerance) {
            continue;
        }

        double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, col);
        double receiver_mean_depth = initial_column_mean_depth(scenario, receiver_band, receiver_col);
        if (donor_mean_depth <= config.dry_tolerance || receiver_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            donor_mean_depth *
                kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefDonorFloorScale);
        double receiver_target = std::max(
            config.dry_tolerance,
            receiver_mean_depth *
                kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(donor_row, receiver_col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);
        next.h(donor_row, receiver_col) = next.h(donor_row, receiver_col) + transfer_h;

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        auto shape_cell = [&](std::size_t cell_col, double speed_fraction, double cross_stream_fraction) {
            if (next.h(donor_row, cell_col) <= config.dry_tolerance) {
                return;
            }
            double target_u =
                flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blended_u =
                next.u(donor_row, cell_col) +
                velocity_blend * (target_u - next.u(donor_row, cell_col));
            double blended_v =
                next.v(donor_row, cell_col) +
                velocity_blend * (target_v - next.v(donor_row, cell_col));
            next.u(donor_row, cell_col) =
                move_toward(
                    next.u(donor_row, cell_col),
                    blended_u,
                    max_speed_step * support_weight);
            next.v(donor_row, cell_col) =
                move_toward(
                    next.v(donor_row, cell_col),
                    blended_v,
                    max_speed_step * support_weight);
        };

        shape_cell(
            col,
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefDonorSpeedFraction,
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefDonorCrossStreamFraction);
        shape_cell(
            receiver_col,
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefReceiverSpeedFraction,
            kConstrictionUpstreamUpperEdgeSpillbackDepthPocketFinalReliefReceiverCrossStreamFraction);
    }
}

void apply_constriction_recovery_inner_interior_momentum_pocket_final_support(
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
             kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryInnerInteriorMomentumPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_inner_interior_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInnerInteriorCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_face_cross_stream_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            -kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeFaceCrossStreamPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_streamwise_depth_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t donor_row =
            kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportTargetRowIndex;
        if (donor_row >= scenario.grid.ny || donor_row != band.last_row ||
            next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            column_mean_depth *
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || row == donor_row ||
                next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double receiver_target = std::max(
                config.dry_tolerance,
                column_mean_depth *
                    kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportReceiverTargetScale);
            double capacity = std::max(0.0, receiver_target - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                return;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * speed_fraction * reference_speed,
                -cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        if (donor_row > band.first_row) {
            add_receiver(
                donor_row - 1,
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportNearReceiverSpeedFraction,
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportNearReceiverCrossStreamFraction);
        }
        if (donor_row > band.first_row + 1) {
            add_receiver(
                donor_row - 2,
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportFarReceiverSpeedFraction,
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportFarReceiverCrossStreamFraction);
        }

        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity *
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportDepthRate * dt *
                support_weight;
            double transfer_h =
                std::min(
                    donor_capacity,
                    std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
            if (transfer_h > config.dry_tolerance) {
                next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);
                for (const ConstrictionProfileTransferCell& receiver : receivers) {
                    double added_h = transfer_h * receiver.capacity / receiver_capacity;
                    if (added_h <= 0.0) {
                        continue;
                    }
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + added_h;
                    double merged_hu =
                        receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
                    double merged_hv =
                        receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance
                            ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                            : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance
                            ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                            : 0.0;
                }
            }
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportDonorSpeedFraction *
            reference_speed;
        double target_v =
            -kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportDonorCrossStreamFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeStreamwiseDepthPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(donor_row, col) + velocity_blend * (target_u - next.u(donor_row, col));
        double blended_v = next.v(donor_row, col) + velocity_blend * (target_v - next.v(donor_row, col));
        next.u(donor_row, col) =
            move_toward(next.u(donor_row, col), blended_u, max_speed_step * support_weight);
        next.v(donor_row, col) =
            move_toward(next.v(donor_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_edge_inlet_streamwise_depth_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        if ((flow_sign >= 0.0 && col == 0) ||
            (flow_sign < 0.0 && col + 1 >= scenario.grid.nx)) {
            continue;
        }
        std::size_t receiver_col = flow_sign >= 0.0 ? col - 1 : col + 1;

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
        if (!donor_band.found || !receiver_band.found ||
            donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row != donor_band.last_row || row != receiver_band.last_row ||
            next.h(row, col) <= config.dry_tolerance ||
            next.h(row, receiver_col) <= config.dry_tolerance) {
            continue;
        }

        double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, col);
        double receiver_mean_depth = initial_column_mean_depth(scenario, receiver_band, receiver_col);
        if (donor_mean_depth <= config.dry_tolerance || receiver_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            donor_mean_depth *
                kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportDonorFloorScale);
        double receiver_target = std::max(
            config.dry_tolerance,
            receiver_mean_depth *
                kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(row, receiver_col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        double receiver_target_u =
            flow_sign *
            kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportReceiverSpeedFraction *
            reference_speed;
        double receiver_target_v =
            -kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportReceiverCrossStreamFraction *
            reference_speed;

        next.h(row, col) = std::max(donor_floor, next.h(row, col) - transfer_h);

        double receiver_h = next.h(row, receiver_col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(row, receiver_col) + transfer_h * receiver_target_u;
        double merged_hv = receiver_h * next.v(row, receiver_col) + transfer_h * receiver_target_v;
        next.h(row, receiver_col) = merged_h;
        next.u(row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        double donor_target_u =
            flow_sign *
            kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportDonorSpeedFraction *
            reference_speed;
        double donor_target_v =
            -kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportDonorCrossStreamFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeInletStreamwiseDepthPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);

        auto shape_cell = [&](std::size_t target_col, double target_u, double target_v) {
            double blended_u = next.u(row, target_col) + velocity_blend * (target_u - next.u(row, target_col));
            double blended_v = next.v(row, target_col) + velocity_blend * (target_v - next.v(row, target_col));
            next.u(row, target_col) =
                move_toward(next.u(row, target_col), blended_u, max_speed_step * support_weight);
            next.v(row, target_col) =
                move_toward(next.v(row, target_col), blended_v, max_speed_step * support_weight);
        };

        shape_cell(col, donor_target_u, donor_target_v);
        shape_cell(receiver_col, receiver_target_u, receiver_target_v);
    }
}

void apply_constriction_upstream_upper_edge_mid_depth_velocity_pocket_final_support(
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
             kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double max_speed_step =
        kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;
    std::size_t receiver_offset = static_cast<std::size_t>(
        kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportReceiverColumnOffsetCells);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        if ((flow_sign >= 0.0 && col + receiver_offset >= scenario.grid.nx) ||
            (flow_sign < 0.0 && col < receiver_offset)) {
            continue;
        }
        std::size_t receiver_col = flow_sign >= 0.0 ? col + receiver_offset : col - receiver_offset;

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
        if (!donor_band.found || !receiver_band.found || donor_band.count <= throat_width_cells) {
            continue;
        }

        std::size_t donor_row = kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportDonorRowIndex;
        std::size_t receiver_row = kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportReceiverRowIndex;
        if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
            donor_row != donor_band.last_row ||
            next.h(donor_row, col) <= config.dry_tolerance ||
            next.h(receiver_row, receiver_col) <= config.dry_tolerance) {
            continue;
        }

        double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, col);
        double receiver_mean_depth = initial_column_mean_depth(scenario, receiver_band, receiver_col);
        if (donor_mean_depth <= config.dry_tolerance || receiver_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            donor_mean_depth * kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportDonorFloorScale);
        double receiver_target = std::max(
            config.dry_tolerance,
            receiver_mean_depth *
                kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportReceiverTargetScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, receiver_col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportDepthRate * dt *
            support_weight;
        double transfer_h =
            std::min(
                donor_capacity,
                std::min(receiver_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        double receiver_target_u =
            flow_sign *
            kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportReceiverSpeedFraction *
            reference_speed;
        double receiver_target_v =
            kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportReceiverCrossStreamFraction *
            reference_speed;
        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

        double receiver_h = next.h(receiver_row, receiver_col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(receiver_row, receiver_col) + transfer_h * receiver_target_u;
        double merged_hv = receiver_h * next.v(receiver_row, receiver_col) + transfer_h * receiver_target_v;
        next.h(receiver_row, receiver_col) = merged_h;
        next.u(receiver_row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, receiver_col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        double donor_target_u =
            flow_sign *
            kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportDonorSpeedFraction *
            reference_speed;
        double donor_target_v =
            kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportDonorCrossStreamFraction *
            reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperEdgeMidDepthVelocityPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);

        auto shape_cell = [&](std::size_t row, std::size_t target_col, double target_u, double target_v) {
            double blended_u = next.u(row, target_col) + velocity_blend * (target_u - next.u(row, target_col));
            double blended_v = next.v(row, target_col) + velocity_blend * (target_v - next.v(row, target_col));
            next.u(row, target_col) =
                move_toward(next.u(row, target_col), blended_u, max_speed_step * support_weight);
            next.v(row, target_col) =
                move_toward(next.v(row, target_col), blended_v, max_speed_step * support_weight);
        };

        shape_cell(donor_row, col, donor_target_u, donor_target_v);
        shape_cell(receiver_row, receiver_col, receiver_target_u, receiver_target_v);
    }
}

}  // namespace raftsim::solver_detail
