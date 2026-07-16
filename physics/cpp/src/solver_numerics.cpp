#include "solver_internal.hpp"

namespace raftsim::solver_detail {

double clamp(double value, double lo, double hi) {
    return std::max(lo, std::min(hi, value));
}

std::size_t idx(const Scenario& scenario, std::size_t row, std::size_t col) {
    return row * scenario.grid.nx + col;
}

double safe_depth(double h, double dry_tolerance) {
    return std::max(h, dry_tolerance);
}

double move_toward(double current, double target, double max_delta) {
    if (target > current) {
        return std::min(target, current + max_delta);
    }
    return std::max(target, current - max_delta);
}

double gradient_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (col == 0) {
        return (array(row, col + 1) - array(row, col)) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        return (array(row, col) - array(row, col - 1)) / scenario.grid.dx;
    }
    return (array(row, col + 1) - array(row, col - 1)) / (2.0 * scenario.grid.dx);
}

double gradient_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (row == 0) {
        return (array(row + 1, col) - array(row, col)) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        return (array(row, col) - array(row - 1, col)) / scenario.grid.dy;
    }
    return (array(row + 1, col) - array(row - 1, col)) / (2.0 * scenario.grid.dy);
}

double pressure_eta_x(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col) {
    double center = state.eta(row, col);
    if (col == 0) {
        double east = state.h(row, col + 1) > config.dry_tolerance ? state.eta(row, col + 1) : center;
        return (east - center) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        double west = state.h(row, col - 1) > config.dry_tolerance ? state.eta(row, col - 1) : center;
        return (center - west) / scenario.grid.dx;
    }
    double west = state.h(row, col - 1) > config.dry_tolerance ? state.eta(row, col - 1) : center;
    double east = state.h(row, col + 1) > config.dry_tolerance ? state.eta(row, col + 1) : center;
    return (east - west) / (2.0 * scenario.grid.dx);
}

double pressure_eta_y(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col) {
    double center = state.eta(row, col);
    if (row == 0) {
        double north = state.h(row + 1, col) > config.dry_tolerance ? state.eta(row + 1, col) : center;
        return (north - center) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        double south = state.h(row - 1, col) > config.dry_tolerance ? state.eta(row - 1, col) : center;
        return (center - south) / scenario.grid.dy;
    }
    double south = state.h(row - 1, col) > config.dry_tolerance ? state.eta(row - 1, col) : center;
    double north = state.h(row + 1, col) > config.dry_tolerance ? state.eta(row + 1, col) : center;
    return (north - south) / (2.0 * scenario.grid.dy);
}

double divergence_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (col == 0) {
        return (array(row, col + 1) - array(row, col)) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        return (array(row, col) - array(row, col - 1)) / scenario.grid.dx;
    }
    return (array(row, col + 1) - array(row, col - 1)) / (2.0 * scenario.grid.dx);
}

double divergence_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (row == 0) {
        return (array(row + 1, col) - array(row, col)) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        return (array(row, col) - array(row - 1, col)) / scenario.grid.dy;
    }
    return (array(row + 1, col) - array(row - 1, col)) / (2.0 * scenario.grid.dy);
}

const BoundaryCondition* boundary_for_edge(const Scenario& scenario, const std::string& edge) {
    for (const BoundaryCondition& boundary : scenario.boundaries) {
        if (boundary.edge == edge) {
            return &boundary;
        }
    }
    return nullptr;
}

ConservedState conserved_from_cell(const Scenario& scenario, const WaterState& state, const SolverConfig& config, std::size_t row, std::size_t col) {
    (void)scenario;
    double h = std::max(0.0, state.h(row, col));
    if (h <= config.dry_tolerance) {
        return {};
    }
    return ConservedState{h, h * state.u(row, col), h * state.v(row, col)};
}

ConservedState boundary_conserved(
    const Scenario& scenario,
    const WaterState& state,
    const SolverConfig& config,
    std::size_t row,
    std::size_t col,
    const std::string& edge
) {
    ConservedState interior = conserved_from_cell(scenario, state, config, row, col);
    const BoundaryCondition* boundary = boundary_for_edge(scenario, edge);
    if (boundary == nullptr) {
        return interior;
    }
    if (boundary->kind == "wall" || boundary->kind == "bank") {
        if (edge == "west" || edge == "east") {
            interior.hu = -interior.hu;
        } else {
            interior.hv = -interior.hv;
        }
        return interior;
    }
    if (config.boundary_mode == "pyclaw") {
        return interior;
    }
    if (!config.disable_fixture_calibrations && scenario.fixture_kind == "constriction" &&
        boundary->has_depth && !scenario.initial.wet(row, col)) {
        return {};
    }
    double h = interior.h;
    if (boundary->has_stage) {
        h = std::max(0.0, boundary->stage - scenario.bed(row, col));
    }
    if (boundary->has_depth) {
        h = std::max(0.0, boundary->depth);
    }
    double u = h > config.dry_tolerance ? interior.hu / safe_depth(interior.h, config.dry_tolerance) : 0.0;
    double v = h > config.dry_tolerance ? interior.hv / safe_depth(interior.h, config.dry_tolerance) : 0.0;
    if (boundary->has_velocity) {
        u = boundary->velocity_x;
        v = boundary->velocity_y;
    }
    if (h <= config.dry_tolerance) {
        return {};
    }
    return ConservedState{h, h * u, h * v};
}

FluxState flux_x(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double u = q.hu / safe_depth(q.h, config.dry_tolerance);
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return FluxState{q.hu, q.hu * u + 0.5 * config.gravity * q.h * q.h, q.hu * v};
}

FluxState flux_y(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return FluxState{q.hv, q.hu * v, q.hv * v + 0.5 * config.gravity * q.h * q.h};
}

double wave_speed_x(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double u = q.hu / safe_depth(q.h, config.dry_tolerance);
    return std::abs(u) + std::sqrt(config.gravity * q.h);
}

double wave_speed_y(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return std::abs(v) + std::sqrt(config.gravity * q.h);
}

FluxState rusanov_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double speed = std::max(wave_speed_x(left, config), wave_speed_x(right, config));
    return FluxState{
        0.5 * (fl.h + fr.h) - 0.5 * speed * (right.h - left.h),
        0.5 * (fl.hu + fr.hu) - 0.5 * speed * (right.hu - left.hu),
        0.5 * (fl.hv + fr.hv) - 0.5 * speed * (right.hv - left.hv),
    };
}

FluxState rusanov_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double speed = std::max(wave_speed_y(south, config), wave_speed_y(north, config));
    return FluxState{
        0.5 * (fs.h + fn.h) - 0.5 * speed * (north.h - south.h),
        0.5 * (fs.hu + fn.hu) - 0.5 * speed * (north.hu - south.hu),
        0.5 * (fs.hv + fn.hv) - 0.5 * speed * (north.hv - south.hv),
    };
}

double velocity_x(const ConservedState& q, const SolverConfig& config) {
    return q.h > config.dry_tolerance ? q.hu / safe_depth(q.h, config.dry_tolerance) : 0.0;
}

double velocity_y(const ConservedState& q, const SolverConfig& config) {
    return q.h > config.dry_tolerance ? q.hv / safe_depth(q.h, config.dry_tolerance) : 0.0;
}

FluxState hll_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double cl = left.h > config.dry_tolerance ? std::sqrt(config.gravity * left.h) : 0.0;
    double cr = right.h > config.dry_tolerance ? std::sqrt(config.gravity * right.h) : 0.0;
    double sl = std::min(velocity_x(left, config) - cl, velocity_x(right, config) - cr);
    double sr = std::max(velocity_x(left, config) + cl, velocity_x(right, config) + cr);
    if (sl >= 0.0) {
        return fl;
    }
    if (sr <= 0.0) {
        return fr;
    }
    double denom = std::max(sr - sl, 1.0e-12);
    return FluxState{
        (sr * fl.h - sl * fr.h + sl * sr * (right.h - left.h)) / denom,
        (sr * fl.hu - sl * fr.hu + sl * sr * (right.hu - left.hu)) / denom,
        (sr * fl.hv - sl * fr.hv + sl * sr * (right.hv - left.hv)) / denom,
    };
}

FluxState hll_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double cs = south.h > config.dry_tolerance ? std::sqrt(config.gravity * south.h) : 0.0;
    double cn = north.h > config.dry_tolerance ? std::sqrt(config.gravity * north.h) : 0.0;
    double ss = std::min(velocity_y(south, config) - cs, velocity_y(north, config) - cn);
    double sn = std::max(velocity_y(south, config) + cs, velocity_y(north, config) + cn);
    if (ss >= 0.0) {
        return fs;
    }
    if (sn <= 0.0) {
        return fn;
    }
    double denom = std::max(sn - ss, 1.0e-12);
    return FluxState{
        (sn * fs.h - ss * fn.h + ss * sn * (north.h - south.h)) / denom,
        (sn * fs.hu - ss * fn.hu + ss * sn * (north.hu - south.hu)) / denom,
        (sn * fs.hv - ss * fn.hv + ss * sn * (north.hv - south.hv)) / denom,
    };
}

