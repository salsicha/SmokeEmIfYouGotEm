#pragma once

// Diagnostic builds only. No clock reads, storage or logging in normal builds.
// Timings are inclusive wall-clock durations on each solver thread, not CPU
// sampling or release qualification. Nested categories must not be summed.
#if RAFTSIM_PROFILE_SOLVER
#include <array>
#include <chrono>
#include <cstdio>

namespace raftsim::solver_profile {
enum Stage { Total, CFL, Reconstruction, Flux, CombineFriction, Recompute, Count };
struct Totals {
    std::array<double, Count> milliseconds{};
    std::array<unsigned long long, Count> calls{};
    ~Totals() {
        constexpr const char* names[] = {"finite_volume", "cfl", "reconstruction", "flux", "combine_friction", "recompute"};
        std::fprintf(stderr, "RAFTSIM_SOLVER_PROFILE {\"schema\":\"raftsim.solver.stage_profile.v1\",\"inclusive_wall_time\":true,\"stages\":{");
        for (int i=0; i<Count; ++i)
            std::fprintf(stderr, "%s\"%s\":{\"calls\":%llu,\"total_ms\":%.9f}", i ? "," : "", names[i], calls[i], milliseconds[i]);
        std::fprintf(stderr, "}}\n");
    }
};
inline thread_local Totals totals;
struct Scope {
    Stage stage;
    std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now();
    bool active = true;
    explicit Scope(Stage value) : stage(value) {}
    void finish() {
        if (!active) return;
        totals.milliseconds[stage] += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now()-start).count();
        ++totals.calls[stage];
        active=false;
    }
    ~Scope() { finish(); }
};
}
#define RAFTSIM_PROFILE_SCOPE(variable, stage) solver_profile::Scope variable(solver_profile::stage)
#define RAFTSIM_PROFILE_FINISH(variable) variable.finish()
#else
#define RAFTSIM_PROFILE_SCOPE(variable, stage) ((void)0)
#define RAFTSIM_PROFILE_FINISH(variable) ((void)0)
#endif
