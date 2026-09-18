"""Independent geometry and complete-resolution provider traversal controls."""
import numpy as np
import pytest

from build_chili_bar_captured_canopy import green_pixels, triangle_root_metrics
from fetch_chili_bar_ept_canopy import collect_nodes, node_bounds, overlaps_xy


def test_octree_bounds_and_touching_edges():
    bounds = [0, 0, -4, 8, 8, 4]
    np.testing.assert_array_equal(node_bounds('2-1-2-3', bounds), [2,4,2,4,6,4])
    assert overlaps_xy('2-1-2-3', bounds, [4,5,5,7])
    assert not overlaps_xy('2-1-2-3', bounds, [4.01,5,5,7])


@pytest.mark.parametrize('key', ['-1-0-0-0','1-2-0-0','1-0-0','31-0-0-0'])
def test_invalid_nodes_rejected(key):
    with pytest.raises(ValueError):
        node_bounds(key, [0,0,0,8,8,8])


def test_additive_ancestors_and_all_subtree_leaves_retained():
    pages = {'0-0-0-0': {'0-0-0-0': 17, '1-0-0-0': -1, '1-1-1-1': 999},
             '1-0-0-0': {'1-0-0-0': 23, '2-0-0-0': 41, '2-1-1-1': 59}}
    visited = []
    def load(key):
        visited.append(key)
        return pages[key]
    result = collect_nodes(load, [0,0,0,8,8,8], [.1,.1,3.9,3.9])
    assert result == {'0-0-0-0':17, '1-0-0-0':23, '2-0-0-0':41, '2-1-1-1':59}
    assert visited == ['0-0-0-0','1-0-0-0']


def test_unresolved_subtree_is_not_silent_low_resolution():
    with pytest.raises(ValueError, match='Unresolved'):
        collect_nodes(lambda key: {key:-1}, [0,0,0,8,8,8], [0,0,8,8])


def test_visible_green_requires_both_channels():
    np.testing.assert_array_equal(green_pixels([[80,110,70],[110,100,60],[60,100,110],[0,0,0]]), [True,False,False,False])


def test_roots_follow_both_original_triangles_not_bilinear():
    z = np.zeros((12,12)); valid = np.ones((11,11),bool); wet = np.zeros(z.shape,np.uint8)
    z[5,5], z[5,6], z[6,5], z[6,6] = 0, 1, 1, 3
    xy = np.array([[5.2,-5.3],[5.8,-5.7]])*2
    indices, heights, up = triangle_root_metrics(z,valid,wet,0,0,2,xy)
    np.testing.assert_array_equal(indices, [0,1])
    np.testing.assert_allclose(heights, [.5,2.])
    np.testing.assert_allclose(up, [1/np.sqrt(1.5),1/np.sqrt(3)])
    assert heights[0] != pytest.approx(.56)  # bilinear saddle height


@pytest.mark.parametrize('failure', ['wet','missing_quad','missing_height','steep','outside'])
def test_unsupported_roots_are_rejected_without_clamping(failure):
    z = np.zeros((12,12)); valid = np.ones((11,11),bool); wet = np.zeros(z.shape,np.uint8)
    xy = np.array([[10.4,-10.6]])
    if failure == 'wet': wet[3,3] = 1
    if failure == 'missing_quad': valid[7,7] = False
    if failure == 'missing_height': z[3,3] = np.nan
    if failure == 'steep': z[5,6] = 100
    if failure == 'outside': xy[0,0] = -100
    indices, heights, up = triangle_root_metrics(z,valid,wet,0,0,2,xy)
    assert len(indices) == len(heights) == len(up) == 0
