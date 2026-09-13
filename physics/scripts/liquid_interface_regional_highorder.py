"""Independent staged CPU BFECC reference with scalar and validity halo exchange.

Physical exterior values remain caller-owned and can differ between boundary
extensions. No global averaging hides that provisional boundary contract.
"""
from itertools import product
import numpy as np
from liquid_interface_transport import advect
from audit_liquid_native_interface import exchange_scalars


def donors(trace, spacing, shape):
    q = trace['traced_points']/spacing-.5
    low = np.floor(q).astype(int); fraction = q-low; size = np.array(shape[::-1])
    for offset in product((0, 1), repeat=3):
        donor = low+offset
        used = np.prod(np.where(offset, fraction, 1-fraction), axis=1) > 0
        inside = ((donor >= 0) & (donor < size)).all(axis=1)
        rows = np.flatnonzero(used & inside)
        yield used, inside, rows, tuple(donor[rows, ::-1].T)


def advect_regions(fields, velocities, solids, spacing, dt, columns, compact=True):
    if not 2 <= len(fields) <= 16 or len(velocities) != len(fields) or len(solids) != len(fields):
        raise ValueError('Matching bounded regional inputs required')
    # Validate addresses even if subsequent physical motion happens to be zero.
    exchange_scalars(fields, columns)
    for p, s in zip(fields, solids):
        if s.dtype != bool or s.shape != p.shape:
            raise ValueError('Explicit matching boolean solid masks required')
    def transport(source, direction):
        values = []; reports = []; valid = []
        for p, velocity in zip(source, velocities):
            value, report = advect(p, direction*velocity, spacing, dt, np.full(3, 2), np.array(p.shape[::-1])-2,
                                   compact, details=True)
            mask = np.zeros(p.shape, bool); mask[tuple(report['indices'][:, ::-1].T)] = report['valid_mask']
            values.append(value.astype('<f4').astype(float)); reports.append(report); valid.append(mask)
        return values, reports, valid
    forward, a, valid = transport(fields, 1)
    forward = exchange_scalars(forward, columns); valid = exchange_scalars(valid, columns)
    reverse, b, reverse_valid = transport(forward, -1)
    reverse = exchange_scalars(reverse, columns); reverse_valid = exchange_scalars(reverse_valid, columns)
    corrected = []; ready_sources = []
    for p, rev, fvalid, rvalid, solid, trace in zip(fields, reverse, valid, reverse_valid, solids, b):
        key = tuple(trace['indices'][:, ::-1].T)
        ready = fvalid[key] & rvalid[key] & ~solid[key]
        for used, inside, rows, dk in donors(trace, spacing, p.shape):
            ready &= ~used | inside
            ready[rows] &= fvalid[dk] & ~solid[dk]
        chosen = tuple(trace['indices'][ready, ::-1].T)
        value = np.array(p, float); value[chosen] = p[chosen]+.5*(p[chosen]-rev[chosen])
        mask = np.zeros(p.shape, bool); mask[key] = ready
        corrected.append(value.astype('<f4').astype(float)); ready_sources.append(mask)
    corrected = exchange_scalars(corrected, columns); ready_sources = exchange_scalars(ready_sources, columns)
    third, c, _ = transport(corrected, 1)
    results = []; diagnostics = []
    for p, f, t, solid, ready_field, trace, backward, final in zip(fields, forward, third, solids, ready_sources, a, b, c):
        key = tuple(trace['indices'][:, ::-1].T)
        ready = trace['valid_mask'] & ~solid[key]
        minimum = np.full(len(ready), np.inf); maximum = np.full(len(ready), -np.inf)
        for used, inside, rows, dk in donors(trace, spacing, p.shape):
            ready &= ~used | inside
            ready[rows] &= ready_field[dk] & ~solid[dk]
            minimum[rows] = np.minimum(minimum[rows], p[dk]); maximum[rows] = np.maximum(maximum[rows], p[dk])
        candidates = t[key]; chosen = tuple(trace['indices'][ready, ::-1].T)
        result = f.copy(); result[chosen] = np.clip(candidates[ready], minimum[ready], maximum[ready])
        results.append(result.astype('<f4').astype(float))
        diagnostics.append([trace['updated_cells'], trace['rejected_trace_cells'], 0, int(ready.sum()),
                            int((ready & ((candidates < minimum) | (candidates > maximum))).sum()),
                            int((trace['valid_mask'] & ~ready).sum()), backward['rejected_trace_cells'], final['rejected_trace_cells']])
    return exchange_scalars(results, columns), np.asarray(diagnostics, dtype=np.int64)
