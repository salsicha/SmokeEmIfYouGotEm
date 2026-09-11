"""Extract a bounded terrain-contact region without resampling its triangles.

Indices describe an explicit nominal-quad rectangle, including whatever halo
the caller requires. This is terrain paging, not independent fluid simulation:
it does not invent internal sources, discard particles, or reset water state.
"""
import copy
import numpy as np


def extract(profile, first_column, first_row, columns, rows, stable_anchor=False):
    anchored = profile.get('schema') == 'raftsim.registered_liquid_contact.v3'
    if (profile.get('schema') not in ('raftsim.registered_liquid_contact.v2', 'raftsim.registered_liquid_contact.v3') or
            profile.get('vertex_encoding') != 'nominal-quad-local-xy-and-world-z-centimetres'):
        raise ValueError('Explicit quad-relative contact profile required')
    indices = (first_column, first_row, columns, rows)
    if any(not isinstance(v, (int, np.integer)) or isinstance(v, bool) for v in indices):
        raise ValueError('Integer quad indices required')
    if min(first_column, first_row) < 0 or min(columns, rows) < 1 or max(columns, rows) > 256:
        raise ValueError('Region exceeds bounded contact table limit')
    packed = np.asarray(profile['packed_vectors'], dtype=np.float32)
    if packed.ndim != 2 or packed.shape[1] != 3 or len(packed) < 8 or not np.isfinite(packed).all():
        raise ValueError('Finite packed triangle table required')
    meta, dims = packed[:2]
    header = 3 if anchored else 2
    offset = packed[2, :2] if anchored else np.zeros(2, dtype=np.float32)
    nc, nr = int(dims[1]), int(dims[2])
    if (min(meta[2], dims[0], nc, nr) <= 0 or nc != dims[1] or nr != dims[2] or len(packed) != header+6*nc*nr or
            not np.array_equal(offset, np.floor(offset)) or (abs(offset) > 4096).any() or (anchored and packed[2, 2] != 0)):
        raise ValueError('Malformed nominal-quad metadata')
    if first_column+columns > nc or first_row+rows > nr:
        raise ValueError('Region lacks source support; never clamp requested bounds')
    vertices = packed[header:].reshape(nr, nc, 6, 3)[first_row:first_row+rows, first_column:first_column+columns]
    result = {k: copy.deepcopy(v) for k, v in profile.items()
              if k not in ('packed_vectors', 'query_seed_count', 'seed_query_max_error_cm')}
    if anchored or stable_anchor:
        # Preserve the floating-point address calculation as well as triangles.
        # Rebasing meta can choose the neighboring quad at a rounding boundary.
        new_offset = offset+[first_column, first_row]
        if (abs(new_offset) > 4096).any():
            raise ValueError('Global quad offset exceeds bounded addressing range')
        result.update(schema='raftsim.registered_liquid_contact.v3',
            packed_vectors=np.concatenate(([meta, [dims[0], columns, rows], [*new_offset, 0]], vertices.reshape(-1, 3))).tolist(),
            query_columns=columns, query_rows=rows, triangle_count=2*columns*rows,
            source_quad_region=[first_column, first_row, columns, rows],
            runtime_support_verified=False, region_query_accuracy_verified=False)
        return result
    new_meta = meta.copy()
    new_meta[:2] = [meta[0]+first_column*float(meta[2]), meta[1]-first_row*float(dims[0])]
    new_dims = np.array([dims[0], columns, rows], dtype=np.float32)
    # Cropping must not change the float32 origin used for any retained quad.
    # Reject an unrepresentable rebase instead of silently moving rock contacts.
    for start, count, origin, new_origin, step in (
        (first_column, columns, meta[0], new_meta[0], meta[2]),
        (first_row, rows, meta[1], new_meta[1], -dims[0]),
    ):
        original = np.float32(origin+(start+np.arange(count))*float(step))
        rebased = np.float32(new_origin+np.arange(count)*float(step))
        if not np.array_equal(original, rebased):
            raise ValueError('Region origin cannot preserve source float32 quad origins')
    result.update(packed_vectors=np.concatenate((new_meta[None], new_dims[None], vertices.reshape(-1, 3))).tolist(),
                  query_columns=columns, query_rows=rows, triangle_count=2*columns*rows,
                  source_quad_region=[first_column, first_row, columns, rows],
                  runtime_support_verified=False, region_query_accuracy_verified=False)
    return result
