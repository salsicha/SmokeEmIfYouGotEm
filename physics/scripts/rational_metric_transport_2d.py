"""Flat positive periodic TWO-DIMENSIONAL metric transport, research only.

Both physical velocity components and both original rational poles are retained.
The cross-mode operator includes the transposed velocity gradient, not merely a
copy of the 1-D divergence term. No terrain/dry/time/native acceptance is implied.
"""
import numpy as np

from rational_dual_energy_reference import evaluate as dual, factor_direction
from rational_primal_energy import K0, evaluate, depth_gradient
from rational_physical_momentum_rate import factor_transpose_direction
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from patch_pressure_preconditioner import PatchPressureSystem
from reconstructed_acceleration_system import ReconstructedAccelerationSystem


def stage(g, physical_momentum, *, tensor_coupling='full', preconditioner='spectral-flat'):
    if tensor_coupling not in ('full', 'longitudinal-only'):
        raise ValueError('Unknown tensor coupling')
    if not isinstance(g, SmoothPressureGeometry) or not np.all(g.bed == g.bed.flat[0]):
        raise ValueError('Flat positive periodic geometry required')
    h = g.h
    p = np.asarray(physical_momentum, float)
    if p.shape != (*h.shape, 2) or not np.isfinite(p).all():
        raise ValueError('Finite two-component physical momentum required')
    root = np.sqrt(h)
    u = p/h[..., None]
    central = lambda f, axis: (np.roll(f, -1, axis)-np.roll(f, 1, axis))/(2*g.dx)
    divergence = lambda faces: sum((f-np.roll(f, 1, axis))/g.dx for f, axis in zip(faces, (1, 0)))
    def face(c, j):
        edge = g.edges[j]; axis = 1-j
        return edge['other']*c+edge['own']*np.roll(c, -1, axis)
    def derivative(f, j):
        edge = g.edges[j]; axis = 1-j
        return (edge['other']*(np.roll(f, -1, axis)-f)
                +np.roll(edge['own'], 1, axis)*(f-np.roll(f, 1, axis)))/g.dx
    def skew_advection(a, f):
        if f.ndim == 3:
            return sum(.5*(a[..., j, None]*central(f, axis)
                +central(a[..., j, None]*f, axis)) for j, axis in enumerate((1, 0)))
        return sum(.5*(a[..., j]*central(f, axis)+central(a[..., j]*f, axis))
                   for j, axis in enumerate((1, 0)))
    def tensor_action(c, velocity):
        """Symmetric N=div[c((div z)I+(grad z)^T)], with paired adjoints.

        N annihilates constant vectors and is self-adjoint even for signed c.
        The alternate 2*grad(c*div) control is the tempting but incomplete
        extension of the 1-D expression; it must not qualify as full 2-D flow.
        """
        jac = np.stack([np.stack([derivative(velocity[..., i], j) for j in range(2)], axis=-1)
                        for i in range(2)], axis=-2)
        trace = jac[..., 0, 0]+jac[..., 1, 1]
        faces = []
        for j in range(2):
            values = []
            for i in range(2):
                strain = jac[..., j, i]+(trace if i == j else 0.)
                if tensor_coupling == 'longitudinal-only':
                    strain = 2*trace if i == j else np.zeros_like(trace)
                values.append(face(c*strain, j))
            faces.append(np.stack(values, axis=-1))
        return divergence(faces), faces

    if preconditioner not in ('patch', 'spectral-flat'):
        raise ValueError('Unknown two-dimensional pressure preconditioner')
    system_type = PatchPressureSystem if preconditioner == 'patch' else ReconstructedAccelerationSystem
    response = evaluate(g, p, preconditioner=preconditioner)
    au = h[..., None]*response['canonical_velocity']
    means = [.5*(u+np.roll(u, -1, axis)) for axis in (1, 0)]
    mass_faces = [.5*(h+np.roll(h, -1, axis))*means[j][..., j]
                  for j, axis in enumerate((1, 0))]
    ht = -divergence(mass_faces)
    base_faces = [K0*mass_faces[j][..., None]*means[j] for j in range(2)]
    for j, axis in enumerate((1, 0)):
        base_faces[j][..., j] += .25*9.81*(h*h+np.roll(h*h, -1, axis))
    base_rhs = divergence(base_faces)+K0*u*ht[..., None]
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    ell = ht/(2*h)
    q = root[..., None]*u
    qt = ell[..., None]*q
    mapped_t = K0*qt
    skew_force = np.zeros_like(p)
    skew_faces = [np.zeros_like(p), np.zeros_like(p)]
    metric_time_faces = [np.zeros_like(p), np.zeros_like(p)]
    residuals = []
    derivative_error = 0.
    for pole in response['poles']:
        beta, alpha = pole['beta'], pole['alpha']
        system = system_type(g, beta)
        z = pole['normalized_auxiliary_velocity']
        wz, vz = system.w(z), system.v(z)
        wt, bt = factor_direction(g, tangent, z)
        qtz = (factor_transpose_direction(system, tangent, wz)+system.transpose_w(wt)
            +.75*(factor_transpose_direction(system, tangent, vz, bottom=True)+system.transpose_v(bt)))
        zt, stats = system.solve(qt-beta*qtz, iterations=40, preconditioner=preconditioner)
        residuals.extend((pole['relative_residual'], stats['relative_residual']))
        mapped_t += alpha*(qtz+system.transpose_w(system.w(zt))+.75*system.transpose_v(system.v(zt)))
        def solve_l(rhs):
            solution, info = system.solve(rhs/root[..., None], iterations=40, preconditioner=preconditioner)
            residuals.append(info['relative_residual'])
            return solution/root[..., None]
        dh = lambda velocity: system.w(root[..., None]*velocity)/(h*root)
        dh_transpose = lambda scalar: root[..., None]*system.transpose_w(scalar/(h*root))
        auxiliary = z/root[..., None]
        strain = wz/(h*root)
        difference = u-auxiliary
        derivative_error = max(derivative_error, float(np.max(abs(strain
            -sum(derivative(auxiliary[..., j], j) for j in range(2))))))
        auxiliary_t = zt/root[..., None]-ell[..., None]*auxiliary
        strain_t = tangent.kinematic_rate(auxiliary)[0]+g.kinematic_components(auxiliary_t)[0]
        c = h*h*h*strain
        ct = 3*h*h*ht*strain+h*h*h*strain_t
        for j, axis in enumerate((1, 0)):
            erate = tangent.edges[j]
            metric_time_faces[j][..., j] += alpha*(erate['other']*c
                +erate['own']*np.roll(c, -1, axis)+face(ct, j))
        middle = skew_advection(h[..., None]**3*u, strain)
        gradient_rhs = dh_transpose(middle)
        gradient_solution = solve_l(gradient_rhs)
        gradient_pullback = h[..., None]*gradient_solution
        difference_rhs = skew_advection(h[..., None]*u, difference)/beta
        difference_solution = solve_l(difference_rhs)
        difference_pullback = difference_rhs-h[..., None]*difference_solution
        skew_force += alpha*(gradient_pullback+difference_pullback)
        for j in range(2):
            skew_faces[j][..., j] += alpha*(face(middle, j)
                -beta*face(h**3*dh(gradient_solution), j)+beta*face(h**3*dh(difference_solution), j))

        # S_cross = alpha*(T^T N - N T), the full tensor counterpart of
        # 2*alpha*(M T-T^T M). N is symmetric, making this exactly skew.
        n_u, _ = tensor_action(c, u)
        n_w, _ = tensor_action(c, auxiliary)
        _, n_difference_faces = tensor_action(c, difference)
        cross_solution = solve_l(n_u)
        skew_force += alpha*(h[..., None]*cross_solution-n_w)
        for j in range(2):
            skew_faces[j] -= alpha*n_difference_faces[j]
            skew_faces[j][..., j] -= alpha*beta*face(h**3*dh(cross_solution), j)

    metric_time_force = ell[..., None]*au+root[..., None]*mapped_t-K0*ht[..., None]*u
    rhs = base_rhs+.5*metric_time_force+skew_force
    acceleration = dual(g, -rhs/h[..., None], preconditioner=preconditioner)
    ut = acceleration['layer_velocity']
    pt = h[..., None]*ut+ht[..., None]*u
    residuals.extend(pole['relative_residual'] for pole in acceleration['poles'])
    acceleration_metric = evaluate(g, h[..., None]*ut, preconditioner=preconditioner)
    acceleration_faces = [np.zeros_like(p), np.zeros_like(p)]
    for pole in acceleration_metric['poles']:
        aux = pole['normalized_auxiliary_velocity']/root[..., None]
        c = h**3*g.kinematic_components(aux)[0]
        for j in range(2):
            acceleration_faces[j][..., j] += pole['alpha']*face(c, j)
        residuals.append(pole['relative_residual'])
    momentum_faces = [(base_faces[j]-acceleration_faces[j]-.5*metric_time_faces[j]-skew_faces[j])/K0
                      for j in range(2)]
    flux_rate = -divergence(momentum_faces)
    if max(residuals) > 2e-5:
        raise ValueError('Unqualified pressure/auxiliary solve')
    eh, _ = depth_gradient(g, p, response, ht)
    energy_rate = float(np.sum(eh*ht)+np.sum(response['canonical_velocity']*pt))*g.dx**2
    if not all(np.isfinite(v).all() for v in (pt, flux_rate, energy_rate)):
        raise ValueError('Two-dimensional metric transport exceeds represented range')
    return dict(tensor_coupling=tensor_coupling, preconditioner=preconditioner,
        depth_rate=ht, physical_momentum_rate=pt,
        physical_acceleration=ut, physical_momentum_faces=momentum_faces,
        local_momentum_flux_error=float(np.max(abs(flux_rate-pt))),
        metric_time_flux_error=float(np.max(abs(metric_time_force+divergence(metric_time_faces)))),
        skew_flux_error=float(np.max(abs(skew_force+divergence(skew_faces)))),
        reconstructed_derivative_error=derivative_error,
        energy_rate=energy_rate, net_mass_rate=float(ht.sum())*g.dx**2,
        total_momentum_rate=pt.sum(axis=(0, 1))*g.dx**2,
        skew_energy_work=float(np.sum(u*skew_force))*g.dx**2,
        maximum_solve_residual=max(residuals),
        nonlinear_model_or_terrain_or_dry_or_history_or_gameplay_accepted=False)
