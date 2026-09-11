#include "raftsim_water/solver.hpp"

#include <cmath>
#include <chrono>
#include <algorithm>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace fs = std::filesystem;

namespace {

struct CliArgs {
    std::string scenario_dir;
    std::string output_dir = "outputs/cpp_solver";
    std::string solver_mode = "reduced";
    std::string boundary_mode = "scenario";
    std::string flux_scheme = "rusanov";
    int spatial_order = 2;
    int steps = -1;
    int frame_interval = 60;
    double cfl = 0.45;
    double dry_tolerance = 1.0e-6;
    double feature_strength_scale = 1.0;
    double roughness_scale = 1.0;
    double bed_slope_source_scale = 0.0;
    bool preserve_initial_mass = true;
    bool disable_fixture_calibrations = false;
    bool inspect_boundary_flux = false;
    bool inspect_face_fluxes = false;
    bool progress = false;
    double experimental_west_discharge_m3s = -1.0;
    bool experimental_west_supercritical_stage = false;
};

void print_usage(const char* program) {
    std::cout
        << "Usage: " << program << " --scenario <package-dir|scenario.json> [options]\n"
        << "\n"
        << "Options:\n"
        << "  --output <dir>                 Output root directory (default: outputs/cpp_solver)\n"
        << "  --solver-mode <mode>           reduced or finite_volume (default: reduced)\n"
        << "  --boundary-mode <mode>         scenario or pyclaw (default: scenario)\n"
        << "  --flux-scheme <scheme>         rusanov, hll, or roe (default: rusanov)\n"
        << "  --spatial-order <n>            Finite-volume spatial order: 2 = MUSCL, 1 = legacy (default: 2)\n"
        << "  --steps <n>                    Fixed steps to run (default: scenario duration / fixed_dt)\n"
        << "  --frame-interval <n>           Save every n solver steps (default: 60)\n"
        << "  --cfl <x>                      Finite-volume CFL target (default: 0.45)\n"
        << "  --dry-tolerance <x>            Wet/dry depth tolerance in meters (default: 1e-6)\n"
        << "  --feature-strength-scale <x>   Scale authored rapid forcing (default: 1.0)\n"
        << "  --roughness-scale <x>          Scale scenario roughness/friction (default: 1.0)\n"
        << "  --bed-slope-source-scale <x>   Scale finite-volume bed slope source term (default: 0.0)\n"
        << "  --no-preserve-initial-mass     Disable reduced-mode global mass correction\n"
        << "  --disable-fixture-calibrations Run only base dynamics, without fixture-specific treatments\n"
        << "  --inspect-boundary-flux        Print initial-state face flux JSON and exit without stepping/writing\n"
        << "  --inspect-face-fluxes          Print all exact numerical mass fluxes as JSON, without stepping\n"
        << "  --progress                     Log elapsed simulation time and maximum depth at saved frames\n"
        << "  --experimental-west-discharge <m3/s>  Offline subcritical constant-Q inlet trial (default: disabled)\n"
        << "  --experimental-west-supercritical-stage  Use external stage on supercritical constant-Q faces\n"
        << "  --help                         Show this help\n";
}

int parse_int(const std::string& value, const std::string& flag) {
    try {
        return std::stoi(value);
    } catch (const std::exception&) {
        throw std::runtime_error("Invalid integer for " + flag + ": " + value);
    }
}

double parse_double(const std::string& value, const std::string& flag) {
    try {
        return std::stod(value);
    } catch (const std::exception&) {
        throw std::runtime_error("Invalid number for " + flag + ": " + value);
    }
}

CliArgs parse_args(int argc, char** argv) {
    CliArgs args;
    for (int i = 1; i < argc; ++i) {
        std::string flag = argv[i];
        auto require_value = [&](const std::string& name) -> std::string {
            if (i + 1 >= argc) {
                throw std::runtime_error("Missing value for " + name);
            }
            return argv[++i];
        };

        if (flag == "--help" || flag == "-h") {
            print_usage(argv[0]);
            std::exit(0);
        } else if (flag == "--scenario") {
            args.scenario_dir = require_value(flag);
        } else if (flag == "--output") {
            args.output_dir = require_value(flag);
        } else if (flag == "--solver-mode") {
            args.solver_mode = require_value(flag);
        } else if (flag == "--boundary-mode") {
            args.boundary_mode = require_value(flag);
        } else if (flag == "--flux-scheme") {
            args.flux_scheme = require_value(flag);
        } else if (flag == "--spatial-order") {
            args.spatial_order = parse_int(require_value(flag), flag);
        } else if (flag == "--steps") {
            args.steps = parse_int(require_value(flag), flag);
        } else if (flag == "--frame-interval") {
            args.frame_interval = parse_int(require_value(flag), flag);
        } else if (flag == "--cfl") {
            args.cfl = parse_double(require_value(flag), flag);
        } else if (flag == "--dry-tolerance") {
            args.dry_tolerance = parse_double(require_value(flag), flag);
        } else if (flag == "--feature-strength-scale") {
            args.feature_strength_scale = parse_double(require_value(flag), flag);
        } else if (flag == "--roughness-scale") {
            args.roughness_scale = parse_double(require_value(flag), flag);
        } else if (flag == "--bed-slope-source-scale") {
            args.bed_slope_source_scale = parse_double(require_value(flag), flag);
        } else if (flag == "--no-preserve-initial-mass") {
            args.preserve_initial_mass = false;
        } else if (flag == "--disable-fixture-calibrations") {
            args.disable_fixture_calibrations = true;
        } else if (flag == "--inspect-boundary-flux") {
            args.inspect_boundary_flux = true;
        } else if (flag == "--inspect-face-fluxes") {
            args.inspect_face_fluxes = true;
        } else if (flag == "--progress") {
            args.progress = true;
        } else if (flag == "--experimental-west-supercritical-stage") {
            args.experimental_west_supercritical_stage = true;
        } else if (flag == "--experimental-west-discharge") {
            args.experimental_west_discharge_m3s = parse_double(require_value(flag), flag);
            if (!std::isfinite(args.experimental_west_discharge_m3s) || args.experimental_west_discharge_m3s < 0.0)
                throw std::runtime_error("Experimental west discharge must be finite and nonnegative.");
        } else {
            throw std::runtime_error("Unknown argument: " + flag);
        }
    }
    if (args.scenario_dir.empty()) {
        throw std::runtime_error("--scenario is required.");
    }
    if (args.steps < -1) {
        throw std::runtime_error("--steps must be non-negative.");
    }
    if (args.frame_interval < 1) {
        throw std::runtime_error("--frame-interval must be at least 1.");
    }
    if (args.solver_mode != "reduced" && args.solver_mode != "finite_volume") {
        throw std::runtime_error("--solver-mode must be reduced or finite_volume.");
    }
    if (args.boundary_mode != "scenario" && args.boundary_mode != "pyclaw") {
        throw std::runtime_error("--boundary-mode must be scenario or pyclaw.");
    }
    if (args.flux_scheme != "rusanov" && args.flux_scheme != "hll" && args.flux_scheme != "roe") {
        throw std::runtime_error("--flux-scheme must be rusanov, hll, or roe.");
    }
    if (args.spatial_order != 1 && args.spatial_order != 2) {
        throw std::runtime_error("--spatial-order must be 1 or 2.");
    }
    if (args.cfl <= 0.0) {
        throw std::runtime_error("--cfl must be positive.");
    }
    if (args.dry_tolerance < 0.0) {
        throw std::runtime_error("--dry-tolerance must be non-negative.");
    }
    return args;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        CliArgs args = parse_args(argc, argv);
        raftsim::Scenario scenario = raftsim::load_scenario_package(args.scenario_dir);
        int steps = args.steps;
        if (steps < 0) {
            steps = static_cast<int>(std::ceil(scenario.duration / scenario.fixed_dt));
        }

        raftsim::SolverConfig config;
        config.solver_mode = args.solver_mode;
        config.boundary_mode = args.boundary_mode;
        config.flux_scheme = args.flux_scheme;
        config.spatial_order = args.spatial_order;
        config.cfl = args.cfl;
        config.dry_tolerance = args.dry_tolerance;
        config.feature_strength_scale = args.feature_strength_scale;
        config.roughness_scale = args.roughness_scale;
        config.bed_slope_source_scale = args.bed_slope_source_scale;
        config.preserve_initial_mass = args.preserve_initial_mass;
        config.disable_fixture_calibrations = args.disable_fixture_calibrations;
        config.experimental_west_discharge_m3s = args.experimental_west_discharge_m3s;
        config.experimental_west_supercritical_stage = args.experimental_west_supercritical_stage;
        raftsim::ReducedShallowWaterSolver solver(std::move(scenario), config);
        if (args.inspect_face_fluxes) {
            const auto flux = solver.inspect_numerical_mass_flux_grid();
            const auto& grid = solver.scenario().grid;
            std::cout << std::setprecision(17)
                      << "{\"units\":\"m2/s\",\"sign\":\"positive_grid_axis\",\"layout\":\"row_major\","
                      << "\"nx\":" << grid.nx << ",\"ny\":" << grid.ny
                      << ",\"dx_m\":" << grid.dx << ",\"dy_m\":" << grid.dy;
            auto write_array = [](const char* name, const raftsim::Array2D& array) {
                std::cout << ",\"" << name << "\":[";
                bool first = true;
                for (double value : array.values()) {
                    if (!first) std::cout << ',';
                    std::cout << value;
                    first = false;
                }
                std::cout << ']';
            };
            write_array("x_faces", flux.x_faces);
            write_array("y_faces", flux.y_faces);
            std::cout << "}\n";
            return 0;
        }
        if (args.inspect_boundary_flux) {
            const auto flux = solver.inspect_boundary_mass_fluxes();
            std::cout << std::setprecision(17)
                      << "{\"units\":\"m3/s\",\"sign\":\"positive_into_domain\","
                      << "\"west\":" << flux.west << ",\"east\":" << flux.east
                      << ",\"south\":" << flux.south << ",\"north\":" << flux.north
                      << ",\"net\":" << flux.west + flux.east + flux.south + flux.north << "}\n";
            return 0;
        }
        const auto solve_start = std::chrono::steady_clock::now();
        std::vector<raftsim::Frame> frames;
        if (!args.progress) {
            frames = solver.run(steps, args.frame_interval);
        } else {
            frames.push_back(solver.make_frame());
            for (int index = 1; index <= steps; ++index) {
                solver.step(solver.scenario().fixed_dt);
                if (index == 1 || index % args.frame_interval == 0 || index == steps) {
                    const auto& depth = solver.state().h.values();
                    std::cerr << "progress step=" << index << "/" << steps
                              << " time=" << solver.time() << " max_depth="
                              << *std::max_element(depth.begin(), depth.end()) << std::endl;
                }
                if (index % args.frame_interval == 0 || index == steps) frames.push_back(solver.make_frame());
            }
        }
        const auto solve_end = std::chrono::steady_clock::now();
        raftsim::ValidationSummary validation = raftsim::validate_frames(solver.scenario(), frames, config);

        fs::path output_root(args.output_dir);
        fs::path run_dir = output_root / solver.scenario().scenario_id;
        const auto export_start = std::chrono::steady_clock::now();
        raftsim::write_solver_output(solver.scenario(), frames, validation, config, run_dir.string());
        const auto export_end = std::chrono::steady_clock::now();

        std::cout << "scenario_id=" << solver.scenario().scenario_id << "\n";
        std::cout << "solver=raftsim_water_cpp_v1\n";
        std::cout << "solver_mode=" << config.solver_mode << "\n";
        std::cout << "boundary_mode=" << config.boundary_mode << "\n";
        std::cout << "flux_scheme=" << config.flux_scheme << "\n";
        std::cout << "spatial_order=" << config.spatial_order << "\n";
        std::cout << "disable_fixture_calibrations="
                  << (config.disable_fixture_calibrations ? "true" : "false") << "\n";
        std::cout << "steps=" << steps << "\n";
        std::cout << "frames=" << frames.size() << "\n";
        // Separate arithmetic/frame capture from CSV export. Whole-process
        // wall time can hide a solver speedup behind repeated file formatting.
        std::cout << "solve_and_capture_seconds="
                  << std::chrono::duration<double>(solve_end - solve_start).count() << "\n";
        std::cout << "export_seconds="
                  << std::chrono::duration<double>(export_end - export_start).count() << "\n";
        std::cout << "output=" << run_dir.string() << "\n";
        std::cout << "validation_passed=" << (validation.passed ? "true" : "false") << "\n";
        std::cout << "mass_relative_drift=" << validation.mass_relative_drift << "\n";
        std::cout << "max_velocity=" << validation.max_velocity << "\n";
        return validation.passed ? 0 : 2;
    } catch (const std::exception& exc) {
        std::cerr << "raftsim_water_solver: " << exc.what() << "\n";
        return 1;
    }
}
