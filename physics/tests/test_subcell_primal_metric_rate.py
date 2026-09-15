import numpy as np
import pytest

from subcell_primal_metric_rate import direction, metric_time_force, unscaled_operator_direction
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_pressure_rate import dual_direction
from test_subcell_wet_pool_pressure_rate import fixture
from test_subcell_gravity_wave_stage import lake


@pytest.mark.parametrize('kind', ['split', 'slope', 'flat_resolved'])
def test_inverse_metric_direction_matches_independent_perturbations_and_dual_inverse(kind):
    pools = (lake(lambda x, y: 0*x, 1.+.1*np.arange(12).reshape(3, 4),
                  (3, 4), (.4, .4), (-.6, -.4), (True, True)) if kind == 'flat_resolved' else fixture(kind))
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2780)
    p, pd = volume[:, None, None]*rng.normal(size=(2, len(volume), 1, 2))
    vd = volume[:, None]*rng.uniform(-.1, .1, (len(volume), 1))
    result = direction(pools, p, vd, pd)
    dt = 1e-5
    low = evaluate(pools.volume_probe(volume-dt*vd[:, 0]), p-dt*pd)
    high = evaluate(pools.volume_probe(volume+dt*vd[:, 0]), p+dt*pd)
    np.testing.assert_allclose(result['canonical_velocity_rate'],
        (high['canonical_velocity']-low['canonical_velocity'])/(2*dt), atol=2e-8, rtol=3e-8)
    np.testing.assert_allclose(result['total_energy_rate'], (high['total']-low['total'])/(2*dt), atol=2e-8, rtol=3e-8)
    inverse = dual_direction(pools, result['canonical_velocity'], vd, result['canonical_velocity_rate'])
    np.testing.assert_allclose(inverse['physical_momentum'], p, atol=1e-11, rtol=1e-11)
    np.testing.assert_allclose(inverse['physical_momentum_rate'], pd, atol=1e-11, rtol=1e-11)
    assert result['energy_coordinate_error'] < 1e-11
    assert result['canonical_metric_local_error'] < 1e-11
    np.testing.assert_allclose(sum(result['canonical_metric_local_terms'].values()),
                               result['canonical_momentum_rate'], atol=1e-11)
    assert not result['nonlinear_advection_or_bed_force_or_topology_or_native_or_gameplay_accepted']


@pytest.mark.parametrize('exact', [False, True])
def test_metric_time_force_is_fixed_velocity_derivative_not_fixed_momentum(exact):
    pools = lake(exact=exact)
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2781)
    u = rng.normal(size=(len(volume), 1, 2))
    vd = volume[:, None]*rng.uniform(-.2, .2, (len(volume), 1))
    result = metric_time_force(pools, u, vd)
    dt = 1e-5
    low_v, high_v = volume-dt*vd[:, 0], volume+dt*vd[:, 0]
    low = evaluate(pools.volume_probe(low_v), low_v[:, None, None]*u)
    high = evaluate(pools.volume_probe(high_v), high_v[:, None, None]*u)
    expected = (high_v[:, None, None]*high['canonical_velocity']
                -low_v[:, None, None]*low['canonical_velocity'])/(2*dt)
    np.testing.assert_allclose(result['force'], expected, atol=2e-8, rtol=3e-8)
    np.testing.assert_allclose(result['metric_energy_work'], (high['kinetic']-low['kinetic'])/(2*dt), atol=2e-8, rtol=3e-8)
    np.testing.assert_allclose(result['metric_energy_work'], result['direction']['kinetic_energy_rate'], atol=1e-12)


def test_no_changing_volume_has_no_metric_time_force():
    pools = fixture('split')
    result = metric_time_force(pools, np.ones((len(pools.pools), 1, 2)), np.zeros((len(pools.pools), 1)))
    np.testing.assert_array_equal(result['force'], 0.)


def test_disconnected_pool_direction_cannot_induce_a_canonical_acceleration_elsewhere():
    pools = lake(lambda x, y: 1-abs(x), .37, (1, 1), (2., 2.), (0., 0.))
    p, pd = np.zeros((2, 1, 2)), np.zeros((2, 1, 2))
    p[0] = [.3, -.1]; pd[0] = [-.2, .4]
    vd = np.array([[.01], [0.]])
    result = direction(pools, p, vd, pd)
    np.testing.assert_array_equal(result['canonical_velocity_rate'][1], 0.)


def test_terrain_metric_term_is_present_without_creating_a_flat_bed_reaction():
    for bed, expected_nonzero in ((lambda x, y: .2*x+.1*y, True), (lambda x, y: 0*x, False)):
        pools = lake(bed)
        volume = np.array([p['volume'] for p in pools.pools])
        rng = np.random.default_rng(2782)
        u = rng.normal(size=(len(volume), 1, 2))
        vd = volume[:, None]*rng.uniform(-.2, .2, (len(volume), 1))
        result = metric_time_force(pools, u, vd)
        term = result['direction']['canonical_metric_local_terms']['terrain_metric']
        if expected_nonzero:
            assert np.max(abs(term)) > 1e-5
        else:
            np.testing.assert_array_equal(term, 0.)


@pytest.mark.parametrize('exact', [False, True])
def test_complete_metric_time_operator_is_self_adjoint(exact):
    pools = lake(exact=exact)
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2783)
    u, v = rng.normal(size=(2, len(volume), 1, 2))
    vd = volume[:, None]*rng.uniform(-.3, .3, (len(volume), 1))
    mu = metric_time_force(pools, u, vd)['force']
    mv = metric_time_force(pools, v, vd)['force']
    np.testing.assert_allclose(np.sum(u*mv), np.sum(v*mu), atol=1e-11, rtol=1e-11)


def test_unscaled_geometry_direction_does_not_depend_on_pressure_pole_length():
    from subcell_wet_pool_pressure import WetPoolPressureSystem
    from subcell_wet_pool_pressure_rate import WetPoolPressureRate
    pools = fixture('slope')
    volume = np.array([p['volume'] for p in pools.pools])
    vd = volume[:, None]*.1
    q = np.random.default_rng(2784).normal(size=(len(volume), 1, 2))
    unit = WetPoolPressureRate(WetPoolPressureSystem(pools, 1.), vd)
    small = WetPoolPressureRate(WetPoolPressureSystem(pools, 1e-300), vd)
    np.testing.assert_array_equal(unscaled_operator_direction(unit, q), unscaled_operator_direction(small, q))
    np.testing.assert_allclose(unscaled_operator_direction(unit, q), unit.apply(q), atol=1e-13)
    tiny_q = q*1e-100
    np.testing.assert_array_equal(small.apply(tiny_q), 0.)
    assert np.max(abs(unscaled_operator_direction(small, tiny_q))) > 0


@pytest.mark.parametrize('kind', ['split', 'slope'])
def test_original_state_direction_audit_keeps_full_dynamics_unaccepted(kind):
    from audit_primal_metric_direction import audit_direction
    pools = fixture(kind)
    original = np.array([p['momentum'] for p in pools.pools])
    result = audit_direction(pools)
    assert result['fixed_topology_metric_direction_controls_passed'], result
    assert not result['nonlinear_advection_or_complete_force_or_time_or_native_or_gameplay_accepted']
    np.testing.assert_array_equal(np.array([p['momentum'] for p in pools.pools]), original)