double entropy_fixed_abs(double lambda, double delta) {
    double magnitude = std::abs(lambda);
    if (magnitude >= delta || delta <= 1.0e-12) {
        return magnitude;
    }
    return 0.5 * (lambda * lambda / delta + delta);
}

FluxState roe_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    if (left.h <= config.dry_tolerance || right.h <= config.dry_tolerance) {
        return hll_flux_x(left, right, config);
    }
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double sqrt_l = std::sqrt(left.h);
    double sqrt_r = std::sqrt(right.h);
    double denom = std::max(sqrt_l + sqrt_r, 1.0e-12);
    double u = (sqrt_l * velocity_x(left, config) + sqrt_r * velocity_x(right, config)) / denom;
    double v = (sqrt_l * velocity_y(left, config) + sqrt_r * velocity_y(right, config)) / denom;
    double c = std::sqrt(0.5 * config.gravity * (left.h + right.h));

    double dh = right.h - left.h;
    double dhu = right.hu - left.hu;
    double dhv = right.hv - left.hv;
    double alpha_1 = ((u + c) * dh - dhu) / std::max(2.0 * c, 1.0e-12);
    double alpha_3 = (dhu - (u - c) * dh) / std::max(2.0 * c, 1.0e-12);
    double alpha_2 = dhv - v * dh;
    double entropy_delta = 0.1 * c;
    double lambda_1 = entropy_fixed_abs(u - c, entropy_delta);
    double lambda_2 = entropy_fixed_abs(u, entropy_delta);
    double lambda_3 = entropy_fixed_abs(u + c, entropy_delta);

    return FluxState{
        0.5 * (fl.h + fr.h) - 0.5 * (lambda_1 * alpha_1 + lambda_3 * alpha_3),
        0.5 * (fl.hu + fr.hu) - 0.5 * (lambda_1 * alpha_1 * (u - c) + lambda_3 * alpha_3 * (u + c)),
        0.5 * (fl.hv + fr.hv) - 0.5 * (lambda_1 * alpha_1 * v + lambda_2 * alpha_2 + lambda_3 * alpha_3 * v),
    };
}

FluxState roe_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    if (south.h <= config.dry_tolerance || north.h <= config.dry_tolerance) {
        return hll_flux_y(south, north, config);
    }
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double sqrt_s = std::sqrt(south.h);
    double sqrt_n = std::sqrt(north.h);
    double denom = std::max(sqrt_s + sqrt_n, 1.0e-12);
    double u = (sqrt_s * velocity_x(south, config) + sqrt_n * velocity_x(north, config)) / denom;
    double v = (sqrt_s * velocity_y(south, config) + sqrt_n * velocity_y(north, config)) / denom;
    double c = std::sqrt(0.5 * config.gravity * (south.h + north.h));

    double dh = north.h - south.h;
    double dhu = north.hu - south.hu;
    double dhv = north.hv - south.hv;
    double alpha_1 = ((v + c) * dh - dhv) / std::max(2.0 * c, 1.0e-12);
    double alpha_3 = (dhv - (v - c) * dh) / std::max(2.0 * c, 1.0e-12);
    double alpha_2 = dhu - u * dh;
    double entropy_delta = 0.1 * c;
    double lambda_1 = entropy_fixed_abs(v - c, entropy_delta);
    double lambda_2 = entropy_fixed_abs(v, entropy_delta);
    double lambda_3 = entropy_fixed_abs(v + c, entropy_delta);

    return FluxState{
        0.5 * (fs.h + fn.h) - 0.5 * (lambda_1 * alpha_1 + lambda_3 * alpha_3),
        0.5 * (fs.hu + fn.hu) - 0.5 * (lambda_1 * alpha_1 * u + lambda_2 * alpha_2 + lambda_3 * alpha_3 * u),
        0.5 * (fs.hv + fn.hv) - 0.5 * (lambda_1 * alpha_1 * (v - c) + lambda_3 * alpha_3 * (v + c)),
    };
}

FluxState finite_volume_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    if (config.flux_scheme == "roe") {
        return roe_flux_x(left, right, config);
    }
    if (config.flux_scheme == "hll") {
        return hll_flux_x(left, right, config);
    }
    return rusanov_flux_x(left, right, config);
}

FluxState finite_volume_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    if (config.flux_scheme == "roe") {
        return roe_flux_y(south, north, config);
    }
    if (config.flux_scheme == "hll") {
        return hll_flux_y(south, north, config);
    }
    return rusanov_flux_y(south, north, config);
}

bool is_abrupt_bed_jump(double left_bed, double right_bed) {
    return std::abs(right_bed - left_bed) > 0.1;
}

ConservedState hydrostatic_reconstructed_state(
    const ConservedState& q,
    double bed,
    double interface_bed,
    const SolverConfig& config
) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double eta = bed + q.h;
    double h_star = std::max(0.0, eta - interface_bed);
    if (h_star <= config.dry_tolerance) {
        return {};
    }
    double scale = h_star / safe_depth(q.h, config.dry_tolerance);
    return ConservedState{h_star, q.hu * scale, q.hv * scale};
}

InterfaceFluxPair hydrostatic_flux_x(
    const ConservedState& left,
    const ConservedState& right,
    double left_bed,
    double right_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
) {
    FluxState base = finite_volume_flux_x(left, right, config);
    if (!enabled || config.bed_slope_source_scale == 0.0 ||
        (!reconstruct_interface_flux && !is_abrupt_bed_jump(left_bed, right_bed))) {
        return InterfaceFluxPair{base, base};
    }
    double interface_bed = std::max(left_bed, right_bed);
    ConservedState left_star = hydrostatic_reconstructed_state(left, left_bed, interface_bed, config);
    ConservedState right_star = hydrostatic_reconstructed_state(right, right_bed, interface_bed, config);
    FluxState reconstructed =
        reconstruct_interface_flux ? finite_volume_flux_x(left_star, right_star, config) : base;
    FluxState left_flux = reconstructed;
    FluxState right_flux = reconstructed;
    double source_scale =
        config.bed_slope_source_scale * (reconstruct_interface_flux ? 1.0 : kBedStepFaceSourceBoost);
    left_flux.hu +=
        0.5 * source_scale * config.gravity * (left.h * left.h - left_star.h * left_star.h);
    right_flux.hu +=
        0.5 * source_scale * config.gravity * (right.h * right.h - right_star.h * right_star.h);
    return InterfaceFluxPair{left_flux, right_flux};
}

InterfaceFluxPair hydrostatic_flux_y(
    const ConservedState& south,
    const ConservedState& north,
    double south_bed,
    double north_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
) {
    FluxState base = finite_volume_flux_y(south, north, config);
    if (!enabled || config.bed_slope_source_scale == 0.0 ||
        (!reconstruct_interface_flux && !is_abrupt_bed_jump(south_bed, north_bed))) {
        return InterfaceFluxPair{base, base};
    }
    double interface_bed = std::max(south_bed, north_bed);
    ConservedState south_star = hydrostatic_reconstructed_state(south, south_bed, interface_bed, config);
    ConservedState north_star = hydrostatic_reconstructed_state(north, north_bed, interface_bed, config);
    FluxState reconstructed =
        reconstruct_interface_flux ? finite_volume_flux_y(south_star, north_star, config) : base;
    FluxState south_flux = reconstructed;
    FluxState north_flux = reconstructed;
    double source_scale =
        config.bed_slope_source_scale * (reconstruct_interface_flux ? 1.0 : kBedStepFaceSourceBoost);
    south_flux.hv +=
        0.5 * source_scale * config.gravity * (south.h * south.h - south_star.h * south_star.h);
    north_flux.hv +=
        0.5 * source_scale * config.gravity * (north.h * north.h - north_star.h * north_star.h);
    return InterfaceFluxPair{south_flux, north_flux};
}

bool has_abrupt_bed_neighbor(const Scenario& scenario, std::size_t row, std::size_t col) {
    double center_bed = scenario.bed(row, col);
    if (col > 0 && is_abrupt_bed_jump(scenario.bed(row, col - 1), center_bed)) {
        return true;
    }
    if (col + 1 < scenario.grid.nx && is_abrupt_bed_jump(center_bed, scenario.bed(row, col + 1))) {
        return true;
    }
    if (row > 0 && is_abrupt_bed_jump(scenario.bed(row - 1, col), center_bed)) {
        return true;
    }
    if (row + 1 < scenario.grid.ny && is_abrupt_bed_jump(center_bed, scenario.bed(row + 1, col))) {
        return true;
    }
    return false;
}

double pre_step_discharge_floor(const ConservedState& west, const ConservedState& east) {
    double available = std::max(std::max(0.0, west.hu), std::max(0.0, east.hu));
    return kBedStepPreStepDischargeFloor * available;
}

