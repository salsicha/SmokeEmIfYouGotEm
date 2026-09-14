"""Nonlinear SGN-type acceleration/pressure reference, NOT production water.

Includes the SGN velocity-gradient and bottom-acceleration terms. One pole with
length 1/3 is the standard SGN closure; the existing two rational poles retain
the finite-depth linear response and SGN leading long-wave moment. The latter
is an experimental rational extension, not the exact Whitham-GN/DtN operator.
The matrix-free symmetric solve has a fixed maximum of 40 PCG iterations.
"""
import numpy as np
from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from pressure_cg_range_reference import solve as solve_range_cg


def depth_weights(depth):
    """Mass-weighted face velocity interpolation, without a depth cutoff.

Keep both fractions explicitly: 1-left loses tiny but nonzero right weights.
This is a research discretization; it does not change the continuum closure.
"""
    result = []
    for axis in (1, 0):
        other = np.roll(depth, -1, axis)
        total = depth+other
        result.append((np.divide(depth, total, out=np.zeros_like(depth), where=total > 0),
            np.divide(other, total, out=np.zeros_like(depth), where=total > 0)))
    return result


def gradient(value, pairs, dx, weights=None):
    """Negative adjoint of divergence; constants have exactly zero gradient."""
    result = []
    for component, (axis, pair) in enumerate(zip((1, 0), pairs)):
        left = np.roll(pair, 1, axis)
        if weights is None:
            result.append((pair*(np.roll(value, -1, axis)-value)
                + left*(value-np.roll(value, 1, axis)))/(2*dx))
        else:
            own, other = weights[component]
            result.append((pair*own*(np.roll(value, -1, axis)-value)
                + left*np.roll(other, 1, axis)*(value-np.roll(value, 1, axis)))/dx)
    return np.stack(result, axis=-1)


def divergence(vector, pairs, dx, weights=None):
    result = np.zeros(vector.shape[:-1])
    for component, (axis, pair) in enumerate(zip((1, 0), pairs)):
        v = vector[..., component]
        if weights is None:
            right = pair*(v+np.roll(v, -1, axis))/(2*dx)
        else:
            own, other = weights[component]
            right = pair*(own*v+other*np.roll(v, -1, axis))/dx
        result += right-np.roll(right, 1, axis)
    return result


def depth_weight_rates(depth, mass_rate):
    """Time derivative of both face weights on a fixed reconstructed wet graph."""
    result = []
    for axis, (own, other) in zip((1, 0), depth_weights(depth)):
        total = depth+np.roll(depth, -1, axis)
        rate = np.divide(mass_rate*other-own*np.roll(mass_rate, -1, axis), total,
            out=np.zeros_like(depth), where=total > 0)
        result.append((rate, -rate))
    return result


def geometric_bed_slope(bed, dx, periodic=False, exterior_bed=None):
    """Fixed raster geometry derivative, independent of water depth/weights."""
    bed = np.asarray(bed, dtype=float)
    if bed.ndim != 2 or not np.all(np.isfinite(bed)) or not np.isfinite(dx) or dx <= 0:
        raise ValueError('Invalid physical bed geometry')
    if exterior_bed is not None:
        exterior_bed = np.asarray(exterior_bed, dtype=float)
        if periodic or exterior_bed.shape != (2*sum(bed.shape),) or not np.isfinite(exterior_bed).all():
            raise ValueError('Invalid physical exterior bed geometry')
    components = []
    for axis in (1, 0):
        if exterior_bed is not None:
            ny, nx = bed.shape
            count, start = (ny, 0) if axis == 1 else (nx, 2*ny)
            low, high = np.roll(bed, 1, axis), np.roll(bed, -1, axis)
            first, last = [slice(None)]*2, [slice(None)]*2
            first[axis], last[axis] = 0, -1
            low[tuple(first)] = exterior_bed[start:start+count]
            high[tuple(last)] = exterior_bed[start+count:start+2*count]
            components.append((high-low)/(2*dx))
            continue
        value = (np.roll(bed, -1, axis)-np.roll(bed, 1, axis))/(2*dx)
        if bed.shape[axis] == 1: value[:] = 0
        elif not periodic:
            first, last = [slice(None)]*2, [slice(None)]*2
            first[axis], last[axis] = 0, -1
            value[tuple(first)] = (np.take(bed, 1, axis)-np.take(bed, 0, axis))/dx
            value[tuple(last)] = (np.take(bed, -1, axis)-np.take(bed, -2, axis))/dx
        components.append(value)
    return np.stack(components, axis=-1)


