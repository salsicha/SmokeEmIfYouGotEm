"""Integrate trilinear liquid/solid level-set intersections by midpoint sampling.

Samples are cell-centered. Edge values extend constantly through the outer
half cells, so the integration covers the full physical domain. This measures
reconstructed interface volume, NOT conserved particle mass or resolved air.
"""
import numpy as np


def _interval_data(phi, solid_phi, spacing):
    phi = np.asarray(phi, dtype=np.float64)
    solid_phi = np.asarray(solid_phi, dtype=np.float64)
    spacing = np.asarray(spacing, dtype=np.float64)
    if phi.ndim != 3 or min(phi.shape) < 2 or solid_phi.shape != phi.shape:
        raise ValueError('Expected matching nondegenerate 3D cell-center fields')
    if spacing.shape != (3,) or not np.isfinite(spacing).all() or not (spacing > 0).all():
        raise ValueError('Need positive finite physical cell spacing')
    if not np.isfinite(phi).all() or not np.isfinite(solid_phi).all():
        raise ValueError('Nonfinite level set')

    # Padded values are located at domain boundaries and original centers.
    # Thus boundary intervals have half the width of interior intervals.
    bits = np.array([(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    corners = []
    for field in (phi, solid_phi):
        padded = np.pad(field, 1, mode='edge')
        corners.append(np.stack([padded[i:i+phi.shape[0]+1,
                                        j:j+phi.shape[1]+1,
                                        k:k+phi.shape[2]+1].ravel()
                                 for i, j, k in bits], axis=1))
    liquid, solid = corners
    widths = [np.r_[.5, np.ones(n-1), .5]*h for n, h in zip(phi.shape, spacing)]
    volumes = (widths[0][:, None, None]*widths[1][None, :, None]*widths[2][None, None, :]).ravel()
    full = (liquid.max(axis=1) < 0) & (solid.min(axis=1) >= 0)
    empty = (liquid.min(axis=1) >= 0) | (solid.max(axis=1) < 0)
    cut = np.flatnonzero(~(full | empty))
    return bits, liquid, solid, volumes, full, empty, cut


def reconstructed_volume(phi, solid_phi, spacing, subdivisions=8, chunk_size=256,
                         return_interval_volumes=False):
    if subdivisions not in (2, 4, 8, 16, 32) or chunk_size < 1:
        raise ValueError('Use supported quadrature refinement and a positive chunk size')
    bits, liquid, solid, volumes, full, empty, cut = _interval_data(phi, solid_phi, spacing)
    volume = float(volumes[full].sum())
    contributions = np.where(full, volumes, 0.) if return_interval_volumes else None

    q = (np.arange(subdivisions)+.5)/subdivisions
    points = np.stack(np.meshgrid(q, q, q, indexing='ij'), axis=-1).reshape(-1, 3)
    weights = np.stack([np.prod(np.where(bit, points, 1-points), axis=1) for bit in bits])
    for start in range(0, len(cut), chunk_size):
        ids = cut[start:start+chunk_size]
        inside = (liquid[ids] @ weights < 0) & (solid[ids] @ weights >= 0)
        partial = inside.mean(axis=1)*volumes[ids]
        volume += float(partial.sum())
        if contributions is not None:
            contributions[ids] = partial
    result = dict(volume_m3=volume, quadrature_subdivisions=subdivisions,
                full_intervals=int(full.sum()), empty_intervals=int(empty.sum()),
                cut_intervals=int(len(cut)), covered_domain_volume_m3=float(volumes.sum()))
    if contributions is not None:
        # Intervals include both outer half cells, indexed 0..shape[axis].
        # Their contributions form a complete nonoverlapping decomposition.
        result['interval_volumes_m3'] = contributions.reshape(tuple(n+1 for n in np.shape(phi)))
    return result


def reconstructed_volume_bounds(phi, solid_phi, spacing, subdivisions=16, chunk_size=128):
    """Bound volume of these trilinear fields, not unknown continuum liquid.

    A multilinear polynomial attains its extrema at box corners. Each fine
    subinterval is entirely inside, entirely outside, or uncertain. Summing
    entire-inside and possible-inside volumes gives lower and upper bounds.
    A small roundoff guard makes near-zero corners uncertain, not definitive.
    """
    if subdivisions not in (2, 4, 8, 16, 32) or chunk_size < 1:
        raise ValueError('Use supported refinement and a positive chunk size')
    bits, liquid, solid, volumes, full, empty, cut = _interval_data(phi, solid_phi, spacing)
    # Reclassify full/empty coarse boxes with the same roundoff guard.
    eps = 1e-10*max(1., float(np.max(np.abs(liquid))), float(np.max(np.abs(solid))))
    full = (liquid.max(axis=1) < -eps) & (solid.min(axis=1) > eps)
    empty = (liquid.min(axis=1) > eps) | (solid.max(axis=1) < -eps)
    cut = np.flatnonzero(~(full | empty))
    lower = upper = float(volumes[full].sum())
    q = np.arange(subdivisions+1)/subdivisions
    points = np.stack(np.meshgrid(q, q, q, indexing='ij'), axis=-1).reshape(-1, 3)
    weights = np.stack([np.prod(np.where(bit, points, 1-points), axis=1) for bit in bits])
    n = subdivisions
    for start in range(0, len(cut), chunk_size):
        ids = cut[start:start+chunk_size]
        f = (liquid[ids] @ weights).reshape(-1, n+1, n+1, n+1)
        s = (solid[ids] @ weights).reshape(-1, n+1, n+1, n+1)
        entirely = np.ones((len(ids), n, n, n), bool)
        liquid_possible = np.zeros_like(entirely)
        solid_possible = np.zeros_like(entirely)
        for i, j, k in bits:
            fv, sv = f[:, i:i+n, j:j+n, k:k+n], s[:, i:i+n, j:j+n, k:k+n]
            entirely &= (fv < -eps) & (sv > eps)
            liquid_possible |= fv <= eps
            solid_possible |= sv >= -eps
        lower += float(entirely.mean(axis=(1, 2, 3)) @ volumes[ids])
        upper += float((liquid_possible & solid_possible).mean(axis=(1, 2, 3)) @ volumes[ids])
    return dict(lower_m3=lower, upper_m3=upper, width_m3=upper-lower,
                subdivisions=subdivisions, roundoff_guard_levelset_units=eps,
                scope='Bounds of the supplied trilinear fields only; not conserved mass or spatial CFD convergence.')
