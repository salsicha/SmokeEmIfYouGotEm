"""Stage full-river Cartesian terrain, retained captured rapid, and inferred seam.

Bed outside the rapid is an explicit uncalibrated shore-distance prior. This is
not a validated hydraulic solution and is not promoted to the game by this tool.
"""
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
from south_fork_composite_terrain import stitch_rectangular_boundaries, coarse_quad_mask, sample_triangles

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = BASE/'full_reach/composite_terrain'
RAPID_SOURCE = ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912/registered_mesh_source.npz'
MAX_INFERRED_DEPTH_M = 2.2
INFERRED_SHORE_SLOPE = .35
SEAM_MIN_WIDTH_M = 4.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import rasterio
    from scipy.ndimage import distance_transform_edt
    terrain_manifest = json.loads((BASE/'full_reach/manifest.json').read_text())
    source_path = BASE/'full_reach/captured_surface_navd88_m.tif'
    mask_path = BASE/'full_reach/unknown_submerged_bed_mask.tif'
    assert sha(source_path) == terrain_manifest['canonical_source_surface']['sha256']
    assert sha(mask_path) == terrain_manifest['unknown_submerged_bed_mask']['sha256']
    delivery = json.loads((BASE/'troublemaker/playable_flow/delivery.json').read_text())
    assert sha(RAPID_SOURCE) == delivery['source_geometry_sha256']
    rapid_coordinates = json.loads((BASE/'troublemaker/playable_flow/coordinate_map.json').read_text())
    origin = np.asarray(rapid_coordinates['origin_utm_m'])
    datum = rapid_coordinates['vertical_datum_m']
    with rasterio.open(source_path) as ds:
        source = ds.read(1)
        profile = ds.profile.copy()
        affine = ds.transform
        cell = ds.res[0]
        x0, y0 = affine*(.5, .5)
    with rasterio.open(mask_path) as ds:
        assert ds.transform == affine and ds.shape == source.shape
        water = ds.read(1) == 1
    assert np.isfinite(source[water]).all()
    print('Inferring only submerged cells; captured dry elevations stay bit-identical', flush=True)
    distance = distance_transform_edt(water, sampling=cell).astype(np.float32)
    depth = np.minimum(MAX_INFERRED_DEPTH_M, INFERRED_SHORE_SLOPE*np.maximum(0., distance-cell*.5))
    bed = source.copy()
    bed[water] -= depth[water]
    del distance, depth
    assert np.array_equal(source[~water], bed[~water], equal_nan=True)
    with np.load(RAPID_SOURCE, allow_pickle=False) as mesh:
        ex, ny = mesh['east_m']+origin[0], mesh['north_m']+origin[1]
        zz = mesh['z_m'].astype(np.float64)+datum
        inner = [np.column_stack((ex[0], ny[0], zz[0])),
                 np.column_stack((ex[:, -1], ny[:, -1], zz[:, -1])),
                 np.column_stack((ex[-1, ::-1], ny[-1, ::-1], zz[-1, ::-1])),
                 np.column_stack((ex[::-1, 0], ny[::-1, 0], zz[::-1, 0]))]
        assert all(np.allclose(edge[:, axis], edge[0, axis], atol=1e-9, rtol=0)
                   for edge, axis in zip(inner, [1, 0, 1, 0]))
        xmin, xmax, ymin, ymax = ex.min(), ex.max(), ny.min(), ny.max()
        inner_bounds = [float(xmin), float(ymin), float(xmax), float(ymax)]
    c0 = int(np.floor((xmin-SEAM_MIN_WIDTH_M-x0)/cell))
    c1 = int(np.ceil((xmax+SEAM_MIN_WIDTH_M-x0)/cell))
    r0 = int(np.floor((y0-ymax-SEAM_MIN_WIDTH_M)/cell))
    r1 = int(np.ceil((y0-ymin+SEAM_MIN_WIDTH_M)/cell))
    exclusion = [x0+c0*cell, y0-r1*cell, x0+c1*cell, y0-r0*cell]
    valid_quads = coarse_quad_mask(bed, x0, y0, cell, exclusion)
    def vertices(rows, cols):
        rows, cols = np.broadcast_arrays(rows, cols)
        return np.column_stack((x0+cols*cell, y0-rows*cell, bed[rows, cols]))
    outer = [vertices(r0, np.arange(c0, c1+1)), vertices(np.arange(r0, r1+1), c1),
             vertices(r1, np.arange(c1, c0-1, -1)), vertices(np.arange(r1, r0-1, -1), c0)]
    xyz, faces = stitch_rectangular_boundaries(inner, outer)
    edge_a = xyz[faces[:, 1], :2]-xyz[faces[:, 0], :2]
    edge_b = xyz[faces[:, 2], :2]-xyz[faces[:, 0], :2]
    area = (edge_a[:, 0]*edge_b[:, 1]-edge_a[:, 1]*edge_b[:, 0])*.5
    expected_area = (exclusion[2]-exclusion[0])*(exclusion[3]-exclusion[1])-(xmax-xmin)*(ymax-ymin)
    assert abs(area.sum()-expected_area) < 1e-6 and area.min() > 0
    # Every seam triangle is sampled through the same authoritative triangles.
    probes = xyz[faces].mean(axis=1)
    error = np.max(abs(sample_triangles(xyz, faces, probes[:, 0], probes[:, 1])-probes[:, 2]))
    assert error < 1e-7
    OUT.mkdir(parents=True, exist_ok=True)
    retained = OUT/'troublemaker_registered_source.npz'
    if retained.exists():
        assert sha(retained) == delivery['source_geometry_sha256'], 'Do not overwrite another rapid revision'
    else:
        shutil.copy2(RAPID_SOURCE, retained)
    assert sha(retained) == delivery['source_geometry_sha256']
    with rasterio.open(OUT/'coarse_bed_navd88_m.tif', 'w', **profile) as ds:
        ds.write(bed, 1)
        ds.update_tags(vertical_datum='NAVD88', bathymetry='UNCALIBRATED_INFERENCE_IN_WATER_MASK_ONLY')
    np.savez_compressed(OUT/'coarse_topology.npz', valid_quads=valid_quads)
    np.savez_compressed(OUT/'troublemaker_seam.npz', xyz_navd88_utm_m=xyz, triangles=faces)
    report = dict(schema='raftsim.south_fork.composite_terrain.v1',
        status='shared_cartesian_geometry_requires_hydraulic_cook_and_engine_integration',
        horizontal_crs='EPSG:32610', vertical_datum='NAVD88',
        source_surface_sha256=sha(source_path), source_water_mask_sha256=sha(mask_path),
        registered_rapid_sha256=sha(retained), rapid_origin_utm_m=origin.tolist(), rapid_datum_navd88_m=datum,
        source_dry_vertices_bit_identical=True, captured_rapid_arrays_and_topology_byte_identical=True,
        coarse_bed_prior=dict(maximum_depth_m=MAX_INFERRED_DEPTH_M, shore_slope=INFERRED_SHORE_SLOPE,
            calibrated=False, measured=False, inferred_water_vertex_count=int(water.sum())),
        grid=dict(first_vertex_utm_m=[x0, y0], cell_m=cell, shape=list(source.shape)),
        inner_boundary_utm_m=inner_bounds, coarse_exclusion_boundary_utm_m=list(exclusion),
        minimum_seam_width_m=SEAM_MIN_WIDTH_M, seam_is_inferred=True,
        seam_vertex_count=len(xyz), seam_triangle_count=len(faces), seam_projected_area_m2=float(area.sum()),
        seam_centroid_sampling_max_error_m=float(error), coarse_triangle_count=int(valid_quads.sum())*2,
        normal_map_integrated=False, hydraulic_validation_passed=False, full_reconstruction_accepted=False)
    report['artifacts'] = {name: sha(OUT/name) for name in ['coarse_bed_navd88_m.tif', 'coarse_topology.npz',
        'troublemaker_seam.npz', 'troublemaker_registered_source.npz']}
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
