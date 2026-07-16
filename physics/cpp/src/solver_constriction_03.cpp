#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_lower_edge_contraction_face_velocity_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double max_speed_step = kConstrictionLowerEdgeContractionFaceMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double contraction_weight =
            constriction_lower_edge_contraction_face_weight(scenario, throat_width_cells, col);
        double post_contraction_weight =
            constriction_lower_edge_post_contraction_face_weight(scenario, col);
        double face_weight = std::max(contraction_weight, post_contraction_weight);
        if (face_weight <= 0.0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        if (!inside_relaxed_wet_band(scenario, band, throat_width_cells, col, lower_shelf_row) &&
            !inside_constriction_local_shallow_fringe(
                scenario, band, throat_width_cells, col, lower_shelf_row)) {
            continue;
        }

        bool entry_column = constriction_lower_edge_contraction_entry_column(scenario, col);

        double shelf_fraction = kConstrictionLowerEdgeContractionFaceApproachShelfCrossStreamFraction;
        double first_wet_fraction = kConstrictionLowerEdgeContractionFaceApproachFirstWetCrossStreamFraction;
        if (post_contraction_weight > 0.0) {
            shelf_fraction = kConstrictionLowerEdgeContractionFacePostEntryShelfCrossStreamFraction;
            first_wet_fraction = kConstrictionLowerEdgeContractionFacePostEntryFirstWetCrossStreamFraction;
        } else if (entry_column) {
            shelf_fraction = kConstrictionLowerEdgeContractionFaceEntryShelfCrossStreamFraction;
            first_wet_fraction = kConstrictionLowerEdgeContractionFaceEntryFirstWetCrossStreamFraction;
        }

        auto shape_lower_face_row = [&](std::size_t row, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = cross_stream_fraction * reference_speed;
            double blend =
                clamp(kConstrictionLowerEdgeContractionFaceVelocityRate * dt * face_weight, 0.0, 1.0);
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * face_weight);
        };

        shape_lower_face_row(lower_shelf_row, shelf_fraction);
        shape_lower_face_row(band.first_row, first_wet_fraction);
    }
}

void apply_constriction_upstream_edge_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpstreamEdgeSupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamEdgeOppositionMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double edge_target_h = std::max(
            kConstrictionYFaceStateMinDepth,
            column_mean_depth * kConstrictionUpstreamEdgeSupportTargetDepthScale);
        double interior_target_h = std::max(
            edge_target_h,
            column_mean_depth * kConstrictionUpstreamEdgeSupportInteriorDepthScale);

        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;
        if (band.last_row > band.first_row + 1) {
            for (std::size_t receiver_row = band.first_row + 1; receiver_row < band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                double current_h = next.h(receiver_row, col);
                if (current_h <= config.dry_tolerance || current_h >= interior_target_h) {
                    continue;
                }
                double capacity = interior_target_h - current_h;
                receivers.push_back(ConstrictionDepthTransferCell{receiver_row, col, capacity});
                receiver_capacity += capacity;
            }
        }

        double distributable_depth = receiver_capacity;
        auto support_edge = [&](std::size_t row) {
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                return;
            }

            double requested_depth = 0.0;
            if (current_h > edge_target_h && distributable_depth > config.dry_tolerance) {
                double depth_error = current_h - edge_target_h;
                requested_depth = std::min(
                    depth_error,
                    std::min(depth_error * kConstrictionUpstreamEdgeSupportRate * dt * approach_weight,
                             max_depth_step * approach_weight));
                requested_depth = std::min(requested_depth, distributable_depth);
            }

            if (requested_depth > config.dry_tolerance && receiver_capacity > 0.0) {
                double target_u =
                    constriction_response_target_u(next.u(row, col), scenario.initial.u(row, col), flow_sign);
                for (const ConstrictionDepthTransferCell& receiver : receivers) {
                    double added_h = requested_depth * receiver.capacity / receiver_capacity;
                    if (added_h <= 0.0) {
                        continue;
                    }
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + added_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * target_u;
                    double merged_hv = receiver_h * next.v(receiver.row, receiver.col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                }
                next.h(row, col) = std::max(config.dry_tolerance, current_h - requested_depth);
                distributable_depth -= requested_depth;
            }

            double supported_h = next.h(row, col);
            if (supported_h <= config.dry_tolerance) {
                return;
            }

            double lateral_sign = constriction_lateral_sign(band, row);
            double target_u = flow_sign * kConstrictionUpstreamEdgeOppositionSpeedFraction * reference_speed;
            double target_v =
                -lateral_sign * kConstrictionUpstreamEdgeOppositionCrossStreamFraction * reference_speed;
            double blend = clamp(kConstrictionUpstreamEdgeOppositionVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        support_edge(band.first_row);
        if (band.last_row != band.first_row) {
            support_edge(band.last_row);
        }
    }
}

void apply_constriction_lower_edge_width_depth_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionLowerEdgeWidthDepthBalanceMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionLowerEdgeWidthDepthBalanceMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t receiver_row = band.first_row - 1;
        if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
            continue;
        }

        auto shape_lower_row = [&](std::size_t row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
            double target_v = kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
            double blend = clamp(kConstrictionLowerEdgeWidthDepthBalanceVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        double current_h = next.h(receiver_row, col);
        double target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionLowerEdgeWidthDepthBalanceTargetDepthScale);
        if (current_h >= target_h) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
        }

        std::vector<ConstrictionDepthTransferCell> donors;
        double donor_capacity = 0.0;
        double donor_floor = column_mean_depth * kConstrictionLowerEdgeWidthDepthBalanceDonorFloorScale;
        for (std::size_t donor_row = band.first_row; donor_row <= band.last_row; ++donor_row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, donor_row)) {
                continue;
            }
            double donor_h = next.h(donor_row, col);
            if (donor_h <= donor_floor) {
                continue;
            }
            double capacity = donor_h - donor_floor;
            donors.push_back(ConstrictionDepthTransferCell{donor_row, col, capacity});
            donor_capacity += capacity;
        }
        if (donor_capacity <= config.dry_tolerance) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
        }

        double requested_h = (target_h - current_h) * kConstrictionLowerEdgeWidthDepthBalanceRate * dt * approach_weight;
        double transfer_h = std::min(
            target_h - current_h,
            std::min(requested_h, std::min(max_depth_step * approach_weight, donor_capacity)));
        if (transfer_h <= config.dry_tolerance) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
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

        double target_u =
            flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
        double target_v =
            kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
        double merged_h = current_h + transfer_h;
        double merged_hu = current_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = current_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        shape_lower_row(receiver_row);
        shape_lower_row(band.first_row);
    }
}

