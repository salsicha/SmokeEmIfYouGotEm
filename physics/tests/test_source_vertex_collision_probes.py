import numpy as np
import pytest

from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain
from prepare_source_vertex_collision_probes import segment_hits,visible_vertex_probes


def test_segment_hits_respect_first_surface_and_segment_limits():
    triangle=np.array([[0,0,0],[1,0,0],[0,1,0.]])
    layers=np.array([triangle,triangle+[0,0,2],triangle+[0,0,4]])
    assert segment_hits(layers,[.2,.2,3],[.2,.2,-1]).tolist()==pytest.approx([.25,.75])
    assert len(segment_hits(layers,[2,2,3],[2,2,-1]))==0
    assert len(segment_hits(layers,[.2,.2,1],[.3,.2,1]))==0


def test_shared_vertex_is_retained_and_nonfinite_segment_rejected():
    triangle=np.array([[[0,0,0],[1,0,0],[0,1,0.]]])
    assert segment_hits(triangle,[0,0,1],[0,0,-1]).tolist()==[.5]
    with pytest.raises(ValueError):segment_hits(triangle,[0,0,np.nan],[0,0,-1])
    with pytest.raises(ValueError):segment_hits(triangle,[0,0,1],[0,0,1])


def test_visible_cones_use_all_incident_planes_without_moving_vertices():
    xyz=np.array([[0,0,1],[1,0,1],[1,1,6],[0,1,1.]])
    faces=np.array([[0,1,3],[1,2,3]])
    solid,closed,_,_=close_cap_below_retained_terrain(xyz,faces,0.)
    probes=visible_vertex_probes(xyz,faces,solid,closed)
    assert len(probes)==len(xyz)
    for i,p in enumerate(probes):
        assert np.array_equal(p['world_position_cm'],xyz[i]*[100,-100,100])
        assert p['source_first_hit_error_cm']<1e-7
        n=np.array(p['outward_normal'])*[1,-1,1]
        for face in faces[np.any(faces==i,axis=1)]:
            tri=xyz[face];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0])
            assert normal@n>0
