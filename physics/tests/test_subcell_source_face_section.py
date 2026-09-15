from fractions import Fraction as F

import numpy as np
import pytest

from subcell_source_face_section import SourceFaceSection, fragment_section, stage_difference
from subcell_exact_geometry import SourceRelativeStorage, cell_fragments
from subcell_donor_face_flux import flux as donor_flux
from subcell_dry_front_flux import flux as dry_flux
from subcell_energy_flux import face_flux_normal
from subcell_wet_connectivity import components
from subcell_wet_pool_pressure import harmonic_area
from subcell_wet_pool_pressure_rate import harmonic_area_rate
from triangle_face_section import TriangleFaceSection
from test_triangle_face_section import sampler


def test_positive_original_face_length_survives_collapsed_float_projection():
    width, depth = F(1, 10**40), 1e-100
    datum = F(220)+F(1, 3)
    section = SourceFaceSection([[(F(1), datum), (F(1)+width, datum)]])
    assert section.segments[0, 0, 0] == section.segments[0, 1, 0]
    assert section.lengths[0] == float(width)
    expected = [float(width)*depth, float(width)*depth*depth, float(width)]
    np.testing.assert_allclose(section.moments(depth, datum), expected, rtol=1e-15, atol=0)


def test_rounded_absolute_bed_cannot_create_false_wet_pressure_support():
    datum, gap = F(220)+F(1, 3), F(1, 10**30)
    section = SourceFaceSection([[(F(0), datum+gap), (F(1), datum+gap)]])
    projected = TriangleFaceSection(section.segments, [0., 1.])
    assert projected.moments(1e-40, float(datum))[0] > 0
    assert section.moments(1e-40, datum) == (0., 0., 0.)
    assert section.maximum_depth(1e-40, datum) == 0.


@pytest.mark.parametrize('scheme', ('donor', 'paired'))
def test_two_distinct_exact_datums_match_independent_local_frame_flux(scheme):
    datum, gap = F(220)+F(1, 3), F(1, 10**30)
    assert float(datum) == float(datum+gap)
    section = SourceFaceSection([[(F(0), datum), (F(1), datum)]])
    local = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0., 1.])
    lh, rh = 2e-31, 4e-31
    left, right, normal = [.3, -.2], [-.1, .4], [1., 0.]
    method = donor_flux if scheme == 'donor' else face_flux_normal
    actual, _ = method(section, lh, left, rh, right, normal, left_datum=datum, right_datum=datum+gap)
    expected, _ = method(local, lh, left, float(gap+F(rh)), right, normal)
    np.testing.assert_allclose(actual, expected, atol=0, rtol=2e-15)
    assert stage_difference(lh, datum, rh, datum+gap) == float(gap+F(rh)-F(lh))


def test_exact_datum_dry_front_matches_local_frame_including_energy_and_force():
    datum = F(220)+F(1, 3)
    section = SourceFaceSection([[(F(0), datum), (F(1), datum+1)]])
    local = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0., 1.])
    for stage in (.2, 1e-20, 1e-100):
        actual, info = dry_flux(section, stage, datum, [.4, -.2], [1., 0.], energy_datum=datum)
        expected, local_info = dry_flux(local, stage, 0., [.4, -.2], [1., 0.])
        np.testing.assert_allclose(actual, expected, rtol=3e-15, atol=0)
        np.testing.assert_allclose(info['nonadvective_momentum_flux'], local_info['nonadvective_momentum_flux'], rtol=3e-15, atol=0)
        np.testing.assert_allclose(info['energy_flux'], local_info['energy_flux'], rtol=3e-15, atol=0)


def test_shared_source_face_verifier_uses_exact_heights_not_float_tolerance():
    section = SourceFaceSection([[(F(0), F(220)), (F(1), F(221))]])
    split = SourceFaceSection([[(F(0), F(220)), (F(1, 2), F(441, 2))],
                               [(F(1, 2), F(441, 2)), (F(1), F(221))]])
    section.verify_shared(split)
    gap = F(1, 10**30)
    wrong = SourceFaceSection([[(F(0), F(220)+gap), (F(1), F(221)+gap)]])
    np.testing.assert_array_equal(section.segments, wrong.segments)
    with pytest.raises(ValueError, match='heights differ'):
        section.verify_shared(wrong)


def test_full_extent_restriction_reuses_read_only_geometry_not_water_values():
    datum, width = F(220)+F(1, 3), F(1, 10**40)
    section = SourceFaceSection([[(F(1), datum), (F(1)+width, datum+F(1, 10**30))]])
    restricted = section.restricted(F(1), F(1)+width)
    assert restricted is section
    assert not any(value.flags.writeable for value in (restricted.lengths, restricted.segments, restricted.levels))
    fresh = SourceFaceSection(section.source_segments)
    for stage in (0., 1e-40, 1e-31, 1e-25, .3):
        np.testing.assert_array_equal(restricted.depth_intervals(stage, datum), fresh.depth_intervals(stage, datum))
        np.testing.assert_array_equal(restricted.moments(stage, datum), fresh.moments(stage, datum))
    assert restricted.moments(1e-25, datum)[0] > 0


