"""Exact, bounded pressure-cut basis reuse; isolated construction experiment.

Reuse is by ALL exact height/cut values and their rates, never by cell/stage or
approximate geometry. Coefficients and outputs remain arbitrary-precision
Fractions; exact subtraction retains tiny blocked slivers without float loss.
"""
from contextlib import contextmanager
from fractions import Fraction
from functools import lru_cache
from pressure_cut_face_reference import PressureCut, _exact


def make_cut_pressure_column(maxsize=4096, metrics=None):
    if type(maxsize) is not int or maxsize <= 0: raise ValueError('Positive bounded basis cache required')
    counts = metrics if metrics is not None else {}
    counts.update(closed=0, full=0, partial=0)
    zero = Fraction(0)

    @lru_cache(maxsize=maxsize)
    def basis(h, retained, ht, rt):
        r = retained/h; r_rate = (rt-r*ht)/h
        square = r*r; complement = 1-r
        a = square*(3-2*r)
        c = -h*square*complement
        a_rate = 6*r*complement*r_rate
        c_rate = -ht*square*complement+h*r*(3*r-2)*r_rate
        return a, c, a_rate, c_rate

    def cut(height, integrated, bottom, retained_height, *, height_rate=0.,
            integrated_rate=0., bottom_rate=0., retained_height_rate=0.):
        h, p, b, retained, ht, pt, bt, rt = map(_exact, (height, integrated, bottom,
            retained_height, height_rate, integrated_rate, bottom_rate, retained_height_rate))
        if h <= 0 or retained < 0 or retained > h:
            raise ValueError('Cut requires a positive column and 0 <= retained height <= height')
        if (retained == 0 and rt < 0) or (retained == h and rt > ht):
            raise ValueError('Cut tangent leaves the physical column')
        if retained == 0:
            counts['closed'] += 1
            return PressureCut(zero, p, zero, pt)
        if retained == h:
            counts['full'] += 1
            rate = pt+b*(rt-ht)
            return PressureCut(p, zero, rate, pt-rate)
        counts['partial'] += 1
        a, c, at, ct = basis(h, retained, ht, rt)
        transmitted = (p*a if p else zero)+(b*c if b else zero)
        rate = ((pt*a if pt else zero)+(p*at if p else zero)
                +(bt*c if bt else zero)+(b*ct if b else zero))
        return PressureCut(transmitted, p-transmitted, rate, pt-rate)
    cut.cache_info = basis.cache_info
    return cut


@contextmanager
def exact_cut_basis(metrics=None, maxsize=4096):
    import reconstructed_pressure_geometry as geometry
    import reconstructed_pressure_rates as rates
    counts = metrics if metrics is not None else {}
    function = make_cut_pressure_column(maxsize, counts)
    originals = geometry.cut_pressure_column, rates.cut_pressure_column
    geometry.cut_pressure_column = rates.cut_pressure_column = function
    try:
        yield counts
    finally:
        geometry.cut_pressure_column, rates.cut_pressure_column = originals
        counts['cache'] = function.cache_info()._asdict()
