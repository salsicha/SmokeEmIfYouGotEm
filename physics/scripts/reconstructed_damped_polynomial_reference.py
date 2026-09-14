"""SPD parallel damped-Jacobi polynomial inverse preconditioner reference.

For S=D^-1/2 A D^-1/2 and beta=max(row sums of abs(S)), omega=1/beta.
S is SPD and lambda_max(S)<=beta, so B=I-omega*S has eigenvalues in[0,1).
P=omega*D^-1/2*(I+B+...+B^degree)*D^-1/2 is therefore SPD. The bound
comes from the unchanged matrix, not an accuracy gate or fitted damping of
water. Only the preconditioner changes. This is not an evolved/native solution.
"""
import numpy as np
from scipy import sparse
from pressure_cg_range_reference import solve
from diagnose_reconstructed_pressure_convergence import assembled_matrix


class DampedPolynomialSystem:
    def __init__(self, original, degree):
        if type(degree) is not int or not 0 <= degree <= 8:
            raise ValueError('Explicit polynomial degree from0 through8 required')
        self.original, self.h, self.degree = original, original.h, degree
        matrix = assembled_matrix(original); diagonal = matrix.diagonal()
        if not np.isfinite(matrix.data).all() or np.any(diagonal <= 0):
            raise ValueError('Invalid matrix; no diagonal repair')
        self.inverse_root = 1/np.sqrt(diagonal)
        scaling = sparse.diags(self.inverse_root)
        self.scaled = (scaling@matrix@scaling).tocsr()
        self.bound = float(np.asarray(abs(self.scaled).sum(axis=1)).max())
        if not np.isfinite(self.bound) or self.bound <= 0: raise ValueError('Invalid spectral bound')
        self.omega = 1/self.bound
        self.inverse_root.flags.writeable = False

    def apply(self, value): return self.original.apply(value)

    def precondition(self, residual, scheme='damped_polynomial'):
        if scheme != 'damped_polynomial': raise ValueError('Unknown polynomial scheme')
        residual = self.original._vector(residual)
        normalized = residual.ravel()*self.inverse_root
        value = normalized.copy()
        for _ in range(self.degree): value = normalized+value-self.omega*(self.scaled@value)
        result = self.omega*self.inverse_root*value
        if not np.isfinite(result).all(): raise ValueError('Damped polynomial exceeds range')
        return result.reshape(residual.shape)

    def solve(self, rhs): return solve(self, rhs, 40, preconditioner='damped_polynomial')
