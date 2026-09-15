"""One original EDGE-birth pressure limit, not a wetting force or time update.

V=c*e^2 makes the old/new normalized pressure coupling order one. Its old-row
contribution to the newborn diagonal must therefore be retained, together with
the response of ALL old unknowns. The point-birth 2x2 limit is not applicable.
No positive water is inserted to construct this boundary operator.
"""
from fractions import Fraction as F
import math
import numpy as np

from pressure_cg_range_reference import solve as range_cg
from rational_primal_energy import K0
from subcell_exact_geometry import area
from subcell_source_activation import faces
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_frames import face_section
from subcell_wet_pool_pressure import WetPoolPressureSystem


def edge_factor(birth):
    """Original leading triangle squares; point triangles have higher order."""
    if birth.volume_power != 2:
        raise ValueError('Quadratic original edge storage required')
    rows = []
    for fragment in birth.fragments:
        bx, by = map(float, fragment.gradient)
        for triangle in fragment.triangles:
            a, b, c = sorted(v[2]-birth.datum for v in triangle)
            if a > 0 or b > 0:
                continue
            if c <= 0:
                raise ValueError('Flat triangle is not an edge birth')
            root = np.sqrt(float(area(triangle)/(c*birth.volume_coefficient)))
            rows.extend(root*np.array([[np.sqrt(.5), -bx/np.sqrt(.5), -by/np.sqrt(.5)],
                                      [0., bx, by]]))
    return np.asarray(rows)


class EdgeBirthSystem:
    """Original positive factors augmented by one limiting normalized source."""
    def __init__(self, old, old_columns, newborn_factor):
        self.old, self.beta = old, old.length
        self.columns = [pool['form']['factor'][:, :1]*column[None, :]
                        for pool, column in zip(old.partition.pools, old_columns)]
        self.newborn_factor = newborn_factor
        # Only the range-CG vector shape is required here. Unit weights are
        # coordinates of this limiting operator, NOT actual newborn water.
        self.h = np.ones((len(old.h)+1, 1))
        block = np.eye(2)+self.beta*newborn_factor.T@newborn_factor
        for column in self.columns:
            block += self.beta*column.T@column
        self.cholesky = np.linalg.cholesky(block)

    def vector(self, value):
        value = np.asarray(value, float)
        if value.shape != (*self.h.shape, 2) or not np.isfinite(value).all():
            raise ValueError('Finite normalized edge-limit vector required')
        return value

    def factor_action(self, value):
        value = self.vector(value)
        result = [v+column@value[-1, 0] for v, column
                  in zip(self.old.factor_action(value[:-1]), self.columns)]
        return result+[self.newborn_factor@value[-1, 0]]

    def factor_transpose(self, factors):
        old = self.old.factor_transpose(factors[:-1])
        new = self.newborn_factor.T@factors[-1]
        for column, value in zip(self.columns, factors[:-1]):
            new += column.T@value
        return np.concatenate((old, new[None, None, :]))

    def q_action(self, value):
        return self.factor_transpose(self.factor_action(value))

    def apply(self, value):
        value = self.vector(value)
        return value+self.beta*self.q_action(value)

    def precondition(self, residual, scheme):
        if scheme != 'source-block':
            raise ValueError('Original old-source blocks and one newborn block required')
        residual = self.vector(residual)
        old = self.old.precondition(residual[:-1], 'source-block')
        new = np.linalg.solve(self.cholesky.T, np.linalg.solve(self.cholesky, residual[-1, 0]))
        return np.concatenate((old, new[None, None, :]))


