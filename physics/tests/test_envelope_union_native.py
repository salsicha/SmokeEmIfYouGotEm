import numpy as np
import pytest
from prepare_envelope_union_native import union_heights,flank_probes


class Flat:
    def __init__(self,height):self.height=height
    def sample(self,x,y):return np.zeros_like(np.asarray(x),dtype=float)+self.height


def roof():
    return np.array([[0.,0.,2.],[2.,0.,2.],[0.,2.,2.]]),np.array([[0,1,2]])


def test_lower_envelope_only_and_ground_outside():
    vertices,faces=roof()
    z,owner=union_heights(Flat(1),vertices,faces,[[.2,.3],[3.,3.]])
    assert z.tolist()==[2.,1.] and owner.tolist()==[True,False]
    vertices[:,2]=.5
    z,owner=union_heights(Flat(1),vertices,faces,[[.2,.3],[3.,3.]])
    assert z.tolist()==[1.,1.] and not owner.any()


def test_tie_owned_by_ground():
    vertices,faces=roof()
    z,owner=union_heights(Flat(2),vertices,faces,[[.2,.3]])
    assert z.tolist()==[2.] and not owner.any()


def test_flank_targets_above_ground_outward_and_reflected():
    vertices,faces=roof()
    rows=flank_probes(Flat(1),vertices,faces,[[0,1]],np.array([10,20,30]))
    assert rows==[dict(kind='exposed_inferred_flank',world_position_cm=[110.,20.,180.],
        outward_normal=[0.,1.,0.],ray_half_length_cm=1.,expected_rock=True)]


def test_covered_boundary_checks_ground_not_buried_wall():
    vertices,faces=roof()
    row,=flank_probes(Flat(3),vertices,faces,[[0,1]],np.zeros(3))
    assert row['world_position_cm']==[100.,0.,300.]
    assert row['outward_normal']==[0.,0.,1.] and not row['expected_rock']
    assert row['kind']=='covered_boundary'


def test_ambiguous_boundary_rejected():
    vertices,faces=roof()
    with pytest.raises(ValueError,match='Ambiguous'):
        flank_probes(Flat(1),vertices,np.tile(faces,(2,1)),[[0,1]],np.zeros(3))
