"""Independent full-matrix controls for the unchanged pressure operator."""
import numpy as np
import pytest
from unittest.mock import patch

from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from smooth_rational_velocity_stage import make


def dense(system):
    columns = []
    for index in range(2*system.h.size):
        basis = np.zeros((*system.h.shape, 2))
        basis.flat[index] = 1.
        columns.append(system.apply(basis).ravel())
    return np.stack(columns, axis=1)


@pytest.mark.parametrize('shape', ((1, 1), (1, 2), (2, 1), (1, 11), (3, 4), (5, 3)))
@pytest.mark.parametrize('fraction', (1., .37, 0.))
def test_sweeps_match_full_matrix_factorization_and_preserve_operator(shape, fraction):
    rng = np.random.default_rng(413811)
    h = .4+rng.random(shape)
    g = make(h, .2*rng.normal(size=shape), .4)
    system = ReconstructedAccelerationSystem(g, .4052787713439809,
                                             dispersion_fraction=np.full(shape, fraction))
    matrix = dense(system)
    a, b = rng.normal(size=(2, *shape, 2))
    before = system.apply(a).copy()
    diagonal = np.zeros_like(matrix)
    lower = np.zeros_like(matrix)
    for i in range(h.size):
        diagonal[2*i:2*i+2, 2*i:2*i+2] = matrix[2*i:2*i+2, 2*i:2*i+2]
        lower[2*i:2*i+2, :2*i] = matrix[2*i:2*i+2, :2*i]
    expected = np.linalg.solve((diagonal+lower) @ np.linalg.solve(diagonal, (diagonal+lower).T),
                               a.ravel()).reshape(a.shape)
    pa, pb = system.precondition(a, 'block'), system.precondition(b, 'block')
    np.testing.assert_allclose(pa, expected, rtol=2e-13, atol=2e-13)
    np.testing.assert_allclose(np.sum(a*pb), np.sum(b*pa), rtol=2e-13, atol=2e-13)
    assert np.sum(a*pa) > 0
    np.testing.assert_array_equal(system.apply(a), before)
    np.testing.assert_array_equal(dense(system), matrix)
    np.testing.assert_allclose(system.precondition(a, 'block-jacobi'),
                               np.linalg.solve(diagonal, a.ravel()).reshape(a.shape),
                               rtol=2e-13, atol=2e-13)
    if fraction == 0:
        np.testing.assert_array_equal(pa, a)


def test_each_application_uses_current_rhs_without_mutation():
    g = make(np.ones((3, 4)), np.zeros((3, 4)), .25)
    system = ReconstructedAccelerationSystem(g, .4)
    a = np.random.default_rng(8177).normal(size=(3, 4, 2))
    original = a.copy()
    first = system.precondition(a, 'block')
    for factor in (0., -1., 2.):
        np.testing.assert_allclose(system.precondition(factor*a, 'block'), factor*first,
                                   rtol=2e-14, atol=2e-14)
    np.testing.assert_array_equal(a, original)
    np.testing.assert_array_equal(first, system.precondition(a, 'block'))


def test_exactly_dry_columns_stay_identity_and_do_not_couple():
    from reconstructed_pressure_geometry import ReconstructedPressureGeometry

    h = np.array([[0., 1., 2.], [0., 0., .5]])
    g = ReconstructedPressureGeometry(h, np.zeros_like(h), .5, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    system = ReconstructedAccelerationSystem(g, .4)
    rhs = np.random.default_rng(419).normal(size=(*h.shape, 2))
    result = system.precondition(rhs, 'block')
    np.testing.assert_array_equal(result[h == 0], rhs[h == 0])
    wet_rhs = rhs.copy()
    wet_rhs[h == 0] = 0.
    wet_result = system.precondition(wet_rhs, 'block')
    np.testing.assert_array_equal(wet_result[h > 0], result[h > 0])
    np.testing.assert_array_equal(wet_result[h == 0], 0.)


def test_invalid_rhs_and_unchanged_iteration_budget_rejected():
    g = make(np.ones((2, 3)), np.zeros((2, 3)), .25)
    system = ReconstructedAccelerationSystem(g, .4)
    for rhs in (np.zeros((2, 3)), np.full((2, 3, 2), np.nan)):
        with pytest.raises(ValueError):
            system.precondition(rhs, 'block')
    for iterations in (39, 41, 80):
        with pytest.raises(ValueError, match='iteration budget'):
            system.solve(np.ones((2, 3, 2)), iterations=iterations, preconditioner='block')


@pytest.mark.parametrize('seed', (2201, 2203, 2205, 2207))
def test_original_failed_directions_are_unchanged_and_now_resolved(seed):
    from audit_reconstructed_closed_energy import fixture
    from reconstructed_energy_reference import metric
    from smooth_rational_velocity_stage import stage
    from rational_physical_momentum_rate import physical_rate

    source, bed = fixture(seed, 'smooth', 128)
    before = source.copy(), bed.copy()
    h = source[..., 0]
    g = make(h, bed, .125)
    root = np.sqrt(h)[..., None]
    k, _ = metric(g, rational=True)
    u = source[..., 1:]/h[..., None]
    v = (k @ (root*u).ravel()).reshape(u.shape)/root
    current = ReconstructedAccelerationSystem.precondition

    def legacy(self, rhs, scheme='diagonal'):
        return current(self, rhs, 'block-jacobi' if scheme == 'block' else scheme)

    # Freeze the ORIGINAL state AND directions computed by the old default.
    # Improving the rate used as input cannot conceal the previous failure.
    with patch.object(ReconstructedAccelerationSystem, 'precondition', legacy):
        direction = stage(g, v)
        args = g, v, direction['depth_rate'], direction['canonical_velocity_rate']
        old = physical_rate(*args)
    new = physical_rate(*args)
    gate = lambda r: 1e-10*max(1., abs(r['physical_energy_rate']), abs(r['canonical_energy_rate']))
    assert old['energy_coordinate_error'] > gate(old)
    assert new['energy_coordinate_error'] <= gate(new)
    assert max(p['iterations'] for p in new['poles']) <= 40
    np.testing.assert_array_equal(source, before[0])
    np.testing.assert_array_equal(bed, before[1])
