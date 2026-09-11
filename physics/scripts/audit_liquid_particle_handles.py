"""Check staged persistent handles/free lists from native receiving particles."""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_liquid_particle_assembly import audit as audit_assembly


def verify_handles(capacities, counts, words, references, handles, table, free_ids, free_counts, index_plane, epoch, id_capacities=None):
    if not 0 < epoch < 0x7fffffff:
        raise ValueError('Unwrapped positive transfer epoch required')
    total = int(sum(capacities))
    id_capacities = capacities if id_capacities is None else id_capacities
    total_ids = int(sum(id_capacities))
    if len(id_capacities) != len(capacities) or any(c < 1 for c in id_capacities):
        raise ValueError('Complete bounded ID capacities required')
    if (handles.shape != (total, 2) or table.shape != (total_ids,) or free_ids.shape != (total_ids,) or
            references.shape != (total, 2) or counts.shape != (len(capacities),) or free_counts.shape != counts.shape):
        raise ValueError('Complete staged handle and free-ID tables required')
    if any(a.dtype != np.dtype('<u4') for a in (words, handles, table, free_ids, free_counts)):
        raise ValueError('Exact integer handle words required')
    offset = id_offset = kept = imported = 0
    for owner, capacity in enumerate(capacities):
        n, nf = int(counts[owner]), int(free_counts[owner])
        id_capacity = id_capacities[owner]
        if n > capacity or n > id_capacity or nf != id_capacity-n:
            raise ValueError('Native used/free handle accounting differs')
        used = set()
        for i in range(n):
            p = offset+i
            index, tag = map(int, handles[p])
            if index >= id_capacity or index in used or table[id_offset+index] != i:
                raise ValueError('Duplicate, invalid or incorrectly mapped receiving handle')
            used.add(index)
            if references[p, 0] == owner:
                if not np.array_equal(handles[p], words[index_plane:index_plane+2, p]):
                    raise ValueError('Staying particle persistent handle was changed')
                kept += 1
            else:
                if tag != (0x80000000 | epoch):
                    raise ValueError('Imported particle acquire tag has wrong namespace/epoch')
                imported += 1
        unused = list(map(int, free_ids[id_offset:id_offset+nf]))
        if len(set(unused)) != nf or used & set(unused) or used | set(unused) != set(range(id_capacity)):
            raise ValueError('Free IDs missing, duplicated, or still used by a live particle')
        if any(table[id_offset+i] != 0xffffffff for i in unused):
            raise ValueError('Free ID still maps to a live particle')
        if np.any(handles[offset+n:offset+capacity] != 0xffffffff):
            raise ValueError('Stale handle outside live particle range')
        offset += capacity
        id_offset += id_capacity
    return dict(receiving_handles_verified=True, staying_handles_unchanged=kept, imported_handles=imported,
                disjoint_complete_free_lists=True, native_particle_handoff_verified=False)


def audit(directory, prepared):
    directory = Path(directory).resolve()
    audit_assembly(directory, prepared)
    report = json.loads((directory/'stages.json').read_text())
    a = report['native_particle_assembly']
    if not report['native_particle_handles_requested'] or not a['handles_prepared'] or a['native_acquire_tag'] >= 0x80000000:
        raise ValueError('Actual native handle preparation with separated tag namespaces required')
    total, owners = a['total_capacity'], len(a['destination_capacities'])
    id_capacities = a.get('id_capacities', a['destination_capacities']);total_ids = sum(id_capacities)
    def read(key, shape):
        path = (directory/a[key]).resolve()
        if path.parent != directory:
            raise ValueError('Invalid handle snapshot path')
        return np.fromfile(path, dtype='<u4').reshape(shape)
    return verify_handles(a['destination_capacities'], read('counts', (owners,)),
                          read('words', (a['float_components']+a['int_components'], total)),
                          read('references', (total, 2)), read('handles', (total, 2)),
                          read('id_to_index', (total_ids,)), read('free_ids', (total_ids,)),
                          read('free_counts', (owners,)), a['float_components']+a['id_component'], a['transfer_epoch'], id_capacities)


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
