"""Audit full-state GPU routing candidates against physical prepared regions.

This verifies staging, never claims particles have been imported into a new
Niagara dataset. The reference uses canonical station/lateral region bounds,
not the GPU's uploaded cell routing table.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_native_ownership import prepared_float_frame_owners


def physical_owners(world_positions, regions):
    points = np.asarray(world_positions, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('Finite Nx3 world positions required')
    canonical = points * [1, -1, 1]
    bounds = np.array([r['bounds_station_lateral_m'] for r in regions], dtype=float)
    upper = bounds[:, 1].max(axis=0)
    result = np.full(len(points), -1, dtype=np.int64)
    for r in regions:
        axes = np.array([r['axis_x_canonical'], r['axis_y_canonical']], dtype=float)
        if axes.shape not in ((2, 2), (2, 3)) or not np.isfinite(axes).all():
            raise ValueError('Finite horizontal canonical frame required')
        if axes.shape == (2, 3) and np.any(axes[:, 2]):
            raise ValueError('Physical region bounds require horizontal axes')
        q = canonical[:, :2] @ axes[:, :2].T / 100
        b = np.array(r['bounds_station_lateral_m'])
        inside = ((q >= b[0]) & ((q < b[1]) | ((b[1] == upper) & (q <= b[1])))).all(axis=1)
        if np.any(inside & (result >= 0)):
            raise ValueError('Overlapping physical owners')
        result[inside] = int(r['id'])
    return result


def storage_owners(world_positions,regions,frame_model=None):
    """Exact declared native storage frame, with survey exterior checks intact.

    Returns both owner arrays so internal-cut precision differences remain
    visible. Never uses observed GPU destinations or a distance tolerance.
    """
    survey=physical_owners(world_positions,regions)
    if frame_model is None:return survey,survey
    if frame_model not in ('double-float-demote-v1','double-float-residual-outer-v2'):
        raise ValueError('Unknown native ownership coordinate contract')
    uploaded=prepared_float_frame_owners(world_positions,regions,
        residual_outer=frame_model=='double-float-residual-outer-v2')[0]
    if np.any((survey<0)&(uploaded>=0)):
        raise ValueError('Native storage frame cannot expand physical survey exterior')
    return uploaded,survey


def verify_packet(record, words, routes, counts, positions, velocities, identities, expected_owners, owners=12):
    n, capacity = record['particle_count'], record['particle_capacity']
    nf, ni = record['route_float_components'], record['route_int_components']
    if words.dtype != np.dtype('<u4') or words.shape != (nf+ni, capacity):
        raise ValueError('Exact full native word planes required')
    if routes.shape != (n, 4) or counts.shape != (owners+3,) or len(expected_owners) != n:
        raise ValueError('Incomplete native route accounting')
    if positions.shape != (n, 4) or velocities.shape != (n, 4) or identities.shape != (n, 4):
        raise ValueError('Incomplete independent native snapshot')
    for key, reference in (('route_position_offset', positions), ('route_velocity_offset', velocities)):
        offset = record[key]
        if not 0 <= offset <= nf-3:
            raise ValueError('Invalid native float component offset')
        if not np.array_equal(words[offset:offset+3, :n].T, reference[:, :3].copy().view('<u4')):
            raise ValueError('Particle float data changed during routing')
    offsets = record['route_identity_offsets']
    if len(offsets) != 4 or any(not 0 <= i < ni for i in offsets):
        raise ValueError('Invalid native integer identity offsets')
    if not np.array_equal(words[nf+np.array(offsets), :n].T, identities.copy().view('<u4')):
        raise ValueError('Particle identity bits changed during routing')
    expected = np.empty((n, 4), dtype='<u4')
    expected[:, 0] = np.where(expected_owners >= 0, expected_owners, 0xffffffff)
    expected[:, 1] = record['region_id']
    expected[:, 2] = np.arange(n)
    expected[:, 3] = np.where(expected_owners >= 0, 1, 2)
    if not np.array_equal(routes, expected):
        raise ValueError('GPU routes differ from independent physical owners')
    accounting = np.zeros(owners+3, dtype='<u4')
    for owner in expected_owners:
        accounting[owner if owner >= 0 else owners] += 1
    accounting[-1] = n
    if not np.array_equal(counts, accounting):
        raise ValueError('Lost, duplicated, invalid, or miscounted route record')
    if np.any(words[:, n:]):
        raise ValueError('Inactive capacity contains stale payload')
    return int(np.count_nonzero((expected_owners >= 0) & (expected_owners != record['region_id'])))


def audit(directory, prepared):
    directory, prepared = Path(directory).resolve(), Path(prepared).resolve()
    capture = json.loads((directory/'capture.json').read_text())
    report = json.loads((directory/'stages.json').read_text())
    if (not capture['complete'] or report['exchange_error'] or report['zero_water'] or
            not report['native_transfer_packet_saved'] or not report['native_particle_routes_requested']):
        raise ValueError('Successful actual native routing capture required')
    records = report['native_transfer_packet']
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve native owners required')
    regions = [json.loads((prepared/f'region-{i:03d}.json').read_text()) for i in range(12)]
    crossings = live = 0
    destinations = []
    for r in records:
        def read(key, dtype, shape):
            path = (directory/r[key]).resolve()
            if path.parent != directory:
                raise ValueError('Snapshot outside capture directory')
            return np.fromfile(path, dtype=dtype).reshape(shape)
        n = r['particle_count']
        p, v = (read(k, '<f4', (n, 4)) for k in ('positions', 'velocities'))
        ids = read('identities', '<i4', (n, 4))
        words = read('route_words', '<u4', (r['route_float_components']+r['route_int_components'], r['particle_capacity']))
        routes = read('route_destinations', '<u4', (n, 4))
        counts = read('route_counts', '<u4', (15,))
        expected = physical_owners(p[:, :3], regions)
        if np.any(expected < 0):
            raise ValueError('Bounded native crossing fixture unexpectedly exited physical domain')
        crossings += verify_packet(r, words, routes, counts, p, v, ids, expected)
        destinations.extend(dict(source=r['region_id'], index=i, destination=int(o)) for i, o in enumerate(expected))
        live += n
    if crossings == 0:
        raise ValueError('Native particles must actually cross a physical region boundary')
    return dict(native_full_state_routing_staged=True, live_particles=live, physical_boundary_crossings=crossings,
                destinations=destinations, native_particle_handoff_verified=False,
                visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('prepared', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory, args.prepared)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
