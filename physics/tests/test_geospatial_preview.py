import json

import numpy as np
from PIL import Image

from raftsim.geospatial_preview import (
    build_colorado_import_pilot_derivatives,
    build_source_imagery_masks,
    build_south_fork_import_pilot_derivatives,
)


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


def test_build_south_fork_import_pilot_derivatives_stitches_tiles_and_records_manifest(tmp_path):
    south_fork_root = tmp_path / "south_fork"
    naip_dir = south_fork_root / "imagery/production_import_pilot/naip_tiles"
    dem_dir = south_fork_root / "terrain/production_import_pilot/3dep_tiles"
    naip_dir.mkdir(parents=True)
    dem_dir.mkdir(parents=True)
    (south_fork_root / "production_import_pilot.json").write_text("{}", encoding="utf-8")
    (south_fork_root / "production_import_pilot_pull_manifest.json").write_text("{}", encoding="utf-8")

    for row in range(2):
        for column in range(2):
            tile_id = f"sfa_chili_bar_tile_r{row}_c{column}"
            rgb = np.zeros((8, 8, 3), dtype=np.uint8)
            rgb[..., 0] = 40 + column * 35
            rgb[..., 1] = 120 + row * 45
            rgb[..., 2] = 65 + row * 20
            rgb[:, 3:5, 2] = 160
            Image.fromarray(rgb, mode="RGB").save(naip_dir / f"{tile_id}.png")

            dem = np.full((8, 8), 220.0 + row * 20.0 + column * 7.0, dtype=np.float32)
            dem += np.linspace(0.0, 3.0, 8, dtype=np.float32)[None, :]
            Image.fromarray(dem, mode="F").save(dem_dir / f"{tile_id}.tif")

    build_south_fork_import_pilot_derivatives(
        south_fork_root,
        repo_root=tmp_path,
        source_drape_size_px=16,
        relief_size_px=16,
        heightfield_size_px=17,
        mask_size_px=16,
    )

    manifest_path = south_fork_root / "production_import_pilot_derivatives_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_drape = Image.open(south_fork_root / "imagery/production_import_pilot/source_drape_16.png")
    heightfield = Image.open(south_fork_root / "terrain/production_import_pilot/heightfield_candidate_17.png")
    water_mask = np.asarray(Image.open(south_fork_root / "imagery/production_import_pilot/water_mask_16.png"))
    vegetation_mask = np.asarray(Image.open(south_fork_root / "imagery/production_import_pilot/vegetation_mask_16.png"))

    assert manifest["schema"] == "raftsim.south_fork_import_pilot_derivatives.v1"
    assert manifest["outputs"]["source_drape"] == "south_fork/imagery/production_import_pilot/source_drape_16.png"
    assert source_drape.size == (16, 16)
    assert heightfield.size == (17, 17)
    assert manifest["processing"]["north_up_mosaic"] == "pilot tile row 1 is placed above row 0"
    assert water_mask.mean() > 0.0
    assert vegetation_mask.mean() > 0.0


def test_build_colorado_import_pilot_derivatives_stitches_tiles_and_records_manifest(tmp_path):
    colorado_root = tmp_path / "colorado"
    naip_dir = colorado_root / "imagery/production_import_pilot/naip_tiles"
    dem_dir = colorado_root / "terrain/production_import_pilot/3dep_tiles"
    naip_dir.mkdir(parents=True)
    dem_dir.mkdir(parents=True)
    (colorado_root / "production_import_pilot.json").write_text("{}", encoding="utf-8")
    (colorado_root / "production_import_pilot_pull_manifest.json").write_text("{}", encoding="utf-8")

    for row in range(2):
        for column in range(2):
            tile_id = f"colorado_lees_ferry_tile_r{row}_c{column}"
            rgb = np.zeros((8, 8, 3), dtype=np.uint8)
            rgb[..., 0] = 105 + column * 22
            rgb[..., 1] = 95 + row * 25
            rgb[..., 2] = 70 + column * 15
            rgb[:, 2:6, 2] = 150
            Image.fromarray(rgb, mode="RGB").save(naip_dir / f"{tile_id}.png")

            dem = np.full((8, 8), 920.0 + row * 30.0 + column * 11.0, dtype=np.float32)
            dem += np.linspace(0.0, 5.0, 8, dtype=np.float32)[:, None]
            Image.fromarray(dem, mode="F").save(dem_dir / f"{tile_id}.tif")

    build_colorado_import_pilot_derivatives(
        colorado_root,
        repo_root=tmp_path,
        source_drape_size_px=16,
        relief_size_px=16,
        heightfield_size_px=17,
        mask_size_px=16,
    )

    manifest_path = colorado_root / "production_import_pilot_derivatives_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_drape = Image.open(colorado_root / "imagery/production_import_pilot/source_drape_16.png")
    heightfield = Image.open(colorado_root / "terrain/production_import_pilot/heightfield_candidate_17.png")
    water_mask = np.asarray(Image.open(colorado_root / "imagery/production_import_pilot/water_mask_16.png"))
    vegetation_mask = np.asarray(Image.open(colorado_root / "imagery/production_import_pilot/vegetation_mask_16.png"))

    assert manifest["schema"] == "raftsim.colorado_import_pilot_derivatives.v1"
    assert manifest["outputs"]["source_drape"] == "colorado/imagery/production_import_pilot/source_drape_16.png"
    assert source_drape.size == (16, 16)
    assert heightfield.size == (17, 17)
    assert manifest["processing"]["north_up_mosaic"] == "pilot tile row 1 is placed above row 0"
    assert "guide/oarsman" in manifest["caveats"][1]
    assert water_mask.mean() > 0.0
    assert vegetation_mask.mean() > 0.0
