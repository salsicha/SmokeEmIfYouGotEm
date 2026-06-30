#include "raftsim_water/solver.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace raftsim {

namespace fs = std::filesystem;

namespace {

constexpr double kPi = 3.14159265358979323846;

double clamp(double value, double lo, double hi) {
    return std::max(lo, std::min(hi, value));
}

std::size_t idx(const Scenario& scenario, std::size_t row, std::size_t col) {
    return row * scenario.grid.nx + col;
}

double safe_depth(double h, double dry_tolerance) {
    return std::max(h, dry_tolerance);
}

struct ConservedState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

struct FluxState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

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

std::string json_escape(const std::string& value) {
    std::string escaped;
    for (char c : value) {
        if (c == '"' || c == '\\') {
            escaped.push_back('\\');
        }
        escaped.push_back(c);
    }
    return escaped;
}

void write_frame_csv(const Scenario& scenario, const Frame& frame, const fs::path& path) {
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Could not write frame CSV: " + path.string());
    }
    out << "row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude\n";
    out << std::setprecision(17);
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
            double y = scenario.grid.origin_y + static_cast<double>(row) * scenario.grid.dy;
            out << row << ',' << col << ',' << x << ',' << y << ','
                << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
                << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
                << frame.state.hu(row, col) << ',' << frame.state.hv(row, col) << ','
                << (frame.state.wet(row, col) ? 1 : 0) << ','
                << frame.derived.normal_x(row, col) << ',' << frame.derived.normal_y(row, col) << ','
                << frame.derived.normal_z(row, col) << ',' << frame.derived.froude(row, col) << '\n';
        }
    }
}

void write_probe_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path) {
    std::ofstream out(path);
    out << "time,h,eta,u,v,hu,hv,wet,froude\n";
    out << std::setprecision(17);
    std::size_t index = grid_index_for_position(scenario, probe.x, probe.y);
    std::size_t row = row_from_index(scenario, index);
    std::size_t col = col_from_index(scenario, index);
    for (const Frame& frame : frames) {
        out << frame.time << ','
            << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
            << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
            << frame.state.hu(row, col) << ',' << frame.state.hv(row, col) << ','
            << (frame.state.wet(row, col) ? 1 : 0) << ','
            << frame.derived.froude(row, col) << '\n';
    }
}

void write_cross_section_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path) {
    std::ofstream out(path);
    out << "time,distance,h,eta,u,v,froude\n";
    out << std::setprecision(17);
    double nx = probe.normal_x;
    double ny = probe.normal_y;
    double nlen = std::hypot(nx, ny);
    if (nlen <= 1.0e-12) {
        nx = 0.0;
        ny = 1.0;
        nlen = 1.0;
    }
    nx /= nlen;
    ny /= nlen;
    double length = probe.length > 0.0 ? probe.length : (scenario.grid.ny - 1) * scenario.grid.dy;
    int samples = std::max(2, static_cast<int>(length / std::min(scenario.grid.dx, scenario.grid.dy)) + 1);
    for (const Frame& frame : frames) {
        for (int i = 0; i < samples; ++i) {
            double t = samples == 1 ? 0.0 : static_cast<double>(i) / static_cast<double>(samples - 1);
            double distance = -0.5 * length + t * length;
            double x = probe.x + nx * distance;
            double y = probe.y + ny * distance;
            std::size_t index = grid_index_for_position(scenario, x, y);
            std::size_t row = row_from_index(scenario, index);
            std::size_t col = col_from_index(scenario, index);
            out << frame.time << ',' << distance << ','
                << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
                << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
                << frame.derived.froude(row, col) << '\n';
        }
    }
}

}  // namespace

ReducedShallowWaterSolver::ReducedShallowWaterSolver(Scenario scenario, SolverConfig config)
    : scenario_(std::move(scenario)),
      config_(config),
      state_(scenario_.initial),
      initial_mass_(compute_mass(scenario_, scenario_.initial)) {
    recompute_state(state_);
}

