"""Strict metric layout for live reconstruction evidence, not inferred shapes."""
import numpy as np


def from_report(report):
    names = ('solver_cells', 'render_cells', 'computational_extents_cm')
    present = [name in report for name in names]
    if any(present) and not all(present):
        raise ValueError('Incomplete explicit reconstruction layout')
    if not any(present):
        return dict(solver=[68, 68, 24], render=[136, 136, 48], extent=[2231.25, 2231.25, 800.], half=[1050., 1050.], legacy=True)
    solver = np.asarray(report[names[0]], dtype=float)
    render = np.asarray(report[names[1]], dtype=float)
    extent = np.asarray(report[names[2]], dtype=float)
    if any(a.shape != (3,) or not np.isfinite(a).all() for a in (solver, render, extent)):
        raise ValueError('Finite XYZ layout required')
    if (solver < [6, 6, 4]).any() or (solver > 4096).any() or not np.array_equal(solver, np.floor(solver)) or solver[0] % 2:
        raise ValueError('Integer bounded solver with XY halo required')
    if not np.array_equal(render, 2*solver) or np.prod(render) > 2000000 or (extent <= 0).any():
        raise ValueError('Bounded 2x reconstruction and positive metric extent required')
    half = extent[:2]*(solver[:2]-4)/solver[:2]/2
    return dict(solver=solver.astype(int).tolist(), render=render.astype(int).tolist(),
                extent=extent.tolist(), half=half.tolist(), legacy=False)
