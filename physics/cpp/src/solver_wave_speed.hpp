#pragma once

#include "solver_internal.hpp"
#include "solver_grid_view.hpp"
#include "solver_row_executor.hpp"

namespace raftsim::solver_detail {

// The CFL maximum is not a sum: regrouping the same nonnegative maxima does
// not reassociate floating-point arithmetic. Keep both wave-speed expressions,
// the dry-cell conversion, and std::max's handling of unordered samples exact.
// Each row starts at +0, just as the original complete scan does. A NaN speed
// never replaces that accumulator; +infinity still propagates to CFL rejection.
inline double maximum_wave_speed(const WaterState& state, const SolverConfig& config,
                                 std::size_t ny, std::size_t nx) {
    const ReadGridView h(state.h,ny,nx), u(state.u,ny,nx), v(state.v,ny,nx);
    std::vector<double> row_maximum(ny,0.0);
    solver_row_ranges(ny,nx*ny>=16384,[&](std::size_t first,std::size_t end) {
        for (std::size_t row=first;row<end;++row) {
            double speed=0.0;
            for (std::size_t col=0;col<nx;++col) {
                const double depth=std::max(0.0,h(row,col));
                const ConservedState q=depth<=config.dry_tolerance ? ConservedState{}
                    : ConservedState{depth,depth*u(row,col),depth*v(row,col)};
                speed=std::max(speed,wave_speed_x(q,config));
                speed=std::max(speed,wave_speed_y(q,config));
            }
            row_maximum[row]=speed;
        }
    });
    double maximum=0.0;
    for (double speed:row_maximum) maximum=std::max(maximum,speed);
    return maximum;
}

} // namespace raftsim::solver_detail
