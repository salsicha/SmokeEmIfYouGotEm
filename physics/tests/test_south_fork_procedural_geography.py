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
    PROCEDURAL_BOULDER_CATALOG_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_GRID_RELATIVE_PATH,
    PROCEDURAL_GEOGRAPHY_MANIFEST_RELATIVE_PATH,
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
        procedural = grid["procedural_infill"]
        uncertainty = grid["uncertainty"]
        features = grid["features"]

        assert stations[0] == 0.0
        assert np.isclose(stations[-1], 49077.732, atol=0.01)
        assert np.max(np.diff(stations)) <= 4.001
        assert lateral[0] == -256.0
        assert lateral[-1] == 256.0
        assert bed.shape == (stations.size, lateral.size)
        assert np.isfinite(bed).all()
        assert np.array_equal(source.astype(np.uint16) + procedural, np.full(source.shape, 255))
        assert np.any(source == 255)
        assert np.any(procedural == 255)
        assert np.mean(uncertainty[procedural == 255]) > np.mean(uncertainty[source == 255])
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

    assert manifest["grid"]["no_voids"] is True
    assert manifest["continuity"]["no_unbounded_discontinuities"] is True
    assert manifest["continuity"]["maximum_center_bed_step_m"] < 2.0


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
