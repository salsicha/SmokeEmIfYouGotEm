#pragma once

#include <string>
#include <vector>

#include "raftsim_water/scenario.hpp"

namespace raftsim {

// Call during host module shutdown, before DLL unloading/Windows loader lock.
// Waits for in-flight row work and joins the bounded persistent workers.
void shutdown_solver_workers();
// Optional one-shot process setting, before the first worker-pool use.
// Default remains four total execution lanes (caller included), bounded by
// hardware concurrency. Offline cooks may explicitly request 1..64 lanes.
// Late/repeated configuration is rejected; no in-flight pool is resized.
void configure_solver_workers(unsigned maximum_lanes);

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
    // Offline opt-in: constant west-edge discharge, negative disables it.
    // Requires a wet, subcritical west inflow and uncalibrated MUSCL. The supplied
    // inlet stage defines a fixed wet footprint only; evolving stage is free.
    // Do not infer this setting from informational metadata.
    double experimental_west_discharge_m3s = -1.0;
    // Explicit offline mixed-regime closure: where both characteristics enter,
    // use the supplied external stage as the second boundary condition.
    // Subcritical faces still determine stage from the outgoing characteristic.
    bool experimental_west_supercritical_stage = false;
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
    bool finite_state = true;
    bool velocity_limit_reached = false;
    bool passed = false;
};

// Instantaneous domain-face volume fluxes (m^3/s), positive into the domain.
// These are numerical fluxes, not h*u sampled at boundary cell centers.
struct BoundaryMassFluxes {
    double west = 0.0;
    double east = 0.0;
    double south = 0.0;
    double north = 0.0;
};

// Exact MUSCL mass flux density (m^2/s), positive along the grid's +x/+y.
// x_faces is ny by (nx+1); y_faces is (ny+1) by nx. Integrating the enclosing
// faces gives the instantaneous volume derivative of any grid-aligned window.
struct NumericalMassFluxGrid {
    Array2D x_faces;
    Array2D y_faces;
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
    // Explicit offline diagnostic; never called by normal stepping. Only the
    // uncalibrated second-order finite-volume path is supported. State is unchanged.
    BoundaryMassFluxes inspect_boundary_mass_fluxes() const;
    NumericalMassFluxGrid inspect_numerical_mass_flux_grid() const;

    /**
     * Replace the live state without recreating the solver.  Moving gameplay
     * windows use this to preserve overlapping water and simulation time
     * during a handoff.  The replacement must match the scenario grid and be
     * finite; derived state is recomputed before it becomes authoritative.
     */
    void replace_state(WaterState state, double time);

private:
    friend class CartesianWaterDomain;
    Scenario scenario_;
    SolverConfig config_;
    WaterState state_;
    // Per-instance RK scratch, allocated lazily. Stages read only h/u/v;
    // derived fields are rebuilt once after the final combination. These are
    // never authoritative and are fully overwritten after replace_state().
    WaterState muscl_predictor_;
    WaterState muscl_corrector_;
    WaterState muscl_next_;
    double time_ = 0.0;
    double initial_mass_ = 0.0;

    void apply_boundaries();
    void apply_initial_mass_correction(WaterState& next) const;
    void step_reduced(double dt);
    void step_finite_volume(double dt);
    void step_finite_volume_once(double dt);
    bool finite_volume_second_order_enabled() const;
    void step_finite_volume_once_second_order(double dt);
    void finish_finite_volume_second_order_step(double dt);
    void finite_volume_second_order_flux_update(const WaterState& from, double dt, WaterState& to,
        BoundaryMassFluxes* boundary_fluxes = nullptr,
        NumericalMassFluxGrid* face_fluxes = nullptr) const;
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
