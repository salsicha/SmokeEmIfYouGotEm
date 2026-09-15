"""Original-source mode components, never full nonlinear model acceptance."""
from fractions import Fraction as F
import numpy as np
import pytest

from subcell_auxiliary_transport import SourceAuxiliaryTransport, face_coupling, geometric_commutator, tensor_derivative_part
from subcell_pressure_kinetic_geometry import quadrature
from subcell_source_face_section import SourceFaceSection
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from test_subcell_gravity_wave_stage import lake


@pytest.mark.parametrize('exact', (False, True))
def test_source_integrated_commutator_matches_independent_pointwise_kinematics(exact):
    pools = lake(lambda x, y: .2*x+.1*y+.1*abs(x), exact=exact)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2810)
    vd = s.h*rng.uniform(-.2, .2, s.h.shape)
    t = WetPoolPressureRate(s, vd)
    u, v = rng.normal(size=(2, len(pools.pools), 1, 2))
    result = geometric_commutator(t, u)
    du, dv = s.divergence(u[:, 0]), s.divergence(v[:, 0])
    dtu, dtv = t.divergence_rate(u[:, 0]), t.divergence_rate(v[:, 0])
    expected = 0.
    for i, pool in enumerate(pools.pools):
        weights, h, slopes = quadrature(pool['storage'], pool['form']['stage_offset'])
        eta_t = vd[i, 0]/pool['form']['wet_area']
        fu, fv = h*du[i]-1.5*(slopes@u[i, 0]), h*dv[i]-1.5*(slopes@v[i, 0])
        ftu, ftv = eta_t*du[i]+h*dtu[i], eta_t*dv[i]+h*dtv[i]
        expected += .5*np.sum(weights*h*(fv*ftu-ftv*fu))
    np.testing.assert_allclose(np.sum(v*result), expected, atol=1e-12)
    np.testing.assert_allclose(np.sum(v*result)+np.sum(u*geometric_commutator(t, v)), 0., atol=1e-12)
    assert np.max(abs(result)) > 1e-5


@pytest.mark.parametrize('right_stage', (1.2, .1, -.1))
def test_original_face_integral_matches_independent_high_order_quadrature(right_stage):
    section = SourceFaceSection([[(F(0), F(-.25)), (F(1), F(.5))]])
    lf, rf = dict(stage_offset=.8, datum=0.), dict(stage_offset=right_stage, datum=0.)
    ls, rs, speed = np.array([.3, -.2]), np.array([.1, .4]), .7
    actual, mass = face_coupling(section, lf, rf, ls, rs, speed)
    # Independent coordinate-space cut and Gauss rule, not the production
    # endpoint/depth-interval parameterization or two-node cubic rule.
    end = min(1., (min(.8, right_stage)+.25)/.75)
    nodes, weights = np.polynomial.legendre.leggauss(8)
    points = .5*end*(nodes+1)
    expected, expected_mass = np.zeros((3, 3)), 0.
    for x, weight in zip(points, weights*.5*end):
        hl, hr = .8-(-.25+.75*x), right_stage-(-.25+.75*x)
        first_l, first_r = np.r_[hl, -1.5*ls], np.r_[hr, -1.5*rs]
        last_l, last_r = np.r_[0., ls], np.r_[0., rs]
        flux = weight*speed*.5*(hl+hr)
        expected += flux*(np.outer(first_l, first_r)+.75*np.outer(last_l, last_r))
        expected_mass += flux
    np.testing.assert_allclose(actual, expected, atol=1e-14)
    np.testing.assert_allclose(mass, expected_mass, atol=1e-14)
    reverse, reverse_mass = face_coupling(section, rf, lf, rs, ls, speed)
    np.testing.assert_allclose(reverse, actual.T, atol=1e-14)
    assert reverse_mass == mass


@pytest.mark.parametrize('exact', (False, True))
def test_shared_source_transport_is_skew_but_not_a_full_force(exact):
    pools = lake(lambda x, y: .2*x+.1*y+.1*abs(x), exact=exact)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2811)
    adv, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    transport = SourceAuxiliaryTransport(s, adv)
    for action in (transport.factor_force, transport.difference_force):
        np.testing.assert_allclose(np.sum(v*action(u))+np.sum(u*action(v)), 0., atol=1e-12)
        assert np.max(abs(action(u))) > 1e-6
    assert not transport.scope()['full_tensor_or_front_or_nonlinear_or_time_or_gameplay_accepted']
    assert transport.scope()['shared_source_faces'] > 0


