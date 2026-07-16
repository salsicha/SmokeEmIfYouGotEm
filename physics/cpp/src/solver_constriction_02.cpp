#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_flux_mass_froude_timing_reconstruction(
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
    double max_step_depth = kConstrictionFluxMassTimingMaxDepthPerSecond * dt;
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

        if (signed_x > half_length) {
            double target_h = column_mean_depth * kConstrictionFluxMassTimingRecoveryDepthScale;
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionFluxMassTimingRate * dt;
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
        double receiver_scale = signed_x < 0.0 ? kConstrictionFluxMassTimingUpstreamReceiverDepthScale
                                               : kConstrictionFluxMassTimingDownstreamReceiverDepthScale;
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
    if (transfer_depth > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
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
            double target_u = constriction_response_target_u(
                next.u(receiver.row, receiver.col),
                scenario.initial.u(receiver.row, receiver.col),
                flow_sign);
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

    if (reference_speed <= 0.0) {
        return;
    }

    double max_step_speed = kConstrictionFluxMassTimingMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionFluxMassTimingVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double base_target_u = constriction_local_fringe_target_u(scenario, band, row, reference_speed);
            bool upper_bank = constriction_lateral_sign(band, row) > 0.0;
            double target_u = upper_bank
                                  ? flow_sign * kConstrictionFluxMassTimingFringeSpeedFraction * reference_speed
                                  : base_target_u;
            double target_v = upper_bank
                                  ? -kConstrictionFluxMassTimingFringeCrossStreamFraction * reference_speed
                                  : 0.02 * reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_lateral_slope_shape_reconstruction(
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
    if (reference_speed <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionLateralSlopeShapeMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionLateralSlopeShapeVelocityRate * dt, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (scenario.initial.wet(row, col) || next.h(row, col) <= kConstrictionLateralSlopeShapeDryBankDepthCap) {
                continue;
            }
            std::size_t receiver_count = 0;
            for (std::size_t receiver_row = band.first_row; receiver_row <= band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                ++receiver_count;
            }
            if (receiver_count == 0) {
                continue;
            }
            double excess_h = next.h(row, col) - kConstrictionLateralSlopeShapeDryBankDepthCap;
            double added_h = excess_h / static_cast<double>(receiver_count);
            next.h(row, col) = kConstrictionLateralSlopeShapeDryBankDepthCap;
            for (std::size_t receiver_row = band.first_row; receiver_row <= band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                next.h(receiver_row, col) += added_h;
            }
        }
    }

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

        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            bool dry_bank_support = !scenario.initial.wet(row, col);
            if (!dry_bank_support && edge_norm < kConstrictionLateralSlopeShapeBankInfluenceFloor) {
                continue;
            }

            double bank_weight = dry_bank_support ? 1.0 : edge_norm;
            double target_u = next.u(row, col);
            double target_v = next.v(row, col);
            if (upstream) {
                double approach_strength = signed_x < -2.0 * half_length ? 1.0 : (signed_x < -half_length ? 0.55 : 0.18);
                double speed_fraction = lateral_sign < 0.0
                                            ? kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction
                                            : kConstrictionLateralSlopeShapeUpstreamUpperSpeedFraction * approach_strength;
                target_u = flow_sign * speed_fraction * reference_speed;
                double cross_fraction = dry_bank_support && lateral_sign < 0.0
                                            ? 0.02
                                            : kConstrictionLateralSlopeShapeUpstreamCrossStreamFraction * approach_strength * bank_weight;
                target_v = -lateral_sign * cross_fraction * reference_speed;
            } else if (downstream_constriction) {
                target_u = flow_sign * kConstrictionLateralSlopeShapeDownstreamBankSpeedFraction * reference_speed;
                target_v = lateral_sign * kConstrictionLateralSlopeShapeDownstreamCrossStreamFraction * bank_weight * reference_speed;
            } else {
                target_u = flow_sign * kConstrictionLateralSlopeShapeRecoveryBankSpeedFraction * reference_speed;
                target_v = lateral_sign * kConstrictionLateralSlopeShapeRecoveryCrossStreamFraction * bank_weight * reference_speed;
            }

            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_center_throat_circulation_reconstruction(
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
    if (reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionCenterThroatCirculationMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionCenterThroatCirculationVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!is_center_throat_column(scenario, band, throat_width_cells, col)) {
            continue;
        }

        std::size_t target_first = band.first_row > 0 ? band.first_row - 1 : band.first_row;
        std::size_t target_last = std::min(scenario.grid.ny - 1, target_first + band.count - 1);
        double center_row = 0.5 * (static_cast<double>(target_first) + static_cast<double>(target_last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(std::max<std::size_t>(1, target_last - target_first)));
        for (std::size_t row = target_first; row <= target_last; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double target_u = flow_sign * kConstrictionCenterThroatCirculationDownstreamSpeedFraction * reference_speed;
            double target_v =
                kConstrictionCenterThroatCirculationCrossStreamFraction * (1.0 + edge_norm * (kConstrictionCenterThroatCirculationEdgeBoost - 1.0)) *
                reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_localized_circulation_reconstruction(
    const Scenario& scenario,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double max_step_speed = kConstrictionLocalizedCirculationMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionLocalizedCirculationVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool upstream_approach = kConstrictionLocalizedCirculationUpstreamCrossStreamFraction > 0.0 && signed_x < -half_length;
        bool center_throat = is_center_throat_column(scenario, band, throat_width_cells, col);
        bool near_recovery = signed_x > half_length && signed_x <= half_length + 3.0 * scenario.grid.dx;
        if (!upstream_approach && !center_throat && !near_recovery) {
            continue;
        }

        std::size_t first_row =
            upstream_approach || near_recovery ? band.first_row : (band.first_row > 0 ? band.first_row - 1 : band.first_row);
        std::size_t last_row = upstream_approach || near_recovery ? band.last_row
                                                                  : std::min(scenario.grid.ny - 1, first_row + band.count - 1);
        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = first_row; row <= last_row; ++row) {
            if (next.h(row, col) <= kConstrictionLocalizedCirculationMinDepth) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double weight = kConstrictionLocalizedCirculationInteriorWeightFloor +
                            (1.0 - kConstrictionLocalizedCirculationInteriorWeightFloor) * edge_norm;
            double target_v = next.v(row, col);
            if (upstream_approach) {
                double approach_weight = signed_x <= -2.0 * half_length ? 1.0 : 0.6;
                target_v = -lateral_sign * kConstrictionLocalizedCirculationUpstreamCrossStreamFraction *
                           approach_weight * weight * reference_speed;
            } else if (center_throat) {
                target_v = kConstrictionLocalizedCirculationThroatCrossStreamFraction * weight * reference_speed;
            } else {
                target_v = lateral_sign * kConstrictionLocalizedCirculationRecoveryCrossStreamFraction *
                           weight * reference_speed;
            }

            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed * weight);
        }
    }
}

void apply_constriction_recovery_centerline_timing_reconstruction(
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
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionRecoveryCenterlineTimingMaxDepthPerSecond * dt * late_response;
    double max_speed_step = kConstrictionRecoveryCenterlineTimingMaxSpeedPerSecond * dt * late_response;
    double blend = clamp(kConstrictionRecoveryCenterlineTimingRate * dt * late_response, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool near_recovery = signed_x > half_length && signed_x <= half_length + 3.0 * scenario.grid.dx;
        if (!near_recovery) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        double receiver_target_h = column_mean_depth * kConstrictionRecoveryCenterlineTimingLateDepthScale;
        double donor_floor_h = column_mean_depth * kConstrictionRecoveryCenterlineTimingDonorFloorScale;
        std::vector<ConstrictionDepthTransferCell> donors;
        std::vector<ConstrictionDepthTransferCell> receivers;
        double donor_capacity = 0.0;
        double receiver_capacity = 0.0;
        if (column_mean_depth > config.dry_tolerance && band.last_row > band.first_row) {
            double donor_h = next.h(band.last_row, col);
            if (donor_h > donor_floor_h) {
                double requested_h =
                    (donor_h - donor_floor_h) * kConstrictionRecoveryCenterlineTimingDepthRate * dt * late_response;
                double capacity =
                    std::min(donor_h - donor_floor_h, std::min(requested_h, max_depth_step));
                if (capacity > config.dry_tolerance) {
                    donors.push_back(ConstrictionDepthTransferCell{band.last_row, col, capacity});
                    donor_capacity += capacity;
                }
            }
            for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
                double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
                if (edge_norm > kConstrictionRecoveryCenterlineTimingDepthInteriorEdgeNorm ||
                    next.h(row, col) >= receiver_target_h) {
                    continue;
                }
                double capacity = receiver_target_h - next.h(row, col);
                if (capacity > config.dry_tolerance) {
                    receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                    receiver_capacity += capacity;
                }
            }
        }
        double transfer_h = std::min(donor_capacity, receiver_capacity);
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
            for (const ConstrictionDepthTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
                double receiver_h = next.h(receiver.row, receiver.col);
                double edge_norm =
                    std::min(1.0, std::abs(static_cast<double>(receiver.row) - center) / half_span);
                double interior_weight =
                    1.0 - edge_norm / std::max(kConstrictionRecoveryCenterlineTimingInteriorEdgeNorm, 1.0e-9);
                double target_u =
                    flow_sign * kConstrictionRecoveryCenterlineTimingLateSpeedFraction * reference_speed;
                double target_v =
                    kConstrictionRecoveryCenterlineTimingLateCrossStreamFraction * reference_speed * interior_weight;
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
            if (edge_norm > kConstrictionRecoveryCenterlineTimingInteriorEdgeNorm) {
                continue;
            }
            double interior_weight =
                1.0 - edge_norm / std::max(kConstrictionRecoveryCenterlineTimingInteriorEdgeNorm, 1.0e-9);
            double target_u =
                flow_sign * kConstrictionRecoveryCenterlineTimingLateSpeedFraction * reference_speed;
            double target_v =
                kConstrictionRecoveryCenterlineTimingLateCrossStreamFraction * reference_speed * interior_weight;
            double blended_u = next.u(row, col) + blend * interior_weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * interior_weight * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * interior_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * interior_weight);
        }
    }
}

