import numpy as np
import json
import pytest
from audit_reconstructed_wave_motion import metrics, run
import audit_reconstructed_wave_motion as audit


@pytest.mark.parametrize('cycles', [.25, .5, .75, 1.])
def test_exact_physical_phase_is_compared_at_actual_sample_time(cycles):
    phase = (np.arange(32)+.5)*2*np.pi/32
    state = np.zeros((1, 32, 3)); state[..., 0] = 1.5+1e-5*np.cos(phase-2*np.pi*cycles)
    result = metrics(state, phase, 1e-5, 1.5, 2., np.pi, cycles)
    assert result['phase_error_cycles'] < 1e-11
    assert result['amplitude_ratio'] == pytest.approx(1., abs=1e-10)
    assert result['linear_check_passed']


def test_stationary_or_overdamped_wave_cannot_pass_quarter_period():
    phase = (np.arange(32)+.5)*2*np.pi/32
    state = np.zeros((1, 32, 3)); state[..., 0] = 1.5+1e-5*np.cos(phase)
    assert not metrics(state, phase, 1e-5, 1.5, 2., np.pi, .25)['linear_check_passed']
    state[..., 0] = 1.5+.8e-5*np.cos(phase-np.pi/2)
    assert not metrics(state, phase, 1e-5, 1.5, 2., np.pi, .25)['linear_check_passed']


def test_failed_solver_is_not_completed_motion(monkeypatch):
    def fail(*args, **kwargs): raise ValueError('retained test failure')
    monkeypatch.setattr(audit.bank, 'advance', fail)
    result = run(4., 32, lambda value: None)
    assert not result['completed'] and not result['linear_check_passed']
    assert result['error'] == 'retained test failure'


def test_successful_motion_report_serializes_numpy_solver_scalars(monkeypatch):
    def exact(initial, bed, dx, seconds, **kwargs):
        phase = (np.arange(32)+.5)*2*np.pi/32
        stats = dict(elapsed_s=np.float64(seconds),
            pressure_solver=dict(worst_relative_residual=np.float64(0.)))
        for fraction in (.25, .5, .75, 1.):
            value = initial.copy()
            value[0, :, 0] = 1.5+1e-5*np.cos(phase-2*np.pi*fraction)
            kwargs['on_checkpoint'](value, dict(elapsed_s=np.float64(seconds*fraction)))
        return value, stats
    monkeypatch.setattr(audit.bank, 'advance', exact)
    result = run(4., 32, lambda value: None)
    decoded = json.loads(json.dumps(result, allow_nan=False))
    assert decoded['completed'] is True and decoded['linear_check_passed'] is True
