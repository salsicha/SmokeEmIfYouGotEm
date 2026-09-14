"""Research scalar boundary action on actual three-ring source support.

This does NOT replace the interior pressure geometry, its affine face traces,
or a playable solver. The exterior velocity/divergence/bed-velocity traces are
derived from supplied conserved samples, not padded interior values. Scalar
coefficients use the reconstructed extended geometry; physical pressure still
uses the caller's original D/E and signed transposes. Mechanical-energy and
wetting-front qualification remain separate requirements.
"""
import numpy as np
from fractions import Fraction
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from difference_scalar_gradient_reference import difference_gradient
from directional_pressure_geometry import DirectionalPressureGeometry
from pressure_cut_face_reference import represented_float


def velocity_of(state):
    state = np.asarray(state, dtype=float)
    if (state.ndim != 3 or state.shape[-1] != 3 or not np.isfinite(state).all()
            or np.any(state[..., 0] < 0)
            or np.any(state[..., 1:][state[..., 0] == 0] != 0)):
        raise ValueError('Invalid conserved source; no depth or momentum repair')
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        result = np.divide(state[..., 1:], state[..., 0, None],
            out=np.zeros_like(state[..., 1:]), where=state[..., 0, None] > 0)
    if not np.isfinite(result).all():
        raise ValueError('Unrepresentable source velocity')
    return result


