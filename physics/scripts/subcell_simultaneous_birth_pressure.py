"""Coupled POINT-birth limit of the original pressure metric, not time evolution.

Each exact original source rises by k_i*e above its own minimum. The positive
path parameter e is not physical time. New physical velocities remain bounded;
old V/P are held fixed. No epsilon state, dry inverse mass, or front force is
introduced. Distinct source minima do not gain fictitious immediate contact.
"""
from fractions import Fraction as F
import math
import numpy as np

from pressure_cg_range_reference import solve as range_cg
from subcell_source_activation import faces
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_exact_geometry import area as projected_area
from subcell_source_frames import face_section
from subcell_source_region_faces import internal_faces
from subcell_wet_pool_pressure import _harmonic_interval


def birth_faces(partition, keys):
    """Original Cartesian traces plus original edges with ownership labels only."""
    labels = {key: len(partition.pools)+i for i, key in enumerate(keys)}
    for face in faces(partition):
        if not face['internal']:
            yield face
    for face in internal_faces(partition, labels):
        yield dict(face, left_parent=face['parent'], right_parent=face['parent'], internal=True)


def harmonic_height_coefficient(section, datum, left_scale, right_scale):
    """lim A_harmonic/e^2 from original sloping face endpoints and logarithm.

    Rescaling the wetted bed coordinate gives width/span times the integral
    from zero to min(kL,kR); the original finite face is never extended in a
    positive-water calculation. A flat minimum edge contradicts point storage.
    """
    lo, hi = sorted((left_scale, right_scale))
    values = []
    for first, second in section.source_segments:
        a, b = sorted((first[1]-datum, second[1]-datum))
        if a < 0:
            raise ValueError('Original shared face lies below the birth minimum')
        if a > 0:
            continue
        if b == 0:
            raise ValueError('Flat minimum edge is incompatible with point birth')
        width_per_height = float((second[0]-first[0])/b)
        values.append(_harmonic_interval(0., lo, lo, width_per_height*lo, hi-lo))
    return math.fsum(values)


def point_factor(birth):
    """Positive original point-cone squares; no Gram eigenvalue repair."""
    rows = []
    for fragment in birth.fragments:
        bx, by = map(float, fragment.gradient)
        for triangle in fragment.triangles:
            a, b, c = sorted(v[2]-birth.datum for v in triangle)
            if a > 0:
                continue
            if b <= 0:
                raise ValueError('Positive point-cone source factors required')
            coefficient = projected_area(triangle)/(3*b*c)
            root = np.sqrt(float(coefficient/birth.volume_coefficient))
            rows.extend(root*np.array([[np.sqrt(.3), -.75*bx/np.sqrt(.3), -.75*by/np.sqrt(.3)],
                                      [0., np.sqrt(1.125)*bx, np.sqrt(1.125)*by]]))
    return np.asarray(rows)


class BirthLimitSystem:
    """Positive local Gram action with 2x2 preconditioning and original 40 CG."""
    def __init__(self, mappings, factors, volumes, beta):
        self.factors = [factor@mapping for factor, mapping in zip(factors, mappings)]
        self.beta = beta
        self.h = np.asarray(volumes)[:, None]
        count = len(volumes)
        blocks = np.repeat(np.eye(2)[None], count, axis=0)
        for factor in self.factors:
            for i in range(count):
                local = factor[:, 2*i:2*i+2]
                blocks[i] += beta*(local.T@local)
        self.cholesky = np.linalg.cholesky(blocks)

    def q_action(self, value):
        vector = value.ravel()
        result = np.zeros_like(vector)
        for factor in self.factors:
            result += factor.T@(factor@vector)
        return result.reshape(value.shape)

    def apply(self, value):
        return value+self.beta*self.q_action(value)

    def precondition(self, residual, scheme):
        if scheme != 'block':
            raise ValueError('Only original local block preconditioning is available')
        result = np.empty_like(residual)
        for i, chol in enumerate(self.cholesky):
            result[i, 0] = np.linalg.solve(chol.T, np.linalg.solve(chol, residual[i, 0]))
        return result


