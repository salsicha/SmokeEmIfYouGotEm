"""Verify native receiving-side GPU assembly, without claiming Niagara commit."""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_liquid_particle_routes import audit as audit_routes


def verify_assembly(sources, routes, capacities, words, references, counts, control):
    capacities = np.asarray(capacities, dtype=np.int64)
    owners = len(capacities)
    if sorted(sources) != list(range(owners)) or sorted(routes) != list(range(owners)):
        raise ValueError('Complete source owners required')
    if np.any(capacities <= 0) or words.dtype != np.dtype('<u4') or words.ndim != 2:
        raise ValueError('Bounded destinations and exact word planes required')
    total = sum(len(r) for r in routes.values())
    if control.shape != (4,) or not np.array_equal(control, [1, 0, total, 0]):
        raise ValueError('GPU transaction did not pass capacity and accounting checks')
    slots = int(capacities.sum())
    if words.shape[1] != slots or references.shape != (slots, 2) or counts.shape != (owners,):
        raise ValueError('Incomplete receiving buffers')
    expected = {(s, i) for s, r in routes.items() for i in range(len(r))}
    seen, offset, moved = set(), 0, 0
    for d, capacity in enumerate(capacities):
        n = int(counts[d])
        if n < 0 or n > capacity:
            raise ValueError('Destination capacity exceeded')
        for j in range(n):
            s, i = map(int, references[offset+j])
            key = (s, i)
            if key not in expected or key in seen:
                raise ValueError('Missing, invalid, or duplicated source particle')
            seen.add(key)
            if not np.array_equal(routes[s][i], [d, s, i, 1]):
                raise ValueError('Particle assembled into wrong physical destination')
            if sources[s].dtype != np.dtype('<u4') or not np.array_equal(words[:, offset+j], sources[s][:, i]):
                raise ValueError('Full native particle payload changed in destination assembly')
            moved += s != d
        if np.any(words[:, offset+n:offset+capacity]) or np.any(references[offset+n:offset+capacity] != 0xffffffff):
            raise ValueError('Stale payload or source reference outside live destination range')
        offset += capacity
    if seen != expected:
        raise ValueError('Source particles missing from receiving assembly')
    return dict(receiving_gpu_assembly_verified=True, assembled_particles=total, cross_owner_particles=moved,
                all_native_word_planes_bit_exact=True, native_particle_handoff_verified=False,
                sustained_flow_or_visual_performance_acceptance=False)


def audit(directory, prepared):
    directory = Path(directory).resolve()
    routing = audit_routes(directory, prepared)
    report = json.loads((directory/'stages.json').read_text())
    if not report['native_particle_assembly_requested']:
        raise ValueError('Actual native assembly capture required')
    a = report['native_particle_assembly']
    if a['native_committed']:
        raise ValueError('Staging auditor cannot certify native commit')
    def read(record, key, shape):
        path = (directory/record[key]).resolve()
        if path.parent != directory:
            raise ValueError('Invalid receiving snapshot path')
        return np.fromfile(path, dtype='<u4').reshape(shape)
    sources, routes = {}, {}
    components = a['float_components']+a['int_components']
    for r in report['native_transfer_packet']:
        if r['route_float_components'] != a['float_components'] or r['route_int_components'] != a['int_components']:
            raise ValueError('Native ABI changed across owners')
        sources[r['region_id']] = read(r, 'route_words', (components, r['particle_capacity']))
        routes[r['region_id']] = read(r, 'route_destinations', (r['particle_count'], 4))
    result = verify_assembly(sources, routes, a['destination_capacities'],
                             read(a, 'words', (components, a['total_capacity'])),
                             read(a, 'references', (a['total_capacity'], 2)),
                             read(a, 'counts', (len(sources),)), read(a, 'control', (4,)))
    if result['cross_owner_particles'] != routing['physical_boundary_crossings']:
        raise ValueError('Physical crossings differ from assembled exchanges')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path);parser.add_argument('prepared', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory, args.prepared)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
