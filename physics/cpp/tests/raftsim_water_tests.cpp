#include "raftsim_water/chrono_coupling.hpp"
#include "raftsim_water/solver.hpp"
#include "../src/solver_internal.hpp"
#include "../src/solver_row_executor.hpp"
#include "../src/solver_grid_view.hpp"
#include "../src/solver_wave_speed.hpp"
#include "../src/solver_stage_scratch.hpp"
#include <future>

#include <algorithm>
#include <cmath>
#include <exception>
#include <filesystem>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

double max_abs_diff(const raftsim::Array2D& left, const raftsim::Array2D& right) {
    expect(left.nx() == right.nx() && left.ny() == right.ny(), "array shapes differ");
    double diff = 0.0;
    for (std::size_t row = 0; row < left.ny(); ++row) {
        for (std::size_t col = 0; col < left.nx(); ++col) {
            diff = std::max(diff, std::abs(left(row, col) - right(row, col)));
        }
    }
    return diff;
}

void assert_validated_grid_views() {
    using namespace raftsim::solver_detail;
    raftsim::Array2D field(7,11);
    WriteGridView write(field,7,11);
    for (std::size_t r=0;r<7;++r) for (std::size_t c=0;c<11;++c)
        write(r,c)=double(r*11+c)*.03125;
    const ReadGridView read(field,7,11);
    for (std::size_t r=0;r<7;++r) for (std::size_t c=0;c<11;++c)
        expect(read(r,c)==field(r,c),"validated view changed a value or coordinate");
    auto rejected=[&](std::size_t ny,std::size_t nx) {
        bool failed=false;
        try { ReadGridView bad(field,ny,nx); } catch (const std::runtime_error&) { failed=true; }
        expect(failed,"invalid view must fail before unchecked access");
    };
    rejected(11,7); rejected(0,11); rejected(7,0);
    rejected(std::numeric_limits<std::size_t>::max(),2);
    field.values().pop_back(); rejected(7,11);
    field.values().resize(78); rejected(7,11);
}

void assert_stage_scratch_ownership() {
    using namespace raftsim::solver_detail;
    SolverStageScratch* retained = nullptr;
    const MusclFaceState* allocation = nullptr;
    {
        SolverStageScratchLease outer;
        auto& storage = outer.get();
        retained = &storage;
        storage.prepare(17000);
        allocation = storage.primitives.data();
        storage.primitives[13] = {1., 2., 3., 4.};
        for (auto& slope : storage.slopes) slope = {1., 2., 3., 4., 5., 6.};
        {
            SolverStageScratchLease inner;
            expect(&inner.get() != retained, "nested stage aliases active storage");
            inner.get().prepare(25000);
            inner.get().primitives[13] = {7., 8., 9., 10.};
        }
        expect(storage.primitives.data() == allocation && storage.primitives[13].v == 4.,
            "nested stage invalidated outer arrays");
        auto worker = std::async(std::launch::async, [retained] {
            SolverStageScratchLease other;
            other.get().prepare(31);
            return &other.get() != retained;
        });
        expect(worker.get(), "different caller threads share scratch");
        for (std::size_t size : {7u, 0u, 17000u}) {
            storage.prepare(size);
            expect(storage.primitives.size() == size && storage.slopes.size() == size,
                "reused stage has wrong active size");
            if (size) expect(storage.primitives.data() == allocation, "same-capacity stage reallocated");
            for (const auto& s : storage.slopes)
                expect(s.x_eta == 0. && s.x_u == 0. && s.x_v == 0. &&
                       s.y_eta == 0. && s.y_u == 0. && s.y_v == 0.,
                       "stale dry-cell or dry-neighbor slope survived prepare");
        }
    }
    struct FixtureException {};
    try {
        SolverStageScratchLease failing;
        expect(&failing.get() == retained, "completed stage did not release retained storage");
        throw FixtureException{};
    } catch (const FixtureException&) {}
    SolverStageScratchLease recovered;
    expect(&recovered.get() == retained, "exception stranded scratch lease");
}

void assert_scenario_loads(const raftsim::Scenario& scenario) {
    expect(!scenario.scenario_id.empty(), "scenario id is empty");
    expect(scenario.grid.nx >= 2 && scenario.grid.ny >= 2, "grid too small");
    expect(scenario.bed.nx() == scenario.grid.nx, "bed nx mismatch");
    expect(scenario.initial.h.ny() == scenario.grid.ny, "initial h ny mismatch");
    expect(scenario.initial.wet.values.size() == scenario.grid.nx * scenario.grid.ny, "wet mask shape mismatch");
    expect(!scenario.boundaries.empty(), "expected scenario boundaries");
    expect(!scenario.probes.empty(), "expected probes for telemetry exports");
    if (scenario.cascading.present) {
        expect(scenario.cascading.schema_version == "raftsim.cascading2_5d.v0", "unexpected cascading schema version");
        expect(!scenario.cascading.reaches.empty(), "expected cascading reaches");
        expect(!scenario.cascading.drop_transitions.empty(), "expected cascading drop transitions");
        expect(scenario.cascading.reaches.front().station_start <= scenario.cascading.reaches.front().station_end, "invalid cascading reach range");
    }
}

