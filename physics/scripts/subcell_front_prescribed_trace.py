"""Affine pressure-kinetic lifting of the original fan's exterior velocity.

The old reflecting divergence is the homogeneous part only. Prescribed outward
column flux adds b=integral(h u.n)/V, so the local jet is (D v+b,vx,vy).
Its kinetic functional is .5*v.K.v+l.v+c, not the reflecting quadratic alone.
This is a prescribed-trace reference component, NOT a radiation/open-pressure
condition, interacting-fan law, coupled force/time step or playable solver.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _line_integral
from subcell_affine_front_pressure import FrontPressureGeometry, face_metric


def face_mass_flux_rate(fan, first, last, time):
    """Exact physical-time derivative of the SAME outward fan mass flux.

    Head contributions cancel (continuous h*u); front contributions vanish.
    No finite differencing, depth averaging or rounded edge normal is used.
    """
    face_metric(fan, first, last, time)  # Original XYZ/time validation.
    a, b, t = tuple(map(F, first)), tuple(map(F, last)), F(time)
    head, front, linear, velocity, _ = fan._profile(t)
    normal = (b[1]-a[1], a[0]-b[0])
    acceleration = fan.gravity*sum(n*s for n, s in zip(fan.normal, fan.gradient))
    linear_rate = lambda p: fan._coordinate(p)/(t*t)-acceleration/2
    un = lambda p: sum((n*u(p) for n, u in zip(normal, velocity)), fan.zero)
    unt = lambda p: sum((n*(-2*m*linear_rate(p)/(3*fan.norm2)-fan.gravity*s)
                          for n, m, s in zip(normal, fan.normal, fan.gradient)), fan.zero)
    qa, qb = fan._coordinate(a), fan._coordinate(b)
    cuts = [fan.zero, fan.zero+1]
    if qa != qb:
        cuts += [s for bound in (head, front) if 0 < (s := (bound-qa)/(qb-qa)) < 1]
    point = lambda s: tuple(x+s*(y-x) for x, y in zip(a, b))
    result = fan.zero
    cuts = sorted(cuts)
    for lo, hi in zip(cuts, cuts[1:]):
        q = fan._coordinate(point((lo+hi)/2))
        if q >= front:
            continue
        if q <= head:
            result -= (hi-lo)*fan.depth*fan.gravity*sum(n*s for n, s in zip(normal, fan.gradient))
            continue
        ends = (point(lo), point(hi))
        result += (hi-lo)/(9*fan.gravity*fan.norm2)*(
            2*_line_integral(ends, [linear, linear_rate, un], fan.zero)
            +_line_integral(ends, [linear, linear, unt], fan.zero))
    return result


class FrontPrescribedTrace:
    def __init__(self, fan, fragments, time, *, boundary):
        if boundary != 'prescribed-fan-velocity':
            raise ValueError('Explicit prescribed fan velocity required; no natural open-pressure closure')
        self.geometry = g = FrontPressureGeometry(fan, fragments, time, outer_boundary='reflecting')
        self.zero = z = g.zero
        n = len(g.active)
        positions = {owner: row for row, owner in enumerate(g.active)}
        flux, flux_rate = [z]*n, [z]*n
        self.boundary_faces = []
        for face in g.faces:
            if len(face['owners']) != 1:
                continue
            owner = face['owners'][0]
            q = fan.face_flux(face['first'], face['last'], time)['volume_rate']
            qt = face_mass_flux_rate(fan, face['first'], face['last'], time)
            if owner not in positions:
                if q != 0 or qt != 0:
                    raise ValueError('Dry owner cannot carry a prescribed pressure trace')
                continue
            row = positions[owner]
            flux[row] += q
            flux_rate[row] += qt
            self.boundary_faces.append(dict(owner=owner, row=row, first=face['first'],
                                             last=face['last'], outward_mass_flux=q,
                                             outward_mass_flux_rate=qt))
        self.outward_mass_flux = tuple(flux)
        self.outward_mass_flux_rate = tuple(flux_rate)
        self.lift = tuple(q/v for q, v in zip(flux, g.volumes))
        self.lift_rate = tuple((qt-b*vt)/v for qt, b, vt, v in
                               zip(flux_rate, self.lift, g.volume_rates, g.volumes))
        linear, linear_rate = [z]*(2*n), [z]*(2*n)
        self.constant = self.constant_rate = z
        for row, owner in enumerate(g.active):
            b, bt = self.lift[row], self.lift_rate[row]
            gram, rate = g.forms[owner]['gram'], g.forms[owner]['gram_rate']
            d, dt = g.divergence[row], g.divergence_rate[row]
            for col in range(2*n):
                j = (d[col], int(col == 2*row), int(col == 2*row+1))
                linear[col] += b*sum((j[k]*gram[k][0] for k in range(3)), z)
                linear_rate[col] += bt*sum((j[k]*gram[k][0] for k in range(3)), z)
                linear_rate[col] += b*(dt[col]*gram[0][0]
                                      +sum((j[k]*rate[k][0] for k in range(3)), z))
            self.constant += gram[0][0]*b*b/2
            self.constant_rate += rate[0][0]*b*b/2+gram[0][0]*b*bt
        self.linear, self.linear_rate = tuple(linear), tuple(linear_rate)

    def vector(self, velocity):
        rows = tuple(tuple(row) for row in velocity)
        if len(rows) != len(self.geometry.active) or any(len(row) != 2 for row in rows):
            raise ValueError('Two components per active original owner required')
        return tuple(self.zero+x for row in rows for x in row)

    def evaluate(self, velocity, velocity_rate=None):
        g, z = self.geometry, self.zero
        v = self.vector(velocity)
        vt = (z,)*len(v) if velocity_rate is None else self.vector(velocity_rate)
        action = lambda matrix: tuple(sum((a*b for a, b in zip(row, v)), z) for row in matrix)
        kv, ktv = action(g.kinetic), action(g.kinetic_rate)
        gradient = tuple(a+b for a, b in zip(kv, self.linear))
        energy = sum((x*k/2+x*l for x, k, l in zip(v, kv, self.linear)), z)+self.constant
        geometry_work = sum((x*k/2+x*l for x, k, l in zip(v, ktv, self.linear_rate)), z)+self.constant_rate
        velocity_work = sum((a*b for a, b in zip(gradient, vt)), z)
        # Independent direct local-jet evaluation, including the boundary lift.
        local_energy, trace_gradient = z, []
        for row, owner in enumerate(g.active):
            jet = (sum((a*b for a, b in zip(g.divergence[row], v)), z)+self.lift[row],
                   v[2*row], v[2*row+1])
            gram = g.forms[owner]['gram']
            gj = tuple(sum((a*b for a, b in zip(gr, jet)), z) for gr in gram)
            local_energy += sum((a*b for a, b in zip(jet, gj)), z)/2
            trace_gradient.append(gj[0]/g.volumes[row])
        if energy != local_energy or energy < 0:
            raise ValueError('Prescribed-trace kinetic functional does not match original local Gram forms')
        return dict(kinetic_energy=energy, velocity_gradient=tuple(zip(gradient[::2], gradient[1::2])),
                    explicit_geometry_time_work=geometry_work, velocity_time_work=velocity_work,
                    kinetic_time_work=geometry_work+velocity_work,
                    boundary_mass_flux_gradient=tuple(trace_gradient[f['row']] for f in self.boundary_faces),
                    prescribed_trace_only=True,
                    natural_open_pressure_or_coupled_force_or_gameplay_accepted=False)