void apply_constriction_downstream_return_current_balance(
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
    double late_response = clamp((response_progress - 0.85) / 0.15, 0.0, 1.0);
    if (late_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionDownstreamReturnCurrentMaxSpeedPerSecond * dt * late_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.last_row == band.first_row || band.count <= throat_width_cells) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool downstream_constriction = signed_x >= 0.0 && signed_x <= half_length;
        if (!downstream_constriction) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));

        double downstream_weight = downstream_constriction
                                       ? clamp(signed_x / std::max(half_length, scenario.grid.dx), 0.0, 1.0)
                                       : 1.0;
        downstream_weight *= late_response;
        if (downstream_weight <= 0.0) {
            continue;
        }

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (edge_norm < kConstrictionDownstreamReturnCurrentEdgeNormFloor) {
                continue;
            }

            bool upper_side = static_cast<double>(row) > center;
            if (downstream_constriction && !upper_side) {
                continue;
            }

            double edge_weight =
                (edge_norm - kConstrictionDownstreamReturnCurrentEdgeNormFloor) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamReturnCurrentEdgeNormFloor);
            double inner_fraction = kConstrictionDownstreamReturnCurrentDownstreamUpperInnerSpeedFraction;
            double edge_fraction = kConstrictionDownstreamReturnCurrentDownstreamUpperEdgeSpeedFraction;
            double target_fraction = inner_fraction + edge_weight * (edge_fraction - inner_fraction);
            double target_u = flow_sign * target_fraction * reference_speed;
            double blend =
                clamp(kConstrictionDownstreamReturnCurrentVelocityRate * dt * downstream_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * downstream_weight);
        }
    }
}

