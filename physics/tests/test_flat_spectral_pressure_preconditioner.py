"""Same full pressure operator; only its SPD preconditioner is different."""
import numpy as np
import pytest

from flat_spectral_pressure_preconditioner import precondition
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from smooth_rational_velocity_stage import make
from rational_metric_transport_2d import stage


@pytest.mark.parametrize('shape', ((1, 16), (16, 1), (5, 7), (8, 8)))
def test_constant_depth_inverse_and_null_frequencies(shape):
    g = make(np.full(shape, 1.5), np.zeros(shape), .5)
    system = ReconstructedAccelerationSystem(g, .4052787713439809)
    rhs = np.random.default_rng(2330).normal(size=(*shape, 2))
    result = precondition(system, rhs)
    np.testing.assert_allclose(system.apply(result), rhs, atol=1e-13, rtol=0)
    constants = np.ones_like(rhs)
    np.testing.assert_allclose(precondition(system, constants), constants, atol=1e-14, rtol=0)


def test_variable_depth_positive_symmetric_preconditioner_and_full_solve():
    rng = np.random.default_rng(2332)
    h = 1.+.3*rng.random((4, 5))
    system = ReconstructedAccelerationSystem(make(h, np.zeros_like(h), .5), .4052787713439809)
    a, b = rng.normal(size=(2, *h.shape, 2))
    ma, mb = precondition(system, a), precondition(system, b)
    assert np.sum(a*ma) > 0
    assert abs(np.sum(a*mb)-np.sum(b*ma)) < 1e-12
    # Frozen preconditioner alone is deliberately NOT the variable-depth solve.
    assert np.max(abs(system.apply(ma)-a)) > .01
    columns = []
    for i in range(a.size):
        basis = np.zeros_like(a); basis.flat[i] = 1.
        columns.append(system.apply(basis).ravel())
    expected = np.linalg.solve(np.stack(columns, axis=1), a.ravel()).reshape(a.shape)
    solution, stats = system.solve(a, iterations=40, preconditioner='spectral-flat')
    np.testing.assert_allclose(solution, expected, atol=1e-12, rtol=0)
    assert stats['iterations'] == 40
    assert stats['relative_residual'] < 1e-12


def test_stage_agrees_with_original_patch_on_resolved_small_state():
    rng = np.random.default_rng(2334)
    h = 1.4+.2*rng.random((3, 4))
    p = h[..., None]*rng.normal(size=(3, 4, 2))*.2
    g = make(h, np.zeros_like(h), .5)
    original = stage(g, p, preconditioner='patch')
    spectral = stage(g, p, preconditioner='spectral-flat')
    for key in ('depth_rate', 'physical_momentum_rate', 'physical_acceleration'):
        np.testing.assert_allclose(spectral[key], original[key], atol=1e-11, rtol=0)


def test_variable_bed_and_fractional_dispersion_rejected():
    h = np.ones((3, 4)); b = np.zeros_like(h); b[0, 0] = .1
    system = ReconstructedAccelerationSystem(make(h, b, .5), .1)
    with pytest.raises(ValueError, match='flat full dispersion'):
        precondition(system, np.ones((*h.shape, 2)))
    system = ReconstructedAccelerationSystem(make(h, np.zeros_like(h), .5), .1,
                                            dispersion_fraction=np.full_like(h, .5))
    with pytest.raises(ValueError, match='flat full dispersion'):
        precondition(system, np.ones((*h.shape, 2)))
