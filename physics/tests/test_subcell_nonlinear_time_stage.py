import numpy as np
import pytest

from subcell_nonlinear_time_stage import A, B, advance, history, state_at
from test_subcell_gravity_wave_stage import lake


def test_gauss_tableau_has_independent_sixth_order_quadrature_and_symplectic_pairing():
    c = A.sum(axis=1)
    for power in range(6):
        np.testing.assert_allclose(B@c**power, 1/(power+1), atol=1e-15, rtol=0)
    for power in range(3):
        np.testing.assert_allclose(A@c**power, c**(power+1)/(power+1), atol=1e-15, rtol=0)
    np.testing.assert_allclose(B[:, None]*A+B[None, :]*A.T, np.outer(B, B), atol=1e-15, rtol=0)


@pytest.mark.parametrize('bed', [lambda x, y: 0*x, lambda x, y: .125*x*x+.25*y*y+.125*x*y])
def test_full_nonlinear_time_stage_keeps_a_source_lake_at_rest(bed):
    part = lake(bed)
    p = np.zeros((len(part.pools), 1, 2))
    result = advance(part, p, 1/120)
    np.testing.assert_allclose(result['physical_momentum'], p, atol=1e-12, rtol=0)
    np.testing.assert_allclose(result['volume'], [pool['volume'] for pool in part.pools], atol=1e-12, rtol=0)
    assert abs(result['energy_change']) < 1e-10
    assert not result['full_time_or_topology_or_open_or_native_or_gameplay_accepted']


def test_moving_nonlinear_source_state_advances_with_independent_finite_impulses():
    part = lake(lambda x, y: .125*x*x+.25*y*y+.125*x*y)
    volume = np.array([pool['volume'] for pool in part.pools])
    p = volume[:, None, None]*np.random.default_rng(2854).normal(size=(len(volume), 1, 2))*.3
    original_momentum = np.array([pool['momentum'] for pool in part.pools])
    result = advance(part, p, 1/120)
    assert np.max(abs(result['physical_momentum']-p)) > 1e-4
    assert np.max(abs(result['volume']-volume)) > 1e-5
    for name in ('mass_error', 'local_momentum_impulse_error', 'total_momentum_impulse_error', 'energy_change'):
        assert abs(result[name]) < 1e-10
    independent_impulse = result['integrated_bed_impulse']+result['integrated_wall_impulse']
    for left, right, value in result['integrated_face_impulses']:
        independent_impulse[left] -= value
        independent_impulse[right] += value
    np.testing.assert_allclose((result['physical_momentum']-p)[:, 0], independent_impulse,
                               atol=1e-10, rtol=0)
    np.testing.assert_array_equal([pool['volume'] for pool in part.pools], volume)
    np.testing.assert_array_equal([pool['momentum'] for pool in part.pools], original_momentum)
    np.testing.assert_array_equal([pool['momentum'] for pool in result['partition'].pools],
                                  result['physical_momentum'][:, 0])
    assert result['collocation_sweeps'] <= 40 and result['collocation_residual'] <= 1e-12


def test_periodic_flat_constant_flow_is_unchanged():
    part = lake(lambda x, y: 0*x, 1.3, (4, 4), (.4, .4), (-.6, -.6), (True, True))
    volume = np.array([pool['volume'] for pool in part.pools])
    p = volume[:, None, None]*np.array([[[.4, -.2]]])
    result = advance(part, p, 1/120)
    np.testing.assert_allclose(result['physical_momentum'], p, atol=1e-12, rtol=0)
    np.testing.assert_allclose(result['volume'], volume, atol=1e-12, rtol=0)
    np.testing.assert_array_equal(result['integrated_bed_impulse'], 0.)
    np.testing.assert_array_equal(result['integrated_wall_impulse'], 0.)


@pytest.mark.parametrize('dt', [0., -1., float('nan'), float('inf')])
def test_invalid_time_step_rejects(dt):
    part = lake()
    with pytest.raises(ValueError, match='Positive finite time'):
        advance(part, np.zeros((len(part.pools), 1, 2)), dt)


