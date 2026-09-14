from fractions import Fraction
import numpy as np
import pytest
from continuous_shoreline_reconstruction import factors
from total_depth_bank_replay import advance, rate, hydrostatic_faces, momentum_faces, mc
from detail_nonlinear_flux import simple_wave
from audit_recorded_shoreline_sensitivity import probe
from adaptive_hydrostatic_precision import refine_faces


def test_limiter_is_continuous_at_blocked_face_without_depth_threshold():
    hp = np.array([[.25]]); hm = np.array([[.75]])
    for value in (0., 1e-30, 1e-15, 1e-7, .125, .25):
        actual = factors(hm, hp, np.array([[0., value]]), np.array([[.75, 0.]]), 1)
        assert actual.item() == value/.25


@pytest.mark.parametrize('depth', [1e-4, 2.**-126, 2.**-300])
@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_uniform_film_preserves_gravity_not_artificial_stair_blockage(depth,limiter):
    # Exact dyadic bed increments isolate genuine thin-film behavior from
    # input rounding of a supposedly linear bed.
    dx, slope = .5, .125
    bed = np.broadcast_to(slope*dx*np.arange(13), (3, 13)).copy()
    state = np.zeros((3, 13, 3)); state[..., 0] = depth
    actual, _ = rate(state, bed, dx, second_order=True, shoreline_limiter=limiter)
    np.testing.assert_allclose(actual[1, 4:-4, 1], -9.81*depth*slope, rtol=3e-14, atol=0)
    np.testing.assert_allclose(actual[1, 4:-4, [0, 2]], 0, atol=1e-15*depth)


@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_resting_lake_and_emergent_banks_remain_balanced(limiter):
    bed = np.arange(35).reshape(5, 7)*.1
    state = np.zeros((5, 7, 3)); state[..., 0] = np.maximum(0, 2-bed)
    final, stats = advance(state, bed, .5, .2, second_order=True, shoreline_limiter=limiter)
    np.testing.assert_allclose(final, state, atol=2e-14, rtol=0)
    assert abs(stats['volume_error_m3']) < 1e-13


@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_fractional_shoreline_slopes_preserve_exact_represented_lake(limiter):
    y, x = np.indices((13, 17)); bed = .125*(x+y)
    state = np.zeros((13, 17, 3)); state[..., 0] = np.maximum(0, 1-bed)
    actual, _ = rate(state, bed, .5, second_order=True, shoreline_limiter=limiter)
    np.testing.assert_array_equal(actual, np.zeros_like(actual))


@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_dry_bed_dam_break_preserves_mass_and_wets_downstream(limiter):
    state = np.zeros((9, 31, 3)); state[:, :8, 0] = 1
    final, stats = advance(state, np.zeros((9, 31)), .5, .5,
        second_order=True, shoreline_limiter=limiter)
    assert final[4, 9, 0] > .01
    assert stats['minimum_depth_m'] >= 0
    assert abs(stats['volume_error_m3']) < 1e-12


def test_convex_polynomial_preserves_cell_mass_momentum_and_velocity_bounds():
    rng = np.random.default_rng(29389)
    h = 10**rng.uniform(-15, .5, (11, 17)); u = rng.uniform(-5, 5, (*h.shape, 2))
    f = rng.uniform(0, 1, h.shape)
    dh = mc(h, 1, True)*f; du = mc(u, 1, True)*f[..., None]
    low = np.minimum(u, np.minimum(np.roll(u, 1, 1), np.roll(u, -1, 1)))
    high = np.maximum(u, np.maximum(np.roll(u, 1, 1), np.roll(u, -1, 1)))
    qm, qp = momentum_faces(h, u, dh, du, low, high)
    hm, hp = h-.5*dh, h+.5*dh
    assert np.min(hm) > 0 and np.min(hp) > 0
    np.testing.assert_allclose(.5*(hm+hp), h, rtol=3e-16, atol=0)
    np.testing.assert_allclose(.5*(qm+qp), h[..., None]*u, rtol=2e-14, atol=1e-25)
    for q, hh in ((qm, hm), (qp, hp)):
        v = q/hh[..., None]
        assert np.all(v >= low-2e-14) and np.all(v <= high+2e-14)


