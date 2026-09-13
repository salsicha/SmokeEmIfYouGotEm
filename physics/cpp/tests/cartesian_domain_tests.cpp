#include "raftsim_water/cartesian_domain.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
void expect(bool value, const char* message) { if (!value) throw std::runtime_error(message); }

raftsim::Scenario fixture(bool lake) {
    raftsim::Scenario s;
    s.scenario_id = "cartesian_muscl_equivalence";
    s.scenario_type = "analytic_validation";
    s.grid = {32,24,1.,1.,-5432.5,3600.5};
    s.fixed_dt = .005;
    s.roughness = .035;
    s.bed = raftsim::Array2D(24,32);
    auto& state = s.initial;
    state.h = state.eta = state.u = state.v = state.hu = state.hv = raftsim::Array2D(24,32);
    state.wet.nx = 32; state.wet.ny = 24; state.wet.values.resize(32*24);
    for (std::size_t r=0;r<24;++r) for (std::size_t c=0;c<32;++c) {
        s.bed(r,c) = 1.+.35*std::sin(c*.24)+.21*std::cos(r*.32)+(c>26 ? 2. : 0.);
        const double h = lake ? std::max(0.,2.2-s.bed(r,c)) : (c>26 ? 0. : .8+.15*std::sin(c*.21)+.05*std::cos(r*.31));
        state.h(r,c) = !lake && r==10 && c==15 ? 5.e-9 : h;
        state.eta(r,c) = s.bed(r,c)+state.h(r,c);
        state.u(r,c) = lake ? 0. : .3+.03*std::sin(r*.31);
        state.v(r,c) = lake ? 0. : -.2+.025*std::cos(c*.23);
        state.hu(r,c) = state.h(r,c)*state.u(r,c);
        state.hv(r,c) = state.h(r,c)*state.v(r,c);
        state.wet.values[r*32+c] = state.h(r,c)>1.e-6;
    }
    for (const char* edge : {"west","east","south","north"}) {
        raftsim::BoundaryCondition b; b.edge=edge; b.kind="wall"; s.boundaries.push_back(b);
    }
    return s;
}

std::vector<raftsim::Scenario> split(const raftsim::Scenario& full, std::size_t across=2) {
    std::vector<raftsim::Scenario> parts;
    const std::size_t nx=full.grid.nx/across,ny=full.grid.ny/across;
    for (std::size_t ty=0;ty<across;++ty) for (std::size_t tx=0;tx<across;++tx) {
        auto part = full;
        part.grid.nx=nx; part.grid.ny=ny;
        part.grid.origin_x+=tx*nx*full.grid.dx; part.grid.origin_y+=ty*ny*full.grid.dy;
        auto crop = [&](const raftsim::Array2D& input) {
            raftsim::Array2D output(ny,nx);
            for (std::size_t r=0;r<ny;++r) for (std::size_t c=0;c<nx;++c) output(r,c)=input(r+ty*ny,c+tx*nx);
            return output;
        };
        part.bed=crop(full.bed);
        part.initial.h=crop(full.initial.h); part.initial.eta=crop(full.initial.eta);
        part.initial.u=crop(full.initial.u); part.initial.v=crop(full.initial.v);
        part.initial.hu=crop(full.initial.hu); part.initial.hv=crop(full.initial.hv);
        part.initial.wet.nx=nx; part.initial.wet.ny=ny; part.initial.wet.values.resize(nx*ny);
        for (std::size_t r=0;r<ny;++r) for (std::size_t c=0;c<nx;++c)
            part.initial.wet.values[r*nx+c]=full.initial.wet(r+ty*ny,c+tx*nx);
        for (auto& boundary : part.boundaries) {
            if (boundary.kind != "ghost" && boundary.kind != "discharge_profile") continue;
            const bool x_edge=boundary.edge=="west" || boundary.edge=="east";
            const std::size_t count=x_edge ? ny : nx;
            const std::size_t full_count=x_edge ? full.grid.ny : full.grid.nx;
            const std::size_t offset=x_edge ? ty*ny : tx*nx;
            auto original=boundary.ghost_cells;
            boundary.ghost_cells.clear();
            for (std::size_t layer=0;layer<2;++layer) for (std::size_t i=0;i<count;++i)
                boundary.ghost_cells.push_back(original.at(layer*full_count+offset+i));
        }
        parts.push_back(std::move(part));
    }
    return parts;
}

