"""Choose isotropic domain dimensions while preserving center and longest axis.

This is an authoring-coordinate correction, not a conservation correction.
Native grid dimensions and cell spacing must still be checked after baking.
"""
import math


def aligned_domain(lower, upper, resolution):
    lower, upper = tuple(lower), tuple(upper)
    if (len(lower) != 3 or len(upper) != 3 or not isinstance(resolution, int)
            or resolution < 3 or not all(math.isfinite(x) for x in (*lower, *upper))
            or any(b <= a for a, b in zip(lower, upper))):
        raise ValueError('Need positive finite three-axis bounds and integral resolution')
    dimensions = [b-a for a, b in zip(lower, upper)]
    spacing = max(dimensions)/resolution
    counts = [int(math.floor(d/spacing+.5)) for d in dimensions]
    if min(counts) < 3:
        raise ValueError('Domain would have fewer than three cells on an axis')
    center = [(a+b)/2 for a, b in zip(lower, upper)]
    aligned = [n*spacing for n in counts]
    return dict(nominal_dimensions_m=dimensions, dimensions_m=aligned,
                expected_grid_cells=counts, isotropic_cell_m=spacing,
                center_m=center, lower_m=[c-d/2 for c, d in zip(center, aligned)],
                upper_m=[c+d/2 for c, d in zip(center, aligned)],
                scope='Center/longest axis preserved; shorter domain bounds move by at most half a cell. Existing collider/source geometry is not rescaled. Native validation required; not physical acceptance.')
