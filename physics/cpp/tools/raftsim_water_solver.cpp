#include "raftsim_water/solver.hpp"

#include <cmath>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
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
    int steps = -1;
    int frame_interval = 60;
    double cfl = 0.45;
    double dry_tolerance = 1.0e-6;
    double feature_strength_scale = 1.0;
    double roughness_scale = 1.0;
    double bed_slope_source_scale = 0.0;
    bool preserve_initial_mass = true;
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
        << "  --steps <n>                    Fixed steps to run (default: scenario duration / fixed_dt)\n"
        << "  --frame-interval <n>           Save every n solver steps (default: 60)\n"
        << "  --cfl <x>                      Finite-volume CFL target (default: 0.45)\n"
        << "  --dry-tolerance <x>            Wet/dry depth tolerance in meters (default: 1e-6)\n"
        << "  --feature-strength-scale <x>   Scale authored rapid forcing (default: 1.0)\n"
        << "  --roughness-scale <x>          Scale scenario roughness/friction (default: 1.0)\n"
        << "  --bed-slope-source-scale <x>   Scale finite-volume bed slope source term (default: 0.0)\n"
        << "  --no-preserve-initial-mass     Disable reduced-mode global mass correction\n"
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
        config.cfl = args.cfl;
        config.dry_tolerance = args.dry_tolerance;
        config.feature_strength_scale = args.feature_strength_scale;
        config.roughness_scale = args.roughness_scale;
        config.bed_slope_source_scale = args.bed_slope_source_scale;
        config.preserve_initial_mass = args.preserve_initial_mass;
        raftsim::ReducedShallowWaterSolver solver(std::move(scenario), config);
        std::vector<raftsim::Frame> frames = solver.run(steps, args.frame_interval);
        raftsim::ValidationSummary validation = raftsim::validate_frames(solver.scenario(), frames, config);

        fs::path output_root(args.output_dir);
        fs::path run_dir = output_root / solver.scenario().scenario_id;
        raftsim::write_solver_output(solver.scenario(), frames, validation, config, run_dir.string());

        std::cout << "scenario_id=" << solver.scenario().scenario_id << "\n";
        std::cout << "solver=raftsim_water_cpp_v1\n";
        std::cout << "solver_mode=" << config.solver_mode << "\n";
        std::cout << "boundary_mode=" << config.boundary_mode << "\n";
        std::cout << "flux_scheme=" << config.flux_scheme << "\n";
        std::cout << "steps=" << steps << "\n";
        std::cout << "frames=" << frames.size() << "\n";
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
