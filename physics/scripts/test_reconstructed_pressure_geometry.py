import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry, transfer_coefficients
from total_depth_nonlinear_pressure import gradient, depth_weights


@pytest.mark.parametrize('periodic', [False, True])
def test_two_kinematic_components_are_exact_signed_force_adjoints(periodic):
    rng = np.random.default_rng(20260914)
    h = rng.uniform(.05, 2., (5, 7)); bed = rng.uniform(0., 3., h.shape)
    h[1, 2] = 0
    original = h.copy(), bed.copy()
    h.flags.writeable = bed.flags.writeable = False
    geometry = ReconstructedPressureGeometry(h, bed, .5, periodic=periodic)
    p, b = rng.normal(size=h.shape), rng.normal(size=h.shape)
    p[h == 0] = b[h == 0] = 0
    u = rng.normal(size=(*h.shape, 2))
    d, e = geometry.kinematic_components(u)
    lhs = np.sum(u*geometry.gradient_traction(p, b))
    rhs = -np.sum(p*d)+np.sum(b*e)
    assert abs(lhs-rhs) < 1e-12
    np.testing.assert_array_equal(h, original[0]); np.testing.assert_array_equal(bed, original[1])
    assert not np.shares_memory(geometry.h, h)
    assert all(not v.flags.writeable for edge in geometry.edges for v in edge.values())
    assert np.all(geometry.gradient_traction(p, b)[h == 0] == 0)


def test_flat_periodic_pressure_conserves_momentum_with_original_mc_slopes():
    rng = np.random.default_rng(20260914)
    h = rng.uniform(.4, 2., (5, 7)); p = rng.normal(size=h.shape)
    geometry = ReconstructedPressureGeometry(h, np.zeros_like(h), .5, periodic=True)
    value = geometry.gradient_traction(p, np.zeros_like(h))
    np.testing.assert_allclose(value.sum((0, 1)), 0., atol=1e-13)
    d, e = geometry.kinematic_components(np.ones((*h.shape, 2)))
    np.testing.assert_allclose(d, 0., atol=2e-15)
    np.testing.assert_array_equal(e, 0.)
    assert any(np.any(g['dh']) for g in geometry.polynomials)


def test_uniform_flat_column_matches_original_pressure_operator_exactly():
    rng = np.random.default_rng(91)
    h = np.full((5, 7), .25); p = rng.normal(size=h.shape)
    g = ReconstructedPressureGeometry(h, np.zeros_like(h), .5, periodic=True)
    pairs = [np.ones_like(h, dtype=bool) for _ in (0, 1)]
    np.testing.assert_array_equal(g.gradient_traction(p, np.zeros_like(h)),
        gradient(p, pairs, .5, depth_weights(h)))


def test_operator_implies_spd_normalized_acceleration_matrix_on_cut_geometry():
    # This tests the static algebra, NOT a nonlinear evolution/energy invariant.
    rng = np.random.default_rng(101)
    h = rng.uniform(.1, 2., (3, 4)); bed = rng.uniform(0., 3., h.shape)
    geometry = ReconstructedPressureGeometry(h, bed, .5, periodic=True)
    basis = np.eye(2*h.size).reshape(2*h.size, *h.shape, 2)
    columns = [geometry.kinematic_components(v) for v in basis]
    d = np.stack([v[0].ravel() for v in columns], axis=1)
    e = np.stack([v[1].ravel() for v in columns], axis=1)
    root = np.sqrt(h.ravel()); inv = np.repeat(1/root, 2)
    w = (h.ravel()[:, None]*root[:, None]*d-1.5*root[:, None]*e)*inv
    v = root[:, None]*e*inv
    matrix = np.eye(2*h.size)+(w.T@w+.75*v.T@v)/3
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-14)
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-12


def test_matches_shared_flux_plus_blocked_faces_and_within_cell_bed_traction():
    rng = np.random.default_rng(117)
    h = rng.uniform(.1, 2., (5, 7)); bed = rng.uniform(0., 2., h.shape)
    p, b = rng.normal(size=h.shape), rng.normal(size=h.shape)
    g = ReconstructedPressureGeometry(h, bed, .5, periodic=True)
    expected = []
    for axis, edge, poly in zip((1, 0), g.edges, g.polynomials):
        ta = edge['aa']*p+edge['ca']*b
        tb = edge['ab']*np.roll(p, -1, axis)+edge['cb']*np.roll(b, -1, axis)
        shared = edge['other']*ta+edge['own']*tb
        blocked_plus = p*(poly['hp']/h)-ta
        blocked_minus = p*(poly['hm']/h)-np.roll(tb, 1, axis)
        expected.append((shared-np.roll(shared, 1, axis)+blocked_plus-blocked_minus+
                         b*(poly['deta']-poly['dh']))/.5)
    np.testing.assert_allclose(g.gradient_traction(p, b), np.stack(expected, axis=-1),
                               rtol=1e-13, atol=1e-13)


def test_height_datum_translation_does_not_change_operator():
    rng = np.random.default_rng(119)
    h = rng.uniform(.2, 2., (5, 7)); bed = rng.integers(0, 16, h.shape)/16
    a = ReconstructedPressureGeometry(h, bed, .5, periodic=True)
    b = ReconstructedPressureGeometry(h, bed+2**20, .5, periodic=True)
    for before, after in zip(a.edges, b.edges):
        for name in before:
            np.testing.assert_array_equal(before[name], after[name])


def test_refinement_audit_reports_constant_pressure_defect_not_a_false_pass():
    from audit_reconstructed_pressure_geometry import refinement
    rows = refinement((32, 64))
    assert rows[0]['constant_integrated_pressure_error']['linf'] > .01
    assert rows[1]['constant_integrated_pressure_error']['linf'] > .005
    # A regression recording a detected limitation, not an accuracy acceptance.
    assert rows[1]['candidate_error']['l1'] < rows[0]['candidate_error']['l1']
    assert rows[1]['observed_orders']['constant_integrated_pressure_error']['linf'] < 1.1


def test_column_transfer_preserves_cell_integrated_moment():
    # Mean of reconstructed face P equals cell P when the cut is absent.
    for h, dh in ((2., .5), (1e-100, 1e-100), (1., 2.)):
        minus = transfer_coefficients(h, h-.5*dh, h-.5*dh)
        plus = transfer_coefficients(h, h+.5*dh, h+.5*dh)
        assert .5*(minus[0]+plus[0]) == 1
        assert minus[1] == plus[1] == 0


@pytest.mark.parametrize('h', [1., 1e-100, np.nextafter(0., 1.)])
def test_uniform_thin_columns_keep_identity_without_depth_floor(h):
    assert transfer_coefficients(h, h, h) == (1., 0.)


def test_reconstructed_column_closure_is_not_a_boolean_pressure_switch():
    for face in (1., 1e-6, 1e-18, 0.):
        a, c = transfer_coefficients(2., face, face)
        assert a == face/2 and c == 0
    for wet in (1e-3, 1e-6, 1e-12, 0.):
        a, c = transfer_coefficients(2., 1., wet)
        assert abs(a) <= 1.5*wet*wet
        assert abs(c) <= wet*wet


@pytest.mark.parametrize('args', [(0., 1., 0.), (1., -1., 0.), (1., 1., 2.), (1., 1., -1.),
                                  (np.nan, 1., 0.)])
def test_invalid_transfer_geometry_is_rejected(args):
    with pytest.raises(ValueError):
        transfer_coefficients(*args)
