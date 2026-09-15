from types import SimpleNamespace

import numpy as np
import pytest

from subcell_coupled_front_update import coupled_update
from subcell_source_activation import assembly, attempt
from test_subcell_source_activation import dam
from test_subcell_wet_pool_pressure import partition


def test_coupled_transfer_has_exact_positive_solution_and_same_velocity():
    velocity = np.array([.4, -.2])
    source = dict(partition=SimpleNamespace(pools=[dict(volume=1., momentum=velocity)]),
        new_region_rates=[dict(volume_rate=2., momentum_rate=2*velocity)],
        transfers=[(0, 1, 2.)], volume_rate=np.array([-2.]), momentum_rate=np.array([-2*velocity]))
    result = coupled_update(source, 5.)
    np.testing.assert_allclose(result['volume'], [1/11, 10/11], rtol=1e-14)
    np.testing.assert_allclose(result['momentum']/result['volume'][:, None], [velocity, velocity], atol=1e-15)
    assert result['audit']['solve_residual'] < 1e-14
    assert not result['audit']['full_rational_or_energy_or_gameplay_accepted']


def moving_pools():
    pools, _, _, _ = partition(lambda x, y: 0*x, [[1., 1.3, .8]], (1, 3), (.5, .5), (-.5, 0.))
    return pools.with_regions([dict(p, momentum=p['volume']*np.array([.2+.1*i, -.15+.1*i]))
                               for i, p in enumerate(pools.pools)])


@pytest.mark.parametrize('factory', [dam, moving_pools])
@pytest.mark.parametrize('gross_donors', [False, True])
def test_coupled_update_reproduces_original_infinitesimal_face_rates(factory, gross_donors):
    pools = factory()
    source = assembly(pools, face_scheme='donor' if gross_donors else 'paired')
    original_v = np.r_[[p['volume'] for p in pools.pools], np.zeros(len(source['new_region_rates']))]
    original_p = np.concatenate(([p['momentum'] for p in pools.pools], np.zeros((len(source['new_region_rates']), 2))))
    dv = np.r_[source['volume_rate'], [r['volume_rate'] for r in source['new_region_rates']]]
    dp = np.concatenate((source['momentum_rate'], np.array([r['momentum_rate'] for r in source['new_region_rates']]).reshape(-1, 2)))
    errors = []
    for dt in (1e-4, 5e-5, 2.5e-5):
        result = coupled_update(source, dt, gross_donors=gross_donors)
        error = max(np.max(abs((result['volume']-original_v)/dt-dv)),
                    np.max(abs((result['momentum']-original_p)/dt-dp)))
        errors.append(error)
        np.testing.assert_allclose(result['volume'].sum(), original_v.sum(), atol=1e-14)
        np.testing.assert_allclose(result['momentum'].sum(axis=0)-original_p.sum(axis=0), dt*dp.sum(axis=0), atol=1e-14)
    assert 1.99 < errors[0]/errors[1] < 2.01
    assert 1.99 < errors[1]/errors[2] < 2.01


def test_mass_transfer_ledger_matches_gross_rates_and_detects_missing_face():
    source = assembly(dam())
    np.testing.assert_allclose(source['incoming_volume_rate']-source['outgoing_volume_rate'],
                               source['volume_rate'], atol=1e-14)
    source['transfers'] = source['transfers'][1:]
    with pytest.raises(ValueError, match='ledger'):
        coupled_update(source, .02)


def test_coupled_candidate_still_requires_finite_energy_gate():
    result = attempt(dam(), .001, scheme='coupled-frozen')
    assert result['audit']['candidate_accepted'], result['audit']
    assert result['audit']['base_energy_change'] < 0
    assert result['audit']['full_energy_change'] < 0
    assert result['audit']['coupled_update']['pressure_and_bed_work_remain_explicit']
    with pytest.raises(ValueError, match='Unknown'):
        attempt(dam(), .001, scheme='unknown')


def test_zero_net_mass_momentum_exchange_requires_nonincreasing_energy():
    # An independent two-region pure velocity-exchange system. True continuous
    # dynamics decay as exp(-2*k*t); backward Euler would give 1/(1+2*k*t).
    # The original candidate failed this physical gate with -39 amplification.
    # Keep the energy requirement, and independently verify the implicit value.
    velocity = np.array([[0., .1], [0., -.1]])
    rate = 1000*(velocity[::-1]-velocity)
    source = dict(partition=SimpleNamespace(pools=[dict(volume=1., momentum=p) for p in velocity]),
        new_region_rates=[], transfers=[], velocity_exchanges=[(0, 1, 1000.)],
        volume_rate=np.zeros(2), momentum_rate=rate)
    result = coupled_update(source, .02)
    np.testing.assert_array_equal(result['volume'], [1., 1.])
    assert not result['audit']['full_rational_or_energy_or_gameplay_accepted']
    assert np.sum(result['momentum']**2) <= np.sum(velocity**2)+1e-14
    np.testing.assert_allclose(result['momentum'], velocity/41, atol=1e-15)


