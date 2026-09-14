"""Exact-geometry base-coupling controls on the real rapid; not river acceptance."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'unreal/Scripts'))
from audit_carrier_source_epochs import exact_cells


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--atlas', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=10)
    parser.add_argument('--stepper', choices=('explicit', 'implicit-frozen'), default='explicit')
    parser.add_argument('--relative-stages', action='store_true')
    parser.add_argument('--energy-audit', action='store_true')
    args = parser.parse_args()
    if args.steps < 1:
        parser.error('--steps must be positive')
    if args.report.exists():
        raise FileExistsError(args.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    geometry_path, coordinate_path = base/'composite_terrain/manifest.json', base/'hydraulic_regions_context/coordinate_map.json'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry, coordinates, atlas = read(geometry_path), read(coordinate_path), read(args.atlas)
    if sha(mesh_path) != geometry['registered_rapid_sha256'] or atlas['schema'] != 'raftsim.cartesian_state_atlas.v1':
        raise ValueError('Changed source mesh or unsupported atlas')
    with np.load(mesh_path, allow_pickle=False) as mesh:
        terrain = RegisteredMeshSampler(mesh)
    origin, shape = np.array([-5439., 3593.]), (16, 16)
    if atlas['grid_spacing_m'] != 1. or atlas['source_elevation_datum_m'] != coordinates['vertical_datum_m']:
        raise ValueError('Different source grid/datum')
    offset = np.array(coordinates['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    yy, xx = np.indices(shape)
    cells = exact_cells(origin+np.stack((xx.ravel(), yy.ravel()), 1),
                        [tile['origin_m'] for tile in atlas['tiles']], atlas['tile_shape'], 1.)
    if (cells < 0).any():
        raise ValueError('Missing source cell in selected footprint')
    # Requested whole-metre labels only select cell IDs. Use the stored lattice
    # coordinates for geometry; the atlas retains a ~1 nm origin offset from
    # large UTM subtraction. Do not silently resample those cells at rounded XY.
    origins = np.array([tile['origin_m'] for tile in atlas['tiles']])
    source_points = origins[cells[:, 0]]+cells[:, [2, 1]]*atlas['grid_spacing_m']
    origin = source_points[0].copy()
    if not np.array_equal(source_points, origin+np.stack((xx.ravel(), yy.ravel()), 1)):
        raise ValueError('Selected source cells do not form one exact regular patch')
    patch = SubcellGeometryPatch(terrain, origin+offset, shape, relative_stages=args.relative_stages)
    paths = [args.atlas, geometry_path, coordinate_path, mesh_path, Path(__file__),
             ROOT/'physics/scripts/triangle_cell_storage.py', ROOT/'physics/scripts/triangle_face_section.py',
             ROOT/'physics/scripts/subcell_geometry_patch.py', ROOT/'physics/scripts/south_fork_registered_mesh.py']
    if args.stepper == 'implicit-frozen':
        paths.append(ROOT/'physics/scripts/subcell_implicit_transport.py')
    if args.energy_audit:
        paths.append(ROOT/'physics/scripts/subcell_mechanical_energy.py')
    initial_hashes = {str(path): sha(path) for path in paths}
    fields = {}
    for key in ('bed', 'h', 'u', 'v'):
        record = atlas['arrays'][key]
        path = (args.atlas.parent/record['file']).resolve()
        if sha(path) != record['sha256']:
            raise ValueError('Changed source array: '+key)
        array = np.load(path, allow_pickle=False, mmap_mode='r')
        if list(array.shape) != record['shape'] or array.dtype != np.dtype('<f8') or not np.isfinite(array).all():
            raise ValueError('Malformed source array: '+key)
        tile, row, col = cells.T
        fields[key] = np.array(array[tile*atlas['tile_shape'][0]+row, col]).reshape(shape)
        paths.append(path)
        initial_hashes[str(path)] = sha(path)
    local_points = origin+np.stack((xx.ravel(), yy.ravel()), 1)+offset
    exact_bed = terrain.sample(local_points[:, 0], local_points[:, 1]).reshape(shape)
    source_bed = fields['bed']+atlas['source_elevation_datum_m']-geometry['rapid_datum_navd88_m']
    if not np.allclose(source_bed, exact_bed, atol=1e-9, rtol=0):
        raise ValueError('Compared hydraulic/source geometry differs at cell centers')
    controls = []
    for eta in (6.5, 7.5, 8.5, 10.):
        volume, momentum = patch.state_from_stages(eta)
        dv, dp, _ = patch.rates(volume, momentum)
        maximum_rate = float(abs(dp).max())
        if abs(dv).max() > 1e-11 or maximum_rate > 1e-10:
            raise ValueError('Actual-geometry lake-at-rest control failed')
        controls.append(dict(stage_rapid_datum_m=eta, wet_cells=int((volume > 0).sum()),
            dry_cells=int((volume == 0).sum()), volume_m3=float(volume.sum()),
            maximum_cell_volume_rate_m3s=float(abs(dv).max()),
            maximum_momentum_rate_m4s2=maximum_rate))
    volume = fields['h'].copy()
    momentum = volume[:, :, None]*np.stack((fields['u'], fields['v']), axis=2)
    initial_volume = float(volume.sum())
    steps, elapsed, failure = [], 0., None
    started = time.perf_counter()
    for index in range(args.steps):
        dv, dp, limit, bound = patch.rates(volume, momentum, diagnostics=True)
        eta = np.array([cell.stage_for_volume(v) for cell, v in zip(patch.cells, volume.ravel())]).reshape(shape)
        velocity = np.divide(momentum, volume[:, :, None], out=np.zeros_like(momentum), where=volume[:, :, None] > 0)
        # Gradient of nondispersive mechanical energy for exact hydrostatic
        # cell storage. This is not the required two-pole physical energy.
        rate = float(np.sum((9.81*eta-.5*np.sum(velocity*velocity, axis=2))*dv)+np.sum(velocity*dp))
        if rate > 1e-9:
            failure = dict(step=index+1, elapsed_seconds=elapsed,
                error='Base mechanical energy production became positive', energy_rate=rate)
            break
        old_volume = volume
        energy_check = None
        if args.energy_audit:
            from subcell_mechanical_energy import energy
            before_energy = energy(patch, volume, momentum)
        if args.stepper == 'implicit-frozen':
            from subcell_implicit_transport import advance
            dt = min(.02, .45*bound['wave_limit_seconds'])
            try:
                volume, momentum = advance(patch, volume, momentum, dt)
            except (ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
                failure = dict(step=index+1, elapsed_seconds=elapsed, attempted_dt_seconds=dt,
                    error=str(error), before_step_bounds=bound)
                break
        else:
            dt = min(.02, .45*limit)
            volume, momentum = patch.advance(volume, momentum, dt)
        if args.energy_audit:
            after_energy = energy(patch, volume, momentum)
            energy_change = after_energy['total']-before_energy['total']
            energy_check = dict(before=before_energy, after=after_energy, change=energy_change)
            if energy_change > 1e-9:
                failure = dict(step=index+1, elapsed_seconds=elapsed, attempted_dt_seconds=dt,
                    error='Finite-step nondispersive mechanical energy increased', energy_check=energy_check)
                break
        elapsed += dt
        error = float(volume.sum()-initial_volume)
        if abs(error) > 1e-10:
            raise ValueError('Closed-patch volume conservation failed')
        steps.append(dict(step=index+1, elapsed_seconds=elapsed, dt_seconds=dt,
            local_dt_limit_seconds=float(limit), minimum_volume_m3=float(volume.min()),
            maximum_volume_m3=float(volume.max()), total_volume_error_m3=error,
            nondispersive_mechanical_energy_rate=rate, before_step_bounds=bound,
            finite_step_energy=energy_check,
            dry_cells=int((volume == 0).sum()),
            floating_to_zero_cells=int(((old_volume > 0) & (volume == 0)).sum()),
            maximum_cell_speed_mps=float(np.max(np.divide(np.linalg.norm(momentum, axis=2), volume,
                out=np.zeros_like(volume), where=volume > 0)))))
    for path in paths:
        if sha(path) != initial_hashes[str(path)]:
            raise ValueError('Protected input changed during audit')
    report = dict(schema='raftsim.south_fork.subcell_base_transport.v1', accepted=False,
        stepper=args.stepper,
        relative_stages=args.relative_stages,
        finite_step_energy_audited=args.energy_audit,
        completed_requested_steps=failure is None, rejected_update=failure,
        cells=shape[0]*shape[1], shared_and_wall_faces=len(patch.faces), source_field_origin_m=origin.tolist(),
        source_shape=list(shape), original_atlas_time_seconds=atlas['source_time_seconds'],
        maximum_source_center_bed_error_m=float(abs(source_bed-exact_bed).max()),
        stationary_controls=controls, source_initialized_closed_patch_steps=steps,
        initial_volume_m3=initial_volume, evolving_loop_wall_seconds=time.perf_counter()-started,
        input_sha256={str(path.resolve()): initial_hashes[str(path)] for path in paths},
        scope='Original registered terrain and exact shared face geometry. Synthetic lakes and nondispersive base steps using the recorded stepper, initialized from the real atlas with reflecting walls on this small test patch, NOT actual river boundaries or continued river history. No artificial depth, global rescale or source/cook/map mutation. Rusanov base transport is dissipative and first order; mechanical energy checks do not qualify the full two-pole energy, dispersion, refinement, internal basin connectivity, breaking waves, open boundaries, native budget, rendered contact, 30 FPS, or scene acceptance.')
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({key: value for key, value in report.items()
        if key not in ('input_sha256', 'source_initialized_closed_patch_steps')}, indent=2))
    if failure is not None:
        raise RuntimeError('Rejected coupled update; failure retained in '+str(args.report))


if __name__ == '__main__':
    main()
