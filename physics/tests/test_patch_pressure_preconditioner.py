import numpy as np
import pytest
from smooth_rational_velocity_stage import make
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from patch_pressure_preconditioner import PatchPressureSystem


@pytest.mark.parametrize('shape',((1,19),(2,11),(9,3)))
def test_principal_blocks_original_actions_and_symmetry(shape):
    rng=np.random.default_rng(9448);h=1+rng.random(shape);b=.1*rng.normal(size=shape)
    g=make(h,b,.4);a=ReconstructedAccelerationSystem(g,.4052787713439809)
    p=PatchPressureSystem(g,.4052787713439809);x=rng.normal(size=(*shape,2));y=rng.normal(size=x.shape)
    np.testing.assert_array_equal(p.apply(x),a.apply(x))
    for patch in p.patches:
        cols=patch['columns'];matrix=[]
        for index in cols:
            basis=np.zeros_like(x);basis.ravel()[index]=1
            matrix.append(a.apply(basis).ravel()[cols])
        np.testing.assert_allclose(patch['matrix'],np.array(matrix).T,rtol=1e-13,atol=1e-13)
    px=p.precondition(x);py=p.precondition(y)
    assert np.sum(x*px)>0
    assert abs(np.sum(x*py)-np.sum(y*px))<1e-10
    result,stats=p.solve(x,iterations=40,preconditioner='patch')
    assert stats['iterations']<=40
    assert stats['relative_residual']<1e-10
    np.testing.assert_allclose(a.apply(result),x,rtol=1e-9,atol=1e-10)
