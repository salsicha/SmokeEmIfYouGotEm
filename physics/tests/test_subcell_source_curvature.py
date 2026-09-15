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


def test_source_curvature_refines_to_independent_analytic_smooth_bed_force(record_property):
    from audit_subcell_nonlinear_metric_stage import fixture
    # Constant vectors make div(w)=0, isolating 3 h (grad(b).w) Hess(b) z.
    # Analytic derivatives of the original prescribed smooth bed, not a
    # numerical derivative or reuse of source curvature/Gram coefficients.
    seed = 2843
    phase = np.random.default_rng(seed).uniform(0, 2*np.pi, 6)
    w, z = np.array([.4, -.2]), np.array([.7, .3])
    errors = {'constant': [], 'variable': []}
    omitted = {'constant': [], 'variable': []}
    for n in (8, 16, 32):
        part, _ = fixture(seed, n)
        s = WetPoolPressureSystem(part, .1)
        curvature = SourceCurvatureTensor(s)
        y, x = np.meshgrid(2*np.pi*(np.arange(n)+.5)/n,
                          2*np.pi*(np.arange(n)+.5)/n, indexing='ij')
        a, b, c = x+phase[0], y+phase[1], 2*x-y+phase[2]
        bed = .35*np.sin(a)*np.cos(b)+.2*np.cos(c)
        h = 1.5-.6*bed+.12*np.sin(x-y+phase[3])
        k = 2*np.pi/16
        bx = k*(.35*np.cos(a)*np.cos(b)-.4*np.sin(c))
        by = k*(-.35*np.sin(a)*np.sin(b)+.2*np.sin(c))
        bxx = k*k*(-.35*np.sin(a)*np.cos(b)-.8*np.cos(c))
        bxy = k*k*(-.35*np.cos(a)*np.sin(b)+.4*np.cos(c))
        byy = k*k*(-.35*np.sin(a)*np.cos(b)-.2*np.cos(c))
        for mode in errors:
            field = np.broadcast_to(w, (n, n, 2)).copy()
            divergence = np.zeros((n, n))
            if mode == 'variable':
                field[..., 0] += .1*np.sin(x+y)
                field[..., 1] += .1*np.cos(x-y)
                divergence = .1*k*(np.cos(x+y)+np.sin(x-y))
            actual = curvature.action(field.reshape(n*n, 1, 2),
                                      np.broadcast_to(z, (n*n, 1, 2))).reshape(n, n, 2)/(16/n)**2
            coefficient = -1.5*h*h*divergence+3*h*(bx*field[..., 0]+by*field[..., 1])
            expected = coefficient[..., None]*np.stack(
                (bxx*z[0]+bxy*z[1], bxy*z[0]+byy*z[1]), axis=-1)
            errors[mode].append(float(np.sqrt(np.mean((actual-expected)**2))))
            omitted[mode].append(float(np.sqrt(np.mean(expected**2))))
    record_property('analytic_curvature_rms_8_16_32', str(errors))
    record_property('omitted_curvature_rms_8_16_32', str(omitted))
    for mode in errors:
        measured, control = errors[mode], omitted[mode]
        assert measured[0]/measured[1] > 3, (mode, errors, omitted)
        assert measured[1]/measured[2] > 3, (mode, errors, omitted)
        assert measured[2] < .1*control[2], (mode, errors, omitted)
