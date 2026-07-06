"""Small deterministic geospatial preview helpers for source-derived Unreal drapes."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class BoundsWgs84:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


@dataclass(frozen=True)
class CopernicusTile:
    path: Path
    south_lat: int
    west_lon: int

    @property
    def north_lat(self) -> int:
        return self.south_lat + 1

    @property
    def east_lon(self) -> int:
        return self.west_lon + 1


def _load_float_tiff(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image, dtype=np.float32)


def _sample_tile_nearest(tile: CopernicusTile, data: np.ndarray, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    height, width = data.shape
    col = np.clip(((lon - tile.west_lon) / (tile.east_lon - tile.west_lon) * (width - 1)).round(), 0, width - 1)
    row = np.clip(((tile.north_lat - lat) / (tile.north_lat - tile.south_lat) * (height - 1)).round(), 0, height - 1)
    return data[row.astype(np.int32), col.astype(np.int32)]


def sample_copernicus_dem(
    southern_tile: CopernicusTile,
    northern_tile: CopernicusTile,
    bounds: BoundsWgs84,
    size: int,
) -> np.ndarray:
    """Sample the two Pacuare GLO-30 tiles into a small north-up preview grid."""

    south_data = _load_float_tiff(southern_tile.path)
    north_data = _load_float_tiff(northern_tile.path)

    xs = np.linspace(bounds.min_lon, bounds.max_lon, size, dtype=np.float32)
    ys = np.linspace(bounds.max_lat, bounds.min_lat, size, dtype=np.float32)
    lon, lat = np.meshgrid(xs, ys)

    sampled = np.empty((size, size), dtype=np.float32)
    north_mask = lat >= float(northern_tile.south_lat)
    sampled[north_mask] = _sample_tile_nearest(northern_tile, north_data, lon[north_mask], lat[north_mask])
    sampled[~north_mask] = _sample_tile_nearest(southern_tile, south_data, lon[~north_mask], lat[~north_mask])
    return sampled


def _normalized_relief(dem: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    finite = np.isfinite(dem)
    low, high = np.percentile(dem[finite], [2.0, 98.0])
    height = np.clip((dem - low) / max(1.0, high - low), 0.0, 1.0)

    grad_y, grad_x = np.gradient(dem)
    slope = np.sqrt(grad_x * grad_x + grad_y * grad_y)
    slope_high = np.percentile(slope[np.isfinite(slope)], 97.0)
    slope_norm = np.clip(slope / max(1.0, slope_high), 0.0, 1.0)

    light = np.clip(0.62 + (-grad_x * 0.0025) + (-grad_y * 0.0035), 0.32, 0.94)
    relief = np.clip(light * (0.82 + height * 0.24) - slope_norm * 0.10, 0.0, 1.0)
    return height, relief


def build_pacuare_demshade_drape(
    nasa_truecolor_path: Path,
    southern_dem_path: Path,
    northern_dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    bounds: BoundsWgs84,
    selected_date: str,
    repo_root: Path | None = None,
) -> None:
    """Blend NASA true color with DEM-derived rainforest relief for preview-only draping."""

    with Image.open(nasa_truecolor_path) as image:
        source = image.convert("RGBA").resize((512, 512), Image.Resampling.BILINEAR)
    source_rgb = np.asarray(source, dtype=np.float32)[..., :3] / 255.0
    source_alpha = np.asarray(source, dtype=np.float32)[..., 3:4] / 255.0

    dem = sample_copernicus_dem(
        CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
        CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
        bounds,
        512,
    )
    height, relief = _normalized_relief(dem)

    brightness = source_rgb.mean(axis=2)
    color_range = source_rgb.max(axis=2) - source_rgb.min(axis=2)
    cloud_mask = (brightness > 0.70) & (color_range < 0.16)

    forest_low = np.array([0.05, 0.20, 0.08], dtype=np.float32)
    forest_high = np.array([0.20, 0.36, 0.13], dtype=np.float32)
    forest = forest_low + (forest_high - forest_low) * relief[..., None]
    ridge_warmth = np.array([0.09, 0.06, 0.02], dtype=np.float32) * height[..., None]
    dem_rgb = np.clip(forest + ridge_warmth, 0.0, 1.0)

    non_cloud = np.clip(source_rgb * 0.45 + dem_rgb * 0.55, 0.0, 1.0)
    blended = np.where(cloud_mask[..., None], dem_rgb, non_cloud)
    rgba = np.dstack((blended, source_alpha))

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(rgba * 255.0, 0, 255).astype(np.uint8), mode="RGBA").save(output_png_path)

    def manifest_path(path: Path) -> str:
        if repo_root is None:
            return str(path)
        return str(path.resolve().relative_to(repo_root.resolve()))

    manifest = {
        "schema": "raftsim.pacuare_source_drape_composite.v1",
        "status": "generated_preview_only_not_production_photoreal",
        "bounds_wgs84": {
            "min_lon": bounds.min_lon,
            "min_lat": bounds.min_lat,
            "max_lon": bounds.max_lon,
            "max_lat": bounds.max_lat,
        },
        "inputs": {
            "nasa_gibs_truecolor": manifest_path(nasa_truecolor_path),
            "nasa_gibs_selected_date": selected_date,
            "copernicus_dem_glo30_southern_tile": manifest_path(southern_dem_path),
            "copernicus_dem_glo30_northern_tile": manifest_path(northern_dem_path),
        },
        "output": manifest_path(output_png_path),
        "processing": {
            "size_px": 512,
            "dem_sampling": "nearest_neighbor_from_copernicus_glo30_tiles",
            "cloud_mask": "truecolor brightness > 0.70 and channel range < 0.16",
            "blend": "non_cloud = 45% NASA truecolor + 55% DEM rainforest relief; cloud = DEM rainforest relief",
        },
        "caveats": [
            "Preview composite is a deterministic source-derived drape, not a production orthomosaic.",
            "Cloud-filled areas are DEM-derived rainforest relief placeholders and must be replaced by higher-resolution cloud-screened imagery before photoreal approval.",
            "DEM tiles are not yet clipped, reprojected, hydrologically conditioned, or imported as Unreal heightfields.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Pacuare source-derived DEM-shaded preview drape.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    pacuare_root = repo_root / "physics/data/real_world/pacuare_river_costa_rica"
    build_pacuare_demshade_drape(
        nasa_truecolor_path=pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_512.png",
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_512.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_source_drape_composite_manifest.json",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        selected_date="2025-04-02",
        repo_root=repo_root,
    )


if __name__ == "__main__":
    main()
