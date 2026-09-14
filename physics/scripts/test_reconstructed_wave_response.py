import numpy as np
import pytest
import total_depth_bank_replay as bank
from audit_reconstructed_wave_response import measure


def test_actual_rate_response_refines_toward_independent_closure():
    values = [measure(12., cells) for cells in (16, 32, 64)]
    errors = [abs(v['relative_closure_response_error']) for v in values]
    assert errors[1] < errors[0] and errors[2] < errors[1]
    assert errors[2] < .005
    for value in values:
        assert abs(value['mass_rate_integral_m3ps']) < 1e-14
        np.testing.assert_allclose(value['momentum_rate_integral_m4ps2'], 0, atol=1e-14)
        assert value['transverse_rate_max'] == 0
        assert abs(value['quadrature_response']) < 1e-9
        assert max(p['relative_residual'] for s in value['pressure_stages']
                   for p in s['pressure_stats']) < 2e-5


def test_axis_rotation_and_amplitude_check_do_not_substitute_a_model():
    original = bank.rate
    x = measure(4., 32)
    y = measure(4., 32, axis=0)
    small = measure(4., 32, amplitude=1e-6)
    sgn = measure(4., 32, model='sgn')
    assert bank.rate is original
    assert x['measured_restoring_response'] == pytest.approx(y['measured_restoring_response'], abs=1e-12)
    assert x['measured_restoring_response'] == pytest.approx(small['measured_restoring_response'], abs=1e-7)
    assert abs(sgn['relative_airy_response_error']) > abs(x['relative_airy_response_error'])
    assert abs(x['relative_airy_response_error']) < .03


@pytest.mark.parametrize('kwargs', [dict(wavelength=0), dict(cells=7), dict(axis=2),
    dict(amplitude=0), dict(model='linear')])
def test_invalid_wave_experiment_is_rejected(kwargs):
    with pytest.raises(ValueError): measure(**(dict(wavelength=4., cells=16) | kwargs))
