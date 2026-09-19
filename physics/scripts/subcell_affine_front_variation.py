"""Exact primitive energy derivatives with prescribed exterior velocity.

Retains the original two poles and both momentum coordinates. This supplies
energy derivatives, NOT the conservative transport bracket, front activation,
natural open-pressure law or a playable nonlinear time step.
"""
from fractions import Fraction as F


class AffineFrontPressureVariation:
    def __init__(self, trace, metric, physical_momentum, *, solved_state=None):
        g, m, z = trace.geometry, metric, metric.zero
        n = len(g.active)
        if (tuple(m.mass) != tuple(v for v in g.volumes for _ in range(2))
                or m.kinetic != tuple(map(tuple, g.kinetic))
                or m.linear != trace.linear or m.boundary_constant != trace.constant):
            raise ValueError('Matching original source geometry and prescribed trace required')
        self.trace, self.geometry, self.metric = trace, g, m
        p = m.vector(physical_momentum)
        if solved_state is None:
            v = m.solve_physical.solve(tuple(x-q for x, q in zip(p, m.offset)))
            auxiliaries = None
        else:
            v = m.vector(solved_state['canonical_velocity'])
            states = solved_state['poles']
            if len(states) != len(m.poles) or any(m.number(s['length']) != pole['length']
                    or m.number(s['weight']) != pole['weight'] for s, pole in zip(states, m.poles)):
                raise ValueError('Both original pressure poles in original order required')
            auxiliaries = tuple(m.vector(s['auxiliary_velocity']) for s in states)
        # Physical E_p=v. At fixed canonical m=Mv, E_m=Bv/M=(p-q)/M;
        # it is NOT the physical layer velocity p/M when q is nonzero.
        bv = m.action(m.physical, v)
        self.momentum_gradients = dict(physical=m.pairs(v),
            canonical=m.pairs(tuple(x/mass for x, mass in zip(bv, m.mass))))
        mass = dict(physical=[-m.constant*x*x/2 for x in v],
                    canonical=[m.constant*x*x/2-y*x/mi for x, y, mi in zip(v, bv, m.mass)])
        grams = {key: [[[z]*3 for _ in range(3)] for _ in range(n)] for key in mass}
        divergence = {key: [[z]*(2*n) for _ in range(n)] for key in mass}
        lift = {key: [z]*n for key in mass}
        reconstructed = [m.constant*mi*x for mi, x in zip(m.mass, v)]
        for index, pole in enumerate(m.poles):
            w, lam = pole['weight'], pole['length']
            rhs = tuple(mi*x-lam*l for mi, x, l in zip(m.mass, v, m.linear))
            a = pole['solver'].solve(rhs) if auxiliaries is None else auxiliaries[index]
            if m.action(pole['matrix'], a) != rhs:
                raise ValueError('Prescribed original pressure pole residual is nonzero')
            s = pole['boundary_shift']
            if m.action(pole['matrix'], s) != tuple(-lam*l for l in m.linear):
                raise ValueError('Prescribed original boundary shift equation failed')
            a0 = tuple(x-y for x, y in zip(a, s))
            for i in range(2*n):
                reconstructed[i] += w*m.mass[i]*a[i]
                mass['physical'][i] -= w*(v[i]*a[i]-a[i]*a[i]/2)
                mass['canonical'][i] += w*(v[i]*a0[i]-a0[i]*a0[i]/2+s[i]*s[i]/2)
            for row, owner in enumerate(g.active):
                gram = g.forms[owner]['gram']
                jet = lambda u, b: (m.dot(g.divergence[row], u)+b, u[2*row], u[2*row+1])
                ja, js, j0 = jet(a, trace.lift[row]), jet(s, trace.lift[row]), jet(a0, z)
                ga, gs, g0 = (m.dot(gram[0], j) for j in (ja, js, j0))
                lift['physical'][row] += w*lam*ga
                lift['canonical'][row] += w*lam*gs
                for i in range(2*n):
                    divergence['physical'][row][i] += w*lam*ga*a[i]
                    divergence['canonical'][row][i] += w*lam*(gs*s[i]-g0*a0[i])
                for i in range(3):
                    for j in range(3):
                        grams['physical'][row][i][j] += w*lam*ja[i]*ja[j]/2
                        grams['canonical'][row][i][j] += w*lam*(js[i]*js[j]-j0[i]*j0[j])/2
        if tuple(reconstructed) != p or tuple(x+y for x, y in zip(bv, m.offset)) != p:
            raise ValueError('Original affine momentum reconstruction failed')
        self.gradients = {}
        positions = {owner: row for row, owner in enumerate(g.active)}
        for key in mass:
            dg, bg, gg = divergence[key], lift[key], grams[key]
            # Both D and b have the SAME owner's evolving volume denominator.
            volumes = tuple(mass[key][2*i]+mass[key][2*i+1]
                            -(m.dot(dg[i], g.divergence[i])+bg[i]*trace.lift[i])/g.volumes[i]
                            for i in range(n))
            faces = []
            for face in g.faces:
                owners = face['owners']
                if any(owner not in positions for owner in owners):
                    if any(x != 0 for x in (*face['column_normal'], *face['column_normal_rate'])):
                        raise ValueError('Dry owner cannot carry a pressure column')
                    faces.append(None)
                    continue
                first, count = positions[owners[0]], len(owners)
                if count not in (1, 2):
                    raise ValueError('One or two original face owners required')
                gradient = []
                for axis in range(2):
                    value = z
                    for owner in owners:
                        row = positions[owner]
                        term = -dg[row][2*first+axis]
                        if count == 2:
                            term += dg[row][2*positions[owners[1]]+axis]
                        value += term/(count*g.volumes[row])
                    gradient.append(value)
                faces.append(tuple(gradient))
            moments, slopes = [], []
            for row, owner in enumerate(g.active):
                gram, (x, y) = gg[row], g.fragments[owner].gradient
                _, h1, h2, _ = g.forms[owner]['depth_moments']
                moments.append((volumes[row]+3*(x*x*gram[1][1]+2*x*y*gram[1][2]+y*y*gram[2][2]),
                                -3*(x*gram[0][1]+y*gram[0][2]), gram[0][0]))
                slopes.append((-3*h2*gram[0][1]+6*h1*(x*gram[1][1]+y*gram[1][2]),
                               -3*h2*gram[0][2]+6*h1*(x*gram[1][2]+y*gram[2][2])))
            self.gradients[key] = dict(momentum=self.momentum_gradients[key],
                moments=tuple(moments), slopes=tuple(slopes), columns=tuple(faces),
                boundary_flux=tuple(bg[f['row']]/g.volumes[f['row']] for f in trace.boundary_faces))

    def work(self, momentum_direction, moment_direction, face_column_direction, bed_gradient_direction,
             boundary_flux_direction, *, momentum_coordinate='physical'):
        if momentum_coordinate not in self.gradients:
            raise ValueError('Explicit physical or canonical momentum coordinate required')
        grad, m = self.gradients[momentum_coordinate], self.metric
        terms = {}
        for key, values, width in (('momentum', momentum_direction, 2), ('moments', moment_direction, 3),
                                   ('slopes', bed_gradient_direction, 2), ('columns', face_column_direction, 2)):
            values = tuple(tuple(m.number(x) for x in row) for row in values)
            if len(values) != len(grad[key]) or any(len(row) != width for row in values):
                raise ValueError('Matching original primitive directions required')
            value = m.zero
            for derivative, direction in zip(grad[key], values):
                if derivative is None:
                    if any(x != 0 for x in direction):
                        raise ValueError('Dry topology creation requires a coupled front law')
                else:
                    value += m.dot(derivative, direction)
            terms[key] = value
        flux = tuple(m.number(x) for x in boundary_flux_direction)
        if len(flux) != len(grad['boundary_flux']):
            raise ValueError('One flux direction per active original exterior face required')
        terms['boundary_flux'] = m.dot(grad['boundary_flux'], flux)
        return dict(momentum_work=terms['momentum'], depth_moment_work=terms['moments'],
                    bed_gradient_work=terms['slopes'], face_column_work=terms['columns'],
                    boundary_flux_work=terms['boundary_flux'], energy_direction=sum(terms.values(), m.zero),
                    momentum_coordinate=momentum_coordinate,
                    nonlinear_force_or_topology_change_or_gameplay_accepted=False)

    def time_work(self, momentum_rate, *, momentum_coordinate='physical'):
        g = self.geometry
        return self.work(momentum_rate, [g.forms[i]['depth_moment_rates'] for i in g.active],
                         [f['column_normal_rate'] for f in g.faces], [(F(0), F(0)) for _ in g.active],
                         [f['outward_mass_flux_rate'] for f in self.trace.boundary_faces],
                         momentum_coordinate=momentum_coordinate)
