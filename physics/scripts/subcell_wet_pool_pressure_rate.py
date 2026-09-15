"""Analytic fixed-topology pressure/dual-energy volume directions.

These are derivatives of the original two-pole map, NOT a mass flux, nonlinear
equation of motion, topology transition, time integrator or gameplay closure.
"""
import math
import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_mechanical_energy import squared_depth_integral
from subcell_wet_pool_pressure import WetPoolPressureSystem, harmonic_area, shared_subsegments
from triangle_face_section import TriangleFaceSection


def harmonic_area_rate(segment, lh, rh, ld, rd, left_rate, right_rate):
    """Exact integral of the two stage partials on the common wet interval.

    The moving shoreline boundary term is zero because its harmonic column is
    zero. For lower depth t and stage difference d, the two partials are
    .5*(1 +/- d/(2*t+d))**2. Integrating these avoids differencing areas and
    does not differentiate a numerically selected antiderivative branch.
    """
    harmonic_area(segment, lh, rh, ld, rd)  # Validate the same represented inputs.
    if not np.isfinite([left_rate, right_rate]).all():
        raise ValueError('Finite stage directions required')
    segment = np.asarray(segment, float)
    width = segment[1, 0]-segment[0, 0]
    delta = math.fsum((rd, -ld, rh, -lh))
    if delta < 0:
        lh, rh, ld, rd = rh, lh, rd, ld
        left_rate, right_rate = right_rate, left_rate
        delta = -delta
    low, high = np.sort(segment[:, 1])
    a = math.fsum((lh, ld, -float(high)))
    b = math.fsum((lh, ld, -float(low)))
    if b == 0 and high == low:
        raise ValueError('Level-dry face requires a one-sided topology transition')
    if b <= 0:
        return 0.
    if a < 0:
        width *= b/(high-low)
        a = 0.
    if delta == 0:
        return .5*width*(left_rate+right_rate)
    denominator = 2*a+delta
    span = b-a
    ratio = delta/denominator
    z = 2*span/denominator
    log_mean = math.log1p(z)/z if z > 0 and math.isfinite(z) else (1. if z == 0 else 0.)
    first = ratio*log_mean
    second = ratio*(delta/(2*b+delta))
    # Direct square for a flat face avoids subtracting nearly equal terms in
    # the upper-stage partial when one side is extremely shallow.
    if span == 0:
        lower = .5*(1+ratio)**2
        upper = 2*(a/denominator)**2
    elif z < .01:
        # Integral (1-d/s)^2 = (1-r)^2 + 2r(1-r)<w> + r^2<w^2>,
        # w=(s-den)/s. Positive leading terms retain thin upper-side rates.
        mean_w = sum((-1)**(k+1)*z**k/(k+1) for k in range(1, 13))
        mean_w2 = sum((-1)**k*(k-1)*z**k/(k+1) for k in range(2, 14))
        one_minus = 2*a/denominator
        upper = .5*(one_minus**2+2*ratio*one_minus*mean_w+ratio**2*mean_w2)
        lower = .5*(1+2*first+second)
    else:
        lower, upper = .5*(1+2*first+second), .5*(1-2*first+second)
    result = width*(lower*left_rate+upper*right_rate)
    if not math.isfinite(result):
        raise ValueError('Shared column direction exceeds represented range')
    return result