Frame ReducedShallowWaterSolver::make_frame() const {
    return Frame{time_, state_, compute_derived_fields(scenario_, state_, config_)};
}

void ReducedShallowWaterSolver::step(double dt) {
    if (config_.solver_mode == "finite_volume") {
        step_finite_volume(dt);
        return;
    }
    step_reduced(dt);
}

void ReducedShallowWaterSolver::step_reduced(double dt) {
    apply_boundaries();
    WaterState next = state_;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = state_.h(row, col);
            if (h <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            double div = divergence_x(state_.hu, scenario_, row, col) + divergence_y(state_.hv, scenario_, row, col);
            double h_next = std::max(0.0, h - dt * div);
            double sx = pressure_eta_x(state_, scenario_, config_, row, col);
            double sy = pressure_eta_y(state_, scenario_, config_, row, col);
            double u_next = state_.u(row, col) - dt * config_.gravity * sx;
            double v_next = state_.v(row, col) - dt * config_.gravity * sy;
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    recompute_state(next);
    state_ = std::move(next);
    apply_boundaries();
    apply_initial_mass_correction(state_);
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume(double dt) {
    double stable_dt = finite_volume_stable_dt();
    int substeps = std::max(1, static_cast<int>(std::ceil(dt / std::max(stable_dt, 1.0e-9))));
    double sub_dt = dt / static_cast<double>(substeps);
    for (int i = 0; i < substeps; ++i) {
        step_finite_volume_once(sub_dt);
    }
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume_once(double dt) {
    WaterState next = state_;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState center = conserved_from_cell(scenario_, state_, config_, row, col);
            ConservedState west = col > 0 ? conserved_from_cell(scenario_, state_, config_, row, col - 1)
                                          : boundary_conserved(scenario_, state_, config_, row, col, "west");
            ConservedState east = col + 1 < scenario_.grid.nx ? conserved_from_cell(scenario_, state_, config_, row, col + 1)
                                                              : boundary_conserved(scenario_, state_, config_, row, col, "east");
            ConservedState south = row > 0 ? conserved_from_cell(scenario_, state_, config_, row - 1, col)
                                           : boundary_conserved(scenario_, state_, config_, row, col, "south");
            ConservedState north = row + 1 < scenario_.grid.ny ? conserved_from_cell(scenario_, state_, config_, row + 1, col)
                                                               : boundary_conserved(scenario_, state_, config_, row, col, "north");

            FluxState flux_w = finite_volume_flux_x(west, center, config_);
            FluxState flux_e = finite_volume_flux_x(center, east, config_);
            FluxState flux_s = finite_volume_flux_y(south, center, config_);
            FluxState flux_n = finite_volume_flux_y(center, north, config_);

            double h_next = center.h - dt * ((flux_e.h - flux_w.h) / scenario_.grid.dx + (flux_n.h - flux_s.h) / scenario_.grid.dy);
            double hu_next = center.hu - dt * ((flux_e.hu - flux_w.hu) / scenario_.grid.dx + (flux_n.hu - flux_s.hu) / scenario_.grid.dy);
            double hv_next = center.hv - dt * ((flux_e.hv - flux_w.hv) / scenario_.grid.dx + (flux_n.hv - flux_s.hv) / scenario_.grid.dy);

            if (config_.bed_slope_source_scale != 0.0 && center.h > config_.dry_tolerance) {
                double bed_sx = gradient_x(scenario_.bed, scenario_, row, col);
                double bed_sy = gradient_y(scenario_.bed, scenario_, row, col);
                hu_next -= dt * config_.bed_slope_source_scale * config_.gravity * center.h * bed_sx;
                hv_next -= dt * config_.bed_slope_source_scale * config_.gravity * center.h * bed_sy;
            }

            h_next = std::max(0.0, h_next);
            if (h_next <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }

            double u_next = hu_next / safe_depth(h_next, config_.dry_tolerance);
            double v_next = hv_next / safe_depth(h_next, config_.dry_tolerance);
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h_next, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    recompute_state(next);
    state_ = std::move(next);
}

double ReducedShallowWaterSolver::finite_volume_stable_dt() const {
    double max_speed = 0.0;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState q = conserved_from_cell(scenario_, state_, config_, row, col);
            max_speed = std::max(max_speed, wave_speed_x(q, config_));
            max_speed = std::max(max_speed, wave_speed_y(q, config_));
        }
    }
    if (max_speed <= 1.0e-9) {
        return scenario_.fixed_dt;
    }
    double spacing = std::min(scenario_.grid.dx, scenario_.grid.dy);
    return clamp(config_.cfl, 0.05, 0.95) * spacing / max_speed;
}

std::vector<Frame> ReducedShallowWaterSolver::run(int steps, int frame_interval) {
    if (steps < 0) {
        throw std::runtime_error("steps must be non-negative.");
    }
    frame_interval = std::max(1, frame_interval);
    std::vector<Frame> frames;
    frames.push_back(make_frame());
    for (int step_index = 1; step_index <= steps; ++step_index) {
        step(scenario_.fixed_dt);
        if (step_index % frame_interval == 0 || step_index == steps) {
            frames.push_back(make_frame());
        }
    }
    return frames;
}

void ReducedShallowWaterSolver::apply_boundaries() {
    for (const BoundaryCondition& boundary : scenario_.boundaries) {
        if (boundary.edge == "west") {
            std::size_t col = 0;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.kind == "inflow" && boundary.has_depth) {
                    state_.h(row, col) = boundary.depth;
                    if (boundary.has_velocity) {
                        state_.u(row, col) = boundary.velocity_x;
                        state_.v(row, col) = boundary.velocity_y;
                    }
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col + 1);
                    state_.u(row, col) = state_.u(row, col + 1);
                    state_.v(row, col) = state_.v(row, col + 1);
                }
            }
        } else if (boundary.edge == "east") {
            std::size_t col = scenario_.grid.nx - 1;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col - 1);
                    state_.u(row, col) = state_.u(row, col - 1);
                    state_.v(row, col) = state_.v(row, col - 1);
                }
            }
        } else if (boundary.edge == "south") {
            std::size_t row = 0;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row + 1, col);
                    state_.u(row, col) = state_.u(row + 1, col);
                    state_.v(row, col) = state_.v(row + 1, col);
                }
            }
        } else if (boundary.edge == "north") {
            std::size_t row = scenario_.grid.ny - 1;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row - 1, col);
                    state_.u(row, col) = state_.u(row - 1, col);
                    state_.v(row, col) = state_.v(row - 1, col);
                }
            }
        }
    }
    recompute_state(state_);
}

