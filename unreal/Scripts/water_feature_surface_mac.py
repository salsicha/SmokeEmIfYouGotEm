"""Explicit one-sided affine velocity reconstruction at a liquid interface.

This is a NEW sampling approximation, not native MAC extrapolation, a liquid
solve, or a relaxation of DenseMacField. Only faces with two liquid/non-solid
adjacent centres supply velocity data. Interface queries may use that data's
local affine continuation; unsupported/rank-deficient fits fail, never clamp.
Native field-to-rendered-mesh agreement must be audited separately.
"""
import numpy as np

from water_feature_dense_mac import BITS, DenseMacField, trilinear


class SurfaceMacField:
    def __init__(self, phi, solid, velocity, origin, spacing, velocity_scale,
                 radius_cells=2.5, maximum_condition=100., band_cells=2.):
        self.interior = DenseMacField(phi, solid, velocity, origin, spacing, velocity_scale)
        if (not np.allclose(self.interior.spacing, self.interior.spacing[0], rtol=1e-10, atol=0)
                or not np.isfinite(radius_cells) or not 1.5 <= radius_cells <= 4
                or not np.isfinite(maximum_condition) or maximum_condition <= 1
                or not np.isfinite(band_cells) or band_cells <= 0):
            raise ValueError('Isotropic grid and finite bounded reconstruction settings required')
        self.h = float(self.interior.spacing[0])
        self.radius = float(radius_cells)
        self.condition = float(maximum_condition)
        self.band = float(band_cells)

    def surface(self, position):
        """Trilinear phi and its exact piecewise gradient, in metres.

        Native phi is in isotropic grid cells. No finite-difference gradient
        reaches beyond the eight checked narrow-band/non-solid centres.
        """
        point = np.asarray(position, float)
        if point.shape != (3,) or not np.isfinite(point).all():
            raise ValueError('Finite 3D query required')
        coordinate = (point-self.interior.origin)/self.h-.5
        base = np.floor(coordinate).astype(int)
        if np.any(base < 0) or np.any(base+1 >= self.interior.phi.shape):
            return None
        ids = base+BITS
        phi = self.interior.phi[tuple(ids.T)]
        solid = self.interior.solid[tuple(ids.T)]
        if np.any(np.abs(phi) > self.band) or np.any(solid <= 0):
            return None
        fraction = coordinate-base
        factors = np.where(BITS, fraction, 1-fraction)
        value = float(np.prod(factors, axis=1) @ phi)*self.h
        gradient = np.array([np.sum(phi*np.where(BITS[:, axis], 1., -1.)
                            *np.prod(factors[:, [a for a in range(3) if a != axis]], axis=1))
                            for axis in range(3)])
        if np.linalg.norm(gradient) < 1e-10:
            return None
        return value, gradient

    def sample(self, position, interface_tolerance_cells=1e-6):
        """Return velocity and fit diagnostics, or None on missing support.

        Fits are weighted affine fits in dimensionless local coordinates.
        Residuals are exposed, NOT silently used as physical-accuracy proof.
        This method is for phi=0 only, not a broad replacement for the strict
        interior sampler. Source/query segments require positive solid phi.
        """
        if not np.isfinite(interface_tolerance_cells) or interface_tolerance_cells <= 0:
            raise ValueError('Positive finite interface tolerance required')
        point = np.asarray(position, float)
        surface = self.surface(point)
        if surface is None or abs(surface[0]) > interface_tolerance_cells*self.h:
            return None
        cell = (point-self.interior.origin)/self.h
        lower = np.floor(cell-self.radius-1).astype(int)
        upper = np.ceil(cell+self.radius+1).astype(int)
        lower = np.maximum(lower, 1)
        upper = np.minimum(upper, np.asarray(self.interior.phi.shape)-1)
        if np.any(upper <= lower):
            return None
        ids = np.stack(np.meshgrid(*(np.arange(a, b) for a, b in zip(lower, upper)), indexing='ij'), axis=-1).reshape(-1, 3)
        result, details = [], []
        for axis in range(3):
            offset = np.full(3, .5)
            offset[axis] = 0
            delta = ids+offset-cell
            distance = np.linalg.norm(delta, axis=1)
            eligible = self.interior.face_support[axis][tuple(ids.T)] & (distance <= self.radius)
            face_ids, delta = ids[eligible], delta[eligible]
            # A solid separator must not be bridged by the reconstruction.
            # Spacing <=h/4 along every source/query segment, with a checked
            # positive trilinear solid field. Still NOT exact collider proof.
            clear = []
            for displacement in delta:
                fractions = np.linspace(0, 1, int(np.ceil(np.linalg.norm(displacement)*4))+1)
                solid_values = [trilinear(self.interior.solid, cell+f*displacement-.5) for f in fractions]
                clear.append(all(value is not None and value > 0 for value in solid_values))
            face_ids, delta = face_ids[clear], delta[clear]
            if len(delta) < 8 or np.min(np.linalg.norm(delta, axis=1)) > 1.5:
                return None
            design = np.column_stack((np.ones(len(delta)), delta))
            weights = 1/(1+np.sum(delta*delta, axis=1))
            weighted = design*np.sqrt(weights)[:, None]
            data = self.interior.velocity[tuple(face_ids.T)][..., axis]*self.interior.scale
            coefficients, _, rank, singular = np.linalg.lstsq(weighted, data*np.sqrt(weights), rcond=None)
            if rank != 4 or singular[-1] <= 0 or singular[0]/singular[-1] > self.condition:
                return None
            residual = design @ coefficients-data
            result.append(float(coefficients[0]))
            details.append(dict(source_faces=len(delta), condition=float(singular[0]/singular[-1]),
                                weighted_rms_mps=float(np.sqrt(np.average(residual**2, weights=weights))),
                                maximum_residual_mps=float(np.max(np.abs(residual))),
                                nearest_source_cells=float(np.min(np.linalg.norm(delta, axis=1)))))
        return np.array(result), dict(components=details, radius_cells=self.radius,
            model='One-sided weighted affine continuation from strict liquid/liquid MAC faces',
            accepted=False)

    def manifold_surface(self, positions, time):
        """A frozen snapshot adapter only; no pretend temporal field support."""
        if not np.isfinite(time) or time != 0:
            raise ValueError('Snapshot has no temporal support; supply evolving fields explicitly')
        samples = [self.surface(p) for p in positions]
        if any(sample is None for sample in samples):
            raise ValueError('Unsupported surface query')
        return np.array([s[0] for s in samples]), np.array([s[1] for s in samples])
