import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_procedural_geography import (
    FEATURE_BOULDER,
    FEATURE_CHANNEL,
    FEATURE_EDDY,
    FEATURE_HOLE_CONTROL,
    FEATURE_LEDGE,
    FEATURE_SHELF,
    FEATURE_SHORELINE_BREAKUP,
    FEATURE_WAVE_TRAIN,
    MATERIAL_EXPOSED_ROCK,
    MATERIAL_VEGETATION,
    PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
    _effective_raster_bounds,
    build_south_fork_procedural_geography_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_procedural_geography_manifest_and_artifact_hashes_are_valid():
    manifest = build_south_fork_procedural_geography_manifest(REPO_ROOT)

    assert manifest == _load_manifest()
    assert manifest["schema"] == "raftsim.south_fork.procedural_geography.v1"
    assert manifest["status"] == "full_reach_procedural_geography_complete"
    assert manifest["authority_policy"]["never_claim_as_surveyed"] is True
    assert manifest["authority_policy"]["not_for_navigation"] is True
    assert manifest["acceptance"]["ready_for_hydraulic_authoring_m3"] is True
    assert len(manifest["determinism_signature_sha256"]) == 64


def test_procedural_geography_grid_is_continuous_complete_and_labelled():
    manifest = _load_manifest()
    with np.load(REPO_ROOT / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH) as grid:
        stations = grid["stations_m"]
        lateral = grid["lateral_offsets_m"]
        bed = grid["bed_elevation_m"]
        source = grid["source_authority"]
        source_vegetation_score = grid["source_vegetation_score"]
        procedural = grid["procedural_infill"]
        uncertainty = grid["uncertainty"]
        features = grid["features"]
        water_surface = grid["conditioned_water_surface_m"]
        channel_half_width = grid["channel_half_width_m"]
        ground_scale = float(grid["epsg3857_to_ground_scale"])
        frame_smoothing_radius_m = float(grid["centerline_frame_smoothing_radius_m"])
        center = (
            np.column_stack(
                (
                    grid["centerline_epsg3857_x_m"],
                    grid["centerline_epsg3857_y_m"],
                )
            )
            * ground_scale
        )
        normals = np.column_stack(
            (grid["centerline_normal_x"], grid["centerline_normal_y"])
        )

        assert stations[0] == 0.0
        assert np.isclose(stations[-1], 49077.732, atol=0.01)
        assert np.max(np.diff(stations)) <= 4.001
        assert 0.7 < ground_scale < 0.9
        assert frame_smoothing_radius_m == 128.0
        assert lateral[0] == -256.0
        assert lateral[-1] == 256.0
        assert bed.shape == (stations.size, lateral.size)
        assert source_vegetation_score.shape == bed.shape
        assert np.isfinite(bed).all()
        assert np.array_equal(
            source.astype(np.uint16) + procedural, np.full(source.shape, 255)
        )
        assert np.any(source == 255)
        assert np.any(procedural == 255)
        assert np.mean(uncertainty[procedural == 255]) > np.mean(
            uncertainty[source == 255]
        )
        for bit in (
            FEATURE_CHANNEL,
            FEATURE_SHELF,
            FEATURE_BOULDER,
            FEATURE_LEDGE,
            FEATURE_HOLE_CONTROL,
            FEATURE_WAVE_TRAIN,
            FEATURE_EDDY,
            FEATURE_SHORELINE_BREAKUP,
        ):
            assert np.count_nonzero(features & bit) > 0

        # The river must stay seated in its valley. This catches using an
        # export request bbox instead of the expanded GeoTIFF response extent,
        # which previously floated long channel sections tens of meters above
        # their source-conditioned banks.
        lateral_grid = np.abs(lateral[None, :])
        near_bank = (lateral_grid >= channel_half_width[:, None] + 12.0) & (
            lateral_grid <= channel_half_width[:, None] + 28.0
        )
        bank_clearance = (
            bed[near_bank]
            - np.repeat(water_surface[:, None], lateral.size, axis=1)[near_bank]
        )
        assert np.percentile(bank_clearance, 5.0) > -4.0
        assert np.percentile(bank_clearance, 50.0) > 0.5

        # A wide curvilinear strip must rotate gradually.  Raw polyline
        # normals previously moved an outer edge over 150 m between adjacent
        # four-metre rows, producing the floating terrain ribbons caught in
        # the M4 captures.
        left_edge = center + normals * 256.0
        right_edge = center - normals * 256.0
        maximum_edge_step = max(
            np.max(np.linalg.norm(np.diff(left_edge, axis=0), axis=1)),
            np.max(np.linalg.norm(np.diff(right_edge, axis=0), axis=1)),
        )
        assert maximum_edge_step < 16.0

    assert manifest["grid"]["no_voids"] is True
    assert manifest["continuity"]["no_unbounded_discontinuities"] is True
    assert manifest["continuity"]["maximum_center_bed_step_m"] < 2.0
    assert manifest["continuity"]["maximum_corridor_edge_step_m"] < 16.0
    detailed_orientation = manifest["continuity"][
        "unreal_detailed_ribbon_orientation"
    ]
    assert detailed_orientation["half_width_m"] == 112.0
    assert detailed_orientation["inverted_or_degenerate_triangle_count"] == 0
    assert detailed_orientation["mixed_orientation_cell_count"] == 0
    assert detailed_orientation["affected_row_count"] == 0


def test_source_backed_canopy_is_not_stripped_from_plausible_wooded_slopes():
    manifest = _load_manifest()
    with np.load(REPO_ROOT / PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH) as grid:
        lateral = grid["lateral_offsets_m"]
        material = grid["material"]
        vegetation_score = grid["source_vegetation_score"]
        source_dem = grid["source_dem_elevation_m"]
        features = grid["features"]
        cross_slope = np.abs(np.gradient(source_dem, 4.0, axis=1))
        visible_bank = np.broadcast_to(
            (np.abs(lateral)[None, :] >= 34.0)
            & (np.abs(lateral)[None, :] <= 112.0),
            material.shape,
        )
        strong_source_canopy = (
            visible_bank & (vegetation_score > 142)
        )
        dry_bank = (
            (features & FEATURE_SHORELINE_BREAKUP) == 0
        ) & ((features & FEATURE_CHANNEL) == 0)
        plausible_wooded_slope = (
            strong_source_canopy & dry_bank & (cross_slope <= 1.25)
        )
        extreme_source_slope = strong_source_canopy & dry_bank & (cross_slope > 1.25)

        assert np.count_nonzero(plausible_wooded_slope) > 50_000
        assert np.all(material[plausible_wooded_slope] == MATERIAL_VEGETATION)
        assert np.all(material[extreme_source_slope] == MATERIAL_EXPOSED_ROCK)

    classification = manifest["surface_classification"]
    assert classification["strong_source_vegetation_score_threshold"] == 142
    assert classification["maximum_wooded_cross_slope"] == 1.25
    assert classification["visible_strong_source_canopy_preserved_fraction"] > 0.9
    assert classification["visible_bank_lateral_range_m"] == [34.0, 112.0]
    assert manifest["bank_conditioning"] == {
        "algorithm": "world_space_bounded_erosion_envelope_v1",
        "authority": (
            "procedural game infill where the adopted route and source DEM "
            "thalweg are horizontally misregistered; never surveyed"
        ),
        "full_conditioning_distance_from_bank_m": 88.0,
        "maximum_erosion_relief_m": 5.5,
        "profile_base_m": 0.35,
        "profile_linear_grade": 0.09,
        "profile_quadratic_grade": 0.00032,
        "provenance_mask_updated_per_changed_sample": True,
        "source_fade_distance_from_bank_m": 224.0,
        "source_samples_retained": True,
        "wet_transition_m": 14.0,
    }


def test_geotiff_response_extent_overrides_non_square_request_bounds():
    manifest = _load_manifest()
    first_source = json.loads(
        (
            REPO_ROOT / manifest["inputs"]["source_windows"][0]["manifest_path"]
        ).read_text(encoding="utf-8")
    )
    artifact = first_source["source_artifacts"]["dem"]
    with Image.open(REPO_ROOT / artifact["path"]) as image:
        actual = _effective_raster_bounds(image, artifact["source_bounds_epsg3857"])
    requested = artifact["source_bounds_epsg3857"]
    assert np.isclose(actual[0], requested[0], atol=0.01)
    assert np.isclose(actual[2], requested[2], atol=0.01)
    assert actual[1] < requested[1] - 500.0
    assert actual[3] > requested[3] + 500.0


def test_procedural_geography_boulders_are_seeded_and_traceable():
    catalog = json.loads(
        (REPO_ROOT / PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    manifest = _load_manifest()

    assert catalog["authority"] == "procedural_infill"
    assert catalog["not_for_navigation"] is True
    assert catalog["count"] == manifest["hydraulic_features"]["boulder_count"]
    assert catalog["count"] >= 50
    assert all(item["seed"] > 0 for item in catalog["boulders"])
    assert all(item["authority"] == "procedural_infill" for item in catalog["boulders"])
    assert all(0.0 <= item["station_m"] <= 49077.732 for item in catalog["boulders"])


def test_unreal_tiles_share_render_collision_heights_and_overlap_exactly():
    manifest = _load_manifest()
    tiles = manifest["unreal_import"]["tiles"]

    assert manifest["unreal_import"]["tile_count"] == 13
    assert tiles[0]["station_range_m"][0] == 0.0
    assert np.isclose(tiles[-1]["station_range_m"][1], 49077.732, atol=0.01)
    previous_height = None
    previous_range = None
    for tile in tiles:
        render = tile["render_heightfield"]
        collision = tile["collision_heightfield"]
        assert render["path"] == collision["path"]
        assert render["sha256"] == collision["sha256"]
        assert tile["render_collision_registered"] is True
        height_path = REPO_ROOT / render["path"]
        assert _sha256(height_path) == render["sha256"]
        with Image.open(height_path) as image:
            height = np.asarray(image)
            assert image.size == (129, 1009)
            assert image.mode == "I;16"
        with Image.open(REPO_ROOT / tile["packed_authority_features"]["path"]) as image:
            assert image.size == (129, 1009)
            assert image.mode == "RGBA"
        with Image.open(REPO_ROOT / tile["material_mask"]["path"]) as image:
            assert image.size == (129, 1009)
            assert image.mode == "L"
        if previous_height is not None:
            overlap_start = max(previous_range[0], tile["row_range"][0])
            overlap_stop = min(previous_range[1], tile["row_range"][1])
            assert overlap_stop >= overlap_start
            previous_offset = overlap_start - previous_range[0]
            current_offset = overlap_start - tile["row_range"][0]
            count = overlap_stop - overlap_start + 1
            assert np.array_equal(
                previous_height[previous_offset : previous_offset + count],
                height[current_offset : current_offset + count],
            )
        previous_height = height
        previous_range = tile["row_range"]
