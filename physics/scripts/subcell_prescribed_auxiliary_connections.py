"""Auxiliary skew connections with explicit prescribed-pressure flux ports.

The variables are owner velocities and one outward mass flux per exterior
face. The jet divergence is D*u+C*q, C[row,face]=1/V[row]. Time connections
differentiate D and C at FIXED coordinates, not a prescribed q(t) trajectory.
The latter's q_t work belongs to the energy derivative, not this connection.

This extends the reflecting shared-face/spatial/time connections, NOT their
advective exterior closure. Boundary flux-coordinate work is not automatically
the physical advective/pressure energy flux. No coupled PDE or time step is
provided or enabled in gameplay.
"""
from subcell_front_prescribed_trace import FrontPrescribedTrace
from subcell_front_profile_transport import FrontProfileTransport


class PrescribedAuxiliaryConnections:
    def __init__(self, fan, fragments, time, *, boundary):
        fragments = tuple(fragments)
        self.trace = FrontPrescribedTrace(fan, fragments, time, boundary=boundary)
        self.profile = FrontProfileTransport(fan, fragments, time, outer_boundary='reflecting')
        self.geometry = g = self.trace.geometry
        self.zero = g.zero
        self.velocity_size = nv = 2*len(g.active)
        self.fluxes = tuple(f['outward_mass_flux'] for f in self.trace.boundary_faces)
        self.divergence = tuple(tuple(g.divergence[i]) + tuple(
            1/g.volumes[i] if f['row'] == i else self.zero
            for f in self.trace.boundary_faces) for i in range(len(g.active)))
        self.divergence_rate = tuple(tuple(g.divergence_rate[i]) + tuple(
            -g.volume_rates[i]/(g.volumes[i]*g.volumes[i]) if f['row'] == i else self.zero
            for f in self.trace.boundary_faces) for i in range(len(g.active)))
        self.size = nv+len(self.fluxes)

    def state(self, velocity, boundary_flux=None):
        u = self.profile.vector(velocity)
        try:
            q = self.fluxes if boundary_flux is None else tuple(self.zero+x for x in boundary_flux)
            if len(q) != len(self.fluxes):
                raise ValueError
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('One finite flux coordinate per active exterior face required') from exc
        return u+q

    def _flat(self, value, size):
        try:
            value = tuple(self.zero+x for x in value)
            if len(value) != size:
                raise ValueError
            return value
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Complete finite augmented coordinate vector required') from exc

    def apply_divergence(self, state, *, rate=False):
        state = self._flat(state,self.size)
        matrix = self.divergence_rate if rate else self.divergence
        return tuple(sum((a*b for a,b in zip(row,state)),self.zero) for row in matrix)

    def transpose(self, scalar, *, rate=False):
        scalar = self._flat(scalar,len(self.geometry.active))
        matrix = self.divergence_rate if rate else self.divergence
        return tuple(sum((row[j]*s for row,s in zip(matrix,scalar)),self.zero)
                     for j in range(self.size))

    def result(self, state, action):
        state,action = self._flat(state,self.size),self._flat(action,self.size)
        nv = self.velocity_size
        interior = sum((a*b for a,b in zip(state[:nv],action[:nv])),self.zero)
        port = sum((a*b for a,b in zip(state[nv:],action[nv:])),self.zero)
        if interior+port != 0:
            raise ValueError('Augmented connection is not work neutral')
        return dict(velocity_action=self.profile.pairs(action[:nv]),
                    boundary_flux_action=tuple(action[nv:]), interior_work=interior,
                    flux_coordinate_work=port, augmented_action=tuple(action),
                    advective_exterior_closure_or_coupled_pde_or_gameplay_accepted=False)

    def volume_connection(self, velocity, boundary_flux=None):
        state = self.state(velocity,boundary_flux)
        d = self.apply_divergence(state)
        k = self.profile.connection
        scalar = [sum((k[i][j]*state[2*i+j] for j in range(2)),self.zero)
                  for i in range(len(d))]
        action = [-x for x in self.transpose(scalar)]
        for i in range(len(d)):
            for j in range(2):
                action[2*i+j] += k[i][j]*d[i]
        return self.result(state,action)

    def factor_connection(self, velocity, boundary_flux=None):
        state = self.state(velocity,boundary_flux)
        d = self.apply_divergence(state)
        jets = [(d[i],state[2*i],state[2*i+1]) for i in range(len(d))]
        stress = [[self.zero]*3 for _ in jets]
        for face in self.profile.faces:
            l,r,matrix = face['left'],face['right'],face['matrix']
            for i in range(3):
                stress[l][i] += sum((matrix[i][j]*jets[r][j]/2 for j in range(3)),self.zero)
                stress[r][i] -= sum((matrix[j][i]*jets[l][j]/2 for j in range(3)),self.zero)
        action = list(self.transpose([s[0] for s in stress]))
        for i in range(len(d)):
            for j in range(2):
                action[2*i+j] += stress[i][j+1]
        connection = self.volume_connection(velocity,boundary_flux)['augmented_action']
        return self.result(state,[a+b for a,b in zip(action,connection)])

    def time_connection(self, velocity, boundary_flux=None):
        state = self.state(velocity,boundary_flux)
        d,dt = self.apply_divergence(state),self.apply_divergence(state,rate=True)
        first,second = [],[]
        local = [self.zero]*self.size
        for i,owner in enumerate(self.geometry.active):
            form = self.geometry.forms[owner]
            a,c,ct = form['gram'][0][0],form['gram'][0][1:],form['gram_rate'][0][1:]
            cu = sum((c[j]*state[2*i+j] for j in range(2)),self.zero)
            ctu = sum((ct[j]*state[2*i+j] for j in range(2)),self.zero)
            first.append(a*dt[i]/2-ctu/4)
            second.append(-(a*d[i]+cu)/2)
            for j in range(2):
                local[2*i+j] += c[j]*dt[i]/2+ct[j]*d[i]/4
        x,y = self.transpose(first),self.transpose(second,rate=True)
        return self.result(state,[a+b+c for a,b,c in zip(local,x,y)])
