#include "raftsim_water/chrono_bridge_fixtures.hpp"

namespace raftsim {

const std::vector<ChronoBridgeFixture>& chrono_bridge_fixture_catalog() {
    static const std::vector<ChronoBridgeFixture> fixtures{
        {"flat_pool_float", "flat_pool", "raft floats without vertical contact jitter"},
        {"current_drift", "uniform_current", "raft translates downstream with bounded yaw drift"},
        {"standing_wave_lift", "standing_wave", "bow rises over a potential-energy wave barrier"},
        {"eddy_line_yaw", "eddy_line", "cross-raft shear produces measurable yaw torque"},
        {"rock_bounce", "rock_impact", "raft deflects with partially elastic restitution"},
        {"riverbed_grounding", "shallow_bed", "raft grounds with near-zero elastic bounce"},
        {"shallow_shelf_pivot", "shallow_shelf", "raft pivots around a grounded floor/tube patch"},
        {"pin_release", "strainer_or_rock_pin", "pin state can be detected and released by force threshold"}
    };
    return fixtures;
}

}  // namespace raftsim
