import numpy as np
import pytest
from total_depth_bank_replay import rate, advance, momentum_faces, ReplayExhausted
from detail_nonlinear_flux import simple_wave


@pytest.mark.parametrize('depth', [1e-20, 1e-40, 1e-100])
@pytest.mark.parametrize('second_order', [False, True])
def test_tiny_incoming_water_is_not_canceled_while_momentum_survives(depth, second_order):
    state = np.zeros((1, 2, 3)); state[0, 1] = [depth, 5*depth, 0]
    derivative, _ = rate(state, np.zeros((1, 2)), .5, second_order=second_order)
    assert derivative[0, 0, 0] > 0
    np.testing.assert_allclose(derivative[0, 0, 0], depth*np.sqrt(9.81*depth), rtol=1e-14, atol=0)
    assert abs(derivative[0, 0, 1]/derivative[0, 0, 0]) < 6
    final, stats = advance(state, np.zeros((1, 2)), .5, .01, second_order=second_order)
    assert stats['elapsed_s'] == .01
    assert np.all(final[..., 0] >= 0)
    assert abs(stats['volume_error_m3']) <= 1e-14*depth


def test_exhaustion_preserves_last_admissible_state_and_reason():
    state = np.zeros((3, 7, 3)); state[..., 0] = 1
    with pytest.raises(ReplayExhausted) as failure:
        advance(state, np.zeros((3, 7)), .5, .1, max_trials=1, second_order=True)
    error = failure.value
    np.testing.assert_array_equal(error.state, state)
    assert error.diagnostics['steps'] == 1
    assert error.diagnostics['elapsed_s'] == 1/120
    assert error.diagnostics['maximum_speed_mps'] == 0
    assert error.diagnostics['maximum_depth_m'] == 1
    assert error.diagnostics['exhaustion_reason'] == 'trial_budget'
    assert error.diagnostics['pressure_solver'] == {}


def test_first_stage_failure_retains_previous_accepted_state(monkeypatch):
    import total_depth_bank_replay as bank
    original = bank.rate; calls = 0
    def fail_after_one_step(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3: raise ValueError('Injected pressure failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(bank, 'rate', fail_after_one_step)
    state = np.zeros((3, 7, 3)); state[..., 0] = 1
    with pytest.raises(bank.ReplayInvalidRate) as failure:
        bank.advance(state, np.zeros((3, 7)), .5, .1, second_order=True)
    np.testing.assert_array_equal(failure.value.state, state)
    assert failure.value.diagnostics['elapsed_s'] == 1/120
    assert failure.value.diagnostics['steps'] == 1
    assert failure.value.diagnostics['error'] == 'Injected pressure failure'


@pytest.mark.parametrize('second_order', [False, True])
def test_thin_water_motion_is_independent_of_vertical_datum(second_order):
    x = np.arange(21)
    h = 1e-12*(2+np.sin(2*np.pi*x/21))
    state = np.stack((h, h*(1+.2*np.cos(2*np.pi*x/21)), .3*h), axis=-1)[None]
    bed = np.zeros((1, 21))
    expected, expected_dt = rate(state, bed, .5, second_order=second_order, periodic=True)
    actual, dt = rate(state, bed+1e6, .5, second_order=second_order, periodic=True)
    np.testing.assert_array_equal(actual, expected)
    assert dt == expected_dt


def test_thin_layer_on_linear_bed_retains_gravity_acceleration():
    # Limiting the free-surface slope by depth suppresses downhill gravity,
    # although positivity already follows from the separate MC depth slope.
    dx, slope, depth = .5, .1, 1e-4
    bed = np.broadcast_to(slope*dx*np.arange(11), (3, 11)).copy()
    state = np.zeros((3, 11, 3)); state[..., 0] = depth
    derivative, _ = rate(state, bed, dx, second_order=True)
    np.testing.assert_allclose(derivative[1, 3:-3, 0], 0, atol=1e-15)
    np.testing.assert_allclose(derivative[1, 3:-3, 1], -9.81*depth*slope, atol=1e-15)
    np.testing.assert_allclose(derivative[1, 3:-3, 2], 0, atol=1e-15)


def test_reconstructed_faces_preserve_momentum_and_velocity_bounds():
    rng = np.random.default_rng(8140)
    h = 10**rng.uniform(-12, .5, (19, 23))
    u = rng.uniform(-5, 5, (*h.shape, 2))
    dh = rng.uniform(-1.98, 1.98, h.shape)*h
    du = rng.uniform(-4, 4, u.shape)
    low, high = u-rng.uniform(0, 2, u.shape), u+rng.uniform(0, 2, u.shape)
    qm, qp = momentum_faces(h, u, dh, du, low, high)
    np.testing.assert_allclose(.5*(qm+qp), h[..., None]*u, atol=5e-15, rtol=5e-15)
    for q, depth in ((qm, h-.5*dh), (qp, h+.5*dh)):
        v = q/depth[..., None]
        assert np.all(v >= low-1e-14) and np.all(v <= high+1e-14)


@pytest.mark.parametrize('second_order', [False, True])
def test_lake_at_rest_with_emergent_dry_banks(second_order):
    bed = np.arange(35).reshape(5, 7)*.1
    state = np.zeros((5, 7, 3)); state[..., 0] = np.maximum(0, 2-bed)
    final, stats = advance(state, bed, .5, .2, second_order=second_order)
    np.testing.assert_allclose(final, state, atol=2e-14, rtol=0)
    assert abs(stats['volume_error_m3']) < 1e-13


@pytest.mark.parametrize('second_order', [False, True])
def test_previous_eta_flux_counterexample_does_not_drain_empty_bank(second_order):
    bed = -np.array([[.02, 1.]])
    state = np.zeros((1, 2, 3)); state[0, :, 0] = [1e-12, .9]
    derivative, _ = rate(state, bed, .5, second_order=second_order)
    assert derivative[0, 0, 0] >= -1e-10
    final, stats = advance(state, bed, .5, 5, second_order=second_order)
    assert stats['elapsed_s'] == 5
    assert np.min(final[..., 0]) >= 0
    assert abs(stats['volume_error_m3']) < 1e-12


@pytest.mark.parametrize('second_order', [False, True])
def test_dam_break_wets_dry_cells_without_mass_repair(second_order):
    bed = np.zeros((9, 31)); state = np.zeros((9, 31, 3)); state[:, :8, 0] = 1
    final, stats = advance(state, bed, .5, .5, second_order=second_order)
    assert final[4, 9, 0] > .01
    assert stats['minimum_depth_m'] >= 0
    assert abs(stats['volume_error_m3']) < 1e-12
    bad = state.copy(); bad[0, 15, 1] = .01
    with pytest.raises(ValueError): rate(bad, bed, .5)


def test_second_order_analytic_finite_amplitude_steepening():
    errors = []
    for count in (200, 400):
        dx = 40/count; x = (np.arange(count)+.5)*dx
        initial = simple_wave(x, 0)
        h = initial[:, 0]+1.5
        state = np.stack((h, initial[:, 1]+.4*h, initial[:, 2]), axis=-1)[None]
        final, stats = advance(state, np.zeros((1, count)), dx, 1.2, second_order=True, periodic=True)
        exact = simple_wave(x, 1.2)[:, 0]+1.5
        errors.append(float(np.mean(abs(final[0, :, 0]-exact))))
        assert abs(stats['volume_error_m3']) < 1e-11
    assert errors[1] < .4*errors[0]
    assert errors[1] < .001
