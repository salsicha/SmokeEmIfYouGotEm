"""Isolated CPU coupling of source-supported forcing to the ORIGINAL two poles.

The original nonlinear pressure routine owns directional support, normalization,
pole lengths/weights, force adjoints and true CG gates. Only its explicit forcing
binding is replaced during this call, then restored even on failure. Not thread
safe, not installed in native/playable code, and never used in running histories.
"""
import numpy as np
import reconstructed_nonlinear_pressure as pressure
from source_supported_scalar_boundary import SourceSupportedScalarBoundary,velocity_of


def solve(geometry,current_state,full_source_state,full_bed,full_rate,boundary_velocity,*,rational=True):
    ny,nx=geometry.h.shape;core=(slice(3,ny+3),slice(3,nx+3))
    rate=np.asarray(full_rate,dtype=float)
    if rate.shape!=(ny+6,nx+6,3) or not np.isfinite(rate).all():
        raise ValueError('Full source/current conserved rate required')
    original=pressure.kinematic_forcing
    def forcing(g,tangent,u,*,boundary_velocity=None):
        support=SourceSupportedScalarBoundary(g,current_state,full_source_state,full_bed,full_rate=rate)
        if not np.array_equal(support.velocity[core],u):
            raise ValueError('Original pressure velocity trace differs from actual conserved direction')
        return support.forcing(tangent,boundary_velocity)
    pressure.kinematic_forcing=forcing
    try:
        return pressure.nonlinear_pressure(geometry,velocity_of(current_state),rate[core][...,0],rate[core][...,1:],
            rational=rational,preconditioner='block',boundary_velocity=boundary_velocity,dry_treatment='directional_limit')
    finally:
        pressure.kinematic_forcing=original
