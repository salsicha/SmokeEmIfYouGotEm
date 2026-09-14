"""Closed-control periodic extension of the connected research derivative.

Periodic halo values are exact copies of the explicitly periodic domain,
not a replacement for real open-river source support. This context is for
isolated CPU audits only; pressure D/E and their adjoints remain unchanged.
"""
from contextlib import contextmanager
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from connected_depth_weighted_scalar_gradient import ConnectedDepthWeightedScalarGradient


def gradient(geometry, scalar):
    if not geometry.periodic:
        raise ValueError('Periodic audit cannot supply open-boundary scalar data')
    f=geometry._scalar(scalar)
    if np.any(geometry.h<=0):
        raise ValueError('This energy control is fully positive only')
    h=np.pad(geometry.h,3,mode='wrap')
    values=np.pad(f,3,mode='wrap')
    return ConnectedDepthWeightedScalarGradient(h,geometry.dx).gradient(values)[3:-3,3:-3].copy()


@contextmanager
def periodic_connected_gradients():
    original=ReconstructedPressureGeometry.scalar_gradient
    ReconstructedPressureGeometry.scalar_gradient=gradient
    try:
        yield
    finally:
        ReconstructedPressureGeometry.scalar_gradient=original
