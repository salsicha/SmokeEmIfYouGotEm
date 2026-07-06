import hashlib
import json
from pathlib import Path

import numpy as np

from raftsim.real_world import (
    CANDIDATE_RIVER_INVENTORY_FILE,
    CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION,
    COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE,
    COLORADO_NHD_CROSS_SECTION_SEED_FILE,
    COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE,
    COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE,
    COLORADO_NHD_HU8_MANIFEST_FILE,
    COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE,
    COLORADO_NHD_MAINSTEM_CANDIDATE_FILE,
    COLORADO_NHD_MAINSTEM_MANIFEST_FILE,
    COLORADO_NHD_MAINSTEM_STATIONING_FILE,
    COLORADO_NHD_WATER_PRIOR_FILE,
    COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE,
    COLORADO_PRODUCTION_IMPORT_PILOT_FILE,
    COLORADO_USBR_RELEASE_CONTEXT_FILE,
    COLORADO_USBR_TOTAL_RELEASE_FILE,
    COURSE_ELEVATION_EXTRACTION_FILE,
    COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION,
    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
    PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE,
    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
    PACUARE_PRODUCTION_IMPORT_PILOT_FILE,
    PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE,
    PRODUCTION_ENVIRONMENT_GAP_REGISTER_SCHEMA_VERSION,
    RAPID_REVIEW_EDITOR_WORKFLOW_FILE,
    RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION,
    PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE,
    adaptive_solver_parameters,
    build_candidate_river_inventory_package,
    build_colorado_production_import_pilot,
    build_course_elevation_extraction,
    build_pacuare_production_import_pilot,
    build_player_selection_model,
    build_production_environment_gap_register,
    build_rapid_review_editor_workflow,
    build_rapid_review_flow_difficulty_mapping,
    build_real_world_corridor_package,
    build_south_fork_production_import_pilot,
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

REAL_WORLD_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "real_world"


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
    source_ids = {source.source_id for source in sources}

    assert {"elevation", "hydrography", "imagery", "gauge", "guide_reference", "field_media"}.issubset(categories)
    assert {"cdec_cbr", "cdec_a25_powerhouse_context"}.issubset(source_ids)
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
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE in manifest["artifacts"]["source_pulls"]
    assert "hydrology/cdec_terms_flags_and_station_relation_review.json" in manifest["artifacts"]["gauges"]
    assert "hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json" in manifest["artifacts"]["gauges"]
    assert "hydrography/nhd_hu8_18020129_bbox_extract_manifest.json" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_flowline_bbox_extract.geojson" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_support_layers_bbox_extract.geojson" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_mainstem_candidate_manifest.json" in manifest["artifacts"]["hydrography"]
    assert (
        "hydrography/nhd_hu8_18020129_south_fork_mainstem_candidate.geojson"
        in manifest["artifacts"]["hydrography"]
    )
    assert "hydrography/nhd_hu8_18020129_mainstem_stationing_candidate.json" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_cross_section_seed_manifest.json" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_cross_section_seed_candidates.geojson" in manifest["artifacts"]["hydrography"]
    assert "hydrography/nhd_hu8_18020129_naip_dem_alignment_diagnostic.json" in manifest["artifacts"]["hydrography"]
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json" in manifest["artifacts"]["imagery"]
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png" in manifest["artifacts"]["imagery"]


def test_south_fork_nhd_hu8_extract_records_selection_and_counts():
    hydro_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / "hydrography"
    manifest = json.loads((hydro_dir / "nhd_hu8_18020129_bbox_extract_manifest.json").read_text())
    mainstem_manifest = json.loads((hydro_dir / "nhd_hu8_18020129_mainstem_candidate_manifest.json").read_text())
    flowlines = json.loads((hydro_dir / "nhd_hu8_18020129_flowline_bbox_extract.geojson").read_text())
    support = json.loads((hydro_dir / "nhd_hu8_18020129_support_layers_bbox_extract.geojson").read_text())
    mainstem = json.loads((hydro_dir / "nhd_hu8_18020129_south_fork_mainstem_candidate.geojson").read_text())
    stationing = json.loads((hydro_dir / "nhd_hu8_18020129_mainstem_stationing_candidate.json").read_text())
    cross_section_manifest = json.loads((hydro_dir / "nhd_hu8_18020129_cross_section_seed_manifest.json").read_text())
    cross_sections = json.loads((hydro_dir / "nhd_hu8_18020129_cross_section_seed_candidates.geojson").read_text())
    alignment = json.loads((hydro_dir / "nhd_hu8_18020129_naip_dem_alignment_diagnostic.json").read_text())
    water_prior = json.loads(
        (
            REAL_WORLD_DATA_DIR
            / "south_fork_american_chili_bar"
            / "imagery"
            / "production_import_pilot"
            / "nhd_mainstem_water_prior_manifest.json"
        ).read_text()
    )

    assert manifest["selected_product"]["hydrologic_unit"] == "18020129"
    assert manifest["source_crs"]["epsg"] == "EPSG:4269"
    assert manifest["layer_summary"]["NHDFlowline"]["bbox_intersecting_feature_count"] == 1816
    assert manifest["adjacent_product_diagnostic"]["bbox_intersection_summary"]["NHDFlowline"][
        "bbox_intersecting_feature_count"
    ] == 0
    assert len(flowlines["features"]) == 1816
    assert len(support["features"]) == 129
    assert any(
        name["gnis_name"] == "South Fork American River" and name["count"] == 102
        for name in manifest["layer_summary"]["NHDFlowline"]["top_named_features"]
    )
    assert mainstem_manifest["derivation"]["ordered_feature_count"] == 102
    assert mainstem_manifest["derivation"]["vertex_count"] == 361
    assert mainstem_manifest["derivation"]["endpoint_snapping"] == "none_required_exact_7_decimal_endpoint_matches"
    assert mainstem["features"][0]["properties"]["length_km_nhd_sum"] == 26.19019554
    assert mainstem["features"][0]["geometry"]["type"] == "LineString"
    assert stationing["local_transform"]["type"] == "local_equirectangular_preview_meters"
    assert stationing["summary"]["vertex_count"] == 361
    assert stationing["summary"]["station_sample_count"] == 264
    assert stationing["summary"]["station_sample_interval_m"] == 100.0
    assert cross_section_manifest["summary"]["feature_count"] == 133
    assert cross_section_manifest["parameters"]["half_width_m_each_side"] == 80.0
    assert len(cross_sections["features"]) == 133
    assert alignment["summary"]["station_samples_in_bounds"] == 260
    assert alignment["summary"]["station_samples_out_of_bounds"] == 4
    assert alignment["summary"]["station_water"]["ge_0_35_fraction"] == 0.3962
    assert alignment["summary"]["cross_sections_out_of_bounds"] == 3
    assert water_prior["status"] == "generated_review_gated_alignment_prior_not_segmentation_truth"
    assert water_prior["processing"]["line_width_px"] == 18
    assert water_prior["processing"]["station_samples_outside_bbox"] == 4
    assert water_prior["summary"]["nonzero_pixel_fraction"] == 0.044446
    assert water_prior["summary"]["ge_128_pixel_fraction"] == 0.020542
    assert water_prior["summary"]["sha256"] == "d01014e177ebced19c61583038a96f677fefde4a94ffc113704f744bab29ca17"


def test_south_fork_production_import_pilot_exposes_official_tile_plan_and_review_gates():
    pilot = build_south_fork_production_import_pilot()
    classes = {entry["class_id"]: entry for entry in pilot["required_source_classes"]}
    tiles = pilot["tile_grid"]["tiles"]

    assert pilot["schema"] == PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION
    assert pilot["status"] == "planned_review_gated_not_downloaded"
    assert pilot["river_id"] == "american_south_fork"
    assert len(tiles) == 4
    assert {tile["tile_id"] for tile in tiles} == {
        "sfa_chili_bar_tile_r0_c0",
        "sfa_chili_bar_tile_r0_c1",
        "sfa_chili_bar_tile_r1_c0",
        "sfa_chili_bar_tile_r1_c1",
    }
    assert all("3dep_dem_export" in tile["download_specs"] for tile in tiles)
    assert all("naip_export" in tile["download_specs"] for tile in tiles)
    assert "elevation.nationalmap.gov" in tiles[0]["download_specs"]["3dep_dem_export"]["url"]
    assert "gis.apfo.usda.gov" in tiles[0]["download_specs"]["naip_export"]["url"]
    assert {
        "terrain_dem_or_lidar",
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "water_and_vegetation_masks",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    }.issubset(classes)
    assert classes["hydrography_and_centerline"]["status"] == "nhd_hu8_alignment_diagnostic_attached_review_pending"
    assert "hydrography/nhd_hu8_18020129_bbox_extract_manifest.json" in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert "hydrography/nhd_hu8_18020129_south_fork_mainstem_candidate.geojson" in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert "hydrography/nhd_hu8_18020129_mainstem_stationing_candidate.json" in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert "hydrography/nhd_hu8_18020129_cross_section_seed_candidates.geojson" in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert "hydrography/nhd_hu8_18020129_naip_dem_alignment_diagnostic.json" in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert classes["water_and_vegetation_masks"]["status"] == "requires_new_derivatives_from_pilot_imagery_and_hydrography"
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json" in classes[
        "water_and_vegetation_masks"
    ]["target_outputs"]
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png" in classes[
        "water_and_vegetation_masks"
    ]["target_outputs"]
    assert pilot["unreal_import_targets"]["future_production_map"] == "/Game/RaftSim/Maps/Production/L_SouthForkAmerican_ChiliBar"


