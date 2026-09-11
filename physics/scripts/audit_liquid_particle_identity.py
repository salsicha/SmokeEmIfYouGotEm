"""Check actual birth and later integer identities from one native GPU replay.

Identity persistence is a prerequisite, not proof of regional particle handoff.
Both snapshots belong to the same simulation generation; comparisons across
independent runs or resets are intentionally not used as persistence evidence.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def compare_identity_sets(birth, current):
    def collect(owners, is_birth):
        found = {}
        for owner, values in owners.items():
            if not isinstance(owner, int) or not 0 <= owner <= 4095:
                raise ValueError('Invalid regional identity owner')
            if values.dtype.kind != 'i' or values.dtype.itemsize != 4 or values.ndim != 2 or values.shape[1] != 4:
                raise ValueError('Exact int32 four-component identity records required')
            for row in values:
                # Native sequence is a 32-bit counter; retain all bits, including
                # the signed half of its range. Never round it through float32.
                key = (int(row[0]), int(row[1]) & 0xffffffff)
                if not 0 <= key[0] <= 4095 or key in found:
                    raise ValueError('Invalid or duplicated global particle identity')
                if is_birth and (key[0] != owner or row[1] != row[2]):
                    raise ValueError('Birth identity differs from actual owner/native spawn sequence')
                found[key] = owner
        return found
    initial, final = collect(birth, True), collect(current, False)
    if not initial or initial.keys() != final.keys():
        raise ValueError('Missing, added, or relabeled particle identity')
    return dict(native_birth_identity_preserved=True, distinct_particles=len(initial),
                observed_owner_changes=sum(final[k] != initial[k] for k in initial),
                identity_scope='one native simulation generation, birth owner and uint32 sequence',
                particle_handoff_verified=False, visual_or_performance_acceptance=False)


def audit(directory):
    directory = Path(directory).resolve()
    capture = json.loads((directory/'capture.json').read_text())
    report = json.loads((directory/'stages.json').read_text())
    if (not capture['complete'] or report['zero_water'] or report['exchange_error'] or
            not report['native_transfer_packet_saved'] or report['native_transfer_packet_step'] <= 1):
        raise ValueError('Successful later-step snapshot with actual first-step birth records required')
    rasters = [g for g in report['groups'] if g['entries'][0]['name'] == 'Neighbor Grid Rasterize Particles']
    step = report['native_transfer_packet_step']
    if (len(rasters) < step or any(not g['complete'] or not g['aligned'] or len(g['entries']) != 12
                                  for g in rasters[:step]) or
            any(not e['reset'] for e in rasters[0]['entries']) or
            any(e['reset'] for g in rasters[1:step] for e in g['entries'])):
        raise ValueError('Birth and current identities must belong to one uninterrupted native generation')
    records = report['native_transfer_packet']
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve native owners required')
    birth, current = {}, {}
    for record in records:
        if record['identity_layout'] != 'int32:birth_owner,birth_sequence,native_unique_id,native_persistent_index':
            raise ValueError('Unknown native identity layout')
        for target, key, count in ((birth, 'birth_identities', record['birth_particle_count']),
                                   (current, 'identities', record['particle_count'])):
            path = (directory/record[key]).resolve()
            if path.parent != directory or count < 0:
                raise ValueError('Invalid native identity snapshot path/count')
            values = np.fromfile(path, dtype='<i4')
            if values.size != count*4:
                raise ValueError('Incomplete native integer identity snapshot')
            target[record['region_id']] = values.reshape(count, 4)
    result = compare_identity_sets(birth, current)
    result['native_p2g_step'] = report['native_transfer_packet_step']
    return result


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
