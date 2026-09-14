"""Experimental continuous replacement for binary shoreline slope flattening.

Scale all cell-polynomial slopes by the smaller fraction of owning-face water
that survives hydrostatic reduction. This is a convex blend with the constant
cell polynomial, not a change to conserved averages or supplied bed samples.
There is no depth threshold. A continuous-bed uniform film retains factor one;
approaching a blocked face sends the factor continuously to zero.

This is a project-specific candidate, NOT Skevington's published reconstruction
or a calibrated river model. Convex reconstruction versus sharp switches is
discussed in https://arxiv.org/abs/2106.11273 . Accuracy, wet/dry continuity and
physical validation must be checked separately before runtime promotion.
"""
import numpy as np


def factors(hm, hp, reduced_a, reduced_b, axis):
    if axis not in (0, 1): raise ValueError('Invalid reconstruction axis')
    positive = np.take(reduced_a, range(1, reduced_a.shape[axis]), axis=axis)
    negative = np.take(reduced_b, range(reduced_b.shape[axis]-1), axis=axis)
    if (hm.shape != hp.shape or positive.shape != hp.shape or negative.shape != hm.shape
            or any(not np.isfinite(v).all() or np.any(v < 0) for v in (hm, hp, positive, negative))):
        raise ValueError('Invalid owning-face water depths')
    # A zero polynomial face carries no water and cannot support a slope.
    right = np.divide(positive, hp, out=np.zeros_like(hp), where=hp > 0)
    left = np.divide(negative, hm, out=np.zeros_like(hm), where=hm > 0)
    return np.minimum(1., np.minimum(left, right))