def test_colorado_production_import_pilot_exposes_lees_ferry_tile_plan_and_review_gates():
    pilot = build_colorado_production_import_pilot()
    classes = {entry["class_id"]: entry for entry in pilot["required_source_classes"]}
    tiles = pilot["tile_grid"]["tiles"]

    assert COLORADO_PRODUCTION_IMPORT_PILOT_FILE == "production_import_pilot.json"
    assert pilot["schema"] == PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION
    assert pilot["status"] == "planned_review_gated_not_downloaded"
    assert pilot["river_id"] == "colorado_river"
    assert pilot["section_id"] == "grand_canyon_lees_ferry_to_diamond_creek"
    assert pilot["route_style"] == "rowing_oar_rig"
    assert pilot["corridor_scope"]["status"] == "lees_ferry_pilot_slice_not_full_canyon_route"
    assert len(tiles) == 4
    assert {tile["tile_id"] for tile in tiles} == {
        "colorado_lees_ferry_tile_r0_c0",
        "colorado_lees_ferry_tile_r0_c1",
        "colorado_lees_ferry_tile_r1_c0",
        "colorado_lees_ferry_tile_r1_c1",
    }
    assert all("3dep_dem_export" in tile["download_specs"] for tile in tiles)
    assert all("naip_export" in tile["download_specs"] for tile in tiles)
    assert "elevation.nationalmap.gov" in tiles[0]["download_specs"]["3dep_dem_export"]["url"]
    assert "gis.apfo.usda.gov" in tiles[0]["download_specs"]["naip_export"]["url"]
    assert {
        "terrain_dem_or_lidar",
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "water_and_vegetation_masks",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    }.issubset(classes)
    assert "usbr_glen_canyon_release_context" in classes["seasonal_flow_or_release_history"]["source_ids"]
    assert classes["hydrography_and_centerline"]["status"] == "nhd_hu8_alignment_diagnostic_attached_review_pending"
    assert COLORADO_NHD_HU8_MANIFEST_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_MAINSTEM_MANIFEST_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_MAINSTEM_CANDIDATE_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_MAINSTEM_STATIONING_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_CROSS_SECTION_SEED_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert classes["seasonal_flow_or_release_history"]["status"] == (
        "usgs_daily_discharge_and_usbr_release_context_attached_review_pending"
    )
    assert COLORADO_USBR_TOTAL_RELEASE_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert COLORADO_USBR_RELEASE_CONTEXT_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert classes["water_and_vegetation_masks"]["status"] == "nhd_water_prior_attached_release_sandbar_masks_pending"
    assert COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert COLORADO_NHD_WATER_PRIOR_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert "sandbar_wet_bank_mask_2048.png" in " ".join(classes["water_and_vegetation_masks"]["target_outputs"])
    assert (
        pilot["unreal_import_targets"]["future_production_map"]
        == "/Game/RaftSim/Maps/Production/L_ColoradoGrandCanyon_LeesFerryRowing"
    )


