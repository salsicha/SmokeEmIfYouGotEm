import copy
import json
import numpy as np
import pytest
import audit_live_moving_owner as audit
from test_live_temporal_evolution import record


@pytest.mark.parametrize('shift', [(1, 0), (-1, 0), (0, 1), (1, -1)])
def test_exact_retention_and_explicit_inventory(shift):
    pair = record(); closing = audit.source(pair['second'])
    opening = copy.deepcopy(closing); opening['revision'] += 1
    opening['origin_x'] += shift[0]*opening['cell_meters']
    opening['origin_y'] += shift[1]*opening['cell_meters']
    state = closing['state'][..., :3].copy()
    state[..., 0] = np.arange(1, 7).reshape(2, 3)*.125
    state[0, 0, 0] = 1e-30
    state[..., 1] = 2*state[..., 0]; state[..., 2] = -state[..., 0]
    result, exchange, stats = audit.transfer(state, closing, opening)
    for y in range(2):
        for x in range(3):
            px, py = x+shift[0], y+shift[1]
            expected = state[py, px] if 0 <= px < 3 and 0 <= py < 2 else opening['state'][y, x, :3]
            np.testing.assert_array_equal(result[y, x], expected)
    np.testing.assert_allclose((result-state).sum(axis=(0, 1)), exchange.sum(axis=(0, 1)), rtol=0, atol=1e-15)
    assert stats['overlap_cells'] == (3-abs(shift[0]))*(2-abs(shift[1]))


@pytest.mark.parametrize('bad', ['time', 'bed', 'state', 'fractional', 'teleport', 'revision'])
def test_invalid_transition_rejected_without_input_mutation(bad):
    pair = record(); closing = audit.source(pair['second']); opening = copy.deepcopy(closing)
    opening['revision'] += 1; opening['origin_x'] += opening['cell_meters']
    if bad == 'time': opening['native_seconds'] += .03125
    if bad == 'bed': opening['bed'][0, 0] += 1
    if bad == 'state': opening['state'][0, 0, 0] += 1
    if bad == 'fractional': opening['origin_x'] += .25*opening['cell_meters']
    if bad == 'teleport': opening['origin_x'] += 3*opening['cell_meters']
    if bad == 'revision': opening['revision'] = closing['revision']
    state = closing['state'][..., :3].copy(); before = state.copy()
    with pytest.raises(ValueError): audit.transfer(state, closing, opening)
    np.testing.assert_array_equal(state, before)


def moving_record():
    pair = record(); opening = copy.deepcopy(pair['second'])
    opening['revision'] += 1; opening['origin_x'] += opening['cell_meters']
    state = pair['first']['state'].copy()
    return dict(schema='raftsim.live_nonlinear_owner_audit.v1', observations=[pair['first'], pair['second'], opening],
                state=state, progress=[opening['native_seconds'], 0., 0., 0.], completed_moves=1,
                state_origin_meters=[opening['origin_x'], opening['origin_y']], failure='',
                window_exchange=[0.]*len(state), cumulative_boundary_volume=[0.]*40)


def test_temporal_interval_then_move_has_no_time_advance_or_interior_reset():
    value = moving_record(); before = copy.deepcopy(value)
    state, report = audit.replay(value)
    assert value == before and report['cpu_completed'] and report['state_gates_passed']
    assert len(report['intervals']) == 1 and len(report['moves']) == 1
    assert report['gpu_float_water_balance_m3'] == 0
    assert json.loads(json.dumps(report, allow_nan=False))['state_gates_passed'] is True


def test_pending_move_is_not_applied_to_old_committed_state():
    value = moving_record(); value['completed_moves'] = 0
    first = value['observations'][0]; value['state_origin_meters'] = [first['origin_x'], first['origin_y']]
    _, report = audit.replay(value)
    assert report['cpu_completed'] and report['moves'] == []


@pytest.mark.parametrize('limiter,mode',[('continuous',3),('unscaled',5)])
def test_continuous_model_is_fixed_for_every_independent_interval(monkeypatch,limiter,mode):
    value = moving_record(); value['shoreline_limiter'] = limiter; value['summary'] = [1, 1, 1, mode]
    before = copy.deepcopy(value); calls = []; original = audit.temporal.bank.advance
    def advance(*args, **kwargs):
        calls.append(kwargs['shoreline_limiter'])
        return original(*args, **kwargs)
    monkeypatch.setattr(audit.temporal.bank, 'advance', advance)
    _, report = audit.replay(value)
    assert calls == [limiter] and value == before
    assert report['shoreline_limiter'] == limiter and report['state_gates_passed']


@pytest.mark.parametrize('limiter,summary', [('continuous', None), ('continuous', [1,1,1,1]),
    ('binary', [1,1,1,3]), ('unknown', [1,1,1,1]),('unscaled',None),
    ('unscaled',[1,1,1,1]),('unscaled',[1,1,1,3]),('unscaled',[1,1,1,7])])
def test_captured_model_identity_cannot_be_changed(limiter, summary):
    value = moving_record(); value['shoreline_limiter'] = limiter
    if summary is not None: value['summary'] = summary
    with pytest.raises(ValueError, match='model|mode'): audit.replay(value)


def test_readonly_observation_does_not_change_evolution_and_captures_move():
    value = moving_record(); seen = []
    baseline, baseline_report = audit.replay(value)
    def observe(state, time, origin):
        assert not state.flags.writeable
        with pytest.raises(ValueError): state[0, 0, 0] = 99
        seen.append((time, origin))
    actual, report = audit.replay(value, on_state=observe)
    np.testing.assert_array_equal(actual, baseline)
    assert report == baseline_report
    assert seen == [(s['native_seconds'], (s['origin_x'], s['origin_y']))
                    for s in value['observations']]
