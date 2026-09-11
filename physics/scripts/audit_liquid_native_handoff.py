"""Verify actual native writes and next-step particle ownership, not staging."""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_liquid_particle_routes import physical_owners
from audit_liquid_particle_handles import verify_handles
from audit_liquid_particle_identity import audit as audit_identity


def compare_native_steps(before, after, later, birth_planes, id_planes, position_planes, require_change=True, allow_births=False):
    def index(owners):
        result = {}
        for owner, words in owners.items():
            if words.dtype != np.dtype('<u4') or words.ndim != 2:
                raise ValueError('Exact native word planes required')
            for i in range(words.shape[1]):
                key = tuple(map(int, words[birth_planes, i]))
                if key in result:
                    raise ValueError('Duplicated native birth identity')
                result[key] = (owner, words[:, i])
        return result
    b, a, n = (index(x) for x in (before, after, later))
    if not b or b.keys() != a.keys() or (not a.keys() <= n.keys() if allow_births else a.keys() != n.keys()):
        raise ValueError('Native commit or following step lost/added/relabelled particles')
    moved = 0
    for key in b:
        if a[key][0] != n[key][0] or not np.array_equal(a[key][1][id_planes], n[key][1][id_planes]):
            raise ValueError('Native next step lost receiving ownership or persistent handles')
        moved += not np.array_equal(a[key][1][position_planes], n[key][1][position_planes])
    changed = sum(b[k][0] != a[k][0] for k in b)
    if (require_change and changed == 0) or moved == 0:
        raise ValueError('Actual ownership change followed by native motion required')
    return dict(bounded_native_handoff_verified=True, particles=len(b), native_owner_changes=changed,
                particles_moving_on_following_step=moved, sustained_flow_or_visual_performance_acceptance=False)


def read(root, record, key, shape):
    path = (root/record[key]).resolve()
    if path.parent != root.resolve():
        raise ValueError('Snapshot path outside expected directory')
    return np.fromfile(path, dtype='<u4').reshape(shape)


def native_snapshot(directory, handoff, phase):
    components = handoff['float_components']+handoff['int_components']
    if [r['owner'] for r in handoff[phase]] != list(range(12)):
        raise ValueError('Incomplete native before/after owners')
    target = {}
    for r in handoff[phase]:
        counts = read(directory, r, 'counts', (15,))
        n = int(counts[-1])
        if n > r['capacity'] or counts[-2] or counts[-3] or counts[:-3].sum() != n:
            raise ValueError('Invalid native before/after count or exterior particle')
        target[r['owner']] = read(directory, r, 'words', (components, r['capacity']))[:, :n]
    return target


def verify_empty_receiver(records, before, later, per_owner, new_births=0):
    # Intentionally omit only owner 0's initial packet, not an arbitrary count
    # deficit. Verify actual birth readback, not the requested seed metadata alone.
    if per_owner not in (1, 2, 3, 4) or set(before) != set(range(12)) or set(later) != set(range(12)):
        raise ValueError('Complete bounded empty-receiver packet required')
    for r in records:
        expected = per_owner if r['region_id'] in (1, 4, 5) else 0
        if r['birth_particle_count'] != expected or r['expected_count'] != expected:
            raise ValueError('Initially empty receiver birth packet differs from requested sources')
    if before[0].shape[1] or later[0].shape[1] == 0:
        raise ValueError('Actual empty-to-nonempty native receiver required')
    if new_births < 0 or sum(w.shape[1] for w in later.values()) != 3*per_owner+new_births:
        raise ValueError('Empty receiver lost or invented particles')
    return dict(initially_empty_receiver_verified=True, receiving_owner=0,
                received_particles=later[0].shape[1])


def verify_commit(directory, handoff, records, later, regions, require_change, allow_births=False):
    if not handoff['issued']:
        raise ValueError('Native commit was not issued')
    nf, ni = handoff['float_components'], handoff['int_components']
    components = nf+ni
    identity = records[0]['route_identity_offsets']
    index_plane = nf+handoff['id_component']
    position = records[0]['route_position_offset']
    before = native_snapshot(directory, handoff, 'before')
    after = native_snapshot(directory, handoff, 'after')
    for r in records:
        if (r['route_identity_offsets'] != identity or r['route_position_offset'] != position or
                r['route_float_components'] != nf or r['route_int_components'] != ni):
            raise ValueError('Native word layout changed across owners/steps')
    receiving = handoff['receiving'];root = directory/'handoff-receiving'
    caps, total = receiving['destination_capacities'], receiving['total_capacity']
    id_caps = receiving.get('id_capacities', caps);total_ids = sum(id_caps)
    words = read(root, receiving, 'words', (components, total))
    refs = read(root, receiving, 'references', (total, 2))
    counts = read(root, receiving, 'counts', (12,))
    handles = read(root, receiving, 'handles', (total, 2))
    control = read(root, receiving, 'control', (4,))
    if not np.array_equal(control, [1, 0, sum(x.shape[1] for x in before.values()), 0]):
        raise ValueError('Native commit transaction gate failed')
    verify_handles(caps, counts, words, refs, handles, read(root, receiving, 'id_to_index', (total_ids,)),
                   read(root, receiving, 'free_ids', (total_ids,)), read(root, receiving, 'free_counts', (12,)),
                   index_plane, receiving['transfer_epoch'], id_caps)
    expected = {s: physical_owners(w[position:position+3].T.copy().view('<f4'), regions) for s, w in before.items()}
    seen, offset = set(), 0
    for owner, capacity in enumerate(caps):
        n = int(counts[owner])
        if after[owner].shape[1] != n:
            raise ValueError('Actual native live count differs from receiving count')
        for i in range(n):
            s, j = map(int, refs[offset+i])
            if s not in before or j >= before[s].shape[1] or (s, j) in seen or expected[s][j] != owner:
                raise ValueError('Native commit duplicated or misrouted a particle')
            seen.add((s, j))
            if not np.array_equal(words[:, offset+i], before[s][:, j]):
                raise ValueError('Precommit assembly changed native source payload')
            required = words[:, offset+i].copy();required[index_plane:index_plane+2] = handles[offset+i]
            if not np.array_equal(after[owner][:, i], required):
                raise ValueError('Native commit payload differs beyond permitted local-ID remapping')
        offset += capacity
    if len(seen) != sum(x.shape[1] for x in before.values()):
        raise ValueError('Native commit omitted source particles')
    return compare_native_steps(before, after, later, [nf+identity[0], nf+identity[1]],
                                [index_plane, index_plane+1], list(range(position, position+3)), require_change, allow_births)


