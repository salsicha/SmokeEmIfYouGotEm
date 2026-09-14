"""Local two-pole momentum-stress RESEARCH candidate; energy not qualified.

Positive periodic flat beds only, not a replacement for the variable-bed river.
Both poles and original reconstructed flat D are retained. Positive donor mass
transport stays separate from reversible stress; no donor-pressure transpose.
Canonical stress is a discretization of the auxiliary-field continuum stress.
Convert it to a local PHYSICAL momentum flux using the complete derivative of
p=h*v+div(B). This identity is exact for the registered flat D up to solve error.
It fixes local conservation, NOT the discrete energy/product-rule problem.
"""
import numpy as np
from rational_dual_energy_reference import evaluate
from rational_physical_momentum_rate import physical_rate
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from continuous_extremum_transport import ContinuousExtremumTransport
from rational_velocity_bracket_reference import gradient


def stress_stage_physical(g,physical_momentum):
    """Physical-state entry using the equivalent matrix-free inverse metric.

    Inputs stay untouched. The solve's momentum round-trip is checked, never
    replaced by a reset/rescale. This retains the same unqualified stress and
    energy failure; it does not enable dry/variable-bed/gameplay use.
    """
    from rational_primal_energy import evaluate as primal_energy
    p=np.asarray(physical_momentum,dtype=float)
    prepared=primal_energy(g,p)
    result=stress_stage(g,prepared['canonical_velocity'])
    error=float(abs(result['momentum']-p).max())
    if error>1e-10*max(1.,float(abs(p).max())):
        raise ValueError('Physical momentum preparation round-trip is unqualified')
    result.update(source_momentum_roundtrip_error=error,
                  prepared_canonical_velocity=prepared['canonical_velocity'],
                  prepared_physical_energy=prepared['total'])
    return result


def negative_divergence(faces,dx):
    return -sum((face-np.roll(face,1,axis))/dx for face,axis in zip(faces,(1,0)))


def stress_stage(g,canonical_velocity):
    if (not isinstance(g,SmoothPressureGeometry) or not np.all(g.bed==g.bed.flat[0])):
        raise ValueError('Flat positive periodic stress component only; bed force is not derived')
    h=g.h;v=np.asarray(canonical_velocity,dtype=float);root=np.sqrt(h)
    response=evaluate(g,v,preconditioner='patch');p=response['canonical_gradient_flux'];u=response['layer_velocity']
    transport=ContinuousExtremumTransport(h,g.bed,u,g.dx,periodic=True);ht=transport.mass_rate
    # tau_mj = h*v_m*u_j + delta_mj*(g*h²/2-sum(w*lambda*h³*d²))
    #          -sum(w*lambda*h³*d*partial_m(auxiliary_velocity_j)).
    # It reduces to h*v*u+g*h²/2-2*sum(w*lambda*h³*aux_x²) in 1-D.
    with np.errstate(over='raise',under='raise',invalid='raise'):
        stress=h[...,None,None]*v[..., :,None]*u[...,None,:]
        diagonal=.5*9.81*h*h
        for pole in response['poles']:
            auxiliary=pole['normalized_auxiliary_velocity']/root[...,None]
            d,_=g.kinematic_components(auxiliary)
            coefficient=pole['weight']*pole['length']*h*h*h*d
            diagonal-=coefficient*d
            for j in range(2):
                stress[..., :,j]-=coefficient[...,None]*gradient(auxiliary[...,j],g.dx)
        for j in range(2):stress[...,j,j]+=diagonal
        canonical_faces=[.5*(stress[..., :,j]+np.roll(stress[..., :,j],-1,axis))
                         for j,axis in enumerate((1,0))]
        mt=negative_divergence(canonical_faces,g.dx)
        vt=(mt-ht[...,None]*v)/h[...,None]
    transformed=physical_rate(g,v,ht,vt,derivative_preconditioner='patch',
                              primal_preconditioner='patch',include_auxiliary_rates=True)
    tangent=SmoothPressureGeometryRate(g,g.bed,ht);ell=ht/(2*h)
    bfaces=[np.zeros_like(h),np.zeros_like(h)];btfaces=[np.zeros_like(h),np.zeros_like(h)]
    with np.errstate(over='raise',under='raise',invalid='raise'):
        for pole in transformed['poles']:
            auxiliary=pole['normalized_auxiliary_velocity']/root[...,None]
            auxiliary_t=pole['normalized_auxiliary_rate']/root[...,None]-ell[...,None]*auxiliary
            d,_=g.kinematic_components(auxiliary);dt,_=tangent.kinematic_rate(auxiliary)
            rate,_=g.kinematic_components(auxiliary_t);dt+=rate
            c=h*h*h*d;ct=3*h*h*ht*d+h*h*h*dt;scale=pole['weight']*pole['length']
            for j,(axis,edge,erate) in enumerate(zip((1,0),g.edges,tangent.edges)):
                bfaces[j]+=scale*(edge['other']*c+edge['own']*np.roll(c,-1,axis))
                btfaces[j]+=scale*(erate['other']*c+erate['own']*np.roll(c,-1,axis)
                    +edge['other']*ct+edge['own']*np.roll(ct,-1,axis))
        faces=[face.copy() for face in canonical_faces]
        for j in range(2):faces[j][...,j]-=btfaces[j]
        flux_rate=negative_divergence(faces,g.dx)
        identity=h[...,None]*v+np.stack([(b-np.roll(b,1,axis))/g.dx
                                       for b,axis in zip(bfaces,(1,0))],axis=-1)
    # Each momentum component has its own diagonal B divergence correction.
    identity_error=float(abs(identity-p).max())
    flux_error=float(abs(flux_rate-transformed['momentum_rate']).max())
    if not np.isfinite(flux_rate).all():raise ValueError('Stress flux exceeds storage range')
    # Diagnostic split only: actual ht remains the positive donor rate.
    # At fixed canonical momentum m=h*v, the energy depth derivative is
    # chi=H_h-u.v, and the conjugate momentum velocity is u. This is distinct
    # from the physical-(h,p) Legendre derivatives returned by the bridge.
    chi=2*9.81*(h+g.bed)-transformed['physical_depth_energy_gradient']-np.sum(u*v,axis=-1)
    central_ht=negative_divergence([.5*(p[...,j]+np.roll(p[...,j],-1,axis))
                                    for j,axis in enumerate((1,0))],g.dx)
    centered_work=float(np.sum(chi*central_ht)+np.sum(u*mt))*g.dx**2
    donor_work=float(np.sum(chi*(ht-central_ht)))*g.dx**2
    return dict(depth_rate=ht,canonical_velocity_rate=vt,momentum=p,
        physical_momentum_rate=transformed['momentum_rate'],physical_momentum_fluxes=faces,
        physical_momentum_flux_rate=flux_rate,auxiliary_momentum_identity_error=identity_error,
        local_momentum_flux_error=flux_error,energy_rate=transformed['physical_energy_rate'],
        energy_coordinate_error=transformed['energy_coordinate_error'],
        centered_mass_control_energy_rate=centered_work,donor_incremental_energy_rate=donor_work,
        energy_work_split_error=abs(centered_work+donor_work-transformed['physical_energy_rate']),
        mass_only_forward_euler_bound=transport.draining_bound,
        poles=[dict(length=entry['length'],weight=entry['weight'],relative_residual=entry['relative_residual'])
               for entry in transformed['poles']],
        energy_or_variable_bed_or_dry_or_history_or_gameplay_accepted=False)