def prescribed_boundary_source(boundary_velocity, depth, pairs, dx):
    """Affine divergence lift for prescribed face-normal velocity and its dt.

    Packed west/east/south/north traces use positive x/y orientation. The
    linear velocity-correction divergence and its pressure adjoint stay paired;
    the trace and trace time derivative are supplied data, not solved unknowns.
    This is a prescribed-velocity/zero-normal-pressure-gradient condition,
    NOT a transparent-wave condition. Dry pressure cells remain inactive.
    """
    trace = np.asarray(boundary_velocity, dtype=float)
    ny, nx = depth.shape
    if (trace.shape != (2*(nx+ny), 2) or not np.isfinite(trace).all() or not np.isfinite(dx) or dx<=0
            or np.any(pairs[0][:, -1]) or np.any(pairs[1][-1, :])):
        raise ValueError('Invalid prescribed pressure boundary trace or wrapped graph')
    result = np.zeros((*depth.shape, 2))
    result[:, 0] -= trace[:ny]/dx
    result[:, -1] += trace[ny:2*ny]/dx
    result[0, :] -= trace[2*ny:2*ny+nx]/dx
    result[-1, :] += trace[2*ny+nx:]/dx
    return np.where(depth[..., None] > 0, result, 0.)


def kinematic_terms(h, bed, velocity, mass_rate, pairs, dx, weights, bed_slope=None, boundary_velocity=None):
    """Discrete material identities, without assuming a spatial product rule.

    q = (D u)^2 - (partial_t + u.G)(D u) = Q - D a,
    c = (partial_t + u.G)(u.G b) = b.a + C, a=u_t+u.G u.
    D/G depend on h for weighted interpolation; differentiate those weights
    with the actual finite-volume h_t. Connectivity is fixed within each rate
    evaluation; this does not assert smoothness across wet-graph changes.
    """
    derivatives = np.stack([gradient(velocity[..., c], pairs, dx, weights) for c in (0, 1)], axis=-2)
    advective = np.einsum('...ij,...j->...i', derivatives, velocity)
    div_u = divergence(velocity, pairs, dx, weights)
    lift = prescribed_boundary_source(boundary_velocity, h, pairs, dx) if boundary_velocity is not None else None
    if lift is not None: div_u += lift[..., 0]
    b = gradient(bed, pairs, dx, weights) if bed_slope is None else bed_slope
    weight_rates = depth_weight_rates(h, mass_rate) if weights is not None else None
    div_rate = divergence(velocity, pairs, dx, weight_rates) if weight_rates is not None else 0.
    if lift is not None: div_rate = div_rate+lift[..., 1]
    bed_rate = gradient(bed, pairs, dx, weight_rates) if weight_rates is not None and bed_slope is None else np.zeros_like(b)
    quadratic = div_u**2+divergence(advective, pairs, dx, weights) \
        -np.sum(velocity*gradient(div_u, pairs, dx, weights), axis=-1)-div_rate
    curvature = np.sum(velocity*gradient(np.sum(velocity*b, axis=-1), pairs, dx, weights), axis=-1) \
        -np.sum(b*advective, axis=-1)+np.sum(velocity*bed_rate, axis=-1)
    return quadratic, curvature, advective


