from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from raftsim.international_production_corridor import (
    FUTALEUFU,
    ZAMBEZI,
    _condition_visual_channel,
    _write_route_artifacts,
    extract_route,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ZAMBEZI_TERRAIN_ACQUISITION_LEAD_PATH = (
    REPO_ROOT
    / "physics/data/real_world/zambezi_batoka_gorge/terrain/source/"
    "batoka_high_resolution_terrain_acquisition_leads.json"
)
ZAMBEZI_CORRIDOR_MANIFEST_PATH = (
    REPO_ROOT
    / "physics/data/real_world/zambezi_batoka_gorge/production_corridor/"
    "boiling_pot_to_mukuni_beach/manifest.json"
)
ZAMBEZI_TERRAIN_ACQUISITION_REQUEST_PATH = (
    REPO_ROOT / "docs/batoka-high-resolution-terrain-acquisition-request.md"
)
PHOTOREAL_SOURCE_PLAN_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
)


def _way(way_id: int, points: list[tuple[float, float]]) -> dict[str, object]:
    return {
        "type": "way",
        "id": way_id,
        "geometry": [{"lon": lon, "lat": lat} for lon, lat in points],
    }


def test_extract_route_orients_segments_and_clips_at_station() -> None:
    definition = replace(
        ZAMBEZI,
        way_ids=(1, 2),
        start_seed_lon_lat=(0.0, 0.0),
        end_station_m=1500.0,
    )
    payload = {
        "elements": [
            _way(1, [(0.01, 0.0), (0.0, 0.0)]),
            _way(2, [(0.01, 0.0), (0.02, 0.0)]),
        ]
    }
    route = extract_route(payload, definition)
    assert route[0] == (0.0, 0.0)
    assert route[-1][0] == pytest.approx(1500.0 / 111_194.9266, rel=1e-4)


def test_extract_route_clips_between_futaleufu_bridge_seeds() -> None:
    definition = replace(
        FUTALEUFU,
        way_ids=(10, 11),
        start_seed_lon_lat=(0.01, 0.0),
        end_seed_lon_lat=(0.03, 0.0),
    )
    payload = {
        "elements": [
            _way(10, [(0.0, 0.0), (0.01, 0.0), (0.02, 0.0)]),
            _way(11, [(0.02, 0.0), (0.03, 0.0), (0.04, 0.0)]),
        ]
    }
    assert extract_route(payload, definition) == [(0.01, 0.0), (0.02, 0.0), (0.03, 0.0)]


def test_extract_route_orients_a_midway_tributary_put_in_toward_mainstem() -> None:
    definition = replace(
        FUTALEUFU,
        way_ids=(10, 11),
        start_seed_lon_lat=(0.08, 0.0),
        end_seed_lon_lat=(0.13, 0.0),
    )
    payload = {
        "elements": [
            _way(10, [(0.0, 0.0), (0.08, 0.0), (0.10, 0.0)]),
            _way(11, [(0.10, 0.0), (0.13, 0.0), (0.16, 0.0)]),
        ]
    }
    assert extract_route(payload, definition) == [(0.08, 0.0), (0.10, 0.0), (0.13, 0.0)]


def test_extract_route_rejects_disconnected_configured_ways() -> None:
    definition = replace(
        FUTALEUFU,
        way_ids=(10, 11),
        start_seed_lon_lat=(0.0, 0.0),
        end_seed_lon_lat=(1.01, 0.0),
    )
    payload = {
        "elements": [
            _way(10, [(0.0, 0.0), (0.01, 0.0)]),
            _way(11, [(1.0, 0.0), (1.01, 0.0)]),
        ]
    }
    with pytest.raises(ValueError, match="route gap"):
        extract_route(payload, definition)


def test_extract_route_rejects_missing_configured_way() -> None:
    definition = replace(ZAMBEZI, way_ids=(1,), end_station_m=100.0)
    with pytest.raises(ValueError, match="missing configured OSM ways"):
        extract_route({"elements": []}, definition)


