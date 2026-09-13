#include "raftsim_water/cartesian_domain.hpp"
#include "raftsim_water/json.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace fs=std::filesystem;
namespace {
void require(bool value,const char* message) { if (!value) throw std::runtime_error(message); }
void write_field(const fs::path& path,const raftsim::CartesianWaterDomain& domain,char field) {
    std::ofstream out(path,std::ios::binary);
    out.exceptions(std::ios::badbit|std::ios::failbit);
    const auto& grid=domain.tile(0).scenario().grid;
    std::string header="{'descr': '<f8', 'fortran_order': False, 'shape': ("+
        std::to_string(domain.size()*grid.ny)+", "+std::to_string(grid.nx)+"), }";
    while ((10+header.size()+1)%64) header+=' ';
    header+='\n';
    require(header.size()<65536,"NPY header too large");
    const char magic[]={char(0x93),'N','U','M','P','Y',1,0};
    const std::uint16_t size=static_cast<std::uint16_t>(header.size());
    out.write(magic,8); out.put(static_cast<char>(size&255)); out.put(static_cast<char>(size>>8));
    out.write(header.data(),header.size());
    for (std::size_t i=0;i<domain.size();++i) {
        const auto& state=domain.tile(i).state();
        const auto& values=field=='h' ? state.h.values() : field=='u' ? state.u.values() : state.v.values();
        out.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(double));
    }
}
}

