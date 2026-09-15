"""Exact-direction bridge to physical conserved variables, RESEARCH ONLY.

Keep the existing smooth geometry, both poles and 40-CG solves. For p=R*S*q,
q=R*v, R=sqrt(h), differentiate every normalization and pole operator:
  z_j,t=A_j^-1(q_t-A_j,t*z_j), p_t=ell*p+R*(c*q_t+sum(w_j*z_j,t)).
This is a coordinate derivative, not a new momentum flux or repaired stage.
It is needed to derive a conservative physical-momentum/energy coupling;
using h*v_t or the canonical momentum rate in its place is incorrect locally.
Strictly positive periodic smooth geometry only; no dry/open/native claim.
"""
import numpy as np
from finite_depth_pressure_reference import WEIGHTS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from rational_dual_energy_reference import evaluate, factor_direction
from reverse_rational_depth_gradient import depth_gradient
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from smooth_pressure_reverse import smooth_coefficient_reverse


def factor_transpose_direction(system, tangent, scalar, *, bottom=False):
    """Analytic W_t.T*s or V_t.T*s at fixed s; independent of factor_direction."""
    g=system.geometry; h=g.h; root=np.sqrt(h); ell=tangent.mass_rate/(2*h)
    s=g._scalar(scalar)
    if tangent.geometry is not g or tangent.one_sided:
        raise ValueError('Matching stationary-positive tangent required')
    if bottom:
        transpose=system.transpose_v
        inside=tangent.force_operator_rate(np.zeros_like(h),root*s)
    else:
        transpose=system.transpose_w
        inside=g.gradient_traction(-tangent.mass_rate*root*s,np.zeros_like(h))
        inside+=tangent.force_operator_rate(-h*root*s,-1.5*root*s)
    result=transpose(ell*s)+inside/root[...,None]-ell[...,None]*transpose(s)
    if not np.isfinite(result).all():
        raise ValueError('Factor transpose rate exceeds storage range')
    return result


def physical_rate(geometry,canonical_velocity,mass_rate,canonical_velocity_rate,*,derivative_preconditioner='block',primal_preconditioner='block',include_auxiliary_rates=False):
    g=geometry
    if not isinstance(g,SmoothPressureGeometry):
        raise ValueError('Matching smooth positive geometry required')
    v=np.asarray(canonical_velocity,dtype=float)
    vt=np.asarray(canonical_velocity_rate,dtype=float)
    ht=np.asarray(mass_rate,dtype=float)
    if (v.shape!=(*g.h.shape,2) or vt.shape!=v.shape or ht.shape!=g.h.shape
            or not all(np.isfinite(x).all() for x in (v,vt,ht))):
        raise ValueError('Registered finite state and direction required')
    response=evaluate(g,v,preconditioner=primal_preconditioner); tangent=SmoothPressureGeometryRate(g,g.bed,ht)
    if derivative_preconditioner not in ('block','patch','spectral-flat','spectral-frozen-depth'):
        raise ValueError('Unknown derivative preconditioner')
    system_type=ReconstructedAccelerationSystem
    if derivative_preconditioner=='patch':
        from patch_pressure_preconditioner import PatchPressureSystem
        system_type=PatchPressureSystem
    root=np.sqrt(g.h); ell=ht/(2*g.h); q=root[...,None]*v
    qt=root[...,None]*vt+ell[...,None]*q
    rt=(1-float(np.sum(WEIGHTS)))*qt; poles=[]
    for pole in response['poles']:
        system=system_type(g,pole['length'])
        z=pole['normalized_auxiliary_velocity']
        wz,vz=system.w(z),system.v(z)
        wt,bt=factor_direction(g,tangent,z)
        operator_rate=pole['length']*(
            factor_transpose_direction(system,tangent,wz)+system.transpose_w(wt)
            +.75*(factor_transpose_direction(system,tangent,vz,bottom=True)+system.transpose_v(bt)))
        zt,stats=system.solve(qt-operator_rate,iterations=40,preconditioner=derivative_preconditioner)
        if max(pole['relative_residual'],stats['relative_residual'])>2e-5:
            raise ValueError('Unqualified pole derivative residual')
        rt+=pole['weight']*zt
        entry=dict(length=pole['length'],weight=pole['weight'],**stats)
        if include_auxiliary_rates:
            entry.update(normalized_auxiliary_velocity=z,normalized_auxiliary_rate=zt)
        poles.append(entry)
    p=response['canonical_gradient_flux']
    pt=ell[...,None]*p+root[...,None]*rt
    # Legendre transformation of the quadratic kinetic energy, holding the
    # physical momentum p (not h*v) fixed: E_h=2*g*(h+b)-H_h, E_p=v.
    a,_=depth_gradient(g,v,response,ht,reverse_coefficients=smooth_coefficient_reverse)
    eh=2*9.81*(g.h+g.bed)-a
    canonical_work=float(np.sum(a*ht)+np.sum(p*vt))*g.dx**2
    physical_work=float(np.sum(eh*ht)+np.sum(v*pt))*g.dx**2
    if not np.isfinite(pt).all() or not np.isfinite(physical_work):
        raise ValueError('Physical rate exceeds storage range')
    return dict(momentum=p,momentum_rate=pt,physical_depth_energy_gradient=eh,
        physical_momentum_energy_gradient=v.copy(),energy=response['total'],
        canonical_energy_rate=canonical_work,physical_energy_rate=physical_work,
        energy_coordinate_error=abs(physical_work-canonical_work),poles=poles,
        primal_pressure_residuals=[p['relative_residual'] for p in response['poles']],
        conserved_transport_or_gameplay_accepted=False)
