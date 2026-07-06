from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.production_imports import PULL_MANIFEST_SCHEMA_VERSION, pull_production_import_pilot


def test_pull_production_import_pilot_records_existing_tiles_without_network(tmp_path):
    repo_root = tmp_path
    river_root = repo_root / "physics/data/real_world/test_river"
    recipe_path = river_root / "production_import_pilot.json"
    dem_path = river_root / "terrain/production_import_pilot/3dep_tiles/test_tile.tif"
    image_path = river_root / "imagery/production_import_pilot/naip_tiles/test_tile.png"
    manifest_path = river_root / "production_import_pilot_pull_manifest.json"

    dem_path.parent.mkdir(parents=True)
    image_path.parent.mkdir(parents=True)
    Image.fromarray(np.ones((4, 4), dtype=np.float32), mode="F").save(dem_path)
    Image.fromarray(np.full((8, 8, 3), 128, dtype=np.uint8), mode="RGB").save(image_path)
    recipe_path.parent.mkdir(parents=True, exist_ok=True)
    recipe_path.write_text(
        """
{
  "river_id": "test_river",
  "section_id": "test_section",
  "tile_grid": {
    "tiles": [
      {
        "tile_id": "test_tile",
        "download_specs": {
          "3dep_dem_export": {
            "provider": "USGS 3D Elevation Program ImageServer",
            "url": "https://example.invalid/dem.tif",
            "target_artifact": "terrain/production_import_pilot/3dep_tiles/test_tile.tif",
            "size_px": [4, 4]
          },
          "naip_export": {
            "provider": "USDA/APFO NAIP ImageServer",
            "url": "https://example.invalid/naip.png",
            "target_artifact": "imagery/production_import_pilot/naip_tiles/test_tile.png",
            "size_px": [8, 8]
          }
        }
      }
    ]
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = pull_production_import_pilot(
        recipe_path=recipe_path,
        river_root=river_root,
        repo_root=repo_root,
        output_manifest_path=manifest_path,
        reuse_existing=True,
    )

    downloads = {entry["download_kind"]: entry for entry in manifest["downloads"]}
    assert manifest["schema"] == PULL_MANIFEST_SCHEMA_VERSION
    assert manifest["download_count"] == 2
    assert manifest_path.exists()
    assert downloads["3dep_dem_export"]["actual_size_px"] == [4, 4]
    assert downloads["3dep_dem_export"]["image_mode"] == "F"
    assert downloads["naip_export"]["actual_size_px"] == [8, 8]
    assert downloads["naip_export"]["image_mode"] == "RGB"
    assert all(Path(entry["path"]).is_relative_to("physics/data/real_world/test_river") for entry in downloads.values())
