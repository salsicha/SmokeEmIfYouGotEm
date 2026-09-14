import numpy as np
import pytest
from nonlinear_detail_replay import Replay, ReplayExhausted
from detail_nonlinear_flux import simple_wave
from finite_depth_pressure_reference import chebyshev_potentials, WEIGHTS


@pytest.mark.parametrize('periodic', [False, True])
def test_pressure_stencil_matches_independent_dense_operator(periodic):
    rng = np.random.default_rng(422)
    flow = np.zeros((5, 6, 4)); flow[..., 0] = rng.uniform(.2, 2, (5, 6)); flow[1:4, 3, 0] = 0
    eta = rng.uniform(-.03, .03, (5, 6)); eta[flow[..., 0] == 0] = 0
    replay = Replay(flow, .5, periodic=periodic)
    potentials, _ = chebyshev_potentials(flow[..., 0], eta, .5, periodic=periodic)
    expected = eta/15 + np.sum(WEIGHTS[:, None, None]*potentials.reshape(2, 5, 6), axis=0)
    np.testing.assert_allclose(replay.pressure(eta), expected, atol=1e-13, rtol=0)


def test_variable_depth_rest_and_dry_cells():
    flow = np.zeros((9, 13, 4)); flow[..., 0] = .2 + np.arange(13)[None, :]*.1
    flow[:, 6, 0] = 0
    state = np.zeros((9, 13, 3)); state[..., 0] = np.where(flow[..., 0] > 0, .04, 0)
    replay = Replay(flow, .5)
    actual, stats = replay.advance(state, .13)
    np.testing.assert_allclose(actual, state, atol=1e-12, rtol=0)
    assert abs(stats['signed_volume_error_m3']) < 1e-12
    np.testing.assert_array_equal(actual[:, 6], 0)
    bad = state.copy(); bad[3, 2, 0] = -1
    with pytest.raises(ValueError):
        replay.advance(bad, .1)


def test_nonlinear_replay_matches_analytic_simple_wave():
    errors = []
    for count in (200, 400):
        dx = 40/count; x = (np.arange(count)+.5)*dx
        flow = np.zeros((1, count, 4)); flow[..., 0] = 1.5; flow[..., 1] = .4
        state = simple_wave(x, 0)[None]
        replay = Replay(flow, dx, dispersive=False, periodic=True, damping=0)
        actual, stats = replay.advance(state, 1.2)
        errors.append(float(np.mean(abs(actual[0, :, 0]-simple_wave(x, 1.2)[:, 0]))))
        assert abs(stats['signed_volume_error_m3']) < 1e-11
        assert stats['elapsed_s'] == 1.2
    assert errors[1] < .4*errors[0]
    assert errors[1] < .001


def test_nearly_drained_cell_keeps_mass_without_height_clamp():
    flow = np.zeros((5, 9, 4)); flow[..., 0] = .1
    state = np.zeros((5, 9, 3)); state[2, 4] = [-.099, .02, -.015]
    replay = Replay(flow, .5, dispersive=False, damping=0)
    actual, stats = replay.advance(state, .05)
    assert stats['minimum_total_depth_m'] > 0
    assert abs(stats['signed_volume_error_m3']) < 1e-12
    assert np.max(abs(actual[..., 0])) > 0


def test_trial_exhaustion_preserves_last_state_and_reason():
    flow = np.zeros((3, 5, 4)); flow[..., 0] = 1
    state = np.zeros((3, 5, 3))
    replay = Replay(flow, .5, dispersive=False)
    with pytest.raises(ReplayExhausted, match='Trial budget exhausted') as caught:
        replay.advance(state, .1, max_trials=1)
    error = caught.value
    assert error.statistics['elapsed_s'] == 1/120
    assert error.statistics['accepted_steps'] == 1
    assert error.statistics['rejected_trials'] == 0
    assert error.diagnostics['bounds']['cfl_step_s'] > 0
    np.testing.assert_array_equal(error.state, state)
    assert error.statistics['signed_volume_error_m3'] == 0


@pytest.mark.parametrize('nonlinear', [False, True])
def test_rejected_candidate_dry_bank_counterexample_is_not_hidden(nonlinear):
    # This is a failure-detector regression, NOT physical acceptance. The
    # perturbation jump at a bed step drains an almost empty shallow cell even
    # with zero mean velocity/strain, zero q, and no dispersive pressure.
    flow = np.zeros((1, 2, 4)); flow[0, :, 0] = [.02, 1.]
    state = np.zeros((1, 2, 3)); state[0, :, 0] = [-.02+1e-12, -.1]
    replay = Replay(flow, .5, nonlinear=nonlinear, dispersive=False, damping=0)
    rate, _ = replay.rate(state)
    assert rate[0, 0, 0] < -.03
    assert rate[..., 0].sum() == 0
    with pytest.raises(ReplayExhausted, match='Admissible timestep below') as caught:
        replay.advance(state, .1)
    error = caught.value
    assert error.statistics['elapsed_s'] == 0
    assert error.statistics['accepted_steps'] == 0
    assert error.statistics['minimum_total_depth_m'] > 0
    assert error.diagnostics['bounds']['draining_step_s'] < 1e-9
    np.testing.assert_array_equal(error.state, state)
