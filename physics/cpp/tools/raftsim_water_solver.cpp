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
    int steps = -1;
    int frame_interval = 60;
    double feature_strength_scale = 1.0;
};

void print_usage(const char* program) {
    std::cout
        << "Usage: " << program << " --scenario <package-dir|scenario.json> [options]\n"
        << "\n"
        << "Options:\n"
        << "  --output <dir>                 Output root directory (default: outputs/cpp_solver)\n"
        << "  --steps <n>                    Fixed steps to run (default: scenario duration / fixed_dt)\n"
        << "  --frame-interval <n>           Save every n solver steps (default: 60)\n"
        << "  --feature-strength-scale <x>   Scale authored rapid forcing (default: 1.0)\n"
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
        } else if (flag == "--steps") {
            args.steps = parse_int(require_value(flag), flag);
        } else if (flag == "--frame-interval") {
            args.frame_interval = parse_int(require_value(flag), flag);
        } else if (flag == "--feature-strength-scale") {
            args.feature_strength_scale = parse_double(require_value(flag), flag);
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
        config.feature_strength_scale = args.feature_strength_scale;
        raftsim::ReducedShallowWaterSolver solver(std::move(scenario), config);
        std::vector<raftsim::Frame> frames = solver.run(steps, args.frame_interval);
        raftsim::ValidationSummary validation = raftsim::validate_frames(solver.scenario(), frames, config);

        fs::path output_root(args.output_dir);
        fs::path run_dir = output_root / solver.scenario().scenario_id;
        raftsim::write_solver_output(solver.scenario(), frames, validation, run_dir.string());

        std::cout << "scenario_id=" << solver.scenario().scenario_id << "\n";
        std::cout << "solver=raftsim_water_reduced_cpp_v0\n";
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