void assert_solver_is_deterministic(const raftsim::Scenario& scenario) {
    raftsim::ReducedShallowWaterSolver first(scenario);
    raftsim::ReducedShallowWaterSolver second(scenario);

    std::vector<raftsim::Frame> first_frames = first.run(12, 4);
    std::vector<raftsim::Frame> second_frames = second.run(12, 4);
    expect(first_frames.size() == second_frames.size(), "deterministic frame count mismatch");
    expect(max_abs_diff(first_frames.back().state.h, second_frames.back().state.h) < 1.0e-12, "depth run is not deterministic");
    expect(max_abs_diff(first_frames.back().state.u, second_frames.back().state.u) < 1.0e-12, "u run is not deterministic");
    expect(max_abs_diff(first_frames.back().state.v, second_frames.back().state.v) < 1.0e-12, "v run is not deterministic");
}

raftsim::SolverConfig finite_volume_second_order_config() {
    raftsim::SolverConfig config;
    config.solver_mode = "finite_volume";
    config.flux_scheme = "hll";
    config.spatial_order = 2;
    config.bed_slope_source_scale = 1.0;
    config.feature_strength_scale = 0.0;
    config.preserve_initial_mass = false;
    config.disable_fixture_calibrations = true;
    return config;
}

void assert_boundary_flux_diagnostic(const raftsim::Scenario& source) {
    raftsim::Scenario scenario = source;
    for (auto& boundary : scenario.boundaries) {
        boundary.kind = (boundary.edge == "west") ? "inflow" :
            ((boundary.edge == "east") ? "outflow" : "wall");
        boundary.has_stage = boundary.edge == "west" || boundary.edge == "east";
        boundary.stage = 1.0;
        boundary.has_depth = false;
        boundary.has_velocity = boundary.edge == "west";
        boundary.velocity_x = 0.5;
        boundary.velocity_y = 0.0;
    }
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            scenario.bed(row, col) = 0.0;
            scenario.initial.h(row, col) = 1.0;
            scenario.initial.u(row, col) = 0.5;
            scenario.initial.v(row, col) = 0.0;
        }
    }
    auto config = finite_volume_second_order_config();
    config.roughness_scale = 0.0;
    raftsim::ReducedShallowWaterSolver solver(scenario, config);
    const auto before = solver.make_frame();
    const auto flux = solver.inspect_boundary_mass_fluxes();
    const auto faces = solver.inspect_numerical_mass_flux_grid();
    expect(faces.x_faces.nx()==scenario.grid.nx+1 && faces.x_faces.ny()==scenario.grid.ny &&
        faces.y_faces.nx()==scenario.grid.nx && faces.y_faces.ny()==scenario.grid.ny+1,
        "numerical face grid dimensions incorrect");
    double face_west=0.0,face_east=0.0,face_south=0.0,face_north=0.0;
    for (std::size_t row=0;row<scenario.grid.ny;++row) {
        face_west+=faces.x_faces(row,0)*scenario.grid.dy;
        face_east-=faces.x_faces(row,scenario.grid.nx)*scenario.grid.dy;
        for (std::size_t col=1;col<scenario.grid.nx;++col)
            expect(std::abs(faces.x_faces(row,col)-0.5)<1e-12,"interior face flux differs from uniform h*u");
    }
    for (std::size_t col=0;col<scenario.grid.nx;++col) {
        face_south+=faces.y_faces(0,col)*scenario.grid.dx;
        face_north-=faces.y_faces(scenario.grid.ny,col)*scenario.grid.dx;
    }
    expect(std::abs(face_west-flux.west)+std::abs(face_east-flux.east)+
        std::abs(face_south-flux.south)+std::abs(face_north-flux.north)<1e-12,
        "numerical face grid disagrees with exact boundary flux audit");
    const double expected = 0.5 * scenario.grid.ny * scenario.grid.dy;
    expect(std::abs(flux.west - expected) < 1e-10, "uniform west boundary flux units/sign incorrect");
    expect(std::abs(flux.east + expected) < 1e-10, "uniform east boundary flux units/sign incorrect");
    expect(std::abs(flux.north) + std::abs(flux.south) < 1e-10, "wall boundary leaked volume");
    expect(max_abs_diff(solver.state().h, before.state.h) == 0.0 &&
        max_abs_diff(solver.state().u, before.state.u) == 0.0 &&
        max_abs_diff(solver.state().v, before.state.v) == 0.0 && solver.time() == before.time,
        "boundary inspection mutated live state");

    auto raised = solver.state();
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) raised.h(row, col) = 1.1;
    }
    solver.replace_state(raised, 0.0);
    const auto backwater = solver.inspect_boundary_mass_fluxes();
    expect(backwater.west < expected, "stage/velocity inlet incorrectly treated as prescribed discharge");
    const double mass_before = raftsim::compute_mass(scenario, solver.state());
    const double dt = 1e-5;
    solver.step(dt);
    const double measured_rate = (raftsim::compute_mass(scenario, solver.state()) - mass_before) / dt;
    const double face_rate = backwater.west + backwater.east + backwater.south + backwater.north;
    expect(std::abs(measured_rate - face_rate) < 1e-3 * std::max(1.0, std::abs(face_rate)),
        "boundary face flux does not match small-step volume balance");
    config.experimental_west_discharge_m3s = expected;
    raftsim::ReducedShallowWaterSolver prescribed(scenario, config);
    prescribed.replace_state(raised, 0.0);
    const auto fixed_flux = prescribed.inspect_boundary_mass_fluxes();
    expect(std::abs(fixed_flux.west - expected) < 1e-10,
        "prescribed inlet discharge changed under backwater");
    const double fixed_mass = raftsim::compute_mass(scenario, prescribed.state());
    prescribed.step(dt);
    const double fixed_rate = (raftsim::compute_mass(scenario, prescribed.state()) - fixed_mass) / dt;
    expect(std::abs(fixed_rate - (fixed_flux.west + fixed_flux.east)) < 1e-3 * std::max(1.0, std::abs(fixed_rate)),
        "prescribed discharge is not conservative at the domain face");
    // Uniform flow is preserved, and the new branch is opt-in only.
    raftsim::ReducedShallowWaterSolver uniform(scenario, config);
    uniform.step(0.01);
    expect(max_abs_diff(uniform.state().h, before.state.h) < 1e-12 &&
        max_abs_diff(uniform.state().u, before.state.u) < 1e-12,
        "prescribed characteristic boundary disturbed matching uniform flow");
    auto supercritical = raised;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) supercritical.u(row, 0) = 10.0;
    prescribed.replace_state(supercritical, 0.0);
    bool critical_rejected = false;
    try { prescribed.inspect_boundary_mass_fluxes(); }
    catch (const std::runtime_error&) { critical_rejected = true; }
    expect(critical_rejected, "unsupported supercritical discharge boundary was accepted");
    auto mixed_config = config;
    mixed_config.experimental_west_supercritical_stage = true;
    raftsim::ReducedShallowWaterSolver mixed(scenario, mixed_config);
    mixed.replace_state(supercritical, 0.0);
    const auto mixed_flux = mixed.inspect_boundary_mass_fluxes();
    expect(std::abs(mixed_flux.west - expected) < 1e-10,
        "mixed-regime boundary lost prescribed total discharge");
    const double mixed_mass_before = raftsim::compute_mass(scenario, mixed.state());
    mixed.step(dt);
    const double mixed_rate = (raftsim::compute_mass(scenario, mixed.state())-mixed_mass_before)/dt;
    expect(std::abs(mixed_rate-(mixed_flux.west+mixed_flux.east+mixed_flux.north+mixed_flux.south)) < 1e-3,
        "mixed-regime boundary violates face-flux volume balance");
    auto mixed_fringe = raised;
    mixed_fringe.h(0,0) = 0.085847;
    mixed_fringe.u(0,0) = 0.979504;
    mixed.replace_state(mixed_fringe,0.0);
    expect(std::abs(mixed.inspect_boundary_mass_fluxes().west-expected)<1e-10,
        "natural shallow supercritical fringe lost net inflow");
    mixed_config.experimental_west_discharge_m3s = -1.0;
    bool missing_q_rejected = false;
    try { raftsim::ReducedShallowWaterSolver invalid_mixed(scenario,mixed_config); }
    catch (const std::runtime_error&) { missing_q_rejected = true; }
    expect(missing_q_rejected,"mixed-regime stage accepted without explicit discharge");
    auto film_scenario = scenario;
    for (auto& boundary : film_scenario.boundaries) boundary.kind = "wall";
    for (std::size_t row=0;row<scenario.grid.ny;++row) {
        for (std::size_t col=0;col<scenario.grid.nx;++col) {
            film_scenario.initial.h(row,col)=0.5*config.dry_tolerance;
            film_scenario.initial.u(row,col)=0.0;
            film_scenario.initial.v(row,col)=0.0;
        }
    }
    auto film_config=finite_volume_second_order_config();
    raftsim::ReducedShallowWaterSolver film(film_scenario,film_config);
    const double film_mass=raftsim::compute_mass(film_scenario,film.state());
    film.step(.01);
    expect(std::abs(raftsim::compute_mass(film_scenario,film.state())-film_mass)<1e-12,
        "positive sub-dry-tolerance water volume disappeared");
    auto fringe = raised;
    fringe.h(0, 0) = 0.00001;
    fringe.u(0, 0) = -0.13; // both characteristics leave through the west face
    prescribed.replace_state(fringe, 0.0);
    expect(std::abs(prescribed.inspect_boundary_mass_fluxes().west - expected) < 1e-10,
        "draining fringe was forced as inflow or lost net discharge accounting");
    auto dry_bank = scenario;
    dry_bank.bed(0, 0) = 2.0; // above the inlet's authored stage/flow segment
    dry_bank.initial.h(0, 0) = 0.0003;
    dry_bank.initial.u(0, 0) = 10.0;
    raftsim::ReducedShallowWaterSolver bounded_inlet(dry_bank, config);
    expect(std::abs(bounded_inlet.inspect_boundary_mass_fluxes().west - expected) < 1e-10,
        "inlet injected flow into an unrelated dry-bank film");
    config.experimental_west_discharge_m3s = -1.0;
    config.spatial_order = 1;
    bool rejected = false;
    try { raftsim::ReducedShallowWaterSolver(scenario, config).inspect_boundary_mass_fluxes(); }
    catch (const std::runtime_error&) { rejected = true; }
    expect(rejected, "unsupported diagnostic mode was silently accepted");
}

