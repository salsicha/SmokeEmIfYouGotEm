"""Research C1 pressure-energy stage with continuous positive mass transport.

Both original dispersion poles and independent tangent gates are retained.
Strictly positive periodic only: not dry/open/entropy/native qualification.
"""
import numpy as np
from smooth_pressure_geometry import SmoothPressureGeometry,SmoothPressureGeometryRate
from smooth_pressure_reverse import smooth_coefficient_reverse
from continuous_extremum_transport import ContinuousExtremumTransport
from rational_dual_energy_reference import evaluate
from reverse_rational_depth_gradient import depth_gradient
from rational_velocity_bracket_reference import gradient


def make(h,b,dx):return SmoothPressureGeometry(h,b,dx,periodic=True)


def stage(g,canonical_velocity):
    if not isinstance(g,SmoothPressureGeometry):raise ValueError('Matching smooth pressure geometry required')
    v=np.asarray(canonical_velocity,dtype=float);response=evaluate(g,v)
    flux=response['canonical_gradient_flux'];u=response['layer_velocity'];area=g.dx**2
    transport=ContinuousExtremumTransport(g.h,g.bed,u,g.dx,periodic=True)
    ht=transport.mass_rate
    a,reverse=depth_gradient(g,v,response,ht,reverse_coefficients=smooth_coefficient_reverse)
    actual=evaluate(g,v,tangent=SmoothPressureGeometryRate(g,g.bed,ht))['depth_direction']['total']
    assembled=float(np.sum(a*ht))*area;error=abs(assembled-actual)
    if error>1e-10*max(1.,abs(actual),abs(assembled)):
        raise ValueError('Smooth reverse derivative does not match independent actual-direction tangent')
    omega=gradient(v[...,1],g.dx)[...,0]-gradient(v[...,0],g.dx)[...,1]
    rotation=omega[...,None]*np.stack((-u[...,1],u[...,0]),axis=-1)
    vt=-transport.adjoint(a,normalized=True)-rotation
    return dict(depth_rate=ht,canonical_velocity_rate=vt,depth_energy_gradient=a,flux=flux,
        layer_velocity=u,energy=response['total'],energy_rate=actual+float(np.sum(flux*vt))*area,
        net_mass_rate=float(np.sum(ht))*area,branch_chain_rule_error=error,
        rotational_work=float(np.sum(flux*rotation))*area,
        pressure_residuals=[p['relative_residual'] for p in response['poles']],reverse=reverse,
        mass_only_forward_euler_bound=transport.draining_bound,
        original_fv_transport_preserved=False,
        nonlinear_history_or_wetting_or_breaking_or_gameplay_accepted=False)


def rk2_step(depth,bed,canonical_velocity,dx,dt):
    if not np.isfinite(dt) or dt<=0:raise ValueError('Finite positive step required')
    h=np.asarray(depth,dtype=float);v=np.asarray(canonical_velocity,dtype=float)
    def euler(hh,vv,r):
        if dt>r['mass_only_forward_euler_bound']:raise ValueError('Step exceeds donor draining bound')
        a=hh+dt*r['depth_rate'];c=vv+dt*r['canonical_velocity_rate']
        if np.any(a<=0) or not np.isfinite(a).all() or not np.isfinite(c).all():
            raise ValueError('Trial leaves qualified positive pressure domain; no repair')
        return a,c
    first=stage(make(h,bed,dx),v);h1,v1=euler(h,v,first)
    second=stage(make(h1,bed,dx),v1);h2,v2=euler(h1,v1,second)
    return .5*h+.5*h2,.5*v+.5*v2,dict(initial_energy=first['energy'],
        maximum_stage_chain_rule_error=max(first['branch_chain_rule_error'],second['branch_chain_rule_error']),
        maximum_stage_energy_rate=max(abs(first['energy_rate']),abs(second['energy_rate'])),
        maximum_pressure_residual=max(first['pressure_residuals']+second['pressure_residuals']),
        minimum_mass_step_bound=min(first['mass_only_forward_euler_bound'],second['mass_only_forward_euler_bound']))
