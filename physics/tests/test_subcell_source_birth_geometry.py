from fractions import Fraction as F
import numpy as np
import pytest

from subcell_exact_geometry import SourceRelativeStorage, SourceFragment, source_fragment
from subcell_source_birth_geometry import SourceBirthGeometry, value
from subcell_source_face_section import SourceFaceSection
from subcell_pressure_kinetic_geometry import local_form


def storage(kind, datum=0):
    levels = {'flat': [0, 0, 0], 'edge': [0, 0, 2], 'point': [0, 1, 2]}[kind]
    points = [[x, y, datum+z] for (x, y), z in zip([(0, 0), (1, 0), (0, 1)], levels)]
    return SourceRelativeStorage([source_fragment(points, [0, 0], [4, 4], 17)])


@pytest.mark.parametrize('kind,power,coefficient', [('flat', 1, F(1, 2)), ('edge', 2, F(1, 4)), ('point', 3, F(1, 12))])
def test_original_birth_polynomials_match_independently_clipped_source_moments(kind, power, coefficient):
    source = storage(kind, 220)
    birth = SourceBirthGeometry(source)
    assert birth.volume_power == power and birth.volume_coefficient == coefficient
    for height in [F(1, 8), F(1, 100), F(1, 10**100)]:
        expected = tuple(sum(f.depth_moments(source.source_datum+height)[k] for f in source.fragments) for k in range(4))
        assert birth.moments(height) == expected
        # Independent exact integration of the original completed-square Gram.
        m0, m1, m2, m3 = expected
        b = source.fragments[0].gradient
        gram = ((m3, -F(3, 2)*m2*b[0], -F(3, 2)*m2*b[1]),
                (-F(3, 2)*m2*b[0], 3*m1*b[0]**2, 3*m1*b[0]*b[1]),
                (-F(3, 2)*m2*b[1], 3*m1*b[0]*b[1], 3*m1*b[1]**2))
        assert birth.gram(height) == gram
        rates = birth.stage_rates(height, F(3, 7))
        for k in range(1, 4):
            assert rates[k] == F(3, 7)*k*expected[k-1]
    assert birth.moments(0)[1:] == (0, 0, 0)
    assert birth.gram(0) == ((0, 0, 0),)*3
    assert birth.record()['stage_inverse_derivative_singular_at_birth'] == (power > 1)
    assert not birth.record()['full_pressure_or_front_flux_or_time_or_gameplay_accepted']


def test_flat_zero_area_is_explicit_right_limit_not_artificial_positive_water():
    birth = SourceBirthGeometry(storage('flat'))
    assert birth.moments(0) == (F(1, 2), 0, 0, 0)
    assert birth.stage_rates(0, 2) == (0, 1, 0, 0)
    for kind in ('edge', 'point'):
        assert SourceBirthGeometry(storage(kind)).stage_rates(0, 2)[1] == 0
    with pytest.raises(ValueError, match='birth cone'):
        birth.stage_rates(0, -1)


@pytest.mark.parametrize('kind,a,c', [('flat', F(1), F(0)), ('edge', F(1, 2), F(-1)), ('point', F(3, 10), F(-3, 4))])
def test_scaled_divergence_limit_keeps_exact_vertical_inertia(kind, a, c):
    source = storage(kind)
    birth = SourceBirthGeometry(source)
    bx, by = source.fragments[0].gradient
    expected = ((a, c*bx, c*by), (c*bx, 3*bx*bx, 3*bx*by), (c*by, 3*bx*by, 3*by*by))
    assert birth.scaled_gram_limit == expected
    # PSD is checked on exact principal minors, not by clipping eigenvalues.
    for i in range(3):
        assert expected[i][i] >= 0
        for j in range(i+1, 3):
            assert expected[i][i]*expected[j][j]-expected[i][j]**2 >= 0
    height = 1e-5
    volume = float(birth.moments(F(height))[1])
    original = local_form(source, volume)
    scale = np.diag([1/height, 1, 1])
    np.testing.assert_allclose(scale@original['gram']@scale/volume, np.asarray(expected, float), atol=1e-5, rtol=1e-5)