raftsim::SolverConfig config() {
    raftsim::SolverConfig c;
    c.solver_mode="finite_volume"; c.flux_scheme="hll"; c.spatial_order=2;
    c.disable_fixture_calibrations=true; c.feature_strength_scale=0.;
    c.preserve_initial_mass=false; c.bed_slope_source_scale=1.; c.cfl=.2;
    return c;
}

void compare(const raftsim::Scenario& source, std::size_t across, bool reverse,
             int steps, bool closed) {
    raftsim::ReducedShallowWaterSolver whole(source,config());
    auto parts=split(source,across);
    if (reverse) std::reverse(parts.begin(),parts.end());
    raftsim::CartesianWaterDomain domain(std::move(parts),config());
    const double initial_volume=raftsim::compute_mass(whole.scenario(),whole.state());
    double error=0., flux_error=0.;
    for (int step=0;step<steps;++step) {
        whole.step(.005); domain.step(.005);
        expect(domain.time()==whole.time(),"tile clock differs from whole domain");
        const auto whole_faces=whole.inspect_numerical_mass_flux_grid();
        for (std::size_t tile=0;tile<domain.size();++tile) {
            const auto& state=domain.tile(tile).state();
            const auto faces=domain.tile(tile).inspect_numerical_mass_flux_grid();
            const auto& grid=domain.tile(tile).scenario().grid;
            const std::size_t ox=std::llround((grid.origin_x-source.grid.origin_x)/source.grid.dx);
            const std::size_t oy=std::llround((grid.origin_y-source.grid.origin_y)/source.grid.dy);
            for (std::size_t r=0;r<grid.ny;++r) for (std::size_t c=0;c<grid.nx;++c) {
                expect(std::isfinite(state.h(r,c)) && std::isfinite(state.u(r,c)) && std::isfinite(state.v(r,c)) &&
                    std::isfinite(whole.state().h(r+oy,c+ox)) && std::isfinite(whole.state().u(r+oy,c+ox)) &&
                    std::isfinite(whole.state().v(r+oy,c+ox)),"nonfinite state in partition comparison");
                error=std::max(error,std::abs(state.h(r,c)-whole.state().h(r+oy,c+ox)));
                error=std::max(error,std::abs(state.u(r,c)-whole.state().u(r+oy,c+ox)));
                error=std::max(error,std::abs(state.v(r,c)-whole.state().v(r+oy,c+ox)));
                expect(domain.tile(tile).scenario().bed(r,c)==source.bed(r+oy,c+ox),"source bed changed");
            }
            for (std::size_t r=0;r<grid.ny;++r) for (std::size_t c=0;c<=grid.nx;++c) {
                expect(std::isfinite(faces.x_faces(r,c)) && std::isfinite(whole_faces.x_faces(r+oy,c+ox)),
                    "nonfinite X face flux in partition comparison");
                flux_error=std::max(flux_error,std::abs(faces.x_faces(r,c)-whole_faces.x_faces(r+oy,c+ox)));
            }
            for (std::size_t r=0;r<=grid.ny;++r) for (std::size_t c=0;c<grid.nx;++c) {
                expect(std::isfinite(faces.y_faces(r,c)) && std::isfinite(whole_faces.y_faces(r+oy,c+ox)),
                    "nonfinite Y face flux in partition comparison");
                flux_error=std::max(flux_error,std::abs(faces.y_faces(r,c)-whole_faces.y_faces(r+oy,c+ox)));
            }
        }
    }
    std::cout << "source=" << source.scenario_id << " tiles=" << domain.size() << " reverse=" << reverse
              << " max_state_error=" << error << " max_face_flux_error=" << flux_error
              << " volume_drift=" << domain.total_volume()-initial_volume
              << " split_unsplit_volume_difference=" << domain.total_volume()-raftsim::compute_mass(whole.scenario(),whole.state()) << '\n';
    expect(error<2.e-12,"tiled RK2 state does not reproduce unsplit MUSCL");
    expect(flux_error<2.e-12,"tiled interface flux differs from unsplit MUSCL");
    if (closed) expect(std::abs(domain.total_volume()-initial_volume)<1.e-8,"closed tiled domain changed mass");
    expect(std::abs(domain.total_volume()-raftsim::compute_mass(whole.scenario(),whole.state()))<1.e-8,
        "tiled volume differs from unsplit volume");
}