void apply_constriction_lower_edge_final_support(
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

    double max_depth_step = kConstrictionLowerEdgeFinalSupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionLowerEdgeFinalSupportMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        double transition_weight = constriction_transition_edge_face_weight(scenario, col);
        double velocity_weight = std::max(approach_weight, transition_weight);
        if (velocity_weight > 0.0) {
            velocity_weight = std::max(
                velocity_weight,
                kConstrictionLowerEdgeFinalSupportTransitionVelocityWeightFloor);
        }
        if (approach_weight <= 0.0 && velocity_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (band.first_row > 1) {
            std::size_t shelf_row = band.first_row - 2;
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, shelf_row)) {
                double target_h = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionLowerEdgeFinalSupportTargetDepthScale);
                double receiver_capacity = std::max(0.0, target_h - next.h(shelf_row, col));
                double donor_floor = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionLowerEdgeFinalSupportDonorFloorScale);
                double donor_capacity = std::max(0.0, next.h(band.first_row, col) - donor_floor);
                if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
                    double requested_h =
                        receiver_capacity * kConstrictionLowerEdgeFinalSupportRate * dt * approach_weight;
                    double transfer_h = std::min(
                        receiver_capacity,
                        std::min(donor_capacity, std::min(requested_h, max_depth_step * approach_weight)));
                    if (transfer_h > config.dry_tolerance) {
                        next.h(band.first_row, col) = std::max(0.0, next.h(band.first_row, col) - transfer_h);
                        if (next.h(band.first_row, col) <= config.dry_tolerance) {
                            next.h(band.first_row, col) = 0.0;
                            next.u(band.first_row, col) = 0.0;
                            next.v(band.first_row, col) = 0.0;
                        }

                        double receiver_h = next.h(shelf_row, col);
                        double target_u = next.u(band.first_row, col);
                        double target_v = kConstrictionLowerEdgeFinalSupportCrossStreamFraction * reference_speed;
                        double merged_h = receiver_h + transfer_h;
                        double merged_hu = receiver_h * next.u(shelf_row, col) + transfer_h * target_u;
                        double merged_hv = receiver_h * next.v(shelf_row, col) + transfer_h * target_v;
                        next.h(shelf_row, col) = merged_h;
                        next.u(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                        next.v(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                    }
                }
            }
        }

        auto shape_lower_row = [&](std::size_t row, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_v = cross_stream_fraction * kConstrictionLowerEdgeFinalSupportCrossStreamFraction *
                              reference_speed;
            double blend = clamp(kConstrictionLowerEdgeFinalSupportVelocityRate * dt * velocity_weight, 0.0, 1.0);
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * velocity_weight);
        };

        if (band.first_row > 0) {
            shape_lower_row(band.first_row - 1, 1.0);
        }
        shape_lower_row(band.first_row, kConstrictionLowerEdgeFinalSupportInteriorCrossStreamFraction);

        double signed_x = constriction_signed_x(scenario, col);
        double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
        double upstream_edge_distance = -signed_x - half_length;
        double pre_throat_shelf_weight =
            signed_x < -half_length
                ? 1.0 - clamp(upstream_edge_distance / std::max(scenario.grid.dx, 1.0e-9), 0.0, 1.0)
                : 0.0;
        double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
        double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
        double transition_shelf_response =
            clamp(
                (response_progress - kConstrictionLowerEdgeFinalSupportTransitionShelfResponseStart) /
                    std::max(1.0e-9, 1.0 - kConstrictionLowerEdgeFinalSupportTransitionShelfResponseStart),
                0.0,
                1.0);
        double transition_shelf_weight = pre_throat_shelf_weight * transition_shelf_response;
        auto shape_transition_shelf_row = [&](std::size_t shelf_row) {
            if (next.h(shelf_row, col) > config.dry_tolerance) {
                double target_u = constriction_flow_sign(scenario) *
                                  kConstrictionLowerEdgeFinalSupportTransitionShelfSpeedFraction *
                                  reference_speed;
                double target_v =
                    kConstrictionLowerEdgeFinalSupportTransitionShelfCrossStreamFraction * reference_speed;
                double transition_step =
                    kConstrictionLowerEdgeFinalSupportTransitionShelfMaxSpeedPerSecond * dt *
                    transition_shelf_weight;
                double transition_blend =
                    clamp(
                        kConstrictionLowerEdgeFinalSupportTransitionShelfVelocityRate * dt *
                            transition_shelf_weight,
                        0.0,
                        1.0);
                double blended_u =
                    next.u(shelf_row, col) + transition_blend * (target_u - next.u(shelf_row, col));
                double blended_v =
                    next.v(shelf_row, col) + transition_blend * (target_v - next.v(shelf_row, col));
                next.u(shelf_row, col) =
                    move_toward(next.u(shelf_row, col), blended_u, transition_step);
                next.v(shelf_row, col) =
                    move_toward(next.v(shelf_row, col), blended_v, transition_step);
            }
        };
        if (transition_shelf_weight > 0.0) {
            if (band.first_row > 1) {
                std::size_t outer_shelf_row = band.first_row - 2;
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, outer_shelf_row)) {
                    shape_transition_shelf_row(outer_shelf_row);
                }
            }
            if (band.first_row > 0) {
                shape_transition_shelf_row(band.first_row - 1);
            }
        }

        double far_approach_weight =
            clamp(
                (approach_weight - kConstrictionLowerEdgeFinalSupportFarApproachStart) /
                    std::max(1.0e-9, 1.0 - kConstrictionLowerEdgeFinalSupportFarApproachStart),
                0.0,
                1.0);
        double far_response =
            clamp(
                (response_progress - kConstrictionLowerEdgeFinalSupportFarResponseStart) /
                    std::max(1.0e-9, 1.0 - kConstrictionLowerEdgeFinalSupportFarResponseStart),
                0.0,
                1.0);
        double far_weight = far_approach_weight * far_response;
        if (far_weight <= 0.0) {
            continue;
        }

        std::size_t upstream_distance_cells =
            constriction_flow_sign(scenario) >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        double inlet_ramp = clamp(static_cast<double>(upstream_distance_cells), 0.0, 1.0);
        double outer_shelf_speed_fraction =
            kConstrictionLowerEdgeFinalSupportInletShelfSpeedFraction +
            inlet_ramp *
                (kConstrictionLowerEdgeFinalSupportOuterShelfSpeedFraction -
                 kConstrictionLowerEdgeFinalSupportInletShelfSpeedFraction);
        double far_response_step =
            kConstrictionLowerEdgeFinalSupportFarMaxSpeedPerSecond * dt * far_weight;
        double far_response_blend =
            clamp(kConstrictionLowerEdgeFinalSupportFarVelocityRate * dt * far_weight, 0.0, 1.0);
        auto shape_far_upstream_lower_shelf_row =
            [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
                if (next.h(row, col) <= config.dry_tolerance) {
                    return;
                }
                double target_u = constriction_flow_sign(scenario) * speed_fraction * reference_speed;
                double target_v = cross_stream_fraction * reference_speed;
                double blended_u = next.u(row, col) + far_response_blend * (target_u - next.u(row, col));
                double blended_v = next.v(row, col) + far_response_blend * (target_v - next.v(row, col));
                next.u(row, col) = move_toward(next.u(row, col), blended_u, far_response_step);
                next.v(row, col) = move_toward(next.v(row, col), blended_v, far_response_step);
            };

        if (band.first_row > 1) {
            std::size_t outer_shelf_row = band.first_row - 2;
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, outer_shelf_row)) {
                shape_far_upstream_lower_shelf_row(
                    outer_shelf_row,
                    outer_shelf_speed_fraction,
                    kConstrictionLowerEdgeFinalSupportOuterShelfCrossStreamFraction);
            }
        }
        if (band.first_row > 0) {
            shape_far_upstream_lower_shelf_row(
                band.first_row - 1,
                kConstrictionLowerEdgeFinalSupportLowerShelfSpeedFraction,
                kConstrictionLowerEdgeFinalSupportLowerShelfCrossStreamFraction);
        }
        shape_far_upstream_lower_shelf_row(
            band.first_row,
            kConstrictionLowerEdgeFinalSupportFirstWetSpeedFraction,
            kConstrictionLowerEdgeFinalSupportFirstWetCrossStreamFraction);
    }
}

