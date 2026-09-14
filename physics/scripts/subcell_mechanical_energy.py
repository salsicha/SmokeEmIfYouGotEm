"""Exact nondispersive hydrostatic energy; NOT the full two-pole energy gate."""
import numpy as np


def squared_depth_integral(storage, stage, relative=False):
    if not np.isfinite(stage):
        raise ValueError('Finite stage required')
    levels = storage.relative_levels if relative else storage.levels
    a, b, c = levels.T
    result = np.zeros(len(a))
    full = (stage > a) & (stage >= c)
    h = stage-levels[full]
    result[full] = (np.sum(h*h, axis=1)+h[:, 0]*h[:, 1]+h[:, 0]*h[:, 2]+h[:, 1]*h[:, 2])/6
    low = (stage > a) & (stage <= b) & (stage < c)
    t = stage-a[low]
    result[low] = t**4/(6*(b[low]-a[low])*(c[low]-a[low]))
    high = (stage > b) & (stage < c)
    t, l, r, span = stage-b[high], b[high]-a[high], c[high]-b[high], c[high]-a[high]
    # Integral of 2*V from the middle-height knot, expanded positively.
    # Avoid full signed integral minus dry cap for arbitrarily thin films.
    result[high] = (l**3/6+2*l*l*t/3+l*t*t+t**3*(2/3-t/(6*r)))/span
    return float(storage.areas@result)


def energy(patch, volumes, momenta, gravity=9.81):
    v, p = np.asarray(volumes, float), np.asarray(momenta, float)
    if (v.shape != patch.shape or p.shape != (*patch.shape, 2)
            or not np.isfinite(v).all() or not np.isfinite(p).all() or (v < 0).any()
            or np.any(p[v == 0] != 0) or not np.isfinite(gravity) or gravity <= 0):
        raise ValueError('Finite physical energy state required')
    normalized = np.divide(p, np.sqrt(v)[..., None], out=np.zeros_like(p), where=v[..., None] > 0)
    kinetic = .5*np.sum(normalized*normalized)
    datum = min(float(cell.levels.min()) for cell in patch.cells)
    potential = 0.
    for cell, volume in zip(patch.cells, v.ravel()):
        relative = patch.relative_stages
        stage = cell.relative_stage_for_volume(volume) if relative else cell.stage_for_volume(volume)
        relative_to_datum = (cell.datum-datum)+stage if relative else stage-datum
        potential += gravity*(relative_to_datum*volume-.5*squared_depth_integral(cell, stage, relative))
    if not np.isfinite([kinetic, potential]).all():
        raise ValueError('Mechanical energy exceeds storage range')
    return dict(kinetic=float(kinetic), potential=float(potential), total=float(kinetic+potential),
                reference_datum_m=datum)
