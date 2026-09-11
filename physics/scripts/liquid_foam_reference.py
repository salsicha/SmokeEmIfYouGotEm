"""Independent reference for the surface foam transport/reaction, not 2-phase CFD."""
import numpy as np
from analyze_liquid_surface_exchange import sample_grid


def advance_foam(history, velocity, source_rate, dt, extents, age):
    history, velocity, source_rate, extents = (np.asarray(a, dtype=float) for a in (history, velocity, source_rate, extents))
    if history.ndim != 3 or velocity.shape != (*history.shape, 3) or source_rate.shape != history.shape or extents.shape != (3,):
        raise ValueError('Matching volume, velocity and source fields required')
    if not all(np.isfinite(a).all() for a in (history, velocity, source_rate, extents)) or not np.isfinite(dt) or dt <= 0 or (extents <= 0).any() or not np.isfinite(age):
        raise ValueError('Finite fields and positive dimensions/time step required')
    nz, ny, nx = history.shape
    z, y, x = np.meshgrid((np.arange(nz)+.5)/nz, (np.arange(ny)+.5)/ny, (np.arange(nx)+.5)/nx, indexing='ij')
    unit = np.stack((x, y, z), axis=-1)
    back = unit-velocity*dt/extents
    inside = ((back > 0) & (back < 1)).all(axis=-1)
    transported = np.clip(sample_grid(history[..., None], back*extents, minimum=(0, 0, 0), extent=extents)[..., 0], 0, 1)
    transported = np.where(inside & (age > 1.5*dt), transported, 0)
    rate = np.clip(source_rate, 0, 8)
    total = rate+.25
    equilibrium = rate/total
    return np.clip(equilibrium+(transported-equilibrium)*np.exp(-total*dt), 0, 1)
