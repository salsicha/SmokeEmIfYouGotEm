"""Exact native neighbor insertion/histogram/scatter readback consistency.

This checks a retained native P2G neighbor list, not visual or flow acceptance.
"""
import numpy as np


def verify_neighbors(cell_ids, ids, tags, counts, offsets, sorted_ids, sorted_tags, native_ids):
    arrays=[np.asarray(a,dtype=np.int64) for a in
            (cell_ids,ids,tags,counts,offsets,sorted_ids,sorted_tags)]
    cell_ids,ids,tags,counts,offsets,sorted_ids,sorted_tags=arrays
    native_ids=np.asarray(native_ids,dtype=np.int64)
    if (any(a.ndim!=1 for a in arrays) or native_ids.ndim!=2 or native_ids.shape[1]!=2 or
        len(ids)!=len(cell_ids) or len(tags)!=len(ids) or len(sorted_ids)!=len(ids) or
        len(sorted_tags)!=len(ids) or len(counts)!=len(offsets) or
        np.any(counts<0) or np.any(cell_ids < -1) or np.any(cell_ids>=len(counts))):
        raise ValueError('Malformed native neighbor buffers')
    valid=cell_ids>=0
    histogram=np.bincount(cell_ids[valid],minlength=len(counts))
    if not np.array_equal(histogram,counts) or not np.array_equal(counts.cumsum(),offsets):
        raise ValueError('Native neighbor insertion/histogram/prefix mismatch')
    live=int(counts.sum())
    if live!=len(native_ids) or live>len(ids):
        raise ValueError('Native neighbor list omitted or duplicated live particles')
    def ordered(rows):
        return rows[np.lexsort(tuple(rows[:,i] for i in reversed(range(rows.shape[1]))))]
    inserted=np.column_stack((cell_ids[valid],ids[valid],tags[valid]))
    sorted_cells=np.repeat(np.arange(len(counts)),counts)
    scattered=np.column_stack((sorted_cells,sorted_ids[:live],sorted_tags[:live]))
    if not np.array_equal(ordered(inserted),ordered(scattered)):
        raise ValueError('Native neighbor scatter changed cell/identity/tag membership')
    if (len(np.unique(native_ids,axis=0))!=live or
        not np.array_equal(ordered(inserted[:,1:]),ordered(native_ids))):
        raise ValueError('Native neighbor list differs from current persistent identities')
    return dict(native_neighbor_membership_verified=True,particles=live,nonempty_cells=int(np.count_nonzero(counts)))


def audit_record(directory, record):
    r=record;n=r['particle_count'];capacity=r['particle_capacity']
    words=np.fromfile(directory/r['route_words'],dtype=np.uint32).reshape(
        r['route_float_components']+r['route_int_components'],capacity)
    offset=r['route_float_components']+r['route_identity_offsets'][3]
    native=words[offset:offset+2,:n].T.view(np.int32)
    names=('nq_cells','nq_ids','nq_tags','nq_counts','nq_offsets','nq_sorted_ids','nq_sorted_tags')
    buffers=[np.fromfile(directory/r[name],dtype=np.int32) for name in names]
    if len(buffers[0])!=r['nq_slots'] or len(buffers[3])!=np.prod(r['nq_dimensions']):
        raise ValueError('Native neighbor readback allocation metadata differs')
    return verify_neighbors(*buffers,native)
