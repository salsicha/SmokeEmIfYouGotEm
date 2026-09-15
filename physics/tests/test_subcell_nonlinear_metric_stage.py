import numpy as np
import pytest

from subcell_nonlinear_metric_stage import stage
from subcell_source_curvature import SourceCurvatureTensor
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_metric_force_ledger import divergence_transpose
from test_subcell_gravity_wave_stage import lake


@pytest.mark.parametrize('bed', (lambda x, y: .25*x+.125*y,
                               lambda x, y: .25*abs(x)+.125*x,
                               lambda x, y: .125*x*x+.25*y*y+.125*x*y))
@pytest.mark.parametrize('include_curvature', (False, True))
def test_coupled_source_mass_energy_and_local_physical_force_budgets(bed, include_curvature):
    pools = lake(bed)
    volume = np.array([p['volume'] for p in pools.pools])
    p = volume[:, None, None]*np.random.default_rng(2846).normal(size=(len(volume), 1, 2))*.3
    result = stage(pools, p, include_curvature=include_curvature)
    for key in ('local_momentum_ledger_error', 'metric_time_ledger_error', 'skew_ledger_error',
                'energy_rate', 'net_mass_rate', 'skew_energy_work'):
        assert abs(result[key]) < 1e-10, key
    np.testing.assert_allclose(result['physical_momentum_rate'][:, 0].sum(axis=0),
                               (result['bed_force']+result['wall_force']).sum(axis=0), atol=1e-10)
    assert result['maximum_solve_residual'] < 2e-5
    assert not result['full_continuum_or_topology_or_time_or_native_or_gameplay_accepted']


def test_nonflat_lake_at_rest_and_velocity_reversal():
    pools = lake(lambda x, y: .125*x*x+.25*y*y+.125*x*y)
    volume = np.array([p['volume'] for p in pools.pools])
    p = volume[:, None, None]*np.random.default_rng(2847).normal(size=(len(volume), 1, 2))*.3
    resting = stage(pools, np.zeros_like(p))
    np.testing.assert_allclose(resting['physical_momentum_rate'], 0., atol=1e-11)
    np.testing.assert_array_equal(resting['volume_rate'], 0.)
    forward, reverse = stage(pools, p), stage(pools, -p)
    np.testing.assert_allclose(forward['physical_momentum_rate'], reverse['physical_momentum_rate'], atol=1e-11)
    np.testing.assert_allclose(forward['volume_rate'], -reverse['volume_rate'], atol=1e-11)


def test_flat_source_has_no_spurious_local_bed_force_or_net_momentum_change():
    n, dx = 4, .4
    pools = lake(lambda x, y: 0*x, 1.3, (n, n), (dx, dx), (-.6, -.6), (True, True))
    volume = np.array([p['volume'] for p in pools.pools])
    p = volume[:, None, None]*np.random.default_rng(2848).normal(size=(n*n, 1, 2))*.3
    result = stage(pools, p)
    np.testing.assert_array_equal(result['bed_force'], 0.)
    np.testing.assert_array_equal(result['wall_force'], 0.)
    np.testing.assert_allclose(result['physical_momentum_rate'].sum(axis=0), 0., atol=1e-11)


def test_original_source_curvature_changes_the_nonlinear_force_not_energy_work():
    pools = lake(lambda x, y: .125*x*x+.25*y*y+.125*x*y)
    volume = np.array([p['volume'] for p in pools.pools])
    p = volume[:, None, None]*np.random.default_rng(2849).normal(size=(len(volume), 1, 2))*.3
    full, omitted = stage(pools, p), stage(pools, p, include_curvature=False)
    assert np.max(abs(full['physical_momentum_rate']-omitted['physical_momentum_rate'])) > 1e-6
    assert abs(full['energy_rate']) < 1e-10 and abs(omitted['energy_rate']) < 1e-10


@pytest.mark.parametrize('derivative', (False, True))
def test_scalar_and_tensor_stress_ledgers_match_independent_graph_transpose(derivative):
    pools = lake(lambda x, y: .125*x*x+.25*y*y)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2850)
    vd = s.h*rng.uniform(-.2, .2, s.h.shape)
    t = WetPoolPressureRate(s, vd)
    action = t.transpose_rate if derivative else s.divergence_transpose
    scalar = rng.normal(size=len(pools.pools))
    np.testing.assert_allclose(divergence_transpose(pools, scalar, vd if derivative else None).action()[:, 0],
                               action(scalar), atol=1e-12)
    tensor = rng.normal(size=(len(pools.pools), 2, 2))
    expected = np.stack([sum(action(tensor[:, i, j])[:, j] for j in range(2)) for i in range(2)], axis=-1)
    np.testing.assert_allclose(divergence_transpose(pools, tensor, vd if derivative else None).action()[:, 0],
                               expected, atol=1e-12)


