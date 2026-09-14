"""Actual-mass-rate tangent of the integrated/shared-bottom RESEARCH geometry.

Differentiate the original MC and cut polynomials on represented inputs, before
rounding their outputs. Exact rational scalar arithmetic resolves MC ties and
cut boundaries. Report differences between these exact polynomial values and
the existing rounded static geometry; do not repair caller state or geometry.

The default requires a stationary exact-dry set. Explicit one_sided assembly
instead exposes the analytic right-limit coefficients and derivatives, which
must be bound to DirectionalPressureGeometry before actions are evaluated.
No rate is frozen or discarded. This module does not solve or integrate water.
"""
from fractions import Fraction as F
import numpy as np
from pressure_cut_face_reference import cut_pressure_column, represented_float


class DryGeometryTransition(ValueError):
    pass


def mc_dual(back, front, back_rate, front_rate):
    """Exact MC value and right directional derivative, including tied branches."""
    candidates = [(2*back, 2*back_rate), ((back+front)/2, (back_rate+front_rate)/2),
                  (2*front, 2*front_rate)]
    if all(v > 0 or (v == 0 and d >= 0) for v, d in candidates):
        return min(candidates)
    if all(v < 0 or (v == 0 and d <= 0) for v, d in candidates):
        return max(candidates)
    return F(0), F(0)


def positive_dual(value, rate):
    return (value, rate) if value > 0 else (F(0), max(F(0), rate) if value == 0 else F(0))


