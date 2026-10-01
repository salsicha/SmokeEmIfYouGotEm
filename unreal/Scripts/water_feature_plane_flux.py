"""Midpoint partial-area flux of bilinear fields on an actual MAC z face.

The face's liquid/solid level sets and z velocity are all located at horizontal
cell centers. Constant extension fills the boundary half intervals. This is
interface quadrature, not an exact source budget or solver mass conservation.
"""
import numpy as np


def partial_face_flux(phi, solid_phi, downward_velocity_mps, spacing_xy, subdivisions=16):
    phi, solid, downward = [np.asarray(a, dtype=np.float64) for a in (phi, solid_phi, downward_velocity_mps)]
    if phi.ndim != 2 or min(phi.shape) < 2 or solid.shape != phi.shape or downward.shape != phi.shape:
        raise ValueError('Need matching nondegenerate horizontal fields')
    if not all(np.isfinite(a).all() for a in (phi, solid, downward)):
        raise ValueError('Nonfinite face field')
    spacing = np.asarray(spacing_xy, dtype=np.float64)
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or not (spacing > 0).all():
        raise ValueError('Need positive finite horizontal spacing')
    if subdivisions not in (2, 4, 8, 16, 32, 64):
        raise ValueError('Unsupported quadrature refinement')
    bits = [(i, j) for i in (0, 1) for j in (0, 1)]
    corners = []
    for a in (phi, solid, downward):
        padded = np.pad(a, 1, mode='edge')
        corners.append(np.stack([padded[i:i+phi.shape[0]+1, j:j+phi.shape[1]+1].ravel()
                                 for i, j in bits], axis=1))
    f, s, v = corners
    widths = [np.r_[.5, np.ones(n-1), .5]*h for n, h in zip(phi.shape, spacing)]
    areas = (widths[0][:, None]*widths[1][None, :]).ravel()
    full = (f.max(axis=1) < 0) & (s.min(axis=1) >= 0)
    empty = (f.min(axis=1) >= 0) | (s.max(axis=1) < 0)
    exact = full & ((v.min(axis=1) >= 0) | (v.max(axis=1) <= 0))
    # For full intervals of one velocity sign, integrate bilinear v exactly.
    flux = v[exact].mean(axis=1)*areas[exact]
    positive, negative = float(flux[flux > 0].sum()), float(-flux[flux < 0].sum())
    area = float(areas[exact].sum())
    ids = np.flatnonzero(~(exact | empty))
    q = (np.arange(subdivisions)+.5)/subdivisions
    points = np.stack(np.meshgrid(q, q, indexing='ij'), axis=-1).reshape(-1, 2)
    weights = np.stack([np.prod(np.where(bit, points, 1-points), axis=1) for bit in bits])
    for start in range(0, len(ids), 256):
        subset = ids[start:start+256]
        mask = (f[subset] @ weights < 0) & (s[subset] @ weights >= 0)
        velocity = v[subset] @ weights
        positive += float((np.maximum(velocity, 0)*mask).mean(axis=1) @ areas[subset])
        negative += float((np.maximum(-velocity, 0)*mask).mean(axis=1) @ areas[subset])
        area += float(mask.mean(axis=1) @ areas[subset])
    return dict(subdivisions=subdivisions, liquid_area_m2=area,
                signed_downward_flux_m3s=positive-negative,
                downward_only_flux_m3s=positive, upward_only_flux_m3s=negative,
                mean_downward_velocity_mps=(positive-negative)/area if area else None,
                covered_domain_area_m2=float(areas.sum()))
