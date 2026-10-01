"""Supported trilinear sampling of native lower-face MAC liquid velocities.

No extension, path clamping, surface projection, or replacement of missing data.
"""
import numpy as np

BITS = np.array([(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)])


def trilinear(array, coordinate):
    coordinate = np.asarray(coordinate, dtype=float)
    base = np.floor(coordinate).astype(int)
    if np.any(base < 0) or np.any(base+1 >= np.asarray(array.shape[:3])):
        return None
    fraction = coordinate-base
    ids = base+BITS
    weights = np.prod(np.where(BITS, fraction, 1-fraction), axis=1)
    return np.tensordot(weights, array[ids[:, 0], ids[:, 1], ids[:, 2]], axes=(0, 0))


class DenseMacField:
    def __init__(self, phi, solid, velocity, origin, spacing, velocity_scale):
        self.phi, self.solid, self.velocity = map(np.asarray, (phi, solid, velocity))
        self.origin, self.spacing = map(lambda x: np.asarray(x, float), (origin, spacing))
        self.scale = float(velocity_scale)
        if (self.phi.ndim != 3 or min(self.phi.shape) < 3 or self.solid.shape != self.phi.shape
                or self.velocity.shape != (*self.phi.shape, 3)
                or self.origin.shape != (3,) or self.spacing.shape != (3,)
                or not np.all(self.spacing > 0) or not np.isfinite(self.scale) or self.scale <= 0
                or not all(np.isfinite(x).all() for x in
                           (self.phi, self.solid, self.velocity, self.origin, self.spacing))):
            raise ValueError('Need finite matching fields, positive mapping and calibrated velocity scale')
        liquid = (self.phi < 0) & (self.solid >= 0)
        self.face_support = []
        for axis in range(3):
            supported = np.zeros_like(liquid)
            lower, upper = [slice(None)]*3, [slice(None)]*3
            lower[axis], upper[axis] = slice(None, -1), slice(1, None)
            supported[tuple(upper)] = liquid[tuple(lower)] & liquid[tuple(upper)]
            self.face_support.append(supported)

    def sample(self, position):
        cell = (np.asarray(position)-self.origin)/self.spacing
        center = cell-.5
        base = np.floor(center).astype(int)
        if np.any(base < 0) or np.any(base+1 >= np.array(self.phi.shape)):
            return None
        # Require all eight center neighbors to be liquid and outside solid,
        # not just a negative interpolated value at a possible interface.
        sl = tuple(slice(i, i+2) for i in base)
        if not (np.all(self.phi[sl] < 0) and np.all(self.solid[sl] >= 0)):
            return None
        result = []
        for axis in range(3):
            face = cell-.5
            face[axis] += .5  # Component axis samples its lower face.
            face_base = np.floor(face).astype(int)
            if np.any(face_base < 0) or np.any(face_base+1 >= np.array(self.phi.shape)):
                return None
            face_sl = tuple(slice(i, i+2) for i in face_base)
            if not self.face_support[axis][face_sl].all():
                return None
            value = trilinear(self.velocity[..., axis], face)
            if value is None:
                return None
            result.append(value*self.scale)
        return np.array(result)
