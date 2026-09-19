"""Original two pressure poles with prescribed affine kinetic boundary work.

For E_C(a)=a.C.a/2+l.a+k, each original pole solves
H a=M v-lambda*l, H=M+lambda*C. Physical momentum is B v+q,
not B v. This exact reference preserves the existing pole constants and both
mass normalizations. It is not a natural open boundary or nonlinear PDE step.
"""
from subcell_moving_pressure_metric import MovingPressureMetric, PositiveSolve


class AffineMovingPressureMetric(MovingPressureMetric):
    def __init__(self, volumes, volume_rates, kinetic, kinetic_rate,
                 linear, linear_rate, constant, constant_rate):
        super().__init__(volumes, volume_rates, kinetic, kinetic_rate)
        z, n = self.zero, len(self.mass)
        self.linear = tuple(self.number(x) for x in linear)
        self.linear_rate = tuple(self.number(x) for x in linear_rate)
        self.boundary_constant = self.number(constant)
        self.boundary_constant_rate = self.number(constant_rate)
        if len(self.linear) != n or len(self.linear_rate) != n:
            raise ValueError('Matching affine kinetic vectors required')
        # Positivity belongs to the whole affine functional, not C alone.
        augmented = [(*row, self.linear[i]) for i, row in enumerate(self.kinetic)]
        augmented.append((*self.linear, 2*self.boundary_constant))
        PositiveSolve(augmented, z, allow_semidefinite=True)
        offset, offset_rate = [z]*n, [z]*n
        self.dual_constant = self.dual_constant_rate = z
        for pole in self.poles:
            length, weight = pole['length'], pole['weight']
            shift = pole['solver'].solve(tuple(-length*x for x in self.linear))
            hts = self.action(pole['matrix_rate'], shift)
            shift_rate = pole['solver'].solve(tuple(-length*x-y for x, y in zip(self.linear_rate, hts)))
            hs = self.action(pole['matrix'], shift)
            for i in range(n):
                offset[i] += weight*self.mass[i]*shift[i]
                offset_rate[i] += weight*(self.mass_rate[i]*shift[i]+self.mass[i]*shift_rate[i])
            self.dual_constant += weight*(self.dot(shift, hs)/2-length*self.boundary_constant)
            self.dual_constant_rate += weight*(self.dot(shift_rate, hs)+self.dot(shift, hts)/2
                                                -length*self.boundary_constant_rate)
            pole['boundary_shift'], pole['boundary_shift_rate'] = shift, shift_rate
        self.offset, self.offset_rate = tuple(offset), tuple(offset_rate)
        if self.dual_constant > 0:
            raise ValueError('Affine boundary energy is not nonnegative')

    @classmethod
    def from_trace(cls, trace):
        g = trace.geometry
        return cls(g.volumes, g.volume_rates, g.kinetic, g.kinetic_rate,
                   trace.linear, trace.linear_rate, trace.constant, trace.constant_rate)

    def dot(self, a, b):
        return sum((x*y for x, y in zip(a, b)), self.zero)

    def physical_momentum(self, canonical_velocity):
        bv = self.action(self.physical, self.vector(canonical_velocity))
        return self.pairs(tuple(x+y for x, y in zip(bv, self.offset)))

    def evaluate(self, physical_momentum, physical_momentum_rate):
        p, pt = self.vector(physical_momentum), self.vector(physical_momentum_rate)
        shifted = tuple(x-y for x, y in zip(p, self.offset))
        v = self.solve_physical.solve(shifted)
        btv = self.action(self.physical_rate, v)
        vt = self.solve_physical.solve(tuple(x-y-q for x, y, q in zip(pt, btv, self.offset_rate)))
        energy = self.dot(shifted, v)/2-self.dual_constant
        momentum_work = self.dot(pt, v)
        geometry_work = -self.dot(v, btv)/2-self.dot(v, self.offset_rate)-self.dual_constant_rate
        direct_rate = (self.dot(tuple(x-y for x, y in zip(pt, self.offset_rate)), v)
                       +self.dot(shifted, vt))/2-self.dual_constant_rate
        if direct_rate != momentum_work+geometry_work:
            raise ValueError('Affine physical momentum chain rule failed')
        mv = tuple(m*x for m, x in zip(self.mass, v))
        mvt = tuple(mt*x+m*xt for mt, x, m, xt in zip(self.mass_rate, v, self.mass, vt))
        reconstructed = [self.constant*x for x in mv]
        reconstructed_rate = [self.constant*x for x in mvt]
        positive_terms = [self.constant*self.dot(v, mv)/2]
        positive_rate = self.constant*(self.dot(vt, mv)+self.dot(v, mvt))/2
        poles = []
        for pole in self.poles:
            length, weight = pole['length'], pole['weight']
            rhs = tuple(x-length*y for x, y in zip(mv, self.linear))
            # Independent direct solve; don't reconstruct a from cached shifts.
            a = pole['solver'].solve(rhs)
            hta = self.action(pole['matrix_rate'], a)
            rhs_rate = tuple(x-length*y for x, y in zip(mvt, self.linear_rate))
            at = pole['solver'].solve(tuple(x-y for x, y in zip(rhs_rate, hta)))
            if self.action(pole['matrix'], a) != rhs:
                raise ValueError('Prescribed original pole residual is nonzero')
            if tuple(x+y for x, y in zip(self.action(pole['matrix'], at), hta)) != rhs_rate:
                raise ValueError('Prescribed original pole derivative failed')
            for i in range(len(p)):
                reconstructed[i] += weight*self.mass[i]*a[i]
                reconstructed_rate[i] += weight*(self.mass_rate[i]*a[i]+self.mass[i]*at[i])
            ca, cta = self.action(self.kinetic, a), self.action(self.kinetic_rate, a)
            kinetic = self.dot(a, ca)/2+self.dot(self.linear, a)+self.boundary_constant
            kinetic_rate = (self.dot(at, ca)+self.dot(a, cta)/2+self.dot(self.linear_rate, a)
                            +self.dot(self.linear, at)+self.boundary_constant_rate)
            if kinetic < 0:
                raise ValueError('Original lifted pressure kinetic energy is negative')
            positive_terms.append(weight*(sum((m*x*x for m, x in zip(self.mass, a)), self.zero)/2
                                          +length*kinetic))
            positive_rate += weight*(sum((mt*x*x/2+m*x*xt for mt, x, m, xt in
                                           zip(self.mass_rate, a, self.mass, at)), self.zero)+length*kinetic_rate)
            poles.append(dict(length=length, weight=weight, auxiliary_velocity=self.pairs(a),
                              auxiliary_velocity_rate=self.pairs(at), exact_residual_zero=True,
                              exact_rate_residual_zero=True))
        if tuple(reconstructed) != p or tuple(reconstructed_rate) != pt:
            raise ValueError('Affine two-pole momentum or rate reconstruction failed')
        if energy < 0 or sum(positive_terms, self.zero) != energy or positive_rate != direct_rate:
            raise ValueError('Independent affine positive energy or time work failed')
        layer = tuple(x/m for x, m in zip(p, self.mass))
        layer_rate = tuple((x-mt*u)/m for x, mt, u, m in zip(pt, self.mass_rate, layer, self.mass))
        return dict(kinetic_energy=energy, kinetic_energy_rate=direct_rate, momentum_work=momentum_work,
                    geometry_time_work=geometry_work, canonical_velocity=self.pairs(v),
                    canonical_velocity_rate=self.pairs(vt), canonical_momentum=self.pairs(mv),
                    canonical_momentum_rate=self.pairs(mvt), layer_velocity=self.pairs(layer),
                    layer_velocity_rate=self.pairs(layer_rate), poles=poles,
                    positive_energy_terms=tuple(positive_terms), positive_auxiliary_energy_rate=positive_rate,
                    exact_original_momentum_and_rate_reconstruction=True,
                    native_40cg_or_nonlinear_force_or_open_boundary_or_gameplay_accepted=False)
