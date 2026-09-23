"""Continuity-derived depth/spatial moment transport on an original affine fan.

For k=1..3, (h^k)_t + div(h^k u) = -(k-1) h^k div(u).
For q=x-origin, (q h)_t + div(q h u) = h u.
Higher depth moments are NOT conserved densities. These common-face receipts
retain the volume compression and spatial source, including exterior fluxes.
This is a prescribed shallow-water profile, not a dispersive force/time step,
interacting-front closure, native implementation or gameplay acceptance.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _clip, _integrate, _line_integral
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_front_profile_transport import face_advection_moments


def face_spatial_advection(fan, first, last, time):
    """Directed integrals of (x-origin)*h*u.n, with the original depth profile."""
    fan.face_flux(first, last, time)  # Original XYZ/time validation.
    a, b = tuple(map(F, first)), tuple(map(F, last))
    head, front, linear, velocity, wet = fan._profile(time)
    qa, qb = fan._coordinate(a), fan._coordinate(b)
    cuts = [fan.zero, fan.zero+1]
    if qa != qb:
        cuts += [s for bound in (head, front) if 0 < (s := (bound-qa)/(qb-qa)) < 1]
    point = lambda s: tuple(x+s*(y-x) for x, y in zip(a, b))
    normal = b[1]-a[1], a[0]-b[0]
    result = [fan.zero, fan.zero]
    cuts = sorted(cuts)
    for lo, hi in zip(cuts, cuts[1:]):
        q = fan._coordinate(point((lo+hi)/2))
        if q >= front:
            continue
        varying = q > head
        coefficient = F(1, 9)/(fan.gravity*fan.norm2) if varying else fan.depth
        forms = [linear, linear] if varying else []
        speed = velocity if varying else tuple((lambda p, v=v: fan.zero+v) for v in wet)
        un = lambda p: sum((n*u(p) for n, u in zip(normal, speed)), fan.zero)
        for axis in range(2):
            coordinate = lambda p, axis=axis: p[axis]-fan.origin[axis]
            result[axis] += (hi-lo)*coefficient*_line_integral(
                (point(lo), point(hi)), forms+[un, coordinate], fan.zero)
    return tuple(result)


def volume_compression(fan, fragment, time):
    """Integrals h^k div(u), k=1..3; no time-difference or residual construction."""
    fan.integrate(fragment, time)  # Validate the original convex affine polygon.
    t = F(time)
    head, front, linear, _, _ = fan._profile(t)
    varying = _clip(_clip(fragment.polygon, lambda p: fan._coordinate(p)-head, True),
                    lambda p: fan._coordinate(p)-front, False)
    # Direct spatial derivative of the original velocity: grad(u)=2 N N^T/(3t |N|^2).
    # The wet branch has constant velocity and contributes zero divergence.
    divergence = F(2, 3)/t
    coefficient = F(1, 9)/(fan.gravity*fan.norm2)
    return tuple(divergence*coefficient**k*sum(
        (_integrate((varying[0], varying[i], varying[i+1]), [linear]*(2*k), fan.zero)
         for i in range(1, len(varying)-1)), fan.zero) for k in (1, 2, 3))


class FrontMomentTransport:
    def __init__(self, fan, fragments, time):
        self.fan, self.time = fan, F(time)
        # Use only this geometry's conforming face ownership and analytic moment
        # checks. Its homogeneous pressure boundary is NOT an advective wall.
        self.geometry = g = FrontPressureGeometry(fan, fragments, time, outer_boundary='reflecting')
        self.zero = fan.zero
        self.faces = tuple(dict(owners=face['owners'], first=face['first'], last=face['last'],
                                moments=face_advection_moments(fan, face['first'], face['last'], time),
                                spatial=face_spatial_advection(fan, face['first'], face['last'], time))
                           for face in g.faces)
        self.compression = tuple(volume_compression(fan, f, time) for f in g.fragments)
        self.spatial_source = tuple(fan.integrate(f, time)['momentum'] for f in g.fragments)

    def rates(self):
        """One flux per common face; both owners use opposite exact contributions."""
        g = self.geometry
        moments = [[-k*x for k, x in enumerate(row)] for row in self.compression]
        spatial = [list(row) for row in self.spatial_source]
        for face in self.faces:
            for side, owner in enumerate(face['owners']):
                sign = -1 if side == 0 else 1
                for k in range(3):
                    moments[owner][k] += sign*face['moments'][k]
                for axis in range(2):
                    spatial[owner][axis] += sign*face['spatial'][axis]
        moments, spatial = tuple(map(tuple, moments)), tuple(map(tuple, spatial))
        if (moments != tuple(f['depth_moment_rates'] for f in g.forms)
                or spatial != tuple(f['depth_spatial_moment_rates'] for f in g.forms)):
            raise ValueError('Continuity transport disagrees with original analytic moment rates')
        return dict(moments=moments, spatial=spatial,
                    moment_compression_sources=tuple(tuple(-k*x for k, x in enumerate(row))
                                                     for row in self.compression),
                    spatial_sources=self.spatial_source,
                    exterior_faces=tuple(f for f in self.faces if len(f['owners']) == 1),
                    dispersive_force_or_interacting_fronts_or_gameplay_accepted=False)

    def potential_balance(self, energy_datum=0):
        """Explicit potential-energy advection, compression work and bed work.

        dG/dt = -boundary[g*(h^2/2+(bed-datum)*h)*u.n]
                 - integral(g*h^2*div(u)/2) + integral(g*h*u.grad(bed)).
        This is a gravitational exchange ledger, NOT the total-energy flux.
        """
        fan, g, datum = self.fan, self.geometry, F(energy_datum)
        rates = self.rates()
        pressure = tuple(-fan.gravity*row[1]/2 for row in self.compression)
        bed = tuple(fan.gravity*sum(s*p for s, p in zip(fan.gradient, row)) for row in self.spatial_source)
        boundary = [self.zero for _ in g.fragments]
        faces = []
        for face in self.faces:
            flux = fan.gravity*((fan.bed-datum)*face['moments'][0]+face['moments'][1]/2
                                 +sum(s*x for s, x in zip(fan.gradient, face['spatial'])))
            faces.append(dict(owners=face['owners'], first=face['first'], last=face['last'], potential_flux=flux))
            for side, owner in enumerate(face['owners']):
                boundary[owner] += (-1 if side == 0 else 1)*flux
        rate = tuple(a+b+c for a, b, c in zip(boundary, pressure, bed))
        chain = tuple(fan.gravity*((fan.bed-datum)*m[0]+m[1]/2+sum(s*x for s, x in zip(fan.gradient, q)))
                      for m, q in zip(rates['moments'], rates['spatial']))
        if rate != chain:
            raise ValueError('Original gravitational exchange disagrees with primitive work')
        return dict(potential_rate=rate, boundary_advection=tuple(boundary),
                    compression_work=pressure, bed_work=bed, faces=tuple(faces),
                    exterior_potential_flux=sum((f['potential_flux'] for f in faces if len(f['owners']) == 1), self.zero),
                    energy_datum=datum, total_energy_flux_or_dispersive_force_or_gameplay_accepted=False)