void equivalence(bool lake, std::size_t across=2, bool reverse=false) {
    auto source=fixture(lake);
    source.scenario_id+=lake ? "_lake" : "_moving";
    source.grid.dy=.75; // Non-square metric cells must preserve both flux axes.
    compare(source,across,reverse,50,true);
}

// This exercises the numerical partition on actual source geometry. Fixed
// exterior states are a short kernel diagnostic, NOT a settled river solution.
void source_package_equivalence(const char* package) {
    const auto original=raftsim::load_scenario_package(package);
    constexpr std::size_t ox=100, oy=32, size=256;
    expect(original.grid.nx>=ox+size+2 && original.grid.ny>=oy+size+2,
        "source package lacks two exterior ghost layers around diagnostic crop");
    auto source=original;
    source.scenario_id+="_source_exact_partition_diagnostic";
    source.grid.nx=source.grid.ny=size;
    source.grid.origin_x+=ox*source.grid.dx; source.grid.origin_y+=oy*source.grid.dy;
    auto crop=[&](const raftsim::Array2D& input) {
        raftsim::Array2D output(size,size);
        for (std::size_t r=0;r<size;++r) for (std::size_t c=0;c<size;++c)
            output(r,c)=input(r+oy,c+ox);
        return output;
    };
    source.bed=crop(original.bed);
    source.initial.h=crop(original.initial.h); source.initial.eta=crop(original.initial.eta);
    source.initial.u=crop(original.initial.u); source.initial.v=crop(original.initial.v);
    source.initial.hu=crop(original.initial.hu); source.initial.hv=crop(original.initial.hv);
    source.initial.wet.nx=source.initial.wet.ny=size; source.initial.wet.values.resize(size*size);
    for (std::size_t r=0;r<size;++r) for (std::size_t c=0;c<size;++c)
        source.initial.wet.values[r*size+c]=original.initial.wet(r+oy,c+ox);
    source.boundaries.clear();
    for (const char* edge : {"west","east","south","north"}) {
        raftsim::BoundaryCondition b; b.edge=edge; b.kind="ghost";
        for (std::size_t layer=0;layer<2;++layer) for (std::size_t i=0;i<size;++i) {
            const std::size_t r=b.edge=="south" ? oy-1-layer : b.edge=="north" ? oy+size+layer : oy+i;
            const std::size_t c=b.edge=="west" ? ox-1-layer : b.edge=="east" ? ox+size+layer : ox+i;
            b.ghost_cells.push_back({original.bed(r,c),original.initial.h(r,c),
                original.initial.u(r,c),original.initial.v(r,c)});
        }
        source.boundaries.push_back(std::move(b));
    }
    compare(source,4,false,10,false);
}

void profiles_and_rejections() {
    auto s=fixture(false);
    for (double sign : {-1.,1.}) {
        for (std::size_t r=0;r<24;++r) for (std::size_t c=0;c<32;++c) {
            s.bed(r,c)=0.; s.initial.h(r,c)=2.; s.initial.u(r,c)=sign*.3; s.initial.v(r,c)=sign*.5;
        }
        for (auto& b:s.boundaries) {
            b.kind="ghost";
            b.ghost_cells.assign(2*((b.edge=="west" || b.edge=="east") ? 24 : 32),{0.,2.,sign*.3,sign*.5});
        }
        raftsim::ReducedShallowWaterSolver solver(s,config());
        const auto flux=solver.inspect_boundary_mass_fluxes();
        expect(std::abs(flux.west-sign*.6*24)<1.e-12 && std::abs(flux.east+sign*.6*24)<1.e-12,
            "east/west profiles do not admit signed discharge");
        expect(std::abs(flux.south-sign*32)<1.e-12 && std::abs(flux.north+sign*32)<1.e-12,
            "north/south profiles do not admit signed discharge");
        solver.step(.005);
        expect(std::abs(solver.state().h(0,0)-2.)<1.e-12,"uniform open flow changed depth");
    }
    auto reject=[&](auto operation,const char* message) { bool failed=false; try { operation(); } catch (const std::exception&) { failed=true; } expect(failed,message); };
    auto bad=s; bad.boundaries[0].ghost_cells.pop_back();
    reject([&]{raftsim::ReducedShallowWaterSolver solver(bad,config());},"short ghost profile accepted");
    bad=s; bad.boundaries[0].ghost_cells[0].h=-1.;
    reject([&]{raftsim::ReducedShallowWaterSolver solver(bad,config());},"negative ghost depth accepted");
    auto c=config(); c.spatial_order=1;
    reject([&]{raftsim::ReducedShallowWaterSolver solver(s,c);},"unsupported first-order ghost mode accepted");
    auto parts=split(fixture(false)); parts[1].grid.origin_x+=.5;
    reject([&]{raftsim::CartesianWaterDomain domain(parts,config());},"unaligned tiles accepted");
    parts=split(fixture(false)); parts.push_back(parts.front());
    reject([&]{raftsim::CartesianWaterDomain domain(parts,config());},"duplicate tile accepted");
    std::cout << "signed four-edge profiles and invalid-input checks passed\n";
}

