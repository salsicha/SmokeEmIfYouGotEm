"""Range-factored STATIC acceleration system for reconstructed pressure research.

W = sqrt(h) (h D - 3 E/2) invsqrt(h), V = sqrt(h) E invsqrt(h).
A = I + length * (W.T fraction W + 3/4 V.T fraction V).
This is the same completed-square SGN acceleration form with the NEW paired
D/E geometry. Coefficients are combined before mass normalization; never form
h**3, an overflowing depth ratio, or velocity = normalized_unknown/sqrt(h).
Dry columns have no physical unknown; their algebraic rows remain identity.

Only static actions and a linear solve are supplied. No nonlinear wet/dry
forcing, prescribed boundary lifts, evolved history or playable qualification.
Exact rational coefficient assembly and high-precision square roots are slow
research choices, not a claim of meeting the production solver budget.

``block`` uses symmetric two-component block sweeps over this same matrix.
The earlier cell-local inverse remains available as ``block-jacobi`` for
unchanged negative controls. Diagonal and spectral choices are unaffected.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import numpy as np
from pressure_cut_face_reference import represented_float
from pressure_cg_range_reference import solve as solve_range_cg


def mass_scaled(coefficient, row_depth, column_depth):
    """coefficient*sqrt(row_depth/column_depth), without intermediate range loss."""
    if row_depth < 0 or column_depth < 0:
        raise ValueError('Negative mass normalization')
    if coefficient == 0:
        return 0.
    if row_depth == 0 or column_depth == 0:
        raise ValueError('Nonzero physical coefficient touches an exactly dry unknown')
    square = coefficient*coefficient*row_depth/column_depth
    with localcontext() as context:
        context.prec = 90
        value = (Decimal(square.numerator)/Decimal(square.denominator)).sqrt()
        if coefficient < 0: value = -value
        return represented_float(value)


class ReconstructedAccelerationSystem:
    def __init__(self, geometry, length, *, dispersion_fraction=None, project_zero_mass_rows=False):
        if geometry.pressure_trace != 'integrated_column' or geometry.bed_quadrature != 'shared_bottom':
            raise ValueError('Requires integrated/shared-bottom research geometry')
        if not np.isfinite(length) or length <= 0:
            raise ValueError('Invalid pressure pole length')
        self.geometry, self.h, self.length = geometry, geometry.h, float(length)
        if type(project_zero_mass_rows) is not bool:
            raise ValueError('Invalid zero-mass projection mode')
        self.fraction = (np.ones_like(self.h) if dispersion_fraction is None
                         else np.array(dispersion_fraction, dtype=float, copy=True))
        if (self.fraction.shape != self.h.shape or not np.isfinite(self.fraction).all()
                or np.any(self.fraction < 0) or np.any(self.fraction > 1)):
            raise ValueError('Invalid nonbreaking dispersion fraction')
        self.fraction.flags.writeable = False
        self.rows, self.columns, self.w_coefficients, self.v_coefficients = [], [], [], []
        diagonal = np.ones((*self.h.shape, 2)).ravel()
        off = np.zeros(self.h.size)
        dx = F(geometry.dx)
        for point in np.ndindex(self.h.shape):
            row = np.ravel_multi_index(point, self.h.shape)
            hi = F(float(self.h[point])); coefficients = {}
            if project_zero_mass_rows and not hi:
                # Solve only the physical positive-mass block. Directional
                # zero-mass auxiliary rows can have nonzero raw D/E limits;
                # their normalized block is not asserted to equal identity.
                # Coupling to positive-mass columns must vanish in the limit,
                # and is separately tested. No positive mass is projected.
                continue
            for component, (axis, edge) in enumerate(zip((1, 0), geometry.edges)):
                left, right = list(point), list(point)
                left[axis] = (point[axis]-1) % self.h.shape[axis]
                right[axis] = (point[axis]+1) % self.h.shape[axis]
                left, right = tuple(left), tuple(right)
                get = lambda name, p: F(float(edge[name][p]))
                dr = get('aa', point)*get('other', point)/dx
                dl = -get('ab', left)*get('own', left)/dx
                dc = (get('aa', point)*get('own', point)-get('ab', left)*get('other', left))/dx
                er, el = get('shared_b', point)/dx, get('shared_b', left)/dx
                ec = get('physical_b', point)-er-el
                for p, d, e in ((point, dc, ec), (right, dr, er), (left, dl, el)):
                    column = 2*np.ravel_multi_index(p, self.h.shape)+component
                    before = coefficients.get(column, (F(0), F(0)))
                    # Combine aliases (singleton/two-cell periodic axes) BEFORE
                    # normalization, squaring or computing the true diagonal.
                    coefficients[column] = before[0]+hi*d-F(3, 2)*e, before[1]+e
            grouped = {}
            for column, (w, v) in coefficients.items():
                hj = F(float(self.h.ravel()[column//2]))
                w, v = mass_scaled(w, hi, hj), mass_scaled(v, hi, hj)
                if not w and not v: continue
                self.rows.append(row); self.columns.append(column)
                self.w_coefficients.append(w); self.v_coefficients.append(v)
                factor = self.length*self.fraction.ravel()[row]
                diagonal[column] += factor*(w*w+.75*v*v)
                grouped[column] = w, v
            for column, (w, v) in grouped.items():
                if column % 2 == 0 and column+1 in grouped:
                    other_w, other_v = grouped[column+1]
                    off[column//2] += factor*(w*other_w+.75*v*other_v)
        for name in ('rows', 'columns', 'w_coefficients', 'v_coefficients'):
            value = np.asarray(getattr(self, name), dtype=np.int64 if name in ('rows', 'columns') else float)
            value.flags.writeable = False
            setattr(self, name, value)
        self.diagonal = diagonal.reshape(*self.h.shape, 2)
        self.off_diagonal = off.reshape(self.h.shape)
        if not np.isfinite(self.diagonal).all() or not np.isfinite(self.off_diagonal).all():
            raise ValueError('Acceleration preconditioner exceeds storage range')
        self.diagonal.flags.writeable = self.off_diagonal.flags.writeable = False

    def _vector(self, value):
        value = np.asarray(value, dtype=float)
        if value.shape != (*self.h.shape, 2) or not np.isfinite(value).all():
            raise ValueError('Invalid normalized acceleration field')
        return value

    def _action(self, value, coefficients):
        value = self._vector(value)
        result = np.bincount(self.rows, weights=coefficients*value.ravel()[self.columns],
                             minlength=self.h.size).reshape(self.h.shape)
        if not np.isfinite(result).all(): raise ValueError('Factored action exceeds storage range')
        return result

    def _transpose(self, value, coefficients):
        value = self.geometry._scalar(value)
        result = np.bincount(self.columns, weights=coefficients*value.ravel()[self.rows],
                             minlength=2*self.h.size).reshape(*self.h.shape, 2)
        if not np.isfinite(result).all(): raise ValueError('Factored transpose exceeds storage range')
        return result

    def w(self, value): return self._action(value, self.w_coefficients)
    def v(self, value): return self._action(value, self.v_coefficients)
    def transpose_w(self, value): return self._transpose(value, self.w_coefficients)
    def transpose_v(self, value): return self._transpose(value, self.v_coefficients)

    def apply(self, value):
        value = self._vector(value)
        result = value+self.length*(self.transpose_w(self.fraction*self.w(value))
                                   +.75*self.transpose_v(self.fraction*self.v(value)))
        if not np.isfinite(result).all(): raise ValueError('Acceleration action exceeds storage range')
        return result

    def precondition(self, residual, scheme='diagonal'):
        residual = self._vector(residual)
        if scheme == 'spectral-flat':
            from flat_spectral_pressure_preconditioner import precondition
            return precondition(self, residual)
        if scheme == 'spectral-frozen-depth':
            from flat_spectral_pressure_preconditioner import frozen_depth_precondition
            return frozen_depth_precondition(self, residual)
        if scheme == 'diagonal': return residual/self.diagonal
        if scheme == 'block':
            from symmetric_pressure_preconditioner import precondition
            return precondition(self, residual)
        if scheme != 'block-jacobi': raise ValueError('Unknown pressure preconditioner')
        a, b = self.diagonal[..., 0], self.diagonal[..., 1]
        ratio = self.off_diagonal/a
        schur = b-self.off_diagonal*ratio
        if np.any(schur <= 0) or not np.isfinite(schur).all(): raise ValueError('Invalid pressure block')
        second = (residual[..., 1]-ratio*residual[..., 0])/schur
        first = residual[..., 0]/a-ratio*second
        return np.stack((first, second), axis=-1)

    def solve(self, rhs, iterations=40, *, preconditioner='diagonal'):
        return solve_range_cg(self, self._vector(rhs), iterations, preconditioner=preconditioner)
