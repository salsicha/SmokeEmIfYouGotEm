#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_throat_upper_edge_cross_stream_final_support(
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
            (response_progress - kConstrictionThroatUpperEdgeCrossStreamFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionThroatUpperEdgeCrossStreamFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double target_center =
        -kConstrictionThroatUpperEdgeCrossStreamFinalSupportCenterOffsetCells * scenario.grid.dx;
    double window_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionThroatUpperEdgeCrossStreamFinalSupportWindowCells * scenario.grid.dx);
    double max_speed_step =
        kConstrictionThroatUpperEdgeCrossStreamFinalSupportMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= 0.0) {
            continue;
        }

        double offset = std::abs(signed_x - target_center);
        if (offset > window_width) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row <= band.first_row) {
            continue;
        }

        std::size_t upper_edge_row = band.last_row;
        if (next.h(upper_edge_row, col) <= config.dry_tolerance) {
            continue;
        }

        double window_weight = 1.0 - clamp(offset / std::max(window_width, 1.0e-9), 0.0, 1.0);
        double response_weight = final_response * window_weight;
        if (response_weight <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionThroatUpperEdgeCrossStreamFinalSupportVelocityRate * dt *
                    response_weight,
                0.0,
                1.0);
        double target_v =
            -kConstrictionThroatUpperEdgeCrossStreamFinalSupportCrossStreamFraction * reference_speed;
        double blended_v =
            next.v(upper_edge_row, col) + velocity_blend * (target_v - next.v(upper_edge_row, col));
        next.v(upper_edge_row, col) =
            move_toward(next.v(upper_edge_row, col), blended_v, max_speed_step * response_weight);
    }
}

