#include "raftsim_water/chrono_bridge_fixtures.hpp"

#include <iostream>

int main() {
    const auto& fixtures = raftsim::chrono_bridge_fixture_catalog();
    std::cout << "chrono_bridge_fixtures=" << fixtures.size() << "\n";
    for (const raftsim::ChronoBridgeFixture& fixture : fixtures) {
        std::cout
            << fixture.id
            << " scenario=" << fixture.scenario_kind
            << " water_dt=" << fixture.water_step_seconds
            << " chrono_dt=" << fixture.chrono_substep_seconds
            << " expected=\"" << fixture.expected_behavior << "\"\n";
    }
    return fixtures.empty() ? 1 : 0;
}
