import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.colorado_production_corridor import (
    CORRIDOR_RELATIVE_ROOT,
    LANDSCAPE_SIZE,
    STATION_END_M,
    STATION_START_M,
    build_colorado_lees_ferry_production_corridor,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_colorado_production_corridor_is_source_scale_aligned_and_review_gated(tmp_path):
    # Regenerate into tmp so committed corridor artifacts are never rewritten
    # mid-suite; recorded manifest paths stay canonical, so map them into the
    # tmp output root when reading generated files.
    manifest = build_colorado_lees_ferry_production_corridor(REPO_ROOT, output_dir=tmp_path)

    def generated(relative_path: str) -> Path:
        return tmp_path / Path(relative_path).relative_to(CORRIDOR_RELATIVE_ROOT)

    centerline = json.loads((tmp_path / "centerline_local.json").read_text(encoding="utf-8"))

    assert manifest["status"] == (
        "official_source_attached_physical_landscape_inputs_generated_review_gated"
    )
    assert manifest["production_promoted"] is False
    assert manifest["unreal_landscape"]["heightfield_size_px"] == [LANDSCAPE_SIZE, LANDSCAPE_SIZE]
    assert manifest["unreal_landscape"]["relief_m"] > 100.0
    assert manifest["unreal_landscape"]["channel_conditioning"]["policy"].startswith("none_")
    assert len(manifest["source_artifacts"]["tile_hashes"]) == 8
    assert len(manifest["review_boundaries"]["blocked_now"]) == 4

    heightfield = Image.open(generated(manifest["unreal_landscape"]["heightfield"]))
    assert heightfield.size == (LANDSCAPE_SIZE, LANDSCAPE_SIZE)
    assert heightfield.mode in {"I", "I;16"}
    assert len(centerline["points"]) > 500
    assert centerline["source_station_range_m"] == [STATION_START_M, STATION_END_M]
    assert centerline["station_range_m"] == [0.0, STATION_END_M - STATION_START_M]
    span_x, span_y = manifest["ground_span_m_approx"]
    for point in centerline["points"]:
        x_cm, y_cm = point["unreal_local_cm"]
        assert 0.0 <= x_cm <= span_x * 100.0
        assert 0.0 <= y_cm <= span_y * 100.0
    for path in manifest["derived_artifacts"].values():
        assert generated(path).is_file()

    raw_albedo = np.asarray(
        Image.open(generated(manifest["derived_artifacts"]["source_albedo"])).convert("RGB"),
        dtype=np.float32,
    ) / 255.0
    terrain_albedo = np.asarray(
        Image.open(generated(manifest["derived_artifacts"]["terrain_albedo"])).convert("RGB"),
        dtype=np.float32,
    ) / 255.0
    raw_luma = raw_albedo @ np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    terrain_luma = terrain_albedo @ np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    assert float(np.percentile(terrain_luma, 1.0)) >= 0.19
    assert float(np.percentile(terrain_luma, 1.0)) > float(np.percentile(raw_luma, 1.0))
    assert manifest["terrain_albedo_conditioning"]["authority"].startswith("visual_render_derivative_only")
