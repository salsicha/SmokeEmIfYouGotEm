#include "raftsim_water/solver.hpp"

#include <algorithm>
#include <cmath>
#include <exception>
#include <filesystem>
#include <iostream>
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

void assert_scenario_loads(const raftsim::Scenario& scenario) {
    expect(!scenario.scenario_id.empty(), "scenario id is empty");
    expect(scenario.grid.nx >= 2 && scenario.grid.ny >= 2, "grid too small");
    expect(scenario.bed.nx() == scenario.grid.nx, "bed nx mismatch");
    expect(scenario.initial.h.ny() == scenario.grid.ny, "initial h ny mismatch");
    expect(scenario.initial.wet.values.size() == scenario.grid.nx * scenario.grid.ny, "wet mask shape mismatch");
    expect(!scenario.boundaries.empty(), "expected scenario boundaries");
    expect(!scenario.probes.empty(), "expected probes for telemetry exports");
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

void assert_output_can_be_written(const raftsim::Scenario& scenario, const std::string& output_dir) {
    raftsim::ReducedShallowWaterSolver solver(scenario);
    std::vector<raftsim::Frame> frames = solver.run(8, 4);
    raftsim::ValidationSummary validation = raftsim::validate_frames(scenario, frames, {});
    expect(validation.passed, "validation failed for smoke scenario");
    raftsim::write_solver_output(scenario, frames, validation, output_dir);
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "manifest.json"), "manifest was not written");
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "validation.json"), "validation was not written");
    expect(std::filesystem::exists(std::filesystem::path(output_dir) / "frames" / "frame_0000.csv"), "frame was not written");
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 3) {
            std::cerr << "Usage: " << argv[0] << " <scenario-dir|scenario.json> [output-dir]\n";
            return 1;
        }
        raftsim::Scenario scenario = raftsim::load_scenario_package(argv[1]);
        assert_scenario_loads(scenario);
        assert_solver_is_deterministic(scenario);
        if (argc == 3) {
            assert_output_can_be_written(scenario, argv[2]);
        }
        std::cout << "raftsim_water_tests passed for " << scenario.scenario_id << "\n";
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "raftsim_water_tests: " << exc.what() << "\n";
        return 1;
    }
}
