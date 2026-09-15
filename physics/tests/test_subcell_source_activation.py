import numpy as np
import pytest

from test_subcell_wet_pool_pressure import partition
from triangle_face_section import TriangleFaceSection
from subcell_dry_front_flux import flux
from subcell_source_activation import assembly, attempt, wet_support_transition
from subcell_exact_source_faces import triangle_cut
import audit_source_activation


@pytest.mark.parametrize('height', [1., .13, 1e-50, 1e-150])
def test_dry_dam_break_flat_flux_has_exact_rarefaction_mass_and_pressure(height):
    section = TriangleFaceSection([[[0., 220.], [1., 220.]]], [0., 1.])
    gravity = 9.81
    c = np.sqrt(gravity*height)
    actual, _ = flux(section, height, 220., [0., 0.], [1., 0.], energy_datum=220.)
    expected = np.array([8/27*height*c, 8/27*gravity*height*height, 0.])
    np.testing.assert_allclose(actual, expected, atol=0., rtol=1e-14)


def test_linear_partial_wet_face_integrates_dry_rarefaction_exactly():
    section = TriangleFaceSection([[[0., 0.], [2., 2.]]], [0., 2.])
    result, info = flux(section, 1., 0., [0., 0.], [1., 0.])
    c = np.sqrt(9.81)
    np.testing.assert_allclose(result, [8/27*c*2/5, 8/27*9.81/3, 0.], atol=1e-14)
    np.testing.assert_allclose(info['energy_flux'], 8/27*9.81*c*32/105, atol=1e-14)
    np.testing.assert_allclose(info['branch_projected_widths']['fan'], 1., atol=1e-14)


def test_dry_front_rotation_receding_and_upstream_branches():
    section = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0., 1.])
    c = np.sqrt(9.81)
    zero, _ = flux(section, 1., 0., [-3*c, .2], [1., 0.])
    np.testing.assert_array_equal(zero, 0.)
    actual, _ = flux(section, 1., 0., [2*c, .2], [1., 0.])
    np.testing.assert_allclose(actual, [2*c, 4.5*9.81, .4*c], atol=1e-13)
    rot = np.array([[.6, -.8], [.8, .6]])
    u = np.array([-.4, .7])
    a, ai = flux(section, 1., 0., u, [1., 0.])
    b, bi = flux(section, 1., 0., rot@u, rot@np.array([1., 0.]))
    np.testing.assert_allclose(b, np.r_[a[0], rot@a[1:]], atol=1e-14)
    np.testing.assert_allclose(ai['energy_flux'], bi['energy_flux'], atol=1e-14)
    np.testing.assert_allclose(bi['nonadvective_momentum_flux'], rot@ai['nonadvective_momentum_flux'], atol=1e-14)


def test_front_flux_rejects_unrepresentable_positive_transfer():
    section = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0., 1.])
    with pytest.raises(ValueError, match='underflows'):
        flux(section, 1e-150, 0., [0., 0.], [1., 0.])


def test_upstream_dry_front_keeps_tiny_pressure_separate_from_large_advection():
    section = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0., 1.])
    result, info = flux(section, 1e-100, 0., [1., 0.], [1., 0.])
    assert result[1]-result[0] == 0.  # Subtraction has lost the actual pressure.
    np.testing.assert_allclose(info['nonadvective_momentum_flux'], [4.905e-200, 0.], rtol=1e-14, atol=0.)


