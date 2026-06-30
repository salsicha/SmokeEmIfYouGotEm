#include "raftsim_water/scenario.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <stdexcept>

#include "raftsim_water/json.hpp"

namespace raftsim {

namespace fs = std::filesystem;

namespace {

std::string optional_string(const JsonValue& object, const std::string& key) {
    const JsonValue* value = object.find(key);
    if (value == nullptr || value->is_null()) {
        return "";
    }
    return value->as_string();
}

double optional_number(const JsonValue& object, const std::string& key, double fallback = 0.0) {
    const JsonValue* value = object.find(key);
    if (value == nullptr || value->is_null()) {
        return fallback;
    }
    return value->as_number();
}

bool has_key(const JsonValue& object, const std::string& key) {
    const JsonValue* value = object.find(key);
    return value != nullptr && !value->is_null();
}

Array2D require_float_array(const NpzArchive& archive, const std::string& name) {
    auto it = archive.float_arrays.find(name);
    if (it == archive.float_arrays.end()) {
        throw std::runtime_error("Missing initial_state array: " + name);
    }
    return it->second;
}

BoolGrid require_bool_array(const NpzArchive& archive, const std::string& name) {
    auto it = archive.bool_arrays.find(name);
    if (it == archive.bool_arrays.end()) {
        throw std::runtime_error("Missing initial_state bool array: " + name);
    }
    return it->second;
}

CascadingMetadata load_cascading_metadata(const fs::path& package_dir) {
    fs::path metadata_path = package_dir / "cascading_metadata.json";
    if (!fs::exists(metadata_path)) {
        return {};
    }
    JsonValue root = parse_json_file(metadata_path.string());
    CascadingMetadata metadata;
    metadata.present = true;
    metadata.schema_version = root.at("schema_version").as_string();
    if (metadata.schema_version != "raftsim.cascading2_5d.v0") {
        throw std::runtime_error("Unsupported cascading schema version.");
    }
    for (const JsonValue& value : root.at("reaches").as_array()) {
        CascadingReach reach;
        reach.id = value.at("reach_id").as_string();
        reach.kind = value.at("kind").as_string();
        reach.station_start = value.at("station_start").as_number();
        reach.station_end = value.at("station_end").as_number();
        metadata.reaches.push_back(reach);
    }
    for (const JsonValue& value : root.at("drop_transitions").as_array()) {
        CascadingDropTransition transition;
        transition.id = value.at("transition_id").as_string();
        transition.upstream_reach_id = value.at("upstream_reach_id").as_string();
        transition.downstream_reach_id = value.at("downstream_reach_id").as_string();
        transition.crest_station = value.at("crest_station").as_number();
        transition.bed_elevation_fall = value.at("bed_elevation_fall").as_number();
        metadata.drop_transitions.push_back(transition);
    }
    return metadata;
}

}  // namespace

Scenario load_scenario_package(const std::string& scenario_dir) {
    fs::path root(scenario_dir);
    fs::path scenario_path = root.filename() == "scenario.json" ? root : root / "scenario.json";
    fs::path package_dir = scenario_path.parent_path();
    JsonValue manifest = parse_json_file(scenario_path.string());
    if (manifest.at("schema_version").as_string() != "raftsim.scenario2_5d.v0") {
        throw std::runtime_error("Unsupported scenario schema version.");
    }

    Scenario scenario;
    const JsonValue& metadata = manifest.at("metadata");
    scenario.scenario_id = metadata.at("scenario_id").as_string();
    scenario.scenario_type = metadata.at("scenario_type").as_string();
    scenario.fixture_kind = optional_string(metadata, "fixture_kind");

    const JsonValue& grid = manifest.at("grid");
    scenario.grid.nx = static_cast<std::size_t>(grid.at("nx").as_int());
    scenario.grid.ny = static_cast<std::size_t>(grid.at("ny").as_int());
    scenario.grid.dx = grid.at("dx").as_number();
    scenario.grid.dy = grid.at("dy").as_number();
    scenario.grid.origin_x = grid.number_or("origin_x", 0.0);
    scenario.grid.origin_y = grid.number_or("origin_y", 0.0);
    scenario.fixed_dt = manifest.at("fixed_dt").as_number();
    scenario.duration = manifest.at("duration").as_number();
    scenario.roughness = manifest.number_or("roughness", 0.035);

    const JsonValue& array_files = manifest.at("array_files");
    fs::path bed_path = package_dir / array_files.string_or("bed", "bed.npy");
    fs::path state_path = package_dir / array_files.string_or("initial_state", "initial_state.npz");
    fs::path features_path = package_dir / array_files.string_or("features", "features.json");
    fs::path probes_path = package_dir / array_files.string_or("probes", "probes.json");

    scenario.bed = load_npy_f64(bed_path.string());
    NpzArchive state = load_npz(state_path.string());
    scenario.initial.h = require_float_array(state, "depth");
    scenario.initial.eta = require_float_array(state, "eta");
    scenario.initial.u = require_float_array(state, "u");
    scenario.initial.v = require_float_array(state, "v");
    scenario.initial.hu = require_float_array(state, "hu");
    scenario.initial.hv = require_float_array(state, "hv");
    scenario.initial.wet = require_bool_array(state, "wet");

    for (const JsonValue& value : manifest.at("boundaries").as_array()) {
        BoundaryCondition boundary;
        boundary.edge = value.at("edge").as_string();
        boundary.kind = value.at("kind").as_string();
        boundary.has_stage = has_key(value, "stage");
        boundary.stage = optional_number(value, "stage");
        boundary.has_depth = has_key(value, "depth");
        boundary.depth = optional_number(value, "depth");
        const JsonValue* velocity = value.find("velocity");
        if (velocity != nullptr && !velocity->is_null()) {
            boundary.has_velocity = true;
            boundary.velocity_x = velocity->at(0).as_number();
            boundary.velocity_y = velocity->at(1).as_number();
        }
        scenario.boundaries.push_back(boundary);
    }

    JsonValue features_root = parse_json_file(features_path.string());
    for (const JsonValue& value : features_root.at("features").as_array()) {
        Feature feature;
        feature.kind = value.at("kind").as_string();
        feature.center_x = value.at("center").at("x").as_number();
        feature.center_y = value.at("center").at("y").as_number();
        feature.radius = value.number_or("radius", 0.0);
        feature.strength = value.number_or("strength", 1.0);
        feature.length = value.number_or("length", 0.0);
        feature.width = value.number_or("width", 0.0);
        feature.angle = value.number_or("angle", 0.0);
        scenario.features.push_back(feature);
    }

    JsonValue probes_root = parse_json_file(probes_path.string());
    for (const JsonValue& value : probes_root.at("probes").as_array()) {
        Probe probe;
        probe.id = value.at("probe_id").as_string();
        probe.kind = value.string_or("kind", "point");
        probe.x = value.at("position").at("x").as_number();
        probe.y = value.at("position").at("y").as_number();
        const JsonValue* normal = value.find("normal");
        if (normal != nullptr && !normal->is_null()) {
            probe.normal_x = normal->at("x").as_number();
            probe.normal_y = normal->at("y").as_number();
        }
        probe.length = value.number_or("length", 0.0);
        scenario.probes.push_back(probe);
    }

    scenario.cascading = load_cascading_metadata(package_dir);
    validate_scenario(scenario);
    return scenario;
}

void validate_scenario(const Scenario& scenario) {
    if (scenario.grid.nx < 2 || scenario.grid.ny < 2) {
        throw std::runtime_error("Scenario grid must have at least 2x2 cells.");
    }
    if (scenario.grid.dx <= 0.0 || scenario.grid.dy <= 0.0) {
        throw std::runtime_error("Scenario grid spacing must be positive.");
    }
    const std::size_t nx = scenario.grid.nx;
    const std::size_t ny = scenario.grid.ny;
    auto assert_shape = [&](const Array2D& array, const std::string& name) {
        if (array.nx() != nx || array.ny() != ny) {
            throw std::runtime_error(name + " shape does not match scenario grid.");
        }
    };
    assert_shape(scenario.bed, "bed");
    assert_shape(scenario.initial.h, "h");
    assert_shape(scenario.initial.eta, "eta");
    assert_shape(scenario.initial.u, "u");
    assert_shape(scenario.initial.v, "v");
    assert_shape(scenario.initial.hu, "hu");
    assert_shape(scenario.initial.hv, "hv");
    if (scenario.initial.wet.nx != nx || scenario.initial.wet.ny != ny) {
        throw std::runtime_error("wet mask shape does not match scenario grid.");
    }
    if (scenario.fixed_dt <= 0.0 || scenario.duration <= 0.0) {
        throw std::runtime_error("Scenario timestep and duration must be positive.");
    }
    if (scenario.cascading.present && scenario.cascading.reaches.empty()) {
        throw std::runtime_error("Cascading package metadata must include at least one reach.");
    }
}

std::size_t grid_index_for_position(const Scenario& scenario, double x, double y) {
    long col = static_cast<long>(std::nearbyint((x - scenario.grid.origin_x) / scenario.grid.dx));
    long row = static_cast<long>(std::nearbyint((y - scenario.grid.origin_y) / scenario.grid.dy));
    col = std::max<long>(0, std::min<long>(static_cast<long>(scenario.grid.nx) - 1, col));
    row = std::max<long>(0, std::min<long>(static_cast<long>(scenario.grid.ny) - 1, row));
    return static_cast<std::size_t>(row) * scenario.grid.nx + static_cast<std::size_t>(col);
}

std::size_t row_from_index(const Scenario& scenario, std::size_t index) {
    return index / scenario.grid.nx;
}

std::size_t col_from_index(const Scenario& scenario, std::size_t index) {
    return index % scenario.grid.nx;
}

}  // namespace raftsim