void ReducedShallowWaterSolver::apply_initial_mass_correction(WaterState& next) const {
    if (!config_.preserve_initial_mass || initial_mass_ <= 1.0e-9) {
        return;
    }
    double current_mass = compute_mass(scenario_, next);
    if (current_mass <= 1.0e-9) {
        return;
    }
    double scale = initial_mass_ / current_mass;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            if (next.h(row, col) <= config_.dry_tolerance) {
                continue;
            }
            next.h(row, col) *= scale;
        }
    }
    recompute_state(next);
}

void ReducedShallowWaterSolver::apply_feature_forcing(double dt, WaterState& next) const {
    for (const Feature& feature : scenario_.features) {
        double scale_x = std::max({feature.length * 0.5, feature.radius, scenario_.grid.dx});
        double scale_y = std::max({feature.width * 0.5, feature.radius, scenario_.grid.dy});
        for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
            double y = scenario_.grid.origin_y + static_cast<double>(row) * scenario_.grid.dy;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                double x = scenario_.grid.origin_x + static_cast<double>(col) * scenario_.grid.dx;
                double dx = (x - feature.center_x) / scale_x;
                double dy = (y - feature.center_y) / scale_y;
                double influence = std::exp(-(dx * dx + dy * dy)) * feature.strength * config_.feature_strength_scale;
                if (influence < 1.0e-6 || next.h(row, col) <= config_.dry_tolerance) {
                    continue;
                }
                if (feature.kind == "hole") {
                    next.u(row, col) -= dt * 2.0 * influence;
                    next.h(row, col) += dt * 0.08 * influence;
                } else if (feature.kind == "lateral") {
                    double side = feature.center_y >= 0.0 ? -1.0 : 1.0;
                    next.v(row, col) += dt * side * 2.4 * influence;
                } else if (feature.kind == "boil") {
                    next.u(row, col) += dt * dx * 1.4 * influence;
                    next.v(row, col) += dt * dy * 1.4 * influence;
                    next.h(row, col) += dt * 0.04 * influence;
                } else if (feature.kind == "wave_train") {
                    next.h(row, col) += dt * 0.05 * std::sin((x - feature.center_x) * kPi / std::max(scale_x, 1.0e-6)) * influence;
                } else if (feature.kind == "ledge") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.05 * influence);
                    next.u(row, col) += dt * 0.8 * influence;
                } else if (feature.kind == "shallow") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.06 * influence);
                    next.u(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                    next.v(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                }
            }
        }
    }
}

