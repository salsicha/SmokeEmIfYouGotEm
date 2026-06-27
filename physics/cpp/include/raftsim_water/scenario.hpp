#pragma once

#include <cstddef>
#include <string>
#include <vector>

#include "raftsim_water/array2d.hpp"
#include "raftsim_water/numpy_io.hpp"

namespace raftsim {

struct GridSpec {
    std::size_t nx = 0;
    std::size_t ny = 0;
    double dx = 1.0;
    double dy = 1.0;
    double origin_x = 0.0;
    double origin_y = 0.0;
};

struct BoundaryCondition {
    std::string edge;
    std::string kind;
    double stage = 0.0;
    double depth = 0.0;
    double velocity_x = 0.0;
    double velocity_y = 0.0;
    bool has_stage = false;
    bool has_depth = false;
    bool has_velocity = false;
};

struct Feature {
    std::string kind;
    double center_x = 0.0;
    double center_y = 0.0;
    double radius = 0.0;
    double strength = 1.0;
    double length = 0.0;
    double width = 0.0;
    double angle = 0.0;
};

struct Probe {
    std::string id;
    std::string kind;
    double x = 0.0;
    double y = 0.0;
    double normal_x = 0.0;
    double normal_y = 1.0;
    double length = 0.0;
};

struct WaterState {
    Array2D h;
    Array2D eta;
    Array2D u;
    Array2D v;
    Array2D hu;
    Array2D hv;
    BoolGrid wet;
};

struct Scenario {
    std::string scenario_id;
    std::string scenario_type;
    std::string fixture_kind;
    GridSpec grid;
    double fixed_dt = 1.0 / 60.0;
    double duration = 1.0;
    double roughness = 0.035;
    Array2D bed;
    WaterState initial;
    std::vector<BoundaryCondition> boundaries;
    std::vector<Feature> features;
    std::vector<Probe> probes;
};

Scenario load_scenario_package(const std::string& scenario_dir);
void validate_scenario(const Scenario& scenario);

std::size_t grid_index_for_position(const Scenario& scenario, double x, double y);
std::size_t row_from_index(const Scenario& scenario, std::size_t index);
std::size_t col_from_index(const Scenario& scenario, std::size_t index);

}  // namespace raftsim
