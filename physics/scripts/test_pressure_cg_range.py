import numpy as np
import pytest
from total_depth_nonlinear_pressure import AccelerationSystem
from pressure_cg_range_reference import solve
from total_depth_pressure import wet_pairs


@pytest.mark.parametrize('tiny',[2.**-149,2.**-130,2.**-126])
@pytest.mark.parametrize('arithmetic',[np.float64,np.float32])
def test_normalized_recurrence_preserves_small_physically_significant_components(tiny,arithmetic):
    h=np.ones((5,7));h[2,3]=tiny;bed=h*0
    system=AccelerationSystem(h,bed,wet_pairs(h,bed),.5,.4052787713439809,
        interpolation='depth_weighted',bed_slope=np.full((*h.shape,2),.02))
    y,x=np.indices(h.shape);rhs=np.stack((np.sin(x)+.5,np.cos(y)-.2),-1)
    rhs[2,3]=[.5/np.sqrt(tiny),-.1/np.sqrt(tiny)]
    matrix=np.empty((rhs.size,rhs.size));basis=np.zeros_like(rhs)
    for i in range(rhs.size):
        basis.flat[i]=1;matrix[:,i]=system.apply(basis).ravel();basis.flat[i]=0
    direct=np.linalg.solve(matrix,rhs.ravel()).reshape(rhs.shape)
    value,stats=solve(system,rhs,arithmetic=arithmetic)
    root=np.sqrt(h)[...,None]
    np.testing.assert_allclose(root*value,root*direct,rtol=2e-5,atol=1e-6)
    assert stats['physical_relative_residual']<2e-5
    assert stats['iterations']<=40


def test_exact_zero_and_iteration_budget():
    h=np.ones((3,5));system=AccelerationSystem(h,h*0,wet_pairs(h,h*0),1.,.4)
    value,stats=solve(system,np.zeros((*h.shape,2)))
    assert not value.any() and stats['iterations']==0
    with pytest.raises(ValueError):solve(system,value,iterations=41)
