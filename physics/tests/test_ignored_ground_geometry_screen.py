import numpy as np
import pytest
from audit_eldorado_ignored_ground_geometry import peer_support


def test_self_noise_and_class_ten_are_not_ground_corroboration():
    xyz = np.array([[0.,0.,3.], [.1,0.,4.], [.2,0.,2.], [.3,0.,0.], [.4,0.,1.]])
    classes = np.array([20, 2, 1, 10, 9])
    row = peer_support(xyz, classes, [0])[0]
    assert row['peer_count'] == 2
    assert row['classified_ground_peer_indices'] == [1]
    assert row['classified_ground_peer_height_delta_m'] == [1.]
    np.testing.assert_array_equal(classes, [20, 2, 1, 10, 9])


def test_isolated_observation_has_no_corroboration():
    row = peer_support([[0.,0.,3.]], [20], [0])[0]
    assert row['peer_count'] == row['classified_ground_peer_count'] == 0


@pytest.mark.parametrize('ids', [[-1], [1], [.1]])
def test_bad_original_indices_rejected(ids):
    with pytest.raises(ValueError):
        peer_support([[0.,0.,3.]], [20], ids)
