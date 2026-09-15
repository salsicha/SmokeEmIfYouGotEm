from types import SimpleNamespace
import numpy as np
import pytest

from subcell_event_front_update import event_update
from subcell_source_activation import assembly, attempt
from test_subcell_source_activation import dam
from test_subcell_coupled_front_update import moving_pools


def network(volume, velocity, edges, bed=None):
    v, u = np.asarray(volume, float), np.asarray(velocity, float)
    p = v[:, None]*u
    dv, dp = np.zeros(len(v)), np.zeros_like(p)
    for a, b, rate in edges:
        dv[a] -= rate; dv[b] += rate
        dp[a] -= rate*u[a]; dp[b] += rate*u[a]
    body = np.zeros_like(p) if bed is None else np.asarray(bed, float)
    return dict(face_scheme='donor', partition=SimpleNamespace(pools=[dict(volume=a, momentum=b) for a, b in zip(v, p)]),
        new_region_rates=[], gross_donor_transfers=edges, volume_rate=dv, momentum_rate=dp+body,
        pressure_forces=[], front_forces=[], explicit_force_parts=dict(bed=body, wall=np.zeros_like(p)))


def test_extinct_inflowing_chain_conserves_momentum_without_zero_volume_division():
    s = network([1., 1., 1.], [[2., -.3], [-.5, .7], [.2, -.8]], [(0, 1, 2.), (1, 2, 3.)])
    result = event_update(s, 1.)
    np.testing.assert_array_equal(result['volume'], [0., 0., 3.])
    np.testing.assert_array_equal(result['momentum'][:2], 0.)
    np.testing.assert_allclose(result['momentum'].sum(axis=0), [1.7, -.4], atol=1e-14)
    assert result['audit']['zero_regions'] == [0, 1]
    from subcell_coupled_front_update import coupled_update
    old = coupled_update(s, 1., gross_donors=True)
    assert min(old['volume'][:2]) > 0  # Frozen proportional drains have different finite-time dynamics.


@pytest.mark.parametrize('scale', [1., 2.**-900])
def test_event_mixing_preserves_constant_velocity_at_all_volume_scales(scale):
    v = np.array([1., 2., 3.])*scale
    u = np.tile([.3, -.7], (3, 1))
    result = event_update(network(v, u, [(0, 1, 4*scale), (1, 2, 2*scale)]), 1.)
    positive = result['volume'] > 0
    np.testing.assert_allclose(result['momentum'][positive]/result['volume'][positive, None], u[positive], atol=1e-14)
    assert result['volume'][0] == 0


def test_body_force_stops_with_integrated_water_exposure():
    s = network([1., 1.], [[0., 0.], [0., 0.]], [(0, 1, 2.)], [[4., -2.], [0., 0.]])
    result = event_update(s, 1.)
    # V0(t)=1-2t until t=.5; integral(V0 dt)=.25, not a full-second impulse.
    np.testing.assert_array_equal(result['boundary_impulse'], [1., -.5])
    np.testing.assert_allclose(result['momentum'].sum(axis=0), [1., -.5], atol=1e-14)
    assert result['volume'][0] == 0


def test_front_impulse_uses_transferred_parcels_not_growing_owner_exposure():
    # Owner 1 receives much more water during this interval than it held
    # initially. That must not multiply pressure per emitted front parcel.
    s = network([1., 1e-6], [[0., 0.], [0., 0.]], [(0, 1, 10.)])
    rate, force = .001, np.array([.0002, 0.])
    s['gross_donor_transfers'].append((1, 2, rate))
    s['volume_rate'][1] -= rate
    s['momentum_rate'][1] -= force
    s['new_region_rates'] = [dict(volume_rate=rate, momentum_rate=force)]
    s['front_forces'] = [(1, 2, force)]
    result = event_update(s, .02)
    u = result['momentum']/result['volume'][:, None]
    np.testing.assert_allclose(u[2]-u[1], force/rate, atol=1e-13)


def test_positive_remainder_below_float_range_is_not_a_drying_event():
    tiny = float(np.nextafter(0., 1.))
    source = network([tiny, 1.], [[0., 0.], [0., 0.]], [(0, 1, tiny)])
    with pytest.raises(ValueError, match='Positive event volume'):
        event_update(source, .75)
    result = event_update(source, 1.)
    assert result['volume'][0] == 0
    assert result['audit']['zero_regions'] == [0]


def test_wet_side_pressure_uses_its_original_donor_active_time():
    source = network([1., 1e-6, 1e-6], np.zeros((3, 2)), [(0, 1, 10.), (1, 2, .001)])
    force, dt = np.array([.0002, 0.]), .02
    source['pressure_forces'] = [(1, 1, 2, force)]
    source['momentum_rate'][1] -= force
    source['momentum_rate'][2] += force
    result = event_update(source, dt)
    velocity = result['momentum']/result['volume'][:, None]
    # Receiver has retained original water and receives one directed parcel.
    recovered_impulse = result['momentum'][2]-(dt*.001)*velocity[1]
    np.testing.assert_allclose(recovered_impulse, dt*force, atol=1e-13)


def test_event_update_rejects_missing_original_pressure_impulse():
    source = assembly(moving_pools(), face_scheme='donor')
    source['pressure_forces'] = []
    with pytest.raises(ValueError, match='ledger'):
        event_update(source, .02)


@pytest.mark.parametrize('factory', [dam, moving_pools])
def test_event_update_reproduces_original_infinitesimal_flux_and_force(factory):
    source = assembly(factory(), face_scheme='donor')
    old = source['partition'].pools
    n = len(source['new_region_rates'])
    v = np.r_[[p['volume'] for p in old], np.zeros(n)]
    p = np.concatenate(([s['momentum'] for s in old], np.zeros((n, 2))))
    dv = np.r_[source['volume_rate'], [r['volume_rate'] for r in source['new_region_rates']]]
    dp = np.concatenate((source['momentum_rate'], np.array([r['momentum_rate'] for r in source['new_region_rates']]).reshape(-1, 2)))
    errors = []
    for dt in (1e-4, 5e-5, 2.5e-5):
        result = event_update(source, dt)
        errors.append(max(np.max(abs((result['volume']-v)/dt-dv)), np.max(abs((result['momentum']-p)/dt-dp))))
    assert all(1.99 < a/b < 2.01 for a, b in zip(errors, errors[1:]))


def test_event_candidate_keeps_both_finite_energy_gates():
    result = attempt(dam(), .001, scheme='coupled-events')
    assert result['audit']['candidate_accepted'], result['audit']
    assert result['audit']['base_energy_change'] <= 1e-10
    assert result['audit']['full_energy_change'] <= 1e-10
    assert not result['audit']['full_rational_model_or_time_history_or_gameplay_accepted']


@pytest.mark.parametrize('seed', [9401, 9402, 9403])
def test_frozen_mixing_cannot_create_kinetic_energy(seed):
    rng = np.random.default_rng(seed)
    v, u = rng.uniform(.1, 1., 5), rng.normal(size=(5, 2))
    edges = [(i, (i+1)%5, float(rng.uniform(1., 4.))) for i in range(5)]
    result = event_update(network(v, u, edges), 2.)
    wet = result['volume'] > 0
    after = .5*np.sum(result['momentum'][wet]**2/result['volume'][wet, None])
    assert after <= .5*np.sum(v[:, None]*u**2)
    np.testing.assert_allclose(result['momentum'].sum(axis=0), (v[:, None]*u).sum(axis=0), atol=1e-13)
