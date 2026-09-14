"""Parallel-action polynomial approximation to symmetric triangular sweeps.

Let H=D^-1/2 L D^-1/2 be the strictly lower part of the ORIGINAL A, and
F_m=I-H+H^2-...+(-H)^m. Use P_m=D^-1/2 F_m^T F_m D^-1/2 as the inverse
preconditioner. F_m is unit lower triangular, hence nonsingular: P_m is SPD
for every finite m, without a spectral cutoff or repaired diagonal. All
polynomial terms are kept. Two fixed-length sparse-action chains replace the
grid-length triangular dependency; this is a CPU reference, not a GPU budget
claim. CG still applies the original operator/RHS with exactly40 iterations.
"""
import numpy as np
from scipy import sparse
from pressure_cg_range_reference import solve
from diagnose_reconstructed_pressure_convergence import assembled_matrix


class PolynomialSweepSystem:
    def __init__(self, original, degree):
        if type(degree) is not int or not 0 <= degree <= 8:
            raise ValueError('Explicit polynomial degree from0 through8 required')
        self.original, self.h, self.degree = original, original.h, degree
        matrix = assembled_matrix(original)
        diagonal = matrix.diagonal()
        if not np.isfinite(matrix.data).all() or np.any(diagonal <= 0):
            raise ValueError('Invalid matrix; no diagonal repair')
        self.inverse_root = 1/np.sqrt(diagonal)
        scaling = sparse.diags(self.inverse_root)
        self.lower = (scaling@sparse.tril(matrix, k=-1, format='csr')@scaling).tocsr()
        self.upper = self.lower.T.tocsr()
        self.inverse_root.flags.writeable = False

    def apply(self, value): return self.original.apply(value)

    def precondition(self, residual, scheme='polynomial_sweep'):
        if scheme != 'polynomial_sweep': raise ValueError('Unknown polynomial sweep')
        residual = self.original._vector(residual)
        normalized = residual.ravel()*self.inverse_root
        forward = normalized.copy()
        for _ in range(self.degree): forward = normalized-self.lower@forward
        backward = forward.copy()
        for _ in range(self.degree): backward = forward-self.upper@backward
        result = self.inverse_root*backward
        if not np.isfinite(result).all(): raise ValueError('Polynomial sweep exceeds range')
        return result.reshape(residual.shape)

    def solve(self, rhs): return solve(self, rhs, 40, preconditioner='polynomial_sweep')
