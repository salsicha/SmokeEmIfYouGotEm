from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.chilko_lava_canyon_visual_terrain import (
    SCHEMA,
    build_chilko_lava_canyon_visual_terrain,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_build_chilko_lava_canyon_visual_terrain(tmp_path: Path) -> None:
    manifest = build_chilko_lava_canyon_visual_terrain(
        REPO_ROOT, output_dir=tmp_path, output_size_px=257
    )

    assert manifest["schema"] == SCHEMA
    assert manifest["reference_flow_band"] == "median_runnable"
    assert manifest["landscape"]["horizontal_span_x_m"] == 600.0
    assert manifest["landscape"]["horizontal_span_y_m"] == 600.0
    assert manifest["landscape"]["source_solver_span_y_m"] == 80.0
    assert manifest["procedural_infill"]["protected_solver_strip_change_m"] == 0.0
    assert manifest["procedural_infill"]["maximum_official_dem_edge_correction_m"] < 3.0
    assert manifest["procedural_infill"]["maximum_procedural_microrelief_m"] <= 1.35
    assert manifest["alignment"][
        "maximum_static_to_runtime_centerline_surface_error_m"
    ] < 1.0e-9
    assert manifest["honesty"]["production_promoted"] is False

    image = np.asarray(Image.open(tmp_path / "lava_canyon_conditioned_heightfield_257.png"))
    assert image.shape == (257, 257)
    assert image.dtype == np.uint16
    assert int(image.min()) == 0
    assert int(image.max()) == 65535

    centerline = json.loads(
        (tmp_path / "lava_canyon_local_centerline.json").read_text(encoding="utf-8")
    )
    assert len(centerline["points"]) == 301
    assert centerline["points"][0]["unreal_local_cm"] == [0.0, 30000.0]
    assert centerline["points"][-1]["unreal_local_cm"] == [60000.0, 30000.0]
    assert centerline["points"][0]["corridor_station_m"] == 8730.0
    assert centerline["points"][-1]["corridor_station_m"] == 9330.0

    coordinate_map = json.loads(
        (tmp_path / "lava_canyon_runtime_coordinate_map.json").read_text(
            encoding="utf-8"
        )
    )
    assert coordinate_map["points"][0] == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert coordinate_map["points"][-1] == [600.0, 600.0, 0.0, 0.0, 1.0]
    assert coordinate_map["vertical_datum_m"] > 1000.0
