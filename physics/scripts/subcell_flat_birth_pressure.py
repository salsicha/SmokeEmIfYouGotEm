"""One flat-source pressure/work limit of the ORIGINAL two-pole energy.

V=A*e+O(e^2), fixed old physical V/P, bounded new physical velocity v.
Unlike a point birth, old self-divergence changes at order e and v contributes
to the leading energy. Unlike an edge birth, there is no finite energy jump.
Only original face polynomials and existing old pressure solves are used here;
no epsilon water, finite-difference force or dry inverse mass is constructed.
This is a boundary derivative, not a front force, flux or time update.
"""
from fractions import Fraction as F
import math
import numpy as np

from rational_primal_energy import K0
from subcell_source_activation import faces
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_frames import face_section


def flat_limit(context, parent, source_id, newborn_velocity=(0., 0.)):
    part = context.partition
    if context.state_signature() != context.original_state:
        raise ValueError('Birth pressure context requires its unchanged original state')
    if not isinstance(parent, (int, np.integer)) or not 0 <= parent < len(part.patch.cells):
        raise ValueError('Original receiving parent required')
    if not isinstance(source_id, (int, np.integer)):
        raise ValueError('Original integer source ID required')
    if (parent, source_id) in context.occupied:
        raise ValueError('Birth source must be unowned at the original state')
    velocity = np.asarray(newborn_velocity, float)
    if velocity.shape != (2,) or not np.isfinite(velocity).all():
        raise ValueError('Finite bounded two-component newborn velocity required')
    birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source_id]))
    if birth.volume_power != 1:
        raise ValueError('Linear original flat storage required; point/edge limits differ')
    area = float(birth.volume_coefficient)
    if not np.isfinite(area) or area <= 0:
        raise ValueError('Positive flat area exceeds represented range')
    root = np.sqrt(area)
    old_columns = np.zeros((len(part.pools), 2))
    old_self = np.zeros_like(old_columns)
    connected = 0
    for face in faces(part):
        left = (face['left_parent'], face['left_source']) == (parent, source_id)
        right = (face['right_parent'], face['right_source']) == (parent, source_id)
        # A flat newborn's own wall/velocity factors vanish too quickly to
        # contribute to the height slope. Existing old walls do not change.
        if left == right or min(face['left_parent'], face['right_parent']) < 0:
            continue
        owner = face['right'] if left else face['left']
        if owner is None:
            continue  # Other dry support is not a reflecting wall.
        form = part.pools[owner]['form']
        if F(form['datum'])+F(float(form['stage_offset'])) <= birth.datum:
            continue
        width = float(birth.face_area_polynomial(face_section(face['segment'])).get(1, F(0)))
        if width == 0:
            continue
        direction = (1 if right else -1)*width*face['normal']/part.pools[owner]['volume']
        # Harmonic area = 2*width*e + O(e^2). The old row gains
        # sqrt(e)*old_columns.q_new and e*old_self.u_old simultaneously.
        old_columns[owner] += direction/root
        old_self[owner] -= direction
        connected += 1
    if not np.isfinite(old_columns).all() or not np.isfinite(old_self).all():
        raise ValueError('Original flat pressure coefficients exceed represented range')
    volume = np.array([p['volume'] for p in part.pools])
    r = root*velocity
    base_slope = .5*K0*area*float(velocity@velocity)
    canonical = K0*velocity.copy()
    fixed_p_gradient = -.5*K0*float(velocity@velocity)
    poles = []
    for pole, stress in context.poles:
        alpha, beta = pole['alpha'], pole['beta']
        z = pole['normalized_auxiliary_velocity'][:, 0]
        old_velocity = z/np.sqrt(volume)[:, None]
        coupling = old_columns.T@stress  # B.T z, Q_on = sqrt(e)*B + o(sqrt(e)).
        self_work = float(stress@np.einsum('ni,ni->n', old_self, old_velocity))
        # Q_oo = Q_old + e*Q1; .5*z.T*Q1*z = self_work.
        # New principal Q has zero limit. The Schur contribution is therefore
        # -.5*beta*|B.T*z|^2, not the nonzero point-birth 2x2 inverse.
        geometric_work = self_work-.5*beta*float(coupling@coupling)
        slope = alpha*(float(r@coupling)+geometric_work)
        canonical += alpha*coupling/root
        fixed_p_gradient += alpha*geometric_work/area
        poles.append(dict(alpha=alpha, beta=beta, old_pressure_residual=pole['relative_residual'],
            energy_height_slope=slope, old_self_geometry_work=self_work,
            old_new_coupling=coupling, auxiliary_velocity_limit=velocity-beta*coupling/root))
    slope = math.fsum([base_slope]+[p['energy_height_slope'] for p in poles])
    work_error = abs(slope-area*(fixed_p_gradient+float(canonical@velocity)))
    if not np.isfinite([slope, fixed_p_gradient, work_error]).all() or not np.isfinite(canonical).all():
        raise ValueError('Original flat pressure work exceeds represented range')
    if work_error > 1e-10:
        raise ValueError('Original flat pressure chain-rule work identity gate failed')
    return dict(parent=int(parent), source_id=int(source_id), volume_leading_power=1,
        volume_leading_coefficient=area, newborn_velocity=velocity.copy(),
        old_divergence_column_sqrt_height_coefficient=old_columns,
        old_self_divergence_height_derivative=old_self,
        immediately_connected_old_faces=connected, poles=poles,
        fixed_old_bounded_new_velocity_energy_jump=0.,
        fixed_old_state_energy_height_slope=slope,
        canonical_velocity_limit=canonical, kinetic_fixed_momentum_volume_gradient_limit=fixed_p_gradient,
        chain_rule_work_identity_error=work_error,
        full_metric_front_force_or_time_or_gameplay_accepted=False)
