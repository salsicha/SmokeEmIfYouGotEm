"""Bounded continuous P2 velocity moving-liquid reference.

Quadratic 3D geometry, material kinetic mass, Simpson space-time divergence
and implicit-midpoint gravity/pressure. Global volume and mechanical energy
are discrete identities, NOT proof of locally constant density or converged
Euler dynamics. No topological changes, viscosity, capillarity or air phase.
"""
from itertools import combinations, product
import math
import numpy as np

EDGE_PAIRS = tuple(combinations(range(4), 2))
GRAD_LAMBDA = np.array([[-1., -1., -1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])


def quadrature(order=5):
    """Duffy tensor Gauss, including reference-simplex Jacobian."""
    roots, weights = np.polynomial.legendre.leggauss(order); roots = (roots+1)/2; weights = weights/2
    bary = []; w = []
    for i, j, k in product(range(order), repeat=3):
        a, b, c = roots[i], roots[j], roots[k]
        xyz = [a, (1-a)*b, (1-a)*(1-b)*c]
        bary.append([1-sum(xyz), *xyz]); w.append(weights[i]*weights[j]*weights[k]*(1-a)**2*(1-b))
    return np.array(bary), np.array(w)


def basis(bary):
    l = np.asarray(bary, float)
    n = [l[:, i]*(2*l[:, i]-1) for i in range(4)]
    grad = [(4*l[:, i, None]-1)*GRAD_LAMBDA[i] for i in range(4)]
    for i, j in EDGE_PAIRS:
        n.append(4*l[:, i]*l[:, j]); grad.append(4*(l[:, i, None]*GRAD_LAMBDA[j]+l[:, j, None]*GRAD_LAMBDA[i]))
    return np.array(n).T, np.moveaxis(np.array(grad), 0, 1)


def geometry_jacobian(positions, cells, grad):
    jac = np.einsum('tja,qjb->tqab', positions[cells], grad)
    cof = np.empty_like(jac)
    cof[..., 0] = np.cross(jac[..., 1], jac[..., 2])
    cof[..., 1] = np.cross(jac[..., 2], jac[..., 0])
    cof[..., 2] = np.cross(jac[..., 0], jac[..., 1])
    determinant = np.einsum('tqa,tqa->tq', jac[..., 0], cof[..., 0])
    return determinant, cof


def cubic_bernstein_matrix():
    alpha = np.array([a for a in product(range(4), repeat=4) if sum(a) == 3], int)
    bary = alpha/3
    matrix = np.array([[math.factorial(3)/math.prod(math.factorial(int(x)) for x in a)
                       *math.prod(float(l[i])**int(a[i]) for i in range(4)) for a in alpha] for l in bary])
    return bary, np.linalg.inv(matrix)


class MovingLiquid:
    def __init__(self, vertices, tetrahedra, density=1000., maximum_velocity_nodes=400,
                 pressure_mode='discontinuous_p1'):
        v = np.asarray(vertices, float); t = np.asarray(tetrahedra)
        if (v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all() or t.ndim != 2 or t.shape[1] != 4
                or not np.issubdtype(t.dtype, np.integer) or len(t) == 0 or np.any(t < 0) or np.any(t >= len(v))
                or not np.isfinite(density) or density <= 0 or len({tuple(sorted(x)) for x in t}) != len(t)):
            raise ValueError('Finite conforming nonoverlapping tetrahedral input required')
        t = t.copy(); rawdet = np.linalg.det(v[t[:, 1:]]-v[t[:, :1]])
        if np.any(rawdet == 0):
            raise ValueError('Degenerate material cell, not removed')
        reverse = rawdet < 0; t[reverse, 2:4] = t[reverse, 3:1:-1]
        edges = {}; nodes = list(v.copy()); cells = []
        for tet in t:
            ids = list(tet)
            for i, j in EDGE_PAIRS:
                key = tuple(sorted((int(tet[i]), int(tet[j]))))
                if key not in edges:
                    edges[key] = len(nodes); nodes.append((v[key[0]]+v[key[1]])/2)
                ids.append(edges[key])
            cells.append(ids)
        if len(nodes) > maximum_velocity_nodes:
            raise ValueError('Bounded dense moving-liquid reference size exceeded')
        if pressure_mode not in ('continuous_p1', 'discontinuous_p1'):
            raise ValueError('Explicit pressure space required')
        self.pressure_mode = pressure_mode; self.positions = np.array(nodes)
        self.pressure_cells = t if pressure_mode == 'continuous_p1' else np.arange(4*len(t)).reshape(-1, 4)
        self.vertex_cells = t; self.cells = np.array(cells); self.edges = edges
        self.pressure_nodes = len(v) if pressure_mode == 'continuous_p1' else 4*len(t)
        self.density = float(density); self._cached_free = None
        self.bary, self.weights = quadrature(); self.N, self.grad = basis(self.bary)
        self.cert_bary, self.cert_inverse = cubic_bernstein_matrix(); _, self.cert_grad = basis(self.cert_bary)
        self.velocities = np.zeros_like(self.positions); self.steps = 0
        self.initialize_material(self.positions)
        self.fixed = np.zeros_like(self.positions, bool)

    def initialize_material(self, positions):
        """Author the initial curved material geometry BEFORE any step.

        Not a volume/density fit or post-step reset. Initial quadrature mass
        follows the genuinely supplied geometry and remains immutable thereafter.
        """
        positions = np.asarray(positions, float)
        if self.steps != 0 or np.any(self.velocities != 0) or positions.shape != self.positions.shape or not np.isfinite(positions).all():
            raise ValueError('Only finite pre-simulation material authoring allowed')
        self.certify(positions); self.positions = positions.copy()
        self.reference_positions = positions.copy(); self.reference_det, _ = geometry_jacobian(positions, self.cells, self.grad)
        reference_samples, _ = geometry_jacobian(positions, self.cells, self.cert_grad)
        self.reference_bernstein = reference_samples@self.cert_inverse.T
        self.scalar_mass = np.zeros((len(positions), len(positions)))
        local = self.density*np.einsum('q,tq,qi,qj->tij', self.weights, self.reference_det, self.N, self.N)
        for ci, ids in enumerate(self.cells):
            self.scalar_mass[np.ix_(ids, ids)] += local[ci]
        self.M = np.kron(self.scalar_mass, np.eye(3))
        self._cached_free = None
        self.material_mass = float(self.scalar_mass.sum()); self.reference_volume = self.material_mass/self.density

    def tank_slip_walls(self, length=(1., .6, .5)):
        """Stationary planar solid walls; component constraints at ALL P2 nodes.

        Only a flat bed and x/y planar walls are authored here, not arbitrary
        collider fitting. Free top can deform in all 3D directions permitted
        by the walls. These constraints extend over entire quadratic wall faces.
        """
        x = self.reference_positions; self.fixed[:] = False
        for axis in (0, 1):
            self.fixed[:, axis] = (x[:, axis] == 0) | (x[:, axis] == length[axis])
        self.fixed[:, 2] = x[:, 2] == 0

    def certify(self, positions):
        det, _ = geometry_jacobian(positions, self.cells, self.cert_grad)
        coefficients = det@self.cert_inverse.T
        minimum = float(coefficients.min())
        allowance = 128*np.finfo(float).eps*float(np.max(np.abs(coefficients)))
        if not np.isfinite(coefficients).all() or minimum <= allowance:
            raise ValueError('Quadratic material mapping not certified positive; no inverted-cell deletion')
        return minimum

    def divergence_matrix(self, positions):
        _, cof = geometry_jacobian(positions, self.cells, self.grad)
        local = np.einsum('q,qi,qjb,tqab->tija', self.weights, self.bary, self.grad, cof, optimize=True)
        result = np.zeros((self.pressure_nodes, 3*len(self.positions)))
        for ci, ids in enumerate(self.cells):
            dofs = (3*ids[:, None]+np.arange(3)).ravel()
            result[np.ix_(self.pressure_cells[ci], dofs)] += local[ci].reshape(4, 30)
        return result

    def volume(self, positions):
        det, _ = geometry_jacobian(positions, self.cells, self.grad)
        return float(np.sum(det*self.weights))

    def energy(self, positions, velocities, gravity):
        u = velocities.ravel(); force = self.M@np.tile(gravity, len(positions))
        return float(u@self.M@u/2-positions.ravel()@force)

    def step(self, dt, gravity=(0., 0., -9.80665), maximum_iterations=16,
             position_tolerance=2e-12, weak_flux_tolerance=2e-11):
        g = np.asarray(gravity, float)
        if (not np.isfinite(dt) or dt <= 0 or g.shape != (3,) or not np.isfinite(g).all()
                or not np.isfinite([position_tolerance, weak_flux_tolerance]).all()
                or position_tolerance <= 0 or weak_flux_tolerance <= 0):
            raise ValueError('Physical step and fixed finite tolerances required')
        old_x = self.positions.copy(); old_u = self.velocities.copy(); free = ~self.fixed.ravel()
        if np.any(old_u[self.fixed] != 0):
            raise ValueError('Initial motion violates prescribed wall contact')
        force = self.M@np.tile(g, len(old_x)); mf = self.M[np.ix_(free, free)]
        rhs = (self.M@old_u.ravel()+dt/2*force)[free]
        if self.pressure_mode == 'discontinuous_p1' and not np.array_equal(self._cached_free, free):
            self._cached_free = free.copy(); self._free_cholesky = np.linalg.cholesky(mf)
        end = old_x+dt*old_u; initial_B = self.divergence_matrix(old_x); history = []
        for iteration in range(maximum_iterations):
            # Cofactor is quadratic along the straight node trajectory. Simpson
            # gives the EXACT represented time integral, not an endpoint guess.
            Bbar = (initial_B+4*self.divergence_matrix((old_x+end)/2)+self.divergence_matrix(end))/6
            bf = Bbar[:, free]
            if self.pressure_mode == 'continuous_p1':
                system = np.block([[mf, -bf.T], [bf, np.zeros((len(bf), len(bf)))]])
                sol = np.linalg.solve(system, np.concatenate((rhs, np.zeros(len(bf)))))
                rank = len(bf); null_gradient = 0.
            else:
                # DG pressure can contain exact redundant constraints on this
                # mesh. Solve the FULL minimum-kinetic projection, explicitly
                # verify null gradients and ALL original constraint rows. This
                # is not a claim of inf-sup stability or unique pressure values.
                factor = self._free_cholesky
                # Rank revelation on the kinetic-whitened gradient itself,
                # NOT squared Schur eigenvalues (which lose small real modes).
                unscaled = np.linalg.solve(factor, bf.T).T
                diagonal = np.linalg.norm(unscaled, axis=1)
                if np.any(diagonal <= 0):
                    raise ValueError('Uncoupled local pressure row, not removed')
                scaled = unscaled/diagonal[:, None]
                vectors, singular, right = np.linalg.svd(scaled, full_matrices=False)
                cutoff = 128*np.finfo(float).eps*max(scaled.shape)*singular[0]
                active = singular > cutoff; rank = int(active.sum())
                null_gradient = float(np.linalg.norm(bf.T@(vectors[:, ~active]/diagonal[:, None]))) if (~active).any() else 0.
                if null_gradient > 2e-9:
                    raise ValueError('Discarded pressure modes are not verified redundant constraints')
                predictor = np.linalg.solve(factor, rhs)
                row_coordinates = right[active]@predictor
                multiplier = -vectors[:, active]@(row_coordinates/singular[active])/diagonal
                corrected = np.linalg.solve(factor.T, predictor-right[active].T@row_coordinates)
                sol = np.concatenate((corrected, multiplier))
            midpoint_u = np.zeros(old_x.size); midpoint_u[free] = sol[:free.sum()]
            candidate = old_x+dt*midpoint_u.reshape(old_x.shape)
            error = float(np.max(np.abs(candidate-end))); history.append(error); end = candidate
            if error <= position_tolerance:
                break
        else:
            raise ValueError('Implicit moving-pressure fixed point failed, state unchanged; '
                             f'pressure rank {rank}/{len(bf)}, position history {history}')
        # Fresh end-geometry readback, not the preceding iteration matrix.
        Bbar = (initial_B+4*self.divergence_matrix((old_x+end)/2)+self.divergence_matrix(end))/6
        residual = Bbar@midpoint_u; impulse = sol[free.sum():]
        momentum = self.M@midpoint_u-(self.M@old_u.ravel()+dt/2*force)-Bbar.T@impulse
        if np.max(np.abs(residual)) > weak_flux_tolerance or np.max(np.abs(momentum[free])) > 2e-8:
            raise ValueError('Fresh moving pressure/momentum constraints failed, state unchanged')
        minimum = self.certify(end); new_u = 2*midpoint_u.reshape(old_x.shape)-old_u
        old_volume = self.volume(old_x); new_volume = self.volume(end)
        if abs(new_volume-old_volume) > 2e-11 or (self.fixed.any() and np.max(np.abs(end[self.fixed]-old_x[self.fixed])) != 0):
            raise ValueError('Swept volume or exact wall contact failed, state unchanged')
        old_energy = self.energy(old_x, old_u, g); new_energy = self.energy(end, new_u, g)
        if abs(new_energy-old_energy) > 2e-8:
            raise ValueError('Material midpoint pressure/gravity energy identity failed')
        det, cof = geometry_jacobian(end, self.cells, self.grad)
        ratio = self.reference_det/det  # carried material density / initial density
        certificate_samples, _ = geometry_jacobian(end, self.cells, self.cert_grad)
        current_bernstein = certificate_samples@self.cert_inverse.T
        coefficient_ratios = self.reference_bernstein/current_bernstein
        # Both polynomials have positive coefficients in the same basis. Their
        # pointwise ratio is a positive weighted average of coefficient ratios.
        # Floating coefficient bounds, not outward-rounded interval arithmetic.
        old_det, _ = geometry_jacobian(old_x, self.cells, self.grad)
        cell_change = np.sum((det-old_det)*self.weights, axis=1)
        if self.pressure_mode == 'discontinuous_p1' and np.max(np.abs(cell_change)) > 2e-11:
            raise ValueError('Local material cell volume failed, state unchanged')
        physical_grad_u = np.einsum('tja,qjb,tqcb->tqac', new_u[self.cells], self.grad, cof)/det[:, :, None, None]
        point_divergence = np.trace(physical_grad_u, axis1=2, axis2=3)
        proof = dict(iterations=iteration+1, iteration_history_m=history,
            pressure_mode=self.pressure_mode, pressure_rows=len(bf), pressure_rank=rank,
            null_gradient_norm=null_gradient,
            maximum_weak_flux_residual_m3_s=float(np.max(np.abs(residual))),
            maximum_free_momentum_residual=float(np.max(np.abs(momentum[free]))),
            volume_m3=new_volume, volume_change_m3=new_volume-old_volume, material_mass_kg=self.material_mass,
            maximum_cell_volume_change_m3=float(np.max(np.abs(cell_change))),
            energy_j=new_energy, energy_change_j=new_energy-old_energy,
            minimum_bernstein_jacobian=minimum, wall_displacement_m=0.,
            quadrature_density_ratio_min=float(ratio.min()), quadrature_density_ratio_max=float(ratio.max()),
            bernstein_density_ratio_lower=float(coefficient_ratios.min()),
            bernstein_density_ratio_upper=float(coefficient_ratios.max()),
            maximum_point_divergence_per_second=float(np.max(np.abs(point_divergence))),
            maximum_end_weak_flux_residual_m3_s=float(np.max(np.abs(self.divergence_matrix(end)@new_u.ravel()))),
            maximum_nodal_speed_m_s=float(np.max(np.linalg.norm(new_u, axis=1))), accepted=False)
        self.positions = end; self.velocities = new_u; self.steps += 1
        return impulse*2/dt, proof
