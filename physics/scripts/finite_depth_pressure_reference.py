"""Independent matrix checks for the finite-depth pressure candidate.

The rational approximation truncates NIST DLMF 4.39.1 after denominator 9.
The wet-neighbour Helmholtz discretization is a local-depth approximation,
not the exact variable-bathymetry Dirichlet-to-Neumann operator.
"""
import numpy as np

LENGTHS = np.array([0.4052787713439809, 0.03916567310046354])
WEIGHTS = np.array([0.8106202879112342, 0.12271304542209915])


def response(kh):
    kh = np.asarray(kh, dtype=float)
    return 1 / 15 + np.sum(WEIGHTS / (1 + kh[..., None] ** 2 * LENGTHS), axis=-1)


def matrices(depth, cell_m, periodic=False):
    depth = np.asarray(depth, dtype=float)
    if (depth.ndim != 2 or not np.all(np.isfinite(depth)) or np.any(depth < 0) or
            not np.isfinite(cell_m) or cell_m <= 0):
        raise ValueError("Invalid depth grid or spacing")
    ny, nx = depth.shape
    result = np.broadcast_to(np.eye(nx * ny), (2, nx * ny, nx * ny)).copy()
    for y in range(ny):
        for x in range(nx):
            i = y * nx + x
            if depth[y, x] <= .01:
                continue
            alpha = LENGTHS * (depth[y, x] / cell_m) ** 2
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if periodic:
                    xx, yy = xx % nx, yy % ny
                elif not (0 <= xx < nx and 0 <= yy < ny):
                    continue
                if depth[yy, xx] <= .01:
                    continue
                result[:, i, i] += alpha
                result[:, i, yy * nx + xx] -= alpha
    return result


def chebyshev_potentials(depth, eta, cell_m, iterations=40, periodic=False):
    matrix = matrices(depth, cell_m, periodic)
    eta = np.asarray(eta, dtype=float)
    if eta.shape != np.shape(depth) or not np.all(np.isfinite(eta)) or not 1 <= iterations <= 128:
        raise ValueError("Invalid wave state or iteration count")
    rhs = np.where(np.asarray(depth) > .01, eta, 0).ravel()
    previous = np.broadcast_to(rhs, (2, rhs.size)).copy()
    older = previous.copy()
    diagonal = np.diagonal(matrix, axis1=1, axis2=2)
    c = 1 - 1 / (1 + 4 * LENGTHS * (np.max(depth) / cell_m) ** 2)
    rho = c.copy()
    for iteration in range(iterations):
        relaxation, momentum = np.ones(2), np.zeros(2)
        nonzero = c > 0
        if iteration:
            next_rho = np.zeros(2)
            next_rho[nonzero] = 1 / (2 / c[nonzero] - rho[nonzero])
            relaxation[nonzero] = 2 * next_rho[nonzero] / c[nonzero]
            momentum = next_rho * rho
            rho = next_rho
        residual = (rhs - np.einsum("kij,kj->ki", matrix, previous)) / diagonal
        new = previous + relaxation[:, None] * residual + momentum[:, None] * (previous - older)
        older, previous = previous, new
    return previous, np.stack([np.linalg.solve(a, rhs) for a in matrix])
