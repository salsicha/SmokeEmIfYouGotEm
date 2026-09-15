"""Nonlinear positive-periodic terrain metric candidate, NOT a native solver.

Retains the original two-pole inertia. In physical variables F=h D-1.5 B,
G=F.T h F+.75 B.T h B, T=(h+beta G)^-1 h. The per-pole skew
coupling includes T.T N-N T and the geometric commutator J. Energy skewness
alone does not establish the nonlinear model or a physical bed-force ledger.
"""
import numpy as np

from patch_pressure_preconditioner import PatchPressureSystem
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from rational_dual_energy_reference import evaluate as dual, factor_direction
from rational_physical_momentum_rate import factor_transpose_direction
from rational_primal_energy import K0, evaluate, depth_gradient
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
import terrain_metric_force_ledger as ledger


def central(value, j, dx):
    axis = 1-j
    return (np.roll(value, -1, axis)-np.roll(value, 1, axis))/(2*dx)


def skew_advection(flux, value, dx):
    return sum(.5*(flux[..., j, None]*central(value, j, dx)
                     +central(flux[..., j, None]*value, j, dx))
               if value.ndim == 3 else
               .5*(flux[..., j]*central(value, j, dx)
                     +central(flux[..., j]*value, j, dx)) for j in range(2))


def tensor_action(g, c, s, value, *, include_hessian=True):
    """Self-adjoint div[c((div z) I+(grad z).T)]+s Hess(b) z.

    Central derivatives use their exact negative transposes, including both
    off-diagonal terms. This is a consistent tensor stencil, not a claim of
    exact equality with the old depth-weighted flat discrete stencil.
    """
    jac = [[central(value[..., i], j, g.dx) for j in range(2)] for i in range(2)]
    trace = jac[0][0]+jac[1][1]
    result = np.stack([sum(central(c*(jac[j][i]+(trace if i == j else 0.)), j, g.dx)
                           for j in range(2)) for i in range(2)], axis=-1)
    if include_hessian:
        result += s[..., None]*np.stack([sum(central(central(g.bed, j, g.dx), i, g.dx)
                                            *value[..., j] for j in range(2))
                                         for i in range(2)], axis=-1)
    return result


class PhysicalFactors:
    """Actual reconstructed factors and analytic time/transpose pairings."""
    def __init__(self, system, tangent):
        self.system = system
        self.tangent = tangent
        self.h = system.geometry.h
        self.root = np.sqrt(self.h)
        self.ell = tangent.mass_rate/(2*self.h)

    def action(self, value, *, bottom=False):
        op = self.system.v if bottom else self.system.w
        return op(self.root[..., None]*value)/self.root

    def transpose(self, value, *, bottom=False):
        op = self.system.transpose_v if bottom else self.system.transpose_w
        return self.root[..., None]*op(value/self.root)

    def rate(self, value, *, bottom=False):
        dt, et = self.tangent.kinematic_rate(value)
        if bottom:
            return et
        d, _ = self.system.geometry.kinematic_components(value)
        return self.tangent.mass_rate*d+self.h*dt-1.5*et

    def transpose_rate(self, value, *, bottom=False):
        return (self.ell[..., None]*self.transpose(value, bottom=bottom)
                +self.root[..., None]*factor_transpose_direction(
                    self.system, self.tangent, value/self.root, bottom=bottom)
                -self.transpose(self.ell*value, bottom=bottom))

    def commutator(self, value):
        result = np.zeros_like(value)
        for bottom, weight in ((False, .5), (True, .375)):
            result += weight*(self.transpose(self.h*self.rate(value, bottom=bottom), bottom=bottom)
                              -self.transpose_rate(self.h*self.action(value, bottom=bottom), bottom=bottom))
        return result


