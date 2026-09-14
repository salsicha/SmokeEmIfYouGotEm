"""Process-scoped RESEARCH pressure adapter; original FV/RK/CFL gates unchanged.

Use only in explicit independent CPU replays. Context cleanup restores both
functions even after a failed rate/solve. Never installs a native/gameplay mode.
"""
from contextlib import contextmanager
import numpy as np
import total_depth_bank_replay as bank
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_nonlinear_pressure import nonlinear_pressure


@contextmanager
def reconstructed_pressure(on_stage=None):
    original_rate, original_pressure = bank.rate, bank.nonlinear_pressure_force
    contexts = []
    def rate(*args, **kwargs):
        exterior = kwargs.get('exterior')
        contexts.append(dict(periodic=kwargs.get('periodic', False),
                             exterior_bed=exterior[1] if exterior is not None else None))
        try: return original_rate(*args, **kwargs)
        finally: contexts.pop()
    def pressure(depth, bed, velocity, hydro_force, pairs, dx, **kwargs):
        if (not contexts or kwargs.get('formulation') != 'kinematic'
                or kwargs.get('interpolation') != 'depth_weighted'):
            raise ValueError('Reconstructed adapter requires its scoped original FV kinematic call')
        context = contexts[-1]
        g = ReconstructedPressureGeometry(depth, bed, dx, **context,
            pressure_trace='integrated_column', bed_quadrature='shared_bottom')
        if not np.array_equal(g.physical_slope, kwargs.get('bed_slope')):
            raise ValueError('Reconstructed adapter exterior bed differs from original FV pressure geometry')
        force, result = nonlinear_pressure(g, velocity, kwargs['mass_rate'], kwargs['momentum_rate'],
            rational=kwargs.get('rational', True), dispersion_fraction=kwargs.get('dispersion_fraction'),
            boundary_velocity=kwargs.get('boundary_velocity'), preconditioner='block', dry_treatment='directional_limit')
        stats = [{key: p[key] for key in ('iterations', 'relative_residual')} for p in result['poles']]
        if on_stage is not None:
            on_stage(dict(activating_dry_cells=result['activating_dry_cells'],
                directional_extension_used=result['directional_extension_used'],
                maximum_pressure_force=float(abs(force).max()), pressure_stats=stats))
        return force, stats
    bank.rate, bank.nonlinear_pressure_force = rate, pressure
    try: yield
    finally: bank.rate, bank.nonlinear_pressure_force = original_rate, original_pressure
