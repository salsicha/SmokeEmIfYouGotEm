import numpy as np
from prepare_constrained_wall_native import fingerprint


def test_native_hash_retains_winding_but_allows_cyclic_rotation():
    v=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    assert fingerprint(v,[[0,1,2]])==fingerprint(v,[[1,2,0]])
    assert fingerprint(v,[[0,1,2]])!=fingerprint(v,[[0,2,1]])


def test_native_hash_detects_coordinate_change_and_ignores_face_order():
    v=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    faces=[[0,1,2],[0,2,3]]
    assert fingerprint(v,faces)==fingerprint(v,faces[::-1])
    moved=v.copy();moved[0,2]=.001
    assert fingerprint(v,faces)!=fingerprint(moved,faces)
