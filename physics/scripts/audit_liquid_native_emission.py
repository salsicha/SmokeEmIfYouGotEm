"""Native source births plus repeated ownership handoff; not scene acceptance."""
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read, native_snapshot, verify_commit, verify_empty_receiver


def verify_birth_growth(samples, planned, birth_planes, unique_plane, source=1):
    """Compare every retained population against independent native spawn plans."""
    previous = {};previous_step = 0;initial = 0;added_total = 0
    for step, owners in samples:
        if step <= previous_step or set(owners) != set(range(12)):
            raise ValueError('Ordered complete native population samples required')
        current = {}
        for owner, words in owners.items():
            if words.dtype != np.dtype('<u4') or words.ndim != 2:
                raise ValueError('Exact native identity word planes required')
            for i in range(words.shape[1]):
                key = tuple(map(int, words[birth_planes, i]))
                if key in current or key[0] not in range(12) or int(words[unique_plane, i]) != key[1]:
                    raise ValueError('Duplicate/relabelled native birth identity or unique ID')
                current[key] = owner
        if not previous.keys() <= current.keys():
            raise ValueError('Existing particles disappeared during source emission')
        new = current.keys()-previous.keys()
        expected = {owner: sum(planned[s].get(owner, 0) for s in range(previous_step+1, step+1)) for owner in range(12)}
        actual = {owner: sum(k[0] == owner for k in new) for owner in range(12)}
        if expected != actual or any(current[k] != k[0] for k in new):
            raise ValueError('Observed births differ from native owner/spawn schedule')
        if previous_step:
            if any(k[0] != source for k in new):
                raise ValueError('Unplanned regional source emitted particles')
            added_total += len(new)
        else:
            initial = len(new)
        previous = current;previous_step = step
    if initial == 0 or added_total < 2:
        raise ValueError('Initial population plus repeated nonzero native emission required')
    return dict(initial_particles=initial, verified_new_births=added_total, particles=len(previous))


def audit_emission(directory, prepared, report):
    # Called only after the normal handoff entry point checks capture and RHI log.
    if (not report.get('native_empty_receiver_requested') or not report['native_emission_activated'] or
            report['native_emission_rate'] != 60 or report['native_emission_start_step'] < 1):
        raise ValueError('Activated bounded native source required')
    history = report['native_particle_handoff_history'];step = report['native_transfer_packet_step']
    if (not history or len(history) != report['native_particle_handoff_count'] or len(history) > 8 or
            [h['native_step'] for h in history] != list(range(2, 2+len(history))) or
            [h['receiving']['transfer_epoch'] for h in history] != list(range(1, 1+len(history))) or
            not history[-1]['native_step']+2 <= step <= 12):
        raise ValueError('Complete ordered native commit/epoch history required')
    roots = [(directory/h.get('snapshot_directory', '')).resolve() for h in history]
    if len(set(roots)) != len(roots) or any(r != directory and r.parent != directory for r in roots):
        raise ValueError('Invalid native history directories')
    records = report['native_transfer_packet']
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve native owners required')
    nf, ni, index = history[0]['float_components'], history[0]['int_components'], history[0]['id_component']
    if any((h['float_components'], h['int_components'], h['id_component']) != (nf, ni, index) for h in history):
        raise ValueError('Changing native particle layout')
    offsets = records[0]['route_identity_offsets'];birth_planes = [nf+offsets[0], nf+offsets[1]]
    unique = nf+offsets[2]
    initial = {}
    for r in records:
        n = r['birth_particle_count'];ids = read(directory, r, 'birth_identities', (n, 4))
        words = np.zeros((nf+ni, n), dtype='<u4')
        words[np.asarray(offsets)+nf] = ids.T
        initial[r['region_id']] = words
    before = [native_snapshot(root, h, 'before') for root, h in zip(roots, history)]
    later = {r['region_id']: read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))[:, :r['particle_count']] for r in records}
    from liquid_stage_journal import stage_groups
    groups = [g for g in stage_groups(report) if g['entries'][0]['first']][:step]
    if len(groups) != step:
        raise ValueError('Missing native first-stage spawn plan')
    planned = {}
    for s, g in enumerate(groups, 1):
        if not g['complete'] or not g['aligned'] or sorted(e['owner'] for e in g['entries']) != list(range(12)):
            raise ValueError('Native spawn schedule incomplete')
        if any(bool(e['reset']) != (s == 1) for e in g['entries']):
            raise ValueError('Unaccounted native generation reset')
        planned[s] = {e['owner']: int(e['native_rate_spawns'])+int(e['native_event_spawns']) for e in g['entries']}
        if s > 1 and (any(v for o, v in planned[s].items() if o != 1) or planned[s][1] not in (0, 1)):
            raise ValueError('Bounded source emitted outside its native birth budget')
    growth = verify_birth_growth([(1, initial)]+[(h['native_step'], b) for h, b in zip(history, before)]+[(step, later)],
                                 planned, birth_planes, unique)
    regions = [json.loads((Path(prepared)/f'region-{i:03d}.json').read_text()) for i in range(12)]
    commits = [verify_commit(roots[i], h, records, before[i+1] if i+1 < len(history) else later,
                             regions, require_change=i == 0, allow_births=True) for i, h in enumerate(history)]
    empty = verify_empty_receiver(records, before[0], later, report['native_transfer_packet_per_owner'], growth['verified_new_births'])
    growth.update(empty, bounded_native_handoff_verified=True, native_emission_verified=True,
                  verified_native_commits=len(history), owner_changes_per_commit=[r['native_owner_changes'] for r in commits],
                  native_owner_changes=sum(r['native_owner_changes'] for r in commits),
                  following_step_counts={o: w.shape[1] for o, w in later.items()},
                  planned_births_per_step=[sum(planned[s].values()) for s in range(1, step+1)],
                  sustained_flow_or_visual_performance_acceptance=False)
    return growth
