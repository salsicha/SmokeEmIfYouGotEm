"""Research closed two-pole stage with EP donor mass/energy work pairing.

Positive-depth periodic domains only. Dry mass transport tests do not extend
the pressure model to dry states. No full-history, entropy, open boundary or
gameplay qualification. This is not the original FV/Rusanov model.
"""
import numpy as np
from rational_dual_energy_reference import evaluate
from rational_velocity_bracket_reference import gradient
from reconstructed_pressure_rates import PressureGeometryRate
from reverse_rational_depth_gradient import depth_gradient
from extremum_preserving_transport import ExtremumPreservingTransport
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def stage(geometry,canonical_velocity):
    g=geometry;v=np.asarray(canonical_velocity,dtype=float)
    result=evaluate(g,v);flux=result['canonical_gradient_flux'];u=result['layer_velocity']
    transport=ExtremumPreservingTransport(g.h,g.bed,u,g.dx,periodic=g.periodic)
    ht=transport.mass_rate;area=g.dx**2
    a,reverse=depth_gradient(g,v,result,ht)
    actual=evaluate(g,v,tangent=PressureGeometryRate(g,g.bed,ht))['depth_direction']['total']
    assembled=float(np.sum(a*ht))*area;error=abs(assembled-actual)
    if error>1e-10*max(1.,abs(actual),abs(assembled)):
        raise ValueError('Reverse MC branch does not match original actual-direction derivative')
    omega=gradient(v[...,1],g.dx)[...,0]-gradient(v[...,0],g.dx)[...,1]
    rotation=omega[...,None]*np.stack((-u[...,1],u[...,0]),axis=-1)
    vt=-transport.adjoint(a,normalized=True)-rotation
    return dict(depth_rate=ht,canonical_velocity_rate=vt,depth_energy_gradient=a,flux=flux,
        layer_velocity=u,energy=result['total'],energy_rate=actual+float(np.sum(flux*vt))*area,
        net_mass_rate=float(np.sum(ht))*area,branch_chain_rule_error=error,
        rotational_work=float(np.sum(flux*rotation))*area,
        pressure_residuals=[p['relative_residual'] for p in result['poles']],reverse=reverse,
        mass_only_forward_euler_bound=transport.draining_bound,
        original_fv_transport_preserved=False,
        nonlinear_history_or_wetting_or_breaking_or_gameplay_accepted=False)


def rk2_step(depth,bed,canonical_velocity,dx,dt):
    """One explicit SSP-RK2 trial; no clipping, projection or automatic retry.

    Both forward-Euler constituents must respect their own donor bound and
    remain strictly positive for the current pressure primitive. A failure is
    returned as an exception, not repaired or relabeled as an accepted step.
    """
    if not np.isfinite(dt) or dt<=0:raise ValueError('Finite positive step required')
    h=np.asarray(depth,dtype=float);v=np.asarray(canonical_velocity,dtype=float)
    def make(hh):
        return ReconstructedPressureGeometry(hh,bed,dx,periodic=True,
            pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    def euler(hh,vv,r):
        if dt>r['mass_only_forward_euler_bound']:raise ValueError('Step exceeds donor draining bound')
        out_h=hh+dt*r['depth_rate'];out_v=vv+dt*r['canonical_velocity_rate']
        if np.any(out_h<=0) or not np.isfinite(out_h).all() or not np.isfinite(out_v).all():
            raise ValueError('Trial leaves qualified positive pressure domain; no repair')
        return out_h,out_v
    first=stage(make(h),v);h1,v1=euler(h,v,first)
    second=stage(make(h1),v1);h2,v2=euler(h1,v1,second)
    out_h=.5*h+.5*h2;out_v=.5*v+.5*v2
    return out_h,out_v,dict(initial_energy=first['energy'],
        maximum_stage_chain_rule_error=max(first['branch_chain_rule_error'],second['branch_chain_rule_error']),
        maximum_stage_energy_rate=max(abs(first['energy_rate']),abs(second['energy_rate'])),
        maximum_pressure_residual=max(first['pressure_residuals']+second['pressure_residuals']),
        minimum_mass_step_bound=min(first['mass_only_forward_euler_bound'],second['mass_only_forward_euler_bound']))
