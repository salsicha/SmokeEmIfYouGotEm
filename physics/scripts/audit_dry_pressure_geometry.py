"""Read-only positive-mass direction probe at exactly dry pressure-geometry cells.

The small direction parameters are sensitivity probes, NOT timesteps used by
an evolved trajectory. Preserve all positive mass rates, including values below
native float32 storage. Pressure and velocity remain fixed to isolate geometry.
"""
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def locate_change(before, after, mask):
    """Locate a change without conflating dry rows and already wet rows."""
    points = np.argwhere(mask)
    if not len(points):
        return dict(maximum=0., yx=None)
    delta = after-before
    point = tuple(points[np.argmax(abs(delta[mask]))])
    return dict(maximum=float(abs(delta[point])), yx=list(map(int, point)),
                before=float(before[point]), after=float(after[point]))


def dry_mass_limit(geometry, mass_rate, velocity, integrated, bottom, *, exterior_bed=None):
    h = geometry.h; rate = np.asarray(mass_rate, dtype=float)
    if rate.shape != h.shape or not np.isfinite(rate).all() or np.any((h == 0) & (rate < 0)):
        raise ValueError('Invalid original mass direction')
    points = np.argwhere((h == 0) & (rate > 0))
    if not len(points):
        raise ValueError('A positive mass rate on an exactly dry cell is required')
    force = geometry.gradient_traction(integrated, bottom)
    d, e = geometry.kinematic_components(velocity)
    rows = []
    for parameter in (1e-12, 1e-20, 1e-28):
        later_h = h+parameter*rate
        if not np.isfinite(later_h).all() or np.any(later_h < 0) or np.any(later_h[tuple(points.T)] <= 0):
            raise ValueError('Sensitivity parameter leaves positive storage/physical range; no repair')
        later = ReconstructedPressureGeometry(later_h, geometry.bed, geometry.dx,
            periodic=geometry.periodic, pressure_trace=geometry.pressure_trace,
            bed_quadrature=geometry.bed_quadrature, exterior_bed=exterior_bed)
        dl, el = later.kinematic_components(velocity)
        change = later.gradient_traction(integrated, bottom)-force
        worst = tuple(np.unravel_index(abs(change).argmax(), change.shape))
        polynomial_changes = {}
        for name in ('dh', 'deta', 'ha', 'hb', 'fa', 'fb'):
            polynomial_changes[name] = max(float(abs(b[name]-a[name]).max()) for a, b in
                zip(geometry.polynomials, later.polynomials))
        rows.append(dict(parameter_seconds=parameter, maximum_depth_change=float(abs(later_h-h).max()),
            new_depths_at_activations=[float(later_h[tuple(p)]) for p in points],
            polynomial_changes=polynomial_changes, maximum_fixed_pressure_action_change=float(abs(change).max()),
            worst_action_yxc=list(map(int, worst)), action_change_at_worst=float(change[worst]),
            maximum_fixed_velocity_D_change=float(abs(dl-d).max()),
            maximum_fixed_velocity_E_change=float(abs(el-e).max()),
            D_change_by_original_support={name: locate_change(d, dl, mask) for name, mask in
                (('wet', h > 0), ('activating', (h == 0) & (rate > 0)), ('stationary_dry', (h == 0) & (rate == 0)))},
            column_velocity_change=locate_change(h*d, later_h*dl, np.ones_like(h, dtype=bool))))
    return dict(scope=__doc__, activations=[dict(yx=p.tolist(), original_mass_rate=float(rate[tuple(p)]),
        rounded_cpu_mass_rate_fp32=float(np.float32(rate[tuple(p)]))) for p in points], probes=rows,
        qualification='No geometry tangent or nonlinear evolution is qualified by this sensitivity probe.')