int main(int argc,char** argv) {
    try {
        require(argc==5,"Usage: raftsim_cartesian_cook manifest.json fresh-output-directory steps frame-interval");
        const fs::path input=fs::absolute(argv[1]), output=fs::absolute(argv[2]);
        const int steps=std::stoi(argv[3]), interval=std::stoi(argv[4]);
        require(steps>0 && interval>0 && !fs::exists(output),"Require positive steps/interval and a fresh output directory");
        const auto manifest=raftsim::parse_json_file(input.string());
        require(manifest.at("schema").as_string()=="raftsim.cartesian_flow_cook.v1","Unsupported Cartesian cook schema");
        const double dt=manifest.at("dt_seconds").as_number();
        require(std::isfinite(dt) && dt>0.,"Invalid cook timestep");
        std::vector<raftsim::Scenario> scenarios;
        for (const auto& package:manifest.at("packages").as_array())
            scenarios.push_back(raftsim::load_scenario_package((input.parent_path()/package.as_string()).string()));
        raftsim::SolverConfig config;
        config.solver_mode="finite_volume"; config.boundary_mode="scenario"; config.flux_scheme="hll";
        config.spatial_order=2; config.cfl=.2; config.feature_strength_scale=0.; config.bed_slope_source_scale=1.;
        config.disable_fixture_calibrations=true; config.preserve_initial_mass=false;
        const double initial_time=manifest.number_or("initial_time_seconds",0.);
        raftsim::CartesianWaterDomain domain(std::move(scenarios),config,initial_time);
        fs::create_directories(output);
        fs::copy_file(input,output/"input_manifest.json");
        // Keep the immutable copied manifest and the original package root:
        // its relative package paths are not relative to the output directory.
        std::ofstream location(output/"input_manifest_path.txt");
        location.exceptions(std::ios::badbit|std::ios::failbit);
        location<<input.generic_string()<<'\n'; location.close();
        std::ofstream progress(output/"progress.jsonl"); progress.exceptions(std::ios::badbit|std::ios::failbit);
        progress<<std::setprecision(17); std::cout<<std::setprecision(17);
        const auto start=std::chrono::steady_clock::now();
        double cumulative_boundary_volume=0., maximum_step_residual=0.;
        const double initial_volume=domain.total_volume();
        double previous_volume=initial_volume;
        auto report=[&](int step,bool save_frame) {
            double depth=0.,speed=0.;
            for (std::size_t i=0;i<domain.size();++i) {
                const auto& state=domain.tile(i).state();
                for (std::size_t j=0;j<state.h.values().size();++j) {
                    const double h=state.h.values()[j],u=state.u.values()[j],v=state.v.values()[j];
                    require(std::isfinite(h) && std::isfinite(u) && std::isfinite(v) && h>=0.,"Nonfinite/negative coupled water state");
                    depth=std::max(depth,h); speed=std::max(speed,std::hypot(u,v));
                }
            }
            const double volume=domain.total_volume();
            const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            std::ostringstream line; line<<std::setprecision(17)<<"{\"step\":"<<step<<",\"time_seconds\":"<<domain.time()
                <<",\"elapsed_wall_seconds\":"<<seconds<<",\"volume_m3\":"<<volume<<",\"maximum_depth_m\":"<<depth
                <<",\"maximum_speed_mps\":"<<speed<<",\"boundary_volume_m3\":"<<cumulative_boundary_volume
                <<",\"conservation_residual_m3\":"<<volume-initial_volume-cumulative_boundary_volume
                <<",\"maximum_step_residual_m3\":"<<maximum_step_residual<<",\"exterior_fluxes\":[";
            bool first=true;
            for (const auto& probe:manifest.at("boundary_probes").as_array()) {
                const auto flux=domain.tile(probe.at("tile_index").as_int()).inspect_boundary_mass_fluxes();
                const std::string edge=probe.at("edge").as_string();
                require(edge=="west" || edge=="east" || edge=="south" || edge=="north","Invalid boundary probe edge");
                if (!first) line<<','; first=false;
                line<<(edge=="west" ? flux.west : edge=="east" ? flux.east : edge=="south" ? flux.south : flux.north);
            }
            line<<"],\"snapshot\":"<<(save_frame ? "true" : "false")<<"}";
            progress<<line.str()<<'\n'; progress.flush(); std::cout<<line.str()<<std::endl;
            require(depth<=10. && speed<=20.,"Coupled cook exceeded existing 10 m depth / 20 m/s speed gates");
            require(maximum_step_residual<=.001*dt,"Coupled cook exceeded 0.001 m3/s step-conservation gate");
            if (save_frame) {
                const auto& grid=domain.tile(0).scenario().grid;
                const auto bytes=domain.size()*grid.nx*grid.ny*3*sizeof(double);
                require(fs::space(output).available>bytes+512ull*1024*1024,"Insufficient disk for frame and safety reserve");
                std::ostringstream name; name<<"frame_"<<std::setw(6)<<std::setfill('0')<<step;
                const auto frame=output/name.str(); fs::create_directory(frame);
                write_field(frame/"h.npy",domain,'h'); write_field(frame/"u.npy",domain,'u'); write_field(frame/"v.npy",domain,'v');
                std::ofstream done(frame/"complete.json"); done.exceptions(std::ios::badbit|std::ios::failbit);
                done<<line.str()<<'\n';
            }
        };
        report(0,true);
        for (int step=1;step<=steps;++step) {
            domain.step_with_flux_audit(dt);
            for (std::size_t i=0;i<domain.size();++i) {
                const auto& state=domain.tile(i).state();
                for (std::size_t j=0;j<state.h.size();++j) {
                    const double h=state.h.values()[j],u=state.u.values()[j],v=state.v.values()[j];
                    if (!(std::isfinite(h) && std::isfinite(u) && std::isfinite(v) && h>=0. && h<=10. && u*u+v*v<=400.)) {
                        const auto& scenario=domain.tile(i).scenario();
                        const auto& grid=scenario.grid;
                        std::ofstream failure(output/"failure.txt"); failure.exceptions(std::ios::badbit|std::ios::failbit);
                        failure<<std::setprecision(17)<<"state gate failed at step="<<step<<" time="<<domain.time()
                            <<" tile="<<i<<" cell="<<j<<" x="<<grid.origin_x+(j%grid.nx)*grid.dx
                            <<" y="<<grid.origin_y+(j/grid.nx)*grid.dy<<" bed="<<scenario.bed.values()[j]
                            <<" initial_h="<<scenario.initial.h.values()[j]<<" h="<<h<<" u="<<u<<" v="<<v<<'\n';
                        failure.close();
                        write_field(output/"failure_h.npy",domain,'h');
                        write_field(output/"failure_u.npy",domain,'u');
                        write_field(output/"failure_v.npy",domain,'v');
                        throw std::runtime_error("Coupled state failed finite/depth/speed gates; full failure state retained");
                    }
                }
            }
            cumulative_boundary_volume+=domain.last_boundary_volume_change();
            const double volume=domain.total_volume();
            maximum_step_residual=std::max(maximum_step_residual,std::abs(volume-previous_volume-domain.last_boundary_volume_change()));
            previous_volume=volume;
            if (step%10==0 || step%interval==0 || step==steps)
                report(step,step%interval==0 || step==steps);
        }
        std::ofstream done(output/"completed.json"); done.exceptions(std::ios::badbit|std::ios::failbit);
        done<<"{\"completed\":true,\"settling_accepted\":false,\"normal_map_integrated\":false}\n";
        raftsim::shutdown_solver_workers(); return 0;
    } catch (const std::exception& error) {
        raftsim::shutdown_solver_workers(); std::cerr<<error.what()<<'\n'; return 1;
    }
}
