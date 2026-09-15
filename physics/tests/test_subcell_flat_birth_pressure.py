"""Flat wetting: independent finite-water energy, work and full-Q checks."""
import numpy as np
import pytest
from fractions import Fraction as F

from rational_primal_energy import K0
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_source_activation import assembly
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_flat_birth_pressure import flat_limit
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from test_triangle_face_section import sampler
from test_subcell_source_birth_pressure import positive_probe, fixture as point_fixture
from test_subcell_edge_birth_pressure import fixture as edge_fixture


def fixture(axis=0, reverse=False, velocity=(.8, .25), datum=0., sloped_old=False):
    source = sampler(lambda x, y: datum+(.5*np.minimum((-1 if reverse else 1)*(x if axis == 0 else y), 0.)
                                        if sloped_old else 0*x))
    origin, shape = ([-.25, .25], (1, 3)) if axis == 0 else ([.25, -.25], (3, 1))
    patch = SubcellGeometryPatch(source, origin, shape, [.5, .5], relative_stages=True, exact_sources=True)
    stages = [-5., .73, 1.17] if reverse else [1.17, .73, -5.]
    # state_from_stages accepts absolute elevations. Construct original
    # datum-relative storage directly so this large-datum fixture does not
    # round its shallow offsets by first adding them to the absolute datum.
    v = np.array([cell.relative_volume_and_wet_area(float(F(datum)+F(stage)-cell.source_datum))[0]
                  for cell, stage in zip(patch.cells, stages)]).reshape(shape)
    p = v[..., None]*np.asarray(velocity)
    # Excite pressure in the old pool adjoining the new source; a uniform
    # old velocity can leave that row's stress zero and hide a missing term.
    p.reshape(-1, 2)[1] *= 1.3
    part = WetPoolPartition(patch, source, origin, v, p)
    receipt = assembly(part)['new_region_rates'][0]
    return part, receipt['parent'], receipt['source_triangle_indices'][0]


def internal_fixture():
    source = sampler(lambda x, y: 0*x)
    origin = [-.25, .25]
    patch = SubcellGeometryPatch(source, origin, (1, 1), [.5, .5], relative_stages=True, exact_sources=True)
    v, p = patch.state_from_stages([[.73]], (.8, .25))
    part = WetPoolPartition(patch, source, origin, v, p)
    first, second = part.pools[0]['source_triangle_indices']
    birth = SourceBirthGeometry(patch.cells[0].subset_sources([first]))
    volume = float(birth.moments(F(.73))[1])
    part = part.with_regions([dict(parent=0, source_triangle_indices=[first], volume=volume,
                                  momentum=volume*np.array([.8, .25]))])
    assert any(f['left_source'] == first and f['right_source'] == second
               or f['right_source'] == first and f['left_source'] == second for f in part.internal_faces)
    return part, 0, second


CASES = [lambda: fixture(0, False), lambda: fixture(0, True), lambda: fixture(1, False),
         lambda: fixture(1, True), internal_fixture,
         lambda: fixture(datum=2.**35, sloped_old=True),
         lambda: fixture(axis=1, reverse=True, sloped_old=True)]


@pytest.mark.parametrize('factory', CASES)
@pytest.mark.parametrize('velocity', [(0., 0.), (.37, -.21)])
def test_energy_canonical_velocity_and_fixed_p_volume_work_converge(factory, velocity):
    part, parent, source = factory()
    context = SourceBirthPressure(part)
    limit = flat_limit(context, parent, source, velocity)
    assert limit['immediately_connected_old_faces'] > 0
    assert max(abs(p['old_self_geometry_work']) for p in limit['poles']) > 1e-8
    assert max(np.linalg.norm(p['old_new_coupling']) for p in limit['poles']) > 1e-8
    errors = []
    for height in (1e-3, 2.5e-4, 6.25e-5):
        candidate = positive_probe(part, parent, source, height, velocity)
        result = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
        observed = (result['kinetic']-context.primal['kinetic'])/height
        gradient = result['volume_gradient'][-1]-result['volume_gradient_terms']['potential'][-1]
        errors.append([abs(observed-limit['fixed_old_state_energy_height_slope']),
            np.max(abs(result['canonical_velocity'][-1, 0]-limit['canonical_velocity_limit'])),
            abs(gradient-limit['kinetic_fixed_momentum_volume_gradient_limit']),
            max(np.max(abs(p['normalized_auxiliary_velocity'][-1, 0]/np.sqrt(candidate.pools[-1]['volume'])
                               -expected['auxiliary_velocity_limit']))
                for p, expected in zip(result['poles'], limit['poles']))])
        assert max(p['relative_residual'] for p in result['poles']) <= 2e-5
        assert result['positive_energy_contraction_error'] <= 1e-10
    errors = np.asarray(errors)
    assert np.all(errors[-1] < errors[0]/3), errors
    assert np.max(errors[-1]) < 1e-3, errors
    assert limit['chain_rule_work_identity_error'] <= 1e-10
    assert limit['fixed_old_bounded_new_velocity_energy_jump'] == 0.
    assert not limit['full_metric_front_force_or_time_or_gameplay_accepted']
    assert context.state_signature() == context.original_state


