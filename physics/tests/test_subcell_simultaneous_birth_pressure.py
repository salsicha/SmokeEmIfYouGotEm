from fractions import Fraction as F
import numpy as np
import pytest

from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_simultaneous_birth_pressure import point_limits, birth_faces, BirthLimitSystem
from subcell_source_region_faces import internal_faces
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from test_subcell_source_birth_pressure import fixture
from test_triangle_face_section import sampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition


def requests_for(part, scales=(1., 1.)):
    ids = sorted(map(int, part.patch.cells[1].source_triangle_indices))
    assert len(ids) == len(scales)
    return [(1, s, k) for s, k in zip(ids, scales)]


def positive_probes(part, requests, path, velocity=(.27, -.13)):
    regions = list(part.pools)
    for parent, source, scale in requests:
        birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source]))
        volume = float(birth.moments(F(float(path))*F(float(scale)))[1])
        regions.append(dict(parent=parent, source_triangle_indices=[source], volume=volume,
                            momentum=volume*np.asarray(velocity)))
    return part.with_regions(regions)


def test_geometry_only_labels_expose_original_dry_dry_edge_without_mutation():
    part, _, _ = fixture()
    keys = [(p, s) for p, s, _ in requests_for(part)]
    assert not [f for f in internal_faces(part) if f['parent'] == 1]
    exposed = [f for f in birth_faces(part, keys) if f['internal'] and f['parent'] == 1]
    assert len(exposed) == 1
    assert {exposed[0]['left_source'], exposed[0]['right_source']} == {s for _, s in keys}
    assert len(part.pools) == 1 and not part.parent_pools[1]
    assert not [f for f in internal_faces(part) if f['parent'] == 1]
    with pytest.raises(ValueError, match='replace an existing'):
        internal_faces(part, {(0, int(part.pools[0]['source_triangle_indices'][0])): 1})
    with pytest.raises(ValueError, match='Explicit unowned'):
        internal_faces(part, {(1, 100000): 1})


@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7)])
def test_coupled_limit_matches_original_full_operator_and_positive_energy(scales):
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part, scales)
    result = point_limits(context, requests)
    assert len(result['immediate_newborn_connections']) == 1
    assert abs(result['fixed_old_state_energy_path_slope']-result['independent_single_source_sum']) > 1e-5
    assert not result['full_metric_front_force_or_time_or_gameplay_accepted']
    errors = []
    for path in (1e-3, 5e-4, 2.5e-4):
        candidate = positive_probes(part, requests, path)
        metric = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
        observed = (metric['kinetic']-context.primal['kinetic'])/path
        errors.append(abs(observed-result['fixed_old_state_energy_path_slope']))
        assert max(p['relative_residual'] for p in metric['poles']) < 2e-5
        assert metric['positive_energy_contraction_error'] < 1e-10
    assert errors[-1] < errors[0]/3
    assert errors[-1] < .01*abs(result['fixed_old_state_energy_path_slope'])
    candidate = positive_probes(part, requests, 1e-6)
    for pole, stress in context.poles:
        system = WetPoolPressureSystem(candidate, pole['beta'])
        limit_system = BirthLimitSystem(result['newborn_jet_maps'], result['newborn_scaled_factors'],
                                        result['volume_path_coefficients'], pole['beta'])
        actual, expected, cross = np.zeros((4, 4)), np.zeros((4, 4)), np.zeros(4)
        for j in range(4):
            basis = np.zeros((3, 1, 2)); basis[1+j//2, 0, j%2] = 1.
            column = system.factor_transpose(system.factor_action(basis))
            actual[:, j] = column[1:].ravel()
            expected[:, j] = limit_system.q_action(basis[1:]).ravel()
            cross[j] = np.sum(column[:1]*pole['normalized_auxiliary_velocity'])/1e-3
        np.testing.assert_allclose(actual, expected, rtol=3e-4, atol=3e-4)
        np.testing.assert_allclose(cross, result['old_divergence_column_sqrt_path_coefficient'].T@stress,
                                   rtol=3e-4, atol=3e-4)
        # Small dense test oracle only, never the coupled solver implementation.
        rhs = result['old_divergence_column_sqrt_path_coefficient'].T@stress
        direct = np.linalg.solve(np.eye(4)+pole['beta']*expected, rhs)
        record = next(p for p in result['poles'] if p['beta'] == pole['beta'])
        np.testing.assert_allclose(record['energy_path_slope'], -.5*pole['alpha']*pole['beta']*(rhs@direct), rtol=1e-12)
        assert record['iterations'] <= 40 and record['relative_residual'] < 2e-5


def test_single_birth_agrees_and_stage_reparameterization_is_linear():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    original = context.point_limit(parent, source)
    result = point_limits(context, [(parent, source, 2.3)])
    np.testing.assert_allclose(result['fixed_old_state_energy_path_slope'],
                               2.3*original['fixed_old_state_energy_height_slope'], rtol=1e-13)
    requests = requests_for(part, (.7, 1.6))
    first = point_limits(context, requests)
    second = point_limits(context, [(p, s, 3*k) for p, s, k in requests])
    np.testing.assert_allclose(second['fixed_old_state_energy_path_slope'], 3*first['fixed_old_state_energy_path_slope'], rtol=1e-13)


@pytest.mark.parametrize('scales', [(0., 1.), (-1., 1.), (float('nan'), 1.), (1., float('inf'))])
def test_invalid_path_scales_reject(scales):
    part, _, _ = fixture()
    with pytest.raises(ValueError, match='strictly positive'):
        point_limits(SourceBirthPressure(part), requests_for(part, scales))


def test_duplicate_empty_and_stale_states_reject():
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part)
    with pytest.raises(ValueError, match='Duplicate'):
        point_limits(context, requests*2)
    with pytest.raises(ValueError, match='At least one'):
        point_limits(context, [])
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        point_limits(context, requests)


