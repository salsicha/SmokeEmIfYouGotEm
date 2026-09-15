"""Independent finite-water and full-operator checks of the edge limit."""
import numpy as np
import pytest

from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_source_activation import assembly
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_edge_birth_pressure import edge_factor, edge_limit, EdgeBirthSystem
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from test_triangle_face_section import sampler
from test_subcell_source_birth_pressure import positive_probe, fixture as point_fixture
from test_subcell_source_birth_geometry import storage


def fixture(axis=0, slope=1., velocity=(.8, .25)):
    source = sampler(lambda x, y: slope*(x if axis == 0 else y))
    origin, shape = ([-.25, .25], (1, 2)) if axis == 0 else ([.25, -.25], (2, 1))
    patch = SubcellGeometryPatch(source, origin, shape, [.5, .5], relative_stages=True, exact_sources=True)
    v, p = patch.state_from_stages(np.array([1.17, -5.]).reshape(shape), velocity)
    part = WetPoolPartition(patch, source, origin, v, p)
    receipts = assembly(part)['new_region_rates']
    for receipt in receipts:
        parent, source_id = receipt['parent'], receipt['source_triangle_indices'][0]
        if SourceBirthGeometry(patch.cells[parent].subset_sources([source_id])).volume_power == 2:
            return part, parent, source_id
    raise AssertionError('Fixture must expose an original minimum edge')


def systems(context, limit):
    for original, _ in context.poles:
        yield EdgeBirthSystem(WetPoolPressureSystem(context.partition, original['beta']),
                              limit['old_divergence_column_limit'], limit['newborn_factor'])


def test_edge_factor_matches_exact_original_gram_without_eigenvalue_repair():
    birth = SourceBirthGeometry(storage('edge', 220))
    factor = edge_factor(birth)
    np.testing.assert_allclose(factor.T@factor, np.asarray(birth.scaled_gram_limit, float), atol=2e-15, rtol=2e-15)
    for kind in ('flat', 'point'):
        with pytest.raises(ValueError, match='Quadratic'):
            edge_factor(SourceBirthGeometry(storage(kind)))


@pytest.mark.parametrize('axis,slope', [(0, .4), (0, 1.), (1, 1.)])
@pytest.mark.parametrize('new_velocity', [(0., 0.), (.37, -.21)])
def test_independent_positive_water_energy_converges_to_nonzero_jump(axis, slope, new_velocity):
    part, parent, source_id = fixture(axis, slope)
    context = SourceBirthPressure(part)
    limit = edge_limit(context, parent, source_id)
    expected = limit['fixed_old_bounded_new_velocity_energy_jump']
    assert expected < -1e-5
    errors = []
    for height in (1e-3, 2.5e-4, 6.25e-5):
        candidate = positive_probe(part, parent, source_id, height, new_velocity)
        result = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
        errors.append(abs(result['kinetic']-context.primal['kinetic']-expected))
        assert max(p['relative_residual'] for p in result['poles']) <= 2e-5
        assert result['positive_energy_contraction_error'] <= 1e-10
    assert errors[-1] < errors[0]/3
    assert errors[-1] < .01*abs(expected)
    assert limit['positive_energy_contraction_error'] <= 1e-10
    assert limit['schur_energy_jump_identity_error'] <= 1e-10
    assert not limit['full_metric_front_force_or_time_or_gameplay_accepted']
    assert context.state_signature() == context.original_state