def test_source_polygon_fan_and_source_subdivision_preserve_full_birth_polynomial():
    # A clipped rectangle on bed y: its two fan triangles have different
    # minimum multiplicities. Their cubic terms MUST cancel exactly.
    whole = SourceFragment(3, tuple(tuple(map(F, v)) for v in [(0, 0, 220), (1, 0, 220), (1, 1, 221), (0, 1, 221)]), (F(0), F(1)))
    first = SourceBirthGeometry(SourceRelativeStorage([whole]))
    split = SourceBirthGeometry(SourceRelativeStorage([SourceFragment(i, t, whole.gradient) for i, t in enumerate(whole.triangles)]))
    assert first.moment_polynomials == split.moment_polynomials
    assert first.gram_polynomials == split.gram_polynomials
    assert first.moment_polynomials[1] == {2: F(1, 2)}
    assert first.volume_power == 2
    for k, polynomial in enumerate(first.moment_polynomials):
        assert polynomial == {k+1: F(1, k+1)}


@pytest.mark.parametrize('kind', ['flat', 'edge', 'point'])
def test_exact_birth_face_area_and_scaled_divergence(kind):
    source = storage(kind, 220)
    birth = SourceBirthGeometry(source)
    polygon = source.fragments[0].polygon
    for i, j in [(0, 1), (0, 2)]:
        section = SourceFaceSection([[(F(0), polygon[i][2]), (F(1), polygon[j][2])]])
        polynomial = birth.face_area_polynomial(section)
        for height in (F(1, 16), F(1, 100), F(1, 10**100)):
            # Exact integral of the clipped affine face, independent of the
            # storage polynomial and using only the source endpoints.
            low, high = sorted((polygon[i][2]-birth.datum, polygon[j][2]-birth.datum))
            expected = height if high == 0 else height*height/(2*high)
            assert value(polynomial, height) == expected
        limit = birth.scaled_face_divergence_limit(section)
        if kind == 'flat':
            assert limit == 0
        elif kind == 'edge' and j == 1:
            assert limit == 4
        elif kind == 'point':
            assert limit == 6/(polygon[j][2]-birth.datum)


def test_positive_height_source_face_has_no_initial_connection():
    birth = SourceBirthGeometry(storage('point', 220))
    section = SourceFaceSection([[(0, 221), (1, 222)]])
    assert birth.face_area_polynomial(section) == {}
    assert birth.scaled_face_divergence_limit(section) == 0
    contact = birth.face_contact(section)
    assert contact == dict(height_above_source_minimum=F(1),
                           stored_volume_before_face_opens=F(1, 12), contact_starts_at_birth=False)
    # Subdivision by the opposite source trace introduces an earlier face knot
    # without changing the receiving polygon or its own storage interval.
    subset = SourceFaceSection([[(0, F(441, 2)), (1, 221)]])
    assert birth.face_area_polynomial(subset) == {}
    assert birth.face_next_height(subset) == F(1, 2)
    assert birth.next_height == 1
    with pytest.raises(ValueError, match='below original'):
        birth.face_area_polynomial(SourceFaceSection([[(0, 219), (1, 220)]]))


def test_face_contact_can_follow_multiple_storage_knots_without_extending_birth_polynomial():
    birth = SourceBirthGeometry(storage('point', 220))
    face = SourceFaceSection([[(0, F(443, 2)), (1, 222)]])
    contact = birth.face_contact(face)
    assert contact['height_above_source_minimum'] == F(3, 2)
    assert contact['stored_volume_before_face_opens'] == birth.fragments[0].depth_moments(F(443, 2))[1]
    assert not contact['contact_starts_at_birth']
    with pytest.raises(ValueError, match='first original'):
        birth.moments(contact['height_above_source_minimum'])
    assert birth.face_contact(SourceFaceSection([[(0, 220), (1, 221)]]))['contact_starts_at_birth']


def test_birth_cone_and_exact_source_contract_reject_without_repair():
    birth = SourceBirthGeometry(storage('point'))
    for height in [-1, 1, 2, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            birth.moments(height)
    with pytest.raises(ValueError, match='exact-source'):
        SourceBirthGeometry(object())
    with pytest.raises(ValueError, match='exact source face'):
        birth.face_area_polynomial(np.array([[0., 0.], [1., 1.]]))
    with pytest.raises(ValueError):
        birth.stage_rates(F(1, 2), float('inf'))
