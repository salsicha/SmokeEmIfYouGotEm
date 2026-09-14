"""1-D positive periodic two-pole metric-transport RESEARCH stage.

Same physical kinetic metric/poles/factor derivatives/40-CG solves. Half the
time derivative of the extra metric supplies its changing-depth work. A skew
transport of both stationary auxiliary energy modes does no net energy work.
The modes also need their variational cross-coupling; transporting them
independently conserves totals but changes the nonlinear continuum model.
Conservation alone is NOT continuum-model, dry, time-history or gameplay proof.
"""
import numpy as np
from rational_primal_energy import K0, evaluate, depth_gradient
from rational_dual_energy_reference import evaluate as dual, factor_direction
from rational_physical_momentum_rate import factor_transpose_direction
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from patch_pressure_preconditioner import PatchPressureSystem


def stage(g, physical_momentum, *, auxiliary_transport='coupled-modes'):
    if auxiliary_transport not in ('coupled-modes', 'independent-modes'):
        raise ValueError('Unknown auxiliary transport coupling')
    if (not isinstance(g, SmoothPressureGeometry) or min(g.h.shape) != 1 or
            max(g.h.shape) < 3 or not np.all(g.bed == g.bed.flat[0])):
        raise ValueError('Flat, positive, genuinely one-dimensional periodic geometry required')
    h = g.h
    axis = 1 if h.shape[0] == 1 else 0
    component = 1-axis
    p = np.asarray(physical_momentum, float)
    if p.shape != (*h.shape, 2) or not np.isfinite(p).all() or np.any(p[..., axis] != 0):
        raise ValueError('Finite longitudinal physical momentum required; transverse model is not derived')
    u = p[..., component]/h
    root = np.sqrt(h)
    D = lambda f: (np.roll(f, -1, axis)-np.roll(f, 1, axis))/(2*g.dx)
    div = lambda f: (f-np.roll(f, 1, axis))/g.dx
    vector = lambda f: np.stack((f, np.zeros_like(f)) if component == 0 else (np.zeros_like(f), f), axis=-1)
    response = evaluate(g, p)
    au = h*response['canonical_velocity'][..., component]
    hf = .5*(h+np.roll(h, -1, axis))
    uf = .5*(u+np.roll(u, -1, axis))
    mass_face = hf*uf
    ht = -div(mass_face)
    base_face = K0*mass_face*uf+.25*9.81*(h*h+np.roll(h*h, -1, axis))
    base_rhs = div(base_face)+K0*u*ht
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    q = vector(root*u)
    ell = ht/(2*h)
    qt = ell[..., None]*q  # Fixed physical u, changing normalization.
    mapped_t = K0*qt
    skew_force = np.zeros_like(h)
    skew_face = np.zeros_like(h)
    metric_time_face = np.zeros_like(h)
    edge = g.edges[component]
    edge_rate = tangent.edges[component]
    # D_h^T c = -div(face(c)) for this original flat reconstruction.
    face = lambda c: edge['other']*c+edge['own']*np.roll(c, -1, axis)
    residuals = []
    for pole in response['poles']:
        beta, alpha = pole['beta'], pole['alpha']
        system = PatchPressureSystem(g, beta)
        z = pole['normalized_auxiliary_velocity']
        w, bottom = system.w(z), system.v(z)
        wt, bt = factor_direction(g, tangent, z)
        qtz = (factor_transpose_direction(system, tangent, w)+system.transpose_w(wt)
               +.75*(factor_transpose_direction(system, tangent, bottom, bottom=True)+system.transpose_v(bt)))
        zt, stats = system.solve(qt-beta*qtz, iterations=40, preconditioner='patch')
        residuals.extend((pole['relative_residual'], stats['relative_residual']))
        mapped_t += alpha*(qtz+system.transpose_w(system.w(zt))+.75*system.transpose_v(system.v(zt)))

        # L=h+beta*G, G=D_h^T h^3 D_h, T=L^-1 h. The original normalized
        # pressure system supplies these exact operators without dense matrices.
        def solve_l(rhs):
            solution, info = system.solve(vector(rhs/root), iterations=40, preconditioner='patch')
            residuals.append(info['relative_residual'])
            return solution[..., component]/root

        def transpose_dh(scalar):
            return root*system.transpose_w(scalar/(h*root))[..., component]

        auxiliary = z[..., component]/root
        strain = w/(h*root)
        difference = u-auxiliary
        auxiliary_t = zt/root[..., None]-ell[..., None]*(z/root[..., None])
        strain_t = tangent.kinematic_rate(z/root[..., None])[0]+g.kinematic_components(auxiliary_t)[0]
        c = h*h*h*strain
        ct = 3*h*h*ht*strain+h*h*h*strain_t
        metric_time_face += alpha*(edge_rate['other']*c+edge_rate['own']*np.roll(c, -1, axis)+face(ct))
        strain_of = lambda scalar: system.w(vector(root*scalar))/(h*root)
        # Both B=a*D+D*a are skew for the unchanged centered periodic D.
        a = h*h*h*u
        gradient_middle = .5*(a*D(strain)+D(a*strain))
        gradient_rhs = transpose_dh(gradient_middle)
        gradient_solution = solve_l(gradient_rhs)
        gradient_pullback = h*gradient_solution
        a = h*u
        difference_rhs = .5*(a*D(difference)+D(a*difference))/beta
        difference_solution = solve_l(difference_rhs)
        difference_pullback = difference_rhs-h*difference_solution
        skew_force += alpha*(gradient_pullback+difference_pullback)
        # T^T*y = y-beta*G*L^-1*y and R^T*y=beta*G*L^-1*y
        # hold up to each measured solve residual. Do not reset either force
        # to its flux form: independent local residuals remain visible below.
        skew_face += alpha*(face(gradient_middle)
            -beta*face(h*h*h*strain_of(gradient_solution))
            +beta*face(h*h*h*strain_of(difference_solution)))
        if auxiliary_transport == 'coupled-modes':
            # c=h^3*D_h(w), M=D_h^T*c*D_h is symmetric. The missing
            # variational coupling is 2*alpha*(M*T-T^T*M)*u, hence skew.
            # In the continuum it equals
            # 2*alpha*[T^T*d_x(c*r_x)-R^T*d_x(c*w_x)], R=I-T.
            # It vanishes in the SGN T=I limit, but not for rational poles.
            # No energy projection, changed pole, or finite-difference tangent.
            metric_w = transpose_dh(c*strain)
            strain_u = strain_of(u)
            metric_u = transpose_dh(c*strain_u)
            cross_solution = solve_l(metric_u)
            skew_force += 2*alpha*(metric_w-h*cross_solution)
            skew_face += 2*alpha*(face(c*(strain-strain_u))
                +beta*face(h*h*h*strain_of(cross_solution)))

    metric_time_force = ell*au+root*mapped_t[..., component]-K0*ht*u
    rhs = base_rhs+.5*metric_time_force+skew_force
    # A^-1 = h^-1/2 S h^-1/2 uses the ORIGINAL two-pole response.
    acceleration = dual(g, vector(-rhs/h), preconditioner='patch')
    ut = acceleration['layer_velocity'][..., component]
    pt = vector(h*ut+ht*u)
    residuals.extend(pole['relative_residual'] for pole in acceleration['poles'])
    acceleration_metric = evaluate(g, vector(h*ut))
    acceleration_face = np.zeros_like(h)
    for pole in acceleration_metric['poles']:
        aux = pole['normalized_auxiliary_velocity']/root[..., None]
        acceleration_face += pole['alpha']*face(h*h*h*g.kinematic_components(aux)[0])
        residuals.append(pole['relative_residual'])
    momentum_face = vector((base_face-acceleration_face-.5*metric_time_face-skew_face)/K0)
    flux_rate = -(momentum_face-np.roll(momentum_face, 1, axis))/g.dx
    local_flux_error = float(np.max(abs(flux_rate-pt)))
    metric_time_flux_error = float(np.max(abs(metric_time_force+div(metric_time_face))))
    skew_flux_error = float(np.max(abs(skew_force+div(skew_face))))
    if max(residuals) > 2e-5:
        raise ValueError('Unqualified pressure/auxiliary solve')
    eh, _ = depth_gradient(g, p, response, ht)
    energy_rate = float(np.sum(eh*ht)+np.sum(response['canonical_velocity']*pt))*g.dx**2
    if not np.isfinite(pt).all() or not np.isfinite(energy_rate):
        raise ValueError('Metric transport exceeds represented physical range')
    return dict(auxiliary_transport=auxiliary_transport,
        depth_rate=ht, physical_momentum_rate=pt, physical_acceleration=vector(ut),
        energy_rate=energy_rate, total_momentum_rate=pt.sum(axis=(0, 1))*g.dx**2,
        net_mass_rate=float(ht.sum())*g.dx**2,
        skew_energy_work=float(np.sum(u*skew_force))*g.dx**2,
        physical_momentum_face=momentum_face, physical_momentum_flux_rate=flux_rate,
        local_momentum_flux_error=local_flux_error,
        metric_time_flux_error=metric_time_flux_error, skew_flux_error=skew_flux_error,
        maximum_solve_residual=max(residuals),
        nonlinear_model_or_local_flux_or_dry_or_history_or_gameplay_accepted=False)