def test_unowned_source_front_rejects_full_stage_instead_of_returning_partial_rate():
    from test_subcell_source_region_faces import regions
    # Only inspect the support gate; legacy geometry must not reach curvature.
    base, _, states = regions(lambda x, y: 0*x, (2., 2.), (0., 0.))
    omitted = next(state for state in states if np.all(abs(base.sampler.xyz[
        base.sampler.faces[state['source_triangle_indices'][0]], :2]) < 1))
    candidate = base.with_regions([state for state in states if state is not omitted])
    with pytest.raises(ValueError, match='source activation'):
        stage(candidate)


def test_invalid_state_and_curvature_switch_reject():
    pools = lake()
    with pytest.raises(ValueError, match='physical pool'):
        stage(pools, np.zeros((4, 2)))
    with pytest.raises(ValueError, match='Explicit'):
        stage(pools, include_curvature='full')


def test_within_triangle_factor_connection_matches_independent_volume_quadrature():
    from subcell_auxiliary_transport import SourceAuxiliaryTransport
    from subcell_pressure_kinetic_geometry import quadrature
    pools = lake(lambda x, y: .25*x+.125*y)
    s = WetPoolPressureSystem(pools, .1)
    rng = np.random.default_rng(2851)
    adv, u, v = rng.normal(size=(3, len(pools.pools), 1, 2))
    transport = SourceAuxiliaryTransport(s, adv)
    du, dv = s.divergence(u[:, 0]), s.divergence(v[:, 0])
    expected = 0.
    for i, pool in enumerate(pools.pools):
        weights, h, b = quadrature(pool['storage'], pool['form']['stage_offset'])
        fu, fv = h*du[i]-1.5*(b@u[i, 0]), h*dv[i]-1.5*(b@v[i, 0])
        advh = -(b@adv[i, 0])
        expected += .5*np.sum(weights*h*(fv*advh*du[i]-advh*dv[i]*fu))
    np.testing.assert_allclose(np.sum(v*transport.volume_factor_force(u)), expected, atol=1e-12)
    assert abs(expected) > 1e-6


def test_same_region_slope_jumps_participate_in_auxiliary_advection():
    from subcell_auxiliary_transport import SourceAuxiliaryTransport
    pools = lake(lambda x, y: .25*abs(x)+.125*x, .73, (1, 1), (2., 2.), (0., 0.))
    assert not pools.internal_faces
    s = WetPoolPressureSystem(pools, .1)
    transport = SourceAuxiliaryTransport(s, np.array([[[.4, -.2]]]))
    assert transport.same_region_geometry_faces > 0
    assert any(face['left'] == face['right'] for face in transport.faces)


def test_coupled_stage_preserves_original_oblique_linear_wave_response():
    from finite_depth_pressure_reference import response
    n, dx, h, eps = 4, .4, 1.3, 1e-5
    pools = lake(lambda x, y: 0*x, h, (n, n), (dx, dx), (-.6, -.6), (True, True))
    y, x = np.indices((n, n))
    wave, mode = np.sin(2*np.pi*(x+y)/n), np.cos(2*np.pi*(x+y)/n)
    k = np.sin(2*np.pi*np.array([1, 1])/n)/dx
    depth_response, mass_response = [], []
    for sign in (-1, 1):
        volume = (dx**2*(h+sign*eps*wave)).ravel()
        probe = pools.volume_probe(volume)
        depth_response.append(stage(probe, np.zeros((n*n, 1, 2)))['physical_momentum_rate'].reshape(n, n, 2)/dx**2)
        momentum = (dx**2*h*sign*eps*wave[..., None]*k/np.linalg.norm(k)).reshape(n*n, 1, 2)
        mass_response.append(stage(pools, momentum)['volume_rate'].reshape(n, n)/dx**2)
    measured = np.sum((depth_response[1]-depth_response[0])/(2*eps)*mode[..., None], axis=(0, 1))/np.sum(mode*mode)
    np.testing.assert_allclose(measured, -9.81*h*k*response(h*np.linalg.norm(k)), atol=1e-7, rtol=0)
    measured_mass = np.sum((mass_response[1]-mass_response[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(measured_mass+h*np.linalg.norm(k)) < 1e-7


def test_source_nonlinear_rate_refines_toward_independent_turning_flow_bracket():
    from audit_subcell_nonlinear_metric_stage import compare
    coarse, fine = compare(2843, 8), compare(2843, 16)
    assert coarse['full_vs_continuum_rms']/fine['full_vs_continuum_rms'] > 3
    for row in (coarse, fine):
        assert row['canonical_vorticity_rms'] > .1
        assert row['maximum_roundtrip_error'] < 1e-10
        assert abs(row['energy_rate']) < 1e-10
        # The incomplete control also conserves energy: this test does not
        # pretend that coarse-grid energy or error alone proves the full model.
        assert abs(row['omitted_curvature_energy_rate']) < 1e-10
        assert not row['full_continuum_or_topology_or_time_or_native_or_gameplay_accepted']
