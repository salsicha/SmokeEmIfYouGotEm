"""Verify native pre-advection positions across consecutive committed steps.

This is segment provenance, not permission to retire exterior particles.
An outlet still needs a validated physical face and an atomic exit ledger.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_liquid_native_handoff import audit as audit_handoff, native_snapshot, read


def verify_origins(previous, following, birth_planes, position, step_start, components):
    if (set(previous) != set(following) or not previous or
            not 0 <= position <= components-3 or not 0 <= step_start <= components-3 or
            set(range(position, position+3)) & set(range(step_start, step_start+3)) or
            len(birth_planes) != 2 or len(set(birth_planes)) != 2 or
            any(p < components for p in birth_planes)):
        raise ValueError('Complete owners and distinct native position/identity planes required')

    def indexed(owners):
        result = {}
        for owner, words in owners.items():
            if (words.dtype != np.dtype('<u4') or words.ndim != 2 or
                    words.shape[0] <= max(birth_planes)):
                raise ValueError('Exact full native word planes required')
            for particle in words.T:
                key = tuple(map(int, particle[birth_planes]))
                if key in result:
                    raise ValueError('Duplicate segment birth identity')
                for offset in (position, step_start):
                    if not np.isfinite(particle[offset:offset+3].view('<f4')).all():
                        raise ValueError('Nonfinite native segment endpoint')
                result[key] = (owner, particle)
        return result

    before, after = indexed(previous), indexed(following)
    if not before or not before.keys() <= after.keys():
        raise ValueError('Previous native particle missing from next step')
    moved = 0
    for key, (owner, words) in before.items():
        next_owner, next_words = after[key]
        if owner != next_owner:
            raise ValueError('Unexpected ownership change between commit and next precommit')
        if not np.array_equal(words[position:position+3], next_words[step_start:step_start+3]):
            raise ValueError('Segment origin is not the actual previous committed position')
        moved += not np.array_equal(next_words[position:position+3], next_words[step_start:step_start+3])
    return dict(verified_segments=len(before), moving_segments=int(moved))


def audit(directory):
    directory = Path(directory).resolve()
    audit_handoff(directory)  # Actual writes, birth accounting, IDs, motion and clean RHI.
    report = json.loads((directory/'stages.json').read_text())
    records = report['native_transfer_packet']
    history = report['native_particle_handoff_history']
    nf = history[0]['float_components']
    ni = history[0]['int_components']
    first = records[0]
    start, position = first['route_step_start_offset'], first['route_position_offset']
    if any((r['route_step_start_offset'], r['route_position_offset']) != (start, position) for r in records):
        raise ValueError('Native segment layout differs across owners')
    if not 0 <= start <= nf-3:
        raise ValueError('Native pre-advection attribute missing')
    birth = [nf+i for i in first['route_identity_offsets'][:2]]
    verified = moved = pairs = 0
    for earlier, later in zip(history, history[1:]):
        if later['native_step'] != earlier['native_step']+1:
            raise ValueError('Only consecutive steps prove native segment origin')
        before = native_snapshot(directory/earlier.get('snapshot_directory', ''), earlier, 'after')
        following = native_snapshot(directory/later.get('snapshot_directory', ''), later, 'before')
        result = verify_origins(before, following, birth, position, start, nf)
        verified += result['verified_segments'];moved += result['moving_segments'];pairs += 1
    if pairs < 2 or moved == 0:
        raise ValueError('Repeated actual moving native segments required')
    # The retained P2G snapshot precedes advection, immediately after the origin
    # assignment. Check all live particles, including new births, exactly.
    live = 0
    for r in records:
        n = r['particle_count']
        words = read(directory, r, 'route_words', (nf+ni, r['particle_capacity']))[:, :n]
        if not np.array_equal(words[position:position+3], words[start:start+3]):
            raise ValueError('P2G particle origin was not refreshed before advection')
        live += n
    return dict(native_segment_origins_verified=True, consecutive_step_pairs=pairs,
                verified_segments=verified, moving_segments=moved,
                pre_advection_snapshot_particles=live,
                exterior_retirement_verified=False, visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
