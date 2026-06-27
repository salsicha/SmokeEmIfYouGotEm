#include "raftsim_water/chrono_coupling.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace raftsim {

namespace {

double clamp(double value, double lo, double hi) {
    return std::max(lo, std::min(hi, value));
}

std::size_t nearest_col(const Scenario& scenario, double x) {
    double fx = (x - scenario.grid.origin_x) / scenario.grid.dx;
    return static_cast<std::size_t>(clamp(std::round(fx), 0.0, static_cast<double>(scenario.grid.nx - 1)));
}

std::size_t nearest_row(const Scenario& scenario, double y) {
    double fy = (y - scenario.grid.origin_y) / scenario.grid.dy;
    return static_cast<std::size_t>(clamp(std::round(fy), 0.0, static_cast<double>(scenario.grid.ny - 1)));
}

Vec3d operator*(const Vec3d& vector, double scalar) {
    return Vec3d{vector.x * scalar, vector.y * scalar, vector.z * scalar};
}

Vec3d operator+(const Vec3d& left, const Vec3d& right) {
    return Vec3d{left.x + right.x, left.y + right.y, left.z + right.z};
}

}  // namespace

WaterFieldSample sample_water_field(const Scenario& scenario, const Frame& frame, double x, double y) {
    if (scenario.grid.nx == 0 || scenario.grid.ny == 0) {
        throw std::runtime_error("Cannot sample an empty water grid.");
    }
    std::size_t row = nearest_row(scenario, y);
    std::size_t col = nearest_col(scenario, x);
    return WaterFieldSample{
        x,
        y,
        frame.state.eta(row, col),
        scenario.bed(row, col),
        frame.state.h(row, col),
        Vec3d{frame.state.u(row, col), frame.state.v(row, col), 0.0},
        Vec3d{frame.derived.normal_x(row, col), frame.derived.normal_y(row, col), frame.derived.normal_z(row, col)},
        frame.state.wet(row, col),
    };
}

ChronoForceSample sample_chrono_raft_patch(
    const Scenario& scenario,
    const Frame& frame,
    const ChronoRaftPatch& patch,
    const ChronoCouplingConfig& config
) {
    if (patch.area <= 0.0) {
        throw std::runtime_error("Chrono raft patch area must be positive.");
    }
    WaterFieldSample water = sample_water_field(scenario, frame, patch.world_position.x, patch.world_position.y);
    double submerged_depth = water.surface_height - patch.world_position.z;
    double bed_penetration = water.bed_height - patch.world_position.z;
    Vec3d force{};
    bool wet = water.wet && submerged_depth > 0.0;
    if (wet) {
        double magnitude = config.water_density * config.gravity * patch.area * submerged_depth;
        force = force + water.normal * magnitude;
    }
    bool grounded = bed_penetration > 0.0;
    if (grounded) {
        double normal_speed = std::min(patch.world_velocity.z, 0.0);
        double normal_force = config.contact_stiffness * bed_penetration - config.contact_damping * normal_speed;
        force = force + Vec3d{0.0, 0.0, normal_force};
    }
    return ChronoForceSample{
        force,
        patch.world_position,
        std::max(0.0, submerged_depth),
        std::max(0.0, bed_penetration),
        wet,
        grounded,
    };
}

}  // namespace raftsim
