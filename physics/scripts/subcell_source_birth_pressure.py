"""Point-birth asymptotic of the ORIGINAL two-pole pressure energy.

Single newborn source, fixed old V/P, and bounded newborn physical velocity.
This derives a pressure-metric boundary limit, NOT a conservative mass/force
update. In particular it is not permission to start Gauss time stepping on
zero mass or to erase the singular source-front terms.
"""
from fractions import Fraction as F
import numpy as np

from subcell_source_activation import faces
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_frames import face_section
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate


class SourceBirthPressure:
    def __init__(self, partition):
        self.partition = partition
        self.original_state = self.state_signature()
        self.occupied = {(p['parent'], int(s)) for p in partition.pools for s in p['source_triangle_indices']}
        momentum = np.array([p['momentum'] for p in partition.pools])[:, None, :]
        self.primal = evaluate(partition, momentum)
        if self.primal['positive_energy_contraction_error'] > 1e-10:
            raise ValueError('Original positive-energy contraction gate failed')
        self.poles = []
        gram = np.array([p['form']['gram'] for p in partition.pools])
        for pole in self.primal['poles']:
            system = WetPoolPressureSystem(partition, pole['beta'])
            w = pole['normalized_auxiliary_velocity'][:, 0]/system.root[:, None]
            jet = np.column_stack((system.divergence(w), w))
            stress = np.einsum('ni,ni->n', gram[:, 0], jet)
            self.poles.append((pole, stress))

    def state_signature(self):
        return tuple((p['parent'], tuple(p['source_triangle_indices']), p['volume'], tuple(p['momentum']))
                     for p in self.partition.pools)

    def point_limit(self, parent, source_id):
        part = self.partition
        if self.state_signature() != self.original_state:
            raise ValueError('Birth pressure context requires its unchanged original state')
        if not isinstance(parent, (int, np.integer)) or not 0 <= parent < len(part.patch.cells):
            raise ValueError('Original receiving parent required')
        if not isinstance(source_id, (int, np.integer)):
            raise ValueError('Original integer source ID required')
        if (parent, source_id) in self.occupied:
            raise ValueError('Birth source must be unowned at the original state')
        birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source_id]))
        if birth.volume_power != 3:
            raise ValueError('Point-birth asymptotic requires cubic source storage; edge/flat limits differ')
        coefficient = float(birth.volume_coefficient)
        if not np.isfinite(coefficient) or coefficient <= 0:
            raise ValueError('Positive birth coefficient exceeds represented pressure range')
        root_coefficient = np.sqrt(coefficient)
        # h*D_new = dself.u_new + sum d_old.u_old at leading order.
        # Old normalized rows gain sqrt(h)*k_i.q_new. Only those old rows
        # contribute to the leading sqrt(h) cross block of Q.
        dself = np.zeros(2)
        old_columns = np.zeros((len(part.pools), 2))
        connected = 0
        for face in faces(part):
            left_target = face['left_parent'] == parent and face['left_source'] == source_id
            right_target = face['right_parent'] == parent and face['right_source'] == source_id
            if left_target == right_target:
                continue
            wall = min(face['left_parent'], face['right_parent']) < 0
            owner = face['right'] if left_target else face['left']
            if not wall:
                if owner is None:
                    continue  # No fabricated wall or auxiliary on other dry support.
                form = part.pools[owner]['form']
                if F(form['datum'])+F(float(form['stage_offset'])) <= birth.datum:
                    continue
            section = face_section(face['segment'])
            scaled_area = float(birth.scaled_face_divergence_limit(section))
            direction = (1 if right_target else -1)*scaled_area*face['normal']
            dself += direction
            if not wall and scaled_area != 0:
                # Harmonic area = 2*newborn area + higher-order terms when
                # the old side has strictly positive depth at the birth point.
                old_columns[owner] += direction*root_coefficient/part.pools[owner]['volume']
                connected += 1
        mapping = np.vstack((dself, np.eye(2)))
        qdd = mapping.T@np.asarray(birth.scaled_gram_limit, float)@mapping
        if not np.isfinite(qdd).all() or not np.isfinite(old_columns).all():
            raise ValueError('Original birth pressure coefficients exceed represented range')
        results = []
        for pole, stress in self.poles:
            alpha, beta = pole['alpha'], pole['beta']
            coupling = old_columns.T@stress
            matrix = np.eye(2)+beta*qdd
            cholesky = np.linalg.cholesky(matrix)
            solution = np.linalg.solve(cholesky.T, np.linalg.solve(cholesky, coupling))
            energy_slope = -.5*alpha*beta*float(coupling@solution)
            if not np.isfinite(energy_slope) or not np.isfinite(solution/root_coefficient).all():
                raise ValueError('Point-birth pressure work exceeds represented range')
            results.append(dict(beta=beta, alpha=alpha, old_pressure_residual=pole['relative_residual'],
                energy_height_slope=energy_slope,
                auxiliary_velocity_height_product_limit=-beta*solution/root_coefficient))
        slope = sum(p['energy_height_slope'] for p in results)
        return dict(parent=int(parent), source_id=int(source_id), volume_leading_power=3,
            volume_leading_coefficient=coefficient, leading_newborn_normalized_gram=qdd,
            old_divergence_column_sqrt_height_coefficient=old_columns,
            immediately_connected_old_faces=connected, poles=results,
            fixed_old_state_energy_height_slope=slope,
            fixed_old_state_energy_volume_derivative_is_singular=slope != 0,
            full_metric_front_force_or_time_or_gameplay_accepted=False)