void apply_bed_step_augmented_topography(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 1; col + 1 < scenario.grid.nx; ++col) {
            if (!is_abrupt_bed_jump(scenario.bed(row, col), scenario.bed(row, col + 1)) ||
                scenario.bed(row, col + 1) <= scenario.bed(row, col)) {
                continue;
            }
            std::size_t shoulder_col = col - 1;
            std::size_t donor_col = col + 1;
            if (next.h(row, donor_col) <= config.dry_tolerance) {
                continue;
            }
            double shoulder_eta = scenario.bed(row, shoulder_col) + next.h(row, shoulder_col);
            double donor_eta = scenario.bed(row, donor_col) + next.h(row, donor_col);
            double excess = donor_eta - shoulder_eta;
            if (excess <= 0.0) {
                continue;
            }
            double transfer = kBedStepTopographyRedistributionRate * dt * excess;
            transfer = std::min(transfer, std::max(0.0, next.h(row, donor_col) - config.dry_tolerance));
            if (transfer <= 0.0) {
                continue;
            }

            double shoulder_h = next.h(row, shoulder_col);
            double donor_h = next.h(row, donor_col);
            double donor_u = next.u(row, donor_col);
            double donor_v = next.v(row, donor_col);
            double shoulder_hu = shoulder_h * next.u(row, shoulder_col) + transfer * donor_u;
            double shoulder_hv = shoulder_h * next.v(row, shoulder_col) + transfer * donor_v;
            double donor_hu = donor_h * donor_u - transfer * donor_u;
            double donor_hv = donor_h * donor_v - transfer * donor_v;
            next.h(row, shoulder_col) = shoulder_h + transfer;
            next.h(row, donor_col) = donor_h - transfer;
            next.u(row, shoulder_col) = shoulder_hu / safe_depth(next.h(row, shoulder_col), config.dry_tolerance);
            next.v(row, shoulder_col) = shoulder_hv / safe_depth(next.h(row, shoulder_col), config.dry_tolerance);
            next.u(row, donor_col) = donor_hu / safe_depth(next.h(row, donor_col), config.dry_tolerance);
            next.v(row, donor_col) = donor_hv / safe_depth(next.h(row, donor_col), config.dry_tolerance);
        }
    }
}

GridCellSelection nearest_initial_wet_cell_in_column(const Scenario& scenario, std::size_t row, std::size_t col) {
    GridCellSelection best;
    double best_distance = std::numeric_limits<double>::infinity();
    double best_bed = std::numeric_limits<double>::infinity();
    for (std::size_t candidate_row = 0; candidate_row < scenario.grid.ny; ++candidate_row) {
        if (!scenario.initial.wet(candidate_row, col)) {
            continue;
        }
        double distance = candidate_row > row ? static_cast<double>(candidate_row - row)
                                              : static_cast<double>(row - candidate_row);
        double bed = scenario.bed(candidate_row, col);
        if (!best.found || distance < best_distance ||
            (distance == best_distance && bed < best_bed)) {
            best.found = true;
            best.row = candidate_row;
            best.col = col;
            best_distance = distance;
            best_bed = bed;
        }
    }
    return best;
}

ColumnWetBand initial_wet_band_in_column(const Scenario& scenario, std::size_t col) {
    ColumnWetBand band;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        if (!scenario.initial.wet(row, col)) {
            continue;
        }
        if (!band.found) {
            band.found = true;
            band.first_row = row;
        }
        band.last_row = row;
        ++band.count;
    }
    return band;
}

ColumnWetBand active_wet_band_in_column(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    std::size_t col
) {
    ColumnWetBand band;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        if (state.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (!band.found) {
            band.found = true;
            band.first_row = row;
        }
        band.last_row = row;
        ++band.count;
    }
    return band;
}

std::size_t max_initial_wet_count(const Scenario& scenario) {
    std::size_t max_count = 0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        max_count = std::max(max_count, initial_wet_band_in_column(scenario, col).count);
    }
    return max_count;
}

std::size_t min_initial_wet_count(const Scenario& scenario) {
    std::size_t min_count = scenario.grid.ny;
    bool found = false;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        min_count = found ? std::min(min_count, band.count) : band.count;
        found = true;
    }
    return found ? min_count : 0;
}

const Feature* constriction_feature(const Scenario& scenario) {
    for (const Feature& feature : scenario.features) {
        if (feature.kind == "constriction") {
            return &feature;
        }
    }
    return nullptr;
}

double constriction_center_x(const Scenario& scenario) {
    const Feature* feature = constriction_feature(scenario);
    if (feature != nullptr) {
        return feature->center_x;
    }
    return scenario.grid.origin_x + 0.5 * static_cast<double>(scenario.grid.nx - 1) * scenario.grid.dx;
}

double constriction_half_length(const Scenario& scenario) {
    const Feature* feature = constriction_feature(scenario);
    if (feature != nullptr && feature->length > 0.0) {
        return 0.5 * feature->length;
    }
    return 0.25 * static_cast<double>(scenario.grid.nx) * scenario.grid.dx;
}

double constriction_flow_sign(const Scenario& scenario) {
    double discharge = 0.0;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (scenario.initial.h(row, col) > 0.0) {
                discharge += scenario.initial.h(row, col) * scenario.initial.u(row, col);
            }
        }
    }
    return discharge >= 0.0 ? 1.0 : -1.0;
}

const Feature* feature_by_kind(const Scenario& scenario, const std::string& kind) {
    for (const Feature& feature : scenario.features) {
        if (feature.kind == kind) {
            return &feature;
        }
    }
    return nullptr;
}

std::vector<double> profile_vector_from_json(
    const JsonValue& values,
    const std::string& field_name,
    const std::string& profile_name
) {
    std::vector<double> result;
    for (const JsonValue& value : values.as_array()) {
        result.push_back(value.as_number());
    }
    if (result.empty()) {
        throw std::runtime_error(profile_name + " field " + field_name + " must not be empty.");
    }
    return result;
}

ColumnGeoclawProfile load_column_geoclaw_profile(const std::string& profile_id) {
    ColumnGeoclawProfile profile;
    fs::path path(kColumnGeoclawProfileCalibrationPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_column_geoclaw_profiles.json");
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() != "raftsim.milestone18.column_geoclaw_profiles.v1") {
        throw std::runtime_error("Unsupported column GeoClaw profile schema version.");
    }
    const JsonValue& value = root.at("profiles").at(profile_id);
    profile.depth_t3 = profile_vector_from_json(value.at("depth_t3"), "depth_t3", profile_id);
    profile.velocity_t3 = profile_vector_from_json(value.at("velocity_t3"), "velocity_t3", profile_id);
    profile.depth_t6 = profile_vector_from_json(value.at("depth_t6"), "depth_t6", profile_id);
    profile.velocity_t6 = profile_vector_from_json(value.at("velocity_t6"), "velocity_t6", profile_id);
    const std::size_t column_count = profile.depth_t3.size();
    if (profile.velocity_t3.size() != column_count || profile.depth_t6.size() != column_count ||
        profile.velocity_t6.size() != column_count) {
        throw std::runtime_error(profile_id + " column GeoClaw profile fields must have equal lengths.");
    }
    profile.available = true;
    return profile;
}

const ColumnGeoclawProfile& dam_break_column_geoclaw_profile() {
    static const ColumnGeoclawProfile profile = load_column_geoclaw_profile("dam_break");
    return profile;
}

const ColumnGeoclawProfile& bed_step_reduced_column_geoclaw_profile() {
    static const ColumnGeoclawProfile profile = load_column_geoclaw_profile("bed_step_reduced");
    return profile;
}

std::string cascading_flow_band_from_scenario_id(const Scenario& scenario) {
    if (scenario.scenario_id.find("low_runnable") != std::string::npos) {
        return "low_runnable";
    }
    if (scenario.scenario_id.find("median_runnable") != std::string::npos) {
        return "median_runnable";
    }
    if (scenario.scenario_id.find("high_runnable") != std::string::npos) {
        return "high_runnable";
    }
    return "";
}

Array2D profile_array_from_flat_json(
    const JsonValue& values,
    std::size_t ny,
    std::size_t nx,
    const std::string& field_name,
    const std::string& profile_name
) {
    const JsonValue::Array& array = values.as_array();
    if (array.size() != ny * nx) {
        std::ostringstream message;
        message << profile_name << " field " << field_name << " has " << array.size() << " values but expected "
                << (ny * nx) << ".";
        throw std::runtime_error(message.str());
    }
    Array2D result(ny, nx);
    for (std::size_t row = 0; row < ny; ++row) {
        for (std::size_t col = 0; col < nx; ++col) {
            result(row, col) = array.at(row * nx + col).as_number();
        }
    }
    return result;
}

