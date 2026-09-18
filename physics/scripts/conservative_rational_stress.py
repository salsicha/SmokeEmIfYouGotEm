"""Flat-periodic two-pole research entry with coupled metric transport by default.

Positive periodic flat beds only, not a replacement for the variable-bed river.
Both poles and original reconstructed flat D are retained. Failed legacy donor
stress and paired-base stress remain explicit negative controls; no donor-pressure
transpose or global energy correction is applied.
Canonical stress is a discretization of the auxiliary-field continuum stress.
Convert it to a local PHYSICAL momentum flux using the complete derivative of
p=h*v+div(B). This identity is exact for the registered flat D up to solve error.
Those legacy controls fix local conservation, NOT the energy/product-rule
problem. The default uses the derived full-tensor metric transport instead.
No terrain/wetting/finite-time/native/gameplay acceptance is implied.
"""
import numpy as np
from rational_dual_energy_reference import evaluate
from rational_physical_momentum_rate import physical_rate
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from continuous_extremum_transport import ContinuousExtremumTransport
from rational_velocity_bracket_reference import gradient


def stress_stage_physical(g,physical_momentum,*,flux_scheme='metric-transport',preconditioner='patch'):
    """Physical-state entry using the equivalent matrix-free inverse metric.

    Inputs stay untouched. The solve's momentum round-trip is checked, never
    replaced by a reset/rescale. Failed stress variants require explicit
    selection; none of these research modes enables dry/variable-bed/gameplay use.
    """
    from rational_primal_energy import evaluate as primal_energy
    p=np.asarray(physical_momentum,dtype=float)
    if flux_scheme == 'metric-transport':
        return _coupled_stage(g, p, preconditioner)
    prepared=primal_energy(g,p,preconditioner=preconditioner)
    result=stress_stage(g,prepared['canonical_velocity'],flux_scheme=flux_scheme,preconditioner=preconditioner)
    error=float(abs(result['momentum']-p).max())
    if error>1e-10*max(1.,float(abs(p).max())):
        raise ValueError('Physical momentum preparation round-trip is unqualified')
    result.update(source_momentum_roundtrip_error=error,
                  prepared_canonical_velocity=prepared['canonical_velocity'],
                  prepared_physical_energy=prepared['total'])
    return result


def negative_divergence(faces,dx):
    return -sum((face-np.roll(face,1,axis))/dx for face,axis in zip(faces,(1,0)))


def _coupled_stage(g, p, preconditioner):
    from rational_metric_transport_2d import stage
    from rational_physical_momentum_rate import canonical_rate
    from rational_primal_energy import evaluate as primal_energy
    r = stage(g, p, preconditioner=preconditioner)
    ht, pt = r['depth_rate'], r['physical_momentum_rate']
    inverse = canonical_rate(g, p, ht, pt, preconditioner=preconditioner)
    v, vt = inverse['canonical_velocity'], inverse['canonical_velocity_rate']
    # Independent forward derivative verifies the physical/canonical API
    # bridge. Neither rate is overwritten with the other's reconstruction.
    forward = physical_rate(g, v, ht, vt, derivative_preconditioner=preconditioner,
                            primal_preconditioner=preconditioner)
    roundtrip = float(np.max(abs(forward['momentum']-p)))
    rate_roundtrip = float(np.max(abs(forward['momentum_rate']-pt)))
    work_error = abs(forward['physical_energy_rate']-r['energy_rate'])
    local = float(np.max(abs(negative_divergence(r['physical_momentum_faces'], g.dx)-pt)))
    h, u = g.h, p/g.h[..., None]
    chi = 2*9.81*(h+g.bed)-forward['physical_depth_energy_gradient']-np.sum(u*v, axis=-1)
    central_ht = negative_divergence([.5*(p[..., j]+np.roll(p[..., j], -1, axis))
                                     for j, axis in enumerate((1, 0))], g.dx)
    canonical_mt = h[..., None]*vt+ht[..., None]*v
    centered_work = float(np.sum(chi*central_ht)+np.sum(u*canonical_mt))*g.dx**2
    incremental_work = float(np.sum(chi*(ht-central_ht)))*g.dx**2
    split_error = abs(centered_work+incremental_work-r['energy_rate'])
    gates = (abs(r['energy_rate']), abs(r['net_mass_rate']), float(np.max(abs(r['total_momentum_rate']))),
             r['local_momentum_flux_error'], r['metric_time_flux_error'], r['skew_flux_error'],
             local, rate_roundtrip, work_error, split_error, forward['energy_coordinate_error'])
    if roundtrip > 1e-10*max(1., float(np.max(abs(p)))) or max(gates) > 1e-10:
        raise ValueError('Coupled flat-periodic conservation or coordinate gate failed')
    mass_faces = [.5*(h+np.roll(h, -1, axis))*.5*(u[..., j]+np.roll(u[..., j], -1, axis))
                  for j, axis in enumerate((1, 0))]
    outgoing = sum((np.maximum(f, 0)+np.maximum(-np.roll(f, 1, axis), 0))/g.dx
                   for f, axis in zip(mass_faces, (1, 0)))
    donating = outgoing > 0
    bound = float(np.min(h[donating]/outgoing[donating])) if donating.any() else np.inf
    prepared = primal_energy(g, p, preconditioner=preconditioner)
    return dict(**r, flux_scheme='metric-transport', canonical_velocity_rate=vt, momentum=p.copy(),
        physical_momentum_fluxes=r['physical_momentum_faces'], physical_momentum_flux_rate=negative_divergence(r['physical_momentum_faces'], g.dx),
        auxiliary_momentum_identity_error=roundtrip, source_momentum_roundtrip_error=roundtrip,
        physical_rate_roundtrip_error=rate_roundtrip, energy_coordinate_error=forward['energy_coordinate_error'],
        energy_work_split_error=split_error, mass_only_forward_euler_bound=bound,
        centered_mass_control_energy_rate=centered_work, mass_scheme_incremental_energy_rate=incremental_work,
        prepared_canonical_velocity=v, prepared_physical_energy=prepared['total'],
        poles=forward['poles'], incremental_work_is_donor=False,
        donor_incremental_energy_rate=None,
        energy_or_variable_bed_or_dry_or_history_or_gameplay_accepted=False)


