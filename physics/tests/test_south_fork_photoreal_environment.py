import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from raftsim.south_fork_photoreal_environment import (
    FLOW_BANDS,
    INFRASTRUCTURE_CATALOG_RELATIVE_PATH,
    PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH,
    RIVER_COORDINATE_MAP_RELATIVE_PATH,
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
        "south_fork_photoreal_environment_v12_fold_safe_registered_corridor"
    )
    assert manifest["not_for_navigation"] is True
    assert manifest["grid"]["tile_count"] == 13
    assert manifest["presentation"]["flow_bands"] == list(FLOW_BANDS)
    assert len(manifest["determinism_signature_sha256"]) == 64


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
            assert np.std(albedo) > 15.0
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
    assert far_field["grid_size"] == 257
    assert far_field["corridor_exclusion_radius_m"] == 52.0
    assert far_field["corridor_underlay_falloff_m"] == 80.0
    assert far_field["corridor_underlay_max_depth_m"] == 6.4
    assert far_field["continuous_underlay"] is True
    assert far_field["procedural_infill_explicit"] is True
    assert far_field["not_for_navigation"] is True
    assert manifest["acceptance"]["far_field_geography_complete"] is True
    total_visible = 0
    total_excluded = 0
    for patch in far_field["patches"]:
        assert "USGS_3DEP" in patch["authority"]
        assert patch["dimensions"] == [257, 257]
        minimum_x, minimum_y, maximum_x, maximum_y = patch["bounds_local_m"]
        assert maximum_x > minimum_x
        assert maximum_y > minimum_y
        with Image.open(REPO_ROOT / patch["height"]["path"]) as image:
            assert image.size == (257, 257)
            assert image.mode == "I;16"
        with Image.open(REPO_ROOT / patch["macro_albedo"]["path"]) as image:
            assert image.size == (257, 257)
            assert image.mode == "RGB"
            assert np.std(np.asarray(image)) > 10.0
        with Image.open(REPO_ROOT / patch["corridor_exclusion_mask"]["path"]) as image:
            mask = np.asarray(image)
            assert image.size == (257, 257)
            assert image.mode == "L"
            total_visible += int(np.count_nonzero(mask))
            total_excluded += int(np.count_nonzero(mask == 0))
        with Image.open(
            REPO_ROOT / patch["source_window_ownership_mask"]["path"]
        ) as image:
            ownership = np.asarray(image)
            assert image.size == (257, 257)
            assert image.mode == "L"
            assert np.count_nonzero(ownership) > 0
            assert np.count_nonzero(ownership == 0) > 0
            assert patch["owned_vertex_fraction"] == pytest.approx(
                np.count_nonzero(ownership) / ownership.size, abs=1e-6
            )
    assert 0 < total_visible < 8 * 257 * 257
    assert total_excluded > 0


def test_manifest_hashes_match_direct_sha256_for_primary_products():
    manifest = _load(PHOTOREAL_ENVIRONMENT_MANIFEST_RELATIVE_PATH)
    for key in ("coordinate_map", "infrastructure_catalog", "boulder_catalog"):
        artifact = manifest[key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