def test_colorado_usbr_glen_canyon_release_context_records_official_series_and_gauge_comparisons():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    raw_release = json.loads((colorado_dir / COLORADO_USBR_TOTAL_RELEASE_FILE).read_text())
    context = json.loads((colorado_dir / COLORADO_USBR_RELEASE_CONTEXT_FILE).read_text())

    assert COLORADO_USBR_TOTAL_RELEASE_FILE in source_manifest["artifacts"]["gauges"]
    assert COLORADO_USBR_RELEASE_CONTEXT_FILE in source_manifest["artifacts"]["gauges"]
    assert any(source["source_id"] == "usbr_glen_canyon_release_context" for source in source_manifest["sources"])
    assert any(
        artifact["artifact_id"] == "usbr_glen_canyon_total_release_daily"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert raw_release["columns"] == ["datetime", "total release"]
    assert len(raw_release["data"]) == 23125
    assert context["status"] == "official_usbr_release_series_attached_review_gated"
    assert context["source"]["dashboard_variable_id"] == "42"
    assert context["source"]["raw_sha256"] == "41e5929b5dc6dc3e953943ed3e855284b5458001502ce8c449939c6c293c0ca0"
    assert context["usbr_total_release_summary"]["all_available"]["valid_value_count"] == 23124
    assert context["usbr_total_release_summary"]["all_available"]["first_valid_date"] == "1963-03-14"
    assert context["usbr_total_release_summary"]["all_available"]["last_valid_date"] == "2026-07-05"
    assert context["usbr_total_release_summary"]["water_year_2026_to_date"]["mean_cfs"] == 8426.237
    assert context["release_visual_band_candidates"]["low_release_cfs"] == [7044.695, 7868.888]
    assert context["release_visual_band_candidates"]["status"] == (
        "review_gated_initial_thresholds_not_final_gameplay_bands"
    )
    lees_comparison = context["daily_comparisons"][0]
    assert lees_comparison["comparison_id"] == "usbr_total_release_vs_usgs_09380000_lees_ferry_same_date"
    assert lees_comparison["overlapping_valid_days"] == 23122
    assert lees_comparison["mean_absolute_delta_cfs"] == 110.058


def test_colorado_nhd_hu8_lees_ferry_extract_records_stitched_source_overlay():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    manifest = json.loads((colorado_dir / COLORADO_NHD_HU8_MANIFEST_FILE).read_text())
    flowlines = json.loads((colorado_dir / COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE).read_text())
    support = json.loads((colorado_dir / COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE).read_text())

    assert COLORADO_NHD_HU8_MANIFEST_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(source["source_id"] == "usgs_nhd_hu8_lees_ferry_stitched_extract" for source in source_manifest["sources"])
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_bbox_extract"
        for artifact in pull_manifest["pulled_artifacts"]
    )

    assert manifest["status"] == "official_nhd_hu8_bbox_extract_attached_review_gated_not_ordered_centerline"
    assert [product["hu8"] for product in manifest["source_products"]] == ["14070006", "14070007", "15010001"]
    assert manifest["mainstem_evidence"]["named_colorado_river_flowline_hits"] == 59
    assert manifest["mainstem_evidence"]["named_paria_river_flowline_hits"] == 15
    assert manifest["mainstem_evidence"]["named_cathedral_wash_flowline_hits"] == 8
    assert "150100010303 Cathedral Wash-Colorado River" in manifest["mainstem_evidence"]["intersecting_huc12s"]
    assert manifest["layer_summary"]["14070006"]["NHDFlowline"]["bbox_intersecting_feature_count"] == 172
    assert manifest["layer_summary"]["14070007"]["NHDFlowline"]["bbox_intersecting_feature_count"] == 61
    assert manifest["layer_summary"]["15010001"]["NHDFlowline"]["bbox_intersecting_feature_count"] == 272
    assert manifest["output_checksums"]["flowline_geojson"]["sha256"] == (
        "614b831f1b89eb027815d5af6d62d75d1eae6251ada3dbbb807a8eb7d8eddb97"
    )
    assert manifest["output_checksums"]["support_layers_geojson"]["sha256"] == (
        "889fbe56849a4a3d843f8fc41d12dc48c788a43dd0b4fa390a4eea807c914838"
    )
    assert len(flowlines["features"]) == 505
    assert len(support["features"]) == 20


