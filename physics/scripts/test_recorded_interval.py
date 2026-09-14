import copy
import numpy as np
import pytest
from test_live_temporal_evolution import record
from audit_recorded_interval import isolate


def test_isolation_uses_captured_input_not_observed_interior():
    pair = record(); source = dict(observations=[pair['first'], pair['second']])
    before = copy.deepcopy(source)
    endpoints = {}
    for raw in source['observations']:
        state = np.array(raw['state']).reshape(raw['ny'], raw['nx'], 4)[..., :3]
        endpoints[(raw['native_seconds'], (raw['origin_x'], raw['origin_y']))] = state.copy()
    # Source interior is not the evolved input. It must not reset this control.
    source['observations'][0]['state'][0] += 1
    actual, report = isolate(source, endpoints, 0)
    assert report['maximum_state_error'] == 0 and not report['full_history_qualified']
    np.testing.assert_array_equal(actual, next(iter(endpoints.values())))
    assert source['observations'][0]['state'][0] == before['observations'][0]['state'][0]+1


@pytest.mark.parametrize('interval', [-1, 1, .5])
def test_invalid_interval_rejected(interval):
    with pytest.raises(ValueError, match='outside observed'):
        isolate(dict(observations=[{}, {}]), {}, interval)
