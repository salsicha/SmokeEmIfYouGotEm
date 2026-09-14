import copy
import numpy as np
import pytest
from replay_requested_reconstructed_owner import requested_replay
import audit_live_temporal_evolution as temporal


def records():
    def packet(t, origin, revision):
        state = np.zeros((2, 3, 4)); state[..., 0] = 1.
        exterior = np.zeros((10, 4)); exterior[:, 0] = 1.
        return dict(nx=3, ny=2, cell_meters=.5, origin_x=origin, origin_y=0,
            native_seconds=t, revision=revision, state=state.ravel().tolist(), bed=[0.]*6,
            exterior_state=exterior.ravel().tolist(), exterior_bed=[0.]*10, face_normal_velocity=[0.]*10)
    obs = [packet(0., 0., 1), packet(1., 0., 2), packet(1., .5, 3),
           packet(2., .5, 4), packet(2., 1., 5), packet(3., 1., 6)]
    record = dict(schema='raftsim.live_nonlinear_owner_audit.v1', shoreline_limiter='unscaled',
        observations=obs, requested_moves=2, completed_moves=0, progress=[.4, 0., 0., 0.])
    request = dict(observations=copy.deepcopy(obs), requested_moves=2, completed_requested_intervals=True,
        progress=[2., 0., 0., 0.], completed_native_seconds=2., state_origin_meters=[1., 0.])
    return record, request


def test_full_requested_target_and_endpoint_move_not_failed_prefix(monkeypatch):
    record, request = records(); durations = []; events = []
    def advance(state, bed, dx, seconds, **kwargs):
        durations.append(seconds)
        assert kwargs['max_trials'] == 4096 and kwargs['shoreline_limiter'] == 'unscaled'
        return state.copy(), dict(elapsed_s=seconds)
    monkeypatch.setattr(temporal.bank, 'advance', advance)
    state, result = requested_replay(record, request, events.append)
    assert durations == [1., 1.]  # Never truncates at the old .4s failure clock.
    assert result['completed'] and result['reached_native_seconds'] == 2.
    assert result['completed_moves'] == 2
    assert result['moves'][-1]['native_seconds'] == 2.
    np.testing.assert_array_equal(state[..., 0], 1.)


def test_requested_source_mismatch_is_not_rewritten():
    record, request = records(); request['observations'][0]['state'][0] = 2.
    with pytest.raises(ValueError, match='Matching'): requested_replay(record, request)


def test_failure_keeps_requested_endpoint_unachieved(monkeypatch):
    record, request = records()
    def fail(*args, **kwargs): raise ValueError('original rate gate')
    monkeypatch.setattr(temporal.bank, 'advance', fail)
    _, result = requested_replay(record, request)
    assert not result['completed'] and result['reached_native_seconds'] == 0.
    assert result['error'] == 'original rate gate'