void assert_malformed_state_storage_is_rejected(const raftsim::Scenario& scenario) {
    for (int field=0;field<8;++field) {
        auto malformed=scenario;
        if(field==7) malformed.initial.wet.values.pop_back();
        else {
            raftsim::Array2D* arrays[]={&malformed.bed,&malformed.initial.h,&malformed.initial.u,
                &malformed.initial.v,&malformed.initial.eta,&malformed.initial.hu,&malformed.initial.hv};
            arrays[field]->values().pop_back();
        }
        bool rejected=false;
        try { raftsim::ReducedShallowWaterSolver bad(malformed); }
        catch(const std::runtime_error&) { rejected=true; }
        expect(rejected,"constructor accepted inconsistent numerical backing storage");
    }
    raftsim::ReducedShallowWaterSolver solver(scenario);
    const auto before=solver.state();
    auto malformed=before;
    malformed.h.values().pop_back();
    bool rejected=false;
    try { solver.replace_state(malformed,3.); } catch(const std::runtime_error&) { rejected=true; }
    expect(rejected && solver.time()==0. && solver.state().h.values()==before.h.values() &&
        solver.state().u.values()==before.u.values() && solver.state().v.values()==before.v.values(),
        "rejected malformed replacement mutated the committed state");
}

void assert_solver_row_barrier_and_failure_recovery() {
    using raftsim::solver_detail::solver_row_ranges;
    for (int repeat = 0; repeat < 12; ++repeat) {
        std::vector<int> values(163, -1);
        solver_row_ranges(values.size(), true, [&](std::size_t first, std::size_t end) {
            for (auto row = first; row < end; ++row) values[row] = static_cast<int>(row) + repeat;
        });
        for (std::size_t row = 0; row < values.size(); ++row)
            expect(values[row] == static_cast<int>(row) + repeat, "row dispatch returned before completion");
    }
    bool caught = false;
    try {
        solver_row_ranges(163, true, [](std::size_t first, std::size_t) {
            if (first == 8) throw std::runtime_error("row failure probe");
        });
    } catch (const std::runtime_error& error) { caught = std::string(error.what()) == "row failure probe"; }
    expect(caught, "worker exception was lost");
    std::atomic<int> count{0};
    auto dispatch = [&] {
        solver_row_ranges(163, true, [&](std::size_t first, std::size_t end) {
            count.fetch_add(static_cast<int>(end-first));
            // Nested use must not wait on its own worker barrier.
            solver_row_ranges(20, true, [](std::size_t, std::size_t) {});
        });
    };
    std::thread concurrent(dispatch);
    dispatch();
    concurrent.join();
    expect(count == 326, "concurrent dispatch or post-failure recovery lost work");
    const int rounding = std::fegetround();
    std::fesetround(FE_DOWNWARD);
    std::atomic<int> wrong_rounding{0};
    solver_row_ranges(163, true, [&](std::size_t, std::size_t) {
        if (std::fegetround() != FE_DOWNWARD) ++wrong_rounding;
    });
    std::fesetround(rounding);
    expect(wrong_rounding == 0, "worker changed host floating-point rounding mode");
}

