import numpy as np
import pytest
from audit_directional_pressure_limit import directional_pressure_limit
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def fixture():
    state = np.zeros((1, 3, 3)); state[0, 0, :2] = 1.
    rate = np.zeros_like(state); rate[0, 0, :2] = -.1; rate[0, 1, :2] = .1
    g = ReconstructedPressureGeometry(state[..., 0], np.zeros((1, 3)), .5,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    fraction = np.ones((1, 3))
    trace = np.zeros((8, 2)); trace[0, 0] = 1.
    return g, state, rate, fraction, trace


def test_full_direction_keeps_finite_entering_velocity_and_source_unchanged():
    g, state, rate, fraction, trace = fixture()
    values = (state, rate, fraction, trace); before = [a.copy() for a in values]
    for a in values: a.flags.writeable = False
    result = directional_pressure_limit(g, state, rate, fraction, trace)
    assert len(result['probes']) == 3
    assert 'no base dry-transition closure' in result['qualification']
    for row in result['probes']:
        active = row['activations'][0]
        assert active['yx'] == [0, 1]
        assert active['depth'] == row['parameter_seconds']*.1
        assert active['velocity'] == [1., 0.]
        assert np.isfinite(row['maximum_pressure_force'])
        assert all(p['iterations'] <= 40 for p in row['poles'])
    for old, value in zip(before, values): np.testing.assert_array_equal(old, value)


def test_analytic_comparison_retains_zero_depth_without_probe_initialization():
    g, state, rate, fraction, trace = fixture()
    result = directional_pressure_limit(g, state, rate, fraction, trace, analytic=True)
    analytic = result['analytic_limit']
    assert analytic['source_depth_unchanged']
    assert analytic['dry_pressure_force_maximum'] == 0
    assert analytic['comparisons'][-1]['maximum_pressure_force_difference'] < 1e-12
    assert state[0, 1, 0] == 0


@pytest.mark.parametrize('failure', ['shape', 'mismatch', 'nan', 'negative_dry', 'unrepresentable'])
def test_invalid_original_direction_cannot_be_repaired(failure):
    g, state, rate, fraction, trace = fixture()
    if failure == 'shape': rate = rate[:, :2]
    if failure == 'mismatch': state[0, 0, 0] = .9
    if failure == 'nan': rate[0, 1, 1] = np.nan
    if failure == 'negative_dry': rate[0, 2, 0] = -.1
    if failure == 'unrepresentable': rate[0, 1, 0] = np.nextafter(0., 1.)
    with pytest.raises(ValueError): directional_pressure_limit(g, state, rate, fraction, trace)