def audit(directory, prepared=None):
    directory = Path(directory).resolve()
    log = directory.with_suffix('.log').read_text(errors='replace')
    if '-RHIValidation' not in log or any(x in log for x in ('LogRHI: Error', 'Fatal error:', 'GPU Crashed')):
        raise ValueError('Native handoff requires a clean RHI-validated replay log')
    if prepared is None:
        prepared = Path(__file__).resolve().parents[2]/'tmp/south-fork-liquid-regional-state-20260910'
    report = json.loads((directory/'stages.json').read_text())
    if report.get('native_compact_handoff_requested'):
        raise ValueError('Compact telemetry is not an exact native handoff history')
    if report.get('simulation_generation'):
        from audit_liquid_native_generation import verify_generation
        verify_generation(report)
    if report.get('native_particle_retirement_requested'):
        raise ValueError('Native retirement requires an explicit survivor/exit ledger audit, not the closed-population handoff audit')
    capture = json.loads((directory/'capture.json').read_text())
    if (not capture['complete'] or report['exchange_error'] or not report['native_transfer_packet_saved'] or
            not report.get('native_particle_handoff_requested') or report['native_transfer_packet_step'] < 4):
        raise ValueError('Successful live handoff and subsequent native snapshot required')
    if report.get('native_emission_requested'):
        from audit_liquid_native_emission import audit_emission
        return audit_emission(directory, prepared, report)
    history = report.get('native_particle_handoff_history', [report['native_particle_handoff']])
    if not history or len(history) != report.get('native_particle_handoff_count', 1):
        raise ValueError('Missing native commit history')
    if [h['native_step'] for h in history] != list(range(2, 2+len(history))):
        raise ValueError('Native commit history must cover every requested consecutive step')
    if [h['receiving']['transfer_epoch'] for h in history] != list(range(1, 1+len(history))):
        raise ValueError('Native transfer epochs reused or skipped')
    if report['native_transfer_packet_step'] < history[-1]['native_step']+2:
        raise ValueError('Completed native motion after final commit required')
    roots = [(directory/h.get('snapshot_directory', '')).resolve() for h in history]
    if len(set(roots)) != len(roots) or any(r != directory and r.parent != directory for r in roots):
        raise ValueError('Commit history directories invalid or duplicated')
    records = report['native_transfer_packet']
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve native owners required')
    nf, ni = history[0]['float_components'], history[0]['int_components']
    if any((h['float_components'], h['int_components'], h['id_component']) !=
           (nf, ni, history[0]['id_component']) for h in history):
        raise ValueError('Native dataset ABI changed during commit history')
    later = {r['region_id']: read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))[:, :r['particle_count']]
             for r in records}
    regions = [json.loads((Path(prepared)/f'region-{i:03d}.json').read_text()) for i in range(12)]
    results = []
    for i, h in enumerate(history):
        following = native_snapshot(roots[i+1], history[i+1], 'before') if i+1 < len(history) else later
        results.append(verify_commit(roots[i], h, records, following, regions, require_change=i == 0))
    identity = records[0]['route_identity_offsets'];position = records[0]['route_position_offset']
    index = nf+history[0]['id_component']
    net = compare_native_steps(native_snapshot(roots[0], history[0], 'before'),
                               native_snapshot(roots[-1], history[-1], 'after'), later,
                               [nf+identity[0], nf+identity[1]], [index, index+1],
                               list(range(position, position+3)), require_change=False)
    if audit_identity(directory)['observed_owner_changes'] != net['native_owner_changes']:
        raise ValueError('Birth-to-next-step owner evidence differs from native commits')
    net.update(verified_native_commits=len(history),
               owner_changes_per_commit=[r['native_owner_changes'] for r in results],
               following_step_counts={s: w.shape[1] for s, w in later.items()})
    if report.get('native_empty_receiver_requested'):
        net.update(verify_empty_receiver(records, native_snapshot(roots[0], history[0], 'before'),
                                         later, report['native_transfer_packet_per_owner']))
    return net


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path);parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