class PressureGeometryRate:
    def __init__(self, geometry, bed, mass_rate, *, one_sided=False):
        if geometry.pressure_trace != 'integrated_column' or geometry.bed_quadrature != 'shared_bottom':
            raise ValueError('Mass tangent requires integrated/shared-bottom research geometry')
        h = geometry.h; bed = np.asarray(bed, dtype=float); ht = np.asarray(mass_rate, dtype=float)
        if bed.shape != h.shape or ht.shape != h.shape or not np.isfinite(bed).all() or not np.isfinite(ht).all():
            raise ValueError('Invalid original bed or actual FV mass rate')
        if not np.array_equal(bed, geometry.bed):
            raise ValueError('Tangent bed differs from the original static geometry')
        if np.any((h == 0) & (ht < 0)):
            raise ValueError('Negative mass rate in an exactly dry cell; no repair')
        if type(one_sided) is not bool:
            raise ValueError('Invalid directional geometry mode')
        if np.any((h == 0) & (ht > 0)) and not one_sided:
            raise DryGeometryTransition('Exactly dry owner begins wetting; its geometry/stencil derivative is not yet qualified')
        self.geometry = geometry
        self.source_geometry = geometry
        self.one_sided = one_sided
        self.mass_rate = ht.copy(); self.mass_rate.flags.writeable = False
        self.edges = []
        self.directional_support = (h > 0) | ((ht > 0) if one_sided else False)
        self.directional_support.flags.writeable = False
        self.coefficient_limits = []; self.polynomial_limits = []
        errors = {name: F(0) for name in ('ha', 'hb', 'fa', 'fb', 'aa', 'ab', 'ca', 'cb', 'own', 'other', 'shared_b')}
        for axis, edge, static in zip((1, 0), geometry.edges, geometry.polynomials):
            n = h.shape[axis]; cache = {}
            def polynomial(point):
                if point in cache:
                    return cache[point]
                coordinate = point[axis]
                hi, zi, hi_t = F(float(h[point])), F(float(bed[point])), F(float(ht[point]))
                dh = de = dh_t = de_t = F(0)
                if self.directional_support[point] and (geometry.periodic or 0 < coordinate < n-1):
                    a, b = list(point), list(point)
                    a[axis], b[axis] = (coordinate-1) % n, (coordinate+1) % n
                    a, b = tuple(a), tuple(b)
                    if self.directional_support[a] and self.directional_support[b]:
                        back, front = hi-F(float(h[a])), F(float(h[b]))-hi
                        back_t, front_t = hi_t-F(float(ht[a])), F(float(ht[b]))-hi_t
                        dh, dh_t = mc_dual(back, front, back_t, front_t)
                        de, de_t = mc_dual(back+zi-F(float(bed[a])), front+F(float(bed[b]))-zi, back_t, front_t)
                cache[point] = hi, zi, hi_t, dh, de, dh_t, de_t
                return cache[point]
            rates = {name: np.zeros_like(h) for name in ('aa', 'ab', 'ca', 'cb', 'own', 'other', 'shared_b')}
            limits = {name: np.zeros_like(h) for name in rates}
            polys = {name: np.zeros_like(h) for name in ('ha', 'hb', 'fa', 'fb', 'dh', 'deta')}
            for point in np.ndindex(h.shape):
                if n == 1 or (not geometry.periodic and point[axis] == n-1):
                    continue
                neighbor = list(point); neighbor[axis] = (point[axis]+1) % n; neighbor = tuple(neighbor)
                hi, zi, ti, dhi, dei, dhi_t, dei_t = polynomial(point)
                hj, zj, tj, dhj, dej, dhj_t, dej_t = polynomial(neighbor)
                ha, hb = hi+dhi/2, hj-dhj/2
                ha_t, hb_t = ti+dhi_t/2, tj-dhj_t/2
                jump = zj-zi-(dei-dhi+dej-dhj)/2
                jump_t = -(dei_t-dhi_t+dej_t-dhj_t)/2
                ja, ja_t = positive_dual(jump, jump_t)
                jb, jb_t = positive_dual(-jump, -jump_t)
                fa, fa_t = positive_dual(ha-ja, ha_t-ja_t)
                fb, fb_t = positive_dual(hb-jb, hb_t-jb_t)
                values = dict(ha=ha, hb=hb, fa=fa, fb=fb)
                exact_rates = dict(aa=F(0), ab=F(0), ca=F(0), cb=F(0))
                for side, height, wet, height_t, wet_t in (('a', ha, fa, ha_t, fa_t), ('b', hb, fb, hb_t, fb_t)):
                    if height == 0:
                        if one_sided and height_t > 0:
                            if wet != 0:
                                raise DryGeometryTransition('Nonzero retained column at a zero-height limit')
                            # H=t*H_t, R=t*R_t on this one-sided MC branch:
                            # A has a finite constant limit; C=t*C(H_t,R_t).
                            # No positive-depth probe or pressure-column floor.
                            ac = cut_pressure_column(height_t, F(1), F(0), wet_t)
                            cc = cut_pressure_column(height_t, F(0), F(1), wet_t)
                            values['a'+side], values['c'+side] = ac.transmitted, F(0)
                            exact_rates['c'+side] = cc.transmitted
                            rates['c'+side][point] = represented_float(cc.transmitted)
                            continue
                        if one_sided and (hi if side == 'a' else hj) > 0:
                            raise DryGeometryTransition('Positive owner has an identically zero reconstructed column on this direction')
                        # Exact dry set is stationary. Its unnormalized column
                        # and pressure contribution are zero, not floored.
                        if height_t or wet or wet_t:
                            raise DryGeometryTransition('A zero reconstructed column has a nonstationary tangent')
                        values['a'+side] = values['c'+side] = F(0)
                        continue
                    ac = cut_pressure_column(height, F(1), F(0), wet,
                        height_rate=height_t, retained_height_rate=wet_t)
                    cc = cut_pressure_column(height, F(0), F(1), wet,
                        height_rate=height_t, retained_height_rate=wet_t)
                    values['a'+side], values['c'+side] = ac.transmitted, cc.transmitted
                    exact_rates['a'+side], exact_rates['c'+side] = ac.transmitted_rate, cc.transmitted_rate
                    rates['a'+side][point] = represented_float(ac.transmitted_rate)
                    rates['c'+side][point] = represented_float(cc.transmitted_rate)
                total = hi+hj
                own = hi/total if total else F(0); other = hj/total if total else F(0)
                if one_sided and not total and ti+tj > 0:
                    own, other = ti/(ti+tj), tj/(ti+tj)
                own_t = (ti*other-own*tj)/total if total else F(0)
                rates['own'][point] = represented_float(own_t)
                rates['other'][point] = -rates['own'][point]
                values['own'], values['other'] = own, other
                # Use exact rates before rounding in the product rule.
                # Values/rates for either dry column are exactly zero.
                values['shared_b'] = own*other*(values['cb']-values['ca'])
                k_t = own_t*(other-own)*(values['cb']-values['ca'])+own*other*(exact_rates['cb']-exact_rates['ca'])
                rates['shared_b'][point] = represented_float(k_t)
                for name, exact in values.items():
                    target = polys if name in ('ha', 'hb', 'fa', 'fb') else limits
                    target[name][point] = represented_float(exact)
                    stored = static[name][point] if name in ('ha', 'hb', 'fa', 'fb') else edge[name][point]
                    errors[name] = max(errors[name], abs(exact-F(float(stored))))
            for point in np.ndindex(h.shape):
                _, _, _, dh, de, _, _ = polynomial(point)
                polys['dh'][point], polys['deta'][point] = represented_float(dh), represented_float(de)
            for value in (*rates.values(), *limits.values(), *polys.values()):
                value.flags.writeable = False
            self.edges.append(rates)
            self.coefficient_limits.append(limits); self.polynomial_limits.append(polys)
        # Only diagnostic error bounds round upward, including subnormal error
        # bounds. No physical coefficient, rate, depth or state is floored.
        self.maximum_value_discrepancy = {}
        for name, value in errors.items():
            bound = float(value)
            if F(bound) < value:
                bound = float(np.nextafter(bound, np.inf))
            self.maximum_value_discrepancy[name] = bound

    def kinematic_rate(self, velocity):
        """D_t u and E_t u at FIXED u; not the total derivative of D/E applied to u."""
        if self.one_sided and self.geometry is self.source_geometry:
            raise ValueError('One-sided rates must be bound to their limit geometry')
        g = self.geometry; u = np.asarray(velocity, dtype=float)
        if u.shape != (*g.h.shape, 2) or not np.isfinite(u).all():
            raise ValueError('Invalid fixed velocity for geometry rate')
        d, e = np.zeros_like(g.h), np.zeros_like(g.h)
        for component, (axis, edge, rate) in enumerate(zip((1, 0), g.edges, self.edges)):
            value = u[..., component]
            face = edge['own']*value+edge['other']*np.roll(value, -1, axis)
            face_t = rate['own']*value+rate['other']*np.roll(value, -1, axis)
            d += (rate['aa']*face+edge['aa']*face_t-
                  np.roll(rate['ab']*face+edge['ab']*face_t, 1, axis))/g.dx
            k = rate['shared_b']
            e += (k*(np.roll(value, -1, axis)-value)+np.roll(k, 1, axis)*(np.roll(value, 1, axis)-value))/g.dx
        if not np.isfinite(d).all() or not np.isfinite(e).all():
            raise ValueError('Geometry rate exceeds scalar storage range')
        return d, e

    def force_operator_rate(self, integrated, bottom):
        """L_t(P,B)=-D_t^T P+E_t^T B at fixed pressure; same signed coefficients."""
        if self.one_sided and self.geometry is self.source_geometry:
            raise ValueError('One-sided rates must be bound to their limit geometry')
        g = self.geometry; p, b = g._scalar(integrated), g._scalar(bottom)
        if np.any(p[g.h == 0] != 0) or np.any(b[g.h == 0] != 0):
            raise ValueError('Dry cells have no pressure column')
        result = []
        for axis, edge, rate in zip((1, 0), g.edges, self.edges):
            jump = edge['ab']*np.roll(p, -1, axis)-edge['aa']*p
            jump_t = rate['ab']*np.roll(p, -1, axis)-rate['aa']*p
            value = rate['own']*jump+edge['own']*jump_t
            value += np.roll(rate['other']*jump+edge['other']*jump_t, 1, axis)
            k = rate['shared_b']
            value += k*(np.roll(b, -1, axis)-b)+np.roll(k, 1, axis)*(np.roll(b, 1, axis)-b)
            result.append(value/g.dx)
        result = np.stack(result, axis=-1)
        if not np.isfinite(result).all():
            raise ValueError('Pressure force geometry rate exceeds scalar storage range')
        return result


