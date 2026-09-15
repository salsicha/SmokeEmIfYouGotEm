import numpy as np
import pytest

from subcell_wet_pool_partition import WetPoolPartition
from subcell_wet_pool_pressure import WetPoolPressureSystem
from audit_subcell_nonlinear_metric_stage import fixture, compare
from test_subcell_gravity_wave_stage import lake


def configured(part):
    return WetPoolPartition(part.patch, part.sampler, part.origin,
        part.reassembled_volumes, part.reassembled_momenta,
        pressure_preconditioner='spectral-frozen-depth')


def test_periodic_flat_reference_inverts_original_full_source_matrix():
    part = configured(lake(lambda x, y: 0*x, 1.3, (8, 8), (.2, .2), (-.7, -.7), (True, True)))
    s = WetPoolPressureSystem(part, .31)
    rhs = np.random.default_rng(2852).normal(size=(64, 1, 2))
    inverse = s.precondition(rhs, 'spectral-frozen-depth')
    np.testing.assert_allclose(s.apply(inverse), rhs, atol=1e-12, rtol=0)
    solved, info = s.solve(rhs)
    np.testing.assert_allclose(solved, inverse, atol=1e-12, rtol=0)
    assert info['iterations'] <= 40 and info['relative_residual'] < 1e-12
    assert info['preconditioner'] == 'spectral-frozen-depth'


def test_variable_source_preconditioner_is_spd_without_replacing_physical_matrix():
    part, _ = fixture(2843, 8)
    selected, _ = fixture(2843, 8, preconditioner='spectral-frozen-depth')
    original, candidate = WetPoolPressureSystem(part, .31), WetPoolPressureSystem(selected, .31)
    rng = np.random.default_rng(2853)
    u, v = rng.normal(size=(2, 64, 1, 2))
    np.testing.assert_array_equal(original.apply(u), candidate.apply(u))
    np.testing.assert_array_equal(original.coefficients, candidate.coefficients)
    pu, pv = (candidate.precondition(value, 'spectral-frozen-depth') for value in (u, v))
    assert np.sum(u*pu) > 0
    np.testing.assert_allclose(np.sum(v*pu), np.sum(u*pv), atol=1e-12, rtol=0)
    # The reference is NOT used as the actual variable-terrain inverse.
    assert np.max(abs(candidate.apply(pu)-u)) > 1e-3
    solved, info = candidate.solve(u)
    np.testing.assert_allclose(candidate.apply(solved), u, atol=1e-10, rtol=0)
    assert info['iterations'] <= 40 and info['relative_residual'] < 1e-10
    assert part.pressure_preconditioner == 'auto'


@pytest.mark.parametrize('part', [
    lambda: lake(),
    lambda: lake(lambda x, y: 0*x, 1.3, periodic=(True, True), exact=False),
    lambda: lake(lambda x, y: .5*abs(x), .3, (1, 1), (2., 2.), (0., 0.), (True, True)),
])
def test_unqualified_wall_legacy_or_partial_wet_geometry_rejects(part):
    s = WetPoolPressureSystem(configured(part()), .1)
    with pytest.raises(ValueError, match='Spectral reference requires'):
        s.solve(np.ones((len(s.h), 1, 2)))


def test_unknown_source_preconditioner_rejects():
    with pytest.raises(ValueError, match='Unknown original-source'):
        WetPoolPartition(None, None, None, None, None, pressure_preconditioner='relaxed')


def test_combined_stage_keeps_original_budgets_with_opt_in_preconditioning():
    result = compare(2843, 8, preconditioner='spectral-frozen-depth')
    assert result['maximum_solve_residual'] < 2e-5
    for name in ('local_momentum_ledger_error', 'metric_time_ledger_error',
                 'skew_ledger_error', 'energy_rate', 'maximum_roundtrip_error'):
        assert abs(result[name]) < 1e-10
    assert not result['full_continuum_or_topology_or_time_or_native_or_gameplay_accepted']


def test_nonlinear_audit_preserves_stage_rejection_without_accepting_a_partial_run(monkeypatch, tmp_path):
    import json
    import sys
    import audit_subcell_nonlinear_metric_stage as audit
    report = tmp_path/'rejected.json'
    calls = []

    def rejected(seed, n, **options):
        calls.append((seed, n, options))
        raise ValueError('Original force/energy gate failed')

    monkeypatch.setattr(audit, 'compare', rejected)
    monkeypatch.setattr(sys, 'argv', ['audit', '--report', str(report), '--resolutions', '64', '128'])
    assert audit.main() == 1
    result = json.loads(report.read_text())
    assert len(calls) == len(result['records']) == 1
    assert result['records'][0]['failure'] == 'Original force/energy gate failed'
    assert result['records'][0]['resolution'] == 64
    assert result['implementation_hashes']
    assert not result['full_continuum_or_topology_or_time_or_native_or_gameplay_accepted']