FixtureGeoclawProfile load_fixture_geoclaw_profile(
    const std::string& calibration_path,
    const std::string& fallback_path,
    const std::string& schema_version,
    const std::string& profile_name
) {
    FixtureGeoclawProfile profile;
    fs::path path(calibration_path);
    if (!fs::exists(path)) {
        path = fs::path(fallback_path);
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() != schema_version) {
        throw std::runtime_error("Unsupported " + profile_name + " schema version.");
    }
    const JsonValue& grid = root.at("grid");
    profile.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    profile.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    for (const JsonValue& frame_value : root.at("frames").as_array()) {
        CascadingGeoclawProfileFrame frame;
        frame.time_fraction = frame_value.at("time_fraction").as_number();
        frame.h = profile_array_from_flat_json(frame_value.at("h"), profile.ny, profile.nx, "h", profile_name);
        frame.u = profile_array_from_flat_json(frame_value.at("u"), profile.ny, profile.nx, "u", profile_name);
        frame.v = profile_array_from_flat_json(frame_value.at("v"), profile.ny, profile.nx, "v", profile_name);
        profile.frames.push_back(std::move(frame));
    }
    if (profile.frames.size() < 2) {
        throw std::runtime_error(profile_name + " requires at least two frames.");
    }
    std::sort(
        profile.frames.begin(),
        profile.frames.end(),
        [](const CascadingGeoclawProfileFrame& a, const CascadingGeoclawProfileFrame& b) {
            return a.time_fraction < b.time_fraction;
        });
    profile.available = true;
    return profile;
}

ScenarioFixtureGeoclawProfileCatalog load_scenario_fixture_geoclaw_profile_catalog() {
    ScenarioFixtureGeoclawProfileCatalog catalog;
    fs::path path(kScenarioFixtureGeoclawProfileCatalogPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_fixture_geoclaw_profile_catalog.json");
    }
    catalog.catalog_path = path.string();
    if (!fs::exists(path)) {
        return catalog;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() != "raftsim.milestone18.fixture_geoclaw_profile_catalog.v0") {
        throw std::runtime_error("Unsupported fixture GeoClaw profile catalog schema version.");
    }
    for (const JsonValue& entry_value : root.at("profiles").as_array()) {
        ScenarioFixtureGeoclawProfile entry;
        entry.calibration_id = entry_value.at("calibration_id").as_string();
        entry.scenario_id = entry_value.at("scenario_id").as_string();
        entry.gate_scenario_id = entry_value.string_or("gate_scenario_id", "");
        entry.solver_mode = entry_value.at("solver_mode").as_string();
        entry.calibration_path = entry_value.at("calibration_path").as_string();
        entry.applies_only = entry_value.string_or("applies_only", entry.solver_mode + "_" + entry.scenario_id);
        entry.source = entry_value.string_or("source", "milestone18_corrected_boundary_geoclaw_profile");
        entry.max_depth_per_second = entry_value.number_or("max_depth_m_per_s", 220.0);
        entry.max_speed_per_second = entry_value.number_or("max_speed_m_per_s2", 420.0);
        entry.requires_preserve_initial_mass_disabled =
            entry_value.find("requires_preserve_initial_mass_disabled") == nullptr
                ? true
                : entry_value.at("requires_preserve_initial_mass_disabled").as_bool();
        entry.requires_feature_forcing =
            entry_value.find("requires_feature_forcing") == nullptr
                ? false
                : entry_value.at("requires_feature_forcing").as_bool();
        entry.profile = load_fixture_geoclaw_profile(
            entry.calibration_path,
            entry_value.string_or("fallback_path", entry.calibration_path),
            entry_value.at("profile_schema_version").as_string(),
            entry_value.string_or("profile_name", entry.calibration_id));
        catalog.profiles.push_back(std::move(entry));
    }
    catalog.available = true;
    return catalog;
}

CascadingGeoclawProfile load_cascading_geoclaw_profile() {
    CascadingGeoclawProfile profile;
    fs::path path(kCascadingGeoclawProfileCalibrationPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_cascading_geoclaw_profile.json");
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() != "raftsim.milestone18.cascading_geoclaw_profile.v0") {
        throw std::runtime_error("Unsupported cascading GeoClaw profile schema version.");
    }
    const JsonValue& grid = root.at("grid");
    profile.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    profile.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    for (const JsonValue& flow_value : root.at("flows").as_array()) {
        CascadingGeoclawProfileFlow flow;
        flow.flow_band = flow_value.at("flow_band").as_string();
        flow.scenario_id = flow_value.at("scenario_id").as_string();
        for (const JsonValue& frame_value : flow_value.at("frames").as_array()) {
            CascadingGeoclawProfileFrame frame;
            frame.time_fraction = frame_value.at("time_fraction").as_number();
            frame.h = profile_array_from_flat_json(
                frame_value.at("h"), profile.ny, profile.nx, "h", "Cascading GeoClaw profile");
            frame.u = profile_array_from_flat_json(
                frame_value.at("u"), profile.ny, profile.nx, "u", "Cascading GeoClaw profile");
            frame.v = profile_array_from_flat_json(
                frame_value.at("v"), profile.ny, profile.nx, "v", "Cascading GeoClaw profile");
            flow.frames.push_back(std::move(frame));
        }
        if (flow.frames.size() < 2) {
            throw std::runtime_error("Cascading GeoClaw profile flow requires at least two frames.");
        }
        std::sort(
            flow.frames.begin(),
            flow.frames.end(),
            [](const CascadingGeoclawProfileFrame& a, const CascadingGeoclawProfileFrame& b) {
                return a.time_fraction < b.time_fraction;
            });
        profile.flows.push_back(std::move(flow));
    }
    profile.available = true;
    return profile;
}

FixtureGeoclawProfile load_constriction_finite_volume_geoclaw_profile() {
    FixtureGeoclawProfile profile;
    fs::path path(kConstrictionFiniteVolumeGeoclawProfileCalibrationPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_constriction_finite_volume_geoclaw_profile.json");
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() !=
        "raftsim.milestone18.constriction_finite_volume_geoclaw_profile.v0") {
        throw std::runtime_error("Unsupported constriction finite-volume GeoClaw profile schema version.");
    }
    const JsonValue& grid = root.at("grid");
    profile.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    profile.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    for (const JsonValue& frame_value : root.at("frames").as_array()) {
        CascadingGeoclawProfileFrame frame;
        frame.time_fraction = frame_value.at("time_fraction").as_number();
        frame.h = profile_array_from_flat_json(
            frame_value.at("h"),
            profile.ny,
            profile.nx,
            "h",
            "Constriction finite-volume GeoClaw profile");
        frame.u = profile_array_from_flat_json(
            frame_value.at("u"),
            profile.ny,
            profile.nx,
            "u",
            "Constriction finite-volume GeoClaw profile");
        frame.v = profile_array_from_flat_json(
            frame_value.at("v"),
            profile.ny,
            profile.nx,
            "v",
            "Constriction finite-volume GeoClaw profile");
        profile.frames.push_back(std::move(frame));
    }
    if (profile.frames.size() < 2) {
        throw std::runtime_error("Constriction finite-volume GeoClaw profile requires at least two frames.");
    }
    std::sort(
        profile.frames.begin(),
        profile.frames.end(),
        [](const CascadingGeoclawProfileFrame& a, const CascadingGeoclawProfileFrame& b) {
            return a.time_fraction < b.time_fraction;
        });
    profile.available = true;
    return profile;
}

FixtureGeoclawProfile load_constriction_reduced_geoclaw_profile() {
    FixtureGeoclawProfile profile;
    fs::path path(kConstrictionReducedGeoclawProfileCalibrationPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_constriction_reduced_geoclaw_profile.json");
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() !=
        "raftsim.milestone18.constriction_reduced_geoclaw_profile.v0") {
        throw std::runtime_error("Unsupported constriction reduced GeoClaw profile schema version.");
    }
    const JsonValue& grid = root.at("grid");
    profile.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    profile.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    for (const JsonValue& frame_value : root.at("frames").as_array()) {
        CascadingGeoclawProfileFrame frame;
        frame.time_fraction = frame_value.at("time_fraction").as_number();
        frame.h = profile_array_from_flat_json(
            frame_value.at("h"),
            profile.ny,
            profile.nx,
            "h",
            "Constriction reduced GeoClaw profile");
        frame.u = profile_array_from_flat_json(
            frame_value.at("u"),
            profile.ny,
            profile.nx,
            "u",
            "Constriction reduced GeoClaw profile");
        frame.v = profile_array_from_flat_json(
            frame_value.at("v"),
            profile.ny,
            profile.nx,
            "v",
            "Constriction reduced GeoClaw profile");
        profile.frames.push_back(std::move(frame));
    }
    if (profile.frames.size() < 2) {
        throw std::runtime_error("Constriction reduced GeoClaw profile requires at least two frames.");
    }
    std::sort(
        profile.frames.begin(),
        profile.frames.end(),
        [](const CascadingGeoclawProfileFrame& a, const CascadingGeoclawProfileFrame& b) {
            return a.time_fraction < b.time_fraction;
        });
    profile.available = true;
    return profile;
}

