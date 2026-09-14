import numpy as np
import pytest
from total_depth_pressure import wet_pairs
from total_depth_nonlinear_pressure import (nonlinear_pressure_force, prescribed_boundary_source,
    depth_weights, divergence, gradient, kinematic_terms)


def traces(shape, velocity, acceleration=(0., 0.)):
    ny, nx = shape
    return np.array([[velocity[0], acceleration[0]]]*(2*ny)+[[velocity[1], acceleration[1]]]*(2*nx))


@pytest.mark.parametrize('shape', [(9, 13), (1, 17), (19, 1), (1, 1)])
@pytest.mark.parametrize('velocity', [(1., 0.), (-1., 0.), (0., 1.), (0., -1.)])
def test_uniform_throughflow_has_no_false_boundary_pressure(shape, velocity):
    h = np.ones(shape); bed = h*0; pairs = wet_pairs(h, bed)
    u = np.broadcast_to(velocity, (*shape, 2)).copy(); zero = np.zeros_like(u)
    force, stats = nonlinear_pressure_force(h, bed, u, zero, pairs, .5,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=bed,
        momentum_rate=zero, bed_slope=zero, boundary_velocity=traces(shape, velocity))
    np.testing.assert_array_equal(force, 0)
    assert all(s['relative_residual'] == 0 for s in stats)


def test_time_derivative_of_prescribed_trace_is_essential():
    shape = (9, 13); h = np.ones(shape); bed = h*0; pairs = wet_pairs(h, bed)
    u = np.zeros((*shape, 2)); u[..., 0] = .75; u[..., 1] = -.25
    acceleration = np.array([.125, -.375]); mr = h[..., None]*acceleration
    kw = dict(interpolation='depth_weighted', formulation='kinematic', mass_rate=bed,
              momentum_rate=mr, bed_slope=u*0)
    force, stats = nonlinear_pressure_force(h, bed, u, mr, pairs, .5,
        boundary_velocity=traces(shape, (.75, -.25), acceleration), **kw)
    np.testing.assert_allclose(force, 0, atol=1e-14, rtol=0)
    wrong, _ = nonlinear_pressure_force(h, bed, u, mr, pairs, .5,
        boundary_velocity=traces(shape, (.75, -.25)), **kw)
    assert abs(wrong).max() > .01
    assert all(s['relative_residual'] < 2e-5 for s in stats)


def test_affine_divergence_pressure_boundary_work_identity():
    rng = np.random.default_rng(909)
    h = rng.uniform(.1, 3, (7, 11)); bed = h*0; pairs = wet_pairs(h, bed)
    u = rng.normal(size=(*h.shape, 2)); p = rng.normal(size=h.shape)
    boundary = rng.normal(size=(36, 2)); weights = depth_weights(h)
    lift = prescribed_boundary_source(boundary, h, pairs, .5)[..., 0]
    work = np.sum(u*gradient(p, pairs, .5, weights))+np.sum(p*(divergence(u, pairs, .5, weights)+lift))
    assert abs(work-np.sum(p*lift)) < 1e-13


def test_affine_time_differentiation_matches_discrete_kinematic_identity():
    rng = np.random.default_rng(931)
    h = rng.uniform(.5, 2, (7, 9)); bed = h*0; pairs = wet_pairs(h, bed)
    u = rng.normal(size=(*h.shape, 2)); ht = rng.uniform(-.1, .1, h.shape)
    ut = rng.normal(size=u.shape); trace = rng.normal(size=(32, 2)); epsilon = 1e-6
    weights = depth_weights(h)
    q, _, advective = kinematic_terms(h, bed, u, ht, pairs, .5, weights, u*0, trace)
    def full_div(hh, uu, boundary):
        return divergence(uu, pairs, .5, depth_weights(hh))+prescribed_boundary_source(boundary, hh, pairs, .5)[..., 0]
    tp, tm = trace.copy(), trace.copy();tp[:, 0] += epsilon*trace[:, 1];tm[:, 0] -= epsilon*trace[:, 1]
    dtdiv = (full_div(h+epsilon*ht, u+epsilon*ut, tp)-full_div(h-epsilon*ht, u-epsilon*ut, tm))/(2*epsilon)
    div = full_div(h, u, trace)
    lhs = div**2-dtdiv-np.sum(u*gradient(div, pairs, .5, weights), axis=-1)
    rhs = q-divergence(ut+advective, pairs, .5, weights)
    np.testing.assert_allclose(lhs, rhs, atol=3e-8, rtol=1e-7)


@pytest.mark.parametrize('failure', ['count', 'nan', 'inf_rate', 'periodic', 'dx'])
def test_invalid_prescribed_boundary_refused(failure):
    h = np.ones((3, 5)); p = wet_pairs(h, h*0, failure == 'periodic'); t = traces(h.shape, (1., 0.)); dx = .5
    if failure == 'count': t = t[:-1]
    if failure == 'nan': t[-1, 0] = np.nan
    if failure == 'inf_rate': t[-1, 1] = np.inf
    if failure == 'dx': dx = 0
    with pytest.raises(ValueError): prescribed_boundary_source(t, h, p, dx)


def test_closed_boundary_failure_is_not_silently_promoted():
    h = np.ones((9, 13)); bed = h*0; pairs = wet_pairs(h, bed)
    u = np.zeros((*h.shape, 2)); u[..., 0] = 1
    force, _ = nonlinear_pressure_force(h, bed, u, u*0, pairs, .5,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=bed,
        momentum_rate=u*0, bed_slope=u*0)
    assert abs(force).max() > .1


def test_manufactured_gpu_fixtures_are_finite_reproducible_and_qualified():
    from export_prescribed_pressure_fixtures import cases
    first, second = cases(), cases()
    assert len(first) == 21
    for (name, fields, meta), (other_name, other_fields, other_meta) in zip(first, second):
        assert name == other_name and meta == other_meta
        assert len(fields) == 11
        ny, nx = meta['shape']
        assert fields[-1].shape == (2*(nx+ny), 2)
        np.testing.assert_array_equal(fields[0][..., 0], fields[1][..., 0])
        for a, b in zip(fields, other_fields):
            assert np.isfinite(a).all()
            np.testing.assert_array_equal(a, b)
        assert all(s['relative_residual'] <= 2e-5 and s['iterations'] <= 40 for s in meta['reference_solver'])
        if name.startswith('uniform') or name == 'single_cell_rest':
            np.testing.assert_array_equal(fields[9], 0)
