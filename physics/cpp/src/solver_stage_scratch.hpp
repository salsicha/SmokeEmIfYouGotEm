#pragma once

#include "solver_internal.hpp"
#include <memory>

namespace raftsim::solver_detail {

// Capacity belongs to the calling thread, not to a physical solver state.
// Joined row workers borrow disjoint ranges only until the stage returns.
// A nested call gets independent storage; it must never invalidate the outer
// call's arrays. No class-layout/ABI change is required for solver instances.
struct SolverStageScratch {
    std::vector<MusclFaceState> primitives;
    std::vector<MusclHalfSlopes> slopes;
    bool leased = false;

    void prepare(std::size_t cells) {
        // Every primitive member is assigned by the reconstruction loop.
        primitives.resize(cells);
        // Dry cells and dry-neighbor directions skip slope assignment. Reset
        // ALL six slopes, including reused wet-to-dry cells, before any read.
        slopes.resize(cells);
        std::fill(slopes.begin(), slopes.end(), MusclHalfSlopes{});
    }
};

class SolverStageScratchLease {
    static SolverStageScratch& retained() {
        thread_local SolverStageScratch scratch;
        return scratch;
    }
    std::unique_ptr<SolverStageScratch> nested_;
    SolverStageScratch* storage_;
public:
    SolverStageScratchLease() : storage_(&retained()) {
        if (storage_->leased) {
            nested_ = std::make_unique<SolverStageScratch>();
            storage_ = nested_.get();
        }
        storage_->leased = true;
    }
    ~SolverStageScratchLease() { storage_->leased = false; }
    SolverStageScratchLease(const SolverStageScratchLease&) = delete;
    SolverStageScratchLease& operator=(const SolverStageScratchLease&) = delete;
    SolverStageScratch& get() { return *storage_; }
};

} // namespace raftsim::solver_detail