def test_zambezi_high_resolution_terrain_lead_is_rights_gated_and_generator_bound() -> None:
    lead = json.loads(ZAMBEZI_TERRAIN_ACQUISITION_LEAD_PATH.read_text(encoding="utf-8"))
    corridor = json.loads(ZAMBEZI_CORRIDOR_MANIFEST_PATH.read_text(encoding="utf-8"))
    source_plan = json.loads(PHOTOREAL_SOURCE_PLAN_PATH.read_text(encoding="utf-8"))

    assert ZAMBEZI.terrain_acquisition_lead_file == (
        "terrain/source/batoka_high_resolution_terrain_acquisition_leads.json"
    )
    assert FUTALEUFU.terrain_acquisition_lead_file is None
    assert lead["production_promoted"] is False
    assert lead["schema"] == (
        "raftsim.zambezi_batoka_high_resolution_terrain_acquisition_leads.v4"
    )
    assert lead["status"] == (
        "survey_products_disambiguated_vol3_coverage_index_request_ready_not_sent"
    )
    assert lead["policy"]["report_figures_are_not_geometry_authority"] is True
    assert lead["policy"]["no_lidar_dtm_dsm_ortho_or_breakline_data_downloaded"] is True
    sources = {source["source_id"]: source for source in lead["discovered_sources"]}
    assert "bghes_lidar_topographic_survey_report_230_gen_r_sp_001" in sources
    assert "bghes_dam_safety_plan_346_gen_r_sp_001" in sources
    assert "pietrangeli_batoka_drone_photogrammetry_case_study" in sources
    assert "world_bank_p133380_batoka_engineering_and_lidar_records" in sources
    assert "zamcom_zamwis_public_catalog_audit" in sources
    assert all(source["data_attached"] is False for source in sources.values())
    coverage_audit = lead["coverage_audit"]
    game_reach = coverage_audit["game_reach"]
    assert game_reach["station_length_m"] == pytest.approx(30_000.0)
    assert game_reach["geometry_authority"].endswith("not_surveyed_centerline")
    assert coverage_audit["batoka_dam"][
        "straight_line_separation_from_current_review_route_m"
    ] == pytest.approx(12_767.5)
    dispositions = {
        product["product_id"]: product
        for product in coverage_audit["product_disposition"]
    }
    assert dispositions["vol3_230_gen_r_sp_001"]["coverage_status"].startswith(
        "unknown_"
    )
    assert dispositions["vol3_230_gen_r_sp_001"]["priority"] == (
        "request_report_and_coverage_index_first"
    )
    for excluded_product in (
        "dam_safety_0_3m_lidar_dtm",
        "2014_ebee_drone_dsm",
        "kariba_rehabilitation_additional_lidar",
    ):
        assert (
            dispositions[excluded_product]["can_satisfy_game_reach_replacement_gate"]
            is False
        )
        assert dispositions[excluded_product]["priority"].startswith("exclude_")
    assert sources["bghes_dam_safety_plan_346_gen_r_sp_001"][
        "coverage_status"
    ] == "documented_downstream_from_batoka_dam_to_lake_kariba"
    assert sources["pietrangeli_batoka_drone_photogrammetry_case_study"][
        "coverage_status"
    ] == "documented_13_square_kilometre_batoka_dam_site_survey"
    assert sources["world_bank_p133380_batoka_engineering_and_lidar_records"][
        "coverage_status"
    ].endswith("kariba_additional_lidar_separate")
    zamwis_audit = sources["zamcom_zamwis_public_catalog_audit"]["catalog_result"]
    assert zamwis_audit["public_thematic_layer_count"] == 65
    assert zamwis_audit["batoka_high_resolution_terrain_found"] is False
    assert zamwis_audit["survey_geometry_downloaded"] is False
    assert "classified ground point cloud or bare-earth DTM" in " ".join(
        lead["acquisition_request"]["request_products"]
    )
    assert lead["acquisition_request"]["request_template"] == (
        "docs/batoka-high-resolution-terrain-acquisition-request.md"
    )
    assert ZAMBEZI_TERRAIN_ACQUISITION_REQUEST_PATH.is_file()
    contacts = {
        contact["provider"]: contact
        for contact in lead["acquisition_request"]["contact_routes"]
    }
    assert contacts["Zambezi River Authority"]["email"] == "info@zambezira.org"
    assert contacts["Studio Ing. G. Pietrangeli S.r.l."]["email"] == (
        "info@pietrangeli.it"
    )
    assert contacts["Zambezi Watercourse Commission"]["email"] == (
        "zamcom@zambezicommission.org"
    )
    assert contacts["World Bank Access to Information"]["request_portal"].startswith(
        "https://"
    )
    assert lead["acquisition_request"]["outreach_status"]["sent"] is False
    request_text = ZAMBEZI_TERRAIN_ACQUISITION_REQUEST_PATH.read_text(encoding="utf-8")
    for bound in (
        "25.826935535974975",
        "-18.02077352349982",
        "26.01842667723117",
        "-17.90811477650018",
    ):
        assert bound in request_text
    assert "commercial desktop, console, handheld, and VR game use" in request_text
    assert "World Bank Records Request Addendum" in request_text
    assert "information disclosure is not a game-use license" in request_text
    assert "coverage polygon or sheet index" in request_text
    assert "downstream Batoka dam-to-Lake Kariba dam-break model" in request_text
    assert "We are specifically trying to establish whether Vol.3" in request_text
    assert "The request has not been sent." in request_text
    acquisition_records = [
        record
        for record in corridor["source_records"]
        if record["role"] == "high_resolution_terrain_acquisition_lead"
    ]
    assert len(acquisition_records) == 1
    assert acquisition_records[0]["authority"] == "lead_only_no_geometry_or_media_imported"
    assert acquisition_records[0]["status"] == lead["status"]
    assert acquisition_records[0]["sha256"] == sha256(
        ZAMBEZI_TERRAIN_ACQUISITION_LEAD_PATH.read_bytes()
    ).hexdigest()
    assert corridor["artifacts"]["high_resolution_terrain_acquisition_lead"].endswith(
        "batoka_high_resolution_terrain_acquisition_leads.json"
    )
    centerline_review_records = [
        record
        for record in corridor["source_records"]
        if record["role"] == "surface_water_centerline_review_candidate"
    ]
    assert len(centerline_review_records) == 1
    assert centerline_review_records[0]["production_promoted"] is False
    assert "not_surveyed_centerline_or_bathymetry" in (
        centerline_review_records[0]["authority"]
    )
    assert corridor["artifacts"]["centerline_review_candidate"].endswith(
        "sentinel2_20260610_centerline_candidate.geojson"
    )
    assert corridor["route"]["geometry_authority"] == (
        "low_precision_osm_international_boundary_trace_cross_reference_not_surveyed_centerline"
    )
    zambezi_source_plan = next(
        river for river in source_plan["rivers"] if river["river_id"] == "zambezi_batoka_gorge"
    )
    lidar_lead = next(
        source
        for source in zambezi_source_plan["river_map_sources"]
        if source["source_id"] == "zra_bghes_lidar_and_drone_survey_acquisition_leads"
    )
    assert lidar_lead["authority"] == "discovery_only_no_geometry_or_media_imported"


