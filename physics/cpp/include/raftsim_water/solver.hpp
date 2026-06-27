#pragma once

#include <string>
#include <vector>

#include "raftsim_water/scenario.hpp"

namespace raftsim {

struct DerivedFields {
    Array2D normal_x;
    Array2D normal_y;
    Array2D normal_z;
    Array2D froude;
};

struct SolverConfig {
    std::string solver_mode = "reduced";
    std::string boundary_mode = "scenario";
    std::string flux_scheme = "rusanov";
    double gravity = 9.81;
    double dry_tolerance = 1.0e-6;
    double max_velocity = 60.0;
    double cfl = 0.45;
    double feature_strength_scale = 1.0;
    double roughness_scale = 1.0;
    double bed_slope_source_scale = 0.0;
};

struct Frame {
    double time = 0.0;
    WaterState state;
    DerivedFields derived;
};

struct ValidationSummary {
    double mass_initial = 0.0;
    double mass_final = 0.0;
    double mass_relative_drift = 0.0;
    double max_velocity = 0.0;
    double min_depth = 0.0;
    bool passed = false;
};

class ReducedShallowWaterSolver {
public:
    explicit ReducedShallowWaterSolver(Scenario scenario, SolverConfig config = {});

    const Scenario& scenario() const { return scenario_; }
    const WaterState& state() const { return state_; }
    double time() const { return time_; }

    Frame make_frame() const;
    void step(double dt);
    std::vector<Frame> run(int steps, int frame_interval);

private:
    Scenario scenario_;
    SolverConfig config_;
    WaterState state_;
    double time_ = 0.0;

    void apply_boundaries();
    void step_reduced(double dt);
    void step_finite_volume(double dt);
    void step_finite_volume_once(double dt);
    double finite_volume_stable_dt() const;
    void apply_feature_forcing(double dt, WaterState& next) const;
    void recompute_state(WaterState& next) const;
};

DerivedFields compute_derived_fields(const Scenario& scenario, const WaterState& state, const SolverConfig& config);
double compute_mass(const Scenario& scenario, const WaterState& state);
ValidationSummary validate_frames(const Scenario& scenario, const std::vector<Frame>& frames, const SolverConfig& config);

void write_solver_output(
    const Scenario& scenario,
    const std::vector<Frame>& frames,
    const ValidationSummary& validation,
    const SolverConfig& config,
    const std::string& output_dir
);

}  // namespace raftsim
