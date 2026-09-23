"""Tests for exact exported-support queries, not production contact acceptance."""
import numpy as np
from analyze_crew_support_stance import top_at_many


def test_slopes_winding_and_highest_surface():
    triangle = np.array([[0., 0., 3.], [2., 0., 5.], [0., 2., 7.]])
    lower = triangle.copy()
    lower[:, 2] -= 10.
    points = np.array([[.5, .5, 0.], [1., 1., 0.], [1.5, 1.5, 0.]])
    for order in (triangle, triangle[::-1]):
        actual = top_at_many(points, np.array([lower, order]))
        np.testing.assert_allclose(actual[:2], [4.5, 6.])
        assert np.isneginf(actual[2])


def test_spatial_bin_edges_do_not_drop_support():
    triangles = np.array([[[19., -1., 3.], [21., -1., 3.], [20., 2., 3.]]])
    points = np.array([[19.5, 0., 0.], [20., 0., 0.], [20.5, 0., 0.]])
    np.testing.assert_allclose(top_at_many(points, triangles), [3., 3., 3.])


def test_translation_and_vertical_faces():
    triangles = np.array([[[0., 0., 3.], [2., 0., 5.], [0., 2., 7.]],
                          [[0., 0., 100.], [0., 0., 130.], [0., 1., 100.]]])
    offset = np.array([10300., -7400., 2300.])
    actual = top_at_many(np.array([[.5, .5, 0.]])+offset, triangles+offset)
    np.testing.assert_allclose(actual, [2304.5])


def test_empty_mesh_reports_missing_not_invented_plane():
    assert np.isneginf(top_at_many(np.array([[0., 0., 0.]]), np.empty((0, 3, 3)))[0])