def test_local_centerline_uses_northwest_image_origin(tmp_path: Path) -> None:
    bbox = (20.0, -18.1, 20.2, -17.9)
    points = [(20.05, -17.92), (20.06, -18.02)]

    artifacts = _write_route_artifacts(tmp_path, ZAMBEZI, points, bbox)
    payload = json.loads(Path(artifacts["centerline_local"]).read_text(encoding="utf-8"))

    assert "southward from the northwest" in payload["local_metric_policy"]
    first_y = payload["points"][0]["unreal_local_cm"][1]
    second_y = payload["points"][1]["unreal_local_cm"][1]
    assert first_y == pytest.approx((bbox[3] - points[0][1]) * 111_320.0 * 100.0)
    assert second_y > first_y


def test_visual_channel_conditioning_is_bounded_monotone_and_manifest_recorded() -> None:
    bbox = (0.0, 0.0, 0.01, 0.01)
    points = [(0.001, 0.005), (0.005, 0.005), (0.009, 0.005)]
    definition = replace(
        ZAMBEZI,
        channel_half_width_m=20.0,
        channel_feather_width_m=30.0,
        channel_profile_smoothing_m=300.0,
        channel_maximum_downstream_slope=0.01,
        channel_bed_depth_m=2.0,
        channel_maximum_cut_m=60.0,
        channel_maximum_fill_m=0.0,
    )
    dem = np.tile(np.linspace(100.0, 200.0, 101, dtype=np.float32), (101, 1))

    conditioned, metadata = _condition_visual_channel(
        dem,
        (1_000.0, 1_000.0),
        points,
        bbox,
        definition,
    )

    route_row = round((bbox[3] - points[0][1]) * 111_320.0 / 1_000.0 * 100.0)
    center_profile = conditioned[route_row, [10, 50, 90]]
    visual_surface_profile = np.asarray(
        [sample["conditioned_surface_elevation_m"] for sample in metadata["profile_samples"]]
    )
    assert np.all(np.diff(visual_surface_profile) <= 1.0e-4)
    assert center_profile[-1] < dem[route_row, 90]
    assert np.array_equal(conditioned[0], dem[0])
    assert metadata["authority"]["changes_custom_cpp_solver_state"] is False
    assert metadata["authority"]["changes_collision_or_raft_forces"] is False
    assert metadata["measurements"]["modified_raster_sample_count"] > 0
    assert metadata["measurements"]["maximum_cut_m"] > 0.0
    assert metadata["measurements"]["maximum_cut_m"] <= 60.0
    assert metadata["measurements"]["maximum_fill_m"] == 0.0
    assert metadata["measurements"]["conditioned_profile_maximum_upstream_rise_m"] == 0.0
    assert metadata["measurements"]["conditioned_profile_maximum_downstream_slope"] <= 0.01
