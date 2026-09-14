"""Research primitive-scalar reconstruction; never a pressure-force operator.

Fit a local quadratic to real +/-1, +/-2 axial scalar samples. Neighbor depth
weights vanish continuously as a neighbor dries beside a positive-depth owner.
The dry entering limit uses the supplied conserved mass direction, not a depth
floor or overwritten dry state. All two-neighbor fits reproduce quadratics;
their Gram-determinant weights form the weighted least-squares solution.

The pairwise formula avoids subtracting nearly equal moment determinants.
Rank-one neighborhoods explicitly fall back to an affine one-neighbor fit;
rank-zero neighborhoods have no inferred gradient. The rank map must remain
visible in qualification. This is a NEW proposed scalar/advection discretization,
not the pressure adjoint, a physical energy proof, or a playable solver change.
"""
from contextlib import contextmanager
import numpy as np
from source_supported_scalar_boundary import SourceSupportedScalarBoundary


def ratio(numerator, denominator_other):
    scale = np.maximum(numerator, denominator_other)
    a = np.divide(numerator, scale, out=np.zeros_like(scale), where=scale > 0)
    b = np.divide(denominator_other, scale, out=np.zeros_like(scale), where=scale > 0)
    if np.any((numerator > 0)&(a == 0)) or np.any((denominator_other > 0)&(b == 0)):
        raise ValueError('Positive depth ratio exceeds storage range')
    return np.divide(a, a+b, out=np.zeros_like(scale), where=a+b > 0)


class DepthWeightedScalarGradient:
    offsets = (-2, -1, 1, 2)

    def __init__(self, depth, dx, *, mass_rate=None):
        h = np.asarray(depth, dtype=float)
        ht = np.zeros_like(h) if mass_rate is None else np.asarray(mass_rate, dtype=float)
        if (h.ndim != 2 or not h.size or ht.shape != h.shape or not np.isfinite(h).all()
                or not np.isfinite(ht).all() or np.any(h < 0) or np.any((h == 0)&(ht < 0))
                or not np.isfinite(dx) or dx <= 0):
            raise ValueError('Invalid original depth/direction/spacing; no repair')
        self.shape = h.shape; self.dx = float(dx); self.weights = []
        support = (h > 0)|((h == 0)&(ht > 0))
        self.ranks = []
        for axis in (1, 0):
            weights = []
            for offset in self.offsets:
                neighbor = np.roll(h, -offset, axis)
                valid = support & np.roll(support, -offset, axis)
                coordinate = np.arange(h.shape[axis])
                inside = (coordinate+offset >= 0)&(coordinate+offset < h.shape[axis])
                valid &= inside[None, :] if axis == 1 else inside[:, None]
                w = ratio(neighbor, h)
                entering_pair = (h == 0)&(neighbor == 0)&valid
                limit = ratio(np.maximum(np.roll(ht, -offset, axis), 0), np.maximum(ht, 0))
                w = np.where(valid, np.where(entering_pair, limit, w), 0.)
                weights.append(w)
            weights = np.stack(weights)
            rank = np.minimum(2, np.count_nonzero(weights, axis=0))
            scale = weights.max(axis=0)
            weights = np.divide(weights, scale, out=np.zeros_like(weights), where=scale > 0)
            weights.flags.writeable = False; rank.flags.writeable = False
            self.weights.append(weights); self.ranks.append(rank)

    def gradient(self, scalar):
        f = np.asarray(scalar, dtype=float)
        if f.shape != self.shape or not np.isfinite(f).all():
            raise ValueError('Missing finite scalar support')
        result = []
        for axis, weights, rank in zip((1, 0), self.weights, self.ranks):
            delta = [np.roll(f, -offset, axis)-f for offset in self.offsets]
            numerator, denominator = np.zeros_like(f), np.zeros_like(f)
            for i, ri in enumerate(self.offsets):
                for j in range(i+1, len(self.offsets)):
                    rj = self.offsets[j]
                    gram = weights[i]*weights[j]*(ri*rj*(rj-ri))**2
                    if np.any((weights[i] > 0)&(weights[j] > 0)&(gram == 0)):
                        raise ValueError('Positive least-squares weight exceeds storage range')
                    pair = (delta[i]*rj*rj-delta[j]*ri*ri)/(ri*rj*(rj-ri))
                    numerator += gram*pair; denominator += gram
            if np.any((rank == 2)&(denominator == 0)):
                raise ValueError('Quadratic neighborhood lost representable weight')
            g = np.divide(numerator, denominator, out=np.zeros_like(f), where=denominator > 0)
            first_order = sum(w*d/r for w, d, r in zip(weights, delta, self.offsets))
            first_order = np.divide(first_order, weights.sum(axis=0), out=np.zeros_like(f), where=weights.sum(axis=0) > 0)
            result.append(np.where(rank == 1, first_order, g)/self.dx)
        result = np.stack(result, axis=-1)
        if not np.isfinite(result).all():
            raise ValueError('Scalar reconstruction exceeds storage range')
        return result


class DepthWeightedSourceBoundary(SourceSupportedScalarBoundary):
    def gradient(self, scalar, exterior_scalar):
        f = self.original._scalar(scalar)
        supplied = np.asarray(exterior_scalar, dtype=float)
        if supplied.shape != self.state.shape[:2] or not np.isfinite(supplied).all():
            raise ValueError('Missing finite full scalar support')
        full = supplied.copy(); full[self.core] = f
        if not hasattr(self, 'primitive_gradient'):
            self.primitive_gradient = DepthWeightedScalarGradient(self.state[..., 0], self.original.dx,
                mass_rate=None if self.full_rate is None else self.full_rate[..., 0])
        return self.primitive_gradient.gradient(full)[self.core].copy()


@contextmanager
def depth_weighted_forcing():
    """Process-isolated source-forcing binding; original pressure D/E stay intact."""
    import source_supported_pressure_reference as pressure
    original = pressure.SourceSupportedScalarBoundary
    pressure.SourceSupportedScalarBoundary = DepthWeightedSourceBoundary
    try:
        yield
    finally:
        pressure.SourceSupportedScalarBoundary = original
