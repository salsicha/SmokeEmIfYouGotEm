"""Partition existing water identities; never initialize independent tanks.

Canonical positions stay in the parent ENU-centimetre frame. Internal faces
are shared solver interfaces, NOT new native-boundary particle emitters. This
is preparation for coupled runtime regions, not an installed GPU simulation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def partition(domain, max_xy=(128, 64)):
    counts = np.asarray(domain['physical_cells'])
    maximum = np.asarray(max_xy)
    spacing = np.asarray(domain['cell_size_m'], dtype=float)
    bounds = np.asarray(domain['native_face_bounds_m'], dtype=float)
    if (counts.shape != (3,) or maximum.shape != (2,) or
            not np.issubdtype(counts.dtype, np.integer) or not np.issubdtype(maximum.dtype, np.integer) or
            (counts < 2).any() or (maximum < 2).any() or counts[0] % 2 or maximum[0] % 2):
        raise ValueError('Integer cells and even X counts required; never trim the final cells')
    if (spacing.shape != (3,) or not np.isfinite(spacing).all() or (spacing <= 0).any() or
            bounds.shape != (2, 2) or not np.isfinite(bounds).all() or
            not np.allclose(bounds[1]-bounds[0], spacing[:2]*counts[:2], atol=1e-9, rtol=0)):
        raise ValueError('Parent bounds and cell metrics disagree')
    edges = []
    for axis in range(2):
        edge = list(range(0, int(counts[axis]), int(maximum[axis])))+[int(counts[axis])]
        # Do not create an unsupported one-cell last row: merge it with its
        # predecessor. The independent capacity check below still applies.
        if edge[-1]-edge[-2] == 1 and len(edge) > 2:
            edge.pop(-2)
        edges.append(np.asarray(edge, dtype=int))
    regions = []
    for j in range(len(edges[1])-1):
        for i in range(len(edges[0])-1):
            lo = np.array([edges[0][i], edges[1][j]])
            hi = np.array([edges[0][i+1], edges[1][j+1]])
            physical = np.r_[hi-lo, counts[2]]
            computational = physical+np.array([4, 4, 0])
            if np.prod(computational, dtype=np.int64)*8 > 2000000:
                raise ValueError('Regional reconstruction exceeds existing two-million-voxel cap')
            regions.append(dict(id=len(regions), cell_bounds_xy=[lo.tolist(), hi.tolist()],
                physical_cells=physical.tolist(), computational_cells=computational.tolist(),
                computational_extents_m=(computational*spacing).tolist(),
                bounds_station_lateral_m=(bounds[0]+np.array([lo, hi])*spacing[:2]).tolist()))
    # Each interface is represented ONCE with two equal-and-opposite owners.
    interfaces = []
    nx = len(edges[0])-1
    for r in regions:
        i, j = r['id'] % nx, r['id'] // nx
        for axis, neighbor, exists in ((0, r['id']+1, i+1 < nx),
                                        (1, r['id']+nx, j+1 < len(edges[1])-1)):
            if exists:
                interfaces.append(dict(id=len(interfaces), axis=axis, lower_region=r['id'], upper_region=neighbor,
                    parent_face_index=r['cell_bounds_xy'][1][axis],
                    tangential_cell_range=[r['cell_bounds_xy'][0][1-axis], r['cell_bounds_xy'][1][1-axis]],
                    coupling='shared-pressure-velocity-and-particle-transfer', native_source_emission=False))
    return regions, interfaces


def owners(positions_sl_m, regions):
    """Half-open ownership; the parent upper face belongs to the last region.

    Deliberately no clamp or nearest-region fallback for escaped particles.
    The runtime must account for outlet particles instead of losing them here.
    """
    points = np.asarray(positions_sl_m, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError('Finite station/lateral points required')
    outer = np.max([r['bounds_station_lateral_m'][1] for r in regions], axis=0)
    result = np.full(len(points), -1, dtype=np.int32)
    for r in regions:
        lo, hi = np.asarray(r['bounds_station_lateral_m'])
        inside = np.all((points >= lo) & ((points < hi) | ((hi == outer) & (points == hi))), axis=1)
        if np.any(result[inside] != -1):
            raise ValueError('Region overlap duplicates water ownership')
        result[inside] = r['id']
    if np.any(result < 0):
        raise ValueError('Water outside declared parent coverage; no silent deletion or clamping')
    return result


def split_state(window, source, initial, axes, max_xy=(128, 64)):
    if (source.get('schema') != 'raftsim.native_face_liquid_source.v2' or
            initial.get('schema') != 'raftsim.registered_liquid_initial_state.v2' or
            source['domain'] != initial['domain'] or
            source['source_geometry_sha256'] != window['source_geometry_sha256'] or
            initial['source_geometry_sha256'] != window['source_geometry_sha256'] or
            source['solid_sha256'] != window['solid_sha256']):
        raise ValueError('Matching full-domain source, initial state and geometry required')
    rotation = np.asarray(axes, dtype=float).T
    if rotation.shape != (2, 2) or not np.isfinite(rotation).all() or not np.allclose(rotation.T@rotation, np.eye(2), atol=1e-9, rtol=0) or np.linalg.det(rotation) < 0:
        raise ValueError('Explicit right-handed canonical ENU axes required')
    domain = source['domain']
    volume = float(domain['nominal_particle_volume_m3'])
    if not np.isfinite(volume) or volume <= 0 or source['nominal_particle_volume_m3'] != volume or initial['nominal_particle_volume_m3'] != volume:
        raise ValueError('Inlet and seed particle volume mismatch')
    regions, interfaces = partition(domain, max_xy)
    spacing = np.asarray(domain['cell_size_m'], dtype=float)
    if (not np.isclose(volume, np.prod(spacing)/4, atol=1e-12, rtol=0) or
            not np.allclose(domain['physical_extents_m'], np.asarray(domain['physical_cells'])*spacing, atol=1e-9, rtol=0)):
        raise ValueError('Particle volume or physical extent disagrees with cell metric')
    points = np.asarray(initial['positions_world_cm'], dtype=float)
    velocity = np.asarray(initial['velocities_world_cm_per_s'], dtype=float)
    origin = np.asarray(window['local_origin_engine_cm'], dtype=float)
    expected_xy = np.asarray(domain['centre_station_lateral_m'])@rotation.T*100
    if origin.shape != (3,) or not np.isfinite(origin).all() or not np.allclose(origin[:2], expected_xy, atol=1e-7, rtol=0):
        raise ValueError('Source-offset origin is not the declared canonical parent frame')
    source_points = np.asarray(source['positions_world_offset_cm'], dtype=float)+origin
    source_velocity = np.asarray(source['velocities_world_cm_per_s'], dtype=float)
    weights = np.asarray(source['weights_m3_per_s'], dtype=float)
    for p, v in ((points, velocity), (source_points, source_velocity)):
        if p.ndim != 2 or p.shape[1] != 3 or v.shape != p.shape or not np.isfinite(p).all() or not np.isfinite(v).all():
            raise ValueError('Matching finite position/velocity triples required')
        if np.any(p[:, 2] <= origin[2]) or np.any(p[:, 2] >= origin[2]+domain['physical_extents_m'][2]*100):
            raise ValueError('Water outside declared vertical volume')
    if (weights.shape != (len(source_points),) or not np.isfinite(weights).all() or (weights <= 0).any() or
            not np.isclose(weights.sum(), source['total_inflow_m3_per_s'], atol=1e-9, rtol=0) or
            not np.isclose(weights.sum()/volume, source['requested_spawn_particles_per_second'], atol=1e-7, rtol=0) or
            len(points) != initial['particle_count']):
        raise ValueError('Source discharge, rate or seed count mismatch')
    seed_owner = owners(points[:, :2]@rotation/100, regions)
    source_owner = owners(source_points[:, :2]@rotation/100, regions)
    bundles = []
    for r in regions:
        ids = np.flatnonzero(seed_owner == r['id'])
        sources = np.flatnonzero(source_owner == r['id'])
        if len(ids) > 163840:
            raise ValueError('Regional seeds exceed existing burst capacity; subdivide without dropping identities')
        center = np.mean(r['bounds_station_lateral_m'], axis=0)@rotation.T*100
        bundles.append(dict(schema='raftsim.regional_liquid_state.v1', **r,
            canonical_frame='parent-ENU-centimetres', origin_canonical_cm=[*center.tolist(), float(origin[2])],
            axis_x_canonical=rotation[:, 0].tolist(), axis_y_canonical=rotation[:, 1].tolist(),
            nominal_particle_volume_m3=volume, seed_parent_ids=ids.tolist(),
            positions_canonical_cm=points[ids].tolist(), velocities_canonical_cm_per_s=velocity[ids].tolist(),
            source_parent_ids=sources.tolist(), source_positions_canonical_cm=source_points[sources].tolist(),
            source_velocities_canonical_cm_per_s=source_velocity[sources].tolist(),
            source_weights_m3_per_s=weights[sources].tolist(),
            external_inflow_m3_per_s=float(weights[sources].sum()),
            external_spawn_particles_per_second=float(weights[sources].sum()/volume),
            internal_source_emission=False, runtime_coupling_verified=False))
    return bundles, dict(schema='raftsim.regional_liquid_ownership.v1', domain=domain,
        region_count=len(regions), interfaces=interfaces, particle_count=len(points),
        source_count=len(source_points), represented_nominal_volume_m3=len(points)*volume,
        external_inflow_m3_per_s=float(weights.sum()),
        max_region_seeds=max(len(b['seed_parent_ids']) for b in bundles),
        max_region_render_voxels=max(int(np.prod(r['computational_cells'])*8) for r in regions),
        geometry_source_sha256=window['source_geometry_sha256'], solid_sha256=window['solid_sha256'],
        initial_state_applied_once_required=True, internal_interfaces_are_not_reservoirs=True,
        runtime_coupling_verified=False, full_rapid_gpu_or_visual_acceptance=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--max-cells', type=int, nargs=2, default=(128, 64))
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Keep previous regional evidence')
    read = lambda name: json.loads((args.parent/name).read_text())
    window, source, initial = (read(n) for n in ('manifest.json', 'native_source_profile.json', 'hydraulic_initial_state.json'))
    boundary = read('grid_boundary_profile.json')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if initial['native_source_profile_sha256'] != sha(args.parent/'native_source_profile.json'):
        raise ValueError('Initial state references different source bytes')
    bundles, report = split_state(window, source, initial, [v[:2] for v in boundary['packed_vectors'][:2]], args.max_cells)
    report['parent_files_sha256'] = {n: sha(args.parent/n) for n in
        ('manifest.json', 'native_source_profile.json', 'hydraulic_initial_state.json', 'grid_boundary_profile.json')}
    args.output.mkdir(parents=True)
    report['region_files'] = []
    for bundle in bundles:
        path = args.output/f"region-{bundle['id']:03d}.json"
        path.write_text(json.dumps(bundle, separators=(',', ':'), allow_nan=False)+'\n')
        report['region_files'].append(dict(file=path.name, sha256=sha(path)))
    (args.output/'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('domain', 'interfaces', 'region_files', 'parent_files_sha256')}, indent=2))


if __name__ == '__main__':
    main()
