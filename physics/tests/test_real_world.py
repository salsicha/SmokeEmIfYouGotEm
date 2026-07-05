import json

import numpy as np

from raftsim.real_world import (
    CANDIDATE_RIVER_INVENTORY_FILE,
    CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION,
    COURSE_ELEVATION_EXTRACTION_FILE,
    COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION,
    RAPID_REVIEW_EDITOR_WORKFLOW_FILE,
    RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION,
    adaptive_solver_parameters,
    build_candidate_river_inventory_package,
    build_course_elevation_extraction,
    build_player_selection_model,
    build_rapid_review_editor_workflow,
    build_rapid_review_flow_difficulty_mapping,
    build_real_world_corridor_package,
    build_source_manifest,
    default_candidate_river_inventory,
    default_manual_rapid_review_labels,
    default_player_selections,
    default_source_catalog,
    extract_channel_indicators,
    generate_real_world_scenario2_5d,
    generate_south_fork_american_cascading_scenario2_5d,
    generate_south_fork_american_cascading_seed_scenarios,
    identify_candidate_rapids,
    south_fork_american_centerline_stations,
    south_fork_american_fetch_specs,
    south_fork_american_flow_bands,
    write_real_world_seed_package,
)
from raftsim.examples.generate_real_world_scenario import main as generate_real_world_main
from raftsim.cascading import (
    UNREAL_CASCADING_CORRIDOR_GRID_FILE,
    UNREAL_CASCADING_CORRIDOR_METADATA_FILE,
    read_cascading_scenario_package,
)
from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.schema_versions import SOURCE_MANIFEST_SCHEMA_VERSION


def test_candidate_inventory_covers_first_playable_sections_and_priorities():
    sections = default_candidate_river_inventory()
    first = sections[0]
    third = sections[2]

    assert len(sections) >= 5
    assert [section.river_id for section in sections[:3]] == [
        "american_south_fork",
        "colorado_grand_canyon_rowing",
        "pacuare",
    ]
    assert first.river_id == "american_south_fork"
    assert first.section_id == "chili_bar_to_coloma"
    assert third.country == "CR"
    assert third.section_id == "lower_pacuare_planning_corridor"
    assert "Third runnable river target" in third.notes
    assert {"3dep_lidar_dem", "3dhp_nhd_flowlines", "naip_imagery", "nwis_gauge_11445500"}.issubset(
        set(first.data_priorities)
    )


def test_candidate_river_inventory_package_links_primary_source_manifest():
    inventory = build_candidate_river_inventory_package()
    data = inventory.to_json_dict()
    primary_link = data["section_source_manifests"][0]
    colorado_link = data["section_source_manifests"][1]
    pacuare_link = data["section_source_manifests"][2]
    planned_links = data["section_source_manifests"][2:]

    assert data["schema_version"] == CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION
    assert data["inventory_id"] == "raftsim.real_world_candidate_river_inventory.v0"
    assert data["source_catalog"] == "source_catalog.json"
    assert data["section_count"] == len(default_candidate_river_inventory())
    assert data["primary_section"] == {
        "river_id": "american_south_fork",
        "section_id": "chili_bar_to_coloma",
    }
    assert primary_link["source_manifest_status"] == "drafted"
    assert primary_link["source_manifest_path"] == "south_fork_american_chili_bar/source_manifest.json"
    assert colorado_link["source_manifest_status"] == "drafted"
    assert colorado_link["source_manifest_path"] == "colorado_river_grand_canyon_rowing/source_manifest.json"
    assert pacuare_link["source_manifest_status"] == "planned"
    assert pacuare_link["source_manifest_path"] is None
    assert all(link["source_manifest_status"] == "planned" for link in planned_links)
    assert any("seasonal flow bands" in criterion for criterion in data["selection_criteria"])


def test_source_catalog_records_required_categories_and_attribution():
    sources = default_source_catalog()
    categories = {source.category for source in sources}

    assert {"elevation", "hydrography", "imagery", "gauge", "guide_reference", "field_media"}.issubset(categories)
    assert all(source.license_or_terms for source in sources)
    assert all(source.attribution for source in sources)


