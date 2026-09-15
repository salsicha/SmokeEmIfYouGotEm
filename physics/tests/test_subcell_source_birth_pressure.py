from fractions import Fraction as F
import numpy as np
import pytest

from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_source_activation import assembly
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_pressure import WetPoolPressureSystem
from test_triangle_face_section import sampler


def fixture(velocity=(.8, .25), flat=False):
    source = sampler((lambda x, y: x*0) if flat else (lambda x, y: x+2*y))
    patch = SubcellGeometryPatch(source, [-.25, .25], (1, 2), [.5, .5], relative_stages=True, exact_sources=True)
    v, p = patch.state_from_stages([[1.17, -5.]], velocity)
    part = WetPoolPartition(patch, source, [-.25, .25], v, p)
    receipt = assembly(part)['new_region_rates'][0]
    return part, receipt['parent'], receipt['source_triangle_indices'][0]


def positive_probe(part, parent, source, height, velocity=(0., 0.)):
    birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source]))
    volume = float(birth.moments(F(height))[1])
    return part.with_regions(list(part.pools)+[dict(parent=parent, source_triangle_indices=[source],
        volume=volume, momentum=volume*np.asarray(velocity))])


@pytest.mark.parametrize('newborn_velocity', [(0., 0.), (.37, -.21)])
def test_original_positive_pressure_energy_converges_to_analytic_point_birth_slope(newborn_velocity):
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    limit = context.point_limit(parent, source)
    slope = limit['fixed_old_state_energy_height_slope']
    assert slope < -1e-5 and limit['immediately_connected_old_faces'] > 0
    errors = []
    for height in (1e-3, 5e-4, 2.5e-4):
        candidate = positive_probe(part, parent, source, height, newborn_velocity)
        p = np.array([pool['momentum'] for pool in candidate.pools])[:, None, :]
        metric = evaluate(candidate, p)
        assert max(p['relative_residual'] for p in metric['poles']) < 2e-5
        # Finite positive-water energy, independent of the asymptotic Schur
        # calculation. This is an injected-volume probe, NOT a time update.
        observed = (metric['kinetic']-context.primal['kinetic'])/height
        errors.append(abs(observed-slope))
    assert errors[-1] < errors[0]/3
    assert errors[-1] < .01*abs(slope)
    assert limit['fixed_old_state_energy_volume_derivative_is_singular']
    assert not limit['full_metric_front_force_or_time_or_gameplay_accepted']


def test_newborn_principal_pressure_block_and_old_cross_column_match_full_operator():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    limit = context.point_limit(parent, source)
    height = 1e-5
    candidate = positive_probe(part, parent, source, height)
    for pole, _ in context.poles:
        system = WetPoolPressureSystem(candidate, pole['beta'])
        actual = np.zeros((2, 2))
        cross = np.zeros(2)
        z = pole['normalized_auxiliary_velocity']
        for axis in range(2):
            basis = np.zeros((len(candidate.pools), 1, 2));basis[-1, 0, axis] = 1.
            qcolumn = system.factor_transpose(system.factor_action(basis))
            actual[:, axis] = qcolumn[-1, 0]
            cross[axis] = np.sum(z*qcolumn[:-1])/np.sqrt(height)
        np.testing.assert_allclose(actual, limit['leading_newborn_normalized_gram'], atol=2e-3, rtol=2e-3)
        # Independent old stress contraction through the original Q operator.
        old = WetPoolPressureSystem(part, pole['beta'])
        w = z[:, 0]/old.root[:, None]
        jet = np.column_stack((old.divergence(w), w))
        stress = np.array([pool['form']['gram'][0]@v for pool, v in zip(part.pools, jet)])
        expected = limit['old_divergence_column_sqrt_height_coefficient'].T@stress
        np.testing.assert_allclose(cross, expected, atol=2e-4, rtol=2e-4)


def test_zero_old_momentum_has_no_leading_pressure_birth_work():
    part, parent, source = fixture((0., 0.))
    result = SourceBirthPressure(part).point_limit(parent, source)
    assert result['fixed_old_state_energy_height_slope'] == 0
    for pole in result['poles']:
        np.testing.assert_array_equal(pole['auxiliary_velocity_height_product_limit'], 0.)


def test_stale_owned_and_different_birth_cones_reject():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    with pytest.raises(ValueError, match='unowned'):
        context.point_limit(part.pools[0]['parent'], part.pools[0]['source_triangle_indices'][0])
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        context.point_limit(parent, source)
    part, parent, source = fixture(flat=True)
    with pytest.raises(ValueError, match='edge/flat'):
        SourceBirthPressure(part).point_limit(parent, source)
