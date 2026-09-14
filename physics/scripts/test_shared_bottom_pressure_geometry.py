import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry, transfer_coefficients
from total_depth_nonlinear_pressure import gradient, depth_weights, geometric_bed_slope


def make(h, bed, dx=.5, periodic=True):
    return ReconstructedPressureGeometry(h, bed, dx, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


@pytest.mark.parametrize('periodic', [False, True])
def test_shared_bottom_has_both_physical_constant_moments_and_signed_adjoints(periodic):
    rng = np.random.default_rng(214)
    h = rng.uniform(.1, 2, (5, 7)); bed = rng.uniform(0, 3, h.shape); h[2, 3] = 0
    g = make(h, bed, periodic=periodic)
    slope = geometric_bed_slope(bed, .5, periodic)
    slope[h == 0] = 0
    wet = (h > 0).astype(float); zero = np.zeros_like(h)
    np.testing.assert_array_equal(g.gradient_traction(zero, wet), slope)
    for component in (0, 1):
        u = np.zeros((*h.shape, 2)); u[..., component] = 1
        _, e = g.kinematic_components(u)
        np.testing.assert_array_equal(e, slope[..., component])
    p, b = rng.normal(size=h.shape)*wet, rng.normal(size=h.shape)*wet
    u = rng.normal(size=(*h.shape, 2))
    d, e = g.kinematic_components(u)
    lhs = np.sum(u*g.gradient_traction(p, b)); rhs = -np.sum(p*d)+np.sum(b*e)
    assert abs(lhs-rhs) < 1e-12
    # Every symmetric bed-step contribution cancels in the global force.
    np.testing.assert_allclose(g.gradient_traction(zero, b).sum((0, 1)),
        np.sum(b[..., None]*slope, axis=(0, 1)), atol=1e-13)


def test_fully_wet_flat_variable_depth_preserves_original_pressure_gradient():
    rng = np.random.default_rng(215)
    h = rng.uniform(.1, 3, (5, 7)); bed = np.zeros_like(h); p = rng.normal(size=h.shape)
    g = make(h, bed)
    pairs = [np.ones_like(h, dtype=bool) for _ in (0, 1)]
    np.testing.assert_allclose(g.gradient_traction(p, bed), gradient(p, pairs, .5, depth_weights(h)),
                               atol=2e-15, rtol=1e-15)
    np.testing.assert_array_equal(g.gradient_traction(np.ones_like(h), bed), 0)
    np.testing.assert_allclose(g.gradient_traction(p, bed).sum((0, 1)), 0, atol=1e-13)


def test_shared_bed_action_is_symmetric_with_the_required_diagonal_moment():
    rng = np.random.default_rng(218)
    h = rng.uniform(.1, 2, (3, 4)); bed = rng.uniform(0, 3, h.shape)
    g = make(h, bed); n = h.size
    basis = np.eye(n).reshape(n, *h.shape)
    matrices = [np.stack([g.gradient_traction(np.zeros_like(h), b)[..., k].ravel() for b in basis], axis=1)
                for k in (0, 1)]
    for k, matrix in enumerate(matrices):
        np.testing.assert_allclose(matrix, matrix.T, atol=1e-14)
        np.testing.assert_allclose(matrix@np.ones(n), geometric_bed_slope(bed, .5, True)[..., k].ravel(), atol=1e-14)
    velocity_basis = np.eye(2*n).reshape(2*n, *h.shape, 2)
    components = [g.kinematic_components(u) for u in velocity_basis]
    d = np.stack([v[0].ravel() for v in components], axis=1)
    e = np.stack([v[1].ravel() for v in components], axis=1)
    root = np.sqrt(h.ravel()); inv = np.repeat(1/root, 2)
    w = (h.ravel()[:, None]*root[:, None]*d-1.5*root[:, None]*e)*inv
    v = root[:, None]*e*inv
    matrix = np.eye(2*n)+(w.T@w+.75*v.T@v)/3
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-12


def test_closing_hydrostatic_cut_has_quadratic_pressure_integral():
    for r in (1e-3, 1e-6, 1e-12, 0.):
        a, c = transfer_coefficients(2, 1, r, pressure_trace='integrated_column')
        assert abs(a) <= 3*r*r and abs(c) <= r*r
    with pytest.raises(ValueError, match='Zero reconstructed column'):
        transfer_coefficients(2, 0, 0, pressure_trace='integrated_column')


def test_original_mc_raw_face_pinch_has_vanishing_shared_flux_for_bounded_cell_means():
    # The owning cell stays at h=1; its MC right face tends to the neighbor's
    # small positive depth. One-sided P/H_face is NOT bounded, so explicitly
    # test the actual shared flux, not an invented finite one-sided profile.
    values = []
    # Dyadic inputs make the analytical H_face=neighbor_depth bound exact in
    # the stored reconstruction, including where its rational fallback runs.
    for small in (2.**-10, 2.**-20, 2.**-40, 2.**-140, 2.**-1070, 0.):
        h = np.array([[8., 5., 1., small, small/2, .5, 2.]])
        g = make(h, np.zeros_like(h)); edge = g.edges[0]; point = (0, 2)
        q = np.array([[1., 1., 2., 3., 3., 1., 1.]])
        p = h*q
        ta = edge['aa'][point]*p[point]
        tb = edge['ab'][point]*p[0, 3]
        shared = edge['other'][point]*ta+edge['own'][point]*tb
        assert abs(shared) <= 5*small
        if small:
            assert g.polynomials[0]['ha'][point] > 0
            assert abs(shared/g.polynomials[0]['ha'][point]) <= 5+1e-12
        values.append(shared)
    assert values[-1] == 0
    assert all(a > b for a, b in zip(values, values[1:]))


def test_decimal_pinch_keeps_existing_face_arithmetic_without_repair():
    small = 1e-12
    h = np.array([[8., 5., 1., small, small/2, .5, 2.]])
    before = h.copy(); g = make(h, np.zeros_like(h))
    # Existing MC fast-path cancellation is visible, not silently corrected
    # by this pressure trace. The exact 5 bound cannot be asserted using the
    # rounded face height; this is separate from shared-flux convergence.
    assert g.polynomials[0]['ha'][0, 2] == 9.999778782798785e-13
    np.testing.assert_array_equal(h, before)


def test_manufactured_pressure_force_keeps_second_order_maximum_accuracy():
    from audit_reconstructed_pressure_geometry import refinement
    rows = refinement((32, 64, 128, 256), pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    assert all(row['flat_constant_integrated_pressure_error']['linf'] == 0 for row in rows)
    for row in rows[1:]:
        assert row['observed_orders']['candidate_error']['linf'] > 1.9
        assert row['observed_orders']['candidate_error']['l2'] > 1.9
    # Limiter alignment can vary between adjacent grids; retain the measured
    # per-grid orders and check the overall refinement of BOTH kinematics.
    for name in ('kinematic_divergence_error', 'kinematic_bed_error'):
        order = np.log(rows[0][name]['linf']/rows[-1][name]['linf'])/np.log(256/32)
        assert order > 1.9


@pytest.mark.parametrize('which', ['trace', 'quadrature'])
def test_unknown_model_choices_are_not_silently_accepted(which):
    kw = dict(pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    kw['pressure_trace' if which == 'trace' else 'bed_quadrature'] = 'unknown'
    with pytest.raises(ValueError, match='Unknown research'):
        ReconstructedPressureGeometry(np.ones((3, 4)), np.zeros((3, 4)), .5, **kw)