class AccelerationSystem:
    def __init__(self, depth, bed, pairs, dx, length, *, interpolation='centered', bed_slope=None, dispersion_fraction=None):
        self.h, self.bed = np.asarray(depth, dtype=float), np.asarray(bed, dtype=float)
        if (self.h.ndim != 2 or self.h.shape != self.bed.shape or not self.h.size
                or np.any(self.h < 0) or not np.all(np.isfinite(self.h))
                or not np.all(np.isfinite(self.bed)) or not np.isfinite(dx) or dx <= 0
                or not np.isfinite(length) or length <= 0 or len(pairs) != 2):
            raise ValueError('Invalid nonlinear pressure geometry')
        for axis, pair in zip((1, 0), pairs):
            if np.shape(pair) != self.h.shape or np.asarray(pair).dtype != bool:
                raise ValueError('Invalid nonlinear pressure graph')
            if np.any(pair & ((self.h <= 0) | (np.roll(self.h, -1, axis) <= 0))):
                raise ValueError('Nonlinear pressure edge touches a dry cell')
        self.pairs, self.dx, self.length = pairs, dx, length
        self.fraction = np.ones_like(self.h) if dispersion_fraction is None else np.asarray(dispersion_fraction,dtype=float)
        if (self.fraction.shape != self.h.shape or not np.all(np.isfinite(self.fraction))
                or np.any(self.fraction < 0) or np.any(self.fraction > 1)):
            raise ValueError('Invalid nonbreaking dispersion fraction')
        self.root = np.sqrt(self.h)
        self.inv_root = np.divide(1, self.root, out=np.zeros_like(self.h), where=self.h > 0)
        self.h32 = self.h*self.root
        if interpolation not in ('centered', 'depth_weighted'):
            raise ValueError('Unknown nonlinear pressure interpolation')
        self.weights = depth_weights(self.h) if interpolation == 'depth_weighted' else None
        if bed_slope is not None and (np.shape(bed_slope) != (*self.h.shape, 2) or not np.all(np.isfinite(bed_slope))):
            raise ValueError('Invalid physical bed slope')
        self.b = gradient(self.bed, pairs, dx, self.weights) if bed_slope is None else np.where(self.h[..., None]>0, bed_slope, 0.)
        self.factored_edges = None
        if self.weights is not None:
            self.factored_edges = []
            for axis, pair, (own, other) in zip((1, 0), pairs, self.weights):
                left = np.roll(pair, 1, axis)
                # sqrt(w*w)=w exactly for equal depths. Multiplying two
                # rounded square roots otherwise breaks the constant-row
                # transverse nullspace, even in a one-dimensional flow.
                root_weight = np.where(own == other, own, np.sqrt(own)*np.sqrt(other))
                right = pair*self.h*root_weight/dx
                minus = -self.h*left*np.roll(root_weight, 1, axis)/dx
                self.factored_edges.append((right, minus))
        # Diagonal of the completed-square operator (an upper approximation
        # for a two-cell periodic axis where the +/- neighbors coincide).
        diagonal = np.ones((*self.h.shape, 2))
        centers = []
        for component, (axis, pair) in enumerate(zip((1, 0), pairs)):
            left = np.roll(pair, 1, axis)
            if self.weights is None:
                center = self.h*(pair.astype(float)-left)/(2*dx)-1.5*self.b[..., component]
                neighboring = (pair*np.roll(self.fraction*self.h**3, -1, axis)+left*np.roll(self.fraction*self.h**3, 1, axis))*self.inv_root**2/(4*dx*dx)
            else:
                own, other = self.weights[component]
                other_left = np.roll(other, 1, axis)
                center = self.h*(pair*own-left*other_left)/dx-1.5*self.b[..., component]
                right, minus = self.factored_edges[component]
                neighboring = np.roll(self.fraction*minus**2, -1, axis)+np.roll(self.fraction*right**2, 1, axis)
            centers.append(center)
            diagonal[..., component] += length*(self.fraction*(center**2+.75*self.b[..., component]**2)+neighboring)
        self.diagonal = diagonal
        self.centers = np.stack(centers, axis=-1)
        self.off_diagonal = length*self.fraction*(centers[0]*centers[1]+.75*self.b[..., 0]*self.b[..., 1])

    def precondition(self, residual, scheme='diagonal'):
        if scheme == 'diagonal':
            return residual/self.diagonal
        if scheme != 'block':
            raise ValueError('Unknown nonlinear pressure preconditioner')
        # Same-cell 2x2 blocks retain the x/y coupling from W and bottom slope.
        # Schur elimination avoids forming the potentially huge determinant.
        a, b = self.diagonal[..., 0], self.diagonal[..., 1]
        ratio = self.off_diagonal/a
        schur = b-self.off_diagonal*ratio
        if np.any(schur <= 0) or not np.all(np.isfinite(schur)):
            raise ValueError('Invalid nonlinear pressure preconditioner block')
        second = (residual[..., 1]-ratio*residual[..., 0])/schur
        first = residual[..., 0]/a-ratio*second
        return np.stack((first, second), axis=-1)

    def w(self, value):
        if self.factored_edges is not None:
            result = np.sum(self.centers*value, axis=-1)
            for component, (axis, (right, minus)) in enumerate(zip((1, 0), self.factored_edges)):
                result += right*np.roll(value[..., component], -1, axis)+minus*np.roll(value[..., component], 1, axis)
            return result
        acceleration = value*self.inv_root[..., None]
        return self.h32*divergence(acceleration, self.pairs, self.dx, self.weights)-1.5*np.sum(self.b*value, axis=-1)

    def transpose_w(self, value):
        if self.factored_edges is not None:
            result = self.centers*value[..., None]
            for component, (axis, (right, minus)) in enumerate(zip((1, 0), self.factored_edges)):
                result[..., component] += np.roll(minus*value, -1, axis)+np.roll(right*value, 1, axis)
            return result
        return -self.inv_root[..., None]*gradient(self.h32*value, self.pairs, self.dx, self.weights)-1.5*self.b*value[..., None]

    def apply(self, value):
        # I + l W^T W + 3l/4 B^T B: symmetric positive definite, including
        # dry cells where the row is identity and the physical forcing is zero.
        return value+self.length*(self.transpose_w(self.fraction*self.w(value))
            + .75*self.fraction[...,None]*self.b*np.sum(self.b*value, axis=-1)[..., None])

    def solve(self, rhs, iterations=40, *, preconditioner='diagonal'):
        return solve_range_cg(self,np.asarray(rhs,dtype=float),iterations,preconditioner=preconditioner)