@pytest.mark.parametrize('normal_speed', [-1., 1., 2.])
def test_mixed_riemann_branches_match_independent_depth_quadrature(normal_speed):
    section = TriangleFaceSection([[[0., 0.], [2., 2.]]], [0., 2.])
    actual, info = flux(section, 1.3, 0., [normal_speed, .3], [1., 0.])
    nodes, weights = np.polynomial.legendre.leggauss(96)
    switch = normal_speed**2/(9.81 if normal_speed > 0 else 4*9.81)
    knots = sorted(set([0., min(switch, 1.3), 1.3]))
    expected = np.zeros(4)
    for low, high in zip(knots, knots[1:]):
        h = .5*(low+high)+.5*(high-low)*nodes
        for depth, weight in zip(h, weights):
            c = np.sqrt(9.81*depth)
            if normal_speed+2*c <= 0:
                continue
            us = normal_speed if normal_speed >= c else (normal_speed+2*c)/3
            hs = depth if normal_speed >= c else us*us/9.81
            m = hs*us
            value = [m, m*us+.5*9.81*hs*hs, .3*m,
                     m*(.5*(us*us+.3**2)+9.81*(hs+1.3-depth))]
            expected += .5*(high-low)*weight*np.array(value)
    np.testing.assert_allclose(np.r_[actual, info['energy_flux']], expected, atol=2e-10, rtol=2e-10)
    np.testing.assert_allclose(info['nonadvective_momentum_flux'],
        expected[1:3]-expected[0]*np.array([normal_speed, .3]), atol=2e-10, rtol=2e-10)


def dam():
    pools, _, _, _ = partition(lambda x, y: 0*x, [[1., 0.]], (1, 2), (.5, .5), (-.25, 0.))
    for p in pools.pools:
        p['momentum'] = np.zeros(2)
    pools.reassembled_momenta[:] = 0.
    return pools


def test_activation_has_equal_opposite_fluxes_and_explicit_receiving_source_ids():
    pools = dam()
    a = assembly(pools)
    assert a['new_region_rates']
    assert abs(a['net_mass_rate']) < 1e-13
    assert a['momentum_boundary_bed_error'] < 1e-13
    for region in a['new_region_rates']:
        assert region['parent'] == 1
        assert len(region['source_triangle_indices']) == 1
        assert region['volume_rate'] > 0
    np.testing.assert_allclose(sum(r['volume_rate'] for r in a['new_region_rates']), .5*8/27*np.sqrt(9.81), atol=1e-14)


@pytest.mark.parametrize('duration', [1e-5, 1e-4, 1e-3])
def test_dry_dam_activation_conserves_state_and_passes_both_finite_energy_checks(duration):
    pools = dam()
    old_v, old_p = pools.reassembled_volumes.copy(), pools.reassembled_momenta.copy()
    result = attempt(pools, duration)
    assert result['audit']['candidate_accepted'], result['audit']
    assert result['state'] is not None
    assert result['audit']['base_energy_change'] < 0
    assert result['audit']['full_energy_change'] < 0
    assert result['audit']['mass_error'] < 1e-13
    assert result['audit']['momentum_error'] < 1e-13
    assert result['state'].parent_pools[1]
    np.testing.assert_array_equal(pools.reassembled_volumes, old_v)
    np.testing.assert_array_equal(pools.reassembled_momenta, old_p)
    assert not result['audit']['full_rational_model_or_time_history_or_gameplay_accepted']


def test_unsafe_step_is_rejected_without_clipping_or_mutating_source():
    pools = dam()
    a = assembly(pools)
    old = pools.reassembled_volumes.copy()
    result = attempt(pools, 2*a['net_volume_limit'], assembled=a)
    assert result['state'] is None
    assert not result['audit']['candidate_accepted']
    assert 'drains' in result['audit']['rejection']
    np.testing.assert_array_equal(pools.reassembled_volumes, old)
    with pytest.raises(ValueError, match='Matching'):
        attempt(dam(), 1e-4, assembled=a)


def test_steep_dry_front_base_flux_cannot_spend_unavailable_full_model_energy():
    pools, _, _, _ = partition(lambda x, y: 10*x, [[.5, -10.]], (1, 2), (.5, .5), (-.25, 0.))
    for p in pools.pools:
        p['momentum'] = np.zeros(2)
    pools.reassembled_momenta[:] = 0.
    result = attempt(pools, 1e-5)
    assert result['state'] is None
    assert result['audit']['base_energy_change'] < 0
    assert result['audit']['full_energy_change'] > 1e-10
    assert not result['audit']['candidate_accepted']


