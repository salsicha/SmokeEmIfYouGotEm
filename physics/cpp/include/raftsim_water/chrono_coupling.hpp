#pragma once

#include "raftsim_water/solver.hpp"

namespace raftsim {

struct Vec3d {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct ChronoCouplingConfig {
    double water_density = 1000.0;
    double gravity = 9.81;
    double contact_stiffness = 12000.0;
    double contact_damping = 1200.0;
};

struct WaterFieldSample {
    double x = 0.0;
    double y = 0.0;
    double surface_height = 0.0;
    double bed_height = 0.0;
    double depth = 0.0;
    Vec3d velocity;
    Vec3d normal{0.0, 0.0, 1.0};
    bool wet = false;
};

struct ChronoRaftPatch {
    Vec3d world_position;
    Vec3d world_velocity;
    double area = 1.0;
};

struct ChronoForceSample {
    Vec3d force;
    Vec3d application_point;
    double submerged_depth = 0.0;
    double bed_penetration = 0.0;
    bool wet = false;
    bool grounded = false;
};

WaterFieldSample sample_water_field(const Scenario& scenario, const Frame& frame, double x, double y);
ChronoForceSample sample_chrono_raft_patch(
    const Scenario& scenario,
    const Frame& frame,
    const ChronoRaftPatch& patch,
    const ChronoCouplingConfig& config = {}
);

}  // namespace raftsim
