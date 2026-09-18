import numpy as np
import pytest
from source_native_triangle_hash import triangle_hash


def test_directed_geometry_invariance_and_mutation_controls():
    v = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 2.], [1., 1., 3.]])
    f = np.array([[0, 1, 2], [1, 3, 2]])
    value = triangle_hash(v, f)
    assert value == triangle_hash(v, f[::-1, [1, 2, 0]])
    assert value == triangle_hash(v[::-1], 3-f)
    assert value != triangle_hash(v, f[:, ::-1])
    moved = v.copy(); moved[2, 2] += .001
    assert value != triangle_hash(moved, f)
    assert value != triangle_hash(v, f, np.array([0, 1]))


def test_duplicate_corner_rotations_match():
    v = np.array([[0., 0., 0.], [1., 0., 0.]])
    assert triangle_hash(v, np.array([[0, 1, 0]])) == triangle_hash(v, np.array([[0, 0, 1]]))


def test_invalid_source_rejected():
    with pytest.raises(ValueError):
        triangle_hash(np.array([[np.nan, 0, 0]]), np.array([[0, 0, 0]]))