void ReducedShallowWaterSolver::recompute_state(WaterState& next) const {
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = std::max(0.0, next.h(row, col));
            next.h(row, col) = h;
            bool wet = h > config_.dry_tolerance;
            next.wet.values[idx(scenario_, row, col)] = wet ? 1 : 0;
            if (!wet) {
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
            next.eta(row, col) = scenario_.bed(row, col) + h;
            next.hu(row, col) = h * next.u(row, col);
            next.hv(row, col) = h * next.v(row, col);
        }
    }
}

DerivedFields compute_derived_fields(const Scenario& scenario, const WaterState& state, const SolverConfig& config) {
    DerivedFields fields{
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
    };
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double sx = gradient_x(state.eta, scenario, row, col);
            double sy = gradient_y(state.eta, scenario, row, col);
            double len = std::sqrt(sx * sx + sy * sy + 1.0);
            fields.normal_x(row, col) = -sx / len;
            fields.normal_y(row, col) = -sy / len;
            fields.normal_z(row, col) = 1.0 / len;
            double speed = std::hypot(state.u(row, col), state.v(row, col));
            fields.froude(row, col) = state.wet(row, col) ? speed / std::sqrt(std::max(config.gravity * state.h(row, col), config.dry_tolerance)) : 0.0;
        }
    }
    return fields;
}

double compute_mass(const Scenario& scenario, const WaterState& state) {
    double sum = 0.0;
    for (double h : state.h.values()) {
        sum += h;
    }
    return sum * scenario.grid.dx * scenario.grid.dy;
}

ValidationSummary validate_frames(const Scenario& scenario, const std::vector<Frame>& frames, const SolverConfig&) {
    if (frames.empty()) {
        return {};
    }
    ValidationSummary summary;
    summary.mass_initial = compute_mass(scenario, frames.front().state);
    summary.mass_final = compute_mass(scenario, frames.back().state);
    summary.mass_relative_drift = std::abs(summary.mass_final - summary.mass_initial) / std::max(std::abs(summary.mass_initial), 1.0);
    summary.min_depth = frames.front().state.h.min();
    for (const Frame& frame : frames) {
        summary.min_depth = std::min(summary.min_depth, frame.state.h.min());
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
                summary.max_velocity = std::max(summary.max_velocity, std::hypot(frame.state.u(row, col), frame.state.v(row, col)));
            }
        }
    }
    summary.passed = summary.min_depth >= -1.0e-9 && summary.max_velocity <= 100.0 && summary.mass_relative_drift <= 0.50;
    return summary;
}