void apply_constriction_downstream_upper_edge_final_shear(
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
            (response_progress - kConstrictionDownstreamUpperEdgeFinalShearResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionDownstreamUpperEdgeFinalShearResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionDownstreamUpperEdgeFinalShearMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x < 0.0 || signed_x > half_length) {
            continue;
        }

        double downstream_weight = clamp(signed_x / std::max(half_length, scenario.grid.dx), 0.0, 1.0);
        double response_weight = downstream_weight * final_response;
        if (response_weight <= 0.0 || next.h(band.last_row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign * kConstrictionDownstreamUpperEdgeFinalShearSpeedFraction * reference_speed;
        double blend =
            clamp(kConstrictionDownstreamUpperEdgeFinalShearVelocityRate * dt * response_weight, 0.0, 1.0);
        double blended_u = next.u(band.last_row, col) + blend * (target_u - next.u(band.last_row, col));
        next.u(band.last_row, col) =
            move_toward(next.u(band.last_row, col), blended_u, max_speed_step * response_weight);
    }
}

double constriction_recovery_progress(const Scenario& scenario, double half_length, std::size_t col) {
    double signed_x = constriction_signed_x(scenario, col);
    double farthest_x = 0.0;
    if (scenario.grid.nx > 0) {
        farthest_x = std::max(
            std::abs(constriction_signed_x(scenario, 0)),
            std::abs(constriction_signed_x(scenario, scenario.grid.nx - 1)));
    }
    double recovery_length = std::max(scenario.grid.dx, farthest_x - half_length);
    return clamp((signed_x - half_length) / recovery_length, 0.0, 1.0);
}

double constriction_recovery_edge_speed_fraction(double recovery_progress) {
    double eased_progress = std::pow(clamp(recovery_progress, 0.0, 1.0), 1.6);
    return kConstrictionRecoveryEdgeBalanceNearEdgeSpeedFraction +
           eased_progress *
               (kConstrictionRecoveryEdgeBalanceFarEdgeSpeedFraction -
                kConstrictionRecoveryEdgeBalanceNearEdgeSpeedFraction);
}

double constriction_recovery_interior_speed_fraction(double recovery_progress) {
    return kConstrictionRecoveryEdgeBalanceNearInteriorSpeedFraction +
           clamp(recovery_progress, 0.0, 1.0) *
               (kConstrictionRecoveryEdgeBalanceFarInteriorSpeedFraction -
                kConstrictionRecoveryEdgeBalanceNearInteriorSpeedFraction);
}

void apply_constriction_recovery_edge_balance(
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
    double late_response = clamp((response_progress - 0.85) / 0.15, 0.0, 1.0);
    if (late_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionRecoveryEdgeBalanceMaxDepthPerSecond * dt * late_response;
    double max_speed_step = kConstrictionRecoveryEdgeBalanceMaxSpeedPerSecond * dt * late_response;
    double depth_blend = clamp(kConstrictionRecoveryEdgeBalanceDepthRate * dt * late_response, 0.0, 1.0);
    double velocity_blend = clamp(kConstrictionRecoveryEdgeBalanceVelocityRate * dt * late_response, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.last_row == band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= half_length) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double recovery_progress = constriction_recovery_progress(scenario, half_length, col);
        double edge_speed_fraction = constriction_recovery_edge_speed_fraction(recovery_progress);
        double interior_speed_fraction = constriction_recovery_interior_speed_fraction(recovery_progress);
        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));

        std::vector<ConstrictionDepthTransferCell> donors;
        std::vector<ConstrictionProfileTransferCell> receivers;
        double donor_capacity = 0.0;
        double receiver_capacity = 0.0;

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (lateral_sign > 0.0 && edge_norm >= kConstrictionRecoveryEdgeBalanceInteriorEdgeNorm) {
                double target_scale = edge_norm > 0.85
                                          ? kConstrictionRecoveryEdgeBalanceUpperEdgeTargetDepthScale
                                          : kConstrictionRecoveryEdgeBalanceUpperInnerTargetDepthScale;
                double target_h = std::max(config.dry_tolerance, column_mean_depth * target_scale);
                if (current_h > target_h) {
                    double requested_h = (current_h - target_h) * depth_blend;
                    double capacity = std::min(current_h - target_h, std::min(requested_h, max_depth_step));
                    if (capacity > config.dry_tolerance) {
                        donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                        donor_capacity += capacity;
                    }
                }
            }

            double target_h = 0.0;
            if (row + 1 == band.first_row) {
                target_h = column_mean_depth * kConstrictionRecoveryEdgeBalanceLowerShelfTargetDepthScale;
            } else if (row == band.first_row) {
                target_h = column_mean_depth * kConstrictionRecoveryEdgeBalanceLowerEdgeTargetDepthScale;
            } else if (row > band.first_row && static_cast<double>(row) <= center) {
                target_h = column_mean_depth * kConstrictionRecoveryEdgeBalanceLowerInnerTargetDepthScale;
            }
            if (target_h <= 0.0 || current_h >= target_h) {
                continue;
            }

            double target_u_fraction = row == band.first_row || row + 1 == band.first_row
                                           ? edge_speed_fraction
                                           : interior_speed_fraction;
            double target_v = kConstrictionRecoveryEdgeBalanceLowerCrossStreamFraction * reference_speed;
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                target_h - current_h,
                flow_sign * target_u_fraction * reference_speed,
                target_v});
            receiver_capacity += target_h - current_h;
        }

        double transfer_h = std::min(donor_capacity, receiver_capacity);
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
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            double speed_fraction = edge_norm >= kConstrictionRecoveryEdgeBalanceInteriorEdgeNorm
                                        ? edge_speed_fraction
                                        : interior_speed_fraction;
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = lateral_sign < 0.0
                                  ? kConstrictionRecoveryEdgeBalanceLowerCrossStreamFraction * reference_speed
                                  : -kConstrictionRecoveryEdgeBalanceUpperCrossStreamFraction * reference_speed;
            if (edge_norm < kConstrictionRecoveryEdgeBalanceInteriorEdgeNorm) {
                target_v = kConstrictionRecoveryEdgeBalanceInteriorCrossStreamFraction *
                           (lateral_sign < 0.0 ? 1.0 : -1.0) * reference_speed;
            }
            double weight = kConstrictionRecoveryEdgeBalanceInteriorEdgeNorm +
                            (1.0 - kConstrictionRecoveryEdgeBalanceInteriorEdgeNorm) * edge_norm;
            double blended_u = next.u(row, col) + velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * weight);
        }
    }
}

double constriction_recovery_final_lower_edge_shear_speed_fraction(double recovery_progress) {
    double progress = clamp(recovery_progress, 0.0, 1.0);
    return kConstrictionRecoveryFinalLowerEdgeShearNearSpeedFraction +
           progress *
               (kConstrictionRecoveryFinalLowerEdgeShearFarSpeedFraction -
                kConstrictionRecoveryFinalLowerEdgeShearNearSpeedFraction);
}

void apply_constriction_recovery_final_lower_edge_shear_balance(
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
    double response_width = std::max(1.0e-6, 1.0 - kConstrictionRecoveryFinalLowerEdgeShearResponseStart);
    double final_response =
        clamp((response_progress - kConstrictionRecoveryFinalLowerEdgeShearResponseStart) / response_width, 0.0, 1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionRecoveryFinalLowerEdgeShearMaxSpeedPerSecond * dt * final_response;
    double velocity_blend =
        clamp(kConstrictionRecoveryFinalLowerEdgeShearVelocityRate * dt * final_response, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.last_row == band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= half_length) {
            continue;
        }

        std::size_t row = band.first_row;
        if (next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double recovery_progress = constriction_recovery_progress(scenario, half_length, col);
        double target_fraction = constriction_recovery_final_lower_edge_shear_speed_fraction(recovery_progress);
        double target_u = flow_sign * target_fraction * reference_speed;
        double recovery_weight = 1.0 - 0.25 * clamp(recovery_progress, 0.0, 1.0);
        double blended_u = next.u(row, col) + velocity_blend * recovery_weight * (target_u - next.u(row, col));
        next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * recovery_weight);
    }
}

