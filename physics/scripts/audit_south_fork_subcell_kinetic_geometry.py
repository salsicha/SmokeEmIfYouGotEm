"""Captured-cell pressure kinetic coefficients, NOT evolved river acceptance."""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_south_fork_subcell_energy_flux import ROOT, read, sha, exact_cells
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_pressure_kinetic_geometry import local_form, quadrature


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--atlas', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    geometry_path = base/'composite_terrain/manifest.json'
    coordinate_path = base/'hydraulic_regions_context/coordinate_map.json'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry, coordinates, atlas = read(geometry_path), read(coordinate_path), read(args.atlas)
    if (sha(mesh_path) != geometry['registered_rapid_sha256']
            or atlas['schema'] != 'raftsim.cartesian_state_atlas.v1' or atlas['grid_spacing_m'] != 1.
            or atlas['source_elevation_datum_m'] != coordinates['vertical_datum_m']):
        raise ValueError('Changed registered source or unsupported grid/datum')
    yy, xx = np.indices((16, 16))
    offsets = np.stack((xx.ravel(), yy.ravel()), axis=1)
    cells = exact_cells(np.array([-5439., 3593.])+offsets,
        [tile['origin_m'] for tile in atlas['tiles']], atlas['tile_shape'], 1.)
    if (cells < 0).any():
        raise ValueError('Missing actual source cell')
    origins = np.array([tile['origin_m'] for tile in atlas['tiles']])[cells[:, 0]]+cells[:, [2, 1]]
    if not np.array_equal(origins, origins[0]+offsets):
        raise ValueError('Source is not the original regular lattice')
    paths = [args.atlas, geometry_path, coordinate_path, mesh_path, Path(__file__)]
    paths += [ROOT/'physics/scripts'/name for name in (
        'subcell_pressure_kinetic_geometry.py', 'triangle_cell_storage.py', 'subcell_geometry_patch.py',
        'triangle_face_section.py', 'south_fork_registered_mesh.py', 'audit_south_fork_subcell_energy_flux.py')]
    hashes = {str(path.resolve()): sha(path) for path in paths}
    fields = {}
    for key in ('h', 'bed'):
        record = atlas['arrays'][key]
        path = (args.atlas.parent/record['file']).resolve()
        if sha(path) != record['sha256']:
            raise ValueError('Changed source array '+key)
        source = np.load(path, mmap_mode='r', allow_pickle=False)
        if source.shape != tuple(record['shape']) or source.dtype != np.dtype('<f8'):
            raise ValueError('Malformed source array '+key)
        tile, row, col = cells.T
        fields[key] = np.array(source[tile*atlas['tile_shape'][0]+row, col])
        if not np.isfinite(fields[key]).all():
            raise ValueError('Nonfinite actual source cell')
        hashes[str(path)] = record['sha256']
    with np.load(mesh_path, allow_pickle=False) as mesh:
        terrain = RegisteredMeshSampler(mesh)
        authority = np.asarray(mesh['authority']).ravel().copy()
    shift = np.array(coordinates['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    patch = SubcellGeometryPatch(terrain, origins[0]+shift, (16, 16), relative_stages=True)
    source_bed = fields['bed']+atlas['source_elevation_datum_m']-geometry['rapid_datum_navd88_m']
    exact_bed = terrain.sample(*(origins+shift).T)
    if not np.allclose(source_bed, exact_bed, atol=1e-9, rtol=0):
        raise ValueError('Captured and hydraulic center beds differ')
    records, unsupported, provenance = [], [], {}
    for index, (cell, volume) in enumerate(zip(patch.cells, fields['h'])):
        if volume < 0:
            raise ValueError('Negative original source volume is not a dry cell')
        if volume == 0:
            unsupported.append(dict(index=index, reason='dry; no inverse-mass or wet-front closure'))
            continue
        form = local_form(cell, volume)
        triangle_volume, triangle_wet_area = cell._triangle_volume_and_wet_area(form['stage_offset'], cell.relative_levels)
        cell_codes = set()
        for source_id, tv, tw in zip(cell.source_triangle_indices, triangle_volume, triangle_wet_area):
            if tw == 0:
                continue
            codes = sorted(set(map(int, authority[terrain.faces[source_id]])))
            cell_codes.update(codes)
            key = ','.join(map(str, codes))
            entry = provenance.setdefault(key, dict(wet_projected_area_m2=0., volume_m3=0.))
            entry['wet_projected_area_m2'] += float(tw)
            entry['volume_m3'] += float(tv)
        weights, h, slopes = quadrature(cell, form['stage_offset'])
        average_slope = np.sum((weights*h)[:, None]*slopes, axis=0)/volume
        slope_gram = form['gram'][1:, 1:]
        collapsed_slope_gram = 3*volume*np.outer(average_slope, average_slope)
        covariance = slope_gram-collapsed_slope_gram
        # This exact wet-volume-weighted mean is a best aggregate diagnostic,
        # NOT an assertion that it is the actual runtime coarse slope stencil.
        slope_trace = float(np.trace(slope_gram))
        lost_fraction = float(np.trace(covariance)/slope_trace) if slope_trace > 0 else 0.
        step = volume*1e-5
        low, high = local_form(cell, volume-step), local_form(cell, volume+step)
        fd = (high['gram']-low['gram'])/(2*step)
        derivative_error = float(np.max(abs(fd-form['volume_derivative']))
                                 /max(1., np.max(abs(form['volume_derivative']))))
        relative_volume_error = form['volume_error']/volume
        if relative_volume_error > 1e-10 or derivative_error > 1e-6:
            raise ValueError('Actual exact-volume/kinetic-tangent geometry control failed')
        mean_wet_depth_cubic = volume*(volume/form['wet_area'])**2
        records.append(dict(index=index, volume_m3=float(volume), wet_area_m2=form['wet_area'],
            wet_source_vertex_authority_codes=sorted(cell_codes),
            original_triangle_count=len(cell.areas), factor_row_count=len(form['factor']),
            relative_volume_error=relative_volume_error, relative_kinetic_tangent_error=derivative_error,
            slope_variance_energy_fraction=lost_fraction,
            minimum_slope_covariance_eigenvalue=float(np.linalg.eigvalsh(covariance).min()),
            exact_cubic_depth_moment=float(form['depth_moments'][3]),
            mean_wet_depth_cubic_moment=mean_wet_depth_cubic,
            mean_depth_cubic_loss_fraction=float(1-mean_wet_depth_cubic/form['depth_moments'][3]),
            gram=form['gram'].tolist(), volume_derivative=form['volume_derivative'].tolist()))
    if not records:
        raise ValueError('No positive actual cells evaluated')
    for path, expected in hashes.items():
        if sha(Path(path)) != expected:
            raise ValueError('Source changed during geometry audit')
    quantiles = lambda key: np.quantile([r[key] for r in records], [0, .5, .95, 1]).tolist()
    result = dict(schema='raftsim.south_fork.subcell_pressure_kinetic_geometry.v1',
        accepted=False, positive_cell_geometry_controls_passed=True, total_cells=256,
        positive_cells=len(records), unsupported_cells=unsupported,
        wet_geometry_by_source_vertex_authority_codes=provenance,
        provenance_note='Codes are preserved per original triangle vertex, not averaged or promoted. '
            '1=captured DEM ground; 3=original exposed-rock return support. Other codes are inference/'
            'interpolation, including 2=uncalibrated submerged prior and 5=inferred connecting flank. '
            'A triangle with mixed vertex authority is not wholly measured bathymetry.',
        source_time_seconds=atlas['source_time_seconds'], source_origin_m=origins[0].tolist(),
        source_center_error_m=float(np.max(abs(source_bed-exact_bed))),
        maximum_relative_volume_error=max(r['relative_volume_error'] for r in records),
        maximum_relative_kinetic_tangent_error=max(r['relative_kinetic_tangent_error'] for r in records),
        slope_variance_energy_fraction_min_median_p95_max=quantiles('slope_variance_energy_fraction'),
        mean_depth_cubic_loss_fraction_min_median_p95_max=quantiles('mean_depth_cubic_loss_fraction'),
        records=records, source_sha256=hashes,
        scope='Original wet source-triangle geometry and original cell volumes. Positive local kinetic '
              'factor and fixed-terrain volume derivative only; no selected intercell derivative, '
              'two-pole solve, nonlinear bed-force work, dry/open/time, native or gameplay qualification.')
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'source_sha256')}, indent=2))


if __name__ == '__main__':
    main()
