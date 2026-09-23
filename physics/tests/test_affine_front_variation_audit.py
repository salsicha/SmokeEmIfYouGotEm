from copy import deepcopy
from fractions import Fraction as F
import json

import pytest

from audit_south_fork_affine_front_variation import check_saved, check_coverage
from exact_rational_json import json_default
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_moving_pressure_metric import PositiveSolve
from subcell_affine_dry_fan import Radical
from test_subcell_affine_moving_pressure import trace, P, PT


@pytest.fixture(scope='module')
def data():
    boundary = trace()
    metric = AffineMovingPressureMetric.from_trace(boundary)
    saved = dict(source_id=17, physical_momentum=P, physical_momentum_rate=PT,
                 boundary_momentum_shift=metric.pairs(metric.offset),
                 boundary_momentum_shift_rate=metric.pairs(metric.offset_rate),
                 boundary_energy_constant=-metric.dual_constant,
                 boundary_energy_constant_rate=-metric.dual_constant_rate,
                 result=metric.evaluate(P, PT))
    return boundary, metric, saved


def test_serialized_saved_states_reused_without_solving(data, monkeypatch):
    boundary, metric, saved = data
    serialize = lambda x: x.record() if isinstance(x, Radical) else json_default(x)
    encoded = json.loads(json.dumps(saved, default=serialize))
    def forbidden(*args):
        raise AssertionError('No solved state may be re-solved by the pullback check')
    monkeypatch.setattr(PositiveSolve, 'solve', forbidden)
    result = check_saved(boundary, metric, encoded)
    assert result['exact_saved_state_and_pullback']
    assert result['physical_time_work']['energy_direction'] == saved['result']['kinetic_energy_rate']
    assert result['canonical_time_work']['energy_direction'] == result['physical_time_work']['energy_direction']
    assert result['physical_time_work']['boundary_flux_work'] != 0
    assert not result['conservative_force_or_open_boundary_or_gameplay_accepted']


@pytest.mark.parametrize('field', ('canonical_velocity', 'canonical_velocity_rate', 'canonical_momentum',
                                 'canonical_momentum_rate', 'auxiliary_velocity', 'auxiliary_velocity_rate',
                                 'kinetic_energy', 'kinetic_energy_rate', 'momentum_work', 'geometry_time_work',
                                 'positive_auxiliary_energy_rate', 'boundary_energy_constant',
                                 'boundary_energy_constant_rate'))
def test_sub_float_corruption_is_not_tolerated(data, field):
    boundary, metric, saved = data
    bad = deepcopy(saved)
    target = bad if field.startswith('boundary_') else bad['result']
    if field.startswith('auxiliary_'):
        target = target['poles'][0]
    if isinstance(target[field], tuple):
        rows = [list(r) for r in target[field]]
        rows[0][0] += F(1, 10**400)
        target[field] = rows
    else:
        target[field] += F(1, 10**400)
    with pytest.raises(ValueError):
        check_saved(boundary, metric, bad)


def coverage(saved):
    record = dict(status='local-uniform-state-predictor-only', source_id=17,
                  wet_side=dict(momentum=P[0]), dry_side=dict(momentum=P[1]),
                  wet_side_rates=dict(momentum_rate=PT[0]), dry_side_rates=dict(momentum_rate=PT[1]))
    unsupported = dict(status='unsupported', reason='unchanged original branch')
    source = dict(schema='raftsim.south_fork.affine_front_predictor.v1', local_rate_controls_passed=True,
                  records=[record, unsupported])
    replay = dict(schema='raftsim.south_fork.affine_moving_pressure.v1', affine_original_poles_checks_passed=True,
                  records=[dict(index=0, tested=True, result=saved), dict(index=1, tested=False, original_record=unsupported)])
    return deepcopy(source), deepcopy(replay)


@pytest.mark.parametrize('corruption', (None, 'missing', 'order', 'unsupported', 'status', 'source', 'momentum', 'rate'))
def test_entire_original_coverage_and_unsupported_records_retained(data, corruption):
    source, replay = coverage(data[2])
    if corruption is None:
        check_coverage(source, replay)
        return
    if corruption == 'missing': replay['records'].pop()
    elif corruption == 'order': replay['records'].reverse()
    elif corruption == 'unsupported': replay['records'][1]['original_record']['reason'] = 'discarded'
    elif corruption == 'status': replay['records'][1]['tested'] = True
    elif corruption == 'source': replay['records'][0]['result']['source_id'] = 18
    else:
        key = 'physical_momentum' if corruption == 'momentum' else 'physical_momentum_rate'
        values = [list(v) for v in replay['records'][0]['result'][key]]
        values[0][0] += F(1, 10**400)
        replay['records'][0]['result'][key] = values
    with pytest.raises(ValueError):
        check_coverage(source, replay)
