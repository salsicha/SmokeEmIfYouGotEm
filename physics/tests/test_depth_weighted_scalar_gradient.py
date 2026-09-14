import numpy as np
import pytest
from depth_weighted_scalar_gradient import DepthWeightedScalarGradient as Gradient, depth_weighted_forcing


def grid(n):
    dx=1/n
    y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
    return dx,x,y


def test_constant_affine_and_quadratic_with_arbitrary_positive_weights():
    dx,x,y=grid(13);h=np.exp(2*x-y)
    g=Gradient(h,dx)
    assert np.all(g.gradient(np.ones_like(h)) == 0)
    actual=g.gradient(2*x*x-3*x*y+4*y*y+2*x-y+3)
    expected=np.stack((4*x-3*y+2,-3*x+8*y-1),axis=-1)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=3e-12)
    assert all(np.all(r==2) for r in g.ranks)


def test_independent_weighted_least_squares_matrix():
    dx,x,y=grid(9);rng=np.random.default_rng(883)
    h=np.exp(rng.normal(size=x.shape));f=rng.normal(size=x.shape);g=Gradient(h,dx)
    actual=g.gradient(f)
    for point in [(0,0),(3,3),(5,7),(14,14)]:
        for component,axis in enumerate((1,0)):
            rows=[];values=[];weights=[]
            for r in g.offsets:
                neighbor=list(point);neighbor[axis]+=r
                if not 0 <= neighbor[axis] < h.shape[axis]:continue
                neighbor=tuple(neighbor);rows.append([r,r*r]);values.append(f[neighbor]-f[point])
                weights.append(h[neighbor]/(h[point]+h[neighbor]))
            a=np.array(rows)*np.sqrt(weights)[:,None];b=np.array(values)*np.sqrt(weights)
            expected=np.linalg.lstsq(a,b,rcond=None)[0][0]/dx
            assert abs(actual[point][component]-expected)<2e-12


def test_near_dry_neighbor_is_not_a_finite_wet_gradient_source():
    h=np.ones((7,7));h[:,1:3]=0.;ht=np.full_like(h,.125)
    f=np.zeros_like(h);f[:,1:3]=1.
    limit=Gradient(h,1.,mass_rate=ht).gradient(f)
    assert limit[3,3,0]==0
    errors=[]
    for eps in (2.**-8,2.**-16,2.**-24):
        errors.append(abs(Gradient(h+eps*ht,1.).gradient(f)[3,3,0]))
    assert errors[-1]<1e-6 and errors[0]/errors[-1]>50000


def test_smooth_field_second_order_or_better_with_one_sided_wet_front():
    errors=[]
    for n in (16,32,64):
        dx,x,y=grid(n);h=np.where(x<.25,0.,1.+x)
        g=Gradient(h,dx);f=np.sin(2*x)+np.cos(y)
        core=(x>=.25)&(x<=1)&(y>=0)&(y<=1)
        exact=np.stack((2*np.cos(2*x),-np.sin(y)),axis=-1)
        errors.append(np.max(abs(g.gradient(f)[core]-exact[core])))
    assert errors[0]/errors[1]>3.5 and errors[1]/errors[2]>3.5


def test_rank_deficiency_is_explicit_and_no_input_is_modified():
    h=np.zeros((5,5));h[2,2]=1.;h[2,3]=2.;original=h.copy()
    g=Gradient(h,1.);f=np.indices(h.shape)[1].astype(float)
    assert g.ranks[0][2,2]==1 and g.ranks[1][2,2]==0
    np.testing.assert_array_equal(g.gradient(f)[2,2],[1.,0.])
    np.testing.assert_array_equal(h,original)


def test_invalid_input_and_binding_restoration():
    import source_supported_pressure_reference as pressure
    from depth_weighted_scalar_gradient import DepthWeightedSourceBoundary
    original=pressure.SourceSupportedScalarBoundary
    with pytest.raises(RuntimeError):
        with depth_weighted_forcing():
            assert pressure.SourceSupportedScalarBoundary is DepthWeightedSourceBoundary
            raise RuntimeError('deliberate')
    assert pressure.SourceSupportedScalarBoundary is original
    for depth,rate in [(np.array([[-1.]]),None),(np.array([[0.]]),np.array([[-1.]])),(np.array([[np.nan]]),None)]:
        with pytest.raises(ValueError):Gradient(depth,1.,mass_rate=rate)
    with pytest.raises(ValueError):Gradient(np.ones((5,5)),0.)
    with pytest.raises(ValueError):Gradient(np.ones((5,5)),1.).gradient(np.ones((4,5)))