def test_colorado_nhd_mainstem_candidate_orders_exact_graph_without_promotion():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    manifest = json.loads((colorado_dir / COLORADO_NHD_MAINSTEM_MANIFEST_FILE).read_text())
    mainstem = json.loads((colorado_dir / COLORADO_NHD_MAINSTEM_CANDIDATE_FILE).read_text())

    assert COLORADO_NHD_MAINSTEM_MANIFEST_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_NHD_MAINSTEM_CANDIDATE_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_mainstem_candidate"
        for artifact in pull_manifest["pulled_artifacts"]
    )

    assert manifest["status"] == "derived_review_gated_mainstem_candidate_not_river_mile_stationing"
    assert manifest["selection"]["raw_named_feature_count"] == 59
    assert manifest["selection"]["unique_segment_count"] == 57
    assert manifest["selection"]["duplicate_overlap_segment_count"] == 2
    assert manifest["graph_diagnostic"]["snapping_used"] is False
    assert manifest["graph_diagnostic"]["branch_node_count"] == 0
    assert manifest["graph_diagnostic"]["ordered_segment_count"] == 57
    assert manifest["graph_diagnostic"]["unvisited_segment_count"] == 0
    assert manifest["summary"]["candidate_vertex_count"] == 145
    assert manifest["summary"]["source_length_km_sum"] == 24.205286
    assert manifest["summary"]["preview_local_length_m"] == 24223.694
    assert manifest["output_checksums"]["mainstem_candidate_geojson"]["sha256"] == (
        "c6495f43181f46177a61674b3062df84b35a9a754f31746d5ec44dfd9ef5d692"
    )
    assert len(mainstem["features"]) == 1
    assert mainstem["features"][0]["properties"]["status"] == (
        "derived_review_gated_mainstem_candidate_not_river_mile_stationing"
    )


