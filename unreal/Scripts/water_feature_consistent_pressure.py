"""Area-weighted pressure reference with matching velocity boundary response.

Uniform-density Cartesian pressure impulse, not a complete liquid simulator.
Liquid-to-air distance comes from cached phi; solid open area is independently
geometric. Prescribed outflow velocity has zero pressure-gradient response on
BOTH orientations. Cell volumes, inertia and trajectory contact are not here.
"""
import numpy as np


def edges(shape, axis):
    low = [slice(None)]*3; high = list(low)
    low[axis] = slice(None, -1); high[axis] = slice(1, None)
    return tuple(low), tuple(high)


def flux_divergence(velocity, fractions):
    v, f = np.asarray(velocity, float), np.asarray(fractions, float)
    if v.ndim != 4 or v.shape[-1] != 3 or v.shape != f.shape or not np.isfinite([v, f]).all():
        raise ValueError('Matching finite lower-face arrays required')
    result = np.zeros(v.shape[:3]); w = v*f
    for axis in range(3):
        low, high = edges(result.shape, axis)
        result[low] += w[high+(axis,)]
        result[high] -= w[high+(axis,)]
    return result


class PressureBoundary:
    def __init__(self, flags, phi, fractions, fluid_type=1, empty_type=4, outflow_type=16, theta_floor=1e-4):
        flags = np.asarray(flags); phi = np.asarray(phi, float); f = np.asarray(fractions, float)
        if (flags.ndim != 3 or min(flags.shape) < 3 or phi.shape != flags.shape or f.shape != (*flags.shape, 3)
                or not np.issubdtype(flags.dtype, np.integer) or not np.isfinite(phi).all()
                or not np.isfinite(f).all() or np.any(f < 0) or np.any(f > 1) or not 0 < theta_floor <= 1):
            raise ValueError('Finite physical pressure lattice required')
        self.fluid = (flags & fluid_type) != 0
        if any(np.any(np.take(self.fluid, [0, -1], axis=a)) for a in range(3)):
            raise ValueError('Pressure stencil requires an explicit nonfluid outer cage')
        self.shape = flags.shape; self.fractions = f.copy(); self.faces = []; self.diagonal = np.zeros(flags.shape)
        self.inverse_distance = np.zeros_like(f); frozen_count = 0; free_count = 0; clamped = 0
        empty = (flags & empty_type) != 0; out = (flags & outflow_type) != 0
        for axis in range(3):
            low, high = edges(flags.shape, axis)
            fl, fh = self.fluid[low], self.fluid[high]
            frozen = (fl & out[high]) | (fh & out[low])
            free = ((fl & empty[high]) | (fh & empty[low])) & ~frozen
            active = ((fl & fh) | free) & (f[high+(axis,)] > 0)
            inside = np.where(fl, phi[low], phi[high]); outside = np.where(fl, phi[high], phi[low])
            if np.any(free & active & ((inside >= 0) | (outside < 0))):
                raise ValueError('Free-surface flags and liquid sign disagree; do not invent interface distance')
            distance = np.ones(fl.shape)
            # Linear interface location between the two centers, independent
            # of the solid aperture. No same-sign fallback or volume fit.
            distance[free & active] = -inside[free & active]/(outside[free & active]-inside[free & active])
            clamped += int(np.count_nonzero(free & active & (distance < theta_floor)))
            response = np.where(active, 1./np.maximum(distance, theta_floor), 0.)
            weight = f[high+(axis,)]*response
            self.inverse_distance[high+(axis,)] = response
            self.faces.append((low, high, weight))
            self.diagonal[low] += weight; self.diagonal[high] += weight
            frozen_count += int(np.count_nonzero(frozen & (f[high+(axis,)] > 0)))
            free_count += int(np.count_nonzero(free & active))
        self.diagonal[~self.fluid] = 0
        if np.any(self.fluid & (self.diagonal <= 0)):
            indices = np.argwhere(self.fluid & (self.diagonal <= 0))
            raise ValueError('Uncoupled fluid cell has no pressure response; geometry/flags must be repaired: '
                             +str(len(indices))+' cells, first indices '+str(indices[:20].tolist()))
        self.proof = dict(active_fluid_cells=int(np.count_nonzero(self.fluid)),
            prescribed_outflow_faces=frozen_count, free_surface_faces=free_count,
            interface_distance_floor=theta_floor, clamped_interface_faces=clamped,
            minimum_diagonal=float(self.diagonal[self.fluid].min()),
            maximum_diagonal=float(self.diagonal.max()),
            scope='Matched area/distance gradient and flux operator; not geometric volume/contact or CFD acceptance')

    def apply(self, pressure):
        p = np.asarray(pressure, float)
        if p.shape != self.shape or not np.isfinite(p).all() or np.any(p[~self.fluid] != 0):
            raise ValueError('Finite pressure impulse supported only on fluid cells required')
        result = np.zeros(self.shape)
        for low, high, weight in self.faces:
            difference = weight*(p[high]-p[low])
            result[low] -= difference; result[high] += difference
        result[~self.fluid] = 0
        return result

    def correct(self, velocity, pressure):
        v = np.asarray(velocity, float).copy(); p = np.asarray(pressure, float)
        if v.shape != self.fractions.shape or not np.isfinite(v).all():
            raise ValueError('Finite physical MAC velocity required')
        self.apply(p)  # validate support; no arbitrary pressure outside liquid.
        for axis, (low, high, _) in enumerate(self.faces):
            v[high+(axis,)] -= self.inverse_distance[high+(axis,)]*(p[high]-p[low])
        return v

    def solve(self, rhs, tolerance=1e-8, max_iterations=2000):
        b = np.asarray(rhs, float)
        if b.shape != self.shape or not np.isfinite(b).all() or np.any(b[~self.fluid] != 0) or tolerance <= 0:
            raise ValueError('Finite fluid-only RHS and positive tolerance required')
        p = np.zeros(self.shape); residual = b.copy(); z = np.zeros(self.shape)
        z[self.fluid] = residual[self.fluid]/self.diagonal[self.fluid]
        direction = z.copy(); energy = float(np.sum(residual*z)); history = []
        for step in range(max_iterations+1):
            maximum = float(np.max(np.abs(residual[self.fluid])))
            history.append(maximum)
            if maximum <= tolerance:
                # Recurrence can hide drift; verify with a fresh matrix apply.
                fresh = b-self.apply(p); error = float(np.max(np.abs(fresh[self.fluid])))
                if error <= tolerance:
                    return p, dict(iterations=step, maximum_fresh_residual=error,
                        fixed_absolute_tolerance=tolerance, residual_history=history)
                residual = fresh; z[self.fluid] = residual[self.fluid]/self.diagonal[self.fluid]
                direction = z.copy(); energy = float(np.sum(residual*z))
            if step == max_iterations:
                break
            product = self.apply(direction); denominator = float(np.sum(direction*product))
            if not np.isfinite([energy, denominator]).all() or denominator <= 0 or energy <= 0:
                raise ValueError('Nonpositive/invalid pressure Krylov energy; no compatibility correction imposed')
            alpha = energy/denominator; p += alpha*direction; residual -= alpha*product
            z[self.fluid] = residual[self.fluid]/self.diagonal[self.fluid]
            following = float(np.sum(residual*z)); direction = z+(following/energy)*direction; energy = following
        raise ValueError('Pressure reference failed its fixed residual target')

    def project(self, velocity, tolerance=1e-8, max_iterations=2000):
        b = -flux_divergence(velocity, self.fractions); b[~self.fluid] = 0
        p, proof = self.solve(b, tolerance, max_iterations)
        corrected = self.correct(velocity, p)
        return corrected, p, proof