void discharge_profiles() {
    auto s=fixture(false);
    s.scenario_id="four_edge_prescribed_discharge";
    for (std::size_t r=0;r<s.grid.ny;++r) for (std::size_t c=0;c<s.grid.nx;++c) {
        s.bed(r,c)=0.; s.initial.h(r,c)=2.; s.initial.u(r,c)=s.initial.v(r,c)=0.;
    }
    double expected=0.;
    for (auto& b:s.boundaries) {
        b.kind="discharge_profile";
        const bool x=b.edge=="west" || b.edge=="east";
        const double sign=b.edge=="west" || b.edge=="south" ? 1. : -1.;
        const std::size_t count=x ? s.grid.ny : s.grid.nx;
        b.ghost_cells.clear();
        for (std::size_t layer=0;layer<2;++layer) for (std::size_t i=0;i<count;++i) {
            const double normal=i%7==0 ? 0. : sign*(.2+.001*i);
            b.ghost_cells.push_back({0.,2.,x ? normal : -.07,x ? .09 : normal});
            if (layer==0) expected+=2.*sign*normal*(x ? s.grid.dy : s.grid.dx);
        }
    }
    raftsim::ReducedShallowWaterSolver solver(s,config());
    const double initial=raftsim::compute_mass(s,solver.state());
    const auto flux=solver.inspect_boundary_mass_fluxes();
    expect(std::abs(flux.west+flux.east+flux.south+flux.north-expected)<1.e-12,
        "four-edge prescribed physical flux does not match authored total");
    solver.step(.001);
    expect(std::abs(raftsim::compute_mass(s,solver.state())-initial-.001*expected)<1.e-9,
        "RK2 four-edge inlet did not conserve exact imposed volume");
    raftsim::CartesianWaterDomain audited(split(s,4),config());
    const double before=audited.total_volume();
    audited.step_with_flux_audit(.1); // Deliberately forces multiple CFL substeps.
    expect(std::abs(audited.last_boundary_volume_change()-.1*expected)<1.e-12,
        "audited RK2 exterior flux includes internal tile interfaces or has wrong time weighting");
    expect(std::abs(audited.total_volume()-before-audited.last_boundary_volume_change())<1.e-9,
        "audited RK2 exterior flux does not explain actual volume change");
    compare(s,4,false,10,false);
    bool rejected=false;
    s.boundaries[0].ghost_cells[1].u=-1.;
    try { raftsim::ReducedShallowWaterSolver invalid(s,config()); } catch (const std::exception&) { rejected=true; }
    expect(rejected,"outward prescribed inflow profile accepted");
    std::cout << "four-edge discharge total=" << expected << " exact-volume and partition checks passed\n";
}