def nonlinear_pressure_force(depth, bed, velocity, hydro_force, pairs, dx, *, rational=True,
                             preconditioner='diagonal', interpolation='centered',
                             formulation='expanded', mass_rate=None, momentum_rate=None, bed_slope=None,
                             on_pressure=None, dispersion_fraction=None, boundary_velocity=None):
    """Return conservative pressure divergence plus physical bottom traction.

Material acceleration a satisfies (I+T)a=a_hydro-Q. Reconstruct depth-integrated
pressure and bottom pressure from that a, rather than multiplying a smoothed
surface gradient by changing h. On flat periodic beds pressure divergence sums
to zero independently of iterative-solve residual.
"""
    h = np.asarray(depth, dtype=float)
    if velocity.shape != (*h.shape, 2) or hydro_force.shape != velocity.shape:
        raise ValueError('Invalid nonlinear pressure vector fields')
    if not np.all(np.isfinite(velocity)) or not np.all(np.isfinite(hydro_force)):
        raise ValueError('Nonfinite nonlinear pressure vector fields')
    if boundary_velocity is not None and (formulation != 'kinematic' or bed_slope is None):
        raise ValueError('Prescribed pressure boundary requires kinematic forcing and physical bed slopes')
    # Work in sqrt(h)*acceleration throughout. A finite momentum rate can
    # exceed the representable acceleration in a positive subnormal cell.
    # Dividing by h and then multiplying by sqrt(h) overflows unnecessarily.
    root = np.sqrt(h)
    scaled_acceleration0 = np.divide(hydro_force, root[..., None], out=np.zeros_like(hydro_force), where=h[..., None] > 0)
    if interpolation not in ('centered', 'depth_weighted'):
        raise ValueError('Unknown nonlinear pressure interpolation')
    weights = depth_weights(h) if interpolation == 'depth_weighted' else None
    derivatives = np.stack([gradient(velocity[..., c], pairs, dx, weights) for c in (0, 1)], axis=-2)
    div_u = divergence(velocity, pairs, dx, weights)
    quadratic = div_u**2+np.einsum('...ij,...ji->...', derivatives, derivatives)
    if bed_slope is not None and (np.shape(bed_slope) != velocity.shape or not np.all(np.isfinite(bed_slope))):
        raise ValueError('Invalid physical bed slope')
    bed_gradient = gradient(bed, pairs, dx, weights) if bed_slope is None else np.asarray(bed_slope)
    bed_hessian = np.stack([gradient(bed_gradient[..., c], pairs, dx, weights) for c in (0, 1)], axis=-2)
    bottom_curvature = np.einsum('...i,...ij,...j->...', velocity, bed_hessian, velocity)
    if formulation not in ('expanded', 'kinematic'):
        raise ValueError('Unknown nonlinear pressure formulation')
    if formulation == 'kinematic':
        if (np.shape(mass_rate) != h.shape or np.shape(momentum_rate) != velocity.shape
                or not np.all(np.isfinite(mass_rate)) or not np.all(np.isfinite(momentum_rate))):
            raise ValueError('Kinematic pressure requires the actual finite-volume mass/momentum rates')
        quadratic, bottom_curvature, advective = kinematic_terms(h, bed, velocity, mass_rate, pairs, dx, weights, bed_slope, boundary_velocity)
        scaled_acceleration0 = np.divide(momentum_rate-velocity*mass_rate[..., None], root[..., None],
            out=np.zeros_like(velocity), where=h[..., None] > 0)+root[..., None]*advective
    force = np.zeros_like(velocity)
    diagnostics = []
    captured = [] if on_pressure is not None else None
    lengths, pole_weights = (LENGTHS, WEIGHTS) if rational else (np.array([1/3]), np.array([1.]))
    for length, weight in zip(lengths, pole_weights):
        system = AccelerationSystem(h, bed, pairs, dx, float(length), interpolation=interpolation, bed_slope=bed_slope,
                                    dispersion_fraction=dispersion_fraction)
        fraction = system.fraction
        forcing_pressure = length*fraction*(h**3*quadratic+1.5*h*h*bottom_curvature)
        forcing_bottom = length*fraction*(1.5*h*h*quadratic+3*h*bottom_curvature)
        nonlinear_force = gradient(forcing_pressure, pairs, dx, weights)+forcing_bottom[..., None]*bed_gradient
        # Solve for the pressure correction, not the enormous identity part
        # of a newly wet cell's FV acceleration. Construct K*base explicitly:
        # A*base-base loses small pressure terms to cancellation. This is the
        # same equation A*(base+delta)=base-nonlinear_force/sqrt(h), not a
        # different tolerance, velocity bound or added damping.
        base_w = system.w(scaled_acceleration0)
        base_bottom = np.sum(system.b*scaled_acceleration0, axis=-1)
        rhs = -length*(system.transpose_w(fraction*base_w)+.75*fraction[...,None]*system.b*base_bottom[..., None]) \
            -system.inv_root[..., None]*nonlinear_force
        correction, stats = system.solve(rhs, preconditioner=preconditioner)
        stats['unknown'] = 'normalized_acceleration_correction'
        # Same pressure reconstruction factored through W: never materialize
        # acceleration=scaled/sqrt(h), which can overflow although the depth-
        # integrated pressure and conservative momentum derivative are finite.
        w = base_w+system.w(correction)
        pressure = forcing_pressure-length*fraction*system.h32*w
        bottom_pressure = forcing_bottom+length*fraction*system.root*(-1.5*w+.75*(base_bottom+np.sum(system.b*correction, axis=-1)))
        force -= weight*(gradient(pressure, pairs, dx, weights)+bottom_pressure[..., None]*bed_gradient)
        diagnostics.append(stats)
        if captured is not None:
            captured.append(dict(length=float(length), weight=float(weight),
                rhs=rhs.copy(), correction=correction.copy(), pressure=pressure.copy(),
                bottom_pressure=bottom_pressure.copy(), base=scaled_acceleration0.copy(),
                quadratic=quadratic.copy(), curvature=bottom_curvature.copy()))
    if on_pressure is not None:
        # Diagnostics never receive aliases to caller inputs or a live solve.
        # No clipping, physical validity decision or change to returned force.
        on_pressure(captured)
    return force, diagnostics