void apply_constriction_recovery_split_balance(
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
    double response_width = std::max(1.0e-6, 1.0 - kConstrictionRecoverySplitBalanceResponseStart);
    double final_response =
        clamp((response_progress - kConstrictionRecoverySplitBalanceResponseStart) / response_width, 0.0, 1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionRecoverySplitBalanceMaxDepthPerSecond * dt * final_response;
    double max_edge_speed_step = kConstrictionRecoverySplitBalanceEdgeMaxSpeedPerSecond * dt * final_response;
    double edge_velocity_blend =
        clamp(kConstrictionRecoverySplitBalanceEdgeVelocityRate * dt * final_response, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.last_row == band.first_row) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= half_length) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        double donor_floor_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionRecoverySplitBalanceDonorFloorDepthScale);
        double receiver_target_h = column_mean_depth * kConstrictionRecoverySplitBalanceReceiverTargetDepthScale;

        std::vector<ConstrictionDepthTransferCell> donors;
        std::vector<ConstrictionProfileTransferCell> receivers;
        double donor_capacity = 0.0;
        double receiver_capacity = 0.0;

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (lateral_sign > 0.0 && edge_norm >= kConstrictionRecoverySplitBalanceDonorEdgeNormFloor &&
                current_h > donor_floor_h) {
                double requested_h =
                    (current_h - donor_floor_h) * kConstrictionRecoverySplitBalanceDepthRate * dt * final_response;
                double capacity = std::min(current_h - donor_floor_h, std::min(requested_h, max_depth_step));
                if (capacity > config.dry_tolerance) {
                    donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                    donor_capacity += capacity;
                }
                continue;
            }

            if (edge_norm <= kConstrictionRecoverySplitBalanceReceiverEdgeNormMax &&
                current_h < receiver_target_h) {
                double capacity = receiver_target_h - current_h;
                if (capacity > config.dry_tolerance) {
                    double center_weight = 1.0 - edge_norm / std::max(
                                                       kConstrictionRecoverySplitBalanceReceiverEdgeNormMax,
                                                       1.0e-9);
                    double target_u =
                        flow_sign * kConstrictionRecoverySplitBalanceCenterSpeedFraction * reference_speed;
                    double target_v = kConstrictionRecoverySplitBalanceCenterCrossStreamFraction *
                                      center_weight * reference_speed;
                    receivers.push_back(ConstrictionProfileTransferCell{row, col, capacity, target_u, target_v});
                    receiver_capacity += capacity;
                }
            }
        }

        double requested_h = receiver_capacity * kConstrictionRecoverySplitBalanceDepthRate * dt * final_response;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));
        if (transfer_h <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
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

        auto shape_edge_row = [&](std::size_t row, double target_u, double target_v, double row_weight) {
            if (row >= scenario.grid.ny || row_weight <= 0.0 || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double weight = row_weight * final_response;
            double blended_u = next.u(row, col) + edge_velocity_blend * weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + edge_velocity_blend * weight * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_edge_speed_step * weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_edge_speed_step * weight);
        };

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            if (edge_norm < kConstrictionRecoverySplitBalanceDonorEdgeNormFloor) {
                continue;
            }
            double edge_weight =
                (edge_norm - kConstrictionRecoverySplitBalanceDonorEdgeNormFloor) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoverySplitBalanceDonorEdgeNormFloor);
            double target_u = flow_sign * kConstrictionRecoverySplitBalanceEdgeSpeedFraction * reference_speed;
            double target_v = lateral_sign < 0.0
                                  ? kConstrictionRecoverySplitBalanceLowerEdgeCrossStreamFraction * reference_speed
                                  : -kConstrictionRecoverySplitBalanceUpperEdgeCrossStreamFraction * reference_speed;
            shape_edge_row(row, target_u, target_v, edge_weight);
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            shape_edge_row(
                band.last_row + 1,
                flow_sign * kConstrictionRecoverySplitBalanceUpperShelfSpeedFraction * reference_speed,
                kConstrictionRecoverySplitBalanceUpperShelfCrossStreamFraction * reference_speed,
                1.0);
        }
    }
}

void apply_constriction_recovery_interior_shear_balance(
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
    double response_width = std::max(1.0e-6, 1.0 - kConstrictionRecoveryInteriorShearResponseStart);
    double final_response =
        clamp((response_progress - kConstrictionRecoveryInteriorShearResponseStart) / response_width, 0.0, 1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionRecoveryInteriorShearMaxDepthPerSecond * dt * final_response;
    double max_speed_step = kConstrictionRecoveryInteriorShearMaxSpeedPerSecond * dt * final_response;
    double velocity_blend =
        clamp(kConstrictionRecoveryInteriorShearVelocityRate * dt * final_response, 0.0, 1.0);
    double recovery_window =
        static_cast<double>(kConstrictionRecoveryInteriorShearWindowCells) * scenario.grid.dx;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.last_row <= band.first_row + 1) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x <= half_length || signed_x > half_length + std::max(scenario.grid.dx, recovery_window)) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t lower_inner_row = band.first_row + 1;
        std::size_t upper_inner_row = band.last_row - 1;
        std::size_t upper_outer_row = band.last_row;
        double donor_floor_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionRecoveryInteriorShearLowerInnerDonorFloorScale);
        double receiver_target_h =
            std::max(kConstrictionLocalFringeTargetDepth,
                     column_mean_depth * kConstrictionRecoveryInteriorShearUpperInnerReceiverTargetScale);

        double donor_capacity = std::max(0.0, next.h(lower_inner_row, col) - donor_floor_h);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(upper_inner_row, col));
        double requested_h =
            receiver_capacity * kConstrictionRecoveryInteriorShearDepthRate * dt * final_response;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step)));

        if (transfer_h > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
            next.h(lower_inner_row, col) = std::max(0.0, next.h(lower_inner_row, col) - transfer_h);
            if (next.h(lower_inner_row, col) <= config.dry_tolerance) {
                next.h(lower_inner_row, col) = 0.0;
                next.u(lower_inner_row, col) = 0.0;
                next.v(lower_inner_row, col) = 0.0;
            }

            double receiver_h = next.h(upper_inner_row, col);
            double merged_h = receiver_h + transfer_h;
            double receiver_target_u =
                flow_sign * kConstrictionRecoveryInteriorShearUpperInnerSpeedFraction * reference_speed;
            double receiver_target_v =
                kConstrictionRecoveryInteriorShearUpperInnerCrossStreamFraction * reference_speed;
            double merged_hu = receiver_h * next.u(upper_inner_row, col) + transfer_h * receiver_target_u;
            double merged_hv = receiver_h * next.v(upper_inner_row, col) + transfer_h * receiver_target_v;
            next.h(upper_inner_row, col) = merged_h;
            next.u(upper_inner_row, col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(upper_inner_row, col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }

        auto shape_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
        };

        shape_row(
            lower_inner_row,
            kConstrictionRecoveryInteriorShearLowerInnerSpeedFraction,
            kConstrictionRecoveryInteriorShearLowerInnerCrossStreamFraction);
        shape_row(
            upper_inner_row,
            kConstrictionRecoveryInteriorShearUpperInnerSpeedFraction,
            kConstrictionRecoveryInteriorShearUpperInnerCrossStreamFraction);
        shape_row(
            upper_outer_row,
            kConstrictionRecoveryInteriorShearUpperOuterSpeedFraction,
            kConstrictionRecoveryInteriorShearUpperOuterCrossStreamFraction);
    }
}

