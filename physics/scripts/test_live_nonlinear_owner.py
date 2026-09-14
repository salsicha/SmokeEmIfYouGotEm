import copy
import numpy as np
import pytest
import audit_live_nonlinear_owner as audit
from test_live_temporal_evolution import record


def owner_record():
    pair = record()
    third = copy.deepcopy(pair['second'])
    third.update(native_seconds=.1875, revision=3)
    pair['second']['state'][0] = 3.
    third['state'][0] = 7.
    return dict(schema='raftsim.live_nonlinear_owner_audit.v1', observations=[pair['first'], pair['second'], third],
                state=pair['first']['state'].copy(), progress=[.1875, 0., 0., 0.], failure='',
                cumulative_boundary_volume=[0.]*40)


def test_multiple_observations_retain_evolved_state_and_inputs():
    value = owner_record(); before = copy.deepcopy(value)
    state, report = audit.replay(value)
    assert value == before
    np.testing.assert_array_equal(state, np.array(value['state']).reshape(2, 3, 4)[..., :3])
    assert report['cpu_completed'] and report['state_gates_passed'] and len(report['intervals']) == 2
    assert not report['scene_accepted'] and not report['normal_solver_promoted']


def test_failed_partial_gpu_time_is_not_mistaken_for_full_interval():
    value = owner_record(); value['progress'] = [.1640625, 0., .0234375, 0.]
    value['failure'] = 'deliberate GPU failure'
    _, report = audit.replay(value)
    assert report['gpu_failure'] and report['cpu_completed']
    assert report['requested_seconds'] == .0390625
    assert report['intervals'][-1]['requested_seconds'] == .0078125


@pytest.mark.parametrize('mutation', ['foam', 'outside', 'bed', 'order'])
def test_invalid_ownership_or_foam_rejected(mutation):
    value = owner_record()
    if mutation == 'foam': value['state'][3] = .1
    if mutation == 'outside': value['progress'][0] = 1
    if mutation == 'bed': value['observations'][2]['bed'][0] = 1
    if mutation == 'order': value['observations'][2]['revision'] = 1
    with pytest.raises(ValueError): audit.replay(value)


def test_failure_keeps_last_valid_cpu_state(monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError('invalid pressure')
    monkeypatch.setattr(audit.temporal.bank, 'advance', fail)
    value = owner_record(); state, report = audit.replay(value)
    assert not report['cpu_completed'] and not report['state_gates_passed']
    np.testing.assert_array_equal(state, np.array(value['state']).reshape(2, 3, 4)[..., :3])
