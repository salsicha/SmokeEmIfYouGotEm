"""Equivalent positive physical-energy realization of the SAME two-pole metric.

For Q=W.T*W+.75*V.T*V, original S=cI+sum(w_j*(I+lambda_j Q)^-1).
Partial fractions give K=S^-1=k0 I+sum(alpha_j Q*(I+beta_j Q)^-1).
Both alpha/beta are positive. These are inverse-metric factors, NOT a different
dispersion model or newly fitted poles. Parameters derive from the original
represented constants, including their small zero-frequency roundoff.

At physical momentum p, q=p/sqrt(h), z_j=(I+beta_j Q)^-1 q:
Ekin=.5*k0*|q|²+.5*sum(alpha_j*(|Wz_j|²+.75|Vz_j|²+beta_j|Qz_j|²)).
This positive local auxiliary representation avoids a dense/global inverse S.
It is an energy primitive, NOT an energy-conserving time/flux/river solver.
"""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import numpy as np
from finite_depth_pressure_reference import LENGTHS,WEIGHTS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from patch_pressure_preconditioner import PatchPressureSystem
from rational_dual_energy_reference import factor_direction
from reverse_rational_depth_gradient import factor_depth_gradient
from smooth_pressure_geometry import SmoothPressureGeometry
from smooth_pressure_reverse import smooth_coefficient_reverse


def inverse_parameters():
    l1,l2=map(lambda x:F(float(x)),LENGTHS);w1,w2=map(lambda x:F(float(x)),WEIGHTS)
    c=F(1-float(np.sum(WEIGHTS)));s0=c+w1+w2
    n1=c*(l1+l2)+w1*l2+w2*l1;n2=c*l1*l2
    with localcontext() as ctx:
        ctx.prec=80
        decimal=lambda f:D(f.numerator)/D(f.denominator)
        a=decimal(n1/s0);b=decimal(n2/s0);k0=decimal(1/s0)
        discriminant=a*a-4*b
        if discriminant<=0:raise ValueError('Original response lacks distinct real inverse factors')
        beta1=(a+discriminant.sqrt())/2;beta2=b/beta1
        t1=decimal((l1+l2)/s0-n1/(s0*s0));t2=decimal(l1*l2/s0-n2/(s0*s0))
        alpha1=(t1*beta1-t2)/(beta1-beta2);alpha2=(t2-t1*beta2)/(beta1-beta2)
        if min(k0,beta1,beta2,alpha1,alpha2)<=0:raise ValueError('Nonpositive inverse energy factor')
        return float(k0),(float(beta1),float(beta2)),(float(alpha1),float(alpha2)),str(s0)


K0,BETAS,ALPHAS,ZERO_RESPONSE_EXACT=inverse_parameters()


def evaluate(geometry,physical_momentum,*,tangent=None,preconditioner='patch'):
    g=geometry;h=g.h;p=np.asarray(physical_momentum,dtype=float)
    if (not g.periodic or np.any(h<=0) or p.shape!=(*h.shape,2) or not np.isfinite(p).all()):
        raise ValueError('Positive finite periodic primal energy required')
    if tangent is not None and (tangent.geometry is not g or tangent.one_sided):
        raise ValueError('Matching stationary positive energy tangent required')
    if preconditioner not in ('block','patch','spectral-flat'):raise ValueError('Unknown primal energy preconditioner')
    system_type=PatchPressureSystem if preconditioner=='patch' else ReconstructedAccelerationSystem
    root=np.sqrt(h);q=p/root[...,None];mapped=K0*q;density=.5*K0*np.sum(q*q,axis=-1)
    poles=[];operator_direction=0.
    for beta,alpha in zip(BETAS,ALPHAS):
        system=system_type(g,beta);z,stats=system.solve(q,iterations=40,preconditioner=preconditioner)
        if stats['relative_residual']>2e-5:raise ValueError('Unqualified inverse energy solve')
        w,v=system.w(z),system.v(z)
        # Never use (q-z)/beta: that subtracts near-equal constant-mode values.
        qz=system.transpose_w(w)+.75*system.transpose_v(v)
        mapped+=alpha*qz
        density+=.5*alpha*(w*w+.75*v*v+beta*np.sum(qz*qz,axis=-1))
        if tangent is not None:
            wt,vt=factor_direction(g,tangent,z)
            operator_direction+=alpha*float(np.sum(w*wt+.75*v*vt))
        poles.append(dict(beta=beta,alpha=alpha,normalized_auxiliary_velocity=z,**stats))
    area=g.dx**2;potential_density=9.81*h*(.5*h+g.bed)
    kinetic=float(np.sum(density))*area;potential=float(np.sum(potential_density))*area
    contraction=.5*float(np.sum(q*mapped))*area;direction=None
    if tangent is not None:
        qt=-(tangent.mass_rate/(2*h))[...,None]*q
        normalization=float(np.sum(qt*mapped))*area
        gravity=float(np.sum(9.81*(h+g.bed)*tangent.mass_rate))*area
        direction=dict(total=normalization+operator_direction*area+gravity,
                       normalization=normalization,operator=operator_direction*area,potential=gravity)
    if not np.isfinite(mapped).all() or not np.isfinite(density).all() or np.any(density<0):
        raise ValueError('Primal energy exceeds storage range')
    return dict(total=kinetic+potential,kinetic=kinetic,potential=potential,
        kinetic_density=density,canonical_velocity=mapped/root[...,None],
        layer_velocity=p/h[...,None],depth_direction=direction,poles=poles,
        positive_energy_contraction_error=abs(kinetic-contraction),
        conserved_flux_or_dry_or_history_or_gameplay_accepted=False)


def depth_gradient(geometry,physical_momentum,response,mass_direction):
    """Direct fixed-physical-p gradient with positive inverse-factor weights."""
    if not isinstance(geometry,SmoothPressureGeometry):
        raise ValueError('Matching smooth reverse geometry required')
    g=geometry;p=np.asarray(physical_momentum,dtype=float)
    if p.shape!=(*g.h.shape,2) or not np.isfinite(p).all():raise ValueError('Invalid physical momentum')
    base=-.5*np.sum(response['canonical_velocity']*(p/g.h[...,None]),axis=-1)+9.81*(g.h+g.bed)
    terms=[(pole['normalized_auxiliary_velocity'],pole['alpha']) for pole in response['poles']]
    return factor_depth_gradient(g,mass_direction,terms,base,reverse_coefficients=smooth_coefficient_reverse)