def test_flat_resolved_transport_and_commutator_reduce_to_original_smooth_factors():
    from rational_terrain_metric_transport import PhysicalFactors, skew_advection
    from reconstructed_acceleration_system import ReconstructedAccelerationSystem
    from smooth_pressure_geometry import SmoothPressureGeometryRate
    from smooth_rational_velocity_stage import make
    n, depth, dx = 4, 1.3, .4
    pools = lake(lambda x, y: 0*x, depth, (n, n), (dx, dx), (-.6, -.6), (True, True))
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2812)
    adv, u = rng.normal(size=(2, n*n, 1, 2))
    ht = rng.normal(size=(n, n))*.1
    g = make(np.full((n, n), depth), np.zeros((n, n)), dx)
    f = PhysicalFactors(ReconstructedAccelerationSystem(g, .1), SmoothPressureGeometryRate(g, g.bed, ht))
    transport = SourceAuxiliaryTransport(s, adv)
    shaped_u, shaped_adv = u.reshape(n, n, 2), adv.reshape(n, n, 2)
    expected = f.transpose(skew_advection(depth*shaped_adv, f.action(shaped_u), dx))
    np.testing.assert_allclose(transport.factor_force(u).reshape(n, n, 2)/dx**2, expected, atol=1e-11)
    t = WetPoolPressureRate(s, ht.reshape(-1, 1)*dx**2)
    np.testing.assert_allclose(geometric_commutator(t, u).reshape(n, n, 2)/dx**2,
                               f.commutator(shaped_u), atol=1e-11)


def test_disconnected_pools_have_no_auxiliary_transport_leakage():
    pools = lake(lambda x, y: 1-abs(x), .37, (1, 1), (2., 2.), (0., 0.))
    s = WetPoolPressureSystem(pools, .1)
    u = np.zeros((2, 1, 2)); u[0] = [1., .2]
    transport = SourceAuxiliaryTransport(s, u)
    np.testing.assert_array_equal(transport.factor_force(u), 0.)
    np.testing.assert_array_equal(transport.difference_force(u), 0.)


def test_zero_volume_direction_has_zero_geometric_commutator():
    pools = lake()
    s = WetPoolPressureSystem(pools, .1)
    t = WetPoolPressureRate(s, np.zeros_like(s.h))
    np.testing.assert_array_equal(geometric_commutator(t, np.ones((len(pools.pools), 1, 2))), 0.)


def test_oblique_internal_source_edges_retain_skew_pairing_and_original_ids():
    from subcell_source_frames import physical_datum
    base = lake(lambda x, y: .2*x-.13*y, .713, (1, 1), (1., 1.), (.11, .07))
    cell, whole = base.patch.cells[0], base.pools[0]
    surface = F(whole['form']['datum'])+F(whole['form']['stage_offset'])
    states = []
    for source in sorted(set(cell.source_triangle_indices)):
        storage = cell.subset_sources([source])
        volume = storage.volume_and_wet_area(float(surface-physical_datum(storage)))[0]
        states.append(dict(parent=0, source_triangle_indices=[int(source)], volume=volume,
                           momentum=volume*np.array([.4, -.2])))
    pools = base.with_regions(states)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2813)
    adv, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    transport = SourceAuxiliaryTransport(s, adv)
    assert any(face['internal_source_edge'] for face in transport.faces)
    assert any(np.all(abs(face['normal']) > .1) for face in pools.internal_faces)
    for action in (transport.factor_force, transport.difference_force):
        np.testing.assert_allclose(np.sum(v*action(u))+np.sum(u*action(v)), 0., atol=1e-11)


def test_inconsistent_legacy_clipped_slopes_are_not_averaged_into_a_source_slope():
    from test_subcell_source_region_faces import regions
    _, pools, _ = regions()
    s = WetPoolPressureSystem(pools, .1)
    with pytest.raises(ValueError, match='inconsistent'):
        SourceAuxiliaryTransport(s, np.ones((len(pools.pools), 1, 2)))