void apply_constriction_upstream_shelf_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double max_depth_step = kConstrictionUpstreamShelfBalanceMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamShelfBalanceMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0 ||
            band.last_row == band.first_row) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        std::size_t upper_edge_row = band.last_row;
        std::size_t upper_inner_row = band.last_row - 1;
        if (!inside_relaxed_wet_band(scenario, band, throat_width_cells, col, lower_shelf_row) ||
            !inside_relaxed_wet_band(scenario, band, throat_width_cells, col, upper_edge_row)) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamShelfBalanceUpperDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(upper_edge_row, col) - donor_floor);
        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;

        auto add_receiver = [&](std::size_t row, double target_scale) {
            double target_h = std::max(kConstrictionLocalFringeTargetDepth, column_mean_depth * target_scale);
            double capacity = std::max(0.0, target_h - next.h(row, col));
            if (capacity > config.dry_tolerance) {
                receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                receiver_capacity += capacity;
            }
        };

        add_receiver(lower_shelf_row, kConstrictionUpstreamShelfBalanceLowerShelfDepthScale);
        add_receiver(band.first_row, kConstrictionUpstreamShelfBalanceLowerFirstWetDepthScale);

        double transfer_h = 0.0;
        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamShelfBalanceRate * dt * approach_weight;
            transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * approach_weight)));
        }

        if (transfer_h > config.dry_tolerance) {
            next.h(upper_edge_row, col) =
                std::max(donor_floor, next.h(upper_edge_row, col) - transfer_h);
            for (const ConstrictionDepthTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + added_h;
                double merged_hu = receiver_h * next.u(receiver.row, receiver.col) +
                                   added_h * next.u(receiver.row, receiver.col);
                double target_v =
                    receiver.row == lower_shelf_row
                        ? kConstrictionUpstreamShelfBalanceLowerShelfCrossStreamFraction * reference_speed
                        : kConstrictionUpstreamShelfBalanceLowerFirstWetCrossStreamFraction * reference_speed;
                double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * target_v;
                next.h(receiver.row, receiver.col) = merged_h;
                next.u(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        auto shape_row = [&](std::size_t row, double target_v) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double blend = clamp(kConstrictionUpstreamShelfBalanceVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        shape_row(
            lower_shelf_row,
            kConstrictionUpstreamShelfBalanceLowerShelfCrossStreamFraction * reference_speed);
        shape_row(
            band.first_row,
            kConstrictionUpstreamShelfBalanceLowerFirstWetCrossStreamFraction * reference_speed);
        shape_row(
            upper_edge_row,
            -kConstrictionUpstreamShelfBalanceUpperEdgeCrossStreamFraction * reference_speed);
        shape_row(
            upper_inner_row,
            -kConstrictionUpstreamShelfBalanceUpperInnerCrossStreamFraction * reference_speed);
    }
}

void apply_constriction_upstream_centerline_timing_balance(
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
    double late_response = clamp((response_progress - 0.5) / 0.5, 0.0, 1.0);
    if (late_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double max_depth_step = kConstrictionUpstreamCenterlineTimingMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamCenterlineTimingMaxSpeedPerSecond * dt;
    double flow_sign = constriction_flow_sign(scenario);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= 0.0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        double near_throat_weight = signed_x < -half_length
                                        ? 1.0 - approach_weight
                                        : clamp(-signed_x / half_length, 0.0, 1.0);
        if (approach_weight <= 0.0 && near_throat_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        double target_h = column_mean_depth * kConstrictionUpstreamCenterlineTimingTargetDepthScale;
        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (edge_norm > kConstrictionUpstreamCenterlineTimingInteriorEdgeNorm ||
                next.h(row, col) >= target_h) {
                continue;
            }
            double capacity = target_h - next.h(row, col);
            if (capacity > config.dry_tolerance) {
                receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                receiver_capacity += capacity;
            }
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamCenterlineTimingDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        double transfer_weight = late_response * std::max(approach_weight, near_throat_weight);
        double transfer_h = 0.0;
        if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance &&
            transfer_weight > 0.0) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamCenterlineTimingRate * dt * transfer_weight;
            transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * transfer_weight)));
        }

        double target_speed_fraction =
            kConstrictionUpstreamCenterlineTimingFarSpeedFraction +
            near_throat_weight *
                (kConstrictionUpstreamCenterlineTimingNearSpeedFraction -
                 kConstrictionUpstreamCenterlineTimingFarSpeedFraction);
        double target_cross_stream_fraction =
            kConstrictionUpstreamCenterlineTimingFarCrossStreamFraction +
            near_throat_weight *
                (kConstrictionUpstreamCenterlineTimingNearCrossStreamFraction -
                 kConstrictionUpstreamCenterlineTimingFarCrossStreamFraction);
        double target_u = flow_sign * target_speed_fraction * reference_speed;
        double target_v = -target_cross_stream_fraction * reference_speed;

        if (transfer_h > config.dry_tolerance) {
            next.h(band.last_row, col) = std::max(donor_floor, next.h(band.last_row, col) - transfer_h);
            for (const ConstrictionDepthTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
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

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (edge_norm > kConstrictionUpstreamCenterlineTimingInteriorEdgeNorm) {
                continue;
            }
            double interior_weight =
                1.0 - edge_norm / std::max(kConstrictionUpstreamCenterlineTimingInteriorEdgeNorm, 1.0e-9);
            double blend =
                clamp(kConstrictionUpstreamCenterlineTimingVelocityRate * dt * transfer_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * interior_weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * interior_weight * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * transfer_weight * interior_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * transfer_weight * interior_weight);
        }

        auto shape_edge_cross_stream = [&](std::size_t row, double target_v) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double blend =
                clamp(kConstrictionUpstreamCenterlineTimingVelocityRate * dt * transfer_weight, 0.0, 1.0);
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * transfer_weight);
        };

        if (band.first_row > 0) {
            shape_edge_cross_stream(
                band.first_row - 1,
                kConstrictionUpstreamCenterlineTimingEdgeCrossStreamFraction * reference_speed);
        }
        shape_edge_cross_stream(
            band.last_row,
            -kConstrictionUpstreamCenterlineTimingEdgeCrossStreamFraction * reference_speed);
    }
}

