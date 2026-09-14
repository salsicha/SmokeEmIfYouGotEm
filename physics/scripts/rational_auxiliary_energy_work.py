"""Local auxiliary energy-work identity for the unchanged two-pole metric.

This differentiates a supplied physical state/direction; it does NOT alter the
direction to enforce energy conservation. In particular an auxiliary exchange
whose integral vanishes cannot remove the stress/transport energy defect.
Positive periodic smooth geometry only, including variable bed. No dry/open,
breaking, evolution, production-performance or gameplay qualification.
"""
import numpy as np
from patch_pressure_preconditioner import PatchPressureSystem
from rational_primal_energy import K0, evaluate, depth_gradient
from rational_dual_energy_reference import factor_direction
from rational_physical_momentum_rate import factor_transpose_direction
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate


def stationary_density(g, p, response):
    """Stationary local density, retaining finite solve error explicitly."""
    q = p / np.sqrt(g.h)[..., None]
    density = .5 * K0 * np.sum(q*q, axis=-1) + 9.81*g.h*(.5*g.h+g.bed)
    for pole in response['poles']:
        system = PatchPressureSystem(g, pole['beta'])
        z = pole['normalized_auxiliary_velocity']
        density += .5*pole['alpha']*(system.w(z)**2 + .75*system.v(z)**2
                    + np.sum((q-z)**2, axis=-1)/pole['beta'])
    return density


def graph_exchange(system, scalar_w, scalar_v, vector):
    """Actual factor-stencil exchange, not a cumulative/global flux fit.

    For each stored A[row,column], deposit a[row]*A[row,column]*x[column]
    at row and its exact negative at column's cell. Self edges cancel. Short
    periodic-axis aliases were combined by the authoritative factor assembly.
    The result equals a*(A*x)-x*(A.T*a) cell by cell. This is an auxiliary
    graph flux only, not a complete hydrodynamic energy flux.
    """
    vector = system._vector(vector)
    scalar_w = system.geometry._scalar(scalar_w)
    scalar_v = system.geometry._scalar(scalar_v)
    rows, cells = system.rows, system.columns//2
    transfer = (scalar_w.ravel()[rows]*system.w_coefficients
                + .75*scalar_v.ravel()[rows]*system.v_coefficients)*vector.ravel()[system.columns]
    incoming = np.bincount(rows, weights=transfer, minlength=system.h.size)
    outgoing = np.bincount(cells, weights=transfer, minlength=system.h.size)
    exchange = (incoming-outgoing).reshape(system.h.shape)
    if not np.isfinite(exchange).all():
        raise ValueError('Auxiliary exchange exceeds storage range')
    return exchange


def local_work(g, physical_momentum, depth_rate, physical_momentum_rate):
    if not isinstance(g, SmoothPressureGeometry):
        raise ValueError('Matching positive periodic smooth geometry required')
    h = g.h
    p = np.asarray(physical_momentum, dtype=float)
    ht = np.asarray(depth_rate, dtype=float)
    pt = np.asarray(physical_momentum_rate, dtype=float)
    if (p.shape != (*h.shape, 2) or pt.shape != p.shape or ht.shape != h.shape
            or not all(np.isfinite(a).all() for a in (p, ht, pt))):
        raise ValueError('Finite registered physical state and direction required')
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    response = evaluate(g, p, tangent=tangent)
    root = np.sqrt(h)[..., None]
    q = p/root
    qt = pt/root-(ht/(2*h))[..., None]*q
    gravity = 9.81*(h+g.bed)*ht
    rate = K0*np.sum(q*qt, axis=-1)+gravity
    explicit_work = rate.copy()
    exchange = np.zeros_like(h)
    residual_work = np.zeros_like(h)
    poles = []
    for pole in response['poles']:
        beta, alpha = pole['beta'], pole['alpha']
        system = PatchPressureSystem(g, beta)
        z = pole['normalized_auxiliary_velocity']
        w, v = system.w(z), system.v(z)
        wt, vt = factor_direction(g, tangent, z)
        qz = system.transpose_w(w)+.75*system.transpose_v(v)
        qtz = (factor_transpose_direction(system, tangent, w)+system.transpose_w(wt)
               + .75*(factor_transpose_direction(system, tangent, v, bottom=True)
                        + system.transpose_v(vt)))
        zt, stats = system.solve(qt-beta*qtz, iterations=40, preconditioner='patch')
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Unqualified auxiliary energy derivative solve')
        mismatch = (q-z)/beta
        stationarity = qz-mismatch
        rate += alpha*(w*(wt+system.w(zt))+.75*v*(vt+system.v(zt))
                       + np.sum(mismatch*(qt-zt), axis=-1))
        explicit_work += alpha*(w*wt+.75*v*vt+np.sum(mismatch*qt, axis=-1))
        exchange += alpha*graph_exchange(system, w, v, zt)
        residual_work += alpha*np.sum(stationarity*zt, axis=-1)
        poles.append(dict(beta=beta, alpha=alpha,
                          maximum_stationarity_residual=float(abs(stationarity).max()), **stats))
    eh, _ = depth_gradient(g, p, response, ht)
    coordinate_work = eh*ht+np.sum(response['canonical_velocity']*pt, axis=-1)
    area = g.dx**2
    if not all(np.isfinite(a).all() for a in (rate, explicit_work, residual_work)):
        raise ValueError('Local energy work exceeds storage range')
    return dict(local_energy_rate=rate, explicit_local_work=explicit_work,
        auxiliary_exchange=exchange, stationarity_residual_work=residual_work,
        local_balance_error=float(abs(rate-explicit_work-exchange-residual_work).max()),
        integrated_auxiliary_exchange=float(exchange.sum())*area,
        integrated_stationarity_residual_work=float(residual_work.sum())*area,
        integrated_energy_rate=float(rate.sum())*area,
        integrated_coordinate_work=float(coordinate_work.sum())*area,
        coordinate_work_error=float(abs(rate.sum()-coordinate_work.sum()))*area,
        poles=poles, energy_conservation_or_gameplay_accepted=False)
