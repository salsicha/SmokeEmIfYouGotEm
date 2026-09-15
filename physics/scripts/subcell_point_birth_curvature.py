"""Leading singularity of the existing COMMON-TRACE curvature at point birth.

This diagnoses a guarded expression; it does NOT authorize extending that
trace to a wet front. Both old and newborn blocks below are lim e^2 times
sum alpha*(T.T*N(w)*u-N(w)*w), with V_new=c*k^3*e^3 and bounded physical u.
It is a nonlinear-equation RHS component, not an accepted acceleration law.
"""
from fractions import Fraction as F
import numpy as np

from pressure_cg_range_reference import solve as range_cg
from subcell_simultaneous_birth_pressure import point_limits, birth_faces, BirthLimitSystem
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_curvature import original_gradient
from subcell_source_frames import face_section
from subcell_wet_pool_pressure import WetPoolPressureSystem


def point_curvature_limit(context, requests, newborn_velocity=(0., 0.)):
    limit = point_limits(context, requests)
    part = context.partition
    old, count = len(part.pools), len(limit['source_keys'])
    new_u = np.asarray(newborn_velocity, float)
    if new_u.shape == (2,):
        new_u = np.broadcast_to(new_u, (count, 2))
    if new_u.shape != (count, 2) or not np.isfinite(new_u).all():
        raise ValueError('Finite bounded physical newborn velocities required')
    old_u = np.array([p['momentum'] for p in part.pools])/np.array([p['volume'] for p in part.pools])[:, None]
    roots = np.sqrt(limit['volume_path_coefficients'])
    scales = limit['stage_scales']
    columns = limit['old_divergence_column_sqrt_path_coefficient']
    nmap = limit['newborn_jet_maps'][:, 0]*np.repeat(roots, 2)[None, :]/(roots*scales)[:, None]
    lookup = {key: i for i, key in enumerate(limit['source_keys'])}
    births = [SourceBirthGeometry(part.patch.cells[p].subset_sources([s])) for p, s in limit['source_keys']]
    edges = []
    scope = dict(original_old_new_faces=0, equal_source_slope_faces=0,
                 old_below_birth_datum_faces=0, delayed_face_contact=0, leading_curvature_faces=0)
    for face in birth_faces(part, limit['source_keys']):
        if min(face['left_parent'], face['right_parent']) < 0:
            continue  # No invented exterior bed extension.
        li = lookup.get((face['left_parent'], face['left_source']))
        ri = lookup.get((face['right_parent'], face['right_source']))
        if (li is None) == (ri is None):
            continue  # Old/old is regular; new/new contributes at lower order.
        index, owner = (li, face['right']) if li is not None else (ri, face['left'])
        if owner is None or owner >= old:
            continue
        scope['original_old_new_faces'] += 1
        gl = original_gradient(part, face['left_parent'], face['left_source'])
        gr = original_gradient(part, face['right_parent'], face['right_source'])
        jump = tuple(b-a for a, b in zip(gl, gr))
        if jump == (0, 0):
            scope['equal_source_slope_faces'] += 1
            continue
        if face['internal']:
            a, b = part.sampler.xyz[face['edge_vertex_ids']]
            tangent = tuple(F(float(b[i]))-F(float(a[i])) for i in range(2))
        else:
            tangent = tuple(F(int(face['normal'][i] == 0)) for i in range(2))
        if sum(a*b for a, b in zip(jump, tangent)) != 0:
            raise ValueError('Original source slopes disagree along birth curvature edge')
        birth = births[index]
        form = part.pools[owner]['form']
        old_depth = F(form['datum'])+F(float(form['stage_offset']))-birth.datum
        if old_depth <= 0:
            scope['old_below_birth_datum_faces'] += 1
            continue
        width = F(0)
        for first, second in face_section(face['segment']).source_segments:
            low, high = sorted((first[1]-birth.datum, second[1]-birth.datum))
            if low < 0 or (low == 0 and high == 0):
                raise ValueError('Original point curvature requires sloping minimum face')
            if low == 0:
                width += (second[0]-first[0])/high
        if width == 0:
            scope['delayed_face_contact'] += 1
            continue
        normal = face['normal']
        jump_normal = float(np.array(tuple(map(float, jump)))@normal)
        m2 = float(width*old_depth*old_depth/4)*scales[index]
        if not np.isfinite(m2) or m2 <= 0 or not np.isfinite(jump_normal) or jump_normal == 0:
            raise ValueError('Original nonzero curvature coefficient exceeds represented range')
        edges.append(dict(old=owner, newborn=index, squared_mean_depth_over_path=m2,
                          hessian=jump_normal*np.outer(normal, normal), internal=face['internal'],
                          left_source=face['left_source'], right_source=face['right_source']))
        scope['leading_curvature_faces'] += 1
    result = np.zeros((old+count, 2))
    records = []
    for pole in limit['poles']:
        alpha, beta = pole['alpha'], pole['beta']
        a = -beta*pole['coupled_response']/roots[:, None]
        d = nmap@a.ravel()  # lim e^2*D*w on newborn sources.
        nw = np.zeros_like(result)
        nu_new = np.zeros((count, 2))
        for edge in edges:
            i, j = edge['old'], edge['newborn']
            coefficient = -.75*edge['squared_mean_depth_over_path']*d[j]
            nw_edge = .25*coefficient*(edge['hessian']@a[j])
            nw[i] += nw_edge
            nw[old+j] += nw_edge
            nu_new[j] += .25*coefficient*(edge['hessian']@(old_u[i]+new_u[j]))
        birth_system = BirthLimitSystem(limit['newborn_jet_maps'], limit['newborn_scaled_factors'],
                                        limit['volume_path_coefficients'], beta)
        y, new_stats = range_cg(birth_system, (nu_new/roots[:, None])[:, None], 40, preconditioner='block')
        system = WetPoolPressureSystem(part, beta)
        divergence = columns@y.ravel()
        rhs = system.factor_transpose([p['form']['factor'][:, 0]*value
                                       for p, value in zip(part.pools, divergence)])
        solution, old_stats = system.solve(rhs)
        if max(new_stats['relative_residual'], old_stats['relative_residual']) > 2e-5:
            raise ValueError('Original 40-CG point curvature pullback residual gate failed')
        force = -nw
        force[:old] -= beta*system.root[:, None]*solution[:, 0]
        work = float(np.sum(np.vstack((old_u, new_u))*force))
        if not np.isfinite(force).all() or not np.isfinite(work):
            raise ValueError('Original point curvature force exceeds represented range')
        if abs(work) > 1e-10:
            raise ValueError('Original point curvature skew-work gate failed')
        result += alpha*force
        records.append(dict(alpha=alpha, beta=beta, force_path_squared_limit=force,
            skew_work_limit=work, old_pullback_solve=old_stats, newborn_pullback_solve=new_stats))
    if not np.isfinite(result).all():
        raise ValueError('Combined point curvature force exceeds represented range')
    return dict(limit=limit, edges=edges, front_edge_scope=scope, old_force_path_squared_limit=result[:old],
        newborn_force_path_squared_limit=result[old:], poles=records,
        common_trace_front_or_complete_force_or_time_or_native_or_gameplay_accepted=False)