@pytest.mark.parametrize('factory', CASES)
def test_all_old_self_and_cross_operator_columns_have_the_derived_first_variation(factory):
    part, parent, source = factory()
    context = SourceBirthPressure(part)
    limit = flat_limit(context, parent, source)
    old = WetPoolPressureSystem(part, context.poles[0][0]['beta'])
    n = 2*len(part.pools)
    # Dense matrices are independent small TEST ORACLES only, never a solver.
    old_factors = [old.factor_action(e.reshape(-1, 1, 2)) for e in np.eye(n)]
    f = np.column_stack([np.concatenate(v) for v in old_factors])
    df = np.column_stack([np.concatenate([pool['form']['factor'][:, 0]*float(d@u)
        for pool, d, u in zip(part.pools, limit['old_self_divergence_height_derivative'],
                              e.reshape(-1, 2)/old.root[:, None])]) for e in np.eye(n)])
    columns = np.vstack([pool['form']['factor'][:, :1]*c[None, :]
                         for pool, c in zip(part.pools, limit['old_divergence_column_sqrt_height_coefficient'])])
    derivative, cross = f.T@df+df.T@f, f.T@columns
    assert np.linalg.norm(derivative) > .01  # Cannot omit the flat old-self term.
    errors = []
    for height in (1e-3, 2.5e-4, 6.25e-5):
        candidate = positive_probe(part, parent, source, height)
        finite = WetPoolPressureSystem(candidate, old.length)
        q = np.column_stack([finite.factor_transpose(finite.factor_action(e.reshape(-1, 1, 2))).ravel()
                             for e in np.eye(n+2)])
        errors.append([np.max(abs((q[:n, :n]-f.T@f)/height-derivative)),
                       np.max(abs(q[:n, n:]/np.sqrt(height)-cross)), np.max(abs(q[n:, n:]))])
    errors = np.asarray(errors)
    assert np.all(errors[-1] < errors[0]/3), errors
    assert np.max(errors[-1]) < 1e-2, errors


def test_zero_old_momentum_retains_newborn_base_energy_and_velocity():
    part, parent, source = fixture(velocity=(0., 0.))
    velocity = np.array([.37, -.21])
    result = flat_limit(SourceBirthPressure(part), parent, source, velocity)
    assert result['fixed_old_state_energy_height_slope'] == .5*K0*result['volume_leading_coefficient']*(velocity@velocity)
    np.testing.assert_array_equal(result['canonical_velocity_limit'], K0*velocity)
    assert result['kinetic_fixed_momentum_volume_gradient_limit'] == -.5*K0*(velocity@velocity)
    for pole in result['poles']:
        np.testing.assert_array_equal(pole['auxiliary_velocity_limit'], velocity)


def test_stale_owned_invalid_velocity_and_other_birth_cones_reject():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    with pytest.raises(ValueError, match='unowned'):
        flat_limit(context, part.pools[0]['parent'], part.pools[0]['source_triangle_indices'][0])
    with pytest.raises(ValueError, match='parent'):
        flat_limit(context, -1, source)
    with pytest.raises(ValueError, match='integer'):
        flat_limit(context, parent, float(source))
    for velocity in ([1.], [np.inf, 0.], [np.nan, 0.]):
        with pytest.raises(ValueError, match='bounded'):
            flat_limit(context, parent, source, velocity)
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        flat_limit(context, parent, source)
    for factory in (point_fixture, edge_fixture):
        part, parent, source = factory()
        with pytest.raises(ValueError, match='Linear original flat'):
            flat_limit(SourceBirthPressure(part), parent, source)
