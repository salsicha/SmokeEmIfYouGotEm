import numpy as np
import pytest

from subcell_point_birth_metric_force import point_metric_force
from subcell_primal_metric_rate import metric_time_force
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_wet_pool_primal_energy import evaluate
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from test_triangle_face_section import sampler
from test_subcell_source_birth_pressure import fixture
from test_subcell_simultaneous_birth_pressure import requests_for, positive_probes


def independent_rate(part, requests, path, newborn_velocity):
    candidate = positive_probes(part, requests, path, newborn_velocity)
    volume = np.array([p['volume'] for p in candidate.pools])
    velocity = np.array([p['momentum'] for p in candidate.pools])[:, None]/volume[:, None, None]
    vd = np.zeros((len(volume), 1))
    vd[len(part.pools):, 0] = 3*volume[len(part.pools):]/path
    return metric_time_force(candidate, velocity, vd), candidate


@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7)])
@pytest.mark.parametrize('newborn_velocity', [(0., 0.), (.27, -.13)])
def test_vector_limit_matches_original_analytic_metric_rate(scales, newborn_velocity):
    part, _, _ = fixture()
    requests = requests_for(part, scales)
    result = point_metric_force(SourceBirthPressure(part), requests)
    errors = []
    for path in (1e-3, 2.5e-4, 6.25e-5):
        rate, _ = independent_rate(part, requests, path, newborn_velocity)
        old_error = np.max(abs(rate['force'][:1, 0]-result['old_force_limit']))
        new_error = np.max(abs(rate['force'][1:, 0]/path-result['newborn_force_over_path_limit']))
        errors.append([old_error, new_error])
        assert rate['direction']['canonical_metric_local_error'] < 1e-10
        assert rate['direction']['energy_coordinate_error'] < 1e-10
    assert np.all(np.array(errors[-1]) < np.array(errors[0])/8)
    np.testing.assert_allclose(rate['force'][:1, 0], result['old_force_limit'], atol=2e-5, rtol=.005)
    np.testing.assert_allclose(rate['force'][1:, 0]/path, result['newborn_force_over_path_limit'], atol=2e-5, rtol=.005)
    assert result['work_identity_error'] < 1e-10
    assert not result['full_front_force_or_impulse_or_time_or_native_or_gameplay_accepted']
    assert all(p['old_pullback_solve']['iterations'] <= 40 for p in result['poles'])


def test_independent_canonical_momentum_difference_and_nonlocal_old_force():
    source = sampler(lambda x, y: x+2*y)
    patch = SubcellGeometryPatch(source, [-.25, .25], (1, 4), [.5, .5],
                                relative_stages=True, exact_sources=True)
    volume, momentum = patch.state_from_stages([[3.17, 2.67, 2.17, -5.]], (.8, .25))
    part = WetPoolPartition(patch, source, [-.25, .25], volume, momentum)
    requests = [(3, int(s), k) for s, k in zip(patch.cells[3].source_triangle_indices, (.7, 1.6))]
    result = point_metric_force(SourceBirthPressure(part), requests)
    assert len(part.pools) == 3
    # First old pool has no direct newborn face. Its pressure response cannot
    # be replaced by a force only on the donor or by a scalar work correction.
    assert np.linalg.norm(result['old_force_limit'][0]) > 1e-7
    path, delta = 1e-5, 1e-7
    values = []
    for value in (path-delta, path+delta):
        candidate = positive_probes(part, requests, value)
        v = np.array([p['volume'] for p in candidate.pools])
        p = np.array([p['momentum'] for p in candidate.pools])[:, None]
        values.append(v[:, None, None]*evaluate(candidate, p)['canonical_velocity'])
    fd = ((values[1]-values[0])/(2*delta))[:, 0]
    np.testing.assert_allclose(fd[:3], result['old_force_limit'], atol=2e-6, rtol=.003)
    np.testing.assert_allclose(fd[3:]/path, result['newborn_force_over_path_limit'], atol=2e-6, rtol=.003)


