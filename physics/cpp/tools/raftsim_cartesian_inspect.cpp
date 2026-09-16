// Read-only instantaneous tile-face flux inspection of a completed cook frame.
#include "raftsim_water/cartesian_domain.hpp"
#include "raftsim_water/json.hpp"
#include "raftsim_water/numpy_io.hpp"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>

namespace fs=std::filesystem;
namespace {
void require(bool value,const char* message) { if(!value)throw std::runtime_error(message); }
std::string bytes(const fs::path& path) {
    std::ifstream in(path,std::ios::binary);require(bool(in),"Cannot read manifest");
    return {std::istreambuf_iterator<char>(in),std::istreambuf_iterator<char>()};
}
}
int main(int argc,char** argv) {
    try {
        require(argc>=4,"Usage: raftsim_cartesian_inspect input-manifest frame-directory tile-index [tile-index ...]");
        const fs::path input=fs::absolute(argv[1]),frame=fs::absolute(argv[2]);
        require(bytes(input)==bytes(frame.parent_path()/"input_manifest.json"),"Cook/input manifest mismatch");
        const auto manifest=raftsim::parse_json_file(input.string());
        require(manifest.at("schema").as_string()=="raftsim.cartesian_flow_cook.v1","Unsupported cook schema");
        const auto complete=raftsim::parse_json_file((frame/"complete.json").string());
        require(complete.at("snapshot").as_bool(),"Completed snapshot required");
        const double time=complete.at("time_seconds").as_number();
        require(std::isfinite(time) && time>=0.,"Invalid checkpoint time");
        std::ostringstream expected_frame;expected_frame<<"frame_"<<std::setw(6)<<std::setfill('0')<<complete.at("step").as_int();
        require(frame.filename()==expected_frame.str(),"Checkpoint step/directory mismatch");
        const auto h=raftsim::load_npy_f64((frame/"h.npy").string());
        const auto u=raftsim::load_npy_f64((frame/"u.npy").string());
        const auto v=raftsim::load_npy_f64((frame/"v.npy").string());
        const auto& packages=manifest.at("packages").as_array();
        require(!packages.empty(),"Empty cook");
        std::vector<raftsim::Scenario> scenarios;
        for(std::size_t i=0;i<packages.size();++i) {
            const fs::path name=packages[i].as_string();
            require(name==name.filename() && name!="." && name!="..","Simple package name required");
            auto scenario=raftsim::load_scenario_package((input.parent_path()/name).string());
            const auto& g=scenario.grid;
            for(const auto* field:{&h,&u,&v})
                require(field->nx()==g.nx && field->ny()==packages.size()*g.ny,"Unexpected checkpoint dimensions");
            for(std::size_t r=0;r<g.ny;++r)for(std::size_t c=0;c<g.nx;++c) {
                const auto row=i*g.ny+r;
                require(std::isfinite(h(row,c)) && std::isfinite(u(row,c)) && std::isfinite(v(row,c)) &&
                    h(row,c)>=0. && h(row,c)<=10. && std::hypot(u(row,c),v(row,c))<=20.,"Checkpoint state gate failed");
                scenario.initial.h(r,c)=h(row,c);scenario.initial.u(r,c)=u(row,c);scenario.initial.v(r,c)=v(row,c);
                scenario.initial.eta(r,c)=scenario.bed(r,c)+h(row,c);
                scenario.initial.hu(r,c)=h(row,c)*u(row,c);scenario.initial.hv(r,c)=h(row,c)*v(row,c);
                scenario.initial.wet.values[r*g.nx+c]=h(row,c)>1.e-6;
            }
            scenarios.push_back(std::move(scenario));
        }
        std::set<std::size_t> selected;
        for(int i=3;i<argc;++i) {
            std::size_t consumed=0;const std::string raw=argv[i];
            require(!raw.empty() && raw[0]!='-',"Nonnegative tile index required");
            const auto index=std::stoull(raw,&consumed);
            require(consumed==raw.size() && index<packages.size() && selected.insert(index).second,"Invalid/duplicate tile index");
        }
        raftsim::SolverConfig config;
        config.solver_mode="finite_volume";config.boundary_mode="scenario";config.flux_scheme="hll";
        config.spatial_order=2;config.cfl=.2;config.feature_strength_scale=0.;config.bed_slope_source_scale=1.;
        config.disable_fixture_calibrations=true;config.preserve_initial_mass=false;
        raftsim::CartesianWaterDomain domain(std::move(scenarios),config,time);
        auto unchanged=[&](){
            require(domain.time()==time,"Inspection advanced time");
            for(std::size_t i=0;i<domain.size();++i) {
                const auto& s=domain.tile(i).state();const auto ny=s.h.ny(),nx=s.h.nx();
                for(std::size_t r=0;r<ny;++r)for(std::size_t c=0;c<nx;++c)
                    require(s.h(r,c)==h(i*ny+r,c) && s.u(r,c)==u(i*ny+r,c) && s.v(r,c)==v(i*ny+r,c),"Checkpoint changed during loading/inspection");
            }
        };
        unchanged();
        require(std::abs(domain.total_volume()-complete.at("volume_m3").as_number())<1.e-6,"Checkpoint volume differs from completion record");
        std::ostringstream out;out<<std::setprecision(17);
        out<<"{\"schema\":\"raftsim.cartesian_instantaneous_flux.v1\",\"time_seconds\":"<<time
            <<",\"solver_steps_run\":0,\"state_unchanged\":true,\"tiles\":[";
        bool first=true;double volume=0.,net=0.;
        for(std::size_t i:selected) {
            const auto& tile=domain.tile(i);const auto f=tile.inspect_boundary_mass_fluxes();
            const double local=raftsim::compute_mass(tile.scenario(),tile.state());
            for(double value:{f.west,f.east,f.south,f.north})require(std::isfinite(value),"Nonfinite numerical flux");
            if(!first)out<<',';first=false;
            out<<"{\"tile_index\":"<<i<<",\"volume_m3\":"<<local<<",\"inward_flux_m3s\":["
                <<f.west<<','<<f.east<<','<<f.south<<','<<f.north<<"]}";
            volume+=local;net+=f.west+f.east+f.south+f.north;
        }
        unchanged();
        out<<"],\"selected_volume_m3\":"<<volume<<",\"instantaneous_selected_net_inflow_m3s\":"<<net
            <<",\"settling_accepted\":false,\"playable_integrated\":false}";
        std::cout<<out.str()<<'\n';raftsim::shutdown_solver_workers();return 0;
    } catch(const std::exception& error) {
        raftsim::shutdown_solver_workers();std::cerr<<error.what()<<'\n';return 1;
    }
}
