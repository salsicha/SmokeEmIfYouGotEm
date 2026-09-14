from fractions import Fraction as F
import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, DryGeometryTransition, mc_dual, positive_dual, kinematic_forcing


def geometry(h, bed, periodic=True):
    return ReconstructedPressureGeometry(h, bed, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


@pytest.mark.parametrize('back,front,bt,ft,expected', [
    (1, 3, 2, -1, F(1, 2)), (1, 3, -2, 1, -4),
    (-1, -3, -2, 1, F(-1, 2)), (0, 0, 1, 2, F(3, 2)),
    (0, 1, 1, 0, 2), (0, 1, -1, 0, 0), (1, -1, 1, 2, 0)])
def test_mc_directional_ties_follow_the_supplied_direction(back, front, bt, ft, expected):
    base, tangent = mc_dual(*map(F, (back, front, bt, ft)))
    assert tangent == expected
    eps = F(1, 10**6)
    later = mc_dual(F(back)+eps*bt, F(front)+eps*ft, F(0), F(0))[0]
    assert (later-base)/eps == expected


def test_cut_boundary_uses_right_derivative_not_a_depth_threshold():
    assert positive_dual(F(0), F(-2)) == (0, 0)
    assert positive_dual(F(0), F(2)) == (0, 2)
    assert positive_dual(F(1, 10**100), F(-2)) == (F(1, 10**100), -2)


def fields():
    rng = np.random.default_rng(404)
    h = rng.uniform(.4, 2, (4, 5)); bed = rng.uniform(0, 2, h.shape)
    ht = rng.normal(size=h.shape)*.03
    u = rng.normal(size=(*h.shape, 2))*.2
    return h, bed, ht, u, rng


@pytest.mark.parametrize('periodic', [False, True])
def test_tangent_actions_match_refined_finite_difference_and_preserve_inputs(periodic):
    h, bed, ht, u, rng = fields()
    p, b = rng.normal(size=h.shape), rng.normal(size=h.shape)
    copies = [v.copy() for v in (h, bed, ht, u, p, b)]
    for value in (h, bed, ht, u, p, b): value.flags.writeable = False
    g = geometry(h, bed, periodic); rate = PressureGeometryRate(g, bed, ht)
    expected_l = rate.force_operator_rate(p, b)
    expected_d, expected_e = rate.kinematic_rate(u)
    errors = []
    for eps in (1e-2, 1e-3, 1e-4):
        plus, minus = geometry(h+eps*ht, bed, periodic), geometry(h-eps*ht, bed, periodic)
        dl = (plus.gradient_traction(p, b)-minus.gradient_traction(p, b))/(2*eps)
        dp, ep = plus.kinematic_components(u); dm, em = minus.kinematic_components(u)
        errors.append(max(abs(dl-expected_l).max(), abs((dp-dm)/(2*eps)-expected_d).max(),
                          abs((ep-em)/(2*eps)-expected_e).max()))
    assert errors[-1] < 2e-10
    assert errors[1] < errors[0]/50
    for before, value in zip(copies, (h, bed, ht, u, p, b)):
        np.testing.assert_array_equal(before, value)
    assert not np.shares_memory(rate.mass_rate, ht)
    assert all(not v.flags.writeable for row in rate.edges for v in row.values())
    assert max(rate.maximum_value_discrepancy.values()) < 1e-14


def test_rate_signed_adjoint_and_constant_bottom_moment_are_exactly_paired():
    h, bed, ht, u, rng = fields()
    g = geometry(h, bed); rate = PressureGeometryRate(g, bed, ht)
    p, b = rng.normal(size=h.shape), rng.normal(size=h.shape)
    d, e = rate.kinematic_rate(u)
    assert abs(np.sum(u*rate.force_operator_rate(p, b))+np.sum(p*d)-np.sum(b*e)) < 1e-13
    np.testing.assert_array_equal(rate.force_operator_rate(np.zeros_like(h), np.ones_like(h)), 0)
    np.testing.assert_array_equal(rate.kinematic_rate(np.ones_like(u))[1], 0)


def test_nonlinear_material_identities_include_both_geometry_rates():
    h, bed, ht, u, rng = fields(); ut = rng.normal(size=u.shape)*.1
    g = geometry(h, bed); rate = PressureGeometryRate(g, bed, ht)
    q, c, adv = kinematic_forcing(g, rate, u)
    d, e = g.kinematic_components(u); da, ea = g.kinematic_components(ut+adv)
    eps = 1e-4
    dp, ep = geometry(h+eps*ht, bed).kinematic_components(u+eps*ut)
    dm, em = geometry(h-eps*ht, bed).kinematic_components(u-eps*ut)
    grad_d = g.gradient_traction(d, np.zeros_like(h))
    grad_e = g.gradient_traction(e, np.zeros_like(h))
    direct_q = d*d-(dp-dm)/(2*eps)-np.sum(u*grad_d, axis=-1)
    direct_c = (ep-em)/(2*eps)+np.sum(u*grad_e, axis=-1)
    np.testing.assert_allclose(q-da, direct_q, atol=2e-10, rtol=0)
    np.testing.assert_allclose(ea+c, direct_c, atol=2e-10, rtol=0)
    dt, et = rate.kinematic_rate(u)
    assert abs(dt).max() > 1e-5 and abs(et).max() > 1e-5


def test_stationary_dry_rows_and_uniform_positive_subnormal_films_need_no_floor():
    h = np.array([[1., 0., 2.]])
    bed = np.array([[0., 2., 0.]])
    g = geometry(h, bed); rate = PressureGeometryRate(g, bed, np.array([[.1, 0., -.1]]))
    q, c, a = kinematic_forcing(g, rate, np.zeros((*h.shape, 2)))
    np.testing.assert_array_equal(q, 0); np.testing.assert_array_equal(c, 0)
    tiny = np.nextafter(0., 1.)
    h = np.full((3, 4), tiny); bed = np.zeros_like(h)
    rate = PressureGeometryRate(geometry(h, bed), bed, np.full_like(h, tiny))
    for row in rate.edges:
        for value in row.values(): np.testing.assert_array_equal(value, 0)


@pytest.mark.parametrize('bad', ['activation', 'negative_dry_rate', 'bed', 'nan', 'shape'])
def test_unqualified_dry_transition_or_mismatched_inputs_are_rejected(bad):
    h = np.ones((3, 4)); h[1, 1] = 0; bed = np.zeros_like(h); ht = np.zeros_like(h)
    g = geometry(h, bed)
    if bad == 'activation': ht[1, 1] = .1
    elif bad == 'negative_dry_rate': ht[1, 1] = -.1
    elif bad == 'bed': bed[0, 0] = .1
    elif bad == 'nan': ht[0, 0] = np.nan
    else: ht = ht[:1]
    with pytest.raises(DryGeometryTransition if bad == 'activation' else ValueError):
        PressureGeometryRate(g, bed, ht)
