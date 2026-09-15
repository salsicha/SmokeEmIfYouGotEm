from fractions import Fraction as F
import numpy as np
import pytest

from subcell_point_birth_front_flux import point_front_flux
from subcell_dry_front_flux import flux as original_flux
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_frames import face_section
from subcell_simultaneous_birth_pressure import birth_faces
from test_subcell_source_birth_pressure import fixture


def face_fixture():
    part, parent, source = fixture()
    birth = SourceBirthGeometry(part.patch.cells[parent].subset_sources([source]))
    for face in birth_faces(part, [(parent, source)]):
        if face['left_parent'] == parent and face['left_source'] == source and face['right_parent'] >= 0:
            section = face_section(face['segment'])
            if birth.face_area_polynomial(section):
                return birth, section, face['normal']
        if face['right_parent'] == parent and face['right_source'] == source and face['left_parent'] >= 0:
            section = face_section(face['segment'])
            return birth, section, -face['normal']
    raise AssertionError('Original point face required')


@pytest.mark.parametrize('speed', [-2., -.03, 0., 1e-126, .03, 2.])
@pytest.mark.parametrize('height', [1e-6, .01, .2])
def test_piecewise_closed_flux_matches_original_wave_speed_quadrature(speed, height):
    birth, section, normal = face_fixture()
    tangent = np.array([-normal[1], normal[0]])
    velocity = speed*normal+.27*tangent
    expected, info = original_flux(section, height, birth.datum, velocity, normal)
    actual = point_front_flux(birth, section, height, velocity, normal)
    np.testing.assert_allclose(actual['flux'], expected, rtol=1e-11, atol=1e-14)
    np.testing.assert_allclose(actual['energy_flux'], info['energy_flux'], rtol=1e-11, atol=1e-14)
    np.testing.assert_allclose(actual['nonadvective_momentum_flux'], info['nonadvective_momentum_flux'], rtol=1e-11, atol=1e-14)
    for branch in ('dry', 'wet', 'fan'):
        np.testing.assert_allclose(actual['branch_projected_widths'][branch], info['branch_projected_widths'][branch], rtol=1e-11, atol=1e-14)
    assert not actual['complete_rational_front_or_time_or_native_or_gameplay_accepted']


@pytest.mark.parametrize('speed,power', [(1., 2.), (0., 2.5)])
def test_original_outward_and_zero_speed_powers_are_distinct(speed, power):
    birth, section, normal = face_fixture()
    for height in (1e-3, 1e-5):
        result = point_front_flux(birth, section, height, speed*normal, normal)
        assert result['mass_height_power'] == power
        np.testing.assert_allclose(result['flux'][0]/height**power, result['mass_height_coefficient'], rtol=1e-12)


def test_tiny_nonzero_speed_is_not_reclassified_or_forced_into_its_unrepresentable_wet_regime():
    birth, section, normal = face_fixture()
    result = point_front_flux(birth, section, 1e-6, 1e-126*normal, normal)
    assert result['asymptotic_branch'] == 'outward-wet'
    assert result['mass_height_coefficient'] > 0
    assert 0 < result['asymptotic_branch_height_bound'] < F(1, 10**250)
    assert result['branch_projected_widths']['fan'] > 0
    assert result['flux'][0] > 1e-126


def test_receding_front_switch_is_retained_without_minimum_water():
    birth, section, normal = face_fixture()
    velocity = -.03*normal
    bound = F(.03)**2/(4*F(9.81))
    low = point_front_flux(birth, section, float(bound/2), velocity, normal)
    high = point_front_flux(birth, section, float(bound*2), velocity, normal)
    np.testing.assert_array_equal(low['flux'], 0.)
    assert high['flux'][0] > 0
    assert low['asymptotic_branch'] == high['asymptotic_branch'] == 'receding-dry'


def test_zero_height_and_invalid_geometry_velocity_or_height():
    birth, section, normal = face_fixture()
    result = point_front_flux(birth, section, 0., normal, normal)
    np.testing.assert_array_equal(result['flux'], 0.)
    for height in (-1., float(birth.next_height)):
        with pytest.raises(ValueError):
            point_front_flux(birth, section, height, normal, normal)
    with pytest.raises(ValueError, match='unit outward'):
        point_front_flux(birth, section, .01, normal, normal*2)


def test_original_subdivided_face_knot_is_not_skipped():
    birth, section, normal = face_fixture()
    first, last = section.source_segments[0][0], section.source_segments[-1][1]
    mid = (first[0]+last[0])/2
    cut = section.restricted(first[0], mid) if first[1] < last[1] else section.restricted(mid, last[0])
    bound = birth.face_next_height(cut)
    assert bound < birth.next_height
    with pytest.raises(ValueError, match='positive face knot'):
        point_front_flux(birth, cut, float(bound), normal, normal)


def test_secondary_mass_receipts_pair_losses_with_gains_without_evolving_water():
    from subcell_source_activation import assembly
    from audit_south_fork_secondary_fronts import analyze
    part, _, _ = fixture()
    receipts = assembly(part, face_scheme='donor')['new_region_rates']
    result = analyze(part, receipts)
    assert result['original_flux_integration_controls_passed']
    assert result['original_water_unchanged']
    assert result['conservative_secondary_mass_terms']
    for term in result['conservative_secondary_mass_terms']:
        assert term['donor_volume_coefficient'] == -term['receiver_volume_coefficient']
        assert term['volume_time_power'] == F(5, 3)
        assert not term['receiver_connected_pool_update_accepted']
    assert not result['full_rational_front_or_force_or_time_or_native_or_gameplay_accepted']
    zero = [dict(r, momentum_rate=np.zeros(2)) for r in receipts]
    fan = analyze(part, zero)
    assert fan['original_flux_integration_controls_passed']
    assert all(t['volume_time_power'] == F(11, 6) for t in fan['conservative_secondary_mass_terms'])


def test_secondary_front_rejects_invalid_or_duplicate_receipts():
    from subcell_source_activation import assembly
    from audit_south_fork_secondary_fronts import analyze
    part, _, _ = fixture()
    receipts = assembly(part, face_scheme='donor')['new_region_rates']
    with pytest.raises(ValueError, match='Distinct original unowned'):
        analyze(part, receipts*2)
    with pytest.raises(ValueError, match='Positive original single-source'):
        analyze(part, [dict(receipts[0], volume_rate=-1.)])
