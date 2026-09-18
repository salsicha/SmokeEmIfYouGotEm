"""Original-profile auxiliary transport on a moving affine dry front.

This supplies the face exchange, spatial factor connection and physical-time
commutator for the SAME depth-weighted vertical kinetic form. It does not
assume a horizontal free surface: inside a fan grad(h) != -grad(b).
It is not a conservative mass/momentum closure or an interacting-fan solver.
No open boundary, finite step, pressure solve or native acceptance is implied.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _line_integral
from subcell_affine_front_pressure import FrontPressureGeometry, face_metric


class FrontForceLedger:
    """Direct paired exchanges and source/wall terms, never residual forces."""
    def __init__(self, count, zero):
        self.zero = zero
        self.faces = []
        self.bed = [[zero, zero] for _ in range(count)]
        self.wall = [[zero, zero] for _ in range(count)]

    def action(self):
        value = [[a+b for a, b in zip(bed, wall)] for bed, wall in zip(self.bed, self.wall)]
        for left, right, force in self.faces:
            for axis in range(2):
                value[left][axis] -= force[axis]
                value[right][axis] += force[axis]
        return tuple(map(tuple, value))


def face_depth_moments(fan, first, last, time):
    """Exact parameter integrals of h, h^2 and h^3 on the original XYZ edge.

    Head/front clipping and polynomial integration stay in the original
    quadratic field, including positive support below float export range.
    These are moments of the profile, not powers of a mean column depth.
    """
    reference = face_metric(fan, first, last, time)  # Validate original bed/edge.
    a, b, t = tuple(map(F, first)), tuple(map(F, last)), F(time)
    head, front, linear, _, _ = fan._profile(t)
    qa, qb = fan._coordinate(a), fan._coordinate(b)
    cuts = [fan.zero, fan.zero+1]
    if qa != qb:
        for bound in (head, front):
            value = (bound-qa)/(qb-qa)
            if 0 < value < 1:
                cuts.append(value)
    point = lambda s: tuple(x+(y-x)*s for x, y in zip(a, b))
    moments = [fan.zero]*3
    cuts = sorted(cuts)
    for lo, hi in zip(cuts, cuts[1:]):
        q = fan._coordinate(point((lo+hi)/2))
        if q >= front:
            continue
        variable = q > head
        coefficient = F(1, 9)/(fan.gravity*fan.norm2) if variable else fan.depth
        for k in range(1, 4):
            moments[k-1] += ((hi-lo)*coefficient**k*_line_integral(
                (point(lo), point(hi)), [linear]*(2*k) if variable else [], fan.zero))
    if moments[0] != reference['parameter_depth_integral'] or any(x < 0 for x in moments):
        raise ValueError('Original front face moments disagree with pressure support')
    return tuple(moments)


class FrontAuxiliaryTransport:
    """Exact graph operators paired with the original moving pressure geometry.

    Transport velocity has two components per ACTIVE owner. Outer faces are
    reflecting for advective exchange; they still enter the geometric identity
    integral(h grad(h)) = integral_boundary(h^2 n)/2. Omitting those faces would
    confuse a spatial derivative with a no-through-flow condition.
    """
    def __init__(self, fan, fragments, time, transport_velocity, *, outer_boundary):
        self.geometry = g = FrontPressureGeometry(fan, fragments, time, outer_boundary=outer_boundary)
        self.zero = g.zero
        self.transport_velocity = adv = self.vector(transport_velocity)
        self.positions = {owner: row for row, owner in enumerate(g.active)}
        self.faces = []
        gradient = [[g.zero, g.zero] for _ in g.active]
        for face in g.faces:
            owners, a, b = face['owners'], face['first'], face['last']
            moments = face_depth_moments(fan, a, b, time)
            normal = (b[1]-a[1], a[0]-b[0])
            for side, owner in enumerate(owners):
                if owner not in self.positions:
                    if any(x != 0 for x in moments):
                        raise ValueError('Positive front trace lacks an active original owner')
                    continue
                row = self.positions[owner]
                for axis in range(2):
                    gradient[row][axis] += (1 if side == 0 else -1)*normal[axis]*moments[1]/2
            if len(owners) == 1 or moments[0] == 0:
                continue
            left, right = (self.positions[owner] for owner in owners)
            speed = sum((normal[j]*(adv[2*left+j]+adv[2*right+j])/2 for j in range(2)), g.zero)
            m1, m2, m3 = moments
            x, y = fan.gradient
            matrix = ((m3, -F(3, 2)*x*m2, -F(3, 2)*y*m2),
                      (-F(3, 2)*x*m2, 3*x*x*m1, 3*x*y*m1),
                      (-F(3, 2)*y*m2, 3*x*y*m1, 3*y*y*m1))
            self.faces.append(dict(left=left, right=right, mass_flux=speed*m1,
                matrix=tuple(tuple(speed*v for v in row) for row in matrix),
                owners=owners, first=a, last=b, depth_moments=moments))
        self.depth_gradient_moments = tuple(map(tuple, gradient))
        # .5*h*(F_v adv(F_w)-adv(F_v) F_w), F=h*D-1.5*grad(b).u.
        # k=-.75*grad(b)*integral(h adv(h)). The hydrostatic specialization
        # +Gamma_vv*adv/4 is not valid for the quadratic front profile.
        self.connection = tuple(tuple(-F(3, 4)*s*sum(
            (adv[2*i+j]*gradient[i][j] for j in range(2)), g.zero)
            for s in fan.gradient) for i in range(len(g.active)))

    def vector(self, value):
        try:
            rows = tuple(tuple(row) for row in value)
            if len(rows) != len(self.geometry.active) or any(len(row) != 2 for row in rows):
                raise ValueError
            # Preserve algebraic values when chaining the pressure operators.
            return tuple(self.zero+x for row in rows for x in row)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Two finite components per active original owner required') from exc

    def pairs(self, value):
        return tuple(tuple(value[i:i+2]) for i in range(0, len(value), 2))

    def divergence(self, value, *, rate=False):
        matrix = self.geometry.divergence_rate if rate else self.geometry.divergence
        return tuple(sum((a*b for a, b in zip(row, value)), self.zero) for row in matrix)

    def transpose(self, value, *, rate=False):
        matrix = self.geometry.divergence_rate if rate else self.geometry.divergence
        return tuple(sum((matrix[i][j]*value[i] for i in range(len(matrix))), self.zero)
                     for j in range(2*len(matrix)))

    def _divergence_ledger(self, ledger, scalar, *, rate=False):
        g = self.geometry
        for face in g.faces:
            if any(owner not in self.positions for owner in face['owners']):
                if any(x != 0 for x in (*face['column_normal'], *face['column_normal_rate'])):
                    raise ValueError('Dry pressure owner carries an unsupported force column')
                continue
            rows = [self.positions[owner] for owner in face['owners']]
            force = []
            for axis in range(2):
                area, area_rate = face['column_normal'][axis], face['column_normal_rate'][axis]
                value = self.zero
                for row in rows:
                    volume, volume_rate = g.volumes[row], g.volume_rates[row]
                    coefficient = (area_rate-area*volume_rate/volume) if rate else area
                    value += scalar[row]*coefficient/(len(rows)*volume)
                force.append(value)
            if len(rows) == 2:
                ledger.faces.append((rows[0], rows[1], tuple(force)))
            else:
                for axis in range(2):
                    ledger.wall[rows[0]][axis] -= force[axis]

    def factor_force_ledger(self, velocity):
        """Direct source-factor stresses and actual-profile spatial connection."""
        u = self.vector(velocity)
        d = self.divergence(u)
        jets = [(d[i], u[2*i], u[2*i+1]) for i in range(len(d))]
        stress = [[self.zero]*3 for _ in jets]
        for face in self.faces:
            l, r, matrix = face['left'], face['right'], face['matrix']
            for i in range(3):
                stress[l][i] += sum((matrix[i][j]*jets[r][j]/2 for j in range(3)), self.zero)
                stress[r][i] -= sum((matrix[j][i]*jets[l][j]/2 for j in range(3)), self.zero)
        ledger = FrontForceLedger(len(d), self.zero)
        scalar = [stress[i][0]-sum((k[j]*u[2*i+j] for j in range(2)), self.zero)
                  for i, k in enumerate(self.connection)]
        self._divergence_ledger(ledger, scalar)
        for i, k in enumerate(self.connection):
            for j in range(2):
                ledger.bed[i][j] += stress[i][j+1]+k[j]*d[i]
        return ledger

    def time_commutator_ledger(self, velocity):
        """Both original divergence transpose paths, including their walls."""
        g = self.geometry
        u = self.vector(velocity)
        d, dt = self.divergence(u), self.divergence(u, rate=True)
        ledger = FrontForceLedger(len(d), self.zero)
        first, second = [], []
        for i, owner in enumerate(g.active):
            form = g.forms[owner]
            a, c, ct = form['gram'][0][0], form['gram'][0][1:], form['gram_rate'][0][1:]
            cu = sum((c[j]*u[2*i+j] for j in range(2)), self.zero)
            ctu = sum((ct[j]*u[2*i+j] for j in range(2)), self.zero)
            first.append(a*dt[i]/2-ctu/4)
            second.append(-(a*d[i]+cu)/2)
            for j in range(2):
                ledger.bed[i][j] += c[j]*dt[i]/2+ct[j]*d[i]/4
        self._divergence_ledger(ledger, first)
        self._divergence_ledger(ledger, second, rate=True)
        return ledger

    def volume_factor_force(self, velocity):
        u = self.vector(velocity)
        d = self.divergence(u)
        scalar = [sum((k[j]*u[2*i+j] for j in range(2)), self.zero)
                  for i, k in enumerate(self.connection)]
        dt = self.transpose(scalar)
        return self.pairs(tuple(k[j]*d[i]-dt[2*i+j]
            for i, k in enumerate(self.connection) for j in range(2)))

    def factor_force(self, velocity):
        u = self.vector(velocity)
        d = self.divergence(u)
        jets = [(d[i], u[2*i], u[2*i+1]) for i in range(len(d))]
        force = [[self.zero]*3 for _ in jets]
        for face in self.faces:
            l, r, matrix = face['left'], face['right'], face['matrix']
            for i in range(3):
                force[l][i] += sum((matrix[i][j]*jets[r][j]/2 for j in range(3)), self.zero)
                force[r][i] -= sum((matrix[j][i]*jets[l][j]/2 for j in range(3)), self.zero)
        transpose = self.transpose([row[0] for row in force])
        connection = self.vector(self.volume_factor_force(velocity))
        return self.pairs(tuple(transpose[2*i+j]+force[i][j+1]+connection[2*i+j]
                                for i in range(len(d)) for j in range(2)))

    def difference_force(self, velocity):
        u = self.vector(velocity)
        force = [self.zero]*len(u)
        for face in self.faces:
            l, r, flux = face['left'], face['right'], face['mass_flux']
            for j in range(2):
                force[2*l+j] += flux*u[2*r+j]/2
                force[2*r+j] -= flux*u[2*l+j]/2
        return self.pairs(force)

    def time_commutator(self, velocity):
        """Physical-time factor connection; includes D_t and profile h_t."""
        g = self.geometry
        u = self.vector(velocity)
        d, dt = self.divergence(u), self.divergence(u, rate=True)
        forms = [g.forms[i] for i in g.active]
        a = [f['gram'][0][0] for f in forms]
        c = [f['gram'][0][1:] for f in forms]
        ct = [f['gram_rate'][0][1:] for f in forms]
        cu = [sum((c[i][j]*u[2*i+j] for j in range(2)), self.zero) for i in range(len(d))]
        ctu = [sum((ct[i][j]*u[2*i+j] for j in range(2)), self.zero) for i in range(len(d))]
        first = self.transpose([a[i]*dt[i]/2-ctu[i]/4 for i in range(len(d))])
        second = self.transpose([-(a[i]*d[i]+cu[i])/2 for i in range(len(d))], rate=True)
        return self.pairs(tuple(first[2*i+j]+second[2*i+j]+c[i][j]*dt[i]/2+ct[i][j]*d[i]/4
                                for i in range(len(d)) for j in range(2)))

    def scope(self):
        return dict(active_original_owners=len(self.geometry.active), shared_wet_faces=len(self.faces),
                    actual_quadratic_depth_transport=True,
                    mass_or_momentum_closure_or_interacting_fans_or_native_or_gameplay_accepted=False)
