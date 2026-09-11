"""Independently audit native survivor/exit transactions against prepared geometry.

This bounded outlet replay is not dense-flow or visual acceptance.
The reference intersects actual native segments in float64, not GPU exit rows.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_liquid_native_handoff import read
from audit_liquid_native_segments import verify_origins
from audit_liquid_particle_handles import verify_handles
from audit_liquid_particle_routes import physical_owners, verify_packet


def crossing(start, end, profile, bed_query=None):
    """Return face, row, fraction and a float32 forward-error bound."""
    packed = np.asarray(profile['packed_vectors'], dtype=np.float64)
    axes = packed[:2]
    bounds = np.asarray(profile['domain']['native_face_bounds_m'], dtype=float)*100
    floor = packed[2, 2]
    def local(p):
        canonical = np.asarray(p, dtype=float)*[1, -1, 1]
        return np.r_[axes[:, :2] @ canonical[:2]-bounds[0], canonical[2]-floor]
    a, b = local(start), local(end)
    extent = packed[3]
    if not np.isfinite([a, b]).all() or np.any(a < 0) or np.any(a > extent):
        raise ValueError('Invalid or exterior segment origin')
    if np.all((b >= 0) & (b <= extent)):
        return None
    hits = []
    for axis in range(3):
        if b[axis] < 0 or b[axis] > extent[axis]:
            high = b[axis] > extent[axis]
            t = ((extent[axis] if high else 0)-a[axis])/(b[axis]-a[axis])
            hits.append((float(t), 2*axis+int(high)))
    hits.sort()
    t, face = hits[0]
    if (face >= 4 or not 0 <= t <= 1 or
            (len(hits) > 1 and abs(hits[1][0]-t) <= 8*np.finfo(np.float32).eps)):
        raise ValueError('Floor, roof or ambiguous corner crossing')
    hit = a+t*(b-a)
    tangent = 1 if face < 2 else 0
    cells = packed[5].astype(int)
    column = min(max(int(np.floor(hit[tangent]/packed[4, tangent])), 0), cells[tangent]-1)
    row = [0, cells[1], 2*cells[1], 2*cells[1]+cells[0]][face]+column
    bed, stage, inward = packed[8+row]
    if bed_query is not None:
        bed=float(bed_query(face,hit[tangent]))
        if not np.isfinite(bed):raise ValueError('Invalid pointwise terrain bed')
    if inward >= 0 or stage <= bed or hit[2]+floor <= bed:
        raise ValueError('Dry, below-bed or non-outgoing parent face')
    # Bound the GPU's float32 parameter rounding, subtract/dot and division.
    # This is derived from the original frame and actual segment, never fitted
    # to the observed crossing. Topological face/row agreement remains exact.
    world_axes = np.vstack((axes*[1, -1, 1], [0, 0, 1]))
    lower = (axes.T @ bounds[0]+[0, 0, floor])*[1, -1, 1]
    basis32 = world_axes.astype('<f4').astype(float)
    lower32 = lower.astype('<f4').astype(float)
    u = 2.0**-24
    gamma6 = 6*u/(1-6*u)
    endpoint_errors = []
    axis = face//2
    for p, exact in ((start, a), (end, b)):
        p = np.asarray(p, dtype=float)
        rounded_parameters = basis32 @ (p-lower32)
        error = abs(rounded_parameters[axis]-exact[axis])
        error += gamma6*(abs(basis32[axis]) @ (abs(p)+abs(lower32)))
        endpoint_errors.append(error)
    ea, eb = endpoint_errors
    delta = abs(b[axis]-a[axis])
    if delta <= ea+eb:
        raise ValueError('Ill-conditioned crossing cannot be certified')
    extent_error = u*extent[axis] if face % 2 else 0
    fraction_error = (extent_error+ea+abs(t)*(ea+eb))/(delta-ea-eb)+3*u/(1-3*u)*abs(t)
    return face, row, t, fraction_error


def indexed(owners, birth):
    result = {}
    for owner, words in owners.items():
        if words.dtype != np.dtype('<u4') or words.ndim != 2:
            raise ValueError('Exact native words required')
        for w in words.T:
            key = tuple(map(int, w[birth]))
            if key in result:
                raise ValueError('Duplicated birth identity')
            result[key] = (owner, w)
    return result


def verify_population(current, known, retired, expected_births, unique_plane):
    """Account for births and prior exits without allowing either to hide losses."""
    if not known-retired <= current.keys() or retired & current.keys():
        raise ValueError('Lost or resurrected native particle')
    new = current.keys()-known
    actual = {owner: sum(k[0] == owner for k in new) for owner in expected_births}
    if actual != expected_births or any(k[0] not in expected_births for k in new):
        raise ValueError('Native births differ from independent spawn plan')
    for key, (owner, words) in current.items():
        if int(words[unique_plane]) != key[1] or (key in new and owner != key[0]):
            raise ValueError('Native birth unique ID or initial owner differs')
    for owner, count in expected_births.items():
        previous = sum(k[0] == owner for k in known)
        if sorted(k[1] for k in new if k[0] == owner) != list(range(previous, previous+count)):
            raise ValueError('Native birth sequence skipped, reset or relabelled')
    return set(new)


def snapshot(directory, h, phase, regions, position):
    owners = len(regions)
    if [r['owner'] for r in h[phase]] != list(range(owners)):
        raise ValueError('Incomplete native owners')
    target = {}
    for r in h[phase]:
        counts = read(directory, r, 'counts', (owners+3,))
        n = int(counts[-1])
        if n > r['capacity'] or counts[-2] or counts[:-2].sum() != n:
            raise ValueError('Invalid native count accounting')
        w = read(directory, r, 'words', (h['float_components']+h['int_components'], r['capacity']))[:, :n]
        expected = physical_owners(w[position:position+3].T.copy().view('<f4'), regions)
        required = np.zeros(owners+3, dtype='<u4')
        for dest in expected:
            required[dest if dest >= 0 else owners] += 1
        required[-1] = n
        if not np.array_equal(counts, required) or (phase == 'after' and np.any(expected != r['owner'])):
            raise ValueError('Native route counts or committed ownership differ from geometry')
        target[r['owner']] = w
    return target


def verify_partition(before, after, words, refs, counts, caps, handles, exit_words,
                     exit_refs, exit_records, exit_counts, exit_caps, control,
                     destinations, classify, position, start, index_plane):
    """Verify all source words appear exactly once in survivors OR approved exits."""
    nsource = sum(w.shape[1] for w in before.values())
    if (len(caps) != len(before) or len(exit_caps) != len(before) or
            exit_counts.shape != (len(before), 5) or
            not np.array_equal(control, [1, 0, nsource, int(exit_counts[:, 4].sum())])):
        raise ValueError('Native retirement transaction gate/counts failed')
    seen, retired, changed = set(), [], 0
    def source(ref, payload):
        s, j = map(int, ref)
        if s not in before or j >= before[s].shape[1] or (s, j) in seen:
            raise ValueError('Duplicated or invalid source reference')
        if not np.array_equal(payload, before[s][:, j]):
            raise ValueError('Source payload changed during partition')
        seen.add((s, j))
        return s, j
    offset = 0
    for owner, cap in enumerate(caps):
        n = int(counts[owner])
        if n > cap or after[owner].shape[1] != n:
            raise ValueError('Native survivor count differs from assembly')
        for i in range(n):
            k = offset+i
            s, j = source(refs[k], words[:, k])
            w = before[s][:, j]
            if destinations[s][j] != owner or classify(w[start:start+3].view('<f4'), w[position:position+3].view('<f4')) is not None:
                raise ValueError('Exterior or misrouted survivor')
            required = words[:, k].copy()
            required[index_plane:index_plane+2] = handles[k]
            if not np.array_equal(after[owner][:, i], required):
                raise ValueError('Native survivor payload differs beyond local handles')
            changed += s != owner
        offset += cap
    offset = 0
    for owner, cap in enumerate(exit_caps):
        n = int(exit_counts[owner, 4])
        if n > cap or int(exit_counts[owner, :4].sum()) != n:
            raise ValueError('Exit face counts do not partition retired particles')
        faces = np.zeros(4, dtype='<u4')
        for i in range(n):
            k = offset+i
            s, j = source(exit_refs[k], exit_words[:, k])
            if s != owner or destinations[s][j] != -1:
                raise ValueError('Retired particle was not exterior to its physical parent')
            w = before[s][:, j]
            expected = classify(w[start:start+3].view('<f4'), w[position:position+3].view('<f4'))
            status, face, row, time_bits = exit_records[k]
            t = np.array(time_bits, dtype='<u4').view('<f4').item()
            if (expected is None or status != 2 or face != expected[0] or row != expected[1] or
                    not np.isfinite(t) or not 0 <= t <= 1 or abs(t-expected[2]) > expected[3]):
                raise ValueError(f'Exit crossing differs from independent segment/face reference: source={s}, particle={j}, '
                                 f'observed={(int(status), int(face), int(row), t)}, expected={expected}')
            faces[int(face)] += 1
            retired.append((s, j, int(face), int(row), float(t)))
        if not np.array_equal(faces, exit_counts[owner, :4]):
            raise ValueError('Ledger face histogram differs from counts')
        offset += cap
    if len(seen) != nsource:
        raise ValueError('Source particle omitted from survivor/exit partition')
    return retired, changed


def audit(directory, prepared=None, boundary=None, log_path=None):
    directory = Path(directory).resolve()
    repo = Path(__file__).resolve().parents[2]
    prepared = Path(prepared or repo/'tmp/south-fork-liquid-regional-state-20260910')
    boundary = Path(boundary or repo/'tmp/south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json')
    log = Path(log_path or directory.with_suffix('.log')).read_text(errors='replace')
    if '-RHIValidation' not in log or any(x in log for x in ('LogRHI: Error', 'Fatal error:', 'GPU Crashed')):
        raise ValueError('Clean RHI-validated replay required')
    report = json.loads((directory/'stages.json').read_text())
    if report.get('native_compact_handoff_requested'):
        raise ValueError('Compact telemetry is not an exact survivor/exit history')
    if report.get('simulation_generation'):
        from audit_liquid_native_generation import verify_generation
        verify_generation(report)
    capture = json.loads((directory/'capture.json').read_text())
    if (not capture['complete'] or report['exchange_error'] or not report['native_transfer_packet_saved'] or
            not report.get('native_particle_retirement_requested') or not report.get('native_particle_handoff_requested')):
        raise ValueError('Successful native outlet capture required')
    records, history = report['native_transfer_packet'], report['native_particle_handoff_history']
    owners = 12
    if [r['region_id'] for r in records] != list(range(owners)) or not history:
        raise ValueError('Complete native owner/history evidence required')
    if (len(history) != report['native_particle_handoff_count'] or
            [h['native_step'] for h in history] != list(range(2, 2+len(history))) or
            [h['receiving']['transfer_epoch'] for h in history] != list(range(1, 1+len(history))) or
            report['native_transfer_packet_step'] < history[-1]['native_step']+1):
        raise ValueError('Consecutive commits and continued native steps required')
    regions = [json.loads((prepared/f'region-{i:03d}.json').read_text()) for i in range(owners)]
    profile = json.loads(boundary.read_text())
    bounds = np.array([r['bounds_station_lateral_m'] for r in regions])
    if not np.array_equal([bounds[:, 0].min(axis=0), bounds[:, 1].max(axis=0)], profile['domain']['native_face_bounds_m']):
        raise ValueError('Prepared parent and outlet profile bounds differ')
    if any(not np.allclose([r['axis_x_canonical'], r['axis_y_canonical']], np.array(profile['packed_vectors'])[:2, :2], rtol=0, atol=1e-12) for r in regions):
        raise ValueError('Prepared parent and outlet frame differ')
    nf, ni, id_component = (history[0][k] for k in ('float_components', 'int_components', 'id_component'))
    position, start, identity = (records[0][k] for k in ('route_position_offset', 'route_step_start_offset', 'route_identity_offsets'))
    birth = [nf+i for i in identity[:2]]
    index_plane = nf+id_component
    initial = {}
    volume = {}
    for r, region in zip(records, regions):
        if (r['route_float_components'], r['route_int_components'], r['route_position_offset'], r['route_step_start_offset'], r['route_identity_offsets']) != (nf, ni, position, start, identity):
            raise ValueError('Native layout changed across regions')
        n = r['birth_particle_count']
        expected = report['native_transfer_packet_per_owner'] if r['region_id'] in (1, 4, 5, 7) else 0
        if not report.get('native_empty_receiver_requested') or n != expected or r['expected_count'] != expected:
            raise ValueError('Actual outlet/inner wet-seed fixture required')
        ids = read(directory, r, 'birth_identities', (n, 4))
        p = read(directory, r, 'birth_positions', (n, 4)).view('<f4')
        seeds = r['seed_parent_ids']
        if len(seeds) != n or len(set(seeds)) != n:
            raise ValueError('Missing/duplicated seed provenance')
        prepared_ids = {s: i for i, s in enumerate(region['seed_parent_ids'])}
        for ident, point in zip(ids, p):
            owner, sequence, unique = map(int, ident[:3])
            if owner != r['region_id'] or sequence >= n or unique != sequence or (owner, sequence) in initial:
                raise ValueError('Initial native birth identity differs')
            seed = seeds[sequence]
            if seed not in prepared_ids:
                raise ValueError('Initial particle is not a prepared wet seed')
            q = np.array(region['positions_canonical_cm'][prepared_ids[seed]], dtype='<f4')*[1, -1, 1]
            if not np.allclose(point[:3], q, rtol=0, atol=0.002):
                raise ValueError('Initial native position differs from original wet seed')
            initial[owner, sequence] = point[:3]
        v = float(np.float32(region['nominal_particle_volume_m3']))
        if not np.isfinite(v) or v <= 0 or np.float32(r['particle_volume_m3']) != v:
            raise ValueError('Invalid or changed native particle volume')
        volume[r['region_id']] = v
    if len(set(volume.values())) != 1:
        raise ValueError('This native fixture requires equal transferred particle volumes')
    emission = report.get('native_emission_requested', False)
    if emission and (not report['native_emission_activated'] or report['native_emission_rate'] != 60 or report['native_emission_start_step'] < 1):
        raise ValueError('Activated bounded source required')
    step = report['native_transfer_packet_step']
    groups = [g for g in report['groups'] if g['entries'][0]['first']][:step]
    if len(groups) != step:
        raise ValueError('Missing native first-stage spawn plan')
    planned = {}
    for s, g in enumerate(groups, 1):
        if (not g['complete'] or not g['aligned'] or sorted(e['owner'] for e in g['entries']) != list(range(owners)) or
                any(bool(e['reset']) != (s == 1) for e in g['entries'])):
            raise ValueError('Incomplete spawn schedule or unaccounted reset')
        planned[s] = {e['owner']: int(e['native_rate_spawns'])+int(e['native_event_spawns']) for e in g['entries']}
        if s == 1:
            if planned[s] != {o: sum(k[0] == o for k in initial) for o in range(owners)}:
                raise ValueError('Initial native births differ from spawn plan')
        elif any(v < 0 or v > (1 if emission and o == 1 else 0) for o, v in planned[s].items()):
            raise ValueError('Source emitted outside bounded native birth budget')
    roots = [(directory/h['snapshot_directory']).resolve() for h in history]
    if len(set(roots)) != len(roots) or any(r != directory and r.parent != directory for r in roots):
        raise ValueError('Invalid commit snapshot directories')
    retired_keys, ledger, changes = set(), [], []
    known = set(initial);previous_step = 1
    previous = None
    verified_segments = moving_segments = 0
    for root, h in zip(roots, history):
        if not h['issued'] or (h['float_components'], h['int_components'], h['id_component']) != (nf, ni, id_component):
            raise ValueError('Unissued commit or changed native ABI')
        before = snapshot(root, h, 'before', regions, position)
        after = snapshot(root, h, 'after', regions, position)
        b = indexed(before, birth)
        expected_births = {o: sum(planned[s][o] for s in range(previous_step+1, h['native_step']+1)) for o in range(owners)}
        known.update(verify_population(b, known, retired_keys, expected_births, nf+identity[2]))
        previous_step = h['native_step']
        if previous is not None:
            evidence = verify_origins(previous, before, birth, position, start, nf)
            verified_segments += evidence['verified_segments'];moving_segments += evidence['moving_segments']
        a = h['receiving'];d = root/'handoff-receiving'
        caps, total = a['destination_capacities'], a['total_capacity']
        ecaps, etotal = a['exit_source_capacities'], a['total_exit_capacity']
        if (not a['exit_ledger_prepared'] or total != sum(caps) or etotal != sum(ecaps) or
                ecaps != [r['capacity'] for r in h['before']] or
                a['exit_particle_volumes_m3'] != [volume[i] for i in range(owners)]):
            raise ValueError('Exit capacity/volume evidence differs from native source')
        words = read(d, a, 'words', (nf+ni, total));refs = read(d, a, 'references', (total, 2))
        counts = read(d, a, 'counts', (owners,));handles = read(d, a, 'handles', (total, 2))
        idcaps = a['id_capacities'];total_ids = sum(idcaps)
        verify_handles(caps, counts, words, refs, handles, read(d, a, 'id_to_index', (total_ids,)),
                       read(d, a, 'free_ids', (total_ids,)), read(d, a, 'free_counts', (owners,)),
                       index_plane, a['transfer_epoch'], idcaps)
        destinations = {o: physical_owners(w[position:position+3].T.copy().view('<f4'), regions) for o, w in before.items()}
        retired, changed = verify_partition(before, after, words, refs, counts, caps, handles,
            read(d, a, 'exit_words', (nf+ni, etotal)), read(d, a, 'exit_references', (etotal, 2)),
            read(d, a, 'exit_records', (etotal, 4)), read(d, a, 'exit_counts', (owners, 5)), ecaps,
            read(d, a, 'control', (4,)), destinations, lambda x, y: crossing(x, y, profile), position, start, index_plane)
        for source, particle, face, row, t in retired:
            key = tuple(map(int, before[source][birth, particle]))
            if key in retired_keys:
                raise ValueError('Particle retired more than once')
            retired_keys.add(key)
            ledger.append(dict(native_step=h['native_step'], birth=list(key), source=source, face=face, row=row, fraction=t, volume_m3=volume[source]))
        if indexed(after, birth).keys() != known-retired_keys:
            raise ValueError('Survivor/exit birth identities do not partition initial water')
        changes.append(changed);previous = after
    later = {r['region_id']: read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))[:, :r['particle_count']] for r in records}
    for r in records:
        n = r['particle_count']
        words = read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))
        p = read(directory, r, 'positions', (n, 4)).view('<f4')
        v = read(directory, r, 'velocities', (n, 4)).view('<f4')
        ids = read(directory, r, 'identities', (n, 4))
        expected = physical_owners(p[:, :3], regions)
        verify_packet(r, words, read(directory, r, 'route_destinations', (n, 4)),
                      read(directory, r, 'route_counts', (owners+3,)), p, v, ids, expected, owners)
    final, last = indexed(later, birth), indexed(previous, birth)
    continuous = step == history[-1]['native_step']+1
    expected_births = {o: sum(planned[s][o] for s in range(previous_step+1, step+1)) for o in range(owners)}
    known.update(verify_population(final, known, retired_keys, expected_births, nf+identity[2]))
    if final.keys() != known-retired_keys or not retired_keys or not final:
        raise ValueError('Actual exits and surviving native water required')
    moved = 0
    for key, (owner, w) in final.items():
        if key in last:
            old_owner, old = last[key]
            if owner != old_owner or not np.array_equal(w[index_plane:index_plane+2], old[index_plane:index_plane+2]):
                raise ValueError('Following native step lost ownership or handles')
            if continuous and not np.array_equal(w[position:position+3], old[position:position+3]):
                raise ValueError('Postcommit-to-next-P2G position changed before advection')
            moved += not np.array_equal(w[position:position+3], old[position:position+3])
        if not np.array_equal(w[position:position+3], w[start:start+3]) or not np.isfinite(w[position:position+3].view('<f4')).all():
            raise ValueError('Final P2G origin was not refreshed')
        if physical_owners(w[position:position+3].view('<f4')[None, :], regions)[0] != owner:
            raise ValueError('Final survivor left its physical owner without a commit')
    if ((not continuous and moved == 0) or len(history)<3 or moving_segments == 0 or sum(changes) == 0 or
            later[7].shape[1] != 0 or later[0].shape[1] == 0):
        raise ValueError('Continuing motion, owner handoff and emptied outlet required')
    added = len(known)-len(initial)
    if emission and added < 2:
        raise ValueError('Repeated native emission required')
    return dict(native_outlet_retirement_verified=True, initial_particles=len(initial), retired_particles=len(retired_keys),
                native_emission_verified=bool(emission), verified_new_births=added,
                planned_births_per_step=[sum(planned[s].values()) for s in range(1, step+1)],
                surviving_particles=len(final), verified_native_commits=len(history), owner_changes_per_commit=changes,
                verified_segments=verified_segments, moving_segments=moving_segments, following_step_moving_particles=moved,
                handoff_continuous_through_capture=continuous,
                initial_volume_m3=len(initial)*volume[0], retired_volume_m3=sum(x['volume_m3'] for x in ledger),
                added_volume_m3=added*volume[0],
                surviving_volume_m3=len(final)*volume[0], exits=ledger,
                following_step_counts={o: w.shape[1] for o, w in later.items()},
                initially_empty_receiver_verified=True,
                boundary_profile_sha256=hashlib.sha256(boundary.read_bytes()).hexdigest(),
                dense_flow_or_visual_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path);parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
