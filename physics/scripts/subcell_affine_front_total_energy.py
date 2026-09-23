"""Total front energy with the original prescribed-boundary pressure lift.

Adds gravity to AffineFrontPressureVariation, not to the reflecting metric.
The exterior-flux work and both momentum coordinates remain explicit. This
does not supply the conservative bracket, interacting fronts or a time step.
"""
from fractions import Fraction as F

from subcell_affine_front_variation import AffineFrontPressureVariation


def affine_front_potential(geometry, energy_datum=0):
    """Gravity and its primitive derivatives, without constructing a pressure metric."""
    g, datum = geometry, F(energy_datum)
    energy = g.zero
    moments, spatial, slopes, heights = [], [], [], []
    for owner in g.active:
        form, fragment = g.forms[owner], g.fragments[owner]
        gravity, bed = F(form['gravity']), F(form['bed_at_origin'])
        origin = tuple(map(F, form['spatial_origin']))
        if gravity <= 0 or len(origin) != 2 or any(
            p[2] != bed+sum(s*(x-o) for s, x, o in zip(fragment.gradient, p, origin))
            for p in fragment.polygon
        ):
            raise ValueError('Positive gravity and matching original affine bed required')
        h1, h2, _ = form['depth_moments'][1:]
        xh = form['depth_spatial_moments']
        moments.append((gravity*(bed-datum), gravity/2, g.zero))
        spatial.append(tuple(gravity*s for s in fragment.gradient))
        slopes.append(tuple(gravity*x for x in xh))
        heights.append(gravity*h1)
        energy += gravity*((bed-datum)*h1+h2/2+sum(s*x for s, x in zip(fragment.gradient, xh)))
    return dict(energy=energy, gradients=dict(moments=tuple(moments), spatial=tuple(spatial),
                                             slopes=tuple(slopes), bed=tuple(heights)))


class AffineFrontTotalEnergyVariation:
    def __init__(self, trace, metric, physical_momentum, *, energy_datum=0, solved_state=None):
        self.pressure = pressure = AffineFrontPressureVariation(
            trace, metric, physical_momentum, solved_state=solved_state)
        self.trace, self.geometry, self.metric = trace, trace.geometry, metric
        self.energy_datum = F(energy_datum)
        m = metric
        potential = affine_front_potential(self.geometry, self.energy_datum)
        self.potential_energy, self.potential_gradients = potential['energy'], potential['gradients']
        # E is not p.v/2: p=Bv+q and the prescribed boundary has a constant.
        v = m.vector(pressure.momentum_gradients['physical'])
        self.kinetic_energy = m.dot(v, m.action(m.physical, v))/2-m.dual_constant
        self.total_energy = self.kinetic_energy+self.potential_energy
        self.gradients = {}
        for coordinate, original in pressure.gradients.items():
            grad = dict(original)
            for key in ('moments', 'slopes'):
                grad[key] = tuple(tuple(a+b for a, b in zip(row, extra))
                                  for row, extra in zip(original[key], self.potential_gradients[key]))
            grad.update(spatial=self.potential_gradients['spatial'], bed=self.potential_gradients['bed'])
            self.gradients[coordinate] = grad

    def work(self, momentum_direction, moment_direction, face_column_direction, bed_gradient_direction,
             boundary_flux_direction, spatial_moment_direction, bed_height_direction,
             *, momentum_coordinate='physical'):
        m, n = self.metric, len(self.geometry.active)
        moments = tuple(tuple(m.number(x) for x in row) for row in moment_direction)
        slopes = tuple(tuple(m.number(x) for x in row) for row in bed_gradient_direction)
        spatial = tuple(tuple(m.number(x) for x in row) for row in spatial_moment_direction)
        heights = tuple(m.number(x) for x in bed_height_direction)
        if len(spatial) != n or any(len(row) != 2 for row in spatial) or len(heights) != n:
            raise ValueError('Spatial moments and bed-height direction per active original source required')
        kinetic = self.pressure.work(momentum_direction, moments, face_column_direction, slopes,
                                     boundary_flux_direction, momentum_coordinate=momentum_coordinate)
        dot = lambda key, rows: sum((m.dot(a, b) for a, b in zip(self.potential_gradients[key], rows)), m.zero)
        potential = dict(depth_moment_work=dot('moments', moments), bed_gradient_work=dot('slopes', slopes),
                         spatial_moment_work=dot('spatial', spatial),
                         bed_height_work=m.dot(self.potential_gradients['bed'], heights))
        total_potential = sum(potential.values(), m.zero)
        result = dict(kinetic)
        for key, value in potential.items():
            result[key] = result.get(key, m.zero)+value
        result.update(kinetic_energy_direction=kinetic['energy_direction'],
                      potential_energy_direction=total_potential,
                      energy_direction=kinetic['energy_direction']+total_potential,
                      conservative_force_or_open_boundary_or_gameplay_accepted=False)
        return result

    def time_work(self, momentum_rate, *, momentum_coordinate='physical'):
        g = self.geometry
        return self.work(momentum_rate, [g.forms[i]['depth_moment_rates'] for i in g.active],
                         [f['column_normal_rate'] for f in g.faces], [(0, 0) for _ in g.active],
                         [f['outward_mass_flux_rate'] for f in self.trace.boundary_faces],
                         [g.forms[i]['depth_spatial_moment_rates'] for i in g.active], [0 for _ in g.active],
                         momentum_coordinate=momentum_coordinate)
