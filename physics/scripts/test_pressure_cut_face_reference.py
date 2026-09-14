from fractions import Fraction as F
import math
import numpy as np
import pytest
from pressure_cut_face_reference import cut_pressure_column, represented_float
from total_depth_nonlinear_pressure import depth_weights, gradient


def quadrature(h, p, b, retained):
    # Independent Simpson integration in sigma is exact for a quadratic profile.
    alpha, beta = 4*b-6*p/h, 6*p/h-3*b
    low = 1-retained/h
    value = lambda s: alpha*(1-s)+beta*(1-s*s)
    return retained*(value(low)+4*value((low+1)/2)+value(1))/6


@pytest.mark.parametrize('p,b', [(3., 2.), (-3., -2.), (3., -8.), (-3., 8.)])
@pytest.mark.parametrize('retained', [0., .01, .5, 1.5, 2.])
def test_exact_complement_and_independent_quadrature(p, b, retained):
    result = cut_pressure_column(2., p, b, retained)
    assert result.transmitted+result.blocked == F(p)
    assert math.isclose(float(result.transmitted), quadrature(2., p, b, retained),
                        rel_tol=1e-11, abs_tol=1e-14)


def test_full_and_closed_columns_keep_pressure_and_tangents():
    full = cut_pressure_column(2, -7, 3, 2, height_rate=.5,
        integrated_rate=-2, bottom_rate=5, retained_height_rate=.5)
    assert full.transmitted == -7 and full.blocked == 0
    assert full.transmitted_rate == -2 and full.blocked_rate == 0
    closed = cut_pressure_column(2, -7, 3, 0, height_rate=.5,
        integrated_rate=-2, bottom_rate=5, retained_height_rate=1)
    assert closed.transmitted == 0 and closed.blocked == -7
    assert closed.transmitted_rate == 0 and closed.blocked_rate == -2


def test_moving_cut_chain_rule_against_complex_step_quadrature():
    values = np.array([2., -3., 4., .7])
    rates = np.array([.3, 1.2, -.8, -.4])
    result = cut_pressure_column(*values, height_rate=rates[0], integrated_rate=rates[1],
        bottom_rate=rates[2], retained_height_rate=rates[3])
    expected = quadrature(*(values+1j*1e-30*rates)).imag/1e-30
    assert math.isclose(float(result.transmitted_rate), expected, rel_tol=1e-14)
    assert result.transmitted_rate+result.blocked_rate == F(float(rates[1]))


def test_closing_integral_is_quadratic_and_tangent_tends_to_zero():
    cuts = [F(1, 10**k) for k in range(2, 9)]
    values = [cut_pressure_column(2, 3, 4, r, retained_height_rate=1) for r in cuts]
    assert all(abs(a.transmitted) > abs(b.transmitted) for a, b in zip(values, values[1:]))
    assert all(abs(a.transmitted_rate) > abs(b.transmitted_rate) for a, b in zip(values, values[1:]))
    # These exact coefficients show the quadratic/linear limits without an
    # arbitrary finite-cut ratio tolerance (the cubic term is still present).
    for retained, value in zip(cuts, values):
        assert value.transmitted/retained**2 == F(1, 4)+retained/4
        assert value.transmitted_rate/retained == F(1, 2)+3*retained/4


def test_positive_subnormal_full_column_without_floor():
    tiny = math.nextafter(0., 1.)
    result = cut_pressure_column(tiny, tiny, 1, tiny)
    assert result.as_floats()['transmitted'] == tiny
    assert result.blocked == 0


def test_intermediate_overflow_and_underflow_do_not_remove_finite_integral():
    # H*B would overflow and r*r would underflow in ordinary binary64 arithmetic.
    result = cut_pressure_column(1e308, 0, 1e308, 1)
    assert math.isclose(result.as_floats()['transmitted'], -1, rel_tol=1e-15)
    assert result.transmitted+result.blocked == 0
    # P/H overflows, although the cut-column integral is comfortably finite.
    result = cut_pressure_column(1e-300, 1e300, 1, 1e-320)
    assert math.isfinite(result.as_floats()['transmitted'])
    assert 2.9e260 < float(result.transmitted) < 3.1e260


def test_unrepresentable_outputs_are_explicit_not_clipped():
    tiny = math.nextafter(0., 1.)
    result = cut_pressure_column(1, tiny, 0, .25)
    assert result.transmitted > 0
    with pytest.raises(ValueError, match='storage range'):
        result.as_floats()
    with pytest.raises(ValueError, match='storage range'):
        represented_float(F(10)**400)


@pytest.mark.parametrize('args,kwargs', [
    ((0, 0, 0, 0), {}), ((-1, 0, 0, 0), {}), ((1, 0, 0, -1), {}),
    ((1, 0, 0, 2), {}), ((math.nan, 0, 0, 0), {}), ((1, math.inf, 0, 0), {}),
    ((True, 0, 0, 0), {}), ((1, 0, 0, 0), {'retained_height_rate': -1}),
    ((1, 0, 0, 1), {'height_rate': -1}), ((1, 0, 0, .5), {'bottom_rate': math.nan})])
def test_invalid_columns_and_outward_tangents_rejected(args, kwargs):
    with pytest.raises(ValueError):
        cut_pressure_column(*args, **kwargs)


def test_harmonic_cubic_pair_weight_is_rejected_by_flat_bed_momentum():
    # Retain the counterexample to the removed, unused connection candidate.
    # Adjointness alone is insufficient: multiplying both face weights by a
    # variable gamma makes D(1) nonzero and destroys the zero-sum pressure force.
    rng = np.random.default_rng(20260914)
    h = rng.uniform(.4, 2., (5, 7)); p = rng.normal(size=h.shape)
    pairs = [np.ones(h.shape, dtype=bool) for _ in range(2)]
    weights = depth_weights(h)
    candidate = []
    for axis, (own, other) in zip((1, 0), weights):
        neighbor = np.roll(h, -1, axis)
        gamma = 2*(h*neighbor)**1.5/(h**3+neighbor**3)
        candidate.append((gamma*own, gamma*other))
    np.testing.assert_allclose(gradient(p, pairs, .5, weights).sum((0, 1)), 0, atol=1e-13)
    net = gradient(p, pairs, .5, candidate).sum((0, 1))
    np.testing.assert_allclose(net, [-2.051002946060499, -.8266024156621109], atol=1e-13)
