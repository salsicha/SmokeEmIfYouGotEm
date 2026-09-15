from fractions import Fraction as F

import numpy as np
import pytest

from subcell_exact_geometry import SourceRelativeStorage, area, cell_fragments, source_fragment
from subcell_pressure_kinetic_geometry import local_form
from subcell_exact_source_faces import triangle_cut
from triangle_cell_storage import projected_areas
from test_triangle_face_section import sampler
from audit_source_representation import audit_representation


def test_exact_storage_boundary_matches_original_source_face_cut():
    source = sampler(lambda x, y: 8.1723+.38171*x-.2179*y+.1234567*x*y)
    center, spacing = [.123456789, -.234567891], [.73, .91]
    for fragment in cell_fragments(source, center, spacing):
        for axis in (0, 1):
            for sign in (-1, 1):
                expected = triangle_cut(source.xyz[source.faces[fragment.source_id]], center, spacing, axis, sign)
                actual = fragment.face(axis, sign*F(spacing[axis])/2)
                if expected is None:
                    assert actual is None
                else:
                    np.testing.assert_array_equal(np.asarray(actual, float), expected)


def test_original_clip_retains_positive_fragments_collapsed_by_float_vertices():
    source = sampler(lambda x, y: 0*x+3.)
    before = source.xyz.copy(), source.faces.copy()
    spacing = [1.2, .8]
    fragments = cell_fragments(source, [.1, -.1], spacing)
    collapsed = []
    for fragment in fragments:
        for exact, floating in zip(fragment.triangles, np.asarray(fragment.triangles, float)):
            if projected_areas(floating[None])[0] == 0:
                assert area(exact) > 0
                collapsed.append(area(exact))
        # Exact hydrostatic storage retains these areas, without reconstructing
        # a determinant from rounded projected vertices.
        assert fragment.depth_moments(F(4)) == (fragment.area,)*4
    assert len(collapsed) >= 5
    assert sum(collapsed) > 0
    assert sum(f.area for f in fragments) == F(spacing[0])*F(spacing[1])
    np.testing.assert_array_equal(source.xyz, before[0])
    np.testing.assert_array_equal(source.faces, before[1])


@pytest.mark.parametrize('height', (F(1, 10), F(1, 2), F(1), F(1, 10**100)))
def test_partial_ramp_moments_match_independent_integral(height):
    # Original triangle x>=0, y>=0, x+y<=1; bed x+2y.
    fragment = source_fragment([[0, 0, 0], [1, 0, 1], [0, 1, 2]], [0, 0], [4, 4], 17)
    expected = tuple(height**(k+2)/(2*(k+1)*(k+2)) for k in range(4))
    assert fragment.depth_moments(height) == expected
    assert fragment.gradient == (F(1), F(2))
    assert fragment.source_id == 17


def test_thin_water_uses_exact_datum_plus_height_not_rounded_absolute_stage():
    fragment = source_fragment([[0, 0, 220], [1, 0, 221], [0, 1, 222]], [0, 0], [4, 4], 0)
    height = F(1, 10**100)
    assert float(F(220)+height) == 220.
    assert fragment.depth_moments(F(220)+height)[1] == height**3/12
    assert fragment.depth_moments(F(220)) == (F(0),)*4


def test_source_subdivision_preserves_area_moments_and_bed_force_exactly():
    triangle = [[0, 0, 0], [1, 0, 1], [0, 1, 2]]
    original = source_fragment(triangle, [0, 0], [4, 4], 0)
    pieces = [source_fragment(triangle, center, [1, 1], index)
              for index, center in enumerate(([0, 0], [1, 0], [0, 1], [1, 1]))]
    pieces = [p for p in pieces if p is not None]
    assert sum(p.area for p in pieces) == original.area
    for height in (F(1, 100), F(7, 10), F(3, 2), F(3)):
        expected = original.depth_moments(height)
        for k in range(4):
            assert sum(p.depth_moments(height)[k] for p in pieces) == expected[k]
        for axis in (0, 1):
            assert sum(p.gradient[axis]*p.depth_moments(height)[1] for p in pieces) == original.gradient[axis]*expected[1]


def test_original_source_gradients_survive_collapsed_clipped_triangles():
    source = sampler(lambda x, y: x+2*y)
    fragments = cell_fragments(source, [.1, -.1], [1.2, .8])
    assert any(np.any(projected_areas(np.asarray(f.triangles, float)) == 0) for f in fragments)
    assert all(f.gradient == (F(1), F(2)) for f in fragments)


def test_missing_source_and_invalid_geometry_are_not_repaired():
    source = sampler(lambda x, y: 0*x)
    with pytest.raises(ValueError, match='cover'):
        cell_fragments(source, [100, 100], [1, 1])
    for spacing in ([0, 1], [1, -1], [np.nan, 1]):
        with pytest.raises(ValueError):
            cell_fragments(source, [0, 0], spacing)
    with pytest.raises(ValueError, match='Degenerate original'):
        source_fragment([[0, 0, 0], [1, 0, 1], [2, 0, 2]], [0, 0], [1, 1], 0)


def test_relative_storage_keeps_exact_fragment_area_and_original_gradient():
    source = sampler(lambda x, y: x+2*y+220.)
    fragments = cell_fragments(source, [.1, -.1], [1.2, .8])
    storage = SourceRelativeStorage(fragments)
    assert len(storage.areas) == sum(len(f.triangles) for f in fragments)
    assert np.all(storage.areas > 0)
    expected = [float(area(t)) for f in fragments for t in f.triangles]
    np.testing.assert_array_equal(storage.areas, expected)
    np.testing.assert_array_equal(storage.bed_gradients, np.tile([1., 2.], (len(expected), 1)))
    with pytest.raises(ValueError, match='rounded-vertex'):
        _ = storage.triangles
    for fragment in fragments:
        child = storage.subset_sources([fragment.source_id])
        assert child.fragments == (fragment,)
        assert child.source_datum == min(v[2] for v in fragment.polygon)


@pytest.mark.parametrize('height', (.2, .7, 1.4, 3., 1e-100))
def test_local_kinetic_form_uses_new_relative_geometry_not_rounded_xyz(height):
    fragment = source_fragment([[0, 0, 220], [1, 0, 221], [0, 1, 222]], [0, 0], [4, 4], 0)
    storage = SourceRelativeStorage([fragment])
    exact = fragment.depth_moments(F(220)+F(height))
    volume = float(exact[1])
    result = local_form(storage, volume)
    np.testing.assert_allclose(result['depth_moments'], list(map(float, exact)), rtol=1e-12, atol=0)
    assert abs(result['stage_offset']/height-1) < 1e-12
    assert storage.source_datum == 220
    assert result['datum'] == 0.


def test_source_representation_audit_does_not_claim_evolution_acceptance():
    source = sampler(lambda x, y: x+2*y)
    result = audit_representation(source, [0, 0], (1, 2), [.5, .5], [.1, 0.])
    assert result['exact_representation_controls_passed']
    assert result['total_cells'] == 2
    assert result['positive_cells'] == 1
    assert not result['evolving_storage_or_topology_or_full_physics_or_gameplay_accepted']


@pytest.mark.parametrize('volumes', ([0.], [0., np.nan], [0., np.inf], [0., -.1]))
def test_representation_audit_requires_every_finite_actual_cell(volumes):
    source = sampler(lambda x, y: 0*x)
    with pytest.raises(ValueError, match='per requested source cell'):
        audit_representation(source, [0, 0], (1, 2), [.5, .5], volumes)