def edge_limit(context, parent, source_id):
    part = context.partition
    if context.state_signature() != context.original_state:
        raise ValueError('Birth pressure context requires its unchanged original state')
    if not isinstance(parent, (int, np.integer)) or not 0 <= parent < len(part.patch.cells):
        raise ValueError('Original receiving parent required')
    if not isinstance(source_id, (int, np.integer)):
        raise ValueError('Original integer source ID required')
    if (parent, source_id) in context.occupied:
        raise ValueError('Birth source must be unowned at the original state')
    birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source_id]))
    factor = edge_factor(birth)
    coefficient = float(birth.volume_coefficient)
    if not np.isfinite(coefficient) or coefficient <= 0:
        raise ValueError('Positive edge coefficient exceeds represented range')
    root = np.sqrt(coefficient)
    dself = np.zeros(2)
    old_columns = np.zeros((len(part.pools), 2))
    connected = 0
    for face in faces(part):
        left = (face['left_parent'], face['left_source']) == (parent, source_id)
        right = (face['right_parent'], face['right_source']) == (parent, source_id)
        if left == right:
            continue
        wall = min(face['left_parent'], face['right_parent']) < 0
        owner = face['right'] if left else face['left']
        if not wall:
            if owner is None:
                continue
            form = part.pools[owner]['form']
            if F(form['datum'])+F(float(form['stage_offset'])) <= birth.datum:
                continue
        scaled_area = float(birth.scaled_face_divergence_limit(face_section(face['segment'])))
        direction = (1 if right else -1)*scaled_area*face['normal']
        dself += direction
        if not wall and scaled_area != 0:
            old_columns[owner] += direction*root/part.pools[owner]['volume']
            connected += 1
    newborn_factor = factor@np.vstack((dself, np.eye(2)))
    momentum = np.array([p['momentum'] for p in part.pools])[:, None, :]
    volume = np.array([p['volume'] for p in part.pools])
    q = np.concatenate((momentum/np.sqrt(volume)[:, None, None], np.zeros((1, 1, 2))))
    kinetic = .5*K0*float(np.sum(q*q))
    mapped = K0*q
    poles = []
    for original, stress in context.poles:
        alpha, beta = original['alpha'], original['beta']
        system = EdgeBirthSystem(WetPoolPressureSystem(part, beta), old_columns, newborn_factor)
        solution, stats = range_cg(system, q, 40, preconditioner='source-block')
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original 40-CG edge pressure residual gate failed')
        qz = system.q_action(solution)
        factors = system.factor_action(solution)
        kinetic += .5*alpha*(math.fsum(float(v@v) for v in factors)+beta*float(np.sum(qz*qz)))
        mapped += alpha*qz
        # Schur work identity avoids subtracting two nearly equal energies.
        jump = .5*alpha*float((old_columns.T@stress)@solution[-1, 0])
        poles.append(dict(alpha=alpha, beta=beta, normalized_auxiliary_limit=solution,
            energy_jump=jump, auxiliary_velocity_height_product_limit=solution[-1, 0]/root,
            iterations=stats['iterations'], relative_residual=stats['relative_residual']))
    contraction_error = abs(kinetic-.5*float(np.sum(q*mapped)))
    jump = math.fsum(p['energy_jump'] for p in poles)
    jump_identity_error = abs((kinetic-context.primal['kinetic'])-jump)
    if not np.isfinite([kinetic, jump, contraction_error, jump_identity_error]).all():
        raise ValueError('Original edge pressure exceeds represented range')
    if max(contraction_error, jump_identity_error) > 1e-10:
        raise ValueError('Original edge pressure contraction or Schur identity gate failed')
    return dict(parent=int(parent), source_id=int(source_id), volume_leading_power=2,
        volume_leading_coefficient=coefficient, old_divergence_column_limit=old_columns,
        newborn_factor=newborn_factor, immediately_connected_old_faces=connected, poles=poles,
        fixed_old_bounded_new_velocity_energy_jump=jump, limiting_kinetic_energy=kinetic,
        positive_energy_contraction_error=contraction_error, schur_energy_jump_identity_error=jump_identity_error,
        has_nonzero_old_pressure_coupling=bool(np.any(old_columns != 0)),
        full_metric_front_force_or_time_or_gameplay_accepted=False)
