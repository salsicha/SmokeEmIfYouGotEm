#pragma once
#include <array>
#include <memory>
#include <vector>
#include "raftsim_water/solver.hpp"

namespace raftsim {

/** Disjoint equal-sized Cartesian tiles sharing the same finite-volume scheme.
 * Each RK stage exchanges two layers of actual neighbor cells before any tile
 * proceeds. Missing neighbors retain explicitly authored physical boundaries.
 * This is not an overlap blend or independent-window spinup.
 */
class CartesianWaterDomain {
public:
    CartesianWaterDomain(std::vector<Scenario> tiles, SolverConfig config);
    // Scenario initial arrays contain the checkpoint state; preserve its clock.
    CartesianWaterDomain(std::vector<Scenario> tiles, SolverConfig config, double initial_time);
    void step(double dt);
    void step_with_flux_audit(double dt);
    double last_boundary_volume_change() const { return last_boundary_volume_change_; }
    std::size_t size() const { return tiles_.size(); }
    const ReducedShallowWaterSolver& tile(std::size_t index) const { return *tiles_.at(index); }
    double time() const { return tiles_.front()->time(); }
    double total_volume() const;

private:
    void advance(double dt, bool audit_fluxes);
    void exchange_ghosts(bool predictor);
    double last_boundary_volume_change_ = 0.;
    std::vector<std::unique_ptr<ReducedShallowWaterSolver>> tiles_;
    std::vector<std::array<int,4>> neighbors_;
};
}