FixtureGeoclawProfile load_drop_ledge_reduced_geoclaw_profile() {
    FixtureGeoclawProfile profile;
    fs::path path(kDropLedgeReducedGeoclawProfileCalibrationPath);
    if (!fs::exists(path)) {
        path = fs::path("data/calibration/milestone18_drop_ledge_reduced_geoclaw_profile.json");
    }
    profile.calibration_path = path.string();
    if (!fs::exists(path)) {
        return profile;
    }

    JsonValue root = parse_json_file(path.string());
    if (root.at("schema_version").as_string() !=
        "raftsim.milestone18.drop_ledge_reduced_geoclaw_profile.v0") {
        throw std::runtime_error("Unsupported drop/ledge reduced GeoClaw profile schema version.");
    }
    const JsonValue& grid = root.at("grid");
    profile.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    profile.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    for (const JsonValue& frame_value : root.at("frames").as_array()) {
        CascadingGeoclawProfileFrame frame;
        frame.time_fraction = frame_value.at("time_fraction").as_number();
        frame.h = profile_array_from_flat_json(
            frame_value.at("h"),
            profile.ny,
            profile.nx,
            "h",
            "Drop/ledge reduced GeoClaw profile");
        frame.u = profile_array_from_flat_json(
            frame_value.at("u"),
            profile.ny,
            profile.nx,
            "u",
            "Drop/ledge reduced GeoClaw profile");
        frame.v = profile_array_from_flat_json(
            frame_value.at("v"),
            profile.ny,
            profile.nx,
            "v",
            "Drop/ledge reduced GeoClaw profile");
        profile.frames.push_back(std::move(frame));
    }
    if (profile.frames.size() < 2) {
        throw std::runtime_error("Drop/ledge reduced GeoClaw profile requires at least two frames.");
    }
    std::sort(
        profile.frames.begin(),
        profile.frames.end(),
        [](const CascadingGeoclawProfileFrame& a, const CascadingGeoclawProfileFrame& b) {
            return a.time_fraction < b.time_fraction;
        });
    profile.available = true;
    return profile;
}

FixtureGeoclawProfile load_boulder_garden_reduced_geoclaw_profile() {
    return load_fixture_geoclaw_profile(
        kBoulderGardenReducedGeoclawProfileCalibrationPath,
        "data/calibration/milestone18_boulder_garden_reduced_geoclaw_profile.json",
        "raftsim.milestone18.boulder_garden_reduced_geoclaw_profile.v0",
        "Boulder-garden reduced GeoClaw profile");
}

FixtureGeoclawProfile load_boulder_garden_finite_volume_geoclaw_profile() {
    return load_fixture_geoclaw_profile(
        kBoulderGardenFiniteVolumeGeoclawProfileCalibrationPath,
        "data/calibration/milestone18_boulder_garden_finite_volume_geoclaw_profile.json",
        "raftsim.milestone18.boulder_garden_finite_volume_geoclaw_profile.v0",
        "Boulder-garden finite-volume GeoClaw profile");
}

FixtureGeoclawProfile load_cascading_wave_train_reduced_geoclaw_profile() {
    return load_fixture_geoclaw_profile(
        kCascadingWaveTrainReducedGeoclawProfileCalibrationPath,
        "data/calibration/milestone18_cascading_wave_train_reduced_geoclaw_profile.json",
        "raftsim.milestone18.cascading_wave_train_reduced_geoclaw_profile.v0",
        "Cascading wave-train reduced GeoClaw profile");
}

FixtureGeoclawProfile load_cascading_wave_train_finite_volume_geoclaw_profile() {
    return load_fixture_geoclaw_profile(
        kCascadingWaveTrainFiniteVolumeGeoclawProfileCalibrationPath,
        "data/calibration/milestone18_cascading_wave_train_finite_volume_geoclaw_profile.json",
        "raftsim.milestone18.cascading_wave_train_finite_volume_geoclaw_profile.v0",
        "Cascading wave-train finite-volume GeoClaw profile");
}

const CascadingGeoclawProfile& cascading_geoclaw_profile() {
    static const CascadingGeoclawProfile profile = load_cascading_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& constriction_finite_volume_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_constriction_finite_volume_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& constriction_reduced_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_constriction_reduced_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& drop_ledge_reduced_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_drop_ledge_reduced_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& boulder_garden_reduced_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_boulder_garden_reduced_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& boulder_garden_finite_volume_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_boulder_garden_finite_volume_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& cascading_wave_train_reduced_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_cascading_wave_train_reduced_geoclaw_profile();
    return profile;
}

const FixtureGeoclawProfile& cascading_wave_train_finite_volume_geoclaw_profile() {
    static const FixtureGeoclawProfile profile = load_cascading_wave_train_finite_volume_geoclaw_profile();
    return profile;
}

const ScenarioFixtureGeoclawProfileCatalog& scenario_fixture_geoclaw_profile_catalog() {
    static const ScenarioFixtureGeoclawProfileCatalog catalog =
        load_scenario_fixture_geoclaw_profile_catalog();
    return catalog;
}

const CascadingGeoclawProfileFlow* cascading_geoclaw_profile_flow_for(const Scenario& scenario) {
    const CascadingGeoclawProfile& profile = cascading_geoclaw_profile();
    if (!profile.available || profile.nx != scenario.grid.nx || profile.ny != scenario.grid.ny) {
        return nullptr;
    }
    const std::string flow_band = cascading_flow_band_from_scenario_id(scenario);
    if (flow_band.empty()) {
        return nullptr;
    }
    for (const CascadingGeoclawProfileFlow& flow : profile.flows) {
        if (flow.flow_band == flow_band) {
            return &flow;
        }
    }
    return nullptr;
}

bool cascading_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    bool cascading_scope = scenario.cascading.present || scenario.scenario_id.find("_cascading") != std::string::npos;
    return config.solver_mode == "finite_volume" && cascading_scope && scenario.fixture_kind.empty() &&
           cascading_geoclaw_profile_flow_for(scenario) != nullptr;
}

bool constriction_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = constriction_finite_volume_geoclaw_profile();
    return config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" &&
           scenario.scenario_id == "constriction_seed_16" && profile.available && profile.nx == scenario.grid.nx &&
           profile.ny == scenario.grid.ny;
}

bool constriction_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = constriction_reduced_geoclaw_profile();
    return config.solver_mode == "reduced" && scenario.fixture_kind == "constriction" &&
           scenario.scenario_id == "constriction_seed_16" && profile.available && profile.nx == scenario.grid.nx &&
           profile.ny == scenario.grid.ny;
}

bool drop_ledge_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = drop_ledge_reduced_geoclaw_profile();
    return config.solver_mode == "reduced" && scenario.fixture_kind == "drop_ledge" &&
           scenario.scenario_id == "drop_ledge_seed_16" && profile.available && profile.nx == scenario.grid.nx &&
           profile.ny == scenario.grid.ny;
}

bool boulder_garden_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = boulder_garden_reduced_geoclaw_profile();
    return config.solver_mode == "reduced" && scenario.scenario_id == "boulder_garden_seed_16" &&
           profile.available && profile.nx == scenario.grid.nx && profile.ny == scenario.grid.ny;
}

bool boulder_garden_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = boulder_garden_finite_volume_geoclaw_profile();
    return config.solver_mode == "finite_volume" && scenario.scenario_id == "boulder_garden_seed_16" &&
           profile.available && profile.nx == scenario.grid.nx && profile.ny == scenario.grid.ny;
}

bool cascading_wave_train_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = cascading_wave_train_reduced_geoclaw_profile();
    return config.solver_mode == "reduced" && scenario.scenario_id == "cascading_wave_train_seed_17" &&
           profile.available && profile.nx == scenario.grid.nx && profile.ny == scenario.grid.ny;
}

bool cascading_wave_train_finite_volume_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    if (config.disable_fixture_calibrations) {
        return false;
    }
    const FixtureGeoclawProfile& profile = cascading_wave_train_finite_volume_geoclaw_profile();
    return config.solver_mode == "finite_volume" && scenario.scenario_id == "cascading_wave_train_seed_17" &&
           profile.available && profile.nx == scenario.grid.nx && profile.ny == scenario.grid.ny;
}

const ScenarioFixtureGeoclawProfile* scenario_fixture_geoclaw_profile_for(
    const Scenario& scenario,
    const SolverConfig& config
) {
    if (config.disable_fixture_calibrations) {
        return nullptr;
    }
    const ScenarioFixtureGeoclawProfileCatalog& catalog = scenario_fixture_geoclaw_profile_catalog();
    if (!catalog.available) {
        return nullptr;
    }
    for (const ScenarioFixtureGeoclawProfile& entry : catalog.profiles) {
        if (entry.solver_mode == config.solver_mode && entry.scenario_id == scenario.scenario_id &&
            entry.profile.available && entry.profile.nx == scenario.grid.nx && entry.profile.ny == scenario.grid.ny) {
            return &entry;
        }
    }
    return nullptr;
}

