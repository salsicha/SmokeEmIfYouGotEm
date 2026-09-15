"""Source retention and exact geometric checks, not physical/visual acceptance."""
import numpy as np
import pytest
from build_troublemaker_dem_rock_cap import (select_lower_returns, cap_triangles, sample_cap,
    refine_source_coverage,close_cap_below_retained_terrain,sample_terrain_union,native_collision_probes)

REGION = [[-1,-1],[3,-1],[3,3],[-1,3]]


def test_lower_envelope_retains_original_xyz_and_stable_source_index():
    xyz=np.array([[.1,.1,4],[.2,.2,3],[.3,.3,3],[.7,.1,8],[.8,.2,7],[1.1,.1,2.]])
    before=xyz.copy()
    ids,counts=select_lower_returns(xyz,np.ones(6),np.ones(6),REGION)
    assert ids.tolist()==[1,4] and counts.tolist()==[3,2]
    assert np.array_equal(xyz,before)
    assert np.array_equal(xyz[ids],[[.2,.2,3],[.8,.2,7]])


def test_noise_water_and_outside_points_cannot_support_a_rock_bin():
    xyz=np.array([[.1,.1,4],[.2,.2,5],[.3,.3,1],[.4,.4,1],[8,8,4.]])
    ids,_=select_lower_returns(xyz,[1,7,9,18,2],np.ones(5),REGION)
    assert not len(ids)


def test_clearance_is_strict_and_does_not_require_water_membership():
    xyz=np.array([[.1,.1,4],[.2,.2,5],[.3,.3,2]])
    ids,counts=select_lower_returns(xyz,[1,10,2],[.4,.5,.3],REGION)
    assert ids.tolist()==[0] and counts.tolist()==[2]


def test_singleton_requires_two_original_neighbours_and_does_not_propagate():
    xyz=np.array([[.1,.1,4],[.2,.2,4.1],[.6,.1,4],[.7,.2,4.2],
                  [.6,.6,4.1],[1.1,.6,4.2],[1.1,.1,7.]])
    ids,counts=select_lower_returns(xyz,[1]*7,[1]*7,REGION,corroborate_single_returns=True)
    assert ids.tolist()==[0,2,4] and counts.tolist()==[2,2,1]
    assert 5 not in ids  # One original neighbour + new singleton cannot seed it.
    assert 6 not in ids  # Does not meet the original neighbour-height constraint.


def test_singleton_outlier_is_not_accepted_even_with_two_original_neighbours():
    xyz=np.array([[.1,.1,4],[.2,.2,4.1],[.6,.1,4],[.7,.2,4.2],[.6,.6,8.]])
    ids,_=select_lower_returns(xyz,[1]*5,[1]*5,REGION,corroborate_single_returns=True)
    assert ids.tolist()==[0,2]


def test_local_faces_and_sampling_reproduce_original_plane():
    xy=np.array([[0,0],[.5,0],[0,.5],[.5,.5],[1,0],[1,.5]])
    xyz=np.column_stack([xy,3+2*xy[:,0]-xy[:,1]])
    faces=cap_triangles(xyz,REGION)
    centroids=xyz[faces].mean(axis=1)
    assert np.allclose(sample_cap(xyz,faces,centroids[:,:2]),centroids[:,2],rtol=0,atol=1e-12)
    assert np.allclose(sample_cap(xyz,faces,xy),xyz[:,2],rtol=0,atol=1e-12)
    assert np.isnan(sample_cap(xyz,faces,[[2,2]])[0])


def test_large_source_gap_is_not_bridged():
    xyz=np.array([[0,0,3],[.5,0,3],[0,.5,3],[2,0,4],[2.5,0,4],[2,.5,4.]])
    faces=cap_triangles(xyz,REGION)
    assert len(faces)==2
    assert np.isnan(sample_cap(xyz,faces,[[1,0]])[0])


def test_coarse_selection_cannot_create_a_hole_where_original_points_exist():
    xy=np.array([[0,0],[1,0],[0,1],[.5,0],[0,.5],[.5,.5],[.25,.25]])
    xyz=np.column_stack([xy,3+xy[:,0]])
    chosen=refine_source_coverage(xyz,[0,1,2],REGION)
    assert len(chosen)>3
    assert set(chosen).issubset(range(len(xyz)))
    faces=cap_triangles(xyz[chosen],REGION)
    assert sample_cap(xyz[chosen],faces,[[.2,.2]])[0]==pytest.approx(3.2)
    assert np.linalg.norm(xyz[chosen][faces,:2]-np.roll(xyz[chosen][faces,:2],1,axis=1),axis=2).max()<=1