void checkpoint_continuation() {
    for (bool lake : {false,true}) {
        auto original=split(fixture(lake),4);
        raftsim::CartesianWaterDomain uninterrupted(original,config());
        for (int step=0;step<37;++step) uninterrupted.step_with_flux_audit(.005);
        auto checkpoint=original;
        for (std::size_t i=0;i<checkpoint.size();++i)
            checkpoint[i].initial=uninterrupted.tile(i).state();
        raftsim::CartesianWaterDomain restarted(checkpoint,config(),uninterrupted.time());
        const auto compare_state=[&]() {
            expect(restarted.time()==uninterrupted.time(),"checkpoint clock was reset");
            expect(restarted.total_volume()==uninterrupted.total_volume(),"checkpoint changed volume");
            for (std::size_t i=0;i<checkpoint.size();++i) {
                const auto& a=uninterrupted.tile(i).state(); const auto& b=restarted.tile(i).state();
                expect(a.h.values()==b.h.values() && a.u.values()==b.u.values() && a.v.values()==b.v.values() &&
                    a.hu.values()==b.hu.values() && a.hv.values()==b.hv.values() && a.eta.values()==b.eta.values() &&
                    a.wet.values==b.wet.values,"checkpoint changed state or continued evolution");
                const auto af=uninterrupted.tile(i).inspect_numerical_mass_flux_grid();
                const auto bf=restarted.tile(i).inspect_numerical_mass_flux_grid();
                expect(af.x_faces.values()==bf.x_faces.values() && af.y_faces.values()==bf.y_faces.values(),
                    "checkpoint changed numerical face fluxes");
            }
        };
        compare_state();
        for (int step=0;step<50;++step) {
            uninterrupted.step_with_flux_audit(.005); restarted.step_with_flux_audit(.005);
            compare_state();
            expect(uninterrupted.last_boundary_volume_change()==restarted.last_boundary_volume_change(),
                "checkpoint changed audited boundary volume");
        }
        for (double invalid : {-1.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}) {
            bool rejected=false;
            try { raftsim::CartesianWaterDomain bad(checkpoint,config(),invalid); }
            catch (const std::exception&) { rejected=true; }
            expect(rejected,"invalid checkpoint clock accepted");
        }
    }
    std::cout << "16-tile wet/dry moving and lake checkpoint state, clock, face fluxes and 50-step continuation bit-exact\n";
}

void mixed_regime_discharge_profiles() {
    for (const std::string edge : {"west","east","south","north"}) {
        auto s=fixture(false);
        const bool x=edge=="west" || edge=="east";
        const double sign=edge=="west" || edge=="south" ? 1. : -1.;
        const double u=x ? sign*6. : .2, v=x ? .2 : sign*6.;
        for (std::size_t r=0;r<s.grid.ny;++r) for (std::size_t c=0;c<s.grid.nx;++c) {
            s.bed(r,c)=0.; s.initial.h(r,c)=.5; s.initial.u(r,c)=u; s.initial.v(r,c)=v;
        }
        for (auto& b:s.boundaries) {
            b.kind=b.edge==edge ? "discharge_profile" : "ghost";
            b.ghost_cells.assign(2*((b.edge=="west" || b.edge=="east") ? s.grid.ny : s.grid.nx),{0.,.5,u,v});
        }
        auto c=config(); c.roughness_scale=0.;
        raftsim::ReducedShallowWaterSolver uniform(s,c);
        uniform.step(.005);
        for (std::size_t r=0;r<s.grid.ny;++r) for (std::size_t col=0;col<s.grid.nx;++col)
            expect(std::abs(uniform.state().h(r,col)-.5)<1.e-12 &&
                std::abs(uniform.state().u(r,col)-u)<1.e-12 && std::abs(uniform.state().v(r,col)-v)<1.e-12,
                "mixed-regime prescribed face failed uniform supercritical flow");
        for (std::size_t r=0;r<s.grid.ny;++r) for (std::size_t col=0;col<s.grid.nx;++col) {
            s.initial.h(r,col)=0.; s.initial.u(r,col)=s.initial.v(r,col)=0.;
        }
        for (auto& b:s.boundaries) if (b.edge!=edge) { b.kind="wall"; b.ghost_cells.clear(); }
        raftsim::ReducedShallowWaterSolver dry(s,c);
        dry.step(.001);
        const double expected=.001*3.*(x ? s.grid.ny : s.grid.nx);
        expect(std::abs(raftsim::compute_mass(s,dry.state())-expected)<1.e-10,
            "dry prescribed inlet failed to conserve injected water");
    }
    std::cout << "all four supercritical and initially dry discharge inlets passed\n";
}
}

int main(int argc, char** argv) {
    try {
        equivalence(true); equivalence(false); equivalence(false,4); equivalence(false,4,true);
        profiles_and_rejections();
        discharge_profiles();
        mixed_regime_discharge_profiles();
        checkpoint_continuation();
        if (argc>1) source_package_equivalence(argv[1]);
        raftsim::shutdown_solver_workers();
        std::cout << "Cartesian domain tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        raftsim::shutdown_solver_workers();
        std::cerr << error.what() << '\n'; return 1;
    }
}