void apply_constriction_throat_upper_edge_depth_final_relief(
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
            (response_progress - kConstrictionThroatUpperEdgeDepthFinalReliefResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionThroatUpperEdgeDepthFinalReliefResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double target_center =
        -kConstrictionThroatUpperEdgeDepthFinalReliefCenterOffsetCells * scenario.grid.dx;
    double peak_width =
        std::max(
            scenario.grid.dx * 1.0e-6,
            kConstrictionThroatUpperEdgeDepthFinalReliefPeakWidthCells * scenario.grid.dx);
    double max_depth_step =
        kConstrictionThroatUpperEdgeDepthFinalReliefMaxDepthPerSecond * dt * final_response;
    double max_speed_step =
        kConstrictionThroatUpperEdgeDepthFinalReliefMaxSpeedPerSecond * dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double signed_x = constriction_signed_x(scenario, col);
        if (signed_x >= 0.0) {
            continue;
        }

        double normalized_distance = (signed_x - target_center) / peak_width;
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.last_row + 1 >= scenario.grid.ny) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance || next.h(band.last_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionThroatUpperEdgeDepthFinalReliefDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        double receiver_target_h = std::max(
            kConstrictionLocalFringeTargetDepth * support_weight,
            column_mean_depth * kConstrictionThroatUpperEdgeDepthFinalReliefUpperShelfTargetScale *
                support_weight);
        for (std::size_t row = band.last_row + 1; row < scenario.grid.ny; ++row) {
            double capacity = std::max(0.0, receiver_target_h - next.h(row, col));
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            receivers.push_back(ConstrictionProfileTransferCell{
                row,
                col,
                capacity,
                flow_sign * kConstrictionThroatUpperEdgeDepthFinalReliefUpperShelfSpeedFraction *
                    reference_speed,
                -kConstrictionThroatUpperEdgeDepthFinalReliefUpperShelfCrossStreamFraction *
                    reference_speed,
            });
            receiver_capacity += capacity;
        }

        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity * kConstrictionThroatUpperEdgeDepthFinalReliefRate * dt * support_weight;
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
            clamp(kConstrictionThroatUpperEdgeDepthFinalReliefVelocityRate * dt * support_weight, 0.0, 1.0);
        double target_u =
            flow_sign * kConstrictionThroatUpperEdgeDepthFinalReliefEdgeSpeedFraction * reference_speed;
        double target_v = -kConstrictionThroatUpperEdgeDepthFinalReliefEdgeCrossStreamFraction * reference_speed;
        double blended_u = next.u(band.last_row, col) +
                           velocity_blend * (target_u - next.u(band.last_row, col));
        double blended_v = next.v(band.last_row, col) +
                           velocity_blend * (target_v - next.v(band.last_row, col));
        next.u(band.last_row, col) =
            move_toward(next.u(band.last_row, col), blended_u, max_speed_step * support_weight);
        next.v(band.last_row, col) =
            move_toward(next.v(band.last_row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_dry_bank_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (scenario.initial.wet(row, col)) {
                continue;
            }
            if (inside_relaxed_wet_band(scenario, band, throat_width_cells, col, row) &&
                next.h(row, col) > config.dry_tolerance) {
                continue;
            }
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) &&
                next.h(row, col) > config.dry_tolerance) {
                continue;
            }

            double leaked_h = next.h(row, col);
            if (leaked_h > config.dry_tolerance) {
                GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
                if (receiver.found) {
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + leaked_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + leaked_h * next.u(row, col);
                    double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + leaked_h * next.v(row, col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
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
            }
        }
    }
}

void apply_constriction_wet_band_span_shaping(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        if (!band.found || relax_cells == 0) {
            continue;
        }

        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        std::size_t allowed_count = allowed_last - allowed_first + 1;
        if (allowed_count == 0) {
            continue;
        }

        double mass = 0.0;
        double momentum_x = 0.0;
        double momentum_y = 0.0;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double h = next.h(row, col);
            if (h <= config.dry_tolerance) {
                continue;
            }
            mass += h;
            momentum_x += h * next.u(row, col);
            momentum_y += h * next.v(row, col);
        }
        if (mass <= config.dry_tolerance) {
            continue;
        }

        std::size_t supported_count =
            static_cast<std::size_t>(std::max(1.0, std::floor(mass / kConstrictionWetBandMinimumDepth)));
        std::size_t target_envelope_count = constriction_asymmetric_target_count(scenario, band, throat_width_cells, col);
        std::size_t target_count = std::min({allowed_count, target_envelope_count, supported_count});
        target_count = std::max<std::size_t>(1, target_count);

        double target_center = constriction_asymmetric_target_center(scenario, band, throat_width_cells, col);
        long min_first = static_cast<long>(allowed_first);
        long max_first = static_cast<long>(allowed_last + 1 - target_count);
        long desired_first = static_cast<long>(std::lround(target_center - 0.5 * static_cast<double>(target_count - 1)));
        std::size_t target_first = static_cast<std::size_t>(std::max(min_first, std::min(desired_first, max_first)));
        std::size_t target_last = target_first + target_count - 1;

        std::size_t target_fill_count = 0;
        for (std::size_t row = target_first; row <= target_last; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                ++target_fill_count;
            }
        }
        if (target_fill_count == 0) {
            continue;
        }

        double target_depth = mass / static_cast<double>(target_fill_count);
        double average_u = momentum_x / mass;
        double average_v = momentum_y / mass;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            if (row >= target_first && row <= target_last) {
                next.h(row, col) = target_depth;
                next.u(row, col) = average_u;
                next.v(row, col) = average_v;
            } else {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
        }
    }
}

