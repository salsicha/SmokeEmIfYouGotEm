"""Spectral estimate for collocated +/-2 pressure, not a convergence gate.

For the parent rectangular Dirichlet box, the eight parity grids have nearest
neighbors two cells apart. Irregular wet geometry has a different spectrum;
the native residual must still be measured. Regional cuts are not boundaries.
"""
import numpy as np


def parent_omega(cells,spacing):
    cells=np.asarray(cells);spacing=np.asarray(spacing,dtype=float)
    if (cells.shape!=(3,) or spacing.shape!=(3,) or not np.isfinite(cells).all() or
            not np.isfinite(spacing).all() or np.any(cells!=np.floor(cells)) or
            np.any(cells<2) or np.any(spacing<=0)):
        raise ValueError('Positive parent XYZ cell counts and metric spacing required')
    nodes=np.ceil(cells/2)
    weights=1/spacing**2
    rho=float(np.sum(weights*np.cos(np.pi/(nodes+1)))/weights.sum())
    return 2/(1+np.sqrt(1-rho*rho))