void assert_finite_volume_second_order_is_deterministic(const raftsim::Scenario& scenario) {
    raftsim::SolverConfig config = finite_volume_second_order_config();
    raftsim::ReducedShallowWaterSolver first(scenario, config);
    raftsim::ReducedShallowWaterSolver second(scenario, config);
    std::vector<raftsim::Frame> first_frames = first.run(12, 4);
    std::vector<raftsim::Frame> second_frames = second.run(12, 4);
    expect(first_frames.size() == second_frames.size(), "second-order deterministic frame count mismatch");
    expect(max_abs_diff(first_frames.back().state.h, second_frames.back().state.h) < 1.0e-12, "second-order depth run is not deterministic");
    expect(max_abs_diff(first_frames.back().state.u, second_frames.back().state.u) < 1.0e-12, "second-order u run is not deterministic");
    expect(max_abs_diff(first_frames.back().state.v, second_frames.back().state.v) < 1.0e-12, "second-order v run is not deterministic");
}

void assert_finite_volume_cfl_failure_is_bounded(const raftsim::Scenario& scenario) {
    raftsim::ReducedShallowWaterSolver solver(scenario, finite_volume_second_order_config());
    raftsim::WaterState unstable = solver.state();
    // Finite but absurd depth used to request billions of hidden substeps.
    unstable.h(scenario.grid.ny / 2, scenario.grid.nx / 2) = 1.0e24;
    solver.replace_state(std::move(unstable), 2.0);
    bool rejected = false;
    try { solver.step(0.1); }
    catch (const std::runtime_error& error) {
        rejected = std::string(error.what()).find("CFL work limit exceeded") != std::string::npos;
    }
    expect(rejected, "unstable CFL workload was not rejected before integration");
    expect(solver.time() == 2.0, "rejected CFL step advanced simulation time");
}

