from copy import deepcopy
from fractions import Fraction as F
import json

import pytest

from audit_south_fork_affine_front_variation import check_saved
from audit_south_fork_affine_total_energy import branch_potential, check_total, check_pullback_coverage
from exact_rational_json import json_default
from subcell_affine_dry_fan import AffineDryFan, Radical
from subcell_affine_front_total_energy import AffineFrontTotalEnergyVariation
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_moving_pressure_metric import PositiveSolve
from test_affine_front_variation_audit import coverage
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
    pullback = check_saved(boundary, metric, saved)
    fan = AffineDryFan((0, 0), (3, 4), 1, (F(1, 3), -F(1, 4)), 2, (F(1, 5), -F(1, 7)), gravity=1)
    total = AffineFrontTotalEnergyVariation(boundary, metric, P, solved_state=saved['result'], energy_datum=F(1, 3))
    return boundary, fan, saved, pullback, total


def test_serialized_composition_matches_full_total_without_any_pressure_solve(data, monkeypatch):
    boundary, fan, saved, pullback, total = data
    encoded = json.loads(json.dumps([saved, pullback],
                        default=lambda x: x.record() if isinstance(x, Radical) else json_default(x)))
    def forbidden(*args, **kwargs):
        raise AssertionError('No pressure solve or metric construction allowed')
    monkeypatch.setattr(PositiveSolve, 'solve', forbidden)
    monkeypatch.setattr(AffineMovingPressureMetric, 'from_trace', forbidden)
    result = check_total(boundary, fan, F(1, 5), *encoded, datum=F(1, 3))
    assert result['total_energy'] == total.total_energy
    for coordinate, rate in (('physical', PT), ('canonical', saved['result']['canonical_momentum_rate'])):
        full = total.time_work(rate, momentum_coordinate=coordinate)
        for key, value in result[coordinate+'_time_work'].items():
            assert value == full[key]
        assert full['boundary_flux_work'] != 0
    assert not result['pressure_solve_performed']
    assert not result['conservative_force_or_open_boundary_or_gameplay_accepted']


@pytest.mark.parametrize('corruption', ('moments', 'spatial', 'bed', 'work', 'gradient', 'rate', 'dimensions'))
def test_exact_corruption_is_rejected(data, corruption):
    boundary, fan, saved, pullback, _ = deepcopy(data)
    tiny = F(1, 10**400)
    if corruption in ('moments', 'spatial'):
        key = 'depth_moments' if corruption == 'moments' else 'depth_spatial_moments'
        values = list(boundary.geometry.forms[0][key])
        values[1] += tiny
        boundary.geometry.forms[0][key] = values
    elif corruption == 'bed':
        boundary.geometry.forms[0]['bed_at_origin'] += tiny
    elif corruption == 'work':
        pullback['physical_time_work']['boundary_flux_work'] += tiny
    elif corruption == 'rate':
        saved['result']['kinetic_energy_rate'] += tiny
    else:
        grad = pullback['primitive_gradients']['physical']
        rows = [list(row) for row in grad['momentum']]
        if corruption == 'dimensions': rows.pop()
        else: rows[0][0] += tiny
        grad['momentum'] = rows
    with pytest.raises(ValueError):
        check_total(boundary, fan, F(1, 5), saved, pullback)


def test_branch_rate_matches_new_time_quadrature_and_datum_mass(data):
    boundary, fan, _, _, _ = data
    t = F(1, 5)
    energy, rate = branch_potential(fan, boundary.geometry.fragments, t)
    shifted, shifted_rate = branch_potential(fan, boundary.geometry.fragments, t, datum=F(17, 3))
    assert shifted-energy == -F(17, 3)*sum(boundary.geometry.volumes)
    assert shifted_rate-rate == -F(17, 3)*sum(boundary.geometry.volume_rates)
    errors = []
    for divisor in (200, 400, 800):
        eps = t/divisor
        energies = [branch_potential(fan, boundary.geometry.fragments, t+sign*eps)[0] for sign in (-1, 1)]
        errors.append(abs(float((energies[1]-energies[0])/(2*eps)-rate)))
    assert all(a/b > 3.8 for a, b in zip(errors, errors[1:]))
    assert errors[-1] < 1e-6


@pytest.mark.parametrize('corruption', (None, 'missing', 'order', 'unsupported', 'status', 'identity', 'schema'))
def test_original_coverage_retains_unsupported_records(data, corruption):
    source, replay = coverage(data[2])
    pullback = dict(schema='raftsim.south_fork.affine_front_variation.v1', exact_source_pullbacks_passed=True,
                    records=[dict(index=0, tested=True, source_id=17, result=data[3]), deepcopy(replay['records'][1])])
    if corruption is None:
        check_pullback_coverage(source, replay, pullback)
        return
    if corruption == 'missing': pullback['records'].pop()
    elif corruption == 'order': pullback['records'].reverse()
    elif corruption == 'unsupported': pullback['records'][1]['original_record']['reason'] = 'lost'
    elif corruption == 'status': pullback['records'][1]['tested'] = True
    elif corruption == 'identity': pullback['records'][0]['source_id'] = 18
    elif corruption == 'schema': pullback['schema'] = 'unqualified'
    with pytest.raises(ValueError):
        check_pullback_coverage(source, replay, pullback)