def pressure_column(depth, integrated_nonhydrostatic, bottom_nonhydrostatic, gravity=9.81):
    """Quadratic SGN pressure profile, per density, on 0 <= sigma <= 1.

    p(sigma)=alpha*(1-sigma)+beta*(1-sigma**2), with p(1)=0.
    Integrating over z gives h*(alpha/2+2*beta/3). Reconstruct from the
    returned conservative pressures, including the weighted rational poles.
    This is a model diagnostic, not a proof that the physical water follows
    that profile. Negative gauge pressure is reported, never clipped or
    automatically labelled cavitation/confirmed separation.
    """
    h, p, b = (np.asarray(value, dtype=float) for value in
               (depth, integrated_nonhydrostatic, bottom_nonhydrostatic))
    if (h.ndim != 2 or p.shape != h.shape or b.shape != h.shape
            or np.any(h < 0) or not all(np.all(np.isfinite(v)) for v in (h, p, b))
            or not np.isfinite(gravity) or gravity <= 0
            or np.any(p[h == 0] != 0) or np.any(b[h == 0] != 0)):
        raise ValueError('Invalid pressure column fields')
    mean_nonhydrostatic = np.divide(p, h, out=np.zeros_like(h), where=h > 0)
    alpha = gravity*h+4*b-6*mean_nonhydrostatic
    beta = 6*mean_nonhydrostatic-3*b
    bottom = gravity*h+b
    sigma = np.where(bottom < 0, 0., 1.)
    minimum = np.minimum(bottom, 0.)
    stationary = np.divide(-alpha, 2*beta, out=np.zeros_like(h), where=beta != 0)
    interior = (beta < 0) & (stationary > 0) & (stationary < 1)
    interior_pressure = alpha*(1-stationary)+beta*(1-stationary*stationary)
    take = interior & (interior_pressure < minimum)
    sigma = np.where(take, stationary, sigma)
    minimum = np.where(take, interior_pressure, minimum)
    return dict(alpha=alpha, beta=beta, bottom=bottom, minimum=minimum,
                minimum_sigma=sigma, integrated=.5*gravity*h*h+p)
