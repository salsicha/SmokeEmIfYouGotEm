from fractions import Fraction as F
import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_acceleration_system import ReconstructedAccelerationSystem, mass_scaled


def geometry(h, bed, periodic=True):
    return ReconstructedPressureGeometry(h, bed, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


def dense_components(g):
    basis = np.eye(g.h.size*2).reshape(-1, *g.h.shape, 2)
    values = [g.kinematic_components(u) for u in basis]
    d = np.stack([v[0].ravel() for v in values], axis=1)
    e = np.stack([v[1].ravel() for v in values], axis=1)
    root = np.sqrt(g.h.ravel())
    inv = np.repeat(np.divide(1, root, out=np.zeros_like(root), where=root > 0), 2)
    return (root[:, None]*(g.h.ravel()[:, None]*d-1.5*e)*inv,
            root[:, None]*e*inv)


@pytest.mark.parametrize('shape', [(1, 1), (1, 2), (2, 2), (3, 4)])
@pytest.mark.parametrize('periodic', [True, False])
def test_factored_actions_diagonal_blocks_and_solve_match_explicit_geometry(shape, periodic):
    rng = np.random.default_rng(950)
    h = rng.uniform(.3, 2, shape); bed = rng.uniform(0, .7, shape)
    fraction = rng.uniform(.1, 1, shape); fraction.flat[0] = 0
    g = geometry(h, bed, periodic); s = ReconstructedAccelerationSystem(g, 1/3, dispersion_fraction=fraction)
    w, v = dense_components(g)
    matrix = np.eye(2*h.size)+(w.T@(fraction.ravel()[:, None]*w)+.75*v.T@(fraction.ravel()[:, None]*v))/3
    x = rng.normal(size=(*shape, 2)); y = rng.normal(size=shape)
    np.testing.assert_allclose(s.w(x).ravel(), w@x.ravel(), atol=2e-15)
    np.testing.assert_allclose(s.v(x).ravel(), v@x.ravel(), atol=2e-15)
    np.testing.assert_allclose(s.transpose_w(y).ravel(), w.T@y.ravel(), atol=2e-15)
    np.testing.assert_allclose(s.transpose_v(y).ravel(), v.T@y.ravel(), atol=2e-15)
    np.testing.assert_allclose(s.apply(x).ravel(), matrix@x.ravel(), atol=1e-14)
    np.testing.assert_allclose(s.diagonal.ravel(), np.diag(matrix), atol=2e-15)
    np.testing.assert_allclose(s.off_diagonal.ravel(), matrix[np.arange(0, 2*h.size, 2), np.arange(1, 2*h.size, 2)], atol=2e-15)
    assert np.linalg.eigvalsh(matrix).min() >= 1-2e-14
    for scheme in ('diagonal', 'block'):
        solution, report = s.solve(x, preconditioner=scheme)
        np.testing.assert_allclose(solution.ravel(), np.linalg.solve(matrix, x.ravel()), rtol=2e-13, atol=2e-13)
        assert report['relative_residual'] < 2e-13
    assert not s.fraction.flags.writeable and not s.w_coefficients.flags.writeable
    assert not np.shares_memory(s.fraction, fraction)


def test_dry_identity_columns_are_not_thresholded_positive_water():
    h = np.array([[1., 0., 0., 2.]])
    g = geometry(h, np.zeros_like(h)); s = ReconstructedAccelerationSystem(g, 1/3)
    x = np.arange(8.).reshape(1, 4, 2)
    np.testing.assert_array_equal(s.apply(x)[h == 0], x[h == 0])
    x[h > 0] = 0
    np.testing.assert_array_equal(s.w(x), 0)
    np.testing.assert_array_equal(s.v(x), 0)


@pytest.mark.parametrize('depth', [1e-200, 1e-300, 2.**-1070])
def test_thin_uniform_film_keeps_nonzero_factored_coefficients(depth):
    h = np.full((1, 4), depth)
    s = ReconstructedAccelerationSystem(geometry(h, np.zeros_like(h)), 1/3)
    assert np.count_nonzero(s.w_coefficients) == 8
    np.testing.assert_array_equal(abs(s.w_coefficients), depth)
    u = np.zeros((1, 4, 2)); u[0, 1, 0] = 1
    assert s.w(u)[0, 0] == depth
    assert s.w(u)[0, 2] == -depth


def test_mass_factor_avoids_overflow_and_underflow_before_final_rounding():
    assert mass_scaled(F(1, 10**300), F(10**300), F(1, 10**300)) == 1.
    assert mass_scaled(F(-10**300), F(1, 10**300), F(10**300)) == -1.
    assert mass_scaled(F(0), F(0), F(0)) == 0.
    for c, a, b in ((F(1), F(0), F(1)), (F(1), F(1), F(0)),
                    (F(1), F(10**1000), F(1)), (F(1), F(1, 10**1000), F(1))):
        with pytest.raises(ValueError): mass_scaled(c, a, b)


def test_invalid_fraction_and_iteration_budget_rejected():
    g = geometry(np.ones((2, 3)), np.zeros((2, 3)))
    for fraction in (np.ones((1, 3)), np.full((2, 3), np.nan), np.full((2, 3), -1)):
        with pytest.raises(ValueError): ReconstructedAccelerationSystem(g, 1/3, dispersion_fraction=fraction)
    s = ReconstructedAccelerationSystem(g, 1/3)
    with pytest.raises(ValueError): s.solve(np.ones((2, 3, 2)), iterations=41)


def test_original_geometry_manufactured_report_is_explicitly_not_physical_rhs():
    from audit_reconstructed_acceleration import inspect_system
    g = geometry(np.array([[1., .2, 0.]]), np.zeros((1, 3)), False)
    u = np.zeros((1, 3, 2)); u[0, 0, 0] = 1.
    report = inspect_system(g, np.ones_like(g.h), u)
    assert 'Manufactured linear RHS only' in report['qualification']
    assert len(report['poles']) == 2
    for pole in report['poles']:
        assert pole['vector_unknowns'] == 6
        for solve in pole['solves']:
            assert solve['dry_unknown_maximum'] == 0
            assert solve['maximum_recovered_test_vector_error'] < 1e-13
