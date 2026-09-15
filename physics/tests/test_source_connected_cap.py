import numpy as np
import pytest
import json

from build_troublemaker_source_connected_cap import lower_bins, connected_support, separate_vertex_fans, recover_segment, constrained_extension
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


def test_lower_bins_keep_actual_lowest_xyz_with_original_id_tie():
    xyz=np.array([[.1,.1,2],[.2,.2,1],[.3,.3,1],[1.1,1.1,5.]])
    ids,keys,counts=lower_bins(xyz,np.array([3,2,1,0]))
    assert ids.tolist()==[1] and keys.tolist()==[[0,0]] and counts.tolist()==[3]
    assert np.array_equal(xyz[ids],[[.2,.2,1]])


@pytest.mark.parametrize('ids',[np.array([],int),np.array([0,0]),np.array([-1]),np.array([4]),np.array([0.])])
def test_invalid_original_ids_rejected(ids):
    with pytest.raises(ValueError):lower_bins(np.ones((4,3)),ids)


@pytest.mark.parametrize('count',[0,1.5])
def test_count_is_a_positive_integer(count):
    with pytest.raises(ValueError):lower_bins(np.ones((4,3)),np.arange(4),minimum_count=count)


def test_connectivity_stops_at_actual_low_ground_not_missing_data():
    gaps={(0,0):2.,(1,0):1.,(2,0):.2,(3,0):2.,(1,1):.3,(2,2):4.}
    active,collar,missing=connected_support(gaps,[(0,0)])
    assert active=={(0,0),(1,0)}
    assert collar=={(2,0),(1,1)}
    assert ((0,0),(-1,0)) in missing
    assert (3,0) not in active and (2,2) not in active


def test_diagonal_contact_does_not_connect_unrelated_outcrop():
    active,collar,_=connected_support({(0,0):1.,(1,1):1.},[(0,0)])
    assert active=={(0,0)} and collar==set()


def test_forced_old_seed_is_retained_even_if_lower_same_bin_observation_exists():
    active,_,_=connected_support({(0,0):0.,(1,0):1.},[(0,0)])
    assert active=={(0,0),(1,0)}


def test_numpy_seed_bins_produce_serializable_missing_support():
    _,_,missing=connected_support({(0,0):1.},np.array([[0,0]],dtype=np.int64))
    assert len(json.loads(json.dumps(missing)))==4


def test_disconnected_fans_are_exact_geometry_not_filled_holes():
    xyz=np.array([[0,0,2],[1,0,2],[0,1,2],[-1,0,3],[0,-1,3.]])
    faces=np.array([[0,1,2],[0,3,4]])
    with pytest.raises(ValueError,match='nonmanifold'):
        close_cap_below_retained_terrain(xyz,faces,0.)
    vertices,new_faces,source_indices=separate_vertex_fans(xyz,faces)
    assert len(vertices)==6 and source_indices.tolist()==[0,1,2,3,4,0]
    assert np.array_equal(vertices[new_faces],xyz[faces])
    _,_,_,report=close_cap_below_retained_terrain(vertices,new_faces,0.)
    assert report['volume_m3']==pytest.approx(7/3)


def test_connected_fan_is_unchanged():
    xyz=np.array([[0,0,2],[1,0,2],[1,1,3],[0,1,2.]])
    faces=np.array([[0,1,2],[0,2,3]])
    vertices,new_faces,mapping=separate_vertex_fans(xyz,faces)
    assert np.array_equal(vertices,xyz) and np.array_equal(new_faces,faces)
    assert mapping.tolist()==[0,1,2,3]


def test_nonmanifold_edge_is_not_silently_removed():
    xyz=np.array([[0,0,1],[1,0,1],[0,1,1],[0,-1,1],[.5,.5,1.]])
    with pytest.raises(ValueError,match='Nonmanifold source edge'):
        separate_vertex_fans(xyz,np.array([[0,1,2],[1,0,3],[0,1,4]]))


def test_segment_recovery_flips_crossing_diagonal_without_new_vertices():
    xyz=np.array([[0,0,3],[1,0,1],[1,1,3],[0,1,1.]])
    faces=np.array([[0,1,3],[1,2,3]])
    result=recover_segment(xyz,faces,0,2)
    assert len(result)==2 and set(result.ravel())=={0,1,2,3}
    assert all(0 in f and 2 in f for f in result)


def test_preserved_nonplanar_roof_faces_remain_exact():
    xyz=np.array([[0,0,3],[1,0,1],[1,1,3],[0,1,1],[-1,-1,0],[2,-1,0],[2,2,0],[-1,2,0.]])
    old=np.array([[0,1,2],[0,2,3]])
    result=constrained_extension(xyz,old,maximum_edge_m=5.)
    assert np.array_equal(result[:2],old)
    assert len(result)>2
    assert np.array_equal(xyz[result[:2]],xyz[old])


def test_recover_existing_segment_is_bit_exact_noop():
    xyz=np.array([[0,0,1],[1,0,1],[0,1,2.]])
    faces=np.array([[0,1,2]])
    assert np.array_equal(recover_segment(xyz,faces,0,1),faces)