def test_drying_region_splits_by_original_wet_connectivity_without_losing_state():
    pools, _, _, _ = partition(lambda x, y: 1-abs(x), 1.37)
    old = pools.pools[0]
    volume = old['storage'].volume_and_wet_area(.37)[0]
    momentum = volume*np.array([.4, -.2])
    states, records = wet_support_transition(pools, [dict(old, volume=volume, momentum=momentum)])
    assert len(states) == 2 and records[0]['output_regions'] == 2
    np.testing.assert_allclose(sum(s['volume'] for s in states), volume, atol=1e-14)
    np.testing.assert_allclose(sum((s['momentum'] for s in states), np.zeros(2)), momentum, atol=1e-14)
    candidate = pools.with_regions(states)
    assert len(candidate.pools) == 2


def test_releasing_only_dry_source_support_preserves_stored_volume_and_momentum_exactly():
    pools, _, _, _ = partition(lambda x, y: x, 1.37)
    old = pools.pools[0]
    volume = old['storage'].volume_and_wet_area(-.13)[0]
    momentum = volume*np.array([.4, -.2])
    states, records = wet_support_transition(pools, [dict(old, volume=volume, momentum=momentum)])
    assert len(states) == 1
    assert records[0]['released_zero_water_source_ids']
    assert states[0]['volume'] == volume
    np.testing.assert_array_equal(states[0]['momentum'], momentum)
    assert pools.with_regions(states).pools[0]['volume'] == volume


def test_original_triangle_face_cuts_share_exactly_the_same_nonbinary_endpoint():
    a = np.array([-.123456789123, -.334455667, 1.234])
    b = np.array([.765432109987, .2233445567, .857])
    left = np.array([a, b, [-.3, -.8, 1.]])
    right = np.array([b, a, [.8, .9, 1.]])
    one = triangle_cut(left, [0., 0.], [.4, 2.], 0, 1)
    two = triangle_cut(right, [0., 0.], [.4, 2.], 0, 1)
    shared = set(map(tuple, one)) & set(map(tuple, two))
    assert len(shared) == 1
    assert one[1, 0] == two[0, 0]
    np.testing.assert_array_equal(one, triangle_cut(left, [.4, 0.], [.4, 2.], 0, -1))


def test_history_uses_accepted_state_and_stops_without_retry(monkeypatch):
    from types import SimpleNamespace
    initial, next_state = SimpleNamespace(pools=[0]), SimpleNamespace(pools=[0, 1])
    calls = []
    def fake_attempt(state, duration, scheme):
        assert scheme == 'explicit'
        calls.append((state, duration))
        accepted = state is initial
        return dict(state=next_state if accepted else None,
                    audit=dict(candidate_accepted=accepted, rejection=None if accepted else 'energy'))
    monkeypatch.setattr(audit_source_activation, 'attempt', fake_attempt)
    result = audit_source_activation.audit_history(initial, 5)
    assert calls == [(initial, .02), (next_state, .02)]
    assert result['accepted_steps'] == 1 and result['advanced_seconds'] == .02
    assert result['final_region_count'] == 2
    assert not result['all_requested_steps_passed']
    assert result['attempts'][-1]['start_time'] == .02
    assert not result['nonlinear_model_or_native_or_gameplay_accepted']


def test_history_records_assembly_failure_and_rejects_invalid_requests(monkeypatch):
    pools = dam()
    def failed_attempt(state, duration, scheme):
        raise ValueError('incompatible source face')
    monkeypatch.setattr(audit_source_activation, 'attempt', failed_attempt)
    result = audit_source_activation.audit_history(pools, 2)
    assert result['accepted_steps'] == 0 and result['advanced_seconds'] == 0
    assert result['attempts'][0]['failure_phase'] == 'assembly'
    for steps in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match='step count'):
            audit_source_activation.audit_history(pools, steps)
    with pytest.raises(ValueError, match='duration'):
        audit_source_activation.audit_history(pools, 1, float('nan'))