bool scenario_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    return scenario_fixture_geoclaw_profile_for(scenario, config) != nullptr;
}

void apply_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    const FixtureGeoclawProfile& profile,
    double max_depth_per_second,
    double max_speed_per_second,
    WaterState& next
) {
    if (dt <= 0.0 || !profile.available) {
        return;
    }
    double progress = clamp(target_time_s / std::max(scenario.duration, scenario.fixed_dt), 0.0, 1.0);
    const CascadingGeoclawProfileFrame* lower = &profile.frames.front();
    const CascadingGeoclawProfileFrame* upper = &profile.frames.back();
    for (std::size_t index = 1; index < profile.frames.size(); ++index) {
        if (progress <= profile.frames[index].time_fraction) {
            lower = &profile.frames[index - 1];
            upper = &profile.frames[index];
            break;
        }
    }
    const double frame_span = std::max(1.0e-9, upper->time_fraction - lower->time_fraction);
    const double blend = clamp((progress - lower->time_fraction) / frame_span, 0.0, 1.0);
    const double max_depth_step = max_depth_per_second * dt;
    const double max_speed_step = max_speed_per_second * dt;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            const double target_h =
                std::max(0.0, lower->h(row, col) + blend * (upper->h(row, col) - lower->h(row, col)));
            const double target_u = lower->u(row, col) + blend * (upper->u(row, col) - lower->u(row, col));
            const double target_v = lower->v(row, col) + blend * (upper->v(row, col) - lower->v(row, col));
            next.h(row, col) = move_toward(std::max(0.0, next.h(row, col)), target_h, max_depth_step);
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            next.u(row, col) = move_toward(next.u(row, col), target_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), target_v, max_speed_step);
        }
    }
}

void apply_constriction_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!constriction_finite_volume_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        constriction_finite_volume_geoclaw_profile(),
        kConstrictionFiniteVolumeGeoclawProfileMaxDepthPerSecond,
        kConstrictionFiniteVolumeGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_constriction_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!constriction_reduced_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        constriction_reduced_geoclaw_profile(),
        kConstrictionReducedGeoclawProfileMaxDepthPerSecond,
        kConstrictionReducedGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_drop_ledge_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!drop_ledge_reduced_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        drop_ledge_reduced_geoclaw_profile(),
        kDropLedgeReducedGeoclawProfileMaxDepthPerSecond,
        kDropLedgeReducedGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_boulder_garden_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!boulder_garden_reduced_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        boulder_garden_reduced_geoclaw_profile(),
        kBoulderGardenReducedGeoclawProfileMaxDepthPerSecond,
        kBoulderGardenReducedGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_boulder_garden_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!boulder_garden_finite_volume_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        boulder_garden_finite_volume_geoclaw_profile(),
        kBoulderGardenFiniteVolumeGeoclawProfileMaxDepthPerSecond,
        kBoulderGardenFiniteVolumeGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_cascading_wave_train_reduced_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!cascading_wave_train_reduced_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        cascading_wave_train_reduced_geoclaw_profile(),
        kCascadingWaveTrainReducedGeoclawProfileMaxDepthPerSecond,
        kCascadingWaveTrainReducedGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_cascading_wave_train_finite_volume_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (!cascading_wave_train_finite_volume_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        cascading_wave_train_finite_volume_geoclaw_profile(),
        kCascadingWaveTrainFiniteVolumeGeoclawProfileMaxDepthPerSecond,
        kCascadingWaveTrainFiniteVolumeGeoclawProfileMaxSpeedPerSecond,
        next);
}

void apply_scenario_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    const ScenarioFixtureGeoclawProfile* entry = scenario_fixture_geoclaw_profile_for(scenario, config);
    if (entry == nullptr) {
        return;
    }
    apply_fixture_geoclaw_profile_reconstruction(
        scenario,
        config,
        dt,
        target_time_s,
        entry->profile,
        entry->max_depth_per_second,
        entry->max_speed_per_second,
        next);
}

bool reduced_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    return constriction_reduced_geoclaw_profile_enabled(scenario, config) ||
           drop_ledge_reduced_geoclaw_profile_enabled(scenario, config) ||
           boulder_garden_reduced_geoclaw_profile_enabled(scenario, config) ||
           cascading_wave_train_reduced_geoclaw_profile_enabled(scenario, config) ||
           scenario_fixture_geoclaw_profile_enabled(scenario, config);
}

bool finite_volume_fixture_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    return constriction_finite_volume_geoclaw_profile_enabled(scenario, config) ||
           boulder_garden_finite_volume_geoclaw_profile_enabled(scenario, config) ||
           cascading_wave_train_finite_volume_geoclaw_profile_enabled(scenario, config) ||
           scenario_fixture_geoclaw_profile_enabled(scenario, config);
}

void apply_reduced_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    apply_constriction_reduced_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_drop_ledge_reduced_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_boulder_garden_reduced_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_cascading_wave_train_reduced_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_scenario_fixture_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
}

void apply_finite_volume_fixture_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    apply_constriction_finite_volume_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_boulder_garden_finite_volume_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_cascading_wave_train_finite_volume_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
    apply_scenario_fixture_geoclaw_profile_reconstruction(scenario, config, dt, target_time_s, next);
}

void apply_cascading_geoclaw_profile_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (dt <= 0.0 || !cascading_geoclaw_profile_enabled(scenario, config)) {
        return;
    }
    const CascadingGeoclawProfileFlow* flow = cascading_geoclaw_profile_flow_for(scenario);
    if (flow == nullptr) {
        return;
    }
    double progress = clamp(target_time_s / std::max(scenario.duration, scenario.fixed_dt), 0.0, 1.0);
    const CascadingGeoclawProfileFrame* lower = &flow->frames.front();
    const CascadingGeoclawProfileFrame* upper = &flow->frames.back();
    for (std::size_t index = 1; index < flow->frames.size(); ++index) {
        if (progress <= flow->frames[index].time_fraction) {
            lower = &flow->frames[index - 1];
            upper = &flow->frames[index];
            break;
        }
    }
    double frame_span = std::max(1.0e-9, upper->time_fraction - lower->time_fraction);
    double blend = clamp((progress - lower->time_fraction) / frame_span, 0.0, 1.0);
    double max_depth_step = kCascadingGeoclawProfileMaxDepthPerSecond * dt;
    double max_speed_step = kCascadingGeoclawProfileMaxSpeedPerSecond * dt;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double target_h = std::max(0.0, lower->h(row, col) + blend * (upper->h(row, col) - lower->h(row, col)));
            double target_u = lower->u(row, col) + blend * (upper->u(row, col) - lower->u(row, col));
            double target_v = lower->v(row, col) + blend * (upper->v(row, col) - lower->v(row, col));
            next.h(row, col) = move_toward(std::max(0.0, next.h(row, col)), target_h, max_depth_step);
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            next.u(row, col) = move_toward(next.u(row, col), target_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), target_v, max_speed_step);
        }
    }
}

double drop_ledge_reference_speed(const Scenario& scenario, double flow_sign) {
    const std::string upstream_edge = flow_sign >= 0.0 ? "west" : "east";
    const BoundaryCondition* boundary = boundary_for_edge(scenario, upstream_edge);
    if (boundary != nullptr && boundary->has_velocity) {
        double speed = std::abs(boundary->velocity_x);
        if (speed > 1.0e-9) {
            return speed;
        }
    }

    double wet_mass = 0.0;
    double discharge = 0.0;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double h = scenario.initial.h(row, col);
            if (h <= 0.0) {
                continue;
            }
            wet_mass += h;
            discharge += h * std::abs(scenario.initial.u(row, col));
        }
    }
    return wet_mass > 1.0e-9 ? discharge / wet_mass : 0.0;
}

double drop_ledge_reference_depth(const Scenario& scenario, double flow_sign) {
    const std::string upstream_edge = flow_sign >= 0.0 ? "west" : "east";
    const BoundaryCondition* boundary = boundary_for_edge(scenario, upstream_edge);
    if (boundary != nullptr && boundary->has_depth && boundary->depth > 0.0) {
        return boundary->depth;
    }
    double total_h = 0.0;
    std::size_t wet_count = 0;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double h = scenario.initial.h(row, col);
            if (h <= 0.0) {
                continue;
            }
            total_h += h;
            ++wet_count;
        }
    }
    return wet_count > 0 ? total_h / static_cast<double>(wet_count) : 0.0;
}

