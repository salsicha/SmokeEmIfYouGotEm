"""Signed exterior work for the prescribed-fan auxiliary transport split.

L = S + E^T B E/2, where S is the existing skew connection and B integrates
the ORIGINAL velocity-resolved outward trace. Thus v.L(u)+u.L(v)=v.E^T B E.u.
This is a spatial operator convention: a transport RHS uses -L, not +L.

The factor and difference channels are separate, unscaled auxiliary forms.
They are NOT a full momentum law, an inflow/radiation boundary condition or a
time step. In particular, signed inflow work is not dissipative. No gameplay
solver, pressure pole, depth profile or acceptance threshold is changed.
"""
from fractions import Fraction as F

from subcell_front_profile_transport import face_advection_moments
from subcell_prescribed_auxiliary_connections import PrescribedAuxiliaryConnections


class PrescribedAuxiliaryAdvection:
    def __init__(self, fan, fragments, time, *, boundary):
        self.connections = op = PrescribedAuxiliaryConnections(
            fan, fragments, time, boundary=boundary)
        self.zero = op.zero
        x, y = fan.gradient
        faces = []
        for face in op.trace.boundary_faces:
            m1, m2, m3 = face_advection_moments(
                fan, face['first'], face['last'], time)
            if m1 != face['outward_mass_flux']:
                raise ValueError('Exterior transport and prescribed pressure trace disagree')
            faces.append(dict(face, advection_moments=(m1, m2, m3),
                matrix=((m3, -F(3, 2)*x*m2, -F(3, 2)*y*m2),
                        (-F(3, 2)*x*m2, 3*x*x*m1, 3*x*y*m1),
                        (-F(3, 2)*y*m2, 3*x*y*m1, 3*y*y*m1))))
        self.faces = tuple(faces)

    def _channel(self, channel):
        if channel not in ('factor', 'difference'):
            raise ValueError('Explicit factor or difference auxiliary channel required')

    def exterior(self, velocity, boundary_flux=None, *, channel):
        """Assemble E^T B E/2 directly, retaining every original exterior face.

        Factor density = h*((h*d-1.5*grad(b).u)^2+.75*(grad(b).u)^2)/2.
        Difference density = h*|u|^2/2. Their relative physical coefficients
        belong to the still-missing coupled pressure/momentum law.
        """
        self._channel(channel)
        op, z = self.connections, self.zero
        state = op.state(velocity, boundary_flux)
        d = op.apply_divergence(state)
        stress = [[z]*3 for _ in d]
        receipts = []
        for face in self.faces:
            row = face['row']
            jet = (d[row], state[2*row], state[2*row+1])
            if channel == 'factor':
                action = tuple(sum((a*b for a, b in zip(m, jet)), z)/2
                               for m in face['matrix'])
            else:
                flux = face['advection_moments'][0]
                action = (z, flux*jet[1]/2, flux*jet[2]/2)
            for j in range(3):
                stress[row][j] += action[j]
            receipts.append(dict(owner=face['owner'], row=row, first=face['first'],
                last=face['last'], jet=jet, jet_action=action,
                outward_auxiliary_energy_flux=sum((a*b for a, b in zip(jet, action)), z)))
        action = list(op.transpose([s[0] for s in stress]))
        for i, s in enumerate(stress):
            for j in range(2):
                action[2*i+j] += s[j+1]
        nv = op.velocity_size
        interior = sum((a*b for a, b in zip(state[:nv], action[:nv])), z)
        port = sum((a*b for a, b in zip(state[nv:], action[nv:])), z)
        outward = sum((f['outward_auxiliary_energy_flux'] for f in receipts), z)
        if interior+port != outward:
            raise ValueError('Direct exterior pullback differs from signed face work')
        return dict(augmented_action=tuple(action),
                    velocity_action=op.profile.pairs(action[:nv]),
                    boundary_flux_action=tuple(action[nv:]),
                    interior_work=interior, flux_coordinate_work=port,
                    outward_auxiliary_energy_flux=outward, faces=tuple(receipts))

    def apply(self, velocity, boundary_flux=None, *, channel):
        """Spatial split L; positive work is outward flux, not a positive RHS.

        Transport coefficients stay those of the given fan even for arbitrary
        probe coordinates. Changing a probe is NOT changing the advecting fan.
        """
        result = self.exterior(velocity, boundary_flux, channel=channel)
        op, z = self.connections, self.zero
        state = op.state(velocity, boundary_flux)
        if channel == 'factor':
            skew = op.factor_connection(velocity, boundary_flux)['augmented_action']
        else:
            skew = op.profile.vector(op.profile.difference_force(velocity)) + (z,)*len(op.fluxes)
        action = tuple(a+b for a, b in zip(skew, result['augmented_action']))
        nv = op.velocity_size
        interior = sum((a*b for a, b in zip(state[:nv], action[:nv])), z)
        port = sum((a*b for a, b in zip(state[nv:], action[nv:])), z)
        if interior+port != result['outward_auxiliary_energy_flux']:
            raise ValueError('Spatial split violates signed boundary work identity')
        return dict(result, augmented_action=action,
                    velocity_action=op.profile.pairs(action[:nv]),
                    boundary_flux_action=action[nv:], interior_work=interior,
                    flux_coordinate_work=port, channel=channel,
                    spatial_operator_rhs_sign=-1,
                    inflow_or_radiation_or_coupled_pde_or_gameplay_accepted=False)
