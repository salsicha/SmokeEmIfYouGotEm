"""Create one Cartesian terrain authority for the corrected full South Fork.

No bank smoothing, invented S-bends, or procedural boulders are applied. This
is source terrain, not a hydraulic bed: hydro-flattened pixels stay unknown.
"""
from pathlib import Path
import sys
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.features import rasterize
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from pyproj import Transformer
from build_south_fork_survey_reconstruction import read_breaklines, FT_US_TO_M, validated_horizontal_crs

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = BASE / 'full_reach'
CELL = 2.0


def main():
    selections = json.loads((BASE / 'full-reach-lidar-tile-selection.json').read_text())
    tiles = json.loads((BASE / 'sources/dem/full-reach-downloads.json').read_text())
    expected = {s['attributes']['Tile_ID'] for s in selections}
    if {t['tile_id'] for t in tiles} != expected:
        raise ValueError('Incomplete survey intake: refusing a partial full-reach reconstruction')
    route_data = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())
    route_f = next(f for f in route_data['features'] if f['geometry']['type'] == 'LineString')
    project = Transformer.from_crs(4326, 32610, always_xy=True)
    route = transform(project.transform, shape(route_f['geometry']))
    corridor = route.buffer(240)
    xmin, ymin, xmax, ymax = corridor.bounds
    xmin, ymin = np.floor([xmin/CELL, ymin/CELL])*CELL
    xmax, ymax = np.ceil([xmax/CELL, ymax/CELL])*CELL
    width, height = int((xmax-xmin)/CELL), int((ymax-ymin)/CELL)
    affine = from_origin(xmin, ymax, CELL, CELL)
    surface = np.full((height,width), np.nan, dtype=np.float32)
    for index, tile in enumerate(tiles):
        path = BASE / 'sources/dem' / tile['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != tile['sha256']:
            raise ValueError(f'Source hash mismatch: {tile["file"]}')
        with rasterio.open(path) as src:
            source_horizontal_crs = validated_horizontal_crs(src)
            data = src.read(1).astype(np.float32)
            data[data == src.nodata] = np.nan
            data *= FT_US_TO_M
            reproject(data, surface, src_transform=src.transform, src_crs=source_horizontal_crs,
                src_nodata=np.nan, dst_transform=affine, dst_crs='EPSG:32610',
                dst_nodata=np.nan, init_dest_nodata=False, resampling=Resampling.bilinear)
        print(f'Reprojected {index+1}/{len(tiles)}', flush=True)
    coverage = rasterize([(mapping(corridor), 1)], out_shape=surface.shape,
                         transform=affine, dtype='uint8').astype(bool)
    missing = coverage & ~np.isfinite(surface)
    if missing.any():
        raise ValueError(f'{int(missing.sum())} corridor samples have no captured elevation; no invented fill permitted')
    water_geoms = [geom.intersection(corridor) for _, geom in read_breaklines() if geom.intersects(corridor)]
    water = unary_union(water_geoms)
    unknown_bed = rasterize([(mapping(water), 1)], out_shape=surface.shape,
                           transform=affine, dtype='uint8')
    surface[~coverage] = np.nan
    unknown_bed[~coverage] = 255
    OUT.mkdir(exist_ok=True)
    profile = dict(driver='GTiff', width=width, height=height, count=1,
        dtype='float32', crs='EPSG:32610', transform=affine, nodata=np.nan,
        tiled=True, compress='deflate')
    surface_path = OUT / 'captured_surface_navd88_m.tif'
    with rasterio.open(surface_path, 'w', **profile) as dst:
        dst.write(surface, 1); dst.set_band_unit(1, 'metre')
        dst.update_tags(vertical_datum='NAVD88', water_pixels='NOT_BATHYMETRY')
    mask_path = OUT / 'unknown_submerged_bed_mask.tif'
    with rasterio.open(mask_path, 'w', **dict(profile, dtype='uint8', nodata=255)) as dst:
        dst.write(unknown_bed, 1)
    # Source profile for geographic/rapid review, not a fitted water solution.
    stations = np.linspace(0, route.length, int(np.ceil(route.length/2))+1)
    points = np.array([route.interpolate(s).coords[0] for s in stations])
    col = np.floor((points[:,0]-xmin)/CELL).astype(int)
    row = np.floor((ymax-points[:,1])/CELL).astype(int)
    profile_source = surface[row,col]
    profile_wet = unknown_bed[row,col] == 1
    np.savez_compressed(OUT / 'route_source_profile.npz', station_m=stations,
        utm_easting_m=points[:,0], utm_northing_m=points[:,1],
        source_surface_navd88_m=profile_source, within_survey_water=profile_wet)
    manifest = {'schema': 'raftsim.south_fork.cartesian_survey_terrain.v1',
        'status': 'captured_full_reach_terrain_ready_for_geometry_integration',
        'route_axis': route_f['properties']['axis_id'], 'reach_length_m': route.length,
        'horizontal_crs': 'EPSG:32610', 'vertical_datum': 'NAVD88', 'z_units': 'metres',
        'grid_cell_m': CELL, 'native_dem_cell_m': FT_US_TO_M,
        'bounds_utm_m': [xmin,ymin,xmax,ymax], 'shape_rows_cols': [height,width],
        'coordinate_policy': 'Cartesian metres; do not deform this terrain into a station/lateral ribbon',
        'source_tile_count': len(tiles), 'corridor_half_width_m': 240,
        'corridor_valid_fraction': float(np.isfinite(surface[coverage]).mean()),
        'route_samples_inside_survey_water_fraction': float(profile_wet.mean()),
        'canonical_source_surface': {'path': str(surface_path.relative_to(ROOT)),
            'sha256': hashlib.sha256(surface_path.read_bytes()).hexdigest()},
        'unknown_submerged_bed_mask': {'path': str(mask_path.relative_to(ROOT)),
            'sha256': hashlib.sha256(mask_path.read_bytes()).hexdigest()},
        'measured_dry_terrain_modified': False, 'random_boulders_added': 0,
        'bathymetry_known': False, 'game_integrated': False,
        'hydraulic_validation_passed': False, 'production_promoted': False}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    main()
