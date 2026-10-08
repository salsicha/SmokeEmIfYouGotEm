"""Coordinate construction regressions; no claim of playable acceptance."""
import numpy as np
import pytest

from build_futaleufu_continuous_route import geographic_chart, mainstem_join


def test_exact_tributary_join_retains_complete_mainstem():
    assert mainstem_join([[0,1],[1,1],[2,0],[3,0]], [[1,0],[2,0],[3,0],[4,0]]) == (2,1,2)


@pytest.mark.parametrize('route,main', [
    ([[0,1],[2,0],[1,0]], [[1,0],[2,0]]),
    ([[0,1],[1,0],[3,0]], [[1,0],[2,0],[3,0]]),
    ([[0,1],[1,0],[2,1],[3,0]], [[1,0],[2,0],[3,0]]),
    ([[0,1],[1,.0001],[2,1]], [[1,0],[2,0]]),
    ([[1,0],[2,0]], [[1,0],[2,0]]),
    ([[0,1],[1,0],[2,0]], [[1,0],[2,0],[1,0]])])
def test_no_shortcuts_reverse_jumps_or_ambiguous_junction(route, main):
    with pytest.raises(ValueError):
        mainstem_join(route, main)


def test_original_corner_and_both_endpoints_survive_resampling():
    xy = np.array([[10,20],[13,20],[13,24]], dtype=float)
    points, source = geographic_chart(xy, [10,20], 2.)
    np.testing.assert_array_equal(source, [0,3,7])
    assert all(s in points[:,0] for s in [0,2,3,4,6,7])
    np.testing.assert_array_equal(points[np.searchsorted(points[:,0],source),1:3], xy-[10,20])
    np.testing.assert_allclose(np.linalg.norm(points[:,3:5],axis=1), 1)
    np.testing.assert_allclose(points[0,3:5], [0,1])
    np.testing.assert_allclose(points[-1,3:5], [-1,0])
    np.testing.assert_allclose(points[np.searchsorted(points[:,0],3),3:5], [-2**-.5,2**-.5])
    assert np.diff(points[:,0]).max() <= 2
    for sign in (-1,1):
        assert np.linalg.norm(np.diff(points[:,1:3]+sign*256*points[:,3:5],axis=0),axis=1).max() <= 12


@pytest.mark.parametrize('xy', [[], [[1,2]], [[1,2],[1,2]], [[0,0],[np.nan,1]], [[0,0],[1,0],[0,0]]])
def test_rejects_invalid_or_reversing_geometry(xy):
    with pytest.raises(ValueError):
        geographic_chart(xy, [0,0])


@pytest.mark.parametrize('spacing', [0,-1,np.inf,np.nan])
def test_rejects_invalid_sampling(spacing):
    with pytest.raises(ValueError):
        geographic_chart([[0,0],[10,0]], [0,0], spacing)


def test_translation_preserves_chart_and_stations():
    xy = np.array([[0,0],[3,0],[3,5]], dtype=float)
    a, sa = geographic_chart(xy,[0,0])
    b, sb = geographic_chart(xy+[740000,5195000],[740000,5195000])
    np.testing.assert_allclose(a,b)
    np.testing.assert_array_equal(sa,sb)
