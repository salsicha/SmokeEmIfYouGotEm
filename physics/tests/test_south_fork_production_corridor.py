from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_production_corridor import (
    CORRIDOR_RELATIVE_ROOT,
    DEM_SHA256,
    NAIP_SHA256,
    build_south_fork_chili_bar_production_corridor,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_south_fork_production_corridor_is_official_physical_and_reproducible():
    manifest = build_south_fork_chili_bar_production_corridor(REPO_ROOT)
    corridor_root = REPO_ROOT / CORRIDOR_RELATIVE_ROOT

    assert manifest["status"] == (
        "official_source_attached_physical_landscape_inputs_generated_review_gated"
    )
    assert manifest["production_promoted"] is False
    assert manifest["reach_id"] == "chili_bar_0_2500m"
    assert manifest["ground_span_m_approx"][0] > 2_400.0
    assert manifest["ground_span_m_approx"][1] > 1_690.0

    landscape = manifest["unreal_landscape"]
    assert landscape["heightfield_size_px"] == [2017, 2017]
    assert landscape["relief_m"] > 380.0
    assert 70.0 < landscape["z_scale_cm"] < 80.0
    assert 80.0 < landscape["xy_scale_cm_per_quad"][1] < 90.0
    assert 115.0 < landscape["xy_scale_cm_per_quad"][0] < 125.0

    sources = manifest["source_artifacts"]
    assert sources["dem"]["catalog_object_id"] == 131308
    assert sources["dem"]["vertical_datum"] == "NAVD 88"
    assert sources["dem"]["export_request"]["lock_raster_ids"] == [131308]
    assert "Public Domain" in sources["dem"]["rights"]
    assert sources["aerial"]["catalog_object_id"] == 1828092
    assert sources["aerial"]["acquisition_date"] == "2022-07-20"
    assert sources["aerial"]["export_request"]["lock_raster_ids"] == [1828092]
    assert "Public Domain" in sources["aerial"]["rights"]
    assert _sha256(REPO_ROOT / sources["dem"]["path"]) == DEM_SHA256
    assert _sha256(REPO_ROOT / sources["aerial"]["path"]) == NAIP_SHA256

    derived = manifest["derived_artifacts"]
    for artifact in derived.values():
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]

    heightfield = np.asarray(Image.open(REPO_ROOT / derived["heightfield"]["path"]))
    assert heightfield.shape == (2017, 2017)
    assert int(heightfield.min()) < 1000
    assert int(heightfield.max()) > 64000

    centerline = json.loads(
        (REPO_ROOT / derived["local_centerline"]["path"]).read_text(encoding="utf-8")
    )
    assert centerline["status"] == "source_aligned_review_gated_not_gameplay_authority"
    assert centerline["station_range_m"][1] >= 2450.0
    assert len(centerline["points"]) >= 40
    for point in centerline["points"]:
        assert all(0.0 <= value <= 1.0 for value in point["normalized_xy"])

    assert len(manifest["review_gates"]) == 5