def test_colorado_nhd_stationing_candidate_adds_preview_metric_scaffold():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    stationing = json.loads((colorado_dir / COLORADO_NHD_MAINSTEM_STATIONING_FILE).read_text())

    assert COLORADO_NHD_MAINSTEM_STATIONING_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_mainstem_stationing_candidate"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert stationing["review_status"] == "metric_stationing_candidate_review_required_not_final_crs_or_river_mile_stationing"
    assert stationing["local_transform"]["type"] == "local_equirectangular_preview_meters"
    assert stationing["summary"]["vertex_count"] == 145
    assert stationing["summary"]["station_sample_count"] == 244
    assert stationing["summary"]["length_m_geodesic_vertices"] == 24223.694
    assert stationing["summary"]["source_length_km_nhd_sum"] == 24.205286
    assert stationing["station_samples"][0]["station_m"] == 0.0
    assert stationing["station_samples"][-1]["station_m"] == 24223.694


def test_colorado_nhd_cross_section_seeds_are_review_lines_not_banks():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    manifest = json.loads((colorado_dir / COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE).read_text())
    seeds = json.loads((colorado_dir / COLORADO_NHD_CROSS_SECTION_SEED_FILE).read_text())

    assert COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_NHD_CROSS_SECTION_SEED_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_cross_section_seed_candidates"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert manifest["review_status"] == "seed_candidates_review_required_not_banks_or_cross_sections"
    assert manifest["parameters"]["half_width_m_each_side"] == 200.0
    assert manifest["parameters"]["interval_m"] == 200.0
    assert manifest["summary"]["feature_count"] == 123
    assert manifest["summary"]["last_station_m"] == 24223.694
    assert manifest["output_checksums"]["cross_section_seed_geojson"]["sha256"] == (
        "1a6978469e60cd07bb7a6d755ae0a79182a9198246bdf2114446f2b03c52a9ce"
    )
    assert len(seeds["features"]) == 123
    assert seeds["features"][0]["properties"]["review_status"] == (
        "seed_line_requires_bank_dem_imagery_release_and_oarsman_review"
    )


def test_colorado_nhd_alignment_diagnostic_samples_preview_masks_without_acceptance():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    diagnostic = json.loads((colorado_dir / COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE).read_text())

    assert COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_naip_dem_alignment_diagnostic"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert diagnostic["status"] == "diagnostic_preview_masks_not_alignment_acceptance"
    assert diagnostic["summary"]["station_sample_count"] == 244
    assert diagnostic["summary"]["station_samples_in_bounds"] == 219
    assert diagnostic["summary"]["station_samples_out_of_bounds"] == 25
    assert diagnostic["summary"]["station_water"]["ge_0_35_fraction"] == 0.7443
    assert diagnostic["summary"]["cross_section_count"] == 123
    assert diagnostic["summary"]["cross_sections_with_center_in_bounds"] == 109
    assert diagnostic["summary"]["cross_sections_out_of_bounds"] == 14
    assert diagnostic["summary"]["cross_section_center_water"]["ge_0_35_fraction"] == 0.7523
    assert diagnostic["review_flags"]["station_low_water_samples_recorded_count"] == 56
    assert diagnostic["review_flags"]["cross_section_low_center_water_count"] == 27
    assert diagnostic["sampling"]["note"].endswith("high agreement is not production acceptance.")


