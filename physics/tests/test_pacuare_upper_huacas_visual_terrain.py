from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.pacuare_upper_huacas_visual_terrain import (
    DEFAULT_OUTPUT_RELATIVE,
    SCHEMA,
    build_pacuare_upper_huacas_visual_terrain,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_upper_huacas_visual_terrain_is_reach_local_bounded_and_aligned(tmp_path: Path):
    output_dir = tmp_path / "upper_huacas_visual"
    manifest = build_pacuare_upper_huacas_visual_terrain(
        REPO_ROOT,
        output_dir=output_dir,
        output_size_px=257,
    )

    assert manifest["schema"] == SCHEMA
    assert manifest["landscape"]["horizontal_span_x_m"] == 600.0
    assert manifest["landscape"]["horizontal_span_y_m"] == 78.0
    assert manifest["procedural_infill"]["maximum_absolute_relief_m"] <= 0.38
    assert manifest["procedural_infill"]["maximum_protected_channel_change_m"] == 0.0
    assert manifest["procedural_infill"]["maximum_map_edge_change_m"] == 0.0
    assert (
        manifest["alignment"]["maximum_static_to_runtime_centerline_surface_error_m"]
        < 1e-9
    )
    assert manifest["honesty"]["production_promoted"] is False

    heightfield = np.asarray(
        Image.open(output_dir / "upper_huacas_conditioned_heightfield_257.png")
    )
    centerline = json.loads(
        (output_dir / "upper_huacas_local_centerline.json").read_text(encoding="utf-8")
    )
    coordinate_map = json.loads(
        (output_dir / "upper_huacas_runtime_coordinate_map.json").read_text(
            encoding="utf-8"
        )
    )
    assert heightfield.shape == (257, 257)
    assert heightfield.min() == 0
    assert heightfield.max() == 65535
    assert len(centerline["points"]) == 301
    assert centerline["points"][0]["unreal_local_cm"] == [0.0, 3900.0]
    assert centerline["points"][-1]["unreal_local_cm"] == [60000.0, 3900.0]
    assert coordinate_map["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert (
        coordinate_map["vertical_datum_m"]
        == manifest["landscape"]["runtime_vertical_datum_m"]
    )
    assert coordinate_map["points"][0] == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert coordinate_map["points"][-1] == [600.0, 600.0, 0.0, 0.0, 1.0]


def test_committed_upper_huacas_visual_terrain_matches_generator(tmp_path: Path):
    generated_dir = tmp_path / "generated"
    build_pacuare_upper_huacas_visual_terrain(REPO_ROOT, output_dir=generated_dir)
    committed_dir = REPO_ROOT / DEFAULT_OUTPUT_RELATIVE
    for name in (
        "upper_huacas_conditioned_heightfield_1009.png",
        "upper_huacas_local_centerline.json",
        "upper_huacas_runtime_coordinate_map.json",
    ):
        assert (committed_dir / name).read_bytes() == (
            generated_dir / name
        ).read_bytes()

    committed_manifest = json.loads(
        (committed_dir / "upper_huacas_visual_terrain_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    generated_manifest = json.loads(
        (generated_dir / "upper_huacas_visual_terrain_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    for manifest in (committed_manifest, generated_manifest):
        manifest["outputs"]["heightfield"] = Path(
            manifest["outputs"]["heightfield"]
        ).name
        manifest["outputs"]["local_centerline"] = Path(
            manifest["outputs"]["local_centerline"]
        ).name
        manifest["outputs"]["runtime_coordinate_map"] = Path(
            manifest["outputs"]["runtime_coordinate_map"]
        ).name
    assert committed_manifest == generated_manifest


def test_upper_huacas_runnable_review_is_hash_locked_and_honest():
    review_path = (
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "pacuare_upper_huacas_reach_local_runnable_v1_review.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))

    assert review["status"] == (
        "accepted_reference_runnable_photoreal_promotion_rejected"
    )
    assert review["runnable_decision"]["listed_as_runnable_river"] is True
    assert review["runnable_decision"]["reference_runnable"] is True
    assert review["runnable_decision"]["production_promoted"] is False
    assert (
        review["coordinate_contract"][
            "maximum_static_to_runtime_centerline_surface_error_m"
        ]
        == 0.0
    )
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        if artifact.get("hash_locked", True):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
