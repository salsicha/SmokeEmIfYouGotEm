"""Opt-in CPU symmetric Gauss-Seidel preconditioner, not runtime integration.

For the actual SPD matrix A=D+L+L^T, use M=(D+L)D^-1(D+L)^T.
Applying M^-1 requires two triangular solves and preserves symmetry/positivity.
No fill, coupling, source, positive depth or RHS component is intentionally
dropped. CG still applies the ORIGINAL factored operator and checks its true
residual after the same40 iterations. Sparse assembly/serial sweeps are not a
native-cost claim and this module never installs itself in the live model.
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve_triangular
from pressure_cg_range_reference import solve
from diagnose_reconstructed_pressure_convergence import assembled_matrix


class SymmetricSweepSystem:
    def __init__(self, original):
        self.original, self.h = original, original.h
        matrix = assembled_matrix(original)
        self.diagonal = matrix.diagonal()
        if (not np.isfinite(matrix.data).all() or not np.isfinite(self.diagonal).all()
                or np.any(self.diagonal <= 0)):
            raise ValueError('Invalid matrix for symmetric sweep; no diagonal repair')
        difference = matrix-matrix.T
        if difference.nnz and np.max(abs(difference.data)) > 1e-13*np.max(abs(matrix.data)):
            raise ValueError('Symmetric sweep requires a symmetric matrix')
        self.lower = sparse.tril(matrix, format='csr')
        self.upper = self.lower.T.tocsr()
        self.diagonal.flags.writeable = False

    def apply(self, value):
        return self.original.apply(value)

    def precondition(self, residual, scheme='symmetric_sweep'):
        if scheme != 'symmetric_sweep': raise ValueError('Unknown symmetric-sweep scheme')
        residual = self.original._vector(residual)
        forward = spsolve_triangular(self.lower, residual.ravel(), lower=True)
        result = spsolve_triangular(self.upper, self.diagonal*forward, lower=False)
        if not np.isfinite(result).all(): raise ValueError('Nonfinite symmetric sweep')
        return result.reshape(residual.shape)

    def solve(self, rhs):
        return solve(self, rhs, 40, preconditioner='symmetric_sweep')