void apply_constriction_recovery_broad_interior_final_profile(
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
            (response_progress - kConstrictionRecoveryBroadInteriorFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryBroadInteriorFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double start_offset = kConstrictionRecoveryBroadInteriorFinalProfileStartCells * scenario.grid.dx;
    double end_offset = kConstrictionRecoveryBroadInteriorFinalProfileEndCells * scenario.grid.dx;
    double window_width = std::max(scenario.grid.dx, end_offset - start_offset);
    double max_speed_step =
        kConstrictionRecoveryBroadInteriorFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double recovery_offset = signed_x - half_length;
        if (recovery_offset < start_offset || recovery_offset > end_offset) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.last_row <= band.first_row + 2) {
            continue;
        }

        double recovery_weight = clamp((recovery_offset - start_offset) / window_width, 0.0, 1.0);
        double response_weight = final_response * std::sqrt(recovery_weight);
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(kConstrictionRecoveryBroadInteriorFinalProfileVelocityRate * dt * response_weight, 0.0, 1.0);
        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double signed_row_offset = static_cast<double>(row) - center;
            double edge_norm = std::min(1.0, std::abs(signed_row_offset) / half_span);
            double speed_fraction = kConstrictionRecoveryBroadInteriorFinalProfileCenterNearSpeedFraction +
                                    recovery_weight *
                                        (kConstrictionRecoveryBroadInteriorFinalProfileCenterFarSpeedFraction -
                                         kConstrictionRecoveryBroadInteriorFinalProfileCenterNearSpeedFraction);
            double cross_stream_fraction =
                kConstrictionRecoveryBroadInteriorFinalProfileCenterCrossStreamFraction;
            double row_weight = 0.75;

            if (edge_norm > kConstrictionRecoveryBroadInteriorFinalProfileLowerInnerEdgeNormFloor &&
                signed_row_offset < 0.0) {
                speed_fraction =
                    row == band.first_row
                        ? kConstrictionRecoveryBroadInteriorFinalProfileLowerEdgeSpeedFraction
                        : kConstrictionRecoveryBroadInteriorFinalProfileLowerInnerNearSpeedFraction +
                              recovery_weight *
                                  (kConstrictionRecoveryBroadInteriorFinalProfileLowerInnerFarSpeedFraction -
                                   kConstrictionRecoveryBroadInteriorFinalProfileLowerInnerNearSpeedFraction);
                cross_stream_fraction = kConstrictionRecoveryBroadInteriorFinalProfileLowerCrossStreamFraction;
                row_weight = row == band.first_row ? 0.9 : 1.0;
            } else if (edge_norm > kConstrictionRecoveryBroadInteriorFinalProfileUpperInnerEdgeNormFloor &&
                       signed_row_offset > 0.0) {
                speed_fraction = row == band.last_row
                                     ? kConstrictionRecoveryBroadInteriorFinalProfileUpperEdgeSpeedFraction
                                     : kConstrictionRecoveryBroadInteriorFinalProfileUpperInnerSpeedFraction;
                cross_stream_fraction = kConstrictionRecoveryBroadInteriorFinalProfileUpperCrossStreamFraction;
                row_weight = row == band.last_row ? 0.9 : 0.85;
            }

            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * row_weight * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + velocity_blend * row_weight * (target_v - next.v(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight * row_weight);
            next.v(row, col) =
                move_toward(next.v(row, col), blended_v, max_speed_step * response_weight * row_weight);
        }
    }
}

void apply_constriction_recovery_far_interior_streamwise_final_support(
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
            (response_progress - kConstrictionRecoveryFarInteriorStreamwiseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryFarInteriorStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double start_offset =
        kConstrictionRecoveryFarInteriorStreamwiseFinalSupportStartCells * scenario.grid.dx;
    double end_offset =
        kConstrictionRecoveryFarInteriorStreamwiseFinalSupportEndCells * scenario.grid.dx;
    double window_width = std::max(scenario.grid.dx, end_offset - start_offset);
    double max_speed_step =
        kConstrictionRecoveryFarInteriorStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double recovery_offset = signed_x - half_length;
        if (recovery_offset < start_offset || recovery_offset > end_offset) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.last_row <= band.first_row + 2) {
            continue;
        }

        double recovery_weight = std::sqrt(clamp((recovery_offset - start_offset) / window_width, 0.0, 1.0));
        double response_weight = final_response * recovery_weight;
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryFarInteriorStreamwiseFinalSupportVelocityRate * dt * response_weight,
                0.0,
                1.0);
        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));

        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double signed_row_offset = static_cast<double>(row) - center;
            double edge_norm = std::min(1.0, std::abs(signed_row_offset) / half_span);
            double speed_fraction = 0.0;
            if (edge_norm <= kConstrictionRecoveryFarInteriorStreamwiseFinalSupportCenterEdgeNormMax) {
                speed_fraction = kConstrictionRecoveryFarInteriorStreamwiseFinalSupportCenterSpeedFraction;
            } else if (
                edge_norm <= kConstrictionRecoveryFarInteriorStreamwiseFinalSupportInnerEdgeNormMax &&
                signed_row_offset < 0.0) {
                speed_fraction = kConstrictionRecoveryFarInteriorStreamwiseFinalSupportLowerInnerSpeedFraction;
            } else if (
                edge_norm <= kConstrictionRecoveryFarInteriorStreamwiseFinalSupportInnerEdgeNormMax &&
                signed_row_offset > 0.0) {
                speed_fraction = kConstrictionRecoveryFarInteriorStreamwiseFinalSupportUpperInnerSpeedFraction;
            } else {
                continue;
            }

            double target_u = flow_sign * speed_fraction * reference_speed;
            if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
                continue;
            }
            double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            next.u(row, col) =
                move_toward(next.u(row, col), blended_u, max_speed_step * response_weight);
        }
    }
}

