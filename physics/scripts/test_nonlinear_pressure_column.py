import numpy as np
import pytest
from total_depth_nonlinear_pressure import pressure_column, nonlinear_pressure_force


def test_hydrostatic_column_and_dry_cell():
    h = np.array([[0., .1, 2., 1e-100]])
    column = pressure_column(h, np.zeros_like(h), np.zeros_like(h))
    np.testing.assert_allclose(column['bottom'], 9.81*h)
    np.testing.assert_allclose(column['integrated'], .5*9.81*h*h)
    np.testing.assert_array_equal(column['minimum'], 0)
    np.testing.assert_array_equal(column['minimum_sigma'], 1)


def test_quadratic_column_reconstructs_integral_and_interior_minimum():
    # Total p=(1-sigma)-2*(1-sigma**2); min at sigma=.25, p=-1.125.
    h = np.array([[2.]])
    integrated = h*(.5-4/3)-.5*9.81*h*h
    bottom = np.array([[-1.]])-9.81*h
    column = pressure_column(h, integrated, bottom)
    np.testing.assert_allclose(column['alpha'], 1, atol=1e-13)
    np.testing.assert_allclose(column['beta'], -2, atol=1e-13)
    np.testing.assert_allclose(column['minimum_sigma'], .25, atol=1e-13)
    np.testing.assert_allclose(column['minimum'], -1.125, atol=1e-13)
    np.testing.assert_allclose(h*(column['alpha']/2+2*column['beta']/3), column['integrated'], atol=1e-13)


def test_negative_bottom_is_retained_not_clipped():
    h = np.ones((2, 3))
    column = pressure_column(h, -10*np.ones_like(h), -20*np.ones_like(h))
    np.testing.assert_allclose(column['bottom'], -10.19)
    np.testing.assert_allclose(column['minimum'], -10.19)
    np.testing.assert_array_equal(column['minimum_sigma'], 0)


@pytest.mark.parametrize('bad', ['shape', 'dry', 'negative_depth', 'nan', 'gravity'])
def test_column_invalid_input_is_rejected(bad):
    h = np.ones((2, 3)); p = np.zeros_like(h); b = p.copy(); gravity = 9.81
    if bad == 'shape': p = p[:1]
    elif bad == 'dry': h[0,0] = 0; p[0,0] = 1
    elif bad == 'negative_depth': h[0,0] = -1
    elif bad == 'nan': b[0,0] = np.nan
    else: gravity = 0
    with pytest.raises(ValueError): pressure_column(h, p, b, gravity)


def test_pressure_observation_cannot_modify_result_or_inputs():
    h = np.ones((3, 5)); bed = np.zeros_like(h)
    u = np.zeros((*h.shape, 2)); u[...,0] = np.arange(5)*.1
    force = -u*.03; pairs = [np.ones_like(h,dtype=bool), np.ones_like(h,dtype=bool)]
    expected, diagnostics = nonlinear_pressure_force(h, bed, u, force, pairs, .5)
    observed = []
    def modify(poles):
        observed.extend(poles)
        for pole in poles:
            for name, value in pole.items():
                if isinstance(value, np.ndarray): value[:] = 1e9
    actual, actual_diagnostics = nonlinear_pressure_force(h, bed, u, force, pairs, .5, on_pressure=modify)
    assert len(observed) == 2
    np.testing.assert_array_equal(actual, expected)
    assert actual_diagnostics == diagnostics
    np.testing.assert_array_equal(h, 1)
    np.testing.assert_array_equal(bed, 0)
