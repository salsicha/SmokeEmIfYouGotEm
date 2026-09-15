"""Physical-momentum energy and analytic local volume gradient on wet pools.

The inverse factors are algebraically derived from the SAME original two poles.
No new dispersion fit, dense inverse, finite-difference force, depth repair or
conservation projection. This supplies coefficients for transport, not a mass
flux, nonlinear bed-force equation, topology transition or time integrator.
"""
import math
import numpy as np

from rational_primal_energy import K0, BETAS, ALPHAS
from subcell_mechanical_energy import squared_depth_integral
from subcell_wet_pool_pressure import WetPoolPressureSystem, shared_subsegments, harmonic_area
from subcell_source_frames import face_section, physical_datum
from subcell_source_face_section import stage_difference
from subcell_wet_pool_pressure_rate import harmonic_area_rate
from triangle_face_section import TriangleFaceSection


def kinetic_volume_gradient(system, q):
    """Reverse derivative of .5*q.T*Q*q at fixed normalized q (all pools).

    Q is the unscaled exact-terrain kinetic matrix in A=I+length*Q. Work is
    accumulated on original shared faces and physical walls, with both owners'
    divergence denominators and velocity normalization kept independently.
    There is no pressure solve per volume unknown.
    """
    u = system._vector(q)[:, 0]/system.root[:, None]
    volume = system.h[:, 0]
    pools = system.partition.pools
    jet = np.column_stack((system.divergence(u), u))
    gram = np.array([p['form']['gram'] for p in pools])
    gram_v = np.array([p['form']['volume_derivative'] for p in pools])
    f = np.einsum('nij,nj->ni', gram, jet)
    physical = system.divergence_transpose(f[:, 0])+f[:, 1:]
    local = .5*np.einsum('ni,nij,nj->n', jet, gram_v, jet)
    normalization = -.5*np.sum(u*physical, axis=1)/volume
    shared, wall = np.zeros_like(volume), np.zeros_like(volume)
    for left, right, axis, _ in system.partition.patch.faces:
        if left >= 0 and right >= 0:
            first = system.partition.boundary_segments(left, axis, 1)
            second = system.partition.boundary_segments(right, axis, -1)
            for li, ri, segment in shared_subsegments(first, second):
                lp, rp = pools[li]['form'], pools[ri]['form']
                args = (segment, lp['stage_offset'], rp['stage_offset'], lp['datum'], rp['datum'])
                area = harmonic_area(*args)
                jump = u[ri, axis]-u[li, axis]
                adjoint = jump*(f[li, 0]/(2*volume[li])+f[ri, 0]/(2*volume[ri]))
                shared[li] += adjoint*harmonic_area_rate(*args, 1., 0.)/lp['wet_area']
                shared[ri] += adjoint*harmonic_area_rate(*args, 0., 1.)/rp['wet_area']
                for owner in (li, ri):
                    shared[owner] -= (f[owner, 0]/volume[owner])*(area/(2*volume[owner]))*jump
        else:
            parent, sign = (right, -1) if left < 0 else (left, 1)
            for owner, segment in system.partition.boundary_segments(parent, axis, sign):
                form = pools[owner]['form']
                face = face_section(segment)
                area, _, width = face.moments(form['stage_offset'], form['datum'])
                wall[owner] -= sign*f[owner, 0]*u[owner, axis]*(width/form['wet_area']-area/volume[owner])/volume[owner]
    for face in system.partition.internal_faces:
        li, ri = face['left'], face['right']
        if li is None or ri is None:
            continue
        lf, rf = pools[li]['form'], pools[ri]['form']
        args = (face['segment'], lf['stage_offset'], rf['stage_offset'], lf['datum'], rf['datum'])
        area = harmonic_area(*args)
        jump = float((u[ri]-u[li])@face['normal'])
        adjoint = jump*(f[li, 0]/(2*volume[li])+f[ri, 0]/(2*volume[ri]))
        shared[li] += adjoint*harmonic_area_rate(*args, 1., 0.)/lf['wet_area']
        shared[ri] += adjoint*harmonic_area_rate(*args, 0., 1.)/rf['wet_area']
        for owner in (li, ri):
            shared[owner] -= (f[owner, 0]/volume[owner])*(area/(2*volume[owner]))*jump
    result = local+normalization+shared+wall
    if not np.isfinite(result).all():
        raise ValueError('Exact wet-pool reverse volume gradient exceeds represented range')
    return dict(value=result, local_geometry=local, velocity_normalization=normalization,
                shared_faces=shared, reflecting_walls=wall)


def evaluate(partition, physical_momentum, gravity=9.81):
    """Positive inverse-metric energy, canonical velocity and fixed-p dE/dV."""
    first = WetPoolPressureSystem(partition, float(BETAS[0]))
    p = first._vector(physical_momentum)
    if not np.isfinite(gravity) or gravity <= 0:
        raise ValueError('Positive finite gravity required')
    root = first.root[:, None, None]
    volume = first.h[:, 0]
    q = p/root
    mapped = K0*q
    density = .5*K0*np.sum(q[:, 0]*q[:, 0], axis=1)
    gradient = np.zeros_like(volume)
    poles = []
    for i, (beta, alpha) in enumerate(zip(BETAS, ALPHAS)):
        system = first if i == 0 else WetPoolPressureSystem(partition, float(beta))
        z, stats = system.solve(q)
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original inverse-factor 40-CG residual gate failed')
        factors = system.factor_action(z)
        # Do not form Q*z=(q-z)/beta; cancellation destroys small constant modes.
        qz = system.factor_transpose(factors)
        mapped += alpha*qz
        density += .5*alpha*(np.array([float(f@f) for f in factors])
                              +beta*np.sum(qz[:, 0]*qz[:, 0], axis=1))
        reverse = kinetic_volume_gradient(system, z)
        gradient += alpha*reverse['value']
        poles.append(dict(beta=float(beta), alpha=float(alpha), normalized_auxiliary_velocity=z,
                          reverse_terms=reverse, **stats))
    canonical = mapped/root
    velocity = p/volume[:, None, None]
    normalization = -.5*np.sum(canonical[:, 0]*velocity[:, 0], axis=1)
    datum = min(physical_datum(cell) for cell in partition.patch.cells)
    heights = np.array([stage_difference(0., datum, pool['form']['stage_offset'], pool['form']['datum'])
                        for pool in partition.pools])
    potential = gravity*sum(height*pool['volume']-.5*squared_depth_integral(
        pool['storage'], pool['form']['stage_offset'], True) for pool, height in zip(partition.pools, heights))
    kinetic = float(np.sum(density))
    contraction = .5*float(np.sum(q*mapped))
    if not np.isfinite(density).all() or not np.isfinite(canonical).all() or (density < 0).any():
        raise ValueError('Positive pool kinetic energy exceeds represented range')
    return dict(kinetic=kinetic, potential=float(potential), total=kinetic+float(potential),
        kinetic_density=density, canonical_velocity=canonical, layer_velocity=velocity,
        volume_gradient=normalization+gradient+gravity*heights,
        volume_gradient_terms=dict(momentum_normalization=normalization, pressure_geometry=gradient,
                                   potential=gravity*heights),
        positive_energy_contraction_error=abs(kinetic-contraction), poles=poles,
        reference_datum_m=datum, mass_or_nonlinear_bed_force_or_time_or_gameplay_accepted=False)
