import numpy as np
import pytest
from audit_downstream_cap_returns import neighbour_evidence


def test_original_neighbours_preserve_geometry_class_and_stable_ties():
    points = np.array([[0., 0., 3.], [.2, 0., 1.], [-.2, 0., 1.], [.1, 0., -5.], [.4, 0., -9.]])
    classes = np.array([1, 1, 2, 7, 2])
    original = points.copy()
    rows = neighbour_evidence(points[:1], np.array([0]), points, classes)
    assert rows[0]['lowest_original_id'] == 1
    assert rows[0]['nearby_original_count'] == 3
    assert rows[0]['lower_neighbour_drop_m'] == 2
    np.testing.assert_array_equal(points, original)
    np.testing.assert_array_equal(classes, [1, 1, 2, 7, 2])


@pytest.mark.parametrize('radius', [0, -1, float('nan'), float('inf')])
def test_invalid_diagnostic_radius(radius):
    with pytest.raises(ValueError):
        neighbour_evidence(np.zeros((1, 3)), np.array([0]), np.zeros((1, 3)), np.array([1]), radius)


def test_relocated_or_wrong_original_anchor_is_rejected():
    with pytest.raises(ValueError, match='exact original'):
        neighbour_evidence(np.ones((1, 3)), np.array([0]), np.zeros((1, 3)), np.array([1]))