def test_unowned_internal_wet_front_is_reported_not_reclassified_as_wall():
    from test_subcell_source_region_faces import regions
    base, _, states = regions(lambda x, y: 0*x, (2., 2.), (0., 0.))
    omitted = next(state for state in states if np.all(abs(base.sampler.xyz[
        base.sampler.faces[state['source_triangle_indices'][0]], :2]) < 1))
    pools = base.with_regions([state for state in states if state is not omitted])
    s = WetPoolPressureSystem(pools, .1)
    transport = SourceAuxiliaryTransport(s, np.ones((len(pools.pools), 1, 2)))
    assert len(transport.scope()['unresolved_activation_faces']) == 3
    assert not transport.scope()['full_tensor_or_front_or_nonlinear_or_time_or_gameplay_accepted']


def test_face_rotation_and_unrepresentable_nonzero_coefficient():
    section = SourceFaceSection([[(F(0), F(0)), (F(1), F(0))]])
    lf, rf = dict(stage_offset=.8, datum=0.), dict(stage_offset=1.2, datum=0.)
    ls, rs = np.array([.3, -.2]), np.array([.1, .4])
    angle = .61
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    jet_rotation = np.eye(3); jet_rotation[1:, 1:] = rotation
    original, _ = face_coupling(section, lf, rf, ls, rs, .7)
    changed, _ = face_coupling(section, lf, rf, rotation@ls, rotation@rs, .7)
    np.testing.assert_allclose(changed, jet_rotation@original@jet_rotation.T, atol=1e-14)
    thin = dict(stage_offset=1e-200, datum=0.)
    with pytest.raises(ValueError, match='no deletion'):
        face_coupling(section, thin, thin, np.zeros(2), np.zeros(2), 1.)
    matrix, mass = face_coupling(section, thin, thin, np.zeros(2), np.zeros(2), 0.)
    np.testing.assert_array_equal(matrix, 0.)
    assert mass == 0.


def test_original_moving_state_component_audit_does_not_accept_complete_dynamics():
    from audit_source_auxiliary_transport import audit_components
    from test_subcell_wet_pool_pressure_rate import fixture
    result = audit_components(fixture('slope'))
    assert result['source_auxiliary_component_controls_passed']
    assert not result['full_tensor_or_front_or_nonlinear_or_time_or_native_or_gameplay_accepted']


@pytest.mark.parametrize('exact', (False, True))
def test_original_moment_tensor_derivative_is_symmetric(exact):
    pools = lake(lambda x, y: .2*x+.1*y+.1*abs(x), exact=exact)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2814)
    w, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    nu, nv = tensor_derivative_part(s, w, u), tensor_derivative_part(s, w, v)
    np.testing.assert_allclose(np.sum(v*nu), np.sum(u*nv), atol=1e-11)
    assert np.max(abs(nu)) > 1e-5


def test_tensor_derivative_recovers_flat_continuum_stencil_with_original_volume():
    from rational_terrain_metric_transport import tensor_action
    from smooth_rational_velocity_stage import make
    n, depth, dx = 4, 1.3, .4
    pools = lake(lambda x, y: 0*x, depth, (n, n), (dx, dx), (-.6, -.6), (True, True))
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2815)
    w, u = rng.normal(size=(2, n*n, 1, 2))
    g = make(np.full((n, n), depth), np.zeros((n, n)), dx)
    c = depth**3*s.divergence(w[:, 0]).reshape(n, n)
    expected = tensor_action(g, c, np.zeros_like(c), u.reshape(n, n, 2))
    np.testing.assert_allclose(tensor_derivative_part(s, w, u).reshape(n, n, 2)/dx**2,
                               expected, atol=1e-11)


def test_source_face_transport_preserves_exact_datum_and_collapsed_float_coordinates():
    original = SourceFaceSection([[(F(0), F(220)), (F(1, 10000), F(221))]])
    shift = F(10**20)
    translated = SourceFaceSection([[(shift, shift+220), (shift+F(1, 10000), shift+221)]])
    left, right = dict(stage_offset=.7, datum=F(220)), dict(stage_offset=.9, datum=F(220))
    slopes = np.array([.3, -.2])
    matrix, mass = face_coupling(original, left, right, slopes, slopes, .6)
    moved, moved_mass = face_coupling(translated, dict(left, datum=shift+220),
                                     dict(right, datum=shift+220), slopes, slopes, .6)
    np.testing.assert_array_equal(matrix, moved)
    assert mass == moved_mass and mass > 0
    assert translated.segments[0, 0, 0] == translated.segments[0, 1, 0]
