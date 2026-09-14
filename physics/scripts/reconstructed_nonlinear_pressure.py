"""Nonlinear pressure correction for the reconstructed D/E RESEARCH operator.

Homogeneous or original prescribed-velocity boundaries include partial-time
trace derivatives. The default rejects changing exact-dry sets. An explicit
directional_limit research mode evaluates the analytic linear conserved-ray
limit, including entering momentum, without constructing an epsilon-depth
state. Both modes use actual FV rates; no dropped rates, front freeze or fallback.
No native/playable integration or full-history qualification is implied.
"""
from fractions import Fraction as F
import numpy as np
from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing, DryGeometryTransition
from reconstructed_acceleration_system import ReconstructedAccelerationSystem, mass_scaled
from pressure_cut_face_reference import represented_float


def nonlinear_pressure(geometry, velocity, mass_rate, momentum_rate, *, rational=True,
                       dispersion_fraction=None, preconditioner='diagonal', boundary_velocity=None,
                       dry_treatment='reject'):
    h = geometry.h
    u, mt = np.asarray(velocity, dtype=float), np.asarray(momentum_rate, dtype=float)
    if (u.shape != (*h.shape, 2) or mt.shape != u.shape or not np.isfinite(mt).all()
            or not np.isfinite(u).all() or np.any(u[h == 0] != 0)):
        raise ValueError('Invalid original FV momentum rate or velocity shape')
    if dry_treatment not in ('reject', 'directional_limit'):
        raise ValueError('Unknown research dry treatment')
    ht = np.asarray(mass_rate, dtype=float)
    if ht.shape != h.shape or not np.isfinite(ht).all():
        raise ValueError('Invalid original FV mass rate')
    activating = (h == 0) & (ht > 0)
    directional = dry_treatment == 'directional_limit' and bool(np.any(activating))
    if directional:
        from directional_pressure_geometry import DirectionalPressureGeometry
        geometry = DirectionalPressureGeometry(geometry, ht)
        tangent = geometry.tangent
        # This separate trace is the exact linear conserved ray's limit m_t/h_t,
        # not a velocity written into an original dry cell or a repaired rate.
        u = u.copy()
        for point in map(tuple, np.argwhere(activating)):
            for component in (0, 1):
                u[point][component] = represented_float(F(float(mt[point][component]))/F(float(ht[point])))
    else:
        tangent = PressureGeometryRate(geometry, geometry.bed, ht)
    if np.any(mt[(h == 0) & ~activating] != 0):
        raise DryGeometryTransition('Dry cell has a nonzero momentum rate; no stationary-set pressure solve')
    q, c, adv = kinematic_forcing(geometry, tangent, u, boundary_velocity=boundary_velocity)
    base = np.zeros_like(u); qbar, cbar = np.zeros_like(h), np.zeros_like(h)
    for point in np.ndindex(h.shape):
        hi = F(float(h[point]))
        if not hi:
            # Along the exact linear ray, m/h=m_t/h_t is constant, so its
            # partial-time velocity derivative vanishes BEFORE normalization.
            # Q/C are finite on this analytic branch; sqrt(h)*C, h^1.5*Q and
            # sqrt(h)*Adv therefore tend to zero. No represented residual is
            # overwritten: there is no fabricated positive-depth ray state.
            continue
        qbar[point] = mass_scaled(hi*F(float(q[point])), hi, F(1))
        cbar[point] = mass_scaled(F(float(c[point])), hi, F(1))
        for component in (0, 1):
            # Combine conservative rate terms BEFORE dividing by sqrt(h).
            rate = (F(float(mt[point][component]))-F(float(u[point][component]))*
                    F(float(tangent.mass_rate[point]))+hi*F(float(adv[point][component])))
            base[point][component] = mass_scaled(rate, F(1), hi)
    lengths, weights = (LENGTHS, WEIGHTS) if rational else ([1/3], [1.])
    force = np.zeros_like(u); poles = []
    for length, weight in zip(lengths, weights):
        system = ReconstructedAccelerationSystem(geometry, float(length), dispersion_fraction=dispersion_fraction,
                                                project_zero_mass_rows=directional)
        fraction = system.fraction
        base_w, base_v = system.w(base), system.v(base)
        # L(Pforcing,Bforcing)/sqrt(h) = length*(-W.T*f*(qbar+1.5*cbar)
        #                                      +.75*V.T*f*cbar).
        # Construct K*base directly, not A*base-base (cancellation).
        rhs = length*(system.transpose_w(fraction*(qbar+1.5*cbar))
                      -.75*system.transpose_v(fraction*cbar)
                      -system.transpose_w(fraction*base_w)-.75*system.transpose_v(fraction*base_v))
        correction, stats = system.solve(rhs, preconditioner=preconditioner)
        w, v = base_w+system.w(correction), base_v+system.v(correction)
        p, b = np.zeros_like(h), np.zeros_like(h)
        for point in np.ndindex(h.shape):
            hi = F(float(h[point]))
            if not hi: continue
            factor = F(float(length))*F(float(fraction[point]))
            qi, ci, wi, vi = map(lambda a: F(float(a[point])), (qbar, cbar, w, v))
            p[point] = mass_scaled(factor*hi*(qi+F(3, 2)*ci-wi), hi, F(1))
            b[point] = mass_scaled(factor*(F(3, 2)*qi+3*ci-F(3, 2)*wi+F(3, 4)*vi), hi, F(1))
        pole_force = -geometry.gradient_traction(p, b)
        force += weight*pole_force
        poles.append(dict(length=float(length), weight=float(weight), pressure=p, bottom_pressure=b,
            correction=correction, rhs=rhs, base=base.copy(), force=pole_force, **stats))
    if not np.isfinite(force).all(): raise ValueError('Reconstructed pressure force exceeds storage range')
    return force, dict(scope=__doc__, poles=poles,
        quadratic=q, curvature=c, advective=adv,
        dry_treatment=dry_treatment, directional_extension_used=directional,
        velocity_trace=u.copy(), activating_dry_cells=int(np.sum(activating)),
        geometry_value_discrepancy_bounds=tangent.maximum_value_discrepancy)
