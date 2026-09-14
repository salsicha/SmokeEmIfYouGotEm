import numpy as np
import pytest
from audit_conserved_ray_cancellation import cancellation


def test_exact_dyadic_ray_cancels_without_a_residual_repair():
    result = cancellation(2.**-500, 2.**-501, .125, .0625, .5)
    assert all(value == 0 for value in result.values())


def test_primitive_rounding_is_separated_from_conserved_state_error():
    result = cancellation(3., 1., 3., 1., 1/3)
    assert result['stored_state_conservative_residual'] == 0
    assert result['primitive_velocity_rounding_residual'] > 0
    assert result['primitive_velocity_rounding_residual'] == result['actual_rounded_velocity_conservative_residual']


def test_stored_probe_offset_is_not_hidden_by_exact_velocity():
    h = np.nextafter(1., 2.)
    result = cancellation(h, .5, 1., .5, .5/h)
    assert result['stored_state_conservative_residual'] > 0
    assert result['stored_state_velocity_time_rate'] > 0


@pytest.mark.parametrize('depth', [0., -1.])
def test_nonpositive_probe_is_rejected(depth):
    with pytest.raises(ValueError): cancellation(depth, 0, .1, 0, 0)