void apply_constriction_upstream_boundary_column_support(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    std::size_t col = flow_sign >= 0.0 ? 0 : scenario.grid.nx - 1;
    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells || reference_speed <= 0.0) {
        return;
    }

    std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
    if (relax_cells == 0) {
        return;
    }
    std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
    std::size_t lower_span = std::min<std::size_t>(
        kConstrictionUpstreamBoundarySupportLowerSpanCells,
        std::max<std::size_t>(1, band.count / 2));
    std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.first_row + lower_span);

    double max_depth_step = kConstrictionUpstreamBoundarySupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamBoundarySupportMaxSpeedPerSecond * dt;
    double velocity_blend = clamp(kConstrictionUpstreamBoundarySupportVelocityRate * dt, 0.0, 1.0);
    for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
        double target_h = 0.0;
        double target_u = 0.0;
        double target_v = 0.0;
        if (row < band.first_row) {
            target_h = boundary->depth * kConstrictionUpstreamBoundarySupportShelfDepthScale;
            target_u = boundary->velocity_x * kConstrictionUpstreamBoundarySupportShelfSpeedFraction;
            target_v = kConstrictionUpstreamBoundarySupportShelfCrossStreamFraction * reference_speed;
        } else {
            double t = static_cast<double>(row - band.first_row) / static_cast<double>(lower_span);
            target_h = boundary->depth *
                       (kConstrictionUpstreamBoundarySupportLowerDepthScale +
                        t * (kConstrictionUpstreamBoundarySupportInteriorDepthScale -
                             kConstrictionUpstreamBoundarySupportLowerDepthScale));
            double speed_fraction =
                kConstrictionUpstreamBoundarySupportLowerSpeedFraction +
                t * (kConstrictionUpstreamBoundarySupportInteriorSpeedFraction -
                     kConstrictionUpstreamBoundarySupportLowerSpeedFraction);
            double cross_stream_fraction =
                kConstrictionUpstreamBoundarySupportLowerCrossStreamFraction +
                t * (kConstrictionUpstreamBoundarySupportInteriorCrossStreamFraction -
                     kConstrictionUpstreamBoundarySupportLowerCrossStreamFraction);
            target_u = flow_sign * speed_fraction * reference_speed;
            target_v = cross_stream_fraction * reference_speed;
        }

        double current_h = next.h(row, col);
        if (target_h > current_h) {
            double requested_h = (target_h - current_h) * kConstrictionUpstreamBoundarySupportRate * dt;
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
            continue;
        }
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
    }
}