def test_source_manifest_contains_fetch_specs_and_artifact_buckets():
    manifest = build_source_manifest()

    assert manifest["schema_version"] == SOURCE_MANIFEST_SCHEMA_VERSION
    assert manifest["river_id"] == "american_south_fork"
    assert {fetch.fetch_id for fetch in south_fork_american_fetch_specs()} >= {
        "sfa_3dep_dem",
        "sfa_3dhp_nhd_flowlines",
        "sfa_nwis_daily_discharge",
    }
    assert {"elevation", "hydrography", "imagery", "gauges", "guide_references", "field_media"}.issubset(
        set(manifest["artifacts"])
    )
    assert COURSE_ELEVATION_EXTRACTION_FILE in manifest["artifacts"]["elevation"]
    assert RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE in manifest["artifacts"]["guide_references"]


def test_channel_indicators_and_rapid_candidates_find_complex_water():
    indicators = extract_channel_indicators(south_fork_american_centerline_stations())
    candidates = identify_candidate_rapids(indicators)

    assert len(indicators) == len(south_fork_american_centerline_stations())
    assert max(indicator.gradient for indicator in indicators) > 0.01
    assert max(indicator.constriction_score for indicator in indicators) > 0.25
    assert len(candidates) >= 3
    assert any("boulder_garden" in candidate.suggested_labels for candidate in candidates)
    assert any("foam_whitewater_texture" in candidate.signals for candidate in candidates)


def test_course_elevation_extraction_summarizes_section_profile_and_cross_sections():
    package = build_real_world_corridor_package()
    extraction = build_course_elevation_extraction(package)
    data = extraction.to_json_dict()
    summary = data["summary"]
    samples = data["samples"]
    cross_sections = data["cross_section_prototypes"]

    assert data["schema_version"] == COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION
    assert data["river_id"] == "american_south_fork"
    assert data["section_id"] == "chili_bar_to_coloma"
    assert data["source_artifacts"]["source_manifest"] == "source_manifest.json"
    assert summary["sample_count"] == len(package.centerline)
    assert summary["cross_section_prototype_count"] == len(package.indicators)
    assert summary["rapid_candidate_count"] == len(package.rapid_candidates)
    assert summary["length_m"] == package.centerline[-1].station_m - package.centerline[0].station_m
    np.testing.assert_allclose(summary["total_drop_m"], 66.0)
    assert summary["mean_gradient"] > 0.01
    assert summary["max_local_gradient"] > summary["min_local_gradient"]
    assert samples[0]["cumulative_drop_m"] == 0.0
    assert samples[-1]["cumulative_drop_m"] == summary["total_drop_m"]
    assert len(cross_sections) == len(package.indicators)
    assert any(section["rapid_candidate_ids"] for section in cross_sections)
    assert all(section["bank_offsets_m"]["left"] > 0.0 for section in cross_sections)
    assert all(section["bank_offsets_m"]["right"] < 0.0 for section in cross_sections)
    assert data["provenance"]["review_status"] == "prototype_needs_real_dem_lidar_hydrography_pull"


def test_manual_review_labels_cover_required_whitewater_features():
    labels = {label.label for label in default_manual_rapid_review_labels()}

    assert {
        "pool",
        "riffle",
        "wave_train",
        "hole",
        "ledge",
        "lateral",
        "strainer",
        "portage",
        "access_point",
    }.issubset(labels)


def test_adaptive_parameters_scale_with_flow_and_difficulty():
    beginner_low = adaptive_solver_parameters(default_player_selections()[0])
    intermediate_medium = adaptive_solver_parameters(default_player_selections()[1])
    advanced_high = adaptive_solver_parameters(default_player_selections()[2])

    assert beginner_low.boundary_inflow_m3s < intermediate_medium.boundary_inflow_m3s < advanced_high.boundary_inflow_m3s
    assert beginner_low.wave_train_strength < intermediate_medium.wave_train_strength < advanced_high.wave_train_strength
    assert beginner_low.eddy_line_shear < advanced_high.eddy_line_shear
    assert advanced_high.shallow_hazard_threshold_m < beginner_low.shallow_hazard_threshold_m


