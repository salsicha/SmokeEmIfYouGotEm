"""Independent occupancy reference and scoped omitted-fluid-cell completion.

Completion requires exact native-reference agreement; never edits particles
or classifier thresholds. Not an accepted foam/interface simulation model.
"""
import numpy as np


def occupancy_ratio(flags, radius, fluid_bit, excluded_bits, complete_boundary=False):
    flags = np.asarray(flags)
    if (flags.ndim != 3 or not np.issubdtype(flags.dtype, np.integer)
            or not isinstance(radius, int) or radius < 1
            or min(flags.shape) <= 2*radius+1 or fluid_bit <= 0):
        raise ValueError('Need integer 3D flags and a supported positive radius')
    eligible = (flags & fluid_bit) != 0
    interior = np.zeros(flags.shape, bool)
    interior[1:-1, 1:-1, 1:-1] = True
    counted = interior & ((flags & excluded_bits) == 0)
    fluid = counted & eligible
    total, filled = np.zeros(flags.shape, np.int32), np.zeros(flags.shape, np.int32)
    shape = np.array(flags.shape)
    for offset in np.ndindex(*([2*radius+1]*3)):
        delta = np.array(offset)-radius
        if not delta.any():
            continue
        start, end = np.maximum(0, -delta), np.minimum(shape, shape-delta)
        target = tuple(slice(a, b) for a, b in zip(start, end))
        source = tuple(slice(a, b) for a, b in zip(start+delta, end+delta))
        total[target] += counted[source]
        filled[target] += fluid[source]
    active = np.zeros(flags.shape, bool)
    bound = 1 if complete_boundary else radius
    active[(slice(bound, -bound),)*3] = True
    active &= eligible
    ratio = np.zeros(flags.shape, np.float32)
    np.divide(filled, total, out=ratio, where=active & (total > 0))
    return ratio, total, active


def complete_omitted_fluid_cells(flags, native_ratio, radius, fluid_bit, excluded_bits):
    """Complete only omitted interior-fluid centres using bounded neighbours.

    No synthetic air/liquid halo, threshold change or particle-position change.
    Native interior computation must independently agree before completion.
    """
    ratio = np.asarray(native_ratio)
    if ratio.shape != np.shape(flags) or not np.isfinite(ratio).all():
        raise ValueError('Require matching finite native occupancy')
    reference, _, original_active = occupancy_ratio(flags, radius, fluid_bit, excluded_bits)
    np.testing.assert_array_equal(ratio, reference)
    completed, denominator, complete_active = occupancy_ratio(
        flags, radius, fluid_bit, excluded_bits, complete_boundary=True)
    omitted = complete_active & ~original_active
    if np.any(denominator[omitted] == 0):
        raise ValueError('Omitted fluid cell has no valid neighbours')
    result = ratio.copy()
    result[omitted] = completed[omitted]
    np.testing.assert_array_equal(result[~omitted], ratio[~omitted])
    return result, omitted


def phase_bits(ratio, spray_threshold=.4, bubble_threshold=.77):
    ratio = np.asarray(ratio)
    if (not np.isfinite(ratio).all() or not 0 <= spray_threshold < bubble_threshold <= 1):
        raise ValueError('Finite ratios and ordered occupancy thresholds required')
    return np.where(ratio < spray_threshold, 2, np.where(ratio > bubble_threshold, 4, 8))