def test_exchange_uses_new_volume_and_preserves_constant_velocity_during_transfer():
    velocity = np.array([.7, -.3])
    volume = np.array([1., 2.])
    dv = np.array([-.3, .3])
    source = dict(partition=SimpleNamespace(pools=[dict(volume=v, momentum=v*velocity) for v in volume]),
        new_region_rates=[], transfers=[(0, 1, .3)], velocity_exchanges=[(0, 1, 4.)],
        volume_rate=dv, momentum_rate=dv[:, None]*velocity)
    result = coupled_update(source, 3.)
    assert np.max(abs(result['volume']-volume)) > .4
    np.testing.assert_allclose(result['momentum']/result['volume'][:, None], [velocity, velocity], atol=1e-14)
    np.testing.assert_allclose(result['momentum'].sum(axis=0), volume.sum()*velocity, atol=1e-14)


def test_one_cell_periodic_flux_does_not_create_self_donor_transfers():
    pools, _, _, _ = partition(lambda x, y: 0*x, 1., (1, 1), (.5, .5), (0., 0.), (True, True))
    source = assembly(pools)
    assert source['transfers'] == []
    result = coupled_update(source, .02)
    np.testing.assert_allclose(result['volume'], [p['volume'] for p in pools.pools], atol=1e-14)
    np.testing.assert_allclose(result['momentum'], [p['momentum'] for p in pools.pools], atol=1e-14)


def test_direct_face_force_survives_cancellation_of_large_transport_rates():
    volume = np.array([1., 1e-60])
    velocity = np.array([[.7, -.2], [.3, .1]])
    momentum = volume[:, None]*velocity
    generator = np.array([[-1e-20, 0.], [1e-20, 0.]])
    exchange = 2e-6*np.array([[-1., 1.], [1., -1.]])
    force = np.tile([1e-90, -2e-90], (2, 1))
    source = dict(partition=SimpleNamespace(pools=[dict(volume=v, momentum=p) for v, p in zip(volume, momentum)]),
        new_region_rates=[], transfers=[(0, 1, 1e-20)], velocity_exchanges=[(0, 1, 2e-6)],
        volume_rate=generator@volume, momentum_rate=generator@momentum+exchange@velocity+force,
        explicit_force_parts=dict(bed=force))
    result = coupled_update(source, .02)
    assert result['audit']['residual_assembly'] == 'direct-face-and-bed'
    np.testing.assert_array_equal(result['audit']['fastest_region_budget']['explicit_remainder'], force[0])
    assert np.max(np.linalg.norm(result['momentum']/result['volume'][:, None], axis=1)) < 1.


def test_direct_force_ledger_must_still_reproduce_original_rates():
    source = assembly(moving_pools())
    source['explicit_force_parts']['bed'] = source['explicit_force_parts']['bed']+1.
    with pytest.raises(ValueError, match='force ledger'):
        coupled_update(source, .02)


@pytest.mark.parametrize('gross_donors', [False, True])
def test_unrepresentable_positive_donor_volume_is_rejected_without_deletion(gross_donors):
    volume = np.array([1e-250, 1.])
    source = dict(partition=SimpleNamespace(pools=[dict(volume=v, momentum=np.zeros(2)) for v in volume]),
        new_region_rates=[], transfers=[(0, 1, 1e-160)], volume_rate=np.array([-1e-160, 1e-160]),
        momentum_rate=np.zeros((2, 2)), gross_donor_transfers=[(0, 1, 1e-160)])
    # The exact backward-Euler donor is about 5e-339, below float64's range.
    # A global mass tolerance would miss its deletion; positivity must not.
    with pytest.raises(ValueError, match='volume is not positive/finite'):
        coupled_update(source, .02, gross_donors=gross_donors)
    assert source['partition'].pools[0]['volume'] == 1e-250


@pytest.mark.parametrize('gross_donors', [False, True])
def test_front_pressure_uses_same_integrated_transfer_as_front_mass(gross_donors):
    volume, rate, dt = 1e-6, 1e-3, .02
    velocity, force = np.array([2., 0.]), np.array([2e-4, 0.])
    source = dict(partition=SimpleNamespace(pools=[dict(volume=volume, momentum=volume*velocity)]),
        new_region_rates=[dict(volume_rate=rate, momentum_rate=rate*velocity+force, explicit_force_rate=force)],
        transfers=[(0, 1, rate)], gross_donor_transfers=[(0, 1, rate)], front_forces=[(0, 1, force)],
        volume_rate=np.array([-rate]), momentum_rate=np.array([-rate*velocity-force]),
        explicit_force_parts=dict(bed=np.zeros((1, 2)), dry_front=np.array([-force])))
    result = coupled_update(source, dt, gross_donors=gross_donors)
    ratio = 1/(1+dt*rate/volume)
    donor_velocity = velocity-dt*ratio*force/volume
    expected = np.array([donor_velocity, donor_velocity+force/rate])
    np.testing.assert_allclose(result['momentum']/result['volume'][:, None], expected, atol=1e-13)
    np.testing.assert_allclose(result['momentum'].sum(axis=0), volume*velocity, atol=1e-20)


