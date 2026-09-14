"""Analytic one-sided original-MC pressure geometry on a conserved mass ray.

Depth and bed remain the original immutable arrays, including exact zeros.
Only operator limits and their right derivatives are evaluated on the support
h>0 or (h==0 and actual h_t>0). No epsilon-depth state is constructed. This is
a RESEARCH directional extension, not full-history wet/dry qualification.
"""
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate


class DirectionalPressureGeometry(ReconstructedPressureGeometry):
    def __init__(self, source, mass_rate):
        tangent = PressureGeometryRate(source, source.bed, mass_rate, one_sided=True)
        self.source_geometry = source
        for name in ('h', 'bed', 'dx', 'periodic', 'pressure_trace', 'bed_quadrature', 'physical_slope'):
            setattr(self, name, getattr(source, name))
        self.support = tangent.directional_support
        self.edges, self.polynomials = [], tangent.polynomial_limits
        for component, (limits, poly) in enumerate(zip(tangent.coefficient_limits, self.polynomials)):
            edge = dict(limits, local_p=np.zeros_like(self.h), local_b=poly['deta']-poly['dh'],
                        physical_b=np.where(self.support, self.physical_slope[..., component], 0.))
            for value in edge.values(): value.flags.writeable = False
            self.edges.append(edge)
        tangent.geometry = self
        self.tangent = tangent

    @property
    def kinematic_support(self):
        return self.support