void apply_constriction_recovery_lower_shelf_final_profile(
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
            (response_progress - kConstrictionRecoveryLowerShelfFinalProfileResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryLowerShelfFinalProfileResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    auto interpolate = [](double x, double x0, double x1, double y0, double y1) {
        double weight = clamp((x - x0) / std::max(1.0e-9, x1 - x0), 0.0, 1.0);
        return y0 + weight * (y1 - y0);
    };

    auto profile_fraction = [&](double offset_cells, double near_value, double mid_value, double far_value) {
        if (offset_cells <= kConstrictionRecoveryLowerShelfFinalProfileBrakeOffsetCells) {
            return interpolate(
                offset_cells,
                kConstrictionRecoveryLowerShelfFinalProfileStartOffsetCells,
                kConstrictionRecoveryLowerShelfFinalProfileBrakeOffsetCells,
                near_value,
                mid_value);
        }
        if (offset_cells <= kConstrictionRecoveryLowerShelfFinalProfileStallOffsetCells) {
            return mid_value;
        }
        return interpolate(
            offset_cells,
            kConstrictionRecoveryLowerShelfFinalProfileStallOffsetCells,
            kConstrictionRecoveryLowerShelfFinalProfileEndOffsetCells,
            mid_value,
            far_value);
    };

    auto cross_stream_fraction = [&](double offset_cells) {
        if (offset_cells <= kConstrictionRecoveryLowerShelfFinalProfileBrakeOffsetCells) {
            return interpolate(
                offset_cells,
                kConstrictionRecoveryLowerShelfFinalProfileStartOffsetCells,
                kConstrictionRecoveryLowerShelfFinalProfileBrakeOffsetCells,
                kConstrictionRecoveryLowerShelfFinalProfileNearCrossStreamFraction,
                kConstrictionRecoveryLowerShelfFinalProfileShearCrossStreamFraction);
        }
        if (offset_cells <= kConstrictionRecoveryLowerShelfFinalProfileStallOffsetCells) {
            return interpolate(
                offset_cells,
                kConstrictionRecoveryLowerShelfFinalProfileBrakeOffsetCells,
                kConstrictionRecoveryLowerShelfFinalProfileStallOffsetCells,
                kConstrictionRecoveryLowerShelfFinalProfileShearCrossStreamFraction,
                kConstrictionRecoveryLowerShelfFinalProfileStallCrossStreamFraction);
        }
        return interpolate(
            offset_cells,
            kConstrictionRecoveryLowerShelfFinalProfileStallOffsetCells,
            kConstrictionRecoveryLowerShelfFinalProfileEndOffsetCells,
            kConstrictionRecoveryLowerShelfFinalProfileStallCrossStreamFraction,
            kConstrictionRecoveryLowerShelfFinalProfileFarCrossStreamFraction);
    };

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerShelfFinalProfileMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        double recovery_offset = signed_x - half_length;
        double offset_cells = recovery_offset / std::max(1.0e-9, scenario.grid.dx);
        if (offset_cells < kConstrictionRecoveryLowerShelfFinalProfileStartOffsetCells ||
            offset_cells > kConstrictionRecoveryLowerShelfFinalProfileEndOffsetCells) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.first_row == 0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        if (next.h(lower_shelf_row, col) <= config.dry_tolerance) {
            continue;
        }

        double speed_fraction = profile_fraction(
            offset_cells,
            kConstrictionRecoveryLowerShelfFinalProfileNearSpeedFraction,
            kConstrictionRecoveryLowerShelfFinalProfileStallSpeedFraction,
            kConstrictionRecoveryLowerShelfFinalProfileFarSpeedFraction);
        double target_u = flow_sign * speed_fraction * reference_speed;
        double target_v = cross_stream_fraction(offset_cells) * reference_speed;
        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerShelfFinalProfileVelocityRate * dt * final_response,
                0.0,
                1.0);
        double blended_u = next.u(lower_shelf_row, col) + velocity_blend * (target_u - next.u(lower_shelf_row, col));
        double blended_v = next.v(lower_shelf_row, col) + velocity_blend * (target_v - next.v(lower_shelf_row, col));
        next.u(lower_shelf_row, col) =
            move_toward(next.u(lower_shelf_row, col), blended_u, max_speed_step);
        next.v(lower_shelf_row, col) =
            move_toward(next.v(lower_shelf_row, col), blended_v, max_speed_step);
    }
}

