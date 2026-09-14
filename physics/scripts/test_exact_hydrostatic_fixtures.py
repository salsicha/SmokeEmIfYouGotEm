from fractions import Fraction as Q
import numpy as np
from export_exact_hydrostatic_fixtures import expected,polynomial,cases


def test_constant_film_survives_arbitrary_represented_bed_datum():
    for name,rows in cases():
        if name!='constant_film':continue
        result=expected(np.asarray(rows,dtype=np.float32))
        assert result[0]==result[1]==result[2]==result[3]
        assert result[2]>0 and result[4:6]==[1,1]


def test_exact_positive_face_is_not_dry_just_because_output_rounds_to_zero():
    tiny=2.**-149
    rows=[(tiny,2*tiny,3*tiny,1),(0,0,0,-1),(tiny,tiny,tiny,0),(tiny,tiny,tiny,1)]
    h,z=polynomial(rows[0],rows[1]);assert h==Q(3,2)*Q(tiny) and z==0
    # Right bed is one tiny unit, leaving exactly half a tiny unit on the left.
    result=expected(rows);assert result[2]==0 and result[4:6]==[1,1]
    rows[3]=(2*tiny,2*tiny,2*tiny,1)
    # The left face is now exactly blocked; no numerical sign residue.
    assert expected(rows)[2]==0 and expected(rows)[4]==0


def test_flattened_constant_ghosts_do_not_reconstruct_neighbor_slopes():
    rows=[(0,1,100,0),(0,5,10,1),(0,2,100,0),(0,6,10,-1)]
    assert polynomial(rows[0],rows[1])==(Q(1),Q(5))
    result=expected(rows);assert result[2:4]==[0,0x40000000] and result[4:6]==[0,1]
