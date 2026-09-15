"""Controlled lake/wave experiment on registered South Fork terrain, NOT its flow.

The completed source-geometry report locates the original cells and volumes.
Their median reconstructed stage defines an explicitly artificial level lake.
Original source triangles/authority are retained; original river velocities
are NOT reused or claimed. This cannot qualify the actual moving river.
"""
import argparse
import json
from pathlib import Path
import numpy as np

from audit_south_fork_subcell_energy_flux import ROOT, read, sha
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_source_frames import physical_datum
from subcell_gravity_wave_stage import GravityWaveStage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--block-col', type=int, choices=range(13), default=6)
    parser.add_argument('--block-row', type=int, choices=range(13), default=6)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    source = read(args.source_report)
    if (source['schema'] != 'raftsim.south_fork.subcell_pressure_kinetic_geometry.v1'
            or source['pool_geometry'] != 'exact-source-relative' or source['total_cells'] != 256):
        raise ValueError('Original exact-source South Fork geometry report required')
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry_path = base/'composite_terrain/manifest.json'
    coordinates_path = base/'hydraulic_regions_context/coordinate_map.json'
    paths = [args.source_report, mesh_path, geometry_path, coordinates_path]
    for path in paths[1:]:
        if source['source_sha256'][str(path.resolve())] != sha(path):
            raise ValueError('Original registered source changed: '+str(path))
    # Current code is independently locked; the completed input report keeps
    # its historical driver hash rather than pretending it ran today's code.
    paths += sorted((ROOT/'physics/scripts').glob('*.py'))
    hashes = {str(path.resolve()): sha(path) for path in paths}
    geometry, coordinates = read(geometry_path), read(coordinates_path)
    if sha(mesh_path) != geometry['registered_rapid_sha256']:
        raise ValueError('Registered geometry manifest mismatch')
    with np.load(mesh_path, allow_pickle=False) as mesh:
        terrain = RegisteredMeshSampler(mesh)
        authority = np.asarray(mesh['authority']).ravel().copy()
    offset = np.array([args.block_col, args.block_row], float)
    original_origin = np.asarray(source['source_origin_m'])+(
        np.asarray(coordinates['world_origin_utm_m'])-np.asarray(geometry['rapid_origin_utm_m']))
    origin = original_origin+offset
    patch = SubcellGeometryPatch(terrain, origin, (4, 4), relative_stages=True, exact_sources=True)
    records = {r['index']: r for r in source['records']}
    original_indices = [16*(args.block_row+row)+args.block_col+col for row in range(4) for col in range(4)]
    levels = [float(physical_datum(cell))+cell.relative_stage_for_volume(records[index]['volume_m3'])
              for cell, index in zip(patch.cells, original_indices) if index in records]
    level = float(np.median(levels))
    volumes, momenta = patch.state_from_stages(level, [0., 0.])
    pools = WetPoolPartition(patch, terrain, origin, volumes, momenta)
    stage = GravityWaveStage(pools)
    # A prescribed small linear perturbation, not a production depth cutoff
    # or a correction to measured/simulated water. Never lower it after failure.
    a = stage.volume*1e-6*np.cos(np.arange(len(stage.volume)))
    p = np.zeros((len(a), 2))
    steps, failure = [], None
    try:
        for index in range(6):
            result = stage.midpoint(a, p, .02)
            a, p = result['volume_perturbation'], result['physical_momentum']
            steps.append(dict(step=index+1, **{k: v for k, v in result.items()
                             if k not in ('volume_perturbation', 'physical_momentum')}))
    except ValueError as exc:
        failure = str(exc)
    provenance = []
    for pool in pools.pools:
        ids = pool['source_triangle_indices']
        codes = sorted(set(map(int, authority[terrain.faces[ids]].ravel())))
        provenance.append(dict(parent=pool['parent'], original_cell=original_indices[pool['parent']],
            source_triangle_indices=ids, vertex_authority_codes=codes, reference_volume_m3=pool['volume']))
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Implementation or source changed during wave experiment')
    report = dict(schema='raftsim.south_fork.controlled_linear_waves.v1', accepted=False,
        controlled_linear_steps_passed=len(steps) == 6, failure=failure, steps=steps,
        origin_registered_m=origin.tolist(), reference_level_above_registered_datum_m=level,
        original_patch_block_col_row=[args.block_col, args.block_row],
        reference_note='Artificial closed lake at median source-volume stage; NOT original river velocity, level or observed wave amplitude.',
        authority_note='1 captured DEM; 3 exposed-rock returns; 2 submerged prior, 4 gap interpolation, 5 inferred flank. Mixed triangles are not measured bathymetry.',
        pool_count=len(pools.pools), source_provenance=provenance, source_sha256=hashes,
        nonlinear_or_wetting_or_actual_flow_or_native_or_gameplay_accepted=False)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False,
                  default=lambda value: value.tolist() if isinstance(value, np.ndarray) else float(value))
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_provenance', 'source_sha256')},
                     default=lambda value: value.tolist() if isinstance(value, np.ndarray) else float(value)), flush=True)
    return 0 if report['controlled_linear_steps_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