def test_colorado_nhd_water_prior_is_editor_mask_aid_not_segmentation_truth():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    manifest = json.loads((colorado_dir / COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE).read_text())

    assert COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE in source_manifest["artifacts"]["imagery"]
    assert COLORADO_NHD_WATER_PRIOR_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "colorado_nhd_hu8_lees_ferry_water_prior"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (colorado_dir / COLORADO_NHD_WATER_PRIOR_FILE).is_file()
    assert manifest["status"] == "generated_review_gated_alignment_prior_not_segmentation_truth"
    assert manifest["processing"]["station_sample_count"] == 244
    assert manifest["processing"]["station_samples_outside_bbox"] == 25
    assert manifest["processing"]["line_width_px"] == 36
    assert manifest["processing"]["gaussian_blur_radius_px"] == 8
    assert manifest["summary"]["nonzero_pixel_fraction"] == 0.076495
    assert manifest["summary"]["sha256"] == "c7cf5be58214c53a0b04aada52cd98faa96c8e3f7b670bb562bdebf6ff5d7936"


def test_pacuare_production_import_pilot_exposes_source_product_plan_and_review_gates():
    pilot = build_pacuare_production_import_pilot()
    classes = {entry["class_id"]: entry for entry in pilot["required_source_classes"]}
    seeds = {entry["product_id"]: entry for entry in pilot["seed_products"]}

    assert PACUARE_PRODUCTION_IMPORT_PILOT_FILE == "production_import_pilot.json"
    assert pilot["schema"] == PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION
    assert pilot["status"] == "planned_review_gated_source_selection_pending"
    assert pilot["river_id"] == "pacuare"
    assert pilot["section_id"] == "lower_pacuare_planning_corridor"
    assert pilot["route_style"] == "guided_paddle_raft"
    assert pilot["corridor_scope"]["status"] == "draft_lower_pacuare_planning_bounds_not_surveyed_route"
    assert "copernicus_dem_glo30_public_tiles" in seeds
    assert "nasa_gibs_modis_demshade_preview_drape" in seeds
    assert "pacuare_official_source_access_plan" in seeds
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert {
        "terrain_dem_or_lidar",
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "water_and_vegetation_masks",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    }.issubset(classes)
    assert "snit_cr_idecori" in classes["hydrography_and_centerline"]["source_ids"]
    assert "imn_costa_rica" in classes["seasonal_flow_or_release_history"]["source_ids"]
    assert "sinac_minae" in classes["protected_area_and_access_context"]["source_ids"]
    assert "wet_rock_waterfall_mist_mask_2048.png" in " ".join(
        classes["water_and_vegetation_masks"]["target_outputs"]
    )
    assert (
        classes["hydrography_and_centerline"]["status"]
        == "preview_centerline_scaffold_attached_official_hydrography_pending"
    )
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert pilot["procedural_generation_plan"]["status"] == "allowed_only_as_manifest_recorded_review_gated_fill"
    assert (
        pilot["unreal_import_targets"]["future_production_map"]
        == "/Game/RaftSim/Maps/Production/L_PacuareRainforest_LowerPacuare"
    )


def test_pacuare_official_source_access_plan_records_catalogs_without_downloads():
    plan_path = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica" / PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE
    plan = json.loads(plan_path.read_text())
    catalogs = {catalog["source_id"]: catalog for catalog in plan["reviewed_official_service_catalogs"]}
    layer_queue = {entry["candidate_id"]: entry for entry in plan["candidate_layer_review_queue"]}

    assert plan["schema"] == "raftsim.pacuare.official_source_access_plan.v1"
    assert plan["status"] == "official_service_catalogs_recorded_no_layer_download"
    assert plan["policy"]["no_layer_downloaded_or_promoted"] is True
    assert {"snit_ogc_services_catalog", "snit_recurso_hidrico_viewer", "direccion_de_agua_sinigirh_geoservices"}.issubset(
        catalogs
    )
    assert "Aguas:DA_AFOROS" in catalogs["direccion_de_agua_sinigirh_geoservices"]["candidate_layers"]
    assert "Aguas:JASEC_ESTACIONES_HIDROMETRICAS" in catalogs["direccion_de_agua_sinigirh_geoservices"]["candidate_layers"]
    assert "Aguas:DA_UNIDADES_HIDROLOGICAS" in catalogs["direccion_de_agua_sinigirh_geoservices"]["candidate_layers"]
    assert "Aguas:DA_Cuencas_Hidrograficas_CR" in catalogs["direccion_de_agua_sinigirh_geoservices"]["candidate_layers"]
    assert layer_queue["da_aforos"]["target_outputs"] == [
        "hydrology/production_import_pilot/discharge_or_stage_station_review.json"
    ]
    assert layer_queue["jasec_estaciones_hidrometricas"]["target_outputs"] == [
        "hydrology/production_import_pilot/discharge_or_stage_station_review.json"
    ]
    assert any("terms" in item for item in plan["per_layer_required_metadata"])
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in plan["downstream_manifest_targets"]


