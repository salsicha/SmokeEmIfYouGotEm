import numpy as np
import pytest
from audit_dry_pressure_geometry import dry_mass_limit, locate_change
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def fixture():
    h = np.array([[1., 0., 0.]])
    bed = np.zeros_like(h)
    g = ReconstructedPressureGeometry(h, bed, 1., pressure_trace='integrated_column',
                                     bed_quadrature='shared_bottom')
    rate = np.array([[0., 1e-52, 0.]])
    u = np.zeros((*h.shape, 2)); u[0, 0, 0] = 2.
    return g, rate, u, h.copy(), bed


def test_dry_limit_separates_raw_dry_row_jump_from_column_velocity():
    g, rate, u, p, b = fixture()
    inputs = (g.h, g.bed, rate, u, p, b)
    originals = [v.copy() for v in inputs]
    for v in inputs: v.flags.writeable = False
    result = dry_mass_limit(g, rate, u, p, b)
    assert result['activations'][0]['original_mass_rate'] == 1e-52
    assert result['activations'][0]['rounded_cpu_mass_rate_fp32'] == 0
    for row in result['probes']:
        support = row['D_change_by_original_support']
        assert support['activating']['yx'] == [0, 1]
        assert support['activating']['maximum'] == 2.
        assert support['wet']['maximum'] == 0.
        assert support['stationary_dry']['maximum'] == 0.
        assert row['new_depths_at_activations'][0] > 0
        assert row['column_velocity_change']['maximum'] == 2*row['new_depths_at_activations'][0]
    for old, value in zip(originals, inputs): np.testing.assert_array_equal(old, value)


def test_location_handles_empty_support_and_signed_changes():
    a = np.array([[1., 2.]])
    assert locate_change(a, a, np.zeros_like(a, dtype=bool)) == dict(maximum=0., yx=None)
    assert locate_change(a, a-3, np.array([[False, True]])) == dict(maximum=3., yx=[0, 1], before=2., after=-1.)


@pytest.mark.parametrize('direction', [np.array([[0., 0., 0.]]), np.array([[0., -1., 0.]]),
                                       np.array([[0., np.nan, 0.]]), np.zeros((2, 3))])
def test_invalid_or_nonactivating_direction_is_not_repaired(direction):
    g, _, u, p, b = fixture()
    with pytest.raises(ValueError): dry_mass_limit(g, direction, u, p, b)


def test_unrepresentable_positive_depth_is_rejected_not_floored():
    g, rate, u, p, b = fixture(); rate[0, 1] = np.nextafter(0., 1.)
    with pytest.raises(ValueError, match='no repair'): dry_mass_limit(g, rate, u, p, b)
