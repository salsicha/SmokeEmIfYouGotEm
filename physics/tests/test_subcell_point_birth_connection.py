import numpy as np
import pytest

from subcell_point_birth_connection import point_connection
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_auxiliary_transport import geometric_commutator
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_wet_pool_primal_energy import evaluate
from subcell_primal_metric_rate import metric_time_force
from test_subcell_source_birth_pressure import fixture
from test_subcell_simultaneous_birth_pressure import requests_for, positive_probes


def original_connection(part, requests, path, velocity):
    candidate = positive_probes(part, requests, path, velocity)
    volume = np.array([p['volume'] for p in candidate.pools])
    momentum = np.array([p['momentum'] for p in candidate.pools])[:, None]
    root = np.sqrt(volume)[:, None, None]
    vd = np.zeros((len(volume), 1))
    vd[len(part.pools):, 0] = 3*volume[len(part.pools):]/path
    primal = evaluate(candidate, momentum)
    metric = metric_time_force(candidate, momentum/volume[:, None, None], vd)
    total = .5*metric['auxiliary_force']
    records = []
    for pole in primal['poles']:
        s = WetPoolPressureSystem(candidate, pole['beta'])
        j = geometric_commutator(WetPoolPressureRate(s, vd), pole['normalized_auxiliary_velocity']/root)
        solution, stats = s.solve(j/root)
        assert stats['relative_residual'] < 2e-5
        pulled = root*solution
        total += pole['alpha']*pulled
        records.append((j[:, 0], pulled[:, 0]))
    return total[:, 0], records, candidate


@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7)])
@pytest.mark.parametrize('velocity', [(0., 0.), (.27, -.13)])
def test_complete_geometry_time_coefficient_refines_to_original_terms(scales, velocity):
    part, _, _ = fixture()
    requests = requests_for(part, scales)
    result = point_connection(SourceBirthPressure(part), requests)
    errors = []
    for path in (1e-3, 2.5e-4, 6.25e-5):
        actual, poles, _ = original_connection(part, requests, path, velocity)
        row = []
        for (j, pulled), expected in zip(poles, result['poles']):
            for name, value in [('commutator', j), ('pulled_commutator', pulled)]:
                row.extend((np.max(abs(value[:1]-expected['old_'+name+'_limit'])),
                            np.max(abs(value[1:]/path-expected['newborn_'+name+'_over_path_limit']))))
            assert abs(expected['skew_work_limit']) < 1e-10
        row.extend((np.max(abs(actual[:1]-result['old_connection_limit'])),
                    np.max(abs(actual[1:]/path-result['newborn_connection_over_path_limit']))))
        errors.append(row)
    assert np.all(np.array(errors[-1]) < np.array(errors[0])/8)
    assert max(errors[-1]) < 2e-4
    assert not result['complete_front_transport_or_force_or_time_or_native_or_gameplay_accepted']


def test_original_geometry_time_changes_coupled_newborn_force_without_erasing_it():
    part, _, _ = fixture()
    result = point_connection(SourceBirthPressure(part), requests_for(part, (.7, 1.6)))
    # In this fixture the old pullback cancels internally, whereas only one
    # newborn component cancels the half-metric term. The coupled source
    # cross-Gram term survives. Zero skew work must not be confused with a
    # zero vector or used to erase that physically distinct component.
    np.testing.assert_allclose(result['old_connection_limit'], .5*result['metric']['old_force_limit'], atol=1e-11)
    np.testing.assert_allclose(result['newborn_connection_over_path_limit'][0, 0], 0., atol=1e-11)
    assert np.max(abs(result['newborn_connection_over_path_limit'])) > 1e-4
    assert np.max(abs(result['newborn_connection_over_path_limit']
                      -.5*result['metric']['newborn_force_over_path_limit'])) > 1e-5


def test_zero_old_motion_and_linear_path_reparameterization():
    part, _, _ = fixture((0., 0.))
    result = point_connection(SourceBirthPressure(part), requests_for(part))
    np.testing.assert_array_equal(result['old_connection_limit'], 0.)
    np.testing.assert_array_equal(result['newborn_connection_over_path_limit'], 0.)
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part, (.7, 1.6))
    first = point_connection(context, requests)
    second = point_connection(context, [(p, s, 3*k) for p, s, k in requests])
    np.testing.assert_allclose(second['old_connection_limit'], 3*first['old_connection_limit'], atol=1e-11)
    np.testing.assert_allclose(second['newborn_connection_over_path_limit'],
                               9*first['newborn_connection_over_path_limit'], atol=1e-11)


def test_actual_stage_keeps_unequal_wet_support_guard():
    from subcell_nonlinear_metric_stage import stage
    part, _, _ = fixture()
    _, _, candidate = original_connection(part, requests_for(part), 1e-3, (0., 0.))
    with pytest.raises(ValueError, match='One-sided or unequal wet support'):
        stage(candidate)


def test_original_newborn_pullback_residual_gate_is_not_relaxed(monkeypatch):
    import subcell_point_birth_connection as connection
    original = connection.range_cg
    def bad_residual(*args, **kwargs):
        value, stats = original(*args, **kwargs)
        return value, dict(stats, relative_residual=3e-5)
    monkeypatch.setattr(connection, 'range_cg', bad_residual)
    part, _, _ = fixture()
    with pytest.raises(ValueError, match='connection pullback residual'):
        point_connection(SourceBirthPressure(part), requests_for(part))


def test_source_locked_probe_retains_full_vectors_and_detects_wrong_connection():
    from audit_south_fork_simultaneous_birth import connection_probe
    part, _, _ = fixture()
    requests = requests_for(part, (.7, 1.6))
    expected = point_connection(SourceBirthPressure(part), requests)
    candidate = positive_probes(part, requests, 1e-5)
    original = connection_probe(part, candidate, 1e-5, expected)
    assert original['maximum_term_scaled_error'] < .001
    assert len(original['poles']) == 2
    assert original['newborn_connection_over_path'].shape == (2, 2)
    expected['newborn_connection_over_path_limit'] += 1.
    wrong = connection_probe(part, candidate, 1e-5, expected)
    assert wrong['maximum_term_scaled_error'] > 1.