def test_rapid_review_flow_difficulty_mapping_exposes_label_curves_and_parameter_matrix():
    package = build_real_world_corridor_package()
    mapping = build_rapid_review_flow_difficulty_mapping(package)
    data = mapping.to_json_dict()
    label_responses = {entry["label"]: entry for entry in data["label_flow_responses"]}
    hole_responses = {
        response["flow_band"]: response
        for response in label_responses["hole"]["flow_responses"]
    }
    boulder_responses = {
        response["flow_band"]: response
        for response in label_responses["boulder_garden"]["flow_responses"]
    }
    parameter_rows = data["parameter_matrix"]

    assert data["schema_version"] == RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION
    assert data["river_id"] == "american_south_fork"
    assert data["section_id"] == "chili_bar_to_coloma"
    assert {"hole", "wave_train", "lateral", "eddy_line", "boulder_garden"}.issubset(label_responses)
    assert hole_responses["median_runnable"]["activation_scale"] > hole_responses["low_runnable"]["activation_scale"]
    assert hole_responses["median_runnable"]["activation_scale"] > hole_responses["high_runnable"]["activation_scale"]
    assert boulder_responses["low_runnable"]["activation_scale"] > boulder_responses["high_runnable"]["activation_scale"]
    assert "hole_retention_strength" in label_responses["hole"]["tuning_parameters"]
    assert "pin" in label_responses["boulder_garden"]["expected_raft_outcomes"]
    assert len(parameter_rows) == len(south_fork_american_flow_bands()) * 4

    beginner_low = next(
        row for row in parameter_rows
        if row["flow_band"] == "low_runnable" and row["difficulty"] == "beginner"
    )
    expert_high = next(
        row for row in parameter_rows
        if row["flow_band"] == "high_runnable" and row["difficulty"] == "expert"
    )
    assert expert_high["parameters"]["hole_retention_strength"] > beginner_low["parameters"]["hole_retention_strength"]
    assert expert_high["parameters"]["hazard_activation_scale"] > beginner_low["parameters"]["hazard_activation_scale"]
    assert expert_high["review_controls"]["crew_timing_window"] == "very_tight"
    assert any("GeoClaw/C++ conservation" in requirement for requirement in data["review_requirements"])


