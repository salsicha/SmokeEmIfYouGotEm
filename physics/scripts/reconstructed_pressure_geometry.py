"""Second-order cut-column pressure/traction geometry RESEARCH operator.

Uses the existing unscaled MC h/eta reconstruction, including its exact face
arithmetic fallback. Does not advance water or replace the native/playable model.
Horizontal pressure transfer holds the column mean pressure P/h and bottom B
constant within a cell: P_face = P*H_face/h, B_face = B. With linear H(x), its
cell-average integrated pressure remains P. Integrate each hydrostatic cut using
the quadratic vertical profile, then assemble a shared face pressure plus the
blocked-column correction AND the within-cell bed traction.

This determines linear operators L(P,B)=-D^T P+E^T B. The returned E is generally
nonlocal; adding the old B*bed-slope term would double-count bed traction.
This class supplies static operators and the prescribed divergence lift.
Separate research modules supply stationary-dry-set derivatives and a factored
pressure correction. Wetting-front closure, full nonlinear evolution and
physical/cost qualification remain required. The MC wet-stencil switch is retained,
not claimed continuous when an owning cell becomes exactly dry.
KNOWN LIMITATION: the P/h transfer does not exactly annihilate constant
integrated P on a variable-depth flat bed; the refinement audit measures a
first-order maximum-norm defect at limiter extrema. Do not promote this transfer
on the strength of conservation/adjoint tests alone.

An explicit 'integrated_column' research trace instead holds P and B constant
inside each cell (no local P/h*dh term). It recovers the original fully wet
flat-bed pressure stencil. Its raw one-sided normalized profile need not stay
bounded as H_face tends to zero with a positive owning depth; only the actual
weighted shared flux can be assessed in that joint limit. This distinction is
not a bounded-pressure or wet/dry qualification. Zero reconstructed height with
positive owning depth is rejected for this trace, not assigned a finite P.

The explicit 'shared_bottom' quadrature reconstructs one mass-weighted B trace
at each face. Its cut-profile off-diagonal coefficient k=own*other*(Cb-Ca) is
symmetric. The diagonal is fixed by the physical constant-B bed-slope moment,
so BOTH E(1) and E^T(1) equal the original geometric bed slope. This is a new
research nonhydrostatic source quadrature, not a change to FV transport/terrain
or a claim that the earlier polynomial source integral is unchanged.
"""
from fractions import Fraction
import numpy as np
from pressure_cut_face_reference import cut_pressure_column, represented_float
from total_depth_bank_replay import mc, hydrostatic_faces
from total_depth_nonlinear_pressure import geometric_bed_slope


def transfer_coefficients(cell_height, face_height, retained, *, pressure_trace='mean_column'):
    """Linear T=A*P+C*B with moment-preserving P_face=P*H_face/h.

    Exact scalar arithmetic is a reference choice, not a runtime optimization.
    A zero reconstructed column has zero integral and requires no normalization.
    """
    if pressure_trace not in ('mean_column', 'integrated_column'):
        raise ValueError('Unknown research pressure trace')
    h, face, wet = map(float, (cell_height, face_height, retained))
    if (not all(np.isfinite(v) for v in (h, face, wet)) or min(h, face, wet) < 0
            or wet > face or (h == 0 and face != 0)):
        raise ValueError('Invalid pressure transfer geometry')
    if face == 0:
        if h > 0 and pressure_trace == 'integrated_column':
            raise ValueError('Zero reconstructed column cannot carry a positive-owner integrated trace')
        return 0., 0.
    p_face = Fraction(face)/Fraction(h) if pressure_trace == 'mean_column' else Fraction(1)
    a = cut_pressure_column(face, p_face, 0., wet).transmitted
    c = cut_pressure_column(face, 0., 1., wet).transmitted
    return represented_float(a), represented_float(c)