void assert_validation_rejects_clipped_or_nonfinite_flow(const raftsim::Scenario& scenario) {
    auto config = finite_volume_second_order_config();
    raftsim::ReducedShallowWaterSolver solver(scenario, config);
    auto frame = solver.make_frame();
    frame.state.u(0,0) = config.max_velocity;
    auto result = raftsim::validate_frames(scenario, {frame}, config);
    expect(!result.passed && result.velocity_limit_reached,
        "velocity-clamped unstable flow was reported as passing");
    frame = solver.make_frame();
    frame.state.v(0,0) = std::numeric_limits<double>::quiet_NaN();
    result = raftsim::validate_frames(scenario, {frame}, config);
    expect(!result.passed && !result.finite_state, "NaN was ignored by flow validation");
}

void assert_live_state_can_be_replaced(const raftsim::Scenario& scenario) {
    raftsim::ReducedShallowWaterSolver solver(scenario, finite_volume_second_order_config());
    raftsim::WaterState replacement = solver.state();
    const std::size_t row = scenario.grid.ny / 2;
    const std::size_t col = scenario.grid.nx / 2;
    replacement.h(row, col) = std::max(0.25, replacement.h(row, col) + 0.125);
    replacement.u(row, col) = 1.75;
    replacement.v(row, col) = -0.25;
    // Deliberately stale derived fields must be corrected by replace_state.
    replacement.eta(row, col) = -999.0;
    replacement.hu(row, col) = -999.0;
    replacement.hv(row, col) = -999.0;
    replacement.wet.values[row * scenario.grid.nx + col] = 0;
    solver.replace_state(std::move(replacement), 3.25);
    expect(std::abs(solver.time() - 3.25) < 1.0e-12, "replacement did not preserve requested solver time");
    expect(std::abs(solver.state().eta(row, col) -
                    (scenario.bed(row, col) + solver.state().h(row, col))) < 1.0e-12,
           "replacement eta was not recomputed");
    expect(std::abs(solver.state().hu(row, col) -
                    solver.state().h(row, col) * solver.state().u(row, col)) < 1.0e-12,
           "replacement momentum was not recomputed");
    expect(solver.state().wet(row, col), "replacement wet mask was not recomputed");

    raftsim::WaterState bad_shape = solver.state();
    bad_shape.h = raftsim::Array2D(1, 1, 1.0);
    bool rejected = false;
    try {
        solver.replace_state(std::move(bad_shape), 4.0);
    } catch (const std::runtime_error&) {
        rejected = true;
    }
    expect(rejected, "shape-mismatched replacement state was accepted");
}

void assert_muscl_scratch_is_not_state(const raftsim::Scenario& scenario) {
    auto config = finite_volume_second_order_config();
    config.disable_fixture_calibrations = true;
    raftsim::ReducedShallowWaterSolver reused(scenario, config);
    const std::size_t row = scenario.grid.ny / 2;
    const std::size_t col = scenario.grid.nx / 2;
    for (int iteration = 0; iteration < 6; ++iteration) {
        auto replacement = reused.state();
        replacement.h(row, col) = iteration % 2 == 0 ? 0.0 : 0.25;
        replacement.u(row, col) = 0.15;
        replacement.v(row, col) = -0.1;
        raftsim::ReducedShallowWaterSolver fresh(scenario, config);
        fresh.replace_state(replacement, reused.time());
        reused.replace_state(replacement, reused.time());
        const auto before = reused.state();
        (void)reused.inspect_boundary_mass_fluxes();
        expect(before.h.values() == reused.state().h.values(), "flux audit mutated live depth");
        fresh.step(0.001);
        reused.step(0.001);
        const auto& a = fresh.state();
        const auto& b = reused.state();
        expect(a.h.values() == b.h.values() && a.u.values() == b.u.values() &&
            a.v.values() == b.v.values() && a.eta.values() == b.eta.values() &&
            a.hu.values() == b.hu.values() && a.hv.values() == b.hv.values() &&
            a.wet.values == b.wet.values, "RK scratch leaked across wet/dry state replacement");
    }
}