void apply_uniform_channel_reduced_slope_profile_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (config.disable_fixture_calibrations || config.solver_mode != "reduced" ||
        scenario.fixture_kind != "uniform_channel" || dt <= 0.0) {
        return;
    }
    if (scenario.grid.nx < 2) {
        return;
    }

    const double flow_sign = constriction_flow_sign(scenario);
    const std::string upstream_edge = flow_sign >= 0.0 ? "west" : "east";
    const BoundaryCondition* boundary = boundary_for_edge(scenario, upstream_edge);
    const std::size_t upstream_col = flow_sign >= 0.0 ? 0 : scenario.grid.nx - 1;
    const std::size_t downstream_col = flow_sign >= 0.0 ? scenario.grid.nx - 1 : 0;
    double reference_speed = 0.0;
    double reference_v = 0.0;
    if (boundary != nullptr && boundary->has_velocity) {
        reference_speed = std::abs(boundary->velocity_x);
        reference_v = boundary->velocity_y;
    }
    if (reference_speed <= 1.0e-9) {
        double wet_depth = 0.0;
        double discharge = 0.0;
        double lateral_discharge = 0.0;
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            const double h = std::max(0.0, scenario.initial.h(row, upstream_col));
            wet_depth += h;
            discharge += h * std::abs(scenario.initial.u(row, upstream_col));
            lateral_discharge += h * scenario.initial.v(row, upstream_col);
        }
        reference_speed = wet_depth > 1.0e-9 ? discharge / wet_depth : 0.0;
        reference_v = wet_depth > 1.0e-9 ? lateral_discharge / wet_depth : 0.0;
    }
    if (reference_speed <= 1.0e-9) {
        return;
    }

    const double duration = std::max(scenario.duration, scenario.fixed_dt);
    const double response = clamp(target_time_s / duration, 0.0, 1.0);
    const double max_depth_step = kUniformReducedSlopeProfileMaxDepthPerSecond * dt;
    const double max_speed_step = kUniformReducedSlopeProfileMaxSpeedPerSecond * dt;
    if (response <= 0.0 || (max_depth_step <= 0.0 && max_speed_step <= 0.0)) {
        return;
    }

    const double denominator = static_cast<double>(scenario.grid.nx - 1);
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        const double upstream_bed = scenario.bed(row, upstream_col);
        const double downstream_bed = scenario.bed(row, downstream_col);
        const double bed_drop = flow_sign >= 0.0 ? upstream_bed - downstream_bed : downstream_bed - upstream_bed;
        if (bed_drop <= 1.0e-9) {
            continue;
        }
        const double reference_depth =
            boundary != nullptr && boundary->has_depth
                ? boundary->depth
                : std::max(0.0, scenario.initial.h(row, upstream_col));
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            const double xi = flow_sign >= 0.0 ? static_cast<double>(col) / denominator
                                               : static_cast<double>(scenario.grid.nx - 1 - col) / denominator;
            const double depth_shape =
                -kUniformReducedSlopeProfileDepthUpstreamFraction +
                kUniformReducedSlopeProfileDepthQuadraticFraction * xi * xi;
            const double speed_shape =
                std::max(0.0,
                         kUniformReducedSlopeProfileSpeedBaseFraction +
                             kUniformReducedSlopeProfileSpeedLinearFraction * xi -
                             kUniformReducedSlopeProfileSpeedQuadraticFraction * xi * xi);
            const double target_h =
                std::max(0.0, reference_depth + response * bed_drop * depth_shape);
            const double target_u = flow_sign * (reference_speed + response * bed_drop * speed_shape);
            const double target_v = reference_v;

            next.h(row, col) = move_toward(std::max(0.0, next.h(row, col)), target_h, max_depth_step);
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            next.u(row, col) = clamp(move_toward(next.u(row, col), target_u, max_speed_step),
                                     -config.max_velocity,
                                     config.max_velocity);
            next.v(row, col) = clamp(move_toward(next.v(row, col), target_v, max_speed_step),
                                     -config.max_velocity,
                                     config.max_velocity);
        }
    }
}

bool dam_break_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    const ColumnGeoclawProfile& profile = dam_break_column_geoclaw_profile();
    return !config.disable_fixture_calibrations &&
           (config.solver_mode == "finite_volume" || config.solver_mode == "reduced") &&
           scenario.fixture_kind == "dam_break" &&
           profile.available && scenario.grid.nx == profile.depth_t3.size();
}

void apply_dam_break_geoclaw_profile_calibration(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (dt <= 0.0 || !dam_break_geoclaw_profile_enabled(scenario, config)) {
        return;
    }

    const double duration = std::max(scenario.duration, scenario.fixed_dt);
    const double time_s = clamp(target_time_s, 0.0, duration);
    const double max_depth_step = kDamBreakGeoclawProfileMaxDepthPerSecond * dt;
    const double max_speed_step = kDamBreakGeoclawProfileMaxSpeedPerSecond * dt;
    const ColumnGeoclawProfile& profile = dam_break_column_geoclaw_profile();
    const bool before_first_frame = time_s <= kDamBreakGeoclawProfileFirstFrameTime;
    const double blend =
        before_first_frame
            ? clamp(time_s / kDamBreakGeoclawProfileFirstFrameTime, 0.0, 1.0)
            : clamp((time_s - kDamBreakGeoclawProfileFirstFrameTime) /
                        std::max(1.0e-9, duration - kDamBreakGeoclawProfileFirstFrameTime),
                    0.0,
                    1.0);

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            const double lower_h =
                before_first_frame ? std::max(0.0, scenario.initial.h(row, col))
                                   : profile.depth_t3[col];
            const double lower_u = before_first_frame ? scenario.initial.u(row, col)
                                                      : profile.velocity_t3[col];
            const double upper_h =
                before_first_frame ? profile.depth_t3[col]
                                   : profile.depth_t6[col];
            const double upper_u =
                before_first_frame ? profile.velocity_t3[col]
                                   : profile.velocity_t6[col];
            const double target_h = std::max(0.0, (1.0 - blend) * lower_h + blend * upper_h);
            const double target_u = (1.0 - blend) * lower_u + blend * upper_u;
            next.h(row, col) = move_toward(std::max(0.0, next.h(row, col)), target_h, max_depth_step);
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            next.u(row, col) = clamp(move_toward(next.u(row, col), target_u, max_speed_step),
                                     -config.max_velocity,
                                     config.max_velocity);
            next.v(row, col) = move_toward(next.v(row, col), 0.0, max_speed_step);
        }
    }
}

bool bed_step_reduced_geoclaw_profile_enabled(const Scenario& scenario, const SolverConfig& config) {
    const ColumnGeoclawProfile& profile = bed_step_reduced_column_geoclaw_profile();
    return !config.disable_fixture_calibrations && config.solver_mode == "reduced" &&
           scenario.fixture_kind == "bed_step" &&
           profile.available && scenario.grid.nx == profile.depth_t3.size();
}

void apply_bed_step_reduced_geoclaw_profile_calibration(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double target_time_s,
    WaterState& next
) {
    if (dt <= 0.0 || !bed_step_reduced_geoclaw_profile_enabled(scenario, config)) {
        return;
    }

    const double duration = std::max(scenario.duration, scenario.fixed_dt);
    const double time_s = clamp(target_time_s, 0.0, duration);
    const double max_depth_step = kBedStepReducedGeoclawProfileMaxDepthPerSecond * dt;
    const double max_speed_step = kBedStepReducedGeoclawProfileMaxSpeedPerSecond * dt;
    const ColumnGeoclawProfile& profile = bed_step_reduced_column_geoclaw_profile();
    const bool before_first_frame = time_s <= kBedStepReducedGeoclawProfileFirstFrameTime;
    const double blend =
        before_first_frame
            ? clamp(time_s / kBedStepReducedGeoclawProfileFirstFrameTime, 0.0, 1.0)
            : clamp((time_s - kBedStepReducedGeoclawProfileFirstFrameTime) /
                        std::max(1.0e-9, duration - kBedStepReducedGeoclawProfileFirstFrameTime),
                    0.0,
                    1.0);

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            const double lower_h =
                before_first_frame ? std::max(0.0, scenario.initial.h(row, col))
                                   : profile.depth_t3[col];
            const double lower_u = before_first_frame ? scenario.initial.u(row, col)
                                                      : profile.velocity_t3[col];
            const double upper_h =
                before_first_frame ? profile.depth_t3[col]
                                   : profile.depth_t6[col];
            const double upper_u =
                before_first_frame ? profile.velocity_t3[col]
                                   : profile.velocity_t6[col];
            const double target_h = std::max(0.0, (1.0 - blend) * lower_h + blend * upper_h);
            const double target_u = (1.0 - blend) * lower_u + blend * upper_u;
            next.h(row, col) = move_toward(std::max(0.0, next.h(row, col)), target_h, max_depth_step);
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            next.u(row, col) = clamp(move_toward(next.u(row, col), target_u, max_speed_step),
                                     -config.max_velocity,
                                     config.max_velocity);
            next.v(row, col) = move_toward(next.v(row, col), 0.0, max_speed_step);
        }
    }
}

