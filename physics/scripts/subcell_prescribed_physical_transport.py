"""Pull the original two-pole auxiliary transport back to physical work.

At fixed original geometry, y=(canonical velocity, prescribed face flux).
P_j*y=(a_j,q), (M+lambda_j*C)*a_j=M*v-lambda_j*l(q).
The directly assembled action is c*L_mass*y plus
sum_j weight_j*P_j.T*(L_mass+lambda_j*L_factor)*P_j*y.
Its self-work is the signed transport of the existing positive kinetic
energy, including explicit flux-coordinate work. No force is fitted from an
energy residual. This is one frozen-geometry transport contribution, NOT the
complete mass/momentum, pressure/bed-work, boundary or time integration law.
"""
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_prescribed_auxiliary_advection import PrescribedAuxiliaryAdvection


class PrescribedPhysicalTransport:
    def __init__(self, fan, fragments, time, *, boundary):
        self.transport = PrescribedAuxiliaryAdvection(fan, fragments, time, boundary=boundary)
        self.connections = self.transport.connections
        self.metric = AffineMovingPressureMetric.from_trace(self.connections.trace)
        self.zero = self.connections.zero

    def _factor_gradient(self, state):
        """J_aug.T G J_aug, assembled from original owner jets and Gram forms."""
        c, z = self.connections, self.zero
        state = c._flat(state, c.size)
        divergence = c.apply_divergence(state)
        stresses = []
        for i, owner in enumerate(c.geometry.active):
            jet = (divergence[i], state[2*i], state[2*i+1])
            stresses.append(tuple(sum((a*b for a, b in zip(row, jet)), z)
                                  for row in c.geometry.forms[owner]['gram']))
        result = list(c.transpose(tuple(s[0] for s in stresses)))
        for i, stress in enumerate(stresses):
            for k in range(2):
                result[2*i+k] += stress[k+1]
        return tuple(result)

    def auxiliary_state(self, state, pole):
        c, m, z = self.connections, self.metric, self.zero
        state = c._flat(state, c.size)
        lift = self._factor_gradient((z,)*c.velocity_size+state[c.velocity_size:])
        rhs = tuple(mass*v-pole['length']*g for mass, v, g in
                    zip(m.mass, state[:c.velocity_size], lift[:c.velocity_size]))
        return pole['solver'].solve(rhs)+state[c.velocity_size:]

    def pullback(self, action, pole):
        """P_j.T via an exact symmetric solve, retaining its exterior adjoint."""
        c, m = self.connections, self.metric
        action = c._flat(action, c.size)
        r = pole['solver'].solve(action[:c.velocity_size])
        exterior = self._factor_gradient(r+(self.zero,)*len(c.fluxes))[c.velocity_size:]
        return tuple(mass*x for mass, x in zip(m.mass, r))+tuple(
            a-pole['length']*b for a, b in zip(action[c.velocity_size:], exterior))

    def apply(self, canonical_velocity, boundary_flux=None):
        c, m, z, t = self.connections, self.metric, self.zero, self.transport
        state = c.state(canonical_velocity, boundary_flux)
        nv = c.velocity_size
        base = t.apply(canonical_velocity, state[nv:], channel='difference')
        action = [m.constant*x for x in base['augmented_action']]
        face_flux = [m.constant*f['outward_auxiliary_energy_flux'] for f in base['faces']]
        kinetic = m.constant*sum((mass*v*v/2 for mass, v in zip(m.mass, state[:nv])), z)
        poles = []
        for pole in m.poles:
            auxiliary = self.auxiliary_state(state, pole)
            velocity, flux = c.profile.pairs(auxiliary[:nv]), auxiliary[nv:]
            mass = t.apply(velocity, flux, channel='difference')
            factor = t.apply(velocity, flux, channel='factor')
            w, length = pole['weight'], pole['length']
            combined = tuple(w*(a+length*b) for a, b in
                             zip(mass['augmented_action'], factor['augmented_action']))
            pulled = self.pullback(combined, pole)
            action = [a+b for a, b in zip(action, pulled)]
            pole_flux = tuple(w*(a['outward_auxiliary_energy_flux']+length*b['outward_auxiliary_energy_flux'])
                              for a, b in zip(mass['faces'], factor['faces']))
            face_flux = [a+b for a, b in zip(face_flux, pole_flux)]
            gradient = self._factor_gradient(auxiliary)
            kinetic += w*(sum((mass*a*a/2 for mass, a in zip(m.mass, auxiliary[:nv])), z)
                          +length*sum((a*b/2 for a, b in zip(auxiliary, gradient)), z))
            poles.append(dict(length=length, weight=w, auxiliary_state=auxiliary,
                              auxiliary_action=combined, pulled_action=pulled,
                              outward_kinetic_flux=sum(pole_flux, z)))
        interior = sum((a*b for a, b in zip(state[:nv], action[:nv])), z)
        port = sum((a*b for a, b in zip(state[nv:], action[nv:])), z)
        outward = sum(face_flux, z)
        if interior+port != outward or kinetic < 0:
            raise ValueError('Direct physical transport violates weighted kinetic work')
        return dict(augmented_action=tuple(action), canonical_velocity=canonical_velocity,
                    physical_momentum_rhs_contribution=c.profile.pairs(tuple(-x for x in action[:nv])),
                    boundary_flux_action=tuple(action[nv:]),
                    interior_work=interior, flux_coordinate_work=port,
                    outward_kinetic_flux=outward, kinetic_energy=kinetic,
                    faces=tuple(dict(owner=f['owner'], first=f['first'], last=f['last'],
                                     outward_kinetic_flux=value) for f, value in zip(base['faces'], face_flux)),
                    poles=tuple(poles), spatial_operator_rhs_sign=-1,
                    full_momentum_or_total_energy_or_inflow_or_gameplay_accepted=False)

    def prescribed_kinetic_ledger(self, canonical_velocity):
        """Differentiate E(p,t) along this contribution on the original fan.

        q(t), volume(t) and the Gram metric follow the existing prescribed
        trace. Their full explicit time work is kept, not canceled by an
        invented force. This is NOT a total-energy or full-PDE ledger.
        """
        result = self.apply(canonical_velocity)
        m = self.metric
        physical_momentum = m.physical_momentum(canonical_velocity)
        rate = m.evaluate(physical_momentum, result['physical_momentum_rhs_contribution'])
        if rate['kinetic_energy'] != result['kinetic_energy']:
            raise ValueError('Weighted transport and physical energy disagree')
        remaining = rate['geometry_time_work']+result['flux_coordinate_work']
        if rate['kinetic_energy_rate']+result['outward_kinetic_flux'] != remaining:
            raise ValueError('Prescribed kinetic transport chain rule failed')
        return dict(transport=result, physical_momentum=physical_momentum,
                    kinetic_energy_rate=rate['kinetic_energy_rate'],
                    explicit_geometry_time_work=rate['geometry_time_work'],
                    prescribed_flux_coordinate_work=result['flux_coordinate_work'],
                    remaining_geometry_and_port_power=remaining,
                    full_momentum_or_total_energy_or_inflow_or_gameplay_accepted=False)
