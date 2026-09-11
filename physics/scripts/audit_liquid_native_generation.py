"""Check native generation metadata against the observed full spawn schedule."""
from uuid import UUID


def verify_generation(report):
    generation = report['simulation_generation']
    canonical = str(UUID(generation))
    if canonical != generation.lower() or UUID(generation).int == 0 or report['native_lifetime_failed']:
        raise ValueError('Valid active native generation required')
    records = report['native_transfer_packet']
    history = report['native_particle_handoff_history']
    groups = report['groups']
    if any(item.get('simulation_generation') != generation for item in records+history+groups):
        raise ValueError('Stale generation entered native capture or transfer')
    first = [g for g in groups if g['entries'][0]['first']]
    if not first or len(first) != report['native_lifetime_steps']:
        raise ValueError('Lifetime step count differs from actual native groups')
    births = [0]*12
    for step, group in enumerate(first, 1):
        entries = group['entries']
        if (not group['complete'] or not group['aligned'] or sorted(e['owner'] for e in entries) != list(range(12)) or
                any(bool(e['reset']) != (step == 1) for e in entries)):
            raise ValueError('Unexpected reset or incomplete native generation')
        for entry in entries:
            rate, events = entry['native_rate_spawns'], entry['native_event_spawns']
            if rate < 0 or events < 0:
                raise ValueError('Negative native birth plan')
            births[entry['owner']] += rate+events
    if births != report['native_lifetime_births'] or any(n > 2**32 for n in births):
        raise ValueError('Lifetime birth namespace accounting differs')
    return dict(generation=canonical, native_steps=len(first), total_births=sum(births))


def verify_distinct_generations(reports):
    results = [verify_generation(r) for r in reports]
    if len(results) != 2 or len({r['generation'] for r in results}) != 2:
        raise ValueError('Restart must create two distinct native generations')
    return results
