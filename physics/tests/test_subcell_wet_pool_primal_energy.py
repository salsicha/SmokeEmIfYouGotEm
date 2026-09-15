import numpy as np
import pytest

from test_subcell_wet_pool_pressure_rate import fixture
from test_subcell_wet_pool_pressure import partition
from subcell_wet_pool_pressure import WetPoolPressureSystem, response
from subcell_wet_pool_pressure_rate import WetPoolPressureRate, dual_direction
from subcell_wet_pool_primal_energy import evaluate, kinetic_volume_gradient
from rational_primal_energy import evaluate as original_energy, K0, BETAS, ALPHAS
from smooth_rational_velocity_stage import make


@pytest.mark.parametrize('kind', ['split', 'slope', 'flat'])
def test_reverse_all_pool_gradient_matches_forward_direction_and_independent_probes(kind):
    pools = fixture(kind)
    system = WetPoolPressureSystem(pools, .4)
    rng = np.random.default_rng(2601)
    q = rng.normal(size=(*system.h.shape, 2))
    vd = system.h*rng.uniform(-.2, .2, system.h.shape)
    reverse = kinetic_volume_gradient(system, q)
    forward = WetPoolPressureRate(system, vd).apply(q)
    np.testing.assert_allclose(reverse['value']@vd[:, 0], .5*np.sum(q*forward)/system.length, atol=2e-12, rtol=1e-12)
    for i, volume in enumerate(system.h[:, 0]):
        step = volume*1e-5
        v = system.h[:, 0].copy()
        v[i] -= step
        low = WetPoolPressureSystem(pools.volume_probe(v), .4)
        v[i] += 2*step
        high = WetPoolPressureSystem(pools.volume_probe(v), .4)
        energy = lambda s: .5*sum(float(f@f) for f in s.factor_action(q))
        np.testing.assert_allclose(reverse['value'][i], (energy(high)-energy(low))/(2*step), rtol=2e-8, atol=3e-8)


@pytest.mark.parametrize('kind', ['split', 'slope', 'flat'])
def test_physical_energy_gradient_and_original_dual_map_are_consistent(kind):
    pools = fixture(kind)
    volumes = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2602)
    p = volumes[:, None, None]*rng.normal(size=(len(volumes), 1, 2))
    pt = volumes[:, None, None]*rng.normal(size=p.shape)
    vd = volumes*rng.uniform(-.2, .2, len(volumes))
    result = evaluate(pools, p)
    assert (result['kinetic_density'] >= 0).all()
    assert result['positive_energy_contraction_error'] < 1e-12
    dual = dual_direction(pools, result['canonical_velocity'], vd[:, None]*0)
    np.testing.assert_allclose(dual['physical_momentum'], p, atol=1e-11, rtol=1e-11)
    np.testing.assert_allclose(dual['kinetic'], result['kinetic'], atol=1e-11, rtol=1e-11)
    expected = result['volume_gradient']@vd+np.sum(result['canonical_velocity']*pt)
    step = 1e-5
    low = evaluate(pools.volume_probe(volumes-step*vd), p-step*pt)
    high = evaluate(pools.volume_probe(volumes+step*vd), p+step*pt)
    np.testing.assert_allclose(expected, (high['total']-low['total'])/(2*step), atol=2e-8, rtol=2e-8)
    assert not result['mass_or_nonlinear_bed_force_or_time_or_gameplay_accepted']


@pytest.mark.parametrize('kind', ['split', 'slope', 'flat'])
def test_positive_factor_realization_equals_independent_dense_original_response_inverse(kind):
    pools = fixture(kind)
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2603)
    p = volume[:, None, None]*rng.normal(size=(len(volume), 1, 2))
    result = evaluate(pools, p)
    basis = np.eye(p.size)
    matrix = np.column_stack([response(pools, e.reshape(p.shape))['value'].ravel() for e in basis])
    q = p/np.sqrt(volume)[:, None, None]
    mapped = np.linalg.solve(matrix, q.ravel()).reshape(p.shape)
    np.testing.assert_allclose(result['canonical_velocity'], mapped/np.sqrt(volume)[:, None, None], atol=1e-11)
    np.testing.assert_allclose(result['kinetic'], .5*np.sum(q*mapped), atol=1e-11)
    assert all(record['iterations'] <= 40 and record['relative_residual'] < 2e-5 for record in result['poles'])


def test_flat_variable_depth_energy_reduces_to_original_physical_metric():
    depth = np.array([[.8, 1.1], [.9, 1.2]])
    dx = .5
    pools, _, _, _ = partition(lambda x, y: x*0, depth, (2, 2), (dx, dx), (-.25, -.25), (True, True))
    momentum_density = depth[..., None]*np.random.default_rng(2604).normal(size=(*depth.shape, 2))
    result = evaluate(pools, (dx**2*momentum_density).reshape(-1, 1, 2))
    original = original_energy(make(depth, np.zeros_like(depth), dx), momentum_density)
    np.testing.assert_allclose(result['kinetic'], original['kinetic'], atol=1e-12)
    np.testing.assert_allclose(result['potential'], original['potential'], atol=1e-12)
    np.testing.assert_allclose(result['canonical_velocity'].reshape(momentum_density.shape), original['canonical_velocity'], atol=1e-11)


def test_independent_same_cell_pools_do_not_exchange_energy_through_the_reverse_gradient():
    pools, _, _, _ = partition(lambda x, y: 1-abs(x), .37)
    p = np.zeros((2, 1, 2)); p[0] = [.3, -.2]
    result = evaluate(pools, p)
    np.testing.assert_array_equal(result['canonical_velocity'][1], 0.)
    np.testing.assert_array_equal(result['volume_gradient_terms']['pressure_geometry'][1], 0.)
    assert min(K0, *BETAS, *ALPHAS) > 0
    for bad in (p[:, 0], p*np.nan):
        with pytest.raises(ValueError):
            evaluate(pools, bad)
    with pytest.raises(ValueError, match='gravity'):
        evaluate(pools, p, 0.)
