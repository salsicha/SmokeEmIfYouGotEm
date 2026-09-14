"""Exact-triangle vertical kinetic geometry for dispersive coupling RESEARCH.

Integrate the existing completed-square form h*(h*d-1.5*b.u)^2
+ .75*h*(b.u)^2 on the actual wet source triangles. The supplied jet is
(horizontal divergence, velocity_x, velocity_y). This is geometry, not a chosen
intercell derivative, pressure solve, nonlinear closure or wet-front evolution.
"""
import numpy as np


def wet_pieces(storage, height):
    """Positive-area/depth triangulation, relative to the cell's stored datum.

    Only sorted vertex levels, original projected areas and original affine
    bed gradients are needed. No terrain point or slope is displaced or fit.
    """
    if not np.isfinite(height):
        raise ValueError('Finite datum-relative water stage required')
    areas, depths, gradients = [], [], []
    def append(area, h, gradient):
        if area > 0:
            areas.append(area); depths.append(h); gradients.append(gradient)
    for levels, area, gradient in zip(storage.relative_levels, storage.areas, storage.bed_gradients):
        a, b, c = levels
        ha, hb, hc = height-levels
        if ha <= 0:
            continue
        if hc >= 0:
            append(area, [ha, hb, hc], gradient)
        elif hb <= 0:
            # Multiplying the two dimensionless fractions avoids an unnecessary
            # squared-height intermediate before forming the wet area.
            append(area*(ha/(b-a))*(ha/(c-a)), [ha, 0., 0.], gradient)
        else:
            t, s = hb/(c-b), ha/(c-a)
            append(area*t, [ha, hb, 0.], gradient)
            append(area*(1-t)*s, [ha, 0., 0.], gradient)
    return (np.asarray(areas), np.asarray(depths).reshape(-1, 3),
            np.asarray(gradients).reshape(-1, 2))


def quadrature(storage, height):
    """Positive six-node Duffy/Gauss rule, exact for cubic wet-triangle data."""
    areas, vertices, gradients = wet_pieces(storage, height)
    # Triangle barycentrics (1-s, s*(1-t), s*t), Jacobian 2*area*s.
    # Cubic polynomials become degree <=4 in s and <=3 in t. Three-point
    # Gauss in s and two-point Gauss in t therefore integrate them exactly.
    sn = np.array([.5-np.sqrt(15)/10, .5, .5+np.sqrt(15)/10])
    sw = np.array([5/18, 4/9, 5/18])
    tn = np.array([.5-np.sqrt(3)/6, .5+np.sqrt(3)/6])
    barycentric, weights = [], []
    for s, weight in zip(sn, sw):
        for t in tn:
            barycentric.append([1-s, s*(1-t), s*t])
            weights.append(weight*s)  # 2 (Jacobian) * 1/2 (t weight).
    depths = vertices@np.asarray(barycentric).T
    weights = areas[:, None]*np.asarray(weights)[None, :]
    return weights.ravel(), depths.ravel(), np.repeat(gradients, 6, axis=0)


def local_form(storage, volume):
    """Positive kinetic Gram factor and analytic fixed-terrain volume derivative.

    The derivative is piecewise-smooth only. A wet area change at an exactly
    level dry triangle is rejected instead of claiming a two-sided derivative.
    No inverse dry mass or artificial minimum wet volume is introduced.
    """
    if not np.isfinite(volume) or volume <= 0:
        raise ValueError('Strictly positive finite volume required; dry closure is not derived')
    height = storage.relative_stage_for_volume(volume)
    flat_at_stage = np.all(storage.relative_levels == height, axis=1)
    if flat_at_stage.any():
        raise ValueError('Exactly level shoreline has no two-sided volume derivative')
    weights, h, slope = quadrature(storage, height)
    wet_area = float(np.sum(weights))
    if wet_area <= 0 or not np.isfinite(wet_area):
        raise ValueError('Positive volume lacks represented wet geometry')
    represented_volume = float(np.sum(weights*h))
    # Factor each completed square directly; no indefinite matrix eigensolve,
    # negative-eigenvalue clipping or cancellation-based positivity repair.
    root = np.sqrt(weights)*np.sqrt(h)
    first = root[:, None]*np.column_stack((h, -1.5*slope))
    second = np.sqrt(.75)*root[:, None]*np.column_stack((np.zeros_like(h), slope))
    factor = np.concatenate((first, second), axis=0)
    gram = factor.T@factor
    # d/deta integral h^k = k integral h^(k-1); moving wet edges add no
    # boundary term because the original kinetic integrand vanishes at h=0.
    derivative = np.zeros((3, 3))
    derivative[0, 0] = float(np.sum(3*weights*h*h))
    cross = -3*np.sum((weights*h)[:, None]*slope, axis=0)
    derivative[0, 1:] = cross; derivative[1:, 0] = cross
    derivative[1:, 1:] = 3*np.einsum('n,ni,nj->ij', weights, slope, slope)
    derivative /= wet_area
    if not all(np.isfinite(x).all() for x in (factor, gram, derivative)):
        raise ValueError('Exact kinetic geometry exceeds represented range')
    return dict(stage_offset=height, datum=storage.datum, wet_area=wet_area,
        represented_volume=represented_volume, volume_error=abs(represented_volume-volume),
        factor=factor, gram=gram, volume_derivative=derivative,
        depth_moments=np.array([np.sum(weights*h**k) for k in range(4)]),
        intercell_or_two_pole_or_nonlinear_or_dry_or_gameplay_accepted=False)


def energy(form, jet):
    jet = np.asarray(jet, float)
    if jet.shape != (3,) or not np.isfinite(jet).all():
        raise ValueError('Finite divergence and two-component velocity required')
    action = form['factor']@jet
    result = .5*float(action@action)
    derivative = .5*float(jet@form['volume_derivative']@jet)
    if not np.isfinite([result, derivative]).all():
        raise ValueError('Kinetic geometry energy exceeds represented range')
    return result, derivative