void apply_constriction_wet_band_profile_relaxation(
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
    double max_depth_step = kConstrictionWetBandProfileMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionWetBandProfileMaxSpeedPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionProfileTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    auto target_window = [&](const ColumnWetBand& band, std::size_t col, std::size_t& first, std::size_t& last) {
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        if (!band.found || relax_cells == 0) {
            return false;
        }
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        std::size_t allowed_count = allowed_last - allowed_first + 1;
        std::size_t target_envelope_count = constriction_asymmetric_target_count(scenario, band, throat_width_cells, col);
        std::size_t supported_count = 0;
        double supported_mass = 0.0;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            supported_mass += std::max(0.0, next.h(row, col));
        }
        supported_count = static_cast<std::size_t>(std::max(1.0, std::floor(supported_mass / kConstrictionWetBandMinimumDepth)));
        std::size_t target_count = std::min({allowed_count, target_envelope_count, supported_count});
        target_count = std::max<std::size_t>(1, target_count);

        double center = constriction_asymmetric_target_center(scenario, band, throat_width_cells, col);
        long min_first = static_cast<long>(allowed_first);
        long max_first = static_cast<long>(allowed_last + 1 - target_count);
        long desired_first = static_cast<long>(std::lround(center - 0.5 * static_cast<double>(target_count - 1)));
        first = static_cast<std::size_t>(std::max(min_first, std::min(desired_first, max_first)));
        last = first + target_count - 1;
        return true;
    };

    auto profile_target = [&](const ColumnWetBand& band, std::size_t col, std::size_t row, std::size_t first, std::size_t last) {
        double target_h = 0.0;
        if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
            target_h = std::max(target_h, kConstrictionLocalFringeTargetDepth);
        }
        if (row < first || row > last) {
            return target_h;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            return target_h;
        }

        if (!scenario.initial.wet(row, col)) {
            return std::max(target_h, kConstrictionWetBandProfileDryShelfDepth);
        }

        double center = 0.5 * (static_cast<double>(first) + static_cast<double>(last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(last - first));
        double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
        double interior = std::pow(std::max(0.0, 1.0 - edge_norm), kConstrictionWetBandProfileExponent);
        double scale = kConstrictionWetBandProfileEdgeDepthScale +
                       (kConstrictionWetBandProfileInteriorDepthScale - kConstrictionWetBandProfileEdgeDepthScale) *
                           interior;
        return std::max(target_h, column_mean_depth * scale);
    };

    auto profile_velocity = [&](const ColumnWetBand& band, std::size_t row, std::size_t first, std::size_t last) {
        double center = 0.5 * (static_cast<double>(first) + static_cast<double>(last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(last - first));
        double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
        double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
        if (row < band.first_row) {
            lateral_sign = -1.0;
        } else if (row > band.last_row) {
            lateral_sign = 1.0;
        }
        double target_u = flow_sign *
                          (kConstrictionWetBandProfileSpeedFraction +
                           kConstrictionWetBandProfileEdgeSpeedBoost * edge_norm) *
                          reference_speed;
        double target_v = -lateral_sign *
                          kConstrictionWetBandProfileCrossStreamFraction *
                          std::pow(edge_norm, 0.65) *
                          reference_speed;
        return std::pair<double, double>{target_u, target_v};
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t first = 0;
        std::size_t last = 0;
        if (!target_window(band, col, first, last)) {
            continue;
        }
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            double target_h = profile_target(band, col, row, first, last);
            double current_h = next.h(row, col);
            double depth_error = current_h - target_h;
            double requested_h = std::abs(depth_error) * kConstrictionWetBandProfileRate * dt;
            double capacity = std::min(std::abs(depth_error), std::min(requested_h, max_depth_step));
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            if (depth_error > 0.0) {
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            } else {
                auto [target_u, target_v] = profile_velocity(band, row, first, last);
                receivers.push_back(ConstrictionProfileTransferCell{row, col, capacity, target_u, target_v});
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

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t first = 0;
        std::size_t last = 0;
        if (!target_window(band, col, first, last)) {
            continue;
        }
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (next.h(row, col) <= config.dry_tolerance || profile_target(band, col, row, first, last) <= 0.0) {
                continue;
            }
            auto [target_u, target_v] = profile_velocity(band, row, first, last);
            double blend = clamp(kConstrictionWetBandProfileVelocityRate * dt, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
        }
    }
}

void apply_constriction_upstream_interior_velocity_relaxation(
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
    double blend = clamp(kConstrictionUpstreamInteriorVelocityRate * dt, 0.0, 1.0);
    double max_speed_step = kConstrictionUpstreamInteriorVelocityMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (row == band.first_row || row == band.last_row || next.h(row, col) <= config.dry_tolerance ||
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }

            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            double target_fraction =
                kConstrictionUpstreamInteriorVelocityCenterSpeedFraction +
                kConstrictionUpstreamInteriorVelocityEdgeSpeedFraction *
                    std::pow(edge_norm, kConstrictionUpstreamInteriorVelocityEdgeExponent);
            double target_u = flow_sign * target_fraction * reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        }
    }
}

}  // namespace raftsim::solver_detail