def point_limits(context, requests):
    """Requests are (parent, original_source_id, positive stage scale k_i)."""
    part = context.partition
    requests = list(requests)
    if not requests:
        raise ValueError('At least one explicit original birth source required')
    keys = [(p, s) for p, s, _ in requests]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate original birth source')
    scales = np.array([k for _, _, k in requests], float)
    if not np.isfinite(scales).all() or (scales <= 0).any():
        raise ValueError('Finite strictly positive birth stage scales required')
    singles = [context.point_limit(*key) for key in keys]
    births = [SourceBirthGeometry(part.patch.cells[p].subset_sources([s])) for p, s in keys]
    coefficients = np.array([float(b.volume_coefficient) for b in births])*scales**3
    if not np.isfinite(coefficients).all() or (coefficients <= 0).any():
        raise ValueError('Birth path volume coefficients exceed represented range')
    roots = np.sqrt(coefficients)
    count = len(keys)
    mappings = np.zeros((count, 3, 2*count))
    grams = np.array([b.scaled_gram_limit for b in births], float)
    factors = [point_factor(b) for b in births]
    # Recover the single-region divergence map directly from the exact faces.
    # The single-region Q alone cannot recover its signed cross terms.
    lookup = {key: i for i, key in enumerate(keys)}
    connections = []
    for i in range(count):
        mappings[i, 1:, 2*i:2*i+2] = np.eye(2)
    for face in birth_faces(part, keys):
        li = lookup.get((face['left_parent'], face['left_source']))
        ri = lookup.get((face['right_parent'], face['right_source']))
        if li == ri:
            continue
        section, normal = face_section(face['segment']), face['normal']
        wall = min(face['left_parent'], face['right_parent']) < 0
        if li is not None and ri is not None:
            if births[li].datum != births[ri].datum:
                continue
            area = harmonic_height_coefficient(section, births[li].datum, scales[li], scales[ri])
            if area == 0:
                continue
            for owner in (li, ri):
                weight = scales[owner]*area/(2*roots[owner])
                mappings[owner, 0, 2*ri:2*ri+2] += weight*normal/roots[ri]
                mappings[owner, 0, 2*li:2*li+2] -= weight*normal/roots[li]
            connections.append(dict(left=li, right=ri, internal=face['internal'],
                                    harmonic_area_height_squared_coefficient=area))
        else:
            index, owner = (li, face['right']) if li is not None else (ri, face['left'])
            if not wall:
                if owner is None or owner >= len(part.pools):
                    continue
                form = part.pools[owner]['form']
                if F(form['datum'])+F(float(form['stage_offset'])) <= births[index].datum:
                    continue
            direction = (1 if ri is not None else -1)*float(births[index].scaled_face_divergence_limit(section))*normal
            mappings[index, 0, 2*index:2*index+2] += direction
    old_columns = np.concatenate([s['old_divergence_column_sqrt_height_coefficient']*np.sqrt(k)
                                  for s, k in zip(singles, scales)], axis=1)
    if not np.isfinite(mappings).all() or not np.isfinite(old_columns).all():
        raise ValueError('Coupled source limit exceeds represented range')
    poles = []
    for pole, stress in context.poles:
        coupling = (old_columns.T@stress).reshape(count, 1, 2)
        system = BirthLimitSystem(mappings, factors, coefficients, pole['beta'])
        solution, stats = range_cg(system, coupling, 40, preconditioner='block')
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original 40-CG simultaneous birth pressure residual gate failed')
        work = float(np.sum(coupling*solution))
        if not np.isfinite(work) or work < 0:
            raise ValueError('Original positive birth pressure contraction failed')
        poles.append(dict(alpha=pole['alpha'], beta=pole['beta'], **stats,
            energy_path_slope=-.5*pole['alpha']*pole['beta']*work,
            auxiliary_velocity_path_product_limit=-pole['beta']*solution[:, 0]/roots[:, None]))
    return dict(source_keys=keys, stage_scales=scales, volume_path_coefficients=coefficients,
        newborn_jet_maps=mappings, newborn_scaled_grams=grams, newborn_scaled_factors=factors,
        old_divergence_column_sqrt_path_coefficient=old_columns,
        immediate_newborn_connections=connections, poles=poles,
        fixed_old_state_energy_path_slope=sum(p['energy_path_slope'] for p in poles),
        independent_single_source_sum=sum(k*s['fixed_old_state_energy_height_slope'] for k, s in zip(scales, singles)),
        full_metric_front_force_or_time_or_gameplay_accepted=False)
