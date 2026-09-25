import numpy as np
import pytest
from build_boundary_ground_cavities import replace_cavity


def test_exact_local_points_and_shared_seam():
    v=np.array([[0.,0.,2.],[.5,0,1],[.5,.5,1],[0,.5,1],[1,0,1],[1,.5,1]])
    f=np.array([[0,1,2],[0,2,3],[1,4,5],[1,5,2]])
    lower=np.array([.1,.1,1.])
    xyz,triangles,report=replace_cavity(v,f,0,lower)
    assert np.array_equal(xyz[-1],lower)
    assert np.array_equal(xyz[triangles[:2]],v[f[2:]])
    assert report['retained_faces_exact']
    assert not np.any(triangles==0)


def test_edge_gate_not_relaxed():
    v=np.array([[0.,0.,2.],[2,0,1],[2,2,1],[0,2,1]])
    with pytest.raises(ValueError,match='Unsupported patch edge'):
        replace_cavity(v,np.array([[0,1,2],[0,2,3]]),0,np.array([.1,.1,1.]))


def test_existing_lower_is_reused_not_duplicated():
    v=np.array([[0.,0.,2.],[.5,0,1],[.5,.5,1],[0,.5,1],[.1,.1,1.]])
    f=np.array([[0,1,4],[1,2,4],[2,3,4],[3,0,4]])
    xyz,triangles,report=replace_cavity(v,f,0,v[4])
    assert len(xyz)==len(v) and report['lower_already_in_roof']
    assert not np.any(triangles==0) and 4 in triangles
