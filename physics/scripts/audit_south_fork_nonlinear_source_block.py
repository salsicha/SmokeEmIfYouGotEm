"""Unchanged South Fork block state with explicit reflecting test boundaries.

Unlike the earlier artificial-lake experiment, original volumes and physical
velocities are retained as the initial state. Optional fixed-support time steps
are closed controls, not the natural open river or gameplay acceptance.
"""
import argparse
import json
from pathlib import Path
import numpy as np

from audit_south_fork_subcell_energy_flux import ROOT, read, sha, exact_cells
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_nonlinear_metric_stage import stage
from subcell_nonlinear_time_stage import history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', required=True, type=Path)
    parser.add_argument('--atlas', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--block-col', type=int, choices=range(13), default=6)
    parser.add_argument('--block-row', type=int, choices=range(13), default=6)
    parser.add_argument('--steps', type=int, default=0, help='Optional fixed-support nonlinear time steps')
    parser.add_argument('--dt', type=float, default=1/120)
    args = parser.parse_args()
    if args.steps < 0 or not np.isfinite(args.dt) or args.dt <= 0:
        raise ValueError('Nonnegative step count and positive finite duration required')
    if args.report.exists():
        raise FileExistsError(args.report)
    source, atlas = read(args.source_report), read(args.atlas)
    if (source['schema'] != 'raftsim.south_fork.subcell_pressure_kinetic_geometry.v1'
            or source['pool_geometry'] != 'exact-source-relative' or source['total_cells'] != 256
            or atlas['schema'] != 'raftsim.cartesian_state_atlas.v1' or atlas['grid_spacing_m'] != 1.):
        raise ValueError('Original exact-source South Fork report and atlas required')
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry_path = base/'composite_terrain/manifest.json'
    coordinates_path = base/'hydraulic_regions_context/coordinate_map.json'
    inputs = [args.atlas, mesh_path, geometry_path, coordinates_path]
    for key in ('h', 'u', 'v'):
        inputs.append((args.atlas.parent/atlas['arrays'][key]['file']).resolve())
    for path in inputs:
        if source['source_sha256'].get(str(path.resolve())) != sha(path):
            raise ValueError('Original snapshot/source changed: '+str(path))
    paths = [args.source_report]+inputs+sorted((ROOT/'physics/scripts').glob('*.py'))
    hashes = {str(path.resolve()): sha(path) for path in paths}
    geometry, coordinates = read(geometry_path), read(coordinates_path)
    if sha(mesh_path) != geometry['registered_rapid_sha256']:
        raise ValueError('Registered source geometry manifest mismatch')
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
        authority = np.asarray(mesh['authority']).ravel().copy()
    row, col = np.indices((4, 4))
    offsets = np.stack((col.ravel()+args.block_col, row.ravel()+args.block_row), axis=1)
    world = np.asarray(source['source_origin_m'])+offsets
    located = exact_cells(world, [tile['origin_m'] for tile in atlas['tiles']], atlas['tile_shape'], 1.)
    if (located < 0).any():
        raise ValueError('Original block not covered by the original atlas')
    fields = {}
    for key in ('h', 'u', 'v'):
        record = atlas['arrays'][key]
        path = (args.atlas.parent/record['file']).resolve()
        values = np.load(path, mmap_mode='r', allow_pickle=False)
        if values.shape != tuple(record['shape']) or values.dtype != np.dtype('<f8'):
            raise ValueError('Original snapshot array shape/type changed')
        tile, iy, ix = located.T
        fields[key] = np.array(values[tile*atlas['tile_shape'][0]+iy, ix]).reshape(4, 4)
    records = {r['index']: r for r in source['records']}
    indices = [int(16*y+x) for x, y in offsets]
    for index, volume in zip(indices, fields['h'].ravel()):
        expected = records[index]['volume_m3'] if index in records else 0.
        if volume != expected:
            raise ValueError('Original physical source volume mismatch')
    origin = (np.asarray(source['source_origin_m'])
              +(np.asarray(coordinates['world_origin_utm_m'])-np.asarray(geometry['rapid_origin_utm_m']))
              +[args.block_col, args.block_row])
    patch = SubcellGeometryPatch(sampler, origin, (4, 4), relative_stages=True, exact_sources=True)
    momentum = fields['h'][..., None]*np.stack((fields['u'], fields['v']), axis=-1)
    pools = WetPoolPartition(patch, sampler, origin, fields['h'], momentum)
    result, failure = None, None
    try:
        value = stage(pools)
        result = {k: v for k, v in value.items() if k not in
                  ('physical_momentum_rate', 'physical_acceleration', 'volume_rate', 'physical_momentum_faces', 'bed_force', 'wall_force')}
        result.update(maximum_physical_acceleration=float(np.max(np.linalg.norm(value['physical_acceleration'][:, 0], axis=1))),
                      total_momentum_rate=value['physical_momentum_rate'][:, 0].sum(axis=0),
                      total_bed_force=value['bed_force'].sum(axis=0), total_wall_force=value['wall_force'].sum(axis=0))
    except ValueError as exc:
        failure = str(exc)
    time_control = history(pools, args.steps, args.dt,
        on_step=lambda row: print(json.dumps(dict(time_step=row), allow_nan=False), flush=True)
        ) if args.steps and result is not None else None
    provenance = [dict(original_cell=indices[p['parent']], source_triangle_indices=p['source_triangle_indices'],
                       volume_m3=p['volume'], physical_momentum=p['momentum'],
                       vertex_authority_codes=sorted(set(map(int, authority[sampler.faces[p['source_triangle_indices']]].ravel()))))
                  for p in pools.pools]
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source or implementation changed during nonlinear block control')
    report = dict(schema='raftsim.south_fork.closed_nonlinear_source_block.v1', accepted=False,
        original_block_col_row=[args.block_col, args.block_row], origin_registered_m=origin,
        original_snapshot_time_seconds=source['source_time_seconds'], pools=len(pools.pools),
        volume_partition_error=pools.maximum_volume_error, momentum_partition_error=pools.maximum_momentum_error,
        closed_snapshot_rate_controls_passed=result is not None, result=result, failure=failure,
        time_control=time_control,
        boundary_note='Original initial volumes and velocities, but reflecting test-block boundaries. Optional time steps are closed candidates, NOT the natural open river.',
        authority_note='1 captured DEM; 3 exposed-rock returns; 2 submerged prior, 4 interpolation, 5 inferred flank. Mixed triangles are not wholly measured.',
        source_provenance=provenance, source_sha256=hashes,
        actual_open_flow_or_finite_time_or_native_or_gameplay_accepted=False)
    converter = lambda v: v.tolist() if isinstance(v, np.ndarray) else float(v)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False, default=converter)
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_provenance', 'source_sha256')}, default=converter), flush=True)
    return 0 if (report['closed_snapshot_rate_controls_passed']
                 and (not args.steps or time_control['closed_fixed_support_time_controls_passed'])) else 1


if __name__ == '__main__':
    raise SystemExit(main())
