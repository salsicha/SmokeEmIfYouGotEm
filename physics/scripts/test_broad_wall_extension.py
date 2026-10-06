import numpy as np
from build_broad_wall_extension import connected_extensions


def test_only_edge_connected_components_survive():
    old=np.array([[0,1,2]])
    candidate=np.array([[0,3,4],[1,0,5],[5,0,6],[8,9,10]])
    np.testing.assert_array_equal(connected_extensions(old,candidate),candidate[[1,2]])


def test_connectivity_reaches_indirect_faces_in_reverse_order():
    old=np.array([[0,1,2]])
    candidate=np.array([[5,6,7],[0,5,6],[1,0,5]])
    np.testing.assert_array_equal(connected_extensions(old,candidate),candidate)


def test_no_connection_returns_empty_triangle_array():
    result=connected_extensions(np.array([[0,1,2]]),np.array([[0,3,4]]))
    assert result.shape==(0,3)