class SourceSupportedScalarBoundary:
    width = 3

    def __init__(self, interior_geometry, current_state, full_source_state, full_bed, *, full_rate=None):
        g = interior_geometry
        if (g.periodic or g.pressure_trace != 'integrated_column'
                or g.bed_quadrature != 'shared_bottom'):
            raise ValueError('Requires nonperiodic integrated/shared-bottom geometry')
        ny, nx = g.h.shape
        self.core = (slice(3, ny+3), slice(3, nx+3))
        state = np.asarray(current_state, dtype=float)
        full = np.asarray(full_source_state, dtype=float)
        bed = np.asarray(full_bed, dtype=float)
        if (state.shape != (ny, nx, 3) or full.shape != (ny+6, nx+6, 3)
                or bed.shape != full.shape[:2] or not np.isfinite(bed).all()
                or not np.array_equal(state[..., 0], g.h)
                or not np.array_equal(bed[self.core], g.bed)):
            raise ValueError('Source stencil and current geometry are not registered')
        velocity_of(state)
        velocity_of(full)
        # Source interior is NEVER installed as evolving state. Only its ring
        # survives this splice; caller's complete current interior is retained.
        self.state = full.copy()
        self.state[self.core] = state
        self.velocity = velocity_of(self.state)
        self.original = g
        self.extended = ReconstructedPressureGeometry(self.state[..., 0], bed, g.dx,
            periodic=False, pressure_trace='integrated_column', bed_quadrature='shared_bottom')
        self.full_rate = None
        if full_rate is None:
            if np.any(g.kinematic_support != (g.h > 0)):
                raise ValueError('Entering cells require actual full conserved rates')
        else:
            rate = np.asarray(full_rate, dtype=float)
            if rate.shape != self.state.shape or not np.isfinite(rate).all():
                raise ValueError('Invalid full conserved direction')
            h = self.state[..., 0]; ht = rate[..., 0]
            activating = (h == 0)&(ht > 0)
            if (np.any((h == 0)&(ht < 0))
                    or np.any(rate[..., 1:][(h == 0)&~activating] != 0)):
                raise ValueError('Invalid dry conserved direction; no rate repair')
            if not np.array_equal(g.kinematic_support, ((h > 0)|activating)[self.core]):
                raise ValueError('Original geometry does not match actual entering support')
            if isinstance(g, DirectionalPressureGeometry) and not np.array_equal(g.tangent.mass_rate, ht[self.core]):
                raise ValueError('Original tangent differs from actual interior mass rate')
            if np.any(activating):
                self.extended = DirectionalPressureGeometry(self.extended, ht)
                for point in map(tuple, np.argwhere(activating)):
                    for component in (0, 1):
                        self.velocity[point][component] = represented_float(
                            Fraction(float(rate[point][component+1]))/Fraction(float(ht[point])))
            self.full_rate = rate.copy(); self.full_rate.flags.writeable = False
        self.state.flags.writeable = False
        self.velocity.flags.writeable = False

    def gradient(self, scalar, exterior_scalar):
        f = self.original._scalar(scalar)
        supplied = np.asarray(exterior_scalar, dtype=float)
        if supplied.shape != self.state.shape[:2] or not np.isfinite(supplied).all():
            raise ValueError('Missing finite full scalar support')
        full = supplied.copy()
        full[self.core] = f
        return difference_gradient(self.extended, full)[self.core].copy()

    def exterior_kinematics(self, boundary_velocity):
        """Ghost D/E from real neighbors and the ORIGINAL independent face u.

        Replace only the shared normal-velocity value on the four interfaces
        when evaluating ghost D. E retains the extended shared-bottom moment;
        no independent exterior bottom-pressure or radiation data are invented.
        Interior D remains caller-owned and is overwritten explicitly below.
        """
        g = self.original
        trace = np.asarray(boundary_velocity, dtype=float)
        # Existing validator also retains support and corner accumulation rules.
        g.prescribed_divergence_lift(trace)
        d, e = self.extended.kinematic_components(self.velocity)
        ny, nx = g.h.shape
        for component, edge in enumerate(self.extended.edges):
            if component == 0:
                low = (slice(3, ny+3), 2); low_inside = (slice(3, ny+3), 3)
                high = (slice(3, ny+3), nx+2); high_ghost = (slice(3, ny+3), nx+3)
                low_u, high_u = trace[:ny, 0], trace[ny:2*ny, 0]
            else:
                low = (2, slice(3, nx+3)); low_inside = (3, slice(3, nx+3))
                high = (ny+2, slice(3, nx+3)); high_ghost = (ny+3, slice(3, nx+3))
                low_u, high_u = trace[2*ny:2*ny+nx, 0], trace[2*ny+nx:, 0]
            u = self.velocity[..., component]
            low_face = edge['own'][low]*u[low]+edge['other'][low]*u[low_inside]
            high_face = edge['own'][high]*u[high]+edge['other'][high]*u[high_ghost]
            d[low] += edge['aa'][low]*(low_u-low_face)/g.dx
            d[high_ghost] -= edge['ab'][high]*(high_u-high_face)/g.dx
        return d, e

    def forcing(self, geometry_rate, boundary_velocity):
        """Q,C,Adv using unchanged interior D/E, D_t/E_t and affine traces."""
        g = self.original
        if geometry_rate.geometry is not g:
            raise ValueError('Geometry tangent must belong to original interior')
        if self.full_rate is not None and not np.array_equal(geometry_rate.mass_rate, self.full_rate[self.core][..., 0]):
            raise ValueError('Forcing tangent differs from supplied conserved direction')
        if geometry_rate.one_sided and self.full_rate is None:
            raise ValueError('Directional entering velocity requires actual full conserved rates')
        u = self.velocity[self.core]
        adv = np.stack([np.sum(u*self.gradient(u[..., i], self.velocity[..., i]), axis=-1)
                        for i in (0, 1)], axis=-1)
        d, e = g.kinematic_components(u)
        dt, et = geometry_rate.kinematic_rate(u)
        lift = g.prescribed_divergence_lift(boundary_velocity)
        d, dt = d+lift[..., 0], dt+lift[..., 1]
        ghost_d, ghost_e = self.exterior_kinematics(boundary_velocity)
        da, ea = g.kinematic_components(adv)
        q = d*d+da-dt-np.sum(u*self.gradient(d, ghost_d), axis=-1)
        c = et+np.sum(u*self.gradient(e, ghost_e), axis=-1)-ea
        if not all(np.isfinite(v).all() for v in (q, c, adv)):
            raise ValueError('Source-supported forcing exceeds storage range')
        return q, c, adv