class ReconstructedPressureGeometry:
    def __init__(self, depth, bed, dx, *, periodic=False, pressure_trace='mean_column',
                 bed_quadrature='polynomial', exterior_bed=None):
        h, z = np.asarray(depth, dtype=float), np.asarray(bed, dtype=float)
        if (h.ndim != 2 or not h.size or z.shape != h.shape or np.any(h < 0)
                or not np.isfinite(h).all() or not np.isfinite(z).all()
                or not np.isfinite(dx) or dx <= 0 or type(periodic) is not bool):
            raise ValueError('Invalid reconstructed pressure geometry')
        if pressure_trace not in ('mean_column', 'integrated_column'):
            raise ValueError('Unknown research pressure trace')
        if bed_quadrature not in ('polynomial', 'shared_bottom'):
            raise ValueError('Unknown research bottom-pressure quadrature')
        self.pressure_trace = pressure_trace
        self.bed_quadrature = bed_quadrature
        self.h = h.copy(); self.h.flags.writeable = False
        self.bed = z.copy(); self.bed.flags.writeable = False
        self.dx = float(dx); self.periodic = periodic
        physical_slope = geometric_bed_slope(z, dx, periodic, exterior_bed=exterior_bed)
        self.physical_slope = physical_slope.copy(); self.physical_slope.flags.writeable = False
        self.edges = []; self.polynomials = []
        for component, axis in enumerate((1, 0)):
            stencil = (h > 0) & (np.roll(h, 1, axis) > 0) & (np.roll(h, -1, axis) > 0)
            dh = mc(h, axis, periodic)*stencil
            de = mc(h, axis, periodic, other=z)*stencil
            hm, hp, ha, hb, fa, fb = hydrostatic_faces(h, z, dh, de, axis, periodic,
                reconstruction=True)
            selection = [slice(None), slice(None)]; selection[axis] = slice(1, None)
            ha, hb, fa, fb = [v[tuple(selection)].copy() for v in (ha, hb, fa, fb)]
            neighbor = np.roll(h, -1, axis)
            active = np.ones(h.shape, dtype=bool)
            if not periodic:
                endpoint = [slice(None), slice(None)]; endpoint[axis] = -1
                active[tuple(endpoint)] = False
            if h.shape[axis] == 1:
                active[:] = False
            aa, ca, ab, cb, own, other = [np.zeros(h.shape) for _ in range(6)]
            for point in map(tuple, np.argwhere(active)):
                hi, hj = float(h[point]), float(neighbor[point])
                total = Fraction(hi)+Fraction(hj)
                if total:
                    own[point] = represented_float(Fraction(hi)/total)
                    other[point] = represented_float(Fraction(hj)/total)
                aa[point], ca[point] = transfer_coefficients(hi, ha[point], fa[point], pressure_trace=pressure_trace)
                ab[point], cb[point] = transfer_coefficients(hj, hb[point], fb[point], pressure_trace=pressure_trace)
            # Self-column pressure change and within-cell bed traction. These
            # are essential when h and bed vary across the MC polynomial.
            local_p = (np.divide(dh, h, out=np.zeros_like(h), where=h > 0)
                       if pressure_trace == 'mean_column' else np.zeros_like(h))
            local_b = de-dh
            edge = dict(aa=aa, ca=ca, ab=ab, cb=cb, own=own, other=other,
                        local_p=local_p, local_b=local_b)
            if bed_quadrature == 'shared_bottom':
                # Use one bottom-pressure trace own*Bi+other*Bj for BOTH
                # one-sided cut profiles. The resulting off-diagonal traction
                # coefficient is symmetric: own*other*(Cb-Ca). Determine its
                # diagonal from the physical constant-bottom-pressure moment.
                # This also preserves E(1)=bed_slope and total bed force.
                shared_b = np.zeros_like(h)
                for point in map(tuple, np.argwhere(active)):
                    shared_b[point] = represented_float(Fraction(float(own[point]))*
                        Fraction(float(other[point]))*(Fraction(float(cb[point]))-Fraction(float(ca[point]))))
                edge['shared_b'] = shared_b
                edge['physical_b'] = np.where(h > 0, physical_slope[..., component], 0.)
            polynomial = dict(hm=hm.copy(), hp=hp.copy(), ha=ha, hb=hb, fa=fa, fb=fb,
                              dh=dh.copy(), deta=de.copy())
            for value in (*edge.values(), *polynomial.values()):
                value.flags.writeable = False
            self.edges.append(edge); self.polynomials.append(polynomial)

    def _scalar(self, value):
        value = np.asarray(value, dtype=float)
        if value.shape != self.h.shape or not np.isfinite(value).all():
            raise ValueError('Invalid pressure scalar field')
        return value

    def gradient_traction(self, integrated, bottom):
        """Return L(P,B); the momentum pressure force is its negative."""
        p, b = self._scalar(integrated), self._scalar(bottom)
        if np.any(p[self.h == 0] != 0) or np.any(b[self.h == 0] != 0):
            raise ValueError('Dry cells have no pressure column')
        return self._pressure_action(p, b)

    def scalar_gradient(self, scalar):
        """G=-D^T on scalar traces, distinct from a physical pressure column.

        A directional entering-velocity trace can be finite at zero depth.
        Physical pressure still must be zero there in gradient_traction.
        """
        return self._pressure_action(self._scalar(scalar), np.zeros_like(self.h))

    def _pressure_action(self, p, b):
        result = []
        for axis, edge in zip((1, 0), self.edges):
            shared_bottom = self.bed_quadrature == 'shared_bottom'
            ta = edge['aa']*p+(0. if shared_bottom else edge['ca']*b)
            tb = edge['ab']*np.roll(p, -1, axis)+(0. if shared_bottom else edge['cb']*np.roll(b, -1, axis))
            jump = tb-ta
            value = edge['own']*jump+np.roll(edge['other']*jump, 1, axis)+edge['local_p']*p
            result.append(value/self.dx+self._shared_bottom_action(b, axis, edge) if shared_bottom
                          else (value+edge['local_b']*b)/self.dx)
        value = np.stack(result, axis=-1)
        if not np.isfinite(value).all():
            raise ValueError('Pressure geometry action exceeds storage range')
        return value

    @property
    def kinematic_support(self):
        return self.h > 0

    def _shared_bottom_action(self, value, axis, edge):
        k = edge['shared_b']
        return edge['physical_b']*value+(k*(np.roll(value, -1, axis)-value)
            +np.roll(k, 1, axis)*(np.roll(value, 1, axis)-value))/self.dx

    def kinematic_components(self, velocity):
        """Return D u and E u, the signed transposes of the SAME force assembly."""
        v = np.asarray(velocity, dtype=float)
        if v.shape != (*self.h.shape, 2) or not np.isfinite(v).all():
            raise ValueError('Invalid pressure velocity field')
        d, e = np.zeros_like(self.h), np.zeros_like(self.h)
        for component, (axis, edge) in enumerate(zip((1, 0), self.edges)):
            u = v[..., component]
            face_u = edge['own']*u+edge['other']*np.roll(u, -1, axis)
            d += (edge['aa']*face_u-np.roll(edge['ab']*face_u, 1, axis)-edge['local_p']*u)/self.dx
            e += (self._shared_bottom_action(u, axis, edge) if self.bed_quadrature == 'shared_bottom' else
                  (-edge['ca']*face_u+np.roll(edge['cb']*face_u, 1, axis)+edge['local_b']*u)/self.dx)
        if not np.isfinite(d).all() or not np.isfinite(e).all():
            raise ValueError('Pressure geometry kinematics exceeds storage range')
        return d, e

    def prescribed_divergence_lift(self, boundary_velocity):
        """Original prescribed face-normal velocity and partial-time-rate lift.

        Packed west/east/south/north traces use positive x/y orientation. Only
        the affine divergence changes; the homogeneous D/E correction and its
        pressure adjoint remain paired. This is not a transparent boundary.
        The bed moment already uses the constructor's physical exterior bed.
        """
        if self.periodic:
            raise ValueError('Prescribed pressure trace cannot wrap periodically')
        trace = np.asarray(boundary_velocity, dtype=float)
        ny, nx = self.h.shape
        if trace.shape != (2*(nx+ny), 2) or not np.isfinite(trace).all():
            raise ValueError('Invalid prescribed pressure boundary trace')
        result = np.zeros((*self.h.shape, 2))
        result[:, 0] -= trace[:ny]/self.dx
        result[:, -1] += trace[ny:2*ny]/self.dx
        result[0, :] -= trace[2*ny:2*ny+nx]/self.dx
        result[-1, :] += trace[2*ny+nx:]/self.dx
        return np.where(self.kinematic_support[..., None], result, 0.)
