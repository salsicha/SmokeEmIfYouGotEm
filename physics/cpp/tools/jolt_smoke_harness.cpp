#include "raftsim_water/json.hpp"

#include <exception>
#include <iostream>
#include <string>

namespace {

int fail(const std::string& message) {
    std::cerr << "raftsim_jolt_smoke_harness: " << message << "\n";
    return 1;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string manifest_path =
        argc > 1 ? argv[1] : "tests/jolt_smoke_harness_manifest.json";

    try {
        const raftsim::JsonValue manifest = raftsim::parse_json_file(manifest_path);
        const auto& root = manifest.as_object();
        const auto schema = root.at("schema").as_string();
        const auto runtime = root.at("target_runtime").as_string();
        const auto decision = root.at("decision").as_string();
        const auto& fixtures = root.at("fixtures").as_array();

        if (schema != "raftsim.native.jolt_smoke_harness.v1") {
            return fail("unexpected manifest schema: " + schema);
        }
        if (runtime != "Jolt") {
            return fail("unexpected target runtime: " + runtime);
        }
        if (fixtures.empty()) {
            return fail("manifest has no fixtures");
        }

        std::cout << "jolt_smoke_harness_manifest=" << manifest_path << "\n";
        std::cout << "decision=" << decision << "\n";
        std::cout << "fixture_count=" << fixtures.size() << "\n";
        std::cout << "jolt_sdk_linked=false\n";
        std::cout << "status=schema_placeholder_ready_for_jolt_sdk_integration\n";
        for (const raftsim::JsonValue& fixture_value : fixtures) {
            const auto& fixture = fixture_value.as_object();
            std::cout
                << fixture.at("fixture_id").as_string()
                << " cases=" << fixture.at("parameter_case_count").as_int()
                << " steps=" << fixture.at("step_count").as_int()
                << " status=" << fixture.at("status").as_string() << "\n";
        }
    } catch (const std::exception& exc) {
        return fail(exc.what());
    }

    return 0;
}