def test_large_time_step_rejects_without_mutating_the_original_water():
    part = lake(lambda x, y: .125*x*x+.25*y*y)
    volume = np.array([pool['volume'] for pool in part.pools])
    p = volume[:, None, None]*np.random.default_rng(2855).normal(size=(len(volume), 1, 2))
    saved = p.copy()
    with pytest.raises(ValueError):
        advance(part, p, 10.)
    np.testing.assert_array_equal(p, saved)
    np.testing.assert_array_equal([pool['volume'] for pool in part.pools], volume)


def test_consecutive_full_nonlinear_steps_keep_cumulative_original_budgets():
    part = lake(lambda x, y: .125*x*x+.25*y*y+.125*x*y)
    volume = np.array([pool['volume'] for pool in part.pools])
    p = volume[:, None, None]*np.random.default_rng(2856).normal(size=(len(volume), 1, 2))*.3
    initial = state_at(part, volume, p)
    observed = []
    result = history(initial, 2, 1/120, on_step=lambda row: observed.append(row['step']))
    assert observed == [1, 2]
    assert result['completed_steps'] == 2, result['failure']
    assert result['closed_fixed_support_time_controls_passed']
    for row in result['records']:
        for name in ('cumulative_mass_error', 'cumulative_momentum_impulse_error', 'cumulative_full_energy_change'):
            assert abs(row[name]) < 1e-10
        assert np.isfinite(row['nondispersive_energy_change'])
    np.testing.assert_array_equal([pool['momentum'] for pool in initial.pools], p[:, 0])
    assert not result['full_time_or_topology_or_open_or_native_or_gameplay_accepted']


def test_history_preserves_an_oversized_step_failure_without_retry_or_partial_state():
    part = lake(lambda x, y: .125*x*x+.25*y*y)
    volume = np.array([pool['volume'] for pool in part.pools])
    p = volume[:, None, None]*np.random.default_rng(2855).normal(size=(len(volume), 1, 2))
    result = history(state_at(part, volume, p), 3, 10.)
    assert not result['closed_fixed_support_time_controls_passed']
    assert result['completed_steps'] == 0 and result['failure']['step'] == 1
    np.testing.assert_array_equal(result['final_volume'], volume)
    np.testing.assert_array_equal(result['final_physical_momentum'], p[:, 0])


def test_finite_energy_failure_is_not_projected_away(monkeypatch):
    import subcell_nonlinear_time_stage as time
    part = lake(lambda x, y: 0*x)
    p = np.zeros((len(part.pools), 1, 2))
    original_stage = time.stage

    def forced_stage(geometry, momentum):
        result = original_stage(geometry, momentum)
        # Deliberately add work, keeping its independent impulse ledger equal.
        # The endpoint energy check must still detect it and reject the step.
        result['physical_momentum_rate'][:, 0, 0] += .1
        result['bed_force'][:, 0] += .1
        return result

    monkeypatch.setattr(time, 'stage', forced_stage)
    with pytest.raises(ValueError, match='Finite nonlinear source step rejected; no state repair'):
        time.advance(part, p, 1/120)
    np.testing.assert_array_equal(p, 0.)
    np.testing.assert_array_equal([pool['momentum'] for pool in part.pools], 0.)


def test_positive_energy_contraction_gate_is_retained(monkeypatch):
    import subcell_nonlinear_time_stage as time
    part = lake(lambda x, y: 0*x)
    original_evaluate = time.evaluate

    def inconsistent_contraction(*args, **kwargs):
        result = original_evaluate(*args, **kwargs)
        result['positive_energy_contraction_error'] = 1e-6
        return result

    monkeypatch.setattr(time, 'evaluate', inconsistent_contraction)
    with pytest.raises(ValueError, match='Finite nonlinear source step rejected; no state repair'):
        time.advance(part, np.zeros((len(part.pools), 1, 2)), 1/120)
