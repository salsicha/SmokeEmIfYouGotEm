"""Velocity-resolved transport on ONE original affine shallow-water fan.

Face factors and conservative shallow-water receipts use the same continuous
depth/velocity trace, not a product of independently averaged owner quantities.
This is NOT the coupled dispersive mass/momentum law or an interacting-fan
solver. The auxiliary pressure operator still has reflecting outer boundaries;
the separate shallow-water ledger explicitly includes prescribed fan traces at
the exterior. They must not be added together as a qualified open-boundary PDE.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _clip, _integrate, _line_integral
from subcell_front_auxiliary_transport import FrontAuxiliaryTransport


def face_advection_moments(fan, first, last, time):
    """Signed integrals of h**k * (u.n) ds, k=1..3, on the actual fan.

    Include the full directed normal measure. Reversal negates every moment;
    subdivision adds them without another edge-length or parameter weight.
    """
    # Independent existing mass/momentum flux also validates time and XYZ bed.
    reference = fan.face_flux(first, last, time)
    a, b = tuple(map(F, first)), tuple(map(F, last))
    head, front, linear, velocity, wet = fan._profile(time)
    qa, qb = fan._coordinate(a), fan._coordinate(b)
    cuts = [fan.zero, fan.zero+1]
    if qa != qb:
        for bound in (head, front):
            s = (bound-qa)/(qb-qa)
            if 0 < s < 1:
                cuts.append(s)
    point = lambda s: tuple(x+s*(y-x) for x, y in zip(a, b))
    normal = (b[1]-a[1], a[0]-b[0])
    moments = [fan.zero]*3
    cuts = sorted(cuts)
    for lo, hi in zip(cuts, cuts[1:]):
        q = fan._coordinate(point((lo+hi)/2))
        if q >= front:
            continue
        varying = q > head
        c = F(1, 9)/(fan.gravity*fan.norm2) if varying else fan.depth
        speed = velocity if varying else tuple((lambda p, v=v: fan.zero+v) for v in wet)
        un = lambda p: sum((n*v(p) for n, v in zip(normal, speed)), fan.zero)
        for k in range(1, 4):
            forms = [linear]*(2*k) if varying else []
            moments[k-1] += (hi-lo)*c**k*_line_integral(
                (point(lo), point(hi)), forms+[un], fan.zero)
    if moments[0] != reference['volume_rate']:
        raise ValueError('Profile factor and conservative mass traces disagree')
    return tuple(moments)


def profile_depth_advection(fan, fragment, time):
    """Volume integral h*(u.grad(h)), before any owner-velocity averaging."""
    fan.integrate(fragment, time)  # Validate original convex polygon and bed.
    t = F(time)
    head, front, linear, velocity, _ = fan._profile(t)
    varying = _clip(_clip(fragment.polygon, lambda p: fan._coordinate(p)-head, True),
                    lambda p: fan._coordinate(p)-front, False)
    un = lambda p: sum((n*v(p) for n, v in zip(fan.normal, velocity)), fan.zero)
    integral = sum((_integrate((varying[0], varying[i], varying[i+1]),
                              [linear]*3+[un], fan.zero)
                    for i in range(1, len(varying)-1)), fan.zero)
    c = F(1, 9)/(fan.gravity*fan.norm2)
    return -2*c*c*integral/t


class FrontProfileTransport(FrontAuxiliaryTransport):
    """Use the original varying velocity in every auxiliary transport factor.

    The inherited force/commutator machinery retains its original exact source
    geometry and dry-owner semantics. No accepted runtime default is changed.
    """
    def __init__(self, fan, fragments, time, *, outer_boundary, energy_datum=0):
        fragments = tuple(fragments)
        self.energy_datum = F(energy_datum)
        budgets = tuple(fan.integrate(f, time) for f in fragments)
        means = tuple(tuple(p/v['volume'] for p in v['momentum'])
                      for v in budgets if v['volume'] > 0)
        super().__init__(fan, fragments, time, means, outer_boundary=outer_boundary)
        # Means remain useful as probe velocities, never as transport traces.
        self.owner_mean_velocity = means
        self.transport_velocity = None
        self.profile_depth_advection = tuple(profile_depth_advection(fan, fragments[i], time)
                                             for i in self.geometry.active)
        self.connection = tuple(tuple(-F(3, 4)*s*m for s in fan.gradient)
                                for m in self.profile_depth_advection)
        x, y = fan.gradient
        for face in self.faces:
            m1, m2, m3 = face_advection_moments(fan, face['first'], face['last'], time)
            face['advection_moments'] = (m1, m2, m3)
            face['mass_flux'] = m1
            face['matrix'] = ((m3, -F(3, 2)*x*m2, -F(3, 2)*y*m2),
                              (-F(3, 2)*x*m2, 3*x*x*m1, 3*x*y*m1),
                              (-F(3, 2)*y*m2, 3*x*y*m1, 3*y*y*m1))
        # One receipt per original shared face; opposite owners debit/credit
        # the SAME flux. Exterior flux is retained explicitly, not zeroed to
        # manufacture conservation of an open fan subdomain.
        self.profile_faces = tuple(dict(owners=f['owners'], first=f['first'], last=f['last'],
            **fan.face_flux(f['first'], f['last'], time, energy_datum=self.energy_datum))
            for f in self.geometry.faces)
        self.bed_force = tuple(b['bed_force'] for b in budgets)

    def shallow_water_rates(self):
        """Conservative mass/momentum RHS of the prescribed nondispersive fan.

        All original owners are retained here, including exact-zero dry owners.
        These are separate from the reflecting auxiliary force operators.
        """
        mass = [self.zero for _ in self.bed_force]
        momentum = [list(row) for row in self.bed_force]
        energy = [self.zero for _ in self.bed_force]
        for face in self.profile_faces:
            for side, owner in enumerate(face['owners']):
                sign = -1 if side == 0 else 1
                mass[owner] += sign*face['volume_rate']
                energy[owner] += sign*face['energy_rate_per_density']
                for axis in range(2):
                    momentum[owner][axis] += sign*face['momentum_rate'][axis]
        if tuple(mass[i] for i in self.geometry.active) != self.geometry.volume_rates:
            raise ValueError('Conservative fan mass flux differs from analytic support evolution')
        return dict(volume_rate=tuple(mass), momentum_rate=tuple(map(tuple, momentum)),
                    energy_rate_per_density=tuple(energy), bed_force=self.bed_force,
                    energy_datum=self.energy_datum,
                    exterior_faces=tuple(f for f in self.profile_faces if len(f['owners']) == 1),
                    prescribed_shallow_water_trace_only=True,
                    coupled_dispersive_or_open_pressure_or_gameplay_accepted=False)

    def scope(self):
        return dict(**super().scope(), actual_profile_velocity_transport=True,
                    reflecting_auxiliary_boundary=True,
                    separate_prescribed_shallow_water_exterior_trace=True)
