"""Vectorized native cell-center samples; no padding/clamping of missing fields."""
import numpy as np


def sample_centers(field, positions, origin, spacing):
    field, positions = np.asarray(field), np.asarray(positions, float)
    origin, spacing = np.asarray(origin, float), np.asarray(spacing, float)
    if (field.ndim != 3 or positions.ndim != 2 or positions.shape[1] != 3
            or origin.shape != (3,) or spacing.shape != (3,) or np.any(spacing <= 0)
            or not all(np.isfinite(a).all() for a in (field, positions, origin, spacing))):
        raise ValueError('Finite scalar field, positions and positive mapping required')
    coordinates = (positions-origin)/spacing-.5
    base = np.floor(coordinates).astype(int)
    valid = np.all((base >= 0) & (base+1 < np.array(field.shape)), axis=1)
    values = np.full(len(positions), np.nan)
    ids, fraction = base[valid], coordinates[valid]-base[valid]
    result = np.zeros(len(ids))
    for bit in ((i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)):
        corner = ids+bit
        weight = np.prod(np.where(np.array(bit), fraction, 1-fraction), axis=1)
        result += weight*field[corner[:, 0], corner[:, 1], corner[:, 2]]
    values[valid] = result
    return values, valid