def test_refinement_does_not_invent_points_for_a_true_source_gap():
    xyz=np.array([[0,0,3],[2,0,4],[0,2,4.]])
    chosen=refine_source_coverage(xyz,[0,1,2],REGION)
    assert chosen.tolist()==[0,1,2]
    with pytest.raises(ValueError,match='No supported'):cap_triangles(xyz[chosen],REGION)


def test_concave_search_boundary_is_not_filled():
    region=[[0,0],[2,0],[2,.5],[.5,.5],[.5,2],[0,2]]
    xyz=np.array([[0,0,2],[.5,0,2],[0,.5,2],[.5,.5,2],[1,.5,2],[.5,1,2]])
    faces=cap_triangles(xyz,region)
    assert np.isnan(sample_cap(xyz,faces,[[.6,.6]])[0])


@pytest.mark.parametrize('cell,count,threshold',[(0,2,.3),(.5,0,.3),(.5,1.5,.3),(.5,2,-1)])
def test_invalid_selection_parameters_fail(cell,count,threshold):
    with pytest.raises(ValueError):select_lower_returns(np.ones((3,3)),[1]*3,[1]*3,REGION,cell,count,threshold)


def test_duplicate_xy_and_reversed_faces_fail():
    with pytest.raises(ValueError,match='duplicate'):cap_triangles(np.array([[0,0,1],[0,0,2],[1,1,2]]),REGION)
    with pytest.raises(ValueError,match='reversed'):sample_cap(np.array([[0,0,1],[1,0,2],[0,1,3]]),np.array([[0,2,1]]),[[.1,.1]])


def test_closed_solid_retains_original_roof_and_has_exact_volume():
    xyz=np.array([[0,0,3],[1,0,4],[0,1,3.]])
    faces=np.array([[0,1,2]])
    v,t,k,report=close_cap_below_retained_terrain(xyz,faces,1.)
    assert np.array_equal(v[:3],xyz)
    assert len(t)==8 and sorted(k.tolist())==[0,1,2,2,2,2,2,2]
    assert report['volume_m3']==pytest.approx(7/6)
    assert report['maximum_volume_error_m3']<1e-12
    with pytest.raises(ValueError):close_cap_below_retained_terrain(xyz,faces,3.)


def test_physical_union_keeps_parent_outside_cap_and_where_parent_is_higher():
    class Parent:
        def sample(self,x,y):return np.full(len(x),3.)
    xyz=np.array([[0,0,2],[1,0,4],[0,1,2.]])
    points=np.array([[.1,.1],[.8,.1],[2,2]])
    result=sample_terrain_union(Parent(),xyz,np.array([[0,1,2]]),points)
    assert result.tolist()==pytest.approx([3,3.6,3])


def test_native_cone_rays_keep_every_original_point_and_enter_the_solid():
    xyz=np.array([[0,0,3],[1,0,4],[0,1,3.]])
    faces=np.array([[0,1,2]])
    v,t,k,_=close_cap_below_retained_terrain(xyz,faces,0.)
    report=native_collision_probes(xyz,faces,v,t,k,'source')
    assert report['source_cap_sha256']=='source'
    vertical=[p for p in report['probes'] if p['kind']=='original_roof_vertex']
    cone=[p for p in report['probes'] if p['kind']=='original_vertex_interior_cone']
    assert len(vertical)==len(cone)==len(xyz)
    for original,p in zip(xyz,cone):
        assert np.array_equal(p['world_position_cm'],original*[100,-100,100])
        n=np.array(p['outward_normal'])*[1,-1,1]
        assert np.linalg.norm(n)==pytest.approx(1)
        interior=original-n*.01
        roof=sample_cap(xyz,faces,interior[None,:2])[0]
        assert np.isfinite(roof) and 0<interior[2]<roof


def test_vertical_extremal_rays_can_miss_quantized_footprint_without_large_xyz_error():
    xyz=np.array([[-6.967397715430707,17.61073176469654,9.100939801879605],
                  [-6,17,10],[-6,18,10.]])
    faces=cap_triangles(xyz,[[-8,16],[-5,16],[-5,19],[-8,19]],maximum_edge_m=2.)
    quantized=(xyz*100).astype(np.float32).astype(float)/100
    assert np.isfinite(sample_cap(xyz,faces,xyz[:1,:2])[0])
    assert np.isnan(sample_cap(quantized,faces,xyz[:1,:2])[0])
    assert np.linalg.norm((quantized-xyz)*100,axis=1).max()<.1