def test_exact_fallback_uses_scaled_polynomial_not_original_slope():
    h = np.array([[.2, .25, 1., 2., 3., .2]])
    bed = np.zeros_like(h); f = np.full_like(h, .75)
    dh = mc(h, 1, False)*f
    bed[0, 1] = .5
    de = mc(h, 1, False, other=bed)*f
    out = hydrostatic_faces(h, bed, dh, de, 1, False, reconstruction=True, slope_factors=f)
    assert out[0][0, 2] == float(Fraction(1)-Fraction(7, 8)*Fraction(3, 4)/2)
    # Force the conservative precision branch on every reduced face. It must
    # use the scaled rational MC polynomial, not silently restore the raw one.
    hm, hp, ha, hb, sa, sb = [v.copy() for v in out]
    sa[:] = np.nan; sb[:] = np.nan
    refine_faces(h, bed, 1, False, None, True, None, hm, hp, ha, hb, sa, sb,
        np.zeros_like(sa), np.zeros_like(sb), slope_factors=f)
    np.testing.assert_array_equal(ha, out[2]); np.testing.assert_array_equal(hb, out[3])
    np.testing.assert_allclose(sa, out[4], rtol=3e-16, atol=0)
    np.testing.assert_allclose(sb, out[5], rtol=3e-16, atol=0)


def test_candidate_does_not_change_default_or_mutate_inputs():
    rng = np.random.default_rng(6021); bed = rng.uniform(0, 1, (5, 9))
    state = np.zeros((5, 9, 3)); state[..., 0] = rng.uniform(.1, 1, bed.shape)
    old_state, old_bed = state.copy(), bed.copy()
    before, _ = rate(state, bed, .5, second_order=True)
    probe(state, bed, .5, None, limiter='continuous')
    after, _ = rate(state, bed, .5, second_order=True)
    np.testing.assert_array_equal(after, before)
    np.testing.assert_array_equal(state, old_state); np.testing.assert_array_equal(bed, old_bed)


@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_candidate_keeps_second_order_finite_amplitude_wave_accuracy(limiter):
    errors = []
    for count in (200, 400):
        dx = 40/count; x = (np.arange(count)+.5)*dx
        initial = simple_wave(x, 0); h = initial[:, 0]+1.5
        state = np.stack((h, initial[:, 1]+.4*h, initial[:, 2]), axis=-1)[None]
        final, stats = advance(state, np.zeros((1, count)), dx, 1.2,
            second_order=True, periodic=True, shoreline_limiter=limiter)
        errors.append(float(np.mean(abs(final[0, :, 0]-(simple_wave(x, 1.2)[:, 0]+1.5)))))
        assert abs(stats['volume_error_m3']) < 1e-11
    assert errors[1] < .4*errors[0] and errors[1] < .001


@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_smooth_variable_bed_transport_retains_second_order_consistency(limiter):
    errors = []
    for count in (80, 160, 320):
        dx = 2*np.pi/count; x = (np.arange(count)+.5)*dx
        h, u, b = 1+.2*np.sin(x), .4+.1*np.cos(x), .1*np.sin(2*x)
        hx, ux, bx = .2*np.cos(x), -.1*np.sin(x), .2*np.cos(2*x)
        state = np.stack((h, h*u, h*0), axis=-1)[None]
        actual, _ = rate(state, b[None], dx, second_order=True, periodic=True,
            shoreline_limiter=limiter)
        expected = np.stack((-(hx*u+h*ux), -(hx*u*u+2*h*u*ux+9.81*h*(hx+bx)), h*0), axis=-1)
        errors.append(float(np.mean(abs(actual[0]-expected))))
    assert errors[1] < .4*errors[0] and errors[2] < .4*errors[1]
