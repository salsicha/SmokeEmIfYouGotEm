#include "solver_internal.hpp"

namespace raftsim::solver_detail {

void apply_constriction_upstream_inner_upper_shelf_cross_stream_balance_final_support(
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
             kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInnerUpperShelfCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_middle_upper_shelf_cross_stream_balance_final_support(
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
             kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamMiddleUpperShelfCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_inner_upper_shelf_streamwise_balance_final_support(
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
             kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamInnerUpperShelfStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_upper_shelf_velocity_balance_final_support(
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
             kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double target_u =
            flow_sign *
            kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportSpeedFraction *
            reference_speed;
        double target_v =
            kConstrictionUpstreamUpperShelfVelocityBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign > 0.0) {
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

void apply_constriction_recovery_upper_middle_interior_cross_stream_balance_final_support(
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
             kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperMiddleInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_middle_interior_cross_stream_balance_final_support(
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
             kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamMiddleInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_lower_edge_cross_stream_balance_final_support(
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
             kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportMaxSpeedPerSecond * dt *
        final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) <= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerEdgeCrossStreamBalanceFinalSupportVelocityRate * dt *
                    support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_downstream_middle_interior_cross_stream_balance_final_support(
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
             kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionDownstreamMiddleInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_lower_interior_streamwise_balance_final_support(
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
             kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLowerInteriorStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_terminal_upper_interior_depth_balance_final_support(
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
             kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step =
        kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double max_speed_step =
        kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t donor_row =
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDonorRowIndex;
        if (donor_row >= scenario.grid.ny || donor_row <= band.first_row || donor_row >= band.last_row ||
            next.h(donor_row, col) <= config.dry_tolerance) {
            continue;
        }

        double donor_capacity = std::max(
            0.0,
            next.h(donor_row, col) -
                kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDonorFloorDepth);
        if (donor_capacity <= config.dry_tolerance) {
            continue;
        }

        std::vector<ConstrictionProfileTransferCell> receivers;
        double receiver_capacity = 0.0;
        auto add_receiver = [&](std::size_t row, double target_h, double speed_fraction, double cross_stream_fraction) {
            if (row >= scenario.grid.ny) {
                return;
            }
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
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfTargetDepth,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfCrossStreamFraction);
        add_receiver(
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeTargetDepth,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeCrossStreamFraction);
        add_receiver(
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorTargetDepth,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorCrossStreamFraction);
        if (receiver_capacity <= config.dry_tolerance) {
            continue;
        }

        double requested_h =
            receiver_capacity *
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDepthRate *
            dt * support_weight;
        double transfer_h =
            std::min(receiver_capacity, std::min(donor_capacity, std::min(requested_h, max_depth_step * support_weight)));
        if (transfer_h > config.dry_tolerance) {
            next.h(donor_row, col) =
                std::max(
                    kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDonorFloorDepth,
                    next.h(donor_row, col) - transfer_h);
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

        double velocity_blend =
            clamp(
                kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        auto shape_cell = [&](std::size_t row, double speed_fraction, double cross_stream_fraction) {
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

        shape_cell(
            donor_row,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDonorSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportDonorCrossStreamFraction);
        shape_cell(
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerShelfCrossStreamFraction);
        shape_cell(
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerEdgeCrossStreamFraction);
        shape_cell(
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorRowIndex,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorSpeedFraction,
            kConstrictionRecoveryTerminalUpperInteriorDepthBalanceFinalSupportLowerInteriorCrossStreamFraction);
    }
}

void apply_constriction_upstream_center_interior_cross_stream_balance_final_support(
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
             kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamCenterInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_late_upper_interior_cross_stream_balance_final_support(
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
             kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_v =
            kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportCrossStreamFraction *
            reference_speed;
        if (next.v(row, col) >= target_v) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryLateUpperInteriorCrossStreamBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
        next.v(row, col) =
            move_toward(next.v(row, col), blended_v, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_upper_edge_streamwise_balance_final_support(
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
             kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row = kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row < band.first_row || row > band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryUpperEdgeStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_middle_interior_streamwise_balance_final_support(
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
             kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamMiddleInteriorStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_center_interior_streamwise_balance_final_support(
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
             kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamCenterInteriorStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_middle_to_upstream_lower_shelf_depth_balance_final_support(
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
             kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportResponseStart),
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
            kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        donor_row < donor_band.first_row || donor_row > donor_band.last_row ||
        receiver_row >= receiver_band.first_row ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_initial_h = scenario.initial.h(donor_row, *donor_col);
    if (donor_initial_h <= config.dry_tolerance) {
        return;
    }

    double donor_floor = std::max(
        config.dry_tolerance,
        donor_initial_h *
            kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDonorFloorScale);
    double receiver_target =
        std::max(
            config.dry_tolerance,
            kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_floor);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDepthRate * dt *
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
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverCrossStreamFraction *
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
            kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportMaxSpeedPerSecond *
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
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryMiddleToUpstreamLowerShelfDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_upstream_lower_shelf_redistribution_final_support(
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
             kConstrictionUpstreamLowerShelfRedistributionFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamLowerShelfRedistributionFinalSupportResponseStart),
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
        column_for_post_inlet_cell(kConstrictionUpstreamLowerShelfRedistributionFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t row = kConstrictionUpstreamLowerShelfRedistributionFinalSupportTargetRowIndex;
    if (row >= scenario.grid.ny) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        row >= donor_band.first_row || row >= receiver_band.first_row ||
        next.h(row, *donor_col) <= config.dry_tolerance ||
        next.h(row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_floor =
        std::max(
            config.dry_tolerance,
            kConstrictionUpstreamLowerShelfRedistributionFinalSupportDonorTargetDepth);
    double receiver_target =
        std::max(
            config.dry_tolerance,
            kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(row, *donor_col) - donor_floor);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportDepthRate * dt *
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
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu =
        receiver_h * next.u(row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv =
        receiver_h * next.v(row, *receiver_col) + transfer_h * receiver_target_v;

    next.h(row, *donor_col) = std::max(donor_floor, next.h(row, *donor_col) - transfer_h);
    next.h(row, *receiver_col) = merged_h;
    next.u(row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

    double velocity_blend =
        clamp(
            kConstrictionUpstreamLowerShelfRedistributionFinalSupportVelocityRate * dt *
                final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportMaxSpeedPerSecond *
        dt * final_response;
    auto shape_cell = [&](std::size_t col, double speed_fraction, double cross_stream_fraction) {
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
        *donor_col,
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportDonorSpeedFraction,
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportDonorCrossStreamFraction);
    shape_cell(
        *receiver_col,
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverSpeedFraction,
        kConstrictionUpstreamLowerShelfRedistributionFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_upstream_lower_shelf_inner_streamwise_balance_final_support(
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
             kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row >= band.first_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((next.u(row, col) - target_u) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionUpstreamLowerShelfInnerStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_recovery_center_to_lower_edge_depth_balance_final_support(
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
             kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportResponseStart),
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

    std::optional<std::size_t> donor_col = column_for_post_inlet_cell(
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col = column_for_post_inlet_cell(
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDepthRate * dt *
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
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverCrossStreamFraction *
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
            kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportMaxSpeedPerSecond *
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
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryCenterToLowerEdgeDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_recovery_lower_interior_to_lower_edge_depth_balance_final_support(
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
             kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportResponseStart),
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

    std::optional<std::size_t> donor_col = column_for_post_inlet_cell(
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col = column_for_post_inlet_cell(
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDepthRate * dt *
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
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = std::max(0.0, next.h(receiver_row, *receiver_col));
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
            kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportMaxSpeedPerSecond *
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
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryLowerInteriorToLowerEdgeDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_recovery_middle_interior_to_lower_shelf_depth_balance_final_support(
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
             kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportResponseStart),
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

    std::optional<std::size_t> donor_col = column_for_post_inlet_cell(
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col = column_for_post_inlet_cell(
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t donor_row =
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDonorRowIndex;
    std::size_t receiver_row =
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverRowIndex;
    if (donor_row >= scenario.grid.ny || receiver_row >= scenario.grid.ny ||
        next.h(donor_row, *donor_col) <= config.dry_tolerance ||
        next.h(receiver_row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(donor_row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(receiver_row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity *
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDepthRate * dt *
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
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverCrossStreamFraction *
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
            kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportVelocityRate *
                dt * final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportMaxSpeedPerSecond *
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
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        receiver_row,
        *receiver_col,
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionRecoveryMiddleInteriorToLowerShelfDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

void apply_constriction_recovery_middle_interior_streamwise_balance_final_support(
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
             kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 -
                        kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportResponseStart),
            0.0,
            1.0);
    if (final_response <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step =
        kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        double post_inlet_cell =
            flow_sign >= 0.0 ? static_cast<double>(col)
                             : static_cast<double>(scenario.grid.nx - 1 - col);
        double normalized_distance =
            (post_inlet_cell -
             kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportCenterPostInletCell) /
            std::max(
                1.0e-9,
                kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportPeakWidthCells);
        double support_weight = final_response * std::exp(-(normalized_distance * normalized_distance));
        if (support_weight <= 1.0e-6) {
            continue;
        }

        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        std::size_t row =
            kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportTargetRowIndex;
        if (row >= scenario.grid.ny || row <= band.first_row || row >= band.last_row ||
            next.h(row, col) <= config.dry_tolerance) {
            continue;
        }

        double target_u =
            flow_sign *
            kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportSpeedFraction *
            reference_speed;
        if ((target_u - next.u(row, col)) * flow_sign <= 0.0) {
            continue;
        }

        double velocity_blend =
            clamp(
                kConstrictionRecoveryMiddleInteriorStreamwiseBalanceFinalSupportVelocityRate *
                    dt * support_weight,
                0.0,
                1.0);
        double blended_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
        next.u(row, col) =
            move_toward(next.u(row, col), blended_u, max_speed_step * support_weight);
    }
}

void apply_constriction_upstream_interior_depth_balance_final_support(
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
             kConstrictionUpstreamInteriorDepthBalanceFinalSupportResponseStart) /
                std::max(
                    1.0e-9,
                    1.0 - kConstrictionUpstreamInteriorDepthBalanceFinalSupportResponseStart),
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
            kConstrictionUpstreamInteriorDepthBalanceFinalSupportDonorPostInletCell);
    std::optional<std::size_t> receiver_col =
        column_for_post_inlet_cell(
            kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverPostInletCell);
    if (!donor_col || !receiver_col || *donor_col == *receiver_col) {
        return;
    }

    std::size_t row = kConstrictionUpstreamInteriorDepthBalanceFinalSupportTargetRowIndex;
    if (row >= scenario.grid.ny ||
        next.h(row, *donor_col) <= config.dry_tolerance ||
        next.h(row, *receiver_col) <= config.dry_tolerance) {
        return;
    }

    ColumnWetBand donor_band = initial_wet_band_in_column(scenario, *donor_col);
    ColumnWetBand receiver_band = initial_wet_band_in_column(scenario, *receiver_col);
    if (!donor_band.found || !receiver_band.found ||
        donor_band.count <= throat_width_cells || receiver_band.count <= throat_width_cells ||
        row <= donor_band.first_row || row >= donor_band.last_row ||
        row <= receiver_band.first_row || row >= receiver_band.last_row) {
        return;
    }

    double donor_target = std::max(
        config.dry_tolerance,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportDonorTargetDepth);
    double receiver_target = std::max(
        config.dry_tolerance,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverTargetDepth);
    double donor_capacity = std::max(0.0, next.h(row, *donor_col) - donor_target);
    double receiver_capacity = std::max(0.0, receiver_target - next.h(row, *receiver_col));
    if (donor_capacity <= config.dry_tolerance || receiver_capacity <= config.dry_tolerance) {
        return;
    }

    double max_depth_step =
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportMaxDepthPerSecond *
        dt * final_response;
    double requested_h =
        receiver_capacity * kConstrictionUpstreamInteriorDepthBalanceFinalSupportDepthRate *
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
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverSpeedFraction *
        reference_speed;
    double receiver_target_v =
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverCrossStreamFraction *
        reference_speed;
    double receiver_h = next.h(row, *receiver_col);
    double merged_h = receiver_h + transfer_h;
    double merged_hu =
        receiver_h * next.u(row, *receiver_col) + transfer_h * receiver_target_u;
    double merged_hv =
        receiver_h * next.v(row, *receiver_col) + transfer_h * receiver_target_v;

    next.h(row, *donor_col) =
        std::max(donor_target, next.h(row, *donor_col) - transfer_h);
    next.h(row, *receiver_col) = merged_h;
    next.u(row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    next.v(row, *receiver_col) =
        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

    double velocity_blend =
        clamp(
            kConstrictionUpstreamInteriorDepthBalanceFinalSupportVelocityRate * dt *
                final_response,
            0.0,
            1.0);
    double max_speed_step =
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportMaxSpeedPerSecond *
        dt * final_response;
    auto shape_cell = [&](std::size_t col, double speed_fraction, double cross_stream_fraction) {
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
        *donor_col,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportDonorSpeedFraction,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportDonorCrossStreamFraction);
    shape_cell(
        *receiver_col,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverSpeedFraction,
        kConstrictionUpstreamInteriorDepthBalanceFinalSupportReceiverCrossStreamFraction);
}

}  // namespace raftsim::solver_detail
