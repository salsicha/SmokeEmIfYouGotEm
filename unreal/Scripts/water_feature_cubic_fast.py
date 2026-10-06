"""Full-row cubic quadratic-pressure solve with cached material whitening.

Same space-time impulse equations and fresh physical gates as frozen SVD
reference. Cholesky never discards pressure modes; failure preserves state.
No inf-sup/rank proof inferred from positive factors or good conservation.
"""
import numpy as np
from water_feature_cubic_material import CubicMaterial
from water_feature_moving_tetra import geometry_jacobian


def cholesky_vector_solve(lower, rhs):
    """Actual triangular solves, not repeated general LU factorizations."""
    y = np.array(rhs, float, copy=True)
    for i in range(len(y)):
        y[i] = (y[i]-lower[i, :i]@y[:i])/lower[i, i]
    for i in range(len(y)-1, -1, -1):
        y[i] = (y[i]-lower[i+1:, i]@y[i+1:])/lower[i, i]
    return y


class CubicMaterialFast(CubicMaterial):
    def initialize_material(self, positions):
        super().initialize_material(positions)
        self._fast_free = None; self._fast_inverse = None

    def step(self, dt, gravity=(0., 0., -9.80665), maximum_iterations=16,
             position_tolerance=2e-12, weak_flux_tolerance=2e-11):
        if self.pressure_degree != 2:
            return super().step(dt, gravity, maximum_iterations, position_tolerance, weak_flux_tolerance)
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
        if not np.array_equal(self._fast_free, free):
            self._fast_free = free.copy(); factor = np.linalg.cholesky(mf)
            self._fast_inverse = np.linalg.inv(factor)
        end = old_x+dt*old_u; initial_B = self.divergence_matrix(old_x); history = []
        for iteration in range(maximum_iterations):
            # Cofactor is quadratic along the straight node trajectory. Simpson
            # gives the EXACT represented time integral, not an endpoint guess.
            Bbar = (initial_B+4*self.divergence_matrix((old_x+end)/2)+self.divergence_matrix(end))/6
            bf = Bbar[:, free]
            inverse = self._fast_inverse
            unscaled = bf@inverse.T; diagonal = np.linalg.norm(unscaled, axis=1)
            if np.any(diagonal <= 0):
                raise ValueError('Uncoupled actual pressure row, not removed')
            scaled = unscaled/diagonal[:, None]
            schur = scaled@scaled.T; pressure_factor = np.linalg.cholesky(schur)
            predictor = inverse@rhs; pressure_rhs = -(scaled@predictor)
            scaled_multiplier = cholesky_vector_solve(pressure_factor, pressure_rhs)
            # Refine the ORIGINAL full Schur equations; no eigenvalue cutoff,
            # pressure-row removal, density fitting or changed physical RHS.
            for _ in range(2):
                correction = cholesky_vector_solve(pressure_factor, pressure_rhs-schur@scaled_multiplier)
                scaled_multiplier += correction
            multiplier = scaled_multiplier/diagonal
            corrected = inverse.T@(predictor+scaled.T@scaled_multiplier)
            sol = np.concatenate((corrected, multiplier))
            rank = None; null_gradient = None  # no rank certificate is claimed by Cholesky.
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
        if np.max(np.abs(cell_change)) > 2e-11:
            raise ValueError('Local material cell volume failed, state unchanged')
        physical_grad_u = np.einsum('tja,qjb,tqcb->tqac', new_u[self.cells], self.grad, cof)/det[:, :, None, None]
        point_divergence = np.trace(physical_grad_u, axis1=2, axis2=3)
        proof = dict(iterations=iteration+1, iteration_history_m=history,
            pressure_mode=self.pressure_mode, pressure_degree=self.pressure_degree,
            linear_solver='all-row Schur Cholesky with original-row refinement',
            pressure_rows=len(bf), pressure_rank=rank,
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
