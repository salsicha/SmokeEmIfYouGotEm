import json

import numpy as np
from PIL import Image

from raftsim.geospatial_preview import build_source_imagery_masks


def test_build_source_imagery_masks_records_outputs_and_coverage(tmp_path):
    source_path = tmp_path / "source.png"
    water_path = tmp_path / "water.png"
    vegetation_path = tmp_path / "vegetation.png"
    manifest_path = tmp_path / "manifest.json"

    image = np.zeros((32, 32, 4), dtype=np.uint8)
    image[..., 0] = 50
    image[..., 1] = 145
    image[..., 2] = 45
    image[..., 3] = 255
    image[:, 13:19, 0] = 35
    image[:, 13:19, 1] = 120
    image[:, 13:19, 2] = 160
    Image.fromarray(image, mode="RGBA").save(source_path)

    build_source_imagery_masks(
        source_image_path=source_path,
        output_water_mask_path=water_path,
        output_vegetation_mask_path=vegetation_path,
        output_manifest_path=manifest_path,
        source_id="synthetic_source",
        provider="unit test",
        source_description="synthetic green banks with blue-green channel",
        repo_root=tmp_path,
        output_size_px=32,
        preview_river_half_width_cm=150.0,
        preview_bend_amplitude_cm=0.0,
        preview_corridor_half_width_cm=800.0,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    water = np.asarray(Image.open(water_path), dtype=np.float32) / 255.0
    vegetation = np.asarray(Image.open(vegetation_path), dtype=np.float32) / 255.0

    assert manifest["schema"] == "raftsim.source_imagery_masks.v1"
    assert manifest["outputs"]["water_mask"] == "water.png"
    assert manifest["outputs"]["vegetation_mask"] == "vegetation.png"
    assert manifest["processing"]["coverage"]["water_mean"] > 0.0
    assert manifest["processing"]["coverage"]["vegetation_mean"] > 0.0
    assert water[:, 16].mean() > water[:, 2].mean()
    assert vegetation[:, 2].mean() > vegetation[:, 16].mean()
