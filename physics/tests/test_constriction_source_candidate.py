import numpy as np

from audit_constriction_source_support import lower_returns
from recover_constriction_source_candidate import candidate_cells, reconstruct_added_flanks
from south_fork_mesh_sampling import grid_triangles


def test_stable_original_lower_return_selection():
    ids, counts = lower_returns(np.array([[0., 0., 4.], [0., 0., 2.], [0., 0., 2.], [1., 0., 5.]]),
                               np.array([0, 0, 0, 1]), np.array([10, 9, 8, 7]))
    np.testing.assert_array_equal(ids, [8, 7])
    np.testing.assert_array_equal(counts, [3, 1])


def test_connected_two_return_cells_only_and_no_hole_fill():
    authority = np.array([[3, 5, 2, 2], [2, 1, 4, 2], [2, 2, 2, 2]])
    chosen = np.full(authority.shape, 100)
    counts = np.full(authority.shape, 2)
    counts[0, 2] = 1
    counts[1, 0] = 0
    expected = np.zeros(authority.shape, bool)
    expected[0, 1] = True
    np.testing.assert_array_equal(candidate_cells(authority, chosen, counts), expected)


def test_diagonal_only_contact_not_connected():
    authority = np.array([[3, 2], [2, 5]])
    counts = np.array([[2, 0], [0, 2]])
    assert not candidate_cells(authority, np.ones((2, 2), int), counts).any()


def test_flank_prior_preserves_captures_and_bounded_support():
    east, north = np.meshgrid(np.arange(7.), np.arange(6., -1., -1.))
    authority = np.full((7, 7), 2, dtype=np.uint8)
    authority[3, 3] = 3
    authority[3, 4] = 1  # Another fixed captured ground vertex.
    height = np.zeros((7, 7), dtype=np.float32)
    height[3, 3], height[3, 4] = 4., 2.
    mesh = dict(east_m=east, north_m=north, z_m=height, authority=authority,
                triangles=grid_triangles(7, 7))
    added = authority == 3
    result, stats = reconstruct_added_flanks(mesh, added, np.zeros((7, 7)))
    protected = ~np.isin(authority, [2, 5]) | (np.hypot(east-3., north-3.) > 2.)
    np.testing.assert_array_equal(result['z_m'][protected], height[protected])
    np.testing.assert_array_equal(result['east_m'], east)
    np.testing.assert_array_equal(result['north_m'], north)
    np.testing.assert_array_equal(result['triangles'], mesh['triangles'])
    assert stats['inferred_changed_vertices'] > 0
    assert stats['maximum_distance_from_new_capture_m'] <= 2.
    assert np.all(result['authority'][(result['z_m'] != height)] == 5)
    assert result['z_m'].min() >= 0. and result['z_m'].max() <= 4.
