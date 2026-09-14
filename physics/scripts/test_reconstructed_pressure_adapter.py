import numpy as np
import pytest
import total_depth_bank_replay as bank
from reconstructed_pressure_adapter import reconstructed_pressure


def fields():
    state = np.zeros((3, 5, 3)); state[..., 0] = 1.
    bed = np.zeros((3, 5)); kwargs = dict(second_order=True, periodic=True,
        dispersive=True, pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
        pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    return state, bed, kwargs


def test_process_adapter_preserves_original_transport_and_restores_functions():
    state, bed, kwargs = fields(); state[..., 1] = .5
    original_rate, original_pressure = bank.rate, bank.nonlinear_pressure_force
    expected = bank.rate(state, bed, .5, **kwargs)[0]; captured = []
    before = state.copy(); state.flags.writeable = False
    with reconstructed_pressure(captured.append):
        actual = bank.rate(state, bed, .5, **kwargs)[0]
        assert bank.rate is not original_rate
    assert bank.rate is original_rate and bank.nonlinear_pressure_force is original_pressure
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(state, before)
    assert captured[0]['activating_dry_cells'] == 0


def test_failed_callback_restores_original_rate_and_pressure():
    state, bed, kwargs = fields(); original_rate, original_pressure = bank.rate, bank.nonlinear_pressure_force
    def fail(_): raise RuntimeError('diagnostic stop')
    with pytest.raises(RuntimeError, match='diagnostic stop'):
        with reconstructed_pressure(fail): bank.rate(state, bed, .5, **kwargs)
    assert bank.rate is original_rate and bank.nonlinear_pressure_force is original_pressure


def test_adapter_refuses_unmatched_pressure_call():
    state, bed, kwargs = fields()
    with reconstructed_pressure():
        with pytest.raises(ValueError, match='scoped'):
            bank.nonlinear_pressure_force(state[..., 0], bed, state[..., 1:], state[..., 1:], [], .5)