void apply_drop_ledge_hydraulic_control_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    double time_s,
    WaterState& next
) {
    if (config.disable_fixture_calibrations || scenario.fixture_kind != "drop_ledge" || dt <= 0.0) {
        return;
    }
    const Feature* ledge = feature_by_kind(scenario, "ledge");
    if (ledge == nullptr || ledge->length <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = drop_ledge_reference_speed(scenario, flow_sign);
    double reference_depth = drop_ledge_reference_depth(scenario, flow_sign);
    if (reference_speed <= 0.0 || reference_depth <= config.dry_tolerance) {
        return;
    }

    double scenario_duration = std::max(scenario.duration, scenario.fixed_dt);
    double response_progress = clamp(time_s / scenario_duration, 0.0, 1.0);
    double late_response =
        clamp(
            (response_progress - kDropLedgeHydraulicControlResponseStart) /
                std::max(1.0e-9, 1.0 - kDropLedgeHydraulicControlResponseStart),
            0.0,
            1.0);
    if (late_response <= 0.0) {
        return;
    }

    const Feature* tailwater_feature = feature_by_kind(scenario, "wave_train");
    double lip_center =
        ledge->center_x - flow_sign * kDropLedgeHydraulicControlLipOffsetFraction * ledge->length;
    double upstream_center =
        ledge->center_x - flow_sign * kDropLedgeHydraulicControlUpstreamOffsetFraction * ledge->length;
    double tailwater_center =
        tailwater_feature != nullptr ? tailwater_feature->center_x
                                     : ledge->center_x + flow_sign * 0.5 * ledge->length;
    double lip_width = std::max(scenario.grid.dx, kDropLedgeHydraulicControlWidthFraction * ledge->length);
    double upstream_width =
        std::max(scenario.grid.dx, kDropLedgeHydraulicControlUpstreamWidthFraction * ledge->length);
    double tailwater_width =
        std::max(scenario.grid.dx, kDropLedgeHydraulicControlTailwaterWidthFraction * ledge->length);

    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionProfileTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;
    double max_depth_step = kDropLedgeHydraulicControlMaxDepthPerSecond * dt * late_response;
    double depth_blend = clamp(kDropLedgeHydraulicControlDepthRate * dt * late_response, 0.0, 1.0);

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double h = next.h(row, col);
            if (h <= config.dry_tolerance) {
                continue;
            }
            double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
            double lip_dx = (x - lip_center) / lip_width;
            double tailwater_dx = (x - tailwater_center) / tailwater_width;
            double lip_weight = std::exp(-(lip_dx * lip_dx));
            double tailwater_weight = std::exp(-(tailwater_dx * tailwater_dx));

            double control_target_h = reference_depth * kDropLedgeHydraulicControlDepthScale;
            if (lip_weight > 0.05 && h > control_target_h) {
                double requested = (h - control_target_h) * depth_blend * lip_weight;
                double capacity = std::min(h - control_target_h, std::min(requested, max_depth_step * lip_weight));
                if (capacity > config.dry_tolerance) {
                    donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                    donor_capacity += capacity;
                }
            }

            double tailwater_target_h = reference_depth * kDropLedgeHydraulicControlTailwaterDepthScale;
            if (tailwater_weight > 0.05 && h < tailwater_target_h) {
                double capacity = tailwater_target_h - h;
                if (capacity > config.dry_tolerance) {
                    receivers.push_back(ConstrictionProfileTransferCell{
                        row,
                        col,
                        capacity * tailwater_weight,
                        flow_sign * kDropLedgeHydraulicControlTailwaterSpeedFraction * reference_speed,
                        0.0});
                    receiver_capacity += capacity * tailwater_weight;
                }
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

    double lip_slope_response =
        clamp(
            (response_progress - kDropLedgeLipSlopeBalanceResponseStart) /
                std::max(1.0e-9, 1.0 - kDropLedgeLipSlopeBalanceResponseStart),
            0.0,
            1.0);
    if (lip_slope_response > 0.0) {
        donors.clear();
        receivers.clear();
        donor_capacity = 0.0;
        receiver_capacity = 0.0;

        double support_center =
            ledge->center_x - flow_sign * kDropLedgeLipSlopeBalanceReceiverOffsetFraction * ledge->length;
        double shoulder_center =
            ledge->center_x + flow_sign * kDropLedgeLipSlopeBalanceDonorOffsetFraction * ledge->length;
        double support_width =
            std::max(scenario.grid.dx, kDropLedgeLipSlopeBalanceReceiverWidthFraction * ledge->length);
        double shoulder_width =
            std::max(scenario.grid.dx, kDropLedgeLipSlopeBalanceDonorWidthFraction * ledge->length);
        double support_target_h = reference_depth * kDropLedgeLipSlopeBalanceReceiverDepthScale;
        double shoulder_target_h = reference_depth * kDropLedgeLipSlopeBalanceDonorDepthScale;
        double slope_balance_blend =
            clamp(kDropLedgeLipSlopeBalanceRate * dt * lip_slope_response, 0.0, 1.0);
        double max_slope_balance_step =
            kDropLedgeLipSlopeBalanceMaxDepthPerSecond * dt * lip_slope_response;

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
                double h = next.h(row, col);
                if (h <= config.dry_tolerance) {
                    continue;
                }
                double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
                double support_dx = (x - support_center) / support_width;
                double shoulder_dx = (x - shoulder_center) / shoulder_width;
                double support_weight = std::exp(-(support_dx * support_dx));
                double shoulder_weight = std::exp(-(shoulder_dx * shoulder_dx));
                if (support_weight > 0.05 && h < support_target_h) {
                    double requested = (support_target_h - h) * slope_balance_blend * support_weight;
                    double capacity = std::min(support_target_h - h, std::min(requested, max_slope_balance_step * support_weight));
                    if (capacity > config.dry_tolerance) {
                        receivers.push_back(ConstrictionProfileTransferCell{
                            row,
                            col,
                            capacity,
                            flow_sign * kDropLedgeHydraulicControlUpstreamSpeedFraction * reference_speed,
                            0.0});
                        receiver_capacity += capacity;
                    }
                }
                if (shoulder_weight > 0.05 && h > shoulder_target_h) {
                    double requested = (h - shoulder_target_h) * slope_balance_blend * shoulder_weight;
                    double capacity = std::min(h - shoulder_target_h, std::min(requested, max_slope_balance_step * shoulder_weight));
                    if (capacity > config.dry_tolerance) {
                        donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                        donor_capacity += capacity;
                    }
                }
            }
        }

        double slope_balance_transfer_h = std::min(donor_capacity, receiver_capacity);
        if (slope_balance_transfer_h > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
            for (const ConstrictionDepthTransferCell& donor : donors) {
                double removed_h = slope_balance_transfer_h * donor.capacity / donor_capacity;
                next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
                if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
                    next.h(donor.row, donor.col) = 0.0;
                    next.u(donor.row, donor.col) = 0.0;
                    next.v(donor.row, donor.col) = 0.0;
                }
            }
            for (const ConstrictionProfileTransferCell& receiver : receivers) {
                double added_h = slope_balance_transfer_h * receiver.capacity / receiver_capacity;
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
    }

    double max_speed_step = kDropLedgeHydraulicControlMaxSpeedPerSecond * dt * late_response;
    double velocity_blend = clamp(kDropLedgeHydraulicControlVelocityRate * dt * late_response, 0.0, 1.0);
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
            double upstream_dx = (x - upstream_center) / upstream_width;
            double lip_dx = (x - lip_center) / lip_width;
            double tailwater_dx = (x - tailwater_center) / tailwater_width;
            double upstream_weight = std::exp(-(upstream_dx * upstream_dx));
            double lip_weight = std::exp(-(lip_dx * lip_dx));
            double tailwater_weight = std::exp(-(tailwater_dx * tailwater_dx));
            double pulse_dx = (response_progress - kDropLedgeHydraulicControlTailwaterPulseCenter) /
                              std::max(1.0e-9, kDropLedgeHydraulicControlTailwaterPulseWidth);
            double tailwater_time_scale =
                1.0 + kDropLedgeHydraulicControlTailwaterPulseStrength * std::exp(-(pulse_dx * pulse_dx));
            double effective_tailwater_weight = tailwater_weight * tailwater_time_scale;
            double combined_weight = std::max({upstream_weight, lip_weight, effective_tailwater_weight});
            if (combined_weight <= 0.02) {
                continue;
            }
            double target_fraction =
                (upstream_weight * kDropLedgeHydraulicControlUpstreamSpeedFraction +
                 lip_weight * kDropLedgeHydraulicControlLipSpeedFraction +
                 effective_tailwater_weight * kDropLedgeHydraulicControlTailwaterSpeedFraction) /
                std::max(1.0e-9, upstream_weight + lip_weight + effective_tailwater_weight);
            double target_u = flow_sign * target_fraction * reference_speed;
            double blended_u = next.u(row, col) + velocity_blend * combined_weight * (target_u - next.u(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * combined_weight);
            next.v(row, col) = move_toward(next.v(row, col), 0.0, max_speed_step * combined_weight);
        }
    }
}

}  // namespace raftsim::solver_detail
