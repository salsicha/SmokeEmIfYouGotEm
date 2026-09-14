import numpy as np
import pytest
from directional_pressure_geometry import DirectionalPressureGeometry
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_nonlinear_pressure import nonlinear_pressure
from reconstructed_pressure_rates import DryGeometryTransition, PressureGeometryRate


def make(h, z, periodic=False):
    return ReconstructedPressureGeometry(h, z, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


def fixture():
    h = np.array([[2., 1., 0., 0., .5]])
    ht = np.array([[0., -.125, .125, .0625, 0.]])
    z = np.array([[0., 0., 0., .25, .5]])
    return h, z, ht


def test_right_limit_coefficients_preserve_exact_source_zeros_and_mass_rates():
    h, z, ht = fixture(); originals = [a.copy() for a in (h, z, ht)]
    for a in (h, z, ht): a.flags.writeable = False
    source = make(h, z); g = DirectionalPressureGeometry(source, ht)
    assert g.h is source.h and g.bed is source.bed
    assert g.edges[0]['own'][0, 2] == 2/3
    assert g.edges[0]['other'][0, 2] == 1/3
    assert g.tangent.edges[0]['own'][0, 2] == 0
    assert g.kinematic_support.all()
    for old, value in zip(originals, (h, z, ht)): np.testing.assert_array_equal(old, value)
    errors = []
    for epsilon in (2.**-8, 2.**-16, 2.**-24):
        later = make(h+epsilon*ht, z)
        errors.append(max(abs(a[name]-b[name]).max() for a, b in zip(g.edges, later.edges)
                          for name in ('aa', 'ab', 'ca', 'cb', 'own', 'other', 'shared_b', 'physical_b')))
    assert errors[-1] < 1e-8
    assert errors[-1] < errors[0]/10000
    assert all(not a.flags.writeable for edge in g.edges for a in edge.values())


def test_scalar_trace_and_physical_pressure_have_distinct_dry_domains():
    h, z, ht = fixture(); g = DirectionalPressureGeometry(make(h, z), ht)
    scalar = np.ones_like(h)
    assert np.isfinite(g.scalar_gradient(scalar)).all()
    with pytest.raises(ValueError, match='Dry cells'): g.gradient_traction(scalar, z*0)
    rng = np.random.default_rng(118); u = rng.normal(size=(*h.shape, 2))
    d, _ = g.kinematic_components(u)
    assert abs(np.sum(u*g.scalar_gradient(scalar))+np.sum(scalar*d)) < 1e-14


def test_right_tangent_is_derivative_of_right_branch_not_old_dry_stencil():
    h, z, ht = fixture(); g = DirectionalPressureGeometry(make(h, z), ht)
    rng = np.random.default_rng(119); u = rng.normal(size=(*h.shape, 2))
    d, e = g.kinematic_components(u); dt, et = g.tangent.kinematic_rate(u)
    errors = []
    for epsilon in (2.**-8, 2.**-12, 2.**-16):
        dp, ep = make(h+epsilon*ht, z).kinematic_components(u)
        errors.append(max(abs((dp-d)/epsilon-dt).max(), abs((ep-e)/epsilon-et).max()))
    assert errors[-1] < errors[0]/100
    assert errors[-1] < 2e-5


def matrix(s):
    basis = np.eye(2*s.h.size).reshape(-1, *s.h.shape, 2)
    return np.stack([s.apply(x).ravel() for x in basis], axis=1)


def test_positive_mass_block_limit_and_dry_decoupling_not_full_matrix_identity():
    h, z, ht = fixture(); g = DirectionalPressureGeometry(make(h, z), ht)
    projected = ReconstructedAccelerationSystem(g, 1/3, project_zero_mass_rows=True)
    a = matrix(projected); wet = np.repeat(h.ravel() > 0, 2); dry = ~wet
    errors, couplings = [], []
    for epsilon in (2.**-8, 2.**-16, 2.**-24, 2.**-32):
        later = matrix(ReconstructedAccelerationSystem(make(h+epsilon*ht, z), 1/3))
        errors.append(abs(later[np.ix_(wet, wet)]-a[np.ix_(wet, wet)]).max())
        couplings.append(abs(later[np.ix_(wet, dry)]).max())
    assert errors[-1] < 1e-8 and errors[-1] < errors[0]/10000
    assert all(b < a/100 for a, b in zip(errors, errors[1:]))
    assert couplings[-1] < couplings[0]/100
    # The decoupled massless auxiliary block need NOT have an identity limit.
    assert abs(later[np.ix_(dry, dry)]-a[np.ix_(dry, dry)]).max() > .01


@pytest.mark.parametrize('flat', [True, False])
def test_analytic_nonlinear_force_matches_dyadic_full_conserved_direction(flat):
    h, z, ht = fixture()
    if flat: z = z*0
    state = np.zeros((*h.shape, 3)); state[..., 0] = h
    state[0, :2, 1] = h[0, :2]*.5
    mt = np.zeros((*h.shape, 2)); mt[..., 0] = ht*.5
    rate = np.concatenate((ht[..., None], mt), axis=-1)
    u = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(mt), where=h[..., None] > 0)
    originals = [x.copy() for x in (state, rate, u)]
    force, report = nonlinear_pressure(make(h, z), u, ht, mt, dry_treatment='directional_limit')
    assert report['directional_extension_used'] and report['activating_dry_cells'] == 2
    np.testing.assert_array_equal(report['velocity_trace'][h == 0, 0], .5)
    np.testing.assert_array_equal(force[h == 0], 0)
    errors = []
    for epsilon in (2.**-8, 2.**-16, 2.**-24):
        later = state+epsilon*rate; hl = later[..., 0]
        ul = later[..., 1:]/hl[..., None]
        actual, _ = nonlinear_pressure(make(hl, z), ul, ht, mt)
        errors.append(abs(actual-force).max())
    assert errors[-1] < 1e-8 and errors[-1] < errors[0]/10000
    for old, value in zip(originals, (state, rate, u)): np.testing.assert_array_equal(old, value)


def test_default_reject_and_invalid_direction_are_not_bypassed():
    h, z, ht = fixture(); u = np.zeros((*h.shape, 2)); g = make(h, z)
    with pytest.raises(DryGeometryTransition): nonlinear_pressure(g, u, ht, u)
    bad = ht.copy(); bad[0, 2] = -.125
    with pytest.raises(ValueError): nonlinear_pressure(g, u, bad, u, dry_treatment='directional_limit')
    with pytest.raises(ValueError): nonlinear_pressure(g, u, ht, u, dry_treatment='guess')


def test_unbound_one_sided_rates_cannot_be_applied_to_old_dry_stencil():
    h, z, ht = fixture(); g = make(h, z)
    rate = PressureGeometryRate(g, z, ht, one_sided=True)
    with pytest.raises(ValueError, match='bound'): rate.kinematic_rate(np.zeros((*h.shape, 2)))
    with pytest.raises(ValueError, match='bound'): rate.force_operator_rate(h*0, h*0)