void apply_constriction_upper_edge_opposition_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpperEdgeOppositionBalanceMaxDepthPerSecond * dt;
    double max_shelf_depth_step = kConstrictionUpperOutsideShelfSupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpperEdgeOppositionBalanceMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t receiver_row = band.first_row - 1;
        double receiver_target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpperEdgeOppositionBalanceReceiverDepthScale);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, col));
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpperEdgeOppositionBalanceDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpperEdgeOppositionBalanceRate * dt * approach_weight;
            double transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * approach_weight)));
            if (transfer_h > config.dry_tolerance) {
                double donor_h = next.h(band.last_row, col);
                next.h(band.last_row, col) = std::max(0.0, donor_h - transfer_h);
                if (next.h(band.last_row, col) <= config.dry_tolerance) {
                    next.h(band.last_row, col) = 0.0;
                    next.u(band.last_row, col) = 0.0;
                    next.v(band.last_row, col) = 0.0;
                }

                double target_u = flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
                double target_v = kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
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

        if (band.last_row + 1 < scenario.grid.ny) {
            std::size_t shelf_row = std::min(scenario.grid.ny - 1, band.last_row + 2);
            if (shelf_row > band.last_row &&
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, shelf_row)) {
                double shelf_target_h = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionUpperOutsideShelfSupportTargetDepthScale);
                double shelf_capacity = std::max(0.0, shelf_target_h - next.h(shelf_row, col));
                double donor_floor = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionUpperOutsideShelfSupportDonorFloorScale);
                double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
                if (shelf_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
                    double requested_h =
                        shelf_capacity * kConstrictionUpperOutsideShelfSupportRate * dt * approach_weight;
                    double transfer_h = std::min(
                        shelf_capacity,
                        std::min(donor_capacity, std::min(requested_h, max_shelf_depth_step * approach_weight)));
                    if (transfer_h > config.dry_tolerance) {
                        double donor_h = next.h(band.last_row, col);
                        next.h(band.last_row, col) = std::max(0.0, donor_h - transfer_h);
                        if (next.h(band.last_row, col) <= config.dry_tolerance) {
                            next.h(band.last_row, col) = 0.0;
                            next.u(band.last_row, col) = 0.0;
                            next.v(band.last_row, col) = 0.0;
                        }

                        double target_u = flow_sign * kConstrictionUpperOutsideShelfSupportSpeedFraction * reference_speed;
                        double target_v = -kConstrictionUpperOutsideShelfSupportCrossStreamFraction * reference_speed;
                        double receiver_h = next.h(shelf_row, col);
                        double merged_h = receiver_h + transfer_h;
                        double merged_hu = receiver_h * next.u(shelf_row, col) + transfer_h * target_u;
                        double merged_hv = receiver_h * next.v(shelf_row, col) + transfer_h * target_v;
                        next.h(shelf_row, col) = merged_h;
                        next.u(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                        next.v(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                    }
                }
            }
        }

        auto shape_upper_row = [&](std::size_t row, double cross_stream_fraction) {
            double h = next.h(row, col);
            if (h <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionUpperEdgeOppositionBalanceSpeedFraction * reference_speed;
            double target_v = -kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction *
                              cross_stream_fraction * reference_speed;
            double blend = clamp(kConstrictionUpperEdgeOppositionBalanceVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        if (band.last_row > band.first_row) {
            shape_upper_row(band.last_row - 1, kConstrictionUpperEdgeOppositionBalanceInteriorCrossStreamFraction);
        }
        shape_upper_row(band.last_row, 1.0);
        if (band.last_row + 1 < scenario.grid.ny) {
            std::size_t shelf_row = std::min(scenario.grid.ny - 1, band.last_row + 2);
            if (shelf_row > band.last_row &&
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, shelf_row)) {
                shape_upper_row(shelf_row, kConstrictionUpperOutsideShelfSupportCrossStreamFraction /
                                               kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction);
            }
        }
    }
}

void apply_constriction_upper_edge_flux_magnitude_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionUpperEdgeFluxMagnitudeMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        auto shape_flux_row = [&](std::size_t row, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionUpperEdgeFluxMagnitudeSpeedFraction * reference_speed;
            double target_v = -cross_stream_fraction * kConstrictionUpperEdgeFluxMagnitudeCrossStreamFraction *
                              reference_speed;
            double blend = clamp(kConstrictionUpperEdgeFluxMagnitudeRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        if (band.last_row > band.first_row) {
            shape_flux_row(band.last_row - 1, kConstrictionUpperEdgeFluxMagnitudeInteriorCrossStreamFraction);
        }
        shape_flux_row(band.last_row, 1.0);
    }
}

void apply_constriction_upstream_boundary_upper_edge_velocity_shape(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
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

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionUpstreamBoundaryUpperEdgeShapeMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (upstream_distance_cells > kConstrictionUpstreamBoundaryUpperEdgeShapeWindowCells) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        auto shape_row = [&](std::size_t row, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionUpstreamBoundaryUpperEdgeShapeSpeedFraction * reference_speed;
            double target_v = -cross_stream_fraction * reference_speed;
            double blend =
                clamp(kConstrictionUpstreamBoundaryUpperEdgeShapeRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        if (band.last_row > band.first_row) {
            shape_row(band.last_row - 1, kConstrictionUpstreamBoundaryUpperEdgeShapeInteriorCrossStreamFraction);
        }
        shape_row(band.last_row, kConstrictionUpstreamBoundaryUpperEdgeShapeCrossStreamFraction);
    }
}

void apply_constriction_upstream_boundary_upper_edge_profile_release(
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

    double flow_sign = constriction_flow_sign(scenario);
    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double late_response =
        clamp(
            (response_progress - kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseResponseStart),
            0.0,
            1.0);
    if (late_response <= 0.0) {
        return;
    }

    double max_depth_step = kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (upstream_distance_cells > kConstrictionUpstreamBoundaryUpperEdgeShapeWindowCells) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }
        double response_weight = approach_weight * late_response;

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double window_span = std::max(1.0, static_cast<double>(kConstrictionUpstreamBoundaryUpperEdgeShapeWindowCells));
        double inlet_weight = 1.0 - clamp(static_cast<double>(upstream_distance_cells) / window_span, 0.0, 1.0);
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;

        auto add_receiver = [&](std::size_t row, double target_scale, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || row == band.last_row) {
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
                -cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        if (band.last_row > band.first_row) {
            add_receiver(
                band.last_row - 1,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorTargetScale,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorCrossStreamFraction);
        }
        if (band.last_row > band.first_row + 1) {
            add_receiver(
                band.last_row - 2,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorTargetScale,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorCrossStreamFraction);
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            double immediate_shelf_target_scale =
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfTargetScale +
                inlet_weight * kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfInletBonusScale;
            add_receiver(
                band.last_row + 1,
                immediate_shelf_target_scale,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfCrossStreamFraction);
        }
        if (band.last_row + 2 < scenario.grid.ny) {
            double outer_shelf_target_scale =
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfTargetScale +
                inlet_weight * kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfInletBonusScale;
            add_receiver(
                band.last_row + 2,
                outer_shelf_target_scale,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfCrossStreamFraction);
        }

        double transfer_h = 0.0;
        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h = receiver_capacity *
                                 kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseRate * dt * response_weight;
            transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
        }

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
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = -cross_stream_fraction * reference_speed;
            double blend =
                clamp(kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseVelocityRate * dt * response_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * response_weight);
        };

        if (band.last_row > band.first_row) {
            shape_row(
                band.last_row - 1,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseUpperInteriorCrossStreamFraction);
        }
        shape_row(
            band.last_row,
            kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseEdgeSpeedFraction,
            kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseEdgeCrossStreamFraction);
        if (band.last_row + 1 < scenario.grid.ny) {
            shape_row(
                band.last_row + 1,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseImmediateShelfCrossStreamFraction);
        }
        if (band.last_row + 2 < scenario.grid.ny) {
            shape_row(
                band.last_row + 2,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeProfileReleaseOuterShelfCrossStreamFraction);
        }
    }
}

