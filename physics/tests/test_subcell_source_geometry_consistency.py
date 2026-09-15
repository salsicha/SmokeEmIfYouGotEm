"""Storage, face pressure and topology must describe the same represented bed."""
import numpy as np

from subcell_wet_pool_pressure import shared_subsegments
from triangle_cell_storage import cell_triangles
from subcell_exact_source_faces import triangle_cut
from test_triangle_face_section import sampler


def test_shared_subsegment_preserves_source_endpoint_heights_exactly():
    rng = np.random.default_rng(12791)
    for levels in rng.uniform(-10., 20., (64, 2)):
        segment = np.column_stack(([0., 1.], levels))
        result = list(shared_subsegments([(0, segment)], [(1, segment)]))
        assert len(result) == 1
        np.testing.assert_array_equal(result[0][2], segment)


def test_original_storage_face_consistency_still_required():
    # A separate, still-unmet representation requirement. The attempted exact
    # full-cell clip could not retain sub-ulp fragments in this storage API;
    # retain this gate instead of dropping fragments or loosening tolerances.
    source = sampler(lambda x, y: 8.1723+.38171*x-.2179*y+.1234567*x*y)
    center, spacing = np.array([.123456789, -.234567891]), np.array([.73, .91])
    triangles, ids = cell_triangles(source, center, spacing, with_source_ids=True)
    for source_id in sorted(set(ids)):
        for axis in (0, 1):
            for sign in (-1, 1):
                expected = triangle_cut(source.xyz[source.faces[source_id]], center, spacing, axis, sign)
                if expected is None:
                    continue
                segments = []
                for triangle in triangles[ids == source_id]:
                    for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
                        if a[axis] == b[axis] == sign*spacing[axis]/2 and a[1-axis] != b[1-axis]:
                            piece = np.array([[a[1-axis], a[2]], [b[1-axis], b[2]]])
                            segments.append(piece[np.argsort(piece[:, 0])])
                assert len(segments) == 1
                np.testing.assert_array_equal(segments[0], expected)