def test_original_metric_derivative_is_self_adjoint_and_path_covariant():
    velocities = [(1., 0.), (0., 1.), (.8, -.3)]
    results = []
    for velocity in velocities:
        part, _, _ = fixture(velocity)
        requests = requests_for(part, (.7, 1.6))
        context = SourceBirthPressure(part)
        result = point_metric_force(context, requests)
        scaled = point_metric_force(context, [(p, s, 3*k) for p, s, k in requests])
        np.testing.assert_allclose(scaled['old_force_limit'], 3*result['old_force_limit'], atol=1e-11)
        np.testing.assert_allclose(scaled['newborn_force_over_path_limit'],
                                   9*result['newborn_force_over_path_limit'], atol=1e-11)
        results.append(result['old_force_limit'][0])
    np.testing.assert_allclose(results[0][1], results[1][0], atol=1e-11)
    np.testing.assert_allclose(results[2], .8*results[0]-.3*results[1], atol=1e-11)


def test_zero_old_motion_has_zero_leading_force_without_activating_water():
    part, _, _ = fixture((0., 0.))
    context = SourceBirthPressure(part)
    result = point_metric_force(context, requests_for(part))
    np.testing.assert_array_equal(result['old_force_limit'], 0.)
    np.testing.assert_array_equal(result['newborn_force_over_path_limit'], 0.)
    assert context.state_signature() == context.original_state and len(part.pools) == 1


def test_original_source_guards_remain():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    with pytest.raises(ValueError, match='At least one'):
        point_metric_force(context, [])
    with pytest.raises(ValueError, match='Duplicate'):
        point_metric_force(context, [(parent, source, 1.)]*2)
    with pytest.raises(ValueError, match='strictly positive'):
        point_metric_force(context, [(parent, source, 0.)])
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        point_metric_force(context, [(parent, source, 1.)])
    flat, parent, source = fixture(flat=True)
    with pytest.raises(ValueError, match='cubic source storage'):
        point_metric_force(SourceBirthPressure(flat), [(parent, source, 1.)])


def test_original_residual_and_work_gates_reject_corrupt_pullback(monkeypatch):
    from subcell_wet_pool_pressure import WetPoolPressureSystem
    original = WetPoolPressureSystem.solve
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part)
    # Limit construction uses its own original birth-system solver. Only the
    # old-space pullback is corrupted; neither an energy nor a residual repair
    # may conceal this vector error.
    def bad_residual(system, rhs):
        value, stats = original(system, rhs)
        return value, dict(stats, relative_residual=3e-5)
    monkeypatch.setattr(WetPoolPressureSystem, 'solve', bad_residual)
    with pytest.raises(ValueError, match='residual gate'):
        point_metric_force(context, requests)
    def bad_work(system, rhs):
        value, stats = original(system, rhs)
        return 2*value, stats
    monkeypatch.setattr(WetPoolPressureSystem, 'solve', bad_work)
    with pytest.raises(ValueError, match='work identity'):
        point_metric_force(context, requests)


def test_source_locked_audit_checks_both_vector_blocks_without_claiming_evolution():
    from audit_south_fork_simultaneous_birth import analyze, metric_force_probe
    from subcell_source_activation import assembly
    part, _, _ = fixture()
    original = assembly(part, face_scheme='donor')
    result = analyze(part, original['new_region_rates'], original)
    assert result['original_water_unchanged']
    # This one-source receipt fixture does not reach the pre-existing 1e-4
    # all-column operator limit in seven heights. Force convergence cannot
    # silently turn that separate failed gate into an overall audit pass.
    assert not result['pressure_limit_probe_controls_passed']
    for path in result['paths']:
        assert not path['original_newborn_operator_controls_passed']
        assert path['metric_force_probe_controls_passed']
        last = path['rows'][-1]['original_metric_force']
        assert last['old_force_max_norm_relative_error'] < .01
        assert last['newborn_force_max_norm_relative_error'] < .01
        assert not path['analytic_metric_force']['full_front_force_or_impulse_or_time_or_native_or_gameplay_accepted']
    requests = requests_for(part)
    prediction = point_metric_force(SourceBirthPressure(part), requests)
    prediction['old_force_limit'] *= 2
    candidate = positive_probes(part, requests, 1e-5)
    probe = metric_force_probe(part, candidate, 1e-5, prediction)
    assert probe['old_force_max_norm_relative_error'] > .4
    prediction['old_force_limit'][:] = 0
    with pytest.raises(ValueError, match='nonzero vector'):
        metric_force_probe(part, candidate, 1e-5, prediction)