void apply_constriction_upstream_boundary_upper_edge_final_shelf_release(
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
            (response_progress - kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseMaxDepthPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        std::size_t upstream_distance_cells =
            flow_sign >= 0.0 ? col : (scenario.grid.nx - 1 - col);
        if (upstream_distance_cells > kConstrictionUpstreamBoundaryUpperEdgeShapeWindowCells) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0 || next.h(band.last_row, col) <= config.dry_tolerance) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double response_weight = approach_weight * final_response;
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](
                                std::size_t row,
                                double target_scale,
                                double speed_fraction,
                                double signed_cross_stream_fraction) {
            if (row >= scenario.grid.ny || row == band.last_row) {
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
                signed_cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        };

        if (band.first_row > 0) {
            add_receiver(
                band.first_row - 1,
                kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseLowerShelfTargetScale,
                kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseLowerShelfSpeedFraction,
                kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseLowerShelfCrossStreamFraction);
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            add_receiver(
                band.last_row + 1,
                kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseUpperShelfTargetScale,
                kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseUpperShelfSpeedFraction,
                -kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseUpperShelfCrossStreamFraction);
        }
        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }
        double requested_h = receiver_capacity *
                             kConstrictionUpstreamBoundaryUpperEdgeFinalShelfReleaseRate * dt * response_weight;
        double transfer_h = std::min(
            receiver_capacity,
            std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

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
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }
}

void apply_constriction_upstream_approach_final_profile_balance(
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
            (response_progress - kConstrictionUpstreamApproachFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamApproachFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpstreamApproachFinalProfileMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionUpstreamApproachFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= -half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }
        double response_weight = approach_weight * final_response;
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamApproachFinalProfileUpperEdgeDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;

        auto add_receiver = [&](
                                std::size_t row,
                                double target_scale,
                                double speed_fraction,
                                double cross_stream_fraction) {
            if (row >= scenario.grid.ny || row == band.last_row) {
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

        if (band.first_row > 1) {
            add_receiver(
                band.first_row - 2,
                kConstrictionUpstreamApproachFinalProfileLowerOuterShelfTargetScale,
                kConstrictionUpstreamApproachFinalProfileLowerOuterShelfSpeedFraction,
                kConstrictionUpstreamApproachFinalProfileLowerOuterShelfCrossStreamFraction);
        }
        if (band.first_row > 0) {
            add_receiver(
                band.first_row - 1,
                kConstrictionUpstreamApproachFinalProfileLowerShelfTargetScale,
                kConstrictionUpstreamApproachFinalProfileLowerShelfSpeedFraction,
                kConstrictionUpstreamApproachFinalProfileLowerShelfCrossStreamFraction);
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            add_receiver(
                band.last_row + 1,
                kConstrictionUpstreamApproachFinalProfileUpperShelfTargetScale,
                kConstrictionUpstreamApproachFinalProfileUpperShelfSpeedFraction,
                -kConstrictionUpstreamApproachFinalProfileUpperShelfCrossStreamFraction);
        }

        if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpstreamApproachFinalProfileDepthRate * dt * response_weight;
            double transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
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

        double velocity_blend =
            clamp(kConstrictionUpstreamApproachFinalProfileVelocityRate * dt * response_weight, 0.0, 1.0);
        auto shape_row = [&](std::size_t row, double target_u, double target_v, double weight) {
            if (row >= scenario.grid.ny || weight <= 0.0 || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double blended_u = next.u(row, col) + velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * response_weight * weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * response_weight * weight);
        };

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = band.first_row + 1; row < band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance ||
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double signed_row_offset = static_cast<double>(row) - center;
            double edge_norm = std::min(1.0, std::abs(signed_row_offset) / half_span);
            double lateral_bias = signed_row_offset >= 0.0
                                      ? kConstrictionUpstreamApproachFinalProfileInteriorUpperBiasFraction
                                      : kConstrictionUpstreamApproachFinalProfileInteriorLowerBiasFraction;
            double speed_fraction =
                kConstrictionUpstreamApproachFinalProfileInteriorCenterSpeedFraction +
                kConstrictionUpstreamApproachFinalProfileInteriorEdgeSpeedFraction *
                    std::pow(edge_norm, kConstrictionUpstreamApproachFinalProfileInteriorEdgeExponent) +
                lateral_bias * edge_norm;
            double target_u = flow_sign * speed_fraction * reference_speed;
            shape_row(row, target_u, next.v(row, col), 1.0);
        }

        shape_row(
            band.last_row,
            flow_sign * kConstrictionUpstreamApproachFinalProfileUpperEdgeSpeedFraction * reference_speed,
            -kConstrictionUpstreamApproachFinalProfileUpperEdgeCrossStreamFraction * reference_speed,
            1.0);
        if (band.first_row > 1) {
            shape_row(
                band.first_row - 2,
                flow_sign * kConstrictionUpstreamApproachFinalProfileLowerOuterShelfSpeedFraction * reference_speed,
                kConstrictionUpstreamApproachFinalProfileLowerOuterShelfCrossStreamFraction * reference_speed,
                0.7);
        }
        if (band.first_row > 0) {
            shape_row(
                band.first_row - 1,
                flow_sign * kConstrictionUpstreamApproachFinalProfileLowerShelfSpeedFraction * reference_speed,
                kConstrictionUpstreamApproachFinalProfileLowerShelfCrossStreamFraction * reference_speed,
                1.0);
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            shape_row(
                band.last_row + 1,
                flow_sign * kConstrictionUpstreamApproachFinalProfileUpperShelfSpeedFraction * reference_speed,
                -kConstrictionUpstreamApproachFinalProfileUpperShelfCrossStreamFraction * reference_speed,
                1.0);
        }
    }
}

