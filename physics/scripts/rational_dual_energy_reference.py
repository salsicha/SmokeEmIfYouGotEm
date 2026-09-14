"""Two-pole dual kinetic-energy primitive, NOT a replacement river solver.

For canonical velocity v, q=sqrt(h)*v, A_j=I+lambda_j*(W.T W+.75 V.T V),
S=cI+sum(w_j A_j^-1), c=1-sum(w_j), and flux=sqrt(h)*S*q.
The proposed dual kinetic energy is .5*q.T*S*q. Its exact depth-direction
derivative contains -.5*sum(w_j*z_j.T*A_j,t*z_j), z_j=A_j^-1*q.

This is the Legendre-dual quadratic form of the existing inverse-response
metric, not proof that the old acceleration blend conserves it. No canonical
time integrator, FV replacement, breaking closure, dry/open boundary data or
native mode is supplied. All original pole constants and 40-CG gates remain.
"""
import numpy as np
from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem


def factor_direction(geometry, tangent, normalized):
    """W_t*z,V_t*z at fixed normalized z; no dense derivative matrices."""
    g=geometry;h=g.h;root=np.sqrt(h);ell=tangent.mass_rate/(2*h)
    u=normalized/root[...,None];ut=-ell[...,None]*u
    d,e=g.kinematic_components(u);dt,et=tangent.kinematic_rate(u)
    du,eu=g.kinematic_components(ut)
    w=root*(h*d-1.5*e);v=root*e
    wt=ell*w+root*(tangent.mass_rate*d+h*(dt+du)-1.5*(et+eu))
    vt=ell*v+root*(et+eu)
    return wt,vt


def evaluate(geometry, canonical_velocity, *, tangent=None, preconditioner='block'):
    g=geometry;h=g.h;v=np.asarray(canonical_velocity,dtype=float)
    if (not g.periodic or np.any(h<=0) or v.shape!=(*h.shape,2)
            or not np.isfinite(v).all()):
        raise ValueError('Dual primitive requires an explicitly closed, positive, finite domain')
    if tangent is not None and (tangent.geometry is not g or tangent.one_sided):
        raise ValueError('Original registered stationary-positive tangent required')
    if preconditioner not in ('block','patch','spectral-flat'):
        raise ValueError('Unknown dual pressure preconditioner')
    system_type=ReconstructedAccelerationSystem
    if preconditioner=='patch':
        from patch_pressure_preconditioner import PatchPressureSystem
        system_type=PatchPressureSystem
    root=np.sqrt(h);q=root[...,None]*v
    response=(1-float(np.sum(WEIGHTS)))*q
    poles=[];operator_direction=0.
    for length,weight in zip(LENGTHS,WEIGHTS):
        system=system_type(g,float(length))
        z,stats=system.solve(q,iterations=40,preconditioner=preconditioner)
        response+=weight*z
        directional=0.
        if tangent is not None:
            wt,vt=factor_direction(g,tangent,z)
            directional=-float(weight*length)*float(np.sum(system.w(z)*wt+.75*system.v(z)*vt))
            operator_direction+=directional
        poles.append(dict(length=float(length),weight=float(weight),
            normalized_auxiliary_velocity=z,operator_energy_direction=directional*g.dx**2,**stats))
    area=g.dx**2
    kinetic=.5*float(np.sum(q*response))*area
    potential=float(np.sum(9.81*h*(.5*h+g.bed)))*area
    flux=root[...,None]*response
    direction=None
    if tangent is not None:
        qt=(tangent.mass_rate/(2*h))[...,None]*q
        normalization=float(np.sum(qt*response))*area
        gravity=float(np.sum(9.81*(h+g.bed)*tangent.mass_rate))*area
        direction=dict(total=normalization+operator_direction*area+gravity,
            mass_normalization=normalization,pole_operator=operator_direction*area,potential=gravity,
            interpretation='fixed canonical velocity; not the old conserved-momentum direction')
    return dict(kinetic=kinetic,potential=potential,total=kinetic+potential,
        canonical_gradient_flux=flux,layer_velocity=response/root[...,None],
        depth_direction=direction,poles=poles,
        nonlinear_time_evolution_or_dry_boundary_or_gameplay_accepted=False)