@pytest.mark.parametrize('equal_minima', [True, False])
def test_original_cartesian_birth_connection_requires_equal_exact_minima(equal_minima):
    source = sampler((lambda x, y: (x-.5)**2+2*y) if equal_minima else (lambda x, y: x+2*y))
    patch = SubcellGeometryPatch(source, [-.25, .25], (1, 3), [.5, .5], relative_stages=True, exact_sources=True)
    volume, momentum = patch.state_from_stages([[2.17, -5., -5.]], (.8, .25))
    part = WetPoolPartition(patch, source, [-.25, .25], volume, momentum)
    # The right-hand triangle in parent 1 meets the left-hand triangle in 2
    # at a Cartesian face. No same-cell edge is used by this test.
    requests = [(1, max(map(int, patch.cells[1].source_triangle_indices)), .7),
                (2, min(map(int, patch.cells[2].source_triangle_indices)), 1.3)]
    context = SourceBirthPressure(part)
    result = point_limits(context, requests)
    connections = result['immediate_newborn_connections']
    assert len(connections) == int(equal_minima)
    assert all(not c['internal'] for c in connections)
    candidate = positive_probes(part, requests, 1e-6)
    for pole, _ in context.poles:
        system = WetPoolPressureSystem(candidate, pole['beta'])
        limit_system = BirthLimitSystem(result['newborn_jet_maps'], result['newborn_scaled_factors'],
                                        result['volume_path_coefficients'], pole['beta'])
        for j in range(4):
            basis = np.zeros((3, 1, 2)); basis[1+j//2, 0, j%2] = 1.
            original = system.factor_transpose(system.factor_action(basis))[1:]
            np.testing.assert_allclose(original, limit_system.q_action(basis[1:]), atol=3e-4, rtol=3e-4)


def test_audit_preserves_original_state_and_rejects_invalid_receipts():
    from audit_south_fork_simultaneous_birth import analyze
    part, parent, source = fixture()
    with pytest.raises(ValueError, match='Positive original'):
        analyze(part, [])
    with pytest.raises(ValueError, match='Positive original'):
        analyze(part, [dict(parent=parent, source_triangle_indices=[source], volume_rate=-1.)])
    receipts = [dict(parent=p, source_triangle_indices=[s], volume_rate=.3+i*.2)
                for i, (p, s, _) in enumerate(requests_for(part))]
    result = analyze(part, receipts)
    assert result['original_water_unchanged'] and result['pressure_limit_probe_controls_passed']
    assert not result['full_metric_front_force_or_time_or_gameplay_accepted']