void apply_constriction_upstream_upper_core_final_profile(
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
            (response_progress - kConstrictionUpstreamUpperCoreFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamUpperCoreFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpstreamUpperCoreFinalProfileMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionUpstreamUpperCoreFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= -half_length) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 ||
            band.last_row <= band.first_row + kConstrictionUpstreamUpperCoreFinalProfileDonorOffsetFromLast + 1) {
            continue;
        }

        std::size_t donor_row =
            band.last_row - kConstrictionUpstreamUpperCoreFinalProfileDonorOffsetFromLast;
        if (donor_row <= band.first_row || next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }
        double response_weight = approach_weight * final_response;
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamUpperCoreFinalProfileDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        double receiver_start = static_cast<double>(band.first_row + 1);
        double receiver_span = std::max(1.0, static_cast<double>(donor_row - band.first_row - 1));
        for (std::size_t row = band.first_row + 1; row < donor_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double target_h = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionUpstreamUpperCoreFinalProfileInteriorTargetScale);
            double capacity = std::max(0.0, target_h - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                continue;
            }

            double position = clamp((static_cast<double>(row) - receiver_start) / receiver_span, 0.0, 1.0);
            double speed_fraction = kConstrictionUpstreamUpperCoreFinalProfileCenterSpeedFraction;
            double cross_stream_fraction = kConstrictionUpstreamUpperCoreFinalProfileCenterCrossStreamFraction;
            if (row + 1 == donor_row) {
                speed_fraction = kConstrictionUpstreamUpperCoreFinalProfileUpperAdjacentSpeedFraction;
                cross_stream_fraction =
                    kConstrictionUpstreamUpperCoreFinalProfileUpperAdjacentCrossStreamFraction;
            } else if (position >= 0.62) {
                speed_fraction = kConstrictionUpstreamUpperCoreFinalProfileUpperInteriorSpeedFraction;
                cross_stream_fraction = kConstrictionUpstreamUpperCoreFinalProfileUpperCrossStreamFraction;
            } else if (position <= 0.22) {
                speed_fraction = kConstrictionUpstreamUpperCoreFinalProfileLowerInteriorSpeedFraction;
                cross_stream_fraction = kConstrictionUpstreamUpperCoreFinalProfileLowerCrossStreamFraction;
            }

            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * speed_fraction * reference_speed,
                cross_stream_fraction * reference_speed,
            });
            receiver_capacity += capacity;
        }

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionUpstreamUpperCoreFinalProfileDepthRate * dt * response_weight;
        double transfer_h = std::min(
            receiver_capacity,
            std::min(donor_capacity, std::min(requested_h, max_depth_step * response_weight)));
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

        double velocity_blend =
            clamp(kConstrictionUpstreamUpperCoreFinalProfileVelocityRate * dt * response_weight, 0.0, 1.0);
        double target_u = flow_sign * kConstrictionUpstreamUpperCoreFinalProfileDonorSpeedFraction * reference_speed;
        double donor_overfull_weight = clamp(
            (next.h(donor_row, col) - donor_floor) /
                std::max(1.0e-9, column_mean_depth - donor_floor),
            0.0,
            1.0);
        double donor_cross_stream_fraction =
            kConstrictionUpstreamUpperCoreFinalProfileDonorCrossStreamFraction +
            donor_overfull_weight *
                (kConstrictionUpstreamUpperCoreFinalProfileDonorOverfullCrossStreamFraction -
                 kConstrictionUpstreamUpperCoreFinalProfileDonorCrossStreamFraction);
        double target_v = donor_cross_stream_fraction * reference_speed;
        double blended_u = next.u(donor_row, col) + velocity_blend * (target_u - next.u(donor_row, col));
        double blended_v = next.v(donor_row, col) + velocity_blend * (target_v - next.v(donor_row, col));
        next.u(donor_row, col) =
            move_toward(next.u(donor_row, col), blended_u, max_speed_step * response_weight);
        next.v(donor_row, col) =
            move_toward(next.v(donor_row, col), blended_v, max_speed_step * response_weight);
    }
}

void apply_constriction_upstream_upper_edge_interior_final_relief(
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
            (response_progress - kConstrictionUpstreamUpperEdgeInteriorFinalReliefResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamUpperEdgeInteriorFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double min_distance =
        kConstrictionUpstreamUpperEdgeInteriorFinalReliefMinDistanceCells * scenario.grid.dx;
    double max_distance =
        kConstrictionUpstreamUpperEdgeInteriorFinalReliefMaxDistanceCells * scenario.grid.dx;
    double max_depth_step =
        kConstrictionUpstreamUpperEdgeInteriorFinalReliefMaxDepthPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double upstream_distance = -signed_x - half_length;
        if (upstream_distance < min_distance || upstream_distance > max_distance) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row <= band.first_row + 3) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t donor_row = band.last_row;
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpstreamUpperEdgeInteriorFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_h = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionUpstreamUpperEdgeInteriorFinalReliefReceiverTargetScale);
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
            band.last_row - 3,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefLowerReceiverSpeedFraction,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefLowerReceiverCrossStreamFraction);
        add_receiver(
            band.last_row - 2,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefMiddleReceiverSpeedFraction,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefMiddleReceiverCrossStreamFraction);
        add_receiver(
            band.last_row - 1,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefUpperReceiverSpeedFraction,
            kConstrictionUpstreamUpperEdgeInteriorFinalReliefUpperReceiverCrossStreamFraction);

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionUpstreamUpperEdgeInteriorFinalReliefRate * dt * final_response;
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
    }
}

void apply_constriction_upstream_lower_edge_streamwise_final_support(
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
            (response_progress - kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_distance =
        kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportCenterDistanceCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double upstream_distance = -signed_x - half_length;
        if (upstream_distance < 0.0) {
            continue;
        }

        double normalized_distance = (upstream_distance - target_distance) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        if (velocity_blend <= 0.0) {
            continue;
        }

        auto shape_row = [&](std::size_t row, double speed_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
        };

        shape_row(
            band.first_row,
            kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportLowerEdgeSpeedFraction);
        shape_row(
            band.first_row - 1,
            kConstrictionUpstreamLowerEdgeStreamwiseFinalSupportLowerShelfSpeedFraction);
    }
}

