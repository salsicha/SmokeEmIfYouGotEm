import numpy as np
import pytest

from subcell_source_curvature import SourceCurvatureTensor, common_depth_moments
from subcell_wet_pool_pressure import WetPoolPressureSystem
from test_subcell_gravity_wave_stage import lake


def test_exact_planar_source_has_no_curvature_even_with_many_source_edges():
    pools = lake(lambda x, y: .25*x+.125*y, .73, (1, 1), (2., 2.), (0., 0.))
    s = WetPoolPressureSystem(pools, .1)
    c = SourceCurvatureTensor(s)
    assert c.scope()['wet_curvature_edges'] == 0
    np.testing.assert_array_equal(c.action(np.ones((1, 1, 2)), np.ones((1, 1, 2))), 0.)


def test_same_region_crease_has_the_independent_distributional_hessian_force():
    depth = .73
    pools = lake(lambda x, y: .25*abs(x)+.125*x, depth, (1, 1), (2., 2.), (0., 0.))
    s = WetPoolPressureSystem(pools, .1)
    c = SourceCurvatureTensor(s)
    assert not pools.internal_faces  # The old hydraulic graph omits these edges.
    assert c.scope()['same_region_curvature_edges'] > 0
    w, z = np.array([[[.4, -.2]]]), np.array([[[.7, .3]]])
    d = s.divergence(w[:, 0])[0]
    # x=0 crease: length 2, normal slope jump .5, mean slope .125.
    coefficient = -1.5*(2*depth**2)*d+3*(2*depth)*.125*w[0, 0, 0]
    expected = np.array([[[coefficient*.5*z[0, 0, 0], 0.]]])
    np.testing.assert_allclose(c.action(w, z), expected, atol=1e-12)
    assert np.max(abs(expected)) > 1e-5


def test_curvature_tensor_is_self_adjoint_on_variable_source_terrain():
    pools = lake(lambda x, y: .125*x*x+.25*y*y+.125*x*y, .73)
    s = WetPoolPressureSystem(pools, .1)
    c = SourceCurvatureTensor(s)
    rng = np.random.default_rng(2840)
    w, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    np.testing.assert_allclose(np.sum(v*c.action(w, u)), np.sum(u*c.action(w, v)), atol=1e-12)
    assert c.scope()['wet_curvature_edges'] > 0
    assert not c.scope()['full_force_or_front_or_time_or_gameplay_accepted']


def test_grid_aligned_curvature_is_not_doubled_or_omitted():
    # Same crease, but it now lies on a Cartesian interface between two pools.
    pools = lake(lambda x, y: .25*abs(x)+.125*x, .73, (1, 2), (1., 2.), (-.5, 0.))
    s = WetPoolPressureSystem(pools, .1)
    c = SourceCurvatureTensor(s)
    assert c.edges and all(edge['kind'] == 'cartesian-source-jump' for edge in c.edges)
    np.testing.assert_allclose(sum(edge['depth_integral']*edge['hessian'] for edge in c.edges),
                               np.diag([.73, 0.]), atol=1e-12)
    rng = np.random.default_rng(2841)
    w, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    np.testing.assert_allclose(np.sum(v*c.action(w, u)), np.sum(u*c.action(w, v)), atol=1e-12)


def test_reflecting_domain_does_not_invent_an_exterior_bed_extension():
    pools = lake(lambda x, y: .25*x, .73)
    c = SourceCurvatureTensor(WetPoolPressureSystem(pools, .1))
    assert not c.edges and not c.unresolved


def test_legacy_geometry_is_not_promoted_to_original_source_curvature():
    with pytest.raises(ValueError, match='exact-source'):
        SourceCurvatureTensor(WetPoolPressureSystem(lake(exact=False), .1))