void assert_cfl_scan_matches_original() {
    using namespace raftsim;
    using namespace raftsim::solver_detail;
    const int previous_rounding=std::fegetround();
    struct RestoreRounding {
        int value;
        ~RestoreRounding() { std::fesetround(value); }
    } restore{previous_rounding};
    for (auto dimensions:{std::pair<std::size_t,std::size_t>{1,1},{7,19},{131,129}}) {
        Scenario scenario;
        const auto nx=dimensions.first,ny=dimensions.second;
        WaterState state;
        state.h=Array2D(ny,nx);state.u=Array2D(ny,nx);state.v=Array2D(ny,nx);
        SolverConfig config;
        for (std::size_t row=0;row<ny;++row) for (std::size_t col=0;col<nx;++col) {
            const auto i=row*nx+col;
            state.h(row,col)=i%9==0 ? -1. : (i%7==0 ? .5e-6 : .003+(i%113)*.017);
            state.u(row,col)=.13*double(int(i%139)-69);
            state.v(row,col)=-.19*double(int(i%107)-53);
        }
        const auto reference=[&]() {
            double maximum=0.0;
            for (std::size_t row=0;row<ny;++row) for (std::size_t col=0;col<nx;++col) {
                const auto q=conserved_from_cell(scenario,state,config,row,col);
                maximum=std::max(maximum,wave_speed_x(q,config));
                maximum=std::max(maximum,wave_speed_y(q,config));
            }
            return maximum;
        };
        for (int rounding:{FE_TONEAREST,FE_DOWNWARD,FE_UPWARD,FE_TOWARDZERO}) {
            expect(std::fesetround(rounding)==0,"CFL test could not set rounding mode");
            for (double dry:{1.e-6,.01,3.}) {
                config.dry_tolerance=dry;
                const double expected=reference(),actual=maximum_wave_speed(state,config,ny,nx);
                expect(actual==expected && std::signbit(actual)==std::signbit(expected),
                    "row CFL maximum differs from original scan or signed zero");
                expect(std::fegetround()==rounding,"CFL scan changed caller rounding mode");
            }
        }
        std::fesetround(previous_rounding);
        config.dry_tolerance=1.e-6;
        // Exercise the original unordered comparison behavior without claiming
        // these malformed physical inputs constitute a valid solver state.
        state.h.values()[0]=1.;state.u.values()[0]=std::numeric_limits<double>::quiet_NaN();
        state.v.values()[0]=.3;
        expect(maximum_wave_speed(state,config,ny,nx)==reference(),"CFL NaN comparison changed");
        state.v.values().back()=std::numeric_limits<double>::infinity();
        state.h.values().back()=1.;
        expect(maximum_wave_speed(state,config,ny,nx)==reference(),"CFL infinity handling changed");
        for (int field=0;field<3;++field) {
            auto malformed=state;
            Array2D* arrays[]={&malformed.h,&malformed.u,&malformed.v};
            arrays[field]->values().pop_back();
            bool rejected=false;
            try { maximum_wave_speed(malformed,config,ny,nx); }
            catch (const std::runtime_error&) { rejected=true; }
            expect(rejected,"CFL scan accepted malformed storage");
        }
    }
}

void assert_large_parallel_rows_match_serial(const raftsim::Scenario& original) {
    auto scenario = original;
    constexpr std::size_t nx = 131, ny = 129; // Above the real parallel threshold.
    scenario.grid.nx = nx; scenario.grid.ny = ny;
    scenario.grid.dx = .7; scenario.grid.dy = 1.1;
    scenario.bed = raftsim::Array2D(ny,nx);
    for (auto* field : {&scenario.initial.h,&scenario.initial.u,&scenario.initial.v,
                       &scenario.initial.eta,&scenario.initial.hu,&scenario.initial.hv})
        *field = raftsim::Array2D(ny,nx);
    scenario.initial.wet = raftsim::BoolGrid{ny,nx,std::vector<std::uint8_t>(nx*ny,0)};
    for (auto& boundary : scenario.boundaries) {
        boundary.kind = "wall";
        boundary.has_stage = boundary.has_depth = boundary.has_velocity = false;
    }
    for (std::size_t row=0;row<ny;++row) for (std::size_t col=0;col<nx;++col) {
        const double bed = .8*std::sin(row*.11)+.4*std::cos(col*.17) + ((row/7+col/11)%5==0 ? 1.5 : 0.);
        scenario.bed(row,col)=bed;
        scenario.initial.h(row,col)=std::max(0.,1.1-bed);
        if ((row+col)%13==0) scenario.initial.h(row,col)=.5e-6; // Preserve positive films.
        scenario.initial.u(row,col)=.4*std::sin(col*.05);
        scenario.initial.v(row,col)=.3*std::cos(row*.13);
    }
    for (const char* scheme : {"hll","roe","rusanov"}) for (double bed_scale : {0.,1.})
    for (double roughness : {0., .035, .6}) {
        scenario.roughness = roughness;
        auto config=finite_volume_second_order_config();
        config.flux_scheme=scheme;
        config.bed_slope_source_scale=bed_scale;
        raftsim::ReducedShallowWaterSolver parallel(scenario,config),serial(scenario,config);
        for (int step=0;step<12;++step) {
            if (step==4 || step==8) {
                auto replacement=parallel.state();
                replacement.h(64,65)=step==4 ? 0. : .3;
                parallel.replace_state(replacement,parallel.time());
                serial.replace_state(replacement,serial.time());
            }
            // Exercise both single-stage and CFL-subdivided calls, including
            // undamped and strongly damped water, without changing the scheme.
            const double dt=step==11 ? .081 : .003+.0001*step;
            parallel.step(dt);
            // A nested dispatch executes serially; the identical numerical
            // implementation is exercised without adding a public solver knob.
            raftsim::solver_detail::solver_row_ranges(32,true,[&](std::size_t first,std::size_t) {
                if (first==0) serial.step(dt);
            });
            const auto& a=parallel.state();const auto& b=serial.state();
            expect(a.h.values()==b.h.values() && a.u.values()==b.u.values() &&
                a.v.values()==b.v.values() && a.eta.values()==b.eta.values() &&
                a.hu.values()==b.hu.values() && a.hv.values()==b.hv.values() &&
                a.wet.values==b.wet.values && parallel.time()==serial.time(),
                "parallel rows differ from serial across wet/dry/film or replacement state");
        }
    }
}

