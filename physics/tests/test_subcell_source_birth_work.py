from fractions import Fraction as F
import numpy as np
import pytest

from subcell_source_birth_pressure import SourceBirthPressure
from subcell_source_birth_work import point_work, harmonic_coefficient_partials
from subcell_simultaneous_birth_pressure import point_limits, harmonic_height_coefficient
from subcell_source_face_section import SourceFaceSection
from subcell_wet_pool_primal_energy import evaluate
from test_subcell_source_birth_pressure import fixture
from test_subcell_simultaneous_birth_pressure import requests_for, positive_probes


@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7), (1e-5, 2.), (2., 1e-5)])
def test_harmonic_partials_match_independent_integrated_stage_derivative(scales):
    section = SourceFaceSection([[(F(0), F(3)), (F(7), F(5))]])
    actual = harmonic_coefficient_partials(section, F(3), *scales)
    nodes, weights = np.polynomial.legendre.leggauss(256)
    low = min(scales)
    z = low*(nodes+1)/2
    left, right = scales[0]-z, scales[1]-z
    expected = np.array([weights@(2*right**2/(left+right)**2), weights@(2*left**2/(left+right)**2)])*low/2*3.5
    np.testing.assert_allclose(actual, expected, rtol=2e-10, atol=1e-14)
    np.testing.assert_allclose(np.dot(scales, actual), 2*harmonic_height_coefficient(section, F(3), *scales), rtol=1e-13)


@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7)])
def test_scale_gradient_matches_independent_energy_limit_differences(scales):
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part, scales)
    work = point_work(context, requests)
    for i in range(2):
        values = []
        step = 1e-5
        for sign in (-1, 1):
            shifted = [(p, s, k+sign*step*(j == i)) for j, (p, s, k) in enumerate(requests)]
            values.append(point_limits(context, shifted)['fixed_old_state_energy_path_slope'])
        # Test oracle only: no finite differences in the work implementation.
        np.testing.assert_allclose((values[1]-values[0])/(2*step), work['energy_stage_scale_gradient'][i], rtol=3e-7, atol=1e-9)
    assert work['homogeneity_error'] < 1e-12
    np.testing.assert_allclose(work['fixed_old_bounded_velocity_mass_direction_work_coefficient'],
                               work['limit']['fixed_old_state_energy_path_slope']/3, rtol=1e-12)


@pytest.mark.parametrize('velocity', [(0., 0.), (.27, -.13)])
@pytest.mark.parametrize('scales', [(1., 1.), (.7, 1.6), (1.6, .7)])
def test_singular_work_and_canonical_velocity_match_original_positive_water(velocity, scales):
    part, _, _ = fixture()
    work = point_work(SourceBirthPressure(part), requests_for(part, scales))
    target_g, target_c = work['volume_gradient_path_squared_limit'], work['canonical_velocity_path_limit']
    errors = []
    for parameter in (1e-3, 5e-4, 2.5e-4):
        candidate = positive_probes(part, requests_for(part, scales), parameter, velocity)
        metric = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
        gradient = parameter**2*metric['volume_gradient'][1:]
        canonical = parameter*metric['canonical_velocity'][1:, 0]
        errors.append((np.max(abs(gradient-target_g)), np.max(abs(canonical-target_c))))
        assert max(p['relative_residual'] for p in metric['poles']) < 2e-5
        assert metric['positive_energy_contraction_error'] < 1e-10
    assert all(last < first/3 for last, first in zip(errors[-1], errors[0]))
    np.testing.assert_allclose(gradient, target_g, rtol=.01, atol=1e-6)
    np.testing.assert_allclose(canonical, target_c, rtol=.01, atol=1e-6)
    assert work['bounded_physical_momentum_rates_cannot_cancel_leading_work']
    assert not work['full_metric_front_force_or_time_or_gameplay_accepted']


def test_zero_original_momentum_has_no_singular_pressure_work():
    part, _, _ = fixture((0., 0.))
    result = point_work(SourceBirthPressure(part), requests_for(part))
    np.testing.assert_array_equal(result['volume_gradient_path_squared_limit'], 0.)
    np.testing.assert_array_equal(result['canonical_velocity_path_limit'], 0.)
    assert not result['bounded_physical_momentum_rates_cannot_cancel_leading_work']


def test_single_source_work_and_exact_birth_power_are_consistent():
    part, parent, source = fixture()
    context = SourceBirthPressure(part)
    result = point_work(context, [(parent, source, 2.3)])
    old = context.point_limit(parent, source)
    np.testing.assert_allclose(result['energy_stage_scale_gradient'], [old['fixed_old_state_energy_height_slope']], rtol=1e-13)
    np.testing.assert_allclose(result['volume_gradient_path_squared_limit'],
        [old['fixed_old_state_energy_height_slope']/(3*old['volume_leading_coefficient']*2.3**2)], rtol=1e-13)
    assert result['energy_rate_time_power'] == -2/3


def test_work_does_not_repair_owned_stale_or_nonpoint_inputs():
    part, _, _ = fixture()
    context = SourceBirthPressure(part)
    requests = requests_for(part)
    with pytest.raises(ValueError, match='unowned'):
        point_work(context, [(part.pools[0]['parent'], int(part.pools[0]['source_triangle_indices'][0]), 1.)])
    part.pools[0]['momentum'][0] += .1
    with pytest.raises(ValueError, match='unchanged original'):
        point_work(context, requests)
    part, parent, source = fixture(flat=True)
    with pytest.raises(ValueError, match='edge/flat'):
        point_work(SourceBirthPressure(part), [(parent, source, 1.)])


def test_original_balanced_base_direction_still_has_singular_full_energy_work():
    from audit_south_fork_simultaneous_birth import analyze
    from subcell_source_activation import assembly
    part, _, _ = fixture()
    original = assembly(part, face_scheme='donor')
    result = analyze(part, original['new_region_rates'], original)
    assert result['bounded_original_base_direction']['mass_rate_error'] < 1e-10
    assert result['bounded_original_base_direction']['boundary_bed_momentum_rate_error'] < 1e-10
    path = result['paths'][1]
    expected = path['limit']['fixed_old_state_energy_path_slope']/3
    assert expected < 0 and path['pressure_work_probe_controls_passed']
    np.testing.assert_allclose(path['rows'][-1]['bounded_original_direction_scaled_work'], expected, rtol=.01)
    assert not result['full_metric_front_force_or_time_or_gameplay_accepted']
    with pytest.raises(ValueError, match='Matching original assembled'):
        analyze(part, list(original['new_region_rates']), original)
    original['momentum_rate'] = original['momentum_rate']+1.
    with pytest.raises(ValueError, match='boundary-momentum'):
        analyze(part, original['new_region_rates'], original)