class WetPoolPressureRate:
    """Derivative A_dot at FIXED normalized vector, including both roots."""
    def __init__(self, system, volume_rate):
        self.system = system
        vd = np.asarray(volume_rate, float)
        if vd.shape != system.h.shape or not np.isfinite(vd).all():
            raise ValueError('Finite volume direction with the pool-volume shape required')
        self.volume_rate = vd.copy()
        self.ell = .5*vd[:, 0]/system.h[:, 0]
        pools = system.partition.pools
        stage_rate = vd[:, 0]/np.array([p['form']['wet_area'] for p in pools])
        self.gram_rate = np.array([p['form']['volume_derivative']*v for p, v in zip(pools, vd[:, 0])])
        maps = [dict() for _ in pools]
        def add(row, column, value):
            maps[row][column] = maps[row].get(column, 0.)+value
        for left, right, axis, _ in system.partition.patch.faces:
            if left >= 0 and right >= 0:
                first = system.partition.boundary_segments(left, axis, 1)
                second = system.partition.boundary_segments(right, axis, -1)
                for li, ri, segment in shared_subsegments(first, second):
                    lp, rp = pools[li]['form'], pools[ri]['form']
                    args = (segment, lp['stage_offset'], rp['stage_offset'], lp['datum'], rp['datum'])
                    area = harmonic_area(*args)
                    rate = harmonic_area_rate(*args, stage_rate[li], stage_rate[ri])
                    for owner in (li, ri):
                        weight = (rate-2*self.ell[owner]*area)/(2*system.h[owner, 0])
                        add(owner, 2*ri+axis, weight)
                        add(owner, 2*li+axis, -weight)
            else:
                parent, sign = (right, -1) if left < 0 else (left, 1)
                for owner, segment in system.partition.boundary_segments(parent, axis, sign):
                    form = pools[owner]['form']
                    face = TriangleFaceSection([segment], segment[:, 0])
                    area, _, wet_width = face.moments(form['stage_offset'], form['datum'])
                    rate = wet_width*stage_rate[owner]
                    add(owner, 2*owner+axis, -sign*(rate-2*self.ell[owner]*area)/system.h[owner, 0])
        for face in system.partition.internal_faces:
            li, ri = face['left'], face['right']
            if li is None or ri is None:
                continue
            lf, rf = pools[li]['form'], pools[ri]['form']
            args = (face['segment'], lf['stage_offset'], rf['stage_offset'], lf['datum'], rf['datum'])
            area = harmonic_area(*args)
            rate = harmonic_area_rate(*args, stage_rate[li], stage_rate[ri])
            for owner in (li, ri):
                for axis, normal in enumerate(face['normal']):
                    weight = normal*(rate-2*self.ell[owner]*area)/(2*system.h[owner, 0])
                    add(owner, 2*ri+axis, weight)
                    add(owner, 2*li+axis, -weight)
        entries = [(r, c, v) for r, row in enumerate(maps) for c, v in row.items() if v != 0]
        self.rows = np.array([r for r, _, _ in entries], int)
        self.columns = np.array([c for _, c, _ in entries], int)
        self.coefficients = np.array([v for _, _, v in entries])
        if not all(np.isfinite(x).all() for x in (self.ell, stage_rate, self.gram_rate, self.coefficients)):
            raise ValueError('Wet-pool pressure direction exceeds represented range')

    def divergence_rate(self, velocity):
        return np.bincount(self.rows, weights=self.coefficients*velocity.ravel()[self.columns],
                           minlength=len(self.system.h))

    def transpose_rate(self, scalar):
        return np.bincount(self.columns, weights=self.coefficients*scalar[self.rows],
                           minlength=2*len(self.system.h)).reshape(-1, 2)

    def apply(self, q):
        s = self.system
        u = s._vector(q)[:, 0]/s.root[:, None]
        ud = -self.ell[:, None]*u
        jet = np.column_stack((s.divergence(u), u))
        jet_rate = np.column_stack((self.divergence_rate(u)+s.divergence(ud), ud))
        gram = np.array([p['form']['gram'] for p in s.partition.pools])
        f = np.einsum('nij,nj->ni', gram, jet)
        fd = np.einsum('nij,nj->ni', self.gram_rate, jet)+np.einsum('nij,nj->ni', gram, jet_rate)
        physical = s.divergence_transpose(f[:, 0])+f[:, 1:]
        physical_rate = self.transpose_rate(f[:, 0])+s.divergence_transpose(fd[:, 0])+fd[:, 1:]
        return (s.length*(physical_rate-self.ell[:, None]*physical)/s.root[:, None])[:, None, :]


def dual_direction(partition, canonical_velocity, volume_rate, canonical_velocity_rate=None, gravity=9.81):
    """Directional dual energy and physical momentum, with original 40-CG poles.

    Input rates are caller-specified directions, not inferred mass/advection.
    No assertion that energy_rate is zero, or that any state has advanced.
    """
    first = WetPoolPressureSystem(partition, float(LENGTHS[0]))
    v = first._vector(canonical_velocity)
    vt = np.zeros_like(v) if canonical_velocity_rate is None else first._vector(canonical_velocity_rate)
    tangent = WetPoolPressureRate(first, volume_rate)
    if not np.isfinite(gravity) or gravity <= 0:
        raise ValueError('Positive finite gravity required')
    root = first.root[:, None, None]
    ell = tangent.ell[:, None, None]
    q, qt = root*v, root*vt+ell*root*v
    constant = 1-float(np.sum(WEIGHTS))
    sq, sqt = constant*q, constant*qt
    metric_work, records = 0., []
    for i, (length, weight) in enumerate(zip(LENGTHS, WEIGHTS)):
        system = first if i == 0 else WetPoolPressureSystem(partition, float(length))
        rate = tangent if i == 0 else WetPoolPressureRate(system, volume_rate)
        z, stats = system.solve(q)
        az = rate.apply(z)
        zt, rate_stats = system.solve(qt-az)
        if max(stats['relative_residual'], rate_stats['relative_residual']) > 2e-5:
            raise ValueError('Original 40-CG pressure/direction residual gate failed')
        sq += weight*z
        sqt += weight*zt
        metric_work += float(weight*np.sum(z*az))
        records.append(dict(length=float(length), weight=float(weight), solve=stats, direction_solve=rate_stats))
    kinetic = float(.5*np.sum(q*sq))
    kinetic_rate = float(np.sum(qt*sq)-.5*metric_work)
    datum = min(float(cell.datum) for cell in partition.patch.cells)
    potential, potential_rate = 0., 0.
    for pool, vd in zip(partition.pools, tangent.volume_rate[:, 0]):
        form = pool['form']
        height = math.fsum((form['stage_offset'], form['datum'], -datum))
        potential += gravity*(height*pool['volume']-.5*squared_depth_integral(pool['storage'], form['stage_offset'], True))
        potential_rate += gravity*height*vd
    return dict(physical_momentum=root*sq, physical_momentum_rate=ell*root*sq+root*sqt,
        kinetic=kinetic, potential=float(potential), total=kinetic+float(potential),
        kinetic_rate=kinetic_rate, potential_rate=float(potential_rate), total_rate=kinetic_rate+float(potential_rate),
        reference_datum_m=datum, poles=records,
        nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