@pytest.mark.parametrize('axis', [0, 1])
def test_every_original_operator_column_and_auxiliary_response_converges(axis):
    part, parent, source_id = fixture(axis)
    context = SourceBirthPressure(part)
    limit = edge_limit(context, parent, source_id)
    for boundary, pole in zip(systems(context, limit), limit['poles']):
        size = 2*len(boundary.h)
        expected = np.column_stack([boundary.q_action(e.reshape(-1, 1, 2)).ravel() for e in np.eye(size)])
        errors, response_errors = [], []
        for height in (1e-3, 2.5e-4, 6.25e-5):
            candidate = positive_probe(part, parent, source_id, height)
            finite = WetPoolPressureSystem(candidate, pole['beta'])
            actual = np.column_stack([finite.factor_transpose(finite.factor_action(e.reshape(-1, 1, 2))).ravel()
                                      for e in np.eye(size)])
            errors.append(np.max(abs(actual-expected)))
            p = np.array([p['momentum'] for p in candidate.pools])[:, None, :]
            q = p/finite.root[:, None, None]
            solution, stats = finite.solve(q)
            assert stats['relative_residual'] <= 2e-5
            response_errors.append(np.max(abs(solution-pole['normalized_auxiliary_limit'])))
        assert errors[-1] < errors[0]/3 and errors[-1] < 1e-3
        assert response_errors[-1] < response_errors[0]/3 and response_errors[-1] < 1e-3
        # The finite old-factor contribution to the newborn block must not be
        # discarded as it was in the vanishing point-birth cross-column case.
        old_diagonal = expected[-2:, -2:]-limit['newborn_factor'].T@limit['newborn_factor']
        assert np.linalg.norm(old_diagonal) > .01


def test_positive_factor_adjoint_full_old_response_and_original_40cg():
    part, parent, source_id = fixture()
    context = SourceBirthPressure(part)
    limit = edge_limit(context, parent, source_id)
    random = np.random.default_rng(9284)
    for system, pole in zip(systems(context, limit), limit['poles']):
        shape = (*system.h.shape, 2)
        x, y = random.normal(size=shape), random.normal(size=shape)
        fx, fy = system.factor_action(x), system.factor_action(y)
        np.testing.assert_allclose(np.sum(x*system.q_action(y)), sum(a@b for a, b in zip(fx, fy)), atol=1e-12, rtol=1e-12)
        assert np.sum(x*system.apply(x)) >= np.sum(x*x)
        matrix = np.column_stack([system.apply(e.reshape(shape)).ravel() for e in np.eye(x.size)])
        q = np.concatenate((np.array([p['momentum']/np.sqrt(p['volume']) for p in part.pools]), [[0., 0.]]))
        # Independent small dense solve is TEST ORACLE ONLY.
        expected = np.linalg.solve(matrix, q.ravel()).reshape(shape)
        np.testing.assert_allclose(pole['normalized_auxiliary_limit'], expected, atol=1e-12, rtol=1e-12)
        assert pole['iterations'] <= 40 and pole['relative_residual'] <= 2e-5
        with pytest.raises(ValueError, match='normalized'):
            system.apply(np.zeros((1, 2)))


def test_zero_old_momentum_has_zero_jump_and_auxiliary_limit():
    part, parent, source_id = fixture(velocity=(0., 0.))
    result = edge_limit(SourceBirthPressure(part), parent, source_id)
    assert result['fixed_old_bounded_new_velocity_energy_jump'] == 0
    for pole in result['poles']:
        np.testing.assert_array_equal(pole['normalized_auxiliary_limit'], 0.)


def test_stale_owned_wrong_cones_and_invalid_ids_reject():
    part, parent, source_id = fixture()
    context = SourceBirthPressure(part)
    with pytest.raises(ValueError, match='unowned'):
        edge_limit(context, part.pools[0]['parent'], part.pools[0]['source_triangle_indices'][0])
    with pytest.raises(ValueError, match='parent'):
        edge_limit(context, -1, source_id)
    with pytest.raises(ValueError, match='integer'):
        edge_limit(context, parent, float(source_id))
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        edge_limit(context, parent, source_id)
    for flat in (True, False):
        part, parent, source_id = point_fixture(flat=flat)
        with pytest.raises(ValueError, match='Quadratic'):
            edge_limit(SourceBirthPressure(part), parent, source_id)
