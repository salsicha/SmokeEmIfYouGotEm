import numpy as np
import pytest

from test_subcell_wet_pool_pressure import partition
from test_subcell_wet_pool_pressure_rate import fixture
from subcell_wet_pool_transport import rates
from subcell_energy_flux import rates as cell_rates
from subcell_wet_pool_primal_energy import evaluate


@pytest.mark.parametrize('kind', ['flat', 'slope', 'split'])
@pytest.mark.parametrize('dissipative', [False, True])
def test_complete_pool_base_flux_closes_energy_mass_and_boundary_bed_momentum(kind, dissipative):
    pools = fixture(kind)
    volumes = np.array([p['volume'] for p in pools.pools])
    momentum = volumes[:, None]*np.random.default_rng(2610).normal(size=(len(volumes), 2))
    r = rates(pools, momentum, dissipative=dissipative)
    assert r['complete_fixed_topology_base_rates']
    assert abs(r['net_mass_rate']) < 1e-12
    assert r['momentum_boundary_bed_error'] < 1e-12
    assert r['maximum_hydrostatic_geometry_closure_error'] < 1e-12
    assert r['base_energy_identity_error'] < 1e-11
    assert r['expected_base_energy_rate'] <= 0
    assert not r['nonlinear_two_pole_or_wetting_or_time_or_gameplay_accepted']
    # Do not reset momentum to an energy-conserving projection. The independently
    # evaluated full physical metric exposes missing rational transport work.
    energy = evaluate(pools, momentum[:, None])
    expected = energy['volume_gradient']@r['volume_rate']+np.sum(energy['canonical_velocity'][:, 0]*r['momentum_rate'])
    np.testing.assert_allclose(r['full_metric_energy_rate'], expected, atol=1e-12)


@pytest.mark.parametrize('kind', ['slope', 'split'])
def test_exact_pool_lake_at_rest_balances_independently_integrated_bed(kind):
    pools = fixture(kind)
    r = rates(pools, np.zeros((len(pools.pools), 2)))
    assert r['complete_fixed_topology_base_rates']
    np.testing.assert_allclose(r['volume_rate'], 0., atol=1e-13)
    np.testing.assert_allclose(r['momentum_rate'], 0., atol=1e-12)
    assert r['full_metric_energy_rate'] == 0.


def test_one_pool_cells_reduce_to_original_exact_cell_base_flux():
    pools = fixture('slope')
    original = cell_rates(pools.patch, pools.reassembled_volumes, pools.reassembled_momenta)
    r = rates(pools)
    np.testing.assert_allclose(r['volume_rate'], original['volume_rate'].ravel(), atol=1e-12)
    np.testing.assert_allclose(r['momentum_rate'], original['momentum_rate'].reshape(-1, 2), atol=1e-12)


def test_wet_face_into_unowned_dry_source_is_reported_not_blocked_or_dropped():
    pools, _, _, _ = partition(lambda x, y: 0*x, [[.8, 0.]], (1, 2), (.5, .5), (-.25, 0.))
    r = rates(pools)
    assert not r['complete_fixed_topology_base_rates']
    assert r['volume_rate'] is None and r['momentum_rate'] is None
    assert r['unresolved_activation_faces']
    assert all(face['dry_parent'] == 1 and face['wet_column_area'] > 0 for face in r['unresolved_activation_faces'])
    np.testing.assert_allclose(sum(face['wet_column_area'] for face in r['unresolved_activation_faces']), .4, atol=1e-13)


def test_dry_face_on_ridge_is_not_an_activation_request_or_pressure_bridge():
    pools, _, _, _ = partition(lambda x, y: 1-abs(x), .37)
    momentum = np.zeros((2, 2)); momentum[0] = [.1, 0.]
    r = rates(pools, momentum)
    assert r['complete_fixed_topology_base_rates']
    assert not r['unresolved_activation_faces']
    np.testing.assert_allclose(r['momentum_rate'][1], 0., atol=1e-12)


def test_mass_crosses_a_dry_face_when_its_source_triangle_already_has_a_wet_owner():
    pools, _, _, _ = partition(lambda x, y: -.4*x+.2*y, [[.217, -.053]], (1, 2), (1., 1.), (-.5, 0.))
    r = rates(pools)
    assert r['complete_fixed_topology_base_rates']
    assert r['owned_wet_dry_face_segments'] > 0
    assert r['volume_rate'][1] > 0
    assert r['base_energy_identity_error'] < 1e-11
    assert r['maximum_hydrostatic_geometry_closure_error'] < 1e-12


def test_base_transport_does_not_claim_full_metric_energy_conservation():
    pools = fixture('slope')
    p = np.array([pool['volume'] for pool in pools.pools])[:, None]*np.array([[.3, -.7], [1.2, .4], [-.8, 1.1], [.6, -.2]])
    r = rates(pools, p)
    assert r['base_energy_identity_error'] < 1e-11
    assert abs(r['full_metric_energy_rate']) > 1e-5