def test_pacuare_direccion_de_agua_capabilities_are_archived_as_metadata_only():
    base = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    raw_path = base / PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE
    summary = json.loads((base / PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE).read_text())
    selected_names = {layer["name"] for layer in summary["selected_candidate_layers"]}

    assert raw_path.is_file()
    assert summary["schema"] == "raftsim.pacuare.da_sinigirh_wms_capabilities_summary.v1"
    assert summary["status"] == "capabilities_archived_layer_metadata_only_no_features_downloaded"
    assert summary["advertised_named_layer_count"] == 52
    assert summary["advertised_root_srs"] == ["EPSG:4326", "EPSG:5367", "EPSG:5456"]
    assert summary["advertised_root_bbox_wgs84"]["minx"] < summary["pacuare_planning_bounds_wgs84"]["min_lon"]
    assert summary["advertised_root_bbox_wgs84"]["maxx"] > summary["pacuare_planning_bounds_wgs84"]["max_lon"]
    assert summary["raw_capabilities_sha256"] == hashlib.sha256(raw_path.read_bytes()).hexdigest()
    assert "Aguas:DA_AFOROS" in selected_names
    assert "Aguas:JASEC_ESTACIONES_HIDROMETRICAS" in selected_names
    assert "Aguas:DA_UNIDADES_HIDROLOGICAS" in selected_names
    assert "Aguas:DA_Cuencas_Hidrograficas_CR" in selected_names
    assert all(layer["feature_download_status"] == "not_downloaded_metadata_only" for layer in summary["selected_candidate_layers"])