def test_frozen_rusanov_donors_transport_mass_and_momentum_with_the_same_matrix():
    # Independent two-way donor ODE, not a net-discharge-only linearization.
    # The two donor rates are 4.3 and 4, although their net discharge is .3.
    volume = np.array([1., 2.])
    velocity = np.array([[.7, -.3], [-.2, .4]])
    momentum = volume[:, None]*velocity
    outgoing, returning, dt = 4.3, 4., 3.
    a, b = outgoing/volume[0], returning/volume[1]
    rates = np.array([-outgoing+returning, outgoing-returning])
    momentum_rates = np.array([-outgoing*velocity[0]+returning*velocity[1],
                               outgoing*velocity[0]-returning*velocity[1]])
    source = dict(partition=SimpleNamespace(pools=[dict(volume=v, momentum=p) for v, p in zip(volume, momentum)]),
        new_region_rates=[], transfers=[(0, 1, outgoing-returning)],
        velocity_exchanges=[(0, 1, returning)],
        gross_donor_transfers=[(0, 1, outgoing), (1, 0, returning)],
        volume_rate=rates, momentum_rate=momentum_rates,
        explicit_force_parts=dict(bed=np.zeros((2, 2))))
    result = coupled_update(source, dt, gross_donors=True)
    expected_v0 = (volume[0]+dt*b*volume.sum())/(1+dt*(a+b))
    expected_p0 = (momentum[0]+dt*b*momentum.sum(axis=0))/(1+dt*(a+b))
    np.testing.assert_allclose(result['volume'], [expected_v0, volume.sum()-expected_v0], atol=1e-14)
    np.testing.assert_allclose(result['momentum'], [expected_p0, momentum.sum(axis=0)-expected_p0], atol=1e-14)
    assert .5*np.sum(result['momentum']**2/result['volume'][:, None]) <= .5*np.sum(momentum**2/volume[:, None])
    assert result['audit']['momentum_uses_mass_matrix']
    assert result['audit']['implicit_velocity_exchanges'] == 0  # Already in the gross donor matrix.
    old = coupled_update(source, dt)
    assert abs(old['volume'][0]-expected_v0) > .4


def test_gross_transfer_ledger_includes_receivers_and_rejects_a_missing_donor():
    source = assembly(dam(), face_scheme='donor')
    dv = np.r_[source['volume_rate'], [r['volume_rate'] for r in source['new_region_rates']]]
    np.testing.assert_allclose(source['gross_incoming_volume_rate']-source['gross_outgoing_volume_rate'], dv, atol=1e-14)
    source['gross_donor_transfers'] = source['gross_donor_transfers'][1:]
    with pytest.raises(ValueError, match='ledger'):
        coupled_update(source, .02, gross_donors=True)
    with pytest.raises(ValueError, match='gross donor'):
        coupled_update(assembly(dam()), .02, gross_donors=True)


def test_gross_donor_candidate_keeps_all_finite_state_and_energy_gates():
    result = attempt(dam(), .001, scheme='coupled-gross-donor')
    assert result['audit']['candidate_accepted'], result['audit']
    assert result['audit']['base_energy_change'] <= 1e-10
    assert result['audit']['full_energy_change'] <= 1e-10
    assert result['audit']['mass_error'] < 1e-10
    assert result['audit']['momentum_error'] < 1e-10
    assert result['audit']['coupled_update']['momentum_uses_mass_matrix']
    assert not result['audit']['full_rational_model_or_time_history_or_gameplay_accepted']


def test_failed_transfer_neighborhood_retains_incoming_and_outside_connections():
    from subcell_coupled_front_update import transfer_neighborhood
    v = np.array([1., 2., 3., 4., 5.])
    p = np.column_stack((v, -v))
    source = dict(partition=SimpleNamespace(pools=[dict(parent=i, source_triangle_indices=[10+i]) for i in range(5)]),
                  new_region_rates=[])
    edges = [(0, 1, .2), (0, 1, .3), (1, 2, .7), (3, 0, .8), (2, 4, .9)]
    graph = transfer_neighborhood(source, [1], v, p, edges)
    assert [r['index'] for r in graph['regions']] == [0, 1, 2]
    assert graph['regions'][0]['outside_incoming_rate'] == .8
    assert graph['regions'][2]['outside_outgoing_rate'] == .9
    assert graph['transfers'] == [dict(owner=0, receiver=1, rate=.5), dict(owner=1, receiver=2, rate=.7)]
    np.testing.assert_array_equal(graph['regions'][1]['velocity'], [1., -1.])
    assert graph['regions'][1]['failed']
    assert not graph['regions'][0]['failed']