def test_player_selection_model_exposes_river_season_flow_difficulty_and_raft_setup():
    model = build_player_selection_model()
    section = model["regions"][0]["rivers"][0]["sections"][0]

    assert section["section_id"] == "chili_bar_to_coloma"
    assert {"late_summer_low_water", "summer_commercial", "spring_runoff_or_release"}.issubset(
        set(section["seasons"])
    )
    assert {band["flow_band"] for band in section["flow_bands"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert section["flow_difficulty_mapping"] == RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE
    assert "standard_14ft_paddle_raft" in section["raft_setups"]


def test_real_world_corridor_package_collects_unreal_handoff_metadata():
    package = build_real_world_corridor_package()

    assert package.unreal_ready_artifacts["terrain"] == "terrain/solver_bed_grid.npy"
    assert package.unreal_ready_artifacts["course_elevation_extraction"] == COURSE_ELEVATION_EXTRACTION_FILE
    assert package.unreal_ready_artifacts["rapid_review_editor_workflow"] == RAPID_REVIEW_EDITOR_WORKFLOW_FILE
    assert package.unreal_ready_artifacts["rapid_review_flow_difficulty_mapping"] == RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE
    assert len(package.rapid_candidates) >= 3
    assert {band.flow_band for band in south_fork_american_flow_bands()} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }


def test_rapid_review_editor_workflow_displays_required_context_in_one_view():
    workflow = build_rapid_review_editor_workflow()
    data = workflow.to_json_dict()
    required_layer_ids = set(data["required_layer_ids"])
    panel_ids = {panel["panel_id"] for panel in data["panels"]}
    first_item = data["review_items"][0]

    assert data["schema_version"] == RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION
    assert data["view_id"] == "rapid_review_one_view"
    assert {
        "dem_lidar",
        "aerial_satellite_imagery",
        "flowlines",
        "cross_sections",
        "gauge_history",
        "flow_difficulty_mapping",
        "source_manifest",
        "candidate_tags",
        "guide_notes",
    }.issubset(required_layer_ids)
    assert {"one_view_map", "station_profile", "flow_and_sources", "annotation_editor"}.issubset(panel_ids)
    assert len(data["review_items"]) >= 3
    assert first_item["candidate_tags"]
    assert first_item["evidence_refs"]["dem_lidar"]["source_ids"] == ["usgs_3dep", "usgs_tnm"]
    assert "aerial_satellite_imagery" in first_item["evidence_refs"]
    assert first_item["cross_section_summary"]["channel_width_m"] > 0.0
    assert first_item["evidence_refs"]["flow_difficulty_mapping"]["artifacts"] == [
        RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE
    ]
    assert {band["flow_band"] for band in first_item["gauge_context"]["flow_bands"]} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert first_item["guide_notes"]
    assert {"python_scenario_generation", "geoclaw_cpp_validation_reports", "unreal_data_assets"}.issubset(
        set(data["export_targets"])
    )


def test_real_world_scenario_generates_solver_neutral_package(tmp_path):
    scenario = generate_real_world_scenario2_5d(nx=40, ny=20, duration=0.5)
    output_dir = scenario.write_package(tmp_path / "real_world")
    loaded = read_scenario2_5d_package(output_dir)

    assert loaded.metadata.scenario_type == "real_world"
    assert loaded.metadata.river_id == "american_south_fork"
    assert loaded.metadata.source_manifest == "source_manifest.json"
    assert loaded.metadata.flow_band == "median_runnable"
    assert loaded.validate().passed
    np.testing.assert_allclose(loaded.initial_state.depth, scenario.initial_state.depth)


def test_south_fork_cascading_scenario_adds_variable_reaches_and_rapid_drop_metadata():
    package = generate_south_fork_american_cascading_scenario2_5d(nx=80, ny=30, duration=0.5)
    reach_kinds = [reach.kind for reach in package.reaches]
    source_station_ranges = [
        (reach.metadata["source_station_start_m"], reach.metadata["source_station_end_m"]) for reach in package.reaches
    ]

    assert package.scenario.validate().passed
    assert package.scenario.metadata.scenario_type == "real_world"
    assert package.scenario.metadata.river_id == "american_south_fork"
    assert package.scenario.metadata.flow_band == "median_runnable"
    assert package.scenario.metadata.generator == "raftsim.real_world.cascading"
    assert reach_kinds == ["pool", "tongue", "drop", "wave_train", "eddy_recovery", "boulder_garden", "pool"]
    assert len({round(reach.slope_profile[0].value, 4) for reach in package.reaches}) > 3
    assert all(start < end for start, end in source_station_ranges)
    assert package.drop_transitions[0].metadata["source_rapid_id"].startswith("rapid_candidate_")
    assert package.drop_transitions[0].metadata["source_elevation_fall_m"] > 0.0
    assert "boulder_garden" in package.drop_transitions[0].hazard_tags
    assert any(feature.metadata.get("source") == "real_world_rapid_candidate" for feature in package.scenario.features)


def test_south_fork_cascading_seed_suite_covers_low_median_and_high_flows():
    packages = generate_south_fork_american_cascading_seed_scenarios(nx=72, ny=28, duration=0.5)
    flow_bands = [package.scenario.metadata.flow_band for package in packages]
    depths = [float(package.scenario.initial_state.depth.mean()) for package in packages]

    assert flow_bands == ["low_runnable", "median_runnable", "high_runnable"]
    assert [package.scenario.metadata.difficulty_preset for package in packages] == ["beginner", "intermediate", "advanced"]
    assert depths[0] < depths[1] < depths[2]
    assert all(package.scenario.validate().passed for package in packages)


def test_write_real_world_seed_package_outputs_manifest_and_scenario(tmp_path):
    output_dir = write_real_world_seed_package(tmp_path / "real_world_data")

    assert (output_dir.parent / CANDIDATE_RIVER_INVENTORY_FILE).exists()
    assert (output_dir.parent / "candidate_rivers.json").exists()
    assert (output_dir / "source_manifest.json").exists()
    assert (output_dir / COURSE_ELEVATION_EXTRACTION_FILE).exists()
    assert (output_dir / RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE).exists()
    assert (output_dir / "flow_presets.json").exists()
    assert (output_dir / "rapid_candidates.geojson").exists()
    assert (output_dir / RAPID_REVIEW_EDITOR_WORKFLOW_FILE).exists()
    assert (output_dir / "corridor_package_manifest.json").exists()
    assert (output_dir / "scenario" / "scenario.json").exists()
    cascading_dirs = sorted((output_dir / "cascading_scenarios").glob("*_cascading"))
    assert len(cascading_dirs) == 3

    manifest = json.loads((output_dir / "source_manifest.json").read_text(encoding="utf-8"))
    course_elevation = json.loads((output_dir / COURSE_ELEVATION_EXTRACTION_FILE).read_text(encoding="utf-8"))
    flow_mapping = json.loads((output_dir / RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE).read_text(encoding="utf-8"))
    inventory = json.loads((output_dir.parent / CANDIDATE_RIVER_INVENTORY_FILE).read_text(encoding="utf-8"))
    workflow = json.loads((output_dir / RAPID_REVIEW_EDITOR_WORKFLOW_FILE).read_text(encoding="utf-8"))
    scenario = read_scenario2_5d_package(output_dir / "scenario")
    median_cascading_dir = next(path for path in cascading_dirs if "median_runnable" in path.name)
    cascading = read_cascading_scenario_package(median_cascading_dir)
    unreal_metadata_dir = median_cascading_dir / "unreal_corridor_metadata"
    assert manifest["schema_version"] == SOURCE_MANIFEST_SCHEMA_VERSION
    assert course_elevation["schema_version"] == COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION
    assert course_elevation["summary"]["sample_count"] == len(south_fork_american_centerline_stations())
    assert flow_mapping["schema_version"] == RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION
    assert len(flow_mapping["parameter_matrix"]) == len(south_fork_american_flow_bands()) * 4
    assert inventory["schema_version"] == CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION
    assert inventory["section_source_manifests"][0]["source_manifest_status"] == "drafted"
    assert workflow["schema_version"] == RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION
    assert "dem_lidar" in workflow["required_layer_ids"]
    assert scenario.metadata.scenario_type == "real_world"
    assert cascading.scenario.metadata.flow_band == "median_runnable"
    assert len(cascading.reaches) == 7
    assert (unreal_metadata_dir / UNREAL_CASCADING_CORRIDOR_METADATA_FILE).exists()
    assert (unreal_metadata_dir / UNREAL_CASCADING_CORRIDOR_GRID_FILE).exists()


def test_generate_real_world_scenario_example_writes_selected_package(tmp_path):
    exit_code = generate_real_world_main(
        [
            "--output-dir",
            str(tmp_path),
            "--flow-band",
            "high_runnable",
            "--difficulty",
            "advanced",
            "--duration",
            "0.5",
            "--nx",
            "32",
            "--ny",
            "16",
        ]
    )

    assert exit_code == 0
    scenario_dirs = list((tmp_path / "scenario").glob("*"))
    assert len(scenario_dirs) == 1
    scenario = read_scenario2_5d_package(scenario_dirs[0])
    assert scenario.metadata.flow_band == "high_runnable"
    assert scenario.metadata.difficulty_preset == "advanced"
