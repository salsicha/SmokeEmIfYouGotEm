import json
import numpy as np
import pytest
import audit_reconstructed_physical_history as audit
from audit_total_depth_dispersion import solitary


def test_current_benchmark_keeps_four_wavelengths_and_original_momentum():
    state, dx, seconds, spec = audit.setup('current_wave', 4.)
    assert state.shape == (1, 128, 3) and dx == .125
    assert spec['current_mps'] == .4 and spec['wavelengths_in_domain'] == 4
    assert seconds == 4/spec['physical_speed_mps']
    eta = state[..., 0]-1.5
    np.testing.assert_allclose(state[..., 1], .4*state[..., 0]
        +(spec['physical_speed_mps']-.4)*eta, atol=1e-15)


@pytest.mark.parametrize('dx', [.5, .25])
def test_solitary_comparison_retains_geometry_duration_and_model_distinction(dx):
    initial, actual_dx, seconds, spec = audit.setup('solitary', dx, 'sgn')
    assert initial.shape == (1, round(96/dx), 3) and actual_dx == dx and seconds == 4
    x = (np.arange(initial.shape[1])+.5)*dx
    final, _ = solitary(x, seconds)
    result = audit.compare(final[None], initial, dx, seconds, spec)
    assert result['relative_surface_l1_difference'] == 0
    assert spec['exact_for_governing_equations'] is True
    assert audit.setup('solitary', dx, 'rational_sgn')[3]['exact_for_governing_equations'] is False
    assert spec['periodic_tail_truncation'] and spec['amplitude_depth_ratio'] == .3


def test_actual_history_dispatch_keeps_unscaled_transport_and_serializable_success(monkeypatch):
    def exact(initial, bed, dx, seconds, **kwargs):
        assert kwargs['shoreline_limiter'] == 'unscaled'
        assert kwargs['pressure_model'] == 'rational_sgn'
        assert kwargs['max_trials'] == 10000 and kwargs['periodic']
        phase = (np.arange(128)+.5)*2*np.pi*4/128
        for fraction in (.25, .5, .75, 1.):
            value = initial.copy(); value[..., 0] = 1.5+1e-5*np.cos(phase-2*np.pi*fraction)
            kwargs['on_checkpoint'](value, dict(elapsed_s=np.float64(seconds*fraction)))
        return value, dict(elapsed_s=np.float64(seconds),
            pressure_solver=dict(worst_relative_residual=np.float64(0.)))
    monkeypatch.setattr(audit.bank, 'advance', exact)
    captured = []
    final, report = audit.run('current_wave', 4., 'rational_sgn', captured.append)
    decoded = json.loads(json.dumps(report, allow_nan=False))
    assert decoded['completed'] and decoded['linear_motion_check_passed']
    assert len(decoded['checkpoints']) == 4 and final.shape == (1, 128, 3)
    json.dumps(captured, allow_nan=False)


def test_failed_history_retains_actual_failure_state_without_completion(monkeypatch):
    initial, _, _, _ = audit.setup('solitary', .5, 'sgn')
    retained = initial.copy(); retained[..., 1] *= .9
    def fail(*args, **kwargs): raise audit.bank.ReplayExhausted(retained, dict(elapsed_s=.25))
    monkeypatch.setattr(audit.bank, 'advance', fail)
    final, report = audit.run('solitary', .5, 'sgn', lambda value: None)
    np.testing.assert_array_equal(final, retained)
    assert not report['completed'] and not report['pressure_residual_check_passed']
    assert report['diagnostics']['elapsed_s'] == .25


@pytest.mark.parametrize('case', [('current_wave', 8., 'rational_sgn'),
    ('current_wave', 4., 'sgn'), ('solitary', 1., 'sgn'), ('solitary', .5, 'linear')])
def test_benchmark_scope_cannot_silently_change(case):
    with pytest.raises(ValueError): audit.setup(*case)
