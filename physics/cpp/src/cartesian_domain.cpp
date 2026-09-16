#include "raftsim_water/cartesian_domain.hpp"
#include "solver_row_executor.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <stdexcept>

namespace raftsim {
namespace {
constexpr const char* edges[] = {"west","east","south","north"};
constexpr int delta_x[] = {-1,1,0,0};
constexpr int delta_y[] = {0,0,-1,1};

BoundaryCondition& boundary(Scenario& scenario, int edge) {
    for (auto& item : scenario.boundaries) if (item.edge == edges[edge]) return item;
    throw std::runtime_error("Cartesian tile requires all four explicit physical boundaries.");
}

void fill_edge(Scenario& target, int edge, const Scenario& neighbor, const WaterState& state) {
    auto& cells = boundary(target,edge).ghost_cells;
    const std::size_t n = edge < 2 ? target.grid.ny : target.grid.nx;
    for (std::size_t layer = 0; layer < 2; ++layer) {
        for (std::size_t i = 0; i < n; ++i) {
            const std::size_t row = edge < 2 ? i : (edge == 2 ? neighbor.grid.ny-1-layer : layer);
            const std::size_t col = edge >= 2 ? i : (edge == 0 ? neighbor.grid.nx-1-layer : layer);
            cells[layer*n+i] = {neighbor.bed(row,col),state.h(row,col),state.u(row,col),state.v(row,col)};
        }
    }
}
}

CartesianWaterDomain::CartesianWaterDomain(std::vector<Scenario> scenarios, SolverConfig config)
    : CartesianWaterDomain(std::move(scenarios),config,0.) {}

CartesianWaterDomain::CartesianWaterDomain(std::vector<Scenario> scenarios, SolverConfig config, double initial_time) {
    if (!std::isfinite(initial_time) || initial_time < 0.)
        throw std::runtime_error("Cartesian checkpoint time must be finite and non-negative.");
    if (scenarios.empty() || config.solver_mode != "finite_volume" || config.spatial_order != 2 ||
        !config.disable_fixture_calibrations || config.boundary_mode != "scenario" ||
        config.feature_strength_scale != 0. || config.preserve_initial_mass ||
        config.experimental_west_discharge_m3s >= 0.)
        throw std::runtime_error("Cartesian coupling requires nonempty uncalibrated MUSCL tiles, no mass correction or fixture/discharge override.");
    const GridSpec reference = scenarios.front().grid;
    if (reference.nx < 2 || reference.ny < 2 || !std::isfinite(reference.dx) ||
        !std::isfinite(reference.dy) || reference.dx <= 0. || reference.dy <= 0.)
        throw std::runtime_error("Invalid Cartesian tile grid.");
    using Key = std::pair<long long,long long>;
    std::map<Key,std::size_t> keys;
    std::vector<Key> tile_keys;
    for (std::size_t i = 0; i < scenarios.size(); ++i) {
        auto& scenario = scenarios[i];
        validate_scenario(scenario);
        const auto& grid = scenario.grid;
        const double x = (grid.origin_x-reference.origin_x)/(reference.nx*reference.dx);
        const double y = (grid.origin_y-reference.origin_y)/(reference.ny*reference.dy);
        if (grid.nx != reference.nx || grid.ny != reference.ny || grid.dx != reference.dx || grid.dy != reference.dy ||
            !std::isfinite(x) || !std::isfinite(y) || std::abs(x) > 1.e9 || std::abs(y) > 1.e9 ||
            std::abs(x-std::round(x)) > 1.e-8 || std::abs(y-std::round(y)) > 1.e-8)
            throw std::runtime_error("Cartesian tiles must be disjoint, equal-sized and on one lattice.");
        const Key key{std::llround(x),std::llround(y)};
        if (!keys.emplace(key,i).second) throw std::runtime_error("Duplicate Cartesian tile footprint.");
        tile_keys.push_back(key);
        if (scenario.boundaries.size() != 4) throw std::runtime_error("Cartesian tile requires four unique boundaries.");
        for (int edge = 0; edge < 4; ++edge) (void)boundary(scenario,edge);
        for (const Array2D* field : {&scenario.bed,&scenario.initial.h,&scenario.initial.u,&scenario.initial.v}) {
            if (field->nx() != grid.nx || field->ny() != grid.ny)
                throw std::runtime_error("Cartesian tile state/bed shape mismatch.");
            for (double value : field->values()) if (!std::isfinite(value))
                throw std::runtime_error("Cartesian tile contains nonfinite source state.");
        }
        if (scenario.initial.h.min() < 0.) throw std::runtime_error("Negative source depth in Cartesian tile.");
    }
    neighbors_.resize(scenarios.size());
    for (std::size_t i = 0; i < scenarios.size(); ++i) {
        neighbors_[i].fill(-1);
        for (int edge = 0; edge < 4; ++edge) {
            auto found = keys.find({tile_keys[i].first+delta_x[edge],tile_keys[i].second+delta_y[edge]});
            if (found == keys.end()) continue;
            neighbors_[i][edge] = static_cast<int>(found->second);
            auto& item = boundary(scenarios[i],edge);
            item = BoundaryCondition{};
            item.edge = edges[edge];
            item.kind = "ghost";
            item.ghost_cells.resize(2*(edge < 2 ? reference.ny : reference.nx));
            fill_edge(scenarios[i],edge,scenarios[found->second],scenarios[found->second].initial);
        }
    }
    tiles_.reserve(scenarios.size());
    for (auto& scenario : scenarios) {
        tiles_.push_back(std::make_unique<ReducedShallowWaterSolver>(std::move(scenario),config));
        tiles_.back()->time_ = initial_time;
    }
}

void CartesianWaterDomain::exchange_ghosts(bool predictor) {
    for (std::size_t i = 0; i < tiles_.size(); ++i) {
        for (int edge = 0; edge < 4; ++edge) {
            const int other = neighbors_[i][edge];
            if (other < 0) continue;
            const auto& neighbor = *tiles_[other];
            fill_edge(tiles_[i]->scenario_,edge,neighbor.scenario_,
                predictor ? neighbor.muscl_predictor_ : neighbor.state_);
        }
    }
}

void CartesianWaterDomain::step(double dt) { advance(dt,false); }
void CartesianWaterDomain::step_with_flux_audit(double dt) { advance(dt,true); }

void CartesianWaterDomain::advance(double dt, bool audit_fluxes) {
    if (!std::isfinite(dt) || dt <= 0.) throw std::runtime_error("Cartesian step must be finite and positive.");
    double stable_dt = std::numeric_limits<double>::max();
    // Every tile reads only its current immutable state. Reuse the existing
    // bounded executor/environment propagation, then retain the ORIGINAL
    // tile-order reduction (including std::min's unordered-value behavior).
    // The executor suppresses nested row dispatches on larger tile grids.
    std::vector<double> tile_stable_dt(tiles_.size());
    solver_detail::solver_row_ranges(tiles_.size(),tiles_.size() >= 16,
        [&](std::size_t first,std::size_t end) {
            for (std::size_t i=first;i<end;++i)
                tile_stable_dt[i]=tiles_[i]->finite_volume_stable_dt();
        });
    for (double value : tile_stable_dt) stable_dt=std::min(stable_dt,value);
    const double count = std::ceil(dt/stable_dt);
    if (!std::isfinite(stable_dt) || stable_dt <= 0. || !std::isfinite(count) || count > 4096.)
        throw std::runtime_error("Cartesian finite-volume CFL work limit exceeded.");
    const int substeps = std::max(1,static_cast<int>(count));
    const double sub_dt = dt/substeps;
    last_boundary_volume_change_ = 0.;
    std::vector<BoundaryMassFluxes> first_fluxes(audit_fluxes ? tiles_.size() : 0), second_fluxes(first_fluxes.size());
    for (auto& tile : tiles_) {
        for (WaterState* scratch : {&tile->muscl_predictor_,&tile->muscl_corrector_}) {
            if (scratch->h.empty()) {
                const auto& grid = tile->scenario_.grid;
                scratch->h = Array2D(grid.ny,grid.nx);
                scratch->u = Array2D(grid.ny,grid.nx);
                scratch->v = Array2D(grid.ny,grid.nx);
            }
        }
    }
    for (int step = 0; step < substeps; ++step) {
        if (audit_fluxes) {
            std::fill(first_fluxes.begin(),first_fluxes.end(),BoundaryMassFluxes{});
            std::fill(second_fluxes.begin(),second_fluxes.end(),BoundaryMassFluxes{});
        }
        exchange_ghosts(false);
        solver_detail::solver_row_ranges(tiles_.size(),tiles_.size() >= 4,[&](std::size_t first,std::size_t end) {
            for (std::size_t i = first; i < end; ++i)
                tiles_[i]->finite_volume_second_order_flux_update(tiles_[i]->state_,sub_dt,tiles_[i]->muscl_predictor_,
                    audit_fluxes ? &first_fluxes[i] : nullptr);
        });
        // Barrier above is essential: stage two must see EVERY neighbor's
        // predictor, not the previous time level or a partially advanced tile.
        exchange_ghosts(true);
        solver_detail::solver_row_ranges(tiles_.size(),tiles_.size() >= 4,[&](std::size_t first,std::size_t end) {
            for (std::size_t i = first; i < end; ++i)
                tiles_[i]->finite_volume_second_order_flux_update(tiles_[i]->muscl_predictor_,sub_dt,tiles_[i]->muscl_corrector_,
                    audit_fluxes ? &second_fluxes[i] : nullptr);
        });
        solver_detail::solver_row_ranges(tiles_.size(),tiles_.size() >= 4,[&](std::size_t first,std::size_t end) {
            for (std::size_t i = first; i < end; ++i) tiles_[i]->finish_finite_volume_second_order_step(sub_dt);
        });
        if (audit_fluxes) {
            for (std::size_t i=0;i<tiles_.size();++i) for (int edge=0;edge<4;++edge) {
                if (neighbors_[i][edge]>=0) continue;
                auto value=[edge](const BoundaryMassFluxes& flux) {
                    return edge==0 ? flux.west : edge==1 ? flux.east : edge==2 ? flux.south : flux.north;
                };
                last_boundary_volume_change_ += .5*sub_dt*(value(first_fluxes[i])+value(second_fluxes[i]));
            }
        }
    }
    for (auto& tile : tiles_) tile->time_ += dt;
    exchange_ghosts(false); // Public face diagnostics now inspect current state.
}

double CartesianWaterDomain::total_volume() const {
    double volume = 0.;
    for (const auto& tile : tiles_) volume += compute_mass(tile->scenario(),tile->state());
    return volume;
}
}
