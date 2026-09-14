"""Exact endpoint evaluation experiment; never installed in live replays.

Only R=0 and R=H are specialized, using exact rational equality. Every partial
column still uses the original reference. No tolerance, float approximation,
depth floor, cached state, modified rate or changed pressure polynomial.
"""
from contextlib import contextmanager
from fractions import Fraction
from pressure_cut_face_reference import PressureCut, _exact, cut_pressure_column as original_cut


def cut_pressure_column(height, integrated, bottom, retained_height, *,
                        height_rate=0., integrated_rate=0., bottom_rate=0.,
                        retained_height_rate=0.):
    h, p, b, retained, ht, pt, bt, rt = map(_exact, (height, integrated, bottom,
        retained_height, height_rate, integrated_rate, bottom_rate, retained_height_rate))
    if h <= 0 or retained < 0 or retained > h:
        raise ValueError('Cut requires a positive column and 0 <= retained height <= height')
    if (retained == 0 and rt < 0) or (retained == h and rt > ht):
        raise ValueError('Cut tangent leaves the physical column')
    zero = Fraction(0)
    if retained == 0:
        return PressureCut(zero, p, zero, pt)
    if retained == h:
        # At r=1, f=1, g=0, f'=0, g'=1. Keep the one-sided
        # opening/closing tangent: it is NOT generally just integrated_rate.
        rate = pt+b*(rt-ht)
        return PressureCut(p, zero, rate, pt-rate)
    return original_cut(h, p, b, retained, height_rate=ht,
        integrated_rate=pt, bottom_rate=bt, retained_height_rate=rt)


@contextmanager
def exact_endpoint_cuts():
    """Patch only this isolated process's two imported cut bindings, then restore."""
    import reconstructed_pressure_geometry as geometry
    import reconstructed_pressure_rates as rates
    originals = geometry.cut_pressure_column, rates.cut_pressure_column
    geometry.cut_pressure_column = rates.cut_pressure_column = cut_pressure_column
    try:
        yield
    finally:
        geometry.cut_pressure_column, rates.cut_pressure_column = originals
