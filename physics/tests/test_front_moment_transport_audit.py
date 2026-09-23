from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import json
from types import SimpleNamespace

import numpy as np
import pytest

from audit_south_fork_affine_total_energy import branch_potential
from audit_south_fork_front_moment_transport import check_source, check_coverage
from exact_rational_json import json_default
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_exact_geometry import SourceFragment
from subcell_moving_pressure_metric import PositiveSolve


@pytest.fixture(scope='module')
def data():
    fan = AffineDryFan((0, 0), (3, 4), 1, (F(1, 2), -F(1, 4)), 2, (F(1, 4), -F(1, 8)), gravity=1)
    t = F(1, 5)
    polygon = tuple((F(x), F(y), fan.bed+fan.gradient[0]*x+fan.gradient[1]*y) for x, y in ((-1, -1), (1, -1), (0, 1)))
    whole = SourceFragment(0, polygon, fan.gradient)
    coordinate = lambda p: sum(n*(x-o) for n, x, o in zip(fan.normal, p, fan.origin))
    fragments = tuple(replace(whole, polygon=_clip(polygon, coordinate, side)) for side in (False, True))
    record = dict(status='local-uniform-state-predictor-only', source_id=0, point=fan.origin,
                  normal=fan.normal, local_depth=fan.depth, local_velocity=fan.velocity,
                  original_bed=fan.bed, original_gradient=fan.gradient, time_increment=t,
                  whole=fan.integrate(whole, t), wet_side=fan.integrate(fragments[0], t),
                  dry_side=fan.integrate(fragments[1], t), wet_side_rates=fan.boundary_rates(fragments[0], t),
                  dry_side_rates=fan.boundary_rates(fragments[1], t))
    rate = branch_potential(fan, fragments, t)[1]
    saved = dict(energy_datum=0, physical_time_work=dict(potential_energy_direction=rate),
                  canonical_time_work=dict(potential_energy_direction=rate))
    encoded = json.loads(json.dumps([record, saved], default=lambda x: x.record() if isinstance(x, Radical) else json_default(x)))
    sampler = SimpleNamespace(xyz=np.array(polygon, float), faces=np.array([[0, 1, 2]]))
    return *encoded, sampler


def test_original_source_reconstruction_and_gravity_receipt_without_pressure_solve(data, monkeypatch):
    record, saved, sampler = data
    def forbidden(*args, **kwargs):
        raise AssertionError('Pressure solves are not part of moment transport')
    monkeypatch.setattr(PositiveSolve, 'solve', forbidden)
    monkeypatch.setattr(AffineMovingPressureMetric, 'from_trace', forbidden)
    result = check_source(record, sampler, saved)
    assert result['exact_original_moment_transport_and_gravity_work']
    assert not result['pressure_solve_performed']
    assert not result['dispersive_force_or_interacting_fronts_or_gameplay_accepted']


@pytest.mark.parametrize('corruption', ('physical', 'canonical', 'volume', 'bed'))
def test_changed_source_or_certified_gravity_is_rejected(data, corruption):
    record, saved, sampler = deepcopy(data)
    if corruption in ('physical', 'canonical'):
        saved[corruption+'_time_work']['potential_energy_direction'] = '0'
    elif corruption == 'volume': record['wet_side']['volume'] = '0'
    else: record['original_bed'] = str(F(record['original_bed'])+F(1, 10**400))
    with pytest.raises(ValueError):
        check_source(record, sampler, saved)


@pytest.mark.parametrize('corruption', (None, 'missing', 'order', 'unsupported', 'identity', 'status'))
def test_complete_coverage_and_unchanged_unsupported_source(data, corruption):
    record, _, _ = data
    unsupported = dict(status='unsupported', reason='original slope junction')
    source = dict(schema='raftsim.south_fork.affine_front_predictor.v1', local_rate_controls_passed=True,
                  records=[record, unsupported])
    total = dict(schema='raftsim.south_fork.affine_total_energy.v1', exact_source_total_energy_checks_passed=True,
                 records=[dict(index=0, tested=True, source_id=0),
                          dict(index=1, tested=False, original_record=deepcopy(unsupported))])
    if corruption is None:
        check_coverage(source, total)
        return
    if corruption == 'missing': total['records'].pop()
    elif corruption == 'order': total['records'].reverse()
    elif corruption == 'unsupported': total['records'][1]['original_record']['reason'] = 'discarded'
    elif corruption == 'identity': total['records'][0]['source_id'] = 1
    else: total['records'][1]['tested'] = True
    with pytest.raises(ValueError):
        check_coverage(source, total)
