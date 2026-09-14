import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_symmetric_sweep_reference import SymmetricSweepSystem
from diagnose_reconstructed_pressure_convergence import assembled_matrix, capture_systems
import reconstructed_nonlinear_pressure as nonlinear


@pytest.mark.parametrize('shape', [(1, 1), (1, 2), (2, 2), (3, 4)])
@pytest.mark.parametrize('periodic', [True, False])
def test_symmetric_sweep_matches_its_spd_matrix_without_changing_fine_action(shape, periodic):
    rng = np.random.default_rng(415)
    h = rng.uniform(.1, 2, shape); bed = rng.uniform(0, .5, shape)
    fraction = rng.uniform(0, 1, shape); fraction.flat[0] = 0
    geometry = ReconstructedPressureGeometry(h, bed, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    original = ReconstructedAccelerationSystem(geometry, .4052787713439809, dispersion_fraction=fraction)
    wrapper = SymmetricSweepSystem(original); a = assembled_matrix(original).toarray()
    lower = np.tril(a); m = (lower/np.diag(a))@lower.T
    x = rng.normal(size=(*shape, 2)); y = rng.normal(size=x.shape)
    before = x.copy(); x.flags.writeable = False
    actual = wrapper.precondition(x)
    np.testing.assert_allclose(actual.ravel(), np.linalg.solve(m, x.ravel()), atol=3e-14)
    assert np.sum(x*actual) > 0
    assert np.sum(x*wrapper.precondition(y)) == pytest.approx(np.sum(actual*y), abs=3e-14)
    np.testing.assert_array_equal(wrapper.apply(x), original.apply(x))
    np.testing.assert_array_equal(x, before)
    result, report = wrapper.solve(x)
    assert report['relative_residual'] < 1e-12 and report['iterations'] <= 40
    np.testing.assert_allclose(result.ravel(), np.linalg.solve(a, x.ravel()), atol=3e-13)


def test_dry_unknowns_are_identity_without_projecting_thin_positive_cells():
    h = np.array([[1., 0., 0., 1e-100, 2.]])
    g = ReconstructedPressureGeometry(h, np.zeros_like(h), .5, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    original = ReconstructedAccelerationSystem(g, 1/3); wrapper = SymmetricSweepSystem(original)
    rhs = np.arange(10.).reshape(1, 5, 2)
    np.testing.assert_array_equal(wrapper.precondition(rhs)[h == 0], rhs[h == 0])
    np.testing.assert_array_equal(wrapper.apply(rhs), original.apply(rhs))
    assert np.any(original.columns == 6)


def test_capture_scope_restores_original_class_after_exception():
    original = nonlinear.ReconstructedAccelerationSystem
    with pytest.raises(RuntimeError):
        with capture_systems([]):
            assert nonlinear.ReconstructedAccelerationSystem is not original
            raise RuntimeError('test')
    assert nonlinear.ReconstructedAccelerationSystem is original
