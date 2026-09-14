"""Research correction: a two-cell scalar link needs intervening wet support.

Retain the earlier unconnected proposal for reproducible rejected reports.
Multiply only two-cell weights by 4*m/(m+h_i)*m/(m+h_j). This equals one
at constant positive depth and vanishes continuously with an intervening
dry cell beside wet endpoints. Zero/zero entering ratios use the actual
mass direction. This is not a pressure adjoint or an energy qualification.
"""
from contextlib import contextmanager
import numpy as np
from depth_weighted_scalar_gradient import DepthWeightedScalarGradient, DepthWeightedSourceBoundary, ratio


class ConnectedDepthWeightedScalarGradient(DepthWeightedScalarGradient):
    def __init__(self, depth, dx, *, mass_rate=None):
        super().__init__(depth, dx, mass_rate=mass_rate)
        h = np.asarray(depth, dtype=float)
        ht = np.zeros_like(h) if mass_rate is None else np.asarray(mass_rate, dtype=float)
        for component, axis in enumerate((1, 0)):
            weights = self.weights[component].copy()
            for i, offset in enumerate(self.offsets):
                if abs(offset) != 2:
                    continue
                middle = np.roll(h, -(offset//2), axis)
                neighbor = np.roll(h, -offset, axis)
                mt = np.maximum(np.roll(ht, -(offset//2), axis), 0.)
                factors = []
                for endpoint, et in ((h, ht), (neighbor, np.roll(ht, -offset, axis))):
                    factor = ratio(middle, endpoint)
                    entering = (middle == 0) & (endpoint == 0)
                    factor = np.where(entering, ratio(mt, np.maximum(et, 0.)), factor)
                    factors.append(factor)
                bridge = 4*factors[0]*factors[1]
                if np.any((factors[0] > 0) & (factors[1] > 0) & (bridge == 0)):
                    raise ValueError('Positive bridge weight exceeds storage range')
                updated = weights[i]*bridge
                if np.any((weights[i] > 0) & (bridge > 0) & (updated == 0)):
                    raise ValueError('Positive connected weight exceeds storage range')
                weights[i] = updated
            scale = weights.max(axis=0)
            weights = np.divide(weights, scale, out=np.zeros_like(weights), where=scale > 0)
            rank = np.minimum(2, np.count_nonzero(weights, axis=0))
            weights.flags.writeable = False; rank.flags.writeable = False
            self.weights[component] = weights; self.ranks[component] = rank


class ConnectedDepthWeightedSourceBoundary(DepthWeightedSourceBoundary):
    def gradient(self, scalar, exterior_scalar):
        if not hasattr(self, 'primitive_gradient'):
            self.primitive_gradient = ConnectedDepthWeightedScalarGradient(
                self.state[..., 0], self.original.dx,
                mass_rate=None if self.full_rate is None else self.full_rate[..., 0])
        return super().gradient(scalar, exterior_scalar)


@contextmanager
def connected_depth_weighted_forcing():
    import source_supported_pressure_reference as pressure
    original = pressure.SourceSupportedScalarBoundary
    pressure.SourceSupportedScalarBoundary = ConnectedDepthWeightedSourceBoundary
    try:
        yield
    finally:
        pressure.SourceSupportedScalarBoundary = original
