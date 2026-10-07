"""Bounded spatial-index equivalent of the evidence builder's vertex projection.

This preserves nearest *sample* stationing, including first-index ties. It does
not substitute continuous segment projection or alter the inferred channel.
"""
import numpy as np
from scipy.spatial import cKDTree


def project(px, py, X, Y, S, LX, LY):
    px, py, X, Y, S, LX, LY = [np.asarray(a, dtype=float) for a in (px, py, X, Y, S, LX, LY)]
    if (any(a.ndim != 1 or not np.isfinite(a).all() for a in (px, py, X, Y, S, LX, LY)) or
            px.shape != py.shape or not len(X) or
            any(a.shape != X.shape for a in (Y, S, LX, LY))):
        raise ValueError('Finite aligned route and query arrays required')
    tree = cKDTree(np.column_stack((X, Y)))
    out_s, out_l = np.empty(len(px)), np.empty(len(px))
    for start in range(0, len(px), 65536):
        stop = min(start+65536, len(px))
        points = np.column_stack((px[start:stop], py[start:stop]))
        distances, indices = tree.query(points, k=2 if len(X)>1 else 1, workers=1)
        if len(X)>1:
            j = indices[:, 0].copy()
            # KD-tree tie order is unspecified. Re-evaluate close candidates
            # using the original squared-distance expression and index order.
            tolerance = 32*np.finfo(float).eps*np.maximum(1., distances[:, 0])
            ties = np.flatnonzero(distances[:, 1]-distances[:, 0] <= tolerance)
            if len(ties):
                nearby = tree.query_ball_point(points[ties], distances[ties, 0]+tolerance[ties], workers=1)
                for row, candidates in zip(ties, nearby):
                    candidates = np.sort(candidates)
                    d2 = (points[row, 0]-X[candidates])**2+(points[row, 1]-Y[candidates])**2
                    j[row] = candidates[int(d2.argmin())]
        else:
            j = indices
        out_s[start:stop] = S[j]
        out_l[start:stop] = (px[start:stop]-X[j])*LX[j]+(py[start:stop]-Y[j])*LY[j]
    return out_s, out_l
