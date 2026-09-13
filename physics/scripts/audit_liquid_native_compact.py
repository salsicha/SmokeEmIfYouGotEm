"""Check bounded compact telemetry and final native state, not exact tick history."""
import json
from pathlib import Path

import numpy as np

from audit_liquid_native_generation import verify_generation
from audit_liquid_native_handoff import read
from audit_liquid_native_retirement import indexed
from audit_liquid_particle_routes import physical_owners, verify_packet


def verify_summary(history, planned, initial):
    live = initial;retired = np.zeros((12, 4), dtype=np.int64)
    for step, h in enumerate(history, 2):
        if h['native_step'] != step or not h['issued'] or h['full_audit_retained'] or h['retained_summary_bytes'] != 304:
            raise ValueError('Complete consecutive compact native history required')
        control = np.asarray(h['control'], dtype=np.int64)
        counts = np.asarray(h['counts'], dtype=np.int64)
        exits = np.asarray(h['exit_counts'], dtype=np.int64).reshape(12, 5)
        if control.shape != (4,) or counts.shape != (12,) or np.any(counts < 0) or np.any(exits < 0):
            raise ValueError('Invalid compact count layout')
        spawned = sum(planned[step].values())
        nout = int(exits[:, 4].sum())
        if (not np.array_equal(exits[:, :4].sum(axis=1), exits[:, 4]) or
                not np.array_equal(control, [1, 0, live+spawned, nout]) or counts.sum()+nout != live+spawned):
            raise ValueError(f'Compact transaction failed or lost/invented water at native step {step}: {control.tolist()}')
        retired += exits[:, :4];live = int(counts.sum())
    return live, retired


def audit(directory, log_path=None):
    directory = Path(directory).resolve()
    report = json.loads((directory/'stages.json').read_text())
    capture = json.loads((directory/'capture.json').read_text())
    log = Path(log_path or directory.with_suffix('.log')).read_text(errors='replace')
    if (not capture['complete'] or report['exchange_error'] or not report['native_transfer_packet_saved'] or
            not report.get('native_compact_handoff_requested') or not report['native_particle_retirement_requested'] or
            not report['native_emission_requested'] or not report['native_empty_receiver_requested'] or
            '-RHIValidation' not in log or any(x in log for x in ('LogRHI: Error','Fatal error:','GPU Crashed'))):
        raise ValueError('Successful RHI-validated compact inlet/outlet replay required')
    verify_generation(report)
    records, history = report['native_transfer_packet'], report['native_particle_handoff_history']
    if len(history) != report['native_particle_handoff_count'] or len(history) < 3:
        raise ValueError('Repeated native compact commits required')
    step = report['native_transfer_packet_step']
    if step != history[-1]['native_step']+1:
        raise ValueError('Native handoff must continue through the retained P2G boundary')
    from liquid_stage_journal import stage_groups
    groups = [g for g in stage_groups(report) if g['entries'][0]['first']][:step]
    planned = {s: {e['owner']: e['native_rate_spawns']+e['native_event_spawns'] for e in g['entries']}
               for s, g in enumerate(groups, 1)}
    if len(planned) != step or any(v not in (0, 1) or (v and o != 1) for s,p in planned.items() if s > 1 for o,v in p.items()):
        raise ValueError('Bounded native source plan required')
    per_owner = report['native_transfer_packet_per_owner']
    if per_owner not in (1, 2, 3, 4) or [r['region_id'] for r in records] != list(range(12)):
        raise ValueError('Complete bounded wet-seed fixture required')
    initial = set()
    for r in records:
        n = r['birth_particle_count'];owner = r['region_id']
        expected = per_owner if owner in (1, 4, 5, 7) else 0
        ids = read(directory, r, 'birth_identities', (n, 4))
        if n != expected or r['expected_count'] != expected or planned[1][owner] != n:
            raise ValueError('Initial compact replay population differs from native birth plan')
        if sorted(map(tuple, ids[:, :3].tolist())) != [(owner, i, i) for i in range(n)]:
            raise ValueError('Initial native identities differ')
        initial.update((owner, i) for i in range(n))
    live, exits = verify_summary(history, planned, len(initial))
    # This fixture empties the original outlet owner. Without per-exit payload
    # retention we do not claim independently reclassified individual crossings.
    expected_exits = np.zeros((12, 4), dtype=np.int64);expected_exits[7, 1] = per_owner
    if not np.array_equal(exits, expected_exits):
        raise ValueError('Compact fixture did not retire its expected outlet cohort')
    added = sum(sum(p.values()) for s, p in planned.items() if s > 1)
    expected_ids = initial-{(7, i) for i in range(per_owner)}
    expected_ids.update((1, i) for i in range(per_owner, per_owner+added))
    nf, ni = history[0]['float_components'], history[0]['int_components']
    offsets = records[0]['route_identity_offsets'];position = records[0]['route_position_offset']
    birth = [nf+i for i in offsets[:2]]
    repo = Path(__file__).resolve().parents[2]
    regions = [json.loads((repo/f'tmp/south-fork-liquid-regional-state-20260910/region-{i:03d}.json').read_text()) for i in range(12)]
    final = {}
    for r in records:
        n = r['particle_count'];owner = r['region_id']
        words = read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))
        p = read(directory, r, 'positions', (n, 4)).view('<f4')
        v = read(directory, r, 'velocities', (n, 4)).view('<f4')
        ids = read(directory, r, 'identities', (n, 4))
        destinations = physical_owners(p[:, :3], regions)
        verify_packet(r, words, read(directory, r, 'route_destinations', (n, 4)),
                      read(directory, r, 'route_counts', (15,)), p, v, ids, destinations)
        if np.any(destinations != owner) or n != history[-1]['counts'][owner]+planned[step][owner]:
            raise ValueError('Final actual native count/owner differs from compact transaction')
        final[owner] = words[:, :n]
        if not np.array_equal(words[position:position+3, :n], words[r['route_step_start_offset']:r['route_step_start_offset']+3, :n]):
            raise ValueError('Final native pre-advection origin was not refreshed')
    identities = indexed(final, birth)
    if identities.keys() != expected_ids or len(identities) != live+sum(planned[step].values()):
        raise ValueError('Final native identity set lost, duplicated or invented water')
    if any(int(w[nf+offsets[2]]) != key[1] for key, (_, w) in identities.items()):
        raise ValueError('Native unique identity changed')
    return dict(compact_native_telemetry_verified=True, following_step_counts={o:w.shape[1] for o,w in final.items()},
                initially_empty_receiver_verified=final[0].shape[1]>0, initial_particles=len(initial), verified_new_births=added,
                retired_particles=int(exits.sum()), surviving_particles=len(identities), verified_native_commits=len(history),
                retained_history_bytes=sum(h['retained_summary_bytes'] for h in history),
                exact_per_tick_payload_or_exit_history_verified=False, dense_flow_or_visual_performance_acceptance=False)
