#include "raftsim_water/chrono_coupling.hpp"
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
        assert_scenario_loads(scenario);
        assert_solver_is_deterministic(scenario);
        assert_chrono_coupling_samples_water_and_contact(scenario);
        if (argc == 3) {
            assert_output_can_be_written(scenario, argv[2]);
        }
        if (scenario.cascading.present) {
            std::cout << "cascading_reaches=" << scenario.cascading.reaches.size()
                      << " cascading_drop_transitions=" << scenario.cascading.drop_transitions.size() << "\n";
        }
        std::cout << "raftsim_water_tests passed for " << scenario.scenario_id << "\n";
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "raftsim_water_tests: " << exc.what() << "\n";
        return 1;
    }
}
