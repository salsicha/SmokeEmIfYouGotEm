"""1-D positive periodic two-pole metric-transport RESEARCH stage.

Same physical kinetic metric/poles/factor derivatives/40-CG solves. Half the
time derivative of the extra metric supplies its changing-depth work. A skew
transport of both stationary auxiliary energy modes does no net energy work.
Conservation alone is NOT continuum-model, dry, time-history or gameplay proof.
"""
import numpy as np
from rational_primal_energy import K0, evaluate, depth_gradient
from rational_dual_energy_reference import evaluate as dual, factor_direction
from rational_physical_momentum_rate import factor_transpose_direction
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from patch_pressure_preconditioner import PatchPressureSystem


def stage(g, physical_momentum):
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
        # Both B=a*D+D*a are skew for the unchanged centered periodic D.
        a = h*h*h*u
        gradient_rhs = transpose_dh(.5*(a*D(strain)+D(a*strain)))
        gradient_pullback = h*solve_l(gradient_rhs)
        a = h*u
        difference_rhs = .5*(a*D(difference)+D(a*difference))/beta
        difference_pullback = difference_rhs-h*solve_l(difference_rhs)
        skew_force += alpha*(gradient_pullback+difference_pullback)

    metric_time_force = ell*au+root*mapped_t[..., component]-K0*ht*u
    rhs = base_rhs+.5*metric_time_force+skew_force
    # A^-1 = h^-1/2 S h^-1/2 uses the ORIGINAL two-pole response.
    acceleration = dual(g, vector(-rhs/h), preconditioner='patch')
    ut = acceleration['layer_velocity'][..., component]
    pt = vector(h*ut+ht*u)
    residuals.extend(pole['relative_residual'] for pole in acceleration['poles'])
    if max(residuals) > 2e-5:
        raise ValueError('Unqualified pressure/auxiliary solve')
    eh, _ = depth_gradient(g, p, response, ht)
    energy_rate = float(np.sum(eh*ht)+np.sum(response['canonical_velocity']*pt))*g.dx**2
    if not np.isfinite(pt).all() or not np.isfinite(energy_rate):
        raise ValueError('Metric transport exceeds represented physical range')
    return dict(depth_rate=ht, physical_momentum_rate=pt, physical_acceleration=vector(ut),
        energy_rate=energy_rate, total_momentum_rate=pt.sum(axis=(0, 1))*g.dx**2,
        net_mass_rate=float(ht.sum())*g.dx**2,
        skew_energy_work=float(np.sum(u*skew_force))*g.dx**2,
        maximum_solve_residual=max(residuals),
        nonlinear_model_or_local_flux_or_dry_or_history_or_gameplay_accepted=False)