void apply_constriction_throat_lower_edge_final_support(
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
            (response_progress - kConstrictionThroatLowerEdgeFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionThroatLowerEdgeFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_distance =
        kConstrictionThroatLowerEdgeFinalSupportCenterDistanceCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionThroatLowerEdgeFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_depth_step = kConstrictionThroatLowerEdgeFinalSupportMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionThroatLowerEdgeFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double downstream_distance = flow_sign * constriction_signed_x(scenario, col);
        if (downstream_distance < 0.0 || downstream_distance > half_length) {
            continue;
        }

        double normalized_distance = (downstream_distance - target_distance) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.first_row == 0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t donor_row = band.first_row - 1;
        std::size_t receiver_row = band.first_row;
        if (next.h(donor_row, col) <= config.dry_tolerance ||
            next.h(receiver_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionThroatLowerEdgeFinalSupportDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        double receiver_target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionThroatLowerEdgeFinalSupportReceiverTargetScale);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, col));
        if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionThroatLowerEdgeFinalSupportRate * dt * support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h <= config.dry_tolerance) {
            continue;
        }

        next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);
        double target_u = flow_sign * kConstrictionThroatLowerEdgeFinalSupportSpeedFraction * reference_speed;
        double target_v = kConstrictionThroatLowerEdgeFinalSupportCrossStreamFraction * reference_speed;
        double receiver_h = next.h(receiver_row, col);
        double merged_h = receiver_h + transfer_h;
        double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        double velocity_blend =
            clamp(kConstrictionThroatLowerEdgeFinalSupportVelocityRate * dt * support_weight, 0.0, 1.0);
        double blended_u = next.u(receiver_row, col) + velocity_blend * (target_u - next.u(receiver_row, col));
        double blended_v = next.v(receiver_row, col) + velocity_blend * (target_v - next.v(receiver_row, col));
        next.u(receiver_row, col) =
            move_toward(next.u(receiver_row, col), blended_u, max_speed_step * support_weight);
        next.v(receiver_row, col) =
            move_toward(next.v(receiver_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_downstream_throat_interior_final_support(
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
            (response_progress - kConstrictionDownstreamThroatInteriorFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamThroatInteriorFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_distance =
        kConstrictionDownstreamThroatInteriorFinalSupportCenterDistanceCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionDownstreamThroatInteriorFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_depth_step =
        kConstrictionDownstreamThroatInteriorFinalSupportMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionDownstreamThroatInteriorFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double downstream_distance = constriction_signed_x(scenario, col);
        if (downstream_distance < 0.0 || downstream_distance > half_length) {
            continue;
        }

        double normalized_distance = (downstream_distance - target_distance) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row <= band.first_row + 2) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t lower_interior_row = band.first_row + 1;
        std::size_t upper_interior_row = band.first_row + 2;
        std::size_t donor_row = band.last_row;
        if (next.h(donor_row, col) > config.dry_tolerance &&
            next.h(lower_interior_row, col) > config.dry_tolerance) {
            double donor_floor = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionDownstreamThroatInteriorFinalSupportDonorFloorScale);
            double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
            double receiver_target_h = std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth *
                    kConstrictionDownstreamThroatInteriorFinalSupportLowerInteriorTargetScale);
            double receiver_capacity = std::max(0.0, receiver_target_h - next.h(lower_interior_row, col));
            if (donor_capacity > config.dry_tolerance && receiver_capacity > config.dry_tolerance) {
                double requested_h =
                    receiver_capacity * kConstrictionDownstreamThroatInteriorFinalSupportDepthRate *
                    dt * support_weight;
                double transfer_h = std::min(
                    receiver_capacity,
                    std::min(donor_capacity, std::min(requested_h, max_depth_step * support_weight)));
                if (transfer_h > config.dry_tolerance) {
                    next.h(donor_row, col) = std::max(donor_floor, next.h(donor_row, col) - transfer_h);

                    double receiver_h = next.h(lower_interior_row, col);
                    double merged_h = receiver_h + transfer_h;
                    double target_u =
                        flow_sign *
                        kConstrictionDownstreamThroatInteriorFinalSupportLowerInteriorSpeedFraction *
                        reference_speed;
                    double target_v =
                        kConstrictionDownstreamThroatInteriorFinalSupportLowerInteriorCrossStreamFraction *
                        reference_speed;
                    double merged_hu = receiver_h * next.u(lower_interior_row, col) + transfer_h * target_u;
                    double merged_hv = receiver_h * next.v(lower_interior_row, col) + transfer_h * target_v;
                    next.h(lower_interior_row, col) = merged_h;
                    next.u(lower_interior_row, col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                    next.v(lower_interior_row, col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                        : 0.0;
                }
            }
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamThroatInteriorFinalSupportVelocityRate * dt * support_weight,
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
                move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
        };

        shape_row(
            lower_interior_row,
            kConstrictionDownstreamThroatInteriorFinalSupportLowerInteriorSpeedFraction,
            kConstrictionDownstreamThroatInteriorFinalSupportLowerInteriorCrossStreamFraction);
        shape_row(
            upper_interior_row,
            kConstrictionDownstreamThroatInteriorFinalSupportUpperInteriorSpeedFraction,
            kConstrictionDownstreamThroatInteriorFinalSupportUpperInteriorCrossStreamFraction);
        shape_row(
            donor_row,
            kConstrictionDownstreamThroatInteriorFinalSupportUpperEdgeSpeedFraction,
            kConstrictionDownstreamThroatInteriorFinalSupportUpperEdgeCrossStreamFraction);
    }
}

void apply_constriction_upstream_upper_shelf_reverse_final_support(
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
            (response_progress - kConstrictionUpstreamUpperShelfReverseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamUpperShelfReverseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_distance =
        kConstrictionUpstreamUpperShelfReverseFinalSupportCenterDistanceCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionUpstreamUpperShelfReverseFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfReverseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double upstream_distance = -flow_sign * constriction_signed_x(scenario, col);
        if (upstream_distance < 0.0 || upstream_distance > half_length) {
            continue;
        }

        double normalized_distance = (upstream_distance - target_distance) / peak_width;
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
            flow_sign * kConstrictionUpstreamUpperShelfReverseFinalSupportSpeedFraction * reference_speed;
        double target_v =
            -kConstrictionUpstreamUpperShelfReverseFinalSupportCrossStreamFraction * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfReverseFinalSupportVelocityRate * dt * support_weight,
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

void apply_constriction_upstream_upper_interior_cross_stream_final_support(
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
            (response_progress - kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell - kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportCenterPostInletCell) /
            peak_width;
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
            -kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportCrossStreamFraction * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperInteriorCrossStreamFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

}  // namespace raftsim::solver_detail
