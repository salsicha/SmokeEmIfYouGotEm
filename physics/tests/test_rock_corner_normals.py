import numpy as np
import pytest
from rock_corner_normals import corner_normals


def fixture(angle=25.):
    a = np.deg2rad(angle)
    return np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, -np.cos(a), np.sin(a)]]), np.array([[0, 1, 2], [1, 0, 3]])


def test_smooth_join_preserves_source_and_unit_normals():
    v, f = fixture(); before = v.copy(), f.copy()
    n, info = corner_normals(v, f, [1, 1], 45.)
    np.testing.assert_array_equal(n[0, 0], n[1, 1])
    np.testing.assert_array_equal(n[0, 1], n[1, 0])
    np.testing.assert_allclose(np.linalg.norm(n, axis=2), 1, atol=1e-15)
    np.testing.assert_array_equal(v, before[0]); np.testing.assert_array_equal(f, before[1])
    assert info['smooth_edge_count'] == 1 and info['shading_fan_count'] == 4


@pytest.mark.parametrize('angle,kinds', [(70., [1, 1]), (25., [1, 2])])
def test_fractures_and_provenance_are_split(angle, kinds):
    v, f = fixture(angle)
    n, info = corner_normals(v, f, kinds, 45.)
    assert info['smooth_edge_count'] == 0
    np.testing.assert_array_equal(n[:, 0], n[:, 1])
    np.testing.assert_array_equal(n[:, 0], n[:, 2])
    assert not np.array_equal(n[0, 0], n[1, 1])


def test_touching_only_at_vertex_does_not_join():
    v, f = fixture()
    v = np.concatenate([v, v[1:2]])
    f[1, 0] = 4
    _, info = corner_normals(v, f, [1, 1], 45.)
    assert info['smooth_edge_count'] == 0 and info['shading_fan_count'] == 6


def test_nonmanifold_edge_is_not_smoothed():
    v, f = fixture()
    _, info = corner_normals(v, np.concatenate([f, f[1:]]), [1, 1, 1], 45.)
    assert info['smooth_edge_count'] == 0


def test_reflection_and_winding_transform_normals():
    v, f = fixture()
    n, _ = corner_normals(v, f, [1, 1], 45.)
    reflection = np.array([1., -1., 1.])
    actual, _ = corner_normals(v*reflection, f[:, [0, 2, 1]], [1, 1], 45.)
    np.testing.assert_allclose(actual, n[:, [0, 2, 1]]*reflection, atol=1e-15)


@pytest.mark.parametrize('angle', [0., 90., float('nan'), float('inf')])
def test_invalid_crease_rejected(angle):
    v, f = fixture()
    with pytest.raises(ValueError): corner_normals(v, f, [1, 1], angle)


def test_degenerate_triangle_rejected():
    v, f = fixture(); f[0, 2] = 1
    with pytest.raises(ValueError): corner_normals(v, f, [1, 1], 45.)
