#pragma once

#include <string>
#include <vector>

namespace raftsim {

struct ChronoBridgeFixture {
    std::string id;
    std::string scenario_kind;
    std::string expected_behavior;
    double duration_seconds = 4.0;
    double water_step_seconds = 1.0 / 60.0;
    double chrono_substep_seconds = 1.0 / 120.0;
};

const std::vector<ChronoBridgeFixture>& chrono_bridge_fixture_catalog();

}  // namespace raftsim
