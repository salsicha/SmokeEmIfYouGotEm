import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from raftsim.south_fork_photoreal_environment import (
    FLOW_BANDS,
    FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH,
    FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH,
    INFRASTRUCTURE_CATALOG_RELATIVE_PATH,
    PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH,
    RIVER_COORDINATE_MAP_RELATIVE_PATH,
    _guide_feature_aeration,
    _procedural_far_field_macro_palette,
    _solver_derived_hydraulic_aeration,
    build_south_fork_photoreal_environment_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_environment_manifest_and_every_artifact_hash_are_valid():
    manifest = build_south_fork_photoreal_environment_manifest(REPO_ROOT)

    assert manifest == _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    assert manifest["schema"] == "raftsim.south_fork.photoreal_environment.v1"
    assert manifest["algorithm"] == (
        "south_fork_photoreal_environment_v29_guide_feature_breaking_relief"
    )
    assert manifest["not_for_navigation"] is True
    assert manifest["grid"]["tile_count"] == 13
    assert manifest["presentation"]["flow_bands"] == list(FLOW_BANDS)
    assert len(manifest["determinism_signature_sha256"]) == 64


def test_domain_warped_macro_infill_is_coordinate_stable_and_not_striped():
    coordinates = np.linspace(-6_000.0, 6_000.0, 193, dtype=np.float32)
    world_x, world_y = np.meshgrid(coordinates, coordinates)
    first = _procedural_far_field_macro_palette(world_x, world_y, 0x5FA4E004)
    repeat = _procedural_far_field_macro_palette(world_x, world_y, 0x5FA4E004)
    different_seed = _procedural_far_field_macro_palette(world_x, world_y, 0x5FA4E005)

    assert first.dtype == np.float32
    assert np.array_equal(first, repeat)
    assert np.mean(np.abs(first - different_seed)) > 4.0
    assert np.array_equal(
        first[:, 48:145],
        _procedural_far_field_macro_palette(
            world_x[:, 48:145], world_y[:, 48:145], 0x5FA4E004
        ),
    )
    luminance = first[..., 0] * 0.2126 + first[..., 1] * 0.7152 + first[..., 2] * 0.0722
    assert np.std(luminance) > 9.0
    horizontal_lag = np.corrcoef(luminance[:, :-32].ravel(), luminance[:, 32:].ravel())[
        0, 1
    ]
    vertical_lag = np.corrcoef(luminance[:-32].ravel(), luminance[32:].ravel())[0, 1]
    assert max(abs(horizontal_lag), abs(vertical_lag)) < 0.92


def test_saved_meat_grinder_water_matches_runtime_named_rapid_fields():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    streaming = _load(FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH)
    assert manifest["inputs"]["named_rapid_streaming_water"] == (
        FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH
    )
    assert (
        manifest["presentation"]["named_rapid_visual_window_count"]
        == (streaming["rapid_window_count"])
    )
    assert all(
        source["all_bands_passed"]
        for source in manifest["presentation"]["named_rapid_visual_sources"]
    )

    meat_grinder = next(
        window
        for window in streaming["windows"]
        if window["rapid_name"] == "Meat Grinder"
    )
    cooked_path = REPO_ROOT / meat_grinder["cooked_fields_manifest"]
    cooked = json.loads(cooked_path.read_text(encoding="utf-8"))
    grid = cooked["grid"]
    cooked_dir = cooked_path.parent / "median_runnable"
    bed = np.load(cooked_dir / "bed.npy").T
    depth = np.load(cooked_dir / "h.npy").T
    u = np.load(cooked_dir / "u.npy").T
    v = np.load(cooked_dir / "v.npy").T
    wet = np.load(cooked_dir / "wet_mask.npy").T
    source_stations = float(grid["origin_x_m"]) + float(grid["dx_m"]) * np.arange(
        int(grid["nx"])
    )

    coordinate_map = _load(RIVER_COORDINATE_MAP_RELATIVE_PATH)
    full_stations = np.asarray(coordinate_map["points"], dtype=np.float64)[:, 0]
    row = int(np.argmin(np.abs(full_stations - 960.0)))
    station_m = full_stations[row]
    lateral_column = int(grid["ny"]) // 2

    def sample(values: np.ndarray) -> float:
        return float(np.interp(station_m, source_stations, values[:, lateral_column]))

    expected_depth = sample(depth)
    expected_speed = float(np.hypot(sample(u), sample(v)))
    rapid_authority = np.ones(depth.shape, dtype=np.float32)
    expected_foam_field = _solver_derived_hydraulic_aeration(
        depth,
        bed + depth + float(cooked["source_elevation_datum_m"]),
        u,
        v,
        wet.astype(bool),
        float(grid["dx_m"]),
        float(grid["dy_m"]),
        rapid_authority,
    )
    feature_path = (
        cooked_path.parent.parent / "scenario" / "median_runnable" / "features.json"
    )
    features = _load(str(feature_path.relative_to(REPO_ROOT)))["features"]
    expected_foam_field = np.maximum(
        expected_foam_field,
        _guide_feature_aeration(
            features,
            source_stations,
            float(grid["origin_y_m"])
            + float(grid["dy_m"]) * np.arange(int(grid["ny"])),
            u,
            v,
            wet.astype(bool),
        ),
    )
    expected_foam = sample(expected_foam_field)
    expected_presentation = np.asarray(
        [
            np.rint(expected_foam * 255.0),
            np.rint(np.clip(expected_depth / 4.0, 0.0, 1.0) * 255.0),
            np.rint(np.clip(expected_speed / 8.0, 0.0, 1.0) * 255.0),
            255 if sample(wet) >= 0.5 else 0,
        ],
        dtype=np.uint8,
    )
    tile = next(
        tile
        for tile in manifest["unreal_import"]["tiles"]
        if tile["row_range"][0] <= row <= tile["row_range"][1]
    )
    tile_row = row - tile["row_range"][0]
    band = tile["water_bands"]["median_runnable"]
    with Image.open(REPO_ROOT / band["presentation"]["path"]) as image:
        actual_presentation = np.asarray(image)[tile_row, lateral_column]
    # Aeration derivatives are evaluated after the named window is resampled
    # onto the continuous full-reach grid, so the raw-window estimate may
    # differ by a few quantization levels while depth/speed/wetness remain exact.
    assert abs(int(actual_presentation[0]) - int(expected_presentation[0])) <= 5
    assert np.array_equal(actual_presentation[1:], expected_presentation[1:])

    with Image.open(REPO_ROOT / band["surface_height"]["path"]) as image:
        encoded_surface = float(np.asarray(image)[tile_row, lateral_column])
    encoding = tile["water_height_encoding"]
    actual_surface_m = float(encoding["minimum_elevation_m"]) + (
        encoded_surface / 65535.0
    ) * (
        float(encoding["maximum_elevation_m"]) - float(encoding["minimum_elevation_m"])
    )
    expected_surface_m = (
        sample(bed) + expected_depth + float(cooked["source_elevation_datum_m"])
    )
    assert actual_surface_m == pytest.approx(expected_surface_m, abs=0.007)

    transit_dir = (
        REPO_ROOT / FULL_REACH_TRANSIT_MANIFEST_RELATIVE_PATH
    ).parent / "median_runnable"
    transit_surface = (
        np.load(transit_dir / "bed.npy").T[row, lateral_column]
        + np.load(transit_dir / "h.npy").T[row, lateral_column]
    )
    assert abs(expected_surface_m - float(transit_surface)) > 0.25


def test_named_rapid_aeration_is_solver_derived_bounded_and_scope_gated():
    streaming = _load(FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH)
    troublemaker = next(
        window
        for window in streaming["windows"]
        if window["rapid_name"] == "Troublemaker"
    )
    cooked_path = REPO_ROOT / troublemaker["cooked_fields_manifest"]
    cooked = _load(str(cooked_path.relative_to(REPO_ROOT)))
    band_dir = cooked_path.parent / "median_runnable"
    bed = np.load(band_dir / "bed.npy").T
    depth = np.load(band_dir / "h.npy").T
    u = np.load(band_dir / "u.npy").T
    v = np.load(band_dir / "v.npy").T
    wet = np.load(band_dir / "wet_mask.npy").T.astype(bool)
    authority = np.ones(depth.shape, dtype=np.float32)

    enriched = _solver_derived_hydraulic_aeration(
        depth,
        bed + depth + float(cooked["source_elevation_datum_m"]),
        u,
        v,
        wet,
        float(cooked["grid"]["dx_m"]),
        float(cooked["grid"]["dy_m"]),
        authority,
    )
    legacy = (
        np.clip(
            np.hypot(u, v) / np.sqrt(9.80665 * np.maximum(depth, 0.05)) - 0.72,
            0.0,
            1.18,
        )
        / 1.18
        * wet
    )
    gated_off = _solver_derived_hydraulic_aeration(
        depth,
        bed + depth + float(cooked["source_elevation_datum_m"]),
        u,
        v,
        wet,
        float(cooked["grid"]["dx_m"]),
        float(cooked["grid"]["dy_m"]),
        np.zeros(depth.shape, dtype=np.float32),
    )

    assert np.array_equal(gated_off, legacy)
    assert np.all(enriched >= legacy)
    assert float(np.max(enriched)) <= 1.0
    assert np.count_nonzero(enriched[wet] > 0.045) > 3 * np.count_nonzero(
        legacy[wet] > 0.045
    )
    assert np.count_nonzero(enriched[~wet]) == 0


def test_guide_feature_aeration_is_bounded_review_gated_presentation_infill():
    streaming = _load(FULL_HYDRAULICS_STREAMING_MANIFEST_RELATIVE_PATH)
    troublemaker = next(
        window
        for window in streaming["windows"]
        if window["rapid_name"] == "Troublemaker"
    )
    cooked_path = REPO_ROOT / troublemaker["cooked_fields_manifest"]
    cooked = _load(str(cooked_path.relative_to(REPO_ROOT)))
    grid = cooked["grid"]
    band_dir = cooked_path.parent / "median_runnable"
    u = np.load(band_dir / "u.npy").T
    v = np.load(band_dir / "v.npy").T
    wet = np.load(band_dir / "wet_mask.npy").T.astype(bool)
    stations_m = float(grid["origin_x_m"]) + float(grid["dx_m"]) * np.arange(
        int(grid["nx"])
    )
    lateral_m = float(grid["origin_y_m"]) + float(grid["dy_m"]) * np.arange(
        int(grid["ny"])
    )
    feature_path = (
        cooked_path.parent.parent / "scenario" / "median_runnable" / "features.json"
    )
    features = _load(str(feature_path.relative_to(REPO_ROOT)))["features"]
    aeration = _guide_feature_aeration(
        features, stations_m, lateral_m, u, v, wet
    )

    assert len(features) == 17
    assert float(np.max(aeration)) <= 1.0
    assert np.count_nonzero(aeration > 0.045) > 100
    assert np.count_nonzero(aeration[~wet]) == 0
    assert not np.any(
        _guide_feature_aeration([], stations_m, lateral_m, u, v, wet)
    )


def test_dense_coordinate_map_round_trips_station_lateral_geometry():
    coordinate_map = _load(RIVER_COORDINATE_MAP_RELATIVE_PATH)
    points = np.asarray(coordinate_map["points"], dtype=np.float64)

    assert coordinate_map["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert coordinate_map["not_for_navigation"] is True
    assert points.shape == (12271, 5)
    assert points[0, 0] == 0.0
    assert np.isclose(points[-1, 0], 49077.732, atol=0.01)
    assert np.max(np.diff(points[:, 0])) <= 4.001
    assert np.allclose(np.linalg.norm(points[:, 3:5], axis=1), 1.0, atol=1e-5)
    assert np.ptp(points[:, 1]) > 10_000.0
    assert np.ptp(points[:, 2]) > 5_000.0
    world_step_m = np.linalg.norm(np.diff(points[:, 1:3], axis=0), axis=1)
    assert np.isclose(np.sum(world_step_m), points[-1, 0], rtol=2e-4)
    assert 0.7 < coordinate_map["epsg3857_to_ground_scale"] < 0.9
    normal_step = np.linalg.norm(np.diff(points[:, 3:5], axis=0), axis=1)
    assert np.max(normal_step) < 0.04
    left_edge_step = np.linalg.norm(
        np.diff(points[:, 1:3] + points[:, 3:5] * 256.0, axis=0), axis=1
    )
    right_edge_step = np.linalg.norm(
        np.diff(points[:, 1:3] - points[:, 3:5] * 256.0, axis=0), axis=1
    )
    assert max(np.max(left_edge_step), np.max(right_edge_step)) < 16.0

    lateral = 37.5
    row = 4096
    world = points[row, 1:3] + points[row, 3:5] * lateral
    recovered_lateral = np.dot(world - points[row, 1:3], points[row, 3:5])
    assert np.isclose(recovered_lateral, lateral, atol=1e-6)


def test_tile_products_are_complete_and_seam_identical():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    previous: dict[str, np.ndarray] | None = None
    previous_range: list[int] | None = None
    labels = (
        "macro_albedo",
        "normal",
        "ao_roughness_height",
        "vegetation_species_density",
        "water_vfx_zones",
    )
    for tile in manifest["unreal_import"]["tiles"]:
        current: dict[str, np.ndarray] = {}
        for label in labels:
            with Image.open(REPO_ROOT / tile[label]["path"]) as image:
                assert image.size == (129, 1009)
                assert image.mode in {"RGB", "RGBA"}
                current[label] = np.asarray(image)
        for band_id in FLOW_BANDS:
            with Image.open(
                REPO_ROOT / tile["water_bands"][band_id]["surface_height"]["path"]
            ) as image:
                assert image.size == (21, 1009)
                assert image.mode == "I;16"
                current[f"{band_id}_height"] = np.asarray(image)
            with Image.open(
                REPO_ROOT / tile["water_bands"][band_id]["presentation"]["path"]
            ) as image:
                assert image.size == (21, 1009)
                assert image.mode == "RGBA"
                current[f"{band_id}_presentation"] = np.asarray(image)

        if previous is not None and previous_range is not None:
            start, stop = tile["row_range"]
            overlap_start = max(previous_range[0], start)
            overlap_stop = min(previous_range[1], stop)
            assert overlap_stop >= overlap_start
            previous_offset = overlap_start - previous_range[0]
            current_offset = overlap_start - start
            count = overlap_stop - overlap_start + 1
            for label, values in current.items():
                assert np.array_equal(
                    previous[label][previous_offset : previous_offset + count],
                    values[current_offset : current_offset + count],
                )
        previous = current
        previous_range = tile["row_range"]


def test_source_conditioning_and_all_presentation_channels_are_nontrivial():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    albedo_means = []
    vegetation_nonzero = 0
    vfx_nonzero = 0
    wet_by_band = {}
    foam_by_band = {}
    for tile in manifest["unreal_import"]["tiles"]:
        with Image.open(REPO_ROOT / tile["macro_albedo"]["path"]) as image:
            albedo = np.asarray(image)
            albedo_means.append(np.mean(albedo, axis=(0, 1)))
            # Raw RGB dispersion rewards cross-flight exposure mismatch. The
            # normalized product must instead retain both chromatic spread and
            # a substantial within-tile luminance range.
            luminance = (
                albedo[..., 0] * 0.2126
                + albedo[..., 1] * 0.7152
                + albedo[..., 2] * 0.0722
            )
            assert np.std(albedo) > 13.5
            assert np.percentile(luminance, 95) - np.percentile(luminance, 5) > 38.0
        with Image.open(
            REPO_ROOT / tile["vegetation_species_density"]["path"]
        ) as image:
            vegetation_nonzero += int(np.count_nonzero(np.asarray(image)))
        with Image.open(REPO_ROOT / tile["water_vfx_zones"]["path"]) as image:
            vfx_nonzero += int(np.count_nonzero(np.asarray(image)))
        for band_id in FLOW_BANDS:
            with Image.open(
                REPO_ROOT / tile["water_bands"][band_id]["presentation"]["path"]
            ) as image:
                presentation = np.asarray(image)
                wet_by_band[band_id] = wet_by_band.get(band_id, 0) + int(
                    np.count_nonzero(presentation[..., 3])
                )
                foam_by_band[band_id] = foam_by_band.get(band_id, 0) + int(
                    np.count_nonzero(presentation[..., 0])
                )

    assert np.ptp(np.asarray(albedo_means), axis=0).max() > 8.0
    assert vegetation_nonzero > 100_000
    assert vfx_nonzero > 100_000
    assert all(wet_by_band[band] > 20_000 for band in FLOW_BANDS)
    assert all(foam_by_band[band] > 0 for band in FLOW_BANDS)
    assert wet_by_band["high_runnable"] > wet_by_band["low_runnable"]


def test_infrastructure_infill_is_explicit_and_never_navigation_authority():
    catalog = _load(INFRASTRUCTURE_CATALOG_RELATIVE_PATH)

    assert catalog["not_for_navigation"] is True
    assert len(catalog["sites"]) == 3
    assert catalog["sites"][-1]["station_m"] == 49077.732
    assert catalog["policy"][
        "unconfirmed_roads_bridges_and_bank_landings_are_procedural_game_infill"
    ]
    assert all("authority" in site for site in catalog["sites"])
    assert all(
        "procedural" in item["authority"] for item in catalog["procedural_structures"]
    )


def test_far_field_geography_is_a_continuous_lowered_channel_underlay():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    far_field = manifest["far_field"]

    assert far_field["patch_count"] == 8
    assert far_field["grid_size"] == [1593, 663]
    assert far_field["macro_texture_size"] == 1024
    topology = dict(far_field["topology"])
    aerial_exposure = topology.pop("aerial_exposure_normalization")
    assert topology == {
        "algorithm": "edge_weighted_official_source_mosaic_then_shared_grid_tiling",
        "authoritative_vertex_fraction": pytest.approx(0.426457, abs=1e-6),
        "cell_size_m": 20.0,
        "corridor_alignment_below_detailed_m": 1.5,
        "corridor_alignment_fade_distance_m": 520.0,
        "corridor_alignment_full_distance_m": 124.0,
        "corridor_render_overlap_m": 12.0,
        "detailed_terrain_half_width_m": 112.0,
        "global_bounds_local_m": [-29920.0, -6040.0, 1920.0, 7200.0],
        "global_grid_dimensions": [1593, 663],
        "not_for_navigation": True,
        "procedural_infill_explicit": True,
        "procedural_infill_maximum_relief_m": 28.0,
        "procedural_macro_land_cover": (
            "domain_warped_world_space_dry_grass_chaparral_woodland_rock_v2"
        ),
        "procedural_route_extension_each_endpoint_m": 1800.0,
        "procedural_route_extension_not_for_navigation": True,
        "procedural_route_extension_step_m": 32.0,
        "procedural_domain_padding_m": 1600.0,
        "shared_edge_vertices": True,
        "shared_height_encoding": True,
        "source_edge_blend_distance_m": 720.0,
        "source_window_ownership_cuts": False,
        "tile_layout": [4, 2],
        "valley_conditioning_full_distance_m": 180.0,
        "valley_conditioning_start_distance_m": 80.0,
        "valley_grade_base_m": 1.5,
        "valley_grade_cap_fade_distance_m": 1800.0,
        "source_relief_unmodified_beyond_distance_m": 1800.0,
        "valley_grade_cap_full_distance_m": 900.0,
        "valley_gully_carve_maximum_depth_m": 14.0,
        "valley_gully_carve_only_lowers_envelope": True,
        "valley_gully_carve_start_distance_m": 120.0,
        "valley_profile_exponent": 0.8,
        "valley_profile_scale": 0.42,
    }
    assert aerial_exposure["algorithm"] == (
        "bounded_per_window_robust_median_luminance_v1"
    )
    assert aerial_exposure["target_median_luminance"] == pytest.approx(
        96.186699, abs=1e-6
    )
    assert aerial_exposure["gain_bounds"] == [0.68, 1.18]
    assert aerial_exposure["contrast_gain_bounds"] == [1.0, 1.25]
    assert len(aerial_exposure["sources"]) == 8
    exposure_by_window = {
        source["window_id"]: source for source in aerial_exposure["sources"]
    }
    assert exposure_by_window["salmon_falls_takeout_approach_41500_49077m"][
        "applied_gain"
    ] == pytest.approx(0.68, abs=1e-6)
    assert exposure_by_window["salmon_falls_takeout_approach_41500_49077m"][
        "applied_contrast_gain"
    ] == pytest.approx(1.25, abs=1e-6)
    assert manifest["source_conditioning"]["aerial_exposure_normalization"] == (
        aerial_exposure
    )
    assert far_field["corridor_exclusion_radius_m"] == 100.0
    assert far_field["corridor_underlay_falloff_m"] == 136.0
    assert far_field["corridor_underlay_max_depth_m"] == 6.4
    assert far_field["continuous_underlay"] is True
    assert far_field["procedural_infill_explicit"] is True
    assert far_field["not_for_navigation"] is True
    assert manifest["acceptance"]["far_field_geography_complete"] is True
    total_visible = 0
    total_excluded = 0
    loaded_patches = []
    for patch in far_field["patches"]:
        assert "USGS_3DEP" in patch["authority"]
        assert patch["topology"] == "shared_global_grid_streaming_tile"
        assert patch["dimensions"] == [399, 332]
        assert patch["macro_dimensions"] == [1024, 1024]
        assert patch["height_encoding"]["shared_across_all_tiles"] is True
        minimum_x, minimum_y, maximum_x, maximum_y = patch["bounds_local_m"]
        assert maximum_x > minimum_x
        assert maximum_y > minimum_y
        with Image.open(REPO_ROOT / patch["height"]["path"]) as image:
            assert image.size == (399, 332)
            assert image.mode == "I;16"
            height = np.asarray(image)
        with Image.open(REPO_ROOT / patch["macro_albedo"]["path"]) as image:
            assert image.size == (1024, 1024)
            assert image.mode == "RGB"
            macro = np.asarray(image)
            assert np.std(macro) > 10.0
        with Image.open(REPO_ROOT / patch["corridor_exclusion_mask"]["path"]) as image:
            mask = np.asarray(image)
            assert image.size == (399, 332)
            assert image.mode == "L"
            total_visible += int(np.count_nonzero(mask))
            total_excluded += int(np.count_nonzero(mask == 0))
        with Image.open(
            REPO_ROOT / patch["source_window_ownership_mask"]["path"]
        ) as image:
            ownership = np.asarray(image)
            assert image.size == (399, 332)
            assert image.mode == "L"
            assert np.all(ownership == 255)
            assert patch["owned_vertex_fraction"] == 1.0
        with Image.open(REPO_ROOT / patch["river_distance_to_route"]["path"]) as image:
            river_distance = np.asarray(image)
            assert image.size == (399, 332)
            assert image.mode == "I;16"
            assert np.max(river_distance) > 11_000
            assert patch["river_distance_encoding"] == {
                "unit": "decimeter",
                "meters_per_uint16": 0.1,
                "maximum_representable_m": 6553.5,
            }
        loaded_patches.append(
            {
                "height": height,
                "macro": macro,
                "mask": mask,
                "ownership": ownership,
                "river_distance": river_distance,
            }
        )

    for row in range(2):
        for column in range(3):
            left = loaded_patches[row * 4 + column]
            right = loaded_patches[row * 4 + column + 1]
            for key in ("height", "macro", "mask", "ownership", "river_distance"):
                assert np.array_equal(left[key][:, -1], right[key][:, 0])
    for column in range(4):
        north = loaded_patches[column]
        south = loaded_patches[4 + column]
        for key in ("height", "macro", "mask", "ownership", "river_distance"):
            assert np.array_equal(north[key][-1], south[key][0])

    assert 0 < total_visible < 8 * 399 * 332
    assert total_excluded > 0


def test_manifest_hashes_match_direct_sha256_for_primary_products():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    for key in ("coordinate_map", "infrastructure_catalog", "boulder_catalog"):
        artifact = manifest[key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