def kinematic_forcing(geometry, geometry_rate, velocity, *, boundary_velocity=None):
    """Q,C,Adv in q=Q-Da and c=Ea+C, including BOTH geometry time derivatives.

    Optional original prescribed velocity/time-rate traces add an affine
    divergence lift, not a new unknown or change to the pressure adjoint.
    G=-D^T is used consistently for the horizontal advective derivatives.
    """
    if geometry_rate.geometry is not geometry:
        raise ValueError('Forcing geometry and its actual-mass-rate tangent must match')
    u = np.asarray(velocity, dtype=float)
    if u.shape != (*geometry.h.shape, 2) or not np.isfinite(u).all() or np.any(u[~geometry.kinematic_support] != 0):
        raise ValueError('Invalid physical velocity for kinematic pressure forcing')
    grad = geometry.scalar_gradient
    advective = np.stack([np.sum(u*grad(u[..., c]), axis=-1) for c in (0, 1)], axis=-1)
    d, e = geometry.kinematic_components(u)
    dt, et = geometry_rate.kinematic_rate(u)
    if boundary_velocity is not None:
        lift = geometry.prescribed_divergence_lift(boundary_velocity)
        d = d+lift[..., 0]
        dt = dt+lift[..., 1]
    da, ea = geometry.kinematic_components(advective)
    q = d*d+da-dt-np.sum(u*grad(d), axis=-1)
    c = et+np.sum(u*grad(e), axis=-1)-ea
    if not all(np.isfinite(value).all() for value in (q, c, advective)):
        raise ValueError('Nonfinite reconstructed kinematic forcing')
    return q, c, advective
