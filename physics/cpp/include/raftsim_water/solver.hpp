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
    // Spatial accuracy of the finite-volume path: 2 selects MUSCL (piecewise-linear,
    // minmod-limited) reconstruction with well-balanced hydrostatic face states;
    // 1 selects the legacy first-order scheme. Reduced mode ignores this switch.
    int spatial_order = 2;
    double gravity = 9.81;
    double dry_tolerance = 1.0e-6;
    double max_velocity = 60.0;
    double cfl = 0.45;
    double feature_strength_scale = 1.0;
    double roughness_scale = 1.0;
    double bed_slope_source_scale = 0.0;
    bool preserve_initial_mass = true;
    bool disable_fixture_calibrations = false;
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

    /**
     * Replace the live state without recreating the solver.  Moving gameplay
     * windows use this to preserve overlapping water and simulation time
     * during a handoff.  The replacement must match the scenario grid and be
     * finite; derived state is recomputed before it becomes authoritative.
     */
    void replace_state(WaterState state, double time);

private:
    Scenario scenario_;
    SolverConfig config_;
    WaterState state_;
    double time_ = 0.0;
    double initial_mass_ = 0.0;

    void apply_boundaries();
    void apply_initial_mass_correction(WaterState& next) const;
    void step_reduced(double dt);
    void step_finite_volume(double dt);
    void step_finite_volume_once(double dt);
    bool finite_volume_second_order_enabled() const;
    void step_finite_volume_once_second_order(double dt);
    void finite_volume_second_order_flux_update(const WaterState& from, double dt, WaterState& to) const;
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
