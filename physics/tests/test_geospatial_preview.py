import json

import numpy as np
from PIL import Image

from raftsim.geospatial_preview import (
    build_colorado_import_pilot_derivatives,
    build_pacuare_import_pilot_derivatives,
    build_source_imagery_masks,
    build_south_fork_import_pilot_derivatives,
    build_south_fork_production_hydrography_drafts,
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


def test_build_south_fork_production_hydrography_drafts_records_review_gates(tmp_path):
    south_fork_root = tmp_path / "south_fork"
    hydro_root = south_fork_root / "hydrography"
    hydro_root.mkdir(parents=True)

    stationing = {
        "local_transform": {"station_axis": "downstream_from_inferred_upstream_endpoint_meters"},
        "summary": {
            "length_m_geodesic_vertices": 200.0,
            "source_length_km_nhd_sum": 0.2,
            "station_sample_count": 3,
            "vertex_count": 3,
        },
        "vertices": [
            {"lon": -120.0, "lat": 38.0},
            {"lon": -120.001, "lat": 38.001},
            {"lon": -120.002, "lat": 38.002},
        ],
        "station_samples": [
            {"station_m": 0.0},
            {"station_m": 100.0},
            {"station_m": 200.0},
        ],
    }
    cross_sections = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-120.0, 37.999], [-120.0, 38.0], [-120.0, 38.001]],
                },
                "properties": {"cross_section_id": "xs_000", "half_width_m": 80.0, "station_m": 0.0},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-120.002, 38.001], [-120.002, 38.002], [-120.002, 38.003]],
                },
                "properties": {"cross_section_id": "xs_001", "half_width_m": 80.0, "station_m": 200.0},
            },
        ],
    }
    mainstem_manifest = {"derivation": {"orientation": "east_to_west_review_orientation"}}
    (hydro_root / "nhd_hu8_18020129_mainstem_stationing_candidate.json").write_text(
        json.dumps(stationing), encoding="utf-8"
    )
    (hydro_root / "nhd_hu8_18020129_cross_section_seed_candidates.geojson").write_text(
        json.dumps(cross_sections), encoding="utf-8"
    )
    (hydro_root / "nhd_hu8_18020129_mainstem_candidate_manifest.json").write_text(
        json.dumps(mainstem_manifest), encoding="utf-8"
    )

    build_south_fork_production_hydrography_drafts(south_fork_root, repo_root=tmp_path)

    output_root = hydro_root / "production_import_pilot"
    manifest = json.loads((output_root / "hydrography_draft_manifest.json").read_text(encoding="utf-8"))
    centerline = json.loads((output_root / "centerline.geojson").read_text(encoding="utf-8"))
    banks = json.loads((output_root / "banks.geojson").read_text(encoding="utf-8"))
    generated_cross_sections = json.loads((output_root / "cross_sections.geojson").read_text(encoding="utf-8"))

    assert manifest["schema"] == "raftsim.south_fork_production_hydrography_drafts.manifest.v1"
    assert manifest["status"] == "draft_hydrography_artifacts_generated_review_required_not_production_authority"
    assert manifest["summary"]["centerline_vertex_count"] == 3
    assert manifest["summary"]["cross_section_count"] == 2
    assert manifest["outputs"]["centerline"] == "south_fork/hydrography/production_import_pilot/centerline.geojson"
    assert centerline["features"][0]["properties"]["status"] == (
        "draft_from_nhd_mainstem_candidate_review_gated_not_final_centerline"
    )
    assert len(banks["features"]) == 2
    assert banks["features"][0]["properties"]["status"] == "draft_offset_line_not_reviewed_bank"
    assert generated_cross_sections["features"][0]["properties"]["status"] == (
        "draft_production_import_cross_section_review_line_not_solver_section"
    )


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


def test_build_pacuare_import_pilot_derivatives_records_coarse_seed_caveats(tmp_path):
    pacuare_root = tmp_path / "pacuare"
    imagery_dir = pacuare_root / "imagery"
    terrain_dir = pacuare_root / "terrain"
    imagery_dir.mkdir(parents=True)
    terrain_dir.mkdir(parents=True)
    (pacuare_root / "production_import_pilot.json").write_text("{}", encoding="utf-8")

    truecolor = np.zeros((16, 16, 4), dtype=np.uint8)
    truecolor[..., 0] = 34
    truecolor[..., 1] = 92
    truecolor[..., 2] = 42
    truecolor[..., 3] = 255
    truecolor[4:9, :, 1] = 120
    truecolor[:, 7:9, 2] = 150
    Image.fromarray(truecolor, mode="RGBA").save(imagery_dir / "nasa_gibs_pacuare_truecolor_2025-04-02_1024.png")

    southern_dem = np.linspace(120.0, 360.0, 16 * 16, dtype=np.float32).reshape(16, 16)
    northern_dem = np.linspace(260.0, 620.0, 16 * 16, dtype=np.float32).reshape(16, 16)
    Image.fromarray(southern_dem, mode="F").save(terrain_dir / "copernicus_dem_glo30_N09_W084.tif")
    Image.fromarray(northern_dem, mode="F").save(terrain_dir / "copernicus_dem_glo30_N10_W084.tif")

    build_pacuare_import_pilot_derivatives(
        pacuare_root,
        repo_root=tmp_path,
        source_drape_size_px=16,
        relief_size_px=12,
        heightfield_size_px=17,
        mask_size_px=16,
    )

    manifest_path = pacuare_root / "production_import_pilot_derivatives_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_drape = Image.open(pacuare_root / "imagery/production_import_pilot/source_drape_16.png")
    relief = Image.open(pacuare_root / "terrain/production_import_pilot/dem_relief_12.png")
    heightfield = Image.open(pacuare_root / "terrain/production_import_pilot/heightfield_candidate_17.png")
    water_mask = np.asarray(Image.open(pacuare_root / "imagery/production_import_pilot/water_mask_16.png"))

    assert manifest["schema"] == "raftsim.pacuare_import_pilot_derivatives.v1"
    assert manifest["status"] == "generated_review_gated_from_coarse_preview_seeds_not_production_import"
    assert manifest["outputs"]["source_drape"] == "pacuare/imagery/production_import_pilot/source_drape_16.png"
    assert source_drape.size == (16, 16)
    assert relief.size == (12, 12)
    assert heightfield.size == (17, 17)
    assert "coarse and partly cloudy" in " ".join(manifest["caveats"])
    assert water_mask.mean() > 0.0
