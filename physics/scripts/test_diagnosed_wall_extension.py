import numpy as np
import pytest
from build_diagnosed_wall_extension import append_patch
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


def test_exterior_extension_retains_roof_and_closes():
    v=np.array([[0.,0.,2.],[.5,0.,2.],[0.,.5,2.]])
    f=np.array([[0,1,2]])
    xyz,faces,area=append_patch(v,f,[[0,1]],[[.25,-.25,1.5]])
    np.testing.assert_array_equal(xyz[faces[0]],v[f[0]])
    assert area==.0625
    _,_,_,closure=close_cap_below_retained_terrain(xyz,faces,0.)
    assert closure['maximum_volume_error_m3']<1e-12


@pytest.mark.parametrize('point,message', [([.1,.1,1.5],'overlap'),([.25,-2.,1.5],'edge limit'),([.25,0.,1.5],'Degenerate')])
def test_invalid_extension_rejected(point,message):
    with pytest.raises(ValueError,match=message):
        append_patch([[0,0,2],[.5,0,2],[0,.5,2]],[[0,1,2]],[[0,1]],[point])


def test_patch_patch_overlap_rejected():
    with pytest.raises(ValueError,match='overlap'):
        append_patch([[0,0,2],[.5,0,2],[0,.5,2]],[[0,1,2]],[[0,1],[0,1]],[[.25,-.25,1.5],[.25,-.2,1.5]])