void assert_finite_volume_second_order_is_well_balanced(const raftsim::Scenario& scenario) {
    // A lake-at-rest state over the scenario bathymetry (with reflective walls) must
    // stay exactly at rest under the second-order MUSCL path, including partially
    // submerged topography with wet/dry margins.
    raftsim::Scenario rest = scenario;
    for (raftsim::BoundaryCondition& boundary : rest.boundaries) {
        boundary.kind = "wall";
        boundary.has_stage = false;
        boundary.has_depth = false;
        boundary.has_velocity = false;
    }
    double bed_min = rest.bed.min();
    double bed_max = rest.bed.max();
    double stage = bed_max > bed_min + 1.0e-9 ? bed_min + 0.75 * (bed_max - bed_min) : bed_min + 1.0;
    for (std::size_t row = 0; row < rest.grid.ny; ++row) {
        for (std::size_t col = 0; col < rest.grid.nx; ++col) {
            double depth = std::max(0.0, stage - rest.bed(row, col));
            rest.initial.h(row, col) = depth;
            rest.initial.eta(row, col) = rest.bed(row, col) + depth;
            rest.initial.u(row, col) = 0.0;
            rest.initial.v(row, col) = 0.0;
            rest.initial.hu(row, col) = 0.0;
            rest.initial.hv(row, col) = 0.0;
            rest.initial.wet.values[row * rest.grid.nx + col] = depth > 1.0e-6 ? 1 : 0;
        }
    }
    raftsim::ReducedShallowWaterSolver solver(rest, finite_volume_second_order_config());
    std::vector<raftsim::Frame> frames = solver.run(24, 8);
    expect(max_abs_diff(frames.back().state.h, frames.front().state.h) < 1.0e-12, "lake at rest depth drifted under second-order path");
    expect(max_abs_diff(frames.back().state.u, frames.front().state.u) < 1.0e-12, "lake at rest u drifted under second-order path");
    expect(max_abs_diff(frames.back().state.v, frames.front().state.v) < 1.0e-12, "lake at rest v drifted under second-order path");
}

void assert_emergent_step_uses_hydrostatic_flux() {
    using namespace raftsim::solver_detail;
    auto config = finite_volume_second_order_config();
    // Both centres are wet but the lower pool is below the raised neighbour's
    // bed. The interface is a wet/dry problem, not a fully submerged bed step.
    const MusclFaceState lower{0.10, 0.10, 0.0, 0.0};
    const MusclFaceState upper{0.08, 0.38, 0.0, 0.0};
    const MusclFaceState dry{0.0, 0.30, 0.0, 0.0};
    const auto x = muscl_hydrostatic_flux_x(lower, upper, true, config);
    const auto reference_x = muscl_hydrostatic_flux_x(dry, upper, true, config);
    expect(std::abs(x.left.h - reference_x.left.h) < 1e-12,
        "emergent x-step bypassed hydrostatic reconstruction");
    expect(std::abs(x.left.h - x.right.h) < 1e-12, "emergent x-step leaked mass");
    expect(std::abs(x.left.hu - reference_x.left.hu - 0.5*config.gravity*0.01) < 1e-12,
        "emergent x-step lost lower-side pressure correction");
    const auto y = muscl_hydrostatic_flux_y(lower, upper, true, config);
    expect(std::abs(y.left.h - x.left.h) < 1e-12, "emergent step is axis dependent");
    expect(std::abs(y.left.hv - x.left.hu) < 1e-12, "emergent y-step pressure mismatch");
    const auto reversed = muscl_hydrostatic_flux_x(upper, lower, true, config);
    expect(std::abs(reversed.left.h + x.left.h) < 1e-12, "emergent step reversal mismatch");
    expect(std::abs(reversed.right.hu - x.left.hu) < 1e-12, "reversed pressure mismatch");
    // The uncalibrated solver must also retain the hydrostatic flux while a
    // moving surface fully submerges the step, not switch methods at that instant.
    const MusclFaceState deep_lower{0.8, 0.8, 0.4, -0.2};
    const MusclFaceState deep_upper{0.7, 1.0, -0.1, 0.3};
    const ConservedState left_star{0.5, 0.5*0.4, 0.5*-0.2};
    const ConservedState right_star{0.7, 0.7*-0.1, 0.7*0.3};
    const auto expected = finite_volume_flux_x(left_star, right_star, config);
    const auto submerged = muscl_hydrostatic_flux_x(deep_lower, deep_upper, true, config);
    expect(std::abs(submerged.left.h - expected.h) < 1e-12,
        "submerged step switched away from hydrostatic mass flux");
    expect(std::abs(submerged.left.hu - expected.hu - 0.5*config.gravity*(0.64-0.25)) < 1e-12,
        "submerged step pressure correction mismatch");
}

