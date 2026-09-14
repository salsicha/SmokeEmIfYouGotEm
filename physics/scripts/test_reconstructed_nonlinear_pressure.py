import numpy as np
import pytest
from reconstructed_nonlinear_pressure import nonlinear_pressure
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_pressure_rates import DryGeometryTransition
from total_depth_nonlinear_pressure import nonlinear_pressure_force


def make(h, bed):
    return ReconstructedPressureGeometry(h, bed, .5, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


@pytest.mark.parametrize('rational', [True, False])
def test_fully_wet_flat_bed_matches_original_kinematic_model(rational):
    rng = np.random.default_rng(824)
    h = rng.uniform(.5, 2, (3, 4)); z = np.zeros_like(h)
    u = rng.normal(size=(*h.shape, 2))*.1
    ht = rng.normal(size=h.shape)*.03; mt = rng.normal(size=u.shape)*.02
    originals = [a.copy() for a in (h, z, u, ht, mt)]
    for a in (h, z, u, ht, mt): a.flags.writeable = False
    g = make(h, z)
    actual, report = nonlinear_pressure(g, u, ht, mt, rational=rational)
    expected, _ = nonlinear_pressure_force(h, z, u, np.zeros_like(u),
        [np.ones_like(h, dtype=bool)]*2, .5, rational=rational,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=ht,
        momentum_rate=mt, bed_slope=np.zeros_like(u))
    np.testing.assert_allclose(actual, expected, atol=3e-16, rtol=1e-12)
    np.testing.assert_allclose(actual.sum((0, 1)), 0, atol=1e-15)
    assert all(p['relative_residual'] < 1e-13 for p in report['poles'])
    for before, value in zip(originals, (h, z, u, ht, mt)): np.testing.assert_array_equal(before, value)


def test_variable_bed_pressure_satisfies_same_discrete_material_equation():
    rng = np.random.default_rng(825)
    h = rng.uniform(.5, 2, (3, 4)); z = rng.uniform(0, 1, h.shape)
    u = rng.normal(size=(*h.shape, 2))*.1
    ht = rng.normal(size=h.shape)*.03; mt = rng.normal(size=u.shape)*.02
    fraction = rng.uniform(.1, 1, h.shape)
    g = make(h, z)
    force, report = nonlinear_pressure(g, u, ht, mt, dispersion_fraction=fraction, preconditioner='block')
    root = np.sqrt(h)
    for pole in report['poles']:
        acceleration = (pole['base']+pole['correction'])/root[..., None]
        d, e = g.kinematic_components(acceleration)
        q = report['quadratic']-d; c = report['curvature']+e
        expected_p = pole['length']*fraction*(h**3*q+1.5*h*h*c)
        expected_b = pole['length']*fraction*(1.5*h*h*q+3*h*c)
        np.testing.assert_allclose(pole['pressure'], expected_p, atol=2e-16)
        np.testing.assert_allclose(pole['bottom_pressure'], expected_b, atol=2e-16)
        np.testing.assert_allclose(root[..., None]*pole['correction'], pole['force'], atol=2e-16)
        system = ReconstructedAccelerationSystem(g, pole['length'], dispersion_fraction=fraction)
        np.testing.assert_allclose(system.apply(pole['correction']), pole['rhs'], atol=2e-16)
    np.testing.assert_allclose(force, sum(p['weight']*p['force'] for p in report['poles']), atol=1e-16)


@pytest.mark.parametrize('depth', [1., 1e-200, 2.**-1070])
def test_stationary_thin_and_dry_lake_has_no_pressure_force(depth):
    h = np.full((1, 4), depth); h[0, -1] = 0
    g = make(h, np.zeros_like(h)); zero = np.zeros_like(h); u = np.zeros((*h.shape, 2))
    force, report = nonlinear_pressure(g, u, zero, u)
    np.testing.assert_array_equal(force, 0)
    assert all(p['iterations'] == 0 for p in report['poles'])


def test_actual_dry_activation_remains_rejected_no_native_rate_substitution():
    h = np.array([[1., 0., 0.]])
    g = make(h, np.zeros_like(h)); ht = np.zeros_like(h); ht[0, 1] = 1e-52
    u = np.zeros((*h.shape, 2))
    with pytest.raises(DryGeometryTransition): nonlinear_pressure(g, u, ht, u)
    assert ht[0, 1] == 1e-52
