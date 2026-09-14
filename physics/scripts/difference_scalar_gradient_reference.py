"""Research scalar-advection derivative; no native or playable installation.

The pressure force G=-D.T remains unchanged. Ordinary scalar derivatives instead
use the same off-diagonal coefficients on differences of scalar values. This
removes G(1)*f without subtracting two rounded large actions. It exactly
annihilates constants, but that alone does not qualify wet/dry evolution or energy.
"""
from contextlib import contextmanager
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def difference_gradient(geometry, scalar):
    f = geometry._scalar(scalar)
    result = []
    for axis, edge in zip((1, 0), geometry.edges):
        right = edge['own'] * edge['ab'] * (np.roll(f, -1, axis)-f)
        left = np.roll(edge['other'], 1, axis) * np.roll(edge['aa'], 1, axis) * (f-np.roll(f, 1, axis))
        result.append((right+left)/geometry.dx)
    value = np.stack(result, axis=-1)
    if not np.isfinite(value).all():
        raise ValueError('Difference scalar derivative exceeds storage range')
    return value


@contextmanager
def difference_scalar_gradients():
    original = ReconstructedPressureGeometry.scalar_gradient
    ReconstructedPressureGeometry.scalar_gradient = difference_gradient
    try:
        yield
    finally:
        ReconstructedPressureGeometry.scalar_gradient = original
