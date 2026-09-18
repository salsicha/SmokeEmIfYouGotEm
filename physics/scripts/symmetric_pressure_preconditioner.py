"""Symmetric block Gauss-Seidel for the unchanged factored pressure matrix.

M=(D+L) D^-1 (D+L)^T is SPD: two triangular sweeps are a
preconditioner application, not additional CG or physical evolution steps.
Each diagonal block is the original two-component principal block. All
off-diagonal blocks, including periodic wrap and both pole factors, are
assembled from the authoritative combined-alias rows. No stencil truncation,
shift, relaxation parameter, depth floor or residual-dependent correction.
Research Python implementation; no native execution or FPS claim.
"""
import numpy as np


def blocks(system):
    count = system.h.size
    lower = [dict() for _ in range(count)]
    _, starts = np.unique(system.rows, return_index=True)
    ends = np.r_[starts[1:], system.rows.size]
    for start, end in zip(starts, ends):
        columns = system.columns[start:end]
        w = system.w_coefficients[start:end]
        v = system.v_coefficients[start:end]
        scale = system.length * system.fraction.ravel()[system.rows[start]]
        for i, ci in enumerate(columns):
            row, component = divmod(int(ci), 2)
            for j, cj in enumerate(columns):
                col, other = divmod(int(cj), 2)
                if row <= col:
                    continue
                block = lower[row].setdefault(col, np.zeros((2, 2)))
                block[component, other] += scale * (w[i]*w[j] + .75*v[i]*v[j])
    diagonal = np.zeros((count, 2, 2))
    diagonal[:, 0, 0] = system.diagonal[..., 0].ravel()
    diagonal[:, 1, 1] = system.diagonal[..., 1].ravel()
    diagonal[:, 0, 1] = diagonal[:, 1, 0] = system.off_diagonal.ravel()
    # The block inverse follows the existing stable two-by-two Schur solve.
    ratio = diagonal[:, 1, 0] / diagonal[:, 0, 0]
    schur = diagonal[:, 1, 1] - diagonal[:, 1, 0]*ratio
    if np.any(schur <= 0) or not np.isfinite(schur).all():
        raise ValueError('Invalid symmetric pressure block')
    lower = tuple(tuple(sorted(row.items())) for row in lower)
    for row in lower:
        for _, block in row:
            if not np.isfinite(block).all():
                raise ValueError('Symmetric pressure block exceeds storage range')
            block.setflags(write=False)
    for value in (diagonal, ratio, schur):
        value.setflags(write=False)
    return lower, diagonal, ratio, schur


def precondition(system, residual):
    residual = system._vector(residual)
    if not hasattr(system, '_symmetric_pressure_blocks'):
        system._symmetric_pressure_blocks = blocks(system)
    lower, diagonal, ratio, schur = system._symmetric_pressure_blocks

    def inverse(index, value):
        second = (value[1] - ratio[index]*value[0])/schur[index]
        first = value[0]/diagonal[index, 0, 0] - ratio[index]*second
        return np.array((first, second))

    forward = residual.reshape(-1, 2).copy()
    for i, entries in enumerate(lower):
        for j, block in entries:
            forward[i] -= block @ forward[j]
        forward[i] = inverse(i, forward[i])
    result = np.einsum('nij,nj->ni', diagonal, forward)
    for i in range(len(lower)-1, -1, -1):
        result[i] = inverse(i, result[i])
        for j, block in lower[i]:
            result[j] -= block.T @ result[i]
    if not np.isfinite(result).all():
        raise ValueError('Symmetric pressure sweep exceeds storage range')
    return result.reshape(residual.shape)
