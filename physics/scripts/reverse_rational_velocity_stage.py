"""Local reverse version of the research closed variational stage.

Same positive-domain model and original pressure gates. Retains an independent
directional chain-rule check, not a global energy correction. No native mode,
positive/wet-bank flux, original FV history, breaking or open-boundary closure.
"""
import numpy as np
from rational_dual_energy_reference import evaluate
from rational_velocity_bracket_reference import gradient,divergence
from reconstructed_pressure_rates import PressureGeometryRate
from reverse_rational_depth_gradient import depth_gradient


def stage(geometry,canonical_velocity):
    g=geometry;v=np.asarray(canonical_velocity,dtype=float)
    result=evaluate(g,v);flux=result['canonical_gradient_flux'];u=result['layer_velocity']
    ht=-divergence(flux,g.dx);area=g.dx**2
    a,reverse=depth_gradient(g,v,result,ht)
    actual_depth=evaluate(g,v,tangent=PressureGeometryRate(g,g.bed,ht))['depth_direction']['total']
    assembled=float(np.sum(a*ht))*area;branch_error=abs(assembled-actual_depth)
    if branch_error>1e-10*max(1.,abs(actual_depth),abs(assembled)):
        raise ValueError('Reverse MC branch does not match original actual-direction derivative')
    omega=gradient(v[...,1],g.dx)[...,0]-gradient(v[...,0],g.dx)[...,1]
    rotation=omega[...,None]*np.stack((-u[...,1],u[...,0]),axis=-1)
    vt=-gradient(a,g.dx)-rotation
    return dict(depth_rate=ht,canonical_velocity_rate=vt,depth_energy_gradient=a,flux=flux,
        layer_velocity=u,energy=result['total'],energy_rate=actual_depth+float(np.sum(flux*vt))*area,
        net_mass_rate=float(np.sum(ht))*area,branch_chain_rule_error=branch_error,
        rotational_work=float(np.sum(flux*rotation))*area,
        pressure_residuals=[p['relative_residual'] for p in result['poles']],reverse=reverse,
        original_fv_transport_preserved=False,
        nonlinear_history_or_wetting_or_breaking_or_gameplay_accepted=False)
