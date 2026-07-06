import hashlib
import json
from pathlib import Path

import numpy as np

from raftsim.real_world import (
    CANDIDATE_RIVER_INVENTORY_FILE,
    CANDIDATE_RIVER_INVENTORY_SCHEMA_VERSION,
    COLORADO_ACCESS_POINTS_FILE,
    COLORADO_ACCESS_PUBLICATION_REVIEW_FILE,
    COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE,
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
    COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
    COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE,
    COLORADO_PRODUCTION_BANKS_DRAFT_FILE,
    COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE,
    COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
    COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
    COLORADO_PRODUCTION_IMPORT_PILOT_FILE,
    COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE,
    COLORADO_PRODUCTION_SANDBARS_FILE,
    COLORADO_RELEASE_BAND_REVIEW_FILE,
    COLORADO_SOURCE_METADATA_REVIEW_FILE,
    COLORADO_USBR_RELEASE_CONTEXT_FILE,
    COLORADO_USBR_TOTAL_RELEASE_FILE,
    COURSE_ELEVATION_EXTRACTION_FILE,
    COURSE_ELEVATION_EXTRACTION_SCHEMA_VERSION,
    PACUARE_ACCESS_CONSERVATION_POLICY_FILE,
    PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE,
    PACUARE_CLOUD_SHADOW_REVIEW_FILE,
    PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE,
    PACUARE_FLASH_RESPONSE_REVIEW_FILE,
    PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE,
    PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE,
    PACUARE_RAINFALL_STATION_REVIEW_FILE,
    PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE,
    PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE,
    PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE,
    PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE,
    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE,
    PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE,
    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE,
    PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE,
    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE,
    PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE,
    PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_FILE,
    PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE,
    PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE,
    PACUARE_PRODUCTION_BANKS_DRAFT_FILE,
    PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE,
    PACUARE_PRODUCTION_IMPORT_PILOT_FILE,
    PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE,
    PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE,
    PACUARE_SNIT_CONFIG_FILE,
    PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE,
    PACUARE_SNIT_LAYER_LIST_SCRIPT_FILE,
    PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE,
    PACUARE_SNIT_OGC_CATALOG_FILE,
    PACUARE_SOURCE_METADATA_REVIEW_FILE,
    PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE,
    PRODUCTION_ENVIRONMENT_GAP_REGISTER_SCHEMA_VERSION,
    RAPID_REVIEW_EDITOR_WORKFLOW_FILE,
    RAPID_REVIEW_EDITOR_WORKFLOW_SCHEMA_VERSION,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE,
    RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_SCHEMA_VERSION,
    REFERENCE_MEDIA_ANNOTATIONS_FILE,
    REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE,
    PRODUCTION_IMPORT_PILOT_SCHEMA_VERSION,
    SOUTH_FORK_ACCESS_POINTS_FILE,
    SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE,
    SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE,
    SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE,
    SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE,
    SOUTH_FORK_FLOW_BAND_REVIEW_FILE,
    SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE,
    SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
    SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE,
    SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE,
    SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE,
    SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE,
    SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE,
    SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE,
    SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE,
    SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE,
    adaptive_solver_parameters,
    build_candidate_river_inventory_package,
    build_colorado_access_points_geojson,
    build_colorado_access_publication_review,
    build_colorado_camps_and_beaches_review_geojson,
    build_colorado_no_publish_sensitive_polygons_geojson,
    build_colorado_oarsman_route_publication_notes,
    build_colorado_production_import_pilot,
    build_colorado_river_mile_markers_geojson,
    build_colorado_release_band_review,
    build_colorado_sandbar_review_seeds_geojson,
    build_course_elevation_extraction,
    build_pacuare_access_conservation_policy,
    build_pacuare_discharge_stage_station_review,
    build_pacuare_flash_response_review,
    build_pacuare_production_banks_draft_geojson,
    build_pacuare_production_centerline_draft_geojson,
    build_pacuare_production_import_pilot,
    build_pacuare_protected_area_publication_sensitivity,
    build_pacuare_rapid_access_stationing_draft_geojson,
    build_pacuare_rainfall_station_review,
    build_player_selection_model,
    build_production_environment_gap_register,
    build_rapid_review_editor_workflow,
    build_rapid_review_flow_difficulty_mapping,
    build_real_world_corridor_package,
    build_reference_media_annotations_geojson,
    build_reference_media_rights_manifest,
    build_south_fork_access_points_geojson,
    build_south_fork_access_publication_review,
    build_south_fork_evacuation_rescue_routes_geojson,
    build_south_fork_flow_band_review,
    build_south_fork_production_source_gate_review,
    build_south_fork_no_publish_sensitive_polygons_geojson,
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
    assert {
        "elevation",
        "hydrography",
        "imagery",
        "gauges",
        "guide_references",
        "access_and_protected_context",
        "field_media",
    }.issubset(set(manifest["artifacts"]))
    assert COURSE_ELEVATION_EXTRACTION_FILE in manifest["artifacts"]["elevation"]
    assert RAPID_REVIEW_FLOW_DIFFICULTY_MAPPING_FILE in manifest["artifacts"]["guide_references"]
    assert SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_PULL_MANIFEST_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_IMPORT_PILOT_DERIVATIVES_MANIFEST_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE in manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_ACCESS_POINTS_FILE in manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE in manifest["artifacts"]["access_and_protected_context"]
    assert any(
        fetch["fetch_id"] == "sfa_access_publication_sensitivity_review"
        for fetch in manifest["remote_fetches"]
    )
    assert any(
        fetch["fetch_id"] == "sfa_cdec_cbr_a25_seasonal_window_wy2026_to_2026_07_06"
        for fetch in manifest["remote_fetches"]
    )
    assert any(
        fetch["fetch_id"] == "sfa_cdec_cbr_multiyear_flow_review_2021_10_01_2026_07_06"
        for fetch in manifest["remote_fetches"]
    )
    assert "hydrology/cdec_terms_flags_and_station_relation_review.json" in manifest["artifacts"]["gauges"]
    assert "hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json" in manifest["artifacts"]["gauges"]
    assert SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE in manifest["artifacts"]["gauges"]
    assert SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE in manifest["artifacts"]["gauges"]
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
    assert SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in manifest["artifacts"]["hydrography"]
    assert SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE in manifest["artifacts"]["hydrography"]
    assert SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE in manifest["artifacts"]["hydrography"]
    assert SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in manifest["artifacts"]["hydrography"]
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
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in classes["terrain_dem_or_lidar"]["target_outputs"]
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in classes[
        "hydrography_and_centerline"
    ]["target_outputs"]
    assert SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert classes["water_and_vegetation_masks"]["status"] == "requires_new_derivatives_from_pilot_imagery_and_hydrography"
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json" in classes[
        "water_and_vegetation_masks"
    ]["target_outputs"]
    assert "imagery/production_import_pilot/nhd_mainstem_water_prior_2048.png" in classes[
        "water_and_vegetation_masks"
    ]["target_outputs"]
    assert SOUTH_FORK_FLOW_BAND_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert classes["protected_area_and_access_context"]["status"] == (
        "official_state_park_and_county_gis_leads_attached_review_required"
    )
    assert "ca_state_parks_marshall_gold_discovery" in classes["protected_area_and_access_context"]["source_ids"]
    assert "el_dorado_county_gis" in classes["protected_area_and_access_context"]["source_ids"]
    assert SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert SOUTH_FORK_ACCESS_POINTS_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert pilot["unreal_import_targets"]["future_production_map"] == "/Game/RaftSim/Maps/Production/L_SouthForkAmerican_ChiliBar"


