from fractions import Fraction as F

import numpy as np
import pytest

from test_triangle_face_section import sampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from subcell_source_activation import assembly, attempt
from subcell_source_face_section import SourceFaceSection, stage_difference
from subcell_source_frames import physical_datum
from finite_depth_pressure_reference import LENGTHS
from subcell_energy_flux import rates as aggregate_rates
from subcell_mechanical_energy import energy as aggregate_energy
from subcell_source_activation import base_energy
from subcell_implicit_transport import frozen_system


def exact_partition(terrain, stages, shape=(1, 1), spacing=(2., 2.), origin=(0., 0.)):
    source = sampler(terrain)
    patch = SubcellGeometryPatch(source, origin, shape, spacing, relative_stages=True, exact_sources=True)
    volume, momentum = patch.state_from_stages(stages, [.4, -.2])
    return WetPoolPartition(patch, source, origin, volume, momentum), volume, momentum


def test_exact_storage_and_datums_survive_separated_pool_construction():
    pools, volume, momentum = exact_partition(lambda x, y: 221-abs(x), 220.37)
    assert len(pools.pools) == 2
    for pool in pools.pools:
        assert pool['storage'].source_datum == pool['form']['datum']
        assert isinstance(pool['form']['datum'], F)
        assert pool['storage'].datum == 0.
        assert pool['topology_absolute_stage_interval'][0] > 200
    np.testing.assert_allclose(pools.reassembled_volumes, volume, atol=1e-14, rtol=0)
    np.testing.assert_allclose(pools.reassembled_momenta, momentum, atol=1e-14, rtol=0)
    assert pools.maximum_gram_partition_error < 1e-12
    assert pools.maximum_volume_tangent_partition_error < 1e-12
    assert all(isinstance(s, SourceFaceSection) for axis in (0, 1) for sign in (-1, 1)
               for _, s in pools.boundary_segments(0, axis, sign))


@pytest.mark.parametrize('length', LENGTHS)
def test_original_pressure_poles_on_exact_pool_traces_match_dense_operator(length):
    pools, _, _ = exact_partition(lambda x, y: 220.+.2*x-.3*y, 221.17,
                                  shape=(1, 2), spacing=(.5, .5), origin=(-.5, 0.))
    system = WetPoolPressureSystem(pools, float(length))
    n = 2*len(pools.pools)
    dense = np.column_stack([system.apply(np.eye(n)[:, i].reshape(-1, 1, 2)).ravel() for i in range(n)])
    rhs = np.arange(1., n+1).reshape(-1, 1, 2)
    actual, stats = system.solve(rhs)
    np.testing.assert_allclose(actual.ravel(), np.linalg.solve(dense, rhs.ravel()), atol=1e-12, rtol=1e-12)
    assert stats['iterations'] <= 40
    assert stats['relative_residual'] < 2e-5
    assert system.maximum_shared_column_partition_error < 1e-10
    assert system.maximum_wall_column_partition_error < 1e-10
    result = evaluate(pools, np.array([p['momentum'] for p in pools.pools])[:, None, :])
    assert result['positive_energy_contraction_error'] < 1e-10
    assert not result['mass_or_nonlinear_bed_force_or_time_or_gameplay_accepted']


def test_exact_region_subsets_internal_edges_and_volume_probe_keep_source_frames():
    pools, _, _ = exact_partition(lambda x, y: 220.+.2*x-.3*y, 221.17,
                                  spacing=(1., 1.), origin=(.1, -.1))
    old = pools.pools[0]
    states = []
    for source in old['source_triangle_indices']:
        storage = old['storage'].subset_sources([source])
        height = stage_difference(0., physical_datum(storage), old['form']['stage_offset'], old['form']['datum'])
        volume = storage.relative_volume_and_wet_area(height)[0]
        states.append(dict(parent=0, source_triangle_indices=[source], volume=volume,
                           momentum=volume*old['momentum']/old['volume']))
    divided = pools.with_regions(states)
    assert len(divided.pools) == len(states)
    assert divided.internal_faces
    assert all(isinstance(face['segment'], SourceFaceSection) for face in divided.internal_faces)
    np.testing.assert_allclose(sum(p['volume'] for p in divided.pools), old['volume'], atol=1e-14)
    changed = divided.volume_probe(np.array([p['volume'] for p in divided.pools])*(1+1e-7))
    assert all(isinstance(p['form']['datum'], F) for p in changed.pools)
    assert all(hasattr(p['storage'], 'fragments') for p in changed.pools)


def test_source_activation_and_returned_state_keep_exact_storage_and_faces():
    pools, _, _ = exact_partition(lambda x, y: 0*x+220., [[221., 220.]],
                                  shape=(1, 2), spacing=(.5, .5), origin=(-.5, 0.))
    source = assembly(pools, face_scheme='donor')
    assert source['fronts']
    assert source['source_face_below_storage_minimum']['count'] == 0
    result = attempt(pools, .001, scheme='coupled-donor')
    assert result['audit']['candidate_accepted'], result['audit']
    assert not result['audit']['full_rational_model_or_time_history_or_gameplay_accepted']
    state = result['state']
    assert any(p['parent'] == 1 for p in state.pools)
    assert all(hasattr(p['storage'], 'fragments') for p in state.pools)
    assert all(isinstance(p['form']['datum'], F) for p in state.pools)
    assert assembly(state, face_scheme='donor')['source_face_below_storage_minimum']['count'] == 0


def test_aggregate_energy_uses_the_same_exact_source_reference_as_pool_energy():
    pools, volume, momentum = exact_partition(lambda x, y: 220.+x+2*y, 221.17,
                                              shape=(1, 2), spacing=(.5, .5), origin=(-.5, 0.))
    expected = base_energy(pools)
    actual = aggregate_energy(pools.patch, volume, momentum)
    for key in ('kinetic', 'potential', 'total'):
        np.testing.assert_allclose(actual[key], expected[key], atol=1e-12, rtol=1e-12)


def test_aggregate_rate_apis_cannot_bypass_exact_pool_geometry():
    pools, volume, momentum = exact_partition(lambda x, y: 220.+x+2*y, 221.17,
                                              shape=(1, 2), spacing=(.5, .5), origin=(-.5, 0.))
    with pytest.raises(ValueError, match='pool-aware'):
        pools.patch.rates(volume, momentum)
    with pytest.raises(ValueError, match='pool-aware'):
        aggregate_rates(pools.patch, volume, momentum)
    with pytest.raises(ValueError, match='pool-aware'):
        frozen_system(pools.patch, volume, momentum)
