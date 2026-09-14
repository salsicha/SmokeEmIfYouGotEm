import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_polynomial_sweep_reference import PolynomialSweepSystem
from reconstructed_symmetric_sweep_reference import SymmetricSweepSystem
from diagnose_reconstructed_pressure_convergence import assembled_matrix


def system(shape=(3, 4)):
    rng = np.random.default_rng(635)
    h = rng.uniform(.2, 2, shape); bed = rng.uniform(0, .4, shape)
    g = ReconstructedPressureGeometry(h, bed, .25, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    return ReconstructedAccelerationSystem(g, .4052787713439809)


@pytest.mark.parametrize('degree', [0, 1, 2, 4, 8])
def test_polynomial_matches_explicit_spd_product_and_preserves_fine_action(degree):
    original = system(); wrapper = PolynomialSweepSystem(original, degree)
    a = assembled_matrix(original).toarray(); inverse_root = np.diag(1/np.sqrt(np.diag(a)))
    h = inverse_root@np.tril(a, k=-1)@inverse_root
    f = np.eye(a.shape[0]); power = f.copy()
    for _ in range(degree): power = -h@power; f += power
    p = inverse_root@f.T@f@inverse_root
    rng = np.random.default_rng(634); x = rng.normal(size=(*original.h.shape, 2))
    y = rng.normal(size=x.shape); before = x.copy(); x.flags.writeable = False
    result = wrapper.precondition(x)
    np.testing.assert_allclose(result.ravel(), p@x.ravel(), atol=2e-15)
    assert np.linalg.eigvalsh(p).min() > 0 and np.sum(x*result) > 0
    assert np.sum(x*wrapper.precondition(y)) == pytest.approx(np.sum(result*y), abs=1e-14)
    np.testing.assert_array_equal(wrapper.apply(x), original.apply(x))
    np.testing.assert_array_equal(x, before)
    if degree == 0: np.testing.assert_allclose(result, original.precondition(x, 'diagonal'), atol=1e-15)


def test_nilpotent_complete_polynomial_equals_exact_symmetric_sweep():
    original = system((1, 4)); rhs = np.arange(8.).reshape(1, 4, 2)
    polynomial = PolynomialSweepSystem(original, 7); exact = SymmetricSweepSystem(original)
    np.testing.assert_allclose(polynomial.precondition(rhs), exact.precondition(rhs), atol=2e-15)


@pytest.mark.parametrize('degree', [-1, 9, 1., True])
def test_polynomial_budget_must_be_explicit_valid_integer(degree):
    with pytest.raises(ValueError): PolynomialSweepSystem(system(), degree)