void assert_output_can_be_written(const raftsim::Scenario& scenario, const std::string& output_dir) {
    raftsim::SolverConfig config;
    raftsim::ReducedShallowWaterSolver solver(scenario, config);
    std::vector<raftsim::Frame> frames = solver.run(8, 4);
    raftsim::ValidationSummary validation = raftsim::validate_frames(scenario, frames, {});
    expect(validation.passed, "validation failed for smoke scenario");
    raftsim::write_solver_output(scenario, frames, validation, config, output_dir);
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "manifest.json"), "manifest was not written");
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "validation.json"), "validation was not written");
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "frames" / "frame_0000.csv"), "frame was not written");
}

void assert_chrono_coupling_samples_water_and_contact(const raftsim::Scenario& scenario) {
    raftsim::ReducedShallowWaterSolver solver(scenario);
    raftsim::Frame frame = solver.make_frame();
    double x = scenario.grid.origin_x + static_cast<double>(scenario.grid.nx / 2) * scenario.grid.dx;
    double y = scenario.grid.origin_y + static_cast<double>(scenario.grid.ny / 2) * scenario.grid.dy;
    // A wet/dry shoreline fixture need not have water at its grid centre.
    // Exercise buoyancy at an actually wet location, not an assumed one.
    if (raftsim::sample_water_field(scenario, frame, x, y).depth <= 0.0) {
        double deepest = 0.0;
        for (std::size_t row=0;row<scenario.grid.ny;++row) {
            for (std::size_t col=0;col<scenario.grid.nx;++col) {
                if (frame.state.h(row,col)>deepest) {
                    deepest=frame.state.h(row,col);
                    x=scenario.grid.origin_x+col*scenario.grid.dx;
                    y=scenario.grid.origin_y+row*scenario.grid.dy;
                }
            }
        }
    }
    raftsim::WaterFieldSample water = raftsim::sample_water_field(scenario, frame, x, y);
    expect(water.depth >= 0.0, "sampled negative water depth");
    expect(water.normal.z > 0.0, "sampled invalid water normal");

    raftsim::ChronoRaftPatch floating_patch{
        raftsim::Vec3d{x, y, water.surface_height - 0.25},
        raftsim::Vec3d{0.0, 0.0, -0.1},
        0.5,
    };
    raftsim::ChronoForceSample floating = raftsim::sample_chrono_raft_patch(scenario, frame, floating_patch);
    expect(floating.wet, "floating Chrono patch should be wet");
    expect(floating.force.z > 0.0, "floating Chrono patch should receive upward force");

    raftsim::ChronoRaftPatch grounded_patch{
        raftsim::Vec3d{x, y, water.bed_height - 0.05},
        raftsim::Vec3d{0.0, 0.0, -0.1},
        0.5,
    };
    raftsim::ChronoForceSample grounded = raftsim::sample_chrono_raft_patch(scenario, frame, grounded_patch);
    expect(grounded.grounded, "grounded Chrono patch should detect bed contact");
    expect(grounded.bed_penetration > 0.0, "grounded Chrono patch should report penetration");
    expect(grounded.force.z > floating.force.z, "grounded patch should add contact force");
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 3) {
            std::cerr << "Usage: " << argv[0] << " <scenario-dir|scenario.json> [output-dir]\n";
            return 1;
        }
        raftsim::Scenario scenario = raftsim::load_scenario_package(argv[1]);
        assert_validated_grid_views();
        assert_stage_scratch_ownership();
        assert_solver_row_barrier_and_failure_recovery();
        assert_scenario_loads(scenario);
        assert_boundary_flux_diagnostic(scenario);
        assert_solver_is_deterministic(scenario);
        assert_malformed_state_storage_is_rejected(scenario);
        assert_finite_volume_second_order_is_deterministic(scenario);
        assert_finite_volume_cfl_failure_is_bounded(scenario);
        assert_validation_rejects_clipped_or_nonfinite_flow(scenario);
        assert_live_state_can_be_replaced(scenario);
        assert_muscl_scratch_is_not_state(scenario);
        assert_cfl_scan_matches_original();
        assert_large_parallel_rows_match_serial(scenario);
        assert_finite_volume_second_order_is_well_balanced(scenario);
        assert_emergent_step_uses_hydrostatic_flux();
        assert_chrono_coupling_samples_water_and_contact(scenario);
        if (argc == 3) {
            assert_output_can_be_written(scenario, argv[2]);
        }
        if (scenario.cascading.present) {
            std::cout << "cascading_reaches=" << scenario.cascading.reaches.size()
                      << " cascading_drop_transitions=" << scenario.cascading.drop_transitions.size() << "\n";
        }
        std::cout << "raftsim_water_tests passed for " << scenario.scenario_id << "\n";
        raftsim::shutdown_solver_workers();
        raftsim::shutdown_solver_workers();
        raftsim::solver_detail::solver_row_ranges(20, true, [](std::size_t, std::size_t) {
            raftsim::solver_detail::solver_row_ranges(20, true, [](std::size_t, std::size_t) {});
        });
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "raftsim_water_tests: " << exc.what() << "\n";
        return 1;
    }
}