def test_south_fork_source_metadata_review_attaches_pilot_tile_provenance_without_promoting():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((south_fork_dir / "production_source_pull_manifest.json").read_text())
    tile_pull_manifest = json.loads((south_fork_dir / "production_import_pilot_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((south_fork_dir / SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    photoreal_rivers = {river["river_id"]: river for river in photoreal_sources["rivers"]}
    attached_sources = rivers["american_south_fork"]["attached_sources_by_class"]

    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in source_manifest["artifacts"]["source_pulls"]
    assert tile_pull_manifest["metadata_review"] == SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE
    assert any(artifact["artifact_id"] == "south_fork_source_metadata_review" for artifact in pull_manifest["pulled_artifacts"])
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE}"
        in attached_sources["terrain_dem_or_lidar"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE}"
        in attached_sources["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "south_fork_source_metadata_review"
        for artifact in photoreal_rivers["american_south_fork"]["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.south_fork_source_metadata_review.v1"
    assert review["status"] == "pilot_tile_metadata_attached_review_gated_not_production_promoted"
    assert review["raw_response_policy"]["raw_service_payloads_committed"] is False
    assert len(review["official_service_payloads"]) == 4
    assert review["downloaded_tile_summary"]["download_count"] == 8
    assert review["usda_naip_metadata"]["item_query"]["primary_feature_count"] == 12
    assert review["usda_naip_metadata"]["item_query"]["date_min"] == "2022-07-20"
    assert review["usda_naip_metadata"]["item_query"]["date_max"] == "2022-07-21"
    assert review["usgs_3dep_metadata"]["item_query"]["primary_feature_count"] == 12
    assert review["usgs_3dep_metadata"]["item_query"]["overview_feature_count"] == 12
    assert review["usgs_3dep_metadata"]["item_query"]["date_min"] == "2012-03-04"
    assert review["usgs_3dep_metadata"]["item_query"]["date_max"] == "2023-10-13"
    assert any(
        "North American Vertical Datum of 1988" in datum
        for item in review["usgs_3dep_metadata"]["item_query"]["items"]
        for datum in item["vertical_datums"]
    )
    assert "claiming production-ready terrain or water masks" in review["forbidden_use"]


def test_south_fork_flow_band_review_compares_cdec_window_to_planning_bands():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    flow_presets = json.loads((south_fork_dir / "flow_presets.json").read_text())
    cdec_context = json.loads((south_fork_dir / "hydrology/cdec_cbr_a25_flow_context_2026-06-07_2026-07-06.json").read_text())
    source_selection = json.loads((south_fork_dir / "hydrology/south_fork_modern_flow_source_selection.json").read_text())
    review = build_south_fork_flow_band_review(flow_presets, cdec_context, source_selection)

    bands = {band["flow_band"]: band for band in review["reviewed_bands"]}
    assert review["status"] == "review_gated_do_not_promote_presets"
    assert review["cdec_window_summary"]["valid_sample_count"] == 2744
    assert review["cdec_window_summary"]["days_peak_ge_900_cfs"] == 25
    assert review["cdec_window_summary"]["days_peak_ge_1600_cfs"] == 9
    assert review["cdec_window_summary"]["days_peak_ge_3000_cfs"] == 0
    assert review["cdec_window_summary"]["total_hours_ge_900_cfs"] == 165.5
    assert review["cdec_window_summary"]["total_hours_ge_1600_cfs"] == 58.5
    assert bands["low_runnable"]["observed_peak_days_ge_planning_flow"] == 25
    assert bands["median_runnable"]["observed_peak_days_ge_planning_flow"] == 9
    assert bands["high_runnable"]["observed_peak_days_ge_planning_flow"] == 0
    assert bands["high_runnable"]["evidence_status"] == "not_observed_in_attached_30_day_context"


def test_south_fork_flow_band_review_artifact_is_review_gated():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((south_fork_dir / "production_source_pull_manifest.json").read_text())
    review = json.loads((south_fork_dir / SOUTH_FORK_FLOW_BAND_REVIEW_FILE).read_text())

    assert SOUTH_FORK_FLOW_BAND_REVIEW_FILE in source_manifest["artifacts"]["gauges"]
    assert any(artifact["artifact_id"] == "south_fork_flow_band_review" for artifact in pull_manifest["pulled_artifacts"])
    assert review["schema"] == "raftsim.south_fork_flow_band_review.v1"
    assert review["status"] == "review_gated_do_not_promote_presets"
    assert review["cdec_window_summary"]["flow_peak_max_cfs"] == 1688.0
    assert review["cdec_window_summary"]["stage_peak_max_ft"] == 4.04
    assert review["reviewed_bands"][2]["flow_band"] == "high_runnable"
    assert review["reviewed_bands"][2]["observed_peak_days_ge_planning_flow"] == 0
    assert "final preset retuning" in review["forbidden_use"]


def test_south_fork_cdec_seasonal_window_review_expands_context_without_promoting_presets():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((south_fork_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    review = json.loads((south_fork_dir / SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}

    assert SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE in source_manifest["artifacts"]["gauges"]
    assert any(
        artifact["artifact_id"] == "cdec_cbr_a25_seasonal_window_wy2026_to_2026_07_06"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE}"
        in rivers["american_south_fork"]["attached_sources_by_class"]["seasonal_flow_or_release_history"][
            "artifacts"
        ]
    )
    assert review["schema"] == "raftsim.south_fork_cdec_seasonal_window_review.v1"
    assert review["status"] == "water_year_to_date_cdec_context_attached_review_gated"
    assert review["data_policy"]["negative_cbr_flow_values_normalized_to_null"] is True
    assert review["data_policy"]["negative_cbr_flow_row_count"] == 47
    assert review["series"]["cbr_flow_cfs"]["valid_sample_count"] == 26581
    assert review["water_year_summary"]["flow_min_cfs"] == 198.0
    assert review["water_year_summary"]["flow_peak_max_cfs"] == 5660.0
    assert review["water_year_summary"]["days_peak_ge_900_cfs"] == 245
    assert review["water_year_summary"]["days_peak_ge_1600_cfs"] == 182
    assert review["water_year_summary"]["days_peak_ge_3000_cfs"] == 48
    bands = {item["flow_band_hint"]: item for item in review["threshold_review"]}
    assert bands["high_runnable"]["days_peak_ge_threshold"] == 48
    assert bands["high_runnable"]["promotion_decision"] == "review_evidence_only_do_not_retune_presets"
    assert "final preset retuning" in review["forbidden_use"]


def test_south_fork_cdec_multiyear_flow_review_adds_representative_context_without_promoting_presets():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((south_fork_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    review = json.loads((south_fork_dir / SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}

    assert SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE in source_manifest["artifacts"]["gauges"]
    assert any(
        artifact["artifact_id"] == "cdec_cbr_multiyear_flow_review_2021_10_01_2026_07_06"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE}"
        in rivers["american_south_fork"]["attached_sources_by_class"]["seasonal_flow_or_release_history"][
            "artifacts"
        ]
    )
    assert review["schema"] == "raftsim.south_fork_cdec_multiyear_flow_review.v1"
    assert review["status"] == "multiyear_cdec_cbr_flow_context_attached_review_gated"
    assert review["data_policy"]["negative_cbr_flow_values_normalized_to_null"] is True
    assert review["data_policy"]["negative_cbr_flow_row_count"] == 144
    assert review["series"]["valid_sample_count"] == 164992
    assert review["requested_window_summary"]["valid_flow_day_count"] == 1740
    assert review["requested_window_summary"]["flow_peak_max_cfs"] == 38489.0
    assert review["requested_window_summary"]["days_peak_ge_900_cfs"] == 1439
    assert review["requested_window_summary"]["days_peak_ge_1600_cfs"] == 1076
    assert review["requested_window_summary"]["days_peak_ge_3000_cfs"] == 364
    water_years = {item["water_year"]: item for item in review["water_year_summaries"]}
    assert water_years[2023]["flow_peak_max_cfs"] == 38489.0
    assert water_years[2023]["days_peak_ge_3000_cfs"] == 157
    bands = {item["flow_band_hint"]: item for item in review["threshold_review"]}
    assert bands["high_runnable"]["days_peak_ge_threshold"] == 364
    assert review["high_flow_outlier_review"]["required"] is True
    assert review["high_flow_outlier_review"]["sample_count_ge_trigger"] == 92
    assert review["high_flow_outlier_review"]["peak_cfs"] == 38489.0
    assert "final preset retuning" in review["forbidden_use"]
    assert "high-flow preset or feature-forcing tuning before peak/outlier review" in review["forbidden_use"]


def test_south_fork_production_source_gate_review_blocks_promotion_but_allows_next_renderer_iteration():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    gap_register = json.loads((REAL_WORLD_DATA_DIR / PRODUCTION_ENVIRONMENT_GAP_REGISTER_FILE).read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    artifact = json.loads((south_fork_dir / SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE).read_text())
    built = build_south_fork_production_source_gate_review()
    south_fork_gap = next(river for river in gap_register["rivers"] if river["river_id"] == "american_south_fork")
    south_fork_readiness = next(river for river in readiness["rivers"] if river["river_id"] == "american_south_fork")

    assert SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE in source_manifest["artifacts"]["source_pulls"]
    assert SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE in south_fork_gap["attached_preview_inputs"]
    assert (
        readiness["canonical_inputs"]["south_fork_production_source_gate_review"]
        == f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE}"
    )
    assert (
        south_fork_readiness["production_source_gate_review"]
        == f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE}"
    )
    assert artifact == built
    assert artifact["schema"] == "raftsim.south_fork_production_source_gate_review.v1"
    assert artifact["promotion_decision"]["can_drive_next_renderer_iteration"] is True
    assert artifact["promotion_decision"]["can_drive_production_terrain_or_water"] is False
    assert artifact["promotion_decision"]["decision"] == "do_not_promote_to_production_or_lifelike"

    gate_items = {item["source_class"]: item for item in artifact["source_gate_items"]}
    assert {
        "terrain_dem_or_lidar",
        "aerial_or_satellite_imagery",
        "hydrography_and_centerline",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    } == set(gate_items)
    assert SOUTH_FORK_NHD_MAINSTEM_CANDIDATE_FILE in gate_items["hydrography_and_centerline"]["attached_artifacts"]
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in gate_items["terrain_dem_or_lidar"]["attached_artifacts"]
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in gate_items["aerial_or_satellite_imagery"]["attached_artifacts"]
    assert SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE in gate_items["seasonal_flow_or_release_history"][
        "attached_artifacts"
    ]
    assert SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE in gate_items["seasonal_flow_or_release_history"][
        "attached_artifacts"
    ]
    assert SOUTH_FORK_FLOW_BAND_REVIEW_FILE in gate_items["seasonal_flow_or_release_history"]["attached_artifacts"]
    assert "official high-flow peak/outlier interpretation for flood-event samples" in gate_items[
        "seasonal_flow_or_release_history"
    ]["promotion_blockers"]
    assert "channel burning" in gate_items["terrain_dem_or_lidar"]["promotion_blockers"]
    assert "explicit permission or compatible license" in gate_items["guide_and_reference_media_annotations"][
        "promotion_blockers"
    ]


def test_south_fork_access_publication_review_artifact_tracks_official_source_leads():
    south_fork_dir = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar"
    source_manifest = json.loads((south_fork_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((south_fork_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal"
            / "Content"
            / "RaftSim"
            / "Rendering"
            / "photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((south_fork_dir / SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE).read_text())
    stationing = json.loads((south_fork_dir / SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE).read_text())
    access_points = json.loads((south_fork_dir / SOUTH_FORK_ACCESS_POINTS_FILE).read_text())
    no_publish = json.loads((south_fork_dir / SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE).read_text())
    evacuation_routes = json.loads((south_fork_dir / SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE).read_text())
    builder_review = build_south_fork_access_publication_review()
    expected_access_points = build_south_fork_access_points_geojson(builder_review, stationing)
    expected_no_publish = build_south_fork_no_publish_sensitive_polygons_geojson(builder_review, stationing)
    expected_evacuation_routes = build_south_fork_evacuation_rescue_routes_geojson(builder_review, stationing)

    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    photoreal_rivers = {river["river_id"]: river for river in photoreal_sources["rivers"]}
    source_ids = {source["source_id"] for source in review["sources_checked"]}

    assert review == builder_review
    assert access_points == expected_access_points
    assert no_publish == expected_no_publish
    assert evacuation_routes == expected_evacuation_routes
    assert SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_ACCESS_POINTS_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert any(
        artifact["artifact_id"] == "south_fork_access_publication_sensitivity_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "south_fork_access_annotation_scaffolds"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert review["schema"] == "raftsim.south_fork_access_publication_sensitivity_review.v1"
    assert review["status"] == "official_state_park_and_county_gis_leads_attached_review_gated"
    assert access_points["schema"] == "raftsim.south_fork_access_points.geojson.v1"
    assert access_points["status"] == "review_seed_access_points_not_authoritative_geometry"
    assert no_publish["schema"] == "raftsim.south_fork_no_publish_sensitive_polygons.geojson.v1"
    assert no_publish["status"] == "coarse_review_seed_no_publish_polygons_not_authoritative"
    assert evacuation_routes["schema"] == "raftsim.south_fork_evacuation_rescue_routes.geojson.v1"
    assert evacuation_routes["status"] == "coarse_review_seed_evacuation_rescue_routes_not_authoritative"
    assert len(access_points["features"]) == 3
    assert len(no_publish["features"]) == 3
    assert len(evacuation_routes["features"]) == 3
    assert all(feature["geometry"]["type"] == "Point" for feature in access_points["features"])
    assert all(feature["geometry"]["type"] == "Polygon" for feature in no_publish["features"])
    assert all(feature["geometry"]["type"] == "LineString" for feature in evacuation_routes["features"])
    assert {"ca_state_parks_marshall_gold_discovery", "el_dorado_county_gis"}.issubset(source_ids)
    assert len(review["station_review_zones"]) == 3
    assert review["sources_checked"][-1]["source_id"] == "blm_cronan_ranch_legacy_candidate"
    assert review["sources_checked"][-1]["http_status"] == 404
    assert "final access geometry" in review["forbidden_use"]
    assert (
        SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE
        in rivers["american_south_fork"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"][0]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_ACCESS_POINTS_FILE}"
        in rivers["american_south_fork"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE}"
        in rivers["american_south_fork"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/south_fork_american_chili_bar/{SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE}"
        in rivers["american_south_fork"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "south_fork_access_publication_sensitivity_review"
        for artifact in photoreal_rivers["american_south_fork"]["source_sample_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "south_fork_access_annotation_scaffolds"
        for artifact in photoreal_rivers["american_south_fork"]["source_sample_artifacts"]
    )


def test_south_fork_production_hydrography_drafts_are_review_gated():
    hydro_root = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / "hydrography"
    draft_root = hydro_root / "production_import_pilot"
    manifest = json.loads((REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE).read_text())
    centerline_path = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE
    banks_path = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE
    cross_sections_path = REAL_WORLD_DATA_DIR / "south_fork_american_chili_bar" / SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE
    centerline = json.loads(centerline_path.read_text())
    banks = json.loads(banks_path.read_text())
    cross_sections = json.loads(cross_sections_path.read_text())

    assert draft_root.is_dir()
    assert manifest["schema"] == "raftsim.south_fork_production_hydrography_drafts.manifest.v1"
    assert manifest["status"] == "draft_hydrography_artifacts_generated_review_required_not_production_authority"
    assert manifest["summary"]["centerline_vertex_count"] == 361
    assert manifest["summary"]["centerline_station_sample_count"] == 264
    assert manifest["summary"]["cross_section_count"] == 133
    assert manifest["summary"]["bank_offset_line_count"] == 2
    assert manifest["output_checksums"]["centerline"]["sha256"] == hashlib.sha256(centerline_path.read_bytes()).hexdigest()
    assert manifest["output_checksums"]["banks"]["sha256"] == hashlib.sha256(banks_path.read_bytes()).hexdigest()
    assert manifest["output_checksums"]["cross_sections"]["sha256"] == hashlib.sha256(
        cross_sections_path.read_bytes()
    ).hexdigest()
    assert centerline["properties"]["review_status"] == "draft_review_required_not_final_centerline"
    assert centerline["features"][0]["properties"]["status"] == (
        "draft_from_nhd_mainstem_candidate_review_gated_not_final_centerline"
    )
    assert banks["properties"]["review_status"] == "offset_lines_review_required_not_banks_or_wetted_width"
    assert len(banks["features"]) == 2
    assert cross_sections["properties"]["review_status"] == "draft_review_lines_not_solver_cross_sections"
    assert len(cross_sections["features"]) == 133
    assert all(
        feature["properties"]["status"] == "draft_production_import_cross_section_review_line_not_solver_section"
        for feature in cross_sections["features"]
    )


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
    assert COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_PRODUCTION_BANKS_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_PRODUCTION_SANDBARS_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert COLORADO_SOURCE_METADATA_REVIEW_FILE in classes["terrain_dem_or_lidar"]["target_outputs"]
    assert COLORADO_SOURCE_METADATA_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert classes["seasonal_flow_or_release_history"]["status"] == (
        "usgs_daily_discharge_and_usbr_release_context_attached_review_pending"
    )
    assert COLORADO_USBR_TOTAL_RELEASE_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert COLORADO_USBR_RELEASE_CONTEXT_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert COLORADO_RELEASE_BAND_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert classes["protected_area_and_access_context"]["status"] == (
        "official_nps_access_publication_leads_attached_review_required"
    )
    assert "nps_grand_canyon_river_trips_permits" in classes["protected_area_and_access_context"]["source_ids"]
    assert "nps_grand_canyon_noncommercial_river_trip_links" in classes["protected_area_and_access_context"]["source_ids"]
    assert COLORADO_ACCESS_PUBLICATION_REVIEW_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert COLORADO_ACCESS_POINTS_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert classes["water_and_vegetation_masks"]["status"] == "nhd_water_prior_attached_release_sandbar_masks_pending"
    assert COLORADO_NHD_WATER_PRIOR_MANIFEST_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert COLORADO_NHD_WATER_PRIOR_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert "sandbar_wet_bank_mask_2048.png" in " ".join(classes["water_and_vegetation_masks"]["target_outputs"])
    assert (
        pilot["unreal_import_targets"]["future_production_map"]
        == "/Game/RaftSim/Maps/Production/L_ColoradoGrandCanyon_LeesFerryRowing"
    )


def test_colorado_source_metadata_review_attaches_pilot_tile_provenance_without_promoting():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    tile_pull_manifest = json.loads((colorado_dir / "production_import_pilot_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((colorado_dir / COLORADO_SOURCE_METADATA_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    photoreal_rivers = {river["river_id"]: river for river in photoreal_sources["rivers"]}
    attached_sources = rivers["colorado_river"]["attached_sources_by_class"]

    assert COLORADO_SOURCE_METADATA_REVIEW_FILE in source_manifest["artifacts"]["source_pulls"]
    assert tile_pull_manifest["metadata_review"] == COLORADO_SOURCE_METADATA_REVIEW_FILE
    assert any(artifact["artifact_id"] == "colorado_source_metadata_review" for artifact in pull_manifest["pulled_artifacts"])
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_SOURCE_METADATA_REVIEW_FILE}"
        in attached_sources["terrain_dem_or_lidar"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_SOURCE_METADATA_REVIEW_FILE}"
        in attached_sources["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_source_metadata_review"
        for artifact in photoreal_rivers["colorado_river"]["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.colorado_source_metadata_review.v1"
    assert review["status"] == "pilot_tile_metadata_attached_review_gated_not_production_promoted"
    assert review["raw_response_policy"]["raw_service_payloads_committed"] is False
    assert len(review["official_service_payloads"]) == 4
    assert review["downloaded_tile_summary"]["download_count"] == 8
    assert review["usda_naip_metadata"]["item_query"]["primary_feature_count"] == 9
    assert review["usda_naip_metadata"]["item_query"]["date_min"] == "2021-10-15"
    assert review["usda_naip_metadata"]["item_query"]["date_max"] == "2021-10-15"
    assert review["usgs_3dep_metadata"]["item_query"]["primary_feature_count"] == 9
    assert review["usgs_3dep_metadata"]["item_query"]["overview_feature_count"] == 12
    assert review["usgs_3dep_metadata"]["item_query"]["date_min"] == "2022-11-10"
    assert review["usgs_3dep_metadata"]["item_query"]["date_max"] == "2023-09-16"
    assert any(
        "North American Vertical Datum of 1988" in datum
        for item in review["usgs_3dep_metadata"]["item_query"]["items"]
        for datum in item["vertical_datums"]
    )
    assert "claiming production-ready canyon terrain or release-aware water masks" in review["forbidden_use"]


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


def test_colorado_release_band_review_compares_usbr_history_to_planning_bands():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    flow_presets = json.loads((colorado_dir / "flow_presets.json").read_text())
    usbr_total_release = json.loads((colorado_dir / COLORADO_USBR_TOTAL_RELEASE_FILE).read_text())
    release_context = json.loads((colorado_dir / COLORADO_USBR_RELEASE_CONTEXT_FILE).read_text())
    review = build_colorado_release_band_review(flow_presets, usbr_total_release, release_context)

    bands = {band["flow_band"]: band for band in review["reviewed_bands"]}

    assert review["status"] == "review_gated_do_not_promote_release_bands"
    assert (
        bands["low_release_planning"]["window_summaries"]["water_year_2026_to_date"]["days_ge_planning_flow"]
        == 194
    )
    assert (
        bands["moderate_release_planning"]["window_summaries"]["water_year_2026_to_date"]["days_ge_planning_flow"]
        == 0
    )
    assert (
        bands["high_release_planning"]["window_summaries"]["water_year_2026_to_date"]["days_ge_planning_flow"]
        == 0
    )
    assert (
        bands["high_release_planning"]["window_summaries"]["post_2000_operations"]["days_ge_planning_flow"]
        == 278
    )
    assert bands["moderate_release_planning"]["evidence_status"] == (
        "not_observed_in_water_year_2026_daily_release_context"
    )
    assert bands["low_release_planning"]["evidence_status"] == (
        "observed_in_water_year_2026_daily_release_context_not_subdaily_validation"
    )


def test_colorado_release_band_review_artifact_is_review_gated():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    review = json.loads((colorado_dir / COLORADO_RELEASE_BAND_REVIEW_FILE).read_text())

    assert COLORADO_RELEASE_BAND_REVIEW_FILE in source_manifest["artifacts"]["gauges"]
    assert any(artifact["artifact_id"] == "colorado_release_band_review" for artifact in pull_manifest["pulled_artifacts"])
    assert review["schema"] == "raftsim.colorado_release_band_review.v1"
    assert review["status"] == "review_gated_do_not_promote_release_bands"
    bands = {band["flow_band"]: band for band in review["reviewed_bands"]}
    assert (
        bands["low_release_planning"]["window_summaries"]["water_year_2026_to_date"]["days_ge_planning_flow"]
        == 194
    )
    assert (
        bands["moderate_release_planning"]["window_summaries"]["water_year_2026_to_date"]["days_ge_planning_flow"]
        == 0
    )
    assert (
        bands["high_release_planning"]["window_summaries"]["post_2000_operations"]["days_ge_planning_flow"]
        == 278
    )
    assert "final release-band promotion" in review["forbidden_use"]


def test_colorado_access_publication_review_artifact_tracks_nps_source_leads():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((colorado_dir / COLORADO_ACCESS_PUBLICATION_REVIEW_FILE).read_text())
    stationing = json.loads((colorado_dir / COLORADO_NHD_MAINSTEM_STATIONING_FILE).read_text())
    river_miles = json.loads((colorado_dir / COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE).read_text())
    sandbars = json.loads((colorado_dir / COLORADO_PRODUCTION_SANDBARS_FILE).read_text())
    access_points = json.loads((colorado_dir / COLORADO_ACCESS_POINTS_FILE).read_text())
    no_publish = json.loads((colorado_dir / COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE).read_text())
    camps = json.loads((colorado_dir / COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE).read_text())
    oarsman_notes = json.loads((colorado_dir / COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE).read_text())
    builder_review = build_colorado_access_publication_review()
    expected_access_points = build_colorado_access_points_geojson(builder_review, stationing)
    expected_no_publish = build_colorado_no_publish_sensitive_polygons_geojson(builder_review, stationing)
    expected_camps = build_colorado_camps_and_beaches_review_geojson(builder_review, stationing)
    expected_oarsman_notes = build_colorado_oarsman_route_publication_notes(
        builder_review,
        river_miles,
        sandbars,
        camps,
    )

    source_ids = {source["source_id"] for source in review["sources_checked"]}
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    colorado_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "colorado_river")

    assert review == builder_review
    assert access_points == expected_access_points
    assert no_publish == expected_no_publish
    assert camps == expected_camps
    assert oarsman_notes == expected_oarsman_notes
    assert COLORADO_ACCESS_PUBLICATION_REVIEW_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert COLORADO_ACCESS_POINTS_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert any(
        artifact["artifact_id"] == "colorado_access_publication_sensitivity_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_access_publication_annotation_scaffolds"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert review["schema"] == "raftsim.colorado_access_publication_sensitivity_review.v1"
    assert review["status"] == "official_nps_river_access_publication_leads_attached_review_gated"
    assert access_points["schema"] == "raftsim.colorado_access_points.geojson.v1"
    assert access_points["status"] == "review_seed_access_points_not_authoritative_geometry"
    assert no_publish["schema"] == "raftsim.colorado_no_publish_sensitive_polygons.geojson.v1"
    assert no_publish["status"] == "coarse_review_seed_no_publish_polygons_not_authoritative"
    assert camps["schema"] == "raftsim.colorado_camps_and_beaches_review.geojson.v1"
    assert camps["status"] == "camp_beach_review_seeds_not_authoritative"
    assert oarsman_notes["schema"] == "raftsim.colorado_oarsman_route_publication_notes.v1"
    assert oarsman_notes["status"] == "oarsman_publication_notes_template_attached_review_required"
    assert len(access_points["features"]) == 3
    assert len(no_publish["features"]) == 3
    assert len(camps["features"]) == 4
    assert access_points["features"][-1]["geometry"] is None
    assert no_publish["features"][-1]["geometry"] is None
    assert {
        "nps_grand_canyon_river_trips_permits",
        "nps_grand_canyon_noncommercial_river_trip_links",
        "nps_grand_canyon_lees_ferry_diamond_creek_overview",
        "nps_grand_canyon_noncommercial_river_trip_regulations_pdf",
    }.issubset(source_ids)
    assert review["sources_checked"][0]["page_updated"] == "2026-06-03"
    assert review["sources_checked"][1]["page_updated"] == "2026-05-08"
    assert len(review["station_review_zones"]) == 3
    assert "permit or legal advice" in review["forbidden_use"]
    assert COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE in review["required_editor_annotations"]
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_ACCESS_PUBLICATION_REVIEW_FILE}"
        in rivers["colorado_river"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_ACCESS_POINTS_FILE}"
        in rivers["colorado_river"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE}"
        in rivers["colorado_river"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE}"
        in rivers["colorado_river"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/colorado_river_grand_canyon_rowing/{COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE}"
        in rivers["colorado_river"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_access_publication_sensitivity_review"
        for artifact in colorado_sources["source_sample_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_access_publication_annotation_scaffolds"
        for artifact in colorado_sources["source_sample_artifacts"]
    )


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


def test_colorado_production_hydrography_drafts_are_review_gated():
    colorado_dir = REAL_WORLD_DATA_DIR / "colorado_river_grand_canyon_rowing"
    source_manifest = json.loads((colorado_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((colorado_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    stationing = json.loads((colorado_dir / COLORADO_NHD_MAINSTEM_STATIONING_FILE).read_text())
    manifest = json.loads((colorado_dir / COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE).read_text())
    centerline = json.loads((colorado_dir / COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE).read_text())
    banks = json.loads((colorado_dir / COLORADO_PRODUCTION_BANKS_DRAFT_FILE).read_text())
    cross_sections = json.loads((colorado_dir / COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE).read_text())
    river_miles = json.loads((colorado_dir / COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE).read_text())
    sandbars = json.loads((colorado_dir / COLORADO_PRODUCTION_SANDBARS_FILE).read_text())
    expected_river_miles = build_colorado_river_mile_markers_geojson(stationing)
    expected_sandbars = build_colorado_sandbar_review_seeds_geojson(stationing)
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    photoreal_rivers = {river["river_id"]: river for river in photoreal_sources["rivers"]}

    assert COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_PRODUCTION_BANKS_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE in source_manifest["artifacts"]["hydrography"]
    assert COLORADO_PRODUCTION_SANDBARS_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "colorado_production_hydrography_drafts"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_river_mile_and_sandbar_review_seeds"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert river_miles == expected_river_miles
    assert sandbars == expected_sandbars
    assert manifest["schema"] == "raftsim.colorado_production_hydrography_drafts.manifest.v1"
    assert manifest["summary"]["centerline_vertex_count"] == 145
    assert manifest["summary"]["centerline_station_sample_count"] == 244
    assert manifest["summary"]["cross_section_count"] == 123
    assert manifest["summary"]["bank_offset_line_count"] == 2
    assert manifest["summary"]["length_m_preview"] == 24223.694
    assert manifest["summary"]["mainstem_orientation"] == "upstream_endpoint_to_downstream_endpoint_from_exact_graph_review"
    assert manifest["output_checksums"]["centerline"]["sha256"] == (
        "0a6ff25d816b1cb30a3e63fe7bf7697201c7c24c56241af038c0e354881d5d2c"
    )
    assert manifest["output_checksums"]["banks"]["sha256"] == (
        "d1f363e6cd9f176b171ac602f8604d1773cc00fd4454c046deed9b6e415d3e47"
    )
    assert manifest["output_checksums"]["cross_sections"]["sha256"] == (
        "d6483910027e158a320a8f3fc7de869417d733a3fd2c1cb594b6189b02528ee2"
    )
    assert centerline["properties"]["review_status"] == "draft_review_required_not_final_centerline_or_river_miles"
    assert centerline["features"][0]["properties"]["status"] == (
        "draft_from_nhd_mainstem_candidate_review_gated_not_final_centerline"
    )
    assert banks["properties"]["review_status"] == "offset_lines_review_required_not_banks_sandbars_or_wetted_width"
    assert len(banks["features"]) == 2
    assert cross_sections["properties"]["review_status"] == (
        "draft_review_lines_not_solver_cross_sections_or_sandbar_boundaries"
    )
    assert len(cross_sections["features"]) == 123
    assert river_miles["schema"] == "raftsim.colorado_river_mile_markers.geojson.v1"
    assert river_miles["status"] == "preview_river_mile_markers_from_nhd_stationing_not_official"
    assert len(river_miles["features"]) == 16
    assert river_miles["features"][0]["properties"]["preview_river_mile"] == 0
    assert sandbars["schema"] == "raftsim.colorado_sandbar_review_seeds.geojson.v1"
    assert sandbars["status"] == "release_sensitive_sandbar_review_seeds_not_authoritative"
    assert len(sandbars["features"]) == 6
    assert all(feature["geometry"]["type"] == "Polygon" for feature in sandbars["features"])
    assert (
        "physics/data/real_world/colorado_river_grand_canyon_rowing/"
        + COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE
        in rivers["colorado_river"]["attached_sources_by_class"]["hydrography_and_centerline"]["artifacts"]
    )
    assert (
        "physics/data/real_world/colorado_river_grand_canyon_rowing/" + COLORADO_PRODUCTION_SANDBARS_FILE
        in rivers["colorado_river"]["attached_sources_by_class"]["hydrography_and_centerline"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "colorado_river_mile_and_sandbar_review_seeds"
        for artifact in photoreal_rivers["colorado_river"]["source_sample_artifacts"]
    )
    assert all(
        feature["properties"]["status"] == "draft_production_import_cross_section_review_line_not_solver_section"
        for feature in cross_sections["features"]
    )


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
    assert PACUARE_SNIT_OGC_CATALOG_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_SNIT_CONFIG_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_SNIT_LAYER_LIST_SCRIPT_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in seeds["pacuare_official_source_access_plan"]["artifacts"]
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
    assert PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert PACUARE_CLOUD_SHADOW_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert (
        classes["hydrography_and_centerline"]["status"]
        == "preview_centerline_scaffold_attached_official_hydrography_pending"
    )
    assert PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["terrain_dem_or_lidar"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["aerial_or_satellite_imagery"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["water_and_vegetation_masks"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_RAINFALL_STATION_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_FLASH_RESPONSE_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["seasonal_flow_or_release_history"]["target_outputs"]
    assert PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_PRODUCTION_BANKS_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE in classes["hydrography_and_centerline"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert (
        PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE
        in classes["protected_area_and_access_context"]["target_outputs"]
    )
    assert PACUARE_ACCESS_CONSERVATION_POLICY_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["protected_area_and_access_context"]["target_outputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in classes["guide_and_reference_media_annotations"]["target_outputs"]
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
    assert catalogs["snit_ogc_services_catalog"]["archived_catalog_file"] == "snit_ogc_services_catalog.html"
    assert catalogs["snit_ogc_services_catalog"]["layer_catalog_summary"] == "snit_layer_catalog_summary.json"
    assert catalogs["snit_ogc_services_catalog"]["layer_metadata_summary"] == "snit_layer_metadata_summary.json"
    assert "snit_sinac" in catalogs["snit_ogc_services_catalog"]["reviewed_nodes"]
    assert "snit_senara_estaciones" in catalogs["snit_ogc_services_catalog"]["reviewed_nodes"]
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
    assert PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE in plan["downstream_manifest_targets"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in plan["downstream_manifest_targets"]


def test_pacuare_cloud_screened_scene_index_tracks_retained_nasa_candidates():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    scene_index = json.loads((pacuare_dir / PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE).read_text())
    cloud_review = json.loads((pacuare_dir / PACUARE_CLOUD_SHADOW_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_CLOUD_SHADOW_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "pacuare_cloud_screened_scene_index"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(artifact["artifact_id"] == "pacuare_cloud_shadow_review" for artifact in pull_manifest["pulled_artifacts"])
    assert scene_index["schema"] == "raftsim.pacuare.cloud_screened_scene_index.v1"
    assert scene_index["status"] == "modis_gibs_candidates_indexed_review_gated_not_production_imagery"
    assert scene_index["summary"]["candidate_count"] == 5
    assert scene_index["summary"]["active_preview_date"] == "2025-04-02"
    assert scene_index["summary"]["lowest_cloud_metric_date"] == "2025-03-08"
    assert scene_index["summary"]["active_preview_cloud_like_fraction"] == 0.0557
    assert scene_index["summary"]["active_preview_shadow_like_fraction"] == 0.3061
    assert scene_index["candidates"][-1]["date"] == "2025-04-02"
    assert scene_index["candidates"][-1]["active_preview_source"] is True
    assert cloud_review["schema"] == "raftsim.pacuare.cloud_shadow_review.v1"
    assert cloud_review["status"] == "review_gated_modis_cloud_shadow_diagnostic_not_acceptance"
    assert cloud_review["active_preview"]["date"] == "2025-04-02"
    assert any(
        blocker.startswith("MODIS/GIBS is too coarse for production photoreal materials")
        for blocker in cloud_review["promotion_blockers"]
    )
    assert (
        f"physics/data/real_world/pacuare_river_costa_rica/{PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE}"
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_cloud_screened_scene_index"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )


def test_pacuare_high_resolution_scene_metadata_review_tracks_official_candidates_without_downloads():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE).read_text())
    request_hashes = {request["request_id"]: request.get("sha256") for request in review["catalog_requests"]}
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "pacuare_high_resolution_scene_metadata_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["water_and_vegetation_masks"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_high_resolution_scene_metadata_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_high_resolution_scene_metadata_review.v1"
    assert review["status"] == "official_high_resolution_scene_metadata_attached_review_gated_no_imagery_downloaded"
    assert review["raw_response_policy"]["imagery_products_downloaded"] is False
    assert review["raw_response_policy"]["raw_catalog_payloads_committed"] is False
    assert request_hashes["usgs_landsatlook_c2l2_sr_2025_cloud_lt_20"] == (
        "4db5e9fc8323464e647b33b73f36bde383fbc14f77c032bcb9b611232728b14f"
    )
    assert request_hashes["copernicus_data_space_sentinel2_2025_expanded_page"] == (
        "459e6b580cad5db5f155959a74e081e7d860f10698aa757101627affcfe208c6"
    )
    assert review["landsat_metadata"]["cloud_filtered_scene_count"] == 3
    assert review["landsat_metadata"]["best_cloud_cover_percent"] == 12.05
    assert review["landsat_metadata"]["best_candidate_scene_id"] == "LC80140532025345LGN00"
    assert review["sentinel_metadata"]["expanded_page_count"] == 50
    assert review["sentinel_metadata"]["best_cloud_cover_percent"] == 1.39395
    assert (
        review["sentinel_metadata"]["best_l2a_candidate_name"]
        == "S2B_MSIL2A_20250119T160509_N0511_R054_T17PKM_20250119T211653.SAFE"
    )
    assert review["catalog_requests"][-1]["status"] == "timeout_no_payload_after_30s"
    assert "claiming complete yearly scene inventory" in review["review_decision"]["forbidden_use"]
    assert "Page through full-year Sentinel and Landsat catalogs" in review["remaining_blockers"][0]


def test_pacuare_landsat_product_access_gate_blocks_login_html_artifacts():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE).read_text())
    attempts = {attempt["request_id"]: attempt for attempt in review["attempted_asset_requests"]}
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "pacuare_landsat_product_access_gate_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_landsat_product_access_gate_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_landsat_product_access_gate_review.v1"
    assert review["status"] == "direct_landsatlook_asset_requests_return_eros_login_html_no_imagery_downloaded"
    assert review["response_policy"]["do_not_commit_login_html_as_imagery_or_metadata"] is True
    assert review["response_policy"]["bad_download_removed_from_workspace"] is True
    assert review["response_policy"]["imagery_products_downloaded"] is False
    assert attempts["landsat_lc80140532025345_reduced_resolution_browse"]["content_type"] == (
        "text/html; charset=UTF-8"
    )
    assert attempts["landsat_lc80140532025345_reduced_resolution_browse"]["sha256"] == (
        "92af5afe0b66bd6a5c34b452eaac1d871c6d18e28bfcd4e81876e185739edb3b"
    )
    assert attempts["landsat_lc80140532025345_mtl_json"]["response_class"] == "eros_registration_login_html"
    assert attempts["landsat_lc80140532025345_mtl_json"]["artifact_committed"] is False
    assert "claiming Landsat browse imagery is attached" in review["forbidden_use"]


def test_pacuare_sentinel_cog_thumbnail_review_attaches_public_visual_triage_only():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE).read_text())
    tiles = {tile["tile_id"]: tile for tile in review["attached_thumbnails"]}
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert (
        "imagery/production_import_pilot/sentinel_s2b_17pkm_20250119_thumbnail.jpg"
        in source_manifest["artifacts"]["imagery"]
    )
    assert (
        "imagery/production_import_pilot/sentinel_s2b_16phr_20250119_tileinfo_metadata.json"
        in source_manifest["artifacts"]["imagery"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_cog_thumbnail_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["water_and_vegetation_masks"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_cog_thumbnail_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_cog_thumbnail_review.v1"
    assert review["status"] == "public_sentinel_cog_thumbnail_and_tile_metadata_attached_review_gated_not_source_drape"
    assert len(review["attached_thumbnails"]) == 2
    assert tiles["17PKM"]["thumbnail_sha256"] == (
        "c40c6892a088da25ed31cad93fa47a0b9bed636b211b50636e7bf3505a480d2f"
    )
    assert tiles["16PHR"]["thumbnail_sha256"] == (
        "36e68d81e6a6f8c8036d8e0f9fb304693b8916cb88f7c09ffa018dec54232b29"
    )
    assert tiles["17PKM"]["catalog_cloud_cover_percent"] == 4.785432
    assert tiles["16PHR"]["catalog_cloud_cover_percent"] == 14.778528
    assert tiles["17PKM"]["epsg"] == 32617
    assert tiles["16PHR"]["epsg"] == 32616
    assert "production source-drape replacement" in review["forbidden_use"]
    assert "windowed COG reads clipped to the Pacuare corridor" in review["remaining_blockers"][1]


def test_pacuare_sentinel_cog_access_probe_verifies_range_reads_without_promoting_imagery():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")
    probes = {probe["probe_id"]: probe for probe in review["range_probe_results"]}

    assert PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_cog_access_probe"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["water_and_vegetation_masks"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_cog_access_probe"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_cog_access_probe.v1"
    assert review["status"] == "public_sentinel_cog_range_access_verified_extraction_not_promoted"
    assert review["probe_policy"]["full_resolution_bands_committed"] is False
    assert review["probe_policy"]["review_tci_png_committed"] is True
    assert review["probe_policy"]["production_band_derivatives_committed"] is False
    assert review["probe_policy"]["source_drape_replaced"] is False
    assert review["readiness_summary"]["successful_range_probe_count"] == 4
    assert review["readiness_summary"]["total_full_resolution_bytes_advertised_for_probed_assets"] == 679418869
    assert review["readiness_summary"]["scl_probe_available"] is True
    assert review["readiness_summary"]["current_tooling_gap"].startswith("The local validation environment")
    assert probes["sentinel_17pkm_b04_header_range"]["range_http_status"] == 206
    assert probes["sentinel_16phr_scl_header_range"]["content_length_bytes"] == 2213150
    assert "production source-drape replacement" in review["probe_policy"]["forbidden_use"]


def test_pacuare_sentinel_tci_review_preview_is_review_only_not_source_drape():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert (pacuare_dir / PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE).is_file()
    assert (pacuare_dir / PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE).is_file()
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_tci_review_preview"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_tci_16phr_review_preview"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_tci_review_preview"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_tci_16phr_review_preview"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_tci_review_preview.v1"
    assert review["status"] == "sentinel_tci_downsampled_review_preview_attached_not_source_drape"
    assert review["source_asset"]["download_committed"] is False
    assert review["output"]["dimensions_px"] == [1024, 1024]
    assert review["output"]["sha256"] == "69ed0b1e5a54c39108e459b3e06b6f20f1023f8d079b570026424473ad7599ba"
    assert "not a Pacuare corridor clip" in review["coverage_and_limitations"]["limitations"][0]
    assert "production source-drape replacement" in review["forbidden_use"]

    companion_review = json.loads((pacuare_dir / PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE).read_text())
    assert companion_review["schema"] == "raftsim.pacuare_sentinel_tci_review_preview.v1"
    assert companion_review["status"] == "sentinel_tci_downsampled_review_preview_attached_not_source_drape"
    assert companion_review["source_asset"]["tile_id"] == "16PHR"
    assert companion_review["source_asset"]["download_committed"] is False
    assert companion_review["output"]["dimensions_px"] == [1024, 1024]
    assert companion_review["output"]["sha256"] == "facdc17c72df5f300af13f02c8ef262cbcd3bb6127cd2c94aa011ac2704cd937"
    assert "full 16PHR tile downsample" in companion_review["coverage_and_limitations"]["limitations"][0]
    assert "claiming Pacuare corridor imagery coverage" in companion_review["forbidden_use"]


def test_pacuare_sentinel_corridor_tile_coverage_review_gates_windowed_reads():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_tile_coverage_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_tile_coverage_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_corridor_tile_coverage_review.v1"
    assert review["status"] == "sentinel_tile_bbox_coverage_review_attached_windowed_reads_blocked"
    assert {tile["tile_id"] for tile in review["tile_intersections"]} == {"17PKM", "16PHR"}
    assert all(tile["intersects_planning_bounds"] for tile in review["tile_intersections"])
    assert review["coverage_summary"]["approximate_corridor_fraction_covered_by_tile_bboxes"] > 0.99
    assert review["coverage_summary"]["missing_area_requires_exact_crs_review"] is True
    assert review["windowed_read_decision"]["exact_corridor_clips_generated"] is False
    assert "claiming complete Pacuare corridor imagery coverage" in review["forbidden_use"]


def test_pacuare_sentinel_corridor_bbox_clip_review_is_windowed_but_not_promoted():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert (pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE).is_file()
    assert (pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE).is_file()
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_bbox_clip_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_bbox_clip_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_corridor_bbox_clip_review.v1"
    assert review["status"] == "sentinel_corridor_bbox_window_clips_attached_review_only"
    assert review["clip_scope"] == "draft_planning_bounds_bbox_not_route_polygon"
    assert review["windowed_read_decision"]["corridor_bbox_clip_previews_generated"] is True
    assert review["windowed_read_decision"]["source_drape_replaced"] is False
    assert review["windowed_read_decision"]["scl_cloud_mask_applied"] is False

    outputs = {output["tile_id"]: output for output in review["outputs"]}
    assert outputs["17PKM"]["pixel_window"] == {"left": 0, "top": 8004, "width": 3483, "height": 2976}
    assert outputs["17PKM"]["dimensions_px"] == [1024, 875]
    assert outputs["17PKM"]["sha256"] == "02e8950c329826c13db4665eba6572721e075411d01127475440622900d1f587"
    assert outputs["16PHR"]["pixel_window"] == {"left": 5625, "top": 0, "width": 3670, "height": 2388}
    assert outputs["16PHR"]["dimensions_px"] == [1024, 666]
    assert outputs["16PHR"]["sha256"] == "1070bcf391340b10189b418c7899626833307600670020a25514b46fec366ca3"
    assert "production source-drape replacement" in review["forbidden_use"]


def test_pacuare_sentinel_corridor_bbox_scl_qa_review_blocks_cloudy_clip_promotion():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE in source_manifest["artifacts"]["imagery"]
    assert (pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE).is_file()
    assert (pacuare_dir / PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE).is_file()
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_bbox_scl_qa_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_sentinel_corridor_bbox_scl_qa_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_sentinel_corridor_bbox_scl_qa_review.v1"
    assert review["status"] == "sentinel_corridor_bbox_scl_qa_attached_promotion_blocked_by_clouds"
    assert review["windowed_read_decision"]["scl_qa_preview_generated"] is True
    assert review["windowed_read_decision"]["scl_mask_applied_to_source_drape"] is False
    assert review["windowed_read_decision"]["cloud_screening_blocks_promotion"] is True

    outputs = {output["tile_id"]: output for output in review["outputs"]}
    assert outputs["17PKM"]["dimensions_px"] == [1024, 875]
    assert outputs["17PKM"]["sha256"] == "ba86ba7527bfc9d5720266125d34e58a57d9366554426ab6de9e77b3567440e1"
    assert outputs["17PKM"]["class_summary"]["cloud_or_cirrus_fraction"] == 0.243554
    assert outputs["17PKM"]["class_summary"]["cloud_shadow_fraction"] == 0.012988
    assert outputs["16PHR"]["dimensions_px"] == [1024, 666]
    assert outputs["16PHR"]["sha256"] == "13e14fb34470d03ffb6afa4ddbbd2eec69bcacc9912f23d93ffcc0e22ab194f7"
    assert outputs["16PHR"]["class_summary"]["cloud_or_cirrus_fraction"] == 0.110896
    assert outputs["16PHR"]["class_summary"]["cloud_shadow_fraction"] == 0.014826
    assert "production source-drape replacement" in review["forbidden_use"]


def test_pacuare_source_metadata_review_consolidates_metadata_without_promoting():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    review = json.loads((pacuare_dir / PACUARE_SOURCE_METADATA_REVIEW_FILE).read_text())
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")
    reviewed_files = {item["path"]: item for item in review["reviewed_local_artifacts"]}
    source_classes = review["review_status_by_source_class"]

    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in source_manifest["artifacts"]["source_pulls"]
    assert any(
        artifact["artifact_id"] == "pacuare_source_metadata_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SOURCE_METADATA_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["terrain_dem_or_lidar"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_SOURCE_METADATA_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["aerial_or_satellite_imagery"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_source_metadata_review"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_source_metadata_review.v1"
    assert review["status"] == "metadata_consolidated_review_gated_not_production_promoted"
    assert review["raw_response_policy"]["raw_third_party_payloads_committed"] is False
    assert review["pilot_bounds_wgs84"]["min_lon"] == -83.75
    assert review["terrain_dem_metadata"]["heightfield_candidates"]["production_import_size_px"] == 2017
    assert review["terrain_dem_metadata"]["heightfield_candidates"]["elevation_min_m"] == 16.12291
    assert review["terrain_dem_metadata"]["heightfield_candidates"]["elevation_max_m"] == 3230.44604
    assert review["imagery_metadata"]["cloud_screened_candidates"]["candidate_count"] == 5
    assert review["imagery_metadata"]["cloud_screened_candidates"]["active_preview_date"] == "2025-04-02"
    assert review["imagery_metadata"]["cloud_shadow_review"]["active_preview_shadow_like_fraction"] == 0.3061
    assert review["official_costa_rica_metadata"]["snit_selected_candidate_layer_count"] == 17
    assert review["official_costa_rica_metadata"]["snit_selected_metadata_layer_count"] == 11
    assert review["official_costa_rica_metadata"]["direccion_de_agua_advertised_named_layer_count"] == 52
    assert review["hydrology_metadata"]["rainfall_candidate_layer_count"] == 6
    assert review["hydrology_metadata"]["discharge_stage_candidate_count"] == 3
    assert review["reference_media_metadata"]["promoted_item_count"] == 0
    assert review["reference_media_metadata"]["rights_cleared_for_asset_use"] == 0
    assert "production photoreal Pacuare terrain, water, or rainforest material approval" in review["forbidden_use"]
    assert "terrain_dem_or_lidar" in source_classes
    assert source_classes["seasonal_flow_or_release_history"].endswith("numeric_flow_blocked")
    assert reviewed_files["imagery/production_import_pilot/cloud_screened_scene_index.json"]["sha256"] == (
        hashlib.sha256((pacuare_dir / PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE).read_bytes()).hexdigest()
    )


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


def test_pacuare_snit_layer_catalog_is_archived_as_metadata_only():
    base = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    summary_path = base / PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE
    summary = json.loads(summary_path.read_text())
    catalog_path = base / PACUARE_SNIT_OGC_CATALOG_FILE
    config_path = base / PACUARE_SNIT_CONFIG_FILE
    layer_list_script_path = base / PACUARE_SNIT_LAYER_LIST_SCRIPT_FILE
    node_archives = {entry["node_id"]: entry for entry in summary["node_layer_archives"]}
    selected_names = {layer["name"] for layer in summary["selected_candidate_layers"]}

    assert catalog_path.is_file()
    assert config_path.is_file()
    assert layer_list_script_path.is_file()
    assert summary["schema"] == "raftsim.pacuare.snit_layer_catalog_summary.v1"
    assert summary["status"] == "snit_catalog_and_node_layer_lists_archived_metadata_only_no_features_downloaded"
    assert summary["policy"]["feature_downloads_performed"] is False
    assert summary["policy"]["layer_geometry_imported"] is False
    assert summary["archived_catalog"]["raw_sha256"] == hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    assert summary["endpoint_contract_evidence"]["config_script"]["raw_sha256"] == hashlib.sha256(
        config_path.read_bytes()
    ).hexdigest()
    assert summary["endpoint_contract_evidence"]["layer_list_script"]["raw_sha256"] == hashlib.sha256(
        layer_list_script_path.read_bytes()
    ).hexdigest()
    assert node_archives["snit_direccion_de_agua"]["layer_count"] == 37
    assert node_archives["snit_imn"]["layer_count"] == 39
    assert node_archives["snit_sinac"]["layer_count"] == 7
    assert node_archives["snit_senara_estaciones"]["layer_count"] == 2
    assert "DA_AFOROS" in selected_names
    assert "DA_UNIDADES HIDROLOGICAS" in selected_names
    assert "Precipitación Anual: período 1960-2013" in selected_names
    assert "Estaciones Pluviométricas" in selected_names
    assert "Áreas Silvestres Protegidas" in selected_names
    assert "Cobertura Forestal 2023" in selected_names
    assert all(layer["feature_download_status"] == "not_downloaded_metadata_only" for layer in summary["selected_candidate_layers"])


def test_pacuare_snit_layer_metadata_records_terms_and_crs_without_importing_features():
    base = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    summary = json.loads((base / PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE).read_text())
    layers = summary["metadata_layers"]
    titles = {layer["metadata_title"] for layer in layers if layer["metadata_title"]}
    terms_statuses = {layer["terms_status"] for layer in layers}
    crs_values = {layer["crs"] for layer in layers if layer["crs"]}

    assert summary["schema"] == "raftsim.pacuare.snit_layer_metadata_summary.v1"
    assert summary["status"] == "selected_snit_layer_metadata_archived_no_features_downloaded"
    assert summary["selected_metadata_layer_count"] == 11
    assert summary["policy"]["feature_downloads_performed"] is False
    assert summary["policy"]["map_tiles_imported"] is False
    assert summary["policy"]["station_time_series_imported"] is False
    assert summary["policy"]["layer_geometry_imported"] is False
    assert summary["policy"]["metadata_json_only"] is True
    assert "Áreas Silvestres Protegidas de Costa Rica a escala 1:5000 (Capa Oficial)" in titles
    assert "Mapa de Cobertura Forestal 2023 escala 1: 5000" in titles
    assert "Estaciones Pluviométricas, 2023" in titles
    assert "unrestricted_metadata_claim_review_required" in terms_statuses
    assert "copyright_or_ip_restrictions_recorded_import_blocked_until_terms_review" in terms_statuses
    assert any("5367" in crs for crs in crs_values)
    assert any("8908" in crs for crs in crs_values)
    assert all(layer["feature_download_status"] == "not_downloaded_metadata_only" for layer in layers)
    assert all(layer["promotion_gate"].startswith("Do not import layer geometry") for layer in layers)
    assert any("Distribution entries are WMS/service metadata only" in item for item in summary["review_findings"])

    for layer in layers:
        metadata_path = base / "hydrography/production_import_pilot" / layer["metadata_file"]
        assert metadata_path.is_file()
        assert layer["raw_sha256"] == hashlib.sha256(metadata_path.read_bytes()).hexdigest()


def test_pacuare_rainfall_station_review_summarizes_metadata_without_flow_promotion():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    rainfall_context = json.loads((pacuare_dir / "hydrology/rainfall_context.json").read_text())
    gauge_search = json.loads((pacuare_dir / "hydrology/costa_rica_gauge_search.json").read_text())
    catalog_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE).read_text())
    metadata_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE).read_text())
    review = json.loads((pacuare_dir / PACUARE_RAINFALL_STATION_REVIEW_FILE).read_text())
    builder_review = build_pacuare_rainfall_station_review(
        rainfall_context,
        gauge_search,
        catalog_summary,
        metadata_summary,
    )
    rivers = {river["river_id"]: river for river in readiness["rivers"]}

    assert review == builder_review
    assert PACUARE_RAINFALL_STATION_REVIEW_FILE in source_manifest["artifacts"]["gauges_and_rainfall"]
    assert any(
        artifact["artifact_id"] == "pacuare_rainfall_station_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_rainfall_station_review.v1"
    assert review["status"] == "metadata_only_rainfall_station_candidates_attached_numeric_flow_blocked"
    assert review["candidate_layer_summary"]["candidate_layer_count"] == 6
    assert review["candidate_layer_summary"]["imn_precipitation_layers"] == 3
    assert review["candidate_layer_summary"]["senara_station_layers"] == 2
    assert review["candidate_layer_summary"]["wfs_available_count"] == 5
    assert all(layer["feature_download_status"] == "not_downloaded_metadata_only" for layer in review["candidate_layers"])
    assert "numeric Pacuare flow-band promotion" in review["forbidden_use"]
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_RAINFALL_STATION_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["seasonal_flow_or_release_history"]["artifacts"]
    )


def test_pacuare_discharge_stage_station_review_summarizes_metadata_without_flow_promotion():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    gauge_search = json.loads((pacuare_dir / "hydrology/costa_rica_gauge_search.json").read_text())
    da_summary = json.loads((pacuare_dir / PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE).read_text())
    catalog_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE).read_text())
    review = json.loads((pacuare_dir / PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE).read_text())
    builder_review = build_pacuare_discharge_stage_station_review(
        gauge_search,
        da_summary,
        catalog_summary,
    )
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    da_names = {layer["name"] for layer in review["da_sinigirh_candidates"]}

    assert review == builder_review
    assert PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE in source_manifest["artifacts"]["gauges_and_rainfall"]
    assert any(
        artifact["artifact_id"] == "pacuare_discharge_stage_station_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_discharge_stage_station_review.v1"
    assert review["status"] == "metadata_only_discharge_stage_candidates_attached_numeric_flow_blocked"
    assert {"Aguas:DA_AFOROS", "Aguas:JASEC_ESTACIONES_HIDROMETRICAS"}.issubset(da_names)
    assert review["candidate_summary"]["da_sinigirh_candidate_count"] == 3
    assert review["candidate_summary"]["snit_direccion_de_agua_candidate_count"] == 2
    assert review["candidate_summary"]["wfs_feature_access_advertised_count"] == 0
    assert "numeric Pacuare flow-band promotion" in review["forbidden_use"]
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["seasonal_flow_or_release_history"]["artifacts"]
    )


def test_pacuare_flash_response_review_links_hydrology_metadata_without_model_promotion():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    rainfall_context = json.loads((pacuare_dir / "hydrology/rainfall_context.json").read_text())
    rainfall_review = json.loads((pacuare_dir / PACUARE_RAINFALL_STATION_REVIEW_FILE).read_text())
    discharge_review = json.loads((pacuare_dir / PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE).read_text())
    da_summary = json.loads((pacuare_dir / PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE).read_text())
    catalog_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE).read_text())
    review = json.loads((pacuare_dir / PACUARE_FLASH_RESPONSE_REVIEW_FILE).read_text())
    builder_review = build_pacuare_flash_response_review(
        rainfall_context,
        rainfall_review,
        discharge_review,
        da_summary,
        catalog_summary,
    )
    rivers = {river["river_id"]: river for river in readiness["rivers"]}

    assert review == builder_review
    assert PACUARE_FLASH_RESPONSE_REVIEW_FILE in source_manifest["artifacts"]["gauges_and_rainfall"]
    assert any(
        artifact["artifact_id"] == "pacuare_flash_response_review"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert review["schema"] == "raftsim.pacuare_flash_response_review.v1"
    assert review["status"] == "metadata_only_flash_response_context_attached_model_blocked"
    assert review["policy"]["lag_model_built"] is False
    assert review["flash_flow_band_question"]["flow_band"] == "flash_response_review_only"
    assert review["rainfall_review_summary"]["candidate_layer_count"] == 6
    assert review["discharge_stage_review_summary"]["da_sinigirh_candidate_count"] == 3
    assert len(review["basin_and_recharge_context_candidates"]["da_sinigirh_candidates"]) == 2
    assert len(review["basin_and_recharge_context_candidates"]["snit_context_layers"]) == 2
    assert "numeric flash-response tuning" in review["forbidden_use"]
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_FLASH_RESPONSE_REVIEW_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["seasonal_flow_or_release_history"]["artifacts"]
    )


def test_pacuare_protected_area_policy_artifacts_are_review_gated():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    access_constraints = json.loads((pacuare_dir / "review/access_and_conservation_constraints.json").read_text())
    sinac_source_rights = json.loads((pacuare_dir / "review/sinac_protected_area_source_rights.json").read_text())
    catalog_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_CATALOG_SUMMARY_FILE).read_text())
    metadata_summary = json.loads((pacuare_dir / PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE).read_text())
    sensitivity = json.loads((pacuare_dir / PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE).read_text())
    policy = json.loads((pacuare_dir / PACUARE_ACCESS_CONSERVATION_POLICY_FILE).read_text())
    builder_sensitivity = build_pacuare_protected_area_publication_sensitivity(
        access_constraints,
        sinac_source_rights,
        catalog_summary,
        metadata_summary,
    )
    builder_policy = build_pacuare_access_conservation_policy(
        access_constraints,
        sinac_source_rights,
        catalog_summary,
        metadata_summary,
    )
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert sensitivity == builder_sensitivity
    assert policy == builder_policy
    assert (
        PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE
        in source_manifest["artifacts"]["access_and_protected_context"]
    )
    assert PACUARE_ACCESS_CONSERVATION_POLICY_FILE in source_manifest["artifacts"]["access_and_protected_context"]
    assert any(
        artifact["artifact_id"] == "pacuare_protected_area_publication_sensitivity"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_access_conservation_policy"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert sensitivity["schema"] == "raftsim.pacuare_protected_area_publication_sensitivity.v1"
    assert sensitivity["status"] == "metadata_only_protected_area_publication_policy_attached_review_gated"
    assert sensitivity["policy"]["protected_area_geometry_imported"] is False
    assert sensitivity["protected_context_summary"]["candidate_layer_count"] == 8
    assert sensitivity["protected_context_summary"]["metadata_layer_count"] == 8
    assert "route publication authority" in sensitivity["forbidden_use"]
    assert "protected-area clearance" in sensitivity["forbidden_use"]
    assert "review/production_import_pilot/no_publish_sensitive_polygons.geojson" in sensitivity[
        "required_editor_annotations"
    ]
    assert policy["schema"] == "raftsim.pacuare_access_and_conservation_policy.v1"
    assert policy["status"] == "access_conservation_policy_attached_no_geometry_review_gated"
    assert policy["policy"]["flow_dependent_access_review_required"] is True
    assert policy["candidate_layer_summary"]["metadata_layer_count"] == 8
    assert "final access geometry" in policy["forbidden_use"]
    assert "review/production_import_pilot/access_points.geojson" in policy["required_editor_annotations"]
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/"
        + PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert (
        "physics/data/real_world/pacuare_river_costa_rica/" + PACUARE_ACCESS_CONSERVATION_POLICY_FILE
        in rivers["pacuare"]["attached_sources_by_class"]["protected_area_and_access_context"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_protected_area_publication_sensitivity"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_access_conservation_policy"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )


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


def test_pacuare_production_hydrography_review_drafts_are_from_preview_scaffold():
    pacuare_dir = REAL_WORLD_DATA_DIR / "pacuare_river_costa_rica"
    source_manifest = json.loads((pacuare_dir / "source_manifest.json").read_text())
    pull_manifest = json.loads((pacuare_dir / "production_source_pull_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    preview_centerline = json.loads((pacuare_dir / PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE).read_text())
    stationing = json.loads((pacuare_dir / PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE).read_text())
    centerline = json.loads((pacuare_dir / PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE).read_text())
    banks = json.loads((pacuare_dir / PACUARE_PRODUCTION_BANKS_DRAFT_FILE).read_text())
    rapid_access = json.loads((pacuare_dir / PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE).read_text())
    expected_centerline = build_pacuare_production_centerline_draft_geojson(preview_centerline)
    expected_banks = build_pacuare_production_banks_draft_geojson(stationing)
    expected_rapid_access = build_pacuare_rapid_access_stationing_draft_geojson(stationing)
    rivers = {river["river_id"]: river for river in readiness["rivers"]}
    pacuare_sources = next(river for river in photoreal_sources["rivers"] if river["river_id"] == "pacuare")

    assert centerline == expected_centerline
    assert banks == expected_banks
    assert rapid_access == expected_rapid_access
    assert PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert PACUARE_PRODUCTION_BANKS_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE in source_manifest["artifacts"]["hydrography"]
    assert any(
        artifact["artifact_id"] == "pacuare_production_hydrography_review_drafts"
        for artifact in pull_manifest["pulled_artifacts"]
    )
    assert centerline["schema"] == "raftsim.pacuare_production_centerline_draft.geojson.v1"
    assert centerline["status"] == "draft_from_preview_scaffold_review_required_not_official_hydrography"
    assert len(centerline["features"][0]["geometry"]["coordinates"]) == 129
    assert banks["schema"] == "raftsim.pacuare_production_banks_draft.geojson.v1"
    assert banks["status"] == "draft_bank_offsets_from_preview_stationing_review_required"
    assert len(banks["features"]) == 2
    assert rapid_access["schema"] == "raftsim.pacuare_rapid_access_stationing_draft.geojson.v1"
    assert rapid_access["status"] == "preview_rapid_access_stationing_review_seeds_not_authoritative"
    assert len(rapid_access["features"]) == 6
    assert all(feature["geometry"]["type"] == "Point" for feature in rapid_access["features"])
    assert (
        f"physics/data/real_world/pacuare_river_costa_rica/{PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE}"
        in rivers["pacuare"]["attached_sources_by_class"]["hydrography_and_centerline"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/pacuare_river_costa_rica/{PACUARE_PRODUCTION_BANKS_DRAFT_FILE}"
        in rivers["pacuare"]["attached_sources_by_class"]["hydrography_and_centerline"]["artifacts"]
    )
    assert (
        f"physics/data/real_world/pacuare_river_costa_rica/{PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE}"
        in rivers["pacuare"]["attached_sources_by_class"]["hydrography_and_centerline"]["artifacts"]
    )
    assert any(
        artifact["artifact_id"] == "pacuare_production_hydrography_review_drafts"
        for artifact in pacuare_sources["source_sample_artifacts"]
    )


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
    assert (
        register["canonical_inputs"]["first_party_procedural_environment_assets"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json"
    )
    assert any(target["target"] == "water_foam_spray_mist_and_wetness" for target in register["global_visual_replacement_targets"])

    south_fork_p0 = {item["source_class"] for item in rivers["american_south_fork"]["p0_next_pulls_or_attachments"]}
    colorado_p0 = {item["source_class"] for item in rivers["colorado_river"]["p0_next_pulls_or_attachments"]}
    pacuare_p0 = {item["source_class"] for item in rivers["pacuare"]["p0_next_pulls_or_attachments"]}

    assert {
        "hydrography_and_centerline",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    }.issubset(south_fork_p0)
    assert {
        "hydrography_and_centerline",
        "seasonal_flow_or_release_history",
        "protected_area_and_access_context",
        "guide_and_reference_media_annotations",
    }.issubset(colorado_p0)
    assert {
        "hydrography_and_centerline",
        "aerial_or_satellite_imagery",
        "seasonal_flow_or_release_history",
        "guide_and_reference_media_annotations",
    }.issubset(pacuare_p0)
    assert SOUTH_FORK_PRODUCTION_SOURCE_GATE_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_SOURCE_METADATA_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
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
    assert SOUTH_FORK_CDEC_SEASONAL_WINDOW_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_CDEC_MULTIYEAR_FLOW_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
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
    assert SOUTH_FORK_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_PRODUCTION_CENTERLINE_DRAFT_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_PRODUCTION_BANKS_DRAFT_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_FLOW_BAND_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_ACCESS_PUBLICATION_REVIEW_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_ACCESS_POINTS_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert SOUTH_FORK_EVACUATION_RESCUE_ROUTES_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_ANNOTATIONS_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE in rivers["american_south_fork"]["attached_preview_inputs"]
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
    assert COLORADO_SOURCE_METADATA_REVIEW_FILE in rivers["colorado_river"]["attached_preview_inputs"]
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
    assert COLORADO_PRODUCTION_HYDROGRAPHY_DRAFT_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_PRODUCTION_CENTERLINE_DRAFT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_PRODUCTION_BANKS_DRAFT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_PRODUCTION_CROSS_SECTIONS_DRAFT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_PRODUCTION_RIVER_MILE_MARKERS_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_PRODUCTION_SANDBARS_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_USBR_TOTAL_RELEASE_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_USBR_RELEASE_CONTEXT_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_RELEASE_BAND_REVIEW_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_ACCESS_PUBLICATION_REVIEW_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_ACCESS_POINTS_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_NO_PUBLISH_SENSITIVE_POLYGONS_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_CAMPS_AND_BEACHES_REVIEW_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert COLORADO_OARSMAN_ROUTE_PUBLICATION_NOTES_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_ANNOTATIONS_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE in rivers["colorado_river"]["attached_preview_inputs"]
    assert PACUARE_OFFICIAL_SOURCE_ACCESS_PLAN_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_DA_SINIGIRH_WMS_CAPABILITIES_SUMMARY_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SNIT_LAYER_METADATA_SUMMARY_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SOURCE_METADATA_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_MANIFEST_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_CENTERLINE_SCAFFOLD_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PRODUCTION_CENTERLINE_DRAFT_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PRODUCTION_BANKS_DRAFT_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_RAPID_ACCESS_STATIONING_DRAFT_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_CLOUD_SCREENED_SCENE_INDEX_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_CLOUD_SHADOW_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_HIGH_RES_SCENE_METADATA_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_LANDSAT_PRODUCT_ACCESS_GATE_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_COG_THUMBNAIL_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_COG_ACCESS_PROBE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_TCI_REVIEW_PREVIEW_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_TCI_16PHR_REVIEW_PREVIEW_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_TILE_COVERAGE_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_17PKM_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_CLIP_16PHR_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_17PKM_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_SENTINEL_CORRIDOR_BBOX_SCL_QA_16PHR_IMAGE_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_RAINFALL_STATION_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_DISCHARGE_STAGE_STATION_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_FLASH_RESPONSE_REVIEW_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_PROTECTED_AREA_PUBLICATION_SENSITIVITY_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert PACUARE_ACCESS_CONSERVATION_POLICY_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_ANNOTATIONS_FILE in rivers["pacuare"]["attached_preview_inputs"]
    assert REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE in rivers["pacuare"]["attached_preview_inputs"]
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


def test_reference_media_annotations_and_rights_manifests_are_link_only_per_river():
    queue = json.loads((REAL_WORLD_DATA_DIR / "reference_media_review_queue.json").read_text())
    link_manifest = json.loads((REAL_WORLD_DATA_DIR / "reference_media_link_manifest.json").read_text())
    readiness = json.loads((REAL_WORLD_DATA_DIR / "production_geospatial_source_readiness.json").read_text())
    photoreal_sources = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
        ).read_text()
    )
    river_dirs = {
        "american_south_fork": "south_fork_american_chili_bar",
        "colorado_river": "colorado_river_grand_canyon_rowing",
        "pacuare": "pacuare_river_costa_rica",
    }
    stationing_files = {
        "american_south_fork": SOUTH_FORK_NHD_MAINSTEM_STATIONING_FILE,
        "colorado_river": COLORADO_NHD_MAINSTEM_STATIONING_FILE,
        "pacuare": PACUARE_PREVIEW_STATIONING_SCAFFOLD_FILE,
    }
    readiness_by_river = {river["river_id"]: river for river in readiness["rivers"]}
    photoreal_by_river = {river["river_id"]: river for river in photoreal_sources["rivers"]}

    for river_id, river_dir in river_dirs.items():
        data_dir = REAL_WORLD_DATA_DIR / river_dir
        source_manifest = json.loads((data_dir / "source_manifest.json").read_text())
        annotations = json.loads((data_dir / REFERENCE_MEDIA_ANNOTATIONS_FILE).read_text())
        rights = json.loads((data_dir / REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE).read_text())
        stationing = json.loads((data_dir / stationing_files[river_id]).read_text())
        expected_annotations = build_reference_media_annotations_geojson(
            river_id,
            queue,
            stationing,
            stationing_files[river_id],
        )
        expected_rights = build_reference_media_rights_manifest(river_id, link_manifest, queue)

        assert annotations == expected_annotations
        assert rights == expected_rights
        assert annotations["type"] == "FeatureCollection"
        assert annotations["status"] == "link_only_annotation_targets_with_review_seed_geometry_no_media_downloaded"
        assert len(annotations["features"]) == 3
        assert all(feature["geometry"]["type"] == "Point" for feature in annotations["features"])
        assert all(
            feature["properties"]["review_status"] == "candidate_links_only_no_media_downloaded"
            for feature in annotations["features"]
        )
        assert all(
            feature["properties"]["stationing_status"]
            == "review_seed_from_existing_stationing_scaffold_not_authoritative"
            for feature in annotations["features"]
        )
        assert rights["status"] == "candidate_links_only_no_media_downloaded_no_rights_cleared"
        assert rights["rights_summary"]["media_files_downloaded"] == 0
        assert rights["rights_summary"]["promoted_item_count"] == 0
        assert rights["promoted_items"] == []
        assert "using public social media as source textures or training data" in rights["forbidden_use"]
        assert REFERENCE_MEDIA_ANNOTATIONS_FILE in source_manifest["artifacts"]["guide_references"]
        assert REFERENCE_MEDIA_RIGHTS_MANIFEST_FILE in source_manifest["artifacts"]["field_media"]
        assert (
            f"physics/data/real_world/{river_dir}/{REFERENCE_MEDIA_ANNOTATIONS_FILE}"
            in readiness_by_river[river_id]["attached_sources_by_class"]["guide_and_reference_media_annotations"][
                "artifacts"
            ]
        )
        assert any(
            artifact["artifact_id"] == f"{river_id}_reference_media_annotations"
            for artifact in photoreal_by_river[river_id]["source_sample_artifacts"]
        )


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
