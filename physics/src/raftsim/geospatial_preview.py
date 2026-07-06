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


def _manifest_path(path: Path, repo_root: Path | None) -> str:
    if repo_root is None:
        return str(path)
    return str(path.resolve().relative_to(repo_root.resolve()))


def _smoothstep(edge0: np.ndarray | float, edge1: np.ndarray | float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / np.maximum(1.0e-6, np.asarray(edge1) - np.asarray(edge0)), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _preview_channel_prior(
    output_size_px: int,
    river_half_width_cm: float,
    bend_amplitude_cm: float,
    corridor_half_width_cm: float,
) -> np.ndarray:
    min_x = -5600.0
    max_x = 26000.0
    xs = np.linspace(min_x, max_x, output_size_px, dtype=np.float32)
    ys = np.linspace(-corridor_half_width_cm, corridor_half_width_cm, output_size_px, dtype=np.float32)
    x, y = np.meshgrid(xs, ys)

    primary = np.sin((x + 3800.0) * 0.00043) * bend_amplitude_cm
    secondary = np.sin((x - 600.0) * 0.00019) * bend_amplitude_cm * 0.35
    center_y = primary + secondary
    offset = np.abs(y - center_y)
    return 1.0 - _smoothstep(river_half_width_cm * 0.82, river_half_width_cm + 260.0, offset)


def build_source_imagery_masks(
    source_image_path: Path,
    output_water_mask_path: Path,
    output_vegetation_mask_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    source_description: str,
    repo_root: Path | None = None,
    output_size_px: int = 1024,
    preview_river_half_width_cm: float = 340.0,
    preview_bend_amplitude_cm: float = 300.0,
    preview_corridor_half_width_cm: float = 2750.0,
) -> None:
    """Build review-gated source-assisted water and vegetation masks for Unreal preview dressing."""

    with Image.open(source_image_path) as image:
        source = image.convert("RGBA").resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    rgba = np.asarray(source, dtype=np.float32) / 255.0
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    brightness = rgb.mean(axis=2)
    channel_range = rgb.max(axis=2) - rgb.min(axis=2)

    cloud_or_snow = (brightness > 0.78) & (channel_range < 0.12)
    excess_green = np.clip(2.0 * green - red - blue, 0.0, 1.0)
    green_dominance = np.clip(green - np.maximum(red, blue), 0.0, 1.0)
    vegetation = np.clip(excess_green * 1.85 + green_dominance * 2.20 + (green - brightness) * 1.10, 0.0, 1.0)

    blue_green = np.clip((blue + green) * 0.5 - red, 0.0, 1.0)
    muted_smooth = np.clip(0.42 - channel_range, 0.0, 1.0) * np.clip(0.70 - brightness, 0.0, 1.0)
    color_water = np.clip(blue_green * 2.00 + muted_smooth * 1.35, 0.0, 1.0)
    channel_prior = _preview_channel_prior(
        output_size_px,
        preview_river_half_width_cm,
        preview_bend_amplitude_cm,
        preview_corridor_half_width_cm,
    )

    water = np.clip(np.maximum(color_water, channel_prior * 0.78) * alpha, 0.0, 1.0)
    vegetation = np.clip(vegetation * (1.0 - channel_prior * 0.82) * alpha, 0.0, 1.0)
    water = np.where(cloud_or_snow, channel_prior * 0.50, water)
    vegetation = np.where(cloud_or_snow, vegetation * 0.35, vegetation)

    output_water_mask_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(water * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_water_mask_path)
    Image.fromarray(np.clip(vegetation * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_vegetation_mask_path)

    manifest = {
        "schema": "raftsim.source_imagery_masks.v1",
        "status": "generated_review_gated_preview_masks_not_final_segmentation",
        "source_id": source_id,
        "provider": provider,
        "source_description": source_description,
        "input_image": _manifest_path(source_image_path, repo_root),
        "outputs": {
            "water_mask": _manifest_path(output_water_mask_path, repo_root),
            "vegetation_mask": _manifest_path(output_vegetation_mask_path, repo_root),
        },
        "processing": {
            "output_size_px": output_size_px,
            "water_features": [
                "visible_color_blue_green_or_muted_smooth_water_likelihood",
                "bounded_preview_channel_prior_matching_generated_unreal_preview_geometry",
            ],
            "vegetation_features": [
                "visible_green_excess",
                "green_channel_dominance",
                "channel_prior_suppression",
            ],
            "cloud_or_snow_filter": "brightness > 0.78 and channel range < 0.12 reduces mask confidence",
            "coverage": {
                "water_mean": float(np.mean(water)),
                "vegetation_mean": float(np.mean(vegetation)),
                "cloud_or_snow_fraction": float(np.mean(cloud_or_snow)),
            },
        },
        "caveats": [
            "Masks are deterministic source-assisted preview inputs, not production water or vegetation segmentation.",
            "The water mask uses a bounded preview channel prior so the generated Unreal review map can consume the mask before final hydrography and hand-reviewed bank polygons are available.",
            "Production masks still require reviewed orthomosaics or satellite scenes, hydrography/bank alignment, cloud/shadow review, and guide/geospatial approval.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_dem_relief_preview(
    dem_path: Path,
    output_relief_png_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    repo_root: Path | None = None,
    output_size_px: int = 512,
) -> None:
    dem = _load_float_tiff(dem_path)
    _, relief = _normalized_relief(dem)
    relief_image = Image.fromarray(np.clip(relief * 255.0, 0, 255).astype(np.uint8), mode="L")
    relief_image = relief_image.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)

    output_relief_png_path.parent.mkdir(parents=True, exist_ok=True)
    relief_image.save(output_relief_png_path)

    manifest = {
        "schema": "raftsim.dem_relief_preview.v1",
        "status": "generated_preview_only_not_production_heightfield",
        "source_id": source_id,
        "provider": provider,
        "input_dem": _manifest_path(dem_path, repo_root),
        "output_relief": _manifest_path(output_relief_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "height_percentiles": "2_to_98",
            "relief": "slope_aware_normalized_grayscale_preview",
        },
        "caveats": [
            "Preview relief is sampled into procedural geometry only.",
            "Full terrain import still requires clipping, reprojection, conditioning, and Unreal heightfield or landscape import.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_single_dem_heightfield_candidate(
    dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    source_id: str,
    provider: str,
    source_description: str,
    repo_root: Path | None = None,
    output_size_px: int = 1009,
) -> None:
    """Export a review-gated 16-bit DEM sample for Unreal Landscape import tests."""

    dem = _load_float_tiff(dem_path)
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError(f"DEM sample contains no finite elevations: {dem_path}")

    fill_value = float(np.median(dem[finite]))
    dem = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(dem))
    elevation_max_m = float(np.max(dem))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((dem - elevation_min_m) / elevation_span_m, 0.0, 1.0)

    source_image = Image.fromarray(np.round(normalized * 65535.0).astype(np.uint16))
    heightfield_image = source_image.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    heightfield_image.save(output_png_path)

    manifest = {
        "schema": "raftsim.heightfield_candidate.v1",
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "source_id": source_id,
        "provider": provider,
        "source_description": source_description,
        "input_dem": _manifest_path(dem_path, repo_root),
        "output_heightfield_png": _manifest_path(output_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
            "normalization": "input DEM min/max mapped linearly to 0..65535 before resizing",
            "resize": "bilinear_to_unreal_landscape_test_size",
            "unreal_import_note": "Use the recorded elevation min/max and chosen vertical scale when testing Landscape import.",
        },
        "caveats": [
            "This is an import candidate for tool testing, not a production Unreal heightfield.",
            "The source DEM sample is not a complete reviewed corridor DEM, and still needs clipping, reprojection, void/artifact review, hydrologic conditioning, and alignment to reviewed river geometry.",
            "River channel burning, bank breaklines, boulder/bed features, access constraints, and guide review are still required before photoreal terrain promotion.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _south_fork_pilot_tile_id(row: int, column: int) -> str:
    return f"sfa_chili_bar_tile_r{row}_c{column}"


def _stitch_image_tiles(
    tile_dir: Path,
    extension: str,
    rows: int,
    columns: int,
    convert_mode: str,
    output_size_px: int,
) -> tuple[Image.Image, list[Path]]:
    inputs: list[Path] = []
    opened: dict[tuple[int, int], Image.Image] = {}
    for row in range(rows):
        for column in range(columns):
            path = tile_dir / f"{_south_fork_pilot_tile_id(row, column)}.{extension}"
            inputs.append(path)
            opened[(row, column)] = Image.open(path).convert(convert_mode)

    tile_width, tile_height = opened[(0, 0)].size
    mosaic = Image.new(convert_mode, (columns * tile_width, rows * tile_height))
    for row in range(rows):
        for column in range(columns):
            # Row zero is the southern tile band; north-up image mosaics place it at the bottom.
            mosaic.paste(opened[(row, column)], (column * tile_width, (rows - 1 - row) * tile_height))

    if mosaic.size != (output_size_px, output_size_px):
        mosaic = mosaic.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    return mosaic, inputs


def _stitch_float_dem_tiles(tile_dir: Path, rows: int, columns: int) -> tuple[np.ndarray, list[Path]]:
    inputs: list[Path] = []
    arrays: dict[tuple[int, int], np.ndarray] = {}
    for row in range(rows):
        for column in range(columns):
            path = tile_dir / f"{_south_fork_pilot_tile_id(row, column)}.tif"
            inputs.append(path)
            arrays[(row, column)] = _load_float_tiff(path)

    tile_height, tile_width = arrays[(0, 0)].shape
    mosaic = np.empty((rows * tile_height, columns * tile_width), dtype=np.float32)
    for row in range(rows):
        for column in range(columns):
            y0 = (rows - 1 - row) * tile_height
            x0 = column * tile_width
            mosaic[y0 : y0 + tile_height, x0 : x0 + tile_width] = arrays[(row, column)]
    return mosaic, inputs


def _write_heightfield_from_dem(
    dem: np.ndarray,
    output_png_path: Path,
    output_size_px: int,
) -> tuple[float, float]:
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError("DEM mosaic contains no finite elevations")
    fill_value = float(np.median(dem[finite]))
    filled = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(filled))
    elevation_max_m = float(np.max(filled))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((filled - elevation_min_m) / elevation_span_m, 0.0, 1.0)
    heightfield = Image.fromarray(np.round(normalized * 65535.0).astype(np.uint16))
    heightfield = heightfield.resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    heightfield.save(output_png_path)
    return elevation_min_m, elevation_max_m


def build_south_fork_import_pilot_derivatives(
    south_fork_root: Path,
    repo_root: Path | None = None,
    source_drape_size_px: int = 4096,
    relief_size_px: int = 2048,
    heightfield_size_px: int = 2017,
    mask_size_px: int = 2048,
) -> None:
    """Stitch downloaded South Fork pilot tiles into review-gated preview derivatives."""

    rows = 2
    columns = 2
    imagery_root = south_fork_root / "imagery/production_import_pilot"
    terrain_root = south_fork_root / "terrain/production_import_pilot"
    source_drape_path = imagery_root / f"source_drape_{source_drape_size_px}.png"
    relief_path = terrain_root / f"dem_relief_{relief_size_px}.png"
    heightfield_path = terrain_root / f"heightfield_candidate_{heightfield_size_px}.png"
    water_mask_path = imagery_root / f"water_mask_{mask_size_px}.png"
    vegetation_mask_path = imagery_root / f"vegetation_mask_{mask_size_px}.png"
    mask_manifest_path = imagery_root / "source_masks_manifest.json"
    derivative_manifest_path = south_fork_root / "production_import_pilot_derivatives_manifest.json"

    source_drape, imagery_inputs = _stitch_image_tiles(
        imagery_root / "naip_tiles",
        "png",
        rows,
        columns,
        "RGB",
        source_drape_size_px,
    )
    source_drape_path.parent.mkdir(parents=True, exist_ok=True)
    source_drape.save(source_drape_path)

    dem_mosaic, dem_inputs = _stitch_float_dem_tiles(terrain_root / "3dep_tiles", rows, columns)
    _, relief = _normalized_relief(dem_mosaic)
    relief_image = Image.fromarray(np.clip(relief * 255.0, 0, 255).astype(np.uint8), mode="L")
    if relief_image.size != (relief_size_px, relief_size_px):
        relief_image = relief_image.resize((relief_size_px, relief_size_px), Image.Resampling.BILINEAR)
    relief_path.parent.mkdir(parents=True, exist_ok=True)
    relief_image.save(relief_path)
    elevation_min_m, elevation_max_m = _write_heightfield_from_dem(dem_mosaic, heightfield_path, heightfield_size_px)

    build_source_imagery_masks(
        source_image_path=source_drape_path,
        output_water_mask_path=water_mask_path,
        output_vegetation_mask_path=vegetation_mask_path,
        output_manifest_path=mask_manifest_path,
        source_id="south_fork_production_import_pilot_source_drape_4096",
        provider="USDA/APFO NAIP ImageServer",
        source_description="South Fork American stitched 2x2 pilot NAIP source drape generated from official service export tiles.",
        repo_root=repo_root,
        output_size_px=mask_size_px,
        preview_river_half_width_cm=335.0,
        preview_bend_amplitude_cm=290.0,
        preview_corridor_half_width_cm=2750.0,
    )

    manifest = {
        "schema": "raftsim.south_fork_import_pilot_derivatives.v1",
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "source_recipe": _manifest_path(south_fork_root / "production_import_pilot.json", repo_root),
        "source_pull_manifest": _manifest_path(south_fork_root / "production_import_pilot_pull_manifest.json", repo_root),
        "inputs": {
            "naip_tiles": [_manifest_path(path, repo_root) for path in imagery_inputs],
            "dem_tiles": [_manifest_path(path, repo_root) for path in dem_inputs],
        },
        "outputs": {
            "source_drape": _manifest_path(source_drape_path, repo_root),
            "dem_relief": _manifest_path(relief_path, repo_root),
            "heightfield_candidate": _manifest_path(heightfield_path, repo_root),
            "water_mask": _manifest_path(water_mask_path, repo_root),
            "vegetation_mask": _manifest_path(vegetation_mask_path, repo_root),
            "mask_manifest": _manifest_path(mask_manifest_path, repo_root),
        },
        "processing": {
            "tile_grid": {"rows": rows, "columns": columns},
            "north_up_mosaic": "pilot tile row 1 is placed above row 0",
            "source_drape_size_px": source_drape_size_px,
            "relief_size_px": relief_size_px,
            "heightfield_size_px": heightfield_size_px,
            "mask_size_px": mask_size_px,
            "heightfield_pixel_format": "16_bit_grayscale_png",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
        },
        "caveats": [
            "This is a stitched derivative of the official-service pilot tiles, not final photoreal terrain.",
            "The DEM mosaic is not yet reprojected to a selected working CRS, hydrologically conditioned, channel-burned, or guide reviewed.",
            "The source masks are preview segmentation aids and must be reviewed against hydrography, bank polygons, seasonal imagery, and guide feedback before production use.",
        ],
    }
    derivative_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_pacuare_demshade_drape(
    nasa_truecolor_path: Path,
    southern_dem_path: Path,
    northern_dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    output_relief_png_path: Path,
    bounds: BoundsWgs84,
    selected_date: str,
    repo_root: Path | None = None,
    output_size_px: int = 512,
) -> None:
    """Blend NASA true color with DEM-derived rainforest relief for preview-only draping."""

    with Image.open(nasa_truecolor_path) as image:
        source = image.convert("RGBA").resize((output_size_px, output_size_px), Image.Resampling.BILINEAR)
    source_rgb = np.asarray(source, dtype=np.float32)[..., :3] / 255.0
    source_alpha = np.asarray(source, dtype=np.float32)[..., 3:4] / 255.0

    dem = sample_copernicus_dem(
        CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
        CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
        bounds,
        output_size_px,
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
    output_relief_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(relief * 255.0, 0, 255).astype(np.uint8), mode="L").save(output_relief_png_path)

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
            "nasa_gibs_truecolor": _manifest_path(nasa_truecolor_path, repo_root),
            "nasa_gibs_selected_date": selected_date,
            "copernicus_dem_glo30_southern_tile": _manifest_path(southern_dem_path, repo_root),
            "copernicus_dem_glo30_northern_tile": _manifest_path(northern_dem_path, repo_root),
        },
        "output": _manifest_path(output_png_path, repo_root),
        "terrain_relief_output": _manifest_path(output_relief_png_path, repo_root),
        "processing": {
            "size_px": output_size_px,
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


def build_pacuare_heightfield_candidate(
    southern_dem_path: Path,
    northern_dem_path: Path,
    output_png_path: Path,
    output_manifest_path: Path,
    bounds: BoundsWgs84,
    repo_root: Path | None = None,
    output_size_px: int = 1009,
) -> None:
    """Export a review-gated 16-bit Pacuare DEM sample for Unreal Landscape import tests."""

    dem = sample_copernicus_dem(
        CopernicusTile(southern_dem_path, south_lat=9, west_lon=-84),
        CopernicusTile(northern_dem_path, south_lat=10, west_lon=-84),
        bounds,
        output_size_px,
    )
    finite = np.isfinite(dem)
    if not finite.any():
        raise ValueError("Pacuare DEM sample contains no finite elevations")

    fill_value = float(np.median(dem[finite]))
    dem = np.where(finite, dem, fill_value).astype(np.float32)
    elevation_min_m = float(np.min(dem))
    elevation_max_m = float(np.max(dem))
    elevation_span_m = max(1.0, elevation_max_m - elevation_min_m)
    normalized = np.clip((dem - elevation_min_m) / elevation_span_m, 0.0, 1.0)
    heightfield_u16 = np.round(normalized * 65535.0).astype(np.uint16)

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(heightfield_u16).save(output_png_path)

    manifest = {
        "schema": "raftsim.pacuare_heightfield_candidate.v1",
        "status": "generated_review_gated_not_conditioned_not_production_import",
        "bounds_wgs84": {
            "min_lon": bounds.min_lon,
            "min_lat": bounds.min_lat,
            "max_lon": bounds.max_lon,
            "max_lat": bounds.max_lat,
        },
        "inputs": {
            "copernicus_dem_glo30_southern_tile": _manifest_path(southern_dem_path, repo_root),
            "copernicus_dem_glo30_northern_tile": _manifest_path(northern_dem_path, repo_root),
        },
        "output_heightfield_png": _manifest_path(output_png_path, repo_root),
        "processing": {
            "output_size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "dem_sampling": "nearest_neighbor_from_copernicus_glo30_tiles",
            "elevation_min_m": elevation_min_m,
            "elevation_max_m": elevation_max_m,
            "unreal_import_note": "Height samples are normalized to 0..65535; use the recorded elevation min/max and chosen vertical exaggeration when testing Landscape import.",
        },
        "caveats": [
            "This is an import candidate for tool testing, not a production Unreal heightfield.",
            "DEM tiles are not yet clipped to a surveyed corridor, reprojected to the chosen Costa Rica working CRS, void/artifact reviewed, hydrologically conditioned, or aligned to a reviewed river centerline.",
            "River channel burning, bank breaklines, boulder/bed features, access constraints, and guide review are still required before photoreal terrain promotion.",
        ],
    }
    output_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source-derived DEM relief and preview drapes for river environments.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    south_fork_root = repo_root / "physics/data/real_world/south_fork_american_chili_bar"
    colorado_root = repo_root / "physics/data/real_world/colorado_river_grand_canyon_rowing"
    pacuare_root = repo_root / "physics/data/real_world/pacuare_river_costa_rica"
    build_dem_relief_preview(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_sample_256.tif",
        output_relief_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_relief_preview_512.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_relief_preview_manifest.json",
        source_id="usgs_3dep_chili_bar_sample_256",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
    )
    build_dem_relief_preview(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
        output_relief_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_relief_preview_1024.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_relief_preview_manifest.json",
        source_id="usgs_3dep_chili_bar_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_single_dem_heightfield_candidate(
        dem_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_sample_512.tif",
        output_png_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png",
        output_manifest_path=south_fork_root / "terrain/usgs_3dep_chili_bar_corridor_heightfield_manifest.json",
        source_id="usgs_3dep_chili_bar_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        source_description="South Fork American Chili Bar corridor ImageServer export sample; not a complete conditioned corridor DEM.",
        repo_root=repo_root,
    )
    build_source_imagery_masks(
        source_image_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_sample_1024.png",
        output_water_mask_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_water_mask_1024.png",
        output_vegetation_mask_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_vegetation_mask_1024.png",
        output_manifest_path=south_fork_root / "imagery/usda_naip_chili_bar_corridor_masks_manifest.json",
        source_id="usda_naip_chili_bar_corridor_sample_1024",
        provider="USDA/APFO NAIP ImageServer",
        source_description="South Fork American active 1024px NAIP preview drape sample with generated preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=335.0,
        preview_bend_amplitude_cm=290.0,
        preview_corridor_half_width_cm=2750.0,
    )
    build_south_fork_import_pilot_derivatives(south_fork_root, repo_root=repo_root)
    build_dem_relief_preview(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_sample_256.tif",
        output_relief_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_relief_preview_512.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_relief_preview_manifest.json",
        source_id="usgs_3dep_lees_ferry_sample_256",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
    )
    build_dem_relief_preview(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_sample_512.tif",
        output_relief_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_relief_preview_1024.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_relief_preview_manifest.json",
        source_id="usgs_3dep_lees_ferry_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_single_dem_heightfield_candidate(
        dem_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_sample_512.tif",
        output_png_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png",
        output_manifest_path=colorado_root / "terrain/usgs_3dep_lees_ferry_corridor_heightfield_manifest.json",
        source_id="usgs_3dep_lees_ferry_corridor_sample_512",
        provider="USGS 3D Elevation Program ImageServer",
        source_description="Colorado River Lees Ferry corridor ImageServer export sample; not a complete conditioned Grand Canyon corridor DEM.",
        repo_root=repo_root,
    )
    build_source_imagery_masks(
        source_image_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_sample_1024.png",
        output_water_mask_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_water_mask_1024.png",
        output_vegetation_mask_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_vegetation_mask_1024.png",
        output_manifest_path=colorado_root / "imagery/usda_naip_lees_ferry_corridor_masks_manifest.json",
        source_id="usda_naip_lees_ferry_corridor_sample_1024",
        provider="USDA/APFO NAIP ImageServer",
        source_description="Colorado River Lees Ferry active 1024px NAIP preview drape sample with generated big-water preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=520.0 * 1.08,
        preview_bend_amplitude_cm=360.0,
        preview_corridor_half_width_cm=4300.0,
    )
    build_pacuare_demshade_drape(
        nasa_truecolor_path=pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_512.png",
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_512.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_source_drape_composite_manifest.json",
        output_relief_png_path=pacuare_root / "terrain/pacuare_dem_relief_preview_512.png",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        selected_date="2025-04-02",
        repo_root=repo_root,
    )
    build_pacuare_demshade_drape(
        nasa_truecolor_path=pacuare_root / "imagery/nasa_gibs_pacuare_truecolor_2025-04-02_1024.png",
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_source_drape_composite_manifest_1024.json",
        output_relief_png_path=pacuare_root / "terrain/pacuare_dem_relief_preview_1024.png",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        selected_date="2025-04-02",
        repo_root=repo_root,
        output_size_px=1024,
    )
    build_pacuare_heightfield_candidate(
        southern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N09_W084.tif",
        northern_dem_path=pacuare_root / "terrain/copernicus_dem_glo30_N10_W084.tif",
        output_png_path=pacuare_root / "terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png",
        output_manifest_path=pacuare_root / "terrain/pacuare_copernicus_dem_corridor_heightfield_manifest.json",
        bounds=BoundsWgs84(min_lon=-83.75, min_lat=9.72, max_lon=-83.42, max_lat=10.12),
        repo_root=repo_root,
        output_size_px=1009,
    )
    build_source_imagery_masks(
        source_image_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png",
        output_water_mask_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_water_mask_1024.png",
        output_vegetation_mask_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_vegetation_mask_1024.png",
        output_manifest_path=pacuare_root / "imagery/pacuare_nasa_gibs_2025-04-02_masks_manifest.json",
        source_id="pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024",
        provider="NASA GIBS MODIS/Terra true-color plus Copernicus DEM-derived source drape",
        source_description="Pacuare active 1024px NASA GIBS/Copernicus preview drape with generated rainfed-runnable preview-channel prior.",
        repo_root=repo_root,
        output_size_px=1024,
        preview_river_half_width_cm=305.0 * 1.05,
        preview_bend_amplitude_cm=340.0,
        preview_corridor_half_width_cm=2750.0,
    )


if __name__ == "__main__":
    main()