def test_proper_subinterval_is_still_cut_exactly_and_invalid_extents_reject():
    datum = F(220)+F(1, 3)
    section = SourceFaceSection([[(F(0), datum), (F(1), datum+1)]])
    low, high = F(1, 3), F(2, 3)
    restricted = section.restricted(low, high)
    assert restricted is not section
    assert restricted.source_segments == (((low, datum+low), (high, datum+high)),)
    restricted.verify_shared(SourceFaceSection(restricted.source_segments))
    for a, b in ((0, 0), (-1, 1), (0, 2)):
        with pytest.raises(ValueError, match='Positive represented source subinterval'):
            section.restricted(a, b)


def test_exact_relative_storage_connectivity_uses_the_actual_source_datum():
    source = sampler(lambda x, y: 220.+x+2*y)
    center, spacing = [.1, -.1], [1.2, .8]
    storage = SourceRelativeStorage(cell_fragments(source, center, spacing))
    result = components(source, storage, center, spacing, 1.)
    assert storage.datum == 0.
    assert storage.source_datum > 200
    assert result['component_count'] == 1
    assert result['shared_wet_source_edges'] > 0
    np.testing.assert_allclose(result['total_volume_m3'], storage.relative_volume_and_wet_area(1.)[0], atol=0)


@pytest.mark.parametrize('height', (.01, .3, 1., 4.))
def test_same_source_storage_and_boundary_pressure_balance_partial_lake(height):
    source = sampler(lambda x, y: 220.+x+2*y)
    center, spacing = [.1, -.1], [1.2, .8]
    fragments = cell_fragments(source, center, spacing)
    storage = SourceRelativeStorage(fragments)
    force = storage.hydrostatic_bed_force(height, relative=True)
    for axis in (0, 1):
        for sign in (-1, 1):
            section = fragment_section(fragments, axis, sign*F(spacing[axis])/2)
            normal = sign*np.eye(2)[axis]
            flux, _ = donor_flux(section, height, [0., 0.], height, [0., 0.], normal,
                                  left_datum=storage.source_datum, right_datum=storage.source_datum)
            assert flux[0] == 0.
            force -= flux[1:]
    np.testing.assert_allclose(force, [0., 0.], atol=3e-14, rtol=0)


def test_harmonic_pressure_column_and_direction_keep_distinct_subulp_datums():
    datum, width = F(220)+F(1, 3), F(1, 10**40)
    gap, lh, rh = F(1, 10**30), 2e-31, 4e-31
    section = SourceFaceSection([[(F(1), datum), (F(1)+width, datum)]])
    a, b = lh, float(gap+F(rh))
    expected = float(width)*2*a*b/(a+b)
    actual = harmonic_area(section, lh, rh, datum, datum+gap)
    np.testing.assert_allclose(actual, expected, atol=0, rtol=2e-15)
    left_rate, right_rate = .3, -.2
    expected_rate = float(width)*2*(b*b*left_rate+a*a*right_rate)/(a+b)**2
    rate = harmonic_area_rate(section, lh, rh, datum, datum+gap, left_rate, right_rate)
    np.testing.assert_allclose(rate, expected_rate, atol=0, rtol=2e-15)


def test_piecewise_exact_pressure_derivative_matches_independent_perturbation():
    datum = F(220)+F(1, 3)
    section = SourceFaceSection([[(F(0), datum), (F(1), datum+F(1, 2))],
                                 [(F(1), datum+F(1, 2)), (F(2), datum+F(3, 2))]])
    lh, rh, ld, rd = .6, .4, datum, datum+F(1, 3)
    rates = [.3, -.2]
    derivative = harmonic_area_rate(section, lh, rh, ld, rd, *rates)
    step = 1e-5
    expected = (harmonic_area(section, lh+step*rates[0], rh+step*rates[1], ld, rd)
                -harmonic_area(section, lh-step*rates[0], rh-step*rates[1], ld, rd))/(2*step)
    np.testing.assert_allclose(derivative, expected, rtol=1e-8, atol=1e-10)


@pytest.mark.parametrize('sign', (-1, 1))
def test_nonzero_unrepresentable_face_depth_is_not_reclassified_as_zero(sign):
    datum = F(220)
    section = SourceFaceSection([[(F(0), datum+sign*F(1, 10**400)),
                                  (F(1), datum+sign*F(1, 10**400))]])
    with pytest.raises(ValueError, match='depth exceeds represented range'):
        section.moments(0., datum)


def test_bed_queries_on_subulp_face_use_exact_tangent_coordinates():
    width = F(1, 10**40)
    section = SourceFaceSection([[(F(1), F(220)), (F(1)+width, F(222))]])
    np.testing.assert_array_equal(section.bed_at([F(1), F(1)+width/2, F(1)+width]), [220., 221., 222.])
    with pytest.raises(ValueError, match='Outside'):
        section.bed_at([F(1)+2*width])