void apply_constriction_recovery_lower_interior_slowdown_final_support(
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
            (response_progress - kConstrictionRecoveryLowerInteriorSlowdownFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryLowerInteriorSlowdownFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_offset =
        kConstrictionRecoveryLowerInteriorSlowdownFinalSupportCenterOffsetCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionRecoveryLowerInteriorSlowdownFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorSlowdownFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double recovery_offset = constriction_signed_x(scenario, col) - half_length;
        if (recovery_offset < 0.0) {
            continue;
        }

        double normalized_offset = (recovery_offset - target_offset) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_offset * normalized_offset));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.first_row + 1 >= band.last_row) {
            continue;
        }

        std::size_t lower_interior_row = band.first_row + 1;
        if (next.h(lower_interior_row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerInteriorSlowdownFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign * kConstrictionRecoveryLowerInteriorSlowdownFinalSupportSpeedFraction * reference_speed;
        double target_v =
            kConstrictionRecoveryLowerInteriorSlowdownFinalSupportCrossStreamFraction * reference_speed;
        double blended_u =
            next.u(lower_interior_row, col) + velocity_blend * (target_u - next.u(lower_interior_row, col));
        double blended_v =
            next.v(lower_interior_row, col) + velocity_blend * (target_v - next.v(lower_interior_row, col));
        next.u(lower_interior_row, col) =
            move_toward(next.u(lower_interior_row, col), blended_u, max_speed_step * support_weight);
        next.v(lower_interior_row, col) =
            move_toward(next.v(lower_interior_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_streamwise_final_support(
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
            (response_progress - kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportResponseStart) /
                std::max(1.0e-9, 1.0 - kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_offset =
        kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportCenterOffsetCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportPeakWidthCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double recovery_offset = constriction_signed_x(scenario, col) - half_length;
        if (recovery_offset < 0.0) {
            continue;
        }

        double normalized_offset = (recovery_offset - target_offset) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_offset * normalized_offset));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.last_row <= band.first_row + 2) {
            continue;
        }

        std::size_t upper_interior_row = band.last_row - 2;
        if (next.h(upper_interior_row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportVelocityRate * dt * support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign * kConstrictionRecoveryUpperInteriorStreamwiseFinalSupportSpeedFraction * reference_speed;
        if ((target_u - next.u(upper_interior_row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double blended_u =
            next.u(upper_interior_row, col) + velocity_blend * (target_u - next.u(upper_interior_row, col));
        next.u(upper_interior_row, col) =
            move_toward(next.u(upper_interior_row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_interior_depth_final_relief(
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
            (response_progress - kConstrictionRecoveryUpperInteriorDepthFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryUpperInteriorDepthFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double target_offset =
        kConstrictionRecoveryUpperInteriorDepthFinalReliefCenterOffsetCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefPeakWidthCells * scenario.grid.dx);
    double max_depth_step =
        kConstrictionRecoveryUpperInteriorDepthFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionRecoveryUpperInteriorDepthFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double recovery_offset = constriction_signed_x(scenario, col) - half_length;
        if (recovery_offset < 0.0) {
            continue;
        }

        double normalized_offset = (recovery_offset - target_offset) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_offset * normalized_offset));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count < throat_width_cells + 4 || band.last_row <= band.first_row + 2) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance || next.h(band.last_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionRecoveryUpperInteriorDepthFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        double receiver_target_h =
            std::max(
                kConstrictionLocalFringeTargetDepth,
                column_mean_depth * kConstrictionRecoveryUpperInteriorDepthFinalReliefReceiverTargetScale);
        auto add_receiver = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double capacity = std::max(0.0, receiver_target_h - next.h(row, col));
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

        std::size_t primary_row = band.last_row - 2;
        std::size_t secondary_row = band.last_row - 1;
        add_receiver(
            primary_row,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefPrimarySpeedFraction,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefPrimaryCrossStreamFraction);
        add_receiver(
            secondary_row,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefSecondarySpeedFraction,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefSecondaryCrossStreamFraction);

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionRecoveryUpperInteriorDepthFinalReliefRate * dt * support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step * support_weight)));
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

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperInteriorDepthFinalReliefVelocityRate * dt * support_weight,
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
            primary_row,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefPrimarySpeedFraction,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefPrimaryCrossStreamFraction);
        shape_row(
            secondary_row,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefSecondarySpeedFraction,
            kConstrictionRecoveryUpperInteriorDepthFinalReliefSecondaryCrossStreamFraction);
    }
}

void apply_constriction_recovery_center_upper_interior_momentum_pocket_final_support(
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
             kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells ||
            band.first_row +
                    kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportRowOffsetFromWetBandStart >
                band.last_row) {
            continue;
        }

        std::size_t row =
            band.first_row +
            kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportRowOffsetFromWetBandStart;
        if (row >= scenario.grid.ny || next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryCenterUpperInteriorMomentumPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_center_interior_depth_pocket_final_support(
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
            (response_progress - kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportMaxDepthPerSecond * dt *
        final_response;
    double max_speed_step =
        kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportCenterPostInletCell) /
            std::max(1.0e-9, kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        std::size_t receiver_offset =
            static_cast<std::size_t>(kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportReceiverColumnOffsetCells);
        if ((flow_sign >= 0.0 && col < receiver_offset) ||
            (flow_sign < 0.0 && col + receiver_offset >= scenario.grid.nx)) {
            continue;
        }
        std::size_t receiver_col = flow_sign >= 0.0 ? col - receiver_offset : col + receiver_offset;

        ColumnWetBand donor_band = initial_wet_band_in_column(scenario, col);
        ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, receiver_col);
        if (!donor_band.found || !receiver_band.found ||
            donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells) {
            continue;
        }

        std::size_t donor_row = kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportTargetRowIndex;
        if (donor_row >= scenario.grid.ny || donor_row <= donor_band.first_row ||
            donor_row >= donor_band.last_row || next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_mean_depth = initial_column_mean_depth(scenario, donor_band, col);
        double receiver_mean_depth = initial_column_mean_depth(scenario, receiver_band, receiver_col);
        if (donor_mean_depth <= config.dry_tolerance || receiver_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            config.dry_tolerance,
            donor_mean_depth * kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(donor_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double target_scale, double speed_fraction, double cross_fraction) {
            if (row >= scenario.grid.ny || row < receiver_band.first_row || row > receiver_band.last_row ||
                next.h(row, receiver_col) <= config.dry_tolerance) {
                return;
            }
            double target_h = std::max(config.dry_tolerance, receiver_mean_depth * target_scale);
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

        if (donor_row >= 2) {
            add_receiver(
                donor_row - 2,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportLowerReceiverTargetScale,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportLowerReceiverSpeedFraction,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportLowerReceiverCrossStreamFraction);
        }
        if (donor_row >= 1) {
            add_receiver(
                donor_row - 1,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportMiddleReceiverTargetScale,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportMiddleReceiverSpeedFraction,
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportMiddleReceiverCrossStreamFraction);
        }
        add_receiver(
            donor_row,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportUpperReceiverTargetScale,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportUpperReceiverSpeedFraction,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportUpperReceiverCrossStreamFraction);
        add_receiver(
            donor_row + 1,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportUpperReceiverTargetScale,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportEdgeReceiverSpeedFraction,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportEdgeReceiverCrossStreamFraction);

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportDepthRate *
            dt * support_weight;
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
            if (added_h <= 0.0) {
                continue;
            }
            double receiver_h = next.h(receiver.row, receiver.col);
            double merged_h = receiver_h + added_h;
            double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
            double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
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

        double velocity_blend =
            clamp(
                kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        auto shape_cell = [&](std::size_t row, std::size_t target_col, double target_u, double target_v) {
            if (row >= scenario.grid.ny || next.h(row, target_col) <= config.dry_tolerance) {
                return;
            }
            double blended_u = next.u(row, target_col) + velocity_blend * (target_u - next.u(row, target_col));
            double blended_v = next.v(row, target_col) + velocity_blend * (target_v - next.v(row, target_col));
            next.u(row, target_col) =
                move_toward(next.u(row, target_col), blended_u, max_speed_step * support_weight);
            next.v(row, target_col) =
                move_toward(next.v(row, target_col), blended_v, max_speed_step * support_weight);
        };

        shape_cell(
            donor_row,
            col,
            flow_sign * kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportDonorSpeedFraction *
                reference_speed,
            kConstrictionRecoveryCenterInteriorDepthPocketFinalSupportDonorCrossStreamFraction *
                reference_speed);
        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            shape_cell(receiver.row, receiver.col, receiver.target_u, receiver.target_v);
        }
    }
}

void apply_constriction_lower_edge_flux_magnitude_balance(
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
    double max_speed_step = kConstrictionLowerEdgeFluxMagnitudeMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        if (!inside_relaxed_wet_band(scenario, band, throat_width_cells, col, lower_shelf_row) &&
            !inside_constriction_local_shallow_fringe(
                scenario, band, throat_width_cells, col, lower_shelf_row)) {
            continue;
        }

        auto shape_lower_flux_row = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * speed_fraction * reference_speed;
            double target_v = cross_stream_fraction * reference_speed;
            double blend = clamp(kConstrictionLowerEdgeFluxMagnitudeRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        shape_lower_flux_row(
            lower_shelf_row,
            kConstrictionLowerEdgeFluxMagnitudeShelfSpeedFraction,
            kConstrictionLowerEdgeFluxMagnitudeShelfCrossStreamFraction);
        shape_lower_flux_row(
            band.first_row,
            kConstrictionLowerEdgeFluxMagnitudeFirstWetSpeedFraction,
            kConstrictionLowerEdgeFluxMagnitudeFirstWetCrossStreamFraction);
    }
}

void apply_constriction_lower_edge_transition_source_depth_balance(
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
    double max_depth_step = kConstrictionLowerEdgeTransitionSourceDepthMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionLowerEdgeTransitionSourceDepthMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        double transition_weight = 4.0 * approach_weight * (1.0 - approach_weight);
        transition_weight = clamp(transition_weight, 0.0, 1.0);
        if (transition_weight <= 0.0) {
            continue;
        }

        std::size_t lower_shelf_row = band.first_row - 1;
        if (!inside_relaxed_wet_band(scenario, band, throat_width_cells, col, lower_shelf_row) &&
            !inside_constriction_local_shallow_fringe(
                scenario, band, throat_width_cells, col, lower_shelf_row)) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double lower_shelf_target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionLowerEdgeTransitionSourceDepthShelfDepthScale);
        double first_wet_target_h = std::max(
            column_mean_depth,
            column_mean_depth * kConstrictionLowerEdgeTransitionSourceDepthFirstWetDepthScale);

        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double target_h) {
            double capacity = std::max(0.0, target_h - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                return;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        };
        add_receiver(lower_shelf_row, lower_shelf_target_h);
        add_receiver(band.first_row, first_wet_target_h);

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionLowerEdgeTransitionSourceDepthUpperDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        double transfer_h = 0.0;
        if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionLowerEdgeTransitionSourceDepthRate * dt * transition_weight;
            transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * transition_weight)));
        }

        auto target_u_for_row = [&](std::size_t row) {
            double speed_fraction = row == lower_shelf_row
                                        ? kConstrictionLowerEdgeTransitionSourceDepthShelfSpeedFraction
                                        : kConstrictionLowerEdgeTransitionSourceDepthFirstWetSpeedFraction;
            return flow_sign * speed_fraction * reference_speed;
        };
        auto target_v_for_row = [&](std::size_t row) {
            double cross_stream_fraction = row == lower_shelf_row
                                               ? kConstrictionLowerEdgeTransitionSourceDepthShelfCrossStreamFraction
                                               : kConstrictionLowerEdgeTransitionSourceDepthFirstWetCrossStreamFraction;
            return cross_stream_fraction * reference_speed;
        };

        if (transfer_h > config.dry_tolerance) {
            next.h(band.last_row, col) = std::max(0.0, next.h(band.last_row, col) - transfer_h);
            if (next.h(band.last_row, col) <= config.dry_tolerance) {
                next.h(band.last_row, col) = 0.0;
                next.u(band.last_row, col) = 0.0;
                next.v(band.last_row, col) = 0.0;
            }

            for (const ConstrictionDepthTransferCell& receiver : receivers) {
                double added_h = transfer_h * receiver.capacity / receiver_capacity;
                if (added_h <= 0.0) {
                    continue;
                }
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + added_h;
                double merged_hu =
                    receiver_h * next.u(receiver.row, receiver.col) + added_h * target_u_for_row(receiver.row);
                double merged_hv =
                    receiver_h * next.v(receiver.row, receiver.col) + added_h * target_v_for_row(receiver.row);
                next.h(receiver.row, receiver.col) = merged_h;
                next.u(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        auto shape_row = [&](std::size_t row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double blend = clamp(
                kConstrictionLowerEdgeTransitionSourceDepthVelocityRate * dt * transition_weight,
                0.0,
                1.0);
            double target_u = target_u_for_row(row);
            double target_v = target_v_for_row(row);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * transition_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * transition_weight);
        };

        shape_row(lower_shelf_row);
        shape_row(band.first_row);

        if (next.h(band.last_row, col) > config.dry_tolerance) {
            double blend = clamp(
                kConstrictionLowerEdgeTransitionSourceDepthVelocityRate * dt * transition_weight,
                0.0,
                1.0);
            double target_u =
                flow_sign * kConstrictionLowerEdgeTransitionSourceDepthUpperEdgeSpeedFraction * reference_speed;
            double target_v =
                -kConstrictionLowerEdgeTransitionSourceDepthUpperEdgeCrossStreamFraction * reference_speed;
            double blended_u = next.u(band.last_row, col) + blend * (target_u - next.u(band.last_row, col));
            double blended_v = next.v(band.last_row, col) + blend * (target_v - next.v(band.last_row, col));
            next.u(band.last_row, col) =
                move_toward(next.u(band.last_row, col), blended_u, max_speed_step * transition_weight);
            next.v(band.last_row, col) =
                move_toward(next.v(band.last_row, col), blended_v, max_speed_step * transition_weight);
        }
    }
}

double constriction_lower_edge_contraction_face_weight(
    const Scenario& scenario,
    std::size_t throat_width_cells,
    std::size_t col
) {
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells) {
        return 0.0;
    }

    double flow_sign = constriction_flow_sign(scenario);
    auto wet_count_at = [&](std::size_t candidate_col) -> std::size_t {
        ColumnWetBand candidate = initial_wet_band_in_column(scenario, candidate_col);
        return candidate.found ? candidate.count : 0;
    };

    if (flow_sign >= 0.0) {
        if (col > 0 && band.count < wet_count_at(col - 1)) {
            return 1.0;
        }
        for (std::size_t distance = 1; distance <= kConstrictionLowerEdgeContractionFaceApproachWindowCells;
             ++distance) {
            std::size_t downstream_col = col + distance;
            if (downstream_col >= scenario.grid.nx) {
                break;
            }
            if (wet_count_at(downstream_col) < band.count) {
                double window = static_cast<double>(kConstrictionLowerEdgeContractionFaceApproachWindowCells + 1);
                return (window - static_cast<double>(distance)) / window;
            }
        }
        return 0.0;
    }

    if (col + 1 < scenario.grid.nx && band.count < wet_count_at(col + 1)) {
        return 1.0;
    }
    for (std::size_t distance = 1; distance <= kConstrictionLowerEdgeContractionFaceApproachWindowCells;
         ++distance) {
        if (col < distance) {
            break;
        }
        std::size_t downstream_col = col - distance;
        if (wet_count_at(downstream_col) < band.count) {
            double window = static_cast<double>(kConstrictionLowerEdgeContractionFaceApproachWindowCells + 1);
            return (window - static_cast<double>(distance)) / window;
        }
    }
    return 0.0;
}

bool constriction_lower_edge_contraction_entry_column(const Scenario& scenario, std::size_t col) {
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found) {
        return false;
    }

    double flow_sign = constriction_flow_sign(scenario);
    if (flow_sign >= 0.0) {
        if (col == 0) {
            return false;
        }
        ColumnWetBand upstream = initial_wet_band_in_column(scenario, col - 1);
        return upstream.found && band.count < upstream.count;
    }

    if (col + 1 >= scenario.grid.nx) {
        return false;
    }
    ColumnWetBand upstream = initial_wet_band_in_column(scenario, col + 1);
    return upstream.found && band.count < upstream.count;
}

double constriction_lower_edge_post_contraction_face_weight(const Scenario& scenario, std::size_t col) {
    double flow_sign = constriction_flow_sign(scenario);
    for (std::size_t distance = 1; distance <= kConstrictionLowerEdgeContractionFacePostEntryWindowCells;
         ++distance) {
        std::size_t entry_col = 0;
        if (flow_sign >= 0.0) {
            if (col < distance) {
                break;
            }
            entry_col = col - distance;
        } else {
            entry_col = col + distance;
            if (entry_col >= scenario.grid.nx) {
                break;
            }
        }
        if (!constriction_lower_edge_contraction_entry_column(scenario, entry_col)) {
            continue;
        }
        double window = static_cast<double>(kConstrictionLowerEdgeContractionFacePostEntryWindowCells + 1);
        return (window - static_cast<double>(distance)) / window;
    }
    return 0.0;
}

}  // namespace raftsim::solver_detail
