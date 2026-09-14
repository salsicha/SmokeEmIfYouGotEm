"""Small closed 2-D variational stage, NOT native or original FV evolution.

Proposed energy H(h,v) from rational_dual_energy_reference supplies flux F=H_v
and depth derivative a=H_h. The rotational velocity bracket is
  h_t=-div(F), v_t=-grad(a)-curl(v)*J(F/h), J(u)=(-u_y,u_x).
Paired periodic central grad/div cancel energy work; F=h*u makes the rotational
work vanish pointwise. No global energy projection or damping is applied.

Depth derivatives use expensive basis directions only for <=64-cell controls.
The actual h_t direction is checked independently for MC branch additivity;
failure rejects the stage. This is NOT a wetting, positivity, shock/breaking,
open-boundary, efficient-gradient or physical-model qualification. It changes
transport relative to original FV and must never be spliced into its histories.
"""
import numpy as np
from reconstructed_pressure_rates import PressureGeometryRate
from rational_dual_energy_reference import evaluate


def gradient(f,dx):
    return np.stack(((np.roll(f,-1,1)-np.roll(f,1,1))/(2*dx),
                     (np.roll(f,-1,0)-np.roll(f,1,0))/(2*dx)),axis=-1)


def divergence(f,dx):
    return ((np.roll(f[...,0],-1,1)-np.roll(f[...,0],1,1))
            +(np.roll(f[...,1],-1,0)-np.roll(f[...,1],1,0)))/(2*dx)


def stage(geometry,canonical_velocity):
    g=geometry;h=g.h;v=np.asarray(canonical_velocity,dtype=float)
    if h.size>64:raise ValueError('Expensive basis derivative is a bounded control only')
    result=evaluate(g,v);flux=result['canonical_gradient_flux'];u=result['layer_velocity']
    ht=-divergence(flux,g.dx);a=np.empty_like(h);area=g.dx**2
    for point in np.ndindex(h.shape):
        basis=np.zeros_like(h);basis[point]=1.
        tangent=PressureGeometryRate(g,g.bed,basis)
        a[point]=evaluate(g,v,tangent=tangent)['depth_direction']['total']/area
    actual_depth=evaluate(g,v,tangent=PressureGeometryRate(g,g.bed,ht))['depth_direction']['total']
    assembled=float(np.sum(a*ht))*area
    branch_error=abs(assembled-actual_depth)
    if branch_error>1e-10*max(1.,abs(actual_depth),abs(assembled)):
        raise ValueError('MC branch does not supply the assembled depth gradient on this stage')
    omega=gradient(v[...,1],g.dx)[...,0]-gradient(v[...,0],g.dx)[...,1]
    rotation=omega[...,None]*np.stack((-u[...,1],u[...,0]),axis=-1)
    vt=-gradient(a,g.dx)-rotation
    energy_rate=actual_depth+float(np.sum(flux*vt))*area
    return dict(depth_rate=ht,canonical_velocity_rate=vt,depth_energy_gradient=a,
        flux=flux,layer_velocity=u,energy=result['total'],energy_rate=energy_rate,
        net_mass_rate=float(np.sum(ht))*area,branch_chain_rule_error=branch_error,
        rotational_work=float(np.sum(flux*rotation))*area,
        pressure_residuals=[p['relative_residual'] for p in result['poles']],
        original_fv_transport_preserved=False,
        nonlinear_history_or_wetting_or_breaking_or_gameplay_accepted=False)
