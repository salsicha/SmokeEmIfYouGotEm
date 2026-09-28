"""Conservative mass/pressure pairing on frozen original fan geometry.

The pressure-jet divergence is NOT the conservative volume-flux operator.
Here each shared face transports its actual depth column times the mean
LAYER velocity, plus the explicit original subcell-profile lift. Exterior
flux coordinates retain their signs. The original two-pole physical map and
its exact transpose then pair this mass map with a potential covector.

The lift is prescribed data, not a hidden momentum repair. Its power and
the complete flux-coordinate power remain explicit. This is not an evolving
subcell reconstruction, full nonlinear pressure/bed force, boundary law or
time step, and does not enable anything in gameplay.
"""
from subcell_prescribed_physical_transport import PrescribedPhysicalTransport


class PrescribedMassPressurePair:
    def __init__(self, fan, fragments, time, *, boundary):
        fragments = tuple(fragments)
        self.physical = PrescribedPhysicalTransport(fan, fragments, time, boundary=boundary)
        self.connections = c = self.physical.connections
        self.metric, self.zero = self.physical.metric, c.zero
        g, z = c.geometry, self.zero
        self.owner_count = len(fragments)
        positions = {owner: row for row, owner in enumerate(g.active)}
        budgets = tuple(fan.integrate(f, time) for f in fragments)
        self.original_momentum = tuple(budgets[i]['momentum'] for i in g.active)
        original = self.metric.vector(self.original_momentum)
        self.mass_map = [[z]*c.velocity_size for _ in g.active]
        self.profile_outflow = [z]*len(g.active)
        self.shared_faces = []
        for face in g.faces:
            if len(face['owners']) != 2:
                continue
            exact = fan.face_flux(face['first'], face['last'], time)['volume_rate']
            if face['parameter_depth_integral'] == 0:
                if exact != 0:
                    raise ValueError('Dry shared column carries original mass')
                continue
            left, right = (positions[i] for i in face['owners'])
            row = [z]*c.velocity_size
            for owner in (left, right):
                for axis in range(2):
                    row[2*owner+axis] = face['column_normal'][axis]/(2*g.volumes[owner])
            mean_flux = self.dot(row, original)
            lift = exact-mean_flux
            for j, coefficient in enumerate(row):
                self.mass_map[left][j] += coefficient
                self.mass_map[right][j] -= coefficient
            self.profile_outflow[left] += lift
            self.profile_outflow[right] -= lift
            self.shared_faces.append(dict(face, rows=(left, right), momentum_row=tuple(row),
                                          original_flux=exact, profile_lift=lift))
        self.mass_map = tuple(map(tuple, self.mass_map))
        self.profile_outflow = tuple(self.profile_outflow)
        if any(sum((row[j] for row in self.mass_map), z) != 0 for j in range(c.velocity_size)):
            raise ValueError('Shared conservative mass columns do not cancel')
        original_rates = self.mass_rates(self.original_momentum)
        if original_rates['active_volume_rate'] != g.volume_rates:
            raise ValueError('Original profile mass trace was not reproduced')

    def dot(self, a, b):
        if len(a) != len(b):
            raise ValueError('Matching work coordinates required')
        return sum((x*y for x, y in zip(a, b)), self.zero)

    def physical_momentum(self, canonical_velocity, boundary_flux=None):
        """Original physical map, including its arbitrary prescribed-flux lift."""
        c, m = self.connections, self.metric
        state = c.state(canonical_velocity, boundary_flux)
        result = [m.constant*mass*v for mass, v in zip(m.mass, state[:c.velocity_size])]
        for pole in m.poles:
            auxiliary = self.physical.auxiliary_state(state, pole)
            result = [p+pole['weight']*mass*a for p, mass, a in zip(result, m.mass, auxiliary)]
        return m.pairs(result)

    def mass_rates(self, physical_momentum, boundary_flux=None):
        c, m, z = self.connections, self.metric, self.zero
        p = m.vector(physical_momentum)
        q = c.state(m.pairs((z,)*c.velocity_size), boundary_flux)[c.velocity_size:]
        outflow = [self.dot(row, p)+lift for row, lift in zip(self.mass_map, self.profile_outflow)]
        for face, flux in zip(c.trace.boundary_faces, q):
            outflow[face['row']] += flux
        active = tuple(-x for x in outflow)
        rates = [z]*self.owner_count
        for owner, rate in zip(c.geometry.active, active):
            rates[owner] = rate
        if sum(rates, z)+sum(q, z) != 0:
            raise ValueError('Local shared fluxes lost global signed mass balance')
        return dict(volume_rate=tuple(rates), active_volume_rate=active,
                    exterior_mass_flux=q, total_outward_mass_flux=sum(q, z),
                    shared_fluxes=tuple(self.dot(f['momentum_row'], p)+f['profile_lift']
                                        for f in self.shared_faces),
                    prescribed_profile_lift=self.profile_outflow)

    def apply(self, potential_covector, canonical_velocity, boundary_flux=None):
        """Direct face transpose and ORIGINAL pressure pullback, not residual fitting.

        potential_covector is supplied, not invented from averaged fan depth.
        A complete model must still derive its gravity AND kinetic shape terms.
        """
        c, m, z = self.connections, self.metric, self.zero
        phi = c._flat(potential_covector, len(c.geometry.active))
        state = c.state(canonical_velocity, boundary_flux)
        nv = c.velocity_size
        p = self.physical_momentum(canonical_velocity, state[nv:])
        rates = self.mass_rates(p, state[nv:])
        gradient = tuple(sum((row[j]*a for row, a in zip(self.mass_map, phi)), z)
                         for j in range(nv))
        action = [m.constant*mass*a for mass, a in zip(m.mass, gradient)]+[z]*len(c.fluxes)
        for pole in m.poles:
            # P_j maps (v,q) to (a_j,q). Differentiate w_j*M*a_j directly.
            auxiliary_action = tuple(pole['weight']*mass*a for mass, a in zip(m.mass, gradient))+(z,)*len(c.fluxes)
            pulled = self.physical.pullback(auxiliary_action, pole)
            action = [a+b for a, b in zip(action, pulled)]
        for i, face in enumerate(c.trace.boundary_faces):
            action[nv+i] += phi[face['row']]
        pressure_work = self.dot(state[:nv], action[:nv])
        flux_work = self.dot(state[nv:], action[nv:])
        profile_work = self.dot(phi, self.profile_outflow)
        potential_rate = self.dot(phi, rates['active_volume_rate'])
        if potential_rate+pressure_work+flux_work+profile_work != 0:
            raise ValueError('Direct mass-pressure adjoint work failed')
        return dict(mass=rates, physical_momentum=p,
                    physical_momentum_rhs_contribution=m.pairs(action[:nv]),
                    boundary_flux_action=tuple(action[nv:]), augmented_action=tuple(action),
                    potential_covector_rate=potential_rate, pressure_work=pressure_work,
                    prescribed_flux_coordinate_work=flux_work,
                    prescribed_profile_lift_work=profile_work,
                    full_nonlinear_or_total_energy_or_boundary_or_gameplay_accepted=False)