def stage(g, physical_momentum, *, coupling='full', preconditioner='spectral-frozen-depth'):
    if not isinstance(g, SmoothPressureGeometry):
        raise ValueError('Smooth positive periodic terrain required')
    if coupling not in ('full', 'no-commutator', 'no-hessian'):
        raise ValueError('Unknown terrain coupling')
    if preconditioner not in ('patch', 'spectral-frozen-depth'):
        raise ValueError('Unknown terrain pressure preconditioner')
    system_type = PatchPressureSystem if preconditioner == 'patch' else ReconstructedAccelerationSystem
    h = g.h
    p = np.asarray(physical_momentum, float)
    if p.shape != (*h.shape, 2) or not np.isfinite(p).all():
        raise ValueError('Finite two-component physical momentum required')
    root = np.sqrt(h)
    u = p/h[..., None]
    divergence = lambda faces: sum((f-np.roll(f, 1, axis))/g.dx
                                   for f, axis in zip(faces, (1, 0)))
    means = [.5*(u+np.roll(u, -1, axis)) for axis in (1, 0)]
    depth_means = [.5*(h+np.roll(h, -1, axis)) for axis in (1, 0)]
    mass_faces = [depth_means[j]*means[j][..., j] for j in range(2)]
    ht = -divergence(mass_faces)
    base_faces = [K0*mass_faces[j][..., None]*means[j] for j in range(2)]
    # The exact transpose of paired mass transport acting on gravitational
    # potential: zero at a lake at rest, and potential work cancels mass work.
    eta = 9.81*(h+g.bed)
    gravity = np.stack([.5*(depth_means[j]*(np.roll(eta, -1, axis)-eta)
                            +np.roll(depth_means[j], 1, axis)*(eta-np.roll(eta, 1, axis)))/g.dx
                        for j, axis in enumerate((1, 0))], axis=-1)
    base_rhs = divergence(base_faces)+K0*u*ht[..., None]+gravity
    base_ledger = ledger.Ledger([face.copy() for face in base_faces], np.zeros_like(p))
    for j, axis in enumerate((1, 0)):
        base_ledger.faces[j][..., j] += .25*9.81*(h*h+np.roll(h*h, -1, axis))
        base_ledger.bed[..., j] = .5*9.81*(depth_means[j]*(np.roll(g.bed, -1, axis)-g.bed)
            +np.roll(depth_means[j], 1, axis)*(g.bed-np.roll(g.bed, 1, axis)))/g.dx
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    response = evaluate(g, p, preconditioner=preconditioner)
    ell = ht/(2*h)
    q = root[..., None]*u
    qt = ell[..., None]*q
    mapped_t = K0*qt
    skew_force = np.zeros_like(p)
    residuals = []
    commutator_work = 0.
    metric_ledger, skew_ledger = ledger.zero(g), ledger.zero(g)
    for pole in response['poles']:
        beta, alpha = pole['beta'], pole['alpha']
        system = system_type(g, beta)
        factors = PhysicalFactors(system, tangent)
        z = pole['normalized_auxiliary_velocity']
        wz, vz = system.w(z), system.v(z)
        wt, bt = factor_direction(g, tangent, z)
        qtz = (factor_transpose_direction(system, tangent, wz)+system.transpose_w(wt)
               +.75*(factor_transpose_direction(system, tangent, vz, bottom=True)+system.transpose_v(bt)))
        zt, stats = system.solve(qt-beta*qtz, iterations=40, preconditioner=preconditioner)
        residuals.extend((pole['relative_residual'], stats['relative_residual']))
        mapped_t += alpha*(qtz+system.transpose_w(system.w(zt))+.75*system.transpose_v(system.v(zt)))
        auxiliary = z/root[..., None]
        auxiliary_t = zt/root[..., None]-ell[..., None]*auxiliary
        metric_ledger = metric_ledger+(ledger.gram_rate(factors, auxiliary)+ledger.gram(factors, auxiliary_t))*alpha

        def pullback(rhs):
            solution, info = system.solve(rhs/root[..., None], iterations=40, preconditioner=preconditioner)
            residuals.append(info['relative_residual'])
            return root[..., None]*solution, solution/root[..., None]

        auxiliary = z/root[..., None]
        difference = u-auxiliary
        a = factors.action(auxiliary)
        e = factors.action(auxiliary, bottom=True)
        middle = (factors.transpose(skew_advection(p, a, g.dx))
                  +.75*factors.transpose(skew_advection(p, e, g.dx), bottom=True))
        middle_ledger = (ledger.factor_transpose(g, skew_advection(p, a, g.dx))
                         +ledger.factor_transpose(g, skew_advection(p, e, g.dx), bottom=True)*.75)
        j_w = factors.commutator(auxiliary)
        commutator_work += alpha*float(np.sum(auxiliary*j_w))*g.dx**2
        if coupling != 'no-commutator':
            middle += j_w
            middle_ledger = middle_ledger+ledger.commutator(factors, auxiliary)
        c = h*h*a
        s = h*(-1.5*a+.75*e)
        n = lambda value: tensor_action(g, c, s, value, include_hessian=coupling != 'no-hessian')
        difference_rhs = skew_advection(p, difference, g.dx)/beta
        pulled, middle_solution = pullback(middle+n(u))
        difference_pulled, difference_solution = pullback(difference_rhs)
        skew_force += alpha*(pulled-n(auxiliary)+difference_rhs-difference_pulled)
        # h L^-1 f = f-beta G L^-1 f. Assemble every divergence and
        # geometric source directly; no final-force residual becomes a source.
        skew_ledger = skew_ledger+(middle_ledger
            +ledger.tensor(g, c, s, difference, include_hessian=coupling != 'no-hessian')
            +ledger.gram(factors, difference_solution)*beta
            +ledger.gram(factors, middle_solution)*(-beta))*alpha

    metric_time_force = (ell[..., None]*h[..., None]*response['canonical_velocity']
                         +root[..., None]*mapped_t-K0*ht[..., None]*u)
    rhs = base_rhs+.5*metric_time_force+skew_force
    acceleration = dual(g, -rhs/h[..., None], preconditioner=preconditioner)
    ut = acceleration['layer_velocity']
    pt = h[..., None]*ut+ht[..., None]*u
    acceleration_metric = evaluate(g, h[..., None]*ut, preconditioner=preconditioner)
    acceleration_ledger = ledger.zero(g)
    for pole in acceleration_metric['poles']:
        factors = PhysicalFactors(system_type(g, pole['beta']), tangent)
        acceleration_ledger = acceleration_ledger+ledger.gram(
            factors, pole['normalized_auxiliary_velocity']/root[..., None])*pole['alpha']
        residuals.append(pole['relative_residual'])
    physical_ledger = (base_ledger+acceleration_ledger+metric_ledger*.5+skew_ledger)*(-1/K0)
    residuals.extend(pole['relative_residual'] for pole in acceleration['poles'])
    if max(residuals) > 2e-5:
        raise ValueError('Unqualified terrain pressure/auxiliary solve')
    eh, _ = depth_gradient(g, p, response, ht)
    energy_rate = float(np.sum(eh*ht)+np.sum(response['canonical_velocity']*pt))*g.dx**2
    if not np.isfinite(pt).all() or not np.isfinite(energy_rate):
        raise ValueError('Terrain stage exceeds represented range')
    return dict(coupling=coupling, preconditioner=preconditioner, depth_rate=ht, physical_momentum_rate=pt,
                physical_acceleration=ut, energy_rate=energy_rate,
                net_mass_rate=float(ht.sum())*g.dx**2,
                total_momentum_rate=pt.sum(axis=(0, 1))*g.dx**2,
                skew_energy_work=float(np.sum(u*skew_force))*g.dx**2,
                commutator_energy_work=commutator_work,
                gravity_mass_work_error=float(np.sum(u*gravity)-np.sum(eta*ht))*g.dx**2,
                physical_momentum_faces=[-face for face in physical_ledger.faces],
                physical_bed_force=physical_ledger.bed,
                local_momentum_ledger_error=float(np.max(abs(physical_ledger.action(g.dx)-pt))),
                metric_time_ledger_error=float(np.max(abs(metric_ledger.action(g.dx)-metric_time_force))),
                skew_ledger_error=float(np.max(abs(skew_ledger.action(g.dx)-skew_force))),
                maximum_solve_residual=max(residuals),
                local_physical_bed_force_ledger_accepted=False,
                nonlinear_model_or_dry_or_history_or_gameplay_accepted=False)
