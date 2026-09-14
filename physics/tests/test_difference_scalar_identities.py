import numpy as np
from audit_difference_scalar_identities import identity_case, affine_boundary_case, face_matrices, make
from directional_pressure_geometry import DirectionalPressureGeometry
from difference_scalar_gradient_reference import difference_gradient


def test_independent_face_matrices_explain_material_and_work_changes():
    for periodic in (False, True):
        r = identity_case(periodic)
        assert r['explicit_matrix_kinematic_error'] < 1e-14
        assert r['pressure_traction_error'] < 1e-14
        assert r['scalar_matrix_error'] < 1e-14
        assert abs(r['original_pressure_work_residual']) < 1e-14
        assert r['scalar_work_identity_error'] < 1e-14
        assert r['material_time_identity_errors'][-1] < 2e-10
        assert r['changed_scalar_adjoint_is_not_zero']


def test_affine_boundary_defect_is_retained_not_mislabeled_as_consistency():
    for n in (8, 16, 32, 64):
        r = affine_boundary_case(n)
        assert r['constant_gradient_exactly_zero']
        assert r['interior_max_error'] == 0
        assert r['endpoint_derivatives'] == [.5, .5]
        assert r['endpoint_max_error'] == .5
        assert not r['affine_boundary_consistent']


def test_explicit_matrix_distinguishes_pressure_from_constant_null_derivative():
    h = np.array([[1., .75, .5, 1.]])
    bed = 1.-h
    d, e, pressure, scalar, sigma = face_matrices(make(h, bed, False))
    np.testing.assert_array_equal(pressure, -d.T)
    np.testing.assert_allclose(scalar@np.ones(h.size), 0, atol=1e-15)
    assert abs(sigma).max() > .1
    assert abs(pressure-scalar).max() > .1


def test_directional_dry_trace_failure_matches_independent_work_defect():
    h = np.array([[2., 1., 0., 0., .5]])
    bed = np.array([[0., 0., 0., .25, .5]])
    ht = np.array([[0., -.125, .125, .0625, 0.]])
    g = DirectionalPressureGeometry(make(h, bed, False), ht)
    d, e, pressure, scalar, sigma = face_matrices(g)
    u = np.random.default_rng(118).normal(size=(*h.shape, 2)).ravel()
    f = np.ones(h.size)
    actual = difference_gradient(g, np.ones_like(h)).ravel()
    np.testing.assert_array_equal(actual, 0)
    np.testing.assert_allclose(d@u, g.kinematic_components(u.reshape(*h.shape, 2))[0].ravel(), atol=1e-15)
    assert abs(u@(pressure@f)+f@(d@u)) < 1e-14
    candidate_work = u@actual+f@(d@u)
    assert abs(candidate_work) > 1.
    np.testing.assert_allclose(candidate_work, -u@sigma, atol=1e-14)
    # Actual dry physical pressure stays zero; the force adjoint still holds.
    p = np.array([.2, -.1, 0., 0., .3])
    np.testing.assert_allclose(pressure@p, g.gradient_traction(p.reshape(h.shape), bed*0).ravel(), atol=1e-15)
