import numpy as np
import pytest

import audit_source_time_refinement as refinement
from test_subcell_source_activation import dam
from test_subcell_coupled_front_update import moving_pools


def test_source_comparison_is_invariant_to_region_order():
    pools = moving_pools()
    first = refinement.source_state(pools)
    reordered = pools.with_regions(list(reversed(pools.pools)))
    error = refinement.difference(first, refinement.source_state(reordered))
    assert error['source_volume_l1'] == 0
    np.testing.assert_array_equal(error['source_momentum_l1'], 0.)


def test_parent_agreement_cannot_hide_source_water_relocation():
    first = dict(values={(0, 10): np.array([1., .3, -.2]), (0, 11): np.zeros(3)},
                 maximum_pool_storage_error=0., parent_volume=np.array([[1.]]),
                 parent_momentum=np.array([[[.3, -.2]]]))
    second = dict(first, values={(0, 10): np.zeros(3), (0, 11): np.array([1., .3, -.2])})
    error = refinement.difference(first, second)
    assert error['parent_volume_l1'] == 0
    assert error['source_volume_l1'] == 2
    np.testing.assert_allclose(error['source_momentum_l1'], [.6, .4])


def test_each_resolution_starts_from_original_and_never_retries_rejection(monkeypatch):
    pools = dam()
    calls = []
    def rejected(state, dt, scheme):
        calls.append((state, dt, scheme))
        return dict(state=None, audit=dict(candidate_accepted=False, rejection='Required gate failed'))
    monkeypatch.setattr(refinement, 'attempt', rejected)
    result = refinement.audit_refinement(pools, .4, 20)
    assert len(calls) == 3
    assert all(c[0] is pools for c in calls)
    assert [c[1] for c in calls] == [.02, .01, .005]
    assert result['comparisons'] == [None, None]
    assert not result['all_runs_completed']
    assert not result['full_rational_model_or_time_accuracy_or_native_or_gameplay_accepted']


@pytest.mark.parametrize('factory', [dam, moving_pools])
def test_finite_time_front_refinement_reassembles_each_successive_state(factory):
    result = refinement.audit_refinement(factory(), .004, 2)
    assert result['all_runs_completed'], result
    assert [r['accepted_steps'] for r in result['runs']] == [2, 4, 8]
    assert all(r['advanced_seconds'] == .004 for r in result['runs'])
    assert all(c['maximum_pool_storage_error'] < 1e-10 for c in result['comparisons'])
    assert not result['full_rational_model_or_time_accuracy_or_native_or_gameplay_accepted']


def test_finite_time_moving_water_has_first_order_refinement_in_water_and_momentum():
    result = refinement.audit_refinement(moving_pools(), .04, 4)
    assert result['all_runs_completed'], result
    ratios = result['adjacent_difference_ratios'][0]
    assert 1.8 < ratios['source_volume_l1'] < 2.3
    assert all(1.8 < ratio < 2.3 for ratio in ratios['source_momentum_l1'])


def test_original_source_volume_and_momentum_reconstruct_without_renormalization():
    pools = moving_pools()
    state = refinement.source_state(pools)
    sums = np.zeros((len(pools.patch.cells), 3))
    for (parent, _), value in state['values'].items():
        sums[parent] += value
    np.testing.assert_allclose(sums[:, 0], pools.reassembled_volumes.ravel(), atol=1e-14, rtol=0)
    np.testing.assert_allclose(sums[:, 1:], pools.reassembled_momenta.reshape(-1, 2), atol=1e-14, rtol=0)


@pytest.mark.parametrize('horizon, steps, levels', [(0., 2, 3), (float('nan'), 2, 3), (.1, True, 3), (.1, 2, 2)])
def test_refinement_rejects_invalid_requested_scope(horizon, steps, levels):
    with pytest.raises(ValueError):
        refinement.audit_refinement(dam(), horizon, steps, levels)


@pytest.mark.parametrize('exact_sources', [False, True])
def test_successive_partial_lake_at_rest_preserves_terrain_pressure_balance(exact_sources):
    from test_triangle_face_section import sampler
    from subcell_geometry_patch import SubcellGeometryPatch
    from subcell_wet_pool_partition import WetPoolPartition
    source = sampler(lambda x, y: .3*x+.1*y)
    origin = (-.5, 0.)
    patch = SubcellGeometryPatch(source, origin, (1, 3), (.5, .5),
                                relative_stages=True, exact_sources=exact_sources)
    v, p = patch.state_from_stages([[.12, .12, .12]], [0., 0.])
    state = WetPoolPartition(patch, source, origin, v, p)
    original = refinement.source_state(state)
    for _ in range(6):
        result = refinement.attempt(state, .02, scheme='coupled-events')
        assert result['audit']['candidate_accepted'], result['audit']
        assert result['audit']['maximum_candidate_speed_mps'] < 1e-12
        state = result['state']
    error = refinement.difference(original, refinement.source_state(state))
    assert error['source_volume_l1'] < 1e-12
    assert max(error['source_momentum_l1']) < 1e-12


@pytest.mark.parametrize('options, message', [
    (['--pool-refinement-steps', '-1'], '--pool-refinement-steps must be nonnegative'),
    (['--pool-refinement-steps', '2', '--pool-refinement-levels', '2'],
     '--pool-refinement-levels must be at least three'),
])
def test_actual_source_cli_rejects_invalid_refinement_before_opening_sources(monkeypatch, capsys, options, message):
    import audit_south_fork_subcell_kinetic_geometry as actual
    monkeypatch.setattr('sys.argv', ['audit', '--atlas', 'missing-atlas', '--report', 'missing-report']+options)
    with pytest.raises(SystemExit) as exc:
        actual.main()
    assert exc.value.code == 2
    assert message in capsys.readouterr().err
