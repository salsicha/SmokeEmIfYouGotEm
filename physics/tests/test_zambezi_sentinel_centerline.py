from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from raftsim.zambezi_sentinel_centerline import select_centerline_offsets


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    REPO_ROOT
    / "physics/data/real_world/zambezi_batoka_gorge/hydrography/review/"
    "sentinel2_20260610_centerline_candidate_manifest.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_offset_selector_tracks_smooth_observed_channel() -> None:
    offsets = np.arange(-40.0, 41.0, 10.0)
    expected = np.asarray([-20.0, -10.0, 0.0, 10.0, 20.0])
    scores = np.stack(
        [-(offsets - target) ** 2 / 100.0 for target in expected],
        axis=0,
    )
    selected = select_centerline_offsets(scores, offsets)
    assert np.array_equal(selected, expected)


def test_committed_candidate_is_bounded_hashed_and_review_only() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["schema"] == "raftsim.zambezi_sentinel_centerline_candidate.v1"
    assert manifest["production_promoted"] is False
    assert manifest["processing"]["target_crs"] == "EPSG:32735"
    assert manifest["processing"]["target_resolution_m"] == 10.0
    assert manifest["processing"]["maximum_lateral_search_m"] == 200.0
    assert {scene["item_id"] for scene in manifest["source"]["scenes"]} == {
        "S2C_35KLA_20260610_0_L2A",
        "S2C_35KMA_20260610_0_L2A",
    }

    authority = manifest["authority"]
    assert authority["surveyed_centerline"] is False
    assert authority["bathymetry"] is False
    assert authority["may_replace_production_corridor"] is False
    assert authority["changes_cpp_solver_or_geoclaw_state"] is False

    measurements = manifest["measurements"]
    assert 28_000.0 <= measurements["candidate_simplified_length_m"] <= 32_000.0
    assert measurements["maximum_absolute_lateral_shift_m"] <= 200.0
    assert measurements["large_shift_sample_count"] > 0
    assert measurements["large_shift_station_ranges"]
    assert measurements["candidate_water_support_fraction"] >= (
        measurements["source_route_water_support_fraction"]
    )
    assert measurements["candidate_median_ndwi"] >= measurements["source_route_median_ndwi"]

    for output in manifest["outputs"].values():
        path = REPO_ROOT / output["path"]
        assert path.is_file()
        assert _sha256(path) == output["sha256"]


def test_committed_candidate_geojson_preserves_review_authority() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    path = REPO_ROOT / manifest["outputs"]["candidate_geojson"]["path"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    feature = payload["features"][0]
    coordinates = feature["geometry"]["coordinates"]

    assert feature["geometry"]["type"] == "LineString"
    assert len(coordinates) >= 100
    assert feature["properties"]["status"] == "review_candidate_not_production_geometry"
    assert "not_surveyed_centerline_or_bathymetry" in (
        feature["properties"]["geometry_authority"]
    )
    assert 25.82 <= coordinates[0][0] <= 26.02
    assert -18.03 <= coordinates[-1][1] <= -17.90
    review_flags = payload["features"][1:]
    assert review_flags
    assert all(feature["geometry"]["type"] == "Point" for feature in review_flags)
    assert all(feature["properties"]["production_authority"] is False for feature in review_flags)