def test_pacuare_preview_centerline_scaffold_is_not_official_hydrography():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    manifest = json.loads((pacuare_dir / PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE).read_text())
    centerline = json.loads((pacuare_dir / PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE).read_text())
    stationing = json.loads((pacuare_dir / PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE).read_text())

    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE in source_manifest["artifacts"]["hydrography"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE in source_manifest["artifacts"]["hydrography"]
    assert PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "pacuare_unreal_preview_centerline_scaffold"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert manifest["status"] == "generated_review_gated_preview_route_not_official_hydrography"
    assert manifest["parameters"]["vertex_count"] == 129
    assert manifest["parameters"]["station_interval_m"] == 250.0
    assert manifest["summary"]["centerline_vertex_count"] == 129
    assert manifest["summary"]["station_sample_count"] == 184
    assert manifest["summary"]["length_m_preview_wgs84_linearized"] == 45642.42
    assert manifest["output_checksums"]["centerline_geojson"]["sha256"] == (
        "e1fe18636df9c16accc52633e718814028e1013b8e4ee96111d7614ad58f511e"
    )
    assert manifest["output_checksums"]["stationing_json"]["sha256"] == (
        "fbedd0fe2aee67377d60b8ca3116424a767e39755aee3500c056d82fcc822ee4"
    )
    assert len(centerline["features"]) == 1
    assert centerline["features"][0]["properties"]["status"] == (
        "preview_scaffold_from_unreal_curve_not_official_hydrography"
    )
    assert len(centerline["features"][0]["geometry"]["coordinates"]) == 129
    assert stationing["review_status"] == (
        "preview_metric_stationing_review_required_not_final_crs_or_official_route"
    )
    assert stationing["summary"]["station_sample_count"] == 184
    assert stationing["station_samples"][0]["station_m"] == 0.0
    assert stationing["station_samples"][-1]["station_m"] == 45642.42


def test_production_environment_gap_register_tracks_lifelike_blockers_for_all_rivers():
    register = build_production_environment_gap_register()
    rivers = {entry["river_id"]: entry for entry in register["rivers"]}

    assert register["schema"] == PRODUCTION_ENVIRONMENT_GAP_REGISTER_SCHEMA_VERSION
    assert register["status"] == "active_goal_gap_register_all_rivers_preview_only_not_lifelike"
    assert "social_media_reference_only_until_explicit_item_rights_clear" in register["policy"]
    assert register["policy"]["do_not_download_scrape_train_on_or_package_third_party_media_without_rights"] is True
    assert {
        "terrain_dem_or_lidar",
        "seasonal_flow_or_release_history",
        "production_art_assets_or_first_party_procedural_equivalents",
        "unreal_lifelike_capture_and_performance_evidence",
    }.issubset(set(register["source_classes"]))
    assert {"american_south_fork", "colorado_river", "pacuare"} == set(rivers)
    assert any(lead["source_id"] == "snit_cr_idecori" for lead in register["reviewed_source_leads_2026_07_06"])
    assert any(target["target"] == "water_foam_spray_mist_and_wetness" for target in register["global_visual_replacement_targets"])

    south_fork_p0 = {item["source_class"] for item in rivers["american_south_fork"]["p0_next_pulls_or_attachments"]}
    colorado_p0 = {item["source_class"] for item in rivers["colorado_river"]["p0_next_pulls_or_attachments"]}
    pacuare_p0 = {item["source_class"] for item in rivers["pacuare"]["p0_next_pulls_or_attachments"]}

    assert {"hydrography_and_centerline", "seasonal_flow_or_release_history", "guide_and_reference_media_annotations"}.issubset(south_fork_p0)
    assert {"hydrography_and_centerline", "seasonal_flow_or_release_history", "guide_and_reference_media_annotations"}.issubset(colorado_p0)
    assert {
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "seasonal_flow_or_release_history",
        "guide_and_reference_media_annotations",
    }.issubset(pacuare_p0)
    assert "hydrology/south_fork_modern_flow_source_selection.json" in rivers["american_south_fork"]["attached_preview_inputs"]
    assert (
        "hydrology/cdec_cbr_event_flow_stage_2026-07-05_2026-07-06.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert "hydrology/cdec_terms_flags_and_station_relation_review.json" in rivers["american_south_fork"]["attached_preview_inputs"]
    assert (
        "hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_bbox_extract_manifest.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_flowline_bbox_extract.geojson"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_south_fork_mainstem_candidate.geojson"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_mainstem_stationing_candidate.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_cross_section_seed_candidates.geojson"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "hydrography/nhd_hu8_18020129_naip_dem_alignment_diagnostic.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert (
        "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png"
        in rivers["american_south_fork"]["attached_preview_inputs"]
    )
    assert "USGS 11445500" in rivers["american_south_fork"]["procedural_generation_allowlist"][2]
    assert "release-band" in rivers["colorado_river"]["procedural_generation_allowlist"][2]
    assert COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_WATER_PRIOR_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_HU8_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_HU8_FLOWLINE_EXTRACT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_HU8_SUPPORT_EXTRACT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_MAINSTEM_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_MAINSTEM_CANDIDATE_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_MAINSTEM_STATIONING_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_CROSS_SECTION_SEED_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_CROSS_SECTION_SEED_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NHD_ALIGNMENT_DIAGNOSTIC_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_USBR_TOTAL_RELEASE_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_USBR_RELEASE_CONTEXT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert "waterfalls" in rivers["pacuare"]["completion_gate"]


def test_reference_media_review_queue_is_link_only_and_station_aware():
    queue = json.loads((REAL_WORLD_DATA_DIR / "reference_media_review_queue.json").read_text())
    link_manifest = json.loads((REAL_WORLD_DATA_DIR / "reference_media_link_manifest.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )

    assert queue["schema"] == "raftsim.reference_media_review_queue.v1"
    assert queue["status"] == "station_aware_review_queue_no_media_downloaded"
    assert "Do not download" in queue["policy"]["storage"]
    assert link_manifest["review_queue"] == "reference_media_review_queue.json"
    assert (
        photoreal_sources["reference_media_review_queue"]
        == "physics/data/real_world/reference_media_review_queue.json"
    )

    targets_by_river = {}
    for target in queue["review_targets"]:
        targets_by_river.setdefault(target["river_id"], []).append(target)
        assert target["candidate_source_ids"]
        assert target["flow_context_needed"]
        assert target["annotation_outputs"]
        assert target["rights_status"] == "candidate_links_only"

    assert {"american_south_fork", "colorado_river", "pacuare"} == set(targets_by_river)
    assert all(len(targets) >= 3 for targets in targets_by_river.values())
    assert any("rescue" in target["target_id"] for target in queue["review_targets"])


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
    assert (output_dir.parent / PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE).exists()
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
