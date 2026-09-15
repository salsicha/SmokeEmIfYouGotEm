"""Linear gravity waves about a source-supported lake at rest; research only.

Let B map physical pool momentum to conservative volume rate on wet faces,
H=diag(g/wet_area), and M=R*S*R, R=sqrt(reference volume). S is the SAME
original two-pole response. For volume perturbation a and physical momentum p:
    a_t = B p, p_t = -M B.T H a.
The quadratic energy is .5*p.T*M^-1*p + .5*a.T*H*a. The paired operators
conserve its rate without any energy projection. This is NOT nonlinear
advection, evolving geometry/topology, a breaking model or a playable solver.
"""
import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from pressure_cg_range_reference import solve as range_cg
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from subcell_source_activation import assembly


class GravityWaveStage:
    def __init__(self, partition, gravity=9.81):
        if not np.isfinite(gravity) or gravity <= 0:
            raise ValueError('Positive finite gravity required')
        if any(np.any(pool['momentum'] != 0) for pool in partition.pools):
            raise ValueError('Reference must be a lake at rest, not a moving river state')
        equilibrium = assembly(partition, gravity, face_scheme='donor')
        if (equilibrium['new_region_rates'] or np.max(abs(equilibrium['volume_rate'])) > 1e-10
                or np.max(abs(equilibrium['momentum_rate'])) > 1e-10):
            raise ValueError('Reference fails original source-face hydrostatic balance')
        self.partition, self.gravity = partition, gravity
        self.systems = [WetPoolPressureSystem(partition, float(length)) for length in LENGTHS]
        self.volume = self.systems[0].h[:, 0].copy()
        self.root = np.sqrt(self.volume)
        self.hessian = gravity/np.array([pool['form']['wet_area'] for pool in partition.pools])
        self.hroot = np.sqrt(self.hessian)
        self.residuals = []
        entries = {}
        self.faces = []
        for face in self.systems[0].connections:
            left, right = face['left'], face['right']
            normal = np.eye(2)[face['axis']] if face['axis'] is not None else face['normal']
            weight = .5*face['area']*np.asarray(normal)
            self.faces.append((left, right, weight))
            for owner in (left, right):
                for j in range(2):
                    for row, sign in ((left, -1), (right, 1)):
                        key = (row, 2*owner+j)
                        entries[key] = entries.get(key, 0.)+sign*weight[j]/self.volume[owner]
        entries = [(row, col, value) for (row, col), value in entries.items() if value != 0]
        self.rows = np.array([row for row, _, _ in entries], int)
        self.cols = np.array([col for _, col, _ in entries], int)
        self.coefficients = np.array([value for _, _, value in entries])
        # S <= I gives this inexpensive upper-bound diagonal for the Schur
        # preconditioner. Actual actions always retain both original poles.
        self.schur_diagonal_bound = self.hessian*np.bincount(self.rows,
            weights=self.coefficients**2*np.repeat(self.volume, 2)[self.cols], minlength=len(self.volume))

    def scalar(self, value):
        value = np.asarray(value, float)
        if value.shape != self.volume.shape or not np.isfinite(value).all():
            raise ValueError('Finite scalar perturbation per reference pool required')
        return value

    def vector(self, value):
        value = np.asarray(value, float)
        if value.shape != (len(self.volume), 2) or not np.isfinite(value).all():
            raise ValueError('Finite physical momentum per reference pool required')
        return value

    def transport(self, momentum):
        p = self.vector(momentum)
        return np.bincount(self.rows, weights=self.coefficients*p.ravel()[self.cols], minlength=len(self.volume))

    def transport_transpose(self, scalar):
        value = self.scalar(scalar)
        return np.bincount(self.cols, weights=self.coefficients*value[self.rows], minlength=2*len(value)).reshape(-1, 2)

    def metric(self, canonical, *, include_poles=False):
        q = (self.root[:, None]*self.vector(canonical))[:, None, :]
        result = (1-float(np.sum(WEIGHTS)))*q
        poles = []
        for system, weight in zip(self.systems, WEIGHTS):
            z, stats = system.solve(q)
            self.residuals.append(stats['relative_residual'])
            if stats['relative_residual'] > 2e-5:
                raise ValueError('Original 40-CG gravity-wave pressure residual gate failed')
            result += weight*z
            if include_poles:
                poles.append((system, float(weight), z))
        physical = self.root[:, None]*result[:, 0]
        return (physical, poles) if include_poles else physical

    def pressure_force(self, potential):
        """Independent local face flux, exact-bed and reflecting-wall ledger.

        From A*z=q, M*f=V*f-sum(weight*length*R*Q*z). Expand Q through
        its original Gram jet. Its divergence transpose is a paired face
        traction; the remaining two Gram components are the bed reaction.
        Never infer bed force by subtracting the final momentum divergence.
        """
        potential = self.scalar(potential)
        physical, poles = self.metric(-self.transport_transpose(potential), include_poles=True)
        bed, wall = np.zeros_like(physical), np.zeros_like(physical)
        fluxes = [weight*(potential[left]+potential[right]) for left, right, weight in self.faces]
        for i, pool in enumerate(self.partition.pools):
            storage = pool['storage']
            _, wet = storage._triangle_volume_and_wet_area(pool['form']['stage_offset'], storage.relative_levels)
            bed[i] = -potential[i]*np.sum(wet[:, None]*storage.bed_gradients, axis=0)
        for face in self.systems[0].walls:
            wall[face['owner'], face['axis']] -= face['sign']*face['area']*potential[face['owner']]
        for system, weight, z in poles:
            auxiliary = z[:, 0]/self.root[:, None]
            jet = np.column_stack((system.divergence(auxiliary), auxiliary))
            force = np.einsum('nij,nj->ni', np.array([p['form']['gram'] for p in self.partition.pools]), jet)
            multiplier = weight*system.length
            bed -= multiplier*force[:, 1:]
            for index, (left, right, normal_area) in enumerate(self.faces):
                fluxes[index] -= multiplier*normal_area*(force[left, 0]/self.volume[left]+force[right, 0]/self.volume[right])
            for face in system.walls:
                i = face['owner']
                wall[i, face['axis']] += multiplier*face['sign']*face['area']*force[i, 0]/self.volume[i]
        ledger_rate = bed+wall
        for (left, right, _), flux in zip(self.faces, fluxes):
            ledger_rate[left] -= flux
            ledger_rate[right] += flux
        error = float(np.max(abs(ledger_rate-physical)))
        if error > 1e-10:
            raise ValueError('Linear exact-bed/wall/face momentum ledger failed')
        return dict(physical_momentum_rate=physical, face_fluxes=fluxes,
            bed_force=bed, wall_force=wall, local_force_ledger_error=error)

    def rates(self, volume_perturbation, physical_momentum):
        a, p = self.scalar(volume_perturbation), self.vector(physical_momentum)
        return self.transport(p), self.pressure_force(self.hessian*a)['physical_momentum_rate']

    def energy(self, volume_perturbation, physical_momentum):
        a, p = self.scalar(volume_perturbation), self.vector(physical_momentum)
        primal = evaluate(self.partition, p[:, None, :], self.gravity)
        self.residuals.extend(pole['relative_residual'] for pole in primal['poles'])
        return primal['kinetic']+.5*float(np.sum(self.hessian*a*a))

    def midpoint(self, volume_perturbation, physical_momentum, duration):
        """Matrix-free midpoint on the FIXED linear system, not nonlinear state.

        The scalar Schur system is packed into the first component of the
        existing range-PCG API. The unused component has identity action and
        zero RHS. Both scalar/pressure solves retain 40 iterations and gates.
        """
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError('Positive finite duration required')
        a, p = self.scalar(volume_perturbation), self.vector(physical_momentum)
        # A linear perturbation must not be returned as a finite negative-water
        # or changed-support state. Probes validate support only; the linear
        # operator still uses the original lake geometry throughout.
        self.partition.volume_probe(self.volume+a)
        self.residuals = []
        w = self.hroot*a
        coefficient = .25*duration**2
        def schur_action(value):
            return self.hroot*self.transport(self.metric(self.transport_transpose(self.hroot*value)))
        stage = self
        class Schur:
            h = stage.volume[:, None]
            def apply(self, value):
                result = value.copy()
                result[:, 0, 0] += coefficient*schur_action(value[:, 0, 0])
                return result
            def precondition(self, value, scheme):
                result = value.copy()
                result[:, 0, 0] /= 1+coefficient*stage.schur_diagonal_bound
                return result
        rhs = np.zeros((len(a), 1, 2))
        rhs[:, 0, 0] = w-coefficient*schur_action(w)+duration*self.hroot*self.transport(p)
        solved, stats = range_cg(Schur(), rhs, 40)
        if stats['relative_residual'] > 2e-5:
            raise ValueError('40-CG gravity-wave Schur residual gate failed')
        anew = solved[:, 0, 0]/self.hroot
        self.partition.volume_probe(self.volume+anew)
        pnew = p-duration*self.metric(self.transport_transpose(.5*self.hessian*(a+anew)))
        adot = self.transport(.5*(p+pnew))
        force_ledger = self.pressure_force(.5*self.hessian*(a+anew))
        pdot = force_ledger['physical_momentum_rate']
        equation_error = max(float(np.max(abs(anew-a-duration*adot))), float(np.max(abs(pnew-p-duration*pdot))))
        before, after = self.energy(a, p), self.energy(anew, pnew)
        mass_error = abs(float(np.sum(anew-a)))
        external_impulse = duration*np.sum(force_ledger['bed_force']+force_ledger['wall_force'], axis=0)
        momentum_error = float(np.max(abs(np.sum(pnew-p, axis=0)-external_impulse)))
        if max(equation_error, mass_error, momentum_error, abs(after-before)) > 1e-10:
            raise ValueError('Linear midpoint conservation or original-equation residual failed')
        return dict(volume_perturbation=anew, physical_momentum=pnew,
            energy_before=before, energy_after=after, energy_change=after-before,
            mass_error=mass_error, equation_error=equation_error,
            momentum_error=momentum_error, external_impulse=external_impulse,
            local_force_ledger_error=force_ledger['local_force_ledger_error'],
            maximum_pressure_residual=max(self.residuals, default=0.), schur_solve=stats,
            nonlinear_or_topology_or_native_or_gameplay_accepted=False)