void write_solver_output(
    const Scenario& scenario,
    const std::vector<Frame>& frames,
    const ValidationSummary& validation,
    const SolverConfig& config,
    const std::string& output_dir
) {
    fs::path root(output_dir);
    fs::create_directories(root / "frames");
    fs::create_directories(root / "probes");
    fs::create_directories(root / "cross_sections");

    std::vector<std::string> frame_files;
    for (std::size_t i = 0; i < frames.size(); ++i) {
        std::ostringstream name;
        name << "frames/frame_" << std::setw(4) << std::setfill('0') << i << ".csv";
        write_frame_csv(scenario, frames[i], root / name.str());
        frame_files.push_back(name.str());
    }

    std::vector<std::string> probe_files;
    std::vector<std::string> cross_section_files;
    for (const Probe& probe : scenario.probes) {
        if (probe.kind == "cross_section") {
            std::string relative = "cross_sections/" + probe.id + ".csv";
            write_cross_section_csv(scenario, frames, probe, root / relative);
            cross_section_files.push_back(relative);
        } else {
            std::string relative = "probes/" + probe.id + ".csv";
            write_probe_csv(scenario, frames, probe, root / relative);
            probe_files.push_back(relative);
        }
    }

    {
        std::ofstream out(root / "validation.json");
        out << std::setprecision(17)
            << "{\n"
            << "  \"passed\": " << (validation.passed ? "true" : "false") << ",\n"
            << "  \"mass_initial\": " << validation.mass_initial << ",\n"
            << "  \"mass_final\": " << validation.mass_final << ",\n"
            << "  \"mass_relative_drift\": " << validation.mass_relative_drift << ",\n"
            << "  \"max_velocity\": " << validation.max_velocity << ",\n"
            << "  \"min_depth\": " << validation.min_depth << "\n"
            << "}\n";
    }

    std::ofstream manifest(root / "manifest.json");
    manifest << "{\n"
             << "  \"scenario_id\": \"" << json_escape(scenario.scenario_id) << "\",\n"
             << "  \"solver\": \"raftsim_water_cpp_v1\",\n"
             << "  \"solver_mode\": \"" << json_escape(config.solver_mode) << "\",\n"
             << "  \"boundary_mode\": \"" << json_escape(config.boundary_mode) << "\",\n"
             << "  \"flux_scheme\": \"" << json_escape(config.flux_scheme) << "\",\n"
             << "  \"cfl\": " << config.cfl << ",\n"
             << "  \"dry_tolerance\": " << config.dry_tolerance << ",\n"
             << "  \"feature_strength_scale\": " << config.feature_strength_scale << ",\n"
             << "  \"roughness_scale\": " << config.roughness_scale << ",\n"
             << "  \"bed_slope_source_scale\": " << config.bed_slope_source_scale << ",\n"
             << "  \"preserve_initial_mass\": " << (config.preserve_initial_mass ? "true" : "false") << ",\n"
             << "  \"cascading\": {\n"
             << "    \"present\": " << (scenario.cascading.present ? "true" : "false") << ",\n"
             << "    \"schema_version\": \"" << json_escape(scenario.cascading.schema_version) << "\",\n"
             << "    \"reach_count\": " << scenario.cascading.reaches.size() << ",\n"
             << "    \"drop_transition_count\": " << scenario.cascading.drop_transitions.size() << "\n"
             << "  },\n"
             << "  \"validation\": \"validation.json\",\n"
             << "  \"frames\": [";
    for (std::size_t i = 0; i < frame_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << frame_files[i] << "\"";
    }
    manifest << "],\n  \"probes\": [";
    for (std::size_t i = 0; i < probe_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << probe_files[i] << "\"";
    }
    manifest << "],\n  \"cross_sections\": [";
    for (std::size_t i = 0; i < cross_section_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << cross_section_files[i] << "\"";
    }
    manifest << "]\n}\n";
}

}  // namespace raftsim
