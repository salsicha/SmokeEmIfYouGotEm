"""Recover required hydraulic context from retained, hash-verified DEM tiles.

Additive only: original surface/bed vertices, rapid mesh and existing triangle
ownership remain unchanged. New supplemental triangles fill only previously
unrendered source coverage; no invented elevation fills are permitted.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
FULL = BASE/'full_reach'
OUT = FULL/'source_context_extension'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    from rasterio.features import rasterize
    from scipy.ndimage import distance_transform_edt
    from shapely.geometry import mapping
    from shapely.ops import unary_union
    from build_south_fork_survey_reconstruction import read_breaklines, FT_US_TO_M, validated_horizontal_crs
    from prepare_south_fork_hydraulic_regions import region_centers
    from south_fork_composite_terrain import coarse_quad_mask
    assert not OUT.exists(), 'Keep previous context evidence; choose a new revision'
    geometry_file = FULL/'composite_terrain/manifest.json'
    base = json.loads(geometry_file.read_text())
    with rasterio.open(FULL/'captured_surface_navd88_m.tif') as ds:
        old_source = ds.read(1)
        old_transform = ds.transform
    with rasterio.open(FULL/'unknown_submerged_bed_mask.tif') as ds:
        old_water = ds.read(1)
    with rasterio.open(FULL/'composite_terrain/coarse_bed_navd88_m.tif') as ds:
        old_bed = ds.read(1)
    with np.load(FULL/'composite_terrain/coarse_topology.npz') as data:
        old_quads = data['valid_quads']
    assert sha(FULL/'captured_surface_navd88_m.tif') == base['source_surface_sha256']
    assert sha(FULL/'unknown_submerged_bed_mask.tif') == base['source_water_mask_sha256']
    assert sha(FULL/'composite_terrain/coarse_bed_navd88_m.tif') == base['artifacts']['coarse_bed_navd88_m.tif']
    coordinates = json.loads((FULL/'playable_route/coordinate_map.json').read_text())
    points = np.asarray(coordinates['points'])
    _, route_centers = region_centers(points, np.asarray(coordinates['origin_utm_m']))
    wr, wc = np.nonzero(old_water == 1)
    wet_xy = np.column_stack((old_transform.c+(wc+.5)*2, old_transform.f-(wr+.5)*2))
    # Every captured water vertex lies within 40 m (per axis) of this lattice,
    # leaving >=120 m complete-square margin in a 320 m source region.
    water_centers = np.unique(np.rint(wet_xy/80).astype(np.int64)*80, axis=0)
    centers = np.unique(np.vstack((route_centers, water_centers)), axis=0)
    old_x0, old_y0 = base['grid']['first_vertex_utm_m']
    # Keep the original 2 m lattice, allowing an additive outward extent.
    xmin = min(old_x0, old_x0+np.floor((centers[:,0].min()-164-old_x0)/2)*2)
    xmax = max(old_x0+(old_source.shape[1]-1)*2,
               old_x0+np.ceil((centers[:,0].max()+164-old_x0)/2)*2)
    ymin = min(old_y0-(old_source.shape[0]-1)*2,
               old_y0+np.floor((centers[:,1].min()-164-old_y0)/2)*2)
    ymax = max(old_y0, old_y0+np.ceil((centers[:,1].max()+164-old_y0)/2)*2)
    shape = (int(round((ymax-ymin)/2))+1, int(round((xmax-xmin)/2))+1)
    affine = from_origin(xmin-1, ymax+1, 2, 2)
    row0, col0 = int(round((ymax-old_y0)/2)), int(round((old_x0-xmin)/2))
    old_slice = np.s_[row0:row0+old_source.shape[0], col0:col0+old_source.shape[1]]
    requested = np.zeros(shape, dtype=bool)
    for east, north in centers:
        c0 = int(np.floor((east-164-xmin)/2)); c1 = int(np.ceil((east+164-xmin)/2))
        r0 = int(np.floor((ymax-north-164)/2)); r1 = int(np.ceil((ymax-north+164)/2))
        requested[r0:r1+1,c0:c1+1] = True
    old_valid = np.isfinite(old_source)
    requested[old_slice] |= old_valid
    source = np.full(shape, np.nan, dtype=np.float32)
    tiles_file = BASE/'sources/dem/full-reach-downloads.json'
    tiles = json.loads(tiles_file.read_text())
    OUT.mkdir()
    report = dict(schema='raftsim.south_fork.additive_source_context.v1',
        base_geometry_manifest_sha256=sha(geometry_file), retained_source_tile_manifest_sha256=sha(tiles_file),
        source_tile_count=len(tiles), required_region_count=len(centers),
        original_grid_offset_row_col=[row0,col0], grid=dict(first_vertex_utm_m=[xmin,ymax], cell_m=2., shape=list(shape)),
        completed=False, normal_map_integrated=False, measured_bathymetry=False,
        full_reconstruction_accepted=False)
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    for index, tile in enumerate(tiles):
        path = BASE/'sources/dem'/tile['file']
        assert sha(path) == tile['sha256'], 'Retained DEM source hash changed'
        with rasterio.open(path) as ds:
            horizontal = validated_horizontal_crs(ds)
            data = ds.read(1).astype(np.float32)
            data[data == ds.nodata] = np.nan
            data *= FT_US_TO_M
            reproject(data, source, src_transform=ds.transform, src_crs=horizontal,
                src_nodata=np.nan, dst_transform=affine, dst_crs='EPSG:32610',
                dst_nodata=np.nan, init_dest_nodata=False, resampling=Resampling.bilinear)
        if index % 10 == 0:
            print(f'Verified/reprojected retained source {index+1}/{len(tiles)}', flush=True)
    # Restore the original authority exactly, including its previous reprojection.
    original_area = source[old_slice]
    original_area[old_valid] = old_source[old_valid]
    source[~requested] = np.nan
    missing = requested & ~np.isfinite(source)
    if missing.any():
        mr, mc = np.nonzero(missing)
        report.update(missing_source_vertex_count=int(missing.sum()),
            first_missing_utm_m=np.column_stack((xmin+mc[:20]*2,ymax-mr[:20]*2)).tolist())
        (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
        raise ValueError('Retained tiles do not cover required context; additional capture required')
    water_geometry = unary_union([g for _,g in read_breaklines()])
    water = rasterize([(mapping(water_geometry),1)], out_shape=shape, transform=affine, dtype='uint8')
    assert np.array_equal(water[old_slice][old_water != 255], old_water[old_water != 255])
    water[~requested] = 255
    distance = distance_transform_edt(water == 1, sampling=2).astype(np.float32)
    depth = np.minimum(2.2, .35*np.maximum(0., distance-1.))
    bed = source.copy()
    bed[water == 1] -= depth[water == 1]
    original_bed_area = bed[old_slice]
    original_bed_area[old_valid] = old_bed[old_valid]
    assert np.array_equal(source[old_slice][old_valid], old_source[old_valid])
    assert np.array_equal(bed[old_slice][old_valid], old_bed[old_valid])
    quads = coarse_quad_mask(bed, xmin, ymax, 2., base['coarse_exclusion_boundary_utm_m'])
    prior = np.zeros(quads.shape, dtype=bool)
    prior[row0:row0+old_quads.shape[0],col0:col0+old_quads.shape[1]] = old_quads
    assert np.all(quads[prior])
    supplement = quads & ~prior
    profile = dict(driver='GTiff', width=shape[1], height=shape[0], count=1,
        dtype='float32', crs='EPSG:32610', transform=affine, nodata=np.nan, tiled=True, compress='deflate')
    for name, values in [('captured_surface_navd88_m.tif',source), ('coarse_bed_navd88_m.tif',bed)]:
        with rasterio.open(OUT/name,'w',**profile) as ds:
            ds.write(values,1)
            ds.update_tags(vertical_datum='NAVD88', submerged_bed='UNCALIBRATED_INFERENCE_NOT_SURVEY')
    with rasterio.open(OUT/'unknown_submerged_bed_mask.tif','w',**dict(profile,dtype='uint8',nodata=255)) as ds:
        ds.write(water,1)
    np.savez_compressed(OUT/'topology.npz',valid_quads=quads,supplemental_quads=supplement)
    np.savez_compressed(OUT/'required_regions.npz',centers_utm_m=centers)
    names = ['captured_surface_navd88_m.tif','coarse_bed_navd88_m.tif','unknown_submerged_bed_mask.tif','topology.npz','required_regions.npz']
    report.update(completed=True, missing_source_vertex_count=0,
        original_source_vertices_bit_identical=True, original_bed_vertices_bit_identical=True,
        original_coarse_triangles_retained=True, registered_rapid_and_seam_unchanged=True,
        supplemental_triangle_count=int(supplement.sum())*2, added_source_vertex_count=int(np.isfinite(source).sum()-old_valid.sum()),
        new_submerged_bed_is_uncalibrated_inference=True,
        artifacts={name:sha(OUT/name) for name in names})
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