def stress_stage(g,canonical_velocity,*,flux_scheme='metric-transport',preconditioner='patch'):
    if (not isinstance(g,SmoothPressureGeometry) or not np.all(g.bed==g.bed.flat[0])):
        raise ValueError('Flat positive periodic stress component only; bed force is not derived')
    if flux_scheme == 'metric-transport':
        response = evaluate(g, canonical_velocity, preconditioner=preconditioner)
        return _coupled_stage(g, response['canonical_gradient_flux'], preconditioner)
    if flux_scheme not in ('donor-stress','paired-base'):
        raise ValueError('Unknown conservative stress flux scheme')
    h=g.h;v=np.asarray(canonical_velocity,dtype=float);root=np.sqrt(h)
    response=evaluate(g,v,preconditioner=preconditioner);p=response['canonical_gradient_flux'];u=response['layer_velocity']
    if flux_scheme=='donor-stress':
        transport=ContinuousExtremumTransport(h,g.bed,u,g.dx,periodic=True)
        ht=transport.mass_rate;mass_bound=transport.draining_bound
    else:
        # Flat-face specialization of the exact-terrain pressure secant: A*=mean(h).
        # Pair this SAME mass flux with mean canonical velocity in advection.
        # No auxiliary pressure, factor, pole or physical/canonical map changes.
        mass_faces=[.5*(h+np.roll(h,-1,axis))*.5*(u[...,j]+np.roll(u[...,j],-1,axis))
                    for j,axis in enumerate((1,0))]
        ht=negative_divergence(mass_faces,g.dx)
        outgoing=sum((np.maximum(face,0)+np.maximum(-np.roll(face,1,axis),0))/g.dx
                     for face,axis in zip(mass_faces,(1,0)))
        donating=outgoing>0
        mass_bound=float(np.min(h[donating]/outgoing[donating])) if donating.any() else np.inf
    # tau_mj = h*v_m*u_j + delta_mj*(g*h²/2-sum(w*lambda*h³*d²))
    #          -sum(w*lambda*h³*d*partial_m(auxiliary_velocity_j)).
    # It reduces to h*v*u+g*h²/2-2*sum(w*lambda*h³*aux_x²) in 1-D.
    with np.errstate(over='raise',under='raise',invalid='raise'):
        advection=h[...,None,None]*v[..., :,None]*u[...,None,:]
        stress=advection.copy() if flux_scheme=='donor-stress' else np.zeros_like(advection)
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
        if flux_scheme=='paired-base':
            for j,axis in enumerate((1,0)):
                canonical_faces[j]+=mass_faces[j][...,None]*.5*(v+np.roll(v,-1,axis))
        mt=negative_divergence(canonical_faces,g.dx)
        vt=(mt-ht[...,None]*v)/h[...,None]
    transformed=physical_rate(g,v,ht,vt,derivative_preconditioner=preconditioner,
                              primal_preconditioner=preconditioner,include_auxiliary_rates=True)
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
    # Diagnostic split relative to centered physical mass. Only the legacy
    # branch's incremental work is specifically donor work.
    # At fixed canonical momentum m=h*v, the energy depth derivative is
    # chi=H_h-u.v, and the conjugate momentum velocity is u. This is distinct
    # from the physical-(h,p) Legendre derivatives returned by the bridge.
    chi=2*9.81*(h+g.bed)-transformed['physical_depth_energy_gradient']-np.sum(u*v,axis=-1)
    central_ht=negative_divergence([.5*(p[...,j]+np.roll(p[...,j],-1,axis))
                                    for j,axis in enumerate((1,0))],g.dx)
    centered_work=float(np.sum(chi*central_ht)+np.sum(u*mt))*g.dx**2
    donor_work=float(np.sum(chi*(ht-central_ht)))*g.dx**2
    return dict(flux_scheme=flux_scheme,depth_rate=ht,canonical_velocity_rate=vt,momentum=p,
        physical_momentum_rate=transformed['momentum_rate'],physical_momentum_fluxes=faces,
        physical_momentum_flux_rate=flux_rate,auxiliary_momentum_identity_error=identity_error,
        local_momentum_flux_error=flux_error,energy_rate=transformed['physical_energy_rate'],
        energy_coordinate_error=transformed['energy_coordinate_error'],
        centered_mass_control_energy_rate=centered_work,
        donor_incremental_energy_rate=donor_work if flux_scheme=='donor-stress' else None,
        mass_scheme_incremental_energy_rate=donor_work,
        incremental_work_is_donor=flux_scheme=='donor-stress',
        energy_work_split_error=abs(centered_work+donor_work-transformed['physical_energy_rate']),
        mass_only_forward_euler_bound=mass_bound,
        poles=[dict(length=entry['length'],weight=entry['weight'],relative_residual=entry['relative_residual'])
               for entry in transformed['poles']],
        energy_or_variable_bed_or_dry_or_history_or_gameplay_accepted=False)
